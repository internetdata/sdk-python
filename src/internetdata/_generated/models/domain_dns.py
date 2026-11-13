from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dns_address_record import DnsAddressRecord
    from ..models.dns_cname_record import DnsCnameRecord
    from ..models.dns_mx_record import DnsMxRecord
    from ..models.dns_ns_record import DnsNsRecord


T = TypeVar("T", bound="DomainDns")


@_attrs_define
class DomainDns:
    """Its records in Domain DNS, up to 100 a type. Paid plans and the trial.

    Attributes:
        a (list[DnsAddressRecord]):
        aaaa (list[DnsAddressRecord]):
        mx (list[DnsMxRecord]):
        ns (list[DnsNsRecord]):
        cname (list[DnsCnameRecord]):
    """

    a: list[DnsAddressRecord]
    aaaa: list[DnsAddressRecord]
    mx: list[DnsMxRecord]
    ns: list[DnsNsRecord]
    cname: list[DnsCnameRecord]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        a = []
        for a_item_data in self.a:
            a_item = a_item_data.to_dict()
            a.append(a_item)

        aaaa = []
        for aaaa_item_data in self.aaaa:
            aaaa_item = aaaa_item_data.to_dict()
            aaaa.append(aaaa_item)

        mx = []
        for mx_item_data in self.mx:
            mx_item = mx_item_data.to_dict()
            mx.append(mx_item)

        ns = []
        for ns_item_data in self.ns:
            ns_item = ns_item_data.to_dict()
            ns.append(ns_item)

        cname = []
        for cname_item_data in self.cname:
            cname_item = cname_item_data.to_dict()
            cname.append(cname_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "a": a,
                "aaaa": aaaa,
                "mx": mx,
                "ns": ns,
                "cname": cname,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.dns_address_record import DnsAddressRecord
        from ..models.dns_cname_record import DnsCnameRecord
        from ..models.dns_mx_record import DnsMxRecord
        from ..models.dns_ns_record import DnsNsRecord

        d = dict(src_dict)
        a = []
        _a = d.pop("a")
        for a_item_data in _a:
            a_item = DnsAddressRecord.from_dict(a_item_data)

            a.append(a_item)

        aaaa = []
        _aaaa = d.pop("aaaa")
        for aaaa_item_data in _aaaa:
            aaaa_item = DnsAddressRecord.from_dict(aaaa_item_data)

            aaaa.append(aaaa_item)

        mx = []
        _mx = d.pop("mx")
        for mx_item_data in _mx:
            mx_item = DnsMxRecord.from_dict(mx_item_data)

            mx.append(mx_item)

        ns = []
        _ns = d.pop("ns")
        for ns_item_data in _ns:
            ns_item = DnsNsRecord.from_dict(ns_item_data)

            ns.append(ns_item)

        cname = []
        _cname = d.pop("cname")
        for cname_item_data in _cname:
            cname_item = DnsCnameRecord.from_dict(cname_item_data)

            cname.append(cname_item)

        domain_dns = cls(
            a=a,
            aaaa=aaaa,
            mx=mx,
            ns=ns,
            cname=cname,
        )

        domain_dns.additional_properties = d
        return domain_dns

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
