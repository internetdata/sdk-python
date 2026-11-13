from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.lookup_error import LookupError_
from ...models.lookup_response import LookupResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/myip",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> LookupError_ | LookupResponse | None:
    if response.status_code == 200:
        response_200 = LookupResponse.from_dict(response.json())

        return response_200

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
) -> Response[LookupError_ | LookupResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[LookupError_ | LookupResponse]:
    """My IP

     The address you are calling from, answered as `GET /{ip}` would answer it, and charged as
    that lookup is.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LookupError_ | LookupResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> LookupError_ | LookupResponse | None:
    """My IP

     The address you are calling from, answered as `GET /{ip}` would answer it, and charged as
    that lookup is.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LookupError_ | LookupResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[LookupError_ | LookupResponse]:
    """My IP

     The address you are calling from, answered as `GET /{ip}` would answer it, and charged as
    that lookup is.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LookupError_ | LookupResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> LookupError_ | LookupResponse | None:
    """My IP

     The address you are calling from, answered as `GET /{ip}` would answer it, and charged as
    that lookup is.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LookupError_ | LookupResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
