# REVIEW-R22 - a SECOND wired gate is red on main, and the exemption survives its own mutation while its reason does not

<!-- REVIEW-COVERS: 80463a5..4f03004 PATHS: .github docs/adr docs/briefs/PUSH-BRIEF-2026-09-02.md docs/reviews/REPOINT-EXEMPT.txt docs/reviews/brief-report-refs-known-missing.txt docs/reviews/check-adr-numbers.py docs/reviews/check-brief-report-references.py docs/reviews/check-brief-report-refs-controls.sh docs/reviews/check-checkers-are-wired.py docs/reviews/check-design-citation-shape.py docs/reviews/check-row-floor-controls.sh docs/reviews/check-row-floor-exactness.py docs/reviews/probe-204-orphaned-by-repoint.py docs/reviews/probe-213-syntax-split.py docs/reviews/probe-stale-branch-regression.sh docs/reviews/probe-wired-checker-amputation.py -->

Reviewer: `review-r22`, task #225. Worktree `/tmp/wt-review-r22`, branch
`review/r22`, cut from LOCAL `main` at **`4f03004`**. Nothing was fixed,
nothing was pushed, nothing was merged. Written 2026-09-02 01:29 AM CDT.

`docs/DESIGN.md` was read only as
`git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md` - SHA derived, not
retyped: it resolves to **`d1f1a52`**.

**1 High, 2 Medium, 2 Low, 2 nits.** Every finding ships a suggested fix,
marked as a suggestion to be verified.

**H1 IS A LIVE RED ON `main` RIGHT NOW.** It was found independently by
`suborch-221` while I worked, and its task closed with it. I confirmed it
from my own pinned worktree, and I add three things #221's line does not
carry: WHEN it entered, that it entered inside this round's range, and that
a sixteen-gate green list written TWO COMMITS AFTER the apology for exactly
this failure omits it.

---

## The range I derived, and three corrections to the brief

**RANGE: `80463a5..4f03004`.** R21 declared `c749334..80463a5`; everything
after it on `main` was unreviewed. Pinned, and nothing after `4f03004` was
read - `main` HAS moved under me (task #219 closed "at 97 held" while I
worked, so `main` is past `4f03004` already).

    $ git rev-list --count 80463a5..4f03004
    42
    $ git diff --stat 80463a5..4f03004 | tail -1
     39 files changed, 6659 insertions(+), 323 deletions(-)

1. **ELEVEN merges in the range, not seventeen. EIGHTEEN in the held set.**

       $ git log --merges --oneline 80463a5..4f03004 | wc -l
       11
       $ git log --merges --oneline origin/main..4f03004 | wc -l
       18
       $ git rev-list --count origin/main..4f03004
       96

2. **TWO of them have a non-empty combined diff in the range, not three**
   (measured with `git show --cc --format= <sha> | wc -l` over all eleven):
   `043cc6f` at 16 lines and `fb6483e` at 12. The other nine are 0.

3. **`origin/main` is `6e4fae3` and IS the merge base** with `4f03004`, so
   `...` and `..` give the same file set here. I checked, because the push
   brief's headline uses `...` and a divergence would have made the two
   forms disagree.

---

## H1 - `check-no-errexit.py` is WIRED, has no `|| true`, and exits 1 on `main` - since a commit inside this range

    $ python3 docs/reviews/check-no-errexit.py
    Tracked shell scripts checked: 60
      EXEMPT   scripts/check-pytest-bounded.sh: a CHECKER, not a harness. ...

    1 script(s) enable errexit:
      docs/reviews/probe-stale-branch-regression.sh:50  set -euo pipefail
    ...
    rc=1

The step, at `.github/workflows/ci.yml:264-265`, is unguarded:

    - name: No harness enables errexit
      run: python3 docs/reviews/check-no-errexit.py

**WHEN IT ENTERED.** The file was ADDED at `ebaf6c8` ("A merge can silently
delete work, and the branch it caught was a LIVE one"), inside this round's
range, and it carried `set -euo pipefail` from that first commit:

    $ git log --oneline --diff-filter=A 80463a5..4f03004 -- docs/reviews/probe-stale-branch-regression.sh
    ebaf6c8 A merge can silently delete work, and the branch it caught was a LIVE one
    $ git show ebaf6c8:docs/reviews/probe-stale-branch-regression.sh | grep -n 'set -euo pipefail'
    50:set -euo pipefail

So `main` has been red on this gate for the whole tail of the range.

**AND THE GREEN LIST TWO COMMITS LATER DOES NOT CONTAIN IT.** `be4fd12`'s
message lists sixteen gates, each with rc=0 - `ruff format mypy shellcheck
wired wired --self-test brefs refs-controls coverage citations shape freeze
row-floor-exactness row-floor-controls obligations adr-numbers` - and
`check-no-errexit` is not among them. `bc42cc5`, two commits earlier, is the
commit that apologises for precisely this: *"I ran the ones I had been
thinking about and reported the set I ran as though it were the set that
exists."* The lesson was written and then reproduced by the next gate list.

**THE PUSH BRIEF DOES NOT MENTION IT EITHER.** It names this probe under
"What actually changes" as *"deliberately NOT wired and registered as
such"*, which is true and is about a different gate. Nothing in the brief
tells a reader that the probe reds a wired one. The brief has now been
wrong about gate colour twice, in the same shape, about two different gates.

**THE CHECKER'S STATED RATIONALE IS FALSE HERE, AND ITS VERDICT IS STILL
RIGHT BY ITS OWN RULE.** Its message says *"Under errexit the shell exits AT
the command, so `cmd; rc=$?` never runs and every branch below it is dead
code."* Measured, that is not what happens in this probe: `:103-106` brackets
the status read with `set +e` / `set -e`, and all three one-branch arms
return the right code (rc=1 regress, rc=0 clean, rc=2 no such branch - each
run in §"What I verified" below). So this is a rule violation whose named
consequence does not occur.

**Suggested fix (a suggestion, to be verified) - and the obvious one has a
trap.** The mechanical repair, `set -euo pipefail` -> `set -uo pipefail` at
`:50`, does NOT by itself make errexit off for the run: `:106` executes a
bare `set -e` and leaves it on for everything after it in the one-branch
path. Fix both or neither, and re-run all four arms.

The remedy I would try first is the register the checker already has, at
`docs/reviews/check-no-errexit.py:88`, whose single row exempts
`scripts/check-pytest-bounded.sh` as *"a CHECKER, not a harness"* - the same
argument applies here and is measurable:

    "docs/reviews/probe-stale-branch-regression.sh": (
        "a SURVEY, not a harness. It reads no timeout status: its one "
        "status read, at :104-106, is bracketed by `set +e`/`set -e` on "
        "purpose, and all three exit codes are watched by its own arms "
        "(1 regress, 0 clean, 2 no such branch). The dead-branch "
        "consequence this gate names does not occur here - measured, "
        "not argued."
    ),

Whichever is chosen, verify by running `check-no-errexit.py` (must be rc=0)
AND all four probe arms afterwards, because an exemption that hides a real
errexit bug and a `set` change that breaks arm 3 look identical from the
gate's output.

---

## The thing I was asked to press hardest on: the probe-204 exemption

**MEASURED IN THREE ARMS, ON THE TREE, WITH THE TREE RESTORED.** Backups
taken first; `git status --porcelain` empty afterwards.

    ARM 0  as committed                          rc=0   (13 exempt, 17 rows)
    ARM A  register row deleted, markers kept    rc=1   names :8 and :80
    ARM B  both markers deleted, row restored    rc=1   names :8 and :80
    ARM 0' file+register restored, re-run        rc=0   tree byte-clean

Verbatim, ARM A:

    docs/reviews/probe-204-orphaned-by-repoint.py:8  DESIGN.md:489-490
    docs/reviews/probe-204-orphaned-by-repoint.py:80  DESIGN.md:489-490
    2 citation(s) point at something that cannot be their subject.

**THE CONCLUSION HOLDS AND THE MECHANISM IS LOAD-BEARING IN BOTH
DIRECTIONS.** Neither half alone grants the exemption, exactly as `#142`
designed and as the commit message claims. I could not break it.

The supporting facts also hold, each checked rather than assumed:

- `docs/adr/0017-...:16` and `:67` are the two halves, today
  (`grep -n ':489-490' docs/adr/0017-*.md` returns exactly those two lines).
- `DESIGN.md:489` at the frozen blob `d1f1a52` **is blank** and `:490` is
  not, so `classify()` returns *"starts on a BLANK line (the off-by-one
  shape)"* - the register row's *"489 is blank in DESIGN.md today"* is
  accurate, and so is the reason the gate fires.
- `b0e86b8` did move the qualified half to `:495-496` and `be94bce` did
  restore it to `489-490` (read from both commits' diffs of the ADR).
- The ADR itself is never scanned by this gate: `CODE_SUFFIXES = {".py",
  ".sh"}` at `docs/reviews/check-design-citation-shape.py:87`. So
  `ec57a65`'s as-at-acceptance ruling is not in tension with a red gate -
  the ADR could not have been flagged either way.

**So the exemption did not silence a real finding.** That is the answer to
the question I was sent to ask. What is wrong with it is the row's reason -
M1 below.

---

## M1 - the register row's stated reason is false for one of the two sites it covers

`docs/reviews/REPOINT-EXEMPT.txt:48` grants one row for both sites and says:

> NOT A CITATION - a REPRODUCTION of ADR-0017 lines 16 and 67, which are
> the probe subject.

Read the two marked lines (`grep -n 'REPOINT-EXEMPT$'
docs/reviews/probe-204-orphaned-by-repoint.py`):

    8:         `DESIGN.md:489-490` states that ...   # REPOINT-EXEMPT
    80:`DESIGN.md:489-490` qualified and bare;   # REPOINT-EXEMPT

Line 8 IS a reproduction of ADR-0017:16 (elided with `...`, and preceded at
`:7` by that line's opening clause). **Line 80 is not a reproduction of
anything.** In context (`:78-83`) it is the probe's OWN narrative sentence:

    **This test exists because the one CONFIRMED instance was still being
    reported after it was fixed.** `docs/adr/0017-...` carried
    `DESIGN.md:489-490` qualified and bare;   # REPOINT-EXEMPT
    `b0e86b8` moved the qualified half to `:495-496`; `be94bce`
    restored it to `489-490`, so the ADR
    agrees with itself again.

That is a historical statement about what the ADR carried - a MENTION of an
address, not a reproduction of an ADR line and not a claim about
`DESIGN.md` today. And **neither marked line reproduces ADR-0017:67**: the
line that does is `probe:9`, which is in the bare form and was never
flagged, because the gate's selector requires the filename.

So the row's reason names two ADR lines and covers: one faithful (elided)
reproduction of one of them, and one sentence that is not a reproduction at
all. **The exemption is still correct** - repointing :80 would falsify a
record of where the address WAS, which is the same class as the six other
"a record of where a defect WAS" rows already in the register. But a
reader auditing the register cannot verify the row from its own text, and
verifying rows from their own text is the register's entire job.

This is the pattern the round was sent to look for: the conclusion survives
and the stated reasoning does not.

**Suggested fix (a suggestion, to be verified):** rewrite the row's reason
so each site is stated separately and each is checkable, e.g.

    docs/reviews/probe-204-orphaned-by-repoint.py	489-490	TWO SITES, ONE
    ADDRESS. :8 REPRODUCES ADR-0017:16 (elided) - the ADR is this probe's
    subject. :80 is this probe's OWN record of the address the ADR carried
    before b0e86b8 moved it to :495-496 and be94bce restored it. Neither
    asserts anything about DESIGN.md today, and 489 being blank at the
    freeze IS the point. Repointing :8 falsifies a quotation and repointing
    :80 falsifies a record; ec57a65 rules ADR citations are AS AT
    acceptance, so the ADR must not move either. The line that reproduces
    ADR-0017:67 is :9 and is in the bare form, which this gate does not
    select - it is unmarked on purpose.

Verify by re-running ARMS A and B after the edit: both must still be rc=1
and the restored tree rc=0. The row text is not read by the checker, so
this cannot change the verdict - which is exactly why nothing but a reader
will ever catch it.

---

## M2 - the push brief names three of the NINE commits that touch `ci.yml`, in the section it calls the largest unverified thing

`docs/briefs/PUSH-BRIEF-2026-09-02.md` says:

> **`ci.yml` NOW CARRIES HUNKS FROM THREE DIFFERENT AGENTS** - #194 added a
> wiring-probe self-test step, #214 rewrote a comment that had frozen a live
> census, #210 folded an ADR-index check into an already-wired step. All
> three survived the merges; I verified each by name rather than trusting a
> clean `git merge`.

Derived:

    $ git log --oneline --no-merges origin/main..HEAD -- .github/workflows/ci.yml
    8ae3542 #210 #215 #216 #217: the ruling's evidence, ...
    abcaf18 #194: a COMPUTED row count is UNPREDICTABLE, ...
    9be28ec #214 (R21-L1): the credit named the wrong commit ...
    be94bce #204 merged with both rulings, ...
    db90e18 R20-L3/N1/N2: a wiring that erased a refusal, ...
    65fabe4 Fold #187: the merge left my own two floors uncovered, ...
    a0677bc #192: REVIEW-R18.md was never lost, and the gate that would ...
    b4e6d06 R19-N1: the mirror's zero-ref guard PRINTED instead of asserting ...
    23280e2 #180 + #182: the register exists, so the count derives ...

**Nine commits, seven added steps.** "Verified each by name" covers three of
nine. That is a check of what the author was thinking about, in the same
shape as the `043cc6f` grep the brief for this round already flagged - and
it sits in the paragraph the brief itself introduces with *"which is where
the real uncertainty is"*.

**The brief's conclusion is right.** I checked all seven added step names
survive at `4f03004` (`git show <sha> -- .github/workflows/ci.yml | grep -E
'^\+ *- name:'`, then `grep -qF --` each against the file):

    8ae3542  PRESENT: - name: ADR numbers are unique and contiguous, and the index matches
    abcaf18  PRESENT: - name: That probe's own floor still fires
    be94bce  PRESENT: - name: The bare-citation discriminator's controls
    65fabe4  PRESENT: - name: The floor container's own arms
    a0677bc  PRESENT: - name: Every report a brief cites is committed
    a0677bc  PRESENT: - name: Controls for the brief-report reference gate
    b4e6d06  PRESENT: - name: The mirror refuses a zero-ref push

(`9be28ec`, `db90e18`, `23280e2` add no step - they are comment and wiring
edits, and their content is visible in the `origin/main...HEAD` diff.)

`ci.yml` also parses: `yaml.safe_load` gives **4 jobs, 109 steps**, rc=0.

**Suggested fix (a suggestion, to be verified):** replace the sentence with
the derivation and the survival check, so the number cannot go stale and
the claim names its own method:

    git log --oneline --no-merges origin/main..HEAD -- .github/workflows/ci.yml
    # then, per commit:
    git show "$c" -- .github/workflows/ci.yml | grep -E '^\+ *- name:' \
      | sed 's/^+ *//' | while IFS= read -r n; do
          grep -qF -- "$n" .github/workflows/ci.yml || echo "MISSING: $n"
        done

The `--` is load-bearing: without it `grep` reads the step name's leading
`-` as an option and prints an invalid-option error to stderr while
returning nonzero, which reads as MISSING. That happened to me on the first
pass and produced seven false absences (N2).

---

## L1 - the push brief retypes `ci.yml`'s suite floor, which PREAMBLE.md says must live in exactly one place

`docs/briefs/PUSH-BRIEF-2026-09-02.md`:

> The suite is 887 passed / 0 skipped locally, against `ci.yml`'s floor of 887.

`docs/briefs/PREAMBLE.md` says of that number: *"The floor in `ci.yml` is
the one place that value lives ... Anything else is a second copy"*, and
records three separate ratchets over which a retyped copy went stale.

**It is correct today**, which is why this is a Low and not a Medium. Both
halves measured:

    $ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
    check-suite-floor.sh 887
    $ uv run --frozen pytest -q
    887 passed, 6 deselected in 56.99s
    (exit code 0)

0 skipped. The 6 deselected are not skips; the brief does not mention them
and the zero-skips claim is true as written.

**Suggested fix (a suggestion, to be verified):** drop the digits and print
the derivation, the way PREAMBLE.md does:

    The suite is 887 passed / 0 skipped locally. Derive the floor it must
    clear - it is in exactly one place and it ratchets:
        grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1

---

## L2 - the push brief's own two "run them" figures are stale, and its headline is not

The brief gives 65 files and 89 held commits and says *"They rise with every
commit, so run them."* Re-derived at `4f03004`: **68 and 96**. That is the
brief behaving as designed, so it is recorded rather than charged.

**The headline re-derives exactly, which is the number that matters:**

    $ git diff --name-only origin/main...HEAD | grep -cE '^(src|tests)/'
    0
    $ git diff --name-only origin/main..HEAD | grep -cE '^(src|tests)/'
    0

Both forms. **Not one file under `src/` or `tests/` changes.** The claim
that bounds the whole push is true.

**Suggested fix (a suggestion, to be verified):** none for the headline. For
the two stale figures, delete the values and keep only the commands - the
sentence "At the time of writing those were 65 and 89" is a dated record
that a reader has to check before it helps, and the commands beside it are
already the whole content.

---

## N1 - task #225's own framing overstates the merge count by six

The dispatch says *"SEVENTEEN MERGES, several resolved BY HAND by me, three
with a non-empty combined diff."* In the range it is **eleven merges, two
with a non-empty combined diff**; over the whole held set it is **eighteen**.
Seventeen is neither. Not a defect in the tree - a brief figure that moved,
recorded because the brief asked me to report the disagreement.

**Suggested fix (a suggestion, to be verified):** dispatches that quote a
merge count should quote the command with it:
`git log --merges --oneline <base>..HEAD | wc -l`, and say which base.

---

## N2 - my own instrument failed first, in the way this project keeps recording

My first pass at the M2 survival check ran `grep -qF "$n"` without `--`.
Every step name begins with `- name:`, so `grep` parsed it as options:

    ugrep: invalid option - name: The floor container's own arms

and returned nonzero, which my loop printed as `MISSING`. **Seven false
absences, all of them reading exactly like a merge having eaten the step.**
Re-run with `grep -qF --`, all seven were PRESENT. Recorded because the
alarming direction is the one that gets believed.

---

## What I verified and found NO defect in - reported as loudly as the findings

**The two hand-resolved merges, checked by EXECUTION rather than by grep.**

`043cc6f` kept one side of each of two registry rows in
`docs/reviews/check-row-floor-controls.sh`. Both resolved rows were then
RUN, not read:

    $ bash docs/reviews/check-row-floor-controls.sh docs/reviews/probe-131-gate-state.sh
    row invocations still matching: 2 (was 3, must be 2)
    HARNESS-RESULT name=probe-131-gate-state.sh rows=11 floor=12 fired=11/11 status=breach
    CONTROL FIRED: ... loses 1 row(s), reported rows=11 floor=12 status=breach, exiting 1.
    rc=0

    $ bash docs/reviews/check-row-floor-controls.sh docs/reviews/check-brief-report-refs-controls.sh
    row invocations still matching: 22 (was 23, must be 22)
    HARNESS-RESULT name=check-brief-report-refs-controls.sh rows=24 floor=25 fired=24/24 status=breach
    CONTROL FIRED: ... exiting 1.
    rc=0

Both resolutions kept the side that actually selects rows in the live
harness. A wrong side would have matched zero rows and the control would
have failed on "was N, must be N-1". `check-row-floor-exactness.py` rc=0,
32 harnesses, "Every floor equals its harness's live row count".

`fb6483e` resolved `brief-report-refs-known-missing.txt` by keeping both
sides' new rows and DELETING the `WORKLOG-194-watch-last-two.md` in-flight
line that came from `main`. **That deletion is correct, and it is the one
that looks wrong**: the merge's own message says *"both sides' register
edits KEPT"*. The worklog had landed on that branch -

    $ git show fb6483e:docs/worklogs/WORKLOG-194-watch-last-two.md | head -1
    # WORKLOG — #194: the last two floors, watched fire by two DIFFERENT mechanisms

- so the in-flight row was required to go, which is what this file's own
routine says. `check-brief-report-references.py` rc=0 at HEAD.

**Both `UNWIRED_BY_DECISION` reasons hold, and neither is a coverage claim.**

`probe-stale-branch-regression.sh` is registered as *"advisory by design ...
Its survey form exits 0 always ... Its one-branch form (exit 1 regress, 0
clean, 2 no such branch)"*. All four arms measured:

    survey (no argument)              rc=0   "6 unmerged branches, 5 would delete lines from main"
    review/r18 (regressing)           rc=1   "MERGING WOULD DELETE LINES FROM main."
    review/r22 (identical to main)    rc=0   "merging deletes nothing. Read the diff anyway."
    no-such-branch-xyz                rc=2   "NO SUCH BRANCH. Nothing was measured."

Every clause of the registered reason is true, including the exit-code map,
which nothing but running it could have established.

`probe-213-syntax-split.py` is registered as a counterfactual for a ruling
Tier 0 has not made. It exits 0 and reports:

    Report names cited:         26
    CURRENT gate detects:       0  (none)
    SPLIT gate would detect:    0  (none)
    LOST to the split:          0  (none)

It counts and judges; it asserts no property of the tree and claims no
coverage, and the register row says so explicitly and says what would end
the row. **Correct as registered.** The one thing worth noticing is that the
counterfactual currently measures 0 against 0 - the evidence it exists to
supply is, today, "the two gates would agree", which is a real answer and a
weak one. That belongs to #213, not to this round.

**Gate sweep at `4f03004`, each exit code read on its own line, nothing chained:**

    ruff check .                                        rc=0
    ruff format --check .                               rc=0
    mypy src tests                                      rc=0
    shellcheck --severity=warning (all tracked *.sh)    rc=0
    check-design-citation-shape.py                      rc=0   13 exempt / 17 rows / 0 findings
    check-design-citations.py                           rc=0
    check-design-freeze.py                              rc=0
    check-obligations.py                                rc=0
    check-adr-numbers.py                                rc=0
    check-brief-report-references.py                    rc=0
    check-brief-report-refs-controls.sh                 rc=0
    check-row-floor-exactness.py                        rc=0
    check-checkers-are-wired.py                         rc=0
    check-review-coverage.py                            rc=0   backlog holds at 66
    check-no-errexit.py                                 rc=1   *** H1: WIRED, UNGUARDED, RED ***
    scripts/check-harness-anchors.py --self-check --floor 464   rc=0
    uv run --frozen pytest                              887 passed, 0 skipped, 6 deselected, rc=0

Both floors were DERIVED from `ci.yml`, not retyped:
`check-suite-floor.sh 887` and `--floor 464`.

---

## What I did NOT verify

- **`actionlint`.** Not installed here. I did not run it and I make no claim
  about it. The push brief's warning that CI's own step will be the first
  thing to lint these hunks stands unchallenged.
- **`mirror.yml`'s diff over this range.** The range's only `.github` change
  is `ci.yml`; `mirror.yml` moved earlier in the held set, outside my
  declared range, and I did not read it. `probe-mirror-zero-refs.sh` was not
  run.
- **Merge-INVENTED content.** #222 owns it and I deliberately did not
  duplicate it. My merge work asked only whether the resolutions kept the
  right sides, which is a different question and does not cover content
  present in neither parent.
- **The six worklog / findings markdown files in the range** -
  `WORKLOG-209/210/212/213/214`, `FINDINGS-213`, `FINDINGS-204`,
  `CITATION-READ-ADR-VERDICTS.md` - and the seven `docs/briefs/BRIEF-*.md`
  files. They are excluded from my `PATHS` declaration for exactly that
  reason: the fixes' own records have not been read against the fixes, and
  that is the largest single unread thing this round leaves.
- **`repoint-design-citations.py` and `probe-204-bare-citations.py`** as
  they changed in this range. The latter's `--controls` step is wired and I
  did not run it; the former is registered unwired and I read only its
  register entry. Both are excluded from `PATHS`.
- **The nine ci.yml commits' hunks beyond their added step NAMES.** I proved
  the seven steps survive; I did not diff every comment and `run:` body
  against its originating commit.
- **CI behaviour under the runner's `python3`.** #221 is open on it and I
  ran everything under the interpreters named above, in this worktree, on
  this machine.
- **Anything after `4f03004`.** `main` has already moved (#219 closed at 97
  held). My declaration is pinned and I read nothing past it.
