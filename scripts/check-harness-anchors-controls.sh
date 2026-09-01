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

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER_REL="scripts/check-harness-anchors.py"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

export PYTHONDONTWRITEBYTECODE=1

FIRED=0
TOTAL=0

# A pristine copy of everything the checker reads. Rebuilt per row, so no row
# can see another row's edits.
#
# THE UNIT OF STAGING IS THE TREE, not a named pair of directories. This copied
# `scripts` and `src` and nothing else, which was true of what the anchors
# pointed at on the day it was written. The moment the checker learned to read
# `sed -i`, U0's rows arrived pointing at `.env.example`, `.gitignore`,
# `pyproject.toml` and `tests/conftest.py` - none of them staged - and five of
# seven rows went red reporting "target file does not exist" about files that
# exist. The failure was in this function, not in anything under test.
#
# That is the same defect check-u0-test-controls.sh has now hit FIVE times and
# whose comment is three paragraphs long: a hand-kept list of paths selects for
# the path nobody thought of. `git ls-files` is the authority, so the next
# anchor into a new file needs no edit here.
build_tree() {
  local dest="$1"
  rm -rf "$dest"
  mkdir -p "$dest"
  local n
  n=$(cd "$REPO" && git ls-files | wc -l)
  [ "$n" -gt 0 ] || { echo "  STAGING CONTROL: git ls-files returned nothing"; return 1; }
  (cd "$REPO" && git ls-files -z | tar --null -cf - -T -) | (cd "$dest" && tar -xf -) || return 1
  # Positive control on the staging itself: a copy that silently contains
  # nothing produces row failures that read exactly like real findings.
  local probe
  for probe in scripts/check-harness-anchors.py src pyproject.toml; do
    [ -e "$dest/$probe" ] || { echo "  STAGING CONTROL: $probe missing from the copy"; return 1; }
  done
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

# break_sed_anchor <tree> - invalidate one of U0's `sed -i` anchors in the copy.
#
# The SUBJECT IS DERIVED, never named here. The checker itself is imported and
# asked which sed anchors it reads; the first one is taken, the text it matches
# in its target file is found, and a character is inserted into the middle of
# THAT MATCH. So the mutation is guaranteed to invalidate the anchor whatever
# the anchor currently is, and this row cannot rot into breaking a pattern no
# row uses any more - which is exactly how the first version of
# probe-bash-namespace-amputation.sh went vacuous within the hour.
#
# Asking the checker to pick the subject is safe for a POSITIVE control: it
# chooses WHERE to break the tree, and must then independently report the break.
# A checker that picks a row and then cannot see the damage still fails here.
break_sed_anchor() {
  local tree="$1"
  python3 - "$tree" <<'PY'
import importlib.util, pathlib, re, sys

tree = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    "anchors", tree / "scripts/check-harness-anchors.py"
)
mod = importlib.util.module_from_spec(spec)
# REGISTERED BEFORE EXEC, not after. `@dataclass` resolves its annotations
# through `sys.modules[cls.__module__]`, so executing this module unregistered
# dies inside dataclasses.py with an AttributeError about NoneType - nothing
# that names the real cause. Measured, not anticipated.
sys.modules["anchors"] = mod
spec.loader.exec_module(mod)

picked = None
for h in sorted((tree / "scripts").glob("check-*.sh")):
    if h.name.startswith("check-harness-anchors"):
        continue
    for a in mod.collect(h)[0]:
        if a.shape == "sed-bre":
            picked = a
            break
    if picked:
        break

if picked is None:
    print("CONTROL SETUP FAILED: the checker reads no `sed -i` anchors at all")
    sys.exit(3)

target = tree / picked.target
text = target.read_text()
hits = list(re.finditer(picked.text, text, re.M))
if len(hits) != 1:
    print(f"CONTROL SETUP FAILED: {picked.target} has {len(hits)} hits, wanted 1")
    sys.exit(3)
m = hits[0]
matched = m.group(0)
mangled = matched[: len(matched) // 2] + "ZZ" + matched[len(matched) // 2 :]
target.write_text(text[: m.start()] + mangled + text[m.end() :])
if len(re.findall(picked.text, target.read_text(), re.M)) != 0:
    print("CONTROL SETUP FAILED: the anchor still matches after the mutation")
    sys.exit(3)
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
  build_tree "$tree" || { echo "  $label: STAGING FAILED"; return; }

  case "$dobreak" in
    yes) break_source "$tree" || { echo "  $label: SETUP FAILED"; return; } ;;
    sed) break_sed_anchor "$tree" || { echo "  $label: SETUP FAILED"; return; } ;;
  esac

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

# Shape D's subject. U0's rows are sed PATTERNS, not string literals, and until
# the checker learned to read them all eleven were invisible - it named the
# harness as UNREAD rather than counting it clean, which is the only reason this
# was a task and not an incident.
row "P3 an invalidated sed -i anchor is caught" 1 sed

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

# The sed shape, which is where the invalidated pattern lives. Without this row
# shape D is a rule that has never been shown to be what finds anything.
row "A5 the sed -i shape parses nothing" 0 sed \
  '    d_anchors, d_seen = _shape_d(path.name, src, variables)' \
  '    d_anchors, d_seen = ([], 0)'

echo
echo "########## FLOOR - a shape can vanish with every remaining anchor sound"

# A2-A4 break the tree; this one does NOT. It deletes a whole parser shape from
# an INTACT tree, so every anchor that still parses resolves perfectly and the
# checker reports OK on a fraction of its coverage. Only the floor sees it.
TOTAL=$((TOTAL + 1))
tree="$WORK/floor"
build_tree "$tree" || echo "  F1: STAGING FAILED"
cp "$tree/$CHECKER_REL" "$WORK/floor-backup"
if amputate_checker "$tree" \
     '    c_anchors, c_seen = _shape_c(path.name, src, variables)' \
     '    c_anchors, c_seen = ([], 0)' \
   && ! cmp -s "$tree/$CHECKER_REL" "$WORK/floor-backup"; then
  # NOT `--quiet`: that flag suppresses the `anchors resolved:` line, which is
  # the line the floor below is read from. The first version of this derivation
  # kept it and reported "could not read the intact anchor count" - loudly,
  # which is the only reason it is not still here silently reading an empty
  # string.
  before=$(cd "$REPO" && python3 "$CHECKER_REL" 2>&1)
  # THE FLOOR IS DERIVED, NEVER RETYPED. This line read `--floor 154`, a second
  # copy of a number whose one home is ci.yml - in the very harness that exists
  # to prove the floor works. Adding eleven anchors would have left it passing
  # for the wrong reason: 154 is below the new intact count, so the row would
  # have gone green whether or not the deleted shape mattered. It is now read
  # back out of the intact run above, so it cannot disagree with the tree.
  intact=$(printf '%s\n' "$before" | sed -n 's/^anchors resolved: //p')
  case "$intact" in
    ''|*[!0-9]*) intact=0 ;;
  esac
  unfloored=$(cd "$tree" && python3 "$CHECKER_REL" 2>&1); un_rc=$?
  floored=$(cd "$tree" && python3 "$CHECKER_REL" --floor "$intact" 2>&1); fl_rc=$?
  if [ "$intact" -eq 0 ]; then
    echo "  SURVIVED F1: the intact anchor count could not be read, so there is"
    echo "           no floor to test with. This row proves nothing."
  elif [ "$un_rc" -eq 0 ] && [ "$fl_rc" -eq 1 ]; then
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
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally fired "$FIRED" "$TOTAL"

# THE ROW FLOOR. `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness
# whose rows were deleted - or whose rows stopped being counted - reports
# fully green. `TOTAL -eq 0` catches only the total case; PARTIAL deletion
# is the realistic shape. DERIVED: this harness printed "9/9 controls
# fired." at 20e71ed. Lowering this number is a visible diff that has to
# be defended.
ROW_FLOOR=9
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "::error::$TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. A SURVIVOR names a rule that is not what"
  echo "         finds the defect it claims to find. Read it before trusting it."
  exit 1
fi
