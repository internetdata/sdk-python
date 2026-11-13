from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Whois")


@_attrs_define
class Whois:
    """IP Whois's most specific record covering the address. Paid plans and the trial.

    Attributes:
        id (str): Network name of the most specific record covering the address.
        name (str): Its holder.
        org (str): The registry's handle for the holder.
        country (str): ISO 3166 country code.
        status (str): The registry's assignment status.
        source (str): The registry, or rwhois.
        domain (str): The holder's domain.
        abuse_email (str): The record's abuse contact.
        asn (int): The AS announcing the record's start address.
    """

    id: str
    name: str
    org: str
    country: str
    status: str
    source: str
    domain: str
    abuse_email: str
    asn: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        org = self.org

        country = self.country

        status = self.status

        source = self.source

        domain = self.domain

        abuse_email = self.abuse_email

        asn = self.asn

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "org": org,
                "country": country,
                "status": status,
                "source": source,
                "domain": domain,
                "abuse_email": abuse_email,
                "asn": asn,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        org = d.pop("org")

        country = d.pop("country")

        status = d.pop("status")

        source = d.pop("source")

        domain = d.pop("domain")

        abuse_email = d.pop("abuse_email")

        asn = d.pop("asn")

        whois = cls(
            id=id,
            name=name,
            org=org,
            country=country,
            status=status,
            source=source,
            domain=domain,
            abuse_email=abuse_email,
            asn=asn,
        )

        whois.additional_properties = d
        return whois

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
