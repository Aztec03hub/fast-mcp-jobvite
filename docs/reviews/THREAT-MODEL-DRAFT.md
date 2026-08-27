# Threat Model, drop-in draft for DESIGN.md

**Task:** TM-1 · **Author:** conformance-sweep · **Date:** 2026-08-27
**Revision 2.** Re-modelled against DESIGN.md as it now stands (858 lines), not as it stood when
revision 1 was written. Four changes drove it: `ResponseCaching` dropped, inbound TLS added, the
§7.5 era discriminator fixed by spike, and the confirmation-token TTL still unstated.
**Satisfies:** `architecture/threat-modeling.md` TM1-TM8 (see `CONFORMANCE-DESIGN-ARTIFACT.md` §2.2)
**Status:** draft for review. **DESIGN.md is not edited.**

---

## How to use this file

Everything under the horizontal rule below is written in DESIGN.md's voice and is intended to be
pasted in as-is.

**Placement.** Insert as a new **§11**, after §10 "Repository and delivery" and before the current
§11 "Open questions". It references components from §2 through §10, so it has to sit after them.
That renumbers current §11 to §12 and §12 to §13.

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
   Machine-checked: all rated rows agree with the matrix.
3. **Every component is evaluated against all six STRIDE categories, per `:35`.** Where a category
   carries no credible threat, the row says so and gives the reason. A category is never dropped
   silently. Some components carry two rows in one category where two distinct threats exist.

**Traceability.** Threats matching a conformance finding carry the B-number. Threats with no
B-number are new here, surfaced by the STRIDE pass rather than the clause sweep, and are marked
**[NEW]**.

---

## 11. Threat Model

Authored before implementation, per `architecture/threat-modeling.md:143`. Four of the six Required
triggers at `:120-127` fire on this project: it handles PII, it changes authentication and
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
| B2. Network client (Streamable HTTP) | Remote or local MCP client | Server, scoped tool set | `StaticTokenVerifier` bearer token; `require_scopes` per data class; `allowed_hosts` / `allowed_origins` off-loopback; **TLS required off-loopback or the server refuses to start** (§7.1, §7.2) |
| B3. Server to Jobvite | Server | `api.jobvite.com` | `x-jvi-api` / `x-jvi-sc` headers, never in a URL; HTTPS with `httpx2` default verification, never disabled (§4.1, §7.1) |
| B4. Jobvite content to the model | Attacker-authored candidate free text | The calling model's context | Path-keyed allow-listed output models, fencing paths generated from those models, delimiter-token stripping (§6.1) |
| B5. Server to log sink | Server internals, including credentials and PII | Log stream and anything reading it | Single-point redaction in `utils/redaction.py` with a failing test; `include_payloads=False`; `mask_error_details=True` client-side only (§4.1, §5.3) |
| B6. Operator to configuration | Whoever sets environment variables | Server capability set, including whether writes exist and whether TLS is asserted | `pydantic-settings` fail-fast at boot; `JOBVITE_ENABLE_WRITES` and TLS enforcement both server-side (§7.1, §7.3, §2.2) |

### STRIDE Analysis

**C1. Transport and session** (`__main__.py`, `server.py`, `StaticTokenVerifier`, scopes)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C1 | S | Bearer token observed on a non-loopback bind and replayed | M | H | **High** | Off-loopback requires TLS or a declared terminating proxy; absence is a startup failure, not a warning (§7.1). Mitigated |
| C1 | S | Any local process able to spawn the server calls any tool over stdio | L | H | Medium | Accepted. The OS process boundary is the trust boundary (§7.2), stated rather than left implicit |
| C1 | T | Request or response modified in flight on a plaintext non-loopback bind, for example flipping `send_email` to `true` | M | H | **High** | Same control as C1-S row 1 (§7.1). Mitigated |
| C1 | R | A write cannot be attributed to a caller. `audit.py` mints a `request_id` per invocation (§5.3) but no caller or client identity is recorded, although `get_client_id` already derives one for rate limiting (§4.4) **[NEW]** | H | M | **High** | **Unmitigated.** Record the resolved client id in the audit event alongside `request_id` |
| C1 | I | Candidate PII readable in transit on a plaintext non-loopback bind | M | H | **High** | Same control as C1-S row 1 (§7.1). Mitigated |
| C1 | D | Connection or request flooding on the HTTP transport | M | M | Medium | `RateLimitingMiddleware` with a mandatory `get_client_id`, sized per session (§4.4) |
| C1 | E | A token provisioned with the wrong scope set reaches candidate PII it should not | L | H | Medium | `require_scopes` on the three data classes (§7.2). Consider validating configured scope sets at startup |

**C2. Middleware stack** (§7.7: `Timing`, `StructuredLogging`, `RateLimiting`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C2 | S | No credible threat. No adopted middleware establishes identity | - | - | - | Identity is established at C1 |
| C2 | T | No credible threat. No adopted middleware mutates request or response payloads | - | - | - | - |
| C2 | R | `StructuredLoggingMiddleware` runs with `include_payloads=False` and so emits no arguments, leaving invocations unreconstructable | H | M | **High** | `audit.py` emits redacted arguments itself rather than assuming middleware provides them (§5.3). Mitigated |
| C2 | I | `include_payloads` flipped to `True`, sending raw candidate PII to the framework log | L | H | Medium | Constructed with explicit arguments; the value is stated in §7.7 and its rationale in §5.3. Mitigated by review, not by a control |
| C2 | D | A configuration reload calls `limiters.clear()`, resetting every client's quota; repeated reloads are a trivial bypass (§4.4) | L | M | Low | Accepted. Requires operator access. Recorded in Residual Risks |
| C2 | E | No credible threat. No adopted middleware grants capability | - | - | - | - |

*`ResponseCaching` is not adopted (§7.7), so the scope-crossing disclosure and the spent-token
hazard it carried are both out of the model rather than mitigated within it.*

**C3. Tool argument layer** (input models, `strict=True`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C3 | S | No credible threat at this layer. Identity is established at C1 | - | - | - | - |
| C3 | T | Control characters or alternate encodings in a string argument pass unexamined into a Jobvite query (B25) | M | M | Medium | Reject control characters and enforce an encoding check before dispatch. Not currently specified |
| C3 | R | No credible threat beyond C1-R. Arguments are recorded redacted by `audit.py` | - | - | - | §5.3 |
| C3 | I | An over-broad search argument returns more candidate records than the caller needs | M | M | Medium | Result cap enforced in-tool, reported as `showing 50 of 1,240` (§7.7). Document the default (B15) |
| C3 | D | A deeply nested or very large argument payload consumes parse time and memory. No nesting, list-length, dict-key or body-size limits are specified (B30) | M | M | Medium | Add the four limits from `input-validation.md:223-226`. §4.5's page caps are outbound transport limits and do not bound an inbound argument |
| C3 | E | A schema violation reaches the tool body | L | H | Medium | `strict=True`, extra keys forbidden, validation before dispatch (§2.1). The rejection path's error shape is unspecified (B12) |

**C4. Approval subsystem** (`approval.py`, MRTR elicitation, `ctx.elicit()`, confirmation tokens)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C4 | S | A host auto-responds to the elicitation with no human present, so an approval represents no person | H | M | **High** | Not mitigable server-side. The MCP specification places human-in-the-loop on the host. §7.5 limits the claim to *"the server requires an approval response from the host"*. Carried to Residual Risks |
| C4 | T | A confirmation token altered or reused to authorise writing a different candidate | M | H | **High** | HMAC binding to the payload; forged, replayed, argument-mismatched and expired tokens each refused with distinct messages, each tested (§7.6, §8). Mitigated |
| C4 | T | The confirmation-token TTL is not stated anywhere, so the replay window is unreviewable and cannot be tuned per deployment. `agent-guardrails.md:106-107` requires bounds to be configuration, not constants buried in code (B22) **[NEW]** | M | M | Medium | State the default TTL and make it configuration. §8 tests that expiry works; nothing fixes what it expires after |
| C4 | R | The approval decision is not among the audited fields, so there is no record that a gated write was authorised. `agent-guardrails.md:122` requires it (B17) | H | M | **High** | **Unmitigated.** Add the approval decision, and which mechanism produced it, to the `audit.py` event |
| C4 | I | A confirmation token describes what would be written and may embed candidate PII; if logged unredacted it becomes a PII sink | L | M | Low | Redaction is enforced at one point (§4.1). Confirm token payloads are inside its coverage |
| C4 | D | An abandoned approval hangs the call. A client-side timeout does not bound it because the handler runs in the client's process (§7.5) | M | M | Medium | No server-side bound is possible. Disclosed to integrators. Carried to Residual Risks |
| C4 | E | An accepted elicitation carrying `approve: false` treated as approval | M | H | **High** | The guard checks action **and** value: `action == "accept" and content.get("approve") is True`, with a deny arm and an accept-carrying-false arm in the required tests (§7.5, §8). Mitigated |
| C4 | E | Era misdetection silently downgrades the control. If `protocol_version` is absent or carries an unanticipated value, elicitation is unavailable on the chosen path and the write falls through to the confirmation token alone, which by §7.6 *"enforces confirmation, not human confirmation"* **[NEW]** | M | M | Medium | The discriminator is now measured, not inferred (§7.5), which removes the inert-`hasattr` failure. Remaining ask: the fallback to token-only must be an explicit, logged decision rather than an implicit consequence of an unrecognised era |

**C5. Jobvite client** (`services/jobvite_client.py`)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C5 | S | A rejected credential returns `HTTP 200` with a `{"status":{"code":401}}` body and is read as success, reporting zero candidates for an unauthenticated caller (§4.2) | H | H | **Critical** | The invariant: successful only if the body carries no `status.code >= 400` **and** the HTTP status is below 400, both, every call. Required test (§8). Mitigated |
| C5 | T | Response substituted or modified in transit to Jobvite | L | H | Medium | HTTPS with `httpx2` default verification, never disabled (§7.1). Mitigated |
| C5 | R | Retries and circuit-breaker transitions are not logged, so upstream behaviour cannot be reconstructed. `resilience.md:226` requires it (B39) | H | M | **High** | **Unmitigated.** Log each retry and breaker transition with the correlation field. Depends on B40's `request_id_var` ContextVar, also missing |
| C5 | I | The `/v1/jobFeed` URL structurally carries `sc=` as a query parameter and could reach a log line or an exception message | M | H | **High** | Classified sensitive, never logged whole, `sc=` redacted at one enforcement point with a test that fails if a secret can reach a log record (§4.1). Mitigated |
| C5 | D | Retry amplification against an already-degraded Jobvite | M | M | Medium | Bounded retry budget inside the inbound timeout, jitter, one breaker per dependency, 4xx excluded from tripping it (§4.3). Mitigated |
| C5 | E | The Jobvite credential is write-capable in a deployment where `JOBVITE_ENABLE_WRITES=false`, so the narrowest-credential rule is not met (B21) | M | H | **High** | **Unmitigated.** Document that a read-only Jobvite key is required where writes are disabled. Whether Jobvite offers one is unknown, which makes this an operator instruction rather than an enforceable control |

**C6. Output pipeline** (`models/`, `utils/normalise.py`, fencing)

| Component | Category | Threat | L | I | Risk | Mitigation |
|---|---|---|---|---|---|---|
| C6 | S | Candidate free text forges a channel break and impersonates system instructions to the calling model | H | H | **Critical** | Explicit fencing of every free-text field, fencing paths generated from the output models so the two cannot drift, delimiter tokens stripped so content cannot close its own fence. Required test including a fence-closing attempt (§6.1, §8). Mitigated, with residual |
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
| C8 | R | No record of configuration changes, including `JOBVITE_ENABLE_WRITES` being flipped or TLS being declared as proxy-terminated | M | M | Medium | Log the enabled tool set, the write flag and the TLS posture once at startup |
| C8 | I | A real credential or a `.env` reaches the public repository. This repository has already had confidential material reach a public remote once | H | H | **Critical** | Partly mitigated: pre-commit secret scanning and a committed-file-type gate, both exceeding the standard (§10). **Gaps: no `.gitignore` policy is stated (B90) and no `.env.example` exists (B91).** State both |
| C8 | D | A required variable is unset and the server starts anyway, surfacing later as a confusing Jobvite 401 | M | L | Low | `pydantic-settings` fails at boot naming the variable, scoped to the tools actually enabled (§7.3). Mitigated |
| C8 | E | `JOBVITE_ENABLE_WRITES` enabled unintentionally, exposing `create_candidate` | L | H | Medium | Enforced server-side, and the write still requires approval plus a confirmation token (§2.2). Mitigated in depth |
| C8 | E | `JOBVITE_TLS_TERMINATED_BY_PROXY=true` asserted where no proxy terminates TLS, returning the deployment to plaintext with no warning **[NEW]** | L | H | Medium | Accepted. The server cannot verify what sits in front of it, and the alternative (trusting `X-Forwarded-Proto`) is spoofable by anyone who can reach the port. An operator assertion is the correct shape. Carried to Residual Risks |

### Threshold disposition

`threat-modeling.md:86-88`. Inherent Critical and High rows, and what each needs.

**Must mitigate before implementation proceeds** (unmitigated, inherent Critical or High):

| Row | Threat | Action | Ref |
|---|---|---|---|
| C1-R | No caller identity in the audit event | Record the resolved client id beside `request_id` | [NEW] |
| C4-R | Approval decision not audited | Add the decision and the mechanism that produced it to the audit event | B17 |
| C5-R | Retries and breaker transitions unlogged | Log both with the correlation field; needs `request_id_var` | B39, B40 |
| C5-E | Jobvite credential not scoped to the enabled tool set | Document that a read-only key is required where writes are disabled | B21 |
| C8-I | Credential or `.env` reaching the public repository | State the `.gitignore` policy and add `.env.example` | B90, B91 |

**Down from seven to five.** The TLS fix in §7.1 clears C1-S, C1-T and C1-I; dropping
`ResponseCaching` removes the cache disclosure from the model entirely rather than mitigating it.

**Mitigate before production release** (inherent Medium, unmitigated): C3-T control characters
(B25), C3-D structural argument limits (B30), C3-I and C6-D the undocumented result cap (B15),
C4-T the unstated token TTL (B22), C4-E the era-misdetection downgrade, C7-I log-stream handling,
C8-R configuration-change logging.

**Already mitigated at Critical or High**, listed so the mitigations are recognised as load-bearing
and not quietly removed later: C5-S the 200-with-401 trap, C6-S indirect prompt injection, C6-I EEO
exclusion, C7-I PII in logs, C4-T token binding, C4-E accept-carrying-false, C5-I the jobFeed URL,
C1-S/T/I the TLS requirement, C2-R the audit event existing at all. **Each of these has a required
test in §8, or in C1's case a startup check. That is not a coincidence and the coupling should be
preserved: if a mitigation here loses its test, this table becomes false.**

### Residual Risks

| Risk | Rating | Rationale for Acceptance |
|---|---|---|
| A host may auto-respond to elicitation with no human present, so an approval attests to a host response and not to a person (C4-S) | High | Not mitigable by a tool provider. The MCP specification places human-in-the-loop on the host. §7.5 states the honest claim and never asserts human approval. Defence in depth: the deploy-time flag and the confirmation token both operate without host cooperation |
| An autonomous agent can call preview then create with no human anywhere, so the token enforces confirmation and not human confirmation (§7.6) | Medium | Accepted and stated. The token still forces a deliberate two-step and defeats a single malformed or replayed call |
| Fencing reduces but cannot eliminate indirect prompt injection from candidate free text (C6-S) | Medium | Fencing plus delimiter stripping plus an allow-listed output model is the strongest available server-side control. The remaining exposure is the calling model's susceptibility, which is the host's boundary. Red-team cases are merge-gating (§6.1, §8) |
| An abandoned approval hangs the call with no server-side bound (C4-D) | Medium | The elicitation handler runs in the client's process, so no server-side timeout reaches it. The write is safe on every refusal path including abandonment, with `rows=0` confirmed. Disclosed to integrators |
| `JOBVITE_TLS_TERMINATED_BY_PROXY=true` is an operator assertion the server cannot verify (C8-E) | Medium | The server cannot see what terminates TLS in front of it. The alternative, trusting `X-Forwarded-Proto`, is spoofable by anyone who can reach the port and would be a worse control. An unverifiable assertion that fails loudly when absent beats a verifiable-looking one that lies |
| A configuration reload is a quota amnesty and repeated reloads bypass rate limiting (C2-D) | Low | Requires operator access, already inside the trust boundary. Framework limitation: only `limiters.clear()` applies new values |
| The log stream carries redacted arguments and full tracebacks with no specified retention or access control (C7-I) | Medium | Accepted only until C7-I's action is taken. If the log destination is a developer's local disk this is minor; if it is shipped anywhere it is not, and nothing currently says which |
| `problem+json` is honoured nowhere on the default stdio transport (§5.2) | Low | ADR-0003. A media type carries no security property here; the seven RFC 9457 members are present in the payload regardless |
| No success response from Jobvite has ever been observed, so every success-path shape is a hypothesis (§1.1) | Medium | Accepted deliberately and structurally: fail loudly rather than degrade to a plausible empty result; synthetic fixtures are labelled as hypotheses in the test module's own docstring; `CREDENTIAL-CHECKLIST.md` converts them when a key lands |

---

## Notes for review, not part of the drop-in section

### On your three fixes

**Dropping `ResponseCaching`: right, and the §7.7 text is the strongest version of it.** Recording
the un-executed key derivation as *why we do not need to execute it* is better than what I
recommended. One consequence worth naming: the cache is now out of the threat model **entirely**
rather than present-and-mitigated, which is the cleaner outcome. §7.7's closing condition (if a
cache is ever wanted, establish the key derivation by execution and prove isolation with two
differently-scoped tokens) is what keeps it out.

**TLS: right shape, and I want to be explicit about why.** Failing at startup rather than warning
matches §7.3's existing fail-fast posture, and `JOBVITE_TLS_TERMINATED_BY_PROXY=true` as an
**operator assertion** is correct where the obvious alternative is wrong. Trusting
`X-Forwarded-Proto` would look more rigorous and be strictly worse: that header is spoofable by
anyone who can reach the port, so it would authenticate the attacker's claim about their own
connection. An assertion the server cannot verify but which fails loudly when absent beats a check
that appears to verify and does not. Modelled as C8-E and carried to Residual Risks, rated Medium.

**The era discriminator: the fix is right and it changed my model.** `ctx.request_context.
protocol_version` against the same tuple FastMCP's own guard uses, with `ctx.transport` and
`session_id` both measured and both rejected as traps, is exactly the standard of evidence the rest
of the document holds. The new §7.5 table (MRTR raises on every handshake arm *including approve*)
is what makes C4-E-era rateable at all.

### One documentation defect, and it is the kind Phil has a standing rule about

**§7.6 still contains the paragraph beginning "`ResponseCachingMiddleware` must never touch the
preview tool"** (DESIGN.md:613), while §7.7 now says the middleware is not adopted. The document
currently asserts a rule about a component it also says does not exist. A reader of §7.6 alone
concludes the cache is in.

The standing instruction is to rewrite prose in place rather than append a correction, precisely
because appending leaves two contradictory claims. The §7.7 reversal is well written; the §7.6
paragraph needs to go, or be reduced to one clause inside §7.7's rationale, where it is genuinely
useful as the *second* reason not to adopt. **[REASONED]** I would fold it in as: the cache would
also have re-issued a spent preview token for its whole TTL, a self-inflicted denial of service on
the write path.

### Where I think a fix may still be the wrong shape

**C4-E, the era-misdetection downgrade, is the one to look at.** The discriminator is now correct
for the two eras that were measured. My concern is the third case: a `protocol_version` that is
absent, or a future era value nobody has seen. §2.2 lists the confirmation token as the fallback
*"where the host cannot elicit"*, which is right for a host that genuinely cannot. But an
unrecognised era produces the same observable condition, and the write then proceeds on
token-only - a control §7.6 itself describes as enforcing *"confirmation, not human confirmation."*

That is a silent downgrade of the strongest gate, triggered by an input the design does not
control. **It still fails closed against an unauthorised write, so it is not a hole** - which is
why I rated it Medium and not High. The ask is small: make the fallback an explicit, logged
decision rather than an implicit consequence, so an operator can see that approval was degraded
rather than discovering it from a candidate's inbox.

### What I could not do, unchanged from revision 1

- `:145` requires a Tech Lead or Security reviewer to validate the threat model at spec review. I
  authored it, so I cannot be its reviewer.
- `:146` requires mitigations to become numbered functional requirements. Blocked on B73's
  unresolved prefix question (the corpus expects FEAT/FR/BUG/TECH; this work is tracked as EC-###).

### Style

Written with hyphens rather than em dashes, matching DESIGN.md. My two earlier reports in
`docs/reviews/` use em dashes throughout, against Phil's standing preference; converting them is a
mechanical pass whenever you want it.
