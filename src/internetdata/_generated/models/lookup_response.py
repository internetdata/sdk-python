from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.abuse_contact import AbuseContact
    from ..models.asn import Asn
    from ..models.bit_torrent_detail import BitTorrentDetail
    from ..models.carrier_detail import CarrierDetail
    from ..models.class_detail import ClassDetail
    from ..models.company import Company
    from ..models.dns_resolver_detail import DnsResolverDetail
    from ..models.hosted_domains import HostedDomains
    from ..models.location import Location
    from ..models.proxy_detail import ProxyDetail
    from ..models.pubproxy_detail import PubproxyDetail
    from ..models.rwhois import Rwhois
    from ..models.satellite_detail import SatelliteDetail
    from ..models.smtp_detail import SmtpDetail
    from ..models.ssh_detail import SshDetail
    from ..models.web_detail import WebDetail
    from ..models.whois import Whois


T = TypeVar("T", bound="LookupResponse")


@_attrs_define
class LookupResponse:
    """What every database says about one address.

    Attributes:
        ip (str): The address looked up, as parsed: `::ffff:a.b.c.d` answers as `a.b.c.d`.
        is_bogon (bool): Reserved space, answered from the address alone.
        is_tor (bool): In Tor IP: a Tor exit.
        is_relay (bool): In Relay IP: an anonymizing relay such as iCloud Private Relay.
        is_anycast (bool): In Anycast IP: announced from many places at once.
        is_carrier (bool): In Carrier IP: a mobile carrier's address space.
        is_satellite (bool): In Satellite IP: a satellite operator's address space.
        is_ssh (bool): In SSH IP: an SSH server answered here.
        is_smtp (bool): In SMTP IP: a mail server answered here.
        is_web (bool): In Web IP: a web server answered here on port 80 or 443.
        is_dns_resolver (bool): In DNS Resolver IP: an open DNS resolver answered here.
        is_bittorrent (bool): In BitTorrent IP: a BitTorrent client was seen here in the last 90 days.
        tor (ClassDetail):
        relay (ClassDetail):
        location (Location): Where the address is.
        asn (Asn): The network announcing the address, from IP ASN.
        company (Company): Who uses the address, from IP Company.
        hostname (str): The name the address's reverse DNS (PTR) record points to in IP RDNS, empty when it has none.
        abuse (AbuseContact): Where to report abuse, from IP Abuse Contact.
        is_vpn (bool | Unset): In VPN IP: a VPN service's server. Paid plans and the trial.
        is_resproxy (bool | Unset): In Residential Proxy IP's 90-day window: a residential proxy exit. Paid plans and
            the trial.
        is_dcproxy (bool | Unset): In Datacenter Proxy IP's 90-day window. Paid plans and the trial.
        is_mobproxy (bool | Unset): In Mobile Proxy IP's 90-day window. Paid plans and the trial.
        is_pubproxy (bool | Unset): In Public Proxy IP: a public proxy listens here, or its traffic left from here. Paid
            plans and the trial.
        is_hosting (bool | Unset): In Hosting IP: a hosting or cloud network. Paid plans and the trial.
        is_cdn (bool | Unset): In CDN IP: a content delivery network. Paid plans and the trial.
        vpn (ClassDetail | Unset):
        resproxy (ProxyDetail | Unset):
        dcproxy (ProxyDetail | Unset):
        mobproxy (ProxyDetail | Unset):
        pubproxy (PubproxyDetail | Unset):
        hosting (ClassDetail | Unset):
        cdn (ClassDetail | Unset):
        carrier (CarrierDetail | Unset):
        satellite (SatelliteDetail | Unset):
        ssh (SshDetail | Unset):
        smtp (SmtpDetail | Unset):
        web (list[WebDetail] | Unset): A row per port that answered, lowest first; `[]` when `is_web` is false. Paid
            plans and the trial.
        dns_resolver (DnsResolverDetail | Unset):
        bittorrent (BitTorrentDetail | Unset):
        whois (Whois | Unset): IP Whois's most specific record covering the address. Paid plans and the trial.
        rwhois (Rwhois | Unset): IP RWHOIS's most specific network covering the address. Paid plans and the trial.
        hosted_domains (HostedDomains | Unset): From IP Hosted Domains: a count, never the list. Paid plans and the
            trial.
        trial_expired (bool | Unset): On every answer to a key on the free plan, and on no other: `false` while the
            day's trial of every field lasts, `true` once the answer has Unlimited's fields.
    """

    ip: str
    is_bogon: bool
    is_tor: bool
    is_relay: bool
    is_anycast: bool
    is_carrier: bool
    is_satellite: bool
    is_ssh: bool
    is_smtp: bool
    is_web: bool
    is_dns_resolver: bool
    is_bittorrent: bool
    tor: ClassDetail
    relay: ClassDetail
    location: Location
    asn: Asn
    company: Company
    hostname: str
    abuse: AbuseContact
    is_vpn: bool | Unset = UNSET
    is_resproxy: bool | Unset = UNSET
    is_dcproxy: bool | Unset = UNSET
    is_mobproxy: bool | Unset = UNSET
    is_pubproxy: bool | Unset = UNSET
    is_hosting: bool | Unset = UNSET
    is_cdn: bool | Unset = UNSET
    vpn: ClassDetail | Unset = UNSET
    resproxy: ProxyDetail | Unset = UNSET
    dcproxy: ProxyDetail | Unset = UNSET
    mobproxy: ProxyDetail | Unset = UNSET
    pubproxy: PubproxyDetail | Unset = UNSET
    hosting: ClassDetail | Unset = UNSET
    cdn: ClassDetail | Unset = UNSET
    carrier: CarrierDetail | Unset = UNSET
    satellite: SatelliteDetail | Unset = UNSET
    ssh: SshDetail | Unset = UNSET
    smtp: SmtpDetail | Unset = UNSET
    web: list[WebDetail] | Unset = UNSET
    dns_resolver: DnsResolverDetail | Unset = UNSET
    bittorrent: BitTorrentDetail | Unset = UNSET
    whois: Whois | Unset = UNSET
    rwhois: Rwhois | Unset = UNSET
    hosted_domains: HostedDomains | Unset = UNSET
    trial_expired: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ip = self.ip

        is_bogon = self.is_bogon

        is_tor = self.is_tor

        is_relay = self.is_relay

        is_anycast = self.is_anycast

        is_carrier = self.is_carrier

        is_satellite = self.is_satellite

        is_ssh = self.is_ssh

        is_smtp = self.is_smtp

        is_web = self.is_web

        is_dns_resolver = self.is_dns_resolver

        is_bittorrent = self.is_bittorrent

        tor = self.tor.to_dict()

        relay = self.relay.to_dict()

        location = self.location.to_dict()

        asn = self.asn.to_dict()

        company = self.company.to_dict()

        hostname = self.hostname

        abuse = self.abuse.to_dict()

        is_vpn = self.is_vpn

        is_resproxy = self.is_resproxy

        is_dcproxy = self.is_dcproxy

        is_mobproxy = self.is_mobproxy

        is_pubproxy = self.is_pubproxy

        is_hosting = self.is_hosting

        is_cdn = self.is_cdn

        vpn: dict[str, Any] | Unset = UNSET
        if not isinstance(self.vpn, Unset):
            vpn = self.vpn.to_dict()

        resproxy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resproxy, Unset):
            resproxy = self.resproxy.to_dict()

        dcproxy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dcproxy, Unset):
            dcproxy = self.dcproxy.to_dict()

        mobproxy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.mobproxy, Unset):
            mobproxy = self.mobproxy.to_dict()

        pubproxy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pubproxy, Unset):
            pubproxy = self.pubproxy.to_dict()

        hosting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.hosting, Unset):
            hosting = self.hosting.to_dict()

        cdn: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cdn, Unset):
            cdn = self.cdn.to_dict()

        carrier: dict[str, Any] | Unset = UNSET
        if not isinstance(self.carrier, Unset):
            carrier = self.carrier.to_dict()

        satellite: dict[str, Any] | Unset = UNSET
        if not isinstance(self.satellite, Unset):
            satellite = self.satellite.to_dict()

        ssh: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ssh, Unset):
            ssh = self.ssh.to_dict()

        smtp: dict[str, Any] | Unset = UNSET
        if not isinstance(self.smtp, Unset):
            smtp = self.smtp.to_dict()

        web: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.web, Unset):
            web = []
            for web_item_data in self.web:
                web_item = web_item_data.to_dict()
                web.append(web_item)

        dns_resolver: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dns_resolver, Unset):
            dns_resolver = self.dns_resolver.to_dict()

        bittorrent: dict[str, Any] | Unset = UNSET
        if not isinstance(self.bittorrent, Unset):
            bittorrent = self.bittorrent.to_dict()

        whois: dict[str, Any] | Unset = UNSET
        if not isinstance(self.whois, Unset):
            whois = self.whois.to_dict()

        rwhois: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rwhois, Unset):
            rwhois = self.rwhois.to_dict()

        hosted_domains: dict[str, Any] | Unset = UNSET
        if not isinstance(self.hosted_domains, Unset):
            hosted_domains = self.hosted_domains.to_dict()

        trial_expired = self.trial_expired

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ip": ip,
                "is_bogon": is_bogon,
                "is_tor": is_tor,
                "is_relay": is_relay,
                "is_anycast": is_anycast,
                "is_carrier": is_carrier,
                "is_satellite": is_satellite,
                "is_ssh": is_ssh,
                "is_smtp": is_smtp,
                "is_web": is_web,
                "is_dns_resolver": is_dns_resolver,
                "is_bittorrent": is_bittorrent,
                "tor": tor,
                "relay": relay,
                "location": location,
                "asn": asn,
                "company": company,
                "hostname": hostname,
                "abuse": abuse,
            }
        )
        if is_vpn is not UNSET:
            field_dict["is_vpn"] = is_vpn
        if is_resproxy is not UNSET:
            field_dict["is_resproxy"] = is_resproxy
        if is_dcproxy is not UNSET:
            field_dict["is_dcproxy"] = is_dcproxy
        if is_mobproxy is not UNSET:
            field_dict["is_mobproxy"] = is_mobproxy
        if is_pubproxy is not UNSET:
            field_dict["is_pubproxy"] = is_pubproxy
        if is_hosting is not UNSET:
            field_dict["is_hosting"] = is_hosting
        if is_cdn is not UNSET:
            field_dict["is_cdn"] = is_cdn
        if vpn is not UNSET:
            field_dict["vpn"] = vpn
        if resproxy is not UNSET:
            field_dict["resproxy"] = resproxy
        if dcproxy is not UNSET:
            field_dict["dcproxy"] = dcproxy
        if mobproxy is not UNSET:
            field_dict["mobproxy"] = mobproxy
        if pubproxy is not UNSET:
            field_dict["pubproxy"] = pubproxy
        if hosting is not UNSET:
            field_dict["hosting"] = hosting
        if cdn is not UNSET:
            field_dict["cdn"] = cdn
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if satellite is not UNSET:
            field_dict["satellite"] = satellite
        if ssh is not UNSET:
            field_dict["ssh"] = ssh
        if smtp is not UNSET:
            field_dict["smtp"] = smtp
        if web is not UNSET:
            field_dict["web"] = web
        if dns_resolver is not UNSET:
            field_dict["dns_resolver"] = dns_resolver
        if bittorrent is not UNSET:
            field_dict["bittorrent"] = bittorrent
        if whois is not UNSET:
            field_dict["whois"] = whois
        if rwhois is not UNSET:
            field_dict["rwhois"] = rwhois
        if hosted_domains is not UNSET:
            field_dict["hosted_domains"] = hosted_domains
        if trial_expired is not UNSET:
            field_dict["trial_expired"] = trial_expired

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.abuse_contact import AbuseContact
        from ..models.asn import Asn
        from ..models.bit_torrent_detail import BitTorrentDetail
        from ..models.carrier_detail import CarrierDetail
        from ..models.class_detail import ClassDetail
        from ..models.company import Company
        from ..models.dns_resolver_detail import DnsResolverDetail
        from ..models.hosted_domains import HostedDomains
        from ..models.location import Location
        from ..models.proxy_detail import ProxyDetail
        from ..models.pubproxy_detail import PubproxyDetail
        from ..models.rwhois import Rwhois
        from ..models.satellite_detail import SatelliteDetail
        from ..models.smtp_detail import SmtpDetail
        from ..models.ssh_detail import SshDetail
        from ..models.web_detail import WebDetail
        from ..models.whois import Whois

        d = dict(src_dict)
        ip = d.pop("ip")

        is_bogon = d.pop("is_bogon")

        is_tor = d.pop("is_tor")

        is_relay = d.pop("is_relay")

        is_anycast = d.pop("is_anycast")

        is_carrier = d.pop("is_carrier")

        is_satellite = d.pop("is_satellite")

        is_ssh = d.pop("is_ssh")

        is_smtp = d.pop("is_smtp")

        is_web = d.pop("is_web")

        is_dns_resolver = d.pop("is_dns_resolver")

        is_bittorrent = d.pop("is_bittorrent")

        tor = ClassDetail.from_dict(d.pop("tor"))

        relay = ClassDetail.from_dict(d.pop("relay"))

        location = Location.from_dict(d.pop("location"))

        asn = Asn.from_dict(d.pop("asn"))

        company = Company.from_dict(d.pop("company"))

        hostname = d.pop("hostname")

        abuse = AbuseContact.from_dict(d.pop("abuse"))

        is_vpn = d.pop("is_vpn", UNSET)

        is_resproxy = d.pop("is_resproxy", UNSET)

        is_dcproxy = d.pop("is_dcproxy", UNSET)

        is_mobproxy = d.pop("is_mobproxy", UNSET)

        is_pubproxy = d.pop("is_pubproxy", UNSET)

        is_hosting = d.pop("is_hosting", UNSET)

        is_cdn = d.pop("is_cdn", UNSET)

        _vpn = d.pop("vpn", UNSET)
        vpn: ClassDetail | Unset
        if isinstance(_vpn, Unset):
            vpn = UNSET
        else:
            vpn = ClassDetail.from_dict(_vpn)

        _resproxy = d.pop("resproxy", UNSET)
        resproxy: ProxyDetail | Unset
        if isinstance(_resproxy, Unset):
            resproxy = UNSET
        else:
            resproxy = ProxyDetail.from_dict(_resproxy)

        _dcproxy = d.pop("dcproxy", UNSET)
        dcproxy: ProxyDetail | Unset
        if isinstance(_dcproxy, Unset):
            dcproxy = UNSET
        else:
            dcproxy = ProxyDetail.from_dict(_dcproxy)

        _mobproxy = d.pop("mobproxy", UNSET)
        mobproxy: ProxyDetail | Unset
        if isinstance(_mobproxy, Unset):
            mobproxy = UNSET
        else:
            mobproxy = ProxyDetail.from_dict(_mobproxy)

        _pubproxy = d.pop("pubproxy", UNSET)
        pubproxy: PubproxyDetail | Unset
        if isinstance(_pubproxy, Unset):
            pubproxy = UNSET
        else:
            pubproxy = PubproxyDetail.from_dict(_pubproxy)

        _hosting = d.pop("hosting", UNSET)
        hosting: ClassDetail | Unset
        if isinstance(_hosting, Unset):
            hosting = UNSET
        else:
            hosting = ClassDetail.from_dict(_hosting)

        _cdn = d.pop("cdn", UNSET)
        cdn: ClassDetail | Unset
        if isinstance(_cdn, Unset):
            cdn = UNSET
        else:
            cdn = ClassDetail.from_dict(_cdn)

        _carrier = d.pop("carrier", UNSET)
        carrier: CarrierDetail | Unset
        if isinstance(_carrier, Unset):
            carrier = UNSET
        else:
            carrier = CarrierDetail.from_dict(_carrier)

        _satellite = d.pop("satellite", UNSET)
        satellite: SatelliteDetail | Unset
        if isinstance(_satellite, Unset):
            satellite = UNSET
        else:
            satellite = SatelliteDetail.from_dict(_satellite)

        _ssh = d.pop("ssh", UNSET)
        ssh: SshDetail | Unset
        if isinstance(_ssh, Unset):
            ssh = UNSET
        else:
            ssh = SshDetail.from_dict(_ssh)

        _smtp = d.pop("smtp", UNSET)
        smtp: SmtpDetail | Unset
        if isinstance(_smtp, Unset):
            smtp = UNSET
        else:
            smtp = SmtpDetail.from_dict(_smtp)

        _web = d.pop("web", UNSET)
        web: list[WebDetail] | Unset = UNSET
        if _web is not UNSET:
            web = []
            for web_item_data in _web:
                web_item = WebDetail.from_dict(web_item_data)

                web.append(web_item)

        _dns_resolver = d.pop("dns_resolver", UNSET)
        dns_resolver: DnsResolverDetail | Unset
        if isinstance(_dns_resolver, Unset):
            dns_resolver = UNSET
        else:
            dns_resolver = DnsResolverDetail.from_dict(_dns_resolver)

        _bittorrent = d.pop("bittorrent", UNSET)
        bittorrent: BitTorrentDetail | Unset
        if isinstance(_bittorrent, Unset):
            bittorrent = UNSET
        else:
            bittorrent = BitTorrentDetail.from_dict(_bittorrent)

        _whois = d.pop("whois", UNSET)
        whois: Whois | Unset
        if isinstance(_whois, Unset):
            whois = UNSET
        else:
            whois = Whois.from_dict(_whois)

        _rwhois = d.pop("rwhois", UNSET)
        rwhois: Rwhois | Unset
        if isinstance(_rwhois, Unset):
            rwhois = UNSET
        else:
            rwhois = Rwhois.from_dict(_rwhois)

        _hosted_domains = d.pop("hosted_domains", UNSET)
        hosted_domains: HostedDomains | Unset
        if isinstance(_hosted_domains, Unset):
            hosted_domains = UNSET
        else:
            hosted_domains = HostedDomains.from_dict(_hosted_domains)

        trial_expired = d.pop("trial_expired", UNSET)

        lookup_response = cls(
            ip=ip,
            is_bogon=is_bogon,
            is_tor=is_tor,
            is_relay=is_relay,
            is_anycast=is_anycast,
            is_carrier=is_carrier,
            is_satellite=is_satellite,
            is_ssh=is_ssh,
            is_smtp=is_smtp,
            is_web=is_web,
            is_dns_resolver=is_dns_resolver,
            is_bittorrent=is_bittorrent,
            tor=tor,
            relay=relay,
            location=location,
            asn=asn,
            company=company,
            hostname=hostname,
            abuse=abuse,
            is_vpn=is_vpn,
            is_resproxy=is_resproxy,
            is_dcproxy=is_dcproxy,
            is_mobproxy=is_mobproxy,
            is_pubproxy=is_pubproxy,
            is_hosting=is_hosting,
            is_cdn=is_cdn,
            vpn=vpn,
            resproxy=resproxy,
            dcproxy=dcproxy,
            mobproxy=mobproxy,
            pubproxy=pubproxy,
            hosting=hosting,
            cdn=cdn,
            carrier=carrier,
            satellite=satellite,
            ssh=ssh,
            smtp=smtp,
            web=web,
            dns_resolver=dns_resolver,
            bittorrent=bittorrent,
            whois=whois,
            rwhois=rwhois,
            hosted_domains=hosted_domains,
            trial_expired=trial_expired,
        )

        lookup_response.additional_properties = d
        return lookup_response

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
