# fast-mcp-jobvite - Design

Status: **DRAFT, under review.** Frozen at 0C/0H/0M, after which only a numbered ADR in
`docs/adr/` may change it.
Last updated: 2026-08-27 02:23 PM CDT.

Evidence base: `docs/research/JOBVITE-API.md`, `JOBVITE-CONTRACT.md`, `FASTMCP.md`,
`FASTMCP-SPIKE.md`, `STANDARDS.md`, `COMPLIANCE-SPEC.md`. Decisions: `docs/DECISIONS.md`.

---

## 1. What this is

An MCP server that exposes Jobvite, an applicant tracking system, as tools a model can call.
It runs locally over stdio for desktop clients, or over Streamable HTTP when hosted.

**What it is not.** It is not a Jobvite SDK, not a sync engine, and not a cache. It holds no
state between calls beyond an HTTP connection pool and a rate-limiter bucket.

### 1.1 The constraint that shapes everything

Jobvite publishes no public API documentation. `developer.jobvite.com` has never existed; the
support site is login-gated; no OpenAPI document exists anywhere. There is no sandbox -
`api-stg.jobvite.com` fails DNS. Nobody on this project holds a Jobvite credential, so **no
success response from Jobvite has ever been observed by anyone building this.**

Two consequences run through the whole design:

1. **Scope is limited to what is evidenced.** Of 17 live v2 resources, five operations have a
   usable contract. The rest are route names that answer 401 when they exist and 404 when they
   do not. We ship tools for the five and none for the twelve.
2. **Every success-path response shape is a hypothesis.** The design must fail loudly when a
   hypothesis is wrong, rather than degrade into a plausible empty result. This is why §5 exists.

---

## 2. Tool surface

Five tools. The standards require a minimal allow-list because an unused or unreliable tool is
attack surface, and the evidence permits no more than this anyway.

| Tool | Jobvite operation | Kind |
|---|---|---|
| `search_candidates` | `GET /api/v2/candidate` | read |
| `get_candidate` | `GET /api/v2/candidate?candidateId=` | read |
| `search_jobs` | `GET /api/v2/job` | read |
| `get_job_feed` | `GET /v1/jobFeed` | read |
| `create_candidate` | `POST /api/v2/candidate` | **write, destructive, default-denied** |

`search_candidates` and `get_candidate` hit the same endpoint but are separate tools because
their parameter sets are disjoint and each gets a tight, closed schema. One overloaded tool with
mutually exclusive parameters is exactly the loose surface `ai/tool-calling.md` prohibits.

**`POST /api/v2/task` is deliberately excluded from v1.0.** It requires an RSA key exchange with
Jobvite as a human onboarding step, uses AES-256-ECB, and its decrypted success shape is
unknown. It is the lowest-value and highest-cost of the five candidates, and nothing else
depends on it.

### 2.1 Tool schemas

Every tool takes a typed Pydantic model, never a free-form dict. Every string field carries an
explicit `max_length`. Identifier fields carry a regex. Models are `strict=True` and forbid
extra keys, so an unexpected argument is rejected rather than ignored.

Outputs are snake_case, regardless of Jobvite's casing.

### 2.2 `create_candidate` is guarded

It is the only write, it creates real records in a real ATS, and there is no sandbox to rehearse
in. Therefore:

- **Default-denied.** The tool is not registered unless `JOBVITE_ENABLE_WRITES=true`. A
  read-only deployment cannot call it because it does not exist there.
- **`send_email` defaults to `false`.** The destructive side effect of this endpoint is not the
  database row, it is the email to a human candidate. That is not a default anyone should
  inherit by omission.
- **Never retried.** See §4.3. A timeout after a successful create duplicates a candidate.
- Annotated `destructiveHint: true`, `idempotentHint: false`, `readOnlyHint: false`.

The remaining four tools are annotated `readOnlyHint: true`.

---

## 3. Module layout

```
src/fast_mcp_jobvite/
  __main__.py                 entry point; transport selection; logging before imports
  server.py                   FastMCP instance, middleware stack, lifespan
  config.py                   pydantic-settings; SecretStr; fails fast on missing config
  errors.py                   exception hierarchy + RFC 9457 problem construction
  services/jobvite_client.py  httpx client: auth, the error rule, pagination, resilience
  tools/candidates.py         search_candidates, get_candidate, create_candidate
  tools/jobs.py               search_jobs, get_job_feed
  utils/redaction.py          log redaction; untrusted-content delimiting
  utils/normalise.py          casing, dates, empty-string/null unification
```

There is no cache module, no bulk module, and no custom logging module. Framework middleware and
`loguru` cover the first and third; the second is speculation. Jobvite's own guidance is to call
the API on an as-needed basis, so a cache would add a staleness failure mode to buy throughput
nobody asked for.

---

## 4. The Jobvite client

### 4.1 Authentication

v2 credentials travel as headers, `x-jvi-api` and `x-jvi-sc`. **A URL containing a secret is
never constructed**, even though Jobvite's own published sample code does exactly that.

`GET /v1/jobFeed` is the single exception: it structurally requires `api`, `sc` and `companyId`
as query parameters. Its URL is therefore classified as sensitive - never logged whole, never
placed in an exception message, and `sc=` is redacted before any log line is emitted. This is
enforced in one place, `utils/redaction.py`, and covered by a test that fails if a secret can
reach a log record.

Credentials are `SecretStr` throughout and are read with `.get_secret_value()` only at the point
of building a request.

### 4.2 The error-detection rule

**The single most important behaviour in this codebase.** `api.jobvite.com` has been observed
returning `HTTP 200` with a body of `{"status":{"code":401,...}}`. A client that branches on the
HTTP status alone reads that as success, finds no `candidates` key, and reports zero candidates
for what is a rejected credential. A wrong zero that explains itself.

**Invariant:** a response is successful only if the body carries no `status.code >= 400` **and**
the HTTP status is below 400. Both conditions, every call.

The parser cannot assume JSON, and cannot dispatch on content type either. Four error encodings
exist across this one API: a JSON status envelope, plain text with no `Content-Type` header at
all, a Tomcat HTML error page, and HR-XML. XML is parsed with `defusedxml`; entity expansion on
attacker-reachable input is not a risk we take on a public tool.

### 4.3 Resilience

Ordered timeout, then retry, then circuit breaker, as `backend/resilience.md` requires.

- **Timeouts are explicit and per-phase.** No SDK default, no single scalar.
- **Retries use `tenacity` with jitter**, and the total retry budget stays inside the inbound
  timeout. Retries are never blanket: only connection errors, timeouts and 5xx are retried.
- **`create_candidate` is never retried under any condition.** It is not idempotent and there is
  no sandbox in which to discover what a duplicate costs.
- **One circuit breaker for Jobvite.** 4xx responses must not trip it - a bad candidate id is
  our caller's problem, not a signal that Jobvite is unhealthy.

### 4.4 Rate limiting

Jobvite returns **no rate-limit headers of any kind** - no `X-RateLimit-*`, no `Retry-After`.
There is nothing to parse and nothing to feed a backoff calculation, so throttling is entirely
client-side and configuration-driven, with a conservative default.

The mandated Redis token bucket is not used; the standard's stated rationale is desynchronisation
across replicas, and a single-process server has none. This deviation is **ADR-0002**.

### 4.5 Pagination

Offset-based, `start` and `count`, max page size 500 on v2 and 1000 on `/v1/jobFeed`. No cursor,
no `Link` header.

**`start` is 1-based, and this is an assumption, not a fact.** Three working third-party clients
disagree; the only statement from Jobvite itself is its own v1 documentation, which is 1-based.
If we are wrong, we silently skip the first record of every page - a correctness bug that no test
built on synthetic fixtures can catch. It is therefore:

- configurable via `JOBVITE_PAGINATION_START_BASE`, so a user who discovers the truth can fix it
  without a release;
- logged once at startup as an assumption;
- listed as blocking row 2 of the day-one credential checklist;
- stated in the README, because a user with a credential can settle it in one call and we should
  make that easy rather than hide the uncertainty.

Paging terminates on a short page (`len(items) < count`), never on `total`. If `total` counts a
filtered set while pages are unfiltered, or the set mutates mid-scan, a `total`-driven loop
truncates or spins. `total` is reported to the caller and never trusted as a loop condition.

---

## 5. Errors

Failures return `ToolResult(structured_content=<problem>, is_error=True)` carrying a complete
RFC 9457 problem object: `type`, `title`, `status`, `detail`, `instance`, `request_id`,
`timestamp`. There is no `success: true/false` envelope anywhere in this repository.

`type` is a relative `/problems/<slug>`. `instance` is
`urn:fast-mcp-jobvite:invocation:<request_id>`, because MCP has no request URI. `status` carries
the upstream Jobvite status where one exists, 400 for input validation, and 503 for an upstream
5xx.

`application/problem+json` cannot be set on an MCP tool error, which travels inside a 200 OK
JSON-RPC body whose content type the transport fixes. That clause is violated in the letter and
no implementation can satisfy it: **ADR-0003**. Where a real HTTP surface exists - the health
endpoint and transport-level auth rejections - `problem+json` is applied properly.

`mask_error_details=True` is set explicitly at construction. FastMCP defaults it to **False**,
which sends the full text of any unhandled exception to the client. Masking is client-facing
only: the full traceback still reaches the server log, so a credential is never interpolated
into an exception message and the log stream is treated as sensitive.

---

## 6. Untrusted content

Candidate-authored free text - résumé body, cover letter, notes, and any name or email field a
candidate typed - is **attacker-authored input that this server feeds directly to a model.**
That is the exact threat `ai/prompt-injection.md` addresses.

Every such field is delimited before it reaches a tool result, and delimiter tokens occurring
inside the content are stripped so the content cannot close its own fence. The field inventory
lives in `JOBVITE-CONTRACT.md` and is enforced by an allow-list in `utils/redaction.py`: a
response field not on the known-safe list is treated as untrusted by default, so a new Jobvite
field arrives fenced rather than raw.

Red-team cases for this live in the main test suite and are merge-gating.

---

## 7. Server, transport, configuration

**stdio by default**, HTTP opt-in via `JOBVITE_MCP_TRANSPORT=http`. A public repo serves both
local desktop clients, for whom stdio must work with no configuration, and hosted deployments.
HTTP binds `127.0.0.1` unless told otherwise, and `allowed_hosts`/`allowed_origins` are set
whenever the bind address is not loopback.

**Auth on the HTTP surface** uses FastMCP's `StaticTokenVerifier` built from environment at
startup - not a hand-rolled verifier. Under-scoped clients do not merely get refused: the tool
is **removed from `list_tools` entirely**, and a direct call returns "Unknown tool", not a
permission error. This is good behaviour (a read-only token never sees `create_candidate`) with a
confusing failure mode, so the README documents it explicitly. Otherwise every support
conversation starts in the wrong place.

**Configuration is `pydantic-settings`, and it owns required-config validation.** `fastmcp.json`
cannot express a required environment variable - with a variable unset the server starts normally
and the tool receives the literal string `${JOBVITE_API_KEY}`, surfacing later as a confusing
Jobvite 401. A missing credential must fail at boot, naming the variable. `server.json` declares
the variables for registry consumers; pydantic-settings enforces them.

**Middleware:** timing and structured logging, with `include_payloads` left at its default
`False` - for this server those payloads are candidate PII.

`ResponseLimitingMiddleware` is **not used.** It raises `RuntimeError: ... did not return
structured content` on any tool with a return type annotation, which is the documented style and
what we write. It fires only on the oversized path, so it passes every small-payload test and
fails on the first large candidate list. Response size is bounded inside each tool instead: a
page is capped and the result says `showing 50 of 1,240`, which is more useful to a model than a
truncated JSON blob. This is **ADR-0004**, with the upstream bug report attached.

---

## 8. Testing

The default suite runs with no network and no credentials, and CI has **zero skips** - a skip
counts as a failure under `architecture/testing-strategy.md`, so credential-dependent tests are
excluded by selection rather than marked `skipif`.

**Fixtures are split, and the split is load-bearing:**

- **Recorded fixtures** are byte-exact captures of real Jobvite error transport. Assert against
  them verbatim.
- **Synthetic fixtures** are every success body, because no 2xx from Jobvite has ever been
  observed. They are hypotheses in JSON form.

**A suite that passes only against synthetic fixtures proves the client is self-consistent, not
that it speaks Jobvite.** That is the fakes-are-green failure, and it is stated in the test
module's own docstring so nobody mistakes green for verified. `docs/CREDENTIAL-CHECKLIST.md`
converts each synthetic fixture into a recorded one the day a key lands; rows 1-4 are blocking.

Required cases, each of which fails if the corresponding defence is removed:
- the 200-with-401-body trap, which is the one case where a plausible implementation turns an
  auth failure into an empty result set;
- a secret never reaching a log record, including the `jobFeed` URL;
- untrusted-content fencing, including content that tries to close its own fence;
- `create_candidate` not retrying on timeout;
- a 4xx not tripping the circuit breaker;
- the `eId`/`EId` casing asymmetry, pinned so a later refactor cannot "tidy" it into a bug.

Coverage: 80% floor overall, 85% on tool modules, 90% on the Jobvite client, 95% line and 90%
branch on critical paths (auth, argument rejection, the error rule, the write tool).

---

## 9. Known contract hazards

These are Jobvite's, not ours, and each needs explicit handling rather than discovery in
production:

1. **Casing asymmetry.** Reads return `eId`; the create response returns `EId`. Same id space.
   Normalised at the boundary, pinned by a test.
2. **Date asymmetry.** Requests take formatted strings (`yyyy-MM-dd`); responses return epoch
   milliseconds.
3. **Three names for one concept.** The v2 job list keys on `requisitions`, the v1 job feed on
   `jobs`, and the create response nests under `application`.
4. **Empty strings where nulls belong.** Phone fields use `""` rather than `null`. Treated
   identically at the boundary.
5. **No stable sort.** No sort parameter is documented, so a long paged scan over a mutating
   result set may duplicate or skip. Bounded date windows are preferred to full-catalogue walks,
   and the README says so.
6. **Route-level 404s.** `404 "Invalid URL Cannot find API."` means the route does not exist, not
   that a record was not found. The record-level not-found shape is unknown.

---

## 10. Repository and delivery

Canonical at `evolvconsulting/fast-mcp-jobvite`, mirrored to `Aztec03hub/fast-mcp-jobvite` via a
dual-push-URL `origin` plus a workflow for pushes from elsewhere.

Python `>=3.12`. `fastmcp==4.0.0b4`, targeting the sessionless `2026-07-28` MCP spec as
deliberate early adopters; bugs found are reproduced minimally and reported upstream. `uv` with a
committed lockfile. `ruff` check and format, `mypy` at zero errors, `pytest` with branch
coverage.

CI: lint, format, types, tests, plus `pip-audit`, CodeQL, TruffleHog with full history depth,
SBOM in both CycloneDX and SPDX, and a `pip-licenses` allow-list gate. A `fastmcp inspect`
capability report is emitted as an artifact and diffed, so tool-surface drift is visible in
review rather than at runtime.

**Secret scanning also runs pre-commit**, deliberately exceeding the standard, which mandates it
only in CI. On a public remote a pushed secret is compromised the instant it lands; catching it
after the push is catching it too late. This repository has already had one incident of the
adjacent class.

---

## 11. Open questions

Tracked rather than resolved, because resolving them requires access nobody here has:

1. **A Jobvite credential.** Converts every synthetic fixture to a recorded one. Blocking for
   any claim that this is verified against Jobvite.
2. **The `start` base.** One call settles it.
3. **The record-level not-found shape.** Unknown.
4. **Whether success bodies carry a `status` block at all.** The parser tolerates both.
5. **fastmcp 4.0.0b4 behaviour.** The runtime spike is confirmed against 3.4.7; the 4.0 re-run
   is in flight, and this design is not frozen until it lands.

---

## 12. ADRs this design requires at freeze

- **ADR-0001** - target fastmcp 4.0.0b4 and the sessionless spec, not the stable line.
- **ADR-0002** - in-process rate limiting instead of the mandated Redis token bucket.
- **ADR-0003** - RFC 9457 on an MCP transport: `problem+json` cannot be set on a tool error.
- **ADR-0004** - `ResponseLimitingMiddleware` excluded; size bounded in-tool.
- **ADR-0005** - the `ai/` standards domain binds this repository by intent, though its own
  scope clause covers only code that calls foundation models.
- **ADR-0006** - single `main` branch rather than the mandated `main`+`develop` GitFlow.
