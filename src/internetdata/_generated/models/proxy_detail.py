from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ProxyDetail")


@_attrs_define
class ProxyDetail:
    """
    Attributes:
        provider (str): The proxy pool's ID in its catalog, empty where unattributed.
        provider_name (str): The name the catalog gives it.
        first_seen (str): The first day of the window the address was seen as an exit.
        last_seen (str): The last day it was.
        hits (int): How many times it was seen in the window.
        hits_days_pct (int): On what share of the window's days, in percent.
        providers_num (int): How many pools it was seen in.
    """

    provider: str
    provider_name: str
    first_seen: str
    last_seen: str
    hits: int
    hits_days_pct: int
    providers_num: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        provider_name = self.provider_name

        first_seen = self.first_seen

        last_seen = self.last_seen

        hits = self.hits

        hits_days_pct = self.hits_days_pct

        providers_num = self.providers_num

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "provider_name": provider_name,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "hits": hits,
                "hits_days_pct": hits_days_pct,
                "providers_num": providers_num,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        provider = d.pop("provider")

        provider_name = d.pop("provider_name")

        first_seen = d.pop("first_seen")

        last_seen = d.pop("last_seen")

        hits = d.pop("hits")

        hits_days_pct = d.pop("hits_days_pct")

        providers_num = d.pop("providers_num")

        proxy_detail = cls(
            provider=provider,
            provider_name=provider_name,
            first_seen=first_seen,
            last_seen=last_seen,
            hits=hits,
            hits_days_pct=hits_days_pct,
            providers_num=providers_num,
        )

        proxy_detail.additional_properties = d
        return proxy_detail

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
