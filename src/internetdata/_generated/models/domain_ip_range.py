from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DomainIpRange")


@_attrs_define
class DomainIpRange:
    """
    Attributes:
        range_ (str): The range.
        name (str): Its registry name.
        country (str): ISO 3166 country code.
    """

    range_: str
    name: str
    country: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        range_ = self.range_

        name = self.name

        country = self.country

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "range": range_,
                "name": name,
                "country": country,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        range_ = d.pop("range")

        name = d.pop("name")

        country = d.pop("country")

        domain_ip_range = cls(
            range_=range_,
            name=name,
            country=country,
        )

        domain_ip_range.additional_properties = d
        return domain_ip_range

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
