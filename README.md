# [<img src="https://s3.internetdata.io/internetdata-public/brand/mark.svg" alt="InternetData" height="28"/>](https://internetdata.io/) InternetData Python Client Library

[![PyPI](https://img.shields.io/pypi/v/internetdata.svg)](https://pypi.org/project/internetdata/)
[![license](https://img.shields.io/pypi/l/internetdata.svg)](LICENSE)

The official Python client library for the [InternetData](https://internetdata.io) API.

It tells you what every InternetData database says about an IP address, an AS or a domain: where it is, who runs it, whether it is a VPN, proxy, Tor node or hosting server, and what it serves. It also downloads the databases your organization is licensed for.

## Getting Started

```bash
pip install internetdata
```

Requires Python 3.11 or newer. Type hints are included, and the package ships `py.typed`.

## Usage

**No API key needed to start.** Unlimited, the free plan, answers `location`, `asn`, `company`, `abuse` and every flag but the VPN, proxy, hosting and CDN ones, limited per address per minute, with a key or without one.

```python
from internetdata import InternetData

client = InternetData()

result = client.lookup("146.70.116.130")
print(result.location.country)    # 'AT'
print(result.asn.name)            # 'M247 Europe SRL'
print(result.company.name)        # who uses the address
```

The client holds an HTTP connection pool, so use it as a context manager, or call `client.close()` when you are done with it:

```python
with InternetData() as client:
    print(client.lookup("146.70.116.130").asn.name)
```

### With an API key

Every paid plan answers every field: the VPN, proxy, hosting and CDN flags, the detail behind each flag, the city, the Whois records and more. The plans differ only in how many lookups they include, and a free account tries every field, 100 lookups a day. Create a key in the [console](https://app.internetdata.io), then pass it in:

```python
import os

client = InternetData(os.environ["INTERNETDATA_API_KEY"])

result = client.lookup("146.70.116.130")
print(result.is_vpn)              # True, on a paid plan
print(result.vpn.provider)        # 'mullvad', on a paid plan
print(result.location.city)       # 'Vienna', on a paid plan
```

### Async

Everything above works the same way under asyncio, with `AsyncInternetData`:

```python
import asyncio
from internetdata import AsyncInternetData

async def main():
    async with AsyncInternetData() as client:
        result = await client.lookup("146.70.116.130")
        print(result.asn.name)   # 'M247 Europe SRL'

asyncio.run(main())
```

### Your own address

```python
result = client.my_ip()
print(result.ip)   # the address we saw this call come from
```

Same answer `lookup` would give for that address, and the same cost against your allowance. It is deliberately not cached: which address you are is the whole question, and a machine that moves between networks would otherwise be told where it used to be.

### Your plan and usage

```python
acct = client.my_entitlement()
print(acct.plan.key)          # starter
print(acct.usage.requests)    # 580
print(acct.usage.window_end)  # when the allowance resets
```

Usage counts against the anniversary of your subscription on a paid plan, not the calendar month and not the billing period, and against the UTC day on the free plan; it is the same number a lookup is gated on. `hard_limit` is `None` on an uncapped plan, which is not the same as zero.

Both are on the async client too: `await client.my_ip()` and `await client.my_entitlement()`.

### Batch lookup

Look up as many addresses as you like at once. Bogons and cached answers are handled locally, and everything else goes to the batch endpoint in chunks of up to 1000 addresses, in parallel. The batch endpoint needs a paid plan:

```python
results = client.lookup_batch(["146.70.116.130", "8.8.8.8", "1.1.1.1"])

for ip, result in results.items():
    if isinstance(result, Exception):
        print(f"{ip}: {result}")
        continue
    print(f"{ip}: {result.is_vpn}")
```

Results are keyed by address, in the order you first listed each one, so duplicates in your list collapse into a single entry and one address failing never loses the rest: it carries its error as its value, with the status the API would have given that address on its own.

How many chunks are in flight at once, how many times a failed chunk is retried and how long each request may take are configurable per call:

```python
results = client.lookup_batch(many_ips, concurrency=4, retries=4, timeout=30)
```

### Caching

Answers are cached by default, so repeat lookups of the same address are free:

```python
client = InternetData()

result = client.lookup("146.70.116.130")
print(result.asn.name)    # API request

result2 = client.lookup("146.70.116.130")
print(result2.asn.name)   # no API request, result was cached
```

You can change the default cache variables (max size, TTL in seconds, etc) on initialization, or even disable it:

```python
client = InternetData(cache_max_size=50_000, cache_ttl=6 * 60 * 60)
client_no_cache = InternetData(cache=False)
```

### Private and reserved addresses

Private, loopback, link-local, documentation and multicast addresses (and their IPv6 equivalents, including the 6to4 and Teredo ranges) are in no database. The library answers them locally, so they cost no request and no quota:

```python
result = client.lookup("192.168.1.1")
result.is_bogon   # True
result.is_vpn     # False
```

The answer has the shape the API gives a bogon on a paid plan, whatever your plan, so don't read your plan off it. The check is available on the client, which is handy when your inputs are addresses anyway:

```python
client.is_bogon("10.0.0.1")   # True
client.is_bogon("8.8.8.8")    # False
```

It is also importable on its own, if you want it without a client:

```python
from internetdata import is_bogon

is_bogon("10.0.0.1")   # True
```

### AS and domain lookups

```python
asn = client.lookup_asn(9009)
print(asn.name, asn.registry)    # M247 Europe SRL ripe

domain = client.lookup_domain("example.com")
print(domain.is_registered, domain.has_mx)   # True True
```

On a paid plan an AS answer also carries its Whois record, its counts and every prefix it announces, and a domain answer its DNS records, its organization's IP ranges and `is_disposable`. Neither is cached, and neither goes through the batch. `lookup` takes addresses alone, and refuses an AS or a domain with a `bad_request` before sending anything.

### Errors

Failures raise an `InternetDataError` carrying a `kind` and a `retryable` flag:

```python
from internetdata import InternetDataError

try:
    client.lookup("1.1.1.1")
except InternetDataError as err:
    print(err.kind, err.retryable, err.message)
```

`kind` is one of `bad_request`, `unauthorized`, `forbidden`, `rate_limited`, `quota_exceeded`, `server_error` or `network`. `message` is the API's own: a lookup's error message, or a database call's result code, passed through as it was sent, so you can switch on `NOT_LICENSED` against `LICENSE_EXPIRED` without reading the status.

A request that runs past its `timeout` fails with `network`, and is retried like any other network failure. The default is 30 seconds per attempt, body included, so a retried call can take longer in total. A database transfer is exempt, so `download` and `download_bytes` are never cut off part way through a large file. Set it on the client, or on a single `lookup`, `lookup_asn`, `lookup_domain`, `my_ip`, `my_entitlement`, `lookup_batch`, `oauth` or `database` call (transfers aside), in seconds:

```python
client = InternetData(timeout=10)
result = client.lookup("146.70.116.130", timeout=2)
```

`None` means no bound on the client, and the client's own on a call. Anything else that is not a number greater than 0 raises `ValueError` where it is set, before any request is made.

**Changed in 2.1.0:** the default was 10 seconds, and it bounded each read of a response rather than the whole attempt, so a response trickling in slowly could run past it for as long as the server kept sending.

**Changed in 2.2.0:** a timeout of 0 or less, NaN or a string used to be accepted, and failed every call.

Note that `rate_limited` and `quota_exceeded` both arrive as HTTP 429 and are not the same thing. A rate limit carries `Retry-After`, and retrying after it works: Unlimited's per-minute limit is one. A spent quota needs your allowance raised or the window to roll over. The library retries rate limits for you, but not a spent quota, and nothing else you sent either.

### Database downloads

Every database call needs an API key carrying the `db.download` scope. Create one in the console, then:

```python
import os
from internetdata import InternetData

client = InternetData(os.environ["INTERNETDATA_API_KEY"])

for family in client.database.list():
    print(family.base, family.standing, [v.id for v in family.versions])
```

#### The catalog

`list` answers database FAMILIES. A license is held against a family, while a download names a specific version, so the IDs the other calls take come from each family's `versions`:

```python
for family in client.database.list():
    if family.standing != "licensed":
        continue
    for version in family.versions:
        print(version.id, version.formats)   # 'bogon_ip_v1' ('csvgz', 'mmdb')
```

`standing` is `licensed`, `expired` or `unlicensed`, and `license_type` is what your license lets you do with the data (`evaluation`, `standard`, `redistribute`, or `None` when there is no license). A family you have never bought is still listed, as `unlicensed`, so you can see what else exists.

A rolling license also carries `renews_at`, when it next renews, and `notice_due_at`, the last day you can give notice of non-renewal for that term. Both are `None` when there is no license, when it has no defined term, or when `expires` sets a hard stop instead. `DATABASE_FORMATS`, `STANDINGS` and `LICENSE_TYPES` hold the published values at runtime, for checking one that came from a flag or a form before you make a call.

#### What is inside a build

`metadata` is cheap enough to poll. It answers when the build was generated, how many rows it has, its columns and a few real rows, and the size of each format in bytes, all without moving the file:

```python
meta = client.database.metadata("bogon_ip_v1")

print(meta.updated)                  # datetime.date(2026, 9, 4)
print(meta.entries)                  # 1234
print(meta.size["csvgz"])            # 760
print([c.name for c in meta.schema["csvgz"]])
```

Checking `size` before a download is worth the round trip: the catalog spans a few hundred bytes to several gigabytes.

#### Downloading

Three ways, depending on what you want to do with the bytes:

```python
url = client.database.download_url("bogon_ip_v1", "csvgz")
raw = client.database.download_bytes("bogon_ip_v1", "csvgz")
written = client.database.download("bogon_ip_v1", "mmdb", "./bogon_ip_v1.mmdb")
```

`download_url` hands back a time-limited link straight to object storage. It carries its own signature and none of your API key, so you can pass it to `curl`, a job runner or anything else that speaks HTTP. The link authorizes the START of a transfer, so one already running is not cut off when it lapses.

`download` streams to a file, so nothing larger than a chunk is ever held in memory. The bytes land in a neighboring `.part` file that is moved into place only once the whole transfer has arrived, so a failed refresh leaves the copy you already had untouched. `download_bytes` holds the whole file in memory, so reach for it only at the small end of the catalog.

Either way a short transfer fails rather than handing you a truncated file, and the key is never sent to object storage.

Each of the three downloads the build that is live unless you name one. A `database.updated` webhook names the build it announces and carries its `sha256`, so a receiver that downloads after the next publish asks for that build to get the file the hash is of:

```python
client.database.download("vpn_ip_v1", "mmdb", "./vpn_ip_v1.mmdb", build=event["data"]["build"])
```

A build is kept 7 days. Past that the call raises `bad_request` with the message `BUILD_GONE`, and downloading without `build` fetches the live one.

Verify what you fetched against the published digests:

```python
import hashlib

digests = client.database.checksums("bogon_ip_v1", "csvgz")
assert hashlib.sha256(raw).hexdigest() == digests["sha256"]
```

#### Download history

`downloads` answers your organization's recent attempts, newest first, refusals included. A denial is what answers "it stopped working", and its absence answers nothing:

```python
for attempt in client.database.downloads(limit=20):
    print(attempt.created, attempt.dataset_id, attempt.outcome, attempt.http_status)
```

From 2.3.0, `list`, `metadata`, `checksums`, `downloads` and `download_url` each take a keyword-only `timeout` in seconds, bounding each attempt at that one call in place of the client's; `None` there means the client's own rather than no bound. `download` and `download_bytes` deliberately take none and raise `TypeError` if handed one, rather than accepting it and quietly doing nothing: a transfer runs to gigabytes and minutes, so any bound that suits a JSON call would abandon a healthy download. `download_url` does take one, because minting the link is an ordinary API request - it bounds that request, not whatever you do with the link afterwards:

```python
catalog = client.database.list(timeout=2)
```

InternetData's database API has no quota, so you won't see `quota_exceeded` from it.

### Sign in with OAuth (device flow)

A program running on someone's own machine can let them sign in with a browser and pick one of their API keys, instead of asking them to paste it:

```python
from internetdata import InternetData

with InternetData() as signin:
    device = signin.oauth.device_authorization(
        "your-client-id", scope="account.read apikeys.read apikeys.reveal"
    )
    print(f"Open {device.verification_uri} and enter {device.user_code}")
    tokens = signin.oauth.poll_device_token("your-client-id", device)

if tokens.apikey is None:
    raise SystemExit("No API key was picked")
client = InternetData(tokens.apikey)
```

A refusal raises `OauthAccessDeniedError` and a code that ran out raises `OauthExpiredTokenError`, and client IDs are issued on request from support@internetdata.io. `client.oauth.revoke("your-client-id", tokens.refresh_token)` signs the machine out.

### Sign in with OAuth (authorization code)

An app that can take a browser redirect signs the person in there instead, with a PKCE pair made for that one sign-in:

```python
from internetdata import InternetData

signin = InternetData()
redirect_uri = "http://127.0.0.1:8765/callback"
pkce = signin.oauth.create_pkce()

url = signin.oauth.authorization_url(
    "your-client-id", redirect_uri, pkce.challenge, scope="apikeys.use", state="your-state"
)
# Open url in the browser. Its redirect to redirect_uri carries code and state.
tokens = signin.oauth.exchange_authorization_code("your-client-id", code, pkce.verifier, redirect_uri)
```

Check that `state` came back as you sent it before you exchange `code`, which works once. The client ID can also be the https URL of a client metadata document your app serves, and such an app is never handed a key, so `tokens.apikey` stays `None`.

### Register a client

An app with no client ID, and no client metadata document to use as one, registers itself, then signs in with the `client_id` it gets back as the client ID for `authorization_url` and `exchange_authorization_code`:

```python
client = InternetData()
registration = client.oauth.register(
    ["http://127.0.0.1:8765/callback"], client_name="Your App"
)
```

Each redirect URI must be https on a public host name, or http on a loopback address, which then matches any port. Nothing is kept until a person approves the client, so an app with no client ID saved can simply register again.

### Fields your plan does not include

Unlimited leaves out the VPN, proxy, hosting and CDN flags, the detail behind every flag but Tor's and relay's, the city and region, the Whois records and the hosted domains; a free-plan key's answer carries `trial_expired`, true once its daily trial is spent. Those are `None` when your key does not include them, which means "not in your plan" rather than "checked, and no", inside `location`, `asn`, `company` and `abuse` too.

```python
result.flagged("is_hosting")   # False rather than None on a plan without it
result.is_hosting is None      # True on Unlimited: not in your plan
result.location.city is None   # True on Unlimited
result.trial_expired is True   # a free-plan key's daily trial is spent
```

## Other Libraries

There are official InternetData client libraries available for many languages including PHP, Python, Go, Java, and Ruby. See our GitHub at https://github.com/internetdata for more.

## About InternetData

Geolocation, anonymity, ownership and network data for IP addresses, AS numbers and domains, through an API or as database files you download and query yourself.

[<img src="https://s3.internetdata.io/internetdata-public/brand/mark.svg" alt="InternetData" height="64"/>](https://internetdata.io/)

## License

This project is licensed under the [MIT License](LICENSE).
