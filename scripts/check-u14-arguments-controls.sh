#!/usr/bin/env bash
# U14 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the behaviour it claims to check is wrong.
#
# THE ROWS THAT MATTER MOST ARE M1-M4, THE ENUMERATION ROWS. U14's whole
# job is proving the inbound set is COMPLETE, and the mechanism it uses
# is two independent AST walks over `src/fast_mcp_jobvite/tools/`
# asserted EQUAL. A set-equality assertion is satisfied by
# `set() == set()`, so a broken walk that finds nothing agrees perfectly
# with a second broken walk that finds nothing - and reports a green on
# the unit whose entire subject is completeness. M1-M4 break the walks
# one at a time and require the suite to say so.
#
# `utils/constraints.py` and the two `tools/` modules are U14's own
# files; `tests/test_error_contract.py` is U2's and is MUTATED here,
# never edited, because M14 measures whether U14's re-assertion of U2's
# rule can actually fail.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an untracked file whatever
# it contains, which cost four amputation rows on another unit a "did not
# land" verdict when all four had landed.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and a mutation swapping one value can be the same size inside one
# second - the interpreter then reuses stale bytecode, the mutated code
# never runs, and the row reports a clean survivor that is an instrument
# fault rather than a finding.

set -uo pipefail

# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. Three names because the arms are three
# separate decisions, even where two of them share a value today.
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

CONSTRAINTS="src/fast_mcp_jobvite/utils/constraints.py"
JOBS="src/fast_mcp_jobvite/tools/jobs.py"
CANDIDATES="src/fast_mcp_jobvite/tools/candidates.py"
U2SUITE="tests/test_error_contract.py"
SUITE="tests/test_arguments_sweep.py"
OUT=/tmp/u14-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can only detect a failed
# `cp` - a CORRUPTED BACKUP passes it and hands every later row a mutated
# tree.
for f in "$CONSTRAINTS" "$JOBS" "$CANDIDATES" "$U2SUITE" "$SUITE"; do
  cp "$f" "$PRISTINE_DIR/$(echo "$f" | tr / _)" ||
    { echo "COULD NOT TAKE PRISTINE COPY of $f"; exit 3; }
done

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

# --------------------------------------------------------------------
# mutate <label> <file> <test-selector> <old> <new>
# --------------------------------------------------------------------
mutate() {
  local label="$1" file="$2" selector="$3" old="$4" new="$5"
  TOTAL=$((TOTAL + 1))

  echo "########## $label"
  echo "  target: $selector"

  # DOES THE SELECTOR STILL RESOLVE? pytest exits 4 when a selector
  # matches nothing and this harness treats any non-zero exit as a kill,
  # so a renamed test would report KILLED forever while running nothing.
  timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "$selector" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1
  local probe_rc=$?
  if [ "$probe_rc" -ne 0 ]; then
    if [ "$probe_rc" -eq 124 ]; then
      echo "  SELECTOR PROBE TIMED OUT after ${SELECTOR_TIMEOUT}s - collection NEVER FINISHED."
      echo "  Read this, not the lines below: a hang, not a rename."
    fi
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  This row has been reporting KILLED without running. Fix the harness."
    echo
    return
  fi

  local backup
  backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
  cp "$file" "$backup" || { echo "  COULD NOT BACK UP"; return; }

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

  timeout "$ROW_TIMEOUT" uv run --frozen pytest "$selector" -q -p no:cacheprovider >"$OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after ${ROW_TIMEOUT}s - this row NEVER FINISHED. Not a kill,"
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

# ====================================================================
# THE ENUMERATION. The set-equality assertion is the unit's subject and
# `set() == set()` is its failure mode.
# ====================================================================

# M1 - ROUTE A finds nothing. The `params` argument is renamed in the
# walk, so no tool function contributes a model. Route B still finds
# five, so the equality assertion has to notice the asymmetry.
mutate "M1  route A (tool functions) matches no argument" \
  "$SUITE" "$SUITE::test_the_two_enumerations_of_the_input_model_set_are_EQUAL" \
  '            if argument.arg == "params":' \
  '            if argument.arg == "parameters":'

# M2 - ROUTE B admits the OUTPUT models. `CreateCandidateResult` is
# excluded by its `output_schema=` use, and this deletes that exclusion.
# An output model swept as an input model would then be asserted to
# carry `SafeText` fields it has no reason to have.
mutate "M2  route B stops excluding the output models" \
  "$SUITE" "$SUITE::test_the_two_enumerations_of_the_input_model_set_are_EQUAL" \
  '        if node.name in outputs:
            continue' \
  '        if node.name in ():
            continue'

# M3 - THE CONTAINER SHRINKS TO ONE FILE. This is the two-lists defect
# reproduced exactly: a glob replaced by a name somebody typed. It must
# take the population assertion red, not the equality one - both walks
# agree perfectly about a container that is missing a module.
mutate "M3  the tool-module container becomes a hand-typed name" \
  "$SUITE" "$SUITE::test_the_enumeration_is_not_a_wrong_zero" \
  '    return sorted(p for p in TOOLS_DIR.glob("*.py") if p.name != "__init__.py")' \
  '    return [TOOLS_DIR / "jobs.py"]'

# M4 - THE PLANTED-MODULE CONTROL. Route B is made to key on a name
# suffix instead of on the `output_schema=` use - the disguised second
# hand-kept list. It admits `PlantedResult`, which is the whole thing
# the control exists to refuse.
mutate "M4  route B excludes output models by NAME, not by use" \
  "$SUITE" "$SUITE::test_the_enumeration_finds_a_model_planted_in_a_synthetic_module" \
  '        if node.name in outputs:
            continue
        found.add(node.name)' \
  '        if node.name.endswith("Resultx"):
            continue
        found.add(node.name)'

# ====================================================================
# §2.1's PER-MODEL OBLIGATIONS (DESIGN.md:152-154)
# ====================================================================

# M5 - `strict=True` is dropped from ONE of the five models. A sweep
# that asserted the property on a base class, or on a model somebody
# named, would not see this.
mutate "M5  one input model silently loses strict=True" \
  "$CANDIDATES" "$SUITE::test_every_input_model_forbids_extra_keys_and_is_strict" \
  '    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_id: Annotated[' \
  '    model_config = ConfigDict(extra="forbid")

    candidate_id: Annotated['

# M6 - `extra="forbid"` becomes `allow` on the write tool's model, which
# is the one that reaches a live person.
mutate "M6  the write model admits undeclared keys" \
  "$CANDIDATES" "$SUITE::test_every_input_model_forbids_extra_keys_and_is_strict" \
  '    model_config = ConfigDict(extra="forbid", strict=True)

    first_name: Annotated[' \
  '    model_config = ConfigDict(extra="allow", strict=True)

    first_name: Annotated['

# M7 - ONE model stops inheriting the shared limits. ADR-0012's "one
# copy, reused" fails silently for exactly one tool.
mutate "M7  one input model drops the shared structural limits" \
  "$JOBS" "$SUITE::test_every_input_model_carries_the_shared_structural_limits" \
  'class GetJobFeedInput(InboundModel):' \
  'class GetJobFeedInput(BaseModel):'

# M8 - a free-text field loses its ceiling and its character rule at
# once, by being declared a bare `str`. `max_length` on EVERY string is
# DESIGN.md:152-154, and this is the field that carries candidate PII.
mutate "M8  a PII free-text field becomes an unbounded bare str" \
  "$CANDIDATES" "$SUITE::test_every_string_field_carries_an_explicit_length_ceiling_and_a_pattern" \
  '    first_name: Annotated[
        SafeText,' \
  '    first_name: Annotated[
        str,'

# ====================================================================
# §8 #8 - THE CHARACTER RULE (DESIGN.md:1372-1375, B25)
# ====================================================================

# M9 - the C1 range is dropped. C0 and DEL still reject, so a rule
# written and tested only for NUL stays green. This is the narrower
# form of the mistake, and it is the one that survives review.
mutate "M9  the forbidden set loses its C1 range" \
  "$CONSTRAINTS" "$SUITE::test_case8_a_forbidden_character_in_ANY_string_field_FAILS_CLOSED" \
  '_CONTROL_CHARACTERS: Final = r"\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"' \
  '_CONTROL_CHARACTERS: Final = r"\x00-\x08\x0b\x0c\x0e-\x1f"'

# M10 - the bidi overrides are dropped from the COMPILED pattern. Every
# length and regex check still passes the payload, which is the whole
# reason DESIGN.md:172-179 names bidi beside the control characters.
#
# THE ANCHOR IS `_NO_FORBIDDEN`, NOT `_BIDI_OVERRIDES`, AND THAT IS
# DELIBERATE. `_BIDI_OVERRIDES` is a string of LITERAL, INVISIBLE bidi
# characters. An anchor carrying them is a shell string nobody can read,
# review or diff, and the first version of this row wrote them as `\u`
# escapes - which bash does not interpret, so the anchor matched ZERO
# times and the row reported "COULD NOT APPLY" instead of a verdict.
# `_NO_FORBIDDEN` is where the two classes are composed into the pattern
# the models actually use, it is plain ASCII, and dropping the bidi half
# there is the same defect at the point of use.
mutate "M10 the compiled pattern loses its bidi overrides" \
  "$CONSTRAINTS" "$SUITE::test_case8_a_forbidden_character_in_ANY_string_field_FAILS_CLOSED" \
  '_NO_FORBIDDEN = f"\\A[^{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]*\\z"' \
  '_NO_FORBIDDEN = f"\\A[^{_CONTROL_CHARACTERS}]*\\z"'

# ====================================================================
# §8 #9 - THE FOUR STRUCTURAL LIMITS. ONE ROW PER LIMIT, AND EACH ROW
# MOVES THE LIMIT RATHER THAN DELETING IT, SO THE ACCEPTING ARM IS
# WHAT CATCHES SOME OF THEM.
# ====================================================================

# M11 - depth 5 becomes depth 4. The REJECTING arm still passes: a
# six-level payload is refused either way. Only the accepting arm sees
# it, which is the entire argument for having one.
mutate "M11 the depth ceiling is one level too tight" \
  "$CONSTRAINTS" "$SUITE::test_case9_ACCEPT_a_payload_at_exactly_five_levels" \
  'MAX_NESTING_DEPTH: Final = 5' \
  'MAX_NESTING_DEPTH: Final = 4'

# M12 - the list ceiling is off by one in the permissive direction, so
# 1,001 items are admitted. The rejecting arm is what catches this one;
# M11 and M12 are the same defect in opposite directions and the pair
# is why both arms exist.
mutate "M12 the list ceiling admits one item too many" \
  "$CONSTRAINTS" "$SUITE::test_case9_reject_a_collection_past_one_thousand_items" \
  '        if len(payload) > MAX_LIST_ITEMS:' \
  '        if len(payload) > MAX_LIST_ITEMS + 1:'

# M13 - the dict-key ceiling is read off the wrong quantity: the number
# of DISTINCT VALUES rather than the number of keys. A 200-key object
# of repeated values passes.
mutate "M13 the key ceiling counts values, not keys" \
  "$CONSTRAINTS" "$SUITE::test_case9_reject_an_object_past_one_hundred_keys" \
  '        if len(payload) > MAX_DICT_KEYS:' \
  '        if len(set(map(repr, payload.values()))) > MAX_DICT_KEYS:'

# M14 - the size ceiling is measured in CHARACTERS rather than bytes,
# which is the mistake DESIGN.md:178 spends a paragraph on: a
# multi-byte payload is under the limit by one count and over it by the
# other, and 1 MiB is a byte quantity.
mutate "M14 the payload size is measured before encoding" \
  "$CONSTRAINTS" "$SUITE::test_case9_ACCEPT_a_payload_sitting_just_inside_one_mebibyte" \
  '    if len(encoded) > MAX_PAYLOAD_BYTES:' \
  '    if len(encoded) > MAX_PAYLOAD_BYTES - 64:'

# M15 - the walk checks depth AFTER descending rather than before, so
# the ceiling is effectively one level looser and a payload deep enough
# to exhaust the interpreter's own recursion is walked before it is
# refused.
mutate "M15 the depth check happens after the descent" \
  "$CONSTRAINTS" "$SUITE::test_case9_reject_nesting_past_five_levels" \
  '    if depth > MAX_NESTING_DEPTH:' \
  '    if depth > MAX_NESTING_DEPTH + 1:'

# M16 - `str` is admitted to the collection branch. A 1,001-character
# string is then refused as an oversized list, which is fail-closed for
# the wrong reason and refuses a perfectly ordinary argument. The
# ACCEPTING arm on a well-formed payload is what sees it.
mutate "M16 a string is counted as a collection of characters" \
  "$CONSTRAINTS" "$SUITE::test_case7_POSITIVE_CONTROL_a_well_formed_argument_passes" \
  '    if isinstance(payload, (list, tuple, set, frozenset)):' \
  '    if isinstance(payload, (list, tuple, set, frozenset, str)):'

# M17 - the limits are enforced but the payload is not returned, so
# every argument arrives as `None` and every tool breaks. A check that
# silently rewrites what it validates is the failure `SafeText`'s own
# comment refuses `strip_whitespace` to avoid.
mutate "M17 the before-validator drops the payload it checked" \
  "$CONSTRAINTS" "$SUITE::test_case7_POSITIVE_CONTROL_a_well_formed_argument_passes" \
  '        check_structural_limits(data)
        return data' \
  '        check_structural_limits(data)
        return {}'

# ====================================================================
# §8 #7 - FAIL-CLOSED, AND THE POSITIVE CONTROL THAT KEEPS IT HONEST
# ====================================================================

# M18 - the size check raises `TypeError` on an unserialisable value
# instead of measuring it. `TypeError` is not a `ValidationError`, so a
# fail-closed check becomes an unhandled crash on a payload a caller
# controls.
mutate "M18 the size check crashes on a value json cannot serialise" \
  "$CONSTRAINTS" "$SUITE::test_case9_the_size_check_survives_a_value_json_cannot_serialise" \
  '    encoded = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")' \
  '    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")'

# ====================================================================
# U2's NO-`success`-ENVELOPE RULE, RE-RUN WITH TEETH
# ====================================================================
#
# U2's own docstring says the assertion "is near-vacuous today ...
# `src/` holds four modules, so it passes over almost nothing". U14's
# re-assertion adds a claim about the SIZE of the corpus, and these two
# rows are what prove that claim is not itself decoration.

# M19 - the scanner is pointed at one module. It returns a clean empty
# list, which is exactly what a passing repository returns, and only the
# corpus-size assertion can tell the two apart.
mutate "M19 the corpus shrinks to a single module" \
  "$SUITE" "$SUITE::test_the_no_success_envelope_rule_now_runs_over_the_COMPLETED_corpus" \
  '        list(SRC.rglob("*.py")) + list((REPO_ROOT / "tests").rglob("*.py")),' \
  '        list(SRC.rglob("constraints.py")),'

# M20 - U2's SCANNER STOPS MATCHING ANYTHING. The rule reads as
# enforced, the sweep reports a clean corpus, and every envelope in the
# tree is admitted. U2's own positive control is what must go red.
#
# THE ANCHOR IS THE `if`, NOT THE REGEX, AND `check-harness-anchors.py`
# IS WHY. The first version anchored on the `ENVELOPE = re.compile(...)`
# line, which carries nested quotes and backslashes. Bash expanded it
# correctly and the row reported KILLED - but the STATIC anchor checker
# could not resolve it, reporting `0 hits`, so the row would have been
# invisible to the gate that exists to catch a harness whose anchors
# have drifted. **An anchor no checker can read is an anchor nobody is
# checking**, and the row was passing while that was true.
mutate "M20 U2's envelope scanner matches nothing at all" \
  "$U2SUITE" "$U2SUITE::test_the_envelope_scanner_finds_an_envelope_when_one_is_present" \
  '                if ENVELOPE.search(line):' \
  '                if None:'

# ====================================================================
# THE ROW FLOOR
# ====================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted reported fully green. Lowering this number is a visible
# diff that has to be defended.
ROW_FLOOR=20
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
