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
set -euo pipefail

REPO=/home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

# Read the script's OWN exit code. `rc=0; cmd || rc=$?` is safe under errexit
# because the `||` makes it a compound command; a bare `rc=$(cmd)` would make
# the assignment itself the failing command and never reach the check.
arm() {
    local label=$1 want=$2 dir=$3
    shift 3
    local rc=0
    ( cd "$dir" && "$@" ) >"$WORK/out" 2>&1 || rc=$?
    printf '  %-52s rc=%-3s ' "$label" "$rc"
    if [ "$rc" -eq "$want" ]; then
        echo "PASS (wanted $want)"
        pass=$((pass + 1))
    else
        echo "FAIL (wanted $want)"
        sed -n '1,4p' "$WORK/out" | sed 's/^/        /'
        fail=$((fail + 1))
    fi
    sed -n '1,2p' "$WORK/out" | sed 's/^/        > /'
}

echo "=== HUNK 1: check-committed-file-types.py, a real git ls-files failure ==="
# The amputation: a working directory that is not a git repository at all.
mkdir -p "$WORK/notarepo"
git -C "$WORK/notarepo" rev-parse 2>/dev/null \
    && { echo "REFUSING: $WORK/notarepo is a git repo, the arm would be vacuous"; exit 2; }

arm "A1 amputated: cwd is not a git repo" 2 "$WORK/notarepo" \
    python3 "$REPO/scripts/check-committed-file-types.py" --all
arm "A2 control:   cwd IS the repo" 0 "$REPO" \
    python3 "$REPO/scripts/check-committed-file-types.py" --all

echo
echo "=== HUNK 2: check-adr-numbers.py, an absent ADR directory ==="
# ROOT is __file__/../../.., so a skeleton at $WORK/skel puts ROOT at skel.
mkdir -p "$WORK/skel/docs/reviews"
cp "$REPO/docs/reviews/check-adr-numbers.py" "$WORK/skel/docs/reviews/"
[ -d "$WORK/skel/docs/adr" ] \
    && { echo "REFUSING: the skeleton HAS an ADR dir, the arm would be vacuous"; exit 2; }

arm "B1 amputated: no docs/adr under ROOT" 2 "$WORK/skel" \
    python3 "$WORK/skel/docs/reviews/check-adr-numbers.py"

# The control must run the SAME file from a tree that HAS docs/adr. Copying
# the real ADR directory in makes ROOT=skel satisfy the precondition, which
# isolates the absent directory as the single variable between B1 and B2.
cp -r "$REPO/docs/adr" "$WORK/skel/docs/adr"
arm "B2 control:   docs/adr restored under ROOT" 0 "$WORK/skel" \
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
