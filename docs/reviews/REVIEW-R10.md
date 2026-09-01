# REVIEW-R10 - `dad014e..3e0c8ae`

<!-- REVIEW-COVERS: dad014e..3e0c8ae -->

**Reviewer:** `review-r9`, fresh. Nothing here was reconstructed from the author's task records or
commit messages; every claim below was re-derived from the code, from `git`, or from a probe run in
this worktree.

**Worktree:** `/home/plafayette/claude_projects/fmj-worktrees/review-r9`, detached at `3e0c8ae`,
branch `review/r9`.

**Scope:** 13 commits, 33 files, +641/-116. This range was merged and pushed without a review round.

**What the `REVIEW-COVERS` declaration above does and does not claim.** It is the range I read:
`git log --oneline dad014e..3e0c8ae` is 13 commits, `dad014e` is a true ancestor of `3e0c8ae`, so
the range is linear and `dad014e` itself - task #114's merge - is correctly excluded, having been
the previous round's endpoint rather than mine.

Two edges the range does not capture, stated so the declaration is not read as more than it is:

- **Findings reach outside it.** R10-H1 is largely about `check-u0-test-controls.sh`,
  `check-u11-advisory-controls.sh` and the two `check-u15-gate-*.sh` harnesses, and R10-N1 is about
  `check-settings-are-read.py:99` - **none of which this range modifies.** I found them by
  enumerating the container the range's work claimed to have swept. Declaring the range does not
  declare those files reviewed; it declares these 13 commits reviewed.
- **Reading is not reviewing.** I read many files at `HEAD` for context - ADRs, `ci.yml`,
  `PREAMBLE.md`, whole harnesses - without reviewing the commits that produced them. Only the 13
  are covered.

**On the round number.** I was dispatched as "R9" and this document was first written under that
name; the orchestrator corrected it mid-round. `docs/reviews/CODE-REVIEW-R9.md` already exists,
written 2026-08-29 by a different agent also called `review-r9`, covering `8695101..f699f74`. This
is **R10**, findings are numbered `R10-*`, and the file follows the directory's dominant
`REVIEW-R<n>.md` convention. The branch is `review/r9`, left as created rather than churned.

**A 45-commit hole between the two rounds - reported, not reviewed.** The existing R9 ends at
`f699f74`; this round starts at `dad014e`. Measured:

```
$ git merge-base --is-ancestor f699f74 dad014e && echo "clean linear range"
clean linear range
$ git log --oneline f699f74..dad014e | wc -l
45
```

**45 commits have never been covered by any review round.** They are not a merge artifact - the
range is linear. It runs from `b0e2e19` ("An unreadable file was silently treated as NOT exempt,
and repointed") through `dad014e`, and includes `46f401d`, the ADR-0025 merge that **re-froze
`docs/DESIGN.md`** - which is the same artifact R10-M1 finds has since drifted. I did not expand
scope to review them; this is the count, for dispatch.

---

## Gates, run argument for argument, each judged on its own exit code

| Gate | Command | Result |
|---|---|---|
| lint | `uv run --frozen ruff check .` | `All checks passed!` exit 0 |
| format | `uv run --frozen ruff format --check .` | `105 files already formatted` exit 0 |
| types | `uv run --frozen mypy` | `Success: no issues found in 96 source files` exit 0 |
| suite | `uv run --frozen pytest` | **868 passed, 0 skipped**, 6 deselected, 58.99s |
| suite floor | derived: `check-suite-floor.sh 868` | 868 >= 868, tight |
| anchors | `check-harness-anchors.py --self-check --floor 458` | `458 anchors resolve`, 33 harnesses, exit 0 |
| shellcheck | `shellcheck --severity=warning $(git ls-files '*.sh')` | exit 0 over 43 files |

Both floors were derived from `ci.yml`, not retyped.

**ShellCheck was proved to be inspecting, not merely exiting 0.** `~/.local/bin/shellcheck` is
present and is v0.10.0. Positive control: a planted file with `foo=1` and `echo $bar` returned
SC2034 and SC2154 at **exit 1**. A green from this binary is a green that read something.

---

## Disposition - all findings fixed on this branch

Every finding below was accepted and fixed on `review/r9` after the review was delivered. The
findings are left as written rather than rewritten into the past tense, because the measurement
that produced each one is the evidence for the fix. What changed:

| Finding | Fix | Proof it works |
|---|---|---|
| R10-H1 | nine sites bounded with `timeout -k 30 900`; new `scripts/check-pytest-bounded.sh`, **wired** in `ci.yml` | 73/73; guard watched red on both spellings, green when bounded |
| R10-M2 | `classify()` lifted out; four detector controls added | all four amputations now killed, 6/6 controls |
| R10-L1 | exempt count printed | `20 line(s) skipped as REPOINT-EXEMPT` |
| R10-L2 | `return 1` in the 124 branch | no verdict emitted for a hung row |
| R10-N1 | `tokenize` replaces `split("#", 1)` | a read after a `#` inside a string is now seen |
| R10-N2 | `-k 30` folded into every bounded site | - |
| R10-N3 | recorded; the durable fix is #116 | - |
| R10-M1 | **NOT MINE.** Taken by the orchestrator - the freeze pointer and `AUDIT-SHAPES.md` are untouched here | - |

**Bounding was not enough on its own, and that is the part worth keeping.** Six of the nine sites
would have MISREAD a timeout rather than merely tolerated one, and in five of those the misreading
was in the *reassuring* direction:

- `check-u15-gate-amputation.sh` parses survivors from `^PASSED` lines. A hung run prints none, so
  a timeout reported `survivors: NONE` - this harness's **best possible result**.
- `probe-audit-row-container.sh` judges `rc == 0` to mean VACUOUS. A timeout is non-zero, so a hang
  scored as "the failure is recorded by a test" when nothing ran.
- `probe-r4-unmutated-anchors.sh` judges `rc != 0` to mean KILLED, so a hang scored as a kill.
- `check-u15-gate-controls.sh`'s control site does not capture the exit code at all; it greps the
  report. A hung run reads as `DID NOT FIRE` and is counted as HELD.

So every one of those sites now names the hang with the literal phrase `TIMED OUT`, which is what
`ci-harness-gate.sh` greps for, and refuses to emit a verdict for the row. A bound that stops a
hang but lets it be scored is half a fix.

---

# Findings

## R10-H1 - #108's "64 of 64" is true for its selector, and the selector is blind to 9 more pytest invocations, every one of them unbounded

This is the finding the task was about, one level up. The selector
`grep -nE 'uv run --frozen pytest' scripts/*.sh` is narrow in **two independent ways**, and each
one hides sites the other does not:

- **by spelling** - four harnesses hold the interpreter in an array and invoke `-m pytest`;
- **by path** - `scripts/*.sh` cannot see the seven tracked `.sh` files in `docs/reviews/`, three
  of which call `uv run --frozen pytest` unbounded.

The true denominator is **64 of 73**. Nine sites are unbounded, and **`grep -c timeout` over each
of the six files involved returns 0** - not one of them bounds anything, anywhere.

I record that I got this number wrong on my first pass. I enumerated the `-m pytest` spelling,
found seven, and wrote "71" into this report before running the guard I was proposing. Running it
returned 73/64 and surfaced three more in a directory I had already been told, by this repo's own
standing lesson, not to trust a path list about.

Reproduced first, so the 64 is not in dispute:

```
$ grep -nE 'uv run --frozen pytest' scripts/*.sh | wc -l          -> 64
$ grep -nE 'uv run --frozen pytest' scripts/*.sh | grep -c timeout -> 64
$ grep -nE 'uv run --frozen pytest' scripts/*.sh | grep -vE 'timeout [0-9]+ +(env +[A-Z_]+=[^ ]+ +)?uv run'
  (empty - all 64 have `timeout N` directly governing the command, not merely on the line)
```

The 64 are genuinely bounded. Now the container:

```
$ grep -nE '(uv run --frozen|-m) pytest' $(git ls-files '*.sh') | grep -vE ':[0-9]+: *#' | wc -l
73
$ ... | grep -c 'timeout '
64
$ ... | grep -v 'timeout '        # THE NINE
docs/reviews/probe-r4-unmutated-anchors.sh:32:if ! uv run --frozen pytest tests/ -q -p no:cacheprovider >/tmp/r4-base.txt 2>&1; then
docs/reviews/probe-r4-unmutated-anchors.sh:76:  uv run --frozen pytest tests/ -q -p no:cacheprovider >/tmp/r4-out.txt 2>&1
docs/reviews/probe-audit-row-container.sh:90:  out=$(uv run --frozen pytest -q -p no:cacheprovider 2>&1)
scripts/check-u0-test-controls.sh:114:  out=$(cd "$work" && "${PY[@]}" -m pytest -q -p no:cacheprovider 2>&1); rc=$?
scripts/check-u0-test-controls.sh:140:base_out=$(cd "$BASE" && "${PY[@]}" -m pytest -q -p no:cacheprovider 2>&1); base_rc=$?
scripts/check-u11-advisory-controls.sh:67:  ( cd "$TREE" && "${PY[@]}" -m pytest "$SUITE_REL" -p no:cacheprovider -q \
scripts/check-u15-gate-controls.sh:60:  ( cd "$TREE" && "${PY[@]}" -m pytest "$SUITE_REL" -p no:cacheprovider -q \
scripts/check-u15-gate-amputation.sh:54:  ( cd "$tree" && env PATH="$pathenv" "${PY[@]}" -m pytest "$SUITE_REL" \
scripts/check-u15-gate-amputation.sh:71:( cd "$WORK/intact" && "${PY[@]}" -m pytest "$SUITE_REL" -p no:cacheprovider -q \
```

**Six of the nine are live in CI**, so this is not a dormant path:

```
$ grep -n 'ci-harness-gate.sh check-u0-test-controls\|check-u15-gate\|check-u11-advisory' .github/workflows/ci.yml
1009: run: bash scripts/ci-harness-gate.sh check-u0-test-controls.sh --controls-fired
1027: run: bash scripts/ci-harness-gate.sh check-u15-gate-controls.sh --controls-fired
1045: run: bash scripts/ci-harness-gate.sh check-u15-gate-amputation.sh --amputation
1048: run: bash scripts/ci-harness-gate.sh check-u11-advisory-controls.sh --controls-fired
```

The remaining three (`probe-r4-unmutated-anchors.sh`, `probe-audit-row-container.sh`) are **not**
wired in `ci.yml` - I checked, the grep is empty - so those are a developer-machine hang, not a CI
one. They are still in scope: `probe-audit-row-container.sh` is the probe `docs/briefs/AUDIT-SHAPES.md:14`
hands to task #104 as the thing to generalise, so an unbounded call is about to be copied forward.

Note the shape of the miss: the four `scripts/` harnesses that were skipped are precisely the four
that do NOT appear in this range's `git diff --name-only -- scripts/` list. The sweep touched 24
harnesses and the 4 it never opened are the 4 whose pytest call it could not spell.

This also bears directly on task #105 ("the job takes 2.5 HOURS"). Four of the harnesses CI runs
can still hang without bound.

**Suggested fix.** Two parts, and the second matters more than the first.

1. Bound the nine. The six `-m pytest` sites take `${PY[@]}`, so the `timeout` goes in front of the
   array expansion, and the four already inside `( ... )` subshells keep their parentheses:

   ```bash
   out=$(cd "$work" && timeout 900 "${PY[@]}" -m pytest -q -p no:cacheprovider 2>&1); rc=$?
   ```

   The bare-command-then-capture form is safe here for the reason established below in R10-V1
   and R10-V2.

2. Replace the spelling-shaped selector with a container-shaped one, and assert the two sets are
   equal, so the next harness that invents an eighth way to say "pytest" is caught the day it lands:

   ```bash
   # every pytest invocation, however spelled; every one must carry a timeout
   total=$(grep -nE '(uv run --frozen|-m) pytest' $(git ls-files '*.sh') | grep -vE ':[0-9]+: *#' | wc -l)
   bounded=$(grep -nE '(uv run --frozen|-m) pytest' $(git ls-files '*.sh') | grep -vE ':[0-9]+: *#' | grep -c 'timeout ')
   [ "$total" -eq "$bounded" ] || { echo "::error::$((total-bounded)) unbounded pytest call(s)"; exit 1; }
   ```

   Wire that as a `ci.yml` step. I ran both halves in this worktree: today they report `total=73`
   and `bounded=64`, and the guard exits 1 - which is the point. After part 1 they report 73 and 73.

   The selector must span `git ls-files '*.sh'`, not `scripts/*.sh`. That is not a stylistic
   preference: switching it to the path form is what hid three of these nine, and it is the same
   defect this repo has now measured in paths, in `catch {`, in prefixes, and here in a command's
   spelling. Enumerate the container; assert `bounded == total`.

---

## R10-M1 - `docs/DESIGN.md` no longer matches the SHA every reader is told is its freeze, and nothing detects that

`86ab20e` edited `docs/DESIGN.md` (the C2-T2 disposition cell). The edit itself is defensible and
the commit message reasons about it carefully. **The freeze pointer was not moved with it.**

```
$ git rev-parse aca9397:docs/DESIGN.md
e009ac415e530d08fc951445154504291d4fa9e4
$ git rev-parse HEAD:docs/DESIGN.md
639f4b720546683762e9dfc79663ce0ec87bc262
```

`PREAMBLE.md` says the design is frozen and must be read as `git show <SHA>:docs/DESIGN.md`. Four
live sites still name `aca9397`:

```
docs/reviews/check-design-citation-shape.py:144:    parser.add_argument("--sha", default="aca9397", ...)
docs/reviews/check-design-citations.py:43:`aca9397`, where ADR-0025's Q2 and Q3 re-froze it.
docs/reviews/check-design-citations.py:48:    python3 docs/reviews/check-design-citations.py --since aca9397
docs/briefs/AUDIT-SHAPES.md:12:1. `docs/DESIGN.md` §7 (the audit trail) - frozen at `aca9397`. It is the authority.
```

The fourth is the sharp one. `AUDIT-SHAPES.md` was **added by `3e0c8ae`, the tip of this very
range** - the brief for task #104. It dispatches an agent to treat `aca9397:docs/DESIGN.md` as "the
authority" when that object is no longer what is in the tree.

**It is benign today and I want to be precise about that.** The edit replaced one line in place;
`git show aca9397:docs/DESIGN.md | wc -l` and `HEAD` both give **2133**, so no citation moved and
both citation checkers still exit 0. The C2-T2 row is in §11, not §7, so #104's agent is not
actually misled about its subject. The defect is that **none of that was checked by an instrument**
- it is true by luck of where the edit fell, and the next in-place design edit gets the same silent
pass with no such luck.

`docs/worklogs/ADR-0025-REPORT.md:16` already records the right method - it pins the freeze by
**blob hash**, `e009ac41...`, and that recorded hash is now stale. The method existed and was run
once by hand; it is not wired.

**Suggested fix.** Both halves.

1. Re-freeze and repoint. The design as it now stands is `5d17cd7:docs/DESIGN.md` (blob
   `639f4b72...`, verified by `git rev-parse`). Update the four sites above to that SHA, and update
   the blob line in `ADR-0025-REPORT.md` rather than appending a correction beside it.
2. Wire the equality as a gate, so the pointer cannot go stale silently again. Add to `ci.yml`:

   ```bash
   FROZEN=$(grep -oE 'default="[0-9a-f]{7,40}"' docs/reviews/check-design-citation-shape.py | head -1 | tr -d 'default="')
   a=$(git rev-parse "$FROZEN:docs/DESIGN.md"); b=$(git rev-parse HEAD:docs/DESIGN.md)
   if [ "$a" != "$b" ]; then
     echo "::error::docs/DESIGN.md ($b) has drifted from its declared freeze $FROZEN ($a)."
     echo "         Re-freeze and repoint, or the ADR that authorises the edit must say so."
     exit 1
   fi
   ```

   Deriving `FROZEN` from the checker rather than retyping it keeps the value in one place, which is
   the discipline `PREAMBLE.md` asks for with both floors.

---

## R10-M2 - #115's `--controls` license the POPULATION and nothing else; the detector they exist to protect can be deleted with all controls still green

The zero is **real**. I proved the scan can fire, on the real tree, by planting a tracked file:

```
blank range     scripts/r9-plant.sh:2  DESIGN.md:2       -> "the entire range is blank"       exit 1
past the end    scripts/r9-plant.sh:2  DESIGN.md:99999   -> "past the end of DESIGN.md"       exit 1
blank START     scripts/r9-plant.sh:2  DESIGN.md:2-4     -> "starts on a BLANK line"          exit 1
```

(The third needed a range whose first line is blank and whose body is prose; `DESIGN.md:2-4` is one.
My first attempt at this was a false negative worth recording: an **untracked** plant is invisible,
because `code_files()` enumerates `git ls-files`. The count stayed at exactly 875/148 and I nearly
read that as "the detector is dead".)

So 875 citations / 148 files / 0 findings is honest, and the file's closing claim - that resolving
and being correct are different things - is an honest statement of what it cannot do.

**The controls are the weak part.** Amputating each branch in turn:

| amputation | `--controls` | scan exit |
|---|---|---|
| re-narrow population to a directory list (`not name.startswith("docs/")`) | **1/2, exit 1** | 108 files, 871 citations |
| admit `.md` into `CODE_SUFFIXES` | **1/2, exit 1** | 336 files, 1801 citations |
| **delete the blank-start detector** (`elif not body[0].strip()` -> `elif False`) | **2/2, exit 0** | 148 files, 875 citations, **identical output** |

Every mutation was proved to land and proved restored against `git diff --quiet`.

The third row is the finding. The blank-start branch is **the specific defect this file was written
to find** - the R4 off-by-one its own docstring narrates - and deleting it outright changes not one
character of the file's output. Both controls still print FIRED. A future refactor that drops that
branch ships a permanent, self-confident zero.

**Suggested fix.** Extend `controls()` with a positive control per detector, using the frozen design
in memory rather than the tree, so it costs nothing and touches no files:

```python
def detector_controls(lines: list[str]) -> tuple[int, int]:
    """Each detector must FIRE on a citation built to trip it."""
    blank = next(i for i, t in enumerate(lines, 1) if not t.strip())
    start = next(i for i, t in enumerate(lines, 1)
                 if not t.strip() and lines[i].strip()
                 and not lines[i].strip().startswith(STRUCTURAL))
    cases = [
        ("past the end",    f"DESIGN.md:{len(lines) + 1000}"),
        ("entirely blank",  f"DESIGN.md:{blank}"),
        ("starts blank",    f"DESIGN.md:{start}-{start + 2}"),
    ]
    fired = 0
    for label, cite in cases:
        if classify(cite, lines) is not None:   # see note
            fired += 1
            print(f"  DETECTOR {label} -> FIRED")
        else:
            print(f"  DETECTOR {label} -> DID NOT FIRE; the branch is dead")
    return fired, len(cases)
```

This needs the classification lifted out of `main`'s loop into a `classify(cite, lines) -> str | None`
helper - a small refactor that is worth doing anyway, because today the detectors are unreachable
except by scanning the whole tree, which is exactly why they cannot be tested.

---

## R10-L1 - `REPOINT-EXEMPT` silences a genuine finding on the same line, and the scan never says how many lines it skipped

Measured. A tracked plant reading

```
# see DESIGN.md:99999 for the rule  REPOINT-EXEMPT
```

makes the scan exit **0**. Without the marker the same line exits 1 with "past the end of
DESIGN.md". The skip is line-granular by design and the comment says so, but the consequence is
that any line can opt out of the checker with a comment, and the output gives a reader no way to
see that it happened. There are 20 such lines today across 6 files.

This is the shape recorded in the standing lesson about hand-kept lists beside their container: the
exemption set is invisible in the very report that depends on it.

**Suggested fix.** Count and print, so a growing exemption set is visible rather than silent. In
the scan loop, replace the bare `continue`:

```python
if EXEMPT in text:
    exempted += 1
    continue
```

and print it beside the population line, where a reader already looks:

```python
print(f"DESIGN.md citations in {len(paths)} tracked .py/.sh files: {seen}")
print(f"{exempted} line(s) skipped as {EXEMPT}.")
```

Worth considering as a follow-up rather than in this fix: narrow the marker so it exempts a line
from **repointing** without exempting it from **bounds checking**. A citation that records where a
defect was should still not be allowed to point past the end of the file.

---

## R10-L2 - a timed-out row in `check-suite-floor-amputation.sh` prints its warning and then reports SURVIVED anyway

`scripts/check-suite-floor-amputation.sh:58-75`. The timeout arm added in this range is correct
about detecting 124:

```bash
out=$(cd "$REPO" && timeout 300 uv run --frozen pytest "$TESTS" -q 2>&1 | tail -1)
local row_rc=$?
if [ "$row_rc" -eq 124 ]; then
  echo "  TIMED OUT after 300s - this row NEVER FINISHED. Not a kill and"
  echo "  not a survivor: the verdict below is not a measurement of it."
fi
```

but it does not `return`. Control falls into the verdict, `$out` does not contain `failed`, and the
row prints `SURVIVED $name` and is counted as one. The comment is candid that the verdict below is
meaningless - it just does not stop it being emitted.

**CI does catch this**, and I checked rather than assuming: `scripts/ci-harness-gate.sh` greps the
captured output for `TIMED OUT` and sets `fail=1`, and separately fails on any non-zero harness exit.
So the exposure is a developer running the harness standalone, who sees a SURVIVED line and a tally
that includes it.

**Suggested fix.** Make the row refuse to produce a verdict it has just disclaimed:

```bash
if [ "$row_rc" -eq 124 ]; then
  echo "  TIMED OUT after 300s - this row NEVER FINISHED. Not a kill and"
  echo "  not a survivor: no verdict is emitted for it."
  return 1
fi
```

`return 1` rather than `return 0`, so the harness's own exit code carries the fact that a row was
not measured, instead of relying solely on the gate's grep.

---

## R10-N1 - `_code_lines` strips comments by splitting on the first `#`, which also truncates a `#` inside a string

`docs/reviews/check-settings-are-read.py:99` (`return [line.split("#", 1)[0] for line in body]`).

The intent - a comment mentioning a name is not a read - is right, and I confirmed it works (see
R10-V4). But the implementation truncates any line at its first `#` regardless of context, so a
genuine read positioned after a `#` inside a string literal becomes invisible and the field reports
as UNREAD. No such line exists in `src/` today; I checked. This is a latent false positive, not a
current one.

**Suggested fix.** Strip comments with the tokenizer, which knows what a string is:

```python
def _code_lines(path: pathlib.Path) -> list[str]:
    body = path.read_text(encoding="utf-8").splitlines()
    out = list(body)
    with path.open("rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type == tokenize.COMMENT:
                row = tok.start[0] - 1
                out[row] = out[row][: tok.start[1]]
    return out
```

Keep the existing docstring verbatim - it records why the rule exists and that history is the
valuable part.

---

## R10-N2 - `timeout` without `--kill-after`: the bound holds only for a child that honours SIGTERM

All 64 bounded sites use plain `timeout N`. `timeout` sends SIGTERM and then waits indefinitely; a
child that blocks or ignores it makes the bound advisory. Since the command is `uv run ... pytest`,
the signal has to traverse `uv` to reach the interpreter.

**I measured it before raising it, and today it works:**

```
timeout 8 uv run --frozen pytest -q   ->  rc=124, elapsed=8s
pytest processes before: 5    2s after: 5    -> no orphan
```

So this is prophylactic, not a live defect - which is why it is a nit and not a finding.

**Suggested fix.** `timeout -k 30 900 uv run ...` at the bounded sites, so a wedged child gets
SIGKILL 30s after the SIGTERM it ignored. Worth folding into the same pass as R10-H1 so all
invocations end up in one shape. Task #116 already tracks the related problem that these abort
messages retype the number one line above them; a single pass that introduces `-k` **and** derives
the message's number from one variable would close both.

---

## R10-N3 - the dispatching brief describes the row arm as 300s; the amputation harnesses use 900s

The brief for this round summarises #108's three arms as "baseline 900s -> exit 4, row 300s,
selector probe 120s". Measured against the tree, the row arm is **not** uniformly 300s: the
amputation harnesses run their rows at 900s.

```
$ grep -nE 'timeout [0-9]+ .*pytest' scripts/*amputation*.sh | grep -oE 'timeout [0-9]+' | sort | uniq -c
      4 timeout 300
     26 timeout 900
```

The code is internally self-consistent - every abort message names the same number as the `timeout`
above it - so this is a defect in the summary, not in the harnesses. It is recorded because a
summary is what the next agent reads, and "row 300s" is the kind of retyped constant `PREAMBLE.md`
exists to warn about.

**Suggested fix.** State the arms by role rather than by value in future briefs - "baseline, row,
selector probe, each bounded, values in the harness" - so the brief cannot go stale against the
tree. Task #116 already tracks making those values derivable rather than retyped, which would let a
brief cite one name instead of three numbers.

---

# What I set out to falsify and could not - the author's six challenges

These are recorded because "I attacked this and it held" is a result.

**R10-V1. The `set -e` reasoning is sound, and the population is larger than claimed.** The
author verified 22 scripts. I enumerated the container instead: **43 tracked `.sh` files**, and
every one carries `set -uo pipefail` with no `-e`.

```
$ for f in $(git ls-files '*.sh'); do printf '%-50s %s\n' "$f" "$(grep -n '^set ' "$f")"; done
  (43 rows, every one `set -uo pipefail`)
$ grep -rn 'set -[a-z]*e' $(git ls-files '*.sh') | grep -v 'set -uo pipefail'
  (3 hits, all inside probe-set-e-vs-harness.sh - prose and echo strings, no live `set -e`)
```

No script sources another; CI invokes them as `bash scripts/...`, a fresh shell, and `errexit` is
not inherited across `bash` invocations. This matches ADR-0023, whose Ruling re-measured the same
invariant at zero.

**Is anything fragile beyond a comment?** Yes, and it is worth saying plainly: **nothing enforces
it.** ADR-0023 asks that every one of these scripts say so at the `set` line, and the ADR's
correctness depends on `-e` never combining with `rc=$?`. That invariant has been measured by hand
three times now (at `2d20ed6`, at `5eb64b0`, and here) and is checked by no gate. A one-line guard
would retire the hand-measurement:

```bash
grep -ln '^set -e' $(git ls-files '*.sh') | grep . && { echo "::error::a harness gained -e; see ADR-0023"; exit 1; } || true
```

I am not raising that as a finding because it is ADR-0023's stated business rather than this range's,
but it is the answer to the question asked.

**R10-V2. `local row_rc=$?` is correct, and the famous masking form is a different shape.**
Measured on bash 5.2.21:

```
ARM1 bare-cmd then 'local rc=$?'          rc=7     (correct)
ARM2 out=$(cmd) then 'local rc=$?'        rc=7     (correct)
ARM3 'local out=$(cmd)' KNOWN-BAD form    rc=0     (masked - the trap, correctly avoided)
ARM4 timeout FIRED, bare + local          rc=124
```

`$?` is expanded during word-splitting, before `local` runs. The masking bug requires the command
substitution to be *inside* the `local` declaration, which no site in this range does. The author's
reasoning was right for the right reason.

**R10-V3. `pipefail` does propagate 124 through `tail`.** Measured, with a negative control so
the positive result means something:

```
ARM5 out=$(timeout 1 ... | tail -1)  WITH pipefail   rc=124
ARM6 same, pipefail OFF                              rc=0     (the bug pipefail prevents)
ARM7 out=$(cd ... && timeout 1 ... | tail -1)        rc=124   (the real site's exact shape)
```

The real site is `check-suite-floor-amputation.sh:58`. Its 124 detection works. See R10-L2 for what
it does *after* detecting.

**R10-V4. The #113 exemption fires, and the prose is actionable rather than merely nicer.**
Both arms, by planting into `src/` and restoring against `git diff --quiet`:

```
ARM A  baseline, no reader                        exit 0
ARM B  a real reader planted in config.py         exit 1
       "STALE EXEMPTION  outbound_rate_limit is read now; drop its EXEMPT entry"
       "0 unread field(s), 1 stale exemption(s)."
ARM C  the name planted in a COMMENT only         exit 0   <- negative control
```

ARM C matters: it proves the comment-stripping in `_code_lines` is load-bearing, and that the arm
keys on a *read* rather than on the string appearing.

On "did I just write nicer prose" - no. I checked the new reason against the frozen design rather
than against itself. `aca9397:docs/DESIGN.md:448-465` really does say the throttle is not
implemented, really does say **"The throttle is PER-PROCESS"** (`:454`), and really does say
**"Time spent waiting on the throttle SPENDS §4.3's outbound budget"** (`:459`). The exemption's
three claims are each true at the cited section, and it tells the implementer what to do and when to
delete the entry. It also cites **§4.4 by section rather than by line**, which survives the drift
that R10-M1 describes. That is a better citation than the one it replaced.

**R10-V5. #115's zero is real** - see R10-M2 for the three positive controls that fire and the
one amputation that does not.

**R10-V6. The 64 are all genuinely bounded**, with `timeout N` governing the command and not
merely present on the line. The defect is the denominator, not the 64. See R10-H1.

---

# What I could NOT settle

Short, and every item here is something I tried and failed to resolve, not something I skipped.

1. **I did not run the 13 harnesses.** Each is minutes and several mutate `src/`; two other agents
   are live in adjacent worktrees and the standing rule is not to gate a tree someone is on. So
   R10-H1's nine sites are proved **unbounded by reading and by `grep` over the whole container**,
   and proved **reachable from `ci.yml` by line**, but I have not watched one of them hang. The
   claim "these can hang unbounded" is structural, not observed.

2. **Whether the C2-T2 edit is inside ADR-0032's scope is a judgement I cannot make from the
   documents.** ADR-0032 rules the row into existence but says nothing about the disposition
   column's closed vocabulary, which is precisely the incompleteness `86ab20e` describes. Whether
   completing your own ruling counts as "a numbered ADR changing the design" for `PREAMBLE.md`'s
   purposes is your call, not mine. **R10-M1 does not depend on it either way** - the freeze
   pointer is stale whichever way that goes.

3. **I did not audit the other nine `rc=$?` sites ADR-0023 lists as un-audited.** ADR-0023 says
   explicitly that three of twelve were read in full and nine were not. That is still true; this
   review did not change it, and the sites in *this* range are not among the nine.

---

## Housekeeping

Every mutation in this review was proved to land (`cmp` against a backup, never `grep -F`) and
proved restored (`git diff --quiet` against the index). The worktree is clean at submission:
`git status --porcelain` is empty apart from this report. All probes were run from `/tmp` and the
one tracked plant (`scripts/r9-plant.sh`) was removed from both the tree and the index.
