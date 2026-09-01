#!/usr/bin/env bash
# THE NEGATIVE CONTROL for the rewritten docs/reviews/check-row-floor-controls.sh.
# Task #107.
#
# WHY. That control was rewritten to parse ONE canonical line instead of three
# hand-kept prose literals, and a checker that has been rewritten and never
# watched FAIL is untested: it would pass identically if its assertions had been
# deleted. So each arm below PLANTS a specific defect in the subject harness's
# canonical line and requires the control to go red - and to go red for the
# stated reason, not merely to be red.
#
# HOW THE PLANT REACHES THE CONTROL, and why nothing is staged any more. The
# control under test refuses to run on a dirty subject, because a dirty subject
# means someone else is mid-edit and measuring it would measure them. This probe
# needs the opposite, so it sets `ROW_FLOOR_CONTROL_ALLOW_PLANTED=1` - an opt-in
# that control names, for this caller.
#
# IT USED TO `git add` THE PLANT INSTEAD, and that is worth recording. The guard
# was `git diff --quiet`, which compares the WORKING TREE TO THE INDEX, so
# staging made a modified file read CLEAN. The probe was not working around a
# guard; it was relying on a DEFECT in one, and the header here described the
# trick as a technique. When the guard was widened to `git status --porcelain`
# every arm stopped firing at once - which is how the dependency was found, and
# why it is now declared rather than smuggled. Staging is gone: the trap
# restores with `git checkout --`, and with nothing ever staged that is the
# same as restoring from HEAD.
#
# THE SUBJECT is the cheapest harness in the control's table (about one second),
# chosen so this probe can be run often rather than admired.
#
# `-e` deliberately omitted: every arm reads the exit code of a command EXPECTED
# to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTROL="$REPO/docs/reviews/check-row-floor-controls.sh"
TARGET=check-harness-anchors-controls.sh
S="$REPO/scripts/$TARGET"

FIRED=0
TOTAL=0

# `git status --porcelain`, NOT `git diff --quiet`. `git diff` compares the
# worktree to the INDEX, so a file edited and then `git add`-ed reads CLEAN
# and this guard waves it through. Measured: modify + `git add` gives
# `git diff --quiet` exit 0 and `--porcelain` a non-empty `M `.
#
# THIS SITE IS THE SEVERE ONE. `restore()` below runs `git reset HEAD --`
# then `git checkout --`, which IS HEAD-relative - so a STAGED edit here is
# not merely measured, it is DESTROYED. The abort message below has always
# said so; the guard could not see the case it describes.
if [ -n "$(git -C "$REPO" status --porcelain -- "$S")" ]; then
  echo "ABORT: $S is already modified (staged, unstaged or both). This probe"
  echo "       stages edits to it and restores with 'reset HEAD' +"
  echo "       'checkout --', which would DESTROY that work."
  exit 3
fi

restore() {
  # `reset` CLEARS THE INDEX ENTRY THIS PROBE ADDED, then `checkout` takes
  # the worktree back. Together they are HEAD-relative, which WOULD destroy
  # an operator's staged work in this file - so the pre-flight above must
  # refuse any dirty subject, staged included, and now does. That guard is
  # what makes this pair safe; it was `git diff --quiet` and could not see
  # a staged file at all.
  git -C "$REPO" reset -q HEAD -- "$S" 2>/dev/null
  git -C "$REPO" checkout -- "$S" 2>/dev/null
}
trap restore EXIT

# arm <label> <plant-command> <phrase the control must print>
arm() {
  local label="$1" plant="$2" want="$3"
  TOTAL=$((TOTAL + 1))

  restore
  eval "$plant"
  if git -C "$REPO" diff --quiet -- "$S"; then
    echo "::error::BROKEN CONTROL $label - THE PLANT DID NOT LAND. A sed that"
    echo "         matches nothing succeeds silently, and the arm below would"
    echo "         then measure an unplanted harness and pass for no reason."
    restore
    return
  fi
  # STAGE THE PLANT. Not to defeat a guard any more - the opt-in below does
  # that openly - but because the control's own post-restore check compares
  # the worktree to the INDEX. With the plant staged, "restored" means "back
  # to the planted state", which is the correct post-state while this probe
  # is driving. Unstaged, that check fails every arm with exit 9, which is
  # exactly what happened when the staging was first removed.
  git -C "$REPO" add -- "$S"

  local out rc
  out=$(cd "$REPO" && ROW_FLOOR_CONTROL_ALLOW_PLANTED=1 \
          bash "$CONTROL" "$TARGET" 2>&1); rc=$?
  restore

  if [ "$rc" -eq 0 ]; then
    echo "::error::BROKEN CONTROL $label - the control exited 0 with the defect"
    echo "         planted. It is not reading the canonical line at all."
  elif printf '%s\n' "$out" | grep -qF "$want"; then
    FIRED=$((FIRED + 1))
    echo "  FIRED  $label"
    echo "         exit $rc, and it said so:"
    printf '%s\n' "$out" | grep -F "$want" | sed 's/^/           /'
  else
    echo "::error::BROKEN CONTROL $label - the control went red (exit $rc) but"
    echo "         not for the planted reason. It never printed: $want"
    echo "         A red for the wrong reason sends the next reader to the"
    echo "         wrong place, which is the defect one layer up."
    printf '%s\n' "$out" | tail -12 | sed 's/^/         | /'
  fi
}

echo "########## PLANTED DEFECTS - the control must go red, for the right reason"

# P1: the harness stops reporting at all. Its exit code and its prose are
# untouched; only the canonical line changes, from breach to refused.
arm "P1 the harness's report is amputated, so the line says refused" \
    "sed -i 's/^harness_result_ran /: harness_result_ran /' \"\$S\"" \
    "wanted breach"

# P2: the harness reports a row count that is not the one it measured. This is
# the property an impossible-floor run cannot reach, and the one that was
# actually broken on check-u15-gate-amputation.sh.
arm "P2 the harness reports a row count it did not measure" \
    "sed -i 's/^harness_result_ran \"\$TOTAL\" \"\$ROW_FLOOR\"/harness_result_ran 99 \"\$ROW_FLOOR\"/' \"\$S\"" \
    "does not track"

# P3: the harness reports a floor that is not the floor it compared against.
arm "P3 the harness reports a floor its source does not declare" \
    "sed -i 's/^harness_result_ran \"\$TOTAL\" \"\$ROW_FLOOR\"/harness_result_ran \"\$TOTAL\" 4/' \"\$S\"" \
    "are not the same value"

# P4: the line disappears entirely - the shared file is not sourced. Before
# #107 this rendered as a harness whose prose the control simply did not
# recognise; it must now be an explicit "printed NO line", because a missing
# verdict and a failed verdict are different failures.
arm "P4 the shared file is not sourced, so no line is printed at all" \
    "sed -i '\\|^\\. \"\$(dirname \"\${BASH_SOURCE\\[0\\]}\")/lib/harness-result\\.sh\"\$|d' \"\$S\"" \
    "printed NO"

echo
echo "$FIRED/$TOTAL planted defects were caught."
git -C "$REPO" diff --quiet -- "$S" \
  && echo "restored: $TARGET is identical to HEAD" \
  || { echo "::error::RESTORE FAILED - $S still differs"; exit 3; }
if [ "$TOTAL" -eq 0 ]; then
  echo "::error::this probe holds ZERO arms; a green from it means nothing"
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL caught. Each survivor is a defect the rewritten"
  echo "         control cannot see, which is what its predecessor's three prose"
  echo "         literals were for."
  exit 1
fi
