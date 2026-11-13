from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DisposableDetail")


@_attrs_define
class DisposableDetail:
    """
    Attributes:
        confidence (str | Unset): `high`, `medium` or `low`.
        providers (list[str] | Unset): The providers behind it.
        first_seen (str | Unset): The first day seen in use.
        last_seen (str | Unset): The last day.
    """

    confidence: str | Unset = UNSET
    providers: list[str] | Unset = UNSET
    first_seen: str | Unset = UNSET
    last_seen: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        confidence = self.confidence

        providers: list[str] | Unset = UNSET
        if not isinstance(self.providers, Unset):
            providers = self.providers

        first_seen = self.first_seen

        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if providers is not UNSET:
            field_dict["providers"] = providers
        if first_seen is not UNSET:
            field_dict["first_seen"] = first_seen
        if last_seen is not UNSET:
            field_dict["last_seen"] = last_seen

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        confidence = d.pop("confidence", UNSET)

        providers = cast(list[str], d.pop("providers", UNSET))

        first_seen = d.pop("first_seen", UNSET)

        last_seen = d.pop("last_seen", UNSET)

        disposable_detail = cls(
            confidence=confidence,
            providers=providers,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        disposable_detail.additional_properties = d
        return disposable_detail

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
