from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Asn")


@_attrs_define
class Asn:
    """The network announcing the address, from IP ASN.

    Attributes:
        asn (int): The AS announcing the address, 0 where none does.
        name (str): Its operator.
        domain (str): Its operator's domain.
        type_ (str): The kind of network it runs.
        prefix (str): The announced prefix covering the address.
        country (str | Unset): The country its registry assigned it to. Paid plans and the trial.
        rpki_status (str | Unset): The announcement's RPKI status. Paid plans and the trial.
    """

    asn: int
    name: str
    domain: str
    type_: str
    prefix: str
    country: str | Unset = UNSET
    rpki_status: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        asn = self.asn

        name = self.name

        domain = self.domain

        type_ = self.type_

        prefix = self.prefix

        country = self.country

        rpki_status = self.rpki_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "asn": asn,
                "name": name,
                "domain": domain,
                "type": type_,
                "prefix": prefix,
            }
        )
        if country is not UNSET:
            field_dict["country"] = country
        if rpki_status is not UNSET:
            field_dict["rpki_status"] = rpki_status

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        asn = d.pop("asn")

        name = d.pop("name")

        domain = d.pop("domain")

        type_ = d.pop("type")

        prefix = d.pop("prefix")

        country = d.pop("country", UNSET)

        rpki_status = d.pop("rpki_status", UNSET)

        asn = cls(
            asn=asn,
            name=name,
            domain=domain,
            type_=type_,
            prefix=prefix,
            country=country,
            rpki_status=rpki_status,
        )

        asn.additional_properties = d
        return asn

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
