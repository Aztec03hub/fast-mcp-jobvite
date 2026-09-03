# Shell hygiene: tasks #32 and #34

Agent: `shell-hygiene`. Base SHA `c5bdeb6`, branch `chore/shell-hygiene`,
worktree `/tmp/shell-work` (removed - see the last section).

**Headline, the two numbers you asked for:**

- **The anchor floor is now 164**, up from 154. `ci.yml:419` says `--floor 154`
  and is yours to change.
- **The shellcheck hook is NOT wired**, and should not be until two one-line
  fixes land in `scripts/check-u5-jobs-*.sh` - files I was told not to touch.
  Everything else is done. The exact patch is in section 2.

---

## 1. Task #34 - the anchor checker now reads `sed -i`

Commit `9eed403`.

I took option (a) from the task: teach the checker a fifth shape. Option (b)
would have rewritten the mutation mechanism of a harness that works, and the
edit I was making to it for #32 was a dead variable and a comment, not its
mechanism - so "editing it anyway" was not true in the sense the task meant.

**Shape D.** Every double-quoted argument containing `sed -i` is tokenised with
`shlex`, its `s///` and `/addr/d` commands are scanned out, and each pattern is
translated from POSIX BRE to a Python regex before matching, line-wise.

Two things in there are not incidental, and both are the kind of detail that
would have made this silently wrong:

- **The script is SCANNED, not split on `;`.** U0 carries
  `s|# transitive prerelease; must be named or resolution fails||`, whose
  pattern contains the separator. A `split(";")` would have mangled that row
  into two unparseable fragments.
- **BRE is not Python.** In a BRE `(`, `)`, `{`, `}`, `|`, `+` and `?` are
  ORDINARY characters and `\(` is the group - the exact opposite of Python.
  None of U0's eleven current patterns contain one, so passing them to `re`
  unchanged would have worked perfectly today and broken silently on the first
  row anyone added with a paren in it. The translator is `_bre_to_python`.

**Anything it cannot read is a `ParseError`, never a skip** - an unreadable row
that quietly vanishes from the count is the exact defect this checker exists to
catch, one level up.

### 1a. FINDING (medium, FIXED): the shape found a dead mutation on its first run

    STALE ANCHOR  check-u0-test-controls.sh:158 [sed-bre]  0 hits in pyproject.toml
        anchor: '^  "-m",$'

The row "remove the -m selection from addopts" carried two sed expressions:

    sed -i '/"not credentialed and not network",/d; /^  "-m",$/d' pyproject.toml

The second one matched nothing. `-m` and its value are on **one** line of
`addopts` - `pyproject.toml:132` reads `  "-m", "not credentialed and not network",`
- so `/^  "-m",$/` had nothing to match.

Verified three ways, not just by the new parser:

- `grep -n '^  "-m",$' pyproject.toml` -> no match (grep BRE, same dialect).
- Running the real `sed` command against a copy deletes **one** line, 132, and
  `diff` shows only that line. Both expressions together do what the first does
  alone.
- The control still FIRED before and after, because the first expression deletes
  that line by itself. That is exactly why it survived eight review rounds: the
  row was never vacuous, only half of it was dead.

Fixed by deleting the dead expression, with a comment recording why.

### 1b. FINDING (medium, FIXED): `SKIP_TOP`, and prose describing a mechanism the code lacks

This is the #32 item you flagged, and it is the real defect of the batch.
`SKIP_TOP=(.git .venv venv node_modules)` was declared at
`check-u0-test-controls.sh:72` and read by nothing - `grep -rna SKIP_TOP .
--exclude-dir=.git` returned that declaration plus four lines of
`BASH-STANDARD-REPORT.md` quoting it, and nothing else.

Worse than the dead array: the eleven-line comment above it said *"THE UNIT OF
STAGING IS NOW THE TREE, with a deny-list of things that must not be copied"*
and *"A deny-list fails the other way"*. **There is no deny-list.** `stage()`
uses `git ls-files` and excludes nothing; untracked build artifacts are absent
for free because git does not track them, which is why a deny-list was never
needed in the first place.

Both are gone and the paragraph is rewritten in place to describe what `stage()`
actually does. I did not append a correction.

### 1c. FINDING (high, FIXED): the checker's own controls harness staged an allowlist

`build_tree()` copied `scripts` and `src` and nothing else. That was true of
what the anchors pointed at on the day it was written. The moment shape D
landed, U0's rows arrived pointing at `.env.example`, `.gitignore`,
`pyproject.toml` and `tests/conftest.py` - none staged - and **five of seven
rows went red reporting "target file does not exist" about files that exist.**

That is the same defect `check-u0-test-controls.sh` has now hit five times and
whose comment is three paragraphs long. It now stages the tracked tree via
`git ls-files`, with a positive control on the staging, so the next anchor into
a new file needs no edit there.

### 1d. FINDING (high, FIXED): a SECOND copy of the floor, inside the floor's own harness

`check-harness-anchors-controls.sh:168` read `--floor 154`. The checker's
docstring says the floor lives in `ci.yml`, "the one place the suite floor
lives" - and here was a second copy of it, in the very harness that exists to
prove the floor works.

This would not have failed loudly. At 164 anchors, a hard-coded 154 is *below*
the intact count, so row F1 would have gone green whether or not the deleted
shape mattered. It is now read back out of the intact run:

    intact=$(printf '%s\n' "$before" | sed -n 's/^anchors resolved: //p')

with a guard that makes an unreadable count a **SURVIVOR**, not a silent pass -
because `total < 0` is never true, so a fallback of 0 would have made the
floored arm exit 0 and the row pass while testing nothing.

My first version of this derivation kept `--quiet` on the intact run. `--quiet`
suppresses the `anchors resolved:` line. It reported `F1: could not read the
intact anchor count` and failed - which is the only reason it is not still there
reading an empty string.

### 1e. Shape D is covered in both directions

Adding a parser shape with no control would have made it a rule that has only
ever passed. Two new rows:

- **P3** (positive): invalidate a live `sed -i` anchor in the copy, require
  exit 1. The subject is **derived** - the checker is imported and asked which
  sed anchors it reads, the first is taken, and a character is inserted into the
  middle of the text it actually matches. So it cannot rot into breaking a
  pattern no row uses, which is how `probe-bash-namespace-amputation.sh` went
  vacuous within the hour.
- **A5** (amputation): the same broken tree with `_shape_d` deleted, require
  exit 0.

One measured note worth keeping: `importlib` + `@dataclass` needs the module
registered in `sys.modules` **before** `exec_module`, or dataclasses.py dies
with `AttributeError: 'NoneType' object has no attribute '__dict__'` - an error
that names nothing relevant.

### 1f. Coverage this does NOT add

`check-u0-test-controls.sh:150` mutates with
`printf '!secrets/prod.key\n' >> .gitignore`. **An append has no anchor**, so
there is nothing for a static checker to resolve, and shape D correctly
contributes nothing for it. Ten sed invocations yield eleven patterns; the
eleventh row is that append. Not a gap I can close - stated so it is not
mistaken for one later.

---

## 2. Task #32 - shellcheck. Measured, mostly fixed, DELIBERATELY NOT WIRED

### 2a. The re-measurement, at c5bdeb6, shellcheck 0.10.0

You were right to demand it, and the stale part was not the one anyone expected.

`bash-standard` measured `scripts/*.sh` and recorded "15 scripts". At `c5bdeb6`
that population is **18**. The counts:

| severity | scripts/*.sh at c5bdeb6 | BASH-2 row's record at eb4d254 |
|---|---|---|
| error | 0 | 0 |
| warning | 3 | 3 |
| info | 13 | 10 |
| style | 17 | 2 |

The warning count survived the four new scripts unchanged - they are clean at
that severity. **The info and style counts in the BASH-2 row are wrong for the
current tree**, and `style` is off by a factor of eight.

### 2b. FINDING (high): the measured population was the wrong population

**`scripts/*.sh` is not what the hook scans.** The upstream hook is

    - id: shellcheck
      language: docker_image
      entry: docker.io/koalaman/shellcheck:v0.10.0
      types: [shell]

`types: [shell]` selects **files**, by shebang and extension, not a directory.
There are **21** tracked shell files here, not 18: three probes live under
`docs/reviews/`. Repo-wide at `--severity=warning` the count was **4**, not 3.

Every artifact in this chain - the BASH-2 row, the task description, my
dispatch - carried the scripts-only number. Nobody was wrong on purpose; the
directory was never the boundary the gate would use. I enumerated the container
(`git ls-files | grep -E '\.sh$'`, cross-checked against a shebang scan of every
tracked file, which returned the same 21) rather than trusting the list.

### 2c. Fixed: 2 of the 4

- `check-u0-test-controls.sh:72` SC2034 `SKIP_TOP` - see 1b. Commit `9eed403`.
- `docs/reviews/probe-bash-namespace-amputation.sh:18` SC2034 `MAP` - declared,
  read by nothing, in a file whose very next paragraph exists to say the
  artifact is read from the row and never hard-coded. Commit `91152a2`.

I took the probe because `docs/reviews/*.sh` is named in nobody's scope: your
concurrency note gives `r4-fixes` `src/`, `tests/` and `scripts/check-u5-jobs-*.sh`.
Flagging it explicitly rather than assuming, since it is outside the
`scripts/*.sh` you granted me.

### 2d. NOT FIXED, NOT MINE - and this is what blocks the hook

    scripts/check-u5-jobs-amputation.sh:75:9: warning: Declare and assign separately
      to avoid masking return values. [SC2155]
    scripts/check-u5-jobs-controls.sh:66:9: warning: Declare and assign separately
      to avoid masking return values. [SC2155]

**These are the exact two files your dispatch reserved for `r4-fixes`.** Task
#32's step 1 asks for these two fixes; the concurrency rule in the same dispatch
forbids me the files. I followed the concurrency rule - a collision costs more
than a round-trip - and I am reporting the conflict rather than picking.

Suggested fix, both files, one line becoming two:

```diff
--- a/scripts/check-u5-jobs-amputation.sh
+++ b/scripts/check-u5-jobs-amputation.sh
@@ -75 +75,2 @@
-  local backup="$BACKUP_DIR/${ROWS}_$(echo "$file" | tr / _)"
+  local backup
+  backup="$BACKUP_DIR/${ROWS}_$(echo "$file" | tr / _)"

--- a/scripts/check-u5-jobs-controls.sh
+++ b/scripts/check-u5-jobs-controls.sh
@@ -66 +66,2 @@
-  local backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
+  local backup
+  backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
```

### 2e. I PROVED the end state instead of predicting it

`bash-standard`'s note said "the 3 fixes take it to 0" was a prediction it could
not test. I did not repeat that. I copied the worktree to `/tmp/sc-proof`,
applied the two U5 fixes there **without committing them**, and ran shellcheck
over all 21 tracked shell files:

    $ shellcheck --severity=warning --format=gcc $(git ls-files | grep -E '\.sh$')
    $ echo $?
    0

**Zero output, exit 0.** With those two lines fixed the hook lands green
repo-wide. That is measured, not forecast.

### 2f. Why the hook is not in this branch

Your instruction was one commit, not two, because `.pre-commit-config.yaml:61-67`
records this project landing a knowingly-red gate on the secret scanner. I
cannot make that one commit: the fixes it depends on are in files I must not
touch, and adding the hook without them reproduces D3 exactly - and worse,
`ci.yml:561` runs `pre-commit run --all-files`, so a red hook turns **CI** red,
not just local commits.

So the hook is not here, and the recommendation is sequenced, not withheld:

1. `r4-fixes` lands the two SC2155 lines above (or you apply them once
   `check-u5-jobs-*.sh` is free).
2. Add the block from `bash.md:764-768` verbatim, at the rev the standard names:

```yaml
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.10.0
    hooks:
      - id: shellcheck
        args: ['--severity=warning']
```

3. Flip BASH-2 to MET in the same commit.

**One adoption note before you do.** That hook is `language: docker_image` - it
pulls `docker.io/koalaman/shellcheck:v0.10.0` and needs a working Docker daemon
on every developer machine at every `git commit`, and in CI. Docker works here
and `ci.yml` runs `ubuntu-latest` with no `container:`, so both are fine today.
But `CONTRIBUTING.md:14` makes `pre-commit install` mandatory, and this is the
first hook in the file that will hard-fail for anyone without Docker running.
It is what `bash.md:764` prescribes and a `priority: required` clause outranks
my preference, so I am flagging it, not proposing a deviation. If it does bite,
the reviewable alternative is a `language: system` local hook wrapping a pinned
binary - but that is an ADR-shaped decision, not mine.

### 2g. BASH-2's row is stale in three ways - and it is not mine to edit

`PREAMBLE.md` says `docs/OBLIGATIONS.md` is not mine to hand-edit, so I have
not. The row should **stay ABSENT** - nothing runs shellcheck yet. But its
prose is now wrong in three places:

- *"over all 15 scripts"* - the population is 18 under `scripts/`, and **21**
  under the gate the clause actually specifies.
- *"0 error, 3 warning, 10 info, 2 style"* - info is 13 and style is 17 at
  `c5bdeb6` for `scripts/*.sh`.
- *"3 findings in 2 files"* - the three warnings were in **three** distinct
  files (`check-u0-test-controls.sh`, and both `check-u5-jobs-*.sh`), and
  repo-wide there were four in four.

Suggested replacement for the last sentence of the row, for whoever wires the
hook:

> Measured at `c5bdeb6` with shellcheck 0.10.0 over the **21 tracked shell
> files** the hook's `types: [shell]` selects - not `scripts/*.sh`, which is 18
> and is not the gate's boundary: **0 error, 4 warning**. Two are now fixed
> (`SKIP_TOP`, `MAP`); the remaining two are one `local`-split each in
> `scripts/check-u5-jobs-*.sh`, and with them applied the gate exits 0
> repo-wide (measured, not predicted). Left ABSENT rather than wired, because
> wiring the hook without those two lands a red gate - and `ci.yml:561` runs
> `pre-commit run --all-files`, so it would be red in CI, not only locally.

`docs/reviews/check-obligations.py` is clean on my branch, verbatim:

    Mappings: 31  |  anchors verified against their subject: 23  |  recorded as absent: 8
    Every mapped anchor still contains its subject. OK.
    exit 0

    ...
    8/8 controls fired.
    --- negative controls (these must NOT fire) ---
      tolerated     artifact shifted by five lines (B49)
    post-run re-check of the real OBLIGATIONS.md: exit=0
    exit 0

---

## 3. YOUR EDITS - `ci.yml`, which I did not touch

Three of them, all in the region tasks #22/#33 were queued against.

**(1) `ci.yml:419` - the floor. Required, or CI keeps passing on stale coverage.**

    - run: python3 scripts/check-harness-anchors.py --self-check --floor 154
    + run: python3 scripts/check-harness-anchors.py --self-check --floor 164

**(2) `ci.yml:416` - a measurement in the comment above it is now stale.**

It says *"deleting one shape drops 154 to 139 with an exit code of 0"*. On my
branch, deleting shape C drops **164 to 149**, exit 0 - quoted verbatim from the
F1 row:

    no floor:   anchors resolved: 149
    with floor: FAIL: only 149 anchors were resolved, below the floor of 164.

**(3) `ci.yml:453-456` - this comment is now FALSE and reads as a live caveat:**

> NOTE, measured while wiring these gates: this is the one harness whose
> anchors `scripts/check-harness-anchors.py` cannot read, because it mutates
> with `sed -i` expressions rather than literal anchors. The checker NAMES it
> on every run rather than reporting a clean zero over it.

Suggested replacement:

> NOTE: this harness mutates with `sed -i` expressions rather than literal
> anchors. The checker read none of them until shape D landed - it NAMED the
> harness as an unread mechanism rather than reporting a clean zero, which is
> why that gap was a task and not an incident. It now contributes 11 of the
> 164 anchors, and found a dead expression in one of them on its first run.

---

## 3b. Task #39 - `--anchors-applied` passed a harness that ran zero rows

Added to my scope by the team lead after the first report; found by `r4-fixes`,
which took the per-harness half. This is the generic half.

`scripts/ci-harness-gate.sh:207` tested `[ "$rows" -ne "$applied" ]`. At
`rows=0, applied=0` that is FALSE, so a harness that ran **no rows at all**
passed the gate. It affects every harness gated that way, not only U5's.

**The script disagreed with itself**, which is what makes it a defect rather
than a decision. Its two sibling branches already refuse their own zero:

| flag | guard | line |
|---|---|---|
| `--controls-fired` | `[ "$total" -eq 0 ]` | 174 |
| `--result-killed` | `[ "$killed" -eq 0 ]` | 190 |
| `--anchors-applied` | **none** | 207 |

I swept the rest of the script for the same shape rather than fixing only the
reported line. `--min-rows` is safe (`0 < N` is true, and the branch is guarded
by `min_rows > 0`); the `--require` loop is a presence check, which fails
correctly on absence. `--anchors-applied` was the only one.

**The control was written FIRST and confirmed to fail against the unfixed
script**, which is the only thing that distinguishes it from a row that would
have passed all along:

    $ bash scripts/ci-harness-gate-controls.sh     # unfixed
      SURVIVED C24 zero rows is caught, though 0 == 0 (exit 0, wanted 1)
    23/24 controls fired.                                          exit 1

    $ bash scripts/ci-harness-gate-controls.sh     # fixed
    24/24 controls fired.                                          exit 0

C24 is deliberately named and worded to sit beside its siblings C11 ("zero
controls held is caught, though 0 == 0") and C14 ("zero mutations killed is
caught, though 0 survived"). Those two existed; the third did not, and its
absence WAS the defect.

The one live consumer is `ci.yml:445`. Run through the real gate on this branch:

    $ bash scripts/ci-harness-gate.sh check-u5-jobs-amputation.sh --anchors-applied
    ########## ROWS: 11   ANCHORS APPLIED: 11                       exit 0

`git status --porcelain` after that mutation run showed only my own two edits -
the harness restored everything it touched.

---

## 4. Gates, by exit code, on their own line

Run at the tip of `chore/shell-hygiene`.

    $ uv run --frozen ruff check .
    All checks passed!                                        exit 0
    $ uv run --frozen ruff format --check .
    62 files already formatted                                exit 0
    $ uv run --frozen mypy
    Success: no issues found in 44 source files               exit 0
    $ uv run --frozen pytest
    413 passed, 5 deselected in 25.55s                        exit 0

**413 passed, 0 skipped.** The floor derived from `ci.yml` is
`check-suite-floor.sh 413`, so the suite is exactly at it. `5 deselected` is the
credentialed/network arm the default `-m` selection removes, not skips.

Harnesses:

    $ python3 scripts/check-harness-anchors.py --self-check
    harnesses scanned: 15
    anchors resolved: 164
    OK: all 164 anchors resolve to exactly one hit in their target file.   exit 0

    $ bash scripts/check-harness-anchors-controls.sh
    9/9 controls fired.                                                    exit 0

    $ bash scripts/check-u0-test-controls.sh
    BASELINE: 413 passed, 5 deselected in 40.10s
    11/11 controls fired.                                                  exit 0

`git status --porcelain` after every harness run was empty. Ruff's own reformat
of `_shape_d` moved lines after the controls first passed, so **all three
harnesses were re-run after the reformat** and the numbers above are the
post-reformat run - the A5 amputation anchor could have moved and did not.

Three lint findings were in my own new code (one W505, two E501) and are fixed
in `9eed403`'s follow-up; they never left the worktree.

---

## 5. What I did NOT verify

Things I could not settle, not things I skipped.

- **The hook has never been executed.** Every claim in section 2 about what
  `shellcheck-precommit` would report is from the pinned `shellcheck` binary
  invoked directly, at the same rev and the same `--severity=warning`. I did not
  run `pre-commit run shellcheck --all-files`, because adding the hook to run it
  is the thing I decided not to do. If its file selection differs from
  `git ls-files | grep '\.sh$'` in some way I have not anticipated - a file
  `identify` calls shell that neither my extension filter nor my shebang scan
  caught - my "exit 0 repo-wide" is a claim about my selection, not the hook's.
  It is one `pre-commit try-repo` away once the two U5 lines land.
- **Docker in CI is inferred, not observed.** `ubuntu-latest` with no
  `container:` key, and a working daemon locally. I did not push a branch to see
  the hook pull the image.
- **`_bre_to_python` is exercised only by U0's eleven current patterns**, none
  of which contain `(`, `|`, `+`, `?`, `{` or a bracket expression. The
  translation of those constructs is written from the POSIX/GNU BRE rules and
  is **not covered by a control**. The next row that uses one is where it gets
  its first real test. A table-driven unit test over the translator would close
  this; I judged it out of scope for these two tasks rather than beneath
  notice - it is worth a task if anyone adds a pattern with a metacharacter.
- **The `info` and `style` findings (13 and 17) I counted but did not read.**
  The clause's own threshold is `--severity=warning` and that is what I worked
  to. Whether any of the 30 is a real defect is unexamined.
- **`shfmt`** is prescribed alongside shellcheck at `bash.md:770-774` and is not
  wired either. Out of scope for #32, unmeasured by me, and not represented in
  OBLIGATIONS as far as I looked (`grep -n "BASH-" docs/OBLIGATIONS.md` returns
  BASH-1 and BASH-2 only).

## 6. Worktree

`/tmp/shell-work` was removed with `git worktree remove` after the final gate
run. `git worktree list` was checked before I created it and I moved no ref
outside my own branch. I did not push; `chore/shell-hygiene` is local, two
commits on top of `c5bdeb6`, and is yours to merge.
