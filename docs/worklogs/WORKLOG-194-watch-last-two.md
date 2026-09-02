# WORKLOG — #194: the last two floors, watched fire by two DIFFERENT mechanisms

Written 2026-09-02, `suborch-194`, branch `fix/194-watch-last-two`,
worktree `/home/plafayette/claude_projects/evolv/fmj-worktrees/w194b`,
cut from LOCAL `main` at `ed8bc60`. Local `main` is **63 commits ahead of
`origin/main`** (`git rev-list --count origin/main..main`) — derived, not
retyped from the brief, which named no number.

**BOTH FLOORS ARE NOW WATCHED FIRING, red then green, tree restored.**
The two mechanisms are different because the two blockers are different,
exactly as the refusal at `72fe217` said.

---

## The headline, and it is a correction to the brief

**§C's second bullet is wrong in a way that would have failed the gate.**
It says a self-test's own `arm_floor` "puts it in
`check-row-floor-exactness.py`'s container and therefore requires a
control-table row like every other member".

Two errors:

1. `docs/reviews/probe-wired-checker-amputation.py` was **already** a
   table member (`check-row-floor-controls.sh:161` before this change).
   The container keys on the FILE, so a second floor in it adds no new
   membership requirement.
2. A second floor in one file is a **HARD FAILURE** of the exactness
   checker, and I measured it rather than reasoning about it. With
   `arm_floor` added and nothing else changed:

       docs/reviews/probe-wired-checker-amputation.py: 2 floor
       assignments (FLOOR, arm_floor) and nothing says which one the
       table's row count is about.

   exit 1. That refusal lives at `check-row-floor-exactness.py:735-741`
   as it stood on `main`, and it runs BEFORE the `COMPUTED` branch, so
   the token could not save it.

So the brief's Part 2 could not be built as written. The resolution is
in "The third change" below, and it is deliberately narrow.

---

## Part 1 — `probe-131-gate-state.sh`: a COMPUTED count IS watchable

### The mechanism

A new `mode=computed` in `docs/reviews/check-row-floor-controls.sh`.
Nothing predicts the count; it is READ:

```
run it once     -> rows=N floor=N status=ok rc=0     (ASSERTED, not read)
delete ONE row  -> rows=N-1 status=breach rc=<col 4>
restore         -> byte-identical to the backup AND to the index
```

The table cell keeps `COMPUTED` as its FIRST WORD and carries the
deletion ERE after it:

    docs/reviews/probe-131-gate-state.sh|COMPUTED ^row \"|0|1|computed

One cell, two consumers. `check-row-floor-exactness.py` selects on the
token to skip its static comparison; this control uses the rest. That is
why `is_computed()` is a token test, not the equality it replaced — an
equality read `COMPUTED ^row "` as an ordinary regex, matched ZERO rows,
and reported the floor as impossible. **I measured that red before
fixing it**, and it is a red nobody would have traced to a string
comparison.

`^row "` was derived from the file, not guessed: `grep -n '^row "'`
gives three sites (lines 111, 137, 187 as the file stands), each of
which increments `TOTAL` inside `row()`. Neutralising one with the `:`
builtin removes exactly one counted row — the same surgery every `cmd`
row already uses.

### The run — WATCHED FIRING

    $ bash docs/reviews/check-row-floor-controls.sh docs/reviews/probe-131-gate-state.sh
    --- baseline run: READING the row count rather than predicting it ---
    HARNESS-RESULT name=probe-131-gate-state.sh rows=12 floor=12 fired=12/12 status=ok
    baseline exit: 0
    floor (from source): 12
    rows               : 12  (READ from the baseline run; 3 site(s) match the ERE)
    rows to delete     : 1   (one is enough against a TIGHT floor)
    deleting rows at lines: 111
    row invocations still matching: 2 (was 3, must be 2)
    restored: byte-identical to the backup
    restored: and identical to the index
    HARNESS-RESULT name=probe-131-gate-state.sh rows=11 floor=12 fired=11/11 status=breach
    exit with 1 row(s) deleted: 1 (must be 1)
    CONTROL FIRED
    exit 0

### WHICH ASSERTION CAUGHT WHAT — the `fired=N/N` trap, measured

The breach line reads **`fired=11/11`**. Every surviving row still
fired. A checker reading the tally would see a full tally and pass a
harness that had lost a row: `fired=11/11` and `fired=12/12` differ only
in a number nothing compares. **`rows=11` against `floor=12` is what
caught it**, together with `exit 1`. The control now PRINTS that rather
than leaving it to be inferred.

### Two ISOLATED amputations, one branch each

Both drive the control with `ROW_FLOOR_CONTROL_ALLOW_PLANTED=1`, the
opt-in the control already names, and both restore with
`git reset HEAD --` + `git checkout --`; `git status --porcelain` was
empty afterwards each time.

| # | The ONE thing amputated | Result |
|---|---|---|
| P1 | `if [ "$TOTAL" -ne "$ROW_FLOOR" ]; then` → `if false; then` in the probe | control **exit 1**: `status=ok, wanted breach` and `exit 0, wanted 1` |
| P2 | `ROW_FLOOR=12` → `ROW_FLOOR=11` (a SLACK floor) | control **exit 9** at the BASELINE, before mutating anything: `the baseline run is not healthy (exit 1, status=breach)` |

P1 proves the firing claim depends on the probe's own floor comparison.
P2 proves the new baseline assertion is not decoration: a control that
read the count without asserting the baseline was healthy would report a
"firing" it could not attribute.

Each anchor was asserted unique before substitution (`count(a) == 1`, or
the script raises) — a `sed` matching nothing succeeds silently.

---

## Part 2 — `probe-wired-checker-amputation.py`: its own `--self-test`

A bash control cannot drive a Python harness; an arm there measures the
interpreter. So the shape is `check-row-floor-exactness.py --self-test`,
copied and wired.

### The refactor is the point, not the arms

`verdict(rows, floor, failures)` is extracted from `main()` and returns
`(canonical line, diagnosis lines, exit code)`. `main()` calls it and so
does `--self-test`. **A self-test that re-implemented the comparison
would pass whenever its copy agreed with the original**, which they do
right up until one is edited. `FLOOR` moved to module level for the same
reason: a local would have forced the self-test to re-type the constant
the file exists to protect.

    $ uv run --frozen python docs/reviews/probe-wired-checker-amputation.py --self-test
    PASS  S1  the live arm count EQUALS the floor
    PASS  S2  a full arm set with no failures is status=ok, exit 0
    PASS  S3  DELETE one arm and the floor BREACHES: exit 1
    PASS  S4  THE TRAP: the tally reads FULL in that breach
    PASS  S5  the breach SAYS an arm was lost rather than exiting quietly
    PASS  S6  an ADDED arm against an unraised floor also breaches
    PASS  S7  a SURVIVOR breaches even with the arm count intact
    PASS  S8  an EMPTIED ARMS list is a breach, not a green
    PASS  S9  EXPECTED names exactly the ARMS, both directions
    PASS  S10 no two ARMS share a label
    PASS  S11 both floors are literal assignments the container can see
    HARNESS-RESULT name=probe-wired-checker-amputation.py rows=11 floor=11 fired=11/11 status=ok
    exit 0

`arm_floor = 11`. S3 is the arm nothing had ever run.

### WHICH ASSERTION CAUGHT WHAT — the same trap, arm S4

With one arm deleted the line reads `rows=13 floor=14 fired=13/13
status=breach`. **S4 asserts the `13/13`** — it is a positive assertion
that the tally is USELESS here, not an oversight. Only `rows` against
`floor` separates a healthy 14-arm run from a 13-arm one.

### Two ISOLATED amputations of `verdict()`, one branch each

Run against a scratch copy under `mktemp -d`, so the tracked file was
never touched.

| # | The ONE thing amputated | Arms killed |
|---|---|---|
| V1 | `rows == floor` dropped from the `status=` expression | **S3, S6, S8** — exit 1 |
| V2 | the whole `if rows < floor:` branch deleted | **S3, S5, S8** — exit 1 |

The two arms differ (S6 only in V1, S5 only in V2), which is what says
they are testing different branches rather than one thing twice. A
compound amputation of BOTH killed four (S3, S5, S6, S8); it is recorded
here only to say it was split, because three confounded arms in a
sibling harness were each red for a branch they did not name.

---

## The third change — why `check-row-floor-exactness.py` had to move

**A COMPUTED member may carry more than one floor. Nothing else may.**

For a static row the two-floor refusal is right and fatal: the checker
compares a source-derived row count against A floor and with two of them
nothing says which. **For a COMPUTED row it compares NOTHING**, so the
question the refusal asks has no referent. The permission is exactly that
wide and no wider.

The per-row verdict is now `_row_exactness()`, so the self-test arms the
same code rather than a copy, and both directions are held:

- **A19** two floors are ACCEPTED on a COMPUTED row
- **A20** two floors are STILL a finding on a static row

plus **A17** (`COMPUTED <ere>` is still a COMPUTED cell) and **A18**
(NEGATIVE CONTROL: `^row "COMPUTED` is NOT — a substring test would
silently exempt any harness whose row opener quoted the word).

`arm_floor` 16 → 20. `check-row-floor-exactness.py --self-test` reports
`rows=20 floor=20 fired=20/20 status=ok`, exit 0.

The census the checker prints, unchanged in shape:

    members (floor > 0)                                   32
    named by the control TABLE - EQUAL both directions     32
    of those, row count COMPUTED at run time (#193)         2

---

## What I wired, and what I did not

**WIRED**, in the job that already runs the probe, as a SEPARATE step:

```yaml
      - name: That probe's own floor still fires
        run: uv run --frozen python docs/reviews/probe-wired-checker-amputation.py --self-test || exit 1
```

Separate, not chained onto the line above, because under `bash -e` only
the LAST command of an `&&` list triggers errexit — the shape that has
hidden a red on this project three times. `|| exit 1` gates it.

**NOT WIRED**: `mode=computed`. `check-row-floor-controls.sh` is
`UNWIRED_BY_DECISION` in `check-checkers-are-wired.py` — *"it mutates
floors to watch the checker fire; a control that must break its subject
cannot share a job with the subject"* — and that ruling is unchanged by
this task. The computed arm is run by hand, exactly as the other 29 rows
are.

---

## Every gate, exit code on its own line

Read one at a time, never `cmd >/dev/null && echo OK`.

    check-row-floor-exactness.py                         exit 0
    check-row-floor-exactness.py --self-test             exit 0   (20/20 arms)
    check-checkers-are-wired.py                          exit 0
    check-checkers-are-wired.py --self-test              exit 0
    check-row-floor-controls.sh --list                   exit 0   (32 rows)
    check-row-floor-controls.sh <the computed row>       exit 0   CONTROL FIRED
    probe-131-gate-state.sh                              exit 0   (12/12)
    probe-wired-checker-amputation.py                    exit 0   (14/14)
    probe-wired-checker-amputation.py --self-test        exit 0   (11/11)
    probe-floor-checker-planted-defect.sh                exit 0   (4/4 planted defects caught)
    check-row-floors.py                                  exit 0
    check-brief-report-references.py                     exit 0
    check-harness-anchors.py --self-check --floor <ci>   exit 0
    ruff check .                                         exit 0
    ruff format --check .                                exit 0
    mypy                                                 exit 0
    shellcheck --severity=warning -x docs/reviews/*.sh   exit 0

The anchor floor was read out of `ci.yml` rather than typed. The suite
floor in `ci.yml` reads `check-suite-floor.sh 887`; the suite was run and
its result is in the report accompanying this worklog.

**`actionlint` is NOT installed here** — `command -v actionlint` exits 1.
I did not run it and I am not claiming it passed. The `ci.yml` change is
one step of the same shape as its neighbour four lines above.

`ruff check .` was RED on my first pass — 28 W505 doc-line-too-long, all
of them mine, all in prose I had just written. Fixed by rewrapping at 72
and by breaking the two long command samples across a `\` continuation.
Recorded because a report that shows only the green run is showing the
second run.

---

## Findings I am REPORTING, not fixing (Tier 1 does not create tasks)

1. **`docs/reviews/probe-gate-swallowed-exceptions.py` has NO
   `--self-test`.** It is the one remaining `mode=static` member whose
   floor is watched by nothing at all: the bash control refuses it
   (correctly — it is Python) and the file carries no self-test flag.
   Derived, not assumed: `grep -q -- '--self-test'` over each of the
   three static members returns NO for it, HAS for
   `check-secrets-baseline.py` and `check-row-floor-exactness.py`.
   *Suggested fix:* the same shape as Part 2 — extract that probe's
   verdict into one function and arm it, with its own `arm_floor`; the
   two-floor permission this task added is what makes that possible
   without a table change.

2. **`scripts/check-secrets-baseline.py` gates its arm floor with a
   LOWER BOUND**, `len(arms) >= arm_floor` (`check-secrets-baseline.py`,
   the `arm_floor = 9` block). That is the exact direction #193 closed
   for the two COMPUTED members: add an arm without raising the floor and
   nothing says so. I did not touch it — it is outside this brief and it
   is a different file's floor. *Suggested fix:* equality, with the same
   two messages #193 used, so the SLACK direction names itself.

3. **The refusal cannot promise more than a grep.** Where a Python
   member has a `--self-test`, the refusal now says so and adds *"RUN IT.
   This refusal proves the FLAG exists; only the run says whether that
   self-test arms the floor."* I would rather it under-claimed than
   repeated the "is not bash" class of misdiagnosis it replaces.

4. **`ci.yml` is contended.** #214 (R21-L1) is an open finding about a
   census comment in `ci.yml` around the row-floor steps. My edit is at
   the other end of the file, in the wiring-probe job, and touches no
   line #214 names — but two agents in one workflow file is how a merge
   puts damage back, so this is flagged rather than assumed harmless.

---

## What I did NOT verify

- **`actionlint`** — not installed here, said plainly above rather than
  claimed. Only CI can run it.
- **Whether `check-secrets-baseline.py`'s `--self-test` actually arms its
  floor.** I read the flag and the `>=` comparison; I did not run it or
  amputate it. Finding 2 is about the comparison I read, not about a run
  I made.
- **CI.** Nothing here has run on a runner. The new step was executed
  locally with CI's exact invocation (`uv run --frozen python …
  --self-test`), and its exit code is above; the runner's own checkout,
  git identity and ordering are untested.
- **Whether the two-floor permission has other members waiting for it.**
  The census says 32 members and 2 COMPUTED; I did not enumerate whether
  any static member is one refactor away from wanting a second floor.

---

## The merge with main, and what it proved for free

Merged `main` (`507fceb`) in at `fb6483e`, and re-ran everything AFTER
the merge rather than before.

**The regression warning I was sent named the WRONG BRANCH.** The `-149`
on `check-brief-report-refs-controls.sh` and `-22` on
`probe-mirror-zero-refs.sh` belong to `fix/194-floor-firing-container`
(`7ab914c`), the abandoned earlier attempt recorded under Housekeeping
below. My branch forked at `ed8bc60`, and `8aa9150`, `5bcdb45` and
`b7b58b0` are all already ancestors of it
(`git merge-base --is-ancestor`), so neither `b7b58b0`'s rc=2 refusal nor
`5bcdb45`'s bare-name exit 2 was ever at risk here.

**ONE conflict, and taking either whole side was wrong.** In
`brief-report-refs-known-missing.txt`: kept main's `WORKLOG-208` and
`FINDINGS-213` records, took main's deletion of `REVIEW-R21` (it landed),
took my deletion of `WORKLOG-194` (it lands here). Taking HEAD drops two
live records; taking main re-records a worklog the same merge commits.
`ci.yml` auto-merged and `git diff main` over it is +16/-0, so #214's
work is intact — checked, not assumed.

**MAIN WAS ALREADY RED ON THREE GATES**, measured on plain `507fceb`:
the brief-report gate (`WORKLOG-208-orphan-leads.md` tracked AND still
recorded), `check-checkers-are-wired.py`
(`probe-stale-branch-regression.sh` unwired and unexplained), and
`probe-wired-checker-amputation.py` as a consequence of the second. None
was fixed here — each is a one-line change in a file another agent is
holding.

### THE TRAP IN REVERSE, and it is why S4 alone is not enough

Main's red is a free positive control. `probe-wired-checker-amputation.py`
reports there:

    arms=14 failures=2
    HARNESS-RESULT rows=14 floor=14 fired=12/14 status=breach

**The FLOOR is satisfied — `rows=14` against `floor=14` — and only the
TALLY catches it.** That is the exact mirror of the case this task was
about, where the tally reads full and only the floor catches the loss.
Neither assertion can see the other's case:

| what went wrong | `rows` vs `floor` | `fired=` |
|---|---|---|
| a row was DELETED | **catches it** | reads FULL, blind |
| a row FAILED | satisfied, blind | **catches it** |

Both have to be asserted, and both now are — S4 for the first column,
`verdict()`'s `if failures` branch (armed by S7) for the second.

**The `--self-test` stayed GREEN while `main()` went RED**, which is the
property that lets it share a job with its own subject: it is in-process
and never runs the checker, so the floor claim is isolated from the
subject's health.

## Housekeeping

- `docs/reviews/brief-report-refs-known-missing.txt`: the
  `WORKLOG-194-watch-last-two.md` IN FLIGHT line is DELETED in the same
  commit that lands this file, per that file's own routine.
- **The worktree named in the brief was already taken.**
  `../../fmj-worktrees/w194` exists on `fix/194-floor-firing-container`
  at `7ab914c`, 31 commits behind `main`, **with two uncommitted modified
  files** that are an earlier attempt at this same task. I did not touch,
  clean, or reuse it — cleaning an idle agent's worktree is one command
  from destroying unreported work. I cut `w194b` instead. That stale tree
  is Tier 0's to dispose of.
- I spawned ZERO Tier-2 workers. Every step here was one or two tool
  calls; a pane to save thirty seconds is a net loss. That is now six
  runs out of six.
