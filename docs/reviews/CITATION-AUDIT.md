# CITATION-AUDIT - every standards-repo citation in DESIGN.md and docs/adr/ resolved

Auditor: `spike-auditor`. Date: 2026-08-27. Follow-up to task #28 / `SPIKE-CLAIM-AUDIT.md`.

**Scope.** Every `file:line` citation in `docs/DESIGN.md` and `docs/adr/*.md` that points at
`evolv-coder-standards`, plus the two `JOBVITE-API.md` coordinates, resolved against
`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/`.

**32 citation instances across 22 distinct coordinates. All 32 resolve. Zero fabrications.**

**Method.** Every line number in this report was taken from `grep -n` on a distinctive phrase or
from `awk` printing explicit `NR` prefixes. No number was counted inside a `sed` window. Because
`DESIGN.md` is being edited concurrently, each finding is anchored by **quoted phrase first** and
line number second, so it survives the file moving under it.

## Three verdicts, kept separate because they need different fixes

| Verdict | Meaning | Count |
|---|---|---|
| **EXACT** | Coordinate resolves, quoted text is at that line, clause supports the citing sentence | 29 |
| **COORDINATE** | Number wrong, clause exists elsewhere in the file - cheap fix | 0 |
| **MISDIRECTED** | Coordinate resolves, but the clause at it does not carry what the sentence attributes to it, while a clause that does exists elsewhere in the same file | 1 |
| **SUBSTANTIVE** | Coordinate resolves and the clause is real, but it does not support the sentence at the strength claimed - the dangerous one, because both halves look right in isolation | 2 |
| **FABRICATION** | Quoted text exists nowhere in the cited file | **0** |
| **UNRESOLVABLE** | Could not be checked at all | **0** |

**Headline.** The corpus is in far better shape than the three-rounds-of-miscitation history
predicted. **Nothing is fabricated and nothing is unresolvable.** The two SUBSTANTIVE findings are
both the O-5 shape - a real clause cited for more than it says - and one of them **is O-5, still
live after FIX-3 fixed its coordinate.** That is the single most useful result here and it is
exactly why these verdicts are kept apart: the cheap half of O-5 was fixed and the dangerous half
was not.

---

# Findings, ranked

## C-1 (highest) - O-5's coordinate was fixed; O-5's substantive error survives, and the document now contradicts itself

FIX-3 corrected the coordinate I reported in `SPIKE-CLAIM-AUDIT.md` (**O-5**): the citation moved
from `JOBVITE-API.md:401` (a blank line) to `:399`. **The clause now resolves. The sentence citing
it is still wrong**, and the same document now says the right thing in one place and the wrong thing
in another, both citing `:399`.

**What `JOBVITE-API.md:399` actually says** (`grep -n "start=0\` is accepted"`):

> *"**`start=0` is accepted and returns records**, rather than erroring. That falsifies the "1-based
> and strict" hypothesis, **though it still does not distinguish "0-based" from "1-based with
> clamping"** - see the contract document's pagination section."*

**The correct reading, now in DESIGN's front matter** (currently L36-38, phrase *"whose one
load-bearing property"*):

> *"...base-agnostic paging, whose one load-bearing property, **that `start=0` is accepted and
> returns records**, is observed in the one genuine `200` (`JOBVITE-API.md:399`)."*

That is precisely right. It cites `:399` for the thing `:399` establishes.

**The overstatement, still live in §4.5** (currently L303-306, phrase *"which is the strongest
citation available for this paragraph"*):

> *"a 1-based server **clamps 0 to 1** - **confirmed** against the one genuine Jobvite `200` in our
> evidence (`JOBVITE-API.md:399`), which is the strongest citation available for this paragraph and
> was previously unused and returns the same first page it would have anyway"*

`:399` says in its own sentence that it **does not distinguish** clamping from 0-based. It cannot
confirm clamping. Two sentences in one document, same citation, opposite strengths.

`[REASONED]` The decision is unaffected and correct either way - starting every scan at `start=0` is
safe on both bases, which is the whole point of base-agnostic paging. Only the word **"confirmed"**
attached to the clamping *mechanism* is wrong. The front matter already contains the sentence that
should replace it.

**Also still present:** the garbled clause I flagged in the first audit - *"and was previously unused
and returns the same first page it would have anyway"* - which reads as two edits collided. Worth
fixing in the same pass.

**Verdict: SUBSTANTIVE.** Fix: restate §4.5's sentence to claim what the front matter claims.

## C-2 - `architecture/caching.md:833` is cited as a requirement; it is a checklist tick that says "when needed", and the real clause is 205 lines earlier

**DESIGN** (currently L716-717, phrase *"requires cache keys namespaced by"*):

> *"`architecture/caching.md:833` **requires** cache keys namespaced by tenant or user and `:841`
> names un-namespaced user-specific caching as a Don't."*

**What is at `:833`** (`grep -n -i namespac architecture/caching.md`):

```
833| ✅ Namespace cache keys by tenant/user when needed
```

It is a bullet in a **`### Do's`** checklist (heading at `:830`), and it is qualified **"when
needed"**. That is advisory, not a requirement. The design's word is "requires".

**The `:841` half is EXACT:**

```
841| ❌ Cache user-specific data without proper namespacing
```

A `Don'ts` entry (heading at `:839`) is genuinely prohibitive, and it carries the design's argument
on its own.

**And there is a stronger clause the design does not cite.** `caching.md` has a dedicated section:

```
628| ### Cache Key Namespacing
631| # Namespace pattern for multi-tenant apps
```

`[REASONED]` This is the same shape as O-5 in miniature: the sentence is *right*, the conclusion
(do not adopt `ResponseCachingMiddleware`) is *right* and is independently carried by `:841` plus
the design's own §7.2 scope argument - but the strongest available clause sits unused at `:628`
while a "when needed" tick is upgraded to "requires". The fix is to cite `:628` for the requirement
and keep `:841` for the prohibition, or to soften "requires" to match what `:833` says.

**Verdict: SUBSTANTIVE** (strength), plus an under-citation.

## C-3 - ADR-0002 attributes a rationale to `rate-limiting.md:355-356`, which contains no rationale; the rationale is real and lives at `:94-97`

**ADR-0002** (`docs/adr/0002-in-process-rate-limiting.md:7-9`):

> *"`backend/rate-limiting.md:355-356` mandates a Redis token bucket on every public-facing surface
> and forbids in-memory limiting, requiring an ADR to opt out. **Its stated rationale is
> desynchronisation across replicas.**"*

**What is actually at `:355-356`:**

```
355| 1. **Every public endpoint is rate-limited.** Opt-out requires an ADR.
356| 2. **Token bucket via Redis.** No in-memory limiters in production.
```

Two terse rules in a `## Rules` block. **They carry no rationale of any kind.** The mandate and the
prohibition are supported; the *"stated rationale"* is not at this coordinate.

**The rationale is real, and it is stronger than the ADR's paraphrase** (`grep -n -i
"desync\|replica" backend/rate-limiting.md`):

```
94| Redis is the required backing store. In-memory limiters (`@cachetools`,
96| they desynchronize across replicas — a 4-replica deployment with
97| in-memory limits gives each client 4× the intended quota.
```

**Why this one matters more than a coordinate slip.** ADR-0002's entire argument is *"the rationale
is replica desynchronisation; a single-process server has no replicas; therefore the rule's purpose
is not defeated"*. That argument stands or falls on the rationale being what the ADR says it is -
and it **is**, at `:94-97`. The ADR is right and cites the wrong lines for the load-bearing half.

`[REASONED]` `:96-97` is also a better citation than the ADR realises, because it independently
corroborates **DESIGN §1's** single-process warning - *"each worker gets its own buckets, so the
effective limit multiplies by the worker count"* - which is the standard's own `4×` example
generalised. Same finding, arrived at twice, and the standard's version is currently uncited.

One further nuance worth a word: `:355`'s *"Opt-out requires an ADR"* is about opting out of
**rate-limiting**, not about opting out of **Redis**. The ADR's *"requiring an ADR to opt out"*
elides the two. `[REASONED]` Harmless in effect - an ADR exists either way - but the standard does
not literally say what the ADR implies it says.

**Verdict: MISDIRECTED.** Fix: cite `:94-97` for the rationale, keep `:355-356` for the mandate.

## C-4 - the clause the whole write design answers is never cited in DESIGN.md

Reported as an absence, per the reporting instruction.

`grep -n "agent-guardrails" docs/DESIGN.md` returns **five** citations: `:47-49`, `:40`,
`:121-123`, `:122`, `:79`. **`ai/agent-guardrails.md:70` is not among them.**

That clause is the human-in-the-loop mandate:

```
68| ## Human-in-the-loop (HITL) gates
70| - **Default-deny destructive operations.** Any irreversible or
71|   high-blast-radius action (delete, financial transaction, outbound message
72|   to a third party, infra change, mass update) MUST pause for human
73|   approval before execution. Fail closed: no approver, no action.
```

**It is cited everywhere else in this repository** - `STANDARDS.md:189`, `FASTMCP-SPIKE-4.md:1189`
(*"This section exists because `ai/agent-guardrails.md:70`"*) and `:1462`, `CONFORMANCE-B1-B106.md:151`
(B18), and `DESIGN-R1.md:798-800`. Four documents, including the conformance sweep that marked B18
**SATISFIED** against it and the spike section that exists because of it.

`[REASONED]` DESIGN §2.2's two gates, §7.5's entire approval mechanism, and §7.6's reason for cutting
the token are all answers to this one clause. It is the *reason the write path is shaped the way it
is*, and the design never names it. This is not a wrong citation - it is a missing one, and it is
the strongest normative anchor available for the most contested section of the document. The
"outbound message to a third party" wording is also a direct hit on §7.5's email-to-the-candidate
argument, which currently rests on the design's own reasoning.

**Verdict: absence, first-class.** Fix: cite `:70-73` in §2.2 where the two gates are introduced.

---

# Everything that checked out

Recorded in full, because "I checked these and they are fine" is a result and the next reviewer
should not repeat the work. All **EXACT**: coordinate resolves, quoted text is at that line, and the
clause supports the citing sentence at the strength claimed.

## DESIGN.md

| Citation | Standard's text at that line | Citing sentence's claim | ✓ |
|---|---|---|---|
| `ai/agent-guardrails.md:47-49` | *"**Minimal tool set.** Bind to an agent only the tools its task requires. Do not expose a broad "kitchen-sink" toolbox; **an unused tool is attack surface.** The callable-tool list is an explicit allow-list per agent."* | *"requires a minimal allow-list because an unused tool is attack surface"* | EXACT, phrase-for-phrase |
| `ai/tool-calling.md:54` | *"Loose types (bare `string`, `object`) are **attack surface**."* | *"uses the same phrase about loose parameter types, which is a different obligation"* | EXACT - and the design is right that it is a *different* obligation sharing a phrase |
| `ai/agent-guardrails.md:40` | *"Mandatory audit logging of every tool invocation"* | *"mandates audit logging of every tool invocation"* | EXACT |
| `ai/tool-calling.md:171-173` | *"**Log every tool invocation** - tool name, validated arguments (PII redacted), result status, latency, and the request correlation id."* | *"names the fields: tool name, validated arguments with PII redacted, result status, latency, correlation id"* | EXACT, field for field |
| `agent-guardrails.md:121-123` | *"**Log every tool invocation** with: tool name, validated arguments (PII redacted), result status, latency, **the approval decision if gated**, and the request correlation id."* | *"names it [`approval_state`] explicitly"* | EXACT - *"the approval decision if gated"* is at `:122`, inside the cited range |
| `agent-guardrails.md:122` (§11 C4-R1) | as above, `:122` is the *"the approval decision if gated"* line | *"requires it (B17)"* | EXACT - the tighter single-line cite is correct |
| `agent-guardrails.md:79` (§5.3, §11, §13) | *"Record **who** approved **what** and **when** in the audit log."* | *"also requires recording **who** approved"* | EXACT |
| `error-contract.md:44` | *"All error responses MUST use the media type:"* | *"requires the media type `application/problem+json` on all error responses"* | EXACT. The requirement sentence is at `:44`; the literal `Content-Type: application/problem+json` is in the fenced block at `:47`. Citing the requirement rather than the code fence is the right choice |
| `rate-limiting.md:361-362` (§5.1, §13) | *"**429 uses ProblemDetail.** Raise `RateLimitException`, not `HTTPException(status_code=429)`."* | *"separately requires a 429 to use a problem detail"* | EXACT |
| `rate-limiting.md` "rule 5" (§13, ADR-0002 scope) | `:359-360` *"**Headers on every response.** `RateLimit-*` (and the `X-` aliases) on success and 429; `Retry-After` on 429 only."* | *"rule 5's `RateLimit-*` response headers"* | EXACT - it is rule 5, and it is the `RateLimit-*` headers |
| `architecture/gdpr-data-rights.md:9` | `priority: required` | *"reads `priority: required`"* | EXACT, and the design is right that the earlier `optional` claim was false |
| `architecture/caching.md:841` | *"❌ Cache user-specific data without proper namespacing"* | *"names un-namespaced user-specific caching as a Don't"* | EXACT (the `:833` half is **C-2**) |
| `readme-standard.md:67` | *"**Quickstart parity**: the Quickstart commands MUST be exercised by CI on every merge to the default branch."* | *"requires the Quickstart commands to be exercised by CI on every merge"* | EXACT |
| `readme-standard.md:70` | *"**Badges are live**: each badge MUST point at a live source. Static SVGs that no longer reflect reality are forbidden."* | *"`:70` forbids a static badge that does not reflect reality"* | EXACT |
| `readme-standard.md:83` | *"Quickstart steps that require credentials, VPN access, or undocumented prerequisites."* | quoted verbatim, *"under Anti-patterns"* | EXACT - `## Anti-patterns` heading is at `:74`, so `:83` is inside it |
| `readme-standard.md` "fourteen sections" | `:43` *"Every README MUST contain the following sections, **in this order**. Section headings must match exactly so that automated checks can locate them."* then items 1-14 at `:45-58` | *"mandates fourteen README sections in a fixed order"*; *"headings matching exactly, because automated checks locate them by heading text"* | EXACT - counted the numbered items: exactly 14, Title through Maintainers |
| `input-validation.md:223-226` | four table rows: *Max nesting depth 5 levels* / *Max list items 1,000* / *Max dict keys 100* / *Max total request body size 1 MiB* | *"the **four** limits from `input-validation.md:223-226`"* | EXACT - four rows, and four is the right count |
| `backend/resilience.md:224-226` | *"Log every **retry attempt** (at `WARNING`) and every **breaker state transition** (`closed`→`open`→`half-open`), each carrying the `request_id` correlation field. Never retry or trip silently."* | *"requires both, each carrying the `request_id` correlation field (B39)"* | EXACT - "both" is right, and the correlation-field clause is really there |
| `threat-modeling.md:86-88` | *"**Critical/High**: Must mitigate before implementation proceeds / **Medium**: Mitigate before production release / **Low**: Accept with documented rationale"* | §11 *"Threshold disposition"* | EXACT |
| `JOBVITE-API.md:397` | *"**A success body DOES carry a `status` block.** ... **This closes the open question**"* | *"The one genuine `200` answers it"* | EXACT. **Note:** this citation is new since my first audit - it is FIX-3's correction of **S-2**, and it is correct |
| `JOBVITE-API.md:399` (front matter, L36-38) | *"`start=0` is accepted and returns records"* | *"whose one load-bearing property, that `start=0` is accepted and returns records, is observed"* | EXACT (the §4.5 use of the same line is **C-1**) |

## docs/adr/

| ADR | Citation | Standard's text | ✓ |
|---|---|---|---|
| 0002 | `backend/rate-limiting.md:355-356` | *"Every public endpoint is rate-limited. Opt-out requires an ADR."* / *"Token bucket via Redis. No in-memory limiters in production."* | Mandate EXACT; the **rationale** attached to it is **C-3** |
| 0003 | `architecture/error-contract.md:44` | *"All error responses MUST use the media type:"* | EXACT |
| 0003 | `error-contract.md:83` | *"\| `instance` \| string \| yes \| URI of the request that generated the error \|"* | EXACT - the ADR says *"defines it as the URI of the request that generated the error"*, verbatim |
| 0005 | `ai/README.md:22-33` | *"This domain defines standards for **application LLM engineering** - product code that *calls* foundation models."* plus the In/Out scope bullets | EXACT - the ADR's *"scopes the domain to product code that **calls** foundation models"* is the clause's own wording |
| 0006 | `devops/development-workflow.md:48-83` | `:49-50` the `main` / `develop` tree, `:58-68` branch naming, `:70-83` protection rules for **main branch** and **develop branch** | EXACT - a generous range, but every line in it is branch strategy and the two-branch mandate is carried across it |
| 0008 | `architecture/gdpr-data-rights.md:9` | `priority: required` | EXACT |
| 0009 | `ai/agent-guardrails.md:79` | *"Record *who* approved *what* and *when* in the audit log."* | EXACT - and the ADR's scoping (approver identity only, caller identity still recorded) is a correct reading |
| 0010 | `backend/testing.md:583-589` | the coverage table: Overall 80%, Services 90%, API Routes 85%, **Utilities 95%**, Models 70% | EXACT - all four figures the ADR quotes are in the cited range, and DESIGN §8's *"95% on `utils/` - the standard's own Utilities target"* matches `:588` |
| README | `threat-modeling.md:146` | *"4. Mitigations become functional requirements (FR-XXX) in the spec"* | EXACT |
| README | `development-workflow.md:166` | *"│   [FE-001] Add user dashboard component                         │"* | EXACT - the ADR README says it *"expects layer-prefixed `[FE-001]`"*, and that is the PR-title-format example at that line |

---

# What this changes about the miscitation history

`[REASONED]` The premise I was given - that this defect has appeared in the design, in a review of
the design, and in a research file - is true, and I found a fourth instance myself (O-5). But the
shape of the problem is narrower than "citations on this project are unreliable":

- **Coordinates are sound.** 32 instances, zero fabrications, zero unresolvable, and after FIX-3,
  zero wrong numbers. The one number-level defect in this audit (**C-3**) points at a real clause in
  the right file and misplaces only the rationale.
- **The surviving defect class is strength, not location.** Both SUBSTANTIVE findings (**C-1**,
  **C-2**) resolve cleanly and quote real text. Both fail on what the clause *supports*. That is
  invisible to any check that only resolves coordinates - including the check I would have written
  if the instruction had not separated the verdicts.
- **The recurring companion is under-citation.** Three of the four findings involve a *stronger
  clause sitting uncited in the same corpus*: `caching.md:628`, `rate-limiting.md:94-97`,
  `agent-guardrails.md:70-73`. That is the same pattern rounds 3 and 4 found at the document level
  and that I found at `JOBVITE-API.md:399` - **the design consistently under-uses its own
  evidence**, and then over-reads the weaker citation it did use to make up the difference.

`[REASONED]` If one habit is worth adopting from this, it is not "check the line number". It is
**quote the clause into the sentence that cites it.** C-1, C-2 and C-3 would all have been
self-evident at authoring time if the clause's own words sat next to the claim - `:833`'s "when
needed" would not survive being quoted beside the word "requires".

# What I did NOT check

- **Non-`file:line` standards references.** `documentation/readme-standard.md`, `ai/tool-calling.md`
  and `ai/agent-guardrails.md` are also named without coordinates in several places. Those cannot be
  wrong in the coordinate sense, but they can be wrong in the C-2 sense. Not audited.
- **`docs/research/STANDARDS.md` and `docs/reviews/CONFORMANCE-B1-B106.md`.** B1-B106 in particular
  carries a large number of standards quotations and was the source of several design citations.
  It is the obvious next target, and it is the document that would propagate an error furthest.
- **Whether the standards clauses are themselves correct or current.** Out of scope; I checked that
  DESIGN quotes them faithfully, not that they are good rules.
- **`git log` on the standards repo.** If a cited file has changed since the design quoted it, a
  coordinate could have been right when written and drifted. Every coordinate resolves *today*, so
  this is not currently masking anything.
