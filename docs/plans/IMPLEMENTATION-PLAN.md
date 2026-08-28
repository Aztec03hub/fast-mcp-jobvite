# fast-mcp-jobvite - Implementation Plan

Status: **DRAFT 1.** Not reviewed. Written against `docs/DESIGN.md` revision 5 (last updated
2026-08-28 02:01 PM CDT), which has no open Critical, High or Medium findings and an empty
must-mitigate table (`DESIGN.md:1714`).

**The design is authority.** Nothing here changes it. Where I believe the design is wrong or
incomplete, it is recorded in [§9 Questions for the design](#9-questions-for-the-design) and
nowhere else - there are no silent workarounds in this plan, and every open item that blocks a
work unit is named at the unit that it blocks.

**Scope of this document.** It is an ordered set of work units with dependencies and verification.
It contains no code. It does not estimate effort or duration.

---

## 0. Two facts about the repository, established before planning

**`src/` and `tests/` are empty. Zero files.** Everything below is greenfield.

**There is no CI.** `.github/workflows/` contains exactly one file, `mirror.yml`, which pushes to
the mirror remote. **The brief I was given states that the gate scripts in `docs/reviews/` already
run in CI. They do not - no workflow invokes them.** `DESIGN.md:1362` says *"CI runs `python3
docs/reviews/check-coupling.py docs/DESIGN.md"*, which is a statement of what CI must do, not a
record of what it does. I ran the gate by hand against the current document:

```
docs/DESIGN.md: 60 STRIDE rows, 17 Critical/High (16 mitigated by the roster's reckoning, 1 not);
all 60 rows checked for disposition, 23 naming a §8 case.
PASS: ...
exit=0
```

So the gate passes today and has never been enforced by a machine. **Standing it up is part of
U0**, and from U0 onward "the gate keeps passing" is a real constraint rather than an aspiration.
The two harnesses beside it - `check-coupling-controls.py` (21 hand-written mutations) and
`check-coupling-sweep.py` (the subject-free sweep that found 19 escapes the controls missed) -
are what prove the gate can fail, and both must run in CI too, or the gate is a checker that has
only ever passed, which its own docstring names as the failure it exists to avoid.

---

## 1. The count that governs the test plan

§8's required-cases list holds **24 bullets** (`DESIGN.md:1174` through `:1253`), not "about 25".
I enumerated them mechanically rather than by eye. Several are multi-arm and are **not satisfiable
by a single arm**, which the list says in its own text:

| # | §8 line | Case | Arms it explicitly requires |
|---|---|---|---|
| 1 | `:1174` | the 200-with-401-body trap | - |
| 2 | `:1175` | a secret never reaching a log record, including the `jobFeed` URL | - |
| 3 | `:1176` | `.gitignore` covers the credential patterns, `.env.example` carries no real value | asserted against committed files |
| 4 | `:1180` | the audit event is emitted and carries its mandated fields | **positive on purpose**; paired with #5 |
| 5 | `:1186` | candidate PII never reaching a log or audit record | asserted **against the event #4 proves exists** |
| 6 | `:1190` | EEO fields never appearing in any tool result | asserted against the output models |
| 7 | `:1192` | an argument-schema violation failing closed | - |
| 8 | `:1194` | control character / bidi override rejected before dispatch | **+ positive control**: an ordinary name passes |
| 9 | `:1198` | argument payload exceeding a structural limit rejected | **four arms**: depth>5, list>1000, dict keys>100, body>1 MiB |
| 10 | `:1200` | off-loopback bind without TLS refuses to start | exits naming the reason, not a warning |
| 11 | `:1204` | manifest pins `mcp`; frozen resolve has no lock drift | `uv lock --check` + `==` pin present |
| 12 | `:1209` | an undeclared pytest marker fails collection | **+ positive control**: the declared marker still selects |
| 13 | `:1214` | retry and breaker lines carry the invocation's own `request_id` | **concurrent arm is the case**; single-call is insufficient. Also asserts no URL in a retry line |
| 14 | `:1220` | read-only-key requirement present in `CREDENTIAL-CHECKLIST.md` and in README | README arm **gated on file presence, never skipped** |
| 15 | `:1227` | an expired advisory-ignore entry fails the audit gate | **+ positive control**: an unexpired entry is honoured |
| 16 | `:1231` | `request_id` present on every result, success and error | **four arms**: successful read, successful write, audit-failure warning branch, error. Each **on the wire result**, not on `ToolResult` |
| 17 | `:1238` | trace context recorded when supplied, absent when not | **two arms, both required** |
| 18 | `:1243` | untrusted-content fencing, including content closing its own fence | - |
| 19 | `:1244` | unknown non-string field dropped, not stringified | - |
| 20 | `:1245` | `create_candidate` not retrying on timeout | - |
| 21 | `:1246` | approval: deny, accept-carrying-false, no-handler, second leg consumes `input_responses` | **four arms** |
| 22 | `:1248` | a 4xx not tripping the circuit breaker | - |
| 23 | `:1249` | the `eId`/`EId` casing asymmetry pinned | - |
| 24 | `:1250` | approval on **both eras** | asserts **row count unchanged**, not error shape |

Plus the blanket rule at `DESIGN.md:1266-1267`: **every refusal-path test is paired with a positive
control showing the happy path still succeeds.** That applies to #1, #7, #8, #9, #10, #12, #15, #20,
#21, #22 and #24, not only where the bullet says so.

**One required test lives outside this list.** `DESIGN.md:947-950` states the SIGTERM/exit test as
*"a requirement rather than a suggestion"*, on both transports, asserting both the teardown marker
and that the process exited. It is not a §8 bullet and no §11 row names it, so `check-coupling.py`
cannot see it. It is scheduled in **U1** regardless, and the coupling gap is [Q2](#q2).

### Fixture tiers

`DESIGN.md:1161-1172`. Three tiers, and the split is load-bearing:

- **Recorded** - byte-exact captures. Six exist already: `error_auth_401.json`,
  `error_auth_200_body401.json`, `error_route_404.json`, `error_task_400.html`,
  `error_v1_auth_401.txt`, plus the two malformed bodies. **Assert verbatim.**
- **Structural** - the one genuine `200` (`JOBVITE-API.md:393-399`). **Its body cannot ship**, so
  there is no fixture file and there must never be one. This tier is a set of *shape assertions*
  written from the recorded description: the envelope is
  `{"candidates":[...],"total":<int>,"status":{"code":200,"messages":[]}}`, a success body **does**
  carry a `status` block, `total` is the full result-set size and not the page size, and `start=0`
  is accepted and returns records.
- **Synthetic** - `candidate_list_success.json`, `candidate_list_empty.json`,
  `candidate_create_success.json`, `job_list_success.json`, `job_list_empty.json`,
  `jobfeed_success.json`, `jobfeed_empty.json`, `candidate_list_injection.json`. **Hypotheses in
  JSON.**

**The sentence at `DESIGN.md:1168-1169` goes in the test module's own docstring, verbatim in
substance:** a suite passing only against synthetic fixtures proves the client is self-consistent,
not that it speaks Jobvite.

**Sequencing consequence that a naive plan gets backwards:** the structural assertions must be
written **before** the candidate output models (U8), or the models will encode the shape of
fixtures we invented rather than the one success envelope anyone has actually observed. This is the
single clearest place the credential-free constraint reorders the work.

### Zero skips

`DESIGN.md:1139-1159`. CI has zero skips; a skip is a failure. Credential-dependent tests are
excluded **by selection** through a declared marker under `--strict-markers`, and **the excluded
suite is still collected** (`--collect-only`, failing on a collection error). All three properties
land in U0, because every later unit that adds a credentialed arm depends on them existing.

---

## 2. Work units, in order

Each unit states what it builds, the governing design section, what it depends on, and **how it is
verified**. No unit is verified by "it compiles".

---

### U0 - Repository skeleton, pinned manifest, test selection, CI

**Builds.** `pyproject.toml` with the verbatim three-pin block and `prerelease = "explicit"`
(`DESIGN.md:1312-1321`); `uv.lock` committed; `[tool.pytest.ini_options]` with
`addopts` carrying `--strict-markers`, the declared `markers` list including the
credential-dependent marker, `asyncio_mode = "auto"`, and coverage `branch = true`
(`DESIGN.md:1144-1145`); coverage floors per ADR-0010 (80% overall, 85% tools, 90% client,
**95% `utils/`**, 95 line / 90 branch on critical paths); `.github/workflows/ci.yml`.

CI runs, at minimum: `uv sync --frozen`; lint; format; types; the default suite;
`--collect-only` against the credentialed suite; `python3 docs/reviews/check-coupling.py
docs/DESIGN.md`; `check-coupling-controls.py`; `check-coupling-sweep.py`; `pip-audit` behind
`scripts/check_advisories.py` (U11); CodeQL; TruffleHog with full history depth; SBOM in both
formats from the **frozen** resolve; `pip-licenses` allow-list; `fastmcp inspect` emitted and
diffed between builds. Pre-commit: secret scanning and the committed-file-type gate
(`DESIGN.md:1495-1505`).

**Depends on.** Nothing.

**Verified by.** §8 cases **#11**, **#12** and **#3** - all three are runnable today with no `src/`
at all, and all three fail if their defence is removed:

- #11: assert `mcp` present with an `==` pin in `pyproject.toml`, and `uv lock --check` exits 0
  without amending `uv.lock`.
- #12: invoke pytest against a file marked with a name absent from `markers`, require non-zero exit;
  positive control - the declared marker still selects its tests.
- #3: assert against the committed `.gitignore` (currently covers `.env`, `.env.*`, `*.key`,
  `*.pem`, `secrets/`) and that every value in `.env.example` is empty.

Plus: the coupling gate exits 0, the controls harness reports all 21 controls firing, and the sweep
reports only the designed Medium/Low exemptions.

**Note.** `DESIGN.md:1306-1310` records that the three-pin block was resolved on its own and holds
`pydantic` at a stable 2.13.4. Reproduce that resolve; if it does not reproduce, that is a finding
about the ecosystem, not a licence to unpin.

---

### U1 - Boot: config, transport selection, TLS refusal, shutdown

**Builds.** `config.py` (pydantic-settings, `SecretStr`, per-enabled-tool required-variable
validation per `DESIGN.md:880-885`, `JOBVITE_TOOLS` allow-list with an unrecognised name as a
**startup failure**, the `JOBVITE_ENABLE_WRITES` AND `JOBVITE_TOOLS` conjunction in both
directions per `:865-869`); `__main__.py` (transport selection, `_install_shutdown_handler()`,
`os._exit(0)` in `finally`, logging configured before imports); `server.py` (the `FastMCP`
instance, `mask_error_details=True` set explicitly, lifespan via `from fastmcp.server.lifespan
import lifespan` with `|` composition); the off-loopback TLS refusal of `:752-756`;
`server.json` declaring every variable for registry consumers.

**Depends on.** U0.

**Verified by.**

- §8 **#10**: off-loopback bind, no certificates, `JOBVITE_TLS_TERMINATED_BY_PROXY` undeclared -
  the process **exits naming the reason**. Positive control: loopback bind starts; off-loopback
  with the assertion declared starts. Three High rows (C1-S1, C1-T1, C1-I1) rest on this refusal.
- **The §7.4 shutdown test, both halves on both transports** (`DESIGN.md:947-950`): a teardown
  marker was written **and** the process exited within the grace period, with the interpreter PID
  resolved via `/proc/<pid>/cmdline` rather than a wrapper. **Only the stdio arm catches the exit
  failure**; the HTTP arm passes on teardown alone.
- Config fail-fast: per-tool required-variable matrix asserted row by row, including the negative -
  a deployment enabling only `search_candidates` must **not** be forced to supply
  `JOBVITE_COMPANY_ID`.
- An unrecognised `JOBVITE_TOOLS` name fails startup; positive control - a recognised name starts.
- `JOBVITE_ENABLE_WRITES=true` with `JOBVITE_TOOLS` unset does **not** register the write.

**Inherited limits, not quietly resolved.** `DESIGN.md:936-944` states two: the composed
handler-plus-`os._exit` snippet **has never been run end to end on HTTP**, and **PID 1 was never
simulated**. The test above is what closes both, and until it runs green the plan carries them as
open. §12 item 5 additionally records that shutdown depends on a uvicorn implementation detail.

**Blocked on a design decision.** See [Q1](#q1): §7.7's result cap and §4.4's outbound rate limit
are specified as configuration and **have no name and no default** (B15, `DESIGN.md:1448-1452`).
`config.py` cannot enumerate the settings without them, and `.env.example` is specified as the
single enumeration everything else is checked against. U1 can ship without them only if the two
settings are deferred to the units that consume them (U6/U7), and `.env.example` then knowingly
remains incomplete, which the design already says it is.

---

### U2 - The error contract and the correlation ContextVar

**Builds.** `errors.py` - the exception hierarchy and RFC 9457 problem construction, with `type`
and `status` taken **from the registry at `error-contract.md:96-108`**, never from Jobvite
(`DESIGN.md:475-498`). `utils/correlation.py` - a single `ContextVar[str | None]` named
**`request_id_var`**, that name mandated verbatim by `ai/tool-calling.md:173-175`
(`DESIGN.md:568`).

**Depends on.** U0. (Independent of U1.)

**Verified by.**

- A table-driven test over all seven registry rows: a Jobvite 401 maps to
  `/problems/external-service-error` **502**, not 401; validation is **422**, not 400; unmapped is
  `about:blank`.
- `instance` is `urn:fast-mcp-jobvite:invocation:<request_id>` and `request_id` matches it.
- All seven members present: `type`, `title`, `status`, `detail`, `instance`, `request_id`,
  `timestamp`.
- Jobvite's own status and message appear in `detail` and are **not discarded**.
- A repository-wide assertion that **no `success: true/false` envelope exists anywhere**
  (`DESIGN.md:470`).
- Problem objects are **returned, never raised** - the property `DESIGN.md:502-504` says makes them
  the one error shape no configuration can distort.
- `request_id_var` resets in a `finally`; an id cannot leak into the next invocation on a reused
  worker task.

---

### U3 - Audit event and single-point redaction

**Builds.** `audit.py` (mints the UUIDv4, sets `request_id_var` **in the same statement**, emits
the event with the fields `ai/tool-calling.md:171-173` names, records the transport, the resolved
client id on HTTP and an explicit **attribution-unavailable** marker on stdio, reads trace context
from `ctx.request_context.meta`, and implements the three-branch audit-write-failure policy of
`DESIGN.md:668-684`); `utils/redaction.py` **secret redaction only** - the fencing half is U8.

**Depends on.** U2.

**Verified by.**

- §8 **#4** (positive) and **#5** (absence), **as a pair** - `DESIGN.md:1183-1185` requires them
  paired so neither can be satisfied by silence. #5 asserts against the event #4 proves exists.
- §8 **#2**: a secret never reaches a log record, **including the whole `jobFeed` URL**; `sc=`
  redacted at the one enforcement point.
- §8 **#17**: trace context recorded when a `traceparent` is in the request `_meta`, **absent** when
  it is not. **Both arms required** - a field always synthesised passes a single-arm test and is the
  failure that matters. `trace_id`/`span_id` are never synthesised.
- The audit-failure policy, three arms: before the side effect the call fails; on a read it logs to
  stderr and continues; after a successful write it returns **success with a `warnings` array in
  structured content, `is_error=False`, not a problem object**, and the warning goes to **stderr**,
  not to the audit stream that just failed.
- The stdio arm asserts the attribution marker and **not** the literal `"global"`
  (`DESIGN.md:655-660` - the implementer error this row exists to prevent).

**File-boundary note.** `utils/redaction.py` is shared with U8. See [§4](#4-what-can-run-in-parallel).

---

### U4 - Jobvite client, part 1: auth and the error-detection rule

**Builds.** `services/jobvite_client.py` - `httpx2` client construction, v2 header auth
(`x-jvi-api`, `x-jvi-sc`), the v1 `jobFeed` query-parameter exception with its URL classified
sensitive, and **the invariant**: a response is successful only if the body carries no
`status.code >= 400` **and** the HTTP status is below 400 - both, every call
(`DESIGN.md:305-306`). Three error encodings handled: JSON status envelope, plain text with no
`Content-Type`, Tomcat HTML. XML is a **hardened fallback** parsed with `defusedxml` and treated as
an error body, not a handled case.

**Depends on.** U2, U3.

**Verified by.**

- §8 **#1**, the 200-with-401-body trap, against `error_auth_200_body401.json` **verbatim**. This is
  C5-S1, the only Critical on the client. Positive control: a synthetic 200 with
  `status.code == 200` succeeds.
- All five recorded error fixtures asserted byte-exact: `error_auth_401.json`,
  `error_route_404.json`, `error_task_400.html`, `error_v1_auth_401.txt`, plus the two malformed
  bodies (`malformed_not_json.txt`, `malformed_truncated.json`) failing loudly rather than
  degrading to an empty result.
- A route-level `404 "Invalid URL Cannot find API."` is **not** reported as a record-level
  not-found (§9 hazard 7).
- A URL containing a secret is never constructed for v2; the v1 URL never appears whole in any log
  record (joins U3's #2).
- No cookie jar (`JOBVITE-CONTRACT.md:2.3` - the `AWSALBAPP-*` values are the literal `_remove_`).

Transport substitution is `httpx2`'s built-in `MockTransport` (`DESIGN.md:1255-1256`, ADR-0007). No
third-party mocking library is added, at any point in this plan.

---

### U5 - **The first runnable server**: `search_jobs` end to end, plus the fencing-decision registry

**This is the smallest unit that produces a runnable server**, and it is deliberately the *jobs*
read rather than a candidate read.

**Builds.** `models/` for the job list, `tools/jobs.py` with `search_jobs` only, registration
wired to `JOBVITE_TOOLS`, the in-tool result cap reporting `showing N of total`, `request_id`
stamped into the result's `_meta` under
`com.evolvconsulting.fast-mcp-jobvite/requestId`, **and the mechanism that generates the fencing
paths from the output models** together with the test that fails when any model field has no
fencing decision (`DESIGN.md:181-184`).

**Depends on.** U1, U2, U3, U4.

**Why jobs and not candidates.** `search_jobs` is the **public job data** class
(`DESIGN.md:116`), so this slice exercises transport selection, config fail-fast, the error
contract, the audit path, the result cap and `_meta` **without** depending on EEO exclusion,
candidate PII redaction, or red-team fencing content. It is the smallest end-to-end path through
every cross-cutting mechanism on the least dangerous data class.

**Why the fencing-decision registry lands here and not in U8.** `DESIGN.md:181-184` requires the
fencing paths to be **generated from the output models**, with a test failing when any model field
has no fencing decision. That test binds the moment the *first* output model exists. Building the
mechanism against one small model is cheaper than retrofitting it across five, and it retires the
second-riskiest unit early (see [§6](#6-the-riskiest-unit)). Job fields take an explicit
"not free text" decision; U8 is where fencing actually fires.

**Verified by.**

- An in-process FastMCP `Client` calls `search_jobs` against `MockTransport` and gets a typed
  result; the same call against `error_auth_200_body401.json` returns
  `/problems/external-service-error` **502** with `is_error=True`.
- §8 **#16**, read arm: `request_id` present **on the wire result**, under the namespaced key,
  matched against the audit event's own id, **and** the structured content still validates against
  the output model. `DESIGN.md:1236-1237` is explicit that asserting on the `ToolResult` object
  would pass while the wire carried nothing.
- The result cap fires and reports `showing N of total` rather than truncating.
- Every field on the job model has a fencing decision; deleting a decision fails the suite.
- The server starts on stdio and on HTTP and lists exactly the enabled tools.

---

### U6 - Pagination

**Builds.** In `services/jobvite_client.py`: offset paging with **every scan starting at
`start=0`** (`DESIGN.md:428`), page cap 500 on v2 and 1000 on `/v1/jobFeed`, the per-scan seen-set
dropping duplicates, termination on a **short page** (`len(items) < count`) and never on `total`,
the completeness check against `total` **only on an exhaustive scan**, the per-resource base
configured separately with `JOBVITE_PAGINATION_START_BASE` as an override, and
`min(transport_cap, configured_result_cap)`.

**Depends on.** U4. **Sequential with U7** - same file, see [§4](#4-what-can-run-in-parallel).

**Verified by.**

- `start=0` on the first request of every scan, asserted at the transport.
- A clamped/overlapping page drops duplicates; a test proves de-duplication **cannot** recover a
  never-returned record, so the defence is starting at 0 and not de-duplicating harder
  (`DESIGN.md:438-441`).
- Termination on a short page; a `total` that lies does not terminate or extend the loop.
- The completeness check fires on an exhaustive scan with a missing record, and **does not fire** on
  a capped call - the capped call reports `showing 50 of 1,240` and is not logged as an anomaly
  (`DESIGN.md:442-450`). Both arms are required; wiring the check to every call is the failure this
  bullet exists to prevent.
- The structural assertion that `start=0` is accepted and returns records
  (`JOBVITE-API.md:399`).

**Inherited ceiling.** Whether `start` is 0- or 1-based is unresolved as a fact about Jobvite
(§12 item 2), and whether 500 is a real server limit is unobserved. Checklist rows 2 and 3 settle
both. The plan ships the design's base-agnostic scan and does **not** treat either as established.

---

### U7 - Resilience: timeouts, retry, breaker, and correlated logging

**Builds.** Ordered timeout → retry → circuit breaker, all inside
`services/jobvite_client.py`: explicit per-phase timeouts (no SDK default, no single scalar);
`tenacity` with jitter for connection errors, timeouts and 5xx only; a **configured total outbound
budget** bounding all attempts for one tool invocation (`DESIGN.md:346-348`);
`create_candidate` excluded from retry **by construction**; one breaker for Jobvite with **4xx
excluded from tripping it**; open-breaker and outage both `/problems/service-unavailable` **503**
distinguished by `detail` plus a `retry_after` hint; a `429` retried then mapped to 503, honouring
`Retry-After`.

**Depends on.** U6 (same file). **This is the riskiest unit** - see [§6](#6-the-riskiest-unit).

**Verified by.**

- §8 **#13**, the concurrent arm: **two invocations driven in parallel**, each forced to retry, each
  log line matched to the invocation that produced it. `DESIGN.md:1216-1217` states that a
  single-call version passes against a module global, which is the bug `request_id_var` exists to
  prevent - **so the concurrent arm is the case and a single call does not satisfy it.** The same
  case asserts **no URL** appears in a retry line.
- Every breaker transition logs its direction (`closed->open`, `open->half_open`,
  `half_open->closed`), the triggering counter, and `request_id`.
- §8 **#22**: a 4xx does not trip the breaker. Positive control: repeated 5xx does trip it.
- §8 **`create_candidate` not retrying on timeout** (#20), asserted with a **row counter** as the
  control, not by inspecting configuration - the spike measured one call producing **four rows**
  (`DESIGN.md:326`), so the assertion is the row count.
- The total outbound budget bounds a slow upstream into a typed 503 rather than an unbounded wait.

**The library constraint that shapes this unit.** `DESIGN.md:581` requires the breaker to
**evaluate transitions on the call path, not from a background timer**: a ContextVar is per-Task,
so a half-open expiry fired by a timer task has no `request_id_var` set, would log `None`, and
**would fail §8 #13**. Several Python breaker libraries do exactly that, and **no library is
selected yet (B47)**. Selecting one is in scope here; the selection criterion is that constraint,
and it is a rejection test, not a preference.

**Recommendation, where the design leaves a real choice.** Evaluate candidate libraries against the
timer constraint first, and if none passes, **write the breaker inline in
`services/jobvite_client.py`** rather than adopt one and patch around its timer. A breaker is a
counter, a threshold, a timestamp and three states; the design already fixes all four. That keeps
the dependency count at the three pinned packages plus `tenacity`, `loguru`, `defusedxml` and
`pydantic-settings`, and avoids a dependency whose behaviour we would have to constrain in exactly
the way `DESIGN.md:1126-1129` warns about - *on this framework a middleware's default is not a safe
starting point*, generalised. **This is a recommendation, not a decision the plan may make alone**
if it implies a dependency addition needing review.

**Inherited limit.** The circuit breaker is one of the two mechanisms `DESIGN.md:44-47` names as
**never executed** and sitting among measured results, borrowing their credibility. It is
unevidenced until this unit's tests run.

---

### U8 - Candidate reads: models, normalisation, EEO exclusion, fencing

**Builds.** `models/` for candidates (allow-listed, `strict=True`, snake_case, **no EEO fields**);
`utils/normalise.py` (casing, epoch-ms dates, `""`/null unification); the **fencing** half of
`utils/redaction.py` - path-keyed with wildcards, camelCase Jobvite paths, delimiter-token
stripping, strings only, unknown non-string fields **dropped**; `tools/candidates.py` with
`search_candidates` and `get_candidate`.

**Depends on.** U5 (fencing-decision registry), U6, U3 (shares `utils/redaction.py`).

**Write the structural assertions first** (see [§1](#1-the-count-that-governs-the-test-plan)), or
the models encode invented fixtures rather than the one observed envelope.

**Verified by.**

- §8 **#6**: EEO fields never appear in any tool result, **asserted against the output models**, not
  by inspection. C6-I1, Critical.
- §8 **#18**: fencing, including content that tries to **close its own fence** - the red-team cases
  are merge-gating (`DESIGN.md:711`). `candidate_list_injection.json` is the seed; it is not
  sufficient on its own.
- §8 **#19**: an unknown non-string field is dropped, not stringified.
- §8 **#23**: the `eId`/`EId` casing asymmetry pinned, so a later refactor cannot tidy it into a bug.
- §8 **#5** extended to the candidate path: PII reaches the audit *path* by construction and none of
  it is emitted in the clear.
- Path-keyed, not name-keyed: a test where `title` and `eId` appear at two depths and are decided
  differently - name-keying would collide (`DESIGN.md:704-706`).
- Two tools, not one, because output cardinality differs: `get_candidate` returns one record,
  `search_candidates` a page, and under `strict=True` one tool cannot have two return schemas.
- Date asymmetry and empty-string/null unification, both directions.

---

### U9 - HTTP transport hardening

**Builds.** In `server.py`/`config.py`: `StaticTokenVerifier` from environment at startup;
`require_scopes` on the **three data classes of §4.1** (candidate PII, public job data, job feed);
`allowed_hosts`/`allowed_origins` whenever the bind is not loopback; `RateLimitingMiddleware`
with a **mandatory** `get_client_id`; `TimingMiddleware`; `StructuredLoggingMiddleware` with
`include_payloads=False`; inbound `X-Request-ID` **validated as a UUIDv4** before use and echoed.

**Depends on.** U1, U3, U5.

**Verified by.**

- A token lacking a scope: the tool is **absent from `tools/list`** and a direct call returns
  "Unknown tool", not a permission error - the confusing-but-correct behaviour the README must
  document.
- Two differently scoped tokens see different tool sets.
- Rate limiting is **per client**, not the framework default: two clients, one drains its bucket,
  the other is unaffected. The default keys everyone to the literal `"global"`
  (`FASTMCP-SPIKE-4.md:898`).
- A malformed inbound `X-Request-ID` (newlines, over-long) is replaced rather than used; C7-T1.
- **`ResponseCachingMiddleware`, `ErrorHandlingMiddleware`, `ResponseLimitingMiddleware`,
  `RetryMiddleware` and `PingMiddleware` are absent** - assert their absence, since each was
  excluded for a measured reason (ADR-0004, `DESIGN.md:1087-1112`) and re-adding one is a silent
  regression.

**Inherited limits, carried not resolved.** Burst sizing is `desired_calls + 2` where the `2` is
**FastMCP's own client's connect sequence, not a protocol constant**, and under-provisions a
heavier client (`DESIGN.md:368-376`). Every limiter measurement was **sequential and single-client**
(ADR-0002); behaviour under simultaneous callers is unverified, and `limiters.clear()` was never
tested under load. The limiter has **never been exercised on stdio** at all - `DESIGN.md:386-389`
says so explicitly and calls that reasoning, not measurement.

---

### U10 - The write: dual-era approval guard and `create_candidate`

**Builds.** `approval.py` - the dual-era guard, keyed on
`ctx.request_context.protocol_version` compared against `('2026-07-28',)`; MRTR
(`InputRequiredResult` + `ctx.input_responses`) on sessionless; `ctx.elicit()` on handshake; the
conjunction `action == "accept" and content.get("approve") is True`; **an unidentifiable era
refuses the write and logs the observed value**. `create_candidate` in `tools/candidates.py`,
registered only under `JOBVITE_ENABLE_WRITES=true` **and** naming in `JOBVITE_TOOLS`, with
`send_email` defaulting to `false`, annotations `destructiveHint: true` / `idempotentHint: false` /
`readOnlyHint: false`, a `409` surfaced as `/problems/conflict` with the duplicate named in
`detail`, and the elicitation payload naming **the candidate, the target job, and whether
`send_email` is true**.

**Depends on.** U7 (no-retry), U8 (`tools/candidates.py`, models), U9 (era plumbing on HTTP).

**Verified by.**

- §8 **#21**, four arms: deny refuses; **accept-carrying-`approve: false` refuses**; no-handler
  fails closed; the second leg actually consumes `ctx.input_responses`.
- §8 **#24**, **both eras**, asserting **the row count did not change** and not the error shape -
  the no-handler arm **raises `MCPError` on sessionless and returns `is_error=True` on handshake**
  (`FASTMCP-SPIKE-4.md:2153-2165`), so an error-shape assertion passes on one era and fails on the
  other.
- An unidentifiable/absent `protocol_version` **refuses** and logs the observed value; positive
  control - a recognised era approves.
- §8 **#16**, write arms: `request_id` on the wire for a successful write **and** for the
  audit-failure warning branch.
- `approval_state` and the mechanism that produced it are in the audit event; C4-R1.
- Neither `ctx.transport` nor `session_id` is used as the discriminator - both are **identical or
  populated on both eras** and are measured traps (`FASTMCP-SPIKE-4.md:2073-2074`). Assert the
  discriminator is `protocol_version`.
- **The whole harness rests on a server-side row counter as its control**, exactly as the spike ran
  it. Without a counter the refusal arms assert nothing; this is the §16.3 lesson the spike records
  against itself.

**What may never be claimed.** *"The server requires an approval response from the host and refuses
to write without one"* - **never** *"a human approved this."* C4-S1 is a **High residual** and is
not mitigable server-side. An abandoned approval **hangs the call** with no server-side bound
(C4-D1). An authorised write can still be made twice (C4-D2); the idempotency-key remedy was
evaluated and **cannot be built** because nothing establishes Jobvite accepts one (B108,
`DESIGN.md:224-247`). None of these becomes a plan item; all three are disclosed in the README.

---

### U11 - `scripts/check_advisories.py`

**Builds.** The file `DESIGN.md:1401-1408` names as **the advisory-expiry owner** and which does not
exist. It reads the ignore table from `pyproject.toml`, **emits the `--ignore-vuln` flags
`pip-audit` actually takes** - the tool has no expiry concept and no `pyproject.toml` ignore section
of its own - and **exits non-zero on any expired entry**. The table is the single source for both
the flags and the expiry; hand-maintaining the flags beside it would be the two-lists defect the
design designs around elsewhere.

**Depends on.** U0 only. **Parallelisable from the start** - it touches `scripts/` and one
`pyproject.toml` table nothing else reads.

**Verified by.** §8 **#15**: an entry past its recorded expiry is **rejected**, with a positive
control showing an unexpired entry is **honoured** and its flag emitted. Additional arms: an entry
with no expiry is rejected; an expiry more than 30 days out is rejected; a blanket ignore is
rejected.

**The policy this enforces is four ordered steps** (`DESIGN.md:1390-1410`) and step 1 -
reachability - is **human judgement written down, not a tool output**. The script owns steps 3 and
4 only.

---

### U12 - `get_job_feed`

**Builds.** `get_job_feed` in `tools/jobs.py`, the v1 base, the separate `JOBVITE_FEED_KEY` /
`JOBVITE_FEED_SECRET` / `JOBVITE_COMPANY_ID` credential class, the 1000 page cap, and the
`jobs`-keyed envelope (a third name for one concept, §9 hazard 3).

**Depends on.** U5, U6, U3.

**Verified by.** The `jobFeed` URL never reaching a log record whole, `sc=` redacted - this is
C5-I1, a **High**, and it is the one endpoint that structurally requires the secret in the query
string. Plus `jobfeed_success.json` / `jobfeed_empty.json` round-tripping, and the third envelope
key normalised.

**Why it is late rather than in U5.** It is the only endpoint whose *URL* is a secret, so it wants
U3's redaction enforcement point proven first; and it is `[OFFICIAL]` 1-based, so it wants U6's
per-resource base configured.

---

### U13 - README and the documentation obligations

**Builds.** The README, which `DESIGN.md:1416-1423` **deliberately withholds until now** because a
README describing an unbuilt system is a false claim in the present tense. All fourteen sections
with **headings matching exactly**; the Configuration table **checked against `.env.example`**
rather than hand-maintained; an `mcp-name:` string **added before the first PyPI upload, not after**;
the `com.evolvconsulting.fast-mcp-jobvite/requestId` key documented, since a caller cannot guess it
and an id a caller cannot reach discharges nothing; the **six behaviours** of `:1458-1474`; the
read-only-key requirement in the deployment section; and a **credential-free Quickstart in full,
exercised by CI on every merge** - install, start the server, list tools. `readme-standard.md:83`
forbids a Quickstart step requiring credentials, so anything needing a Jobvite key belongs in
Configuration and Usage.

**Depends on.** U1-U12.

**Verified by.** §8 **#14**'s README arm goes **live** here - `DESIGN.md:1221-1223` requires it
**gated on the file's presence rather than skipped**, because a skip is a green that tested nothing.
Heading text asserted exactly; the Configuration table asserted equal to `.env.example`'s
enumeration; CI runs the Quickstart commands.

**Carried, not removed.** The unverified-success-path caveat stays until
`CREDENTIAL-CHECKLIST.md` rows 1-4 close (`CREDENTIAL-CHECKLIST.md:96-97`). **A CI status badge
cannot be live until CI exists** (`:70` forbids a static badge that does not reflect reality) - U0
makes CI exist, so the badge becomes legitimate at U0 and not before.

---

### U14 - Argument-layer hardening

**Builds.** The three inbound controls of §2.1, all in the input models: `strict=True` with extra
keys forbidden, explicit `max_length` and identifier regexes; **UTF-8 validation rejecting C0/C1
control characters other than tab, newline and carriage return, and Unicode bidi overrides**; and
the four structural limits - depth 5, 1,000 list items, 100 dict keys, 1 MiB body.

**Depends on.** U5 (first tool). **Can run in parallel with U8** if the models are already in
place; realistically it accretes as each tool's input model is written, and this unit is the sweep
that proves the set is complete.

**Verified by.** §8 **#7**, **#8** (with its positive control - an ordinary name still passes) and
**#9** (**four arms, one per limit**).

**The thing a naive plan gets wrong here.** `DESIGN.md:160-169` is explicit: **none of these
rejections carries a problem object**, because they live in the input models, run **before the tool
body**, and are raised by the framework. An earlier design revision said 400; the registry says 422;
**and neither reaches the caller on this path at all.** The tests must assert fail-closed behaviour,
not a problem-object shape. The 422 row in the registry is not dead - it serves validation detected
*inside* the tool body - but it is unreachable pre-dispatch.

---

## 3. Dependency order at a glance

```
U0  skeleton / pins / markers / CI
 ├── U1  boot: config, transport, TLS refusal, shutdown
 ├── U2  errors.py + request_id_var
 │    └── U3  audit.py + redaction (secrets)
 │         └── U4  client: auth + the error rule
 │              └── U5  FIRST RUNNABLE SERVER: search_jobs + fencing-decision registry
 │                   ├── U6  pagination ──► U7  resilience      (same file: SEQUENTIAL)
 │                   ├── U9  HTTP hardening
 │                   ├── U14 argument-layer sweep
 │                   └── U8  candidate reads (needs U6)
 │                        └── U10 approval + create_candidate (needs U7, U9)
 └── U11 scripts/check_advisories.py                            (independent throughout)
                                                U12 get_job_feed (needs U5, U6, U3)
                                                U13 README       (needs all)
```

---

## 4. What can run in parallel

Agents sharing a tree is how work gets lost here, so these are stated as **file ownership**, not as
topic areas. One owner per file, for the life of the unit.

### Wave A - immediately after U0

| Unit | Owns, exclusively |
|---|---|
| U1 | `src/fast_mcp_jobvite/config.py`, `__main__.py`, `server.py`, `server.json`, `.env.example` |
| U2 | `src/fast_mcp_jobvite/errors.py`, `utils/correlation.py` |
| U11 | `scripts/check_advisories.py`, the `[tool.*]` advisory-ignore table in `pyproject.toml` |

**Genuinely disjoint.** The one shared file is `pyproject.toml`: U0 writes it, U11 appends one
table. Have U0 land the empty table so U11 only edits rows inside it, or U11 waits for U0's commit.

### Wave B - after U2

U3 (`audit.py`, `utils/redaction.py`) and U4 (`services/jobvite_client.py`) are disjoint **files**,
but U4 depends on U3's redaction point for its logging assertions. Run U3 first, or run them
together with U4 stubbing nothing - do **not** run them concurrently with two agents, because U4's
§8 #2 arm asserts against U3's implementation.

### Wave C - after U5, the widest genuine fan-out

| Unit | Owns, exclusively | Reads but does not write |
|---|---|---|
| U9 | `server.py` (middleware + auth block), the HTTP half of `config.py` | `audit.py` |
| U14 | the input-model modules under `models/` | `tools/` |
| U6→U7 | `services/jobvite_client.py` | - |
| U12 | the `get_job_feed` half of `tools/jobs.py` | `services/jobvite_client.py` |

**Three collisions to plan around, all real:**

1. **U6 and U7 both live in `services/jobvite_client.py`.** §3's module layout fixes that file, so
   they **cannot** be parallelised. One owner, U6 then U7. Splitting the client into two modules to
   parallelise them would be a design change and is not proposed.
2. **`utils/redaction.py` holds secret redaction (U3) and untrusted-content fencing (U8).**
   `DESIGN.md:1262-1264` names both, and ADR-0010 puts `utils/` at the standard's **95%** because of
   it. Two agents cannot both own it. Sequence U3 → U8, or give one agent both halves.
3. **U8 and U10 both write `tools/candidates.py`.** Sequential, U8 then U10.

**U9 and U6→U7 and U14 and U12 can genuinely run as four concurrent agents** once U5 has landed,
because their write sets are disjoint. That is the widest safe fan-out in this plan.

**A rule that costs nothing and prevents the failure that actually happens here:** no agent runs
`git stash`, and no agent switches branches on a tree another agent is working. If two units must
overlap in time on the same file, they get separate worktrees pinned to a SHA, not turns in one
checkout.

---

## 5. Where the credential-free constraint reorders the work

The design's own front matter (`DESIGN.md:39-51`) says **no claim about a Jobvite success response
is verified, because none has ever been observed.** Five consequences for sequencing, each of which
inverts what I would otherwise do:

1. **The error path is built before the success path, and it is the only ground truth.** Normally
   the happy path comes first. Here the recorded fixtures are *all* error transport, so U4 - the
   error-detection rule - is the earliest unit with byte-exact evidence behind it, and the success
   models (U5, U8) come after and are explicitly hypotheses.

2. **The structural assertions are written before the candidate models, not after.** The one
   observed `200` cannot ship as a file. If the models are written first they will encode the
   synthetic fixtures - which we invented - and the structural tier will then be *derived from the
   models it was supposed to constrain*. That is circular, and it is the exact failure the
   three-tier split exists to prevent.

3. **The first slice is `search_jobs`, not `search_candidates`.** With no credential there is no way
   to discover a shape mistake at runtime, so the first end-to-end path should exercise the
   cross-cutting machinery on the data class where a mistake is cheapest. Public job data has no
   EEO exclusion, no PII redaction and no red-team fencing riding on it.

4. **`create_candidate` is last, and its verification is structurally different from every other
   unit's.** It can never be exercised against Jobvite - there is no sandbox, and
   `CREDENTIAL-CHECKLIST.md` row 10 requires customer agreement, a named test job and an agreed
   cleanup path *before* one real write. So U10's entire assurance is the approval guard plus a
   **server-side row counter** as the control, replicating the spike's harness. Every refusal arm
   asserts *the count did not move*; none of them asserts an error shape.

5. **The credentialed suite is written as the units land, and never run.** Each tool unit adds its
   credentialed arm behind the declared marker. CI **collects** it (`--collect-only`) so an import
   error or renamed fixture surfaces immediately rather than on the day a key finally arrives
   (`DESIGN.md:1156-1159`). Without this the excluded suite rots invisibly for the whole project.

Two things the constraint does **not** let us decide, which the plan therefore leaves open: the
`start` base (checklist row 2) and whether 500 is a real page cap (row 3). Both ship as configured
values with the design's base-agnostic scan around them.

---

## 6. The riskiest unit

**U7, resilience - specifically the circuit breaker and its correlated logging.** Four things
compound in one unit:

1. **It is one of only two mechanisms in the entire design that has never been executed.**
   `DESIGN.md:44-47` names the circuit breaker and the capability-drift diff as the pair that *"sit
   among executed results and borrow their credibility"*. Every other mechanism in this plan has a
   spike behind it. This one has a paragraph.
2. **Its dependency is unselected (B47) and the selection criterion eliminates the obvious
   candidates.** `DESIGN.md:581` requires transitions to be evaluated **on the call path, not from a
   background timer**, because a ContextVar is per-Task and a timer-fired half-open expiry would log
   `request_id=None`. Several Python breaker libraries do exactly that. So the library choice is
   made *by a test that does not exist yet*, against libraries nobody has surveyed.
3. **A High that just came off the must-mitigate table depends on it.** C5-R1 left the table in
   revision 5 (`DESIGN.md:1735`) on the strength of `request_id_var` plus retry and breaker
   logging. If the breaker cannot carry `request_id`, that row reopens - and it reopens *after* the
   design was declared settled.
4. **Its required test is the hardest one in §8.** #13 demands two invocations in parallel, each
   forced to retry, each line attributed. A single-call version **passes against a module global**,
   which is precisely the bug being defended against. This is the one §8 case where a plausible,
   green, wrong test is easy to write by accident.

**What to build first to retire it.** Before U6 - in fact it can run concurrently with U3/U4 as a
throwaway - build **the concurrent correlation harness alone**: two `asyncio` tasks, each setting
`request_id_var`, each driving a fake retry hook and a fake breaker transition hook, asserting each
line matches its own task. It needs no Jobvite client, no tools, no server. It answers two
questions cheaply: does a ContextVar survive the call path each candidate library uses, and does
the test fail when the mechanism is swapped for a module global (the positive control that makes
the test non-vacuous). **Run the library survey against that harness, not against the finished
client.** If nothing passes, the inline-breaker recommendation in U7 is taken with evidence rather
than as a preference.

**Runner-up: the generated fencing paths** (`DESIGN.md:181-184`). Also unexecuted, also carrying
Criticals (C6-S1, C6-I1), and it has a subtle failure mode - it must generate camelCase Jobvite
paths from snake_case models, which means the models have to *carry* their source path, and the
design does not say how. Retired early by building it in U5 against one small model, which is why
U5 is scoped that way.

---

## 7. Where the design leaves a real choice, and what I recommend

The design settles almost everything. These are the places it genuinely does not, and where I
believe an implementer would otherwise guess:

| Choice | Recommendation | Reasoning |
|---|---|---|
| Circuit-breaker library vs inline | **Inline in `services/jobvite_client.py`, if the survey finds no library evaluating transitions on the call path** | The constraint at `DESIGN.md:581` is a rejection test most libraries fail. A breaker is four pieces of state the design already specifies. Adding a dependency and then constraining its scheduler is more code and more risk than the thing it replaces. Decide **with** the U7 harness, not before it |
| How a model field carries its Jobvite path, for fencing-path generation | **A per-field alias or `json_schema_extra` entry naming the camelCase Jobvite path**, since aliases are needed for the casing normalisation anyway | `DESIGN.md:181-184` requires generation, not a second hand-kept list. Reusing the alias the model already needs means one source, which is the whole point of the clause |
| Logging library | **`loguru`**, named in §3's module layout | Already fixed by the design; recorded here so nobody re-opens it |
| Retry library | **`tenacity`**, named at `DESIGN.md:320` | Same |
| XML parsing | **`defusedxml`**, named at `DESIGN.md:312` | A hardened fallback only, for a route we do not call |
| Where the structural tier lives | **A test module of shape assertions, with no fixture file** | The body cannot ship. A file would either be empty or be a synthetic wearing a structural label, which is the confusion the three tiers exist to prevent |
| First tool | **`search_jobs`** | See [§5](#5-where-the-credential-free-constraint-reorders-the-work), point 3 |

---

## 8. What this plan does NOT cover

Stated plainly, because an unstated omission reads as coverage.

- **I did not read the standards corpus.** Every `standards/...:line` citation in this plan is
  quoted **from `DESIGN.md` or an ADR**, not verified at its source in
  `evolv-coder-standards/standards/`. If a design citation is wrong, this plan repeats it.
- **I did not read `docs/DESIGN.md`'s supporting research in full.** I read `DESIGN.md` end to end,
  all eleven ADRs, `docs/adr/README.md`, `CREDENTIAL-CHECKLIST.md`, and the fixtures. Of
  `FASTMCP-SPIKE-4.md` (2,354 lines) I read §§1.3, 3.2, 3.3, 10, 10.1, 12, 13.1-13.3, 20.3-20.8 and
  the closing *"What I could NOT verify"*. Of `JOBVITE-CONTRACT.md` I read §§2, 4 and the section
  index; of `JOBVITE-API.md`, §6.1 and the probe map. I did **not** read `COMPLIANCE-SPEC.md`,
  `STANDARDS.md`, `LICENSING-SURVEY.md`, `DECISIONS.md`, `data-inventory.md`, or any of the 17
  documents in `docs/reviews/` beyond the three gate scripts' docstrings.
- **No effort, duration or sequencing-in-time estimate.** The order is a dependency order.
- **No CI runner, Python matrix or workflow YAML is drafted.** U0 names what CI must run, not how.
  Note the spike ran only 3.11.15 and 3.12.3; the design sets `>=3.12`, so 3.13+ is unexercised.
- **No packaging or release process** beyond the pins, the lockfile and the `mcp-name` note. PyPI
  upload, versioning and `mcp-publisher` are untouched; the spike executed nothing from
  `FASTMCP.md` §12(b).
- **No plan for the twelve v2 resources we ship no tools for.** Checklist row 7 names that as the
  highest-yield expansion and it is out of scope.
- **I did not verify that `uv lock` reproduces the 72-package resolve** recorded at
  `DESIGN.md:1306-1310`. That is U0's first act, not this plan's.
- **I did not re-run `check-coupling-controls.py` or `check-coupling-sweep.py`.** I ran
  `check-coupling.py` only, which exits 0.

---

## 9. Questions for the design

Each of these needs a numbered ADR or a design edit. **None is worked around in the plan above**;
each is named at the unit it blocks.

### Q1

**B15's two configuration settings have no name and no default, and `config.py` cannot be written
without them.** `DESIGN.md:1448-1452` states it directly: §7.7's result cap and §4.4's outbound
rate-limit setting *"are both specified as configuration and neither has a name or a default"*,
and records their absence from `.env.example` as an open item. But `DESIGN.md:1431-1437` also makes
`.env.example` **the single enumeration** the README's Configuration table is checked against, and
§7.3 requires fail-fast validation of what each enabled tool needs. So U1 must either invent two
variable names - which is a design decision the plan may not make - or ship an enumeration the
design already calls incomplete.

Both settings are also on the **mitigate-before-production-release** list as C3-I1 and C6-D1
(`DESIGN.md:1749-1750`), where the Test column reads `unmitigated (B15)`. **The plan proceeds with
the settings deferred to U6/U7 and `.env.example` knowingly incomplete**, which is the design's own
current position - but a name and a default are needed before U13 can assert the table matches, and
before production release either way.

### Q2

**The §7.4 shutdown test is a stated requirement that no gate can see.** `DESIGN.md:944` calls it
*"a requirement rather than a suggestion"* and `:947-950` specifies both halves on both transports.
It is **not** in §8's enumerated required-cases list and **no §11 row names it**, so
`check-coupling.py` - whose whole purpose is coupling §11's mitigations to §8's cases - cannot fail
if it is dropped. Three of the design's own stated verification gaps (the composed snippet never run
end to end on HTTP, PID 1 never simulated, and §12 item 5's uvicorn dependency) close **only** on
this test.

The plan schedules it in U1 regardless. The question is whether the design intends §8's list to be
the complete set of required cases - in which case this one is missing from it - or whether required
tests may live outside the list, in which case the gate's coverage claim is narrower than it reads.

### Q3

**C8-R1, startup configuration logging, is `unmitigated` and its remedy interacts with ADR-0011.**
`DESIGN.md:1678` says the remedy is to *"log the enabled tool set, the write flag and the TLS
posture once at startup"* and records it as **"Not currently specified"**. It is on the
mitigate-before-production-release list. ADR-0011 closes with *"Not a licence to add a fourth"*
producer - which is about **per-invocation** producers, and a once-at-startup line is plainly not
one, but the ADR's sentence is unqualified.

U1 is where a startup log line would naturally land. The plan does **not** add one, because doing
so would be specifying an unspecified mitigation and arguably touching an ADR's scope. A one-line
design statement, or an ADR-0011 amendment saying startup lines are out of its scope, unblocks it.

### Q4

**B47's breaker-library selection is deferred to implementation, but the constraint that governs it
can reopen a closed High.** `DESIGN.md:581` frames the call-path-transition rule as *"a constraint
on that choice rather than an observation about one"*, which correctly leaves selection to
implementation. What is not stated is the fallback: if **no** library satisfies the constraint, is
an inline breaker acceptable, given §3's module layout names no home for one and a new dependency
would need review? U7 recommends inline. Confirming that in the design - or naming a library -
would mean the answer is not made by whoever happens to be holding U7.

---

*Written by `impl-plan-draft`, 2026-08-28. Not reviewed. `docs/DESIGN.md` was not edited and nothing
was committed.*
