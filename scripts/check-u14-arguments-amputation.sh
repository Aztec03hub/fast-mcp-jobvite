#!/usr/bin/env bash
# U14 AMPUTATION harness. A DIFFERENT question from the mutation one.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything
#                    still report success?
#
# SURVIVORS ARE THE OUTPUT, not the failure. Each row prints the counts
# and NAMES every test that still passed, so the report can say which
# assertions survived and why.
#
# It exits non-zero only if it could not run, if the intact baseline is
# red, or if an amputation left the tree dirty. THE CI STEP GATES ON
# EVERY ROW HAVING APPLIED ITS ANCHOR and on the vacuous-row count, not
# on this exit code.
#
# A VACUOUS ROW - a behaviour deleted with NOTHING going red - is the
# defect this harness exists to find, one layer up from the suite.
#
# WHAT THIS HARNESS IS FOR, ON THIS UNIT SPECIFICALLY. U14's subject is
# an ENUMERATION, and an enumeration's characteristic failure is not a
# wrong value - it is finding nothing and agreeing with itself. Rows A1
# to A4 delete the enumeration, the container, the population guard and
# the parametrised sweeps outright and require something to go red.
#
# `tests/test_error_contract.py` is U2's file and `tests/test_constraints
# .py` is U5's. Both are amputated here, never edited, and restored with
# `cp` verified by `cmp` against a pristine copy taken before row 1;
# never `git checkout`, never `git stash`.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation replacing a body with a shorter one can be the same
# size inside one second, in which case stale bytecode runs and the row
# fakes a clean result.

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

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CONSTRAINTS="src/fast_mcp_jobvite/utils/constraints.py"
JOBS="src/fast_mcp_jobvite/tools/jobs.py"
CANDIDATES="src/fast_mcp_jobvite/tools/candidates.py"
APPROVAL="src/fast_mcp_jobvite/approval.py"
SUITE="tests/test_arguments_sweep.py"
OUT=/tmp/u14-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

for f in "$CONSTRAINTS" "$JOBS" "$CANDIDATES" "$APPROVAL" "$SUITE"; do
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

  timeout "$ROW_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
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

  tail -1 "$OUT" | sed 's/^/  /'

  # The verdict is the RUN'S EXIT CODE, never `grep -c "^FAILED"`: that
  # grep misses ERROR entirely, and a collection error is a row going
  # red for a real reason.
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
# A1 - THE ENUMERATION DOES NOT EXIST. Route A returns nothing at all,
# so `INPUT_MODELS` is empty, every parametrised sweep below it
# parametrises over ZERO cases, and pytest passes each of them without
# a word. This is the exact failure the unit exists to prevent, and if
# it is vacuous then U14 is decoration.
# ---------------------------------------------------------------------------
amputate "A1 route A finds no input model at all" "$SUITE" \
  '        for argument in node.args.args:
            if argument.arg == "params":
                name = _annotation_name(argument.annotation)
                if name is not None:
                    found.add(name)
    return found' \
  '        for argument in node.args.args:
            if argument.arg == "params":
                pass
    return found'

# ---------------------------------------------------------------------------
# A2 - THE CONTAINER DOES NOT EXIST. The directory walk is replaced by
# an empty list, which is what a glob at a path that does not exist
# returns: a clean, self-explaining empty, identical to a real absence.
# ---------------------------------------------------------------------------
amputate "A2 the tool-module container returns nothing" "$SUITE" \
  '    return sorted(p for p in TOOLS_DIR.glob("*.py") if p.name != "__init__.py")' \
  '    return []'

# ---------------------------------------------------------------------------
# A3 - THE STRING-FIELD SWEEP FINDS NO FIELD. Both `case8` sweeps and
# the length/pattern sweep parametrise over an empty list. Without the
# population assertion, all three go green having asserted nothing.
# ---------------------------------------------------------------------------
amputate "A3 the string-field discovery returns nothing" "$SUITE" \
  '    return [
        name
        for name, field in model.model_fields.items()
        if str in _flatten(field.annotation)
    ]' \
  '    return []'

# ---------------------------------------------------------------------------
# A4 - THE TWO ROUTES BECOME ONE. Route B simply calls route A, so the
# equality assertion compares a set with itself and is true by
# construction. It is the two-instruments-agreeing failure: a check
# that cannot disagree is not a check.
# ---------------------------------------------------------------------------
amputate "A4 the second enumeration route becomes the first" "$SUITE" \
  'def models_defined_as_classes(tree: ast.Module) -> set[str]:' \
  'def models_defined_as_classes(tree: ast.Module) -> set[str]:
    return models_named_by_tool_functions(tree)


def _unreachable_models_defined_as_classes(tree: ast.Module) -> set[str]:'

# ---------------------------------------------------------------------------
# A5 - THE CHARACTER RULE DOES NOT EXIST. The compiled pattern admits
# everything. `max_length` still bounds the field, so a NUL or a bidi
# override in a candidate name is a well-formed short string that every
# remaining check passes - which is DESIGN.md:175-179's whole argument
# for having the rule at all.
# ---------------------------------------------------------------------------
amputate "A5 the forbidden-character pattern admits everything" "$CONSTRAINTS" \
  '_NO_FORBIDDEN = f"\\A[^{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]*\\z"' \
  '_NO_FORBIDDEN = r"\\A[\\s\\S]*\\z"'

# ---------------------------------------------------------------------------
# A6 - THE STRUCTURAL LIMITS DO NOT EXIST. `check_structural_limits`
# returns without measuring anything. This is the tree as it stood
# BEFORE U14, and the row is the measurement of what U14 added: the
# survivors here are every assertion that was green while three of the
# four limits of DESIGN.md:162-164 were absent by a recorded decision.
# ---------------------------------------------------------------------------
amputate "A6 the structural limits measure nothing" "$CONSTRAINTS" \
  '    encoded = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")' \
  '    return
    encoded = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")'

# ---------------------------------------------------------------------------
# A7 - THE LIMITS EXIST AND HAVE NO CALLER. The before-validator is
# gone, so `check_structural_limits` is correct, tested, and reachable
# by nothing a caller can send. **This is the shape the pre-U14
# `constraints.py` comment said it was avoiding** - "an unreachable
# limit is worse than absent: it reads as discharged" - so the row that
# proves the suite can tell "implemented" from "wired" is the one that
# retires that argument.
# ---------------------------------------------------------------------------
amputate "A7 the structural limits have no caller" "$CONSTRAINTS" \
  '        check_structural_limits(data)
        return data' \
  '        return data'

# ---------------------------------------------------------------------------
# A8 - `extra="forbid"` DOES NOT EXIST ON THE WRITE MODEL. §8 #7's
# fail-closed case on the one tool that reaches a live person.
# ---------------------------------------------------------------------------
amputate "A8 the write model's extra-key refusal is gone" "$CANDIDATES" \
  '    model_config = ConfigDict(extra="forbid", strict=True)

    first_name: Annotated[' \
  '    model_config = ConfigDict(strict=True)

    first_name: Annotated['

# ---------------------------------------------------------------------------
# A9 - `strict=True` DOES NOT EXIST ON A READ MODEL. Lax mode coerces,
# so a wrongly typed argument is silently converted rather than refused.
# ---------------------------------------------------------------------------
amputate "A9 a read model stops being strict" "$JOBS" \
  '    model_config = ConfigDict(extra="forbid", strict=True)

    ids: Annotated[' \
  '    model_config = ConfigDict(extra="forbid")

    ids: Annotated['

# ---------------------------------------------------------------------------
# A10 - THE STRUCTURAL WALK NEVER DESCENDS. The top level is measured
# and nothing below it is, so every limit holds for a flat payload and
# none holds one level down - which is the only place they matter.
#
# **THIS ROW REPLACED ONE THAT AMPUTATED AN ASSERTION RATHER THAN A
# BEHAVIOUR.** The first A10 rewrote `assert issubclass(model,
# InboundModel)` to `assert issubclass(model, BaseModel)` IN THE SUITE,
# which is trivially true, so it went vacuous - correctly, because it
# deleted nothing. An amputation whose subject is the test measures the
# harness, and the vacuous-row gate is what said so.
# ---------------------------------------------------------------------------
amputate "A10 the structural walk never descends" "$CONSTRAINTS" \
  '        for value in payload.values():
            _measure(value, depth + 1)
        return' \
  '        return'

# ---------------------------------------------------------------------------
# ROWS A11 TO A16 ARE R8-H1's, AND THEY EXIST BECAUSE ROWS A1 TO A10
# COULD ALL PASS WHILE AN INBOUND MODEL SAT OUTSIDE EVERY ONE OF THEM.
# R8 set `ApprovalAnswer`'s `extra="forbid"` to `extra="allow"` and all
# 768 tests stayed green: the sweep asserted a property about the
# INBOUND SURFACE while enumerating ONE DIRECTORY. Route C widened the
# container to the package; these rows are what say so out loud.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A11 - ROUTE C FINDS NOTHING. The third route returns an empty set, so
# the swept set silently reverts to route A's - which is precisely the
# tree R8 mutated, and it went green. A route whose absence costs
# nothing is not a route.
# ---------------------------------------------------------------------------
amputate "A11 route C finds no outside-response model" "$SUITE" \
  '    aliases = _schema_aliases(tree)' \
  '    return set()
    aliases = _schema_aliases(tree)'

# ---------------------------------------------------------------------------
# A12 - ROUTE C'S CONTAINER NARROWS BACK TO `tools/`. This is R8-H1
# ITSELF, reproduced as a row: the route is intact, the selector is
# intact, and only the container is wrong. It is the shape that is worth
# catching, because a narrowed container looks exactly like a working
# enumeration from every angle except the one model it cannot see.
# ---------------------------------------------------------------------------
amputate "A12 route C's container narrows to the tools directory" "$SUITE" \
  '    return sorted(SRC_PACKAGE_DIR.rglob("*.py"))' \
  '    return _tool_module_paths()'

# ---------------------------------------------------------------------------
# A13 - THE ELICITED MODEL STOPS FORBIDDING EXTRA KEYS. **This is R8's
# surviving mutation, byte for byte.** If this row is vacuous, nothing
# in this unit has changed since R8 measured it.
# ---------------------------------------------------------------------------
amputate "A13 the elicited model's extra-key refusal is gone" "$APPROVAL" \
  '    model_config = ConfigDict(extra="forbid", strict=True)' \
  '    model_config = ConfigDict(strict=True)'

# ---------------------------------------------------------------------------
# A14 - THE ELICITED MODEL STOPS BEING STRICT. R8-H2's fix (`fd1057a`)
# has its own test file; this row asks the different question of whether
# the SWEEP would have caught it, so that the next model to arrive
# outside `tools/` does not need a reviewer to notice it by hand.
# ---------------------------------------------------------------------------
amputate "A14 the elicited model stops being strict" "$APPROVAL" \
  '    model_config = ConfigDict(extra="forbid", strict=True)' \
  '    model_config = ConfigDict(extra="forbid")'

# ---------------------------------------------------------------------------
# A15 - THE ELICITED MODEL LOSES THE SHARED STRUCTURAL LIMITS. The
# third of §2.1's three properties, on the model that declared the other
# two and not this one for four months because no sweep reached it.
# ---------------------------------------------------------------------------
#
# It is amputated at the IMPORT rather than at the class statement,
# because `approval.py` no longer imports `BaseModel` for anything else -
# a row rewriting the base to a name the module does not bind goes red on
# a `NameError`, which measures the harness rather than the property.
amputate "A15 the elicited model loses the structural limits" "$APPROVAL" \
  'from fast_mcp_jobvite.utils.constraints import InboundModel' \
  'from pydantic import BaseModel as InboundModel'

# ---------------------------------------------------------------------------
# A16 - THE MODELLESS-PATH CENSUS FINDS NOTHING. The MRTR leg reads
# `ctx.input_responses` and takes a key off a raw dict, so no route over
# MODELS can see it and the census is the only thing that does. Deleted,
# its equality assertion compares `[]` with a one-element list and goes
# red; if it did not, the census would be decoration and a second
# modelless inbound path could arrive unremarked.
# ---------------------------------------------------------------------------
amputate "A16 the modelless-inbound census finds nothing" "$SUITE" \
  '                found.add(f"{module_path}:{node.name}")' \
  '                pass'

# ---------------------------------------------------------------------------
# THE GATE. `ROWS == APPLIED` says every row measured something; VACUOUS
# says whether any row measured NOTHING. Reporting survivors without
# gating on the vacuous count is how a row that deletes a behaviour and
# kills nothing passes CI.
# ---------------------------------------------------------------------------
# The canonical result line's row count, from the harness's own
# counter. This harness declares no ROW_FLOOR, so the floor is 0:
# 0 is not a floor anything can breach, and it reads as absent.
harness_result_ran "$ROWS" 0
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
if [ "$ROWS" -ne "$APPLIED" ]; then
  echo "A ROW DID NOT APPLY ITS ANCHOR. It measured nothing and said so."
  exit 1
fi
if [ "$VACUOUS" -ne 0 ]; then
  echo "A VACUOUS ROW IS A FINDING: a deleted behaviour that nothing noticed."
  exit 1
fi
