#!/usr/bin/env bash
# THE BEFORE/AFTER LEDGER for task #107, and it is a probe rather than a gate.
#
# #107 is a REPORTING refactor: every script under `scripts/` gains one machine
# line and loses nothing. The claim "no behaviour changed" is only worth what a
# measurement makes it worth, and the measurement is this: run every script in
# the container, record its exit code, and compare the two ledgers.
#
# `-e` deliberately omitted: this probe reads the exit code of harnesses that
# are EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# THE ONE CANONICAL RESULT LINE (task #107) is deliberately NOT sourced here.
# This probe is not a harness; it is the instrument that reads them, and an
# instrument that emits the signal it measures is one grep away from reading
# itself. Its own name never appears in a HARNESS-RESULT line.

usage() {
  echo "usage: $0 <ledger-out> [per-script-timeout-seconds]" >&2
  echo "  then: diff <before-ledger> <after-ledger>" >&2
}

[ "$#" -ge 1 ] || { usage; exit 2; }
OUT="$1"
BUDGET="${2:-900}"

# A dirty tree means someone is mid-edit, and these harnesses mutate `src/` and
# restore it. Measuring here would measure them.
if ! git -C "$REPO" diff --quiet; then
  echo "ABORT: the tree is dirty; a harness restoring src/ would take someone" >&2
  echo "       else's edits with it. Commit or stash first." >&2
  exit 3
fi

# THE POPULATION IS THE GLOB. Not a list in this file, not a list in a table
# beside it. `scripts/*.sh` is the container, and every member is run.
mapfile -t SCRIPTS < <(cd "$REPO/scripts" && ls -1 ./*.sh | sed 's|^\./||' | sort)
echo "population: ${#SCRIPTS[@]} scripts under scripts/*.sh (by glob)"
[ "${#SCRIPTS[@]}" -gt 0 ] || { echo "ABORT: the glob matched nothing - prove the path resolves" >&2; exit 3; }

: > "$OUT"
for s in "${SCRIPTS[@]}"; do
  start=$SECONDS
  log=$(mktemp)
  timeout --signal=TERM --kill-after=30 "$BUDGET" bash "$REPO/scripts/$s" >"$log" 2>&1
  rc=$?
  took=$((SECONDS - start))

  # Did it print the canonical line, and did the line name ITSELF? A gate echoes
  # the harness it ran, so more than one line can appear; only the one carrying
  # this script's own basename is this script's verdict.
  line=$(grep -E "^HARNESS-RESULT name=$s " "$log" | tail -1)
  status="${line##*status=}"
  [ -n "$line" ] || status="NO-LINE"

  printf '%-42s rc=%-4s status=%-8s\n' "$s" "$rc" "$status" >> "$OUT"
  printf '%-42s rc=%-4s status=%-8s %ss\n' "$s" "$rc" "$status" "$took"
  rm -f "$log"

  # A harness that did not restore the tree poisons every run after it.
  if ! git -C "$REPO" diff --quiet; then
    echo "::error::$s LEFT THE TREE DIRTY. Stopping: every later row would" >&2
    echo "         measure its mutation rather than its own subject." >&2
    git -C "$REPO" status --porcelain >&2
    exit 4
  fi
done

echo
echo "ledger written to $OUT"
