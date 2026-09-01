#!/usr/bin/env bash
# PID 1 receives SIGTERM, the lifespan tears down, and the process exits inside the
# grace period - on BOTH transports.
#
# WHY THIS FILE EXISTS. DESIGN.md:1099-1107 carried two inherited limits on the
# shutdown mitigation, one of which was "PID 1 was never simulated". U1 closed it
# by measurement and reported the numbers in prose. The script that produced them
# lived in /tmp and a restart destroyed it, so the measurement became exactly what
# this project keeps warning about: a CLAIM about a measurement rather than one
# anybody can re-run. This is the re-derivation, committed.
#
# WHAT IT MEASURES, AND WHAT IT DOES NOT.
#
#   It DOES put the interpreter at PID 1. `unshare --pid` is not permitted on this
#   host (verified: "unshare failed: Operation not permitted"), so this uses Docker
#   with NO `--init`, which makes the command itself PID 1, and `docker stop -t 15`,
#   which delivers a real SIGTERM to PID 1 and SIGKILLs after the grace period.
#   That is the production shape Docker, Kubernetes and Cloud Run all use.
#
#   AND IT NOW CHECKS THAT, ON EVERY ARM. R3-M2: for one revision this file made
#   the "both transports" claim in its first line while only the `http` arm
#   asserted PID 1 - the assertion keyed off uvicorn's "Started server process [1]"
#   log line, which `stdio` does not emit. The stdio arm asserted teardown and
#   timing, both of which a NON-pid-1 process satisfies, so the row read as proven
#   while being unproven. The PID is now written into the marker by the entry
#   script itself and checked unconditionally, and an arm that cannot read a PID
#   fails LOUDLY rather than degrading to the weaker check. A harness that cannot
#   fail is worse than no harness: it occupies the space a real check would take.
#
#   It does NOT test an image built from this repository. The container runs the
#   IMAGE's own CPython 3.12 with this repo's virtualenv site-packages on
#   PYTHONPATH, bind-mounted read-only. That is a genuine 3.12 interpreter, this
#   project's exact dependency set and a real PID-1 signal disposition; it is not a
#   test of a Dockerfile this project does not have.
#
#   The venv's own `.venv/bin/python` CANNOT be used here and the reason is worth
#   recording: it is a symlink to the host's /usr/bin/python3, which does not exist
#   inside the image, so the first version of this script failed with a bare
#   "no such file or directory" that read like a broken bind mount. The mount was
#   fine; the interpreter was a dangling symlink.
#
#   The ceiling is stated here rather than only in a worklog, because the
#   mitigation this replaced was also called verified and was not.
#
# NOT A CI STEP, DELIBERATELY. CI has no Docker daemon, and wiring one in for a
# single arm is a required check that goes red for reasons nobody caused - the same
# reasoning ci.yml already applies to deferred steps. CONTRIBUTING.md lists it under
# the measurements a human runs, not under the gates.
#
# Exit 0 = both arms passed. 1 = an arm failed. 2 = could not run (no Docker),
# which is deliberately NOT 0: a skip that reports success is a green that tested
# nothing.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="python:3.12-slim"
GRACE=15

command -v docker >/dev/null 2>&1 || { echo "CANNOT RUN: docker is not installed"; exit 2; }
docker info >/dev/null 2>&1 || { echo "CANNOT RUN: the docker daemon is unreachable"; exit 2; }
SITE_PACKAGES="$REPO/.venv/lib/python3.12/site-packages"
[ -d "$SITE_PACKAGES" ] || { echo "CANNOT RUN: $SITE_PACKAGES is missing; run uv sync --frozen"; exit 2; }

WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

# The marker entry script comes from tests/boot_process.py so there is ONE source of
# truth for how teardown is observed. Duplicating it here would be the two-lists
# defect: this file could then drift from the suite and still look right.
python3 - "$WORK/entry.py" <<'PY' || { echo "CANNOT RUN: could not derive the marker entry"; exit 2; }
import pathlib, sys
sys.path.insert(0, "tests")
from boot_process import MARKER_ENTRY
pathlib.Path(sys.argv[1]).write_text(MARKER_ENTRY)
PY

FAILED=0

# A ROW COUNTER, added by task #107. This harness had none, so the
# canonical result line could only ever report rows=0 - and rows=0
# beside a green is exactly the shape a row floor exists to catch.
# The increment is at the TOP of the row function so that a row
# which aborts on a missing anchor still counts as having run.
HR_COUNTED_ROWS=0
run_arm () {
  HR_COUNTED_ROWS=$((HR_COUNTED_ROWS + 1))
  local transport="$1"
  local name="u1-pid1-${transport}-$$"
  local marker="$WORK/marker-${transport}.txt"
  : > "$marker"

  local -a env_args=(
    -e "JOBVITE_MCP_TRANSPORT=${transport}"
    -e "JOBVITE_API_KEY=k" -e "JOBVITE_API_SECRET=s"
    -e "JOBVITE_TOOLS=search_jobs"
    -e "PYTHONUNBUFFERED=1"
    -e "PYTHONPATH=$SITE_PACKAGES:$REPO/src"
  )
  if [ "$transport" = "http" ]; then
    env_args+=(-e "JOBVITE_MCP_HOST=127.0.0.1" -e "JOBVITE_MCP_PORT=8000")
    env_args+=(-e 'JOBVITE_HTTP_TOKENS={"t":["read"]}')
  fi

  # NO --init. That is the whole point: the command is PID 1 and receives the
  # signal itself, rather than a shim reaping it.
  docker run -d --name "$name" \
    -v "$REPO:$REPO:ro" -v "$WORK:$WORK" -w "$REPO" \
    "${env_args[@]}" \
    "$IMAGE" python "$WORK/entry.py" "$marker" >/dev/null 2>&1 || {
      echo "  $transport: FAILED to start the container"; FAILED=1; return; }

  # Wait for the lifespan to open rather than sleeping a guessed interval.
  local waited=0
  while ! grep -q opened "$marker" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    if [ "$waited" -gt 100 ]; then
      echo "  $transport: FAILED - the lifespan never opened within 20s"
      docker logs "$name" 2>&1 | tail -5 | sed 's/^/      /'
      docker rm -f "$name" >/dev/null 2>&1; FAILED=1; return
    fi
  done

  local start elapsed code logs
  start=$(date +%s.%N)
  docker stop -t "$GRACE" "$name" >/dev/null 2>&1
  elapsed=$(echo "$(date +%s.%N) - $start" | bc)
  code=$(docker inspect -f '{{.State.ExitCode}}' "$name" 2>/dev/null)
  logs=$(docker logs "$name" 2>&1)
  docker rm -f "$name" >/dev/null 2>&1

  local final; final=$(tr '\n' ' ' < "$marker")
  echo "  $transport: marker='$final' stop=${elapsed}s exit=$code"

  grep -q closed "$marker" 2>/dev/null || {
    echo "    FAIL: the lifespan never CLOSED - teardown did not run on SIGTERM"; FAILED=1; }

  # Assert on the SIDE EFFECT and the timing, never on the exit code alone: a
  # process that dies uncleanly can still exit 0, which is why DESIGN.md's own
  # section 8 case refuses to assert shutdown that way.
  awk -v e="$elapsed" -v g="$GRACE" 'BEGIN{exit !(e < g)}' || {
    echo "    FAIL: took ${elapsed}s, at or beyond the ${GRACE}s grace - it was SIGKILLed"; FAILED=1; }

  # PID 1, ON BOTH ARMS. R3-M2: this assertion used to sit inside an
  # `http`-only branch because it keyed off uvicorn's "Started server
  # process [1]" log line, which the stdio arm never emits. The stdio arm
  # therefore asserted only "the marker closed inside the grace period",
  # which is equally true of a process that is NOT pid 1 - add `--init`,
  # switch to an image with an entrypoint shim, or wrap the command in
  # `sh -c` and the arm stays green while testing something else.
  #
  # The PID now comes from the entry script itself (tests/boot_process.py's
  # MARKER_ENTRY writes `opened pid=<n>`), so it is transport-independent
  # and owned by this project rather than by a third-party log format.
  #
  # TWO CHECKS, NOT ONE, so the arm cannot silently degrade: first that the
  # marker carries a pid at all - if MARKER_ENTRY stops recording it, the
  # single `grep -q 'pid=1'` below would go red for the right reason but
  # with a message blaming the container, and a future reader would "fix"
  # it by deleting the check. An absent instrument is a DIFFERENT failure
  # from a wrong reading and must say so.
  local recorded_pid
  recorded_pid=$(sed -n 's/^opened pid=\([0-9][0-9]*\)$/\1/p' "$marker" | head -1)
  if [ -z "$recorded_pid" ]; then
    echo "    FAIL: the marker records no pid - MARKER_ENTRY no longer writes"
    echo "          'opened pid=<n>', so this arm CANNOT establish pid 1."
    echo "          marker was: '$final'"
    printf '%s' "$logs" | tail -3 | cut -c1-100 | sed 's/^/          | /'
    FAILED=1
  elif [ "$recorded_pid" != "1" ]; then
    echo "    FAIL: the entry ran as pid $recorded_pid, not pid 1 - this arm did"
    echo "          NOT measure a PID-1 signal disposition."
    printf '%s' "$logs" | tail -3 | cut -c1-100 | sed 's/^/          | /'
    FAILED=1
  fi
}

echo "PID-1 shutdown, host venv under $IMAGE, no --init, docker stop -t $GRACE"
run_arm stdio
run_arm http

# The canonical result line's row count, from the harness's own
# counter. This harness declares no ROW_FLOOR, so the floor is 0:
# 0 is not a floor anything can breach, and it reads as absent.
harness_result_ran "$HR_COUNTED_ROWS" 0
if [ "$FAILED" -ne 0 ]; then
  echo "FAILED"
  exit 1
fi
echo "Both arms: teardown ran and the process exited inside the grace period."
exit 0
