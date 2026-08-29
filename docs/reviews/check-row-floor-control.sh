#!/usr/bin/env bash
# POSITIVE CONTROL for the row floors added by task #79.
#
# WHY THIS EXISTS. Ten harnesses now carry a ROW_FLOOR. Every one of those
# numbers was derived from a run, but a floor that has never been watched
# FAIL is still only a typed number: the comparison could be inverted, the
# variable could be misspelled under `set -u`, the exit could be swallowed.
# This deletes a real row from a real harness and reads that harness's own
# exit code.
#
# It picks check-u15-gate-amputation.sh because that harness deliberately
# does NOT fail on survivors, so it is the one where "exit 1" can only mean
# the floor fired - nothing else in it exits 1 on a healthy tree.
#
# NOT A CI GATE, on purpose: it edits a tracked file in the working tree.
# It restores by byte-comparison against a backup rather than by re-editing,
# because a `sed` that matches nothing succeeds silently.
#
# Run it from anywhere. Takes about a minute.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
S="$REPO/scripts/check-u15-gate-amputation.sh"
B="$(mktemp)"

# A dirty subject file means someone else is mid-edit; measuring it would
# measure them, not the floor.
if ! git -C "$REPO" diff --quiet -- "$S"; then
  echo "ABORT: $S has uncommitted changes; refusing to measure someone else's tree"
  rm -f "$B"
  exit 3
fi

# THE BACKUP IS TAKEN BEFORE THE TRAP IS ARMED, and that order is the whole
# point. Armed first, an abort on the line above would fire the trap and copy
# the EMPTY file mktemp just made over the harness - a restore that destroys
# the thing it restores. Caught by reading, before this script ever ran.
cp "$S" "$B"
trap 'cp "$B" "$S"; rm -f "$B" "$B.out"' EXIT

# The anchor must be unique and present BEFORE the deletion. A row that was
# already renamed would otherwise delete nothing and pass for the wrong reason.
ANCHOR='report "E. git is not on PATH at all" "$WORK/E" "$WORK/nogit"'
n=$(grep -Fc -- "$ANCHOR" "$S")
echo "anchor occurrences: $n (must be exactly 1)"
[ "$n" -eq 1 ] || { echo "ABORT: the anchor is not unique - repoint it"; exit 9; }

grep -vF -- "$ANCHOR" "$B" > "$S"
if cmp -s "$S" "$B"; then
  echo "ABORT: the deletion did NOT land - the file is unchanged"
  exit 9
fi
echo "deletion landed: $(( $(wc -l < "$B") - $(wc -l < "$S") )) line(s) removed"

echo "--- running the harness with 4 of its 5 rows ---"
PYTHONDONTWRITEBYTECODE=1 bash "$S" > "$B.out" 2>&1
rc=$?
grep -E '^########## [0-9]+/[0-9]+ ROWS|LOST ROWS' "$B.out"
echo "exit with a deleted row: $rc (must be 1)"

cp "$B" "$S"
if cmp -s "$S" "$B"; then echo "restored: byte-identical to the backup"; fi
git -C "$REPO" diff --quiet -- "$S" \
  && echo "restored: and identical to the commit" \
  || { echo "::error::RESTORE FAILED - $S still differs from HEAD"; exit 9; }

rm -f "$B.out"
[ "$rc" -eq 1 ] || { echo "::error::CONTROL DID NOT FIRE - the floor let a lost row through"; exit 1; }
echo "CONTROL FIRED: a deleted row is caught by the floor and exits 1."
