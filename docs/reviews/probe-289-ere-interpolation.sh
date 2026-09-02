#!/usr/bin/env bash
# ARMS for #289: a TEST NAME interpolated into an extended regular expression.
#
# THE CLASS. Four lines across three harnesses built their kill verdict by
# pasting a test name straight into a `grep -E` pattern:
#
#   scripts/check-u3-audit-controls.sh    ^(FAILED|ERROR) [^ ]*$want
#   scripts/check-u4-client-controls.sh   ^FAILED $SUITE::$want
#   scripts/check-u15-gate-controls.sh    (FAILED|ERROR) .*::${TEST}\b
#   scripts/check-u15-gate-controls.sh    ^(FAILED|ERROR) .*${TEST}
#
# A name is a LITERAL. In an ERE it is a PATTERN, so a parametrised id like
# `test_x[1]` matches the CHARACTER `1` and never the literal `[1]`, and the
# `.` in `$SUITE` matches any character at all. #264 measured this as REAL and
# demonstrated it, and as UNREACHABLE TODAY: 0 of 681 test names in this repo
# carry a regex metacharacter and 0 parametrised node ids reach one of these
# greps. So this is HARDENING against a named trigger - the first `@pytest.
# mark.parametrize`d killer named in a harness row - and not a live bug.
#
# WHAT THESE ARMS PROVE, per site, in BOTH directions:
#   N   a name with a metacharacter that the OLD expression matches WRONGLY
#       (a kill reported against a test that never failed) and the NEW one
#       does not.
#   P1  the same metacharacter name present LITERALLY: the NEW expression
#       reports the kill, the OLD one MISSES it. The hazard cuts both ways.
#   P2  a REAL, metacharacter-free killer name taken from the harness's own
#       rows: still a kill after the change. A verdict that stopped matching
#       everything would pass N and P1 and be worthless, and "not-killed" is
#       the answer a broken expression gives to every question.
#
# THE NEW EXPRESSION IS READ OUT OF EACH HARNESS, NEVER RETYPED, for the
# reason probe-284 and probe-252-rc4 give: a copy here would be free to agree
# with a harness that had drifted. The OLD expressions above ARE quoted, and
# deliberately: they are a RECORD of what stood at c965ce0, not a live claim,
# and section POP re-derives that none of them survives in the tree.
#
# `-e` deliberately omitted: this probe runs expressions that are EXPECTED to
# report not-killed. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd)" || {
    echo "REFUSING: could not derive REPO_ROOT from ${BASH_SOURCE[0]}" >&2; exit 3; }
cd "$REPO_ROOT" || exit 3

# THE ONE CANONICAL RESULT LINE (#107). It arms an EXIT trap, so an abort
# cannot render identically to a pass, and it is what
# check-row-floor-controls.sh reads to prove this file's ROW_FLOOR can fire.
# shellcheck source=../../scripts/lib/harness-result.sh
. "$REPO_ROOT/scripts/lib/harness-result.sh"

WORK="$(mktemp -d)" || { echo "REFUSING: mktemp -d failed" >&2; exit 3; }
# `harness_result_emit` FIRST: the sourced file armed its own EXIT trap and
# bash has no trap stack, so this REPLACES it.
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

U3=scripts/check-u3-audit-controls.sh
U4=scripts/check-u4-client-controls.sh
U15=scripts/check-u15-gate-controls.sh
for f in "$U3" "$U4" "$U15"; do
  [ -s "$f" ] || { echo "REFUSING: subject not found at $f"; exit 3; }
done

ROWS=0
FIRED=0
row() {  # row <label> <got> <want>
  ROWS=$((ROWS + 1))
  if [ "$2" = "$3" ]; then
    printf '  %-64s %-11s PASS\n' "$1" "$2"
    FIRED=$((FIRED + 1))
  else
    printf '  %-64s %-11s FAIL (wanted %s)\n' "$1" "$2" "$3"
  fi
}

# ---------------------------------------------------------------------------
# The three NEW verdict expressions, read out of the shipped harnesses. Each
# harness runs `<var>="..." awk '<program>' "<log>"`, so the program is what is
# extracted and the name is handed to it the same way the harness hands it -
# through the environment, which is the whole point of the change.
# ---------------------------------------------------------------------------
read_awk() {  # read_awk <file> <log-variable-name>
  sed -n "s/.*awk '\(.*\)' \"\$$2\".*/\1/p" "$1" | head -1
}
AWK_U3=$(read_awk "$U3" MUT_OUT)
AWK_U4=$(read_awk "$U4" MUT_OUT)
AWK_U15=$(sed -n "s|.*awk '\(.*\)' \"\$WORK/out.txt\".*|\1|p" "$U15" | head -1)
for pair in "u3:$AWK_U3" "u4:$AWK_U4" "u15:$AWK_U15"; do
  [ -n "${pair#*:}" ] || {
    echo "REFUSING: could not read the ${pair%%:*} verdict expression out of its harness."
    echo "It is supposed to be an \"awk '...' <log>\" line. If the harness changed"
    echo "shape this probe is measuring nothing, and says so rather than passing."
    exit 3; }
done
echo "verdict expression read from $U3:"
echo "    awk '$AWK_U3'"
echo "verdict expression read from $U4:"
echo "    awk '$AWK_U4'"
echo "verdict expression read from $U15:"
echo "    awk '$AWK_U15'"
echo

# The REAL killer names are DERIVED from the harnesses' own rows, never
# retyped: a name typed here would be free to agree with a row that had been
# renamed, and P2 would then be green about a test nobody runs.
REAL_U3=$(grep -oE "'test_[a-z0-9_]+'" "$U3" | head -1 | tr -d "'")
REAL_U4=$(grep -oE "'test_[a-z0-9_]+'" "$U4" | head -1 | tr -d "'")
REAL_U15=$(sed -n 's/.*@@\(test_[a-z0-9_]*\)$/\1/p' "$U15" | head -1)
SUITE_U4=$(sed -n 's/^SUITE="\(.*\)"$/\1/p' "$U4" | head -1)
for pair in "u3:$REAL_U3" "u4:$REAL_U4" "u15:$REAL_U15" "suite:$SUITE_U4"; do
  [ -n "${pair#*:}" ] || { echo "REFUSING: no real ${pair%%:*} name derived"; exit 3; }
done
echo "real killer names derived: $REAL_U3 / $REAL_U4 / $REAL_U15"
echo "u4 suite derived: $SUITE_U4"
echo

# The metacharacter name. `[1]` is what `@pytest.mark.parametrize` produces and
# is the exact trigger #264 named. It is used as the SUFFIX of a real-looking
# name so that its bracket - not some unrelated difference - is the single
# variable between the arms.
META='test_zzz_parametrised[1]'
# What the OLD ERE collapses `[1]` to: the single character `1`.
COLLAPSED=test_zzz_parametrised1

# ---------------------------------------------------------------------------
# POP: the population, re-derived. The class is defined by a DISCRIMINATOR,
# not a list: a `grep -E` whose pattern interpolates a shell variable holding a
# TEST NAME (a literal), as against one holding a pattern the row DECLARED
# (`$want_re`, `$ROW_RE`, `$EXPECT_UNCOLLECTABLE`, `$PATTERN`), which is
# safe by design. Comment lines are excluded - a grep for a defect pattern
# finds the comment that forbids it, and this file is itself proof of that.
# Four lines qualified. This section asserts each is gone, by its own text.
# ---------------------------------------------------------------------------
echo "########## POP: none of the four ERE-interpolating lines survives"
gone() {  # gone <label> <file> <fixed-string>
  local got=present
  grep -F "$3" "$2" | grep -qv '^ *#' || got=gone
  row "$1" "$got" gone
}
gone "u3   ^(FAILED|ERROR) [^ ]*\$want"   "$U3"  'grep -qE "^(FAILED|ERROR) [^ ]*$want"'
gone "u4   ^FAILED \$SUITE::\$want"       "$U4"  'grep -qE "^FAILED $SUITE::$want"'
gone "u15  (FAILED|ERROR) .*::\${TEST}"   "$U15" 'grep -qE "(FAILED|ERROR) .*::${TEST}'
gone "u15  ^(FAILED|ERROR) .*\${TEST}"    "$U15" 'grep -qE "^(FAILED|ERROR) .*${TEST}"'
echo

# ---------------------------------------------------------------------------
verdict_u3()  { w="$1" awk "$AWK_U3"  "$2" && echo killed || echo not-killed; }
verdict_u4()  { w="$1" awk "$AWK_U4"  "$2" && echo killed || echo not-killed; }
verdict_u15() { t="$1" awk "$AWK_U15" "$2" && echo killed || echo not-killed; }

echo "########## U3: ^(FAILED|ERROR) [^ ]*\$want"
# N: the log names the COLLAPSED test. It really failed; $META did not.
printf 'FAILED tests/test_audit.py::%s - AssertionError\n' "$COLLAPSED" >"$WORK/u3n"
if grep -qE "^(FAILED|ERROR) [^ ]*$META" "$WORK/u3n"; then old=killed; else old=not-killed; fi
row "N  OLD reports a kill for a test that never failed" "$old" killed
row "N  NEW does not" "$(verdict_u3 "$META" "$WORK/u3n")" not-killed
# P1: the log names $META literally.
printf 'FAILED tests/test_audit.py::%s - AssertionError\n' "$META" >"$WORK/u3p1"
row "P1 NEW reports the real kill of a parametrised name" \
    "$(verdict_u3 "$META" "$WORK/u3p1")" killed
# P2: a real killer, no metacharacter. The fix must not stop matching.
printf 'FAILED tests/test_audit.py::%s - AssertionError\n' "$REAL_U3" >"$WORK/u3p2"
row "P2 NEW still reports a kill for $REAL_U3" \
    "$(verdict_u3 "$REAL_U3" "$WORK/u3p2")" killed
echo

echo "########## U4: ^FAILED \$SUITE::\$want"
# N exercises BOTH metacharacters the old line carried: the `.` of `.py` and
# the `[1]` of the name.
printf 'FAILED %s::%s - AssertionError\n' "${SUITE_U4/./X}" "$COLLAPSED" >"$WORK/u4n"
if grep -qE "^FAILED $SUITE_U4::$META" "$WORK/u4n"; then old=killed; else old=not-killed; fi
row "N  OLD reports a kill on a WRONG file and a WRONG test" "$old" killed
row "N  NEW does not" "$(verdict_u4 "$SUITE_U4::$META" "$WORK/u4n")" not-killed
printf 'FAILED %s::%s - AssertionError\n' "$SUITE_U4" "$META" >"$WORK/u4p1"
row "P1 NEW reports the real kill of a parametrised name" \
    "$(verdict_u4 "$SUITE_U4::$META" "$WORK/u4p1")" killed
printf 'FAILED %s::%s - AssertionError\n' "$SUITE_U4" "$REAL_U4" >"$WORK/u4p2"
row "P2 NEW still reports a kill for $REAL_U4" \
    "$(verdict_u4 "$SUITE_U4::$REAL_U4" "$WORK/u4p2")" killed
echo

echo "########## U15: (FAILED|ERROR) .*::\${TEST}\\b  and  ^(FAILED|ERROR) .*\${TEST}"
printf 'FAILED tests/test_file_type_gate.py::%s - AssertionError\n' "$COLLAPSED" >"$WORK/u15n"
if grep -qE "(FAILED|ERROR) .*::${META}\b" "$WORK/u15n" \
   || grep -qE "^(FAILED|ERROR) .*${META}" "$WORK/u15n"; then old=fired; else old=held; fi
row "N  OLD fires the control on a test that never failed" "$old" fired
row "N  NEW does not" "$(verdict_u15 "$META" "$WORK/u15n")" not-killed
printf 'FAILED tests/test_file_type_gate.py::%s - AssertionError\n' "$META" >"$WORK/u15p1"
row "P1 NEW fires on a real parametrised failure" \
    "$(verdict_u15 "$META" "$WORK/u15p1")" killed
printf 'FAILED tests/test_file_type_gate.py::%s - AssertionError\n' "$REAL_U15" >"$WORK/u15p2"
row "P2 NEW still fires for $REAL_U15" \
    "$(verdict_u15 "$REAL_U15" "$WORK/u15p2")" killed
echo

echo "########## ROWS: $FIRED/$ROWS passed"
harness_result_tally fired "$FIRED" "$ROWS"
ROW_FLOOR=16
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "FEWER ROWS THAN THE FLOOR ($ROWS/$ROW_FLOOR) - rows were lost."
  exit 1
fi
[ "$FIRED" -eq "$ROWS" ] || exit 1
echo "PROBE-289: all four sites converted, each proved in both directions."
