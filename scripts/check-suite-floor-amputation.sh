#!/usr/bin/env bash
# Amputation harness for the suite-floor guard.
#
# Deletes one behaviour of `check-suite-floor.sh` at a time and requires
# `tests/test_suite_floor.py` to go red. A guard against a silently-shrinking
# suite is itself a thing that can silently stop working, and it would fail in
# exactly the way it exists to catch: quietly, with everything green.
#
# AMPUTATION, not mutation. Changing a comparison leaves the shape of the code
# intact and a forgiving assertion can still match; deleting the branch outright
# cannot be matched by accident. In five consecutive units on this project,
# amputation found an assertion that mutation had passed.
#
# THE LANDING CHECK IS `cmp` AGAINST A BACKUP, NOT `git diff`. The first run of
# this harness used `git diff --quiet`, and the script under test was untracked
# at the time - so every row reported "did not land" while every amputation had
# in fact landed. A clean zero that explains itself is the dangerous kind.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/.." && pwd)
SCRIPT="$REPO/scripts/check-suite-floor.sh"
TESTS="$REPO/tests/test_suite_floor.py"
BACKUP=$(mktemp)

export PYTHONDONTWRITEBYTECODE=1

cleanup () { cp "$BACKUP" "$SCRIPT"; rm -f "$BACKUP"; }
trap cleanup EXIT

cp "$SCRIPT" "$BACKUP"

fired=0
total=0

amputate () {
  local name="$1" old="$2" new="$3"
  total=$((total + 1))
  cp "$BACKUP" "$SCRIPT"

  python3 - "$SCRIPT" "$old" "$new" <<'PY' || return 1
import sys, pathlib
p, old, new = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
t = p.read_text()
if old not in t:
    print(f"    ANCHOR MISSING: {old[:60]!r}"); sys.exit(1)
if t.count(old) != 1:
    print(f"    ANCHOR NOT UNIQUE ({t.count(old)}x): {old[:60]!r}"); sys.exit(1)
p.write_text(t.replace(old, new, 1))
PY

  if cmp -s "$SCRIPT" "$BACKUP"; then
    echo "  $name: DID NOT LAND (file unchanged) - this row proves nothing"
    return 1
  fi

  local out
  out=$(cd "$REPO" && uv run --frozen pytest "$TESTS" -q 2>&1 | tail -1)
  # `grep -q` exits on its FIRST match; if the writer is still
  # writing it takes SIGPIPE, and `pipefail` promotes that 141 to
  # the pipeline's status - so a string that IS present reports as
  # ABSENT, but only once the output outruns the pipe buffer.
  # Measured: present+large 141, present+small 0. A bash test has
  # no second process and cannot SIGPIPE.
  if [[ "$out" == *"failed"* ]]; then
    echo "  KILLED   $name -> $out"
    fired=$((fired + 1))
  else
    echo "  SURVIVED $name -> $out"
  fi
}

echo "Amputating scripts/check-suite-floor.sh:"

amputate "A1 the floor comparison is deleted" \
  'if [ "$passed" -lt "$floor" ]; then' 'if false; then'
amputate "A2 the empty-count guard is deleted, so a dead run reads as a pass" \
  'if [ -z "$passed" ]; then' 'if false; then'
amputate "A3 the usage guard is deleted, so a typo'd floor is not distinguished" \
  "  '' | *[!0-9]*)" "  'NEVER_MATCHES_ANYTHING')"
amputate "A4 the summary is read as the FIRST match, so a test's stdout spoofs it" \
  'tail -1 | cut' 'head -1 | cut'

cleanup
trap - EXIT

echo
echo "$fired/$total amputations killed a test."

# Post-run re-check of the real script, the same requirement the coupling
# harness carries: a harness that leaves the tree mutated is worse than none.
if ! (cd "$REPO" && uv run --frozen pytest "$TESTS" -q >/dev/null 2>&1); then
  echo "::error::post-run re-check FAILED - the harness did not restore the script"
  exit 1
fi
echo "post-run re-check of the real script: exit=0"

# THE ROW FLOOR. `fired -ne total` is satisfied by 0 == 0, and a zero
# test catches only TOTAL deletion. The realistic shape is PARTIAL: a
# refactor drops rows, or an anchor stops matching and its row silently
# stops being counted. DERIVED: this harness printed "4/4 amputations
# killed a test." at 7d3800c. Lowering this number is a visible diff
# that has to be defended.
ROW_FLOOR=4
if [ "$total" -lt "$ROW_FLOOR" ]; then
  echo "::error::$total/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi
if [ "$fired" -ne "$total" ]; then
  echo "::error::$fired of $total fired. A SURVIVOR is the output, not a crash -"
  echo "         it names an amputation no test noticed. Write the test."
  exit 1
fi
