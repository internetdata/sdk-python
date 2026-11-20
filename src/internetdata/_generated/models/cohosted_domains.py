from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CohostedDomains")


@_attrs_define
class CohostedDomains:
    """From IP Hosted Domains: the other registered domains on the domain's first IPv4 address, how many and the 10 most
    popular. Paid plans and the trial.

        Attributes:
            ip (str): The domain's first IPv4 address, `''` where it has none.
            total (int): How many other registered domains resolve to it.
            domains (list[str]): Up to 10 of them, the most popular first, the domain itself left out; `[]` when none does.
    """

    ip: str
    total: int
    domains: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip = self.ip

        total = self.total

        domains = self.domains

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ip": ip,
                "total": total,
                "domains": domains,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        ip = d.pop("ip")

        total = d.pop("total")

        domains = cast(list[str], d.pop("domains"))

        cohosted_domains = cls(
            ip=ip,
            total=total,
            domains=domains,
        )

        cohosted_domains.additional_properties = d
        return cohosted_domains

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
