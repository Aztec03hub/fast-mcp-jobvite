#!/usr/bin/env bash
# THE CONTROL for task #146 F1 and task #131.
#
#   bash docs/reviews/control-stranded-mutation.sh
#
# WHAT IT PROVES, and why each arm is here rather than being a claim in prose.
#
#   A1  The probe's timeout branch names the harness that was KILLED, not the
#       innocent successor. This is #146's F1 stated as a measurement.
#   A2  A2 IS THE AMPUTATION, and without it A1 is worthless. The fix is CUT
#       OUT of a copy of the probe and A1's assertion is re-run against the
#       amputated copy, which must then name the WRONG harness. A control that
#       has never been seen to fail is a control nobody has seen work - this
#       repo has now measured that four separate times.
#   A3  --check reports a stranded mutation and changes NOTHING.
#   A4  --restore-only puts the file back, verified by cmp against the
#       recorded blob, and the tree is clean afterwards.
#   A5  A LIVE OWNER IS REFUSED. This is #131's subtler hazard: two worktrees
#       were dirty at the moment of a real stranding and BOTH were legitimate,
#       because probes were running in them. A tool that cleaned every dirty
#       tree would have destroyed live work.
#   A6  DIRT WITH NO STATE FILE IS REFUSED, not guessed at. Most harnesses
#       still write no state file, so this is the common case, and getting it
#       wrong is destructive rather than merely unhelpful.
#   A7  A clean tree with no state file is a clean result.
#
# IT NEVER RUNS AGAINST THE LIVE TREE. Everything happens in a scratch git repo
# built from nothing under a mktemp directory, with stub harnesses whose timing
# is chosen so the run is seconds rather than the real container's hours. The
# project rule is that a destructive thing is not tested by doing it here, and
# a killed mutation harness is exactly that.
#
# `-e` deliberately omitted: every arm reads an exit code of something expected
# to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS + 1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# assert_contains <haystack> <needle> <what>
#
# A FAILING ARM PRINTS THE OUTPUT IT JUDGED. Without that, a failure says only
# that a string was absent, and the reader cannot tell a real defect from a
# reworded message or an arm that never ran the thing it was judging - which is
# exactly the ambiguity this project keeps paying for. Bash `==` with a pattern
# on the right, never `grep -q` in a pipeline: a `grep -q` that exits on its
# first match takes SIGPIPE on long output and `pipefail` promotes it to 141, so
# a string that IS present reports as absent.
dump() {
  echo "  ---- last 25 lines of what the arm judged ----"
  printf '%s\n' "$1" | tail -25 | sed 's/^/  | /'
  echo "  ---------------------------------------------"
}
assert_contains() {
  if [[ "$1" == *"$2"* ]]; then ok "$3"; else
    bad "$3 (expected to find: $2)"
    dump "$1"
  fi
}
assert_absent() {
  if [[ "$1" == *"$2"* ]]; then bad "$3 (should NOT contain: $2)"; dump "$1"; else ok "$3"; fi
}
assert_rc() {
  if [ "$1" -eq "$2" ]; then ok "$3 (rc=$1)"; else bad "$3 (rc=$1, wanted $2)"; fi
}

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
REPO="$SANDBOX/repo"

# THE STATE FILE LIVES OUTSIDE THE REPO, and that is not incidental. Inside the
# tree it would be an untracked file, and the probe's pre-flight refuses to
# start on a non-empty `git status --porcelain` - so the probe would abort on
# its own bookkeeping. Proving that here is cheaper than rediscovering it.
export HARNESS_STATE_FILE="$SANDBOX/state"

echo "sandbox: $SANDBOX"
echo

# ---------------------------------------------------------------------------
# Build a scratch repo whose container is two stub harnesses.
# ---------------------------------------------------------------------------
mkdir -p "$REPO/scripts" "$REPO/src" "$REPO/docs/reviews/lib"

cat > "$REPO/src/target.py" <<'PY'
def guard(token):
    if not token:
        raise ValueError("missing token")
    return True
PY
ORIGINAL="$SANDBOX/original-target.py"
cp "$REPO/src/target.py" "$ORIGINAL"

# THE STRANDER. It mutates a tracked file and then outlives its budget, which
# is exactly the shape that stranded a real u9 amputation: killed between the
# mutation and the restore it would have done at the end.
cat > "$REPO/scripts/check-aaa-strander.sh" <<'SH'
#!/usr/bin/env bash
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$REPO/src/target.py" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
s = p.read_text()
old, new = "if not token:", "if False:"
assert s.count(old) == 1, "ANCHOR NOT UNIQUE"
p.write_text(s.replace(old, new))
PY
echo "HARNESS-RESULT name=check-aaa-strander.sh rows=1 floor=0 status=ok"
sleep 60          # outlives the probe's per-script budget; never restores
SH

# THE INNOCENT SUCCESSOR. It refuses to start on a dirty tree - which is its
# guard working - and that refusal is what got it blamed in the real incident.
cat > "$REPO/scripts/check-bbb-innocent.sh" <<'SH'
#!/usr/bin/env bash
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  echo "HARNESS-RESULT name=check-bbb-innocent.sh rows=0 floor=0 status=refused"
  exit 3
fi
echo "HARNESS-RESULT name=check-bbb-innocent.sh rows=1 floor=0 status=ok"
exit 0
SH

cp "$HERE/probe-harness-exit-codes.sh" "$REPO/docs/reviews/"
cp "$HERE/restore-stranded-mutation.sh" "$REPO/docs/reviews/"
cp "$HERE/lib/harness-state.sh" "$REPO/docs/reviews/lib/"

git -C "$REPO" init -q
git -C "$REPO" config user.email control@example.invalid
git -C "$REPO" config user.name control
git -C "$REPO" add -A
git -C "$REPO" commit -qm "scratch container"

if [ -n "$(git -C "$REPO" status --porcelain)" ]; then
  echo "::error::the scratch repo is dirty before any arm ran. Every arm below"
  echo "         would be measuring that instead of its subject."
  exit 2
fi

PROBE="$REPO/docs/reviews/probe-harness-exit-codes.sh"
RESTORE="$REPO/docs/reviews/restore-stranded-mutation.sh"

# ---------------------------------------------------------------------------
# A1 - the timeout branch names the harness that was KILLED
# ---------------------------------------------------------------------------
echo "A1: the probe names the killed harness, not its successor"
out=$(bash "$PROBE" "$SANDBOX/ledger" 3 2>&1); rc=$?

assert_rc "$rc" 4 "the probe stops with exit 4"
assert_contains "$out" "check-aaa-strander.sh WAS KILLED AT 3s AND STRANDED ITS MUTATION" \
  "the message names the STRANDER"
assert_absent "$out" "check-bbb-innocent.sh LEFT THE TREE DIRTY" \
  "the innocent successor is NOT blamed"
# The successor must not have run at all: the probe stops at the stranding.
assert_absent "$out" "HARNESS-RESULT name=check-bbb-innocent.sh" \
  "the successor never ran"
if [ -f "$HARNESS_STATE_FILE" ]; then
  ok "the state file SURVIVED the kill, which is what makes recovery possible"
else
  bad "the state file is gone; nothing can attribute the stranded mutation"
fi
if cmp -s "$ORIGINAL" "$REPO/src/target.py"; then
  bad "nothing was stranded - the arm did not reproduce the defect it tests"
else
  ok "the mutation really is stranded in the tree (cmp differs)"
fi
echo

# ---------------------------------------------------------------------------
# A3 - --check reports and changes nothing   (run before the restore, A4)
# ---------------------------------------------------------------------------
echo "A3: --check reports the stranding and changes nothing"
before_bytes=$(cksum < "$REPO/src/target.py")
out=$(bash "$RESTORE" --check --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 1 "--check exits 1 on a stranded mutation"
assert_contains "$out" "STRANDED MUTATION from check-aaa-strander.sh" \
  "--check names the owning harness"
after_bytes=$(cksum < "$REPO/src/target.py")
if [ "$before_bytes" = "$after_bytes" ]; then ok "--check left the file untouched"
else bad "--check MODIFIED the file"; fi
echo

# ---------------------------------------------------------------------------
# A5 - a LIVE owner is refused (run before A4, which clears the state)
# ---------------------------------------------------------------------------
echo "A5: a live owner is refused, so live work is never destroyed"
sleep 300 &
live_pid=$!
saved_state=$(cat "$HARNESS_STATE_FILE")
sed "s/^pid=.*/pid=$live_pid/" "$HARNESS_STATE_FILE" > "$HARNESS_STATE_FILE.tmp"
mv "$HARNESS_STATE_FILE.tmp" "$HARNESS_STATE_FILE"
out=$(bash "$RESTORE" --restore-only --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 3 "--restore-only REFUSES while the owner is alive"
assert_contains "$out" "IS STILL ALIVE" "it says the owner is running"
if cmp -s "$ORIGINAL" "$REPO/src/target.py"; then
  bad "it restored the file anyway - a live measurement would be corrupted"
else
  ok "the tree was left alone while the owner runs"
fi
kill "$live_pid" 2>/dev/null
wait "$live_pid" 2>/dev/null
printf '%s\n' "$saved_state" > "$HARNESS_STATE_FILE"
echo

# ---------------------------------------------------------------------------
# A4 - --restore-only puts it back, verified by cmp
# ---------------------------------------------------------------------------
echo "A4: --restore-only restores the file and verifies with cmp"
out=$(bash "$RESTORE" --restore-only --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 0 "--restore-only succeeds"
assert_contains "$out" "RESTORED and verified by cmp: src/target.py" \
  "it names the file it restored"
if cmp -s "$ORIGINAL" "$REPO/src/target.py"; then
  ok "the file is byte-identical to the original (cmp)"
else
  bad "the file was NOT restored to its original bytes"
fi
if [ -z "$(git -C "$REPO" status --porcelain)" ]; then
  ok "the tree is clean again"
else
  bad "the tree is still dirty after a reported restore"
fi
if [ -f "$HARNESS_STATE_FILE" ]; then
  bad "the state file survived a successful restore"
else
  ok "the state file was cleared, so the next check reports clean"
fi
echo

# ---------------------------------------------------------------------------
# A7 - clean tree, no state file
# ---------------------------------------------------------------------------
echo "A7: a clean tree with no state file is a clean result"
out=$(bash "$RESTORE" --check --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 0 "--check exits 0"
assert_contains "$out" "NOTHING STRANDED" "it says nothing is stranded"
echo

# ---------------------------------------------------------------------------
# A6 - dirt with no state file is REFUSED, not cleaned
# ---------------------------------------------------------------------------
echo "A6: dirt with no state file is refused rather than guessed at"
echo "# a human's legitimate edit" >> "$REPO/src/target.py"
human_bytes=$(cksum < "$REPO/src/target.py")
out=$(bash "$RESTORE" --restore-only --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 3 "--restore-only REFUSES unattributable dirt"
assert_contains "$out" "CANNOT ATTRIBUTE" "it says it cannot attribute the dirt"
if [ "$(cksum < "$REPO/src/target.py")" = "$human_bytes" ]; then
  ok "the human's edit was NOT destroyed"
else
  bad "it destroyed an edit it could not attribute"
fi
git -C "$REPO" checkout -- src/target.py
echo

# ---------------------------------------------------------------------------
# A8 - a state file about ANOTHER repository is refused, not acted on
#
# The state file's path is keyed by a 32-bit cksum of the repository path, so
# two checkouts can name the same file. Acting on a foreign one would restore
# file bytes from a blob resolved HERE at THAT repository's sha - which usually
# fails loudly and, where both trees hold a path of the same name, does not
# fail at all. `harness_state_begin` has always written `repo=`; until #131's
# gate change made a second writer, nothing read it.
# ---------------------------------------------------------------------------
echo "A8: a state file naming a different repository is refused"
cat > "$HARNESS_STATE_FILE" <<EOF
repo=/nowhere/some-other-checkout
harness=check-aaa-strander.sh
commit=0000000000000000000000000000000000000000
pid=1
started_human=1970-01-01T00:00:00+00:00
EOF
out=$(bash "$RESTORE" --restore-only --repo "$REPO" 2>&1); rc=$?
assert_rc "$rc" 2 "--restore-only refuses a foreign state file"
assert_contains "$out" "DIFFERENT repository" "it says the repository differs"
assert_contains "$out" "/nowhere/some-other-checkout" "it names the other one"
rm -f "$HARNESS_STATE_FILE"
echo

# ---------------------------------------------------------------------------
# A9 - a state file with NO repo= line is tolerated, and SAYS it is
#
# The field is newer than the tool. Refusing a file written before it existed
# would strand exactly the mutation this tool exists to put back. But a check
# that could not see its input and a check that passed must not render the
# same, so it announces the gap. This arm is the pair to A8: without it, A8
# would be satisfied by a tool that simply refused every state file.
# ---------------------------------------------------------------------------
echo "A9: a state file with no repo= line proceeds, and says why it cannot confirm"
cat > "$HARNESS_STATE_FILE" <<EOF
harness=check-aaa-strander.sh
commit=0000000000000000000000000000000000000000
pid=1
started_human=1970-01-01T00:00:00+00:00
EOF
out=$(bash "$RESTORE" --check --repo "$REPO" 2>&1); rc=$?
assert_contains "$out" "records no \`repo=\` line" "it announces the missing field"
assert_absent "$out" "DIFFERENT repository" "and does not claim a mismatch"
if [ "$rc" -ne 2 ]; then
  ok "it did not refuse outright (exit $rc)"
else
  bad "it refused a pre-field state file, stranding what it exists to restore"
fi
rm -f "$HARNESS_STATE_FILE"
echo

# ---------------------------------------------------------------------------
# A2 - THE AMPUTATION. Cut the fix out and A1's assertion must invert.
# ---------------------------------------------------------------------------
echo "A2: AMPUTATION - remove the fix, and the probe must blame the WRONG harness"
AMPUTATED="$REPO/docs/reviews/probe-amputated.sh"
python3 - "$PROBE" "$AMPUTATED" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
# Cut the whole guarded block the fix added inside the timeout branch: from the
# `if` that tests the tree there, through its `fi`. Anchored on the message,
# which is unique to that block.
start = text.index('    if [ -n "$(git -C "$REPO" status --porcelain)" ]; then\n'
                   '      echo "::error::$s WAS KILLED AT')
end = text.index("      exit 4\n    fi\n", start) + len("      exit 4\n    fi\n")
cut = text[:start] + text[end:]
assert "WAS KILLED AT" not in cut, "the amputation did not remove the message"
assert len(cut) < len(text), "the amputation removed nothing"
open(dst, "w").write(cut)
print(f"amputated {len(text) - len(cut)} bytes from the timeout branch")
PY
amp_rc=$?
if [ "$amp_rc" -ne 0 ]; then
  bad "the amputation could not be applied - A1 is therefore UNPROVEN"
else
  ok "the amputation landed (asserted, not assumed)"
  rm -f "$HARNESS_STATE_FILE" "$SANDBOX/ledger-amp"

  # COMMIT THE AMPUTATED COPY BEFORE RUNNING IT, and this cost a failing arm
  # to learn. The probe derives its repo as `dirname($0)/../..`, so the copy
  # HAS to live inside the scratch tree - where it is an UNTRACKED FILE, and
  # the probe's pre-flight refuses to start on a non-empty
  # `git status --porcelain`. The first run of this arm therefore aborted at
  # the pre-flight having measured nothing, and the arm's second assertion
  # ("never says the strander was killed") PASSED VACUOUSLY on that abort.
  # The same rule is why the run state file lives outside the repo.
  git -C "$REPO" add -A
  git -C "$REPO" commit -qm "amputated probe"

  out=$(bash "$AMPUTATED" "$SANDBOX/ledger-amp" 3 2>&1); rc=$?

  # THE ARM MUST HAVE RUN THE THING IT JUDGES. Every assertion below is an
  # absence-or-presence claim about output, and output that was never produced
  # satisfies the absence half for free. This is the guard against the vacuous
  # pass described above.
  assert_contains "$out" "check-aaa-strander.sh" \
    "the amputated probe actually reached the strander (not a vacuous arm)"
  # WITHOUT the fix the probe sails past the timeout, runs the innocent
  # successor, records its refusal, and then blames IT for the dirty tree.
  assert_contains "$out" "check-bbb-innocent.sh LEFT THE TREE DIRTY" \
    "the amputated probe blames the INNOCENT harness - the defect reproduces"
  assert_absent "$out" "WAS KILLED AT" \
    "the amputated probe never says the strander was killed"
  # Clean up after the amputated run, which really did strand a mutation.
  git -C "$REPO" checkout -- src/target.py
  rm -f "$HARNESS_STATE_FILE"
fi
echo

# ---------------------------------------------------------------------------
echo "================================================================"
echo "controls fired: $PASS passed, $FAIL failed"
if [ "$FAIL" -ne 0 ]; then
  echo "::error::$FAIL control(s) failed. Read WHICH rows died above; an exit"
  echo "         code alone does not say which arm broke."
  exit 1
fi
if [ "$PASS" -eq 0 ]; then
  echo "::error::ZERO controls fired. An empty run reports a clean result and"
  echo "         means nothing - this is the instrument failing, not a pass."
  exit 2
fi
echo "ALL $PASS CONTROLS PASSED, and A2 proves A1 can fail."
exit 0
