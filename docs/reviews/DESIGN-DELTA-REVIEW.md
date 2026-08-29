# DESIGN.md delta review - the 118 lines added after R7-CONFIRM

Reviewer: `design-delta-review`, fresh, author of none of this text.
Date: 2026-08-28 02:25 PM CDT.
Range reviewed: `git diff fe3e8b5..HEAD -- docs/DESIGN.md` at HEAD `9d65cc0` (118 insertions, 15
deletions, 4 commits: `f5c63e7`, `90b0504`, `f62733d`, `9d65cc0`).

## VERDICT: DO NOT FREEZE

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 2 |
| LOW | 1 |
| NIT | 1 |

The freeze rule is 0C/0H/0M **and** §11's must-mitigate table empty. The table **is** empty
(`docs/DESIGN.md:1790`, `*(none)*`), so the second condition holds. The first does not: this round
returns 2 HIGH and 2 MEDIUM.

Both HIGHs are the same shape and it is the shape the brief predicted: **four locally sound edits,
none swept against the rest of the document.** Neither is a defect in the new prose. In both cases
the new prose is right and an old sentence that says the opposite was left standing, so the document
now asserts a thing and its negation. Neither is visible to any of the three gates, because all three
check structure and none checks truth.

Nothing in the delta is a fabrication. Every citation I checked resolves and says what it is said to
say; every present-tense claim the delta *adds* is true of the repository as it actually is. The
defects are all sins of omission - siblings not swept.

## Gates, re-run by me from the repository root

| Gate | Result |
|---|---|
| `python3 docs/reviews/check-coupling.py docs/DESIGN.md` | **exit 0**. 60 STRIDE rows, 17 Critical/High, 23 naming a §8 case |
| `python3 docs/reviews/check-coupling-controls.py` | **exit 0**. **32/32 controls fired**, baseline green before and after |
| `python3 docs/reviews/check-coupling-sweep.py` | **exit 0**. 184 substitutions, 7 escapes all the designed Medium/Low exemption, **0 holes** |

The controls count matches the brief's stated 32/32. I did not take that on trust; the run is above.

## What I verified as TRUE (recorded so the next reviewer need not redo it)

Present-tense claims added by the delta, each checked against the repository:

- **No README exists.** `ls README*` -> no such file. §7.2's rewrite (`828-835`) and §8's gated arm
  (`1220-1223`) are therefore correct, and the gating is real, not a skip - control 20 and control 21
  both fire on an ungated nonexistent file.
- **No CI exists.** `.github/workflows/` holds exactly one file, `mirror.yml`. §10's correction
  (`1369-1375`) states this accurately.
- **No Dockerfile, no compose file, no image build.** `find` over the tree returns nothing. §13's
  `devops/docker.md` re-test (`1929-1931`) is accurate.
- **`backend/resilience.md:146-151`** says exactly what §2.2 says it says: *"Make a write retry-safe
  by guarding it with an **idempotency key** so the downstream dedupes the replay... Only then may
  the write be retried."* §2.2's reading of "the other branch of that clause" is faithful.
- **`ai/agent-guardrails.md:54-56`** and **`ai/tool-calling.md:108-111`** both say what §7.2's B107
  paragraph says they say, including the *"never off a value the model supplied"* wording quoted at
  `790-791`.
- **`importDuplicates` is on a different endpoint of a different product**, as §2.2 claims:
  `docs/research/JOBVITE-API.md:620` documents it in the `POST /v1/contacts` Contact Import body,
  and no idempotency field appears in the v2 candidate create body anywhere in the corpus.
- **Credential-checklist rows resolve.** Row 0 (`CREDENTIAL-CHECKLIST.md:45`) records the read-only-key
  question "either way", as §7.2 says. Row 9 (`:57`) is the rate observation §12 points at. Row 10
  (`:58`) is the `409` duplicate behaviour §2.2 points at.
- **`.env.example` carries both new variables and marks the guess.** `:62` `JOBVITE_MAX_RESULTS=50`;
  `:69` `JOBVITE_OUTBOUND_RATE_LIMIT=6` under the line **"THIS IS A CONSERVATIVE GUESS, NOT A VENDOR
  FIGURE"** with the checklist row 9 pointer. The brief's item 5 is satisfied: the guess is stated
  in both places, in the same terms, and neither reads as documented.
- **The `50` is consistent.** `showing 50 of 1,240` appears at `:447`, `:1132`, `:1467`, `:1640`.
  §12's justification for the default holds.
- **The new §8 case's count of three gaps is right.** `#4927` (`:898`), `os._exit(0)` (`:931`), and
  the uvicorn implementation detail at §12 item 5 all exist and all turn on teardown running.
- **§7.4 and the new §8 case do not contradict each other.** `:895` *"Lifespan teardown does not run
  under SIGTERM"* describes the framework default; `:926` installs the explicit handler; the case
  asserts the remedy. Correctly layered.
- **No prose count of §8 cases exists anywhere in the document.** §8 now holds 28 bullets; I looked
  for a stated total that the new case would have decayed and there is none. The brief's item 2 finds
  nothing to report - §11's "This table is the count" rule (`:1742`) has evidently already been
  generalised in practice.

---

# FINDINGS

Every suggested fix below is **MY SUGGESTION, to be verified before adoption.** I did not edit
`DESIGN.md` and did not commit.

## H1 - HIGH. C5-E1's Mitigation cell still asserts the README states the requirement, in the same row whose Test cell was fixed to say it does not

**Where:** `docs/DESIGN.md:1722`, the C5-E1 row of §11.

`f5c63e7` exists to remove the claim that a nonexistent README states the read-only-key requirement.
It corrected §7.2 (`828-835`) and it corrected C5-E1's **Test** cell, which now reads *"in the
README's deployment section once a README exists"*. It did not correct C5-E1's **Mitigation** cell,
four columns to the left in the same table row, which still reads:

> Where writes are disabled a read-only key is required, **stated in the README and the credential
> checklist.**

Present tense, about a file `ls README*` cannot find. This is the exact defect the commit was
authored to eliminate, surviving inside the row it was eliminating it from - and C5-E1 is a **High**
row, so it is the most-read cell of the most-scrutinised class of row in the document. A reader
checking whether the High residuals are honestly stated reads the Mitigation cell first.

No gate can see this. `check-coupling.py` parses the Mitigation column only for a status token and
for agreement with the Test cell; the two cells still agree that the row is mitigated, so the check
passes on a row whose two halves now describe different worlds.

**Suggested fix (MY SUGGESTION):** in `:1672`, replace *"stated in the README and the credential
checklist"* with:

> stated today in `docs/CREDENTIAL-CHECKLIST.md` row 0, and required of the README's deployment
> section once a README exists (§7.2, §10.1)

**Then grep the subject, not the instance.** `grep -n "README" docs/DESIGN.md` returns 18 hits; I
checked all of them and this is the only surviving false present-tense one, but that check should be
repeated after the fix rather than trusted from this review.

## H2 - HIGH. Two §11 rows and a §11 closing list still say the result-cap default is undocumented, which §12 in this same delta made false

**Where:** `docs/DESIGN.md:1690` (C3-I1), `:1683` (C6-D1), `:1775-1776` (the "Mitigate before
production release" list).

`9d65cc0` names `JOBVITE_MAX_RESULTS`, defaults it to 50, puts it in `.env.example` (verified at
`.env.example:62`), and states at `:1477` that this **"closes B15's blocking half"**. Three places
outside the delta still assert the opposite:

- `:1640` C3-I1 Mitigation: **"The default is still undocumented (B15)"**, disposition
  `unmitigated (B15)`
- `:1683` C6-D1 Mitigation: **"The default is still undocumented (B15)"**, disposition
  `unmitigated (B15)`
- `:1775-1776`: *"**Mitigate before production release** (inherent Medium, unmitigated): C3-I1 and
  C6-D1 the undocumented result cap (B15)..."*

The sentence "The default is still undocumented" is now simply false, and it is doing load-bearing
work: it is the **stated reason** both rows are dispositioned `unmitigated`, and the stated reason
both appear on a release-gating list. The residual §12 actually leaves open is a different thing -
*"whether either default is right"* (`:1478`) - which is a question about the value, not about
documentation, and which may or may not justify the same disposition.

This does **not** block the freeze by the letter of the rule: the must-mitigate table is empty, and
the production-release list is a separate object. It blocks it by returning a HIGH. I am rating it
HIGH rather than MEDIUM because §11 is the artifact the freeze rule points a reader at, and three of
its cells now state a fact this delta falsified.

I am deliberately **not** asserting that the rows should now flip to mitigated. That is a
disposition decision with gate consequences (a mitigated Medium row must name a §8 case or carry
`not required (Medium)`), and it is the editor's call, not mine. The finding is the false sentence.

**Suggested fix (MY SUGGESTION):** in both `:1640` and `:1683`, replace *"**The default is still
undocumented (B15)**"* with:

> **The default is now named and shipped - `JOBVITE_MAX_RESULTS=50` in `.env.example` (§12) - and
> what remains open is whether 50 is the right value, which only a live tenant settles (B15).**

and in `:1775-1776` replace *"the undocumented result cap (B15)"* with:

> the result cap whose default is shipped but unvalidated against a live tenant (B15)

**Then re-run all three gates**, because the disposition cells are what `check-coupling.py` reads and
a wording change adjacent to them is exactly where a selector silently stops matching.

## M1 - MEDIUM. The CI disclaimer's selector is narrower than the defect it disclaims, and the sentence 13 lines below it was not corrected

**Where:** `docs/DESIGN.md:1419-1425` (the disclaimer), `:1390` (the uncorrected sibling), plus
`:944`, `:1139`, `:1205`, `:1513`.

The disclaimer is exactly right about the fact and it is well placed as a single statement. Its
problem is its own wording:

> every **"CI runs"** sentence in this document is a specification of what the pipeline must do

That is a literal selector, and the document's present-tense CI claims are not all of that form.
`:1377` was converted to *"CI **must** run"*. Thirteen lines later, `:1390` still reads **"CI also
runs: lint, format, types, tests, plus `pip-audit`, CodeQL, TruffleHog..."** - the sentence directly
continuing the one that was corrected, left in the reporting tense inside the same section, four
paragraphs below a disclaimer whose stated scope arguably does not reach it. Others the literal
selector misses:

- `:944` *"closes both gaps on the first CI run"*
- `:1139` **"CI has **zero skips**"** - a flat present-tense assertion about a pipeline that has
  never run, and the one most likely to be quoted as evidence of rigour
- `:1205` *"the same lock CI installs"*
- `:1513` *"CI exercises all of it"*

This is the "partial check selects for the form it cannot see" pattern: the cheapest way to satisfy a
disclaimer that names one string is to leave every sentence not matching that string alone.

**Suggested fix (MY SUGGESTION):** two parts.

1. Broaden the selector. In `:1369-1370`, replace *"every "CI runs" sentence in this document is a
   specification"* with:

   > every sentence in this document that describes CI in the present tense - "CI runs", "CI also
   > runs", "CI has", "CI installs", "CI exercises" - is a specification of what the pipeline must
   > do, not a report of what it does.

2. Correct the adjacent sibling regardless. In `:1390`, replace *"CI also runs:"* with **"CI must
   also run:"**, so the two sentences either side of the correction do not disagree about tense.

## M2 - MEDIUM. The two new expiring disposals are not enrolled in the only procedure that re-tests expiring claims

**Where:** `docs/DESIGN.md:835-839` (B107's ceiling), `:246-248` (B108's ceiling), `:1934-1937`
(§13's re-test step).

Both new disposals expire on a condition, and both say so - which is the right instinct, and B107's
paragraph argues the point explicitly at `:815-817`: without a written trigger *"this paragraph rots
silently on the day the assumption changes, which is precisely how the conditional dismissal of
`backend/idempotency.md` went unnoticed."*

The remedy `f62733d` then built for that exact rot is §13's new numbered step (`:1934-1937`):

> Whoever performs the freeze runs the re-test and records the outcome for **each conditional
> dismissal**, standing or tripped.

"Conditional dismissal" is that section's term of art for a dismissal **in the standards analysis
register**. §13 is where that register's dismissals live; B107 lives in §7.2 and B108 in §2.2, and
neither is a register entry. So the two disposals whose whole argument is that an unswept expiring
claim rots silently are themselves outside the sweep, and the procedure that has *"now failed twice"*
(`:1935`) would not catch them a third time.

The two triggers are also not equally observable, which the brief asked about:

- **B108's is observable and owned.** It expires when *"a credential or Jobvite documentation shows a
  dedupe key exists"*, and checklist row 10 (`CREDENTIAL-CHECKLIST.md:58`) is a step someone will
  actually run against a live tenant.
- **B107's first limb is observable by nobody.** *"If Jobvite ever exposes per-user or multi-tenant
  scoping"* names no document, no checklist row and no moment at which anyone looks. No checklist row
  probes Jobvite's permission model; row 0 asks only about read-only keys. Its second limb - *"a
  deployment is ever configured with more than one company id"* - **is** observable, in
  `JOBVITE_COMPANY_ID` (`.env.example:27`), and is the honest half.

**Suggested fix (MY SUGGESTION):** two parts.

1. Widen §13's step. In `:1936-1937`, replace *"records the outcome for each conditional dismissal,
   standing or tripped"* with:

   > records the outcome for each conditional dismissal **and for each disposal elsewhere in this
   > document that states a condition which voids it - B107 in §7.2 and B108 in §2.2 today** -
   > standing or tripped.

2. Give B107's first limb an observation point. Append to `:815`:

   > **Checklist row 0 is where this is asked**: the same conversation that establishes whether
   > Jobvite issues a read-only key records whether Jobvite exposes per-user or multi-tenant scoping
   > at all, since both are questions about the same permission model and only Jobvite can answer
   > either.

   If that is adopted, `docs/CREDENTIAL-CHECKLIST.md` row 0 must be widened to actually ask it -
   otherwise the pointer is the same unobservable sentence with a citation bolted on.

## L1 - LOW. "582 lines away" was wrong when it was written and is more wrong now

**Where:** `docs/DESIGN.md:854`.

> it asserted the README stated this while §10.1, **582 lines away**, deliberately withholds the
> README

Measured: the sentence is at `:832` and `### 10.1 Documentation deliverables` is at `:1431`. The
distance is **599**. At the commit that introduced the number, `f5c63e7`, the sentence was at `:775`
and §10.1 at `:1359` - a distance of **584**, so it was already off by two the moment it was typed,
and the §8 case added by `9d65cc0` between the two points has since widened it by seven more.

The number is doing no work the section reference does not already do, and it decays on every edit
that lands between §7.2 and §10.1 - which is most of the document. This is a derived record that
nothing re-checks.

**Suggested fix (MY SUGGESTION):** in `:832`, replace *"while §10.1, 582 lines away, deliberately
withholds the README"* with:

> while §10.1, most of a document away, deliberately withholds the README

Dropping the figure keeps the rhetorical point - that the two statements are far enough apart for
nobody to have noticed - without minting a number that will be wrong again by the next commit.

## NIT1 - Two consecutive blank lines at the end of the B107 paragraph

**Where:** `docs/DESIGN.md:840-841`.

`90b0504` left a doubled blank line between the end of the B107 block and *"**The outbound Jobvite
credential is a separate question...**"*. Cosmetic, invisible in rendered Markdown, and the only such
pair introduced by the delta.

**Suggested fix (MY SUGGESTION):** delete line `819`.

---

## OUT OF SCOPE, NOT ASSESSED

Everything in `docs/DESIGN.md` outside `git diff fe3e8b5..HEAD`, and every other file in the
repository except where it was read as evidence against a delta claim (`.env.example`,
`docs/CREDENTIAL-CHECKLIST.md`, `docs/research/JOBVITE-API.md`, `.github/workflows/`, the three
standards files cited above); the four commits in the range that do not touch `DESIGN.md`
(`b7844eb`, `b9cb611`, `c01966a`, `7d54baf`, `730181c`) were not reviewed.
