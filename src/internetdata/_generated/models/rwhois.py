from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Rwhois")


@_attrs_define
class Rwhois:
    """IP RWHOIS's most specific network covering the address. Paid plans and the trial.

    Attributes:
        id (str): The network's identifier on the operator's RWHOIS server.
        name (str): Its assignee.
        country (str): ISO 3166 country code.
        source (str): The operator that published it.
        domain (str): The contact emails' domain.
        abuse_email (str): Its abuse contact.
    """

    id: str
    name: str
    country: str
    source: str
    domain: str
    abuse_email: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        country = self.country

        source = self.source

        domain = self.domain

        abuse_email = self.abuse_email

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "country": country,
                "source": source,
                "domain": domain,
                "abuse_email": abuse_email,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        country = d.pop("country")

        source = d.pop("source")

        domain = d.pop("domain")

        abuse_email = d.pop("abuse_email")

        rwhois = cls(
            id=id,
            name=name,
            country=country,
            source=source,
            domain=domain,
            abuse_email=abuse_email,
        )

        rwhois.additional_properties = d
        return rwhois

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
