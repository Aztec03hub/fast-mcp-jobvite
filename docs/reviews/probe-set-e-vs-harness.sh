#!/usr/bin/env bash
# Positive control for the ADR-0023 claim: under `set -e`, the exact shape used
# by every control harness here (`out=$(cmd); rc=$?`) aborts before rc is read,
# and any cleanup after it never runs.
#
# Arm A: set -uo pipefail  (what the repo does today)
# Arm B: set -euo pipefail (what bash.md:36-41 mandates)

# `-e` deliberately omitted here too, under ADR-0023, and for this file the
# reason is unusually direct: ARM B is EXPECTED to exit non-zero - that IS the
# observation - so `-e` would abort this probe at the exact behaviour it exists
# to demonstrate. A probe that cannot survive its own finding proves nothing.
set -uo pipefail

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
