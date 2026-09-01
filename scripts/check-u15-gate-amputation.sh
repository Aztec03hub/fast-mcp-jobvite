#!/usr/bin/env bash
# U15 amputation harness. A DIFFERENT question from the mutation harness.
#
# Mutation asks: "break one rule - does the named test notice?"
# Amputation asks: "remove the SUBJECT ENTIRELY - does anything still report
# success?" U0 ran both, and only amputation found its one genuinely vacuous
# assertion (U0-REPORT section 7). A test that passes when its subject is not
# there is not a weak test, it is a false instrument.
#
# For each tree this prints the pass/fail counts and NAMES every test that
# still passes, so the report can say which assertions survived and why rather
# than asserting that none did.
#
# This harness does not exit non-zero on survivors - survivors are the OUTPUT.
# It exits non-zero only if it could not run, or if the intact baseline is red.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE_REL="scripts/check-committed-file-types.py"
SUITE_REL="tests/test_file_type_gate.py"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

# THE INTERPRETER IS CHOSEN, NOT INHERITED - see the note in
# scripts/check-u15-gate-controls.sh. Bare `python3` is the runner's
# hosted-toolchain interpreter with no pytest, so the baseline goes red.
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY=("$REPO_ROOT/.venv/bin/python")
else
  PY=(uv run --frozen --project "$REPO_ROOT" python)
fi

build_tree() {  # $1 = destination
  mkdir -p "$1/scripts" "$1/tests"
  cp "$REPO_ROOT/$GATE_REL" "$1/$GATE_REL"
  cp "$REPO_ROOT/$SUITE_REL" "$1/$SUITE_REL"
  cp "$REPO_ROOT/tests/__init__.py" "$1/tests/" 2>/dev/null || true
  cp "$REPO_ROOT/pyproject.toml" "$1/"
}

ROWS=0
# DERIVED - see the note beside the check at the end of this file.
# The assignment is bare on its own line because docs/reviews/check-row-floors.py
# matches `^\s*ROW_FLOOR=(\d+)\s*$`: a trailing comment here makes the floor
# invisible to the checker, which is the same "a floor nobody can see is a
# floor nobody checks" shape the floor itself exists to catch.
ROW_FLOOR=5

report() {  # $1 = label, $2 = tree, $3 = optional PATH override
  local label="$1" tree="$2" pathenv="${3:-$PATH}"
  ROWS=$((ROWS + 1))
  echo "########## $label"
  ( cd "$tree" && env PATH="$pathenv" "${PY[@]}" -m pytest "$SUITE_REL" \
      -p no:cacheprovider -q -o addopts="" -rA >"$WORK/out.txt" 2>&1 )
  tail -1 "$WORK/out.txt"
  local survivors
  survivors=$(grep -E '^PASSED ' "$WORK/out.txt" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    echo "  survivors (assertions that still reported success):"
    echo "$survivors" | sed 's/^/    /'
  fi
  echo
}

# --- baseline: the intact tree, so a red here invalidates every row below ----
build_tree "$WORK/intact"
echo "########## BASELINE - the intact tree"
( cd "$WORK/intact" && "${PY[@]}" -m pytest "$SUITE_REL" -p no:cacheprovider -q \
    -o addopts="" >"$WORK/out.txt" 2>&1 )
BASE_RC=$?
tail -1 "$WORK/out.txt"
if [ "$BASE_RC" -ne 0 ]; then
  echo "ABORT: the intact tree is red; amputation results would be meaningless."
  cat "$WORK/out.txt"
  exit 3
fi
echo

# --- A. the gate script is GONE --------------------------------------------
build_tree "$WORK/A"; rm -f "$WORK/A/$GATE_REL"
report "A. the gate script does not exist at all" "$WORK/A"

# --- B. the gate script exists and is ZERO BYTES ----------------------------
# The clean-empty trap: the import succeeds, so anything that does not actually
# call the gate keeps passing.
build_tree "$WORK/B"; : > "$WORK/B/$GATE_REL"
report "B. the gate script exists but is ZERO BYTES" "$WORK/B"

# --- C. the gate imports, but classify() is gone ----------------------------
build_tree "$WORK/C"
python3 - "$WORK/C/$GATE_REL" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text()
# EVERY re.sub HERE IS ASSERTED. This harness had NO way to report that a row
# failed to apply: `re.sub` that matches nothing returns the string unchanged
# and raises nothing, so the row ran, printed a survivor list, and had amputated
# an INTACT tree. Every survivor it named would then be a false finding, and no
# CI step could gate on it because it printed no phrase for a step to gate on.
# Measured by task #29: this was the only harness here with no anchor-failure
# vocabulary at all.
out = re.sub(r"\ndef classify\(.*?\n    return None\n", "\n", s, flags=re.S)
if out == s:
    print("  C: AMPUTATION DID NOT LAND - the classify() anchor moved. Fix the harness.")
    sys.exit(1)
p.write_text(out)
PY
# `|| exit 1`, because the message alone is not the gate. Without it the row
# would print DID NOT LAND and then run `report` anyway, publishing a survivor
# list measured against an intact tree - the failure sitting one line below its
# own diagnosis.
[ $? -eq 0 ] || exit 1
report "C. the module imports but classify() has been removed" "$WORK/C"

# --- D. the rule tables are present but EMPTY -------------------------------
# Amputating the DATA rather than the code. A gate whose tables are empty runs,
# exits 0 on everything, and looks entirely healthy.
build_tree "$WORK/D"
python3 - "$WORK/D/$GATE_REL" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1])
s = p.read_text()
# Three tables, asserted SEPARATELY. Asserting only that the file changed would
# pass with two of the three still populated, and the row would report that an
# empty rule table is caught while two thirds of the rules were intact - a
# partial amputation reading as a whole one.
#
# WRITTEN OUT RATHER THAN LOOPED, on purpose. The looped version was shorter and
# scripts/check-harness-anchors.py could not read a single one of these three
# patterns out of it - the anchors became tuple elements instead of arguments to
# `re.sub`, and the static checker's coverage dropped from 154 to 151 while
# still reporting OK on everything it could still see. Its floor is what caught
# that. An anchor that a reader cannot find is an anchor nothing defends, so
# these stay verbose and legible to both readers.
def died(label):
    print(f"  D: AMPUTATION DID NOT LAND - the {label} anchor moved. Fix the harness.")
    sys.exit(1)

out = re.sub(r"ALLOWED_EXTENSIONS = frozenset\(\n.*?\n\)",
             "ALLOWED_EXTENSIONS = frozenset()", s, flags=re.S)
if out == s:
    died("ALLOWED_EXTENSIONS")
s = out

out = re.sub(r"DENIED_EXTENSIONS = \{\n.*?\n\}", "DENIED_EXTENSIONS = {}", s, flags=re.S)
if out == s:
    died("DENIED_EXTENSIONS")
s = out

out = re.sub(r"MAGIC = \(\n.*?\n\)", "MAGIC = ()", s, flags=re.S)
if out == s:
    died("MAGIC")
p.write_text(out)
PY
[ $? -eq 0 ] || exit 1
report "D. the gate runs but every rule table is EMPTY" "$WORK/D"

# --- E. git is unavailable --------------------------------------------------
# Everything that shells out to git loses its subject; everything that calls
# classify() in-process does not.
build_tree "$WORK/E"
mkdir -p "$WORK/nogit"
# `python3` here is the CHOSEN interpreter, not the ambient one - the row's
# subject is "git is absent", and symlinking a python without pytest would
# make it fail for the wrong reason and read as a finding about git.
for tool in sh env sed grep cat; do
  src=$(command -v "$tool") && ln -sf "$src" "$WORK/nogit/$tool"
done
ln -sf "$(command -v "${PY[0]}")" "$WORK/nogit/python3"
report "E. git is not on PATH at all" "$WORK/E" "$WORK/nogit"

echo "########## $ROWS/$ROW_FLOOR ROWS"
echo "########## END. Survivors above are the finding, not a failure."

# THE ROW FLOOR, and the counter it needs, which this harness did not have.
#
# Every other harness here tallies its rows. This one deliberately does not
# fail on survivors - they are the OUTPUT - and it had NO row count at all,
# so it had nothing a floor could be compared against and no line a reader
# could check. Delete four of the five `report` calls and the old ending
# printed the same closing sentence and exited 0, which is the defect this
# whole branch is about, in its purest form: the harness cannot lose rows
# loudly because it never counted them.
#
# The counter does not change what a survivor means. A survivor still does
# not fail the run. Only a MISSING ROW does.
#
# DERIVED: the run at b6e8e3b printed five row headers - A, B, C, D and E -
# counted with `grep -cE '^########## [A-E]\.'` over its output, before this
# counter existed to print the number itself. Lowering this is a visible
# diff that has to be defended.
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "::error::$ROWS/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         A harness with fewer rows than its floor is green for the"
  echo "         wrong reason. Survivors are the output; a missing row is not."
  exit 1
fi
