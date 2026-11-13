"""Asserts the shared conformance corpus that every InternetData SDK asserts.

The corpus is generated into testdata/ and is identical across languages, so a behavior
that drifts here fails here rather than surfacing as two client libraries quietly
disagreeing about the same response.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from helpers import (
    API_KEY,
    CHECKSUM_PATH,
    LIST_PATH,
    METADATA_PATH,
    TESTDATA,
    ClientAdapter,
    ClientFactory,
    Lookups,
    Stub,
    answer,
    as_wire,
    database,
)

from internetdata import (
    DATABASE_FORMATS,
    DEFAULT_BASE_URL,
    LICENSE_TYPES,
    STANDINGS,
    InternetDataError,
    Result,
    is_bogon,
)

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


# A lookup refusal carries its message in `error` and a database refusal in `rc`; each is
# read whichever call it answers, so every case runs against both.
ERROR_CALLS: dict[str, tuple[str, Callable[[ClientAdapter], Any]]] = {
    "lookup": ("/1.1.1.1", lambda client: client.lookup("1.1.1.1")),
    "database": (LIST_PATH, lambda client: client.database.list()),
}


@pytest.mark.parametrize("call", ERROR_CALLS)
def test_every_error_shape_maps_to_the_same_kind_in_every_language(
    make_client: ClientFactory, call: str
) -> None:
    path, send = ERROR_CALLS[call]
    for case in TESTDATA["errors"]:
        stub = Stub(
            {path: {"status": case["status"], "body": case["body"], "headers": case["headers"]}}
        )
        # No retries, so a retryable error still surfaces rather than looping.
        client = make_client(transport=stub.transport, retries=0)
        name = case["name"]
        expect = case["expect"]

        with pytest.raises(InternetDataError) as caught:
            send(client)

        err = caught.value
        assert err.kind == expect["kind"], name
        assert err.retryable is expect["retryable"], f"{name}: retryable"
        assert err.status == case["status"], f"{name}: status"
        if "message" in expect:
            assert str(err) == expect["message"], f"{name}: message"
        if "retryAfterSeconds" in expect:
            assert err.retry_after_seconds == expect["retryAfterSeconds"], name


# The one that has caught three of four bindings: every 4xx but a 429 carrying Retry-After
# is the CALLER's, and classifying by an enumerated list lets the rest (the corpus's 422)
# fall through to a retryable server_error. Asserted with retries ON and by counting
# requests: with retries off, one request is guaranteed and a wrong classifier passes.
@pytest.mark.parametrize("call", ["lookup", "database"])
def test_no_client_error_is_ever_retried(make_client: ClientFactory, call: str) -> None:
    cases = [case for case in TESTDATA["errors"] if not case["expect"]["retryable"]]
    assert any(case["name"] == "unlisted-4xx-is-not-retryable" for case in cases)
    path = "/1.1.1.1" if call == "lookup" else METADATA_PATH

    for case in cases:
        stub = Stub(
            {path: {"status": case["status"], "body": case["body"], "headers": case["headers"]}}
        )
        client = make_client(transport=stub.transport, retries=3)

        with pytest.raises(InternetDataError) as caught:
            if call == "lookup":
                client.lookup("1.1.1.1")
            else:
                client.database.metadata("nope_v1")

        # The count first: a retried case also ends on an error, just a later one.
        assert len(stub.requests) == 1, f"{case['name']}: issued {len(stub.requests)} requests"
        assert caught.value.kind == case["expect"]["kind"], case["name"]


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


def test_is_bogon_matches_the_canonical_ranges() -> None:
    for case in TESTDATA["isBogon"]:
        assert is_bogon(case["ip"]) is case["expect"], f"{case['ip']} ({case['why']})"


# A server listening on :: sees an IPv4 visitor as ::ffff:a.b.c.d, which read whole is
# inside ::ffff:0:0/96: an SDK that does not unmap answers every such visitor as a bogon.
def test_an_ipv4_mapped_address_is_the_ipv4_address_it_carries(
    make_client: ClientFactory,
) -> None:
    for case in TESTDATA["ipv4Mapped"]:
        ip, carries, bogon = case["ip"], case["carries"], case["expect"]
        assert is_bogon(ip) is bogon, f"{ip} ({case['why']})"
        routes = {carries: {"body": answer(carries)}}

        stub = Lookups(routes)
        client = make_client(transport=stub.transport)
        result = client.lookup(ip)
        assert result.is_bogon is bogon, ip
        assert result.ip == carries, ip
        client.lookup(carries)
        assert len(stub.calls) == (0 if bogon else 1), f"{ip}: one request, cached as {carries}"

        # The stub knows only the carried address, so the mapped form alone answers only
        # if the carried one was sent.
        batch_stub = Lookups(routes)
        uncached = make_client(transport=batch_stub.transport, cache=False)
        alone = uncached.lookup_batch([ip])
        assert list(alone) == [ip], ip
        found = alone[ip]
        assert isinstance(found, Result) and found.ip == carries, f"{ip}: {found!r}"
        asked = list(dict.fromkeys([ip, carries]))
        both = uncached.lookup_batch(asked)
        assert list(both) == asked, ip
        assert len(batch_stub.calls) == (0 if bogon else 2), ip


def test_a_bogon_is_answered_locally_in_the_full_paid_shape(make_client: ClientFactory) -> None:
    stub = Lookups({})
    client = make_client(transport=stub.transport)
    result = client.lookup("10.0.0.1")
    shape = TESTDATA["bogonResponse"]

    assert result.is_bogon is True
    assert result.ip == "10.0.0.1"
    for flag in shape["flagsFalse"]:
        assert getattr(result, flag) is False, f"{flag} must be present and false"
    for name in shape["emptyObjects"]:
        detail = getattr(result, name)
        assert detail is not None and as_wire(detail) == {}, f"{name} must be present and empty"
    for name in shape["emptyLists"]:
        assert getattr(result, name) == (), f"{name} must be present and empty"
    for name in ("location", "asn", "company", "abuse", "whois", "rwhois"):
        assert as_wire(getattr(result, name)) == shape[name], f"{name} must carry every key, empty"
    assert result.hostname == shape["hostname"]
    assert as_wire(result.hosted_domains) == shape["hostedDomains"]
    assert as_wire(result) == {**shape["answer"], "ip": "10.0.0.1"}
    assert stub.calls == [], "a bogon must not reach the network"


LOOKUP_CALLS: dict[str, tuple[Callable[[Any], str], str]] = {
    "lookup": (lambda target: f"/{target}", "lookup"),
    "lookupAsn": (lambda target: f"/asn/{target}", "lookup_asn"),
    "lookupDomain": (lambda target: f"/domain/{target}", "lookup_domain"),
}


@pytest.mark.parametrize("case", TESTDATA["lookup"], ids=lambda case: case["name"])
def test_a_lookup_preserves_absent_versus_false_across_every_plan_shape(
    make_client: ClientFactory, case: dict[str, Any]
) -> None:
    path, method = LOOKUP_CALLS[case["call"]]
    body = case["body"]
    stub = Stub({path(case["target"]): {"status": case["status"], "body": body}})
    client = make_client(transport=stub.transport)
    expect = case["expect"]

    result = getattr(client, method)(case["target"])

    assert result.raw == body, "raw must be the wire object"
    for key, value in expect["present"].items():
        assert as_wire(getattr(result, key)) == value, f"{key} should be {value!r}"
        if isinstance(value, bool):
            assert getattr(result, key) is value, f"{key} must be a bool"
    for key in expect["objects"]:
        assert as_wire(getattr(result, key)) == body[key], f"{key} must read as served"
    for key in expect["empty"]:
        assert as_wire(getattr(result, key)) in ({}, []), f"{key} must be present and empty"
    for key in expect["absent"]:
        assert getattr(result, key) is None, f"{key} must be ABSENT, not false"
        if key.startswith("is_") and isinstance(result, Result):
            assert result.flagged(key) is False, f"{key} must coalesce to false"
    for name, members in expect.get("absentIn", {}).items():
        for member in members:
            assert getattr(getattr(result, name), member) is None, f"{name}.{member} must be ABSENT"
    assert as_wire(result) == body, "every member must read back as served"


def test_batch_dedupes_short_circuits_bogons_and_keys_by_address(
    make_client: ClientFactory,
) -> None:
    case = _batch_case("dedup-bogon-and-order-free-keying")
    stub = Lookups({ip: {"body": answer(ip)} for ip in case["input"]})
    client = make_client(transport=stub.transport)

    out = client.lookup_batch(case["input"])

    assert list(out) == case["expect"]["keys"], "keys follow first-seen order"
    assert len(stub.calls) == case["expect"]["httpRequests"]
    assert stub.calls[0].startswith("POST "), "a batch is one POST, not a request per address"
    for ip in case["expect"]["bogonKeys"]:
        found = out[ip]
        assert isinstance(found, Result) and found.is_bogon, ip


def test_one_bad_address_does_not_lose_the_rest_of_the_batch(make_client: ClientFactory) -> None:
    case = _batch_case("partial-failure-does-not-fail-the-batch")
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport)

    out = client.lookup_batch(case["input"])

    assert list(out) == case["expect"]["keys"]
    for ip in case["expect"]["errorKeys"]:
        err = out[ip]
        assert isinstance(err, InternetDataError), ip
        assert err.kind == case["expect"]["errorKinds"][ip]
    assert isinstance(out["1.1.1.1"], Result)


def test_a_cache_hit_issues_no_second_request(make_client: ClientFactory) -> None:
    case = _batch_case("cache-hit-issues-no-second-request")
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport)

    for _ in range(case["repeat"]):
        out = client.lookup_batch(case["input"])

    assert list(out) == case["expect"]["keys"]
    assert len(stub.calls) == case["expect"]["httpRequests"]


@pytest.mark.parametrize("name", ["chunks-of-one-thousand", "uncapped-input-is-chunked"])
def test_a_large_batch_is_sent_in_chunks_of_a_thousand(
    make_client: ClientFactory, name: str
) -> None:
    case = _batch_case(name)
    stub = Lookups({ip: {"body": answer(ip)} for ip in case["input"]})
    client = make_client(transport=stub.transport)

    out = client.lookup_batch(case["input"])

    assert len(stub.calls) == case["expect"]["httpRequests"], "one POST per chunk of 1000"
    assert list(out) == case["input"], "every address answered exactly once"
    assert all(isinstance(result, Result) for result in out.values())


def test_an_entry_error_is_classified_by_its_status(make_client: ClientFactory) -> None:
    case = _batch_case("an-entry-error-is-classified-by-its-status")
    stub = Lookups(
        {
            "1.1.1.1": {"body": answer("1.1.1.1")},
            "8.8.8.8": {"status": 429, "body": {"error": "monthly quota exceeded"}},
            "9.9.9.9": {"status": 500, "body": {"error": "lookup failed"}},
        }
    )
    client = make_client(transport=stub.transport, retries=2)

    out = client.lookup_batch(case["input"])

    assert list(out) == case["expect"]["keys"]
    assert len(stub.calls) == case["expect"]["httpRequests"], "an entry error is never retried"
    for ip, kind in case["expect"]["errorKinds"].items():
        err = out[ip]
        assert isinstance(err, InternetDataError), ip
        assert err.kind == kind, ip
    assert isinstance(out["1.1.1.1"], Result)


def test_two_clients_never_share_a_cached_answer(make_client: ClientFactory) -> None:
    first = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    second = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})

    make_client(transport=first.transport).lookup("1.1.1.1")
    make_client(transport=second.transport).lookup("1.1.1.1")

    assert len(first.calls) == 1
    assert len(second.calls) == 1, "a second client must not read the first one's cache"


def test_caching_can_be_turned_off(make_client: ClientFactory) -> None:
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport, cache=False)

    client.lookup("1.1.1.1")
    client.lookup("1.1.1.1")

    assert len(stub.calls) == 2


def test_the_default_base_url_is_the_api_host() -> None:
    assert DEFAULT_BASE_URL == "https://api.internetdata.io"


def _batch_case(name: str) -> dict[str, Any]:
    (case,) = [case for case in TESTDATA["batch"] if case["name"] == name]
    found: dict[str, Any] = case
    return found


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
    # Null when there is no license, which is a different answer from any of the three.
    assert [f.license_type for f in families][-1] is None
    for family in families:
        assert family.versions, f"{family.base} carries no versions"
        for version in family.versions:
            assert set(version.formats) <= set(TESTDATA["formats"]), (
                f"{version.id} claims a format outside the documented set"
            )


def test_the_runtime_vocabularies_are_the_pinned_specs() -> None:
    """The staleness pin on three hand-written Literals.

    `emit.mjs` reads the corpus's lists out of the pinned spec, so a re-pin that widens a
    vocabulary turns this red instead of leaving a published value unnamed here.
    """
    assert sorted(DATABASE_FORMATS) == sorted(TESTDATA["formats"])
    assert sorted(STANDINGS) == sorted(TESTDATA["standings"])
    assert sorted(LICENSE_TYPES) == sorted(TESTDATA["license_type"])


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

    This is the mistake worth guarding: a client that knows the published database IDs -
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
    would be wrong the moment a license is granted, and a shared one would show an
    organization a family it is not allowed to know exists.
    """
    assert "a-listing-is-never-reused-across-clients" in TESTDATA["visibility"]["clientRules"]
    stub = Stub({LIST_PATH: {"bodies": [{"databases": CATALOG}, {"databases": []}]}})
    first = make_client(transport=stub.transport, api_key="key-a")
    second = make_client(transport=stub.transport, api_key="key-b")

    assert len(first.database.list()) == len(CATALOG)
    assert second.database.list() == [], "the second key answered from the first one's listing"
    assert len(stub.requests) == 2
    # A repeat on the SAME client asks again too: a license granted between two calls has
    # to show up.
    first.database.list()
    assert len(stub.requests) == 3


# Each visibility rule the corpus names, and the test above that holds it. The three tests
# each check that their own rule is still in the corpus; this checks the other direction,
# so a rule added to the corpus fails here until something in this module holds it.
VISIBILITY_RULES = {
    "listing-is-returned-as-served": test_the_listing_is_returned_exactly_as_served,
    "no-catalog-is-compiled-into-the-client": test_no_catalog_is_compiled_into_the_client,
    "a-listing-is-never-reused-across-clients": test_a_listing_is_never_reused_across_clients,
}


def test_every_visibility_rule_in_the_corpus_is_held_here() -> None:
    rules = TESTDATA["visibility"]["clientRules"]
    assert rules, "the corpus pins no visibility rules"
    unheld = sorted(set(rules) - set(VISIBILITY_RULES))
    assert unheld == [], f"the corpus adds {unheld} and this suite does not check it"


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


@pytest.mark.parametrize("api_key", [None, "", "   ", "\t", "\r\n"])
def test_a_keyless_client_sends_no_authorization_header(
    make_client: ClientFactory, api_key: str | None
) -> None:
    """The key is optional because what this API serves without a license is a product
    decision, and a client that could not be built without one would have to change
    shape to follow it. What must never go out is `Bearer ` with nothing after it, which
    reads as a wrong key rather than as none.
    """
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport, api_key=api_key)

    client.database.list()

    assert "authorization" not in stub.requests[0].headers


def test_the_api_key_is_trimmed(make_client: ClientFactory) -> None:
    """A key pasted with a line ending around it went out padded, which httpx refuses, so
    every call failed as a retried network error with nothing sent (2.7.1)."""
    stub = Stub({LIST_PATH: {"body": {"databases": []}}})
    client = make_client(transport=stub.transport, api_key=f" {API_KEY}\r\n")

    client.database.list()

    assert stub.requests[0].headers.get("authorization") == f"Bearer {API_KEY}"


@pytest.mark.parametrize(
    "api_key", ["key\r\nX-Injected: 1", "ke\ty", "key\x00", "key\x7f", "k\ney", "k\x85ey", "kéy"]
)
def test_a_control_character_or_one_outside_ascii_is_refused_where_the_key_is_set(
    make_client: ClientFactory, api_key: str
) -> None:
    """Accepted, a CR, LF or NUL failed every call as a retried network error with nothing
    sent, and a tab or DEL went out on the wire inside the header (2.7.1). A C1 control or
    any other character outside ASCII failed every call with a raw UnicodeEncodeError and
    nothing sent, since httpx encodes a header value as ASCII (2.7.3)."""
    with pytest.raises(ValueError, match="control character or one outside ASCII"):
        make_client(api_key=api_key)


@pytest.mark.parametrize("slashes", [1, 2, 3])
def test_every_trailing_slash_on_the_base_url_is_dropped(
    make_client: ClientFactory, slashes: int
) -> None:
    """httpx drops one when it joins a path on and keeps the rest, so through 2.7.3 a
    second reached the API as `//api/v2/database/list`, which prod answers with a
    redirect this client does not follow."""
    digests = {"md5": "m", "sha1": "s1", "sha256": "s256", "sha512": "s512"}
    stub = Stub(
        {
            LIST_PATH: {"body": {"databases": []}},
            CHECKSUM_PATH: {"body": {"id": "bogon_ip_v1", "format": "csvgz", "checksums": digests}},
            "/.well-known/oauth-authorization-server": {
                "body": {
                    "issuer": "https://api.example",
                    "authorization_endpoint": "https://api.example/oauth/authorize",
                    "token_endpoint": "https://api.example/oauth/token",
                }
            },
        }
    )
    client = make_client(transport=stub.transport, base_url="https://api.example" + "/" * slashes)

    client.database.list()
    client.database.checksums("bogon_ip_v1", "csvgz")
    client.oauth.metadata()

    assert stub.paths() == [LIST_PATH, CHECKSUM_PATH, "/.well-known/oauth-authorization-server"]
