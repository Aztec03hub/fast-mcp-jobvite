#!/usr/bin/env bash
# PID 1 receives SIGTERM, the lifespan tears down, and the process exits inside the
# grace period - on BOTH transports.
#
# WHY THIS FILE EXISTS. DESIGN.md:982-990 carried two inherited limits on the
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

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="python:3.12-slim"
GRACE=15

command -v docker >/dev/null 2>&1 || { echo "CANNOT RUN: docker is not installed"; exit 2; }
docker info >/dev/null 2>&1 || { echo "CANNOT RUN: the docker daemon is unreachable"; exit 2; }
SITE_PACKAGES="$REPO/.venv/lib/python3.12/site-packages"
[ -d "$SITE_PACKAGES" ] || { echo "CANNOT RUN: $SITE_PACKAGES is missing; run uv sync --frozen"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

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

run_arm () {
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

  if [ "$transport" = "http" ]; then
    printf '%s' "$logs" | grep -q 'process \[1\]' || {
      echo "    FAIL: no 'Started server process [1]' in the log - this was NOT pid 1"; FAILED=1; }
  fi
}

echo "PID-1 shutdown, host venv under $IMAGE, no --init, docker stop -t $GRACE"
run_arm stdio
run_arm http

if [ "$FAILED" -ne 0 ]; then
  echo "FAILED"
  exit 1
fi
echo "Both arms: teardown ran and the process exited inside the grace period."
exit 0
