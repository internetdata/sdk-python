from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CarrierDetail")


@_attrs_define
class CarrierDetail:
    """
    Attributes:
        name (str): The mobile carrier.
        mcc (str): Its mobile country code.
        mnc (str): Its mobile network code.
        country (str): ISO 3166 country code.
        confidence (str): `high`, `medium` or `low`.
    """

    name: str
    mcc: str
    mnc: str
    country: str
    confidence: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        mcc = self.mcc

        mnc = self.mnc

        country = self.country

        confidence = self.confidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "mcc": mcc,
                "mnc": mnc,
                "country": country,
                "confidence": confidence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        name = d.pop("name")

        mcc = d.pop("mcc")

        mnc = d.pop("mnc")

        country = d.pop("country")

        confidence = d.pop("confidence")

        carrier_detail = cls(
            name=name,
            mcc=mcc,
            mnc=mnc,
            country=country,
            confidence=confidence,
        )

        carrier_detail.additional_properties = d
        return carrier_detail

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
