#!/usr/bin/env bash
# U7 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything still
#                    report success?
#
# Amputation has exposed a vacuous assertion in every unit built on this
# project so far. SURVIVORS ARE THE OUTPUT, not the failure: for each
# row this prints the counts and NAMES every test that still passed, so
# the report can say which assertions survived and why.
#
# THE WHOLE SUITE IS RUN FOR EACH ROW, not one selector. That is the
# difference from the mutation harness: a mutation asks whether ONE
# named case notices, and an amputation asks whether ANYTHING does. A
# row run against its own case would answer the mutation question again.
#
# WHAT IS DELIBERATELY NOT AMPUTATED HERE, and it is worth saying rather
# than leaving as a gap someone rediscovers.
#
#   * The retry LOOP itself. Deleting `AsyncRetrying` and calling
#     `_attempt` once is not an amputation of a behaviour, it is the
#     `create_candidate` path, which A9's inverse already covers.
#   * The `finally` that clears the cookie jar, and the transport
#     `except` block. Both are U4's behaviours with U4's coverage; this
#     harness amputates U7's.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation that replaces a body with a constant can be the same
# size inside one second, in which case the interpreter reuses stale
# bytecode and the amputated code never runs.

# `-e` deliberately omitted: these harnesses read the exit code of a suite that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_resilience.py"
OUT=/tmp/u7-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

cp "$CLIENT" "$PRISTINE_DIR/client.py" ||
  { echo "COULD NOT TAKE PRISTINE COPY of $CLIENT"; exit 3; }

echo "########## BASELINE - the intact tree"
if ! uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 "$OUT"
  exit 3
fi
tail -1 "$OUT"
echo

TOTAL_SURVIVORS=0
APPLIED=0
ROWS=0
VACUOUS=0

# ---------------------------------------------------------------------------
# amputate <label> <file> <old> <new>
# ---------------------------------------------------------------------------
amputate() {
  local label="$1" file="$2" old="$3" new="$4"
  ROWS=$((ROWS + 1))

  echo "########## $label"

  # SC2155: declared and assigned separately.
  local backup
  backup="$BACKUP_DIR/${ROWS}_client.py"
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
    echo "  AMPUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi
  APPLIED=$((APPLIED + 1))

  # `timeout` is a guard, not a policy. Every row here is believed
  # bounded - the transport is `MockTransport` and answers instantly -
  # and a row that hangs anyway must report rather than stall the gate.
  timeout 300 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA \
    >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/client.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 300s - this row is unbounded. Move it to the"
    echo "  mutation harness, where the change is bounded."
  fi

  tail -1 "$OUT" | sed 's/^/  /'

  # THE VACUOUS-ROW GATE. The verdict is the RUN'S EXIT CODE, not
  # `grep -c "^FAILED"`: that grep misses ERROR entirely, and a
  # collection error is a row going red for a real reason.
  if [ "$rc" -eq 0 ]; then
    echo "  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red."
    echo "      Every assertion below survived. This row measures nothing."
    VACUOUS=$((VACUOUS + 1))
  fi

  local survivors
  survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    local n
    n=$(printf '%s\n' "$survivors" | wc -l)
    TOTAL_SURVIVORS=$((TOTAL_SURVIVORS + n))
    echo "  survivors: $n"
    printf '%s\n' "$survivors" | sed 's/^/    /'
  fi
  echo
}

# ===========================================================================
# THE BUDGET - the behaviour that did not exist before this unit, so
# every row here amputates something with no prior coverage at all.
# ===========================================================================

amputate "A1  the budget scope is never opened around a single request" \
  "$CLIENT" \
  '        with outbound_budget_scope(self._outbound_budget_seconds):
            # THE BREAKER IS OUTERMOST' \
  '        if True:
            # THE BREAKER IS OUTERMOST'

amputate "A2  the budget scope is never opened around a scan" \
  "$CLIENT" \
  '        with outbound_budget_scope(self._outbound_budget_seconds):
            return await self._scan_pages(' \
  '        if True:
            return await self._scan_pages('

amputate "A3  the pre-attempt budget check is deleted" \
  "$CLIENT" \
  '        remaining = outbound_budget_remaining()
        if remaining is not None and remaining <= 0:
            raise JobviteRetryLaterError(
                UNAVAILABLE_BUDGET_DETAIL,
                retry_after=None,
                counts_toward_breaker=False,
            )

        try:
            response = await self._client.request(' \
  '        remaining = outbound_budget_remaining()

        try:
            response = await self._client.request('

amputate "A4  the per-attempt timeout clamp is deleted" \
  "$CLIENT" \
  '        bound = max(remaining, 0.0)
        return httpx2.Timeout(' \
  '        bound = 10_000.0
        return httpx2.Timeout('

amputate "A5  stop_after_delay is deleted, leaving only the attempt cap" \
  "$CLIENT" \
  '            | stop_after_delay(max(remaining or 0.0, 0.0))' \
  '            | stop_after_attempt(self._retry_max_attempts)'

# R6-M1's third arm. Deleting it puts the behaviour back to the clamp
# alone, which sleeps the whole budget away and buys an attempt
# `_attempt` refuses before the transport sees it.
amputate "A19 the Retry-After-exceeds-budget stop arm is deleted" \
  "$CLIENT" \
  '            | _retry_after_exceeds_budget' \
  '            | stop_after_attempt(self._retry_max_attempts)'

# ===========================================================================
# THE BREAKER - DESIGN.md:64-68 names it as NEVER EXECUTED. These rows
# are what turn that from a claim into a measurement.
# ===========================================================================

# THE CALL NO LONGER RUNS INSIDE THE BREAKER'S CONTEXT (R6-H1), so
# "remove the breaker from the call path" is now "never tell it about a
# failure". Same amputation, one layer down: the counter can never
# reach the threshold and the circuit can never open.
amputate "A6  the breaker is never told about a failure and can never open" \
  "$CLIENT" \
  '            with _JOBVITE_BREAKER:
                raise' \
  '            if True:
                raise'

# THE OTHER HALF OF THE SAME MECHANISM, and it did not exist before
# R6-H1's fix: a success is now what resets the counter, explicitly.
# Deleting it leaves a breaker that only ever accumulates, so a server
# that recovers stays one failure away from open forever.
amputate "A18 a success no longer resets the breaker" \
  "$CLIENT" \
  '            with _JOBVITE_BREAKER:
                pass' \
  '            if True:
                pass'

amputate "A7  the open-breaker short circuit is deleted" \
  "$CLIENT" \
  '        _report_breaker_state()
        if _JOBVITE_BREAKER.opened:
            raise JobviteRetryLaterError(' \
  '        _report_breaker_state()
        if False:
            raise JobviteRetryLaterError('

amputate "A8  the outage predicate is deleted and nothing is an outage" \
  "$CLIENT" \
  '    if isinstance(exc, JobviteRetryLaterError):
        return exc.counts_toward_breaker' \
  '    if True:
        return False'

# ===========================================================================
# CORRELATED LOGGING - §8 #13, DESIGN.md:654-660
# ===========================================================================

amputate "A9  the retry line is not written at all" \
  "$CLIENT" \
  '            before_sleep=_log_retry_attempt,' \
  '            before_sleep=None,'

amputate "A10 request_id is dropped from the retry line" \
  "$CLIENT" \
  '        error_type=type(exc).__name__ if exc is not None else "none",
        request_id=request_id_var.get(),' \
  '        error_type=type(exc).__name__ if exc is not None else "none",'

amputate "A11 the breaker transition line is not written at all" \
  "$CLIENT" \
  '    logger.warning(
        "jobvite breaker transition",' \
  '    _breaker_reported_state = current
    return
    logger.warning(
        "jobvite breaker transition",'

amputate "A12 request_id is dropped from the transition line" \
  "$CLIENT" \
  '        failure_count=_JOBVITE_BREAKER.failure_count,
        request_id=request_id_var.get(),' \
  '        failure_count=_JOBVITE_BREAKER.failure_count,'

# ===========================================================================
# THE RETRY SELECTION AND THE WRITE EXCLUSION
# ===========================================================================

amputate "A13 the method dispatch is deleted and everything retries" \
  "$CLIENT" \
  '        if method.upper() not in RETRYABLE_METHODS:' \
  '        if False:'

amputate "A14 the retry predicate is deleted and everything retries" \
  "$CLIENT" \
  '    if isinstance(exc, JobviteRetryLaterError):
        return False
    return isinstance(exc, _RetryableUpstream | JobviteUnavailableError)' \
  '    return True'

amputate "A15 the 5xx-to-retryable wrapping is deleted" \
  "$CLIENT" \
  '            if _is_retryable_status(exc.upstream_status):
                raise _RetryableUpstream(' \
  '            if False:
                raise _RetryableUpstream('

# R6-H2. The non-retrying branch's conversion is deleted, so the
# module-private `_RetryableUpstream` leaves `request()` again and
# ADR-0017 maps it to `/problems/internal-error` 500 with the private
# class name in the detail. IT WAS VACUOUS BEFORE THE CASES THAT NAME
# IT: no test in the suite drove a non-retryable METHOD against a
# retryable STATUS.
amputate "A17 the non-retrying branch's _RetryableUpstream conversion is deleted" \
  "$CLIENT" \
  '            except _RetryableUpstream as exc:
                raise exc.public_error() from None' \
  '            except _RetryableUpstream:
                raise'

amputate "A16 Retry-After parsing is deleted and always returns None" \
  "$CLIENT" \
  '    raw = headers.get("Retry-After")
    if raw is None:
        return None' \
  '    raw = headers.get("Retry-After")
    if True:
        return None'

# ===========================================================================
# THE SCAN'S BOUNDS. `scan()` had NO bound at all before this unit, so
# these two rows restore the state R5-H2 measured - and the suite's own
# handlers abort at SCAN_PROBE_ABORT so a row cannot hang the gate.
# ===========================================================================

amputate "A20 the zero-progress break is deleted (R5-H2 reopens)" \
  "$CLIENT" \
  '            if len(seen) + unidentified == progress_before:
                stalled = True' \
  '            if False:
                stalled = True'

amputate "A21 the record ceiling is deleted" \
  "$CLIENT" \
  '            if len(items) >= MAX_SCAN_RECORDS:
                ceiling_hit = True' \
  '            if False:
                ceiling_hit = True'

amputate "A22 neither bound makes the result incomplete" \
  "$CLIENT" \
  '            or stalled
            or ceiling_hit
        )' \
  '            or False
        )'

echo "ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
echo "VACUOUS ROWS: $VACUOUS"
echo "TOTAL SURVIVING ASSERTIONS ACROSS ALL ROWS: $TOTAL_SURVIVORS"
if [ "$ROWS" -eq 0 ] || [ "$APPLIED" -ne "$ROWS" ]; then
  echo "GATE: an anchor failed to apply - this run is not a measurement."
  exit 3
fi
if [ "$VACUOUS" -gt 0 ]; then
  echo "GATE: $VACUOUS row(s) deleted a behaviour and nothing went red."
  exit 1
fi
echo "GATE: every row was noticed by at least one assertion."
exit 0
