from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BitTorrentDetail")


@_attrs_define
class BitTorrentDetail:
    """
    Attributes:
        verified (bool): A client here answered, or two or more reported it at once.
        id_matches_ip (bool): A client here derived its node ID from the address (BEP 42).
        first_seen (str): The first day a client was seen here.
        last_seen (str): The last day.
        last_reachable (str): The last day one answered, empty when none did.
        days_seen (int): On how many days.
        num_ports (int): Distinct ports over the window.
        peak_num_ports (int): The most on one day.
        indexer (bool): A DHT indexer rather than people.
        clients (list[str]): The two-letter codes its clients name themselves by.
    """

    verified: bool
    id_matches_ip: bool
    first_seen: str
    last_seen: str
    last_reachable: str
    days_seen: int
    num_ports: int
    peak_num_ports: int
    indexer: bool
    clients: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        verified = self.verified

        id_matches_ip = self.id_matches_ip

        first_seen = self.first_seen

        last_seen = self.last_seen

        last_reachable = self.last_reachable

        days_seen = self.days_seen

        num_ports = self.num_ports

        peak_num_ports = self.peak_num_ports

        indexer = self.indexer

        clients = self.clients

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "verified": verified,
                "id_matches_ip": id_matches_ip,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "last_reachable": last_reachable,
                "days_seen": days_seen,
                "num_ports": num_ports,
                "peak_num_ports": peak_num_ports,
                "indexer": indexer,
                "clients": clients,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        verified = d.pop("verified")

        id_matches_ip = d.pop("id_matches_ip")

        first_seen = d.pop("first_seen")

        last_seen = d.pop("last_seen")

        last_reachable = d.pop("last_reachable")

        days_seen = d.pop("days_seen")

        num_ports = d.pop("num_ports")

        peak_num_ports = d.pop("peak_num_ports")

        indexer = d.pop("indexer")

        clients = cast(list[str], d.pop("clients"))

        bit_torrent_detail = cls(
            verified=verified,
            id_matches_ip=id_matches_ip,
            first_seen=first_seen,
            last_seen=last_seen,
            last_reachable=last_reachable,
            days_seen=days_seen,
            num_ports=num_ports,
            peak_num_ports=peak_num_ports,
            indexer=indexer,
            clients=clients,
        )

        bit_torrent_detail.additional_properties = d
        return bit_torrent_detail

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
