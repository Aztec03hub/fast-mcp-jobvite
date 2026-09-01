#!/usr/bin/env bash
# U3 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation  asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything still
#                    report success?
#
# U11 deleted its flag emission outright and the run still exited 0, so an
# exit-code-only suite would have passed it. Amputation has exposed a vacuous
# assertion in every unit built on this project so far, and it is the only
# instrument that finds a test which passes because its subject is absent
# rather than because its subject is correct.
#
# SURVIVORS ARE THE OUTPUT, not the failure. For each amputation this prints
# the counts and NAMES every test that still passed, so the report can say
# which assertions survived and why, rather than asserting that none did.
#
# It exits non-zero only if it could not run, if the intact baseline is red,
# or if an amputation left the tree dirty.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size), and an
# amputation that replaces a body with `pass` can be the same size inside one
# second, in which case the interpreter reuses stale bytecode and the amputated
# code never runs. That failure is silent and it fakes a clean result.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

AUDIT="src/fast_mcp_jobvite/audit.py"
REDACT="src/fast_mcp_jobvite/utils/redaction.py"
# tests/test_logging_process.py is in the suite deliberately. U3's assertions
# all ran against a sink the FIXTURE installed, which is a real loguru stream
# and not the one the server writes to - so A1 (emit() writes nothing) left
# `test_arm1_before_the_side_effect_the_call_fails` green. The process arms
# observe what the child actually wrote, so an amputated emit() has nowhere
# to hide.
SUITE="tests/test_audit.py tests/test_redaction.py tests/test_logging_process.py"
OUT=/tmp/u3-amp.txt

if ! git diff --quiet -- "$AUDIT" "$REDACT"; then
  echo "ABORT: $AUDIT or $REDACT has uncommitted changes."
  echo "This harness restores with 'git checkout --', which would DISCARD them."
  exit 3
fi

echo "########## BASELINE - the intact tree"
timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
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
  # `grep -F` with a multi-line pattern treats each line as an alternative, so
  # an unchanged line inside a multi-line amputation matches a clean file and
  # reports the opposite of the truth.
  if git diff --quiet -- "$file"; then
    echo "  AMPUTATION DID NOT LAND despite a successful write"
    echo
    return
  fi

  timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - this row NEVER FINISHED. Not a kill,"
    echo "  not a survivor: no verdict below is a measurement of this row."
  fi

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
# A1 - the audit event is not emitted AT ALL.
# This is U11's exact failure shape: the emission deleted, the run still green.
# Everything that claims to assert "the event exists and carries X" must die.
# ---------------------------------------------------------------------------
amputate "A1  emit() writes NOTHING - the audit stream is silent" "$AUDIT" \
  '    try:
        logger.bind(**event.to_record()).info(AUDIT_EVENT_NAME)
    except Exception as exc:  # noqa: BLE001 - the policy is defined over ANY failure
        return _on_audit_write_failure(exc, event, phase)
    return []' \
  '    return []'

# ---------------------------------------------------------------------------
# A2 - arguments reach the event UNREDACTED. §8 #2 and #5 must both die.
# ---------------------------------------------------------------------------
amputate "A2  redact_arguments is not called on the way in" "$AUDIT" \
  '            arguments=redact_arguments(arguments),' \
  '            arguments=arguments,'

# ---------------------------------------------------------------------------
# A3 - the stdio attribution marker does not exist.
# ---------------------------------------------------------------------------
amputate "A3  caller_attribution always returns None" "$AUDIT" \
  '        return ATTRIBUTION_UNAVAILABLE if self.transport is Transport.STDIO else None' \
  '        return None'

# ---------------------------------------------------------------------------
# A4 - trace context is never read. §8 #17 arm 1 must die; arm 2 SURVIVES by
# construction, and that is the whole reason arm 2 alone is not the case.
# ---------------------------------------------------------------------------
amputate "A4  the traceparent is never read" "$AUDIT" \
  '        trace = parse_trace_context(meta)' \
  '        trace = None'

# ---------------------------------------------------------------------------
# A5 - the failure policy does not exist: every branch returns no warning and
# raises nothing.
# ---------------------------------------------------------------------------
amputate "A5  the three-branch failure policy is deleted" "$AUDIT" \
  '    detail = redact_text(f"{type(exc).__name__}: {exc}")' \
  '    return []
    detail = redact_text(f"{type(exc).__name__}: {exc}")'

# ---------------------------------------------------------------------------
# A6 - the warnings array is never attached to the success payload.
# ---------------------------------------------------------------------------
amputate "A6  attach_audit_warnings returns the payload untouched" "$AUDIT" \
  '    if not warnings:
        return dict(structured_content)
    return {**structured_content, "warnings": list(warnings)}' \
  '    return dict(structured_content)'

# ---------------------------------------------------------------------------
# A7 - request_id_var is never bound. U2 built the scope; if nothing here
# notices its absence then U3 does not actually use it.
# ---------------------------------------------------------------------------
amputate "A7  request_id_var is never bound" "$AUDIT" \
  '    # DESIGN.md:664-666: minted and bound in the same statement.
    with request_id_scope(resolve_request_id(inbound_request_id)) as request_id:' \
  '    request_id = resolve_request_id(inbound_request_id)
    if True:'

# ---------------------------------------------------------------------------
# A8 - URL redaction does nothing at all.
# ---------------------------------------------------------------------------
amputate "A8  redact_url returns its input unchanged" "$REDACT" \
  '    split = urllib.parse.urlsplit(url)' \
  '    return url
    split = urllib.parse.urlsplit(url)'

# ---------------------------------------------------------------------------
# A9 - argument redaction does nothing at all.
# ---------------------------------------------------------------------------
amputate "A9  redact_arguments returns its input unchanged" "$REDACT" \
  '    if isinstance(arguments, Mapping):' \
  '    return arguments
    if isinstance(arguments, Mapping):'

# ---------------------------------------------------------------------------
# A10 - the stderr failure channel is deleted. DESIGN.md:790-791 says the
# report must NOT go down the audit stream that just failed, so if nothing
# notices stderr going silent, that requirement is untested.
# ---------------------------------------------------------------------------
# The anchor uses a SINGLE backslash. Bash single quotes are literal, so a
# doubled one looks for two backslashes and an n - the row then reports
# "anchor not unique (0 hits)", which reads exactly like a refactor having
# moved the line rather than like a quoting mistake in the harness itself.
amputate "A10 nothing is written to stderr" "$AUDIT" \
  '    sys.stderr.write(f"{message}\n")' \
  '    return None'

echo "########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: $TOTAL_SURVIVORS"
echo "(Survivors are the OUTPUT. Read each one and say why it survived.)"
