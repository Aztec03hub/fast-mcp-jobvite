#!/usr/bin/env bash
# Task #156 - the positive control for the anchor-landing guard in
# `scripts/check-u1-boot-amputation.sh`.
#
# WHAT IS BEING CONTROLLED. That harness runs 13 inline `python3` heredocs
# that mutate the tree. Before this task NOTHING read their exit status:
# `set -uo pipefail` deliberately omits `-e` (ADR-0023), and no heredoc was
# followed by `|| exit`, `if !` or a `$?` read. So a row whose anchor had
# MOVED ran `report` against an UNMUTATED tree.
#
# WHAT THAT ACTUALLY LOOKS LIKE, and it is NOT the silent green the task row
# assumed. Every declared MUST_DIE id is verified to PASS on the intact
# baseline (harness :284-297). So a row that does not mutate leaves all of
# them passing, and each is printed as `UNEXPECTED SURVIVOR` - the harness
# goes RED, with a diagnosis that blames the TESTS for being vacuous when the
# truth is that the HARNESS's anchor moved. Misdirection, not silence. Arm A0
# below measures exactly that, because a claim about what the old code did is
# worth nothing beside a recording of it doing it.
#
# THREE ARMS. Scoring is on WHICH LINES APPEAR, never on the exit code - A0
# and A1 both exit 1 and mean opposite things, which is the whole point.
#
#   A0  the harness AS IT WAS at $BASE_REV, anchor moved
#       expect: `UNEXPECTED SURVIVOR` naming row C's three test ids,
#               and NO landing diagnostic anywhere.
#   A1  the harness FROM THE WORKING TREE, anchor moved
#       expect: `AMPUTATION DID NOT LAND` for row C, the run stops there,
#               and NO `UNEXPECTED SURVIVOR` is ever printed.
#   B   the harness FROM THE WORKING TREE, tree intact
#       expect: exit 0, every row present, no landing diagnostic.
#
# THE ANCHOR MOVE IS BEHAVIOUR-PRESERVING BY CONSTRUCTION. Row C anchors on
# `    reasons: list[str] = []` in `validate_settings`; the arm rewrites it to
# `    reasons: list[str] = list()`, which is the same object built the same
# way. The suite must stay GREEN or the harness aborts at its baseline with
# exit 3 and the arm proves nothing - a clean zero that explains itself.
#
# IT NEVER TOUCHES THE REPOSITORY IT IS RUN FROM. Each arm copies the tree
# into a scratch directory and runs the harness THERE, so an interrupted arm
# strands its mutation in a directory that is about to be deleted rather than
# in a checkout somebody is committing from.
#
# `-e` deliberately omitted: this probe reads the exit code of a harness that
# is EXPECTED to fail in two of its three arms.
# See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
HARNESS_REL="scripts/check-u1-boot-amputation.sh"
CONFIG_REL="src/fast_mcp_jobvite/config.py"
BASE_REV="${BASE_REV:-ccbdaae}"
ARM_TIMEOUT="${ARM_TIMEOUT:-2400}"

ANCHOR_OLD="    reasons: list[str] = []"
ANCHOR_NEW="    reasons: list[str] = list()"

arm="${1:-}"
case "$arm" in
  A0|A1|B) ;;
  *) echo "usage: $0 {A0|A1|B}   (see the header for what each measures)"; exit 2 ;;
esac

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
echo "arm=$arm scratch=$SCRATCH base_rev=$BASE_REV timeout=${ARM_TIMEOUT}s"

# The copy. `.git` and `.venv` are excluded: the harness never reads git, and
# `uv sync --frozen` rebuilds the environment from the shared cache in under a
# second. Copying a worktree's `.git` FILE would point the copy back at the
# real repository, which is the one thing this probe exists not to touch.
tar -C "$REPO_ROOT" --exclude=.git --exclude=.venv -cf - . | tar -C "$SCRATCH" -xf -
if [ ! -f "$SCRATCH/$HARNESS_REL" ]; then
  echo "PROBE ERROR: the copy has no $HARNESS_REL - nothing below measured anything."
  exit 2
fi

# A0 restores the harness as it was BEFORE this task. Everything else in the
# copy stays at the working tree, so the only difference between A0 and A1 is
# the file under test.
if [ "$arm" = "A0" ]; then
  git -C "$REPO_ROOT" show "$BASE_REV:$HARNESS_REL" >"$SCRATCH/$HARNESS_REL" || {
    echo "PROBE ERROR: could not read $HARNESS_REL at $BASE_REV."
    exit 2
  }
fi

# The anchor move, asserted rather than assumed: a `sed` that matches nothing
# exits 0 and would leave both A arms measuring an INTACT anchor - a probe
# whose treatment never fired.
if [ "$arm" != "B" ]; then
  before=$(grep -c -F -- "$ANCHOR_OLD" "$SCRATCH/$CONFIG_REL")
  python3 - "$SCRATCH/$CONFIG_REL" "$ANCHOR_OLD" "$ANCHOR_NEW" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); old, new = sys.argv[2], sys.argv[3]
s = p.read_text()
i = s.index(old + "\n")
p.write_text(s[:i] + new + "\n" + s[i + len(old) + 1:])
PY
  [ $? -eq 0 ] || { echo "PROBE ERROR: the anchor move did not apply."; exit 2; }
  after=$(grep -c -F -- "$ANCHOR_OLD" "$SCRATCH/$CONFIG_REL")
  echo "anchor move: occurrences of the row-C anchor ${before} -> ${after}"
  if [ "$after" -ne $((before - 1)) ]; then
    echo "PROBE ERROR: expected exactly one occurrence to move; the treatment did not fire."
    exit 2
  fi
fi

( cd "$SCRATCH" && uv sync --frozen >/dev/null 2>&1 )

OUT="$SCRATCH/arm-$arm.txt"
echo "PROBE-START arm=$arm" >"$OUT"   # so "empty" and "never started" differ
( cd "$SCRATCH" && timeout "$ARM_TIMEOUT" bash "$HARNESS_REL" ) >>"$OUT" 2>&1
rc=$?

echo "----------------------------------------------------------------"
echo "arm=$arm harness exit=$rc   (NOT the verdict - read the lines below)"
echo "  rows run (########## lines):     $(grep -c '^########## ' "$OUT")"
# ANCHORED AT THE START OF THE DIAGNOSTIC, not a bare substring. The first
# version of this counter said 4 for arm A0 when the true number is 3: the
# fourth hit was the harness's own closing paragraph, which tells the reader
# to "Search this output for 'UNEXPECTED SURVIVOR'". A grep for a defect
# pattern finds the prose about the defect.
echo "  UNEXPECTED SURVIVOR lines:       $(grep -c '^  UNEXPECTED SURVIVOR: ' "$OUT")"
echo "  landing diagnostics:             $(grep -c -E '^ *[A-Z]+: AMPUTATION DID NOT LAND|AssertionError:.*anchor is not unique' "$OUT")"
echo "  row C reached report():          $(grep -c '^########## C\. ' "$OUT")"
echo "--- the lines that decide the arm ---"
grep -n -E 'DID NOT LAND|anchor is not unique|UNEXPECTED SURVIVOR|^########## C\.|^HARNESS-RESULT' "$OUT" \
  | head -20
echo "--- last 5 lines ---"
tail -5 "$OUT"
cp "$OUT" "$REPO_ROOT/docs/reviews/probe-156-arm-$arm.txt"
echo "output kept at docs/reviews/probe-156-arm-$arm.txt"
