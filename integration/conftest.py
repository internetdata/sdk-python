"""The gate and the run banner.

The gate runs before collection rather than as a test, because a suite pointed at local
source is not failing, it is answering the wrong question, and every test in it would pass
while doing so.
"""

from __future__ import annotations

import pytest
from credential import STAGING, notice, skip_reason
from staging import assert_published_artifact


def pytest_configure(config: pytest.Config) -> None:
    assert_published_artifact()

    reason = skip_reason()
    if reason:
        notice(f"{reason}: every test will skip")
        return
    print(f"==> exercising the published package against {STAGING}")
