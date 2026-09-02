#!/usr/bin/env bash
# #284: A FIXED /tmp PATH, TWO CONCURRENT RUNS, AND A VERDICT ASSEMBLED FROM
# ANOTHER PROCESS'S BYTES.
#
# THE MECHANISM. Every mutation harness here redirects pytest into a file and
# reads its verdict back out with `grep`. When that file has a FIXED name, two
# worktrees on one machine open the SAME INODE. Both hold independent offsets,
# so a rival's `>` truncate lands under this run's writer and the kernel leaves
# a NUL hole between the rival's short line and this run's far-out one. GNU grep
# 3.11 then classifies the file as BINARY, and binary is not an error:
#
#   - `grep -qE '^FAILED ...'` still MATCHES and still exits 0 -> the harness
#     records `killed by <test>` for a test THIS RUN NEVER FAILED. That is the
#     false kill #262 produced on check-u3-audit-controls.sh.
#   - `cap=$(grep -E '^FAILED ' "$OUT")` gets an EMPTY capture at EXIT 0, with
#     "binary file matches" on STDERR where no `2>&1` is looking. A reader
#     printing "$cap" prints nothing and calls it a clean row.
#
# WHY THIS PROBE EXISTS AT ALL, AND WHY IT IS DETERMINISTIC. CI can NEVER catch
# a regression of this class: the runner has one checkout and no second
# worktree, so no green run will ever reveal it - which is why it survived. And
# a probe that raced two real harnesses would measure a WINDOW, not a property:
# #262's genuine rival gave 0 hits in 3 trials. So the interleave here is
# ORDERED with an explicit fd rather than raced. That is the point: the question
# is whether the SHAPE admits the collision, not how often the dice land on it.
#
# ARM A is the BEFORE shape (one fixed path, both runs) and MUST show the false
# kill. ARM B is the AFTER shape (`mktemp` per run) and MUST show the correct
# verdict. Without ARM A this file would be an untested assertion that the fix
# was needed; without ARM B, an untested assertion that it worked.
#
# `-e` deliberately omitted, under ADR-0023: this probe reads the exit codes of
# greps that are EXPECTED to fail. `set -e` would take the script down on the
# first honest "not killed".
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 3

# shellcheck source=../../scripts/lib/harness-result.sh
. "$REPO_ROOT/scripts/lib/harness-result.sh"

WANT="test_arm1_the_killer_that_was_neutered"
# The verdict expression is READ OUT OF A REAL HARNESS, never retyped here. A
# copy would be free to agree with a harness that had drifted - the shape this
# repository keeps finding - and it is what makes ARM A a statement about the
# shipped code rather than about a string in this file.
HARNESS=scripts/check-u4-client-controls.sh
[ -f "$HARNESS" ] || { echo "ABORT: $HARNESS not found from $REPO_ROOT"; exit 3; }
if ! grep -q 'grep -qE "\^FAILED \$SUITE::\$want" "\$MUT_OUT"' "$HARNESS"; then
  echo "ABORT: could not find the verdict grep in $HARNESS. If the harness"
  echo "changed shape this probe is measuring nothing, and says so rather"
  echo "than passing on a stale copy."
  exit 3
fi

WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

ROWS=0
FIRED=0
row() {
  local label="$1" cond="$2"
  ROWS=$((ROWS + 1))
  if [ "$cond" = pass ]; then
    FIRED=$((FIRED + 1))
    echo "  ROW $ROWS PASSED: $label"
  else
    echo "  ROW $ROWS FAILED: $label"
  fi
}

# collide <path> - drive the interleave that two concurrent `>` writers on one
# inode produce. THIS RUN opens the path and writes 4 KiB of its own honest
# output while holding the offset; the RIVAL truncates the same inode and writes
# a `FAILED` line at offset 0; this run then writes its tail at offset 4096. The
# result is the rival's line, a NUL hole, and this run's tail - which is exactly
# the on-disk state a real pair of harnesses reaches, reproduced without a race.
collide() {
  local path="$1"
  {
    exec 3>"$path"
    head -c 4096 /dev/zero | tr '\0' '.' >&3
    echo >&3
    : >"$path"
    printf 'FAILED tests/test_jobvite_client.py::%s - AssertionError\n' "$WANT" >>"$path"
    echo "this run's own tail, written at offset 4097" >&3
    exec 3>&-
  }
}

echo "########## ARM A - the BEFORE shape: one FIXED path, shared by both runs"
# THE SUBJECT IS "ONE PATH, TWO WRITERS" - NOT THE STRING `/tmp`. The
# discriminator #284 selects on is a path that does not VARY per invocation, so
# a single shared name inside this run's own mktemp'd directory reproduces the
# property exactly, and leaves this probe safe to run beside itself. A literal
# /tmp name here would make the probe an instance of the defect it measures.
SHARED="$WORK/one-shared-name.txt"
collide "$SHARED"
nuls=$(tr -dc '\000' <"$SHARED" | wc -c)
echo "  file is $(wc -c <"$SHARED") bytes and holds $nuls NUL bytes"
row "the shared path holds NUL bytes - grep will call it binary" \
  "$([ "$nuls" -gt 0 ] && echo pass || echo fail)"

# THE HARNESS'S OWN VERDICT EXPRESSION, against the collided file.
if grep -qE "^FAILED tests/test_jobvite_client.py::$WANT" "$SHARED"; then a_v=killed; else a_v=not-killed; fi
echo "  verdict from the collided shared file: $a_v"
row "THE FALSE KILL: the shared path reports a kill this run never made" \
  "$([ "$a_v" = killed ] && echo pass || echo fail)"

# THE DISPLAY PATH, which is where the silence lives. stderr is deliberately NOT
# redirected into the capture - that is the whole reason the message is unseen.
a_cap=$(grep -E '^FAILED ' "$SHARED" 2>/dev/null); a_rc=$?
echo "  capture rc=$a_rc, capture length=${#a_cap} bytes"
row "the evidence capture is EMPTY at exit 0 - a match that prints nothing" \
  "$([ "$a_rc" -eq 0 ] && [ "${#a_cap}" -eq 0 ] && echo pass || echo fail)"
# WHAT GREP ACTUALLY SAID, on the channel nothing was reading. Captured to a
# file rather than piped: with `2>&1 >/dev/null` grep sees /dev/null on stdout
# and silently behaves like `-q`, printing nothing at all - a measurement that
# would have shown an EMPTY stderr and been read as "grep said nothing".
ERRF="$WORK/arm-a-stderr.txt"
grep -E '^FAILED ' "$SHARED" >"$WORK/arm-a-stdout.txt" 2>"$ERRF"
echo "  stderr: $(cat "$ERRF")"
row "grep announced the problem on STDERR, which no harness reads" \
  "$(grep -qi 'binary file' "$ERRF" && echo pass || echo fail)"
echo

echo "########## ARM B - the AFTER shape: mktemp, so the rival cannot reach it"
# The rival still runs, and still writes its `FAILED` line - into ITS OWN file,
# because that is what a per-run name means. This run reads only its own.
MINE="$(mktemp "$WORK/probe-284-mine-XXXXXX")"
THEIRS="$(mktemp "$WORK/probe-284-theirs-XXXXXX")"
{
  exec 3>"$MINE"
  head -c 4096 /dev/zero | tr '\0' '.' >&3
  echo >&3
  : >"$THEIRS"
  printf 'FAILED tests/test_jobvite_client.py::%s - AssertionError\n' "$WANT" >>"$THEIRS"
  echo "this run's own tail, written at offset 4097" >&3
  exec 3>&-
}
b_nuls=$(tr -dc '\000' <"$MINE" | wc -c)
echo "  this run's file is $(wc -c <"$MINE") bytes and holds $b_nuls NUL bytes"
row "the per-run path holds NO NUL bytes - the rival cannot reach this inode" \
  "$([ "$b_nuls" -eq 0 ] && echo pass || echo fail)"

if grep -qE "^FAILED tests/test_jobvite_client.py::$WANT" "$MINE"; then b_v=killed; else b_v=not-killed; fi
echo "  verdict from this run's own file: $b_v"
row "the per-run path reports NOT-KILLED, which is the truth" \
  "$([ "$b_v" = not-killed ] && echo pass || echo fail)"

# POSITIVE CONTROL. Rows 4 and 5 would both pass for a verdict expression that
# matched NOTHING - "not-killed" is the answer a broken regex gives to every
# question, and a fix that simply blinded the grep would look identical here.
printf 'FAILED tests/test_jobvite_client.py::%s - AssertionError\n' "$WANT" >>"$MINE"
if grep -qE "^FAILED tests/test_jobvite_client.py::$WANT" "$MINE"; then b_ctl=killed; else b_ctl=not-killed; fi
echo "  the same expression against a GENUINE failure in this run's file: $b_ctl"
row "a real kill in this run's own file still reads as a kill" \
  "$([ "$b_ctl" = killed ] && echo pass || echo fail)"
echo

# THE TALLY IS ASSERTED, NOT MERELY PRINTED (#262). A probe that printed
# "6/6" beside a status nothing derived from it is how a short tally rode out a
# green run. ROW_COUNT is the declared population, so a deleted row breaches
# here instead of shrinking the denominator until the ratio agrees with itself.
echo "########## ROWS: $FIRED/$ROWS passed"
harness_result_tally fired "$FIRED" "$ROWS"
ROW_COUNT=7
harness_result_ran "$ROWS" "$ROW_COUNT"
if [ "$ROWS" -ne "$ROW_COUNT" ]; then
  echo "::error::ROW COUNT MOVED - $ROWS rows ran against $ROW_COUNT declared."
  exit 1
fi
[ "$FIRED" -eq "$ROWS" ] || exit 1
echo "BOTH ARMS HELD: the fixed path admits a false kill; the per-run path does not."
