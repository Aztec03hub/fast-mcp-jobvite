#!/usr/bin/env bash
# Task #286: is U9's per-row selection a COVERING set or an ARBITRARY subset?
#
# The count alone cannot answer that. `check-u9-http-amputation.sh` runs row A6
# against ONE test and row A13/A14 against EIGHT, out of a 895-item suite. A row
# that selects a set which COVERS the amputated symbol is correct and fast; a row
# that selects an arbitrary subset is a weakened control that still prints a
# verdict. The discriminator is whether the FULL suite finds a killer the
# SELECTED set did not.
#
# For each row named in ROWS below this replays the harness's own two steps -
# the same selector (`scripts/lib/select-covering-tests.py`) reading a coverage
# map built by the same `pytest --cov --cov-context=test` baseline - and then
# runs the amputated tree BOTH ways:
#
#   ARM SEL   the selected node ids          (what the harness runs today)
#   ARM FULL  the whole `tests` suite        (what the harness ran before #240)
#
# and prints the SET DIFFERENCE of the two FAILED lists. FULL-only killers are
# the finding: they are assertions that catch this amputation and that selection
# drops. NONE means the selected set holds the row.
#
# Selection on an amputation harness is one-directional by construction: the
# selected ids are a SUBSET of the suite, so a test that goes red under selection
# goes red under the suite too. Selection can therefore only turn a real kill
# into a FALSE VACUOUS ROW - which this harness's gate reports loudly (exit 1) -
# never a real vacuous row into a false kill. This probe measures the size of
# that one-directional loss, per row.
#
# THE TREE. A pristine copy is taken first, an EXIT trap restores it on ANY exit,
# `cmp` proves the restore, and `git status --porcelain` is printed at the end.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 3
export PYTHONDONTWRITEBYTECODE=1
ARM_TIMEOUT=900

SUBJECT="src/fast_mcp_jobvite/http_hardening.py"
WORK=$(mktemp -d)
PRISTINE="$WORK/pristine.py"
COVDB="$WORK/covdb"
cp "$SUBJECT" "$PRISTINE" || exit 3
trap 'cp "$PRISTINE" "$SUBJECT"; rm -rf "$WORK"' EXIT

echo "########## BASELINE - builds the same map the harness builds"
COVERAGE_FILE="$COVDB" timeout "$ARM_TIMEOUT" uv run --frozen pytest tests -q \
  -p no:cacheprovider --cov --cov-context=test --cov-report= --cov-fail-under=0 \
  >"$WORK/base.txt" 2>&1
brc=$?
tail -1 "$WORK/base.txt"
if [ "$brc" -ne 0 ]; then
  echo "::error::BROKEN CONTROL - the intact suite is red. Nothing below means anything."
  exit 3
fi
echo

# One arm: amputate, run $2 (a node-id list or `tests`), record FAILED ids.
run_arm() {
  local out="$1" what="$2" old="$3" new="$4"
  if ! OLD="$old" NEW="$new" FILE="$SUBJECT" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
n = s.count(os.environ["OLD"])
if n != 1:
    print(f"ANCHOR NOT UNIQUE ({n} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(os.environ["OLD"], os.environ["NEW"]))
PY
  then
    echo "::error::COULD NOT APPLY the anchor. Fix this probe against the harness."
    exit 2
  fi
  cmp -s "$SUBJECT" "$PRISTINE" && { echo "::error::AMPUTATION DID NOT LAND"; exit 2; }
  # shellcheck disable=SC2086
  timeout "$ARM_TIMEOUT" uv run --frozen pytest $what -q -p no:cacheprovider -rf \
    >"$out.raw" 2>&1
  local rc=$?
  cp "$PRISTINE" "$SUBJECT"
  cmp -s "$SUBJECT" "$PRISTINE" || { echo "::error::RESTORE FAILED"; exit 3; }
  grep -E '^FAILED ' "$out.raw" | sed 's/^FAILED //' | cut -d' ' -f1 | sort -u >"$out"
  echo "$rc"
}

probe_row() {
  local label="$1" old="$2" new="$3"
  echo "########## $label"

  local sel sel_rc
  sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
    python3 scripts/lib/select-covering-tests.py "$SUBJECT")
  sel_rc=$?
  if [ "$sel_rc" -eq 4 ]; then
    echo "  no in-process coverage - the harness falls back to the FULL suite here."
    echo "  Selection cannot weaken a row it does not apply to. SKIPPED."
    echo
    return
  elif [ "$sel_rc" -ne 0 ]; then
    echo "::error::SELECTOR FAILED rc=$sel_rc"
    exit 2
  fi
  local nsel
  nsel=$(printf '%s\n' "$sel" | tr ' ' '\n' | grep -c .)

  local rc_sel rc_full
  rc_sel=$(run_arm "$WORK/sel.txt" "$sel" "$old" "$new")
  rc_full=$(run_arm "$WORK/full.txt" "tests" "$old" "$new")

  echo "  selected ids: $nsel of 895"
  echo "  ARM SEL   rc=$rc_sel   killers=$(wc -l <"$WORK/sel.txt")   $(tail -1 "$WORK/sel.txt.raw")"
  echo "  ARM FULL  rc=$rc_full   killers=$(wc -l <"$WORK/full.txt")   $(tail -1 "$WORK/full.txt.raw")"

  # The finding: killers the FULL suite found and the SELECTED set did not.
  local only
  only=$(comm -13 "$WORK/sel.txt" "$WORK/full.txt")
  if [ -z "$only" ]; then
    echo "  FULL-only killers: NONE - the selected set holds this row."
  else
    echo "  FULL-only killers: $(printf '%s\n' "$only" | wc -l) - SELECTION DROPS THESE:"
    printf '%s\n' "$only" | sed 's/^/    /'
  fi
  # The other direction must be empty: a subset cannot fail what the superset passes.
  local impossible
  impossible=$(comm -23 "$WORK/sel.txt" "$WORK/full.txt")
  if [ -n "$impossible" ]; then
    echo "  ::error::SEL-only killers exist - selection is NOT a subset run. Investigate:"
    printf '%s\n' "$impossible" | sed 's/^/    /'
  fi
  echo
}

# EVERY row in check-u9-http-amputation.sh, in the harness's own order. The
# anchors below are copied from that file and must stay identical to it; a
# drifted anchor fails the uniqueness check above and stops this probe.
probe_row "A1  the token verifier is never built, so HTTP is unauthenticated" \
  '    if settings.mcp_transport != "http":
        return None
    if settings.http_tokens is None:' \
  '    if True:
        return None
    if settings.http_tokens is None:'

probe_row "A2  the fail-closed check for an unset token map is deleted" \
  '    if settings.http_tokens is None:
        msg = (
            "JOBVITE_MCP_TRANSPORT=http requires JOBVITE_HTTP_TOKENS; "
            "validate_settings should have refused this configuration"
        )
        raise ValueError(msg)' \
  '    if settings.http_tokens is None:
        return None'

probe_row "A3  the client id is no longer derived from the token at all" \
  '    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]' \
  '    return "client"'

probe_row "A4  require_scopes is never put on any tool" \
  '    for tool in registered_tools(server):
        tool.auth = require_scopes(TOOL_SCOPES[tool.name])' \
  '    return'

probe_row "A5  the stdio guard is deleted and scopes apply everywhere" \
  '    if settings.mcp_transport != "http":
        return
    for tool in registered_tools(server):' \
  '    for tool in registered_tools(server):'

probe_row "A6  the totality check on TOOL_SCOPES is deleted" \
  '    if frozenset(TOOL_SCOPES) != KNOWN_TOOLS:' \
  '    if False:'

probe_row "A7  the stack is empty: no timing, no logging, no limiter" \
  '    return [
        RequestIdMiddleware(),' \
  '    return []
    return [
        RequestIdMiddleware(),'

probe_row "A8  the structured logging middleware is dropped from the stack" \
  '        StructuredLoggingMiddleware(include_payloads=False),' \
  ''

probe_row "A9  the timing middleware is dropped from the stack" \
  '        TimingMiddleware(),' \
  ''

probe_row "A10 the rate limiter is dropped from the stack" \
  '        RateLimitingMiddleware(
            max_requests_per_second=INBOUND_MAX_REQUESTS_PER_SECOND,
            burst_capacity=INBOUND_BURST_CAPACITY,
            # MANDATORY. See `rate_limit_client_id`.
            get_client_id=rate_limit_client_id,
        ),
' \
  ''

probe_row "A11 the transport never reads the inbound header at all" \
  '        inbound = get_http_headers().get(REQUEST_ID_HEADER.lower())' \
  '        inbound = None'

probe_row "A12 the middleware never binds the id it resolved" \
  '        with request_id_scope(resolve_request_id(inbound)):
            return await call_next(context)' \
  '        return await call_next(context)'

probe_row "A13 the guard lists are never set, off loopback or on" \
  '    if not is_loopback(settings.mcp_host):
        host = settings.mcp_host' \
  '    if False:
        host = settings.mcp_host'

probe_row "A14 the host and port are ignored and the defaults are served" \
  '        "host": settings.mcp_host,
        "port": settings.mcp_port,' \
  '        "host": "127.0.0.1",
        "port": 8000,'

cp "$PRISTINE" "$SUBJECT"
cmp -s "$SUBJECT" "$PRISTINE" || { echo "::error::RESTORE FAILED. DO NOT COMMIT."; exit 3; }
echo "RESTORED (cmp clean)"
git -C "$REPO" status --porcelain -- src tests
echo "TREE ROWS: $(git -C "$REPO" status --porcelain -- src tests | wc -l)"
