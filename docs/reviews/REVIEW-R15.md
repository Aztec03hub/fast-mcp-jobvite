# REVIEW-R15 - the review machinery itself

<!-- REVIEW-COVERS: 8695101..0b149b9 PATHS: docs/reviews scripts .github -->

Round R15, dispatched as a Tier-1 sub-orchestrator against task #119.
Worktree `fmj-worktrees/r15`, branch `review/r15`, cut from local `main`
at `0b149b9`. Zero Tier-2 workers spawned - the sixth run in a row to
judge that nothing here warranted a pane.

The brief's claim was that the uncovered trunk is *"the review machinery
itself"*. That claim **holds**, and it is the reason this round is one
round rather than fifteen. Almost everything else in the brief was off,
and the corrections are in §1.

---

## 1. The population, re-derived - my brief was wrong three ways

The brief gave: **115 uncovered commits**, container `8695101..origin/main`,
**233 file touches**, and the conclusion that one round declaring
`PATHS: docs/reviews scripts .github` *"closes most of it"*.

### 1a. The count is 131, not 115 - and the ref matters

    python3 docs/reviews/check-review-coverage.py --ref main
      Trunk commits on main since 8695101: 239
      Fully covered - range AND every path: 108
      PARTIALLY covered: 0
      COVERED BY NOTHING: 131            exit 1

    python3 docs/reviews/check-review-coverage.py --ref origin/main
      Trunk commits on origin/main since 8695101: 236
      COVERED BY NOTHING: 128            exit 1

**`origin/main` is two commits BEHIND local `main`** (`d486c477` vs
`0b149b91`), so the brief's container and the checker's own default ref
disagree, and they give different answers. The checker's default is
`main` (`:236`), while its own docstring writes the example as
`--ref origin/main` (`:4`). That disagreement is not cosmetic - see H-1.

**The 115 was already known to be unreproducible.** `REVIEW-R14-R1.md`
records it as finding M3, *"the 115 is not reproducible from the
document"*. The number survived that finding and reached me in a brief.
It is a derived record decaying at each copy-forward, which is the class
this repo has measured repeatedly.

### 1b. The shape is 255 touches, not 233

Re-derived over the 131 uncovered commits, bucketing every file each
touches:

| bucket | brief | measured |
|---|---:|---:|
| `docs/reviews/` | 95 | **105** |
| `scripts/` | 55 | **55** |
| other config/docs | 33 | **44** |
| records (exempt) | 17 | **18** |
| `.github/` | 16 | **16** |
| `tests/` | 10 | **10** |
| `src/` | 7 | **7** |
| **total** | 233 | **255** |

`scripts`, `.github`, `tests` and `src` match exactly; `docs/reviews` and
the "other" bucket are both understated. The brief was measured against
the older, smaller uncovered set - the same staleness as 1a.

**The qualitative claim survives.** `docs/reviews` + `scripts` is
**160 of 255** touches (63%); `src` + `tests` together are **17** (7%).
The checker docstring's *"the least-reviewed code here is the code that
does the reviewing"* is confirmed, with better numbers than the brief's.

### 1c. THE CORRECTION THAT MATTERS: touches are not commits

The brief reasoned *"150 of 233 file touches, so one round closes most of
it"*. **The checker does not count touches.** `check-review-coverage.py:274-283`
covers a commit only when **every** file it touches is claimed. Measured:

    With PATHS: docs/reviews scripts .github
      -> FULLY covered  92
      -> still PARTIAL  39

So this round takes **NONE 131 -> 0**, but creates **PARTIAL 0 -> 39**.
It does not reach zero, and the gate stays red. A path filter argued from
touch counts systematically over-promises, because one stray file in an
otherwise in-scope commit demotes the whole commit.

**The 39 residual commits are held back by a small, enumerable set** -
mostly `docs/briefs/` (21 touches across 9 files) and `.secrets.baseline`
(6):

    6  docs/briefs/PROTOCOL-sub-orchestrators.md
    6  .secrets.baseline
    4  docs/briefs/HANDOFF-2026-09-01-orchestration.md
    3  docs/briefs/PREAMBLE.md
    2  each: scratch139/fix.py, scratch139/measure.py,
           docs/briefs/BRIEF-142-scope-the-exemption.md,
           docs/briefs/AUDIT-SHAPES.md, docs/README.md,
           src/.../jobvite_client.py, src/.../redaction.py,
           tests/test_resilience.py, tests/boot_process.py,
           tests/test_spawn_orphan.py
    1  each: 3 files under docs/adr/, 2 under docs/research/,
           4 more docs/briefs/, README.md, pyproject.toml,
           .env.example, .pre-commit-config.yaml, sweep.log,
           docs/DESIGN-FREEZE.txt, and 6 more under src/ and tests/

**Suggested fix (for Tier 0, not for me):** one complementary round over
`docs/briefs docs/adr docs/research src tests` plus the five root config
files takes PARTIAL 39 -> 0. `docs/briefs` cannot be shortcut into
`RECORD_PATHS`: the ruling at `check-review-coverage.py:123-130` refuses
it by name, because a brief *instructs* an agent and has carried
substantive rulings. That ruling is correct and I am not proposing it be
reopened.

`scratch139/` and `sweep.log` are already **deleted at HEAD**
(`git ls-files` returns neither; both were added and removed inside the
uncovered span). They still demote their commits, and reading a deleted
scratch file is cheap - they are not an obstacle.

---

## 2. Findings

### R15-H1 (High) - the default `--ref` cannot resolve in CI, so wiring this gate makes it exit 3

`docs/reviews/check-review-coverage.py:236`

```python
"--ref",
default="main",
help="trunk ref; never HEAD - under checkout that is a merge commit",
```

R12-H3 moved this off `HEAD` because *"under `actions/checkout` HEAD is
the PR's merge commit"* (docstring `:57-59`). The reasoning was right and
the landing was half a step short: **`actions/checkout` produces a
detached HEAD and creates no local `main` branch on a pull request.**
Only the remote-tracking ref exists.

Measured, simulating a PR checkout:

    git clone --no-local --no-checkout <repo> D
    git -C D checkout --detach FETCH_HEAD
    git -C D rev-parse --verify -q main         -> main: DOES NOT RESOLVE
    git -C D rev-parse --verify -q origin/main  -> origin/main: resolves

And the failure that produces:

    python3 docs/reviews/check-review-coverage.py --ref main-does-not-exist
    git rev-list 8695101..main-does-not-exist failed: fatal: ambiguous argument
    This is a BROKEN INSTRUMENT, not a finding. Exit 3.
    EXIT=3

This is exactly the gate task #119 exists to turn green and wire. The day
it is wired it exits **3** on every pull-request run - not 0, not 1, but
the code reserved for "the instrument is broken". A reviewer chasing that
would be chasing an instrument failure that is really a configuration
default.

Two conditions, not one. `CONTAINER_BASE = 8695101` also needs history:
`actions/checkout` defaults to `fetch-depth: 1`. `ci.yml` already knows
this and sets `fetch-depth: 0` on three jobs (`:117`, `:658`, `:1471`),
with a comment at `:644-655` recording that omitting it *"cost three CI
rounds to find"*. Two further checkouts (`:1557`, `:1610`) do not set it.

**Suggested fix**, both halves:

1. `check-review-coverage.py:236` - `default="origin/main"`, matching the
   docstring at `:4`, which has been right all along. Extend the `help`
   to say why: *"a named REMOTE ref; under actions/checkout no local
   branch exists on a PR"*.
2. When the step is wired, put it in a job whose checkout sets
   `fetch-depth: 0`, and add a control that runs the checker against a
   detached clone with no local `main`, asserting exit != 3.

### R15-H2 (High) - four harnesses guard with `git diff`, which is blind to the index, and one documents the wrong reason

`scripts/check-u3-audit-controls.sh:52,107,121`
`scripts/check-u3-audit-amputation.sh:52,112,126`
`scripts/check-u4-client-controls.sh:51,96,110`
`scripts/check-u4-client-amputation.sh:47,107,121`
`docs/reviews/probe-audit-row-container.sh:166,168`

Three roles in each file, all using `git diff --quiet`: a **preflight**
that refuses a dirty tree, a **landing check** that the mutation applied,
and a **restore check** after `git checkout -- "$file"`.

`git diff` compares the worktree against the **INDEX**, not against HEAD.
`git checkout -- <file>` also restores from the **INDEX**. So a
*staged* modification is invisible to all three, and the code says so
incorrectly - `check-u3-audit-controls.sh:105`:

```
  # not the code. `git diff` compares the whole file against the commit and
  # cannot be fooled that way.
```

That sentence is false. It is the justification the guard rests on.

Measured end to end in a scratch repo:

    file staged-modified, worktree == index
    git diff HEAD --quiet : says DIRTY (correct)
    git diff --quiet      : says CLEAN -> PREFLIGHT PASSES, harness proceeds
    ... mutate, then `git checkout -- f.py` ...
    after 'git checkout --': STAGED CHANGE
    HEAD actually contains: original
    RESTORE CHECK (line 121): says RESTORED OK

So the harness runs its whole mutation matrix against a tree that differs
from HEAD, having asserted it does not, and then certifies a "restore"
that restored the wrong content. Every verdict in that run is a
measurement of a tree nobody declared.

This is the sibling of open task **#150**, which records the same defect
in the `ci.yml`-mutating control - *"its dirty-check is blind to the
index, the same defect I fixed in my own probe an hour earlier"*. That
was fixed at one site. **These five were never swept.** Fourteen other
harnesses in `scripts/` carry a header comment saying to use `cmp` rather
than `git diff`; these are the ones that did not get it. A partial sweep
selects for the instance nobody listed.

**Suggested fix:** at all five files, replace `git diff --quiet -- "$f"`
with `git diff --quiet HEAD -- "$f"` in the preflight and restore checks,
and restore with `git checkout HEAD -- "$f"` rather than
`git checkout -- "$f"`. The landing check is the one place plain
`git diff` is acceptable (it only needs "the worktree changed"), but
using `HEAD` there too costs nothing and removes the reader's need to
know which of the three is which. Then correct the comment at
`check-u3-audit-controls.sh:105`: `git diff` compares against the INDEX,
and that is precisely why the guard needed `HEAD`. Add one control per
file that stages a change and asserts the preflight refuses.

### R15-M1 (Medium, STILL OPEN from R13-M3) - a checker name in a string still reads WIRED

`docs/reviews/check-checkers-are-wired.py:502`

```python
wired = [n for n in names if n in text]
```

R13 filed this as M3 against `:300`; the file has grown and the line is
now `:502`, unchanged. The whole file exists because *"the obvious census
counts a name in a COMMENT as wired"* (docstring `:13-22`).
`strip_comments` removed the `#` case. The membership test is still a
bare substring over concatenated `run:` bodies, so a name quoted in an
`echo`, a heredoc, a `--help` string, or passed as an argument to
something else still reads WIRED - the false-positive direction, which is
the one that manufactures silent coverage claims.

**Confirmed still latent, not live.** I swept all three workflows for a
checker basename in a non-executed position and found none. `ci.yml:1286`
passes `check-suite-floor-amputation.sh` as an argument, but that file
lives in `scripts/`, which the container at `:41-48` deliberately
excludes, so it is not in `names`.

Note the sting: were a `docs/reviews/check-*.sh` name ever passed as an
argument to `ci-harness-gate.sh`, it would read WIRED, and because three
of the four `UNWIRED_BY_DECISION` entries are `.sh` controls, the
**stale-exemption** branch (`:507`, `:530-535`) would then fail the build
for a checker that is still not wired. The latent defect fails in the
loud direction, which is luck rather than design.

**Suggested fix:** reuse the machinery already in this file. `_commands()`
and `_script_of()` already tokenise a step body and identify the script a
command runs. Replace the substring test with:

```python
invoked = {pathlib.PurePath(s).name
           for tokens in _commands(text)
           for s in [_script_of(tokens) or (tokens[0] if tokens else "")]}
wired = [n for n in names if n in invoked]
```

extended to recognise `bash <script>` and `ci-harness-gate.sh <name>` in
command position. Add a control asserting
`bare_python_steps`-style: a body of `echo "docs/reviews/<a real checker>"`
must read UNWIRED. That is one row in `--self-test`, which already has
26 passing.

### R15-M2 (Medium, STILL OPEN from R14-R1-M2) - the display caps are still silent

`docs/reviews/check-review-coverage.py:298,300`

```python
for sha in untouched[:15]:
for sha, unread in partial[:10]:
```

R14-R1 filed this as M2 with a suggested fix and it is unimplemented. The
brief that dispatched *this* round carried a wrong population number, and
this checker prints exactly 15 `NONE` rows whatever the true count is.
The two caps differ (15 and 10), so a reader who learns one does not
learn the other.

**Suggested fix** (R14-R1's, unchanged and still right): after each loop,

```python
if len(untouched) > 15:
    print(f"  ... and {len(untouched) - 15} more not listed")
```

and the same for `partial`. A display that says it is truncated cannot be
read as a population. Two lines.

### R15-N1 (Nit) - the docstring's usage line and the code's default disagree

`docs/reviews/check-review-coverage.py:4` writes the invocation as
`[--ref origin/main]`; `:236` defaults to `main`. H-1 argues the
docstring is the correct one. Even after H-1 is fixed this is worth a
line, because the usage example is what a reader copies.

**Suggested fix:** folded into H-1 - change the default, and the two
agree with no further edit.

---

## 3. What I verified as CORRECT

Reported because a review that lists only defects gives no sense of what
the machinery gets right.

- **`check-checkers-are-wired.py` is a genuinely good instrument.**
  It enumerates its container from `git ls-files` rather than a hand-kept
  list (`:116-146`), asserts itself into its own population by control
  rather than by comment (`:436-446`), derives its control subjects from
  the population instead of naming them (`:344-364`), and carries a
  negative arm that is explicitly load-bearing (`:408-411`). Its
  `_script_of` walk is flag-tolerant by tokenising rather than by a wider
  regex, and the docstring says why the wider regex was the wrong repair.
  This is the file that should be copied when the next census is written.

- **The exemption shape is consistent and enforced.** Both
  `UNDECLARED_BY_HISTORY` / `RECORD_PATHS` (`:112`, `:148`) and
  `UNWIRED_BY_DECISION` (`:109-113`) refuse a blank reason with an
  assertion, and `check-checkers-are-wired.py` additionally checks the
  **reverse** direction - an exemption naming a wired checker is a
  failure, not a nit (`:507`, `:530`). I could not find a hand-kept list
  in either file that is blind to a member; both enumerate containers.

- **The record ruling holds and is counted, not silent.**
  `check-review-coverage.py:290-296` prints `records_skipped` (18 in my
  run) and then prints every `RECORD_PATHS` entry with its reason. An
  exemption that reports itself on every run is the right shape.

- **`git()` exits 3, distinct from a finding's 1** (`:178-191`), and both
  files use it consistently. A broken instrument and a real finding do
  not share an exit code.

- **Gates, all run with CI's exact invocation, each exit code on its own
  line:**

      uv run --frozen python docs/reviews/check-checkers-are-wired.py    (ci.yml:241)
      -> 27 checkers, 80 run steps, WIRED 23, EXEMPT 4                   EXIT=0

      uv run --frozen python docs/reviews/check-checkers-are-wired.py --self-test
      -> run steps parsed: 80 (across ci.yml, mirror.yml, pr-title.yml)
      -> 26/26 controls passed                                          EXIT=0

      python3 scripts/check-harness-anchors.py --self-check --floor 458  (ci.yml:873)
      -> harnesses scanned: 34, anchors resolved: 458, all resolve       EXIT=0

      python3 docs/reviews/check-review-coverage.py                      (unwired)
      -> NONE 131                                                       EXIT=1

      python3 docs/reviews/check-review-coverage.py --ref origin/main
      -> NONE 128                                                       EXIT=1

      python3 docs/reviews/check-review-coverage.py --ref main-does-not-exist
      -> BROKEN INSTRUMENT                                              EXIT=3

  The anchor floor 458 was read out of `ci.yml:873`, not from a brief; the
  `--self-check` floor is exact, not slack.

---

## 4. The new NONE count

With this document's declaration in place, re-measured at `10ac6cf`:

    python3 docs/reviews/check-review-coverage.py
      DECLARED  REVIEW-R15.md: 8695101..0b149b9
                239 commits, paths: docs/reviews scripts .github
      Trunk commits on main since 8695101: 239
      Fully covered - range AND every path: 200
      PARTIALLY covered - some files claimed by nobody: 39
      COVERED BY NOTHING: 0
      Record files skipped: 35
                                                         EXIT=1

**`COVERED BY NOTHING` goes 131 -> 0.** `Fully covered` goes 108 -> 200.
`PARTIALLY covered` goes 0 -> **39**, exactly the number §1c predicted
before this document was written, which is the check on that prediction.

**The gate still exits 1, so it must still NOT be wired.** That is the
point of §1c: the brief expected this round to clear the backlog, and it
clears only the `NONE` half. Two things must land before
`check-review-coverage.py` can be wired green:

1. the complementary path round of §1c, taking PARTIAL 39 -> 0, and
2. **R15-H1**, without which the wired step exits 3 on every PR
   regardless of the counts.

`records_skipped` rises 17 -> 35 as a side effect: a record file is only
counted once some round claims its commit, so extending coverage makes
previously-invisible record files visible to the counter. The number
going up is the exemption reporting itself correctly, not a regression.

---

## 5. What I could NOT settle, and what I did not attempt

**Could not settle:**

- **Whether R15-M1 has ever been live.** I swept the three current
  workflows and found no checker basename in a non-executed position, so
  it is latent *today*. I did not sweep the workflow files at every
  historical commit in the uncovered span, so I cannot say the false
  WIRED never fired and silently excused a checker in the past.

- **Whether the 39 residual PARTIAL commits contain anything.** I
  enumerated the files that hold them back and read none of those files'
  diffs. That is the complementary round's job and I am not claiming it.

- **Depth of reading across 105 `docs/reviews/` touches.** I read
  `check-review-coverage.py` and `check-checkers-are-wired.py` in full,
  read the specific sites in the four harnesses and the probe named in
  H-2, and swept **all** of `docs/reviews/` and `scripts/` for the six
  defect classes the brief named (`git diff` without `HEAD`; display
  caps; hand-kept lists; stale anchors; controls omitting an argument;
  gates run without CI's flags). I did **not** read all 105 touches line
  by line. My `PATHS` declaration should be read as: these paths were
  swept for these classes and the two central files were read whole.

**Did not attempt:**

- Running the full suite (`check-suite-floor.sh 887`) or the harness
  matrix. My paths are the checkers, not `src`/`tests`, and neither
  floor moves from a review document. Tier 0 should run the full gate
  before folding this branch, per the standing rule.

- Wiring `check-review-coverage.py`. Explicitly reserved to Tier 0, and
  in any case H-1 must land first: wiring it today gives exit 3 on PRs.

- Any change to `docs/DESIGN.md`, any merge, any push, any ref outside
  `review/r15`. `fmj-worktrees/tally-shapes`, `tally-rebuild` and `w148`
  were not touched.

---

## 6. Worktree

`fmj-worktrees/r15` on branch `review/r15`, cut from `main` at `0b149b9`.
Left in place for Tier 0 to merge; it holds this document and nothing
else. Remove it after the merge.
