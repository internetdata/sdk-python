from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SatelliteDetail")


@_attrs_define
class SatelliteDetail:
    """
    Attributes:
        provider (str): The operator's ID in Satellite IP Provider.
        provider_name (str): The operator's name.
        orbit (str): The orbit: `leo`, `meo` or `geo`.
        segment (str): Who the space serves, such as consumer or maritime.
        country (str): ISO 3166 country code.
        asn (int): The AS the operator announces it from.
        confidence (str): `high`, `medium` or `low`.
    """

    provider: str
    provider_name: str
    orbit: str
    segment: str
    country: str
    asn: int
    confidence: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        provider_name = self.provider_name

        orbit = self.orbit

        segment = self.segment

        country = self.country

        asn = self.asn

        confidence = self.confidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "provider_name": provider_name,
                "orbit": orbit,
                "segment": segment,
                "country": country,
                "asn": asn,
                "confidence": confidence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        provider = d.pop("provider")

        provider_name = d.pop("provider_name")

        orbit = d.pop("orbit")

        segment = d.pop("segment")

        country = d.pop("country")

        asn = d.pop("asn")

        confidence = d.pop("confidence")

        satellite_detail = cls(
            provider=provider,
            provider_name=provider_name,
            orbit=orbit,
            segment=segment,
            country=country,
            asn=asn,
            confidence=confidence,
        )

        satellite_detail.additional_properties = d
        return satellite_detail

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
