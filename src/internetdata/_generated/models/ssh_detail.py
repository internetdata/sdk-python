from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SshDetail")


@_attrs_define
class SshDetail:
    """
    Attributes:
        port (int): The port the server answered on.
        banner (str): Its banner.
        host_key_fp (str): Its host key's fingerprint.
        session_ok (bool): A session was set up.
        first_seen (str): The first day it answered.
        last_seen (str): The last day it did.
    """

    port: int
    banner: str
    host_key_fp: str
    session_ok: bool
    first_seen: str
    last_seen: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        port = self.port

        banner = self.banner

        host_key_fp = self.host_key_fp

        session_ok = self.session_ok

        first_seen = self.first_seen

        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "port": port,
                "banner": banner,
                "host_key_fp": host_key_fp,
                "session_ok": session_ok,
                "first_seen": first_seen,
                "last_seen": last_seen,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        port = d.pop("port")

        banner = d.pop("banner")

        host_key_fp = d.pop("host_key_fp")

        session_ok = d.pop("session_ok")

        first_seen = d.pop("first_seen")

        last_seen = d.pop("last_seen")

        ssh_detail = cls(
            port=port,
            banner=banner,
            host_key_fp=host_key_fp,
            session_ok=session_ok,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        ssh_detail.additional_properties = d
        return ssh_detail

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
