#!/usr/bin/env bash
# U6 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the paging behaviour it claims to check is
# wrong, which is the vacuous-assertion shape this project has found in
# every unit so far.
#
# The AMPUTATION harness beside this one asks the different question -
# remove the behaviour ENTIRELY, does anything still report success -
# and its survivors are output rather than failure.
#
# THE ROWS THAT MATTER MOST HERE ARE M6 AND M7. They are the two arms of
# the completeness check (DESIGN.md:508-516), and they fail in opposite
# directions: M6 makes the check fire on EVERY call, M7 makes it fire on
# NONE. A suite with only one completeness case kills one of them and
# lets the other through, and the one it lets through is usually M6 -
# an implementation that alarms on the default path, which DESIGN.md:513
# says "would train everyone to ignore it".
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains, and this harness is untracked until it is
# committed.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and a mutation that swaps one value can be the same size inside one
# second - in which case the interpreter reuses stale bytecode, the
# mutated code never runs, and the row reports a clean survivor that is
# an instrument fault rather than a finding.

# `-e` deliberately omitted: these harnesses read the exit code of a suite that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CLIENT="src/fast_mcp_jobvite/services/jobvite_client.py"
SUITE="tests/test_pagination.py"
OUT=/tmp/u6-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPY, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can detect only a failed
# `cp`, never "the tree still carries this row's mutation". A corrupted
# backup passes that check and hands every later row a mutated tree.
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

FIRED=0
TOTAL=0

# ---------------------------------------------------------------------------
# mutate <label> <file> <test-selector> <old> <new>
# ---------------------------------------------------------------------------
mutate() {
  local label="$1" file="$2" selector="$3" old="$4" new="$5"
  TOTAL=$((TOTAL + 1))

  echo "########## $label"
  echo "  target: $selector"

  # DOES THE SELECTOR STILL RESOLVE? pytest exits 4 when a selector
  # matches nothing, and this harness treats ANY non-zero exit as a
  # kill - so a renamed or misspelled test would report KILLED on every
  # run, forever, while running nothing. TOTAL is already incremented,
  # so returning here makes fired != total and the run exits 1.
  if ! uv run --frozen pytest "$selector" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1; then
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  This row has been reporting KILLED without running. Fix the harness."
    echo
    return
  fi

  # SC2155: declared and assigned separately, so a failing `echo`/`tr`
  # cannot be masked by `local`'s own exit status.
  local backup
  backup="$BACKUP_DIR/${TOTAL}_client.py"
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
    echo "  MUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi

  uv run --frozen pytest "$selector" -q -p no:cacheprovider >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/client.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  if [ "$rc" -ne 0 ]; then
    FIRED=$((FIRED + 1))
    echo "  KILLED - the named test went red, as it must"
  else
    echo "  *** SURVIVED *** the named test passed against the mutation."
    echo "      The assertion does not check what its name claims."
    tail -1 "$OUT" | sed 's/^/      /'
  fi
  echo
}

# ===========================================================================
# start=0 - THE WHOLE MECHANISM, AND IT IS ONE CHARACTER
# ===========================================================================

# DESIGN.md:502-503: "Starting at 1 is the only choice that can silently
# lose a record, because on a 0-based server record zero is never
# requested." This is that one character.
mutate "M1  the scan starts at 1 instead of 0" \
  "$CLIENT" \
  "$SUITE::test_every_scan_starts_at_zero_on_the_wire" \
  'SCAN_START: Final = 0' \
  'SCAN_START: Final = 1'

# The override stops being per resource (DESIGN.md:517-519). Overriding
# the ONE route with an [OFFICIAL] base drags every [INFERRED] v2
# resource with it, which is exactly the base-guess this section refuses
# to make.
mutate "M2  a per-resource override is applied globally" \
  "$CLIENT" \
  "$SUITE::test_an_override_is_per_resource_and_not_global" \
  '        return self._start_base_overrides.get(path, SCAN_START)' \
  '        return next(iter(self._start_base_overrides.values()), SCAN_START)'

# The advance opens a one-record gap per page. Nothing errors; the scan
# returns a plausible, shorter set.
mutate "M3  the advance skips one record per page" \
  "$CLIENT" \
  "$SUITE::test_a_scan_is_whole_under_both_surviving_hypotheses" \
  '            start += count' \
  '            start += count + 1'

# ===========================================================================
# DE-DUPLICATION, AND ITS LIMITATION
# ===========================================================================

# The seen set never rejects anything, so a clamped page's boundary
# record is returned twice (DESIGN.md:504-505).
mutate "M4  the seen set never rejects a duplicate" \
  "$CLIENT" \
  "$SUITE::test_an_overlapping_page_drops_duplicates" \
  '                if ident in seen:' \
  '                if False:'

# The other direction: id-less records collapse onto one `None` key and
# all but the first are DELETED. The over-reading defence causing an
# under-read.
mutate "M5  records without an id are de-duplicated onto one key" \
  "$CLIENT" \
  "$SUITE::test_records_without_an_id_are_kept_not_collapsed" \
  '                if ident is None:' \
  '                if False:'

# ===========================================================================
# TERMINATION: A SHORT PAGE, AND NEVER `total`
# ===========================================================================

# The short-page test reads the DE-DUPLICATED count instead of the raw
# page. A full page that is entirely duplicate then looks short, and the
# scan stops early on exactly the clamping hypothesis the seen set
# exists to absorb (DESIGN.md:525).
mutate "M6  the short-page test reads the kept records, not the raw page" \
  "$CLIENT" \
  "$SUITE::test_a_full_page_of_duplicates_is_not_a_short_page" \
  '            if len(page) < count:' \
  '            if len(items) < count:'

# `total` becomes a loop condition, which DESIGN.md:526 forbids in
# exactly those words. A server that understates `total` truncates the
# scan and nothing reports it.
mutate "M7  total is used as a loop condition" \
  "$CLIENT" \
  "$SUITE::test_a_total_that_understates_does_not_end_the_loop_early" \
  '            if len(page) < count:
                short_page = True
                break' \
  '            if total is not None and len(items) >= total:
                short_page = True
                break
            if len(page) < count:
                short_page = True
                break'

# `total` is recomputed from the page rather than read from the
# envelope. `JOBVITE-API.md:398` records that `total` is the full
# result-set size and not the page size, so this makes every scan agree
# with itself and report nothing.
mutate "M8  total is counted from the page, not read from the envelope" \
  "$CLIENT" \
  "$SUITE::test_a_total_that_overstates_does_not_extend_the_loop" \
  '            reported = payload.get(TOTAL_KEY)' \
  '            reported = len(payload.get(items_key) or [])'

# ===========================================================================
# THE COMPLETENESS CHECK - BOTH ARMS, IN OPPOSITE DIRECTIONS
# ===========================================================================

# ARM TWO BROKEN: the check no longer asks whether the caller wanted
# everything, so a capped call reporting `showing 50 of 1,240` is logged
# as an anomaly. DESIGN.md:513: this "would fire the alarm on the
# default path and train everyone to ignore it".
mutate "M9  the completeness check fires on a capped call too" \
  "$CLIENT" \
  "$SUITE::test_completeness_does_not_fire_on_a_capped_call" \
  '        if not exhaustive or not short_page or not isinstance(total, int):' \
  '        if not short_page or not isinstance(total, int):'

# ARM ONE BROKEN: the check never fires at all. This is the failure the
# capped-call case CANNOT see, which is why both arms are required.
mutate "M10 the completeness check never fires" \
  "$CLIENT" \
  "$SUITE::test_completeness_fires_on_an_exhaustive_scan_with_a_gap" \
  '        if unique == total:
            return False' \
  '        return False
        if unique == total:
            return False'

# The count compared is the wrong one: the duplicates the seen set
# dropped are counted anyway, so the clamping hypothesis - which serves
# one duplicate per page after the first (DESIGN.md:499-501) - inflates
# `unique` past `total` and a WHOLE scan reports itself incomplete.
#
# R5-M4: THIS ROW'S TITLE AND BODY BOTH USED TO BE WRONG, in opposite
# directions. It read "completeness counts every record returned, not
# unique ones" over a body forcing `unique = total`.
#
#   * The TITLE named a mutation that cannot be detected. `scan()`
#     appends to `items` exactly once per new id and once per
#     unidentified record, so on the path where completeness runs
#     `len(items) == len(seen) + unidentified` IDENTICALLY. Measured:
#     `unique=len(items)` gives 448 passed, 6 deselected, exit 0. A
#     survivor that is not a defect - the row's stated subject is not a
#     behaviour this code has.
#   * The BODY was M10 in different clothes. Forcing `unique = total`
#     makes `if unique == total: return False` always taken, which is
#     exactly what M10 does. Measured: it killed M10's OWN named test,
#     `test_completeness_fires_on_an_exhaustive_scan_with_a_gap`, as
#     well as the one named here. So 16 rows held 15 behaviours and
#     "16/16 controls fired" overstated its own breadth.
#
# The mutation below is the one the title was reaching for, it is
# distinct from every other row, and it is the row that would have seen
# R5-H3's `unique` inflation - which the old body could not.
mutate "M11 the completeness count includes duplicates the seen set dropped" \
  "$CLIENT" \
  "$SUITE::test_a_scan_is_whole_under_both_surviving_hypotheses[1]" \
  '            unique=len(seen) + unidentified,' \
  '            unique=len(seen) + unidentified + duplicates,'

# ===========================================================================
# THE RESULT CAP - THE TRANSPORT HALF AND THE min()
# ===========================================================================

# The `min()` is gone and the transport cap wins always. The configured
# `JOBVITE_MAX_RESULTS` stops bounding anything that leaves the
# transport (DESIGN.md:473-475).
mutate "M12 the result cap drops the configured half of the min()" \
  "$CLIENT" \
  "$SUITE::test_the_result_cap_is_the_min_of_the_two_halves" \
  '        return min(self.transport_cap(jobfeed=jobfeed), self._max_results)' \
  '        return self.transport_cap(jobfeed=jobfeed)'

# The other operand: the configured half wins always and the transport
# cap stops bounding anything. A `min` written as either operand alone
# passes a one-sided test, which is why both rows exist.
mutate "M13 the result cap drops the transport half of the min()" \
  "$CLIENT" \
  "$SUITE::test_the_result_cap_is_the_min_of_the_two_halves" \
  '        return min(self.transport_cap(jobfeed=jobfeed), self._max_results)' \
  '        return self._max_results'

# The base is no longer per resource: `/v1/jobFeed`'s 1000 becomes v2's
# 500. Nothing errors and every feed scan silently doubles its request
# count.
mutate "M14 the jobFeed page cap is the v2 one" \
  "$CLIENT" \
  "$SUITE::test_the_jobfeed_route_uses_its_own_transport_cap" \
  'JOBFEED_PAGE_CAP: Final = 1000' \
  'JOBFEED_PAGE_CAP: Final = 500'

# The v2 transport cap moves. DESIGN.md:473 is the only source for 500
# and it is NOT an observation, which is why the constant is pinned by a
# case rather than left to whatever a later edit types.
mutate "M15 the v2 page cap is not the design's figure" \
  "$CLIENT" \
  "$SUITE::test_the_transport_caps_are_the_designs_figures" \
  'V2_PAGE_CAP: Final = 500' \
  'V2_PAGE_CAP: Final = 50'

# A caller's `limit` is no longer clamped to the configured cap, so an
# argument raises `JOBVITE_MAX_RESULTS` from outside.
mutate "M16 a caller's limit is not clamped to the configured cap" \
  "$CLIENT" \
  "$SUITE::test_a_limit_above_the_configured_cap_is_clamped_to_it" \
  '        effective_limit = cap if exhaustive else min(limit or 0, cap)' \
  '        effective_limit = cap if exhaustive else (limit or 0)'

# ===========================================================================
# THE ROW FLOOR
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted - or all skipped - reports fully green. Lowering this
# number is a visible diff that has to be defended.
ROW_FLOOR=16
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "########## $TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

echo "########## $FIRED/$TOTAL controls fired."
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "A SURVIVING ROW IS A FINDING. Read it before trusting the suite."
  exit 1
fi
