"""The Python-specific API surface, as distinct from the shared conformance corpus."""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import inspect
import time
from collections.abc import Callable
from typing import Any, get_args

import attrs
import httpx
import pytest
from helpers import (
    API,
    API_KEY,
    CHECKSUM_PATH,
    DOWNLOADS_PATH,
    LIST_PATH,
    METADATA_PATH,
    ClientAdapter,
    ClientFactory,
    SlowBody,
    Stub,
    database,
    settle,
)

from internetdata import (
    AsyncInternetData,
    Database,
    DatabaseMetadata,
    DatabaseVersion,
    Download,
    InternetData,
    InternetDataError,
    MetadataColumn,
    Outcome,
    _core,
)
from internetdata._generated.models.database import Database as WireDatabase
from internetdata._generated.models.database_metadata import (
    DatabaseMetadata as WireDatabaseMetadata,
)
from internetdata._generated.models.database_metadata_column import (
    DatabaseMetadataColumn as WireDatabaseMetadataColumn,
)
from internetdata._generated.models.database_version import DatabaseVersion as WireDatabaseVersion
from internetdata._generated.models.download import Download as WireDownload
from internetdata._generated.models.download_outcome import DownloadOutcome as WireDownloadOutcome

METADATA = {
    "id": "bogon_ip_v1",
    "update_freq": "daily",
    "updated": "2026-09-04",
    "entries": 1234,
    "schema": {
        "csvgz": [
            {"name": "first_ip", "type": "string", "description": "First address"},
            {"name": "last_ip", "type": "string"},
        ]
    },
    "sample": {"csvgz": [{"first_ip": "10.0.0.0", "last_ip": "10.255.255.255"}]},
    "size": {"csvgz": 760, "mmdb": 3524},
}

DOWNLOADS = {
    "downloads": [
        {
            "dataset_id": "bogon_ip_v1",
            "format": "csvgz",
            "outcome": "ok",
            "bytes": 760,
            "http_status": 302,
            "apikey_id": "ak_1",
            "client_ip": "203.0.113.4",
            "user_agent": "curl/8.5.0",
            "created": "2026-09-04T10:00:00.000Z",
        },
        {
            "dataset_id": "vpn_ip_v1",
            "format": "mmdb",
            "outcome": "denied",
            "bytes": None,
            "http_status": 403,
            "apikey_id": None,
            "client_ip": None,
            "user_agent": None,
            "created": "2026-09-04T09:00:00.000Z",
        },
    ]
}

# Far under SlowBody's three seconds, so a client that ignores its bound fails on how long
# the call took rather than on the server giving up.
TIMEOUT = 0.3
# A byte every 20 ms, so no single read ever waits long enough for httpx's own bound.
TRICKLE = 0.02
# What starting a thread or an event loop may add to a deadline.
SLACK = 0.25

JSON_CALLS: dict[str, Callable[[ClientAdapter], Any]] = {
    "list": lambda client: client.database.list(),
    "metadata": lambda client: client.database.metadata("bogon_ip_v1"),
    "checksums": lambda client: client.database.checksums("bogon_ip_v1", "csvgz"),
    "downloads": lambda client: client.database.downloads(),
    "download_url": lambda client: client.database.download_url("bogon_ip_v1", "csvgz"),
}


def test_metadata_is_typed_rather_than_a_bag_of_strings(make_client: ClientFactory) -> None:
    stub = Stub({METADATA_PATH: {"body": METADATA}})
    client = make_client(transport=stub.transport)

    meta = client.database.metadata("bogon_ip_v1")

    assert meta.id == "bogon_ip_v1"
    # A date, not the wire's string: this is the whole reason the model layer exists.
    assert meta.updated == datetime.date(2026, 9, 4)
    assert meta.entries == 1234
    assert meta.update_freq == "daily"
    assert meta.size == {"csvgz": 760, "mmdb": 3524}
    assert [column.name for column in meta.schema["csvgz"]] == ["first_ip", "last_ip"]
    assert meta.schema["csvgz"][0].description == "First address"
    assert meta.schema["csvgz"][1].description is None, "an absent description is not a blank one"
    assert meta.sample["csvgz"][0]["first_ip"] == "10.0.0.0"
    assert meta.raw == METADATA, "raw is the wire object, for anything this spec predates"
    assert stub.requests[0].url.params["id"] == "bogon_ip_v1"


def test_a_refusal_is_listed_beside_a_success(make_client: ClientFactory) -> None:
    """A denial is what answers "it stopped working", so it has to survive the mapping
    with its nulls intact rather than being dropped or defaulted."""
    stub = Stub({DOWNLOADS_PATH: {"body": DOWNLOADS}})
    client = make_client(transport=stub.transport)

    attempts = client.database.downloads()

    assert [a.outcome for a in attempts] == ["ok", "denied"]
    assert attempts[0].bytes == 760
    assert attempts[0].created == datetime.datetime(2026, 9, 4, 10, 0, tzinfo=datetime.UTC)
    denied = attempts[1]
    assert denied.bytes is None, "a refusal moved no bytes, which is not zero bytes"
    assert denied.http_status == 403
    assert denied.apikey_id is None and denied.client_ip is None


def test_the_downloads_limit_reaches_the_wire(make_client: ClientFactory) -> None:
    stub = Stub({DOWNLOADS_PATH: {"body": DOWNLOADS}})
    client = make_client(transport=stub.transport)

    client.database.downloads(5)

    assert stub.requests[0].url.params["limit"] == "5"


def test_a_licence_with_no_end_date_reads_as_none(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"body": {"databases": [database("bogon_ip")]}}})
    client = make_client(transport=stub.transport)

    family = client.database.list()[0]

    assert family.starts == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    assert family.expires is None
    assert family.renews_at is None
    assert family.notice_due_at is None


def test_a_rolling_license_carries_its_renewal_dates(make_client: ClientFactory) -> None:
    served = database(
        "bogon_ip",
        renews_at="2027-01-01T00:00:00.000Z",
        notice_due_at="2026-10-02T00:00:00.000Z",
    )
    stub = Stub({LIST_PATH: {"body": {"databases": [served]}}})
    client = make_client(transport=stub.transport)

    family = client.database.list()[0]

    assert family.renews_at == datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC)
    assert family.notice_due_at == datetime.datetime(2026, 10, 2, tzinfo=datetime.UTC)


@pytest.mark.parametrize(
    ("wire", "ours"),
    [
        (WireDatabase, Database),
        (WireDatabaseVersion, DatabaseVersion),
        (WireDatabaseMetadata, DatabaseMetadata),
        (WireDatabaseMetadataColumn, MetadataColumn),
        (WireDownload, Download),
    ],
)
def test_every_field_the_pinned_spec_serves_is_on_the_model(wire: Any, ours: Any) -> None:
    """The staleness pin on the hand-written models.

    They parse the keys they name and nothing else, so a field a re-pin adds reaches the
    generated code and `raw` while the typed model never hears of it: `renews_at` and
    `notice_due_at` sat that way from the 2026-09-09 re-pin until 2.2.0. The generated
    classes come from the same pinned spec, which makes them the list to check against.
    The generator suffixes a name that shadows a builtin with `_`.
    """
    served = {f.name.rstrip("_") for f in attrs.fields(wire)} - {"additional_properties"}
    modeled = {f.name for f in dataclasses.fields(ours)} - {"raw"}
    assert served - modeled == set(), f"{ours.__name__} lacks what the spec serves"


def test_the_outcome_vocabulary_is_the_pinned_specs() -> None:
    """The staleness pin on `Outcome`, the one hand-written Literal the corpus does not
    carry: the generated enum comes from the same pinned spec, so a re-pin that adds an
    outcome turns this red instead of leaving the type a member short."""
    assert sorted(get_args(Outcome)) == sorted(member.value for member in WireDownloadOutcome)


def test_a_database_cannot_be_mutated(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"body": {"databases": [database("bogon_ip")]}}})
    client = make_client(transport=stub.transport)

    family = client.database.list()[0]

    with pytest.raises(dataclasses.FrozenInstanceError):
        family.standing = "licensed"


def test_a_malformed_body_is_the_servers_failure_not_a_traceback(
    make_client: ClientFactory,
) -> None:
    """A 200 missing a required key must not surface as a KeyError out of the model
    layer: the caller catches one exception type from this library, or none."""
    stub = Stub({LIST_PATH: {"body": {"databases": [{"base": "bogon_ip"}]}}})
    client = make_client(transport=stub.transport, retries=0)

    with pytest.raises(InternetDataError) as caught:
        client.database.list()

    assert caught.value.kind == "server_error"
    assert "malformed response" in caught.value.message


def test_a_server_error_is_retried_and_then_reported(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"status": 503, "body": {"rc": "UNAVAILABLE"}}})
    client = make_client(transport=stub.transport, retries=2)

    with pytest.raises(InternetDataError) as caught:
        client.database.list()

    assert caught.value.kind == "server_error"
    # One initial attempt plus two retries.
    assert len(stub.requests) == 3


def test_retries_are_configurable_on_the_client(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"status": 503, "body": {"rc": "UNAVAILABLE"}}})
    client = make_client(transport=stub.transport, retries=0)

    with pytest.raises(InternetDataError):
        client.database.list()

    assert len(stub.requests) == 1


def test_a_spent_quota_is_never_retried(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"status": 429, "body": {"rc": "QUOTA_EXCEEDED"}}})
    client = make_client(transport=stub.transport, retries=3)

    with pytest.raises(InternetDataError) as caught:
        client.database.list()

    # A 429 with no Retry-After is a spent allowance; knocking again cannot help.
    assert caught.value.kind == "quota_exceeded"
    assert len(stub.requests) == 1


def test_a_rate_limit_is_retried_and_honors_retry_after(make_client: ClientFactory) -> None:
    stub = Stub(
        {
            LIST_PATH: {
                "status": 429,
                "body": {"rc": "RATE_LIMITED"},
                "headers": {"Retry-After": "0"},
            }
        }
    )
    client = make_client(transport=stub.transport, retries=2)

    with pytest.raises(InternetDataError) as caught:
        client.database.list()

    assert caught.value.kind == "rate_limited"
    assert caught.value.retry_after_seconds == 0
    assert len(stub.requests) == 3


def test_a_transport_failure_surfaces_as_a_network_error() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with (
        InternetData(API_KEY, transport=httpx.MockTransport(refuse), retries=0) as client,
        pytest.raises(InternetDataError) as caught,
    ):
        client.database.list()

    assert caught.value.kind == "network"
    assert caught.value.retryable is True


@pytest.mark.parametrize("call", JSON_CALLS)
def test_the_timeout_bounds_a_trickling_body_on_every_json_call(
    make_client: ClientFactory, call: str
) -> None:
    with SlowBody(trickle=TRICKLE) as server:
        client = make_client(base_url=server.url, timeout=TIMEOUT, retries=0)
        elapsed, outcome = _timed(lambda: JSON_CALLS[call](client))

    _assert_timed_out(outcome)
    _assert_one_bound(elapsed)


# httpx's per-read bound catches a full stall on its own, so this passes without the
# deadline; the trickle above is what proves the deadline exists.
def test_a_body_that_stalls_after_its_headers_is_bounded(make_client: ClientFactory) -> None:
    with SlowBody(trickle=None) as server:
        client = make_client(base_url=server.url, timeout=TIMEOUT, retries=0)
        elapsed, outcome = _timed(client.database.list)

    _assert_timed_out(outcome)
    _assert_one_bound(elapsed)


def test_a_second_call_is_held_to_the_clients_bound_too(make_client: ClientFactory) -> None:
    with SlowBody(trickle=TRICKLE) as server:
        client = make_client(base_url=server.url, timeout=TIMEOUT, retries=0)
        first, first_outcome = _timed(client.database.list)
        second, second_outcome = _timed(client.database.list)

    _assert_timed_out(first_outcome)
    _assert_one_bound(first)
    _assert_timed_out(second_outcome)
    _assert_one_bound(second)


# The bound is on each ATTEMPT, so a retried call takes one bound per attempt in total.
def test_a_timed_out_attempt_is_retried_under_a_bound_of_its_own(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_core, "_BACKOFF_BASE", 0.0)
    with SlowBody(trickle=TRICKLE) as server:
        client = make_client(base_url=server.url, timeout=TIMEOUT, retries=1)
        elapsed, outcome = _timed(client.database.list)

    assert server.paths == [LIST_PATH, LIST_PATH], "a timed-out attempt was not retried"
    _assert_timed_out(outcome)
    assert 2 * TIMEOUT - 0.05 <= elapsed < 2 * TIMEOUT + SLACK, (
        f"two attempts took {elapsed:.2f}s, not one bound each"
    )


def test_the_default_timeout_is_thirty_seconds() -> None:
    for client in (InternetData, AsyncInternetData):
        assert inspect.signature(client).parameters["timeout"].default == 30


@pytest.mark.parametrize("client", [InternetData, AsyncInternetData])
@pytest.mark.parametrize("timeout", [0, -1, 0.0, float("nan"), float("inf"), "30", True])
def test_a_timeout_no_attempt_can_meet_is_refused_when_the_client_is_built(
    client: type[InternetData | AsyncInternetData], timeout: Any
) -> None:
    """Accepted, each of these failed every call instead, after the retries' backoff."""
    with pytest.raises(ValueError, match="timeout"):
        client(API_KEY, timeout=timeout)


@pytest.mark.parametrize("timeout", [None, 0.25, 1, 30])
def test_a_usable_timeout_builds_a_client(timeout: float | None) -> None:
    InternetData(API_KEY, timeout=timeout).close()
    asyncio.run(AsyncInternetData(API_KEY, timeout=timeout).aclose())


# Refused before the network, and never retried: a typo is the caller's, not a failure of
# the server's to wait out.
def test_an_unpublished_format_is_refused_before_any_request(make_client: ClientFactory) -> None:
    stub = Stub({CHECKSUM_PATH: {"body": {"checksums": {"sha256": "00"}}}})
    client = make_client(transport=stub.transport, retries=2)

    started = time.monotonic()
    with pytest.raises(ValueError, match="zip"):
        client.database.checksums("bogon_ip_v1", "zip")

    assert stub.requests == []
    assert time.monotonic() - started < 0.5, "the refusal was retried"


def test_the_base_url_is_overridable(make_client: ClientFactory) -> None:
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport)

    client.database.list()

    assert str(stub.requests[0].url) == f"{API}{LIST_PATH}"


# The generated decoder validates the spec's enums as it parses, so a `standing` added to
# the API after this client was generated is refused rather than passed through. Pinned as
# a limitation, not a feature: what matters is that it stays inside this library's one
# error type instead of arriving as a bare TypeError out of generated code.
def test_a_value_this_client_was_not_generated_for_stays_inside_the_error_type(
    make_client: ClientFactory,
) -> None:
    stub = Stub({LIST_PATH: {"body": {"databases": [database("bogon_ip", standing="trial")]}}})
    client = make_client(transport=stub.transport, retries=0)

    with pytest.raises(InternetDataError) as caught:
        client.database.list()

    assert caught.value.kind == "server_error"
    assert "trial" in caught.value.message, "the message does not say which value it choked on"


def _timed(call: Callable[[], Any]) -> tuple[float, Any]:
    """How long `call` took to settle, and what it settled with."""
    started = time.monotonic()
    outcome = settle(call)
    return time.monotonic() - started, outcome


def _assert_timed_out(outcome: Any) -> None:
    assert isinstance(outcome, InternetDataError), f"settled with {outcome!r}"
    assert outcome.kind == "network", outcome
    assert outcome.retryable is True


def _assert_one_bound(elapsed: float) -> None:
    assert TIMEOUT - 0.05 <= elapsed < TIMEOUT + SLACK, (
        f"gave up after {elapsed:.2f}s against a {TIMEOUT}s bound"
    )
