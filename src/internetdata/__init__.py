"""The official Python client library for the InternetData API.

    from internetdata import InternetData

    with InternetData(api_key) as client:
        for db in client.database.list():
            print(db.base, db.standing)

See https://internetdata.io for the API, and the README for downloads, checksums and
what the catalog does and does not show you.
"""

from ._core import DEFAULT_BASE_URL
from .aio import AsyncDatabaseApi, AsyncInternetData, AsyncOauthApi
from .client import DatabaseApi, InternetData, OauthApi
from .errors import (
    ErrorKind,
    InternetDataError,
    OauthAccessDeniedError,
    OauthError,
    OauthExpiredTokenError,
)
from .models import (
    DATABASE_FORMATS,
    LICENSE_TYPES,
    STANDINGS,
    Database,
    DatabaseMetadata,
    DatabaseVersion,
    DeviceAuthorization,
    Download,
    Format,
    LicenseType,
    MetadataColumn,
    OauthMetadata,
    Outcome,
    Pkce,
    Standing,
    TokenResponse,
)

__version__ = "2.5.0"

__all__ = [
    "DATABASE_FORMATS",
    "DEFAULT_BASE_URL",
    "LICENSE_TYPES",
    "STANDINGS",
    "AsyncDatabaseApi",
    "AsyncInternetData",
    "AsyncOauthApi",
    "Database",
    "DatabaseApi",
    "DatabaseMetadata",
    "DatabaseVersion",
    "DeviceAuthorization",
    "Download",
    "ErrorKind",
    "Format",
    "InternetData",
    "InternetDataError",
    "LicenseType",
    "MetadataColumn",
    "OauthAccessDeniedError",
    "OauthApi",
    "OauthError",
    "OauthExpiredTokenError",
    "OauthMetadata",
    "Outcome",
    "Pkce",
    "Standing",
    "TokenResponse",
    "__version__",
]
