#!/usr/bin/env bash
# POSITIVE CONTROLS for the two harness gates R4-M5 and R4-N1 added.
#
# A fix for "the harness cannot fail" that is not itself proved able to fail is
# the same defect one layer up. Both gates report ZERO on the intact tree, and a
# zero that explains itself is exactly what this project keeps getting wrong -
# so each is made to fire here, on purpose.
#
#   ARM 1 (R4-M5, the vacuous-row gate). Row A14 kills exactly one test. Rename
#          that test and A14 deletes a behaviour with nothing left to notice,
#          which is the vacuous shape. The harness must print VACUOUS ROW and
#          exit 1. Before this gate existed it printed its survivors and exited
#          0.
#
#   ARM 2 (R4-N1, the restore check). NOT run against the harness - run against
#          the INSTRUMENT, because the claim is about the instrument: after
#          `cp b f`, `cmp f b` is equal BY CONSTRUCTION whatever `b` contains,
#          so the old check could not see a corrupted backup. The new check
#          compares against a pristine copy taken before row 1 and can.
#
# Usage:  bash docs/reviews/probe-r4-m5-n1-the-gates-can-fire.sh
# Exit 0 if both gates fired as they must, 1 if either did not, 3 if it could
# not run. The tree is restored either way; it is checked, and the check is
# against a copy taken before anything was touched.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 3

SUITE="tests/test_tools_jobs.py"
KILLED_BY_A14="test_to_job_sets_every_field_the_model_declares"
PRISTINE=$(mktemp -d)
trap 'cp "$PRISTINE/suite.py" "$SUITE" 2>/dev/null; rm -rf "$PRISTINE"' EXIT

cp "$SUITE" "$PRISTINE/suite.py" || exit 3

fail=0

# ---------------------------------------------------------------------------
echo "########## ARM 1 - the R4-M5 vacuous-row gate"
echo "Renaming $KILLED_BY_A14, the only test row A14 kills."

if ! SUITE="$SUITE" NAME="$KILLED_BY_A14" python3 - <<'PY'
import os
import pathlib
import sys

p = pathlib.Path(os.environ["SUITE"])
s = p.read_text()
old = f"def {os.environ['NAME']}("
if s.count(old) != 1:
    print(f"  ANCHOR NOT UNIQUE ({s.count(old)} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, "def _renamed_out_of_collection("))
PY
then
  echo "COULD NOT RUN: the rename anchor moved."
  exit 3
fi

if cmp -s "$SUITE" "$PRISTINE/suite.py"; then
  echo "COULD NOT RUN: the rename did not land."
  exit 3
fi

out=$(bash scripts/check-u5-jobs-amputation.sh 2>&1); rc=$?
cp "$PRISTINE/suite.py" "$SUITE"

printf '%s\n' "$out" | grep -E 'VACUOUS ROW|^::error|^########## ROWS' | sed 's/^/  /'
echo "  harness exit: $rc"

if printf '%s\n' "$out" | grep -q 'VACUOUS ROW' && [ "$rc" -eq 1 ]; then
  echo "  ARM 1 PASSED - the gate fired and the harness went red."
else
  echo "  ARM 1 FAILED - a row deleted a behaviour, killed nothing, and the"
  echo "                 harness did not say so. The R4-M5 gate is inoperative."
  fail=1
fi
echo

# ---------------------------------------------------------------------------
echo "########## ARM 2 - the R4-N1 restore check, against the instrument"
work=$(mktemp -d)
printf 'ORIGINAL\n' > "$work/file"
cp "$work/file" "$work/pristine"      # taken BEFORE row 1, as the harness does
cp "$work/file" "$work/backup"        # the per-row backup

printf 'MUTATED\n' > "$work/file"     # the row applies its change
printf 'MUTATED\n' > "$work/backup"   # ...and the backup is corrupted

cp "$work/backup" "$work/file"        # the restore the harness performs

if cmp -s "$work/file" "$work/backup"; then
  echo "  OLD CHECK (cmp file backup):   passed - and the tree is MUTATED."
  old_blind=1
else
  echo "  OLD CHECK (cmp file backup):   failed"
  old_blind=0
fi

if cmp -s "$work/file" "$work/pristine"; then
  echo "  NEW CHECK (cmp file pristine): passed"
  new_sees=0
else
  echo "  NEW CHECK (cmp file pristine): FAILED - RESTORE FAILED would fire."
  new_sees=1
fi
rm -rf "$work"

if [ "$old_blind" -eq 1 ] && [ "$new_sees" -eq 1 ]; then
  echo "  ARM 2 PASSED - the old form is equal by construction and cannot see a"
  echo "                 corrupted backup; the new form does."
else
  echo "  ARM 2 FAILED - the two checks did not differ, so R4-N1 is wrong or"
  echo "                 this control is."
  fail=1
fi
echo

# ---------------------------------------------------------------------------
if ! cmp -s "$SUITE" "$PRISTINE/suite.py"; then
  echo "::error::TREE IS DIRTY - $SUITE does not match the pre-run copy"
  exit 3
fi
echo "TREE RESTORED - $SUITE matches the copy taken before arm 1."

exit "$fail"
