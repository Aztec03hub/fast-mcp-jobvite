# DESIGN.md revision 3 (post-R3 fixes) - adversarial review round 4

**Task:** DR4 - **Author:** design-review-r4 - **Date:** 2026-08-27
**Subject under test:** `docs/DESIGN.md`, 1234 lines, as it stands after the fourteen post-R3 changes.
**Roles:** RED and BLUE both played by this agent.
**Result: 0c / 6h / 11m surviving. I would NOT freeze.**

**Correction, post-delivery, by the author.** H5 originally cited the credential-requiring-Quickstart
anti-pattern as `readme-standard.md:88`. **The clause is at `:83`;** `:88` is a line in the Citations
list. The lead caught it and checked the file rather than propagating it. Every occurrence is fixed
above and the substance of H5 is unchanged: the clause exists, it forbids the remedy §10.1 proposed,
and `:67` is meetable. **Recorded rather than silently corrected, because it is the same class H5
reports.** The cause is worth naming: this is the only citation in the round I took from a `sed`
window by counting offsets by eye instead of from `grep -n`, which is how every other `file:line`
here was obtained. An instrument that prints a block without line numbers invites exactly this, and
a reviewer auditing miscitations is the last person who should be reading one off an unnumbered
window.

---

## What I read

**In full:** `docs/DESIGN.md` (all 1234 lines); `docs/reviews/DESIGN-R3.md` (all 584);
`standards/architecture/threat-modeling.md` (Methodology, Risk Rating, Matrix, Thresholds, When to
Perform); `standards/documentation/readme-standard.md` (Required sections `:45-58`, Required
behaviors `:64-72`, Anti-patterns `:76-88`).

**Prior rounds' maps first, per the brief:** the "What I did NOT review" section of R1, R2 and R3,
plus R3's full finding set and its disposition table. R3's map is where four of this round's six
HIGHs came from.

**Targeted, opened at every `file:line` I cite:** `docs/reviews/CONFORMANCE-B1-B106.md` rows B12
(`:145`), B22 (`:155`), B23 (`:156`), B67 (`:235`), B72 (`:240`), and its summary counts (`:20-40`);
`docs/research/JOBVITE-API.md` §6.1 (`:395-405`), the pagination and `total` statements (`:397-398`,
`:426-428`, `:483`, `:614`, `:637`, `:750`, `:754`), the residual-unknowns entry (`:821`), and the
handling policy §0.2 (`:51-57`).

**Not read in full, and it matters:** `FASTMCP-SPIKE-4.md` (~2350 lines),
`CONFORMANCE-DESIGN-ARTIFACT.md`, `STANDARDS.md`, `COMPLIANCE-SPEC.md`, `DECISIONS.md`,
`JOBVITE-CONTRACT.md`. See the closing section.

---

## The factual-assertions-about-the-world check, run first

Round 3's headline positive was that this class did not recur. **It has recurred, once, in new
text.** Recording both halves precisely.

**Landed correctly (checked at the file, not assumed):**

- `threat-modeling.md` frontmatter: `applicable_to: all` (`:6`), `priority: required` (`:8`).
  §11:953-955 states both. Correct.
- `:35` is the STRIDE-per-component sentence; `:62-74` are the Likelihood and Impact ladders;
  `:78-82` is the matrix; `:86-88` are the thresholds; `:120-127` are the six Required triggers;
  `:143` is "authored during specification". **Every one lands.** Four of six triggers do fire.
- **The matrix arithmetic on all eleven new or rerated rows.** Hand-checked against `:78-82`:
  C9-S (L/H)=Medium, C9-T (H/M)=High, C9-R (M/M)=Medium, C9-I (L/H)=Medium, C9-D (H/L)=Medium,
  C9-E (L/H)=Medium, C4-D duplicate write (M/M)=Medium, C4-I (M/M)=Medium, C7-I log retention
  (M/M)=Medium, C8-E (L/H)=Medium, C1-R (H/M)=High. **All eleven agree.** Phil's stated doubt #2
  (that the C9 ratings would not survive the matrix) is **not borne out** as an arithmetic matter.
  The judgement inputs are contestable on two rows and that is m9, not a matrix violation.
- `readme-standard.md` does mandate **fourteen** numbered sections (`:45-58`) in a fixed order.
  §10.1:890 is correct.
- "the conformance sweep found eleven consecutive documentation obligations unaddressed"
  (§10.1:891). `CONFORMANCE-B1-B106.md` summary: *"the entire documentation cluster B77-B87 is
  unaddressed except B83's absence being total - eleven consecutive obligations with no design
  coverage at all."* Correct.
- **B12 is genuinely closed by the new §8 case.** `CONFORMANCE-B1-B106.md:145` rated it PARTIAL for
  two reasons: not in §8's required-cases list, and no stated error shape. §8:771 now lists it and
  §5.1:337-342 now states the shape. Both gaps closed. This one worked.

**Did not land: H5 below.** §10.1 miscites the clause it is excusing the project from, and the
clause it does not cite forbids the remedy it proposes.

---

# RED ROUND - Adversarial review

## HIGH

### H1. §4.5's completeness check fires on every capped call, which is the default path. Third attempt, wrong in a new direction. [DEALBREAKER if shipped as written]

§4.5:296-299, verbatim:

> "**Completeness is checked against `total`, not by looking for gaps.** An earlier revision said a
> gap would be "detected and logged", which had no mechanism ... Comparing the unique-id count to
> the `total` the API reports is a real check; a mismatch is logged and surfaced."

Now §7.7:735-737, verbatim:

> "**Result size is bounded inside each tool**, not by middleware: a page is capped and the result
> says `showing 50 of 1,240`."

And §4.5:266-268 wires the two together: *"The *result* limit returned to a model is separate and
configurable (§7.7); the two are related by `min(transport_cap, configured_result_cap)`."*

**In the design's own worked example the unique-id count is 50 and `total` is 1,240.** That is a
mismatch. §4.5 says a mismatch "is logged and surfaced". So the canonical, correct, everyday
response - the one §7.7 prints as the good outcome and which §11 C3-I and C6-D both cite as a
mitigation - trips the completeness alarm every time.

The check is only meaningful for an **exhaustive** scan. §4.5 never says so. It says *"Every scan
starts at `start=0`"* and then applies the check to that same object. There is no word in §4.5,
§7.7 or §9 distinguishing an exhaustive scan from a capped one for this purpose.

Two consequences, and the second is worse than a noisy log:

1. An alarm that fires on every normal call is an alarm nobody reads. Within a week the real event
   this mechanism exists to catch - a silently short scan - is indistinguishable from background.
2. "Surfaced" is undefined. If it surfaces to the model, every capped result carries a
   completeness warning, and a model told its result may be incomplete will page again. §4.5
   replaced a mechanism that could not detect over-reading with one that manufactures the appearance
   of under-reading.

This is the mechanism that replaced R2's inverted probe and then R3's ungap-able gap detection. **It
is not a false claim about the world this time; it is a mechanism whose trigger condition is
satisfied by the design's own default.** Phil's stated doubt #1 was correct.

**What it needs:** one sentence scoping the check to a scan that ran to a short page without hitting
the configured result cap, and a statement of where "surfaced" goes. A paragraph fix, not a redesign.

### H2. §11's coupling claim is still false. It fails on C2-R and on C9-T, and it needs an escape clause that appears 184 lines later.

§11:979-980, verbatim:

> "**Every mitigated Critical or High row below has a required test in §8. That coupling is the
> point: if a mitigation loses its test, this threat model becomes false.**"

§11:982-986 then says the claim did not hold on first writing, names the three rows, and states the
tests were added. Phil's stated doubt #3 is that he never re-walked the rows. **I walked all of
them.** Two mitigated High rows have no §8 test, and one of them is brand new.

**C2-R** (`:1043`), rated **High**, mitigation *"`audit.py` emits redacted arguments itself rather
than assuming middleware provides them (§5.3). Mitigated"*.

§8's required cases (`:766-784`) contain no case asserting that the audit event **is emitted** or
that it **contains redacted arguments**. The nearest is `:768` *"candidate PII never reaching a log
or audit record"*, which asserts the opposite property: that something is **absent**. A test proving
PII never appears passes trivially against a server that emits no audit event at all. **C2-R's
mitigation is exactly "the audit event exists and carries arguments", and nothing in §8 tests that.**

This is not a new observation. R3's R-2 named C2-R as one of the three rows failing the coupling
claim, and the disposition was *"Accepted. Add three cases to §8"*. Three cases were added: PII in
logs, EEO exclusion, argument-schema rejection. **Those close C7-I and C6-I. Neither closes C2-R.**
The fix landed on two of the three rows the finding named, and §11:982-986 was then rewritten to
declare all three closed.

**C9-T** (`:1123`), rated **High**, mitigation *"`mcp` pinned explicitly ... `uv.lock` committed;
`fastmcp inspect` output diffed between builds"*, and the row itself concedes *"**The diff is
designed and unexecuted**"*. §8 contains no supply-chain case at all: no frozen-resolve test, no
`fastmcp inspect` diff test, no pin-drift test. **A brand-new mitigated High with no test, added in
the same edit that reasserted the coupling claim.**

**C1-S, C1-T, C1-I** (`:1024`, `:1026`, `:1028`), all High, all *"Mitigated"* by the TLS startup
refusal. §8 has no startup-refusal case either. §11:1163-1165 does grant an escape:
*"Each of these has a required test in §8, **or in C1's case a startup check**."* **§11:979 grants
no such escape.** Two statements of the same claim, 184 lines apart, with different scopes. The
stronger one is the one presented as the section's load-bearing invariant.

§11:984-986 says *"**A claim about coverage is worth exactly the check that was run against it**,
which is the fourth time in four review rounds this document has asserted its own compliance and
been wrong."* **This is the fifth.**

### H3. §11's C1-R and C4-R rows are contradicted by §5.3, and both are still listed as must-mitigate freeze blockers.

§11:1032, verbatim:

> "| C1 | R | A write cannot be attributed to a caller ... but **no caller or client identity is
> recorded** ... | H | M | **High** | **Unmitigated.** Record the resolved client id in the audit
> event alongside `request_id` |"

§5.3:386, verbatim, added this round:

> "*which client invoked the tool* is knowable **on the HTTP transport**, where §4.4 already derives
> it through `get_client_id` in order to rate-limit on it. **That value is recorded in the audit
> event.**"

The row's remedy has been performed and the row still says it has not. Same shape for **C4-R**
(`:1068`): *"The approval decision is not among the audited fields ... **Unmitigated.** Add the
approval decision ... to the `audit.py` event"* against §5.3:375 *"**The audit event includes
`approval_state`.**"*

Both rows are then carried into the **Threshold disposition** table (`:1147-1148`) under **"Must
mitigate before implementation proceeds"**, which per `threat-modeling.md:86` is the gate on
implementation starting. **Two of the five stated freeze blockers are already fixed elsewhere in the
same document.** Whoever works that table either does redundant work or, more likely, concludes the
table is stale and stops trusting it - which is the failure mode for the other three rows, which are
real.

There is a second-order defect inside C1-R's remedy that §5.3 got right and §11 did not. §5.3:388-393
states that on stdio there is no client identity and the audit event must say attribution is
unavailable rather than emitting `"global"`. C1-R's remedy - *"Record the resolved client id"* - is
unqualified, and an implementer following it on stdio records `"global"`. R3's R-3 flagged exactly
this and its disposition was *"Accepted, modified. Qualify by transport; **reconcile §11:1073**"*.
**§5.3 was qualified. §11 was not reconciled.** Half of an accepted finding.

### H4. The C9 block and the duplicate-write row were added to the STRIDE tables and never carried into the disposition tables, the counts, or Residual Risks.

The threat model's three closing tables are its output. Six new rows entered the analysis and none
of them reached the output.

**C9-T is a High.** `threat-modeling.md:86`: *"**Critical/High**: Must mitigate before implementation
proceeds."* §11's must-mitigate table (`:1147-1153`) lists five rows: C1-R, C4-R, C5-R, C5-E, C8-I.
**C9-T is not among them**, and its own mitigation text concedes the drift diff is unexecuted, so it
is not cleanly mitigated either. It appears in neither disposition list.

**§11:1155, verbatim:** *"**Down from seven to five.** The TLS fix in §7.1 clears C1-S, C1-T and
C1-I; dropping `ResponseCaching` removes the cache disclosure from the model entirely."* The count
was computed before C9 existed and was not recomputed after. It is also wrong in the other direction
now that H3 shows two of the five are already closed.

**C9-D is an unmitigated Medium.** Its disposition cell reads *"**Open (B72).**"*, and
`CONFORMANCE-B1-B106.md:240` rates B72 **UNADDRESSED**. `threat-modeling.md:87`: *"**Medium**:
Mitigate before production release."* §11:1158-1161's production-release list names C3-T, C3-D, C3-I,
C6-D, C4-E, C7-I and C8-R. **C9-D is absent.** So is C9-I, which its own cell calls
*"**Residual and unmitigable in general**"* and which therefore belongs in Residual Risks - where it
also does not appear.

**C4-D, the duplicate write.** §11:1112, verbatim: *"It is now C4-D below **and in Residual
Risks**."* I read the Residual Risks table (`:1170-1183`) row by row. Its nine rows are: C4-S host
auto-response, the confirmation-token preview-then-create row, C6-S fencing, **C4-D abandoned
approval**, C8-E TLS assertion, C2-D quota amnesty, C7-I log stream, `problem+json` on stdio, and
the unobserved success shapes. **The duplicate-write risk is not there.** The sentence asserting its
presence was written in the same edit that failed to add it.

That is the class the brief asked about, aimed inward: a claim about the document's own contents,
checkable in the document, false.

### H5. §10.1 miscites the clause it excuses the project from, and the clause it does not cite forbids the remedy it proposes.

§10.1:934-937, verbatim:

> "**Two standard behaviours cannot be met as written, and are recorded rather than quietly
> skipped.** Quickstart-CI parity (`:80`) is unmeetable in the obvious form: CI runs credential-free
> by §8, and a Quickstart that reaches a working state needs a Jobvite credential."

**`readme-standard.md:80` is not the Quickstart parity clause.** Verbatim, `:80`:

> "- Inlined API reference tables that drift from the OpenAPI spec or generated CLI help."

That is an anti-pattern about API reference tables. The Quickstart parity clause is **`:67`**:

> "- **Quickstart parity**: the Quickstart commands MUST be exercised by CI on every merge to the
> default branch."

A wrong line number on a clause the design is **waiving** is worse than a wrong line number on one it
is meeting, because the waiver is the thing a reviewer is meant to be able to check.

**And the substance is wrong too.** §10.1 argues parity is unmeetable because a working-state
Quickstart needs a credential, and proposes that *"the README will mark the remaining step as
requiring a credential"*. `readme-standard.md:83`, in Anti-patterns, verbatim:

> "- Quickstart steps that require credentials, VPN access, or undocumented prerequisites."

**The standard forbids exactly the remedy §10.1 proposes.** The standard's own position is that a
Quickstart must not need a credential. A credential-free Quickstart - install, start, list tools - is
what `:48` and `:83` together require, and §10.1 already says CI can exercise precisely that. **So
`:67` is meetable, in full, by the path §10.1 has already described**, and it is meetable only
because the credential-requiring step must be removed from the Quickstart rather than annotated
inside it. Phil's stated doubt #5 was correct: the project has excused itself from something it can
do, and has done so in a way that adopts a named anti-pattern.

The badge half is a lesser version of the same. `:47` requires at least one CI status badge and `:70`
requires badges be live. §10.1 records this as a standard behaviour that "cannot be met as written".
It can: CI is specified in §10 and will exist. The honest statement is that the badge is added when
CI lands, not that the clause is unmeetable.

### H6. Six of Round 3's accepted findings were never applied to the document.

R3 returned 0c/5h/6m and its disposition table (`DESIGN-R3.md:333-357`) marks every minor
**Accepted**. Checked against the current text by grep:

| R3 finding | Disposition | State now |
|---|---|---|
| m1 - cut probe still live in §1 and §12 | Accepted | **Not applied.** §1:21 still lists *"the runtime `start`-base probe (§4.5)"*; §12:1190 still reads *"**The `start` base.** Now probed at runtime (§4.5), but the probe itself is unverified"*. §4.5:283 says *"it needs no probe."* |
| m2 - §12 Q4 answered inside the document | Accepted | **Not applied.** §12:1193 still asks *"Whether success bodies carry a `status` block at all"*; §8:756 answers it and `JOBVITE-API.md:397` states it outright |
| m3 - §8 requires tests for the cut token | Accepted | **Not applied.** §8:778 still reads *"token replay, expiry, and payload mismatch each refused"* |
| m4 - post-write audit warning routed through the failed stream; success-with-warning shape undefined | Accepted | **Half applied.** §5.3:407-409 now routes the warning to stderr, correctly. The second limb stands: §5.1:319 says *"No `success: true/false` envelope exists anywhere in this repository"* and nothing defines the shape of a "success with a warning" |
| m5 - C7-E gives no reason, against §11's own convention | Accepted | **Not applied.** §11:1107 still reads `\| C7 \| E \| No credible threat \| - \| - \| - \| - \|` |
| m6 - `resilience.md:226` ambiguous across two files and clipped | Accepted | **Not applied.** §11:1080 still cites `resilience.md:226` bare |
| m7 - threshold selection rule does not account for accepted-and-unmitigated C4-S | Accepted | **Not applied.** §11:1147 still selects *"unmitigated, inherent Critical or High"* and C4-S remains High, explicitly unmitigated, and absent |
| m8 - confirmation-token residue, eleven rows | Held for rerating | **Four rows survive.** Assets `:1005` still lists *"Confirmation-token HMAC signing key"* as an asset of a cut mechanism; the roster `:1165` still credits *"C4-T token binding"*; Residual Risks `:1174` still says *"Defence in depth: the deploy-time flag **and the confirmation token** both operate without host cooperation"*; Residual Risks `:1175` is an entire row about the token's preview-then-create weakness |

That is eight accepted items unapplied or half-applied. Fourteen changes were made and they went to
the MAJORs and to §11's new content. **The sentence-sized accepted findings were dropped.** m8's four
survivors are the sharpest: three of them state, in the section whose job is naming what protects the
write, that a control exists which §2.2:128-133 spends a paragraph explaining was cut. `:1174` in
particular offers the cut token as **defence in depth for the highest-rated residual risk in the
document**.

---

## MEDIUM

**m1. C9-T's `(§12)` cross-reference points at a section that does not contain the item, and §12's
closing claim is false.** §11:1123 ends *"**The diff is designed and unexecuted** (§12)."* §12's six
open questions are the credential, the `start` base, the not-found shape, the `status` block, Claude
Desktop elicitation, and the uvicorn shutdown dependency. **None is the capability-drift diff.** The
correct pointer is §10:884-886, which does carry the `UNVERIFIED:` marker, or §1:21 which names it.
Separately, §12:1201 reads *"All are external unknowns. **None is a reasoned-but-unexecuted claim
about our own stack.**"* Item 6 is entirely about our own stack, and the drift diff - which C9-T has
just pointed at §12 for - is the definitive reasoned-but-unexecuted claim about our own stack.

**m2. §5.1 still asserts B23 is met; the sweep still says it is not, for a reason the new test does
not touch.** §5.1:342: *"The rejection still fails closed and is unit-tested, which is what B12 and
B23 actually require."* `CONFORMANCE-B1-B106.md:156` rates B23 **PARTIAL** on two arms:
*"**Invalid/over-budget arguments** is the B12 gap above; the **unbounded-loop attempt** has no
analogue in §8 either."* The new §8:771 case closes the first arm. **§8 still contains no
unbounded-loop case.** R3's R-5 was accepted and half applied, and the half that was not applied is
the half §5.1's sentence still claims.

**m3. §7.5's new `send_email` requirement has no test and no stated failure mode.** §7.5:621-626 is
new and normative: *"The elicitation payload therefore names the candidate, the target job, and
**whether `send_email` is true** ... An approval obtained without showing the email is not an
approval for the email."* §8's approval cases (`:776-777`, `:781-784`) test deny,
accept-carrying-false, no-handler, second-leg consumption, and both eras. **None asserts the payload
contains those three items.** The requirement is therefore unenforced by the merge gate §11 relies on
for C4-E. Phil's stated doubt #4 is the second half: nothing says what happens if the host renders
none of the payload. I note the honest limit - the server cannot know what a client rendered, so
there is no server-side remedy - but the design's own answer to unknowable-host behaviour elsewhere
(§7.5:658-663: an unidentifiable era refuses the write) shows it knows how to write that sentence,
and here it does not. At minimum, *"An approval obtained without showing the email is not an approval
for the email"* should say it is a claim about what the server **sends**, not about what the approver
**saw**.

**m4. The new `JOBVITE_TOOLS` semantics did not propagate to the two places that state the same
rule.** §7.3:527-531 is new and explicit: `create_candidate` registers **only if**
`JOBVITE_ENABLE_WRITES=true` **and** it is named in `JOBVITE_TOOLS`. But §7.3's own requirements
table at `:545` reads *"| `create_candidate` | the v2 pair, plus `JOBVITE_ENABLE_WRITES=true` |"* -
the `JOBVITE_TOOLS` conjunct is missing from the table twenty lines below the paragraph that
introduced it. §2.2:123 likewise still reads *"Not registered unless `JOBVITE_ENABLE_WRITES=true`"*
with no mention of the second condition. And §8 has **no case at all** for `JOBVITE_TOOLS`: neither
the AND semantics nor §7.3:533's new *"An unrecognised name in `JOBVITE_TOOLS` is a startup
failure"*. A startup-failure rule with no test is the `--strict-markers` shape that the very same
paragraph invokes as its justification.

**m5. §4.5's completeness check depends on a field observed on one resource and inferred on the
others, and §4.5 does not say so.** `total` is confirmed for `GET /api/v2/candidate` by the one
genuine 200 (`JOBVITE-API.md:397-398`). For `/api/v2/job` the envelope `{total, requisitions[]}` is
marked `[INFERRED]` (`:483`, `:754`), and `:821` states *"The other four in-scope operations remain
entirely unobserved."* §4.5:296-299 states the check flatly as *"a real check"* with no resource
qualifier. §1:24-25 sets the standard the document holds itself to: *"A reviewer should treat
'verified' in this document as meaning one of the first two, and should challenge any sentence that
reads as verified without belonging to them."* This sentence reads as verified and does not belong to
them on three of the five tools. Separately, §9 hazard 5 (no stable sort, mutating set) means `total`
can change between the first page and the last, so even on an exhaustive scan a mismatch does not
distinguish a lost record from a concurrent insert. Neither interaction is stated.

**m6. Threat-model row identifiers are not unique, and the disposition tables address rows by
identifier.** `C4-D` names two different rows (`:1070` abandoned approval, `:1116` duplicate write).
`C7-I` names two (`:1104` PII in logs, Critical, mitigated; `:1105` log retention, Medium,
unmitigated). `C6-I` names two (`:1092` EEO, Critical; `:1093` new field, Medium). `C1-S` names two
(`:1024`, `:1025`). `C4-E` names two (`:1071`, `:1072`). The three closing tables then refer to
*"C7-I PII in logs"*, *"C7-I log-stream handling"* and *"(C4-D)"*, disambiguating by prose in two
cases and not at all in the third. §11:973 claims the ratings are *"Machine-checked"*. **No machine
can check a coupling or a disposition claim against a table whose keys collide**, which is part of
why H2 and H4 went unnoticed. Numbering rows uniquely within each component would make the coupling
claim mechanically verifiable, which is what §11 says it wants it to be.

**m7. §11 states its own conventions twice, in two different registers.** `:953-972` gives the
triggers, the three conventions and their justifications. `:983-989` then gives the triggers, the
inherent-risk convention, the matrix source and the STRIDE-coverage convention again, in compressed
form. The second block is a leftover the first was written to replace. Nothing in it contradicts the
first, so this is redundancy rather than error, but it is seven lines telling a reader that the
section was appended to rather than revised, in the section a reviewer is asked to trust most.

**m8. Three C9 mitigations assert facts about the build that §10 never states.** C9-S (`:1122`)
claims *"Committed `uv.lock` **with hashes**"* and C9-E (`:1127`) claims *"`uv` with a frozen lock
and **hash verification**"*; §10:848-852 states the lockfile is committed and `uv sync --frozen`
runs, and says nothing about hashes. C9-E claims *"no `setup.py` execution in our own build
**(hatchling)**"*; §10's packaging block (`:833-842`) has no `[build-system]` table and hatchling
appears nowhere else in the document. C9-I (`:1125`) claims *"no dependency added without review"*, a
control specified nowhere in §10 or anywhere else. **A threat model may not be the only place a
control is stated**, because the implementer builds from §10 and the reviewer audits against §11.
These are unverified rather than wrong - `uv.lock` does record hashes - but the design has not said
so, and §11 is not the place to say it first.

**m9. Two C9 ratings rest on judgements I would contest, though neither breaks the matrix.**
C9-I *"A dependency exfiltrates credentials or candidate data at runtime"* is rated L=**Low**, which
`:66` defines as *"Requires insider access or unlikely preconditions"*. This project deliberately
ships a **beta** framework and a transitive **prerelease** (`fastmcp-slim==4.0.0b4`), a materially
thinner review surface than a stable release. Under `:65`, *"Requires moderate skill or specific
conditions"*, L=Medium is at least as defensible, and L=Medium with I=High yields **High** per `:81`
- a must-mitigate. C9-D *"a required CI gate goes red ... blocking all merges"* is rated I=**Low**;
`:73` defines Medium as *"Partial data exposure, **service degradation**"*, and a permanently red
required gate is degradation of the delivery pipeline. I=Medium with L=High yields **High** per
`:80`. I am not asserting either rerating is correct - the Impact ladder plausibly scopes "service"
to the product, and supply-chain compromise plausibly is low-likelihood. **I am asserting that the
two rows whose ratings keep C9 out of the must-mitigate table are the two rows whose inputs are
contestable**, and that a threat model extended by its own author with no validation pass is exactly
where that pattern should be looked for. Phil's stated doubt #6.

---

## MINOR

**n1. §4.5 does not cite the one piece of evidence that would settle its own argument.** §4.5:288-291
justifies `start=0` from *"our own finding above"* - the inference that a 1-based server clamps.
`JOBVITE-API.md:401` states, from the genuine recorded 200: *"**`start=0` is accepted and returns
records**, rather than erroring. That falsifies the "1-based and strict" hypothesis."* That is an
**observation**, and it is the strongest sentence available for the paragraph Phil has now written
three times. It is in the repository, it is cited by neither §4.5 nor §12, and its absence leaves the
mechanism resting on an inference when it could rest on a capture.

**n2. §1's preamble misdescribes what is unexecuted.** §1:20-22: *"**Two mechanisms designed here
have never been executed** ... the runtime `start`-base probe (§4.5) and the capability-drift diff
(§10)."* The probe does not exist (H6/m1). The mechanism that replaced it is the base-agnostic
seen-set, and the part of it that matters - that `start=0` is accepted - **has** been observed (n1).
Both halves of the sentence are wrong about the same paragraph.

**n3. The status block does not record Round 3.** `:3-7` reads *"Status: **DRAFT, revision 3.**
Incorporates adversarial review rounds 1 and 2 (`DESIGN-R1.md` 0c/2h/1m, `DESIGN-R2.md` 0c/3h/1m)"*.
R3 ran, returned 0c/5h/6m, and produced fourteen changes to this document. It is not listed. The line
also still says *"Frozen at 0C/0H/0M"* as a present-tense status while three rounds have returned
findings.

**n4. §10 and §11-B6 give different accounts of the same incident.** §10:946-947: *"It does nothing
about confidential prose pasted into Markdown, **which is the incident we actually had**."* B6
(`:1015`): *"a CONFIDENTIAL vendor PDF reached both public remotes and a history rewrite alone did not
evict it."* Both are true - the task record shows a PDF purge and a separate verbatim-prose scrub -
but each sentence is written as though its own incident were the only one. §10's *"the incident we
actually had"* is the misleading half, because it is the sentence that decides how much credit the
file-type gate gets.

**n5. C9 is placed between the C4-D note and C8, and uses a different table header.** Every other
component table heads `| Component | Category | ... | Mitigation |`; C4-D's addendum and C9 head
`| # | Cat | ... | Mitigation / disposition |`. Cosmetic, but it is the visible seam where the new
content was appended, and it is the same seam H4 shows was never carried into the outputs.

**n6. §5.3's "success with a warning" shape is still undefined** (R3 m4, second limb). §5.3:405-406
mandates the response; §5.1:319 says *"No `success: true/false` envelope exists anywhere in this
repository."* What a caller receives is unspecified.

---

# BLUE ROUND - Normal response

| # | Verdict | Reasoning |
|---|---|---|
| H1 | **Accept** | The worked example in §7.7 is a mismatch and §4.5 says a mismatch is surfaced. Not arguable. The fix is two sentences: scope the check to a scan that terminated on a short page without hitting the result cap, and say where the mismatch goes |
| H2 | **Accept** | I walked the rows before writing this and both gaps are real. C2-R is the more damaging because R3 already found it and the fix went to two of the three named rows |
| H3 | **Accept** | Two of five stated freeze blockers are closed elsewhere in the document. C1-R's unqualified remedy is the specific thing R3's R-3 asked to reconcile |
| H4 | **Accept** | Six rows entered the analysis and none reached the outputs. The `:1112` sentence asserting C4-D is in Residual Risks is checkable and false |
| H5 | **Accept** | `:80` is the wrong line and `:83` forbids the proposed remedy. I checked both at the file |
| H6 | **Accept** | Verified by grep, item by item. Eight accepted items unapplied or half-applied |
| m1 | **Accept** | Wrong cross-reference plus a false closing claim in §12 |
| m2 | **Accept** | The sweep row is unchanged and the arm it names is still absent from §8 |
| m3 | **Accept, modified** | Accept that the requirement is untested and that the claim overreaches. **Reject** any remedy that pretends the server can verify rendering. The fix is a test on the payload's contents plus one sentence bounding the claim |
| m4 | **Accept** | Three limbs, all verified: the table, §2.2, and the missing tests |
| m5 | **Accept** | §1:24-25 sets the standard and this sentence does not meet it. The hazard-5 interaction is a genuine second limb |
| m6 | **Accept** | Five colliding identifiers, and the collisions are load-bearing for H2 and H4 |
| m7 | **Accept, downgraded to editorial** | Redundant, not wrong. It stays MEDIUM only for what it signals about how §11 was edited |
| m8 | **Accept** | The hash claim is probably true and the design has not said it. That is the distinction the document itself insists on in §1 |
| m9 | **Accept as stated, and only as stated** | The matrix is not violated and I will not claim it is. The finding is that the two contestable inputs are precisely the two that keep C9 out of the must-mitigate table, and that the extensions had no validation pass |
| n1-n6 | **Accept** | All verified at their lines |

**Rejected outright: nothing.** I looked for a place to reject and did not find one I could defend.

---

# RED ROUND - Adversarial rebuttal

Two new points unlocked by BLUE's answers, and one concession.

**Concession first.** RED considered arguing that §4.5's `start=0` is unsafe because a strict 1-based
server would reject it. **`JOBVITE-API.md:401` refutes that**: `start=0` is accepted and returns
records, observed in the one genuine 200. RED withdraws it. It is the finding this round most wanted
to make and the evidence does not support it, which is worth recording because the brief warned
against manufacturing one.

**New R-A (folds into H2, raises its weight).** BLUE accepts H2 and proposes adding tests. **Adding
tests is what happened last round and it is what produced H2.** R3's R-2 named three rows; three
tests were added; two rows were closed; the claim was rewritten to say all three were. The defect is
not the missing tests, it is that **the claim is restated by hand each time and verified by hand each
time**, and hand-verification of a claim quantified over 43 rows keyed by colliding identifiers has
now failed twice in a row. The remedy H2 needs is not three more tests; it is either a machine-checked
coupling (which m6's unique identifiers would enable) or the deletion of the universally quantified
sentence in favour of a per-row `Test:` column. **A claim that has been false on two consecutive
assertions should not be asserted a third time in the same form.**

**New R-B (raises H5).** BLUE accepts H5 as a citation error plus a substance error. There is a third
layer. §10.1's opening premise is *"**The README is not written yet, deliberately**: it would have to
assert a Quickstart that reaches 'a working state' ... for software that does not exist."* That is
correct and well argued. But H5 shows the section then reasons **from the design's own constraint to
a conclusion about the standard** - "we need a credential, therefore parity is unmeetable" - without
opening the standard to see whether it anticipates that case. **It does: `:83` names
credential-requiring Quickstarts as an anti-pattern.** The class here is not a typo in a line number.
It is the same class as §6.2's `priority: optional` claim that R2 killed: **a scope argument
compressed into a claim about what the standard says, made without reading the clause.** §6.2:444-448
contains that lesson in the document's own words - *"That was false and checkable"* - and §10.1
repeated it four sections later. That earns H5 its rank on its own.

---

# BLUE ROUND - Final response

**R-A: accepted, and it changes the remedy.** H2 should not be closed by adding two tests and
restating the sentence. Either §11 gains a per-row test reference and the universal sentence goes, or
the sentence stays and something mechanical checks it. Given m6, the honest minimum is: number the
rows uniquely, add a `Test` column, and replace §11:979 with a statement about the column. That also
closes H4's bookkeeping class, because a table with unique keys can be diffed against the disposition
lists.

**R-B: accepted.** H5 stands as a HIGH on the strength of the class, not the line number.

**On the concession:** recorded in the final report, because a round that finds six HIGHs should also
say which attack it tried and could not land.

---

# Final report

| # | Sev | Section | Finding | Disposition |
|---|---|---|---|---|
| H1 | HIGH | §4.5:296-299 vs §7.7:735-737 | The completeness check's trigger condition is satisfied by the design's own default capped result (`showing 50 of 1,240`), so it fires on every normal call. Third attempt at this paragraph, wrong in a new direction | **Accepted.** Scope the check to an exhaustive scan; define where a mismatch surfaces. [DEALBREAKER if shipped as written] |
| H2 | HIGH | §11:979-980 | The coupling claim is still false: C2-R (High, mitigated) and C9-T (High, mitigated, new) have no §8 test; C1-S/T/I need the escape clause that only appears at `:1163`. Fifth self-compliance assertion to be wrong | **Accepted, remedy changed per R-A.** Per-row `Test` column plus unique row ids; retire the universal sentence |
| H3 | HIGH | §11:1032, `:1068`, `:1147-1148` vs §5.3:375,386 | C1-R and C4-R are marked Unmitigated and listed as freeze blockers; §5.3 says both are done. C1-R's remedy is also unqualified where §5.3 qualified it by transport (R3 R-3, half applied) | **Accepted.** Reconcile both rows and recompute the blocker list |
| H4 | HIGH | §11:1112, `:1116`, `:1123`, `:1147-1161`, `:1170-1183` | The C9 block and C4-D never reached the disposition tables, the counts or Residual Risks. C9-T is an unlisted High; C9-D an unlisted unmitigated Medium; `:1112`'s claim that C4-D is in Residual Risks is false | **Accepted.** Carry all six new rows into the outputs and recompute "down from seven to five" |
| H5 | HIGH | §10.1:934-937 | Quickstart parity cited as `readme-standard.md:80`; the clause is `:67`. The waiver is also substantively wrong: `:83` forbids credential-requiring Quickstarts, so the clause is meetable by the credential-free path §10.1 already describes. Same class as the `priority: optional` error R2 killed | **Accepted.** Fix the citation, withdraw the waiver, keep the badge item as "added when CI lands" |
| H6 | HIGH | §1:21, §5.1:319, §8:778, §11:1005,1080,1107,1147,1165,1174,1175, §12:1190,1193 | Eight of Round 3's accepted findings unapplied or half-applied, including four confirmation-token rows, one of which offers the cut token as defence in depth for the document's highest residual risk | **Accepted.** Apply m1, m2, m3, m5, m6, m7, m4's second limb and m8's four survivors |
| m1 | MED | §11:1123, §12:1201 | C9-T cites §12 for the unexecuted drift diff; §12 does not contain it, and §12:1201 claims no item is a reasoned-but-unexecuted claim about our own stack | Accepted |
| m2 | MED | §5.1:342 | Asserts B23 is met; `CONFORMANCE-B1-B106.md:156`'s unbounded-loop arm still has no §8 case | Accepted |
| m3 | MED | §7.5:621-626, §8:776-784 | The new `send_email` approval-payload requirement has no test, and the claim about what an approver saw exceeds what the server can know | Accepted, modified |
| m4 | MED | §7.3:527-533,545, §2.2:123, §8 | The new `JOBVITE_TOOLS` AND-semantics missing from §7.3's own table and from §2.2; neither the AND nor the unknown-name startup failure is tested | Accepted |
| m5 | MED | §4.5:296-299 | The completeness check leans on `total`, observed on one resource and `[INFERRED]` on the others, stated without qualifier against §1:24-25's own rule; and §9 hazard 5 makes a mismatch ambiguous | Accepted |
| m6 | MED | §11 tables | Five colliding row identifiers (C4-D, C7-I, C6-I, C1-S, C4-E) while the disposition tables key on them; makes "Machine-checked" and the coupling claim unauditable | Accepted |
| m7 | MED | §11:953-972 vs `:983-989` | The section states its own conventions twice; the second block is the one the first replaced | Accepted, editorial |
| m8 | MED | §11:1122,1125,1127 | C9 asserts lock hashes, a hatchling build and a dependency-review policy that §10 never states | Accepted |
| m9 | MED | §11:1125,1126 | C9-I's L=Low and C9-D's I=Low are the two contestable inputs, and they are the two that keep C9 out of the must-mitigate table. Matrix not violated | Accepted as stated |
| n1 | MIN | §4.5:288-291 | Does not cite `JOBVITE-API.md:401`, the observation that would move the paragraph from inference to evidence | Accepted |
| n2 | MIN | §1:20-22 | Misnames the unexecuted mechanism as a probe and calls unexecuted the one thing that was observed | Accepted |
| n3 | MIN | §1:3-7 | Status block omits Round 3 and its 0c/5h/6m | Accepted |
| n4 | MIN | §10:946-947 vs §11:1015 | Two different accounts of "the incident we actually had"; there were two incidents and neither sentence says so | Accepted |
| n5 | MIN | §11:1109-1127 | C9 placed between the C4-D note and C8 with a different table header; the visible seam | Accepted |
| n6 | MIN | §5.3:405-406 vs §5.1:319 | "Success with a warning" shape still undefined (R3 m4, second limb) | Accepted |

## What did not recur, and what did

**Did not recur:** the matrix arithmetic. All eleven new and rerated rows agree with `:78-82`, and
Phil's doubt #2 about the C9 ratings is not borne out arithmetically. Every `threat-modeling.md`
citation lands. The fourteen-section README count lands. The "eleven consecutive obligations" figure
lands. B12 is genuinely closed.

**Did recur:** the false-claim-about-the-world class, once, at H5 - and it is the same shape as the
`priority: optional` error R2 killed, which is worse than a fresh mistake. Alongside it, the
claim-about-the-document's-own-contents class that R3 identified has **grown**, not shrunk: H2, H3,
H4 and H6 are all of it, and H4 contains a sentence asserting the presence of a row that is not there.

**The attack that failed, recorded deliberately:** RED tried to break `start=0` on the hypothesis that
a strict 1-based server rejects it. `JOBVITE-API.md:401` refutes it from the one genuine 200.
Withdrawn.

## The pattern under the six HIGHs

Five of the six are the same mechanism. New text was written, and the places that state the same fact
elsewhere were not revisited: §11's rows against §5.3 (H3), §11's tables against §11's own new rows
(H4), §11's coupling sentence against §8 (H2), §7.3's paragraph against §7.3's own table (m4), R3's
accepted minors against the document (H6). Only H1 and H5 are defects in the new text itself.

**This document's failure mode is no longer being wrong about the world. It is that a fact stated in
two places gets fixed in one.** That is a structural property of a 1234-line design edited by
paragraph, and it will recur in Round 5 unless something mechanical checks the cross-references -
which is also, not coincidentally, the remedy H2 and m6 converge on.

## Freeze recommendation

**Do not freeze.** `0c / 6h / 11m surviving.`

Six HIGHs, one of them a mechanism that misbehaves on the default path (H1), one a miscited waiver
that excuses the project from a meetable obligation (H5), and one an accepted-findings backlog that
leaves a cut control named as defence in depth (H6). §11:975-976 states the standard the section is
to be held to: *"if a mitigation loses its test, this threat model becomes false."* By that standard
it is false now.

**The good news is the shape.** None of the six needs a credential, a spike, or a design decision. H1
is two sentences. H3, H4 and H6 are bookkeeping against text that already exists. H5 is a citation fix
plus a withdrawn waiver. Only H2 needs a structural change - the per-row `Test` column and unique row
identifiers - and that same change is what would stop H4's class recurring.

Round 5 should be a re-check, not a fresh attack, and it should be run **after** m6's unique
identifiers land so that the coupling claim can be verified mechanically rather than by hand for the
third time.

---

## What I did NOT review, and why

This section is the map for Round 5.

- **`FASTMCP-SPIKE-4.md` in full (~2350 lines).** Not opened at all this round. **Three consecutive
  rounds have now declined it.** R2 read §§1.3, 6, 12.1, 13-15, 17, 19; R3 read it only for
  pagination and era claims; I read none of it. **Every "Measured:", "Verified:" and "Executed on
  both:" claim in §4.3, §4.4, §7.4, §7.5 and §7.7 is therefore unchecked against its spike by
  anybody.** That is a large, growing and entirely unexamined surface, and it is the single
  highest-value target left in this document. §4.4's burst arithmetic ("burst 3 yields 1 tool call, 5
  yields 3, 10 yields 8") and §7.5's two-era table are the two I would open first.
- **`CONFORMANCE-DESIGN-ARTIFACT.md`.** Not opened. R3 also did not open it and called that a real
  gap in its own review. **It is now a two-round gap.** Named in both briefs, read by nobody.
- **`STANDARDS.md` (1310 lines) and `COMPLIANCE-SPEC.md` (661 lines) in full.** Not opened. I worked
  from `CONFORMANCE-B1-B106.md`'s rows for the specific B-numbers I cite and verified those clauses at
  their `file:line` in the standards corpus directly.
- **The 37 UNADDRESSED and 22 PARTIAL rows as a set.** Deliberately not duplicated, per R2's and R3's
  precedent. I touched B12, B22, B23, B67 and B72 only.
- **`docs/DECISIONS.md` D1-D17.** Not opened this round. R3 grepped it for stale token and probe
  references and found it clean; given H6 shows stale references surviving in `DESIGN.md` itself, I
  would not treat that grep as still current.
- **`JOBVITE-CONTRACT.md` (676 lines).** Not opened. `JOBVITE-API.md` answered every pagination and
  `total` question I needed, but the contract document is where §9's seven hazards come from and I did
  not check any of them against it.
- **`standards/` beyond two files.** I opened `architecture/threat-modeling.md` and
  `documentation/readme-standard.md`. I did **not** re-open `ai/agent-guardrails.md`,
  `ai/tool-calling.md`, `ai/prompt-injection.md`, `architecture/error-contract.md`,
  `architecture/caching.md`, `architecture/gdpr-data-rights.md`, `backend/rate-limiting.md`,
  `backend/resilience.md` or `backend/input-validation.md`. R3 verified all of those at their cited
  lines and I relied on that. **H5 is the reason that reliance is uncomfortable**: I found a
  miscitation in the one standard I did open fresh, in a section R3 never examined. **The four
  citations added or changed since R3 that I did not re-verify are `agent-guardrails.md:121-123`
  (§5.3), `:79` (§5.3), `:122` (C4-R) and `input-validation.md:223-226` (C3-D).** R3 verified the
  first and third; the second and fourth I have not checked, and neither did R3 in the form they now
  appear.
- **`docs/reviews/THREAT-MODEL-DRAFT.md`.** Deliberately not opened, for the same reason R3 gave:
  reading the draft tells a reviewer what the author intended rather than what the integrated section
  says. The cost is unchanged - I cannot say which of §11's omissions were dropped in integration and
  which were never drafted.
- **`docs/reviews/PENDING-DESIGN-CHANGES.md` and `PENDING-CONFORMANCE-FIXES.md`.** Not opened. Given
  H6, **somebody should diff those two files against `DESIGN.md` directly**; that is a mechanical
  check that would have found H6 in five minutes and it is the obvious first task of Round 5.
- **Anything requiring a live Jobvite call.** No credential, no sandbox. No remedy above needs one.
  H1's fix, H5's fix and every bookkeeping fix are actionable today.
- **`src/` and `tests/`.** Empty. Correct for a design round.
