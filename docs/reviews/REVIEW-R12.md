# CODE-REVIEW-R12 - the machinery, `f699f74..dad014e`

<!-- REVIEW-COVERS: f699f74..dad014e -->

**THE DECLARATION ABOVE IS PATH-FILTERED AND DOES NOT MEAN THE WHOLE RANGE WAS READ.** This round
was responsible for `f699f74..dad014e` and examined 62 of its 133 files - `docs/reviews`, `scripts`
and `.github` only. `src/`, `tests/`, `docs/adr/` and `docs/DESIGN.md` across the same span were
`review-r11`'s, and this document is not evidence about them. `check-review-coverage.py` records
coverage per COMMIT, so it will read this line as covering all 45; that is the declaration the
orchestrator asked for, and this paragraph is the qualification that goes with it. See the note at
the end of this file - a path-filtered round declaring a whole span is the same manufactured-coverage
shape the checker exists to prevent, arriving from the author's side instead of the inferrer's.

**Scope:** `git diff f699f74..dad014e -- docs/reviews scripts .github` - 62 files, +4289/-1405.
`src/`, `tests/`, the ADRs and `docs/DESIGN.md` belong to `review-r11`; anything I found there is
noted for the orchestrator rather than chased.

**Where I worked:** `/home/plafayette/claude_projects/fmj-worktrees/r12-gates`, detached at
`dad014e`, branch `review/r12`. No other checkout was touched.

**Read first, in the brief's order:** `docs/briefs/PREAMBLE.md`; `docs/DESIGN.md` via
`git show aca9397:docs/DESIGN.md` (2133 lines, headings enumerated, §4.3/§4.5/§8/§10 read in full);
`docs/adr/README.md` and the ADR index; ADR-0023 and ADR-0010 in full, the rest by heading and
Decision.

**Floors derived from `ci.yml`, never retyped:**

```
grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1   -> 868
uv run --frozen pytest    -> 868 passed, 6 deselected in 56.86s, 0 skipped
printf '%s\n' "$out" | bash scripts/check-suite-floor.sh 868  -> "suite floor OK: 868 passed, floor 868"

grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' ...          -> 458
python3 scripts/check-harness-anchors.py --self-check --floor 458
  -> "OK: all 458 anchors resolve to exactly one hit in their target file (floor 458)."  exit 0
```

Both floors are TIGHT (868 == 868, 458 == 458). `grep -cE ' SKIPPED'` over the run: **0**.

---

## Disposition - all eight accepted and fixed on `review/r12`

Fixed in the orchestrator's stated order. Every fix was measured both ways before it was committed;
the evidence is in each commit message and repeated under each finding below.

| Finding | Fix | Commit |
|---|---|---|
| H1 | re-anchored on unreflowable lines, `assert` -> recorded PROBLEM, and WIRED | `ee4c816` |
| H2 | a third claim comparing every `--min-rows` to a live count; u14 10->16, u7 19->22 from runs | `874dedc` |
| M1 | `check-u15-gate-amputation.sh` added as a row, plus a container assertion in both directions | `368c545` |
| M2 | `files = [..., "scripts"]`, proved with a two-arm control on two separate files | `1fa7b5e` |
| L1 | the "never watched" prose rewritten in place; ci.yml's dangling `#102` repointed | `ca84093` |
| L2 | the count deleted rather than corrected | `ee84ab7` |
| N1 | the symmetric check added - **and it found 46, not the 2 I filed** | `ee84ab7` |
| M3 | no code fix: `0fb4cd6` closed it, out of range. Recorded, not actioned | - |

**Two things I got wrong, corrected in place above rather than appended to.** N1's size (2 filed, 46
measured) and the wired/unwired inventory in H1 (three files mislabelled by a grep that counted
comments). Both are the same failure this report is about, committed by the report.

**Not done, and needing its own task:** the 46 ranges N1 now names. They span `src/`, `tests/` and
`scripts/`, where three other agents are working.

---

## Findings

### R12-H1 (High) - `probe-docs-lint-amputation.py` has been DEAD since `449968f`, and nothing noticed

The whole amputation harness for the docs-lint branch aborts on its first row:

```
$ uv run --frozen python docs/reviews/probe-docs-lint-amputation.py ; echo EXIT=$?
  File ".../docs/reviews/probe-docs-lint-amputation.py", line 77, in amputate
    assert count == 1, f"{name}: anchor appears {count} times, not once"
AssertionError: A1 fail-open REPOINT-EXEMPT read restored: anchor appears 0 times, not once
EXIT=1
```

**Cause, measured rather than reasoned about.** The A1 anchor
(`docs/reviews/probe-docs-lint-amputation.py:99-108`) quotes the fail-closed `REPOINT-EXEMPT` read
verbatim, including this two-line f-string:

```python
                f"  UNREADABLE: {m['file']}:{m['lineno']}: "
                f"{type(exc).__name__}: {exc}"
```

`449968f` reflowed it onto one line. At `docs/reviews/repoint-design-citations.py:120` it is now:

```python
                f"  UNREADABLE: {m['file']}:{m['lineno']}: {type(exc).__name__}: {exc}"
```

Counting the anchor against each revision's blob:

| revision | A1 anchor occurrences in `repoint-design-citations.py` |
|---|---|
| `d5340b7` (the docs-lint sweep) | 1 |
| `449968f` (R9's fixes) | 0 |
| `dad014e` (HEAD) | 0 |

**Consequence.** This probe is the only amputation evidence for four behaviour fixes - the
fail-closed `REPOINT-EXEMPT` read, the upstream checker's stderr health check, and the two narrowed
`except` clauses in `check-standards-citations.py` and `probe-r6-breaker-reset.py`. Because
`assert` raises, rows **A2, A3, A4 and the A5 negative control never run either**, and neither does
the closing tree-clean re-check. The two probes it drives still pass on their own
(`probe-repoint-fail-closed.py` exit 0, all 7 rows; `probe-gate-swallowed-exceptions.py` exit 0,
7/7 under `uv run --frozen python`) - but nothing has shown them able to FAIL since `449968f`.

It went unnoticed because the probe is **unwired**: `grep -n 'probe-docs-lint-amputation'
.github/workflows/ci.yml` returns nothing. Of the 39 `.py` files under `docs/reviews/` and
`scripts/`, **19 are unwired** and only `classify-w505.py` and the two `adr-batch-*.py` declare
themselves one-shots - so this one sat in exactly the "cannot tell deliberately-unwired from
overlooked" state `classify-w505.py`'s own docstring says is the reason it declares itself.

**A CORRECTION TO MY OWN METHOD HERE.** I first derived that inventory by grepping each basename
against the whole of `ci.yml`, which counts a name appearing in a COMMENT as wired. Three files were
mislabelled that way - `check-design-citation-shape.py`, `check-clause-citations.py` and
`check-env-vars-are-declared.py` are all unwired, each named only in prose. Re-derived by parsing
every job's `run:` blocks out of the YAML and searching those: **20 wired** (including this probe
now), 19 not. An instrument's output stated as the object's property, which is the failure this
report spends most of its length on.

I checked every other probe in the tree at HEAD, so this is one file and not a class:
`probe-r4-h3-live-arm-cannot-detect`, `probe-r6-arm1c-tautology`, `probe-r6-breaker-reset`,
`probe-r6-post-escape`, `probe-r6-wait-burns-budget`, `probe-u12-f2-embedder-leak`,
`probe-breaker-call-path`, `probe-exception-redaction`, `probe-scan-bounds` - **all exit 0**.

**Suggested fix, three parts:**

1. Re-anchor A1 on the current single-line form. Better still, shorten the anchor to the part that
   carries the SEMANTICS and cannot be reflowed away - the `as exc:` capture plus the `continue`
   that follows the append - and keep the existing uniqueness assert.
2. **Wire it.** A step next to the other checker steps (it needs `uv run --frozen python` for row
   A4's httpx2 import) turns the next reflow into a red run instead of a silent one.
3. Make `amputate()` append the anchor failure to `PROBLEMS` and `return`, instead of `assert`.
   One stale anchor currently hides the other four rows, which is the shape that let this sit.

---

### R12-H2 (High) - the exactness check does not read the floor layer where the slack actually is

`check-row-floor-exactness.py` exists because a merge produced a floor of 26 against 31 rows. It
makes two claims and prints both populations:

```
Harnesses checked for exactness: 23
Harnesses carrying BOTH floors, checked for agreement: 8
Every floor equals its harness's live row count. OK.   (exit 0)
```

**Neither claim reaches an external-only floor.** `ci.yml` carries 16 `--min-rows` flags; 8 of those
harnesses have no internal `ROW_FLOOR`, so the agreement claim skips them, and the exactness claim
only reads the control table (all internal). `--min-rows` is a LOWER bound -
`scripts/ci-harness-gate.sh:299`: `if [ "$rows" -lt "$min_rows" ]` - so nothing anywhere compares
those 8 numbers to a live row count. **Two of them are slack today.**

`amputate()` prints `########## $label` unconditionally as its first act
(`check-u14-arguments-amputation.sh:79`, `check-u7-resilience-amputation.sh:95`), and every call
site is at column 0, so a source count of `^amputate "` is the row count the `--row-re` will see:

| harness | rows in source | `--min-rows` in `ci.yml` | slack |
|---|---|---|---|
| `check-u14-arguments-amputation.sh` | **16** (A1..A16) | 10 (`ci.yml:933`) | **6 rows** |
| `check-u7-resilience-amputation.sh` | **22** (A1..A22) | 19 (`ci.yml:840`) | **3 rows** |
| `check-u1-boot-amputation.sh` | 14 (A..N) | 14 (`ci.yml:1059`) | tight |
| `check-u10-write-amputation.sh` | 10 | 10 | tight |
| `check-u12-jobfeed-amputation.sh` | 10 | 10 | tight |
| `check-u3-audit-amputation.sh` | 10 | 10 | tight |
| `check-u4-client-amputation.sh` | 17 | 17 | tight |
| `check-u9-http-amputation.sh` | 14 | 14 | tight |

Both grew after their step was wired, which is the merge-produced-slack direction again:
`git show 8e5da82:scripts/check-u14-arguments-amputation.sh | grep -c '^amputate "'` is **10** and
HEAD is **16** (A11-A16 arrived at `481c682`); u7's amputation was **19** at `8e5da82` and is **22**
now. So six rows can be deleted from U14's amputation harness and three from U7's with CI green -
the same defect `check-row-floor-exactness.py` was written for, one floor layer over.

This predates `f699f74`, so it is not introduced by this diff. It is reportable here because this
diff is where the instrument that should have caught it landed, and where `0c25ae3` claimed "all 14
floors watched fire, all tight".

**Suggested fix:** add a THIRD claim to `check-row-floor-exactness.py`. `_external_floors()` already
folds continuations and joins harness name to `--min-rows`; extend the same regex to capture
`--row-re` too, count the harness SOURCE's row-emitting call sites (the ERE column of
`check-row-floor-controls.sh` already gives the shape for the harnesses it names; for the rest,
`grep -cE '^(amputate|report|mutate|control|run_control|run_mutation) "'` is the same derivation the
table uses), and require `N == count` rather than `<=`. Raise `--min-rows 10 -> 16` for U14 and
`19 -> 22` for U7 in the same commit, derived from a run rather than by arithmetic on the old
number. A one-line interim that costs nothing: raise the two numbers now, so the checker's future
version lands on an already-tight tree.

---

### R12-M1 (Medium) - the exactness table is a hand-kept list and its container has one member it does not

```
$ grep -lE '^[[:space:]]*ROW_FLOOR=[0-9]+[[:space:]]*$' scripts/*.sh | wc -l
24
$ bash docs/reviews/check-row-floor-controls.sh --list | wc -l
23
$ comm -23 <container> <table>
check-u15-gate-amputation.sh
```

`scripts/check-u15-gate-amputation.sh:48` carries `ROW_FLOOR=5` and is not in the TABLE, so its
floor is never compared to its live row count. It is **tight today** - 5 `^report "` call sites, and
`report()` increments `ROWS` at `:52` - so this is latent rather than live, and its FIRING claim IS
covered, by the singular `docs/reviews/check-row-floor-control.sh` which targets exactly this
harness. Only the static exactness claim misses it.

The file's own docstring says *"THE TABLE IS NOT COPIED HERE"* to avoid a second copy of a number.
That is right, and it does not help here: the table is still a hand-kept LIST beside a container it
never compares itself to, which is the same shape one level up.

**Suggested fix:** two lines.

1. Add to `check-row-floor-controls.sh`'s `TABLE`:
   `check-u15-gate-amputation.sh|^report "|0|1|cmd` (verified: 5 rows, `exit 1` on a floor breach at
   `:199`, mode `cmd` - no row in range carries a command substitution).
2. Add a container assertion to `check-row-floor-exactness.py`: glob `scripts/*.sh` for
   `^\s*ROW_FLOOR=\d+\s*$`, and fail if that set is not EQUAL to the table's set. Then the next
   harness cannot be added without being covered, and this finding cannot recur.

---

### R12-M2 (Medium) - `scripts/*.py` is outside the type gate, including four wired CI checkers

The docs-lint change set `files = ["src", "tests", "docs/reviews"]` in `[tool.mypy]`, replacing
`files = ["src", "tests"]` + `exclude = ["^docs/"]`. `scripts/` was in neither and is in neither
now. Positive control, both arms, same edit:

```
appended to docs/reviews/check-adr-numbers.py:
    def _r12_probe(a: int) -> str: return a
  -> uv run --frozen mypy  EXIT=1
     docs/reviews/check-adr-numbers.py:172: error: Incompatible return value type
     (got "int", expected "str")  [return-value]

appended to scripts/check-committed-file-types.py (identical text):
  -> uv run --frozen mypy  EXIT=0
     Success: no issues found in 96 source files
```

Both files were restored and `git diff --quiet` confirmed byte-identity with the commit.

Nine `.py` files live under `scripts/`, four of them wired CI gates:
`check-harness-anchors.py` (the anchor floor, 458), `check_advisories.py` (the dependency-audit flag
source), `check-committed-file-types.py`, plus four probes and the two `adr-batch-*.py` one-shots.
Ruff DOES cover them - `extend-exclude` is now only `["**/*.md"]`, and `ruff check .` /
`ruff format --check .` both exit 0 over 105 files - so this is the TYPE half only, and it is not a
regression introduced by this diff. It is reportable because the commit's stated purpose was
"so ruff could finally read the wired checkers", and half the wired checkers were not brought in.

**Suggested fix:** `files = ["src", "tests", "docs/reviews", "scripts"]`, then run
`uv run --frozen mypy` and close what it reports in the same commit. Expect real work - these files
were written without annotations under `strict = true`.

---

### R12-M3 (Medium) - two wired gates were RED for the entire 45-commit hole

`ci.yml:172` runs `python3 docs/reviews/check-coupling.py docs/DESIGN.md` bare, so its exit code IS
the step. At `dad014e` it exits **1**:

```
docs/DESIGN.md: 61 STRIDE rows, 17 Critical/High (16 mitigated by the roster's reckoning, 1 not);
all 61 rows checked for disposition, 24 naming a §8 case.
FAIL: 1 problem(s)
  - C2-T2 names §8 case '`test_no_input_model_produces_a_ref_for_the_middleware_to_inline` - the
    tripwire is on the model side, and fires when a model starts nesting', which does not appear in §8
```

Running the CURRENT checker against each revision's `DESIGN.md` blob:

| revision | exit |
|---|---|
| `f699f74` (R9's review point, 60 rows) | 0 |
| `8a9d63c` (ADR-0032 applied, C2-T2 added) | **1** |
| `b079ae5`, `70ae269`, `aca9397`, `dad014e` | **1** |
| `0fb4cd6` (2026-09-01, task #113) | 0 |

`git merge-base --is-ancestor 0fb4cd6 dad014e` says **NOT ancestor** - the fix is on main AFTER the
reviewed HEAD. `check-coupling-sweep.py` was red for the same window too, and for the right reason:
*"ABORT: the unmutated document is already red. Fix that before sweeping - every mutation below would
be reported as caught."* That is a correct fail-closed and I am not filing it as a defect.

**What is reportable is the consequence, not the row.** For the whole review hole, two required
steps could not pass, so **no CI run over that range can have been green**, and any "CI is green"
claim against a commit in it is false. The 45 commits landed on a red trunk.

I also confirmed the fix is real and the sweep behind it is not vacuous. Against `0fb4cd6`'s
`DESIGN.md`:

```
$ python3 docs/reviews/check-coupling-sweep.py /tmp/r12-design-fixed.md ; echo EXIT=$?
  6 escapes are the designed Medium/Low exemption:  C3-T1, C3-D1, C3-E1, C4-I1, C4-E2, C9-D1
  0 escapes are holes. Every one of the 23 rows that names a §8 case loses its green when
  that reference is removed.
EXIT=0
```

**Suggested fix:** no code change - `0fb4cd6` closes it. What is missing is the rule: a merge whose
resulting HEAD leaves a wired gate red is not merged, and the two steps get one confirming run over
the range now that it is fixed. `DESIGN.md` is `review-r11`'s, so the §8-membership question itself
goes to them.

---

### R12-L1 (Low) - a positive control understates its own coverage and points at a closed task

`docs/reviews/check-row-floor-controls.sh:58-64` still reads:

> The exactness claim now covers all 23 rows below. The firing claim covers only the first NINE
> [...] **The fourteen added afterwards have been checked but never watched.** [...] Task #102 is
> the remainder.

Task #102 completed at `0c25ae3`, *"FLOOR-FIRING: all fourteen remaining floors watched fire"*, and
`0c25ae3` IS an ancestor of `dad014e`. But `git diff 0c25ae3^ 0c25ae3 --stat` is **one file**,
`docs/worklogs/FLOOR-FIRING-REPORT.md` - the control's prose was never updated. A reader is told the
evidence is weaker than it is, and sent to a task that is closed.

**Suggested fix:** rewrite those lines in place (not a rider underneath them): the firing claim now
covers all 23, evidenced by `docs/worklogs/FLOOR-FIRING-REPORT.md`, and the remainder sentence
points at #107 (the canonical machine line) rather than #102.

---

### R12-L2 (Low) - a hand-typed population count beside a container that has doubled

`.pre-commit-config.yaml` (just outside the diff, same family) says the shellcheck hook's population
is *"the 22 tracked `.sh` files"*. At `dad014e`, `git ls-files '*.sh' | wc -l` is **43**.

The hook itself is sound. Verified with the real binary rather than assumed:

```
$ ~/.local/bin/shellcheck --version   -> version: 0.10.0
$ git ls-files '*.sh' | xargs ~/.local/bin/shellcheck --severity=warning ; echo EXIT=$?
EXIT=0
```

**Suggested fix:** delete the number. The sentence - "pre-commit's own identify pass over shebang
and extension, so the population is the tracked `.sh` files, which includes the probes under
`docs/reviews/` and excludes `ci.yml`" - makes its point without a constant that decays.

---

### R12-N1 (nit as filed, MEDIUM as measured) - 46 citation ranges end one line past their subject

**FIXED, and my own filing was the illustration.** I raised this off the TWO instances I had
happened to read: `scripts/check-u7-resilience-controls.sh` cites `DESIGN.md:373-383` for the 429
clause and `DESIGN.md:674-680` for correlated logging, and lines 383 and 680 are both blank (the
429 clause ends at 375, ADR-0030's paragraph at 382, the logging paragraph at 679).
`check-design-citation-shape.py` rejects a range that STARTS on a blank line and had no mirror for
one that ENDS on one, so both passed.

**Adding the mirror found 46, not 2.** That is this checker's own opening lesson - a partial check
selects for the form it cannot see - arriving at the reviewer writing the check for it. A finding
raised from a partial read is a partial check. The severity above is corrected rather than left as
filed.

**Fixed at `ee84ab7`:** the symmetric condition is in, as a plain finding rather than an opt-in
flag, because `check-design-citation-shape.py` is NOT wired - so a red run is a backlog to work,
which is exactly what its own closing paragraph asks for. Run: 871 citations, **46 "ends on a BLANK
line (one line too long)"**, exit 1.

**The 46 are NOT swept, deliberately.** They span `src/` and `tests/`, which are `review-r11`'s, and
`scripts/`, where `canonical-line` and `review-r9` are both working; a sweep from this branch would
collide with all three. It needs its own task.

Every other repointed range I read resolved to its stated subject exactly (`366-367` the 4xx/breaker
clause, `392-394` the outbound budget, `359-361` retries-live-inside-this-module, `365` "one call,
four rows created", `370` the `retry_after` hint).

---

## Verified sound - things I attacked and could not break

Recorded so the next reviewer does not repeat them, and so the greens above are attributable.

- **The zero-skips guard now fires.** The here-string is on the grep at `ci.yml:568`. Both arms:
  `"1 passed, 3 skipped in 0.1s"` -> GUARD FIRES; `"868 passed in 90s"` -> quiet. The `fa0c6c1`
  defect is genuinely closed.
- **`set +e` before every `out=$(cmd); rc=$?` block.** 16 blocks in `ci.yml` now carry it. This is
  the correct fix for `3ee39e5`: `set -uo pipefail` does not clear the `bash -e {0}` GitHub imposes,
  and the assignment is the failing command. ADR-0023 covers these blocks by PURPOSE, and its
  re-measurement (0 blocks combining `-e` with `rc=$?`) still holds.
- **Concurrency does what the comment says, not what the comment claims.** `group:
  ci-${{ github.event_name }}-${{ github.ref }}`, `cancel-in-progress: ${{ github.ref !=
  'refs/heads/main' }}`. A push to main gives `refs/heads/main` -> `false`, so main's RUNNING run
  survives; a `pull_request` gives `refs/pull/N/merge` -> `true`; a tag gives `refs/tags/...` ->
  `true`. `aa3498c`'s correction is accurate: this does not guarantee a run per commit, because
  GitHub keeps at most one PENDING run per group regardless of the setting. Comment and expression
  agree.
- **The standards gate's exit-2 arm is precise.** `check-standards-citations.py` returns 2 from
  exactly one place (`:139`, corpus absent), 1 from `:176` (zero citations parsed - the
  broken-selector guard) and `:191` (real findings), 0 from `:196`. So `ci.yml`'s
  `if [ "$rc" -eq 2 ] -> ::warning:: + exit 0` cannot mask a real finding as an absent corpus. The
  green-and-inert state is announced loudly, which is the `switched-off != broken` lesson applied
  correctly.
- **The docs-lint sweep's zero is honest, both tools.** Positive controls above: ruff fires on a
  `docs/reviews` file (E401), mypy fires on a `docs/reviews` file (`[return-value]`). `ruff check .`
  exit 0, `ruff format --check .` "105 files already formatted" exit 0, `mypy` "no issues found in
  96 source files" exit 0. The `**/*.md` exclusion is a real decision with a stated reason (`ruff
  format` would rewrite Python blocks inside 17 documents including the FROZEN `DESIGN.md`), not a
  quiet re-exemption of `docs/`.
- **Every control harness I ran fired.** `check-coupling-controls.py` exit 0;
  `check-obligations.py --controls` exit 0 ("Mappings: 31 | anchors verified against their subject:
  25 | recorded as absent: 6"); `scripts/check-harness-anchors-controls.sh` **9/9**;
  `scripts/ci-harness-gate-controls.sh` **24/24**.
- **A row-floor positive control actually deletes a row and restores.** Ran
  `check-row-floor-controls.sh check-suite-floor-amputation.sh`: 4 rows, floor 4, deleted line 75,
  "row invocations still matching: 3 (was 4, must be 3)", harness printed
  `::error::3/4 ROWS - THE HARNESS LOST ROWS.`, exit 1 as the table demands,
  "restored: byte-identical to the backup / restored: and identical to the commit", **CONTROL
  FIRED**. `git status --porcelain scripts/` clean afterwards.
- **The display grep and the assertion read the same population.** `check-row-floor-controls.sh:257`
  (display) and `floor_line()` at `:275-277` (assertion) both know the same three shapes, and the
  two non-regex ones contain no metacharacters, so `-E` in the display and `-F` in the assertion
  cannot diverge. `de6cd95`'s "verdict above a blank evidence block" is closed. The list is still
  hand-kept beside its container - that is task #107 and I am not re-filing it.
- **`--min-rows` refuses to run without `--row-re`** (`ci-harness-gate.sh:297`), and
  `check-row-floor-exactness.py:110-115` raises rather than reporting a reassuring zero when its
  `--min-rows` join count disagrees with the flag count. Both are the right shape.
- **`classify-w505.py` and both `adr-batch-*.py` declare themselves one-shots in their docstrings**,
  with the reason. That is the correct handling of an unwired tool and it is what makes R12-H1's
  file stand out.

---

## What I could NOT settle

- **21 of the 23 row-floor positive controls.** I ran one end to end (above). Each takes ~2 minutes
  and mutates tracked source; 22 remain unwatched by me. `0c25ae3`'s worklog claims all 14 of the
  later batch fired - I did not re-run them.
- **The 21 hand-written `check-coupling-controls.py` mutations, individually.** They exit 0 as a
  set. I did not amputate the gate to prove each control dies with its subject; the SWEEP is the
  stronger instrument and I exercised that (0 holes, 6 designed escapes). I did NOT run the sweep's
  documented falsification arm - pointing it at a copy of `check-coupling.py` with checks 2b/2c
  removed, which its docstring says reproduces the 19 holes.
- **`check-coverage-floors.py`.** Exits **2** without `coverage.json`, which is the correct
  fail-closed, but I did not run `pytest --cov --cov-report=json` to exercise its real path.
- **The standards gate's absent-corpus arm on a runner.** A corpus exists locally at
  `/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards`, so my run took the
  present-corpus path (exit 0). The exit-2 path is reasoned from the source at `:135-139`, not
  observed here.
- **`check-cross-references.py`, `check-clause-citations.py`, `check-plan-measurements.py`,
  `check-resweep-verdicts.py`, `check-quickstart.py`, `check-env-vars-are-declared.py`,
  `check-settings-are-read.py`, `check-no-sigpipe-pipelines.py`, `check-adr-numbers.py`,
  `check-design-citation-shape.py`, `check-design-citations.py`, `check-row-floors.py`.** All run,
  all exit 0. I did not amputate their subjects to prove any of them non-vacuous.
- **Whether the C2-T2 §8 row SHOULD exist in `DESIGN.md` §8.** That is a frozen-design question and
  belongs to `review-r11`; I only measured that the gate rejects it and when.
- **The 24-minute `check-u9-http-amputation.sh` step and the other 35 harnesses.** Not run - the
  brief's time budget. The static row counts in R12-H2 are derived from unconditional top-level call
  sites, not from a run.

## Addendum - `check-review-coverage.py` at `42293f3`, reviewed as extra credit

Dispatched to me after the round above, on the grounds that a new unreviewed checker is exactly the
category this round audits. It is **unwired** and exits 1 today, so none of this is live. I read it
at `git show 42293f3:docs/reviews/check-review-coverage.py` (174 lines), ran it, and probed it; the
copy was removed and my tree is clean.

The design decision at its centre - **refuse to infer a range, report UNDECLARED instead** - is
right, and it is the load-bearing one. Everything below is around that decision, not against it.

### R12-H3 (High) - the container is `HEAD`, not `main`, and its LOWER BOUND is set by the declarations themselves

Line 149 is `trunk = git("rev-list", f"{earliest}..HEAD").split()`. The docstring says *"the commits
on `main`"*. Two separate ways that reads the wrong population, and I hit both at once by simply
running it in my own worktree:

```
  DECLARED  REVIEW-R12.md: f699f74..dad014e (45 commits)
  UNDECLARED CODE-REVIEW-R9.md: no REVIEW-COVERS line, no reason

Trunk commits since f699f74: 47
Inside a declared review range: 45
COVERED BY NOTHING: 2
```

**2, where you measured 59.** Neither number is a lie and both are useless without knowing which
population they describe.

1. **`HEAD` is whatever branch you are on.** I am on `review/r12` at `dad014e` plus two commits, so
   "trunk" here is my branch. This matters for #119: `actions/checkout` leaves HEAD at the PR's
   MERGE commit, so wiring this as-is makes every pull request red for its own not-yet-trunk
   commits. **Fix:** resolve the container explicitly - `git rev-list <earliest>..origin/main`, or
   take the ref as an argument defaulting to `main` - and refuse (exit 2) if that ref does not
   resolve, rather than silently falling back to HEAD.

2. **The floor is derived from the declarations, so the metric is not monotone.** `earliest` is
   `min(ranges.values(), key=<ancestor count>)[0]` (`:146-148`) - the oldest DECLARED base. In my
   tree `CODE-REVIEW-R9.md` carries no declaration, so the only range is mine, `earliest` becomes
   `f699f74`, and the 35 older commits R9's range would have anchored **left the denominator
   entirely**. That is the finding: the set being measured is defined by the set doing the
   measuring, so **deleting one `REVIEW-COVERS` line moves "COVERED BY NOTHING" from 59 to 2 and
   reads as a 96% improvement.** A coverage number that improves when a declaration is removed is
   the wrong direction for this instrument to be able to move.
   **Fix:** pin the floor to a constant the declarations cannot move - the same `8695101` your run
   names, as a module-level `TRUNK_ORIGIN` with the reason beside it - and keep `min(...)` only as
   an assertion: if any declared base is older than `TRUNK_ORIGIN`, that is a defect in one of them,
   not a new floor.

### R12-M4 (Medium) - the population is a name-shaped glob and it misses a real round

`review_documents()` globs `*REVIEW-R*.md` (`:101`). Enumerating the container instead of the glob:

```
in the container but NOT in the glob: ['REVIEW-CODE-R2.md']
```

`REVIEW-CODE-R2.md` is a genuine code-review round - R2, the U1/U3/U4 round - and the substring
`REVIEW-R` is absent from its name because the words are the other way round. It is therefore
**neither DECLARED, nor HISTORIC, nor UNDECLARED: it is not in the population at all**, so nothing
will ever ask it for a declaration and nothing records that it is missing one. A glob named for the
shape its author pictured missing the member spelled differently is the shape this repository has
now measured seven times.

**Fix:** select by CONTENT or by an explicit roster, not by name shape. Cheapest honest version:
glob `*.md`, keep anything whose first heading matches `CODE-REVIEW|REVIEW-R`, and require every
excluded file to be named in a stated `NOT_A_ROUND` map with its reason - the same discipline
`UNDECLARED_BY_HISTORY` already applies one level down. As a stopgap, `*REVIEW*R[0-9]*.md` picks up
`REVIEW-CODE-R2.md` today, and `REVIEW-CODE-R2.md` needs a `UNDECLARED_BY_HISTORY` entry the moment
it is in scope.

### R12-M5 (Medium) - the exemption and the verdict read `UNDECLARED_BY_HISTORY` with different rules

`:132` grants the exemption on KEY membership (`n not in UNDECLARED_BY_HISTORY`); `:135` prints the
verdict on VALUE truthiness (`if reason:`). An entry whose reason is `""` therefore gets the
exemption while being reported as unexplained. Probed by setting `REVIEW-R3.md` to `""`:

```
  UNDECLARED REVIEW-R3.md: no REVIEW-COVERS line, no reason
```

...printed by a run in which `REVIEW-R3.md` was never in `unexplained`. The docstring at `:71-72`
states the intended rule - *"A bare name is refused: the reason IS the exemption"* - and the code
does not implement it. This is `de6cd95`'s defect in miniature: a verdict line and the assertion
behind it reading the same population by different rules.

**Fix:** one line. Make the exemption test truthiness too -
`unexplained = [n for n in undeclared if not UNDECLARED_BY_HISTORY.get(n)]` - so a blank reason is
refused exactly as a missing key is. And assert at import that no value is blank, so the failure is
at the map rather than at a run.

### R12-L3 (Low) - "could not measure" and "found something" both exit 1

`git()` raises `SystemExit(message)` on a git failure (`:88-90`), and a string argument to
`SystemExit` exits **1** - the same code `main()` returns for "there are uncovered commits". A bad
SHA in a declaration, a missing ref, or git absent all render as a finding. This repository's own
convention is that `2` means the checker could not run: `check-review-coverage.py` already uses it
correctly at `:122` and `:142`, and `check-standards-citations.py:139` is the canonical case.

**Fix:** `raise SystemExit(2)` after printing, or `sys.exit(2)`, in `git()`.

### R12-N2 (nit) - only the FIRST declaration in a document is read

`DECLARATION.search()` (`:110`) returns one match. Measured on a two-declaration document: 2
present, `.search()` returns the first, the second is dropped in silence. A round that covered two
disjoint stretches - or a document later amended with a second range - loses coverage it declared.

**Fix:** `finditer`, and union the ranges. Two lines, and it removes a way for a declaration to be
written and not counted.

### On the declaration this round made

`REVIEW-COVERS: f699f74..dad014e` credits all 45 commits to a round that read 62 of the range's 133
files. The checker cannot see that, by construction - it records coverage per commit and says so at
`:39-44`. **So the manufactured-coverage risk the docstring rules out on the inferrer's side is
still open on the author's side**, and it will get worse the moment two agents split a range by
path, which is what happened here. **Suggested fix:** an optional third field -
`<!-- REVIEW-COVERS: f699f74..dad014e PATHS: docs/reviews scripts .github -->` - and treat a commit
as covered only when the union of the ranges claiming it also covers every path it touched
(`git show --name-only`). Two path-split rounds then compose into full coverage, and one of them
alone does not.

## Worktree

`/home/plafayette/claude_projects/fmj-worktrees/r12-gates` is left in place at the orchestrator's
request (it was created for me, not by me). Working tree is clean apart from this report;
every mutation made during this review was restored and confirmed against git.
