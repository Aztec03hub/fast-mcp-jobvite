# DESIGN.md - Adversarial review, round 2

Target: `docs/DESIGN.md`, revision 2 (last updated 2026-08-27 03:15 PM CDT).
Reviewer: one agent, both lenses, fresh context. Round written 2026-08-27 03:28 PM CDT.
Predecessor: `docs/reviews/DESIGN-R1.md` (`0c / 2h / 1m`).

---

## What I actually read

**Read in full:** `docs/DESIGN.md` (rev 2, all 12 sections); `docs/reviews/DESIGN-R1.md`
RED/BLUE/RED/BLUE plus its decision table, surviving count and its "What I did NOT review"
section.

**Read in full or near-full:** `docs/research/FASTMCP-SPIKE-4.md` §§1.3, 6, 12.1, 13-15, 17,
19 and its closing "What I could NOT verify"; `docs/research/JOBVITE-API.md` §§6.1, 7.1-7.3,
13-15, 20; `standards/ai/agent-guardrails.md` (Scope, Least privilege, HITL, Audit logging);
`standards/ai/tool-calling.md:165-180`; `standards/architecture/error-contract.md:1-50`;
`standards/architecture/gdpr-data-rights.md` (frontmatter, Purpose, Scope, Data classification,
Records of processing, Anti-patterns, Citations, Acceptance); `standards/ai/resilience.md`
§§"Idempotency on retry", "Surfacing failures"; `standards/ai/llm-observability.md` Scope +
"Tracing is mandatory"; frontmatter of thirteen standards files.

**Looked for and could not find:** nothing cited in the brief is missing. All six research
documents named in the brief exist at the given paths. `docs/DECISIONS.md` exists (D1-D17); I
read its headings and the entries the design cross-references, not the whole file.

**Deliberately not duplicated:** the systematic B1-B106 conformance sweep. Where a standards
obligation surfaced in passing inside a section I was already attacking, I report it; I did not
sweep `STANDARDS.md` or `COMPLIANCE-SPEC.md` for more.

**Standing rule applied:** `fast-mcp-jira` carries no authority. Revision 2 does not lean on it
anywhere I could find - the phrase and the repo name do not appear in the document at all. That
is an improvement over the drafts R1 reviewed and it is worth recording as a positive.

---

# RED ROUND - Adversarial review

## The four that matter most

1. **§4.5's probe reaches the wrong conclusion in one of its two branches**, and the branch it
   gets wrong is the one that silently corrupts every page after the first. (C1)
2. **§6.2 states a fact about the standards corpus that is false and checkable.**
   `architecture/gdpr-data-rights.md:9` reads `priority: required`. ADR-0008 is built on the
   opposite. (C3)
3. **§10's headline dependency-drift control is not in §10's own verbatim packaging block.** The
   prose says `mcp` is pinned; the block presented as load-bearing pins two other packages and
   not `mcp`. (C4)
4. **§7.5's era discriminator cannot discriminate**, and the one thing that would settle it needs
   no credential and has not been run. (M2)

---

## CRITICAL

### C1 - §4.5's "identical ids" branch draws the wrong conclusion, and it is the dangerous branch. [DEALBREAKER if shipped as written]

`DESIGN.md` §4.5, verbatim:

> "**Identical first ids means the server clamps and either base is safe**; different ids resolve
> the base."

Take the two hypotheses the evidence actually leaves open. `JOBVITE-API.md` §20 item 6, verbatim:

> "A recorded call (§6.1) proves `start=0` is accepted and returns records, which rules out a
> strict 1-based server that rejects 0, but does **not** distinguish a 0-based server from a
> 1-based one that clamps `0` to `1`."

So "identical first ids" means **the server is 1-based and clamps 0 to 1**. It does not mean
either base is safe. Walk the paging loop with `count=500` on a clamping 1-based server:

- 0-based caller: `start=0` -> clamped to 1 -> records 1..500. `start=500` -> records 500..999.
  **Record 500 is returned twice**, and the same duplication recurs at every page boundary.
- 1-based caller: `start=1` -> 1..500, `start=501` -> 501..1000. Correct.

Clamping makes **only the first page** insensitive to the base. Every subsequent page is not. The
design's own §9 hazard 5 already names the consequence class ("a long paged scan over a mutating
set may duplicate or skip") for a different cause, so the document knows duplication is a real
failure mode - it just does not connect it here.

The probe is a good idea. Its stated interpretation is wrong, and it is wrong in the direction
that produces a silent data defect rather than a loud one. **§11 item 2 lists the probe as an
open question about *verification*; it is currently also an open question about *logic*, and that
one is resolvable here, today, with no credential.**

### C2 - The probe's premise is contradicted by §9 of the same document, and it caches an indeterminate result. [REASONED]

Three independent failure modes, none of which §4.5 acknowledges. This is a direct answer to
Phil's self-nominated weak claim 1 ("what if both bases return the same first id for an unrelated
reason, or the probe itself is what is wrong?"). Both halves are live.

**(a) The probe assumes a stable order that §9 says does not exist.** `DESIGN.md` §9 hazard 5,
verbatim:

> "**No stable sort.** No sort parameter is documented, so a long paged scan over a mutating set
> may duplicate or skip."

`JOBVITE-API.md` §13, verbatim: "**Sorting:** `[ABSENT]` No sort or `orderBy` parameter appears in
any source, official or third-party. I found no evidence that sorting is supported at all."

The probe issues **two separate HTTP requests** and compares the first id of each. If the server's
default order is not stable across requests - which is exactly what "no stable sort" leaves open -
a clamping 1-based server can return *different* first ids for `start=0` and `start=1`, and the
probe concludes 0-based. The design's detection strategy rests on an ordering guarantee the design
elsewhere states it does not have. Phil's instinct was right and the counter-evidence was already
inside his own document.

**(b) An indeterminate probe is cached as a determination.** §4.5, verbatim: "The result is cached
for the process lifetime and logged once." Consider a tenant, or a filtered query, with **zero or
one** matching candidates. `start=0, count=1` and `start=1, count=1` both return nothing, or both
return the same single record. The probe reports "identical" - which under the design's own
(already wrong, per C1) rule means "either base is safe" - and that verdict is then frozen for the
lifetime of the process and applied to every later paged call over a large result set. **A probe
that cannot distinguish "the server clamps" from "there was nothing to page" must not cache a
verdict.** §4.5 defines no indeterminate state at all.

**(c) The probe is not scoped to an endpoint, and the endpoints demonstrably differ.**
`JOBVITE-API.md` §13's table gives `/v1/jobFeed` a `start` base of **1**, marked `[OFFICIAL]`.
`/api/v2/candidate` and `/api/v2/job` are marked "disputed". §4.5 speaks of "the `start` base" in
the singular, probes it on "the first paged call of a process", and caches one value. If the first
paged call of a process is `search_candidates` and the second is `get_job_feed`, a v2-derived
verdict is applied to a v1 endpoint whose base is documented and not in dispute. Nothing in §4.5
prevents this.

### C3 - §6.2 makes a false, checkable claim about the standards corpus, and ADR-0008 rests on it.

`DESIGN.md` §6.2, verbatim:

> "The GDPR machinery in the standards corpus is `priority: optional` and does not bind, so this
> is a design decision rather than a cited obligation"

`standards/architecture/gdpr-data-rights.md:9`, verbatim:

```
priority: required
```

It also carries `compile_group: core-standards` (`:10`) and `applicable_to: - system-design -
all` (`:7-8`). It is not optional, it is not scoped away from us, and it is in the core group.

I checked whether some *other* GDPR file might be the one meant. `grep -rn 'priority: optional'`
across the entire `standards/` tree returns **twelve hits, all of them `README.md` index files**
(`architecture/README.md:8`, `backend/README.md:9`, `frontend/README.md:10`, `devops/README.md:11`,
`database/README.md:11`, `azure/README.md:12`, `snowflake/README.md:12`, `documentation/README.md:9`,
`guides/README.md:8`, `templates/README.md:8`, `architecture/adr/README.md:8`,
`architecture/adr/ADR-000-template-example.md:8`). **No substantive standard in the corpus is
`priority: optional`.** `ls` confirms `gdpr-data-rights.md` is the only GDPR/privacy/data-rights
file that exists.

Three consequences:

1. **ADR-0008's justification is void as written.** §12 states it as: "special-category EEO fields
   excluded from output models (§6.2), **since the GDPR machinery is non-binding** and this is
   therefore a decision rather than a cited obligation." The premise is false, so the ADR is
   currently an ADR waiving a required standard on the grounds that it is not required.
2. **The design's evidentiary claim is damaged by this more than by the substance.** The document
   opens with "**Every framework claim in this document rests on an executed spike or a quoted
   clause.**" This is a claim about a standard's own metadata, the cheapest possible thing to
   check, and it is wrong. R1 recorded reading this file's "frontmatter only" and reached the same
   conclusion via `STANDARDS.md:683`; whatever the origin, it propagated into a design assertion
   without anyone opening line 9.
3. **A binding obligation is unaddressed and is squarely in scope.**
   `gdpr-data-rights.md:119-129`, verbatim:

   > "## Records of processing (Article 30)
   > For each personal-data field, record:
   > - Lawful basis: consent, contract, legal obligation, vital interest, public interest, or
   >   legitimate interest.
   > - Retention period.
   > - Downstream processors.
   > Maintained in `docs/data-inventory.md` (or equivalent) and reviewed each release that touches
   > a personal-data column."

   This is **field-level**, not table-level, so "we hold no tables" does not answer it. This
   server's entire purpose is to route candidate personal data to a **downstream processor** - a
   language model - which is precisely the third bullet. There is no `docs/data-inventory.md` in
   the repository and no section of DESIGN.md that stands in for one. §6.2's field-exclusion
   decision is, in fact, exactly the kind of thing an Article 30 record documents; the design does
   the work and skips the artefact.

Note what I am **not** claiming: I am not claiming the standard obliges dropping EEO fields.
Its scope (`:32-46`) is DSAR, RTBF, anonymisation, cross-store coordination and records of
processing - data-subject rights, not minimisation. **§6.2's substantive conclusion is probably
right. Its stated reason is false, and the reason is what an ADR is made of.**

### C4 - §10's `mcp` pin is asserted in prose and absent from §10's own verbatim block.

`DESIGN.md` §10, verbatim:

> "**`mcp` is pinned explicitly**, not just `fastmcp`: the `ResponseLimiting` regression arrived
> through the transitive SDK with zero change to the code that broke"

Immediately below, introduced as "Packaging, verbatim, **because both lines are load-bearing**":

```toml
dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4"]

[tool.uv]
prerelease = "explicit"
```

`mcp` does not appear. Neither does anything that would pin it. The two "load-bearing lines" are
the prerelease recipe from `FASTMCP-SPIKE-4.md` §1.3 / §12.1, which is about keeping `pydantic` on
a stable release - a different problem entirely. The spike's own resolution output shows
`mcp 2.1.1` arriving **transitively**:

> `fastmcp 4.0.0b4 | fastmcp-slim 4.0.0b4 | pydantic 2.13.4  <- STABLE | mcp 2.1.1`

Phil nominated §10's drift claim as weak on the grounds that it is "reasoning, neither is
executed". It is worse than that. Half of it is **not written down at all**, and the block that
would carry it is presented as the authoritative verbatim text. Anyone implementing §10 exactly as
specified reproduces the regression class the paragraph exists to prevent.

The second half of the same claim - the `fastmcp inspect` diff - is honest about what it is:
"visible in review rather than at runtime". That is a review aid, not a gate. §10 never says where
the baseline lives, what diffs constitute drift, or whether a non-empty diff fails the build. As
written, capability drift is caught only if a human notices a diff in a CI log. **[REASONED]**

---

## MAJOR

### M1 - §2.1's "single mechanism" merges two problems that are not the same problem, and §6.1 defines a second allow-list the sentence denies exists.

This is Phil's self-nominated weak claim 3, and the suspicion is correct.

`DESIGN.md` §2.1, verbatim:

> "**Outputs are allow-listed models, not passthrough.** A field Jobvite returns that is not on
> the model does not reach the caller. **This is the single mechanism that satisfies both the
> untrusted-content requirement (§6) and the special-category-data position (§6.2)**"

§6.1, verbatim, four paragraphs later:

> "Every such field **is fenced** before it reaches a tool result, and delimiter tokens occurring
> inside the content are stripped so content cannot close its own fence."
> "**The allow-list is path-keyed with wildcards, not name-keyed.** ... Keys are paths like
> `candidates[].application.job.title`."

Two objections, and they compound.

**(a) The two problems are different in kind and the mechanism only solves one.** Allow-listing is
a **containment** control: it decides *which* fields leave the server. Fencing is an **injection**
control: it decides *how* an admitted field is presented so a model does not read it as
instruction. A résumé body is on the allow-list - it must be, it is the point of the tool - and
allow-listing does nothing whatsoever to it. The prompt-injection requirement is satisfied by
fencing, which §2.1's sentence explicitly says is the same mechanism. It is not. The design has
two controls and one sentence claiming one. If that sentence is ever the basis of a compliance
answer, the answer is wrong.

**(b) There are two allow-lists in two key spaces, and the design calls them one.** §2.1's
mechanism is Pydantic output models, **snake_case** ("Outputs are snake_case regardless of
Jobvite's casing"). §6.1's mechanism is a path-keyed list in **Jobvite's own camelCase response
paths** (`candidates[].application.job.title`). These are separate artefacts that must be kept in
correspondence by hand, across a casing boundary that §9 hazard 1 already flags as a live bug
source (`eId` / `EId`). Nothing in §3's module layout owns the correspondence: `models/` holds one
and `utils/redaction.py` holds the other. **The failure mode is silent and asymmetric** - a field
admitted to an output model but absent from the fencing paths reaches the model unfenced, and no
test in §8's list would catch it, because §8 tests fencing *of a fenced field*.

The fix is not to abandon the elegance; it is to make it real. Derive one list from the other, or
state that the output model is the single source of truth and the fencing paths are generated from
it, and add the test that fails when a model field has no fencing decision.

### M2 - §7.5's era discriminator is a capability check that cannot detect a capability, and the spike that would settle it needs no credential.

Phil's self-nominated weak claim 4. It is worse than "unreliable"; as literally specified it is
inert.

`DESIGN.md` §7.5, verbatim:

> "Implementation: the tool inspects `ctx.input_responses` - **`None` on the first leg, populated
> on the retry**."

and, four paragraphs later:

> "**The design must branch on capability, not assume an era.** ... **The guard branches on
> whether `ctx.input_responses` exists.**"

The same expression is asked to carry two orthogonal discriminations:

| | handshake era, first leg | sessionless era, first leg | sessionless era, second leg |
|---|---|---|---|
| `ctx.input_responses` | `None` | `None` | populated |

- Read "exists" as **`hasattr(ctx, 'input_responses')`**: `input_responses` is an attribute of
  `Context` (`FASTMCP-SPIKE-4.md` §17.2: "The accessors are `ctx.input_responses` and
  `ctx.request_state` **on `Context`** `[FROM SOURCE]`, not on `request_context`"). A class-level
  attribute exists on every instance regardless of which era negotiated. `hasattr` returns `True`
  on both eras and the branch is never taken. **[REASONED]** - I did not execute this, and I say so.
- Read "exists" as **`is not None`**: that is already the first-leg/second-leg test in the same
  paragraph. A handshake-era first leg and a sessionless-era first leg are indistinguishable under
  it. The branch fires the wrong way on exactly the install §7.5 says it exists to handle.

**And the load-bearing premise underneath it is unverified.** §7.5 asserts, verbatim: "a stdio
install may land on the handshake era **where `ctx.elicit()` works and MRTR does not**." I searched
`FASTMCP-SPIKE-4.md` for the arm that proves the second clause. §15.2's availability matrix covers
`ctx.elicit()` on both eras and both transports. §17.3's MRTR evidence block is headed "**Evidence
- all three arms, sessionless (`mode="auto"`)**". §16.2 ran the confirmation token "both eras". **No
arm anywhere runs MRTR on `mode="legacy"`.** Whether MRTR works, fails, or silently degrades on the
handshake era is unknown, and the design branches on the assumption that it fails.

This is the most actionable finding in the round: **it is a spike, not a credential.** The spike
harness in §17 is stubs and touches no Jobvite endpoint (`FASTMCP-SPIKE-4.md` closing section:
"**Anything about Jobvite.** No Jobvite endpoint was contacted; every tool here is a stub"). Running
§17.2's tool under `mode="legacy"` settles both the premise and the discriminator in one afternoon.

### M3 - §5.3's audit event omits fields a `priority: required` standard names verbatim, and the design has no policy for the audit write failing. [ABSENT] [STD]

Phil's self-nominated weak claim 2, plus two things he did not nominate.

**(a) The failure policy is genuinely absent.** §5.3 specifies what `audit.py` emits and where
`request_id` comes from. It says nothing about what happens when the emit raises. I read the
section three times looking for it. Neither `errors.py` nor `audit.py` in §3's layout carries a
note. Phil's framing of the dilemma is exactly right and the design must pick: an open failure
puts a silent hole in a mandated audit log; a closed failure lets a logging fault take down a read
tool that was working. **The standards give a shape for the answer that the design has not used.**
`ai/llm-observability.md` (frontmatter `priority: required`), "Tracing is mandatory", verbatim:

> "Tracing failures must **never** break the request: trace export is best-effort and async; a
> backend outage degrades observability, not the user response."

That is a *tracing* clause, not an *audit* clause, and the distinction matters -
`agent-guardrails.md:130` calls tool logs "an audit trail: append-only intent". A defensible
position is available (audit failure is fatal to the **write**, non-fatal to the **reads**, and
always raises an alarm), but the design has to state it. The ADR list has no entry either way.

**(b) The mandated field list is incomplete, and the missing field is the one that matters here.**
`ai/agent-guardrails.md:121-123`, verbatim:

> "- **Log every tool invocation** with: tool name, validated arguments (PII redacted), result
>   status, latency, **the approval decision if gated**, and the request correlation id."

and `:77-79`, verbatim:

> "**Approvals are scoped and expire.** An approval authorizes one specific call (or a narrow,
> declared batch), not a standing capability. **Record *who* approved *what* and *when* in the
> audit log.**"

`DESIGN.md` §5.3's field list, verbatim: "tool name, validated arguments with PII redacted, result
status, latency, correlation id." **The approval decision is not there**, on a server whose single
write tool is approval-gated by two mechanisms in §§7.5-7.6. It cites `ai/tool-calling.md:171-173`,
which is the version of the clause *without* the approval field; `agent-guardrails.md:121-123` is
the version *with* it, and §5.3 cites `agent-guardrails.md:40` - which is a **Scope bullet**
("Mandatory audit logging of every tool invocation"), not the normative clause at `:119-131`. The
design cited the table of contents and inherited the shorter field list from the other file.

**(c) There is a real, honest collision here that the design should own rather than inherit.**
`:79` requires recording *who* approved. §7.5 states, correctly and at length, verbatim: "the claim
is *'the server requires an approval response from the host and refuses to write without one'* -
**never** *'a human approved this.'*" **The server cannot record *who*, and a required clause says
it must.** That is a genuine, defensible deviation - and it is exactly what an ADR is for. §12 has
no ADR covering it. §7.5's paragraph is the best writing in the document and it stops one sentence
short of the compliance consequence.

**(d) Two smaller field misses in the same clause.** `ai/tool-calling.md:173-176`, verbatim: "Use
the canonical triple verbatim: HTTP header `X-Request-ID`, log field `request_id`, **ContextVar
`request_id_var`** ... **Also attach the LLM trace/span id** so a tool call ties back to its turn."
§5.3 covers the header and the log field and names neither the ContextVar nor the trace id.

### M4 - §1's "holds no state" claim is false under §7.7, and candidate PII is cached with no stated key, TTL, or eviction. [ABSENT]

`DESIGN.md` §1, verbatim:

> "It holds no state between calls beyond an HTTP connection pool, a rate-limiter bucket, and
> short-lived confirmation tokens."

`DESIGN.md` §7.7, verbatim:

> "Adopted, each constructed with explicit arguments: `ResponseCaching` (never on preview), ..."

`ResponseCachingMiddleware` caches **tool results**. Four of the five tools return data;
`search_candidates` and `get_candidate` return candidate PII. So the server holds candidate
personal data in process memory between calls, and §1 says it does not. That is not a pedantic
catch: §1's sentence is the document's whole statement of its data-at-rest posture, and a reader
deciding whether this server needs a privacy review will read that sentence and stop.

What §7.7 specifies about the cache, in full: that it must never touch the preview tool. What it
does not specify:

- **Whether candidate PII is cacheable at all.** No position taken. §6.2 goes to real trouble to
  keep EEO fields from *leaving* the server and the design then caches everything that does leave.
- **The cache key.** `FASTMCP-SPIKE-4.md` §6.1 proves keying on tool arguments and nothing more:
  "after call#1 (key=a): 1 / after call#2 (key=a): 1 <- CACHE HIT / after call#3 (key=b): 2 <-
  control MISS". **Whether the key includes caller identity was not tested.** Under §7.2's scoped
  tokens the blast radius is bounded - `require_scopes` removes the tool entirely from a caller
  without the candidate scope - but "bounded by a control in another section" is a conclusion the
  design should reach out loud, not one a reader should have to derive.
- **TTL and eviction.** Unspecified here, and unverified in the spike, which lists under "What I
  could NOT verify": "**Token expiry**, and **cache TTL expiry** - I proved cache insertion and
  hit, never eviction."

§7.7's own rule applies to itself: "**on this framework a middleware's default is not a safe
starting point**" and "each one's arguments are justified here." `ResponseCaching` is the one
adopted middleware whose arguments are *not* justified there - it gets a parenthesis.

### M5 - §2.2 and §7.6 give two different answers to whether the confirmation token is always required.

§2.2, verbatim, listing gate 3:

> "**Confirmation token** (§7.6) **as defence-in-depth and as the fallback** where the host cannot
> elicit. Needs no client cooperation."

§7.6, verbatim, first two sentences:

> "**The fallback** where a host reports 'Elicitation not supported', **and defence-in-depth
> otherwise.** A preview call returns a short-lived token describing exactly what would be
> written; **the write requires it.**"

"The write requires it" is unconditional. "As the fallback where the host cannot elicit" is
conditional. These are different servers:

- **Token always required:** every `create_candidate` is a mandatory two-call sequence for every
  client, including a client that supports MRTR perfectly. That is a real ergonomic cost and a real
  documentation obligation, and it makes §7.6's `ResponseCaching` warning load-bearing on the
  happy path rather than on a fallback path.
- **Token only on the elicitation-unavailable path:** then a host that supports MRTR and
  auto-approves without showing a human anything - which §7.5 explicitly warns is possible,
  verbatim: "A host can auto-respond to elicitation without showing anyone a dialog" - passes with
  **one** gate, not two, and §2.2's "three independent gates" is two for the clients most likely
  to be automated.

§12's ADR list has no entry for the composition rule. An implementer reading §2.2 and an
implementer reading §7.6 build different things.

### M6 - The evidence base contains one recorded Jobvite success response. §1.1 and §8 say none exists, and §8's fixture policy is built on that.

`DESIGN.md` §1.1, verbatim, bolded in the original:

> "**Nobody building this holds a Jobvite credential, so no success response from Jobvite has ever
> been observed.**"

`DESIGN.md` §8, verbatim:

> "- **Synthetic** - every success body, **because no 2xx has ever been observed.** Hypotheses in
>   JSON."

`JOBVITE-API.md` §6.1 is titled "**The one observed success response `[RECORDED-3P]`**" and reads,
verbatim:

> "There is exactly one genuine success response available: a VCR cassette committed to
> `atipica/jobvite_api`, recording `GET /api/v2/candidate?count=5&start=0&format=json`."

It settles four things the design currently treats as open:

1. "**A success body DOES carry a `status` block.** The response envelope is `{"candidates": [...],
   "total": <int>, "status": {"code": 200, "messages": []}}`" - which is **§11 open question 4**
   ("Whether success bodies carry a `status` block at all. The parser tolerates both") answered.
2. "**`total` is the full result-set size, not the page size.**" - which is §4.5's termination rule
   confirmed rather than inferred.
3. "**`start=0` is accepted and returns records**" - which is half of C1's hypothesis space.
4. "**The real candidate field map** ... including EEO fields and an inline resume" - which is the
   direct source of §6.2's entire position.

The design's absolute statement is false, and it is false in the direction that *understates* the
evidence. The consequence is not rhetorical: §8's two-tier fixture split ("Recorded" for errors,
"Synthetic" for every success) misclassifies the strongest success-shape evidence in the project as
a hypothesis, and §11 keeps a question open that the evidence closed.

**The remedy is constrained and I want to be precise about the constraint**, because the naive fix
is unsafe. `JOBVITE-API.md` §6.1's handling note, verbatim: "That cassette is a third-party artifact
containing an `api`/`sc` credential pair in the recorded request URI, and candidate records
including EEO attributes ... **Nothing from it is copied into this repository**." So the response
body cannot be recorded verbatim. What can be pinned is its **structure** - a third fixture tier,
structurally-confirmed, whose shape is asserted against a real observation rather than invented.
§8's own sentence "A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite" is exactly right and applies to four operations, not
five.

### M7 - Jobvite's only documented operating envelope is in the evidence and absent from the design. There is no outbound throttle and no 429 handling. [ABSENT]

§4.4 is a full page on rate limiting and every word of it is about **inbound** MCP requests -
`get_client_id`, per-session burst, per-client quotas, a config-reload amnesty. That is protection
for *our* server from a noisy integrator. There is no outbound control on calls **to Jobvite**
anywhere in the document.

`JOBVITE-API.md` §14, verbatim, and marked `[OFFICIAL]` - the strongest provenance tag in that
document:

> "What exists instead is **cadence guidance**, not a limit. Data Services v3.5, 'Best Practices:
> Calling the API', states that Jobvite expects the API to be called on an as-needed basis, and
> that any customer needing to call it **more often than once a day** is required to constrain the
> call with at least one of: a workflow-state date filter, a bounded page size ..., a specific
> requisition's candidates, or only requisitions that have changed."
>
> "The expected cadence is therefore **once a day** ... That is a far tighter operating envelope
> than a typical SaaS API, and it is the closest thing to a documented limit that exists."

and its stated design consequence, verbatim:

> "**Design consequence:** we must assume an undocumented limit exists, implement conservative
> client-side throttling plus exponential backoff on 429/5xx, and cache aggressively"

An MCP server hands a model a search tool. A model in a loop is the *opposite* of once-a-day
as-needed calling. Three specific gaps:

- **No outbound throttle.** §4.3's retry budget and §4.4's inbound limiter do not bound
  requests-per-minute to `api.jobvite.com`.
- **429 is not in the retry set and not in the error map.** §4.3, verbatim: retries fire "only for
  connection errors, timeouts and 5xx." §5.1, verbatim: "`status` carries the upstream Jobvite
  status where one exists, 400 for input validation, 503 for an upstream 5xx." A 429 falls into the
  "upstream status where one exists" bucket and is passed through as 429 with no `Retry-After`
  handling and no backoff. `ai/resilience.md` ("Surfacing failures"), verbatim: "**Map upstream
  throttling to 503** (with `Retry-After` where known), not 500."
- **§3 rejects caching as speculation.** Verbatim: "No cache module ... the second is speculation."
  §14's `[OFFICIAL]` cadence guidance is the specific, evidenced reason a cache is *not*
  speculation. (§7.7's `ResponseCaching` may in fact discharge this - see M4 - but §3 argues
  against a cache and §7.7 adopts one without either section referencing the other.)

I am **not** recommending anything that requires calling Jobvite. Every remedy here is a
client-side configuration decision.

### M8 - The one write tool has no position on Jobvite's duplicate-candidate response, which is in the evidence. [ABSENT]

`JOBVITE-API.md` §7.2, verbatim, describing the production write path this tool is modelled on:

> "**Response:** `HTTP 201` ... Handled error statuses in that config: `400`, `404`, `409`."

and §15.1, verbatim: "`400`, `404`, and `409` are handled on the candidate-create path
(`sahil-kho`); **`409` is presumably a duplicate candidate.**"

`DESIGN.md` §9's hazard list has six entries and none is 409 or duplication. §2.2 guards the write
three ways against *unauthorised* creation and says nothing about *repeated* creation. §4.3
excludes the tool from retry, which prevents the client from duplicating - but the natural agent
behaviour that produces a duplicate is a *model* calling the tool twice, which no gate in §2.2
prevents (the second call gets its own approval and its own token, both of which succeed).

`ai/resilience.md` ("Idempotency on retry"), `priority: required`, verbatim:

> "Make side-effecting tools idempotent (idempotency key) **or** retry only the model call, not
> the tool execution, after a failure."
> "**Never auto-retry across a committed side effect (a sent email, a charged payment).**"

§4.3's no-retry choice satisfies the "or". Good. But `ai/resilience.md` is `priority: required`
and appears **nowhere** in DESIGN.md's citations, and the 409 semantics - is a duplicate an error
the caller should see as 409, or a success? does `send_email` fire on a duplicate? - are the
difference between a confusing tool and a tool that emails a live human twice. §1.1's whole
argument is that the write's side effect is an email to a real person.

### M9 - Five R1 findings accepted in round 1 did not survive the rewrite, and one regressed to the exact wording R1 asked to remove.

Phil's self-nominated weak claim 6 ("rewrites are lossy ... tell me what fell out"). I diffed
R1's decision table against revision 2 line by line. **C1-C4, M1-M7, M9, M10, m1, m2, m4, R2-e all
landed**, several of them strengthened well beyond what was agreed (§7.4 in particular is far
better than R1's M7 asked for). Five did not.

- **m3 regressed to the rejected wording.** R1's decision was **MODIFIED**, verbatim: "Keep
  `defusedxml`; **re-label as a hardened fallback, not one of four handled cases**." Revision 2
  §4.2, verbatim: "**Four error encodings exist across one API**: a JSON status envelope, plain
  text with no `Content-Type` header at all, a Tomcat HTML page, **and HR-XML.** XML is parsed with
  `defusedxml`." That is the "one of four handled cases" framing, restored verbatim in the count
  ("Four"), on a route (`/v1/candidate`) the design does not call. This is the clearest instance of
  the loss Phil suspected: not a dropped sentence, a *reverted decision*.
- **m5 dropped entirely.** R1 decision: **ACCEPTED** - "Open circuit breaker has no problem `type`
  or `status` mapping." §5.1's mapping in revision 2 is "the upstream Jobvite status where one
  exists, 400 for input validation, 503 for an upstream 5xx." §4.3 has a breaker. **No `type` slug
  and no status for an open breaker exists anywhere in revision 2.** R1's objection stands
  unchanged: a caller cannot distinguish "Jobvite is down" from "we have stopped calling Jobvite",
  and `ai/resilience.md` ("Surfacing failures") asks for exactly this: "Use a **stable `type` URI
  per failure mode** (e.g. provider-unavailable, provider-timeout) so clients can branch."
- **m6 dropped.** R1 decision: **ACCEPTED**. §1 still reads "a rate-limiter bucket" without naming
  it as the framework's, which was the entire point - §4.4 spends a paragraph establishing that its
  ownership and its frozen-at-startup parameters are not ours.
- **R2-d's table dropped.** R1 decision: **ACCEPTED** - "**Add the table**; scope fail-fast to the
  enabled tools' configuration." §7.3 states the principle beautifully, verbatim: "fail-fast
  validates the configuration each *enabled* tool requires, not the union of all of them." **The
  table is not there**, and without it the principle is unimplementable - and worse, §2's tool
  table lists five tools with no per-tool enable mechanism at all. The only toggle in the entire
  document is `JOBVITE_ENABLE_WRITES`. §7.3's "each *enabled* tool" presupposes a per-tool enable
  surface that no section defines. **[ABSENT]**
- **m7 half-landed and picked up a mis-citation.** R1 asked for the B20 clause cited inline plus
  the reference project's 51-tool counter-example named. Revision 2 §2, verbatim:
  "**`ai/tool-calling.md` requires a minimal allow-list** because an unused or unreliable tool is
  attack surface." The "unused tool is attack surface" language is not in that file. It is
  `ai/agent-guardrails.md:47-49`, verbatim: "**Minimal tool set.** Bind to an agent only the tools
  its task requires. Do not expose a broad 'kitchen-sink' toolbox; **an unused tool is attack
  surface.** The callable-tool list is an explicit allow-list per agent." R1 gave the correct
  citation in m7; revision 2 moved it to the wrong file and dropped the line number.
  (`tool-calling.md:54` does contain the phrase "attack surface" - about loose parameter types -
  which is the likely source of the slip.)

### M10 - Two controls depend on the server being a single process, and no section states that as a deployment constraint. [ABSENT]

§4.4 argues ADR-0002 on it, verbatim: "the standard's rationale is replica desynchronisation, and
**a single-process server has no replicas**." That reasoning is sound *given* the premise.

§7.6's confirmation tokens depend on the same premise and never mention it. Replay refusal requires
a server-side record of spent tokens; `FASTMCP-SPIKE-4.md`'s closing section says so explicitly:
"the token store is **in-process** (**a multi-worker deployment would need shared state**)".

§7.1 offers an HTTP transport with a bindable address and `allowed_hosts`/`allowed_origins` - the
shape of something someone will put behind a load balancer and run with multiple workers. When they
do: the rate-limit quota fragments per worker (a caller gets N times their limit), and the
confirmation token minted by worker 1 is unknown to worker 3, so the write fails closed at random.
The second is safe-but-broken; the first is a control silently multiplied.

The design needs one sentence somewhere in §7.1 or §10 - "this server runs as a single process;
multi-worker deployment invalidates ADR-0002 and §7.6" - and §12's ADR-0002 needs it in its
consequences. `backend/rate-limiting.md:9` is `priority: required`, so ADR-0002 is a live waiver
and its premise should be enforced, not assumed.

---

## MINOR

**m1.** §4.5 states "Page cap **500** on v2" as flat fact. `JOBVITE-API.md` §13's table marks the
v2 `count` max **`[INFERRED]`**, from two clients' client-side guards, versus `[OFFICIAL]` for the
v1 numbers. The document that opens by insisting every claim rests on a spike or a quoted clause
should carry the provenance distinction into §4.5, as §11 does elsewhere.

**m2.** §10 claims adopting `httpx2` "**removes** that hazard rather than guarding it", the hazard
being that "`except httpx.HTTPError` can never catch a FastMCP-raised exception". It does not
remove it, it **inverts** it. With one shared stack, `except httpx2.HTTPError` in
`services/jobvite_client.py` now *can* catch a transport exception raised by FastMCP's own
internals - a different bug, in the opposite direction, and a quieter one: our Jobvite error path
swallowing a framework failure and reporting it as a Jobvite problem. The conclusion (adopt
httpx2, drop the AST test) is still right; the sentence justifying it is not, and it is the
sentence that retired R1's M8 guard.

**m3.** §4.4's four constraints are presented as "established by execution", and they were - but
`FASTMCP-SPIKE-4.md`'s closing section says, verbatim: "**Rate limiting under concurrency.** Every
limiter test was sequential and single-client; I have not verified bucket behaviour under
simultaneous callers, **which is the case that matters in production**." and "**Whether
`limiters.clear()` is safe to call on a live server.** I used it to prove reconfiguration requires
it; I did not test it under load or check for a race with in-flight consumption." R1 flagged the
first of these against P9/P15 and revision 2 does not carry the caveat. "Burst is sized
`desired_calls + 2` per session. Measured: burst 3 yields 1 tool call" is a sequential measurement
presented without its condition.

**m4.** §4.5's probe adds two extra requests on the first paged call of every process, to an API
whose `[OFFICIAL]` guidance is once-a-day as-needed calling (M7). Small, but it should be one
config-gated line rather than an unremarked cost - and `JOBVITE_PAGINATION_START_BASE` already
provides the escape.

**m5.** §7.7's "a page is capped and the result says `showing 50 of 1,240`" combined with §9 hazard
5's "no stable sort" means *which* 50 is not reproducible between two identical calls. The design
presents the capped result as "more useful to a model than a truncated JSON blob", which is true,
and does not note that it is also non-deterministic. A model that re-runs a search to check
something will sometimes see a different 50.

---

# BLUE ROUND - Normal response

**C1 - ACCEPT, without qualification.** The sentence is wrong and I cannot defend it. Clamping
protects the first page and nothing else; on every later page a 0-based caller against a clamping
1-based server re-reads the boundary record. The corrected rule is: **identical first ids means the
server is 1-based (it clamped 0 to 1); use base 1.** Different first ids means base 0. There is no
"either is safe" branch. I will also add the consequence sentence, because it is what makes the
rule stick: getting this wrong duplicates one record per page boundary and no test against a
synthetic fixture can see it.

**C2 - ACCEPT (a) and (b), ACCEPT (c) with a correction to Red's framing.**

(a) is the finding of the round on this section and I walked past my own §9. If the default order
is unstable across requests, the probe's "different ids" branch is unsound in the direction that
looks like a successful detection. Mitigation, credential-free: probe with `count=2` and compare
the returned **id sets**, not the first id - a clamping server returns the same set, an
order-unstable server returns overlapping sets, a genuinely 0-based server returns sets offset by
one. Any other outcome is indeterminate.

(b) ACCEPT. An indeterminate probe must not cache a verdict. And the design needs a **safe
default** for the indeterminate case, which it currently lacks entirely. It is base **0**, and the
reasoning is asymmetric: under a 1-based clamping server, base-0 paging **duplicates** a record per
boundary; under a 0-based server, base-1 paging **skips** record 0 of every page. For a search tool
feeding a model, a duplicate is visible and a skip is invisible. Pair it with deduplication by
`eId` across pages inside the pagination loop, which is cheap, and the duplicate failure mode
disappears entirely while the skip failure mode cannot be recovered. **That makes the indeterminate
path safe rather than merely honest**, and it needs no credential.

(c) ACCEPT the defect, correct the framing: the probe should not run against `/v1/jobFeed` at all,
because its base is `[OFFICIAL]` 1. Cache keyed per `(api_version, resource)`, and skip the probe
where the base is documented.

**C3 - ACCEPT, and this is the one I am most uncomfortable about.** I asserted a file's metadata
without opening the file. `gdpr-data-rights.md:9` reads `priority: required` and Red checked the
whole corpus for a competing file and an alternative `optional` marker. Three fixes, and I want
them separated because they are different sizes:

1. **Text, immediate.** Delete the `priority: optional` sentence from §6.2.
2. **ADR-0008, re-grounded.** The substantive conclusion survives on **scope**, not priority. The
   standard's own Scope section (`:32-46`) is DSAR, RTBF, anonymisation, cross-store coordination,
   and records of processing - rights machinery over stores of personal data. We operate no store.
   That is a real argument and it is the one the ADR should have made. Red concedes the point
   ("§6.2's substantive conclusion is probably right"), and I agree the reason is what an ADR is
   made of.
3. **`docs/data-inventory.md` - ACCEPT as a new required deliverable.** `:119-129` is field-level
   and names downstream processors, and shipping candidate PII to a model is the clearest possible
   instance. It is also nearly free: §2.1's output models already enumerate every personal-data
   field that leaves the server, so the inventory is a table derived from artefacts the design
   already mandates. Lawful basis is the operator's, not ours, so the file carries a column the
   deploying customer completes.

**C4 - ACCEPT.** The prose promises a pin the block does not contain. Correct the block to
`dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4", "mcp==2.1.1"]`, taking the version
from the spike's own resolution output, and say why the third entry is there so nobody tidies it
away as redundant. On the `fastmcp inspect` half: ACCEPT that "visible in review" is not a gate,
and MODIFY rather than escalate - store the baseline in the repo, diff against it in CI, and fail
the build on a non-empty diff with an instruction to commit the new baseline deliberately. That
converts a review aid into a gate for the cost of one committed file, and it is the same
allowlist-first-with-a-reviewable-override shape §10 already uses for the file-type gate.

**M1 - ACCEPT (a), ACCEPT (b), and drop the "single mechanism" claim.** Red is right that the
elegance was doing the arguing. Containment and injection-fencing are different controls with
different failure modes and I merged them because one sentence covering both reads better. Correct
statement: allow-listed output models satisfy §6.2 and the *unknown-field* half of §6; **fencing is
a second, separate control** covering the admitted-free-text half. On (b): ACCEPT, and the fix is
the derivation, not more prose - the output model is the single source of truth, each field carries
an explicit `fence: true|false`, and the path-keyed fencing list is generated from it. The test
§8's list is missing then becomes writable: **every field on every output model has an explicit
fencing decision, and a new field without one fails the build.** That is the fail-closed property
§2.1 claims and does not currently have.

**M2 - ACCEPT in full, and this is the highest-priority action out of this round.** I cannot
defend "the guard branches on whether `ctx.input_responses` exists" against either reading. The
`hasattr` reading is inert if the attribute is class-level, and the `is not None` reading is
already spent on leg discrimination. And Red is right that the premise underneath - MRTR does not
work on the handshake era - has no arm anywhere in the spike. I checked §15.2, §16.2 and §17.3
myself after reading this and the MRTR evidence is sessionless-only, as stated.

The action is a spike, not a design change, and **it needs no credential**. Run §17.2's tool under
`mode="legacy"` on both transports and record four cells: does `InputRequiredResult` reach a
handshake-era client, does the client retry with `inputResponses`, does `ctx.input_responses`
exist, and what does `hasattr` return on each era. Until those cells exist, §7.5's branch is
unspecified and I will not write a discriminator that guesses. **If** MRTR turns out to work on
both eras, the branch disappears entirely and the section gets simpler.

**M3 - ACCEPT (a), (b), (d). ACCEPT (c) as the finding, and take the decision here.**

(a) The policy, stated: **the audit event is emitted before the tool result is returned. If the
emit fails on `create_candidate`, the call fails closed** - a write to a real ATS that we cannot
account for is worse than a refused write, and §2.2's whole posture says so. **If it fails on a
read, the call succeeds** and the failure is itself logged at ERROR to the transport log plus
whatever alarm the deployment has. Reads are non-destructive and taking a search tool down because
a log sink hiccuped is the failure mode Red's framing warns about. This is a divergence between
tools and it needs to be stated in §5.3 and tested both ways.

(b) ACCEPT. Add `approval_state` to the field list, cite `agent-guardrails.md:121-123` for the
normative clause rather than `:40`'s Scope bullet, and note that `:40` was a table-of-contents
line. Red is right that citing the ToC is how the shorter field list got inherited.

(c) ACCEPT, and it is the best thing in this finding. The collision is real: `:79` requires
recording *who*, and §7.5 correctly refuses to claim a human was involved. **ADR-0009**: the audit
record carries `approval_state`, `approval_mechanism` (`mrtr` | `token` | `none`), and the host
identity the transport gives us - and explicitly records that *who* is unavailable by construction,
with §7.5's reasoning as the justification. Recording "the host asserted approval, and the server
cannot know whether a human was behind it" is more honest than an `approved_by` field holding
something invented.

(d) ACCEPT. `request_id_var` as the ContextVar name, verbatim per the clause; trace/span id
attached where the deployment has a tracer and omitted with a stated reason where it does not.
I will note that `ai/llm-observability.md`'s scope is "all three production providers: Bedrock
Converse, the OpenAI SDK, and the Anthropic `claude-agent-sdk`" and this server calls none of them
- it is the tool a provider calls. So the tracing standard's applicability is genuinely arguable;
`tool-calling.md:176`'s "attach the LLM trace/span id" is not, because it is a clause about tool
logs and we write tool logs.

**M4 - ACCEPT, and take the decision: candidate tools are not cached.** §1's sentence is false as
written and Red is right that it is the document's only data-at-rest statement. Both fixes:

1. `ResponseCaching` is scoped to `search_jobs` and `get_job_feed` - **public job data, the one
   data class in §4.1 where a cache is uncontroversial** - and never to `search_candidates`,
   `get_candidate`, or the preview tool. That resolves the key question, the TTL question and the
   PII question in one move, and it does not cost the thing caching was for: the job feed is the
   high-volume, low-churn, cacheable surface.
2. §1's sentence gains the cache and names the bucket's owner (which also discharges M9's m6).

I take Red's point that §7.7's own rule - a middleware's arguments must be justified there -
applied to `ResponseCaching` and I gave it a parenthesis.

**M5 - ACCEPT the contradiction. MODIFY the resolution: the token is always required.** Red frames
the two servers correctly and the second one is not defensible given §7.5's own warning that a host
can auto-respond without showing anyone a dialog. If the token is only a fallback, the automated
clients - the ones the warning is about - get exactly one gate. Making it unconditional costs a
round trip on the rarest tool in the surface and makes §2.2's "three independent gates" true as
written. §7.6's `ResponseCaching` warning then sits on the happy path, which is an argument *for*
M4's decision to scope caching away from write-adjacent tools entirely.

**M6 - ACCEPT.** §1.1's absolute is false and I overstated the evidence gap in the direction that
flatters the design's caution. Three fixes: §1.1's sentence becomes "no success response has been
observed **by us**; one third-party recording of `GET /api/v2/candidate` exists and is described in
`JOBVITE-API.md` §6.1"; §8 gains a third fixture tier, **structurally-confirmed**, for the one
operation that has one; §11 open question 4 closes, because §6.1 answers it. I accept Red's
constraint that the body cannot be copied - the cassette carries a live credential pair and real
EEO data - so the tier asserts shape, not bytes.

**M7 - ACCEPT the absence. MODIFY the remedy's scope.** The outbound gap is real and §4.4 reads as
a complete rate-limiting section while covering only the inbound half. Adopt: an outbound
requests-per-minute ceiling in `services/jobvite_client.py`, configuration-driven and
conservative-by-default; 429 added to the retry set with `Retry-After` honoured where present;
429 mapped to **503** per `ai/resilience.md`, not passed through; and §14's `[OFFICIAL]` cadence
guidance quoted in the README so an operator sizing the ceiling has the vendor's own words.

What I will **not** decide here: whether the resulting cadence is acceptable to Jobvite under
whatever agreement the deploying customer has. That is a commercial question and it is not mine.
§3's "no cache module" line gets corrected either way, since §7.7 adopts one.

**M8 - ACCEPT.** 409 is in the evidence and absent from the design, on the one tool that writes.
Add it to §9 as hazard 7 with its `[INFERRED]` provenance, map it to a distinct problem `type`
slug so a caller can branch on "this candidate already exists", and state explicitly that
`create_candidate` performs no client-side duplicate check - because it cannot: there is no
documented lookup-by-email and §11 question 3 says the record-level not-found shape is unknown.
Stating that is better than implying a check exists.

**M9 - ACCEPT all five.** This is the answer to the question I asked, and it is more useful than I
expected: the losses are not scattered, they are **all in the small findings**. Every CRITICAL and
every MAJOR from R1 landed and several were strengthened. What the rewrite ate was minors and one
accepted table. m3's regression is the worst of them because a decision was reverted rather than
dropped - the "Four error encodings" sentence is good prose and that is exactly why it survived a
rewrite that should have demoted it. Restore all five: m3 re-labelled as a hardened fallback (three
handled encodings plus a hardened XML fallback); m5's breaker `type`/`status`; m6's bucket
ownership (folded into M4's §1 rewrite); R2-d's table **plus** the per-tool enable surface Red
correctly noticed does not exist; m7's citation corrected to `agent-guardrails.md:47-49` with the
`fast-mcp-jira` counter-example named.

**M10 - ACCEPT.** One sentence in §7.1 and a consequences line in ADR-0002. Cheap and it prevents
a whole class of confusing production reports.

**m1 - ACCEPT.** Carry the `[INFERRED]` tag into §4.5.

**m2 - ACCEPT.** Red is right that "removes" is wrong and "inverts" is right. The conclusion holds;
the justifying sentence gets corrected, and the inverted hazard gets one line: catch `httpx2`
exceptions only around the call site, never around a block that can raise a FastMCP error.

**m3 - ACCEPT.** Carry the spike's own concurrency caveat into §4.4. R1 flagged it and I dropped
it, which makes it a sixth item for M9's list.

**m4 - MODIFY.** Real but small. The probe is once per process per resource, not per call, and
C2(c) already reduces its scope. One sentence noting the cost and pointing at
`JOBVITE_PAGINATION_START_BASE`.

**m5 - ACCEPT.** One sentence in §7.7. It is a genuine surprise for anyone who re-runs a search.

---

# RED ROUND - Adversarial rebuttal

Blue accepted almost everything, which usually means the round was too easy or the acceptances are
softer than they read. Four are softer than they read, and Blue's own answers unlock two new
points.

### R2-a - Blue's C2(b) safe default is right, and it silently changes a claim in §4.5 that Blue did not notice.

The dedup-by-`eId` fallback is good and I endorse it. But note what it does to §4.5's termination
rule. §4.5, verbatim: "Paging terminates on a short page (`len(items) < count`), never on `total`."
If the loop deduplicates, `len(items)` after dedup is no longer the transport's page length. On a
clamping server with base-0 paging, page 2 returns 500 items of which 1 is a duplicate; a naive
implementation of "short page" against the **deduplicated** list sees 499 < 500 and **terminates
the scan early**, silently truncating results. The termination test must run against the **raw**
page length, before dedup. That is a two-word change in the design and a guaranteed bug if it is
left to the implementer to work out.

### R2-b - Blue's M3(a) split policy is defensible and creates a gap Blue did not price.

Fail-closed on write, fail-open on read is the right instinct. But `create_candidate`'s audit emit
happens *around* an operation whose whole point is that it is irreversible and unretryable. If the
emit fails **after** the POST returns 201, failing the call closed reports a failure for a record
that **exists**. The caller - a model - now believes no candidate was created, and a real human has
already received the confirmation email. The natural next action is to try again. §2.2's gates all
sit *before* the write; none of them prevents a second write that the model believes is the first.

So the policy needs a third state, not two: pre-write audit failure fails closed; **post-write
audit failure must return a result that says the write succeeded and the audit did not**, loudly,
never a generic error. This is the same shape as `fast-mcp-jira`'s `build_response(False,
error="Internal error occurred")` that R1's own closing section called out at
`src/fast_mcp_jira/tools/issues.py:110` - a failure wearing a success's clothes, or here the
reverse. Cite it only as a pattern; it carries no authority.

And this collides with §7.4's standing rule, verbatim: "**Nothing that must complete before
connections close may live in a lifespan teardown.**" §7.4 already predicts this, verbatim: "the
constraint is free now and will be violated by the first person who adds a metrics flush or an
audit-log write. **§5.3's audit event makes that more likely, not less.**" Blue's M3 answer makes
audit emission a per-invocation, synchronous, failure-significant operation - which is the correct
way to keep it out of teardown, and §5.3 should say so explicitly rather than leaving the two
sections to agree by accident.

### R2-c - Blue's M5 resolution makes the token unconditional and does not chase what that costs.

"Making it unconditional costs a round trip on the rarest tool" understates it. If the token is
always required, `create_candidate` is a **four**-leg interaction on a MRTR client: preview call,
create call returning `InputRequiredResult`, client retry with `inputResponses`, done - and the
preview's token must still be unspent and unexpired when the retry lands. §7.6 says the token is
"short-lived" and never gives a TTL. An abandoned-then-resumed approval, which §7.5 says can hang
indefinitely ("a client-side timeout does not bound it"), will routinely outlive a short TTL. **The
two gates Blue just made mandatory-together have a timing interaction neither section models**, and
its failure mode is a write that is refused for token expiry after a human has already approved it -
the most infuriating possible outcome, and one that will push integrators toward
`JOBVITE_ENABLE_WRITES=false` or toward asking for the token to be optional again.

The TTL must be specified, it must exceed the realistic approval latency, and §7.6 must state that
the token's clock starts at preview and is not refreshed by the approval round trip.

### R2-d - NEW, unlocked by Blue's M4 decision: scoping the cache to job tools removes the only justification §7.7 gives for adopting caching at all.

I endorse the decision - candidate PII should not be cached. But `get_job_feed` uses a **separate
credential** (§2's table, §4.1's third class) and `search_jobs` is v2. So after Blue's fix, the
cache covers exactly two tools, one of which is on a credential a deployment may not even have
(§7.3, verbatim: "A deployment using only candidate search must not be forced to invent a
`companyId` it has no use for"). For a candidate-search-only deployment - which §7.3 explicitly
designs for - **`ResponseCachingMiddleware` is then adopted, constructed, and reachable by zero
tools.**

§7.7's own rule, verbatim: "**No middleware is adopted on the strength of its documentation, and
each one's arguments are justified here.**" A middleware that no enabled tool can reach is not a
justified argument, it is inert surface - and §2's opening principle, verbatim, is that "an unused
or unreliable tool is attack surface", which generalises. Either the cache is conditional on the
job tools being enabled - which ties it to R2-d/M9's missing per-tool enable table - or it is
dropped and §3's original "no cache module" instinct was right for the wrong reason.

### R2-e - NEW, unlocked by Blue's C3(3): the data inventory Blue just accepted has no owner and no gate, which is how R1's accepted items died.

Blue accepts `docs/data-inventory.md` as a new deliverable and correctly notes it is nearly free to
derive. M9 is a list of five accepted-and-then-lost items. The standard itself supplies the gate,
`gdpr-data-rights.md:128-129`, verbatim: "Maintained in `docs/data-inventory.md` (or equivalent) and
**reviewed each release that touches a personal-data column**." A file with no CI check and no
release-gate reference is a file that will be correct on the day it is written. §10's CI list is
where it belongs, alongside the licence allow-list gate and the file-type gate: **fail the build
when an output model gains a field the inventory does not name.** That is the same derivation Blue
already accepted for M1's fencing test, so it is one mechanism serving two obligations - and this
time the "one mechanism, two problems" claim is actually true, because both are containment
questions over the same field set.

### R2-f - Blue's M2 answer is right and its scheduling is wrong.

Blue calls the MRTR-on-legacy spike "the highest-priority action out of this round" and then leaves
§7.5's discriminator unspecified pending it. That is correct sequencing for the *design*, but
DESIGN.md is stated to be "**Frozen at 0C/0H/0M, after which only a numbered ADR in `docs/adr/` may
change it.**" A section that says "to be determined by a spike" cannot be part of a frozen
document, and the alternative - freezing a discriminator that both readings show does not work - is
worse. **§7.5 is a freeze blocker and should be named as one**, not left as an accepted finding
with an action attached. Everything else in this round is text, a decision, or a CI gate. This one
is the only item that can hold the freeze, and it is cheap: no credential, an existing harness.

---

# BLUE ROUND - Final response

**R2-a - ACCEPT, definitively.** Terminate on the raw page length, never the deduplicated length.
This goes in §4.5 as its own sentence next to the existing termination rule, because Red is right
that leaving it implicit guarantees the bug. Concretely: `fetched = len(raw_items)` decides
termination; dedup applies to what is returned. And the §8 required-cases list gains an arm: a
paged scan whose second page repeats the boundary record still fetches page three.

**R2-b - ACCEPT, and the three-state policy is the correct one.** I priced the audit failure as
one decision and it is two, split by whether the POST has committed. Final policy for §5.3:

- **Pre-write audit failure on `create_candidate`:** fail closed, no POST.
- **Post-write audit failure on `create_candidate`:** return a **successful** result carrying an
  explicit warning field - the record exists, its ids are returned, the audit record did not
  persist - and raise the alarm server-side. Never a generic error, because Red is right that a
  model reading a generic error retries, and a retry here emails a second live human. This is the
  §4.3 no-retry rationale extended one layer up: the tool must not *invite* a retry either.
- **Read tools:** audit failure is logged and non-fatal.

And ACCEPT the §7.4 link: §5.3 will state that the audit event is emitted synchronously within the
invocation and never deferred to teardown, citing §7.4's rule by number. Red is right that the two
sections currently agree by accident.

**R2-c - ACCEPT.** The TTL is unspecified and the interaction is real. §7.6 gains: a stated default
TTL sized against approval latency rather than against replay risk (approval is minutes; replay
protection comes from single-use, not from a short clock); the clock starts at preview and is not
refreshed; and expiry-after-approval is called out in the README next to §7.5's abandonment note,
because they are the same integrator's bad afternoon. I will note the honest tension: a longer TTL
widens the window in which a token is stealable, and single-use plus HMAC-binding-to-payload is
what carries that, not the clock.

**R2-d - ACCEPT, and I take the harder branch: the cache is conditional.** Red's inert-surface
argument is right, and dropping the cache outright would be the easier answer and the wrong one -
`get_job_feed` is the highest-volume, lowest-churn, entirely-public surface in the design and it is
the natural thing to cache. So `ResponseCaching` is constructed only when at least one job tool is
enabled. That makes it the **first** concrete consumer of the per-tool enable surface M9 says does
not exist, which is useful: it turns R2-d/M9's missing table from a documentation debt into a
structural requirement with a caller.

**R2-e - ACCEPT.** The gate is the point and I would have shipped the file without one. §10's CI
list gains: fail the build when an output model declares a field the inventory does not name. And
Red is right that this is the same derivation as M1's fencing test over the same field set, so it
is one generator with two consumers - the fencing paths and the inventory rows. I will keep the
"one mechanism" language out of §2.1 this time and put it where it is actually true.

**R2-f - ACCEPT, and this is the correct final disposition.** §7.5 is a freeze blocker. I will not
freeze a document whose approval branch has two readings, one inert and one wrong, resting on a
premise with no arm in the spike. Everything else in this round resolves into text, a decision, or
a CI gate that can be written today. This one needs an execution I have not done and can do
without a credential.

**On the four Phil nominated that I have not restated:** claim 1 (the probe) is confirmed broken
in both the way he suspected and one he did not (C1, C2). Claim 2 (audit failure) is confirmed
absent and now decided in three states (M3, R2-b). Claim 3 (one mechanism, two problems) is
confirmed - they are two mechanisms and two allow-lists, and the elegance was doing the arguing
(M1). Claim 4 (the capability check) is confirmed worse than unreliable - inert - and is the
freeze blocker (M2, R2-f). Claim 5 (the `mcp` pin) is confirmed not merely unexecuted but not
written down (C4). Claim 6 (rewrite loss) is confirmed with five named instances, all of them
minors, one of them a reverted decision rather than a dropped line (M9). **All six of Phil's
self-nominated weak claims were weak. That is a good hit rate and it is worth saying so: naming
them is what made this round efficient.**

---

# Final report - every decision

| # | Finding | Severity | Decision | Survives? |
|---|---|---|---|---|
| C1 | §4.5's "identical ids ⇒ either base is safe" is wrong; clamping protects only page 1 | CRITICAL | **ACCEPTED.** Identical ⇒ 1-based. No "either is safe" branch. Add the duplicate-per-boundary consequence | No - text fix |
| C2a | Probe assumes a stable order §9 says does not exist | CRITICAL | **ACCEPTED.** Probe with `count=2`, compare id **sets**; overlapping sets ⇒ indeterminate | **Yes (h)** - remains unverified |
| C2b | An indeterminate probe caches a verdict; no indeterminate state defined | CRITICAL | **ACCEPTED.** Never cache indeterminate. Safe default base 0 + dedup by `eId` (duplicates are visible, skips are not) | No - resolved |
| C2c | Probe not scoped per resource; `/v1/jobFeed` is `[OFFICIAL]` 1-based | CRITICAL | **ACCEPTED.** Cache per `(api_version, resource)`; never probe a documented base | No - resolved |
| C3 | §6.2 claims the GDPR standard is `priority: optional`; `gdpr-data-rights.md:9` says `required` | CRITICAL | **ACCEPTED.** Delete the claim; re-ground ADR-0008 on **scope**; add `docs/data-inventory.md` per `:119-129` | No - resolved |
| C4 | §10 claims `mcp` is pinned; §10's verbatim block does not pin it | CRITICAL | **ACCEPTED.** Add `mcp==2.1.1`. `fastmcp inspect` diff becomes a real CI gate with a committed baseline | No - text + CI |
| M1 | "Single mechanism" merges containment and fencing; two allow-lists in two key spaces | MAJOR | **ACCEPTED.** Drop the claim. Generate fencing paths from output models; add the "every field has a fencing decision" test | No - resolved |
| M2 | §7.5's `input_responses`-exists check is inert; MRTR-on-handshake-era has no spike arm | MAJOR | **ACCEPTED.** Spike `mode="legacy"` (no credential needed). **Freeze blocker** per R2-f | **Yes (h)** - needs execution |
| M3 | Audit-failure policy absent; `approval_state` / ContextVar / trace id missing; *who* is unrecordable | MAJOR | **ACCEPTED.** Three-state policy (R2-b). Cite `agent-guardrails.md:121-123`. **ADR-0009** for the unrecordable approver | No - decided |
| M4 | §1's no-state claim false; candidate PII cached with no key/TTL/eviction stated | MAJOR | **ACCEPTED.** Cache scoped to job tools only; §1 rewritten | No - decided |
| M5 | §2.2 and §7.6 disagree on whether the token is always required | MAJOR | **MODIFIED.** Always required. TTL specified, clock starts at preview (R2-c) | No - decided |
| M6 | One recorded 200 exists (`JOBVITE-API.md` §6.1); §1.1 and §8 say none does | MAJOR | **ACCEPTED.** Reword §1.1; third fixture tier (structurally-confirmed); close §11 q4 | No - text fix |
| M7 | No outbound throttle, no 429 handling, against an `[OFFICIAL]` once-a-day cadence | MAJOR | **ACCEPTED**, remedy scoped. Outbound ceiling + 429→503 + `Retry-After`. **Cadence acceptability is commercial** | **Yes (h)** - external |
| M8 | 409 duplicate-candidate absent from §9 and the write path | MAJOR | **ACCEPTED.** Hazard 7, distinct problem slug, state that no client-side dup check exists | No - text fix |
| M9 | Five R1-accepted items lost in the rewrite; m3 **reverted** to the rejected wording | MAJOR | **ACCEPTED all five**, plus m3 below as a sixth | No - restore |
| M10 | Single-process is load-bearing for two controls and never stated | MAJOR | **ACCEPTED.** One sentence in §7.1 + ADR-0002 consequences | No - text fix |
| m1 | v2 page cap `[INFERRED]` presented as fact | MINOR | **ACCEPTED** | No |
| m2 | httpx2 **inverts** rather than removes the exception hazard | MINOR | **ACCEPTED.** Correct the sentence; scope the catch to the call site | No |
| m3 | §4.4's limiter numbers are sequential, single-client measurements | MINOR | **ACCEPTED.** Carry the spike's caveat. Sixth M9 item | **Yes (m)** - unverified |
| m4 | Probe costs two extra requests against a once-a-day envelope | MINOR | **MODIFIED.** One sentence + pointer to the override | No |
| m5 | Capped result + no stable sort ⇒ non-deterministic `showing 50 of 1,240` | MINOR | **ACCEPTED** | No |
| R2-a | Dedup breaks the short-page termination rule | MAJOR (new) | **ACCEPTED.** Terminate on **raw** page length; add the test arm | No - resolved |
| R2-b | Post-write audit failure reported as an error invites a duplicate write | MAJOR (new) | **ACCEPTED.** Three-state policy; success-with-warning after commit | No - decided |
| R2-c | Mandatory token + hanging approval = expiry after a human approved | MAJOR (new) | **ACCEPTED.** TTL sized to approval latency; single-use carries replay | No - decided |
| R2-d | Cache scoped to job tools is unreachable in a candidate-only deployment | MAJOR (new) | **ACCEPTED.** Cache constructed conditionally; first consumer of the missing enable surface | No - decided |
| R2-e | The new data inventory has no gate, which is how M9's items died | MAJOR (new) | **ACCEPTED.** CI fails when an output model field is not in the inventory | No - CI gate |
| R2-f | §7.5 cannot be frozen with an unspecified discriminator | MAJOR (new) | **ACCEPTED.** Named as the freeze blocker | Folded into M2 |

## Verdicts on Phil's six self-nominated weak claims

1. **The `start`-base probe** - **BROKEN, two ways.** Its "identical" branch draws the opposite of
   the correct conclusion (C1), and its premise contradicts §9's own no-stable-sort hazard (C2a).
   Both of Phil's guesses were right and there is a third he did not name: it caches an
   indeterminate result (C2b) and applies one verdict across resources whose bases differ (C2c).
2. **Audit-write failure** - **ABSENT, confirmed.** Now a three-state policy, and R2-b found the
   state that matters most: post-commit failure must not be reported as an error.
3. **One mechanism for two problems** - **CONFIRMED SUSPICION.** Two mechanisms, two allow-lists,
   two key spaces, and no artefact owning their correspondence. The elegance was the argument.
4. **The `ctx.input_responses` capability check** - **WORSE THAN UNRELIABLE: inert.** Both readings
   fail, and the premise beneath it has no arm in the spike. The freeze blocker.
5. **`mcp` pinning + `fastmcp inspect`** - **NOT MERELY UNEXECUTED: the pin is not in the file.**
   §10's own verbatim block, presented as load-bearing, omits it. The inspect diff is a review aid
   the text calls a control.
6. **Rewrite loss** - **CONFIRMED, five instances**, all minors, one a reverted decision (m3).
   Every CRITICAL and MAJOR from R1 landed, several strengthened well past what was agreed. The
   rewrite is lossy at exactly one altitude, and knowing that is more useful than the five items.

## Surviving count

Surviving = no resolution was agreed, or the resolution depends on an execution or a person
outside this review. Same convention R1 used.

- **Critical: 0.** C1-C4 all reached agreed, credential-free resolutions.
- **High/major: 3.**
  - **C2a** - the probe's soundness. Mitigated (id-set comparison, indeterminate state, safe
    default) but **still unverified against a live server**, which needs a credential and is
    therefore not actionable here. This is "unverified", not "wrong" - the distinction matters and
    the mitigation makes the unverified case safe rather than merely honest.
  - **M2** - §7.5's era discriminator. **This is "wrong", not "unverified"** - both readings fail
    on inspection. It survives because the fix depends on a spike arm that has never been run.
    **Needs no Jobvite credential.** Freeze blocker.
  - **M7** - Jobvite's cadence envelope. The client-side remedy is agreed and specified; whether
    the resulting call rate is acceptable under a deploying customer's Jobvite agreement is a
    commercial judgement outside this review, in the same way R1's M2 was a legal one.
- **Minor: 1.**
  - **m3** - the limiter's numbers are sequential, single-client measurements. The spike itself
    names concurrency as "the case that matters in production". Minor because the remedy is a
    caveat and the concurrency test is small.

**`0c / 3h / 1m`**

Everything else was accepted, modified or decided within the round and is text work on
`DESIGN.md`, `DECISIONS.md`, two ADR changes (0009 new, for the unrecordable approver; 0008
re-grounded), one new artefact (`docs/data-inventory.md`), and three CI gates.

---

# What I did NOT review, and why

- **The B1-B106 conformance sweep.** Explicitly excluded by the brief and running in parallel. The
  standards findings here (C3, M3, M7, M8, M9's m7) surfaced from sections I was attacking for
  other reasons, not from a sweep. **There are certainly more.** In particular I opened the
  frontmatter of thirteen standards files and found `ai/resilience.md`, `ai/output-handling.md`,
  `ai/cost-token-controls.md` and `ai/llm-observability.md` are all `priority: required` and
  **none of the four is cited anywhere in DESIGN.md**. I read only the sections of the first and
  fourth that bore on §4.3 and §5.3. `ai/output-handling.md` in particular has a "Sensitive Output
  (LLM02)" section and a "Structured Output" section that look directly relevant to §6 and §2.1
  and which I did not open.
- **`architecture/authentication.md`, `architecture/security.md` and `architecture/threat-modeling.md`
  beyond frontmatter.** §7.2's `StaticTokenVerifier` design - shared secrets from environment, no
  expiry, no rotation, no revocation - is the obvious place a required auth standard would bite and
  I did not check it. Flagging the shape, not the finding.
- **`COMPLIANCE-SPEC.md` and `STANDARDS.md`.** Not opened at all this round. R1 used
  `STANDARDS.md`'s B-numbering; I deliberately went to the standards files directly instead, which
  is how C3 was found - `STANDARDS.md:683` is cited in R1's M4 decision as ruling the GDPR
  machinery non-binding, and the primary source says otherwise. **Someone should check whether
  `STANDARDS.md:683` is the origin of C3's error**, because if it is, every other conclusion drawn
  from that line is suspect too. I did not do it, and it is a ten-minute job with a real chance of
  a second finding.
- **`FASTMCP.md`** (51KB) - targeted greps only, for the middleware scoreboard.
  **`FASTMCP-SPIKE-4.md`** §§1-5, 7-12, 16, 18 - skimmed via headings, read only where a design
  claim pointed at them. §16's confirmation-token attack arms in particular I read only through its
  §16.4 summary; if §7.6's design diverges from what §16.2 actually ran, I would not have caught it.
- **`JOBVITE-CONTRACT.md`** (32KB). Not opened. R1 cited it at `:152` and `:666`; I worked from
  `JOBVITE-API.md` instead. The contract document is the more likely home of a mismatch with §4.2's
  error rule and §9's hazard list, and it is the single largest gap in this round.
- **`DECISIONS.md` D1-D17 in full.** Read headings and the entries the design cross-references. A
  decision recorded there and silently contradicted by revision 2's rewrite would not have been
  caught, which is the same class of loss as M9.
- **`fast-mcp-jira`.** Not opened at all. The design does not reference it anywhere in revision 2,
  so there was nothing to check. R2-b cites R1's own finding about it as a *pattern* only.
- **`src/` and `tests/`.** Still effectively empty. Correct for a design round.
- **Anything requiring a live Jobvite call.** No credential, no sandbox (`api-stg.jobvite.com`
  fails DNS). C2a's residual, §11's five open questions and every success-shape question are
  unresolvable here by construction. **I have recommended no action that requires calling Jobvite.**
  Note the contrast with M2, which is the opposite case: an execution nobody has run that needs no
  credential at all, only the stub harness §17 already built.
