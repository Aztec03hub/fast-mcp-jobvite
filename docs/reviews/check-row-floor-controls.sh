#!/usr/bin/env bash
# POSITIVE CONTROLS for the row floors that have never been watched fire.
#
# WHY THIS EXISTS. `docs/reviews/check-row-floor-control.sh` proved the floor
# mechanism on ONE harness, `check-u15-gate-amputation.sh`. Nine others were
# written to the same shape and never watched. Same shape is an argument, not
# a measurement, and on this project same-shape code has failed differently
# more than once: four of these harnesses print a bare `N/M controls fired.`
# with no `##########` prefix, and `check-u15-gate-amputation.sh` had no row
# counter at all until task #79 added one - it printed the same closing
# sentence and exited 0 with four of its five rows deleted.
#
# WHAT ONE ROW OF THIS CONTROL PROVES, per harness:
#   1. the floor's comparison FIRES (it is not inverted, and the counter
#      variable is spelled the way the comparison spells it),
#   2. the harness EXITS with its own documented failure code rather than
#      swallowing it,
#   3. the counter TRACKS ROWS - deleting k row invocations moves the
#      printed count down by exactly k. This is the property an
#      impossible-floor run cannot reach, and it is the one that was
#      actually broken on `check-u15-gate-amputation.sh`.
#
# WHY NOT THE `ROW_FLOOR` ENVIRONMENT OVERRIDE that ROW-FLOORS-REPORT.md §8
# proposed. It costs the same one run per harness, so it buys no time. It
# would add a lowering-capable env surface to ten production harnesses; it
# would break `docs/reviews/check-row-floors.py`, whose floor regex is
# `^\s*ROW_FLOOR=(\d+)\s*$` and would not match `ROW_FLOOR="${ROW_FLOOR:-9}"`;
# and it proves strictly less, because raising the floor fires whatever the
# counter contains - including a counter wired to nothing. Deleting rows is
# the amputation; raising the floor is only a mutation of the threshold.
#
# HOW MANY ROWS EACH ONE DELETES. Exactly `rows - floor + 1`, the minimum
# that takes the count below the floor - which is 1 for a TIGHT floor and
# more for a SLACK one. `check-u7-resilience-controls.sh` needs SIX, and that
# number is the finding: five rows can be deleted from it today without its
# floor noticing.
#
# NOT A CI GATE, on purpose: it edits a tracked file in the working tree, and
# it refuses to run when that file is already dirty. It restores by
# byte-comparison against a backup rather than by re-editing, because a `sed`
# that matches nothing succeeds silently. The backup is taken BEFORE the trap
# is armed: armed first, an abort on the cleanliness check would fire the trap
# and copy the empty file `mktemp` just made over the harness.
#
#   docs/reviews/check-row-floor-controls.sh --list
#   docs/reviews/check-row-floor-controls.sh check-u3-audit-controls.sh
#
# ONE AT A TIME. These harnesses mutate `src/` for the length of their run.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# TWO CONSUMERS, TWO DIFFERENT CLAIMS, AND DO NOT CONFLATE THEM.
# `check-row-floor-exactness.py` reads columns 1-3 of this table and checks
# STATICALLY that each floor equals its harness's row count. THIS script
# reads all five and WATCHES the floor fire by removing real rows.
#
# R12-M1: check-u15-gate-amputation.sh WAS MISSING FROM THIS TABLE. The
# container held 24 harnesses carrying a literal ROW_FLOOR and the table named
# 23, so that one harness's floor was never compared to a live row count. It
# was TIGHT (5 rows, ROW_FLOOR=5), so the gap was latent rather than live.
#
# It was left out on the argument that `check-row-floor-control.sh` - singular -
# already watches it fire. That argument is CORRECT and it is about the FIRING
# claim; the exactness claim is a different question about a different number,
# and evidence for one is not coverage for the other. So it is a row here rather
# than an exemption, and it costs one line instead of an exemption register that
# a reader would have to follow to a second file to learn the harness is covered
# at all. The two controls overlapping on one harness is not a defect.
#
# check-row-floor-exactness.py enumerates a CONTAINER for a literal floor and
# FAILS unless that set EQUALS this table's, in both directions - so the next
# harness cannot be added without being covered, which is the only form of this
# fix that does not need someone to remember.
#
# THAT SENTENCE USED TO READ "enumerates scripts/*.sh for a literal ROW_FLOOR",
# AND THE GUARANTEE HAD ALREADY STOPPED HOLDING WHEN IT DID (#187). Three
# floors arrived outside that glob in one night - #131's and #149's probe
# floors under docs/reviews/, and #185's `arm_floor` in a `.py` under scripts/ -
# and every one of them is wired into CI. They were not missing from this
# table; they were outside the container BY CONSTRUCTION, so the equality had
# nothing to say about them and reported a clean pass over 25 of 29 members.
# A container bounded by PATH+SUFFIX decays the moment its members move, which
# is #115's ruling arriving from the other side.
#
# The container is now every tracked `.py`/`.sh` under `docs/reviews/` and
# `scripts/` carrying an identifier whose NAME contains `floor` assigned an
# integer literal - the same two directories `check-checkers-are-wired.py` was
# widened to at #153. The spelling is derived, not listed: `ROW_FLOOR=12`,
# `arm_floor = 9` and a bare `floor = 14` are all live today and a fourth
# would be caught without an edit here.
#
# The exactness claim covers all 24 rows below, and SO DOES THE FIRING CLAIM
# NOW. #91 watched the first nine; #102 watched the remaining fourteen at
# `0c25ae3` and found all of them tight, with the evidence written up in
# `docs/worklogs/FLOOR-FIRING-REPORT.md`; `check-u15-gate-amputation.sh` was
# watched by the singular `check-row-floor-control.sh` and has been re-watched
# through this script since it became row 24 (R12-M1). Every row here has been
# seen to fire.
#
# R12-L1: THESE LINES SAID THE OPPOSITE UNTIL NOW, and the shape is worth
# keeping. They read *"the fourteen added afterwards have been checked but never
# watched ... Task #102 is the remainder"* for as long as #102 had been closed,
# because `0c25ae3` added a worklog and touched no code - `git diff 0c25ae3^
# 0c25ae3 --stat` is one file. A control that UNDERSTATES its own coverage and
# points at a closed task is still a control nobody can read correctly, and the
# fix is to rewrite the sentence rather than append a correction under it.
#
# What `--list` prints is still the table, not the evidence. The evidence is the
# worklog and a run of this script.
#
# For those fourteen the ERE and the EXTRA were DERIVED per harness and
# checked rather than assumed: each has exactly ONE counter increment and it
# sits INSIDE its row function, so EXTRA is 0. The method was validated
# against `check-harness-anchors-controls.sh`, which has TWO increments -
# one inside, one at top level for its inline F1 row - and is the reason
# that row's EXTRA is 1. Without that control an ERE-only count would read
# a low count against a low floor as "tight".
#
# harness | row-invocation ERE | rows the harness counts that the ERE canNOT
# match | the exit code that harness uses for a floor breach
#
# THE THIRD COLUMN IS NOT DECORATION. `check-harness-anchors-controls.sh`
# has nine rows and only eight `row "..."` call sites: its F1 row is written
# inline, incrementing TOTAL directly. A control that enumerated rows by
# grepping the call sites alone would have predicted 8 and reported a
# mismatch against a perfectly healthy harness.
#
# THE FOURTH COLUMN IS NOT DECORATION EITHER. `check-u11-advisory-controls.sh`
# exits 6 on a floor breach, not 1. A control asserting `rc -eq 1` everywhere
# would have called it broken.
TABLE="
check-harness-anchors-controls.sh|^row \"|1|1|cmd
check-suite-floor-amputation.sh|^amputate \"|0|1|cmd
check-u0-test-controls.sh|^run_control \"|0|1|cmd
check-u1-boot-controls.sh|^control \"|0|1|cmd
check-u11-advisory-controls.sh|^control (MUT|AMP) |0|6|cmd
check-u15-gate-controls.sh|@@.*@@.*@@|0|1|data
check-u3-audit-controls.sh|^run_mutation \"|0|1|cmd
check-u4-client-controls.sh|^run_mutation \"|0|1|cmd
check-u7-resilience-controls.sh|^mutate \"|0|1|cmd
check-body-cap-amputation.sh|^amputate \"|0|1|cmd
check-body-cap-controls.sh|^mutate \"|0|1|cmd
check-critical-coverage-amputation.sh|^amputate \"|0|1|cmd
check-log-redaction-amputation.sh|^amputate \"|0|1|cmd
check-u10-write-controls.sh|^mutate \"|0|1|cmd
check-u12-jobfeed-controls.sh|^mutate \"|0|1|cmd
check-u14-arguments-controls.sh|^mutate \"|0|1|cmd
check-u5-jobs-amputation.sh|^amputate \"|0|1|cmd
check-u5-jobs-controls.sh|^mutate \"|0|1|cmd
check-u6-paging-amputation.sh|^amputate \"|0|1|cmd
check-u6-paging-controls.sh|^mutate \"|0|1|cmd
check-u8-candidates-amputation.sh|^amputate \"|0|1|cmd
check-u8-candidates-controls.sh|^mutate \"|0|1|cmd
check-u9-http-controls.sh|^mutate \"|0|1|cmd
check-u15-gate-amputation.sh|^report \"|0|1|cmd
check-mirror-liveness-controls.sh|^(row|amputate|transport) \"|0|1|cmd
docs/reviews/probe-gate-swallowed-exceptions.py|row\(\n\s*\"(?P<label>[A-Z])\.|0|1|static
scripts/check-secrets-baseline.py|arm\(\n\s*\"(?P<label>C[0-9]+) |0|1|static
docs/reviews/probe-131-gate-state.sh|COMPUTED|0|1|static
docs/reviews/probe-wired-checker-amputation.py|COMPUTED|0|1|static
docs/reviews/check-brief-report-refs-controls.sh|^ *row \"|0|1|cmd
docs/reviews/probe-mirror-zero-refs.sh|^row |1|1|cmd
docs/reviews/check-row-floor-exactness.py|arm\(\n\s*\"(?P<label>A[0-9]+) |0|1|static
"

list_harnesses() { printf '%s\n' "$TABLE" | sed '/^$/d' | cut -d'|' -f1; }

if [ "${1:-}" = "--list" ]; then list_harnesses; exit 0; fi
if [ "$#" -ne 1 ]; then
  echo "usage: $0 <harness-name>|--list" >&2
  exit 2
fi

TARGET="$1"
# `cut -f2` would truncate check-u11's ERE at the `|` inside `(MUT|AMP)`, so
# the row fields are split from the LAST two delimiters inward, not the first.
ROW=$(printf '%s\n' "$TABLE" | sed '/^$/d' | grep -F "$TARGET|" || true)
if [ -z "$ROW" ]; then
  echo "ABORT: $TARGET is not in this control's table. Known:" >&2
  list_harnesses >&2
  exit 2
fi
MODE="${ROW##*|}";     rest="${ROW%|*}"
WANT_RC="${rest##*|}"; rest="${rest%|*}"
EXTRA="${rest##*|}";   rest="${rest%|*}"
ROW_RE="${rest#*|}"

# COLUMN 1 IS A PATH, and a bare name still means `scripts/<name>` (#187).
# It had to become a path because the container this table must EQUAL is no
# longer one directory: `check-row-floor-exactness.py` used to enumerate
# `scripts/*.sh`, and three floors moved outside that glob in one night.
case "$TARGET" in
  */*) S="$REPO/$TARGET" ;;
  *)   S="$REPO/scripts/$TARGET" ;;
esac
[ -f "$S" ] || { echo "ABORT: $S does not exist - prove the path resolves"; exit 2; }

# MODE `static`: EXACTNESS ONLY, AND THE REFUSAL IS THE POINT.
#
# Everything below this line is bash surgery - it neutralises a row with the
# `:` builtin, syntax-checks with `bash -n`, runs the file with `bash`, and
# reads a `HARNESS-RESULT` line emitted by `scripts/lib/harness-result.sh`,
# which is a bash library. None of that applies to a Python harness, and
# running it anyway would produce a red that says nothing about a floor.
#
# So a `static` row is NOT an inoperative table entry. Columns 1-3 are fully
# live: `check-row-floor-exactness.py` reads them and holds those harnesses to
# the same equality as every other row - that is what put them in the table.
# Columns 4-5 have no meaning here, and this refuses rather than pretending.
#
# WHAT IS STILL MISSING, NAMED SO IT CANNOT PASS FOR DONE: nobody has watched
# these two floors FIRE. Task #194 is the Python arm of this control.
if [ "$MODE" = static ]; then
  echo "REFUSED: $TARGET is a mode=static row."
  echo "  This control mutates bash and reads a bash library's canonical line."
  echo "  $TARGET is not bash, so an arm here would measure the interpreter."
  echo "  Its EXACTNESS is checked - check-row-floor-exactness.py names it."
  echo "  Its FIRING is not watched by anything yet; that is task #194."
  exit 4
fi

# A dirty subject file means someone else is mid-edit; measuring it would
# measure them, not the floor.
# `git status --porcelain`, NOT `git diff --quiet`. `git diff` compares the
# worktree to the INDEX, so a file edited and then `git add`-ed reads CLEAN
# and this guard waves it through. Measured: modify + `git add` gives
# `git diff --quiet` exit 0 and `--porcelain` a non-empty `M `.
# THE ONE SANCTIONED BYPASS, AND IT IS NAMED. `probe-floor-checker-planted-
# defect.sh` is the negative control FOR this file: it plants a defect into the
# subject on purpose and needs this control to measure the planted version.
# It used to get that by STAGING the plant, because the guard here was
# `git diff --quiet` and `git add` made the worktree match the index - the
# blindness was the mechanism, written down in that probe's header as if it
# were a technique. Widening the guard broke it, which is how the coupling was
# found. An opt-in the caller must set BY NAME is the same capability with the
# dependency declared, so the next person to harden this guard sees who relies
# on it instead of discovering it from a red probe.
if [ "${ROW_FLOOR_CONTROL_ALLOW_PLANTED:-0}" != "1" ] &&
   [ -n "$(git -C "$REPO" status --porcelain -- "$S")" ]; then
  echo "ABORT: $S has uncommitted changes (staged or not); refusing to"
  echo "       measure someone else's tree"
  exit 3
fi

# THE FLOOR IS DERIVED FROM THE HARNESS, never typed here. A second copy of
# the number is exactly the defect this branch keeps finding.
FLOOR=$(grep -oE '^[[:space:]]*ROW_FLOOR=[0-9]+[[:space:]]*$' "$S" | grep -oE '[0-9]+')
case "$FLOOR" in
  ''|*[!0-9]*) echo "ABORT: no literal ROW_FLOOR=<n> in $TARGET"; exit 9 ;;
esac

MATCHED=$(grep -cE "$ROW_RE" "$S")
ROWS=$((MATCHED + EXTRA))
DELETE=$((ROWS - FLOOR + 1))
EXPECT=$((ROWS - DELETE))

echo "harness            : $TARGET"
echo "floor (from source): $FLOOR"
echo "rows               : $ROWS  ($MATCHED matched by the ERE + $EXTRA inline)"
echo "rows to delete     : $DELETE   (rows - floor + 1)"
echo "expected count     : $EXPECT   (must print as $EXPECT/$FLOOR)"

if [ "$DELETE" -lt 1 ]; then
  echo "::error::the floor is at or above the row count already; this harness is"
  echo "         RED before any deletion and the control cannot attribute an exit."
  exit 9
fi
if [ "$DELETE" -gt "$MATCHED" ]; then
  echo "ABORT: need to delete $DELETE rows but the ERE matches only $MATCHED"
  exit 9
fi

B="$(mktemp)"
cp "$S" "$B"
trap 'cp "$B" "$S"; rm -f "$B" "$B.out"' EXIT

STARTS=$(grep -nE "$ROW_RE" "$B" | head -n "$DELETE" | cut -d: -f1 | paste -sd, -)
echo "deleting rows at lines: $STARTS"

# HOW A ROW IS REMOVED, and why the obvious way is wrong.
#
# THE FIRST VERSION OF THIS SCRIPT DELETED LINES: the call plus every
# following line held by a trailing backslash. That reads the continuation
# the way a person skimming reads it, and it is WRONG, because a row's
# arguments may themselves contain newlines. `check-u7-resilience-controls.sh`
# row M2 passes a single-quoted Python fragment spanning four lines; the
# backslash rule stopped at the first of them and left the remaining three as
# loose shell. It PASSED every check that version had - `cmp` saw a change,
# `bash -n` parsed the wreckage, the row count fell by the right amount - and
# the only visible trace was an empty file named `=` left in the repository
# root by the orphaned fragment. Measured, not reasoned about.
#
# So the extent of a row is not computed here at all. Prefixing the call with
# the `:` builtin hands the whole logical command - quotes, embedded newlines
# and all - to bash's own parser, which consumes it and does nothing with it.
# The row does not run and is not counted, which is exactly what a lost row
# is. `data` rows are lines in a here-document rather than commands, so those
# are deleted outright; a `:` in front of one would only edit a data field.
if [ "$MODE" = cmd ]; then
  # `:` still EXPANDS its arguments, so a row carrying a command substitution
  # would execute it. Refuse rather than measure that.
  if awk -v starts="$STARTS" '
      BEGIN { n = split(starts, a, ","); for (i = 1; i <= n; i++) kill[a[i]] = 1 }
      NR in kill { on = 1 }
      on && /^[[:space:]]*$/ { on = 0 }
      on { print }' "$B" | grep -qE '\$\(|`'; then
    echo 'ABORT: a row in range carries a command substitution; the : builtin would run it'
    exit 9
  fi
  awk -v starts="$STARTS" '
    BEGIN { n = split(starts, a, ","); for (i = 1; i <= n; i++) kill[a[i]] = 1 }
    NR in kill { print ": " $0; next }
    { print }' "$B" > "$S"
else
  awk -v starts="$STARTS" '
    BEGIN { n = split(starts, a, ","); for (i = 1; i <= n; i++) kill[a[i]] = 1 }
    NR in kill { next }
    { print }' "$B" > "$S"
fi

if cmp -s "$S" "$B"; then
  echo "ABORT: the deletion did NOT land - the file is unchanged"
  exit 9
fi

# THE CONTAINER CHECK. The row invocations still matching the ERE must have
# dropped by exactly DELETE. This is what catches a neutralisation that
# landed on the wrong line, or landed on fewer lines than it claimed.
LEFT=$(grep -cE "$ROW_RE" "$S")
echo "row invocations still matching: $LEFT (was $MATCHED, must be $((MATCHED - DELETE)))"
if [ "$LEFT" -ne "$((MATCHED - DELETE))" ]; then
  echo "ABORT: $DELETE rows were meant to go and $((MATCHED - LEFT)) did"
  exit 9
fi

if ! bash -n "$S"; then
  echo "ABORT: the deletion left the harness syntactically invalid; a syntax"
  echo "       error exits non-zero too and would be read as the floor firing."
  exit 9
fi

echo "--- running the harness with $EXPECT of its $ROWS rows ---"
PYTHONDONTWRITEBYTECODE=1 bash "$S" > "$B.out" 2>&1
rc=$?

cp "$B" "$S"
cmp -s "$S" "$B" && echo "restored: byte-identical to the backup"
# AGAINST THE INDEX, AND THE MESSAGE USED TO SAY "HEAD" - it was wrong.
# `git diff` compares the worktree to the INDEX, and that is the right
# question HERE for two reasons. The restore above is `cp` from a backup
# taken at start, so "restored" means "back to what it was", not "back to
# HEAD". And this control is itself run under
# `probe-floor-checker-planted-defect.sh`, which STAGES a planted defect
# before invoking it - so under that probe the correct post-state really
# does differ from HEAD, and a HEAD comparison would fail every arm.
git -C "$REPO" diff --quiet -- "$S" \
  && echo "restored: and identical to the index" \
  || { echo "::error::RESTORE FAILED - $S still differs from the index"; exit 9; }

echo "--- the harness's canonical result line ---"
# ONE LINE, PARSED BY FIELD NAME. Task #107.
#
# WHAT USED TO BE HERE. A `grep -E` alternation of THREE breach-message shapes,
# and below it a `floor_line()` holding the SAME three as separate greps - two
# hand-kept lists of the prose a healthy harness might print, which had to be
# edited in lockstep. Their own comment recorded that the list "HAS NOW MISSED
# ONE THREE TIMES", and when the display knew two shapes and the assertion knew
# three, this control printed "CONTROL FIRED" above a BLANK evidence block: a
# verdict with nothing under it.
#
# The lists are DELETED rather than extended. Every script under `scripts/` now
# prints one canonical line from `scripts/lib/harness-result.sh`, and this
# control reads that line and NOTHING else. A harness may reword its prose
# freely; a fourth prose shape can no longer break this file, because no prose
# shape is named in it.
#
# THE LINE IS SELECTED BY `name=`, not by position. `tail -1` alone would read
# the wrong line whenever a gate echoes the output of the harness it ran.
RESULT=$(grep -E "^HARNESS-RESULT name=$TARGET " "$B.out" | tail -1)
echo "${RESULT:-<the harness printed no canonical line at all>}"
echo "exit with $DELETE row(s) deleted: $rc (must be $WANT_RC)"

# Field extraction with no shape list of its own: the line is `key=value` pairs
# separated by spaces, so it is split on spaces and the key is looked up by
# name. A field added to the grammar later cannot break this.
field() { printf '%s\n' "$1" | tr ' ' '\n' | sed -n "s/^$2=//p"; }

ok=0
if [ -z "$RESULT" ]; then
  echo "::error::the harness printed NO 'HARNESS-RESULT name=$TARGET ...' line."
  echo "         Either it does not source scripts/lib/harness-result.sh, or an"
  echo "         EXIT trap set later in it replaced the armed one without"
  echo "         chaining harness_result_emit. A missing line is NOT a pass:"
  echo "         nothing here can say whether the floor fired."
  echo "--- last 25 lines of the run ---"
  tail -25 "$B.out"
  ok=1
else
  GOT_ROWS=$(field "$RESULT" rows)
  GOT_FLOOR=$(field "$RESULT" floor)
  GOT_STATUS=$(field "$RESULT" status)

  # THREE SEPARATE CLAIMS, EACH REPORTED SEPARATELY. The old shape match
  # collapsed them into one grep, so a harness whose counter did not track rows
  # failed with the same message as one whose floor never fired.
  if [ "$GOT_ROWS" != "$EXPECT" ]; then
    echo "::error::the harness reported rows=$GOT_ROWS after $DELETE row(s) were"
    echo "         deleted; it must report $EXPECT. The counter does not track"
    echo "         rows - which is the defect that was actually broken on"
    echo "         check-u15-gate-amputation.sh, and the one an impossible-floor"
    echo "         run cannot reach."
    ok=1
  fi
  if [ "$GOT_FLOOR" != "$FLOOR" ]; then
    echo "::error::the harness reported floor=$GOT_FLOOR, but its source says"
    echo "         ROW_FLOOR=$FLOOR. The reported floor and the compared floor"
    echo "         are not the same value."
    ok=1
  fi
  if [ "$GOT_STATUS" != "breach" ]; then
    echo "::error::the harness reported status=$GOT_STATUS, wanted breach. A"
    echo "         'refused' means it never reached its floor comparison at all;"
    echo "         an 'ok' means the comparison ran and did not fire."
    ok=1
  fi
fi
[ "$rc" -eq "$WANT_RC" ] || {
  echo "::error::exit $rc, wanted $WANT_RC - the floor's exit is swallowed or"
  echo "         something else failed first."
  ok=1
}
rm -f "$B.out"
[ "$ok" -eq 0 ] || exit 1
echo "CONTROL FIRED: $TARGET loses $DELETE row(s), reported rows=$EXPECT floor=$FLOOR status=breach, exiting $rc."
