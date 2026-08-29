# CODE-REVIEW-R6 - U7, resilience

**Subject SHA: `ec38835`** ("feat(u7): merge resilience, wire its harnesses, and floors to 500/239").
Every `file:line` in this report is against `ec38835` unless it says otherwise. `u8-candidates` and
`u9-http` are both live in the shared checkout, so nothing here was read from a working tree: the
review ran in `/tmp/code-review-r6-work`, a worktree pinned to `ec38835`, and citations were taken
with `grep -n` inside it.

**Written 2026-08-29 06:51 AM CDT** by `code-review-r6`.

**Three High, three Medium, three nits. One is a surviving mutation.** All six of the graded findings
were measured, not reasoned - the four probes are quoted verbatim below and are reproducible.

---

## Gates, read from the terminal in the pinned worktree

Both floors derived from `ci.yml` rather than retyped, per `PREAMBLE.md`.

| Gate | Command | Result |
|---|---|---|
| floor (suite) | `grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml` | `check-suite-floor.sh 500` |
| suite | `uv run --frozen pytest -q` | **`500 passed, 6 deselected in 58.90s`**, **0 skipped**, exit **0** |
| floor (anchors) | `grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml` | `--floor 239` |
| anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 239` | **`OK: all 239 anchors resolve to exactly one hit in their target file (floor 239)`**, exit **0** |

`500 passed` equals the floor exactly, and there are no skips. **U7's two harnesses ARE wired** -
`ci.yml` at `ec38835` carries both the `U7 resilience controls` and `U7 resilience amputation` steps
through `scripts/ci-harness-gate.sh`, which is the "control that is not wired" shape checked rather
than assumed.

**Mutation hygiene.** One mutation was applied, in the pinned worktree only, never in the shared
checkout. Its anchor was asserted unique before the write (`grep -c` -> `1`), the write was proved to
have landed with `git diff --stat` (`1 file changed, 1 insertion(+), 1 deletion(-)`), and the restore
was a `cp` from a backup verified with `cmp` (`cmp: IDENTICAL`) followed by an empty `git status
--porcelain`. `PYTHONDONTWRITEBYTECODE=1` throughout. No `git stash`, no `git checkout <path>`.

---

# HIGH

## R6-H1 - a non-outage exception does not merely fail to count toward the breaker, it RESETS it. Measured: 4 -> 0.

**`src/fast_mcp_jobvite/services/jobvite_client.py:1379`** (`with _JOBVITE_BREAKER:`), against
`circuitbreaker` 2.1.3 `__exit__`, at `.venv/lib/python3.12/site-packages/circuitbreaker.py:113-120`:

```python
def __exit__(self, exc_type, exc_value, _traceback):
    if exc_type and self.is_failure(exc_type, exc_value):
        self._last_failure = exc_value
        self.__call_failed()
    else:
        self.reset()          # <-- line 119
    return False
```

and `reset()` at `:219-225` sets `_state = STATE_CLOSED` and `_failure_count = 0`.

**So `_is_outage` returning `False` is not "this failure is not evidence". It is "this call
SUCCEEDED".** Every exception the predicate declines - a 4xx, an exhausted budget, and (see R6-H2)
the private `_RetryableUpstream` - closes the breaker and zeroes the counter.

### The measurement

`/tmp/r6-probes/probe_breaker_reset.py` (reproduced in full at the end of this report). Drive the
breaker to `threshold - 1` with real outages, then issue ONE non-outage call, and read
`failure_count` on either side. Verbatim:

```
threshold = 5
ARM 1  last call is a 404 (non-outage): failure_count before=4 after=0 state=closed
ARM 2  last call exhausts the budget   : failure_count before=4 after=0 state=closed
ARM 1c last call is a 500 (outage)     : failure_count before=4 after=5 state=open

ARM 1c control: 4 -> 5  (must be 4 -> 5) PASS
ARM 1 verdict : 4 -> 0  RESET (defect)
ARM 2 verdict : 4 -> 0  RESET (defect)
```

The `ARM 1c` control is mechanism-matched: the same drive with an outage in the last slot reaches
`5` and opens, so the harness observes a real count rather than a constant.

### The failure this produces

`DESIGN.md:354-355` (frozen at `c15b138`) says *"4xx must not trip it - a bad candidate id is the
caller's problem, not a health signal."* **Not tripping it and healing it are different
behaviours, and the code has the second.** Under any traffic that mixes 4xx with outages - which is
what a partially-degraded upstream produces, and what a tool suite issuing `get_job` on stale ids
produces regardless of Jobvite's health - **the breaker can never reach its threshold**, because the
counter is returned to zero by every interleaved 4xx. The mechanism `DESIGN.md:64-68` names as never
executed is not merely unmeasured at its real length; on this composition it can be prevented from
firing at all by traffic that says nothing about the upstream.

The budget arm is worse in kind. `JobviteRetryLaterError`'s own docstring at `:750-755` argues
`counts_toward_breaker=False` because *"counting it would let one slow invocation trip a breaker for
every other caller"*. The reasoning is right and the implementation does the opposite of neutral:
**one slow invocation now CLOSES the breaker for every other caller**, including from `half_open`,
without a single successful call having reached Jobvite.

### Why no test caught it

Both exclusion cases start from a closed breaker and assert the counter is zero:

- `tests/test_resilience.py:335` - `assert jc._JOBVITE_BREAKER.failure_count == 0`
- `tests/test_resilience.py:716` - `assert jc._JOBVITE_BREAKER.failure_count == 0`

`0` is what "not counted" and "reset to zero" both produce from a start of `0`. **The two hypotheses
are indistinguishable to these assertions**, and no case anywhere in the suite pins `failure_count`
to a non-zero value across a non-outage: the only other occurrences are `:800` and `:806`, which read
the `closed->open` log line. This is the brief's shape 3 - *a test NAME is an unverified claim about
its BODY* - and shape 7, a constant read the same way the code reads it.

### Suggested fix

Do not let `circuitbreaker.__exit__` see a declined exception at all. Catch the non-outage classes
inside the `with` and re-raise them outside it, so the block exits cleanly only on a real success:

```python
# jobvite_client.py, replacing the body of the `try` at :1375-1388
_NON_SIGNAL = (JobviteRetryLaterError, JobviteUpstreamError)
try:
    with _JOBVITE_BREAKER:
        try:
            return await self._attempt_with_retry(...)
        except _NON_SIGNAL as exc:
            if _is_outage(type(exc), exc):
                raise
            # Neutral: neither a failure nor a success. Carried out
            # of the breaker's scope so `__exit__` cannot reset().
            neutral = exc
    raise neutral from None
except CircuitBreakerError:
    ...
```

`_is_outage` stays the single authority on which failures are signals; what changes is that a
declined one is now genuinely neutral rather than positive evidence.

**And add the assertion that can tell the two apart**, which is the half of this the code fix does
not buy: drive to `threshold - 1`, issue the non-outage, and assert `failure_count == threshold - 1`
(not `== 0`). Do it for both arms - the 4xx at `:703` and the budget at `:316`. Add a controls row
`M23 - a non-outage resets the breaker instead of being ignored` mutating `_is_outage`'s declined
branch, so the distinction is pinned by the harness as well as by a case.

---

## R6-H2 - the module-private `_RetryableUpstream` escapes to the caller on every non-idempotent call, as `/problems/internal-error` 500. Measured.

**`src/fast_mcp_jobvite/services/jobvite_client.py:1445-1456` and `:1710-1713`.**

This is the brief's opening 2, and the path is not an exotic one - it is the *only* path a write can
take.

`_attempt` wraps any retryable status in `_RetryableUpstream` **regardless of the HTTP method**:

```
1710:            if _is_retryable_status(exc.upstream_status):
1711:                raise _RetryableUpstream(
1712:                    exc, _retry_after_seconds(response.headers)
1713:                ) from None
```

On the retrying branch, `_attempt_with_retry:1485-1509` converts it back via `public_error()`. **On
the non-retrying branch there is no converter** - `:1448` is a bare `return await self._attempt(...)`
with no `except` around it. So a `POST` that meets a 5xx or a 429 raises the private type straight
out of `request()`.

The class docstring at `:781-790` states the invariant this breaks, in its own words:

> **Module-private and it never reaches a caller.** `_attempt` raises it, `_attempt_with_retry`
> converts it back into the public typed error the moment retries are exhausted, and **nothing else
> may see it.**

### The measurement

`/tmp/r6-probes/probe_post_escape.py`. Same 503 response, two methods:

```
all responses are HTTP 503 with a 503 envelope

ARM 1c GET  (retrying branch)
    escaping type : fast_mcp_jobvite.errors.JobviteUpstreamError
    problem       : ('/problems/external-service-error', 502, 'Jobvite returned status 503: no message')
    failure_count : 1

ARM 1  POST (non-retrying branch)
    escaping type : fast_mcp_jobvite.services.jobvite_client._RetryableUpstream
    problem       : ('/problems/internal-error', 500, 'An unexpected _RetryableUpstream occurred.')
    failure_count : 0

same escaping type on both branches? False
```

`ARM 1c` is the positive control: the identical drive on the retrying branch produces the documented
public type and the 502 the design requires, so the difference is the method dispatch and not a
broken fixture.

### Three failures, from one cause

1. **The wrong status and the wrong problem type.** `ADR-0017` routes an out-of-hierarchy exception
   to `/problems/internal-error` **500**. `DESIGN.md:346-349` requires a Jobvite 5xx to surface as
   `/problems/external-service-error` **502**. A write against a failing Jobvite therefore tells the
   caller *we* broke, not that the upstream did - and 500 is the one status a caller must not retry
   or diagnose upstream.
2. **A private class name reaches the API consumer.** The detail is literally `An unexpected
   _RetryableUpstream occurred.` `backend/error-handling.md:383` is `priority: required` and says
   never leak third-party or internal exception detail to API consumers; this leaks the name of a
   module-private class that the same file's docstring says a caller may never see.
3. **It does not count toward the breaker, and per R6-H1 it RESETS it.** `_is_outage:863-888`
   dispatches on `JobviteRetryLaterError`, `JobviteUnavailableError` and `JobviteUpstreamError`;
   `_RetryableUpstream` is none of those and falls to `return False` at `:888`. The measurement
   above shows it: `failure_count : 0` after a 503, where the GET arm reached `1`. **Jobvite can be
   returning 503 to every write in the estate and the breaker will never open, and will be actively
   held closed.**

### Why no test caught it

**No test in the suite drives a non-retryable method against a retryable status.** Every `POST` case
reaches a different branch:

- `tests/test_jobvite_client.py:259` - POST + HTTP 400 (a 4xx, falls through unwrapped)
- `tests/test_jobvite_client.py:408` - POST + HTTP 201 with a 409 envelope (a 4xx)
- `tests/test_resilience.py:522` - POST + a transport **timeout**, which raises
  `JobviteUnavailableError` and never reaches `:1710` at all
- `tests/test_resilience.py:553` - a structural read of `RETRYABLE_METHODS`

This is exactly the brief's shape 3 - *an assertion whose fixture cannot reach the branch it guards*
- and the same shape U7 itself found in A2, one mechanism over. The write path is asserted to reach
the transport once; it is never asserted to produce a correct error when it does.

### Suggested fix

Convert on the non-retrying branch too, so the private type has exactly one exit:

```python
# jobvite_client.py:1445-1456
if method.upper() not in RETRYABLE_METHODS:
    # ONE await, and no loop exists on this branch to run a second
    # one. That is the construction. The conversion is here because
    # `_attempt` wraps a retryable status whatever the method, and
    # this branch is the other place that wrapper has to come off.
    try:
        return await self._attempt(
            method, url, params=params, headers=headers,
            json_body=json_body, jobfeed=jobfeed, path=path,
        )
    except _RetryableUpstream as exc:
        raise exc.public_error() from None
```

Add the case the branch has never had - `test_a_write_that_meets_a_5xx_surfaces_502_not_500`,
asserting `problem_from_exception(...)["status"] == 502` and `["type"] ==
"/problems/external-service-error"` (asserting the type as well as the status, so a future
`about:blank` regression cannot pass), plus its 429 sibling asserting the 503 mapping. Add an
amputation row `A17 - the non-retrying branch's `_RetryableUpstream` conversion is deleted`; it is
vacuous today and must not be.

---

## R6-H3 - SURVIVING MUTATION: a 429 can stop counting toward the breaker and all 500 tests still pass.

**`src/fast_mcp_jobvite/services/jobvite_client.py:882`.**

```
881:    if isinstance(exc, JobviteRetryLaterError):
882:        return exc.counts_toward_breaker
```

**Mutation applied** (anchor asserted unique first, `grep -c "        return exc.counts_toward_breaker"`
-> `1`; landing proved by `git diff --stat` -> `1 file changed, 1 insertion(+), 1 deletion(-)`):

```python
        return False  # R6 MUTATION M-x: a 429 never counts
```

**Result, verbatim from the terminal:**

```
================= 500 passed, 6 deselected in 65.74s (0:01:05) =================
```

**The mutation SURVIVED the entire suite.** Baseline was `500 passed, 6 deselected in 58.90s`;
mutated is `500 passed`. Restored by `cp` from a backup, `cmp: IDENTICAL`, `git status --porcelain`
empty.

### What the mutation means

`_RetryableUpstream.public_error():812-817` builds the 429's public error with
`counts_toward_breaker=True`, and the comment at `:750-755` is explicit that *"A 429 is Jobvite
telling us it is unwell and counts."* The mutation makes that flag inert: **a rate-limited upstream
becomes invisible to the breaker.** Combined with R6-H1, it becomes worse than invisible - a 429
storm would hold the breaker closed by resetting it on every call.

Nothing observes it. The controls harness has M12 (*an exhausted budget trips the breaker*, KILLED)
and M13 (*a 4xx trips the breaker*, KILLED), which pin the two `False` directions. **Neither
direction of the `True` case is pinned.** `test_a_429_is_retried_and_then_mapped_to_503` at `:564`
asserts the status mapping and never reads `failure_count`. This is precisely the M14 shape U7 found
and wrote up - the only breaker case drove the *other* branch of the predicate - reappearing one
`isinstance` arm further down the same function.

### Suggested fix

Add `test_a_429_counts_toward_the_breaker_but_an_exhausted_budget_does_not`, driving
`DEFAULT_BREAKER_FAILURE_THRESHOLD` consecutive 429s and asserting `_JOBVITE_BREAKER.state ==
"open"`, paired in the same case with a budget arm asserting it stays closed - both arms together,
because asserting only the first passes against a predicate that counts everything. Add controls row
`M23b - the 429's counts_toward_breaker is ignored` pointing at it. This one row would have failed
before the first green run, which is the standard U7 set for its own harness.

---

# MEDIUM

## R6-M1 - `Retry-After` is clamped to the remaining budget and then slept out in full, buying an attempt that is refused before it reaches the transport. Measured.

**`src/fast_mcp_jobvite/services/jobvite_client.py:1536-1537`**:

```
1536:        if remaining is not None:
1537:            wait = min(wait, max(remaining, 0.0))
```

The clamp is right in intent - `:1518-1520` says an upstream asking for 900 seconds *"must not be
able to make us wait past a bound we promised the caller"*. But `min(900, remaining)` **is**
`remaining`, so we sleep the budget to zero and then `_attempt:1599-1605` refuses the attempt we
slept for, because `remaining <= 0`.

`/tmp/r6-probes/probe_wait_burns_budget.py`, budget 1.0s:

```
ARM 0c 404, NOT retryable (real control)  : elapsed=0.00s  budget=1.0s  outcome=JobviteUpstreamError
ARM 1c no Retry-After (jittered backoff) : elapsed=1.00s  budget=1.0s  outcome=503 JobviteRetryLaterError
ARM 1  Retry-After: 900 (>> the budget)  : elapsed=1.00s  budget=1.0s  outcome=503 JobviteRetryLaterError
```

`ARM 0c` is the control and returns in 0.00s, so the harness measures elapsed time rather than a
constant. **My first attempt at this probe used `ARM 1c` as the control and it was not one** - at a
1-second budget the local backoff (0.2 + 0.4 + 0.8) also exceeds the budget, so both arms read
1.00s and the arm discriminated nothing. The 404 arm is the one that separates them.

Scoped honestly: at the **60-second** default the attempt cap wins for the local backoff, so `ARM 1c`
is an artefact of the small budget and is NOT the finding. **`ARM 1` holds at any budget**, because
the clamp is `min(retry_after, remaining)` and a `Retry-After` larger than the budget always yields
exactly `remaining`. The caller waits the full 60 seconds for a 503 that was already decided.

**Suggested fix.** Treat "the wait would consume the budget" as a stop condition rather than a wait:

```python
# jobvite_client.py:1536-1537
if remaining is not None:
    if wait >= remaining:
        # The upstream is asking for longer than we have. Sleeping it
        # out buys an attempt `_attempt` refuses before the transport
        # sees it, so stop now and let the budget's 503 be the answer.
        return 0.0
    wait = min(wait, max(remaining, 0.0))
```

Returning `0.0` lets `stop_after_delay` fire on the next loop rather than after a full-budget sleep.
Pin it with a case asserting elapsed wall time is small when `Retry-After` exceeds the budget - and
assert on the DEADLINE rather than on measured elapsed where possible, the way U7's
`test_a_whole_scan_shares_one_budget_rather_than_one_per_page` does, since a mock transport answers
in microseconds.

## R6-M2 - arm 1c of the breaker rejection probe is tautological: it is satisfied by its own search-term list. Measured.

**`scripts/probe-breaker-call-path.py:265`** - `control_names =
scheduling_names_in_source(sys.modules[__name__])` - searching the probe's own source for
`SCHEDULING_NAMES`, which is **defined in that same source at `:77-86`**.

`/tmp/r6-probes/probe_arm1c_tautology.py`:

```
ARM A - names found in the probe's FULL source (what arm 1c reads):
    ['threading', 'Timer', 'call_later', 'call_at', 'create_task', 'ensure_future', 'sched', 'sleep']  (8/8)
ARM A - names found once docstrings/comments/the NAMES tuple are cut:
    ['threading', 'Timer', 'sched', 'sleep']  (4/8)
    exercised by nothing: ['call_at', 'call_later', 'create_task', 'ensure_future']

ARM B - a file containing ONLY the term list, zero scheduling code:
    arm 1c's predicate finds 8/8 -> PASSES (control is tautological)
```

**Four of the eight terms are present only as their own definition** - the probe's executable code
never uses `call_later`, `call_at`, `create_task` or `ensure_future`; `call_later` appears solely in
prose explaining why it was abandoned. And of the four that survive the cut, `sched` is a substring
false-positive on the words *scheduling*/*scheduled*, so the probe genuinely exercises **three**:
`threading`, `Timer`, `sleep`.

Arm B is the falsifying case: a file consisting of nothing but `SCHEDULING_NAMES = (...)` - zero
scheduling of any kind - passes the control 8/8. **A control that cannot fail cannot be told from
one that does not test its subject**, which is the sentence the probe's own docstring at `:38-42`
uses to justify arm 1c's existence.

The probe is still right that `circuitbreaker` schedules nothing - R6 confirms that by reading
`circuitbreaker.py:236-240`, where `state` is a property computing `STATE_HALF_OPEN` from
`open_remaining` with no writer anywhere. **The verdict stands; the control does not support it.**

**Suggested fix.** Run the control against a module that uses schedulers *without* naming the list.
`asyncio.base_events` contains `call_later`, `call_at` and `sleep`; `asyncio.tasks` contains
`create_task` and `ensure_future`; the `TimerDrivenBreaker` class covers `threading` and `Timer`:

```python
CONTROL_MODULES = ("asyncio.base_events", "asyncio.tasks", "threading")
missing = [
    n for n in SCHEDULING_NAMES
    if not any(n in inspect.getsource(importlib.import_module(m))
               for m in CONTROL_MODULES)
]
# arm 1c PASSES only when `missing` is empty AND the probe's own
# SCHEDULING_NAMES literal is excluded from every search.
```

and exclude the `SCHEDULING_NAMES` block from `scheduling_names_in_source` by slicing the tuple's own
line range out before searching, so no file can pass by containing the question.

## R6-M3 - `Retry-After: 0` is trusted, and disables jitter entirely.

**`src/fast_mcp_jobvite/services/jobvite_client.py:860`** - `return value if value >= 0 else None`.

`0` is `>= 0`, so `_retry_after_seconds` returns `0.0`, and `_wait_for_retry:1532-1533` takes it as
`wait` in preference to the jittered schedule. **Every retry then fires with zero delay**, which is
`backend/resilience.md:79-82`'s stated failure - *"fixed-interval or jitter-free retries synchronize
clients into a thundering herd that amplifies the outage"* - produced on demand by a header value
the upstream controls.

This is the brief's shape 6: the branch fails closed on error (`ValueError -> None`) and open on the
empty-ish value. The test that covers this function,
`test_a_retry_after_we_cannot_trust_is_ignored_rather_than_guessed` at `tests/test_resilience.py:622-636`,
checks **absent, malformed, negative and the HTTP-date form** - and not `"0"`, and not `""`. Its
docstring says *"Absent, malformed and negative all return `None`"*, which is a true statement about
a set that does not include the interesting member.

**Suggested fix.** Floor the wait rather than rejecting the header, so back-pressure is still
honoured but jitter cannot be switched off:

```python
# jobvite_client.py:860
# A zero or near-zero hint is honoured as "very soon", not as "now":
# a jitter-free retry is the thundering herd `resilience.md:79-82`
# forbids, and the value is upstream-controlled.
return max(value, DEFAULT_RETRY_INITIAL_BACKOFF) if value >= 0 else None
```

and add `"0"` and `""` to the case at `:622`, asserting the floor rather than `None` for `"0"`.

---

# NITS

## R6-N1 - `docs/worklogs/U7-IMPL-REPORT.md` cites `config.py:203`; the line at `ec38835` is 228.

§6 and finding F1 both say *"`config.py:203` declares `outbound_rate_limit`"*. Measured in the
pinned worktree:

```
$ grep -n "outbound_rate_limit" src/fast_mcp_jobvite/config.py
228:    outbound_rate_limit: int = Field(default=6, ge=1)
```

`ADR-0025` (on `main` at `0fe4628`, not present at `ec38835`) quotes the same grep and has **228**,
correctly. So the report's number was true on the branch base and decayed across the merge - the
"derived record decays where no step's check looks" shape, and the reason a citation should name a
unique subject rather than a line.

**Suggested fix:** repoint both occurrences in `U7-IMPL-REPORT.md` to `config.py:228`, or better,
drop the number and cite `config.py`'s `outbound_rate_limit` field by name, which is unique in the
file.

## R6-N2 - `_RetryableUpstream`'s docstring states an invariant the code does not hold.

`jobvite_client.py:781-790`: *"Module-private and it never reaches a caller ... nothing else may see
it."* R6-H2 measures it reaching a caller. Even after H2's fix lands, the sentence is an assertion no
gate checks.

**Suggested fix:** once H2 is fixed, rewrite the sentence in place (not appended to) to name the two
converters that make it true - *"`_attempt_with_retry` converts it on both branches, `:1448` and
`:1509`, and those are the only two exits"* - so the next reader can check the claim against two
named sites instead of against an adjective.

## R6-N3 - arm 1's term list has no entry for `call_soon`, `signal`, `run_in_executor` or `to_thread`, and `inspect.getsource` would go quiet on a packaged release.

`scripts/probe-breaker-call-path.py:77-86`. Two gaps, both in the "a hand-kept list is blind to the
member nobody added" family the brief names as EIGHT-times measured here:

1. **Missing terms.** `call_soon` and `call_soon_threadsafe` are asyncio's most basic schedulers and
   are the immediate neighbours of the `call_later` the probe *did* think of. `signal`/`alarm`,
   `run_in_executor`, `to_thread` and `concurrent` are also absent. A `circuitbreaker` release that
   expired half-open state from `loop.call_soon` would pass arm 1 silently.
2. **The container, not the list.** `scheduling_names_in_source` calls
   `inspect.getsource(circuitbreaker)`. `circuitbreaker` is a single module today, so this reads the
   whole library. If a future release ships as a package, `inspect.getsource` returns only
   `__init__.py` and the search becomes a clean empty over an incomplete corpus - indistinguishable
   from a real absence, which is the exact failure this project has measured three times.

Not graded higher because R6 independently confirmed the verdict by reading the mechanism
(`circuitbreaker.py:236-240`).

**Suggested fix:** add the missing terms, and enumerate the container rather than one module -
walk `pathlib.Path(circuitbreaker.__file__).parent` for `*.py` when `__file__` ends in
`__init__.py`, and assert the file count searched is non-zero so a packaged release fails loudly
instead of passing quietly.

---

## Things the brief asked about that I checked and did NOT find a defect in

Recorded so nobody re-derives them.

- **"Can a breaker-refused call consume budget?"** No. `request:1316` opens the scope and
  `_through_breaker:1368-1374` raises before any await, so a refusal costs no measurable budget, and
  a refusal inside a `scan` aborts rather than looping. The converse turned out to be the interesting
  one and is R6-H1.
- **What else the `0.01s` shortening changes.** `_recovery_timeout` feeds `open_remaining`, which
  feeds `state`, `opened`, `open_until` and `_breaker_retry_after` - so while it is patched, every
  breaker-window quantity is 0.01s. In `tests/test_resilience.py:759-806` this is contained: the
  patch is applied at `:782`, **after** the `closed->open` line is produced at the real 30s, and
  restored in `finally` at `:789-791`. The `closed->open` assertion at `:806` therefore reads a
  counter produced under the real value. The transition SEQUENCE the case asserts is the same one a
  30-second window produces. What the shortening does hide is the rejection behaviour *during* the
  open window, which is covered separately at `:722`. **No finding.**
- **ADR-0025's arithmetic** (in scope per the brief; the ADR is on `main` at `0fe4628`, not at
  `ec38835`). Re-derived independently: 1,240 records at a page size of `min(500, 50) = 50` is
  `ceil(1240/50) = 25` requests; at 6/min the 25th is issued at `24 x 10s = 240s`; against a 60s
  budget the 7th is issued at `t = 60s`, so "dies at roughly request 7" is right; at a page size of
  500, `ceil(1240/500) = 3` requests, `2 x 10s = 20s`. **Every figure in ADR-0025 checks out.** The
  §7.7 example states the total (`showing 50 of 1,240`), so no 26th probe request is needed and 25
  is not an undercount.
- **A non-idempotent call reaching the retrying branch.** The `method.upper()` dispatch at `:1445`
  holds for every caller at `ec38835` - `scan` -> `:1877` and `tools/jobs.py:368` both pass `GET`.
  The hole is the opposite direction and is R6-H2.
- **U7's two harnesses are wired.** Verified in `ci.yml` at `ec38835`, both through
  `scripts/ci-harness-gate.sh`. Not assumed.

---

## What I could NOT verify

Kept for what I could not settle, not for what I did not try.

- **Whether R6-H1's suggested fix is complete against `circuitbreaker`'s half-open semantics.** I
  proved the reset happens and proved the two exclusion assertions cannot see it. I did NOT run the
  proposed fix, because I am read-only on `src/` and the fix is more than a one-line mutation - a
  restructure I applied and measured would be an implementation, not a review. **The fixer must
  re-run `probe_breaker_reset.py` after the change and require `4 -> 4`, not `4 -> 0`**, and must
  check the `half_open` case separately: a neutral exception in half-open must leave the breaker
  half-open rather than closing it, and I have not established what `circuitbreaker` does there
  under the proposed shape.
- **Whether R6-H2 is reachable from a tool today.** `create_candidate` does not exist at `ec38835`,
  and no `src/` caller passes a non-retryable method. The defect is therefore latent, and its
  severity rests on U8/U12 giving it a caller - which the plan says they will. I could not establish
  a live path, and I am not claiming one.
- **Whether the in-process, per-replica breaker is acceptable in deployment.** Unchanged from U7's
  own note; nothing here establishes the replica count. R6-H1 makes it worse in a way that scales
  with replicas (each replica's counter is independently resettable) but I have no deployment fact to
  size that with.
- **Whether any of `docs/OBLIGATIONS.md`'s 7 "recorded as absent" anchors are U7's.** I ran the
  checker rather than parking it - verbatim: `Mappings: 31 | anchors verified against their subject:
  24 | recorded as absent: 7` / `Every mapped anchor still contains its subject. OK.`, exit **0**.
  What I could not settle is the narrower question U7 raised: the checker asserts every *mapped*
  anchor still contains its subject, which says nothing about whether an absent row's obligation is
  satisfied. Deciding that needs a reading of the 7 rows against their clauses, which is its own task
  and not R6's.
- **Whether a `Retry-After` of `0` is something Jobvite would ever send.** R6-M3 is a property of our
  parser, measured against our own code. `DESIGN.md:361-364` records that no 429 has ever been
  observed from Jobvite at all, so nothing about the header's real values is knowable here.

---

## The probes, for reproduction

**All four are COMMITTED on this branch, under `docs/reviews/`** - not left in `/tmp`, because prose
about a measurement decays into a claim about one, and because a restart has destroyed exactly that
kind of artefact on this project before. `docs/reviews/` rather than `scripts/`, which I am read-only
on; it is where this project's other review probes already live
(`probe-r4-h3-live-arm-cannot-detect.py`, `probe-r4-unmutated-anchors.sh`).

Each is self-contained and run from the repo root as `uv run --frozen python <probe>`. **All four
were re-run from their committed paths after the copy** and all four exit 0:

| Probe | Proves |
|---|---|
| `docs/reviews/probe-r6-breaker-reset.py` | R6-H1: `4 -> 0` on a non-outage, `4 -> 5` on the outage control |
| `docs/reviews/probe-r6-post-escape.py` | R6-H2: `_RetryableUpstream` / 500 on POST vs `JobviteUpstreamError` / 502 on GET |
| `docs/reviews/probe-r6-arm1c-tautology.py` | R6-M2: 4/8 terms exercised; a term-list-only file passes 8/8 |
| `docs/reviews/probe-r6-wait-burns-budget.py` | R6-M1: 1.00s of a 1.0s budget slept out; 0.00s on the non-retryable control |

They are **not wired into CI**, deliberately: `probe-r6-breaker-reset.py` and
`probe-r6-post-escape.py` currently *demonstrate defects*, so gating on them would gate on the bugs
staying. Once H1 and H2 are fixed, both should be inverted into assertions and wired the way
`test_the_breaker_rejection_test_still_passes_against_the_pinned_library` wires
`probe-breaker-call-path.py` - which is the mechanism U7 built for exactly this and the reason its
own rejection test cannot go stale.

## Housekeeping

- The worktree `/tmp/code-review-r6-work` is removed as the last step after the push (stated in the
  `SendMessage`).
- No edits to `src/`, `tests/` or `scripts/`. The one mutation was applied and restored inside the
  pinned worktree, verified with `cmp` and an empty `git status --porcelain`.
- `docs/OBLIGATIONS.md` was not touched and no anchor moved; `check-harness-anchors.py --self-check
  --floor 239` exits 0 after the review as it did before.
