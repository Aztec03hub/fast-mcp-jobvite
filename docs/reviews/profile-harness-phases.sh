#!/usr/bin/env bash
# Task #240 - phase profiler for the mutation/amputation harnesses.
#
# WHAT IT MEASURES, and the method, stated here because a breakdown whose
# method is not stated is not a measurement.
#
# Every amputation harness row is the same four-phase shape:
#
#   cp file backup ; python3 anchor-replace ; pytest <suite> ; cp backup file ; cmp
#
# so the row cost decomposes as
#
#   T_row    = T_mutate + T_pytest + T_restore
#   T_pytest = T_spawn + T_collect_proper + T_exec
#
# and each term is measured DIRECTLY rather than modelled:
#
#   spawn_bare    `uv run --frozen python -c pass`
#                 = uv lock resolution + venv activation + bare CPython start.
#                 The floor under any `uv run --frozen pytest ...`.
#   spawn_pytest  `uv run --frozen pytest --version`
#                 = spawn_bare + pytest and plugin import. Reported separately
#                 so "interpreter/subprocess spawn" is not silently charged the
#                 plugin-import cost.
#   collect_only  `uv run --frozen pytest <suite> -q -p no:cacheprovider --collect-only`
#                 whole-process wall. collect_proper = collect_only - spawn_pytest
#                 = conftest import + test-module import + item construction.
#   full_suite    `uv run --frozen pytest <suite> -q -p no:cacheprovider` whole-process
#                 wall, the exact command a harness row runs (minus -rf, which
#                 only formats a report).
#   exec          = full_suite - collect_only. Test bodies, fixtures, teardown,
#                 reporting.
#   mutate_restore  the harness's own cp + anchor-replace python3 + cmp + cp back,
#                 replayed on a COPY of the real subject file.
#
# REPS: each timing is run REPS times and the MEDIAN is reported, with min and
# max, because a single wall-clock sample on a loaded box is not a measurement
# either. The first run of each command is discarded as a warm-up so filesystem
# cache state is the same for every reported sample.
#
# IT NEVER LEAVES A MUTATION IN THE TREE. The only file it writes is a copy
# under a mktemp dir; the anchor replay is done on that COPY. Nothing under
# src/ is opened for writing. `git status --porcelain` is printed before and
# after and compared, and a difference is a hard failure.
set -uo pipefail

# A GUARD, NOT A POLICY, and it is REQUIRED: scripts/check-pytest-bounded.sh
# fails any tracked shell script whose pytest runs unbounded, because a hung
# suite produces no result lines and every assertion "did not survive". It
# costs one extra fork+exec per sample (~2 ms), which is inside the spread
# reported for every phase except spawn_bare - and spawn_bare doesn't run
# pytest, so it is not wrapped.
PYTEST_TIMEOUT=900

REPS="${REPS:-3}"
SUITE="${SUITE:-tests}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 3
export PYTHONDONTWRITEBYTECODE=1

TREE_BEFORE=$(git -C "$REPO" status --porcelain)

now_ms() { python3 -c 'import time;print(int(time.monotonic()*1000))'; }

# time_it <label> <cmd...>  -> prints one PHASE line, times in ms
time_it() {
  local label="$1"; shift
  "$@" >/dev/null 2>&1                       # warm-up, discarded
  local samples=() a b
  for _ in $(seq 1 "$REPS"); do
    a=$(now_ms); "$@" >/dev/null 2>&1; b=$(now_ms)
    samples+=( $((b - a)) )
  done
  printf '%s\n' "${samples[@]}" | LABEL="$label" python3 -c '
import os, sys
v = sorted(int(x) for x in sys.stdin.read().split())
lab = os.environ["LABEL"]
print("PHASE %s median_ms=%d min_ms=%d max_ms=%d n=%d"
      % (lab, v[len(v) // 2], v[0], v[-1], len(v)))'
}

echo "REPO=$REPO SUITE=$SUITE REPS=$REPS HEAD=$(git rev-parse --short HEAD)"
echo "nproc=$(nproc) load=$(cut -d' ' -f1-3 /proc/loadavg)"
echo "date=$(date -Is)"
echo

time_it spawn_bare   uv run --frozen python -c pass
time_it spawn_pytest timeout "$PYTEST_TIMEOUT" uv run --frozen pytest --version
# shellcheck disable=SC2086
time_it collect_only timeout "$PYTEST_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider --collect-only
# shellcheck disable=SC2086
time_it full_suite   timeout "$PYTEST_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider

# ---- the harness's own git/file work, replayed on a copy -------------------
# U9 row A3's anchor: a one-line return, unique in the file. Chosen because it
# is the shortest real anchor in the pole harness, so this is a LOWER bound on
# the mutate/restore cost and cannot flatter it.
SUBJECT="src/fast_mcp_jobvite/http_hardening.py"
OLD='    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]'
NEW='    return "client"'
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
cp "$SUBJECT" "$SANDBOX/subject.py"

replay_row_io() {
  cp "$SANDBOX/subject.py" "$SANDBOX/backup.py" || return 1
  OLD="$OLD" NEW="$NEW" FILE="$SANDBOX/subject.py" python3 - <<'PY' || return 1
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
n = s.count(old)
if n != 1:
    print(f"  ANCHOR NOT UNIQUE ({n} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  cmp -s "$SANDBOX/subject.py" "$SANDBOX/backup.py" && return 1   # must differ
  cp "$SANDBOX/backup.py" "$SANDBOX/subject.py"
  cmp -s "$SANDBOX/subject.py" "$SANDBOX/backup.py"               # must match now
}

# Prove the replay actually applies before timing it: a replay whose anchor
# missed would time an expensive no-op and report it as the mutate cost.
if ! replay_row_io; then
  echo "::error::the mutate/restore replay did not apply - the anchor moved."
  echo "         MUTATION TARGET NOT FOUND. Timing it would measure nothing."
  exit 2
fi
time_it mutate_restore replay_row_io

echo
TREE_AFTER=$(git -C "$REPO" status --porcelain)
if [ "$TREE_BEFORE" != "$TREE_AFTER" ]; then
  echo "::error::the profiler changed the working tree. It must not."
  exit 1
fi
echo "TREE UNCHANGED (git status --porcelain identical before and after)"
