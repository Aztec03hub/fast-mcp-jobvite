#!/usr/bin/env bash
# THE rc=4 VERDICT TRAP that per-row selection opened in check-u3-audit-controls.sh.
#
# THE DEFECT, measured before it was fixed. When a mutation breaks the import of
# the module under test, pytest behaves differently depending on WHAT it was
# asked to run:
#
#   pytest tests/a.py tests/b.py tests/c.py      rc=2, "Interrupted: 1 error
#                                                during collection". The output
#                                                names NO test.
#   pytest tests/a.py::test_named_killer         rc=4, "ERROR: found no
#                                                collectors for .../a.py::test_named_killer"
#                                                - the output NAMES THE TEST,
#                                                because a node id contains it.
#
# The harness's verdict was `grep -q "$want"` over the whole log. On the bare
# form that never matched, so an import break fell to "red, but NOT at $want"
# and failed closed. On the SELECTING form it matches - pytest complaining that
# it could not collect the killer reads as the killer having failed - and the
# row would report `killed by $want` for a test that never ran.
#
# So the conversion to per-row selection is what made this reachable. That is
# the whole point of this probe: it is the control for a hazard the bare
# harness could not have.
#
# WHY THIS IS NOT AN ARM OF probe-252-selection-can-fail.sh. That probe runs the
# real harness end to end, and this hazard needs a mutation PRE-PLANTED in
# src/ - which the harness's own pre-flight guard refuses
# (`git status --porcelain -- "$AUDIT" "$REDACT"` -> exit 3). So the artifact
# under test here is the pair that actually decides the verdict: real pytest
# output from a real broken import, and the harness's real verdict regex, read
# out of the harness rather than retyped.
#
# `-e` deliberately omitted: this probe reads the exit code of a pytest run that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md.
set -uo pipefail

# shellcheck source=../../scripts/lib/harness-result.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)/lib/harness-result.sh"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 3
export PYTHONDONTWRITEBYTECODE=1

HARNESS=scripts/check-u3-audit-controls.sh
AUDIT="src/fast_mcp_jobvite/audit.py"
SUITE="tests/test_audit.py tests/test_redaction.py tests/test_logging_process.py"
WANT="test_arm3_the_warning_tells_the_caller_not_to_retry"
NODE="tests/test_audit.py::$WANT"
# Bounded, like every other pytest call in a tracked .sh here:
# check-pytest-bounded.sh caught both of the calls below unbounded on this
# probe's first run. A hung suite produces no result lines, so every
# assertion "did not survive" and the row reads as a pass.
PYTEST_TIMEOUT=300
ROWS=0
FIRED=0

for required in "$HARNESS" "$AUDIT" tests/test_audit.py; do
  [ -f "$required" ] || { echo "ABORT: $required not found from $REPO_ROOT"; exit 3; }
done
if [ -n "$(git status --porcelain -- "$AUDIT")" ]; then
  echo "ABORT: $AUDIT has uncommitted changes; this probe mutates and restores it."
  exit 3
fi

# THE VERDICT REGEX IS READ OUT OF THE HARNESS, NEVER RETYPED. A copy here would
# be free to agree with a harness that had drifted, which is the shape this
# repository keeps finding. If the line cannot be located the probe refuses.
# #289 changed the shape it reads: the verdict is no longer an ERE with the
# test name interpolated into it (a name like `test_x[1]` was a PATTERN there,
# not a literal), it is an awk program that takes the name through ENVIRON.
# So what is extracted here is the awk PROGRAM, and it is fed the name the
# same way the harness does - by an environment assignment, never by textual
# substitution, which is the substitution this change exists to remove.
VERDICT_AWK=$(sed -n "s/.*awk '\(.*\)' \"\$MUT_OUT\".*/\1/p" "$HARNESS" | head -1)
if [ -z "$VERDICT_AWK" ]; then
  echo "ABORT: could not read the verdict expression out of $HARNESS."
  echo "It is supposed to be an \"awk '...' \\\"\$MUT_OUT\\\"\" line. If the"
  echo "harness changed shape, this probe is measuring nothing and says so."
  exit 3
fi
echo "verdict expression read from $HARNESS: awk '$VERDICT_AWK'"
echo

restore() { git checkout -- "$AUDIT"; }
# PER-RUN, NEVER A FIXED NAME. Two worktrees on one machine run these probes
# concurrently, and a fixed path gives both the SAME INODE: independent `>`
# offsets leave a NUL hole, `grep` then reports "binary file matches" on
# STDERR and returns an EMPTY capture at exit 0, and a rival's `FAILED
# <nodeid>` lines are read as THIS run's verdict. Reproduced both ways in
# docs/reviews/probe-284-shared-path-collision.sh; #262 is where the class
# already produced a false kill. CI can never catch a regression here - the
# runner has no second worktree.
OUT="$(mktemp /tmp/probe-252-rc4-XXXXXX)"
CTL_OUT="$(mktemp /tmp/probe-252-fake-fail-XXXXXX)"
trap 'harness_result_emit; restore; rm -f "$OUT" "$CTL_OUT"' EXIT

row() {
  local label="$1" cond="$2"
  ROWS=$((ROWS + 1))
  if [ "$cond" = "pass" ]; then
    FIRED=$((FIRED + 1))
    echo "  ROW $ROWS PASSED: $label"
  else
    echo "  ROW $ROWS FAILED: $label"
  fi
}

echo "########## plant an import-breaking mutation in $AUDIT"
printf '\nthis_name_is_undefined_at_import_time\n' >>"$AUDIT"
if git diff --quiet -- "$AUDIT"; then
  echo "MUTATION DID NOT LAND despite a successful write"
  exit 3
fi

echo "########## A: the BARE form, which is what the harness ran before #252"
# shellcheck disable=SC2086
timeout "$PYTEST_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider -rf >"$OUT" 2>&1
a_rc=$?
a_want=$(grep -c "$WANT" "$OUT")
echo "  rc=$a_rc  occurrences of \$want in the log: $a_want"
row "the bare form gives rc=2, not 4" "$([ "$a_rc" -eq 2 ] && echo pass || echo fail)"
row "the bare form's log does NOT name \$want" "$([ "$a_want" -eq 0 ] && echo pass || echo fail)"

echo "########## B: the SELECTING form, which is what #252 made the harness run"
timeout "$PYTEST_TIMEOUT" uv run --frozen pytest "$NODE" -q -p no:cacheprovider -rf >"$OUT" 2>&1
b_rc=$?
b_want=$(grep -c "$WANT" "$OUT")
echo "  rc=$b_rc  occurrences of \$want in the log: $b_want"
grep -E "^ERROR" "$OUT" | sed 's/^/      /' | head -2
row "the selecting form gives rc=4" "$([ "$b_rc" -eq 4 ] && echo pass || echo fail)"
row "THE TRAP: its log DOES name \$want" "$([ "$b_want" -gt 0 ] && echo pass || echo fail)"

echo "########## C: the OLD verdict would have lied; the NEW one does not"
# OLD: `grep -q "$want"` over the whole log - the exact expression #252 shipped.
if grep -q "$WANT" "$OUT"; then old="killed"; else old="not-killed"; fi
if w="$WANT" awk "$VERDICT_AWK" "$OUT"; then new="killed"; else new="not-killed"; fi
echo "  OLD rule (bare name anywhere): $old"
echo "  NEW rule (anchored to a result line): $new"
row "the OLD rule reports a kill here, which is the defect" \
  "$([ "$old" = "killed" ] && echo pass || echo fail)"
row "the NEW rule does NOT report a kill here" \
  "$([ "$new" = "not-killed" ] && echo pass || echo fail)"

restore
if ! git diff --quiet -- "$AUDIT"; then echo "RESTORE FAILED"; exit 3; fi

echo "########## D: the NEW rule is not merely strict - a REAL kill still reads as one"
# Positive control. Without this, a regex matching NOTHING would pass row 6 -
# "not-killed" is the answer a broken regex gives to every question.
cat >"$CTL_OUT" <<EOF
=========================== short test summary info ============================
FAILED tests/test_audit.py::$WANT - AssertionError: assert 0 == 1
EOF
if w="$WANT" awk "$VERDICT_AWK" "$CTL_OUT"; then ctl="killed"; else ctl="not-killed"; fi
echo "  NEW rule against a real '^FAILED <nodeid> - ...' line: $ctl"
row "the NEW rule still reports a kill on a genuine FAILED line" \
  "$([ "$ctl" = "killed" ] && echo pass || echo fail)"

echo
echo "########## ROWS: $FIRED/$ROWS passed"
harness_result_tally fired "$FIRED" "$ROWS"
ROW_FLOOR=7
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "FEWER ROWS THAN THE FLOOR ($ROWS/$ROW_FLOOR) - rows were lost."
  exit 1
fi
[ "$FIRED" -eq "$ROWS" ] || exit 1
