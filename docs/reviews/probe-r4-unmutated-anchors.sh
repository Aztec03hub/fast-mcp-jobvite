#!/usr/bin/env bash
# R4 PROBE - candidate mutation rows that check-u5-jobs-controls.sh does NOT
# carry. Each row changes ONE value in the shipped tool and runs the WHOLE
# suite (not a named selector, so nothing is hidden by selection).
#
# A SURVIVOR here is a finding: the suite is green against a server whose
# behaviour is wrong in the named way.
#
# Restore is checked with `cmp` against a PRISTINE backup taken BEFORE any
# mutation - not against the per-row backup, which is what the row just
# copied from and therefore compares equal by construction.
#
# PYTHONDONTWRITEBYTECODE=1 for the reason the U5 harnesses give: .pyc
# invalidation keys on (mtime, size) and a same-size swap inside one second
# reuses stale bytecode, faking a clean survivor.

set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(dirname "$REPO_ROOT")"
cd "$REPO_ROOT" || exit 3

F="src/fast_mcp_jobvite/tools/jobs.py"
M="src/fast_mcp_jobvite/models/jobs.py"
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$PRISTINE_DIR"' EXIT
cp "$F" "$PRISTINE_DIR/tools_jobs.py"
cp "$M" "$PRISTINE_DIR/models_jobs.py"

echo "########## BASELINE"
timeout -k 30 900 uv run --frozen pytest tests/ -q -p no:cacheprovider \
  >/tmp/r4-base.txt 2>&1
BASE_RC=$?
if [ "$BASE_RC" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "TIMED OUT. Every row below would have measured the hang."
  exit 4
fi
if [ "$BASE_RC" -ne 0 ]; then
  echo "ABORT: intact suite is red"
  tail -20 /tmp/r4-base.txt
  exit 3
fi
tail -1 /tmp/r4-base.txt
echo

SURVIVED=0
ROWS=0

probe() {
  local label="$1" file="$2" pristine="$3" old="$4" new="$5"
  ROWS=$((ROWS + 1))
  echo "########## $label"

  OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
import os
import pathlib
import sys

p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
n = s.count(old)
if n != 1:
    print(f"  ANCHOR NOT UNIQUE ({n} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  if [ $? -ne 0 ]; then
    echo "  COULD NOT APPLY - anchor moved"
    cp "$pristine" "$file"
    echo
    return
  fi

  if cmp -s "$file" "$pristine"; then
    echo "  DID NOT LAND"
    cp "$pristine" "$file"
    echo
    return
  fi

  timeout -k 30 900 uv run --frozen pytest tests/ -q -p no:cacheprovider \
    >/tmp/r4-out.txt 2>&1
  local rc=$?
  cp "$pristine" "$file"

  # A HANG WOULD READ AS A KILL. The verdict below is `rc -ne 0` -> KILLED,
  # and a timeout is non-zero, so an unbounded hang scores as this probe's
  # GOOD outcome. That is the silent direction, so it is named and the row
  # is refused rather than counted.
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - this row NEVER FINISHED, so it is neither"
    echo "  a kill nor a survivor. No verdict is emitted for it."
    return 1
  fi
  if [ "$rc" -ne 0 ]; then
    echo "  KILLED   $(tail -1 /tmp/r4-out.txt)"
  else
    SURVIVED=$((SURVIVED + 1))
    echo "  *** SURVIVED *** $(tail -1 /tmp/r4-out.txt)"
  fi
  echo
}

# R4-P1 - the `ids` argument is accepted, validated, audited, and then
# never sent. The caller asked for one job and gets the whole first page.
probe "R4-P1 the ids query parameter never reaches the wire" \
  "$F" "$PRISTINE_DIR/tools_jobs.py" \
  '                        params=(
                            {"ids": params.ids} if params.ids is not None else None
                        ),' \
  '                        params=None,'

# R4-P2 - the query key Jobvite reads is misspelled. Jobvite ignores an
# unknown parameter, which is the exact failure SearchJobsInput's own
# docstring says the missing date filter was omitted to avoid.
probe "R4-P2 the ids query key is misspelled" \
  "$F" "$PRISTINE_DIR/tools_jobs.py" \
  '{"ids": params.ids} if params.ids is not None else None' \
  '{"id": params.ids} if params.ids is not None else None'

# R4-P3 - the route. Every offline test drives a MockTransport that
# answers whatever it is asked.
probe "R4-P3 JOBS_PATH points at a route that does not exist" \
  "$F" "$PRISTINE_DIR/tools_jobs.py" \
  'JOBS_PATH: Final = "/job"' \
  'JOBS_PATH: Final = "/not-a-route"'

# R4-P4 - the envelope key. The M3 shape: tests that build their payload
# from the constant move with it. The on-disk fixture pins the literal,
# so this row measures whether the fixture-driven cases are load-bearing.
probe "R4-P4 JOBS_ENVELOPE_KEY names a key Jobvite never sends" \
  "$M" "$PRISTINE_DIR/models_jobs.py" \
  'JOBS_ENVELOPE_KEY = "requisitions"' \
  'JOBS_ENVELOPE_KEY = "jobs"'

# R4-P5 - the total key, same shape.
probe "R4-P5 TOTAL_ENVELOPE_KEY names a key Jobvite never sends" \
  "$M" "$PRISTINE_DIR/models_jobs.py" \
  'TOTAL_ENVELOPE_KEY = "total"' \
  'TOTAL_ENVELOPE_KEY = "count"'

# R4-P6 - the advisory annotation flips to a write hint.
probe "R4-P6 the read-only annotation is inverted" \
  "$F" "$PRISTINE_DIR/tools_jobs.py" \
  'annotations={"readOnlyHint": True},' \
  'annotations={"readOnlyHint": False},'

echo "########## ROWS: $ROWS   SURVIVED: $SURVIVED"

# RESTORE IS CHECKED AGAINST THE PRISTINE COPY, taken before row 1.
dirty=0
cmp -s "$F" "$PRISTINE_DIR/tools_jobs.py" || dirty=1
cmp -s "$M" "$PRISTINE_DIR/models_jobs.py" || dirty=1
if [ "$dirty" -ne 0 ]; then
  echo "::error::TREE IS DIRTY - restore failed"
  exit 3
fi
echo "TREE RESTORED - both files match the pristine pre-run copies."
