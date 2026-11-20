from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.asn_hosted_domains import AsnHostedDomains
    from ..models.asn_lookup_response_whois import AsnLookupResponseWhois
    from ..models.asn_prefix import AsnPrefix


T = TypeVar("T", bound="AsnLookupResponse")


@_attrs_define
class AsnLookupResponse:
    """What every database says about one AS.

    Attributes:
        asn (int): The AS number.
        name (str): Its operator.
        country (str): The country its registry assigned it to.
        registry (str): The registry that allocated it.
        allocated (str): When.
        domain (str): Its operator's domain.
        type_ (str | Unset): The kind of network it runs. Paid plans and the trial.
        num_ips (int | Unset): IPv4 addresses it announces. Paid plans and the trial.
        num_prefixes4 (int | Unset): IPv4 prefixes it announces. Paid plans and the trial.
        num_prefixes6 (int | Unset): IPv6 prefixes it announces. Paid plans and the trial.
        rpki_valid (int | Unset): Its announcements RPKI calls valid. Paid plans and the trial.
        rpki_invalid (int | Unset): Invalid. Paid plans and the trial.
        rpki_not_found (int | Unset): With no RPKI record. Paid plans and the trial.
        whois (AsnLookupResponseWhois | Unset): Its ASN Whois record, every column, empty where the registry states
            nothing. Paid plans and the trial.
        prefixes (list[AsnPrefix] | Unset): What it announces, IPv4 then IPv6, up to 20000 a family. Paid plans and the
            trial.
        rank (int | Unset): Its rank in ASN Extended, by customer cone, 1 the largest; `0` for an AS seen in no AS path.
            Paid plans and the trial.
        tier1 (bool | Unset): Whether it is one of the transit-free networks at the top of the hierarchy, which get
            transit from no one and peer with each other. Paid plans and the trial.
        num_upstreams (int | Unset): How many AS numbers it gets transit from. Paid plans and the trial.
        upstreams (list[int] | Unset): Those AS numbers, ascending, up to 20000. Paid plans and the trial.
        num_peers (int | Unset): How many AS numbers it exchanges its own and its customers' routes with. Paid plans and
            the trial.
        peers (list[int] | Unset): Those AS numbers, ascending, up to 20000. Paid plans and the trial.
        num_downstreams (int | Unset): How many AS numbers it provides transit to. Paid plans and the trial.
        downstreams (list[int] | Unset): Those AS numbers, ascending, up to 20000. Paid plans and the trial.
        hosted_domains (AsnHostedDomains | Unset): From ASN Hosted Domains: how many registered domains the AS hosts,
            and the 10 most popular. Its database lists up to 1,000 an AS. Paid plans and the trial.
        trial_expired (bool | Unset): On every answer to a key on the free plan, and on no other: `false` while its
            organization's trial of every field lasts, `true` once the answer has Unlimited's fields.
        cap_reached (bool | Unset): On every answer to a key on a paid plan, and on no other: `false` while the answer
            has every field, `true` once its organization's overage cap is reached and the answer has Unlimited's. Lookups
            answered past the cap are not billed; raising or removing the cap in Billing turns it `false` again.
    """

    asn: int
    name: str
    country: str
    registry: str
    allocated: str
    domain: str
    type_: str | Unset = UNSET
    num_ips: int | Unset = UNSET
    num_prefixes4: int | Unset = UNSET
    num_prefixes6: int | Unset = UNSET
    rpki_valid: int | Unset = UNSET
    rpki_invalid: int | Unset = UNSET
    rpki_not_found: int | Unset = UNSET
    whois: AsnLookupResponseWhois | Unset = UNSET
    prefixes: list[AsnPrefix] | Unset = UNSET
    rank: int | Unset = UNSET
    tier1: bool | Unset = UNSET
    num_upstreams: int | Unset = UNSET
    upstreams: list[int] | Unset = UNSET
    num_peers: int | Unset = UNSET
    peers: list[int] | Unset = UNSET
    num_downstreams: int | Unset = UNSET
    downstreams: list[int] | Unset = UNSET
    hosted_domains: AsnHostedDomains | Unset = UNSET
    trial_expired: bool | Unset = UNSET
    cap_reached: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        asn = self.asn

        name = self.name

        country = self.country

        registry = self.registry

        allocated = self.allocated

        domain = self.domain

        type_ = self.type_

        num_ips = self.num_ips

        num_prefixes4 = self.num_prefixes4

        num_prefixes6 = self.num_prefixes6

        rpki_valid = self.rpki_valid

        rpki_invalid = self.rpki_invalid

        rpki_not_found = self.rpki_not_found

        whois: dict[str, Any] | Unset = UNSET
        if not isinstance(self.whois, Unset):
            whois = self.whois.to_dict()

        prefixes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.prefixes, Unset):
            prefixes = []
            for prefixes_item_data in self.prefixes:
                prefixes_item = prefixes_item_data.to_dict()
                prefixes.append(prefixes_item)

        rank = self.rank

        tier1 = self.tier1

        num_upstreams = self.num_upstreams

        upstreams: list[int] | Unset = UNSET
        if not isinstance(self.upstreams, Unset):
            upstreams = self.upstreams

        num_peers = self.num_peers

        peers: list[int] | Unset = UNSET
        if not isinstance(self.peers, Unset):
            peers = self.peers

        num_downstreams = self.num_downstreams

        downstreams: list[int] | Unset = UNSET
        if not isinstance(self.downstreams, Unset):
            downstreams = self.downstreams

        hosted_domains: dict[str, Any] | Unset = UNSET
        if not isinstance(self.hosted_domains, Unset):
            hosted_domains = self.hosted_domains.to_dict()

        trial_expired = self.trial_expired

        cap_reached = self.cap_reached

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "asn": asn,
                "name": name,
                "country": country,
                "registry": registry,
                "allocated": allocated,
                "domain": domain,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if num_ips is not UNSET:
            field_dict["num_ips"] = num_ips
        if num_prefixes4 is not UNSET:
            field_dict["num_prefixes4"] = num_prefixes4
        if num_prefixes6 is not UNSET:
            field_dict["num_prefixes6"] = num_prefixes6
        if rpki_valid is not UNSET:
            field_dict["rpki_valid"] = rpki_valid
        if rpki_invalid is not UNSET:
            field_dict["rpki_invalid"] = rpki_invalid
        if rpki_not_found is not UNSET:
            field_dict["rpki_not_found"] = rpki_not_found
        if whois is not UNSET:
            field_dict["whois"] = whois
        if prefixes is not UNSET:
            field_dict["prefixes"] = prefixes
        if rank is not UNSET:
            field_dict["rank"] = rank
        if tier1 is not UNSET:
            field_dict["tier1"] = tier1
        if num_upstreams is not UNSET:
            field_dict["num_upstreams"] = num_upstreams
        if upstreams is not UNSET:
            field_dict["upstreams"] = upstreams
        if num_peers is not UNSET:
            field_dict["num_peers"] = num_peers
        if peers is not UNSET:
            field_dict["peers"] = peers
        if num_downstreams is not UNSET:
            field_dict["num_downstreams"] = num_downstreams
        if downstreams is not UNSET:
            field_dict["downstreams"] = downstreams
        if hosted_domains is not UNSET:
            field_dict["hosted_domains"] = hosted_domains
        if trial_expired is not UNSET:
            field_dict["trial_expired"] = trial_expired
        if cap_reached is not UNSET:
            field_dict["cap_reached"] = cap_reached

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.asn_hosted_domains import AsnHostedDomains
        from ..models.asn_lookup_response_whois import AsnLookupResponseWhois
        from ..models.asn_prefix import AsnPrefix

        d = dict(src_dict)
        asn = d.pop("asn")

        name = d.pop("name")

        country = d.pop("country")

        registry = d.pop("registry")

        allocated = d.pop("allocated")

        domain = d.pop("domain")

        type_ = d.pop("type", UNSET)

        num_ips = d.pop("num_ips", UNSET)

        num_prefixes4 = d.pop("num_prefixes4", UNSET)

        num_prefixes6 = d.pop("num_prefixes6", UNSET)

        rpki_valid = d.pop("rpki_valid", UNSET)

        rpki_invalid = d.pop("rpki_invalid", UNSET)

        rpki_not_found = d.pop("rpki_not_found", UNSET)

        _whois = d.pop("whois", UNSET)
        whois: AsnLookupResponseWhois | Unset
        if isinstance(_whois, Unset):
            whois = UNSET
        else:
            whois = AsnLookupResponseWhois.from_dict(_whois)

        _prefixes = d.pop("prefixes", UNSET)
        prefixes: list[AsnPrefix] | Unset = UNSET
        if _prefixes is not UNSET:
            prefixes = []
            for prefixes_item_data in _prefixes:
                prefixes_item = AsnPrefix.from_dict(prefixes_item_data)

                prefixes.append(prefixes_item)

        rank = d.pop("rank", UNSET)

        tier1 = d.pop("tier1", UNSET)

        num_upstreams = d.pop("num_upstreams", UNSET)

        upstreams = cast(list[int], d.pop("upstreams", UNSET))

        num_peers = d.pop("num_peers", UNSET)

        peers = cast(list[int], d.pop("peers", UNSET))

        num_downstreams = d.pop("num_downstreams", UNSET)

        downstreams = cast(list[int], d.pop("downstreams", UNSET))

        _hosted_domains = d.pop("hosted_domains", UNSET)
        hosted_domains: AsnHostedDomains | Unset
        if isinstance(_hosted_domains, Unset):
            hosted_domains = UNSET
        else:
            hosted_domains = AsnHostedDomains.from_dict(_hosted_domains)

        trial_expired = d.pop("trial_expired", UNSET)

        cap_reached = d.pop("cap_reached", UNSET)

        asn_lookup_response = cls(
            asn=asn,
            name=name,
            country=country,
            registry=registry,
            allocated=allocated,
            domain=domain,
            type_=type_,
            num_ips=num_ips,
            num_prefixes4=num_prefixes4,
            num_prefixes6=num_prefixes6,
            rpki_valid=rpki_valid,
            rpki_invalid=rpki_invalid,
            rpki_not_found=rpki_not_found,
            whois=whois,
            prefixes=prefixes,
            rank=rank,
            tier1=tier1,
            num_upstreams=num_upstreams,
            upstreams=upstreams,
            num_peers=num_peers,
            peers=peers,
            num_downstreams=num_downstreams,
            downstreams=downstreams,
            hosted_domains=hosted_domains,
            trial_expired=trial_expired,
            cap_reached=cap_reached,
        )

        asn_lookup_response.additional_properties = d
        return asn_lookup_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
