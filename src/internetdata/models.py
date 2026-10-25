"""What the API answers, and the one place the wire shape becomes an idiomatic one.

The generated models are a wire contract rather than an API: the spec spells
`license_type` as a nullable enum, which the generator renders as a union of three
single-member enum classes, and nobody should have to read that. These are frozen
dataclasses of plain values, built straight from the served JSON, with `raw` kept beside
them so a field this pinned spec predates is still reachable.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

from .errors import InternetDataError

__all__ = [
    "DATABASE_FORMATS",
    "LICENSE_TYPES",
    "STANDINGS",
    "Database",
    "DatabaseMetadata",
    "DatabaseVersion",
    "DeviceAuthorization",
    "Download",
    "Format",
    "LicenseType",
    "MetadataColumn",
    "OauthMetadata",
    "Outcome",
    "Standing",
    "TokenResponse",
]

Format = Literal["csvgz", "mmdb"]
"""The file formats a database version can be built in.

Which of them a given version HAS is `DatabaseVersion.formats`; asking for another is a
`bad_request` rather than a gap, because the `_provider` catalogs are keyed by provider
id and no MMDB exists for them.
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
