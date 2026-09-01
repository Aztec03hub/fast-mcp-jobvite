#!/usr/bin/env bash
# U1 MUTATION harness. "Break one rule - does the named test notice?"
#
# Same "all fired, never a literal count" contract as the U0 and U15
# harnesses: this exits non-zero if any control failed to fire, and prints
# an "N/M controls fired." line whose numerator must equal its denominator.
#
# THREE PROPERTIES THIS HARNESS HAS THAT A NAIVE ONE DOES NOT:
#
#   1. PYTHONDONTWRITEBYTECODE=1 on every run. `.pyc` invalidation keys on
#      (mtime, size), so a SAME-SIZE mutation made inside the same second
#      reuses stale bytecode and the mutant never runs. This has bitten this
#      project.
#   2. Every mutation is GREPPED to confirm it landed before the run, and
#      the file is grepped again after restoring. A mutation that failed to
#      apply produces a green that is indistinguishable from a surviving
#      mutant.
#   3. Restore is from a byte copy taken at the top, NOT `git checkout --`,
#      which would revert uncommitted work along with the mutation.
#
# Mutation is applied IN PLACE and restored by the EXIT trap, so an
# interrupted run does not leave a mutant in the tree.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CONFIG="src/fast_mcp_jobvite/config.py"
MAIN="src/fast_mcp_jobvite/__main__.py"
SERVER="src/fast_mcp_jobvite/server.py"
SUITE="tests/test_config.py tests/test_boot.py tests/test_shutdown.py tests/test_server.py tests/test_logging_process.py"

BACKUP="$(mktemp -d)"
trap 'harness_result_emit; cp "$BACKUP/config.py" "$CONFIG"; cp "$BACKUP/__main__.py" "$MAIN"; \
      cp "$BACKUP/server.py" "$SERVER"; rm -rf "$BACKUP"' EXIT
cp "$CONFIG" "$BACKUP/config.py"
cp "$MAIN" "$BACKUP/__main__.py"
cp "$SERVER" "$BACKUP/server.py"

FIRED=0
TOTAL=0

restore() {
  cp "$BACKUP/config.py" "$CONFIG"
  cp "$BACKUP/__main__.py" "$MAIN"
  cp "$BACKUP/server.py" "$SERVER"
}

# baseline: a red intact tree makes every row below meaningless.
echo "########## BASELINE - the intact tree"
PYTHONDONTWRITEBYTECODE=1 timeout 900 uv run --frozen pytest $SUITE -q \
     -p no:cacheprovider >/tmp/u1-base.txt 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact tree is red; mutation results would be meaningless."
  tail -20 /tmp/u1-base.txt
  exit 3
fi
tail -1 /tmp/u1-base.txt
echo

# control <label> <file> <landed-grep> <named-test> -- the sed/python patch is
# applied by the caller before invoking this.
control() {
  local label="$1" file="$2" landed="$3" named="$4"
  TOTAL=$((TOTAL + 1))

  # THE SELECTOR MUST RESOLVE BEFORE THE MUTATION IS TRUSTED (R4-M3's shape,
  # ported here from check-u5-jobs-controls.sh). `pytest <node-id>` exits
  # NON-ZERO when it cannot collect the id at all, and this function reads any
  # non-zero as "the named test went red" - so a RENAMED test makes its row
  # report FIRED forever while running nothing.
  #
  # MEASURED on this harness before the guard existed: one selector repointed at
  # `test_this_name_does_not_exist_anywhere` produced
  #     [M8 first reason only] FIRED   (... went red)
  #     23/23 controls fired.        exit 0
  # A fully green harness, one row of which could not aim.
  #
  # The row is NOT counted as fired, so FIRED < TOTAL and the run exits 1: a
  # harness that cannot aim must fail rather than report.
  timeout 120 uv run --frozen pytest "$named" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1
  local probe_rc=$?
  if [ "$probe_rc" -ne 0 ]; then
    if [ "$probe_rc" -eq 124 ]; then
      echo "  SELECTOR PROBE TIMED OUT after 120s - collection NEVER FINISHED."
      echo "  Read this, not the lines below: a hang, not a rename."
    fi
    echo "  [$label] SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  -> this row has been reporting FIRED without running. Fix the harness."
    return
  fi

  if ! grep -qF -- "$landed" "$file"; then
    echo "  [$label] MUTATION DID NOT LAND (expected to find: $landed)"
    echo "  -> not counted as fired; this is a harness failure, not a result"
    restore
    return
  fi
  local out rc
  out=$(PYTHONDONTWRITEBYTECODE=1 timeout 300 uv run --frozen pytest $named -q \
        -p no:cacheprovider 2>&1)
  rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  [$label] TIMED OUT after 300s - this row NEVER FINISHED, so the"
    echo "  verdict below is not a measurement of it."
  fi
  restore
  if grep -qF -- "$landed" "$file"; then
    echo "  [$label] RESTORE FAILED - the mutation is still in the tree"
    exit 3
  fi
  if [ "$rc" -ne 0 ]; then
    FIRED=$((FIRED + 1))
    echo "  [$label] FIRED   ($named went red)"
  else
    echo "  [$label] SURVIVED ($named stayed green - the assertion is weak)"
    printf '%s\n' "$out" | tail -3 | sed 's/^/      /'
  fi
}

echo "########## MUTATIONS"

# --- M1: the off-loopback TLS refusal never fires -------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace(
    "    if not is_loopback(settings.mcp_host) and not settings.tls_terminated_by_proxy:",
    "    if False and not settings.tls_terminated_by_proxy:  # MUTANT-M1")
p.write_text(s)
PY
control "M1 TLS refusal disabled" "$CONFIG" "MUTANT-M1" \
  "tests/test_boot.py::test_off_loopback_without_tls_exits_naming_the_reason"

# --- M2: an unrecognisable host counts as loopback ------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    except ValueError:\n        return False",
              "    except ValueError:\n        return True  # MUTANT-M2")
p.write_text(s)
PY
control "M2 unknown host = loopback" "$CONFIG" "MUTANT-M2" \
  "tests/test_config.py::test_non_loopback_and_unrecognisable_hosts_are_not_loopback"

# --- M3: the write gate ignores JOBVITE_ENABLE_WRITES ---------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        if not self.enable_writes:\n            selected -= WRITE_TOOLS",
              "        if False:  # MUTANT-M3\n            selected -= WRITE_TOOLS")
p.write_text(s)
PY
control "M3 write gate ignores the flag" "$CONFIG" "MUTANT-M3" \
  "tests/test_config.py::test_naming_the_write_without_the_flag_does_not_register_it"

# --- M4: unset JOBVITE_TOOLS enables the write too ------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        selected = READ_TOOLS if self.tools is None else recognised",
              "        selected = KNOWN_TOOLS if self.tools is None else recognised  # MUTANT-M4")
p.write_text(s)
PY
# The named test is the ENABLE_WRITES arm, not the "all reads" arm, and the
# difference was measured rather than guessed: with the flag at its default
# `false` the write is stripped again one line later, so this mutant is
# SEMANTICALLY EQUIVALENT under that configuration and the "all reads" arm
# stayed green against it. That is a mutant/test pairing error, not a weak
# assertion - the arm that actually distinguishes the two is the one where
# JOBVITE_ENABLE_WRITES is true and JOBVITE_TOOLS is unset.
control "M4 unset TOOLS includes the write" "$CONFIG" "MUTANT-M4" \
  "tests/test_config.py::test_enable_writes_true_with_tools_unset_does_not_register_the_write"

# --- M5: an unrecognised tool name is a silent skip -----------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys, re
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    _, unknown = settings.split_tool_names()",
              "    _, unknown = [], []  # MUTANT-M5")
p.write_text(s)
PY
control "M5 unrecognised name skipped silently" "$CONFIG" "MUTANT-M5" \
  "tests/test_boot.py::test_an_unrecognised_tool_name_exits_naming_it"

# --- M6: http starts with no tokens (an OPEN SERVER) ----------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    if settings.http_tokens is None:\n        reasons.append(",
              "    if False:  # MUTANT-M6\n        reasons.append(")
p.write_text(s)
PY
control "M6 http serves with no tokens" "$CONFIG" "MUTANT-M6" \
  "tests/test_boot.py::test_http_without_tokens_exits_rather_than_serving_openly"

# --- M7: required variables validated as the UNION ------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    for tool in sorted(settings.enabled_tools):",
              "    for tool in sorted(KNOWN_TOOLS):  # MUTANT-M7")
p.write_text(s)
PY
control "M7 union instead of enabled set" "$CONFIG" "MUTANT-M7" \
  "tests/test_config.py::test_a_candidate_search_deployment_is_not_asked_for_a_company_id"

# --- M8: only the first refusal is reported -------------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    if reasons:\n        raise ConfigurationError(reasons)",
              "    if reasons:\n        raise ConfigurationError(reasons[:1])  # MUTANT-M8")
p.write_text(s)
PY
control "M8 first reason only" "$CONFIG" "MUTANT-M8" \
  "tests/test_config.py::test_every_reason_is_named_not_just_the_first"

# --- M9: an empty value counts as a present credential --------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        if not isinstance(data, dict):\n            return data",
              "        if True:  # MUTANT-M9\n            return data")
p.write_text(s)
PY
control "M9 empty value is a credential" "$CONFIG" "MUTANT-M9" \
  "tests/test_config.py::test_an_empty_value_is_treated_as_unset"

# --- M10: mask_error_details left to the framework default ----------------
python3 - "$SERVER" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        mask_error_details=True,",
              "        mask_error_details=False,  # MUTANT-M10")
p.write_text(s)
PY
control "M10 mask_error_details=False" "$SERVER" "MUTANT-M10" \
  "tests/test_server.py::test_mask_error_details_is_set_explicitly"

# --- M11: the SIGTERM handler is never installed --------------------------
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    signal.signal(signal.SIGTERM, _term)",
              "    pass  # MUTANT-M11")
p.write_text(s)
PY
control "M11 no SIGTERM handler" "$MAIN" "MUTANT-M11" \
  "tests/test_shutdown.py::test_sigterm_runs_lifespan_teardown"

# --- M12: the forced exit removed from the finally ------------------------
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
assert s.count("        os._exit(status)") == 1, "M12 anchor is not unique"
s = s.replace("        os._exit(status)", "        pass  # MUTANT-M12")
p.write_text(s)
PY
control "M12 no forced exit" "$MAIN" "MUTANT-M12" \
  "tests/test_shutdown.py::test_only_stdio_exercises_the_forced_exit"

# --- M14: the exit status is a constant 0 again (ADR-0018 defect) ---------
# The call still runs unconditionally, so the stdio hang stays closed and
# M12 is untouched. Only the constant moves back, which IS the defect.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
assert s.count("        os._exit(status)") == 1, "M14 anchor is not unique"
s = s.replace("        os._exit(status)", "        os._exit(0)  # MUTANT-M14")
p.write_text(s)
PY
# NAMED AT THE BEHAVIOURAL ARM, not the structural one. The structural test
# greps this file's source for "os._exit(status)" and would go red here too -
# but it would go red for the wrong reason, and a defect ABOUT exit codes
# discharged by a substring search is what ADR-0018's own unverified item was.
control "M14 a crash reports exit 0" "$MAIN" "MUTANT-M14" \
  "tests/test_shutdown.py::test_a_crashing_mcp_run_exits_70_read_from_the_process"

# --- M13: the lifespan composition is dropped -----------------------------
python3 - "$SERVER" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        composed = composed | extra_lifespan",
              "        composed = composed  # MUTANT-M13")
p.write_text(s)
PY
control "M13 extra lifespan dropped" "$SERVER" "MUTANT-M13" \
  "tests/test_server.py::test_composed_lifespans_start_in_order_and_tear_down_in_reverse"

# --- M15: loguru is never configured (H-1, the shipped defect) ------------
# The exact tree the review measured: audit.py writes through loguru, nothing
# configures it, and every mandated field goes to the autoinit handler whose
# format carries no {extra}.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "\nconfigure_logging()\n"
assert s.count(anchor) == 1, "M15 anchor is not unique"
p.write_text(s.replace(anchor, "\npass  # MUTANT-M15\n"))
PY
control "M15 loguru never configured" "$MAIN" "MUTANT-M15" \
  "tests/test_logging_process.py::test_the_process_writes_the_mandated_audit_fields"

# --- M16: the sink stops serialising -------------------------------------
# serialize=False falls back to loguru's default format, which carries no
# {extra}. The record is still emitted, so a "the audit stream is non-empty"
# test survives; only an assertion on the FIELDS notices.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        serialize=True,"
assert s.count(anchor) == 1, "M16 anchor is not unique"
p.write_text(s.replace(anchor, "        serialize=False,  # MUTANT-M16"))
PY
control "M16 the sink stops serialising" "$MAIN" "MUTANT-M16" \
  "tests/test_logging_process.py::test_the_process_writes_the_mandated_audit_fields"

# --- M17: catch=True, loguru's default (H-2) ------------------------------
# A sink failure is swallowed, .info() returns normally and emit()'s except
# never runs, so the BEFORE_SIDE_EFFECT branch cannot fire in production.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        catch=False,"
assert s.count(anchor) == 1, "M17 anchor is not unique"
p.write_text(s.replace(anchor, "        catch=True,  # MUTANT-M17"))
PY
control "M17 catch=True swallows sink failures" "$MAIN" "MUTANT-M17" \
  "tests/test_logging_process.py::test_a_failing_sink_fails_the_call_before_the_side_effect"

# --- M18: the sink stops redacting ---------------------------------------
# The anchor moved when `filter=_redact_message` was deleted: the filter
# reached `record["message"]` only, and the U1 amputation harness measured the
# whole boot suite passing 78/78 with it neutered, because the sink now
# redacts the rendered record. This mutant points at the sink instead.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        _redacting_sink(sys.stderr),"
assert s.count(anchor) == 1, "M18 anchor is not unique"
p.write_text(s.replace(anchor, "        sys.stderr,  # MUTANT-M18"))
PY
control "M18 the serialising sink stops redacting" "$MAIN" "MUTANT-M18" \
  "tests/test_logging_process.py::test_an_exception_carrying_a_credential_is_redacted_at_the_sink"

# --- M19: stdlib records no longer reach the one sink ---------------------
# The two-logging-systems defect reinstated: loguru is configured, stdlib keeps
# a handler of its own, and the stream carries two record shapes again.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        handlers=[_InterceptHandler()],"
assert s.count(anchor) == 1, "M19 anchor is not unique"
p.write_text(s.replace(anchor, "        stream=sys.stderr,  # MUTANT-M19"))
PY
control "M19 stdlib records bypass the one sink" "$MAIN" "MUTANT-M19" \
  "tests/test_logging_process.py::test_python_dash_m_gets_the_same_configured_sink"


# --- M20: the record filter stops redacting -------------------------------
# M18 above is the RENDERED half; this is the RECORD half, and they are not
# interchangeable. The filter is what a handler this project did not install
# sees, and the arm named below is the only one that reads such a handler -
# every other arm in that module reads the process's own stream, which M18's
# sink already cleans. That asymmetry is why deleting the filter once left
# this suite entirely green.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = '    message = record.get("message")'
assert s.count(anchor) == 1, "M20 anchor is not unique"
p.write_text(s.replace(anchor, "    return True  # MUTANT-M20\n" + anchor))
PY
control "M20 the record filter stops redacting" "$MAIN" "MUTANT-M20" \
  "tests/test_logging_process.py::test_a_sink_this_project_did_not_install_sees_a_redacted_record"

# --- M21: the refusal exit status is a generic 1 (R2-M-3) -----------------
# 78 is EX_CONFIG and every assertion in the suite compared the constant with
# itself, so this mutation survived the WHOLE suite at 423 passed. The named
# test compares it with the NUMBER a supervisor reads.
python3 - "$MAIN" <<'PY21'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "EXIT_CONFIGURATION_REFUSED = 78"
assert s.count(anchor) == 1, "M21 anchor is not unique"
p.write_text(s.replace(anchor, "EXIT_CONFIGURATION_REFUSED = 1  # MUTANT-M21"))
PY21
control "M21 the refusal status is a generic 1" "$MAIN" "MUTANT-M21" \
  "tests/test_boot.py::test_the_refusal_status_is_the_sysexits_ex_config_number"

# --- M22: empty-is-unset stops stripping whitespace (R2-M-4 residual) -----
# R2's M-4 fix had two halves and only the test landed; this is the half that
# never did, so the whitespace rule was held by the suite and not by a gate.
# The anchor moved into `_is_blank` when nit-2 gave the rule a name.
python3 - "$CONFIG" <<'PY22'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "    return isinstance(value, str) and not value.strip()"
assert s.count(anchor) == 1, "M22 anchor is not unique"
p.write_text(s.replace(anchor, "    return isinstance(value, str) and not value  # MUTANT-M22"))
PY22
control "M22 whitespace-only is a present credential" "$CONFIG" "MUTANT-M22" \
  "tests/test_config.py::test_a_whitespace_only_value_is_also_treated_as_unset"

# --- M23: the blank check ignores SecretStr again (R2-nit-2) --------------
python3 - "$CONFIG" <<'PY23'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        value = value.get_secret_value()"
assert s.count(anchor) == 1, "M23 anchor is not unique"
p.write_text(s.replace(anchor, "        value = None  # MUTANT-M23"))
PY23
control "M23 a blank SecretStr is a credential" "$CONFIG" "MUTANT-M23" \
  "tests/test_config.py::test_a_directly_constructed_blank_secret_is_also_unset"


echo
echo "$FIRED/$TOTAL controls fired."

# THE ROW FLOOR. `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness
# whose rows were deleted - or whose rows stopped being counted - reports
# fully green and exits 0. DERIVED: this harness printed "23/23 controls
# fired." at 73269fe. Lowering this number is a visible diff that has to
# be defended.
ROW_FLOOR=23
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "$TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "NOT every control fired. A surviving mutant is a weak assertion."
  exit 1
fi
exit 0
