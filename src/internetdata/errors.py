"""The one exception this library raises, and how a response becomes one."""

from __future__ import annotations

import datetime
import email.utils
import math
from typing import Any, Literal

import httpx

__all__ = [
    "ErrorKind",
    "InternetDataError",
    "OauthAccessDeniedError",
    "OauthError",
    "OauthExpiredTokenError",
]

ErrorKind = Literal[
    "bad_request",
    "unauthorized",
    "forbidden",
    "rate_limited",
    "quota_exceeded",
    "server_error",
    "network",
]
"""Why a request failed.

`rate_limited` and `quota_exceeded` both arrive as HTTP 429 and are NOT the same thing.
A rate limit is the API protecting itself and carries `Retry-After`; retrying works. A
spent quota carries no such header and retrying will not help until the window rolls
over or the limit is raised. The header is the only thing that distinguishes them.
"""

_RETRYABLE: frozenset[str] = frozenset({"rate_limited", "server_error", "network"})


class InternetDataError(Exception):
    """Every failure this library reports, discriminated by `kind`."""

    kind: ErrorKind
    status: int | None
    retry_after_seconds: float | None

    def __init__(
        self,
        kind: ErrorKind,
        message: str,
        status: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status
        self.retry_after_seconds = retry_after_seconds

    @property
    def message(self) -> str:
        return str(self)

    @property
    def retryable(self) -> bool:
        """Whether retrying this exact request could succeed."""
        return self.kind in _RETRYABLE

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(kind={self.kind!r}, status={self.status!r}, "
            f"message={str(self)!r})"
        )


class OauthError(InternetDataError):
    """The authorization server refusing an OAuth request, such as `slow_down` or
    `invalid_grant`. Never retryable: every token exchange spends what it presents.

    Its `kind` follows the status like any response's, so a 401 here is `unauthorized` and
    means an unregistered `client_id`, never the API key, which these requests do not carry.
    """

    error_code: str
    """The server's code, kept as sent."""
    error_description: str | None
    """The server's explanation, when it sent one."""

    def __init__(
        self, error_code: str, error_description: str | None = None, status: int | None = None
    ) -> None:
        kind = (
            "bad_request" if status is None else error_from_response(status, _NO_HEADERS, None).kind
        )
        message = error_code if error_description is None else f"{error_code}: {error_description}"
        super().__init__(kind, message, status)
        self.error_code = error_code
        self.error_description = error_description

    @property
    def retryable(self) -> bool:
        return False


class OauthAccessDeniedError(OauthError):
    """The person refused the sign-in. Its device code is spent, so a new attempt starts over."""

    def __init__(self, error_description: str | None = None, status: int | None = None) -> None:
        super().__init__("access_denied", error_description, status)


class OauthExpiredTokenError(OauthError):
    """The device code is no longer valid: it expired, or was already used or refused. A poll
    that outlives the code raises this itself, with a `status` of None."""

    def __init__(self, error_description: str | None = None, status: int | None = None) -> None:
        super().__init__("expired_token", error_description, status)


def oauth_error_from(error_code: str, error_description: str | None, status: int) -> OauthError:
    if error_code == "access_denied":
        return OauthAccessDeniedError(error_description, status)
    if error_code == "expired_token":
        return OauthExpiredTokenError(error_description, status)
    return OauthError(error_code, error_description, status)


def error_from_response(status: int, headers: httpx.Headers, body: Any) -> InternetDataError:
    """Classify a failed response.

    Everything outside the four named statuses is decided by its RANGE rather than by an
    enumerated list, which is the whole point: a 404 from a database id that does not
    exist has to land on a client error, and mapping 400/401/403/429 and letting the rest
    fall through to `server_error` retries it twice before failing. Three of the four
    first SDKs shipped exactly that bug, so the shared corpus pins both 404 shapes.
    """
    message = _message_of(body) or f"request failed with status {status}"
    retry_after = _parse_retry_after(headers.get("retry-after"))

    if status == 429:
        # Present means transient, absent means an allowance is spent. Nothing else in
        # the response separates the two.
        if retry_after is None:
            return InternetDataError("quota_exceeded", message, status)
        return InternetDataError("rate_limited", message, status, retry_after)
    if status == 401:
        return InternetDataError("unauthorized", message, status)
    if status == 403:
        return InternetDataError("forbidden", message, status)
    if 400 <= status < 500:
        return InternetDataError("bad_request", message, status)
    return InternetDataError("server_error", message, status)


_NO_HEADERS = httpx.Headers()


def _message_of(body: Any) -> str | None:
    """The API's own result code, which is the whole error envelope.

    `rc` is deliberately not an enum in the spec, so a code added later stays readable by
    a client generated today. Passing it through verbatim is what keeps that promise: a
    caller switching on `NOT_LICENSED` versus `LICENSE_EXPIRED` needs the string, not a
    status.
    """
    if not isinstance(body, dict):
        return None
    code = body.get("rc")
    if isinstance(code, str) and code != "":
        return code
    return None


def _parse_retry_after(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        seconds = float(value)
    except ValueError:
        pass
    else:
        return seconds if seconds >= 0 else None
    # The header also permits an HTTP date.
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.UTC)
    delta = (when - datetime.datetime.now(datetime.UTC)).total_seconds()
    return max(0.0, math.ceil(delta))
