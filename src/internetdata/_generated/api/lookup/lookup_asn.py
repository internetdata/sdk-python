from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.asn_lookup_response import AsnLookupResponse
from ...models.lookup_error import LookupError_
from ...types import Response


def _get_kwargs(
    asn: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/asn/{asn}".format(
            asn=quote(str(asn), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AsnLookupResponse | LookupError_ | None:
    if response.status_code == 200:
        response_200 = AsnLookupResponse.from_dict(response.json())

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
) -> Response[AsnLookupResponse | LookupError_]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    asn: str,
    *,
    client: AuthenticatedClient,
) -> Response[AsnLookupResponse | LookupError_]:
    """ASN lookup

     Answers what InternetData knows about one autonomous system: its registration on every plan,
    and on a paid one its ASN Whois record and every prefix it announces in global BGP, with RPKI
    status,
    up to 20000 per address family (the counts beside them are always whole). An AS no database knows
    answers
    its number with empty values.

    Args:
        asn (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AsnLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        asn=asn,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    asn: str,
    *,
    client: AuthenticatedClient,
) -> AsnLookupResponse | LookupError_ | None:
    """ASN lookup

     Answers what InternetData knows about one autonomous system: its registration on every plan,
    and on a paid one its ASN Whois record and every prefix it announces in global BGP, with RPKI
    status,
    up to 20000 per address family (the counts beside them are always whole). An AS no database knows
    answers
    its number with empty values.

    Args:
        asn (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AsnLookupResponse | LookupError_
    """

    return sync_detailed(
        asn=asn,
        client=client,
    ).parsed


async def asyncio_detailed(
    asn: str,
    *,
    client: AuthenticatedClient,
) -> Response[AsnLookupResponse | LookupError_]:
    """ASN lookup

     Answers what InternetData knows about one autonomous system: its registration on every plan,
    and on a paid one its ASN Whois record and every prefix it announces in global BGP, with RPKI
    status,
    up to 20000 per address family (the counts beside them are always whole). An AS no database knows
    answers
    its number with empty values.

    Args:
        asn (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AsnLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        asn=asn,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    asn: str,
    *,
    client: AuthenticatedClient,
) -> AsnLookupResponse | LookupError_ | None:
    """ASN lookup

     Answers what InternetData knows about one autonomous system: its registration on every plan,
    and on a paid one its ASN Whois record and every prefix it announces in global BGP, with RPKI
    status,
    up to 20000 per address family (the counts beside them are always whole). An AS no database knows
    answers
    its number with empty values.

    Args:
        asn (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AsnLookupResponse | LookupError_
    """

    return (
        await asyncio_detailed(
            asn=asn,
            client=client,
        )
    ).parsed
