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
CHECKER="$ROOT/docs/reviews/check-brief-report-references.py"
PY=(uv run --frozen python)

ROW_FLOOR=9
ROWS=0
FIRED=0

tmp=$(mktemp -d) || exit 3
trap 'rm -rf "$tmp"' EXIT

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

amputate() {  # amputate <name> <sed-expr> -> path to a maimed copy
  local out="$tmp/amp-$1.py"
  sed "$2" "$CHECKER" > "$out"
  if cmp -s "$out" "$CHECKER"; then
    echo "  FAIL amputation '$1' CHANGED NOTHING - anchor not found"
    ROWS=$((ROWS + 1))
    return 1
  fi
  printf '%s' "$out"
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

echo "########## amputations"

# A7 - delete the unrecorded-dangling branch; A1 must go green.
if amp=$(amputate unrecorded 's/^    if unrecorded:$/    if False:/'); then
  record ""
  row "A7 AMP unrecorded -> A1 survives at 0" "$amp" 0
fi

# A8 - delete the resolved branch; A3 must go green.
if amp=$(amputate resolved 's/^    if resolved:$/    if False:/'); then
  record "REVIEW-PRESENT.md  wrongly recorded; it is tracked" \
         'REVIEW-ABSENT.md  recorded, so only resolved can fire'
  row "A8 AMP resolved -> A3 survives at 0" "$amp" 0
fi

# A9 - delete the uncited branch; A4 must go green.
if amp=$(amputate unreferenced 's/^    if unreferenced:$/    if False:/'); then
  record "REVIEW-ABSENT.md  ok" "REVIEW-NOBODY-CITES.md  stale line"
  row "A9 AMP unreferenced -> A4 survives at 0" "$amp" 0
fi

status=ok
if [ "$FIRED" -ne "$ROWS" ] || [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  status=breach
fi
echo "HARNESS-RESULT name=brief-report-refs-controls rows=$ROWS" \
  "floor=$ROW_FLOOR fired=$FIRED/$ROWS status=$status"
[ "$status" = ok ]
