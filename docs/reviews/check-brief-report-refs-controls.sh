#!/usr/bin/env bash
# Controls for check-brief-report-references.py.
#
# Every arm drives the REAL checker against FIXTURES and reads ITS exit
# code. Nothing here re-implements the rule, and nothing mutates the
# repository to watch a gate fail - a control that edits the tree it is
# checking is how a killed harness strands a mutation.
#
# The three amputations are the load-bearing arms: each deletes one
# failure branch from a COPY of the checker and requires the matching
# positive arm to go green. A positive arm nobody has watched fail is a
# claim, not a control. A8 earned that on its first run: A3's fixture
# tripped TWO failure branches, so amputating one left the other and the
# arm proved nothing about the branch it named.
#
# Reason strings are SINGLE-quoted. A backtick inside a double-quoted
# string is command substitution, and the first version of this file ran
# `resolved` as a command - the same defect this project already has a
# rule about for commit messages, in a place the rule did not name.

set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# THE ONE CANONICAL RESULT LINE (#107), sourced rather than re-typed.
# This harness printed its own `HARNESS-RESULT ...` by hand at first, and
# that is exactly the "second shape" the library exists to delete: it
# emitted `name=brief-report-refs-controls` where every consumer looks
# for `name=<the path it was invoked as>`, so
# `check-row-floor-controls.sh` could neutralise a row, watch this
# harness go red for the right reason, and still refuse - "the harness
# printed NO 'HARNESS-RESULT name=...' line ... A missing line is NOT a
# pass". Hand-rolling the line is what made this floor unwatchable
# (#194), not the directory it lives in.
# shellcheck source=../../scripts/lib/harness-result.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/harness-result.sh"
CHECKER="$ROOT/docs/reviews/check-brief-report-references.py"
PY=(uv run --frozen python)

ROW_FLOOR=11
ROWS=0
FIRED=0

tmp=$(mktemp -d) || exit 3
trap 'harness_result_emit; rm -rf "$tmp"' EXIT

if [ ! -f "$CHECKER" ]; then
  echo "MUTATION TARGET NOT FOUND: $CHECKER"
  exit 3
fi

# --- fixtures -----------------------------------------------------------
# briefs/  one brief citing REVIEW-PRESENT.md and REVIEW-ABSENT.md
# tracked  a newline listing standing in for `git ls-files`
mkdir -p "$tmp/briefs"
cat > "$tmp/briefs/BRIEF-fixture.md" <<'EOF'
See `docs/reviews/REVIEW-PRESENT.md` and also REVIEW-ABSENT.md.
EOF
printf 'docs/reviews/REVIEW-PRESENT.md\nsrc/other.py\n' > "$tmp/tracked"

record() { printf '%s\n' "$@" > "$tmp/record"; }

run() {  # run <checker> -> exit code
  "${PY[@]}" "$1" --briefs "$tmp/briefs" --record "$tmp/record" \
    --tracked "$tmp/tracked" >/dev/null 2>&1
}

row() {  # row <label> <checker> <expected-rc>
  ROWS=$((ROWS + 1))
  run "$2"
  rc=$?
  if [ "$rc" -eq "$3" ]; then
    FIRED=$((FIRED + 1))
    echo "  ok   $1 (rc=$rc)"
  else
    echo "  FAIL $1 (rc=$rc, wanted $3)"
  fi
}

# Sets the global AMP. It must NOT be called as `amp=$(amputate ...)`:
# command substitution runs it in a SUBSHELL, so its ROWS increment is
# discarded and its FAIL message is captured into the variable instead
# of printed. The first version of this file did exactly that, and A11
# silently never ran - a harness losing a row is the failure this whole
# file exists to make impossible.
AMP=""
amputate() {  # amputate <name> <sed-expr> ; sets AMP, returns 0/1
  AMP="$tmp/amp-$1.py"
  sed "$2" "$CHECKER" > "$AMP"
  if cmp -s "$AMP" "$CHECKER"; then
    echo "  FAIL amputation '$1' CHANGED NOTHING - ANCHOR NOT FOUND"
    ROWS=$((ROWS + 1))
    return 1
  fi
  return 0
}

# Every arm that changes the fixture brief restores it, so an arm can
# never inherit the previous arm's world.
fixture_default() {
  cat > "$tmp/briefs/BRIEF-fixture.md" <<'EOF'
See `docs/reviews/REVIEW-PRESENT.md` and also REVIEW-ABSENT.md.
EOF
}
fixture_longer_name() {
  cat > "$tmp/briefs/BRIEF-fixture.md" <<'EOF'
See `docs/CODE-REVIEW-CHECKLIST.md`, which is not a report citation.
EOF
}

echo "########## positives"

# A1 - an unrecorded dangling citation must FAIL.
record ""
row "A1 unrecorded dangling -> 1" "$CHECKER" 1

# A2 - recorded, so the same tree must PASS.
record "REVIEW-ABSENT.md  recorded for the control"
row "A2 recorded -> 0" "$CHECKER" 0

# A3 - a recorded entry that RESOLVES must FAIL (the record went stale).
# BOTH lines are needed and that is the point: with only the PRESENT line
# the fixture also trips `unrecorded`, so A3 would be red for two reasons
# and its amputation would still find one of them. A8 caught exactly that
# and the first version of this arm was confounded.
record "REVIEW-PRESENT.md  wrongly recorded; it is tracked" \
       'REVIEW-ABSENT.md  recorded, so only resolved can fire'
row "A3 recorded-but-present -> 1" "$CHECKER" 1

# A4 - a recorded entry nothing cites must FAIL. Same isolation rule:
# REVIEW-ABSENT.md is recorded so only `unreferenced` can fire.
record "REVIEW-ABSENT.md  ok" "REVIEW-NOBODY-CITES.md  stale line"
row "A4 recorded-but-uncited -> 1" "$CHECKER" 1

# A5 - an unreadable listing must REFUSE (exit 2), not pass.
record "REVIEW-ABSENT.md  ok"
mv "$tmp/tracked" "$tmp/tracked.hidden"
row "A5 unreadable listing -> 2 (refusal)" "$CHECKER" 2
mv "$tmp/tracked.hidden" "$tmp/tracked"

# A6 - an EMPTY listing is not the same as an unreadable one: everything
# dangles and it must FAIL, not refuse. None-vs-empty, measured.
record "REVIEW-ABSENT.md  ok"
: > "$tmp/tracked"
row "A6 empty listing -> 1 (not 2)" "$CHECKER" 1
printf 'docs/reviews/REVIEW-PRESENT.md\nsrc/other.py\n' > "$tmp/tracked"

# A10 - A LONGER NAME MUST NOT MATCH ITS TAIL. This is the arm for a
# FALSE FINDING I published: `docs/CODE-REVIEW-CHECKLIST.md` exists and
# is cited by two briefs, and without a left boundary the pattern read
# it as `REVIEW-CHECKLIST.md`, which never has. The fixture cites only
# the longer name, so a correct checker sees NO report citation at all.
fixture_longer_name
record ""
row "A10 longer name not matched by its tail -> 0" "$CHECKER" 0
fixture_default

echo "########## amputations"

# A7 - delete the unrecorded-dangling branch; A1 must go green.
if amputate unrecorded 's/^    if unrecorded:$/    if False:/'; then
  record ""
  row "A7 AMP unrecorded -> A1 survives at 0" "$AMP" 0
fi

# A8 - delete the resolved branch; A3 must go green.
if amputate resolved 's/^    if resolved:$/    if False:/'; then
  record 'REVIEW-PRESENT.md  wrongly recorded; it is tracked' \
         'REVIEW-ABSENT.md  recorded, so only resolved can fire'
  row "A8 AMP resolved -> A3 survives at 0" "$AMP" 0
fi

# A9 - delete the uncited branch; A4 must go green.
if amputate unreferenced 's/^    if unreferenced:$/    if False:/'; then
  record 'REVIEW-ABSENT.md  ok' 'REVIEW-NOBODY-CITES.md  stale line'
  row "A9 AMP unreferenced -> A4 survives at 0" "$AMP" 0
fi

# A11 - delete the LEFT BOUNDARY; A10 must go red. Without this arm the
# lookbehind can be removed and nothing notices, which is exactly how
# the false finding shipped in the first place.
fixture_longer_name
if amputate boundary '/(?<!/d'; then
  record ""
  row "A11 AMP left boundary -> A10 goes red at 1" "$AMP" 1
fi
fixture_default

harness_result_tally fired "$FIRED" "$ROWS"
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -ne "$ROW_FLOOR" ]; then
  echo "::error::$ROWS rows against ROW_FLOOR=$ROW_FLOOR."
  exit 1
fi
if [ "$FIRED" -ne "$ROWS" ]; then
  echo "::error::$FIRED of $ROWS fired. Read WHICH arm failed."
  exit 1
fi
echo "$FIRED/$ROWS controls fired."
