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
from typing import Any, Literal

__all__ = [
    "Database",
    "DatabaseMetadata",
    "DatabaseVersion",
    "Download",
    "Format",
    "MetadataColumn",
    "Outcome",
    "LicenseType",
    "Standing",
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
"""What a licence permits you to do with the data. `None` when there is no licence."""

Outcome = Literal["ok", "unauthorized", "denied", "expired", "unknown", "unavailable"]
"""How one download attempt ended, refusals included."""


@dataclass(frozen=True, slots=True)
class DatabaseVersion:
    """One published version of a family.

    Old versions are frozen rather than migrated, so several stay downloadable at once.
    `id` is what `download`, `checksums` and `metadata` take; the family `base` is what a
    licence is held against.
    """

    id: str
    version: int
    summary: str
    formats: tuple[Format, ...]


@dataclass(frozen=True, slots=True)
class Database:
    """One database FAMILY, with your organization's licence beside it.

    A family your organization has never licensed is still listed, with `standing` set to
    `unlicensed`, so you can see what else exists. A family commissioned for a single
    customer is a different matter: it is absent from this listing entirely for everyone
    who does not license it. Absence here means "not yours to see", never "does not
    exist", so the catalog is not the same document for every key.
    """

    base: str
    name: str
    summary: str
    standing: Standing
    license_type: LicenseType | None
    starts: datetime.datetime | None
    expires: datetime.datetime | None
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


def to_database(body: dict[str, Any]) -> Database:
    return Database(
        base=body["base"],
        name=body["name"],
        summary=body["summary"],
        standing=body["standing"],
        license_type=body["license_type"],
        starts=_datetime(body["starts"]),
        expires=_datetime(body["expires"]),
        versions=tuple(to_version(v) for v in body["versions"]),
        raw=body,
    )


def to_version(body: dict[str, Any]) -> DatabaseVersion:
    return DatabaseVersion(
        id=body["id"],
        version=body["version"],
        summary=body["summary"],
        formats=tuple(body["formats"]),
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
    )


def _datetime(value: Any) -> datetime.datetime | None:
    """A NULLABLE wire timestamp. A licence with no end date carries `expires: null`.

    `fromisoformat` only learned to read a trailing `Z` in 3.11, which is one of the
    three reasons this package floors there. A value that is neither null nor readable
    raises, and the caller reports it as the server's failure rather than as None, which
    would quietly read as "no end date".
    """
    if value is None:
        return None
    return datetime.datetime.fromisoformat(value)
