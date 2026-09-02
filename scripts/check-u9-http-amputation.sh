#!/usr/bin/env bash
# U9 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything still
#                    report success?
#
# THIS MATTERS MORE HERE THAN ANYWHERE ELSE ON THIS PROJECT, and the
# plan says why: "No SS8 case owns this unit ... nothing in the coupling
# gate will miss them if they are dropped." Every other unit has a
# required case that goes red when its behaviour goes. U9 does not. A
# silently deleted test in this unit leaves every gate green, so this
# harness is standing where a required case stands elsewhere.
#
# EACH ROW RUNS THE TESTS THAT EXECUTED THE AMPUTATED LINES, selected
# from a coverage map the BASELINE below builds on this same tree
# (#238). The question is still "does ANYTHING notice": a test that
# never executes the amputated statements cannot go red because of
# them, so the covering set - which crosses unit boundaries, including
# somebody ELSE's assertion that happens to exercise this file - gives
# the identical verdict to a full-suite run at a fraction of the cost.
# Before #238 the full 888-test suite ran per row and this step alone
# cost 1270s in CI (run 33582613697). The fail-safe direction is wide:
# a row whose lines NO in-process test covered runs the FULL suite,
# and a selector precondition failure aborts the harness loudly.
#
# WHAT IS DELIBERATELY NOT AMPUTATED HERE:
#
#   * `config._check_transport`'s two refusals. They are U1's behaviour
#     with U1's coverage in `tests/test_boot.py`, and U9 only consumes
#     them.
#   * `resolve_request_id` itself. That is `audit.py`, which this unit
#     reads and does not write; U3's harness owns it. What is amputated
#     here is the TRANSPORT path that reaches it, which had no caller at
#     all before this unit.
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

# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. The names below are separate decisions,
# even where two of them share a value today.
BASELINE_TIMEOUT=900
ROW_TIMEOUT=900

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"
# ONLY 0 AND 1 ARE MEASUREMENTS (#254). One sourced copy, never retyped -
# the reasoning and the measurement that established it live in the file.
# shellcheck source=lib/verdict-guard.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/verdict-guard.sh" || {
  echo "::error::scripts/lib/verdict-guard.sh could not be sourced. Without it every"
  echo "         row below scores a broken pytest run as a perfect kill (#254). A"
  echo "         missing source is SILENT: 'command not found' is not fatal without"
  echo "         'set -e' (ADR-0023), shellcheck at --severity=warning does not"
  echo "         follow a source, and the harness would exit 0 with status=ok."
  exit 3
}

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

HARDENING="src/fast_mcp_jobvite/http_hardening.py"
SUITE="tests"
OUT=/tmp/u9-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

cp "$HARDENING" "$PRISTINE_DIR/http_hardening.py" ||
  { echo "COULD NOT TAKE PRISTINE COPY of $HARDENING"; exit 3; }

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
# The baseline doubles as the map build: --cov-context records which test
# executed which line, and each row below selects its tests from exactly
# this run of exactly this tree - the map cannot be stale by construction.
COVDB="$PRISTINE_DIR/covdb"
COVERAGE_FILE="$COVDB" timeout "$BASELINE_TIMEOUT" uv run --frozen pytest $SUITE -q \
  -p no:cacheprovider --cov --cov-context=test --cov-report= --cov-fail-under=0 >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - ${BASELINE_TIMEOUT}s with no result, on the INTACT tree."
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

  # Which tests executed the lines this row is about to amputate. Read
  # from the PRISTINE tree before the mutation lands. Exit 4 means "no
  # in-process coverage" and falls back WIDE to the whole suite; any
  # other failure is a broken precondition and aborts - a selection
  # computed from a wrong precondition is a silent wrong zero.
  local sel sel_rc
  sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
    python3 scripts/lib/select-covering-tests.py "$file")
  sel_rc=$?
  if [ "$sel_rc" -eq 4 ]; then
    sel="$SUITE"
    echo "  (no in-process coverage of these lines; running the full suite)"
  elif [ "$sel_rc" -ne 0 ]; then
    echo "  SELECTOR FAILED (rc=$sel_rc) - fix the harness. STOPPING."
    exit 3
  fi

  # SC2155: declared and assigned separately.
  local backup
  backup="$BACKUP_DIR/${ROWS}_http_hardening.py"
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
  # bounded, and a row that hangs anyway must report rather than stall
  # the gate.
  # $sel is a space-separated node-id list.
  # MEASURED, because a suppression that suppresses nothing is the defect
  # this project keeps finding: at `--severity=warning` - the one threshold
  # the hook, ci.yml and SHELLCHECK_OPTS all share - SC2086 is BELOW the
  # line and this directive is INERT. Delete it and shellcheck stays
  # silent. At DEFAULT severity it fires twice in this file, so the
  # directive is kept: it is correct, it documents that the split is
  # WANTED, and it becomes load-bearing the day the threshold tightens.
  # shellcheck disable=SC2086
  timeout "$ROW_TIMEOUT" uv run --frozen pytest $sel -q -p no:cacheprovider -rf \
    >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/http_hardening.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  # If this ever refuses with 124, the row is unbounded: move it to the
  # mutation harness, where the change is bounded.
  #
  # THIS HARNESS READS `^FAILED ` RATHER THAN `^PASSED `, so a non-measurement
  # rc reads as "killed by: NOTHING" instead of as a perfect kill. That is the
  # less alarming direction, not a safe one: the row still publishes a verdict
  # for a run that measured nothing, and this harness has the per-row selector
  # that makes rc=4 reachable.
  verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"

  tail -1 "$OUT" | sed 's/^/  /'

  # THE VACUOUS-ROW GATE. The verdict is the RUN'S EXIT CODE, not
  # `grep -c "^FAILED"`: that grep misses ERROR entirely, and a
  # collection error is a row going red for a real reason.
  if [ "$rc" -eq 0 ]; then
    echo "  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red."
    echo "      Every assertion in the suite survived. This row measures nothing."
    VACUOUS=$((VACUOUS + 1))
  fi

  # WHICH tests went red, so the report can say what each row is held
  # up by. `-rf` lists the failures; the suite is 500+ cases and
  # listing every survivor would bury the answer.
  local killers
  killers=$(grep -E '^FAILED ' "$OUT" | sed 's/^FAILED //' | cut -d' ' -f1 || true)
  if [ -z "$killers" ]; then
    echo "  killed by: NOTHING"
  else
    local n
    n=$(printf '%s\n' "$killers" | wc -l)
    TOTAL_SURVIVORS=$((TOTAL_SURVIVORS + n))
    echo "  killed by: $n test(s)"
    printf '%s\n' "$killers" | head -8 | sed 's/^/    /'
  fi
  echo
}

# ===========================================================================
# AUTHENTICATION - the verifier built from JOBVITE_HTTP_TOKENS
# ===========================================================================

amputate "A1  the token verifier is never built, so HTTP is unauthenticated" \
  "$HARDENING" \
  '    if settings.mcp_transport != "http":
        return None
    if settings.http_tokens is None:' \
  '    if True:
        return None
    if settings.http_tokens is None:'

amputate "A2  the fail-closed check for an unset token map is deleted" \
  "$HARDENING" \
  '    if settings.http_tokens is None:
        msg = (
            "JOBVITE_MCP_TRANSPORT=http requires JOBVITE_HTTP_TOKENS; "
            "validate_settings should have refused this configuration"
        )
        raise ValueError(msg)' \
  '    if settings.http_tokens is None:
        return None'

amputate "A3  the client id is no longer derived from the token at all" \
  "$HARDENING" \
  '    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]' \
  '    return "client"'

# ===========================================================================
# SCOPES - SS7.2's three data classes
# ===========================================================================

amputate "A4  require_scopes is never put on any tool" \
  "$HARDENING" \
  '    for tool in registered_tools(server):
        tool.auth = require_scopes(TOOL_SCOPES[tool.name])' \
  '    return'

amputate "A5  the stdio guard is deleted and scopes apply everywhere" \
  "$HARDENING" \
  '    if settings.mcp_transport != "http":
        return
    for tool in registered_tools(server):' \
  '    for tool in registered_tools(server):'

amputate "A6  the totality check on TOOL_SCOPES is deleted" \
  "$HARDENING" \
  '    if frozenset(TOOL_SCOPES) != KNOWN_TOOLS:' \
  '    if False:'

# ===========================================================================
# THE MIDDLEWARE STACK
# ===========================================================================

amputate "A7  the stack is empty: no timing, no logging, no limiter" \
  "$HARDENING" \
  '    return [
        RequestIdMiddleware(),' \
  '    return []
    return [
        RequestIdMiddleware(),'

amputate "A8  the structured logging middleware is dropped from the stack" \
  "$HARDENING" \
  '        StructuredLoggingMiddleware(include_payloads=False),' \
  ''

amputate "A9  the timing middleware is dropped from the stack" \
  "$HARDENING" \
  '        TimingMiddleware(),' \
  ''

amputate "A10 the rate limiter is dropped from the stack" \
  "$HARDENING" \
  '        RateLimitingMiddleware(
            max_requests_per_second=INBOUND_MAX_REQUESTS_PER_SECOND,
            burst_capacity=INBOUND_BURST_CAPACITY,
            # MANDATORY. See `rate_limit_client_id`.
            get_client_id=rate_limit_client_id,
        ),
' \
  ''

# ===========================================================================
# THE INBOUND CORRELATION ID (C7-T1)
# ===========================================================================

amputate "A11 the transport never reads the inbound header at all" \
  "$HARDENING" \
  '        inbound = get_http_headers().get(REQUEST_ID_HEADER.lower())' \
  '        inbound = None'

amputate "A12 the middleware never binds the id it resolved" \
  "$HARDENING" \
  '        with request_id_scope(resolve_request_id(inbound)):
            return await call_next(context)' \
  '        return await call_next(context)'

# ===========================================================================
# THE BIND AND ITS GUARD LISTS
# ===========================================================================

amputate "A13 the guard lists are never set, off loopback or on" \
  "$HARDENING" \
  '    if not is_loopback(settings.mcp_host):
        host = settings.mcp_host' \
  '    if False:
        host = settings.mcp_host'

amputate "A14 the host and port are ignored and the defaults are served" \
  "$HARDENING" \
  '        "host": settings.mcp_host,
        "port": settings.mcp_port,' \
  '        "host": "127.0.0.1",
        "port": 8000,'

# The canonical result line's row count, from the harness's own
# counter. This harness declares no ROW_FLOOR, so the floor is 0:
# 0 is not a floor anything can breach, and it reads as absent.
harness_result_ran "$ROWS" 0
echo "ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally applied "$APPLIED" "$ROWS"
echo "VACUOUS ROWS: $VACUOUS"
echo "TOTAL KILLING ASSERTIONS ACROSS ALL ROWS: $TOTAL_SURVIVORS"
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
