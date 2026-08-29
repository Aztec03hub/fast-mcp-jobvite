# U7 - Resilience: implementation report

**Branch** `feat/u7-resilience`, from `1501033`. **Written 2026-08-29 06:03 AM CDT.**
Commits: `8328d60` (implementation), `fed05f7` (harnesses and the gaps they found).

---

## 1. The breaker rejection test, and its result either way

**`circuitbreaker 2.1.3` PASSES `DESIGN.md:617`'s criterion and is ADOPTED.** The measurement is
committed as `scripts/probe-breaker-call-path.py` and is run by
`tests/test_resilience.py::test_the_breaker_rejection_test_still_passes_against_the_pinned_library`,
so a version bump that moves expiry onto a timer turns a test red rather than leaving a stale
paragraph in this file.

The single experiment was *does it evaluate half-open expiry on the call path, or from a background
timer?* Three arms, verbatim from the probe's own output:

```
ARM 1  scheduling names in circuitbreaker's source: NONE
       searched for: ['threading', 'Timer', 'call_later', 'call_at', 'create_task',
                      'ensure_future', 'sched', 'sleep']
       PASS - expiry cannot be fired by anything but a read
ARM 1c positive control names in THIS module: ['threading', 'Timer', 'call_later', 'call_at',
                      'create_task', 'ensure_future', 'sched', 'sleep']
       PASS - the search term arm 1 uses is one that CAN be found
ARM 2  STORED state after the window elapsed:  'open'
       DERIVED state, computed by this frame:  'half_open'
       PASS - the expiry is a derived read, evaluated by its reader
ARM 3  request_id visible to a TIMER-fired transition: None
       PASS - the control fails exactly as the design predicts

VERDICT: circuitbreaker 2.x is ADOPTED by DESIGN.md:617's criterion.
```

The mechanism, read in `circuitbreaker.py`: `state` is a **property**, not a field -
`if self._state == STATE_OPEN and self.open_remaining <= 0: return STATE_HALF_OPEN`. Nothing writes
`half_open` anywhere. The transition is computed in whichever frame asks, which is the invocation's
own task, with its `request_id_var` bound. `DESIGN.md:602`'s sanctioned inline breaker is therefore
**not** taken, and `DESIGN.md:617`'s worry about "several Python breaker libraries" does not apply
to the blessed one.

**TWO OF THE PROBE'S OWN ARMS WERE WRONG ON THEIR FIRST RUN, and the corrections are in the file.**

* Arm 2 was written with `recovery_timeout=0`. `CircuitBreaker.__init__` reads
  `recovery_timeout or RECOVERY_TIMEOUT`, so a falsy `0` is silently replaced by the library's
  30-second default. The arm reported `open` and **would have been read as a REJECTION** - the
  library would have been rejected on the record for a defect in my probe.
* Arm 3's control used `loop.call_later`, and asyncio callbacks capture the scheduling context, so
  the "timer" transition saw the caller's `request_id` and the control PASSED when it was required
  to fail. It uses `threading.Timer` now, which is the shape `DESIGN.md:617` actually describes.

**`^2` confirmed against the CORPUS, not the digest.** `evolv-coder-standards` at `3e5da45`,
`standards/architecture/reference-architecture.md:95`:
`| Resilience | tenacity + circuitbreaker | ^9 / ^2 | ... |`. The digest's `STANDARDS.md:374-375`
agrees; the corpus is what was checked for currency.

---

## 2. What I built

All in `src/fast_mcp_jobvite/services/jobvite_client.py`, ordered
**timeout (innermost) -> retry -> breaker (outermost)**, which is `backend/resilience.md:216-222`'s
fixed order and not a preference.

| Layer | Method | What it does |
|---|---|---|
| timeout | `_attempt` / `_attempt_timeout` | four explicit phases, no SDK default, no scalar, clamped to the remaining budget |
| retry | `_attempt_with_retry` | `tenacity` `AsyncRetrying`, jittered backoff, both caps OR-ed, `Retry-After` honoured |
| breaker | `_through_breaker` | one module-level `CircuitBreaker`, 4xx excluded by predicate, transitions logged on the call path |

- **The total outbound budget now exists** - `outbound_budget_scope`, `outbound_budget_remaining`,
  `outbound_deadline_var`. A `ContextVar` holding a `monotonic()` deadline, for the same reason
  `request_id_var` is one (`DESIGN.md:608-612`): a module global would let two concurrent
  invocations share one deadline. Opened once per `scan`, so 25 pages share ONE budget; a bare
  `request` opens its own so an unscoped caller still gets a bound. A nested scope keeps the outer
  deadline.
- **`create_candidate` excluded from retry BY CONSTRUCTION**: `RETRYABLE_METHODS` is
  `frozenset({"GET", "HEAD"})` and the dispatch is on the HTTP method. No configuration can add
  `POST`, and a write tool written next year is excluded the moment it is written rather than the
  moment somebody remembers to add it to a list.
- **429 retried then mapped to 503**, honouring `Retry-After` (delta-seconds form only), clamped to
  the remaining budget.
- **Open breaker, outage and exhausted budget are all `/problems/service-unavailable` 503**, told
  apart by `detail`, with a `retry_after` extension member on the breaker arm. No slug is minted.
- **R2-L-4 closed**: `jobfeed_params` raises `RuntimeError` now, which ADR-0017 routes to
  `/problems/internal-error` **500**. It used to raise `JobviteUpstreamError(None, ...)`, rendering
  *"Jobvite returned status none: ..."* at 502 for a call Jobvite never saw. **The review's own
  suggested fix said `about:blank`; that text predates ADR-0017** and the test asserts the current
  slug, not the one the review named.

---

## 3. Which breaker behaviours I actually EXECUTED, and which remain claims

`DESIGN.md:64-68` names the circuit breaker as one of two mechanisms **never executed**, sitting
among measured results and borrowing their credibility. This is the ledger it asked for.

**EXECUTED, against `httpx2.MockTransport`:**

- it opens after `failure_threshold` consecutive outage-class failures (5xx arm and transport arm,
  separately);
- a 4xx does **not** trip it, driven at twice the threshold;
- an open breaker refuses the call **before** the transport sees a request - asserted by the request
  counter being empty, not by the exception type;
- `closed->open`, `open->half_open` and `half_open->closed` all log, each with the direction, the
  triggering counter and the invocation's `request_id`, and none with a URL;
- the `retry_after` hint on an open breaker is a real remaining window, not a constant;
- an exhausted budget does **not** count toward it.

**NOT EXECUTED, and these remain claims:**

- **Nothing here has ever met Jobvite.** Every response is scripted. `DESIGN.md:57` records that no
  claim about a Jobvite *success* response is verified, and that is still true.
- **The 30-second recovery window is never waited out at its real length.** The `open->half_open`
  case shortens `_recovery_timeout` to 0.01s. What is executed is the transition; what is not is
  that 30 seconds is the right number, and nothing about Jobvite's recovery time has been observed.
- **429 has never been observed from Jobvite** (`DESIGN.md:361-364`). The path is exercised, by us.
- **In-process, per-replica breaker state.** `backend/resilience.md:196-200` records that on N
  replicas each observes the threshold independently. One replica is what runs here; the N-replica
  behaviour is inherited from the library and untested.
- **The budget's 60-second default is a choice, not a measurement.** No Jobvite response-time
  distribution has ever been observed, so there is no percentile to derive it from. It is recorded
  as a choice in the constant's own comment, the way `DESIGN.md:1576-1583` records the 6/min guess.

---

## 4. Gate exit codes, read from the terminal

| Gate | Command | Exit |
|---|---|---|
| lint | `uv run --frozen ruff check src/ tests/ scripts/` | **0** (`All checks passed!`) |
| format | `uv run --frozen ruff format src/ tests/ scripts/` | `52 files left unchanged` |
| types | `uv run --frozen mypy src/ tests/` | **0** (`Success: no issues found in 46 source files`) |
| suite | `uv run --frozen pytest -q` | **0** - `477 passed, 6 deselected in 54.42s`, **0 skipped** |
| anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 197` | **0** - `all 235 anchors resolve` |
| obligations | `python3 docs/reviews/check-obligations.py` | **0** - `Mappings: 31 \| verified: 24 \| absent: 7` |
| citation shape | `python3 docs/reviews/check-design-citation-shape.py` | **0** - `0 citation(s) point at something that cannot be their subject` |
| U7 controls | `bash scripts/ci-harness-gate.sh check-u7-resilience-controls.sh --controls-fired` | **0** |
| U7 amputation | `bash scripts/ci-harness-gate.sh check-u7-resilience-amputation.sh --amputation --min-rows 16 --row-re '^########## A[0-9]+ '` | **0** |
| U4 controls (re-run after repointing) | `bash scripts/check-u4-client-controls.sh` | **0** - `RESULT: 19 killed, 0 not killed` |
| U4 amputation (re-run after repointing) | `bash scripts/check-u4-client-amputation.sh` | 1, its normal amputation exit; **17/17 rows applied, every one went red** |

`ruff format` was run BEFORE the final harness runs, and both harnesses were re-run after it. The
static anchor checker was re-run after it too.

### The two floors, DERIVED on this branch. **Both `ci.yml` edits are yours.**

`ci.yml` on this branch still reads `check-suite-floor.sh 447` and
`check-harness-anchors.py --self-check --floor 197`, which is what `1501033` carried.

| Floor | ci.yml at my base | Measured here |
|---|---|---|
| suite | 447 | **477** |
| harness anchors | 197 | **235** |

**These are branch-local and main has moved under me.** Task #45 records main measuring 467/200 and
#53 records 450/198 after `fix/r5-findings`. My 477 is `1501033`'s 447 plus 30 cases in
`tests/test_resilience.py`; my 235 is 197 plus the 38 anchors in the two new harnesses. **Re-derive
both after merging rather than taking these numbers**, because the delta is what is mine and the
base is not.

### The two `ci.yml` steps to add, for you to place in the harness block

```yaml
      - name: U7 resilience controls
        run: bash scripts/ci-harness-gate.sh check-u7-resilience-controls.sh --controls-fired

      - name: U7 resilience amputation
        run: bash scripts/ci-harness-gate.sh check-u7-resilience-amputation.sh --amputation --min-rows 16 --row-re '^########## A[0-9]+ '
```

---

## 5. Every harness row, and whether it fired

### `scripts/check-u7-resilience-controls.sh` - **22/22 controls fired, exit 0**

| Row | Subject | Result |
|---|---|---|
| M1 | a 4xx becomes retryable | KILLED |
| M2 | a 5xx stops being retryable | KILLED |
| M3 | a 429 surfaces as 502 instead of 503 | KILLED |
| M4 | `Retry-After` ignored in favour of the local backoff | KILLED |
| M5 | a negative `Retry-After` is trusted | KILLED |
| M6 | POST joins the retryable methods | KILLED |
| M7 | the method dispatch is inverted | KILLED |
| M8 | a nested budget scope restarts the deadline | KILLED |
| M9 | the deadline is not reset when its scope closes | KILLED |
| M10 | the attempt timeout is no longer clamped to the budget | KILLED |
| M11 | an exhausted budget surfaces as the last attempt's error | KILLED |
| M12 | an exhausted budget trips the breaker | KILLED |
| M13 | a 4xx trips the breaker | KILLED |
| M14 | a dead upstream never trips the breaker | KILLED **(SURVIVED on its first run - see below)** |
| M15 | an open breaker still issues the request | KILLED |
| M16 | the open breaker drops its `retry_after` hint | KILLED |
| M17 | an open breaker reports the outage detail | KILLED |
| M18 | the transition direction is reported backwards | KILLED |
| M19 | the transition line reports a constant counter | KILLED |
| M20 | the retry line reports a constant attempt number | KILLED |
| M21 | the retry line carries the exception's full text | KILLED |
| M22 | the breaker is skipped and the retry becomes outermost | KILLED |

**M14 SURVIVED on its first run and that is the row that paid for this harness.** It deletes the
branch of `_is_outage` that makes a `JobviteUnavailableError` - every transport failure - count
toward the breaker. The only breaker case at the time was
`test_repeated_5xx_trips_the_breaker`, which drives a 5xx and so reaches the *other* branch, the one
reading `upstream_status`. So an implementation where **a dead upstream never opens the circuit**
passed the case whose name says the breaker trips. `test_repeated_transport_failures_trip_the_breaker`
was written because the row survived, and M14 now points at it.

### `scripts/check-u7-resilience-amputation.sh` - **16 rows, 16 anchors applied, 0 vacuous, exit 0**

| Row | Subject | Suite result | Survivors |
|---|---|---|---|
| A1 | the budget scope is never opened around a single request | 8 failed | 22 |
| A2 | the budget scope is never opened around a scan | 1 failed | 29 |
| A3 | the pre-attempt budget check is deleted | 1 failed | 29 |
| A4 | the per-attempt timeout clamp is deleted | 1 failed | 29 |
| A5 | `stop_after_delay` is deleted, leaving only the attempt cap | 1 failed | 29 |
| A6 | the breaker is removed from the call path entirely | 5 failed | 25 |
| A7 | the open-breaker short circuit is deleted | 2 failed | 28 |
| A8 | the outage predicate is deleted and nothing is an outage | 5 failed | 25 |
| A9 | the retry line is not written at all | 2 failed | 28 |
| A10 | `request_id` is dropped from the retry line | 2 failed | 28 |
| A11 | the breaker transition line is not written at all | 2 failed | 28 |
| A12 | `request_id` is dropped from the transition line | 1 failed | 29 |
| A13 | the method dispatch is deleted and everything retries | 1 failed | 29 |
| A14 | the retry predicate is deleted and everything retries | 2 failed | 28 |
| A15 | the 5xx-to-retryable wrapping is deleted | 6 failed | 24 |
| A16 | `Retry-After` parsing is deleted and always returns `None` | 1 failed | 29 |

Total surviving assertions across all rows: **439**. Survivors are the output, and the reason most
rows leave 28 or 29 survivors is that the rows are narrow: deleting `Retry-After` parsing should not
make the breaker cases red.

**TWO ROWS WERE VACUOUS ON THE FIRST RUN.**

* **A2 was a real gap.** The budget scope was deleted from `scan` and **the whole suite stayed
  green**, because every other budget case drives ONE request. A 25-page scan opening 25 budgets is
  the exact unbounded direction the budget exists to bound.
  `test_a_whole_scan_shares_one_budget_rather_than_one_per_page` closes it, asserting the DEADLINE
  VALUE seen at the transport rather than elapsed time - a mock transport answers in microseconds,
  so a timing assertion there would be measuring the clock.
* **A5 is vacuous BEHAVIOURALLY and is now killed structurally, which is recorded rather than
  hidden.** `_attempt`'s pre-attempt budget check refuses to issue a request once the deadline has
  passed, so it subsumes `stop_after_delay` and the two caps `backend/resilience.md:88-90` requires
  cannot be separated by driving calls. The delay cap's real value is that it stops the loop before
  a final pointless backoff sleep, which no assertion can observe without making the suite sleep.
  `test_the_retry_stop_caps_both_attempts_and_elapsed_time` reads the composed `stop` expression
  instead, and its docstring says plainly that it is structural and why.

---

## 6. The wire page size and the budget, which you deferred until the budget existed (task #48)

**The budget is real now, so here is what the two interact to produce.** Two figures:

- `JOBVITE_MAX_RESULTS` default **50**, so `min(transport_cap, configured_result_cap)` is 50 and an
  exhaustive scan of the 1,240-record resource costs **25 requests**;
- the budget default **60 seconds** for the whole invocation.

**Today those 25 requests fit easily, and the reason is a second missing mechanism.**
`config.py:203` declares `outbound_rate_limit: int = Field(default=6, ge=1)` and
**nothing in `src/` reads it** - `grep -rn "outbound_rate_limit" src/` returns exactly two hits, the
declaration and my own comment saying it is not the budget. **The outbound self-throttle of
`DESIGN.md`'s §4.4 does not exist**, so 25 mock-transport requests complete in milliseconds and the
60-second budget is never approached.

**The moment somebody implements the self-throttle, the exhaustive scan becomes impossible.** At
6 requests per minute the requests are 10 seconds apart, so 25 of them take **240 seconds** against
a **60-second** budget: the scan would die with the budget's typed 503 at roughly request 7, having
returned nothing, on the default configuration. That is not a tuning problem, it is a contradiction
between three defaults that were each chosen separately.

The arithmetic that resolves it, for the record: at the raw v2 transport cap of 500, the same
resource costs **3 requests, about 20 seconds** at 6/min, which fits inside 60 comfortably.

**I have written no branch and no code comment about this, per your instruction.** What it needs is
a **Proposed ADR** settling all three figures together - the wire page size for an exhaustive scan,
the budget, and whether the self-throttle applies within one invocation or between them - because
changing any one alone moves the contradiction rather than removing it. I would not pick the page
size on my own: the design states no paging policy, and U6 was right to delete the branch it wrote.

---

## 7. Findings, each with a suggested fix

**F1 - `outbound_rate_limit` has no consumer; the outbound self-throttle does not exist.**
`config.py:203` declares it and `grep -rn "outbound_rate_limit" src/` finds only that declaration
and my comment. Same shape as the budget obligation I was given (task #43): a promised mechanism
with a named variable and no implementation, which reads as done. *Suggested fix:* a new task, and
an `asyncio` token-bucket or a monotonic last-call timestamp on `JobviteClient`, gated on the same
`_JOBVITE_BREAKER`-style module scope so it throttles the DEPENDENCY rather than an instance. It
must be sequenced with the ADR in §6, since implementing it as-is breaks the exhaustive scan.

**F2 - `JobviteRetryLaterError` lives in my file and belongs in `errors.py`.** It subclasses
`JobviteUnavailableError`, inherits `kind`, mints no slug, and exists only to carry RFC 9457's
`retry_after` member that `build_problem` already accepts and nothing produced. I did not write
`errors.py` because the brief bars it. *Suggested fix:* move the class to `errors.py` beside
`JobviteUnavailableError` and re-export, in one commit with no behaviour change.

**F3 - nothing at the tool boundary passes `retry_after` into the problem object.** The hint is on
the exception; `tools/jobs.py` calls `problem_from_exception(exc, request_id)` without it, so the
member never reaches a caller. `tools/` is not mine. *Suggested fix:* at each tool boundary,
`extras = {"retry_after": exc.retry_after} if isinstance(exc, JobviteRetryLaterError) and
exc.retry_after is not None else {}`, then `problem_from_exception(exc, request_id, **extras)`.

**F4 - the budget is not yet opened at the true invocation boundary.** `scan` opens it and a bare
`request` opens its own, which bounds every path that exists today. But `DESIGN.md:373-375` says
"one tool invocation", and the honest place for that is `audit.py`, in the same statement that mints
the `request_id` - `audit.py` is not mine. *Suggested fix:* one line beside `request_id_scope`:
`with outbound_budget_scope(settings.outbound_budget_seconds):`. Nesting is safe by construction -
an inner scope keeps the outer deadline - so adding it narrows nothing and changes no test.

**F5 - the config variables I need, for you to route.** I took them as constructor arguments with
defaults so the unit is complete without editing `config.py`:
`JOBVITE_OUTBOUND_BUDGET_SECONDS` (float, default 60.0, `gt=0`),
`JOBVITE_RETRY_MAX_ATTEMPTS` (int, default 4, `ge=1`),
and, if you want them configurable rather than constants,
`JOBVITE_BREAKER_FAILURE_THRESHOLD` (int, 5) and `JOBVITE_BREAKER_RECOVERY_SECONDS` (float, 30.0),
plus the four timeout phases. All are module constants named `DEFAULT_*` today, so routing them is
a `Field` plus a keyword at the one construction site.

**F6 (nit) - the R2/R2-LEFTOVER suggested fix for L-4 names a slug ADR-0017 replaced.** Both
documents say the fix is `about:blank`; ADR-0017 routes an out-of-hierarchy exception to
`/problems/internal-error` 500, which is what `problem_from_exception` does and what the test now
asserts. *Suggested fix:* one sentence in `docs/reviews/R2-LEFTOVER-VERDICTS.md` under L-4 noting
the slug moved, so the next reader does not "fix" the test back.

**F7 (nit) - `tests/test_manifest.py`'s dependency set and `pyproject.toml`'s mypy overrides are
files I was not scoped to.** I edited both because the unit cannot exist without them: the manifest
case is a closed-set assertion that must name every runtime dependency, and `circuitbreaker` ships
no `py.typed` so `strict = true` rejects the import without an override. Both edits carry their
reasoning in place. *Suggested fix:* none - flagging the scope crossing so you can review those two
diffs specifically.

---

## 8. What I could NOT settle

- **Whether 60 seconds is the right budget, 5 the right threshold, or 30 the right recovery.** None
  is derived from anything. No Jobvite response-time or availability observation exists on this
  project, so there is no distribution to take a percentile from. They are recorded as choices in
  the constants' own comments; only a live tenant settles them.
- **The wire page size.** §6 states the interaction and the arithmetic and stops there, because you
  said the policy is a Proposed ADR and not an agent's call, and I agree - the three figures have to
  move together.
- **Whether `circuitbreaker`'s in-process, per-replica state is acceptable in deployment.**
  `backend/resilience.md:196-200` calls it acceptable and names `purgatory` or
  `pybreaker`+`CircuitRedisStorage` as the shared-state alternatives if it ever stops being. Nothing
  here establishes how many replicas this will run on.
- **Whether the `_JOBVITE_BREAKER` module global is right for the process's whole lifetime.** It is
  right for what a breaker is *for*, and it is what forced two suite-wide fixtures in
  `tests/conftest.py`. I have not thought through what it means for a long-lived server that has
  been running for weeks, other than that `reset_breaker_for_test` is not for it.
- **The U4 amputation harness's own exit code.** It exits 1 with survivors, which is its designed
  amputation behaviour and unchanged by my repoints, but I did not check how `ci.yml` gates that
  step - I only confirmed all 17 rows applied and all 17 went red.
- **`docs/OBLIGATIONS.md` has 7 anchors "recorded as absent"** and the checker reports that as OK. I
  did not investigate whether any of the 7 are U7's; the checker says every *mapped* anchor still
  contains its subject, which is a narrower statement than the row being satisfied.

## 9. Housekeeping

- **The worktree `/tmp/u7-resilience-work` is removed** (see the SendMessage; it is removed as the
  last step after the push).
- **I never ran `git stash` and never ran `git checkout <path>`.** Every restore in both harnesses
  is `cp` from a backup, verified with `cmp` against a pristine copy taken before row 1.
- **`r2-fixes` is not in `services/jobvite_client.py`.** Nothing on this branch's copy of that file
  came from it.
- **One instrument fault of my own, recorded because it produced two false findings.** I
  backgrounded a U4 mutation harness against this same working tree and then ran the suite while it
  was mid-row. The suite reported failures in `test_jobvite_client.py` that I diagnosed and wrote up
  as breaker pollution. They were the harness's mutations. The correction, with the real
  measurements, is in `tests/conftest.py`'s comment block; the breaker fixture IS needed - disabling
  it alone gives 19 failures, all in `test_tools_jobs.py` - but not for the reason I first gave, and
  the run I first read was not a measurement of anything.
