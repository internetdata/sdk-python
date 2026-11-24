#!/usr/bin/env python3

"""Narrows the pinned spec to what this client generates from, for codegen only.

    python3 scripts/v2_subset.py spec/openapi.yaml /tmp/v2.yaml

`spec/openapi.yaml` is pinned VERBATIM so a refresh diffs against what the API actually
publishes, and that document carries `/api/v1/database/*` as well. v1 is a frozen legacy
contract held for a handful of named customers: a different credential (`?apikey=<uuid>`
rather than a bearer token), a different error vocabulary, and no `list`. Generating it
would ship dead modules and, worse, a second credential spelling that looks usable from
this client and is not.

Everything else is kept: the lookups, the entitlement, the v2 database, IAM and OAuth, as
the VPNDetection SDK generates them. IAM is generated and left unwrapped; the `oauth`
accessor sends its own requests and never calls the generated authorization endpoints.

So the narrowing happens here rather than in the pinned copy. Unreferenced components go
with the paths, or the generator emits models for v1 envelopes nothing can reach.

Uses ruamel.yaml, which openapi-python-client already depends on, so the codegen
virtualenv needs nothing extra.
"""

from __future__ import annotations

import sys
from typing import Any

from ruamel.yaml import YAML

KEEP_PATH_PREFIXES = (
    "/api/v2/",
    "/{ip}",
    "/myip",
    "/asn/",
    "/domain/",
    "/batch",
    "/api/v1/entitlement",
    "/api/v1/iam/",
    "/oauth/",
    "/.well-known/oauth-authorization-server",
)
# v1's `?apikey=` credential. Dropped with v1 itself: leaving it in the spec would put a
# second, unusable auth spelling in the generated client.
DROP_SECURITY_SCHEMES = ("ApiKeyAuth",)
# Every components section that a `$ref` can point at in this spec.
REF_SECTIONS = ("schemas", "parameters", "responses")
# The seen days spec 2026.11.23 gave `format: date`. The answer types hand them back as the
# served string, as they did before (a minor never changes what a member returns), and
# `models` checks each is an RFC 3339 full-date; generated as `date`, the decoder would read
# them with `isoparse`, which takes far more than a full-date. Each edit fails once the spec
# stops matching it, so a moved member stops generation.
SEEN_DAYS = (
    ("ClassDetail", "last_seen"),
    ("ProxyDetail", "first_seen"),
    ("ProxyDetail", "last_seen"),
    ("PubproxyDetail", "last_seen"),
    ("BotDetail", "first_seen"),
    ("BotDetail", "last_seen"),
    ("SshDetail", "first_seen"),
    ("SshDetail", "last_seen"),
    ("SmtpDetail", "first_seen"),
    ("SmtpDetail", "last_seen"),
    ("WebDetail", "first_seen"),
    ("WebDetail", "last_seen"),
    ("DnsResolverDetail", "first_seen"),
    ("DnsResolverDetail", "last_seen"),
    ("BitTorrentDetail", "first_seen"),
    ("BitTorrentDetail", "last_seen"),
    ("AsnPrefix", "first_seen"),
    ("DnsAddressRecord", "last_seen"),
    ("DnsMxRecord", "last_seen"),
    ("DnsNsRecord", "last_seen"),
    ("DnsCnameRecord", "last_seen"),
    ("DisposableDetail", "first_seen"),
    ("DisposableDetail", "last_seen"),
)


def main(source: str, destination: str) -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(source) as handle:
        spec: dict[str, Any] = yaml.load(handle)

    paths = spec.get("paths", {})
    dropped = [path for path in paths if not path.startswith(KEEP_PATH_PREFIXES)]
    for path in dropped:
        del paths[path]
    if not any(path.startswith(KEEP_PATH_PREFIXES[0]) for path in paths):
        raise SystemExit(f"no {KEEP_PATH_PREFIXES[0]} paths survived, so the spec moved under us")

    components = spec.get("components", {})
    for scheme in DROP_SECURITY_SCHEMES:
        components.get("securitySchemes", {}).pop(scheme, None)
    # Every kept operation names its own security, so a document-level default could only
    # name the dropped v1 scheme, which would leave the spec invalid.
    spec.pop("security", None)

    schemas = components.get("schemas", {})
    for schema, member in SEEN_DAYS:
        prop = schemas.get(schema, {}).get("properties", {}).get(member, {})
        if prop.get("format") != "date":
            raise SystemExit(f"{schema}.{member} is no `format: date` member, so the spec moved")
        del prop["format"]

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
    print(f"{destination} <- {source} ({len(paths)} paths kept, dropped {len(dropped)})")
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
