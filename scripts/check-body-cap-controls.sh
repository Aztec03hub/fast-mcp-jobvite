#!/usr/bin/env bash
# BODY-CAP MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test passes
# against a tree where the behaviour it claims to check is wrong.
#
# THE TWO ROWS THAT MATTER MOST ARE M4 AND M11, and they are the same defect
# from two directions: the STREAMING arm. A body cap that reads only
# `Content-Length` looks completely correct against every declared-length arm
# and is defeated by a chunked request, which costs an attacker nothing. If
# either of those rows survives, the case DESIGN.md:165 exists for is unguarded
# and the suite is reporting it clean.
#
# M1 and M2 are the OFF-BY-ONE pair, one per framing. An accepting arm at the
# boundary is the only thing that can see them: every rejecting arm in the file
# stays green when the cap refuses one byte too early.
#
# `utils/constraints.py` is NOT mutated here. Its cap is a different control on
# a different transport (ADR-0029), it has its own harness rows under U14, and
# mutating it here would produce rows that are really about that unit.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT `git diff`. `git diff --quiet`
# reports NO DIFFERENCE for an untracked file whatever it contains, which cost
# four amputation rows on another unit a "did not land" verdict when all four
# had landed.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size), and a
# mutation swapping one operator is the same size inside one second - the
# interpreter then reuses stale bytecode, the mutated code never runs, and the
# row reports a clean survivor that is an instrument fault, not a finding.

set -uo pipefail

# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. The names below are separate decisions,
# even where two of them share a value today.
BASELINE_TIMEOUT=900
ROW_TIMEOUT=300
SELECTOR_TIMEOUT=120

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

HARDENING="src/fast_mcp_jobvite/http_hardening.py"
SUITE="tests/test_body_cap.py"
# THE PYTEST LOG THIS RUN READS ITS VERDICTS OUT OF. Per-RUN, never a fixed
# name. Two worktrees on one machine run these harnesses concurrently, and a
# fixed path gives both the SAME INODE: independent `>` offsets leave a NUL
# hole, `grep` then reports "binary file matches" on STDERR and returns an
# EMPTY capture at exit 0, and a rival's `FAILED <nodeid>` lines are read as
# THIS run's kill. Both directions were reproduced - see
# docs/reviews/probe-284-shared-path-collision.sh, and #262 for the false kill
# this class already produced. CI can never catch a regression here: the runner
# has no second worktree.
OUT="$(mktemp /tmp/body-cap-mut-XXXXXX)"
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR" "$OUT"' EXIT

# THE PRISTINE COPY, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file backup`
# compares equal BY CONSTRUCTION and can only detect a failed `cp` - a CORRUPTED
# backup passes it and hands every later row a mutated tree.
cp "$HARDENING" "$PRISTINE_DIR/hardening.py" ||
  { echo "COULD NOT TAKE PRISTINE COPY of $HARDENING"; exit 3; }

echo "########## BASELINE - the intact tree"
timeout "$BASELINE_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - ${BASELINE_TIMEOUT}s with no result, on the INTACT tree."
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

FIRED=0
TOTAL=0

# Every selector a row aims at, in row order. Verified ONCE against the INTACT
# tree after the last row - see the block above harness_result_ran.
SELECTORS=()

# ---------------------------------------------------------------------------
# mutate <label> <file> <test-selector> <old> <new>
#
# `file` is a PARAMETER rather than the module-level `$HARDENING` even though
# every row passes the same value. scripts/check-harness-anchors.py reads a
# helper's signature to learn which file each anchor is checked against, and a
# helper with an `old` parameter and no `file` one is a PARSER GAP it refuses to
# guess past - correctly, because an anchor whose target the static checker
# cannot resolve is an anchor nothing defends.
# ---------------------------------------------------------------------------
mutate() {
  local label="$1" file="$2" selector="$3" old="$4" new="$5"
  TOTAL=$((TOTAL + 1))
  # Recorded for the ONE intact-tree check after the last row (#249/R24-H1).
  # Appended here, beside the TOTAL it must equal, so a row added without a
  # selector shows up as a count mismatch rather than as silent under-coverage.
  SELECTORS+=("$selector")

  echo "########## $label"
  echo "  target: $selector"

  cp "$file" "$BACKUP_DIR/hardening.py" ||
    { echo "  COULD NOT BACK UP"; return; }

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
    cp "$BACKUP_DIR/hardening.py" "$file"
    echo
    return
  fi

  if cmp -s "$file" "$BACKUP_DIR/hardening.py"; then
    echo "  MUTATION DID NOT LAND despite a successful write"
    cp "$BACKUP_DIR/hardening.py" "$file"
    echo
    return
  fi

  timeout "$ROW_TIMEOUT" uv run --frozen pytest "$selector" -q -p no:cacheprovider >"$OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after ${ROW_TIMEOUT}s - this row NEVER FINISHED. Not a kill,"
    echo "  not a survivor: no verdict below is a measurement of this row."
  fi

  cp "$BACKUP_DIR/hardening.py" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/hardening.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy"
    echo "  taken before row 1. STOPPING."
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
# THE BOUNDARY - one off-by-one per framing
# ===========================================================================
#
# Both of these make the cap refuse a body of EXACTLY 1 MiB, which
# DESIGN.md:165 admits. Every rejecting arm in the suite stays green under
# them; only an accepting arm sitting ON the boundary can see it.

mutate "M1  the declared-length arm refuses a body of exactly the cap" \
  "$HARDENING" \
  "$SUITE::test_a_declared_body_at_or_under_the_cap_is_ACCEPTED" \
  '        if declared is not None and declared > self.max_bytes:' \
  '        if declared is not None and declared >= self.max_bytes:'

mutate "M2  the streaming arm refuses a body of exactly the cap" \
  "$HARDENING" \
  "$SUITE::test_a_CHUNKED_body_at_or_under_the_cap_is_ACCEPTED" \
  '                if seen > self.max_bytes:' \
  '                if seen >= self.max_bytes:'

# ===========================================================================
# EACH ARM, AMPUTATED IN ISOLATION
# ===========================================================================

mutate "M3  the declared-length arm never fires" \
  "$HARDENING" \
  "$SUITE::test_a_declared_body_one_byte_over_the_cap_is_REFUSED" \
  '        if declared is not None and declared > self.max_bytes:' \
  '        if declared is not None and declared > self.max_bytes * 1000:'

# THE ROW THAT MATTERS MOST. A cap that reads only the header is the
# defect this whole unit exists to prevent, and it passes M1 and M3.
mutate "M4  the STREAMING bound never fires - header-only, the attacker's case" \
  "$HARDENING" \
  "$SUITE::test_a_CHUNKED_body_one_byte_over_the_cap_is_REFUSED" \
  '                if seen > self.max_bytes:' \
  '                if seen > self.max_bytes * 1000:'

# ITS TWIN, from the other direction: the sum stops being a SUM. A
# per-chunk comparison passes every request whose chunks are each small,
# which is every chunked request a client actually sends.
mutate "M11 the running sum becomes a per-chunk comparison" \
  "$HARDENING" \
  "$SUITE::test_a_CHUNKED_body_one_byte_over_the_cap_is_REFUSED" \
  '                seen += len(message.get("body", b""))' \
  '                seen = len(message.get("body", b""))'

# ===========================================================================
# THE NUMBER, AND WHETHER ANYTHING MOUNTS IT
# ===========================================================================

mutate "M5  the cap is not the design's number" \
  "$HARDENING" \
  "$SUITE::test_the_cap_is_the_designs_own_number" \
  'MAX_REQUEST_BODY_BYTES: Final = 1024 * 1024' \
  'MAX_REQUEST_BODY_BYTES: Final = 2 * 1024 * 1024'

# A correct control that nothing constructs is the "reads as discharged"
# shape ADR-0029 refused for MAX_PAYLOAD_BYTES. Every arm in section 2 of
# the suite still passes under this row.
mutate "M6  http_run_kwargs stops mounting the cap" \
  "$HARDENING" \
  "$SUITE::test_http_run_kwargs_mounts_the_body_cap" \
  '        "middleware": [
            ASGIMiddleware(
                BodySizeLimitMiddleware,
                max_bytes=MAX_REQUEST_BODY_BYTES,
            )
        ],' \
  '        "middleware": [],'

# ===========================================================================
# WHAT THE CALLER SEES
# ===========================================================================

# The registry row and the HTTP status line must not come apart. This
# writes 413 - the status ADR-0029 named as the other candidate - onto
# the wire while the problem object still says 422, which is exactly the
# incoherent response RFC 9457 forbids and the deliberate choice this
# unit made is meant to prevent.
mutate "M7  the status line stops matching the registry row" \
  "$HARDENING" \
  "$SUITE::test_a_declared_body_one_byte_over_the_cap_is_REFUSED" \
  '                "status": VALIDATION_ERROR.status,' \
  '                "status": 413,'

mutate "M8  the refusal is not served as application/problem+json" \
  "$HARDENING" \
  "$SUITE::test_a_declared_body_one_byte_over_the_cap_is_REFUSED" \
  '                    (b"content-type", b"application/problem+json"),' \
  '                    (b"content-type", b"application/json"),'

mutate "M9  the caller's correlation id is discarded" \
  "$HARDENING" \
  "$SUITE::test_a_refusal_echoes_a_valid_inbound_request_id" \
  '            resolve_request_id(inbound),' \
  '            resolve_request_id(None),'

# ===========================================================================
# THE EDGES
# ===========================================================================

mutate "M10 a negative Content-Length is trusted instead of ignored" \
  "$HARDENING" \
  "$SUITE::test_a_malformed_content_length_falls_through_to_the_running_bound" \
  '            return declared if declared >= 0 else None' \
  '            return declared'

mutate "M12 a websocket scope is answered with an HTTP response" \
  "$HARDENING" \
  "$SUITE::test_a_non_http_scope_is_not_answered_with_an_HTTP_RESPONSE" \
  '        if scope["type"] != "http":' \
  '        if scope["type"] == "never-any-scope-type":'

# ===========================================================================
# THE ROW FLOOR
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were all
# deleted reported fully green. Lowering this number is a visible diff that has
# to be defended.
#
# DERIVED: the run that first completed this harness printed `12/12 controls
# fired`, and 12 is that run's own TOTAL read off its own last line - not a
# count of `mutate` calls made by reading the file, which is the count that goes
# stale when a row stops applying.
ROW_FLOOR=12

# ===========================================================================
# DO ALL THE SELECTORS STILL RESOLVE? ONE process, on the INTACT tree.
# ===========================================================================
#
# The property: a renamed, moved or misspelled test must not report a verdict
# forever while running nothing. Until now it was bought with a SECOND pytest
# process per row - `--collect-only`, inside mutate(), before each mutation
# landed. That doubled the process count of the whole harness, and process
# startup is what a per-row harness is made of.
#
# It also asked the question in the wrong place. The property is about the
# INTACT tree, and mutate() is a loop over MUTATED ones. #244 tried replacing
# the per-row probe with a per-row rule reading pytest's rc plus its
# `^ERROR <file> - <Exception>` line, and R24 measured that rule wrong in BOTH
# directions:
#
#   * A mutation that breaks an import reached from `tests/conftest.py` makes
#     pytest abort at CONFTEST LOAD: rc=4, "ImportError while loading conftest",
#     and NO short-test-summary section - so the discriminating line is absent
#     and a REAL KILL reads as a renamed selector.
#   * A genuinely renamed selector PLUS a mutation that breaks the TEST
#     module's own import DOES print that line, so the guard stayed silent and
#     the row was counted KILLED on a test that does not exist.
#
# Neither direction is answerable from a MUTATED run. So ask the intact tree,
# ONCE, after the last row. Every row above restored its file and compared it
# to the pristine copy (exit 3 if it differed), so the tree here is the tree
# row 1 started on, and one `pytest "${SELECTORS[@]}" --collect-only` covers
# the whole row set: one extra process per HARNESS in place of one per ROW.
#
# The recorded count is checked against TOTAL first, so a row that ran without
# recording its selector cannot pass as covered. It REFUSES rather than
# reporting - exit 3, and `harness_result_emit`'s EXIT trap prints
# `status=refused`, which is the honest word for a harness that cannot aim.
#
# Ported from 84d4959 (R24-H1), which was written, reviewed and never landed.
# The same shape already sits on main in check-u3-audit-controls.sh, arrived at
# from the other direction by #252's per-row selection work.
# `-eq 0` FIRST, and it is not redundant with the mismatch test beside it
# (R249-L2). At TOTAL=0 - every `mutate` call deleted - `0 -ne 0` is FALSE, so
# the mismatch arm alone passes, `pytest "${SELECTORS[@]}" --collect-only` runs
# with NO node ids, collects the WHOLE suite, exits 0, and the success line
# below announces a check that asked nothing. `check-u3-audit-controls.sh:461`
# carries this guard for the same reason; dropping it was this port's own
# defect, not one inherited from 84d4959.
if [ "$TOTAL" -eq 0 ] || [ "${#SELECTORS[@]}" -ne "$TOTAL" ]; then
  echo "########## RECORDED ${#SELECTORS[@]} SELECTORS FOR $TOTAL ROWS."
  echo "The check below covers exactly the selectors it is handed. At zero rows"
  echo "it would collect the whole suite and pass having asked nothing; at a"
  echo "mismatch it cannot cover every row. Either way its pass would mean less"
  echo "than it claims. Fix the harness."
  exit 3
fi
timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "${SELECTORS[@]}" \
  --collect-only -q -p no:cacheprovider >"$OUT" 2>&1
sel_rc=$?
if [ "$sel_rc" -ne 0 ]; then
  echo "########## A SELECTOR DOES NOT RESOLVE ON THE INTACT TREE (pytest rc=$sel_rc)."
  if [ "$sel_rc" -eq 124 ]; then
    echo "Read this, not the lines below: collection NEVER FINISHED within"
    echo "${SELECTOR_TIMEOUT}s. That is a hang, not a rename."
  fi
  echo "At least one row named a test that was renamed or moved, so that row"
  echo "has been reporting a verdict without ever running its killer."
  echo "pytest, on the restored tree:"
  tail -20 "$OUT"
  echo "Any row above whose target appears in those ERROR lines printed a"
  echo "verdict it did not earn - read the target, not the verdict."
  exit 3
fi
echo "########## ALL $TOTAL SELECTORS RESOLVE (one intact-tree process)"
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "########## $TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

echo "########## $FIRED/$TOTAL controls fired."
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally fired "$FIRED" "$TOTAL"
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "A SURVIVING ROW IS A FINDING. Read it before trusting the suite."
  exit 1
fi
