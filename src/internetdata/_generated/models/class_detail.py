from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClassDetail")


@_attrs_define
class ClassDetail:
    """
    Attributes:
        provider (str | Unset): The provider's ID in its catalog; empty for an unattributed range, and on Tor.
        provider_name (str | Unset): The name the catalog gives the provider, empty where it names none.
        confidence (str | Unset): `high`, `medium` or `low`: how sure we are the range is what the flag says.
        last_seen (str | Unset): The last day the range was seen as such.
    """

    provider: str | Unset = UNSET
    provider_name: str | Unset = UNSET
    confidence: str | Unset = UNSET
    last_seen: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        provider_name = self.provider_name

        confidence = self.confidence

        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if provider is not UNSET:
            field_dict["provider"] = provider
        if provider_name is not UNSET:
            field_dict["provider_name"] = provider_name
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if last_seen is not UNSET:
            field_dict["last_seen"] = last_seen

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        provider = d.pop("provider", UNSET)

        provider_name = d.pop("provider_name", UNSET)

        confidence = d.pop("confidence", UNSET)

        last_seen = d.pop("last_seen", UNSET)

        class_detail = cls(
            provider=provider,
            provider_name=provider_name,
            confidence=confidence,
            last_seen=last_seen,
        )

        class_detail.additional_properties = d
        return class_detail

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
