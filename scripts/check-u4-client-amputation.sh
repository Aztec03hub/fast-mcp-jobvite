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
# APPLIED ITS ANCHOR, not on this exit code.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size), and an
# amputation that replaces a body with `pass` can be the same size inside one
# second, in which case the interpreter reuses stale bytecode and the amputated
# code never runs. That failure is silent and it fakes a clean result.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_jobvite_client.py"
OUT=/tmp/u4-amp.txt

if ! git diff --quiet -- "$CLIENT"; then
  echo "ABORT: $CLIENT has uncommitted changes."
  echo "This harness restores with 'git checkout --', which would DISCARD them."
  exit 3
fi

echo "########## BASELINE - the intact tree"
if ! uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1; then
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
amputate() {
  local label="$1" file="$2" old="$3" new="$4"

  echo "########## $label"

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

  uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "  RESTORE FAILED - $file still differs from the commit. STOPPING."
    exit 3
  fi

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
# its body decodes. This is the shape of the bug DESIGN.md:328-333 exists to
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
# leaks nothing, so M-5 stays fixed, and what dies is DESIGN.md:356-360's
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

echo "########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: $TOTAL_SURVIVORS"
echo "(Survivors are the OUTPUT. Read each one and say why it survived.)"
