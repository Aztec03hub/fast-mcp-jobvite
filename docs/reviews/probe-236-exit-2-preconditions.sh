#!/usr/bin/env bash
# PROBE for task #236's residual.
#
# MEASURED-236-exit-2-hunks.md:91-93 closes with an honest gap:
#
#     Only `check-pytest-bounded.sh` was driven to a real exit 2. The other
#     two hunks are unproved. `check-committed-file-types.py` needs a
#     `git ls-files` failure, and `check-adr-numbers.py` needs an absent ADR
#     directory; neither was staged.
#
# This stages both, drives each to a REAL exit 2, and reads THE SCRIPT'S OWN
# exit code. It does not test a proxy: #236 itself recorded that the correct
# code produced by the wrong mechanism (a dead shell) passes a reviewer who
# only asks "does it exit 2?", so each amputated arm is paired with a
# POSITIVE CONTROL proving the same invocation exits 0 when its precondition
# IS met. Without that pair, an arm that exits 2 because the probe is broken
# is indistinguishable from the hunk working.
#
# Neither arm needs a stub. `check-committed-file-types.py`'s git() helper
# runs `["git", *args]` with NO `-C`, so it inherits the working directory;
# running it from a directory that is genuinely not a git repository makes
# `git ls-files` exit 128 for real. `check-adr-numbers.py` derives
# ROOT from `__file__/../../..`, so a skeleton tree without `docs/adr`
# reproduces the absent-directory precondition exactly.
# NO ERREXIT. Every sibling probe under docs/reviews/ uses this exact
# line, and check-no-errexit.py gates it: a probe runs ARMS, and an arm
# that fails must be REPORTED, not kill the probe before the remaining
# arms run. My first version had `-e` here and turned that gate red.
set -uo pipefail

# DERIVED, never hardcoded. R23-M5 asked for this and only half of that
# finding was applied - the `want_re` mechanism landed at a389c79 and this
# line did not. R25 then MEASURED the consequence: it moved BOTH subjects out
# of its own worktree and this probe still printed `arms=4 passed=4 failed=0`
# and exited 0, because it was reading a DIFFERENT tree - the shared checkout,
# by absolute path. A probe that cannot fail when its subject is deleted is
# the exact vacuity its own arms exist to catch, rebuilt one line above them.
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd) || {
    echo "REFUSING: could not derive REPO from ${BASH_SOURCE[0]}" >&2; exit 2; }

# AND THE DERIVED ROOT IS NOT ENOUGH ON ITS OWN. With REPO derived, a deleted
# subject makes python3 exit 2 for "can't open file" - the WANTED code by the
# WRONG mechanism, which is what MEASURED-236's own ARM 4c documents and what
# R23 caught this probe doing once already. So the subjects are asserted to
# EXIST before any arm runs, and their absence is a refusal, not a pass.
for subject in "$REPO/scripts/check-committed-file-types.py" \
               "$REPO/docs/reviews/check-adr-numbers.py"; do
    [ -s "$subject" ] || {
        echo "REFUSING: subject not found at $subject" >&2
        echo "         Every arm below would exit 2 for a missing file and" >&2
        echo "         report PASS. That is the defect this probe demonstrates." >&2
        exit 2
    }
done

WORK=$(mktemp -d) || { echo "REFUSING: mktemp -d failed" >&2; exit 2; }
[ -d "$WORK" ] || { echo "REFUSING: no work directory" >&2; exit 2; }
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

# Read the script's OWN exit code AND ITS DIAGNOSIS. The code alone is not
# enough, and R23 measured why on THIS probe: repoint $REPO at a path that
# does not exist and arms A1 and B1 both printed `rc=2 PASS (wanted 2)` with
# the 2 coming from `python3: can't open file`. That is the correct exit code
# produced by the WRONG MECHANISM - the exact failure MEASURED-236 documents
# in its own ARM 4c - reproduced inside the probe written to demonstrate it.
#
# So an arm now names the message its subject must print. `want_re` is
# REQUIRED for a nonzero expectation: an exit 2 that does not carry the
# checker's own refusal is a different event wearing the same number.
arm() {
    local label=$1 want=$2 want_re=$3 dir=$4
    shift 4
    local rc=0
    ( cd "$dir" && "$@" ) >"$WORK/out" 2>&1 || rc=$?
    printf '  %-52s rc=%-3s ' "$label" "$rc"
    if [ "$rc" -ne "$want" ]; then
        echo "FAIL (wanted $want)"
        sed -n '1,4p' "$WORK/out" | sed 's/^/        /'
        fail=$((fail + 1))
    elif [ -n "$want_re" ] && ! grep -qE "$want_re" "$WORK/out"; then
        # The code matched and the CAUSE did not. This is the vacuous pass.
        echo "FAIL - rc=$want by the WRONG MECHANISM"
        echo "        expected output matching: $want_re"
        sed -n '1,4p' "$WORK/out" | sed 's/^/        got: /'
        fail=$((fail + 1))
    else
        echo "PASS (wanted $want)"
        pass=$((pass + 1))
    fi
    sed -n '1,2p' "$WORK/out" | sed 's/^/        > /'
}

echo "=== HUNK 1: check-committed-file-types.py, a real git ls-files failure ==="
# The amputation: a working directory that is not a git repository at all.
mkdir -p "$WORK/notarepo"
git -C "$WORK/notarepo" rev-parse 2>/dev/null \
    && { echo "REFUSING: $WORK/notarepo is a git repo, the arm would be vacuous"; exit 2; }

arm "A1 amputated: cwd is not a git repo" 2 \
    'git ls-files.*exited|FAILED TO RUN' "$WORK/notarepo" \
    python3 "$REPO/scripts/check-committed-file-types.py" --all
arm "A2 control:   cwd IS the repo" 0 \
    'file\(s\) checked' "$REPO" \
    python3 "$REPO/scripts/check-committed-file-types.py" --all

echo
echo "=== HUNK 2: check-adr-numbers.py, an absent ADR directory ==="
# ROOT is __file__/../../.., so a skeleton at $WORK/skel puts ROOT at skel.
mkdir -p "$WORK/skel/docs/reviews"
cp "$REPO/docs/reviews/check-adr-numbers.py" "$WORK/skel/docs/reviews/"
# The old guard here tested `[ -d $WORK/skel/docs/adr ]`, which after a
# fresh `mktemp -d` can never be true - a refusal that cannot fire is
# decoration, and R23 measured it dead. What CAN go wrong is the copy
# silently not landing, which would make B1 exit 2 for a missing script
# rather than a missing directory. That is the reachable failure, so it is
# the one guarded.
[ -s "$WORK/skel/docs/reviews/check-adr-numbers.py" ] \
    || { echo "REFUSING: the checker did not copy into the skeleton"; exit 2; }

arm "B1 amputated: no docs/adr under ROOT" 2 \
    'NO ADR DIRECTORY' "$WORK/skel" \
    python3 "$WORK/skel/docs/reviews/check-adr-numbers.py"

# The control must run the SAME file from a tree that HAS docs/adr. Copying
# the real ADR directory in makes ROOT=skel satisfy the precondition, which
# isolates the absent directory as the single variable between B1 and B2.
cp -r "$REPO/docs/adr" "$WORK/skel/docs/adr"
arm "B2 control:   docs/adr restored under ROOT" 0 \
    'ADRs: [0-9]+' "$WORK/skel" \
    python3 "$WORK/skel/docs/reviews/check-adr-numbers.py"

echo
echo "=== VERDICT ==="
echo "arms=4 passed=$pass failed=$fail"
if [ "$fail" -ne 0 ]; then
    echo "PROBE-236: at least one arm did not behave as #236 predicted"
    exit 1
fi
echo "PROBE-236: both remaining hunks reach a REAL exit 2, each with a"
echo "           control proving the same invocation exits 0 when its"
echo "           precondition is met. #236's residual is discharged."
