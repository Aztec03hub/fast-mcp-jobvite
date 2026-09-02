#!/usr/bin/env bash
# BODY-CAP AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
# Mutation asks: "break one rule - does the NAMED test notice?"
# Amputation asks: "remove the SUBJECT ENTIRELY - does anything still report
# success?" Only amputation finds an assertion that passes when its subject is
# not there, which is not a weak test but a false instrument.
#
# THIS HARNESS DOES NOT EXIT NON-ZERO ON SURVIVORS - survivors are the OUTPUT.
# It exits non-zero only if it could not run, if the intact baseline is red, if
# an amputation failed to land, or if it lost rows against its floor.
#
# For each row it prints the pass/fail counts and NAMES every test that still
# passes, so the report can say WHICH assertions survived and why rather than
# asserting that none did.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT `git diff`. `git diff --quiet`
# reports NO DIFFERENCE for an untracked file whatever it contains, and four
# amputation rows on another unit were reported "did not land" that way when all
# four had landed.
#
# PYTHONDONTWRITEBYTECODE=1, for the same reason the mutation harness sets it:
# `.pyc` invalidation keys on (mtime, size) and a stale cache makes an amputated
# tree run the intact code, which reads as a clean survivor.

set -uo pipefail

# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. The names below are separate decisions,
# even where two of them share a value today.
BASELINE_TIMEOUT=900
ROW_TIMEOUT=900

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"
# ONLY 0 AND 1 ARE MEASUREMENTS (#254). One sourced copy, never retyped -
# the reasoning and the measurement that established it live in the file.
# shellcheck source=lib/verdict-guard.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/verdict-guard.sh"

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

HARDENING="src/fast_mcp_jobvite/http_hardening.py"
SUITE="tests/test_body_cap.py"
OUT=/tmp/body-cap-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

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
  echo "ABORT: the intact suite is red; amputation results would be meaningless."
  tail -20 "$OUT"
  exit 3
fi
tail -1 "$OUT"
echo

ROWS=0
# DERIVED - see the note beside the check at the end of this file.
# The assignment is bare on its own line because docs/reviews/check-row-floors.py
# matches `^\s*ROW_FLOOR=(\d+)\s*$`: a trailing comment here makes the floor
# invisible to the checker, which is the same "a floor nobody can see is a floor
# nobody checks" shape the floor itself exists to catch.
ROW_FLOOR=5

# ---------------------------------------------------------------------------
# amputate <label> <file> <old> <new>
#
# `file` is a PARAMETER rather than the module-level `$HARDENING` even though
# every row passes the same value. scripts/check-harness-anchors.py reads a
# helper's signature to learn which file each anchor is checked against, and it
# refuses to guess past a helper that takes an `old` anchor and names no target.
# It said so about THIS FILE, in as many words, and the fix is the signature
# rather than the checker: an anchor whose target a static reader cannot resolve
# is an anchor nothing defends.
#
# `old` must be UNIQUE in the file. A `str.replace` that matches nothing
# silently no-ops, and the row would then print a survivor list measured
# against an INTACT tree - every name in it a false finding.
# ---------------------------------------------------------------------------
amputate() {
  local label="$1" file="$2" old="$3" new="$4"
  ROWS=$((ROWS + 1))

  echo "########## $label"

  cp "$file" "$BACKUP_DIR/hardening.py" ||
    { echo "  COULD NOT BACK UP"; exit 3; }

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
    echo "  AMPUTATION DID NOT LAND - the anchor moved. Fix the harness."
    cp "$BACKUP_DIR/hardening.py" "$file"
    exit 1
  fi

  if cmp -s "$file" "$BACKUP_DIR/hardening.py"; then
    echo "  AMPUTATION DID NOT LAND despite a successful write. Fix the harness."
    cp "$BACKUP_DIR/hardening.py" "$file"
    exit 1
  fi

  timeout "$ROW_TIMEOUT" uv run --frozen pytest "$SUITE" -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?
  tail -1 "$OUT"

  local survivors
  survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    echo "  survivors (assertions that still reported success):"
    echo "$survivors" | sed 's/^/    /'
  fi

  cp "$BACKUP_DIR/hardening.py" "$file"
  if ! cmp -s "$file" "$PRISTINE_DIR/hardening.py"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy"
    echo "  taken before row 1. STOPPING."
    exit 3
  fi

  verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"
  echo
}

# --- A. the cap does nothing at all ----------------------------------------
#
# THE ROW THAT MATTERS. The class is still there, still constructed, still
# mounted, still named in every import - and it passes every byte through. Any
# assertion that survives this is an assertion about the SHAPE of the code
# rather than about the behaviour, and the whole of DESIGN.md:165 would be
# undischarged with the suite reporting green.
amputate "A. BodySizeLimitMiddleware.__call__ is a bare passthrough" \
  "$HARDENING" \
  '        if scope["type"] != "http":' \
  '        if True:'

# --- B. the declared-length arm is gone ------------------------------------
#
# Arm 2 alone. Anything that survives here is bounded by the streaming sum, so
# the survivor list is the answer to "what does arm 1 uniquely buy".
amputate "B. the Content-Length arm never fires" \
  "$HARDENING" \
  '        declared = self._declared_length(scope)' \
  '        declared = None'

# --- C. the streaming arm is gone ------------------------------------------
#
# Arm 1 alone - a header-only cap. This is the shape a careless implementation
# actually takes, and the survivor list here is the closest thing this harness
# has to a threat model.
amputate "C. the streaming bound never fires - a header-only cap" \
  "$HARDENING" \
  '                seen += len(message.get("body", b""))
                if seen > self.max_bytes:
                    raise _BodyTooLarge' \
  '                pass'

# --- D. it is not mounted --------------------------------------------------
#
# The class is intact and correct; nothing constructs it. This is the exact
# "reads as discharged" shape ADR-0029 refused for MAX_PAYLOAD_BYTES, and every
# arm that tests the CLASS rather than the SERVER must survive it - so the
# survivor list here should be large, and the arms that go red are the ones
# holding the wiring up.
amputate "D. http_run_kwargs mounts nothing" \
  "$HARDENING" \
  '        "middleware": [
            ASGIMiddleware(
                BodySizeLimitMiddleware,
                max_bytes=MAX_REQUEST_BODY_BYTES,
            )
        ],' \
  '        "middleware": [],'

# --- E. the refusal carries no problem object ------------------------------
#
# The cap still refuses; the caller gets a bare 422 with an empty body. Every
# arm that checks only a status code survives, and that is the point: a status
# code alone cannot tell this control's refusal from any other 422 the stack
# might produce.
amputate "E. the refusal is an empty body, not a problem object" \
  "$HARDENING" \
  '        body = self._problem_response(scope, received)' \
  '        body = b""'

echo "########## $ROWS/$ROW_FLOOR ROWS"
echo "########## END. Survivors above are the finding, not a failure."

# THE ROW FLOOR.
#
# `FIRED -ne TOTAL` cannot exist here, because this harness deliberately does
# not fail on survivors. That leaves a harness which, with four of its five rows
# deleted, would print the same closing sentence and exit 0. The counter is what
# makes a lost row loud; a survivor still does not fail the run, and only a
# MISSING ROW does.
#
# DERIVED: the run that first completed this harness printed `5/5 ROWS` on its
# own counter, and 5 is that run's own ROWS value read off its own output - not
# a count of `amputate` calls taken by reading this file, which is the count
# that goes stale the moment a row stops applying. Lowering this is a visible
# diff that has to be defended.
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "::error::$ROWS/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         A harness with fewer rows than its floor is green for the"
  echo "         wrong reason. Survivors are the output; a missing row is not."
  exit 1
fi
