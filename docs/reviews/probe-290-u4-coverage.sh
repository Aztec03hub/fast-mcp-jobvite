#!/usr/bin/env bash
# Task #290: does `check-u4-client-amputation.sh`'s per-row test selection
# change any row's VERDICT versus running its whole suite?
#
# THE SIBLING RESULT THIS REPLICATES. #286 asked the same question of
# `check-u9-http-amputation.sh` and found selection verdict-preserving 14/14
# and killer-set-identical 13/14. The one row that differed - A14 - lost four
# killers that drive a REAL CHILD PROCESS through `spawn_marker_server`, which
# an in-process `--cov-context` map cannot observe. The rc=4 fallback does not
# catch that: it fires only on ZERO in-process coverage, and A14 had plenty.
#
# THE ONE STRUCTURAL DIFFERENCE FROM U9, and it is the whole reason this had to
# be measured rather than argued from U9. U9's fallback arm is the WHOLE `tests`
# tree. U4's is a SINGLE FILE, `tests/test_jobvite_client.py`, and its coverage
# map is built from that same single file. So U4's "unselected" arm is narrower
# than U9's by construction, and both arms of this probe live inside it.
#
# This replays the harness's own two steps per row - the same selector
# (`scripts/lib/select-covering-tests.py`) reading a map built by the same
# `pytest --cov --cov-context=test` baseline over the same $SUITE - and runs the
# amputated tree BOTH ways:
#
#   ARM SEL   the selected node ids   (what the harness runs today)
#   ARM FULL  all of $SUITE           (what the harness ran before #238)
#
# and prints the SET DIFFERENCE of the two FAILED lists. FULL-only killers are
# the finding. It also prints each arm's pytest rc and tally line, because U4
# reads its verdict out of `^PASSED ` counts and `verdict-guard.sh` refuses any
# rc that is not 0 or 1 - so an rc change is a verdict change even when the
# killer sets agree.
#
# Selection here is one-directional by construction: the selected ids are a
# SUBSET of $SUITE, so a test red under selection is red under $SUITE too.
# Selection can only turn a real kill into a LOUD vacuous row - which this
# harness reports as survivors, and `ci-harness-gate.sh` gates - never a
# vacuous row into a false kill.
#
# THE TREE. A pristine copy is taken first, an EXIT trap restores it on ANY
# exit, `cmp` proves the restore, and `git status --porcelain -- src tests` is
# printed at the end.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 3
export PYTHONDONTWRITEBYTECODE=1
ARM_TIMEOUT=900

SUBJECT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_jobvite_client.py"
# TWO MODES, one anchor list. The anchor list below is the thing that must not
# be duplicated - a second file carrying a copy of it is the drift this repo
# keeps measuring - so the wider-scope question is asked by this same script.
#
#   (default)                          both arms, per row: SEL vs all of $SUITE.
#   PROBE_290_MODE=select-only         no mutation, no arms: print each row's
#                                      covering set and the test FILES it spans.
#   PROBE_290_BASE_SCOPE=tests         build the map from the WHOLE tree instead
#                                      of $SUITE. Combined with select-only this
#                                      answers a DIFFERENT question from
#                                      selection: does a killer for these lines
#                                      live in a test file $SUITE never runs?
#                                      That is the harness's SUITE choice, not
#                                      its selection, and the two must not be
#                                      reported as one finding.
MODE="${PROBE_290_MODE:-full}"
BASE_SCOPE="${PROBE_290_BASE_SCOPE:-$SUITE}"
WORK=$(mktemp -d)
PRISTINE="$WORK/pristine.py"
COVDB="$WORK/covdb"
cp "$SUBJECT" "$PRISTINE" || exit 3
trap 'cp "$PRISTINE" "$SUBJECT"; rm -rf "$WORK"' EXIT

echo "########## BASELINE - builds the same map the harness builds, over $BASE_SCOPE"
bt0=$SECONDS
COVERAGE_FILE="$COVDB" timeout "$ARM_TIMEOUT" uv run --frozen pytest $BASE_SCOPE -q \
  -p no:cacheprovider --cov --cov-context=test --cov-report= --cov-fail-under=0 \
  >"$WORK/base.txt" 2>&1
brc=$?
echo "  rc=$brc  $((SECONDS - bt0))s"
tail -1 "$WORK/base.txt"
if [ "$brc" -ne 0 ]; then
  echo "::error::BROKEN CONTROL - the intact suite is red. Nothing below means anything."
  exit 3
fi
SUITE_N=$(grep -oE '[0-9]+ passed' "$WORK/base.txt" | head -1 | cut -d' ' -f1)
echo "  suite size (from the tally, not counted by hand): $SUITE_N"
echo

# One arm: amputate, run $2 (a node-id list or the suite path), record the
# FAILED and PASSED id sets, the rc, the tally line and the wall time.
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
  local t0=$SECONDS
  # -rA is what the harness passes: it needs the PASSED lines to count survivors.
  # shellcheck disable=SC2086
  timeout "$ARM_TIMEOUT" uv run --frozen pytest $what -q -p no:cacheprovider -rA \
    >"$out.raw" 2>&1
  local rc=$?
  echo $((SECONDS - t0)) >"$out.secs"
  cp "$PRISTINE" "$SUBJECT"
  cmp -s "$SUBJECT" "$PRISTINE" || { echo "::error::RESTORE FAILED"; exit 3; }
  grep -E '^FAILED ' "$out.raw" | sed 's/^FAILED //' | cut -d' ' -f1 | sort -u >"$out"
  grep -E '^PASSED ' "$out.raw" | sed 's/^PASSED //' | cut -d' ' -f1 | sort -u >"$out.pass"
  echo "$rc"
}

# The harness's own verdict, re-derived from the arm's artefacts rather than
# retyped: verdict-guard.sh REFUSES any rc outside {0,1}, and below that the
# harness reports the `^PASSED ` count as survivors.
verdict_of() {
  local rc="$1" out="$2" n
  case "$rc" in
    0|1) ;;
    124) echo "REFUSED(timeout)"; return ;;
    *)   echo "REFUSED(rc=$rc)"; return ;;
  esac
  n=$(wc -l <"$out.pass")
  if [ "$n" -eq 0 ]; then echo "KILLED(survivors=0)"; else echo "SURVIVORS=$n"; fi
}

probe_row() {
  local label="$1" old="$2" new="$3"
  echo "########## $label"

  local sel sel_rc
  sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
    python3 scripts/lib/select-covering-tests.py "$SUBJECT")
  sel_rc=$?
  if [ "$sel_rc" -eq 4 ]; then
    echo "  SELECTOR rc=4: no in-process coverage. The harness falls back to all"
    echo "  of $SUITE, so both arms are the SAME COMMAND. Selection does not"
    echo "  apply to this row and cannot weaken it. NOT MEASURED."
    echo
    return
  elif [ "$sel_rc" -ne 0 ]; then
    echo "::error::SELECTOR FAILED rc=$sel_rc"
    exit 2
  fi
  local nsel
  nsel=$(printf '%s\n' "$sel" | tr ' ' '\n' | grep -c .)

  if [ "$MODE" = "select-only" ]; then
    echo "  covering set: $nsel ids, from these test FILES:"
    printf '%s\n' "$sel" | tr ' ' '\n' | grep . | cut -d: -f1 | sort | uniq -c \
      | sort -rn | sed 's/^/    /'
    echo
    return
  fi

  local rc_sel rc_full
  rc_sel=$(run_arm "$WORK/sel.txt" "$sel" "$old" "$new")
  rc_full=$(run_arm "$WORK/full.txt" "$SUITE" "$old" "$new")

  echo "  selected ids: $nsel of $SUITE_N"
  echo "  ARM SEL   rc=$rc_sel  $(cat "$WORK/sel.txt.secs")s  killers=$(wc -l <"$WORK/sel.txt")  survivors=$(wc -l <"$WORK/sel.txt.pass")  verdict=$(verdict_of "$rc_sel" "$WORK/sel.txt")"
  echo "            $(tail -1 "$WORK/sel.txt.raw")"
  echo "  ARM FULL  rc=$rc_full  $(cat "$WORK/full.txt.secs")s  killers=$(wc -l <"$WORK/full.txt")  survivors=$(wc -l <"$WORK/full.txt.pass")  verdict=$(verdict_of "$rc_full" "$WORK/full.txt")"
  echo "            $(tail -1 "$WORK/full.txt.raw")"

  local only
  only=$(comm -13 "$WORK/sel.txt" "$WORK/full.txt")
  if [ -z "$only" ]; then
    echo "  FULL-only killers: NONE - the selected set holds this row."
  else
    echo "  FULL-only killers: $(printf '%s\n' "$only" | wc -l) - SELECTION DROPS THESE:"
    printf '%s\n' "$only" | sed 's/^/    /'
  fi
  local impossible
  impossible=$(comm -23 "$WORK/sel.txt" "$WORK/full.txt")
  if [ -n "$impossible" ]; then
    echo "  ::error::SEL-only killers exist - selection is NOT a subset run. Investigate:"
    printf '%s\n' "$impossible" | sed 's/^/    /'
  fi
  echo
}

# EVERY row in check-u4-client-amputation.sh, in the harness's own order and
# with the anchors copied from it verbatim. A drifted anchor fails the
# uniqueness check above and stops this probe rather than measuring nothing.

probe_row "A1  evaluate_response applies NEITHER arm - every decodable body succeeds" \
  '    envelope_code = _envelope_status_code(payload)' \
  '    return payload
    envelope_code = _envelope_status_code(payload)'

probe_row "A2  the ENVELOPE arm is deleted (C5-S1 reopens)" \
  '    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(envelope_code, _envelope_message(payload))' \
  '    _ = envelope_code'

probe_row "A3  the HTTP-STATUS arm is deleted" \
  '    if http_status >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(http_status, _envelope_message(payload))' \
  '    pass'

probe_row "A4  _decode_json_object returns {} for anything it cannot parse" \
  '    text = body.decode("utf-8", errors="replace").strip()' \
  '    return {}
    text = body.decode("utf-8", errors="replace").strip()'

probe_row "A5  markup is never routed to defusedxml at all" \
  '    if text.startswith("<"):' \
  '    if False:  # AMPUTATED-A5'

probe_row "A6  v2 sends NO credential headers" \
  '        return {
            API_KEY_HEADER: self._api_key.get_secret_value(),
            API_SECRET_HEADER: self._api_secret.get_secret_value(),
            "Accept": "application/json",
        }' \
  '        return {"Accept": "application/json"}'

probe_row "A7  the jobFeed route sends no credential parameters" \
  '        return {
            "api": self._api_key.get_secret_value(),
            "sc": self._api_secret.get_secret_value(),
            "companyId": self._company_id.get_secret_value(),
        }' \
  '        return {}'

probe_row "A8  _excerpt neither redacts nor truncates" \
  '    redacted = redact_text(text)
    if len(redacted) <= MAX_BODY_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_BODY_EXCERPT_CHARS] + "... [truncated]"' \
  '    return text'

probe_row "A9  M-5 reopened: the exception's text becomes the consumer's detail" \
  '            raise JobviteUnavailableError(_unavailable_detail(exc)) from None' \
  '            raise JobviteUnavailableError(
                redact_text(f"{type(exc).__name__}: {exc}")
            ) from None'

probe_row "A9b a transport error's text reaches the consumer unredacted" \
  '            raise JobviteUnavailableError(_unavailable_detail(exc)) from None' \
  '            raise JobviteUnavailableError(str(exc)) from None'

probe_row "A9c the enumerated detail says nothing a caller can act on" \
  '    if isinstance(exc, httpx2.TimeoutException):
        return UNAVAILABLE_TIMEOUT_DETAIL' \
  '    return "Jobvite is unavailable."
    if isinstance(exc, httpx2.TimeoutException):
        return UNAVAILABLE_TIMEOUT_DETAIL'

probe_row "A9d the v2 credential headers reach the log unredacted" \
  '                headers=redact_headers(dict(headers)),' \
  '                headers=dict(headers),'

probe_row "A9e the exception text is logged without redact_text" \
  '                error=redact_text(f"{type(exc).__name__}: {exc}"),' \
  '                error=f"{type(exc).__name__}: {exc}",'

probe_row "A9f the transport failure is never logged (relocated controls go vacuous)" \
  '            logger.warning(
                "jobvite transport failure",
                method=method,
                route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
                headers=redact_headers(dict(headers)),
                error=redact_text(f"{type(exc).__name__}: {exc}"),
            )' \
  '            pass'

probe_row "A10 the cookie jar is never cleared" \
  '            self._client.cookies.clear()' \
  '            pass'

probe_row "A11 the request path logs NOTHING (absence assertions go vacuous)" \
  '        logger.debug(
            "jobvite request",
            method=method,
            route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
        )' \
  '        pass'

probe_row "A12 a route-level 404 IS mapped to a record-level not-found" \
  '    envelope_code = _envelope_status_code(payload)' \
  '    from ..errors import ResourceNotFoundError

    envelope_code = _envelope_status_code(payload)
    if envelope_code == 404 or http_status == 404:
        raise ResourceNotFoundError(_envelope_message(payload))'

cp "$PRISTINE" "$SUBJECT"
cmp -s "$SUBJECT" "$PRISTINE" || { echo "::error::RESTORE FAILED. DO NOT COMMIT."; exit 3; }
echo "RESTORED (cmp clean)"
git -C "$REPO" status --porcelain -- src tests
echo "TREE ROWS: $(git -C "$REPO" status --porcelain -- src tests | wc -l)"
