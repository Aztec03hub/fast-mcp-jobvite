# WORKLOG-222: merge-invented content, an instrument for it, and what it found

Not a code review, so it declares no `REVIEW-COVERS` range. It builds one
instrument and reports what that instrument measures.

Agent: `suborch-222`. Worktree `/tmp/w222-merge-invented`, branch
`fix/222-merge-invented-content`, based on `main` at
`ae809c5fc0a4e628d0af7b5a9600b1e0dbf4bbd4` (derived with `git rev-parse HEAD`
in the shared checkout, never typed from a brief). `origin/main` is
`6e4fae36fccc2b76c57f9fdc14eb259f4f89a99f`. Dated 2026-09-02 01:28 CDT.

---

## A. THE DISCRIMINATOR, AND BOTH CONTROLS

`docs/reviews/check-merge-invented.py`. The test it applies:

    a line present in the merge's version of a file
    and in NEITHER parent's version of THAT SAME FILE

**A NON-EMPTY `git show --cc` IS A SCREENING FILTER, NOT A FINDING.** `--cc`
reports every region both sides touched, so two agents editing adjacent rows of
one table produce hunks while each row comes whole from one side. The
implementation therefore never consults `--cc` for its verdict; it prints the
byte count only so a reader can see the screen and the verdict disagree.

Set semantics, stated so the next reader does not have to infer them:

- A line that only CHANGES COUNT (once in a parent, twice in the merge) is not
  reported. Multiset arithmetic would report re-ordering as authored content.
- A file present in only ONE parent yields no lines for the other side. Because
  a line must be absent from BOTH parents, whole new files are not flagged.
- Paths scanned are the union of `git diff --name-only <parent> <merge>` over
  every parent. This is not a narrowing: a path byte-identical to every parent
  cannot hold a line absent from every parent.

### The two repo-history controls (`--self-test`), run verbatim

    $ python3 docs/reviews/check-merge-invented.py --self-test
    POSITIVE CONTROL PASS: 73dd717 -> 1 line(s) containing 'A syntax split'
        docs/reviews/check-brief-report-references.py: - **A syntax split**, counting only path-qualified forms as citations
    NEGATIVE CONTROL PASS: 043cc6f cc=983B paths_scanned=17 invented=0
    SELFTEST_RC=0

The negative control is the load-bearing one. `043cc6f` has 983 bytes of
combined diff and comes back clean, over **17 scanned paths** - the zero is a
zero over a population, not a zero over nothing. If it had flagged, the
detector would have been measuring `--cc` and not authorship.

The checker refuses a vacuous negative: if `043cc6f` ever reports `cc=0B` it
prints `NEGATIVE CONTROL INCONCLUSIVE` and exits 1, because a control that does
not exercise the screening filter proves nothing about it.

### The synthetic control (`--synthetic-test`), which needs no history

The repo-history controls prove the detector agrees with one hand-traced case.
A detector that special-cased that SHA would pass them too. So it also builds
two merges from scratch in a temp repo:

    $ python3 docs/reviews/check-merge-invented.py --synthetic-test
    SYNTHETIC ARM A PASS: paths_scanned=1 invented=['CCC typed only in the resolution']
    SYNTHETIC ARM B PASS: cc=165B paths_scanned=1 invented=0
    SYNTH_RC=0

ARM A: both branches edit one line, the resolver types a third version. Caught,
and caught EXACTLY - the assertion is equality against the one expected line,
not "non-empty", so an over-firing detector fails this arm too.
ARM B: each branch adds its own row, the merge keeps both verbatim. `--cc` is
165 bytes and the verdict is clean. This is `043cc6f`'s shape, reproduced from
nothing.

### Determinism

Required by the brief because `suborch-213`'s probe for this same question was
nondeterministic. Run twice on an identical tree, byte-compared with `cmp`:

    DETERMINISM_RC=0    (full-history sweep, 133 merges, two runs identical)

Ordering is by first appearance in the merge's own file, not sorted: these
lines are prose that has to be read, and sorting shreds the argument they make.

---

## B. THE SWEEP

### The held range, `origin/main..HEAD` - 17 merges

    TOTAL merges=17 invented_lines=53

**One merge invents anything: `73dd717`, 53 lines.** Every other merge in the
held range is clean, including the two other non-empty combined diffs:

| merge | cc | paths scanned | invented |
|---|---|---|---|
| `043cc6f` | 983B | 17 | 0 |
| `fb6483e` | 1302B | 21 | 0 |
| `73dd717` | 7226B | 15 | **53** |
| the other 14 | 0B | 3 to 91 | 0 |

**THE ZERO IS NOT VACUOUS**, and here is what makes it so rather than my saying
so: `paths_scanned` is printed per merge and is non-zero for all 17; `fb6483e`
is a second natural negative control the brief did not name (1302 bytes of
combined diff, 0 invented) and it agrees with `043cc6f`; and the same instrument
that returns 0 on those returns 53 on `73dd717` in the same run.

**MY OWN INSTRUMENT'S FIRST WRONG ZERO, RECORDED.** `check-checkers-are-wired.py`
passed at exit 0 with my brand-new unwired checker on disk. It reads
`git ls-files`, so an UNTRACKED file is invisible to it. `git add` made it go
red immediately. I would have committed a green that had never seen the file.

### Before `origin/main` - I chose to sweep it, and it changed the headline

The brief left this to my judgement. I swept it. The sweep costs 12 seconds
over the whole history and the alternative was a finding scoped to whichever
range happened to be held tonight.

    $ python3 docs/reviews/check-merge-invented.py --range HEAD
    TOTAL merges=133 invented_lines=224

**TEN merges of 133 invent content, and NINE of them are before `origin/main`
and have never been looked at.** `73dd717` is not special; it is the one that
happened to be inside the range someone measured.

| merge | cc | invented | where |
|---|---|---|---|
| `73dd717` | 7226B | 53 | `PREAMBLE.md` 11, `BRIEF-199` 14, `check-brief-report-references.py` 28 |
| `a881344` | 13279B | 38 | `check-no-errexit.py` 28, `check-pytest-bounded.sh` 8, `.secrets.baseline` 2 |
| `5bf3fb1` | 6699B | 32 | `ADR-0026` 21, `ci.yml` 10, `.secrets.baseline` 1 |
| `abd856d` | 6725B | 28 | `ci.yml` 18, `server.py` 8, `.secrets.baseline` 2 |
| `92cb89b` | 7429B | 22 | `check-design-citation-shape.py` 20, `.secrets.baseline` 2 |
| `3421ce6` | 5041B | 17 | `check-u1-boot-amputation.sh` 17 |
| `e26c199` | 41703B | 15 | `ci.yml` 13, `OBLIGATIONS.md` 2 |
| `69fba1a` | 3708B | 11 | `test_server.py` 9, `ci.yml` 2 |
| `f2a7bce` | 2151B | 6 | `.secrets.baseline` 5, `ci.yml` 1 |
| `517a810` | 918B | 2 | `ci.yml` 2 |

The remaining 123 merges are 0.

**WHAT THE 224 LINES ARE, BY KIND.** Overwhelmingly PROSE - comments,
docstrings, ADR text, brief text. That is not a downgrade in this repository:
prose is where the rulings live. `check-brief-report-references.py`'s ruling is
in its docstring; `PREAMBLE.md` is the instruction every agent reads first.

The genuinely EXECUTABLE merge-authored lines, all still live at `ae809c5`:

- `docs/reviews/check-no-errexit.py` (`a881344`): the whole `EXEMPT` dict, its
  `assert all(v.strip() ...)` guard, and the loop branch that skips an exempt
  file. **An exemption mechanism for a wired gate, authored in a merge.**
  Live at `:88`, `:95`, `:129`.
- `scripts/check-pytest-bounded.sh` (`a881344`): a self-exclusion,
  `| grep -v '^scripts/check-pytest-bounded\.sh:'`. Live at `:74`.
- `docs/reviews/check-design-citation-shape.py` (`92cb89b`): a whole
  `ends on a BLANK line` branch plus the `ends_blank` generator and its check
  row. Live at `:160`, `:186`, `:199`.
- `.github/workflows/ci.yml`: floor literals (`887` lineage: 873, 810, 801,
  590, 360, 352; anchors 421, 415, 306) and three whole STEPS - the U9 controls
  and amputation steps at `abd856d`, the log-redaction amputation step at
  `5bf3fb1`, and the U3/U4 mutation-survivor guards at `e26c199`. A merged floor
  literal is the EXPECTED shape when two branches each bump the same number;
  a whole new step is not.
- `.secrets.baseline`: 12 lines across four merges. Almost certainly the
  regenerated-hash class rather than authored content; I did not read them.

**A reflow caveat that keeps this honest.** Re-wrapping a paragraph changes
every line boundary, so an unchanged sentence can surface as several "invented"
lines. The docstring says so. This is why the output is a population to read,
not a count to gate on, and it is the main reason I did not wire it.

---

## C. WHAT `73dd717` ACTUALLY WROTE

`suborch-213` traced one bullet and handed over the rest unread. Read now, all
three files, at both parents (`4be5356` and `6f921f8`) and the merge.

### C1. `docs/briefs/PREAMBLE.md` - a rule change to the canon, in a file NEITHER branch touched

**BOTH PARENTS HOLD THE IDENTICAL BLOB.** `git rev-parse` on
`4be5356:docs/briefs/PREAMBLE.md` and `6f921f8:docs/briefs/PREAMBLE.md` both
give `69f6ee5f74c0e5344a37e1bb931de25175a64def`. There was no conflict in this
file. There was no change to it on either side. The merge added 766 bytes to it.

What was there (one sentence, at both parents):

> Work you find outside your scope gets a `TaskCreate`, never a silent fix and
> never a silent drop.

What the merge put in its place (11 lines, live at `PREAMBLE.md:16-26`):

> **Work you find outside your scope is REPORTED - never a silent fix and never
> a silent drop.** Whether you also file it as a task depends on a mandate your
> brief either grants or does not: a REVIEWER's brief says findings go on the
> board and they do; a sub-orchestrator's does not, because deciding what
> becomes a task is Tier 0's call and `PROTOCOL-sub-orchestrators.md` rules it
> so. **If your brief is silent, report it and do not create it.**
>
> That sentence read *"gets a `TaskCreate`"* flatly until `suborch-199` found it
> contradicting `PROTOCOL-sub-orchestrators.md` [...]

**THIS IS THE HIGHEST-VALUE ITEM IN THE TASK, AND IT IS NOT A DEFECT IN ITS
CONTENT.** I read it and I believe it is correct: it resolves a real
contradiction `suborch-199` found, and it defers to the PROTOCOL. The defect is
its PROVENANCE. A governing instruction that every agent on this project reads
first - including me, an hour ago, when it told me to report rather than file -
was rewritten inside a merge resolution, in a file neither branch modified. It
appears as an addition in no branch diff. Nobody reviewed it. It has been
obeyed ever since as reviewed canon.

**Suggested fix (a suggestion, not a ruling).** Do not rewrite the paragraph -
it is right. Land a one-line provenance note under it saying the rule was
settled at `73dd717` in response to `suborch-199`'s finding, so its authority
is visible and a future reader is not left inferring it from prose. If you want
the stronger form, the same content belongs in
`PROTOCOL-sub-orchestrators.md` where the ruling actually lives, with
`PREAMBLE.md` pointing at it - one canonical statement instead of two that can
drift, which is the failure this very paragraph is about.

### C2. `docs/briefs/BRIEF-199-ratchet-defects.md` - a deferral converted into a ruling

Both parents had modified this file, so a conflict here is legitimate. The
merge's resolution is not either side.

Parent `6f921f8` (`suborch-199`'s side) ended:

> That is a finding about the gate, not about this sentence, **and it is
> `suborch-199`'s to report rather than to rule on.**

The merge replaced that with:

> That is a finding about the gate, not about this sentence. **It is now RULED -
> see the checker's docstring - and the ruling is that the false positive is
> ACCEPTED: no marker, no exemption, no syntax split.**

**A merge resolution took a question one side had explicitly LEFT OPEN and
closed it.** That is a legitimate thing for Tier 0 to do; it is not a legitimate
thing for a merge to be the only record of. The ruling it points at is the block
in C3, which was authored in the same merge, so the ruling and its citation are
both merge-invented and each is the other's only support.

**Two new factual claims also entered here, and I checked both.**

- *"TWICE, INDEPENDENTLY"*: CONFIRMED. `fa94f77` (2026-09-02 00:23:27, on the
  `4be5356` side) and `5bcdb45` (00:27:25, on the `6f921f8` side) both edit this
  file and both fix the same sentence, four minutes apart, on opposite sides of
  the merge. The topology supports it.
- *"to Tier 0 and to `suborch-199`"*: the ATTRIBUTION rests on commit messages
  and branch side, not on authorship - both commits are authored `Phil
  Lafayette`, as every commit here is. The claim is supported by which branch
  each landed on, which is the right evidence; I note it because git authorship
  establishes nothing about who decided.

**Suggested fix.** Leave the prose. Add the ruling to wherever this project
records rulings as rulings (a task line or an ADR-shaped note), so it is not
carried solely by a brief and a docstring that a merge wrote in the same breath.

### C3. `docs/reviews/check-brief-report-references.py` - a 33-line RULING block in a gate's docstring

Live at `:50-82`. Twenty-eight reported lines, all of them one block, headed:

> **RULED: THIS GATE CANNOT TELL A CITATION FROM A QUOTATION, AND THAT FALSE
> POSITIVE IS ACCEPTED.**

`suborch-213` traced one bullet of it. Here is the rest, checked claim by claim.

| claim in the merge-authored block | verdict |
|---|---|
| "That happened twice in one hour, independently, to Tier 0 and to `suborch-199`" | SUPPORTED - `fa94f77` and `5bcdb45`, four minutes apart, opposite sides (C2) |
| "An `EXEMPT` marker... inflate a population from 47 to 61 PURELY FROM PROSE ABOUT THE MARKER" | consistent with this project's recorded measurement of the marker class; I did not re-derive 47 -> 61 |
| **"A syntax split... Refused because it is FALSE HERE: six names cited BOTH ways, so the bare form carries real citations and the split would drop them"** | **ALREADY FOUND ARGUED BACKWARDS (task #213 / R21-M3).** If a name is cited BOTH ways, the path-qualified citation still exists, so a syntax split does NOT drop it. The measurement is the argument AGAINST the refusal. Not re-litigated here; recorded because it is the only line of this block anyone had read |
| "Recording the name in the ratchet... that file's own header says recording is not a waiver" | CONFIRMED against `docs/reviews/brief-report-refs-known-missing.txt`, whose header reads *"Recording a line is NOT a waiver"* |
| "a 28KB report written into a worktree, declared destroyed, and recoverable only because someone looked in a third place" | CONFIRMED - `REVIEW-R18.md`, and `a0677bc` records the same three-places account. Consistent with this file's own line 6 |

**So one of five checkable claims in the block is wrong, and it was already
known.** The rest hold. **The finding is not that the block is false. It is
that a RULING with five factual claims entered a wired gate's docstring with no
review, and the one claim anybody has since read turned out to be backwards.**
That is the base rate this task should be sized on.

**Suggested fix.** The syntax-split bullet is #213's to fix and I did not touch
it. Separately, and cheaply: the block asserts a ruling and cites *"see the
checker's docstring"* from a brief that the same merge wrote - a citation that
resolves only because both halves landed together. Give the ruling one home.

---

## D. WHAT GATES ON THIS TODAY - the brief's "nothing gates" is TOO STRONG

The brief flagged that "nothing gates on this" rested on a grep. It does, and
the grep understated the situation in one direction and overstated it in
another. What I found by reading the checker rather than grepping for `--cc`:

**`docs/reviews/check-review-coverage.py` IS merge-aware, and it scores evil
merges.** Its `substantive` test uses `git show --name-only`, which defaults to
`--cc`. A CLEAN merge prints no files and is classed "nothing to read"; an EVIL
merge prints its merge-unique files and *"is scored below like anything else"*
(`:517-522`). So `73dd717` IS in the coverage population.

**And it reads as FULLY COVERED.** It is neither in the `NONE` list, the
`PARTIAL` list, nor the backlog ledger (`review-coverage-backlog.txt`:
`73dd717` NOT PRESENT). The reason is `REVIEW-R21.md:3`:

    <!-- REVIEW-COVERS: c749334..80463a5 -->

No `PATHS`, so it claims the whole tree, and `73dd717` is inside that range
(verified: `git rev-list c749334..80463a5` contains
`73dd7174767a5dc67d7b44cd39419438f6e0db35`).

**The declaration that clears it is the same document that says the merge
invented nothing.** `REVIEW-R21.md:545-548`:

> **The four merges.** `git show --cc` on all four produces an **empty**
> combined diff, i.e. every file in each result matches one parent - no third
> version was invented at any merge.

That is false for `73dd717` (7226 bytes). The coverage gate cannot see it,
and it says so itself, in the last three lines it prints:

    NOTE: this proves a commit's files fall inside some round's
    declared range and paths, NOT that the round read them - a
    declaration is a claim by its author.

**So the accurate statement is not "nothing gates on this". It is: the coverage
gate DOES include this merge, and it is satisfied by a declaration whose own
text records the opposite of what the merge contains.** That is a stronger
finding than an absence, because it is a green that certifies the gap.

**What genuinely has no gate**: nothing anywhere runs the parent-set test. The
only three artefacts that mention combined diffs at all are prose - `REVIEW-R21`,
`REVIEW-R20` and `WORKLOG-213` - and two of the three assert the empty-`--cc`
claim that is false. No `.github/` step, no checker, no probe.

**Suggested fixes, all suggestions.**

1. `check-merge-invented.py --range <base>..<ref> --strict` is ready to wire the
   day you rule that it should be. I did not wire it, deliberately: the reflow
   caveat means it would fail a build on formatting. If it is wired, it should
   be a SET-RATCHET over `(merge, path)` pairs like `review-coverage-backlog.txt`,
   never a demand for zero - a zero-demanding gate on a trunk anyone still
   merges into is red by construction and gets switched off.
2. Cheaper and available now: a review round covering a range that contains an
   evil merge should be required to state the merge-unique content it read. That
   is a `PREAMBLE.md` sentence, not code.
3. `REVIEW-R21.md:545-548` states something false about `73dd717`. Correcting it
   in place is #211/#213 territory; I flag it because a coverage declaration is
   resting on it.

---

## E. GATES RUN, exit codes read on their own line

    $ uv run --frozen ruff check --output-format=concise docs/reviews/check-merge-invented.py
    All checks passed!
    RUFF_RC=0

    $ uv run --frozen mypy docs/reviews/check-merge-invented.py
    Success: no issues found in 1 source file
    MYPY_RC=0

    $ uv run --frozen ruff check --output-format=concise docs/reviews/check-checkers-are-wired.py
    All checks passed!
    RUFF_RC=0

    $ uv run --frozen python docs/reviews/check-checkers-are-wired.py
    WIRED_RC=0

    $ python3 scripts/check-harness-anchors.py --self-check --floor 464
    OK: all 464 anchors resolve in their target file [...] (floor 464).
    ANCHORS_RC=0

    $ uv run --frozen pytest -q
    887 passed, 6 deselected in 57.60s
    $ printf '%s\n' "$out" | bash scripts/check-suite-floor.sh 887
    suite floor OK: 887 passed, floor 887
    HARNESS-RESULT name=check-suite-floor.sh rows=887 floor=887 status=ok
    FLOOR_RC=0

**887 passed, 0 skipped, 6 deselected.** Reported as a passed-count, not as
"green", and the zero-skip requirement is met.

Both floors were DERIVED from `.github/workflows/ci.yml`, never typed from a
brief: `check-suite-floor.sh 887` and `--self-check --floor 464`.

**ONE RED EXISTS AND IT IS NOT MINE.** `docs/reviews/check-no-errexit.py` exits
1 on `docs/reviews/probe-stale-branch-regression.sh:50  set -euo pipefail`. I
ran the identical command in the SHARED CHECKOUT of unmodified `main` and got
the same exit code:

    $ uv run --frozen python docs/reviews/check-no-errexit.py   # in my worktree
    ERREXIT_RC=1
    $ uv run --frozen python docs/reviews/check-no-errexit.py   # shared main, untouched
    MAIN_ERREXIT_RC=1

Same file, same line, same verdict, and my branch changes neither. `suborch-221`
reported this same red independently and traced it to `ebaf6c8`. I did not fix
it - it is outside this task and someone else already owns it - but I record it
here because "I committed while a gate was red" is otherwise indistinguishable
from not having looked.

**Why `check-checkers-are-wired.py` is edited at all.** Adding a checker to
`docs/reviews/` made that gate go RED (`1 checker(s) are UNWIRED and
unexplained`). The brief forbids wiring a gate, and refusing to commit on red is
standing. The checker offers a third path it names itself - `UNWIRED_BY_DECISION`
with a reason - and there is already a section in it headed *"REPORTING
INSTRUMENTS THAT MUST NOT REFUSE"*. The entry I added says the gating decision
is Tier 0's and open on #222. **That is a record of the current state, not a
ruling on it.** If you rule the other way, the entry is one line to delete.

---

## F. WHAT I DID NOT VERIFY

Things I could not settle, not things I did not try.

- **The 224 lines are not all read.** I read all 53 of `73dd717` in full. Of the
  other 171 I read the executable ones and the file-level breakdown; the prose
  in `ADR-0026` (21), `check-u1-boot-amputation.sh` (17), `check-no-errexit.py`
  (28) and `check-design-citation-shape.py` (20) I did NOT read sentence by
  sentence. **On the base rate section C established - one wrong factual claim
  in five, in the only block anyone has read - I would expect more findings in
  there.** That is the single most likely place for the next one.
- **`.secrets.baseline`'s 12 lines.** I did not open them. They are almost
  certainly regenerated hashes, which is a known-benign class here, but "almost
  certainly" is my inference and not a measurement.
- **How many "invented" lines are reflow rather than authorship.** I did not
  quantify the reflow share across the 171 lines I did not read. For `73dd717`
  it is zero - I diffed the parents directly and every line is new prose - but I
  cannot state a rate for the rest.
- **The 47 -> 61 marker measurement** quoted in C3 I did not re-derive. I
  checked that it is consistent with what this project records about that class.
- **`git ls-files` populations elsewhere.** I found ONE checker blind to an
  untracked file (`check-checkers-are-wired.py`, section B). I did not sweep the
  other checkers for the same shape, and that is a real sibling question.
- **Whether an octopus merge exists here.** The detector handles N parents by
  construction (it unions every parent's lines), but every merge in this
  repository has exactly two, so the N>2 path has never executed. Untested.
- **CI.** Nothing here was run in CI, and I did not run the full pytest suite to
  completion before writing this section; the suite result is recorded in the
  commit message. My change touches only `docs/reviews/*.py`.
- **`actionlint`** is not installed in this environment and I make no claim
  about it.
