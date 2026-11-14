# Changelog

What each release changed for you, newest first. Each line is a commit's summary, linked to its full description and diff. Releases before 2.4.1 are described by their release commits.

## 2.12.0 - 2026-11-14

### Features

- Add the framework middleware core ([`5ccfa93`](https://github.com/internetdata/sdk-python/commit/5ccfa939c8435a4dba6af3bd1710dc49b9d9a77c))

## 2.11.0 - 2026-11-13

### Features

- Re-pin the spec to 2026.11.13: the lookups and the entitlement ([`47bd0f3`](https://github.com/internetdata/sdk-python/commit/47bd0f3c1531efd004f6e1cc1b99fd5bc3fff9e4))
- Look up addresses, ASes and domains, on api.internetdata.io by default ([`56b3434`](https://github.com/internetdata/sdk-python/commit/56b343420d6f769306d98a36d4bd9887f54a592e))
- Name this library in every request's User-Agent ([`74d7001`](https://github.com/internetdata/sdk-python/commit/74d70013045309845102dcd80fa6bd31c147709c))
- Re-pin the spec: a detail object requires no member ([`75beb71`](https://github.com/internetdata/sdk-python/commit/75beb712c8c76d2a8541e51359ea44bfcb7715d6))
- Refuse a lookup of anything but an IP address before sending it ([`86da8e8`](https://github.com/internetdata/sdk-python/commit/86da8e884d645049deaf59b6cee01dad97183212))

## 2.10.1 - 2026-11-09

### Fixes

- Re-pin the spec to 2026.11.08: the token and revoke descriptions ([`29bc11a`](https://github.com/internetdata/sdk-python/commit/29bc11ac7a3861021b2ccd23293504c2d5556443))

## 2.10.0 - 2026-11-07

### Features

- Download a named build: download_url, download and download_bytes take build ([`a3b2622`](https://github.com/internetdata/sdk-python/commit/a3b262202a599036a5471f8a0973afb9b93de087))

## 2.9.6 - 2026-11-06

### Fixes

- End a device poll for a NaN lifetime, and once a wait hits the deadline ([`856adea`](https://github.com/internetdata/sdk-python/commit/856adea678d75c23ec24567500c1ac8975d2c6a0))

## 2.9.5 - 2026-11-06

### Fixes

- Re-pin the spec to 2026.11.05: the download's build parameter ([`e3d517c`](https://github.com/internetdata/sdk-python/commit/e3d517c301100738ea7f3082da4abf2dd89c3b1d))

## 2.9.4 - 2026-11-03

### Fixes

- Re-pin the spec to 2026.11.02: ID and IDs in its descriptions ([`3eb09a6`](https://github.com/internetdata/sdk-python/commit/3eb09a6c5c375560eaa3297d85053ab527d51ec8))
- Write ID and IDs in prose, never id or ids ([`6f2e980`](https://github.com/internetdata/sdk-python/commit/6f2e9804321aa68f2818fcc651f355adecf532bd))

## 2.9.3 - 2026-10-25

### Fixes

- Refuse a retry count that is not a whole number from 0 ([`5a29d59`](https://github.com/internetdata/sdk-python/commit/5a29d590e1c8a5396ec48a18c7c7813b1ef09f0c))
- Retry a database answer whose dates or members break the spec ([`496e1e1`](https://github.com/internetdata/sdk-python/commit/496e1e1fc11e15cc9d472d7f23651b52a99cb63c))

## 2.9.2 - 2026-10-21

### Fixes

- Re-pin the spec to 2026.10.21: a 403 for a refused address ([`0a1c67f`](https://github.com/internetdata/sdk-python/commit/0a1c67f54654cf3353d60a4e651c19790ffa48b1))

## 2.9.1 - 2026-10-18

### Fixes

- Re-pin the spec to 2026.10.18: client_id_issued_at is int64 ([`8469fd7`](https://github.com/internetdata/sdk-python/commit/8469fd70636255c8d2f24f9984ee7854d600d968))

## 2.9.0 - 2026-10-18

### Features

- Add oauth.register, for RFC 7591 dynamic client registration ([`5b107e1`](https://github.com/internetdata/sdk-python/commit/5b107e12907ec5cb58eaeb7ff4e0d48a023330ca))

## 2.8.0 - 2026-10-17

### Features

- Re-pin the spec to 2026.10.16: dynamic client registration ([`f5844ce`](https://github.com/internetdata/sdk-python/commit/f5844cef95abc21e261c42695512a9ae3e57f001))

## 2.7.5 - 2026-10-16

### Fixes

- Retry a database answer whose member has the wrong type ([`b800390`](https://github.com/internetdata/sdk-python/commit/b800390f6f5d2c4ebaa4c518fa47e132093a15d9))

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
