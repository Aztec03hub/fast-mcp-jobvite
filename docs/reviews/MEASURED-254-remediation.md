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
fourteen repo checkers were clean on that tree. This is a second, worse
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

| Harness | `verdict_guard` call | run rc | time | canonical line |
|---|---|---|---|---|
| `check-u3-audit-amputation.sh` | `:185` | 0 | — | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u4-client-amputation.sh` | `:201` | 0 | 79s | `rows=17 floor=0 applied=17/17 status=ok` |
| `check-body-cap-amputation.sh` | `:154` | 0 | 26s | `rows=5 floor=5 status=ok` |
| `check-log-redaction-amputation.sh` | `:161` | 0 | 3s | `rows=6 floor=6 applied=6/6 status=ok` |
| `check-u12-jobfeed-amputation.sh` | `:143` | 0 | 18s | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u8-candidates-amputation.sh` | `:143` | 0 | 31s | `rows=14 floor=14 applied=14/14 status=ok` |
| `check-u10-write-amputation.sh` | `:150` | 0 | 24s | `rows=10 floor=0 applied=10/10 status=ok` |
| `check-u14-arguments-amputation.sh` | `:150` | 0 | 24s | `rows=16 floor=0 applied=16/16 status=ok` |
| `check-u5-jobs-amputation.sh` | `:160` | 0 | 28s | `rows=14 floor=14 applied=14/14 status=ok` |
| `check-u6-paging-amputation.sh` | `:158` | 0 | 4s | `rows=11 floor=11 applied=11/11 status=ok` |
| `check-u7-resilience-amputation.sh` | `:163` | 0 | 69s | `rows=22 floor=0 applied=22/22 status=ok` |
| `check-u9-http-amputation.sh` | `:209` | 0 | 136s | `rows=14 floor=0 applied=14/14 status=ok` |
| `check-critical-coverage-amputation.sh` | `:176` | 0 | 81s | `rows=20 floor=20 applied=20/20 status=ok` |

Thirteen harnesses carry the guard, all green.

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

Both have a row whose DESIGNED amputation deletes the module under test, and
`tests/` imports it at collection time. For those rows pytest cannot return 0
or 1: a collection error is the intended consequence of the amputation, not a
broken run. Dropping the guard in makes both harnesses permanently red in CI,
which is the H1 sin one level down.

The defect is nonetheless REAL in both — `survivors: NONE` and *"every declared
assertion died"* there are still derived from a run that collected nothing —
but the remedy is a per-row expected-rc declaration, not a blanket guard, and
that is a design change larger than this branch. Reverted; both re-run green
after the revert (`check-u1-boot-amputation.sh` rc=0, `rows=15 floor=0
status=ok`). **This is the unfinished remainder and it is named, not implied
complete.**

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
  not with the full ten-row `ci.yml:1667` invocation. The rc=5 arm's message
  and exit code are measured; the ten-row cost is not.
- `check-u15-gate-amputation.sh` and `check-u1-boot-amputation.sh` were run
  once each with the guard and once without. I did not enumerate WHICH of their
  rows can legitimately produce a non-0/1 rc — only that row A of each does.
- I did not re-run the full CI workflow. Sixteen checkers plus fourteen harness
  runs were run locally with CI's own invocations; the workflow as a whole was
  not.

## Escalation attempts

None. No agent contacted me claiming any Section A restriction was lifted.
