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
    TRANSFER_CHUNK_BYTES,
    as_error,
    assert_whole_transfer,
    build_client,
    build_transfer_client,
    checksums_of,
    databases_of,
    downloads_of,
    parse_body,
    part_file,
    redirect_location,
    retry_delay,
    send,
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
from ._generated.models.database_checksum_v2_format import DatabaseChecksumV2Format
from ._generated.models.download_database_v2_format import DownloadDatabaseV2Format
from .errors import InternetDataError
from .models import Database, DatabaseMetadata, Download, Format, to_metadata

__all__ = ["DatabaseApi", "InternetData"]

T = TypeVar("T")


class InternetData:
    """A client for the InternetData API.

    Every database published today is licensed, so create a key carrying the
    `db.download` scope in the console and pass it in. The argument is optional
    nonetheless, and an absent or empty one sends no `Authorization` header at all
    rather than an empty one: what this API serves without a licence is a product
    decision, not the client's to refuse.

    Holds an HTTP connection pool, so use it as a context manager or call `close()` when
    you are done with it.
    """

    database: DatabaseApi
    """The licensed database catalog and downloads, which is the whole API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        retries: int = DEFAULT_RETRIES,
        timeout: float | None = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = build_client(api_key, base_url, timeout, transport)
        self._transfer = build_transfer_client(timeout, transport)
        self._retries = retries
        self.database = DatabaseApi(self)

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
    """

    def __init__(self, owner: InternetData) -> None:
        self._owner = owner

    def list(self) -> builtins.list[Database]:
        """The published catalog as YOUR organization may see it.

        Every family carries a `standing`, so one you have never bought is listed as
        `unlicensed` rather than hidden: the catalog is a shop window as much as an
        inventory. The exception is a family commissioned for a single customer, which is
        absent entirely for everyone else, because listing it would advertise that
        customer. Nothing is cached and nothing is reconstructed here - what you get is
        what the server sent for the key you are holding.

        A licence covers a FAMILY, while a download names a version, so the ids for the
        other calls come from each entry's `versions`.
        """

        def call() -> builtins.list[Database]:
            res = send(lambda: list_databases.sync_detailed(client=self._client))
            return parse_body(unwrap(res), databases_of)

        return self._retrying(call)

    def metadata(self, database_id: str) -> DatabaseMetadata:
        """What is inside one database: freshness, row count, columns, samples and sizes.

        Cheap enough to poll: it answers `updated` and `entries` without moving the
        build. `size` is the number to budget a transfer against before starting one.
        """

        def call() -> DatabaseMetadata:
            res = send(
                lambda: database_metadata_v2.sync_detailed(client=self._client, id=database_id)
            )
            return parse_body(unwrap(res), to_metadata)

        return self._retrying(call)

    def checksums(self, database_id: str, format: Format) -> dict[str, str]:
        """Every checksum published for one database file, keyed by algorithm.

        Keyed rather than one digest because the API publishes md5, sha1, sha256 and
        sha512 side by side and which of them you want is your verifier's business.
        """

        def call() -> dict[str, str]:
            res = send(
                lambda: database_checksum_v2.sync_detailed(
                    client=self._client,
                    id=database_id,
                    format_=DatabaseChecksumV2Format(format),
                )
            )
            return parse_body(unwrap(res), checksums_of)

        return self._retrying(call)

    def downloads(self, limit: int = DEFAULT_DOWNLOADS_LIMIT) -> builtins.list[Download]:
        """Your organization's recent download attempts, newest first.

        Refusals are listed too: a denial is what answers "it stopped working", and its
        absence answers nothing.
        """

        def call() -> builtins.list[Download]:
            res = send(lambda: list_downloads.sync_detailed(client=self._client, limit=limit))
            return parse_body(unwrap(res), downloads_of)

        return self._retrying(call)

    def download_url(self, database_id: str, format: Format) -> str:
        """The time-limited URL for one database file.

        The API answers `302` to object storage, and the link carries its own signature,
        so it holds no API key and can be handed to anything that speaks HTTP. Returned
        rather than followed so the caller decides how to move a file that reaches
        gigabytes; the link authorizes the START of a transfer, so one already running is
        not interrupted when it lapses.
        """

        def call() -> str:
            res = send(
                lambda: download_database_v2.sync_detailed(
                    client=self._client,
                    id=database_id,
                    format_=DownloadDatabaseV2Format(format),
                )
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

    def _retrying(self, call: Callable[[], T]) -> T:
        return self._owner._retrying(call, self._owner._retries)
