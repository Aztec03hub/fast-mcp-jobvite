#!/usr/bin/env bash
# #254: is a non-measurement exit code REACHABLE in check-u3-audit-amputation.sh,
# and does the REAL harness refuse it?
#
# The task recorded rc=4 as "unreachable today" because this harness passes a
# bare $SUITE with no per-row selector - no node id to mistype, no coverage map
# to be missing. That reasoning is about rc=4 ONLY. It says nothing about rc=2,
# COLLECTION ERROR, which this harness can cause ITSELF: every row rewrites a
# source file by text substitution, and a substitution that lands can leave the
# module syntactically invalid.
#
# The verdict logic reads `^PASSED ` lines and calls their absence a kill. A
# collection error produces no PASSED lines. So the question is not academic.
#
# WHAT EACH ARM MEASURES, AND WHAT IT MEASURES IT AGAINST. The first version of
# this probe RETYPED the harness's verdict logic into a local `new_verdict()`
# and never executed the harness at all. Measured: deleting the whole guard
# from scripts/check-u3-audit-amputation.sh left that probe at 4/4, exit 0.
# Every arm below therefore names its artifact:
#
#   ARM 1  real pytest, on the harness's own $SUITE, against a really-planted
#          invalid-Python edit.            ARTIFACT: pytest. Expect rc=2.
#   ARM 2  the PRE-FIX inference (count `^PASSED `, absence == kill) over that
#          exact output.                   ARTIFACT: the old logic. Expect a
#                                          false kill - that is the defect.
#   ARM 3  THE REAL HARNESS, built as a one-row derivative whose A1 replacement
#          is invalid Python.              ARTIFACT: check-u3-audit-amputation.sh
#                                          itself. Expect exit 5 and REFUSING.
#   ARM 3b the tree after that refusal.    ARTIFACT: the restore-before-refuse
#                                          claim. Expect src/ clean.
#   ARM 4  positive control: THE REAL HARNESS, same derivative, A1 replacement
#          UNTOUCHED.                      ARTIFACT: the same harness. Expect
#                                          NOT 5, and the row scored.
#
# THE DERIVATIVE IS BUILT FROM THE HARNESS'S OWN TEXT, never retyped, and the
# build ASSERTS every anchor it depends on. If the harness is refactored this
# probe ABORTS (exit 3) rather than silently measuring a stale copy - the
# standard docs/reviews/probe-252-rc4-verdict-trap.sh:29-33 states and
# implements at :70-76.
#
# WHY A DERIVATIVE AND NOT THE HARNESS VERBATIM. The refusal needs a mutation
# that breaks the import, and the harness's own pre-flight
# (`git status --porcelain -- "$AUDIT" "$REDACT"`) refuses a PRE-PLANTED one -
# so the plant has to come from a harness row. One row also keeps this probe to
# five suite runs instead of twenty-two.
#
# `-e` deliberately omitted: this probe reads the exit codes of runs that are
# EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md.
set -uo pipefail

# shellcheck source=../../scripts/lib/harness-result.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/harness-result.sh"
# The library ARM 5 exercises, sourced ONCE and at the top - the same shape
# every adopter uses, and the shape docs/reviews/check-checkers-are-wired.py
# requires of anything that calls a scripts/lib/ function.
# shellcheck source=../../scripts/lib/verdict-guard.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/verdict-guard.sh" || {
  echo "REFUSING: scripts/lib/verdict-guard.sh could not be sourced; ARM 5 is its control." >&2
  exit 2
}

cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." || {
    echo "REFUSING: could not reach the repo root from ${BASH_SOURCE[0]}" >&2; exit 2; }
REPO=$PWD
export PYTHONDONTWRITEBYTECODE=1

HARNESS=scripts/check-u3-audit-amputation.sh
GUARD_LIB=scripts/lib/verdict-guard.sh
DERIV=scripts/zz-probe-254-one-row.sh
AUDIT="src/fast_mcp_jobvite/audit.py"
# Bounded, like every other pytest call in a tracked .sh here: a hung suite
# produces no result lines, so every assertion "did not survive" and the row
# reads as a pass. Declared ONCE and interpolated - `timeout 300` retyped at
# each call site is invisible to check-timeout-literals.py, which scans `echo`
# lines and not `timeout` arguments.
PYTEST_TIMEOUT=300

for required in "$HARNESS" "$GUARD_LIB" "$AUDIT"; do
    [ -f "$required" ] || { echo "REFUSING: $required absent at $REPO"; exit 2; }
done
if [ -n "$(git status --porcelain -- "$AUDIT")" ]; then
    echo "REFUSING: $AUDIT has uncommitted changes; this probe mutates and restores it."
    exit 2
fi

WORK=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$WORK"; rm -f "$REPO/$DERIV"; git -C "$REPO" checkout -- "$AUDIT" 2>/dev/null' EXIT

pass=0; fail=0
ok(){ echo "  PASS  $1"; pass=$((pass+1)); }
no(){ echo "  FAIL  $1"; fail=$((fail+1)); }

# THE SUITE IS READ OUT OF THE HARNESS, NEVER RETYPED. Collection behaviour is
# the whole subject here, and pytest's rc depends on WHAT it was asked to run
# (probe-252-rc4-verdict-trap.sh:8-19: a bare file list gives 2, a node id 4).
# A probe about rc that used a different argument list would be asking a
# different question.
SUITE=$(sed -n 's/^SUITE="\(.*\)"$/\1/p' "$HARNESS" | head -1)
[ -n "$SUITE" ] || { echo "ABORT: could not read SUITE out of $HARNESS"; exit 3; }
echo "SUITE read from $HARNESS: $SUITE"
echo

# ---------------------------------------------------------------------------
# build_deriv <mode>   mode = broken | intact
# ---------------------------------------------------------------------------
# A ONE-ROW copy of the REAL harness: everything above the A2 section header,
# plus the harness's own closing calls. `broken` additionally replaces A1's
# replacement text with invalid Python, so the row's own substitution is what
# breaks the module - exactly the mechanism #254 is about.
build_deriv() {
    MODE="$1" HARNESS="$HARNESS" DERIV="$DERIV" python3 - <<'PY'
import os, pathlib, sys
src = pathlib.Path(os.environ["HARNESS"]).read_text()
marker = ("# ---------------------------------------------------------------------------\n"
          "# A2 -")
if src.count(marker) != 1:
    print(f"ABORT: the A2 section header is not unique in the harness "
          f"({src.count(marker)} hits). It has been refactored; this probe "
          f"refuses to measure a stale copy.", file=sys.stderr)
    sys.exit(3)
src = src[:src.index(marker)] + '\nharness_result_ran "$HR_COUNTED_ROWS" 0\n'
a1 = "  '    return []'\n"
if src.count(a1) != 1:
    print(f"ABORT: A1's replacement text is not unique in the truncated harness "
          f"({src.count(a1)} hits). The row moved; this probe refuses to "
          f"measure a stale copy.", file=sys.stderr)
    sys.exit(3)
if os.environ["MODE"] == "broken":
    src = src.replace(a1, "  '    return [ (   # deliberately unbalanced'\n")
pathlib.Path(os.environ["DERIV"]).write_text(src)
PY
}

echo "=== ARM 1: can an amputation make pytest exit with a collection error? ==="
echo "    artifact: pytest, on the harness's own \$SUITE"
# A text substitution of exactly the kind the harness performs, chosen so the
# result is syntactically invalid. This is not a contrived edit: it deletes a
# block body and leaves the block header, which is what happens whenever a
# replacement is shorter than its anchor and the anchor spanned an indent.
python3 - "$AUDIT" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1]); s = p.read_text()
m = re.search(r'^(\s*)def (\w+)\(', s, re.M)
assert m, "no def found to break"
# leave the def header, delete its whole body -> IndentationError on import
start = m.start()
end = s.find("\ndef ", m.end())
if end == -1: end = len(s)
p.write_text(s[:start] + m.group(0) + "\n" + s[end:])
PY
python3 -c "import ast,sys; ast.parse(open('$AUDIT').read())" 2>/dev/null \
    && { echo "  the planted edit is still valid Python - probe cannot proceed"; exit 2; }
echo "  planted: $AUDIT no longer parses"

OUT="$WORK/rowout.txt"
# shellcheck disable=SC2086
timeout "$PYTEST_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
rc=$?
git -C "$REPO" checkout -- "$AUDIT"
echo "  pytest exited: $rc"
echo "  PASSED lines in its output: $(grep -cE '^PASSED ' "$OUT" || true)"
if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
    ok "ARM 1: a landed amputation produced rc=$rc, NOT a 0/1 measurement"
else
    no "ARM 1: expected a non-measurement rc, got $rc - defect may be unreachable"
fi

echo
echo "=== ARM 2: the PRE-FIX inference over that exact output ==="
echo "    artifact: the verdict logic as it stood before #254"
survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
if [ -z "$survivors" ]; then old_verdict="survivors: NONE (reported as a KILL)"
else old_verdict="survivors: $(printf '%s\n' "$survivors" | wc -l)"; fi
echo "  OLD says -> $old_verdict"
if [ -z "$survivors" ]; then
    ok "ARM 2: the pre-fix inference reports a broken run as a successful kill - THE DEFECT"
else
    no "ARM 2: the pre-fix inference did not produce the false kill this probe exists to show"
fi

echo
echo "=== ARM 3: THE REAL HARNESS, one row, replacement made invalid Python ==="
echo "    artifact: $HARNESS itself"
build_deriv broken || { echo "  (see the ABORT above)"; exit 3; }
timeout "$PYTEST_TIMEOUT" bash "$DERIV" >"$WORK/harness.txt" 2>&1
hrc=$?
rm -f "$DERIV"
sed 's/^/    /' "$WORK/harness.txt" | tail -12
echo "  the real harness exited: $hrc"
if [ "$hrc" -eq 5 ] && grep -q "REFUSING: pytest exited" "$WORK/harness.txt"; then
    ok "ARM 3: the REAL harness REFUSED the run the pre-fix inference scored as a kill"
else
    no "ARM 3: the REAL harness exited $hrc and/or printed no REFUSING line"
fi

# ARM 3b: the restore-before-refuse claim the branch makes, measured. The
# refusal is an `exit` from inside `amputate()`, so a guard placed ABOVE the
# `git checkout --` would strand a mutated tree for the next reader.
dirty=$(git -C "$REPO" status --porcelain -- src/)
if [ -z "$dirty" ]; then
    ok "ARM 3b: the refusal left src/ clean - the restore ran before the exit"
else
    no "ARM 3b: the refusal STRANDED a mutation in src/: $dirty"
fi

echo
echo "=== ARM 4: positive control - the SAME real harness, replacement intact ==="
echo "    artifact: $HARNESS itself"
build_deriv intact || { echo "  (see the ABORT above)"; exit 3; }
timeout "$PYTEST_TIMEOUT" bash "$DERIV" >"$WORK/clean.txt" 2>&1
crc=$?
rm -f "$DERIV"
sed 's/^/    /' "$WORK/clean.txt" | tail -6
echo "  the real harness exited: $crc"
# Tightened from "0 or 1": the harness gates its own baseline green before any
# row runs, so 0 is the only healthy answer and accepting 1 would let a fully
# red tree pass the control. The `survivors:` line is required too - an exit 0
# that scored no row would satisfy an exit-code-only check.
if [ "$crc" -eq 0 ] && grep -q "^  survivors" "$WORK/clean.txt"; then
    ok "ARM 4: the REAL harness ran the row and scored it - the guard is not blanket-refusing"
else
    no "ARM 4: the REAL harness exited $crc and/or scored no row - OVER-REFUSAL"
fi

echo
echo "=== ARM 5: the library's own case arms, both of them, called directly ==="
echo "    artifact: $GUARD_LIB"
# WHY THIS IS NOT THE RETYPED-COPY MISTAKE C1 WAS ABOUT. C1's probe modelled the
# guard in a local function and tested the model. This arm SOURCES THE REAL FILE
# and calls the real function; the artifact under test is the library itself.
#
# WHY IT IS NEEDED AT ALL. ARMs 3 and 4 both drive the harness, and in both the
# derivative's single row makes tests FAIL - pytest returns 2 in ARM 3 and 1 in
# ARM 4 - so NOTHING above ever calls verdict_guard with 0. MEASURED: narrowing
# `0|1)` to `1)`, a guard that refuses every clean row, SURVIVED this probe at
# 5/5 exit 0 before this arm existed. That mutant is not academic - rc=0 on an
# amputated row is the VACUOUS ROW case, and check-u9-http-amputation.sh has an
# explicit `if [ "$rc" -eq 0 ]` branch downstream of the guard whose finding
# would have been switched off silently.
( verdict_guard 0 /dev/null 1 ) >/dev/null 2>&1
g0=$?
( verdict_guard 2 /dev/null 1 ) >/dev/null 2>&1
g2=$?
echo "  verdict_guard 0 -> $g0 (want 0, ACCEPT)   verdict_guard 2 -> $g2 (want 5, REFUSE)"
if [ "$g0" -eq 0 ] && [ "$g2" -eq 5 ]; then
    ok "ARM 5: rc=0 is accepted and rc=2 refuses - both arms of the case reached"
else
    no "ARM 5: verdict_guard 0 -> $g0 (want 0), verdict_guard 2 -> $g2 (want 5)"
fi

echo
echo "arms passed: $pass   failed: $fail"
ROWS=$((pass + fail))
harness_result_tally fired "$pass" "$ROWS"
ROW_FLOOR=6
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
    echo "FEWER ARMS THAN THE FLOOR ($ROWS/$ROW_FLOOR) - arms were lost."
    exit 1
fi
[ "$fail" -eq 0 ] || exit 1
