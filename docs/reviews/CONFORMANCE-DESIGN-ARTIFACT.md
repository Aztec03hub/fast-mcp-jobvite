# Design-artifact standards: obligations the B-list never derived

**Task:** CONF-2 · **Author:** conformance-sweep · **Date:** 2026-08-27
**Companion to:** `docs/reviews/CONFORMANCE-B1-B106.md`

**Subject:** `architecture/threat-modeling.md` and `architecture/data-flow.md` - both
`priority: required`, both dismissed by `docs/research/STANDARDS.md` §3 as *"process/design-artifact
standards rather than code obligations"* **without being read**, so no B-number was ever derived
from either. Plus the wider question: was that dismissal a one-off or a method?

---

## 1. Headline

**Three findings, in descending order of consequence.**

1. **`threat-modeling.md` binds, and DESIGN.md is missing a mandated section.** The file is
   `applicable_to: [all]`, `priority: required`. **Four of its six "Required" triggers fire on this
   project.** It obliges a Threat Model section - assets, trust boundaries, STRIDE analysis,
   residual risks - *inside the design document, before implementation*. DESIGN.md has none of it.
   The word "threat" appears once, incidentally. **The dismissal was wrong**, and the reasoning that
   produced it ("process/design-artifact standard") is the exact reasoning that should have made it
   bind, since DESIGN.md *is* the design artifact.

2. **A previously-unfound security question, surfaced by a standard nobody read.**
   `architecture/caching.md` was dismissed conditionally - *"Optional here; if a cache is added it
   becomes live"* - and **DESIGN.md §7.7 adds one** (`ResponseCaching`). The condition tripped and
   nobody noticed. `caching.md:841` forbids caching **user-specific data without proper
   namespacing**. This server's cached responses are candidate PII, and §4.4 has already *measured*
   that this framework's sibling middleware defaults every caller to the literal string `"global"`.
   See §5 - this is the highest-value thing in this report.

3. **The dismissal was a method, not a slip - and the method is unsound in one specific way.**
   STANDARDS.md decided applicability by **inferring scope from a file's title and domain** rather
   than from its `applicable_to` frontmatter and Scope section. That heuristic is right ~95% of the
   time and fails in a predictable direction: it cannot see a document whose *subject matter* looks
   stack-specific but whose *scope declaration* says `all`. §6 gives the shape and the audit.

**`data-flow.md` is genuinely NOT-APPLICABLE** - but STANDARDS.md reached that right answer for a
wrong reason, and the wrong reason is what it then reused on `threat-modeling.md`. §4.

---

## 2. `architecture/threat-modeling.md` - BINDS

### 2.1 Why it binds, from the file

Frontmatter, `architecture/threat-modeling.md:6-9`:

```
applicable_to:
  - all
priority: required
```

`:24` - *"Define a lightweight, repeatable methodology for identifying and mitigating threats at
design time. **Every security-relevant feature must include a threat model before implementation
begins.**"*

`:26-31`, Scope - all four bullets fire:

> *"- New features handling authentication, authorization, or sensitive data
> - External integrations and API surfaces
> - Infrastructure changes affecting trust boundaries
> - Data flow changes crossing security domains"*

`:120-127`, **"### Required (Tier 1 and Tier 2 specs)"** - **four of six triggers fire**:

| Trigger, verbatim from `:122-127` | Fires? | Why |
|---|---|---|
| *"Features handling PII or financial data"* | **YES** | Candidate PII is the entire subject; §2's tool table classifies three of five tools as `candidate PII`. |
| *"Authentication/authorization changes"* | **YES** | §7.2 `StaticTokenVerifier`, three scopes, `require_scopes`. |
| *"New API endpoints exposed to external clients"* | **YES** | Five MCP tools plus an opt-in Streamable HTTP transport (§7.1). |
| *"Third-party integrations"* | **YES** | Jobvite. The whole project. |
| *"Infrastructure or deployment topology changes"* | no | No deployment target. |
| *"Multi-tenant data access patterns"* | no | Single tenant per credential. |

`:135-139`, **"### Not Required"**, does not reach this: the exclusions are *"Documentation-only
changes"*, *"UI styling or layout changes with no data flow impact"*, and *"Dependency updates"*.

**[REASONED]** One trigger would suffice. Four fire. There is no reading of this file's own scope
rules on which a stateless server handling candidate PII, authenticating external clients, and
integrating a third-party ATS is out of scope.

### 2.2 What it obliges, and how DESIGN.md scores

| # | Obligation | Source (verified, verbatim) | Verdict | Evidence / gap |
|---|---|---|---|---|
| **TM1** | A threat model exists for every security-relevant feature, authored **before implementation begins** | `:24` - *"Every security-relevant feature must include a threat model before implementation begins."* | **UNADDRESSED** | No threat model exists in DESIGN.md or anywhere in `docs/`. Timing is the sharp part: `:143` - *"Threat model is authored during specification (before implementation)"*. No code exists yet, so this is **still satisfiable at zero cost**, and will not be after freeze. |
| **TM2** | The design uses **STRIDE per-component**, evaluating all six categories against each component | `:35` - *"Use **STRIDE per-component** as the default approach. For each component in the feature's data flow, evaluate all six STRIDE categories."* | **UNADDRESSED** | No STRIDE analysis. The words spoofing, tampering, repudiation, elevation appear zero times in DESIGN.md. |
| **TM3** | The seven-step process is followed: identify assets → map trust boundaries → enumerate components → apply STRIDE → rate risk → define mitigations → document residual risk | `:50-56` | **PARTIAL** | Steps 3 and 6 are done well and informally - §3 enumerates components, and the document is largely a catalogue of mitigations. **Steps 1, 2, 4, 5, 7 are absent as artifacts.** Step 2 is the notable near-miss: §7.2 identifies exactly one trust boundary (*"stdio is unauthenticated by design… the trust boundary is the operating system's, not this server's"*) and identifies it correctly. One boundary is mapped; the others are not. See §2.3. |
| **TM4** | Risk is rated likelihood × impact on the documented matrix | `:78-82` (the matrix); `:62-74` (the level definitions) | **UNADDRESSED** | No risk ratings anywhere. §9 "Known contract hazards" and §11 "Open questions" are the nearest artifacts and neither carries a likelihood, an impact, or a rating. |
| **TM5** | Critical/High risks are mitigated **before implementation proceeds**; Medium before production release; Low accepted with documented rationale | `:86-88` - *"- **Critical/High**: Must mitigate before implementation proceeds - **Medium**: Mitigate before production release - **Low**: Accept with documented rationale or address in future iteration"* | **UNADDRESSED** | With no ratings (TM4) there is no threshold to apply. **Consequence:** DESIGN.md §12 freezes the design at 0C/0H/0M *"after which only a numbered ADR may change it"*. Freezing without ratings means no risk was ever tested against the "must mitigate before implementation proceeds" bar. |
| **TM6** | The **Threat Model section** is included in the spec, using the given template - Assets, Trust Boundaries, STRIDE Analysis, Residual Risks | `:92` - *"Include this section in specifications for security-relevant features:"*, template at `:94-116`; `:144` - *"Security-relevant specs must include the Threat Model section"* | **UNADDRESSED** | **This is the concrete deliverable and it does not exist.** Four mandated tables, none present. `:144` uses MUST-equivalent language about the *section*, not merely the analysis. |
| **TM7** | Mitigations become functional requirements; residual risks are documented in an Assumptions & Ambiguities section | `:146-147` - *"4. Mitigations become functional requirements (FR-XXX) in the spec 5. Residual risks are documented in the Assumptions & Ambiguities section"* | **PARTIAL** | Mitigations are real and traceable, but as prose, not numbered requirements - which also feeds B73's unresolved ID scheme. **Residual risk is the stronger half and DESIGN.md does it well in substance**: §7.5 (*"It enforces confirmation, not human confirmation"*), §7.6's stated limit, §5.2's honesty that `problem+json` is honoured nowhere on stdio, §11's six open questions. The material for a Residual Risks table exists and is scattered across five sections instead of collected into one. |
| **TM8** | A Tech Lead or Security reviewer validates the threat model at spec review | `:145` - *"Tech Lead or Security reviewer validates the threat model during spec review"* | **UNADDRESSED** | No threat model to validate. Note round 1 (`DESIGN-R1.md`) and the in-flight DR2 are design reviews, not threat-model validations, and neither had a threat model to check. |
| **TM9** | *(Alternative)* For lower-risk features, the eight-item threat checklist may substitute for full STRIDE | `:151` - *"For lower-risk features where full STRIDE analysis is excessive, use this checklist:"*, items at `:153-160` | **NOT AVAILABLE to this project** | `:151` scopes the substitution to *"lower-risk features"*. A project firing four `:120-127` Required triggers is not one. **Recorded because the checklist is still a useful cross-check** - scored in §2.4, where it surfaces one new gap. |

### 2.3 Trust boundaries the design leaves unmapped

**[REASONED]**, offered as evidence for TM3 rather than as a finding in itself. TM3 step 2 asks for
*"where privilege levels change"*. DESIGN.md maps one. At least five exist:

1. **Host ↔ server over stdio** - mapped, §7.2, and correctly resolved to the OS boundary.
2. **Client ↔ server over Streamable HTTP** - partially mapped. §7.2 covers authN via
   `StaticTokenVerifier` and scopes; §7.1 covers binding and `allowed_hosts`. **Transport
   confidentiality is unaddressed** - see §2.4 item 4.
3. **Server ↔ Jobvite** - §4.1 covers credential handling thoroughly; the boundary itself is never
   named as one.
4. **Jobvite content ↔ the model** - this is the boundary §6.1 defends best in the whole document,
   and it is never called a trust boundary. It is the crossing where attacker-authored text
   (candidate résumés) enters a model's context.
5. **Server ↔ its own log stream** - §5.3 says *"the log stream is treated as sensitive"*, which is
   a boundary assertion with no stated control (noted in the B88 row of the companion report).

Boundary 4 is the interesting one: the design's strongest control guards a boundary the design
never names. That is precisely the coverage question the mandated table exists to make checkable.

### 2.4 The lightweight checklist, scored anyway

`:153-160`. Not available as a substitute (TM9), but a cheap cross-check - and item 4 finds
something new.

| # | Checklist item (verbatim, `:153-160`) | Verdict | Note |
|---|---|---|---|
| 1 | *"All inputs validated and sanitized"* | **PARTIAL** | Strong on shape (B9-B13, B27-B29). Gaps are the companion report's B25 (no control-character or encoding rejection) and B30 (no nesting/list/dict/body limits). |
| 2 | *"Authentication required for all non-public endpoints"* | **SATISFIED** | §7.2. stdio is unauthenticated **by design and with a stated rationale** - the OS is the boundary - which is the documented-decision form this item expects, not a breach. |
| 3 | *"Authorization checks enforce least privilege"* | **PARTIAL** | §7.2's three scopes ✓ inbound. B21's gap outbound: nothing scopes the Jobvite credential itself. |
| 4 | *"Sensitive data encrypted in transit and at rest"* | **PARTIAL - and this is a new finding** | **At rest: N/A and clean** - §1 holds no state. **In transit: unaddressed.** `grep -niE 'tls\|https\|ssl\|encrypt\|certificate'` over DESIGN.md returns **no substantive hit** - the only "TLS" is §10's incidental *"two TLS surfaces in one image"* about `httpx` vs `httpx2`. Outbound to Jobvite is fine in practice (`https://` URLs, and `httpx2` verifies by default), though unstated. **The real gap is inbound:** §7.1 binds `127.0.0.1` by default and sets `allowed_hosts`/`allowed_origins` when the bind is not loopback - but says **nothing about TLS on a non-loopback bind**. A server bound off-loopback carries a bearer token and candidate PII in plaintext. §7.1 already contemplates that deployment ("unless told otherwise") and addresses only host/origin validation, which is a different threat. |
| 5 | *"Rate limiting applied to public-facing endpoints"* | **SATISFIED** | §4.4, with four execution-established constraints. |
| 6 | *"Audit logging captures security-relevant actions"* | **PARTIAL** | §5.3 is strong; B17's gap is that the **approval decision** - the most security-relevant fact the server produces - is not among the logged fields. |
| 7 | *"Error messages do not leak internal details"* | **SATISFIED** | §5.3, `mask_error_details=True` set explicitly against a framework default of `False`. |
| 8 | *"Dependencies checked for known vulnerabilities"* | **SATISFIED** | §10 `pip-audit`, CodeQL. B72's suppression-policy gap is downstream of this, not a failure of it. |

---

## 3. What the threat model would most likely surface

**[REASONED] throughout this section.** Offered so the gap is actionable rather than merely
recorded, and explicitly *not* a substitute for the design team doing TM2 properly. I am naming
where I expect a STRIDE pass to find something the current design does not already handle.

- **Information Disclosure - the cache.** §5 below. Highest expected yield.
- **Information Disclosure - plaintext HTTP on a non-loopback bind.** §2.4 item 4.
- **Repudiation - the approval decision is not logged.** B17. This is the STRIDE category the
  design engages least; §7.5 is careful about what may be *claimed* about approval and does not
  make the claim *recoverable* after the fact. Repudiation is exactly the category that catches
  "we cannot prove who authorised this write".
- **Denial of Service - the config-reload quota amnesty.** §4.4 states it plainly: *"only
  `limiters.clear()` applies new values, **and that resets every client's quota**, making a config
  reload a quota amnesty and repeated reloads a trivial bypass."* That is a rated-risk candidate
  stated as an implementation note, with no likelihood, impact, or mitigation decision attached.
- **Denial of Service - the abandoned-approval hang.** §7.5: an abandoned elicitation hangs the
  call and *"a client-side timeout does not bound it"*. Currently disclosed to integrators via the
  README rather than rated or mitigated.
- **Elevation of Privilege - `require_scopes` failure mode.** §7.2 notes an unauthorised tool
  vanishes from `tools/list` and a direct call returns "Unknown tool". Good behaviour; worth
  confirming under STRIDE that "unknown tool" is genuinely indistinguishable from a
  non-existent tool and does not leak scope topology across tokens.

---

## 4. `architecture/data-flow.md` - NOT-APPLICABLE (right answer, wrong reason)

### 4.1 Verdict

`applicable_to: [system-design]`, `priority: required`, 676 lines. **NOT-APPLICABLE**, and I am
confident having now read it, which STANDARDS.md was not.

`:24` - *"This document defines the complete data flow from user interaction through frontend,
server actions, backend API, to database operations and back."*

`:30-31` - *"**Mutations (writes) MUST go through server actions.** No direct database access from
client components. No mutation calls to the backend API made directly from client-side code."*

Every substantive section presupposes at least one thing this project does not have. Its four
lifecycle layers are *"User Interaction Layer"* (React client components), *"Server Action Layer"*,
*"Backend API Layer"* (FastAPI routers), *"Database Layer"* (`app/crud/`). Its remaining sections
are Zustand, TanStack Query, WebSocket, file upload, batch operations, optimistic updates with
rollback, and Suspense streaming. **This server has no frontend, no server actions, no database,
and no client.**

The "Derived Data and Source of Truth" section (`:237-299`) is the one part written
stack-independently, and it does not reach either. `:241-243` - *"One store holds **authoritative
state** (the system of record, SoR). Every other representation … is a **derived projection**."*
DESIGN.md §1: *"It is not an SDK, a sync engine, or a cache. It holds no state between calls beyond
an HTTP connection pool, a rate-limiter bucket, and short-lived confirmation tokens."* No SoR, no
projections, nothing to rebuild or reconcile. Jobvite is the system of record and this server is
not a projection of it - it is a pass-through.

### 4.2 Residues, all already covered

Three DON'Ts at `:660-662` are stack-independent in wording:

- `:660` *"Skip validation at any layer"* → already B9-B13, B27-B31.
- `:661` *"Ignore error cases"* → already B1-B7.
- `:662` *"Use synchronous operations for I/O"* → **not** covered by any B-number. DESIGN.md never
  states that the Jobvite client is async, though `httpx2` + FastMCP make it so in practice. Too
  thin to raise as a finding; recorded so the dismissal is complete rather than silent.

### 4.3 Why the right answer still matters here

STANDARDS.md dismissed this file as a *"process/design-artifact standard rather than a code
obligation"*. **That characterisation is factually wrong.** `data-flow.md` is not a process
standard at all - it is a stack-specific *implementation* standard, 676 lines of TypeScript and
Python. The correct dismissal is one line: *"Next.js/Server-Actions/Postgres request lifecycle; no
frontend, no database."*

This matters because the wrong reason was **reused**. `data-flow.md` and `threat-modeling.md` were
dismissed in a single table row, on a shared rationale, without either being opened. On
`data-flow.md` the rationale produced a correct verdict by luck. On `threat-modeling.md` - an
actual process standard, and therefore one whose subject is precisely the design artifact under
review - the same rationale produced the opposite of the correct verdict. **A process standard is
the *most* binding kind of standard on a design document, not the least.**

---

## 5. NEW FINDING - `architecture/caching.md` went live and nobody noticed

**This is the highest-consequence item in this report.**

### 5.1 The condition tripped

`architecture/caching.md` is `priority: required`, `applicable_to: [system-design]`, 859 lines.
STANDARDS.md §3 dismissed it conditionally:

> *"Redis response caching for a DB-backed API. Optional here; **if a cache is added it becomes
> live**."*

**DESIGN.md §7.7 adds a cache.** Verbatim: *"Adopted, each constructed with explicit arguments:
`ResponseCaching` (never on preview), `Timing`, `StructuredLogging` with `include_payloads=False`,
`RateLimiting` with `get_client_id`."*

The design changed between STANDARDS.md's conditional dismissal and revision 2. Nothing re-checked
the condition. **No B-number covers caching, because at the time the B-list was written there was
no cache.**

### 5.2 The clause that now binds

`architecture/caching.md:841`, under **"### Don'ts"**:

> *"❌ Cache user-specific data without proper namespacing"*

and `:833`, under **"### Do's"**:

> *"✅ Namespace cache keys by tenant/user when needed"*

### 5.3 Why this is dangerous here specifically

Three facts from DESIGN.md, each stated by the design itself:

1. **The cached responses are candidate PII.** §2's tool table classifies `search_candidates`,
   `get_candidate` and `create_candidate` as `candidate PII`.
2. **Different callers are meant to see different data.** §7.2 builds three scopes on three data
   classes precisely so a token limited to public job data cannot reach candidate PII.
3. **This framework's sibling middleware defaults to a single shared key, and the design measured
   it.** §4.4, verbatim: *"**`get_client_id` is mandatory.** The default keys every caller to the
   literal string `"global"` despite the docstring implying per-client. One noisy integrator would
   throttle everyone."*

§7.7 specifies exactly one constraint on `ResponseCaching` - *"never on preview"* - and §7.6
explains why (a cached preview re-issues a spent token). **The design reasoned carefully about
`ResponseCaching`'s interaction with the confirmation-token path and not about its interaction with
the PII-and-scopes path.**

**[REASONED]** If `ResponseCachingMiddleware` derives its cache key without client identity - as
`RateLimitingMiddleware` demonstrably does, per §4.4's measurement - then a `search_candidates`
response cached for a candidate-PII-scoped token can be served to a token that holds only the
public-job-data scope. That is a cross-scope PII disclosure that defeats §7.2's entire authorisation
model, through a middleware adopted in one clause of §7.7.

**I have not verified FastMCP's `ResponseCachingMiddleware` key derivation.** No code exists and I
will not assert its behaviour. What I assert is narrower and sufficient: **the design does not say,
the standard requires it to say, and the design's own measured evidence about a sibling middleware
makes the unsafe default the one to expect.**

The design already stated the rule that decides this, in §7.7: *"**Design rule, earned rather than
assumed: on this framework a middleware's default is not a safe starting point.** Four of the eight
exercised were unusable or needed their defaults overridden."* `ResponseCaching`'s key derivation
was not exercised against that rule.

### 5.4 What is owed

- Establish `ResponseCachingMiddleware`'s cache-key derivation **by execution**, as §4.4 did for
  `RateLimitingMiddleware`. That is the standard of evidence this document set for itself.
- If identity is not in the key: namespace it per `caching.md:833`, or do not cache PII-bearing
  tools at all.
- A required test: two tokens with different scopes, the second must not receive the first's cached
  candidate result. This belongs in §8's required-case list beside the fence-closing case.
- **[REASONED]** Given §7.6's finding that caching already breaks the preview tool, and that the
  only stated benefit is latency on an upstream nobody has ever successfully called (§1.1), the
  lazy and defensible option is to drop `ResponseCaching` from the adopted set until there is a
  measured reason to want it. Removing it deletes this entire finding and the §7.6 hazard together.

Two lesser clauses, recorded for completeness: `:843` *"❌ Store large objects (> 1MB) in Redis"*
(interacts with B15's result cap) and `:837` *"✅ Handle cache failures gracefully"*.

---

## 6. Was the dismissal a pattern? Yes - here is its shape

### 6.1 The method STANDARDS.md actually used

Stated at its own §"Method and authority note": *"Applicability here is decided by each file's own
`applicable_to` frontmatter and its Scope section."* **That is the correct method.** The finding is
that it was not the method actually applied to the dismissal table.

**Evidence it was not applied:** `threat-modeling.md` is `applicable_to: [all]`. Had the frontmatter
been read, the file could not have been dismissed - `all` admits no stack-based exclusion. It was
dismissed anyway, in a table row it shares with `data-flow.md`, on a rationale about document
*genre*. STANDARDS.md also states plainly that it did not read it: *"Not read in full; both are
process/design-artifact standards rather than code obligations."*

**[REASONED]** The operative method for the §3 dismissal table was therefore **inference of scope
from title and domain**, not inspection of `applicable_to`. That heuristic is fast and mostly right
- it correctly dismissed nine `database/*` files, eleven other-language files, and the frontend
tree, and I re-verified a sample of those and agree with every one. It fails in one predictable
direction: **a document whose subject matter reads as stack-specific or process-y, but whose scope
declaration says `all`.** `threat-modeling.md` is exactly that document, and it is the security one.

### 6.2 The audit

I enumerated every `priority: required` file in the standards tree (excluding the opt-in `azure/`
and `snowflake/` domains, which are correctly out of force) and cross-checked each against whether
STANDARDS.md mentions it anywhere.

- **124** `priority: required` files in scope.
- **41** are never mentioned in STANDARDS.md by path, filename, or glob.

41 sounds alarming and mostly is not: it is `frontend/*` (14 files), `database/*` (5), backend
other-stack and document-generation files, and `documentation/*` client-deliverable templates. All
are dismissible on stack grounds and I agree with each.

**The discriminating test is `applicable_to`.** Only **10** required files declare `all`:

| File | `applicable_to` | Mentioned in STANDARDS.md? | Assessment |
|---|---|---|---|
| `documentation/readme-standard.md` | `all` | yes | B77-B82, B89, B103-B105 ✓ |
| `documentation/changelog-standard.md` | `all` | yes | B83-B87 ✓ |
| `documentation/api-reference-standard.md` | `all` | yes | cited in §5 ✓ |
| `architecture/gdpr-data-rights.md` | `system-design`, `all` | yes | read in full, correctly reduced to B88 ✓ |
| `devops/infrastructure-as-code.md` | `terraform`, `aws`, `ecs`, `all` | yes | cited at B106 ✓ |
| `devops/backup-disaster-recovery.md` | `postgres`, `redis`, `all` | yes | dismissed, reason given ✓ |
| **`architecture/threat-modeling.md`** | **`all`** | **dismissed UNREAD** | **§2 - the finding** |
| `documentation/onboarding-standard.md` | `all` | yes, via glob at STANDARDS.md:688 | dismissed as a client-engagement template. I agree. |
| **`devops/deployment-strategy.md`** | **`all`** | **never mentioned at all** | See §6.3 |
| **`devops/post-mortem-template.md`** | **`all`** | **never mentioned at all** | See §6.3 |

**So the pattern is bounded, and that is the useful result.** Of ten universally-scoped required
standards, seven were handled correctly, one (`threat-modeling.md`) was dismissed unread and binds,
and two were never considered at all. **Nine of ten holes the heuristic could have produced, it did
not produce.** The one it did produce is the security standard.

### 6.3 The two never-considered files - both genuinely N/A, neither ever dismissed

I read both. Neither binds, but neither was ever *stated* not to bind, and silent omission is what
this exercise exists to catch.

**`devops/deployment-strategy.md`** - `applicable_to: [all]`, `priority: required`.
`:24` - *"Define how production application deployments and database schema migrations are rolled
out… This standard governs *how* changes reach production"*. Scope at `:28-31` is *"Production
application deployment (services, frontends, workers)"*, *"Database schema migrations"*, and
*"Rollback policy"*. **NOT-APPLICABLE:** no production deployment target (the brief excludes ECS;
§10 defines a repository and a package, not a deployed service), and no database. **[REASONED]**
Becomes live if this is ever hosted as a service rather than run as a subprocess.

**`devops/post-mortem-template.md`** - `applicable_to: [all]`, `priority: required`.
`:22` - *"Every SEV-1 or SEV-2 incident MUST produce a post-mortem document within 5 business days
of resolution."* **NOT-APPLICABLE** on the same ground STANDARDS.md used, correctly, for
`monitoring-alerting.md` and `backup-disaster-recovery.md`: it presumes owned running
infrastructure with an incident severity scheme and an on-call rotation. There is no running
service and no SEV taxonomy. **Consistent with the existing dismissals - it simply never got one.**

### 6.4 The one conditional dismissal that expired

`caching.md` is a different failure from `threat-modeling.md` and worth separating. It was **read
correctly, dismissed correctly, and dismissed *conditionally*** - *"if a cache is added it becomes
live"*. The design then added a cache. **Nothing re-evaluates a conditional dismissal when the
condition changes.**

**[REASONED]** STANDARDS.md contains at least two other conditional dismissals with live triggers:
`devops/docker.md` (*"Applies only if a container image ships"* - and §7.4's SIGTERM finding is
entirely about container shutdown, which suggests someone expects one) and `backend/idempotency.md`.
A conditional dismissal is a **dated** claim about the design. Every one should be re-tested at
freeze rather than at the next review that happens to notice. That is a cheap, mechanical check and
it would have caught the caching finding.

---

## 7. What I could NOT verify

1. **`ResponseCachingMiddleware`'s actual cache-key derivation.** The core of §5. No code exists,
   and I will not assert framework behaviour I have not executed - which is the standard §4.4 set
   when it *measured* the sibling middleware rather than trusting its docstring. §5 is stated as a
   question the design must answer, with the evidence for expecting the unsafe default, not as a
   confirmed vulnerability. **Resolving it needs a spike, not a reviewer.**

2. **Whether a threat model exists outside `docs/`.** I checked DESIGN.md and the `docs/` tree. If
   one was authored elsewhere, TM1/TM6 change verdict - though `:144`'s requirement is that the
   *spec* contain the section, so a threat model living apart from DESIGN.md would still be
   non-conforming in placement.

3. **`patterns/` and `examples/`.** Out of scope - `README.md:14` marks `patterns/` Recommended and
   `:16` marks `examples/` Optional, so neither binds. I did not read them and no obligation should
   be derived from them.

4. **The 41 never-mentioned required files, individually.** I read the frontmatter of all 124 and
   the full text of five (`threat-modeling.md`, `data-flow.md`, `caching.md`,
   `deployment-strategy.md`, `post-mortem-template.md`). For the remaining 36 I relied on
   `applicable_to` plus path, which is the same class of inference whose failure mode this report
   documents - though applied to the frontmatter field STANDARDS.md skipped, which is the field
   that discriminates. **[REASONED]** Residual risk is low: none of the 36 declares `all`, so none
   can bind a Python MCP server on a scope basis. It is not zero. A file could declare a narrow
   `applicable_to` and still contain a universally-scoped clause in its body, exactly as
   `caching.md` (`system-design`) contains one that now binds.

5. **Whether the `evolv-coder-standards` tree changed under me.** Read once, at one moment. All
   `file:line` citations here were resolved during this task.
