# Threat Model, drop-in draft for DESIGN.md

**Task:** TM-1 · **Author:** conformance-sweep · **Date:** 2026-08-27
**Satisfies:** `architecture/threat-modeling.md` TM1-TM8 (see `CONFORMANCE-DESIGN-ARTIFACT.md` §2.2)
**Status:** draft for review. **DESIGN.md is not edited.**

---

## How to use this file

Everything under the horizontal rule below is written in DESIGN.md's voice and is intended to be
pasted in as-is.

**Placement.** Insert as a new **§11**, after §10 "Repository and delivery" and before the current
§11 "Open questions". It references components from §2 through §10, so it has to sit after them.
That renumbers current §11 to §12 and §12 to §13. Alternatively it can go in as §6.3, but it would
then forward-reference §7 and §10 heavily.

**Three conventions, stated because the template at `threat-modeling.md:94-116` leaves them open
and the standard's thresholds are meaningless without them.**

1. **The Risk column is inherent risk, before the control named in the same row's Mitigation
   column.** `:86` says *"Critical/High: Must mitigate before implementation proceeds"*. Read
   post-mitigation, that rule can never fire, because a rated row would already carry its
   mitigation. Read pre-mitigation it does real work: it says which threats may not be left to the
   implementer's judgement. Post-mitigation exposure lives in the Residual Risks table, which is
   what `:112-115` is for.
2. **Ratings are computed from the matrix at `:78-82`, not chosen.** Likelihood and Impact are
   judged against the definitions at `:62-74`; the Risk cell is then whatever the matrix says.
3. **Every component is evaluated against all six STRIDE categories, per `:35`.** Where a category
   carries no credible threat, the row says so and gives the reason. A category is never dropped
   silently. Some components carry two rows in one category where two distinct threats exist.

**One judgement worth surfacing before you read the table.** C8-I is rated Likelihood **High**, not
Medium, and that single cell drives the only inherent-Critical finding that is not already
mitigated. The reason is that this repository has already had confidential material reach a public
remote once (the CONFIDENTIAL PDF, tasks #8 and #16). `:64` defines High likelihood as *"Easily
exploitable, public attack tooling exists"*, which is a poor fit for an own-goal, but `:66` defines
Low as *"Requires insider access or unlikely preconditions"* and a repeat of a thing that has
already happened here is not an unlikely precondition. Medium would be defensible. I rated it High
because the observed base rate on this repo is not zero, and I would rather you argue me down than
have the rating flatter us.

**Traceability.** Threats that correspond to findings in the conformance sweeps carry their
B-number so the two documents stay joined. Threats with no B-number are new here, surfaced by the
STRIDE pass rather than by the clause-by-clause sweep. There are five of those, marked **[NEW]**.

---

## 11. Threat Model

Authored before implementation, per `architecture/threat-modeling.md:143`. Four of the six
Required triggers at `:120-127` fire on this project: it handles PII, it changes authentication and
authorization, it exposes API endpoints to external clients, and it is a third-party integration.

Risk is inherent risk, before the mitigation named in the same row. Ratings come from the matrix at
`threat-modeling.md:78-82`. All six STRIDE categories are evaluated against every component; where
a category carries no credible threat the row says so.

### Assets

| Asset | Sensitivity | Location |
|---|---|---|
| Candidate personal data (names, emails, phone numbers, résumés, cover letters, interview notes) | Restricted | Jobvite responses in transit; tool results; `models/`; logs if redaction fails |
| Special-category EEO data (`gender`, `race`, `veteranStatus`) | Restricted | Jobvite responses only. Excluded from every output model (§6.2), so never leaves the server |
| Jobvite v2 API credential (`x-jvi-api`, `x-jvi-sc`) | Restricted | Environment; `config.py` as `SecretStr`; request headers |
| Jobvite job-feed credential (`api`, `sc`, `companyId`) | Restricted | Environment; the `/v1/jobFeed` query string, which is why that URL is classified sensitive (§4.1) |
| MCP client bearer tokens | Restricted | Environment at startup; `StaticTokenVerifier` (§7.2) |
| Confirmation-token HMAC signing key | Restricted | Environment; `approval.py` (§7.6) |
| The capability to create a candidate in a live ATS | Restricted | `create_candidate`. Side effect is an email to a live human and there is no sandbox (§2.2) |
| Public job data | Public | `search_jobs`, `get_job_feed` results |
| Server log stream | Confidential | Local log sink. Carries redacted arguments plus full tracebacks (§5.3) |
| Service availability | Internal | The process itself |

### Trust Boundaries

| Boundary | From | To | Controls |
|---|---|---|---|
| B1. Local process spawn (stdio) | Any OS process able to spawn the server | Server, full tool set | None at the server. The OS process boundary is the control, by design (§7.2). `create_candidate` here rests on the deploy-time flag plus approval, not scopes |
| B2. Network client (Streamable HTTP) | Remote or local MCP client | Server, scoped tool set | `StaticTokenVerifier` bearer token; `require_scopes` per data class; `allowed_hosts` / `allowed_origins` when not loopback (§7.1, §7.2). **No transport encryption specified** |
| B3. Server to Jobvite | Server | `api.jobvite.com` | `x-jvi-api` / `x-jvi-sc` headers, never in a URL (§4.1). TLS by `https://` scheme and `httpx2` default verification, not stated anywhere in the design |
| B4. Jobvite content to the model | Attacker-authored candidate free text | The calling model's context | Path-keyed allow-listed output models; explicit fencing with delimiter-token stripping (§6.1) |
| B5. Server to log sink | Server internals, including credentials and PII | Log stream and anything reading it | Single-point redaction in `utils/redaction.py` with a failing test; `include_payloads=False`; `mask_error_details=True` client-side only (§4.1, §5.3) |
| B6. Operator to configuration | Whoever sets environment variables | Server capability set, including whether writes exist at all | `pydantic-settings` fail-fast at boot; `JOBVITE_ENABLE_WRITES` enforced server-side (§7.3, §2.2) |

### STRIDE Analysis

**C1. Transport and session** (`__main__.py`, `server.py`, `StaticTokenVerifier`, scopes)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C1 | S | Bearer token observed on a non-loopback bind and replayed. §7.1 contemplates a non-loopback bind and specifies no transport encryption **[NEW]** | M | H | **High** | Require TLS whenever the bind address is not loopback, or refuse to bind off-loopback without it. Not currently specified |
| C1 | S | Any local process able to spawn the server calls any tool over stdio | L | H | Medium | Accepted. The OS process boundary is the trust boundary (§7.2), stated rather than left implicit |
| C1 | T | Request or response modified in flight on a plaintext non-loopback bind, for example flipping `send_email` to `true` **[NEW]** | M | H | **High** | Same control as C1-S row 1. Not currently specified |
| C1 | R | A write cannot be attributed to a caller. `audit.py` mints a `request_id` per invocation (§5.3) but no caller or client identity is recorded, although `get_client_id` already derives one for rate limiting (§4.4) **[NEW]** | H | M | **High** | Record the resolved client id in the audit event alongside `request_id` |
| C1 | I | Candidate PII readable in transit on a plaintext non-loopback bind **[NEW]** | M | H | **High** | Same control as C1-S row 1 |
| C1 | D | Connection or request flooding on the HTTP transport | M | M | Medium | `RateLimitingMiddleware` with a mandatory `get_client_id`, sized per session (§4.4) |
| C1 | E | A token provisioned with the wrong scope set reaches candidate PII it should not | L | H | Medium | `require_scopes` on the three data classes (§7.2). Consider validating the configured scope sets at startup |

**C2. Middleware stack** (§7.7)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C2 | S | No credible threat. No middleware in the adopted set establishes identity | - | - | - | Identity is established at C1 |
| C2 | T | A cached preview response re-issues a spent confirmation token for the cache TTL, making the write unusable (§7.6) | M | M | Medium | `ResponseCaching` never applied to the preview tool (§7.7) |
| C2 | R | `StructuredLoggingMiddleware` runs with `include_payloads=False` and so emits no arguments, leaving invocations unreconstructable | H | M | **High** | `audit.py` emits redacted arguments itself rather than assuming middleware provides them (§5.3). Mitigated |
| C2 | I | `ResponseCaching` keyed without client identity serves one scope's cached candidate PII to a caller holding only the public-job-data scope, defeating §7.2 **[NEW]** | M | H | **High** | **Unmitigated.** Establish the cache key derivation by execution, as §4.4 did for the sibling middleware, which was measured to key every caller to the literal string `"global"`. Then namespace by client id, or do not cache PII-bearing tools, or drop `ResponseCaching` |
| C2 | D | A configuration reload calls `limiters.clear()`, resetting every client's quota; repeated reloads are a trivial bypass (§4.4) | L | M | Low | Accepted. Requires operator access. Recorded in Residual Risks |
| C2 | E | No credible threat. No adopted middleware grants capability | - | - | - | - |

**C3. Tool argument layer** (input models, `strict=True`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C3 | S | No credible threat at this layer. Identity is established at C1 | - | - | - | - |
| C3 | T | Control characters or alternate encodings in a string argument pass unexamined into a Jobvite query (B25) | M | M | Medium | Reject control characters and enforce an encoding check before dispatch. Not currently specified |
| C3 | R | No credible threat beyond C1-R. Arguments are recorded redacted by `audit.py` | - | - | - | §5.3 |
| C3 | I | An over-broad search argument returns more candidate records than the caller needs | M | M | Medium | Result cap enforced in-tool, reported as `showing 50 of 1,240` (§7.7). Document the default (B15) |
| C3 | D | A deeply nested or very large argument payload consumes parse time and memory. No nesting, list-length, dict-key or body-size limits are specified (B30) | M | M | Medium | Add the four limits from `input-validation.md:223-226`. §4.5's 500/1000 page caps are outbound transport limits and do not bound an inbound argument |
| C3 | E | A schema violation reaches the tool body | L | H | Medium | `strict=True`, extra keys forbidden, validation before dispatch (§2.1). Note the rejection path's error shape is unspecified (B12) |

**C4. Approval subsystem** (`approval.py`, MRTR elicitation, confirmation tokens)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C4 | S | A host auto-responds to the elicitation with no human present, so an approval represents no person | H | M | **High** | Not mitigable server-side. The MCP specification places human-in-the-loop on the host. §7.5 already limits the claim to *"the server requires an approval response from the host"*. Carried to Residual Risks |
| C4 | T | A confirmation token altered or reused to authorise writing a different candidate | M | H | **High** | HMAC binding to the payload; forged, replayed, argument-mismatched and expired tokens each refused with distinct messages, each tested (§7.6, §8). Mitigated |
| C4 | R | The approval decision is not among the audited fields, so there is no record that a gated write was authorised. `agent-guardrails.md:122` requires it (B17) | H | M | **High** | **Unmitigated.** Add the approval decision and its source leg to the `audit.py` event |
| C4 | I | A confirmation token describes what would be written and may embed candidate PII; if logged unredacted it becomes a PII sink | L | M | Low | Redaction is enforced at one point (§4.1). Confirm token payloads are inside its coverage |
| C4 | D | An abandoned approval hangs the call. A client-side timeout does not bound it because the handler runs in the client's process (§7.5) | M | M | Medium | No server-side bound is possible. Disclosed to integrators via the README. Carried to Residual Risks |
| C4 | E | An accepted elicitation carrying `approve: false` treated as approval | M | H | **High** | The guard checks action **and** value: `action == "accept" and content.get("approve") is True`, with a deny arm and an accept-carrying-false arm in the required tests (§7.5, §8). Mitigated |

**C5. Jobvite client** (`services/jobvite_client.py`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C5 | S | A rejected credential returns `HTTP 200` with a `{"status":{"code":401}}` body and is read as success, reporting zero candidates for an unauthenticated caller (§4.2) | H | H | **Critical** | The invariant: successful only if the body carries no `status.code >= 400` **and** the HTTP status is below 400, both, every call. Required test (§8). Mitigated |
| C5 | T | Response substituted or modified in transit to Jobvite | L | H | Medium | `https://` plus `httpx2` default certificate verification. Not stated in the design; state it |
| C5 | R | Retries and circuit-breaker transitions are not logged, so upstream behaviour cannot be reconstructed. `resilience.md:226` requires it (B39) | H | M | **High** | **Unmitigated.** Log each retry and breaker transition with the correlation field. Depends on B40's `request_id_var` ContextVar, which is also missing |
| C5 | I | The `/v1/jobFeed` URL structurally carries `sc=` as a query parameter and could reach a log line or an exception message | M | H | **High** | Classified sensitive, never logged whole, `sc=` redacted at one enforcement point in `utils/redaction.py`, with a test that fails if a secret can reach a log record (§4.1). Mitigated |
| C5 | D | Retry amplification against an already-degraded Jobvite | M | M | Medium | Bounded retry budget inside the inbound timeout, jitter, one breaker per dependency, 4xx excluded from tripping it (§4.3). Mitigated |
| C5 | E | The Jobvite credential is write-capable in a deployment where `JOBVITE_ENABLE_WRITES=false`, so the narrowest-credential rule is not met (B21) | M | H | **High** | **Unmitigated.** Document that a read-only Jobvite key is required where writes are disabled. Whether Jobvite offers one is unknown, which makes this an operator instruction rather than an enforceable control |

**C6. Output pipeline** (`models/`, `utils/normalise.py`, fencing)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C6 | S | Candidate free text forges a channel break and impersonates system instructions to the calling model | H | H | **Critical** | Explicit fencing of every free-text field, with delimiter tokens occurring inside the content stripped so content cannot close its own fence. Required test including a fence-closing attempt (§6.1, §8). Mitigated, with residual |
| C6 | T | An unknown non-string field is stringified, inventing a representation and colliding with `strict=True` output models | M | L | Low | Unknown non-string fields are dropped, not stringified. Required test (§6.1, §8). Mitigated |
| C6 | R | No credible threat. This component produces no auditable decision | - | - | - | - |
| C6 | I | Special-category EEO fields (`gender`, `race`, `veteranStatus`) flow to the model | H | H | **Critical** | Not present in any output model, so they never leave the server (§6.2, ADR-0008). Mitigated |
| C6 | I | A newly added Jobvite field leaks to the model without review | M | M | Medium | Path-keyed allow-list fails closed: an unlisted field is dropped until someone adds it deliberately (§2.1). Mitigated |
| C6 | D | An unbounded Jobvite page returned to the model as a context and cost blowout | M | M | Medium | Result size bounded inside each tool, cap is configuration (§7.7). Document the default (B15) |
| C6 | E | No credible threat. This component grants no capability | - | - | - | - |

**C7. Audit and logging** (`audit.py`, `utils/redaction.py`, `loguru`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C7 | S | No credible threat. This component establishes no identity | - | - | - | - |
| C7 | T | A caller-supplied `X-Request-ID` carrying newlines forges log entries, or an over-long value bloats the log | M | M | Medium | Validated as a UUIDv4 before use and replaced if invalid (§5.3, B41). Mitigated |
| C7 | R | Covered by C1-R and C4-R | - | - | - | - |
| C7 | I | Candidate PII written to logs in the clear | H | H | **Critical** | `audit.py` emits redacted arguments deliberately rather than accepting `include_payloads=False`'s no-arguments default; single-point redaction with a failing test (§4.1, §5.3, B88). Mitigated |
| C7 | I | Full tracebacks reach the server log. §5.3 says *"the log stream is treated as sensitive"*, which asserts a boundary without naming a control: no retention, access-control or destination is specified **[NEW]** | M | M | Medium | State where the log goes, who can read it, and how long it is kept. Carried to Residual Risks |
| C7 | D | A hostile caller inflates log volume to exhaust disk | M | L | Low | Rate limiting bounds request volume (§4.4) |
| C7 | E | No credible threat | - | - | - | - |

**C8. Configuration and secrets** (`config.py`, environment, repository)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C8 | S | No credible threat. Configuration establishes no identity | - | - | - | - |
| C8 | T | Environment or `.env` modified by a local actor to redirect credentials or enable writes | L | H | Medium | OS file permissions. Outside the server's control, stated for completeness |
| C8 | R | No record of configuration changes, including `JOBVITE_ENABLE_WRITES` being flipped | M | M | Medium | Log the enabled tool set and the write flag once at startup |
| C8 | I | A real credential or a `.env` reaches the public repository. This repository has already had confidential material reach a public remote once | H | H | **Critical** | Partly mitigated: pre-commit secret scanning and a committed-file-type gate, both exceeding the standard (§10). **Gaps: no `.gitignore` policy is stated (B90) and no `.env.example` exists (B91).** State both |
| C8 | D | A required variable is unset and the server starts anyway, surfacing later as a confusing Jobvite 401 | M | L | Low | `pydantic-settings` fails at boot naming the variable, scoped to the tools actually enabled (§7.3). Mitigated |
| C8 | E | `JOBVITE_ENABLE_WRITES` enabled unintentionally, exposing `create_candidate` | L | H | Medium | Enforced server-side, and the write still requires approval plus a confirmation token (§2.2). Mitigated in depth |

### Threshold disposition

`threat-modeling.md:86-88`. Inherent Critical and High rows, and what each needs.

**Must mitigate before implementation proceeds** (unmitigated, inherent Critical or High):

| Row | Threat | Action | Ref |
|---|---|---|---|
| C1-S, C1-T, C1-I | No transport encryption specified for a non-loopback bind | Require TLS off-loopback, or refuse to bind off-loopback without it | [NEW] |
| C2-I | `ResponseCaching` may serve one scope's candidate PII to another | Establish the key derivation by execution; namespace, restrict, or drop the middleware | [NEW] |
| C1-R | No caller identity in the audit event | Record the resolved client id beside `request_id` | [NEW] |
| C4-R | Approval decision not audited | Add the decision and its source leg to the audit event | B17 |
| C5-R | Retries and breaker transitions unlogged | Log both with the correlation field; needs `request_id_var` | B39, B40 |
| C5-E | Jobvite credential not scoped to the enabled tool set | Document that a read-only key is required where writes are disabled | B21 |
| C8-I | Credential or `.env` reaching the public repository | State the `.gitignore` policy and add `.env.example` | B90, B91 |

**Mitigate before production release** (inherent Medium, unmitigated): C3-T control characters
(B25), C3-D structural argument limits (B30), C3-I and C6-D the undocumented result cap (B15),
C5-T stating TLS on the outbound path, C7-I log-stream handling, C8-R configuration-change logging.

**Already mitigated at Critical or High**, listed so the mitigations are recognised as load-bearing
and not quietly removed later: C5-S the 200-with-401 trap, C6-S indirect prompt injection, C6-I EEO
exclusion, C7-I PII in logs, C4-T token binding, C4-E accept-carrying-false, C5-I the jobFeed URL,
C2-R the audit event existing at all. **Each of these has a required test in §8. That is not a
coincidence and the coupling should be preserved: if a mitigation here loses its test, this table
becomes false.**

### Residual Risks

| Risk | Rating | Rationale for Acceptance |
|---|---|---|
| A host may auto-respond to elicitation with no human present, so an approval attests to a host response and not to a person (C4-S) | High | Not mitigable by a tool provider. The MCP specification places human-in-the-loop on the host. §7.5 states the honest claim and never asserts human approval. Defence in depth: the deploy-time flag and the confirmation token both operate without host cooperation |
| An autonomous agent can call preview then create with no human anywhere, so the token enforces confirmation and not human confirmation (§7.6) | Medium | Accepted and stated. The token still forces a deliberate two-step and defeats a single malformed or replayed call |
| Fencing reduces but cannot eliminate indirect prompt injection from candidate free text (C6-S) | Medium | Fencing plus delimiter stripping plus an allow-listed output model is the strongest available server-side control. The remaining exposure is the calling model's susceptibility, which is the host's boundary. Red-team cases are merge-gating (§6.1, §8) |
| An abandoned approval hangs the call with no server-side bound (C4-D) | Medium | The elicitation handler runs in the client's process, so no server-side timeout reaches it. The write is safe on every refusal path including abandonment, with `rows=0` confirmed. Disclosed to integrators |
| A configuration reload is a quota amnesty and repeated reloads bypass rate limiting (C2-D) | Low | Requires operator access, which is already inside the trust boundary. Framework limitation: only `limiters.clear()` applies new values |
| The log stream carries redacted arguments and full tracebacks with no specified retention or access control (C7-I) | Medium | Accepted only until C7-I's action is taken. If the log destination is a developer's local disk this is minor; if it is shipped anywhere it is not, and nothing currently says which |
| `problem+json` is honoured nowhere on the default stdio transport (§5.2) | Low | ADR-0003. A media type carries no security property here; the seven RFC 9457 members are present in the payload regardless |
| No success response from Jobvite has ever been observed, so every success-path shape is a hypothesis (§1.1) | Medium | Accepted deliberately and structurally: fail loudly rather than degrade to a plausible empty result; synthetic fixtures are labelled as hypotheses in the test module's own docstring; `CREDENTIAL-CHECKLIST.md` converts them when a key lands |

---

## Notes for review, not part of the drop-in section

**Five threats here have no B-number.** They came out of applying STRIDE per component rather than
walking clauses, which is the argument for the standard requiring this artifact at all:

1. **C1-S / C1-T / C1-I, no transport encryption off-loopback.** The conformance sweep found TLS
   unmentioned; STRIDE is what turns that into three rated rows across three categories and puts
   them above the "before implementation" bar.
2. **C1-R, no caller identity in the audit event.** Entirely new. §5.3 mints a `request_id` and
   §4.4 already derives a client id for rate limiting, so the value exists and is simply not
   recorded. Rated High because it fires on every request, and because C4-R depends on it: recording
   *that* a write was approved is worth much less if you cannot say *who* was approved.
3. **C2-I, the cache.** Already reported from CONF-2. It is here because STRIDE places it as an
   Information Disclosure at a trust boundary rather than as a missed clause, which is the framing
   that makes its severity legible.
4. **C7-I, the log stream asserted sensitive with no control.** §5.3's own phrase, turned into a
   rated row.
5. **C8-R, no configuration-change record.** Minor, cheap.

**What I could not do.** C2-I's rating assumes the unsafe default. I have not executed
`ResponseCachingMiddleware` and will not assert its key derivation, so if the spike shows identity
is already in the key, C2-I drops to Low and leaves the must-mitigate list. That single unknown is
the largest source of error in this table.

**One process point.** `threat-modeling.md:145` requires a Tech Lead or Security reviewer to
validate the threat model at spec review, and `:146` requires mitigations to become numbered
functional requirements. I have done neither: I authored it, so I cannot be its reviewer, and the
FR-numbering depends on the ticket-prefix question that B73 leaves open (the corpus expects
FEAT/FR/BUG/TECH and this work is tracked as EC-###). Both are yours to route.

**Style.** Written with hyphens rather than em dashes, matching DESIGN.md and Phil's standing
preference. Worth flagging that my two earlier review reports in `docs/reviews/` use em dashes
throughout, against that preference. Say the word and I will convert them.
