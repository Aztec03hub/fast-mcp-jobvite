#!/usr/bin/env bash
# CONTROLS for the run state file `scripts/ci-harness-gate.sh` now writes (#131).
#
# WHAT IT IS FOR. `docs/reviews/restore-stranded-mutation.sh` repairs a mutation
# a killed harness left behind, and it reads a STATE FILE rather than
# `git status` - because `git status` can say the tree is dirty and can never
# say whether that dirt has an OWNER. Its own header named the gap: only
# `probe-harness-exit-codes.sh` wrote that state, so every harness run through
# the shared gate was invisible to it. The gate writes it now, and these are the
# arms that say so.
#
# EVERY ARM RUNS IN A SCRATCH GIT REPOSITORY, built here and thrown away. That
# is not tidiness: the gate's first condition is that the tree be CLEAN, and the
# real tree is dirty whenever anyone is working, so an arm run against it would
# take the dirty-tree branch every time and prove nothing about the other two.
# A scratch repo is the only place the clean path can be exercised at all.
#
# It also means no arm can strand a mutation in the real tree while testing the
# tool that repairs stranded mutations, which would be its own joke.
set -uo pipefail

# shellcheck source=lib/harness-result.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/harness-result.sh"

REAL="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

FIRED=0
TOTAL=0

# A scratch repository holding only what the gate reads: the gate itself, the
# two libraries it sources, and whatever stub harness an arm writes.
SCRATCH="$WORK/repo"
mkdir -p "$SCRATCH/scripts/lib" "$SCRATCH/docs/reviews/lib"
cp "$REAL/scripts/ci-harness-gate.sh" "$SCRATCH/scripts/"
cp "$REAL/scripts/lib/harness-result.sh" "$SCRATCH/scripts/lib/"
cp "$REAL/docs/reviews/lib/harness-state.sh" "$SCRATCH/docs/reviews/lib/"
git -C "$SCRATCH" init -q
git -C "$SCRATCH" config user.email probe@example.invalid
git -C "$SCRATCH" config user.name probe
# A tracked file for a stub to mutate. It has to be TRACKED or an edit to it
# would show as `??` rather than ` M`, and the gate's tree comparison would
# still see a change but the restorer would have nothing to restore it to.
printf 'original\n' >"$SCRATCH/subject.txt"
# A SECOND tracked file, and the reason is a real trap. `git status --porcelain`
# reports a STATUS LINE, not content: a stub that rewrites the same file a
# person already edited leaves the porcelain output BYTE-IDENTICAL, so the
# gate's tree comparison sees nothing appear and clears the state. ARM 5 needs
# a strand that APPEARS beside the human's edit, which means a different file.
printf 'original\n' >"$SCRATCH/other.txt"

# The state file is pinned into the scratch dir by the env override the library
# honours, so an arm can never read or clobber the real one.
export HARNESS_STATE_FILE="$WORK/probe.state"

# stub <name> <body>
stub() {
  local path="$SCRATCH/scripts/$1"
  printf '%s\n' "$2" >"$path"
  chmod +x "$path"
  git -C "$SCRATCH" add -A
  git -C "$SCRATCH" commit -qm "stub $1"
}

# A stub that emits the canonical line the gate requires, then does what its
# caller asked. `fired=1/1` satisfies --controls-fired.
#
# THE VOCABULARY LINE IS NOT DECORATION. The gate REFUSES a harness whose source
# contains none of its anchor-failure phrases - a harness that cannot report a
# stale anchor cannot be gated on one - and it refuses BEFORE running anything.
# Without this line every arm below took that refusal path, and the two arms
# asserting the ABSENCE of a NOTE passed vacuously: no NOTE because no run.
# That is exactly the failure this file exists to catch, found in its own first
# execution.
STUB_HEAD='#!/usr/bin/env bash
# ANCHOR NOT UNIQUE - never printed; present so the gate accepts this stub.
echo "  PASS  stub row"
echo "1/1 controls fired."'
# The canonical line must NAME THE HARNESS. The gate reads the tally off the
# line naming the script it ran, so a stub hard-coding some other name is
# refused - correctly, and it refused this one on its first execution.
STUB_TAIL='echo "HARNESS-RESULT name=$(basename "$0") rows=1 floor=1 fired=1/1 status=ok"'

row() {
  local name="$1" want_present="$2"
  TOTAL=$((TOTAL + 1))
  local present="absent"
  [ -f "$HARNESS_STATE_FILE" ] && present="present"
  if [ "$present" = "$want_present" ]; then
    FIRED=$((FIRED + 1))
    echo "  PASS  $name: state file $present (want $want_present)"
  else
    echo "::error::  FAIL  $name: state file $present (want $want_present)"
  fi
}

run_gate() {
  bash "$SCRATCH/scripts/ci-harness-gate.sh" "$1" --controls-fired 2>&1
}

# WHY ARM 1'S "ABSENT" IS NOT VACUOUS, since an absent file is exactly what you
# also get from a gate that never writes one. Two other assertions close that:
# ARM 1 requires NO skip NOTE, so the write branch was the one taken, and ARM 2
# shows the file PRESENT after a run through the same code path. Written, then
# cleared - not never written.
echo "ARM 1 - a clean tree and a well-behaved harness:"
stub "check-stub-clean.sh" "$STUB_HEAD
$STUB_TAIL"
out=$(run_gate check-stub-clean.sh); rc=$?
row "CLEAN     the state file is cleared after a clean run" absent
TOTAL=$((TOTAL + 1))
if [ "$rc" -eq 0 ]; then
  FIRED=$((FIRED + 1))
  echo "  PASS  CLEAN     the gate still passed the run: exit 0"
else
  echo "::error::  FAIL  CLEAN     the gate exited $rc on a healthy stub"
  printf '%s\n' "$out" | sed 's/^/          /'
fi
TOTAL=$((TOTAL + 1))
if ! grep -q "^NOTE:" <<<"$out"; then
  FIRED=$((FIRED + 1))
  echo "  PASS  CLEAN     no NOTE, so state WAS recorded rather than skipped"
else
  echo "::error::  FAIL  CLEAN     the gate printed a skip NOTE on a clean tree:"
  grep "^NOTE:" <<<"$out" | sed 's/^/          /'
fi

echo "ARM 2 - a harness that strands a mutation:"
stub "check-stub-strands.sh" "$STUB_HEAD
printf 'MUTATED\\n' > \"\$(dirname \"\$0\")/../subject.txt\"
$STUB_TAIL"
stub "check-stub-strands-other.sh" "$STUB_HEAD
printf 'MUTATED\\n' > \"\$(dirname \"\$0\")/../other.txt\"
$STUB_TAIL"
out=$(run_gate check-stub-strands.sh); rc=$?
row "STRANDED  the state file SURVIVES a tree that did not come back" present
TOTAL=$((TOTAL + 1))
if [ "$rc" -ne 0 ]; then
  FIRED=$((FIRED + 1))
  echo "  PASS  STRANDED  the gate failed the run: exit $rc"
else
  echo "::error::  FAIL  STRANDED  the gate exited 0 on a stranded mutation"
fi
# Put the scratch subject back so later arms start from a clean tree. Written
# with the recorded bytes, never `git checkout --`, which is this project's
# standing rule about not making the index a participant.
printf 'original\n' >"$SCRATCH/subject.txt"
rm -f "$HARNESS_STATE_FILE"

echo "ARM 3 - an existing state file is another run's evidence:"
printf 'repo=%s\nharness=someone-else.sh\ncommit=deadbeef\npid=1\n' "$SCRATCH" \
  >"$HARNESS_STATE_FILE"
before=$(cat "$HARNESS_STATE_FILE")
out=$(run_gate check-stub-clean.sh)
TOTAL=$((TOTAL + 1))
if [ "$(cat "$HARNESS_STATE_FILE" 2>/dev/null)" = "$before" ]; then
  FIRED=$((FIRED + 1))
  echo "  PASS  FOREIGN   the existing state file is untouched"
else
  echo "::error::  FAIL  FOREIGN   the gate overwrote or deleted another run's state"
fi
TOTAL=$((TOTAL + 1))
if grep -q "already exists" <<<"$out"; then
  FIRED=$((FIRED + 1))
  echo "  PASS  FOREIGN   and it SAYS the run is uncovered rather than going quiet"
else
  echo "::error::  FAIL  FOREIGN   the gate skipped silently, which is the shape"
  echo "::error::            that made 119 red mirror runs unreadable"
fi
rm -f "$HARNESS_STATE_FILE"

# ARM 4's "absent" assertion WAS VACUOUS AND R18-M3 CAUGHT IT. With the
# dirty-tree branch amputated, the gate wrote the state, ran, and cleared it -
# so the file was absent for the WRONG REASON and the arm passed on the mutant
# it exists to catch. Only its sibling NOTE assertion failed.
#
# THE FIX IS THE STUB, NOT THE ASSERTION. Paired with a harness that STRANDS,
# "absent" becomes discriminating: correct code records nothing on a dirty tree
# so there is nothing to leave, while the mutant records state, fails to get
# the tree back, and LEAVES THE FILE. ARM 5 amputates the branch and requires
# exactly that, so this file now checks its own vacuity instead of asserting
# it is fine.
echo "ARM 4 - a dirty tree records nothing, even when the harness strands:"
printf 'edited by a person\n' >>"$SCRATCH/subject.txt"
out=$(run_gate check-stub-strands-other.sh)
row "DIRTY     nothing recorded on a tree that was already dirty" absent
TOTAL=$((TOTAL + 1))
if grep -q "already dirty" <<<"$out"; then
  FIRED=$((FIRED + 1))
  echo "  PASS  DIRTY     and the reason is printed, not inferred"
else
  echo "::error::  FAIL  DIRTY     the gate recorded nothing and did not say why"
fi
printf 'original\n' >"$SCRATCH/subject.txt"
printf 'original\n' >"$SCRATCH/other.txt"
rm -f "$HARNESS_STATE_FILE"

echo "ARM 5 - AMPUTATION: delete the dirty-tree branch, ARM 4 must stop holding:"
AMPUTATED="$SCRATCH/scripts/ci-harness-gate-amputated.sh"
python3 - "$SCRATCH/scripts/ci-harness-gate.sh" "$AMPUTATED" <<'PY'
import sys
import pathlib

src = pathlib.Path(sys.argv[1]).read_text()
anchor = 'elif [ -n "$tree_before" ]; then'
if src.count(anchor) != 1:
    print(f"ANCHOR NOT UNIQUE: matched {src.count(anchor)} times")
    raise SystemExit(1)
pathlib.Path(sys.argv[2]).write_text(src.replace(anchor, "elif false; then"))
PY
printf 'edited by a person\n' >>"$SCRATCH/subject.txt"
bash "$AMPUTATED" check-stub-strands-other.sh --controls-fired >/dev/null 2>&1
TOTAL=$((TOTAL + 1))
if [ -f "$HARNESS_STATE_FILE" ]; then
  FIRED=$((FIRED + 1))
  echo "  PASS  AMP-DIRTY without the dirty-tree branch the state file IS written"
else
  echo "::error::  FAIL  AMP-DIRTY the amputated gate still recorded nothing, so"
  echo "::error::            ARM 4's 'absent' proves nothing about that branch"
fi
rm -f "$AMPUTATED" "$HARNESS_STATE_FILE"
printf 'original\n' >"$SCRATCH/subject.txt"
printf 'original\n' >"$SCRATCH/other.txt"
git -C "$SCRATCH" checkout -q -- subject.txt other.txt

# THE ROW FLOOR. `FIRED -ne TOTAL` is satisfied by 0 == 0. DERIVED from the
# calls above at the commit that adds them: five arms, ten assertions - the
# fifth being R18-M3's amputation of the branch ARM 4 depends on.
ROW_FLOOR=10
harness_result_tally fired "$FIRED" "$TOTAL"
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "::error::$TOTAL/$ROW_FLOOR ROWS - THE PROBE LOST ROWS."
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. Read WHICH row failed."
  exit 1
fi
echo "$FIRED/$TOTAL controls fired."
