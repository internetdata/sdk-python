# Changelog

What each release changed for you, newest first. Each line is a commit's summary, linked to its full description and diff. Releases before 2.4.1 are described by their release commits.

## 2.7.4 - 2026-10-16

### Fixes

- Re-pin the spec to 2026.10.15: three descriptions in US spelling ([`a91d87c`](https://github.com/internetdata/sdk-python/commit/a91d87c2032980cb1900b3d91782963656d0a960))
- Drop every trailing slash from the base URL, and refuse a key outside ASCII ([`8c75289`](https://github.com/internetdata/sdk-python/commit/8c75289e48cb40e05d63ffb21a9866ed7dbc7b9f))

## 2.7.3 - 2026-10-13

### Fixes

- Re-pin the spec to 2026.10.13: Open databases come with a license ([`56c0eb8`](https://github.com/internetdata/sdk-python/commit/56c0eb82adcaa594c1cb48e4aa326842cbf4489c))

## 2.7.2 - 2026-10-12

### Fixes

- Read Retry-After as whole seconds or an HTTP date, nothing else ([`60fb07c`](https://github.com/internetdata/sdk-python/commit/60fb07ce9bc3606d59c15a73a3da8dc2516313a6))
- Trim the API key, and refuse one holding a control character ([`ef12b72`](https://github.com/internetdata/sdk-python/commit/ef12b72bf154034ebb78d52fca105f42cdfdcc83))
- Fail an answer missing what it must hold, and classify a 4xx by status ([`0a6c327`](https://github.com/internetdata/sdk-python/commit/0a6c3275277a0391e63af6ac3d05f95ff58b8d2d))

## 2.7.1 - 2026-10-10

### Fixes

- Re-pin the spec to 2026.10.09: rotating a key needs apikeys.reveal ([`b4fe760`](https://github.com/internetdata/sdk-python/commit/b4fe7609aae6f68ab1e3fc15f25cdd507ccfc410))

## 2.7.0 - 2026-10-09

### Features

- Re-pin the spec to 2026.10.08, adding the Open databases' open flag ([`3df886d`](https://github.com/internetdata/sdk-python/commit/3df886df5444af30fb0299ccbd3d83ebaea61b6b))

## 2.6.2 - 2026-10-04

### Fixes

- Re-pin the spec to 2026.10.03: metadata needs no license ([`9090358`](https://github.com/internetdata/sdk-python/commit/909035886065bde6b826726c6a8b585012f6692b))

## 2.6.1 - 2026-09-30

### Fixes

- Bound the poll's wait, a long Retry-After and a timeout past 292 years ([`4475521`](https://github.com/internetdata/sdk-python/commit/4475521e926427265242b126b89f28971ad7f634))

## 2.6.0 - 2026-09-29

### Features

- Add the authorization code sign-in, with PKCE ([`61c8ac2`](https://github.com/internetdata/sdk-python/commit/61c8ac22fc84753b44e9accd2a4009ad26601e25))

## 2.5.0 - 2026-09-27

### Features

- Re-pin the spec to 2026.09.26, adding its evaluation-sample fields ([`5b9d017`](https://github.com/internetdata/sdk-python/commit/5b9d017980ee9748a64e8940103418e612df567e))

## 2.4.1 - 2026-09-22

### Fixes

- Stop explaining in the docs how a private database is hidden ([`fd9463a`](https://github.com/internetdata/sdk-python/commit/fd9463a130518311105027e1c87b535069429590))
