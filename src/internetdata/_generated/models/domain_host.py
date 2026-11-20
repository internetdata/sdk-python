from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.asn import Asn


T = TypeVar("T", bound="DomainHost")


@_attrs_define
class DomainHost:
    """An address the domain resolves to and the network announcing it.

    Attributes:
        ip (str): One address the domain resolves to.
        asn (Asn): The network announcing the address, from IP ASN.
    """

    ip: str
    asn: Asn
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip = self.ip

        asn = self.asn.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ip": ip,
                "asn": asn,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.asn import Asn

        d = dict(src_dict)
        ip = d.pop("ip")

        asn = Asn.from_dict(d.pop("asn"))

        domain_host = cls(
            ip=ip,
            asn=asn,
        )

        domain_host.additional_properties = d
        return domain_host

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
