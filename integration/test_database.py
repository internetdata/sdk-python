"""The whole API, against the real staging deployment, through the PUBLISHED package.

The transfer is budgeted before it starts. `metadata` publishes a size per format, and that
size is checked against the ceiling below FIRST, so a mistaken database id can never
quietly pull one of the multi-gigabyte families through CI.

Nothing here hardcodes which families the key is licensed for. The organization behind the
staging secret holds the two smallest published families and nothing else, but asserting
their names would turn a licence change into an SDK failure; what the suite pins is the
RELATION - something licensed to transfer, something unlicensed to be refused.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import credential
import pytest
import staging
from staging import AsyncRecorder, Fact, Recorder

from internetdata import AsyncInternetData, Database, Format, InternetData, InternetDataError

FORMAT: Format = "csvgz"

# 8 MiB. The families this key can reach are a few hundred bytes each and the largest in
# the catalog is several GiB, so tripping this means the suite is pointed somewhere
# unintended - which is exactly when a transfer must not go ahead.
CEILING = 8 << 20

HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")

STANDINGS = ("licensed", "expired", "unlicensed")
RIGHTS = ("evaluation", "internal", "redistribute")
FORMATS = ("csvgz", "mmdb")


def test_the_catalog_answers_the_schema_the_client_was_generated_from() -> None:
    client, recorder = api()
    try:
        families = catalog(client)
    finally:
        client.close()

    # Everything below is vacuous unless the key reached the wire. The client builds
    # happily without one and then sends no `Authorization` header at all, which is
    # exactly what an unset CI secret produces, so this is where it has to be caught.
    to_api = [fact for fact in recorder.facts if fact.origin == credential.STAGING]
    assert to_api, "no request reached the staging API"
    for fact in to_api:
        assert fact.carried_key, f"the request to {fact.path} carried no key"

    assert families, "the catalog came back empty, so this key sees nothing at all"
    for family in families:
        assert family.base and family.name, f"a family carries no base or name: {family}"
        assert family.standing in STANDINGS, (
            f"{family.base} carries an undocumented standing {family.standing!r}"
        )
        assert family.redistribution is None or family.redistribution in RIGHTS, (
            f"{family.base} carries an undocumented right {family.redistribution!r}"
        )
        # A licence covers the family, and these are the ids the other calls take.
        assert family.versions, f"{family.base} carries no versions"
        for version in family.versions:
            assert version.id.startswith(family.base), (
                f"{version.id} is not a version of {family.base}"
            )
            assert version.formats, f"{version.id} carries no formats"
            for fmt in version.formats:
                assert fmt in FORMATS, f"{version.id} is built in an undocumented {fmt!r}"
    print(f"==> catalog: {', '.join(f'{f.base}={f.standing}' for f in families)}")


def test_an_unlicensed_family_is_absent_or_marked_never_half_licensed() -> None:
    """The visibility contract, from the outside.

    An organization sees the whole published catalog with a `standing` beside each entry,
    EXCEPT for the families built for a single customer, which are absent entirely. So the
    only thing a client can check without knowing what it is not allowed to see is that
    every entry it did get is internally consistent: a live grant carries a
    redistribution right, and one it never bought does not.
    """
    client, _ = api()
    try:
        families = catalog(client)
    finally:
        client.close()

    for family in families:
        if family.standing == "licensed":
            assert family.redistribution is not None, (
                f"{family.base} is licensed but says nothing about redistribution"
            )
        if family.standing == "unlicensed":
            assert family.redistribution is None, (
                f"{family.base} was never bought but carries a redistribution right"
            )
            assert family.starts is None, f"{family.base} was never bought but has a start date"


def test_metadata_describes_the_build_without_moving_it() -> None:
    client, recorder = api()
    try:
        target = licensed_version(client)
        meta = client.database.metadata(target.id)
    finally:
        client.close()

    assert meta.id == target.id, f"metadata answered about {meta.id!r}, want {target.id!r}"
    assert meta.entries > 0, f"{target.id} publishes {meta.entries} rows"
    assert meta.size, f"{target.id} publishes no size to budget a transfer against"
    for fmt in target.formats:
        assert fmt in meta.size, f"{target.id} is built in {fmt} but publishes no {fmt} size"
        assert meta.size[fmt] > 0, f"{target.id}.{fmt} is published as {meta.size[fmt]} bytes"
    assert meta.schema, f"{target.id} publishes no column list"
    # Nothing here is a transfer: the largest response is a handful of sample rows.
    assert recorder.storage_facts() == [], "metadata went to object storage"
    print(f"==> {target.id}: {meta.entries} rows, updated {meta.updated}, sizes {meta.size}")


def test_download_streams_a_real_database_to_disk_intact() -> None:
    got = transferred()

    assert got.written > 0, "nothing was transferred"
    assert got.path.stat().st_size == got.written, (
        f"the file is {got.path.stat().st_size} bytes and the method reported {got.written}"
    )
    assert not Path(f"{got.path}.part").exists(), "the .part file outlived a successful transfer"
    body = got.path.read_bytes()
    assert body[:2] == b"\x1f\x8b", "the payload is not gzip"

    assert HEX_DIGEST.match(got.sha256), (
        f"sha256 = {got.sha256!r}, so the checksums did not unwrap past the envelope"
    )
    assert digest(body) == got.sha256, (
        f"the bytes hash to {digest(body)} and the API publishes {got.sha256}"
    )
    assert got.written == got.published_size, (
        f"metadata promised {got.published_size} bytes and {got.written} arrived"
    )


def test_the_api_key_never_reaches_object_storage() -> None:
    """The presigned URL authorizes itself, so the request that follows the 302 must carry
    no credential - and object storage answers 400 to one that carries both."""
    got = transferred()

    assert got.storage, "nothing was fetched from object storage, so no 302 was followed"
    for fact in got.storage:
        assert not fact.carried_key, f"the API key was sent to object storage at {fact.origin}"


def test_download_url_hands_back_a_credential_free_link() -> None:
    client, recorder = api()
    try:
        target = licensed_version(client)
        url = client.database.download_url(target.id, FORMAT)
    finally:
        client.close()

    assert url.startswith("https://"), f"the link is {url!r}"
    assert credential.key() not in url, "the API key ended up in a link meant to be passed around"
    assert recorder.storage_facts() == [], "the link was fetched as well as returned"
    print(f"==> download_url answered {url.split('?')[0]} plus a signature")


def test_download_bytes_agrees_with_the_streamed_copy() -> None:
    got = transferred()
    client, _ = api()
    try:
        raw = client.database.download_bytes(got.database_id, FORMAT)
    finally:
        client.close()

    assert len(raw) == got.written, (
        f"the in-memory copy is {len(raw)} bytes and the streamed one {got.written}"
    )
    assert digest(raw) == got.sha256, "the two ways of fetching one file disagree"


def test_the_async_client_downloads_the_same_bytes() -> None:
    got = transferred()

    raw, facts = asyncio.run(async_download(got.database_id))

    assert digest(raw) == got.sha256, "the async client transferred something else"
    storage = [fact for fact in facts if fact.origin != credential.STAGING]
    assert storage, "the async client followed no 302"
    for fact in storage:
        assert not fact.carried_key, f"the async client sent the key to {fact.origin}"


def test_a_family_the_organization_does_not_license_is_refused_cleanly() -> None:
    client, recorder = api()
    try:
        target = unlicensed_version(client)
        with pytest.raises(InternetDataError) as caught:
            client.database.download_url(target.id, target.formats[0])
    finally:
        client.close()

    err = caught.value
    assert err.kind == "forbidden", f"{target.id}: kind = {err.kind!r}, want 'forbidden'"
    assert err.status == 403
    assert err.retryable is False, "a licence refusal is not worth retrying"
    # The API says which refusal this is (`{"rc": "NOT_LICENSED"}`). Falling back to the
    # status means the client never read the envelope.
    assert not err.message.startswith("request failed with status"), (
        f"message = {err.message!r}, which is the client fallback, so the body went unread"
    )
    assert len([f for f in recorder.facts if f.path.endswith("/download")]) == 1, (
        "a 403 was retried"
    )
    print(f"==> {target.id} refused with rc={err.message}")


def test_an_unknown_database_is_a_client_error_rather_than_a_retry() -> None:
    client, recorder = api()
    try:
        with pytest.raises(InternetDataError) as caught:
            client.database.metadata("no_such_database_v1")
    finally:
        client.close()

    assert caught.value.retryable is False, "a 404 was classified as retryable"
    assert caught.value.status == 404
    assert len(recorder.facts) == 1, f"issued {len(recorder.facts)} requests for a 404"


def test_the_download_just_made_shows_up_in_the_history() -> None:
    got = transferred()
    client, _ = api()
    try:
        attempts = client.database.downloads(limit=50)
    finally:
        client.close()

    assert attempts, "the history is empty after a download"
    assert attempts == sorted(attempts, key=lambda a: a.created, reverse=True), (
        "the history is not newest first"
    )
    mine = [a for a in attempts if a.dataset_id == got.database_id and a.outcome == "ok"]
    assert mine, f"no successful {got.database_id} attempt in the last {len(attempts)}"
    print(f"==> history: {len(attempts)} attempts, newest {attempts[0].created}")


def api() -> tuple[InternetData, Recorder]:
    return staging.client()


def catalog(client: InternetData) -> list[Database]:
    return client.database.list()


@dataclass(frozen=True)
class Target:
    id: str
    formats: tuple[Format, ...]


def licensed_version(client: InternetData) -> Target:
    """The smallest thing this key may actually download, picked from the catalog.

    Chosen rather than named so a licence change is not an SDK failure, and restricted to
    a version built in `FORMAT` because that is the one the transfer tests fetch.
    """
    for family in catalog(client):
        if family.standing != "licensed":
            continue
        for version in family.versions:
            if FORMAT in version.formats:
                return Target(version.id, version.formats)
    pytest.skip(f"this key licenses nothing built in {FORMAT}, so there is nothing to transfer")


def unlicensed_version(client: InternetData) -> Target:
    """A real catalog id this key holds no licence for."""
    for family in catalog(client):
        if family.standing == "licensed":
            continue
        for version in family.versions:
            if version.formats:
                return Target(version.id, version.formats)
    pytest.skip("this key licenses the entire catalog, so nothing is left to be refused")


@dataclass(frozen=True)
class Transfer:
    database_id: str
    written: int
    published_size: int
    path: Path
    sha256: str
    storage: list[Fact]


_transfer: Transfer | None = None


def transferred() -> Transfer:
    """The one real download this suite makes, memoized.

    Held in a directory of the module's own rather than a pytest `tmp_path`, which belongs
    to whichever test happened to ask first and would be gone before the others read it.
    """
    global _transfer
    if _transfer is not None:
        return _transfer

    client, recorder = api()
    try:
        target = licensed_version(client)
        meta = client.database.metadata(target.id)
        size = meta.size.get(FORMAT, 0)
        # Budgeted BEFORE a byte moves: this is what stands between a mistaken id and
        # several gigabytes through a CI runner.
        assert 0 < size <= CEILING, (
            f"{target.id}.{FORMAT} is {size} bytes, past the {CEILING} ceiling, so it is "
            f"not transferred"
        )

        path = Path(tempfile.mkdtemp(prefix="internetdata-integration-")) / f"{target.id}.csv.gz"
        written = client.database.download(target.id, FORMAT, path)
        # Read after the transfer, so a rebuild between the two calls shows up as a digest
        # mismatch rather than passing against a digest of nothing.
        checksums = client.database.checksums(target.id, FORMAT)
    finally:
        client.close()
    print(f"==> {target.id}.{FORMAT}: {written} bytes, metadata says {size}")

    _transfer = Transfer(
        database_id=target.id,
        written=written,
        published_size=size,
        path=path,
        sha256=checksums.get("sha256", ""),
        storage=recorder.storage_facts(),
    )
    return _transfer


async def async_download(database_id: str) -> tuple[bytes, list[Fact]]:
    client: AsyncInternetData
    recorder: AsyncRecorder
    client, recorder = staging.async_client()
    try:
        return await client.database.download_bytes(database_id, FORMAT), recorder.facts
    finally:
        await client.aclose()


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()
