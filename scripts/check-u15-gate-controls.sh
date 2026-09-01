#!/usr/bin/env bash
# U15 mutation harness. Proves tests/test_file_type_gate.py can FAIL.
#
# WHY THIS EXISTS: every assertion in that suite is a claim about a gate whose
# whole job is to refuse things. A suite of refusal assertions is green against
# a gate that refuses everything, and a suite of permission assertions is green
# against a gate that permits everything. Neither is worth anything until a
# harness has broken the gate one rule at a time and watched the NAMED test go
# red.
#
# It is deliberately the mirror of scripts/check-u0-test-controls.sh.
#
# Each control: break exactly one thing in a COPY of the tree, run the suite,
# and require the specific named test to fail. A mutation that does not change
# the file is rejected (a no-op control is a green that measured nothing), and
# the run aborts if the unmutated copy is not already green.
#
# Exit 0 only if every control fired. Prints "N/M controls fired." for CI to
# parse on the property N == M and M > 0, never on a literal count.

set -uo pipefail

# THE ONE CANONICAL RESULT LINE (task #107). This arms an EXIT trap that prints
# `HARNESS-RESULT name=... rows=... floor=... status=refused` on ANY exit, so an
# abort cannot render identically to a pass. `harness_result_ran` below upgrades
# it to ok/breach from the real exit code. The format lives in the sourced file
# and nowhere else - the shape lists it replaces are why.
# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE_REL="scripts/check-committed-file-types.py"
SUITE_REL="tests/test_file_type_gate.py"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

TREE="$WORK/tree"
mkdir -p "$TREE"
# Copy only what the suite needs. `git ls-files` would miss the gate while it is
# still untracked, so copy the paths explicitly.
mkdir -p "$TREE/scripts" "$TREE/tests"
cp "$REPO_ROOT/$GATE_REL" "$TREE/$GATE_REL"
cp "$REPO_ROOT/$SUITE_REL" "$TREE/$SUITE_REL"
cp "$REPO_ROOT/tests/__init__.py" "$TREE/tests/" 2>/dev/null || true
cp "$REPO_ROOT/pyproject.toml" "$TREE/"

# THE INTERPRETER IS CHOSEN, NOT INHERITED. This harness runs pytest inside a
# COPIED tree, so `uv run` cannot be used there - it would try to resolve the
# copy as its own project. The obvious `python3 -m pytest` is what was here,
# and it is what turned CI red for eleven consecutive runs: on the runner,
# `python3` is the hosted-toolchain interpreter with no pytest, so the baseline
# was red and the harness aborted with 3 - correctly, since a control measured
# against a red baseline proves nothing. It passed locally the whole time
# because a developer machine's `python3` happens to have pytest.
#
# Same selection as scripts/check-u0-test-controls.sh, which had already solved
# this. Prefer the project venv, fall back to `uv run` where there is none.
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY=("$REPO_ROOT/.venv/bin/python")
else
  PY=(uv run --frozen --project "$REPO_ROOT" python)
fi

PRISTINE="$WORK/pristine.py"
cp "$REPO_ROOT/$GATE_REL" "$PRISTINE"

# BOUNDED HERE, NOT AT THE CALL SITES. All three callers route through this
# one function, so the bound and the hang report live in one place instead of
# being retyped. This matters most at the control call site, which does not
# capture the exit code at all - it greps the report. A hung run writes no
# FAILED line, so it reads as "DID NOT FIRE" and is counted as HELD unless it
# announces itself. `TIMED OUT` is the phrase ci-harness-gate.sh greps for.
run_suite() {  # -> writes report to $WORK/out.txt, returns pytest's exit code
  local rc
  ( cd "$TREE" && timeout -k 30 900 "${PY[@]}" -m pytest "$SUITE_REL" \
      -p no:cacheprovider -q -o addopts="" >"$WORK/out.txt" 2>&1 )
  rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - the suite NEVER FINISHED, so this run"
    echo "  measured nothing. Not a fire and not a hold."
  fi
  return "$rc"
}

echo "BASELINE: the unmutated copy must be green before anything is measured"
run_suite
BASE_RC=$?
tail -1 "$WORK/out.txt"
if [ "$BASE_RC" -ne 0 ]; then
  echo "ABORT: the unmutated copy is already red. Every control below would be"
  echo "a false positive - a test that was failing anyway proves nothing."
  cat "$WORK/out.txt"
  exit 3
fi
echo

FIRED=0
HELD=0

# Controls are declared as a here-document: four fields per line separated by
# '@@' - label, OLD, NEW, and the test that MUST go red. OLD and NEW are Python
# string literals evaluated by the mutator, so \n and quotes survive intact.
read -r -d '' CONTROL_SPEC <<'SPEC'
drop .pdf from the extension denylist@@'    ".pdf": "vendor document - THIS IS THE CLASS THAT LEAKED",\n'@@''@@test_a_pdf_by_extension_is_refused_BY_THE_DENYLIST
drop .raml from the extension denylist@@'    ".raml": "vendor API description - THIS IS THE CLASS THAT LEAKED",\n'@@''@@test_the_raml_that_leaked_is_refused_BY_THE_DENYLIST
allowlist-first inverted: unknown becomes PERMITTED@@'    if lowered not in ALLOWED_EXTENSIONS and name not in ALLOWED_BASENAMES:  # rule 2'@@'    if False:  # rule 2 disabled by the mutation harness'@@test_an_unknown_extension_is_refused_not_permitted
delete the magic-number rule entirely@@'    for signature, label in MAGIC:  # rule 3'@@'    for signature, label in ():  # rule 3 disabled'@@test_a_real_pdf_renamed_markdown_is_refused_by_its_bytes
remove only the %PDF- signature@@'    (b"%PDF-", "PDF"),\n'@@''@@test_a_real_pdf_renamed_markdown_is_refused_by_its_bytes
delete the NUL backstop@@'    nul = data.find(b"\\x00")  # rule 4'@@'    nul = -1  # rule 4 disabled'@@test_a_nul_byte_is_refused_even_with_an_allowed_extension
fail OPEN on a gate error instead of closed@@'        sys.exit(2)\n    except Exception as exc:'@@'        sys.exit(0)\n    except Exception as exc:'@@test_e2e_the_gate_fails_closed_when_it_cannot_run
accept unknown argv instead of refusing@@'        return 2\n\n    reader'@@'        return 0\n\n    reader'@@test_e2e_an_unknown_argument_fails_closed
read the allowlist from the WORKTREE so an unstaged exception applies@@'    allowed_paths = load_allowlist(reader)'@@'    allowed_paths = load_allowlist(worktree_blob)'@@test_e2e_an_override_needs_its_allowlist_entry_staged
read the WORKTREE instead of the index@@'    reader = worktree_blob if check_all else staged_blob'@@'    reader = worktree_blob'@@test_e2e_the_gate_reads_the_index_not_the_worktree
report success even when files were refused@@'    if refusals:\n        print("")'@@'    if False:\n        print("")'@@test_e2e_a_real_pdf_staged_as_markdown_is_refused
classify permits EVERYTHING@@'    name = Path(path).name'@@'    return None\n    name = Path(path).name'@@test_a_real_pdf_renamed_markdown_is_refused_by_its_bytes
classify refuses EVERYTHING@@'    name = Path(path).name'@@'    return "refused"\n    name = Path(path).name'@@test_an_ordinary_repository_file_is_permitted
drop .secrets.baseline, so the two shipped gates refuse each other again@@'        ".secrets.baseline",\n'@@''@@test_an_ordinary_repository_file_is_permitted
empty the rule tables@@'ALLOWED_EXTENSIONS = frozenset('@@'ALLOWED_EXTENSIONS = frozenset()\n_UNUSED = frozenset('@@test_the_rule_tables_are_populated
SPEC

while IFS= read -r line; do
  [ -z "$line" ] && continue
  LABEL="${line%%@@*}"; rest="${line#*@@}"
  OLD="${rest%%@@*}";   rest="${rest#*@@}"
  NEW="${rest%%@@*}"
  TEST="${rest#*@@}"

  cp "$PRISTINE" "$TREE/$GATE_REL"
  if ! python3 - "$TREE/$GATE_REL" "$OLD" "$NEW" <<'PY'
import sys, ast, pathlib
path, old_lit, new_lit = sys.argv[1], sys.argv[2], sys.argv[3]
old = ast.literal_eval(old_lit)
new = ast.literal_eval(new_lit)
p = pathlib.Path(path)
src = p.read_text()
if old not in src:
    sys.stderr.write(f"MUTATION TARGET NOT FOUND: {old!r}\n")
    sys.exit(1)
out = src.replace(old, new, 1)
if out == src:
    sys.stderr.write("MUTATION WAS A NO-OP\n")
    sys.exit(1)
p.write_text(out)
PY
  then
    printf -- '--- %-62s -> BROKEN CONTROL (mutation did not apply)\n' "$LABEL"
    HELD=$((HELD + 1)); continue
  fi

  run_suite
  if grep -qE "(FAILED|ERROR) .*::${TEST}\b" "$WORK/out.txt" \
     || grep -qE "^(FAILED|ERROR) .*${TEST}" "$WORK/out.txt"; then
    printf -- '--- %-62s -> CONTROL FIRED\n' "$LABEL"
    FIRED=$((FIRED + 1))
  else
    printf -- '--- %-62s -> DID NOT FIRE (%s stayed green)\n' "$LABEL" "$TEST"
    tail -3 "$WORK/out.txt" | sed 's/^/        /'
    HELD=$((HELD + 1))
  fi
done <<< "$CONTROL_SPEC"

cp "$PRISTINE" "$TREE/$GATE_REL"
run_suite
POST_RC=$?
TOTAL=$((FIRED + HELD))
echo
echo "${FIRED}/${TOTAL} controls fired."
echo "post-run re-check of the real gate: exit=${POST_RC} (must be 0)"

# THE ROW FLOOR. `TOTAL -gt 0` catches only TOTAL deletion, and here TOTAL
# is DERIVED from the rows that ran (FIRED + HELD) rather than declared -
# so a row that stops being parsed out of CONTROL_SPEC lowers TOTAL and
# takes the pass condition down with it, silently. DERIVED: this harness
# printed "15/15 controls fired." at b9a6b1d. Lowering this number is a
# visible diff that has to be defended.
ROW_FLOOR=15
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "${TOTAL}/${ROW_FLOOR} ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

[ "$FIRED" -eq "$TOTAL" ] && [ "$POST_RC" -eq 0 ] || exit 1
