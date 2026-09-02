# WORKLOG #187 - the floor container is a KIND, not a glob

Branch `fix/187-floor-container`, cut from local `main` at `39c3e2e`.
Worktree `/home/plafayette/claude_projects/evolv/fmj-worktrees/w187`.
**Not pushed, not merged.**

## 0. Three corrections to the brief, before anything else

**0.1 THE WORKTREE BASE IN THE BRIEF WOULD HAVE THROWN AWAY THE FINDING.**
§A says `git worktree add ../../fmj-worktrees/w187 -b fix/187-floor-container
origin/main`. Measured:

    $ git rev-parse origin/main main
    6e4fae36fccc2b76c57f9fdc14eb259f4f89a99f
    39c3e2ec797799a210197b0c26f5393453987ff9
    $ git log --oneline origin/main..main | wc -l
    19

`origin/main` is 19 commits behind, and §E says so itself ("six commits sit
local" - it is nineteen). Two of the three floors the task is about arrived in
that gap: `79e0c2d` carries #185's `arm_floor = 9`, and `3c0bf6b`/`c790727` are
also only local. Cutting from `origin/main` would have produced a branch where
the finding did not exist and every measurement below read differently. **Cut
from `main` at `39c3e2e`.**

**0.2 §C.2 NAMES THE WRONG AXIS.** It says *"the row-count derivation must work
for a `.py`"*. The axis is not the language. Of the four members outside the old
container, the two whose row count cannot be derived statically are
`docs/reviews/probe-131-gate-state.sh` - **a `.sh`** - and
`docs/reviews/probe-wired-checker-amputation.py`. What they share is that the
count is BUILT AT RUN TIME:

    probe-131-gate-state.sh          TOTAL=$((TOTAL + 1)) at NINE sites,
                                     two of them inside functions called
                                     more than once. Live TOTAL is 12.
    probe-wired-checker-amputation.py  rows = len(ARMS) + 2 * halves,
                                     where `halves` is a loop count.

Meanwhile the two `.py` members that CAN be counted statically are counted
statically, exactly and tightly. A fix scoped to "make it work for Python"
would have covered the wrong two files.

**0.3 THE BRIEF'S CONTAINER MEASUREMENT IS CORRECT, and my first selector was
not.** §B's 29/25/4 split reproduces exactly. But my first re-derivation used

    ^[^#]*\b[A-Za-z_][A-Za-z0-9_]*floor[A-Za-z0-9_]*\s*=\s*[0-9]+\b

which requires at least one character before the word, and it therefore MISSED
`    floor = 14` in `probe-wired-checker-amputation.py` - one of the three
CI-wired floors the task exists for. The brief warned "my regex may have missed
a fourth spelling"; what actually happened is that my regex missed one of the
three the brief had already named. That miss is why the shipped rule is
structural and why arm A2 exists.

## 1. The container, BEFORE

    $ python3 docs/reviews/check-row-floor-exactness.py
    Harnesses checked for exactness: 25
    Harnesses carrying BOTH floors, checked for agreement: 8
    Harnesses whose --min-rows was compared to a live count: 16
    Every floor equals its harness's live row count. OK.
    EXIT=0

25 checked. The container was `SCRIPTS.glob("*.sh")` carrying
`^\s*ROW_FLOOR=(\d+)\s*$`. Re-derived by KIND at `39c3e2e`, tracked `.py`/`.sh`
under `docs/reviews/` and `scripts/`, identifier containing `floor` assigned an
integer literal:

    32 floor assignment sites in 31 files
     3 of them ZERO-valued (not floors - see §3)
    29 members
    25 inside the old container
     4 outside it:

       WIRED    docs/reviews/probe-131-gate-state.sh            ROW_FLOOR=12
       WIRED    docs/reviews/probe-wired-checker-amputation.py  floor = 14
       WIRED    scripts/check-secrets-baseline.py               arm_floor = 9
       unwired  docs/reviews/probe-gate-swallowed-exceptions.py ROW_FLOOR = 7

Wiring verified in `.github/workflows/ci.yml`: `:1244`, `:1889`, `:1681`. The
fourth appears in no workflow.

**So the guarantee the checker's docstring makes - "the next harness cannot be
added without being covered" - was true of 25 of 29 members and said nothing
about 4, three of which run in CI. It reported EXIT=0 the whole time.**

## 2. The container, AFTER

    $ python3 docs/reviews/check-row-floor-exactness.py
    CONTAINER: tracked .py, .sh under docs/reviews/, scripts/ carrying a literal floor
      members (floor > 0)                                   30
      named by the control TABLE - EQUAL both directions     30
      of those, row count COMPUTED at run time (#193)         2
          docs/reviews/probe-131-gate-state.sh
          docs/reviews/probe-wired-checker-amputation.py
      0-means-absent sites, each registered with a reason     3
          docs/reviews/check-coverage-floors.py  `branch_floor`
          docs/reviews/check-coverage-floors.py  `line_floor`
          scripts/lib/harness-result.sh  `HR_FLOOR`

    Harnesses checked for exactness: 30
    Harnesses carrying BOTH floors, checked for agreement: 8
    Harnesses whose --min-rows was compared to a live count: 16
    Every floor equals its harness's live row count. OK.
    EXIT=0

**29 -> 30, not 29.** The thirtieth is `check-row-floor-exactness.py` itself:
its new `--self-test` carries `arm_floor = 16`, which puts the checker inside
its own container and requires it to have a table row like everything else.
That is the correct outcome rather than an awkward one, and it is the sharpest
demonstration that the container is real.

Four new floors are now compared to a row count, and all four are TIGHT:

    docs/reviews/probe-gate-swallowed-exceptions.py   floor 7   rows 7
    scripts/check-secrets-baseline.py                 floor 9   rows 9
    docs/reviews/check-row-floor-exactness.py         floor 16  rows 16
    docs/reviews/probe-131-gate-state.sh              floor 12  COMPUTED
    docs/reviews/probe-wired-checker-amputation.py    floor 14  COMPUTED

The two static counts were validated against ground truth by RUNNING the
harnesses before writing the EREs: `7/7 rows ran.` and
`secrets-baseline-controls: arms=9 failed=0 floor=9 status=ok`.

## 3. What the fix is, and the four rules it rests on

**3.1 THE VOCABULARY IS DERIVED.** An identifier whose NAME contains `floor`,
assigned an integer LITERAL, as the whole of the line. Not a list of the three
live spellings - a list is blind to the fourth, which is the finding one level
up, and my own first selector proved it by missing one of the three (§0.3).
`ROW_FLOOR=$TOTAL` is excluded: it equals the count by construction.

**3.2 A LITERAL ZERO IS NOT A FLOOR, and that rule is the repository's, not
mine.** `scripts/lib/harness-result.sh` says *"Pass 0 as the floor for a
harness that has none; 0 is not a floor anything can breach, and it reads as
absent"*, and `check-coverage-floors.py` independently acts on the same reading
with `if line_floor == 0: continue`. Preferring a signal the language already
carries over a marker I invent is the rule here.

**But a zero is never silently dropped**, because a harness whose floor
regressed to 0 must not look identical to a non-member. Every zero site is in
`ZERO_IS_ABSENT` with a reason, an unregistered zero is a finding (arm A12), and
a registration that no longer resolves is a finding too (arm A13).

**3.3 TWO COUNTING RULES, AND THE ERE SAYS WHICH.** By default every match is a
row. A `(?P<label>...)` NAMED group switches to counting DISTINCT labels.

This was necessary, not decorative: `probe-gate-swallowed-exceptions.py` has
EIGHT `row(` sites and prints SEVEN rows (its E row is written once in the try
branch and once in the except); `check-secrets-baseline.py` has ELEVEN `arm(`
sites and prints NINE. Counting sites reports SLACK that does not exist. The
alternative - a negative number in the EXTRA column - would have been a
hand-kept constant beside a container, which is the shape this file deletes.

**The group must be NAMED.** An unnamed group would have silently changed the
meaning of two EREs already in the table: `^control (MUT|AMP) ` would have
counted 2 rows against a floor of 15. Arm A10 pins that.

**3.4 A COMPUTED ROW COUNT IS SAID PER FILE, NEVER SKIPPED.** The literal token
`COMPUTED` in the ERE column. It lives IN the table, so the container equality
still holds in both directions and the default for a new member stays RED.

## 4. §C.4 - `probe-gate-swallowed-exceptions.py`, DECIDED

**It is IN the container, and its unwired status is irrelevant to the claim.**

The reason is derived rather than preferred: static exactness needs no run.
Nothing about comparing a literal floor to a count of row openers in the source
depends on anything executing it, so "unwired" cannot be a reason to exclude a
member from THIS claim. Its floor is now checked, and it is tight at 7/7.

Its unwired status IS already recorded, in the register that exists for it -
`docs/reviews/check-checkers-are-wired.py:377` - as *"the record of an R-round
analysis of two S110 swallows in wired gates ... re-runnable, not a condition
to keep checking."* That register is consulted by a different checker for a
different question, and no second copy of the reason was added here.

## 5. Every floor WATCHED FIRING

Method: delete one line, run `check-row-floor-exactness.py`, restore from a
backup, compare byte-for-byte against the backup AND against the index, run
again. Full transcript reproducible with the loop in §9.

    ########## M1 docs/reviews/probe-gate-swallowed-exceptions.py, row G deleted
      RED   exit=1   floor 7  rows 6
                     "floor 7 exceeds its 6 rows, so the harness cannot
                      pass its own floor."
      restored byte-identical, and identical to the index
      GREEN exit=0   "Every floor equals its harness's live row count. OK."

    ########## M2 scripts/check-secrets-baseline.py, arm C9 deleted
      RED   exit=1   floor 9  rows 8
      restored byte-identical, and identical to the index
      GREEN exit=0

    ########## M3 docs/reviews/probe-131-gate-state.sh, ROW_FLOOR=12 deleted
      RED   exit=1   "named by the control table but carries no literal floor"
                     "no literal floor assignment"
      restored byte-identical, and identical to the index
      GREEN exit=0

    ########## M4 docs/reviews/probe-wired-checker-amputation.py, `floor = 14` deleted
      RED   exit=1   same two lines
      restored byte-identical, and identical to the index
      GREEN exit=0

    ########## M5 the FOURTH-LOCATION tripwire, end to end through main()
      plant src/_probe_187_smoke.py containing `GATE_FLOOR = 4`, git add -N
      RED   exit=1   "src/_probe_187_smoke.py: `GATE_FLOOR = 4` is a floor in
                      a FOURTH LOCATION - outside docs/reviews, scripts."
      removed; `git status --porcelain src/` reports 0 paths
      GREEN exit=0

M3 and M4 are membership arms rather than row-count arms, because those two are
`COMPUTED` and the checker deliberately makes no row claim about them. What is
watched there is that they are IN the container and cannot silently leave it.
**Their FIRING - a lost row taking the harness red - is still unwatched by
anything, and that is task #194, not a thing this branch closes.**

## 6. The arm that goes red on a fourth spelling or a fourth location

`python3 docs/reviews/check-row-floor-exactness.py --self-test`, 16 arms,
`arm_floor = 16`, EXIT=0, `fired=16/16 status=ok`.

    PASS  A1 a spelling that exists NOWHERE in this repository is matched
    PASS  A2 all three LIVE spellings are matched by the one rule
    PASS  A3 NEGATIVE CONTROL: an identifier without `floor` is invisible
    PASS  A4 a computed floor is NOT a floor
    PASS  A5 a floor inside prose or a comment is NOT a floor
    PASS  A6 a floor planted in a THIRD directory is SEEN repo-wide
    PASS  A7 the plant was REMOVED - the tree is as it was
    PASS  A8 the same planted floor is NOT in the default container
    PASS  A9 trimming CONTAINER_DIRS back to scripts/ LOSES members
    PASS  A10 an UNNAMED group does not switch on distinct-label counting
    PASS  A11 a NAMED `label` group counts DISTINCT labels
    PASS  A12 an UNREGISTERED zero floor is a finding
    PASS  A13 a STALE registration is a finding
    PASS  A14 a member the TABLE does not name is a finding
    PASS  A15 a TABLE row with no floor on disk is a finding
    PASS  A16 the container is NOT empty

**A FOURTH SPELLING needs no arm to be caught - the rule is structural - so A1
and A2 prove the rule is structural, and A3 states the bound it really has: the
vocabulary is the WORD `floor`, so a floor named `MIN_ROWS` would be outside it.
That is a limit to know, not a defect to hide.**

**A FOURTH LOCATION is caught by a tripwire, not by an arm.** The same selector
runs over the whole repository and anything outside `CONTAINER_DIRS` fails the
run. It reads zero today - `floor_sites(".")` and `floor_sites()` return the
same 32 sites - and A6 makes that zero non-vacuous by planting one in `src/`.
A7 proves the plant came back out.

**A14 CAUGHT A REAL DEFECT IN MY OWN FIX, on its first run.** My first design
had a second coverage route: a member the table did not name was accepted if it
PUBLISHED a canonical `HARNESS-RESULT` line, derived by reading the file. A14
deletes u7's table row and requires a finding - and it FAILED, because every
shell harness under `scripts/` sources `harness-result.sh`, so all 25 of them
would have silently reclassified from "covered" to "publishes" if their table
row were ever deleted. That is a coverage REGRESSION versus the code I was
fixing, built into the fix, and it is the third time on this project a fix has
rebuilt its own defect one column over. `publishes()` is deleted; the token
`COMPUTED` in the table replaces it, and the default stays red.

## 7. Two files changed

**`docs/reviews/check-row-floor-exactness.py`**

* `CONTAINER_DIRS`, `CONTAINER_SUFFIXES`, `FLOOR_ASSIGN`, `ZERO_IS_ABSENT`,
  `_tracked()`, `floor_sites()` - the container.
* `table_path()` - column 1 of the table is a repo-relative PATH; a bare name
  still means `scripts/<name>`, so 25 rows are unchanged.
* `static_rows()` - the two counting rules of §3.3.
* `_container_gap()` - the fourth-location tripwire, the zero register in both
  directions, and the equality in both directions over paths.
* The `--min-rows` agreement loop now finds the internal floor by the container
  rule too. It was `FLOOR_RE.search(text)`, which would have read a harness
  spelling its floor `arm_floor = 9` as having no internal floor, skipped the
  agreement check and not said so - #187's own defect one layer over, latent.
* `FLOOR_RE` is **DELETED**, not left beside the new rule. All three of its call
  sites are gone; a second floor regex kept "for the shell case" is how this
  class of defect propagates. `check-row-floors.py` keeps that spelling for its
  own narrower question, which is a different claim about a different set.
* `self_test()` and `--self-test`.
* The docstring gains **THE FOURTH CLAIM** and its "WHAT THIS STILL DOES NOT
  COVER" paragraph is REWRITTEN IN PLACE, not appended to.

**`docs/reviews/check-row-floor-controls.sh`**

* Five new TABLE rows (the four outsiders plus the checker itself).
* Column 1 is a path; `S=` resolves `*/*` as repo-relative.
* Mode `static`: this control mutates bash with the `:` builtin, syntax-checks
  with `bash -n`, runs with `bash` and parses a line from a bash library. On a
  Python harness every one of those measures the interpreter, so it REFUSES at
  exit 4 with the reason, rather than producing a red that says nothing about a
  floor. Watched:

      $ bash docs/reviews/check-row-floor-controls.sh scripts/check-secrets-baseline.py
      REFUSED: scripts/check-secrets-baseline.py is a mode=static row.
        ...
        Its EXACTNESS is checked - check-row-floor-exactness.py names it.
        Its FIRING is not watched by anything yet; that is task #194.
      rc=4

  Columns 1-3 of those rows are fully live, so they are not inoperative entries.
* The stale sentence *"check-row-floor-exactness.py now enumerates scripts/*.sh
  for a literal ROW_FLOOR"* is REWRITTEN IN PLACE with the history under it.

## 8. The full gate, run before folding

    uv run --frozen ruff check .                                  EXIT=0  All checks passed!
    uv run --frozen ruff format --check .                         EXIT=0  137 files already formatted
    uv run --frozen mypy                                          EXIT=0  no issues in 137 source files
    uv run --frozen pytest                                        EXIT=0  887 passed, 6 deselected, 0 SKIPPED
    printf '%s\n' "$out" | bash scripts/check-suite-floor.sh 887   EXIT=0  suite floor OK: 887, floor 887
    python3 scripts/check-harness-anchors.py --self-check --floor 464   EXIT=0  all 464 anchors resolve
    python3 docs/reviews/check-row-floor-exactness.py             EXIT=0  30 checked
    python3 docs/reviews/check-row-floor-exactness.py --self-test EXIT=0  16/16
    python3 docs/reviews/check-row-floors.py                      EXIT=0
    python3 docs/reviews/check-checkers-are-wired.py              EXIT=0
    python3 docs/reviews/check-checkers-are-wired.py --self-test  EXIT=0
    python3 docs/reviews/check-obligations.py                     EXIT=0
    python3 docs/reviews/check-no-errexit.py                      EXIT=0
    python3 docs/reviews/check-design-freeze.py                   EXIT=0
    python3 docs/reviews/check-cross-references.py                EXIT=0
    python3 docs/reviews/check-adr-numbers.py                     EXIT=0
    bash docs/reviews/check-harness-result.sh                     EXIT=0
    python3 scripts/check-committed-file-types.py                 EXIT=0
    python3 scripts/check-timeout-literals.py                     EXIT=0

Both floors DERIVED from `ci.yml` rather than typed from a brief:

    $ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
    check-suite-floor.sh 887
    $ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
    check-harness-anchors.py --self-check --floor 464

`ruff check` was RED twice on this branch, both W505 doc-line-too-long in my own
new comments, both fixed at the source line. `ruff format` reformatted the file
once; every gate above was re-run after that.

**`actionlint` is NOT installed on this machine.** I did not run it and I am not
claiming that gate. No workflow file is touched by this branch, so its input is
unchanged.

## 9. The ONE ci.yml step this hands over, RUN FIRST

`ci.yml` is the orchestrator's, so this is a handover rather than an edit. Add
beside the existing exactness step at `:1200`:

      - name: The floor container's own arms
        run: python3 docs/reviews/check-row-floor-exactness.py --self-test

Run from this worktree, verbatim:

    $ python3 docs/reviews/check-row-floor-exactness.py --self-test
    ...
    HARNESS-RESULT name=check-row-floor-exactness.py rows=16 floor=16 fired=16/16 status=ok
    EXIT=0

Runtime under one second. It plants and removes one file under `src/` (arm A6),
so it is a tree-touching step - but it removes the plant in a `finally` and A7
asserts the removal, which is why it can share a job with its subject where
`check-row-floor-controls.sh` cannot.

**Until that step lands, the sixteen arms are run by nobody.** That is the whole
class #125 exists for and it should not be left implicit.

Reproducer for the §5 transcript, from this worktree:

    run() { PYTHONDONTWRITEBYTECODE=1 python3 \
      docs/reviews/check-row-floor-exactness.py; echo "exit=$?"; }
    cp docs/reviews/probe-gate-swallowed-exceptions.py /tmp/bak
    sed -i '212d' docs/reviews/probe-gate-swallowed-exceptions.py
    run
    cp /tmp/bak docs/reviews/probe-gate-swallowed-exceptions.py
    git diff --quiet -- docs/reviews/probe-gate-swallowed-exceptions.py && echo restored
    run

## 10. Tasks raised

* **#193** - the two `COMPUTED` members publish `rows=` and `floor=` on one
  canonical line from a CI run, and nothing asserts EQUALITY. Both are tight
  today (12/12, 14/14, measured by hand) and `rows >= floor` is a lower bound,
  which is the defect this file's docstring opens with. The fix belongs in
  `check-harness-result.sh`, a consumer of run output.
* **#194** - the two `static` members are checked for exactness and their FIRING
  has never been watched, because the control is bash-only. And a second finding
  falls out of it: **neither emits a canonical `HARNESS-RESULT name=` line at
  all** - one prints `7/7 rows ran.`, the other
  `secrets-baseline-controls: arms=9 ...`. #107's "37 of 37 emit one canonical
  line" stops at the same `scripts/*.sh` boundary this task found the floor
  container stopping at. A Python arm has nothing to parse until that is fixed.

## 11. What I did NOT verify

* **`actionlint`.** Not installed here (§8). No workflow file is modified.
* **CI.** Nothing on this branch has been near a runner. The two paths I cannot
  reproduce locally are the `git ls-files` behaviour under `actions/checkout`'s
  shallow clone - `_tracked()` uses `git ls-files`, which reads the index and
  not history, so I expect it to be identical, but I have not seen it there -
  and arm A6's write into `src/` on a runner filesystem.
* **Whether all 30 floors are DERIVED rather than typed-and-lucky.** The
  checker's own docstring says only running each harness answers that, and I ran
  four of them (the four new members). The other 26 were watched by #91 and #102
  and I did not re-run them.
* **`check-row-floor-control.sh`, singular.** Untouched, not run. It targets one
  harness that was already covered.
* **The five other floor-adjacent checkers** (`check-coverage-floors.py`,
  `check-critical-coverage-*`, ...) were run only where the §8 list shows them.
  I did not audit whether any of them keeps a THIRD copy of a floor container.

## 12. Housekeeping

The worktree at `/home/plafayette/claude_projects/evolv/fmj-worktrees/w187` is
**left in place**, because the branch is unmerged and removing it would strand
the only checkout of the work. Remove it after the fold:

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        worktree remove ../../fmj-worktrees/w187

`git status --porcelain` on this branch before the commit showed exactly the two
modified files in §7 and nothing else - no stranded mutation, no plant left in
`src/`.
