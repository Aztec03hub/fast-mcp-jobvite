# Conformance re-sweep: the 59 open obligations, against DESIGN.md revision 4

**Task:** CONF-4 · **Author:** conformance-resweep · **Date:** 2026-08-27
**Updated:** 2026-08-27, after FIX-11. **All nine Tier 1 defects are closed.**

> **Read this first, because this document is both a finding record and a status.** The §3 table
> below states each finding **as it was made**, and every row whose verdict has since changed
> carries a **CLOSED** marker naming the fix and what landed. §1's counts and §4's ranking are kept
> **current**, not historical, because those are what a freeze decision reads. Where the two appear
> to disagree, §1 and §4 are the live numbers and §3's prose is the record of what was wrong.
>
> Three defects (B5, B7, B90) and one not-yet-built item (B91) were closed by other agents before
> FIX-11; I verified each in the artifact rather than taking the report of it. The remaining six -
> the B25/B30 cross-cutting contradiction, B78, B55, B43, B86, B33 - were closed by FIX-11.
> **Tier 1 is now empty. The case against freezing that this document made no longer stands.**

**Subject under test:** `docs/DESIGN.md` (DRAFT revision 4, last updated 2026-08-27 05:10 PM CDT),
**plus the repository as it actually stands**. The second half is not scope creep: the brief that
sent me here says explicitly that a section specifying what a README must contain is not the same
as a README existing, and the inverse turned out to matter more. Two obligations the earlier sweep
recorded as UNADDRESSED are satisfied by committed artifacts that `DESIGN.md` never mentions, and
one freeze-blocker row in `DESIGN.md` §11 asserts the absence of a file that is committed.

**Scope:** the 37 UNADDRESSED and 22 PARTIAL rows of `docs/reviews/CONFORMANCE-B1-B106.md`,
re-walked one at a time. **The 42 SATISFIED and 5 NOT-APPLICABLE rows were not re-checked** - see
§5.

**Method.** Every clause below was re-opened in
`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/` and every line
number was taken from `grep -n` on a distinctive phrase from the clause itself. No line number in
this document was counted off a `sed` window. Every design section cited was read in full, not
matched. Where I reason rather than observe, the sentence is marked `[REASONED]`.

> **Amended 2026-08-28 by the CONF-5 citation-range audit.** The "Clause (re-verified)" column
> originally carried a **single anchor line plus a truncated excerpt** - `:153` rather than
> `:153-155`, `:174` rather than `:173-177`. That convention is **retired**, and the affected rows
> (B15, B16, B17, B21, B23, B40) now cite the clause's full line range with the clause quoted whole.
>
> The convention was not merely untidy. Citation ranges in this corpus contract on every
> copy-forward - `STANDARDS.md` cited `ai/tool-calling.md:173-177`, the first sweep narrowed it to
> `:173-175`, and this document narrowed it again to `:174`. The lines dropped in that chain,
> `:176-177`, carry a real obligation (attach the LLM trace/span id) that consequently went
> untracked by every instrument for six review rounds. **Re-verification cannot catch this**: a
> contracted range still resolves, still quotes accurately, and still reads as sound. **The rule
> going forward is that a citation names the clause's boundaries, never a convenient anchor inside
> it.** See `docs/reviews/CITATION-RANGE-AUDIT.md`.

---

## 1. Counts

### The 59 re-walked

| Verdict | At first sweep | **Now, after the fixes** |
|---|---|---|
| SATISFIED | 10 | **16** |
| PARTIAL | 24 | **18** |
| UNADDRESSED | 24 | **22** |
| NOT-APPLICABLE | 1 | **3** |
| **Total** | 59 | **59** |

Ten rows moved: B5, B7, B90 and B55, B86 to SATISFIED; B91 to SATISFIED; B43 and B33 to
NOT-APPLICABLE as settled deviations with the adaptation stated; B78 stays PARTIAL with its
category corrected. The B25/B30 cross-cutting defect is closed against rows already SATISFIED.

### Projected across all 106

Carrying the 42 SATISFIED and 5 NOT-APPLICABLE rows forward unverified:

| Verdict | Before this sweep | At first sweep | **Now** |
|---|---|---|---|
| SATISFIED | 42 | 52 | **58** |
| PARTIAL | 22 | 24 | **18** |
| UNADDRESSED | 37 | 24 | **22** |
| NOT-APPLICABLE | 5 | 6 | **8** |
| **Total** | 106 | 106 | **106** |

**Thirteen obligations closed since revision 2. Twenty-four are still unaddressed and twenty-four
are still partial.** The movement is real and it is concentrated: the input-limits work (B25, B30)
and the supply-chain work (B64, B65, B66) each closed a cluster outright, and the documentation
cluster moved from eleven-consecutive-unaddressed to a mix, partly through §10.1 and partly because
`CHANGELOG.md` was written and nobody told the design.

### By category, which is the number the freeze decision needs

| Category | Count | What it means |
|---|---|---|
| Category | At first sweep | **Now** | What it means |
|---|---|---|---|
| **DEFECT** | **8** | **0** | The design says something wrong, or contradicts a clause, or contradicts itself |
| **NOT-YET-BUILT** | 13 | 12 | The design specifies it correctly; only implementation is missing |
| **DEFERRED-WITH-REASON** | 5 | 6 | Consciously not done, with an ADR or a stated rationale |
| **STILL-OPEN** | 22 | 22 | Nobody addressed it and nobody decided not to |
| *(closed)* | 11 | 19 | SATISFIED or NOT-APPLICABLE |

The eight per-row DEFECTs were B5, B7, B33, B43, B55, B78, B86 and B90. **A ninth was
cross-cutting and belonged to no single row**: the 400-problem-object contradiction sat on B25 and
B30, both otherwise closed, so it is recorded in the table beneath them and ranked in §4 rather
than counted as a row category.

**Those nine were the entire freeze argument, and all nine are now closed.** What remains is
twenty-two obligations nobody has decided about and twelve that need only code. Section 4 ranks
what is left and records how each defect was closed.

---

## 2. Corrections to the earlier sweep

The B1-B106 sweep is a secondary source here and two of its verdicts were wrong when written,
independently of anything that changed since.

- **B87 (changelog date integrity) was never UNADDRESSED; it was NOT-APPLICABLE.**
  `documentation/changelog-standard.md:93` - *"**Date integrity**: a release date MUST equal the
  date the artifact was published. Backdating is forbidden."* A release date cannot be wrong when
  no release exists. `CHANGELOG.md` carries `## [Unreleased]` and nothing else. The obligation
  becomes live at the first tagged version and not before. Recording it as an unmet obligation
  inflated the headline count by one.

- **B50 (type hints and docstring style) was over-called.** The sweep marked it UNADDRESSED on the
  grounds that neither appears in `DESIGN.md`. `DESIGN.md:1101` lists `types` among the CI jobs,
  which is mypy, which gates the type-hint half of `documentation/agentic-coding-standard.md:169` -
  *"- [ ] Python has type hints on all public functions"*. Only the docstring-style half is open.
  PARTIAL, not UNADDRESSED.

One further note on the earlier document's framing rather than its verdicts. It said of the
documentation cluster that *"The entire documentation cluster B77-B87 is unaddressed except B83's
absence being total."* **B83's absence was not total and was not absent.** `CHANGELOG.md` is
committed at the repository root, follows Keep a Changelog 1.1.0 by its own header, and opens with
`## [Unreleased]`. It was committed before that sweep ran. The sweep assessed the design and
reported a conclusion about the repository, which is the same class of error as assessing by
keyword: a correct statement about the instrument, stated as a fact about the object.

---

## 3. The table

Verdicts are against the design **and** the repository, and where those differ the row says so.
Category is `DEFECT` / `NOT-YET-BUILT` / `DEFERRED-WITH-REASON` / `STILL-OPEN`.

### 3.1 Error contract

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B5** | `type` URIs relative, and stable once published | `architecture/error-contract.md:211` - *"8. **Relative type URIs**: Use `/problems/<slug>`, not absolute URLs."*; `:210` - *"7. **Type URIs are stable**: Once published, a `type` URI is a contract. Changing it is a breaking change."* | PARTIAL | **SATISFIED** | **CLOSED** | **CLOSED.** §5.1 now maps every condition onto the registry's own types and §4.3 distinguishes an open breaker from an outage through `detail` rather than a minted slug. Original finding: Shape still correct (`DESIGN.md:408`). The stability half is still unmechanised, and this pass found the harder problem underneath it: **`error-contract.md:96-108` is a registry of thirteen canonical problem types with fixed statuses**, and `DESIGN.md` invents four slugs against it - `/problems/jobvite-circuit-open`, `/problems/jobvite-unavailable` (`:279-281`), `/problems/jobvite-duplicate-candidate` (`:978`) - without declaring that it extends the registry or mapping them onto `/problems/service-unavailable` (503) and `/problems/conflict` (409), which the registry already provides for those exact conditions. Separately, `DESIGN.md:410` assigns **400** to input validation where `error-contract.md:101` fixes `/problems/validation-error` at **422**, and `backend/input-validation.md:393` says the same: *"7. **Map to ProblemDetail** — 422 responses use `errors` array per error-contract.md"*. A frozen `type` URI is a contract; freezing the wrong statuses against it is the expensive kind of wrong |
| **B6** | Exception hierarchy carrying `problem_type` + `title` class attributes | `backend/error-handling.md:205` - *"When raising `AppException` directly for domain-specific errors, always provide `problem_type` and `title`:"* | PARTIAL | **PARTIAL** | NOT-YET-BUILT | Unchanged. `DESIGN.md:216` still says only *"`errors.py` exception hierarchy + RFC 9457 problem construction"*. The design does not contradict the clause; it is silent on the shape. Nothing wrong is locked in by freezing |
| **B7** | Upstream 5xx → `ServiceUnavailableException`; upstream 4xx → `ExternalServiceException` | `backend/error-handling.md:413,417` (`ServiceUnavailableException` / `ExternalServiceException` in the upstream branch); `architecture/error-contract.md:105` - *"\| `/problems/external-service-error` \| 502 \| External Service Error \| Upstream service failure \|"* | PARTIAL | **SATISFIED** | **CLOSED** | **CLOSED.** §5.1's table sends every Jobvite failure including its 4xx to `/problems/external-service-error` at 502; the upstream status moves to `detail`. Original finding: Unchanged and now sharper. `DESIGN.md:409-410` still reads *"`status` carries the upstream Jobvite status where one exists"*, which surfaces a Jobvite **401** to the caller as a **401**. The registry says an upstream failure is a caller-facing **502**. This is not silence: it is a stated rule that contradicts a clause, in the one section the whole error surface is generated from |

### 3.2 Tool definition and guardrails

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B12** | Schema violation fails closed with a typed tool error, never reaching the body; unit-tested | `ai/tool-calling.md:100` - *"**Reject on violation** — return a typed tool error back to the model so"*; `:188` - *"The per-tool argument-rejection path is unit-tested: a schema violation"* [must fail closed] | PARTIAL | **SATISFIED** | *(closed)* | Both gaps closed. `DESIGN.md:424-429` now states the rejection's actual shape rather than implying uniformity: FastMCP validates before the body runs, so the rejection is raised by the framework and carries no problem object. `DESIGN.md:937-938` puts *"an argument-schema violation failing closed"* in §8's **Required cases** list, which is the merge-gating list the earlier sweep found it missing from |
| **B15** | Result size bounded to a **documented** maximum | `ai/tool-calling.md:153-155` - *"**Bound result size** before returning it to the model (truncate to a documented max); an oversized result is both an injection surface and a context/cost blowout."* | PARTIAL | **PARTIAL** | STILL-OPEN | The document to put it in now exists: §10.1's Configuration table (`DESIGN.md:1122-1125`) commits to listing every variable. **The number itself still appears nowhere.** The design says so about itself, twice - `DESIGN.md:1293` and `:1288` both read *"**The default is still undocumented (B15)**"* and both carry the disposition `unmitigated (B15)`. Safe to freeze: adding a default later changes no design decision |
| **B16** | Tool name + description reviewed like prompts - clear, minimal, no secrets | `ai/tool-calling.md:55-57` - *"Tool name + description are part of the prompt and are **reviewed like prompts** — clear, minimal, no secrets. The callable-tool set is an explicit allow-list per agent"* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | **`DESIGN.md` still never mentions tool descriptions.** I read §2, §2.1 and §10.1 in full rather than searching: §2 gives a five-row table of tool names and Jobvite operations, §2.1 governs schemas, §10.1 lists what the README must document. None asserts that descriptions exist, that anyone reviews them, or that they carry no tenant or credential detail. **It is also absent from the threat model**: C3 covers the argument layer, C6 the output pipeline, and no row covers the tool manifest, which is the one payload sent to every model on every connection before any argument exists |
| **B17** | Log every invocation with tool name, redacted args, result status, latency, **approval decision if gated**, correlation id; wire-shaped snake_case | `ai/agent-guardrails.md:121-123` - *"**Log every tool invocation** with: tool name, validated arguments (PII redacted), result status, latency, the approval decision if gated, and"* [the correlation id]; `:129` - *"wire-shaped **snake_case** (`tool_name`, `request_id`, `approval_state`)."* | PARTIAL | **PARTIAL** | NOT-YET-BUILT | **The gap that mattered is closed.** `DESIGN.md:462` - *"**The audit event includes `approval_state`.**"* - with the reasoning, and `DESIGN.md:925-930` makes it a required §8 case paired with a positive control so an absence cannot pass by silence. Remaining: the **field-naming** clause at `:129` is never stated. De facto met (`request_id`, `approval_state` are used in that form throughout) but not committed to, and `DESIGN.md:120`'s snake_case rule is scoped to tool *outputs*, not to log fields |
| **B21** | Credentials scoped narrowly; scope the credential, never the prompt | `ai/agent-guardrails.md:50-53` - *"**Minimal scope per tool.** Each tool runs with the narrowest credentials / permissions that work ... Scope the *credential*, never rely on the prompt to keep the model in bounds."* | PARTIAL | **PARTIAL** | STILL-OPEN | Inbound token still scoped on three data classes (§7.2); the **outbound Jobvite credential** is still unscoped. Now modelled rather than missed: `DESIGN.md:1325` is C5-E1, rated **High**, marked *"**Unmitigated.**"*, and it is one of three rows on the must-mitigate-before-implementation list at `DESIGN.md:1391`. The remedy named there - *"Document that a read-only key is required where writes are disabled"* - is not written anywhere in §4.1 or §10.1 |
| **B23** | Adversarial cases merge-gating: invalid/over-budget arguments, an injection payload, an unbounded-loop attempt | `ai/tool-calling.md:185-187` - *"Adversarial tool cases — invalid/over-budget arguments, a tool result"*; `:187` - *"**merge-gating** tests"*; `ai/prompt-injection.md:138` - *"- Maintain red-team cases for injection and jailbreaks as **merge-gating**"* | PARTIAL | **PARTIAL** | STILL-OPEN | Two of three arms now present in §8's required list: invalid arguments (`:917`, `:919`, `:923`) and the injection payload (`:934`). **The unbounded-loop arm still has no case.** §4.5 bounds a scan by short-page termination and a per-scan seen set, and §9 hazard 5 (`DESIGN.md:993`) records that a paged walk over a mutating set with no stable sort may duplicate or skip - which is the unbounded-walk shape - with no test attached |

### 3.3 Input validation

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B25** | Input size and encoding limits before dispatch; reject control characters and oversized payloads | `ai/prompt-injection.md:124` - *"- Enforce input size/encoding limits before dispatch; reject control"* [characters and oversized payloads] | PARTIAL | **SATISFIED** | *(closed, with a defect noted below)* | `DESIGN.md:138-146` now specifies it directly, with the reasoning about why `max_length` and the output allow-list cannot reach it, and `DESIGN.md:939-942` makes it a required §8 case **with a positive control** showing an ordinary name still passes. C3-T1 (`:1243`) is mitigated against that case. This is the cleanest close in the sweep |
| **B30** | Nesting depth ≤ 5, list items ≤ 1,000, dict keys ≤ 100, body ≤ 1 MiB | `backend/input-validation.md:223-226` - *"\| Max nesting depth \| 5 levels \|"*, *"\| Max list items \| 1,000 \|"*, *"\| Max dict keys \| 100 \|"*, *"\| Max total request body size \| 1 MiB \|"*; rules at `:391-392` | UNADDRESSED | **SATISFIED** | *(closed, same caveat)* | All four limits are in `DESIGN.md:126-131` at the standard's own values, enforced before dispatch, with `DESIGN.md:133-136` naming the exact confusion the earlier sweep flagged (that §4.5's 500/1000 page caps are a different axis). §8 requires **one arm per limit** (`:923-924`). C3-D1 (`:1246`) mitigated |
| | | | | | **DEFECT** | **The shared caveat, which belongs to neither B alone.** `DESIGN.md:145` says of both rejections: *"Rejection is a `400` problem object per §5.1."* `DESIGN.md:424-426` says the opposite about the same layer: *"**An argument-schema violation carries no problem object either.** FastMCP validates arguments **before the tool body runs**, so ... nothing can return one."* §2.1 places its own checks *"before dispatch"*, which is that same layer. **By §5.1's own reasoning, §2.1's sentence cannot be true.** `[REASONED]` - I have not executed FastMCP's validator to confirm a Pydantic field-validator rejection surfaces identically to a schema rejection; §5.1 asserts the mechanism and §2.1 contradicts it, and one of the two is wrong regardless of which. Compounding it: the status should be **422**, not 400, per `error-contract.md:101` and `input-validation.md:393` |

### 3.4 Resilience, logging, correlation

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B33** | Timeouts shorter than the inbound request's own deadline | `backend/resilience.md:74` - *"- Timeouts MUST be **shorter than the inbound request's own deadline** so a"* [slow dependency surfaces as a fast typed error] | PARTIAL | **NOT-APPLICABLE** | **CLOSED** | **CLOSED by FIX-11.** §4.3 now states the clause has no referent on this transport and supplies a configured outbound ceiling instead, and records that §7.5's abandoned-approval hang is out of its reach. Original finding: Unchanged, and the reason it is a defect rather than a gap is that `DESIGN.md:271-272` states the clause as satisfied - *"budget inside the inbound timeout"* - **naming a deadline this architecture does not have.** MCP has no inbound request deadline and no HTTP request worker to hang. `DESIGN.md:823` admits the failure mode the clause exists to prevent occurring anyway, from a different cause: *"an abandoned approval **hangs the call**"*, unbounded. One sentence stating the adaptation would fix it; freezing preserves a sentence that reads as compliance and is not |
| **B39** | Retries and breaker transitions logged with the correlation field, never silent | `backend/resilience.md:226` - *"`request_id` correlation field. Never retry or trip silently."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Still not designed, but now **modelled and escalated**: `DESIGN.md:1322` is C5-R1, rated **High**, *"**Unmitigated.**"*, disposition `unmitigated (B39, B40)`, and it is the first row on the must-mitigate-before-implementation list (`:1342`). §11's own governing rule is `threat-modeling.md:86`, which requires Critical and High mitigated *before implementation proceeds* |
| **B40** | The correlation triple verbatim, including ContextVar `request_id_var` | `ai/tool-calling.md:173-177` - *"Use the canonical triple verbatim: HTTP header `X-Request-ID`, log field `request_id`, ContextVar `request_id_var` ... Also attach the LLM trace/span id so a tool call ties back to its turn"*; identically `ai/agent-guardrails.md:124-127`; `architecture/observability.md:72` - *"request_id_var: ContextVar[str] = ContextVar(\"request_id\", default=\"\")"* | PARTIAL | **UNADDRESSED** | STILL-OPEN | **Downgraded from PARTIAL, deliberately.** The header and the log field are still right, but `request_id_var` appears in `DESIGN.md` only twice and both are gap statements (`:1274`, `:1342`) - the design now names it as a thing it does not have. That is more honest and less covered than before. Same row as B39 and the same remedy; they are one gap |
| **B42** | Every request gets a request_id, echoed on **every** response, success and error | `backend/request-middleware.md:142` - *"1. **Every request gets a request_id**: No request may complete without a correlation ID on `request.state`."*; `:144` - *"3. **Always echo**: The `X-Request-ID` response header is present on every response (success and error)."* | PARTIAL | **PARTIAL** | STILL-OPEN | Minting and error-path echo unchanged and correct. **Success-path echo is still absent**, and this revision made the omission conspicuous rather than closing it: `DESIGN.md:498-500` now specifies success-path structured content in detail for the audit-failure branch - *"the normal success result, `is_error=False`, with a `warnings` array in its structured content"* - so a success payload envelope now exists and `request_id` is still not on it. Consequence worth stating: C1-R1 (`DESIGN.md:1261`, **High**, *"a write cannot be attributed to a caller"*) is declared mitigated on the audit event alone. The audit record exists; **the caller holds nothing that points at it** |
| **B43** | Exactly one structured log entry per request | `backend/request-middleware.md:145` - *"4. **One log per request**: The middleware emits exactly one structured log entry per request."* | PARTIAL | **NOT-APPLICABLE** | **CLOSED** | **CLOSED by FIX-11, via ADR-0011.** The deviation is recorded with why the third producer is forced and what it costs while B40 is open. Original finding: Unchanged. `DESIGN.md:846` adopts `Timing` **and** `StructuredLogging`; `DESIGN.md:449` adds `audit.py` on top, with a good reason (`include_payloads=False` emits no arguments at all). Three producers per invocation against a numbered rule that says one. The design never reconciles it and no ADR covers it. **This is the cheapest defect on the list to fix** - it is one ADR, and the deviation is already argued in prose at `DESIGN.md:449-454` |

### 3.5 Python and blessed libraries

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B47** | Pydantic `>=2.10`, `httpx`, `tenacity ^9` + `circuitbreaker ^2`, `uv`, ruff/mypy/pytest | `architecture/reference-architecture.md:85` - *"\| Models/validation \| Pydantic \| `>=2.10` \| v2 API \|"*; `:95` - *"\| Resilience \| tenacity + circuitbreaker \| `^9` / `^2` \| retry + circuit breaker; `circuitbreaker` (fabfuel) is async-aware + maintained, in-process state"* | PARTIAL | **PARTIAL** | STILL-OPEN (circuitbreaker) / NOT-YET-BUILT (pydantic floor) | **`circuitbreaker` is still never named anywhere in `DESIGN.md`** - zero occurrences. §4.3 says *"One circuit breaker for Jobvite"* and never says what implements it, while the standard pins a specific library and says why (async-aware, and the named alternatives are unmaintained). §12 already flags the breaker as the one mechanism in §4.3 *"beside a measured retry finding"* with **no supporting execution anywhere** (`DESIGN.md:1464-1466`), so the unnamed library and the unevidenced mechanism are the same soft spot. The **Pydantic `>=2.10` floor** is still unstated, but a committed `uv.lock` plus `uv sync --frozen` (B64/B65, now satisfied) pins the resolve at 2.13.4, so the floor is met by the lock even though the manifest never declares it |
| **B49** | Line length 88; comments and docstrings 72 | `backend/python.md:35` - *"- Maximum line length: **88 characters** (`ruff format` default)"*; `:36` - *"- For comments and docstrings: **72 characters**"* | UNADDRESSED | **UNADDRESSED** | NOT-YET-BUILT | Not in `DESIGN.md`. A `pyproject.toml` line, and `pyproject.toml` does not exist yet. Nothing wrong is locked in |
| **B50** | Type hints on all public functions; Google- or NumPy-style docstrings | `backend/python.md:97` - *"Use Google-style or NumPy-style docstrings"*; `documentation/agentic-coding-standard.md:169` - *"- [ ] Python has type hints on all public functions"* | UNADDRESSED | **PARTIAL** | NOT-YET-BUILT | Corrected verdict, see §2. Type hints are gated by the `types` CI job (`DESIGN.md:1101`). **Docstring style is still unstated**, and §8 leans on a docstring carrying a load-bearing warning (`DESIGN.md:917-918`: *"That sentence is in the test module's own docstring"*), so docstrings here do work no linter checks |
| **B51** | `datetime.now(UTC)`; `datetime.utcnow()` forbidden | `backend/python.md:227` - *"Never use `datetime.utcnow()` — deprecated since Python 3.12 (returns naive datetime missing tzinfo)."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Still zero occurrences of UTC, timezone, or `utcnow` in `DESIGN.md`. Three live surfaces, unchanged: §5.1's `timestamp` on every problem object, §7.5's approval, and **§9 hazard 2** (`DESIGN.md:988`), which names the epoch-millisecond-versus-`yyyy-MM-dd` asymmetry as a hazard *"needing explicit handling"* and then does not say which representation wins. **This is the only lint-family obligation I would not group with the others**: it is a named hazard whose handling the design declines to specify, and a naive datetime there produces a wrong answer rather than a type error |
| **B52** | Naming per the table: snake_case functions/modules, PascalCase classes and models, UPPER_SNAKE_CASE constants | `backend/python.md:64-71` (the naming table) | UNADDRESSED | **UNADDRESSED** | NOT-YET-BUILT | Unchanged. De facto satisfied by §3's module layout and by ruff's defaults; nothing commits to it. Lowest consequence in the sweep |
| **B53** | Secrets as `SecretStr` via pydantic-settings, `.get_secret_value()`; committed `.env.example` with names only | `architecture/security.md:469` - *"# Always use .get_secret_value() to access secrets"*; `:418` - *"# .env.example (commit this)"* | PARTIAL | **PARTIAL** | NOT-YET-BUILT | Code half still fully satisfied (`DESIGN.md:247-248`, `:604-608`). The `.env.example` half is B91 and is genuinely absent from disk and design both |

### 3.6 Testing

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B55** | pytest with `asyncio_mode = "auto"`, `--strict-markers`, declared markers, `branch = true` | `backend/testing.md:59` - `asyncio_mode = "auto"`; `:67` - `"--strict-markers"`; `:82` - `branch = true` | PARTIAL | **SATISFIED** | **CLOSED** | **CLOSED by FIX-11.** §8 now states all four pytest configuration items and carries a required case asserting an undeclared marker fails collection; §7.3's citation resolves. This closed the substance, not just the citation. Original finding: `branch = true` still implied by §8's 90%-branch requirement. The three configuration items are still absent - **and this revision introduced a cross-reference that asserts one of them exists.** `DESIGN.md:637` reads: *"A typo that silently disables a tool is exactly the shape of the `--strict-markers` problem in §8"*. **§8 contains no `--strict-markers` discussion.** I read §8 end to end (`DESIGN.md:899-979`); the string does not occur there or anywhere else in the document. §7.3 points at a control §8 does not have, which is precisely the failure the sentence is warning about. The substantive risk is unchanged and is the one §8 can least afford: §8's whole credential-free strategy rests on `DESIGN.md:901-903` - *"credential-dependent tests are excluded by *selection*, not marked `skipif`"* - and a mistyped selection marker without `--strict-markers` selects nothing silently |
| **B56** | Coverage floor 80%; sub-targets Services 90%, API Routes 85%, **Utilities 95%** | `backend/testing.md:96` - `fail_under = 80`; `:588` - *"\| Utilities \| 95% \| Pure functions are easy to test \|"* | PARTIAL | **SATISFIED** | *(closed)* | `DESIGN.md:969-970` now sets *"**95% on `utils/` - the standard's own Utilities target, kept rather than remapped**"*, and `DESIGN.md:973-975` states why: `utils/redaction.py` holds two Critical-rated controls and the earlier remap left it at the floor. **ADR-0010 records the remap and explicitly records the correction**, which is the ADR mechanism working as intended. The risk inversion the earlier sweep found is gone |
| **B58** | A collection-guard meta-test inside a configured `testpaths` root, passing in CI | `backend/testing.md:138` - *"2. **A collection-guard meta-test is required.** Add a meta-test that walks"* [the repository for `test_*.py` files]; `devops/quality-gates.md:79` - *"MUST be present in a configured root and MUST pass in CI. If the guard is"* [absent ... the CI backend test job MUST fail] | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | **The mandated guard is still absent, and §8's structure still makes it more necessary here than in a normal repository.** `DESIGN.md:905-908`'s `--collect-only` against the live suite is a different control for a different failure: it proves the *excluded* suite still imports. The guard proves no `test_*.py` is unreachable from `testpaths` at all. §8 deliberately maintains **two** suites with different selection, which is the configuration in which an orphaned third file is least visible. `quality-gates.md:79` makes the CI job's failure **mandatory** in its absence, so this is a required-check breach rather than a preference |
| **B59** | CI runs pytest with no positional path so `testpaths` is authoritative | `backend/testing.md:166` - *"3. **CI must run all roots.** The CI `pytest` invocation MUST NOT restrict"* [to a single directory via a positional argument] | PARTIAL | **PARTIAL** | NOT-YET-BUILT | Unchanged: exclusion is by selection, which is the compliant mechanism, but the design still never states the CI invocation, and §8's `--collect-only` pass necessarily takes a target. A workflow-YAML line. Compounded by B58: with no guard, nothing catches a shadowing positional path |
| **B61** | Test names follow `test_{what}_{when}_{expected}` | `documentation/agentic-coding-standard.md:346` - *"# Python: test_{what}_{when}_{expected}"* | UNADDRESSED | **UNADDRESSED** | NOT-YET-BUILT | Unchanged. §8's required cases are still prose descriptions. Low consequence, with the standing caveat that a test *name* is an unverified claim about its *body*, and this convention exists to make that claim checkable |

### 3.7 CI/CD and supply chain

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B64** | Frozen installs: `uv sync --frozen` | `devops/supply-chain-security.md:77` - *"- Python: `uv sync --frozen` (fails if `uv.lock` is out of date)."*; `devops/ci-cd.md:179` - `run: uv sync --frozen` | UNADDRESSED | **SATISFIED** *(design)* | NOT-YET-BUILT *(artifact)* | `DESIGN.md:1060-1064` closes it and names its own earlier failure: *"**The lockfile is the actual cure and it was missing.** This section argues that a transitive bump broke code with zero change to that code, then pinned three packages by hand - which diagnoses the disease and does not prescribe the remedy. `uv.lock` is committed, CI runs `uv sync --frozen`, and the SBOM is generated from that frozen resolve."* Backed by a §8 case (`:929-933`) and by C9-T1 (`:1320`). **No `pyproject.toml`, no `uv.lock` and no CI workflow exist on disk yet** - the specification is complete, the artifact is not |
| **B65** | `uv.lock` committed and pinning transitives | `devops/supply-chain-security.md:69` - *"- **Python**: `uv.lock` MUST be committed (see"*; `:73` - *"- **Transitive** dependencies MUST be pinned by the lockfile, not just"* [direct dependencies] | UNADDRESSED | **SATISFIED** *(design)* | NOT-YET-BUILT *(artifact)* | Same sentence at `DESIGN.md:1062`. The hand-pinning of three packages is now correctly framed as a supplement to the lock rather than a substitute for it |
| **B66** | An unpinned or floating install never runs in CI or an image build | `devops/supply-chain-security.md:81` - *"unpinned) **MUST NEVER** run in CI or in an image build. It defeats"* [reproducibility] | PARTIAL | **SATISFIED** | *(closed)* | Follows from B64/B65 being specified: `uv sync --frozen` **is** the install command the design names for CI, and §8 tests for lock drift (`uv lock --check` succeeding without amending `uv.lock`). The design does not use the word *never*, which is why this is a judgement rather than a quotation `[REASONED]` - but there is no longer any install path in the design that could float |
| **B72** | A known advisory that cannot be remediated is tracked, not silently suppressed | `devops/supply-chain-security.md:131` - *"an explicit, time-bounded, reviewed suppression"* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | No triage or suppression policy anywhere. Now modelled: `DESIGN.md:1371` is C9-D1, marked *"**Open (B72).**"*, disposition `unmitigated (B72)`, and it is on the mitigate-before-production-release list (`:1356-1358`). The row states the mechanism itself: *"`pip-audit` has no severity threshold and fails on any advisory. We chose a beta stack deliberately and owe it an advisory-triage policy; the unsanctioned workaround is a blanket ignore, which is the silent suppression the clause forbids"* |
| **B73** | PR titles carry a traceability ID | `devops/quality-gates.md:49` - *"- [ ] Descriptive title with ID: `[FEAT-XXX] Description`"*; prefixes at `:225-228` | UNADDRESSED | **UNADDRESSED** | **DEFERRED-WITH-REASON** | Verdict unchanged; **category upgraded, and this is a real improvement.** `docs/adr/README.md` now carries a section headed *"Acknowledged non-conformances without an ADR"* recording that the corpus contradicts itself on the prefix - `agentic-coding-standard.md` expects FEAT/FR/BUG/TECH, `development-workflow.md:166` expects layer-prefixed `[FE-001]`, and this work is tracked as `EC-###` - and concluding that *"Inventing a prefix to satisfy a clause the standards cannot agree on would move the defect rather than fix it."* That is a decision on the record, which is what this category is for |
| **B74** | No `TODO` without a ticket reference | `documentation/agentic-coding-standard.md:171` - *"- [ ] No `TODO` comments without ticket reference (e.g., `# TODO(FEAT-001): ...`)"* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Still unstated, and the CI step the standard specifies is still not among §10's jobs. Inherits B73's prefix problem: a `# TODO(EC-123)` uses a prefix the standards do not recognise, so satisfying B74 as written is currently impossible in the same way B73 is. Nobody has connected those two |
| **B75** | No commented-out code blocks | `documentation/agentic-coding-standard.md:173` - *"- [ ] No commented-out code blocks"* | UNADDRESSED | **UNADDRESSED** | NOT-YET-BUILT | Unchanged. Lint-level, lowest consequence |
| **B76** | `.github/workflows/` is a protected path agents do not auto-modify | `documentation/agentic-coding-standard.md:66` - *"### Always Protected (Never Auto-Modify)"*, with `.github/workflows/         # GitHub Actions` at `:94` | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Still unstated, and **materially more live than when it was first raised**: `.github/workflows/mirror.yml` now exists and is the repository's only workflow, §10 mandates ten more CI gates that agents will be asked to author, and this project runs agents against this tree continuously. The protected-path rule is the thing that stops an agent editing the gate that is failing it |

### 3.8 Documentation

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B77** | `README.md` contains all fourteen sections, in order, exact headings | `documentation/readme-standard.md:43` - *"Every README MUST contain the following sections, in this order. Section headings must match exactly so that automated checks can locate them."*; list at `:45-58` | UNADDRESSED | **PARTIAL** | **DEFERRED-WITH-REASON** | §10.1 now fixes the specification: `DESIGN.md:1120-1121` - *"**All fourteen sections, headings matching exactly**, because automated checks locate them by heading text."* **No `README.md` exists at the repository root** - confirmed against `git ls-files`, not inferred. The design states why: `DESIGN.md:1112-1115` - *"**The README is not written yet, deliberately**: it would have to assert a Quickstart that reaches 'a working state', live CI badges, and a test command, for software that does not exist."* Specification discharged, artifact not produced, reason recorded |
| **B78** | The Configuration table lists **every** environment variable, with `Name`, `Required`, `Default`, `Description`, no real values | `documentation/readme-standard.md:50` - *"6. **Configuration** — a table of environment variables with columns: `Name`, `Required`, `Default`, `Description`. Secrets are referenced by name only; never include real values."*; `:66` - *"every environment variable read by the component MUST appear in the Configuration table."* | UNADDRESSED | **PARTIAL** | **DEFERRED-WITH-REASON** | **DEFECT CLOSED by FIX-11.** The hand-kept enumeration is removed rather than corrected; `.env.example` is the single enumeration the README table is checked against, and the two still-unnamed variables are recorded as open. The obligation stays PARTIAL only because the README itself is deferred with B77. Original finding: §10.1 now commits to the table and the same-PR update rule (`DESIGN.md:1122-1125`) - a large improvement. **But the enumeration it commits to is wrong.** It reads *"the **four** credential variables"*; §7.3's own requirements table at `DESIGN.md:644-647` names **five**: `JOBVITE_API_KEY`, `JOBVITE_API_SECRET`, `JOBVITE_FEED_KEY`, `JOBVITE_FEED_SECRET`, `JOBVITE_COMPANY_ID`. `JOBVITE_COMPANY_ID` is the job feed's separate credential, which §4.1 calls out as its own credential class. The clause B78 enforces is *every* variable, so an off-by-one in the committing sentence produces exactly the incomplete table the clause forbids. The §7.7 result-cap variable is also still unnamed, which is B15 |
| **B79** | README ≤ 500 lines; overflow moves to `docs/` | `documentation/readme-standard.md:64` - *"- **Length cap**: 500 lines. Content beyond the cap MUST be extracted to `docs/` and linked."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Still unstated - and §10.1 has made it a live constraint rather than a formality by loading the README with fourteen sections, a configuration table of ten-plus variables, **six** must-document behaviours (`DESIGN.md:1131-1147`), Jobvite's operating envelope, and an `mcp-name:` string. Nothing acknowledges the cap or names what goes to `docs/` when it is hit |
| **B80** | Quickstart commands exercised by CI on every merge to the default branch | `documentation/readme-standard.md:67` - *"- **Quickstart parity**: the Quickstart commands MUST be exercised by CI on every merge to the default branch."* | UNADDRESSED | **SATISFIED** | *(closed)* | **The best-resolved item in the sweep.** `DESIGN.md:1149-1162` takes the tension the earlier sweep identified and resolves it in the right direction, correcting a draft that had been wrong in both halves: the credential-free path (install, start the server, list tools) *is* CI-exercisable, and `readme-standard.md:83` independently forbids the workaround the draft proposed. Conclusion at `DESIGN.md:1160` - *"**So the Quickstart is credential-free in full, and CI exercises all of it.**"* |
| **B81** | Badges point at live sources; static stale SVGs forbidden | `documentation/readme-standard.md:70` - *"- **Badges are live**: each badge MUST point at a live source. Static SVGs that no longer reflect reality are forbidden."* | UNADDRESSED | **PARTIAL** | **DEFERRED-WITH-REASON** | `DESIGN.md:1164-1166` addresses it directly: *"**A CI status badge still cannot be live until CI exists**, since `:70` forbids a static badge that does not reflect reality. That one is genuinely deferred until the implementation lands, not excused."* The distinction between deferred and excused is drawn explicitly, which is the whole point of this category |
| **B82** | A link checker runs in CI; a broken link blocks merge | `documentation/readme-standard.md:69` - *"- **Links are checked**: a link checker MUST run in CI; a broken link blocks merge."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | I read §10's CI enumeration in full (`DESIGN.md:1095-1106`): `check-coupling.py`, lint, format, types, tests, `pip-audit`, CodeQL, TruffleHog, SBOM in both formats, `pip-licenses`, `fastmcp inspect` diff. **No link checker.** Live rather than academic: `DESIGN.md:659-660` and `:852-853` treat two upstream GitHub issues as load-bearing evidence, and `CHANGELOG.md` links the same two |
| **B83** | `CHANGELOG.md` per Keep a Changelog 1.1.0 with a top `## [Unreleased]` | `documentation/changelog-standard.md:42` - *"The changelog MUST follow [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Top-level structure:"* | UNADDRESSED | **SATISFIED** | *(closed)* | **Satisfied by an artifact the design never mentions.** `CHANGELOG.md` is committed at the repository root; its header cites Keep a Changelog 1.1.0 and SemVer by name, and `## [Unreleased]` is the top section. The earlier verdict was assessing `DESIGN.md`, which still says nothing about a changelog - a gap in the design's §10 coverage, but not an unmet obligation |
| **B84** | Breaking changes prefixed `BREAKING:` with a migration note, triggering a major bump | `documentation/changelog-standard.md:91` - *"- **Breaking changes**: every breaking change MUST be prefixed `BREAKING:` in the bullet and MUST include a \"Migration\" sub-bullet or link to a migration note. A breaking change MUST trigger a major-version bump."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Not in `DESIGN.md`, not in `CHANGELOG.md`'s own conventions, and not in `changelog.d/README.md`, which enumerates the six permitted headings and says nothing about `BREAKING:`. **B5 still needs it**: `error-contract.md:210` makes a published `type` URI a contract whose change is a breaking change, and with no breaking-change discipline B5's stability half has no enforcement mechanism anywhere. The two remain one gap |
| **B85** | Security fixes under `### Security` with a CVE where one exists | `documentation/changelog-standard.md:92` - *"- **Security entries**: vulnerabilities fixed MUST appear under `### Security` with a CVE identifier when one exists; embargoed details MAY be omitted but the entry itself MUST appear."* | UNADDRESSED | **SATISFIED** | *(closed)* | `CHANGELOG.md` carries a `### Security` block under `[Unreleased]` with four entries, including the confidential-PDF purge. The CVE half is untriggered - no advisory has been remediated - so it is satisfied structurally and untested in substance. Still compounded by B72: with no advisory-triage policy, there is no process that produces a remediation for this section to record |
| **B86** | Internal-only changes MUST NOT appear in `CHANGELOG.md` | `documentation/changelog-standard.md:94` - *"- **Internal-only changes**: refactors, test-only changes, and CI changes that produce no user-visible effect MUST NOT appear in `CHANGELOG.md`. They live in commit history only."* | UNADDRESSED | **SATISFIED** | **CLOSED** | **CLOSED by FIX-11.** The two offending entries are removed and the governing rule, with where the line falls on a pre-release documentation repository, is written into `changelog.d/README.md`. Original finding: **The only documentation obligation where an artifact exists and breaches the clause**, rather than being absent. `CHANGELOG.md`'s `### Added` block contains at least two entries that are CI or tooling changes with no user-visible effect: *"`docs/reviews/check-coupling.py` and its control harness ... **Wired into CI**"*, and *"Repository scaffolding: gitignore, the changelog-fragment workflow that keeps parallel agent work off a single shared file, and the docs layout."* **The mitigating argument, stated so the reader can weigh it:** this is a pre-release repository whose only shipped output so far *is* documents, so the line between internal and user-visible is genuinely blurred here. That argument is not written down anywhere, which is what makes it a defect rather than a deviation - it would be disposed of by one sentence in `changelog.d/README.md` |
| **B87** | Release dates equal publication date; backdating forbidden | `documentation/changelog-standard.md:93` - *"- **Date integrity**: a release date MUST equal the date the artifact was published. Backdating is forbidden."* | UNADDRESSED | **NOT-APPLICABLE** | *(corrected)* | See §2. No release exists; `CHANGELOG.md` holds only `## [Unreleased]`. Becomes live at the first tag |

### 3.9 Licensing and repository hygiene

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B89** | The README License section names an SPDX identifier and links to `LICENSE` | `documentation/readme-standard.md:57` - *"13. **License** — SPDX identifier and link to `LICENSE`."* | PARTIAL | **PARTIAL** | **DEFERRED-WITH-REASON** | Substance settled and settled well (`DESIGN.md:1031`: Apache-2.0, `Copyright 2026 evolv Consulting`, with a NOTICE), and `LICENSE` and `NOTICE` are both committed. The obligation is specifically about the **README section**, which B77 defers with a stated reason. The right thing exists with nowhere yet to be declared |
| **B90** | `.env` and key material gitignored; `.env.example` is the committed template | `devops/environments.md:616-621` - the gitignore block: `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`, `secrets/` | UNADDRESSED | **SATISFIED** | **CLOSED** | **CLOSED.** C8-I1 reads `Mitigated` and names `.gitignore` consistently with boundary B6; `*.pem` and `secrets/` are present. Verified in the artifacts. Original finding: **`.gitignore` exists and is committed.** It covers `.env`, `.env.*`, `!.env.example` and `*.key`, plus a vendored-document block responding to the PDF incident. Against `environments.md:616-621` it is **missing `*.pem` and `secrets/`** - so PARTIAL on substance. **The defect is in the design, not the file.** `DESIGN.md:1358` (C8-I1, rated **Critical**) asserts *"**Gaps: no `.gitignore` policy is stated (B90) and no `.env.example` exists (B91)**"* and carries the disposition `unmitigated (B90, B91)`, and `DESIGN.md:1392` puts it on the must-mitigate-before-implementation list. Meanwhile `DESIGN.md:1249` - the trust-boundary table, in the same section - already names *"`.gitignore`"* among boundary B6's controls. **§11 contradicts itself and contradicts the repository, in the table the freeze decision reads.** Freezing preserves a Critical row that misdescribes the deployed control set in both directions: it denies a control that exists, and it does not notice the two patterns that control is actually missing |
| **B91** | `.env.example` lists every variable, placeholder values only | `devops/environments.md:144` - *"# .env.example - Copy to .env.local and fill in values"*; `documentation/readme-standard.md:50` - *"Secrets are referenced by name only; never include real values."* | UNADDRESSED | **SATISFIED** | **CLOSED** | **CLOSED.** `.env.example` is committed with every value empty. Original finding: Genuinely absent from disk and from the design. Named as an action item at `DESIGN.md:1392`, and `.gitignore` already carries the `!.env.example` negation waiting for it. Its content is fully determined by §7.3's requirements table plus §10.1's enumeration, so this is a file to write, not a decision to make |
| **B96** | Third-party API keys rotate quarterly, and on any suspicion of exposure; enforced, with a runbook | `devops/environments.md:636` - *"\| Third-party API keys (Stripe, SendGrid, etc.) \| Quarterly \| Vendor breach notice, key found in logs \|"*; `:626` - *"Rotation MUST be enforced (not aspirational) for every secret class."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | No rotation policy or runbook reference anywhere. I checked `DESIGN.md` (zero occurrences of any form of "rotat") and read `SECURITY.md` in full - it covers reporting, scope, data handling and three disclosed limitations, and says nothing about rotation. **This server's entire reason to exist is holding third-party API keys** - three credential classes by §4.1's own count. The standard's unscheduled trigger is literally *"key found in logs"*, which is the exact event §4.1's redaction test is built to prevent: **the design builds the detection and not the response**, and `:626` forecloses the informal reading |

### 3.10 Development workflow and required checks

| B | Requires | Clause (re-verified) | Was | Now | Category | Evidence / what is still missing |
|---|---|---|---|---|---|---|
| **B97** | Branch names follow the documented pattern | `devops/development-workflow.md:63` - *"\| Feature (Backend) \| `feature/BE-{ID}-short-description` \| `feature/BE-001-user-api` \|"*; `:66` - *"\| Bugfix \| `bugfix/{PREFIX}-{ID}-short-description` \| `bugfix/FE-015-form-validation` \|"* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN (acknowledged) | ADR-0006 now names it - *"**B97, branch naming**, is an independent clause the branch-model deviation does not touch. It also collides with the ticket-prefix conflict noted in the ADR index."* **That is an acknowledgement, not a disposition.** The ADR says the clause survives its deviation intact and then leaves it unmet, which is the correct scoping and an open obligation. Compounded by the same `{PREFIX}` collision as B73 |
| **B98** | `main` protected: PR required, ≥1 approval, all CI checks pass, no direct pushes, merge only from develop or hotfix | `devops/development-workflow.md:73` - *"- Requires PR with at least 1 approval"*; `:75` - *"- No direct pushes"*; `:76` - *"- Only merge from develop or hotfix branches"* | UNADDRESSED | **PARTIAL** | NOT-YET-BUILT | **Upgraded.** ADR-0006 disposes of the develop/hotfix clause (necessarily voided by removing `develop`) and states that the remaining properties *"**relocate onto `main`** rather than retiring"* - pull request, at least one approval, all CI green, branch current, squash merge. So the obligation is now on the record and assigned. What is missing is the **wiring**: nothing says these are configured branch-protection rules, and no CI workflow exists to be a required check. (Minor: ADR-0006 says *"B99's four properties"* and then lists five.) |
| **B100** | A PR template exists with the mandated sections | `devops/quality-gates.md:50` - *"- [ ] Completed PR template"*; template at `devops/development-workflow.md:202-241` | UNADDRESSED | **UNADDRESSED** | NOT-YET-BUILT | `.github/` contains exactly one file, `workflows/mirror.yml`. No PR template. A file to write |
| **B101** | Reviewers verify the code-review checklist before approving | `devops/development-workflow.md:248` - *"Reviewers must verify all items before approving:"* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | Unchanged. The Security and Type Safety blocks of that checklist apply directly here; the frontend items do not, and nobody has said which subset binds |
| **B102** | Squash merge; delete the branch after merge | `devops/development-workflow.md:192` - *"│   - Squash and merge                                            │"*; `:194` - *"│   - Delete feature branch after merge                           │"* | UNADDRESSED | **PARTIAL** | NOT-YET-BUILT | Squash is now carried by ADR-0006's relocation list. Branch deletion is still unstated |
| **B103** | A README exists at the repo root, with all fourteen sections | `documentation/readme-standard.md:32-35` - *"A `README.md` is **required** in each of the following locations: - The top level of every Git repository. - The root of every published package (npm, PyPI, Cargo, Go module, container image, Helm chart)."* | PARTIAL | **PARTIAL** | **DEFERRED-WITH-REASON** | Same disposition as B77. Both triggers still fire: this is a Git repository root, and §10 makes it a published package. `git ls-files` confirms no `README.md` at the root. The design now presumes the README as a specified artifact rather than only as a place to put caveats, which is the half that moved |
| **B104** | Contributing rules present - `CONTRIBUTING.md` or inlined under the heading | `documentation/readme-standard.md:56` - *"12. **Contributing** — link to `CONTRIBUTING.md` or equivalent. Repos without that file must inline the contribution rules under this heading."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | No `CONTRIBUTING.md`, and §10.1 does not list contribution rules among what the README must carry. Still the corpus's only contributor-facing obligation, and still live: the repository is public and org-owned, and §10's two commit-time gates - pre-commit secret scanning and the committed-file-type gate with its same-commit allowlist-override rule - are exactly the local setup an outside contributor cannot discover without being told |
| **B105** | Named maintainers in the README | `documentation/readme-standard.md:58` - *"14. **Maintainers** — named owners (people or team aliases) responsible for review and release."* | UNADDRESSED | **UNADDRESSED** | STILL-OPEN | §10.1 commits to all fourteen sections, which formally includes this one, but nobody has named an owner anywhere in the repository. `SECURITY.md` gives a reporting address and not an owner. Deferred with B77 in form; unowned in substance |
| **B106** | Required checks wired to branch protection; skipped ≠ success; path-filtered jobs gated through an aggregator | `devops/ci-cd.md:679` - *"1. **Do not set `skipped == success` for required checks.** GitHub branch"* [protection allows treating a skipped job as passing]; `:723` - *"4. **Path-filtered jobs that skip are not required checks.** A job that may"* [legitimately not run] | PARTIAL | **PARTIAL** | STILL-OPEN | §10 now enumerates eleven jobs and §8 satisfies the test-level half of skipped≠success (zero skips, a skip counts as a failure). **The wiring is still absent**: nothing says any job is a *required* check, and neither structural rule is addressed. The aggregator rule now has a concrete referent in the repository rather than a hypothetical one: `.github/workflows/mirror.yml` is guarded by `if: ${{ secrets.MIRROR_TOKEN != '' }}`, so it is a job that may legitimately not run - exactly the shape `:723` forbids wiring directly to branch protection. §10's `fastmcp inspect` diff and the two commit-time gates are naturally path-filtered and have the same exposure. The earlier sweep's line still holds: a gate nothing blocks on is a report |

---

## 4. Ranked by whether freezing locks it in badly

The brief's question. An obligation that only needs code is safe to freeze around; one the design
contradicts is not. **Freezing does not make an unbuilt thing harder to build. It makes a wrong
sentence expensive**, because after the freeze only a numbered ADR may change `DESIGN.md`
(`DESIGN.md:17-20`).

### Tier 1 - CLOSED. Every defect that argued against freezing has been fixed.

Each of these was a sentence that would have been implemented as written. All nine are closed, and
each entry below records what the defect was and what replaced it, because a ranking that simply
deleted them would destroy the reason the fixes exist.

1. **B7 - upstream 4xx passed the Jobvite status straight through. CLOSED.** §5.1 now carries a
   condition-to-type-to-status table mapping every Jobvite failure including its 4xx onto
   `/problems/external-service-error` at **502**, per the registry. Jobvite's own status and message
   move to `detail` and the audit event, *"where they help whoever is debugging, rather than in
   `status`, where they mislead whoever is calling"*.

2. **B5 - four invented problem slugs and a 400/422 mismatch. CLOSED.** The custom
   `/problems/jobvite-*` types are gone; §4.3 now distinguishes an open breaker from an outage
   through `detail` rather than by minting a contract-bearing type URI, and §5.1 states that
   validation is **422** per the registry, not 400.

3. **B25/B30 cross-cutting - §2.1 claimed a 400 problem object §5.1 rules out. CLOSED by FIX-11.**
   §2.1 now states what a caller actually receives: every one of its checks lives in the input
   models, so all of them run before the tool body and are raised by the framework, and **nothing
   on that path can return a problem object**. §5.1's third exception is widened from *"an
   argument-schema violation"* to all three inbound controls, which is what let §2.1 contradict it
   without any reader noticing. The registry's 422 validation row is recorded as **unreachable
   pre-dispatch** and serving in-body validation only, so a slug that covers half of validation is
   not cited as covering all of it.

4. **B90 - §11 asserted the absence of a committed `.gitignore`. CLOSED.** C8-I1 now reads
   `Mitigated` and names the file as a control consistently with boundary B6, and the two patterns
   the file genuinely lacked, `*.pem` and `secrets/`, are present. Verified in `.gitignore` and in
   §11, not taken from the report of it.

5. **B78 - the config table committed to "the four credential variables" and there are five.
   CLOSED by FIX-11.** The hand-kept enumeration is removed rather than corrected, because
   restating it would only reset the clock: `.env.example` is now the single enumeration and the
   README table is checked against it, which is §2.1's generated-fencing-paths argument applied to
   configuration. The miscount is recorded, and the two variables that are specified but still
   unnamed (§7.7's result cap, §4.4's rate-limit setting) are stated as an open item so neither
   list reads as complete.

6. **B55 - §7.3 cited §8 for a `--strict-markers` control §8 did not contain. CLOSED by FIX-11.**
   §8 now states the pytest configuration the exclusion strategy rests on - `asyncio_mode`,
   `--strict-markers`, a declared `markers` list, `branch = true`, all four from
   `backend/testing.md` - explains why the first is load-bearing rather than housekeeping, and
   carries a required case asserting that an undeclared marker fails collection instead of
   selecting nothing. §7.3's cross-reference now resolves. **This closes B55's substance, not just
   the citation**: the three missing configuration items were the gap.

7. **B43 - three log producers against a rule that says exactly one. CLOSED by FIX-11, via
   ADR-0011.** The deviation is recorded rather than redesigned, which is what the brief called the
   cheapest fix in the tier and it was. The ADR states why the third producer is forced rather than
   chosen - `include_payloads=False` emits no arguments while B17 mandates redacted ones - why
   collapsing onto `audit.py` alone would leave the most-hit failure path with no record at all,
   and what the deviation costs while B40's `request_id_var` is still missing.

8. **B86 - `CHANGELOG.md` carried CI-only and tooling-only entries. CLOSED by FIX-11.** The two
   offending entries are removed. More usefully, the rule that governs the judgement is now written
   in `changelog.d/README.md`, where fragments are authored, including where the line falls on this
   repository specifically: a document published here is user-visible and gets an entry, the
   machinery that produces those documents does not. The tempting inference - no users, so nothing
   counts - is named and refuted, since it is what produced the breach.

9. **B33 - §4.3 claimed a retry budget "inside the inbound timeout" on a transport with no inbound
   deadline. CLOSED by FIX-11.** §4.3 now says plainly that `resilience.md:74-76` has no referent
   here, supplies the deadline the transport does not by bounding all attempts for one invocation
   with a configured outbound ceiling, and records where that does not reach: §7.5's abandoned
   approval hangs the call for a different reason and no outbound budget touches it.

**What this means for the freeze.** This document's case against freezing was Tier 1 and Tier 1 is
empty. What remains is Tier 2's five acknowledged blockers, Tier 3's twenty-two undecided
obligations, and Tier 4. **None of them is a wrong sentence.**
### Tier 2 - freezing is defensible only if the blocker list is honoured

These are open, correctly modelled, and carry a named action item. **They are safe to freeze around
only in the sense that the design already says they must be done first.** §11's governing rule is
`threat-modeling.md:86`, which requires inherent Critical and High mitigated **before
implementation proceeds** - so freezing with them open means freezing a document that instructs
against its own next step.

**One of the five has since closed (B91), leaving four**, and the must-mitigate table is down from
three rows to two: C5-R1 and C5-E1. FIX-11 also corrected the arithmetic paragraph under that
table, which still read *"Three"* after C8-I1 came off - a paragraph written specifically to stop a
stale count being carried forward had carried one forward itself.

10. **B39 + B40** - retries and breaker transitions unlogged; `request_id_var` absent. C5-R1, High,
    must-mitigate row 1. One gap, one remedy.
11. **B21** - the outbound Jobvite credential is unscoped. C5-E1, High, must-mitigate row 2.
12. **B91** - `.env.example`. **CLOSED.** The file is committed with every value empty, C8-I1 is
    mitigated with a §8 case, and it has come off the must-mitigate table. Two variables it will
    eventually need are still unnamed, which is B15 and is tracked there rather than here.
13. **B72** - no advisory-triage policy on a deliberately beta stack where `pip-audit` fails on any
    advisory. C9-D1, on the before-production list. The predicted failure - somebody adds a blanket
    ignore under deadline pressure - is the exact behaviour the clause forbids.
14. **B42** - `request_id` still absent from success results, while C1-R1 (High) is declared
    mitigated. The audit record exists; the caller holds nothing that points at it.

### Tier 3 - open, unmodelled, and nobody has decided. Freezing makes them invisible.

Not wrong, but a freeze is the moment the open list stops being read.

15. **B58** - the mandated collection-guard meta-test. `quality-gates.md:79` makes the CI job's
    failure mandatory in its absence, so this is a **required-check breach**, not a preference. §8's
    deliberate two-suite structure is the configuration in which an orphaned test file is least
    visible. Highest in this tier.
16. **B16** - tool descriptions: never mentioned in the design, and absent from the threat model
    too. The one payload sent to every model on every connection, with no owner and no review rule.
17. **B96** - no key-rotation policy or runbook, on a server whose purpose is holding three classes
    of third-party API key. `environments.md:626` forecloses the informal reading, and the
    standard's unscheduled trigger is the exact event §4.1's redaction test exists to prevent.
18. **B51** - `datetime.now(UTC)` unstated, while §9 hazard 2 names the epoch-ms/`yyyy-MM-dd`
    asymmetry as needing explicit handling and does not say which representation wins.
19. **B76** - `.github/workflows/` protected-path rule unstated, in a repository that now has a
    workflow, plans ten more gates, and runs agents against the tree continuously.
20. **B106** - no job declared a required check; the aggregator rule now has a live referent in
    `mirror.yml`'s conditional guard.
21. **B82** - no link checker, in a document that treats two upstream issue links as load-bearing.
22. **B84** - no breaking-change discipline, which is the mechanism B5 needs and does not have.
23. **B104**, **B105**, **B101**, **B97**, **B79**, **B74**, **B23** (unbounded-loop arm),
    **B47** (`circuitbreaker` unnamed, beside a mechanism §12 already flags as unevidenced),
    **B15** (the cap default).

### Tier 4 - safe to freeze. Only implementation is missing.

Nothing wrong is preserved and no decision is foreclosed. **This is the tier the freeze question is
really about, and it is the largest.**

- **Specified correctly, artifact not built:** B64, B65, B66 (lockfile and frozen install - fully
  specified, with a §8 case; no `pyproject.toml` or `uv.lock` on disk yet), B98, B102, B100, B59,
  B61, B75, B52, B49, B50, B53, B6, B17 (field naming).
- **Deferred with a stated reason:** B77, B103, B89, B81 (the README and its badge - deliberately
  not written, because asserting a Quickstart for software that does not exist is a false claim in
  the present tense), B73 (the ticket-prefix conflict, recorded in `docs/adr/README.md` as a
  knowing non-conformance rather than papered over).

**On freezing generally, since the ranking implies a view:** nothing in Tier 4 argues against a
freeze, and Tier 4 is where most of the twenty-four unaddressed obligations live. The case against
freezing today is Tier 1 and it is nine items, seven of which are one or two sentences each.

---

## 5. What I did not check, and why

Stated as limits on this document rather than as caveats, because a re-sweep that overstates its
coverage is worse than no re-sweep.

- **The 42 SATISFIED and 5 NOT-APPLICABLE rows were not re-verified.** The brief scoped me to the
  59 open rows. `DESIGN.md` has changed substantially since those verdicts were taken, and a change
  can break a satisfied obligation as easily as it can close an open one - §2.1's rewrite is
  directly under B9, B10 and B11, all recorded SATISFIED, and §5.1's new third exception sits
  inside B1's and B2's territory. **I have no evidence any of them regressed and I did not look.**
  The projected 52 in §1 therefore carries forty-seven verdicts I did not take.

- **I did not re-audit citations in `CONFORMANCE-B1-B106.md`.** That was CONF-3's job and its
  three defects (CD-1, CD-2, CD-3) stand. Every clause I quote above was re-opened at its own
  `grep -n` line, so this document does not inherit those line numbers - but I did not check the
  ones I had no reason to cite.

- **I did not execute anything.** No FastMCP behaviour, no `uv lock`, no test run. The B25/B30
  problem-object contradiction is identified by reading two sections that disagree; I did not run
  the validator to determine **which** of them is right, only that they cannot both be. Marked
  `[REASONED]` at the row.

- **I did not review `docs/adr/0001`-`0005`, `0007`, `0008` in full.** I read 0006, 0009 and 0010
  because three rows turned on their scope. The other seven were taken from `docs/adr/README.md`'s
  index and from §13's summaries. **If an ADR's body disposes of an obligation its index line does
  not mention, I would have missed it.**

- **I did not assess the obligations from `data-flow.md` and `threat-modeling.md`** that CONF-2
  derived. Those are outside B1-B106 and outside this brief.

- **I did not check whether the eleven CI jobs §10 specifies would actually pass**, or whether
  `check-coupling.py` covers what §11 claims it covers. FIX-7 and FIX-8 touched that gate twice and
  a third look was not mine to take.

- **`git ls-files` is my authority for what exists in the repository.** An untracked file would not
  appear; `git status --porcelain` was empty at the time of writing, so nothing is untracked, but
  the claim is about the index rather than the filesystem.

---

## 6. One thing this pass changed about how the count should be read

The earlier sweep assessed `DESIGN.md` and reported conclusions phrased as facts about the
repository - *"No changelog anywhere"*, *"`.gitignore` is never mentioned"* - and the second of
those was propagated into `DESIGN.md` §11 as a **Critical** threat-model row and a freeze blocker,
where it is now wrong. `CHANGELOG.md` was already committed when it was called absent.

The correct phrasing for a design-only verdict is *"the design does not specify it"*, which is a
different claim from *"it does not exist"* and licenses a different response. Two obligations in
this sweep (B83, B85) were closed by files nobody had looked at, and one defect (B90) exists only
because a design-only absence was written down as a real one.

**A design sweep measures a document. Saying so in the verdict costs one clause and prevents this.**
