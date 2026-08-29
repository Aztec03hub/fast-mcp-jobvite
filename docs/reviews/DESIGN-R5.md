# DESIGN-R5 - Round 5 adversarial review, and the freeze decision

**Task:** DR5 · **Reviewer:** `design-review-r5` (single agent, both lenses) · **Date:** 2026-08-27 05:48 PM CDT
**Subject:** `docs/DESIGN.md` (DRAFT revision 4, 1460 lines), and `docs/reviews/check-coupling.py`
as its standing guarantor.

**Result: 0c / 4h / 5m surviving. DO NOT FREEZE.**

---

## What I actually read

**In full, in one sitting** (this was the point of the round - concern #4): `docs/DESIGN.md`, all
1460 lines, §1 through §13 including the whole of §11. `docs/reviews/check-coupling.py` (all 300
lines, including its docstring's declared limitations) and `check-coupling-controls.py`'s output.

**Prior rounds' maps first, per the brief:** the "What I did NOT review" section of `DESIGN-R1.md`,
`R2`, `R3` and `R4`, plus R3's and R4's factual-assertions sections and R4's freeze recommendation
and closing map.

**Opened at every `file:line` I cite, in the standards corpus at
`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/`:**
`ai/agent-guardrails.md:38-42,47-49,70-75,77-81,119-131`; `ai/tool-calling.md:54,171-173`;
`ai/prompt-injection.md:124-125`; `backend/input-validation.md:220-226,391-392`;
`backend/rate-limiting.md:94-97,361-362`; `backend/resilience.md:224-226`;
`architecture/gdpr-data-rights.md:9,119-129`; `architecture/caching.md:628,833,841` and its whole
`MUST` count; `architecture/threat-modeling.md:1-12,35,62-90,118-129,143`;
`documentation/readme-standard.md:41-90`; `architecture/error-contract.md:40-48`; and a corpus-wide
`grep -rln "^priority: optional"`.

**Opened targeted:** `docs/research/JOBVITE-API.md:393-402` and §0.2 at `:51`;
`docs/research/FASTMCP-SPIKE-4.md:887-944,1058-1102` and its §20 heading map at `:1979-2334`;
`docs/reviews/CONFORMANCE-B1-B106.md:1-55`; the `docs/adr/` directory listing.

**Executed rather than read:** `check-coupling.py` against `DESIGN.md` (green, exit 0);
`check-coupling-controls.py` (21/21 fired); and **five mutation experiments of my own**, including
an exhaustive 8-disposition x 19-row sweep (152 runs) against a temp copy. `DESIGN.md` was opened
read-only throughout and no file outside `docs/reviews/` was touched.

---

## The factual-assertions-about-the-world check, run first

Per the brief this is cheap and has the best yield. **This round it yielded one MINOR, not a HIGH.**
Recording the negative results explicitly, because a clean sub-result is only worth the checks
behind it.

**Landed correctly, checked at the file:**

- `threat-modeling.md` frontmatter is `applicable_to: all` (`:6-7`) and `priority: required` (`:8`);
  `:35` is the STRIDE-per-component sentence; `:62-74` the ladders; `:78-82` the matrix; `:86-88`
  the thresholds; `:120-127` the six Required triggers; `:143` "authored during specification".
  **Every one lands.** Four of the six triggers do fire (`:122` PII, `:123` authn/authz, `:124`
  external endpoints, `:125` third-party integrations).
- `agent-guardrails.md:70-73` is the Default-deny block, and it does name *"outbound message
  to a third party"* and *"Fail closed: no approver, no action"*. `:40` is the audit-logging
  mandate. `:47-49` is the Minimal tool set bullet. `:79` does require recording *who* approved.
  `:122` does read *"result status, latency, the approval decision if gated, and"*.
- `tool-calling.md:171-173` names exactly the five fields §5.3 says it names. `:54` is the
  loose-types sentence, and it is a different obligation, as §2 says.
- `prompt-injection.md:124-125` reads *"Enforce input size/encoding limits before dispatch; reject
  control characters and oversized payloads"* - **verbatim as §2.1 quotes it.**
- `input-validation.md:221-226` is the four-row limits table with exactly 5 / 1,000 / 100 / 1 MiB.
  `:391-392` are the body-size-via-middleware and depth-limiting items. **Both land.**
- `rate-limiting.md:94-97` contains both phrases §1 quotes - *"because they desynchronize across
  replicas"* and *"a 4-replica deployment with in-memory limits gives each client 4x the intended
  quota"*. **Verbatim.** `:361-362` is the 429-uses-ProblemDetail rule.
- `resilience.md:224-226` requires logging every retry and every breaker transition, each carrying
  `request_id`. C5-R1 cites it correctly.
- `gdpr-data-rights.md:9` is `priority: required`; `:119-129` is Article 30 and `:126` is
  *"Downstream processors"*.
- `caching.md` contains **zero** occurrences of `MUST` (`grep -c` = 0), exactly as §7.7 claims.
  `:628` is the *Cache Key Namespacing* heading, `:833` the *"when needed"* tick, `:841` the
  *"Cache user-specific data without proper namespacing"* Don't. **All three land.**
- `readme-standard.md:45-58` is fourteen numbered sections in a fixed order; `:43` requires the
  headings match exactly; `:67` is Quickstart parity; `:70` is badges-are-live; `:83` is the
  credential-requiring-Quickstart anti-pattern. **§10.1's reading of `:67` vs `:83` is correct.**
- `error-contract.md:44` is *"All error responses MUST use the media type:"*. **Lands.**
- `JOBVITE-API.md:397` does state a success body carries a `status` block; `:399` does state
  `start=0` is accepted and returns records **and** in its own sentence declines to separate
  0-based from 1-based-with-clamping. §4.5 represents both halves accurately.
- **§4.4's burst arithmetic**, which R4 named as the first thing it would open and did not:
  `FASTMCP-SPIKE-4.md:913-915` reads `burst_capacity=3 -> 1`, `=5 -> 3`, `=10 -> 8`, and `:918`
  derives `desired + 2` from `server/discover` + `tools/list`. `:1058` is the `burst_capacity=6`
  both-eras arm. **Every number in §4.4 matches its spike line.**
- **The matrix arithmetic, computed rather than sampled.** I parsed all 60 STRIDE rows and applied
  `:78-82` to the 49 rated ones. **49 rated rows, 0 mismatches.** The arithmetic is right.

**Did not land: m1 below** - one characterisation of the standards corpus is false in detail,
though its conclusion survives.

---

# RED ROUND - Adversarial Review

## HIGH

### H1. There is a fifth gate defect, it is worse than the four before it, and every row that names a §8 case can escape through it. [DEALBREAKER FOR FREEZE]

The brief said to assume a fifth. There is one, and it is not subtle once you stop choosing your
own control subjects.

`check-coupling.py`'s check 3 forbids a Critical or High row from claiming exemption from having a
test. That ban is keyed on `NOT_REQUIRED_RE` alone:

> ```python
> elif (m := NOT_REQUIRED_RE.match(test)) is not None:
>     if rid in high:
>         failures.append(...)
> ```

Everything else falls through to `DISPOSITION_RE`, which accepts `no credible threat`
**unconditionally, at every severity**. And the reverse-direction status-token check consults
`NOT_MITIGATED_RE`, which is `residual|accepted|unmitigated` - **`no credible threat` is not in
it.** So a row may carry the `Mitigated` token *and* dispose of itself as `no credible threat`, and
neither half of the biconditional objects. Check 4 then skips it, because the token puts it in
`mitigated` rather than `unmitigated`.

**Measured, not reasoned.** I ran an exhaustive sweep: for each of the 19 rows that currently names
a §8 case, substitute each of the 8 recognised dispositions and re-run the gate. 152 runs.
**25 substitutions produce exit 0.** Six are legitimate (a Medium or Low row taking
`not required (<its own rating>)`, which is the designed exemption). **Nineteen are not, and they
are exactly the `no credible threat` column - one for every single row that names a §8 case:**

```
C1-S1 High     C2-R1 High     C4-E1 High     C5-S1 Critical   C6-S1 Critical
C1-T1 High     C3-T1 Medium   C4-E2 Medium   C5-I1 High       C6-T1 Low
C1-R1 High     C3-D1 Medium   C4-I1 Medium   C6-I1 Critical   C7-I1 Critical
C1-I1 High     C3-E1 Medium   C4-R1 High     C9-T1 High
```

Worked instance, run and confirmed: take C4-E1 - the accept-carrying-`false` guard, an inherent
High, named in the "Already mitigated at Critical or High" roster as load-bearing - replace
`§8: accept-carrying-false refuses` with `no credible threat`, change nothing else. Gate output:

> `PASS: ids unique, STRIDE coverage complete, all 60 rows at EVERY severity dispose of themselves
> by naming a §8 case that exists ... no Critical/High row claims exemption from having a test ...`

**exit 0.** The row now claims a mitigation, is still on the roster, and names no test at all. All
four Criticals - the 200-with-401 trap, indirect prompt injection, EEO exclusion, PII in logs - go
green the same way.

This is the same *class* as FIX-8 and it is a worse *instance*. FIX-8 made rows invisible to the
loop; this lets the loop see the row, read its disposition, and approve it. And it is
self-contradictory on the document's own terms: §11 convention 4 defines `no credible threat` as
what a row says **where a category carries no credible threat**, and every such row in the document
carries `-` in Likelihood, Impact and Risk. Nothing in the gate ties the disposition to an unrated
row.

**Why this is a freeze blocker specifically.** §1's freeze rule makes the design changeable only by
ADR after freezing, and §10 makes `check-coupling.py` "the only thing standing between this document
and a fifth wrong assertion that the threat model and the test list agree". Freezing hands the
guarantee to a gate that does not hold it for any row.

**Remedy, and it is small.** In check 3, treat `no credible threat` as legal only when the row's
Likelihood, Impact and Risk cells are all `-`; and add it to `NOT_MITIGATED_RE` so the token/Test
biconditional rejects `Mitigated` + `no credible threat`. Then add two controls, and pick their
subjects **from the rows the existing controls did not use.**

### H2. §11 convention 3 says "Machine-checked" and no machine checks it. The one committed gate explicitly disclaims the check.

`DESIGN.md:1205-1208`, verbatim:

> "3. **Ratings are computed from the matrix at `:78-82`, not chosen.** Likelihood and Impact are
>    judged against `:62-74`; the Risk cell is whatever the matrix yields. Machine-checked: every
>    rated row agrees with it."

`check-coupling.py`'s docstring, verbatim, under *What this script does NOT check*:

> "  - Whether a row's risk RATING is right. A Critical threat rated Medium escapes the
>    Critical/High strictness entirely, and nothing here can see that."

Those are the only two Python files in the repository (`ls docs/reviews/*.py`), and the second
one only mutates the first. **No machine checks the matrix.** What actually happened is that R3
hand-checked 43 rated rows and R4 hand-checked eleven new ones - `DESIGN-R3.md`: *"I also
hand-checked the arithmetic claim ... All 43 rated rows agree"*. The claim was upgraded from
"hand-checked" to "Machine-checked" without a machine.

**The fact is true and I verified it independently** - I parsed the tables and applied `:78-82`
programmatically: 49 rated rows, 0 mismatches. This is a defect in the *mechanism*, not the
arithmetic. But that is exactly the distinction §11 makes eight lines below, about the sentence it
retired:

> "**A claim about coverage is worth exactly the check that was run against it**, so the claim is
> now a column and the check is a script."

Convention 3 is a claim about coverage with no script. It is the retired sentence's failure mode,
re-entering the same section in the adjacent bullet.

**And the missing check is load-bearing, not cosmetic.** The gate's own disclosed rating hole -
"a Critical threat rated Medium escapes" - is only reachable *because* nothing computes the matrix.
I confirmed it: rerate C5-S1 from `**Critical**` to `Medium` (leaving L=H, I=H untouched) and swap
its test for `not required (Medium)`; the gate returns exit 0. A matrix check would fire on that
mutation, because H/H is Critical by `:78-82`. **One check closes both H2 and the gate's declared
worst blind spot.**

### H3. §1.1 and §12 disagree about how many designed mechanisms have never been executed, and the disputed one carries a threat-model mitigation with no marker.

`DESIGN.md:34-38`, the front matter that tells a reviewer how to read the entire document:

> "- **One mechanism designed here has never been executed**: the capability-drift diff (§10), which
>   is marked at its point of use and carried in §11's Residual Risks."

`DESIGN.md:1464-1469`:

> "Two items are different in kind, because they are reasoned claims sitting inside sections whose
> neighbouring results *were* executed, and so borrow credibility nobody granted them: the
> **capability-drift diff**, marked `UNVERIFIED:` at its point of use (§10) and carried in §11's
> Residual Risks; and the **circuit breaker**, which appears in §4.3 beside a measured retry finding
> and has no supporting execution anywhere."

One and two. §12 is right and §1.1 is wrong, and the consequences are concrete:

- **§4.3:277-280 carries no marker.** `grep -n "circuit breaker\|breaker" docs/DESIGN.md` returns
  ten hits; not one is an `UNVERIFIED:` at the breaker's point of use. The capability-drift diff
  gets its marker at §10; the breaker gets none, in a section whose neighbouring bullets read
  "Measured: one call, **four rows created**."
- **§11's Residual Risks has no circuit-breaker row.** The capability-drift diff has one. So of
  §1.1's two promised treatments - marked at point of use, carried in Residual Risks - the breaker
  receives neither.
- **A threat-model row is mitigated by it.** C5-D1 (`:1276`): *"Bounded retry budget inside the
  inbound timeout, jitter, one breaker per dependency, 4xx excluded from tripping it (§4.3).
  Mitigated"*, disposed `not required (Medium)`. An unexecuted, unevidenced, unmarked mechanism
  carries a Medium mitigation.

§1.1 closes by telling the reviewer to *"challenge any sentence that reads as verified without
belonging to them."* This is that sentence, and §1.1 is the paragraph that certified it.

**Remedy:** change §1.1's "One mechanism" to "Two mechanisms" and name the breaker; add the
`UNVERIFIED:` marker at §4.3; add a Residual Risks row. Three edits, no new information required.

### H4. The freeze rule is under-specified, it contradicts §13's own freeze procedure, and as written it permits freezing with three inherent Critical/High rows unmitigated.

Nobody has reviewed this rule. Three problems, in increasing order of seriousness.

**(a) §1 and §13 disagree about what freezing requires.** §1:17-19:

> "this document freezes when a review round returns 0C/0H/0M against it, and **after that** only a
> numbered ADR in `docs/adr/` may change it."

§13:1456-1460:

> "**Freeze procedure, and one step exists because it already failed once:** every **conditional**
> dismissal in the standards analysis is re-tested at freeze. ... `devops/docker.md` and
> `backend/idempotency.md` are the two most likely to have gone live."

§1 makes freezing a pure function of one review result. §13 adds a mandatory precondition that a
review round cannot discharge, because it is a sweep of the standards corpus and not an examination
of this document. **That step has not been run.** Under §1's rule the document could freeze today
with it outstanding; under §13's it could not. The first and last sections of the design do not
agree on the event the whole document is being driven toward.

**(b) The rule's trigger cannot see the thing most likely to change the document.** A review round
counts *defects*. `CONFORMANCE-B1-B106.md:20-30` records 37 UNADDRESSED and 22 PARTIAL obligations,
and task CONF-4 - *"Re-sweep the 37 UNADDRESSED obligations against the current design, before the
freeze decision"* - **is open and in progress right now.** An UNADDRESSED obligation is not a defect
and will never appear in a round's `Nc/Nh/Nm`. So the freeze rule can fire while the sweep whose
whole purpose is to say what the document still owes has not reported. **The design cannot
responsibly freeze ahead of its own conformance re-sweep, and the freeze rule does not know that.**

**(c) Most seriously: 0C/0H/0M does not mean §11's must-mitigate table is empty.** §11:1338-1344
lists three inherent Critical/High rows as **unmitigated** and requiring action before
implementation proceeds:

| Row | Rating | Action |
|---|---|---|
| C5-R1 | High | Log retries and breaker transitions with the correlation field (B39, B40) |
| C5-E1 | High | Document that a read-only Jobvite key is required where writes are disabled (B21) |
| C8-I1 | **Critical** | State the `.gitignore` policy and add `.env.example` (B90, B91) |

`threat-modeling.md:86` reads *"**Critical/High**: Must mitigate before implementation proceeds"*.
None of the four review rounds counted these as findings - they are correctly disposed, tracked and
visible, which is what a well-run threat model looks like. **But that means a 0C/0H/0M round is
compatible with all three still being open.** And every one of those three remedies is *an edit to
this document*: C5-E1's is a sentence in §4.1 or §10.1, C8-I1's is a `.gitignore` policy statement.
**Freezing puts three document edits the design itself mandates behind an ADR requirement.** That is
the wrong instrument, and it is the orchestrator's own stated doubt, confirmed with a mechanism.

**Remedy:** state the freeze rule as a conjunction rather than a single result - 0C/0H/0M **and**
§11's must-mitigate table empty **and** §13's conditional-dismissal re-test run **and** the
conformance re-sweep reported - and say explicitly what an ADR is *not* required for (typo fixes,
adding a §8 case a row already names, closing a tracked must-mitigate row with the text it
already specifies).

## MINOR

**m1. §6.2 miscounts what the corpus's `optional` files are.** `DESIGN.md:542-544`:

> "corpus-wide the only `optional` files are twelve README indexes, and no substantive standard is
> optional."

`grep -rln "^priority: optional"` returns twelve files, so the number is right. **Eleven are README
indexes. The twelfth is `architecture/adr/ADR-000-template-example.md`** (`:8` reads
`priority: optional`), an ADR worked example, not an index. The load-bearing half - no substantive
standard is optional - survives, since a template example is not a substantive standard. Fix the
noun, keep the conclusion.

**m2. `DESIGN.md:796` cites `§20.2` with no document named.** Every other bare `§N` in this document
means a section of this document, whose numbering stops at §13. `§20.2` is
`FASTMCP-SPIKE-4.md:2007`, *"MRTR is REFUTED on the handshake era"* - the content is correct and
supports the sentence. Compare `:1136`, which does it right: *"`JOBVITE-API.md` §0.2"*. Name the file.

**m3. §5.3 cites `agent-guardrails.md:121-123` for `approval_state` "explicitly".** `:121-123` reads
*"Log every tool invocation with: tool name, validated arguments (PII redacted), result status,
latency, the approval decision if gated, and the request correlation id."* The literal snake_case
token `approval_state` is at **`:129`**. The obligation is real at `:121-123`; the *name* is at
`:129`. Cite both, or drop "explicitly".

**m4. Emphasis added inside a verbatim quotation.** §2.2's `:70-73` block bolds *"outbound message
to a third party"*. The source does not bold it. The design's convention is to reproduce quotations
exactly; this one is edited inside the quote marks. Move the emphasis to the prose beneath, which
already makes the point.

**m5. The gate checks the Critical/High roster for exact equality and leaves the Medium
production-release list unchecked.** Check 6 compares the "Already mitigated at Critical or High"
roster to the set the tables imply and fails on any difference. The parallel list -
*"Mitigate before production release (inherent Medium, unmitigated)"* at `:1348-1352` - gets only
check 5's "these ids exist" treatment. **I hand-verified it is complete today** (C3-I1, C6-D1,
C8-R1, C9-D1 are the unmitigated Mediums; C7-I2 is listed and is `residual`). Recording it as an
asymmetry, not a live error: the argument for check 6 applies unchanged one band down.

---

# BLUE ROUND - Normal Response

**H1 - ACCEPT, in full, as a freeze blocker.** No defence. The escape was demonstrated by execution
against a temp copy rather than argued, it hits every row that names a test including all four
Criticals, and the disposition it exploits is one §11 defines only for unrated rows. The suggested
remedy is right and is about six lines. I would add one thing the finding does not: **the two new
controls must not use C4-E1**, the row R5 used, for the same reason R5 gives.

**H2 - ACCEPT.** The word "Machine-checked" is not supportable. Two dispositions were considered and
one is clearly better:

- Downgrade the wording to "hand-checked at R3, R4 and R5". Honest, cheap, and leaves the rating
  hole open.
- **Implement the check.** Chosen. It is nine lines, it is the check that would have caught the
  MUT-D rerating, and it converts the sentence from a claim into a column-and-script the same way
  §11 already did for coupling. Leaving the sentence as prose after this review would be the exact
  failure §11 documents itself as having made three times.

**H3 - ACCEPT.** Three edits, no new information needed. Note for whoever applies it: the §1.1
sentence is load-bearing beyond its own paragraph, because §1.1 is what a reviewer is told to
calibrate "verified" against, so this is not bookkeeping.

**H4 - ACCEPT (a) and (c). MODIFY (b).**

(a) and (c) are correct and I have no counter. The freeze rule as written is a single-clause rule
governing a multi-clause event, and (c) is the sharp end: three rows the design's own table calls
must-mitigate-before-implementation would, on freezing, need an ADR to close with text the design
already specifies.

(b) I modify only in emphasis. R5 is right that a review round's `Nc/Nh/Nm` cannot see an
UNADDRESSED obligation and right that CONF-4 is open. But an UNADDRESSED obligation is a *gap in
what the design speaks to*, and the correct instrument for closing one after a freeze may well be
an ADR - that is not obviously the wrong tool the way it is for (c). What is wrong is freezing
*before the sweep reports*, because nobody then knows which of the 37 are design gaps and which are
implementation gaps. **Accepted as a sequencing constraint rather than as a defect in the ADR
instrument.**

**m1 - ACCEPT.** One-noun fix.
**m2 - ACCEPT.** Name the file.
**m3 - ACCEPT.** Cite `:121-123` for the obligation and `:129` for the field name.
**m4 - ACCEPT.** Move the emphasis out of the quote.
**m5 - ACCEPT as a limitation, MODIFY as a finding.** Nothing is wrong today and R5 says so. It is
worth an issue, not an edit under review pressure; it goes in with H1's gate work or not at all.

**On the two concerns the gate's author nominated against itself:**

- **Concern 1 - REJECTED as stated, and the inverse is H1.** The claim was that the biconditional
  *"treats `no credible threat` as the only legitimate no-token state."* It does not.
  `NOT_MITIGATED_RE` is `residual | accepted | unmitigated`, and all three are legal no-token
  states - eight rows use them today. The feared failure - a genuinely mitigated row rated so low
  nobody writes a token - cannot arise either, because such a row's Test cell must read
  `not required (<rating>)`, and requiring the token there is the intended behaviour, not a false
  positive. **The author looked in the right place and read the sign backwards.** The real defect is
  that `no credible threat` is *missing* from `NOT_MITIGATED_RE`, which is the opposite of being
  privileged by it.
- **Concern 2 - VALIDATED, with a measurement.** The author's suspicion that it had chosen control
  subjects from the covered set is correct and consequential. Controls 16a and 16b use C1-S1 and
  C1-D1; control 14d uses C5-R1; control 15 uses C3-I1. All are rows the mutation they encode was
  designed around. An independent sweep that chose no subjects at all - all 19 x all 8 - found 19
  escapes in 152 runs. **The 21 controls did not miss the hole by bad luck; they could not have
  found it, because none of them substitutes the one disposition that opens it.**

---

# RED ROUND - Adversarial Rebuttal

Blue accepted everything material, so there is little to press. Two points, both unlocked by Blue's
own answers, and one concession.

**R-1. Blue's H2 remedy must not stop at the matrix.** Blue chose "implement the check", which is
right, but the chosen check computes Risk from L and I. It does **not** check that L and I are
themselves drawn from the ladders at `:62-74` - i.e. that each is one of `H`/`M`/`L` and not a
stray `Med`, `-`, or empty cell. A row with an empty Likelihood cell would make the matrix lookup
miss and, depending on how it is written, either crash or silently skip. Since the whole lesson of
FIX-8 is *the selector decided the check never ran*, the matrix check must **fail on a row it cannot
evaluate**, never skip it. Fold that into H2 rather than discovering it in Round 6.

**R-2. Blue's modification of H4(b) concedes the sequencing and leaves the rule silent about it.**
Blue agrees the design must not freeze before CONF-4 reports, and calls it a sequencing constraint.
A sequencing constraint that lives only in a review document is not a rule. §1's freeze rule is the
only place that survives into the frozen artifact, and Blue's own H4(a) accepts that §1 and §13
already disagree because the precondition lives in the wrong section. **If the CONF-4 dependency is
real, it belongs in §1's rule text with the other conjuncts.** Otherwise Round 6 inherits a
constraint nobody wrote down, which is precisely how §13's conditional-dismissal step came to be
needed.

**Conceded, and recorded because a round that concedes nothing is not adversarial:** I looked hard
for a defect in the eight rows the orchestrator tokenised by hand (his stated doubt #1) and **found
none.** The gate's biconditional now checks that population both ways over all 60 rows on every run
- forward (a row claiming a mitigation must carry the token) and reverse (a row carrying the token
may not dispose of itself as not-mitigated) - and I re-ran it: 60 rows parsed, zero violations. The
ad-hoc script that originally verified it has been superseded by a committed one. **That doubt is
closed**, and it is closed by machine rather than by my agreement.

I also found nothing wrong in the §8 required-case list's correspondence with the Test columns
beyond what H1 describes, nothing wrong in the risk arithmetic, nothing wrong in any of the 30-odd
standards citations beyond m1/m3/m4, and nothing wrong in the burst measurements R4 named as the
highest-value unopened target. **The document is in materially better shape than any prior round
found it.** That is not a reason to freeze it; it is the reason the four HIGHs are worth fixing
rather than arguing about.

---

# BLUE ROUND - Final Normal Response

**R-1 - ACCEPT.** Folded into H2. The matrix check fails loudly on any row whose L or I is not one
of `H`/`M`/`L`, and unrated rows (all three cells `-`) are the only exemption - which is the same
predicate H1 needs for `no credible threat`, so the two fixes share one helper. Good catch; it is
the FIX-8 lesson applied to the new check before the new check exists.

**R-2 - ACCEPT.** §1's rule text gets all four conjuncts, CONF-4's successor included, stated as
"the conformance sweep has reported against the current revision" rather than naming a task id that
will not mean anything in six months.

**On the concession:** recorded and welcome. It is the first round where the largest surface -
§11's 60 rows and their coupling to §8 - is guarded by something executable, and R5's own attack on
that guard is the strongest evidence yet that the guard is the right shape. H1 is a bug in a
mechanism that should exist, not an argument that it should not.

---

## Final report: every decision and why

| # | Finding | Section | Disposition | Why |
|---|---|---|---|---|
| H1 | `no credible threat` lets any row at any severity drop its §8 case; 19/19 §8-naming rows escape, all four Criticals included | `check-coupling.py` check 3 + `NOT_MITIGATED_RE`, against §11 convention 4 | **SURVIVES - freeze blocker** | Demonstrated by 152 executed mutations, not argued. Same class as FIX-8, worse instance. The freeze rule hands the coupling guarantee to this gate |
| H2 | §11 convention 3 claims "Machine-checked"; no machine checks ratings, and the gate disclaims it in writing | `DESIGN.md:1207` vs `check-coupling.py` docstring | **SURVIVES** | The arithmetic is right (verified 49/49) but the claim has no check, which is the exact failure §11 retired a sentence for eight lines below. Also the missing check is the one that closes the gate's declared rating hole |
| H3 | §1.1 says one unexecuted mechanism, §12 says two; the second (circuit breaker) has no marker, no Residual Risks row, and carries C5-D1's mitigation | `DESIGN.md:34` vs `:1413-1418`, `:277-280`, `:1276` | **SURVIVES** | A contradiction inside the paragraph that tells a reviewer how to read "verified" everywhere else |
| H4 | Freeze rule contradicts §13's freeze procedure, cannot see the open conformance sweep, and permits freezing with three inherent Critical/High rows unmitigated | `DESIGN.md:17-19` vs `:1456-1460`, `:1338-1344`; `threat-modeling.md:86` | **SURVIVES** | (a) and (c) accepted outright; (b) accepted as a sequencing constraint that must be written into §1's rule text, not left in a review |
| m1 | "twelve README indexes" - twelve optional files, eleven READMEs, one is an ADR template example | `DESIGN.md:542-544` | **SURVIVES** | False and checkable. Conclusion survives, noun does not |
| m2 | Bare `§20.2` is a cross-reference into `FASTMCP-SPIKE-4.md` with no document named | `DESIGN.md:796` | **SURVIVES** | Content correct, citation unresolvable within this document |
| m3 | `agent-guardrails.md:121-123` cited as naming `approval_state` explicitly; the token is at `:129` | `DESIGN.md` §5.3 | **SURVIVES** | Obligation lands, field name does not |
| m4 | Emphasis added inside a verbatim quotation | `DESIGN.md` §2.2 | **SURVIVES** | Convention violation, no factual error |
| m5 | Medium production-release list unchecked while the Critical/High roster is checked exactly | `check-coupling.py` check 6 vs `DESIGN.md:1399-1403` | **SURVIVES** | Verified correct today; recorded as an asymmetry to close with H1's gate work |
| - | Gate author's concern 1: "`no credible threat` is the only legitimate no-token state" | - | **REJECTED** | `residual`, `accepted`, `unmitigated` are all legal no-token states and eight rows use them. The sign is inverted: `no credible threat` is *missing* from `NOT_MITIGATED_RE`, which is H1 |
| - | Gate author's concern 2: control subjects chosen from the covered set | - | **VALIDATED** | Measured. 21 hand-picked controls, 0 found the hole; 152 subject-free mutations, 19 escapes |
| - | Orchestrator doubt 1: eight hand-tokenised rows verified by ad-hoc script | - | **CLOSED** | The committed gate now checks that population both ways on every run; 60 rows, 0 violations, re-executed this round |
| - | Orchestrator doubt 3: 37 UNADDRESSED obligations | - | **DEFERRED to CONF-4** | Open and in progress. Not re-swept here to avoid a duplicate verdict; it is H4(b)'s sequencing constraint |
| - | Orchestrator doubt 4: never read end to end | - | **ADDRESSED** | Read in one sitting. H3 and H4 are the yield, and neither is visible from a delta review |

**Surviving: 0c / 4h / 5m.**

## Freeze recommendation

**DO NOT FREEZE.**

**The reason, in one sentence:** the machine gate that the freeze rule makes the standing guarantor
of §11 does not enforce the property it exists to enforce for a single one of the nineteen rows
that name a test, and the freeze rule itself has never been specified well enough to say what
freezing requires.

Expanded:

1. **H1 is the disqualifying one.** Freezing means "only an ADR may change this", which is only
   safe if something mechanical holds the document's internal consistency afterwards. That
   something is `check-coupling.py`, and it currently green-lights the removal of every test
   reference in the threat model, Criticals included. Freeze after the fix and its controls, not
   before.
2. **H4 means the freeze event is not defined.** §1 and §13 disagree; the rule cannot see the
   conformance sweep that is open right now; and it permits freezing over three inherent
   Critical/High rows that `threat-modeling.md:86` says must be mitigated before implementation
   proceeds. A rule this consequential should be written before it fires, not after.
3. **H2 and H3 are cheap and belong in the same pass.** H2 is nine lines of Python that also closes
   the gate's own worst declared blind spot. H3 is three sentences.
4. **Nothing here needs a credential, a spike, or a design decision.** Every remedy is actionable
   today. This is the same shape R4 reported, and the document has genuinely converged - the
   round's yield is one real mechanism defect, one false mechanism claim, one internal
   contradiction, and a rule nobody wrote properly. That is a document close to done, not a
   document in trouble.

**What would make Round 6 a freeze round:** H1's fix plus two controls with subjects drawn from
outside the existing 21; H2's matrix check with R-1's fail-loud predicate; H3's three edits; H4's
rewritten rule; the five MINORs; CONF-4 reported; and §13's conditional-dismissal re-test run
against `devops/docker.md` and `backend/idempotency.md`. Round 6 should be a **re-check with a
fresh reviewer**, and it should re-run the 152-mutation sweep rather than trusting the controls,
because the controls are what missed this.

---

## What I did NOT review, and why

This section is the map for Round 6.

- **`FASTMCP-SPIKE-4.md` in full (~2350 lines). Fourth consecutive round to decline it.** I opened
  `:887-944` and `:1058-1102` (the rate-limiter arms, which R4 named as its first target) and the
  §20 heading map at `:1979-2334`. **Every number in §4.4 that I checked landed.** But §7.4's
  SIGTERM arms, §7.5's dual-era table, §5.1's "verified across five arms", §7.6's token spike and
  §7.7's middleware findings I did **not** open against their spike sections. `VER-1` and
  `SPIKE-CLAIM-AUDIT.md` exist and cover this ground; **I did not read either**, so I cannot say
  whether their corrections were fully applied. That is now the largest surface no round has
  examined directly, and it is Round 6's obvious first task.
- **`SPIKE-CLAIM-AUDIT.md`, `CITATION-AUDIT.md`, `CITATION-AUDIT-B1-B106.md`, `FIX-3-REPORT.md`,
  `CONFORMANCE-DESIGN-ARTIFACT.md`, `PENDING-CONFORMANCE-FIXES.md`, `THREAT-MODEL-DRAFT.md`.**
  Not opened. Deliberately, for two different reasons: the audits, because I wanted my citation
  checks to be independent rather than a re-read of somebody's verdicts, and I did re-derive
  ~30 citations from the standards files directly; the draft, for R3's and R4's stated reason.
  **The cost is real and specific: I cannot say which audit corrections landed and which did not,
  and `CONFORMANCE-DESIGN-ARTIFACT.md` is now a three-round gap - named in every brief, read by
  nobody.**
- **The 37 UNADDRESSED and 22 PARTIAL conformance rows as a set.** Not re-swept. CONF-4 owns it and
  is in progress; two independent verdicts on the same set would be worse than one. I read only
  `CONFORMANCE-B1-B106.md:1-55`. **This is why H4(b) is a sequencing finding rather than a
  content one - I am asserting the sweep must report, not what it will say.**
- **`STANDARDS.md` (1310 lines), `COMPLIANCE-SPEC.md` (661 lines), `JOBVITE-CONTRACT.md` (676
  lines), `DECISIONS.md`, `LICENSING-SURVEY.md`, `docs/adr/*.md`.** Not opened. **§13's ten ADRs
  are unread by me**, so every claim in §13 about what an ADR's *scope includes* - ADR-0002's
  three clauses, ADR-0006's B97/B99 split, ADR-0009's approver-only scoping - is **unverified
  against the ADR files themselves.** §13 is 40 lines of assertions about ten documents I did not
  open, and it is the section that governs what may change after the freeze. **That is a real gap
  and I would rank it second only to the spike.**
- **`standards/` beyond the eleven files listed at the top.** I did not sweep the corpus for
  obligations the design misses. In passing I noticed `readme-standard.md:64` (a 500-line README
  cap) and `:69` (*"a link checker MUST run in CI; a broken link blocks merge"*), neither of which
  appears in §10 or §10.1 - **I did not check whether either is already a B-number**, so I report
  them as unexamined rather than as findings.
- **§9's seven contract hazards against `JOBVITE-CONTRACT.md`.** Not checked. R4 flagged this and
  it remains a two-round gap.
- **Whether any §8 case is *adequate*.** The gate checks a case's text exists in §8; I checked the
  gate. **Neither of us checked that a named case would actually fail if its mitigation were
  removed**, which is what §8's own framing promises. That is unfalsifiable until code exists, and
  I say so rather than listing it as verified.
- **Anything requiring a live Jobvite call.** No credential, no sandbox. **No remedy above needs
  one.**
- **`src/` and `tests/`.** Empty. Correct for a design round.
