from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
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
        trial_expired (bool | Unset): On every answer to a key on the free plan, and on no other: `false` while the
            day's trial of every field lasts, `true` once the answer has Unlimited's fields.
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
    trial_expired: bool | Unset = UNSET
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

        trial_expired = self.trial_expired

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
        if trial_expired is not UNSET:
            field_dict["trial_expired"] = trial_expired

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
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

        trial_expired = d.pop("trial_expired", UNSET)

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
            trial_expired=trial_expired,
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
