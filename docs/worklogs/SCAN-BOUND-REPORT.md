# SCAN-BOUND - ADR-0024's bound, re-measured on `5eb64b0` and reviewed line by line

**Agent:** `scan-bound`. **Branch:** `feat/scan-bound`, based at `5eb64b0`. **Task:** #74.
**Written:** 2026-08-29 09:33 AM CDT. **Design read at:** `git show c15b138:docs/DESIGN.md`.

## The short version

ADR-0024's shape on `rescue/adr-0024-scan-bound` is **right and I kept it**: a zero-progress break
plus a ceiling in RECORDS, both feeding `incomplete`, neither reading `total`. What I rewrote is
everything that made a claim: **the probe** (its verdict lines could disagree with its own gate, and
its abort sat on the exact number the fixed behaviour produces), **the ceiling's justification**
(both of its arguments were wrong, and one of them cited machinery that does not exist), and **three
harness row ids that collided with rows `main` added since the rescue was taken**.

Every number below is one I ran, in this worktree, at the SHA named.

---

## 1. What I kept, what I rewrote, and the measurement for each

### KEPT, verified rather than trusted

| Thing | Why kept | How I verified it |
|---|---|---|
| The zero-progress break, and its placement AFTER the short-page exit | It therefore fires only on a FULL page that added nothing, which healthy paging cannot produce | Probe arms A1/A2: 2 requests, 50 records, `incomplete=True`. Positive control `test_neither_bound_fires_on_healthy_paging`: 3 requests, 101 records, `incomplete=False` |
| `progress_before` counting `unidentified` alongside `seen` | An id-less record IS a record the caller receives, so a page of them is progress and must not stall the scan (`DESIGN.md:465-468`) | Read the loop; a page of id-less records grows `items`, so it is bounded by the CEILING, not the break - which is the correct division of labour |
| The ceiling counted in RECORDS, not pages | The ADR's ruling settles it; a page ceiling is a different record count per page size | Probe `RECORDS-NOT-PAGES` row: 100,000 records held at BOTH page sizes; 2,000 requests at 50/page vs 200 at 500/page |
| `incomplete = _check_completeness(...) or stalled or ceiling_hit` | `_check_completeness` is armed only by a short page AND an integer `total`, so it is structurally blind to both new bounds | Amputation A22 deletes the `or` and is killed |
| `incomplete` rather than an exception | Records already collected are real; the budget's answer is a 503 and nothing | Probe's "caller holds" column, which is why that column exists |
| The five new tests and the two fake servers | Both failure directions, and each defeats the other's bound | 31/31 controls fired; the 5 new mutations M28-M32 each killed by a NAMED test |
| Three amputation rows and five control rows | Correct subjects | Ran both harnesses; see §4 |

### REWROTE, with the defect each rewrite fixes

**R1 - `scripts/probe-scan-bounds.py`, the abort had ZERO margin. (would have become a false
`*** UNBOUNDED ***`)**
The rescued file hard-codes `PROBE_ABORT_REQUESTS = 2_000`. Arm B1 issues **exactly 2,000** requests
when the ceiling works (100,000 records at 50 per page). The probe's own abort and the correct answer
sat on the same integer. A ceiling raised by one record, or a page size lowered, and a WORKING bound
prints `*** UNBOUNDED ***`.
*Fix, applied:* derive it - `PROBE_ABORT_REQUESTS = (jc.MAX_SCAN_RECORDS // PAGE_SIZE) * 2`, now
**4,000**. Measured after: B1 still 2,000 requests, and the margin is now a property of the code
rather than of a coincidence.

**R2 - the probe's printed verdict and its exit code were computed in two places.**
`run()` printed `bounded IN THE CLIENT; caller gets N records` for every arm; `check()` separately
asserted the numbers. A human reading the transcript would see four confident "bounded" lines while
`check()` failed on a record count. This is exactly the defect
`docs/reviews/probe-r6-breaker-reset.py` records at `3ef01f5` - it printed `not counted (ok)` beside
a counter that had just moved.
*Fix, applied:* `run()` now records an `Observation` and renders **no verdict**. `judge()` is the
single predicate; the printed VERDICTS block and the process exit code are both derived from its
output. Its rows are `A1 A2 B1 B2 RECORDS-NOT-PAGES`.

**R3 - the probe emitted 236KB of DEBUG around twenty lines that matter.**
One client DEBUG line per request, times ~4,400 requests.
*Fix, applied:* `logger.remove()` at import. Full run is now 40 lines and **0.67s wall clock**.

**R4 - the ceiling's justification made TWO arguments and both are wrong.** This is the one I would
flag hardest if I were reviewing someone else's branch, because it reads as a derivation and is not
one. Verbatim from the rescue:

> It sits above the largest scan the outbound budget could ever complete - at the 6/min figure
> DESIGN.md:1576-1583 records as a GUESS, 100,000 records is 2,000 pages and about five and a half
> hours against a 60-second budget

- **"above the largest scan the outbound budget could complete"** contradicts the ADR the constant
  exists to serve. The budget bounds WALL CLOCK. My own pre-fix run (§2) issued **2,001 requests
  inside a TWO-SECOND budget without it firing once**. The budget does not bound the request count
  at all, so it cannot be what sizes a ceiling.
- **"5.5 hours at 6/min"** sizes the ceiling against `JOBVITE_OUTBOUND_RATE_LIMIT`, whose
  self-throttle **is not implemented**. Task #43 recorded its absence; I re-checked -
  `grep -rn "RATE_LIMIT\|rate_limit\|throttle" --include=*.py src/` returns the INBOUND
  `RateLimitingMiddleware` in `http_hardening.py` and, at
  `src/fast_mcp_jobvite/services/jobvite_client.py:611`, a comment saying `config.py`'s
  `outbound_rate_limit` "is NOT this and cannot be made into it". There is no outbound throttle to
  compute 5.5 hours against.

*Fix, applied:* the comment now states what the number IS sized against and what it COSTS, and names
both wrong arguments so they are not made again:
- sized against the resource - `DESIGN.md:474` records the largest real one as `showing 50 of 1,240`,
  so 100,000 is roughly **eighty times** the biggest scan this project has ever named;
- cost stated at both page sizes the ADR requires: **2,000 requests at 50/page, 200 at 500/page**,
  and **100,000 records in memory in either case**;
- and the honest statement that the ceiling's subject is MEMORY, because the request count on the
  only shape that produces it cheaply is already covered by the break.

**I did not change the value.** 100,000 is a choice, it is labelled one, and I have no measurement
that would justify moving it - which is the reason I rewrote the argument instead.

**R5 - three amputation ids and three control ids COLLIDED with rows `main` added after the rescue
was taken.** The cherry-pick auto-merged clean and produced a file with two `A17`, two `A18`, two
`A19`, two `M23`, two `M24` and two `M25`. Nothing errors; the harness just prints each id twice and
a reader cannot tell which row a verdict belongs to.
*Fix, applied:* renumbered mine to **A20, A21, A22** and **M28, M29, M30, M31, M32**.
Verified: `grep -E '^(amputate|mutate) ' ... | grep -oE '"[AM][0-9]+' | sort | uniq -d` is empty for
both files.

**R6 - stale ADR status in three files.** `ADR-0024, Proposed` in the client constant, the test
section header and the controls harness header; ADR-0024 was Accepted on 2026-08-29. Also the
controls comment on M31 called the record ceiling "what this unit amended", when the ADR's own ruling
made that correction. All rewritten in place, not appended to. Verified:
`grep -rn "ADR-0024" src/ tests/ scripts/ | grep -i proposed` is empty.

**R7 - one added assertion, and it is WEAK by measurement.**
`test_a_fully_duplicate_page_is_still_not_a_short_page` asserted a request count and
`duplicates_dropped`, and never that the scan ended NORMALLY. I added `assert result.incomplete is
False`. **The amputation run then showed that case surviving both A20 and A22**, so the assertion is
not the guard I first wrote it up as, and I rewrote its comment to say so rather than leaving a
comment that overclaimed. It states the other half of the outcome; the request count already kills
the break-fires-always mutation.

---

## 2. My own probe numbers, BEFORE and AFTER

**BEFORE** - the rewritten probe copied into a detached worktree at `5eb64b0`
(`/tmp/scan-bound-before`, since removed), run WITHOUT `--assert` because the unfixed client has no
`MAX_SCAN_RECORDS` for `judge()` to read:

```
A1  budget 60s   page 50    requests issued: 2001   *** UNBOUNDED *** probe aborted
A2  budget  2s   page 50    requests issued: 2001   *** UNBOUNDED *** probe aborted
B1  budget 60s   page 50    requests issued: 2001   *** UNBOUNDED *** probe aborted
B2  budget 60s   page 500   requests issued: 2001   *** UNBOUNDED *** probe aborted
```

Two things the rescued record did not have. **All FOUR arms are unbounded**, not just A1/A2 - the
rescue's commit message quotes only the two non-advancing rows. And the whole four-arm run, 8,004
requests, **completes in under a second**, which is why the two-second budget in A2 never fires. That
is ADR-0024's load-bearing claim, measured on current `main` rather than inherited.

**AFTER**, on this branch, `uv run --frozen python scripts/probe-scan-bounds.py --assert`, exit 0:

```
A1  page 50    budget 60.0s   requests: 2      bound by: client   holds 50 records, incomplete=True
A2  page 50    budget  2.0s   requests: 2      bound by: client   holds 50 records, incomplete=True
B1  page 50    budget 60.0s   requests: 2000   bound by: client   holds 100000, incomplete=True
B2  page 500   budget 60.0s   requests: 200    bound by: client   holds 100000, incomplete=True

A1                 bounded as ADR-0024 requires (ok)
A2                 bounded as ADR-0024 requires (ok)
B1                 bounded as ADR-0024 requires (ok)
B2                 bounded as ADR-0024 requires (ok)
RECORDS-NOT-PAGES  bounded as ADR-0024 requires (ok)
```

**2,001 requests to 2.** And the caller holds records with `incomplete=True` in every arm - not a 503
and nothing, which is what the budget would eventually have handed it.

**The probe GATES**, through `tests/test_resilience.py::test_the_scan_bounds_probe_still_reproduces_its_measurements`,
which runs it with `--assert` and asserts `returncode == 0`. That is the same wiring the repository
already uses for `scripts/probe-breaker-call-path.py` at `tests/test_resilience.py:1612`, so it needs
no new `ci.yml` step.

---

## 3. The ceiling, and its cost at both page sizes

**`MAX_SCAN_RECORDS = 100_000`**, unchanged from the rescue, rejustified (R4).

| | 50 records/page | 500 records/page |
|---|---|---|
| Requests to reach the ceiling | **2,000** | **200** |
| Records held when it fires | **100,000** | **100,000** |
| Records vs `DESIGN.md:474`'s largest named resource (1,240) | ~80x | ~80x |

That table is the ADR's "sane at both 50 and 500 records per page" requirement, discharged: the
column that matters - the resource at risk - is **identical** at both page sizes, and it is the
column a page ceiling would have made differ tenfold. Both halves are asserted by the probe's
`RECORDS-NOT-PAGES` row and by
`test_the_record_ceiling_holds_at_both_50_and_500_per_page`.

**Neither bound substitutes for the other, and it is measured, not asserted.** A non-advancing
server's record count never grows, so the ceiling can never fire on it; an endless server never
repeats a record, so the break can never fire on it. `test_neither_bound_substitutes_for_the_other`
runs both against the SAME ceiling and reads which one stopped it. Its docstring records that its
first arm was written with a ceiling of 1 and FAILED, because page one legitimately adds 50 records -
so the claim is conditional on "a ceiling larger than one page", which every plausible value meets.
I kept that; it is the sort of correction that usually gets deleted.

**The outbound budget is explicitly not the answer here**, and §2's before-numbers are the evidence
rather than the ADR's assertion.

**`total` is never read as a loop condition.** The only additions to the loop's exits are
`len(seen) + unidentified == progress_before` and `len(items) >= MAX_SCAN_RECORDS`. `DESIGN.md:486-487`
is intact.

---

## 4. Gates, all run in this worktree, floors DERIVED

Floors read out of `ci.yml`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 768
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 401
```

| Gate | Result |
|---|---|
| `uv lock --check` | `Resolved 120 packages` |
| `ruff check .` | `All checks passed!` |
| `ruff format --check .` | `71 files already formatted` |
| `mypy` | `Success: no issues found in 58 source files` |
| `pytest` | **`775 passed, 6 deselected in 47.64s`** - **0 skipped**; 6 deselected are the credentialed/network arms excluded by `-m` in `addopts`, as `CONTRIBUTING.md` describes |
| `check-quickstart.py` | exit 0 |
| `check-harness-anchors.py --self-check --floor 401` | `OK: all 409 anchors resolve to exactly one hit in their target file (floor 401)` |
| `check-harness-anchors-controls.sh` | `9/9 controls fired` |
| `check-committed-file-types.py --all` | exit 0 |
| `check_advisories.py` | exit 0 |
| `ci-harness-gate.sh check-u7-resilience-controls.sh --controls-fired` | **`31/31 controls fired.`** |
| `ci-harness-gate.sh check-u7-resilience-amputation.sh --amputation --min-rows 19 --row-re '^########## A[0-9]+ '` | **`ROWS: 22   ANCHORS APPLIED: 22`, `VACUOUS ROWS: 0`, `GATE: every row was noticed by at least one assertion.`** |
| all 8 `design-gates` checkers | exit 0 each |
| `probe-scan-bounds.py --assert` | exit 0 |
| `uv tool run pre-commit@4.6.2 run --all-files` (`ci.yml:848`) | **FAILS - and it fails identically on the base commit. See below.** |

### One gate is RED, it is NOT mine, and it is red on `main` - task #87

`ci.yml:848`'s "Secret scan hook runs clean" step exits 1. I did not cause it. Reproduced with CI's
exact command in a throwaway detached worktree at **`5eb64b0`**, before any of my changes existed:

```
$ uv tool run pre-commit@4.6.2 run --all-files --show-diff-on-failure
secret scan (detect-secrets, staged content).....................................Failed
CI_EXACT_EXIT=1
Secret Type: Secret Keyword   Location: docs/reviews/probe-u12-f2-embedder-leak.py:39
Secret Type: Secret Keyword   Location: docs/reviews/probe-u12-f2-embedder-leak.py:40
Secret Type: Secret Keyword   Location: tests/test_tools_job_feed.py:76
Secret Type: Secret Keyword   Location: tests/test_tools_job_feed.py:78
Secret Type: Secret Keyword   Location: tests/test_tools_job_feed.py:79
```

All five are test and probe literals that already carry `# noqa: S105 - a test literal` for ruff's
version of the same complaint, and `grep -c 'probe-u12-f2-embedder-leak\|test_tools_job_feed'
.secrets.baseline` returns **0** - neither file is in the baseline at all. `git log -1` on them gives
**6e537ea** (U12) and **8516c2f** (ADR-0026's probe), so the step has been red since U12 landed.

**Why nobody saw it, and it is a shape this project already has a memory for.** The hook is named
"detect-secrets, **staged content**". At commit time it scans only what is staged, so it is green on
any commit that does not touch those two files - it was green on mine. Only `--all-files`, which is
what CI runs, reaches them. A hook that is green locally and red in CI is the fastest way to teach
everyone to stop reading the CI step.

**I did not fix it**, and that is a decision rather than an omission: it touches
`tests/test_tools_job_feed.py` and the AUDITED `.secrets.baseline`, both of which three other live
worktrees may be sitting on, and silently regenerating a secrets baseline is how a real finding gets
baselined by accident. Task #87 carries two suggested fixes (per-line `# pragma: allowlist secret`,
preferred, or an audited baseline regeneration) and the positive control either one needs.

**My own commit passed the commit-time hook.** I committed once with `--no-verify` by mistake, then
reset and re-committed with the hooks enabled; `9e74a1a` is the one that went through them.

**The harnesses were run one at a time, under no timeout that could fire**, and the tree was
confirmed restored by `git diff --stat` matching before and after each run.

### The new rows, and their survivors - which are output, not failure

```
########## A20 the zero-progress break is deleted (R5-H2 reopens)   survivors: 39
########## A21 the record ceiling is deleted                        survivors: 38
########## A22 neither bound makes the result incomplete            survivors: 38
```

Each row was noticed. The scan cases that SURVIVE each amputation are exactly the ones that do not
exercise it - `test_the_record_ceiling_holds_at_both_50_and_500_per_page` survives A20, and
`test_a_server_that_ignores_start_is_bounded_after_one_wasted_page` survives A21, which is the
division of labour ADR-0024 predicts. The one survivor I did not expect is R7 above, and I recorded
it against my own assertion rather than around it.

Controls M28-M32 each name a DIFFERENT test, and each killed it:

```
M28 the zero-progress break can never fire            -> test_a_server_that_ignores_start_is_bounded_after_one_wasted_page
M29 progress is sampled after the page                -> test_neither_bound_fires_on_healthy_paging
M30 a stalled scan reports itself as complete         -> test_a_server_that_ignores_start_is_bounded_after_one_wasted_page
M31 the ceiling counts pages instead of records       -> test_the_record_ceiling_holds_at_both_50_and_500_per_page
M32 the record ceiling can never fire                 -> test_a_server_that_never_runs_out_is_bounded_by_the_record_ceiling
```

M29 is the one worth pointing at: it is the OPPOSITE failure from M28 - a break that fires on EVERY
page, healthy ones included - and it is killed by the positive control. A suite carrying only "it
stops" cases would have passed it.

---

## 5. `ci.yml` steps you need (it is yours, not mine)

Two floors, both **branch-local measurements** - re-derive them on `main` after merging rather than
copying these:

```yaml
bash scripts/check-suite-floor.sh 775                              # was 768; +7 tests
python3 scripts/check-harness-anchors.py --self-check --floor 409  # was 401; +8 anchors
```

and one existing step's `--min-rows`, which the three new amputation rows move:

```yaml
bash scripts/ci-harness-gate.sh check-u7-resilience-amputation.sh \
  --amputation --min-rows 22 --row-re '^########## A[0-9]+ '       # was 19
```

**No new step is needed for the probe.** It gates through the suite.
`scripts/ci-harness-gate.sh check-u7-resilience-controls.sh --controls-fired` needs no change - it
reads the harness's own `N/N` line.

**No CHANGELOG entry.** `scan()` still has zero callers, so this is internal-only today and
`changelog-standard.md:94` forbids such an entry. The unit that gives `scan()` its first caller is
the one that makes it user-facing, and that is where the entry belongs.

---

## 6. What I could NOT settle

- **Whether the defect is reachable against real Jobvite. Still open, and I did not close it.** It
  needs an endpoint that ignores `start`; `/v1/jobFeed` is the candidate and no credential exists.
  R5 recorded it unsettled, ADR-0024 repeated it, the ruling repeated it, and I am repeating it. The
  bound is adopted because the client must terminate against a server that misbehaves, not because
  this one is known to. **Everything in §2 is measured against a `MockTransport` fake and says
  nothing whatever about Jobvite's real behaviour.**

- **Whether `incomplete=True` will actually reach an MCP caller.** It is on `ScanResult` and is
  therefore observable, and the brief's requirement is met at that boundary. But **`scan()` still has
  zero callers in `src/`** - I re-ran the ruling's own grep and both hits are still the comments at
  `tools/jobs.py:321` and `:680` saying so. So nothing renders `incomplete` into a tool response
  today, and no test can prove it does. **The first unit to call `scan()` must surface it**; a bound
  that sets a flag nobody reads truncates just as silently as one that sets nothing. That is a real
  gap and it is not mine to close - **raised as task #86** rather than left here.

- **Whether 100,000 is the right number.** I rejustified it and did not move it. Nothing in this
  repository measures a Jobvite resource size, so there is no distribution to pick a percentile from;
  §3's table is a cost statement, not a derivation. It is labelled a choice in the code.

- **Whether 100,000 records is survivable memory.** I did not measure the resident size of 100,000
  requisition dicts. The ceiling's stated subject is memory, so this is the one measurement that
  would turn its value from a choice into a derivation, and it is cheap - it just needs a realistic
  record shape, which needs a real payload, which is the credential problem again.

- **Whether `main`'s secret-scan step has any OTHER unbaselined finding.** I read the five the tool
  printed and stopped there; a baseline whose `generated_at` is today and which still covers neither
  file may be stale in ways those five do not reveal. Task #87 says to verify a fix by re-running the
  CI command rather than assuming a regeneration covered it.

- **The suite floor and anchor floor above are branch-local.** Other branches are in flight
  (`fix/r7-findings`, `review/r8`, `chore/row-floors` all have live worktrees). 775 and 409 are what
  THIS branch measures; they have been wrong four times on this project by being copied out of a
  branch and into `ci.yml` unchecked.

---

**Worktree:** `/tmp/scan-bound-work`, removed after the final commit. The temporary
`/tmp/scan-bound-before` worktree used for §2's before-numbers was removed as soon as it was read.
**Not merged, not pushed.**
