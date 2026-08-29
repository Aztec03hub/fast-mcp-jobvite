#!/usr/bin/env bash
# CONTROLS for scripts/ci-harness-gate.sh - the gate every harness step calls.
#
# A gate whose whole job is to notice that a harness stopped checking is worth
# nothing until something has watched it FAIL. Task #27 exists because that gate
# lived inline in a ci.yml `run:` block and could not be exercised at all.
#
# EACH ROW SUBSTITUTES A STUB HARNESS that replays RECORDED output - the real
# lines the real harnesses print - and exits with a chosen code. Stubs, because
# the arms worth testing are the ones a healthy repository never produces: a
# moved anchor, a hung row, a control that did not fire. Waiting for a real
# harness to fail is not a test plan, and a green repository cannot supply one.
#
# THE STUB IS NOT A TWIN OF THE GATE. The thing being tested is the real
# scripts/ci-harness-gate.sh, copied unmodified and invoked as CI invokes it;
# only its SUBJECT is substituted. A twin of the gate would be the two-lists
# defect this whole change exists to remove.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/scripts"
cp "$REPO/scripts/ci-harness-gate.sh" "$WORK/scripts/"

FIRED=0
TOTAL=0

# stub <name> <vocab: yes|no> <exit code> <lines...>
#
# `vocab` puts the anchor-failure phrases in the stub's SOURCE, as a comment,
# without PRINTING them. That separation is the whole subject: the gate derives
# what to grep for from the harness's source and then looks for it in the
# harness's OUTPUT, and a stub that conflated the two could not tell the two
# halves apart. `vocab no` is C4 - the harness that cannot report a moved anchor
# at all, which is the defect check-u15-gate-amputation.sh actually had.
#
# Lines are emitted single-quoted, NOT with `printf %q`. %q backslash-escapes
# the spaces, so `echo COULD\ NOT\ APPLY` does not contain the phrase
# `COULD NOT APPLY` as source text - and the first run of this harness had 21 of
# 23 rows refused for want of a vocabulary that was there all along, in a form
# no `grep -F` could see. An escaping that survives execution but not inspection
# is invisible in exactly the direction that matters here.
stub() {
  local name="$1" vocab="$2" code="$3"; shift 3
  { echo '#!/usr/bin/env bash'
    if [ "$vocab" = yes ]; then
      echo '# recorded vocabulary, present in source and NOT printed:'
      echo '#   COULD NOT APPLY / DID NOT LAND / ANCHOR NOT UNIQUE'
    fi
    local line
    for line in "$@"; do printf "echo '%s'\n" "$line"; done
    echo "exit $code"
  } > "$WORK/scripts/$name"
  chmod +x "$WORK/scripts/$name"
}

# row <label> <want rc> <harness> <gate args...>
row() {
  local label="$1" want="$2" harness="$3"; shift 3
  TOTAL=$((TOTAL + 1))
  local out rc
  out=$(bash "$WORK/scripts/ci-harness-gate.sh" "$harness" "$@" 2>&1); rc=$?
  if [ "$rc" -eq "$want" ]; then
    FIRED=$((FIRED + 1))
    echo "  FIRED    $label (exit $rc)"
  else
    echo "  SURVIVED $label (exit $rc, wanted $want)"
    printf '%s\n' "$out" | sed 's/^/      /'
  fi
}

echo "########## THE ANCHOR GATE - the defect that started all of this"

# The vocabulary is DERIVED from the stub's own source, so a stub that prints
# COULD NOT APPLY also contains it and the gate greps for it. That coupling is
# the point: a phrase a harness cannot print is never grepped for.
stub clean.sh yes 0 'RESULT: 12 killed, 0 not killed'
row "C1 a clean mutation harness passes" 0 clean.sh --result-killed

stub moved.sh yes 0 \
  'M8: COULD NOT APPLY - the anchor moved. Fix the harness.' \
  'RESULT: 11 killed, 0 not killed'
row "C2 COULD NOT APPLY is caught even though the harness exited 0" 1 moved.sh --result-killed

stub notland.sh yes 0 \
  '  AMPUTATION DID NOT LAND despite a successful write' \
  'RESULT: 12 killed, 0 not killed'
row "C3 DID NOT LAND is caught even though the harness exited 0" 1 notland.sh --result-killed

echo
echo "########## THE HARNESS THAT CANNOT REPORT ONE AT ALL - task #29's sharpest item"

# No phrase from the vocabulary anywhere in its source. The gate must REFUSE it
# rather than pass it, because a grep for a string a harness never prints is an
# inoperative gate that looks exactly like coverage.
stub mute.sh no 0 'everything is fine'
row "C4 a harness with no anchor-failure vocabulary is REFUSED" 2 mute.sh --result-killed

echo
echo "########## EXIT CODES - three, kept apart"

stub survivor.sh yes 1 '  UNEXPECTED SURVIVOR: tests/test_boot.py::test_x'
row "C5 an amputation exit 1 is a FINDING, not a pass" 1 survivor.sh --amputation

stub cannotrun.sh yes 3 'baseline is red'
row "C6 an amputation exit 3 is could-not-run" 1 cannotrun.sh --amputation

stub weird.sh yes 7 'something else'
row "C7 any other non-zero exit fails" 1 weird.sh --amputation

echo
echo "########## A HUNG ROW MEASURES NOTHING AND READS AS A PASS"

stub hung.sh yes 0 '  TIMED OUT after 300s' \
  '########## A1 x' '########## A2 x'
row "C8 TIMED OUT is caught" 1 hung.sh --amputation

echo
echo "########## THE COUNTING ARMS"

stub fired.sh yes 0 '14/14 controls fired.'
row "C9 all controls fired passes" 0 fired.sh --controls-fired

stub partial.sh yes 0 '13/14 controls fired.'
row "C10 13 of 14 fired is caught" 1 partial.sh --controls-fired

# A harness that holds ZERO controls reports "0/0 controls fired." and every
# equality check passes. A green from it means nothing, and equality alone
# cannot tell it apart from a harness that ran everything.
stub zero.sh yes 0 '0/0 controls fired.'
row "C11 zero controls held is caught, though 0 == 0" 1 zero.sh --controls-fired

stub noline.sh yes 0 'ran some things'
row "C12 a missing 'N/M controls fired.' line is caught" 1 noline.sh --controls-fired

stub survived.sh yes 0 'RESULT: 11 killed, 1 not killed'
row "C13 a surviving mutation is caught" 1 survived.sh --result-killed

stub nokill.sh yes 0 'RESULT: 0 killed, 0 not killed'
row "C14 zero mutations killed is caught, though 0 survived" 1 nokill.sh --result-killed

stub applied.sh yes 0 'ROWS: 11   ANCHORS APPLIED: 11'
row "C15 every anchor applied passes" 0 applied.sh --anchors-applied

stub short.sh yes 0 'ROWS: 11   ANCHORS APPLIED: 9'
row "C16 9 of 11 anchors applied is caught" 1 short.sh --anchors-applied

# C11 and C14 are this row's siblings, and its absence was the defect: `rows -ne
# applied` is FALSE at 0 == 0, so a harness that ran NOTHING passed the gate
# while the other two flags already refused their own zero. The generic form of
# R4-M4, and it applied to every harness gated this way, not just U5's.
stub norows.sh yes 0 'ROWS: 0   ANCHORS APPLIED: 0'
row "C24 zero rows is caught, though 0 == 0" 1 norows.sh --anchors-applied

echo
echo "########## ROW COUNT - how a row goes missing without a red run"

stub rows.sh yes 0 \
  '########## A1 x' '########## A2 x' '########## A3 x'
row "C17 enough rows passes" 0 rows.sh --amputation --min-rows 3 --row-re '^########## A[0-9]+ '
row "C18 a vanished row is caught" 1 rows.sh --amputation --min-rows 4 --row-re '^########## A[0-9]+ '

# The U4 lesson, as a row: `A[0-9]+ ` requires a space straight after the
# digits, so A9b..A9f are invisible to it and the gate reports the number of
# rows it can SEE. The correct pattern counts them.
stub suffixed.sh yes 0 \
  '########## A9b x' '########## A9c x' '########## A9d x'
row "C19 a suffixed row id is INVISIBLE to the naive pattern" 1 suffixed.sh \
  --amputation --min-rows 3 --row-re '^########## A[0-9]+ '
row "C20 and visible to the corrected one" 0 suffixed.sh \
  --amputation --min-rows 3 --row-re '^########## A[0-9]+[a-z]* '

echo
echo "########## --require, which is how a restore failure is noticed"

stub restored.sh yes 0 \
  'post-run re-check of the real script: exit=0'
row "C21 the restore line present passes" 0 restored.sh --amputation \
  --require 'post-run re-check of the real script: exit=0'

stub norestore.sh yes 0 '4/4 amputations killed a test.'
row "C22 a missing restore line is caught" 1 norestore.sh --amputation \
  --require 'post-run re-check of the real script: exit=0'

echo
echo "########## MISUSE - a gate misconfigured must not read as a pass"

row "C23 a harness that does not exist is refused" 2 no-such-harness.sh --result-killed

echo
echo "$FIRED/$TOTAL controls fired."

if [ "$TOTAL" -eq 0 ]; then
  echo "::error::the harness holds zero rows; a green from it means nothing"
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. Every survivor names an arm of the gate that"
  echo "         does not do what its own message says it does."
  exit 1
fi
