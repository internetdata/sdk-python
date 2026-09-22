"""The synchronous client."""

from __future__ import annotations

import builtins
import os
import time
from collections.abc import Callable
from types import TracebackType
from typing import Self, TypeVar

import httpx

from ._core import (
    DEFAULT_BASE_URL,
    DEFAULT_DOWNLOADS_LIMIT,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEVICE_CODE_GRANT,
    OAUTH_DEVICE_AUTHORIZATION_PATH,
    OAUTH_METADATA_PATH,
    OAUTH_REVOKE_PATH,
    OAUTH_TOKEN_PATH,
    TRANSFER_CHUNK_BYTES,
    Clock,
    as_error,
    assert_whole_transfer,
    build_client,
    build_transfer_client,
    check_timeout,
    checksums_of,
    databases_of,
    downloads_of,
    oauth_body,
    oauth_request,
    parse_body,
    part_file,
    redirect_location,
    request,
    retry_delay,
    storage_refusal,
    unwrap,
)
from ._generated.api.database_v_2 import (
    database_checksum_v2,
    database_metadata_v2,
    download_database_v2,
    list_databases,
    list_downloads,
)
from ._generated.client import AuthenticatedClient
from ._generated.models.database_format import DatabaseFormat
from .errors import InternetDataError, OauthError, OauthExpiredTokenError
from .models import (
    Database,
    DatabaseMetadata,
    DeviceAuthorization,
    Download,
    Format,
    OauthMetadata,
    TokenResponse,
    to_device_authorization,
    to_metadata,
    to_oauth_metadata,
    to_token_response,
)

__all__ = ["DatabaseApi", "InternetData", "OauthApi"]

T = TypeVar("T")


class InternetData:
    """A client for the InternetData API.

    Every database published today is licensed, so create a key carrying the
    `db.download` scope in the console and pass it in. The argument is optional
    nonetheless, and an absent or empty one sends no `Authorization` header at all
    rather than an empty one: what this API serves without a license is a product
    decision, not the client's to refuse. `oauth` needs no key at all.

    `timeout` is how long one attempt at a request may take, in seconds, body included, so a
    call that is retried can take longer in total; None means no bound, and a database
    transfer is exempt. Every `oauth` request and every `database` call but the two
    transfers also takes `timeout`, which overrides the client's for that call alone.
    Anything else that is not a finite number greater than 0 is a `ValueError` where it is
    set, rather than a failure of every call.

    Holds an HTTP connection pool, so use it as a context manager or call `close()` when
    you are done with it.
    """

    database: DatabaseApi
    """The licensed database catalog and downloads."""

    oauth: OauthApi
    """Signing a person in with OAuth, to hand a program on their machine one of their keys."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        retries: int = DEFAULT_RETRIES,
        timeout: float | None = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        timeout = check_timeout(timeout)
        self._client = build_client(api_key, base_url, timeout, transport)
        self._transfer = build_transfer_client(timeout, transport)
        self._retries = retries
        self._timeout = timeout
        self.database = DatabaseApi(self)
        self.oauth = OauthApi(self)

    def close(self) -> None:
        self._client.get_httpx_client().close()
        self._transfer.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # A per-call timeout, checked, or the client's own when the call gave none.
    def _bound(self, timeout: float | None) -> float | None:
        return self._timeout if timeout is None else check_timeout(timeout)

    def _retrying(self, call: Callable[[], T], retries: int) -> T:
        attempt = 0
        while True:
            try:
                return call()
            except (InternetDataError, httpx.HTTPError) as exc:
                err = as_error(exc)
                delay = retry_delay(err, attempt, retries)
                if delay is None:
                    raise err
                time.sleep(delay)
                attempt += 1


class DatabaseApi:
    """The database catalog and downloads. Access is granted by contract, not self-serve.

    `list` is a method here, which shadows the builtin for everything else in the class
    body, so the return annotations name `builtins.list` explicitly.

    Every call here that asks the API a question takes `timeout`, in seconds, bounding
    each ATTEMPT of that call alone and overriding the client's. The two transfers take
    none and refuse one rather than ignoring it: a database runs to gigabytes and minutes,
    so any bound that suits a JSON call would abandon a healthy download.
    """

    def __init__(self, owner: InternetData) -> None:
        self._owner = owner

    def list(self, *, timeout: float | None = None) -> builtins.list[Database]:
        """The published catalog as YOUR organization may see it.

        Every family carries a `standing`, so one you have never bought is listed as
        `unlicensed`: the catalog is a shop window as much as an inventory. Nothing is
        cached and nothing is reconstructed here - what you get is what the server sent
        for the key you are holding, so a listing held from one key is not an answer for
        another.

        A license covers a FAMILY, while a download names a version, so the ids for the
        other calls come from each entry's `versions`.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        def call() -> builtins.list[Database]:
            res = request(list_databases, self._client, self._bound(timeout))
            return parse_body(unwrap(res), databases_of)

        return self._retrying(call)

    def metadata(self, database_id: str, *, timeout: float | None = None) -> DatabaseMetadata:
        """What is inside one database: freshness, row count, columns, samples and sizes.

        Cheap enough to poll: it answers `updated` and `entries` without moving the
        build. `size` is the number to budget a transfer against before starting one.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        def call() -> DatabaseMetadata:
            res = request(database_metadata_v2, self._client, self._bound(timeout), id=database_id)
            return parse_body(unwrap(res), to_metadata)

        return self._retrying(call)

    def checksums(
        self, database_id: str, format: Format, *, timeout: float | None = None
    ) -> dict[str, str]:
        """Every checksum published for one database file, keyed by algorithm.

        Keyed rather than one digest because the API publishes md5, sha1, sha256 and
        sha512 side by side and which of them you want is your verifier's business.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        def call() -> dict[str, str]:
            res = request(
                database_checksum_v2,
                self._client,
                self._bound(timeout),
                id=database_id,
                format_=DatabaseFormat(format),
            )
            return parse_body(unwrap(res), checksums_of)

        return self._retrying(call)

    def downloads(
        self, limit: int = DEFAULT_DOWNLOADS_LIMIT, *, timeout: float | None = None
    ) -> builtins.list[Download]:
        """Your organization's recent download attempts, newest first.

        Refusals are listed too: a denial is what answers "it stopped working", and its
        absence answers nothing.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        def call() -> builtins.list[Download]:
            res = request(list_downloads, self._client, self._bound(timeout), limit=limit)
            return parse_body(unwrap(res), downloads_of)

        return self._retrying(call)

    def download_url(
        self, database_id: str, format: Format, *, timeout: float | None = None
    ) -> str:
        """The time-limited URL for one database file.

        The API answers `302` to object storage, and the link carries its own signature,
        so it holds no API key and can be handed to anything that speaks HTTP. Returned
        rather than followed so the caller decides how to move a file that reaches
        gigabytes; the link authorizes the START of a transfer, so one already running is
        not interrupted when it lapses.

        `timeout` bounds each attempt at MINTING the link, which is an ordinary API
        request, and says nothing about the transfer you then run with it.
        """

        def call() -> str:
            res = request(
                download_database_v2,
                self._client,
                self._bound(timeout),
                id=database_id,
                format_=DatabaseFormat(format),
            )
            return redirect_location(res)

        return self._retrying(call)

    def download(self, database_id: str, format: Format, path: str | os.PathLike[str]) -> int:
        """Download one database file to `path`, and return the bytes written.

        The bytes are streamed straight to disk, so nothing larger than a chunk is ever
        held in memory whatever the database weighs. They land in a neighboring `.part`
        file that is moved into place only once the whole transfer has arrived, so a
        failure leaves neither a truncated file at `path` nor the `.part` behind, and an
        existing copy at `path` survives a refresh that fails.

        A failure DURING the transfer surfaces as it happened, an `httpx` error or an
        `OSError`, rather than as this library's error type: a reset socket and a full
        disk are different problems, and only one of them is ours.
        """
        res = self._open_transfer(database_id, format)
        try:
            written = 0
            with part_file(path) as sink:
                for chunk in res.iter_bytes(TRANSFER_CHUNK_BYTES):
                    sink.write(chunk)
                    written += len(chunk)
                # Inside, so a short transfer fails before anything is moved into place.
                assert_whole_transfer(res, written)
            return written
        finally:
            res.close()

    def download_bytes(self, database_id: str, format: Format) -> bytes:
        """Download one database file and hand back its bytes.

        **This holds the entire file in memory**, and the catalog spans seven orders of
        magnitude, from a few hundred bytes to several gigabytes. Reach for it at the
        small end, where the bytes go straight into a parser, and use `download` for
        anything you have not checked `metadata` for.
        """
        res = self._open_transfer(database_id, format)
        try:
            body = res.read()
            assert_whole_transfer(res, len(body))
            return body
        finally:
            res.close()

    # Follows the 302 as a SECOND, unauthenticated request rather than by loosening the
    # redirect guard: the presigned URL authorizes itself, so forwarding the API key
    # would hand a credential to a host with no business holding it - and object storage
    # rejects a request carrying both signatures outright.
    #
    # Returns the response with its body still unread, so the caller decides whether a
    # database is going to disk or into memory.
    def _open_transfer(self, database_id: str, format: Format) -> httpx.Response:
        url = self.download_url(database_id, format)
        transfer = self._owner._transfer

        def call() -> httpx.Response:
            res = transfer.send(transfer.build_request("GET", url), stream=True)
            if res.status_code != httpx.codes.OK:
                res.close()
                raise storage_refusal(res)
            return res

        return self._retrying(call)

    @property
    def _client(self) -> AuthenticatedClient:
        return self._owner._client

    def _bound(self, timeout: float | None) -> float | None:
        return self._owner._bound(timeout)

    def _retrying(self, call: Callable[[], T]) -> T:
        return self._owner._retrying(call, self._owner._retries)


class OauthApi:
    """Signing a person in with the OAuth device flow, so a program running on their own
    machine can be handed one of their API keys instead of asking them to paste it.

    No request here carries this client's API key, and none needs one: build the client
    with no key to sign in, then a second one with the key the sign-in hands over. The
    `client_id` is your registered one, issued on request from support@internetdata.io.

    `metadata`, `device_authorization` and `revoke` are retried like a lookup. The token
    exchanges are sent exactly once, because the server spends what they present. A
    refusal is an `OauthError` and is never retried.
    """

    def __init__(self, owner: InternetData) -> None:
        self._owner = owner
        self._clock = Clock()

    def metadata(self, *, timeout: float | None = None) -> OauthMetadata:
        """The authorization server's discovery document."""

        def call() -> OauthMetadata:
            res = self._send("GET", OAUTH_METADATA_PATH, None, timeout)
            return to_oauth_metadata(oauth_body(res), res.status_code)

        return self._owner._retrying(call, self._owner._retries)

    def device_authorization(
        self,
        client_id: str,
        *,
        scope: str | None = None,
        resource: str | None = None,
        timeout: float | None = None,
    ) -> DeviceAuthorization:
        """Start a device sign-in. Show the person `verification_uri` and `user_code`, then
        pass the answer to `poll_device_token`.

        `scope` is one space-delimited string, narrowed by the server to what `client_id`
        may ask for. Under a burst the server refuses with the `OauthError` `slow_down`.
        """
        form = {"client_id": client_id}
        if scope is not None:
            form["scope"] = scope
        if resource is not None:
            form["resource"] = resource

        def call() -> DeviceAuthorization:
            res = self._send("POST", OAUTH_DEVICE_AUTHORIZATION_PATH, form, timeout)
            return to_device_authorization(oauth_body(res), res.status_code)

        return self._owner._retrying(call, self._owner._retries)

    def exchange_device_code(
        self, client_id: str, device_code: str, *, timeout: float | None = None
    ) -> TokenResponse:
        """Redeem an approved device code, once. Until the person approves it the server
        refuses with the `OauthError` `authorization_pending`; `poll_device_token` does the
        waiting for you.
        """
        form = {"grant_type": DEVICE_CODE_GRANT, "device_code": device_code, "client_id": client_id}
        return self._exchange(form, timeout)

    def exchange_refresh_token(
        self, client_id: str, refresh_token: str, *, timeout: float | None = None
    ) -> TokenResponse:
        """Trade a refresh token for a new pair, once: the server spends the old one before
        it mints the new. The answer never carries `apikey`, only `apikey_id`.
        """
        form = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }
        return self._exchange(form, timeout)

    def revoke(self, client_id: str, token: str, *, timeout: float | None = None) -> None:
        """End a token. A refresh token ends the whole sign-in and every token it issued, so
        revoking it is how a program signs the machine out."""

        def call() -> None:
            self._send("POST", OAUTH_REVOKE_PATH, {"token": token, "client_id": client_id}, timeout)

        self._owner._retrying(call, self._owner._retries)

    def poll_device_token(
        self, client_id: str, device: DeviceAuthorization, *, timeout: float | None = None
    ) -> TokenResponse:
        """Wait for the person to approve a device sign-in, and return its tokens.

        Waits `device.interval` seconds (5 when that is below 1) before EVERY request, the
        first included, and 5 more for the rest of the call each time the server answers
        `slow_down`. Ends at the first answer that is neither: a refusal raises
        `OauthAccessDeniedError`, a code that ran out `OauthExpiredTokenError`, as does
        outliving `device.expires_in` counted from this call (with a `status` of None), and
        any other failure is raised as it came. `timeout` bounds each request, not the poll.

        Blocks the calling thread until one of those; the sync client has no way to cancel
        it sooner.
        """
        # Refused before the first wait, not after it.
        check_timeout(timeout)
        interval = device.interval if device.interval >= 1 else 5
        deadline = self._clock.now() + device.expires_in
        while True:
            self._clock.sleep(interval)
            if self._clock.now() >= deadline:
                raise OauthExpiredTokenError()
            try:
                return self.exchange_device_code(client_id, device.device_code, timeout=timeout)
            except OauthError as err:
                # RFC 8628: slow_down widens the interval for every later request, not the next.
                if err.error_code == "slow_down":
                    interval += 5
                elif err.error_code != "authorization_pending":
                    raise

    def _exchange(self, form: dict[str, str], timeout: float | None) -> TokenResponse:
        def call() -> TokenResponse:
            res = self._send("POST", OAUTH_TOKEN_PATH, form, timeout)
            return to_token_response(oauth_body(res), res.status_code)

        return self._owner._retrying(call, 0)

    def _send(
        self, method: str, path: str, form: dict[str, str] | None, timeout: float | None
    ) -> httpx.Response:
        return oauth_request(self._owner._client, method, path, form, self._owner._bound(timeout))
