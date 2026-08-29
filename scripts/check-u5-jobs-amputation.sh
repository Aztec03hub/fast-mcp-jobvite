#!/usr/bin/env bash
# U5 AMPUTATION harness. A DIFFERENT question from the mutation one.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything
#                    still report success?
#
# Amputation has exposed a vacuous assertion in every unit built on this
# project so far. U3's found a test that passed with the behaviour
# deleted because it searched the module's file text for a string the
# module's own docstring quoted - it was asserting that the
# DOCUMENTATION existed. That is why this unit's one structural check
# (the module-scope credential rule) walks the AST instead of grepping.
#
# SURVIVORS ARE THE OUTPUT, not the failure. For each amputation this
# prints the counts and NAMES every test that still passed, so the
# report can say which assertions survived and why, rather than
# asserting that none did.
#
# It exits non-zero only if it could not run, if the intact baseline is
# red, or if an amputation left the tree dirty. THE CI STEP GATES ON
# EVERY ROW HAVING APPLIED ITS ANCHOR, not on this exit code.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp` AGAINST A PRISTINE BACKUP,
# never with `git diff`. `git diff --quiet` reports NO DIFFERENCE for an
# UNTRACKED file whatever it contains, and this harness was untracked
# until it was committed - four amputation rows on another unit reported
# "did not land" that way while all four had landed, contradicting the
# anchor-uniqueness check printed two lines above them.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation that replaces a body with `pass` can be the same
# size inside one second, in which case the interpreter reuses stale
# bytecode and the amputated code never runs. That failure is silent and
# it fakes a clean result.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

TOOLS="src/fast_mcp_jobvite/tools/jobs.py"
MODELS="src/fast_mcp_jobvite/models/jobs.py"
FENCING="src/fast_mcp_jobvite/models/fencing.py"
CONSTRAINTS="src/fast_mcp_jobvite/utils/constraints.py"
SUITE="tests/test_tools_jobs.py"
OUT=/tmp/u5-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1 (R4-N1). The restore check
# below used to be `cp backup file; cmp file backup`, which compares equal
# BY CONSTRUCTION after the copy: it could detect only a failed `cp`, never
# the thing its message claims - "the tree still carries this row's
# amputation". A CORRUPTED BACKUP passes that check and hands every later
# row an amputated tree. The LANDING check above it was always real; this
# one was not, and the two read identically in the log.
for f in "$TOOLS" "$MODELS" "$FENCING" "$CONSTRAINTS"; do
  cp "$f" "$PRISTINE_DIR/$(echo "$f" | tr / _)" ||
    { echo "COULD NOT TAKE PRISTINE COPY of $f"; exit 3; }
done

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

  # SC2155: declared and assigned separately, so a failing `echo`/`tr`
  # cannot be masked by `local`'s own exit status (task #38).
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

  uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  local pristine
  pristine="$PRISTINE_DIR/$(echo "$file" | tr / _)"
  if ! cmp -s "$file" "$pristine"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  tail -1 "$OUT" | sed 's/^/  /'

  # THE VACUOUS-ROW GATE (R4-M5). This harness reported the vacuous shape
  # in its header - "no row survived N/N, which is the vacuous shape" -
  # and gated on something else entirely: APPLIED == ROWS. A row that
  # deleted a behaviour and killed NOTHING printed its survivors and
  # passed CI, which is the exact defect the whole harness exists to find,
  # one layer up.
  #
  # The verdict is the RUN'S EXIT CODE, not `grep -c "^FAILED"`: that
  # grep misses ERROR entirely, and a collection error is a row going red
  # for a real reason.
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
# A1 - THE RESULT CAP IS GONE ENTIRELY. Every item Jobvite returned is
# forwarded and `total` is recomputed to agree, so `showing N of N` is
# true on every call and the cap reports nothing because there is
# nothing to report. This is DESIGN.md:469-477 deleted outright.
# ---------------------------------------------------------------------------
amputate "A1  the result cap does not exist; total is recomputed to agree" \
  "$TOOLS" \
  '    items = payload.get(JOBS_ENVELOPE_KEY) or []
    jobs = [_to_job(item) for item in items[:max_results] if isinstance(item, dict)]
    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return JobSearchResult(jobs=jobs, total=total)' \
  '    items = payload.get(JOBS_ENVELOPE_KEY) or []
    jobs = [_to_job(item) for item in items if isinstance(item, dict)]
    return JobSearchResult(jobs=jobs, total=len(jobs))'

# ---------------------------------------------------------------------------
# A2 - `_meta` IS NEVER SET ON THE SUCCESS RESULT. SS8 #16's read arm
# has nothing to read. Every case that claims to assert `request_id`
# reaches the caller must die here; anything that survives was asserting
# something else.
# ---------------------------------------------------------------------------
amputate "A2  the success result carries no _meta at all" "$TOOLS" \
  '            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )' \
  '            return ToolResult(
                structured_content=result.model_dump(mode="json"),
            )'

# ---------------------------------------------------------------------------
# A3 - THE ERROR PATH RAISES INSTEAD OF RETURNING. This deletes
# DESIGN.md:536-540's central property: problem objects are the one
# error shape no configuration can distort BECAUSE they are returned.
# Raised, it goes through `mask_error_details` and the caller gets a
# masked string with no `request_id`, no `status` and no `type`.
# ---------------------------------------------------------------------------
amputate "A3  the error path raises rather than returning a problem" "$TOOLS" \
  '                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )' \
  '                raise'

# ---------------------------------------------------------------------------
# A4 - THE AUDIT EVENT IS NEVER EMITTED. Both id cases match the wire
# against "the audit event"; with no event there is nothing to match.
# This is the row that proves those two are not asserting against
# silence - the same construction DESIGN.md:1280-1282 uses to pair its
# own #4 and #5.
# ---------------------------------------------------------------------------
amputate "A4  no audit event is ever emitted (the id pairings go vacuous)" \
  "$TOOLS" \
  '            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),' \
  '            return ToolResult(
                structured_content=result.model_dump(mode="json"),'

# ---------------------------------------------------------------------------
# A5 - THE FENCING REGISTRY GENERATES NOTHING. `fencing_paths` returns
# an empty mapping for every model. DESIGN.md:202-205's whole mechanism
# is gone, and a test that iterates the generated paths asserting a
# property of each one passes VACUOUSLY over an empty mapping - which is
# why the registry case asserts the mapping is non-empty first.
# ---------------------------------------------------------------------------
amputate "A5  fencing_paths returns nothing for every model" "$FENCING" \
  '    paths: dict[str, Fenced] = {}
    for name in model.model_fields:' \
  '    paths: dict[str, Fenced] = {}
    return paths
    for name in model.model_fields:'

# ---------------------------------------------------------------------------
# A6 - A MISSING DECISION IS NEVER DETECTED. The refusal is deleted, so
# a field with no `Fenced` annotation is silently skipped rather than
# raising. The registry still generates paths for the decided fields, so
# every "the paths are correct" assertion still passes - only the case
# that exists to catch an UNDECIDED field can die here.
# ---------------------------------------------------------------------------
amputate "A6  a field with no fencing decision is silently skipped" "$FENCING" \
  '    found = [item for item in metadata if isinstance(item, Fenced)]
    if len(found) != 1:' \
  '    found = [item for item in metadata if isinstance(item, Fenced)]
    if not found:
        return Fenced(FencingDecision.NOT_FREE_TEXT, name, "skipped")
    if len(found) != 1:'

# ---------------------------------------------------------------------------
# A7 - THE ENABLE GATE IS GONE. `register` always registers, whatever
# `JOBVITE_TOOLS` says. DESIGN.md:227-229 calls this the only
# unconditionally enforceable control the design has, so its deletion
# must be visible.
# ---------------------------------------------------------------------------
amputate "A7  registration ignores the enable gate entirely" "$TOOLS" \
  '    if SEARCH_JOBS not in settings.enabled_tools:
        return' \
  '    pass'

# ---------------------------------------------------------------------------
# A8 - THE OUTPUT ALLOW-LIST IS GONE in the direction that leaks: an
# admitted field carries the whole raw object, so every unadmitted key
# reaches the caller through a field that was allowed. Containment
# (DESIGN.md:192-195) is deleted while every field name still looks
# right.
# ---------------------------------------------------------------------------
amputate "A8  an admitted field forwards the entire raw Jobvite object" \
  "$TOOLS" \
  '        title=raw.get("title") or "",' \
  '        title=str(raw),'

# ---------------------------------------------------------------------------
# A9 - THE INBOUND CHARACTER RULE IS GONE. The identifier type keeps its
# length bound and loses its alphabet, so a NUL or a bidi override is
# admitted into an argument that reaches Jobvite and the audit event.
# DESIGN.md:176-183 and B25.
# ---------------------------------------------------------------------------
amputate "A9  inbound identifiers accept any character" "$CONSTRAINTS" \
  '        pattern=r"\A[A-Za-z0-9_-]+\z",' \
  '        pattern=r"\A[\s\S]*\z",'

# ---------------------------------------------------------------------------
# A10 - THE `summary` FIELD IS GONE. The caller-facing
# `showing N of total` string DESIGN.md:474-476 names disappears from
# the result. `showing` and `total` remain, so a test asserting only the
# numbers survives - and that survivor is the finding, because the
# design specifies the reported STRING.
# ---------------------------------------------------------------------------
amputate "A10 the caller-facing summary string is removed" "$MODELS" \
  '    @computed_field  # type: ignore[prop-decorator]
    @property
    def summary(' \
  '    @property
    def summary('

# ---------------------------------------------------------------------------
# A11 - TRACE CONTEXT IS NEVER READ from the live context. U3 could not
# test its parse call site against a real FastMCP context because no
# server existed; this row is what proves the composition is asserted
# rather than assumed. With `meta=None` the audit event carries no
# `trace_id`, and the ABSENT arm still passes - which is exactly why
# that arm needs the present arm beside it.
# ---------------------------------------------------------------------------
amputate "A11 the live request _meta is never read (trace context lost)" \
  "$TOOLS" \
  '        request_context = ctx.request_context
        meta = request_context.meta if request_context is not None else None' \
  '        meta = None'

# ---------------------------------------------------------------------------
# A12 - THE COMPUTED-FIELD WALK IS GONE (R4-M1). `fencing_paths` goes
# back to reading `model_fields` only, so `showing` and `summary` - the
# caller-facing string built from data, which is exactly what a fencing
# decision is about - can never carry one and nothing notices.
# ---------------------------------------------------------------------------
amputate "A12 fencing_paths stops walking computed fields" "$FENCING" \
  '    for name in model.model_computed_fields:
        decision = _computed_decision_of(model, name)
        paths[f"{prefix}{PATH_SEPARATOR}{decision.jobvite_key}"] = decision
    return paths' \
  '    return paths'

# ---------------------------------------------------------------------------
# A13 - THE TOP-LEVEL OUTPUT MODEL LOSES A DECISION (R4-M1). Before this
# unit's fix, `JobSearchResult` carried NO decisions at all and no test
# asked it to, because every call site named `Job` by hand. This row is
# what proves the discovery test is doing the work rather than the three
# hand-named call sites.
# ---------------------------------------------------------------------------
amputate "A13 JobSearchResult.total loses its fencing decision" "$MODELS" \
  '    total: Annotated[int, Fenced(_NOT_FREE_TEXT, "total", "integer from the envelope")]' \
  '    total: int'

# ---------------------------------------------------------------------------
# A14 - `_to_job` STOPS SETTING A FIELD (R4-L1). The field stays on the
# model, stays fenced, stays in the output schema, and is `None` in every
# result. Nothing about the model or the registry changes, which is why
# the fencing tests cannot see this and a completeness case must.
# ---------------------------------------------------------------------------
amputate "A14 _to_job silently stops mapping one admitted field" "$TOOLS" \
  '        sent_date=raw.get("sentDate"),' \
  '        sent_date=None,'

echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
echo "########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: $TOTAL_SURVIVORS"
echo "(Survivors are the OUTPUT. Read each one and say why it survived.)"

# The gate is that every row APPLIED its anchor. A row that could not
# find its anchor tested nothing and must not be read as a clean result.
if [ "$APPLIED" -ne "$ROWS" ]; then
  echo "::error::$((ROWS - APPLIED)) row(s) did not apply an anchor - the harness is stale"
  exit 1
fi

# R4-M4's other half: `APPLIED -ne ROWS` is satisfied by 0 == 0, so a
# harness whose rows were all deleted was fully green. Lowering this number
# is a visible diff that has to be defended.
ROW_FLOOR=14
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "::error::the harness holds $ROWS rows, below its floor of $ROW_FLOOR"
  exit 1
fi

# R4-M5. Survivors are output; a row that killed NOTHING is not.
if [ "$VACUOUS" -ne 0 ]; then
  echo "::error::$VACUOUS VACUOUS ROW(S) - a behaviour was deleted and nothing"
  echo "         went red. Search the log above for 'VACUOUS ROW'."
  exit 1
fi
