# Jobvite REST API - Research Reference

**Compiled:** 2026-08-27 by `jobvite-api-research` for the `fast-mcp-jobvite` design.
**Scope:** the complete, currently-reachable Jobvite REST API surface, with every claim sourced.

---

## Table of Contents

1. [Confidence & Sources](#1-confidence--sources)
2. [The headline finding: there is no public Jobvite API documentation](#2-the-headline-finding-there-is-no-public-jobvite-api-documentation)
3. [API families and their status](#3-api-families-and-their-status)
4. [Base URLs and environments](#4-base-urls-and-environments)
5. [Authentication](#5-authentication)
6. [The v2 API: live-probed resource map](#6-the-v2-api-live-probed-resource-map)
7. [Resource family: Candidates & Applications (v2)](#7-resource-family-candidates--applications-v2)
8. [Resource family: Jobs / Requisitions (v2)](#8-resource-family-jobs--requisitions-v2)
9. [Resource family: Onboard tasks - encrypted envelope API (v2)](#9-resource-family-onboard-tasks---encrypted-envelope-api-v2)
10. [Resource family: Webhooks](#10-resource-family-webhooks)
11. [Resource families with no observed documentation (v2)](#11-resource-families-with-no-observed-documentation-v2)
12. [The v1 API (legacy, still live) - fully documented](#12-the-v1-api-legacy-still-live---fully-documented)
13. [Pagination, filtering, sorting, date formats](#13-pagination-filtering-sorting-date-formats)
14. [Rate limits](#14-rate-limits)
15. [Error model](#15-error-model)
16. [Versioning and deprecation policy](#16-versioning-and-deprecation-policy)
17. [OpenAPI / Swagger availability](#17-openapi--swagger-availability)
18. [Summary table of every endpoint](#18-summary-table-of-every-endpoint)
19. [Implications for fast-mcp-jobvite](#19-implications-for-fast-mcp-jobvite)
20. [What I could NOT verify](#20-what-i-could-not-verify)

---

## 1. Confidence & Sources

Every line in this document carries one of four labels.

| Label | Meaning |
|---|---|
| `[OFFICIAL]` | From a Jobvite-authored artifact: the archived *Jobvite Data Services v3.5* PDF, or the `Jobvite/APIConnectorSamples` GitHub repo (Jobvite's own org). |
| `[PROBE]` | I sent the request myself on 2026-08-27 and am quoting the server's actual response. This is first-party evidence from Jobvite's production host, but the *semantics* behind a status code are my reading. |
| `[INFERRED]` | Read off a third-party client or integration config, not Jobvite's own docs. Corroboration, not documentation. |
| `[ABSENT]` | I looked and it is not there. Stated as loudly as any positive finding. |

**Primary sources**

| Source | URL | Nature |
|---|---|---|
| Jobvite Data Services v3.5 (June 26, 2014) | `http://web.archive.org/web/20150319012741/http://careers.jobvite.com:80/careersites/JobviteWebServices.pdf` | `[OFFICIAL]` The only complete Jobvite-written API doc I could obtain. Covers **v1 only**. Saved locally as `jobvite-data-services-v3.5-2014.pdf`. The live URL `https://careers.jobvite.com/careersites/JobviteWebServices.pdf` now returns `text/html` (dead). |
| Jobvite/APIConnectorSamples | `https://github.com/Jobvite/APIConnectorSamples` | `[OFFICIAL]` Jobvite's own GitHub org. Java + C# samples for the encrypted `/api/v2/task` endpoint. Last pushed 2025-02-01. |
| Live probes of `https://api.jobvite.com` | - | `[PROBE]` ~180 requests, 2026-08-27. |
| raml-apis/Jobvite | `https://github.com/raml-apis/Jobvite/blob/master/api.raml` | `[INFERRED]` Third-party RAML 0.8 of the v1 API; matches the 2014 PDF closely enough to be a transcription of it. Saved as `jobvite-v1-api.raml`. |
| kippnorcal/jobvite | `https://github.com/kippnorcal/jobvite/blob/master/jobvite.py` | `[INFERRED]` Working Python v2 client. Source of the header-auth mechanics. |
| atipica/jobvite_api | `https://github.com/atipica/jobvite_api/blob/master/lib/jobvite_api/api/client.rb` | `[INFERRED]` Working Ruby v2 client (query-string auth era). |
| jeremylivingston/jobvite | `https://github.com/jeremylivingston/jobvite/blob/master/src/Livingstn/Jobvite/Client.php` | `[INFERRED]` PHP v1 jobFeed client. Source of the staging hostname. |
| frague/rm | `https://github.com/frague/rm/blob/master/server/controllers/integrations/jobvite.ts` | `[INFERRED]` TypeScript v2 client. |
| sahil-kho/ats-integrations (JobVite/) | `https://github.com/sahil-kho/ats-integrations/tree/main/JobVite` | `[INFERRED]` A production ATS-integration config for Jobvite: exact header names, request bodies, response field paths, webhook payload fields. The richest v2 artifact I found. **Note: this repo leaks a live-looking `x-jvi-sc` secret; do not copy it.** |
| APIs.json index (api-evangelist/jobvite) | `https://raw.githubusercontent.com/api-evangelist/jobvite/refs/heads/main/apis.yml` | `[INFERRED]` Metadata index only. No spec. |

**What is official vs inferred, in one sentence:** the **v1** API is fully documented by an official (if 12-year-old) Jobvite PDF; the **v2** API - the one anyone would actually build on - has **no public documentation at all**, and everything below about v2 is either a live probe of Jobvite's server or corroboration from working third-party clients.

---

## 2. The headline finding: there is no public Jobvite API documentation

This is the single most important input to our design, so it goes first.

* `[ABSENT]` **`developer.jobvite.com` does not exist.** DNS resolution fails:
  ```
  $ curl -L https://developer.jobvite.com
  curl: (6) Could not resolve host: developer.jobvite.com
  ```
  It has **never** existed publicly: the Wayback Machine has zero snapshots for it -
  `http://archive.org/wayback/available?url=developer.jobvite.com` returns `{"url": "developer.jobvite.com", "archived_snapshots": {}}`.
  One third-party client cites `@see https://developer.jobvite.com` (`odiseo153/search-job.`, `packages/plugins/source-ats-jobvite/src/jobvite.constants.ts`); **that citation is fabricated.** Do not propagate it.

* `[ABSENT]` `developer.employinc.com`, `api.employinc.com`, `developer.employ.com` - all fail DNS resolution.

* `[ABSENT]` **The Jobvite Help Center is login-gated and the old article URLs are dead.**
  `https://help.jobvite.com` is now a Salesforce Experience Cloud site. The legacy Zendesk-style article URLs behave as follows:

  | URL | Result (2026-08-27) |
  |---|---|
  | `/hc/en-us/articles/8870636608925-Jobvite-API` | HTTP 200 but the body is only a Salesforce SPA shell whose visible text is `Jobvite Help Center Loading × Sorry to interrupt CSS Error Refresh` - no article content is served to an unauthenticated client |
  | `/hc/en-us/articles/22012542918813-Jobvite-Onboard-New-Hire-API` | same SPA shell, no content |
  | `/hc/en-us/articles/24314987912733` (CRM Candidate Data API) | **HTTP 401** |
  | `/hc/en-us/sections/24681426999069-Integrations-API` | **HTTP 401** |

  The current portal lives at `https://employinc.my.site.com/jobvite/s/topic/0TOUa0000003v3NOAQ/api` and requires a customer login.

* `[OFFICIAL]` The public summary of the docs situation, as indexed from the help centre: *"Documentation is available to customers and ATS integration partners"* - i.e. gated by design.

* `[OFFICIAL]` Credentials are issued by humans, not self-service: *"In order to access the services you will need to be issued an API key and secret key by the Jobvite Customer Success team. Please file a request here: http://recruiting.jobvite.com/support/customer"* (Data Services v3.5, "Accessing Our Services").

**Consequence for us:** we cannot generate tools from a spec, and we cannot fully validate parameter names for most v2 resources without a customer sandbox and the gated PDF. Plan for a customer-supplied doc drop, or design for a narrow, evidence-backed subset. See §19.

---

## 3. API families and their status

| Family | Status | Evidence |
|---|---|---|
| **Jobvite API v2** (`/api/v2/*` on `api.jobvite.com`) | **CURRENT.** This is what modern integrations use. | `[PROBE]` 17 resources respond with an auth challenge; `[INFERRED]` every working client from 2019 onward targets `https://api.jobvite.com/api/v2` |
| **Jobvite API v1** (`/v1/*` on `api.jobvite.com`) | **LEGACY but STILL LIVE.** `/v1/candidate`, `/v1/job`, `/v1/employee`, `/v1/jobFeed` all still answer. Returns HR-XML for candidates. | `[OFFICIAL]` Data Services v3.5; `[PROBE]` see §12 |
| **Job Feed** (`/v1/jobFeed`) | **LIVE.** Public-ish career-site feed, still v1-only. There is no v2 job feed on `api.jobvite.com`: `GET /api/v2/jobFeed` → 404. | `[OFFICIAL]` + `[PROBE]` |
| **Contact Import API** (`/v1/contacts`) - Jobvite **Engage** CRM | Documented in 2014; **I could not confirm it is still live** (not probed to avoid a POST-only endpoint returning misleading results; a GET was not attempted for `/v1/contacts`). *"This API is only available to Jobvite Engage Customers."* | `[OFFICIAL]` Data Services v3.5 |
| **CRM Candidate Data API** | Exists as a help-centre article (`/hc/en-us/articles/24314987912733`) whose title is *"CRM Candidate Data API"*, described in search indexing as allowing third-party vendors to pull candidates created/updated/deleted in a date range. **Article body is 401-gated; I could not read it.** | `[ABSENT]` for content |
| **Jobvite Onboard - New Hire API** | Exists as a gated help-centre article (`/hc/en-us/articles/22012542918813`). The `/api/v2/task` endpoint in Jobvite's own sample code, with its `processInstanceId` filter, is workflow/onboarding-shaped and is my best guess at the Onboard surface - but that link is `[INFERRED]`. | `[OFFICIAL]` sample code; `[ABSENT]` doc content |
| **Bridge / JVX** | `[ABSENT]` I found **no** evidence of any API family under these names. `GET /api/v2/jvx` and `/api/v2/bridge` → 404. Do not assume these exist. |
| **Talemetry** | Separate live host: `https://api.talemetry.com` returns **HTTP 401** at the root, so an API exists there. `[ABSENT]` I found no documentation for it and it is not reachable via `api.jobvite.com`. Treat as out of scope unless the customer says otherwise. |
| **Engage** as an API namespace | `[ABSENT]` `engage.jobvite.com` and `api.engage.jobvite.com` fail DNS. Engage functionality reaches the API through `/v1/contacts`, not a separate host. |

---

## 4. Base URLs and environments

| Environment | Host | Status |
|---|---|---|
| **Production** | `https://api.jobvite.com` | `[OFFICIAL]` + `[PROBE]` LIVE. v2 base path `https://api.jobvite.com/api/v2`, v1 base path `https://api.jobvite.com/v1`. |
| **Staging** | `https://api-stg.jobvite.com` | `[OFFICIAL]` Documented in Data Services v3.5 for every v1 endpoint. `[PROBE]` **DNS resolution now FAILS** (`curl: (6) Could not resolve host`). The documented staging host is dead. |
| Staging (v2, third-party) | `https://app-stg.jobvite.com/api/v2/` | `[INFERRED]` Commented-out in `frague/rm`. `[PROBE]` also **fails DNS**. |
| Career-site feed host | `https://jobs.jobvite.com/api/v2/job-feed/{companyId}` | `[INFERRED]` from `odiseo153/search-job.`. `[PROBE]` **This is wrong or dead**: every slug I tried returns `HTTP 302 → http://search.jobvite.com?invalid=1`. Do not build on it. |
| App host | `https://app.jobvite.com` (and `hire.jobvite.com`, which redirects there) | `[PROBE]` LIVE, but this is the UI login, not an API. |

`[PROBE]` Production responses carry `Server: Jobvite`, `X-JOBVITE-PROXY: true`, `Access-Control-Allow-Origin: *`, and AWS ALB cookies - the API sits behind an AWS load balancer.

**Customer-specific identity.** There is **no per-customer hostname**. The company is identified two ways:

* `[OFFICIAL]` **`companyId`** - a query parameter, required for `/v1/jobFeed` and present in the Employee JSON body as `CompanyId`. How to find it: *"You can find your company ID by looking in Admin/Profile and looking under the Career Site section. The company ID is the numbers and letters after the c= in the url."* Example value from the docs: `dah4p0sl`.
* The **API key itself** scopes the caller to a company for the v2 endpoints - no `companyId` parameter appears in any working v2 client I read. `[INFERRED]`

---

## 5. Authentication

This is the section that decides our config and security posture, so it is the most carefully sourced.

### 5.1 The credential pair

`[OFFICIAL]` Two opaque strings, issued by a human at Jobvite:

> "What you need from us: • API key – This will give you access to a service to get data related to your company. • Secret key – This will be used to validate your API key."
> - Data Services v3.5, "Accessing Our Services"

`[OFFICIAL]` There is also an optional IP allowlist: *"You may also give us the IP address of the server that will be calling our service to increase security."* and *"What we need from you: • The IP address of the server accessing our services."*

`[OFFICIAL]` For the Requisition (Jobs) API specifically, a feature flag must be turned on first: *"Before starting development, please file a support ticket with the Jobvite Customer Success team asking that the 'Jobs API' be enabled for your company. This can be done at the same time the customer requests their company specific API Key, API Secret, and Company ID."*

`[ABSENT]` **There is no OAuth2, no bearer token, no token endpoint, and therefore no token lifetime.** `GET /api/v2/oauth`, `/api/v2/token`, `/api/v2/auth`, `/api/v2/login`, `/api/v2/authenticate` all return `404 Invalid URL Cannot find API.` The credentials are long-lived static secrets; rotation is a support ticket.

### 5.2 Header auth - the current mechanism

`[INFERRED]` **Two custom headers**, `x-jvi-api` (the key) and `x-jvi-sc` (the secret):

```python
    @property
    def request_credentials(self):
        return {"x-jvi-api": self.api_key, "x-jvi-sc": self.api_secret}
...
        # As of 10/1/2023, credentials have to be passed through headers
        response = requests.get(endpoint, params=params, headers=self.request_credentials)
```
- `kippnorcal/jobvite`, `jobvite.py` (verbatim)

Independently corroborated by a production integration config, on both the read and the write path:

```json
"method": "POST", "authTypes": ["BASIC"],
"apiPath": "https://api.jobvite.com/api/v2/candidate",
"headers": {"x-jvi-sc": "${api-secret}", "x-jvi-api": "${api-key}"}
```
- `sahil-kho/ats-integrations`, `JobVite/jobvite_data_model_integrations.json` (verbatim)

`[INFERRED]` **Timeline of the migration.** Two independent third parties date it differently: the Python client comments *"As of 10/1/2023"*; search indexing of the Jobvite help centre states the transition from URL-based to header-based authentication was *"effective April 1, 2024"*. I could not read the announcement article itself (401). Treat **April 1, 2024** as the customer-facing deadline and **October 2023** as when headers started working.

### 5.3 Query-string auth - legacy, and still accepted

`[OFFICIAL]` v1 uses query parameters, and the parameter names differ between endpoints - this is a real trap:

* `/v1/candidate` uses **`api`** and **`secret`**:
  > `https://api.jobvite.com/v1/candidate?api=jobvite&secret=test&action=getNewHires&format=hrxml&datestart=08-01-2009&dateend=2009-08-15T11:21:33-0700`
* `/v1/jobFeed` and `/v1/contacts` use **`api`** and **`sc`**:
  > `https://api.jobvite.com/v1/jobFeed?companyId=dah4p0sl&api=<api_key>&sc=<secret>&start=10&count=100&type=full-time&availableTo=internal&category=Finance&department=Human Resource&location=Burlingame, CA, USA&region=Europe`

`[OFFICIAL]` Jobvite's **own** current sample code (repo last pushed 2025-02-01) still puts the secret in the query string:

```java
	static String baseUrl="https://api.jobvite.com/api/v2/task?api={0}&sc={1}";
```
- `Jobvite/APIConnectorSamples`, `JobviteApiConnectorApplication.java` (verbatim)

`[INFERRED]` The Ruby client does the same for v2, adding a `format` parameter: `options.merge(api: @api_key, sc: @api_token, format: 'json')` (`atipica/jobvite_api`).

`[PROBE]` I could not determine whether query-string auth is still *honoured* on v2, because both a bogus header pair and a bogus query pair produce the identical `401` body. **This is a gap** - see §20.

### 5.4 Security posture for our design

* **Secrets in the query string are a live hazard.** They land in access logs, proxies, and `Referer` headers. Jobvite's own sample still does it. **We must use `x-jvi-api` / `x-jvi-sc` headers and never accept a config that puts credentials in a URL.**
* The credential is a **static, long-lived, company-wide secret with no scoping** - whatever the key can read, our server can read. There is no read-only variant documented.
* `[PROBE]` The API responds with `Access-Control-Allow-Origin: *`, so the credential is the only thing standing between a caller and the data.
* A cautionary datapoint: `sahil-kho/ats-integrations` has a live-looking secret committed at `JobVite/jobvite_data_model_integrations.json` (`x-jvi-sc: b9f9df17efb1b1558ce80ea9b590d4aa`), and its own README flags it: *"SECURITY: Hardcoded API keys in integration headers ... must be rotated and moved to customerStaticValues"*. Do not reuse it; do not let ours end up the same way.

### 5.5 The encrypted-envelope scheme (`/api/v2/task`)

`[OFFICIAL]` One endpoint uses a completely different, much heavier scheme on top of the api/sc pair. From `Jobvite/APIConnectorSamples`:

1. Client generates a **256-bit AES** key.
2. Request payload JSON is encrypted with `AES/ECB/PKCS5Padding`.
3. The AES key is encrypted with **Jobvite's RSA public key** (`RSA/ECB/PKCS1Padding`), supplied to the customer as a PEM or DER file.
4. Both are base64'd and POSTed as `{"key": "<b64 rsa-wrapped aes key>", "payload": "<b64 aes ciphertext>"}`.
5. The response is the same envelope, with the AES key wrapped in the **customer's** RSA public key; the client decrypts with its own private key.

```java
String jsonPayload = "{ \"filter\":{ \"task\":{ \"processInstanceId\":{ \"eq\":\"5fda297111edfb36b766c787\" } } } }";
```

So there is a **key exchange**: the customer gives Jobvite a public key and receives Jobvite's. Note `AES/ECB` is a weak mode - that is Jobvite's choice, quoted here as fact, not endorsed.

---

## 6. The v2 API: live-probed resource map

`[PROBE]` Method: unauthenticated `GET https://api.jobvite.com/api/v2/{name}` for ~180 candidate names on 2026-08-27. The server distinguishes two responses cleanly:

* **Exists** → `HTTP 401` `{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}`
* **Does not exist** → `HTTP 404` `{"status":{"code":404,"messages":["Invalid URL Cannot find API."]}}`

A 401 means *the route is registered and auth ran first*; it does **not** prove which HTTP methods, parameters, or response shapes that route supports.

**The 17 v2 resources that exist:**

| Resource | GET | POST | PUT | DELETE |
|---|---|---|---|---|
| `/api/v2/candidate` | 401 | 401 | 401 | 401 |
| `/api/v2/job` | 401 | 401 | - | - |
| `/api/v2/interview` | 401 | 401 | - | - |
| `/api/v2/employee` | 401 | - | - | - |
| `/api/v2/contact` | 401 | - | - | - |
| `/api/v2/workflow` | 401 | - | - | - |
| `/api/v2/department` | 401 | - | - | - |
| `/api/v2/location` | 401 | - | - | - |
| `/api/v2/category` | 401 | - | - | - |
| `/api/v2/customfield` | 401 | - | - | - |
| `/api/v2/task` | 401 | 401 (official sample) | - | - |
| `/api/v2/message` | 401 | - | - | - |
| `/api/v2/webhook` | 401 | - | - | - |
| `/api/v2/disposition` | 401 | - | - | - |
| `/api/v2/offerLetter` | 401 | - | - | - |
| `/api/v2/role` | 401 | - | - | - |
| `/api/v2/batch` | 401 | - | - | - |

(A `-` means I did not probe that method for that resource, not that it is unsupported. `PATCH /api/v2/candidate` returned a `302` redirect to `app.jobvite.com/admin/info/404.html`, i.e. the proxy does not route PATCH.)

**Routing is case-sensitive and inconsistent.** `customfield` exists but `customField` 404s; `offerLetter` exists but `offerletter` 404s. Any client we write must hard-code the exact casing above.

**Names that returned 404 (do NOT exist as v2 routes)** - worth recording because several are things a designer would assume are present:
`offer`, `user`/`users`, `requisition`, `hiringTeam`/`hiringteam`, `eeo`/`eeoc`, `attachment`, `application`/`applications`, `note`/`notes`, `activity`, `source`/`sources`, `referral`, `company`, `onboard`, `newHire`, `evaluation`, `questionnaire`, `survey`, `tag`, `jobFeed`, `careerSite`, `resume`, `file`, `document`, `picklist`, `metadata`, `schema`, `ping`, `health`, `status`, `version`, `agency`, `vendor`, `email`, `event`/`events`, `subscription`, `workflowState`, `stage`/`stages`, `rejectReason`, `background`, `assessment`, `feedback`, `interviewFeedback`, `scorecard`, `recruiter`, `hiringManager`, `interviewer`, `panel`, `schedule`, `calendar`, `search`, `report`, `analytics`, `export`, `import`, `bulk`, `sync`, `template`, `pipeline`, `jvx`, `bridge`, `engage`, `talemetry`, `hire`, `approval`, `permission`, `group`, `team`, `organization`, `salary`, `compensation`, `history`, `audit`, `config`, `settings`, `admin`, `profile`.

**Important caveat about `application`.** `sahil-kho/ats-integrations` describes a *"2-step: start-chain → create"* application write and its README calls it `POST /application/create`. `[PROBE]` **`/api/v2/application` and `/api/v2/application/create` both 404 on GET and POST.** Reading the actual config resolves the contradiction: the real call is `POST /api/v2/candidate` with a nested `application` object (§7.2). The README's path is wrong; trust the config, not its prose.

---

## 7. Resource family: Candidates & Applications (v2)

### 7.1 `GET /api/v2/candidate` - list/search candidates

`[INFERRED]` (three independent clients agree)

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `start` | int | no | Offset. `atipica` computes `(page-1)*per_page`; `kippnorcal` starts at `0`; `frague/rm` coerces `<1` to `1`. **The clients disagree about whether it is 0- or 1-based** - the v1 docs say 1-based. Unresolved. |
| `count` | int | no | Page size. **Maximum 500**, enforced client-side in two clients (`if batch_size > 500: raise ValueError('Batch size cannot be greater than "500"')`). |
| `candidateId` | string | no | Fetch one candidate (`atipica`: `options[:candidateId] = id`). |
| `applicationId` | string | no | Used together with `candidateId` to resolve one application: `https://api.jobvite.com/api/v2/candidate?candidateId=${candidateId}&applicationId=${applicationId}` (`sahil-kho`). |
| `datestart` | date | no | Lower bound on last-updated. |
| `dateend` | date | no | Upper bound on last-updated. |
| `dateFormat` | string | no | e.g. `yyyy-MM-dd`. Note the **camelCase `dateFormat`** in v2 clients vs the all-lowercase **`dateformat`** in the v1 PDF. |
| `wflowstate` | string | no | Workflow-state filter; both Python and TS clients leave a TODO saying they never implemented it, so it is `[INFERRED]` from v1 continuity, not observed working on v2. |
| `format` | string | no | `atipica` sends `format: 'json'`. |

**Response shape** `[INFERRED]`:
```json
{ "total": <int>, "candidates": [ { ... } ] }
```
`total` is the full result-set size (`atipica` fetches `count=5` purely to read `total`). Termination rule used by working clients: stop when `len(candidates) < count`.

**Candidate fields observed in mappings** (`sahil-kho`, `frague/rm`):
`eId` (the candidate id), `firstName`, `lastName`, `email`, `mobile`, `workPhone`, `homePhone`, `workExperience`, `education`, and a nested `application` object containing `job.eId`.

### 7.2 `POST /api/v2/candidate` - create candidate + application

`[INFERRED]` from `sahil-kho/ats-integrations`, which is a working production write path.

Request body:
```json
{
  "candidate": {
    "email": "...",
    "firstName": "...",
    "lastName": "...",
    "mobile": "...",
    "sendEmail": <bool>,
    "application": {
      "jobEId": "...",
      "sourceType": "CareerSite",
      "source": "Joveo",
      "resume": {
        "name": "resume.pdf",
        "contentByteArray": "<base64>",
        "format": "ByteArray"
      }
    }
  }
}
```
Required by the caller's own precondition rule: `firstName`, `lastName`, `email` (and `application.jobEId` for it to attach to a job).

**Response:** `HTTP 201`, with ids at `application.candidate.EId` and `application.EId` - note the **capital `EId`** on the write response versus lowercase `eId` on reads. Handled error statuses in that config: `400`, `404`, `409`.

Resume upload is inline base64 inside the same POST; there is no separate attachment endpoint (`/api/v2/attachment` 404s).

### 7.3 `PUT` / `DELETE /api/v2/candidate`

`[PROBE]` Both return `401`, so both routes are registered. `[ABSENT]` I have **no** evidence of their payloads or semantics. Do not design tools against them without a sandbox.

---

## 8. Resource family: Jobs / Requisitions (v2)

### 8.1 `GET /api/v2/job`

`[INFERRED]`

| Parameter | Type | Notes |
|---|---|---|
| `ids` | string | Fetch specific jobs: `https://api.jobvite.com/api/v2/job?ids=${jobId}` (`sahil-kho`) |
| `start`, `count` | int | Same pagination as candidates; `count` max 500 (`kippnorcal`, `frague/rm` default `count=500`) |
| date filters | - | The integration README says *"JOB → REST_API → Supported (date-filtered GET)"* but does not name the parameters. `[ABSENT]` exact names unverified for v2. |

**Response shape** `[INFERRED]`: `{ "total": <int>, "requisitions": [ ... ] }` - note the collection key is **`requisitions`**, not `jobs` (that is the v1 jobFeed key).

**Requisition fields observed** (`sahil-kho` JSONata mappings):
`eId`, `title`, `description`, `applyLink`, `jobState`, `department`, `category`, `locations[]` (with `city`, `state`, `country`), `lastUpdatedDate` (epoch millis - the mapping calls `$fromMillis()`), `sentDate` (epoch millis).

**`jobState` enumeration** `[INFERRED]` - the mapping switches on exactly these string values:
`Open`, `Closed`, `Filled`, `On Hold`, `Awaiting Approval`, `Approved`, `Rejected`, `Retracted`.

### 8.2 `POST /api/v2/job`

`[PROBE]` Returns `401`, so the route exists. `[OFFICIAL]` for v1 the equivalent (`POST /v1/job`) creates/synchronises requisitions from an external system, with these documented semantics that almost certainly still apply: *"Each time you update a requisition, we will overwrite any fields that are different – unless you manually update the requisition in Jobvite. In that case, we will stop overwriting the information. We will close the requisition when it's no longer in your feed."* `[ABSENT]` v2 body schema unverified.

---

## 9. Resource family: Onboard tasks - encrypted envelope API (v2)

`[OFFICIAL]` `POST https://api.jobvite.com/api/v2/task?api={key}&sc={secret}`

The only v2 endpoint with a **Jobvite-authored** example. Auth via query string; body and response are RSA+AES envelopes (§5.5). The decrypted request payload is a **filter DSL**:

```json
{ "filter": { "task": { "processInstanceId": { "eq": "5fda297111edfb36b766c787" } } } }
```

Two things worth noting for our design:
* the `{field: {operator: value}}` shape implies other operators exist (`eq` is clearly one of a set) - `[ABSENT]` the operator catalogue is undocumented;
* `processInstanceId` is a 24-hex-char MongoDB-style ObjectId, unlike the 8-char `eId` used for candidates and jobs - so **Jobvite's id formats are not uniform across resources**.

---

## 10. Resource family: Webhooks

`[PROBE]` `/api/v2/webhook` exists (401). `[ABSENT]` No documentation of registration, payload signing, retry policy, or event catalogue.

`[INFERRED]` Two webhook event types are consumed in production by `sahil-kho/ats-integrations`:
* **Job event** - handler `jobvite-job-webhook-event`, enriched by calling `GET /api/v2/job?ids=${jobId}`.
* **Application-stage event** - handler `jobvite-candidate-application-webhook-event`. Its payload is validated to contain exactly these fields:
  `eventType`, `url`, `id`, `applicationId`, `oldValue`, `newValue`, `date`.
  `newValue` is the raw new workflow-state value; the integration notes *"stageName equals raw stageId (newValue from webhook) — no human-readable label transformation"*, i.e. **Jobvite sends state values, not labels**. To get the job for a stage event you must call `GET /api/v2/candidate?candidateId=..&applicationId=..` and read `candidates[0].application.job.eId` - and that config marks the call `failSilently: true` because it *"may be null"*.

`[ABSENT]` No signature header is mentioned anywhere. If we ever receive Jobvite webhooks we must assume unauthenticated POSTs unless proven otherwise.

---

## 11. Resource families with no observed documentation (v2)

These routes exist (`401`) and nothing else about them is known. Listing them explicitly so nobody mistakes silence for absence - or absence for a spec:

`interview`, `employee`, `contact`, `workflow`, `department`, `location`, `category`, `customfield`, `message`, `disposition`, `offerLetter`, `role`, `batch`.

Reasonable-but-**unverified** readings, all `[INFERRED]` and flagged as guesses: `workflow`/`disposition` are the workflow-state and rejection-reason catalogues; `department`/`location`/`category`/`role` are picklist metadata (good cache candidates); `customfield` is the custom-field schema; `batch` is a multi-request wrapper. **None of this is evidence.** Do not ship tools shaped by these guesses.

Notably **absent from v2 entirely**: offers (`/api/v2/offer` 404s, though `offerLetter` exists), users (`/api/v2/user` 404s, though `employee` and `role` exist), hiring teams, EEO, and standalone attachments.

---

## 12. The v1 API (legacy, still live) - fully documented

Everything in this section is `[OFFICIAL]`, from *Jobvite Data Services v3.5, June 26, 2014*. `[PROBE]` confirms `/v1/candidate`, `/v1/job`, `/v1/employee`, `/v1/jobFeed` all still return `401 Invalid api/secret...` today - as **plain text**, not JSON, unlike v2.

### 12.1 Candidate API - `GET /v1/candidate`

> "This service can be used to get information about candidates and new hires... **We will return up to 500 candidates.** Please note that this API returns HR-XML"

| Parameter | Required | Description (verbatim) |
|---|---|---|
| `api` | Required | "The API key issued by Jobvite." |
| `secret` | Required | "The secret for this service, issued by Jobvite" |
| `action` | Required | "The action to perform. `getNewHires`, `getCandidates`" |
| `format` | Required | "The format of the data (HRXML)" |
| `wflowstate` | Optional | "The Jobvite candidate state name of candidates you are searching for (only applicable to getCandidates)" |
| `datestart` | Optional | "The date after which the candidate was last updated for filtering purposes." |
| `dateend` | Optional | "The date before which the candidate was last updated for filtering purposes." |
| `dateformat` | Optional | "The supported defaults are: `MM/dd/yyyy`, `MM-dd-yyyy`, `MM-dd-yyyy'THH:mm:ssZ`" |
| `start`, `count` | Optional | See pagination below |

> "The API can only call up to 500 candidates at a time. To retrieve more than 500 at once, leverage the `count` and a `start` parameter you can specify in the URL. For example, if you already get the first 500 records and you want the next 500 records, you would add `start=501&count=500` in the URL. The count means how many you want (maximum 500). The start means from where you want the next set of candidates."

**Response** is HR-XML (`http://ns.hr-xml.org/2007-04-15`) wrapped in `<Results xmlns="http://api.jobvite.com/action/api/v1" action="getNewHires" version="1.0">` with a `<NewHires first="1" count="1" total="1">` or `<Candidates first="1" count="3" total="3">` envelope. Candidate ids appear as `<ns:IdValue name="applicationId">p0MIXgwc</ns:IdValue>`; EEO data as `<ns:DemographicDescriptors><ns:Race/></ns:DemographicDescriptors>` and `<ns:BiologicalDescriptors><ns:GenderCode>1</ns:GenderCode></ns:BiologicalDescriptors>`; custom fields as `<Field type="Candidate" name="...">value</Field>`.

### 12.2 `POST /v1/candidate` with `action=updateCandidates`

> "Format – Required – hrxml/json/csv. POST Data: The json should be sent as a post parameter with name **`data`**."
```json
[{ "applicationId": "xyz123", "wflowstate": "Offer Accepted" },
 { "applicationId": "xyz456", "wflowstate": "Rejected" }]
```
This is the **only documented way to advance a candidate's workflow state.**

### 12.3 Employee API - `POST /v1/employee`

> "This operation is **not incremental**. If there are any employee information missing in subsequent feeds, that employee information is removed from the system."
> "Note: This is a scheduled task that runs nightly and an email confirmation will be received upon completion after 24 hours."

Required fields: `FirstName`, `LastName`, `Name` (the email address). Body-level flags: `CompanyId`, `ImporterEmail`, `ReportEmail`, `DoNotSyncOnWarnings`, `OverwriteEmployeeNamesAndEmail`, `DoNotRestoreDeleted`, `IgnoreExcludes`, `DoNotPerformEmployeeUpdates`, and an `Employees[]` array with `FirstName`, `LastName`, `Name`, `DepartmentName`, `LocationName`, `RegionName`, `SubsidiaryName`, `Role`, `Title`, `EmployeeId`.

**Role enumeration** (verbatim): `Recruiter`, `Administrator`, `SuperUser`, `HR`, `Scheduler`, `HiringManager`, `Research`, `JobApprover`, `Employee` ("default if no role is provided"). And a live footgun: *"If you import a field called Role, we will overwrite all employees' existing roles in Jobvite."*

*"We never sync if there are errors."*

### 12.4 Requisition API - `POST /v1/job`

XML or JSON. Envelope fields: `companyName`, `siteUrl`, `recruiterEmail`, `closeMissingReqs`, then `job[]` with `applyLink`, `briefDescription`, `description`, `isPrivate`, `internalOnly`, `category`, `jobId`, `jobLink`, `locationName`, `locationCity`, `locationState`, `locationCountry`, `recruiterEmail`, `evaluationFormName`. Requires the "Jobs API" feature flag (§5.1).

### 12.5 Job Feed - `GET /v1/jobFeed`

Two feeds: an XML feed (URL obtained from Customer Support; standard fields `id`, `title`, `requisitionid`, `category`, `jobtype`, `location`, `date`, `detail-url`, `apply-url`, `description`, `briefdescription`) and the JSON feed below.

| Parameter | Required | Default | Description (verbatim where quoted) |
|---|---|---|---|
| `api` | yes | - | API key |
| `sc` | yes | - | Secret |
| `companyId` | yes | - | "the numbers and letters after the c= in the URL" |
| `start` | no | `1` | "denotes the starting index. Default start index: 1" |
| `count` | no | `100` | "Default count: 100; **Posting Limit per call: 1000**" |
| `type` | no | - | "Job type, configured in Admin" - e.g. `Contractor, Full-time, Intern, Part-time` |
| `availableTo` | no | `External` | `External`, `Internal` |
| `category` | no | - | "The categories used on your career site, configured in Admin" |
| `location` | no | - | "City, state, Country" |
| `region` | no | - | "Region, configured in Admin" |
| `department` | no | - | present in the sample request and the RAML |

Response: `{"total": 2, "jobs": [ { "hiringManager": "...", ... } ]}`.

**Note the inconsistency:** jobFeed's `count` limit is **1000**, while the candidate API's is **500**.

### 12.6 Contact Import API - `POST /v1/contacts` (Jobvite Engage only)

Auth: `api` + `sc` in the query string. Body: `userEmail*`, `importDuplicates` (default false), `notes`, `tags[]`, `contacts[]*`. Per-contact: `firstName`, `middleName`, `lastName`, `company`, `jobTitle`, `tags[]`, `notes[]`, `resume`, `coverLetter`, `sourceType`, `sourceName`, `emails[]`, `homePhone`, `workPhone`, `cellPhone`, `address`, `address2`, `city`, `state`, `zip`, `country`, `urls[]`, `facebook`, `linkedin`, `twitter`, `assigneTo` (spelled `assignedTo` in the body example - the doc contradicts itself), `customFields[]` as `{name, value}` pairs.

---

## 13. Pagination, filtering, sorting, date formats

**Pagination** is offset-based on both versions: `start` + `count`. There is **no cursor, no `next` link, no `Link` header** anywhere in any source I read.

| Endpoint | `count` default | `count` max | `start` base |
|---|---|---|---|
| `/v1/candidate` | - | **500** `[OFFICIAL]` | 1 `[OFFICIAL]` |
| `/v1/jobFeed` | **100** `[OFFICIAL]` | **1000** `[OFFICIAL]` | 1 `[OFFICIAL]` |
| `/api/v2/candidate` | - | **500** `[INFERRED]` | disputed - see below |
| `/api/v2/job` | - | **500** `[INFERRED]` | disputed |

`[INFERRED]` **`start` base is genuinely ambiguous on v2.** `kippnorcal/jobvite` starts at `start=0` and increments by `batch_size`; `atipica/jobvite_api` computes `(page-1)*per_page` (also 0 for page 1); `frague/rm` explicitly forces `if (start < 1) start = 1`. The v1 docs are unambiguous that it is 1-based. **Off-by-one risk: one record duplicated or skipped per page.** Resolve against a sandbox before shipping.

`[INFERRED]` Both working clients terminate on `len(items) < count` rather than trusting `total`. We should do the same.

**Sorting:** `[ABSENT]` No sort or `orderBy` parameter appears in any source, official or third-party. I found no evidence that sorting is supported at all.

**Date formats:** `[OFFICIAL]` v1 accepts `MM/dd/yyyy`, `MM-dd-yyyy`, and `MM-dd-yyyy'THH:mm:ssZ` (as printed; the RAML transcribes the third as `yyyy-MM-dd'T'HH:mm:ssZ`, which matches the doc's own sample value `2009-08-15T11:21:33-0700` - **the PDF's parameter table appears to have a typo**). The format is selected by the `dateformat`/`dateFormat` parameter, not sniffed. `[INFERRED]` v2 clients send `dateFormat=yyyy-MM-dd`. Timestamps *in responses* are **epoch milliseconds** on v2 (`lastUpdatedDate`, `sentDate`) - a different convention from the request side.

---

## 14. Rate limits

**`[ABSENT]` Jobvite publishes no rate-limit numbers whatsoever.** Stating this plainly because it is a design input:

* No documented requests-per-second, per-minute, per-hour, or per-day figure exists in any source I found - official or third-party.
* `[PROBE]` The response headers contain **no** `X-RateLimit-*`, `RateLimit-*`, or `Retry-After` header. The full header set on a 401 is: `Date`, `Content-Type`, `Content-Length`, `Connection`, `Pragma`, `Cache-Control`, `Server: Jobvite`, four `Set-Cookie: AWSALBAPP-*`, `Access-Control-Allow-Origin: *`, `X-JOBVITE-PROXY: true`. That is all.
* `[ABSENT]` I did **not** observe a 429 from Jobvite and cannot describe its backoff behaviour. I deliberately did not attempt to trigger one.
* `[OFFICIAL]` What exists instead is **prose guidance**, not a limit:
  > "Best Practices: Calling the API: • Jobvite recommends calling our API on an 'as needed' basis. Should customers need to call the API more frequently than **once a day**, it is required that parameters be set on one of the following: o Dates at which candidates hit a desired workflow state. o # of candidates per candidate list page (last 100, last 500 etc.) o Candidates specific to a given requisition. o Requisitions that have only seen changes"

  Read that carefully: the *expected* cadence is **once a day**, and anything more frequent is expected to be **filtered**. That is a far tighter operating envelope than a typical SaaS API, and it is the closest thing to a documented limit that exists.
* `[INFERRED]` A production integration syncs Jobvite hourly (`"dataSyncFrequencyInHours": 1`, `sahil-kho/ats-integrations`), so hourly polling is evidently tolerated in practice.

**Design consequence:** we must assume an undocumented limit exists, implement conservative client-side throttling plus exponential backoff on 429/5xx, and cache aggressively - and we must **not** put a number in our docs that Jobvite has never published.

---

## 15. Error model

### 15.1 v2 error envelope `[PROBE]`

Every v2 error is JSON with an identical shape:
```json
{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}
```
`status.code` mirrors the HTTP status; `status.messages` is an **array** of strings.

Observed verbatim:

| HTTP | Body |
|---|---|
| 401 | `{"status":{"code":401,"messages":["Invalid api/secret. Try again with a valid api/secret"]}}` |
| 404 | `{"status":{"code":404,"messages":["Invalid URL Cannot find API."]}}` |

`[INFERRED]` `400`, `404`, and `409` are handled on the candidate-create path (`sahil-kho`); `409` is presumably a duplicate candidate. `201` is the documented success status for that create.

`[PROBE]` **A trap:** `GET /api/v2/../api/v1/candidate` returns **`HTTP 200`** with a `401` error *body*. Our client must therefore key error detection on `status.code` in the body, **not** on the HTTP status alone, or it will treat auth failures as successes. (`/v1/*` in contrast returns a real `401` with a plain-text body: `Invalid api/secret. Try again with a valid api/secret`.)

### 15.2 v1 error codes `[OFFICIAL]`

Full catalogue from Appendix B of Data Services v3.5, verbatim:

| Code | Message |
|---|---|
| 100 | No candidates or new hires found for the given query. |
| 101 | API key & secret could not be validated. |
| 102 | format is required. |
| 103 | Unable to parse datestart=* |
| 104 | Unable to parse dateend=* |
| 105 | An error occurred retrieving candidates. |
| 106 | Unknown format requested. |
| 107 | Error preparing candidate information. |
| 108 | Unrecognized candidate state (parameter wflowstate) in the request. |
| 201 | Cannot load the company from the json. *(updateCandidates)* |
| 202 | The data in the request is not a JSON array. |
| 203 | "applicationId" item is missing from the JSON. |
| 204 | Cannot find the application from the "applicationId". |
| 205 | Cannot find the candidate. |
| 206 | Candidate is not a candidate for this company. |
| 207 | Cannot determine a workflow state from the "wflowstate" item. |
| 208 | Error updating the candidate's record in the database. |

(`*` = "Incorrect format value.")

v1 errors are returned in the response envelope: `<Errors><Error code="100">No candidates or new hires found for the given query.</Error></Errors>`, and *"If there are any errors processing the request, only the Errors data will be returned."*

`[ABSENT]` **There is no equivalent published error-code catalogue for v2.** The 2014 PDF itself admits the gap even for v1 new-hires: *"The exact new hire data and error codes will be provided in a revision of this document."* No such revision is public.

---

## 16. Versioning and deprecation policy

`[ABSENT]` **Jobvite publishes no versioning or deprecation policy.** What can actually be established:

* Versioning is by **URL path segment**, and inconsistently: v1 is `/v1/{resource}` while v2 is `/api/v2/{resource}`. `[PROBE]` `/api/v1/jobFeed` → 404 but `/v1/jobFeed` → 401; `/v2/candidate` → 302 redirect but `/api/v2/candidate` → 401. **The prefix is not interchangeable between versions.** `[PROBE]` `/api/v1/candidate` does answer (with the 200-carrying-401-body quirk), so the v1 surface is partly mirrored under `/api/`, but not reliably.
* `[PROBE]` **There is no v3:** `/api/v3/candidate` → 404.
* v1 has survived at least 12 years past v2's arrival with no announced sunset - `[PROBE]` it still answers today.
* The one deprecation event I can point to is the **auth migration** (query string → headers, effective 2023-10-01 / 2024-04-01), and even that I know only second-hand because the announcement is behind the login.
* `[PROBE]` No `Sunset`, `Deprecation`, or `Warning` header is returned on any response.

---

## 17. OpenAPI / Swagger availability

**`[ABSENT]` No OpenAPI or Swagger specification for the Jobvite API is published anywhere.** Nothing was downloaded to `docs/research/jobvite-openapi.json|yaml` because no such document exists. Specifically checked:

* `https://apis.io/apis/jobvite/rest-api/` - lists Jobvite but its only machine-readable artifact is an **APIs.json index**, not a spec. Confirmed by fetching `https://raw.githubusercontent.com/api-evangelist/jobvite/refs/heads/main/apis.yml`: it is `specificationVersion: '0.23'` APIs.json, whose `properties` are three help-centre links and whose `baseURL` is `https://api.jobvite.com`. No `type: OpenAPI` property. Its own `accessModel` says `public: false`, `confidence: low`.
* `https://github.com/raml-apis/Jobvite` - a **RAML 0.8** file, not OpenAPI, and it describes **v1 only** (`title: Jobvite API v1`, `baseUri: https://api.jobvite.com/{version}`). Saved as `jobvite-v1-api.raml`. It is a third-party transcription of the 2014 PDF; it adds nothing the PDF lacks and contains at least one divergence (it names the jobFeed secret parameter `sc` and the candidate one `secret`, matching the PDF, but its `dateFormat` default text differs).
* `[ABSENT]` No public Postman workspace for Jobvite surfaced in any search.
* `[ABSENT]` No `/swagger.json`, `/openapi.json`, `/api/v2/schema`, or `/api/v2/metadata` route exists - all 404.

---

## 18. Summary table of every endpoint

Auth column: **H** = `x-jvi-api` + `x-jvi-sc` headers; **Q** = `api` + `secret`/`sc` query params; **E** = encrypted envelope on top of Q.

### v2 - `https://api.jobvite.com/api/v2`

| Method | Path | Purpose | Auth | Confidence | Notes |
|---|---|---|---|---|---|
| GET | `/candidate` | List/search candidates | H (Q legacy) | `[PROBE]` route, `[INFERRED]` params | `start`, `count`≤500, `candidateId`, `applicationId`, `datestart`, `dateend`, `dateFormat`. Returns `{total, candidates[]}` |
| POST | `/candidate` | Create candidate + application (+ base64 resume) | H | `[PROBE]` route, `[INFERRED]` body | 201 → `application.candidate.EId`, `application.EId` |
| PUT | `/candidate` | unknown | H | `[PROBE]` route only | no payload evidence |
| DELETE | `/candidate` | unknown | H | `[PROBE]` route only | no payload evidence |
| GET | `/job` | List requisitions | H | `[PROBE]` + `[INFERRED]` | `ids`, `start`, `count`≤500. Returns `{total, requisitions[]}` |
| POST | `/job` | Create/sync requisitions | H | `[PROBE]` route only | v1 analogue documented |
| GET/POST | `/interview` | unknown | H | `[PROBE]` route only | |
| GET | `/employee` | unknown | H | `[PROBE]` route only | v1 analogue is a full-roster POST |
| GET | `/contact` | unknown (Engage CRM?) | H | `[PROBE]` route only | v1 analogue `/v1/contacts` |
| GET | `/workflow` | unknown (workflow states?) | H | `[PROBE]` route only | |
| GET | `/department` | unknown (picklist?) | H | `[PROBE]` route only | |
| GET | `/location` | unknown (picklist?) | H | `[PROBE]` route only | |
| GET | `/category` | unknown (picklist?) | H | `[PROBE]` route only | |
| GET | `/customfield` | unknown (field schema?) | H | `[PROBE]` route only | lowercase only |
| GET | `/role` | unknown | H | `[PROBE]` route only | |
| GET | `/disposition` | unknown (reject reasons?) | H | `[PROBE]` route only | |
| GET | `/offerLetter` | unknown | H | `[PROBE]` route only | camelCase only |
| GET | `/message` | unknown | H | `[PROBE]` route only | |
| GET | `/webhook` | unknown (subscription mgmt?) | H | `[PROBE]` route only | |
| GET | `/batch` | unknown | H | `[PROBE]` route only | |
| POST | `/task` | Query Onboard/workflow tasks | E (Q) | `[OFFICIAL]` | AES-256 + RSA envelope; filter DSL `{filter:{task:{field:{eq:val}}}}` |

### v1 - `https://api.jobvite.com/v1`

| Method | Path | Purpose | Auth | Confidence |
|---|---|---|---|---|
| GET | `/candidate?action=getCandidates` | List candidates (HR-XML) | Q (`api`+`secret`) | `[OFFICIAL]` |
| GET | `/candidate?action=getNewHires` | List new hires (HR-XML) | Q (`api`+`secret`) | `[OFFICIAL]` |
| POST | `/candidate?action=updateCandidates` | Set workflow state for applications | Q (`api`+`secret`) | `[OFFICIAL]` |
| POST | `/employee` | Full (non-incremental) employee roster sync | Q | `[OFFICIAL]` |
| POST | `/job` | Create/sync requisitions | Q | `[OFFICIAL]` |
| GET | `/jobFeed` | Career-site job feed (JSON) | Q (`api`+`sc`+`companyId`) | `[OFFICIAL]` |
| POST | `/contacts` | Import contacts into Engage CRM | Q (`api`+`sc`) | `[OFFICIAL]`, liveness unverified |

**Endpoint count:** 21 distinct v2 method+path combinations across 17 resources (1 of them officially documented), plus 7 documented v1 operations.

---

## 19. Implications for fast-mcp-jobvite

Not design decisions - just the constraints the evidence imposes.

1. **Config must be header-based.** `JOBVITE_API_KEY` → `x-jvi-api`, `JOBVITE_API_SECRET` → `x-jvi-sc`. Never build a URL containing the secret, even though Jobvite's own sample does.
2. **One host, no per-tenant URL.** `JOBVITE_BASE_URL` defaults to `https://api.jobvite.com`; there is no working sandbox host to point at (`api-stg` is dead), so there is **no safe environment to test writes against** without a customer's real tenant. This is the biggest operational risk in the project.
3. **Error detection cannot trust HTTP status** - parse `status.code` from the body (§15.1).
4. **Only 4 v2 endpoints have enough evidence to build a tool against today**: `GET /candidate`, `POST /candidate`, `GET /job`, `POST /task`. The other 13 resources are names without contracts. Building tools for them means guessing parameter names, and a wrong parameter on a POST could mutate customer data.
5. **Rate limiting must be conservative and configurable**, defaulting near Jobvite's own "as needed / once a day, filtered" guidance rather than an invented number.
6. **Cache the picklist-shaped resources** (`department`, `location`, `category`, `role`, `customfield`, `workflow`, `disposition`) once their shapes are known - they are the natural cache targets, same as the JIRA server's metadata caching.
7. **Ask the customer for the gated docs.** The fastest path to a complete surface is a Jobvite customer login to `employinc.my.site.com/jobvite` or a partner doc pack from Employ Inc. Everything unknown in this report is behind that login.

---

## 20. What I could NOT verify

Listed without softening. Each one is a real hole.

1. **The current official v2 documentation.** Gated behind a customer login at `help.jobvite.com` / `employinc.my.site.com`; `/hc/en-us/sections/24681426999069-Integrations-API` returns **HTTP 401** and the article URLs return an empty Salesforce SPA shell. I never read a single line of Jobvite's current API documentation.
2. **The CRM Candidate Data API** (`/hc/en-us/articles/24314987912733`) - **HTTP 401**. Title and a one-line search-engine description only. I do not know its endpoint, parameters, or whether it is a v2 route or something else entirely.
3. **The Onboard New Hire API** (`/hc/en-us/articles/22012542918813`) - SPA shell, no content. Its relationship to `/api/v2/task` is my inference, not established fact.
4. **Whether query-string auth still works on v2.** A bogus header pair and a bogus query pair return byte-identical 401s, so my probe cannot discriminate. Only a valid credential can settle it.
5. **The exact header-auth cutover date.** Two third parties give two dates (2023-10-01 and 2024-04-01) and the announcement is behind the login.
6. **Whether `start` is 0-based or 1-based on v2.** Three working clients disagree (§13). Off-by-one risk on every paged read.
7. **The request/response contract for 13 of the 17 v2 resources** - `interview`, `employee`, `contact`, `workflow`, `department`, `location`, `category`, `customfield`, `message`, `webhook`, `disposition`, `offerLetter`, `role`, `batch`. I know only that the routes exist and answer with an auth challenge.
8. **Which HTTP methods each v2 resource supports.** I probed POST on 7 resources and PUT/DELETE on 1. A 401 on GET says nothing about whether POST is routed.
9. **Rate limits.** No numbers, no headers, no observed 429, no documented backoff. See §14.
10. **The v2 error-code catalogue.** Only 401 and 404 bodies observed directly; 400/404/409 inferred from a third-party handler. There is no v2 equivalent of the v1 Appendix B.
11. **Webhook registration, signing, retry, and the event catalogue.** `/api/v2/webhook` exists; nothing else is known. I found no evidence of any signature header - if we ever consume these, assume unauthenticated.
12. **Whether sorting is supported at all.** No `sort`/`orderBy` parameter appears in any source. Absence of evidence here, not evidence of absence.
13. **Any working sandbox.** `api-stg.jobvite.com` and `app-stg.jobvite.com` both fail DNS resolution today, despite `api-stg` being documented for every v1 endpoint. I could not confirm any non-production environment exists in 2026.
14. **`/v1/contacts` liveness.** Documented in 2014, never probed (POST-only; a GET result would have been misleading).
15. **The Talemetry API.** `https://api.talemetry.com` returns 401 at the root, so something is there. I found no documentation and did not map it.
16. **Actual response bodies.** I hold **no valid credential**, so every response shape in this document comes from a third-party client's field mappings, never from a 200 I saw myself.
17. **The `/api/v2/task` filter operator catalogue.** `eq` is the only operator in Jobvite's sample.
18. **The 2014 PDF's currency.** It is the authority for v1 in this document and it is **12 years old**. Behaviour may have drifted; its own text promises a revision that was never published.

---

*Artifacts saved alongside this report:*
* `jobvite-data-services-v3.5-2014.pdf` - the archived official v1 documentation (492 KB, 8 pages)
* `jobvite-v1-api.raml` - third-party RAML 0.8 of the v1 surface

*No `jobvite-openapi.json` / `.yaml` exists to save. See §17.*
