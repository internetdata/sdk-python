from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AsnPrefix")


@_attrs_define
class AsnPrefix:
    """
    Attributes:
        prefix (str): The announced prefix.
        peer_count (int): How many peers saw it.
        rpki_status (str): Its RPKI status.
        first_seen (str): The first day BGP Route saw it.
        country (str): Where its first address is.
        size (int): IPv4 addresses it covers; 0 for IPv6.
        other_origins (list[int]): Every other AS announcing it.
    """

    prefix: str
    peer_count: int
    rpki_status: str
    first_seen: str
    country: str
    size: int
    other_origins: list[int]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        prefix = self.prefix

        peer_count = self.peer_count

        rpki_status = self.rpki_status

        first_seen = self.first_seen

        country = self.country

        size = self.size

        other_origins = self.other_origins

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "prefix": prefix,
                "peer_count": peer_count,
                "rpki_status": rpki_status,
                "first_seen": first_seen,
                "country": country,
                "size": size,
                "other_origins": other_origins,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        prefix = d.pop("prefix")

        peer_count = d.pop("peer_count")

        rpki_status = d.pop("rpki_status")

        first_seen = d.pop("first_seen")

        country = d.pop("country")

        size = d.pop("size")

        other_origins = cast(list[int], d.pop("other_origins"))

        asn_prefix = cls(
            prefix=prefix,
            peer_count=peer_count,
            rpki_status=rpki_status,
            first_seen=first_seen,
            country=country,
            size=size,
            other_origins=other_origins,
        )

        asn_prefix.additional_properties = d
        return asn_prefix

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
