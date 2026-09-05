#!/bin/bash

# Regenerates src/internetdata/_generated/ from the PINNED spec in this repo.
#
# Unlike most of the SDKs, the generated client is COMMITTED here: a Python
# package is installed from source, so a gitignored generated tree would mean a
# `pip install` of this repo produced a package that cannot import itself.
# Refresh it deliberately and commit the diff alongside any spec change.
#
# The generator lives in a throwaway virtualenv under /tmp rather than in the
# working tree, because a venv is thousands of files and one committed by
# accident is far more annoying to remove than to recreate.
#
#   ./scripts/generate.sh

set -euo pipefail

cd "$(dirname "$0")/.."

VENV="${VENV:-/tmp/internetdata-sdk-python-codegen}"
GENERATOR_VERSION="${GENERATOR_VERSION:-0.29.1}"
SUBSET="${SUBSET:-/tmp/internetdata-sdk-python-v2.yaml}"

if [ ! -x "$VENV/bin/openapi-python-client" ] ; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet "openapi-python-client==${GENERATOR_VERSION}"
fi

# ruff must be on PATH: the generator shells out to it to format and lint its
# own output, and silently skips both when it cannot find it. It picks up this
# repo's pyproject.toml, so `requires-python` decides whether the models import
# `Self` from typing or from typing_extensions - which is the difference between
# three runtime dependencies and four.
export PATH="$VENV/bin:$PATH"

# The pinned spec carries v1 as well, and this client does not target it. See
# scripts/v2_subset.py for why the narrowing happens here and not in spec/.
python3 scripts/v2_subset.py spec/openapi.yaml "$SUBSET"

rm -rf src/internetdata/_generated
openapi-python-client generate \
    --path "$SUBSET" \
    --meta none \
    --output-path src/internetdata/_generated

# The generator's own docstring templates carry em-dashes, which this codebase does
# not use anywhere. Normalizing them here keeps generation deterministic.
find src/internetdata/_generated -name '*.py' -exec sed -i 's/\xe2\x80\x94/ - /g' {} +

echo "src/internetdata/_generated <- spec/openapi.yaml"
grep -m1 '^  version:' spec/openapi.yaml
