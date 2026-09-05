"""Asserts the shared conformance corpus that every InternetData SDK asserts.

The corpus is generated into testdata/ and is identical across languages, so a behavior
that drifts here fails here rather than surfacing as two client libraries quietly
disagreeing about the same response.
"""

from __future__ import annotations

import pytest
from helpers import (
    API_KEY,
    CHECKSUM_PATH,
    LIST_PATH,
    METADATA_PATH,
    TESTDATA,
    ClientFactory,
    Stub,
    database,
)

from internetdata import InternetDataError

# One live grant, one that has run out, and one never bought. Between them these cover
# every value the corpus pins for `standing` and `license_type`.
CATALOG = [
    database("bogon_ip", standing="licensed", license_type="redistribute"),
    database(
        "bogon_asn",
        standing="expired",
        license_type="evaluation",
        expires="2026-01-01T00:00:00.000Z",
    ),
    database("vpn_ip", standing="unlicensed", license_type=None, starts=None),
]


def test_every_error_shape_maps_to_the_same_kind_in_every_language(
    make_client: ClientFactory,
) -> None:
    for case in TESTDATA["errors"]:
        stub = Stub(
            {
                LIST_PATH: {
                    "status": case["status"],
                    "body": case["body"],
                    "headers": case["headers"],
                }
            }
        )
        # No retries, so a retryable error still surfaces rather than looping.
        client = make_client(transport=stub.transport, retries=0)
        name = case["name"]
        expect = case["expect"]

        with pytest.raises(InternetDataError) as caught:
            client.database.list()

        err = caught.value
        assert err.kind == expect["kind"], name
        assert err.retryable is expect["retryable"], f"{name}: retryable"
        assert err.status == case["status"], f"{name}: status"
        assert str(err) == expect["message"], f"{name}: message"
        if "retryAfterSeconds" in expect:
            assert err.retry_after_seconds == expect["retryAfterSeconds"], name


# The one that has caught three of four bindings: 404 is a CLIENT error. Mapping
# 400/401/403/429 by name and letting the rest fall through to a retryable server_error
# means an unknown database id is asked for three times before failing.
def test_a_404_is_never_retried(make_client: ClientFactory) -> None:
    for case in TESTDATA["errors"]:
        if case["status"] != 404:
            continue
        stub = Stub({METADATA_PATH: {"status": 404, "body": case["body"]}})
        client = make_client(transport=stub.transport, retries=3)

        with pytest.raises(InternetDataError) as caught:
            client.database.metadata("nope_v1")

        assert caught.value.retryable is False, case["name"]
        assert len(stub.requests) == 1, f"{case['name']}: issued {len(stub.requests)} requests"


# Both arrive as 429 and the header is the only thing separating them, so a client that
# reads the status alone either hammers a spent allowance or gives up on a transient one.
def test_the_two_429s_differ_only_by_retry_after(make_client: ClientFactory) -> None:
    cases = {case["expect"]["kind"]: case for case in TESTDATA["errors"] if case["status"] == 429}
    assert set(cases) == {"rate_limited", "quota_exceeded"}, "the corpus lost one of the 429s"

    for kind, case in cases.items():
        stub = Stub({LIST_PATH: {"status": 429, "body": case["body"], "headers": case["headers"]}})
        client = make_client(transport=stub.transport, retries=1)

        with pytest.raises(InternetDataError) as caught:
            client.database.list()

        assert caught.value.kind == kind
        expected_requests = 2 if kind == "rate_limited" else 1
        assert len(stub.requests) == expected_requests, (
            f"{kind}: made {len(stub.requests)} requests, expected {expected_requests}"
        )


def test_the_catalog_carries_every_standing_and_license_type_the_corpus_pins(
    make_client: ClientFactory,
) -> None:
    stub = Stub({LIST_PATH: {"body": {"databases": CATALOG}}})
    client = make_client(transport=stub.transport)

    families = client.database.list()

    assert [f.base for f in families] == [entry["base"] for entry in CATALOG], (
        "the served order is the answer's order"
    )
    assert {f.standing for f in families} == set(TESTDATA["standings"])
    served_rights = {f.license_type for f in families if f.license_type is not None}
    assert served_rights <= set(TESTDATA["license_type"]), (
        f"undocumented license_type right in {served_rights}"
    )
    # Null when there is no licence, which is a different answer from any of the three.
    assert [f.license_type for f in families][-1] is None
    for family in families:
        assert family.versions, f"{family.base} carries no versions"
        for version in family.versions:
            assert set(version.formats) <= set(TESTDATA["formats"]), (
                f"{version.id} claims a format outside the documented set"
            )


# The visibility contract. A private family is one commissioned for a single customer: the
# server leaves it out of the listing entirely for anyone else, rather than including it
# with standing 'unlicensed'. All this library has to do is not undo that, which is a real
# assertion because the plausible mistakes all involve the client adding something.
def test_the_listing_is_returned_exactly_as_served(make_client: ClientFactory) -> None:
    assert "listing-is-returned-as-served" in TESTDATA["visibility"]["clientRules"]
    stub = Stub({LIST_PATH: {"body": {"databases": CATALOG}}})
    client = make_client(transport=stub.transport)

    families = client.database.list()

    assert len(families) == len(CATALOG), "the client added or dropped an entry"
    assert [f.raw for f in families] == CATALOG, "an entry is not the object the server sent"


def test_no_catalog_is_compiled_into_the_client(make_client: ClientFactory) -> None:
    """An empty listing must stay empty.

    This is the mistake worth guarding: a client that knows the published database ids -
    from a bundled table, an enum, or a merge with anything - would hand back a family the
    server deliberately withheld, and the leak answers 200 while moving no bytes.
    """
    assert "no-catalog-is-compiled-into-the-client" in TESTDATA["visibility"]["clientRules"]
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport)

    assert client.database.list() == []


def test_a_listing_is_never_reused_across_clients(make_client: ClientFactory) -> None:
    """Two keys are two organizations, and they do not see the same catalog.

    So there is no listing cache at all here, per instance or otherwise: a cached one
    would be wrong the moment a licence is granted, and a shared one would show an
    organization a family it is not allowed to know exists.
    """
    assert "a-listing-is-never-reused-across-clients" in TESTDATA["visibility"]["clientRules"]
    stub = Stub({LIST_PATH: {"bodies": [{"databases": CATALOG}, {"databases": []}]}})
    first = make_client(transport=stub.transport, api_key="key-a")
    second = make_client(transport=stub.transport, api_key="key-b")

    assert len(first.database.list()) == len(CATALOG)
    assert second.database.list() == [], "the second key answered from the first one's listing"
    assert len(stub.requests) == 2
    # A repeat on the SAME client asks again too: a licence granted between two calls has
    # to show up.
    first.database.list()
    assert len(stub.requests) == 3


def test_checksums_unwrap_past_the_envelope(make_client: ClientFactory) -> None:
    """`checksums` nests under a key, beside `id` and `format`.

    Reading a top-level `sha256` finds nothing and shipped broken in another binding's
    1.0.x, so the depth is pinned rather than assumed.
    """
    digests = {"md5": "m", "sha1": "s1", "sha256": "s256", "sha512": "s512"}
    stub = Stub(
        {CHECKSUM_PATH: {"body": {"id": "bogon_ip_v1", "format": "csvgz", "checksums": digests}}}
    )
    client = make_client(transport=stub.transport)

    assert client.database.checksums("bogon_ip_v1", "csvgz") == digests


def test_the_api_key_reaches_the_wire_under_the_bearer_scheme(
    make_client: ClientFactory,
) -> None:
    """Deleting the auth header, or sending it under the wrong scheme, passed a whole
    suite in another language until something mutated it."""
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport)

    client.database.list()

    assert stub.requests[0].headers.get("authorization") == f"Bearer {API_KEY}"


@pytest.mark.parametrize("api_key", [None, ""])
def test_a_keyless_client_sends_no_authorization_header(
    make_client: ClientFactory, api_key: str | None
) -> None:
    """The key is optional because what this API serves without a licence is a product
    decision, and a client that could not be built without one would have to change
    shape to follow it. What must never go out is `Bearer ` with nothing after it, which
    reads as a wrong key rather than as none.
    """
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport, api_key=api_key)

    client.database.list()

    assert "authorization" not in stub.requests[0].headers
