#!/bin/bash

# The integration suite in docker, for a box whose python has no way to build a
# virtualenv or reach PyPI. CI runs `python3 scripts/run.py` directly; this is
# the same entry point with an interpreter around it.
#
#   ./scripts/run.sh
#
# The staging key is read from the environment and passed through by NAME, so it
# never reaches a command line. Only the integration directory is mounted: the
# suite must see the published package rather than the source beside it.

set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_IMAGE="${PYTHON_IMAGE:-python:3.13-slim}"

docker run --rm \
    -v "$PWD:/app" -w /app \
    -e PIP_ROOT_USER_ACTION=ignore \
    -e INTERNETDATA_STAGING_KEY \
    "$PYTHON_IMAGE" python3 scripts/run.py "$@"
