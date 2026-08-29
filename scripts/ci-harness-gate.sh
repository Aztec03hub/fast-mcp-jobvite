#!/usr/bin/env bash
# ONE gate for every mutation and amputation harness, runnable locally.
#
# WHY IT EXISTS (task #27). The U1 amputation gate's logic lived inline in a
# ci.yml `run:` block, so it could not be run locally, reviewed as code, or
# exercised by a control. The agent before this one verified a change to it by
# hand-copying the block into a local script and replaying recorded output, then
# deliberately did NOT commit the copy - a hand-copied twin of a gate is the
# two-lists defect: ci.yml moves, the twin does not, and the twin keeps passing.
# That refusal was right. This is the real thing, called by ci.yml, with no twin.
#
# WHY IT IS SHARED (task #29). Six steps could not detect a stale anchor. The
# fix is NOT six copies of one grep: the harnesses use different vocabulary, and
# a grep for a string a harness never prints is an INOPERATIVE gate - the same
# defect as the stale anchor, arriving from the other side, and worse than the
# gap because it looks like coverage.
#
# So the vocabulary is DERIVED, not configured. For each harness this reads the
# HARNESS'S OWN SOURCE, keeps the anchor-failure phrases that actually appear in
# it, and greps the log for exactly those. A phrase a harness cannot print is
# never grepped, and a harness that can print NONE of them fails the gate
# outright with a message saying so - because a harness that cannot report a
# failed anchor cannot be gated on one, and that is a defect in the harness.
#
# SCOPE DECISION, task #27, MINE AND STATED. Every harness step in ci.yml now
# calls this; none is left inline. Converting one step would have made the file
# inconsistent for no gain, and the sibling steps were near-identical copies of
# each other already - which is what let U3's and U4's mutation steps BOTH ship
# the same anchor blindness and get fixed twice. The non-harness steps (lint,
# types, the licence gate) are untouched: they are single commands, not
# multi-branch logic, and inline is the right form for them.
#
# THIS IS THE SECOND LAYER, NOT THE FIRST. scripts/check-harness-anchors.py
# reads the anchors statically and catches a stale one in milliseconds, without
# running anything. This catches what only running can show - a mutation that
# applied and then landed on nothing, a row that hung, a control that did not
# fire - and it is also what covers a harness inventing a phrase the static
# checker's shapes cannot see.
#
# Usage:
#   ci-harness-gate.sh <harness.sh> [options]
#     --controls-fired        require an "N/M controls fired." line with N == M and M > 0
#     --result-killed         require a "RESULT: N killed, M not killed" line, N > 0, M == 0
#     --anchors-applied       require a "ROWS: N   ANCHORS APPLIED: M" line with N == M
#     --min-rows N --row-re RE  require at least N lines matching RE
#     --require RE            require at least one line matching RE
#     --amputation            survivors are output, so exit 0 is not the only pass;
#                             exit 1 is a FINDING and exit 3 is "could not run"
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# THE ANCHOR-FAILURE VOCABULARY, all of it, across every harness here. A phrase
# is grepped for ONLY when the harness's own source contains it, so this list
# can gain a phrase without making any existing gate inoperative.
#
# `MUTATION TARGET NOT FOUND` and `BROKEN CONTROL` come from U15's controls;
# `ANCHOR MISSING`/`ANCHOR NOT UNIQUE` from the suite-floor harness and the
# shared python mutators; `COULD NOT APPLY` from U3, U4 and U5; `DID NOT LAND`
# from U1's controls and the suite-floor harness; `anchor is not unique` from
# U1's amputation harness. They are NOT unified into one phrase: each is printed
# beside a different diagnosis, and collapsing them would send the next reader to
# the wrong place - the same defect one layer up that this file's exit-code
# branches exist to avoid.
VOCABULARY=(
  'COULD NOT APPLY'
  'DID NOT LAND'
  'ANCHOR MISSING'
  'ANCHOR NOT UNIQUE'
  'anchor is not unique'
  'MUTATION TARGET NOT FOUND'
  'BROKEN CONTROL'
  'STAGING ERROR'
  'the mutation target was not found'
)

harness=""
want_controls_fired=0
want_result_killed=0
want_anchors_applied=0
min_rows=0
row_re=""
amputation=0
requires=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --controls-fired)  want_controls_fired=1; shift ;;
    --result-killed)   want_result_killed=1; shift ;;
    --anchors-applied) want_anchors_applied=1; shift ;;
    --amputation)      amputation=1; shift ;;
    --min-rows)        min_rows="$2"; shift 2 ;;
    --row-re)          row_re="$2"; shift 2 ;;
    --require)         requires+=("$2"); shift 2 ;;
    -*) echo "::error::unknown option $1"; exit 2 ;;
    *)  harness="$1"; shift ;;
  esac
done

[ -n "$harness" ] || { echo "::error::no harness named"; exit 2; }
HARNESS_PATH="$REPO/scripts/$harness"
[ -f "$HARNESS_PATH" ] || { echo "::error::no such harness: scripts/$harness"; exit 2; }

# Derive this harness's vocabulary from its own source BEFORE running it, so a
# harness that cannot report a failed anchor fails in seconds rather than after
# the run. THE HARNESS'S OWN GATE VOCABULARY IS THE ONE THING NOT TAKEN ON
# TRUST: task #29 measured that check-u15-gate-amputation.sh had none at all, so
# no step could gate on it, and it had been passing for months on that basis.
present=()
for phrase in "${VOCABULARY[@]}"; do
  if grep -qF -- "$phrase" "$HARNESS_PATH"; then present+=("$phrase"); fi
done

if [ "${#present[@]}" -eq 0 ]; then
  echo "::error::scripts/$harness prints NO anchor-failure phrase, so nothing can gate"
  echo "         on one. A mutation that applies to nothing tests nothing, and this"
  echo "         harness cannot say that it happened. Give it one of:"
  printf '           %s\n' "${VOCABULARY[@]}"
  exit 2
fi
echo "gate vocabulary for $harness (derived from its source): ${present[*]}"

out=$(bash "$HARNESS_PATH" 2>&1); rc=$?
echo "$out"

# ---- exit code -------------------------------------------------------------
# An amputation harness exits 0 by design because SURVIVORS ARE ITS OUTPUT, so
# the exit code alone cannot be the verdict. U1's harness distinguishes three
# codes and the messages are kept apart on purpose: a message that misdescribes
# what happened sends the next reader to the wrong place.
if [ "$amputation" -eq 1 ]; then
  if [ "$rc" -eq 1 ]; then
    echo "::error::$harness: an amputation was survived by an assertion that exists to"
    echo "         notice it, or a row could not be measured. Search the log above for"
    echo "         UNEXPECTED SURVIVOR and TIMED OUT."
    exit 1
  fi
  if [ "$rc" -eq 3 ]; then
    echo "::error::$harness could not run: the intact baseline is red, or a declared"
    echo "         test id no longer exists (a rename silently voids its row)."
    exit 1
  fi
fi
if [ "$rc" -ne 0 ]; then
  echo "::error::$harness exited $rc"
  exit 1
fi

fail=0

# ---- the anchor gate, uniform and never inoperative ------------------------
for phrase in "${present[@]}"; do
  if printf '%s\n' "$out" | grep -qF -- "$phrase"; then
    echo "::error::$harness printed '$phrase' - a row's anchor moved and that row"
    echo "         tested NOTHING. The harness still exited 0; that is the point."
    fail=1
  fi
done

# ---- a hang measures nothing, and a timed-out row reads as a pass ----------
if printf '%s\n' "$out" | grep -q 'TIMED OUT'; then
  echo "::error::$harness: a row hung. It produced no result lines, so every"
  echo "         assertion 'did not survive' and the row reads as a pass."
  fail=1
fi

# ---- "N/M controls fired." -------------------------------------------------
if [ "$want_controls_fired" -eq 1 ]; then
  line=$(printf '%s\n' "$out" | grep -oE '[0-9]+/[0-9]+ controls fired\.' | tail -1)
  if [ -z "$line" ]; then
    echo "::error::$harness printed no 'N/M controls fired.' line"; fail=1
  else
    fired=${line%%/*}; rest=${line#*/}; total=${rest%% *}
    if [ "$total" -eq 0 ]; then
      echo "::error::$harness holds ZERO controls; a green from it means nothing"; fail=1
    elif [ "$fired" -ne "$total" ]; then
      echo "::error::$harness: only $fired of $total controls fired"; fail=1
    fi
  fi
fi

# ---- "RESULT: N killed, M not killed" --------------------------------------
if [ "$want_result_killed" -eq 1 ]; then
  line=$(printf '%s\n' "$out" | grep -oE 'RESULT: [0-9]+ killed, [0-9]+ not killed' | tail -1)
  if [ -z "$line" ]; then
    echo "::error::$harness printed no 'RESULT:' line"; fail=1
  else
    killed=$(printf '%s' "$line" | grep -oE '[0-9]+ killed' | grep -oE '[0-9]+')
    not_killed=$(printf '%s' "$line" | grep -oE '[0-9]+ not killed' | grep -oE '[0-9]+')
    if [ "$killed" -eq 0 ]; then
      echo "::error::$harness killed ZERO mutations - it ran nothing"; fail=1
    fi
    if [ "${not_killed:-1}" -ne 0 ]; then
      echo "::error::$harness: $not_killed mutations survived"; fail=1
    fi
  fi
fi

# ---- "ROWS: N   ANCHORS APPLIED: M" ---------------------------------------
if [ "$want_anchors_applied" -eq 1 ]; then
  line=$(printf '%s\n' "$out" | grep -oE 'ROWS: [0-9]+   ANCHORS APPLIED: [0-9]+' | tail -1)
  if [ -z "$line" ]; then
    echo "::error::$harness printed no 'ROWS/ANCHORS APPLIED' line"; fail=1
  else
    rows=$(printf '%s\n' "$line" | grep -oE 'ROWS: [0-9]+' | grep -oE '[0-9]+')
    applied=$(printf '%s\n' "$line" | grep -oE 'APPLIED: [0-9]+' | grep -oE '[0-9]+')
    # ZERO FIRST, because `rows -ne applied` is FALSE at 0 == 0 and a harness
    # that ran NOTHING would sail through the comparison below. The two sibling
    # branches above already refuse their own zero - `total -eq 0` for
    # --controls-fired, `killed -eq 0` for --result-killed - so without this the
    # script disagreed with ITSELF about whether an empty run is acceptable,
    # depending only on which flag you passed. The generic form of R4-M4.
    if [ "$rows" -eq 0 ]; then
      echo "::error::$harness ran ZERO rows; a green from it means nothing"; fail=1
    elif [ "$rows" -ne "$applied" ]; then
      echo "::error::$harness: only $applied of $rows anchors applied"; fail=1
    fi
  fi
fi

# ---- row count -------------------------------------------------------------
# A gate reporting the number of rows it can SEE is how a row goes missing
# without a red run: U4's pattern once required a space straight after the
# digits, so it counted 12 while 17 ran.
if [ "$min_rows" -gt 0 ]; then
  [ -n "$row_re" ] || { echo "::error::--min-rows needs --row-re"; exit 2; }
  rows=$(printf '%s\n' "$out" | grep -cE "$row_re")
  if [ "$rows" -lt "$min_rows" ]; then
    echo "::error::$harness: only $rows rows ran, expected at least $min_rows"; fail=1
  fi
fi

# ---- arbitrary required lines ---------------------------------------------
for re in ${requires+"${requires[@]}"}; do
  if ! printf '%s\n' "$out" | grep -qE -- "$re"; then
    echo "::error::$harness did not print a line matching: $re"; fail=1
  fi
done

exit "$fail"
