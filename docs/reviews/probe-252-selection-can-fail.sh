#!/usr/bin/env bash
# THE AMPUTATION ARM FOR TASK #252's PER-ROW SELECTION.
#
# `scripts/check-u3-audit-controls.sh` now runs each row against the tests the
# coverage map says executed the mutated lines, instead of the whole three-file
# `$SUITE`. The conversion's own evidence is that all fifteen rows keep the
# SAME verdict. That is a necessary check and it is not a sufficient one: a
# selection that could never fail would produce exactly the same fifteen greens.
#
# So this probe breaks, one at a time, the very test the map SELECTED for a row,
# and requires that row to stop reporting `killed`.
#
# THE BREAK IS DELIBERATELY AN ASSERTION-ECTOMY, NOT A DELETION. Each arm keeps
# the test CALLING the code and removes only what it asserts. A deleted test
# would stop executing the mutated lines, drop out of the coverage map, and take
# the row down the WIDE fallback - which would prove that the fallback works,
# not that the SELECTED path can fail. Removing the assertion leaves the test in
# the map, leaves it named in the row's selector line, and still makes it
# incapable of failing. That is the arm that discriminates.
#
# `-e` deliberately omitted: this probe reads the exit code of a harness that is
# EXPECTED to go non-zero in every arm. See
# docs/adr/0023-harnesses-drop-e-from-strict-mode.md.
set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). Without it
# `check-row-floor-controls.sh` cannot tell a fired floor from a silent one -
# it said so, in those words, the first time it was pointed at this file.
# shellcheck source=../../scripts/lib/harness-result.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/harness-result.sh"

# TWO levels up, not one: this probe lives in `docs/reviews/`, where the
# `/..` that the `scripts/` harnesses use lands on `docs/`. Written wrong the
# first time and caught only because every arm then reported
# `FileNotFoundError: tests/test_audit.py` - a probe whose paths are wrong
# must not be able to print a quiet zero.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 3

HARNESS=scripts/check-u3-audit-controls.sh

# The precondition the wrong REPO_ROOT above would have violated, asserted
# rather than left to be diagnosed from three stack traces.
for required in "$HARNESS" tests/test_audit.py tests/test_redaction.py; do
  [ -f "$required" ] || {
    echo "ABORT: $required not found from REPO_ROOT=$REPO_ROOT."
    echo "This probe's paths are relative to the repository root; if that is"
    echo "wrong every arm below fails for a reason that is not the subject."
    exit 3
  }
done
OUT=/tmp/probe-252-arm.txt
ARMS_RUN=0
ARMS_PASSED=0

# Refuse a dirty test tree rather than measure someone's edit and then
# `git checkout --` it away. `git status --porcelain`, not `git diff`, because
# a staged edit reads CLEAN to `git diff` and this probe restores from the
# index.
for f in tests/test_audit.py tests/test_redaction.py; do
  if [ -n "$(git status --porcelain -- "$f")" ]; then
    echo "ABORT: $f has uncommitted changes. This probe edits and restores it"
    echo "with 'git checkout --', which would destroy your work."
    exit 3
  fi
done

# ---------------------------------------------------------------------------
# arm <row-id> <killer-test> <file> <old> <new>
#
# Asserts, in order: the anchor is unique; the edit landed; the row's selector
# line still NAMES the killer with a numeric node count (i.e. the row did NOT
# take the wide fallback); the row's verdict is no longer `killed by`; and the
# file is restored byte-for-byte afterwards.
# ---------------------------------------------------------------------------
arm() {
  local row="$1" killer="$2" file="$3" old="$4" new="$5"
  ARMS_RUN=$((ARMS_RUN + 1))
  echo "########## ARM $row - neuter the assertion in $killer"

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
    echo "  COULD NOT APPLY - the anchor moved. Fix this probe."
    return
  fi

  if git diff --quiet -- "$file"; then
    echo "  DID NOT LAND despite a successful write"
    git checkout -- "$file"
    return
  fi

  bash "$HARNESS" >"$OUT" 2>&1
  local harness_rc=$?

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "  RESTORE FAILED - $file still differs. STOPPING."
    exit 3
  fi

  local sel_line verdict_line
  sel_line=$(grep -E "^$row .*: SELECTOR " "$OUT" | tail -1)
  verdict_line=$(grep -E "^$row " "$OUT" | grep -v ': SELECTOR ' | tail -1)
  echo "  selector: $sel_line"
  echo "  verdict : $verdict_line"
  echo "  harness : rc=$harness_rc  $(grep -E '^HARNESS-RESULT' "$OUT" | tail -1)"

  # The row must still be SELECTING - a wide fallback here would mean the arm
  # measured the fallback rather than the selection.
  case "$sel_line" in
    *"SELECTOR "[0-9]*" node(s)"*) ;;
    *)
      echo "  ARM VOID: $row took the WIDE fallback, so this arm did not test"
      echo "  the selected path. Pick a different row."
      echo
      return
      ;;
  esac
  case "$sel_line" in
    *"$killer"*) ;;
    *)
      echo "  ARM VOID: the selector no longer names $killer, so the break"
      echo "  removed the test from the map instead of disarming it."
      echo
      return
      ;;
  esac

  case "$verdict_line" in
    *"killed by"*)
      echo "  ARM FAILED: the row still reports killed with its named test"
      echo "  unable to fail. The selection is VACUOUS for this row."
      ;;
    *)
      if [ "$harness_rc" -eq 0 ]; then
        echo "  ARM FAILED: the row stopped being killed and the harness still"
        echo "  exited 0. A lost control must fail the gate."
      else
        echo "  ARM PASSED: killed -> not killed, harness rc=$harness_rc"
        ARMS_PASSED=$((ARMS_PASSED + 1))
      fi
      ;;
  esac
  echo
}

# --- ARM 1: M6's killer, selected at 7 nodes -------------------------------
arm "M6" "test_arm1_before_the_side_effect_the_call_fails" "tests/test_audit.py" \
  '        with pytest.raises(AuditWriteError):
            emit(event, AuditPhase.BEFORE_SIDE_EFFECT)' \
  '        try:
            emit(event, AuditPhase.BEFORE_SIDE_EFFECT)
        except AuditWriteError:
            pass'

# --- ARM 2: M8's killer, selected at 2 nodes - the narrowest row -----------
arm "M8" "test_arm2_on_a_read_it_logs_to_stderr_and_continues" "tests/test_audit.py" \
  '    assert warnings == [], "a read must not surface a warning to the caller"
    assert "audit write failed" in capsys.readouterr().err' \
  '    _ = (warnings, capsys.readouterr().err)'

# --- ARM 3: M14's killer, in the OTHER mutated file ------------------------
arm "M14" "test_a_container_under_an_unlisted_key_is_redacted_WHOLE" \
  "tests/test_redaction.py" \
  '    assert out == {"secretBlob": "[REDACTED:dict]"}
    leaked = _leaks(repr(out), "job-42", "a@b.invalid")
    assert not leaked, "a leaf escaped from inside an unlisted container"' \
  '    _ = (out, _leaks(repr(out), "job-42", "a@b.invalid"))'

echo "########## ARMS: $ARMS_PASSED/$ARMS_RUN passed"
# `fired`, not `killed`: this probe's tally is "how many arms fired", the same
# meaning check-row-floor-controls.sh and the other docs/reviews probes use.
# harness-result.sh refuses any other name.
harness_result_tally fired "$ARMS_PASSED" "$ARMS_RUN"
ROW_FLOOR=3
harness_result_ran "$ARMS_RUN" "$ROW_FLOOR"
if [ "$ARMS_RUN" -lt "$ROW_FLOOR" ]; then
  echo "FEWER ARMS THAN THE FLOOR ($ARMS_RUN/$ROW_FLOOR) - arms were lost."
  exit 1
fi
[ "$ARMS_PASSED" -eq "$ARMS_RUN" ] || exit 1
