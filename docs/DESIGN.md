# fast-mcp-jobvite - Design

Status: **DRAFT, revision 3.** Incorporates adversarial review rounds 1 and 2
(`DESIGN-R1.md` 0c/2h/1m, `DESIGN-R2.md` 0c/3h/1m), the B1-B106 conformance sweep
(`CONFORMANCE-B1-B106.md`), the design-artifact sweep (`CONFORMANCE-DESIGN-ARTIFACT.md`), and all
runtime-spike findings. Frozen at 0C/0H/0M, after which only a numbered ADR in
`docs/adr/` may change it.
Last updated: 2026-08-27 03:45 PM CDT.

Evidence: `docs/research/JOBVITE-API.md`, `JOBVITE-CONTRACT.md`, `FASTMCP.md`,
`FASTMCP-SPIKE-4.md`, `STANDARDS.md`, `COMPLIANCE-SPEC.md`. Decisions: `docs/DECISIONS.md`.

**What is and is not verified in this document**, stated precisely because a blanket compliance
claim is exactly the kind of self-certification that has already been wrong once on this project:

- **Every claim about FastMCP or the MCP protocol is executed.** Each rests on a spike in
  `FASTMCP-SPIKE-4.md` against `fastmcp==4.0.0b4`, or on a clause quoted at its `file:line`.
- **Every claim about Jobvite's error transport is recorded.** Byte-exact captures.
- **No claim about a Jobvite success response is verified**, because none has ever been observed.
- **Two mechanisms designed here have never been executed** and cannot be without a credential:
  the runtime `start`-base probe (§4.5) and the capability-drift diff (§10). Both are marked at
  their point of use, not only in §11.

A reviewer should treat "verified" in this document as meaning one of the first two, and should
challenge any sentence that reads as verified without belonging to them.

---

## 1. What this is

An MCP server exposing Jobvite, an applicant tracking system, as tools a model can call. It runs
over stdio for local clients and over Streamable HTTP when hosted.

It is not an SDK, a sync engine, or a cache. **It caches no Jobvite response** (§7.7). The only
state outliving a call is an HTTP connection pool, the framework rate limiter's in-process token
buckets, and unredeemed confirmation tokens (§7.6) - none of which holds candidate data.

**Single-process is load-bearing**, not incidental: ADR-0002's rate-limiting argument and §7.6's
token store both assume one process. Running this multi-worker breaks both silently - each worker
gets its own buckets and its own token store, so limits multiply and a token minted by one worker
is unknown to another. Stated here because it is the kind of assumption someone violates by
deploying normally.

### 1.1 The constraint that shapes everything

Jobvite publishes no public API documentation. `developer.jobvite.com` has never existed - the
Wayback Machine holds zero snapshots, and a third-party client citing it fabricated the citation.
The support site is login-gated. No OpenAPI document exists. There is no sandbox:
`api-stg.jobvite.com` fails DNS. **Nobody building this holds a Jobvite credential.**

**One** genuine Jobvite `200` exists in our evidence: a third-party VCR cassette recorded against a
live tenant (`JOBVITE-API.md` §6.1). It is the project's strongest success-shape evidence and it
already answers what a success envelope looks like. Its body cannot be copied here - it was
captured with a live credential and contains real candidate data including EEO fields - so it is
used as a **structural** reference only (§8). Every other success shape remains a hypothesis.

Three consequences run through the design:

1. **Scope is limited to what is evidenced.** Of 17 live v2 resources, five operations have a
   usable contract. The rest are route names that answer 401 when they exist and 404 when they do
   not. We ship tools for the five and none for the twelve.
2. **Every success-path response shape is a hypothesis.** The design must fail loudly when a
   hypothesis is wrong rather than degrade into a plausible empty result.
3. **Response handling is defensive by default.** We do not assert schemas we have never seen.

---

## 2. Tool surface

Five tools. `ai/agent-guardrails.md:47-49` requires a minimal allow-list because an unused tool is
attack surface, and the evidence permits no more. (`ai/tool-calling.md:54` uses the same phrase
about loose parameter types, which is a different obligation - §2.1.)

| Tool | Jobvite operation | Kind | Data class |
|---|---|---|---|
| `search_candidates` | `GET /api/v2/candidate` | read | candidate PII |
| `get_candidate` | `GET /api/v2/candidate?candidateId=` | read | candidate PII |
| `search_jobs` | `GET /api/v2/job` | read | public job data |
| `get_job_feed` | `GET /v1/jobFeed` | read | public job data, **separate credential** |
| `create_candidate` | `POST /api/v2/candidate` | **write, destructive** | candidate PII |

`search_candidates` and `get_candidate` are separate tools because **their output cardinality
differs**: `?candidateId=` returns one record, the paged form returns a page. Under
`strict=True` one tool cannot have two return schemas. (The earlier justification - "tighter
schemas" - was the weaker argument.)

**`POST /api/v2/task` is excluded.** It requires an RSA key exchange with Jobvite as a human
onboarding step, uses AES-256-ECB, and its decrypted success shape is unknown. Highest cost,
lowest value, nothing depends on it.

### 2.1 Tool schemas

Every tool takes a typed Pydantic model, never a free-form dict. `strict=True`, extra keys
forbidden, explicit `max_length` on every string, regex on every identifier. Outputs are
snake_case regardless of Jobvite's casing.

**Outputs are allow-listed models, not passthrough.** A field Jobvite returns that is not on the
model does not reach the caller, and it fails closed: a new Jobvite field is dropped until someone
admits it deliberately. That is **containment**, and it satisfies the special-category-data position
(§6.2).

**Containment is not injection-fencing.** They are different controls with different failure modes,
and an earlier revision claimed one mechanism covered both. Allow-listing decides *whether a field
leaves*; fencing decides *how an admitted field is presented to a model* (§6.1). A field can be
correctly admitted and still carry an injection payload.

**The two lists live in different key spaces** - models are snake_case, fencing paths are
camelCase Jobvite paths - so **the fencing paths are generated from the output models** rather than
maintained beside them, and a test fails when any model field has no fencing decision. Two
hand-maintained lists that must correspond is a defect waiting for the first schema change.

### 2.2 `create_candidate` is guarded three ways

It is the only write, it creates real records in a real ATS, its side effect is an email to a
live human, and there is no sandbox. Three independent gates:

1. **Deploy-time.** Not registered unless `JOBVITE_ENABLE_WRITES=true`. Enforced server-side; a
   client cannot bypass it. This is the weakest control conceptually and the only one that is
   unconditionally enforceable, which is why it is kept rather than replaced.
2. **Per-invocation human approval** via MRTR elicitation (§7.5). Fails closed when unavailable.
3. **Confirmation token** (§7.6) as defence-in-depth and as the fallback where the host cannot
   elicit. Needs no client cooperation.

Also: `send_email` defaults to `false`, and the tool is never retried (§4.3).

Annotations: `destructiveHint: true`, `idempotentHint: false`, `readOnlyHint: false`. The other
four are `readOnlyHint: true`. **Annotations are advisory only** - verified: one non-test
reference exists in the entire framework, a field-name alias table, and nothing acts on them. We
set them because a well-behaved host may prompt on them. **The design never counts them as a
control.**

---

## 3. Module layout

```
src/fast_mcp_jobvite/
  __main__.py                 entry; transport selection; signal handling; logging before imports
  server.py                   FastMCP instance, middleware stack, lifespan
  config.py                   pydantic-settings; SecretStr; fails fast on missing config
  errors.py                   exception hierarchy + RFC 9457 problem construction
  audit.py                    the per-invocation audit event (§5.3)
  approval.py                 MRTR elicitation + confirmation tokens (§7.5, §7.6)
  services/jobvite_client.py  httpx2: auth, the error rule, pagination, resilience
  tools/candidates.py         search_candidates, get_candidate, create_candidate
  tools/jobs.py               search_jobs, get_job_feed
  models/                     allow-listed output models, one per tool
  utils/redaction.py          log redaction; untrusted-content fencing
  utils/normalise.py          casing, dates, empty-string/null unification
```

No cache module, no bulk module, no custom logging module. Framework middleware and `loguru`
cover the first and third; the second is speculation.

---

## 4. The Jobvite client

### 4.1 Authentication, and three credential classes

v2 credentials travel as headers, `x-jvi-api` and `x-jvi-sc`. **A URL containing a secret is never
constructed**, even though Jobvite's own published sample code does exactly that.

`GET /v1/jobFeed` is the exception: it structurally requires `api`, `sc` and `companyId` as query
parameters. Its URL is classified sensitive - never logged whole, never in an exception message,
`sc=` redacted before any log line. Enforced in one place, `utils/redaction.py`, with a test that
fails if a secret can reach a log record.

**This gives three credential/data classes, which is also the token-scoping axis (§7.2):**
candidate PII, public job data, and the job feed's separate `companyId` credential.

Credentials are `SecretStr` throughout, resolved with `.get_secret_value()` only when building a
request.

### 4.2 The error-detection rule

**The load-bearing behaviour in this codebase.** `api.jobvite.com` returns `HTTP 200` with a body
of `{"status":{"code":401,...}}`. A client branching on HTTP status reads that as success, finds
no `candidates` key, and reports zero candidates for a rejected credential.

**Invariant:** a response is successful only if the body carries no `status.code >= 400` **and**
the HTTP status is below 400. Both, every call.

The parser cannot assume JSON and cannot dispatch on content type either. **Three error encodings
are handled** on the routes we call: a JSON status envelope, plain text with no `Content-Type`
header at all, and a Tomcat HTML page. **HR-XML is a hardened fallback, not a handled case** - it
appears on `/v1/candidate`, which we do not call. If XML ever arrives it is parsed with
`defusedxml` and treated as an error body; entity expansion on attacker-reachable input is not a
risk worth taking for a route that should never respond to us.

### 4.3 Resilience

Ordered timeout, then retry, then circuit breaker.

- **Timeouts explicit and per-phase.** No SDK default, no single scalar.
- **Retries live inside this module**, via `tenacity` with jitter, budget inside the inbound
  timeout, and only for connection errors, timeouts and 5xx.
- **`create_candidate` is excluded from retry by construction**, not by configuration. This is
  forced: `RetryMiddleware` cannot be scoped to exclude a tool, and narrowing `retry_exceptions`
  does not help because FastMCP wraps tool exceptions as `ToolError(...) from original` and the
  retry check unwraps one level of `__cause__`. Measured: one call, **four rows created**.
- **One circuit breaker for Jobvite. 4xx must not trip it** - a bad candidate id is the caller's
  problem, not a health signal.
- **An open breaker is distinguishable from an outage.** It returns `/problems/jobvite-circuit-open`
  with `status` 503 and a `retry_after` hint, where a genuine upstream failure returns
  `/problems/jobvite-unavailable`. Without distinct slugs a caller cannot tell "Jobvite is down"
  from "we have stopped calling Jobvite", and those need different responses.
- **Jobvite's `429`, if it exists, is retried and then mapped to 503**, honouring `Retry-After`
  when present. No 429 has ever been observed and no rate-limit header is returned (§4.4), so this
  path is written defensively and is unexercised.

### 4.4 Rate limiting

Jobvite returns **no rate-limit headers of any kind**. Nothing to parse, nothing to feed a
backoff calculation, so throttling is client-side and configuration-driven.

**Inbound** throttling uses **FastMCP's own `RateLimitingMiddleware`** - the framework's, not one
we wrote - with four constraints established by execution:

- **`get_client_id` is mandatory.** The default keys every caller to the literal string
  `"global"` despite the docstring implying per-client. One noisy integrator would throttle
  everyone.
- **Burst is sized `desired_calls + 2` per session.** It counts every MCP request, not just tool
  calls. Measured: burst 3 yields 1 tool call, 5 yields 3, 10 yields 8.
- **Limits are startup-only.** Mutating them has no effect; only `limiters.clear()` applies new
  values, **and that resets every client's quota**, making a config reload a quota amnesty and
  repeated reloads a trivial bypass.
- **A trip raises `MCPError`, not an `is_error` result**, so a rate-limit refusal does **not**
  carry an RFC 9457 problem object. §5 states this rather than claiming uniformity it does not
  have.

On stdio there is no token and thus no `client_id`, but there is exactly one caller, so the
global bucket is correct there.

**Every one of those measurements was sequential and single-client.** Bucket behaviour under
simultaneous callers - the case that actually matters in production - is unverified, and
`limiters.clear()` was never tested under load. ADR-0002 records that as a limitation rather than
implying coverage we do not have.

**Outbound, we throttle ourselves against Jobvite's only documented operating envelope**, which is
prose rather than a number: call it on an as-needed basis, and anything more frequent than once a
day must be filtered. That is the sole guidance Jobvite gives. So the client carries a configurable
outbound rate limit with a conservative default, and the README states the envelope, because a user
syncing hourly is outside what the vendor documents and should know it.

The mandated Redis token bucket is not used: the standard's rationale is replica
desynchronisation, and a single-process server has no replicas. **ADR-0002.**

### 4.5 Pagination, and detecting the `start` base at runtime

Offset-based, `start` and `count`. Page cap **500** on v2, **1000** on `/v1/jobFeed`. These are
the *transport* limits. The *result* limit returned to a model is separate and configurable
(§7.7); the two are related by `min(transport_cap, configured_result_cap)`.

**The `start` base is genuinely unresolved** - three third-party clients disagree; the only
statement from Jobvite is its own v1 documentation, which is 1-based. If we are wrong we silently
skip the first record of every page.

**An earlier revision proposed a runtime probe and its logic was inverted.** It read "identical
first ids means the server clamps and either base is safe". That is backwards: identical ids mean
the server is **1-based and clamped 0 to 1**, and clamping protects only page one - a 0-based
caller then re-reads the boundary record on **every subsequent page**. The probe also contradicted
§9 hazard 5: with no stable sort, two requests can return different first ids for reasons having
nothing to do with the base, so the "different ids" branch was unsound in exactly the direction
that looks like successful detection. It cached an indeterminate verdict (a tenant with one
candidate always probes "identical") and applied one verdict across resources whose bases differ.

**What we do instead, and it needs no probe.** `start` is **1-based**, per Jobvite's own v1
documentation, which is the only statement from the vendor. Correctness does not rest on that being
right, because paging is made **base-agnostic**:

- Pages are requested by `start` and every returned record's id is checked against a per-scan seen
  set. **A record already seen is dropped, and a gap is detected and logged.** A 1-off error then
  costs a duplicate read of one boundary record per page, which is invisible to the caller, rather
  than silently skipping a record.
- The base is per-resource, not global. `/v1/jobFeed` is `[OFFICIAL]` 1-based; the v2 resources are
  `[INFERRED]`. They are configured separately.
- `JOBVITE_PAGINATION_START_BASE` overrides per resource for anyone who has established the truth.
- Checklist row 2 still settles it definitively the day a credential exists.

De-duplicating on the way out is cheaper than detecting the base, and unlike a probe it cannot be
fooled by an unstable sort.

Paging terminates on a short page (`len(items) < count`), never on `total`. `total` is reported
and never trusted as a loop condition.

---

## 5. Errors, logging, and correlation

### 5.1 The error contract

Failures return `ToolResult(structured_content=<problem>, is_error=True)` carrying a complete RFC
9457 problem object: `type`, `title`, `status`, `detail`, `instance`, `request_id`, `timestamp`.
No `success: true/false` envelope exists anywhere in this repository.

`type` is a relative `/problems/<slug>`. `instance` is
`urn:fast-mcp-jobvite:invocation:<request_id>`. `status` carries the upstream Jobvite status where
one exists, 400 for input validation, 503 for an upstream 5xx.

**Problem objects are the primary channel for expected conditions** - unknown candidate id,
rejected credential, validation failure. Verified across five arms: because they are *returned*
rather than *raised*, they are untouched by `ErrorHandlingMiddleware`, by `transform_errors`, and
by `mask_error_details`. They are the only error shape no configuration can distort. Raising is
reserved for the genuinely exceptional.

**Three honest exceptions to uniformity**, stated rather than glossed. The third is the most
common and was the last to be admitted:
- A rate-limit refusal raises `MCPError` and carries no problem object (§4.4). **ADR-0002 covers
  this**, because `rate-limiting.md:361-362` separately requires a 429 to use a problem detail, and
  substituting the limiter does not dispose of that clause.
- An abandoned approval never resolves at all (§7.5).
- **An argument-schema violation carries no problem object either.** FastMCP validates arguments
  **before the tool body runs**, so by this section's own reasoning - problem objects are safe
  because they are *returned* rather than *raised* - nothing can return one. The rejection is
  raised by the framework. This is the failure path callers hit most often, so implying uniformity
  here would be the most misleading place to do it. The rejection still fails closed and is
  unit-tested, which is what B12 and B23 actually require.

### 5.2 `problem+json` and the transport

`error-contract.md:44` requires the media type `application/problem+json` on all error responses.
An MCP tool error travels inside a 200 OK JSON-RPC body whose content type the transport fixes.
**That clause is violated in the letter and no implementation can satisfy it: ADR-0003.**

The ADR rests on transport-level auth rejections, which are genuine HTTP responses and do carry
`problem+json`. **There is no health endpoint** - an earlier draft claimed one as mitigation and
none is specified anywhere in this design. Note the consequence honestly: transport-level
rejections exist only on the opt-in HTTP transport, **so on the default stdio transport
`problem+json` is honoured nowhere at all.**

### 5.3 Audit logging and `request_id`

`ai/agent-guardrails.md:40` mandates audit logging of every tool invocation;
`ai/tool-calling.md:171-173` names the fields: tool name, validated arguments with PII redacted,
result status, latency, correlation id.

**We emit this ourselves in `audit.py`, and do not assume middleware provides it.** Three of the
eight framework middlewares exercised shipped a default wrong for this project, so "the framework
probably logs it" is not a basis for a compliance claim. `StructuredLoggingMiddleware` runs with
`include_payloads=False` - for this server those payloads are candidate PII - which means it emits
*no* arguments, not *redacted* arguments. The mandated field is redacted arguments, so we produce
them.

**`request_id` originates here.** MCP has no `X-Request-ID` middleware and no ambient request id.
`audit.py` mints a UUIDv4 per tool invocation, and it is the same value that appears in the
problem object's `request_id` and inside its `instance` URN. Where the HTTP transport receives an
inbound `X-Request-ID`, it is validated as a UUIDv4 before use - unvalidated inbound ids are a
log-forging vector - and echoed.

**The audit event includes `approval_state`.** `agent-guardrails.md:121-123` names it explicitly,
and `create_candidate` is gated three ways and emails a live human - without it, the only record
that a gated write was authorised would not exist. `:79` also requires recording **who** approved,
which §7.5 establishes we can never know: the host may auto-respond with no human present. We
record what we can prove - that an approval response was received and what it said - and
**ADR-0009** records that the identity half is unsatisfiable.

**Audit-write failure has a stated policy, and the third case is the one that matters:**
- **Before the side effect:** fail the call. No audit, no write.
- **On a read tool:** log to stderr and continue. A read is recoverable and losing the tool is
  worse than losing one audit line.
- **After a successful write:** return **success with a warning**, never an error. If a post-write
  audit failure surfaced as an error, the model would retry, and **a second live human would be
  emailed.** The audit hole is the lesser harm and it is recorded as a warning in the same stream.

`mask_error_details=True` is set explicitly at construction; FastMCP defaults it to `False`,
which sends the full text of any unhandled exception to the client. **Masking is client-facing
only**: the full traceback still reaches the server log, so a credential is never interpolated
into an exception message and the log stream is treated as sensitive.

---

## 6. Untrusted and sensitive content

### 6.1 Candidate free text is attacker-authored

Résumé bodies, cover letters, notes and any free-text field a candidate typed are **input from
people outside the operator's organisation, fed directly to a model**. That is exactly the threat
`ai/prompt-injection.md` addresses.

Every such field is fenced before it reaches a tool result, and delimiter tokens occurring inside
the content are stripped so content cannot close its own fence.

**The allow-list is path-keyed with wildcards, not name-keyed.** Name-keying collides: `title` and
`eId` each appear at multiple depths in our own fixtures, and `customField[]` is open-ended. Keys
are paths like `candidates[].application.job.title`.

**Fencing is defined for strings only.** An unknown non-string field is **dropped**, not
stringified - stringifying invents a representation and collides with `strict=True` output models.

Red-team cases live in the main suite and are merge-gating.

### 6.2 Special-category data

Our own fixtures show `gender`, `race` and `veteranStatus` in candidate responses. These are EEO
fields, they are special-category personal data, and left alone they would flow straight to a
model.

**A previous revision justified this by saying the GDPR standard is `priority: optional`. That was
false and checkable.** `architecture/gdpr-data-rights.md:9` reads `priority: required`; corpus-wide
the only `optional` files are twelve README indexes, and no substantive standard is optional. The
research it came from made a *scope* argument, correctly, and the compression into a priority claim
was mine.

**The correct argument is scope.** That standard's obligations attach to systems that **store**
personal data - DSAR policies per table, erasure dispositions, a `gdpr_erasures` table. This server
stores nothing and Jobvite is the controller's system of record, so the DSAR and
right-to-be-forgotten machinery does not reach us. **ADR-0008 makes that argument, not the priority
one.**

**What does bind, and is not waived:** `:119-129`, records of processing under Article 30, is
field-level and names downstream processors. Routing candidate PII to a model is exactly that, so
`docs/data-inventory.md` records the categories handled, the purpose, and the recipients. And the
residue that always binds is no-PII-in-logs, since a log file is the one place a stateless server
can accidentally become a store of personal data.

On the fields themselves: **they are not in any output model and therefore never leave the
server.** The allow-listed output models of §2.1 are the mechanism, and
they generalise - the point is not "drop three fields" but "nothing reaches the model that was not
deliberately admitted."

---

## 7. Server, transport, configuration

### 7.1 Transport

**stdio by default**, HTTP opt-in via `JOBVITE_MCP_TRANSPORT=http`. HTTP binds `127.0.0.1` unless
told otherwise, with `allowed_hosts`/`allowed_origins` set whenever the bind address is not
loopback.

**Off-loopback requires TLS, and the server refuses to start without it.** A non-loopback bind
carries a bearer token and candidate PII over the wire; `allowed_hosts` and `allowed_origins`
address a different threat entirely and do nothing about plaintext. So binding a non-loopback
address without either TLS terminated in front (declared via `JOBVITE_TLS_TERMINATED_BY_PROXY=true`)
or certificates configured here is a startup failure, not a warning. Outbound to Jobvite is HTTPS
with `httpx2`'s default verification, and verification is never disabled.

**Sessionless `2026-07-28` is the default era**, with the handshake era served simultaneously -
verified on one server, one port. Two deployment consequences:
- Any reverse proxy, load balancer or WAF must pass `mcp-method`, `mcp-name` and
  `MCP-Protocol-Version` through untouched. A proxy stripping unknown headers breaks the server in
  a way that looks like our bug.
- `server/discover` advertises only `2026-07-28` even though handshake-era clients are served.

### 7.2 Authentication and scopes

HTTP auth uses `StaticTokenVerifier` built from environment at startup. **Scopes follow the three
data classes of §4.1**: candidate PII, public job data, and the job feed. That axis survives
regardless of the tool set; the earlier axis - "a read-only token never sees the write tool" -
collapsed whenever the write was out of scope.

**`require_scopes` removes an unauthorised tool from `tools/list` entirely**, and a direct call
returns "Unknown tool", not a permission error. Good behaviour, confusing failure mode; the README
documents it or every support conversation starts in the wrong place.

**stdio is unauthenticated by design.** Anything able to spawn the process can call its tools; the
trust boundary is the operating system's, not this server's. That is the correct model for a local
subprocess, and it is stated rather than left implicit. It also means `create_candidate` on stdio
rests on the deploy-time flag plus approval, not on scopes.

### 7.3 Configuration

`pydantic-settings` owns required-config validation. `fastmcp.json` **cannot** express a required
environment variable: with one unset the server starts normally and the tool receives the literal
string `${JOBVITE_API_KEY}`, surfacing later as a confusing Jobvite 401. A missing credential must
fail at boot, naming the variable. `server.json` declares variables for registry consumers;
pydantic-settings enforces them.

**Configuration is scoped to the tools actually enabled**, and the enable surface is defined here
rather than presupposed. `JOBVITE_TOOLS` is a comma-separated allow-list of tool names; unset means
all read tools. `JOBVITE_ENABLE_WRITES` additionally gates `create_candidate` (§2.2) and is
independent, so a write cannot be enabled by naming it alone.

Fail-fast validates what each *enabled* tool requires, never the union - a deployment using only
candidate search must not be forced to invent a `companyId` it has no use for:

| Tool | Requires |
|---|---|
| `search_candidates`, `get_candidate` | `JOBVITE_API_KEY`, `JOBVITE_API_SECRET` |
| `search_jobs` | `JOBVITE_API_KEY`, `JOBVITE_API_SECRET` |
| `get_job_feed` | `JOBVITE_FEED_KEY`, `JOBVITE_FEED_SECRET`, `JOBVITE_COMPANY_ID` |
| `create_candidate` | the v2 pair, plus `JOBVITE_ENABLE_WRITES=true` |

`server.json` declares every variable for registry consumers; pydantic-settings enforces only the
subset the enabled tools need.

### 7.4 Lifespan and shutdown

`from fastmcp.server.lifespan import lifespan` with `|` composition; startup in order, teardown in
strict reverse, verified.

**Lifespan teardown does not run under SIGTERM** - only SIGINT. Verified 3 of 3 with process
identity checks, and reproduced on the previous major, so it is longstanding rather than a 4.0
regression. Docker, Kubernetes and Cloud Run all stop containers with SIGTERM. Filed upstream as
[#4927](https://github.com/PrefectHQ/fastmcp/issues/4927).

**The obvious mitigation is actively dangerous and we do not use it.** An earlier draft proposed
`signal.signal(SIGTERM, signal.getsignal(SIGINT))`. Both doubts the review raised were correct, and
executing it found a third problem worse than either:

- **`getsignal(SIGINT)` returns whatever is installed at that moment.** A backgrounded process
  inherits `SIGINT = SIG_IGN`, so the one-liner installs **"ignore SIGTERM"** - the opposite of the
  intent. In a container that means the process does not stop on `docker stop` and is SIGKILLed
  after the grace period, **guaranteeing no teardown at all.** Its behaviour depends on ambient
  state that differs between a shell job, a foreground terminal, and PID 1.
- **Uvicorn does overwrite both handlers** during `run()`, confirmed from inside a live server. So
  the one-liner is a no-op while the server runs. Teardown happened anyway only because uvicorn's
  `capture_signals` *restores* the original handlers and *re-raises* the captured signal. **We
  would have been depending on a uvicorn implementation detail while believing we handled SIGTERM.**
- **On stdio there is no uvicorn at all**, and teardown runs but **the process does not die** - a
  non-daemon AnyIO worker thread blocks interpreter shutdown, so even an explicit `sys.exit(0)`
  never completes.

**The verified implementation** installs an explicit handler rather than copying SIGINT's, and
forces exit after teardown:

```python
def _install_shutdown_handler() -> None:
    # Do NOT use signal.getsignal(SIGINT): it returns whatever is installed at that
    # moment, which is SIG_IGN for a backgrounded process - installing "ignore SIGTERM".
    def _term(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, _term)

# in main(), after mcp.run(...) inside try/except KeyboardInterrupt:
finally:
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(0)   # a non-daemon AnyIO thread blocks sys.exit() on stdio
```

Teardown completes before `os._exit`, so skipping atexit handlers costs nothing we rely on.

**The test must assert both halves, on both transports:** that the teardown marker was written
**and** that the process exited within the grace period, signalling the interpreter PID resolved
via `/proc/<pid>/cmdline` rather than a wrapper. The HTTP path passes on teardown alone; **only
stdio catches the exit failure**, which is precisely why a single-transport test would have shipped
this bug.

**The rule that survives regardless of the mitigation, and it belongs at the lifespan definition
in `server.py` rather than in a review:** even when teardown runs, it runs *after* connections are
gone. **Nothing that must complete before connections close may live in a lifespan teardown.**
Today nothing depends on teardown - the only resource is a connection pool the OS reclaims - which
means the constraint is free now and will be violated by the first person who adds a metrics flush
or an audit-log write. §5.3's audit event makes that more likely, not less.

### 7.5 Human approval (MRTR)

Server-initiated elicitation is unavailable on the sessionless era by design. **The sanctioned
replacement is Multi Round-Trip Requests**: the tool returns an `InputRequiredResult` carrying an
`elicitation/create` request, and the client retries the original call with `inputResponses`
attached. Verified end to end on our default era: approve writes, deny refuses with the row count
unchanged, no client handler fails closed.

Implementation: the tool inspects `ctx.input_responses` - `None` on the first leg, populated on
the retry. Accessors are `ctx.input_responses` and `ctx.request_state` on `Context`, **not** on
`request_context`.

**The guard must check the action AND the value:**
`action == "accept" and content.get("approve") is True`. An *accepted* elicitation carrying
`approve: false` is still an acceptance. This conjunction is not optional and has its own test
with a deny arm and an accept-carrying-false arm.

**The two mechanisms are exactly complementary, and a single-mechanism guard is broken on one era
whichever it picks.** Executed on both:

| Era | MRTR | `ctx.elicit()` |
|---|---|---|
| sessionless `2026-07-28` | works | raises |
| handshake `2025-11-25` | **raises, every arm including approve** | works |

FastMCP's own error names the remedy: the multi-round-trip result type "only exists at MCP
2026-07-28 ... Use `ctx.elicit()` for server-initiated input on handshake-era connections."

**This matters most where most users are.** Claude Code negotiates `2026-07-28` automatically over
HTTP, but for stdio only when `MCP_PROTOCOL_NEGOTIATION=auto` - so **a default stdio install lands
on the handshake era**, and a sessionless-only guard would be broken for the majority of local
users while passing every test we had.

**The discriminator is `ctx.request_context.protocol_version`**, compared against the same
`('2026-07-28',)` tuple FastMCP's own guard uses. Two plausible alternatives were measured and both
are traps: `ctx.transport` is **identical** on both eras (`'streamable-http'`), and `session_id` is
**populated on both** despite one era being called sessionless. `ctx._is_modern_protocol()` works
but is private.

**An earlier revision branched on whether `ctx.input_responses` exists. That branch was inert** -
`input_responses` and `request_state` are class-level properties, so `hasattr` is True on every era,
and `is not None` is already spent telling the first leg from the retry. It looked like handling,
which is why nobody looked further. The premise underneath it had never been measured on the
handshake era at all.

**What we may honestly claim.** A host can auto-respond to elicitation without showing anyone a
dialog. The MCP specification places human-in-the-loop confirmation on the host, not the server.
So the claim is *"the server requires an approval response from the host and refuses to write
without one"* - **never** *"a human approved this."*

**Liveness, for the README:** the write is safe on every refusal path including abandonment, with
`rows=0` independently confirmed. But an abandoned approval **hangs the call**, and a client-side
timeout does not bound it, because the elicitation handler runs in the client's own process. "The
write silently never completes" is a confusing failure mode and integrators are told about it.

### 7.6 Confirmation tokens

The fallback where a host reports "Elicitation not supported", and defence-in-depth otherwise.
A preview call returns a short-lived token describing exactly what would be written; the write
requires it. HMAC-bound to the payload, so a token minted for candidate A does not authorise
writing candidate B. Forged, replayed, argument-mismatched and expired tokens are each refused
with distinct messages.

Its honest limit: it forces a deliberate two-step, but an autonomous agent can call preview then
create with no human anywhere. **It enforces confirmation, not human confirmation.**

**`ResponseCachingMiddleware` must never touch the preview tool.** A cached preview re-issues the
*same* token, so once spent the cache keeps serving a dead token for its whole TTL and the write
becomes unusable. It fails closed but it is a self-inflicted denial of service. The preview tool
is annotated `readOnlyHint=True`, which makes it exactly the tool someone would naively cache.

### 7.7 Middleware

Adopted, each constructed with explicit arguments: `Timing`, `StructuredLogging` with
`include_payloads=False`, and `RateLimiting` with `get_client_id`.

**`ResponseCachingMiddleware` is NOT adopted, and this reverses an earlier revision.** Three facts
from this design decide it: the cacheable responses are candidate PII (§2); §7.2's three scopes
exist precisely so different callers see different data; and §4.4 **measured** that this
framework's sibling middleware defaults every caller to the literal string `"global"` while its
docstring implies per-client. `architecture/caching.md:833` requires cache keys namespaced by
tenant or user and `:841` names un-namespaced user-specific caching as a Don't. If the cache keys
without client identity, a candidate-PII-scoped result can be served to a public-job-data token,
defeating §7.2 entirely through one middleware line.

We have not executed its key derivation, and the honest position is that we do not need to: **the
only benefit is latency against an upstream nobody has ever successfully called.** Dropping it
removes the scope-crossing risk and the spent-token hazard (§7.6) in one edit. If a cache is ever
wanted, its key derivation must be established by execution the way §4.4 established the limiter's,
and a test with two differently-scoped tokens must prove isolation before it ships.

Not used: `ResponseLimiting` (broken - raises on any tool with a return annotation, filed as
[#4926](https://github.com/PrefectHQ/fastmcp/issues/4926)), `ErrorHandling` (its default converts
a caller's input problem into a raised server fault), `Retry` (§4.3), `Ping` (inert on our era).

**Design rule, earned rather than assumed: on this framework a middleware's default is not a safe
starting point.** Four of the eight exercised were unusable or needed their defaults overridden.
No middleware is adopted on the strength of its documentation, and each one's arguments are
justified here.

**Result size is bounded inside each tool**, not by middleware: a page is capped and the result
says `showing 50 of 1,240`. That is more useful to a model than a truncated JSON blob. The cap is
configuration, not a constant.

---

## 8. Testing

The default suite runs with no network and no credentials, and CI has **zero skips** - a skip
counts as a failure, so credential-dependent tests are excluded by *selection*, not marked
`skipif`.

**The live suite must be collected even though it is not run.** A suite that is excluded and never
collected rots silently: an import error or a renamed fixture in it is invisible until the day
someone finally has a credential. CI runs `--collect-only` against it and fails on a collection
error.

**Fixtures are in three tiers, and the split is load-bearing:**
- **Recorded** - byte-exact captures of real Jobvite error transport. Assert verbatim.
- **Structural** - the one genuine `200` (§1.1). Its body cannot ship, since it holds real
  candidate data, so we assert its *shape*: envelope keys, types, nesting, and whether a success
  body carries a `status` block. That last point already answers what was an open question.
- **Synthetic** - every other success body. Hypotheses in JSON.

**A suite passing only against synthetic fixtures proves the client is self-consistent, not that
it speaks Jobvite.** That sentence is in the test module's own docstring so nobody mistakes green
for verified. `docs/CREDENTIAL-CHECKLIST.md` converts each synthetic fixture to a recorded one
when a key lands; rows 1-4 are blocking.

Required cases, each failing if its defence is removed:
- the 200-with-401-body trap;
- a secret never reaching a log record, including the `jobFeed` URL;
- untrusted-content fencing, including content that tries to close its own fence;
- an unknown non-string field being dropped rather than stringified;
- `create_candidate` not retrying on timeout;
- approval: deny refuses, accept-carrying-false refuses, no-handler fails closed, and the second
  leg actually consumes `ctx.input_responses`;
- token replay, expiry, and payload mismatch each refused;
- a 4xx not tripping the circuit breaker;
- the `eId`/`EId` casing asymmetry pinned, so a later refactor cannot tidy it into a bug;
- **approval on BOTH eras**, because the no-handler arm surfaces differently on each: sessionless
  raises `MCPError`, handshake returns `is_error=True` with a masked message. A test asserting
  `pytest.raises(MCPError)` passes on one era and fails on the other. **The test asserts the
  invariant that matters - the row count did not change - not the error shape.**

Transport substitution uses `httpx2`'s built-in `MockTransport`. No third-party mocking library is
required, which matters because a credential-free test strategy cannot afford to depend on one.

Coverage: 80% floor overall, 85% tool modules, 90% the Jobvite client, 95% line and 90% branch on
critical paths (auth, argument rejection, the error rule, approval, the write).

**A guard that refuses everything is not a guard, and its refusals prove nothing.** Every
refusal-path test is paired with a positive control showing the happy path still succeeds.

---

## 9. Known contract hazards

Jobvite's, not ours, each needing explicit handling:

1. **Casing asymmetry.** Reads return `eId`; the create response returns `EId`. Normalised at the
   boundary, pinned by a test.
2. **Date asymmetry.** Requests take `yyyy-MM-dd` strings; responses return epoch milliseconds.
3. **Three names for one concept.** v2 jobs key on `requisitions`, the v1 feed on `jobs`, the
   create response nests under `application`.
4. **Empty strings where nulls belong.** Phone fields use `""`. Treated identically at the
   boundary.
5. **No stable sort.** No sort parameter is documented, so a long paged scan over a mutating set
   may duplicate or skip. Bounded date windows are preferred to full-catalogue walks.
6. **Duplicate creates return `409`, and none of §2.2's gates prevent one.** All three gates stop
   an *unauthorised* write; none stops an *authorised* write being made twice - a model calling the
   tool again after a timeout, or a user approving twice. The `409` shape is `[INFERRED]` and never
   observed. So `create_candidate` surfaces a `409` as `/problems/jobvite-duplicate-candidate`
   rather than a generic failure, and never retries (§4.3). This is a real residual risk, not a
   solved one: we can report a duplicate, not prevent it.
7. **Route-level 404s.** `404 "Invalid URL Cannot find API."` means the route does not exist, not
   that a record was not found. The record-level not-found shape is unknown.

---

## 10. Repository and delivery

Canonical at `evolvconsulting/fast-mcp-jobvite`, mirrored to `Aztec03hub/fast-mcp-jobvite`.
Apache-2.0, `Copyright 2026 evolv Consulting`, with a NOTICE.

Python `>=3.12`. `fastmcp==4.0.0b4` targeting the sessionless `2026-07-28` spec as deliberate
early adopters. **`mcp` is pinned explicitly**, not just `fastmcp`: the `ResponseLimiting`
regression arrived through the transitive SDK with zero change to the code that broke, which is
the characteristic failure mode of early adoption on a freshly major-bumped dependency.

Packaging, verbatim, because both lines are load-bearing:

```toml
dependencies = [
  "fastmcp==4.0.0b4",
  "fastmcp-slim==4.0.0b4",   # transitive prerelease; must be named or resolution fails
  "mcp==2.1.1",              # the transitive SDK that broke a middleware with no code change
]

[tool.uv]
prerelease = "explicit"
```

**A previous revision claimed in prose that `mcp` was pinned and then omitted it from this block**,
which was presented as verbatim. Anyone implementing that block exactly would have reproduced the
regression class the paragraph exists to prevent.

**The lockfile is the actual cure and it was missing.** This section argues that a transitive bump
broke code with zero change to that code, then pinned three packages by hand - which diagnoses the
disease and does not prescribe the remedy. `uv.lock` is committed, CI runs `uv sync --frozen`, and
the SBOM is generated from that frozen resolve. An SBOM produced from an unfrozen resolve documents
a build nobody shipped.

`--prerelease=allow` is global in uv and pulls in a beta pydantic; `explicit` alone fails to
resolve because `fastmcp-slim` arrives transitively. Naming it directly resolves pydantic to
stable.

**HTTP client is `httpx2`, the same one FastMCP ships: ADR-0007.** One HTTP stack in the image,
not two.

An earlier revision chose `httpx` on the belief that httpx2 was "a fork with a much smaller
ecosystem" whose mocking support was unproven. **That characterisation was wrong and was never
checked.** Verified:

- `httpx2` is authored by **Tom Christie, httpx's own author**, and published under the
  **pydantic** organisation. Its README states plainly that *"With HTTPX itself seeing limited
  activity recently, Pydantic is picking up stewardship under the HTTPX2 name so that users have a
  reliably maintained path forward - including timely security updates."*
- It is **the maintained continuation**, not a competitor. Releases through 2.12.0 in August 2026;
  `httpx` itself has shipped only `1.0.devN` prereleases.
- It ships `httpx2/_transports/mock.py`. **`MockTransport` is built in**, so the entire premise -
  that our credential-free test strategy would rest on unproven mocking - was false. We need no
  third-party mocking library at all.

Choosing `httpx` would have meant two HTTP stacks and two TLS surfaces in one image, a dependency
with limited activity in the critical path, and a silent hazard we would have invented ourselves:
`except httpx.HTTPError` can never catch a FastMCP-raised exception. Adopting httpx2 removes that
hazard rather than guarding it, so the module-confinement rule and its AST test in §8 are dropped
as unnecessary.

CI: lint, format, types, tests, plus `pip-audit`, CodeQL, TruffleHog with full history depth, SBOM
in both formats, and a `pip-licenses` allow-list gate. `fastmcp inspect` output is emitted and
**diffed between builds**, so capability drift arriving through a dependency bump is visible in
review rather than at runtime. **UNVERIFIED:** that this actually catches the drift it is meant to
catch is reasoning, not an executed result - the `ResponseLimiting` regression is the case it is
modelled on, and nobody has replayed that bump against this check.

**Two commit-time gates, both exceeding the standard deliberately:**
- Secret scanning pre-commit, not only in CI. On a public remote a pushed secret is compromised
  the instant it lands.
- **A committed-file-type gate.** A CONFIDENTIAL PDF has no high-entropy token and matches no
  credential regex, so it passes every secret scanner cleanly - the control we had named as
  preventing that incident could never have caught it. Allowlist-first, extension denylist,
  magic-number sniffing, NUL-byte backstop, fail-closed, overrides only via an allowlist entry in
  the same commit so the exception is reviewable in the diff.
  **Its limit, stated so it is not over-trusted:** it stops a *file* of the wrong type entering the
  repository. It does nothing about confidential prose pasted into Markdown, which is the incident
  we actually had. Review and `JOBVITE-API.md` §0.2 cover that.

---

## 11. Open questions

1. **A Jobvite credential.** Converts every synthetic fixture to a recorded one. Blocking for any
   claim that this is verified against Jobvite.
2. **The `start` base.** Now probed at runtime (§4.5), but the probe itself is unverified against
   a live server.
3. **The record-level not-found shape.** Unknown.
4. **Whether success bodies carry a `status` block at all.** The parser tolerates both.
5. **Whether Claude Desktop supports elicitation.** No first-party statement found; secondary
   sources conflict and are not relied upon.
6. **Shutdown depends on a uvicorn implementation detail** (§7.4). Our handler works because
   uvicorn restores and re-raises; that is behaviour uvicorn does not guarantee. Recorded as a
   known dependency rather than left as an assumption, and the shutdown test would catch a
   regression.

All are external unknowns. None is a reasoned-but-unexecuted claim about our own stack.

---

## 12. ADRs required at freeze

- **ADR-0001** - target `fastmcp 4.0.0b4` and the sessionless spec rather than the stable line.
- **ADR-0002** - in-process rate limiting instead of the mandated Redis token bucket. **Scope
  includes** `rate-limiting.md:361-362` (a 429 must use a problem detail, and ours raises
  `MCPError`), rule 5's `RateLimit-*` response headers, and the limitation that every supporting
  measurement was sequential and single-client.
- **ADR-0003** - `problem+json` cannot be set on an MCP tool error; scope and consequences.
- **ADR-0004** - `ResponseLimitingMiddleware` excluded; size bounded in-tool.
- **ADR-0005** - the `ai/` standards domain binds this repository by intent.
- **ADR-0006** - single `main` branch rather than the mandated `main`+`develop`. **Scope includes**
  B97 branch *naming*, which the branch-model deviation does not touch, and the "merge only from
  develop or hotfix" clause the deviation necessarily voids. B99's four properties - PR, approval,
  CI green, currency, squash - **relocate onto `main`** rather than retiring.
- **ADR-0007** - `httpx2` rather than `httpx`, matching what FastMCP ships.
- **ADR-0008** - special-category EEO fields excluded from output models, **on scope grounds**:
  `gdpr-data-rights.md` is `priority: required` and its DSAR/RTBF machinery attaches to systems that
  store personal data, which this is not. Article 30 records-of-processing is separately satisfied
  by `docs/data-inventory.md`.
- **ADR-0009** - the audit log records that an approval response was received and what it said, but
  cannot record **who** approved, because a host may auto-respond with no human present.
  `agent-guardrails.md:79` requires the identity and it is unsatisfiable on this transport.
- **ADR-0010** - coverage targets remapped from the standard's category model, which has no
  category matching an MCP tool module. Loosening a mandated coverage number is exactly what this
  mechanism exists to record.

**Freeze procedure, and one step exists because it already failed once:** every **conditional**
dismissal in the standards analysis is re-tested at freeze. `architecture/caching.md` was dismissed
as "optional here; if a cache is added it becomes live", a cache was then added, and nothing
re-evaluated it - the condition tripped silently and it took a second sweep to notice. **A
conditional dismissal is a dated claim about the design, not a permanent verdict.**
`devops/docker.md` and `backend/idempotency.md` are the two most likely to have gone live.
