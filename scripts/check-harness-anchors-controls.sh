#!/usr/bin/env bash
# AMPUTATION harness for scripts/check-harness-anchors.py.
#
# The static anchor checker exists to notice that a harness stopped checking.
# Its own failure mode is the one it hunts: it reports OK, and it reports OK
# because a parser shape stopped matching rather than because the anchors are
# sound. A checker that has only ever passed is indistinguishable from one that
# cannot fail, so every row here DELETES one of its behaviours and requires it
# to stop finding a defect it finds intact.
#
# Rows 1-2 are POSITIVE CONTROLS on the checker's subject: break the real source
# and require exit 1. Rows 3+ are amputations of the checker: break the source
# AND delete the rule that notices, then require exit 0. A row that stays red
# after its rule is deleted is a row whose rule was never what found the defect.
#
# EVERYTHING RUNS IN A COPY. This harness never edits the working tree - two
# commits on this project captured an amputated src/ because a harness was
# killed mid-run, and `git status` after a run is the check that catches it.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER_REL="scripts/check-harness-anchors.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export PYTHONDONTWRITEBYTECODE=1

FIRED=0
TOTAL=0

# A pristine copy of everything the checker reads: the harnesses and the files
# they anchor into. Rebuilt per row, so no row can see another row's edits.
build_tree() {
  local dest="$1"
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -R "$REPO/scripts" "$dest/scripts"
  cp -R "$REPO/src" "$dest/src"
}

# break_source <tree> - reflow a comment INSIDE a live anchor, which is exactly
# what B49b did to U3's M8. Derived from the checker's own output rather than
# hard-coded: the first shell-arg anchor in U3's amputation harness that spans
# more than one line is the subject, so this control cannot rot into pointing at
# a row that no longer exists.
break_source() {
  local tree="$1"
  python3 - "$tree" <<'PY'
import pathlib, sys
tree = pathlib.Path(sys.argv[1])
target = tree / "src/fast_mcp_jobvite/audit.py"
s = target.read_text()
old = "        return ATTRIBUTION_UNAVAILABLE if self.transport is Transport.STDIO else None"
if s.count(old) != 1:
    print(f"CONTROL SETUP FAILED: the subject line is not unique ({s.count(old)} hits)")
    sys.exit(3)
# The same shape a reflow produces: the statement wrapped across two lines. The
# code is equivalent; only the TEXT the anchor matches on has changed.
new = ("        return (\n"
       "            ATTRIBUTION_UNAVAILABLE if self.transport is Transport.STDIO else None\n"
       "        )")
target.write_text(s.replace(old, new))
PY
}

# amputate_checker <tree> <old> <new> - delete one rule from the checker.
amputate_checker() {
  local tree="$1" old="$2" new="$3"
  OLD="$old" NEW="$new" FILE="$tree/$CHECKER_REL" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
if s.count(old) != 1:
    print(f"    ANCHOR NOT UNIQUE ({s.count(old)} hits) in the checker", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
}

# row <label> <want_rc> <break?> [old new] - run the checker in a fresh tree.
row() {
  local label="$1" want="$2" dobreak="$3"; shift 3
  TOTAL=$((TOTAL + 1))
  local tree="$WORK/t$TOTAL"
  build_tree "$tree"

  if [ "$dobreak" = yes ]; then
    break_source "$tree" || { echo "  $label: SETUP FAILED"; return; }
  fi

  if [ "$#" -eq 2 ]; then
    local backup="$WORK/backup$TOTAL"
    cp "$tree/$CHECKER_REL" "$backup"
    if ! amputate_checker "$tree" "$1" "$2"; then
      echo "  $label: DID NOT LAND - the checker anchor moved. Fix this harness."
      return
    fi
    # LANDED? `cmp` against the backup, never `git diff`: the copy is UNTRACKED,
    # and `git diff` reports NO DIFFERENCE for an untracked file whatever it
    # contains. Four rows once reported "did not land" when all four had.
    if cmp -s "$tree/$CHECKER_REL" "$backup"; then
      echo "  $label: DID NOT LAND (file unchanged) - this row proves nothing"
      return
    fi
  fi

  local out rc
  out=$(cd "$tree" && python3 "$CHECKER_REL" 2>&1); rc=$?
  if [ "$rc" -eq "$want" ]; then
    FIRED=$((FIRED + 1))
    echo "  FIRED    $label (exit $rc, wanted $want)"
  else
    echo "  SURVIVED $label (exit $rc, wanted $want)"
    printf '%s\n' "$out" | tail -4 | sed 's/^/      /'
  fi
}

echo "########## POSITIVE CONTROLS - the checker's subject, intact checker"

row "P1 an intact tree passes" 0 no
row "P2 a reflowed line inside a live anchor is caught" 1 yes

echo
echo "########## AMPUTATIONS - the same broken tree, one rule deleted per row"

# The uniqueness rule itself. Without it nothing compares the hit count at all.
row "A1 the hit-count comparison is deleted" 0 yes \
  'if hits != 1:' \
  'if False:'

# `!= 1` weakened to `> 1`: catches the ambiguous anchor and MISSES the stale
# one. This is the specific half that B49b's failure needed.
row "A2 zero hits is no longer a failure, only ambiguity is" 0 yes \
  'if hits != 1:' \
  'if hits > 1:'

# The shell-arg shape, which is where the reflowed anchor lives.
row "A3 the shell-helper shape parses nothing" 0 yes \
  '    carriers = {h: pb for h, pb in sigs.items() if "old" in pb[0]}' \
  '    carriers = {}'

# The verdict. If the exit code is not derived from the findings, printing them
# is decoration - the same defect as a gate that greps and ignores the result.
row "A4 findings are printed but the exit code ignores them" 0 yes \
  '    if stale:
        print(f"FAIL: {len(stale)} of {total} anchors do not resolve uniquely.")
        return 1' \
  '    if stale:
        print(f"FAIL: {len(stale)} of {total} anchors do not resolve uniquely.")'

echo
echo "########## FLOOR - a shape can vanish with every remaining anchor sound"

# A2-A4 break the tree; this one does NOT. It deletes a whole parser shape from
# an INTACT tree, so every anchor that still parses resolves perfectly and the
# checker reports OK on a fraction of its coverage. Only the floor sees it.
TOTAL=$((TOTAL + 1))
tree="$WORK/floor"
build_tree "$tree"
cp "$tree/$CHECKER_REL" "$WORK/floor-backup"
if amputate_checker "$tree" \
     '    c_anchors, c_seen = _shape_c(path.name, src, variables)' \
     '    c_anchors, c_seen = ([], 0)' \
   && ! cmp -s "$tree/$CHECKER_REL" "$WORK/floor-backup"; then
  before=$(cd "$REPO" && python3 "$CHECKER_REL" --quiet 2>&1)
  unfloored=$(cd "$tree" && python3 "$CHECKER_REL" 2>&1); un_rc=$?
  floored=$(cd "$tree" && python3 "$CHECKER_REL" --floor 154 2>&1); fl_rc=$?
  if [ "$un_rc" -eq 0 ] && [ "$fl_rc" -eq 1 ]; then
    FIRED=$((FIRED + 1))
    echo "  FIRED    F1 a deleted shape passes WITHOUT the floor (exit 0) and fails WITH it (exit 1)"
    printf '%s\n' "$unfloored" | grep -E '^(anchors resolved|OK)' | sed 's/^/      no floor:   /'
    printf '%s\n' "$floored" | grep -E '^FAIL' | sed 's/^/      with floor: /'
    printf '%s\n' "$before" | sed 's/^/      intact:     /'
  else
    echo "  SURVIVED F1 (no-floor exit $un_rc wanted 0, floored exit $fl_rc wanted 1)"
  fi
else
  echo "  F1: DID NOT LAND - the shape-C call site moved. Fix this harness."
fi

echo
echo "$FIRED/$TOTAL controls fired."

if [ "$TOTAL" -eq 0 ]; then
  echo "::error::the harness holds zero rows; a green from it means nothing"
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. A SURVIVOR names a rule that is not what"
  echo "         finds the defect it claims to find. Read it before trusting it."
  exit 1
fi
