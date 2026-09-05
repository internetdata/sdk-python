from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.database_metadata_sample import DatabaseMetadataSample
    from ..models.database_metadata_schema import DatabaseMetadataSchema
    from ..models.database_metadata_size import DatabaseMetadataSize


T = TypeVar("T", bound="DatabaseMetadata")


@_attrs_define
class DatabaseMetadata:
    """The build document written by the exporter, served through unchanged.

    Attributes:
        id (str):
        updated (datetime.date): ISO-8601 date (YYYY-MM-DD) the published build was generated on. Example: 2026-09-04.
        entries (int): Row count in the current build.
        schema (DatabaseMetadataSchema): Columns, keyed by format.
        size (DatabaseMetadataSize): Bytes per format.
        update_freq (str | Unset): How often a new build is published.
        sample (DatabaseMetadataSample | Unset): A few real rows, keyed by format.
    """

    id: str
    updated: datetime.date
    entries: int
    schema: DatabaseMetadataSchema
    size: DatabaseMetadataSize
    update_freq: str | Unset = UNSET
    sample: DatabaseMetadataSample | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        updated = self.updated.isoformat()

        entries = self.entries

        schema = self.schema.to_dict()

        size = self.size.to_dict()

        update_freq = self.update_freq

        sample: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sample, Unset):
            sample = self.sample.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "updated": updated,
                "entries": entries,
                "schema": schema,
                "size": size,
            }
        )
        if update_freq is not UNSET:
            field_dict["update_freq"] = update_freq
        if sample is not UNSET:
            field_dict["sample"] = sample

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.database_metadata_sample import DatabaseMetadataSample
        from ..models.database_metadata_schema import DatabaseMetadataSchema
        from ..models.database_metadata_size import DatabaseMetadataSize

        d = dict(src_dict)
        id = d.pop("id")

        updated = datetime.date.fromisoformat(d.pop("updated"))

        entries = d.pop("entries")

        schema = DatabaseMetadataSchema.from_dict(d.pop("schema"))

        size = DatabaseMetadataSize.from_dict(d.pop("size"))

        update_freq = d.pop("update_freq", UNSET)

        _sample = d.pop("sample", UNSET)
        sample: DatabaseMetadataSample | Unset
        if isinstance(_sample, Unset):
            sample = UNSET
        else:
            sample = DatabaseMetadataSample.from_dict(_sample)

        database_metadata = cls(
            id=id,
            updated=updated,
            entries=entries,
            schema=schema,
            size=size,
            update_freq=update_freq,
            sample=sample,
        )

        database_metadata.additional_properties = d
        return database_metadata

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
