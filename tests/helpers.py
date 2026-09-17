"""Test doubles and corpus loading, shared by every test module.

Every corpus assertion runs against BOTH clients. `ClientAdapter` drives the async one
through the synchronous surface so the corpus is written once: two bindings that disagree
with each other are exactly what the corpus exists to catch, and asserting only the sync
client would leave half of this library unchecked.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

import httpx
import pytest

from internetdata import AsyncInternetData, InternetData

TESTDATA: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parent.parent / "testdata" / "testdata.json").read_text()
)

API = "https://api.example"
API_KEY = "secret-key"

LIST_PATH = "/api/v2/database/list"
DOWNLOAD_PATH = "/api/v2/database/download"
METADATA_PATH = "/api/v2/database/metadata"
CHECKSUM_PATH = "/api/v2/database/checksum"
DOWNLOADS_PATH = "/api/v2/database/downloads"


class ClientFactory:
    """Builds clients of one flavor and closes every one of them afterwards."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._built: list[ClientAdapter] = []

    def __call__(self, **options: Any) -> ClientAdapter:
        adapter = ClientAdapter(self.kind, **options)
        self._built.append(adapter)
        return adapter

    def close_all(self) -> None:
        for adapter in self._built:
            adapter.close()


class ClientAdapter:
    """One synchronous surface over both clients.

    The download path is not one method shared by two clients: the async one writes each
    chunk from a worker thread rather than blocking the event loop, so it is genuinely
    different code and has to be asserted as such.
    """

    def __init__(self, kind: str, **options: Any) -> None:
        options.setdefault("api_key", API_KEY)
        options.setdefault("base_url", API)
        self.kind = kind
        self.client: InternetData | AsyncInternetData = (
            InternetData(**options) if kind == "sync" else AsyncInternetData(**options)
        )
        self.database = DatabaseAdapter(self.client)

    def close(self) -> None:
        if isinstance(self.client, InternetData):
            self.client.close()
        else:
            asyncio.run(self.client.aclose())


class DatabaseAdapter:
    """The `database` surface of whichever client this run is exercising."""

    def __init__(self, client: InternetData | AsyncInternetData) -> None:
        self._client = client

    def list(self) -> Any:
        return self._call("list")

    def metadata(self, database_id: str) -> Any:
        return self._call("metadata", database_id)

    def checksums(self, database_id: str, format: str) -> Any:
        return self._call("checksums", database_id, format)

    def downloads(self, *args: Any) -> Any:
        return self._call("downloads", *args)

    def download_url(self, database_id: str, format: str) -> Any:
        return self._call("download_url", database_id, format)

    def download(self, database_id: str, format: str, path: Any) -> Any:
        return self._call("download", database_id, format, path)

    def download_bytes(self, database_id: str, format: str) -> Any:
        return self._call("download_bytes", database_id, format)

    def _call(self, name: str, *args: Any) -> Any:
        method = getattr(self._client.database, name)
        if isinstance(self._client, InternetData):
            return method(*args)
        return asyncio.run(method(*args))


class Stub:
    """A transport that answers one route from a table and records every request.

    Keyed by path, so a test says what `/api/v2/database/list` answers without having to
    know how the client spells the query string. Recording the requests is what lets a
    test assert how MANY were made, which is the only way to tell a retry policy from an
    intention.
    """

    def __init__(self, routes: dict[str, dict[str, Any]]) -> None:
        self.routes = routes
        self.requests: list[httpx.Request] = []
        self.transport = httpx.MockTransport(self._handle)

    @property
    def calls(self) -> list[str]:
        return [str(request.url) for request in self.requests]

    def paths(self) -> list[str]:
        return [request.url.path for request in self.requests]

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        route = self.routes.get(request.url.path)
        if route is None:
            return httpx.Response(404, json={"rc": "UNKNOWN_DATASET"})
        return httpx.Response(
            route.get("status", 200), json=self._body(route), headers=route.get("headers")
        )

    def _served(self, path: str) -> int:
        return len([request for request in self.requests if request.url.path == path])

    def _body(self, route: dict[str, Any]) -> Any:
        """One body, or the next of several.

        A route carrying `bodies` answers them in order and then repeats the last, which
        is how a test says "the second key sees a different catalog" without standing up
        a second transport and losing the shared request record.
        """
        if "bodies" not in route:
            return route["body"]
        bodies = route["bodies"]
        return bodies[min(self._served(self.requests[-1].url.path) - 1, len(bodies) - 1)]


class LocalServer:
    """A real socket on 127.0.0.1, answering each connection's one request from a thread.

    What a deadline is tested against: `MockTransport` never consults a timeout. Past
    `MAX_REQUESTS` it stops accepting, so a retry loop that never ends waits for good instead
    of spinning, and `settle` fails the test from outside it.
    """

    MAX_REQUESTS = 20

    def __init__(self) -> None:
        self._listener = socket.create_server(("127.0.0.1", 0))
        self._listener.settimeout(0.05)
        host, port = self._listener.getsockname()[:2]
        self.url = f"http://{host}:{port}"
        self.paths: list[str] = []
        self.closed = threading.Event()
        threading.Thread(target=self._serve, daemon=True).start()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.closed.set()
        self._listener.close()

    def answer(self, conn: socket.socket, path: str) -> None:
        raise NotImplementedError

    def _serve(self) -> None:
        while not self.closed.is_set():
            if len(self.paths) >= self.MAX_REQUESTS:
                self.closed.wait(0.05)
                continue
            try:
                conn, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        with conn:
            try:
                conn.settimeout(3.0)
                request_line = conn.recv(65536).decode("latin-1").split("\r\n", 1)[0]
                path = request_line.split(" ")[1].split("?", 1)[0] if " " in request_line else ""
                self.paths.append(path)
                self.answer(conn, path)
            except OSError:
                return


class SlowBody(LocalServer):
    """Answers every request with a 200's headers and the first byte of its body, then a
    byte every `trickle` seconds, or nothing more when that is None.

    What httpx's own timeout cannot bound: it limits each read rather than the attempt, so a
    trickle faster than the bound resets it forever. Each response gives up after
    `for_at_most` seconds, so a client that stops honoring its bound fails its test instead
    of hanging the suite.
    """

    def __init__(self, trickle: float | None, for_at_most: float = 3.0) -> None:
        self._trickle = trickle
        self._for_at_most = for_at_most
        super().__init__()

    def answer(self, conn: socket.socket, path: str) -> None:
        give_up = time.monotonic() + self._for_at_most
        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: 100000\r\nConnection: close\r\n\r\n{"
        )
        gap = self._for_at_most if self._trickle is None else self._trickle
        while not self.closed.wait(gap) and time.monotonic() < give_up:
            if self._trickle is not None:
                conn.sendall(b" ")


class SlowTransfer(LocalServer):
    """The API's `302` to a blob on this same server, and that blob in two halves with
    `pause` seconds between them.

    A pause longer than a client's timeout outlasts it twice over: in total, and as the one
    gap between two reads. So neither a deadline over the transfer nor a bound on each read
    can pass unseen.
    """

    BODY = bytes(range(256)) * 64

    def __init__(self, pause: float) -> None:
        self._pause = pause
        super().__init__()

    def answer(self, conn: socket.socket, path: str) -> None:
        if path == DOWNLOAD_PATH:
            conn.sendall(
                f"HTTP/1.1 302 Found\r\nLocation: {self.url}/blob\r\n"
                "Content-Length: 0\r\nConnection: close\r\n\r\n".encode()
            )
            return
        half = len(self.BODY) // 2
        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
            + f"Content-Length: {len(self.BODY)}\r\nConnection: close\r\n\r\n".encode()
            + self.BODY[:half]
        )
        if not self.closed.wait(self._pause):
            conn.sendall(self.BODY[half:])


def settle(call: Callable[[], Any], within: float = 10.0) -> Any:
    """What `call` returned, or the exception it raised, run on a thread of its own so a
    call that never ends fails the test instead of hanging the suite."""
    outcome: list[Any] = []

    def run() -> None:
        try:
            outcome.append(call())
        except BaseException as exc:  # noqa: BLE001 - the outcome under test
            outcome.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(within)
    if worker.is_alive():
        pytest.fail(f"the call under test did not settle within {within}s")
    return outcome[0]


def database(base: str, **overrides: Any) -> dict[str, Any]:
    """One served catalog entry, in the wire shape, with the boring fields filled in."""
    entry: dict[str, Any] = {
        "base": base,
        "name": base.replace("_", " ").title(),
        "summary": f"{base} rows",
        "standing": "licensed",
        "license_type": "standard",
        "starts": "2026-01-01T00:00:00.000Z",
        "expires": None,
        "renews_at": None,
        "notice_due_at": None,
        "versions": [
            {
                "id": f"{base}_v1",
                "version": 1,
                "summary": f"{base} v1",
                "formats": ["csvgz", "mmdb"],
            }
        ],
    }
    entry.update(overrides)
    return entry
