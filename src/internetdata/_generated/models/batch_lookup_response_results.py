from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.asn_lookup_response import AsnLookupResponse
    from ..models.domain_lookup_response import DomainLookupResponse
    from ..models.lookup_response import LookupResponse


T = TypeVar("T", bound="BatchLookupResponseResults")


@_attrs_define
class BatchLookupResponseResults:
    """Each answered item's lookup, keyed by the string sent."""

    additional_properties: dict[str, AsnLookupResponse | DomainLookupResponse | LookupResponse] = (
        _attrs_field(init=False, factory=dict)
    )

    def to_dict(self) -> dict[str, Any]:
        from ..models.asn_lookup_response import AsnLookupResponse
        from ..models.lookup_response import LookupResponse

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, LookupResponse) or isinstance(prop, AsnLookupResponse):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.asn_lookup_response import AsnLookupResponse
        from ..models.domain_lookup_response import DomainLookupResponse
        from ..models.lookup_response import LookupResponse

        d = dict(src_dict)
        batch_lookup_response_results = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> AsnLookupResponse | DomainLookupResponse | LookupResponse:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = LookupResponse.from_dict(data)

                    return additional_property_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_1 = AsnLookupResponse.from_dict(data)

                    return additional_property_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                additional_property_type_2 = DomainLookupResponse.from_dict(data)

                return additional_property_type_2

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        batch_lookup_response_results.additional_properties = additional_properties
        return batch_lookup_response_results

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> AsnLookupResponse | DomainLookupResponse | LookupResponse:
        return self.additional_properties[key]

    def __setitem__(
        self, key: str, value: AsnLookupResponse | DomainLookupResponse | LookupResponse
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
