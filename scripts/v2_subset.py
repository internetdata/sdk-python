#!/usr/bin/env python3

"""Narrows the pinned spec to the v2 API, for codegen only.

    python3 scripts/v2_subset.py spec/openapi.yaml /tmp/v2.yaml

`spec/openapi.yaml` is pinned VERBATIM so a refresh diffs against what the API actually
publishes, and that document carries `/api/v1/database/*` as well. v1 is a frozen legacy
contract held for a handful of named customers: a different credential (`?apikey=<uuid>`
rather than a bearer token), a different error vocabulary, and no `list`. Generating it
would ship dead modules and, worse, a second credential spelling that looks usable from
this client and is not.

So the narrowing happens here rather than in the pinned copy. Unreferenced components go
with the paths, or the generator emits models for v1 envelopes nothing can reach.

Uses ruamel.yaml, which openapi-python-client already depends on, so the codegen
virtualenv needs nothing extra.
"""

from __future__ import annotations

import sys
from typing import Any

from ruamel.yaml import YAML

KEEP_PATH_PREFIX = "/api/v2/"
# v1's `?apikey=` credential. Dropped with v1 itself: leaving it in the spec would put a
# second, unusable auth spelling in the generated client.
DROP_SECURITY_SCHEMES = ("ApiKeyAuth",)
# Every components section that a `$ref` can point at in this spec.
REF_SECTIONS = ("schemas", "parameters", "responses")


def main(source: str, destination: str) -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(source) as handle:
        spec: dict[str, Any] = yaml.load(handle)

    paths = spec.get("paths", {})
    dropped = [path for path in paths if not path.startswith(KEEP_PATH_PREFIX)]
    for path in dropped:
        del paths[path]
    if not paths:
        raise SystemExit(f"no {KEEP_PATH_PREFIX} paths survived, so the spec moved under us")

    components = spec.get("components", {})
    for scheme in DROP_SECURITY_SCHEMES:
        components.get("securitySchemes", {}).pop(scheme, None)
    # The document-level default is v1's; every v2 operation names BearerAuth itself, and
    # leaving a scheme here that no longer exists is an invalid spec.
    spec["security"] = [{"BearerAuth": []}]

    reachable = resolve_refs(spec, components)
    for section in REF_SECTIONS:
        entries = components.get(section)
        if entries is None:
            continue
        for name in [name for name in entries if f"#/components/{section}/{name}" not in reachable]:
            del entries[name]
        if not entries:
            del components[section]

    with open(destination, "w") as handle:
        yaml.dump(spec, handle)
    print(f"{destination} <- {source} ({len(paths)} v2 paths, dropped {len(dropped)})")
    return 0


def resolve_refs(spec: dict[str, Any], components: dict[str, Any]) -> set[str]:
    """Every `#/components/...` a kept path can reach, following refs through refs.

    A fixed point rather than one pass: `V2Unauthorized` is a response holding a ref to
    the `Error` schema, so a single sweep would keep the response and prune the schema it
    needs.
    """
    reachable = refs_in(spec.get("paths", {}))
    while True:
        found = set(reachable)
        for ref in reachable:
            _, _, section, name = ref.split("/")
            found |= refs_in(components.get(section, {}).get(name, {}))
        if found == reachable:
            return reachable
        reachable = found


def refs_in(node: Any) -> set[str]:
    if isinstance(node, dict):
        found: set[str] = set()
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and value.startswith("#/components/"):
                found.add(value)
            else:
                found |= refs_in(value)
        return found
    if isinstance(node, list):
        found = set()
        for item in node:
            found |= refs_in(item)
        return found
    return set()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} <source spec> <destination spec>")
    sys.exit(main(sys.argv[1], sys.argv[2]))
