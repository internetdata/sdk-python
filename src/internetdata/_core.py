"""Plumbing the sync and the async client both need: transport wiring, the deadline on
each attempt, response unwrapping, and the retry policy."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import contextvars
import hashlib
import json
import math
import os
import secrets
import threading
import time
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import IO, Any, TypeVar, cast
from urllib.parse import quote

import httpx

from ._generated.client import AuthenticatedClient, Client
from ._generated.types import Response
from .errors import InternetDataError, error_from_response, oauth_error_from
from .models import Database, Download, Pkce, to_database, to_download

DEFAULT_BASE_URL = "https://internetdata.io"
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 30.0
DEFAULT_DOWNLOADS_LIMIT = 50

OAUTH_METADATA_PATH = "/.well-known/oauth-authorization-server"
OAUTH_DEVICE_AUTHORIZATION_PATH = "/oauth/device_authorization"
OAUTH_TOKEN_PATH = "/oauth/token"
OAUTH_REVOKE_PATH = "/oauth/revoke"
OAUTH_AUTHORIZE_PATH = "/oauth/authorize"
DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"

# One chunk of a transfer, and therefore the ceiling on what a download of any size
# costs in memory.
TRANSFER_CHUNK_BYTES = 1 << 20

_BACKOFF_BASE = 1.0

T = TypeVar("T")


def build_client(
    api_key: str | None,
    base_url: str,
    timeout: float | None,
    transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None,
) -> AuthenticatedClient:
    """The generated client, wired for one of ours.

    Every generated endpoint function types `client` as `AuthenticatedClient` because
    every operation lists a security scheme, but a keyless caller must send NO
    `Authorization` header rather than an empty one: `Bearer ` with nothing after it is
    a 401 that reads as a wrong key. The two classes are interchangeable where the
    endpoints use them, so the keyless one is built as `Client` and the cast lives here
    instead of at every call site.

    The transport is injected through `httpx_args` rather than with
    `set_httpx_client()`, which silently bypasses auth: the generated client only adds
    the `Authorization` header when it CONSTRUCTS the httpx client itself.
    """
    httpx_args: dict[str, Any] = {}
    if transport is not None:
        httpx_args["transport"] = transport
    if not api_key:
        return cast(
            AuthenticatedClient,
            Client(base_url=base_url, timeout=httpx.Timeout(timeout), httpx_args=httpx_args),
        )
    return AuthenticatedClient(
        base_url=base_url,
        token=api_key,
        timeout=httpx.Timeout(timeout),
        httpx_args=httpx_args,
    )


def build_transfer_client(
    timeout: float | None, transport: httpx.BaseTransport | None
) -> httpx.Client:
    """A SECOND client, holding no credential, for the object-storage leg of a download.

    The API answers a download with a `302` to a presigned URL, and that URL authorizes
    itself. Following the redirect on the API client would forward the key to a host with
    no business holding it. Worth more than tidiness: object storage answers 400 to a
    request carrying both a presigned signature and an `Authorization` header, so
    forwarding the key does not merely leak it, it breaks the download.

    Only the connect phase keeps the client's timeout. That timeout is a sane bound on a
    metadata call and the wrong one on a body that reaches gigabytes, which would
    otherwise be cut off mid-transfer. Redirects ARE followed here, unlike on the API
    client: object storage behind a CDN answers one, and there is no credential to leak
    by going along with it.
    """
    return httpx.Client(
        timeout=httpx.Timeout(None, connect=timeout),
        transport=transport,
        follow_redirects=True,
    )


def build_async_transfer_client(
    timeout: float | None, transport: httpx.AsyncBaseTransport | None
) -> httpx.AsyncClient:
    """`build_transfer_client`, for asyncio."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(None, connect=timeout),
        transport=transport,
        follow_redirects=True,
    )


def check_timeout(timeout: float | None) -> float | None:
    """`timeout`, once it is a bound an attempt can meet.

    Refused where it is SET, because nothing downstream refuses it: zero, a negative
    number, NaN or a string reached the first call and failed it, and every call after,
    as a retried `network` error after three seconds of backoff, or for a string as a
    `server_error` blaming the API. Infinity is refused too, since the sync client's wait
    cannot hold it (`OverflowError`); None is the spelling for no bound.
    """
    if timeout is None:
        return None
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError(
            f"timeout must be a number of seconds greater than 0, or None for no bound, "
            f"not {timeout!r}"
        )
    return timeout


def storage_refusal(res: httpx.Response) -> InternetDataError:
    """What object storage refusing a download link becomes.

    The body is deliberately left unread: the status is what separates a lapsed link from
    a refused one, and nothing bounds the size of an error page.
    """
    return error_from_response(
        res.status_code,
        res.headers,
        {"rc": f"object storage refused the download link with status {res.status_code}"},
    )


def assert_whole_transfer(res: httpx.Response, written: int) -> None:
    """Check what arrived against what was promised.

    A transfer that dies mid-body can reach a client as a plain end of stream, and a
    short file that looks complete is worse than no file at all: the next run reads it as
    a whole database.

    Skipped when the body was decoded on the way in, because `Content-Length` then
    describes the ENCODED bytes and disagreeing with it is correct rather than short. A
    chunked response declares no length; httpx raises for itself when one of those is cut
    off.
    """
    declared = res.headers.get("content-length")
    encoding = res.headers.get("content-encoding", "identity").strip().lower()
    if declared is None or encoding not in ("", "identity"):
        return
    try:
        expected = int(declared)
    except ValueError:
        return
    if expected != written:
        raise InternetDataError(
            "network",
            f"the transfer ended after {written} of {expected} bytes",
            res.status_code,
        )


@contextlib.contextmanager
def part_file(destination: str | os.PathLike[str]) -> Iterator[IO[bytes]]:
    """A download's bytes, landing beside `destination` and moved onto it at the end.

    Two failures this prevents, and only the first is the obvious one. A transfer that
    dies half way leaves no truncated file carrying the real name. And a refresh that
    fails leaves yesterday's good copy untouched, which opening the destination itself
    could not do: that truncates it before the first byte of the new one arrives.
    """
    partial = os.fspath(destination) + ".part"
    try:
        with open(partial, "wb") as sink:
            yield sink
        os.replace(partial, destination)
    except BaseException:
        Path(partial).unlink(missing_ok=True)
        raise


def send(call: Callable[[], Response[Any]]) -> Response[Any]:
    """One generated endpoint call.

    The generated code eagerly decodes the body of every DOCUMENTED status into its model
    before anything here sees the response, and it raises three different ways doing it: a
    503 carrying an intermediary's HTML error page is a `ValueError` out of `json()`, a
    200 missing a required key is a `KeyError`, and a `standing` this pinned spec predates
    is a `ValueError` out of an enum constructor. All three are the server sending
    something this client cannot read, which is a failed request rather than a bug in the
    caller's code, so all three become the one error type here.

    The call does nothing but build one generated request, send it and hand the answer to
    the generated decoder, which is what keeps this catch from swallowing a fault of our own.
    An argument is converted before it, so a format this client does not publish is the
    caller's `ValueError` rather than the server's failure.
    """
    try:
        return call()
    except (KeyError, TypeError, ValueError) as exc:
        raise malformed(exc) from exc


async def send_async(call: Callable[[], Awaitable[Response[Any]]]) -> Response[Any]:
    """`send`, awaited."""
    try:
        return await call()
    except (KeyError, TypeError, ValueError) as exc:
        raise malformed(exc) from exc


def request(
    endpoint: ModuleType, client: AuthenticatedClient, bound: float | None, **params: Any
) -> Response[Any]:
    """`send` for one generated endpoint, one attempt of it finished within `bound` seconds,
    or unbounded when that is None.

    Assembled from the endpoint module's `_get_kwargs` and `_build_response` because its
    `sync_detailed` sends through httpx alone, and httpx has no bound on the attempt.
    """

    def call() -> Response[Any]:
        http = client.get_httpx_client()
        req = http.build_request(**endpoint._get_kwargs(**params), timeout=httpx.Timeout(bound))
        res = exchange(http, req, bound)
        return cast(Response[Any], endpoint._build_response(client=client, response=res))

    return send(call)


async def request_async(
    endpoint: ModuleType, client: AuthenticatedClient, bound: float | None, **params: Any
) -> Response[Any]:
    """`request`, awaited."""

    async def call() -> Response[Any]:
        http = client.get_async_httpx_client()
        req = http.build_request(**endpoint._get_kwargs(**params), timeout=httpx.Timeout(bound))
        res = await exchange_async(http, req, bound)
        return cast(Response[Any], endpoint._build_response(client=client, response=res))

    return await send_async(call)


def exchange(http: httpx.Client, req: httpx.Request, bound: float | None) -> httpx.Response:
    """One attempt at `req`, its whole body read, finished within `bound` seconds or failed
    as a `network` error.

    httpx bounds each PHASE of a request (connect, write, every read), not the attempt, so a
    body trickling in a byte at a time outlasts any timeout it is given. The attempt runs on
    a thread of its own and the caller waits at most `bound` for it; one abandoned stops at
    its next chunk, or at the per-phase bound `req` also carries.
    """
    if bound is None:
        return http.send(req)
    finished = threading.Event()
    abandoned = threading.Event()
    outcome: list[httpx.Response | BaseException] = []
    context = contextvars.copy_context()

    def attempt() -> None:
        try:
            outcome.append(context.run(_read_whole, http, req, abandoned))
        except BaseException as exc:  # noqa: BLE001 - raised again on the caller's thread
            outcome.append(exc)
        finally:
            finished.set()

    threading.Thread(target=attempt, name="internetdata-attempt", daemon=True).start()
    try:
        if not finished.wait(bound):
            raise _deadline_passed(bound)
    finally:
        abandoned.set()
    if isinstance(outcome[0], BaseException):
        raise outcome[0]
    return outcome[0]


async def exchange_async(
    http: httpx.AsyncClient, req: httpx.Request, bound: float | None
) -> httpx.Response:
    """`exchange`, awaited. Cancelling the attempt closes its connection, so no thread is
    needed to leave it behind."""
    if bound is None:
        return await http.send(req)
    deadline = asyncio.timeout(bound)
    try:
        async with deadline:
            return await http.send(req)
    except TimeoutError:
        if not deadline.expired():
            raise
        raise _deadline_passed(bound) from None


def oauth_request(
    client: AuthenticatedClient,
    method: str,
    path: str,
    form: dict[str, str] | None,
    bound: float | None,
) -> httpx.Response:
    """One attempt at an OAuth endpoint, carrying no credential, its failure raised."""
    http = client.get_httpx_client()
    return oauth_checked(exchange(http, _oauth_build(http, method, path, form, bound), bound))


async def oauth_request_async(
    client: AuthenticatedClient,
    method: str,
    path: str,
    form: dict[str, str] | None,
    bound: float | None,
) -> httpx.Response:
    """`oauth_request`, awaited."""
    http = client.get_async_httpx_client()
    req = _oauth_build(http, method, path, form, bound)
    return oauth_checked(await exchange_async(http, req, bound))


def authorization_url(
    base_url: str,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    optional: dict[str, str | None],
) -> str:
    """The authorization code flow's URL, built with no request: the five parameters every
    one carries, then `scope`, `state` and `resource` when given and not empty.

    Each value is percent-encoded over UTF-8 with only A-Z a-z 0-9 - . _ ~ left literal, so
    a space is %20 and never +. A required value that is empty, or has no UTF-8 (a lone
    surrogate), is refused.
    """
    required = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
    }
    for name, value in required.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string, not {value!r}")
    params = [
        ("response_type", "code"),
        *required.items(),
        ("code_challenge_method", "S256"),
        *((name, value) for name, value in optional.items() if value),
    ]
    encoded = []
    for name, value in params:
        try:
            encoded.append(f"{name}={quote(value, safe='')}")
        except UnicodeEncodeError as exc:
            raise ValueError(f"{name} has no UTF-8 to send: {value!r}") from exc
    return f"{base_url.rstrip('/')}{OAUTH_AUTHORIZE_PATH}?{'&'.join(encoded)}"


def create_pkce() -> Pkce:
    """A fresh PKCE pair, from 32 bytes of the system's secure random source."""
    verifier = _base64url(secrets.token_bytes(32))
    return Pkce(verifier=verifier, challenge=pkce_challenge(verifier))


def pkce_challenge(verifier: str) -> str:
    """The `S256` challenge for a PKCE verifier: its SHA-256, as unpadded base64url."""
    return _base64url(hashlib.sha256(verifier.encode("utf-8")).digest())


def _base64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def oauth_checked(res: httpx.Response) -> httpx.Response:
    """A 2xx as it came, or the failure it describes.

    Only a 4xx whose body is a JSON object with a STRING `error` is an OAuth refusal. Every
    5xx, whatever its body says, is the server failing, and is retried wherever the
    operation retries.
    """
    status = res.status_code
    if 200 <= status < 300:
        return res
    body = _decode(res.content)
    if 400 <= status < 500 and isinstance(body, dict) and isinstance(body.get("error"), str):
        description = body.get("error_description")
        raise oauth_error_from(
            body["error"], description if isinstance(description, str) else None, status
        )
    raise error_from_response(status, res.headers, body)


def oauth_body(res: httpx.Response) -> Any:
    """A 2xx OAuth answer's JSON, or None when it does not parse."""
    return _decode(res.content)


class Clock:
    """The device poll's wait and its deadline, replaced together in tests."""

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class AsyncClock:
    """`Clock`, awaited."""

    def now(self) -> float:
        return time.monotonic()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


def malformed(exc: Exception) -> InternetDataError:
    return InternetDataError("server_error", f"malformed response from the API: {exc}")


def unwrap(res: Response[Any]) -> dict[str, Any]:
    """The response body as it came off the wire, or the failure it describes."""
    body = _decode(res.content)
    status = int(res.status_code)
    if not 200 <= status < 300:
        raise error_from_response(status, _headers(res), body)
    if not isinstance(body, dict):
        raise InternetDataError("server_error", "the API answered with a non-object body", status)
    return body


def as_error(exc: InternetDataError | httpx.HTTPError) -> InternetDataError:
    """A transport failure, as the one error type this library raises.

    Deliberately narrow: anything else is a bug rather than a failed request, and turning
    it into a `network` error here would hide it behind a retry.
    """
    if isinstance(exc, InternetDataError):
        return exc
    return InternetDataError("network", str(exc) or type(exc).__name__)


def parse_body(body: dict[str, Any], parse: Callable[[dict[str, Any]], T]) -> T:
    """A served body through the model layer, with a malformed one reported as the
    server's failure rather than as a traceback out of a dataclass constructor."""
    try:
        return parse(body)
    except (KeyError, TypeError, ValueError) as exc:
        raise malformed(exc) from exc


def redirect_location(res: Response[Any]) -> str:
    """Where a `302` points, or whatever the API said instead."""
    location: str | None = _headers(res).get("location")
    if int(res.status_code) == 302 and location:
        return location
    unwrap(res)
    raise InternetDataError(
        "server_error", "expected a redirect to object storage", int(res.status_code)
    )


def databases_of(body: dict[str, Any]) -> list[Database]:
    """Exactly the families the server listed for THIS key, in the order it listed them.

    Nothing is added here, and nothing may be: a family built for a single customer is
    absent from this array for every organization that does not license it, so filling a
    gap from any other source would publish the fact that the family exists.
    """
    return [to_database(d) for d in body["databases"]]


def downloads_of(body: dict[str, Any]) -> list[Download]:
    return [to_download(d) for d in body["downloads"]]


def checksums_of(body: dict[str, Any]) -> dict[str, str]:
    """The digests, unwrapped one level past the envelope.

    The response carries `id` and `format` beside them, so reading a top-level `sha256`
    finds nothing. That exact mistake shipped in another binding's 1.0.x, which is why
    the shared corpus pins the depth.
    """
    return dict(body["checksums"])


def retry_delay(err: InternetDataError, attempt: int, retries: int) -> float | None:
    """How long to wait before attempt `attempt + 1`, or None when there must not be one.

    A server-supplied `Retry-After` wins over the backoff schedule outright: it is the
    only thing that makes a 429 worth retrying at all, so second-guessing it with a
    shorter wait would just spend the next attempt on the same rejection.
    """
    if attempt >= retries or not err.retryable:
        return None
    if err.retry_after_seconds is not None:
        return err.retry_after_seconds
    return _BACKOFF_BASE * (2.0**attempt)


# The generated client bakes the API key into every request it builds. None of the OAuth
# endpoints reads one, and on the token endpoint an `Authorization` header reads as client
# authentication, which these public clients do not have. So it comes off here, in the one
# place every OAuth request is built.
def _oauth_build(
    http: httpx.Client | httpx.AsyncClient,
    method: str,
    path: str,
    form: dict[str, str] | None,
    bound: float | None,
) -> httpx.Request:
    req = http.build_request(method, path, data=form, timeout=httpx.Timeout(bound))
    req.headers.pop("authorization", None)
    return req


# Reads the body on the attempt's own thread, and gives up between chunks once the caller
# has stopped waiting, which closes the connection rather than draining a trickle.
def _read_whole(
    http: httpx.Client, req: httpx.Request, abandoned: threading.Event
) -> httpx.Response:
    res = http.send(req, stream=True)
    try:
        if isinstance(res.stream, httpx.SyncByteStream):
            res.stream = _Abandonable(res.stream, abandoned, req)
        res.read()
    finally:
        res.close()
    return res


class _Abandonable(httpx.SyncByteStream):
    def __init__(
        self, inner: httpx.SyncByteStream, abandoned: threading.Event, req: httpx.Request
    ) -> None:
        self._inner = inner
        self._abandoned = abandoned
        self._req = req

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._inner:
            if self._abandoned.is_set():
                raise httpx.ReadError("abandoned once its deadline passed", request=self._req)
            yield chunk

    def close(self) -> None:
        self._inner.close()


def _deadline_passed(bound: float) -> InternetDataError:
    return InternetDataError("network", f"the request did not complete within {bound:g} seconds")


# The generated Response declares a plain MutableMapping, but always carries httpx's
# case-insensitive Headers. Rebuilding one keeps a header lookup case-blind whichever it
# turns out to be, which matters for `Retry-After`.
def _headers(res: Response[Any]) -> httpx.Headers:
    return httpx.Headers(res.headers)


def _decode(content: bytes) -> Any:
    try:
        return json.loads(content)
    except ValueError:
        return None
