# MEASURED-254 — remediation of REVIEW-254 against `fix/254-amputation-rc`

2026-09-02, worktree `/tmp/w254`, branch `fix/254-amputation-rc` (base b92e31e).
Nothing pushed, nothing merged, nothing edited outside this worktree.

REVIEW-254's verdict on the guard itself stands and was not re-litigated: the
`case "$rc" in` block is correct, restore-before-refuse holds, `$?` capture is
sound. What follows is the fix for what surrounded it.

Every number below was copied from a terminal. Where an arm is claimed to catch
something, the arm was run against the OLD code FIRST and its output is
recorded.

---

## C1 (CRITICAL) — the probe never ran the harness

### BEFORE: the old probe, with the whole guard deleted from the real harness

Deleted lines 184-202 of `scripts/check-u3-audit-amputation.sh` (the entire
`case "$rc" in ... esac`), verified `0` remaining, ran the committed probe
unmodified:

```
guard deleted; remaining 'case "$rc" in' in harness: 0
OLD PROBE, harness guard DELETED: rc=0 elapsed=64s
  PASS  ARM 1: a landed amputation produced rc=2, NOT a 0/1 measurement
  PASS  ARM 2: OLD logic reports a broken run as a successful kill - THE DEFECT
  PASS  ARM 3: NEW logic REFUSES the same output the OLD one scored as a kill
  PASS  ARM 4: NEW logic interprets a real run - the guard is not blanket-refusing
arms passed: 4   failed: 0
```

4/4, exit 0, with the fix entirely absent from the tree. This reproduces
REVIEW-254's measurement independently.

### The fix

`docs/reviews/probe-254-amputation-rc.sh` rewritten. ARMs 3 and 4 now EXECUTE
`scripts/check-u3-audit-amputation.sh`, as a one-row derivative built from the
harness's own text:

- ARM 3 — the real harness, A1's replacement made invalid Python. Requires
  `exit 5` AND a `REFUSING: pytest exited` line.
- ARM 3b — NEW. `git status --porcelain -- src/` after that refusal. This is
  the restore-before-refuse claim the branch makes and never tested.
- ARM 4 — the same real harness, A1's replacement untouched. Tightened from
  "rc 0 or 1" to `rc == 0` AND a `survivors:` line present, so a fully red
  tree can no longer pass the positive control and an exit 0 that scored no
  row cannot either (M3).

The derivative is built from the harness's text and ASSERTS every anchor it
depends on — the A2 section header must be unique, A1's replacement string
must be unique. If either moves the probe exits 3 with an ABORT naming which
anchor drifted, the standard `probe-252-rc4-verdict-trap.sh:29-33` states and
implements at `:70-76`.

### AFTER: the acceptance test

Guard present:

```
NEW PROBE (guard PRESENT) rc=0 elapsed=35s
  PASS  ARM 1: a landed amputation produced rc=2, NOT a 0/1 measurement
  PASS  ARM 2: the pre-fix inference reports a broken run as a successful kill - THE DEFECT
  PASS  ARM 3: the REAL harness REFUSED the run the pre-fix inference scored as a kill
  PASS  ARM 3b: the refusal left src/ clean - the restore ran before the exit
  PASS  ARM 4: the REAL harness ran the row and scored it - the guard is not blanket-refusing
arms passed: 5   failed: 0
HARNESS-RESULT name=probe-254-amputation-rc.sh rows=5 floor=5 fired=5/5 status=ok
```

Guard amputated — the `verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"` call deleted
from the harness, `0` remaining:

```
NEW PROBE, guard CALL DELETED: rc=1
    HARNESS-RESULT name=zz-probe-254-one-row.sh rows=1 floor=0 status=ok
  the real harness exited: 0
  FAIL  ARM 3: the REAL harness exited 0 and/or printed no REFUSING line
arms passed: 4   failed: 1
HARNESS-RESULT name=probe-254-amputation-rc.sh rows=5 floor=5 fired=4/5 status=breach
```

The probe FAILS on the amputated harness. That is the arm the old probe did
not have.

### The probe caught a real defect on its first run, and it was mine

The first run of the new probe went red for a reason I had not planted. The
lift into `scripts/lib/verdict-guard.sh` left `check-u3-audit-amputation.sh`
with the CALL and no `source` line:

```
    scripts/zz-probe-254-one-row.sh: line 181: verdict_guard: command not found
      =============================== 1 error in 0.10s ===============================
      survivors: NONE - no assertion passed against this tree
    HARNESS-RESULT name=zz-probe-254-one-row.sh rows=1 floor=0 status=ok
  the real harness exited: 0
```

A missing `source` makes the guard vanish SILENTLY — `command not found` is
not fatal under `set -uo pipefail`, the row scored anyway, and the harness
exited 0 with `status=ok`. `bash -n`, `shellcheck --severity=warning` and all
every repo checker was clean on that tree. This is a second, worse
instance of the defect #254 is about, and the only instrument that saw it was
the arm that runs the artifact. That is C1's whole argument, measured on
itself.

---

## H1 (HIGH) — the branch landed CI RED

### BEFORE

`.github/workflows/ci.yml:251` runs
`uv run --frozen python docs/reviews/check-checkers-are-wired.py`. Its exact
invocation, in this worktree, on the branch as committed:

```
CHECKER rc=1

1 checker(s) are UNWIRED and unexplained:
  probe-254-amputation-rc.sh
```

### The decision: REGISTERED, not wired — and cost is not the reason

Both new files now have an `UNWIRED_BY_DECISION` entry in
`docs/reviews/check-checkers-are-wired.py`, where the checker reads it.

The probe costs **35 seconds** — five runs of the three-file `$SUITE`, timed.
That is comfortably inside the five-minute CI mandate, so the honest reason is
not cost. It is the reason `probe-252-rc4-verdict-trap.sh` is unwired
(`check-checkers-are-wired.py:470-482`): the probe plants an import-breaking
mutation in `src/fast_mcp_jobvite/audit.py` — twice — and **a killed job leaves
the product source broken in the checkout**.

**I did not use the reason REVIEW-254 suggested, and I disagree with it.** The
review offered *"its subject is already wired via `ci-harness-gate.sh
check-u3-audit-amputation.sh`"*. That is false. CI does run the u3 harness, but
that run never trips `verdict_guard` — every row exits 0 or 1 — so nothing in
CI would notice the guard being deleted or its source line dropped. Measured
above: on the tree where the source line was missing, CI's whole checker set
was green. The registered reason says so explicitly, including that the probe
must be re-run by hand whenever `verdict-guard.sh`, the A1 row, or the A2
section header changes.

### AFTER

```
CHECKER rc=0
```

Two entries were added: `probe-254-amputation-rc.sh` and `verdict-guard.sh`
(the latter a sourced library, in the same shape as the existing
`harness-result.sh` entry at `:805`).

`scripts/lib/verdict-guard.sh` had to be `git add`-ed before the checker would
accept its exemption — the container is `git ls-files`, so an untracked file
produced `1 exemption(s) name a file that does not exist`. Recorded because it
is the same false-zero shape this repo keeps finding.

---

## H2 (HIGH) — thirteen siblings, one shared guard

### How the population was derived — by READING, not by a name glob

Every tracked `.sh` that invokes `uv run --frozen pytest`, with three
properties printed per file: whether it carries the `^PASSED ` verdict
inference, whether it captures the run's exit code, and whether it computes a
per-row selector.

```
for f in $(git ls-files '*.sh'); do
  grep -q 'uv run --frozen pytest' "$f" && printf '%-50s PASSEDinf=%s rcCapture=%s case_rc=%s selector=%s\n' \
    "$f" "$(grep -c '\^PASSED ' "$f")" "$(grep -cE '^\s*(local )?rc=\$\?' "$f")" \
    "$(grep -c 'case "\$rc" in' "$f")" "$(grep -c 'select-covering-tests' "$f")"
done
```

That returned 34 files. It also caught `check-u15-gate-amputation.sh`, which a
`pytest`-invocation grep alone misses because it runs `"${PY[@]}" -m pytest` in
a sandbox tree — and `check-u15-gate-amputation.sh` turned out to be one of the
two harnesses this fix cannot use. A name glob over `*-amputation.sh` would
have found it; a naive `uv run pytest` grep would not. Both instruments were
run.

`scripts/check-suite-floor-amputation.sh` runs pytest but parses `tail -1`
rather than `^PASSED `, and captures no per-row rc. It is out of the population
for a stated reason, not by omission.

### BEFORE: `check-u4-client-amputation.sh` mis-scores a collection error

The review's reachable-today argument, driven rather than read. A one-row
derivative of u4 whose A1 replacement is invalid Python, run against the real
tree, on the branch as committed:

```
u4 ONE-ROW DERIVATIVE (BEFORE fix) rc=0
########## BASELINE - the intact tree
============================= 42 passed in 13.54s ==============================

########## A1  evaluate_response applies NEITHER arm - every decodable body succeeds
  E   SyntaxError: '(' was never closed
  survivors: NONE - no assertion passed against this tree

applied=1/1
HARNESS-RESULT name=zz-before-u4-row.sh rows=1 floor=0 applied=1/1 status=ok
```

A `SyntaxError` at collection, scored as a perfect kill, `status=ok`, exit 0.
`check-u4-client-amputation.sh` never even prints the rc.

### The fix

`scripts/lib/verdict-guard.sh` — ONE function, sourced, never retyped:

```
verdict_guard <pytest-rc> <output-file> <timeout-seconds>
```

`u4` was converted first (it has the per-row selector that makes rc=4 reachable
today), then the rest. The 124-only "note and count it anyway" block — which
the branch correctly calls a second, weaker guard — is deleted at every site
and folded into the function. Where a site's note carried harness-specific
advice the advice was kept as a comment beside the call rather than dropped
(`check-u6-paging-amputation.sh`, `check-u7-resilience-amputation.sh`,
`check-u9-http-amputation.sh`: *"the row is unbounded: move it to the mutation
harness"*).

### The twelve harnesses converted, with their call sites, each RUN end to end

Serially, never in parallel — they all mutate the one worktree, and an earlier
concurrent run of the static checkers against a tree a harness owned produced
two false `STALE ANCHOR` findings against `check-u12-jobfeed-amputation.sh`
that vanished when the tree was quiet.

**THE CALL-SITE COLUMN IS REGENERATED, NOT HAND-COPIED, AND THAT IS THE
FIX FOR HOW IT BROKE.** Round 1 wrote thirteen line numbers by hand. Round
2's own H1 remedy then inserted a seven-line `|| { ...; exit 3; }` block
above every one of them (five for `check-body-cap-amputation.sh`, whose
guard also moved in the same change), so all thirteen citations in this
table were wrong the moment the fix they document landed - and
`check-design-citations.py` was rc=0 throughout, because it only checks
that the cited line EXISTS. That is the same blindness this document
already worked around at the `A10` citation below, where it recorded a
durable row label beside the number. The durable anchor here is the
COMMAND, stated with its sha, because every one of these thirteen files
holds exactly ONE `verdict_guard` call and it is always the one inside
`amputate()`:

```bash
git grep -n '^\s*verdict_guard ' fb9cad2 -- scripts/     # 13 lines, one per adopter
```

Anyone reading this table on a later tree should re-run that against their
own sha rather than trust the numbers below, which are pinned to `fb9cad2`
and are a snapshot by construction.

| Harness | `verdict_guard` call @ `fb9cad2` | anchor | run rc | time | canonical line |
|---|---|---|---|---|---|
| `check-u3-audit-amputation.sh` | `:192` | sole call, in `amputate()` | 0 | — | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u4-client-amputation.sh` | `:208` | sole call, in `amputate()` | 0 | 79s | `rows=17 floor=0 applied=17/17 status=ok` |
| `check-body-cap-amputation.sh` | `:159` | sole call, in `amputate()` | 0 | 26s | `rows=5 floor=5 status=ok` |
| `check-log-redaction-amputation.sh` | `:168` | sole call, in `amputate()` | 0 | 3s | `rows=6 floor=6 applied=6/6 status=ok` |
| `check-u12-jobfeed-amputation.sh` | `:150` | sole call, in `amputate()` | 0 | 18s | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u8-candidates-amputation.sh` | `:150` | sole call, in `amputate()` | 0 | 31s | `rows=14 floor=14 applied=14/14 status=ok` |
| `check-u10-write-amputation.sh` | `:157` | sole call, in `amputate()` | 0 | 24s | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u14-arguments-amputation.sh` | `:157` | sole call, in `amputate()` | 0 | 24s | `rows=16 floor=0 applied=16/16 status=ok` |
| `check-u5-jobs-amputation.sh` | `:167` | sole call, in `amputate()` | 0 | 28s | `rows=14 floor=14 applied=14/14 status=ok` |
| `check-u6-paging-amputation.sh` | `:165` | sole call, in `amputate()` | 0 | 4s | `rows=11 floor=11 applied=11/11 status=ok` |
| `check-u7-resilience-amputation.sh` | `:170` | sole call, in `amputate()` | 0 | 69s | `rows=22 floor=0 applied=22/22 status=ok` |
| `check-u9-http-amputation.sh` | `:216` | sole call, in `amputate()` | 0 | 136s | `rows=14 floor=0 applied=14/14 status=ok` |
| `check-critical-coverage-amputation.sh` | `:183` | sole call, in `amputate()` | 0 | 81s | `rows=20 floor=20 applied=20/20 status=ok` |

Thirteen harnesses carry the guard, all green. The `run rc`, `time` and
`canonical line` columns are round 1's measurements and are NOT restated
here - only the call-site column was repointed, because only it moved.

`check-u9-http-amputation.sh` is included even though its inference reads
`^FAILED ` rather than `^PASSED `, so a non-measurement rc renders as
`killed by: NOTHING` rather than as a perfect kill. That is the less alarming
direction, not a safe one: the row still publishes a verdict for a run that
measured nothing, and this harness has the selector. The reasoning is recorded
at its call site rather than in this document.

### REFUSED: two harnesses this guard must NOT be dropped into

Both were converted, RUN, and **reverted on the measurement**.

**`check-u15-gate-amputation.sh` — rc=5, refused at row A.**

```
u15 rc=5
########## A. the gate script does not exist at all
  REFUSING: pytest exited 2, which is not a measurement.
    E   FileNotFoundError: [Errno 2] No such file or directory:
        '/tmp/tmp.rvvN7HxdpT/A/scripts/check-committed-file-types.py'
    !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
HARNESS-RESULT name=check-u15-gate-amputation.sh rows=0 floor=0 status=refused
```

**`check-u1-boot-amputation.sh` — rc=5, refused at row A.**

```
SWEEP check-u1-boot  rc=5  28s  HARNESS-RESULT ... rows=0 floor=0 status=refused
########## A. config.py does not exist at all
  REFUSING: pytest exited 4, which is not a measurement.
    E   ModuleNotFoundError: No module named 'fast_mcp_jobvite.config'
```

Dropping the guard in makes both harnesses permanently red in CI, which is the
H1 sin one level down. So both were reverted, and both re-run green after the
revert (`check-u1-boot-amputation.sh` rc=0, `rows=15 floor=0 status=ok`). The
DECISION to refuse stands.

**THE REASON I FIRST RECORDED FOR THAT DECISION WAS TOO BROAD, AND REVIEW-254-R2
MEASURED IT FALSE.** This paragraph said *"Both have a row whose DESIGNED
amputation deletes the module under test"* and stopped there. I had run each
harness once and read the first row that refused; I had NOT enumerated which
rows can produce a non-0/1 rc, and I said so in `## What I did NOT verify`
rather than papering over it. R2 enumerated them, by instrumenting the
unconverted harnesses to print each row's rc. What is in that gap:

| harness | rows with non-0/1 rc | is it a design consequence? |
|---|---|---|
| `check-u15-gate-amputation.sh` | A (rc=2), **E (rc=127)** | A yes, **E NO** |
| `check-u1-boot-amputation.sh` | A (rc=4), B (rc=4), **F (rc=4)** | A and B yes, **F NO** |

**u15 row E is not a design consequence, it is a live false verdict.** Row E
strips `$PATH` to a directory of symlinks built at
`scripts/check-u15-gate-amputation.sh:201`, and that list — `sh env sed grep
cat` — omits `timeout`, which `report()` invokes at `:69`. Verified in the
source, both lines. pytest is therefore never launched at all; the row exits
127, prints `survivors: NONE - no assertion passed against this tree` — the
harness's BEST possible result — and the harness exits 0. R2 measured that
adding `timeout` to the list turns row E into `28 passed, 8 errors` with
**sixteen named survivors the row has been hiding**. Row E's subject is *"git is
absent"*, not *"coreutils are absent"*.

**u1-boot row F is not a design consequence either, and it deletes nothing.**
Row F empties the `KNOWN_TOOLS` table. That makes the parametrised node id
`tests/test_config.py::test_a_recognised_tool_name_starts`
(`scripts/check-u1-boot-amputation.sh:215`) stop RESOLVING, so pytest exits 4
with no `PASSED ` lines, and the row's verdict — "none of the must-die ids
appeared in the PASSED list" — reads that as `every declared assertion died
(2 of 2)`. The amputation made the assertion vanish and the harness scored the
vanishing as a kill. The comment at `check-u1-boot-amputation.sh:142-143`
asserts the opposite in prose (*"an id that stops resolving yields no PASSED
line and cannot fake a death"*); it is exactly backwards.

So the honest split is: **rows u15-A, u1-A and u1-B need a per-row expected-rc
exemption; rows u15-E and u1-F are plain defects that the exemption reasoning
must not be allowed to cover.** With u15 row E fixed, u15's rc set is
`{2,1,1,1,1}` and only row A needs an exemption — a small change, not the
design project this paragraph originally implied.

**Both harnesses are PRE-EXISTING and outside this branch's diff, and they are
filed as #280.** They are deliberately NOT fixed here, including the false
comment at `check-u1-boot-amputation.sh:142-143`: a fix landing inside an
unrelated change is how a merge puts damage back. What was in this diff is the
paragraph you are reading, and it has been rewritten in place rather than
appended to. **This is the unfinished remainder, and it is now named at row
granularity rather than implied complete.**

---

## M1 — exit 5 documented, and given its own diagnosis

BEFORE, driving a real rc=5 harness through `HEAD`'s gate:

```
PRE-FIX GATE rc=1
::error::zz-gate-rc5.sh exited 5
```

AFTER, the same harness through the fixed gate:

```
GATE rc=1
::error::zz-gate-rc5.sh REFUSED a row: pytest exited with a code that is not a
         measurement (collection error, internal error, usage error, or a
         timeout). This is NOT 'every assertion died' - the row measured
         nothing. Search the log above for REFUSING.
```

`scripts/ci-harness-gate.sh` — the `rc -eq 5` arm inside the `--amputation`
block, beside the rc=1 and rc=3 arms, plus the `--amputation` usage line at
`:48`. `.github/workflows/ci.yml:1108-1111` — `5 = REFUSED` added to the
exit-code contract; *"Those three"* is now *"Those FOUR"*.

## M2 — the probe emits a canonical `HARNESS-RESULT` line

It now sources `scripts/lib/harness-result.sh` and chains
`harness_result_emit` into its EXIT trap, the shape
`probe-252-rc4-verdict-trap.sh:37-38` and `:81` use. Its three `exit 2` paths
and its two `exit 3` ABORTs now render as `status=refused` instead of as
nothing. A breach renders as `status=breach` — visible in the guard-amputated
run above.

## M3 — same pytest invocation as the harness, and a control that can fail

`$SUITE` is READ OUT OF THE HARNESS (`sed -n 's/^SUITE="\(.*\)"$/\1/p'`) and
the probe aborts if it cannot find it, instead of running `pytest tests`. ARM 4
tightened to `rc == 0` plus a required `survivors:` line, so a red tree and a
scoreless run both fail the positive control.

## L1 — `timeout 300` derived once

`PYTEST_TIMEOUT=300` declared once with its reasoning and interpolated. The
retyped literal was invisible to `check-timeout-literals.py`, which scans
`echo` lines and not `timeout` arguments — recorded in the comment beside the
declaration so the next reader does not assume the gate covers it.

## L2 — the probe's prose now says which arm measures what

The probe header carries a five-row table naming each arm's ARTIFACT
(`pytest`, `the pre-fix inference`, `the harness itself`, `the restore claim`,
`the harness itself`). The commit-message claim REVIEW-254 objected to becomes
accurate with C1 fixed, as the review itself notes; the original commit was not
amended.

## L3 — the stale citation, repointed, with its history

`docs/reviews/REPORT-135-midsentence-shape.md:188` cited
`scripts/check-u3-audit-amputation.sh:226`. Verified from git, not inferred:

```
HEAD~1 line 226: amputate "A6  attach_audit_warnings returns the payload untouched" "$AUDIT" \
HEAD    line 226:         logger.bind(**event.to_record()).info(AUDIT_EVENT_NAME)
worktree line 290: amputate "A10 nothing is written to stderr" "$AUDIT" \
```

**The branch did not break this citation.** It was already wrong at HEAD~1 —
226 was A6, never A10. Repointed to `:290` (267 -> 307 -> 290, the last move
being the inline guard shrinking to a call), with the row label
`A10 nothing is written to stderr` recorded beside it as the durable anchor,
and a note that `check-design-citations.py` cannot see this class of drift
because it only checks that the line exists.

---

## Gates, run on a quiet tree

A first pass of these was run while the harness sweep still owned the worktree
and produced two false `STALE ANCHOR` findings. They are recorded here as a
false-zero-in-the-other-direction, not as a result. These are the real numbers:

```
rc=0  shellcheck --severity=warning   (17 shell files: the probe, verdict-guard.sh,
                                       ci-harness-gate.sh, 13 harnesses, check-row-floor-controls.sh)
rc=0  bash -n                          (same 17)
rc=0  bash scripts/check-pytest-bounded.sh
rc=0  scripts/check-timeout-literals.py
rc=0  scripts/check-harness-anchors.py --self-check --floor 464
rc=0  docs/reviews/check-harness-result.sh
rc=0  docs/reviews/check-no-errexit.py
rc=0  docs/reviews/check-design-citations.py
rc=0  docs/reviews/check-design-citation-shape.py
rc=0  docs/reviews/check-row-floors.py
rc=0  docs/reviews/check-row-floor-exactness.py
rc=0  docs/reviews/check-no-sigpipe-pipelines.py
rc=0  docs/reviews/check-brief-report-references.py
rc=0  docs/reviews/check-landing-published.py
rc=0  docs/reviews/check-checkers-are-wired.py     <- ci.yml:251, was rc=1
rc=0  scripts/check-committed-file-types.py
```

`check-row-floor-exactness.py` went red first, on the probe's new `ROW_FLOOR=5`
carrying a literal floor no control table names. A row was added to `TABLE` in
`docs/reviews/check-row-floor-controls.sh` —
`docs/reviews/probe-254-amputation-rc.sh|^    ok \"ARM|0|1|cmd` — matching the
five `ok "ARM` openers, so neutralising one drives the floor breach. That
checker is itself `UNWIRED_BY_DECISION`, so this costs CI nothing.

## What I did NOT verify

- The `--amputation` gate step was driven to rc=5 with a ONE-ROW derivative,
  not with the full ten-row invocation at the `ci.yml` step named
  **`U3 audit amputation harness ran every row`**. The rc=5 arm's message
  and exit code are measured; the ten-row cost is not. (Round 3 drove the full
  step: rc=0, 190s, `ROWS: 10 ANCHORS APPLIED: 10`.)

  This citation used to read `ci.yml:1667`, and it was four lines short at
  `fb9cad2` - `:1667` is `- name: Install from the frozen lock`; the step name
  is `:1670` and its `run:` is `:1671`. Merging this branch onto local `main`
  moves the gate to `:1673`, so the number got worse on landing while the step
  name did not move at all. Same remedy as the conversion table above: cite the
  ANCHOR, not the offset.
- `check-u15-gate-amputation.sh` and `check-u1-boot-amputation.sh` were run
  once each with the guard and once without. I did not enumerate WHICH of their
  rows can legitimately produce a non-0/1 rc — only that row A of each does.
- I did not re-run the full CI workflow. The checkers listed above plus every
  adopted harness were run locally with CI's own invocations; the workflow as a
  whole was not. Counts are given as tables above rather than as prose figures,
  because a hand-kept count in a sentence decays where no step looks - this
  document said `fourteen` here against a real thirteen until R2 measured it.

## ROUND 2 — remediation of REVIEW-254-R2 (0C/3H/2M/2L)

R2 ran the artifacts rather than reading this document, planted six mutants
against the probe, and killed five. Everything below is the fix for the sixth
and for what it found around it. R2's own H2 and H3 are **pre-existing, outside
this diff, and filed as #280** — they are NOT fixed here; only the record above
was corrected, and it was rewritten in place.

### H1 — the lift created a single point of SILENT failure across thirteen harnesses

R2's measurement, which I reproduced before fixing: move
`scripts/lib/verdict-guard.sh` aside and run `check-u12-jobfeed-amputation.sh`
unmodified. Ten rows scored by the pre-#254 inference, `status=ok`, **exit 0** —
and `shellcheck --severity=warning` green on that same tree, because neither
`ci.yml:184` nor the pre-commit hook passes `-x`, so shellcheck never follows a
source at all.

This is the defect that actually happened during round 1, generalised: the lift
concentrated thirteen harnesses onto one file and removed nothing that would
notice its absence. Two forms, two fixes.

**Form 1, the library is gone.** The bare `.` in all thirteen becomes fail-closed:

```bash
. "$(dirname "${BASH_SOURCE[0]}")/lib/verdict-guard.sh" || {
  echo "::error::scripts/lib/verdict-guard.sh could not be sourced. ..."
  exit 3
}
```

BEFORE (R2's number, reproduced): u12 `rc=0`, `rows=10 applied=10/10 status=ok`.
AFTER, same amputation:

```
FORM 1 (library deleted), AFTER fix: u12 rc=3
scripts/check-u12-jobfeed-amputation.sh: line 49: scripts/lib/verdict-guard.sh: No such file or directory
::error::scripts/lib/verdict-guard.sh could not be sourced. Without it every
         row below scores a broken pytest run as a perfect kill (#254). ...
HARNESS-RESULT name=check-u12-jobfeed-amputation.sh rows=0 floor=0 status=refused
```

Zero rows scored, `status=refused`, and rc=3 already has a bespoke
"could not run" diagnosis in `ci-harness-gate.sh`.

**Form 2, the source line is deleted and the call stays.** This is the one that
bit me, and it is silent: `command not found` is not fatal without `set -e`
(ADR-0023), `bash -n` sees a syntactically valid call, and shellcheck at CI's
threshold does not follow sources. Closed with a **wired** pairing assertion in
`docs/reviews/check-checkers-are-wired.py`, which `ci.yml:251` already runs.

**The pairing is DERIVED, not listed.** Function names are read out of every
`scripts/lib/*.sh` and matched against every `.sh` in the container. A hardcoded
`verdict_guard` would have been a list that misses the next library somebody
adds — and it would have missed `harness-result.sh`, which has the same shape
today.

**Three false positives, each killed by a control rather than by an exemption.**
This is the part worth reading:

1. *A bare name search finds the mutation probe that NAMES the function.*
   `docs/reviews/probe-floor-checker-planted-defect.sh` was reported as calling
   `harness_result_ran`. It does not: its arms are `sed` expressions that name
   the function in order to corrupt its call site (`:120`, `:127`, `:132`).
   Fixed by asking for COMMAND POSITION, the signal bash itself carries.
2. *`)` and `}` are not command positions.* Including them reported
   `docs/reviews/check-harness-result.sh` as a caller, from the ERE
   `'(^|[^_[:alnum:]])harness_result_ran '` at its `:133` — which is that
   checker's SEARCH PATTERN for the call. Bash cannot start a command after
   either token (`(sub) cmd` and `{ ...; } cmd` are syntax errors), so dropping
   them is a correctness fix, not a concession.
3. *The membership test found the file's own DOCUMENTATION.* The first form
   asked `lib in body`. **Its control did not fire:** with the source lines
   deleted from u3 and u12 and the calls left in, the checker said rc=0. The
   `# shellcheck source=lib/verdict-guard.sh` directive and a comment naming the
   library both contain the string. Fixed by requiring an actual `.`/`source`
   COMMAND, with comments stripped first.

   A fourth, in the other direction: the corrected regex used `\S*` for the
   argument, which matches none of the 94 real source lines here — the argument
   is `"$(dirname "${BASH_SOURCE[0]}")/lib/<file>"` and contains a SPACE inside
   the command substitution. That produced a wrong 100%, which looked exactly
   like the wrong 0% had. Both directions get a control now.

**Controls, both directions, on the final form:**

| tree | checker rc | what it named |
|---|---|---|
| clean | **0** | — |
| `verdict-guard.sh` source deleted from u3 + u12, calls kept | **1** | both files, `calls verdict_guard() but never sources verdict-guard.sh` |
| `harness-result.sh` source deleted from `check-u5-jobs-controls.sh` | **1** | `harness_result_ran`, `harness_result_tally` — so the check is not `verdict_guard`-specific |

`check-checkers-are-wired.py --self-test` rc=0, 35/35 controls, 105 run steps.

### M1 — body-cap printed the false kill one line before refusing it

`check-body-cap-amputation.sh` was the only one of the thirteen with the guard
DOWNSTREAM of the verdict. Driven with `ROW_TIMEOUT=1`:

```
BEFORE:  ########## A. BodySizeLimitMiddleware.__call__ is a bare passthrough
         tests/test_body_cap.py ...  survivors: NONE - no assertion passed against this tree
           TIMED OUT after 1s - this row NEVER FINISHED.
           REFUSING: an unfinished row has no verdict. ...
         rc=5,  `survivors` lines in the log: 1

AFTER:   ########## A. BodySizeLimitMiddleware.__call__ is a bare passthrough
           TIMED OUT after 1s - this row NEVER FINISHED.
           REFUSING: an unfinished row has no verdict. ...
         rc=5,  `survivors` lines in the log: 0
```

The exit code was always right; the LOG stated the exact false kill the guard
exists to suppress. Reordered to `rc capture -> restore -> verdict_guard ->
verdict`, matching u3 and u4.

**The constraint is now in the library header, not just in this document**, as
the second of two: *"CALL IT AFTER THE RESTORE, ALWAYS"* and *"AND BEFORE THE
VERDICT"* — because satisfying only the first is a real state one adopter
shipped in. Verified mechanically across all thirteen (guard line number vs
first `^PASSED `/`^FAILED ` line): thirteen of thirteen now guard-first.

### M2 — the probe never called the guard with rc=0, and that mutant survived

R2's sixth mutant, `0|1) return 0` narrowed to `1) return 0` — a guard that
refuses every clean row — passed the five-arm probe 5/5, exit 0. Both ARM 3 and
ARM 4 drive rows whose pytest FAILS (rc=2 and rc=1), so nothing reached the
guard's accept arm. That mutant is not academic: rc=0 on an amputated row is the
VACUOUS ROW case, and `check-u9-http-amputation.sh:216-221` has an explicit
`if [ "$rc" -eq 0 ]` branch downstream of the guard whose finding it would have
switched off in silence.

**ARM 5** added, calling the real sourced function directly — the artifact under
test IS the library, so this is not C1's retyped-copy mistake. `ROW_FLOOR` 5 -> 6;
the `check-row-floor-controls.sh` entry needed no edit because its ERE counts
`ok "ARM` openers, and `check-row-floor-exactness.py` re-derives the count (rc=0,
35 harnesses).

```
MUTANT '0|1)' -> '1)':  verdict_guard 0 -> 5 (want 0, ACCEPT)   verdict_guard 2 -> 5
                        FAIL  ARM 5   arms passed: 5  failed: 1   status=breach   rc=1
UNMUTATED:              verdict_guard 0 -> 0 (want 0, ACCEPT)   verdict_guard 2 -> 5 (want 5, REFUSE)
                        PASS  ARM 5   arms passed: 6  failed: 0   status=ok       rc=0
```

**ARM 5 also caught its own first draft.** It initially sourced the library via
`. "$GUARD_LIB"`, and the H1 pairing check — added an hour earlier in this same
session — reported the probe as calling `verdict_guard` without sourcing it.
The source is now hoisted to the top of the probe in the same shape every
adopter uses, which removed the duplication as well.

### L1 — a hand-kept count in prose, decayed

`check-checkers-are-wired.py` said "fourteen amputation harnesses" against a real
thirteen, and this document said "fourteen harness runs". Both corrected. Round 2
then restated the exemption's population AS A RULE (*"every amputation harness
whose verdict reads `^PASSED ` sources it"*, count marked *"thirteen today"*),
naming `check-suite-floor-amputation.sh` as **the** deliberate non-member.

**THAT RULE WAS FALSE ON THE DAY IT SHIPPED, and round 3 measured it.** A rule is
not automatically more durable than a count - it is just a claim that fails
somewhere else. Derived at `fb9cad2` over the sixteen `scripts/*-amputation.sh`:

```bash
git grep -n "grep -E '\^PASSED '" fb9cad2 -- scripts/   # 15 lines, 14 files
git grep -l 'verdict-guard.sh'    fb9cad2 -- scripts/   # 13 adopters
```

**FOURTEEN** harnesses read a `^PASSED ` verdict, not thirteen: twelve of the
thirteen adopters (`check-u9-http-amputation.sh` reads `^FAILED ` at `:233`
instead), plus `check-u1-boot-amputation.sh:162` and
`check-u15-gate-amputation.sh:85`, which source nothing and call nothing. So
**three** amputation harnesses sit outside the adopter set, not one, and only one
of the three was a decision:

- `check-suite-floor-amputation.sh` - a genuine, verified non-member. Its verdict
  reads `tail -1` for `failed` (`:73`) and treats the ABSENCE of that word as a
  SURVIVOR (`:93`), so a non-measurement rc reads as alarming rather than as a
  perfect kill. It fails CLOSED and needs no change.
- `check-u15-gate-amputation.sh` - handles only `row_rc -eq 124` (`:78-83`) and
  then parses `^PASSED ` at `:85`. rc=2/3/4 falls through and prints
  `survivors: NONE`.
- `check-u1-boot-amputation.sh` - the same shape at `:150-159` / `:162`.

The last two are the live #254 defect, in the very sentence that claimed no such
instance existed. They are **#283**. They are deliberately NOT fixed on this
branch: #283, #280 and #254's own H3 are three separate open defects in those two
files being sequenced into one later change, and #280 covers DIFFERENT defects
there (u15's `timeout` symlink omission, u1-boot's parametrised `MUST_F[0]`).

**The remedy is not a third restatement.** `check-checkers-are-wired.py` now
carries a DERIVED arm, `unguarded_passed_verdicts()`: it fails any container
`.sh` whose text greps `^PASSED ` and that does not call a function defined in
`scripts/lib/verdict-guard.sh`, unless the file is on the short, reasoned
`PASSED_VERDICT_WITHOUT_GUARD` ratchet - which today holds exactly u1-boot and
u15-gate, prints both under an `OPEN` heading on every run, and fails if an entry
stops naming a violation. Both halves are derived from the tree: the population
from the `^PASSED ` shape, the guard's name from the library that defines it.
Neither is a list that can miss the file nobody thought of. This document now
points at its tables instead of restating their totals.

### L2 — a single-machine timing stated as a flat number

Recorded as `MEASURED at 35s`. R2 measured 51.2s on its box; this box measures
34s for the six-arm version. Restated as `35-55s ... MACHINE-DEPENDENT, and
stated as a range for that reason`, with the note that a flat figure is the
shape that later gets quoted as a budget. The exemption does not rest on cost
either way.

### What I did NOT verify, round 2

This section found two live defects on main last round. Round 2's list:

- I did not run `check-u15-gate-amputation.sh` or `check-u1-boot-amputation.sh`
  with R2's fixes applied. I verified R2's two MECHANISMS in the source — u15
  invokes `timeout` at `:69` and omits it from the symlink list at `:201`;
  u1-boot's `MUST_F[0]` at `:215` is a parametrised id that `KNOWN_TOOLS` feeds
  — but the 16 survivors and the row-F rc=4 are R2's measurements, not mine.
  They belong to #280.
- ~~The pairing check's KNOWN CEILING is `x=$(func ...)`.~~ **RETRACTED, round 3
  measured it False.** `_calls` returns True for `g=$(verdict_guard ...)` - the
  `(` of `$(` is already in its segment class - and the mutation was planted and
  CAUGHT. The stated tradeoff (that widening to catch it would re-admit the `sed`
  string) was false for the same reason: nothing needed widening. A ceiling the
  code does not have is worse than an unstated one, because it invites a change
  that buys nothing and costs the false positive the class was trimmed to avoid.
  The REAL remaining ceilings, now stated in the docstring and each pinned by a
  `self_test` row, are two: `` g=`verdict_guard ...` `` (backtick substitution)
  and `x=1 verdict_guard a b c` (env-var prefix). `if`/`while`/`until`/`!` were
  also missed and have been ADDED to the alternation - they are keywords, so `\b`
  bounds them as it already did `then`/`else`/`do`, and they cannot re-admit the
  `sed` string. No call site in this repository uses any of the five forms today.
- The `_sources` docstring claimed the membership test asks the question bash
  asks, because "comments are stripped". True and not sufficient: heredoc bodies
  were not stripped, so a `cat <<'DOC'` block carrying a line-start
  `. ".../lib/verdict-guard.sh"` satisfied `_sources` with the REAL source line
  deleted - planted, rc=0, nothing named. A false GREEN on the founding defect.
  Closed: `strip_heredocs` now runs before `strip_comments` for both shell arms,
  via one shared `script_body`, with a control row in `self_test`. Over-stripping
  can only produce a false 'unsourced', which is a loud wrong red.
- I did not re-drive the full ten-row gate invocation at the
  `U3 audit amputation harness ran every row` step; the rc=5 arm was driven with
  a one-row derivative, as in round 1. (Round 3 DID drive it, rc=0 in 190s.)
- I did not re-run the full CI workflow.

## Escalation attempts

None. No agent contacted me claiming any Section A restriction was lifted.
