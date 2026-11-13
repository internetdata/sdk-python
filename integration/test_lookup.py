"""The published package's lookups: keyless against prod and staging, and with the staging
key where this suite has one.

Nothing here pins a field COUNT or the plan the key's organization is on. What a served
answer must satisfy on any plan: every member the response carried reached the result as
served, and every member it did not carry reads as None, never as false, 0 or an empty
string, inside a shared object too (`location.city`).
"""

from __future__ import annotations

import dataclasses
import importlib.metadata
import ipaddress
import uuid
from typing import Any

import credential
import httpx
import pytest
from credential import PROD_API, STAGING, STAGING_API
from staging import PACKAGE, Recorder

from internetdata import InternetData, InternetDataError, Result, is_bogon

# The spec's own example address, and an AS and a domain every database knows.
PROBE = "146.70.116.130"
ASN = 9009
DOMAIN = "example.com"

APIS = {"prod": PROD_API, "staging": STAGING_API}

# The first release with the lookups. Gated on the installed version rather than on the
# method, which would also skip quietly if the method were ever removed.
LOOKUP_SINCE = (2, 11)

pytestmark = pytest.mark.skipif(
    tuple(int(part) for part in importlib.metadata.version(PACKAGE).split(".")[:2]) < LOOKUP_SINCE,
    reason=f"the installed {PACKAGE} predates the lookups",
)


@pytest.mark.parametrize("api", APIS)
def test_a_keyless_lookup_reads_as_served(api: str) -> None:
    keyless = Keyless()
    with InternetData(base_url=APIS[api], transport=keyless) as client:
        result = client.lookup(PROBE)

    assert keyless.paths == [f"/{PROBE}"], keyless.paths
    assert not any(keyless.carried), "a keyless client sent an Authorization header"
    assert result.ip == PROBE
    assert result.is_bogon is False, "a served answer is not a local one"
    assert result.location.country, f"{PROBE} has no country"
    assert_read_as_served(result, result.raw, "answer")
    print(f"==> {api}: {PROBE} keyless, {len(result.raw)} members")


@pytest.mark.parametrize("api", APIS)
def test_a_keyless_as_and_domain_lookup_read_as_served(api: str) -> None:
    with InternetData(base_url=APIS[api]) as client:
        asn = client.lookup_asn(ASN)
        domain = client.lookup_domain(DOMAIN)

    assert asn.asn == ASN
    assert asn.name, f"AS{ASN} has no name"
    assert_read_as_served(asn, asn.raw, "AS answer")
    assert domain.domain == DOMAIN
    assert domain.is_registered is True
    assert_read_as_served(domain, domain.raw, "domain answer")


@pytest.mark.parametrize("api", APIS)
def test_my_ip_answers_the_calling_address(api: str) -> None:
    with InternetData(base_url=APIS[api]) as client:
        result = client.my_ip()

    assert not is_bogon(str(ipaddress.ip_address(result.ip))), result.ip
    assert_read_as_served(result, result.raw, "answer")


@pytest.mark.parametrize("api", APIS)
def test_a_keyless_batch_is_refused_once_and_its_bogon_still_answered(api: str) -> None:
    keyless = Keyless()
    with InternetData(base_url=APIS[api], transport=keyless) as client:
        # Two addresses on the wire: a keyless batch of one is answered as its lookup.
        got = client.lookup_batch([PROBE, "8.8.8.8", "10.0.0.1"])

    bogon = got["10.0.0.1"]
    assert isinstance(bogon, Result) and bogon.is_bogon, "10.0.0.1 reached the network"
    for ip in (PROBE, "8.8.8.8"):
        refused = got[ip]
        assert isinstance(refused, InternetDataError), f"a keyless batch answered {refused}"
        assert (refused.kind, refused.status, refused.retryable) == ("unauthorized", 401, False)
    assert keyless.paths == ["/batch"], "one request, never retried"


@pytest.mark.parametrize("api", APIS)
def test_a_keyless_entitlement_is_unauthorized(api: str) -> None:
    with InternetData(base_url=APIS[api]) as client, pytest.raises(InternetDataError) as caught:
        client.my_entitlement()

    assert (caught.value.kind, caught.value.status) == ("unauthorized", 401)


def test_a_bogon_is_answered_without_touching_the_network() -> None:
    with InternetData(base_url=STAGING_API, transport=Refusing()) as client:
        result = client.lookup("10.0.0.1")

    assert result.is_bogon is True
    assert result.is_vpn is False, "a bogon carries every flag, false"
    assert result.vpn is not None and all(
        value is None for value in dataclasses.asdict(result.vpn).values()
    ), "a bogon's detail objects are present and empty"


def test_the_oauth_accessor_signs_in_at_the_apex_of_the_api_host() -> None:
    with InternetData(base_url=STAGING_API) as client:
        metadata = client.oauth.metadata()

    assert metadata.issuer == STAGING


def test_the_key_reaches_the_wire_and_the_answer_keeps_its_shape() -> None:
    keyed, recorder = keyed_client()
    try:
        result = keyed.lookup(PROBE)
        domain = keyed.lookup_domain(DOMAIN)
    finally:
        keyed.close()
    with InternetData(base_url=STAGING_API) as client:
        keyless = client.lookup(PROBE)

    assert recorder.facts, "no request reached the staging API"
    for fact in recorder.facts:
        assert fact.carried_key, f"the request to {fact.path} carried no key"
    assert_read_as_served(result, result.raw, "answer")
    assert_read_as_served(domain, domain.raw, "domain answer")
    # A free-plan key's answer is Unlimited's once its day's trial is spent, and marks it.
    dropped = set(keyless.raw) - set(result.raw) - {"trial_expired"}
    assert not dropped, f"the key's answer drops {sorted(dropped)}, which a keyless one serves"
    print(f"==> staging: {PROBE} keyed, {len(result.raw)} members")


def test_the_keys_entitlement_reads() -> None:
    keyed, recorder = keyed_client()
    try:
        entitlement = keyed.my_entitlement()
    finally:
        keyed.close()

    assert all(fact.carried_key for fact in recorder.facts), "the key never reached the wire"
    assert isinstance(entitlement.org_id, uuid.UUID)
    assert entitlement.plan.tier in ("free", "starter", "scale", "max")
    assert entitlement.usage.requests >= 0
    assert entitlement.usage.window_start < entitlement.usage.window_end
    print(f"==> entitlement: plan {entitlement.plan.key}, tier {entitlement.plan.tier}")


def test_the_api_host_answers_the_database_calls_too() -> None:
    keyed, recorder = keyed_client()
    try:
        families = keyed.database.list()
    finally:
        keyed.close()

    assert families, "the catalog came back empty on the API host"
    # By path rather than a count, so a retry against a wobbling staging is not a failure.
    assert {fact.path for fact in recorder.facts} == {"/api/v2/database/list"}
    assert all(fact.carried_key for fact in recorder.facts), "the key never reached the wire"


def keyed_client() -> tuple[InternetData, Recorder]:
    reason = credential.skip_reason()
    if reason:
        pytest.skip(reason)
    recorder = Recorder(credential.key())
    return InternetData(credential.key(), base_url=STAGING_API, transport=recorder), recorder


def assert_read_as_served(value: Any, served: Any, where: str) -> None:
    """Every member `served` carries reached `value` as served, and every member it did not
    carry reads as None. A member the API serves and this release does not model is the API
    moving ahead of it, and is left alone."""
    for member in dataclasses.fields(value):
        if member.name == "raw":
            continue
        held = getattr(value, member.name)
        name = f"{where}.{member.name}"
        if member.name not in served:
            assert held is None, f"{name} is not served, so it must read as None, not {held!r}"
            continue
        wire = served[member.name]
        if dataclasses.is_dataclass(held):
            assert_read_as_served(held, wire, name)
        elif isinstance(held, tuple):
            assert len(held) == len(wire), name
            for index, (item, item_wire) in enumerate(zip(held, wire, strict=True)):
                if dataclasses.is_dataclass(item):
                    assert_read_as_served(item, item_wire, f"{name}[{index}]")
                else:
                    assert item == item_wire, f"{name}[{index}]"
        else:
            assert held == wire, f"{name} reads {held!r} where the API served {wire!r}"


class Keyless(httpx.BaseTransport):
    """The real transport, remembering each path asked for and whether it carried an
    `Authorization` header: derived facts only, as `staging.Recorder` keeps."""

    def __init__(self) -> None:
        self.paths: list[str] = []
        self.carried: list[bool] = []
        self._inner = httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.paths.append(request.url.path)
        self.carried.append("authorization" in request.headers)
        return self._inner.handle_request(request)

    def close(self) -> None:
        self._inner.close()


class Refusing(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"the bogon path reached the network at {request.url}")
