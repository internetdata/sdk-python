"""Plumbing the sync and the async client both need: transport wiring, the deadline on
each attempt, response unwrapping, the retry policy, and the per-instance cache."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import contextvars
import hashlib
import ipaddress
import json
import math
import os
import re
import secrets
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from types import ModuleType
from typing import IO, Any, TypeVar, cast
from urllib.parse import quote, urlsplit, urlunsplit

import httpx
from cachetools import TTLCache

from ._generated.client import AuthenticatedClient, Client
from ._generated.types import UNSET, Unset
from .errors import InternetDataError, error_from_response, oauth_error_from
from .models import Database, Download, Pkce, Result, to_database, to_download, to_result

DEFAULT_BASE_URL = "https://api.internetdata.io"
DEFAULT_CONCURRENCY = 8
DEFAULT_RETRIES = 2
DEFAULT_CACHE_MAX_SIZE = 10_000
DEFAULT_CACHE_TTL = 3600.0
DEFAULT_TIMEOUT = 30.0
DEFAULT_DOWNLOADS_LIMIT = 50

# The most addresses POST /batch takes in one call; a larger batch is sent in chunks of
# this size.
BATCH_MAX = 1000

OAUTH_METADATA_PATH = "/.well-known/oauth-authorization-server"
OAUTH_DEVICE_AUTHORIZATION_PATH = "/oauth/device_authorization"
OAUTH_TOKEN_PATH = "/oauth/token"
OAUTH_REVOKE_PATH = "/oauth/revoke"
OAUTH_AUTHORIZE_PATH = "/oauth/authorize"
OAUTH_REGISTER_PATH = "/oauth/register"
DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"

# One chunk of a transfer, and therefore the ceiling on what a download of any size
# costs in memory.
TRANSFER_CHUNK_BYTES = 1 << 20

_BACKOFF_BASE = 1.0

# The longest wait the sync client's clock can count, about 292 years: past it a lock's
# wait, `socket.settimeout` and `time.sleep` all raise OverflowError instead.
WAIT_CEILING = threading.TIMEOUT_MAX

# The longest `Retry-After` waited as given, 2^31 - 1 ms, the bound every SDK takes. One
# past it is still a throttle, waited out on the backoff: as given, 2147484 held a call
# for 24.8 days, and 9223372036854775807, 1e400 or a year-9999 date raised a raw
# OverflowError from the sync client's sleep (measured on 2.6.0, 2026-09-30).
RETRY_AFTER_CEILING = 2147483.647

# An `expires_in` past this, about 146 billion years, is a deadline nobody reaches. The
# cap keeps the poll's deadline a float: past 1.8e308 adding it to the clock raises.
POLL_DEADLINE_CAP = 2**62

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
    api_key = check_api_key(api_key)
    # httpx drops one trailing slash when it joins a path onto the base URL and keeps the
    # rest, so a second or third reached the API as `//api/v2/database/list`, which prod
    # answers with a redirect this client does not follow: every call failed (2.7.3,
    # measured 2026-10-16).
    base_url = base_url.rstrip("/")
    httpx_args: dict[str, Any] = {}
    if transport is not None:
        httpx_args["transport"] = transport
    headers = {"User-Agent": user_agent()}
    if api_key is None:
        return cast(
            AuthenticatedClient,
            Client(
                base_url=base_url,
                headers=headers,
                timeout=httpx.Timeout(timeout),
                httpx_args=httpx_args,
            ),
        )
    return AuthenticatedClient(
        base_url=base_url,
        token=api_key,
        headers=headers,
        timeout=httpx.Timeout(timeout),
        httpx_args=httpx_args,
    )


def user_agent() -> str:
    """`internetdata-python/<version>`, on every request this library makes, object storage's
    included, so its traffic, and which releases are still in use, can be counted. Read at
    call time: the package's `__init__` imports this module before it sets the version."""
    from . import __version__

    return f"internetdata-python/{__version__}"


# A base URL on the API host (`api.`, or `api-<env>.` for an environment).
_API_HOST = re.compile(r"api(?:-([^.]+))?\.(.+)", re.IGNORECASE)


def oauth_base(base_url: str) -> str:
    """Where the `oauth` accessor asks: the apex the API host serves, since InternetData's
    authorization server issues at the apex, not on the API host. `api.` is dropped and
    `api-<env>.` becomes `<env>.`, so `https://api.internetdata.io` signs in at
    `https://internetdata.io`; any other base URL is used as given."""
    base_url = base_url.rstrip("/")
    parts = urlsplit(base_url)
    match = _API_HOST.fullmatch(parts.netloc)
    if match is None:
        return base_url
    env, rest = match.groups()
    return urlunsplit(parts._replace(netloc=f"{env}.{rest}" if env else rest))


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
        headers={"User-Agent": user_agent()},
        timeout=httpx.Timeout(None, connect=timeout),
        transport=transport,
        follow_redirects=True,
    )


def build_async_transfer_client(
    timeout: float | None, transport: httpx.AsyncBaseTransport | None
) -> httpx.AsyncClient:
    """`build_transfer_client`, for asyncio."""
    return httpx.AsyncClient(
        headers={"User-Agent": user_agent()},
        timeout=httpx.Timeout(None, connect=timeout),
        transport=transport,
        follow_redirects=True,
    )


def check_api_key(api_key: str | None) -> str | None:
    """`api_key` without the blanks around it, or None when nothing else is left.

    Refused where it is SET when a control character remains, or a character outside
    ASCII, which httpx cannot put in a header: a CR, LF or NUL failed every call as a
    retried `network` error with nothing sent, a C1 control or any other non-ASCII
    character as a raw `UnicodeEncodeError` (2.7.3, measured 2026-10-16), while a tab or
    DEL went out on the wire. Untrimmed, a key of blanks was sent as one rather than as no
    key, and failed every call the same way (2.7.1, measured 2026-10-12).
    """
    if api_key is None:
        return None
    if not isinstance(api_key, str):
        raise TypeError(f"api_key must be a string or None, not {type(api_key).__name__}")
    key = api_key.strip()
    if any(ord(char) < 0x20 or ord(char) >= 0x7F for char in key):
        raise ValueError("api_key holds a control character or one outside ASCII")
    return key or None


def check_build(build: str | None) -> str | Unset:
    """`build` as the download takes it: unset for None or an empty name, so a value read
    from an unset setting downloads the live build."""
    if build is None or build == "":
        return UNSET
    if not isinstance(build, str):
        raise TypeError(f"build must be a build's name, a string, not {build!r}")
    return build


def check_timeout(timeout: float | None) -> float | None:
    """`timeout`, once it is a bound an attempt can meet.

    Refused where it is SET, because nothing downstream refuses it: zero, a negative
    number, NaN or a string reached the first call and failed it, and every call after,
    as a retried `network` error after three seconds of backoff, or for a string as a
    `server_error` blaming the API. So is anything past `WAIT_CEILING`, infinity
    included, since the sync client's wait cannot hold it: 1e300 failed every call with
    a raw `OverflowError` (2.6.0, measured 2026-09-30). None is the spelling for no bound.

    Compared rather than handed to `math.isfinite`, which raised a raw `OverflowError` for
    an integer too large for a float, such as 10**400 (2.9.2, measured 2026-10-25). NaN
    fails both comparisons.
    """
    if timeout is None:
        return None
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)
        or not 0 < timeout <= WAIT_CEILING
    ):
        raise ValueError(
            f"timeout must be a number of seconds greater than 0 and at most "
            f"{WAIT_CEILING:.0f}, or None for no bound, not {timeout!r}"
        )
    return timeout


def check_retries(retries: float) -> float:
    """`retries`, once it is a count of retries: a whole number from 0, or `math.inf` to
    retry a failing call until it succeeds.

    Refused where it is SET, because nothing downstream refuses it: NaN compares false with
    every attempt number, so a failing call was retried until it succeeded, a negative read
    as 0, 1.5 as two retries, and a string or None raised a raw `TypeError` out of every
    call that failed, a 404 included (2.9.2, measured 2026-10-25).
    """
    if (
        isinstance(retries, bool)
        or not isinstance(retries, int | float)
        or not retries >= 0
        or (isinstance(retries, float) and not (retries.is_integer() or retries == math.inf))
    ):
        raise ValueError(f"retries must be a whole number from 0, or math.inf, not {retries!r}")
    return retries


def check_address(ip: str) -> None:
    """Refuse what is not an IP address before anything is sent. The API answers an AS
    (`AS15169`) or a domain at the lookup's own path, and that answer is not a lookup's, so
    sent, it came back as a retried `server_error` the caller could do nothing with."""
    if isinstance(ip, str):
        try:
            ipaddress.ip_address(ip)
            return
        except ValueError:
            pass
    raise InternetDataError(
        "bad_request",
        f"{ip!r} is not an IP address: look an AS up with lookup_asn, and a domain with "
        "lookup_domain",
    )


def call_retries(retries: float | None) -> float | None:
    """A per-call `retries`, checked as the client's is, or None for the client's own."""
    return None if retries is None else check_retries(retries)


def check_client_concurrency(concurrency: int) -> int:
    """A client's `concurrency`, once it is a whole number of at least 1, refused where it
    is SET as a retry count is: taken as it came, 0, -1, NaN and `True` would run each batch
    one chunk at a time, 1.5 two, and a string, None or a list fail every batch that sent
    anything with a raw `TypeError` (measured on the VPNDetection SDK, 2026-11-11)."""
    if isinstance(concurrency, bool) or not isinstance(concurrency, int) or concurrency < 1:
        raise ValueError(f"concurrency must be a whole number of at least 1, not {concurrency!r}")
    return concurrency


def check_concurrency(concurrency: int | None) -> None:
    """Refuse a per-call concurrency that could never send a chunk, before anything is sent,
    rather than quietly running it as 1."""
    if concurrency is None:
        return
    if isinstance(concurrency, bool) or not isinstance(concurrency, int) or concurrency < 1:
        raise InternetDataError(
            "bad_request", f"concurrency must be a whole number of at least 1, got {concurrency!r}"
        )


def chunked(ips: list[str], size: int) -> list[list[str]]:
    return [ips[i : i + size] for i in range(0, len(ips), size)]


def entry_error(entry: dict[str, Any]) -> InternetDataError:
    """A per-entry failure inside a successful batch: the status the single lookup would
    have answered, and its message, with no headers at all - so a 429 here is a spent
    allowance, which is the only kind the API puts in an entry."""
    return error_from_response(int(entry["status"]), httpx.Headers(), {"error": entry.get("error")})


def batch_body(res: httpx.Response) -> dict[str, Any]:
    """A chunk's answer, once it holds `results` or `errors` and neither is anything but a
    map. Anything else is the whole chunk unreadable, a retried `server_error` carrying the
    status. Each entry is read on its own by `batch_answers`, so one it cannot read is that
    address's error alone."""
    body = unwrap(res)
    members = [body.get(name) for name in ("results", "errors")]
    if all(m is None for m in members) or any(
        m is not None and not isinstance(m, dict) for m in members
    ):
        raise InternetDataError(
            "server_error", "the batch answer held neither results nor errors", res.status_code
        )
    return body


def batch_answers(chunk: list[str], body: dict[str, Any]) -> dict[str, Result | InternetDataError]:
    """One chunk's answer, mapped back onto the addresses it was asked about.

    Every address lands in exactly one of `results` and `errors`; an address in neither
    is the server breaking its own contract, and is reported as such rather than lost.
    """
    results = body.get("results") or {}
    errors = body.get("errors") or {}
    out: dict[str, Result | InternetDataError] = {}
    for ip in chunk:
        if ip in results:
            try:
                out[ip] = parse_entry(results[ip], to_result, 200)
            except InternetDataError as err:
                out[ip] = err
        elif ip in errors:
            try:
                out[ip] = entry_error(errors[ip])
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                out[ip] = malformed(exc, 200)
        else:
            out[ip] = InternetDataError(
                "server_error", f"the batch answer did not include {ip}", 200
            )
    return out


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


def request(
    endpoint: ModuleType,
    client: AuthenticatedClient,
    bound: float | None,
    *,
    decode: bool = True,
    **params: Any,
) -> httpx.Response:
    """One attempt at one generated endpoint, finished within `bound` seconds, or unbounded
    when that is None, and its answer checked by `decoded` unless `decode` is False.

    Assembled from the endpoint module's `_get_kwargs` and `_build_response` because its
    `sync_detailed` sends through httpx alone, and httpx has no bound on the attempt.
    """
    http = client.get_httpx_client()
    req = http.build_request(**endpoint._get_kwargs(**params), timeout=httpx.Timeout(bound))
    res = exchange(http, req, bound)
    return decoded(endpoint, client, res) if decode else res


async def request_async(
    endpoint: ModuleType,
    client: AuthenticatedClient,
    bound: float | None,
    *,
    decode: bool = True,
    **params: Any,
) -> httpx.Response:
    """`request`, awaited."""
    http = client.get_async_httpx_client()
    req = http.build_request(**endpoint._get_kwargs(**params), timeout=httpx.Timeout(bound))
    res = await exchange_async(http, req, bound)
    return decoded(endpoint, client, res) if decode else res


def decoded(
    endpoint: ModuleType, client: AuthenticatedClient, res: httpx.Response
) -> httpx.Response:
    """`res`, once the generated decoder has read it, where it is a 2xx.

    The generated code eagerly decodes the body of every DOCUMENTED status into its model,
    and it raises three different ways doing it: a body that is not JSON is a `ValueError`
    out of `json()`, an object missing a required key a `KeyError`, and a `standing` this
    pinned spec predates a `ValueError` out of an enum constructor. On a 2xx each is the
    server sending an answer this client cannot read, so each is the one error type here,
    a retried `server_error` carrying the status.

    Any other status is left to `unwrap`, which classifies it by the status alone, whatever
    its body. Decoded too, a proxy's HTML page on a 401, a 404 or an empty 403 was a
    retried `server_error` with no status, sent three times (2.7.1, measured 2026-10-12).
    """
    if 200 <= res.status_code < 300:
        try:
            endpoint._build_response(client=client, response=res)
        except (KeyError, TypeError, ValueError) as exc:
            raise malformed(exc, res.status_code) from exc
    return res


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
    body: dict[str, Any] | None = None,
) -> httpx.Response:
    """One attempt at an OAuth endpoint, carrying no credential, its failure raised. `body`
    goes as JSON, for `register`; every other one sends a form or nothing."""
    http = client.get_httpx_client()
    req = _oauth_build(http, method, path, form, bound, body)
    return oauth_checked(exchange(http, req, bound))


async def oauth_request_async(
    client: AuthenticatedClient,
    method: str,
    path: str,
    form: dict[str, str] | None,
    bound: float | None,
    body: dict[str, Any] | None = None,
) -> httpx.Response:
    """`oauth_request`, awaited."""
    http = client.get_async_httpx_client()
    req = _oauth_build(http, method, path, form, bound, body)
    return oauth_checked(await exchange_async(http, req, bound))


def registration_body(redirect_uris: Sequence[str], client_name: str | None) -> dict[str, Any]:
    """`register`'s JSON body: the redirect URIs in the order given, then `client_name`
    unless it is None or empty. No URI at all, an empty one, or one with no UTF-8 (a lone
    surrogate) is refused before anything is sent."""
    if isinstance(redirect_uris, str) or not redirect_uris:
        raise ValueError(f"redirect_uris must list at least one URI, not {redirect_uris!r}")
    uris = list(redirect_uris)
    for i, uri in enumerate(uris):
        _check_text(f"redirect_uris[{i}]", uri)
    body: dict[str, Any] = {"redirect_uris": uris}
    if client_name:
        _check_text("client_name", client_name)
        body["client_name"] = client_name
    return body


def _check_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{name} must be a non-empty string, not {value!r}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} has no UTF-8 to send: {value!r}") from exc


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
        # In parts, since `time.sleep` raises past WAIT_CEILING rather than waiting.
        while seconds > 0:
            part = min(seconds, WAIT_CEILING)
            time.sleep(part)
            seconds -= part


class AsyncClock:
    """`Clock`, awaited."""

    def now(self) -> float:
        return time.monotonic()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


def malformed(exc: Exception, status: int) -> InternetDataError:
    return InternetDataError("server_error", f"malformed response from the API: {exc}", status)


def unwrap(res: httpx.Response) -> dict[str, Any]:
    """The response body as it came off the wire, or the failure it describes."""
    body = _decode(res.content)
    status = res.status_code
    if not 200 <= status < 300:
        raise error_from_response(status, res.headers, body)
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


def parse_body(res: httpx.Response, parse: Callable[[dict[str, Any]], T]) -> T:
    """A served body through the model layer, with a malformed one reported as the
    server's failure, carrying its status, rather than as a traceback out of a dataclass
    constructor."""
    return parse_entry(unwrap(res), parse, res.status_code)


def parse_entry(body: Any, parse: Callable[[dict[str, Any]], T], status: int) -> T:
    """`parse_body` for a body already decoded: an answer, or one entry of a batch's."""
    if not isinstance(body, dict):
        raise InternetDataError("server_error", "the API answered with a non-object body", status)
    try:
        return parse(body)
    # AttributeError too: metadata's `schema` or `sample` as an array instead of an object
    # escaped 2.7.1 raw, out of `.items()` (measured 2026-10-12).
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise malformed(exc, status) from exc


def redirect_location(res: httpx.Response) -> str:
    """Where a `302` points, or whatever the API said instead."""
    location: str | None = res.headers.get("location")
    if res.status_code == 302 and location:
        return location
    unwrap(res)
    raise InternetDataError(
        "server_error", "expected a redirect to object storage", res.status_code
    )


def databases_of(body: dict[str, Any]) -> list[Database]:
    """Exactly the families the server listed for THIS key, in the order it listed them.

    Nothing is added here, and nothing may be: a family built for a single customer is
    absent from this array for every organization that does not license it, so filling a
    gap from any other source would publish the fact that the family exists.

    An object where the list is due is refused rather than read as one with nothing in it:
    `{"databases": {}}` answered an empty catalog (2.9.2, measured 2026-10-25).
    """
    return [to_database(d) for d in _listed(body, "databases")]


def downloads_of(body: dict[str, Any]) -> list[Download]:
    return [to_download(d) for d in _listed(body, "downloads")]


def _listed(body: dict[str, Any], name: str) -> list[Any]:
    value = body[name]
    if not isinstance(value, list):
        raise TypeError(f"{name} is not a list: {value!r}")
    return value


def checksums_of(body: dict[str, Any]) -> dict[str, str]:
    """The digests, unwrapped one level past the envelope, the four the spec requires
    among them as strings.

    The response carries `id` and `format` beside them, so reading a top-level `sha256`
    finds nothing. That exact mistake shipped in another binding's 1.0.x, which is why
    the shared corpus pins the depth.

    `id` and `format` are read too, though nothing returns them: a null or numeric `id`
    came back as a whole answer, and so did `checksums` sent as a list of pairs (2.9.2,
    measured 2026-10-25).
    """
    for member in ("id", "format"):
        if not isinstance(body[member], str):
            raise TypeError(f"the checksum answer's {member} is not a string: {body[member]!r}")
    if not isinstance(body["checksums"], dict):
        raise TypeError(f"checksums is not an object: {body['checksums']!r}")
    digests = dict(body["checksums"])
    for algorithm in ("md5", "sha1", "sha256", "sha512"):
        if not isinstance(digests[algorithm], str):
            raise TypeError(f"the {algorithm} checksum is not a string: {digests[algorithm]!r}")
    return digests


def retry_delay(err: InternetDataError, attempt: int, retries: float) -> float | None:
    """How long to wait before attempt `attempt + 1`, or None when there must not be one.

    A server-supplied `Retry-After` wins over the backoff schedule outright: it is the
    only thing that makes a 429 worth retrying at all, so second-guessing it with a
    shorter wait would just spend the next attempt on the same rejection. One past
    `RETRY_AFTER_CEILING` is waited out on the backoff instead.
    """
    if attempt >= retries or not err.retryable:
        return None
    if err.retry_after_seconds is not None and err.retry_after_seconds <= RETRY_AFTER_CEILING:
        return err.retry_after_seconds
    return _BACKOFF_BASE * (2.0**attempt)


class Cache:
    """A per-client result cache.

    Never global or static: two clients with different keys are on different plans and
    entitled to different fields, so a shared cache would serve one of them the other's
    shape. The lock is not optional, because the sync batch drives lookups from a thread
    pool and `TTLCache` is not thread-safe.
    """

    def __init__(self, max_size: int, ttl: float) -> None:
        self._entries: TTLCache[str, Result] = TTLCache(maxsize=max_size, ttl=ttl)
        self._lock = threading.Lock()

    def get(self, ip: str) -> Result | None:
        with self._lock:
            return self._entries.get(ip)

    def put(self, ip: str, result: Result) -> None:
        with self._lock:
            self._entries[ip] = result


class Abandoned(Exception):
    """A request's leader stopped before its answer landed; a waiter asks again."""


class Flights:
    """The addresses with a request in flight, so concurrent misses share one.

    A lookup that misses joins the request in flight for its address or leads one; a batch
    joins those and boards the rest before it builds its chunks, so a lookup arriving
    meanwhile awaits the batch. The registry is ours rather than a coalescing cache's
    because a batch has to know which addresses it leads before it sends any. `make` builds
    what a waiter blocks or awaits on: a `concurrent.futures.Future` for the sync client,
    the running loop's future for the async one.
    """

    def __init__(self, make: Callable[[], Any]) -> None:
        self._make = make
        self._lock = threading.Lock()
        self._flights: dict[str, Any] = {}

    def board(self, ips: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
        led: dict[str, Any] = {}
        joined: dict[str, Any] = {}
        with self._lock:
            for ip in ips:
                flight = self._flights.get(ip)
                if flight is not None:
                    joined[ip] = flight
                    continue
                flight = self._make()
                self._flights[ip] = flight
                led[ip] = flight
        return led, joined

    def land(self, ip: str, flight: Any, answer: Result | BaseException) -> None:
        """Hands every waiter the answer and takes the address off the board. Cache a
        served answer FIRST: a caller that missed just before it landed finds no flight
        after this, and reads the cache again before it sends."""
        with self._lock:
            if self._flights.get(ip) is flight:
                del self._flights[ip]
        if flight.done():
            return
        if isinstance(answer, BaseException):
            flight.set_exception(answer)
            # Retrieved here, so an answer nobody joined logs no warning when collected.
            flight.exception()
        else:
            flight.set_result(answer)


def landed_error(err: InternetDataError) -> InternetDataError:
    """One waiter's own copy of a shared failure, so raising it in one thread or task
    never grows the traceback another raises. Built by hand: `copy.copy` calls the
    constructor with `args` alone, which lacks the kind."""
    clone = type(err).__new__(type(err), *err.args)
    clone.__dict__.update(err.__dict__)
    clone.__cause__ = err.__cause__
    return clone


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
    body: dict[str, Any] | None = None,
) -> httpx.Request:
    req = http.build_request(method, path, data=form, json=body, timeout=httpx.Timeout(bound))
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


def _decode(content: bytes) -> Any:
    try:
        return json.loads(content)
    except ValueError:
        return None
