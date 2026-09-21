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
from typing import Any, NoReturn, Self

import httpx
import pytest

from internetdata import AsyncInternetData, InternetData
from internetdata._core import AsyncClock, Clock

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
        self.oauth = OauthAdapter(self.client)

    def close(self) -> None:
        if isinstance(self.client, InternetData):
            self.client.close()
        else:
            asyncio.run(self.client.aclose())


class DatabaseAdapter:
    """The `database` surface of whichever client this run is exercising."""

    def __init__(self, client: InternetData | AsyncInternetData) -> None:
        self._client = client

    def list(self, **kwargs: Any) -> Any:
        return self._call("list", **kwargs)

    def metadata(self, database_id: str, **kwargs: Any) -> Any:
        return self._call("metadata", database_id, **kwargs)

    def checksums(self, database_id: str, format: str, **kwargs: Any) -> Any:
        return self._call("checksums", database_id, format, **kwargs)

    def downloads(self, *args: Any, **kwargs: Any) -> Any:
        return self._call("downloads", *args, **kwargs)

    def download_url(self, database_id: str, format: str, **kwargs: Any) -> Any:
        return self._call("download_url", database_id, format, **kwargs)

    def download(self, database_id: str, format: str, path: Any, **kwargs: Any) -> Any:
        return self._call("download", database_id, format, path, **kwargs)

    def download_bytes(self, database_id: str, format: str, **kwargs: Any) -> Any:
        return self._call("download_bytes", database_id, format, **kwargs)

    # Keyword arguments are forwarded untouched and none is named here: a `timeout`
    # in this signature would swallow the TypeError a transfer must raise for one.
    def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        method = getattr(self._client.database, name)
        if isinstance(self._client, InternetData):
            return method(*args, **kwargs)
        return asyncio.run(method(*args, **kwargs))


class OauthAdapter:
    """The `oauth` surface of whichever client this run is exercising."""

    def __init__(self, client: InternetData | AsyncInternetData) -> None:
        self._client = client

    def use_clock(self, clock: FakeClock) -> None:
        if isinstance(self._client, InternetData):
            self._client.oauth._clock = clock
        else:
            self._client.oauth._clock = AsyncFakeClock(clock)

    def metadata(self, **kwargs: Any) -> Any:
        return self._call("metadata", **kwargs)

    def device_authorization(self, client_id: str, **kwargs: Any) -> Any:
        return self._call("device_authorization", client_id, **kwargs)

    def exchange_device_code(self, client_id: str, device_code: str, **kwargs: Any) -> Any:
        return self._call("exchange_device_code", client_id, device_code, **kwargs)

    def exchange_refresh_token(self, client_id: str, refresh_token: str, **kwargs: Any) -> Any:
        return self._call("exchange_refresh_token", client_id, refresh_token, **kwargs)

    def revoke(self, client_id: str, token: str, **kwargs: Any) -> Any:
        return self._call("revoke", client_id, token, **kwargs)

    def poll_device_token(self, client_id: str, device: Any, **kwargs: Any) -> Any:
        return self._call("poll_device_token", client_id, device, **kwargs)

    def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        method = getattr(self._client.oauth, name)
        if isinstance(self._client, InternetData):
            return method(*args, **kwargs)
        return asyncio.run(method(*args, **kwargs))


# Past this many requests, waits or clock reads, a loop under test fails its test.
LOOP_BOUND = 16


class LoopBound:
    """Ends a test whose code under test does not end.

    Past its cap a stub or a fake clock calls `trip`, which BLOCKS for good rather than
    raising: an exception can be swallowed by the very loop it is meant to stop, a wait
    cannot. `settle` notices the trip and fails the test from outside the call.
    """

    def __init__(self) -> None:
        self.why = ""
        self.tripped = threading.Event()

    def trip(self, why: str) -> NoReturn:
        self.why = why
        self.tripped.set()
        threading.Event().wait()
        raise AssertionError("unreachable")


def settle(call: Callable[[], Any], bound: LoopBound | None = None, within: float = 10.0) -> Any:
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
    give_up = time.monotonic() + within
    while worker.is_alive():
        if bound is not None and bound.tripped.is_set():
            pytest.fail(f"{bound.why}: the call under test does not end")
        if time.monotonic() > give_up:
            pytest.fail(f"the call under test did not settle within {within}s")
        worker.join(0.02)
    return outcome[0]


class FakeClock(Clock):
    """A poll's sleep and monotonic clock, replaced together, recording every wait in
    seconds. Past LOOP_BOUND waits, or twice that many clock reads, it trips `bound`."""

    def __init__(self, bound: LoopBound) -> None:
        self.waits: list[float] = []
        self._elapsed = 0.0
        self._reads = 0
        self._bound = bound

    def now(self) -> float:
        self._reads += 1
        if self._reads > 2 * LOOP_BOUND:
            self._bound.trip(f"read the clock {self._reads} times")
        return self._elapsed

    def sleep(self, seconds: float) -> None:
        if len(self.waits) == LOOP_BOUND:
            self._bound.trip(f"waited more than {LOOP_BOUND} times")
        self.waits.append(seconds)
        self._elapsed += seconds


class AsyncFakeClock(AsyncClock):
    """`FakeClock`, for the async client."""

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock

    def now(self) -> float:
        return self._clock.now()

    async def sleep(self, seconds: float) -> None:
        self._clock.sleep(seconds)


class OauthStub:
    """Answers from a list of replies in order, repeating the last, and keeps every request
    that left the client. Past `limit` requests it trips `bound` rather than answering."""

    def __init__(
        self, replies: list[dict[str, Any]], bound: LoopBound, limit: int = LOOP_BOUND
    ) -> None:
        self.requests: list[httpx.Request] = []
        self.transport = httpx.MockTransport(self._handle)
        self._replies = replies
        self._bound = bound
        self._limit = limit

    def _handle(self, request: httpx.Request) -> httpx.Response:
        if len(self.requests) == self._limit:
            self._bound.trip(f"sent more than {self._limit} request(s)")
        self.requests.append(request)
        reply = self._replies[min(len(self.requests), len(self._replies)) - 1]
        body = reply["rawBody"] if "rawBody" in reply else json.dumps(reply["body"])
        return httpx.Response(
            reply["status"], content=body.encode(), headers={"content-type": "application/json"}
        )


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
