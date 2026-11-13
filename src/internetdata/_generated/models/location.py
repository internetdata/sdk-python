from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Location")


@_attrs_define
class Location:
    """Where the address is.

    Attributes:
        continent (str): Continent code.
        continent_name (str): Continent name.
        country (str): ISO 3166-1 alpha-2 country code.
        country_name (str): Country name.
        timezone (str): IANA timezone.
        currency_code (str): ISO 4217 code.
        currency_name (str): Currency name.
        currency_symbol (str): Currency symbol.
        flag_emoji (str): The country's flag.
        flag_unicode (str): Its code points, `U+1F1E6 U+1F1F9`.
        region (str | Unset): Region (state or province). Paid plans and the trial.
        region_code (str | Unset): ISO 3166-2 region code. Paid plans and the trial.
        city (str | Unset): City. Paid plans and the trial.
        postal_code (str | Unset): Postal code. Paid plans and the trial.
        latitude (float | Unset): Latitude of the city. Paid plans and the trial.
        longitude (float | Unset): Longitude of the city. Paid plans and the trial.
        accuracy_radius (int | Unset): Radius in km holding the true location with 67% confidence. Paid plans and the
            trial.
        geoname_id (str | Unset): GeoNames ID of the city. Paid plans and the trial.
        dma_code (str | Unset): US TV market (DMA) code. Paid plans and the trial.
        last_changed (str | Unset): The day the range's location last changed. Paid plans and the trial.
    """

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
    region: str | Unset = UNSET
    region_code: str | Unset = UNSET
    city: str | Unset = UNSET
    postal_code: str | Unset = UNSET
    latitude: float | Unset = UNSET
    longitude: float | Unset = UNSET
    accuracy_radius: int | Unset = UNSET
    geoname_id: str | Unset = UNSET
    dma_code: str | Unset = UNSET
    last_changed: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        continent = self.continent

        continent_name = self.continent_name

        country = self.country

        country_name = self.country_name

        timezone = self.timezone

        currency_code = self.currency_code

        currency_name = self.currency_name

        currency_symbol = self.currency_symbol

        flag_emoji = self.flag_emoji

        flag_unicode = self.flag_unicode

        region = self.region

        region_code = self.region_code

        city = self.city

        postal_code = self.postal_code

        latitude = self.latitude

        longitude = self.longitude

        accuracy_radius = self.accuracy_radius

        geoname_id = self.geoname_id

        dma_code = self.dma_code

        last_changed = self.last_changed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "continent": continent,
                "continent_name": continent_name,
                "country": country,
                "country_name": country_name,
                "timezone": timezone,
                "currency_code": currency_code,
                "currency_name": currency_name,
                "currency_symbol": currency_symbol,
                "flag_emoji": flag_emoji,
                "flag_unicode": flag_unicode,
            }
        )
        if region is not UNSET:
            field_dict["region"] = region
        if region_code is not UNSET:
            field_dict["region_code"] = region_code
        if city is not UNSET:
            field_dict["city"] = city
        if postal_code is not UNSET:
            field_dict["postal_code"] = postal_code
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if accuracy_radius is not UNSET:
            field_dict["accuracy_radius"] = accuracy_radius
        if geoname_id is not UNSET:
            field_dict["geoname_id"] = geoname_id
        if dma_code is not UNSET:
            field_dict["dma_code"] = dma_code
        if last_changed is not UNSET:
            field_dict["last_changed"] = last_changed

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        continent = d.pop("continent")

        continent_name = d.pop("continent_name")

        country = d.pop("country")

        country_name = d.pop("country_name")

        timezone = d.pop("timezone")

        currency_code = d.pop("currency_code")

        currency_name = d.pop("currency_name")

        currency_symbol = d.pop("currency_symbol")

        flag_emoji = d.pop("flag_emoji")

        flag_unicode = d.pop("flag_unicode")

        region = d.pop("region", UNSET)

        region_code = d.pop("region_code", UNSET)

        city = d.pop("city", UNSET)

        postal_code = d.pop("postal_code", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        accuracy_radius = d.pop("accuracy_radius", UNSET)

        geoname_id = d.pop("geoname_id", UNSET)

        dma_code = d.pop("dma_code", UNSET)

        last_changed = d.pop("last_changed", UNSET)

        location = cls(
            continent=continent,
            continent_name=continent_name,
            country=country,
            country_name=country_name,
            timezone=timezone,
            currency_code=currency_code,
            currency_name=currency_name,
            currency_symbol=currency_symbol,
            flag_emoji=flag_emoji,
            flag_unicode=flag_unicode,
            region=region,
            region_code=region_code,
            city=city,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            accuracy_radius=accuracy_radius,
            geoname_id=geoname_id,
            dma_code=dma_code,
            last_changed=last_changed,
        )

        location.additional_properties = d
        return location

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
