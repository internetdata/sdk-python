from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cohosted_domains import CohostedDomains
    from ..models.disposable_detail import DisposableDetail
    from ..models.domain_backlinks import DomainBacklinks
    from ..models.domain_dns import DomainDns
    from ..models.domain_host import DomainHost
    from ..models.domain_ip_ranges import DomainIpRanges
    from ..models.domain_redirects import DomainRedirects
    from ..models.domain_web import DomainWeb


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
        hosting (list[DomainHost] | Unset): The network announcing each address in `dns.a` and then `dns.aaaa`, from IP
            ASN; `[]` where it resolves to none. Paid plans and the trial.
        cohosted_domains (CohostedDomains | Unset): From IP Hosted Domains: the other registered domains on the domain's
            first IPv4 address, how many and the 10 most popular. Paid plans and the trial.
        ip_ranges (DomainIpRanges | Unset): The organization's IP ranges, from Domain IP Ranges. Paid plans and the
            trial.
        disposable (DisposableDetail | Unset):
        web (DomainWeb | Unset): What our crawl last read of the domain's own home page, every member empty where it
            holds none. Paid plans and the trial.
        redirects (DomainRedirects | Unset): The registered domains whose home page redirects to this one, how many and
            the 10 most popular. Paid plans and the trial.
        backlinks (DomainBacklinks | Unset): The registered domains whose home page links to this one, how many and the
            10 most popular. Paid plans and the trial.
        trial_expired (bool | Unset): On every answer to a key on the free plan, and on no other: `false` while its
            organization's trial of every field lasts, `true` once the answer has Unlimited's fields.
        cap_reached (bool | Unset): On every answer to a key on a paid plan, and on no other: `false` while the answer
            has every field, `true` once its organization's overage cap is reached and the answer has Unlimited's. Lookups
            answered past the cap are not billed; raising or removing the cap in Billing turns it `false` again.
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
    hosting: list[DomainHost] | Unset = UNSET
    cohosted_domains: CohostedDomains | Unset = UNSET
    ip_ranges: DomainIpRanges | Unset = UNSET
    disposable: DisposableDetail | Unset = UNSET
    web: DomainWeb | Unset = UNSET
    redirects: DomainRedirects | Unset = UNSET
    backlinks: DomainBacklinks | Unset = UNSET
    trial_expired: bool | Unset = UNSET
    cap_reached: bool | Unset = UNSET
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

        hosting: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.hosting, Unset):
            hosting = []
            for hosting_item_data in self.hosting:
                hosting_item = hosting_item_data.to_dict()
                hosting.append(hosting_item)

        cohosted_domains: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cohosted_domains, Unset):
            cohosted_domains = self.cohosted_domains.to_dict()

        ip_ranges: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ip_ranges, Unset):
            ip_ranges = self.ip_ranges.to_dict()

        disposable: dict[str, Any] | Unset = UNSET
        if not isinstance(self.disposable, Unset):
            disposable = self.disposable.to_dict()

        web: dict[str, Any] | Unset = UNSET
        if not isinstance(self.web, Unset):
            web = self.web.to_dict()

        redirects: dict[str, Any] | Unset = UNSET
        if not isinstance(self.redirects, Unset):
            redirects = self.redirects.to_dict()

        backlinks: dict[str, Any] | Unset = UNSET
        if not isinstance(self.backlinks, Unset):
            backlinks = self.backlinks.to_dict()

        trial_expired = self.trial_expired

        cap_reached = self.cap_reached

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
        if hosting is not UNSET:
            field_dict["hosting"] = hosting
        if cohosted_domains is not UNSET:
            field_dict["cohosted_domains"] = cohosted_domains
        if ip_ranges is not UNSET:
            field_dict["ip_ranges"] = ip_ranges
        if disposable is not UNSET:
            field_dict["disposable"] = disposable
        if web is not UNSET:
            field_dict["web"] = web
        if redirects is not UNSET:
            field_dict["redirects"] = redirects
        if backlinks is not UNSET:
            field_dict["backlinks"] = backlinks
        if trial_expired is not UNSET:
            field_dict["trial_expired"] = trial_expired
        if cap_reached is not UNSET:
            field_dict["cap_reached"] = cap_reached

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.cohosted_domains import CohostedDomains
        from ..models.disposable_detail import DisposableDetail
        from ..models.domain_backlinks import DomainBacklinks
        from ..models.domain_dns import DomainDns
        from ..models.domain_host import DomainHost
        from ..models.domain_ip_ranges import DomainIpRanges
        from ..models.domain_redirects import DomainRedirects
        from ..models.domain_web import DomainWeb

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

        _hosting = d.pop("hosting", UNSET)
        hosting: list[DomainHost] | Unset = UNSET
        if _hosting is not UNSET:
            hosting = []
            for hosting_item_data in _hosting:
                hosting_item = DomainHost.from_dict(hosting_item_data)

                hosting.append(hosting_item)

        _cohosted_domains = d.pop("cohosted_domains", UNSET)
        cohosted_domains: CohostedDomains | Unset
        if isinstance(_cohosted_domains, Unset):
            cohosted_domains = UNSET
        else:
            cohosted_domains = CohostedDomains.from_dict(_cohosted_domains)

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

        _web = d.pop("web", UNSET)
        web: DomainWeb | Unset
        if isinstance(_web, Unset):
            web = UNSET
        else:
            web = DomainWeb.from_dict(_web)

        _redirects = d.pop("redirects", UNSET)
        redirects: DomainRedirects | Unset
        if isinstance(_redirects, Unset):
            redirects = UNSET
        else:
            redirects = DomainRedirects.from_dict(_redirects)

        _backlinks = d.pop("backlinks", UNSET)
        backlinks: DomainBacklinks | Unset
        if isinstance(_backlinks, Unset):
            backlinks = UNSET
        else:
            backlinks = DomainBacklinks.from_dict(_backlinks)

        trial_expired = d.pop("trial_expired", UNSET)

        cap_reached = d.pop("cap_reached", UNSET)

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
            hosting=hosting,
            cohosted_domains=cohosted_domains,
            ip_ranges=ip_ranges,
            disposable=disposable,
            web=web,
            redirects=redirects,
            backlinks=backlinks,
            trial_expired=trial_expired,
            cap_reached=cap_reached,
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
