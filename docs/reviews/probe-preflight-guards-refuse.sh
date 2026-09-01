#!/usr/bin/env bash
# ONE ARM PER GUARD: stage a change to the harness's own subject file and
# assert the harness REFUSES. Before the widening, every one of these
# passed the guard and went on to mutate a tree nobody had declared.
#
# WHY STAGED AND NOT MERELY MODIFIED: `git diff` compares the worktree to
# the INDEX. A modify-then-`git add` leaves worktree == index, so the old
# guard read CLEAN. The arm below reproduces exactly that state with
# `git add` followed by `git checkout-index -f`, and the OLD incantation is
# printed beside the new one so the difference is visible, not asserted.
#
# NOT A KILL TEST. Nothing is signalled; each harness is expected to exit
# at its own guard within seconds. Every staged edit is unstaged and
# checked out again, and the tree is asserted clean at the end.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$REPO/.." && pwd)"
cd "$REPO" || exit 3

PASS=0
FAIL=0

if [ -n "$(git status --porcelain)" ]; then
  echo "ABORT: the tree is dirty; this probe stages edits and would take"
  echo "       someone else's work with it. Commit or stash first."
  exit 3
fi

# arm <harness> <subject file> <expected exit>
arm() {
  local harness="$1" subject="$2" want="$3"
  local out rc

  if [ ! -f "$harness" ]; then
    echo "  BROKEN ARM: $harness does not exist - prove the path resolves"
    FAIL=$((FAIL + 1))
    return
  fi
  if [ ! -f "$subject" ]; then
    echo "  BROKEN ARM: $subject does not exist. A guard tested against a"
    echo "              path that resolves to nothing reads clean-empty and"
    echo "              this arm would pass for no reason."
    FAIL=$((FAIL + 1))
    return
  fi

  printf '\n# preflight-guard control, staged then removed\n' >> "$subject"
  git add -- "$subject"
  git checkout-index -f -- "$subject"

  # PROVE THE STATE IS THE ONE THAT DEFEATED THE OLD GUARD.
  git diff --quiet -- "$subject"
  local old_rc=$?
  local porcelain
  porcelain="$(git status --porcelain -- "$subject")"

  out=$(timeout 60 bash "$harness" 2>&1)
  rc=$?

  git restore --staged -- "$subject" 2>/dev/null
  git checkout -- "$subject"

  if [ "$old_rc" -ne 0 ]; then
    echo "  BROKEN ARM $harness: the old incantation ALREADY saw this state,"
    echo "              so the arm is not reproducing the defect."
    FAIL=$((FAIL + 1))
    return
  fi
  if [ -z "$porcelain" ]; then
    echo "  BROKEN ARM $harness: porcelain saw nothing either; nothing staged."
    FAIL=$((FAIL + 1))
    return
  fi
  if [ "$rc" -eq "$want" ]; then
    echo "  REFUSED  $harness  exit=$rc  (old 'git diff --quiet' said CLEAN)"
    PASS=$((PASS + 1))
  else
    echo "  DID NOT REFUSE  $harness  exit=$rc, wanted $want"
    printf '%s\n' "$out" | head -4 | sed 's/^/      /'
    FAIL=$((FAIL + 1))
  fi
}

echo "########## A staged subject must be REFUSED by every guard"
arm scripts/check-u3-audit-controls.sh          src/fast_mcp_jobvite/audit.py 3
arm scripts/check-u3-audit-amputation.sh        src/fast_mcp_jobvite/audit.py 3
arm scripts/check-u4-client-controls.sh         src/fast_mcp_jobvite/services/jobvite_client.py 3
arm scripts/check-u4-client-amputation.sh       src/fast_mcp_jobvite/services/jobvite_client.py 3
arm docs/reviews/check-row-floor-control.sh     scripts/check-u15-gate-amputation.sh 3
arm docs/reviews/probe-audit-row-container.sh   src/fast_mcp_jobvite/tools/candidates.py 3

echo
echo "ROWS: $((PASS + FAIL))   REFUSED: $PASS   FAILED: $FAIL"

if [ -n "$(git status --porcelain)" ]; then
  echo "TREE LEFT DIRTY - a restore failed. STOPPING."
  git status --porcelain
  exit 3
fi
echo "TREE RESTORED CLEAN"

[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge 6 ] || { echo "FEWER ROWS THAN EXPECTED - did an arm silently skip?"; exit 1; }
echo "All $PASS guards refuse a STAGED subject."
