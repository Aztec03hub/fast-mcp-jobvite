# Citation-range audit: which binding obligations no B-number ever cited

**Task:** CONF-5 · **Author:** conf5-citation-ranges · **Date:** 2026-08-28

**Question.** Round 6 found `ai/tool-calling.md:176-177` (the LLM trace/span id) tracked by no
B-number, no sweep verdict and no ADR, because the corpus cited the lines around it and not it.
**Did the same skip happen anywhere else?**

**Answer up front.** Yes, in nine places across the two `ai/` standards, and the mechanism is worse
than a one-off: **citation ranges contract monotonically each time the corpus is copied forward**
(§3). A second pass over the priority-2 standards (§8) found **one more skip of the same shape, and
it is the more consequential of the two.** In total, **two** obligations are uncited and
undischarged; the rest are corpus gaps the design satisfies anyway, or clauses with no referent in
a tool *provider*. **This does not overturn the freeze of `DESIGN.md`**, but it adds two required
design paragraphs and two corpus entries, and it bears on whether the *conformance corpus* may be
frozen as a compliance record (§7).

The contraction test was then **mechanised and extended to the priority-2 standards** (§8.1). It
reproduced all seven `ai/` contractions as a positive control and found **three more**, two of them
consequential: **F11**, where B37's citation no longer contains the 4xx obligation B37's own title
still asserts, and **F12**, where B38 kept the composition order and dropped its enforcement. Both
are corpus defects with the design already compliant. Ten contraction events across four standards
is no longer a pattern that can be attributed to individual slips.

Two citation defects outside the brief's scope were also found and are recorded in §6, because they
falsify a self-claim in `CONFORMANCE-B1-B106.md` §2. **All corpus fixes proposed in this document
have now been applied** - §9 lists what changed in which file. `DESIGN.md` was deliberately not
touched.

> **`DESIGN.md` line numbers.** `DESIGN.md` was being edited by another task while this audit ran,
> so it is cited by **section plus quoted text**, not by line, except where a line was re-verified
> with `grep -n` at the moment of writing. Standards-file and review-file line numbers are stable
> and are given exactly.

---

## 1. Method

The brief is right that the obvious method cannot work: every citation in the corpus resolves, so a
corpus-outward checker passes. Three passes were run **standard-inward** instead.

**Pass A - clause enumeration.** `ai/tool-calling.md` (206 lines) and `ai/agent-guardrails.md`
(171 lines) were read in full with `cat -n`. Every normative unit was enumerated: a bullet, table
row or sentence carrying MUST / MUST NOT / "never" / "always" / a bare imperative in a normative
section. Front matter, Purpose, Scope, code fences, "Related Standards" and the closing epigram
were excluded. **42 units** resulted - 23 in `tool-calling.md`, 19 in `agent-guardrails.md`.

**Pass B - cited-line union.** Every reference to those two files was extracted mechanically from
`docs/research/STANDARDS.md`, `docs/reviews/CONFORMANCE-B1-B106.md`,
`docs/reviews/CONFORMANCE-RESWEEP.md` and `docs/research/COMPLIANCE-SPEC.md`, then unioned. Each of
the 42 units was asked: **does any cited range intersect it?** A unit no range touches is a
candidate.

**Pass C - disposition.** Each candidate was checked against `docs/DESIGN.md`, the eleven ADRs, and
the `A1`-`A5` adaptation entries in `STANDARDS.md` §2, to separate a corpus gap from a real hole.

**Range-contraction test** (added after Pass B). Because the same B-number appears in three corpus
generations, each B-number's range was compared *across* them. This is what turned a list of gaps
into a mechanism (§3).

**Citation discipline.** Every `file:line` here came from `grep -n` or from a `cat -n` read of the
whole file. No offset was counted inside a `sed -n X,Yp` window - that is how the original defect
got in, and one `sed` window used during this audit was indeed 11 lines stale against the live
file, which is why §1's note above exists.

---

## 2. What was enumerated, and the three-way classification

**Priority 1 - the two `ai/` standards** (`ADR-0005` binds this domain in full):

| Class | Count | Meaning |
|---|---|---|
| **Covered** - a cited range includes it | **26** | Tracked by a B-number, an `A`-adaptation, or an ADR |
| **Uncited but satisfied** - corpus gap only | **12** | No citation; `DESIGN.md` meets it anyway, or it has no referent in a tool provider |
| **Uncited and undischarged** - a real hole | **1** | No citation, no ADR, no design sentence |
| **Out of scope by the file's own words** | **3** | e.g. the `patterns/agents/agent-shape.md` pointer at `agent-guardrails.md:153-155` |
| **Total** | **42** | |

The 12 "uncited but satisfied" split further, and the split decides what the fix should be:

- **5 the design actively satisfies** (F2, F3, F4, F5, F9). These are the dangerous ones: the design
  does the right thing for reasons it wrote down independently, so **no instrument would notice if
  a future revision stopped doing it.**
- **7 with no referent on the tool-provider side** (F6, F7, F8 and the four loop-bound clauses).
  `A5` disposes of the loop clauses by name; the rest are disposed only by inference.

---

## 3. The mechanism: citation ranges contract as they are copied forward

The round-6 defect is not an isolated typo. The same B-number's cited range gets **shorter** in each
successive corpus document, and each contraction drops the tail of a clause.

| B | `STANDARDS.md` | `CONFORMANCE-B1-B106.md` | `CONFORMANCE-RESWEEP.md` | What the contraction dropped |
|---|---|---|---|---|
| **B40** | `tool-calling.md:173-177` (at `:307`) | `:173-175` (at `:193`) | `:174` (at `:159`) | **`:176-177`, the trace/span id** - the round-6 defect, verbatim |
| **B40** | `agent-guardrails.md:124-127` (at `:307`) | `:124-126` (at `:193`) | `:125` (at `:159`) | `:127`, the same trace-id clause in the second binding file |
| **B16** | `tool-calling.md:55-57` (at `:172`) | `:55-56` (at `:149`) | `:55` (at `:140`) | `:57`, *"The callable-tool set is an explicit allow-list per agent"* |
| **B17** | `tool-calling.md:171-173` (at `:178`) | `:171-172` (at `:150`) | drops to `agent-guardrails.md:121-122` | `:173`, *"and the request correlation id"* |
| **B15** | `tool-calling.md:153-155` (at `:165`) | `:153-155` (at `:148`) | `:153` (at `:139`) | `:154-155`, why the cap exists (injection surface, cost blowout) |
| **B21** | `agent-guardrails.md:50-53` (at `:211`) | `:50-53` (at `:154`) | `:50` (at `:142`) | `:51-53`, *"Scope the credential, never rely on the prompt"* - the operative half |
| **B23** | `tool-calling.md:185-187` (at `:221`) | `:185-187` (at `:156`) | `:185` + `:187` (at `:143`) | `:186`, which adversarial cases are meant |

**Read the B40 row across.** `STANDARDS.md` cited `:173-177` and *did* cover the trace-id lines. The
sweep narrowed it to `:173-175`; the resweep to `:174`. The obligation did not go invisible in the
corpus's first generation - it went invisible in its **second**, and the resweep then re-verified
the narrowed range and reported it sound, **because a narrowed range is still a correct range**.

That is the general failure: **a contraction is undetectable by any check that asks whether a
citation resolves.** It shows up only if you ask what the citation stopped covering.

`CONFORMANCE-RESWEEP.md` contracting to a single anchor line is defensible as a quote-anchor
convention. The `STANDARDS.md` -> `CONFORMANCE-B1-B106.md` step is not: it is prose to prose, and it
silently dropped the tail of four clauses (B40 twice, B16, B17).

---

## 4. Findings

Every suggested fix below is **my suggestion, to be verified** - a hypothesis about the remedy, not
an instruction.

### F1 - UNCITED AND UNDISCHARGED - "No ambient authority" is in both binding files and in no B-number

**Clause, stated twice:**

- `ai/agent-guardrails.md:54-56` - *"**No ambient authority.** A tool must not act on behalf of an
  arbitrary user. Pass the caller's identity/tenant explicitly and enforce authorization inside the
  tool"*.
- `ai/tool-calling.md:108-111` - *"Tools **re-validate authorization independently** of the model:
  enforce the authenticated caller's tenant / row-level access inside the tool, off the request
  principal, never off a value the model supplied."*

**Cited by:** nothing. `grep -rn` over `docs/` returns zero hits for either range. This is the
round-6 shape exactly: in `agent-guardrails.md` the corpus cites `:47-49` (B20), `:50-53` (B21) and
`:57-58` (B13), and **steps over `:54-56` between them.**

**Disposed by:** no ADR. ADR-0005 grants *"Obligations B9-B26 apply in full"* - which cannot reach a
clause that has no B-number. ADR-0009 reads *"This ADR is scoped to the approver and explicitly not
to the caller"*, disclaiming exactly this territory.

**Design:** §7.2 governs *which tools* a token may call (`require_scopes` over three data classes)
and the rights of the *outbound* Jobvite credential. Neither is this clause. Nothing states what
happens inside a tool body: `get_candidate(candidate_id)` resolves a record off a **model-supplied
value** with no principal check, which is the literal thing `tool-calling.md:111` forbids.

**Is it a real risk?** Probably not, and that is exactly why it needs a sentence rather than a
control. There is one Jobvite tenant credential and no per-user model, so there is no caller-scoped
record set to enforce - the clause has no referent *as a matter of fact about this deployment*. But
that fact is nowhere written down, and §7.2 states the opposite-facing fact (*"stdio is
unauthenticated by design"*, `DESIGN.md:778`) without connecting it. **A reader cannot tell a clause
was considered and found inapplicable from a clause that was never opened.**

**Suggested fix (design edit + corpus edit):**
1. **Design:** one paragraph in §7.2 stating that the server holds a single Jobvite tenant
   credential; that there is therefore no caller-scoped record set to enforce inside a tool body;
   that per-record authorization is the host's boundary; and that **if a second tenant is ever
   configured, `agent-guardrails.md:54-56` becomes a live obligation.** Model it on §4.3's handling
   of `resilience.md:74-76` having no referent (`CONFORMANCE-RESWEEP.md:307` records that as the
   accepted pattern here, and `CONFORMANCE-B1-B106.md:181` shows the same remedy prescribed:
   *"Worth one sentence stating the adaptation."*).
2. **Corpus:** add **B107** citing `ai/agent-guardrails.md:54-56` **and** `ai/tool-calling.md:108-111`
   together, so a future revision that introduces multi-tenancy trips an instrument.

I recommend **not** an ADR. An ADR records a decision to depart from a standard; this is a statement
that the clause has no referent, which belongs in the design.

### F2 - UNCITED BUT SATISFIED - "schema validation is necessary, not sufficient"

`ai/tool-calling.md:104-107` - *"Tool arguments are **model output**, hence untrusted at the sink the
tool touches (SQL, shell, paths, HTTP). Apply [output-handling] sink rules inside the tool - schema
validation is necessary, not sufficient."* **Cited by nothing.**

**Satisfied:** §2.1 requires *"regex on every identifier"* (`DESIGN.md:132`) and *"Input is rejected
on control characters and encoding before dispatch"* (`DESIGN.md:151`) - sink-side handling for the
HTTP/path sink these tools actually touch.

**Why it still matters:** this is the one clause in either file saying a schema is *not enough*, and
§2.1's whole defence is schema-shaped. The corpus tracks the sufficient part (B9, B10, B11, B25,
B29, B30) and not the clause that qualifies it.

**Suggested fix (corpus edit):** fold `:104-107` into **B11**'s cited range, or give it a B-number.
No design change needed.

### F3 - UNCITED BUT SATISFIED - the gate decides on the validated call, and the operation is rendered to the approver

`ai/agent-guardrails.md:74-76` - *"The gate decides on the **validated tool call** ... Render the
concrete operation to the approver"* - and its twin `ai/tool-calling.md:131-132`. **Neither is
cited.** The corpus cites `:70-73` (B18, at `CONFORMANCE-B1-B106.md:151`) and stops one bullet short.

**Satisfied, and load-bearing:** §7.5 - *"The approval request must state what is actually being
authorised, including the email"* (`DESIGN.md:928`) and *"The elicitation payload accordingly names
the candidate, the target job, and whether `send_email` is true"* (`DESIGN.md:936`). That is exactly
`:76`'s *"Render the concrete operation to the approver"*.

§7.5 reaches that conclusion from `:70-73`'s *"outbound message to a third party"*, not from
`:74-76`, so **the strongest paragraph in §7.5 currently rests on a clause that says something
adjacent to what it needs.**

**Suggested fix (corpus edit):** extend **B18**'s cited range to `ai/agent-guardrails.md:70-76`.
This is the highest-value one-character fix in this report: it puts a B-number under a design
paragraph that already exists and is already correct.

### F4 - UNCITED BUT SATISFIED - the approval decision is a policy/code check the model cannot grant itself

`ai/agent-guardrails.md:80-84`. **Cited by nothing.**

**Satisfied:** §7.5's conjunction *"`action == "accept" and content.get("approve") is True`"*
(`DESIGN.md:943`, mirrored in the §11 row C4-E1 at `DESIGN.md:1611`) and *"What we may honestly
claim"* (`DESIGN.md:1027`), which states the server never claims a human approved.

**Suggested fix (corpus edit):** include `:80-84` in B18's range alongside F3, or give it its own
B-number.

### F5 - UNCITED BUT SATISFIED - "Approvals are scoped and expire"

`ai/agent-guardrails.md:77-79`. **`:79` alone is cited** - by ADR-0009 (`docs/adr/0009-approver-identity-unknowable.md:7`),
`DESIGN.md:1607` and `DESIGN.md:1848`, all for the *"record who approved"* half. **`:77-78` -
*"An approval authorizes one specific call (or a narrow, declared batch), not a standing
capability"* - is cited nowhere.** Half a bullet tracked, half not: the same shape again.

**Satisfied by mechanism:** MRTR binds the approval to the retry of that exact call (§7.5), so it
cannot become a standing capability, and §7.6 cut the confirmation token - the one mechanism that
could have created one.

**Suggested fix (corpus edit):** widen ADR-0009's context citation to `:77-79` and add one sentence
saying the *scoped-and-expires* half is **satisfied by MRTR, not scoped out**. As written, ADR-0009
reads as though `:79` were the whole bullet, which invites a later reader to treat the whole bullet
as disposed.

### F6-F8 - UNCITED, NO REFERENT - host-side clauses disposed only by inference

| # | Clause | Why no referent |
|---|---|---|
| **F6** | `tool-calling.md:101-103` - *"A bounded re-ask is fine; an unbounded repair loop is not"*. B12 cites `:100` and stops at the line boundary | The re-ask loop is the host's. This server returns one typed error and does not loop |
| **F7** | `tool-calling.md:146-152` - re-enter the prompt-injection and output-handling controls before feeding a tool result back | Tracked *in substance* by B24 via `prompt-injection.md:49-50` and implemented by §6.1 fencing. The `tool-calling.md` statement of it is uncited |
| **F8** | `tool-calling.md:74-82`, `:156-157`, `:163-170`; `agent-guardrails.md:101-105`, `:139-151` - runtime mapping, loop-breach handling, *"never let a tool result auto-trigger a privileged action"* | `A5` scopes out the agent loop by naming `agent-guardrails.md:93-99`. These neighbouring loop clauses fall to the same reasoning but not to the same citation |

**Suggested fix (corpus edit) for all three:** `A5` currently cites `agent-guardrails.md:93-99`.
Widen it to name `agent-guardrails.md:101-105` and `:139-151`, and `tool-calling.md:74-82`,
`:101-103`, `:156-157`, `:163-170`, as the full clause set the tool-provider adaptation disposes of.
One edit, seven clauses, no design change.

### F9 - UNCITED BUT SATISFIED - "tool logs are an audit trail: append-only intent"

`ai/agent-guardrails.md:130-131`. **Cited by no B-number.**

It *was* raised by a reviewer: `DESIGN-R2.md:325` quotes it and says *"the design has to state it.
The ADR list has no entry either way."* The design then answered it - §5.3's *"Audit-write failure
has a stated policy, and the third case is the one that matters"* (`DESIGN.md:656`) is precisely the
position R2 asked for.

**This is the clearest single piece of evidence for §3's mechanism.** A finding was made, the design
was fixed, and **no B-number was created** - so the discharge is invisible to every instrument this
project has. If §5.3 regressed tomorrow, nothing would flag it.

**Suggested fix (corpus edit):** add a B-number citing `ai/agent-guardrails.md:130-131`, verdict
SATISFIED, evidence `DESIGN.md` §5.3.

---

## 5. Two obligations hand-checked end to end

A clean zero that explains itself is the failure that produced this task, so here is the full
working for two - one from each outcome class.

### Hand-check 1: `agent-guardrails.md:54-56` (F1) - the hole

1. **Clause located.** `grep -n "No ambient authority" ai/agent-guardrails.md` -> `54:`. Read
   `:54-56` inside a `cat -n` of the whole file; the bullet ends at `:56` with the pointer to
   `../architecture/security.md`.
2. **Neighbours confirmed cited.** `:47-49` -> B20 (`STANDARDS.md:203`); `:50-53` -> B21
   (`STANDARDS.md:211`); `:57-58` -> B13 (`STANDARDS.md:157`). The bullets either side are tracked
   and the one between them is not.
3. **Absence established, not assumed.** `grep -rn 'agent-guardrails.md:5[4-6]' docs/` -> zero hits.
   `grep -rn 'tool-calling.md:10[4-9]|tool-calling.md:11[01]' docs/` -> zero hits. **Positive
   control:** the identical grep for `agent-guardrails.md:79` returns five hits across four files
   (`DESIGN.md:1607`, `DESIGN.md:1848`, `adr/0009-...:7`, `THREAT-MODEL-DRAFT.md:266`,
   `CITATION-AUDIT.md:213`), so the pattern shape and the corpus path are both live and the zero is
   a real absence rather than a broken instrument.
4. **ADRs checked by reading, not by title.** ADR-0005: grants B9-B26 in full - inapplicable, no
   B-number exists to grant. ADR-0009: *"scoped to the approver and explicitly not to the caller."*
5. **Design checked.** `grep -n -i "ambient|principal|tenant|authoriz|row-level"` over `DESIGN.md`
   returns `:534` (*"no ambient request id"* - a different sense of the word), `:1026` (a cache-key
   example) and `:1437` (a threat-model preamble). §7.2 was then read in full: it governs inbound
   scopes and the outbound credential, not in-tool authorization.
6. **Verdict:** uncited, undisposed, and factually inapplicable for a reason the design never
   states. **Class 3.**

### Hand-check 2: `agent-guardrails.md:74-76` (F3) - the corpus-only gap

1. **Clause located.** `grep -n "The gate decides on the"` -> `agent-guardrails.md:74` **and**
   `tool-calling.md:131`. The same obligation in both binding files, as with F1.
2. **Absence established.** `grep -rn 'agent-guardrails.md:7[4-6]' docs/` -> zero hits. The nearest
   citation is B18's `:70-73` (`STANDARDS.md:189`, `CONFORMANCE-B1-B106.md:151`), which stops at the
   bullet before.
3. **Design read.** §7.5, `DESIGN.md:928` and `:916` (quoted in F3 above) meet `:76` in full.
4. **Provenance of the design sentence checked** - this is the step that decides the class. §7.5
   justifies itself from `:70-73` (*"The standard settles this rather than leaving it to our
   judgement"*), i.e. from the **cited** bullet, and arrives at the right answer by a different
   route. So the design is right and the corpus is thin, not the reverse.
5. **Verdict:** uncited but satisfied. **Class 2.** Corpus edit only.

---

### Hand-check 3: `resilience.md:166-168` (F11) - a contraction, end to end

1. **Both generations opened.** `STANDARDS.md` B37 (`grep -n 'B37\.'`) cites *two* ranges,
   `:159-161` and `:167-169`, and quotes the second: *"a caller error (4xx) is not an outage and
   MUST NOT"* trip the breaker. `CONFORMANCE-B1-B106.md:185` cites `:159-161` only and quotes only
   the one-breaker sentence.
2. **The dropped lines read at source.** `cat -n backend/resilience.md`, lines 166-168:
   *"Count **only outage-class errors** toward the breaker via `expected_exception` — a caller error
   (4xx) is not an outage and MUST NOT trip it."* The obligation is real and imperative.
3. **The range itself checked, not inherited.** `STANDARDS.md`'s `:167-169` is wrong at both ends:
   `:166` opens the bullet, `:168` closes it, and `:169` opens the next one (*"When the breaker is
   open, the call raises `CircuitBreakerError`"*). Corrected to `:166-168` rather than propagated.
4. **Consequence isolated.** The sweep row's **title** still asserts *"4xx does not trip it"* and its
   **verdict** still credits §4.3 for it. So the contraction did not make the obligation invisible -
   it made the row **unsupported by its own citation**, which a resolve-the-citation check cannot
   detect because `:159-161` resolves perfectly.
5. **Design checked before classifying.** §4.3: *"One circuit breaker for Jobvite. **4xx must not
   trip it** - a bad candidate id is the caller's problem, not a health signal."* Satisfied.
6. **Verdict:** corpus defect, not a design defect. Citation restored and range corrected.

### Hand-check 4: `threat-modeling.md:35` (B110) - the obligation behind the vacuous zero

1. **Clause located.** `grep -n "STRIDE per-component" architecture/threat-modeling.md` -> `:35`:
   *"Use **STRIDE per-component** as the default approach. For each component in the feature's data
   flow, evaluate all six STRIDE categories."*
2. **Absence established.** The corpus's entire citation set for this 174-line file is `{:86}`.
   `:35` is uncited. **Positive control:** the same extraction over `ai/tool-calling.md` returns 13
   distinct ranges, so the extractor is not simply failing on this file.
3. **The obligation made falsifiable before checking it.** "All six categories per component" is
   testable by extraction, not by reading: pull every row ID from §11's STRIDE tables and check the
   cross-product. That is the step that separates this from an impression of thoroughness.
4. **Checked.** Row IDs extracted from `DESIGN.md` §11: **C1 through C8, each carrying S, T, R, I,
   D and E** - a complete 8x6 grid - plus four second findings (C4-D2, C4-E2, C6-I2, C7-I2).
   Satisfied, and satisfied more completely than the standard demands.
5. **Why it still matters.** Nothing in the corpus would notice if that grid lost a category. The
   most structurally complete claim in `DESIGN.md` was guaranteed by no instrument.
6. **Verdict:** uncited but satisfied. B110 added; no design change.

---

## 6. Citation defects found in passing (outside the brief's scope)

Both falsify a self-claim. `CONFORMANCE-B1-B106.md:78` states *"All 106 B-numbers resolved to an
existing file and an existing line"*, and its method paragraph claims the first pass *"confirmed no
B-number cites a missing file or a line past EOF."*

| # | Where | Defect |
|---|---|---|
| **CD-4** | **B43**, `STANDARDS.md:324` | Cites the request-middleware required-fields table at **`:471-477`**. `backend/request-middleware.md` is **154 lines**. The table is at **`:80-86`** |
| **CD-5** | **A3**, `STANDARDS.md:589` | Cites LIFO middleware ordering at **`:481-489`**. Same 154-line file. The passage is at **`:90-98`** |

**Root cause, verified arithmetically rather than guessed.** `471-477` minus **391** is `80-86`.
`481-489` minus **391** is `90-98`. Both land exactly. These two citations were therefore taken from
a **compiled bundle** in which `request-middleware.md` begins at line 391 - `backend/` files carry a
`compile_group` in their front matter - not from the standalone file. CD-3 in
`CONFORMANCE-B1-B106.md` §2 (`error-contract.md:290`, real line `:83`) is the same species with a
different offset.

**Why the sweep missed them.** Both are **bare continuation citations** - a `` `:471-477` `` whose
filename is carried over from an earlier reference in the same sentence. A matcher keyed on
`file.md:N` cannot see them. **That is the same instrument blind spot that let the round-6 skip
through: the checker's shape decided what could be found.**

**Suggested fix (corpus edit):**
1. Correct `STANDARDS.md:324` to `:80-86` and `STANDARDS.md:589` to `:90-98`.
2. Re-run the resolution pass with a bare-continuation-aware matcher. The one written for this audit
   carries the last-seen filename forward and resolves `` `:N` `` / `` `:N-M` `` against it; over
   `STANDARDS.md` it raises 39 candidates, of which these two plus CD-3 survive inspection - the
   remainder are my matcher carrying a filename across a paragraph break, a known and acceptable
   false-positive rate for a screen.
3. Amend the `CONFORMANCE-B1-B106.md` §2 self-claim **in place - rewrite the prose, do not append a
   correction** - since *"no B-number cites a line past EOF"* is now false.

**All three applied. A re-run after the fixes found no further past-EOF defects, and here is what
that zero cost to establish.** The continuation-aware matcher was re-run over `STANDARDS.md`, both
conformance documents, ADR-0009 and this audit: **724 resolvable citations checked**, 27 flagged.
Of the 27, six are the CD-3/CD-4/CD-5 rows *quoting the wrong numbers on purpose* (expected), and
the remaining 21 were opened one at a time and resolve as **my matcher carrying a filename across a
markdown table-column boundary** - `RESWEEP:173`'s `:1274` and `:1342` follow
`architecture/observability.md:72` in the clause column but belong to `DESIGN.md` references in the
evidence column, and `RESWEEP:157`'s `:917`-`:934` are the same shape. **One is unresolved and I am
not asserting it either way:** `CONFORMANCE-B1-B106.md:331` (B106) contains `` `:723-726` `` twice,
once carrying `devops/ci-cd.md` (792 lines, valid) and once after
`devops/infrastructure-as-code.md:160` (314 lines, would be past EOF). It is probably a re-cite of
the ci-cd.md range; it is outside this brief and I did not read the surrounding clause to settle it.
Recorded so the next pass has the thread rather than a clean bill.

---

## 7. Does this change the freeze decision?

**Not for `DESIGN.md`.** There are **two** class-3 findings, F1 and F10. Neither is a missing
control: F1 is a missing paragraph about a clause with no referent, and F10 is an unevaluated
remedy for a risk the design has already identified, rated and accepted. Close both before freeze
because both are cheap - two design paragraphs and two corpus entries - not because the design is
wrong. **Nothing found in this audit contradicts a design decision.**

**F10 deserves more weight than F1**, and I would not let the pairing flatten them. F1's obligation
has no referent here; F10's has one, it names a specific remedy, the design's own residual-risk
table describes exactly the harm the remedy exists to prevent, and the standard that carries the
remedy was dismissed on a rationale that does not hold (§8).

**The thing to weigh is §3, not F1.** The evidence is that the corpus loses clause tail on every
copy-forward; that it has done so at least seven times in the two `ai/` files alone; and that the
resweep's re-verification pass **cannot** detect it, because a contracted range is still a valid
range. Freezing the design is defensible. **Freezing the conformance corpus as a durable compliance
record is not, until the ranges are widened back to clause boundaries.** Those are separable
decisions and I would not let one carry the other.

**What F11 and F12 change:** nothing in the freeze calculus, and that is worth stating plainly
rather than letting two new F-numbers imply escalation. Both are corpus defects with the design
already compliant - §4.3 states the 4xx rule and the composition order explicitly. They matter
because **F11 is the first case where a contracted citation left a row asserting an obligation its
own citation no longer contained**, which is the mechanism's most dangerous form: the row still
reads as evidence.

**Scope, stated so this document's silence is not read as coverage.** All four priority-2 standards
have now been passed over (§8), at lower resolution than `ai/`: the uncited-line test was run in
full on each, but the cross-generation contraction test of §3 was run only over the `ai/`
citations, and only the two `ai/` files were enumerated clause by clause to a unit count. Standards
outside priorities 1 and 2 were not examined at all.

---

## 8. Priority-2 pass: `resilience.md`, `error-contract.md`, `threat-modeling.md`, `request-middleware.md`

Same uncited-line test, lower resolution: cited-line union per file, then every imperative clause
(`grep -n` for MUST / MUST NOT / SHALL / never / always / a numbered normative rule) checked for
intersection with it.

| Standard | Lines | Cited-line union | Uncited imperatives | Holes |
|---|---|---|---|---|
| `backend/resilience.md` | 285 | `71-76 92-101 130 143-145 159-161 167-169 209 216 226` | **`:146-151`** | **1 (F10)** |
| `architecture/error-contract.md` | 226 | `38 44 66 83 96-108 200 204 206 210-211` | rules 2, 4, 5, 6, 9 at `:205`, `:207-209`, `:212` | 0 |
| `architecture/threat-modeling.md` | 174 | **`86` only** | 7 of 8 obligations | 0 |
| `backend/request-middleware.md` | 154 | `38 60 142-145` (+ two bad, §6) | none | 0 |

### F10 - UNCITED AND UNDISCHARGED - the idempotency-key remedy for a duplicate write

**Clause:** `backend/resilience.md:146-151` -

> *"Make a write retry-safe by guarding it with an **idempotency key** so the downstream dedupes
> the replay; see [`./idempotency.md`]. Only then may the write be retried."*
> *"Never auto-retry across an already-committed side effect; resume from a durable checkpoint or
> hand off to a background job instead."*

**Cited by:** nothing. `grep -rn 'resilience.md:14[6-9]|resilience.md:15[0-8]' docs/` -> zero hits.
**Same shape as F1 and as round 6:** the corpus cites `:143-145` (B36) and `:159-161` (B37), and
steps over the six lines between them.

**Why this one has teeth.** The two clauses either side of the gap are about the *server's own*
auto-retry, and both are discharged that way: B36 is SATISFIED because §4.3 excludes
`create_candidate` from retry by construction (`CONFORMANCE-B1-B106.md:184`), and B19 likewise
(`:152`). The skipped clause is about the **other** replay path - a caller re-issuing the write -
and names its remedy: an idempotency key.

That other path is not hypothetical here. `DESIGN.md:1610` (row C4-D2) reads: *"An authorised write
is made twice - **a model retrying after a timeout, or a human approving twice** - creating a
duplicate candidate and a second email to a live person ... **Detection, not prevention**"*, rated
Medium and carried to Residual Risks at `DESIGN.md:1758`. **That is precisely the harm
`resilience.md:146-148` exists to prevent, and the design accepted it as residual without any
instrument ever pointing at the clause that names the remedy.**

**The dismissal that should have caught it is circular.** `backend/idempotency.md` was dismissed at
`STANDARDS.md:673` with: *"The `Idempotency-Key` HTTP recipe is for inbound mutating endpoints.
B19's tool-level idempotency covers the residue."* But B19 cites `tool-calling.md:133-134` and is
discharged purely by "never auto-retried" - **it does not cover the caller-replay residue at all.**
The standard is dismissed because a B-number covers the residue; the B-number is satisfied by
something that is not the residue; and the clause bridging them is uncited. Each step reads sound
in isolation.

**The design already suspects this.** `DESIGN.md:1868`, in the freeze procedure: *"`devops/docker.md`
and `backend/idempotency.md` are the two most likely to have gone live."* `DESIGN-R5.md:497` asked
round 6 to re-check exactly those two. So the suspicion was recorded and the instrument that would
have settled it does not exist.

**What I did not settle.** Whether Jobvite accepts an idempotency key at all. `grep -rn -i idempot`
over `docs/research/JOBVITE-API.md` and `JOBVITE-CONTRACT.md` returns **zero hits**, so the
remedy may simply be unavailable - in which case the correct outcome is a stated ceiling, not a
control. **I am not claiming the decision is wrong. I am claiming nothing would have made anyone
check.**

**Suggested fix (design edit + corpus edit), to be verified:**
1. **Corpus:** add **B108** citing `backend/resilience.md:146-151`, and reopen the
   `backend/idempotency.md` dismissal at `STANDARDS.md:673` - its stated rationale does not survive
   reading B19's verdict.
2. **Design:** in §4.3 or beside C4-D2, one paragraph evaluating the idempotency-key remedy against
   the caller-replay path: whether Jobvite supports a dedupe key, and if not, that the residual risk
   stands **with that ceiling named**. §7.2's treatment of the unverifiable read-only Jobvite key is
   the model - a requirement stated as unsatisfiable is worth more than one quietly unticked.
3. **Not an ADR** unless the answer is that a supported remedy is being declined.

### 8.1 The contraction test extended to the priority-2 files

The §3 test was mechanised for this pass: parse every B-number's citations out of all three corpus
generations, normalise each to a line set per standard file, and report any line a generation
**stopped** citing. **Positive control:** the script independently reproduced all seven `ai/`
contractions found by hand in §3, including the B40 chain, before I read its priority-2 output.
16 contraction events total; after discarding artifacts of disjoint-span display (B1's `:200` is a
horizontal rule, B35's `:130` a table row restating `:99-101`), **three are real and two of those
are consequential.**

| B | Standard | `STANDARDS.md` | `CONFORMANCE-B1-B106.md` | Dropped | Verdict |
|---|---|---|---|---|---|
| **B37** | `resilience.md` | `:159-161` **and** `:166-168` | `:159-161` only | the 4xx clause | **F11** |
| **B38** | `resilience.md` | `:209` **and** `:214-217` | `:209` only | retry-inside-breaker | **F12** |
| **B41** | `request-middleware.md` | `:38`, `:60`, `:143` | `:38`, `:60` | Rule 2 restatement | minor |

### F11 - CONTRACTED - B37's citation no longer contains the obligation B37's own title asserts

`STANDARDS.md` cites **two** ranges for B37 and quotes the second: *"a caller error (4xx) is not an
outage and MUST NOT"* trip the breaker. `CONFORMANCE-B1-B106.md:185` kept only `:159-161` - the
one-breaker-per-dependency sentence - and dropped the 4xx clause entirely.

**This is a sharper failure than B40's.** The sweep row's own title still reads *"One breaker per
dependency; **4xx does not trip it**"*, and its verdict column still credits §4.3's *"4xx must not
trip it"*. So the row **asserts an obligation its citation does not contain**, and a reader checking
the citation would find the title unsupported. B40 lost a clause quietly; B37 lost one while
continuing to claim it.

**Not a design defect:** §4.3 states *"One circuit breaker for Jobvite. **4xx must not trip it**"*
explicitly. Corpus only.

**Fix (applied):** B37's citation restored to `:159-161` **and** `:166-168`, with the clause quoted
whole. **Note the range correction:** `STANDARDS.md` cited `:167-169`, which is off by one at both
ends - the bullet starts at `:166` (*"Count **only outage-class errors** toward the breaker via"*)
and ends at `:168`. `:169` belongs to the next bullet. Corrected in both documents.

### F12 - CONTRACTED - B38 kept the composition order and dropped its enforcement

`STANDARDS.md` cites `:209` (the order) **and** `:214-217`, quoting *"Never let a retry loop sit
outside the breaker"*. The sweep kept `:209` alone.

**Classification: uncited but satisfied, narrowly.** §4.3's opening line - *"Ordered timeout, then
retry, then circuit breaker"* - restates `:209`, and `:209` is itself a nesting statement
(innermost -> outermost), so the retry loop being inside the breaker follows. But it follows by
implication, and **the dropped clause is the one that names the failure mode**: *"that lets retry
storms defeat the breaker and keep hammering a down upstream."* §4.3's bullets say *"Retries live
inside this module"* and *"One circuit breaker for Jobvite"* without ever saying retries live inside
the **breaker**, which is the thing implementations get wrong.

**Suggested fix beyond the citation (to be verified):** §8's resilience cases should assert the
composition directly - that a tripped breaker short-circuits **before** any retry budget is spent -
rather than only that the three primitives exist. That is a test-list suggestion, not a design
change, and it is for whoever owns §8. **Citation fix applied:** B38 now cites `:209` and
`:214-217`, quoted whole. `STANDARDS.md`'s `:216` anchor was mid-sentence and is now `:214-217`.

### The other three files: no holes, two observations worth recording

**`architecture/threat-modeling.md` returns zero contractions, and that zero is worthless.** It was
named the highest-stakes file of the three, so the shape of its zero matters more than the zero. A
contraction test compares a citation across generations; **`threat-modeling.md` has exactly one
citation in the entire corpus, so there is nothing to compare and the test cannot fail.** Reporting
"no contractions in threat-modeling.md" would be true, reassuring, and empty - the same species of
clean zero that produced this task.

**The test that is informative here is the uncited-obligation test, and it is damning in a different
direction:** 7 of 8 obligations were never cited at all, so they could not contract because they
never entered the corpus. A dropped clause tail is impossible in a file nobody quotes. The risk in
`threat-modeling.md` was never contraction; it was **non-enumeration**, and that is what B110 now
closes.

**`architecture/threat-modeling.md` is a 174-line binding standard tracked by exactly one cited
line** (`:86`, the Critical/High threshold). Seven of its eight obligations are uncited - and all
seven are satisfied, several impressively. In particular `:35` (*"Use **STRIDE per-component** ...
For each component in the feature's data flow, evaluate **all six** STRIDE categories"*) is met by a
complete grid: §11 carries C1 through C8, each with an S, T, R, I, D and E row (verified by
extracting the row IDs - 8 components x 6 categories, plus four second findings C4-D2, C4-E2,
C6-I2, C7-I2). **The most complete structural claim in `DESIGN.md` is guaranteed by no B-number.**
If §11 lost a category tomorrow, nothing would notice. *Suggested fix (corpus edit):* one B-number
citing `threat-modeling.md:35` and `:50-56`, verdict SATISFIED, evidence §11's grid.

**`architecture/error-contract.md`: the design cites a clause the corpus does not.** The ten
numbered rules at `:204-213` are cited at rules 1, 3, 7 and 8 only; rules 2, 4, 5, 6 and 9 are
uncited by any B-number, and all are covered in substance by B2 via `:66`'s seven elevated fields
and by ADR-0003 for the `Content-Type` rule. Rule 9 (`:212`, `about:blank` for unknowns) is
uncited by the corpus but **used directly by `DESIGN.md:475`** (*"Anything unmapped | `about:blank`
per `:212`"*). That is the inverse of the F9 pattern and equally invisible: the design is ahead of
its own instrument. No hole; *suggested fix (corpus edit):* fold `:205-209` and `:212` into B2's
range so the rule list is tracked as the unit it is.

---

## 9. What was changed, and where

Applied to the corpus; **`docs/DESIGN.md` was not touched** (a confirmation reviewer holds it), and
nothing was committed.

| File | Change |
|---|---|
| `docs/research/STANDARDS.md` | CD-4 `:471-477`->`:80-86`; CD-5 `:481-489`->`:90-98`; B37 `:167-169`->`:166-168`; B38 `:216`->`:214-217`; B2 folds `error-contract.md:205-209` and `:212`; B11 folds `tool-calling.md:104-107` (F2); B18 folds `agent-guardrails.md:70-76` and `:80-84` (F3, F4); A5 widened to name the full host-side clause set (F6-F8); **new B107** (F1), **B108** (F10), **B109** (F9), **B110** (threat-modeling); `backend/idempotency.md` dismissal reopened |
| `docs/reviews/CONFORMANCE-B1-B106.md` | B16 `:55-56`->`:55-57`; B17 `:171-172`->`:171-173`; B40 `:173-175`->`:173-177` and `:124-126`->`:124-127`; B37 restored `:166-168`; B38 restored `:214-217`; B41 restored `:143`; **§2 self-claim rewritten in place**, CD-4/CD-5 added with the +391 bundle cause |
| `docs/reviews/CONFORMANCE-RESWEEP.md` | B15, B16, B17, B21, B23, B40 anchors widened to clause boundaries; the single-anchor convention retired in the method note with the reason |
| `docs/adr/0009-approver-identity-unknowable.md` | Context citation `:79`->`:77-79`; the scoped-and-expires half recorded as SATISFIED by MRTR rather than scoped out (F5) |

**Two things I applied beyond the instruction, flagged so they can be reverted cheaply.** **B108**
belongs to the F10 board item and may be owned elsewhere - I added it because I was editing the same
file and leaving a known gap open would have been worse. **B110** was a suggestion in §8, not on the
apply list; I added it because the same edit pass was open and `threat-modeling.md` had been named
highest-stakes. Both are additive; neither changes an existing verdict.

**One residual I did not silently absorb.** `agent-guardrails.md:124-127` was *restored* to
`STANDARDS.md`'s original range, but the clause actually runs to `:129` (*"Log/trace payloads are
wire-shaped **snake_case**"*). That tail is covered in substance by B17 via `tool-calling.md:178-179`,
so I left the restored range rather than quietly widening past what the corpus had ever claimed. By
the rule this audit just wrote into the resweep, it should be `:124-129`; I am flagging it rather
than deciding it.

---
