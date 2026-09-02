#!/usr/bin/env bash
# Does the mirror push step REFUSE a zero-ref push? The guard is extracted from
# mirror.yml itself, never retyped, so this cannot pass against a copy.
set -uo pipefail
YML="${1:?path to mirror.yml}"
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

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

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

FLOOR=3
status=ok; [ "$FIRED" -eq "$ROWS" ] && [ "$ROWS" -ge "$FLOOR" ] || status=breach
echo "HARNESS-RESULT name=mirror-zero-refs rows=$ROWS floor=$FLOOR fired=$FIRED/$ROWS status=$status"
[ "$status" = ok ]
