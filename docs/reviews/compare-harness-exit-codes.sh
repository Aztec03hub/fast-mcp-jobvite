#!/usr/bin/env bash
# COMPARE TWO EXIT-CODE LEDGERS. Task #107.
#
#   docs/reviews/compare-harness-exit-codes.sh <before-ledger> <after-ledger>
#
# WHY THIS IS NOT `diff`. `diff` on two ledger files answers "are these two
# files the same", which is not the question. The question is "did any harness's
# exit code MOVE", and the two ledgers can legitimately hold different SETS of
# rows: a pass may be resumed, bounded by a deadline, or have skipped a harness
# whose run timed out and was therefore not recorded. `diff` reports every such
# row as a difference, which trains the reader to skim past real ones.
#
# SO THE COMPARISON IS ON THE INTERSECTION, AND THE INTERSECTION IS REPORTED.
# Two claims, kept apart because they fail differently:
#
#   1. AGREEMENT - of the harnesses measured on BOTH sides, how many exit codes
#      moved. This is the claim the refactor stands or falls on.
#   2. COVERAGE  - how many of the container's harnesses that intersection
#      actually covers. A perfect agreement over four rows is not evidence
#      about thirty-six, and a comparison that printed only claim 1 would let
#      the reader supply the wrong denominator themselves.
#
# THE ASYMMETRIC-BUDGET HAZARD, named because it was raised against this probe.
# The two ledgers may be produced with different per-script `timeout` budgets. A
# harness whose true duration falls between the two budgets would time out on
# one side and complete on the other. That CANNOT manufacture a false difference
# here, because `probe-harness-exit-codes.sh` refuses to record a 124 or 137 at
# all - a timeout is not a measurement, so the row is simply absent from that
# side and drops out of the intersection. What the asymmetry CAN do is quietly
# shrink coverage, which is why coverage is printed as loudly as agreement and
# why the exit code below is non-zero when the intersection is not the whole
# container.
#
# `-e` deliberately omitted for consistency with the harnesses this reads.
# See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

[ "$#" -eq 2 ] || { echo "usage: $0 <before-ledger> <after-ledger>" >&2; exit 2; }
BEFORE="$1"
AFTER="$2"
for f in "$BEFORE" "$AFTER"; do
  [ -f "$f" ] || { echo "ABORT: $f does not exist - prove the path resolves" >&2; exit 2; }
done

# The container is the glob, as everywhere else in this task.
total=$(cd "$REPO/scripts" && ls -1 ./*.sh | wc -l)

# A 124/125/137 must never appear; the probe refuses to write one. If one is
# here, the ledger was produced by an older probe and the whole comparison is
# void rather than merely incomplete.
if grep -qE 'rc=(124|125|137) ' "$BEFORE" "$AFTER"; then
  echo "::error::a ledger contains a timeout exit code. A timed-out run has NO"
  echo "         verdict, and comparing one against a real code on the other side"
  echo "         is the specific shape that manufactures a false difference."
  grep -nE 'rc=(124|125|137) ' "$BEFORE" "$AFTER"
  exit 3
fi

b_names=$(awk '{print $1}' "$BEFORE" | sort -u)
a_names=$(awk '{print $1}' "$AFTER"  | sort -u)
both=$(comm -12 <(printf '%s\n' "$b_names") <(printf '%s\n' "$a_names"))
n_both=$(printf '%s\n' "$both" | grep -c . || true)

moved=0
echo "harness                                    before    after"
echo "---------------------------------------------------------"
while IFS= read -r name; do
  [ -n "$name" ] || continue
  b=$(awk -v n="$name" '$1 == n { print $2 }' "$BEFORE" | tail -1)
  a=$(awk -v n="$name" '$1 == n { print $2 }' "$AFTER"  | tail -1)
  if [ "$b" = "$a" ]; then
    printf '%-42s %-9s %-9s\n' "$name" "$b" "$a"
  else
    printf '%-42s %-9s %-9s   <-- MOVED\n' "$name" "$b" "$a"
    moved=$((moved + 1))
  fi
done <<< "$both"

echo
echo "container (scripts/*.sh)          : $total"
echo "measured on the before side       : $(printf '%s\n' "$b_names" | grep -c . || true)"
echo "measured on the after side        : $(printf '%s\n' "$a_names" | grep -c . || true)"
echo "COMPARED (measured on both sides) : $n_both of $total"
echo "exit codes that MOVED             : $moved"

# WHICH ROWS ARE MISSING, BY NAME, PER SIDE. A reader given only "17 of 36"
# has to infer WHICH seventeen, and the inference is usually "the boring ones" -
# whereas the rows most likely to be absent are the SLOWEST, which are also the
# ones that exercise the most behaviour. Naming them turns a number a reader
# discounts into a list a reader can act on, and it makes an asymmetric per-script
# budget between the two arms visible as a longer list on one side.
missing_b=$(comm -23 <(cd "$REPO/scripts" && ls -1 ./*.sh | sed 's|^\./||' | sort) \
                     <(printf '%s\n' "$b_names"))
missing_a=$(comm -23 <(cd "$REPO/scripts" && ls -1 ./*.sh | sed 's|^\./||' | sort) \
                     <(printf '%s\n' "$a_names"))
if [ -n "$missing_b" ]; then
  echo
  echo "NOT MEASURED on the before side ($(printf '%s\n' "$missing_b" | grep -c .)):"
  printf '  %s\n' $missing_b
fi
if [ -n "$missing_a" ]; then
  echo
  echo "NOT MEASURED on the after side ($(printf '%s\n' "$missing_a" | grep -c .)):"
  printf '  %s\n' $missing_a
fi
if [ -n "$missing_b$missing_a" ]; then
  echo
  echo "A row absent from ONE side only is the tell for the two arms having been"
  echo "run under different per-script budgets. It cannot produce a false"
  echo "difference - a timeout is never recorded - but it shrinks coverage, and"
  echo "coverage is the denominator every number above is divided by."
fi

if [ "$n_both" -eq 0 ]; then
  echo "::error::the intersection is EMPTY. This is an instrument failure, not a"
  echo "         clean result - a zero that explains itself is the bug."
  exit 3
fi
if [ "$moved" -ne 0 ]; then
  echo "::error::$moved harness(es) changed exit code. This was a REPORTING"
  echo "         refactor; a moved exit code means behaviour changed and must be"
  echo "         explained rather than absorbed."
  exit 1
fi
if [ "$n_both" -ne "$total" ]; then
  echo "::error::no exit code moved across the $n_both compared, and that is NOT"
  echo "         a statement about the other $((total - n_both)). Resume both"
  echo "         ledgers until the intersection is the whole container."
  exit 1
fi
echo "EVERY harness in the container was measured on both sides, and none moved."
