# PROFILE-240: where the harness minutes actually go

Task #240, for #238 (`blackthorn-revamp`). Measured 2026-09-02 on branch
`measure/240-harness-profile`, worktree `/tmp/w240-harness-profile`, base
`4bc96a4` (main's HEAD, derived with `git rev-parse main`, not typed from a brief).

Box: 8 CPUs, load 1.2-2.1 at start. **This is a local box, not a GitHub runner.**
Ratios transfer; absolute seconds do not. The one CI datum used for calibration is
`#154`'s green run, which recorded the U9 amputation step at **1270s**.

**THE HEADLINE, IN ONE LINE.** Test EXECUTION is **96.7%** of a harness row.
Collection is 3.2%, interpreter/subprocess spawn is 0.16%, and the mutate/restore
file-and-git work is **0.04%**. So of `#238`'s four levers, **only per-mutation test
selection can pay**, and it pays: the covering set for the pole harness's subject is
**156 of 888 tests**, a selected row is **10s against 76s**, and the amputation still
goes red on the selected set - measured, both arms, not modelled.

---

## The runnable artefacts

Prose about a measurement decays into a claim about one. Everything below comes from
these three, committed beside this file:

| script | what it produces |
| --- | --- |
| `scripts/profile-harness-phases.sh` | the per-phase table in §1 |
| `scripts/coverage-test-map.py` | the file -> covering-tests map in §2 |
| `scripts/probe-240-selected-row.sh` | the two-armed selection proof in §3 |

Reproduce §1 and §3 directly. §2 needs its coverage data first:

```bash
COVERAGE_FILE=/tmp/prof240/.coverage-ctx PYTHONDONTWRITEBYTECODE=1 \
  uv run --frozen pytest tests -q -p no:cacheprovider \
    --cov=src/fast_mcp_jobvite --cov-context=test --cov-report=
python3 scripts/coverage-test-map.py --data /tmp/prof240/.coverage-ctx \
    --total 888 --harnesses --phases run
```

---

## 1. Per-phase breakdown of a harness row

### Method, stated

Every amputation row is the same shape:

```
cp file backup ; python3 anchor-replace ; uv run --frozen pytest tests ; cp backup file ; cmp
```

so `T_row = T_mutate/restore + T_pytest`, and `T_pytest` splits into spawn,
collection and execution. Each term is **measured directly**, never subtracted from a
model:

| term | command timed | what it contains |
| --- | --- | --- |
| `spawn_bare` | `uv run --frozen python -c pass` | uv lock resolution + venv activation + bare CPython start |
| `spawn_pytest` | `uv run --frozen pytest --version` | the above + pytest and plugin import |
| `collect_only` | `uv run --frozen pytest tests -q -p no:cacheprovider --collect-only` | the above + conftest import + test-module import + item construction |
| `full_suite` | `uv run --frozen pytest tests -q -p no:cacheprovider` | the exact command a row runs (minus `-rf`, which only formats a report) |
| `mutate_restore` | the harness's own `cp` + anchor-replace + `cmp` + `cp` back, replayed on a copy of the subject | the file and git work |

Each is run 4 times; the **first is discarded as warm-up** so filesystem cache state is
identical for every reported sample, and the **median** of the remaining 3 is reported
with min and max. `PYTHONDONTWRITEBYTECODE=1` throughout, as the harnesses set.

Derived phases are differences of measured wholes, and are labelled as derived:
`collect_proper = collect_only - spawn_pytest`, `exec = full_suite - collect_only`.

### The pole: `check-u9-http-amputation.sh` (14 rows + 1 baseline, full suite each)

Raw output, `scripts/profile-harness-phases.sh`, `REPS=3`. **The profiler was run
TWICE and BOTH runs are printed**, because the second came in 23% faster on the same
box at the same commit and a single wall-clock run would have hidden that:

```
run 1  load 2.06 1.49 1.27   02:49:03-05:00   (before the pytest bound was added)
PHASE spawn_bare     median_ms=33    min_ms=31    max_ms=33    n=3
PHASE spawn_pytest   median_ms=122   min_ms=122   max_ms=123   n=3
PHASE collect_only   median_ms=2535  min_ms=2521  max_ms=2608  n=3
PHASE full_suite     median_ms=75852 min_ms=75673 max_ms=75873 n=3
PHASE mutate_restore median_ms=27    min_ms=26    max_ms=28    n=3

run 2  load 1.90 1.55 1.59   03:12:08-05:00   (the committed script, pytest bounded)
PHASE spawn_bare     median_ms=31    min_ms=31    max_ms=32    n=3
PHASE spawn_pytest   median_ms=76    min_ms=75    max_ms=77    n=3
PHASE collect_only   median_ms=1823  min_ms=1726  max_ms=1834  n=3
PHASE full_suite     median_ms=58308 min_ms=57472 max_ms=58473 n=3
PHASE mutate_restore median_ms=27    min_ms=26    max_ms=28    n=3
```

**The absolute seconds moved and the SHARES did not**, which is the thing the report
turns on. Run 1's numbers are used as the headline because they are the pessimistic
pair and they are the closer of the two to CI's own per-run figure (1,270s / 15 runs =
84.7s). The `timeout` wrapper added in run 2 is required by
`scripts/check-pytest-bounded.sh` and cannot explain a run getting *faster*; the
difference is box noise, and it is reported rather than averaged away.

**One U9 amputation row:**

| phase | run 1 ms | run 1 % | run 2 ms | run 2 % | measured or derived |
| --- | ---: | ---: | ---: | ---: | --- |
| mutate + restore (cp, anchor replace, cmp, cp back) | 27 | 0.04% | 27 | 0.05% | measured |
| uv + interpreter spawn | 33 | 0.04% | 31 | 0.05% | measured (`spawn_bare`) |
| pytest + plugin import | 89 | 0.12% | 45 | 0.08% | derived (`spawn_pytest - spawn_bare`) |
| collection (conftest + 888 items) | 2,413 | 3.18% | 1,747 | 2.99% | derived (`collect_only - spawn_pytest`) |
| **test execution** | **73,317** | **96.62%** | **56,485** | **96.82%** | derived (`full_suite - collect_only`) |
| **row total** | **75,879** | 100% | **58,335** | 100% | |

**Whole harness:** 1 baseline + 14 rows = 15 full-suite runs = **1,138s / 19.0 min**
locally at run 1's rate, 875s / 14.6 min at run 2's. CI recorded 1,270s for the same
step (`#154`), a 1.12x factor over run 1 - which is the sanity check that this local
profile is measuring the same thing CI is.

### The contrast: `check-u9-http-controls.sh` - same file, same mutations, selected tests

The controls sibling mutates the **same** `http_hardening.py` with the **same**
`cp`/anchor-replace/`cmp` mechanics, and differs in exactly one respect: each row runs
**one node id** (`tests/test_http_hardening.py::test_...`) instead of `tests`. It also
runs a `--collect-only` probe first, to catch a selector that no longer resolves.

Timed three times on `::test_the_rate_limiter_has_a_get_client_id`, warm-up discarded:

```
collect_probe_ms=1055  row_run_ms=1189
collect_probe_ms=1091  row_run_ms=1068
```

| | U9 amputation row | U9 controls row |
| --- | ---: | ---: |
| selector probe (`--collect-only`) | - | 1,055 ms |
| row run | 75,852 ms | 1,120 ms |
| mutate + restore | 27 ms | 27 ms |
| **row total** | **75,879 ms** | **2,202 ms** |

**34x, from one difference: what is passed to pytest.** Note what the cheap row's
profile looks like: of its 1,120 ms run, ~933 ms is collection and ~65 ms is execution.
At a single test the two harnesses are *inverted* - the cheap one is 95% overhead. That
is why "collection reuse" reads as attractive from the cheap end and is worth almost
nothing at the pole.

---

## 2. The coverage-derived map: source file -> the tests that cover it

### Method, stated

`pytest --cov-context=test` makes coverage.py record, per measured line/arc, **which
test was running when it executed**. This is a dynamic per-test record: a test that
imports a module but never runs a line in it does not appear. `coverage-test-map.py`
reads the resulting SQLite directly and takes the distinct node ids per file.

Run: `888 passed, 6 deselected in 81.60s`, 0 skipped, coverage 97.01%.

**Two instrument failures were caught and are reported because they are the shape the
brief warned about.**

1. **A clean zero.** The first version read `line_bits` and got **0 rows**, which would
   have printed "no test covers any file" with a plausible story attached. The project
   runs `branch = true`, so coverage.py writes `arc` and leaves `line_bits` empty. The
   join key was wrong, not the codebase. The script now reads both and prints
   `line_bits=0 arc=3974` so the next reader can see which one carried the data.
2. **A clean 888.** With all phases folded in, `services/jobvite_client.py` came out at
   **exactly 888 of 888** - the other suspicious number. It is real but it is not
   coverage of behaviour: `tests/conftest.py`'s autouse fixture calls the module's
   `reset_breaker()`, so every test touches that file in `setup` **and** `teardown`
   through **exactly 3 arcs of one 2-line helper** (minimum arcs per test = 6 = 3 x 2
   phases). Restricted to the `run` phase the same file measures **174 (19.6%)**.
   Both views are printed; **the `run`-phase view is the one below**, because a
   selection lever must not be sized on fixture traffic.

### Per source file (run phase, of 888)

```
covering tests  % of suite  source file
           305      34.3%   src/fast_mcp_jobvite/utils/redaction.py
           208      23.4%   src/fast_mcp_jobvite/__main__.py
           197      22.2%   src/fast_mcp_jobvite/config.py
           190      21.4%   src/fast_mcp_jobvite/utils/constraints.py
           174      19.6%   src/fast_mcp_jobvite/services/jobvite_client.py
           164      18.5%   src/fast_mcp_jobvite/audit.py
           156      17.6%   src/fast_mcp_jobvite/http_hardening.py
           148      16.7%   src/fast_mcp_jobvite/utils/correlation.py
           126      14.2%   src/fast_mcp_jobvite/tools/candidates.py
           126      14.2%   src/fast_mcp_jobvite/tools/jobs.py
           118      13.3%   src/fast_mcp_jobvite/server.py
            97      10.9%   src/fast_mcp_jobvite/errors.py
            53       6.0%   src/fast_mcp_jobvite/approval.py
            53       6.0%   src/fast_mcp_jobvite/utils/normalise.py
            16       1.8%   src/fast_mcp_jobvite/models/job_feed.py
            16       1.8%   src/fast_mcp_jobvite/models/jobs.py
            10       1.1%   src/fast_mcp_jobvite/models/fencing.py
             8       0.9%   src/fast_mcp_jobvite/models/candidate.py
```

### Per harness (union over the subject files it names, run phase)

Subjects are derived from **each harness's own source** (`^[A-Z_]+="src/..."`), the same
derivation `ci-harness-gate.sh` uses for its vocabulary, so a harness that changes
subject cannot leave a stale row here.

```
  union  % of suite  harness
    346      39.0%   check-u8-candidates-{amputation,controls}.sh
    345      38.9%   check-u12-jobfeed-{amputation,controls}.sh
    341      38.4%   check-u3-audit-{amputation,controls}.sh
    311      35.0%   check-log-redaction-amputation.sh
    305      34.3%   check-u1-boot-{amputation,controls}.sh
    249      28.0%   check-u14-arguments-amputation.sh
    239      26.9%   check-u14-arguments-controls.sh
    238      26.8%   check-u5-jobs-{amputation,controls}.sh
    229      25.8%   check-u10-write-{amputation,controls}.sh
    174      19.6%   check-u4-client / u6-paging / u7-resilience {amputation,controls}.sh
    159      17.9%   check-critical-coverage-amputation.sh
    156      17.6%   check-body-cap-{amputation,controls}.sh
    156      17.6%   check-u9-http-{amputation,controls}.sh
```

**The answer to the question that decides it: no covering set is anywhere near 888.**
The worst is 346 (39%), the pole is 156 (17.6%). **Lever 1 is alive.**

The union is the honest number for a harness, not the per-file one: a harness mutates
one file per row, but several of its rows sit on different files, and the union is what
a per-harness selection would have to run. A per-**row** selection could go lower still
(U9 would not change - one subject - but U8 would drop from 346 towards 126).

---

## 3. Does the covering set actually HOLD a row? Two arms, measured

A map is a claim about coverage, not about the harness. `probe-240-selected-row.sh`
replays **U9 row A1** - the amputation that disables every bearer-token check on the
HTTP transport - against the 156 selected tests:

```
SELECTED 156 node ids covering src/fast_mcp_jobvite/http_hardening.py (run phase)
ARM1 intact     rc=0  seconds=10  156 passed in 8.86s
AMPUTATION APPLIED (U9 row A1)
ARM2 amputated  rc=1  seconds=9   13 failed, 143 passed in 8.83s
FAILED tests/test_http_hardening.py::test_a_drained_client_is_locked_out_at_initialize_not_degraded
FAILED tests/test_http_hardening.py::test_a_malformed_inbound_request_id_is_replaced[not-a-uuid]
FAILED tests/test_http_hardening.py::test_a_malformed_inbound_request_id_is_replaced[over-long]
FAILED tests/test_http_hardening.py::test_a_valid_inbound_request_id_is_the_one_stamped_into_meta
RESTORED (cmp clean)
VERDICT: the covering set HOLDS U9 row A1 - selection preserves the verdict.
```

ARM 1 is a real negative control, not decoration: without it a red in ARM 2 could be a
broken selection rather than a caught amputation. The probe refuses if fewer than 2 ids
are selected, restores from a pristine copy in an EXIT trap, proves the restore with
`cmp`, and prints `git status --porcelain` for the reader.

**A selected row is 10s against 76s - 7.6x.** Note it is not 5.7x (888/156): the
selected tests are *cheaper than average* as well as fewer, so a linear projection from
test counts **understates** the saving. That also means it cannot be trusted in the
other direction, which is why §4 marks its numbers as projections.

---

## 4. What this says about each of #238's four levers

| lever | verdict | evidence |
| --- | --- | --- |
| **1. per-mutation test selection** | **THE ANSWER.** Take it first. | Execution is 96.6% of a row; covering sets are 17.6%-39.0% of 888; a selected row measured 10s vs 76s, with the amputation still caught |
| **2. collection reuse** | Ceiling is **3.2% of a row**. Not worth engineering *at the pole*. | `collect_proper` 2,413 ms of 75,879 ms. It only looks big on already-cheap rows (95% of a 1.1s single-selector run), where the absolute saving is ~1s |
| **3. matrix fan-out** | Still needed, still cannot go below the largest single job - which lever 1 shrinks from 19 min to ~4 min | pole 1,138s local / 1,270s CI, projected ~216s under selection (76s baseline + 14 x 10s) |
| **4. sharding** | Fallback, and now clearly the wrong first move | it buys wall-clock by spending runner minutes on a cost that is 96.6% avoidable rather than avoiding it |

**Sizing the whole matrix (PROJECTION, not a measurement).** 14 amputation harnesses run
the full suite per row - body-cap 5, critical-coverage 20, log-redaction 6, u1-boot 15,
u3 10, u4 17, u5 14, u6 11, u7 22, u8 14, u9 14, u10 10, u12 10, u14 16 = **184 rows**,
plus 14 baselines = **198 full-suite runs**. At the measured 75.85s that is **250 min of
pytest wall** across the matrix. I have measured the selected-row cost for **one** row of
**one** harness; applying U9's 7.6x to the other thirteen is arithmetic, not evidence,
and the report says so rather than printing a number that would be quoted back.

### The suggested fix, and it is already in this tree

Every finding ships a fix. This one needs no new machinery: **the controls harnesses
already implement lever 1.** `check-u9-http-controls.sh` mutates the same file with the
same code and runs a selector, at 2.2s a row. The amputation harnesses run `$SUITE`
instead **by an explicit design decision**, stated in `check-u9-http-amputation.sh:15-20`:

> THE WHOLE SUITE IS RUN FOR EACH ROW, not this unit's file. That is deliberate and it
> is what "does ANYTHING notice" means: an amputation run against only the tests written
> for it answers the mutation question a second time. It also catches the case that
> would be invisible otherwise - a U9 behaviour whose removal breaks somebody ELSE's
> assertion, which is coverage this unit did not know it had.

**A coverage-derived covering set keeps that property; a hand-written selector does not.**
That is the whole point of building the map from coverage instead of from file names:
the 156 for `http_hardening.py` are *whichever* tests execute its lines, from *any* file,
including the somebody-else assertions the comment is protecting. So the substitution to
propose to `blackthorn-revamp` is:

- replace `pytest $SUITE` in each amputation row with `pytest $(covering-set-for $file)`,
  generated by `scripts/coverage-test-map.py` from a coverage run CI already does;
- keep the **baseline** on the full suite - it is one run per harness, it is what proves
  the intact tree is green, and cutting it saves 1/15th while removing the one thing that
  makes the rows interpretable;
- gate the substitution on a **row floor for the selected set**, so a covering set that
  silently empties (a renamed test, a stale map) cannot render as a green row. The
  controls harnesses' `--collect-only` selector probe is the existing precedent, and
  `probe-240-selected-row.sh` refuses below 2 ids for the same reason.

**The map is a derived record and will decay.** It must be regenerated in the same run
that uses it, or a source file that gains a caller keeps its old, smaller covering set
and the row quietly stops testing what it thinks it tests. Do not commit the map.

---

## What I did NOT verify

- **Any harness other than U9, end to end.** §1 and §3 are U9's; the per-file map in §2
  is repo-wide but I ran the two-armed proof on **one row of one harness**. The other 13
  harnesses' covering sets are measured; whether each of their rows still goes red on
  them is not.
- **The other 13 U9 rows.** A1 holds. Rows A2-A14 amputate different behaviours and
  could in principle be held up only by a test outside the covering set - though by
  construction of coverage that would require the amputation to change behaviour on a
  line no covering test executes, which I could not construct.
- **GitHub runner numbers.** Everything here is one 8-CPU local box. The only CI figure
  quoted is `#154`'s 1,270s, read from that task, not re-run by me.
- **`check-suite-floor-amputation.sh` and `check-u15-gate-amputation.sh`** are excluded
  from the 184-row count: their pytest invocations do not match the `$SUITE` form the
  other 14 share, and I did not read them closely enough to say what they run.
- **Whether `ci.yml`'s current step list still runs all 14.** `#235` gated 41 harness
  steps on code changes; a docs-only push runs fewer. I did not open `ci.yml` beyond
  reading step names - it belongs to `blackthorn-revamp`, and I changed nothing in it.
- **The `mutate_restore` figure is a lower bound.** It replays U9 row A3's anchor, the
  shortest real anchor in the harness, on a copy. At 27 ms it is 0.04% of a row, so a 3x
  error in it changes nothing.
- **The 23% spread between the two profiler runs is unexplained.** Same box, same commit, loads within 8% of each other. I did not chase it: both runs put execution above 96.6% and that is the only quantity the report's conclusion rests on. If `blackthorn-revamp` needs an absolute second-count rather than a share, it should be taken from CI, not from here.
- One instrument note, reported rather than buried: `profile-harness-phases.sh`'s own
  "the profiler changed the working tree" guard **fired** on BOTH complete runs. It was
  correct both times and the cause was me - I was editing other files in the worktree
  while it ran, so untracked/modified paths appeared between its two `git status` calls.
  The guard is doing its job; the tree was never mutated by the profiler, and the probe's
  own `cmp`-checked restore is the evidence for the one script that does mutate.
