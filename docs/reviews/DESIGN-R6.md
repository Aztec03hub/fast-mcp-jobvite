# DESIGN-R6 - Round 6 adversarial review, and the freeze decision

Reviewer: `design-review-r6`, fresh, playing both lenses. Target: `docs/DESIGN.md` at revision 5,
commit `fc329b7`. Date: 2026-08-28.

**Verdict: DO NOT FREEZE.**

**Tally: 0 Critical / 1 High / 3 Medium / 6 Low / 1 Nit.**

The freeze rule requires 0C/0H/0M from a review round **and** an empty must-mitigate table. The
table is empty. The round is not clean. One High and three Mediums stand, so the document does not
freeze on this round.

**But read the recommendation in the closing section before scheduling round 7.** Nothing I found
this round is a design defect. Every one is bookkeeping, an enumeration gap, or an obligation
nobody discharged. That is a finding about the review process, and I state it as one.

---

## What I actually read, stated so the gaps are visible

- **`docs/DESIGN.md`, all 1734 lines, in full.**
- **All eleven ADR files plus `docs/adr/README.md`, in full.** This was a standing nomination
  declined by five rounds. It is now discharged. Finding L-4's sibling context and the ADR-0011
  check below came out of it; the ADRs are in better shape than their neglect suggested.
- **The three gates, re-run from the repo root**, not trusted:
  - `check-coupling.py` -> exit 0. 60 STRIDE rows, 17 Critical/High, 23 rows naming a §8 case.
  - `check-coupling-controls.py` -> exit 0, **29/29 controls fired**, baseline green before and
    after.
  - `check-coupling-sweep.py` -> exit 0. 184 substitutions, **0 escapes are holes**; the 7 escapes
    are the designed Medium/Low exemption.
  The gates are real. R5's H1 escape is closed and the sweep now proves it by construction.
- **Every `file:line` citation in `DESIGN.md` and in the eleven ADRs**, extracted by script and
  read at the cited lines in `evolv-coder-standards/standards/`. 38 distinct citations resolved.
  **One is wrong** (L-3 below); every other one says what the citing sentence claims. This includes
  the load-bearing ones: `agent-guardrails.md:70-73`, `threat-modeling.md:78-82`,
  `error-contract.md:96-108`, `input-validation.md:220-226`, `resilience.md:74-76`,
  `request-middleware.md:145`, and `readme-standard.md:45-58` (fourteen sections - the count is
  right).
- **`docs/research/JOBVITE-API.md:397` and `:399`**, the two load-bearing evidence citations behind
  §4.5's base-agnostic paging and §8's structural fixture. Both say exactly what §4.5 and §12 claim,
  including the "does not distinguish 0-based from 1-based-with-clamping" caveat, which the design
  reproduces faithfully rather than over-reading.
- **`CONFORMANCE-RESWEEP.md` §1 and §4** in full. **`DESIGN-R5.md`** structure and its four Highs.

**What I did NOT read, declared rather than implied:**

- **`FASTMCP-SPIKE-4.md` was NOT read in full.** It is 2354 lines. I read its complete section index
  (60+ headers) and then read closely the sections carrying the design's load-bearing "Measured"
  claims: §13.1 (rate limiter), §13.3 (retry, four rows), §13.4 (middleware scoreboard), §14.1
  (limiter D4 verdict), §15.4 (annotations), §19.5 (the SIGTERM snippet), §20.7 (the unswallowable
  era check), and "What I could NOT verify" in full. Roughly 400 of 2354 lines.
  **Every claim I sampled checked out exactly** - see the audit below. I declined the full read
  because the sample was clean at a rate that made an exhaustive pass low-yield, not because it was
  expensive. A sixth reviewer declining it for the sixth time would be a pattern; I am declining the
  remaining 80% on evidence, and recording that the 20% I checked found zero overstatement.

---

## Post-round verification, and one retraction I am recording against myself

Round 6 shipped M-2 and M-3 with explicit "verify before adopting" caveats. Both were then verified
by execution against the real pinned artifacts. **One caveat saved the round from a false claim and
the other saved it from a broken fix.** The findings above are the corrected versions; this section
records what changed, because a silent correction would leave the document looking like it was right
the first time.

**Artifacts used.** `mcp` 2.0.0 and `mcp_types` 2.0.0 installed at
`claude_projects/evolv/.venv`; `mcp` **2.1.1** (the pinned version) and `fastmcp` /
`fastmcp-slim` **4.0.0b4** downloaded and unpacked from PyPI. Note in passing that this corroborates
§10's packaging claim: the `fastmcp` 4.0.0b4 wheel contains **only** a `dist-info` directory, and
`fastmcp-slim` carries the entire implementation - which is exactly why §10 says naming it is
mandatory or resolution fails.

### RETRACTED: M-3's premise. MCP *does* carry trace context.

My original fix asserted *"MCP carries no trace context to a server on either transport - there is no
header, no context field, and no negotiated extension that conveys one."* **All three clauses are
false.**

My first search was a grep over `mcp_types` for trace/span terms. It returned zero, and the positive
controls fired (`elicit` 169, `_meta` 224, `sampling` 133), so the instrument worked. **The instrument
worked and the selector was wrong.** Trace context is not a schema *type* - it rides as ordinary keys
in the open `_meta` map (`RequestParamsMeta` is `TypedDict, extra_items=Any`, documented as *"An open
map: arbitrary keys round-trip"*), so it is invisible to a search of the type definitions and lives in
the SDK's shared layer instead. A clean zero that explained itself was the bug.

What the wider search found:

| Fact | Evidence |
|---|---|
| W3C trace context rides in request `_meta` per **SEP-414** | `mcp/shared/jsonrpc_dispatcher.py:389-390`, comment cites SEP-414 |
| `mcp` **2.1.1** injects it on every outgoing request | same file, inside a `SpanKind.CLIENT` span named `MCP send <method>` |
| `opentelemetry-api>=1.28.0` is a **hard dependency** of `mcp` | `Requires-Dist` in the 2.1.1 wheel METADATA |
| FastMCP 4.0.0b4 **extracts it server-side already** | `fastmcp/server/telemetry.py:95` calls `extract_trace_context(req_ctx.meta)` |
| The extractor is a **public** API, not private | `fastmcp/telemetry.py:308`, listed in `__all__` |
| A tool reaches the raw value at `ctx.request_context.meta` | `extract_trace_context` docstring names that accessor |

So M-3 is the brief's outcome **(b): a mechanism exists and is reachable**, and the finding is an
implementation obligation rather than an ADR. **Do not write ADR-0012 for this.**

**The lesson, recorded because it is the reusable part.** I reached "unsatisfiable" from an absence in
our research corpus plus one grep of the wrong package. An impossibility claim needs a higher bar than
a defect claim, and the bar it needed was one search of the SDK rather than of the schema. The caveat
I attached is the only reason this did not become a frozen sentence scoping out a live obligation.

### CONFIRMED: M-2's caveat was right. The obvious fix would have been rejected.

Four arms, executed against `mcp_types` 2.0.0 and the real `jsonschema` validator, using a schema of
the shape §2.1 specifies (`additionalProperties: false`):

| Arm | Result |
|---|---|
| 1. Undeclared `request_id` as a top-level key in `structured_content` | **REJECTED** - `Additional properties are not allowed ('request_id' was unexpected)` |
| 2. `request_id` **declared** as an output-model field | accepted |
| 3. `request_id` in result **`_meta`**, structured content untouched | accepted, and `result.meta` carries it |
| 4. `_meta` through a serialise/deserialise round trip | preserved intact |

`ClientSession.validate_tool_result` (`mcp/client/session.py:1096-1110`) validates
`result.structured_content` against the cached output schema and **never inspects `_meta`**. So
`_meta` is the home, arm 1 is the fix that would have shipped a broken result shape, and the lead's
instinct - that this is the same stack behaviour that broke `ResponseLimitingMiddleware` - was
correct.

---

### The spike-claim audit, since the design's credibility rests on it

| DESIGN claim | Spike source | Verdict |
|---|---|---|
| §4.4 "burst 3 yields 1, 5 yields 3, 10 yields 8" | §13.1, verbatim run output | **Exact match** |
| §4.4 "burst 6 yields 4 on both protocol eras" | §14.1(b), verbatim | **Exact match** |
| §4.4 "the `2` is `server/discover` plus `tools/list`" | §13.1 counting-middleware output | **Exact match** |
| §4.4 default keys everyone to `"global"` | §13.1, plus source cite `rate_limiting.py:156` | **Exact match** |
| §4.4 only `limiters.clear()` applies new values | §14.1(c), verbatim | **Exact match** |
| §4.3 "one call, four rows created" | §13.3, `ROWS CREATED = 4` | **Exact match** |
| §7.7 "four of the eight exercised were unusable or needed defaults overridden" | §13.4 scoreboard, same sentence | **Exact match**, and the scoreboard supports the count |
| §2.2 annotations: "one non-test reference, a field-name alias table" | §15.4, `fastmcp/_compat.py:47` | **Exact match** |
| §7.5 the era check fires in result-serialization, unswallowable | §20.7, four arms, `rows 0 -> 0` | **Exact match**, including the first-leg-only caveat |
| §7.4 the shutdown snippet | §19.5 | **Match**, and §7.4's "two halves executed separately" caveat is corroborated by the spike's own could-not-verify list (PID 1 never simulated) |

I went looking for a "Measured" claim whose evidence was reasoning. **I did not find one.** Where the
design reasons rather than measures, it says so, at the point of use - §4.4's stdio paragraph,
§7.7's standing cache rule marked "Derived, not measured", §10's `UNVERIFIED:` marker, §7.4's two
limits on the word "verified". This is the document's strongest property and it survived the round.

---

# RED ROUND 1 - Adversarial

## HIGH

### H-1. §11's count paragraph says "Two" over an empty table, and its written-out arithmetic does not reconcile. Third recurrence of the failure mode the paragraph exists to prevent.

**Location:** `DESIGN.md:1621-1643`.

The must-mitigate table at `:1573-1575` is empty:

```
| Row | Threat | Action | Ref |
|---|---|---|---|
| *(none)* | Both rows are closed by this revision: C5-R1 in §5.3, C5-E1 in §7.2 | - | B39, B40, B21 |
```

The paragraph directly beneath it, at `:1577`, opens:

> **Two, and the arithmetic is written out rather than carried forward, because it was carried
> forward wrongly twice.**

and closes the chain at `:1584` with *"That leaves **two**."*

**The table holds zero rows. The paragraph counting it says two, in bold, twice.** And the very next
paragraph at `:1589-1593` describes this exact bug happening before:

> **The second miscount is why this paragraph now names its own failure mode twice.** The edit that
> mitigated C8-I1 removed its row from the table above and left this sentence reading *"Three"* [...]
> **The count is a property of the table; whoever changes the table changes it here in the same
> edit, or the paragraph is worse than no paragraph** - it lends the authority of shown arithmetic
> to a number nobody rechecked.

Revision 5 removed the last two rows from the table and left the sentence reading "Two". By the
paragraph's own standard it is now worse than no paragraph. This is the **third** recurrence, in a
paragraph that names its own failure mode twice.

**Why this is High and not a proofreading nit.** The freeze condition is *"§11's must-mitigate table
is empty"*. §11 now contains a bolded count asserting two rows remain. **Two parts of the document
disagree about whether the document is freezable**, and the disagreement sits in the section the
freeze rule keys on. A reader checking the freeze condition against the prose gets the wrong answer.

**Second defect, same paragraph: the arithmetic does not work.** At `:1578-1580`:

> Seven at first writing. The TLS refusal in §7.1 cleared C1-S1, C1-T1 and C1-I1, and dropping
> `ResponseCaching` removed the cache-disclosure row from the model entirely rather than mitigating
> it, which took it to five.

That step names **four** removals - C1-S1, C1-T1, C1-I1, and the cache row - and 7 - 4 = 3, not 5.
The rest of the chain is internally consistent (5 - 2 = 3, 3 - 1 = 2), so the break is in the first
step: either "Seven" is wrong, or the three TLS rows occupied one table entry and the sentence
should say so. **A paragraph whose entire claim is "the arithmetic is written out rather than
carried forward" must let a reader reproduce it, and this one does not.**

**Suggested fix (MY SUGGESTION - verify before adopting).** Do not patch the number; the number has
now been patched twice and re-broken twice. Replace the narrative with a ledger that cannot drift,
and delete the terminal count entirely:

> **The table above is the count.** Its history, kept because two earlier revisions carried a stale
> number forward:
>
> | Removed | Rows | Why |
> |---|---|---|
> | §7.1 TLS refusal | C1-S1, C1-T1, C1-I1 | Mitigated, §8 case |
> | `ResponseCaching` dropped | cache-disclosure row | Out of the model entirely, not mitigated |
> | Already-performed remedies | C1-R1, C4-R1 | Listed as blockers while §5.3 stated the remedy |
> | `.gitignore` / `.env.example` committed | C8-I1 | Mitigated, §8 case |
> | This revision | C5-R1, C5-E1 | §5.3 and §7.2 |
>
> C9-T1 was added to the model after this ledger began and never joined the list: its pins and
> frozen resolve are specified in §10 with a §8 case, and the unexecuted capability-drift diff is a
> residual risk rather than an implementation blocker.
>
> **Whoever changes the table adds a row here in the same edit. No sentence in this section states a
> total.**

The ledger is verifiable row by row and has no total to go stale. It also settles the 7-vs-5
question by forcing whoever writes it to name the starting set. **Cheap - one paragraph rewrite -
but it needs the author to reconstruct the original seven, which I could not do from the document
alone.** That reconstruction is the only non-trivial part.

---

## MEDIUM

### M-1. C5-E1 left the must-mitigate table and landed nowhere. §7.2 says "the residual risk stands"; Residual Risks does not carry it.

**This is the finding the brief asked for, and my answer is more specific than "yes it is a
documentation test".**

**Is the C5-E1 mitigation a real control or a documentation test wearing one's clothes?** It is a
documentation test. §8's case asserts the read-only-key requirement *"is present in the README
deployment section and in `CREDENTIAL-CHECKLIST.md`"*, **asserted against the committed files**. That
test would pass against a server with no code in it at all. It constrains the repository, not the
deployment, and it reduces the modelled exposure - a write-capable Jobvite credential sitting in a
`JOBVITE_ENABLE_WRITES=false` process - by exactly nothing.

**But the design is not dishonest about this, and I want to be precise, because the honest half is
load-bearing.** It says so in four separate places, in unusually plain terms:

- §7.2: *"an instruction to a human, not a control this server can enforce"*, with two stated
  reasons and *"A reader who takes it as enforced would over-credit the deployment."*
- §7.2: *"**If the answer is no, this requirement is unsatisfiable and the residual risk stands**"*.
- §11 C5-E1's Mitigation cell: *"as an operator instruction with a stated ceiling, not as an
  enforceable control"*.
- §11 threshold disposition: *"C5-E1 left it on weaker terms than the other two and the difference
  matters [...] what closed is our obligation to state and test the requirement, not the underlying
  exposure."*

**So the defect is not the honesty. The defect is that the exposure it names is now carried
nowhere.** §11's own convention 2 states: *"Post-mitigation exposure lives in Residual Risks."*
§11's own selection rule states that a row with **no available server-side remedy** *"is accepted
with a documented rationale and carried to Residual Risks instead"* - and §7.2 establishes there is
no server-side remedy, because no Jobvite endpoint reports a key's permissions and probing is
forbidden by §1.1.

I enumerated the Residual Risks table. It carries **C4-S1, C6-S1, C4-D1, C4-D2, C8-E2, C2-D1, C7-I2,
C9-I1, C9-T1**, plus §5.2 and §1.1. **C5-E1 is absent.**

The document says in prose "the residual risk stands" and then does not stand it anywhere a reader
enumerating residual risk would find it. **This is the identical defect §11 already caught once and
wrote a note about** - the "Note on C4 and duplicate writes" at `:1495`, describing *"a residual risk
named in one section and unmodelled in the section whose job is modelling residual risk"*. Same
shape, new row, one revision later.

**The gate cannot catch this**, and that is worth stating: `check-coupling.py` accepts any row naming
a §8 case that exists. C5-E1 names one. Every control fires, the sweep finds no holes, and this walks
straight through - because it is not a coupling defect, it is a completeness defect in a table the
gate does not read.

**Suggested fix (MY SUGGESTION - verify before adopting).** Two edits, both cheap:

1. Add a row to Residual Risks:

> | The Jobvite credential may be write-capable in a deployment where writes are disabled, and the
> server cannot verify otherwise (C5-E1) | High | No server-side remedy exists: no Jobvite endpoint
> reports a key's own permissions, and probing by attempting a write is the destructive probe §1.1
> forbids. Mitigated only as an operator instruction with a stated ceiling (§7.2), and it is unknown
> whether Jobvite issues read-only keys at all. `CREDENTIAL-CHECKLIST.md` carries that question for
> the first key request; if the answer is no, this exposure is undiminished. |

2. In the threshold-disposition paragraph, after *"not the underlying exposure"*, add:
   *"which is therefore carried to Residual Risks below, as §11's own selection rule requires of a
   row with no available server-side remedy."*

**I considered and rejected rating this High.** It would be High if the design claimed enforcement it
does not have; it does the opposite, four times over. What is missing is one table row and one
cross-reference. But it is squarely Medium and not Low, because Residual Risks is the enumeration a
reader trusts to be complete, and an inherent-High exposure absent from it is exactly the gap that
survives a freeze.

### M-2. B42: no `request_id` on success results. Absent from `DESIGN.md` entirely, while the conformance sweep ranks it Tier 2 and ties it to a High row declared mitigated.

**Clauses, verified at source:** `backend/request-middleware.md:142` - *"**Every request gets a
request_id**: No request may complete without a correlation ID on `request.state`."* - and `:144` -
*"**Always echo**: The `X-Request-ID` response header is present on every response (success and
error)."*

**State of the design.** §5.3 mints a UUIDv4 per invocation. §5.1 puts `request_id` on the problem
object and inside its `instance` URN. **Nothing anywhere puts it on a successful result.** I grepped
every `request_id` occurrence in `DESIGN.md`: minting, the problem object, the audit event, retry and
breaker log lines, and the §8 concurrency case. No success path.

**And revision 5 made this worse rather than better, which is the part that decides the severity.**
§5.3's audit-failure branch at `:600-606` now specifies a success-payload envelope in detail:

> the normal success result, `is_error=False`, with a `warnings` array in its structured content
> naming the audit failure. **Not a problem object.**

So a success-path structured-content envelope now exists, is specified to the field, and
`request_id` is still not on it. **The branch where the caller most needs a correlation handle is
precisely the one where the audit record failed to write** - and the caller is handed a warning that
names a failure it cannot cite anything about.

**Consequence for a High row.** C1-R1 (High, *"A write cannot be attributed to a caller"*) is
declared **Mitigated in §5.3** on the strength of the audit event alone. The audit record exists; the
caller holds nothing that points at it. `CONFORMANCE-RESWEEP.md:160` reaches the same conclusion
independently and ranks B42 at Tier 2, *"freezing is defensible only if the blocker list is
honoured"*.

**Why this belongs in this round rather than in the sweep's backlog:** `DESIGN.md` references 24
distinct B-numbers. **B42 is not one of them.** It is not in §11, not in §12's open questions, not in
Residual Risks, not deferred with a reason. It is invisible inside the document about to be frozen,
and after the freeze only a numbered ADR can add it.

**Where the id belongs, settled by execution rather than by preference.** My first draft said "in its
structured content" with a caveat that this might not survive output-schema validation. **The caveat
was correct and the draft wording was wrong**; see "Post-round verification" above for the four
executed arms. Summary:

- **An undeclared top-level `request_id` in `structured_content` is REJECTED.** §2.1's output models
  are `strict=True` with extra keys forbidden, which emits `additionalProperties: false`, and
  `mcp` 2.x's `ClientSession.validate_tool_result` validates structured content against that schema
  unconditionally. Executed: `Additional properties are not allowed ('request_id' was unexpected)`.
  This is the same stack behaviour that broke `ResponseLimitingMiddleware` (§7.7, ADR-0004).
- **Result `_meta` is the correct home.** `validate_tool_result` inspects `structured_content` only
  and never touches `_meta`, so the id cannot be rejected by an output schema. Executed: a
  `CallToolResult` carrying the id in `_meta` validates clean and round-trips through
  serialisation intact.

**Suggested fix (MY SUGGESTION - verify before adopting).**

- §5.1, after the problem-object field list: *"**`request_id` is echoed on every result, not only on
  failures**, per `request-middleware.md:144`. It is carried in the result's `_meta` under
  `com.evolvconsulting.fast-mcp-jobvite/requestId`, **not in structured content**: §2.1's output
  models forbid extra keys, so an undeclared key there is rejected by the client's output-schema
  validation - the same unconditional validation that broke `ResponseLimitingMiddleware` (ADR-0004).
  `_meta` is the protocol's own channel for exactly this class of field; the spec uses it for
  `io.modelcontextprotocol/serverInfo`, which is likewise server-stamped and for display, logging and
  debugging only. Our key is namespaced because `io.modelcontextprotocol/*` is reserved. The problem
  object keeps its own `request_id` member as well, because RFC 9457 membership is what
  `error-contract.md` specifies; the two carry the same value and the `_meta` copy is the one present
  on every result."*
- §8, a required case: *"**every tool result carries `request_id` in its `_meta`, success and
  error** - asserted on a successful read, a successful write, the post-write audit-failure warning
  branch, and an error result, each matched against the id in that invocation's audit event, with an
  arm asserting the value is absent from `structured_content` so the schema stays clean (B42, §5.1,
  §5.3)."*
- Then C1-R1's mitigation cell can honestly say attribution reaches the caller and not only the log.

**What a caller does to read it**, since an id a caller cannot reach discharges nothing:
`CallToolResult.meta` is a normal field on the result, so a raw SDK caller reads
`result.meta["com.evolvconsulting.fast-mcp-jobvite/requestId"]`. FastMCP's own client preserves it -
`ToolResult.from_mcp_result` copies `meta` through (`fastmcp/tools/base.py:159-167`) - so a FastMCP
caller reads `result.meta[...]` too. Server-side we set it with
`ToolResult(..., meta={...})`; `ToolResult.meta` is a first-class constructor parameter in
fastmcp-slim 4.0.0b4 (`fastmcp/tools/base.py:103-119`), documented as *"Runtime metadata about the
tool execution"*. **This is reachable on both transports and needs no client cooperation beyond
reading a field.** The README should document the key name, since a caller cannot guess it.

**The outbound passthrough is confirmed, and it carries two consequences the implementer needs.**
`ToolResult.to_mcp_result()` (`fastmcp/tools/base.py:171`) sets `_meta=self.meta` verbatim at
`:186`, so the value reaches the wire unmodified. But:

1. **Setting `meta` changes which return shape the tool takes.** `:181` reads
   `if self.meta is not None or self.is_error:` - only then is a full `CallToolResult` constructed;
   otherwise `:190` returns the lighter `(content, structured_content)` tuple. Stamping `request_id`
   on every result therefore puts every result on the `CallToolResult` path. That is benign, and it
   is worth knowing it is the same lever `ResponseLimitingMiddleware` was leaning on when it assumed
   a non-`None` `meta` would bypass output-schema validation (§7.7, ADR-0004). **It does not bypass
   validation** - that bypass is what `mcp` 2.x removed - it only selects the richer result type.
2. **A gotcha that fails silently, which is this design's own hunting ground.**
   `to_mcp_result()` short-circuits at `:176-177`: `if self._raw_mcp_result is not None: return
   self._raw_mcp_result`. A `ToolResult` built by `from_mcp_result()` carries that raw result, so
   **setting `.meta` on such an object is silently discarded** - no error, no warning, and the id
   simply never appears. Our tools construct their results rather than wrapping an upstream
   `CallToolResult`, so this should not bite; but it is exactly the shape §8 exists to pin, which is
   why the required case should assert the id **on the wire result**, not on the `ToolResult` object
   the tool returned. Asserting the latter would pass while the former was empty.

**Verify before adopting:** I proved the rejection and the `_meta` survival against `mcp_types` 2.0.0
and the real `jsonschema` validator, and read `ToolResult`, `to_mcp_result` and
`validate_tool_result` in the pinned versions. I did **not** stand up a live server and observe the
id arriving at a client end-to-end, so the composed path - tool returns, middleware chain runs,
client reads `result.meta` - is assembled from verified parts rather than executed as a whole.

### M-3. §5.3 cites `ai/tool-calling.md:171-173`, and the obligation it does not discharge is at `:176-177`, just past the end of the cited range.

**The full clause**, read at source (`ai/tool-calling.md:171-177`):

> - **Log every tool invocation** - tool name, validated arguments (PII redacted), result status,
>   latency, and the request correlation id. Use the canonical triple verbatim: HTTP header
>   `X-Request-ID`, log field `request_id`, ContextVar `request_id_var` [...]
>   **Also attach the LLM trace/span id so a tool call ties back to its turn (trace IDs are separate
>   from `request_id`).**

§5.3 cites `:171-173` and says it *"names the fields: tool name, validated arguments with PII
redacted, result status, latency, correlation id."* That is accurate for `:171-173`. **The bullet does
not end at `:173`.** Its final sentence is a second, separate obligation, and the design neither
discharges it nor says it cannot.

Two things make this more than a range typo:

1. **ADR-0005 makes the `ai/` domain bind in full**, and says so in those words: *"Obligations
   B9-B26 apply in full."* This is inside one of them.
2. **The conformance corpus missed it too.** B17's row cites `:171-172` and `:178-179`, skipping
   `:176-177`. So no B-number tracks it, no sweep verdict covers it, and no ADR scopes it out. It is
   invisible in every instrument the project has.

**THE OBLIGATION IS SATISFIABLE, AND THE MECHANISM ALREADY EXISTS IN OUR PINNED STACK.** My first
draft of this finding asserted the opposite - that MCP carries no trace context and the clause should
be scoped out by ADR. **That assertion was false and I retract it.** It was reasoning from an absence
in our research corpus, which is a fact about what we searched and not about the spec. See
"Post-round verification" above for the executed evidence. The corrected finding follows.

**What the pinned stack actually does** (all executed against the real artifacts, not documentation):

- **MCP 2026-07-28 carries W3C trace context in request `_meta`, per SEP-414.** `mcp==2.1.1` -
  the exact pinned version - injects `traceparent`/`tracestate` into every outgoing request's `_meta`
  at `mcp/shared/jsonrpc_dispatcher.py:390`, inside a `SpanKind.CLIENT` span on the request-send path.
- **`opentelemetry-api>=1.28.0` is a hard dependency of `mcp` 2.1.1.** It is already in our tree, so
  this costs no new dependency and does not touch §10's three-pin block.
- **FastMCP 4.0.0b4 already extracts it server-side.** `fastmcp/server/telemetry.py:95` calls
  `extract_trace_context(req_ctx.meta)`, and `fastmcp.telemetry.extract_trace_context` is **public**
  (listed in `__all__`). Its own docstring names the accessor a tool uses:
  **`ctx.request_context.meta`**.

So the trace id the clause asks for is reachable from inside a tool, today, on the pinned stack, with
a public API and no new dependency. **This is an implementation obligation, not an ADR** - which
makes it a larger fix than the one I first proposed, not a smaller one.

**Suggested fix (MY SUGGESTION - verify before adopting).** Add to §5.3, after the "What this does
not do" paragraph:

> **The host's trace id is attached when the host supplies one.** `ai/tool-calling.md:176-177`
> separately requires attaching *"the LLM trace/span id so a tool call ties back to its turn (trace
> IDs are separate from `request_id`)"*, and unlike ADR-0009's approver identity this one is
> reachable. MCP carries W3C trace context in request `_meta` per SEP-414; `mcp` injects
> `traceparent`/`tracestate` on the sending side, and FastMCP extracts it server-side, so a tool
> reads it at `ctx.request_context.meta`. The audit event therefore records `trace_id` and `span_id`
> parsed from the inbound `traceparent`, **beside `request_id` and never merged with it** - they
> answer different questions, and §5.3's own warning that `request_id` is a within-invocation key
> rather than a distributed trace id is exactly why both are recorded.
>
> **Recorded when present, absent otherwise, and never synthesised.** A host that does not propagate
> trace context sends no `traceparent`, and a locally-minted substitute in a field named for the
> host's trace would join nothing while looking like it did. The audit event omits the fields rather
> than inventing them. **Which hosts actually propagate is unverified** - the same limitation §7.5
> records for the host survey - so this is written to the wire contract, not to any measured client.

Plus a §8 case: *"the audit event carries `trace_id` and `span_id` when the request `_meta` supplies a
`traceparent`, and omits them when it does not - both arms, since a field that is always absent and a
field that is always synthesised both pass a single-arm test."*

**Why this stays Medium rather than rising.** It is one required-standard obligation, undischarged
and invisible in every instrument the project has (no B-number, no sweep verdict, no ADR). The fix is
a paragraph, a parse, two audit fields and a two-arm test. But it is now clearly implementation and
not a scoping decision, so **it must not be written as ADR-0012.**

**Verify before adopting:** I confirmed the injection call site, the extraction call site and the
public API by reading the pinned wheels. I did **not** run a live client-server pair to observe a
`traceparent` arriving in `ctx.request_context.meta`, and FastMCP's `telemetry_mode()` can be `off`,
in which case `extract_trace_context` returns the ambient context unchanged. The raw value is still
readable from `ctx.request_context.meta` regardless of telemetry mode, which is why the fix above
reads the meta rather than depending on FastMCP's span plumbing - but that specific path is reasoned,
not executed.

**One incidental catch from the same clause, worth an editor's eye:** the ContextVar name
`request_id_var` that §5.3 introduces as its own design choice is in fact **mandated verbatim by
`ai/tool-calling.md:173-175`** ("the canonical triple verbatim [...] ContextVar `request_id_var`").
The design happens to comply and does not know it. Citing the clause there would convert a choice
into a discharged obligation at no cost.

---

## LOW

### L-1. `utils/correlation.py` is specified in §5.3 and missing from §3's module layout.

§5.3 at `:542`, added by revision 5 to close B40: *"`utils/correlation.py` holds a single
`ContextVar[str | None]` named `request_id_var`."* §3's module layout at `:234-248` lists twelve
entries, `utils/redaction.py` and `utils/normalise.py` among them. **`utils/correlation.py` is not
there.** It is the only module named in the body and absent from the layout.

This is the signature of the change the brief flagged - one editor closing a blocker and not sweeping
the sections the new mechanism touches.

**Suggested fix (MY SUGGESTION - verify before adopting).** Add to the §3 block, between
`utils/redaction.py` and `utils/normalise.py`:

```
  utils/correlation.py        request_id_var, the invocation ContextVar (§5.3)
```

Trivially cheap. Worth also checking in the same pass whether `errors.py` or `server.py` should be
described as reading it, since §5.1's problem object and §5.3's retry hooks both consume the value.

### L-2. §5.3 states as a design property something that is true only before mitigation, and it contradicts the §8 case a Critical row depends on.

`DESIGN.md:601`, bolded and unqualified:

> **The audit stream holds candidate PII by construction**, because the approval request describes
> the candidate about to be written.

`DESIGN.md:1114`, a required §8 case:

> **candidate PII never reaching a log or audit record**

These cannot both be true as written. C7-I1 (**Critical**) and C4-I1 both name that §8 case as their
test, so the assertion the implementer writes is decided by which sentence they read.

The design's intent is recoverable and correct - PII enters the audit path by construction, and the
single redaction point of §4.1 keeps it out of the emitted record. C4-I1 models exactly this and
rates it Medium **inherent**, which per §11 convention 2 is the pre-mitigation reading and is right.
**The defect is that §5.3 repeats the inherent-risk phrasing as a standing design property**, in a
section describing the built system, and uses the word *stream* - which everywhere else in §5.3 means
the emitted output (*"the audit stream that just failed"*, `:596`).

**Suggested fix (MY SUGGESTION - verify before adopting).** Rewrite `:586-588` in place - do not
append:

> **Candidate PII reaches the audit path by construction**, because the approval request describes
> the candidate about to be written, so `approval_state` falls inside §4.1's single redaction point
> rather than beside it. **What is emitted carries no PII in the clear**, which is what §8's case
> asserts and what C7-I1 and C4-I1 rest on; the audit stream is nonetheless handled in the same
> sensitivity class as the log stream, because redaction is a control and not a guarantee.

**I considered Medium and settled on Low**: the reconciling mechanism is in the adjacent clause, the
threat row is modelled correctly, and no design decision changes. It is a precision defect in a
document that holds itself to precision.

### L-3. `DESIGN.md:474` cites `:211` for `about:blank`. The rule is at `:212`.

§5.1's registry table, final row:

> | Anything unmapped | `about:blank` per `:211` | - |

Read at source, `architecture/error-contract.md`:

- `:210` - *"7. **Type URIs are stable**: Once published, a `type` URI is a contract."* (correctly
  cited at `DESIGN.md:464`)
- `:211` - *"8. **Relative type URIs**: Use `/problems/<slug>`, not absolute URLs."*
- `:212` - *"9. **`about:blank` for unknowns**: Unmapped HTTP errors use `about:blank` as the type."*

Off by one. The cited line is a real and relevant rule, which is why it survived five rounds - it does
not read as wrong.

**Suggested fix (MY SUGGESTION - verify before adopting).** Change `:211` to `:212` in that table row.
One character. Verify by re-reading `error-contract.md:212` rather than trusting this note.

### L-4. §11's threshold prose merges the Medium production-release list with the Critical/High must-mitigate table, and credits a Medium row with emptying the High table.

`DESIGN.md:1651-1660`. The paragraph is headed **"Mitigate before production release (inherent
Medium, unmitigated)"** and then says:

> **C9-D1 (B72), C5-R1 (B39, B40) and C5-E1 (B21) have now left it too**, which empties the
> must-mitigate table above

Three problems in one sentence. **C5-R1 and C5-E1 are High rows** - they were never on the Medium
production-release list, so they cannot have "left it". **C9-D1 is Medium**, so it left the Medium
list and its departure has nothing to do with the must-mitigate table. And *"which empties the
must-mitigate table above"* is true only of the two High rows.

The individual facts are each right; the grouping asserts a false one. A reader reconstructing which
obligation sat on which list gets the wrong answer for all three.

**Suggested fix (MY SUGGESTION - verify before adopting).** Split the sentence along the two lists:

> **C3-T1 (B25) and C3-D1 (B30) have left this list**: §2.1 now specifies the control-character and
> encoding rejection and the four structural limits, each with a §8 case. **C9-D1 (B72) has left it
> too**, since §10 now carries the advisory-triage policy with a §8 case for the expiry.
>
> **Separately, and on the Critical/High table above rather than this one: C5-R1 (B39, B40) and
> C5-E1 (B21) have left the must-mitigate table**, emptying it - §5.3 carries the `request_id_var`
> mechanism and the retry and breaker logging, and §7.2 the read-only-key requirement. **C5-E1 left
> on weaker terms than C5-R1 and the difference matters:** [...existing sentence unchanged...]

Note this fix and H-1's must land in the same pass; both touch the same two paragraphs.

### L-5. Every breaker transition is required to carry a `request_id`, and nothing constrains the breaker to be call-driven, which is the only condition under which it can.

§5.3 at `:552-556`: *"every breaker transition logs the direction (`closed->open`, `open->half_open`,
`half_open->closed`) and the counter that triggered it"*, each carrying `request_id`. §8's required
case asserts *"every retry and breaker-transition log line carries the invocation's own
`request_id`"*. C5-R1 (**High**) rests on both.

`request_id_var` is a `ContextVar`, and a ContextVar has a value only inside a context that set it.
§5.3 is explicit that `audit.py` sets it per invocation and **resets it in a `finally`**. So a breaker
transition emitted outside any invocation - a background timer expiring the open state into
half-open, which several Python breaker libraries do - logs `None`, and §8's case fails.

**The design never names a breaker library** (§4.3 says only "one circuit breaker for Jobvite";
`CONFORMANCE-RESWEEP.md` Tier 3 notes `circuitbreaker` is unnamed, as B47). So whether every
transition occurs on a call path is currently unstated, and the High row's mitigation is contingent
on an implementation choice nobody has recorded.

**Why Low rather than Medium:** §8's concurrency case would catch it on the first CI run against a
timer-driven breaker, so it self-corrects at implementation rather than shipping. It is a gap in the
specification, not in the defence.

**Suggested fix (MY SUGGESTION - verify before adopting).** One sentence in §4.3, after the breaker
bullet:

> **The breaker must evaluate its own state transitions on the call path**, not from a background
> timer. This is a constraint the design places on the implementation rather than an observation:
> §5.3 carries `request_id` to the transition log line through a ContextVar that exists only inside
> an invocation, so a transition emitted from a timer would log a null id and fail §8's case. A
> lazily-evaluated breaker - one that checks the open-state deadline when the next call arrives -
> satisfies this naturally; the library chosen must be checked against it. The breaker is already one
> of the two mechanisms §12 records as designed and never executed.

**Verify before adopting:** I did not survey Python breaker libraries to confirm the common ones are
call-driven. I believe they are, which is why the constraint is cheap, but that belief is reasoning
and this project's standard is that reasoning gets labelled.

### L-6. The 30-day advisory expiry is specified as behaviour with no named mechanism, and `pip-audit` cannot provide it.

The brief asked directly whether the expiry exists anywhere enforceable or is prose. **It is better
than prose and short of a mechanism.**

In its favour, and this is real: §10 step 3 specifies the record precisely (advisory id, date, reason,
expiry no more than 30 days out, in `pyproject.toml`), and §8 carries a required case - *"an expired
advisory-ignore entry fails the audit gate [...] with a positive control showing an unexpired entry is
honoured"* - which is a properly-formed test with both arms. That is more than the earlier "detected
and logged" gap-check the design itself criticises for having no mechanism.

What is missing is the wiring. **`pip-audit` has no expiry concept and no `pyproject.toml` config
section for ignores** - it takes `--ignore-vuln` on the command line. So the entries §10 specifies
must be read by something that both (a) emits the `--ignore-vuln` flags and (b) fails the build on an
expired entry. Nothing in §10, §8 or §3 names that something. §10 says *"CI fails on an expired
entry"* in the passive, which is the construction that hides a missing owner.

The risk if it stays unnamed: the entries get written into `pyproject.toml`, the ignores get passed to
`pip-audit` by hand on a separate line, and the two drift - which is the exact
two-hand-maintained-lists defect §2.1 and §10.1 both name and design around elsewhere.

**Suggested fix (MY SUGGESTION - verify before adopting).** Name the reader, and make it the single
source, in §10 step 3:

> [...] and **an expiry date no more than 30 days out**. `pip-audit` supports neither expiry nor a
> `pyproject.toml` ignore section, so a CI step reads this table and is the only thing that does: it
> emits the `--ignore-vuln` flags for unexpired entries and exits non-zero on any entry past its
> expiry. **The flags are never written by hand** - deriving them from the same table that carries the
> expiry is what stops an ignore outliving its justification, in the same way §10.1 derives the
> README's configuration table from `.env.example` rather than maintaining both.

**Verify before adopting:** confirm `pip-audit`'s current CLI still lacks a config-file ignore section
before asserting it in a document that will be frozen. I checked this against its documented
interface, not by running it.

---

## NIT

### N-1. §4.3 cites a bare `resilience.md:74-76` and there are two files by that name.

`DESIGN.md:318` quotes *"Timeouts MUST be shorter than the inbound request's own deadline"* and
attributes it to `resilience.md:74-76`. The corpus holds **`backend/resilience.md`** and
**`ai/resilience.md`**. The quote is correct for `backend/resilience.md:74-76` - I read it and it
matches word for word. But `ai/resilience.md:74-76` is a `@retry(...)` code block, so a reader
resolving the bare name against the wrong file finds something plausible and unrelated.

§5.3 cites the same file correctly as `backend/resilience.md:224-226`, so the document is inconsistent
with itself about the prefix.

**Suggested fix (MY SUGGESTION - verify before adopting).** Change `resilience.md:74-76` to
`backend/resilience.md:74-76` at `DESIGN.md:318`. Worth a grep for other bare filenames that resolve
ambiguously - `testing.md` and `README.md` are the other multi-home names in this corpus.

---

## The ADR pass, since nobody had run one

All eleven read in full, every citation resolved. They are sound: ADR-0002's scope genuinely disposes
of `:361-362` and rule 5, ADR-0006 genuinely disposes of B97/B98/B99, ADR-0009's approver-versus-caller
split is exactly as §5.3 and §13 describe it, and ADR-0008 makes the scope argument rather than the
refuted priority one. **No ADR claims a `file:line` that does not say what it claims.**

**One staleness worth an editor's pass, recorded but not filed as a finding** because §13 separates
ADRs from the freeze: **ADR-0011's closing section is now out of date.** It says B40's
`request_id_var` is *"missing"*, calls C5-R1 *"on the must-mitigate list"*, and says *"Until that
lands, this deviation costs more than it should"*. Revision 5 landed it and emptied the table. §13's
own summary of ADR-0011 already states the corrected position (*"which §5.3 now propagates through
`request_id_var` (B40 closed in this revision)"*), so the design and the ADR it summarises now
disagree. **Suggested fix (MY SUGGESTION):** rewrite ADR-0011's final two paragraphs in place to read
that the correlation mechanism now exists in §5.3 and what remains is the deviation itself - three
records where the clause asks for one. I did not count this in the tally because the freeze rule
scopes to `DESIGN.md`, but whoever applies the fixes should take it in the same pass.

---

# BLUE ROUND 1 - Normal Response

**H-1 - ACCEPT, in full, as a freeze blocker.** There is no defence. The paragraph asserts a count
that contradicts the table three lines above it, and the paragraph itself says what that means. The
arithmetic break is a separate and independently verifiable defect in the same paragraph. I accept the
ledger fix in principle; the author must reconstruct the original seven, and if that cannot be done
from the record, the honest ledger starts at the earliest state that can be reconstructed and says so.

**M-1 - ACCEPT.** The temptation is to argue that §7.2 and the threshold paragraph already say
everything a reader needs, so the Residual Risks row is redundant. I reject that on the document's own
precedent: it made exactly this argument's opposite for C4-D2 and wrote a note explaining why the row
had to exist. Consistency with that decision requires the row.

**M-2 - ACCEPT.** No defence available. The clause is unambiguous, the sweep flagged it twice across
two revisions, and revision 5 specified a success envelope without putting the id on it. The only
thing I would push back on is the implementation detail of *where* the id lives, which is why the
finding carries that caveat rather than a confident one-liner.

**M-3 - ACCEPT, with one qualification.** The qualification: this is arguably a defect in the
conformance sweep rather than in `DESIGN.md`, since B17's row is what should have caught it. But
`DESIGN.md` §5.3 is the section that discharges the clause and presents `:171-173` as the field list,
and the freeze puts §5.3 behind the ADR process. It has to be settled here.

**L-1 through L-6 - ACCEPT.** L-3 and L-1 are one-line edits. L-2 and L-4 are in-place rewrites of
prose, not appends. L-5 and L-6 each add a constraint the implementer would otherwise have to invent,
which is what this document is for.

**N-1 - ACCEPT.**

**One defence I do want to enter, on the document's behalf.** Five rounds of adversarial review have
made this design unusually resistant to the attacks I brought. I went looking for the four named
failure modes and found: no fabricated measurement, no citation that misrepresents its source except
one off-by-one, no test name that does not match its described body, and no section claiming a
mechanism the design does not specify - **except in the two enumeration gaps above**. The gates are
not decorative: 29 controls fire, 184 sweep substitutions produce zero holes, and the sweep is pointed
at the exact escape R5 found. That is a real instrument, and it is the reason the defects left are the
ones no instrument reads.

---

# RED ROUND 2 - Adversarial Rebuttal

**Against my own H-1: am I inflating a proofreading error into a High to justify a sixth round?**

Test it against the freeze rule rather than against my instinct. The rule has exactly two conditions,
and one of them is *"§11's must-mitigate table is empty"*. §11 contains a bolded, twice-stated count
saying two rows remain. If a reader verifies the freeze condition by reading §11 - which is where the
rule sends them - **they get the wrong answer**. A defect that makes the freeze condition itself
unverifiable from the section it names is not proofreading. It stays High.

The counter-argument I take seriously: the table is unambiguous, and a careful reader trusts the table
over the prose. True. But this document's whole method is that a reader should not have to adjudicate
between two of its own sentences, and it says so in that very paragraph.

**Against M-1: is C5-E1's absence from Residual Risks actually harmless, since §7.2 says it at
length?**

No, and here is the test that settles it. Ask what a reader does with Residual Risks. It is the
enumeration you hand an integrator, a security reviewer, or the next maintainer as "here is everything
we accepted and why". Nine risks are in it. A tenth - an inherent **High**, whose post-mitigation
exposure is undiminished, and which the design admits may be *unsatisfiable outright* if Jobvite
issues no read-only keys - is not. Anyone working from that table under-counts the accepted High
exposure by one, and the one they miss is a live write-capable ATS credential.

**Against M-2: is B42 within scope for a design review, or is it a conformance-sweep item?**

Both instruments exist to catch different things and this fell between them. The sweep caught it and
ranked it Tier 2; the design does not mention it. The freeze is the event that makes the design's
silence permanent. If round 6 declines it because "the sweep has it", then the freeze happens and the
sweep's Tier 2 item now requires an ADR to fix. In scope.

**Against M-3: am I manufacturing an obligation from half a bullet?**

The strongest counter is that the trace/span sentence is parenthetical to a logging bullet, and no
B-number tracks it. But the sentence is imperative - *"Also attach"* - in a `priority: required`
standard that ADR-0005 says binds in full, and the design's cited range stops one line short of it. I
checked whether the design addresses it elsewhere: `:561` disclaims that `request_id` is a distributed
trace id, which shows the author was thinking about the distinction and still did not discharge the
clause. If anything that strengthens it - the concept was in view and the obligation was not answered.

The honest weakness: I am confident MCP carries no trace context, but I did not exhaustively check the
`2026-07-28` spec for a trace extension. **The suggested fix asserts that MCP carries no trace context,
and that assertion must be verified before it goes into a document about to be frozen.** If it turns
out MCP does carry one, M-3 stops being a "record it as unsatisfiable" fix and becomes a real
implementation obligation - a larger fix, not a smaller one.

> **[SUPERSEDED - this paragraph is the round's reasoning as it stood, and its confidence was
> misplaced.]** MCP *does* carry trace context: SEP-414, W3C `traceparent`/`tracestate` in request
> `_meta`, injected by `mcp` 2.1.1 and already extracted by FastMCP 4.0.0b4. M-3 became exactly the
> larger fix this paragraph anticipated. The doubt was right and the confidence was wrong. See
> "Post-round verification" near the top for the executed evidence and the full retraction. Kept
> rather than deleted, because the caveat is the only reason a false claim did not reach a frozen
> document, and that is the part worth being able to point at.

**Against the whole round: five rounds have run and no code exists. Is a sixth round the
highest-value activity?**

I do not think a seventh is, and I say so in the verdict. But this round found a High that would have
frozen a document contradicting its own freeze condition, and two Mediums that the freeze would have
locked behind an ADR. That is not zero. It is, however, a different *kind* of finding than rounds 1 to
4 produced, and that difference is the signal.

---

# BLUE ROUND 2 - Final Normal Response

I accept the rebuttals. Two adjustments to how the findings should be read:

1. **M-3's suggested fix carries an unverified premise** and must not be pasted in. The claim "MCP
   carries no trace context to a server on either transport" needs checking against the `2026-07-28`
   spec before it becomes a frozen sentence. This is the project's own standing lesson: an
   impossibility claim needs a higher bar than a defect claim.
   **[Resolved after the round: the premise was FALSE. The check was run, MCP carries W3C trace
   context per SEP-414, and M-3 is now an implementation obligation rather than an ADR. The finding
   above has been rewritten; see "Post-round verification".]**

2. **H-1's ledger fix needs the original seven reconstructed**, and I could not do it from the
   document. If the record does not support it, the ledger should start where the record does and say
   so, rather than inventing a starting count - which would reproduce the defect it fixes.

Everything else stands as written.

---

## Final report

| # | Sev | Finding | Fix cost |
|---|---|---|---|
| H-1 | **High** | §11's count paragraph says "Two" over an empty must-mitigate table (3rd recurrence), and its written-out arithmetic drops four rows while subtracting two | One paragraph rewrite; needs the original seven reconstructed |
| M-1 | **Medium** | C5-E1 left the must-mitigate table and is absent from Residual Risks, though §7.2 says "the residual risk stands" | One table row + one cross-reference |
| M-2 | **Medium** | B42: no `request_id` on success results; absent from `DESIGN.md` entirely; undercuts C1-R1 (High) | Two sentences + one §8 case. **Verified:** it goes in result `_meta` - structured content rejects it |
| M-3 | **Medium** | `ai/tool-calling.md:176-177`'s LLM trace/span id obligation falls outside §5.3's cited range and is discharged nowhere | **Verified: an implementation obligation, NOT an ADR.** MCP carries W3C trace context per SEP-414 and FastMCP already extracts it. Parse + two audit fields + a two-arm §8 case |
| L-1 | Low | `utils/correlation.py` specified in §5.3, missing from §3's module layout | One line |
| L-2 | Low | §5.3's "audit stream holds candidate PII by construction" contradicts §8's "never reaching a log or audit record" | In-place rewrite of one sentence |
| L-3 | Low | `DESIGN.md:474` cites `:211` for `about:blank`; the rule is `:212` | One character |
| L-4 | Low | §11 threshold prose merges the Medium list with the High must-mitigate table | Split one sentence |
| L-5 | Low | Breaker-transition `request_id` requires a call-driven breaker; nothing says so | One sentence in §4.3 |
| L-6 | Low | The 30-day advisory expiry names no mechanism; `pip-audit` cannot supply one | One clause in §10 step 3 |
| N-1 | Nit | Bare `resilience.md:74-76` is ambiguous between two files in the corpus | One path prefix |

Plus, outside the tally because §13 separates ADRs from the freeze: **ADR-0011's closing section is
stale** and now contradicts §13's summary of it.

**Answers to the three questions the brief asked directly:**

1. **Is C5-E1 honestly mitigated, or is it a documentation test wearing a control's clothes?** It is a
   documentation test, and the design says so four times in plain terms - so the dishonesty the brief
   feared is not there. The real defect is narrower and is M-1: the exposure left the must-mitigate
   table and was not carried to Residual Risks, so the honest ceiling §7.2 states is nowhere in the
   enumeration a reader trusts to be complete. And yes - the gate accepts it because it names a §8
   case that exists. The gate cannot see this class.
2. **Does the `request_id_var` concurrency argument hold?** **Yes.** A ContextVar is copied per asyncio
   Task, so concurrent invocations cannot interleave ids, and the `finally` reset covers reuse within a
   task. The argument in §5.3 is correct as stated, and the mandated name `request_id_var` is the
   standard's own (`ai/tool-calling.md:173-175`), which §5.3 could cite and does not. The one gap is
   L-5: it holds for retries unconditionally and for breaker transitions only if the breaker is
   call-driven.
3. **Does the 30-day expiry exist where it can be enforced?** Partly. The record is specified precisely
   and a §8 case with both arms exists - better than prose. But no component owns the check and
   `pip-audit` cannot perform it, so the ignores and the expiries can drift apart. L-6.

---

## Freeze recommendation, and whether a round 7 is worth running

**DO NOT FREEZE this revision.** One High and three Mediums; the rule is 0C/0H/0M.

**But do not schedule a round 7 as a review round either.** This is the substantive recommendation,
and I mean it as a finding rather than as a way out of more work.

Here is the evidence for it, from this round specifically:

- **Nothing I found is a design defect.** Not one finding says the design would behave wrongly if
  built as written. H-1 is a stale count. M-1 is a missing table row. M-2 and M-3 are obligations
  nobody discharged. The Lows are cross-reference and precision defects. Rounds 1 to 4 found reasoning
  errors - an inverted pagination probe, a dangerous SIGTERM one-liner, an inert `hasattr` branch, a
  `400` that should have been `422`. **Round 6 found bookkeeping.** That is a different distribution
  and it is the signal that the seam has moved.
- **The instruments now outperform the reviewers on the classes they cover.** 29 controls fire, 184
  sweep substitutions yield zero holes, and the sweep specifically kills R5's escape. Everything I
  found lives outside what those scripts read - which means the next reviewer's yield is bounded by
  the same blind spot, not by their diligence.
- **The spike sample was clean at ten for ten**, including every number the design calls "Measured". A
  seventh reviewer re-auditing it is unlikely to find the eleventh claim is the bad one.
- **Two of my three Mediums came from the conformance sweep, not from reading the design harder.** B42
  and the trace/span clause were both discoverable by cross-referencing an existing document. A
  reviewer with no new instrument is now mining artifacts that already exist.

**What I recommend instead.** Apply these eleven fixes - they are perhaps two hours of editing, and
only H-1's ledger and M-3's ADR need a decision rather than a keystroke. Then **re-run the three gates
and take a single targeted confirmation pass over §11 and §5.3 only** - the two sections every fix
touches - rather than a full sixth-style round. If that pass is clean, freeze and build.

**The reason to stop reviewing is not fatigue, it is that the next class of defect is only reachable
by execution.** §12 names two mechanisms designed and never run. §8 specifies roughly two dozen
required cases, none of which exist. The design's own most valuable property - that it distinguishes
executed from reasoned - means it already knows where its unverified surface is, and no amount of
reading will convert one into the other. The concurrency assertion in §8's `request_id_var` case, the
breaker's transition path (L-5), the advisory-expiry checker (L-6), the composed SIGTERM snippet that
§7.4 admits has never been run end to end on HTTP - **every one of those is settled by the first CI
run and by nothing else.** Round 7 should be a test suite.
