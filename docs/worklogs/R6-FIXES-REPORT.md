# R6-FIXES - all nine findings closed, and R6's own suggested fix for H1 does not work

**Branch `fix/r6-findings`, based at `a48adf8`.** Worktree `/tmp/r6-fixes-work`, removed as the last
step after the push. Written **2026-08-29 07:32 AM CDT** by `r6-fixes`.

Authority is `docs/reviews/REVIEW-R6.md`. Nine findings: three High, three Medium, three nits. **All
nine are fixed**, each with the control that proves the fix can fail, and two of the fixes are not
the ones R6 proposed - both times because the proposal was measured and found wanting.

---

## Gates, read from the terminal

Both floors DERIVED from `ci.yml`, never retyped. **The `ci.yml` edits are the team lead's.**

| Gate | Command | Result | Exit |
|---|---|---|---|
| floor (suite), as found | `grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml` | `check-suite-floor.sh 562` | - |
| suite, BEFORE | `uv run --frozen pytest -q` | `562 passed, 6 deselected in 59.99s`, **0 skipped** | **0** |
| suite, AFTER | `uv run --frozen pytest -q` | **`567 passed, 6 deselected in 43.89s`**, **0 skipped** | **0** |
| floor (anchors), as found | `grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml` | `--floor 278` | - |
| anchors, AFTER | `python3 scripts/check-harness-anchors.py --self-check --floor 278` | **`OK: all 285 anchors resolve to exactly one hit in their target file (floor 278)`** | **0** |
| anchor controls | `bash scripts/check-harness-anchors-controls.sh` | `9/9 controls fired.` | **0** |
| lint | `uv run --frozen ruff check .` | `All checks passed!` | **0** |
| format | `uv run --frozen ruff format --check .` | `62 files already formatted` | **0** |
| types | `uv run --frozen mypy` | `Success: no issues found in 50 source files` | **0** |
| lock | `uv lock --check` | `Resolved 120 packages` | **0** |
| quickstart | `uv run --frozen python docs/reviews/check-quickstart.py` | `OK: 1 Quickstart command(s) ran and printed what they should.` | **0** |
| obligations | `python3 docs/reviews/check-obligations.py` | `Mappings: 31 \| anchors verified against their subject: 24 \| recorded as absent: 7` / `Every mapped anchor still contains its subject. OK.` | **0** |
| U7 controls | `bash scripts/check-u7-resilience-controls.sh` | **`26/26 controls fired.`** (was 22/22) | **0** |
| U7 amputation | `bash scripts/check-u7-resilience-amputation.sh` | **`ROWS: 19  ANCHORS APPLIED: 19`** / `VACUOUS ROWS: 0` / `TOTAL SURVIVING ASSERTIONS ACROSS ALL ROWS: 605` (was 16 rows) | **0** |

### THE NEW FLOORS, for `ci.yml`

- **`check-suite-floor.sh 567`** (from 562; +5 cases, 0 skips)
- **`check-harness-anchors.py --self-check --floor 285`** (from 278; +7 anchors)

### The sibling harnesses over the same file, re-run because I changed it

`jobvite_client.py` is also the subject of U4, U6 and U8. None of their rows became survivors:

| Harness | Result | Exit |
|---|---|---|
| `check-u4-client-controls.sh` | `RESULT: 19 killed, 0 not killed` | **0** |
| `check-u4-client-amputation.sh` | gate passed, 657 surviving assertions | **0** |
| `check-u6-paging-controls.sh` | `16/16 controls fired.` | **0** |
| `check-u6-paging-amputation.sh` | `ROWS: 11  ANCHORS APPLIED: 11`, gate passed | **0** |
| `check-u8-candidates-controls.sh` | `25/25 controls fired.` | **0** |
| `check-u8-candidates-amputation.sh` | `ROWS: 14  ANCHORS APPLIED: 14`, gate passed | **0** |

**`check-u4-client-*.sh` refused to run on a dirty tree** - `ABORT: ... has uncommitted changes. This
harness restores with 'git checkout --', which would DISCARD them.` That guard is correct and I
committed first rather than working around it. Recording it because the two exit-3s in my transcript
are that refusal and not a failure.

---

# HIGH

## R6-H1 - a non-outage RESET the breaker. The probe reads 4 -> 4 where it read 4 -> 0.

**THE H1 PROBE, BOTH SIDES**, `docs/reviews/probe-r6-breaker-reset.py`, run from its committed path:

```
BEFORE (at a48adf8, unmodified)          AFTER (this branch)
threshold = 5                            threshold = 5
ARM 1  404 (non-outage): 4 -> 0 closed   ARM 1  404 (non-outage): 4 -> 4 closed
ARM 2  budget exhausted : 4 -> 0 closed  ARM 2  budget exhausted : 4 -> 4 closed
ARM 1c 500 (outage)     : 4 -> 5 open    ARM 1c 500 (outage)     : 4 -> 5 open

ARM 1c control: 4 -> 5  PASS             ARM 1c control: 4 -> 5  PASS
ARM 1 verdict : 4 -> 0  RESET (defect)   ARM 1 verdict : 4 -> 4  not counted (ok)
ARM 2 verdict : 4 -> 0  RESET (defect)   ARM 2 verdict : 4 -> 4  not counted (ok)
```

**The control moved not at all**, which is what makes the two arms a reading and not a constant.

### R6's SUGGESTED FIX DOES NOT FIX IT, and I measured that rather than reasoning about it

R6 proposed catching the declined exception *inside* the `with`, holding it in a local, and re-raising
it after the block. **The block then exits CLEANLY, and a clean exit is exactly the branch that calls
`reset()`.** Driven directly against `circuitbreaker` 2.1.3 with a predicate that declines
everything:

```
$ uv run --frozen python -c '<the R6 shape, counter primed to 4>'
R6's suggested shape: 4 -> 0 closed
```

Same defect, same number. This is the review's own diagnosis being correct and its remedy being
subject to the very mechanism it diagnosed - `__exit__` has **two** outcomes and the fix needs
**three**.

### What I did instead

**The call runs OUTSIDE the breaker's context and its outcome is reported afterwards.** Three
genuinely distinct outcomes, expressed with nothing but the public context manager:

- **success** - enter an empty `with _JOBVITE_BREAKER: pass`. `__exit__(None, None, None)` **is**
  `reset()`, which is what a success should do, now said explicitly instead of as a side effect.
- **an accepted failure** - `with _JOBVITE_BREAKER: raise`, so `__exit__` sees it and counts it.
- **a declined failure** - the breaker is **never entered**. Neutral is expressed by absence.

`_is_outage` remains the single authority on which failures are signals; what changed is what a
declined one costs. `except Exception`, not `BaseException`, so a `CancelledError` - the caller going
away, which says nothing about Jobvite - also leaves the breaker untouched, by not being caught.

**The half-open question R6 could not settle is answered by construction.** A neutral exception now
performs no operation on the breaker at all, so a breaker whose open window has expired keeps
`_state = STATE_OPEN` and its `state` property keeps computing `half_open`. There is no path by which
a call that never reached Jobvite can close it.

### The control that proves the new case can fail

The two pre-existing exclusion cases assert `failure_count == 0` from a closed start, and **`0` is
what "not counted" and "reset to zero" both produce** - they cannot see this defect in either
direction. So the new case starts from `threshold - 1`, the only start the two hypotheses disagree
about:

`test_a_non_outage_does_not_RESET_the_breakers_accumulated_failures`, three arms - a 4xx, an
exhausted budget, and a mechanism-matched control that puts a real outage in the last slot and
reaches `threshold`, `state == "open"`.

Controls row **`M23 a non-outage RESETS the breaker instead of being ignored`** deletes the neutral
guard, restoring the pre-fix behaviour. **KILLED.**

## R6-H2 - the private type escaped on every write. Same public type on both branches now.

`docs/reviews/probe-r6-post-escape.py`, both sides:

```
BEFORE                                              AFTER
ARM 1c GET  JobviteUpstreamError                    ARM 1c GET  JobviteUpstreamError
       /problems/external-service-error 502                /problems/external-service-error 502
       failure_count : 1                                   failure_count : 1
ARM 1  POST _RetryableUpstream                      ARM 1  POST JobviteUpstreamError
       /problems/internal-error 500                        /problems/external-service-error 502
       'An unexpected _RetryableUpstream occurred.'         'Jobvite returned status 503: no message'
       failure_count : 0                                   failure_count : 1

same escaping type on both branches? False           same escaping type on both branches? True
```

All three of R6's failures close together: the status is 502 not 500, the private class name is gone
from the detail, and `failure_count` moves from 0 to 1 - a 503 to a write is now visible to the
breaker, where before it was invisible **and**, per H1, actively held the breaker closed.

The fix is R6's: the non-retrying branch converts too, `raise exc.public_error() from None`. Two
conversion sites now, and `_RetryableUpstream`'s docstring names both (R6-N2).

**Controls:** amputation row **`A17 the non-retrying branch's _RetryableUpstream conversion is
deleted`**. It was **vacuous before this work** - no test in the suite drove a non-retryable METHOD
against a retryable STATUS - and it is **not vacuous now**: the amputation run reports `VACUOUS ROWS:
0` across 19 rows. Two new cases: `test_a_write_that_meets_a_5xx_surfaces_502_and_not_an_internal_error`
(asserting type AND status, plus `"_RetryableUpstream" not in problem["detail"]`, plus
`failure_count == 1`, plus `seen == ["POST"]` so §8 #21 still holds) and its 429 sibling asserting the
503 mapping.

## R6-H3 - the surviving mutation is dead.

`return exc.counts_toward_breaker` -> `return False` passed **all 562 tests** at `a48adf8`. New case
`test_a_429_counts_toward_the_breaker_but_an_exhausted_budget_does_not` drives
`DEFAULT_BREAKER_FAILURE_THRESHOLD` 429s and asserts `state == "open"`, **paired in the same case**
with a budget arm asserting it stays closed - both arms, because the 429 arm alone passes against a
predicate that counts everything (which is M12's mutation) and the budget arm alone passes against
one that counts nothing (which is this row's).

Controls row **`M23b a 429's counts_toward_breaker is ignored`** applies exactly R6's surviving
mutation. **KILLED.**

---

# MEDIUM

## R6-M1 - and R6's remedy here is wrong too, in a way that is worse than the defect

R6 proposed returning `0.0` from `_wait_for_retry`, on the reasoning that "`stop_after_delay` will
fire on the next loop". **It does not. `stop_after_delay` fires on ELAPSED time**, so a zero wait
advances the clock by nothing, no stop arm ever fires, and the loop **burns the entire attempt cap
back to back** - hammering an upstream that had just asked us to wait fifteen minutes, which is the
precise opposite of `backend/resilience.md:95-97`.

I implemented that version first and the probe showed it: ARM 1 went to `0.00s` **and the outcome
changed to `JobviteUpstreamError`** because the retries had all fired instantly and hit the attempt
cap. The elapsed number looked like a fix. The row count would have shown it was not.

**What I did instead: a third `stop` arm.** `_RetryAfterExceedsBudget` is a `stop_base` subclass
(the type `|` composes; a plain callable is not) that stops when the failed attempt carried a
`Retry-After` we cannot afford. `_wait_for_retry` goes back to being a pure clamp. The call then ends
after the attempt that carried the header, **with no further request**, and the existing conversion
surfaces the 429's own `Retry-After` to the caller.

```
BEFORE                                          AFTER
ARM 0c 404, not retryable : elapsed=0.00s       ARM 0c 404, not retryable : elapsed=0.00s
ARM 1c no Retry-After     : elapsed=1.00s       ARM 1c no Retry-After     : elapsed=1.00s
ARM 1  Retry-After: 900   : elapsed=1.00s       ARM 1  Retry-After: 900   : elapsed=0.00s
```

**The assertion in the case is the ROW COUNT**, not elapsed time - `seen == ["GET"]` - because a mock
transport answers in microseconds and elapsed time cannot tell "stopped" from "retried instantly".
That is the distinction that caught the first fix. The case carries its own control: the identical
drive with a budget the header fits inside retries to the cap, `len(seen2) == 4`.

`test_a_retry_after_we_cannot_afford_stops_instead_of_sleeping`; controls row **`M24 a Retry-After we
cannot afford is slept out anyway`** (KILLED); amputation row **`A19 the Retry-After-exceeds-budget
stop arm is deleted`** (non-vacuous).

**`test_the_retry_stop_caps_both_attempts_and_elapsed_time` had to change** and it is worth naming:
it asserted the literal one-line string `"stop_after_attempt(self._retry_max_attempts) |
stop_after_delay("`, which a third arm makes false without making the behaviour wrong. It now parses
the `|`-joined arms out of the source and asserts the SET contains all three, so a fourth arm will not
break it either.

## R6-M2 - arm 1c no longer reads the file that defines its own question

Arm 1c searched the probe's own source for `SCHEDULING_NAMES`, defined in that same source. **The new
arm 1c does not read the probe at all.** It reads `CONTROL_MODULES` - eight stdlib modules that really
schedule, none of which has ever heard of this probe's term list - and requires every term to be
demonstrable in one of them. **R6's falsifying case is now structurally impossible**: a file
containing only the term list is not consulted by the control, so it cannot pass it.

Searching is now **whole-word** (`\b`), which kills the `sched` substring hit on *scheduling* that R6
measured. `sched` is replaced by `scheduler`, which the `sched` module really defines.

**Proof the new arm can fail**, measured: I added `"definitely_not_a_scheduler"` to
`SCHEDULING_NAMES`, ran the probe, and read

```
ARM 1c terms no scheduling module demonstrates: ['definitely_not_a_scheduler']
       *** BROKEN CONTROL *** arm 1 searches for term(s) that no
           real scheduling code contains, so their absence from
           circuitbreaker means nothing.
VERDICT: circuitbreaker 2.x is REJECTED by DESIGN.md:617's criterion.
PROBE EXIT=1
```

Restored by `cp` from a backup, `cmp: IDENTICAL`.

**`docs/reviews/probe-r6-arm1c-tautology.py` still reports the tautology and that is correct** - it
carries its own copy of the OLD predicate and its own copy of the term list, so it is a record of what
was measured at `ec38835`, not an assertion about the current probe. Its ARM A now reads 5/8 rather
than 4/8 because R6-N3's rewrite changed the probe's prose. Do not read it as a live check.

## R6-M3 - `Retry-After: 0` is floored, not trusted

`return max(value, DEFAULT_RETRY_INITIAL_BACKOFF) if value >= 0 else None`. Back-pressure is still
honoured; jitter cannot be switched off by an upstream-controlled header. The case at
`test_a_retry_after_we_cannot_trust_is_ignored_rather_than_guessed` gained `"0"` (asserting the floor)
and `""`, and its docstring now says which members it checks instead of the word "malformed".

Controls row **`M25 a Retry-After of 0 is trusted and disables jitter`** (KILLED). **M5's anchor moved
with the code** and was repointed; both rows now target the new expression, and the anchor checker
caught the stale one before I ran anything.

---

# NITS

- **R6-N1** - `U7-IMPL-REPORT.md`'s two `config.py:203` citations. Repointed to **the field name**,
  which `grep -c "outbound_rate_limit" src/fast_mcp_jobvite/config.py` says is **1** and so cannot
  drift, rather than to `228` which would decay the same way across the next merge. An HTML comment
  records why.
- **R6-N2** - `_RetryableUpstream`'s docstring rewritten **in place**, naming the two converters and
  saying plainly that the old sentence was false and how. It deliberately does NOT offer a grep as
  the check: **every grep short enough to put in the docstring also matches the docstring**, which is
  R6-M2's own shape one file over. I wrote that self-matching grep twice before noticing and measuring
  it (`grep -c "raise exc.public"` returned **3**, not 2).
- **R6-N3** - six terms added (`call_soon`, `call_soon_threadsafe`, `signal`, `run_in_executor`,
  `to_thread`, `concurrent`); `inspect.getsource` replaced by `module_source`, which walks the package
  directory when `__file__` is an `__init__.py` and **raises** if it finds no readable file, so a
  packaged `circuitbreaker` release fails loudly instead of returning a clean empty.
  **`alarm` was considered and deliberately left out**: `signal.alarm` is implemented in C, so no
  readable Python source can serve as its control, and the new arm 1c would fail on it forever.
  Reaching for it is already caught by the `signal` term. `sched` -> `scheduler` as above.

---

## Things I checked and did NOT change

- **`_should_retry`, `_log_retry_attempt` and the composition order** - untouched. M20, M21 and M22
  all still KILLED against them.
- **`server.py` and `config.py`** - not touched at all, per the brief. **No fix needed a new
  setting**, so nothing is waiting on routing.
- **`docs/DESIGN.md`** - not read from the working tree and not edited. **No Proposed ADR was
  needed**: every fix here makes the code do what DESIGN.md:346-364 and :373-375 already say, and
  ADR-0026 remains free.
- **`ci.yml`** - not touched. Both floors reported above, neither retyped into any file.

## What I could NOT settle

- **What a 5xx carrying a `Retry-After` we cannot afford should surface as.** With the M1 fix it
  surfaces as `/problems/external-service-error` 502 (the 5xx mapping DESIGN.md:346-349 requires) and
  the upstream's hint is dropped, because `public_error()` only attaches `retry_after` on the 429
  path. A 429 keeps its hint. I did not change the 5xx mapping - it is the design's, not a defect -
  but "the upstream told us when to come back and we did not pass it on" may be worth a finding of its
  own. Not mine to rule on.
- **Whether the in-process, per-replica breaker is acceptable in deployment.** Unchanged from U7's own
  note and R6's. H1's fix removes the "each replica's counter is independently resettable" amplifier,
  but I still have no deployment fact to size the replica count with.
- **Whether R6-H2 is reachable from a tool today.** Still latent: no `src/` caller passes a
  non-retryable method at this SHA. I did not establish a live path and am not claiming one. The fix
  lands ahead of the caller rather than behind it.
- **Whether `probe-r6-breaker-reset.py` and `probe-r6-post-escape.py` should now be wired into CI.**
  R6 kept them out because they demonstrated defects and gating on them would gate on the bugs
  staying. Both now demonstrate correct behaviour and exit 0, so the objection is gone - but wiring
  them is a `ci.yml` edit, which is the team lead's. **The behaviour they check is already pinned by
  M23, M23b and A17**, so this is a redundancy question, not a coverage gap.

## Housekeeping

- No `git stash`, no `git checkout <path>` at any point. Every mutation restored with `cp` and
  verified with `cmp`; `PYTHONDONTWRITEBYTECODE=1` throughout.
- `ruff format` was run BEFORE the final harness runs, and the harnesses and
  `check-harness-anchors.py` were then re-run - which is how the two stale anchors (M5's and A5's)
  were caught rather than shipped.
- The worktree `/tmp/r6-fixes-work` is removed after the push.
