"""Test doubles and corpus loading, shared by every test module.

Every corpus assertion runs against BOTH clients. `ClientAdapter` drives the async one
through the synchronous surface so the corpus is written once: two bindings that disagree
with each other are exactly what the corpus exists to catch, and asserting only the sync
client would leave half of this library unchecked.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

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
