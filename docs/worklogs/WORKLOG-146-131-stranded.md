# WORKLOG - #146 (probe timeout attribution) and #131 (--restore-only)

Branch `fix/146-131-stranded`, cut from `9e04411`.

## What I was given, and where it was wrong

The brief's numbers were hypotheses. Four corrections, all small but all real.

**The line numbers in #146 are stale.** The task cites
`probe-harness-exit-codes.sh:110`, `:112`, `:121`. At `9e04411` the same three
sites are `:110`, `:112` and `:126` in a file that has since gained a section.
Re-derived with `grep -n`; the DEFECT is exactly as described, only the
citations had drifted. Flagged because the repo's own rule is to cite from
`grep -n` and not from a brief.

**The brief said my scope was "the probe and a new restore mode".** That is
right, but the reason is stronger than "suborch-116 owns `scripts/*.sh`": a new
file under `scripts/` would join the probe's own container (`scripts/*.sh`),
which is enumerated by `check-harness-result.sh` as a SET EQUALITY, so it would
have had to emit a canonical `HARNESS-RESULT` line, gain a row floor, and be
wired in `ci.yml`. Everything I added lives in `docs/reviews/` for that reason,
and none of it is named `check-*` - `check-checkers-are-wired.py` enumerates
`docs/reviews/check-*.py` and `check-*.sh` and would have demanded a `ci.yml`
step I am not allowed to write. **The naming is a structural answer, not a
preference.** Measured after the change: `Checkers in docs/reviews/: 27`,
unchanged, exit 0.

**#131's central mechanism cannot be built inside this scope, and I did not
pretend otherwise.** #131 asks for every harness to record its pre-mutation
state before mutating. That is an edit to all 37 `scripts/check-*.sh`. What I
built instead puts the state file in the one place that can honestly write it
today - the probe - and the restorer says out loud, in its own header and in
its error message, that a harness run any other way is NOT covered. Two of
#131's three incidents were of exactly that uncovered kind.

**One claim in the brief I could NOT reproduce and did not try to**: the 1040s
measurement of `check-u9-http-amputation.sh`. Re-measuring it costs ~20 minutes
of a machine other agents are using and would strand a mutation if killed. I
took it as given and sized the new default from it; see the unsettled list.

## #146 F1 - the timeout branch now checks the tree

`probe-harness-exit-codes.sh` `continue`d out of the timeout branch BEFORE the
end-of-row dirty-tree check, so the one exit path most likely to strand a
mutation was the only path that never looked at the tree. The dirt surfaced one
iteration later and was attributed to `$s`, which by then names the NEXT script.

The branch now runs its own check with its own message and `exit 4`. The two
messages are deliberately different: a harness killed mid-row and a harness
that completed without restoring are different events needing different
remedies.

**Second, unasked-for finding in the same file.** The pre-flight guard used
`git status --porcelain`; the in-loop check used `git diff --quiet`. The probe
disagreed with itself about the reference, and the WEAKER instrument was the one
inside the loop - so a harness that mutated and `git add`-ed, or that left an
untracked artefact, walked past the guard that exists to catch exactly that.

**I checked this against the ruling before changing it, because it looks like
the sweep that was already refused.** Commit `13a4a65` ("Widen every
index-blind pre-flight guard: 11 sites, not 5") explicitly REFUSED to widen
in-loop checks, on the grounds that they are *paired with `git checkout --`,
which reads the INDEX, so index-relative is the reading that matches the
restore*. That refusal does not cover this site: the probe contains no restore
at all - `grep -n 'checkout\|cp \|restore'` over it returns only comments and
message text - so there is no restore for the question to match. It is a pure
detection site whose own pre-flight has already established an empty baseline,
which makes `--porcelain` the reading that matches what it is asking. This is
the same before/after reasoning `scripts/ci-harness-gate.sh` uses.

## #146 F2 - the default could not measure its own container

Default per-script budget 900 -> 1800. #108 concluded 900 had ~15x headroom
from measuring u0 at 711s; that was true of u0 and does not generalise, because
u0 is not the slowest member.

Two reporting changes so the next person sizes this from a measurement:

- the probe prints the **slowest COMPLETED row** and says so - a maximum over
  rows that all died at the budget is a statement about the budget, not about
  the harnesses;
- the ledger FILE now carries a `#`-prefixed completeness banner naming the
  MISSING rows. Previously a caller who read only the file got 36 rows and no
  hint that a 37th existed and had timed out: loud on the terminal, silent in
  its own artefact.

`compare-harness-exit-codes.sh` was taught to strip `#`. **This was necessary,
not cosmetic** - measured on a real ledger:

    awk '{print $1}' ... | sort -u | grep -c .              -> 38
    grep -v '^#' | awk '{print $1}' | sort -u | grep -c .   -> 37

against a container of 37. The banner would have entered both name sets as a
harness literally called `#`.

## #131 - what `--restore-only` does, and what it deliberately does not

`docs/reviews/lib/harness-state.sh` holds the state file's path and format in
one place, so the probe and the restorer cannot disagree about where to look.
The probe writes it BEFORE launching each harness - a state file written
afterwards is not written at all for the run that gets killed - and clears it
only after the row completed AND the tree was verified clean.

`docs/reviews/restore-stranded-mutation.sh`:

| situation | verdict | exit |
|---|---|---|
| no state file, clean tree | nothing stranded | 0 |
| no state file, DIRTY tree | **cannot attribute - refuses** | 3 |
| state file, owner pid ALIVE | **owner is running - refuses** | 3 |
| state file, owner dead, clean tree | restored itself; clears stale state | 0 |
| state file, owner dead, dirty tree | STRANDED (`--check` reports) | 1 |
| `--restore-only` on the above | restores, verified by `cmp` | 0 |
| index moved, or a rename | **refuses** | 3 |
| write failed verification | tree NOT clean | 4 |

**What it does NOT do, stated because each is a real limit:**

1. **It does not cover harnesses the probe did not launch** - by hand, by a
   shell loop, or by `ci-harness-gate.sh`. Those write no state file and the
   tool refuses rather than guesses.
2. **It never deletes an untracked file.** There is nothing to restore one to,
   and deleting is unrecoverable.
3. **It never touches the index, and refuses outright if the harness staged
   anything.** It uses neither `git checkout -- <f>` (index-relative) nor
   `git checkout HEAD -- <f>` (which this project measured DESTROYS staged
   work). It extracts the blob itself and writes bytes with `cp`, so the index
   is not a participant; where the index HAS moved it stops, because unstaging
   is the destructive operation that ruling is about.
4. **It is not a lock.** The probe's pre-flight is what stops a second start.
5. **`kill -0` has a pid-reuse hole.** A recycled pid makes a dead owner look
   alive. The failure is in the SAFE direction - it refuses and tells the
   operator to look - and `started` is printed so an anomaly is visible.

The ownership question is the whole reason this is not "clean anything dirty":
#131 records two worktrees dirty at the moment of a real stranding, both
legitimate, both with probes running in them.

## The control, and the arm that failed

`docs/reviews/control-stranded-mutation.sh` - 7 arms, 26 assertions, in a
scratch git repo built from nothing under `mktemp`. The live tree is never
used; a killed mutation harness is precisely the destructive thing this project
does not test by doing.

- **A1** the probe names the KILLED harness, not the successor
- **A2** **THE AMPUTATION** - the fix is cut out of a copy and A1's assertion
  inverts: the amputated probe blames `check-bbb-innocent.sh`
- **A3** `--check` reports and changes nothing
- **A4** `--restore-only` restores, byte-verified with `cmp`
- **A5** a LIVE owner is REFUSED and the tree is untouched
- **A6** dirt with NO state file is REFUSED and a human's edit survives
- **A7** clean tree, no state file, clean result

**A2 FAILED on its first run, and the defect was mine.** The amputated probe
has to be written inside the scratch tree (the probe derives its repo from its
own path), where it is an UNTRACKED file - so the probe's pre-flight aborted
having measured nothing, and A2's second assertion (`never says the strander
was killed`) PASSED VACUOUSLY on that abort. Two fixes: the copy is committed
before the run, and the arm now asserts it actually reached the strander. That
same rule is why the run state file lives outside the repo, and I had written
that comment before the control proved it on me.

Final: **26 passed, 0 failed, exit 0.**

## Gates, each exit code on its own line

    bash -n (4 scripts)                                     0
    shellcheck --severity=warning (5 scripts)               0
    python3 docs/reviews/check-no-errexit.py                0   (54 tracked .sh)
    uv run --frozen python docs/reviews/check-checkers-are-wired.py  0   (27 checkers, 23 wired, 4 exempt)
    python3 docs/reviews/check-no-sigpipe-pipelines.py      0   (40 files)
    bash docs/reviews/check-harness-result.sh               0   (37/37 EQUAL)
    python3 docs/reviews/check-cross-references.py          0   (0 unresolved)
    python3 scripts/check-harness-anchors.py --self-check --floor 458   0   (458 resolved)
    bash docs/reviews/control-stranded-mutation.sh          0   (26 passed, 0 failed)
    bash docs/reviews/probe-harness-exit-codes.sh (4 real harnesses)    0
    bash docs/reviews/compare-harness-exit-codes.sh          0   (37 of 37, 0 moved)
    uv run --frozen pytest                                  0   (887 passed, 0 skipped, 6 deselected)
    ... | bash scripts/check-suite-floor.sh 887              0   (887 passed, floor 887)

The suite is unchanged at the floor, which is expected and is stated rather
than presented as evidence: this branch touches five files, all under
`docs/reviews/`, and no `src/` or `tests/` file at all. **A green suite here
licenses only what it checked**, and it checked none of this work. The control
is what checks this work.

Both floors were derived from `ci.yml`, not retyped: `check-suite-floor.sh 887`
and `check-harness-anchors.py --self-check --floor 458`.

The probe run above is the real thing, not a stub: I seeded a ledger with the
33 pytest-invoking harnesses so the resume skipped them, and let the four
non-pytest ones actually run against my changed porcelain check. `git status
--porcelain` was empty before and after. That is the direct test of the one
false-positive risk the porcelain widening creates.

## Left for Tier 0

**Nothing I added is wired to CI, and I could not wire it** - `ci.yml` belongs
to `suborch-143`. The steps I have RUN from this worktree, so they are not
guesses:

    - name: Stranded-mutation control
      run: bash docs/reviews/control-stranded-mutation.sh

`--min-rows`/`--row-re` are NOT offered here: `ci-harness-gate.sh` takes a bare
harness NAME under `scripts/`, and this is neither, so routing it through the
gate would resolve to `scripts/docs/reviews/...` and exit 2. It is a plain
`run:` step. It prints `controls fired: N passed, M failed` and exits 1 on any
failure and 2 on zero arms, so the exit code alone is a sufficient gate.

**Task #153 will collide with this.** It proposes widening
`check-checkers-are-wired.py` from `docs/reviews/check-*` to the container. If
that lands, `restore-stranded-mutation.sh` and `control-stranded-mutation.sh`
become unwired members needing a step or a recorded exemption. The control
wants the step above; the restorer is an operator tool that repairs a tree and
should be EXEMPT for the same reason `check-row-floor-control.sh` is - running
it in CI would have it act on the job's tree.

## What I did NOT verify - could not settle

1. **The 1040s figure for `check-u9-http-amputation.sh` is inherited, not
   re-measured.** The new 1800s default rests on it. Re-measuring needs one
   unbounded run on a quiet machine, which I judged too expensive and too
   likely to strand a mutation on a box other agents are using. **If that
   number is wrong the new default is wrong with it.** Related: #154 says the
   300 and 120 bounds have no recorded measurement either.
2. **Whether any of the 33 pytest-invoking harnesses leaves an untracked
   artefact** in the repo. If one does, the porcelain widening turns a
   previously-tolerated condition into an abort. I measured only the four
   non-pytest members. The indirect argument that none does - the pre-flight
   already refuses untracked at the START of every pass, and resumed passes
   have reached 37/37 - is suggestive, not proof. **The cheap way to settle it
   is one full probe pass at the new default**, which is a Tier-0 call because
   it is hours long.
3. **`--restore-only` against a REAL stranded amputation.** Every arm uses a
   stub. The mechanism is identical, but I have not watched it repair
   `src/fast_mcp_jobvite/audit.py` in anger.

## What I did NOT attempt - deliberately, separate from the above

- Any edit to `scripts/*.sh` (suborch-116) or `.github/workflows/ci.yml`
  (suborch-143).
- Making every harness write its own state file - #131's full mechanism. It is
  the right end state and it is a `scripts/*.sh` sweep.
- Re-running the full 37-row probe pass.
