#!/usr/bin/env bash
# U9 MUTATION harness. Change one value - does the NAMED test notice?
#
# THIS UNIT HAS NO REQUIRED CASE. IMPLEMENTATION-PLAN.md SS U9 says so in
# as many words: "No SS8 case owns this unit ... nothing in the coupling
# gate will miss them if they are dropped." Every other unit here has a
# required case that goes red when its behaviour goes. U9 does not. So
# these two harnesses are the whole of this unit's defence, and a
# surviving row here is not a nit - it is the one instrument that would
# have noticed, reporting that it would not have.
#
# THE ROW THAT MATTERS MOST IS M1, and it is the one with a threat row
# of its own. `include_payloads` flipped to True sends raw candidate PII
# to the framework log (C2-I1). The framework's DEFAULT for that keyword
# is ALSO False, which is why the mutation flips it to True rather than
# deleting the keyword: deleting it changes no behaviour and would be a
# row that cannot fail. That is stated here because a reader checking
# the harness is entitled to know which rows can fire and which cannot.
#
# M2 IS THE POSITIVE CONTROL'S MIRROR. It ADDS an excluded middleware
# rather than removing an adopted one, because the absence assertion is
# what a future contributor would break by re-adding `ResponseCaching`
# for latency - the exact regression ADR-0004 and DESIGN.md's caching
# paragraph exist to prevent.
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

HARDENING="src/fast_mcp_jobvite/http_hardening.py"
SUITE="tests/test_http_hardening.py"
OUT=/tmp/u9-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPY, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can detect only a failed
# `cp`, never "the tree still carries this row's mutation".
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
  # run, forever, while running nothing.
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
  backup="$BACKUP_DIR/${TOTAL}_http_hardening.py"
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
  if ! cmp -s "$file" "$PRISTINE_DIR/http_hardening.py"; then
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
# THE MIDDLEWARE STACK - the three adopted, the five excluded, and the one
# value a threat row is written about.
# ===========================================================================

# C2-I1, DESIGN.md:1820. Flipped to True the framework log receives raw
# candidate PII. Flipping rather than deleting, because the framework's
# own default is False and a deleted keyword changes nothing.
mutate "M1  include_payloads is flipped to True" \
  "$HARDENING" \
  "$SUITE::test_structured_logging_is_constructed_with_include_payloads_false" \
  '        StructuredLoggingMiddleware(include_payloads=False),' \
  '        StructuredLoggingMiddleware(include_payloads=True),'

# The regression ADR-0004 and DESIGN.md's caching paragraph exist to
# prevent: somebody re-adds a cache for latency, and a candidate-PII
# result is served to a public-job-data token.
mutate "M2  ResponseCachingMiddleware is re-added to the stack" \
  "$HARDENING" \
  "$SUITE::test_the_five_excluded_middleware_are_absent" \
  '    return [
        RequestIdMiddleware(),' \
  '    from fastmcp.server.middleware.caching import ResponseCachingMiddleware

    return [
        ResponseCachingMiddleware(),
        RequestIdMiddleware(),'

# DESIGN.md:411-413: the default keys every caller to the literal
# "global", so one noisy integrator throttles everyone.
mutate "M3  get_client_id is dropped and the limiter keys everyone to global" \
  "$HARDENING" \
  "$SUITE::test_the_rate_limiter_has_a_get_client_id" \
  '            get_client_id=rate_limit_client_id,' \
  '            get_client_id=None,'

# The same defect from the other side: the callable stays wired but
# returns one constant, so every caller shares a bucket again. This is
# the row the LIVE per-client arm exists for - M3 is visible by reading
# the object, this one is not.
mutate "M4  rate_limit_client_id returns one constant for every caller" \
  "$HARDENING" \
  "$SUITE::test_rate_limiting_is_per_client" \
  '    token = get_access_token()
    if token is None:
        return ANONYMOUS_CLIENT_ID
    return token.client_id' \
  '    return ANONYMOUS_CLIENT_ID'

# DESIGN.md:414-422. `desired_calls + 2`, where the 2 is FastMCP's own
# client's connect sequence.
mutate "M5  the burst loses the connect-sequence allowance" \
  "$HARDENING" \
  "$SUITE::test_the_burst_is_the_designs_sizing" \
  'INBOUND_BURST_CAPACITY: Final = DESIRED_TOOL_CALLS_PER_BURST + 2' \
  'INBOUND_BURST_CAPACITY: Final = DESIRED_TOOL_CALLS_PER_BURST'

# ===========================================================================
# SCOPES - the three data classes of SS4.1, and the transport they apply on
# ===========================================================================

# A tool moves to the wrong data class, so a jobs token reaches
# candidate PII. C1-E1.
mutate "M6  search_jobs is scoped to candidate PII instead of job data" \
  "$HARDENING" \
  "$SUITE::test_two_differently_scoped_tokens_see_different_tool_sets" \
  '    SEARCH_JOBS: SCOPE_JOBS,' \
  '    SEARCH_JOBS: SCOPE_CANDIDATES,'

# DESIGN.md:917-921. Applied on stdio, `_RequireScopes` denies an absent
# token and every tool disappears from a transport the design declares
# fully authorised.
mutate "M7  the scopes are applied on stdio too" \
  "$HARDENING" \
  "$SUITE::test_scopes_are_NOT_applied_on_stdio" \
  '    if settings.mcp_transport != "http":
        return
    for tool in registered_tools(server):' \
  '    for tool in registered_tools(server):'

# The other direction: the scope is never applied at all, so every token
# sees every tool. This is the silent one - nothing fails, the server
# just stops enforcing SS7.2.
mutate "M8  the scopes are never applied at all" \
  "$HARDENING" \
  "$SUITE::test_scopes_are_applied_on_http" \
  '        tool.auth = require_scopes(TOOL_SCOPES[tool.name])' \
  '        tool.auth = None'

# ===========================================================================
# THE VERIFIER, AND THE CLIENT ID IT MINTS
# ===========================================================================

# The limiter interpolates `client_id` into the MCPError it RAISES, so a
# raw token there is published to the caller and the log.
mutate "M9  the client id becomes the bearer token itself" \
  "$HARDENING" \
  "$SUITE::test_the_client_id_is_never_the_token" \
  '    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]' \
  '    return token'

# A verifier that authenticates but grants nothing: every token holds
# every scope. The map is read and its scopes thrown away.
mutate "M10 every token is issued every scope" \
  "$HARDENING" \
  "$SUITE::test_the_verifier_carries_each_token_and_its_scopes" \
  '            token: {"client_id": token_client_id(token), "scopes": list(scopes)}' \
  '            token: {"client_id": token_client_id(token), "scopes": ["*"]}'

# ===========================================================================
# THE BIND, AND THE GUARD LISTS
# ===========================================================================

# `allowed_origins=None` is not "no origins" - `server/http.py:242`
# reads `is not None` to decide whether the list was set at all, so None
# restores the framework default this unit exists to replace.
mutate "M11 allowed_origins reverts to the framework default" \
  "$HARDENING" \
  "$SUITE::test_off_loopback_SETS_the_guard_lists" \
  '        kwargs["allowed_origins"] = []' \
  '        kwargs["allowed_origins"] = None'

# The guard lists are set unconditionally, which narrows `allowed_hosts`
# on a loopback bind and breaks `localhost` against 127.0.0.1 for no
# threat that exists inside the host.
mutate "M12 the guard lists are set on loopback too" \
  "$HARDENING" \
  "$SUITE::test_loopback_leaves_the_guard_lists_alone" \
  '    if not is_loopback(settings.mcp_host):
        host = settings.mcp_host' \
  '    if True:
        host = settings.mcp_host'

# ===========================================================================
# THE INBOUND CORRELATION ID (C7-T1)
# ===========================================================================

# The header is read under the wrong name, so a caller's id is never
# found and every request mints a fresh one. Silent: the tool still
# gets a well-formed UUID.
mutate "M13 the inbound header is looked up under the wrong name" \
  "$HARDENING" \
  "$SUITE::test_a_valid_inbound_request_id_reaches_the_tool_unchanged" \
  '        inbound = get_http_headers().get(REQUEST_ID_HEADER.lower())' \
  '        inbound = get_http_headers().get("x-correlation-id")'

# The validation is skipped and the header is used verbatim. This is
# C7-T1 itself: a value carrying a newline writes a second,
# attacker-authored line into the audit stream.
mutate "M14 the inbound id is bound without being validated" \
  "$HARDENING" \
  "$SUITE::test_a_malformed_inbound_request_id_is_replaced" \
  '        with request_id_scope(resolve_request_id(inbound)):' \
  '        with request_id_scope(inbound or resolve_request_id(None)):'

# ===========================================================================
# THE ROW FLOOR (R4-M4, applied here by R7-H2)
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted - or all skipped - reports fully green. `TOTAL -gt 0` below
# was the only floor, which one surviving row satisfies. Lowering this
# number is a visible diff that has to be defended.
#
# 14 is DERIVED, not typed: this harness was run at 03c4ae6 in a
# dedicated worktree and reported "14/14 controls fired", with 14 rows
# counted from the log. A floor copied from a report or a task record
# would be a second copy of a number that is measured in one place.
ROW_FLOOR=14
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "########## $TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

echo "$FIRED/$TOTAL controls fired."
[ "$TOTAL" -gt 0 ] && [ "$FIRED" -eq "$TOTAL" ] && exit 0
exit 1
