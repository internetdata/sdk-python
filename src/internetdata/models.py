"""What the API answers, and the one place the wire shape becomes an idiomatic one.

The generated models are a wire contract rather than an API: the spec spells
`license_type` as a nullable enum, which the generator renders as a union of three
single-member enum classes, and nobody should have to read that. These are frozen
dataclasses of plain values, built straight from the served JSON, with `raw` kept beside
them so a field this pinned spec predates is still reachable.
"""

from __future__ import annotations

import dataclasses
import datetime
import re
import types
import typing
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar, get_args

from .errors import InternetDataError

__all__ = [
    "DATABASE_FORMATS",
    "LICENSE_TYPES",
    "STANDINGS",
    "AbuseContact",
    "Asn",
    "AsnPrefix",
    "AsnResult",
    "BitTorrentDetail",
    "CarrierDetail",
    "ClassDetail",
    "Company",
    "Database",
    "DatabaseMetadata",
    "DatabaseVersion",
    "DeviceAuthorization",
    "DisposableDetail",
    "DnsAddressRecord",
    "DnsCnameRecord",
    "DnsMxRecord",
    "DnsNsRecord",
    "DnsResolverDetail",
    "DomainDns",
    "DomainIpRange",
    "DomainIpRanges",
    "DomainResult",
    "Download",
    "Entitlement",
    "EntitlementApikey",
    "EntitlementPlan",
    "EntitlementPlanTier",
    "EntitlementUsage",
    "Flag",
    "Format",
    "HostedDomains",
    "LicenseType",
    "Location",
    "MetadataColumn",
    "OauthMetadata",
    "Outcome",
    "ProxyDetail",
    "PubproxyDetail",
    "Result",
    "Rwhois",
    "SatelliteDetail",
    "SmtpDetail",
    "SshDetail",
    "Standing",
    "TokenResponse",
    "WebDetail",
    "Whois",
]

Format = Literal["csvgz", "mmdb"]
"""The file formats a database version can be built in.

Which of them a given version HAS is `DatabaseVersion.formats`; asking for another is a
`bad_request` rather than a gap, because the `_provider` catalogs are keyed by provider
ID and no MMDB exists for them.
"""

Standing = Literal["licensed", "expired", "unlicensed"]
"""Where your organization stands with one database family."""

LicenseType = Literal["evaluation", "standard", "redistribute"]
"""What a license permits you to do with the data. `None` when there is no license."""

DATABASE_FORMATS: tuple[Format, ...] = get_args(Format)
"""Every `Format`, at runtime.

A `Literal` is erased to nothing a program can check against, so a format read from a
flag, a form or a config file has these to be tested against before a call.
"""

STANDINGS: tuple[Standing, ...] = get_args(Standing)
"""Every `Standing`, at runtime."""

LICENSE_TYPES: tuple[LicenseType, ...] = get_args(LicenseType)
"""Every `LicenseType`, at runtime. `None`, for no license, is not one of them."""

Outcome = Literal["ok", "unauthorized", "denied", "expired", "unknown", "unavailable"]
"""How one download attempt ended, refusals included."""


@dataclass(frozen=True, slots=True)
class DatabaseVersion:
    """One published version of a family.

    Old versions are frozen rather than migrated, so several stay downloadable at once.
    `id` is what `download`, `checksums` and `metadata` take; the family `base` is what a
    license is held against.
    """

    id: str
    version: int
    summary: str
    formats: tuple[Format, ...]
    # The formats an evaluation sample is published in, None when there is none.
    sample_formats: tuple[Format, ...] | None = None


@dataclass(frozen=True, slots=True)
class Database:
    """One database FAMILY, with your organization's license beside it.

    A family your organization has never licensed is still listed, with `standing` set to
    `unlicensed`, so you can see what else exists. One that is `open` is free under
    CC BY-SA 4.0, and every organization holds a `standard` license to it from the start,
    which `standing` and `license_type` report like any other.

    A rolling license carries `renews_at`, when it next renews, and `notice_due_at`, the
    last day notice of non-renewal can be given for the term ending then. Both are None
    when there is no license, when it has no defined term, or when `expires` sets a hard
    stop instead; `notice_due_at` is None too when the agreement records no notice period.
    """

    base: str
    name: str
    summary: str
    standing: Standing
    license_type: LicenseType | None
    starts: datetime.datetime | None
    expires: datetime.datetime | None
    # Keyword-only with a default, so a Database built by hand before 2.2.0 still builds;
    # the parser always sets both.
    renews_at: datetime.datetime | None = field(default=None, kw_only=True)
    notice_due_at: datetime.datetime | None = field(default=None, kw_only=True)
    versions: tuple[DatabaseVersion, ...]
    raw: dict[str, Any] = field(default_factory=dict)
    # Keyword-only with a default, so a Database built by hand before 2.7.0 still builds;
    # the parser always sets it.
    open: bool = field(default=False, kw_only=True)


@dataclass(frozen=True, slots=True)
class MetadataColumn:
    """One column of a published file. `description` is absent on older builds."""

    name: str
    type: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class DatabaseMetadata:
    """What is inside one database: freshness, row count, columns, samples and sizes.

    Poll this to decide whether today's build is worth fetching. `size` is keyed by
    format and is in bytes, which is what a caller should budget a transfer against
    before starting one.
    """

    id: str
    updated: datetime.date
    entries: int
    schema: dict[str, tuple[MetadataColumn, ...]]
    size: dict[str, int]
    update_freq: str | None = None
    sample: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    # Bytes per format and row count of the evaluation sample, where one is published.
    sample_size: dict[str, int] | None = None
    sample_entries: int | None = None


@dataclass(frozen=True, slots=True)
class Download:
    """One download ATTEMPT by your organization, refusals included.

    `bytes` is the object size when the link was minted rather than bytes delivered: the
    transfer is a presigned redirect straight to object storage, so the API never
    observes how much of it was taken.
    """

    dataset_id: str
    format: str
    outcome: Outcome
    created: datetime.datetime
    bytes: int | None = None
    http_status: int | None = None
    apikey_id: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    # Whether this was the evaluation sample rather than the database itself. Keyword-only
    # with a default, so a Download built by hand before 2.5.0 still builds; the parser
    # always sets it.
    sample: bool = field(default=False, kw_only=True)
    # A download of an Open database. Keyword-only with a default, so a Download built
    # by hand before 2.7.0 still builds.
    open: bool = field(default=False, kw_only=True)


def to_database(body: dict[str, Any]) -> Database:
    return Database(
        base=_present(body, "base", str),
        name=_present(body, "name", str),
        summary=_present(body, "summary", str),
        standing=_one_of(_present(body, "standing", str), STANDINGS, "standing"),
        license_type=_one_of(_nullable(body, "license_type", str), LICENSE_TYPES, "license_type"),
        starts=_datetime(body["starts"], "starts"),
        expires=_datetime(body["expires"], "expires"),
        renews_at=_datetime(body["renews_at"], "renews_at"),
        notice_due_at=_datetime(body["notice_due_at"], "notice_due_at"),
        versions=tuple(to_version(v) for v in _present(body, "versions", list)),
        raw=body,
        open=_present(body, "open", bool),
    )


def to_version(body: dict[str, Any]) -> DatabaseVersion:
    sample_formats = _nullable(body, "sample_formats", list, absent=True)
    return DatabaseVersion(
        id=_present(body, "id", str),
        version=_present(body, "version", int),
        summary=_present(body, "summary", str),
        formats=_strings(_present(body, "formats", list), "formats"),
        sample_formats=None
        if sample_formats is None
        else _strings(sample_formats, "sample_formats"),
    )


def to_metadata(body: dict[str, Any]) -> DatabaseMetadata:
    schema = _present(body, "schema", dict)
    sample = _of_type(body.get("sample", {}), "sample", dict)
    return DatabaseMetadata(
        id=_present(body, "id", str),
        updated=_date(_present(body, "updated", str), "updated"),
        entries=_present(body, "entries", int),
        schema={
            fmt: tuple(
                to_column(_of_type(c, "schema", dict)) for c in _of_type(cols, "schema", list)
            )
            for fmt, cols in schema.items()
        },
        size=_sizes(_present(body, "size", dict), "size"),
        update_freq=_nullable(body, "update_freq", str, absent=True),
        sample={
            fmt: tuple(_of_type(row, "sample", dict) for row in _of_type(rows, "sample", list))
            for fmt, rows in sample.items()
        },
        raw=body,
        sample_size=_sizes(body["sample_size"], "sample_size")
        if body.get("sample_size") is not None
        else None,
        sample_entries=_nullable(body, "sample_entries", int, absent=True),
    )


def to_column(body: dict[str, Any]) -> MetadataColumn:
    return MetadataColumn(
        name=_present(body, "name", str),
        type=_present(body, "type", str),
        description=_nullable(body, "description", str, absent=True),
    )


def to_download(body: dict[str, Any]) -> Download:
    return Download(
        dataset_id=_present(body, "dataset_id", str),
        format=_present(body, "format", str),
        outcome=_one_of(_present(body, "outcome", str), get_args(Outcome), "outcome"),
        created=_date_time(_present(body, "created", str), "created"),
        bytes=_nullable(body, "bytes", int),
        http_status=_nullable(body, "http_status", int),
        apikey_id=_nullable(body, "apikey_id", str),
        client_ip=_nullable(body, "client_ip", str),
        user_agent=_nullable(body, "user_agent", str),
        sample=_present(body, "sample", bool),
        open=_present(body, "open", bool),
    )


def _present(body: dict[str, Any], name: str, kind: type) -> Any:
    """A member the spec requires and never sends as null, of the type it gives.

    A null one is the server's failure, raised for the caller to report as one, rather
    than handed back in the answer: 2.7.1 listed a family whose `base` was null as a
    family with no base (measured 2026-10-12). So is one of another type: 2.7.4 handed
    back a version served as `"3"` as that string (measured 2026-10-16).
    """
    value = body[name]
    if value is None:
        raise ValueError(f"{name} is null")
    return _of_type(value, name, kind)


def _nullable(body: dict[str, Any], name: str, kind: type, absent: bool = False) -> Any:
    """A member that may be null, or with `absent` left out, and is otherwise of `kind`."""
    value = body.get(name) if absent else body[name]
    return None if value is None else _of_type(value, name, kind)


def _of_type(value: Any, name: str, kind: type) -> Any:
    # A bool is an int to isinstance, and neither may stand for the other.
    if isinstance(value, bool) != (kind is bool) or not isinstance(value, kind):
        raise ValueError(f"{name} is not a {kind.__name__}: {value!r}")
    return value


def _strings(values: list[Any], name: str) -> tuple[Any, ...]:
    return tuple(_of_type(v, name, str) for v in values)


def _one_of(value: Any, allowed: tuple[str, ...], name: str) -> Any:
    """`value`, a member of `allowed`, or None. One outside it is a value this client was not
    built for: `license_type` came back as served while its type promised one of three, and
    `standing` beside it was refused (2.9.2, measured 2026-10-25)."""
    if value is not None and value not in allowed:
        raise ValueError(f"{name} is not one of {', '.join(allowed)}: {value!r}")
    return value


def _sizes(sizes: Any, name: str) -> dict[str, int]:
    return {fmt: _of_type(n, name, int) for fmt, n in _of_type(sizes, name, dict).items()}


def _datetime(value: Any, name: str) -> datetime.datetime | None:
    """A NULLABLE wire timestamp. A license with no end date carries `expires: null`.

    A value that is neither null nor readable raises, and the caller reports it as the
    server's failure rather than as None, which would quietly read as "no end date".
    """
    return None if value is None else _date_time(value, name)


# The spec's `date-time` and `date` are RFC 3339's, and only those are read: `fromisoformat`
# took a date-time with no offset as a naive datetime, which no aware one can be compared
# with, a date alone as midnight, `+0500`, `+05`, `+05:00:30`, `+05:60` as an hour more,
# a space for the `T`, no seconds, a comma for the point, week dates and `20261005`
# (2.9.2, measured 2026-10-25). RFC 3339 allows a lowercase `t` and `z`, which it refused.
_DIGITS2 = "([0-9]{2})"
_FULL_DATE = re.compile(rf"([0-9]{{4}})-{_DIGITS2}-{_DIGITS2}")
_DATE_TIME = re.compile(
    rf"([0-9]{{4}})-{_DIGITS2}-{_DIGITS2}[Tt]{_DIGITS2}:{_DIGITS2}:{_DIGITS2}(?:\.([0-9]+))?"
    rf"(?:[Zz]|([+-]){_DIGITS2}:{_DIGITS2})"
)


def _date(value: str, name: str) -> datetime.date:
    match = _FULL_DATE.fullmatch(value)
    if match is None:
        raise ValueError(f"{name} is not an RFC 3339 date: {value!r}")
    # A day its month lacks, 30 February, raises here.
    return datetime.date(*(int(part) for part in match.groups()))


def _date_time(value: Any, name: str) -> datetime.datetime:
    match = _DATE_TIME.fullmatch(_of_type(value, name, str))
    if match is None:
        raise ValueError(f"{name} is not an RFC 3339 date-time: {value!r}")
    year, month, day, hour, minute, second, fraction, sign, offset_hour, offset_minute = (
        match.groups()
    )
    zone = datetime.UTC
    if sign is not None:
        if int(offset_hour) > 23 or int(offset_minute) > 59:
            raise ValueError(f"{name} has no such offset: {value!r}")
        offset = datetime.timedelta(hours=int(offset_hour), minutes=int(offset_minute))
        zone = datetime.timezone(-offset if sign == "-" else offset)
    # A day its month lacks, an hour of 24 and a leap second's 60 raise here; past six
    # digits a fraction is cut, as `fromisoformat` cuts it.
    return datetime.datetime(
        int(year),
        int(month),
        int(day),
        int(hour),
        int(minute),
        int(second),
        int((fraction or "")[:6].ljust(6, "0")),
        tzinfo=zone,
    )


# The lookups. A member the spec does not require is one your plan does not include, and
# reads as None, never False, 0 or "": `None` is "not in your plan", `False` is "checked,
# and no". Each type is frozen, because a cached answer is handed to every later caller of
# the same address. Read by `_record`, member by member, from the type each field names.

Flag = Literal[
    "is_vpn",
    "is_tor",
    "is_relay",
    "is_resproxy",
    "is_dcproxy",
    "is_mobproxy",
    "is_pubproxy",
    "is_hosting",
    "is_cdn",
    "is_anycast",
    "is_carrier",
    "is_satellite",
    "is_ssh",
    "is_smtp",
    "is_web",
    "is_dns_resolver",
    "is_bittorrent",
]

EntitlementPlanTier = Literal["free", "starter", "scale", "max"]
"""The pricing tier a plan grants."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ClassDetail:
    """A row of VPN IP, Tor IP, Relay IP, Hosting IP or CDN IP. Present and empty (every
    field None) when the flag above it is false; a populated one carries every field.
    `provider` is empty for an unattributed range, and on Tor."""

    provider: str | None = None
    provider_name: str | None = None
    confidence: str | None = None
    last_seen: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ProxyDetail:
    """A row of Residential, Datacenter or Mobile Proxy IP, over a rolling 90-day window.
    Empty when the flag above it is false."""

    provider: str | None = None
    provider_name: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    hits: int | None = None
    hits_days_pct: int | None = None
    providers_num: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PubproxyDetail:
    """A row of Public Proxy IP: a public proxy listens here (`entry`), or its traffic
    leaves from here (`exit`). Empty when `is_pubproxy` is false."""

    entry: bool | None = None
    exit: bool | None = None
    protocols: tuple[str, ...] | None = None
    num_ports: int | None = None
    num_proxies: int | None = None
    last_seen: str | None = None
    last_usable: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CarrierDetail:
    """The mobile carrier, from Carrier IP. Empty when `is_carrier` is false."""

    name: str | None = None
    mcc: str | None = None
    mnc: str | None = None
    country: str | None = None
    confidence: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SatelliteDetail:
    """The satellite operator, from Satellite IP. Empty when `is_satellite` is false."""

    provider: str | None = None
    provider_name: str | None = None
    orbit: str | None = None
    segment: str | None = None
    country: str | None = None
    asn: int | None = None
    confidence: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SshDetail:
    """The SSH server answering here. Empty when `is_ssh` is false."""

    port: int | None = None
    banner: str | None = None
    host_key_fp: str | None = None
    session_ok: bool | None = None
    first_seen: str | None = None
    last_seen: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SmtpDetail:
    """The SMTP server answering here. Empty when `is_smtp` is false."""

    port: int | None = None
    banner: str | None = None
    session_ok: bool | None = None
    first_seen: str | None = None
    last_seen: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class WebDetail:
    """One port of Web IP that answered."""

    port: int
    tls_ok: bool
    session_ok: bool
    status_code: int
    server: str
    location: str
    title: str
    cert_subject_cn: str
    cert_subject_o: str
    cert_issuer_dn: str
    cert_browser_trusted: bool
    tls_version: str
    first_seen: str
    last_seen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DnsResolverDetail:
    """The open DNS resolver answering here. Empty when `is_dns_resolver` is false."""

    port: int | None = None
    recursion_available: bool | None = None
    rcode: int | None = None
    answer_correct: bool | None = None
    first_seen: str | None = None
    last_seen: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class BitTorrentDetail:
    """BitTorrent clients seen here. Empty when `is_bittorrent` is false."""

    verified: bool | None = None
    id_matches_ip: bool | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    last_reachable: str | None = None
    days_seen: int | None = None
    num_ports: int | None = None
    peak_num_ports: int | None = None
    indexer: bool | None = None
    clients: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Location:
    """Where the address is, on every answer. A field is the empty string where it is not
    known, and None where your plan does not include it."""

    continent: str
    continent_name: str
    country: str
    country_name: str
    timezone: str
    currency_code: str
    currency_name: str
    currency_symbol: str
    flag_emoji: str
    flag_unicode: str
    region: str | None = None
    region_code: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    accuracy_radius: int | None = None
    geoname_id: str | None = None
    dma_code: str | None = None
    last_changed: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Asn:
    """The network announcing the address, from IP ASN, on every answer: `asn` is 0 where
    none does."""

    asn: int
    name: str
    domain: str
    type: str
    prefix: str
    country: str | None = None
    rpki_status: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Company:
    """Who uses the address, from IP Company, on every answer."""

    name: str
    domain: str
    type: str | None = None
    country: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AbuseContact:
    """Where to report abuse from the address, from IP Abuse Contact, on every answer."""

    email: str
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    country: str | None = None
    network: str | None = None
    validated: bool | None = None
    unvalidated_since: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Whois:
    """IP Whois's most specific record covering the address."""

    id: str
    name: str
    org: str
    country: str
    status: str
    source: str
    domain: str
    abuse_email: str
    asn: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Rwhois:
    """IP RWHOIS's most specific network covering the address."""

    id: str
    name: str
    country: str
    source: str
    domain: str
    abuse_email: str


@dataclass(frozen=True, slots=True, kw_only=True)
class HostedDomains:
    """From IP Hosted Domains: how many registered domains resolve to the address."""

    total: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Result:
    """What a lookup answers.

    An **optional** member is one your plan does not include. It never means "we could
    not check", so `None` and `False` are genuinely different answers: `None` is "not in
    your plan", `False` is "checked, and no". Use `flagged()` when you only care whether
    the address is flagged. That holds inside a shared object too: `location.city` is
    None on a plan without it.

    A detail object that is present but empty (every field `None`, Web IP's an empty
    tuple) means the flag above it is false. A populated one always carries every one of
    its keys.

    Frozen, because a cached answer is handed to every later caller of the same address.
    """

    ip: str
    is_bogon: bool
    is_vpn: bool | None = None
    is_tor: bool
    is_relay: bool
    is_resproxy: bool | None = None
    is_dcproxy: bool | None = None
    is_mobproxy: bool | None = None
    is_pubproxy: bool | None = None
    is_hosting: bool | None = None
    is_cdn: bool | None = None
    is_anycast: bool
    is_carrier: bool
    is_satellite: bool
    is_ssh: bool
    is_smtp: bool
    is_web: bool
    is_dns_resolver: bool
    is_bittorrent: bool

    vpn: ClassDetail | None = None
    tor: ClassDetail
    relay: ClassDetail
    resproxy: ProxyDetail | None = None
    dcproxy: ProxyDetail | None = None
    mobproxy: ProxyDetail | None = None
    pubproxy: PubproxyDetail | None = None
    hosting: ClassDetail | None = None
    cdn: ClassDetail | None = None
    carrier: CarrierDetail | None = None
    satellite: SatelliteDetail | None = None
    ssh: SshDetail | None = None
    smtp: SmtpDetail | None = None
    web: tuple[WebDetail, ...] | None = None
    dns_resolver: DnsResolverDetail | None = None
    bittorrent: BitTorrentDetail | None = None

    location: Location
    asn: Asn
    company: Company
    hostname: str
    abuse: AbuseContact
    whois: Whois | None = None
    rwhois: Rwhois | None = None
    hosted_domains: HostedDomains | None = None

    #: On answers to a key on the free plan only: False while its organization's daily trial
    #: lasts (every field for the first 100 lookups each UTC day), True once the answer has
    #: Unlimited's.
    trial_expired: bool | None = None

    raw: dict[str, Any] = field(default_factory=dict)

    def flagged(self, flag: Flag) -> bool:
        """Whether a flag is present AND true, with anything your plan does not include
        reading as false.

        Python has no `??`, and `result.is_hosting` is three-valued, so every caller who
        only wants a yes-or-no would otherwise write the same coalesce by hand.
        """
        return getattr(self, flag) is True


@dataclass(frozen=True, slots=True, kw_only=True)
class AsnPrefix:
    """One prefix an AS announces, from BGP Route."""

    prefix: str
    peer_count: int
    rpki_status: str
    first_seen: str
    country: str
    size: int
    other_origins: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class AsnResult:
    """What an AS lookup answers: its registration on every plan, and on a paid one its
    ASN Whois record, its counts and every prefix it announces. None is "not in your plan",
    as on `Result`. An AS no database knows answers its number with empty values."""

    asn: int
    name: str
    country: str
    registry: str
    allocated: str
    domain: str
    type: str | None = None
    num_ips: int | None = None
    num_prefixes4: int | None = None
    num_prefixes6: int | None = None
    rpki_valid: int | None = None
    rpki_invalid: int | None = None
    rpki_not_found: int | None = None
    whois: dict[str, str] | None = None
    prefixes: tuple[AsnPrefix, ...] | None = None
    trial_expired: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class DnsAddressRecord:
    """An A or AAAA record."""

    ip: str
    last_seen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DnsMxRecord:
    """An MX record."""

    priority: int
    host: str
    last_seen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DnsNsRecord:
    """An NS record."""

    host: str
    last_seen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DnsCnameRecord:
    """A CNAME record."""

    target: str
    last_seen: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainDns:
    """A domain's records in Domain DNS, up to 100 a type."""

    a: tuple[DnsAddressRecord, ...]
    aaaa: tuple[DnsAddressRecord, ...]
    mx: tuple[DnsMxRecord, ...]
    ns: tuple[DnsNsRecord, ...]
    cname: tuple[DnsCnameRecord, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainIpRange:
    """One range an organization holds."""

    range: str
    name: str
    country: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainIpRanges:
    """The organization's IP ranges, from Domain IP Ranges."""

    domain: str
    redirects_to: str
    total: int
    ipv4: int
    ranges: tuple[DomainIpRange, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class DisposableDetail:
    """A row of Disposable Domain. Empty when `is_disposable` is false."""

    confidence: str | None = None
    providers: tuple[str, ...] | None = None
    first_seen: str | None = None
    last_seen: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainResult:
    """What a domain lookup answers: on every plan whether it is registered and which DNS
    record types it has; on a paid one the records, the organization's IP ranges and
    whether it is a disposable email domain. None is "not in your plan", as on `Result`."""

    domain: str
    is_registered: bool
    is_disposable: bool | None = None
    has_a: bool
    has_aaaa: bool
    has_mx: bool
    has_ns: bool
    has_cname: bool
    dns: DomainDns | None = None
    ip_ranges: DomainIpRanges | None = None
    disposable: DisposableDetail | None = None
    trial_expired: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitlementApikey:
    """The key the call was made with: `expires` is None for a key that does not expire,
    and `allowed_cidrs` empty for one usable from anywhere."""

    id: uuid.UUID
    expires: datetime.datetime | None
    allowed_cidrs: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitlementPlan:
    """The plan the key's organization is on."""

    key: str
    tier: EntitlementPlanTier


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitlementUsage:
    """What the allowance window has spent: `hard_limit` is None where no cap stops the
    lookups past `quota`."""

    requests: int
    quota: int
    hard_limit: int | None
    window_start: datetime.datetime
    window_end: datetime.datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class Entitlement:
    """What a key may spend, and what it has."""

    org_id: uuid.UUID
    apikey: EntitlementApikey
    plan: EntitlementPlan
    usage: EntitlementUsage


def to_result(body: dict[str, Any]) -> Result:
    """One served answer as a `Result`, every member read on PRESENCE rather than
    truthiness, or a plan that includes a field and answers `false` would lose it.

    A member of another type than the spec gives it, or a required one absent or null, is
    the server's failure, raised for the caller to report as one, from a lookup and a batch
    entry alike.
    """
    result = _record(Result, body, "answer")
    if result.ip == "":
        raise ValueError("the answer's ip is not an address: ''")
    return result


def to_asn_result(body: dict[str, Any]) -> AsnResult:
    return _record(AsnResult, body, "answer")


def to_domain_result(body: dict[str, Any]) -> DomainResult:
    return _record(DomainResult, body, "answer")


def to_entitlement(body: dict[str, Any]) -> Entitlement:
    return _record(Entitlement, body, "answer")


# The lookups' detail objects: `{}` under a false flag, and otherwise every member the spec
# requires, which for each of these is every member.
_DETAILS = (
    ClassDetail,
    ProxyDetail,
    PubproxyDetail,
    CarrierDetail,
    SatelliteDetail,
    SshDetail,
    SmtpDetail,
    DnsResolverDetail,
    BitTorrentDetail,
    DisposableDetail,
)

R = TypeVar("R")


def _record(cls: type[R], body: Any, name: str) -> R:
    """`body` as `cls`, each member read by the type its field names: one with no default
    must be present and is null only where that type allows None, and one defaulting to
    None reads as None when absent or null. A detail object is `{}` or carries every member.
    `raw` is the body itself."""
    body = _of_type(body, name, dict)
    whole = cls in _DETAILS
    if whole and not body:
        return cls()
    hints = _hints(cls)
    values: dict[str, Any] = {}
    for member in dataclasses.fields(cls):  # type: ignore[arg-type]
        if member.name == "raw":
            values["raw"] = body
            continue
        wire = f"{name}.{member.name}"
        required = whole or member.default is dataclasses.MISSING
        if member.name not in body:
            if required:
                raise KeyError(wire)
            continue
        value = body[member.name]
        arms = _arms(hints[member.name])
        if value is None:
            if whole or type(None) not in arms:
                raise ValueError(f"{wire} is null")
            values[member.name] = None
            continue
        (kind,) = (arm for arm in arms if arm is not type(None))
        values[member.name] = _value(value, kind, wire)
    return cls(**values)


def _value(value: Any, kind: Any, name: str) -> Any:
    origin = typing.get_origin(kind)
    if origin is tuple:
        return tuple(_value(item, get_args(kind)[0], name) for item in _of_type(value, name, list))
    if origin is dict:
        return {
            key: _value(item, get_args(kind)[1], name)
            for key, item in _of_type(value, name, dict).items()
        }
    if origin is Literal:
        return _one_of(_of_type(value, name, str), get_args(kind), name)
    if isinstance(kind, type) and dataclasses.is_dataclass(kind):
        return _record(kind, value, name)
    if kind is float:
        # JSON does not tell 48 from 48.0, so an integer stands for a number; a bool never.
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{name} is not a number: {value!r}")
        return float(value)
    if kind is datetime.datetime:
        return _date_time(value, name)
    if kind is uuid.UUID:
        return uuid.UUID(_of_type(value, name, str))
    return _of_type(value, name, kind)


def _arms(hint: Any) -> tuple[Any, ...]:
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        return get_args(hint)
    return (hint,)


_HINTS: dict[type, dict[str, Any]] = {}


def _hints(cls: type) -> dict[str, Any]:
    """A dataclass's field types, its string annotations resolved once."""
    hints = _HINTS.get(cls)
    if hints is None:
        hints = _HINTS[cls] = typing.get_type_hints(cls)
    return hints


@dataclass(frozen=True, slots=True)
class OauthMetadata:
    """The authorization server's discovery document (RFC 8414)."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    device_authorization_endpoint: str | None = None
    revocation_endpoint: str | None = None
    scopes_supported: tuple[str, ...] | None = None
    response_types_supported: tuple[str, ...] | None = None
    grant_types_supported: tuple[str, ...] | None = None
    code_challenge_methods_supported: tuple[str, ...] | None = None
    token_endpoint_auth_methods_supported: tuple[str, ...] | None = None
    authorization_response_iss_parameter_supported: bool | None = None
    service_documentation: str | None = None
    client_id_metadata_document_supported: bool | None = None
    registration_endpoint: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceAuthorization:
    """A started device sign-in. Show the person `verification_uri` and `user_code`, then
    pass this to `poll_device_token`. `expires_in` and `interval` are seconds.

    `device_code` is left out of the repr, because it is what redeems the sign-in.
    """

    device_code: str = field(repr=False)
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    verification_uri_complete: str | None = None


@dataclass(frozen=True, slots=True)
class Pkce:
    """One sign-in's PKCE pair: `challenge` goes in the authorization URL, `verifier` to the
    code exchange. The verifier is left out of the repr, so logging the pair does not leak it.
    """

    verifier: str = field(repr=False)
    challenge: str
    method: Literal["S256"] = "S256"


@dataclass(frozen=True, slots=True)
class TokenResponse:
    """What a token exchange answers.

    `apikey_id` names the API key the person picked, and `apikey` is its secret. Either can
    be None: no key was picked, or their role no longer reveals keys. `apikey` also stays
    None after a refresh, which never hands a secret over, and for a key created before
    secrets could be revealed. The secrets are left out of the repr, so logging one does
    not leak them.
    """

    access_token: str = field(repr=False)
    token_type: str
    expires_in: int
    refresh_token: str | None = field(default=None, repr=False)
    scope: str | None = None
    apikey_id: str | None = None
    apikey: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class ClientRegistration:
    """A registered client, public and with no secret: it proves each sign-in with PKCE.

    `client_id` goes to `authorization_url` and `exchange_authorization_code`.
    `client_id_issued_at` is Unix seconds, and `client_name` the name the person will see,
    a placeholder when none was given or none can be shown. `token_endpoint_auth_method` is
    always `none`, and `scope` the most this client may be granted.
    """

    client_id: str
    client_id_issued_at: int
    client_name: str
    redirect_uris: tuple[str, ...]
    token_endpoint_auth_method: str
    grant_types: tuple[str, ...] | None = None
    response_types: tuple[str, ...] | None = None
    scope: str | None = None


def to_oauth_metadata(body: Any, status: int) -> OauthMetadata:
    return OauthMetadata(**_members(body, _OAUTH_METADATA, status))


def to_device_authorization(body: Any, status: int) -> DeviceAuthorization:
    return DeviceAuthorization(**_members(body, _DEVICE_AUTHORIZATION, status))


def to_token_response(body: Any, status: int) -> TokenResponse:
    return TokenResponse(**_members(body, _TOKEN_RESPONSE, status))


def to_client_registration(body: Any, status: int) -> ClientRegistration:
    return ClientRegistration(**_members(body, _CLIENT_REGISTRATION, status))


# A member's type on the wire, and whether a 2xx without it is malformed.
_Member = tuple[Literal["str", "int", "bool", "strs"], bool]

_OAUTH_METADATA: dict[str, _Member] = {
    "issuer": ("str", True),
    "authorization_endpoint": ("str", True),
    "token_endpoint": ("str", True),
    "device_authorization_endpoint": ("str", False),
    "revocation_endpoint": ("str", False),
    "scopes_supported": ("strs", False),
    "response_types_supported": ("strs", False),
    "grant_types_supported": ("strs", False),
    "code_challenge_methods_supported": ("strs", False),
    "token_endpoint_auth_methods_supported": ("strs", False),
    "authorization_response_iss_parameter_supported": ("bool", False),
    "service_documentation": ("str", False),
    "client_id_metadata_document_supported": ("bool", False),
    "registration_endpoint": ("str", False),
}

_DEVICE_AUTHORIZATION: dict[str, _Member] = {
    "device_code": ("str", True),
    "user_code": ("str", True),
    "verification_uri": ("str", True),
    "verification_uri_complete": ("str", False),
    "expires_in": ("int", True),
    "interval": ("int", True),
}

_TOKEN_RESPONSE: dict[str, _Member] = {
    "access_token": ("str", True),
    "token_type": ("str", True),
    "expires_in": ("int", True),
    "refresh_token": ("str", False),
    "scope": ("str", False),
    "apikey_id": ("str", False),
    "apikey": ("str", False),
}

_CLIENT_REGISTRATION: dict[str, _Member] = {
    "client_id": ("str", True),
    "client_id_issued_at": ("int", True),
    "client_name": ("str", True),
    "redirect_uris": ("strs", True),
    "token_endpoint_auth_method": ("str", True),
    "grant_types": ("strs", False),
    "response_types": ("strs", False),
    "scope": ("str", False),
}

_WIRE_NAMES = {"apikey_id": "mslm:apikey_id", "apikey": "mslm:apikey"}


# Only the declared members are copied, on PRESENCE, so an absent one stays None and an
# empty `scope` stays "". A null reads as absent. Anything undeclared is dropped.
def _members(body: Any, members: dict[str, _Member], status: int) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise InternetDataError("server_error", "the answer was not a JSON object", status)
    out: dict[str, Any] = {}
    for name, (kind, required) in members.items():
        wire = _WIRE_NAMES.get(name, name)
        value = body.get(wire)
        if value is None:
            if required:
                raise InternetDataError("server_error", f"the answer carried no {wire}", status)
            continue
        out[name] = _typed(value, kind, wire, status)
    return out


def _typed(value: Any, kind: str, wire: str, status: int) -> Any:
    if kind == "strs" and isinstance(value, list) and all(isinstance(v, str) for v in value):
        return tuple(value)
    if kind == "str" and isinstance(value, str):
        return value
    if kind == "bool" and isinstance(value, bool):
        return value
    # bool is an int in Python, and never a count of seconds.
    if kind == "int" and isinstance(value, int) and not isinstance(value, bool):
        return value
    if kind == "int" and isinstance(value, float) and value.is_integer():
        return int(value)
    raise InternetDataError("server_error", f"the answer's {wire} is not a {kind}", status)
