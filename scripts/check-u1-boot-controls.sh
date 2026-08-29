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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CONFIG="src/fast_mcp_jobvite/config.py"
MAIN="src/fast_mcp_jobvite/__main__.py"
SERVER="src/fast_mcp_jobvite/server.py"
SUITE="tests/test_config.py tests/test_boot.py tests/test_shutdown.py tests/test_server.py"

BACKUP="$(mktemp -d)"
trap 'cp "$BACKUP/config.py" "$CONFIG"; cp "$BACKUP/__main__.py" "$MAIN"; \
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
if ! PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest $SUITE -q \
     -p no:cacheprovider >/tmp/u1-base.txt 2>&1; then
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
  if ! grep -qF -- "$landed" "$file"; then
    echo "  [$label] MUTATION DID NOT LAND (expected to find: $landed)"
    echo "  -> not counted as fired; this is a harness failure, not a result"
    restore
    return
  fi
  local out rc
  out=$(PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest $named -q \
        -p no:cacheprovider 2>&1)
  rc=$?
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

# --- M12: os._exit(0) removed from the finally ----------------------------
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("        os._exit(0)", "        pass  # MUTANT-M12")
p.write_text(s)
PY
control "M12 no forced exit" "$MAIN" "MUTANT-M12" \
  "tests/test_shutdown.py::test_only_stdio_exercises_the_forced_exit"

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

echo
echo "$FIRED/$TOTAL controls fired."
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "NOT every control fired. A surviving mutant is a weak assertion."
  exit 1
fi
exit 0
