"""Plumbing the sync and the async client both need: transport wiring, response
unwrapping, and the retry policy."""

from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import IO, Any, TypeVar

import httpx

from ._generated.client import AuthenticatedClient
from ._generated.types import Response
from .errors import InternetDataError, error_from_response
from .models import Database, Download, to_database, to_download

DEFAULT_BASE_URL = "https://internetdata.io"
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 10.0
DEFAULT_DOWNLOADS_LIMIT = 50

# One chunk of a transfer, and therefore the ceiling on what a download of any size
# costs in memory.
TRANSFER_CHUNK_BYTES = 1 << 20

_BACKOFF_BASE = 1.0

T = TypeVar("T")


def build_client(
    api_key: str,
    base_url: str,
    timeout: float | None,
    transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None,
) -> AuthenticatedClient:
    """The generated client, wired for one of ours.

    Every endpoint here needs a key, so there is no keyless flavor to fall back to: an
    `Authorization: Bearer ` with nothing after it is a 401, not an anonymous request.

    The transport is injected through `httpx_args` rather than with
    `set_httpx_client()`, which silently bypasses auth: the generated client only adds
    the `Authorization` header when it CONSTRUCTS the httpx client itself.
    """
    httpx_args: dict[str, Any] = {}
    if transport is not None:
        httpx_args["transport"] = transport
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

    The lambda does nothing but call the generated function, which is what keeps this
    catch from swallowing a fault of our own.
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
