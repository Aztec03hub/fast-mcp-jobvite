#!/usr/bin/env bash
# U6 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything still
#                    report success?
#
# Amputation has exposed a vacuous assertion in every unit built on this
# project so far. SURVIVORS ARE THE OUTPUT, not the failure: for each
# row this prints the counts and NAMES every test that still passed, so
# the report can say which assertions survived and why.
#
# WHAT IS DELIBERATELY NOT AMPUTATED HERE, and it is worth saying rather
# than leaving as a gap someone rediscovers. Two behaviours cannot be
# removed by this harness without hanging it: the `start += count`
# advance, and the short-page termination with no replacement. Delete
# either and the scan requests the same full page forever against a
# server that keeps answering. Both are covered by the MUTATION harness
# instead (M3 and M6/M7), where the change is bounded. A row that hangs
# CI is not a measurement.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation that replaces a body with a constant can be the same
# size inside one second, in which case the interpreter reuses stale
# bytecode and the amputated code never runs.

# `-e` deliberately omitted: these harnesses read the exit code of a suite that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_pagination.py"
OUT=/tmp/u6-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

cp "$CLIENT" "$PRISTINE_DIR/client.py" ||
  { echo "COULD NOT TAKE PRISTINE COPY of $CLIENT"; exit 3; }

echo "########## BASELINE - the intact tree"
if ! uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 "$OUT"
  exit 3
fi
tail -1 "$OUT"
echo

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

  # SC2155: declared and assigned separately.
  local backup
  backup="$BACKUP_DIR/${ROWS}_client.py"
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

  # `timeout` is a guard, not a policy. Every row here is believed
  # bounded (see the header), and a row that hangs anyway must report
  # rather than stall the gate: the non-zero exit reads as a kill, and
  # the log carries the reason.
  timeout 300 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA \
    >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/client.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 300s - this row is unbounded. Move it to the"
    echo "  mutation harness, where the change is bounded."
  fi

  tail -1 "$OUT" | sed 's/^/  /'

  # THE VACUOUS-ROW GATE. The verdict is the RUN'S EXIT CODE, not
  # `grep -c "^FAILED"`: that grep misses ERROR entirely, and a
  # collection error is a row going red for a real reason.
  if [ "$rc" -eq 0 ]; then
    echo "  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red."
    echo "      Every assertion below survived. This row measures nothing."
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
    echo "  survivors ($n assertions still reported success):"
    printf '%s\n' "$survivors" | sed 's/^/    /'
  fi
  echo
}

# ---------------------------------------------------------------------------
# A1 - DE-DUPLICATION IS GONE ENTIRELY. Every record a clamped page
# re-serves is returned again. DESIGN.md:465-466 deleted outright.
# ---------------------------------------------------------------------------
amputate "A1  the seen set does not exist; nothing is de-duplicated" \
  "$CLIENT" \
  '                if ident in seen:
                    duplicates += 1
                    continue
                seen.add(ident)
                items.append(item)' \
  '                seen.add(ident)
                items.append(item)'

# ---------------------------------------------------------------------------
# A2 - THE COMPLETENESS CHECK IS GONE. An exhaustive scan missing records
# reports a clean, short answer. This is the "wrong zero that explains
# itself" shape, and every case claiming to check completeness must die.
# ---------------------------------------------------------------------------
amputate "A2  the completeness check never runs at all" \
  "$CLIENT" \
  '        if not exhaustive or not short_page or not isinstance(total, int):
            return False' \
  '        return False
        if not exhaustive or not short_page or not isinstance(total, int):
            return False'

# ---------------------------------------------------------------------------
# A3 - THE OPPOSITE AMPUTATION, and the one DESIGN.md:474 names. The
# check fires on EVERY call, so the default capped path reports an
# anomaly and everyone learns to ignore the alarm. A suite with only
# arm one survives this completely.
# ---------------------------------------------------------------------------
amputate "A3  the completeness check fires on every call" \
  "$CLIENT" \
  '        if not exhaustive or not short_page or not isinstance(total, int):
            return False
        if unique == total:
            return False' \
  '        if not isinstance(total, int):
            return False'

# ---------------------------------------------------------------------------
# A4 - PAGING IS GONE. One request, first page, done. Every record past
# the first page is lost and the scan reports success.
# ---------------------------------------------------------------------------
amputate "A4  the scan issues exactly one request and stops" \
  "$CLIENT" \
  '            if len(page) < count:
                short_page = True
                break' \
  '            short_page = True
            break
            if len(page) < count:
                short_page = True
                break'

# ---------------------------------------------------------------------------
# A5 - BASE-AGNOSTICISM IS GONE. Every scan starts at the vendor's
# claimed base. On a 0-based server record zero is never requested,
# which DESIGN.md:463-464 says is the one choice that silently loses a
# record.
# ---------------------------------------------------------------------------
amputate "A5  every scan starts at the vendor's claimed base of 1" \
  "$CLIENT" \
  '        return self._start_base_overrides.get(path, SCAN_START)' \
  '        return 1'

# ---------------------------------------------------------------------------
# A6 - THE TRANSPORT HALF OF THE RESULT CAP IS GONE. `min()` collapses to
# the configured value and nothing bounds what a route may be asked for.
# This is U6's half of a behaviour U5 owns the other half of, so a
# survivor here is a claim about THIS file only.
# ---------------------------------------------------------------------------
amputate "A6  the result cap has no transport half; min() is gone" \
  "$CLIENT" \
  '        return min(self.transport_cap(jobfeed=jobfeed), self._max_results)' \
  '        return self._max_results'

# ---------------------------------------------------------------------------
# A7 - THE CALLER'S LIMIT IS NEVER ENFORCED. Both the loop break and the
# final truncation go, so a `limit=50` call returns everything Jobvite
# holds - and reports it as an ordinary result.
# ---------------------------------------------------------------------------
amputate "A7  a caller's limit bounds nothing" \
  "$CLIENT" \
  '            if not exhaustive and len(items) >= effective_limit:
                capped = True
                break' \
  '            if False:
                capped = True
                break'

# ---------------------------------------------------------------------------
# A8 - RECORDS WITHOUT AN ID ARE DROPPED. A silent under-read produced by
# the de-duplication path, which is the failure DESIGN.md:465-468 warns
# about arriving from the other side.
# ---------------------------------------------------------------------------
amputate "A8  records carrying no id are discarded" \
  "$CLIENT" \
  '                    unidentified += 1
                    items.append(item)
                    continue' \
  '                    continue'

# ---------------------------------------------------------------------------
# A9 - `total` IS NEVER READ. The envelope's own number never reaches
# the result, so the completeness check has nothing to compare against
# and is silent for a reason no caller can see.
# ---------------------------------------------------------------------------
amputate "A9  total is never read from the envelope" \
  "$CLIENT" \
  '            reported = payload.get(TOTAL_KEY)
            if isinstance(reported, int):
                total = reported' \
  '            pass'

# ---------------------------------------------------------------------------
# A10 - THE ANOMALY IS DETECTED AND NEVER RECORDED. `incomplete` is still
# returned, so a caller inspecting the object still sees it; nothing
# reaches the log. A suite asserting only the flag survives this, and an
# operator watching logs sees a complete-looking scan.
# ---------------------------------------------------------------------------
amputate "A10 an incomplete scan is never logged" \
  "$CLIENT" \
  '        logger.warning(
            "jobvite scan incomplete",
            route=redact_url(f"{V2_BASE_URL}{path}"),
            unique=unique,
            reported_total=total,
        )
        return True' \
  '        return True'

echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
echo "########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: $TOTAL_SURVIVORS"
echo "(Survivors are the OUTPUT. Read each one and say why it survived.)"

# The gate is that every row APPLIED its anchor. A row that could not
# find its anchor tested nothing and must not be read as a clean result.
if [ "$APPLIED" -ne "$ROWS" ]; then
  echo "::error::$((ROWS - APPLIED)) row(s) did not apply an anchor - the harness is stale"
  exit 1
fi

# `APPLIED -ne ROWS` is satisfied by 0 == 0, so a harness whose rows were
# all deleted would be fully green. Lowering this number is a visible
# diff that has to be defended.
ROW_FLOOR=10
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "::error::the harness holds $ROWS rows, below its floor of $ROW_FLOOR"
  exit 1
fi

# Survivors are output; a row that killed NOTHING is not.
if [ "$VACUOUS" -ne 0 ]; then
  echo "::error::$VACUOUS VACUOUS ROW(S) - a behaviour was deleted and nothing"
  echo "         went red. Search the log above for 'VACUOUS ROW'."
  exit 1
fi
