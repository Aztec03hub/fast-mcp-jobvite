#!/usr/bin/env bash
# U4 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation  asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything still
#                    report success?
#
# Amputation has exposed a vacuous assertion in every unit built on this project
# so far. U3's found a test that passed with the behaviour deleted because it
# searched the module's file text for a string the module's own docstring
# quoted - it was asserting that the DOCUMENTATION existed. That is why
# tests/test_jobvite_client.py asserts on behaviour, and why its one structural
# check walks the AST instead of grepping.
#
# SURVIVORS ARE THE OUTPUT, not the failure. For each amputation this prints the
# counts and NAMES every test that still passed, so the report can say which
# assertions survived and why, rather than asserting that none did.
#
# It exits non-zero only if it could not run, if the intact baseline is red, or
# if an amputation left the tree dirty. The CI step gates on every row having
# APPLIED ITS ANCHOR, not on this exit code - and that is true only because the
# step passes `--anchors-applied` and this harness publishes `applied=N/M`.
#
# THIS SENTENCE WAS FALSE FROM THE DAY IT WAS WRITTEN UNTIL TASK #152. There was
# no anchor counter here and no `applied=` field, and the step read
# `--amputation --min-rows 17 --row-re ...` - rows and an exit code, never
# anchors. A row whose anchor moved printed "COULD NOT APPLY", `return`ed, was
# counted as a row like any other, and the step passed. The claim named the
# gate that would have caught it, which is the reason it read as safe: no gate
# reads a comment, so a comment describing a gate that does not exist is
# indistinguishable from one that does.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size), and an
# amputation that replaces a body with `pass` can be the same size inside one
# second, in which case the interpreter reuses stale bytecode and the amputated
# code never runs. That failure is silent and it fakes a clean result.

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

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_jobvite_client.py"
OUT=/tmp/u4-amp.txt

# `git status --porcelain`, NOT `git diff --quiet`. `git diff` compares
# the worktree to the INDEX, so a file that was edited and then `git
# add`-ed reads CLEAN and this guard waves it through - after which the
# harness measures STAGED, unreviewed code and calls the result a
# measurement of HEAD. Measured: modify + `git add` gives `git diff
# --quiet` exit 0 and `--porcelain` a non-empty `M `.
#
# ONLY THE PRE-FLIGHT GUARD MOVES. The landing and restore checks below
# stay on `git diff` ON PURPOSE: they are paired with `git checkout --`,
# which restores from the INDEX, so an index-relative question is the
# one that matches the restore. Widening those would report RESTORE
# FAILED on a tree this guard has already refused to run against.
if [ -n "$(git status --porcelain -- "$CLIENT")" ]; then
  echo "ABORT: $CLIENT has uncommitted changes (staged, unstaged or both)."
  echo "This harness mutates it and restores with 'git checkout --', so it"
  echo "would measure your edit rather than HEAD. Commit or stash first."
  exit 3
fi

echo "########## BASELINE - the intact tree"
# The baseline doubles as a per-test coverage map build (#238): each row
# below runs only the tests that executed the amputated lines, selected
# from this same run of this same tree, so the map cannot be stale. A row
# with no in-process coverage of its lines falls back to the whole $SUITE.
COVDB="$(mktemp /tmp/u4-amp-covdb-XXXXXX)"
COVERAGE_FILE="$COVDB" timeout "$BASELINE_TIMEOUT" uv run --frozen pytest $SUITE -q \
  -p no:cacheprovider --cov --cov-context=test --cov-report= --cov-fail-under=0 >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - ${BASELINE_TIMEOUT}s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
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

# ---------------------------------------------------------------------------
# amputate <label> <file> <old> <new>
# ---------------------------------------------------------------------------
# A ROW COUNTER, added by task #107. This harness had none, so the
# canonical result line could only ever report rows=0 - and rows=0
# beside a green is exactly the shape a row floor exists to catch.
# The increment is at the TOP of the row function so that a row
# which aborts on a missing anchor still counts as having run.
HR_COUNTED_ROWS=0
# THE ANCHOR-LANDING COUNTER, task #152. Every row below verifies TWICE that
# its anchor landed - once for uniqueness inside the Python heredoc, once
# against git - and then threw both results away into prose and `return`ed.
# The row still counted as having RUN, so `rows=` on the canonical line was
# identical whether an anchor landed or not, and no checker downstream could
# see the difference: a tally this harness computed per row and never
# published. It is counted here and published as `applied=` below.
HR_APPLIED=0
amputate() {
  HR_COUNTED_ROWS=$((HR_COUNTED_ROWS + 1))
  local label="$1" file="$2" old="$3" new="$4"

  echo "########## $label"

  # Selection from the PRISTINE file, before the mutation lands. Exit 4 =
  # no in-process coverage, fall back WIDE to $SUITE; any other selector
  # failure is a broken precondition and aborts loudly.
  local sel sel_rc
  sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
    python3 scripts/lib/select-covering-tests.py "$file")
  sel_rc=$?
  if [ "$sel_rc" -eq 4 ]; then
    sel="$SUITE"
    echo "  (no in-process coverage of these lines; running all of $SUITE)"
  elif [ "$sel_rc" -ne 0 ]; then
    echo "  SELECTOR FAILED (rc=$sel_rc) - fix the harness. STOPPING."
    exit 3
  fi

  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
if s.count(old) != 1:
    print(f"  ANCHOR NOT UNIQUE ({s.count(old)} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  then
    echo "  COULD NOT APPLY - the anchor moved. Fix the harness."
    echo
    return
  fi

  # It landed. Compared against git, never with a grep for the replacement:
  # `grep -F` with a multi-line pattern treats each line as a separate
  # alternative, so an unchanged line inside a multi-line amputation matches a
  # clean file and reports the opposite of the truth.
  if git diff --quiet -- "$file"; then
    echo "  AMPUTATION DID NOT LAND despite a successful write"
    echo
    return
  fi

  # IT LANDED. Counted separately from the row count, because a row that
  # RAN and a row whose anchor APPLIED are different facts and the two
  # `return`s above are exactly where they diverge.
  HR_APPLIED=$((HR_APPLIED + 1))

  # Which tests executed the amputated lines (see the BASELINE note). The
  # selection was computed BEFORE the mutation landed, from the pristine
  # file. $sel is a space-separated node list.
  # MEASURED, because a suppression that suppresses nothing is the defect
  # this project keeps finding: at `--severity=warning` - the one threshold
  # the hook, ci.yml and SHELLCHECK_OPTS all share - SC2086 is BELOW the
  # line and this directive is INERT. Delete it and shellcheck stays
  # silent. At DEFAULT severity it fires twice in this file, so the
  # directive is kept: it is correct, it documents that the split is
  # WANTED, and it becomes load-bearing the day the threshold tightens.
  # shellcheck disable=SC2086
  timeout "$ROW_TIMEOUT" uv run --frozen pytest $sel -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "  RESTORE FAILED - $file still differs from the commit. STOPPING."
    exit 3
  fi

  verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"

  tail -1 "$OUT" | sed 's/^/  /'
  local survivors
  survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    local n
    n=$(printf '%s\n' "$survivors" | wc -l)
    TOTAL_SURVIVORS=$((TOTAL_SURVIVORS + n))
    echo "  survivors ($n assertions still reported success):"
    printf '%s\n' "$survivors" | sed 's/^/    /'
  fi
  echo
}

# ---------------------------------------------------------------------------
# A1 - THE INVARIANT IS GONE ENTIRELY. Every response is a success as long as
# its body decodes. This is the shape of the bug DESIGN.md:340-345 exists to
# prevent, and every test claiming to assert the error rule must die here.
# ---------------------------------------------------------------------------
amputate "A1  evaluate_response applies NEITHER arm - every decodable body succeeds" \
  "$CLIENT" \
  '    envelope_code = _envelope_status_code(payload)' \
  '    return payload
    envelope_code = _envelope_status_code(payload)'

# ---------------------------------------------------------------------------
# A2 - arm 1 only. The 200-with-401-body trap (C5-S1) reopens; the recorded
# fixtures whose HTTP status is ALSO >= 400 still fail, via arm 2. Survivors
# here are expected and are the point: they show which cases were never
# testing arm 1 in the first place.
# ---------------------------------------------------------------------------
amputate "A2  the ENVELOPE arm is deleted (C5-S1 reopens)" "$CLIENT" \
  '    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(envelope_code, _envelope_message(payload))' \
  '    _ = envelope_code'

# ---------------------------------------------------------------------------
# A3 - arm 2 only. Symmetric to A2. A body with no status block arriving on a
# 5xx becomes a success.
# ---------------------------------------------------------------------------
amputate "A3  the HTTP-STATUS arm is deleted" "$CLIENT" \
  '    if http_status >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(http_status, _envelope_message(payload))' \
  '    pass'

# ---------------------------------------------------------------------------
# A4 - decoding never fails. Every undecodable body - plain text, HTML, XML,
# both malformed fixtures - becomes an empty dict, which then passes both arms.
# This is the "wrong zero that explains itself" in its purest form.
# ---------------------------------------------------------------------------
amputate "A4  _decode_json_object returns {} for anything it cannot parse" "$CLIENT" \
  '    text = body.decode("utf-8", errors="replace").strip()' \
  '    return {}
    text = body.decode("utf-8", errors="replace").strip()'

# ---------------------------------------------------------------------------
# A5 - markup handling is deleted outright. HTML and XML fall through to the
# JSON parser, which fails - so they still error, but by accident and with no
# defusedxml anywhere in the path. An entity bomb would reach json.loads
# instead of a hardened parser, which is a different (and quieter) failure.
# ---------------------------------------------------------------------------
# THE ANCHOR IS THE `if`, NOT THE BLOCK. It used to span the whole branch,
# comment included - and the comment was reflowed, so this row applied to
# nothing and silently tested nothing until the static anchor checker read it.
# A prose line inside an anchor is a line that WILL be rewrapped; anchoring on
# the condition alone amputates the same behaviour (the branch is unreachable,
# so `_raise_from_markup` is never called) with nothing reflowable in it.
amputate "A5  markup is never routed to defusedxml at all" "$CLIENT" \
  '    if text.startswith("<"):' \
  '    if False:  # AMPUTATED-A5'

# ---------------------------------------------------------------------------
# A6 - v2 authentication is gone. No credential headers are sent at all.
# ---------------------------------------------------------------------------
amputate "A6  v2 sends NO credential headers" "$CLIENT" \
  '        return {
            API_KEY_HEADER: self._api_key.get_secret_value(),
            API_SECRET_HEADER: self._api_secret.get_secret_value(),
            "Accept": "application/json",
        }' \
  '        return {"Accept": "application/json"}'

# ---------------------------------------------------------------------------
# A7 - the jobFeed route sends no credentials either, so the one route whose
# URL is classified sensitive stops being sensitive - and any test that only
# asserted "no secret in the log" would now pass for the wrong reason.
# ---------------------------------------------------------------------------
amputate "A7  the jobFeed route sends no credential parameters" "$CLIENT" \
  '        return {
            "api": self._api_key.get_secret_value(),
            "sc": self._api_secret.get_secret_value(),
            "companyId": self._company_id.get_secret_value(),
        }' \
  '        return {}'

# ---------------------------------------------------------------------------
# A8 - redaction is deleted from the excerpt path entirely. Whatever the body
# said reaches `detail` verbatim, unbounded.
# ---------------------------------------------------------------------------
amputate "A8  _excerpt neither redacts nor truncates" "$CLIENT" \
  '    redacted = redact_text(text)
    if len(redacted) <= MAX_BODY_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_BODY_EXCERPT_CHARS] + "... [truncated]"' \
  '    return text'

# ---------------------------------------------------------------------------
# A9 - M-5 REOPENED. The consumer's `detail` goes back to being formatted from
# the exception, which is what `backend/error-handling.md:383` and `:493`
# forbid. This is the exact pre-fix line, restored.
# ---------------------------------------------------------------------------
amputate "A9  M-5 reopened: the exception's text becomes the consumer's detail" "$CLIENT" \
  '            raise JobviteUnavailableError(_unavailable_detail(exc)) from None' \
  '            raise JobviteUnavailableError(
                redact_text(f"{type(exc).__name__}: {exc}")
            ) from None'

# ---------------------------------------------------------------------------
# A9b - and the same with no redaction at all: `str(exc)` verbatim. httpx puts
# the request URL into its exception text, so on the feed this publishes `sc=`
# straight to the caller.
# ---------------------------------------------------------------------------
amputate "A9b a transport error's text reaches the consumer unredacted" "$CLIENT" \
  '            raise JobviteUnavailableError(_unavailable_detail(exc)) from None' \
  '            raise JobviteUnavailableError(str(exc)) from None'

# ---------------------------------------------------------------------------
# A9c - THE NEGATIVE ARM. The enumerated detail collapses to one string. It
# leaks nothing, so M-5 stays fixed, and what dies is DESIGN.md:368-372's
# requirement that `detail` distinguish an upstream outage from an open
# breaker. A fix that makes `detail` useless passes M-5 and breaks the design;
# this row is what catches it.
# ---------------------------------------------------------------------------
amputate "A9c the enumerated detail says nothing a caller can act on" "$CLIENT" \
  '    if isinstance(exc, httpx2.TimeoutException):
        return UNAVAILABLE_TIMEOUT_DETAIL' \
  '    return "Jobvite is unavailable."
    if isinstance(exc, httpx2.TimeoutException):
        return UNAVAILABLE_TIMEOUT_DETAIL'

# ---------------------------------------------------------------------------
# A9d - L-1 UNWIRED AGAIN. `redact_headers` loses its one caller and the v2
# credential headers reach the log line in the clear.
# ---------------------------------------------------------------------------
# REPOINTED BY U7. `headers` is a `Mapping` parameter on `_attempt` now, so
# the call site reads `redact_headers(dict(headers))`. The SUBJECT is
# unchanged - `redact_headers` losing its one caller - and only the spelling
# moved.
amputate "A9d the v2 credential headers reach the log unredacted" "$CLIENT" \
  '                headers=redact_headers(dict(headers)),' \
  '                headers=dict(headers),'

# ---------------------------------------------------------------------------
# A9e - the exception text reaches the LOG unredacted. The consumer is still
# safe, so M-5 stays fixed; what dies is DESIGN.md:315-318's "never in an
# exception message, `sc=` redacted before any log line".
# ---------------------------------------------------------------------------
amputate "A9e the exception text is logged without redact_text" "$CLIENT" \
  '                error=redact_text(f"{type(exc).__name__}: {exc}"),' \
  '                error=f"{type(exc).__name__}: {exc}",'

# ---------------------------------------------------------------------------
# A9f - the failure is not logged AT ALL. The exception text now has nowhere
# else to go, so every control this fix RELOCATED to the log must die here.
# This is the row that proves the two transport cases are not asserting
# absence against an empty list.
# ---------------------------------------------------------------------------
amputate "A9f the transport failure is never logged (relocated controls go vacuous)" "$CLIENT" \
  '            logger.warning(
                "jobvite transport failure",
                method=method,
                route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
                headers=redact_headers(dict(headers)),
                error=redact_text(f"{type(exc).__name__}: {exc}"),
            )' \
  '            pass'

# ---------------------------------------------------------------------------
# A10 - the cookie jar is never cleared. Not httpx2's default behaviour being
# relied on: the default is to KEEP them, so this restores the default.
# ---------------------------------------------------------------------------
amputate "A10 the cookie jar is never cleared" "$CLIENT" \
  '            self._client.cookies.clear()' \
  '            pass'

# ---------------------------------------------------------------------------
# A11 - the ONE request entry point stops logging anything. Every "no secret
# reached the log" assertion that lacks a paired positive passes vacuously
# against a silent logger, and this row is what proves whether ours has one.
# ---------------------------------------------------------------------------
amputate "A11 the request path logs NOTHING (absence assertions go vacuous)" "$CLIENT" \
  '        logger.debug(
            "jobvite request",
            method=method,
            route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
        )' \
  '        pass'

# ---------------------------------------------------------------------------
# A12 - the route-level 404 distinction. There is no code to delete here, which
# is itself the finding: §9 hazard 7 is honoured by the ABSENCE of a mapping
# from 404 to ResourceNotFoundError. So this row amputates the property from
# the other side - it INTRODUCES the mapping the hazard forbids - and asks
# whether anything notices. An amputation that adds code is unusual and is
# stated as such rather than dressed up as a deletion.
# ---------------------------------------------------------------------------
# The injection goes at the TOP of evaluate_response, BEFORE arm 1. An earlier
# revision of this row put it after arm 1 and the whole suite stayed green,
# because arm 1 already raises for the recorded fixture's 404 envelope and the
# injected branch was unreachable. The row tested nothing and said so by passing
# 36/36 - a survivor that was an instrument fault, not a finding about the code.
amputate "A12 a route-level 404 IS mapped to a record-level not-found" "$CLIENT" \
  '    envelope_code = _envelope_status_code(payload)' \
  '    from ..errors import ResourceNotFoundError

    envelope_code = _envelope_status_code(payload)
    if envelope_code == 404 or http_status == 404:
        raise ResourceNotFoundError(_envelope_message(payload))'

# The canonical result line's row count, from the harness's own
# counter. This harness declares no ROW_FLOOR, so the floor is 0:
# 0 is not a floor anything can breach, and it reads as absent.
harness_result_ran "$HR_COUNTED_ROWS" 0
# THE ANCHOR TALLY, published as a named field (task #152). The same two
# counters the rows maintained all along. `applied` is the field, not
# `killed`: survivors are this harness's OUTPUT and are not a failure, so
# there is no kill tally to report - what CAN silently go wrong is a row
# whose anchor stopped matching, and that is what this counts.
# PRINTED BESIDE THE FIELD, in the phrasing every other
# anchors-applied harness uses. check-harness-result.sh requires the
# set that PUBLISHES a tally to equal the set that PRINTS one: a
# published field with nothing printed has no second reading to
# disagree with, which is the whole point of publishing it. This was
# invisible on #152's branch because the field only appears once the
# --anchors-applied flag is wired, and ci.yml was contended there.
echo "########## ROWS: $HR_COUNTED_ROWS   ANCHORS APPLIED: $HR_APPLIED"
harness_result_tally applied "$HR_APPLIED" "$HR_COUNTED_ROWS"
echo "########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: $TOTAL_SURVIVORS"
echo "(Survivors are the OUTPUT. Read each one and say why it survived.)"
