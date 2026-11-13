from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.disposable_detail import DisposableDetail
    from ..models.domain_dns import DomainDns
    from ..models.domain_ip_ranges import DomainIpRanges


T = TypeVar("T", bound="DomainLookupResponse")


@_attrs_define
class DomainLookupResponse:
    """What every database says about one domain.

    Attributes:
        domain (str): The domain, lowercase and in punycode.
        is_registered (bool): In Domain List: a registered domain.
        has_a (bool): It has A records.
        has_aaaa (bool): AAAA records.
        has_mx (bool): MX records.
        has_ns (bool): NS records.
        has_cname (bool): A CNAME record.
        is_disposable (bool | Unset): In Disposable Domain. Paid plans and the trial.
        dns (DomainDns | Unset): Its records in Domain DNS, up to 100 a type. Paid plans and the trial.
        ip_ranges (DomainIpRanges | Unset): The organization's IP ranges, from Domain IP Ranges. Paid plans and the
            trial.
        disposable (DisposableDetail | Unset):
        trial_expired (bool | Unset): On every answer to a key on the free plan, and on no other: `false` while the
            day's trial of every field lasts, `true` once the answer has Unlimited's fields.
    """

    domain: str
    is_registered: bool
    has_a: bool
    has_aaaa: bool
    has_mx: bool
    has_ns: bool
    has_cname: bool
    is_disposable: bool | Unset = UNSET
    dns: DomainDns | Unset = UNSET
    ip_ranges: DomainIpRanges | Unset = UNSET
    disposable: DisposableDetail | Unset = UNSET
    trial_expired: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain = self.domain

        is_registered = self.is_registered

        has_a = self.has_a

        has_aaaa = self.has_aaaa

        has_mx = self.has_mx

        has_ns = self.has_ns

        has_cname = self.has_cname

        is_disposable = self.is_disposable

        dns: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dns, Unset):
            dns = self.dns.to_dict()

        ip_ranges: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ip_ranges, Unset):
            ip_ranges = self.ip_ranges.to_dict()

        disposable: dict[str, Any] | Unset = UNSET
        if not isinstance(self.disposable, Unset):
            disposable = self.disposable.to_dict()

        trial_expired = self.trial_expired

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domain": domain,
                "is_registered": is_registered,
                "has_a": has_a,
                "has_aaaa": has_aaaa,
                "has_mx": has_mx,
                "has_ns": has_ns,
                "has_cname": has_cname,
            }
        )
        if is_disposable is not UNSET:
            field_dict["is_disposable"] = is_disposable
        if dns is not UNSET:
            field_dict["dns"] = dns
        if ip_ranges is not UNSET:
            field_dict["ip_ranges"] = ip_ranges
        if disposable is not UNSET:
            field_dict["disposable"] = disposable
        if trial_expired is not UNSET:
            field_dict["trial_expired"] = trial_expired

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.disposable_detail import DisposableDetail
        from ..models.domain_dns import DomainDns
        from ..models.domain_ip_ranges import DomainIpRanges

        d = dict(src_dict)
        domain = d.pop("domain")

        is_registered = d.pop("is_registered")

        has_a = d.pop("has_a")

        has_aaaa = d.pop("has_aaaa")

        has_mx = d.pop("has_mx")

        has_ns = d.pop("has_ns")

        has_cname = d.pop("has_cname")

        is_disposable = d.pop("is_disposable", UNSET)

        _dns = d.pop("dns", UNSET)
        dns: DomainDns | Unset
        if isinstance(_dns, Unset):
            dns = UNSET
        else:
            dns = DomainDns.from_dict(_dns)

        _ip_ranges = d.pop("ip_ranges", UNSET)
        ip_ranges: DomainIpRanges | Unset
        if isinstance(_ip_ranges, Unset):
            ip_ranges = UNSET
        else:
            ip_ranges = DomainIpRanges.from_dict(_ip_ranges)

        _disposable = d.pop("disposable", UNSET)
        disposable: DisposableDetail | Unset
        if isinstance(_disposable, Unset):
            disposable = UNSET
        else:
            disposable = DisposableDetail.from_dict(_disposable)

        trial_expired = d.pop("trial_expired", UNSET)

        domain_lookup_response = cls(
            domain=domain,
            is_registered=is_registered,
            has_a=has_a,
            has_aaaa=has_aaaa,
            has_mx=has_mx,
            has_ns=has_ns,
            has_cname=has_cname,
            is_disposable=is_disposable,
            dns=dns,
            ip_ranges=ip_ranges,
            disposable=disposable,
            trial_expired=trial_expired,
        )

        domain_lookup_response.additional_properties = d
        return domain_lookup_response

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
