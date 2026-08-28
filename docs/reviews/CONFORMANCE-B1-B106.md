# B1-B106 conformance sweep of DESIGN.md revision 2

**Task:** CONF-1 · **Author:** conformance-sweep · **Date:** 2026-08-27

**Subject under test:** `docs/DESIGN.md` (DRAFT revision 2, last updated 2026-08-27 03:15 PM CDT).
**Obligation list:** `docs/research/STANDARDS.md` §1 and §6.4-§6.5, B1 through B106.
**Authority:** every clause was re-opened at its `file:line` in
`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/`. STANDARDS.md was
treated as a secondary source throughout; quotes below come from the standards files, not from it.

Verdicts are against **the design document only**. No code exists yet. "UNADDRESSED" means *the
design does not speak to this obligation*, not that the eventual implementation will fail it. That
distinction matters most in the CI/CD and documentation clusters, where many obligations are
conventionally handled in `pyproject.toml` and workflow YAML rather than in a design doc - but §10
does claim to cover repository and delivery, so silence there is a real omission of that section's
own scope.

---

## 1. Summary counts

| Verdict | Count |
|---|---|
| SATISFIED | 42 |
| PARTIAL | 22 |
| UNADDRESSED | 37 |
| NOT-APPLICABLE | 5 |
| **Total** | **106** |

**Headline: 37 obligations are genuinely unaddressed and 22 more are partial.**

The lead's two suspicions were both correct, and one was understated:

- **The CI/CD cluster (B63-B76) and documentation cluster (B77-B87) are where the gaps are.**
  Of the 25 obligations in those two clusters, **17 are UNADDRESSED**. §10 lists CI job *names*
  and stops; it never reaches lockfiles, frozen installs, README structure, or the changelog. The
  entire documentation cluster B77-B87 is unaddressed except B83's absence being total - eleven
  consecutive obligations with no design coverage at all.
- **The one-mechanism-two-clusters worry was justified, partly.** Allow-listed output models plus
  path-keyed fencing genuinely do cover B24 and B14 and the §6.2 EEO position. They do **not**
  cover B16 (tool descriptions - never mentioned in DESIGN.md), B25's control-character and
  encoding limits, or B30's inbound structural limits. The mechanism is an *output* control; three
  obligations in those clusters are *input* controls and fall outside it.
- **The testing cluster is weaker than believed.** B58's mandated collection-guard meta-test is
  **absent** - §8's `--collect-only` against the live suite is a different control solving a
  different problem - and `devops/quality-gates.md:79-81` says the CI backend test job MUST fail
  without it. The zero-skips rule (B60) is genuinely and explicitly satisfied; the coverage numbers
  (B56) are remapped without an ADR.

Two structural findings outside the table:

- **ADR-0002 is scoped too narrowly** (§5 below). It covers the Redis substitution but not the
  ProblemDetail that a rate-limit refusal loses, which is a separate clause of the same standard.
- **ADR-0006 is scoped too narrowly.** It disposes of B99 but leaves B97 (branch naming) and the
  "only merge from develop or hotfix" half of B98 undisposed.

---

## 2. Citation defects

Five defects. All were found by opening the cited file; none is fatal to the obligation, but each
would propagate a wrong `file:line` into a compliance claim. **CD-4 and CD-5 were added by the
CONF-5 citation-range audit** (`docs/reviews/CITATION-RANGE-AUDIT.md`), which also established why
this section's original two-pass method could not have found them - see the rewritten method note
below.

| # | Where | Defect |
|---|---|---|
| **CD-1** | **B45**, `documentation/agentic-coding-standard.md:173` | STANDARDS.md quotes *"No `console.log` / `print` debugging statements"* at `:173`. Line 173 actually reads `- [ ] No commented-out code blocks`. The quoted clause is at **`:172`**. Off by one. |
| **CD-2** | **B75**, `documentation/agentic-coding-standard.md:174` | STANDARDS.md cites `:174` for *"No commented-out code blocks"*. Line 174 is **blank**. The clause is at **`:173`**. Off by one, and it is the same off-by-one as CD-1 - B45 and B75 have swapped onto each other's neighbours. |
| **CD-3** | **§2/A1**, `architecture/error-contract.md:290` | STANDARDS.md §2/A1 sources the `instance` semantics - *"URI of the request that generated the error"* - to `:290`. **The file is 226 lines long.** Line 290 does not exist. The quote is real and correct, at **`:83`**. This one matters more than the other two: A1 is the adaptation DESIGN.md §5.1 relies on to justify its `urn:fast-mcp-jobvite:invocation:<request_id>` substitution, and it currently rests on a line number that cannot be checked. |
| **CD-4** | **B43**, `backend/request-middleware.md:471-477` | STANDARDS.md sourced the required-fields table to `:471-477`. **The file is 154 lines long.** The table is at **`:80-86`**. Corrected in STANDARDS.md. |
| **CD-5** | **§2/A3**, `backend/request-middleware.md:481-489` | STANDARDS.md sourced the LIFO middleware-ordering passage to `:481-489`. Same 154-line file. The passage is at **`:90-98`**. Corrected in STANDARDS.md. |

**CD-4 and CD-5 share one verified cause, and it is not carelessness.** `471-477` minus **391** is
`80-86`; `481-489` minus **391** is `90-98`. Both land exactly. Those two citations were taken from
a **compiled bundle** in which `request-middleware.md` begins at line 391 - `backend/` standards
carry a `compile_group` in their front matter - rather than from the standalone file. CD-3 is the
same species at a different offset. **Any citation in this corpus may have a bundle provenance**,
and an offset citation resolves cleanly against the bundle while pointing nowhere in the file a
reader will open.

One imprecision short of a defect, recorded for completeness:

- **B76** cites `documentation/agentic-coding-standard.md:93-96` for *"`.github/workflows/` is a
  protected path"*. Lines 93-96 are the CI/CD entries **inside** a fenced list; `.github/workflows/`
  is at `:94`. The binding language is the section heading at **`:66`** - `### Always Protected
  (Never Auto-Modify)`. The obligation is real and the path is where STANDARDS.md says; only the
  clause that makes it binding is elsewhere.

**What these two passes established, and what they structurally could not.** The original claim here
- *"All 106 B-numbers resolved to an existing file and an existing line"* - was **false**, and is
withdrawn rather than qualified. CD-4 and CD-5 are B-numbers citing lines past EOF, which is exactly
what the first pass reported finding none of.

The reason is a property of the matcher, not of the reading. Both defects are **bare continuation
citations**: a `` `:471-477` `` whose filename is carried over from a `file.md:N` reference earlier
in the same sentence. A matcher keyed on the `file.md:N` shape does not see them at all, so they
were never candidates and their absence from the results read as a clean pass. **A pass reports on
the citations its pattern can express; the ones it cannot express are silently outside the
denominator.** The corrected statement is: *every citation of the form `file.md:N` resolved to an
existing file and an existing line; continuation citations of the form `:N` were not checked, and
two of them were wrong.*

The same blind spot has a second consequence, established by CONF-5 and stated here because it
bounds what any verdict in §3 is worth: **a citation can resolve perfectly and still have stopped
short of the obligation it is offered for.** Seven ranges in this corpus contract between
`STANDARDS.md` and this document or the resweep, each dropping a clause tail - B40 dropped
`tool-calling.md:176-177`, the trace/span id, which then went untracked by any instrument for six
review rounds. A resolve-the-citation check passes on a contracted range, because a contracted range
is still a *correct* range. Those seven have been widened back to clause boundaries; the audit
document records which and why.

**Method, so the absence of further defects is a claim about what I actually did.** Two passes.
First, every `file.md:N` citation in every B-number was resolved mechanically against the standards
tree and the cited lines printed - that pass found CD-1, CD-2 and CD-3, and confirmed no citation
**of that form** names a missing file or a line past EOF. Second, every italic-quoted span in the B-list was checked for
verbatim existence *anywhere* in the file it is attributed to, to catch a fabricated or altered
quote rather than a merely misnumbered one. That pass raised 20 candidates and **all 20 resolved as
sound**: legitimate `...` / `…` elisions (B21, B58, B60, B67, B77, B103, B106), bullet lines joined
with `/` (B98), and markdown link or inline-code syntax inside the quoted span (B8, B19, B66, B83).

Two of those candidates were false negatives of my own tooling worth stating, because they cite the
standards repo's **`README.md`** rather than a file under `standards/` and so fell outside the
first pass entirely. Both were then checked by hand and **both are correct**:

- **B89 / §6.2's copyright reasoning** - `README.md:3` - *"Organization-wide development standards,
  patterns, evaluation criteria, and examples for Evolv Consulting projects."* ✓
- **B106 / §6.6's authority note** - `README.md:13-16` - *"| `standards/` | Mandatory rules and
  conventions | Required | | `patterns/` | Advisory implementation patterns | Recommended | |
  `evaluation/` | Quality rubrics, guardrails, compliance checklists | Optional | | `examples/` |
  Reference implementations | Optional |"* ✓

The second of those matters beyond its own B-number: it is the sole source for STANDARDS.md §6.6's
ruling that `evaluation/compliance/` is `priority: optional` and therefore that **the GDPR and
OWASP checklists do not bind**. DESIGN.md §6.2 rests on that ruling when it frames the EEO
exclusion as a design decision rather than a cited obligation. **The ruling is correctly sourced
and holds.**

One nit, below the threshold of a defect: **B92** renders
`documentation/agentic-coding-standard.md:127` as *"Hardcode secrets, API keys, or passwords"*; the
file reads *"Hardcodes secrets, API keys, or passwords"*. A verb form changed to fit STANDARDS.md's
carrier sentence. No change of meaning.

**One substantive observation this pass turned up, outside the B-list.** `README.md:3` is the only
written form of the company name anywhere in the standards corpus, and it reads **"Evolv
Consulting"**. DESIGN.md §10 sets the copyright notice as **`Copyright 2026 evolv Consulting`**,
lowercase. STANDARDS.md §6.8 item 10 flagged the casing as unresolved and it is still unresolved;
the design picked a form that matches Phil's brief but not the only in-corpus precedent. On a
public, org-owned repository this is the copyright line of record, so it is worth settling
deliberately rather than by whichever document was open last. Routing to NEEDS-PHIL.md alongside
the entity-suffix question is the right disposition - it is a legal determination, not an
engineering one, and §6.2 already says so.

---

## 3. The full table, B1-B106

### Error contract (B1-B8)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B1** | RFC 9457 Problem Details on every error surface; no custom envelope | `architecture/error-contract.md:204` - *"1. **RFC 9457 shape**: All errors use the Problem Details object. No custom envelopes."* | **SATISFIED** | §5.1: *"No `success: true/false` envelope exists anywhere in this repository."* |
| **B2** | All seven elevated fields on every error | `architecture/error-contract.md:66` - *"We elevate `type`, `title`, `status`, `detail`, `instance`, `request_id`, and `timestamp` to required for consistency across our services."* | **SATISFIED** | §5.1 names all seven verbatim. |
| **B3** | `Content-Type: application/problem+json` on HTTP error responses | `architecture/error-contract.md:44` - *"All error responses MUST use the media type:"* | **NOT-APPLICABLE** (settled deviation, ADR-0003) | §5.2 states the clause is violated in the letter and no implementation can satisfy it on an MCP tool error. ADR scope is correct. §5.2 also volunteers the honest consequence - on stdio, `problem+json` is honoured nowhere. |
| **B4** | No stack traces or internal detail to a caller | `architecture/error-contract.md:206` - *"3. **No stack traces**: 500 errors return a fixed message. Stack traces are logged, not returned."*; `backend/error-handling.md:383` - *"Never leak raw exception messages from third-party libraries to API consumers:"* | **SATISFIED** | §5.3: `mask_error_details=True` set explicitly; masking is client-facing only, traceback stays in the server log. |
| **B5** | `type` URIs relative `/problems/<slug>` and a frozen contract | `architecture/error-contract.md:211` - *"8. **Relative type URIs**: Use `/problems/<slug>`, not absolute URLs."*; `:210` - *"7. **Type URIs are stable**: Once published, a `type` URI is a contract. Changing it is a breaking change."* | **PARTIAL** | §5.1 gets the shape right (*"`type` is a relative `/problems/<slug>`"*). **Gap:** the stability half is nowhere. No slug register exists, and nothing in §10 ties a changed slug to the major bump B84 would require. |
| **B6** | Typed exception hierarchy with `problem_type` + `title` class attributes | `backend/error-handling.md:205` - *"When raising `AppException` directly for domain-specific errors, always provide `problem_type` and `title`:"*; canonical subclass set at `:127-200` | **PARTIAL** | §3 lists `errors.py` as *"exception hierarchy + RFC 9457 problem construction"*. **Gap:** the design never states that the hierarchy carries `problem_type`/`title` class attributes, and never maps onto the canonical ten subclasses. `errors.py` existing is not the obligation; its shape is. |
| **B7** | Upstream failures map to typed domain exceptions | `backend/error-handling.md:412-419` - `>=500` → `ServiceUnavailableException`, `>=400` → `ExternalServiceException` | **PARTIAL** | §5.1 maps *"503 for an upstream 5xx"* ✓. **Gap:** no `ExternalServiceException` / 502 mapping for a Jobvite 4xx. §5.1 says *"`status` carries the upstream Jobvite status where one exists"*, which passes a Jobvite 401 straight through as 401 - the standard says a caller-facing 502. §4.2's error rule detects the condition; the design does not say what `status` it becomes. |
| **B8** | `fastapi.HTTPException` never raised directly | `backend/python.md:126` - *"**Do not raise `fastapi.HTTPException` directly.** FastAPI serializes it as `{"detail": "..."}`, which violates the [error contract]"* | **NOT-APPLICABLE** | No FastAPI. The server is FastMCP over stdio/Streamable HTTP; `fastapi.HTTPException` is not importable in the dependency set of §10. The clause's intent is carried by B1, which is satisfied. |

### Tool definition (B9-B23)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B9** | Explicit typed input schema from a Pydantic model; no free-form parameters | `ai/tool-calling.md:48` - *"**Every tool has an explicit, typed input schema** (JSON Schema, derived"* [from a Pydantic model] | **SATISFIED** | §2.1: *"Every tool takes a typed Pydantic model, never a free-form dict."* |
| **B10** | Constrained fields - enums, bounded numerics, max lengths, explicit optionality | `ai/tool-calling.md:52-54` - *"Schema fields are **constrained**: enums for closed sets, bounded numeric ranges, max string lengths, required vs optional made explicit. Loose types (bare `string`, `object`) are attack surface."* | **SATISFIED** | §2.1: *"`strict=True`, extra keys forbidden, explicit `max_length` on every string, regex on every identifier."* Bounded numerics are covered for the one numeric that exists (`count`, capped at 500/1000 in §4.5). |
| **B11** | Validated typed object reaches the body, never the raw dict | `ai/tool-calling.md:97-99` - *"**Never pass raw model arguments through to a tool.** Parse the model-supplied JSON against the tool's schema first; the tool body receives the **validated, typed object**, never the raw dict/string."* | **SATISFIED** | §2.1's typed-model-only rule is exactly this. FastMCP performs the parse before dispatch. |
| **B12** | Schema violation fails closed with a **typed tool error**, never reaches the body; unit-tested | `ai/tool-calling.md:100` - *"**Reject on violation** — return a typed tool error back to the model so"* [it can correct]; `:188-189` - *"The per-tool argument-rejection path is unit-tested: a schema violation must fail closed, not reach the tool body."* | **PARTIAL** | §8 names *"argument rejection"* among the 95%/90% critical paths ✓. **Two gaps.** (a) It is **not** in §8's "Required cases" list, the list that defines what is merge-gating. (b) More substantively: §5.1 says problem objects are the primary channel *"because they are **returned** rather than raised"* - but a schema violation is caught by the framework **before the tool body runs**, so nothing in the tool can return anything. The design never says what shape a rejected argument produces. On the evidence of §5.1's own reasoning it can only be a raised `ToolError`, which carries no problem object - the same defect §4.4 admits for rate limiting, unadmitted here. |
| **B13** | Tools validate their own inputs independently of the caller | `ai/agent-guardrails.md:57-58` - *"**Tools validate their own inputs** independently of the model; never execute raw model-supplied arguments"* | **SATISFIED** | §2.1, same mechanism as B11. Validation is server-side and unconditional. |
| **B14** | Tool outputs to the model are wire-shaped snake_case | `ai/tool-calling.md:59-60` - *"Tool **outputs** intended for the model are wire-shaped **snake_case**, consistent with [`../architecture/error-contract.md`]"* | **SATISFIED** | §2.1: *"Outputs are snake_case regardless of Jobvite's casing."* §9.1's `eId`/`EId` normalisation is the concrete case, pinned by a test. |
| **B15** | Result size bounded to a **documented** maximum | `ai/tool-calling.md:153-155` - *"**Bound result size** before returning it to the model (truncate to a documented max); an oversized result is both an injection surface and a context/cost blowout."* | **PARTIAL** | §7.7 bounds it in-tool with a useful truncation notice (*"showing 50 of 1,240"*) and makes the cap configuration ✓. **Gap: "documented max" is not met.** No default value appears anywhere in DESIGN.md, and since B78 (README config table) is itself UNADDRESSED, nothing currently commits to documenting it. |
| **B16** | Tool name + description reviewed like prompts - clear, minimal, no secrets | `ai/tool-calling.md:55-57` - *"Tool name + description are part of the prompt and are **reviewed like prompts** — clear, minimal, no secrets. The callable-tool set is an explicit allow-list per agent"* | **UNADDRESSED** | **DESIGN.md never mentions tool descriptions.** §2 gives a table of five tool names and their Jobvite operations; there is no statement that descriptions exist, that they are reviewed, or that they carry no credential/tenant detail. Given §4.1's three credential classes and the jobFeed `companyId`, a description is a plausible leak surface. This is the clean miss in the cluster the lead flagged. |
| **B17** | Log every invocation: tool name, redacted args, result status, latency, **approval decision if gated**, correlation id; snake_case; no secrets | `ai/tool-calling.md:171-173` - *"**Log every tool invocation** — tool name, validated arguments (PII redacted), result status, latency, and the request correlation id."*; `ai/agent-guardrails.md:121-123` - same list plus *"the approval decision if gated"*; `ai/tool-calling.md:178-179` - *"Tool logs are wire-shaped **snake_case** (`tool_name`, `request_id`, `result_status`) and never contain secrets or raw credentials."* | **PARTIAL** | §5.3 is a strong answer to round 1: `audit.py` emits the event itself rather than trusting middleware, with the reasoning (`include_payloads=False` emits *no* arguments, not *redacted* ones) spelled out. **Two gaps.** (a) `agent-guardrails.md:122` requires **the approval decision if gated** - `create_candidate` is gated three ways in §2.2 and §7.5, and §5.3 does not list the approval decision among the audited fields. That is the one field this project most needs, since it is the only record that a write was authorised. (b) The snake_case field-name requirement at `:178-179` is not stated. |
| **B18** | Destructive operations default-deny behind an approval gate; fail closed with no approver | `ai/agent-guardrails.md:70-73` - *"**Default-deny destructive operations.** Any irreversible or high-blast-radius action (delete, financial transaction, outbound message to a third party, infra change, mass update) MUST pause for human approval before execution. Fail closed: no approver, no action."*; `ai/tool-calling.md:140` - *"\| Destructive / irreversible (delete, payment, send, deploy) \| **Approval gate required** \|"* | **SATISFIED** | §2.2's three independent gates, each fail-closed. §7.5's honesty about what may be claimed (*"the server requires an approval response from the host and refuses to write without one"* - **never** *"a human approved this"*) is exactly the right reading of a clause the server cannot fully discharge. |
| **B19** | Write tools idempotent or guarded against double-apply on retry | `ai/tool-calling.md:133-134` - *"Tools are **idempotent or guarded** so a retry (see [`./resilience.md`]) cannot double-apply a side effect."* | **SATISFIED** | §4.3 excludes `create_candidate` from retry **by construction**, with the measured failure it prevents (*"one call, **four rows created**"*). §7.6's HMAC payload binding is the second guard. |
| **B20** | Minimal explicit allow-list, not a kitchen sink | `ai/agent-guardrails.md:47-49` - *"**Minimal tool set.** Bind to an agent only the tools its task requires. Do not expose a broad "kitchen-sink" toolbox; an unused tool is attack surface. The callable-tool list is an explicit allow-list per agent."* | **SATISFIED** | Five tools, §2, with the twelve unevidenced resources explicitly not shipped and `POST /api/v2/task` explicitly excluded with a reason. |
| **B21** | Credentials scoped narrowly; scope the credential, never the prompt | `ai/agent-guardrails.md:50-53` - *"**Minimal scope per tool.** Each tool runs with the narrowest credentials / permissions that work (read-only DB role for a read tool; a single S3 prefix; one API scope). Scope the *credential*, never rely on the prompt to keep the model in bounds."* | **PARTIAL** | §7.2 scopes the **inbound MCP token** on three data classes ✓, and §4.1 separates the jobFeed credential from the v2 credential ✓. **Gap:** nothing scopes the **outbound Jobvite credential**. The clause's own examples are all outbound (*"read-only DB role for a read tool"*). A deployment with `JOBVITE_ENABLE_WRITES=false` still supplies a Jobvite key that can write; the design never says it should be a read-only key. Whether Jobvite offers read-only keys is unknown (no credential exists - §11.1), so the honest form of this obligation is a documented instruction to the operator, and that is absent. |
| **B22** | Bounds are configuration, not constants in code | `ai/agent-guardrails.md:106-107` - *"Bounds are configuration, not constants buried in code, so they can be tuned per agent and environment."* | **SATISFIED** | §7.7: *"The cap is configuration, not a constant."* §4.4's rate limits and §4.5's `JOBVITE_PAGINATION_START_BASE` are likewise config. §4.4's honesty that limits are startup-only and a reload is a quota amnesty is a caveat on tunability, not a breach - they remain configuration. |
| **B23** | Adversarial cases are merge-gating tests | `ai/tool-calling.md:185-187` - *"Adversarial tool cases — invalid/over-budget arguments, a tool result carrying an injection payload, an unbounded-loop attempt — are **merge-gating** tests"*; `ai/prompt-injection.md:138-139` - *"Maintain red-team cases for injection and jailbreaks as **merge-gating** tests in the eval suite"* | **PARTIAL** | §6.1: *"Red-team cases live in the main suite and are merge-gating"* ✓ - and §8's fencing case *"including content that tries to close its own fence"* is exactly the injection-payload arm. **Gap:** the clause enumerates three adversarial classes. **Invalid/over-budget arguments** is the B12 gap above; the **unbounded-loop attempt** has no analogue in §8 either - the nearest hazard is §4.5's paged scan over a mutating set with no stable sort (§9.5), which is unbounded-walk-shaped and untested. |

### Untrusted content (B24-B26)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B24** | Jobvite response content treated as untrusted indirect input, fenced as inert data | `ai/prompt-injection.md:49-50` - *"Every byte that reaches a model is **untrusted data**, whether it came from an end user or from the system itself."*; `:74-75` - *"Wrap untrusted content in explicit delimiters and frame it as inert data"* | **SATISFIED** | §6.1 is the strongest section in the document against its clause. Fencing with delimiter-token stripping so *"content cannot close its own fence"*, path-keyed rather than name-keyed with the collision that forced it (`title`/`eId` at multiple depths), and the fence-closing attempt as a required test in §8. |
| **B25** | Input size and encoding limits enforced before dispatch; reject control characters and oversized payloads | `ai/prompt-injection.md:124-125` - *"Enforce input size/encoding limits before dispatch; reject control characters and oversized payloads"* | **PARTIAL** | Size limits ✓ via §2.1's `max_length` on every string. **Two gaps: control characters and encoding.** Neither word appears in DESIGN.md. This is precisely where the allow-listed-output-model mechanism does *not* reach - it is an output filter, and B25 is an input control that must fire *before dispatch*. A candidate name containing `\x00` or a bidi override reaches the Jobvite call unexamined, and §6.1's fencing is applied on the way back out, not on the way in. |
| **B26** | Secrets and PII redacted before anything reaches a trace/log backend | `ai/prompt-injection.md:127-128` - *"**Redact secrets and PII from untrusted input before it reaches the trace backend**"* | **SATISFIED** | §4.1 enforces secret redaction in one place (`utils/redaction.py`) with a test that fails if a secret can reach a log record, including the jobFeed URL. §5.3 emits redacted arguments; §7.7 sets `include_payloads=False`. |

### Input validation (B27-B31)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B27** | `ConfigDict(strict=True)` on all request models | `backend/input-validation.md:37` - *"All request models MUST enable strict mode to prevent silent type coercion:"*; rule 1 at `:387` | **SATISFIED** | §2.1: *"`strict=True`, extra keys forbidden"*. §2 leans on it structurally - the two-tool split for `search_candidates`/`get_candidate` exists *because* *"Under `strict=True` one tool cannot have two return schemas."* |
| **B28** | Explicit `max_length` on every string field | `backend/input-validation.md:64` - *"All string fields MUST declare an explicit `max_length`. Use these defaults unless domain requirements justify a different limit:"* | **SATISFIED** | §2.1: *"explicit `max_length` on every string"*. The defaults table at `:66-76` is a default, not a floor, so not specifying values is within the clause. |
| **B29** | Regex `pattern` constraints on identifier fields | `backend/input-validation.md:389` - *"3. **Regex for identifiers** — slugs, handles, UUIDs must use `pattern` constraints"* | **SATISFIED** | §2.1: *"regex on every identifier"*. `candidateId` and `companyId` are the identifiers in scope. |
| **B30** | Nesting depth ≤ 5, list items ≤ 1 000, dict keys ≤ 100, body ≤ 1 MiB | `backend/input-validation.md:223-226` - *"\| Max nesting depth \| 5 levels \| … \| Max list items \| 1,000 \| \| Max dict keys \| 100 \| \| Max total request body size \| 1 MiB \|"*; rules at `:391-392` | **UNADDRESSED** | **None of the four limits appears in DESIGN.md.** §4.5's page caps of 500/1000 are *outbound transport* limits on what we ask Jobvite for - a different axis entirely, and §4.5 says so (*"These are the **transport** limits"*). Nothing bounds an inbound argument payload, a nested `customField[]` structure, or a list argument. §6.1 notes `customField[]` is *"open-ended"*, which is the exact shape B30 exists to bound, and bounds it only on the way out. |
| **B31** | Fail closed - reject anything not fully validatable | `backend/input-validation.md:396` - *"10. **Fail closed** — reject requests that cannot be fully validated"* | **SATISFIED** | §2.1's allow-list *"fails closed: a new Jobvite field is dropped until someone adds it deliberately"*; §6.1 drops unknown non-string fields rather than stringifying; §7.3 fails at boot on missing config. Fail-closed is the document's consistent default. |

### Resilience (B32-B39)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B32** | Explicit connect and read (or total) timeout on every outbound call; no SDK default | `backend/resilience.md:71-73` - *"**Every** outbound call MUST set an **explicit connect and read (or total) timeout**. No call may rely on the client/SDK default — many default to *no* timeout or a multi-minute one."* | **SATISFIED** | §4.3: *"**Timeouts explicit and per-phase.** No SDK default, no single scalar."* |
| **B33** | Timeouts shorter than the inbound request's own deadline | `backend/resilience.md:74-76` - *"Timeouts MUST be **shorter than the inbound request's own deadline** so a slow dependency surfaces as a fast, typed error rather than a hung request worker."* | **PARTIAL** | §4.3 bounds the *retry budget* inside the inbound timeout ✓. **Gap:** MCP has no inbound deadline - there is no HTTP request worker to hang, and §7.5 admits an abandoned approval *"hangs the call"* with no bound at all. The design does not say the clause has no referent here, and §7.5 shows the failure mode the clause exists to prevent occurring for a different reason. Worth one sentence stating the adaptation. |
| **B34** | `tenacity`, exponential backoff **with jitter**, bounded stop, total budget ≤ inbound timeout | `backend/resilience.md:92-98` - *"Wrap retryable calls with `tenacity` using **exponential backoff WITH jitter**. … The total retry budget MUST be ≤ the inbound request timeout"* | **SATISFIED** | §4.3: *"via `tenacity` with jitter, budget inside the inbound timeout"*. |
| **B35** | Retry only on connection errors, timeouts, 429, 5xx - never a blanket exception | `backend/resilience.md:99-101` - *"Retry **only transient/retryable** errors: connection errors, read timeouts, HTTP **429**, and **5xx**. **Never** retry on a blanket `except Exception`"* | **SATISFIED** | §4.3: *"only for connection errors, timeouts and 5xx"*. 429 is omitted, which is a **tightening**, not a breach - the clause is an allow-list ceiling. §4.4's finding that Jobvite emits no rate-limit headers of any kind makes a 429 retry unbackoffable anyway. Worth a sentence in the design saying the omission is deliberate, since a reader will otherwise read it as an oversight. |
| **B36** | Non-idempotent writes not blindly retried | `backend/resilience.md:143-145` - *"A **non-idempotent `POST`** (create, charge, send) MUST NOT be blindly retried — a retry after a partial failure can double-charge or double-create."* | **SATISFIED** | §4.3, by construction, with the measured four-row duplication that forced it. §8 makes *"`create_candidate` not retrying on timeout"* a required test. |
| **B37** | One breaker per dependency; 4xx does not trip it | `backend/resilience.md:159-161` - *"Use **one breaker per dependency** (a distinct `@circuit(name=...)`, or a `CircuitBreaker` subclass per dependency) — never a single global breaker."*; `:166-168` - *"Count **only outage-class errors** toward the breaker via `expected_exception` — a caller error (4xx) is not an outage and MUST NOT trip it."* **[range restored by CONF-5: this row's title asserts the 4xx half, and until now its citation did not contain it]** | **SATISFIED** | §4.3: *"One circuit breaker for Jobvite. 4xx must not trip it"* with the reasoning. §8 makes *"a 4xx not tripping the circuit breaker"* a required test. |
| **B38** | Composition order timeout → retry → breaker, with the retry loop **inside** the breaker | `backend/resilience.md:209` - *"**timeout (innermost) → retry → circuit breaker (outermost)**"*; `:214-217` - *"The **breaker** wraps the retried call, so **retries count toward the breaker** ... Never let a retry loop sit outside the breaker — that lets retry storms defeat the breaker and keep hammering a down upstream."* **[range restored by CONF-5]** | **SATISFIED** | §4.3 opening line: *"Ordered timeout, then retry, then circuit breaker."* |
| **B39** | Retries and breaker transitions logged with the correlation field, never silent | `backend/resilience.md:226` - *"`request_id` correlation field. Never retry or trip silently."* | **UNADDRESSED** | **DESIGN.md never says a retry or a breaker transition is logged.** §5.3's audit event is per *tool invocation* - one event per call, emitted around the tool, not around each attempt. A tool that retried three times and then tripped the breaker produces exactly the same audit record as one that succeeded first try. On a server whose entire upstream is unobserved (no credential, no sandbox, §1.1), silent retries are the difference between "Jobvite is slow" and "Jobvite is down", and neither is currently visible. |

### Correlation and logging (B40-B45)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B40** | The correlation triple verbatim: header `X-Request-ID`, log field `request_id`, ContextVar `request_id_var` | `ai/tool-calling.md:173-177` - *"Use the canonical triple verbatim: HTTP header `X-Request-ID`, log field `request_id`, ContextVar `request_id_var` ... Also attach the LLM trace/span id so a tool call ties back to its turn (trace IDs are separate from `request_id`)."*; identically at `ai/agent-guardrails.md:124-127`; `architecture/observability.md:626` | **PARTIAL** | Two of three ✓ - §5.3 uses the header `X-Request-ID` on the HTTP transport and the field `request_id` in the problem object and audit event. **Gap: `request_id_var` is never named.** The clause says *verbatim*, and STANDARDS.md §2/A3 explicitly predicted this would be the mechanism (*"`request.state.request_id` becomes the `request_id_var` ContextVar"*). Without a ContextVar the id has to be threaded as a parameter into `utils/redaction.py`, the client, and the breaker logging B39 asks for - which is plausibly why B39 is missing. These two gaps are the same gap. |
| **B41** | Caller-supplied `X-Request-ID` validated as UUID v4, replaced if invalid | `backend/request-middleware.md:38` - *"2. **Validate** the value as a UUID v4 format (reject non-UUID values)"*; `:143` - *"2. **Always validate**: Never blindly trust caller-supplied `X-Request-ID` values."* **[range restored by CONF-5]** | **SATISFIED** | §5.3: *"validated as a UUIDv4 before use - unvalidated inbound ids are a log-forging vector"*, which is the rationale the standard gives at `:60`. |
| **B42** | Every request gets a request_id; echoed on **every** response, success and error | `backend/request-middleware.md:142` - *"1. **Every request gets a request_id**: No request may complete without a correlation ID on `request.state`."*; `:144` - *"3. **Always echo**"* | **PARTIAL** | Minting ✓ - §5.3 mints a UUIDv4 per tool invocation. Echo on **errors** ✓ - the problem object carries `request_id` and its `instance` URN. **Gap: success responses.** Nothing in the design puts `request_id` on a successful tool result. §7.7's truncation notice (*"showing 50 of 1,240"*) is the only stated success-path metadata. A caller cannot correlate a successful call with its audit record. |
| **B43** | Exactly one structured log entry per request with method, path, status, duration, request_id | `backend/request-middleware.md:145` - *"4. **One log per request**: The middleware emits exactly one structured log entry per request."* | **PARTIAL** | The fields adapt cleanly and §5.3 covers them (status, latency, correlation id; method/path have no MCP referent). **Gap: "exactly one" is breached by the design's own middleware stack.** §7.7 adopts `Timing` **and** `StructuredLogging`, and §5.3 adds `audit.py` on top *because* `StructuredLogging` emits no arguments. That is three log lines per invocation from three producers. The design justifies the third convincingly; it never reconciles the result with a clause that says one. Either the two middlewares are redundant with `audit.py` and should go, or the clause is deviated from and should say so. |
| **B44** | `loguru` is the logging library | `architecture/reference-architecture.md:94` - *"\| Logging \| **loguru** \| — \| std + prod agree; canonical \|"* | **SATISFIED** | §3: *"Framework middleware and `loguru` cover the first and third"*, and no custom logging module. |
| **B45** | No `print()`; no logging of PII, tokens, or secrets | `architecture/observability.md:636` - *"- Log sensitive data (passwords, tokens, PII)"* (under **Don't**); `:642` - *"- Use print statements instead of loggers"*; `documentation/agentic-coding-standard.md:`**`172`** (STANDARDS.md says `:173` - see **CD-1**) - *"- [ ] No `console.log` / `print` debugging statements"* | **SATISFIED** | The load-bearing half - no PII, no secrets - is §4.1, §5.3 and §6 and is the most thoroughly designed control in the document. The `print()` half is a lint rule; §3's note that `__main__.py` does *"logging before imports"* implies loguru from the first line. |

### Language, stack and style (B46-B54)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B46** | Python floor `>=3.12` | `architecture/reference-architecture.md:83` - *"\| Language \| Python \| `>=3.12` \| deep tier \|"*; `backend/tech-stack.md:30` - *"- **Python 3.12+** - Programming language"*; `:129` - `requires-python = ">=3.12"` | **SATISFIED** | §10: *"Python `>=3.12`"*. Resolves STANDARDS.md conflict C1 the right way, without an ADR, because the standard wins. |
| **B47** | Blessed libraries: Pydantic `>=2.10`, `httpx`, `tenacity ^9` + `circuitbreaker ^2`, `uv`, `ruff`/`mypy`/`pytest` | `architecture/reference-architecture.md:85` - *"\| Models/validation \| Pydantic \| `>=2.10` \| v2 API \|"*; `:91`, `:92`, `:95`, `:98` | **PARTIAL** | `uv` ✓ (§10 `[tool.uv]`), `tenacity` ✓ (§4.3), `ruff`/`mypy`/`pytest` ✓ (§10 CI), `httpx` → **`httpx2` with ADR-0007** ✓ and well argued. **Two gaps.** (a) The **`circuitbreaker` library is never named** - §4.3 says "one circuit breaker" without saying what implements it, and the standard pins `circuitbreaker ^2` specifically. (b) The **Pydantic `>=2.10` floor is never stated**. §10 discusses pydantic only as a *resolution* concern (`prerelease = "explicit"` keeping it stable) - resolving to stable is not the same as pinning a floor, and a stale transitive resolution to 2.9 would satisfy §10's text while breaching B47. |
| **B48** | `ruff format` is the formatter; not Black | `architecture/reference-architecture.md:92` - *"\| Lint / type / test \| ruff / mypy / pytest \| — \| ruff format (not Black) \|"*; `backend/python.md:368` - *"- **ruff format**: Code formatter (opinionated; replaces Black)"* | **SATISFIED** | §10 CI: *"lint, format, types, tests"* with ruff named as the toolchain. Black appears nowhere. |
| **B49** | Line length 88; docstrings/comments at 72 | `backend/python.md:35-36` - *"- Maximum line length: **88 characters** (`ruff format` default) - For comments and docstrings: **72 characters**"* | **UNADDRESSED** | Not in DESIGN.md. Low consequence - it is a `pyproject.toml` line - but §10 claims the packaging section and gives `[tool.uv]` verbatim, so the omission is inside that section's own scope. |
| **B50** | Type hints on all public functions; Google- or NumPy-style docstrings | `backend/python.md:76` - *"Always use type hints for function parameters and return values:"*; `:97` - *"Use Google-style or NumPy-style docstrings"*; `documentation/agentic-coding-standard.md:169` - *"- [ ] Python has type hints on all public functions"* | **UNADDRESSED** | Not in DESIGN.md. Partly self-enforcing - mypy is a CI gate (B63) and would catch missing annotations under `strict` - but the docstring style is not enforced by anything the design names, and §8 relies on a docstring carrying a load-bearing warning (*"That sentence is in the test module's own docstring"*). |
| **B51** | `datetime.now(UTC)`; `datetime.utcnow()` forbidden | `backend/python.md:227` - *"Never use `datetime.utcnow()` — deprecated since Python 3.12 (returns naive datetime missing tzinfo)."* | **UNADDRESSED** | Not in DESIGN.md, and this one has live surface. §5.1 requires a `timestamp` on every problem object; §7.6 requires token expiry; §9.2 handles Jobvite's epoch-millisecond responses against `yyyy-MM-dd` requests. Three places where a naive datetime produces a wrong answer rather than a type error, and the design names none of them as UTC-aware. §9.2 flags the asymmetry as a hazard but says only *"Date asymmetry"*, not which representation wins. |
| **B52** | Naming per the table - snake_case functions/modules, PascalCase classes and Pydantic models, UPPER_SNAKE_CASE constants | `backend/python.md:64-71` - *"\| Variables/Functions \| snake_case \| … \| Classes \| PascalCase \| … \| Constants \| UPPER_SNAKE_CASE \| … \| Modules/Files \| snake_case.py \| … \| Pydantic Models \| PascalCase \|"* | **UNADDRESSED** | Not stated. De facto satisfied by §3's module layout, which is snake_case throughout, and by ruff's default rule set. Recorded rather than waived because nothing in the design commits to it. |
| **B53** | Secrets as `SecretStr` in a pydantic-settings `Settings` class, read from env, accessed via `.get_secret_value()`; committed `.env.example` with names only | `architecture/security.md:433-463` (the `Settings(BaseSettings)` block with `SecretStr` fields); `:469` - *"# Always use .get_secret_value() to access secrets"*; `:418` - *"# .env.example (commit this)"* | **PARTIAL** | The code half is fully satisfied - §4.1: *"Credentials are `SecretStr` throughout, resolved with `.get_secret_value()` only when building a request"*, and §7.3 puts required-config validation in pydantic-settings ✓. **Gap: `.env.example` is nowhere in DESIGN.md.** Same gap as B90/B91, which is where its consequence is ranked. |
| **B54** | Approved crypto libraries only: `cryptography`, `bcrypt`, `argon2-cffi` | `documentation/agentic-coding-standard.md:146` - *"- Approved cryptographic libraries only"*, which is where the word **only** comes from; the approved list is the table row at `:153` - *"\| Python \| `cryptography`, `bcrypt`, `argon2-cffi` \|"* | **NOT-APPLICABLE** | **Because there is no password storage and no encryption at rest.** The clause's neighbours (`:155`, never MD5/SHA1 for passwords) fix its scope as credential hashing. The only cryptographic operation in the design is §7.6's HMAC binding of a confirmation token, for which stdlib `hmac`/`hashlib` is correct and is what `architecture/authentication.md:539` itself uses (`hashlib.sha256(key.encode()).hexdigest()`). **Recorded as a residue:** §7.6 does not name what implements the HMAC, and a token comparison written with `==` rather than `hmac.compare_digest` would reintroduce the timing side channel STANDARDS.md §2/A4 warns about for the API-key path. |

### Testing (B55-B62)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B55** | pytest with `asyncio_mode = "auto"`, `--strict-markers`, declared markers, `branch = true` coverage | `backend/testing.md:59` - `asyncio_mode = "auto"`; `:67` - `"--strict-markers"`; `:71-75` markers block; `:82` - `branch = true` | **PARTIAL** | `branch = true` is implied and required by §8's *"95% line and 90% branch on critical paths"* ✓. **Gaps:** `asyncio_mode = "auto"`, `--strict-markers`, and a declared markers list are all absent - and the markers gap is not cosmetic here. §8's whole credential-free strategy rests on *"credential-dependent tests are excluded by **selection**, not marked `skipif`"*. Selection means a marker. With `--strict-markers` undeclared, a typo in that marker name silently selects nothing, and the live suite would be excluded by accident rather than by design - a green run that tested less than it claimed. |
| **B56** | Coverage floor 80% overall, `fail_under = 80`; sub-targets Services 90%, API Routes 85%, Utilities 95% | `backend/testing.md:96` - `fail_under = 80`; `architecture/testing-strategy.md:322` - `--cov-fail-under=80`; `devops/quality-gates.md:44` - *"- [ ] Coverage meets minimum threshold (80%)"*; `backend/testing.md:586-588` - *"\| Services \| 90% \| … \| API Routes \| 85% \| … \| Utilities \| 95% \|"* | **PARTIAL** | The 80% floor is exact ✓ - §8: *"80% floor overall"*. **Gap: the sub-targets are remapped without saying so.** §8 sets 85% tool modules and 90% Jobvite client. Mapping tools→"API Routes" (85%) and client→"Services" (90%) is defensible. **`Utilities 95%` has no counterpart at all**, and §3 puts real logic in utilities - `utils/redaction.py` holds the secret-redaction enforcement point and the untrusted-content fencing, the two controls §8 itself calls required cases. Under §8 as written, the module carrying both controls is covered at the 80% floor while the client is held to 90%. That inverts the risk. A remap that *loosens* a required number needs an ADR; none is listed in §12. |
| **B57** | Critical paths at 95% line / 90% branch; data mutations and security-sensitive operations are critical paths | `architecture/testing-strategy.md:306` - *"\| Critical Paths \| 95% \| 90% \|"*; `:310-314` - *"Critical paths require higher coverage: - Authentication flows … - Data mutations (create, update, delete) - Security-sensitive operations"* | **SATISFIED** | §8 states 95/90 verbatim and enumerates them correctly: *"auth, argument rejection, the error rule, approval, the write"*. The write is the data mutation; auth and approval are the security-sensitive operations. |
| **B58** | A collection-guard meta-test inside a configured `testpaths` root, passing in CI | `backend/testing.md:138-141` - *"2. **A collection-guard meta-test is required.** Add a meta-test that walks the repository for `test_*.py` files and asserts every discovered file is reachable from the configured `testpaths`. The guard must itself live inside a configured root so that its own absence fails collection:"*; `devops/quality-gates.md:79-81` - *"MUST be present in a configured root and MUST pass in CI. If the guard is absent or if any test file lives outside the configured roots, the CI backend test job MUST fail."* | **UNADDRESSED** | **The mandated guard is absent.** §8's *"CI runs `--collect-only` against [the live suite] and fails on a collection error"* is a genuinely good control and is **not this one** - it proves the excluded suite still *imports*, and says nothing about whether some third `test_*.py` is reachable from `testpaths` at all. The standard's failure mode is a test file nobody runs; §8's failure mode is a test file that rots. Both are real; only the second is designed for. Note the compounding: §8 deliberately maintains **two** suites with different selection, which is exactly the configuration in which an orphaned third file is least visible. `quality-gates.md:79-81` makes the CI job's failure mandatory, so this is a required-check breach, not a nice-to-have. |
| **B59** | CI runs pytest with no positional path argument so `testpaths` is authoritative | `backend/testing.md:166-169` - *"3. **CI must run all roots.** The CI `pytest` invocation MUST NOT restrict to a single directory via a positional argument that would shadow `testpaths`. Run without a positional path argument so `pyproject.toml` `testpaths` is authoritative"* | **PARTIAL** | §8's exclusion is by *selection* (a marker), not by a positional path, which is the compliant mechanism ✓. **Gap:** the design never states the CI invocation, and `--collect-only` *against the live suite* (§8) necessarily takes a target. That target is legitimate for a `--collect-only` pass but a reader implementing §8 has no statement that the main `pytest --cov` run must be bare. Given B58 is missing, the guard that would catch a shadowing positional path is missing too. |
| **B60** | A SKIPPED required check fails the gate; skip count must be 0 | `devops/quality-gates.md:85-87` - *"A SKIPPED result on a **required** check is not a passing result — it is an unknown result and MUST fail the gate."*; `devops/ci-cd.md:673-675` - *"A SKIPPED job or test is an **unknown result**, not a passing one … a SKIPPED outcome MUST block merge exactly as a FAILED outcome would."* | **SATISFIED** | §8, first line: *"CI has **zero skips** - a skip counts as a failure, so credential-dependent tests are excluded by *selection*, not marked `skipif`."* This is the clause stated exactly and with the right mechanism. The job-level half of the rule is B106's. |
| **B61** | Test names follow `test_{what}_{when}_{expected}` | `documentation/agentic-coding-standard.md:346-348` - *"# Python: test_{what}_{when}_{expected}"* with `test_create_user_with_valid_data_returns_user()` | **UNADDRESSED** | Not stated. §8's required-case list is written as prose descriptions (*"the 200-with-401-body trap"*, *"token replay, expiry, and payload mismatch each refused"*) with no naming convention attached. Consequence is low but non-zero: a test *name* is an unverified claim about its *body*, and the convention exists to make the claim checkable at a glance. |
| **B62** | Mock external APIs; do not mock own code or business logic | `architecture/testing-strategy.md:420` - *"\| External APIs \| Your own code \|"*; `:424` - *"\| Network requests \| Pure functions \|"* | **SATISFIED** | §8 substitutes at the transport boundary with `httpx2`'s built-in `MockTransport` - the external API and the network request, exactly the two rows on the Mock side. Nothing in §8 mocks our own client, parser, or fencing logic. |

### CI/CD (B63-B76)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B63** | CI runs `ruff check`, `ruff format --check`, `mypy`, `pytest --cov` as separate gates, 0 errors | `devops/ci-cd.md:182` - `run: uv run ruff check .`; `:185` - `run: uv run ruff format --check .`; `:188` - `run: uv run mypy app`; `devops/quality-gates.md:63-65` - *"\| Backend Lint \| Ruff \| 0 errors \| \| Backend Types \| mypy \| 0 errors \| \| Backend Tests \| pytest \| 80%+ coverage, all test roots run \|"* | **SATISFIED** | §10: *"CI: lint, format, types, tests"*. All four gates named. |
| **B64** | Dependencies install frozen: `uv sync --frozen` | `devops/ci-cd.md:179` - `run: uv sync --frozen`; `devops/supply-chain-security.md:75-77` - *"Reproducible installs MUST use a **frozen** install everywhere CI and container images resolve dependencies: - Python: `uv sync --frozen` (fails if `uv.lock` is out of date)."* | **UNADDRESSED** | **`--frozen` appears nowhere in DESIGN.md.** §10 is the section that would carry it - it gives `[tool.uv] prerelease = "explicit"` verbatim *"because both lines are load-bearing"* - and stops at resolution policy without reaching install policy. This is the sharpest of the supply-chain gaps because §10's own thesis is that a transitive bump broke the code with zero change to it (*"the `ResponseLimiting` regression arrived through the transitive SDK"*). An unfrozen CI install is precisely the mechanism by which that recurs, and §10 diagnoses the disease without prescribing the standard's cure. |
| **B65** | `uv.lock` committed and pinning transitives | `devops/supply-chain-security.md:69` - *"- **Python**: `uv.lock` MUST be committed"*; `:73-74` - *"**Transitive** dependencies MUST be pinned by the lockfile, not just direct dependencies. The full graph is reproducible from the lock."* | **UNADDRESSED** | `uv.lock` is never mentioned. Same root as B64: §10 pins `fastmcp` and `mcp` *by hand in `pyproject.toml`* - a direct-dependency pin - which is the manual substitute for the lockfile the standard mandates, and covers two packages out of the full graph. |
| **B66** | An unpinned/floating install never runs in CI or an image build | `devops/supply-chain-security.md:81-82` - *"unpinned) **MUST NEVER** run in CI or in an image build. It defeats reproducibility and lets the graph drift between build and audit."* | **PARTIAL** | The *intent* is served better than most repos manage - §10's explicit `mcp` pin exists precisely to stop graph drift, with the incident that motivated it. **Gap:** the obligation is about the install *command*, and with B64 and B65 both unaddressed nothing in the design forbids a floating `uv sync` in CI. Partial rather than unaddressed because §10 demonstrably understands the failure mode. |
| **B67** | `pip-audit` on every PR; fails the build on High/Critical | `devops/supply-chain-security.md:94-97` - *"`pip-audit` (Python) and `npm audit` (Node) **MUST** run in CI on every pull request and on the release build. The scan **MUST FAIL the build** on any known **High** or **Critical** advisory"*; `devops/ci-cd.md:484` - `uv run pip-audit` | **SATISFIED** | §10: *"plus `pip-audit`"*. The gate exists. Its interaction with B72 is where the risk sits. |
| **B68** | CodeQL analysis runs for Python | `devops/ci-cd.md:496` - `language: ['javascript-typescript', 'python']`; `devops/quality-gates.md:70` - *"\| Security Scan \| CodeQL/Trivy \| No high/critical \|"* | **SATISFIED** | §10: *"CodeQL"*. Python-only is the correct adaptation of the matrix. |
| **B69** | TruffleHog secret scanning on PRs with `fetch-depth: 0` | `devops/ci-cd.md:549` - `fetch-depth: 0`; `:552` - `uses: trufflesecurity/trufflehog@v3.88.0` | **SATISFIED** | §10: *"TruffleHog with full history depth"* - `fetch-depth: 0` stated in words. §10 then **exceeds** it with a pre-commit secret-scanning gate, correctly reasoning that on a public remote a pushed secret is compromised on landing. |
| **B70** | Every CI run emits CycloneDX **and** SPDX SBOMs as artifacts; tagged releases attach them | `devops/quality-gates.md:262-263` - *"Every CI run MUST produce a Software Bill of Materials (SBOM) for each shippable artifact"*; `:271` - *"\| Formats \| CycloneDX JSON **and** SPDX JSON (emit both) \|"*; `:273` - *"\| Releases \| Attached as release assets on tagged releases \|"*; `:269-270` - tool `anchore/sbom-action` pinned `@v0` | **SATISFIED** | §10: *"SBOM in both formats"*. **Two residues, neither a breach:** the tool pin (`anchore/sbom-action@v0`) is not named, and the release-attachment half (`:273`) is not stated - §10 covers CI runs but the design has no release process at all, which is B83-B87's gap. |
| **B71** | `pip-licenses` gate against the allow-list; a non-allow-listed dependency blocks the build | `devops/quality-gates.md:282` - *"All third-party dependencies MUST resolve to a license on the allow-list."*; `:290-294` - MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC; `devops/supply-chain-security.md:221` - *"- **Disallowed licenses MUST block** the build."*; `devops/ci-cd.md:648-651` - the `--allow-only` invocation | **SATISFIED** | §10: *"a `pip-licenses` allow-list gate"*. Gate present and correctly characterised as a gate, not a warning. |
| **B72** | A known advisory that cannot be remediated is tracked, not silently suppressed | `devops/supply-chain-security.md:130-131` - *"A known advisory that cannot yet be remediated **MUST** be tracked with an explicit, time-bounded, reviewed suppression"* | **UNADDRESSED** | No suppression or tracking policy anywhere. **This is materially worse here than in a normal repo**, and the design creates the exposure itself: §10 deliberately ships `fastmcp==4.0.0b4`, a **beta**, as *"deliberate early adopters"*, and STANDARDS.md records at `supply-chain-security.md:99-101` that **`pip-audit` has no severity threshold and fails on any advisory**. So a single advisory against any transitive of a beta dependency turns the required build gate red, with no stated process for a time-bounded reviewed suppression. The predictable outcome is someone adds `--ignore-vuln` under deadline pressure, which is the silent suppression the clause exists to prevent. |
| **B73** | PR titles carry a traceability ID | `devops/quality-gates.md:222-228` - *"[ID] Description … FEAT-XXX: Product feature - FR-XXX: Functional requirement - BUG-XXX: Bug fix - TECH-XXX: Technical improvement"*; `documentation/agentic-coding-standard.md:333-338` | **UNADDRESSED** | Not stated. Note the live collision STANDARDS.md flags as C4: this work is tracked under **EC-###** Jira ids, which is not one of the four documented prefixes. The design is the place that would resolve it and does not. |
| **B74** | No `TODO` without a ticket reference | `documentation/agentic-coding-standard.md:171` - *"- [ ] No `TODO` comments without ticket reference (e.g., `# TODO(FEAT-001): ...`)"*, with the CI check at `:405-411` | **UNADDRESSED** | Not stated, and there is a CI step in the standard (`:405-411`) that §10's CI list does not include. Sharpened by §11: the design has **six open questions** and every one is a thing someone will mark in code. |
| **B75** | No commented-out code blocks | `documentation/agentic-coding-standard.md:`**`173`** (STANDARDS.md says `:174` - see **CD-2**) - *"- [ ] No commented-out code blocks"* | **UNADDRESSED** | Not stated. Lint-level; lowest consequence in the sweep. |
| **B76** | `.github/workflows/` is a protected path agents do not auto-modify | `documentation/agentic-coding-standard.md:66` - *"### Always Protected (Never Auto-Modify)"*, with `.github/workflows/` at `:94` | **UNADDRESSED** | Not stated. Relevant rather than academic: §10 mandates two commit-time gates and a CI suite that agents will be asked to author, and the protected-path rule is what stops an agent editing the gate that is failing it. |

### Documentation (B77-B87)

**Cluster note.** All eleven are unaddressed. DESIGN.md refers to *"the README"* three times as the
place a hazard gets disclosed - §7.2 (`require_scopes` removing a tool from `tools/list`, *"the
README documents it or every support conversation starts in the wrong place"*), §7.1's proxy
header requirement, §7.5's abandoned-approval hang (*"integrators are told about it"*) - and never
once specifies that a README exists, what it must contain, or that any of those three disclosures
has a section to live in. The design has assigned the README four jobs and given it no
specification.

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B77** | `README.md` contains all 14 required sections, in order, with exact heading text | `documentation/readme-standard.md:43` - *"Every README MUST contain the following sections, in this order. Section headings must match exactly so that automated checks can locate them."*; list at `:45-58` | **UNADDRESSED** | No README structure anywhere in DESIGN.md. §10 is titled *"Repository and delivery"* and covers licensing, packaging, dependencies and CI without reaching documentation at all. |
| **B78** | The README Configuration table lists **every** environment variable with `Name`, `Required`, `Default`, `Description`, and no real values | `documentation/readme-standard.md:50` - *"6. **Configuration** — a table of environment variables with columns: `Name`, `Required`, `Default`, `Description`. Secrets are referenced by name only; never include real values."*; `:66` - *"every environment variable read by the component MUST appear in the Configuration table. New variables added in a PR require the table to be updated in the same PR."* | **UNADDRESSED** | The design names at least seven variables in passing - `JOBVITE_ENABLE_WRITES`, `JOBVITE_MCP_TRANSPORT`, `JOBVITE_PAGINATION_START_BASE`, `JOBVITE_API_KEY`, `MCP_PROTOCOL_NEGOTIATION`, plus the §7.7 result cap and §4.4's rate-limit settings - and never collects them. **This is the obligation that closes B15**: B15's *"documented max"* has no document to live in until B78 exists. §7.3's fail-fast-naming-the-variable behaviour also depends on an operator knowing which variables their enabled tool set requires, which §7.3 explicitly makes conditional. |
| **B79** | README ≤ 500 lines; overflow moves to `docs/` | `documentation/readme-standard.md:64` - *"- **Length cap**: 500 lines. Content beyond the cap MUST be extracted to `docs/` and linked."* | **UNADDRESSED** | Not stated. On current trajectory a live concern rather than a formality - the README is being asked to carry §7.1's proxy caveat, §7.2's `tools/list` behaviour, §7.5's hang, §7.6's token semantics and B78's table. |
| **B80** | Quickstart commands exercised by CI on every merge to the default branch | `documentation/readme-standard.md:67` - *"- **Quickstart parity**: the Quickstart commands MUST be exercised by CI on every merge to the default branch."* | **UNADDRESSED** | Not stated, **and there is a real tension the design should resolve rather than inherit.** §8 fixes that CI runs with *"no network and no credentials"*; §1.1 fixes that nobody holds a Jobvite credential. A Quickstart that reaches a working state necessarily needs one. Either the Quickstart stops at "server starts and lists tools" - which is CI-exercisable and worth stating - or B80 cannot be met and needs an ADR. Neither is chosen. |
| **B81** | Badges point at live sources; static stale SVGs forbidden | `documentation/readme-standard.md:70` - *"- **Badges are live**: each badge MUST point at a live source. Static SVGs that no longer reflect reality are forbidden."* | **UNADDRESSED** | Not stated. `readme-standard.md:47` also requires *at least one CI status badge*, which the design's CI suite could supply. |
| **B82** | A link checker runs in CI; a broken link blocks merge | `documentation/readme-standard.md:69` - *"- **Links are checked**: a link checker MUST run in CI; a broken link blocks merge."* | **UNADDRESSED** | §10's CI enumeration - lint, format, types, tests, pip-audit, CodeQL, TruffleHog, SBOM, pip-licenses, `fastmcp inspect` diff - has **no link checker**. Non-trivial here: the design links two live upstream issues ([#4926](https://github.com/PrefectHQ/fastmcp/issues/4926), [#4927](https://github.com/PrefectHQ/fastmcp/issues/4927)) that §7.4 and §7.7 treat as load-bearing evidence for excluding middleware and for the SIGTERM mitigation. |
| **B83** | `CHANGELOG.md` per Keep a Changelog 1.1.0 with a top `## [Unreleased]` | `documentation/changelog-standard.md:42` - *"The changelog MUST follow [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Top-level structure:"*; `:84` - *"An `## [Unreleased]` section MUST sit at the top of the file and accumulate pending changes between releases."* | **UNADDRESSED** | No changelog anywhere in DESIGN.md. |
| **B84** | Breaking changes prefixed `BREAKING:` with a migration note, triggering a major bump | `documentation/changelog-standard.md:91` - *"- **Breaking changes**: every breaking change MUST be prefixed `BREAKING:` in the bullet and MUST include a "Migration" sub-bullet or link to a migration note. A breaking change MUST trigger a major-version bump."* | **UNADDRESSED** | Not stated - **and B5 needs it.** `error-contract.md:210` makes a published `type` URI a contract whose change *is* a breaking change. With no changelog and no breaking-change discipline, B5's stability half has no enforcement mechanism. The two gaps are one gap. |
| **B85** | Security fixes under `### Security` with a CVE where one exists | `documentation/changelog-standard.md:92` - *"- **Security entries**: vulnerabilities fixed MUST appear under `### Security` with a CVE identifier when one exists; embargoed details MAY be omitted but the entry itself MUST appear."* | **UNADDRESSED** | Not stated. Compounds B72 - a `pip-audit` advisory that gets remediated has nowhere to be recorded, on a public repo whose consumers have no other channel. |
| **B86** | Internal-only changes do NOT appear in `CHANGELOG.md` | `documentation/changelog-standard.md:94` - *"- **Internal-only changes**: refactors, test-only changes, and CI changes that produce no user-visible effect MUST NOT appear in `CHANGELOG.md`. They live in commit history only."* | **UNADDRESSED** | Not stated. |
| **B87** | Release dates equal publication date; backdating forbidden | `documentation/changelog-standard.md:93` - *"- **Date integrity**: a release date MUST equal the date the artifact was published. Backdating is forbidden."* | **UNADDRESSED** | Not stated. |

### PII (B88)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B88** | Candidate PII never written to logs or traces in the clear | `ai/tool-calling.md:171-172` - *"**Log every tool invocation** — tool name, validated arguments (PII redacted)"*; `ai/prompt-injection.md:127-128` - *"**Redact secrets and PII from untrusted input before it reaches the trace backend**"*; `architecture/observability.md:636` - *"- Log sensitive data (passwords, tokens, PII)"* (under **Don't**) | **SATISFIED** | The obligation STANDARDS.md called *"most likely to be missed"* is the one the design handles best. §5.3 emits **redacted** arguments deliberately rather than accepting `include_payloads=False`'s no-arguments default; §4.1 enforces secret redaction at a single point with a failing test; §6.2 keeps EEO fields out of output models entirely. **One residue, and the design names it itself:** §5.3 says the full traceback reaches the server log and *"the log stream is treated as sensitive"* - a handling instruction with no stated mechanism (retention, access control, or where that log goes). Not a breach of B88, which governs clear-text PII, but it is the seam. |

### Public-repo obligations (B89-B106)

| B | Requires | Source (verified) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **B89** | The README License section names an SPDX identifier and links to `LICENSE` | `documentation/readme-standard.md:57` - *"13. **License** — SPDX identifier and link to `LICENSE`."* | **PARTIAL** | §10 settles the substance and settles it well: *"Apache-2.0, `Copyright 2026 evolv Consulting`, with a NOTICE"* - resolving the two questions STANDARDS.md §6.2 escalated, and choosing the licence whose patent grant and NOTICE mechanism §6.2 identified as the reason to prefer it. **Gap:** the obligation is specifically about the **README section**, which B77 leaves unspecified. The right thing exists with nowhere to be declared. |
| **B90** | `.env` and key material gitignored; `.env.example` is the committed template | `devops/environments.md:614-621` - *"```gitignore # .gitignore .env .env.local .env.*.local *.pem *.key secrets/"*; `architecture/security.md:412` - *"# .env.local (never commit)"*; `devops/docker.md:470-471` - `.env*` / `!.env.example` | **UNADDRESSED** | `.gitignore` is never mentioned. §10 builds two commit-time gates - a pre-commit secret scanner and a committed-file-type gate with magic-number sniffing - and never states the simplest control of the three. The file-type gate is allowlist-first with an extension denylist, so a `.env` may well be caught by it, but by accident of its extension policy rather than by design. On a public repo with a live Jobvite credential class, that is the wrong control to leave implicit. |
| **B91** | `.env.example` lists every variable, placeholder values only | `devops/environments.md:143-144` - *"```bash # .env.example - Copy to .env.local and fill in values"*; `documentation/readme-standard.md:50` - *"Secrets are referenced by name only; never include real values."* | **UNADDRESSED** | No `.env.example` in DESIGN.md. Same family as B78 and B53 - three obligations that each require an enumeration of the environment variables, and the design produces that enumeration nowhere despite naming seven variables in passing. |
| **B92** | Secrets never hardcoded in source | `documentation/agentic-coding-standard.md:126` - *"# NEVER generate code that:"*, item at `:127` - *"- Hardcodes secrets, API keys, or passwords"* (`:126` is what makes the item a prohibition, and its scope is *generated* code); `devops/development-workflow.md:280` - *"- [ ] No secrets or credentials in code"*, which carries the claim for source generally | **SATISFIED** | §4.1 and §7.3: all credentials are `SecretStr` from environment via pydantic-settings. §10's pre-commit secret scanning is the second line. |
| **B93** | Secrets are `SecretStr`, accessed via `.get_secret_value()`, never logged | `architecture/security.md:437-447` (the `SecretStr` field block); `:469` - *"# Always use .get_secret_value() to access secrets"*; `:472-473` - *"# Secrets are not logged or exposed in errors"* | **SATISFIED** | §4.1 states all three, and §4.1's jobFeed handling is the hard case done right - a URL that structurally must carry `sc=` as a query parameter, classified sensitive, never logged whole, never in an exception message, redacted at one enforcement point with a test that fails if a secret can reach a log record. |
| **B94** | CI reads secrets from the GitHub secrets store, never from the repo | `devops/environments.md:461-465` - *"```yaml # Use GitHub secrets and variables env: DATABASE_URL: ${{ secrets.DATABASE_URL }}"* | **NOT-APPLICABLE** | **Because CI holds no secrets.** §8 fixes that the default suite runs *"with no network and no credentials"* and §1.1 that no credential exists. There is nothing for CI to read from anywhere. **Becomes live the moment `CREDENTIAL-CHECKLIST.md` is satisfied** and the live suite is wired to run, which is the design's own stated trajectory (§8, §11.1) - worth a forward note in the design rather than a rediscovery then. |
| **B95** | TruffleHog secret scanning in CI on every PR | `devops/ci-cd.md:543-556`, job `secrets-scan`, `trufflesecurity/trufflehog@v3.88.0`, `fetch-depth: 0` | **SATISFIED** | §10, and exceeded with the pre-commit gate. (Duplicate of B69 by STANDARDS.md's own construction.) |
| **B96** | Third-party API keys rotate quarterly, and on any suspicion of exposure | `devops/environments.md:636` - *"\| Third-party API keys (Stripe, SendGrid, etc.) \| Quarterly \| Vendor breach notice, key found in logs \|"*; `:626-628` - rotation *"MUST be enforced (not aspirational) for every secret class"* with a runbook a new on-call engineer can follow without tribal knowledge | **UNADDRESSED** | No rotation policy or runbook reference anywhere. This server's whole reason to exist is holding third-party API keys - **three credential classes** by §4.1's own count, including the jobFeed's separate `companyId`. The standard's unscheduled trigger is literally *"key found in logs"*, which is the exact event §4.1's redaction test is designed to prevent; the design builds the detection and not the response. `:626` forecloses the "we'll do it informally" reading. |
| **B97** | Branch names follow the documented pattern | `devops/development-workflow.md:62-68` - *"\| Feature (Backend) \| `feature/BE-{ID}-short-description` \| … \| Bugfix \| `bugfix/{PREFIX}-{ID}-short-description` \| \| Hotfix \| `hotfix/{PREFIX}-{ID}-short-description` \| \| Release \| `release/v{VERSION}` \|"* | **UNADDRESSED** | Not stated, **and ADR-0006 does not reach it.** ADR-0006 is scoped to the branch *model* (single `main` vs `main`+`develop`); branch *naming* is an independent clause that survives the deviation intact. Compounded by B73's EC-### prefix collision - the `{PREFIX}` set is FE/BE/DB/DO and this work is tracked as EC. |
| **B98** | `main` protected: PR required, ≥1 approval, all CI checks pass, no direct pushes | `devops/development-workflow.md:72-77` - *"**main branch:** - Requires PR with at least 1 approval - All CI checks must pass - No direct pushes - Only merge from develop or hotfix branches - Signed commits required (recommended)"* | **UNADDRESSED** | Not stated. **Partly reachable by ADR-0006 and not reached:** the *"Only merge from develop or hotfix branches"* clause is the one ADR-0006's deviation necessarily voids, and ADR-0006 as described in §12 disposes of the two-branch model without disposing of that clause. The other four requirements - PR, approval, CI green, no direct pushes - are untouched by the deviation and remain binding, unstated. §10 builds nine CI gates and never says any of them is a **required** check; a gate nothing blocks on is a report. |
| **B99** | `develop` protected: PR, ≥1 approval, CI green, squash merge, branch current before merge | `devops/development-workflow.md:79-83` - *"**develop branch:** - Requires PR with at least 1 approval - All CI checks must pass - Squash merge required - Branch must be up to date before merge"* | **NOT-APPLICABLE** (settled deviation, ADR-0006) | ADR-0006 - *"single `main` branch rather than the mandated `main`+`develop` GitFlow"* - is correctly scoped for **this** obligation: with no `develop` branch there is nothing to protect. Note the residue: the four *properties* listed here (approval, CI green, squash, currency) are the same properties B98 requires of `main`, so removing `develop` should relocate them, not retire them. |
| **B100** | A PR template exists with the mandated sections | `devops/development-workflow.md:202-241` - the verbatim template (Summary, Type of Change, Changes Made, Testing, Test Commands Run, Screenshots, Checklist, Related Issues); `devops/quality-gates.md:48` - *"PR must include:"*, item at `:50` - *"- [ ] Completed PR template"* | **UNADDRESSED** | Not stated. |
| **B101** | Reviewers verify the code-review checklist before approving | `devops/development-workflow.md:248` - *"Reviewers must verify all items before approving:"*, checklist at `:250-309` | **UNADDRESSED** | Not stated. The Security (`:279-287`) and Type Safety (`:272-277`) blocks apply directly here; the frontend items do not. |
| **B102** | Squash merge; delete the branch after merge | `devops/development-workflow.md:192-194` - *"│ - Squash and merge │ … │ - Delete feature branch after merge │"* | **UNADDRESSED** | Not stated. |
| **B103** | A README exists at the repo root with all 14 sections | **Location half:** `documentation/readme-standard.md:32` - *"A `README.md` is **required** in each of the following locations:"*, listing at `:34-35` - *"- The top level of every Git repository. - The root of every published package (npm, PyPI, Cargo, Go module, container image, Helm chart)."*  **Sections half:** `:43` - *"Every README MUST contain the following sections, in this order. Section headings must match exactly so that automated checks can locate them."*, list at `:45-58` (the same clause B77 cites) | **PARTIAL** | Restatement of B77 with a second trigger. **Partial rather than unaddressed only** because the design references *"the README"* four times (§7.1, §7.2, §7.5 twice) and so presumes its existence - but presumes it as a place to put caveats, never as an artifact with a specification. Both triggers fire: this is a Git repository root and, per §10's packaging block, a published package. |
| **B104** | Contributing rules present - `CONTRIBUTING.md` or inlined under the heading | `documentation/readme-standard.md:56` - *"12. **Contributing** — link to `CONTRIBUTING.md` or equivalent. Repos without that file must inline the contribution rules under this heading."* | **UNADDRESSED** | Not stated. This is the corpus's only contributor-facing obligation, and it is live: §10 makes the repo public and org-owned, and §10's two commit-time gates (pre-commit secret scanning, the committed-file-type gate with its allowlist-override-in-the-same-commit rule) are exactly the local setup an outside contributor cannot discover without being told. |
| **B105** | Named maintainers in the README | `documentation/readme-standard.md:58` - *"14. **Maintainers** — named owners (people or team aliases) responsible for review and release."* | **UNADDRESSED** | Not stated. STANDARDS.md §6.5 is right that `CODEOWNERS` is **not** required - I confirmed zero occurrences across the standards tree - but named ownership **in the README** is, and B77's absence takes this with it. |
| **B106** | Required GitHub Actions checks wired to branch protection; skipped ≠ success; path-filtered jobs gated through an aggregator | `devops/ci-cd.md:679-681` - *"1. **Do not set `skipped == success` for required checks.** GitHub branch protection allows treating a skipped job as passing. Never enable this for integration tests, E2E smoke suites, or any gate that guards production"*; `:723-726` - *"4. **Path-filtered jobs that skip are not required checks.** A job that may legitimately not run (because no relevant files changed) must not be a direct branch-protection requirement. Gate it through an aggregator"*; `devops/infrastructure-as-code.md:160` - *"by branch protection."* | **PARTIAL** | §10 enumerates the nine jobs that would form the required set ✓ and §8 satisfies the test-level half of skipped≠success ✓. **Gap: the wiring.** Nothing says these are **required** checks, and neither structural rule is addressed. The aggregator rule has a live referent the design hands it: §10's `fastmcp inspect` diff and the two commit-time gates are naturally path-filtered, and a path-filtered job wired directly to branch protection is the exact configuration `:723-726` forbids. |

---

## 4. Ranked gaps by consequence

Ranked by what actually goes wrong if this ships as designed. B-number order is ignored.

### Tier 1 - a required CI gate is breached, or a control the design relies on does not exist

**1. B58 - the mandated collection-guard meta-test is absent.** `devops/quality-gates.md:79-81`
makes this unambiguous: absent guard → *"the CI backend test job MUST fail."* This is not a
best-practice gap, it is a required check that cannot pass. And the design is in the specific
configuration the guard exists for: §8 deliberately runs **two** suites with different selection
criteria, so a `test_*.py` orphaned from `testpaths` is maximally invisible. §8's `--collect-only`
control is good and solves a different problem - rot in the excluded suite, not unreachability of a
third file. **What goes wrong:** a test file that nobody runs, in a repo whose entire safety
argument is "the suite is green", plus a CI job that is non-compliant from the first commit.

**2. B39 - retries and circuit-breaker transitions are never logged.** `resilience.md:226` -
*"Never retry or trip silently."* §5.3's audit event fires once per tool invocation, around the
tool; three retries and a breaker trip inside it produce an identical record to a first-try
success. **What goes wrong:** on a server whose upstream has *never been observed succeeding*
(§1.1), the first production incident is undiagnosable. "Jobvite is slow", "Jobvite is down", and
"our timeout is too tight" are the same log line. This is the single gap that most degrades the
first bad day, and it is a five-line fix.

**3. B72 - no advisory-tracking or suppression policy, against a deliberately-beta dependency.**
§10 ships `fastmcp==4.0.0b4` as *"deliberate early adopters"*; `pip-audit` has **no severity
threshold** and fails on **any** advisory (`supply-chain-security.md:99-101`, quoted in
STANDARDS.md); `supply-chain-security.md:130-131` requires an *"explicit, time-bounded, reviewed
suppression"*. **What goes wrong:** one advisory against any transitive of a beta package turns a
required gate red with no sanctioned response, and the unsanctioned response - a blanket
`--ignore-vuln` added under deadline - is exactly the silent suppression the clause forbids. The
design chose the risk deliberately and did not design its handling.

**4. B64 + B65 - no `uv sync --frozen`, no committed `uv.lock`.** §10's own thesis is that *"the
`ResponseLimiting` regression arrived through the transitive SDK with zero change to the code that
broke"* - a diagnosis of exactly the disease frozen installs cure - and then pins two packages by
hand instead. **What goes wrong:** the failure §10 describes recurs through any of the other
transitives, and CI's graph drifts from the audited graph, which also silently undermines B67's
`pip-audit` and B70's SBOM (an SBOM generated from an unfrozen resolve documents a build nobody
shipped).

**5. B96 - no key-rotation policy for three credential classes.** `environments.md:626-628` makes
rotation *"enforced (not aspirational)"* with a runbook usable *"without prior tribal knowledge"*,
and `:636` sets quarterly for third-party API keys with *"key found in logs"* as an unscheduled
trigger. §4.1 builds excellent detection for that exact event and no response to it. **What goes
wrong:** a leaked Jobvite key on a public repo has no defined revocation path and the credential
outlives the incident.

### Tier 2 - a control the design claims is weaker than claimed

**6. B12 + B23 - the argument-rejection path has no stated error shape and is not in the
merge-gating list.** §5.1's reasoning is that problem objects are safe *"because they are
**returned** rather than raised"*. A schema violation is caught by FastMCP **before the tool body
runs**, so there is nothing to return from - it can only be raised, which by §5.1's own analysis
means no problem object. **What goes wrong:** the design's strongest compliance claim (B1/B2,
uniform RFC 9457) has a third hole beside the two §5.1 admits, and it is the one on the most
common failure path. §4.4 admits this honestly for rate limiting; the same admission is owed here.
Then B23's *"invalid/over-budget arguments"* arm needs adding to §8's required cases.

**7. B17 - the approval decision is not among the audited fields.** `agent-guardrails.md:122`
requires *"the approval decision if gated"*. `create_candidate` is gated three ways and its side
effect is *"an email to a live human"* (§2.2). **What goes wrong:** the only record that a real
write was authorised does not exist. When someone asks "who approved this candidate creation", the
audit event says a write happened and not that it was approved. Given §7.5's careful limit on what
may be claimed (*"never 'a human approved this'"*), the log is the only place the actual response
is recoverable - and it is not recorded.

**8. B40 - `request_id_var` ContextVar is missing, which is why B39 is missing.**
`tool-calling.md:173-175` says *"the canonical triple **verbatim**"*. Two of three are present.
**What goes wrong:** with no ContextVar the id must be threaded by parameter into
`utils/redaction.py`, the Jobvite client and the breaker - so the correlated retry/breaker logging
of B39 becomes awkward enough to skip, which is what happened. Fixing B40 makes B39 nearly free;
these should be fixed together.

**9. B30 + B25 - no inbound structural or encoding limits.** Nesting ≤5, list items ≤1 000, dict
keys ≤100, body ≤1 MiB (`input-validation.md:223-226`); control characters and encoding rejected
before dispatch (`prompt-injection.md:124-125`). §4.5's 500/1000 page caps are outbound transport
limits and §4.5 says so. **What goes wrong:** this is where the lead's "one mechanism, two
clusters" instinct pays out. The allow-listed output model is an **output** control; these are
**input** controls that must fire before dispatch, and the mechanism cannot reach them by
construction. §6.1 identifies `customField[]` as *"open-ended"* and bounds it only on return.

**10. B56 - the coverage remap inverts the risk, without an ADR.** The standard sets Utilities at
**95%** (`testing.md:588`). §8 has no utilities target, so `utils/redaction.py` - which holds
secret redaction *and* untrusted-content fencing, the two controls §8 itself lists as required
cases - falls to the 80% floor while the client is held to 90%. **What goes wrong:** the least
covered module is the one carrying two of the design's named security controls. A remap that
loosens a required number needs an ADR and has none in §12.

### Tier 3 - real but conventional, and cheap

**11. B77/B78/B103/B105/B89 - the README has four jobs and no specification.** The design assigns
the README four disclosures (§7.1 proxy headers, §7.2 `tools/list` behaviour, §7.5 the
abandoned-approval hang, §7.6 token semantics) and never specifies its existence, its 14 mandated
sections, its Configuration table, its maintainers, or where B89's SPDX declaration goes.
**B78 is the load-bearing one** - it also closes B15's *"documented max"* and, with B91, is the
enumeration B53 needs. One table discharges three obligations.

**12. B98 + B106 - nine CI gates, none declared required.** §10 builds the gates; nothing wires
them to branch protection, and neither structural rule (`skipped ≠ success` at job level, the
aggregator for path-filtered jobs) is addressed. **What goes wrong:** a gate nothing blocks on is
a report. §10's `fastmcp inspect` diff and the two commit-time gates are naturally path-filtered
and would be wired directly, which `ci-cd.md:723-726` specifically forbids.

**13. B7 - a Jobvite 4xx has no defined caller-facing status.** `error-handling.md:416-419` maps
`>=400` → `ExternalServiceException` (502). §5.1 passes the upstream status through. **What goes
wrong:** a Jobvite 401 surfaces to the caller as a 401, which reads as *the caller's* auth failing
rather than the server's upstream credential. Given §4.2's whole point is that Jobvite disguises a
401 as a 200, mislabelling it a second time on the way out is an avoidable own-goal.

**14. B90 + B91 + B53's `.env.example` half - no `.gitignore` policy on a public repo.** §10
builds two sophisticated commit-time gates and never states the simplest one. The file-type gate
may catch `.env` by extension policy, but by accident rather than design.

**15. B51 - no UTC datetime idiom, with three live surfaces.** Problem-object `timestamp` (§5.1),
token expiry (§7.6), and Jobvite's epoch-ms/`yyyy-MM-dd` asymmetry (§9.2). **What goes wrong:**
a naive datetime in §7.6 makes token expiry wrong by the UTC offset - silently, in the direction
of tokens living longer than intended, on the write path.

**16. B55's markers gap.** §8's credential-free strategy rests on excluding the live suite *by
selection*, which means a marker; without `--strict-markers` a typo in that marker name selects
nothing and CI goes green having run less than it claimed. Small change, disproportionate
protection for the design's central testing choice.

**17. B80 - Quickstart CI parity is unmeetable as implied, and unresolved.** §8 fixes CI as
credential-free; a Quickstart to a working state needs a credential. Either scope the Quickstart to
"starts and lists tools" (CI-exercisable, and worth stating) or take an ADR.

**18. Remaining hygiene, low consequence:** B49, B50, B52, B61, B73, B74, B75, B76, B82, B83-B87,
B94 (dormant), B97, B100, B101, B102, B104. Mostly `pyproject.toml` lines, workflow YAML, and
`.github/` files. Cheap; none changes behaviour. B82's link checker is worth pulling forward
slightly, since §7.4 and §7.7 rest evidentially on two upstream issue links.

---

## 5. ADR scope check

The lead asked whether the five settled deviations are scoped correctly. Three are; two are not.

| ADR | Scope as stated in §12 | Verdict |
|---|---|---|
| **ADR-0003** - `problem+json` unsettable on an MCP tool error | Correct. §5.2 states the violation plainly, does not overclaim mitigation (it withdrew an earlier draft's imaginary health endpoint), and volunteers the sharper consequence: on the default stdio transport, `problem+json` is honoured nowhere at all. | **Correctly scoped** |
| **ADR-0005** - the `ai/` domain binds by intent | Correct, and load-bearing: B9-B26 all descend from `ai/`. Without this ADR the largest satisfied cluster in the sweep rests on an unstated premise. | **Correctly scoped** |
| **ADR-0008** - EEO fields excluded from output models | Correct, and honestly framed in §6.2 as a design decision rather than a cited obligation, since the GDPR machinery is `priority: optional`. | **Correctly scoped** |
| **ADR-0002** - in-process rate limiting instead of Redis | **Under-scoped.** The Redis substitution is well argued (`rate-limiting.md:94-97`'s stated rationale is replica desync; a single-process server has no replicas). But `rate-limiting.md` rule 6 at `:361-362` is a **separate clause** - *"**429 uses ProblemDetail.** Raise `RateLimitException`, not `HTTPException(status_code=429)`"* - and §4.4 admits the design breaches it (*"A trip raises `MCPError`, not an `is_error` result"*, so no problem object). §5.1 lists this among its *"two honest exceptions to uniformity"* and assigns it **no ADR**. Rule 5 at `:359-360` (`RateLimit-*` headers on success and 429) is likewise undisposed. **Fix:** widen ADR-0002 to cover the lost ProblemDetail and the absent headers, or add a fourth ADR. As it stands the design's most candid admission is the one with no decision record behind it. |
| **ADR-0006** - single `main` rather than main+develop | **Under-scoped.** Correctly disposes of B99 (no `develop` → nothing to protect). Leaves two things standing: **B97** (branch *naming* - `feature/BE-{ID}-...`, an independent clause the branch-model deviation does not touch, and colliding with the EC-### prefix per STANDARDS.md C4), and the *"Only merge from develop or hotfix branches"* clause of **B98**, which the deviation necessarily voids and which nothing currently voids on the record. **Fix:** widen ADR-0006 to state what replaces both, and note that B99's four properties (PR, approval, CI green, squash, currency) relocate onto `main` rather than retiring. |

One ADR that §12 does not list and the sweep says is needed: **the B56 coverage remap.** §8 drops
the standard's Utilities 95% target entirely. Loosening a required coverage number is precisely the
class of deviation §12 exists to record.

---

## 6. What I could NOT verify

1. **Anything about the implementation.** No code exists. Every verdict is *design says / design
   does not say*. An UNADDRESSED verdict on a `pyproject.toml`-shaped obligation (B49, B52, B55,
   B61) will often be discharged the moment someone writes the file, and the sweep cannot
   distinguish "the design omitted it" from "the design correctly considered it out of scope".
   I have not padded these - they are recorded as unaddressed and ranked last.

2. **`docs/adr/` contents.** §12 lists eight ADRs "required at freeze". I assessed their **stated
   scope in §12** against the clauses they must dispose of. I did not open the ADR files; §12's
   phrasing ("ADRs required at freeze") suggests they are not yet written. If they exist, the
   scope findings in §5 need re-checking against their actual text.

3. **Whether the standards corpus changed under me.** I read it once, at one moment. All
   `file:line` citations in this report were resolved during this sweep.

4. **`ai/evaluation-testing.md`.** B12 and B23 both route merge-gating tests into *"the eval
   suite"* defined by that file, which STANDARDS.md itself records as not read in full. I did not
   read it either. If it imposes structure on what an eval suite is, B12/B23 may be more
   demanding than the PARTIAL verdicts here allow.

5. **`architecture/data-flow.md` and `architecture/threat-modeling.md`.** STANDARDS.md dismissed
   both as *"process/design-artifact standards rather than code obligations"* without reading
   them in full, and derived no B-numbers from them. They are `priority: required`. A design
   document is exactly the artifact a design-artifact standard would bind, so this is the most
   likely place for obligations the B-list never enumerated. **Out of scope for a B1-B106 sweep,
   flagged as a possible hole in the list itself.**

6. **Whether the five tools' actual Jobvite behaviour matches the design's hypotheses.** §1.1
   settles this: no credential, no sandbox, no observed 2xx. Obligations whose satisfaction needs
   a live call - the §4.5 `start`-base probe, the record-level not-found shape, whether success
   bodies carry a `status` block - cannot be verified now by anyone. Not marked as failures.

7. **B71's outcome.** The licence *gate* is present (SATISFIED). Whether `fastmcp==4.0.0b4`,
   `fastmcp-slim` and `httpx2` and their transitives all resolve to the five allow-listed licences
   is a question only running `pip-licenses` answers, and no lockfile exists to run it against.

8. **Whether `evolv Consulting` is the correct copyright holder.** §10 states
   `Copyright 2026 evolv Consulting`, which follows STANDARDS.md §6.2's recommendation. §6.2
   itself flags this as a legal determination needing Phil (casing, entity suffix, and whether the
   employment agreement vests copyright in the company). Unchanged by this sweep; still open.
