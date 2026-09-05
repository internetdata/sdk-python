"""The staging credential, and whether this run has one.

Its own module, importing nothing but the standard library, because `scripts/run.py`
reads it BEFORE pip has installed anything: the runner has to decide what it is about to
do while the virtualenv is still empty.
"""

from __future__ import annotations

import os

SECRET = "INTERNETDATA_STAGING_KEY"

STAGING = "https://staging.internetdata.io"


def key() -> str:
    """The staging credential, or an empty string.

    Actions interpolates a secret that does not exist to an EMPTY STRING rather than
    leaving the variable unset, so "set but empty" and "absent" are the same thing here,
    and both mean the suite has nothing to authenticate with. This gate is the only thing
    standing between that and a green run: the client accepts a keyless build and sends
    no `Authorization` header, so an ungated suite would collect 401s that every
    assertion downstream reads as an ordinary refusal.
    """
    return os.environ.get(SECRET, "").strip()


def skip_reason() -> str | None:
    """A reason this suite cannot run, or None."""
    if key() != "":
        return None
    return f"{SECRET} is not set, so there is no key to exercise the API with"


def notice(message: str) -> None:
    """Surfaced on the workflow run itself, so a skip is visible without opening the log
    and reading to the end of it."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::notice title=Integration::{message}")
        return
    print(f"==> {message}")
