#!/usr/bin/env bash
# Does the mirror push step REFUSE a zero-ref push? The guard is extracted from
# mirror.yml itself, never retyped, so this cannot pass against a copy.
set -uo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# THE ONE CANONICAL RESULT LINE (#107), sourced rather than re-typed.
# Hand-rolling it emitted `name=mirror-zero-refs` where every consumer
# looks for `name=<the path it was invoked as>`, which is what made this
# floor unwatchable by `check-row-floor-controls.sh` (#194).
# shellcheck source=../../scripts/lib/harness-result.sh
. "$REPO/scripts/lib/harness-result.sh"

# THE ARGUMENT DEFAULTS, and that is not a convenience. The floor control
# runs a harness with NO arguments; a mandatory `${1:?}` made this probe
# exit 3 there and report nothing, so its floor could never be watched by
# the machinery built to watch floors. An explicit path still overrides.
YML="${1:-$REPO/.github/workflows/mirror.yml}"
ROWS=0; FIRED=0

guard() {  # runs the extracted guard in $1, returns its exit code
  ( cd "$1" && bash -e -c "$GUARD" ) >/dev/null 2>&1
}

# EXTRACT, do not retype: the four lines from `refs=$(...)` through the `fi`.
GUARD=$(awk '/^ *refs=\$\(git for-each-ref/,/^ *fi$/' "$YML" | sed 's/^ *//')
if [ -z "$GUARD" ]; then echo "ANCHOR NOT FOUND in $YML"; exit 3; fi
if ! grep -q 'exit 1' <<<"$GUARD"; then echo "ANCHOR NOT UNIQUE / wrong block"; exit 3; fi
echo "guard extracted, $(wc -l <<<"$GUARD") lines"

row() {  # row <label> <dir> <expected-rc>
  ROWS=$((ROWS+1))
  guard "$2"; rc=$?
  if [ "$rc" -eq "$3" ]; then FIRED=$((FIRED+1)); echo "  ok   $1 (rc=$rc)"
  else echo "  FAIL $1 (rc=$rc, wanted $3)"; fi
}

tmp=$(mktemp -d); trap 'harness_result_emit; rm -rf "$tmp"' EXIT

# ARM 1 - a repo with NO refs/remotes/origin and NO tags: the guard must REFUSE.
git init -q "$tmp/empty"
row "0 refs REFUSED" "$tmp/empty" 1

# ARM 2 - a repo carrying a remote ref and a tag: the guard must PASS.
git init -q "$tmp/full"
( cd "$tmp/full" || exit 1
  git -c user.email=p@x -c user.name=p commit -q --allow-empty -m x
  git update-ref refs/remotes/origin/main HEAD
  git tag v1 ) >/dev/null 2>&1
row "N refs ALLOWED" "$tmp/full" 0

# ARM 3 - AMPUTATION: delete the `exit 1` and ARM 1 must stop refusing.
GUARD_SAVED="$GUARD"
GUARD=$(sed 's/^ *exit 1$/:/' <<<"$GUARD")
guard "$tmp/empty"; rc=$?
ROWS=$((ROWS+1))
if [ "$rc" -eq 0 ]; then FIRED=$((FIRED+1)); echo "  ok   amputation SURVIVES green (rc=0) - arm 1 was testing the guard"
else echo "  FAIL amputation still refused (rc=$rc) - arm 1 proves nothing"; fi
GUARD="$GUARD_SAVED"

ROW_FLOOR=3
harness_result_tally fired "$FIRED" "$ROWS"
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -ne "$ROW_FLOOR" ]; then
  echo "::error::$ROWS rows against ROW_FLOOR=$ROW_FLOOR."
  exit 1
fi
if [ "$FIRED" -ne "$ROWS" ]; then
  echo "::error::$FIRED of $ROWS fired. Read WHICH row failed."
  exit 1
fi
echo "$FIRED/$ROWS controls fired."
