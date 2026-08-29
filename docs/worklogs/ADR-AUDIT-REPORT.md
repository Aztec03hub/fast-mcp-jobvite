# ADR-AUDIT-REPORT - seven ADRs, read against the frozen design

**Agent:** `adr-audit`. **Read-only.** Nothing in this repository was edited, committed or branched
except this file, which the orchestrator commits.

**Repo state when this was written:** `main` at `8f5bb6f` (`git log --oneline -1`).
**Design read as** `git show c15b138:docs/DESIGN.md`, dumped once to `/tmp/D.md`
(`wc -l` = **2045**). Every `DESIGN.md:<n>` in this report is an `awk`/`grep -n` line number taken
off that dump, never counted by eye inside a window.

**My seven:** 0023, 0027, 0028, 0030, 0031, 0032, 0033. 0024/0025/0026 are the orchestrator's and
were not read.

---

## The one-line answer per ADR

| ADR | later section? | relation to Decision | DESIGN.md edit needed | already applied? |
|---|---|---|---|---|
| 0023 | **Ruling** | **AGREES, and OVERRIDES a stale bullet INSIDE the same ADR** | **NO-DESIGN-CHANGE** | n/a (no design edit exists to have been applied) |
| 0027 | **Ruling** | AGREES on substance, **NARROWS** one option to one | YES - add `JOBVITE_OUTBOUND_BUDGET_SECONDS` | **NO** (`grep -c` = 0) |
| 0028 | **Ruling** | AGREES | YES - `sampling` -> `mrtr`, two sites | **NO** (`sampling` at `:687`, `:1280`) |
| 0030 | none | - | YES - and **the ADR does not say where**; see below | **NO** |
| 0031 | none | - | YES - one registry row | **NO** |
| 0032 | none | - | YES - three sites (§7.7 prose, C2 heading, C2 row) | **NO** |
| 0033 | none | - | YES - §5.3 names the four values as a closed set | **NO** |

**Nothing on my list is already applied.** Establishing that once, cheaply and for all seven:
`grep -o 'ADR-00[0-9][0-9]' /tmp/D.md | sort -u` returns
`ADR-0001 … ADR-0011, ADR-0012, ADR-0013, ADR-0017, ADR-0018, ADR-0021` and **nothing above
0021**. Each ADR below is additionally confirmed by grepping for its own subject matter.

**Two of the three ADRs carrying a Ruling do not contradict their Decision.** The
contradicting ones in this batch are 0024/0025/0026, which are not mine. The trap on my seven is a
different one and it is real: **ADR-0023 contradicts ITSELF**, and the Ruling settles it.

---

## ADR-0023 - `docs/adr/0023-harnesses-drop-e-from-strict-mode.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Standards deviation
```

Sections (`grep -n '^#\{1,4\} '`, minus two false hits at `:160-161` which are shell comments
inside a fenced block, not headings):

- `:1` `# ADR-0023: the harnesses run set -uo pipefail, where bash.md:40 mandates set -euo pipefail`
- `:13` `## Context` - `:15` The clause, quoted at source; `:53` What is actually in the tree,
  measured; `:69` Why `-e` is not a cosmetic difference here, measured both ways; `:106` The
  compliant alternative, stated so it is a choice and not an oversight
- `:125` `## Decision`
- `:165` `## Consequences`
- `:181` `## What this ADR does not settle`
- `:193` `## Ruling, 2026-08-29` - `:204-205` a single H3 split across two `###` lines
  (*"Re-measured at `5eb64b0`, because the ADR's evidence was taken at `2d20ed6` and I have added /
  blocks to that file since"*). **Nit, with a fix:** join those two lines into one `###` heading; a
  heading-extracting checker sees two headings today.

### 2. What the Decision says

Keep `set -uo pipefail` (drop only `-e`) in the measurement harnesses, and record it as a
**deviation** from `bash.md:36-41` rather than as compliance. The scope is stated **by PURPOSE, not
by path**: anything whose measurement is the exit code of a command expected to fail.

### 3. The later section, and the contradiction it resolves

**A Ruling exists (`:193`) and it AGREES with the Decision. But the Decision and the ADR's own
"What this ADR does not settle" section CONTRADICT each other, and the Ruling picks the Decision.**

Decision, `:133-137`, whole sentence:

> **Scope, stated by PURPOSE and not by path.** This ADR covers **anything here whose measurement
> is the exit code of a command that is expected to fail** - the control and amputation harnesses in
> `scripts/`, the two probes in `docs/reviews/` that this ADR and its obligation row are evidenced
> by, and **the `run:` blocks in `.github/workflows/ci.yml` that call them**.

"What this ADR does not settle", `:189-191`, whole sentence:

> **It does not cover `ci.yml`.** `bash.md` is `applicable_to: ci-cd`, and every `run:` block in the
> workflow is shell that no strict-mode line governs at all. That is a separate and unmeasured gap,
> recorded in the report rather than decided here.

Ruling, `:195-196`, whole sentence:

> **ACCEPTED**, including the scope stated by PURPOSE rather than by path, and including the
> `ci.yml` `run:` blocks the first draft left out.

**THE RULING WINS: `ci.yml`'s `run:` blocks ARE in scope.** The `:189` bullet is a survivor of the
first draft (the draft the Decision's own italic note at `:140-153` describes replacing) and is now
false. **Suggested fix:** delete the `:189-191` bullet from "What this ADR does not settle", or
rewrite it in place as *"An earlier draft scoped this by artifact type and excluded `ci.yml`; the
Ruling brings the `run:` blocks in."* Do not leave both claims standing - that is the
two-contradictory-claims shape this project keeps paying for.

### 4. THE EDIT to `docs/DESIGN.md`

**NONE. This is a finding, not a gap.** `DESIGN.md` contains no strict-mode, ShellCheck, `bash.md`
or harness-shell subject matter at all:

```
$ grep -ic 'set -e\|strict mode\|shellcheck\|bash\.md' /tmp/D.md
0
```

(The path resolves - `/tmp/D.md` is 2045 lines and other greps against it return hits, so this zero
is a real absence and not a bad-path zero.) ADR-0023's applied home is **`docs/OBLIGATIONS.md` row
`BASH-1`**, which already names it: `grep -n '0023' docs/OBLIGATIONS.md` returns line **146**,
status `SUPERSEDED`, citing `docs/adr/0023-harnesses-drop-e-from-strict-mode.md`. **The applier
must not invent a DESIGN.md edit for this ADR.**

**One question I cannot settle, for the orchestrator** - see the unsettled list: whether §13's list
of deviation ADRs should grow to include 0023.

### 5. Already applied?

Not applicable to `DESIGN.md`. Its obligation row exists. **The in-ADR contradiction at `:189` is
NOT fixed** and is the only outstanding item I found for 0023.

---

## ADR-0027 - `docs/adr/0027-the-budget-must-be-configured-and-the-variable-set-is-closed.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

- `:11` `## Context` - `:13` How this surfaced, and it was a gate catching me; `:30` The conflict,
  stated precisely
- `:40` `## Decision` - `:56` And the count in `test_repo_hygiene.py:81` must stop being a literal
- `:64` `## Consequences` - `:66`, `:77`, `:85`
- `:92` `## Ruling, 2026-08-29` - `:100`, `:117`, `:128`, `:137` What this ruling does not settle

### 2. What the Decision says

The design requires the outbound budget to be **configured** (`DESIGN.md:373-375`) while the
design's variable set does not name a variable for it. Close the gap in the design's favour: the
variable list gains `JOBVITE_OUTBOUND_BUDGET_SECONDS`, and three things land together - the design's
list; the `Settings` field + `.env.example` + README table + `server.json`; and **all three** client
factories (`tools/jobs.py` twice, `tools/candidates.py` once).

### 3. Ruling: AGREES, and NARROWS one thing

Ruling `:94`: **"ACCEPTED as written, including all three landing conditions and the count fix."**

**The one NARROWING, and it changes what the applier may do.** Decision, `:61-62`, whole sentence:

> Derive it from `Settings`, or assert `> 0` and let the closed-set test carry the equality it
> already carries.

Ruling, `:131-133`, whole sentence:

> **Derive it from `Settings`** rather than asserting `> 0`: the closed-set test carries the
> equality, but a `> 0` control no longer proves the parser found more than one variable, which is
> what it exists to prove.

**THE RULING WINS: derive from `Settings`. `assert len(variables) > 0` is no longer permitted.**

I also verified the design line the ADR turns on. `DESIGN.md:373-375`, whole sentence:

> What the clause is *for* still applies, so we satisfy the intent by supplying the deadline the
> transport does not: **a total outbound budget, configured, that bounds all attempts for one tool
> invocation**, so a slow Jobvite surfaces as a typed 503 rather than an unbounded wait.

That citation is exact at `c15b138`.

### 4. THE EDIT

**a) `docs/DESIGN.md` - and the ADR points at the WRONG SECTION. This is my most load-bearing
finding on 0027.**

Decision `:42-43`, whole sentence:

> **§7.6's variable list should gain `JOBVITE_OUTBOUND_BUDGET_SECONDS`, so that §4.3's "configured"
> becomes true.**

`§4.3` is correct - `### 4.3 Resilience` is at `DESIGN.md:342`, and `:373-375` sits inside it.
**`§7.6` is wrong.** In the frozen design:

```
$ grep -n '^#\{2,4\} ' /tmp/D.md   (extract)
1148:### 7.6 Why there is no confirmation token
1165:### 7.7 Middleware
```

§7.6 carries no variable list. **The design's environment-variable enumeration lives in §10.1
Documentation deliverables** (`### 10.1 Documentation deliverables` at `DESIGN.md:1531`), in the
bullet at `:1545-1584`, whose named-variable sub-bullets are `JOBVITE_MAX_RESULTS` at `:1572-1575`
and `JOBVITE_OUTBOUND_RATE_LIMIT` at `:1576-1581`. That is also the block the tests point at:
`tests/test_config.py:576` says *"The variable set is closed. DESIGN.md:1548-1552 makes
`.env.example` the single enumeration"*, and
`test_env_example_and_design_declare_the_same_variables` (`tests/test_config.py:605-607`) diffs
`_env_example_names()` against `_design_names()`, where `_design_names()` (`:587-589`) regexes
`JOBVITE_[A-Z0-9_]+` over **the whole design file**.

**Suggested edit, precisely.** Add a third sub-bullet beside `:1572` and `:1576`, in the same shape:

> - **`JOBVITE_OUTBOUND_BUDGET_SECONDS`**, seconds, default *(unset by this ADR - see below)* -
>   §4.3's total outbound budget, the deadline the transport does not supply. It is required to be
>   **configured** by §4.3, and naming it here is what makes that true.

**and two hazards at that site, both of which will bite a mechanical edit:**

1. `:1563` opens *"**Five variables had no name, and all five have one now**"* and then names five.
   A sixth sub-bullet under a sentence that says "five" is a retyped constant going stale in the very
   bullet whose subject is hand-kept lists going stale (`:1569-1570` says so about itself). **Fix:**
   rewrite `:1563` so it does not carry a count - e.g. *"The variables that had no name have one now
   - ... - and the budget below joins them"* - rather than bumping five to six.
2. `:1583` says *"**Both** are now in `.env.example`"*, referring to the two sub-bullets. A third
   sub-bullet makes "Both" wrong. **Fix:** rewrite to *"These are now in `.env.example`"*.

**b) NOT a DESIGN.md edit but part of the same landing, and the ADR's citation is one line off:**
`assert len(variables) == 15` is at **`tests/test_repo_hygiene.py:82`**, not `:81` as the ADR says
twice (`:35`, `:56`). `:81` is `variables = _declared_variables()`. Verified by numbered read.
Note the function it guards, `_declared_variables()` (`:60-72`), parses **`.env.example`**, not
`Settings`; "derive it from `Settings`" therefore means importing `Settings` into that test and
asserting `len(variables) == len(Settings.model_fields)` (the mapping `_settings_names()` at
`tests/test_config.py:592-593` already exists and is the honest joiner).

**Nothing must be REMOVED from the design** for 0027, beyond the two count-bearing phrases above,
which are rewrites and not deletions.

### 5. Already applied?

**NO.** `grep -c JOBVITE_OUTBOUND_BUDGET_SECONDS /tmp/D.md` = **0**, which is the same measurement
the ADR itself records at `:22-23`.

---

## ADR-0028 - `docs/adr/0028-approval-mechanism-names-a-path-this-design-does-not-use.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

(Preceded by a renumbering note at `:3-8`: this was written as ADR-0027 and renumbered on merge.)

- `:22` `## Context`
- `:56` `## Decision`
- `:73` `## Consequences`
- `:83` `## What this does NOT settle`
- `:98` `## Ruling, 2026-08-29` - `:107`, `:119` The one thing the implementing work must not do

### 2. What the Decision says

Rename the sessionless member of `approval_mechanism`'s closed set from `sampling` to `mrtr` and
keep the set closed at three, because this server has no MCP sampling path - the sessionless era
uses MRTR.

### 3. Ruling: AGREES

Ruling `:100`: **"ACCEPTED. `sampling` becomes `mrtr`, and the set stays closed at three."**
Ruling `:102-105` restates all three amendments and adds one prohibition (`:121-124`): do not
rename the value and leave the code comment that documents the old mismatch standing.

### 4. THE EDIT

**Two sites in `DESIGN.md`, and the ADR's line range for the second one does NOT cover the word it
is telling you to change.**

- **Site 1, §5.3 (`### 5.3 Audit logging and request_id` at `:582`).** `DESIGN.md:686-688`, whole
  sentence:

  > **The audit event also records which approval path produced the response**, in a field named
  > `approval_mechanism`, drawn from a closed set: `elicitation`, `sampling`, `no_handler` - the
  > three paths §7.5 establishes.

  **After the edit** the set must read `` `elicitation`, `mrtr`, `no_handler` ``. The word
  `sampling` is on **line 687**.

- **Site 2, the §8 arm.** ADR-0028 cites this twice as `DESIGN.md:1276-1278` (`:27`, `:61`).
  **Measured, the operative word is on line 1280, outside that range.** `DESIGN.md:1276-1280`, whole
  sentence:

  > - **the audit event is emitted and carries its mandated fields** - tool name, redacted
  >   arguments, result status, latency, `request_id`, the resolved client id on the HTTP transport
  >   and an explicit attribution-unavailable marker on stdio, and on the write `approval_state`
  >   together with the mechanism that produced it - `approval_mechanism`, present and one of
  >   `elicitation`, `sampling`, `no_handler` (§5.3).

  `elicitation,` ends line 1279; `` `sampling`, `no_handler` (§5.3). `` opens line **1280**. **An
  applier who edits only `:1276-1278` changes nothing and its checker still passes** - this is the
  contracted-citation-that-still-resolves hazard, live, on a range the applier is about to trust.
  **Suggested fix:** anchor on the subject, not the range. `grep -n 'sampling' /tmp/D.md` returns
  exactly two lines, **687 and 1280**, and both are the vocabulary. Edit by that grep, and while
  applying, repoint ADR-0028's own `:1276-1278` citations to the range that actually contains the
  set.

Nothing must be REMOVED. The set stays at three members.

Outside the design (stated because the Ruling requires all of it to land together, `:102-105`):
`src/fast_mcp_jobvite/approval.py`'s `ApprovalMechanism.SAMPLING` -> `MRTR`, the two
era-parameterised expectations in `tests/test_approval_write.py`, and the comment at the definition
recording the old mismatch must be **rewritten or deleted, not left** (`:121-124`).

### 5. Already applied?

**NO.** `sampling` is still at `DESIGN.md:687` and `:1280`; `mrtr` / `MRTR` appears in the design
only as the *approval mechanism's prose name* (`:1049` `### 7.5 Human approval (MRTR)`, `:1083`,
`:1115`, `:1750`) and never as a member of the closed set.

---

## ADR-0030 - `docs/adr/0030-the-upstreams-retry-hint-is-dropped-on-every-shape-but-two.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

- `:12` `## Context` - `:14` Where the hint currently survives, quoted at source; `:40` Why the
  obvious objection is weaker than it looks; `:49` The fact that decides the cost, and it is not
  what the raising task assumed
- `:60` `## Decision`
- `:72` `## Consequences` - `:74`, `:80`, `:87` What must NOT happen when this is implemented
- `:99` `## What this ADR does not settle`

**There is NO Ruling, Correction or Addendum section.** The Decision stands alone and is the
operative text.

### 2. What the Decision says

`:62`, whole sentence: **"`retry_after` is populated wherever the upstream supplied one, on whatever
problem shape results."** It stays an optional RFC 9457 extension member; absent means *we were not
told*, never *do not retry*; it never becomes required.

### 3. Later section

None. Nothing to reconcile.

### 4. THE EDIT - **and this is the one ADR of my seven that does not name its own edit site**

ADR-0030 quotes the two design sentences that constrain today's behaviour but **never says "amend
§X"**. It is nonetheless a `Type: Design change` that widens a caller-visible promise
(`:76-78`: *"A caller may now rely on the hint appearing on a 502. That is a promise, and promises
are what the frozen design exists to control."*), so an edit is required and the applier has to
choose the site. The two sentences it quotes, verified verbatim at `c15b138`:

- `DESIGN.md:356-360`, whole sentence:

  > - **An open breaker is distinguishable from an outage without inventing a type.** Both use
  >   `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail`,
  >   which says whether Jobvite failed or whether we have stopped calling it, plus a `retry_after`
  >   hint. An earlier revision minted two slugs for this. The distinction is real and worth making;
  >   a new contract-bearing type URI is not the way to make it.

- `DESIGN.md:361-363`, whole sentence:

  > - **Jobvite's `429`, if it exists, is retried and then mapped to 503**, honouring `Retry-After`
  >   when present. No 429 has ever been observed and no rate-limit header is returned (§4.4), so
  >   this path is written defensively and is unexercised.

`grep -n 'retry_after\|Retry-After' /tmp/D.md` returns **only** `:358` and `:361`. So today the
design mentions the hint on the 503 shapes and nowhere else.

**My recommended edit (a proposal for the orchestrator, not something the ADR authorises by
name).** Add a bullet to §4.3's list immediately after `:363`, i.e. as a sibling of the two above:

> - **A `Retry-After` the upstream volunteered is passed on, on whatever problem shape results** -
>   `retry_after` is an optional RFC 9457 extension member, not a registry row and not a new type
>   URI. Its absence means *we were not told*, never *do not retry*, and callers must tolerate it
>   being absent, which is the common case (§4.4: no rate-limit header is returned). **Only a value
>   the upstream actually sent** is attached; the open breaker's hint is computed from our own
>   remaining window and is ours to compute precisely because it describes our own state (ADR-0030).

**Consider a second, smaller site.** `DESIGN.md:495-497`, whole sentence:

> Failures return `ToolResult(structured_content=<problem>, is_error=True)` carrying a complete RFC
> 9457 problem object: `type`, `title`, `status`, `detail`, `instance`, `request_id`, `timestamp`.
> No `success: true/false` envelope exists anywhere in this repository.

That is §5.1's seven-member list and it says nothing about extension members, while `:1923` calls
them *"the seven RFC 9457 members"*. Nothing there is falsified by ADR-0030 (`retry_after` is an
extension, not an eighth mandated member), so **the seven must NOT be bumped to eight.** If §5.1 is
touched at all it is to add a clause that extension members are permitted and `retry_after` is one -
and if it is left alone, that is defensible. **I flag it rather than deciding it.**

**Nothing must be REMOVED**: `:358` and `:361` are unchanged by this ADR
(`:65-66`, whole sentence: *"The two 503 shapes are unchanged - this widens where the hint may
appear, and changes nothing about where it already does."*).

### 5. Already applied?

**NO.** The design mentions `retry_after` only on the two 503 shapes, which is exactly the state the
ADR describes as needing widening.

---

## ADR-0031 - `docs/adr/0031-the-registry-has-no-row-for-a-refused-approval.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

- `:12` `## Context` - `:14` The registry claims to be complete, and that claim is now false; `:25`
  What the implementation did, and why it was right to flag it
- `:35` `## Decision` - `:41` The precedent is the design's own ...
- `:55` `## Consequences` - `:57`, `:64`, `:71` It does not settle U10-F7, deliberately
- `:78` `## What this ADR does not claim`

**No Ruling / Correction / Addendum.** The Decision is operative.

### 2. What the Decision says

`:37`, whole sentence: **"Add a row: *"An approval was required and none was returned"* ->
`/problems/forbidden`, 403."** And `:39`, whole sentence: **"No new slug. The 403 row now names two
conditions, and `detail` distinguishes them."**

### 3. Later section

None.

### 4. THE EDIT

The registry table is `DESIGN.md:513-521`, seven data rows:

```
513:| Condition | Type | Status |
514:|---|---|---|
515:| Any Jobvite failure, including its 4xx | `/problems/external-service-error` | 502 |
516:| Jobvite unreachable, breaker open, timeout | `/problems/service-unavailable` | 503 |
517:| Argument or schema validation | `/problems/validation-error` | 422 |
518:| Candidate or job id not found | `/problems/resource-not-found` | 404 |
519:| Duplicate candidate on create | `/problems/conflict` | 409 |
520:| Caller's token lacks the scope | `/problems/forbidden` | 403 |
521:| Anything unmapped, including an unhandled exception in a tool body | `/problems/internal-error`, *"Internal Server Error"* | 500 |
```

**Suggested edit:** insert one row **after `:520`**, keeping the 403 rows adjacent:

> `| An approval was required and none was returned | `/problems/forbidden` | 403 |`

**A small ambiguity the applier must not resolve by feel.** `:37` says *add a row*; `:39` says *the
403 row now names two conditions*. Those describe two different diffs - an eighth table row sharing
the slug, versus widening `:520`'s Condition cell to name both conditions. **I recommend the eighth
row**, because `:37` is the sentence in the imperative and because the design's own cited precedent
(`DESIGN.md:356-360`, quoted inside the ADR at `:45-48`) keeps two conditions distinguishable in
prose while sharing one slug. Under the eighth-row reading `:39` is still true: the slug
`/problems/forbidden` then names two conditions. **If the orchestrator disagrees, the alternative is
a one-cell rewrite of `:520` and no new row - but it must be chosen, not defaulted into.**

**Check the sentence immediately above the table before and after.** `DESIGN.md:510-511`, whole
sentence:

> - **`:210` makes a published `type` URI a contract**, so inventing slugs is a promise we would owe
>   forever. The registry already has a type for every condition we produce.

That claim is what ADR-0031 says the new row repairs (`:21-23`). **It stays true after the edit and
needs no change** - adding a row that mints no slug is precisely how it is repaired. (Nit: ADR-0031
cites this as `DESIGN.md:509` at its `:28`; measured, it is `:510`. One line off. Repoint while
applying.)

**Nothing must be REMOVED.** In particular `:529`'s *"seven-member requirement"* is about the seven
RFC 9457 **members** of a problem object (`:496`), **not** about seven registry rows, so an eighth
row does not touch it. I read both to be sure.

### 5. Already applied?

**NO.** `grep -ni 'refus' /tmp/D.md` returns 19 lines, none of them in `:513-521`, and the table has
seven rows with `/problems/forbidden` appearing exactly once.

---

## ADR-0032 - `docs/adr/0032-a-fifth-middleware-runs-that-the-design-never-assessed.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

- `:13` `## Context` - `:15` Measured, at `a38013f`; `:35` What it actually does to us today, and
  the trap in measuring it
- `:67` `## Decision` - `:78` C2 gains: *"the schema-dereferencing middleware rewrites published
  tool schemas"*
- `:85` `## Consequences` - `:87` THE NO-OP IS A PROPERTY OF TODAY'S MODELS, NOT OF THE MIDDLEWARE;
  `:110` `FRAMEWORK_INJECTED_MIDDLEWARE` stays, and is not the same guarantee
- `:116` `## What this ADR does not claim`

**No Ruling / Correction / Addendum.** The Decision is operative.

### 2. What the Decision says

`:69`, whole sentence: **"Adopt it. §7.7 gains a fourth adopted middleware, and C2 gains a row."**
The rejected alternative is `dereference_schemas=False` (`:71-76`), on the grounds that it buys
nothing measurable and trades a real future compatibility property for cosmetic agreement:
*"**Fix the document, which is wrong, not the stack, which is fine.**"*

### 3. Later section

None.

### 4. THE EDIT - three sites

**Site 1, §7.7's adopted list.** `DESIGN.md:1167-1168`, whole sentence:

> Adopted, each constructed with explicit arguments: `Timing`, `StructuredLogging` with
> `include_payloads=False`, and `RateLimiting` with `get_client_id`.

**After:** it must name a fourth, `DereferenceRefs`, and say it arrived framework-injected
(`FastMCP.__init__` appends it whenever `dereference_schemas` is true, which is the default) and is
**adopted rather than disabled**, with the ADR's reason. **HAZARD:** the very next sentence,
`DESIGN.md:1170-1171`, opens *"**These two plus §5.3's `audit.py` make three log producers per
invocation, against a clause that says one**"*. "These two" resolves against the list you are about
to lengthen. **Suggested fix:** name them - *"`StructuredLogging` and `Timing`, plus §5.3's
`audit.py`, make three log producers"* - so the count cannot be broken by a fourth adopted
middleware that produces no log. Do this in the same edit or the sentence silently becomes wrong.

**Site 2, the C2 group heading.** `DESIGN.md:1725`, verbatim:

> **C2. Middleware stack** (§7.7: `Timing`, `StructuredLogging`, `RateLimiting`)

**After:** `` (§7.7: `Timing`, `StructuredLogging`, `RateLimiting`, `DereferenceRefs`) ``. This is
the line ADR-0032 names at its `:27` and it is exact at `c15b138`.

**Site 3, the C2 table.** Existing rows are `:1729` C2-S1, `:1730` C2-T1, `:1731` C2-R1, `:1732`
C2-I1, `:1733` C2-D1, `:1734` C2-E1 - STRIDE, one row per letter, columns
`| ID | Threat | L | I | Risk | Mitigation | Test |`. **Add the row ADR-0032 `:78` names:**
*"the schema-dereferencing middleware rewrites published tool schemas"*, ruled **low**, with the
ADR's stated reasoning (`:80-83`): it rewrites **schemas**, never request or response payloads, so
it cannot carry caller data anywhere; it is downstream of `RequestIdMiddleware`, so anything it logs
is correlated; it has no configuration we set and no credential. Its Test cell should name the
tripwire the ADR describes at `:95-99`,
`test_no_input_model_produces_a_ref_for_the_middleware_to_inline`.

**Two things about site 3 the ADR does not settle, and I am not going to guess them:**

1. **The row has no ID and every STRIDE letter in C2 is already taken.** `C2-T2` is the natural
   choice (it is a tampering-shaped concern) but the ADR never says. See the unsettled list.
2. **`L` and `I` are not given.** The ADR states an overall *"Ruled **low**"* only, and every other
   populated row in this table carries an L and an I that compose to the Risk. `L`/`I` = `L`/`L`
   composes to Low and matches the reasoning, but it is an inference, not the ADR's text.

**Does anything have to be REMOVED?** No, and one line deserves an explicit "leave it".
`DESIGN.md:1730`, verbatim:

> | C2-T1 | No credible threat. No adopted middleware mutates request or response payloads | - | - | - | Payload shaping happens in the tools and in `models/`, which is C3 and C6 | no credible threat |

**That sentence stays TRUE after adoption** - the new middleware rewrites schemas, not payloads -
which is exactly what the ADR's own header note says (`:9-11`: it *"is not false about it. It is
**unreached**, which is worse"*). Whether C2-T1 should nonetheless gain a qualifier so a reader
cannot mistake it for covering schemas is a judgement the ADR does not make. See the unsettled list.
The same reading applies to `:1729` C2-S1 (*"No adopted middleware establishes identity"*) and
`:1734` C2-E1 (*"No adopted middleware grants capability"*): both remain true of
`DereferenceRefsMiddleware` and need no edit.

### 5. Already applied?

**NO.** `grep -n 'Dereference\|dereference' /tmp/D.md` returns **nothing** (path proven to resolve
by the other greps against the same file); `:1167` lists three adopted; `:1725` names three.

---

## ADR-0033 - `docs/adr/0033-approval-state-is-a-published-vocabulary.md`

### 1. Status line, verbatim, and section list

```
**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change
```

- `:12` `## Context` - `:14` ADR-0021's restraint was correct and is the reason this is cheap;
  `:22` The values are not an implementation detail, and that is what decides it; `:36` All four are
  reachable, checked rather than assumed
- `:43` `## Decision` (carries a four-row table, `:49-54`)
- `:66` `## Consequences` - `:68` The set is CLOSED, and a fifth value is an ADR; `:74` A count in
  prose is not the set
- `:81` `## What this ADR does not settle`

**No Ruling / Correction / Addendum.** The Decision is operative.

### 2. What the Decision says

`:45`, whole sentence: **"The four values are correct and `DESIGN.md` §5.3 names them as a closed
set."** The four are `approved`, `refused`, `pending`, `unavailable`, and `:56-61` insists `pending`
and `unavailable` must not be collapsed (an abandoned conversation versus one that never started).

### 3. Later section

None.

### 4. THE EDIT

**Site: §5.3, `### 5.3 Audit logging and request_id` at `DESIGN.md:582`.** The paragraph that
introduces the field is `DESIGN.md:678-684`; its opening sentence, verbatim:

> **The audit event includes `approval_state`.** `agent-guardrails.md:121-123` names it explicitly,
> and `create_candidate` is gated two ways and emails a live human - without it, the only record
> that a gated write was authorised would not exist.

(ADR-0033 cites this as `DESIGN.md:678` at its `:27`. Exact.)

**After the edit** that paragraph, or a new one immediately after it, must name the vocabulary as a
**closed** set of four with the distinctions the ADR's table draws, and say a fifth value is an ADR.
The natural shape is the one §5.3 already uses for `approval_mechanism` eight lines below
(`:686-691`), so the two vocabularies read alike. Suggested text:

> **`approval_state` is drawn from a closed set of four:** `approved` - a response arrived and
> authorised the write; `refused` - a response arrived and did not, so a human said no; `pending` -
> the request went out and no answer has come, so no write has happened and **may never**;
> `unavailable` - no handler existed to ask, so nobody was asked. `pending` and `unavailable` are
> the pair most likely to be collapsed and must not be: one is an abandoned conversation, the other
> a conversation that never started, and collapsing them makes an abandoned approval
> indistinguishable from an unconfigured host in the only record either leaves. The set is closed
> for the same reason `approval_mechanism`'s is - a value emitted into an audit record is a
> contract - and a fifth value is an ADR (ADR-0033).

**Sequencing note for the applier:** this lands in the same paragraph neighbourhood as ADR-0028's
site 1 (`:687`). Apply them as one edit to §5.3 and re-read the result, rather than as two
independent `sed`s.

**Do the threat rows need touching?** `DESIGN.md:1756` (C4-R1, High) is cited by ADR-0033 at `:29`
and is exact. Its mitigation already reads *"the audit event includes `approval_state` and the
mechanism that produced it"*. **No change required** - the ADR names the values, it does not change
what mitigates the row. `DESIGN.md:1757` (C4-I1) likewise. **Nothing must be REMOVED** anywhere.

**Outside the design, and the ADR asks for it explicitly** (`:74-79`): `approval.py:181-190`'s
docstring says *"These **three** values"* while declaring four. **The applier fixes the count and
should prefer prose that carries no count** - *"the values below"* cannot go stale.

### 5. Already applied?

**NO.** `approval_state` appears at `DESIGN.md:678`, `:708`, `:1278`, `:1756`, `:1757` and the four
values are enumerated at none of them; the design names no `approval_state` value anywhere.

---

## Unreconcilable pairs

**One, and it is inside a single ADR rather than between an ADR and the design.**

**ADR-0023's Decision (`:133-137`) and its "What this ADR does not settle" (`:189-191`) directly
contradict each other about `ci.yml`.** It is *reconcilable* only because the Ruling (`:195-196`)
explicitly picks one side - *"including the `ci.yml` `run:` blocks the first draft left out"* - so I
am reporting it as **settled by the Ruling, with a stale bullet still standing in the ADR**. The
bullet must be rewritten or deleted in the same pass, because a reader who lands on `:189` first
gets the opposite instruction. **I did not edit it.**

No pair among my seven is genuinely unreconcilable.

---

## What I could NOT settle - decisions for the orchestrator

These are questions I could not answer from the documents, not items I skipped.

1. **ADR-0027 names §7.6 and the variable list is in §10.1.** I established the mismatch by
   measurement; what I cannot decide is whether the applier should (a) put the variable in §10.1's
   bullet where the tests already point, and repoint ADR-0027's `§7.6` to `§10.1` in the same
   commit, or (b) treat "§7.6" as evidence the ADR intended a *new* variable list somewhere in §7.
   **I recommend (a).** It is a decision about the ADR's text, so it is yours.

2. **ADR-0031: "add a row" versus "the 403 row names two conditions".** Two different diffs, both
   supportable from the Decision's own two consecutive sentences. **I recommend the eighth table
   row.** Named above so it cannot be defaulted into silently.

3. **ADR-0032's new C2 row has no ID and no `L`/`I` values.** `C2-T2` with `L`/`L` -> Low is my
   reading; the ADR gives only *"Ruled low"*. A row ID is a citation target for the rest of the
   corpus, so guessing it is the kind of thing that gets cited forward.

4. **ADR-0032: does `C2-T1` (`DESIGN.md:1730`) need a qualifier?** It stays literally true after
   adoption. The ADR's complaint is that it *reads* as covering the stack. Adding a clause makes it
   unambiguous; leaving it is defensible and is the smaller diff. The ADR does not say.

5. **Does §13's list of deviation ADRs grow to include ADR-0023?** §13 (`DESIGN.md:1971`) lists
   ADR-0001 to ADR-0011 under *"The eleven required at freeze"* (`:1990`), and `:1975` calls them
   *"all eleven ADRs below"*. ADR-0023 is `Type: Standards deviation` and would fit job 1 as §13
   describes it (`:1975-1978`), but it was recorded **after** the freeze and the list's framing is
   historical. **If the answer is yes, note that §13 carries "eleven" twice in prose** and both
   would go stale - the fix is to drop the count, not to bump it. I flag this for the whole batch,
   not only for 0023: none of 0012-0033 appears in §13's list today.

6. **ADR-0030 names no edit site.** I proposed one (a §4.3 bullet after `:363`) and a second
   candidate (§5.1 at `:495-497`, which I recommend leaving alone). The ADR authorises neither by
   name. A `Type: Design change` ADR whose Decision changes a caller-visible promise but points at
   no section is a gap in the ADR, and the applier will otherwise choose a site by feel.

**What I deliberately did NOT check, and why it is not on the list above:** I did not verify the
current `src/` and `tests/` state for the code halves of 0027, 0028, 0031, 0032 and 0033. My brief
scopes me to the ADRs and the frozen design, and #95 applies the design edits. The one exception is
`tests/test_repo_hygiene.py:82` and `tests/test_config.py:576-617`, which I read because ADR-0027's
Ruling makes a specific demand about them and cites a line number that is off by one.
