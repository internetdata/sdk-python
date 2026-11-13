from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchLookupRequest")


@_attrs_define
class BatchLookupRequest:
    """Up to 1000 items across the three arrays, each optional.

    Attributes:
        ips (list[str] | Unset): Addresses.
        asns (list[str] | Unset): AS numbers, `AS15169` or `15169`; a JSON number reads too.
        domains (list[str] | Unset): Domains.
    """

    ips: list[str] | Unset = UNSET
    asns: list[str] | Unset = UNSET
    domains: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ips: list[str] | Unset = UNSET
        if not isinstance(self.ips, Unset):
            ips = self.ips

        asns: list[str] | Unset = UNSET
        if not isinstance(self.asns, Unset):
            asns = self.asns

        domains: list[str] | Unset = UNSET
        if not isinstance(self.domains, Unset):
            domains = self.domains

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ips is not UNSET:
            field_dict["ips"] = ips
        if asns is not UNSET:
            field_dict["asns"] = asns
        if domains is not UNSET:
            field_dict["domains"] = domains

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        ips = cast(list[str], d.pop("ips", UNSET))

        asns = cast(list[str], d.pop("asns", UNSET))

        domains = cast(list[str], d.pop("domains", UNSET))

        batch_lookup_request = cls(
            ips=ips,
            asns=asns,
            domains=domains,
        )

        batch_lookup_request.additional_properties = d
        return batch_lookup_request

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
