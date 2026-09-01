# Jobvite Client Contract - the buildable subset

**Compiled:** 2026-08-27 by `jobvite-api-research`. Companion to [`JOBVITE-API.md`](JOBVITE-API.md), which is the survey; this is the implementable contract.

**Scope:** the five endpoints with enough evidence to code against - `GET /api/v2/candidate`, `POST /api/v2/candidate`, `GET /api/v2/job`, `POST /api/v2/task`, and `GET /v1/jobFeed`. Everything else in the Jobvite surface is a route name without a contract and is deliberately out of scope (see `JOBVITE-API.md` §11).

---

## Table of Contents

1. [How to read this document](#1-how-to-read-this-document)
2. [Transport contract](#2-transport-contract)
3. [The error-detection rule](#3-the-error-detection-rule)
4. [Pagination contract](#4-pagination-contract)
5. [`GET /api/v2/candidate`](#5-get-apiv2candidate)
6. [`POST /api/v2/candidate`](#6-post-apiv2candidate)
7. [`GET /api/v2/job`](#7-get-apiv2job)
8. [`POST /api/v2/task`](#8-post-apiv2task)
9. [`GET /v1/jobFeed`](#9-get-v1jobfeed)
10. [Fixtures: recorded transport](#10-fixtures-recorded-transport)
11. [Fixtures: synthetic success bodies](#11-fixtures-synthetic-success-bodies)
12. [Documented negative: the OPTIONS `Allow` header is a decoy](#12-documented-negative-the-options-allow-header-is-a-decoy)
13. [Day-one credential checklist](#13-day-one-credential-checklist)

---

## 1. How to read this document

Every contract statement carries a provenance marker. The distinction that matters most:

| Marker | Meaning | Safe to code against? |
|---|---|---|
| `[RECORDED]` | I sent this exact request on 2026-08-27 and this is the response, byte for byte. | Yes - this is ground truth. |
| `[OFFICIAL]` | From Jobvite's own artifacts (the archived v1 PDF, or `Jobvite/APIConnectorSamples`). | Yes, subject to age. |
| `[INFERRED]` | Read off a working third-party client. Corroboration, not documentation. | Code against it, but treat a mismatch as *expected*, not exceptional. |
| `[ASSUMED]` | My reasoning filling a gap. Nobody has observed this. | **No.** Gate it behind the day-one checklist (§13). |

### The one thing to understand before writing any code

**I hold no Jobvite credential. Not a single 2xx success body in this document was observed.** Every success shape here is reconstructed from third-party field mappings. This has a hard consequence for the fixture set:

* **§10 fixtures are real.** Recorded error transport, exact bytes. Use them as-is.
* **§11 fixtures are synthetic.** They are my best reconstruction, shaped to match the field names and types that working clients actually read. **They are hypotheses in JSON form.**

A test suite that passes only against §11 proves the client is self-consistent, not that it speaks Jobvite. That is the classic fakes-are-green failure. §13 exists to close it the day a credential lands, and **no success-path fixture should be trusted until the corresponding checklist row is ticked.**

---

## 2. Transport contract

`[RECORDED]` Base URLs:

| Purpose | URL |
|---|---|
| v2 | `https://api.jobvite.com/api/v2` |
| v1 | `https://api.jobvite.com/v1` |

There is no sandbox. `api-stg.jobvite.com` and `app-stg.jobvite.com` both fail DNS resolution as of 2026-08-27. **There is no environment in which a write can be safely rehearsed.**

### 2.1 Authentication

`[INFERRED]` v2 request headers - this is the current mechanism and the only one we implement:

```
x-jvi-api: <api_key>
x-jvi-sc:  <api_secret>
Accept: application/json
```

`[OFFICIAL]` v1 (`/v1/jobFeed`) takes credentials as **query parameters** instead: `api`, `sc`, `companyId`. Note the parameter naming is inconsistent across v1 - `/v1/candidate` uses `secret` where `/v1/jobFeed` uses `sc`.

**Rules for our implementation:**
1. Credentials go in headers for every v2 call. Never build a URL containing a secret, even though Jobvite's own sample code does.
2. `GET /v1/jobFeed` is the one endpoint that structurally requires the secret in the query string. Its URL must be treated as sensitive: never log it whole, never include it in an error message, redact `sc=` before any log line is emitted.
3. `[ASSUMED]` Whether v2 still accepts query-string auth is **unknown** - a bogus header pair and a bogus query pair return byte-identical 401s, so no probe can distinguish them. We do not rely on it either way.

### 2.2 Request headers to send

`[ASSUMED]` `Content-Type: application/json` on POST bodies, matching Jobvite's own Java sample (`con.setRequestProperty("Content-Type", "application/json; utf-8")`).

### 2.3 Response headers

`[RECORDED]` Responses carry `Server: Jobvite`, `X-JOBVITE-PROXY: true`, `Access-Control-Allow-Origin: *` (v2) or `https://app.jobvite.com` (v1 jobFeed), `Pragma: no-cache`, `Cache-Control: private, no-cache, no-store, max-age=0`, and four `AWSALBAPP-*` cookies.

**`[RECORDED]` There is no rate-limit header of any kind.** No `X-RateLimit-*`, no `RateLimit-*`, no `Retry-After`. There is nothing to parse and nothing to feed a backoff calculation - our throttling must be entirely client-side and configuration-driven. See `JOBVITE-API.md` §14.

`[RECORDED]` The `Set-Cookie: AWSALBAPP-*` values are all the literal string `_remove_`. **Clear the cookie jar after every request.** The API is credential-authenticated per request and there is no session to carry, and the HTTP client's default is to persist and resend what Jobvite sets - measured on the pinned `httpx2` 2.12.0: a bare `AsyncClient` stores both `AWSALBAPP-*` values and sends them back on the next request. Disabling that is an explicit step, not the result of leaving cookie handling alone (ADR-0022). The `[RECORDED]` observation above is untouched; only the instruction derived from it changes.

---

## 3. The error-detection rule

This is the most important behavioural contract in the document, because getting it wrong turns an auth failure into a silent empty result.

### 3.1 The trap

`[RECORDED]` `GET https://api.jobvite.com/api/v1/candidate` returns:

```
HTTP/1.1 200
Content-Type: application/json;charset=utf-8

{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}
```

**HTTP 200. Body says 401.** A client that branches on `response.status_code` alone treats this as success, then reads `data["candidates"]`, gets a `KeyError`, and - if that is caught anywhere broad - reports "0 candidates" for what is actually a rejected credential. A wrong zero that explains itself.

### 3.2 The rule

```python
def parse_jobvite_response(http_status: int, body_bytes: bytes) -> dict:
    """Decide success/failure for a Jobvite v2 response.

    The HTTP status is NOT authoritative: api.jobvite.com has been observed
    returning HTTP 200 with a body carrying {"status": {"code": 401}}.
    The body's status.code wins whenever it is present.
    """
    try:
        payload = json.loads(body_bytes)
    except ValueError:
        # v1 emits plain text; some errors emit an HTML error page.
        raise JobviteTransportError(http_status, body_bytes[:500])

    status = payload.get("status")
    if isinstance(status, dict) and "code" in status:
        code = status["code"]
        if code >= 400:
            raise JobviteApiError(
                code=code,
                messages=status.get("messages", []),
                http_status=http_status,
            )
        # A status block with a <400 code has never been observed; see below.

    if http_status >= 400:
        raise JobviteApiError(code=http_status, messages=[], http_status=http_status)

    return payload
```

**The invariant, stated for the test that must enforce it:** *a response is successful only if the body carries no `status.code >= 400` **and** the HTTP status is < 400.* Both conditions, every time.

`[ASSUMED]` I have never seen a success body, so **I do not know whether success responses include a `status` block at all.** The code above tolerates both (a `status` block with a code under 400 falls through to success). Checklist §13 row 1 settles it.

### 3.3 Error shapes to handle

| Shape | Content-Type | Seen on | Provenance |
|---|---|---|---|
| `{"status":{"code":N,"messages":[...]}}` | `application/json` | all v2 routes | `[RECORDED]` |
| Plain text `Invalid api/secret. Try again with a valid api/secret` | *(none sent)* | `/v1/*` | `[RECORDED]` |
| Tomcat HTML error page | `text/html` | `POST /api/v2/task` with a malformed envelope | `[RECORDED]` |
| HR-XML `<Errors><Error code="N">...</Error></Errors>` | `application/xml` | `/v1/candidate` | `[OFFICIAL]` |

**Four different error encodings across one API.** The parser must not assume JSON. `[RECORDED]` the v1 jobFeed 401 sends **no `Content-Type` header at all**, so content-type sniffing cannot be the only dispatch either.

### 3.4 Known codes

`[RECORDED]` `401` = `"Invalid api/secret. Try again with a valid api/secret"` - bad or missing credentials.
`[RECORDED]` `404` = `"Invalid URL Cannot find API."` - the route does not exist. Note this is **route-level**, not record-level: it does not mean "candidate not found".
`[INFERRED]` `400`, `404`, `409` are handled on the candidate-create path by a production integration; `409` is presumably a duplicate candidate.
`[ASSUMED]` **A record-level "not found" shape is unknown.** We do not know what `GET /api/v2/candidate?candidateId=<nonexistent>` returns - an empty `candidates` array, a 404 body, or something else. Checklist §13 row 4.

Full v1 numeric catalogue (100-108, 201-208) is in `JOBVITE-API.md` §15.2. `[ABSENT]` There is no v2 equivalent.

---

## 4. Pagination contract

`[INFERRED]` Offset-based on both list endpoints. No cursor, no `next` link, no `Link` header anywhere.

| Parameter | Meaning | Limit |
|---|---|---|
| `start` | offset into the result set | see the base ambiguity below |
| `count` | page size | **max 500** on `/api/v2/candidate` and `/api/v2/job`; **max 1000** on `/v1/jobFeed` |

### 4.1 The `start` base is genuinely unresolved

`[INFERRED]` Three working clients disagree:

| Client | Behaviour |
|---|---|
| `kippnorcal/jobvite` (Python) | `start = 0`, then `start += batch_size` |
| `atipica/jobvite_api` (Ruby) | `(page - 1) * per_page`, i.e. 0 for the first page |
| `frague/rm` (TypeScript) | `if (start < 1) start = 1` - explicitly forces 1-based |
| `[OFFICIAL]` Data Services v3.5 | **1-based.** The document states the default start index is 1, and its worked example retrieves records 501-1000 with `start=501&count=500` - i.e. `start` names the first record wanted, not an offset before it |

**Failure mode either way:** if the API is 1-based and we send 0, the first page may return the first record twice or the server may reject it; if it is 0-based and we send 1, we silently skip record one. **A silently skipped record is the worse outcome and would not surface in any test built on §11 fixtures.**

`[ASSUMED]` **Recommended interim:** follow the official v1 documentation and use **1-based** `start`, because it is the only statement from Jobvite itself, and the two clients that use 0 are both consistent with a server that clamps `0 → 1`. Gate on checklist §13 row 2 before trusting any full-catalogue sync.

### 4.2 Termination

`[INFERRED]` Both working clients stop when `len(items) < count` rather than trusting `total`:

```python
while True:
    page = get(endpoint, params={**filters, "start": start, "count": count})
    items = page[items_key]          # "candidates" or "requisitions"
    yield from items
    if len(items) < count:
        break
    start += count
```

`[INFERRED]` `total` is present in list responses and is the full result-set size - `atipica` fetches `count=5` purely to read it. **Use `total` for reporting, never as the loop's termination condition:** if `total` is a filtered-set count and pages are unfiltered (or the set mutates mid-scan), a `total`-driven loop truncates or spins.

`[ASSUMED]` No stable-sort guarantee exists (no sort parameter is documented anywhere), so a long paged scan over a mutating result set may duplicate or skip records. For any sync we care about, prefer a bounded date window over a full-catalogue walk.

---

## 5. `GET /api/v2/candidate`

`[RECORDED]` route exists (401 without credentials). `[INFERRED]` everything below.

### Request

```http
GET /api/v2/candidate?start=1&count=500&datestart=2026-01-01&dateend=2026-08-27&dateFormat=yyyy-MM-dd HTTP/1.1
Host: api.jobvite.com
x-jvi-api: <api_key>
x-jvi-sc: <api_secret>
Accept: application/json
```

| Parameter | Type | Req | Notes | Provenance |
|---|---|---|---|---|
| `start` | int | no | offset; base disputed (§4.1) | `[INFERRED]` |
| `count` | int | no | page size, **max 500** | `[INFERRED]` |
| `candidateId` | string | no | fetch one candidate | `[INFERRED]` |
| `applicationId` | string | no | with `candidateId`, resolves one application | `[INFERRED]` |
| `datestart` | date | no | lower bound on last-updated | `[INFERRED]` |
| `dateend` | date | no | upper bound on last-updated | `[INFERRED]` |
| `dateFormat` | string | no | e.g. `yyyy-MM-dd`. **camelCase on v2**, lowercase `dateformat` on v1 | `[INFERRED]` |
| `wflowstate` | string | no | workflow-state filter. Two clients left it as an unimplemented TODO, so this is v1 continuity, **not observed working on v2** | `[ASSUMED]` |
| `format` | string | no | `atipica` sends `json` | `[INFERRED]` |

### Response field map

`[INFERRED]` Envelope: `{"total": <int>, "candidates": [...]}`

| Path | Type | Notes |
|---|---|---|
| `total` | int | full result-set size |
| `candidates[].eId` | string | **candidate id**, ~8 alphanumeric chars. Lowercase `eId` on reads |
| `candidates[].firstName` | string | |
| `candidates[].lastName` | string | |
| `candidates[].email` | string | may be `null` - a mapping guards `email != null` |
| `candidates[].mobile` | string | may be empty string |
| `candidates[].workPhone` | string | may be empty string |
| `candidates[].homePhone` | string | may be empty string |
| `candidates[].workExperience` | array | shape unknown |
| `candidates[].education` | array | shape unknown |
| `candidates[].application` | object | single object, not an array, in the observed mapping |
| `candidates[].application.job.eId` | string | the job this application is against. A production integration marks this read `failSilently: true` because it **may be null** |

**Normalisation warning:** `[INFERRED]` the phone fields are distinguished only by name (`workPhone`/`homePhone`/`mobile`) and empty strings are used rather than nulls. Treat `""` and `null` identically at the boundary.

---

## 6. `POST /api/v2/candidate`

Creates a candidate **and** an application in one call. `[RECORDED]` route exists. `[INFERRED]` body and response, from a production write integration.

**This is the only write in scope, it has no sandbox, and it creates real records in a real ATS.** Treat it accordingly: it must be gated behind an explicit non-default opt-in, never invoked by a read-shaped tool, and never retried blindly on an ambiguous failure (a timeout after a successful create would duplicate a candidate; note `409` appears in the handled set and is plausibly the duplicate signal).

### Request

```http
POST /api/v2/candidate HTTP/1.1
Host: api.jobvite.com
x-jvi-api: <api_key>
x-jvi-sc: <api_secret>
Content-Type: application/json
```
```json
{
  "candidate": {
    "email": "<email>",
    "firstName": "<first>",
    "lastName": "<last>",
    "mobile": "<phone>",
    "sendEmail": false,
    "application": {
      "jobEId": "<jobEId>",
      "sourceType": "CareerSite",
      "source": "<source name>",
      "resume": {
        "name": "<filename.pdf>",
        "contentByteArray": "<base64>",
        "format": "ByteArray"
      }
    }
  }
}
```

| Field | Req | Notes | Provenance |
|---|---|---|---|
| `candidate.firstName` | **yes** | enforced as a precondition by the calling integration | `[INFERRED]` |
| `candidate.lastName` | **yes** | as above | `[INFERRED]` |
| `candidate.email` | **yes** | as above | `[INFERRED]` |
| `candidate.mobile` | no | | `[INFERRED]` |
| `candidate.sendEmail` | no | boolean. **Sends mail to a real candidate** - default it to `false` and require an explicit caller opt-in | `[INFERRED]` |
| `candidate.application.jobEId` | no* | required in practice to attach the application to a job | `[INFERRED]` |
| `candidate.application.sourceType` | no | observed literal: `"CareerSite"` | `[INFERRED]` |
| `candidate.application.source` | no | free-text source name | `[INFERRED]` |
| `candidate.application.resume` | no | inline base64; there is **no separate attachment endpoint** (`/api/v2/attachment` 404s) | `[INFERRED]` |
| `...resume.format` | with resume | observed literal: `"ByteArray"` | `[INFERRED]` |

`[INFERRED]` The observed integration only attaches a resume when the content type is `application/pdf` and the encoding is base64. Whether other types are accepted is unknown.

### Response

`[INFERRED]` `HTTP 201`:

| Path | Meaning |
|---|---|
| `application.candidate.EId` | the new candidate id |
| `application.EId` | the new application id |

**`[INFERRED]` Casing trap: the write response uses capital `EId`; reads use lowercase `eId`.** Both refer to the same identifier space. Any shared model must normalise, and a test must pin this asymmetry or the next refactor will "fix" it into a bug.

`[INFERRED]` Handled error statuses: `400`, `404`, `409`.

---

## 7. `GET /api/v2/job`

`[RECORDED]` route exists. `[INFERRED]` below.

### Request

| Parameter | Type | Notes | Provenance |
|---|---|---|---|
| `ids` | string | fetch specific jobs: `?ids=<jobEId>`. Whether it accepts a comma-separated list is **unknown** | `[INFERRED]` |
| `start` | int | offset (§4.1) | `[INFERRED]` |
| `count` | int | page size, max 500 | `[INFERRED]` |
| date filters | - | an integration README says "date-filtered GET" is supported but **does not name the parameters**. `datestart`/`dateend` by analogy with `/candidate` is `[ASSUMED]` and unverified | `[ASSUMED]` |

### Response field map

`[INFERRED]` Envelope: `{"total": <int>, "requisitions": [...]}` - note the collection key is **`requisitions`**, not `jobs`. (`jobs` is the v1 jobFeed key. Same domain object, two names, two versions.)

| Path | Type | Notes |
|---|---|---|
| `requisitions[].eId` | string | job id |
| `requisitions[].title` | string | |
| `requisitions[].description` | string | **may be `null` or `""`** - the observed mapping falls back to `title` |
| `requisitions[].applyLink` | string | public apply URL |
| `requisitions[].jobState` | string | see enum below |
| `requisitions[].department` | string | |
| `requisitions[].category` | string | one mapping uses `category` as the department field - the two are **not** reliably distinct |
| `requisitions[].locations` | array | may be absent; objects carry `city`, `state`, `country` |
| `requisitions[].lastUpdatedDate` | int | **epoch milliseconds** |
| `requisitions[].sentDate` | int | **epoch milliseconds** |

**`[INFERRED]` Date asymmetry to encode once and test:** requests take **formatted date strings** (`yyyy-MM-dd`); responses return **epoch milliseconds**. Anything reading a timestamp back out must convert.

`[INFERRED]` `jobState` observed values - a production mapping switches on exactly these strings:

```
Open | Closed | Filled | On Hold | Awaiting Approval | Approved | Rejected | Retracted
```

`[ASSUMED]` This list is what one integration handled, **not a documented enum**. Any mapping we write must have a default branch; an unrecognised state must pass through rather than raise or silently become `null`.

---

## 8. `POST /api/v2/task`

`[OFFICIAL]` The only in-scope endpoint documented by Jobvite themselves (`Jobvite/APIConnectorSamples`). It is unlike every other endpoint: **query-string auth plus an RSA+AES encrypted envelope.**

### Request

```http
POST /api/v2/task?api=<api_key>&sc=<secret> HTTP/1.1
Host: api.jobvite.com
Content-Type: application/json; utf-8
Accept: application/json
```
```json
{ "key": "<base64(RSA-PKCS1(jobvite_public_key, aes_key))>",
  "payload": "<base64(AES-256-ECB-PKCS5(plaintext_json))>" }
```

`[OFFICIAL]` Envelope construction, exactly as Jobvite's sample does it:
1. Generate a 256-bit AES key (`KeyGenerator.getInstance("AES")`, `kg.init(256)`).
2. Encrypt the plaintext JSON with `AES/ECB/PKCS5Padding`.
3. Encrypt the AES key with **Jobvite's RSA public key** using `RSA/ECB/PKCS1Padding`. Jobvite supplies this key as a PEM or DER file.
4. Base64 both; POST as `{"key":..., "payload":...}`.
5. The response is the same envelope, with the AES key wrapped in **our** RSA public key. Decrypt with our private key.

So there is a **two-way key exchange**: we hand Jobvite a public key and receive theirs. That is an onboarding prerequisite, not a config value.

`[OFFICIAL]` Decrypted request payload is a filter DSL:
```json
{ "filter": { "task": { "processInstanceId": { "eq": "<processInstanceId>" } } } }
```

`[ASSUMED]` `eq` is evidently one operator of a set; **the operator catalogue is undocumented**. `[OFFICIAL]` `processInstanceId` is a 24-hex-character MongoDB-style ObjectId - **a different id format from the ~8-char `eId` used by candidates and jobs**. Do not build a single id validator across resources.

### Response

`[RECORDED]` A malformed envelope is rejected with **`HTTP 400` and a Tomcat HTML error page**, not the JSON `status` envelope:
```
HTTP/1.1 400
Content-Type: text/html;charset=utf-8

<!doctype html><html lang="en"><head><title>HTTP Status 400 – Bad Request</title>...
```
So §3's parser must survive an HTML body on this endpoint specifically.

`[ASSUMED]` Decrypted success shape unknown - no sample response is published and I have no key.

**Recommendation:** `AES/ECB` is a weak mode (identical plaintext blocks produce identical ciphertext blocks). That is Jobvite's choice and we must match it to interoperate, but it is worth an explicit note wherever we implement it so a future reader does not think it was ours. Given the key-exchange onboarding, the crypto burden, and the unknown response shape, **this endpoint is the lowest-value of the five and should be the last built, if at all.**

---

## 9. `GET /v1/jobFeed`

`[OFFICIAL]` Fully documented (2014 PDF), `[RECORDED]` still live today. The only endpoint here with a complete official parameter table.

### Request

```http
GET /v1/jobFeed?companyId=<companyId>&api=<api_key>&sc=<secret>&start=1&count=100 HTTP/1.1
Host: api.jobvite.com
```

| Parameter | Req | Default | Notes |
|---|---|---|---|
| `api` | **yes** | - | API key, **in the query string** |
| `sc` | **yes** | - | secret, **in the query string** |
| `companyId` | **yes** | - | from Admin/Profile, the value after `c=` in the career-site URL |
| `start` | no | `1` | 1-based, per the official doc |
| `count` | no | `100` | **max 1000** here, unlike the 500 cap on v2 lists |
| `type` | no | - | e.g. `Contractor`, `Full-time`, `Intern`, `Part-time` |
| `availableTo` | no | `External` | `External` \| `Internal` |
| `category` | no | - | career-site category |
| `location` | no | - | "City, state, Country" |
| `region` | no | - | configured in Admin |
| `department` | no | - | in the official sample request |

`[OFFICIAL]` Response: `{"total": <int>, "jobs": [ {"hiringManager": "...", ...} ]}` - collection key **`jobs`**, third distinct naming for the same concept.

**Security note (repeat of §2.1 rule 2):** this endpoint puts the secret in the URL by design. Its full URL must never reach a log, an exception message, or a trace. Redact `sc=` at the client boundary, not at the log sink.

---

## 10. Fixtures: recorded transport

`[RECORDED]` Captured 2026-08-27 against `https://api.jobvite.com`, unauthenticated. **These are real bytes and are safe to assert against verbatim.** Volatile headers (`Date`, `Set-Cookie` expiry) are marked; everything else was stable across repeated captures.

### 10.1 v2 auth failure - the canonical error

Request: `GET /api/v2/candidate` with no credentials (identical response with bogus credentials, in headers or query string).

```
HTTP/1.1 401
Content-Type: application/json;charset=utf-8
Content-Length: 92
Pragma: no-cache
Cache-Control: private, no-cache, no-store, max-age=0
Server: Jobvite
Access-Control-Allow-Origin: *
X-JOBVITE-PROXY: true
```
```json
{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}
```

### 10.2 v2 unknown route

Request: `GET /api/v2/offer`

```
HTTP/1.1 404
Content-Type: application/json
Content-Length: 67
```
```json
{"status":{"code":404,"messages":["Invalid URL Cannot find API."]}}
```

### 10.3 The 200-with-401-body trap - **the highest-value fixture here**

Request: `GET /api/v1/candidate`

```
HTTP/1.1 200
Content-Type: application/json;charset=utf-8
Content-Length: 92
```
```json
{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}
```

**This fixture must have a test.** It is the one case where a plausible client implementation silently converts an auth failure into an empty success. If our error handling regresses, this is the fixture that catches it, and nothing in §11 will.

### 10.4 v1 plain-text error, no Content-Type

Request: `GET /v1/jobFeed`

```
HTTP/1.1 401
Content-Length: 53
Server: Jobvite
Access-Control-Allow-Origin: https://app.jobvite.com
X-JOBVITE-PROXY: true
```
```
Invalid api/secret. Try again with a valid api/secret
```
Note: **no `Content-Type` header is sent.** A client that dispatches on content type must have a fallback.

### 10.5 HTML error body

Request: `POST /api/v2/task?api=<api_key>&sc=<secret>` with body `{"key":"x","payload":"y"}`

```
HTTP/1.1 400
Content-Type: text/html;charset=utf-8
Content-Length: 435
```
```html
<!doctype html><html lang="en"><head><title>HTTP Status 400 – Bad Request</title>...</head><body><h1>HTTP Status 400 – Bad Request</h1></body></html>
```

---

## 11. Fixtures: synthetic success bodies

> **⚠ NOT RECORDED. NOT EVIDENCE.**
> No success response from Jobvite has ever been observed by this research. Every body below is **reconstructed** from the field names, types, and null-handling that working third-party clients demonstrably read. Field *names* are well-corroborated; **value formats, optionality, and nesting depth are hypotheses.**
> Use these to develop against. Do not let a green suite built on them be read as "the client works". Replace them with recorded captures the day a credential lands (§13).

### 11.1 `GET /api/v2/candidate` - page of results

```json
{
  "total": 2,
  "candidates": [
    {
      "eId": "aBcD1234",
      "firstName": "Ada",
      "lastName": "Lovelace",
      "email": "ada@example.com",
      "mobile": "555-0100",
      "workPhone": "",
      "homePhone": "",
      "workExperience": [],
      "education": [],
      "application": {
        "eId": "app00001",
        "job": { "eId": "job00001" }
      }
    },
    {
      "eId": "eFgH5678",
      "firstName": "Grace",
      "lastName": "Hopper",
      "email": null,
      "mobile": "",
      "workPhone": "555-0199",
      "homePhone": "",
      "workExperience": [],
      "education": [],
      "application": { "eId": "app00002", "job": null }
    }
  ]
}
```
Deliberately encodes three observed hazards: `email: null`, empty-string phones, and `application.job: null` (the case a production integration guards with `failSilently`).

### 11.2 `POST /api/v2/candidate` - create success

```json
{
  "application": {
    "EId": "app00003",
    "candidate": { "EId": "iJkL9012" }
  }
}
```
Note the capital `EId`. `[INFERRED]` HTTP 201.

### 11.3 `GET /api/v2/job` - page of results

```json
{
  "total": 2,
  "requisitions": [
    {
      "eId": "job00001",
      "title": "Staff Engineer",
      "description": "<p>Build things.</p>",
      "applyLink": "https://jobs.example.com/apply/job00001",
      "jobState": "Open",
      "department": "Engineering",
      "category": "Engineering",
      "locations": [ { "city": "Chicago", "state": "IL", "country": "USA" } ],
      "lastUpdatedDate": 1756300000000,
      "sentDate": 1756200000000
    },
    {
      "eId": "job00002",
      "title": "Recruiter",
      "description": null,
      "applyLink": "https://jobs.example.com/apply/job00002",
      "jobState": "On Hold",
      "department": null,
      "category": "Human Resources",
      "lastUpdatedDate": 1756310000000,
      "sentDate": null
    }
  ]
}
```
Encodes `description: null` (mapping falls back to `title`), an absent `locations` key, a `null` department, and epoch-millisecond timestamps.

### 11.4 `GET /v1/jobFeed`

```json
{ "total": 1,
  "jobs": [ { "hiringManager": "Alan Turing", "title": "Staff Engineer", "id": "job00001" } ] }
```
`[OFFICIAL]` only `total`, `jobs`, and `hiringManager` are attested by the doc's sample; the rest of the job object's fields are **not** enumerated in the PDF excerpt available to me.

### 11.5 Suggested negative fixtures

Derive from §10 verbatim: 401 JSON, 404 JSON, **200-with-401-body**, v1 plain text with no content type, and the HTML 400. Every one is real, and together they cover all four error encodings in §3.3.

---

## 12. Documented negative: the OPTIONS `Allow` header is a decoy

Recording this so nobody re-discovers it and mistakes it for a finding.

`[RECORDED]` `OPTIONS /api/v2/candidate` succeeds **without credentials** and returns:
```
HTTP/1.1 200
Allow: GET,HEAD,POST,PUT,DELETE,OPTIONS
```
All 17 v2 resources return that identical `Allow` line. That looks like it resolves "which methods does each resource support" - the open question from `JOBVITE-API.md` §20 item 8.

**It does not.** I falsified it:

```
OPTIONS /api/v2/offer                              → 200  Allow: GET,HEAD,POST,PUT,DELETE,OPTIONS
OPTIONS /api/v2/definitely_not_a_real_endpoint_zzz → 200  Allow: GET,HEAD,POST,PUT,DELETE,OPTIONS
```

**A route that does not exist** (`GET` returns `404 Invalid URL Cannot find API.`) advertises the same method list. The header is emitted by the servlet container for any path, describing the dispatcher's capabilities rather than any handler's. It carries **zero** information about a specific resource, and treating it as a method contract would put `DELETE /api/v2/candidate` in our tool list on the strength of a framework default.

**The question stays open.** Method support per resource remains unresolved and belongs in §13.

---

## 13. Day-one credential checklist

The moment a real key exists, run these **in this order** and replace the §11 fixtures with recorded captures. Each row names what is currently unknown and what observing it settles. Rows 1-4 are blocking: no success-path code should be trusted until they are ticked.

| # | Check | Why it blocks | Settles |
|---|---|---|---|
| 1 | `GET /api/v2/candidate?count=1` - capture the **full** response, headers and body | The entire success-path contract is unobserved | Does a success body carry a `status` block? (§3.2) Envelope keys, real field names and types, rate-limit headers if any |
| 2 | `GET /api/v2/candidate?count=1&start=0` vs `&start=1` - compare the returned `eId`s | A silent off-by-one skips or duplicates a record on every page | Whether `start` is 0- or 1-based (§4.1) |
| 3 | `GET /api/v2/candidate?count=501` | We enforce a 500 cap client-side on third-party say-so | Whether 500 is a real server limit, and how it fails - error, or silent truncation |
| 4 | `GET /api/v2/candidate?candidateId=<nonexistent>` | Distinguishing "no such record" from "no such route" from "empty page" | The record-level not-found shape (§3.4) |
| 5 | `GET /api/v2/job?ids=<a>,<b>` | Batch-fetch efficiency and whether it silently ignores extras | Whether `ids` accepts a list |
| 6 | `GET /api/v2/job` with `datestart`/`dateend` | Incremental sync depends on it; the parameter names are pure assumption | Whether job date filtering exists and under what names |
| 7 | `GET /api/v2/<resource>?count=1` for each of the 13 undocumented resources | 13 route names with no contract | Their envelope keys and field shapes - the single highest-yield step for expanding tool coverage |
| 8 | `PUT` / `DELETE /api/v2/candidate` with an invalid id | The OPTIONS header cannot answer this (§12), and a probe with a *valid* id is destructive | Whether these are implemented at all - **use an invalid id; never test a destructive method by successfully running it** |
| 9 | Repeated `GET` at increasing rate | No documented limit, no headers to read (§2.3) | Whether a 429 exists, what it returns, and whether backoff guidance is included. **Run last, deliberately, and stop at the first 429** |
| 10 | One `POST /api/v2/candidate` in a customer-agreed test window | The only write in scope, and there is no sandbox | The 201 shape, the `EId` casing, and the `409` duplicate behaviour on an intentional repeat |

**Row 10 carries a standing caveat:** there is no sandbox, so this creates a real record in a real ATS. It needs the customer's explicit agreement, a named test job, and an agreed cleanup path *before* it is run - not after.
