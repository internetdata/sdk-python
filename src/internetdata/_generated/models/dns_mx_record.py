from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DnsMxRecord")


@_attrs_define
class DnsMxRecord:
    """
    Attributes:
        priority (int): Its priority.
        host (str): The mail host.
        last_seen (str): The last day seen.
    """

    priority: int
    host: str
    last_seen: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        priority = self.priority

        host = self.host

        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "priority": priority,
                "host": host,
                "last_seen": last_seen,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        priority = d.pop("priority")

        host = d.pop("host")

        last_seen = d.pop("last_seen")

        dns_mx_record = cls(
            priority=priority,
            host=host,
            last_seen=last_seen,
        )

        dns_mx_record.additional_properties = d
        return dns_mx_record

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
