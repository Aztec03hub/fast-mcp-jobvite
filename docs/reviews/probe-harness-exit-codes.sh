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
  echo "usage: $0 <ledger-out> [per-script-seconds] [overall-deadline-seconds]" >&2
  echo "  per-script-seconds  timeout for ONE harness (default 900). A run that" >&2
  echo "                      exceeds it is NOT recorded - a timeout is not a" >&2
  echo "                      measurement - so a later, larger budget retries it." >&2
  echo "  overall-deadline    0 (default) means run to completion. Otherwise the" >&2
  echo "                      probe stops CLEANLY between harnesses once a further" >&2
  echo "                      per-script budget would not fit, so an outside" >&2
  echo "                      bound never lands mid-harness. Combined with the" >&2
  echo "                      resume, repeated bounded calls walk the container." >&2
  echo "                      A harness slower than the caller's own limit can" >&2
  echo "                      therefore never be measured this way; it needs one" >&2
  echo "                      unbounded run." >&2
  echo "  then: docs/reviews/compare-harness-exit-codes.sh <before> <after>" >&2
  echo "        NOT \`diff\` - the two ledgers may legitimately hold different" >&2
  echo "        SETS of rows, and diff reports every such row as a difference." >&2
}

[ "$#" -ge 1 ] || { usage; exit 2; }
OUT="$1"
BUDGET="${2:-900}"

# AN OVERALL DEADLINE, CHECKED ONLY BETWEEN SCRIPTS. A caller that has to bound
# this probe from outside - a CI step limit, a tool timeout - would kill it
# MID-HARNESS, and a mutation harness killed mid-row strands its mutation in the
# working tree. That is a measured failure here, not a hypothetical.
#
# So the bound is given TO the probe instead: before each script it asks whether
# a full per-script budget still fits, and if not it stops cleanly and says how
# many rows remain. Combined with the resume above, repeated bounded calls walk
# the whole container without any of them ever being killed.
DEADLINE="${3:-0}"

# A dirty tree means someone is mid-edit, and these harnesses mutate `src/` and
# restore it. Measuring here would measure them.
# `git status --porcelain`, NOT `git diff --quiet`. `git diff` compares the
# worktree to the INDEX, so a file edited and then `git add`-ed reads CLEAN
# and this guard waves it through. Measured: modify + `git add` gives
# `git diff --quiet` exit 0 and `--porcelain` a non-empty `M `.
if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  echo "ABORT: the tree is dirty (staged, unstaged or untracked); a harness" >&2
  echo "       restoring src/ would take someone else's edits with it." >&2
  echo "       Commit or stash first." >&2
  exit 3
fi

# THE POPULATION IS THE GLOB. Not a list in this file, not a list in a table
# beside it. `scripts/*.sh` is the container, and every member is run.
mapfile -t SCRIPTS < <(cd "$REPO/scripts" && ls -1 ./*.sh | sed 's|^\./||' | sort)
echo "population: ${#SCRIPTS[@]} scripts under scripts/*.sh (by glob)"
[ "${#SCRIPTS[@]}" -gt 0 ] || { echo "ABORT: the glob matched nothing - prove the path resolves" >&2; exit 3; }

# RESUMABLE, BY MEASUREMENT AND NOT BY DESIGN TASTE. A full pass over this
# container is hours long, and this probe was killed twice mid-run - once by a
# tracked file changing under it (correctly: the guard below), once from
# outside. A pass that has to start over each time never finishes, and the
# temptation at that point is to report the partial as if it were whole.
#
# So an existing ledger is APPENDED TO, not truncated: any script already
# named in it is skipped. Delete the file to force a clean pass. The rows are
# keyed by script name in column 1, which is the same key the comparison uses.
touch "$OUT"
already=$(cut -d' ' -f1 "$OUT" | sed '/^$/d' | sort -u)
[ -z "$already" ] || echo "resuming: $(printf '%s\n' "$already" | grep -c .) row(s) already measured"

for s in "${SCRIPTS[@]}"; do
  if printf '%s\n' "$already" | grep -qxF "$s"; then
    echo "skipped (already in $OUT): $s"
    continue
  fi
  if [ "$DEADLINE" -gt 0 ] && [ "$((SECONDS + BUDGET))" -gt "$DEADLINE" ]; then
    echo "STOPPING CLEANLY at the overall deadline: ${SECONDS}s used, a further"
    echo "${BUDGET}s would exceed ${DEADLINE}s. Re-run to resume; nothing was"
    echo "interrupted mid-harness."
    break
  fi
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

  # A TIMEOUT IS NOT A MEASUREMENT, so it is NOT written to the ledger. 124 is
  # `timeout`'s own code for "I killed it"; recording it would freeze a budget
  # artefact into a file whose whole purpose is to be compared against another
  # run, and the resume above would then never retry it. Left unrecorded, the
  # next call with a larger budget picks it up.
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    printf '%-42s TIMED OUT at %ss - NOT recorded; re-run with a larger budget\n' "$s" "$BUDGET"
    rm -f "$log"
    continue
  fi

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
measured=$(cut -d' ' -f1 "$OUT" | sed '/^$/d' | sort -u | grep -c .)
echo "ledger $OUT holds $measured of ${#SCRIPTS[@]} rows"
[ "$measured" -eq "${#SCRIPTS[@]}" ] \
  && echo "COMPLETE: every script in the container has been measured." \
  || echo "INCOMPLETE: $(( ${#SCRIPTS[@]} - measured )) still to measure. Re-run to resume."
