# WORKLOG #214 (R21-L1): the ci.yml comment that credited the wrong commit and froze a live census

Branch `fix/214-ci-comment-census`, worktree `/tmp/w214-ci-comment-census`, off `a52af14`.

## What the finding claimed, and what measurement says

R21-L1 made three claims. **Two hold. One is wrong, and it is the provenance.**

### (a) The attribution is wrong - CONFIRMED

`789d3be`, suborch-187's own commit message:

    CONTAINER, BEFORE: 25 checked for exactness, exit 0.
    CONTAINER, AFTER:  30 checked, exit 0. Equal to the control table in

`65fabe4`:

    suborch-187 widened check-row-floor-exactness.py's container from 25
    members to 32 by KIND. I had, on the other side of the merge, added two

So #187 did **25 -> 30**; the last two came from the fold. The comment attributed
the whole delta to #187. Confirmed exactly as reported.

### (b) 32 is a live census frozen into prose - CONFIRMED

    $ uv run --frozen python docs/reviews/check-row-floor-exactness.py
    CONTAINER: tracked .py, .sh under docs/reviews/, scripts/ carrying a literal floor
      members (floor > 0)                                   32
      named by the control TABLE - EQUAL both directions     32
    Harnesses checked for exactness: 32
    Every floor equals its harness's live row count. OK.
    exactness_rc=0

The step **immediately above the comment** prints the number the comment restates,
and it moves whenever a harness gains a floor. Nothing compares the comment to it,
so it drifts silently. The sibling precedent is real -
`docs/reviews/check-checkers-are-wired.py:94`: *"The property is stated; the digits
are not, and the command at the bottom of this docstring returns them."*

### (c) THE FINDING'S PROVENANCE IS WRONG - the line was NOT added at `a6430ba`

R21-L1 says the line was *"added at `a6430ba`"*. It was not.

    $ git blame -L 1202,1209 .github/workflows/ci.yml
    65fabe42 (Phil Lafayette 2026-09-02 1203) # #187 widened that checker's container from 25 members to 32, and a

    $ git show --numstat --format="" a6430ba
    17	2	docs/reviews/probe-131-gate-state.sh
    13	1	docs/reviews/probe-wired-checker-amputation.py

**`a6430ba` never touched `ci.yml` at all.** The comment was written by `65fabe4` -
the same commit whose own message carries the wrong-edged sentence. That makes the
story tighter than the finding told it: this is not a sentence copied forward into a
later commit, it is **one commit writing the same wrong edge into two artifacts at
once**, its own message and the workflow file.

The practical consequence: the "two places" are the ci.yml comment and a **commit
message**. Only one of them is fixable - history is not rewritten here (#7).

## The sibling sweep: measured, not guessed

The brief warned in both directions - fix the twin, but do not blanket-sweep. So I
looked for a **discriminator**, not a pattern.

Raw candidate counts in `ci.yml`:

    comment lines carrying an integer >= 10 : 188
    comment lines carrying a task credit    : 37

188 is far too many to sweep, and the brief said to stop and report if the answer was
"many". But most of those are **dated historical records**, which are CORRECT frozen -
a record of what was measured at a moment does not decay. The defect class is narrower:
*a number that describes TODAY's population, printed by a live checker, that nothing
compares the comment to.*

Intersecting the two sets - a task credit that also asserts a numeric delta:

    $ grep -nE '^\s*#.*#[0-9]{2,3}\b' .github/workflows/ci.yml \
        | grep -E '[0-9]+ *(->|to) *[0-9]+|widened|raised|from [0-9]+'
    1203:      # #187 widened that checker's container from 25 members to 32, and a

**One line. The scope really is one line, and that is a measurement, not an assumption.**

Repo-wide, the wrong-edged sentence has exactly one live home:

    $ grep -rnE '25 members to 32|from 25 .*32|187 widened' \
        --include='*.md' --include='*.yml' --include='*.py' --include='*.sh' .
    .github/workflows/ci.yml:1203

### Siblings I READ and deliberately LEFT, with reasons

| site | text | verdict |
|---|---|---|
| `:267` | `WIRED 2026-09-01, GREEN WHEN WIRED: 37/37 scripts in the container` | **LEFT.** Explicitly DATED and labelled `WHEN WIRED`. A record of a moment, not a claim about today. Correct frozen. |
| `:300` | `it saw 28 of 123 files and printed "Every checker is wired" about the other 95` | **LEFT.** Past tense, describing the defect the OLD glob container had. A historical record. Note its live half - *"the container is now every tracked `.py`/`.sh` ... selected by KIND"* - already states the property with NO digits. That is the target shape, already correct. |
| `:1167` | `18 checkers, 16 wired, and of the two that were not...` | **LEFT.** Past tense, `found by enumerating` - the record of the enumeration that motivated the wiring. |
| `:1521` | `Row counts DERIVED from the harnesses' own ROW_FLOOR (12 and 5)` | **LEFT, and this was the closest call.** `12` and `5` are restatements of `--min-rows 12` and `--min-rows 5` in the **executable YAML two lines below** (`:1529`, `:1535`). `check-row-floor-exactness.py` compares every `--min-rows` in this file to its harness's live row count (`Harnesses whose --min-rows was compared to a live count: 16`). So these **cannot drift silently** - the gate goes red at the literal, and whoever fixes it is looking straight at the comment. That is the opposite of `:1203`, whose `32` nothing compares to anything. |

`:1521` is the one a blanket sweep would have damaged: deleting its digits would have
removed the reader's cross-check on two gated literals sitting two lines away.

## The fix

`.github/workflows/ci.yml`, comment above `The floor container's own arms`:

```diff
-      # #187 widened that checker's container from 25 members to 32, and a
-      # container change to a gate with its own control table is exactly the
-      # thing whose arms need running. It plants and removes one file under
-      # `src/` in a `finally` that its own arm A7 asserts, which is why it
-      # can share a job with its subject.
+      # #187 rebuilt that checker's container as a KIND rather than a glob,
+      # and the fold at 65fabe4 added two more members; the live census is
+      # printed by the step above under `CONTAINER:`. A container change to a
+      # gate with its own control table is exactly the thing whose arms need
+      # running. It plants and removes one file under `src/` in a `finally`
+      # that its own arm A7 asserts, which is why it can share a job with its
+      # subject.
```

The digits are gone; the reader is pointed at the step that prints them. `65fabe4` is
named because it is a stable historical fact, not a live figure.

**`THE SIXTEEN ARMS` on the line above is LEFT deliberately**, and I checked it rather
than inheriting the finding's word for it:

    HARNESS-RESULT name=check-row-floor-exactness.py rows=16 floor=16 fired=16/16 status=ok
    selftest_rc=0

`rows=16 floor=16` and the checker gates its own floor at **equality**, so this number
cannot drift silently. It is a live figure with a live gate - which is exactly the
property `32` lacked.

## Gates - every exit code on its own line

    $ python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"
    yaml_parse_rc=0

All five checkers that read `ci.yml`:

    check-checkers-are-wired      rc=0
    check-obligations             rc=0    Mappings: 31 | anchors verified: 25 | recorded absent: 6
                                          "Every mapped anchor still contains its subject. OK."
    check-row-floor-exactness     rc=0    "Every floor equals its harness's live row count. OK."
    check-no-sigpipe-pipelines    rc=0    "Occurrences inside COMMENTS, ignored: 2"
    check-row-floors              rc=0    Harnesses: 33 | not referenced by ci.yml: 0 | no floor: 0

    $ python3 scripts/check-harness-anchors.py --self-check --floor 464   # floor DERIVED from ci.yml
    OK: all 464 anchors resolve in their target file ... (floor 464).
    anchors_rc=0

No anchor moved, so `docs/OBLIGATIONS.md` needed no repoint.

### THREE CHECKERS ARE RED, AND ALL THREE ARE RED AT THE UNTOUCHED BASE

I swept all 25 `docs/reviews/check-*.py`, not just the five that read `ci.yml`. Three
exit nonzero. I did **not** take their word for being "someone else's" - I built a
clean detached worktree at `a52af14` and ran them there:

    $ git worktree add --detach /tmp/w214-base a52af14
    BASE a52af14: check-brief-report-references rc=1
    BASE a52af14: check-coverage-floors         rc=2
    BASE a52af14: check-design-citation-shape   rc=1

Identical exit codes on the branch and at the base, so **this branch introduces no new
red.** What they are:

- `check-brief-report-references` rc=1 - `FINDINGS-213-syntax-split.md` cited by
  `BRIEF-211-213-record-and-counterfactual.md` exists nowhere. That is task **#213**'s
  report, still in flight. Not mine to commit or waive.
- `check-coverage-floors` rc=2 - `coverage.json does not exist`. Environmental; needs a
  `pytest --cov` run. The checker deliberately exits **2** rather than 0 here, which is
  the "a search at a path that does not exist returns a clean empty" rule working.
- `check-design-citation-shape` rc=1 - 2 citations in
  `docs/reviews/probe-204-orphaned-by-repoint.py:7` and `:70` start on a BLANK line.
  That file is task **#204**'s.

**Reported, not fixed and not silently dropped** - all three are outside this task's
scope and two belong to tasks that are currently in flight. Fixing another agent's file
underneath them is how a merge puts damage back.

## ACTIONLINT WAS NOT RUN, AND CI'S RUN WILL BE ITS FIRST TEST

`actionlint` is **not installed in this environment**, and I verified that rather than
assuming it:

    $ command -v actionlint
    actionlint_lookup_rc=1
    $ ls ~/.local/bin/actionlint
    actionlint_home_rc=2

**The `ci.yml` hunk in this branch has never been through actionlint.** CI's own
actionlint step will be the first thing to lint it. The change is comment-only and the
file still parses as YAML, which bounds the risk but does not remove it - actionlint
checks things `yaml.safe_load` does not.

## What I did NOT verify

- **actionlint on this hunk.** Not installed here (probed, rc=1). Stated above.
- **`uv run --frozen pytest`.** Not run. The diff is seven comment lines inside a YAML
  file; no Python, no test, no harness changed, so the suite floor cannot move. I did
  not run it, and I am not reporting a passed-count I do not have.
- **That `65fabe4` is the ONLY commit that added the last two members.** I confirmed
  `65fabe4`'s message claims them and that #187's claims 25 -> 30, so the edges are
  right. I did not replay the container at each parent to prove the count was 30 at
  `c7493341` - the commit messages agree with each other and with today's 32, but that
  is coherence, not an independent measurement.
- **The other 33 task-credit lines in `ci.yml`.** I filtered them by a discriminator
  (credit + numeric delta) and read the four census-shaped siblings above. I did not
  read all 37 lines end to end for non-numeric wrong attribution - a credit naming the
  wrong commit with no number in it would not have been caught by my selector.
- **My brief and my dispatch disagree on the base.** The brief says the worktree
  should be off `d2159e7`; the dispatch message said `a52af14`. I used `a52af14`
  (current `main`; `d2159e7` is its parent, a briefs-only commit). `ci.yml` is
  byte-identical at both, so the fix is unaffected - but the disagreement is reported
  rather than silently resolved, per the PREAMBLE.

## Worktree

**Left in place at `/tmp/w214-ci-comment-census`**, as instructed. Not removed.

## For the team lead

    git merge --ff-only fix/214-ci-comment-census

Not pushed, not merged.
