#!/usr/bin/env bash
# U11 mutation AND amputation harness. Proves tests/test_advisory_gate.py can FAIL.
#
# WHY THIS EXISTS. Every assertion in that suite is a claim about a gate whose
# job is to refuse things. A suite of refusal assertions is green against a gate
# that refuses everything, and a suite of acceptance assertions is green against
# a gate that accepts everything. Neither is worth anything until a harness has
# broken the gate one rule at a time and watched the NAMED test go red.
#
# It is deliberately the mirror of scripts/check-u15-gate-controls.sh.
#
# TWO KINDS OF CONTROL, and the second is the one that has repeatedly found what
# the first cannot:
#
#   MUTATION   change a VALUE or an operator - 30 becomes 31, `<` becomes `<=`.
#              Catches an off-by-one and a wrong comparison.
#   AMPUTATION DELETE the behaviour outright - remove the emission, remove a
#              whole check. Catches a VACUOUS assertion: one that passes because
#              it never actually looked at what it claims to assert on. A test
#              asserting only on an exit code survives every mutation above and
#              dies here, which is exactly the defect this unit was warned about
#              (a script that exits 0 and emits nothing silently disables every
#              ignore).
#
# Each control breaks exactly one thing in a COPY of the tree, runs the suite,
# and requires the specific named test to fail. A mutation that does not change
# the file is rejected - a no-op control is a green that measured nothing - and
# the run aborts if the unmutated copy is not already green.
#
# PYTHONDONTWRITEBYTECODE=1 throughout. .pyc invalidation keys on (mtime, size),
# so a same-size mutation applied inside one second reuses stale bytecode and the
# mutant never runs. That has bitten this project.
#
# Exit 0 only if every control fired. Prints "N/M controls fired." for CI to
# parse on the property N == M and M > 0, never on a literal count.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"
export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# THE INTERPRETER IS CHOSEN, NOT INHERITED - see the note in
# scripts/check-u15-gate-controls.sh. Bare `python3` is the runner's
# hosted-toolchain interpreter, which has no pytest, so the baseline goes red
# and the harness aborts. Same selection as scripts/check-u0-test-controls.sh.
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY=("$REPO_ROOT/.venv/bin/python")
else
  PY=(uv run --frozen --project "$REPO_ROOT" python)
fi
GATE_REL="scripts/check_advisories.py"
SUITE_REL="tests/test_advisory_gate.py"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

TREE="$WORK/tree"
mkdir -p "$TREE/scripts" "$TREE/tests"
cp "$REPO_ROOT/$GATE_REL" "$TREE/$GATE_REL"
cp "$REPO_ROOT/$SUITE_REL" "$TREE/$SUITE_REL"
cp "$REPO_ROOT/tests/__init__.py" "$TREE/tests/" 2>/dev/null || true
cp "$REPO_ROOT/pyproject.toml" "$TREE/"

PRISTINE="$WORK/pristine.py"
cp "$REPO_ROOT/$GATE_REL" "$PRISTINE"

# BOUNDED HERE, NOT AT THE CALL SITES. Every caller goes through this one
# function, so the timeout and the hang report live in one place rather than
# being retyped three times - a retyped bound is a bound that drifts.
# `TIMED OUT` is the phrase ci-harness-gate.sh greps for: a row that never
# finished produces no FAILED lines, and reads as "did not fire" to every
# caller below unless it says so out loud.
run_suite() {
  local rc
  ( cd "$TREE" && timeout -k 30 900 "${PY[@]}" -m pytest "$SUITE_REL" \
      -p no:cacheprovider -q -o addopts="" >"$WORK/out.txt" 2>&1 )
  rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - the suite NEVER FINISHED, so this run"
    echo "  measured nothing. Not a fire and not a hold."
  fi
  return "$rc"
}

echo "BASELINE: the unmutated copy must be green before anything is measured"
run_suite
BASE_RC=$?
tail -1 "$WORK/out.txt"
if [ "$BASE_RC" -ne 0 ]; then
  echo "ABORT: the unmutated copy is already red. Every control below would be"
  echo "a false positive - a test that was failing anyway proves nothing."
  cat "$WORK/out.txt"
  exit 3
fi
echo

FIRED=0
HELD=0

# control KIND "label" "expected-test-name" python-replacement-expression
control() {
  local kind="$1" label="$2" expect="$3" old="$4" new="$5"
  HELD=$((HELD + 1))
  cp "$PRISTINE" "$TREE/$GATE_REL"

  # Apply, and REQUIRE the file to change. A control whose edit silently missed
  # is a green that measured nothing.
  python3 - "$TREE/$GATE_REL" "$old" "$new" <<'PY'
import sys, pathlib
path, old, new = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
text = path.read_text()
if old not in text:
    sys.exit(9)
path.write_text(text.replace(old, new, 1))
PY
  local applied=$?
  if [ "$applied" -ne 0 ]; then
    echo "  [$kind] $label -- ABORT: the mutation target was not found."
    echo "         The gate changed and this control no longer edits anything."
    exit 4
  fi
  # Grep that it LANDED, independently of the tool that applied it.
  if grep -qF -- "$new" "$TREE/$GATE_REL"; then :; else
    echo "  [$kind] $label -- ABORT: mutation did not land in the file."
    exit 4
  fi

  run_suite
  local rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  [$kind] $label -- DID NOT FIRE. Suite green with the gate broken."
    echo "         Expected '$expect' to fail. This assertion is VACUOUS."
  elif grep -qF "$expect" "$WORK/out.txt"; then
    local n
    n=$(grep -c "^FAILED" "$WORK/out.txt")
    echo "  [$kind] $label -- fired ($n failed, incl. $expect)"
    FIRED=$((FIRED + 1))
  else
    echo "  [$kind] $label -- fired, but NOT via '$expect'."
    echo "         Something else broke; this control is not measuring its subject."
    grep "^FAILED" "$WORK/out.txt" | head -3
  fi

  # Restore from the PRISTINE COPY, never `git checkout --`, which would revert
  # uncommitted work in the real tree alongside the mutation.
  cp "$PRISTINE" "$TREE/$GATE_REL"
  if diff -q "$PRISTINE" "$TREE/$GATE_REL" >/dev/null; then :; else
    echo "ABORT: restore failed; later controls would run against a mutant."
    exit 5
  fi
}

echo "MUTATION CONTROLS - change a value or an operator"

control MUT "the 30-day budget becomes 31" \
  "test_an_expiry_more_than_30_days_out_is_rejected" \
  "MAX_IGNORE_DAYS = 30" "MAX_IGNORE_DAYS = 31"

control MUT "the 30-day budget becomes 29" \
  "test_an_expiry_exactly_30_days_out_is_honoured" \
  "MAX_IGNORE_DAYS = 30" "MAX_IGNORE_DAYS = 29"

control MUT "expiry compared with <= so today counts as expired" \
  "test_an_entry_expiring_today_is_not_yet_expired" \
  "if expires < now:" "if expires <= now:"

control MUT "expiry comparison inverted" \
  "test_an_entry_past_its_recorded_expiry_is_rejected" \
  "if expires < now:" "if expires > now:"

control MUT "budget measured from now instead of the recorded date" \
  "test_the_30_day_budget_is_measured_from_the_recorded_date_not_from_now" \
  "budget = (expires - recorded).days" "budget = (expires - now).days"

control MUT "the emitted flag is misspelled" \
  "test_an_unexpired_entry_is_honoured_AND_ITS_FLAG_IS_EMITTED" \
  'flags.extend(["--ignore-vuln", advisory_id])' \
  'flags.extend(["--ignore-vulns", advisory_id])'

control MUT "a blank advisory id is accepted as an id" \
  "test_a_blank_advisory_id_is_a_blanket_ignore" \
  "if not isinstance(advisory_id, str) or not advisory_id.strip():" \
  "if not isinstance(advisory_id, str):"

echo
echo "AMPUTATION CONTROLS - delete the behaviour outright"

# THE ONE THAT MATTERS MOST. The gate still exits 0 on a legal table; it simply
# emits nothing. Every exit-code assertion in the suite stays green. Only an
# assertion that actually reads the emitted flags can catch this.
control AMP "the flag emission is deleted entirely (gate still exits 0)" \
  "test_an_unexpired_entry_is_honoured_AND_ITS_FLAG_IS_EMITTED" \
  'flags.extend(["--ignore-vuln", advisory_id])' \
  "pass  # AMPUTATED: emits nothing, still exits 0"

control AMP "the expiry check is deleted" \
  "test_an_entry_past_its_recorded_expiry_is_rejected" \
  "        if expires < now:" \
  "        if False:  # AMPUTATED"

control AMP "the 30-day budget check is deleted" \
  "test_an_expiry_more_than_30_days_out_is_rejected" \
  "        if budget > MAX_IGNORE_DAYS:" \
  "        if False:  # AMPUTATED"

control AMP "the blanket-ignore check is deleted" \
  "test_a_blanket_ignore_with_no_advisory_id_is_rejected" \
  "        if not isinstance(advisory_id, str) or not advisory_id.strip():" \
  "        if False:  # AMPUTATED"

control AMP "the missing-expiry check is deleted" \
  "test_an_entry_with_no_expiry_is_rejected" \
  '        if "expires" not in entry:' \
  "        if False:  # AMPUTATED"

control AMP "the written-reason check is deleted" \
  "test_an_entry_with_no_reason_is_rejected" \
  "        if not isinstance(reason, str) or not reason.strip():" \
  "        if False:  # AMPUTATED"

control AMP "the CLI stops printing the flags (exit codes unchanged)" \
  "test_cli_emits_the_flag_on_stdout_for_a_legal_entry" \
  '        print(" ".join(flags))' \
  "        pass  # AMPUTATED: exit code unchanged, stdout empty"

control AMP "the whole validator is short-circuited to accept everything" \
  "test_an_entry_past_its_recorded_expiry_is_rejected" \
  "    flags: list[str] = []" \
  "    return ([], [])  # AMPUTATED"

echo
echo "$FIRED/$HELD controls fired."
# THE ROW FLOOR. `FIRED -eq HELD` is satisfied by 0 == 0. The zero test
# this replaces caught only TOTAL deletion; the realistic shape is
# PARTIAL - a refactor that drops rows, or an anchor that stops matching
# so a row silently stops being held at all. DERIVED: this harness
# printed "15/15 controls fired." at 71774e2. Lowering this number is a
# visible diff that has to be defended.
ROW_FLOOR=15
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$HELD" "$ROW_FLOOR"
if [ "$HELD" -lt "$ROW_FLOOR" ]; then
  echo "ABORT: $HELD/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 6
fi
[ "$FIRED" -eq "$HELD" ] || exit 1
exit 0
