# MEASURED-286: what `check-u9-http-amputation.sh` actually selects, and whether it covers

Task #286. Measured 2026-09-02 on a detached worktree `/tmp/wu9` at
`82ca84be32d6f09ccfeac3e7c9b9fc4311bf6b37` (main's HEAD, from `git rev-parse main`,
not typed from a brief). Box: WSL2, 8 CPUs. Runnable artefact:
`docs/reviews/probe-286-u9-coverage.sh`, committed beside this file. Raw logs of both
runs quoted below are reproducible by running it.

**THE ANSWER IN ONE LINE.** `check-u9-http-amputation.sh` **does** select per row, from
a coverage map its own baseline builds; **possibility 1 holds** - `PROFILE-240` describes
a tree that stopped existing at `50b006d`. Selection is **verdict-preserving on all 14
rows, measured both ways**. It is **not** verdict-preserving on the *killer count*: row
**A14 loses 4 of its 5 killers**, because they run the amputated lines in a **child
process** the in-process coverage map cannot see. That is a reporting defect with a
one-directional failure mode, not a weakened gate - the detail is in §4.

---

## 1. What the harness actually does

`scripts/check-u9-http-amputation.sh:105-106` runs the baseline **on the full `tests`
suite** with `--cov --cov-context=test`, writing a coverage database into a `mktemp -d`
that lives for exactly this run. Each row then calls, at `:143-152`:

```
sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
  python3 scripts/lib/select-covering-tests.py "$file")
```

and passes `$sel` - a space-separated node-id list - to pytest at `:197`, in place of
`$SUITE`. The selector (`scripts/lib/select-covering-tests.py:68-98`) locates the anchor
in the **pristine** file, converts it to a line range, and reads `DISTINCT c.context`
from the `arc` table for arcs whose `fromno` or `tono` falls in that range.

So the selector is **a coverage map, not a static list and not a heuristic**, and the
map is rebuilt by the same run against the same tree - it cannot be stale by
construction. Three failure directions are already deliberate and correct:

| selector rc | harness does | at |
| --- | --- | --- |
| 0 | runs the selected node ids | `:143` |
| 4 (no in-process coverage) | falls back to the **full `$SUITE`** | `:146-149` |
| anything else | **aborts the harness**, exit 3 | `:150-151` |

`check-u3-audit-amputation.sh` does **not** select: its rows run bare `$SUITE` at `:162`.
Only `check-u9-http-amputation.sh` and `check-u4-client-amputation.sh` reference
`select-covering-tests.py` among the amputation harnesses.

## 2. The per-row counts I measured

`bash scripts/check-u9-http-amputation.sh`, one clean run, exit 0,
`HARNESS-RESULT name=check-u9-http-amputation.sh rows=14 floor=0 applied=14/14 status=ok`,
`git status --porcelain -- src tests` **0 rows** afterwards.

```
BASELINE   889 passed, 6 deselected in 79.42s   -> 895 collected
```

| row | tests run | failed | passed | seconds |
| --- | ---: | ---: | ---: | ---: |
| A1 token verifier never built | 132 | 13 | 119 | 6.42 |
| A2 fail-closed check deleted | 22 | 1 | 21 | 3.95 |
| A3 client id not derived | 21 | 2 | 19 | 4.26 |
| A4 `require_scopes` never applied | 16 | 3 | 13 | 3.38 |
| A5 stdio guard deleted | 124 | 91 | 33 | 5.61 |
| A6 totality check deleted | 1 | 1 | 0 | 1.18 |
| A7 stack empty | 125 | 11 | 114 | 5.26 |
| A8 logging middleware dropped | 125 | 4 | 121 | 5.12 |
| A9 timing middleware dropped | 125 | 3 | 122 | 5.24 |
| A10 rate limiter dropped | 125 | 4 | 121 | 5.37 |
| A11 inbound header never read | 111 | 2 | 109 | 5.34 |
| A12 resolved id never bound | 111 | 6 | 105 | 5.53 |
| A13 guard lists never set | 8 | 1 | 7 | 1.86 |
| A14 host and port ignored | 8 | 1 | 7 | 1.74 |

**The relayed CI figures in the brief are CORRECT.** Baseline **895** is
`889 passed + 6 deselected`; rows **132 / 22 / 21 / 16** are exactly A1 / A2 / A3 / A4.
Nothing in that part of the brief needed re-deriving. Baseline **79.42s** against
**60.26s** of rows also reproduces #251's 82.79s / 60.93s split.

## 3. The coverage verdict, per row - measured, not argued

The count cannot settle this, so `probe-286-u9-coverage.sh` runs **every** row twice
against the amputated tree - once on the selected ids, once on the whole `tests` suite -
and prints the **set difference of the two `FAILED` lists**. A FULL-only killer is an
assertion that catches the amputation and that selection drops.

```
BASELINE   889 passed, 6 deselected in 87.33s

row   selected   SEL killers   FULL killers   FULL-only
A1     132/895        13            13           NONE
A2      22/895         1             1           NONE
A3      21/895         2             2           NONE
A4      16/895         3             3           NONE
A5     124/895        91            91           NONE
A6       1/895         1             1           NONE
A7     125/895        11            11           NONE
A8     125/895         4             4           NONE
A9     125/895         3             3           NONE
A10    125/895         4             4           NONE
A11    111/895         2             2           NONE
A12    111/895         6             6           NONE
A13      8/895         1             1           NONE
A14      8/895         1             5           *** 4 ***
```

`rc=1` on both arms of all 14 rows. **The verdict - "did anything go red" - is preserved
on 14 of 14.** The killer set is identical on 13 of 14.

The reverse difference (a killer the SELECTED arm found and the FULL suite did not) is
empty on every row, as it must be: the selected ids are a subset of the suite, so the
probe asserts it rather than assuming it.

**A small selected set is not the same as a weak one.** A6 selects **one** test out of
895 and that one test is the whole covering set of `if frozenset(TOOL_SCOPES) !=
KNOWN_TOOLS:` - the full suite finds no other killer. A13 selects 8 and loses nothing.
Count is not the discriminator; coverage is, and it was measured.

## 4. THE ONE FINDING: row A14, and what the map is blind to

```
########## A14 the host and port are ignored and the defaults are served
  selected ids: 8 of 895
  ARM SEL   rc=1   killers=1   1 failed, 7 passed in 2.03s
  ARM FULL  rc=1   killers=5   5 failed, 884 passed, 6 deselected in 166.56s
  FULL-only killers: 4 - SELECTION DROPS THESE:
    tests/test_boot.py::test_off_loopback_with_the_assertion_declared_starts
    tests/test_boot.py::test_the_default_loopback_bind_starts_a_real_process
    tests/test_shutdown.py::test_a_clean_stop_still_reports_zero
    tests/test_shutdown.py::test_a_crashing_mcp_run_exits_70_read_from_the_process
```

The probe was run twice - once on the four smallest selected sets, once on all 14 rows -
and produced the **identical four-name list** both times (170.24s and 166.56s on the
FULL arm).

All four go through `spawn_marker_server` (`tests/test_boot.py:83`, `:112`, `:255`;
`tests/test_shutdown.py:71`, `:153`, `:407`), which starts a **real child process**.
Those four tests *do* execute the amputated `"host": settings.mcp_host` lines - in a
child the parent's `--cov-context` map never sees. So the selector's central premise,
stated at `scripts/lib/select-covering-tests.py:9-11`:

> A test that never EXECUTES the mutated statements cannot go red because of them

is true, but the map does not answer the question it is being asked. The map answers
"which test executed these lines **in this process**", and the harness reads that as
"which test executed these lines". For a subprocess-driving test the two differ, and
A14 is the measured instance.

**Why this is not a weakened gate.** The selected ids are a strict subset of `$SUITE`,
so a red under selection is a red under the suite. Selection can therefore only turn a
real kill into a **FALSE VACUOUS ROW** - and the harness's gate reports exactly that,
loudly, at `:377-380` (`GATE: N row(s) deleted a behaviour and nothing went red`, exit 1).
It cannot turn a genuinely vacuous row into a false kill. The failure direction is
towards a false alarm the reader must then explain, never towards a silent green. A14
is not at that boundary today: it retains
`tests/test_http_hardening.py::test_the_host_and_port_are_honoured` inside the covering
set, which is why the row still kills.

**What IS wrong, and is a finding rather than a fix I made silently:**

- **F1 (Medium).** The `killed by: N test(s)` line (`:240`) and
  `TOTAL KILLING ASSERTIONS ACROSS ALL ROWS` (`:372`) are counts **within the selected
  set**, printed with no marker saying so. This run reported **143**; the full-suite
  answer for the same 14 rows is **147**. A number that is 97% of the truth and reads as
  100% of it is the shape this project keeps finding. *Fix (not applied - it changes a
  published tally and #251/#268 quote these figures):* rename the line to
  `killed by (within the selected set): N`, and either drop the cross-row total or
  compute it only on rows that fell back to the full suite.
- **F2 (Medium).** `check-u9-http-amputation.sh:15-25` claims the covering set "gives
  the identical verdict to a full-suite run". The **verdict** claim is now measured true
  (14/14). The surrounding prose implies the killer set is identical too, and A14 refutes
  that. *Fixed in this commit*, in place: the comment now names the child-process blind
  spot and scopes the identity claim to the verdict.
- **F3 (Low).** The `rc=4` full-suite fallback fires only on **zero** in-process
  coverage. A row with *some* in-process coverage and a subprocess-only killer gets no
  fallback - A14's exact shape. *Fix (not applied, needs its own task):* declare the
  subprocess-driving test files once and union them into every selected set for a
  harness whose subject is reachable from a spawned server. That is cheap for U9
  (`tests/test_boot.py` and `tests/test_shutdown.py` are 2 files) and it restores
  killer-set identity without giving up the 13x.

**U9's row floors and its VACUOUS accounting do NOT need re-deriving.** The harness
declares `ROW_FLOOR` 0 (`:366`, with the reason at `:363-365`), `VACUOUS` is computed
from each row's exit code (`:223`) and not from a killer count, and this run measured
`VACUOUS ROWS: 0` under selection with all 14 rows red under the full suite too. The
figure that is affected is `TOTAL_SURVIVORS`, which is F1.

## 5. Which document was wrong, and what I corrected

- **`PROFILE-240-harness-cost.md` was stale, and it is the only one.** It is the report
  that *proposed* per-row selection; the proposal landed at `50b006d` fifteen minutes
  before the report was committed, so the report describes base `4bc96a4`. Its §"The
  suggested fix" block quotes `check-u9-http-amputation.sh:15-20` as saying "THE WHOLE
  SUITE IS RUN FOR EACH ROW"; those lines now say the opposite. **Corrected in place:**
  the section heading is pinned to `4bc96a4`, the quote is marked as the pre-`50b006d`
  text, a banner says the proposal landed, and the "What I did NOT verify" bullet about
  rows A2-A14 - which correctly said the author could not construct a test outside the
  covering set - now points at A14, which is that construction.

- **`MEASURED-268-u3-shard.md` was NOT wrong about U9, and the brief's premise here is
  incorrect.** Its only full-`$SUITE` claim is about `check-u3-audit-amputation.sh`, and
  that harness genuinely runs bare `$SUITE` at HEAD. It never says U9's rows run the full
  suite; its U9 material is timing, and its §"unverified" note already flags #251's
  82.79s/60.93s split - which is selection-consistent and which §2 above reproduces.
  Two real but smaller defects **corrected in place**: two dangling line citations
  (`check-u3-audit-amputation.sh:56` -> `:162`, and the `^PASSED` extraction at `:166`
  -> `:196`, both already wrong when written), and §1's blanket "per-row selection was
  refused" - which is true of U3's **survivor-list** product and false as a statement
  about amputation harnesses generally, since its sibling U9 reports a **killer list**
  and has selected since `50b006d`.

- **The harness itself** needed the F2 correction above and got it.

## 6. What I did NOT verify

- **`check-u4-client-amputation.sh`**, the other coverage-map selector. Same mechanism,
  different subject; I ran neither arm of it. Its rows could carry A14's shape and this
  report says nothing about them.
- **The three non-coverage selectors** named in `50b006d` (`check-u0-test-controls`,
  `check-u1-boot-amputation`, `check-u4-client-controls`). They select by other
  mechanisms and are outside this task.
- **CI's own logs.** I re-derived the brief's relayed figures by running the harness
  locally rather than by opening the three green runs. They agree, which is the check,
  but I did not read the runs.
- **Whether A14's four subprocess killers are stable.** They were found on two separate
  full-suite runs of that row in this session. Two draws on one box is not a flake
  study, and `test_shutdown.py:117` documents a ~50% detection rate for a neighbouring
  spawn-and-signal case.
- **The 147 cross-row killer total.** It is the sum of the FULL arms in §3 and is
  therefore measured, but it was assembled by me from the probe output rather than
  printed by an instrument.
