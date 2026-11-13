from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AbuseContact")


@_attrs_define
class AbuseContact:
    """Where to report abuse, from IP Abuse Contact.

    Attributes:
        email (str): Where to report abuse from the address.
        name (str | Unset): The contact. Paid plans and the trial.
        phone (str | Unset): Its phone number. Paid plans and the trial.
        address (str | Unset): Its postal address. Paid plans and the trial.
        country (str | Unset): ISO 3166 country code. Paid plans and the trial.
        network (str | Unset): The registry block it was derived from. Paid plans and the trial.
        validated (bool | Unset): ARIN reports the contact answered its yearly validation. Paid plans and the trial.
        unvalidated_since (str | Unset): Since when it has not. Paid plans and the trial.
    """

    email: str
    name: str | Unset = UNSET
    phone: str | Unset = UNSET
    address: str | Unset = UNSET
    country: str | Unset = UNSET
    network: str | Unset = UNSET
    validated: bool | Unset = UNSET
    unvalidated_since: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        name = self.name

        phone = self.phone

        address = self.address

        country = self.country

        network = self.network

        validated = self.validated

        unvalidated_since = self.unvalidated_since

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if phone is not UNSET:
            field_dict["phone"] = phone
        if address is not UNSET:
            field_dict["address"] = address
        if country is not UNSET:
            field_dict["country"] = country
        if network is not UNSET:
            field_dict["network"] = network
        if validated is not UNSET:
            field_dict["validated"] = validated
        if unvalidated_since is not UNSET:
            field_dict["unvalidated_since"] = unvalidated_since

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        email = d.pop("email")

        name = d.pop("name", UNSET)

        phone = d.pop("phone", UNSET)

        address = d.pop("address", UNSET)

        country = d.pop("country", UNSET)

        network = d.pop("network", UNSET)

        validated = d.pop("validated", UNSET)

        unvalidated_since = d.pop("unvalidated_since", UNSET)

        abuse_contact = cls(
            email=email,
            name=name,
            phone=phone,
            address=address,
            country=country,
            network=network,
            validated=validated,
            unvalidated_since=unvalidated_since,
        )

        abuse_contact.additional_properties = d
        return abuse_contact

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
