#!/usr/bin/env bash
# POSITIVE CONTROLS for the canonical result line. Task #107.
#
# WHY A SECOND LAYER. `docs/reviews/check-harness-result.sh` reads SOURCE: it can
# prove that every script sources the shared file and chains the emitter into its
# trap, and it cannot prove that a single line is ever printed. A static checker
# that says "wired" about a mechanism nobody has watched run is the shape this
# repository has already been bitten by - `check-u15-gate-amputation.sh` had no
# row counter at all and printed the same closing sentence for months.
#
# So every row here RUNS A REAL ARTIFACT from `scripts/` and reads ITS output and
# ITS exit code. No stub stands in for a harness, because a stub is a claim about
# a harness rather than a measurement of one.
#
# THE THREE PROPERTIES BEING PROVED, and they are separable:
#   1. an ABORT reports `refused` - not a pass, not silence, not a crash;
#   2. a completing run reports `ok`/`breach` matching its real exit code, with
#      the rows and floor it actually measured;
#   3. removing the harness's `harness_result_ran` call turns `ok` back into
#      `refused` - so the field tracks the harness, not the exit code alone.
#      That is the amputation arm: without it, rows 1 and 2 are consistent with
#      a line that is simply printf'd from the exit status and means nothing.
#
# `-e` deliberately omitted: every row here reads the exit code of a command
# EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIRED=0
TOTAL=0

# This file is an instrument, not a harness, and does not source
# scripts/lib/harness-result.sh: it must never print a line a checker could
# mistake for one of its subjects'. It greps by `name=`, which is exactly the
# field that makes that distinction possible.

# row <label> <expected-name> <want-rc> <want-status> <want-rows|-> <want-floor|-> -- <command...>
#
# THE EXPECTED NAME IS AN ARGUMENT, not derived from the command. Deriving it
# from `$1` was the first version and it was wrong for every row invoked through
# `bash -c`: `basename "$1"` returned `bash`, so the grep looked for a line no
# artifact could ever print and EVERY row would have failed for the same reason,
# telling nobody anything about the subject.
row() {
  local label="$1" name="$2" want_rc="$3" want_status="$4" want_rows="$5" want_floor="$6"
  shift 7   # drops the six above plus the literal `--`
  TOTAL=$((TOTAL + 1))

  local out rc line got_status got_rows got_floor bad
  out=$(cd "$REPO" && "$@" 2>&1); rc=$?

  # THE LINE IS SELECTED BY `name=`, never by position. A gate echoes the output
  # of the harness it ran, so two HARNESS-RESULT lines can appear in one log and
  # `tail -1` would silently read the wrong one.
  line=$(printf '%s\n' "$out" | grep -E "^HARNESS-RESULT name=$name " | tail -1)

  bad=""
  if [ -z "$line" ]; then
    bad="printed NO HARNESS-RESULT line naming $(basename "$name")"
  else
    got_status=$(field "$line" status)
    got_rows=$(field "$line" rows)
    got_floor=$(field "$line" floor)
    [ "$rc" = "$want_rc" ]                                  || bad="$bad; exit $rc, wanted $want_rc"
    [ "$got_status" = "$want_status" ]                      || bad="$bad; status=$got_status, wanted $want_status"
    [ "$want_rows" = "-" ]  || [ "$got_rows" = "$want_rows" ]   || bad="$bad; rows=$got_rows, wanted $want_rows"
    [ "$want_floor" = "-" ] || [ "$got_floor" = "$want_floor" ] || bad="$bad; floor=$got_floor, wanted $want_floor"
  fi

  if [ -z "$bad" ]; then
    FIRED=$((FIRED + 1))
    echo "  FIRED  $label"
    echo "         $line   (exit $rc)"
  else
    echo "::error::BROKEN CONTROL $label"
    echo "         $bad"
    echo "         line was: ${line:-<none>}"
    printf '%s\n' "$out" | tail -8 | sed 's/^/         | /'
  fi
}

# Field extraction with NO shape list: the line is `key=value` pairs separated by
# spaces, so it is split on spaces and the key is looked up. Adding a field
# cannot break this, which is the entire difference from what it replaces.
field() {
  printf '%s\n' "$1" | tr ' ' '\n' | sed -n "s/^$2=//p"
}

echo "########## THE ABORT PATH - refused must not render as a pass"

# `check-suite-floor.sh` with no argument reaches its usage branch and exits 2
# WITHOUT ever running. This is a real refusal by a real artifact, and before
# #107 its output was indistinguishable from a harness that ran and passed
# except by reading the prose.
row "C1 a script that refuses its arguments reports refused" \
  check-suite-floor.sh 2 refused 0 0 -- bash "$REPO/scripts/check-suite-floor.sh"

# The gate refuses too, and it refuses BEFORE running anything - so its line is
# the only evidence that it did not silently do nothing.
row "C2 the gate with no harness named reports refused" \
  ci-harness-gate.sh 2 refused 0 0 -- bash "$REPO/scripts/ci-harness-gate.sh"

row "C3 the gate pointed at a harness that does not exist reports refused" \
  ci-harness-gate.sh 2 refused 0 0 -- bash "$REPO/scripts/ci-harness-gate.sh" no-such-harness.sh

echo
echo "########## THE COMPLETING PATH - ok and breach carry the real numbers"

row "C4 a floor met reports ok with the rows and floor it measured" \
  check-suite-floor.sh 0 ok 900 3 -- bash -c 'echo "900 passed" | bash '"$REPO"'/scripts/check-suite-floor.sh 3'

row "C5 a floor breached reports breach, and rows < floor is in the line" \
  check-suite-floor.sh 1 breach 1 5 -- bash -c 'echo "1 passed" | bash '"$REPO"'/scripts/check-suite-floor.sh 5'

echo
echo "########## THE INTERRUPTED PATH - a killed run must not read as a verdict"

# SIGTERM. A killed run measured NOTHING, and its silence must not read as a
# pass - that is the switched-off-vs-broken shape that let 119 consecutive CI
# failures go unread here. Neither row below touches `src/`: a mutation harness
# killed mid-row strands its mutation in the working tree, measured once when a
# killed check-u9-http-amputation.sh left every bearer-token check disabled.
TREE_BEFORE=$(git -C "$REPO" status --porcelain)

# C6 kills a script through the trap the SHARED FILE arms at source time.
# `check-suite-floor.sh` reads its input with `cat`, so a producer that never
# writes and never closes blocks it indefinitely - a deterministic interrupt,
# not a race against a timer. 124 is `timeout`'s own code for "I killed it".
row "C6 a SIGTERMed script reports refused from the source-armed trap" \
  check-suite-floor.sh 124 refused 0 0 -- \
  bash -c 'timeout --signal=TERM 2 bash '"$REPO"'/scripts/check-suite-floor.sh 5 < <(sleep 60)'

# C7 kills a script through a trap the HARNESS ITSELF sets, which REPLACED the
# armed one - bash has no trap stack, so this is a different code path and a
# separate claim. Without this row, C6 is consistent with the emitter being
# disarmed in all 27 scripts that set their own EXIT trap.
#
# The budget starts far below the harness's ~1s runtime and HALVES on a miss,
# because a fixed timer on a loaded machine is a race. Finishing inside the
# budget is reported as a BROKEN CONTROL, never passed over in silence.
TOTAL=$((TOTAL + 1))
trap_budget=0.3
trap_line=""
trap_rc=0
for _ in 1 2 3; do
  trap_out=$(cd "$REPO" && timeout --signal=TERM "$trap_budget" \
    bash "$REPO/scripts/check-harness-anchors-controls.sh" 2>&1)
  trap_rc=$?
  [ "$trap_rc" -eq 0 ] || break
  trap_budget=$(awk -v b="$trap_budget" 'BEGIN { print b / 2 }')
done
trap_line=$(printf '%s\n' "$trap_out" \
  | grep -E '^HARNESS-RESULT name=check-harness-anchors-controls\.sh ' | tail -1)
if [ "$trap_rc" -eq 0 ]; then
  echo "::error::BROKEN CONTROL C7 - the harness FINISHED inside every budget"
  echo "         tried, so nothing was interrupted and this row measured nothing."
elif [ "$(field "$trap_line" status)" = "refused" ]; then
  FIRED=$((FIRED + 1))
  echo "  FIRED  C7 a SIGTERMed harness reports refused from its OWN chained trap"
  echo "         $trap_line   (exit $trap_rc, budget ${trap_budget}s)"
else
  echo "::error::BROKEN CONTROL C7 - an interrupted harness that sets its own EXIT"
  echo "         trap did not report refused. line was: ${trap_line:-<none>}"
  echo "         exit $trap_rc. The harness's trap REPLACED the armed one without"
  echo "         chaining the emitter, and a run that measured nothing is silent."
fi

if [ "$TREE_BEFORE" != "$(git -C "$REPO" status --porcelain)" ]; then
  echo "::error::a SIGTERM row left the tree changed. STOP and read the diff"
  echo "         before committing anything from it."
  git -C "$REPO" status --porcelain
  exit 3
fi

echo
echo "########## THE AMPUTATION - remove the report and the line must notice"

# Without this row, C4 and C5 are equally consistent with a line derived from
# nothing but the exit code. Deleting the harness's own `harness_result_ran`
# call must turn `ok` into `refused` while the exit code stays 0.
S="$REPO/scripts/check-suite-floor.sh"
if ! git -C "$REPO" diff --quiet -- "$S"; then
  echo "::error::$S is already modified; refusing to measure someone else's tree"
  exit 3
fi
B=$(mktemp)
cp "$S" "$B"
trap 'cp "$B" "$S"; rm -f "$B"' EXIT

# The `:` builtin hands the whole logical command to bash's parser and does
# nothing with it, so the call does not run and the line count does not move.
if ! grep -q '^harness_result_ran ' "$S"; then
  echo "::error::no harness_result_ran call to amputate in check-suite-floor.sh -"
  echo "         the anchor moved, and a sed matching nothing succeeds silently."
  exit 3
fi
sed -i 's/^harness_result_ran /: harness_result_ran /' "$S"
if cmp -s "$S" "$B"; then
  echo "::error::THE AMPUTATION DID NOT LAND - the file is unchanged."
  exit 3
fi

TOTAL=$((TOTAL + 1))
amp_out=$(echo "900 passed" | bash "$S" 3 2>&1); amp_rc=$?
amp_line=$(printf '%s\n' "$amp_out" | grep -E '^HARNESS-RESULT name=check-suite-floor\.sh ' | tail -1)
if [ "$(field "$amp_line" status)" = "refused" ] && [ "$amp_rc" -eq 0 ]; then
  FIRED=$((FIRED + 1))
  echo "  FIRED  C8 with its report amputated the line says refused at exit 0"
  echo "         $amp_line   (exit $amp_rc)"
else
  echo "::error::BROKEN CONTROL C8 - amputating harness_result_ran did not change"
  echo "         the line. status=$(field "$amp_line" status) exit=$amp_rc."
  echo "         The line is then a restatement of the exit code and adds nothing."
fi

cp "$B" "$S"
cmp -s "$S" "$B" && echo "restored: byte-identical to the backup"
git -C "$REPO" diff --quiet -- "$S" \
  && echo "restored: and identical to the commit" \
  || { echo "::error::RESTORE FAILED - $S still differs from HEAD"; exit 3; }

echo
echo "$FIRED/$TOTAL controls fired."
if [ "$TOTAL" -eq 0 ]; then
  echo "::error::this harness holds ZERO rows; a green from it means nothing"
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. Each survivor names a property of the"
  echo "         canonical line that is not true of the line as it is printed."
  exit 1
fi
