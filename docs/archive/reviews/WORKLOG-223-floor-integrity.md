# WORKLOG - #223: the floor nothing watched, and the bound that only went one way

Written 2026-09-02 by `suborch-223`, branch `fix/223-floor-integrity`,
worktree `/tmp/w223-floor-integrity`, cut from LOCAL `main` at
`4f03004` (derived with `git rev-parse main`, not retyped from the
brief, which named no SHA).

Both items came out of `#194`'s report as READINGS. Both are now
measurements, and **both measurements changed the finding.**

---

## The headline, and it is two corrections to #194

### 1. `#194`'s derivation of which members have a `--self-test` is WRONG, and the refusal that produced it printed a command that does not exist

`#194` reported: *"`grep -q -- '--self-test'` over each of the three
static members returns NO for it, HAS for `check-secrets-baseline.py`
and `check-row-floor-exactness.py`."*

`check-secrets-baseline.py` has NEVER had a `--self-test`. The grep
matched line 372 of that file:

    # mutants have survived a `--self-test` in this repository before.

A grep for a pattern found the prose ABOUT the pattern. The same grep
lives in `check-row-floor-controls.sh`'s static refusal, so the refusal
printed a remedy that does not exist. RUN, verbatim:

    $ uv run --frozen python scripts/check-secrets-baseline.py --self-test
    usage: check-secrets-baseline.py [-h] [--controls]
    check-secrets-baseline.py: error: unrecognized arguments: --self-test
    exit: 2

That is the precise class of defect the refusal's own comment says it
exists to avoid: *"A refusal that names a remedy the file does not
carry is the same class of defect as the 'is not bash' it replaces."*

**Re-derived container.** The brief asked me to re-derive rather than
trust `#194`'s three. The table has **FOUR** `mode=static` rows, not
three (`check-row-floor-controls.sh:191,192,194,197`), because `#194`
itself moved `probe-wired-checker-amputation.py` into that mode. With
the corrected discriminator - the DOUBLE-QUOTED form, which is how a
flag is written in code and not how it is written in prose:

| static member | `"--self-test"` | what actually arms its floor |
|---|---|---|
| `docs/reviews/probe-gate-swallowed-exceptions.py` | NO (was NO) | **nothing, before this task** |
| `scripts/check-secrets-baseline.py` | **NO (was a false HAS)** | its own `--controls`, plus the exactness checker |
| `docs/reviews/probe-wired-checker-amputation.py` | HAS | its `--self-test` (#194) |
| `docs/reviews/check-row-floor-exactness.py` | HAS | its `--self-test` |

So `#194`'s CONCLUSION - `probe-gate-swallowed-exceptions.py` is the
one unwatched member - **holds**, and one of its three premises was a
false positive. The corrected refusal is in the fix.

### 2. Item 2 is REAL but MUCH NARROWER than `#194` said, and I would rather say so than ship the fix under a claim that does not hold

`#194`: *"add an arm without raising the floor and nothing says so."*

The first half is measured and true. Planting a tenth arm on a scratch
copy, against the UNCHANGED gate:

    [OLD gate, arms intact]     secrets-baseline-controls: arms=9  failed=0 floor=9 status=ok
    [OLD gate, arms intact]     exit: 0
    [OLD gate, ONE ARM ADDED]   secrets-baseline-controls: arms=10 failed=0 floor=9 status=ok
    [OLD gate, ONE ARM ADDED]   exit: 0

**The second half is false.** `check-row-floor-exactness.py` statically
counts this file's `arm(` sites - that is what its table row is for -
and on the SAME plant, made in the tracked tree this time:

      scripts/check-secrets-baseline.py                    floor   9  rows  10
    1 floor(s) wrong:
      scripts/check-secrets-baseline.py: SLACK by 1. It has 10 rows and a floor of 9,
      so 1 row(s) can be deleted without the floor noticing. This is the direction
      that never announces itself.
    exactness exit: 1

`#193` scoped its equality fix to the two COMPUTED members precisely
because those are the two the exactness checker CANNOT look at. This
member is not one of them. What the `>=` cost is that the harness
printed `status=ok` over its own slack and left the whole claim to a
second file. That is worth fixing - a harness that fails on its own
evidence is the point of the container - but it is a Low, not `#193`'s
class of hole, and the report that raised it read the comparison
without asking what else was looking.

**Why the wrong belief was durable.** The comment block above that
comparison ARGUED for it:

    # check-row-floor-exactness.py enumerates `scripts/*.sh` so a `.py`
    # is outside its container by construction.

True when written; false since `#187` widened the container to tracked
`.py` and `.sh` under `scripts/` and `docs/reviews/`. A sentence
describing a container that had already moved made a lower bound look
harmless. It is rewritten in place, not annotated.

---

## THE TRAP, and I did not walk into it

The brief states it as a property: a row-floor harness has TWO
independent failure modes and the assertions for them are blind to each
other. On `main` the wired-checker probe reads `rows=14 floor=14
fired=12/14` - floor satisfied, only the tally catching it. `#194`'s
arm S4 covers the reverse.

Both directions are asserted in both files I touched, and each is armed
by an arm that dies to its own branch and no other:

| what went wrong | `rows` vs `floor` | the failure list |
|---|---|---|
| a row was DELETED | **catches it** | reads EMPTY, blind |
| a row RAN and misbehaved | satisfied, blind | **catches it** |

- `probe-gate-swallowed-exceptions.py`: **S2/S3/S6** hold the first
  column, **S5** holds the second, **S4** holds the ADD direction that
  neither column had.
- `check-secrets-baseline.py`: **C11** holds the first, the `if failed`
  branch holds the second, **C10** holds the ADD direction.

---

## Item 1 - `probe-gate-swallowed-exceptions.py`

### `#194`'s suggested fix cannot be built, and I planted it rather than reasoning about it

Suggested: *"extract its verdict into one function and arm it, with its
own `arm_floor`; the two-floor permission this task added is what makes
that possible without a table change."*

Planted `arm_floor = 3` under `ROW_FLOOR = 7` in the tracked file and
ran the checker:

    1 floor(s) wrong:
      docs/reviews/probe-gate-swallowed-exceptions.py: 2 floor assignments
      (ROW_FLOOR, arm_floor) and nothing says which one the table's row count
      is about.
    exactness exit: 1

    --- proof of RESTORE ---
    restore: git diff --quiet exit: 0
    0

The permission does NOT stretch. It is written for COMPUTED rows -
*"for a COMPUTED row it compares NOTHING"* - and this row's count is
static and correctly compared (7 distinct `[A-G].` labels against
`ROW_FLOOR = 7`). Turning the row COMPUTED to buy the permission would
throw away a working static check to make room for a second one.

### What I built instead: a name list, not a number

`verdict(ran, floor, failures)` is extracted from the file's tail;
the live run calls it and so does a new `--self-test`. The arm set is
held by `SELF_TEST_ARMS`, a tuple of labels, asserted by arm S8 in both
directions.

That is a floor by another mechanism and the choice is deliberate.
**A floor buys a two-place edit** - to defeat it you must delete the row
AND lower the number. A name list buys exactly the same thing: delete
the arm AND delete its name. What it does not buy is an integer for
`floor_sites()` to find, so no ambiguity is created for a static row.
`#194`'s own S9 arm is the same device. This is not hiding a floor from
the container: the container's question is *"which floor is the table's
row count about"*, and a tuple of strings is not an answer it can
mistake.

### The run

    $ uv run --frozen python docs/reviews/probe-gate-swallowed-exceptions.py --self-test
    PASS  S1  a full row set with no failures is exit 0
    PASS  S2  DELETE one row and the floor BREACHES: exit 1
    PASS  S3  the breach SAYS a row was lost rather than exiting quietly
    PASS  S4  an ADDED row against an unraised floor also breaches
    PASS  S5  THE OTHER DIRECTION: the floor is SATISFIED and only the failure
              list catches a row that ran and misbehaved
    PASS  S6  a run that executed NO rows is a breach, not a green
    PASS  S7  ROW_FLOOR is exactly ONE literal assignment the container can see
    PASS  S8  SELF_TEST_ARMS names exactly these arms, in order, with no
              duplicate label - deleting an arm takes a two-place edit
      8/8 self-test arms ran.
    self-test exit: 0

`ROW_FLOOR`'s comparison is EQUALITY now, not `len(RAN) < ROW_FLOOR`.
S4 is the arm that direction never had.

### THE END-TO-END WATCH - the thing nothing had ever done

The self-test is in-process. It does not prove the LIVE floor fires. So
row G was deleted from the TRACKED file and the probe run:

    --- BASELINE, unmutated ---
      7/7 rows ran.
      every row behaved. Both swallows now catch only what they name.
    baseline exit: 0
    --- proof the deletion LANDED (row G gone, 6 labelled row sites left) ---
    1
    6
    --- THE FLOOR FIRING ---
      6/7 rows ran.
      ONLY 6 of 7 rows ran. A partial run is not a pass.
    breached exit: 1

**Restore, and the instrument I used first was the WRONG ONE.**
`git diff --quiet` reported DIRTY, and that was correct and useless:
the tree carries my own uncommitted fix, so the index is not the
reference the restore writes from. Compared against the backup, which
is:

    $ diff -q /tmp/223-swallow2.bak docs/reviews/probe-gate-swallowed-exceptions.py
    diff-vs-backup exit: 0
    post-restore live exit: 0

### Three ISOLATED amputations of `verdict()`, one branch each

Scratch copies under `mktemp` - `--self-test` exits before any row
runs, so a copy is a complete subject. Each anchor asserted unique
before substitution; a `sed` matching nothing succeeds silently.

| # | The ONE thing amputated | Arms killed |
|---|---|---|
| V1 | the `if ran < floor:` branch | **S2, S3, S6** - exit 1 |
| V2 | the `if ran > floor:` branch | **S4** - exit 1 |
| V3 | the `if failures:` branch | **S5** - exit 1 |

Three disjoint sets. That is what says they test three branches rather
than one thing three times.

### The dependent harness still passes, and that was not assumed

`probe-docs-lint-amputation.py` amputates the two guarded call sites
and asserts WHICH rows of this probe die. It watches the FAILURE half
of the verdict I just refactored:

    ########## A3 _corpus() catch widened back to Exception CAUGHT: probe rc=1, rows killed = ['C'] (expected ['C'])
    ########## A4 drive_to() catch widened back to Exception CAUGHT: probe rc=1, rows killed = ['F'] (expected ['F'])
    ########## A5 NEGATIVE CONTROL, comment-only edit CAUGHT: probe rc=0, rows killed = NONE (expected NONE)
      post-run re-check of probe-gate-swallowed-exceptions.py: exit=0 failed=none
      every amputation was caught, the control survived, the tree is clean.
    docs-lint amputation exit: 0

This is also the answer to *"why was only one half unwatched"*: the
failure half already had a watcher, in another file, by a different
mechanism. The floor half had none.

---

## Item 2 - `scripts/check-secrets-baseline.py`

`arm_verdict(arms, floor, failed)` extracted, equality, two distinct
messages carrying `#193`'s shape. `arm_floor` 9 -> 11 for the two arms
that arm it.

    PASS  C10 an ADDED arm against an unraised floor is a breach
    PASS  C11 a DELETED arm is a breach, in the other direction
    secrets-baseline-controls: arms=11 failed=0 floor=11 status=ok
    exit: 0

The SAME plant that was green before the fix:

    [ONE ARM ADDED]  secrets-baseline-controls: arms=12 failed=0 floor=11 status=breach
    [ONE ARM ADDED]  exit: 1

Two ISOLATED amputations, scratch copies, disjoint:

| # | The ONE thing amputated | Arms killed |
|---|---|---|
| V1 | the `if arms > floor:` branch | **C10** - exit 1 |
| V2 | the `if arms < floor:` branch | **C11** - exit 1 |

---

## Item 3 (not in the brief, found while re-deriving) - the refusal's grep

Fixed at the discriminator, not at the prose. Requiring the
DOUBLE-QUOTED `"--self-test"` separates `add_argument("--self-test")`
and `"--self-test" in sys.argv` from every backticked mention. Measured
over all four static members: HAS for exactly the two that have the
flag, NO for the two that do not.

I did NOT rewrite the sentence in `check-secrets-baseline.py` that
triggered it. Deleting the mention would fix this instance and leave
the instrument that produced it intact, and a defect grep finding its
own documentation is a class, not an incident.

The NO branch also no longer asserts *"nothing watches its floor fire"*
- for `check-secrets-baseline.py` that would have been a NEW false
claim, since `--controls` and the exactness checker both watch it. It
now says what it derived and points the reader at the argparse block.

*Suggested follow-up (not done, outside this brief):* the refusal asks
about ONE flag name. A member arming its floor behind any other name
reads as a gap. A cheap improvement is to derive the file's declared
flags rather than test one; I did not build it because the obvious
implementation - grepping quoted `--x` tokens - also picks up
subprocess arguments like `--porcelain` and `--exclude-standard`, which
would trade a false NO for a false HAS.

---

## Every gate, exit code on its own line

Read one at a time. No `cmd && echo OK` anywhere.

    ruff check .                                          exit 0
    ruff format --check .                                 exit 0
    mypy                                                  exit 0   (141 files)
    shellcheck --severity=warning -x docs/reviews/*.sh    exit 0
    check-row-floor-exactness.py                          exit 0   (32 members, 32 named)
    check-row-floor-exactness.py --self-test              exit 0   (20/20)
    check-checkers-are-wired.py                           exit 0
    check-checkers-are-wired.py --self-test               exit 0
    check-row-floor-controls.sh --list                    exit 0   (32 rows)
    probe-wired-checker-amputation.py                     exit 0
    probe-wired-checker-amputation.py --self-test         exit 0   (11/11)
    probe-gate-swallowed-exceptions.py                    exit 0   (7/7)
    probe-gate-swallowed-exceptions.py --self-test        exit 0   (8/8)
    probe-docs-lint-amputation.py                         exit 0
    probe-floor-checker-planted-defect.sh                 exit 0
    check-row-floors.py                                   exit 0
    check-brief-report-references.py                       exit 0
    check-obligations.py                                  exit 0   (31 mappings, 25 verified, 6 absent)
    check-harness-anchors.py --self-check --floor 464     exit 0
    uv run --frozen pytest                                exit 0   887 passed, 0 skipped

Both floors were READ out of `ci.yml`, not typed:

    check-suite-floor.sh 887
    check-harness-anchors.py --self-check --floor 464

**`ruff check .` was RED on my first pass** - one W505, 73 > 72, in a
docstring line I had just written. Recorded because a report showing
only the green run is showing the second run.

**`actionlint` is NOT installed here** and I did not run it. No claim.

---

## What I did NOT verify

- **CI.** Nothing here has run on a runner. `ci.yml` is UNCHANGED by
  this branch - see the wiring decision below - so there is no new step
  to run, but the runner's own checkout and ordering are untested.
- **`actionlint`** - not installed, said plainly rather than claimed.
- **Whether the new `--self-test` should be WIRED.**
  `probe-gate-swallowed-exceptions.py` is `UNWIRED_BY_DECISION` in
  `check-checkers-are-wired.py` - *"the record of an R-round analysis
  ... not a condition to keep checking"*. `#194` wired ITS self-test
  because its subject was already wired; mine is not, and adding a CI
  step for a file the container calls a record is Tier 0's call, not
  mine. The step, if you want it, is one line of the same shape as its
  neighbours and I ran its exact invocation locally (exit 0 above):

        - name: That probe's own floor still fires
          run: uv run --frozen python docs/reviews/probe-gate-swallowed-exceptions.py --self-test || exit 1

  `|| exit 1`, never chained with `&&`: under `bash -e` only the LAST
  command of an AND-list triggers errexit, and that shape has hidden a
  red on this project three times.
- **Whether `SELF_TEST_ARMS` is the right general mechanism**, or
  whether the exactness checker should instead learn to resolve a
  two-floor static row by NAME (a table cell saying which floor its
  count is about, mirroring `#194`'s `COMPUTED` token). I did not build
  that: it is a checker + table + arms design change, it would need
  A19/A20 rewritten, and one agent deciding it inside a fix brief is
  how a merge puts damage back. It is the durable answer if a THIRD
  static member ever wants a second harness.
- **Whether any other member's floor is watched by prose rather than
  code.** I corrected the one grep that produced a false HAS; I did not
  sweep the repo for other greps whose pattern can appear in their own
  documentation. `#194`'s finding 3 is the same family.
- **The other three `mode=static` members' self-tests actually ARM
  their floors.** I ran the two that have the flag and read their
  output; I amputated only the two files this task names.

---

## Housekeeping

- Worktree `/tmp/w223-floor-integrity` is LEFT IN PLACE, as the brief
  asked, on `fix/223-floor-integrity`. `git worktree list` was run
  before any ref moved; no other worktree was touched and nothing was
  checked out in the shared checkout.
- Nothing pushed, nothing merged.
- No Tier-2 workers spawned. Every step here was one or two tool calls.
- `git status --porcelain` is empty apart from this report, which lands
  in the commit below.
