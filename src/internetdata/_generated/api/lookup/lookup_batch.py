from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_lookup_request import BatchLookupRequest
from ...models.batch_lookup_response import BatchLookupResponse
from ...models.lookup_error import LookupError_
from ...types import Response


def _get_kwargs(
    *,
    body: BatchLookupRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/batch",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BatchLookupResponse | LookupError_ | None:
    if response.status_code == 200:
        response_200 = BatchLookupResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = LookupError_.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = LookupError_.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = LookupError_.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = LookupError_.from_dict(response.json())

        return response_403

    if response.status_code == 413:
        response_413 = LookupError_.from_dict(response.json())

        return response_413

    if response.status_code == 429:
        response_429 = LookupError_.from_dict(response.json())

        return response_429

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[BatchLookupResponse | LookupError_]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: BatchLookupRequest,
) -> Response[BatchLookupResponse | LookupError_]:
    """Batch

     Up to 1000 addresses, AS numbers and domains in one call, each answered exactly as its own
    lookup would be and each counted as one lookup. Answers and failures are keyed by the string you
    sent, in
    the order you sent them; duplicates collapse. Needs a paid plan: a batch of one item is answered as
    the
    lookup it is on any plan.

    Args:
        body (BatchLookupRequest): Up to 1000 items across the three arrays, each optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: BatchLookupRequest,
) -> BatchLookupResponse | LookupError_ | None:
    """Batch

     Up to 1000 addresses, AS numbers and domains in one call, each answered exactly as its own
    lookup would be and each counted as one lookup. Answers and failures are keyed by the string you
    sent, in
    the order you sent them; duplicates collapse. Needs a paid plan: a batch of one item is answered as
    the
    lookup it is on any plan.

    Args:
        body (BatchLookupRequest): Up to 1000 items across the three arrays, each optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchLookupResponse | LookupError_
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: BatchLookupRequest,
) -> Response[BatchLookupResponse | LookupError_]:
    """Batch

     Up to 1000 addresses, AS numbers and domains in one call, each answered exactly as its own
    lookup would be and each counted as one lookup. Answers and failures are keyed by the string you
    sent, in
    the order you sent them; duplicates collapse. Needs a paid plan: a batch of one item is answered as
    the
    lookup it is on any plan.

    Args:
        body (BatchLookupRequest): Up to 1000 items across the three arrays, each optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchLookupResponse | LookupError_]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: BatchLookupRequest,
) -> BatchLookupResponse | LookupError_ | None:
    """Batch

     Up to 1000 addresses, AS numbers and domains in one call, each answered exactly as its own
    lookup would be and each counted as one lookup. Answers and failures are keyed by the string you
    sent, in
    the order you sent them; duplicates collapse. Needs a paid plan: a batch of one item is answered as
    the
    lookup it is on any plan.

    Args:
        body (BatchLookupRequest): Up to 1000 items across the three arrays, each optional.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchLookupResponse | LookupError_
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
