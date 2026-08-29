# FLOOR-FIRING - the remaining fourteen floors, watched firing

Task #102, the firing half. Branch `chore/floor-firing`, based at `f699f74`. Worktree
`/tmp/floor-firing-work`, removed when this was written. Not merged, not pushed. **No tracked file
under `src/`, `tests/`, `scripts/` or `.github/` was changed by this task**: every harness the
control mutates is restored by byte-copy inside the same run, and `git status --porcelain` was read
in the worktree after every one of the fifteen runs below and was empty every time.

**All fourteen floors FIRED.** Each one printed a line naming the count and the floor, and each one
exited its own documented breach code. One of the fourteen also produced a **sixth tally shape**
that `docs/reviews/check-row-floor-controls.sh` cannot see, so the control reported a failure
against a harness that was working correctly - section 3. That is a defect in the control, not in
the harness, and it is exactly the class of error the control's own header warns about.

The exit-6 question is settled by running it, in section 4: **a floor breach on the harness that
exits 6 DOES fail the CI job.** The gate exits 1.

## 1. The fourteen, and the exact line each one printed

Every line below is copied out of that run's own output. The floor is derived by `grep` from the
harness's source by the control; no floor is typed anywhere in this report or in the control.

| Harness | Rows | Floor | Removed | The line the floor printed | Exit | Fired |
|---|---|---|---|---|---|---|
| `check-body-cap-amputation.sh` | 5 | 5 | 1 | `::error::4/5 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-body-cap-controls.sh` | 12 | 12 | 1 | `########## 11/12 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-critical-coverage-amputation.sh` | 18 | 18 | 1 | `ONLY 17 ROWS RAN against a floor of 18. Rows were deleted` | 1 | **yes** (see §3) |
| `check-log-redaction-amputation.sh` | 6 | 6 | 1 | `::error::5/6 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u10-write-controls.sh` | 21 | 21 | 1 | `########## 20/21 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u12-jobfeed-controls.sh` | 17 | 17 | 1 | `########## 16/17 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u14-arguments-controls.sh` | 20 | 20 | 1 | `########## 19/20 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u5-jobs-amputation.sh` | 14 | 14 | 1 | `::error::the harness holds 13 rows, below its floor of 14` | 1 | yes |
| `check-u5-jobs-controls.sh` | 16 | 16 | 1 | `########## 15/16 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u6-paging-amputation.sh` | 11 | 11 | 1 | `::error::the harness holds 10 rows, below its floor of 11` | 1 | yes |
| `check-u6-paging-controls.sh` | 16 | 16 | 1 | `########## 15/16 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u8-candidates-amputation.sh` | 14 | 14 | 1 | `::error::the harness holds 13 rows, below its floor of 14` | 1 | yes |
| `check-u8-candidates-controls.sh` | 25 | 25 | 1 | `########## 24/25 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |
| `check-u9-http-controls.sh` | 14 | 14 | 1 | `########## 13/14 ROWS - THE HARNESS LOST ROWS.` | 1 | yes |

Thirteen of the fourteen also printed the control's closing sentence
`CONTROL FIRED: <harness> loses 1 row(s), prints <N>/<M> ROWS, exits 1.` The fourteenth is §3.

Every floor is TIGHT: `rows - floor + 1` was **1** for all fourteen, so one removed row was enough
in every case. Nothing here resembles the five-row slack #91 found in
`check-u7-resilience-controls.sh`. With #91's nine and the singular control's
`check-u15-gate-amputation.sh`, **all 24 harnesses carrying a literal `ROW_FLOOR` have now been
watched fire.**

Wall clock: the fourteen ran in about eight minutes total, not the ninety #91 measured for nine -
because all fourteen are tight, so each removes ONE row rather than six, and a control run executes
fewer rows than a normal run.

## 2. The widening for the fifth tally shape WORKS - it was exercised three times

The brief flagged that the control's assertion had been widened to accept
`holds N rows, below its floor of M` for the u5, u6 and u8 amputation harnesses, and that the
widening had never been run. **It ran three times and passed three times** - the three
`::error::the harness holds ...` rows in the table above. Had the widening been absent or wrong,
those three would have failed on the assertion; they did not. Nothing to fix.

## 3. FINDING (Medium) - a SIXTH tally shape, and the control calls a healthy harness broken

`check-critical-coverage-amputation.sh` fired correctly and exited 1. The control reported it as a
failure anyway, because it prints neither of the two shapes the control's `floor_line()` accepts:

```
########## ROWS: 17   ANCHORS APPLIED: 17
########## TOTAL SURVIVING ASSERTIONS: 3341
########## VACUOUS ROWS: 0 (declared survivors included)
########## UNDECLARED VACUOUS ROWS: 0
ONLY 17 ROWS RAN against a floor of 18. Rows were deleted
or a parser shape stopped matching; either way this is not a green.
::error::the floor named neither '17/18 ROWS' nor
         'holds 17 rows, below its floor of 18'. Either the
         comparison never fired, or the counter does not track rows.
exit with 1 row(s) deleted: 1 (must be 1)
```

The harness is fine. `scripts/check-critical-coverage-amputation.sh:468-470` is:

```bash
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "ONLY $ROWS ROWS RAN against a floor of $ROW_FLOOR. Rows were deleted"
  echo "or a parser shape stopped matching; either way this is not a green."
```

The comparison fired, the counter tracked the row (17 where 18 stood), the exit was 1 as the table
predicts. Only the control's pattern is short. **This is the same class of error the control's own
header names** - "a control asserting only the `N/M ROWS` form calls those three broken while they
are working perfectly" - arriving from a shape nobody had enumerated.

**I enumerated the container rather than patching this one instance.** For all 23 harnesses in the
control's table I read the `echo` immediately under the floor comparison
(`grep -nA3 -E 'lt "\$ROW_FLOOR"' scripts/<h>`). The shapes are:

- `N/M ROWS - THE HARNESS LOST ROWS.` with four prefixes - `::error::`, bare, `##########`,
  `ABORT: ` - 19 harnesses;
- `the harness holds N rows, below its floor of M` - 3 harnesses (u5, u6, u8 amputation);
- `ONLY N ROWS RAN against a floor of M` - **1 harness**, `check-critical-coverage-amputation.sh`.

That is the whole container. There is no seventh shape today.

**Suggested fix** (I did not apply it; the control is #91's file and this branch touches no
harness). One line in `docs/reviews/check-row-floor-controls.sh`'s `floor_line()`:

```bash
floor_line() {
  grep -qE "(^|[^0-9])${EXPECT}/${FLOOR} ROWS" "$1" ||
    grep -qF "holds ${EXPECT} rows, below its floor of ${FLOOR}" "$1" ||
    grep -qF "ONLY ${EXPECT} ROWS RAN against a floor of ${FLOOR}" "$1"
}
```

**Suggested fix, the durable one**, which I prefer and which is bigger than this task: three
hand-kept literal shapes beside 23 harnesses is a hand-kept list beside its container, and this
finding is that list's third miss. Make the harnesses print one canonical machine line
(`ROW-FLOOR: N/M`) *in addition to* their human sentence, and have the control grep only that. The
prose stays as varied as its author wants; the control stops guessing.

## 4. THE EXIT-6 QUESTION, SETTLED BY RUNNING IT: the gate exits 1, so CI fails

#91 left open whether a floor breach on `check-u11-advisory-controls.sh`, which exits **6** rather
than 1, actually fails the CI job. `scripts/ci-harness-gate.sh:206` reads `if [ "$rc" -ne 0 ]`,
which should catch it - but that is a READ.

I neutralised one of that harness's fifteen rows with the `:` builtin, then invoked the gate exactly
as `.github/workflows/ci.yml:874` invokes it. Verbatim output:

```
rows before        : 15
neutralising line  : 141
control MUT "the 30-day budget becomes 31" \
rows after         : 14 (must be 14)
--- ci.yml:874 verbatim: bash scripts/ci-harness-gate.sh check-u11-advisory-controls.sh --controls-fired ---
14/14 controls fired.
ABORT: 14/15 ROWS - THE HARNESS LOST ROWS.
A harness with fewer rows than its floor is green for the wrong reason.
::error::check-u11-advisory-controls.sh exited 6
GATE EXIT: 1   (0 = the breach would NOT fail CI; non-zero = it would)
restored: identical to the commit
```

**Answer: yes.** The harness exits 6, the gate's `rc -ne 0` branch catches it, prints
`::error::check-u11-advisory-controls.sh exited 6`, and the gate itself exits **1**, which fails the
step and the job. Note the harness's own `14/14 controls fired.` line immediately above the abort:
that is precisely the "green for the wrong reason" the floor exists to catch, and the gate does not
let it through.

Note also that the gate's amputation branch at `:193-204` special-cases `rc` of 1 and 3 *before*
line 206. `--controls-fired` is not `--amputation`, so that branch is not entered here; a floor
breach on an amputation harness would still reach 206 for any code other than 1 or 3, and for 1 it
exits 1 through the amputation message instead. Either way the job fails.

The probe is reproduced verbatim in section 6 so this is a measurement rather than a claim about
one.

## 5. Method, and the hazard I did not re-pay for

I used `docs/reviews/check-row-floor-controls.sh` unchanged, once per harness, sequentially, in a
dedicated worktree off `f699f74`. I did not reinvent the row-removal mechanism: it prefixes the call
with the `:` builtin and lets bash's own parser find the row's extent, which is #91's fix for the
row-cut-in-half defect that left an empty file named `=` in the repo root.

Checked after every run, and after the probe in §4:

- the control's own `restored: byte-identical to the backup` and `restored: and identical to the
  commit` lines - both present on all fifteen runs;
- `git -C /tmp/floor-firing-work status --porcelain` - **empty after every single run**, so no
  stranded mutation and no orphan file. I checked this because a stranded mutation poisons every
  later measurement and reads as someone else's merge.

Zero skips: every one of the fifteen runs executed its harness to completion and produced a floor
line and an exit code. Nothing was sampled, deferred, or reasoned about instead of run.

## 6. The exit-6 probe, verbatim

Not committed as a script: it is a one-shot answer to a one-shot question and it mutates a tracked
harness, which is not something that belongs in `scripts/` or in a CI path. It is reproduced whole
so it can be re-run rather than believed. Run as `bash <this> /path/to/worktree`.

```bash
#!/usr/bin/env bash
# Does a ROW-FLOOR breach on the one harness that exits 6 actually FAIL the CI
# job? scripts/ci-harness-gate.sh:206 reads `if [ "$rc" -ne 0 ]`, which should
# catch a 6 - but that is a READ. This runs it.
set -uo pipefail
REPO="${1:-/tmp/floor-firing-work}"
cd "$REPO" || exit 2
S=scripts/check-u11-advisory-controls.sh
RE='^control (MUT|AMP) '

git diff --quiet -- "$S" || { echo "ABORT: $S is dirty"; exit 3; }
B="$(mktemp)"
cp "$S" "$B"
trap 'cp "$B" "$S"; rm -f "$B"' EXIT

BEFORE=$(grep -cE "$RE" "$B")
L=$(grep -nE "$RE" "$B" | head -1 | cut -d: -f1)
echo "rows before        : $BEFORE"
echo "neutralising line  : $L"
sed -n "${L}p" "$B"
sed -n "${L}p" "$B" | grep -qE '\$\(|`' && { echo "ABORT: command substitution in row"; exit 9; }

awk -v k="$L" 'NR==k { print ": " $0; next } { print }' "$B" > "$S"
cmp -s "$S" "$B" && { echo "ABORT: the edit did not land"; exit 9; }
AFTER=$(grep -cE "$RE" "$S")
echo "rows after         : $AFTER (must be $((BEFORE - 1)))"
[ "$AFTER" -eq "$((BEFORE - 1))" ] || { echo "ABORT: wrong number of rows removed"; exit 9; }
bash -n "$S" || { echo "ABORT: neutralised harness does not parse"; exit 9; }

PYTHONDONTWRITEBYTECODE=1 bash scripts/ci-harness-gate.sh \
  check-u11-advisory-controls.sh --controls-fired > "$B.out" 2>&1
GATE_RC=$?
tail -12 "$B.out"
echo "GATE EXIT: $GATE_RC   (0 = the breach would NOT fail CI; non-zero = it would)"
rm -f "$B.out"

cp "$B" "$S"
git diff --quiet -- "$S" && echo "restored: identical to the commit" || echo "::error::RESTORE FAILED"
```

## 7. Nit - the control's closing sentence can misdescribe what it saw

`docs/reviews/check-row-floor-controls.sh`'s final line is hard-coded:

```
CONTROL FIRED: check-u5-jobs-amputation.sh loses 1 row(s), prints 13/14 ROWS, exits 1.
```

That harness printed `the harness holds 13 rows, below its floor of 14` and no `13/14 ROWS`
anywhere. The claim is false as written, and a reader taking that sentence as the evidence would
carry a shape the harness never emitted - the same decay that put a wrong citation into three
readers' hands on this project already.

**Suggested fix**: drop the shape from the sentence, since the run already prints the floor's real
line four lines above it under `--- the floor's own line ---`:

```bash
echo "CONTROL FIRED: $TARGET loses $DELETE row(s) and its floor said so, exiting $rc."
```

## 8. What I did NOT verify

- **I did not run the repository gates** (`ruff`, `mypy`, `pytest`, the suite and anchor floors).
  This branch adds one Markdown file under `docs/worklogs/` and changes nothing else; the harness
  mutations are restored inside each run and the tree was verified empty by
  `git status --porcelain` after every one. If you want the gate numbers for this branch they cost
  one run.
- **I did not fix the sixth tally shape (§3) or the nit (§7).** Both are in
  `docs/reviews/check-row-floor-controls.sh`, which is #91's file and is being read by the
  exactness checker; the brief said record and keep going. Both fixes are written out above.
- **The container survey in §3 covers the 23 harnesses in the control's table.** The 24th,
  `check-u15-gate-amputation.sh`, belongs to the singular `docs/reviews/check-row-floor-control.sh`
  and I did not read its floor message - it is out of this control's table and was already watched
  fire, but if the canonical-machine-line fix in §3 is adopted it needs to be in that sweep too.
- **I did not measure whether any floor is slack in the other direction after a future merge.**
  Every one of the fourteen is tight TODAY, at `f699f74`. That is a measurement of this commit, and
  #91's u7 finding is what a merge does to it. `docs/reviews/check-row-floor-exactness.py` is the
  standing instrument for that and it is already wired.
