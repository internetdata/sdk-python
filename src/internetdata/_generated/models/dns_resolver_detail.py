from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DnsResolverDetail")


@_attrs_define
class DnsResolverDetail:
    """
    Attributes:
        port (int): The port it answered on.
        recursion_available (bool): It offered recursion.
        rcode (int): Its answer's response code.
        answer_correct (bool): Its answer was right.
        first_seen (str): The first day it answered.
        last_seen (str): The last day it did.
    """

    port: int
    recursion_available: bool
    rcode: int
    answer_correct: bool
    first_seen: str
    last_seen: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        port = self.port

        recursion_available = self.recursion_available

        rcode = self.rcode

        answer_correct = self.answer_correct

        first_seen = self.first_seen

        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "port": port,
                "recursion_available": recursion_available,
                "rcode": rcode,
                "answer_correct": answer_correct,
                "first_seen": first_seen,
                "last_seen": last_seen,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        port = d.pop("port")

        recursion_available = d.pop("recursion_available")

        rcode = d.pop("rcode")

        answer_correct = d.pop("answer_correct")

        first_seen = d.pop("first_seen")

        last_seen = d.pop("last_seen")

        dns_resolver_detail = cls(
            port=port,
            recursion_available=recursion_available,
            rcode=rcode,
            answer_correct=answer_correct,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        dns_resolver_detail.additional_properties = d
        return dns_resolver_detail

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
