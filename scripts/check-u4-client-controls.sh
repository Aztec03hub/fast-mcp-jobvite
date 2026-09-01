#!/usr/bin/env bash
# U4 MUTATION harness: change one value, require a NAMED test to go red.
#
# This is half of U4's control story. The other half is
# `check-u4-client-amputation.sh`, which asks the different and harder question
# ("delete the behaviour outright - does anything still report success?").
# Amputation has exposed a vacuous assertion in every unit built on this project
# so far, so a value-mutation harness on its own is not sufficient evidence.
#
# Each row below names the test that MUST fail. A mutation that turns the suite
# red somewhere else is not a pass: it would prove only that the suite is
# sensitive to something, not that the assertion the design relies on is the one
# watching. That is the difference between a control and a coincidence.
#
# THE ROW THAT MATTERS MOST IS M02. DESIGN.md:344-345's first arm is C5-S1, the
# only Critical on the client: HTTP 200 with {"status":{"code":401}}. If M02
# does not kill `test_C5_S1_...`, this unit has not been verified at all.
#
# PYTHONDONTWRITEBYTECODE=1 is not optional. `.pyc` invalidation keys on
# (mtime, size), and several mutations here are the same size as the line they
# replace; inside one second the interpreter would reuse stale bytecode and the
# mutant would never run.
#
# Every mutation is checked against GIT before the suite runs (it landed) and
# again after the restore (it is gone). Never with `grep -F`: with a multi-line
# pattern grep treats each line as a separate alternative, so an unchanged line
# inside a multi-line mutation matches a clean file and reports the opposite of
# the truth. That instrument error cost U3 a false "RESTORE FAILED".

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_jobvite_client.py"

PASS=0
FAIL=0

if ! git diff --quiet -- "$CLIENT"; then
  echo "ABORT: $CLIENT has uncommitted changes."
  echo "This harness restores with 'git checkout --', which would DISCARD them."
  exit 3
fi

echo "########## BASELINE - the intact tree"
timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider >/tmp/u4-base.txt 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 /tmp/u4-base.txt
  exit 3
fi
tail -1 /tmp/u4-base.txt
echo

# ---------------------------------------------------------------------------
# run_mutation <id> <file> <old> <new> <test-that-must-fail>
# ---------------------------------------------------------------------------
run_mutation() {
  local id="$1" file="$2" old="$3" new="$4" want="$5"

  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
if s.count(old) != 1:
    print(f"  ANCHOR NOT UNIQUE ({s.count(old)} hits): {old!r}", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  then
    echo "$id: COULD NOT APPLY - the anchor moved. Fix the harness."
    FAIL=$((FAIL + 1))
    return
  fi

  if git diff --quiet -- "$file"; then
    echo "$id: MUTATION DID NOT LAND despite a successful write"
    FAIL=$((FAIL + 1))
    return
  fi

  timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rf >/tmp/u4-mut.txt 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - this row NEVER FINISHED. Not a kill,"
    echo "  not a survivor: no verdict below is a measurement of this row."
  fi

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "$id: RESTORE FAILED - $file still differs from the commit. STOPPING."
    exit 3
  fi

  # The NAMED test must be among the failures. A red suite is not enough.
  if grep -qE "^FAILED $SUITE::$want" /tmp/u4-mut.txt; then
    echo "$id: KILLED by $want"
    PASS=$((PASS + 1))
  else
    echo "$id: SURVIVED - $want did not fail. Suite result was:"
    tail -1 /tmp/u4-mut.txt | sed 's/^/      /'
    grep -E '^FAILED ' /tmp/u4-mut.txt | sed 's/^/      also-red: /' | head -5
    FAIL=$((FAIL + 1))
  fi
}

# ===========================================================================
# THE INVARIANT (DESIGN.md:344-345). M01-M04 are the reason this file exists.
# ===========================================================================

# M01 - the boundary itself. `>= 400` becomes `> 400`, so a status.code of
# exactly 400 - a real Jobvite code - is read as a success.
run_mutation "M01 the envelope threshold moves off 400" "$CLIENT" \
  '    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:' \
  '    if envelope_code is not None and envelope_code > ERROR_STATUS_THRESHOLD:' \
  'test_a_status_code_under_400_in_the_envelope_is_not_an_error'

# M02 - **C5-S1**. The envelope arm stops firing. This is the 200-with-401-body
# trap: the recorded fixture comes back as a SUCCESS with no candidates key.
# If this row ever survives, stop and read the report before shipping anything.
run_mutation "M02 the envelope arm never fires (C5-S1)" "$CLIENT" \
  '    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:' \
  '    if envelope_code is None and envelope_code >= ERROR_STATUS_THRESHOLD:' \
  'test_C5_S1_an_http_200_carrying_a_401_body_is_NOT_a_success'

# M03 - the HTTP arm stops firing for everything below 600, which is every
# status that exists. DESIGN.md:344-345 says BOTH arms, every call.
run_mutation "M03 the HTTP-status arm never fires" "$CLIENT" \
  '    if http_status >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(http_status, _envelope_message(payload))' \
  '    if http_status >= 600:
        raise JobviteUpstreamError(http_status, _envelope_message(payload))' \
  'test_arm_2_an_http_500_with_a_passing_envelope_still_fails'

# M04 - the arms become mutually exclusive. This is the subtle one: with `elif`
# the code still looks like it checks both, and every fixture whose envelope
# carries a failing code still fails. Only a body that passes arm 1 and fails
# arm 2 can tell the difference.
run_mutation "M04 the two arms become an if/elif instead of two statements" "$CLIENT" \
  '    envelope_code = _envelope_status_code(payload)
    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(envelope_code, _envelope_message(payload))' \
  '    envelope_code = _envelope_status_code(payload)
    if envelope_code is not None:
        if envelope_code >= ERROR_STATUS_THRESHOLD:
            raise JobviteUpstreamError(envelope_code, _envelope_message(payload))
        return payload' \
  'test_arm_2_an_http_500_with_a_passing_envelope_still_fails'

# M05 - a JSON body that will not decode degrades to an empty dict. This is the
# "wrong zero" arriving by a different road from C5-S1.
# REPOINTED BY U7: a bare `except ValueError:` now has TWO hits in the client
# (`_decode_json_object` and `_retry_after_seconds`), so the anchor carries the
# comment that belongs to THIS one. The mutation is unchanged.
run_mutation "M05 an undecodable body degrades to an empty result" "$CLIENT" \
  '    except ValueError:
        # Plain text with no Content-Type' \
  '    except ValueError:
        return {}
    except TypeError:
        # Plain text with no Content-Type' \
  'test_a_malformed_body_fails_loudly_rather_than_degrading'

# M06 - a boolean is accepted as a status code. `{"code": true}` would then be
# compared as 1 and read as a success, or as an error if the value were large.
run_mutation "M06 a boolean status code is read as an integer" "$CLIENT" \
  '    if isinstance(code, bool) or not isinstance(code, int):' \
  '    if not isinstance(code, int):' \
  'test_a_boolean_status_code_is_not_read_as_an_integer'

# ===========================================================================
# The three error encodings, and the XML hardening.
# ===========================================================================

# M07 - markup is no longer recognised, so the Tomcat HTML page and any XML
# fall through to the JSON parser.
run_mutation "M07 markup bodies are not recognised as markup" "$CLIENT" \
  '    if text.startswith("<"):' \
  '    if text.startswith("\x00"):' \
  'test_hr_xml_is_treated_as_an_error_body_never_as_a_success'

# M08 - the XML error code is discarded, so an HR-XML error loses the one piece
# of information that says WHAT failed.
run_mutation "M08 the HR-XML error code is discarded" "$CLIENT" \
  '            int(code) if code is not None and code.isdigit() else None,' \
  '            None,' \
  'test_hr_xml_is_treated_as_an_error_body_never_as_a_success'

# ===========================================================================
# Credentials. DESIGN.md:312-318.
# ===========================================================================

# M09 - the redactor and the client stop naming the same header. This fails
# OPEN and silently: a redactor that matches nothing still returns a mapping.
run_mutation "M09 the secret header is renamed out from under the redactor" "$CLIENT" \
  'API_SECRET_HEADER: Final = "x-jvi-sc"  # noqa: S105' \
  'API_SECRET_HEADER: Final = "x-jvi-secret"  # noqa: S105' \
  'test_the_client_and_the_redactor_name_the_SAME_two_headers'

# M10 - v2 credentials move into the query string, which is exactly what
# Jobvite's own published sample code does and what DESIGN.md:312-313 forbids.
run_mutation "M10 v2 credentials are put in the URL instead of the headers" "$CLIENT" \
  '            headers = self.v2_headers()
            query = dict(params or {})' \
  '            headers = {"Accept": "application/json"}
            query = {
                **dict(params or {}),
                "api": self._api_key.get_secret_value(),
                "sc": self._api_secret.get_secret_value(),
            }' \
  'test_v2_credentials_travel_as_headers_and_NEVER_in_the_url'

# M11 - the jobFeed route silently loses its companyId requirement, so a
# missing credential becomes a 401 that looks like a bad secret.
# REPOINTED BY U7: R2-L-4 changed what this branch RAISES - it was
# `JobviteUpstreamError(None, ...)`, which rendered "Jobvite returned status
# none" at 502 for a call Jobvite never saw, and is a `RuntimeError` now
# (ADR-0017 routes it to /problems/internal-error 500). The mutation's subject,
# the requirement disappearing, is unchanged.
run_mutation "M11 the jobFeed route no longer requires a companyId" "$CLIENT" \
  '        if self._company_id is None:
            msg = (' \
  '        if self._company_id is None and False:
            msg = (' \
  'test_the_jobfeed_route_refuses_without_a_company_id'

# ===========================================================================
# §8 #2 - no secret reaches a log record. Joins U3's case.
# ===========================================================================

# M12 - the exception-message redaction arm is removed. `httpx` puts the
# request URL in its exception text, and on the feed that URL carries `sc=`.
#
# THE ANCHOR MOVED WHEN M-5 WAS FIXED and the harness said so only in a line
# the CI step did not read: `COULD NOT APPLY` left the run at exit 0 with
# "16 killed, 1 not killed", and the step gates on the exit code and on
# `killed > 0`. The exception text is no longer built for the consumer's
# `detail`; it is built for the log line, and that is where the arm lives now.
run_mutation "M12 a transport error is no longer redacted" "$CLIENT" \
  '                error=redact_text(f"{type(exc).__name__}: {exc}"),' \
  '                error=f"{type(exc).__name__}: {exc}",' \
  'test_a_transport_error_on_the_jobfeed_route_is_redacted'

# M12b - the enumerated consumer detail is replaced by the exception text.
# M-5 itself, as a mutation rather than an amputation.
run_mutation "M12b the consumer detail is formatted from the exception again" "$CLIENT" \
  '            raise JobviteUnavailableError(_unavailable_detail(exc)) from None' \
  '            raise JobviteUnavailableError(str(exc)) from None' \
  'test_a_transport_error_on_the_jobfeed_route_is_redacted'

# M12c - `redact_headers` loses its one caller (L-1, unwired again).
# REPOINTED BY U7, same cause as the amputation harness's A9d: `headers` is a
# `Mapping` parameter now and the call site reads `redact_headers(dict(...))`.
run_mutation "M12c the v2 credential headers reach the log unredacted" "$CLIENT" \
  '                headers=redact_headers(dict(headers)),' \
  '                headers=dict(headers),' \
  'test_the_v2_credential_headers_are_redacted_in_the_failure_log'

# M13 - the body excerpt stops being redacted, so an error body that quotes the
# request URL back at us publishes the credential into `detail`.
run_mutation "M13 the error-body excerpt is no longer redacted" "$CLIENT" \
  '    redacted = redact_text(text)' \
  '    redacted = text' \
  'test_an_error_body_quoting_a_credential_is_redacted_before_detail'

# M14 - truncation is removed, so a body we do not control becomes an unbounded
# log line.
run_mutation "M14 the error-body excerpt is no longer truncated" "$CLIENT" \
  '    if len(redacted) <= MAX_BODY_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_BODY_EXCERPT_CHARS] + "... [truncated]"' \
  '    return redacted' \
  'test_an_enormous_error_body_is_truncated_before_reaching_detail'

# ===========================================================================
# Transport hygiene.
# ===========================================================================

# M15 - the cookie jar is kept. JOBVITE-CONTRACT.md 2.3: the AWSALBAPP-* values
# are the literal `_remove_` and there is no session to carry. This is NOT
# httpx2's default, which is why removing one line is enough to break it.
run_mutation "M15 the cookie jar is carried between requests" "$CLIENT" \
  '            self._client.cookies.clear()' \
  '            pass' \
  'test_no_cookie_jar_is_carried_between_requests'

# M16 - the per-phase timeout collapses to a single scalar, which is what
# DESIGN.md:358 forbids ("No SDK default, no single scalar").
# REPOINTED BY U7: the four phases are NAMED CONSTANTS now
# (DEFAULT_CONNECT_TIMEOUT and its three siblings) rather than inline literals,
# and the construction moved out of the `AsyncClient(...)` call so
# `_attempt_timeout` can clamp it to the outbound budget. DESIGN.md:358's
# subject - "no single scalar" - is what this row still mutates.
run_mutation "M16 the per-phase timeout becomes a single scalar" "$CLIENT" \
  '        self._timeout = timeout or httpx2.Timeout(
            connect=DEFAULT_CONNECT_TIMEOUT,
            read=DEFAULT_READ_TIMEOUT,
            write=DEFAULT_WRITE_TIMEOUT,
            pool=DEFAULT_POOL_TIMEOUT,
        )' \
  '        self._timeout = timeout or httpx2.Timeout(30.0)' \
  'test_the_module_declares_an_explicit_per_phase_timeout'

# M17 - a decode failure on a 200 claims Jobvite returned 200 as the error,
# which inverts the meaning of the field.
run_mutation "M17 a 200 is reported as the upstream failure status" "$CLIENT" \
  '    return http_status if http_status >= ERROR_STATUS_THRESHOLD else None' \
  '    return http_status' \
  'test_a_malformed_body_on_a_200_reports_no_upstream_status'

echo
echo "########## RESULT: $PASS killed, $FAIL not killed"

# THE ROW FLOOR. `FAIL -eq 0` is satisfied by a harness with no rows at
# all: delete every `run_mutation` call and this prints "0 killed, 0 not
# killed" and exits 0. The row count is PASS + FAIL, since every row
# lands in exactly one of them. DERIVED: this harness printed
# "########## RESULT: 19 killed, 0 not killed" at cf30446 - NINETEEN,
# while its labels run M01..M17, because M12 carries an M12b and an M12c
# beside it. Read the tally; the highest M-number is not the row count.
# Lowering this number is a visible diff that has to be defended.
ROW_FLOOR=19
ROWS=$((PASS + FAIL))
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "########## $ROWS/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

[ "$FAIL" -eq 0 ] || exit 1
