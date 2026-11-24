from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.domain_web_links import DomainWebLinks


T = TypeVar("T", bound="DomainWeb")


@_attrs_define
class DomainWeb:
    """What our crawl last read of the domain's own home page, every member empty where it holds none. Paid plans and the
    trial.

        Attributes:
            url (str): The URL of the home page read.
            title (str): An English page's title.
            description (str): An English page's description.
            last_seen (str): The day it was last read, empty when the crawl holds no page.
            links (DomainWebLinks): The external hosts the home page links to.
    """

    url: str
    title: str
    description: str
    last_seen: str
    links: DomainWebLinks
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        title = self.title

        description = self.description

        last_seen = self.last_seen

        links = self.links.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "url": url,
                "title": title,
                "description": description,
                "last_seen": last_seen,
                "links": links,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.domain_web_links import DomainWebLinks

        d = dict(src_dict)
        url = d.pop("url")

        title = d.pop("title")

        description = d.pop("description")

        last_seen = d.pop("last_seen")

        links = DomainWebLinks.from_dict(d.pop("links"))

        domain_web = cls(
            url=url,
            title=title,
            description=description,
            last_seen=last_seen,
            links=links,
        )

        domain_web.additional_properties = d
        return domain_web

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
