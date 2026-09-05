from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.database_license_type_type_1 import DatabaseLicenseTypeType1
from ..models.database_license_type_type_2_type_1 import DatabaseLicenseTypeType2Type1
from ..models.database_license_type_type_3_type_1 import DatabaseLicenseTypeType3Type1
from ..models.database_standing import DatabaseStanding

if TYPE_CHECKING:
    from ..models.database_version import DatabaseVersion


T = TypeVar("T", bound="Database")


@_attrs_define
class Database:
    """One database FAMILY, with your organization's licence beside it. A
    licence covers the family, while a download names a specific version,
    so the ids passed to `download` and `checksum` come from `versions`.

        Attributes:
            base (str): The family, e.g. `vpn_ip`. What a licence is held against. Example: vpn_ip.
            name (str):  Example: VPN IP.
            summary (str): One line on what the newest version contains.
            standing (DatabaseStanding): `licensed` is a live grant, `expired` one whose term has ended, and
                `unlicensed` a database published but never bought.
            license_type (DatabaseLicenseTypeType1 | DatabaseLicenseTypeType2Type1 | DatabaseLicenseTypeType3Type1 | None):
                What your licence permits you to do with the data. Null when there
                is no licence.
            starts (datetime.datetime | None):
            expires (datetime.datetime | None): Null when the licence has no end date, or when there is none.
            versions (list[DatabaseVersion]): Every published version of this family, oldest first. Old versions
                are frozen rather than migrated, so both stay downloadable.
    """

    base: str
    name: str
    summary: str
    standing: DatabaseStanding
    license_type: (
        DatabaseLicenseTypeType1
        | DatabaseLicenseTypeType2Type1
        | DatabaseLicenseTypeType3Type1
        | None
    )
    starts: datetime.datetime | None
    expires: datetime.datetime | None
    versions: list[DatabaseVersion]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base = self.base

        name = self.name

        summary = self.summary

        standing = self.standing.value

        license_type: None | str
        if (
            isinstance(self.license_type, DatabaseLicenseTypeType1)
            or isinstance(self.license_type, DatabaseLicenseTypeType2Type1)
            or isinstance(self.license_type, DatabaseLicenseTypeType3Type1)
        ):
            license_type = self.license_type.value
        else:
            license_type = self.license_type

        starts: None | str
        if isinstance(self.starts, datetime.datetime):
            starts = self.starts.isoformat()
        else:
            starts = self.starts

        expires: None | str
        if isinstance(self.expires, datetime.datetime):
            expires = self.expires.isoformat()
        else:
            expires = self.expires

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "base": base,
                "name": name,
                "summary": summary,
                "standing": standing,
                "license_type": license_type,
                "starts": starts,
                "expires": expires,
                "versions": versions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.database_version import DatabaseVersion

        d = dict(src_dict)
        base = d.pop("base")

        name = d.pop("name")

        summary = d.pop("summary")

        standing = DatabaseStanding(d.pop("standing"))

        def _parse_license_type(
            data: object,
        ) -> (
            DatabaseLicenseTypeType1
            | DatabaseLicenseTypeType2Type1
            | DatabaseLicenseTypeType3Type1
            | None
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                license_type_type_1 = DatabaseLicenseTypeType1(data)

                return license_type_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                license_type_type_2_type_1 = DatabaseLicenseTypeType2Type1(data)

                return license_type_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                license_type_type_3_type_1 = DatabaseLicenseTypeType3Type1(data)

                return license_type_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                DatabaseLicenseTypeType1
                | DatabaseLicenseTypeType2Type1
                | DatabaseLicenseTypeType3Type1
                | None,
                data,
            )

        license_type = _parse_license_type(d.pop("license_type"))

        def _parse_starts(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                starts_type_0 = datetime.datetime.fromisoformat(data)

                return starts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        starts = _parse_starts(d.pop("starts"))

        def _parse_expires(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_type_0 = datetime.datetime.fromisoformat(data)

                return expires_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires = _parse_expires(d.pop("expires"))

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = DatabaseVersion.from_dict(versions_item_data)

            versions.append(versions_item)

        database = cls(
            base=base,
            name=name,
            summary=summary,
            standing=standing,
            license_type=license_type,
            starts=starts,
            expires=expires,
            versions=versions,
        )

        database.additional_properties = d
        return database

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
