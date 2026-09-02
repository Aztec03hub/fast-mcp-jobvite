# REVIEW-R20: the held twenty-eight, and the two gates that went red inside a merge

<!-- REVIEW-COVERS: 6e4fae3..c749334 PATHS: .github/workflows/ci.yml .github/workflows/mirror.yml docs/reviews/check-brief-report-references.py docs/reviews/check-brief-report-refs-controls.sh docs/reviews/brief-report-refs-known-missing.txt docs/reviews/probe-mirror-zero-refs.sh docs/reviews/check-checkers-are-wired.py docs/reviews/check-row-floor-exactness.py docs/reviews/check-row-floor-controls.sh docs/reviews/check-clause-citations.py docs/reviews/review-coverage-backlog.txt docs/adr docs/DESIGN.md docs/DESIGN-FREEZE.txt docs/OBLIGATIONS.md docs/CODE-REVIEW-CHECKLIST.md docs/briefs/PROTOCOL-sub-orchestrators.md docs/briefs/HANDOFF-2026-09-01-orchestration.md scripts/check-secrets-baseline.py scripts/check-mirror-liveness-controls.sh -->

**Reviewer:** `review-r20` (Tier 1, fresh). **Task:** #195.
**Pinned at:** `c749334` — derived, not typed, and re-derived at the end of
this document. **`origin/main` is `6e4fae3`** and the push is HELD.

**Headline: two CI-wired gates exited 1 at the pinned SHA, and would have
failed the first push.** Both went red *at a merge*, with both parents
green. That makes the merge record on this project **six for six**: every
merge has found something neither branch could see alone.

**Both were closed independently at `65fabe4` while this round was still
running**, by the orchestrator, who found them the same way. §8 records
that with the verifying measurement — the findings stand as measured, and
so does the fact that I was not the one who caught them first.

**2 High (both since closed), 3 Medium, 3 Low, 3 nits.**

---

## §0 — Corrections to my brief

Every agent on this project has found an error in its brief. Four here.

1. **The population is 28 commits, not 25, and 32 files, not 28.** The
   trunk moved under me: `c749334` merged `fix/187-floor-container`,
   which the brief §F told me was still live and untouchable. Derived:

       $ git log --oneline origin/main..HEAD | wc -l
       28
       $ git diff --stat origin/main..HEAD | tail -1
       32 files changed, 5626 insertions(+), 224 deletions(-)

   `fmj-worktrees/w187` was left untouched as instructed.

2. **`check-brief-report-refs-controls.sh` has 11 arms with floor 11,
   not "9 arms, floor 9"** (brief §C1). Task #195's own description says
   11. `docs/reviews/check-brief-report-refs-controls.sh:27` reads
   `ROW_FLOOR=11`; the run below prints `rows=11 floor=11 fired=11/11`.
   The brief and the task disagreed and the task was right.

3. **The wiring container is 129 -> 133, not "131 -> 133"** (brief §C7).
   `131` was a mid-population figure from `789d3be`'s commit body
   (`members 130 -> 131`). The endpoints:

       $ git ls-tree -r --name-only origin/main docs/reviews scripts | grep -cE '\.(py|sh)$'
       129
       $ git ls-tree -r --name-only HEAD docs/reviews scripts | grep -cE '\.(py|sh)$'
       133

   That selector is not mine: it reproduces the checker's own
   `Members: 133` at HEAD exactly, and the container definition is
   unchanged across the range.

4. **`actionlint` is not installed on this machine** — confirmed, as the
   brief predicted: `command -v actionlint` returns nothing. Neither
   workflow file was linted by me. It is on the unverified list.

---

## §1 — HIGH

### H1. `check-brief-report-references.py` exited 1 on the trunk. CI would have failed on the first push. **CLOSED at `65fabe4` - see §8.**

**Wired at** `.github/workflows/ci.yml:1267`. **Measured at `c749334`:**

    $ uv run --frozen python docs/reviews/check-brief-report-references.py
    Briefs scanned:            71
    Report names cited:        21
    Cited but not in the repo: 1
    Recorded as known-missing: 2

    ::error::A RECORDED ENTRY NOW RESOLVES, so the record is stale.
      WORKLOG-187-floor-container.md   is tracked now; delete its line
    An excuse list that only grows stops being read. It must
    shrink when the world does.
    $ echo $?
    1

**Neither parent could see it.** `789d3be` (the branch) does not contain
the gate at all — the file does not exist there, so the step is vacuously
absent. `1985471` (main, the commit immediately before the merge) exits
**0**: `Cited but not in the repo: 2`, both recorded. I ran the checker in
throwaway worktrees at both parents to get those numbers, and removed them.

The mechanism is exactly the one the record file documents at line 14:
the entry was *"designed to EXPIRE - the moment that worklog is committed,
the checker fails ... and the line must be deleted."* `a0677bc` wrote that
line on main; `789d3be` committed
`docs/worklogs/WORKLOG-187-floor-container.md` on the branch; the merge put
them in one tree. **The self-deleting record does not delete itself.** It
goes red and waits for a human, and the human who did the merge did not
see it because nothing ran.

**Suggested fix:** delete line 14 of
`docs/reviews/brief-report-refs-known-missing.txt`. Then delete line 15
(`REVIEW-R20.md`) in the same edit, once this report is on the trunk — see
M3, because **committing this report makes the gate red a second time by
the same mechanism, and no task owns that deletion.**

### H2. `check-row-floor-exactness.py` exited 1 on the trunk. Same shape, same merge. **CLOSED at `65fabe4` - see §8.**

**Wired at** `.github/workflows/ci.yml:1200`. **Measured at `c749334`:**

    $ python3 docs/reviews/check-row-floor-exactness.py
    Harnesses checked for exactness: 30
    Harnesses carrying BOTH floors, checked for agreement: 8
    Harnesses whose --min-rows was compared to a live count: 16

    2 floor(s) wrong:
      docs/reviews/check-brief-report-refs-controls.sh: carries a literal floor and the
        control table does not name it, so its floor is never compared to a row count.
      docs/reviews/probe-mirror-zero-refs.sh: carries a literal floor and the control
        table does not name it, so its floor is never compared to a row count.
    $ echo $?
    1

**Both parents exit 0:**

    1985471 (main)   rc=0   "Harnesses checked for exactness: 25 ... Every floor equals its
                             harness's live row count. OK."
    789d3be (branch) rc=0   "Harnesses checked for exactness: 30 ... OK."

The branch widened the container from 25 to 30 by KIND. Main added two new
harnesses with literal floors (`b4e6d06`, `a0677bc`). **Each half was
consistent with itself.** The widened selector only meets the new
harnesses in the merged tree, and `TABLE` in
`docs/reviews/check-row-floor-controls.sh` names neither.

This overlaps task #194, which was updated while I worked to say the
unwatched-floor population is four. **#194 is about watching; this is
about exit code.** The trunk is red whether or not anyone watches.

**Suggested fix:** add two rows to `TABLE` in
`docs/reviews/check-row-floor-controls.sh` — an ERE matching
`^  (ok|FAIL) +A[0-9]+` for the brief-report controls (its `row` function
prints `  ok   A1 ...`), and one matching `^  (ok|FAIL) ` for
`probe-mirror-zero-refs.sh`, whose third arm prints its own line outside
`row()` and so may need the `COMPUTED` token instead. **Derive both from a
run of the harness; do not adjust until the gate passes** — that is the
failure mode the checker's own closing paragraph names.

---

## §2 — MEDIUM

### M1. "the 87 `run:` steps" was true for two commits, was 89 at the pinned SHA and is 90 now — inside the file whose subject is stale numbers.

`docs/reviews/check-checkers-are-wired.py:94` and `:1410`:

    **Measured on 2026-09-02: of the 87 `run:` steps then in `ci.yml`, 21
    disabled or bypassed errexit ...**

Run the file's **own published re-derivation command** at each commit in
the range:

    25ee53b  86      file says 86   correct
    72c1a27  86      file says 86   correct
    b4e6d06  87      file says 87   correct
    a0677bc  89      file says 87   WRONG
    c749334  89      file says 87   WRONG

`b4e6d06` set it to 87 and converted the sentence to past tense with the
date `2026-09-02`. `a0677bc` then added two `run:` steps. **The date does
not save it:** every commit in that table is the same working night, so a
reader re-deriving "on 2026-09-02" gets 89 and cannot tell which 2026-09-02
the sentence means. A dated past-tense figure only resolves an ambiguity
coarser than the rate at which the figure moves.

**Suggested fix:** delete the numerator and denominator from both the
docstring and the `print()`, exactly as ADR-0034 ruled for the ADR count.
The sentence keeps its whole force as *"that population has been measured
and was empty; the command below re-derives it"* — the command is already
there, and it is the only part that cannot go stale.

### M2. ADR-0034's census is labelled "AT ACCEPTANCE" and it is not — and the same ADR says so eight lines below.

`docs/adr/0034-...md:48-49` (added by `c790727`, in this range):

    The partition AT ACCEPTANCE, recorded as the evidence for this ruling and NOT as a
    live figure - the set has grown since, and the command below is the live answer:

        19  Design change
        15  Deviation
        --
        34  total   (this ADR included)

**Measured, by running the ADR's own `Type:` census over each tree:**

    e3b5c97 (acceptance)  17 Design change / 14 Deviation / 1 Standards deviation
                          / 1 "Correction to a contract statement..." / 1 "Correction to a count..."
    c0f1524 (re-freeze)   identical
    d29937f               19 Design change / 15 Deviation      <- this is the table
    HEAD                  20 Design change / 15 Deviation / 35 total

The ADR's *next* paragraph already states this correctly: *"THAT TABLE IS
NOT WHAT I FIRST WROTE ... The census at acceptance read `17 / 14 / 1
Standards deviation / 1 Correction ...`"*. So the tense remedy did not hide
a wrong number — **it attached a right number to the wrong moment**, and
put the contradiction two paragraphs apart in one document. This is the
brief's §C5 question answered: the remedy was a label, and the label is
what went wrong.

**Suggested fix:** change `AT ACCEPTANCE` to `AFTER d29937f NORMALISED THE
THREE OUTLIERS`, which is the moment the table describes and the moment
the paragraph below already names.

**What I checked in ADR-0034 and found CORRECT**, because a wrong
correction is worse than the defect:

- *"Six of the `Design change` ADRs are unambiguous"* — all six named
  (0019, 0021, 0028, 0029, 0031, 0033) carry `**Type:** Design change`,
  verified by reading each file's `Type:` line. The de-counting from
  *"Six of the seventeen"* is right.
- *"A MINORITY OF ADRs DO JOB 1 - fifteen of thirty-four when this was
  written"* — 15/34 at `d29937f`, 15/35 live, still a minority.
- The blockquote now states no population at all. Correct.
- **The freeze holds.** `docs/DESIGN-FREEZE.txt` says `d1f1a52`, and
  `git rev-parse d1f1a52:docs/DESIGN.md` and `HEAD:docs/DESIGN.md` are the
  same blob `61e264d`. Derived, not typed.
- ADR-0035's claim that *"The eleven below are all `Deviation`"* is
  untouched and remains true; it describes an enumerated list, not a
  population.

### M3. The ratchet's record accepts a line with no reason, so an excuse needs no argument — and nothing ages one out.

This is the brief's §C6 question: *does a recorded line ever become a
permanent excuse?*

`check-brief-report-references.py:129`:

    name, _, reason = line.partition("  ")

`partition` on a line with no double space returns `("REVIEW-X.md", "", "")`.
The name is recorded, `reason` is empty, and **nothing checks it**. The
record file's own header says *"One line per report: `<basename>
<reason>`"* and *"Recording a line is NOT a waiver"* — a line with no
reason is precisely a waiver, and the gate accepts it silently.

Second half: a recorded line expires only when the report becomes tracked
or when every citing brief is deleted. **A brief that stays in
`docs/briefs/` forever with a report nobody ever writes holds its excuse
forever**, and there is no date, no owner, and no age on the line to make
that visible. H1 shows the first expiry mechanism does not fire by itself
either.

**Suggested fix, two lines:** in `read_record`, refuse (`return 2` via a
new error path, so it is a broken-instrument refusal and not a pass) any
non-comment line whose `reason` is empty after stripping; and require the
reason to begin with an ISO date, printing the age of every recorded line
in the summary so an old one is visible without a new gate. The record has
two entries today, so the migration is two edits.

---

## §3 — LOW

### L1. The gate discards the path it captured, and does not recurse into `docs/briefs/`.

`check-brief-report-references.py:88-92` captures the optional
`docs/(reviews|worklogs)/` prefix **outside** group 1, and
`tracked_basenames` compares basenames only. So a brief citing
`docs/reviews/REVIEW-X.md` is satisfied by a tracked
`docs/briefs/REVIEW-X.md`, or by a copy anywhere in the tree. The
docstring's closing note admits the gate cannot prove *identity*; this is
weaker than that — it cannot prove *location* either, and location is
mechanical.

`cited()` at line 137 uses `briefs.glob("*.md")`, which is not recursive.
A brief filed in `docs/briefs/archive/` is invisible to the gate, which is
the shape that makes a gate quietly stop covering things.

**Suggested fix:** move the prefix inside group 1 (`((?:docs/(?:reviews|worklogs)/)?(?:REVIEW|...)...)`)
and, when a citation carries a prefix, look it up in the full tracked-path
set rather than the basename set; keep the basename fallback for bare
citations. Change `glob` to `rglob` and add an arm to the controls with a
fixture brief in a subdirectory.

### L2. `set -uo pipefail` does not "disable or bypass errexit", and 5 of the 21 members are selected on that form alone.

`check-checkers-are-wired.py:93-94` describes the container as *"21
disabled or bypassed errexit (`set +e` or `set -uo pipefail`)"*.
**Measured:**

    $ cat /tmp/r20-errexit.sh
    set -uo pipefail
    false
    echo "REACHED-AFTER-FALSE"
    $ bash -e /tmp/r20-errexit.sh ; echo "rc=$?"
    rc=1

Nothing printed. Under GitHub's default `bash -e {0}` — which the same
paragraph correctly names two sentences earlier — `set -uo pipefail`
adds `-u` and `pipefail` and leaves `-e` exactly as it found it. It
neither disables nor bypasses errexit.

Of the 21, **16 contain `set +e` and 5 are selected only by the
`set -uo pipefail` form**: *The mirror workflow is still running*, *Every
pytest invocation is bounded by a timeout*, *Committed file types, whole
tree*, *Secret scan hook runs clean*, *Capability drift report*.

**This does not break the zero.** The selector is a strict superset of the
real container, so "all 21 tested a status" still implies the real members
did. But the paragraph is the register that tells the next reader what the
container *is*, and it is wrong about it.

**Suggested fix:** keep both forms in the selector — a superset is the
right conservative choice — and change the prose to *"21 either turn
errexit off (`set +e`) or restate the shell's options in a way that reads
like turning it off (`set -uo pipefail`, which under `bash -e {0}` does
not)"*. One sentence, and it stops the next reader inheriting the wrong
model.

### L3. HANDOFF v7 pins itself honestly and three of its figures are still wrong at HEAD.

`docs/briefs/HANDOFF-2026-09-01-orchestration.md` is pinned throughout to
`33fc977`, *"which is this file's PARENT"* — the right instinct, and the
commit message is literally *"version 6 went false by standing still"*.
Five commits later:

    handoff says              measured at c749334
    23 commits held           28
    backlog 80, holding       66
    check-row-floor-exactness 0   1  (H2)
    probe-mirror-zero-refs 0      0  (holds)

The `80` was correct at `33fc977` and went false at the *very next commit*,
`a0677bc`, which added `REVIEW-R18.md` and cleared 14 backlog entries. The
brief's own §E figure (80 -> 66) is right; the handoff is the stale copy.

**Suggested fix:** the handoff's status block and gate table should not be
transcribed at all. Replace the table with the commands that produce it
(`git rev-list --count origin/main..HEAD`, `grep -cvE '^\s*(#|$)'` over
the backlog, and the harness invocations), so the next reader gets HEAD's
answer instead of a snapshot. Failing that, regenerate the block as the
last commit before the push, when it is true for the longest.

---

## §4 — NITS

### N1. `PROTOCOL-sub-orchestrators.md` lost a verb in the rewrite.

Lines 98-100 read:

    **`TaskCreate` has NOT been tested from Tier 1** — the
    agent that could have declined, because deciding what becomes a task is
    Tier 0's, not because the tool was thought absent.

"the agent that could have declined" has no object. The sentence it
replaced read *"the agent that found this declined to test them"*. This is
canon that every agent is ordered to read.

**Suggested fix:** *"— the agent that could have tested it declined,
because deciding what becomes a task is Tier 0's, not because the tool was
thought absent."*

### N2. `ci.yml:1267`'s `|| exit 1` collapses the gate's deliberate exit 2.

    run: uv run --frozen python docs/reviews/check-brief-report-references.py || exit 1

The checker distinguishes **2 (refusal: `git ls-files` unreadable, nothing
was checked)** from **1 (a real finding)**, and arm A5 exists to prove it.
`|| exit 1` maps both to 1. The step still fails, so nothing is hidden from
CI's status — but the one bit the author built and controlled for is
thrown away in the wiring.

**Suggested fix:** `... || exit $?`. It keeps the errexit-safe shape the
project requires (only the last command of an AND-list triggers errexit)
and preserves the code.

### N3. The refusal branch is the one failure path with no amputation arm.

`check-brief-report-refs-controls.sh` amputates `unrecorded`, `resolved`,
`unreferenced` and the regex's left boundary. The `names is None` refusal
that A5 exercises has no amputation partner. It is the weakest gap of the
four because deleting that branch produces a `TypeError` rather than a
green — but A5 is currently the only positive arm in the file whose
subject nobody has watched being removed.

**Suggested fix:** A12 — `sed 's/^    if names is None:$/    if False:/'`,
with A5's fixture, expecting rc **1** (the traceback's exit code), and
raise `ROW_FLOOR` to 12. It proves the refusal is reached rather than
merely reachable.

---

## §5 — What I checked and found CORRECT

Not wasted lines: the brief asked me to say so.

- **The two new gates' controls all fire, and I watched the floors, not
  the source.**

      $ bash docs/reviews/check-brief-report-refs-controls.sh
      ...11 rows, all ok...
      HARNESS-RESULT name=brief-report-refs-controls rows=11 floor=11 fired=11/11 status=ok
      rc=0

  I traced each of the 7 positive arms by hand against the checker's four
  branches to look for the third confounded arm the brief predicted.
  **A3 and A4 are correctly isolated** — each records the *other* fixture
  name precisely so only one branch can fire, which is the fix A8 forced.
  A1, A2, A6, A10 each trip exactly one branch. **I did not find a third
  confounded arm in this file.** A11 is a genuine amputation: deleting the
  lookbehind makes `docs/CODE-REVIEW-CHECKLIST.md` match as
  `REVIEW-CHECKLIST.md` and A10 goes red at 1.

- **`probe-mirror-zero-refs.sh` extracts rather than retypes, and it fails
  loudly.** The `awk` range is anchored on `refs=$(git for-each-ref` and
  the *first* following `^ *fi$`, which is the guard's own `fi`. If the
  block moves or is renamed, `GUARD` is empty and the probe exits **3**
  with `ANCHOR NOT FOUND`; if `exit 1` becomes anything else, the
  `grep -q` guard exits 3 with `ANCHOR NOT UNIQUE / wrong block`. Both are
  refusals, not passes. Arm 3's amputation (`exit 1` -> `:`) is real: arm 1
  goes from rc 1 to rc 0. Measured 3/3, floor 3, rc 0.

- **The `GITHUB_STEP_SUMMARY` question resolves clean.** The brief asked
  whether the writes work when the variable is unset. They would not —
  the step opens `set -euo pipefail`, so an unset `GITHUB_STEP_SUMMARY`
  is an unbound-variable failure — but **no path reaches them outside
  Actions**: all four writes sit outside the `awk` range the probe
  extracts (`mirror.yml:151,153,156,220`; the range ends at the `fi` on
  line 212), and nothing else executes `mirror.yml` locally. Not a finding.

- **`git for-each-ref refs/remotes/origin` is populated at that point.**
  `actions/checkout@v6` with `fetch-depth: 0` fetches
  `+refs/heads/*:refs/remotes/origin/*`, so the guard counts real refs
  rather than always-zero. I did **not** execute this — it is on the
  unverified list — but I looked for the trap rather than assuming.

- **The three merges are all clean.** `git show --cc` on `39c3e2e`,
  `33fc977` and `c749334` each produces an **empty** combined diff: no
  evil-merge hunk, no resolution that reintroduced anything. The two red
  gates are therefore not conflict damage; they are composition.

- **Every other CI-wired gate I could run is green at `c749334`:**

      uv run --frozen pytest                       887 passed, 0 skipped, 6 deselected   rc=0
      uv run --frozen mypy                         no issues in 138 source files         rc=0
      uv run --frozen ruff check .                 All checks passed!                    rc=0
      uv run --frozen ruff format --check .        138 files already formatted           rc=0
      python3 scripts/check-harness-anchors.py --self-check --floor 464   464 anchors     rc=0
      python3 docs/reviews/check-row-floors.py     33 harnesses, 0 unfloored             rc=0
      docs/reviews/check-review-coverage.py        backlog 66 recorded / 66 measured     rc=0
      docs/reviews/probe-coverage-ratchet.py       10/10 arms                            rc=0
      docs/reviews/check-checkers-are-wired.py     133 members, 0 unexplained            rc=0
      docs/reviews/check-clause-citations.py                                             rc=0
      docs/reviews/check-obligations.py            31 mappings, 25 verified, 6 absent    rc=0
      docs/reviews/check-design-citations.py                                             rc=0
      docs/reviews/probe-repoint-fail-closed.py    every row behaved                     rc=0
      scripts/check-mirror-liveness-controls.sh    17/17, floor 17                       rc=0
      scripts/check-secrets-baseline.py            audited=22 found=22 new=0 stale=0     rc=0

  Both floors were derived from `ci.yml`, not typed: `check-suite-floor.sh
  887` and `--self-check --floor 464`. **887 passed is exactly the floor,
  with zero slack** — worth knowing before the next test lands.

  `scripts/check-secrets-baseline.py` exits **2** under `uv run --frozen`
  (`detect-secrets is not importable, so this gate cannot run and must not
  report success`). That is the documented refusal, not a failure; run the
  documented way (`--with detect-secrets==1.5.0`) it exits 0. CI installs it.

- **The 6 deselected tests are not skips.** `pyproject.toml:153-166`
  deselects `credentialed` and `network` by `-m` and states the rule
  explicitly — *"deselected, never marked skipif"* — and `ci.yml:1020` and
  `:1093` run both arms in their own steps. The zero-skips requirement is
  met by construction, not by luck.

- **The commit-message numbers in §C7 hold, except the two in §0:**
  backlog 80 -> 66 (counted at both ends), 31 register rows
  (`grep -c '^| WS-'`), 138 mypy files, ADR census 20/15/35, floor 3 for
  the mirror probe. Floors "9/3" and members "131 -> 133" are corrected
  above.

- **The `PATHS` half of the delivery rule works.** `check-review-coverage.py`
  is green with the backlog holding at 66 and 0 entered / 0 cleared /
  0 changed-kind / 0 subject disagreements. Note that it measures
  **`origin/main`**, so none of my 28 commits are in its population yet;
  this declaration is scored only after the push.

---

## §6 — What I did NOT verify

For what I could not settle, not for what I did not try.

1. **`actionlint`.** Not installed (`command -v actionlint` empty). Neither
   `ci.yml` nor `mirror.yml` was linted. Two workflow files changed in this
   range and neither has been through it.
2. **Anything in CI.** The trunk has one green run ever (`33582613697`,
   head `22c9873`) and every commit here is unpushed. H1 and H2 are
   predictions of a CI failure derived from running the exact wired
   commands locally; they are not observations of a CI run.
3. **`actions/checkout@v6` populating `refs/remotes/origin/*`.** Reasoned,
   not executed. If it does not, `probe-mirror-zero-refs.sh`'s subject
   would refuse every real push — but the step has never executed for want
   of `MIRROR_TOKEN`, so nothing would tell us either way. I did not test
   the mirror push by running it; it is `--force --prune`.
4. **Three large new documents read only in part:**
   `docs/reviews/probe-170-retyped-counts.py` (971 lines),
   `docs/reviews/FINDINGS-170-retyped-counts.md` (831),
   `docs/worklogs/WORKLOG-187-floor-container.md` (423). I ran neither
   probe-170 nor the #187 worklog's measurements. They are excluded from
   my `PATHS` declaration.
5. **`REVIEW-R18.md` and `REVIEW-R19.md` themselves** (636 + 714 lines).
   I read R19's *outcome* through the seven closed findings and their
   commits, not the report end to end. Excluded from `PATHS`.
6. **`check-row-floor-exactness.py`'s 629 new lines were run, not read.**
   H2 is a measurement of its exit code and message, not a review of its
   logic. Its `TABLE`-driven half in `check-row-floor-controls.sh` I read
   only far enough to write H2's suggested fix.
7. **Whether `probe-mirror-zero-refs.sh`'s arm 3 label is honest about a
   second `refs=$(git for-each-ref` appearing later in `mirror.yml`.** An
   `awk` range restarts, so a second occurrence would concatenate a second
   copy into `GUARD`. There is exactly one occurrence today
   (`mirror.yml:206`); I did not build the two-occurrence fixture to see
   what the probe does with it.

---

## §7 — Re-derived at the end, as the brief required

    $ git rev-parse HEAD
    c7493341abc9ee20e0972f81c086e4196060a17c
    $ git rev-parse origin/main
    6e4fae36fccc2b76c57f9fdc14eb259f4f89a99f
    $ git log --oneline origin/main..HEAD | wc -l
    28

Everything above was measured at `c749334`, which is where my worktree is
pinned. **`main` itself moved three commits further while I worked** — see
§8. `c749334` is still an ancestor of it, so nothing above was invalidated
by the move; two findings were closed by it.

---

## §8 — The trunk moved under me, and it closed both Highs

Re-derived after writing §1-§7:

    $ git -C repos/fast-mcp-jobvite log --oneline c749334..main
    b7de853 BRIEF for #196: the ADR corpus has never been read, and it is a reading job not a grep
    417339e #191: the register said the sub-claim "is a grep" - the grep returns zero, for the wrong reason
    65fabe4 Fold #187: the merge left my own two floors uncovered, which is the point of it
    $ git rev-list --count origin/main..main
    31

**Measured at `b7de853` in a throwaway worktree, since removed:**

    uv run --frozen python docs/reviews/check-brief-report-references.py    rc=0
      Briefs scanned: 72 | Report names cited: 21 | Cited but not in the repo: 1
      Recorded as known-missing: 1
    python3 docs/reviews/check-row-floor-exactness.py                        rc=0
      Harnesses checked for exactness: 32 ... Every floor equals its harness's
      live row count. OK.

**H1 and H2 are both closed at `65fabe4`**, which deleted the
`WORKLOG-187-floor-container.md` line from the record and added the two
missing `TABLE` rows in one commit. Its message — *"the merge left my own
two floors uncovered, which is the point of it"* — says the orchestrator
found the same thing from the other side. **I did not catch these first,
and the report should not read as if I had.** What R20 adds is the
measurement at both parents, which is the evidence that the merge, not
either branch, is where it entered.

**M1 is not closed and got worse.** At `b7de853` the file still says 87
and its own command returns **90**:

    $ grep -oE 'of the [0-9]+ `run:` steps' docs/reviews/check-checkers-are-wired.py
    of the 87 `run:` steps
    $ <the docstring's own yaml command>
    run steps=90

The three commits touch five files:

    .github/workflows/ci.yml
    docs/briefs/BRIEF-196-adr-citation-read.md
    docs/reviews/WRONG-SUBJECT-REGISTER.md
    docs/reviews/brief-report-refs-known-missing.txt
    docs/reviews/check-row-floor-controls.sh

So **M2, M3, L1, L3, N1 and N3 sit in files that did not move** and stand
as measured. **N2 and L2 have `ci.yml` as their subject**: N2's line number
`1267` and L2's list of five members are as at `c749334` and should be
re-derived before either is acted on. Neither claim is about a line the
three commits added.

**This report is committed on `review/r20`.** The worktree
`fmj-worktrees/r20` is removed. I did not push, did not merge, and fixed
nothing.
