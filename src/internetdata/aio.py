"""The asyncio client.

Mirrors `client.py` method for method; only the waiting differs. The two are written out
rather than shared because every difference between them is an `await`, and the wrappers
that hide that are harder to read than the duplication.
"""

from __future__ import annotations

import asyncio
import builtins
import os
from collections.abc import Awaitable, Callable
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
    build_async_transfer_client,
    build_client,
    check_timeout,
    checksums_of,
    databases_of,
    downloads_of,
    parse_body,
    part_file,
    redirect_location,
    request_async,
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
from .errors import InternetDataError
from .models import Database, DatabaseMetadata, Download, Format, to_metadata

__all__ = ["AsyncDatabaseApi", "AsyncInternetData"]

T = TypeVar("T")


class AsyncInternetData:
    """A client for the InternetData API, for asyncio.

    Identical in behavior to `InternetData`. Close it with `await client.aclose()`, or
    use it as an async context manager.
    """

    database: AsyncDatabaseApi
    """The licensed database catalog and downloads, which is the whole API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        retries: int = DEFAULT_RETRIES,
        timeout: float | None = DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        timeout = check_timeout(timeout)
        self._client = build_client(api_key, base_url, timeout, transport)
        self._transfer = build_async_transfer_client(timeout, transport)
        self._retries = retries
        self._timeout = timeout
        self.database = AsyncDatabaseApi(self)

    async def aclose(self) -> None:
        await self._client.get_async_httpx_client().aclose()
        await self._transfer.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    # A per-call timeout, checked, or the client's own when the call gave none.
    def _bound(self, timeout: float | None) -> float | None:
        return self._timeout if timeout is None else check_timeout(timeout)

    async def _retrying(self, call: Callable[[], Awaitable[T]], retries: int) -> T:
        attempt = 0
        while True:
            try:
                return await call()
            except (InternetDataError, httpx.HTTPError) as exc:
                err = as_error(exc)
                delay = retry_delay(err, attempt, retries)
                if delay is None:
                    raise err
                await asyncio.sleep(delay)
                attempt += 1


class AsyncDatabaseApi:
    """The database catalog and downloads. Access is granted by contract, not self-serve.

    `list` is a method here, which shadows the builtin for everything else in the class
    body, so the return annotations name `builtins.list` explicitly.

    Every call here that asks the API a question takes `timeout`, in seconds, bounding
    each ATTEMPT of that call alone and overriding the client's. The two transfers take
    none and refuse one rather than ignoring it: a database runs to gigabytes and minutes,
    so any bound that suits a JSON call would abandon a healthy download.
    """

    def __init__(self, owner: AsyncInternetData) -> None:
        self._owner = owner

    async def list(self, *, timeout: float | None = None) -> builtins.list[Database]:
        """The published catalog as YOUR organization may see it.

        Every family carries a `standing`, so one you have never bought is listed as
        `unlicensed` rather than hidden. The exception is a family commissioned for a
        single customer, which is absent entirely for everyone else. Nothing is cached
        and nothing is reconstructed here - what you get is what the server sent for the
        key you are holding.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        async def call() -> builtins.list[Database]:
            res = await request_async(list_databases, self._client, self._bound(timeout))
            return parse_body(unwrap(res), databases_of)

        return await self._retrying(call)

    async def metadata(self, database_id: str, *, timeout: float | None = None) -> DatabaseMetadata:
        """What is inside one database: freshness, row count, columns, samples and sizes.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        async def call() -> DatabaseMetadata:
            res = await request_async(
                database_metadata_v2, self._client, self._bound(timeout), id=database_id
            )
            return parse_body(unwrap(res), to_metadata)

        return await self._retrying(call)

    async def checksums(
        self, database_id: str, format: Format, *, timeout: float | None = None
    ) -> dict[str, str]:
        """Every checksum published for one database file, keyed by algorithm.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        async def call() -> dict[str, str]:
            res = await request_async(
                database_checksum_v2,
                self._client,
                self._bound(timeout),
                id=database_id,
                format_=DatabaseFormat(format),
            )
            return parse_body(unwrap(res), checksums_of)

        return await self._retrying(call)

    async def downloads(
        self, limit: int = DEFAULT_DOWNLOADS_LIMIT, *, timeout: float | None = None
    ) -> builtins.list[Download]:
        """Your organization's recent download attempts, newest first.

        `timeout` bounds each attempt at this call alone, in place of the client's.
        """

        async def call() -> builtins.list[Download]:
            res = await request_async(
                list_downloads, self._client, self._bound(timeout), limit=limit
            )
            return parse_body(unwrap(res), downloads_of)

        return await self._retrying(call)

    async def download_url(
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

        async def call() -> str:
            res = await request_async(
                download_database_v2,
                self._client,
                self._bound(timeout),
                id=database_id,
                format_=DatabaseFormat(format),
            )
            return redirect_location(res)

        return await self._retrying(call)

    async def download(self, database_id: str, format: Format, path: str | os.PathLike[str]) -> int:
        """Download one database file to `path`, and return the bytes written.

        The bytes are streamed straight to disk, so nothing larger than a chunk is ever
        held in memory whatever the database weighs. They land in a neighboring `.part`
        file that is moved into place only once the whole transfer has arrived, so a
        failure leaves neither a truncated file at `path` nor the `.part` behind, and an
        existing copy at `path` survives a refresh that fails.

        A failure DURING the transfer surfaces as it happened, an `httpx` error or an
        `OSError`, rather than as this library's error type: a reset socket and a full
        disk are different problems, and only one of them is ours.

        Each chunk is written from a worker thread. A gigabyte of blocking writes on the
        event loop would stall every other task in the process for the length of the
        transfer, which is the one thing an async caller cannot afford.
        """
        res = await self._open_transfer(database_id, format)
        try:
            loop = asyncio.get_running_loop()
            written = 0
            with part_file(path) as sink:
                async for chunk in res.aiter_bytes(TRANSFER_CHUNK_BYTES):
                    await loop.run_in_executor(None, sink.write, chunk)
                    written += len(chunk)
                # Inside, so a short transfer fails before anything is moved into place.
                assert_whole_transfer(res, written)
            return written
        finally:
            await res.aclose()

    async def download_bytes(self, database_id: str, format: Format) -> bytes:
        """Download one database file and hand back its bytes.

        **This holds the entire file in memory**, and the catalog spans seven orders of
        magnitude, from a few hundred bytes to several gigabytes. Reach for it at the
        small end, where the bytes go straight into a parser, and use `download` for
        anything you have not checked `metadata` for.
        """
        res = await self._open_transfer(database_id, format)
        try:
            body = await res.aread()
            assert_whole_transfer(res, len(body))
            return body
        finally:
            await res.aclose()

    # Follows the 302 as a SECOND, unauthenticated request rather than by loosening the
    # redirect guard: the presigned URL authorizes itself, so forwarding the API key
    # would hand a credential to a host with no business holding it - and object storage
    # rejects a request carrying both signatures outright.
    #
    # Returns the response with its body still unread, so the caller decides whether a
    # database is going to disk or into memory.
    async def _open_transfer(self, database_id: str, format: Format) -> httpx.Response:
        url = await self.download_url(database_id, format)
        transfer = self._owner._transfer

        async def call() -> httpx.Response:
            res = await transfer.send(transfer.build_request("GET", url), stream=True)
            if res.status_code != httpx.codes.OK:
                await res.aclose()
                raise storage_refusal(res)
            return res

        return await self._retrying(call)

    @property
    def _client(self) -> AuthenticatedClient:
        return self._owner._client

    def _bound(self, timeout: float | None) -> float | None:
        return self._owner._bound(timeout)

    async def _retrying(self, call: Callable[[], Awaitable[T]]) -> T:
        return await self._owner._retrying(call, self._owner._retries)
