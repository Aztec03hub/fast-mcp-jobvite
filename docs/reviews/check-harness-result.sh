#!/usr/bin/env bash
# THE CONTAINER GATE for the canonical result line. Task #107.
#
# WHAT THIS ASSERTS, and why it is an EQUALITY rather than a checklist.
# `scripts/lib/harness-result.sh` exists so that no checker has to carry a
# hand-kept list of the prose shapes a harness might print. That fix is only
# worth anything if EVERY member of the container emits the line: one script
# that does not is a silent hole exactly where the old shape lists had theirs.
#
# So the population here is the GLOB `scripts/*.sh` and nothing else. There is no
# table in this file, no allowlist, and no "harness vs not a harness" partition -
# a partition would be the same hand-kept list one level up. The assertion is
#
#     { scripts that emit the line } == { scripts that exist }
#
# and it is stated as a set equality so that ADDING a script fails this gate
# until the script is wired. A checklist would simply not mention it.
#
# THIS IS THE STATIC LAYER. It reads source and cannot see a line that fails to
# print at runtime. `docs/reviews/check-harness-result-controls.sh` is the layer
# that RUNS artifacts and reads their real output; neither substitutes for the
# other, and this file's green says only what it checked.
#
# `-e` deliberately omitted for consistency with the harnesses it reads; every
# failing branch here sets `fail=1` explicitly rather than relying on it.
# See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB="$REPO/scripts/lib/harness-result.sh"

fail=0

[ -f "$LIB" ] || {
  echo "::error::$LIB does not exist. Prove the path resolves before reading a"
  echo "         clean zero out of the loop below - a glob at a path that is not"
  echo "         there exits empty and looks exactly like compliance."
  exit 2
}

# ---- THE FORMAT APPEARS ONCE -----------------------------------------------
# The whole point of the shared file is that the format string has one home. A
# second printf of that line anywhere else is a copy, and a copy drifts.
#
# THE NEEDLE IS SPLIT ACROSS A CONCATENATION ON PURPOSE. Written whole, this
# file would contain the string it searches for, match ITSELF, and report two
# copies where there is one - an instrument reading its own reflection. That is
# not hypothetical: it is what the first version of this check did.
NEEDLE="printf 'HARNESS-""RESULT"
#
# ONLY EXECUTABLE SOURCE IS SCANNED. A report that QUOTES the format is not
# a second copy of it - prose is a record, not a producer, and it cannot
# drift out of step with anything. Measured: the first version scanned all
# of docs/ and failed on the very worklog paragraph describing this defect.
copies=$(grep -rlF --include='*.sh' --include='*.py' --include='*.yml' \
           -- "$NEEDLE" "$REPO/scripts" "$REPO/docs" "$REPO/.github" 2>/dev/null | sort)
n_copies=$(printf '%s\n' "$copies" | grep -c . || true)
if [ "$n_copies" -ne 1 ] || [ "$copies" != "$LIB" ]; then
  echo "::error::the HARNESS-RESULT format is written in $n_copies place(s):"
  printf '           %s\n' $copies
  echo "         It must live only in scripts/lib/harness-result.sh."
  fail=1
fi

# ---- THE CONTAINER ---------------------------------------------------------
mapfile -t SCRIPTS < <(cd "$REPO/scripts" && ls -1 ./*.sh | sed 's|^\./||' | sort)
total=${#SCRIPTS[@]}
if [ "$total" -eq 0 ]; then
  echo "::error::scripts/*.sh matched NOTHING. A zero here is an instrument"
  echo "         failure, not a clean repository."
  exit 2
fi

sourcing=0
armed=0
reporting=0
missing_source=()
missing_arm=()
missing_ran=()

for s in "${SCRIPTS[@]}"; do
  f="$REPO/scripts/$s"

  # THE SOURCE COMMAND, not the string. `grep -qF lib/harness-result.sh` was the
  # first version and it PASSED a script whose `.` line had been deleted: the
  # `# shellcheck source=lib/harness-result.sh` directive three lines above it
  # carries the same path, so the substring survived the amputation and the gate
  # reported the script as wired. Found by this file's own negative control.
  if grep -qE '^\. .*/lib/harness-result\.sh"$' "$f"; then
    sourcing=$((sourcing + 1))
  else
    missing_source+=("$s")
  fi

  # EVERY EXIT trap must carry the emitter. bash has no trap stack: a later
  # `trap ... EXIT` REPLACES the one the shared file arms at source time, so a
  # trap that does not chain `harness_result_emit` silently disarms the whole
  # mechanism for that script - and disarmed looks exactly like passing.
  traps=$(grep -cE '^[[:space:]]*trap .*[[:space:]]EXIT$' "$f")
  chained=$(grep -cE '^[[:space:]]*trap .*harness_result_emit.*[[:space:]]EXIT$' "$f")
  if [ "$traps" -eq "$chained" ]; then
    armed=$((armed + 1))
  else
    missing_arm+=("$s ($chained of $traps EXIT traps chain the emitter)")
  fi

  # A script that never calls `harness_result_ran` can only ever report
  # `refused`. That is safe - it fails closed - but it is also useless, and it
  # means the script's rows and floor are never reported.
  if grep -qE '(^|[^_[:alnum:]])harness_result_ran ' "$f"; then
    reporting=$((reporting + 1))
  else
    missing_ran+=("$s")
  fi
done

echo "scripts/*.sh (the container)     : $total"
echo "source scripts/lib/harness-result.sh : $sourcing"
echo "every EXIT trap chains the emitter   : $armed"
echo "call harness_result_ran              : $reporting"

if [ "${#missing_source[@]}" -ne 0 ]; then
  echo "::error::these scripts do NOT source the shared result file, so they emit"
  echo "         no canonical line and any checker reading one sees nothing:"
  printf '           %s\n' "${missing_source[@]}"
  fail=1
fi
if [ "${#missing_arm[@]}" -ne 0 ]; then
  echo "::error::these scripts set an EXIT trap that does NOT chain"
  echo "         harness_result_emit, which REPLACES the armed trap and disarms"
  echo "         the line on every exit path, including their aborts:"
  printf '           %s\n' "${missing_arm[@]}"
  fail=1
fi
if [ "${#missing_ran[@]}" -ne 0 ]; then
  echo "::error::these scripts never call harness_result_ran, so their line can"
  echo "         only ever say status=refused and never reports rows or floor:"
  printf '           %s\n' "${missing_ran[@]}"
  fail=1
fi

# ---- THE EQUALITY, stated as one comparison --------------------------------
if [ "$sourcing" -eq "$total" ] && [ "$armed" -eq "$total" ] && [ "$reporting" -eq "$total" ]; then
  echo "EQUAL: all $total scripts in the container emit the canonical line."
else
  echo "::error::the set that emits the line is NOT the set that exists."
  fail=1
fi

exit "$fail"
