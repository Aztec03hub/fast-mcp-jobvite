#!/usr/bin/env bash
# U1 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation asks: "break one rule - does the named test notice?"
#   Amputation asks: "remove the SUBJECT ENTIRELY - does anything still
#   report success?"
#
# In every unit built on this project so far, amputation found an assertion
# that survived mutation and was vacuous. A test that passes when its
# subject is not there is not a weak test, it is a false instrument.
#
# TWO KINDS OF SURVIVOR, AND ONLY ONE IS A FAILURE.
#
#   An assertion whose subject this row does not touch passing is not news:
#   it passes on an intact tree for the same reason. Those are printed as
#   CONTEXT and do not affect the exit code.
#
#   An assertion that EXISTS TO NOTICE this row's amputation and passes
#   anyway is an UNEXPECTED SURVIVOR. That is a false instrument, it is the
#   finding this file is for, and it EXITS 1. Each row declares those ids in
#   a `MUST_DIE` array; see the long comment above `report`.
#
# Exit 0 = every declared assertion died on every row. 1 = an unexpected
# survivor, or a row that timed out and therefore measured nothing. 3 = could
# not run: the intact baseline is red, or a declared id no longer exists.
#
# PYTHONDONTWRITEBYTECODE=1 on every run, and the tree is restored from a
# byte copy taken at the top (never `git checkout --`, which would revert
# uncommitted work along with the amputation).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CONFIG="src/fast_mcp_jobvite/config.py"
MAIN="src/fast_mcp_jobvite/__main__.py"
SERVER="src/fast_mcp_jobvite/server.py"
SUITE="tests/test_config.py tests/test_boot.py tests/test_shutdown.py tests/test_server.py tests/test_logging_process.py"

WORK="$(mktemp -d)"
trap 'cp "$WORK/config.py" "$CONFIG"; cp "$WORK/__main__.py" "$MAIN"; \
      cp "$WORK/server.py" "$SERVER"; rm -rf "$WORK"' EXIT
cp "$CONFIG" "$WORK/config.py"
cp "$MAIN" "$WORK/__main__.py"
cp "$SERVER" "$WORK/server.py"

restore() {
  cp "$WORK/config.py" "$CONFIG"
  cp "$WORK/__main__.py" "$MAIN"
  cp "$WORK/server.py" "$SERVER"
}

# WHY EVERY ROW NOW DECLARES WHAT IT MUST KILL.
#
# For one revision this harness printed EVERY passing test as a "survivor".
# That made the word mean "passed": row L removes the sink's redactor and
# reported 82 survivors, of which exactly ONE - the redaction test - was
# about redaction at all. The other 81 are tests whose subject row L does
# not touch, and they pass for the same reason they pass on an intact tree.
# A reader looking for a vacuous assertion had to tell those apart by hand,
# and the one signal that matters was 1 line in 82.
#
# Worse, the harness could not go red. It exited 0 whatever it found, so a
# row that stopped amputating anything - an anchor that moved, a `re.sub`
# that matched nothing, a rename - would report a longer survivor list and
# still exit 0, which is indistinguishable from a clean run to anything
# automated and to most humans. A harness that cannot fail is worse than no
# harness: it occupies the space a real check would take.
#
# So each row now names the assertions that EXIST TO NOTICE IT. Those are
# `MUST_DIE`. The full passed list is still printed, relabelled as the
# context it always was; a MUST_DIE test that passes is an UNEXPECTED
# SURVIVOR, and that is the finding this harness is for. It sets exit 1.
#
# THE MUST_DIE IDS ARE THEMSELVES VERIFIED, at the top, against the intact
# baseline: an id that no longer exists (a renamed or deleted test) would
# otherwise "not survive" every row forever, which is a green that checked
# nothing - the exact defect this file hunts. That check aborts with 3.
#
# The lists were derived by MEASUREMENT, not by reading names: each row was
# run and the tests it actually killed were recorded. See
# docs/worklogs/HARNESS-INTEGRITY-REPORT.md for the per-row measurement.

UNEXPECTED=0

report() {  # $1 = label, $2.. = the test ids this row MUST kill
  local label="$1"; shift
  local must_die=("$@")
  echo "########## $label"
  # A HARD WALL-CLOCK CAP, because an amputated tree can HANG rather than
  # fail: removing a refusal let an in-process arm fall through to serving
  # forever, and a hang is indistinguishable from a slow run until someone
  # looks. The interlock in tests/test_server.py fixes that specific case;
  # this cap is what stops the NEXT one costing half an hour.
  timeout 300 env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest $SUITE \
    -p no:cacheprovider -q -rA >"$WORK/out.txt" 2>&1
  local rc=$?
  restore
  if [ "$rc" -eq 124 ]; then
    # NOT just a note. A timed-out run produces no PASSED lines, so every
    # MUST_DIE id "did not survive" and the row would read as a pass. A
    # row that could not be measured is a row that failed.
    echo "  TIMED OUT after 300s - the amputated tree HANGS rather than failing."
    echo "  THIS ROW MEASURED NOTHING; treat it as a FAILURE, not a pass."
    UNEXPECTED=1
    echo
    return
  fi
  tail -1 "$WORK/out.txt"
  local survivors
  survivors=$(grep -E '^PASSED ' "$WORK/out.txt" | sed 's/^PASSED //' || true)

  # THE FINDING, FIRST. Anything below it is context.
  local t unexpected_here=0
  for t in "${must_die[@]}"; do
    # `grep -Fxq` is a WHOLE-LINE match, so the builtin needs the
    # newlines around it to mean the same thing - a bare substring
    # test would match a survivor that merely CONTAINS this name.
    if [[ $'\n'"$survivors"$'\n' == *$'\n'"$t"$'\n'* ]]; then
      echo "  UNEXPECTED SURVIVOR: $t"
      echo "    This assertion exists to notice THIS amputation and did not."
      unexpected_here=1
      UNEXPECTED=1
    fi
  done
  if [ "$unexpected_here" -eq 0 ]; then
    echo "  every declared assertion died (${#must_die[@]} of ${#must_die[@]})"
  fi

  if [ -z "$survivors" ]; then
    echo "  everything else: NOTHING passed against this tree"
  else
    echo "  everything else that passed (context, NOT a finding - these are"
    echo "  assertions this row's subject does not reach):"
    echo "$survivors" | sed 's/^/    /'
  fi
  echo
}

# --- the MUST_DIE declarations ---------------------------------------------
# One array per row. Each id was OBSERVED to die under its row; none of them
# is a guess from the test's name, because a test name is an unverified
# claim about its body.
MUST_A=(
  "tests/test_config.py::test_the_whole_committed_template_loads"
  "tests/test_boot.py::test_a_missing_credential_exits_naming_the_variable"
)
MUST_B=("${MUST_A[@]}")
MUST_C=(
  "tests/test_config.py::test_every_reason_is_named_not_just_the_first"
  "tests/test_boot.py::test_a_missing_credential_exits_naming_the_variable"
  "tests/test_boot.py::test_an_unrecognised_tool_name_exits_naming_it"
)
MUST_D=(
  "tests/test_config.py::test_http_without_tokens_is_a_startup_failure"
  "tests/test_config.py::test_off_loopback_without_the_assertion_refuses"
  "tests/test_boot.py::test_off_loopback_without_tls_exits_naming_the_reason"
)
MUST_E=(
  "tests/test_config.py::test_a_candidate_search_deployment_is_not_asked_for_a_company_id"
  "tests/test_boot.py::test_a_missing_credential_exits_naming_the_variable"
)
MUST_F=(
  "tests/test_config.py::test_a_recognised_tool_name_starts"
  "tests/test_boot.py::test_the_default_loopback_bind_starts_a_real_process"
)
MUST_G=(
  "tests/test_shutdown.py::test_the_handler_does_not_read_ambient_state"
  "tests/test_shutdown.py::test_a_clean_stop_still_reports_zero"
)
MUST_H=(
  "tests/test_shutdown.py::test_a_crashing_mcp_run_exits_70_read_from_the_process"
  "tests/test_shutdown.py::test_only_stdio_exercises_the_forced_exit"
)
MUST_I=(
  "tests/test_server.py::test_mask_error_details_is_set_explicitly"
  "tests/test_server.py::test_composed_lifespans_start_in_order_and_tear_down_in_reverse"
  "tests/test_server.py::test_create_server_builds_from_the_environment"
)
MUST_J=(
  "tests/test_logging_process.py::test_the_process_writes_the_mandated_audit_fields"
  "tests/test_logging_process.py::test_a_failing_sink_after_a_write_returns_a_warning_not_an_error"
  "tests/test_logging_process.py::test_a_failing_sink_on_a_read_does_not_fail_the_read"
)
MUST_K=("${MUST_J[@]}")
# ONE arm, not two. Redaction is DEFENCE IN DEPTH - a record filter and a
# rendering sink, deliberately independent - so a test that either layer
# protects CANNOT die when only one is amputated, and demanding that it does
# makes the row red against correct code. Only the arm that no other layer
# reaches belongs here: a sink this project did not install is invisible to
# the sink-level redaction by construction.
#
# MEASURED, not reasoned: each of rows L and N kills exactly ONE arm, and not
# the same arm. `test_a_third_party_log_line_is_redacted_at_the_sink` survives
# row L not vacuously but because row N's sink still redacts what it renders,
# so the stream that arm reads is clean either way.
#
# The doubly-protected arm is not dropped; it moves to row LN below, which
# removes BOTH layers and is where it must die.
MUST_L=(
  "tests/test_logging_process.py::test_a_sink_this_project_did_not_install_sees_a_redacted_record"
)
# Row N arrived with the sink-level redaction split (main). Its subject is the
# RENDERED half - the serialised `text` and `exception` fields the record
# filter cannot reach - so the arms that must notice it are the ones that read
# a real process's stream and look for a credential in it.
# Same correction as row L, from the other side. The transport-failure arm
# reads the process stream, which BOTH layers protect, so it survives a
# sink-only amputation.
MUST_N=(
  "tests/test_logging_process.py::test_an_exception_carrying_a_credential_is_redacted_at_the_sink"
)

# Row LN: BOTH redaction layers removed at once.
#
# Without it the corrections above would WEAKEN the harness - a doubly-protected
# arm would be asserted by no row at all, and an arm no row can kill is an arm
# that might be vacuous. This is where it must die.
#
# ONE arm, and the omission is a THIRD layer nobody had named.
# `test_the_process_publishes_no_credential_when_the_transport_fails` was
# declared here and SURVIVED even with both logging layers gone. It is not
# vacuous: its credentials travel in HEADERS, which `redact_headers` scrubs at
# the PRODUCER (M-5/L-1) before a record is ever built. The logging layers are
# not what protects that arm, so requiring it to notice an amputation here would
# declare an expectation the code does not owe. The row that kills layer 1 is
# A9d in check-u4-client-amputation.sh, whose subject IS that module: it removes
# `redact_headers` from the log call and takes down
# test_the_v2_credential_headers_are_redacted_in_the_failure_log. Measured
# 2026-08-29, 1 failed / 412 passed on the whole suite. This pointer named "the
# board" until then, which is a reference that decays the moment a task closes.
MUST_LN=(
  "tests/test_logging_process.py::test_a_third_party_log_line_is_redacted_at_the_sink"
)
MUST_M=(
  "tests/test_logging_process.py::test_python_dash_m_gets_the_same_configured_sink"
  "tests/test_logging_process.py::test_a_third_party_log_line_is_redacted_at_the_sink"
)

echo "########## BASELINE - the intact tree"
PYTHONDONTWRITEBYTECODE=1 timeout 900 uv run --frozen pytest $SUITE -q -rA \
     -p no:cacheprovider >"$WORK/base.txt" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact tree is red; amputation results would be meaningless."
  tail -20 "$WORK/base.txt"
  exit 3
fi
tail -1 "$WORK/base.txt"

# EVERY DECLARED ID MUST EXIST AND PASS ON THE INTACT TREE. Without this, a
# renamed or deleted test silently "dies" under every row forever and its
# row is checking nothing - a green that tested nothing, which is the whole
# subject of this file. This is the positive control on the instrument.
grep -E '^PASSED ' "$WORK/base.txt" | sed 's/^PASSED //' >"$WORK/base_passed.txt"
MISSING=0
for t in "${MUST_A[@]}" "${MUST_B[@]}" "${MUST_C[@]}" "${MUST_D[@]}" \
         "${MUST_E[@]}" "${MUST_F[@]}" "${MUST_G[@]}" "${MUST_H[@]}" \
         "${MUST_I[@]}" "${MUST_J[@]}" "${MUST_K[@]}" "${MUST_L[@]}" \
         "${MUST_M[@]}" "${MUST_N[@]}"; do
  grep -Fxq -- "$t" "$WORK/base_passed.txt" || {
    echo "ABORT: declared MUST_DIE id does not pass on the INTACT tree:"
    echo "         $t"
    echo "       It was renamed, deleted or is failing. Its row is checking"
    echo "       nothing until this is repointed."
    MISSING=1; }
done
[ "$MISSING" -eq 0 ] || exit 3
echo "  all declared MUST_DIE ids pass on the intact tree."
echo

# --- A. config.py does not exist at all -----------------------------------
rm -f "$CONFIG"
report "A. config.py does not exist at all" "${MUST_A[@]}"

# --- B. config.py exists and is ZERO BYTES --------------------------------
# The clean-empty trap: the import of the MODULE succeeds, so anything that
# does not actually reach a name inside it keeps passing.
: > "$CONFIG"
report "B. config.py exists but is ZERO BYTES" "${MUST_B[@]}"

# --- C. validate_settings() runs and refuses NOTHING ----------------------
# Every refusal amputated at once, with the function, its name, its
# signature and its callers all still present. This is the shape a real
# regression takes: the module imports, boot succeeds, nothing is checked.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(
    r"    reasons: list\[str\] = \[\]\n(?:.*?\n)*?        raise ConfigurationError\(reasons\)\n",
    "    return\n",
    s,
    count=1,
)
p.write_text(s)
PY
report "C. validate_settings() refuses nothing" "${MUST_C[@]}"

# --- D. the transport refusals are gone entirely --------------------------
# The TLS refusal and the token requirement both live in _check_transport.
# Removing the whole function is the amputation; M1 and M6 only disabled one
# branch each.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    _check_transport(settings, reasons)\n", "")
p.write_text(s)
PY
report "D. _check_transport is never called" "${MUST_D[@]}"

# --- E. the rule TABLE is empty, not the code -----------------------------
# Amputating the DATA. Every function is present and runs; the matrix it
# consults holds nothing, so no tool ever requires anything.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"TOOL_REQUIREMENTS: Final\[dict\[str, tuple\[str, \.\.\.\]\]\] = \{\n.*?\n\}",
           "TOOL_REQUIREMENTS: Final[dict[str, tuple[str, ...]]] = {}",
           s, flags=re.S)
p.write_text(s)
PY
report "E. TOOL_REQUIREMENTS is an EMPTY table" "${MUST_E[@]}"

# --- F. the tool allow-list is empty --------------------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("KNOWN_TOOLS: Final[frozenset[str]] = READ_TOOLS | WRITE_TOOLS",
              "KNOWN_TOOLS: Final[frozenset[str]] = frozenset()")
p.write_text(s)
PY
report "F. KNOWN_TOOLS is EMPTY" "${MUST_F[@]}"

# --- G. the shutdown handler does not exist -------------------------------
# Not "installs nothing" (that is M11) but "the function is gone", so a
# caller that referenced it would fail loudly rather than silently.
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"def _install_shutdown_handler\(\) -> None:\n(?:.*?\n)*?    signal\.signal\(signal\.SIGTERM, _term\)\n",
           "def _install_shutdown_handler() -> None:\n    return\n", s, count=1)
s = re.sub(r"def _term\(signum: int, frame: FrameType \| None\) -> None:\n(?:.*?\n)*?    raise KeyboardInterrupt\n",
           "", s, count=1)
p.write_text(s)
PY
report "G. _term and the handler installation are GONE" "${MUST_G[@]}"

# --- H. the whole finally block is gone -----------------------------------
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s, n = re.subn(r"    finally:\n        sys\.stdout\.flush\(\)\n        sys\.stderr\.flush\(\)\n.*?\n        os\._exit\(status\)\n",
               "", s, count=1, flags=re.S)
assert n == 1, "amputation H found nothing to remove; the anchor moved"
p.write_text(s)
PY
report "H. the finally block (flush + os._exit) is GONE" "${MUST_H[@]}"

# --- I. server.py builds a bare FastMCP -----------------------------------
# No lifespan, no mask_error_details, no settings. Everything server.py
# exists to configure, removed.
python3 - "$SERVER" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"    composed = make_base_lifespan\(settings\)\n(?:.*?\n)*?    \)\n",
           "    return FastMCP(name=SERVER_NAME)\n", s, count=1)
p.write_text(s)
PY
report "I. build_server returns a BARE FastMCP" "${MUST_I[@]}"


# --- J. the log sink is never configured at all ---------------------------
# H-1's shipped tree, amputated rather than mutated: `configure_logging` is
# still defined, still importable and still documented - it is simply never
# called, which is exactly the shape the defect had. Everything that claims
# "the audit event carries its mandated fields" must die here.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "\nconfigure_logging()\n"
assert s.count(anchor) == 1, "J anchor is not unique"
p.write_text(s.replace(anchor, "\n"))
PY
report "J. configure_logging() is never called" "${MUST_J[@]}"

# --- K. it is called and configures NOTHING -------------------------------
# The clean-empty trap on a function rather than a module: the call site is
# present, the name resolves, the body does nothing. Loguru's autoinit
# handler survives, so the stream is NOT silent - it carries the field-less
# line the review measured. An assertion that only proves the stream is
# non-empty passes here, and that is the survivor worth naming.
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "    _loguru.remove()"
assert s.count(anchor) == 1, "K anchor is not unique"
start = s.index(anchor)
end = s.index("\n\n\nconfigure_logging()", start)
p.write_text(s[:start] + "    return" + s[end:])
PY
report "K. configure_logging() runs and configures NOTHING" "${MUST_K[@]}"

# --- L. the record FILTER redacts nothing ---------------------------------
# The RECORD half. `_redact_message` mutates `record["message"]`, which is
# what every handler in the process sees - including one this project did not
# install, and the suite itself is such a handler.
#
# THIS ROW ONCE SURVIVED 78/78 AND THE SURVIVAL WAS AN INSTRUMENT FAULT. Once
# the sink began redacting what it renders, every arm in this suite - all of
# which read the process's own stream - stopped being able to see the filter
# at all, and the filter was briefly deleted on that evidence. The full suite
# then went red on a foreign sink. The arm that fixes the instrument is
# tests/test_logging_process.py::test_a_sink_this_project_did_not_install_sees_a_redacted_record
# and it must die here.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = '    message = record.get("message")'
assert s.count(anchor) == 1, "L anchor is not unique"
p.write_text(s.replace(anchor, "    return True\n" + anchor))
PY
report "L. the record filter returns without redacting" "${MUST_L[@]}"

# --- N. the SINK-level redaction is bypassed ------------------------------
# The RENDERED half. `serialize` emits `record["exception"]` and a `text`
# carrying the formatted traceback, neither of which is `record["message"]`,
# so the filter above cannot reach them. Measured before this sink existed: a
# stdlib `logger.exception` published the feed URL twice, in the clear.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        _redacting_sink(sys.stderr),"
assert s.count(anchor) == 1, "N anchor is not unique"
p.write_text(s.replace(anchor, "        sys.stderr,"))
PY
report "N. the sink writes the serialised record without redacting it" "${MUST_N[@]}"

# --- LN. BOTH redaction layers removed --------------------------------------
# The rows above each remove ONE layer, and the arms that read the process
# stream survive that by design - the other layer still covers them. Removing
# both is the only amputation those arms can see, and it is what proves they
# are not vacuous.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
filter_anchor = '    message = record.get("message")'
sink_anchor = "        _redacting_sink(sys.stderr),"
assert s.count(filter_anchor) == 1, "LN filter anchor is not unique"
assert s.count(sink_anchor) == 1, "LN sink anchor is not unique"
s = s.replace(filter_anchor, "    return True\n" + filter_anchor)
s = s.replace(sink_anchor, "        sys.stderr,")
p.write_text(s)
PY
report "LN. BOTH the record filter and the sink redaction are gone" "${MUST_LN[@]}"

# --- M. stdlib logging is never bridged into loguru -----------------------
# Two logging systems again, both live, writing two shapes onto one fd.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "    logging.basicConfig("
assert s.count(anchor) == 1, "J anchor is not unique"
start = s.index(anchor)
end = s.index("    )\n", start) + len("    )\n")
p.write_text(s[:start] + "    return\n" + s[end:])
PY
report "M. stdlib logging is never bridged into loguru" "${MUST_M[@]}"
echo "########## END"
if [ "$UNEXPECTED" -ne 0 ]; then
  echo "FAILED: at least one assertion that exists to notice an amputation"
  echo "        survived it, or a row could not be measured. Search this"
  echo "        output for 'UNEXPECTED SURVIVOR' and 'TIMED OUT'."
  exit 1
fi
echo "Every declared assertion died under its own amputation."
echo "The 'everything else that passed' lists are context, not findings."
exit 0
