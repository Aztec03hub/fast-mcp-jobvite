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
  echo "  per-script-seconds  timeout for ONE harness (default 1800). A run that" >&2
  echo "                      exceeds it is NOT recorded - a timeout is not a" >&2
  echo "                      measurement - so a later, larger budget retries it." >&2
  echo "                      THE DEFAULT WAS 900 AND COULD NOT MEASURE ITS OWN" >&2
  echo "                      CONTAINER: check-u9-http-amputation.sh takes 1040s" >&2
  echo "                      on a quiet machine, so a default-argument run left" >&2
  echo "                      that row permanently unmeasured and ended" >&2
  echo "                      INCOMPLETE. 1800 was chosen from that measurement," >&2
  echo "                      not from taste. #108's finding that 900 had ~15x" >&2
  echo "                      headroom was true of u0 at 711s and does NOT" >&2
  echo "                      generalise - u0 is not the slowest member." >&2
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
BUDGET="${2:-1800}"

# THE RUN-STATE FILE (task #131). Sourced, not reimplemented: the path and the
# format live in one file so this probe and the restorer cannot disagree about
# where to look.
# shellcheck source=lib/harness-state.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-state.sh"

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

# THE RESTORE REFERENCE, resolved ONCE and while the tree is provably clean.
# Read AFTER the guard above on purpose: at this point worktree, index and HEAD
# all agree, so this sha is a reference that cannot destroy staged work when a
# restore later writes from it - there is none to destroy. Resolved once rather
# than per row so that a pass cannot silently straddle two commits.
HEAD_SHA=$(git -C "$REPO" rev-parse HEAD)
[ -n "$HEAD_SHA" ] || { echo "ABORT: could not resolve HEAD" >&2; exit 3; }

# THE SLOWEST ROW, so the next person sizing the budget has a MEASUREMENT
# rather than a guess (task #146, F2). The 900s default stood because #108
# measured u0 at 711s and concluded there was headroom - a conclusion true of
# u0 and false of the container, because u0 is not the slowest member.
slowest_secs=0
slowest_name="(none completed)"

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
#
# `#`-PREFIXED LINES ARE NOT ROWS. The ledger carries a completeness banner
# (written at the end of every pass), and both readers of this file - the
# resume below and `compare-harness-exit-codes.sh` - key on column 1. A banner
# read as a row would become a harness named `#`, present on both sides, and
# the comparison would report it as a compared row. Both readers strip it.
touch "$OUT"
already=$(grep -v '^#' "$OUT" | cut -d' ' -f1 | sed '/^$/d' | sort -u)
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
  # RECORD THE OWNER BEFORE MUTATING, NOT AFTER (task #131). The tree is clean
  # at this instant - the pre-flight refused to start otherwise, and the
  # end-of-row check below refuses to continue otherwise - so HEAD, the index
  # and the worktree all agree, and that is exactly the precondition that makes
  # this commit a safe restore reference. Written BEFORE the harness starts
  # because a state file written afterwards is not written at all for the run
  # that gets killed, which is the only run it exists for.
  harness_state_begin "$REPO" "$s" "$HEAD_SHA"
  timeout --signal=TERM --kill-after=30 "$BUDGET" bash "$REPO/scripts/$s" >"$log" 2>&1
  rc=$?
  took=$((SECONDS - start))
  if [ "$took" -gt "$slowest_secs" ]; then slowest_secs=$took; slowest_name=$s; fi

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

    # THE TREE CHECK BELONGS HERE TOO, AND ITS ABSENCE NAMED THE WRONG HARNESS
    # (task #146, F1). This branch used to `continue` straight past the
    # end-of-row check below, so the ONE exit path most likely to strand a
    # mutation - a harness killed mid-row, which never reaches its own restore -
    # was the single path that never looked at the tree. The dirt was then found
    # one iteration later and attributed to `$s`, which by then names the NEXT
    # script.
    #
    # MEASURED, and this is the whole argument: `check-u9-http-amputation.sh`
    # timed out at 900s and stranded a u9 amputation. The very next row,
    # `check-u9-http-controls.sh`, was recorded `rc=3 status=refused` and then
    # named as the script that "LEFT THE TREE DIRTY" - when in fact it had
    # REFUSED TO START precisely because the tree was already dirty, which is
    # its guard working correctly. On a restored tree it re-measured
    # `rc=0 status=ok` in 42s. A reader following that message would have
    # audited a blameless harness and never looked at the one that did it.
    #
    # THE TWO MESSAGES ARE KEPT APART ON PURPOSE. A harness killed mid-row and a
    # harness that completed and failed to restore are different events with
    # different remedies, and this repo's own gate says one section down why a
    # message that misdescribes what happened sends the next reader to the wrong
    # place.
    if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
      echo "::error::$s WAS KILLED AT ${BUDGET}s AND STRANDED ITS MUTATION." >&2
      echo "         A harness killed mid-row never reaches its restore: SIGKILL" >&2
      echo "         runs no trap and no finally. This is NOT a defect in the" >&2
      echo "         next harness - that one will refuse to start on the dirty" >&2
      echo "         tree and look like the culprit." >&2
      echo "         DO NOT COMMIT FROM THIS TREE." >&2
      git -C "$REPO" status --porcelain >&2
      echo "         Put it back with:" >&2
      echo "           bash docs/reviews/restore-stranded-mutation.sh --restore-only" >&2
      exit 4
    fi
    # Nothing stranded, so this row's owner is discharged.
    harness_state_end "$REPO"
    continue
  fi

  printf '%-42s rc=%-4s status=%-8s\n' "$s" "$rc" "$status" >> "$OUT"
  printf '%-42s rc=%-4s status=%-8s %ss\n' "$s" "$rc" "$status" "$took"
  rm -f "$log"

  # A harness that did not restore the tree poisons every run after it.
  #
  # `git status --porcelain`, NOT `git diff --quiet`, AND THE PROBE USED TO
  # DISAGREE WITH ITSELF ABOUT THIS. The pre-flight at the top of this file
  # already refuses to start unless `--porcelain` is empty, and states why:
  # `git diff` compares the worktree to the INDEX, so a file edited and then
  # `git add`-ed reads CLEAN. This check was the weaker instrument, which meant
  # a harness that mutated and staged - or that left an untracked artefact
  # behind - walked past the guard that exists to catch exactly that.
  #
  # WHY THE STRICTER READING IS SAFE HERE, rather than a source of false
  # aborts. The pre-flight established an EMPTY porcelain at the start of the
  # pass, so anything `--porcelain` reports now appeared during this row and is
  # this harness's doing. That is the same before/after reasoning
  # `scripts/ci-harness-gate.sh` uses, and it is the house instrument.
  if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
    echo "::error::$s LEFT THE TREE DIRTY. Stopping: every later row would" >&2
    echo "         measure its mutation rather than its own subject." >&2
    echo "         This harness RAN TO COMPLETION and failed to restore - which" >&2
    echo "         is a different event from the timeout branch above, where a" >&2
    echo "         harness was killed before it could reach its restore." >&2
    git -C "$REPO" status --porcelain >&2
    echo "         Put it back with:" >&2
    echo "           bash docs/reviews/restore-stranded-mutation.sh --restore-only" >&2
    exit 4
  fi

  # The row completed AND the tree is clean, so this row's owner is discharged.
  # Cleared HERE and nowhere earlier: a state file removed before the tree is
  # verified would erase the evidence at the one moment it is needed.
  harness_state_end "$REPO"
done

# THE PASS ITSELF IS OVER, so no row owns the tree any more. A state file that
# survives to here would make the next `--restore-only` report a stranded
# mutation that does not exist.
harness_state_end "$REPO"

echo
measured=$(grep -v '^#' "$OUT" | cut -d' ' -f1 | sed '/^$/d' | sort -u | grep -c .)
echo "ledger $OUT holds $measured of ${#SCRIPTS[@]} rows"

# THE SLOWEST ROW THAT ACTUALLY COMPLETED, and the qualifier is the point. A
# maximum computed over rows that all died at a timeout is a statement about
# the BUDGET, not about the harnesses - this repo has already been bitten by
# caps sized from runs that never reached the step they were sizing. Only
# completed rows update it, and a pass in which nothing completed says so.
echo "slowest COMPLETED row this pass    : $slowest_name at ${slowest_secs}s"
echo "  (per-script budget in force: ${BUDGET}s. A row that TIMED OUT is not in"
echo "   this number - it has no duration, only a lower bound of ${BUDGET}s.)"

# THE BANNER GOES INSIDE THE LEDGER, not only on stdout (task #146, F2). A
# caller who reads only the file used to get 36 rows and no indication that a
# 37th existed and had timed out - the pass was loud on the terminal and silent
# in its own artefact. Stale banners are stripped rather than appended to, so
# the file never carries two contradictory completeness claims.
tmp_ledger=$(mktemp)
grep -v '^#' "$OUT" > "$tmp_ledger"
cat "$tmp_ledger" > "$OUT"
rm -f "$tmp_ledger"

if [ "$measured" -eq "${#SCRIPTS[@]}" ]; then
  echo "COMPLETE: every script in the container has been measured."
  echo "# COMPLETE: $measured of ${#SCRIPTS[@]} scripts/*.sh measured at budget ${BUDGET}s." >> "$OUT"
else
  echo "INCOMPLETE: $(( ${#SCRIPTS[@]} - measured )) still to measure. Re-run to resume."
  echo "# INCOMPLETE: $measured of ${#SCRIPTS[@]} scripts/*.sh measured at budget ${BUDGET}s." >> "$OUT"
  echo "# $(( ${#SCRIPTS[@]} - measured )) row(s) are MISSING, not passing. A timeout is not a" >> "$OUT"
  echo "# measurement, so it is never recorded - which makes an unmeasured row" >> "$OUT"
  echo "# INVISIBLE in the rows above. Re-run with a larger per-script budget." >> "$OUT"
  # Naming them costs nothing and turns a number the reader discounts into a
  # list the reader can act on - the same argument compare-harness-exit-codes.sh
  # makes for printing its missing rows by name.
  # RE-DERIVED FROM THE LEDGER, not reused from `$already`. `$already` is the
  # PRE-PASS snapshot; every row measured during this pass is absent from it,
  # so reusing it here would list rows this very run had just measured as
  # missing. Caught by reading, before it was ever run.
  now_measured=$(grep -v '^#' "$OUT" | cut -d' ' -f1 | sed '/^$/d' | sort -u)
  for s in "${SCRIPTS[@]}"; do
    printf '%s\n' "$now_measured" | grep -qxF "$s" || echo "#   MISSING: $s" >> "$OUT"
  done
fi
