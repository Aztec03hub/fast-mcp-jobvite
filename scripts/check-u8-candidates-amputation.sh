#!/usr/bin/env bash
# U8 AMPUTATION harness. A DIFFERENT question from the mutation one.
#
#   Mutation   asks: change one value - does the NAMED test notice?
#   Amputation asks: remove the BEHAVIOUR ENTIRELY - does anything
#                    still report success?
#
# Amputation has exposed a vacuous assertion in every unit built on this
# project so far. On THIS unit the vacuous shape was predicted before a
# line was written: `IMPLEMENTATION-PLAN.md` §U8 records that §8 #6, #5
# and #20 all pass against a `search_candidates` returning an empty
# page, and two of them carry Criticals. **A1 is that prediction turned
# into a row**: the tool is amputated to return nothing at all, and any
# assertion that survives it was asserting an absence against silence.
#
# SURVIVORS ARE THE OUTPUT, not the failure. For each amputation this
# prints the counts and NAMES every test that still passed, so the
# report can say which assertions survived and why.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp` AGAINST A PRISTINE BACKUP,
# never with `git diff`. `git diff --quiet` reports NO DIFFERENCE for an
# UNTRACKED file whatever it contains.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation that replaces a body with `pass` can be the same
# size inside one second, in which case the interpreter reuses stale
# bytecode and the amputated code never runs.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

TOOLS="src/fast_mcp_jobvite/tools/candidates.py"
MODELS="src/fast_mcp_jobvite/models/candidate.py"
NORMALISE="src/fast_mcp_jobvite/utils/normalise.py"
REDACTION="src/fast_mcp_jobvite/utils/redaction.py"
SUITE="tests/test_tools_candidates.py"
OUT=/tmp/u8-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

for f in "$TOOLS" "$MODELS" "$NORMALISE" "$REDACTION"; do
  cp "$f" "$PRISTINE_DIR/$(echo "$f" | tr / _)" ||
    { echo "COULD NOT TAKE PRISTINE COPY of $f"; exit 3; }
done

echo "########## BASELINE - the intact tree"
timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider >"$OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - 900s with no result, on the INTACT tree."
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

  timeout 900 uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after 900s - this row NEVER FINISHED. Not a kill,"
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

  # THE VACUOUS-ROW GATE (R4-M5). The verdict is the RUN'S EXIT CODE,
  # not `grep -c "^FAILED"`: that grep misses ERROR entirely, and a
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
# A1 - THE TOOL RETURNS AN EMPTY PAGE, ALWAYS. THE PLAN'S OWN PREDICTION,
# TURNED INTO A ROW. `IMPLEMENTATION-PLAN.md` §U8: against a
# `search_candidates` that returns an empty page every time, §8 #6, #5
# and #20 all pass - three green arms over a tool that returns nothing,
# on the unit carrying C6-I1 and C6-S1. EVERY ASSERTION THAT SURVIVES
# THIS ROW IS ONE THE POSITIVE CONTROL EXISTS TO RESCUE.
# ---------------------------------------------------------------------------
#
# THE ANCHOR IS THE TWO-LINE FORM, NOT THE FIRST LINE ALONE. The bare
# `items = payload.get(CANDIDATES_ENVELOPE_KEY) or []` appears TWICE in
# the module - once in `build_result` and once in `_one_record` - and
# the first run of this harness reported `ANCHOR NOT UNIQUE (2 hits)`,
# which is the uniqueness check doing its job on the row that matters
# most in the file.
amputate "A1  the tool returns an empty page whatever Jobvite sent" "$TOOLS" \
  '    items = payload.get(CANDIDATES_ENVELOPE_KEY) or []
    candidates = [' \
  '    items: list[Any] = []
    candidates = ['

# ---------------------------------------------------------------------------
# A2 - FENCING DOES NOT EXIST. `fence_text` becomes the identity, so
# every résumé body, name and self-reported field reaches the model raw
# and DESIGN.md:817-818 is deleted outright. §8 #19 must die here.
# ---------------------------------------------------------------------------
amputate "A2  fence_text is the identity function" "$REDACTION" \
  '    stripped = _FENCE_TOKENS.sub(FENCE_STRIPPED, text)
    return f"{FENCE_OPEN}\n{stripped}\n{FENCE_CLOSE}"' \
  '    return text'

# ---------------------------------------------------------------------------
# A3 - THE DELIMITER STRIPPER IS GONE, THE WRAPPER STAYS. This is the
# HALF-amputation and it is the one that looks safest: every value is
# still fenced, so a test asserting "the value is wrapped" passes, and
# content can close its own fence. DESIGN.md:817-818's second clause,
# deleted alone.
# ---------------------------------------------------------------------------
amputate "A3  content is wrapped but delimiters are no longer stripped" "$REDACTION" \
  '    stripped = _FENCE_TOKENS.sub(FENCE_STRIPPED, text)
    return f"{FENCE_OPEN}\n{stripped}\n{FENCE_CLOSE}"' \
  '    return f"{FENCE_OPEN}\n{text}\n{FENCE_CLOSE}"'

# ---------------------------------------------------------------------------
# A4 - THE PATH-KEYED ALLOW-LIST IS GONE. Every field is passed through
# whatever its path, so containment does not exist and §8 #20's drop
# does not happen. The result is still POPULATED, which is what makes
# this different from A1.
# ---------------------------------------------------------------------------
amputate "A4  the walk admits every field regardless of its path" "$REDACTION" \
  '        decision = _lookup(path, registry)
        if decision is None:' \
  '        decision = _lookup(path, registry)
        if decision is None:
            out[key] = value
            continue
        if False:'

# ---------------------------------------------------------------------------
# A5 - THE WHOLE FENCING WALK IS BYPASSED. `to_candidate` reads the raw
# record. Containment, fencing, the blank unification and the drop all
# disappear in one line, which is the closest thing to "U8 was never
# written" that leaves a working tool.
# ---------------------------------------------------------------------------
amputate "A5  to_candidate reads the raw record, never the fenced one" "$TOOLS" \
  '    fenced = fence_payload(raw, CANDIDATE_FENCING_PATHS, f"{CANDIDATES_ENVELOPE_KEY}[]")' \
  '    fenced = dict(raw)'

# ---------------------------------------------------------------------------
# A6 - THE EMPTY-STRING UNIFICATION IS GONE (§9 hazard 4). `""` reaches
# the caller as a present value carrying nothing, and - because the
# unification runs BEFORE fencing - as a FENCED empty value.
# ---------------------------------------------------------------------------
amputate "A6  the blank/null unification does not exist" "$NORMALISE" \
  '    if isinstance(value, str) and not value.strip():
        return None
    return value' \
  '    return value'

# ---------------------------------------------------------------------------
# A7 - THE DATE NORMALISATION IS GONE (§9 hazard 2). Epoch milliseconds
# reach the caller, so one concept has two spellings depending on which
# way the caller is going. The field is still PRESENT and still a
# value, which is why a completeness assertion cannot see this.
# ---------------------------------------------------------------------------
amputate "A7  epoch milliseconds are never converted to a date" "$NORMALISE" \
  '    moment = dt.datetime.fromtimestamp(value / _MS_PER_SECOND, tz=dt.UTC)
    return moment.strftime(DATE_FORMAT)' \
  '    return str(value)'

# ---------------------------------------------------------------------------
# A8 - THE WRITE SPELLING IS GONE (§8 #24). `ID_KEY_WRITE` collapses
# onto the read one, which is the tidy-up DESIGN.md:1434 says a
# well-meaning refactor performs. The asymmetry is Jobvite's and this
# deletes our record of it.
# ---------------------------------------------------------------------------
amputate "A8  the eId/EId asymmetry is tidied away" "$NORMALISE" \
  'ID_KEY_WRITE: Final = "EId"' \
  'ID_KEY_WRITE: Final = ID_KEY_READ'

# ---------------------------------------------------------------------------
# A9 - THE EEO EXCLUSION IS GONE (§8 #6, C6-I1, Critical). Every EEO
# field is declared on the application model, so the special-category
# data flows straight to a model. THE ROW EXISTS BECAUSE THIS IS THE
# ARM THE PLAN SAYS WAS VACUOUS: on an empty page nothing notices.
# ---------------------------------------------------------------------------
amputate "A9  every EEO field is admitted to the application model" "$MODELS" \
  '    resume: Annotated[
        CandidateResume | None,' \
  '    gender: Annotated[
        str | None, Fenced(_NOT_FREE_TEXT, "gender", "amputation row")
    ] = None
    race: Annotated[
        str | None, Fenced(_NOT_FREE_TEXT, "race", "amputation row")
    ] = None
    veteranStatus: Annotated[  # noqa: N815
        str | None, Fenced(_NOT_FREE_TEXT, "veteranStatus", "amputation row")
    ] = None
    resume: Annotated[
        CandidateResume | None,'

# ---------------------------------------------------------------------------
# A10 - THE PER-DEPTH DECISION IS GONE. Both `title` fields take the
# same decision, which is what a name-keyed registry would produce and
# what DESIGN.md:820-822 exists to prevent. Every OTHER path stays
# correct, so only a case written at the collision can see it.
# ---------------------------------------------------------------------------
amputate "A10 both title fields take one decision, as name-keying would" \
  "$MODELS" \
  '    title: Annotated[str | None, Fenced(_FENCE, "title", _CANDIDATE_TYPED)] = None' \
  '    title: Annotated[
        str | None, Fenced(_NOT_FREE_TEXT, "title", "collapsed onto one decision")
    ] = None'

# ---------------------------------------------------------------------------
# A11 - THE RESULT CAP IS GONE ENTIRELY, and `total` is recomputed to
# agree, so `showing N of N` is true on every call and the cap reports
# nothing because there is nothing to report.
# ---------------------------------------------------------------------------
amputate "A11 the result cap does not exist; total is recomputed to agree" "$TOOLS" \
  '    candidates = [
        to_candidate(item) for item in items[:max_results] if isinstance(item, dict)
    ]
    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return CandidateSearchResult(candidates=candidates, total=total)' \
  '    candidates = [to_candidate(item) for item in items if isinstance(item, dict)]
    return CandidateSearchResult(candidates=candidates, total=len(candidates))'

# ---------------------------------------------------------------------------
# A12 - `_meta` IS NEVER SET ON THE SUCCESS RESULT, on either tool.
# §8 #16's read arm has nothing to read, and the audit event's id
# correlates with nothing a caller can see.
# ---------------------------------------------------------------------------
amputate "A12 the get_candidate success result carries no _meta" "$TOOLS" \
  '                return ToolResult(
                    structured_content=record.model_dump(mode="json"),
                    meta={REQUEST_ID_META_KEY: event.request_id},
                )' \
  '                return ToolResult(
                    structured_content=record.model_dump(mode="json"),
                )'

# ---------------------------------------------------------------------------
# A13 - THE REGISTRATION GATE IS GONE. Both tools register whatever
# `JOBVITE_TOOLS` says, so the deploy-time control DESIGN.md:990-1007
# describes does not exist.
# ---------------------------------------------------------------------------
# U10 ADDED `create_candidate` TO THIS SET AND THE OLD ANCHOR WENT
# STALE - 0 hits, which `check-harness-anchors.py` caught in
# milliseconds and this row would otherwise have reported as a
# non-applying amputation. The anchor is REPOINTED, not shortened: the
# replacement keeps the write out of the mutant set as well, so the row
# still deletes the whole gate rather than two thirds of it.
amputate "A13 registration ignores the enabled-tools gate entirely" "$TOOLS" \
  '    wanted = {
        SEARCH_CANDIDATES,
        GET_CANDIDATE,
        CREATE_CANDIDATE,
    } & settings.enabled_tools
    if not wanted:
        return' \
  '    wanted = {SEARCH_CANDIDATES, GET_CANDIDATE, CREATE_CANDIDATE}'

# ---------------------------------------------------------------------------
# A14 - `to_candidate` SILENTLY STOPS MAPPING ONE ADMITTED FIELD. The
# field stays on the model, stays fenced, stays in the output schema,
# and is `None` in every result. Nothing about the model or the registry
# changes, which is why the fencing tests cannot see this and only a
# completeness case can.
# ---------------------------------------------------------------------------
amputate "A14 to_candidate silently stops mapping one admitted field" "$TOOLS" \
  '        home_phone=fenced.get("homePhone"),' \
  '        home_phone=None,'

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
# harness whose rows were all deleted was fully green. Lowering this
# number is a visible diff that has to be defended.
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
