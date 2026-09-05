"""The official Python client library for the InternetData API.

    from internetdata import InternetData

    with InternetData(api_key) as client:
        for db in client.database.list():
            print(db.base, db.standing)

See https://internetdata.io for the API, and the README for downloads, checksums and
what the catalog does and does not show you.
"""

from ._core import DEFAULT_BASE_URL
from .aio import AsyncDatabaseApi, AsyncInternetData
from .client import DatabaseApi, InternetData
from .errors import ErrorKind, InternetDataError
from .models import (
    Database,
    DatabaseMetadata,
    DatabaseVersion,
    Download,
    Format,
    MetadataColumn,
    Outcome,
    LicenseType,
    Standing,
)

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_BASE_URL",
    "AsyncDatabaseApi",
    "AsyncInternetData",
    "Database",
    "DatabaseApi",
    "DatabaseMetadata",
    "DatabaseVersion",
    "Download",
    "ErrorKind",
    "Format",
    "InternetData",
    "InternetDataError",
    "MetadataColumn",
    "Outcome",
    "LicenseType",
    "Standing",
    "__version__",
]
