#!/usr/bin/env bash
# ADR-0026 AMPUTATION harness - the embedder's log redaction (task #83).
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything
#                    still report success?
#
# SURVIVORS ARE THE OUTPUT, not the failure. Each row prints the counts
# and NAMES every assertion that still passed.
#
# **The row this harness exists for is A1.** ADR-0026's ruling adds a
# requirement its own body does not state - the install must be
# IDEMPOTENT - and the obvious test, "the filter is installed", passes
# on the FIRST construction and says nothing about the twentieth. A1
# deletes the idempotence check so `addFilter` runs on every
# construction, which is the unbounded per-invocation growth the ruling
# describes, and asserts something goes red.
#
# A3 is the one nobody would have thought to write: it points the
# constant at `httpx` instead of `httpx2` (ADR-0007). A filter installed
# on a logger the library never writes to is accepted by `logging`
# without complaint, never fires, and leaves the leak exactly as
# measured - a fix that is real, and lands on the wrong artefact.
#
# It exits non-zero only if it could not run, if the intact baseline is
# red, if a row failed to apply its anchor, or if a row was VACUOUS.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation replacing a body with a same-size one inside one
# second would otherwise run from stale bytecode and fake a clean row.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

REDACTION="src/fast_mcp_jobvite/utils/redaction.py"
CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
PROBE="docs/reviews/probe-u12-f2-embedder-leak.py"
SUITE="tests/test_redaction.py"
OUT=/tmp/log-redaction-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

for f in "$REDACTION" "$CLIENT" "$PROBE"; do
  cp "$f" "$PRISTINE_DIR/$(echo "$f" | tr / _)" ||
    { echo "COULD NOT TAKE PRISTINE COPY of $f"; exit 3; }
done

echo "########## BASELINE - the intact tree"
timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 "$OUT"
  exit 3
fi
tail -1 "$OUT"
echo

# THE ROW FLOOR, layer one. `ROWS -ne APPLIED` catches a row whose anchor
# moved; it does NOT catch a row somebody DELETED, because `6 == 6` and
# `0 == 0` are equally satisfied and the harness reports the same green
# with all but one row gone. The floor is the only check that sees a
# harness shrink.
#
# DERIVED from a run of this harness - six rows, six applied, zero
# vacuous - not typed in.
#
# The assignment is bare on its own line because
# docs/reviews/check-row-floors.py matches `^\s*ROW_FLOOR=(\d+)\s*$`: a
# trailing comment here makes the floor invisible to the checker, which
# is the same "a floor nobody can see is a floor nobody checks" shape
# the floor exists to catch.
ROW_FLOOR=6

TOTAL_SURVIVORS=0
APPLIED=0
ROWS=0
VACUOUS=0

# ---------------------------------------------------------------------------
# amputate <label> <file> <old> <new>
# ---------------------------------------------------------------------------
amputate() {
  local label="$1" file="$2" old="$3" new="$4"
  ROWS=$((ROWS + 1))

  echo "########## $label"

  local backup
  backup="$BACKUP_DIR/${ROWS}_$(echo "$file" | tr / _)"
  cp "$file" "$backup" || { echo "  COULD NOT BACK UP"; echo; return; }

  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
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
  then
    echo "  COULD NOT APPLY - the anchor moved. Fix the harness."
    cp "$backup" "$file"
    echo
    return
  fi

  if cmp -s "$file" "$backup"; then
    echo "  AMPUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi
  APPLIED=$((APPLIED + 1))

  timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - this row NEVER FINISHED. Not a kill,"
    echo "  not a survivor: no verdict below is a measurement of this row."
  fi

  cp "$backup" "$file"
  local pristine
  pristine="$PRISTINE_DIR/$(echo "$file" | tr / _)"
  if ! cmp -s "$file" "$pristine"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  tail -1 "$OUT" | sed 's/^/  /'

  # The verdict is the RUN'S EXIT CODE, never `grep -c "^FAILED"`: that
  # grep misses ERROR entirely, and a collection error is a row going
  # red for a real reason.
  if [ "$rc" -eq 0 ]; then
    echo "  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red."
    VACUOUS=$((VACUOUS + 1))
  fi
  local survivors
  survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    local n
    n=$(printf '%s\n' "$survivors" | wc -l)
    TOTAL_SURVIVORS=$((TOTAL_SURVIVORS + n))
    echo "  survivors ($n assertions still reported success)"
  fi
  echo
}

# ---------------------------------------------------------------------------
# A1 - THE IDEMPOTENCE CHECK DOES NOT EXIST. Every construction appends
# a filter, so a long-running server grows the list by one per tool
# call and every record walks all of them. ADR-0026's ruling in one
# deletion.
# ---------------------------------------------------------------------------
amputate "A1  the idempotence check does not exist" "$REDACTION" \
  '        if any(isinstance(f, RedactingLogFilter) for f in logger.filters):
            return False
' \
  ''

# ---------------------------------------------------------------------------
# A2 - THE CONSTRUCTOR DOES NOT INSTALL. Back to the measured state:
# an embedder who never runs `configure_logging()` receives all three
# credentials in the clear.
# ---------------------------------------------------------------------------
amputate "A2  JobviteClient.__init__ installs nothing" "$CLIENT" \
  '            _install_log_redaction()' \
  '            pass'

# ---------------------------------------------------------------------------
# A3 - THE WRONG LOGGER. `httpx`, not `httpx2` (ADR-0007). Installed,
# counted, idempotent - and inert, because the library writes somewhere
# else. The row that says whether any other row is measuring the real
# producer or only its own bookkeeping.
#
# THE ANCHOR MOVED WITH R11-M1, and it had to. ADR-0026 requires the
# logger name DERIVED from the imported module rather than retyped, so
# the literal this row used to anchor on no longer exists - and this
# harness is what caught the change, by going stale rather than by
# silently matching nothing. The mutation is unchanged in substance:
# replace the derived name with a literal `httpx`, which is BOTH the
# wrong logger AND the retyping ADR-0026 forbids, so the row is now
# strictly stronger than it was.
# ---------------------------------------------------------------------------
amputate "A3  the filter is installed on the wrong logger" "$REDACTION" \
  'HTTPX_LOGGER_NAME: Final[str] = _httpx2_logger.name' \
  'HTTPX_LOGGER_NAME: Final[str] = "httpx"'

# ---------------------------------------------------------------------------
# A4 - THE FILTER DOES NOT REDACT. Installed, found, counted, and it
# passes every record through untouched.
# ---------------------------------------------------------------------------
amputate "A4  the filter body does nothing" "$REDACTION" \
  '        record.msg = redact_text(record.getMessage())
        record.args = None' \
  '        pass'

# ---------------------------------------------------------------------------
# A5 - `record.msg` ONLY. Not a deletion but the mistake next to it:
# `httpx2` puts the URL in `record.args` and leaves `msg` a format
# string carrying no credential, so a redactor that reads only `msg`
# looks correct and leaks every real record.
# ---------------------------------------------------------------------------
amputate "A5  args are left unredacted, msg only" "$REDACTION" \
  '        record.msg = redact_text(record.getMessage())
        record.args = None' \
  '        record.msg = redact_text(str(record.msg))'

# ---------------------------------------------------------------------------
# A6 - THE PROBE'S CONTROL ARM CANNOT READ A LEAK. Its opt-out is
# removed, so ARM 1c installs the redaction like ARM 1 and observes no
# credentials - a control that cannot fail. The probe's own gate must
# refuse that, or its pass says nothing.
# ---------------------------------------------------------------------------
amputate "A6  the probe's positive control opts in too" "$PROBE" \
  '        install_log_redaction=install,' \
  '        install_log_redaction=True,'

# ---------------------------------------------------------------------------
# THE GATE. `ROWS == APPLIED` says every row measured something;
# VACUOUS says whether any row measured NOTHING.
# ---------------------------------------------------------------------------
echo "########## $ROWS/$ROW_FLOOR ROWS"
echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally applied "$APPLIED" "$ROWS"
echo "########## TOTAL SURVIVING ASSERTIONS: $TOTAL_SURVIVORS"
echo "########## VACUOUS ROWS: $VACUOUS"

if [ "$ROWS" -eq 0 ]; then
  echo "The harness ran ZERO rows; a green from it means nothing."
  exit 3
fi
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "::error::$ROWS/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         Every remaining row can still apply and still kill, so"
  echo "         ROWS == APPLIED says nothing about the ones that are gone."
  exit 1
fi
if [ "$ROWS" -ne "$APPLIED" ]; then
  echo "A ROW DID NOT APPLY ITS ANCHOR. It measured nothing and said so."
  exit 1
fi
if [ "$VACUOUS" -ne 0 ]; then
  echo "A VACUOUS ROW IS A FINDING: a deleted behaviour that nothing noticed."
  exit 1
fi
