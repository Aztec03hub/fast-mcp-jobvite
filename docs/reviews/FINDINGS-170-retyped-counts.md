# FINDINGS #170 — the retyped-count container, measured

<!-- REVIEW-COVERS: e845839..1cddd76 PATHS: docs pyproject.toml CONTRIBUTING.md .github/workflows -->

**Measured at `1cddd76` unless a line says otherwise.** The census tool
is `docs/reviews/probe-170-retyped-counts.py`, committed on this branch;
every number below is reproducible by running it. **DO NOT PUSH** — a CI
run was in flight when this was written and nothing here has been pushed
or merged.

## §0 — THE CONTAINER, BEFORE ANY FINDING

Nobody had this number. Here it is, at `d30f1e1` (this branch, one
commit after `1cddd76`; the tool's own file adds candidates, which is
disclosed rather than hidden):

| Stage | Count | Files |
|---|---|---|
| tracked files | 485 | — |
| skipped as binary/unreadable | **0** | — |
| number-beside-plural adjacencies | **20,566** | 470 |
| …whose noun is ENUMERABLE | **6,762** | 432 |
| …of those, inside a DATED RECORD | **4,401** | — |
| …**LIVE, and therefore checkable** | **2,361** | **298** |
| …of those carrying a QUANTIFIER (`all`/`every`/`none`/`only`/`both`/`no`) | **530** | — |
| …of those whose noun is a GLOB, so the true figure is MECHANICAL | **28** | — |

**The last row is the one that got fully derived.** A glob names a set by
construction, so `--derive` counts the tracked files it matches and
compares. Every other noun needs a human to say which set it names, and
2,361 sentences is not a night's reading — so §2's coverage is stated
honestly in §5 rather than implied.

**Population by kind, never by path** (#115). The tool reads every
tracked text file: BASH-1 lived in a markdown table cell, #116's figures
lived in shell comments and Python docstrings, and `pyproject.toml`
below is a TOML comment. A `docs/*.md` filter would have found none of
those three.

### The zero was a finding about my selector, twice, and once it mattered

**THE FIRST VERSION MISSED A LIVE THREE-NUMBER FINDING IN ITS OWN
MOTIVATING FILE.** `docs/OBLIGATIONS.md:161` hard-wraps `13 of the 15`
onto one line and `` `scripts/*.sh` exceed 100 lines `` onto the next. A
line-based scan cannot see the pair. Joining each line with its
successor moved the LIVE container **1,960 → 2,361**: the first census
understated itself by 19% and reported nothing about the file BASH-1
came from. That case is now self-test arm 8.

Two more selector faults, each of which returned a **plausible wrong
noun** rather than none — the dangerous kind:

- a lazy noun regex truncated `assertions` to `as` and
  `` `scripts/*.sh` `` to `scripts`;
- a greedy one truncated the same glob to `scripts/*.s`.

And one that produced a **clean zero that explained itself**: accepting
any token with `/` and `*` as a glob admitted `6/min**` and `L/I.**` —
markdown bold read as a path — each deriving a confident population of
**0**.

15/15 self-test arms pass, and all three historically measured instances
(#116, #166, BASH-1) are planted and required back.

## §1 — TWO INSTRUMENTS DISAGREE ABOUT `scripts/*.sh`, AND IT IS NOT ROUNDING

Before any finding that cites this glob:

    git ls-files -- 'scripts/*.sh'   ->  39
    shell / PurePosixPath glob       ->  38

A git pathspec wildcard **crosses `/`**, so it admits
`scripts/lib/harness-result.sh`; a shell glob does not. BASH-1's own fix
at `d0bdf2a` counted **39** and named that file as one of them, so git's
reading is the one this repository means. `--derive` prints both
whenever they differ, because a glob whose population depends on which
tool reads it should not have a side picked for it silently.

## §2 — FINDINGS, in the three classes the brief names

### Class B — stale AND the surrounding claim is false. Rewrite the claim, do not swap the digit.

---

**F1 (HIGH) — `docs/DESIGN.md:2063` and `:2067`: "all eleven ADRs" / "eleven ADRs", against 33.**

Derived at `1cddd76`: `git ls-files 'docs/adr/0*.md'` → **33**.

This is #166's exact finding, in the document the two files it fixed
both describe. #166 corrected `docs/README.md:22` and
`docs/adr/README.md:7` — **both verified clean here, see §3** — and did
not reach `DESIGN.md`, which says it twice.

**AND THE WORD "all" IS FALSE INDEPENDENTLY OF THE NUMBER, which is why
replacing 11 with 33 is the wrong fix.** `:2063` claims recording a
deviation from a `priority: required` standard "is the job all eleven
ADRs below do". It is not the job of all of them: ADR-0019, ADR-0021,
ADR-0028, ADR-0029, ADR-0031 and ADR-0033 record design defects,
rulings and published vocabularies, not standards deviations — and
`docs/adr/README.md` itself now distinguishes `Deviation` from
`Design change` as two `Type:` values. A cell reading "all 33 ADRs"
would still claim every member is a deviation, which is the same
mistake BASH-1 made.

**Suggested fix — and it needs an ADR, because `DESIGN.md` is FROZEN**
(freeze `5d17cd7`; the working tree blob `639f4b7` was verified
identical to the freeze blob before reading). Proposed ADR text for §13:

- `:2063` → "This is the job of the `Deviation` ADRs below, and it has
  **nothing to do with the freeze**."
- `:2067` → "That is why `Deviation` ADRs exist against a document that
  is not frozen…"

No count in either. That is #166's ruling — delete the number, do not
replace it with today's — applied to the third and fourth sites.

---

**F2 (HIGH) — `docs/OBLIGATIONS.md:161-162`: "13 of the 15 `scripts/*.sh` exceed 100 lines; the largest is 469."**

Derived at `1cddd76`:

    tracked `scripts/*.sh`                 39 (git) / 38 (shell glob)
    ...of those, over 100 lines            38
    the largest                            598  (scripts/check-u1-boot-amputation.sh)

**Three numbers stale in one sentence, in the same file as BASH-1, about
the same population, fifteen lines below the row `d0bdf2a` had just
fixed.** The section it heads exists to weigh `bash.md:799` honestly, and
it currently weighs it against a population less than half the real one.

The `13 of 15` framing also carries an implied claim that **two members
are under the guideline**. Today the exception is **one**, and it is
**`scripts/check-suite-floor.sh` at 66 lines**.

**THIS SENTENCE FIRST NAMED THE WRONG FILE, AND THE MISTAKE IS THE ONE
THIS WHOLE TASK IS ABOUT.** It said `scripts/lib/harness-result.sh` —
reasoned across from BASH-1's own cell, which names that file as the
legitimate exception to the `set -uo pipefail` rule. **It is a different
rule.** `harness-result.sh` is 175 lines and is comfortably OVER the
100-line guideline; being outside one rule buys nothing from another.
Corrected by Tier 0's independent re-derivation and re-verified here:
`git ls-files 'scripts/*.sh'` piped through `wc -l` returns exactly one
member at or under 100, and it is `check-suite-floor.sh`.

**A claim inherited from a neighbouring sentence instead of derived is
the same defect as a count retyped from a neighbouring commit** — and
`--derive` could not have caught it, because it derives glob POPULATIONS
and this was a claim about a per-member PROPERTY with no derivation
behind it at all. The headline figures either side of it (39 tracked, 38
over, largest 598) were derived and all held.

**Suggested fix — REWRITE, no count retyped** (this file is not mine to
edit; §B of the brief reserves it):

> **`devops/bash.md:799` - ">100 lines of logic - rewrite in Python or
> Go". Nearly every tracked `scripts/*.sh` exceeds 100 lines — derive it:
> list them with `git ls-files 'scripts/*.sh'` and count those whose
> `wc -l` exceeds 100. Do not assume the exception is the file BASH-1
> names: that row is about `set -uo pipefail`, a different rule, and its
> exception `scripts/lib/harness-result.sh` is 175 lines.**

Landed by Tier 0 at `30be0ce` (local, held), re-derived rather than
transcribed from this report — which is how the wrong file above was
caught.

---

**F3 (MEDIUM) — `pyproject.toml:345`: "the file count moves 96 -> 105 and there are exactly 9 `scripts/*.py`".**

Derived at `1cddd76`:

    tracked `scripts/*.py`                       14 (git) / 13 (shell glob)
    mypy `files` population, without `scripts`   122
    mypy `files` population, with `scripts`      136

All three numbers are stale and `exactly` is the quantifier that makes
it a claim rather than an estimate.

**But the digits are LOAD-BEARING EVIDENCE, not decoration:** `105 - 96
= 9` is the arithmetic that justifies adding `"scripts"` to
`tool.mypy.files`. Swapping in today's figures breaks nothing about the
argument and everything about its tense — the measurement was made once,
at a commit, and was correct then. **The remedy is tense, not
arithmetic.**

**Suggested fix** — one word, preserving the internal consistency:

> `MEASURED BOTH WAYS AT THE TIME, because a nine-file addition
> reporting ZERO errors under `strict = true` was a suspiciously clean
> number. The file count moved 96 -> 105, the size of `scripts/*.py`
> then; …`

### Class A — merely stale. Delete the number, or derive it.

---

**F4 (MEDIUM) — `CONTRIBUTING.md:219`: "There are 847 `DESIGN.md:N` citations across 82 files".**

Derived at `1cddd76` **by this repository's own checker**,
`python3 docs/reviews/check-design-citations.py`:

    1988 DESIGN.md citations across 216 files

**Tier 0 read 1987 across 215 on the main checkout, and that is the SAME
measurement, not a disagreement**: this branch carries one file the main
checkout does not — the census tool itself, which quotes a citation.
Recorded because two instruments differing by one is exactly the shape
that should be explained rather than averaged, and Tier 0 used its own
figure when it landed the fix.

Stale by 2.3x in both figures. This sentence is live guidance: it is the
argument a contributor reads to decide whether skipping the repointer
matters. Understating it by 1,141 citations argues the wrong way.

**Suggested fix — derive, do not retype**, exactly as `CONTRIBUTING.md`
already does for the harness list twenty lines above it:

> **The count is deliberately absent — derive it, because it moves with
> every edit:** `python3 docs/reviews/check-design-citations.py` prints
> the inventory. A five-line insertion moves most of them, so an edit
> that skips this ships hundreds of wrong citations.

---

**F5 (LOW) — `.github/workflows/ci.yml:1143`: "18 checkers, 16 wired".**

Derived at `1cddd76`: `docs/reviews/check-*.py` → **24**; and the
container that comment's own subject now uses is **130 members, 71
wired** (#153's widening). Not mine to edit — reported for Tier 0.

**Suggested fix:** make it past tense and name the sha —
"found by enumerating `docs/reviews/check-*.py` against this file at the
time: 18 checkers, 16 wired" — or drop both digits and point at
`check-checkers-are-wired.py`, which now prints the live figure.

---

**F6 (LOW) — `docs/reviews/check-checkers-are-wired.py:63`: "33 of the 34 probes here are unwired".**

Derived at `1cddd76`: `probe-*` in that file's own container
(tracked `.py`/`.sh` under `docs/reviews/` and `scripts/`) → **38**.

The number is inside the bullet explaining #155's finding, so it is
arguably a record of what #155 measured — but it sits in a live
docstring with no date, in the file whose entire subject is that a
container grows. **Suggested fix:** "`probe-*` was never in the
population, so nobody was ever ASKED for a reason — at the time, 33 of
34 probes here were unwired."

---

**F7 (LOW) — `docs/reviews/probe-wired-checker-amputation.py:38`: "23 Python probes".**

Derived at `1cddd76`: `docs/reviews/probe-*.py` → **24**. Stale by one.
It is the size of a container the file's ruling declines to widen into,
so the digit does real work in the argument. **Suggested fix:** "Widening
that container to the Python probes here would be a large unasked sweep".

### Class C — inside a DATED RECORD. Correct as written, LEFT ALONE.

Recorded so they are visibly considered rather than overlooked. #166
measured this distinction and deliberately left `REPORT-147` §6's stale
13 in place; the same ruling applies.

| Site | Claim | Today | Left alone because |
|---|---|---|---|
| `docs/briefs/HANDOFF-2026-09-01-orchestration.md:52` | "Only 4 of 28 `docs/reviews/probe-*` files are wired" | **37** tracked; and task #155 records the truth as **1 of 30** | a dated handoff. It was already known wrong on its own date, which is exactly what a record preserves |
| `docs/briefs/HANDOFF-2026-09-01-orchestration.md:185` | "(24 of 28 probes)" | 37 | same record |
| `docs/reviews/COMPLIANCE-SPEC-PASS.md:260` | "`docs/` holds 8 research documents, 16 ADRs, 24 review documents" | 7 research `.md`, 33 ADRs, 147 entries under `docs/reviews/` | a dated conformance pass |
| `docs/reviews/DESIGN-DELTA-REVIEW.md:37`, `DESIGN-FREEZE-REVIEW.md:26` | "32/32 controls fired", "34/34" | superseded by later rounds | review documents; each records one run |
| `docs/DESIGN.md:1615` | "the conformance sweep found eleven consecutive documentation obligations unaddressed" | — | a past sweep's RESULT stated in the past tense, and `fourteen README sections` beside it is the STANDARD's number, not this repo's |

### Class D — a historical justification inside a LIVE file. RULED AND ADOPTED.

**Tier 0 ruled this class in, as framed.** It is neither a dated record
nor a plain stale count: the file is load-bearing and undated, but the
number is **evidence for a decision already taken**, so swapping the
digit falsifies the argument it supports. The remedy is **TENSE** — say
when it was measured — a fifth remedy distinct from delete, derive, and
rewrite-the-claim. **F3, F5, F6 and F7 are class D and take it.**

### RULING — `docs/briefs/` IS NOT a dated-record class

Tier 0 ruled, on a precedent already on the books: `check-review-coverage.py`
refuses `docs/briefs` as a RECORD path **by name**, because a brief
INSTRUCTS an agent and has carried substantive rulings. One ruling, one
place — briefs are not records for one tool and records for another. The
conservative default this tool already used is therefore correct and
stays: `RECORD_PREFIXES` does not admit them.

**THE TWO RULINGS COMPOSE, and that is what settles the 41 brief
candidates:**

- a count in a brief **already dispatched and completed** is **class D**
  — true at dispatch, and it justified a decision since taken. Tense,
  not correction.
- a count in a brief **still live and still steering an agent** is
  **class A** — derive it or delete it.

That is the rule to apply to the `docs/briefs/` remainder, and it is
sharper than either ruling alone.

## §3 — CHECKED, AND FOUND CORRECT

Named because a findings list that only lists failures says nothing
about how hard it looked.

- **`docs/README.md:22`** — #166's "Eleven decision records" is **gone**;
  the cell now reads "The decision records". The fix holds at `1cddd76`.
- **`docs/adr/README.md:7`** — #166's "eleven ADRs" is **gone**; the
  clause now reads "that is why the ADRs exist". Holds.
- **`docs/README.md:25` "Seven reports"** — #166 cleared this and it is
  **still right**: `docs/research/` holds exactly 7 `.md` files
  (COMPLIANCE-SPEC, FASTMCP-SPIKE-4, FASTMCP, JOBVITE-API,
  JOBVITE-CONTRACT, LICENSING-SURVEY, STANDARDS) plus 15 fixtures.
- **`docs/README.md:26` "Six further gates"** — **still right**, and it
  is self-enumerating: it names all six (design-freeze blob, no-errexit,
  row-floor exactness, row-floor firing, citation-shape scan,
  settings-are-read), so it can be checked by reading.
- **`docs/OBLIGATIONS.md:146` (the BASH-1 cell itself)** — the
  `--derive` pass flags "all 20 `scripts/*.sh`" here. **It is a
  QUOTATION** of the text `d0bdf2a` removed, inside the sentence
  explaining why it was wrong. Correct as written; a scanner cannot tell
  a quotation from a claim and this one should not be "fixed".
- **`docs/reviews/check-row-floor-exactness.py:201`** — flagged as
  "CLAIMS 5 against 39". **False positive**: the 5 is `ROW_FLOOR=5` from
  the neighbouring clause, and "Enumerating `scripts/*.sh`" carries no
  count at all. Nothing to fix.
- **`docs/reviews/lib/harness-state.sh:25` and
  `docs/reviews/restore-stranded-mutation.sh:33`** — "every
  `scripts/check-*.sh` writing its own state". **Correct**: a statement
  about a hypothetical future change, carrying no population claim. 36
  tracked members today, and the sentence would still be true at any
  number.
- **`docs/adr/0023:130` "only in `scripts/*.sh`"** — **correct**: a scope
  statement, not a count.
- **`docs/briefs/BRIEF-156-u1-boot-unguarded.md:44` "the other 36
  `scripts/*.sh`"** — 39 tracked, the brief owns 1
  (`scripts/check-u1-boot-amputation.sh`), so the arithmetic wanted 38.
  **Reported as a nit only**: it is a dispatch document, dated, and its
  purpose (do not touch scripts you do not own) is unaffected.

## §4 — WHERE THIS BRIEF WAS WRONG

1. **§A says to cut the worktree "from `origin/main`", and the command it
   gives has no start-point** — so it branches from local `HEAD`.
   Branching from `origin/main` would have been **wrong**: `d0bdf2a`,
   the worked example §A tells you to read, is one of the three
   local-only commits and is not on `origin/main`. The command is right
   and the sentence above it is not. Fix: delete "from `origin/main`".
2. **§A's canon list omits `docs/briefs/PREAMBLE.md`**, which
   `PROTOCOL-sub-orchestrators.md` §1 makes the *first* thing a Tier-1
   brief must order. It carries the evidence standards, the
   derive-the-freeze-SHA rule and the delivery protocol. Fix: add it as
   item 0.
3. **§C says BASH-1 measured "39 tracked, 37 with the option".** True,
   but `39` is only true under `git ls-files`; a shell glob gives 38.
   §E asks every count to carry its container — it should also carry its
   **instrument** when the two disagree (§1).
4. **§E's suite figure (887 passed, 0 skipped) was RIGHT** — measured,
   not assumed. Reported because a correction list that only lists
   errors is its own kind of stale claim.
5. Task #170's description is dated `2026-09-02` and `d0bdf2a` is
   authored `Tue Sep 1 22:29:48 2026 -0500`. Not acted on; noted so the
   next reader is not confused by a future-dated raise.

## §4b — SECOND SWEEP: the floor and tally nouns, and the answer is CLEAN

Dispatched by Tier 0 as the highest-value remainder, on the reasoning
that `rows`/`arms`/`controls`/`citations` are where this project's floors
live and **a stale one there is a floor carrying slack**. Measured at
`b0040fd`.

**The four nouns hold 619 live candidates** (`rows` 303, `arms` 190,
`controls` 69, `citations` 57). Reading 619 sentences is not the answer;
the answer is that a sub-class of them has a **mechanical derivation
nothing in the tree currently reads.** `check-row-floors.py` compares a
harness's internal `ROW_FLOOR` against `ci.yml`'s `--min-rows`, and
`check-row-floor-exactness.py` compares the floor against the table.
**Neither reads the PROSE.** So `--tallies` was built to compare a
docstring's claimed count against the floor declared in the same file.

**RESULT: 17 prose tallies in 11 files, and NOT ONE IS STALE.**

- 10 agree exactly with their file's own `ROW_FLOOR`.
- 7 differ, and **every one of the 7 is a dated narrative** — a class D
  sentence already carrying the remedy class D prescribes. The largest
  delta, `scripts/check-u7-resilience-controls.sh:557`, claims 26 against
  `ROW_FLOOR=31` and says so itself: *"this harness printed '26/26
  controls fired.' at 2b31e82, and that number went five rows stale
  WITHOUT FAILING ANYTHING"*, then re-derives 31 two ways. Verified
  independently: `grep -cE '^mutate "'` returns **31**, matching the
  floor.

**SO THE HARNESS FAMILY ALREADY APPLIES THE CLASS-D REMEDY, SYSTEMATICALLY.**
That is the finding. The class Tier 0 ruled in was not invented for this
report — the harnesses had converged on it independently, and the four
documents in §2 are where it has not reached.

### The zero is proved non-vacuous, and two false-positive classes were killed first

**An empty finding list is a claim about the selector.** So:

- **POSITIVE CONTROL (self-test arm 19):** a synthetic stale
  `26 controls` is planted against `check-u7-resilience-controls.sh`'s
  real floor and **must come back as `(floor 31, claimed 26)`**. It does.
  The plant is synthetic rather than a tree mutation deliberately — a
  harness that edits its own repository has to prove it restored, and
  this proves the same property with nothing to restore.
- **NEGATIVE CONTROL (arm 20):** a file declaring no `ROW_FLOOR` yields
  **no tally**, rather than a `0` that would read as agreement.

And the first two runs of `--tallies` were **wrong in the alarming
direction**, which is why the clean result is only reportable now:

1. **38 tallies, of which 14 were shell positionals.** `local
   label="$1" file="$2" old="$3" new="$4"` sits one line above
   `ROWS=$((ROWS + 1))` in nine amputation harnesses, so `$3` and `$4`
   were read as "3 rows" and "4 rows" against floors of 14 and 20 —
   deltas of −17 and −16, the top of the sorted list, every one a
   variable.
2. **Then 24, of which 7 were assignments.** `ROWS=0` beside `APPLIED=0`
   read as a claim of "0 rows"; worse, **`ROW_FLOOR=15` was read as a
   claim about the very floor it defines** — the instrument agreeing
   with itself, which is the one agreement that proves nothing.

Both are now self-test arms (16, 17, 18). **Had I reported the first
run, I would have filed fourteen findings against nine harnesses that
are all correct** — the mirror image of the wrap defect in §0, and in the
more damaging direction.

## §5 — WHAT I COULD NOT SETTLE (separate from what I did not attempt)

**COULD NOT SETTLE:**

- **Whether `docs/briefs/` is a DATED RECORD class.** It has the
  properties of one (dated, superseded, a snapshot of what was known at
  dispatch) and it is not in #166's enumerated list. 41 LIVE candidates
  sit in `docs/briefs/`, and the answer moves them all between class A
  and class C. **This is a Tier-0 ruling, not mine.** The tool's
  `RECORD_PREFIXES` currently does NOT treat them as records, so the
  container above counts them as live — the conservative direction.
- **`docs/OBLIGATIONS.md:21-23`: "Of the twelve obligations CONF-6 found
  **met**, exactly **one** — B58 — … The other **nine** are met by
  accident."** `1 + 9 = 10`, not 12. This is not staleness against a
  container — it is internally inconsistent as written, and I cannot
  tell from this repository whether CONF-6 found 10 or 12, because the
  audit it cites (`CONF-6-PROPAGATION-AUDIT.md`) is the record and
  correcting a record is exactly what class C forbids. **Needs someone
  who can read CONF-6's tally.** Flagged rather than guessed.
- **`docs/OBLIGATIONS.md:181`: "3374 lines of amputation-verified
  harness".** Derived: all tracked `scripts/*.sh` total **13,760** lines;
  the 16 matching `scripts/*amputation*.sh` total **5,967**. 3,374
  matches neither, and I could not reconstruct which container it named
  when written.
- **`docs/OBLIGATIONS.md:94`: "the 28 open obligations"** against 31 table
  rows today. The sentence says "Seeded from CONF-6's population", which
  may make 28 correct as a description of the SEED rather than the
  table. I could not settle which without CONF-6's own tally, same
  blocker as above.

**NOT ATTEMPTED, and stated so it is not mistaken for an absence:**

- **`citations` (57 live) was NOT swept.** It was in Tier 0's list of
  four and `--tallies` does not reach it: a citation count has no
  `ROW_FLOOR` to compare against, and its real derivation is
  `check-design-citations.py`'s inventory — which is exactly what F4
  used. F4 is therefore the one citation-count finding, not the sweep of
  that noun. **`arms` was reached only where the file declares a floor**;
  arm counts in review prose were not.
- **2,333 of the 2,361 live candidates were not individually derived.**
  Only the 28 GLOB candidates have a mechanical derivation; the rest
  ("222 rows", "148 arms", "77 gates") name sets that need a human to
  say which container is meant. §2 is the yield of the derivable
  sub-container plus a hand pass over the `adrs`/`checkers`/`probes`/
  `obligations`/`decisions` nouns. **The remaining nouns — `rows`,
  `arms`, `sites`, `controls`, `citations`, `commits` — were not swept**,
  and at 222 and 148 members the two largest are where I would look next.
- I did not run `check-clause-citations.py` (needs the standards sibling
  checkout, exits 2 when absent) or the harness gates. Nothing in this
  change touches a harness.
