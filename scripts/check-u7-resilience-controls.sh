#!/usr/bin/env bash
# U7 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the resilience behaviour it claims to
# check is wrong, which is the vacuous-assertion shape this project has
# found in every unit so far.
#
# The AMPUTATION harness beside this one asks the different question -
# remove the behaviour ENTIRELY, does anything still report success -
# and its survivors are output rather than failure.
#
# THE ROWS THAT MATTER MOST HERE ARE M1 AND M13, and they are the two
# halves of one boundary. `backend/resilience.md:92-94` says 4xx must
# not be retried and DESIGN.md:366-367 says 4xx must not trip the
# breaker; M1 makes a 4xx retryable and M13 makes it trip the breaker.
# A suite that only checked "a 5xx is retried and trips the breaker"
# kills neither, because both mutations leave that behaviour intact and
# only WIDEN it - and widening is the direction nobody notices, since
# every existing case still passes.
#
# M22 IS THE ONE NO SINGLE-CALL TEST CAN CATCH. It swaps the composition
# order so the retry loop sits OUTSIDE the breaker. Both orders return
# the same value on every call until the breaker opens, which is why the
# case that kills it reads the CALL GRAPH rather than driving a call.
#
# M14 IS THE ROW THAT ALREADY PAID FOR THIS HARNESS. It survived on its
# first run: it deletes the branch that makes a dead upstream open the
# circuit, and the only breaker case at the time drove a 5xx, which
# reaches the OTHER branch. The suite gained
# `test_repeated_transport_failures_trip_the_breaker` because of it.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains, and this harness is untracked until it is
# committed.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and a mutation that swaps one value can be the same size inside one
# second - in which case the interpreter reuses stale bytecode, the
# mutated code never runs, and the row reports a clean survivor that is
# an instrument fault rather than a finding.

# `-e` deliberately omitted: these harnesses read the exit code of a suite that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_resilience.py"
OUT=/tmp/u7-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPY, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can detect only a failed
# `cp`, never "the tree still carries this row's mutation".
cp "$CLIENT" "$PRISTINE_DIR/client.py" ||
  { echo "COULD NOT TAKE PRISTINE COPY of $CLIENT"; exit 3; }

echo "########## BASELINE - the intact tree"
# BOUNDED, exactly as the rows below are, and for the same reason. This was
# unbounded until this was measured: `U9 HTTP hardening amputation` takes
# 24m19s and PASSES, against 27-77s for the steps either side of it. Where one
# step legitimately runs for 24 minutes, a real hang is indistinguishable from
# normal slowness for as long as anyone will wait.
# `timeout` returns 124, which is why a hang and a red suite get DIFFERENT
# messages and DIFFERENT exit codes: "never finished" and "finished red" need
# different diagnoses, and this project has been bitten before by two states
# that render identically.
timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "       This is not a red suite. Nothing below ran, and the harness is"
  echo "       not at fault until this is explained. Last 20 lines:"
  tail -20 "$OUT"
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 "$OUT"
  exit 3
fi
tail -1 "$OUT"
echo

FIRED=0
TOTAL=0

# ---------------------------------------------------------------------------
# mutate <label> <file> <test-selector> <old> <new>
# ---------------------------------------------------------------------------
mutate() {
  local label="$1" file="$2" selector="$3" old="$4" new="$5"
  TOTAL=$((TOTAL + 1))

  echo "########## $label"
  echo "  target: $selector"

  # DOES THE SELECTOR STILL RESOLVE? pytest exits 4 when a selector
  # matches nothing, and this harness treats ANY non-zero exit as a
  # kill - so a renamed or misspelled test would report KILLED on every
  # run, forever, while running nothing. TOTAL is already incremented,
  # so returning here makes fired != total and the run exits 1.
  timeout 120 uv run --frozen pytest "$selector" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1
  local probe_rc=$?
  if [ "$probe_rc" -ne 0 ]; then
    if [ "$probe_rc" -eq 124 ]; then
      echo "  SELECTOR PROBE TIMED OUT after 120s - collection NEVER FINISHED."
      echo "  Read this, not the lines below: a hang, not a rename."
    fi
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  This row has been reporting KILLED without running. Fix the harness."
    echo
    return
  fi

  # SC2155: declared and assigned separately, so a failing `cp` cannot
  # be masked by `local`'s own exit status.
  local backup
  backup="$BACKUP_DIR/${TOTAL}_client.py"
  cp "$file" "$backup" || { echo "  COULD NOT BACK UP"; echo; return; }

  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
n = s.count(old)
if n != 1:
    print(f"  ANCHOR NOT UNIQUE ({n} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  then
    echo "  COULD NOT APPLY - the anchor moved. Fix the harness."
    cp "$backup" "$file"
    echo
    return
  fi

  if cmp -s "$file" "$backup"; then
    echo "  MUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi

  timeout 300 uv run --frozen pytest "$selector" -q -p no:cacheprovider \
    >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/client.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 300s - this row is unbounded. Rewrite it."
  fi

  if [ "$rc" -ne 0 ]; then
    FIRED=$((FIRED + 1))
    echo "  KILLED - the named test went red, as it must"
  else
    echo "  *** SURVIVED *** the named test passed against the mutation."
    echo "      The assertion does not check what its name claims."
    tail -1 "$OUT" | sed 's/^/      /'
  fi
  echo
}

# ===========================================================================
# RETRY SELECTION - the predicate, and the boundary it must not widen
# ===========================================================================

# `backend/resilience.md:92-94`: 4xx "must surface immediately". Widening
# the floor to 400 makes every caller error a retry, which quadruples the
# load a bad candidate id puts on Jobvite and delays the error the caller
# actually needs.
mutate "M1  a 4xx becomes retryable" \
  "$CLIENT" \
  "$SUITE::test_a_4xx_is_not_retried_and_surfaces_immediately" \
  '    return status >= SERVER_ERROR_STATUS_FLOOR or status == RATE_LIMITED_STATUS' \
  '    return status >= ERROR_STATUS_THRESHOLD'

# The other direction: a 5xx stops being retried at all, which is the
# transient failure DESIGN.md:359-361 names first.
mutate "M2  a 5xx stops being retryable" \
  "$CLIENT" \
  "$SUITE::test_a_5xx_is_retried_to_the_attempt_cap" \
  '    if status is None:
        return False
    return status >= SERVER_ERROR_STATUS_FLOOR' \
  '    if status is None:
        return False
    return status >= 600'

# DESIGN.md:373-383: a 429 is "retried and then mapped to 503". Dropping
# the mapping tells a caller the upstream ERRORED when it asked us to
# slow down, and 502 is not a status a client backs off on.
mutate "M3  a 429 surfaces as 502 instead of 503" \
  "$CLIENT" \
  "$SUITE::test_a_429_is_retried_and_then_mapped_to_503" \
  '        if self.cause.upstream_status == RATE_LIMITED_STATUS:' \
  '        if False:'

# `backend/resilience.md:95-97`: honour the server's back-pressure. This
# reverts to the local jittered schedule, which is the client deciding
# it knows better than the upstream that just throttled it.
mutate "M4  Retry-After is ignored in favour of the local backoff" \
  "$CLIENT" \
  "$SUITE::test_retry_after_is_honoured_over_the_local_backoff" \
  '            wait = exc.retry_after' \
  '            wait = _JITTERED_BACKOFF(state)'

# A negative or malformed Retry-After becomes a wait we invented.
mutate "M5  a negative Retry-After is trusted" \
  "$CLIENT" \
  "$SUITE::test_a_retry_after_we_cannot_trust_is_ignored_rather_than_guessed" \
  '    return max(value, DEFAULT_RETRY_INITIAL_BACKOFF) if value >= 0 else None' \
  '    return max(value, DEFAULT_RETRY_INITIAL_BACKOFF)'

# R6-M3. `0` is `>= 0`, so it used to be returned verbatim and
# `_wait_for_retry` preferred it to the jittered schedule - every retry
# then fired with NO delay, which is `backend/resilience.md:79-82`'s
# thundering herd switched on by a header the UPSTREAM controls. This
# row reverts the floor. Its NEW text is what the code used to say, and
# the case that covered this function checked absent, malformed,
# negative and the HTTP-date form - a true statement about a set with
# no `0` in it.
mutate "M25 a Retry-After of 0 is trusted and disables jitter" \
  "$CLIENT" \
  "$SUITE::test_a_retry_after_we_cannot_trust_is_ignored_rather_than_guessed" \
  '    return max(value, DEFAULT_RETRY_INITIAL_BACKOFF) if value >= 0 else None' \
  '    return value if value >= 0 else None'

# R6-M1. The stop condition becomes the old clamp again, so a
# `Retry-After` larger than the budget sleeps the budget to zero and
# buys an attempt `_attempt` refuses before the transport sees it.
mutate "M24 a Retry-After we cannot afford is slept out anyway" \
  "$CLIENT" \
  "$SUITE::test_a_retry_after_we_cannot_afford_stops_instead_of_sleeping" \
  '    return remaining is not None and exc.retry_after >= remaining' \
  '    return False'

# ===========================================================================
# §8 #21 - `create_candidate` excluded BY CONSTRUCTION. The measurement
# this prevents is DESIGN.md:365's one call, FOUR rows created.
# ===========================================================================

mutate "M6  POST joins the retryable methods" \
  "$CLIENT" \
  "$SUITE::test_a_write_that_times_out_reaches_the_transport_exactly_once" \
  'RETRYABLE_METHODS: Final = frozenset({"GET", "HEAD"})' \
  'RETRYABLE_METHODS: Final = frozenset({"GET", "HEAD", "POST"})'

# The dispatch is inverted rather than widened: reads stop retrying and
# writes start. A suite that only counted POST rows would still pass.
mutate "M7  the method dispatch is inverted" \
  "$CLIENT" \
  "$SUITE::test_the_same_failure_on_a_read_IS_retried" \
  '        if method.upper() not in RETRYABLE_METHODS:' \
  '        if method.upper() in RETRYABLE_METHODS:'

# ===========================================================================
# THE TOTAL OUTBOUND BUDGET (DESIGN.md:392-394). It did not exist before
# this unit, so every row here is a behaviour with no prior coverage.
# ===========================================================================

# A nested scope restarts the clock, so a 25-page scan costs 25 budgets
# and the bound becomes `pages x seconds` - unbounded in exactly the
# direction the budget exists to bound.
mutate "M8  a nested budget scope restarts the deadline" \
  "$CLIENT" \
  "$SUITE::test_a_nested_scope_keeps_the_outer_deadline" \
  '    deadline = existing if existing is not None else monotonic() + seconds' \
  '    deadline = monotonic() + seconds'

# The deadline leaks into the next invocation on a reused worker task -
# the same leak `correlation.request_id_scope` documents for the id, and
# the second invocation inherits a budget that is already spent.
mutate "M9  the deadline is not reset when its scope closes" \
  "$CLIENT" \
  "$SUITE::test_the_deadline_does_not_leak_out_of_its_scope" \
  '        outbound_deadline_var.reset(token)' \
  '        pass'

# The per-attempt timeout stops being clamped, so the LAST attempt can
# buy a fresh 30-second read and outlive the budget by a factor of the
# read timeout. The budget then bounds when we stop RETRYING rather than
# how long the caller waits, which is not what DESIGN.md:392-394 says.
mutate "M10 the attempt timeout is no longer clamped to the budget" \
  "$CLIENT" \
  "$SUITE::test_an_attempt_timeout_is_clamped_to_what_the_budget_has_left" \
  '        if remaining is None:
            return self._timeout' \
  '        if True:
            return self._timeout'

# The budget stops being the authority on WHY a call ended, so a slow
# upstream that answered 503 twice surfaces as 502 - a true statement
# about the last attempt and the wrong answer to the caller's question.
mutate "M11 an exhausted budget surfaces as the last attempt's error" \
  "$CLIENT" \
  "$SUITE::test_a_slow_upstream_becomes_a_typed_503_not_an_unbounded_wait" \
  '            remaining = outbound_budget_remaining()
            if remaining is not None and remaining <= 0:' \
  '            remaining = outbound_budget_remaining()
            if False:'

# An exhausted budget starts counting toward the breaker, so one slow
# invocation can open the circuit for every other caller - a bound WE
# applied being read as evidence about Jobvite's health.
mutate "M12 an exhausted budget trips the breaker" \
  "$CLIENT" \
  "$SUITE::test_an_exhausted_budget_does_not_trip_the_breaker" \
  '        return exc.counts_toward_breaker' \
  '        return True'

# ===========================================================================
# THE BREAKER (DESIGN.md:366-370, §8 #23)
# ===========================================================================

# §8 #23's subject. A bad candidate id becomes a health signal and one
# caller typing an id wrong five times stops the server calling Jobvite
# for everybody.
mutate "M13 a 4xx trips the breaker" \
  "$CLIENT" \
  "$SUITE::test_repeated_4xx_does_not_trip_the_breaker" \
  '        return _is_retryable_status(exc.upstream_status)' \
  '        return True'

# The TRANSPORT arm of `_is_outage`: a dead upstream never opens the
# circuit. THIS ROW SURVIVED ON ITS FIRST RUN against
# `test_repeated_5xx_trips_the_breaker`, which drives a 5xx and so only
# ever exercises the status branch - so the row is real and the suite
# was one case short. `test_repeated_transport_failures_trip_the_breaker`
# was written because this survived, not the other way round.
mutate "M14 a dead upstream never trips the breaker" \
  "$CLIENT" \
  "$SUITE::test_repeated_transport_failures_trip_the_breaker" \
  '    if isinstance(exc, JobviteUnavailableError):
        # Every transport failure: connect, read, write, pool, protocol.
        return True' \
  '    if isinstance(exc, JobviteUnavailableError):
        return False'

# The open breaker stops short-circuiting, so calls queue against an
# upstream we have already concluded is down - the opposite of
# `backend/resilience.md:165-170`'s "fail fast".
mutate "M15 an open breaker still issues the request" \
  "$CLIENT" \
  "$SUITE::test_repeated_5xx_trips_the_breaker" \
  '        if _JOBVITE_BREAKER.opened:' \
  '        if False:'

# DESIGN.md:370's `retry_after` hint disappears, so a caller has no
# number to back off on and the 503 says only "later".
mutate "M16 the open breaker drops its retry_after hint" \
  "$CLIENT" \
  "$SUITE::test_an_open_breaker_and_an_outage_are_told_apart_by_detail" \
  '        _report_breaker_state()
        if _JOBVITE_BREAKER.opened:
            raise JobviteRetryLaterError(
                UNAVAILABLE_BREAKER_DETAIL,
                retry_after=_breaker_retry_after(),' \
  '        _report_breaker_state()
        if _JOBVITE_BREAKER.opened:
            raise JobviteRetryLaterError(
                UNAVAILABLE_BREAKER_DETAIL,
                retry_after=None,'

# The two 503s stop being distinguishable, which is the whole of
# DESIGN.md:367-370: "what distinguishes them is `detail`".
mutate "M17 an open breaker reports the outage detail" \
  "$CLIENT" \
  "$SUITE::test_an_open_breaker_and_an_outage_are_told_apart_by_detail" \
  'UNAVAILABLE_BREAKER_DETAIL: Final = (
    "We have stopped calling Jobvite because it has been failing. "
    "This is an open circuit breaker, not an upstream failure in flight."
)' \
  'UNAVAILABLE_BREAKER_DETAIL: Final = UNAVAILABLE_TRANSPORT_DETAIL'

# R6-H1. THE ROW THAT PINS "NEUTRAL" AGAINST "HEALTHY". Deleting the
# guard sends every declined exception into `with _JOBVITE_BREAKER:`,
# where `__exit__` calls `reset()` on it - which is the pre-fix
# behaviour, measured at 4 -> 0. The two exclusion cases beside it
# CANNOT kill this row: both start from a closed breaker and assert
# `failure_count == 0`, and `0` is what "not counted" and "reset to
# zero" both produce from a start of `0`. The case named here starts
# from `threshold - 1`, which is the only start the two hypotheses
# disagree about.
mutate "M23 a non-outage RESETS the breaker instead of being ignored" \
  "$CLIENT" \
  "$SUITE::test_a_non_outage_does_not_RESET_the_breakers_accumulated_failures" \
  '            if not _is_outage(type(exc), exc):
                raise' \
  '            if False:
                raise'

# R6-H3, and it SURVIVED THE WHOLE SUITE at 562 passed before the case
# named here existed. M12 and M13 pin the two `False` directions of this
# predicate arm; neither direction of the `True` case was pinned, so a
# 429 could stop counting toward the breaker with nothing noticing.
mutate "M23b a 429's counts_toward_breaker is ignored" \
  "$CLIENT" \
  "$SUITE::test_a_429_counts_toward_the_breaker_but_an_exhausted_budget_does_not" \
  '        return exc.counts_toward_breaker' \
  '        return False'

# ===========================================================================
# CORRELATED LOGGING (DESIGN.md:674-680, §8 #13)
# ===========================================================================

# The direction is reported backwards. Every line still looks
# well-formed - `open->closed` is a plausible string - which is why the
# case asserts the exact directions rather than that a `->` appeared.
mutate "M18 the transition direction is reported backwards" \
  "$CLIENT" \
  "$SUITE::test_every_breaker_transition_is_logged_with_direction_and_counter" \
  '        transition=f"{_breaker_reported_state}->{current}",' \
  '        transition=f"{current}->{_breaker_reported_state}",'

# The triggering counter becomes a constant. The line is still there,
# still carries a direction and a request_id, and tells an operator
# nothing about how close the threshold was.
mutate "M19 the transition line reports a constant counter" \
  "$CLIENT" \
  "$SUITE::test_every_breaker_transition_is_logged_with_direction_and_counter" \
  '        failure_count=_JOBVITE_BREAKER.failure_count,' \
  '        failure_count=0,'

# The attempt number stops being the attempt number. This is the row
# that the CONCURRENT case kills: it asserts each invocation produced
# the attempt numbers ITS OWN failure script called for, so a constant
# collapses both sets.
mutate "M20 the retry line reports a constant attempt number" \
  "$CLIENT" \
  "$SUITE::test_two_concurrent_invocations_each_log_their_own_request_id" \
  '        attempt=state.attempt_number,' \
  '        attempt=1,'

# THE URL REACHES A RETRY LINE. DESIGN.md:678-680: "a retry line is
# exactly where an unredacted URL would otherwise reach a log", because
# the v1 jobFeed URL carries `sc=` in its query string.
mutate "M21 the retry line carries the exception's full text" \
  "$CLIENT" \
  "$SUITE::test_no_retry_line_carries_a_url" \
  '        error_type=type(exc).__name__ if exc is not None else "none",' \
  '        error_type=str(exc),'

# ===========================================================================
# COMPOSITION ORDER (`backend/resilience.md:216-222`)
# ===========================================================================

# The retry loop moves OUTSIDE the breaker, so retry storms defeat the
# breaker and keep hammering a down upstream. Both orders return the
# same value on every call until the breaker opens, which is why the
# case that kills this reads the call graph.
mutate "M22 the breaker is skipped and the retry becomes outermost" \
  "$CLIENT" \
  "$SUITE::test_the_composition_order_is_timeout_then_retry_then_breaker" \
  '            return await self._through_breaker(' \
  '            return await self._attempt_with_retry('

# ===========================================================================
# THE SCAN'S BOUNDS (R5-H2, ADR-0024 Accepted). `scan()` had none at all.
# ===========================================================================

# The zero-progress break stops comparing and always sees progress, so a
# server that ignores `start` pages forever again. This is R5-H2 exactly.
mutate "M28 the zero-progress break can never fire" \
  "$CLIENT" \
  "$SUITE::test_a_server_that_ignores_start_is_bounded_after_one_wasted_page" \
  '            if len(seen) + unidentified == progress_before:' \
  '            if False:'

# Progress is measured AFTER the page is consumed instead of before, so
# the comparison is against itself and is always equal - the break then
# fires on EVERY page, including healthy ones, and every scan stops after
# one page reporting incomplete. The opposite failure from M23, and the
# one a suite with only the "it stops" case would miss.
mutate "M29 progress is sampled after the page, so the break fires always" \
  "$CLIENT" \
  "$SUITE::test_neither_bound_fires_on_healthy_paging" \
  '            progress_before = len(seen) + unidentified

            for item in page:' \
  '            for item in page:'

# The break stops setting `incomplete`, so a caller receives a truncated
# result that claims to be whole - the silent under-read DESIGN.md:508-516
# exists to prevent, arriving by a new road.
mutate "M30 a stalled scan reports itself as complete" \
  "$CLIENT" \
  "$SUITE::test_a_server_that_ignores_start_is_bounded_after_one_wasted_page" \
  '            or stalled
            or ceiling_hit' \
  '            or False
            or ceiling_hit'

# The ceiling counts PAGES instead of records, which is ADR-0024's own
# text and what its ruling corrected. At 50 records per page it admits
# ten times the records it admits at 500, so the bound stops being sane
# at both page sizes - the exact property the ADR requires of it.
mutate "M31 the ceiling counts pages instead of records" \
  "$CLIENT" \
  "$SUITE::test_the_record_ceiling_holds_at_both_50_and_500_per_page" \
  '            if len(items) >= MAX_SCAN_RECORDS:' \
  '            if pages >= MAX_SCAN_RECORDS:'

# The ceiling never fires, so a server that honours `start` and never
# runs out consumes memory until the process dies.
mutate "M32 the record ceiling can never fire" \
  "$CLIENT" \
  "$SUITE::test_a_server_that_never_runs_out_is_bounded_by_the_record_ceiling" \
  '            if len(items) >= MAX_SCAN_RECORDS:' \
  '            if len(items) >= MAX_SCAN_RECORDS * 10_000:'

echo "$FIRED/$TOTAL controls fired."

# THE ROW FLOOR. `TOTAL -gt 0` catches only TOTAL deletion; `FIRED -eq
# TOTAL` is satisfied by 0 == 0. Neither sees PARTIAL deletion, which is
# the realistic shape: a refactor that drops rows, or an anchor that
# stops matching so a row silently stops being counted. Lowering this
# number is a visible diff that has to be defended.
#
# DERIVED: this harness printed "26/26 controls fired." at 2b31e82, and
# that number went five rows stale WITHOUT FAILING ANYTHING. It was
# derived on `chore/row-floors`, which branched from 20e71ed; M28-M32
# were added by 1e55129 on `feat/scan-bound`; neither commit is an
# ancestor of the other, so both branches were right in isolation and
# the merge left a floor five rows below its harness. A floor derived on
# a branch is a measurement of that branch. Re-derived at 31 by task
# #91's control: removing six rows printed "25/26 ROWS", and
# `grep -cE '^mutate "'` says 31 independently.
ROW_FLOOR=31
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "$TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

[ "$FIRED" -eq "$TOTAL" ] && exit 0
exit 1
