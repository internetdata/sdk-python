"""The Python-specific API surface, as distinct from the shared conformance corpus."""

from __future__ import annotations

import dataclasses
import datetime

import httpx
import pytest
from helpers import (
    API,
    API_KEY,
    DOWNLOADS_PATH,
    LIST_PATH,
    METADATA_PATH,
    ClientFactory,
    Stub,
    database,
)

from internetdata import InternetData, InternetDataError

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
