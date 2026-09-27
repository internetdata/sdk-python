"""What the API answers, and the one place the wire shape becomes an idiomatic one.

The generated models are a wire contract rather than an API: the spec spells
`license_type` as a nullable enum, which the generator renders as a union of three
single-member enum classes, and nobody should have to read that. These are frozen
dataclasses of plain values, built straight from the served JSON, with `raw` kept beside
them so a field this pinned spec predates is still reachable.
"""

from __future__ import annotations

import datetime
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
    `unlicensed`, so you can see what else exists.

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


def to_database(body: dict[str, Any]) -> Database:
    return Database(
        base=body["base"],
        name=body["name"],
        summary=body["summary"],
        standing=body["standing"],
        license_type=body["license_type"],
        starts=_datetime(body["starts"]),
        expires=_datetime(body["expires"]),
        renews_at=_datetime(body["renews_at"]),
        notice_due_at=_datetime(body["notice_due_at"]),
        versions=tuple(to_version(v) for v in body["versions"]),
        raw=body,
    )


def to_version(body: dict[str, Any]) -> DatabaseVersion:
    return DatabaseVersion(
        id=body["id"],
        version=body["version"],
        summary=body["summary"],
        formats=tuple(body["formats"]),
        sample_formats=_optional_tuple(body.get("sample_formats")),
    )


def to_metadata(body: dict[str, Any]) -> DatabaseMetadata:
    return DatabaseMetadata(
        id=body["id"],
        updated=datetime.date.fromisoformat(body["updated"]),
        entries=body["entries"],
        schema={
            fmt: tuple(to_column(c) for c in columns) for fmt, columns in body["schema"].items()
        },
        size=dict(body["size"]),
        update_freq=body.get("update_freq"),
        sample={fmt: tuple(rows) for fmt, rows in body.get("sample", {}).items()},
        raw=body,
        sample_size=dict(body["sample_size"]) if body.get("sample_size") is not None else None,
        sample_entries=body.get("sample_entries"),
    )


def to_column(body: dict[str, Any]) -> MetadataColumn:
    return MetadataColumn(name=body["name"], type=body["type"], description=body.get("description"))


def to_download(body: dict[str, Any]) -> Download:
    return Download(
        dataset_id=body["dataset_id"],
        format=body["format"],
        outcome=body["outcome"],
        created=datetime.datetime.fromisoformat(body["created"]),
        bytes=body["bytes"],
        http_status=body["http_status"],
        apikey_id=body["apikey_id"],
        client_ip=body["client_ip"],
        user_agent=body["user_agent"],
        sample=body["sample"],
    )


def _optional_tuple(value: Any) -> tuple[Any, ...] | None:
    return tuple(value) if value is not None else None


def _datetime(value: Any) -> datetime.datetime | None:
    """A NULLABLE wire timestamp. A license with no end date carries `expires: null`.

    `fromisoformat` only learned to read a trailing `Z` in 3.11, which is one of the
    three reasons this package floors there. A value that is neither null nor readable
    raises, and the caller reports it as the server's failure rather than as None, which
    would quietly read as "no end date".
    """
    if value is None:
        return None
    return datetime.datetime.fromisoformat(value)


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


def to_oauth_metadata(body: Any, status: int) -> OauthMetadata:
    return OauthMetadata(**_members(body, _OAUTH_METADATA, status))


def to_device_authorization(body: Any, status: int) -> DeviceAuthorization:
    return DeviceAuthorization(**_members(body, _DEVICE_AUTHORIZATION, status))


def to_token_response(body: Any, status: int) -> TokenResponse:
    return TokenResponse(**_members(body, _TOKEN_RESPONSE, status))


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
