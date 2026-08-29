#!/usr/bin/env bash
# U3 MUTATION harness: change one value, require a NAMED test to go red.
#
# This is half of U3's control story. The other half is
# `check-u3-audit-amputation.sh`, which asks the different and harder question
# ("delete the behaviour outright - does anything still report success?").
# U11 found that deleting its flag emission entirely still exited 0, so a
# harness that only mutates values would have passed it.
#
# Each row below names the test that MUST fail. A mutation that turns the suite
# red somewhere else is not a pass: it would prove only that the suite is
# sensitive to something, not that the assertion the design relies on is the one
# watching. That is the difference between a control and a coincidence.
#
# PYTHONDONTWRITEBYTECODE=1 is not optional. `.pyc` invalidation keys on
# (mtime, size), and several mutations here are the same size as the line they
# replace; inside one second the interpreter would reuse stale bytecode and the
# mutant would never run.
#
# Every mutation is grepped for BEFORE the suite runs (it landed) and the file
# is grepped again AFTER the restore (it is gone), because `git checkout --` is
# how a mutation harness silently reverts the fix it was meant to be testing.

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

PASS=0
FAIL=0

if ! git diff --quiet -- "$AUDIT" "$REDACT"; then
  echo "ABORT: $AUDIT or $REDACT has uncommitted changes."
  echo "This harness restores with 'git checkout --', which would DISCARD them."
  exit 3
fi

echo "########## BASELINE - the intact tree"
if ! uv run --frozen pytest $SUITE -q -p no:cacheprovider >/tmp/u3-base.txt 2>&1; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 /tmp/u3-base.txt
  exit 3
fi
tail -1 /tmp/u3-base.txt
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

  # The mutation LANDED. This is the control on the control: a replace that
  # silently did nothing gives a green run that means nothing.
  #
  # Compared against GIT, not with grep. An earlier revision of this harness
  # grepped for the replacement text, and `grep -F` with a MULTI-LINE pattern
  # treats each line as a separate alternative - so a multi-line mutation whose
  # first line was an unchanged `if not meta:` matched the RESTORED file and
  # reported a restore failure that had not happened. The instrument was wrong,
  # not the code. `git diff` compares the whole file against the commit and
  # cannot be fooled that way.
  if git diff --quiet -- "$file"; then
    echo "$id: MUTATION DID NOT LAND despite a successful write"
    FAIL=$((FAIL + 1))
    return
  fi

  uv run --frozen pytest $SUITE -q -p no:cacheprovider -rf >/tmp/u3-mut.txt 2>&1
  local rc=$?

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "$id: RESTORE FAILED - $file still differs from the commit. STOPPING."
    exit 3
  fi

  if [ "$rc" -eq 0 ]; then
    echo "$id: SURVIVED - the suite stayed green. NOT A CONTROL."
    FAIL=$((FAIL + 1))
  elif grep -q "$want" /tmp/u3-mut.txt; then
    echo "$id: killed by $want"
    PASS=$((PASS + 1))
  else
    echo "$id: suite went red, but NOT at $want - a coincidence, not a control"
    grep -E '^FAILED' /tmp/u3-mut.txt | sed 's/^/      /' | head -5
    FAIL=$((FAIL + 1))
  fi
}

echo "########## MUTATIONS"

# --- the stdio attribution marker (DESIGN.md:698-703) ----------------------
run_mutation "M1  stdio records the literal \"global\"" "$AUDIT" \
  'ATTRIBUTION_UNAVAILABLE: Final = "unavailable:stdio-has-no-caller-token"' \
  'ATTRIBUTION_UNAVAILABLE: Final = "global"' \
  'test_stdio_never_records_the_literal_global'

run_mutation "M2  stdio keeps the client id instead of discarding it" "$AUDIT" \
  'client_id=client_id if transport is Transport.HTTP else None,' \
  'client_id=client_id,' \
  'test_stdio_never_records_the_literal_global'

# --- trace context, both arms (DESIGN.md:663-665, :1287-1292) ---------------
run_mutation "M3  trace fields emitted as None instead of omitted" "$AUDIT" \
  'record.update({key: v for key, v in optional.items() if v is not None})' \
  'record.update(optional)' \
  'test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none'

run_mutation "M4  trace id SYNTHESISED when the caller sent none" "$AUDIT" \
  '    if not meta:
        return None' \
  '    if not meta:
        return uuid.uuid4().hex, uuid.uuid4().hex[:16]' \
  'test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none'

run_mutation "M5  an all-zero traceparent accepted as a real join" "$AUDIT" \
  'r"\A00-(?!0{32})([0-9a-f]{32})-(?!0{16})([0-9a-f]{16})-[0-9a-f]{2}\Z"' \
  'r"\A00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}\Z"' \
  'test_case17_a_malformed_traceparent_yields_nothing_rather_than_a_guess'

# --- the three-branch failure policy (DESIGN.md:711-727) -------------------
run_mutation "M6  a pre-write audit failure no longer fails the call" "$AUDIT" \
  '    if phase is AuditPhase.BEFORE_SIDE_EFFECT:' \
  '    if False:' \
  'test_arm1_before_the_side_effect_the_call_fails'

run_mutation "M7  a post-write audit failure returns no warning" "$AUDIT" \
  '    if phase is AuditPhase.AFTER_WRITE:' \
  '    if False:' \
  'test_arm3'

run_mutation "M8  a read surfaces a warning it must not surface" "$AUDIT" \
  '    # AuditPhase.READ: log to stderr and continue. A read is recoverable
    # and losing the tool is worse than losing one audit line.
    return []' \
  '    return ["audit write failed"]' \
  'test_arm2_on_a_read_it_logs_to_stderr_and_continues'

# --- request_id (DESIGN.md:597-606) ----------------------------------------
run_mutation "M9  an inbound request id echoed WITHOUT validation" "$AUDIT" \
  '    if inbound_request_id is not None and _UUID4_RE.match(inbound_request_id):' \
  '    if inbound_request_id is not None:' \
  'test_an_invalid_inbound_request_id_is_replaced_rather_than_used'

# The anchor carries the comment line above it. The `with` line ALONE appears
# twice - once in the module docstring, which quotes it as the proof that the
# mint and the bind are one statement - and the harness refused to guess which.
run_mutation "M10 the var is set directly, losing correlation.py's finally" "$AUDIT" \
  '    # DESIGN.md:604-606: minted and bound in the same statement.
    with request_id_scope(resolve_request_id(inbound_request_id)) as request_id:' \
  '    request_id = resolve_request_id(inbound_request_id)
    request_id_var.set(request_id)
    if True:' \
  'test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself'

# --- redaction (DESIGN.md:312-318) -----------------------------------------
run_mutation "M11 sc= dropped from the secret parameter set" "$REDACT" \
  'frozenset({"api", "sc", "companyid"})' \
  'frozenset({"api", "companyid"})' \
  'test_case2'

run_mutation "M12 the parameter match becomes case-sensitive" "$REDACT" \
  'if key.lower() in SECRET_QUERY_PARAMS else value' \
  'if key in SECRET_QUERY_PARAMS else value' \
  'test_uppercase_parameter_names_are_still_redacted'

run_mutation "M13 arguments become a DENY-list: unlisted keys pass through" "$REDACT" \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS' \
  '                if key not in ("password",)' \
  'test_an_unlisted_argument_key_is_redacted'

# M14 is the row that EARNED this harness. Its first form removed the container
# walk and SURVIVED - which was not a weak test but a wrong mutation: with the
# walk gone the container was redacted whole, so nothing leaked. Chasing that
# down found the real defect the walk was hiding, and this is the mutation that
# reinstates it.
run_mutation "M14 the allow-list becomes leaf-keyed instead of path-keyed" "$REDACT" \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS
                else _redacted_value(value)' \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS
                or isinstance(value, Mapping | list)
                else _redacted_value(value)' \
  'test_a_container_under_an_unlisted_key_is_redacted_WHOLE'

# The anchor was `out.append(redact_url(token) if ... else token)` until R2's
# nit-3 split the trailing-punctuation run off the token, which turned that
# expression into an if/else block. Repointed at the redacting call itself,
# which is the SUBJECT of the mutation and the smallest thing that survives a
# reflow of the lines around it.
run_mutation "M15 the exception-message arm stops redacting" "$REDACT" \
  'out.append(redact_url(core) + token[len(core) :])' \
  'out.append(token)' \
  'test_a_url_embedded_in_an_exception_message_is_redacted'

echo
echo "########## RESULT: $PASS killed, $FAIL not killed"
[ "$FAIL" -eq 0 ] || exit 1
