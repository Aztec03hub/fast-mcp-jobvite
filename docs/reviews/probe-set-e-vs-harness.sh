#!/usr/bin/env bash
# Positive control for the ADR-0022 claim: under `set -e`, the exact shape used
# by every control harness here (`out=$(cmd); rc=$?`) aborts before rc is read,
# and any cleanup after it never runs.
#
# Arm A: set -uo pipefail  (what the repo does today)
# Arm B: set -euo pipefail (what bash.md:40 mandates)

arm () {
  local flags="$1"
  bash -c '
    set '"$flags"'
    trap "echo \"    [reached line: NOTHING - shell exited early]\"" ERR
    out=$(python3 -c "import sys; print(\"boom\"); sys.exit(1)"); rc=$?
    echo "    captured rc=$rc  out=$out"
    echo "    RESTORE RAN"
  '
  echo "    outer sees exit=$?"
}

echo "ARM A: set -uo pipefail"
arm "-uo pipefail"
echo
echo "ARM B: set -euo pipefail"
arm "-euo pipefail"
