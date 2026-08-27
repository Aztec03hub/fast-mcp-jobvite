# DESIGN.md - Adversarial review, round 1

**Reviewer:** `design-review-r1` (both lenses, one agent). **Date:** 2026-08-27.
**Target:** `docs/DESIGN.md` @ 349 lines, "DRAFT, under review", last updated 2026-08-27 02:23 PM CDT.
**Also in scope:** `docs/reviews/PENDING-DESIGN-CHANGES.md` (P1-P17), treated as agreed-but-not-sanctified.

**Evidence base actually opened by me:** `docs/DESIGN.md`, `docs/DECISIONS.md`,
`docs/CREDENTIAL-CHECKLIST.md`, `docs/reviews/PENDING-DESIGN-CHANGES.md`,
`docs/research/JOBVITE-CONTRACT.md` (targeted), `docs/research/JOBVITE-API.md` (targeted),
`docs/research/STANDARDS.md` (targeted), `docs/research/COMPLIANCE-SPEC.md` (targeted),
`docs/research/FASTMCP.md` (targeted), `docs/research/FASTMCP-SPIKE-4.md` (targeted),
`docs/research/fixtures/*`, the standards corpus files cited below, and the
`fast-mcp-jira` reference at `src/fast_mcp_jira/`. See §"Not reviewed" at the end for what
I did not open and why.

Marking: **[STD]** cited clause with `file:line`. **[REASONED]** my inference, not a citation.
**[ABSENT]** the design does not address it - a first-class finding.

---

# RED ROUND 1 - Adversarial review

## The five that matter most

**C1, C2, C3, C4, M1** below. C3 is the one that will bite this week; C1 and C2 are the two
places where the design claims compliance it has not designed.

---

## CRITICAL

### C1 - The "health endpoint" that ADR-0003's compliance argument rests on is specified nowhere. [ABSENT]

`DESIGN.md:194-196` states:

> "That clause is violated in the letter and no implementation can satisfy it: **ADR-0003**.
> Where a real HTTP surface exists - the health endpoint and transport-level auth rejections -
> `problem+json` is applied properly."

This is the sentence that converts ADR-0003 from "we ignore a `priority: required` clause" into
"we honour it everywhere we can". It names two surfaces. One of them does not exist in this
design.

- `DESIGN.md:78-88` (§3 module layout) has no health module and no health route.
- `DESIGN.md:200-232` (§7 server, transport, configuration) describes transport selection,
  auth, config and middleware. It never mentions a health endpoint.
- `DECISIONS.md` D6 makes the identical claim and likewise never specifies one.
- The claim is inherited from `STANDARDS.md:564` and `COMPLIANCE-SPEC.md:463`, which both say
  `problem+json` applies to "genuine HTTP surfaces (health endpoint, transport-level auth
  rejections)". The research asserted the surface conditionally; the design promoted it to a
  fact without building it.

So the design mitigates a required-standard deviation with a component it does not contain.
Either specify the health endpoint (route, response shape, what it checks, whether it probes
Jobvite, whether it is exposed on stdio at all - it cannot be) or delete the clause and let
ADR-0003 stand on the transport-level auth rejections alone. **Not both.**

Secondary: nothing in the design says whether a health endpoint would be reachable without a
token. An unauthenticated health check that probes Jobvite is an unauthenticated liveness
oracle for someone else's ATS credential.

### C2 - B17, per-invocation tool logging, is absent, and `request_id` is used without ever being defined. [ABSENT] [STD]

`ai/agent-guardrails.md:40` **[STD]**:

> "- Mandatory audit logging of every tool invocation"

`STANDARDS.md:175-186` renders this as **B17**, citing `ai/tool-calling.md:171-173` and
`ai/agent-guardrails.md:121-123`:

> "**Log every tool invocation** with: tool name, validated arguments (PII redacted), result
> status, latency, the approval decision if gated, and the request correlation id."

and `ai/tool-calling.md:178-179`:

> "Tool logs are wire-shaped **snake_case** (`tool_name`, `request_id`, `result_status`) and
> never contain secrets or raw credentials."

`STANDARDS.md:184-186` adds, in the research's own words: *"PII redaction is not discretionary
here - Jobvite tool arguments and results are candidate personal data."*

What the design provides, `DESIGN.md:229-231` (§7):

> "**Middleware:** timing and structured logging, with `include_payloads` left at its default
> `False` - for this server those payloads are candidate PII."

That is the opposite of B17, not a satisfaction of it. B17 requires the validated arguments to
be logged **with PII redacted**. The design logs no arguments at all. That is defensible as a
privacy posture but it is a deviation from a `priority: required` clause and it is undeclared -
there is no ADR for it in `DESIGN.md:341-349` (§12) and no row in `DECISIONS.md`. Under the
project's own standing rule (an in-scope numbered ADR is the only thing that overrides a
standard), this is drift.

Compounding it: **`request_id` is load-bearing and undefined.** `DESIGN.md:189-192` (§5) puts
`request_id` in every RFC 9457 problem object and builds `instance` out of it
(`urn:fast-mcp-jobvite:invocation:<request_id>`). Nowhere does the design say where a
`request_id` comes from on an MCP transport that has no `X-Request-ID` middleware
(`architecture/observability.md:160-195` assumes exactly that HTTP middleware, which does not
exist here), whether it is generated per tool call or per connection, whether it is propagated
into the Jobvite request, or whether it appears in any log line. A correlation id that
correlates nothing is decoration.

Three concrete gaps: (a) no per-invocation log event is designed; (b) no argument-redaction
design exists for the case where arguments *are* logged; (c) `request_id`'s origin and
propagation are unstated.

### C3 - P17 cuts `create_candidate`, and its blast radius is not chased. Applied as staged, DESIGN.md contradicts itself in seven places.

I accept P17's decision (see the BLUE round - I think it is correct and well-argued). This
finding is not about the decision. It is about the fact that P17 states a conclusion and does
not enumerate the text it invalidates. The project's own standing rule is that a fix must
rewrite the prose, not sit beside it - otherwise round 2 re-finds the stale half.

Sections that become false or orphaned the moment P17 is applied:

1. **`DESIGN.md:44`** - *"Five tools."* Becomes four.
2. **`DESIGN.md:48-54`** - the tool table's `create_candidate` row, and the "Kind" column's only
   `write, destructive, default-denied` entry.
3. **`DESIGN.md:66-77`** (§2.2, entire subsection) - `JOBVITE_ENABLE_WRITES`, the `send_email`
   default, `destructiveHint`. All of it describes a tool that no longer ships. Note the env var
   `JOBVITE_ENABLE_WRITES` also appears nowhere else; if it is deleted, say so, because a
   half-removed feature flag is how a write tool comes back by accident.
4. **`DESIGN.md:143-144`** (§4.3) - *"`create_candidate` is never retried under any condition."*
   The rule is still correct for v1.1 and for the client-internal retry design (P13), but as
   written it references a tool that does not exist.
5. **`DESIGN.md:200-218`** (§7, auth) - this is the serious one. The design's entire
   justification for scoped `StaticTokenVerifier` auth is *"a read-only token never sees
   `create_candidate`"* (`DESIGN.md:214`). With four read tools and no write, **there is no
   scope distinction left to make.** Either the design states what scopes now separate (nothing?
   candidate-PII reads versus job reads?), or the scoping story and its "confusing failure mode"
   README obligation are solving a problem v1.0 does not have.
6. **`DESIGN.md:257-266`** (§8, required cases) - two of the six named merge-gating tests lose
   their subject: *"`create_candidate` not retrying on timeout"*, and *"the `eId`/`EId` casing
   asymmetry"*. Per `JOBVITE-CONTRACT.md:244` the lowercase `eId` is what reads return; the
   uppercase `EId` occurs **only on the create response**. With no create tool, there is no
   `EId` in our code to pin. The test either becomes vacuous or must be re-scoped to "reads
   normalise `eId`", which pins nothing about the asymmetry.
7. **`DESIGN.md:277-279`** (§9 hazard 1, casing asymmetry) and **`DESIGN.md:300-306`** (§11 open
   questions) - both are framed around the create path.

Additionally: `DESIGN.md:56-59` justifies splitting `search_candidates` / `get_candidate` by
citing `ai/tool-calling.md`. That survives. But `DESIGN.md:61-64`'s exclusion of
`POST /api/v2/task` is now argued on different grounds than the exclusion of
`create_candidate`, and a reader will reasonably ask why one write is excluded for cost and the
other for safety. Say both reasons once, together.

**This is DEALBREAKER-adjacent for the freeze, not for the design.** The design is not wrong;
it is about to become internally inconsistent, and the freeze criterion is 0C/0H/0M against a
document that must be self-consistent to be freezable.

### C4 - §4.5's `start`-base mitigation is a disclosure strategy, not a detection strategy. A runtime probe exists and was not considered. [REASONED]

`DESIGN.md:169-171`:

> "**`start` is 1-based, and this is an assumption, not a fact.** [...] If we are wrong, we
> silently skip the first record of every page - a correctness bug that no test built on
> synthetic fixtures can catch."

The design's own words identify the defect class precisely: silent, per-page, invisible to the
test suite. It then offers three mitigations (`DESIGN.md:173-180`): configurable via
`JOBVITE_PAGINATION_START_BASE`, logged once at startup, stated in the README and on the
checklist.

**All three require the user to already suspect the bug.** A configuration knob helps someone
who knows the answer. A startup log line saying "assuming 1-based" is read by nobody. A README
paragraph is read once, before the bug matters. None of them *detect* anything. The design has
converted an unresolved unknown into documentation and called it mitigation.

The detection strategy: **the server can settle it at runtime, itself, on any deployment that
holds a credential - which is every real deployment.** `CREDENTIAL-CHECKLIST.md` row 2 already
specifies the exact experiment:

> "`GET /api/v2/candidate?count=1&start=0` versus `&start=1`, comparing returned `eId`s"

That is two cheap requests. Run them once per process, on the first paged call rather than at
boot (so a server that is never used costs nothing, and so a Jobvite outage at boot is not
fatal):

- Different `eId`s returned -> the API is 0-based and our 1-based assumption is skipping record
  one on every page. Log at ERROR, and either self-correct or refuse to page.
- Identical `eId`s -> either 1-based or the server clamps `0 -> 1`. Both are safe under our
  assumption. Proceed.
- Probe errors, or `start=0` is rejected -> fall back to the configured value and log. Benign.

`JOBVITE-CONTRACT.md:189` reaches the same interim recommendation the design took, but frames it
as *"Gate on checklist row §13.2 before trusting any full-catalogue sync"* - a gate on a human,
which is what the design implemented. The runtime probe moves the gate into the software.

**[REASONED], and I flag its limit honestly:** I cannot verify this probe against live Jobvite,
because nobody on this project can. What I can assert is that the design does not mention it,
does not reject it, and its three stated mitigations detect nothing. Phil's own suspicion in the
brief - "that may be rationalising an unresolved unknown rather than mitigating it" - is
correct.

---

## MAJOR

### M1 - The stated defence against the incident that already happened would not have caught it. [ABSENT]

`DESIGN.md:334-338`:

> "**Secret scanning also runs pre-commit**, deliberately exceeding the standard, which mandates
> it only in CI. On a public remote a pushed secret is compromised the instant it lands [...]
> This repository has already had one incident of the adjacent class."

The incident was a vendor PDF stamped `CONFIDENTIAL - Jobvite Data Services`
(`JOBVITE-API.md:44`) reaching a public repo and requiring a history rewrite. **TruffleHog and
pre-commit secret scanning detect credentials. They do not detect confidential documents.** A
PDF with no API key in it passes every scanner named in §10, in CI and pre-commit alike.

The design names a control, cites a real incident as its justification, and the control does not
cover the incident. That is worse than having no control, because it reads as covered.

What is [ABSENT]: any third-party-source handling policy at all. `JOBVITE-API.md:44` and `:90`
show the research team got this right by hand - the PDF is linked to a Wayback URL and
explicitly "**NOT committed**" - but that discipline lives in a research document, not in the
design, and nothing enforces it. A cheap enforceable control exists: a CI/pre-commit gate that
refuses any binary or document file (`*.pdf`, `*.docx`, `*.xlsx`, images outside a declared
`docs/assets/` path) unless explicitly allow-listed. That is a file-extension check, not a
scanner.

### M2 - Verbatim excerpts of the purged CONFIDENTIAL document are still in the public repository.

The artifact was purged from history. Its content was not.

- `JOBVITE-CONTRACT.md:185` quotes it directly: *"`[OFFICIAL]` v1 PDF | 1-based: *"Default start
  index: 1"*, and *"you would add start=501&count=500"*"*.
- `JOBVITE-API.md:549` quotes its parameter table and adjudicates a typo in it.
- `JOBVITE-API.md` §15.2 is referenced from `JOBVITE-CONTRACT.md:163` as holding the *"Full v1
  numeric catalogue (100-108, 201-208)"* - a substantial reproduction of the document's content
  rather than a short citation.
- `JOBVITE-CONTRACT.md:627` reasons from *"the PDF excerpt available to me"*.

`JOBVITE-API.md:44` states the source has **"No redistribution grant"** and is stamped
CONFIDENTIAL on all 8 pages. Removing the container while retaining transcribed excerpts is a
distinction that will matter to exactly one audience, and that audience is Jobvite's counsel.

I am not asserting this is unlawful - I am not qualified to and short factual quotation of an
API parameter is a weak claim for anyone to press. I am asserting that **it is currently
undecided**, in a public repo, after an incident of the same class, and that the design is
silent on it. `DESIGN.md:328-338` (§10) covers licensing gates for dependencies
(`pip-licenses` allow-list) and says nothing about the licensing of the *sources this project
was built from*. Decide it deliberately: either the excerpts are defensible and a note in
`JOBVITE-API.md` §0 says why, or they are paraphrased down to facts. Facts about an API are not
copyrightable; the document's prose is.

### M3 - §6's default-untrusted allow-list is under-specified in the two ways that decide whether it can be built.

`DESIGN.md:245-249`:

> "The field inventory lives in `JOBVITE-CONTRACT.md` and is enforced by an allow-list in
> `utils/redaction.py`: a response field not on the known-safe list is treated as untrusted by
> default, so a new Jobvite field arrives fenced rather than raw."

Phil's stated worry - that this is not implementable without knowing the full response schema -
is **wrong, and for a good reason**: not knowing the schema is precisely what default-deny is
for. An allow-list of known-safe names is enumerable today from
`JOBVITE-CONTRACT.md:239-256`; everything else falls through to fenced. The mechanism is sound.

The real gaps are two, and both are load-bearing:

**(a) Name-keyed or path-keyed?** The design says "field", which is ambiguous, and the two
readings fail differently. Name-keying collides: `title` appears both as `candidates[].title`
(`JOBVITE-CONTRACT.md` field map) and as `candidates[].application.job.title`
(`fixtures/candidate_list_success.json`). `eId` appears at three depths - candidate,
application, job. A name-keyed allow-list that marks `title` safe marks both safe, including a
recruiter-authored job title. Path-keying fixes that but cannot express
`candidates[].application.customField[]`, which is an open-ended array of customer-defined
keys (`fixtures/candidate_list_success.json` shows `"customField": []`) whose contents are by
construction unknowable in advance. Path-keying therefore needs a wildcard rule, and the design
does not state one.

**(b) What does "fenced" mean for a non-string?** Fencing is a text operation. An unknown field
arriving as an array, an object, a number or `null` cannot be wrapped in delimiters without
first being stringified, which changes the tool's output schema for that field. The design
mandates typed Pydantic output (`DESIGN.md:80-84`, §2.1) and `strict=True`. A default-deny rule
that stringifies unknown structures and a strict output model are in direct tension, and the
design does not resolve it.

Neither gap kills the approach. Both must be decided before someone writes `redaction.py`, and
whoever writes it will otherwise decide them by accident.

### M4 - Candidate special-category data flows to the model, and the design has no position on it. [ABSENT] [REASONED]

`fixtures/candidate_list_success.json` - the project's own hypothesis of a success body -
contains, per candidate application:

```
"gender": "Undefined", "race": "Undefined", "veteranStatus": "Undefined"
```

These are EEO fields. `DESIGN.md:236-252` (§6) treats candidate content exclusively as an
*injection* risk. `DESIGN.md:229-231` (§7) keeps PII out of *logs*. **Nothing in the design
addresses what is returned to the model**, which is the only place this data actually goes.

I am careful about the standards claim here, because it is weaker than it looks:
`STANDARDS.md:683` rules `architecture/gdpr-data-rights.md` **non-binding** for this repo -
*"Its obligations attach to systems that **store** personal data [...] This server is stateless
and stores nothing"* - leaving only B88, which is the no-PII-in-logs rule the design already
satisfies. So **this is not a standards violation.** It is an uncovered gap, and the corpus
being silent is why it needs a design decision rather than a citation.

The decision to take: does `search_candidates` return `gender` / `race` / `veteranStatus` in its
tool output at all? A recruiting connector that hands protected-class attributes to a language
model, for a caller who did not ask for them, is a product risk that will be raised by the first
enterprise legal review this repo meets - and `DECISIONS.md` D7 says enterprise legal review is
a realistic adoption gate we deliberately optimised the licence for. Drop them from the output
model by default; the four read tools lose nothing.

### M5 - The result-size bound is stated in two places with two different numbers and no stated relationship. [STD]

- `DESIGN.md:167` (§4.5): *"max page size 500 on v2 and 1000 on `/v1/jobFeed`"*.
- `DESIGN.md:226-228` (§7): *"Response size is bounded inside each tool instead: a page is
  capped and the result says `showing 50 of 1,240`"*.

Undefined: whether a caller requesting `count=500` causes us to fetch 500 candidate records
(500 candidates' PII, over the wire, into process memory) and return 50. If so, the bound is a
display bound, not a resource bound, and 90% of the retrieved personal data is fetched for
nothing.

**[STD] B15**, `STANDARDS.md:161-166` citing `ai/tool-calling.md:153-155`: *"**Bound result
size** before returning it to the model (truncate to a documented max)"*, with the research's
own fail condition: *"The max must be **documented**, not merely present in code."* The number
50 appears once, inside an illustrative output string. That is not a documented maximum.

**[STD] B22**, `STANDARDS.md:225-228` citing `ai/agent-guardrails.md:106-107`: *"Bounds are
configuration, not constants buried in code"*, and `STANDARDS.md:228` explicitly scopes this:
*"Applies to B15's result cap, timeouts, and retry budgets."* The design does not say the cap is
configurable.

Three things to state: the cap's value, that it is configuration, and whether it bounds the
fetch or only the return.

### M6 - stdio auth: the threat model is probably right, and the design does not state it. [ABSENT]

Phil's weak claim 2, assessed directly.

`DESIGN.md:206-218` (§7) describes auth entirely on the HTTP surface. stdio is mentioned only as
the default transport (`DESIGN.md:202`). The word "auth" and the word "stdio" never appear in
the same paragraph.

**Post-P17, the threat model is defensible and I would not block on it.** A stdio caller has
already spawned the process and therefore already controls the environment that holds
`JOBVITE_API_KEY`; authenticating them to a credential they supplied is theatre. All four
remaining tools are reads. This is the correct answer, and the design should simply say it.

**The finding is what happens next.** `PENDING-DESIGN-CHANGES.md` P17 says *"`create_candidate`
returns in v1.1, gated on [...] a HITL mechanism that actually exists."* On stdio there is no
token, no scope, no `StaticTokenVerifier`, and - per P17's own executed evidence - no
elicitation on the sessionless era. So **v1.1's write tool cannot be reintroduced on the default
transport at all** under any mechanism currently known to this project. That constraint is worth
recording now, while the reasoning is fresh, rather than rediscovering it in v1.1 planning. If
it is not written down, the likely v1.1 outcome is a write tool gated by an env var on stdio -
which is exactly the control P17 just rejected.

### M7 - The SIGTERM mitigation in P1 is asserted, not executed, and its correctness depends on ordering that is not stated. [REASONED]

`PENDING-DESIGN-CHANGES.md` P1 stages:

> "`__main__.py` installs the mitigation explicitly, one line, with a comment pointing at the
> upstream issue: `signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))`"

The finding it mitigates was executed 3-of-3 with `/proc/<pid>/cmdline` verification. **The
mitigation was not.** P1's own framing is "Changes to make", and every other item in that file
is explicit that it was executed. This one silently is not.

Two [REASONED] reasons to doubt the one-liner as written:

1. **Ordering.** `signal.getsignal(signal.SIGINT)` returns whatever handler is installed *at
   the moment the line runs*. If it runs before uvicorn starts, that is Python's default
   `default_int_handler`, and aliasing SIGTERM to it makes SIGTERM raise `KeyboardInterrupt` -
   which is plausibly what is wanted, but is a different mechanism from what the line appears to
   say. If it runs after uvicorn installs its own handlers, it copies uvicorn's SIGINT handler,
   which is again a different thing. And uvicorn's `Server.install_signal_handlers()` installs
   handlers for **both** SIGINT and SIGTERM during `run()` - so a handler installed before
   `run()` is overwritten by uvicorn, and the mitigation silently does nothing.
2. **stdio.** On the default transport there is no uvicorn at all. The mitigation's behaviour
   differs between the two transports and P1 does not say which one it was reasoned against.

This project has a documented pattern of predicted fixes landing on the wrong artifact. The
mitigation is one line and one spike run; it should not enter the design on reasoning when
everything around it was executed. Until it is, state the constraint (P1 already does, correctly
- nothing that must complete before connections close may live in a lifespan teardown) and mark
the one-liner unverified.

Corollary, and the more useful half: **if the mitigation does not work, what actually breaks?**
The design's only lifespan-teardown user is the httpx client pool (`DESIGN.md:33-34`: state is
*"an HTTP connection pool and a rate-limiter bucket"*). A leaked pool at process death costs
nothing - the OS reclaims the sockets. So the honest answer is that this constraint is currently
**free** for us, and the risk is entirely about what someone adds to teardown later. Say that.

### M8 - The httpx/httpx2 guard in P2 is a grep, and greps have holes. [REASONED]

P2's guard: *"A test asserts no `except httpx.` appears outside that module."*

That literal string misses at least three real forms:

- `except (httpx.ConnectError, httpx.ReadTimeout):` - matches, fine. But a tuple broken across
  lines puts `httpx.ConnectError` on a line with no `except`.
- `from httpx import HTTPError` then `except HTTPError:` - the string `except httpx.` never
  appears. This is the form a well-meaning contributor writes.
- `except HTTPError as e:` where `HTTPError` came from a shared `errors.py` re-export.

And the guard is one-directional. It confines `except httpx.*`, but says nothing about `httpx`
*types* crossing the module boundary - an `httpx.Response` in a function signature in
`tools/candidates.py`, or an `isinstance(e, httpx.HTTPError)` check, both leak the choice out of
the module the guard claims contains it.

Cheaper and tighter: assert on the **import graph**, not the text. No module outside
`services/jobvite_client.py` may import `httpx` at all. That is one AST walk, catches all three
forms above and the type-leak case, and is the actual invariant P2 wants ("the choice stays
reversible in one module"). The grep tests a proxy for the invariant; the import check tests the
invariant.

### M9 - §12's ADR list is stale against the staged decisions, and one staged item has no home. [ABSENT]

`DESIGN.md:341-349` lists ADR-0001 through ADR-0006. Against `PENDING-DESIGN-CHANGES.md`:

- **ADR-0007** (httpx over httpx2) is created by P2 and is not in §12.
- **ADR-0002's content changes materially.** §12 describes it as *"in-process rate limiting
  instead of the mandated Redis token bucket"*, and `DESIGN.md:156-160` describes a limiter we
  build. P9 replaces that with the framework's `RateLimitingMiddleware` plus a mandatory
  `get_client_id`. The deviation from `backend/rate-limiting.md:355-356` survives, so the ADR
  survives, but every sentence of its body changes - and P15 adds two constraints that belong in
  it: the limiter is not runtime-reconfigurable, and `limiters.clear()` is a quota amnesty and
  therefore a trivial bypass for anyone who can trigger a config reload.
- **P15's contractual gap has no home.** A rate-limit refusal raises `MCPError`, a JSON-RPC
  protocol error, and therefore **carries no RFC 9457 problem object**. `DESIGN.md:186-188` (§5)
  says failures return a problem object, flatly, with no exception. That is now false for one
  class of failure. Either §5 states the exception or ADR-0002 does; currently neither does.
- **ADR-0004's evidence gets stronger and should be updated.** P5 upgrades it from "we observed
  a bug" to "a merged upstream fix regressed when `mcp` major-versioned underneath it", with
  issue and PR numbers. That is a materially better ADR.
- **P17 needs a recorded decision even though it is correctly *not* an ADR.** P17 argues
  persuasively that an ADR waiving a required safety control should not exist. Agreed. But
  "we cut a planned capability, here is why" still has to be recorded somewhere a future
  maintainer will find it - `DECISIONS.md` as D17, and `DESIGN.md` §11. Otherwise the cut looks
  like an oversight, which is the exact failure mode `DECISIONS.md` D10 was written to avoid.

### M10 - The live-credential suite is designed to exist and not designed to stay alive. [ABSENT]

`DESIGN.md:255` and `DECISIONS.md` D12: credential-dependent tests are *"excluded by selection
rather than marked `skipif`"*, satisfying `architecture/testing-strategy.md`'s zero-skip rule.
The reasoning is sound and I have no quarrel with it.

What is [ABSENT] is the mechanism and its upkeep. The design does not say what the selection is
(a directory? a marker plus `-m "not live"`? a separate `pytest.ini`?), and it does not say that
the excluded suite is ever collected. A suite that CI never imports rots invisibly: it drifts
out of sync with the client's API, and the day a credential finally lands - the single event the
entire `CREDENTIAL-CHECKLIST.md` is built around - it does not run.

One line fixes it: CI runs `pytest --collect-only` over the live suite, so import errors and
signature drift fail the build while execution stays excluded. Zero skips preserved, zero
network, and the suite is guaranteed to at least start on day one.

---

## MINOR

**m1.** `DESIGN.md:8` lists `docs/research/FASTMCP-SPIKE.md` in the evidence base. **That file
does not exist**, in the working tree or in any commit (`git log --all -- ` returns nothing for
that path; the two commits touching a similarly-named file are for `FASTMCP-SPIKE-4.md`). The
real artifacts are `FASTMCP.md` and `FASTMCP-SPIKE-4.md`. A design that cites a nonexistent
evidence file undercuts every other citation in it.

**m2.** `DESIGN.md:303` (§11 item 2): *"The `start` base. One call settles it."* It is two calls
- `CREDENTIAL-CHECKLIST.md` row 2 and `JOBVITE-CONTRACT.md:666` both specify `start=0` **versus**
`start=1`, compared. A single call settles nothing, because there is no reference to compare it
against. `DESIGN.md:178-180` makes the same "one call" claim.

**m3.** `DESIGN.md:152-155` (§4.2) commits to parsing HR-XML with `defusedxml`. Per
`JOBVITE-CONTRACT.md:152` the HR-XML shape is `[OFFICIAL]`-provenance and was seen on
`/v1/candidate` - **not one of the four endpoints we call**. So the design carries a dependency
and a parse branch for a route it never invokes. Either cite the path by which HR-XML can reach
our four endpoints, or demote it: the parser should not *assume* JSON (correct, and
`JOBVITE-CONTRACT.md:154` proves it with a `Content-Type`-less 401), but the specific XML branch
is currently speculative surface. Keeping `defusedxml` as a hardened fallback is fine; presenting
it as a handled case is not.

**m4.** `DESIGN.md:76` annotates the write tool `destructiveHint: true` and the reads
`readOnlyHint: true`. MCP tool annotations are **hints to a client**, not enforcement - a client
is free to ignore them. The design should say this once, plainly, so nobody downstream reads the
annotation as a control. (Moot for `create_candidate` under P17; still live for the four reads.)

**m5.** `DESIGN.md:186-188` (§5) maps `status` to *"400 for input validation, and 503 for an
upstream 5xx"*. The circuit breaker (`DESIGN.md:146-147`) has no mapping. What does the caller
see while the breaker is open - 503 with what `type` slug, and is it distinguishable from a
genuine upstream 5xx? A caller cannot retry intelligently if "Jobvite is down" and "we have
stopped calling Jobvite" look identical.

**m6.** `DESIGN.md:33-34` (§1): *"It holds no state between calls beyond an HTTP connection pool
and a rate-limiter bucket."* Under P9 the bucket is not ours - it is the framework's, keyed by
`get_client_id`, and per P15 its parameters are frozen at first use. The sentence stays true but
should name what it is describing, since the ownership is the whole point of the P9 change.

**m7.** `DESIGN.md:44-46`: *"The standards require a minimal allow-list because an unused or
unreliable tool is attack surface."* Correct and citable - `ai/agent-guardrails.md:47-49` via
**B20** (`STANDARDS.md:211-217`). Worth citing inline, because it is one of the few places the
design's scope decision is defending itself against an obvious "why so few tools?" objection and
the citation is genuinely strong. Also worth naming the reference's counter-example: the
`fast-mcp-jira` tool modules total 51 `@mcp.tool` registrations across `tools/` including a
`bulk.py`, which `COMPLIANCE-SPEC.md:506` already flags as a **B20** failure. The design's §3
omission of a bulk module is a deliberate divergence from the reference and reads as an accident.

---

# BLUE ROUND 1 - Response

**C1 (health endpoint). ACCEPT, fully.** This is the finding I least want to be true and it is
plainly true. The sentence was inherited from `STANDARDS.md:564` where it was a conditional
("apply it to genuine HTTP surfaces *where they exist*") and promoted to a factual claim about
this design. **Resolution: delete the health endpoint from the claim.** ADR-0003 stands on
transport-level auth rejections alone, which do exist and do carry a real content type. Adding a
health endpoint to justify an ADR would be building a component to satisfy a citation, which is
backwards. If a health endpoint is later wanted for deployment reasons, it arrives on its own
merits with its own decision about authentication - and RED's secondary point about an
unauthenticated liveness oracle for someone else's ATS credential is a good reason to think hard
before adding one.

**C2 (B17 / `request_id`). ACCEPT, with one push-back on framing.** The `request_id` half is
indefensible - it is used in two places in §5 and defined nowhere, and I will not argue with
that. On B17 I want to be precise about what the deviation is. The design does not *fail* to log
invocations by oversight; it chose `include_payloads=False` deliberately because the payloads are
candidate PII. But RED is right that B17 asks for redacted arguments, not for no arguments, and
that a deliberate deviation from a `priority: required` clause with no ADR is exactly the drift
this project's standing rule exists to catch. **Resolution: three changes.** (a) Design a
per-invocation log event carrying `tool_name`, `request_id`, `result_status` and latency - all
four of which are non-PII and satisfy most of B17 at zero privacy cost. (b) State explicitly
that validated arguments are *not* logged, and record it as a deviation with its rationale - it
may not need a full ADR if the log event covers the rest of the clause, but it needs a
`DECISIONS.md` row. (c) Define `request_id`: generated per tool invocation, at the middleware
boundary, surfaced in the problem object, in the log event, and - this is the useful part -
propagated to Jobvite if any header will carry it, so a support conversation with Jobvite can
name a request.

**C3 (P17 blast radius). ACCEPT, in full, and this is the most actionable finding in the
round.** Seven locations, all correctly identified. I would add that item 5 - the auth scoping
story losing its only example - is not merely a text fix. It forces a real question: with four
read tools, do we still want scoped tokens at all? I think yes, but for a different reason than
the one in §7: `search_candidates` returns candidate PII and `search_jobs` returns public job
postings, and those are genuinely different sensitivity classes. That is a better scope boundary
than read-versus-write ever was, and it survives P17. **Resolution: apply all seven, and re-argue
§7's scoping on the PII-versus-public axis.**

**C4 (`start` runtime probe). ACCEPT.** RED is right and so was Phil's own suspicion. I will
defend one thing: the configurability and the README disclosure are *good* and should stay -
they are what lets a user override a probe that gets a surprising answer. But they are not
detection, and the design presented them as if they were. **Resolution: add the two-request
self-calibration probe on first paged call, log the outcome at INFO on agreement and ERROR on
disagreement, and keep `JOBVITE_PAGINATION_START_BASE` as an override that skips the probe.** The
probe is explicitly marked as unverified against live Jobvite, because it must be - the failure
mode of an unrunnable probe is a fallback to today's behaviour, which is the current design.

**M1 (secret scanning does not catch confidential documents). ACCEPT.** The control-to-incident
mismatch is real and the paragraph as written is actively misleading. **Resolution: keep the
pre-commit secret scanning (it is still correct for its own purpose) and add a separate,
honestly-labelled control - a committed-file-type gate.** And correct the prose: the sentence
"This repository has already had one incident of the adjacent class" currently sits at the end of
a paragraph about secrets, implying the secret scanner addresses it. It does not.

**M2 (verbatim CONFIDENTIAL excerpts remain). ACCEPT as a finding, MODIFY the remedy.** RED is
correctly hedged about the legal question and I will not overclaim either. But "undecided, in a
public repo, after an incident of the same class" is exactly right as a characterisation. I do
not think the short parameter quotes are a real exposure. I do think the reproduced v1 numeric
error catalogue is a different kind of thing - it is the document's substance rather than a
citation of it. **Resolution: this is Phil's call, not mine.** Recommendation to him: paraphrase
the numeric catalogue to bare facts (code -> meaning, no prose), keep the short quotes with
attribution, and add one paragraph to `JOBVITE-API.md` §0 stating the handling policy explicitly
so the next researcher inherits the decision instead of re-making it. Raise it to him rather than
acting on it - it is a legal-exposure judgement and I am a reviewer.

**M3 (allow-list keying and non-strings). ACCEPT.** Both gaps are real and neither is fatal.
**Resolution: path-keyed with an explicit wildcard for `customField[]` and any array of unknown
objects; and "fenced" is defined only for string-valued leaves - an unknown non-string field is
*dropped*, not stringified.** Dropping resolves RED's tension with `strict=True` cleanly and is
the safer default: an unknown structure we cannot fence is an unknown structure we should not be
handing to a model.

**M4 (EEO fields to the model). ACCEPT.** RED's honesty about the standards position is worth
preserving in the final report - this is *not* a citable violation, and pretending otherwise
would be exactly the fabricated-citation failure this project guards against. It is a design
decision the corpus does not make for us. **Resolution: `gender`, `race`, `veteranStatus` are
excluded from every tool output model.** They are on nobody's use case for a candidate-search
tool, and their presence in the output is pure downside.

**M5 (result-size bound). ACCEPT.** Straightforward. **Resolution: name the cap, make it
configuration per B22, and state that it bounds the *fetch*, not just the return** - which also
answers RED's privacy point, since we then never retrieve the 450 records we intended to discard.

**M6 (stdio auth). ACCEPT.** RED reached the same conclusion I did about the threat model and
then found the part I had not thought about, which is the v1.1 constraint. That is the valuable
half. **Resolution: state the stdio threat model in §7 in two sentences, and record the v1.1
constraint - a write tool cannot be reintroduced on stdio under any mechanism currently known to
this project - alongside P17's deferral, where the v1.1 planner will actually read it.**

**M7 (SIGTERM mitigation unverified). ACCEPT the finding, and RED's corollary is better than its
main point.** The ordering concern is genuine and the uvicorn-overwrites-it scenario in
particular would make the mitigation a silent no-op, which is the worst outcome - we would
believe teardown runs. **Resolution: mark the one-liner UNVERIFIED in the design, and spike it.**
It is one signal and one process. Meanwhile adopt RED's corollary as the primary statement:
nothing in the current design depends on teardown running, so the constraint costs us nothing
today, and the design's job is to keep it that way.

**M8 (grep guard). ACCEPT.** The import-graph check is strictly better than the grep and is not
harder to write. **Resolution: replace the text assertion with an AST-based import check.**

**M9 (ADR list stale). ACCEPT.** All five sub-items. The P15 contractual gap in particular is a
place where §5 currently states something flatly false, which matters more than the ADR
bookkeeping. **Resolution: §5 gains one sentence naming rate-limit refusals as the one failure
class that does not carry a problem object; §12 gains ADR-0007; ADR-0002's body is rewritten
around P9/P15; ADR-0004 picks up P5's regression evidence; P17 is recorded as D17.**

**M10 (live suite rots). ACCEPT.** `--collect-only` is a one-line CI addition for a real
protection. **Resolution: adopt.**

**m1.** ACCEPT. Correct the evidence base line to `FASTMCP.md` and `FASTMCP-SPIKE-4.md`.

**m2.** ACCEPT. "Two calls settle it."

**m3.** MODIFY. RED is right that HR-XML has no evidenced path to our four endpoints. But I am
not willing to remove the tolerance, because the design's central error-parsing claim is
precisely that we cannot dispatch on content type and cannot assume JSON - and the v1 surface is
where the weirdness lives (`JOBVITE-CONTRACT.md:154`: the jobFeed 401 sends no `Content-Type` at
all, and we *do* call jobFeed). **Resolution: keep `defusedxml` and the branch, and re-label it
in §4.2 as a hardened fallback for an unevidenced-but-plausible shape rather than as one of four
handled cases.** RED's framing objection is accepted; the deletion is not.

**m4.** ACCEPT. One sentence: annotations are hints, not enforcement.

**m5.** ACCEPT. The open-breaker state needs its own `type` slug and a stated `status`.

**m6.** ACCEPT. Name the framework limiter in §1.

**m7.** ACCEPT. Cite B20 inline, and name the reference's 51-tool `bulk.py` counter-example, with
the standing rule stated: the reference is a source of patterns, never authority.

---

# RED ROUND 2 - Adversarial rebuttal

Blue accepted nearly everything, which is either a well-built design meeting a fair review or a
reviewer being agreed with too easily. Three responses do not survive contact, and Blue's own
answers unlock two new points.

### R2-a - Blue's C1 resolution is right but leaves ADR-0003 thinner than Blue admits.

Blue deletes the health endpoint from the claim and rests ADR-0003 on transport-level auth
rejections. Fine. But note what that costs: transport-level auth rejections exist **only on the
HTTP transport**, which is opt-in (`DESIGN.md:202`). On the default stdio deployment there is no
HTTP surface whatsoever, so `problem+json` is applied *nowhere*, and ADR-0003 goes from
"honoured everywhere it can be" to "honoured on an optional transport some users never enable".

That is still a correct ADR - the clause genuinely cannot be satisfied on a JSON-RPC tool result,
and `STANDARDS.md:557-564` reached the same conclusion independently, which matters because it
means the design is not alone in a self-serving reading. But the ADR must say the smaller true
thing rather than the larger comfortable one. **Blue's resolution is accepted; the ADR's wording
must shrink with it.**

### R2-b - Blue's C2 resolution invents a per-invocation log event and does not check where it comes from.

Blue proposes logging `tool_name`, `request_id`, `result_status`, latency. Good. But the design's
logging is `StructuredLoggingMiddleware` plus `TimingMiddleware` (`DESIGN.md:229-231`), both
framework components - and `PENDING-DESIGN-CHANGES.md` P12 is a whole section arguing, from
executed evidence, that **on this framework a middleware's defaults are not a safe starting
point**, with four of eight middlewares exercised turning out unusable or requiring overridden
defaults.

So Blue's resolution assumes the framework's structured logging emits the four fields it wants,
in snake_case, per B17's `ai/tool-calling.md:178-179`. **That is exactly the class of assumption
P12 was written to stop.** `PENDING-DESIGN-CHANGES.md` P7 records that timing and structured
logging were "verified" - but verified to *run*, not verified to emit a particular field set with
particular names.

**New requirement: before the design commits to satisfying B17 through framework middleware,
someone must look at what `StructuredLoggingMiddleware` actually emits.** If it does not carry
`tool_name` and a correlation id in the right shape, B17 is satisfied by our own code or not at
all. This is cheap - it is reading one middleware's output - and it is precisely the step this
project keeps finding was skipped.

### R2-c - Blue's M4 resolution under-reaches. Dropping three fields does not address the class.

Blue drops `gender`, `race`, `veteranStatus`. Correct, and insufficient. Those three are the
fields that happen to appear in **a synthetic fixture we wrote ourselves**
(`fixtures/candidate_list_success.json`). Per `JOBVITE-CONTRACT.md:534` the success shapes are
*"reconstructed [...] value formats, optionality, and nesting depth are hypotheses"*, and
`JOBVITE-CONTRACT.md:627` notes even the `[OFFICIAL]` job sample does not enumerate the object's
fields.

So the real Jobvite response may carry EEO or other special-category fields under names nobody
here has guessed - `disability`, `ethnicity`, `dateOfBirth`, a `customField` entry a customer
configured. Blocking three known names is a deny-list, and the design's own §6 already
establishes that a deny-list is the wrong shape for an unknown schema.

**The consistent answer is the one §6 already reached for untrusted content: allow-list the
output model.** The four read tools return exactly the fields their Pydantic output models
declare, and an unrecognised field is dropped rather than passed through. That is one mechanism
covering both M3 and M4, it composes with `strict=True`, and it means an unexpected
special-category field arriving from a customer's Jobvite instance never reaches the model. Blue
built the right machine in §6 and then hand-listed three field names in §2.1.

### R2-d - NEW, unlocked by Blue's C3 resolution: the PII-versus-public scope split does not survive `get_job_feed`.

Blue re-argues §7's token scoping on a candidate-PII-versus-public-jobs axis. That is a better
axis. It also has a hole Blue did not check: `get_job_feed` hits `GET /v1/jobFeed`, whose
credentials travel **in the query string** (`DESIGN.md:113-118`). It is the one endpoint whose
URL is classified sensitive.

So the scope classes are not two, they are three: candidate PII (`search_candidates`,
`get_candidate`), public job data over header auth (`search_jobs`), and public job data over
query-string auth with a separate `companyId` (`get_job_feed`). Whether `companyId` is even
available in a deployment that only wants candidate search is unstated - `DESIGN.md` never says
which configuration variables are required for which subset of tools.

**New finding: the design does not state its configuration-to-tool dependency map.** With a
required-config-fails-at-boot policy (`DESIGN.md:220-225`, and it is a good policy), a deployment
that wants only candidate search must currently supply a `companyId` it has no use for, or the
server refuses to boot. That is a real adoption friction created by an otherwise correct
fail-fast rule, and it is decided by omission today.

### R2-e - NEW, unlocked by Blue's M7 corollary: "nothing depends on teardown" is true today and the design has no rule keeping it true.

Blue's corollary is the best thing in the Blue round: the SIGTERM constraint is currently free
because the only teardown user is a connection pool the OS reclaims anyway. I agree entirely.

But Blue then treats that as reassurance, and it is the opposite. A constraint that costs nothing
today and is enforced by nothing is a constraint that will be violated by the first person who
adds something reasonable to teardown - a metrics flush, a final audit-log write (which C2's
resolution makes *more* likely, since Blue just introduced per-invocation logging), a graceful
in-flight-request drain.

**The constraint needs to be stated as a rule with a reason, in the module that owns the
lifespan, not as a note in a review.** P1 half-does this ("nothing that must complete before
connections close may live in a lifespan teardown"). It should be in `server.py`'s own
documentation next to the lifespan, where the person adding the flush will read it.

### R2-f - Blue's M2 hand-off to Phil is correct procedure and must not become a dropped item.

No argument with the substance. But "raise it to Phil" is how findings die. It belongs in
`NEEDS-PHIL.md` with a recommendation attached, per this project's own convention, not in a
review document nobody re-reads. Flagging so the orchestrator files it rather than relaying it.

---

# BLUE ROUND 2 - Final response

**R2-a. ACCEPT.** ADR-0003's wording shrinks. Final text should say: the clause cannot be
satisfied on an MCP tool result at all; it is honoured on the HTTP transport's own auth
rejections, which are the only genuine HTTP surface this server has; on the default stdio
deployment there is no surface to honour it on. That is less comfortable and it is what is true.
`PENDING-DESIGN-CHANGES.md` P14 also gives the ADR a much stronger positive argument than it
currently carries - problem objects are *returned*, never raised, and were measured surviving
every middleware and masking configuration unchanged - so the ADR should lead with the executed
evidence rather than with the reasoning. Phil's weak claim 4 asked whether the "cannot be set"
assertion came from reasoning rather than execution. It did. It is nonetheless correct, and it is
independently corroborated at `STANDARDS.md:557-564`, so the ADR is necessary rather than
unnecessary - but its *evidence base* should move to P14, which was executed.

**R2-b. ACCEPT, and this becomes a pre-freeze action rather than a design edit.** RED is right
that I proposed satisfying a required clause through a framework component whose output I have
not seen, in a project that has now found four of eight middlewares defective or
default-hostile. **Final: the design states the required log event and its four fields as our
obligation; whether `StructuredLoggingMiddleware` emits them, or whether we emit them ourselves,
is settled by looking - and it is settled before freeze, not after.** If it does not, we log
them in our own tool wrapper, which is a small amount of code and removes the dependency
entirely.

**R2-c. ACCEPT, and this supersedes my M4 answer.** RED is right that I built an allow-list
mechanism in §6 and then reached for a three-name deny-list in §2.1, which is incoherent.
**Final: tool output is allow-listed by the Pydantic output model. An unrecognised response field
is dropped. `gender`, `race` and `veteranStatus` are then excluded automatically, along with
every special-category field nobody has guessed.** This merges the M3 and M4 resolutions into one
mechanism, which is also less code than either. Note the consequence honestly: a genuinely useful
new Jobvite field will also be dropped until someone adds it to the model, and that is the right
trade for this data class.

**R2-d. ACCEPT.** The three-way scope split is correct and the configuration-to-tool dependency
map is a genuine omission. **Final: the design gains a short table mapping each tool to the
configuration it requires, and the fail-fast rule is scoped to the configuration the *enabled*
tools need** - so a candidate-search-only deployment is not forced to invent a `companyId`. This
also gives the token scopes something concrete to attach to.

**R2-e. ACCEPT.** RED is right that I read my own corollary as reassurance when it is a warning,
and right that C2's per-invocation logging makes a teardown flush *more* tempting, not less.
**Final: the constraint is stated as a rule at the lifespan definition in `server.py`, with the
reason (SIGTERM does not run teardown; containers stop with SIGTERM) and the pointer to the
spike, so the person who wants to add a flush reads why they cannot before they do.**

**R2-f. ACCEPT.** M2 goes to `NEEDS-PHIL.md` with the recommendation attached, not into a review
document. Filed as an action for the orchestrator.

---

# Final report - every decision

## Verdicts on Phil's six self-nominated weak claims

**1. §2.2 `create_candidate` guarding does not satisfy `ai/agent-guardrails.md:70`. CONFIRMED -
and the remedy you suspected does not exist.**
The clause is real and verified verbatim at `ai/agent-guardrails.md:70-73`: *"**Default-deny
destructive operations.** Any irreversible or high-blast-radius action (delete, financial
transaction, outbound message to a third party, infra change, mass update) MUST pause for human
approval before execution. Fail closed: no approver, no action."* An environment variable is a
deploy-time switch, not a per-invocation approval, and `:75-77` is explicit that the gate decides
on *"the **validated tool call** - the exact tool name and resolved arguments"*. Your reading was
correct.
**But MCP elicitation is not the mechanism**, and this is the more important half.
`FASTMCP.md:523` records that *"`ctx.elicit()` [...] is gated off on sessionless connections"*,
and `FASTMCP.md:657` repeats it - on the `2026-07-28` sessionless spec you deliberately chose in
D1, elicitation is unavailable **by design**. `PENDING-DESIGN-CHANGES.md` P17 then proved it by
execution, with the verbatim raise, and found something worse: all three elicitation result types
are truthy, so `if result:` treats a human clicking Decline as approval - measured at three
refusals producing three records. **P17's answer - cut the tool - is correct**, and I want to
endorse the specific reasoning that an ADR waiving a required safety control should not exist.
That is the right instinct and it is the one that would have been easiest to talk yourself out
of.

**2. §7 stdio has no authentication. PARTLY WAVING - the answer is right and unstated, and the
consequence you did not chase is the real finding.** See **M6**. Post-P17 the stdio threat model
is defensible: a caller who spawned the process already holds the credential, and every tool is a
read. Say it. The finding is v1.1: on stdio there is no token, no scope and no elicitation, so
**the deferred write tool cannot be reintroduced on the default transport under any mechanism
this project currently knows of.** Record that next to P17's deferral or v1.1 will rediscover it
by proposing an env-var gate.

**3. §4.5 the 1-based `start`. RATIONALISING - you were right to suspect it.** See **C4**. All
three mitigations are disclosure, not detection; none of them fires unless the user already
suspects the bug. A runtime probe was dismissed too fast: two requests on first paged call,
`start=0` versus `start=1`, comparing `eId`s - the exact experiment your own
`CREDENTIAL-CHECKLIST.md` row 2 specifies for a human. Move the gate into the software. Keep the
config knob as an override.

**4. §5 ADR-0003's `problem+json` claim came from reasoning. CORRECT CLAIM, WRONG EVIDENCE
BASE.** The assertion is right, and it is independently corroborated at `STANDARDS.md:557-564`,
which reached the same adaptation from the same clause without our motivation - so the ADR is
necessary, not self-serving. Two corrections: the ADR's *scope* shrinks (R2-a: on stdio there is
no HTTP surface at all, so it is honoured nowhere on the default deployment), and its *evidence*
should move to `PENDING-DESIGN-CHANGES.md` P14, which measured problem objects surviving every
middleware and masking configuration intact. One further divergence you should know about:
`STANDARDS.md:562-564` recommends using **the tool name** as the `instance` substitute and
documenting the substitution; the design instead uses
`urn:fast-mcp-jobvite:invocation:<request_id>`. I think the design's choice is better - it
identifies one invocation rather than one tool - but it is an undeclared divergence from the
project's own research and should be noted as a deliberate one.

**5. §2's five-tool scope. NOT TOO NARROW, AND `get_candidate` IS NOT REDUNDANT - but your
stated reason is the weaker one.** Keep the split. The justification in `DESIGN.md:56-59`
(schema tightness) is true but post-hoc-sounding. The stronger reason is cardinality: `?candidateId=`
returns one record and the date-window/paging form returns a page, so they have **different output
schemas**, not merely different inputs. One tool cannot have two return types under `strict=True`.
That argument is unanswerable and the current one invites debate. Also, `DESIGN.md:44` now says
"Five tools" and P17 makes it four.

**6. §6 default-untrusted allow-list. IMPLEMENTABLE - your stated worry is the wrong one, and
there are two real ones.** See **M3** and **R2-c**. Not knowing the response schema is not an
obstacle to default-deny; it is the reason default-deny is correct. The real gaps: name-keying
collides (`title` and `eId` each occur at multiple depths in your own fixture) so it must be
path-keyed with a wildcard for `customField[]`; and "fenced" is undefined for non-string values,
which collides with `strict=True` output models. Resolution: path-keyed, unknown non-strings
dropped rather than stringified - and per R2-c, extend the same allow-list discipline to the tool
*output* models, which also solves M4.

## Decisions on every numbered finding

| # | Finding | Severity | Decision |
|---|---|---|---|
| C1 | Health endpoint cited in ADR-0003's compliance argument, specified nowhere | CRITICAL | **ACCEPTED.** Delete the claim; ADR-0003 rests on transport-level auth rejections only, with its scope reduced per R2-a |
| C2 | B17 per-invocation logging absent; `request_id` used but never defined | CRITICAL | **ACCEPTED.** Design the log event (`tool_name`, `request_id`, `result_status`, latency); record the no-arguments deviation in DECISIONS.md; define `request_id`'s origin and propagation. **Pre-freeze action:** verify what `StructuredLoggingMiddleware` actually emits (R2-b) |
| C3 | P17's cut of `create_candidate` invalidates seven sections of DESIGN.md | CRITICAL | **ACCEPTED in full.** Apply all seven; re-argue §7 token scoping on the PII-vs-public axis, refined to three classes per R2-d |
| C4 | §4.5 `start`-base mitigation detects nothing; runtime probe not considered | CRITICAL | **ACCEPTED.** Add the two-request self-calibration probe on first paged call; keep the config knob as an override |
| M1 | Secret scanning cannot catch the confidential-document incident it cites | MAJOR | **ACCEPTED.** Add a committed-file-type gate; correct the misleading prose |
| M2 | Verbatim CONFIDENTIAL excerpts remain in the public repo | MAJOR | **ACCEPTED as a finding, remedy is Phil's.** File in `NEEDS-PHIL.md` with recommendation: paraphrase the reproduced numeric catalogue, keep short attributed quotes, add a handling policy to `JOBVITE-API.md` §0 |
| M3 | Allow-list keying (name vs path) and non-string fencing undefined | MAJOR | **ACCEPTED.** Path-keyed with a `customField[]` wildcard; unknown non-strings dropped, not stringified |
| M4 | EEO / special-category fields flow to the model; no data-minimisation position | MAJOR | **ACCEPTED, superseded by R2-c.** Not a citable standards violation - `STANDARDS.md:683` rules the GDPR machinery non-binding. Resolution is allow-listed output models, not a three-name deny-list |
| M5 | Result-size bound stated as both 500/1000 and 50, relationship undefined | MAJOR | **ACCEPTED.** Name the cap, make it configuration (B22), state that it bounds the fetch |
| M6 | stdio threat model unstated; v1.1 write cannot return to stdio | MAJOR | **ACCEPTED.** State the threat model; record the v1.1 constraint next to P17's deferral |
| M7 | P1's SIGTERM mitigation is reasoned, not executed; uvicorn may overwrite it | MAJOR | **ACCEPTED.** Mark UNVERIFIED and spike it. Adopt the corollary as primary: nothing depends on teardown today, and per R2-e that must be enforced by a stated rule at the lifespan, not left to luck |
| M8 | P2's httpx guard is a text grep with three holes and no type-leak coverage | MAJOR | **ACCEPTED.** Replace with an AST import-graph assertion |
| M9 | §12 ADR list stale; P15's rate-limit refusal contradicts §5's flat claim | MAJOR | **ACCEPTED.** Add ADR-0007; rewrite ADR-0002 around P9/P15; add P5's regression evidence to ADR-0004; record P17 as D17; §5 gains the rate-limit-refusal exception |
| M10 | Live-credential suite is excluded and never collected, so it rots | MAJOR | **ACCEPTED.** CI runs `pytest --collect-only` over it |
| m1 | `DESIGN.md:8` cites `FASTMCP-SPIKE.md`, which does not exist in any commit | MINOR | **ACCEPTED.** Correct to `FASTMCP.md` + `FASTMCP-SPIKE-4.md` |
| m2 | "One call settles it" - the `start` probe is two calls | MINOR | **ACCEPTED** |
| m3 | HR-XML parsing committed for `/v1/candidate`, a route we do not call | MINOR | **MODIFIED.** Keep `defusedxml`; re-label as a hardened fallback, not one of four handled cases |
| m4 | Tool annotations presented without noting they are hints, not enforcement | MINOR | **ACCEPTED.** One sentence |
| m5 | Open circuit breaker has no problem `type` or `status` mapping | MINOR | **ACCEPTED** |
| m6 | §1 describes a rate-limiter bucket we no longer own (P9) | MINOR | **ACCEPTED** |
| m7 | B20 not cited inline; reference's 51-tool `bulk.py` counter-example unnamed | MINOR | **ACCEPTED** |
| R2-d | Configuration-to-tool dependency map absent; fail-fast forces unused `companyId` | MAJOR (new) | **ACCEPTED.** Add the table; scope fail-fast to the enabled tools' configuration |
| R2-e | Nothing enforces the "no teardown dependency" constraint | MAJOR (new) | **ACCEPTED.** State it as a rule at the lifespan definition |

## Review of the staged changes (PENDING-DESIGN-CHANGES.md)

Reviewed as instructed, since they are staged rather than sanctified.

- **P17 (cut `create_candidate`): endorsed.** The strongest item in the file. Executed evidence,
  a retraction-shaped honesty about the truthiness trap, and the right instinct that an ADR is
  not a waiver. The gap is blast radius - see **C3**.
- **P2 (keep httpx): endorsed, guard weakened.** The decision is right and the testability
  argument is the correct deciding axis given no credential and no sandbox. The guard is a grep -
  see **M8**.
- **P1 (SIGTERM): finding endorsed, mitigation unverified.** See **M7** and **R2-e**.
- **P9/P15 (rate limiter): endorsed, with an unclosed contract hole.** A rate-limit refusal
  carries no problem object, which contradicts `DESIGN.md:186-188` as written - see **M9**. P15's
  own honesty note that all limiter testing was sequential and single-client stands, and the one
  concurrency test it asks for is worth doing before ADR-0002 is final.
- **P13 (RetryMiddleware disqualified): endorsed and now partly moot.** Its argument was
  `create_candidate`-specific and that tool is cut, but the conclusion - retries live inside
  `services/jobvite_client.py` where idempotency is known - survives on its own merits and should
  not be softened just because its motivating example left.
- **P5/P6 (regression guardrails): endorsed, and P6 answers the generalised question directly.**
  Pinning `mcp` and gating on a `fastmcp inspect` diff are the right two controls. The design
  already emits the capability report (`DESIGN.md:331-333`); making it a gate is nearly free.
- **P12 (a middleware's defaults are not a safe starting point): endorsed as the most valuable
  general principle in the file** - and see **R2-b**, where Blue's own C2 resolution violated it
  within one round of it being written. That is how quickly this principle gets forgotten.

## Which design decisions become WRONG if 4.0 differs

Answering the brief's specific question, now that `FASTMCP-SPIKE-4.md` has landed. The remaining
exposure is small and named:

1. **`ToolResult(content, structured_content, meta, is_error)`** - `DECISIONS.md` D6 explicitly
   flags that this signature was read from 3.4.7 and *"must be re-confirmed against 4.0.0b4"*.
   P14 exercised problem objects on 4.0 across five arms, which is strong indirect confirmation,
   but I did not find an explicit signature re-read in the staged file. If the constructor
   differs, **D6's entire mechanism** changes - and D6 has already been wrong once about a
   constructor (the retracted `ToolError` version). Cheapest possible check; do it.
2. **`StaticTokenVerifier`** - P7 verifies `require_scopes` behaviour on both eras, which implies
   the verifier works, but the design names the class specifically (`DESIGN.md:206-208`) and I
   found no direct confirmation that `StaticTokenVerifier` itself survives 4.0 under that name.
   If it does not, §7's auth design needs a substitute.
3. **`mask_error_details=True`** - confirmed on 4.0 by P7, all four combinations. No exposure.
4. **Lifespan composition** - confirmed by P7. No exposure.
5. **Everything downstream of a transitive bump** - P6's point, and the honest general answer:
   the design's framework-dependent claims are now mostly executed, but P5 proves that executed
   today is not executed after the next `mcp` release. The two guardrails in P6 are the only real
   answer to this and both should be adopted.

## Surviving count

Findings that survived the round **unresolved** - meaning no resolution was agreed, or the
resolution depends on someone outside this review:

- **Critical: 0.** C1-C4 all reached agreed resolutions.
- **High/major: 2.**
  - **M2** - the CONFIDENTIAL-excerpt exposure. Unresolved by design: it is a legal-judgement
    call that belongs to Phil, filed to `NEEDS-PHIL.md` with a recommendation.
  - **M7** - the SIGTERM mitigation. Unresolved because it is unverified: the one-liner must be
    executed, and it may not work.
- **Minor: 1.**
  - **R2-b's pre-freeze action** - what `StructuredLoggingMiddleware` actually emits is unknown,
    and C2's resolution is conditional on it. Minor because the fallback (emit the log event
    ourselves) is small and certain.

**`0c / 2h / 1m`**

Everything else was accepted, modified, or superseded within the round and is actionable text
work on `DESIGN.md`, `DECISIONS.md` and `PENDING-DESIGN-CHANGES.md`.

---

# What I did NOT review, and why

- **`fast-mcp-jira` in depth.** I sampled it to verify three specific claims the design and
  `DECISIONS.md` make about it, and all three hold: the `build_response` envelope is real
  (`src/fast_mcp_jira/tools/issues.py:98,105,107,110` - note `:110` returns
  `build_response(False, error="Internal error occurred")`, a failure in a success-shaped result,
  which is exactly D6's objection); `mask_error_details` appears nowhere in the package,
  confirming D16; and `src/fast_mcp_jira/__main__.py:35` hardcodes `transport="http"` with no
  stdio path, confirming D11. I did not audit it further, because per the standing rule it
  carries no authority and no finding in this review depends on it.
- **`FASTMCP-SPIKE-4.md` in full** (1076 lines). Read via `PENDING-DESIGN-CHANGES.md`'s summary
  plus targeted greps. If a design claim rests on a spike detail not surfaced in P1-P17, I would
  not have caught the mismatch.
- **`JOBVITE-API.md` in full** (740 lines) and **`STANDARDS.md` in full** (1310 lines). Targeted
  reads only. Every clause I cite, I opened at its `file:line`; I did not sweep either document
  for obligations the design misses beyond the ones named here. **There are almost certainly more
  B-numbers unaddressed than the two I found** - a systematic B1-B106 conformance sweep against
  DESIGN.md is a separate piece of work and I did not do it.
- **`LICENSING-SURVEY.md`.** Not opened. D7/D13 are settled by Phil and out of review scope.
- **The standards corpus beyond seven files.** I opened `ai/agent-guardrails.md`,
  `ai/prompt-injection.md`, `ai/tool-calling.md`, `architecture/error-contract.md`,
  `architecture/gdpr-data-rights.md` (frontmatter only), `architecture/observability.md`,
  `architecture/security.md` (frontmatter only), `architecture/testing-strategy.md` (frontmatter
  only) and `backend/rate-limiting.md`. Where I cite a clause I quote it verbatim from the file.
  Where I rely on `STANDARDS.md`'s B-numbering I say so and give both citations.
- **`src/` and `tests/`.** Effectively empty - the only file under `.github/` is
  `workflows/mirror.yml`. There is no implementation to review, which is correct for a design
  round.
- **Anything requiring a live Jobvite call.** No credential exists, no sandbox exists
  (`api-stg.jobvite.com` fails DNS per `DESIGN.md:23`). C4's probe, M5's page-cap question and
  every success-shape question in the design are unresolvable here by construction. I have not
  recommended a single action that requires calling Jobvite, except where
  `CREDENTIAL-CHECKLIST.md` already lists it for the day a key lands.
