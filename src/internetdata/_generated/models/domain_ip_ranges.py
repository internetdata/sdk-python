from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.domain_ip_range import DomainIpRange


T = TypeVar("T", bound="DomainIpRanges")


@_attrs_define
class DomainIpRanges:
    """The organization's IP ranges, from Domain IP Ranges. Paid plans and the trial.

    Attributes:
        domain (str): The organization's domain.
        redirects_to (str): Where its home page redirects, when that is how it was reached.
        total (int): How many ranges it holds.
        ipv4 (int): IPv4 addresses across them.
        ranges (list[DomainIpRange]): The first 1000, IPv4 before IPv6, the largest first.
    """

    domain: str
    redirects_to: str
    total: int
    ipv4: int
    ranges: list[DomainIpRange]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain = self.domain

        redirects_to = self.redirects_to

        total = self.total

        ipv4 = self.ipv4

        ranges = []
        for ranges_item_data in self.ranges:
            ranges_item = ranges_item_data.to_dict()
            ranges.append(ranges_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domain": domain,
                "redirects_to": redirects_to,
                "total": total,
                "ipv4": ipv4,
                "ranges": ranges,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.domain_ip_range import DomainIpRange

        d = dict(src_dict)
        domain = d.pop("domain")

        redirects_to = d.pop("redirects_to")

        total = d.pop("total")

        ipv4 = d.pop("ipv4")

        ranges = []
        _ranges = d.pop("ranges")
        for ranges_item_data in _ranges:
            ranges_item = DomainIpRange.from_dict(ranges_item_data)

            ranges.append(ranges_item)

        domain_ip_ranges = cls(
            domain=domain,
            redirects_to=redirects_to,
            total=total,
            ipv4=ipv4,
            ranges=ranges,
        )

        domain_ip_ranges.additional_properties = d
        return domain_ip_ranges

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
