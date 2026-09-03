# MEASURED: three defects in the two unguarded amputation harnesses

2026-09-02. Branch `fix/u15-u1boot-three`, based on `fix/254-r3-findings`
(`707b56c`). Subjects: `scripts/check-u15-gate-amputation.sh`,
`scripts/check-u1-boot-amputation.sh`, and the
`PASSED_VERDICT_WITHOUT_GUARD` ratchet in
`docs/reviews/check-checkers-are-wired.py`.

Three defects, one commit, because they live in the same two files and
fixing them one at a time is how a merge resolution puts damage back.

Every figure below was produced by running the harness, not by reading it.
Two of the three defects were stated wrongly in the brief that dispatched
them; both corrections are recorded here in the section for the defect.

---

## Defect 1 (#280) - a five-name allowlist starved the call one screen below it

`report` runs each row as `timeout -k 30 "$ROW_TIMEOUT" ...`. Row E builds a
directory of symlinks and passes it as the row's ENTIRE `PATH`. The list held
`sh env sed grep cat` and `python3`. It did not hold `timeout`.

BEFORE, whole row, unedited:

    ########## E. git is not on PATH at all
    env: 'timeout': No such file or directory
      survivors: NONE - no assertion passed against this tree

    ########## 5/5 ROWS
    HARNESS-RESULT name=check-u15-gate-amputation.sh rows=5 floor=5 status=ok

harness exit `0`. Row exit code, measured with a `ROW_RC` echo inserted after
the capture: **127**. pytest never launched, so the row produced no `^PASSED `
lines, so the harness printed `survivors: NONE` - its best possible result -
for a row that ran nothing.

AFTER, one word added to the `for tool in ...` list:

    ########## E. git is not on PATH at all
    28 passed, 8 errors in 0.22s

row exit code **1**, and **28 named survivors** where the file had been
reporting none. The eight errors are the `e2e` arms that shell out to git.
The 28 are listed in full in the harness output; their shape is the row's
own stated expectation - *"everything that shells out to git loses its
subject; everything that calls `classify()` in-process does not"* - so they
are the row's CONTEXT rather than 28 fresh findings. What was defective is
that the row published none of them and could not be told apart from a row
that killed everything.

THE BRIEF WAS WRONG ABOUT THE COUNT. It said a prior round had measured
"16 named survivors it has been hiding". The measurement is 28, which is
also what the same sentence's own `28 passed` figure implies. 16 matches no
subset of this row.

## Defect 2 (#283) - a `^PASSED ` verdict parsed with no guard

Both files read their verdict by counting `^PASSED ` lines and handled
exactly one non-measurement exit code, `124`. On rc=2 (collection error),
rc=3 (internal error), rc=4 (usage error) or rc=127 (the binary was not
there) they fell through to the parse, found nothing, and reported
`survivors: NONE` / `every declared assertion died`.

Measured per row on the base tree, again with a `ROW_RC` echo:

| harness  | rows at rc 0/1 | rows NOT at rc 0/1        |
| -------- | -------------- | ------------------------- |
| u15      | B, C, D        | A (rc=2), E (rc=127)      |
| u1-boot  | C D E G H I J K L N LN M | A (rc=4), B (rc=4), F (rc=4) |

Five of the twenty rows across the two files were being scored by an
inference the guard exists to forbid.

Both files now source `scripts/lib/verdict-guard.sh` and call
`verdict_guard` in the order the library mandates - **rc -> restore ->
guard -> verdict**. `u1-boot` has a restore step and the call sits below it;
`u15` builds each row its own tree under `$WORK` and has none, which is
stated at the call site so a later reader does not read the missing restore
as the ordering defect one adopter shipped.

### The rows that are UNCOLLECTABLE BY DESIGN

A naive adoption refuses u15's row A and u1-boot's rows A and B, which is
wrong: those rows delete or empty the module the suite imports at module
scope, so a collection error IS the death they are testing for. They now
DECLARE the import error they expect, as a `grep -E` pattern, immediately
before the `report` call:

    u15    A   FileNotFoundError.*check-committed-file-types\.py
    u1-boot A  No module named 'fast_mcp_jobvite\.config'
    u1-boot B  cannot import name '[A-Za-z_]+' from 'fast_mcp_jobvite\.config'

Rows A and B of u1-boot carry DIFFERENT patterns on purpose: deleting the
file raises `ModuleNotFoundError`, emptying it raises `ImportError`, and one
pattern covering both would let either row pass on the other's evidence.

The declaration is not a bare rc test. A broken amputation that writes
invalid Python also exits 2 or 4, and it prints something else - so it is
still refused. That is the discrimination `--continue-on-collection-errors`
would have destroyed, which is why that one-flag alternative was rejected.

The ten-line block is duplicated at the single call site in each file rather
than added to `scripts/lib/verdict-guard.sh`, because
`check-checkers-are-wired.py` derives "is this script guarded" from the
function names that library defines: a second name there would let a script
that calls only the weaker one count as guarded.

### Both arms, per file

Each arm is a throwaway copy of the real harness with ONE planted
non-measurement exit. All six exited **5** and printed a refusal.

| arm                                                    | rc  | result |
| ------------------------------------------------------ | --- | ------ |
| u15, defect 1 reintroduced with the guard present       | 127 | `REFUSING: pytest exited 127, which is not a measurement.` exit 5 |
| u15, row C's amputation writes a `SyntaxError`          | 2   | `REFUSING: pytest exited 2 ...` exit 5 |
| u15, row A declares a pattern pytest never prints       | 2   | `REFUSING: this row DECLARED an uncollectable suite ... and did not get it` exit 5 |
| u1-boot, row C's amputation writes a `SyntaxError`      | 2   | `REFUSING: pytest exited 2 ...` exit 5 |
| u1-boot, row C made uncollectable with nothing declared | 4   | `REFUSING: pytest exited 4 ...` exit 5 |
| u1-boot, row A declares a pattern pytest never prints   | 4   | `REFUSING: this row DECLARED an uncollectable suite ...` exit 5 |

The first row of that table is the load-bearing one: it is defect 1's exact
symptom, and defect 2's guard catches it independently. The last two are the
positive control on the declaration itself - a declared row that stops being
uncollectable, or becomes uncollectable for a different reason, fails.

`git status --porcelain -- src tests` was 0 rows after every arm.

Normal runs are unchanged. Diffing the before and after output over u15 rows
B, C and D, and over u1-boot rows C through M, the ONLY differences are the
wall-clock seconds in each pytest summary line and row F, which is defect 3
below. Every count, every survivor list and every
`every declared assertion died (n of n)` line is identical. Both harnesses
exit 0.

## Defect 3 (#254 H3) - row F exited 4, and the stated reason was not the real one

Row F empties `KNOWN_TOOLS` and declared two ids. It exited **4** and printed
`every declared assertion died (2 of 2)` for a run that collected nothing
from one of the two files.

THE BRIEF'S DIAGNOSIS IS REFUTED, and so is the one in the ratchet entry
this commit deletes. Both say the amputation "stops the parametrised node id
from resolving". Neither declared id is parametrised, and no node id fails to
resolve. What actually happens, measured by running row F's amputation by
hand:

    tests/test_boot.py:21: in <module>
        from fast_mcp_jobvite.__main__ import EXIT_CONFIGURATION_REFUSED
    src/fast_mcp_jobvite/__main__.py:362: in <module>
        from fast_mcp_jobvite.http_hardening import http_run_kwargs
    src/fast_mcp_jobvite/http_hardening.py:128: in <module>
        _assert_total()
    E   RuntimeError: TOOL_SCOPES must cover exactly KNOWN_TOOLS;
        unscoped=[] unknown=['create_candidate', ...]

`http_hardening` asserts at IMPORT TIME that `TOOL_SCOPES` covers
`KNOWN_TOOLS`. An empty allow-list violates that invariant, so importing
`__main__` raises and `tests/test_boot.py` cannot be collected. The config
arm collects fine - `collected 1 item / 1 error` - but pytest bails during
collection, so it never runs either.

The brief also cited the false reasoning as a comment at `:142-143` of
`check-u1-boot-amputation.sh`. There is no such comment: `git grep -n
"module under test" 707b56c` and `git grep -n "designed amputation"
707b56c` both return nothing, and `:142-143` on the base is the `#238`
per-row test selection note, which is true. There was no false comment to
fix; there was a missing one, and it is now written above `MUST_F`.

REMEDY: the row is restated, not repaired. The boot arm is removed from
`MUST_F` because this row cannot measure it - it can neither survive nor die
in a module that does not collect - and the row's real subject, the
config-level allow-list, is what is left. Measured with the boot id alone
removed:

    BEFORE   ########## F. KNOWN_TOOLS is EMPTY
             1 error in 0.79s          rc=4
             every declared assertion died (2 of 2)

    AFTER    ########## F. KNOWN_TOOLS is EMPTY
             1 failed in 0.10s         rc=1
             every declared assertion died (1 of 1)

and the config arm now genuinely runs and dies on the
`ConfigurationError: JOBVITE_TOOLS names an unrecognised tool 'search_jobs'`
the empty allow-list produces.

The alternative - keeping both ids and declaring row F
`EXPECT_UNCOLLECTABLE` - was rejected on the measurement: with the boot id
present pytest bails during collection and the config arm is never executed
at all, so that shape trades the one arm this row CAN measure for an
assertion about an import-time invariant that is not this row's subject.

## The ratchet

`docs/reviews/check-checkers-are-wired.py`, run and self-tested on both
sides.

|                            | base `707b56c` | after |
| -------------------------- | -------------- | ----- |
| Members                    | 150            | 150   |
| WIRED                      | 75             | 75    |
| UNWIRED, with a reason     | 75             | 75    |
| unexplained                | 0              | 0     |
| `^PASSED `-without-guard   | 2 KNOWN AND OPEN | **0** |
| exit                       | 0              | 0     |
| `--self-test`              | 57/57          | 53/53 |

No member moved WIRED -> EXEMPT: both counts are unchanged and the
membership is the same 150 files. The self-test total drops by 4 because it
is computed as `... + 2 * len(PASSED_VERDICT_WITHOUT_GUARD)` and the dict
went from two entries to none; every control that still exists passed.

With the two entries still present and the harnesses fixed, the checker
reported them as stale - `2 ratchet entry(s) no longer name a violation` -
which is that gate working as designed and the reason both entries had to go
in this commit.

THE ARM DID NOT SIMPLY GO QUIET. A planted `scripts/zz-plant-unguarded.sh`
holding a bare `grep -E '^PASSED '` and no guard was staged, and the checker
named it and exited 1:

    1 script(s) infer a verdict from `^PASSED ` lines
    without calling the guard, and are not on the ratchet:
      scripts/zz-plant-unguarded.sh

The plant was then removed. Zero violations with the plant absent, one
violation named with it present.

The `UNWIRED_BY_DECISION` reason for `verdict-guard.sh` was rewritten in
place rather than appended to: it said the two harnesses "are NOT fixed on
this branch" and "are on the `PASSED_VERDICT_WITHOUT_GUARD` ratchet below",
and it named `thirteen` adopters. All three are now false. The adopter count
is FIFTEEN, derived rather than typed: `grep -l "lib/verdict-guard.sh"
scripts/*.sh | wc -l`.

## Everything else that was run

    bash -n scripts/check-u15-gate-amputation.sh                    OK
    bash -n scripts/check-u1-boot-amputation.sh                     OK
    shellcheck -x -P docs/reviews:scripts --severity=warning ...    exit 0
    docs/reviews/check-row-floor-exactness.py                       35/35, OK
    docs/reviews/check-row-floors.py                                33 harnesses, 0 unfloored
    scripts/check-harness-anchors.py                                464 anchors resolve
    scripts/check-timeout-literals.py                               0 retyped figures
    docs/reviews/check-harness-result.sh                            31/31, 38/38

Neither harness's row count moved: u15 prints `5/5 ROWS` and u1-boot
`rows=15`, so no floor needed changing and the exactness gate stays equal.

    HARNESS-RESULT name=check-u15-gate-amputation.sh rows=5 floor=5 status=ok
    HARNESS-RESULT name=check-u1-boot-amputation.sh rows=15 floor=0 status=ok

`git status --porcelain -- src tests` was 0 rows after each.
