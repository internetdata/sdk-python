# [<img src="https://s3.internetdata.io/internetdata-public/brand/mark.svg" alt="InternetData" height="28"/>](https://internetdata.io/) InternetData Python Client Library

[![PyPI](https://img.shields.io/pypi/v/internetdata.svg)](https://pypi.org/project/internetdata/)
[![license](https://img.shields.io/pypi/l/internetdata.svg)](LICENSE)

The official Python client library for the [InternetData](https://internetdata.io) API.

The library helps you browse the databases your organization is licensed for, check what is in each build before you fetch it, and download and verify the files.

## Getting Started

```bash
pip install internetdata
```

Requires Python 3.11 or newer. Type hints are included, and the package ships `py.typed`.

## Usage

Every call needs an API key carrying the `db.download` scope. Create one in the console, then:

```python
import os
from internetdata import InternetData

client = InternetData(os.environ["INTERNETDATA_API_KEY"])

for family in client.database.list():
    print(family.base, family.standing, [v.id for v in family.versions])
```

The client holds an HTTP connection pool, so use it as a context manager, or call `client.close()` when you are done with it:

```python
with InternetData(api_key) as client:
    print(len(client.database.list()))
```

### The catalog

`list` answers database FAMILIES. A license is held against a family, while a download names a specific version, so the ids the other calls take come from each family's `versions`:

```python
for family in client.database.list():
    if family.standing != "licensed":
        continue
    for version in family.versions:
        print(version.id, version.formats)   # 'bogon_ip_v1' ('csvgz', 'mmdb')
```

`standing` is `licensed`, `expired` or `unlicensed`, and `license_type` is what your license lets you do with the data (`evaluation`, `standard`, `redistribute`, or `None` when there is no license). A family you have never bought is still listed, as `unlicensed`, so you can see what else exists.

A rolling license also carries `renews_at`, when it next renews, and `notice_due_at`, the last day you can give notice of non-renewal for that term. Both are `None` when there is no license, when it has no defined term, or when `expires` sets a hard stop instead. `DATABASE_FORMATS`, `STANDINGS` and `LICENSE_TYPES` hold the published values at runtime, for checking one that came from a flag or a form before you make a call.

### What is inside a build

`metadata` is cheap enough to poll. It answers when the build was generated, how many rows it has, its columns and a few real rows, and the size of each format in bytes, all without moving the file:

```python
meta = client.database.metadata("bogon_ip_v1")

print(meta.updated)                  # datetime.date(2026, 9, 4)
print(meta.entries)                  # 1234
print(meta.size["csvgz"])            # 760
print([c.name for c in meta.schema["csvgz"]])
```

Checking `size` before a download is worth the round trip: the catalog spans a few hundred bytes to several gigabytes.

### Downloading

Three ways, depending on what you want to do with the bytes:

```python
url = client.database.download_url("bogon_ip_v1", "csvgz")
raw = client.database.download_bytes("bogon_ip_v1", "csvgz")
written = client.database.download("bogon_ip_v1", "mmdb", "./bogon_ip_v1.mmdb")
```

`download_url` hands back a time-limited link straight to object storage. It carries its own signature and none of your API key, so you can pass it to `curl`, a job runner or anything else that speaks HTTP. The link authorizes the START of a transfer, so one already running is not cut off when it lapses.

`download` streams to a file, so nothing larger than a chunk is ever held in memory. The bytes land in a neighboring `.part` file that is moved into place only once the whole transfer has arrived, so a failed refresh leaves the copy you already had untouched. `download_bytes` holds the whole file in memory, so reach for it only at the small end of the catalog.

Either way a short transfer fails rather than handing you a truncated file, and the key is never sent to object storage.

Verify what you fetched against the published digests:

```python
import hashlib

digests = client.database.checksums("bogon_ip_v1", "csvgz")
assert hashlib.sha256(raw).hexdigest() == digests["sha256"]
```

### Download history

`downloads` answers your organization's recent attempts, newest first, refusals included. A denial is what answers "it stopped working", and its absence answers nothing:

```python
for attempt in client.database.downloads(limit=20):
    print(attempt.created, attempt.dataset_id, attempt.outcome, attempt.http_status)
```

### Async

Everything above works the same way under asyncio, with `AsyncInternetData`:

```python
import asyncio
from internetdata import AsyncInternetData

async def main():
    async with AsyncInternetData(api_key) as client:
        meta = await client.database.metadata("bogon_ip_v1")
        await client.database.download("bogon_ip_v1", "csvgz", "./bogon_ip_v1.csv.gz")
        print(meta.entries)

asyncio.run(main())
```

### Errors

Failures raise an `InternetDataError` carrying a `kind` and a `retryable` flag:

```python
from internetdata import InternetDataError

try:
    client.database.download_url("vpn_ip_v1", "mmdb")
except InternetDataError as err:
    print(err.kind, err.retryable, err.message)   # forbidden False NOT_LICENSED
```

`kind` is one of `bad_request`, `unauthorized`, `forbidden`, `rate_limited`, `quota_exceeded`, `server_error` or `network`. `message` is the API's own result code, passed through as it was sent, so you can switch on `NOT_LICENSED` against `LICENSE_EXPIRED` without reading the status.

A request that runs past its `timeout` fails with `network`, and is retried like any other network failure. The default is 30 seconds per attempt, body included, so a retried call can take longer in total. A database transfer is exempt, so `download` and `download_bytes` are never cut off part way through a large file. Set it on the client, in seconds, or pass `None` for no bound. Anything else that is not a number greater than 0 raises `ValueError` where it is set:

```python
client = InternetData(api_key, timeout=10)
catalog = client.database.list(timeout=2)
```

From 2.3.0, `list`, `metadata`, `checksums`, `downloads` and `download_url` each take a keyword-only `timeout` in seconds, bounding each attempt at that one call in place of the client's; `None` there means the client's own rather than no bound. `download` and `download_bytes` deliberately take none and raise `TypeError` if handed one, rather than accepting it and quietly doing nothing: a transfer runs to gigabytes and minutes, so any bound that suits a JSON call would abandon a healthy download. `download_url` does take one, because minting the link is an ordinary API request - it bounds that request, not whatever you do with the link afterwards.

**Changed in 2.1.0:** the default was 10 seconds, and it bounded each read of a response rather than the whole attempt, so a response trickling in slowly could run past it for as long as the server kept sending.

**Changed in 2.2.0:** a timeout of 0 or less, NaN or a string used to be accepted, and failed every call.

Note that `rate_limited` and `quota_exceeded` both arrive as HTTP 429 and are not the same thing. A rate limit is the API facing a traffic burst, and retrying later works; a spent quota needs your allowance raised or the window to roll over. The library retries rate limits for you, and server and network failures, but never a spent quota or anything else you sent.

## Other Libraries

There are official InternetData client libraries available for many languages including PHP, Python, Go, Java, Ruby, and many popular frameworks such as Django, Rails, and Laravel. See our GitHub at https://github.com/internetdata for more.

## About InternetData

InternetData: IP and network intelligence databases, published as CSV and MMDB, licensed by contract and downloadable on demand.

[<img src="https://s3.internetdata.io/internetdata-public/brand/mark.svg" alt="InternetData" width="96"/>](https://internetdata.io/)

## License

This project is licensed under the [MIT License](LICENSE).
