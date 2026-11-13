from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PubproxyDetail")


@_attrs_define
class PubproxyDetail:
    """
    Attributes:
        entry (bool): A public proxy listens here.
        exit_ (bool): Public proxies' traffic leaves from here.
        protocols (list[str]): The protocols at either end, `[]` when unknown.
        num_ports (int): How many ports a proxy listens on here.
        num_proxies (int): How many proxies' traffic left from here.
        last_seen (str): The last day one was seen.
        last_usable (str): The last day one answered a request, empty when none did.
    """

    entry: bool
    exit_: bool
    protocols: list[str]
    num_ports: int
    num_proxies: int
    last_seen: str
    last_usable: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        entry = self.entry

        exit_ = self.exit_

        protocols = self.protocols

        num_ports = self.num_ports

        num_proxies = self.num_proxies

        last_seen = self.last_seen

        last_usable = self.last_usable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entry": entry,
                "exit": exit_,
                "protocols": protocols,
                "num_ports": num_ports,
                "num_proxies": num_proxies,
                "last_seen": last_seen,
                "last_usable": last_usable,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        entry = d.pop("entry")

        exit_ = d.pop("exit")

        protocols = cast(list[str], d.pop("protocols"))

        num_ports = d.pop("num_ports")

        num_proxies = d.pop("num_proxies")

        last_seen = d.pop("last_seen")

        last_usable = d.pop("last_usable")

        pubproxy_detail = cls(
            entry=entry,
            exit_=exit_,
            protocols=protocols,
            num_ports=num_ports,
            num_proxies=num_proxies,
            last_seen=last_seen,
            last_usable=last_usable,
        )

        pubproxy_detail.additional_properties = d
        return pubproxy_detail

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
