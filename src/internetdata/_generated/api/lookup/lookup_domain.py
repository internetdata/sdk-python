from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.domain_lookup_response import DomainLookupResponse
from ...models.lookup_error import LookupError_
from ...types import Response


def _get_kwargs(
    domain: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/domain/{domain}".format(
            domain=quote(str(domain), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DomainLookupResponse | LookupError_ | None:
    if response.status_code == 200:
        response_200 = DomainLookupResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = LookupError_.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = LookupError_.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = LookupError_.from_dict(response.json())

        return response_403

    if response.status_code == 429:
        response_429 = LookupError_.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = LookupError_.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DomainLookupResponse | LookupError_]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    domain: str,
    *,
    client: AuthenticatedClient,
) -> Response[DomainLookupResponse | LookupError_]:
    """Domain lookup

     Answers what InternetData knows about one domain from its latest snapshots: on every plan
    whether it is registered and which DNS record types it has; on a paid one the records themselves, up
    to
    100 a type, the organization's IP ranges and whether it is a disposable email domain. An
    internationalized
    name is answered under its punycode spelling.

    Args:
        domain (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DomainLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        domain=domain,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    domain: str,
    *,
    client: AuthenticatedClient,
) -> DomainLookupResponse | LookupError_ | None:
    """Domain lookup

     Answers what InternetData knows about one domain from its latest snapshots: on every plan
    whether it is registered and which DNS record types it has; on a paid one the records themselves, up
    to
    100 a type, the organization's IP ranges and whether it is a disposable email domain. An
    internationalized
    name is answered under its punycode spelling.

    Args:
        domain (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DomainLookupResponse | LookupError_
    """

    return sync_detailed(
        domain=domain,
        client=client,
    ).parsed


async def asyncio_detailed(
    domain: str,
    *,
    client: AuthenticatedClient,
) -> Response[DomainLookupResponse | LookupError_]:
    """Domain lookup

     Answers what InternetData knows about one domain from its latest snapshots: on every plan
    whether it is registered and which DNS record types it has; on a paid one the records themselves, up
    to
    100 a type, the organization's IP ranges and whether it is a disposable email domain. An
    internationalized
    name is answered under its punycode spelling.

    Args:
        domain (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DomainLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        domain=domain,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    domain: str,
    *,
    client: AuthenticatedClient,
) -> DomainLookupResponse | LookupError_ | None:
    """Domain lookup

     Answers what InternetData knows about one domain from its latest snapshots: on every plan
    whether it is registered and which DNS record types it has; on a paid one the records themselves, up
    to
    100 a type, the organization's IP ranges and whether it is a disposable email domain. An
    internationalized
    name is answered under its punycode spelling.

    Args:
        domain (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DomainLookupResponse | LookupError_
    """

    return (
        await asyncio_detailed(
            domain=domain,
            client=client,
        )
    ).parsed
