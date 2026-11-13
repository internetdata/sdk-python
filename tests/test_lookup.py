"""The lookups' Python surface, as distinct from the shared conformance corpus: the bogon
short-circuit, the batch's concurrency, the per-call options, the self-endpoints, and what
each lookup makes of an answer it cannot read."""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import importlib
import json
import math
import re
import uuid
from collections.abc import Callable
from typing import Any, get_args

import attrs
import httpx
import pytest
from helpers import (
    API,
    API_KEY,
    TESTDATA,
    ClientFactory,
    Lookups,
    LoopBound,
    Meter,
    Stub,
    answer,
    settle,
)

import internetdata
from internetdata import (
    AsnResult,
    AsyncInternetData,
    DomainResult,
    Entitlement,
    EntitlementPlanTier,
    InternetData,
    InternetDataError,
    Result,
    _core,
    is_bogon,
)
from internetdata._generated.models.entitlement_plan_tier import (
    EntitlementPlanTier as WireEntitlementPlanTier,
)

# Enough addresses for seven chunks of the batch endpoint's 1000, so a concurrency bound
# has something to bound: one request per chunk, and only the chunks overlap.
ADDRESSES = [f"9.{1 + n // 65536}.{n // 256 % 256}.{n % 256}" for n in range(6001)]

PAID: dict[str, Any] = next(c for c in TESTDATA["lookup"] if c["name"] == "paid-services")["body"]
ASN: dict[str, Any] = next(c for c in TESTDATA["lookup"] if c["name"] == "asn-paid-answer")["body"]
DOMAIN: dict[str, Any] = next(c for c in TESTDATA["lookup"] if c["name"] == "domain-paid-answer")[
    "body"
]

ENTITLEMENT: dict[str, Any] = {
    "org_id": "85bb51e4-2eb6-4a31-8e4d-02ba8b98fe61",
    "apikey": {
        "id": "0ab424cc-7619-4dad-b027-afacdc2cedb0",
        "expires": None,
        "allowed_cidrs": [],
    },
    "plan": {"key": "max", "tier": "max"},
    "usage": {
        "requests": 580,
        "quota": 5000000,
        "hard_limit": None,
        "window_start": "2026-09-04T07:00:00Z",
        "window_end": "2026-10-04T07:00:00Z",
    },
}

# Each lookup, the path it asks, and the call.
CALLS: dict[str, tuple[str, Callable[..., Any]]] = {
    "lookup": ("/8.8.8.8", lambda client, **kw: client.lookup("8.8.8.8", **kw)),
    "lookup_asn": ("/asn/9009", lambda client, **kw: client.lookup_asn(9009, **kw)),
    "lookup_domain": (
        "/domain/example.com",
        lambda client, **kw: client.lookup_domain("example.com", **kw),
    ),
    "my_ip": ("/myip", lambda client, **kw: client.my_ip(**kw)),
    "my_entitlement": ("/api/v1/entitlement", lambda client, **kw: client.my_entitlement(**kw)),
}


def test_is_bogon_is_on_the_client_and_agrees_with_the_standalone_export(
    make_client: ClientFactory,
) -> None:
    client = make_client()
    for case in TESTDATA["isBogon"]:
        assert client.is_bogon(case["ip"]) is case["expect"], f"{case['ip']} ({case['why']})"
        assert client.is_bogon(case["ip"]) is is_bogon(case["ip"]), (
            f"{case['ip']}: client and export disagree"
        )


def test_a_bogon_lookup_issues_zero_http_requests(make_client: ClientFactory) -> None:
    stub = Lookups({})
    client = make_client(transport=stub.transport)
    for ip in ("10.0.0.1", "127.0.0.1", "::1", "fe80::1", "192.168.1.1"):
        assert client.lookup(ip).is_bogon is True
    assert stub.calls == []


def test_a_served_answer_is_read_member_by_member(make_client: ClientFactory) -> None:
    stub = Lookups({"1.1.1.1": {"body": PAID}})
    client = make_client(transport=stub.transport)

    result = client.lookup("1.1.1.1")

    assert result.is_bogon is False
    assert result.hostname == "one.one.one.one"
    assert result.web is not None and result.web[0].port == PAID["web"][0]["port"]
    assert result.location.latitude == PAID["location"]["latitude"]
    assert result.flagged("is_dns_resolver") is True
    assert result.flagged("is_vpn") is False


def test_batch_concurrency_is_configurable_per_call(make_client: ClientFactory) -> None:
    meter = Meter(make_client.kind)
    client = make_client(transport=meter.transport, cache=False)

    client.lookup_batch(ADDRESSES, concurrency=3)

    assert meter.calls == 7, "one request per chunk of 1000"
    assert meter.peak <= 3, f"peak in flight was {meter.peak}, expected at most 3"
    assert meter.peak > 1, "requests should still overlap"


def test_a_per_call_concurrency_overrides_the_client_default(make_client: ClientFactory) -> None:
    meter = Meter(make_client.kind)
    # Instance default of 2, raised to 6 for this one batch.
    client = make_client(transport=meter.transport, cache=False, concurrency=2)

    client.lookup_batch(ADDRESSES, concurrency=6)

    assert meter.peak > 2, f"override ignored: peak was {meter.peak}, expected above 2"
    assert meter.peak <= 6, f"peak in flight was {meter.peak}, expected at most 6"


def test_without_an_override_the_client_concurrency_still_applies(
    make_client: ClientFactory,
) -> None:
    meter = Meter(make_client.kind)
    client = make_client(transport=meter.transport, cache=False, concurrency=2)

    client.lookup_batch(ADDRESSES)

    assert meter.peak <= 2, f"peak in flight was {meter.peak}, expected at most 2"


@pytest.mark.parametrize(
    "concurrency", [0, -1, 0.5, 1.5, 2.0, float("nan"), math.inf, "2", "", "x", True, [2], object()]
)
def test_a_per_call_concurrency_below_one_is_refused_before_any_request(
    make_client: ClientFactory, concurrency: Any
) -> None:
    stub = Lookups({})
    client = make_client(transport=stub.transport, cache=False)
    bound = LoopBound()

    outcome = settle(
        lambda: client.lookup_batch(["45.83.91.1", "10.0.0.1"], concurrency=concurrency),
        bound,
        within=5.0,
    )

    assert isinstance(outcome, InternetDataError), f"{concurrency}: settled with {outcome!r}"
    assert outcome.kind == "bad_request"
    assert outcome.retryable is False
    assert "concurrency" in str(outcome)
    assert stub.calls == []


@pytest.mark.parametrize("client", [InternetData, AsyncInternetData])
@pytest.mark.parametrize(
    "concurrency",
    [0, -1, 1.5, 2.0, float("nan"), math.inf, "2", "", "x", None, True, [2], object()],
)
def test_a_concurrency_that_is_not_a_whole_number_from_1_is_refused_when_the_client_is_built(
    client: type[InternetData | AsyncInternetData], concurrency: Any
) -> None:
    with pytest.raises(ValueError, match="concurrency"):
        client(concurrency=concurrency)


@pytest.mark.parametrize("concurrency", [1, 2, 2**63])
def test_a_whole_concurrency_from_1_is_taken_when_the_client_is_built(concurrency: int) -> None:
    InternetData(concurrency=concurrency).close()
    asyncio.run(AsyncInternetData(concurrency=concurrency).aclose())


PER_CALL_RETRIES: dict[str, Callable[..., Any]] = {
    "lookup": lambda c, **o: c.lookup("9.9.9.9", **o),
    "a bogon": lambda c, **o: c.lookup("10.0.0.1", **o),
    "a cached address": lambda c, **o: c.lookup("1.1.1.1", **o),
    "lookup_asn": lambda c, **o: c.lookup_asn(9009, **o),
    "lookup_domain": lambda c, **o: c.lookup_domain("example.com", **o),
    "my_ip": lambda c, **o: c.my_ip(**o),
    "my_entitlement": lambda c, **o: c.my_entitlement(**o),
    "lookup_batch": lambda c, **o: c.lookup_batch(["9.9.9.9"], **o),
    "a batch of a bogon and a cached address": lambda c, **o: c.lookup_batch(
        ["10.0.0.1", "1.1.1.1"], **o
    ),
}


@pytest.mark.parametrize("retries", [-1, 1.5, float("nan"), "2", True])
@pytest.mark.parametrize("call", PER_CALL_RETRIES)
def test_a_per_call_retry_count_that_is_not_a_whole_number_from_0_is_refused_before_anything_answers(
    make_client: ClientFactory, call: str, retries: Any
) -> None:
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport)
    client.lookup("1.1.1.1")
    sent = len(stub.calls)

    with pytest.raises(ValueError, match="retries"):
        PER_CALL_RETRIES[call](client, retries=retries)

    assert len(stub.calls) == sent


@pytest.mark.parametrize("on", ["client", "call"])
def test_infinite_retries_retry_a_failing_call_until_it_succeeds(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch, on: str
) -> None:
    monkeypatch.setattr(_core, "_BACKOFF_BASE", 0.0)
    sent: list[str] = []

    def serve(request: httpx.Request) -> httpx.Response:
        sent.append(request.url.path)
        if len(sent) <= 8:
            return httpx.Response(503, json={"error": "unavailable"})
        return httpx.Response(200, json=answer("9.9.9.9"))

    client = make_client(
        transport=httpx.MockTransport(serve),
        cache=False,
        retries=math.inf if on == "client" else 0,
    )

    result = client.lookup("9.9.9.9", **({} if on == "client" else {"retries": math.inf}))

    assert result.ip == "9.9.9.9"
    assert len(sent) == 9


@pytest.mark.parametrize("call", CALLS)
def test_retries_are_configurable_per_call(make_client: ClientFactory, call: str) -> None:
    path, send = CALLS[call]
    stub = Stub({path: {"status": 500, "body": {"error": "lookup failed"}}})
    client = make_client(transport=stub.transport, cache=False, retries=0)

    with pytest.raises(InternetDataError):
        send(client, retries=2)

    # 1 initial attempt plus 2 retries, rather than the instance's 0.
    assert len(stub.requests) == 3


@pytest.mark.parametrize("timeout", [-1, 1e300])
@pytest.mark.parametrize("ip", ["10.0.0.1", "1.1.1.1"])
def test_a_per_call_timeout_is_refused_even_when_the_answer_needs_no_request(
    make_client: ClientFactory, ip: str, timeout: float
) -> None:
    """A bogon, and an address already cached."""
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport)
    client.lookup("1.1.1.1")

    with pytest.raises(ValueError, match="timeout"):
        client.lookup(ip, timeout=timeout)
    with pytest.raises(ValueError, match="timeout"):
        client.lookup_batch([ip], timeout=timeout)

    assert len(stub.calls) == 1


def test_a_result_cannot_be_mutated(make_client: ClientFactory) -> None:
    stub = Lookups({"1.1.1.1": {"body": answer("1.1.1.1")}})
    client = make_client(transport=stub.transport)

    result = client.lookup("1.1.1.1")

    # The cache hands the same object to every later caller of this address.
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.is_vpn = True  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.location.city = "Vienna"  # type: ignore[misc]


def test_an_empty_batch_makes_no_request(make_client: ClientFactory) -> None:
    stub = Lookups({})
    client = make_client(transport=stub.transport)

    assert client.lookup_batch([]) == {}
    assert stub.calls == []


def test_a_transport_failure_surfaces_as_a_network_error() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with (
        InternetData(transport=httpx.MockTransport(refuse), retries=0) as client,
        pytest.raises(InternetDataError) as caught,
    ):
        client.lookup("9.9.9.9")

    assert caught.value.kind == "network"
    assert caught.value.retryable is True


def test_a_200_missing_a_required_key_is_a_typed_error_not_a_traceback(
    make_client: ClientFactory,
) -> None:
    """A healthy-looking 200 whose body omits a required member: a KeyError out of the
    model layer would escape a caller writing `except InternetDataError`."""
    body = {key: value for key, value in answer("1.1.1.1").items() if key != "location"}
    stub = Lookups({"1.1.1.1": {"status": 200, "body": body}})
    client = make_client(transport=stub.transport, cache=False, retries=0)

    with pytest.raises(InternetDataError) as caught:
        client.lookup("1.1.1.1")

    assert caught.value.kind == "server_error"
    assert caught.value.status == 200
    assert "location" in str(caught.value)


def test_my_ip_reads_the_calling_address(make_client: ClientFactory) -> None:
    stub = Stub({"/myip": {"body": answer("146.70.116.130")}})
    client = make_client(transport=stub.transport)

    result = client.my_ip()

    assert result.ip == "146.70.116.130"
    assert result.is_vpn is None, "not in Unlimited"


def test_my_ip_is_not_cached(make_client: ClientFactory) -> None:
    """The cache is keyed by address, and which address this is IS the question - a
    machine that moves between networks would otherwise be told where it used to be."""
    stub = Stub({"/myip": {"body": answer("146.70.116.130")}})
    client = make_client(transport=stub.transport)

    client.my_ip()
    client.my_ip()

    assert len(stub.requests) == 2


def test_my_entitlement_reports_the_plan_and_the_usage(make_client: ClientFactory) -> None:
    stub = Stub({"/api/v1/entitlement": {"body": ENTITLEMENT}})
    client = make_client(transport=stub.transport)

    ent = client.my_entitlement()

    assert isinstance(ent, Entitlement)
    assert ent.org_id == uuid.UUID(ENTITLEMENT["org_id"])
    assert ent.apikey.id == uuid.UUID(ENTITLEMENT["apikey"]["id"])
    assert ent.plan.key == "max"
    assert ent.plan.tier == "max"
    assert ent.usage.requests == 580
    assert ent.usage.quota == 5000000
    # Null means NEVER stop, which is not the same as a limit of zero.
    assert ent.usage.hard_limit is None
    assert ent.usage.window_start == datetime.datetime(2026, 9, 4, 7, tzinfo=datetime.UTC)
    assert ent.apikey.expires is None
    assert ent.apikey.allowed_cidrs == ()


def test_my_entitlement_is_not_cached(make_client: ClientFactory) -> None:
    """The whole point is what has been spent, so a cached answer is a wrong one within
    seconds of the next request."""
    stub = Stub({"/api/v1/entitlement": {"body": ENTITLEMENT}})
    client = make_client(transport=stub.transport)

    client.my_entitlement()
    client.my_entitlement()

    assert len(stub.requests) == 2


def test_my_entitlement_surfaces_an_unauthorized_key(make_client: ClientFactory) -> None:
    """Unlike a lookup there is no useful unauthenticated answer, so this is an error
    rather than a partial result."""
    stub = Stub({"/api/v1/entitlement": {"status": 401, "body": {"error": "invalid API key"}}})
    client = make_client(transport=stub.transport, retries=0)

    with pytest.raises(InternetDataError) as caught:
        client.my_entitlement()

    assert (caught.value.kind, str(caught.value)) == ("unauthorized", "invalid API key")


@pytest.mark.parametrize("call", ["lookup_asn", "lookup_domain"])
def test_an_as_or_a_domain_is_not_cached(make_client: ClientFactory, call: str) -> None:
    path, send = CALLS[call]
    stub = Stub({path: {"body": ASN if call == "lookup_asn" else DOMAIN}})
    client = make_client(transport=stub.transport)

    first = send(client)
    send(client)

    assert isinstance(first, AsnResult if call == "lookup_asn" else DomainResult)
    assert len(stub.requests) == 2


@pytest.mark.parametrize(
    ("asn", "path"),
    [(9009, "/asn/9009"), (4294967295, "/asn/4294967295"), ("AS9009", "/asn/AS9009")],
)
def test_an_as_number_is_sent_as_given(make_client: ClientFactory, asn: Any, path: str) -> None:
    stub = Stub({path: {"body": ASN}})
    client = make_client(transport=stub.transport)

    client.lookup_asn(asn)

    assert [request.url.raw_path.decode() for request in stub.requests] == [path]


@pytest.mark.parametrize(
    ("domain", "path"),
    [
        ("example.com", "/domain/example.com"),
        ("Example.COM", "/domain/Example.COM"),
        ("a/b?c#d", "/domain/a%2Fb%3Fc%23d"),
        ("bücher.example", "/domain/b%C3%BCcher.example"),
    ],
)
def test_a_domain_is_sent_as_given_path_escaped(
    make_client: ClientFactory, domain: str, path: str
) -> None:
    stub = Lookups({})
    client = make_client(transport=stub.transport, retries=0)

    with pytest.raises(InternetDataError):
        client.lookup_domain(domain)

    assert stub.calls == [f"GET {API}{path}"]


def test_a_lookup_carries_the_key_and_a_keyless_one_none(make_client: ClientFactory) -> None:
    seen: list[str | None] = []

    def serve(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("authorization"))
        return httpx.Response(200, json=answer("1.1.1.1"))

    make_client(transport=httpx.MockTransport(serve)).lookup("1.1.1.1")
    make_client(transport=httpx.MockTransport(serve), api_key=None).lookup("1.1.1.1")

    assert seen == [f"Bearer {API_KEY}", None]


MALFORMED: dict[str, tuple[str, dict[str, Any]]] = {
    "ip null": ("lookup", answer("8.8.8.8", ip=None)),
    "ip empty": ("lookup", answer("8.8.8.8", ip="")),
    "is_bogon a string": ("lookup", answer("8.8.8.8", is_bogon="false")),
    "is_tor null": ("lookup", answer("8.8.8.8", is_tor=None)),
    "is_vpn a number": ("lookup", answer("8.8.8.8", is_vpn=1)),
    "tor null": ("lookup", answer("8.8.8.8", tor=None)),
    "tor a list": ("lookup", answer("8.8.8.8", tor=[])),
    "a detail missing a member": (
        "lookup",
        answer("8.8.8.8", is_vpn=True, vpn={"provider": "x", "provider_name": "X"}),
    ),
    "a detail's member null": (
        "lookup",
        {**PAID, "ip": "8.8.8.8", "hosting": {**PAID["hosting"], "provider": None}},
    ),
    "a proxy's hits a numeric string": (
        "lookup",
        {
            **PAID,
            "ip": "8.8.8.8",
            "dcproxy": {
                "provider": "p",
                "provider_name": "P",
                "first_seen": "2026-11-01",
                "last_seen": "2026-11-02",
                "hits": "3",
                "hits_days_pct": 5,
                "providers_num": 1,
            },
        },
    ),
    "web an object": ("lookup", {**PAID, "ip": "8.8.8.8", "web": {}}),
    "a web row empty": ("lookup", {**PAID, "ip": "8.8.8.8", "web": [{}]}),
    "a bittorrent client a number": (
        "lookup",
        {**PAID, "ip": "8.8.8.8", "bittorrent": {**PAID["bittorrent"], "clients": [1]}},
    ),
    "location.country null": (
        "lookup",
        answer("8.8.8.8", location={**answer("x")["location"], "country": None}),
    ),
    "location.city a number": (
        "lookup",
        answer("8.8.8.8", location={**answer("x")["location"], "city": 1}),
    ),
    "location.latitude a string": (
        "lookup",
        answer("8.8.8.8", location={**answer("x")["location"], "latitude": "48.2"}),
    ),
    "asn.asn a numeric string": (
        "lookup",
        answer("8.8.8.8", asn={**answer("x")["asn"], "asn": "9009"}),
    ),
    "asn.asn a bool": ("lookup", answer("8.8.8.8", asn={**answer("x")["asn"], "asn": True})),
    "abuse.validated a string": (
        "lookup",
        answer("8.8.8.8", abuse={**answer("x")["abuse"], "validated": "yes"}),
    ),
    "hosted_domains.total a string": ("lookup", answer("8.8.8.8", hosted_domains={"total": "4"})),
    "my_ip's ip null": ("my_ip", answer("8.8.8.8", ip=None)),
    "an AS's asn a string": ("lookup_asn", {**ASN, "asn": "9009"}),
    "an AS's prefix row missing a member": (
        "lookup_asn",
        {**ASN, "prefixes": [{"prefix": "146.70.0.0/16"}]},
    ),
    "an AS's whois value a number": ("lookup_asn", {**ASN, "whois": {"as_name": 1}}),
    "an AS's other origins of strings": (
        "lookup_asn",
        {**ASN, "prefixes": [{**ASN["prefixes"][0], "other_origins": ["174"]}]},
    ),
    "a domain's has_a a string": ("lookup_domain", {**DOMAIN, "has_a": "true"}),
    "a domain's dns missing a type": (
        "lookup_domain",
        {**DOMAIN, "dns": {k: v for k, v in DOMAIN["dns"].items() if k != "mx"}},
    ),
    "a domain's disposable partly there": (
        "lookup_domain",
        {**DOMAIN, "is_disposable": True, "disposable": {"confidence": "high"}},
    ),
    "the entitlement's quota a numeric string": (
        "my_entitlement",
        {**ENTITLEMENT, "usage": {**ENTITLEMENT["usage"], "quota": "5000000"}},
    ),
    "the entitlement's tier a number": (
        "my_entitlement",
        {**ENTITLEMENT, "plan": {"key": "max", "tier": 1}},
    ),
    "the entitlement's tier unknown": (
        "my_entitlement",
        {**ENTITLEMENT, "plan": {"key": "max", "tier": "platinum"}},
    ),
    "the entitlement's org_id not a UUID": ("my_entitlement", {**ENTITLEMENT, "org_id": "x"}),
    "the entitlement's window_start not RFC 3339": (
        "my_entitlement",
        {**ENTITLEMENT, "usage": {**ENTITLEMENT["usage"], "window_start": "2026-09-04"}},
    ),
    "the entitlement's hard_limit missing": (
        "my_entitlement",
        {
            **ENTITLEMENT,
            "usage": {k: v for k, v in ENTITLEMENT["usage"].items() if k != "hard_limit"},
        },
    ),
}


@pytest.mark.parametrize("case", list(MALFORMED.values()), ids=list(MALFORMED))
def test_a_member_sent_as_null_or_the_wrong_type_is_the_servers_failure(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch, case: tuple[str, dict[str, Any]]
) -> None:
    monkeypatch.setattr(_core, "_BACKOFF_BASE", 0.0)
    name, body = case
    path, send = CALLS[name]
    stub = Stub({path: {"body": body}})
    client = make_client(transport=stub.transport, cache=False, retries=2)

    with pytest.raises(InternetDataError) as caught:
        send(client)

    assert (caught.value.kind, caught.value.status) == ("server_error", 200), repr(caught.value)
    assert len(stub.requests) == 3


# Each of these is the spec's own: an optional member sent as null is absent, a detail
# object is `{}` under a false flag, and JSON does not tell 48 from 48.0.
READABLE: dict[str, tuple[str, dict[str, Any], Callable[[Any], bool]]] = {
    "an optional member null": (
        "lookup",
        answer("8.8.8.8", is_vpn=None),
        lambda result: result.is_vpn is None,
    ),
    "a paid member of location null": (
        "lookup",
        answer("8.8.8.8", location={**answer("x")["location"], "city": None}),
        lambda result: result.location.city is None,
    ),
    "a whole latitude": (
        "lookup",
        answer("8.8.8.8", location={**answer("x")["location"], "latitude": 48}),
        lambda result: result.location.latitude == 48.0,
    ),
    "an empty detail": (
        "lookup",
        answer("8.8.8.8", is_vpn=False, vpn={}),
        lambda result: result.vpn is not None and result.vpn.provider is None,
    ),
    "a member this spec predates": (
        "lookup",
        answer("8.8.8.8", is_new=True),
        lambda result: result.raw["is_new"] is True,
    ),
    "an expiring key": (
        "my_entitlement",
        {**ENTITLEMENT, "apikey": {**ENTITLEMENT["apikey"], "expires": "2027-01-01t00:00:00z"}},
        lambda ent: ent.apikey.expires == datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC),
    ),
}


@pytest.mark.parametrize("case", list(READABLE.values()), ids=list(READABLE))
def test_what_the_spec_allows_reads_as_an_answer(
    make_client: ClientFactory, case: tuple[str, dict[str, Any], Callable[[Any], bool]]
) -> None:
    name, body, holds = case
    path, send = CALLS[name]
    client = make_client(transport=Stub({path: {"body": body}}).transport)

    assert holds(send(client))


ENTRIES: dict[str, Any] = {
    "null": None,
    "a string": "x",
    "a list": [],
    "an empty object": {},
    "ip null": answer("8.8.8.8", ip=None),
    "is_tor a string": answer("8.8.8.8", is_tor="yes"),
}


@pytest.mark.parametrize("entry", list(ENTRIES.values()), ids=list(ENTRIES))
def test_a_batch_entry_it_cannot_read_is_that_addresss_error_alone(
    make_client: ClientFactory, entry: Any
) -> None:
    body = {"results": {"8.8.8.8": entry, "1.1.1.1": answer("1.1.1.1")}}
    stub = Stub({"/batch": {"raw": json.dumps(body).encode()}})
    client = make_client(transport=stub.transport, cache=False, retries=2)

    answers = client.lookup_batch(["8.8.8.8", "1.1.1.1"])

    failed = answers["8.8.8.8"]
    assert isinstance(failed, InternetDataError), repr(failed)
    assert (failed.kind, failed.status) == ("server_error", 200)
    assert isinstance(answers["1.1.1.1"], Result)
    assert stub.paths() == ["/batch"]


@pytest.mark.parametrize(
    "body",
    ["<html>502</html>", "", "null", "[]", "{}", '{"results": null}', '{"results": []}'],
    ids=["HTML", "empty", "null", "a list", "neither map", "results null", "results a list"],
)
def test_a_batch_answer_holding_neither_map_fails_its_chunk_retried(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    monkeypatch.setattr(_core, "_BACKOFF_BASE", 0.0)
    stub = Stub({"/batch": {"raw": body.encode()}})
    client = make_client(transport=stub.transport, cache=False, retries=2)

    answers = client.lookup_batch(["8.8.8.8", "1.1.1.1"])

    for ip in ("8.8.8.8", "1.1.1.1"):
        failed = answers[ip]
        assert isinstance(failed, InternetDataError), f"{ip}: {failed!r}"
        assert (failed.kind, failed.status) == ("server_error", 200), repr(failed)
    assert stub.paths() == ["/batch"] * 3


def test_a_batch_entry_missing_from_the_answer_is_reported_not_lost(
    make_client: ClientFactory,
) -> None:
    stub = Stub({"/batch": {"body": {"results": {"1.1.1.1": answer("1.1.1.1")}, "errors": {}}}})
    client = make_client(transport=stub.transport, cache=False)

    answers = client.lookup_batch(["8.8.8.8", "1.1.1.1"])

    missing = answers["8.8.8.8"]
    assert isinstance(missing, InternetDataError) and missing.kind == "server_error"
    assert isinstance(answers["1.1.1.1"], Result)


# Each hand-written lookup type beside the generated model of the same spec schema.
LOOKUP_MODELS = {
    "Result": "lookup_response.LookupResponse",
    "ClassDetail": "class_detail.ClassDetail",
    "ProxyDetail": "proxy_detail.ProxyDetail",
    "PubproxyDetail": "pubproxy_detail.PubproxyDetail",
    "CarrierDetail": "carrier_detail.CarrierDetail",
    "SatelliteDetail": "satellite_detail.SatelliteDetail",
    "SshDetail": "ssh_detail.SshDetail",
    "SmtpDetail": "smtp_detail.SmtpDetail",
    "WebDetail": "web_detail.WebDetail",
    "DnsResolverDetail": "dns_resolver_detail.DnsResolverDetail",
    "BitTorrentDetail": "bit_torrent_detail.BitTorrentDetail",
    "Location": "location.Location",
    "Asn": "asn.Asn",
    "Company": "company.Company",
    "AbuseContact": "abuse_contact.AbuseContact",
    "Whois": "whois.Whois",
    "Rwhois": "rwhois.Rwhois",
    "HostedDomains": "hosted_domains.HostedDomains",
    "AsnResult": "asn_lookup_response.AsnLookupResponse",
    "AsnPrefix": "asn_prefix.AsnPrefix",
    "DomainResult": "domain_lookup_response.DomainLookupResponse",
    "DomainDns": "domain_dns.DomainDns",
    "DnsAddressRecord": "dns_address_record.DnsAddressRecord",
    "DnsMxRecord": "dns_mx_record.DnsMxRecord",
    "DnsNsRecord": "dns_ns_record.DnsNsRecord",
    "DnsCnameRecord": "dns_cname_record.DnsCnameRecord",
    "DomainIpRanges": "domain_ip_ranges.DomainIpRanges",
    "DomainIpRange": "domain_ip_range.DomainIpRange",
    "DisposableDetail": "disposable_detail.DisposableDetail",
    "Entitlement": "entitlement.Entitlement",
    "EntitlementApikey": "entitlement_apikey.EntitlementApikey",
    "EntitlementPlan": "entitlement_plan.EntitlementPlan",
    "EntitlementUsage": "entitlement_usage.EntitlementUsage",
}


@pytest.mark.parametrize("name", LOOKUP_MODELS)
def test_every_member_the_pinned_spec_serves_is_on_the_lookup_model(name: str) -> None:
    """The staleness pin on the hand-written lookup types, as on the database ones: a member
    a re-pin adds reaches the generated model and `raw`, and this turns red until the typed
    one has it. A member with no default is one the spec requires, which is what `_record`
    reads it as; a detail object's members are all required once it is not `{}`."""
    module, cls = LOOKUP_MODELS[name].split(".")
    wire = getattr(importlib.import_module(f"internetdata._generated.models.{module}"), cls)
    ours = getattr(internetdata, name)
    served = {f.name.rstrip("_"): f for f in attrs.fields(wire)}
    served.pop("additional_properties")
    modeled = {f.name: f for f in dataclasses.fields(ours)}
    modeled.pop("raw", None)

    assert set(served) == set(modeled), f"{name} and the spec disagree on its members"
    if name.endswith("Detail") and name != "WebDetail":
        assert all(f.default is attrs.NOTHING for f in served.values()), name
        return
    required = {key for key, f in served.items() if f.default is attrs.NOTHING}
    assert required == {key for key, f in modeled.items() if f.default is dataclasses.MISSING}, (
        f"{name}: what the spec requires is not what the model requires"
    )


def test_the_tier_vocabulary_is_the_pinned_specs() -> None:
    assert sorted(get_args(EntitlementPlanTier)) == sorted(m.value for m in WireEntitlementPlanTier)


def test_no_lookup_type_carries_a_mutable_list() -> None:
    """Frozen is not enough where a member is a list: the cache hands the same answer to
    every later caller of its address."""
    for name in LOOKUP_MODELS:
        for member in dataclasses.fields(getattr(internetdata, name)):
            assert not re.search(r"\blist\[", str(member.type)), f"{name}.{member.name}"
