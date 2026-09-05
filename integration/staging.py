"""The staging fixtures the test files share: the gate that keeps this suite honest, the
clients, and the request record that proves where the key went.

Everything here imports the PUBLISHED package, so nothing in it may be read before pip has
run. The credential itself lives in `credential.py`, which the runner can read on an empty
virtualenv.
"""

from __future__ import annotations

import importlib.metadata
import json
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from credential import STAGING, key, skip_reason

from internetdata import AsyncInternetData, InternetData

PACKAGE = "internetdata"


def assert_published_artifact() -> None:
    """Refuse to run against the working tree.

    This suite exists to test the artifact a stranger installs, and running it against
    local source is the one failure that is completely silent: every test passes, against
    code no consumer has. Two ways that happens, and each is ruled out here.

    The import resolves inside this repository's own `src`, which is what a stray
    PYTHONPATH or an editable install gives you. Note the test is `src` rather than the
    repository, because the virtualenv the runner builds lives under `integration/` and is
    exactly where a legitimate install lands.

    Or the distribution came from a path rather than a registry, which is a locally built
    wheel passed off as a release. Nothing about the installed files would show that; pip
    records it in `direct_url.json`, which a registry install does not write at all.
    """
    module = __import__(PACKAGE)
    where = Path(module.__file__ or "").resolve()
    source = Path(__file__).resolve().parent.parent / "src"
    if source in where.parents:
        pytest.exit(f"{PACKAGE} imports from {where}, which is this repository's own source", 1)

    direct = importlib.metadata.distribution(PACKAGE).read_text("direct_url.json")
    if direct is None:
        return
    url = json.loads(direct).get("url", "")
    if not url.startswith("https://"):
        pytest.exit(f"{PACKAGE} was installed from {url}, which is not a registry", 1)


@dataclass(frozen=True)
class Fact:
    """What a test is allowed to remember about a request it made.

    Only derived facts leave here. An assertion that fails prints its operands, so holding
    on to the request itself is how a key ends up in a public CI log: whether the key was
    carried is a boolean, and the caller never sees the key.
    """

    origin: str
    path: str
    carried_key: bool


class Recorder(httpx.BaseTransport):
    """The real transport, remembering what it was asked for.

    One instance serves both the API client and the credential-free one the download path
    uses, so a single record holds the request that must carry the key and the request
    that must not.
    """

    def __init__(self, api_key: str) -> None:
        self.key = api_key
        self.facts: list[Fact] = []
        self._inner = httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.facts.append(fact_for(request, self.key))
        return self._inner.handle_request(request)

    def close(self) -> None:
        self._inner.close()

    def storage_facts(self) -> list[Fact]:
        """The requests that went somewhere other than the API, which is the transfer."""
        return [fact for fact in self.facts if fact.origin != STAGING]


class AsyncRecorder(httpx.AsyncBaseTransport):
    """`Recorder`, for the asyncio client."""

    def __init__(self, api_key: str) -> None:
        self.key = api_key
        self.facts: list[Fact] = []
        self._inner = httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.facts.append(fact_for(request, self.key))
        return await self._inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self._inner.aclose()

    def storage_facts(self) -> list[Fact]:
        return [fact for fact in self.facts if fact.origin != STAGING]


def fact_for(request: httpx.Request, api_key: str) -> Fact:
    carried = api_key != "" and (
        api_key in request.url.query.decode()
        or any(api_key in value for value in request.headers.values())
    )
    return Fact(
        origin=f"{request.url.scheme}://{request.url.netloc.decode()}",
        path=request.url.path,
        carried_key=carried,
    )


def client() -> tuple[InternetData, Recorder]:
    """A client of its own per test, so one test's request record cannot be read through
    another's. Skips rather than fails when there is no key to run with."""
    reason = skip_reason()
    if reason:
        pytest.skip(reason)
    recorder = Recorder(key())
    return InternetData(key(), base_url=STAGING, transport=recorder), recorder


def async_client() -> tuple[AsyncInternetData, AsyncRecorder]:
    recorder = AsyncRecorder(key())
    return AsyncInternetData(key(), base_url=STAGING, transport=recorder), recorder
