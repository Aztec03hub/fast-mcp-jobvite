#!/usr/bin/env bash
# U8 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the behaviour it claims to check is wrong,
# which is the vacuous-assertion shape this project has found in every
# unit so far.
#
# THE AMPUTATION HARNESS BESIDE THIS ONE asks the different question -
# remove the behaviour ENTIRELY, does anything still report success -
# and its survivors are output rather than failure.
#
# WHY THIS UNIT'S ROWS MATTER MORE THAN MOST. `IMPLEMENTATION-PLAN.md`
# §U8 records that three of this unit's arms were VACUOUS until the
# positive control was added: against a `search_candidates` returning an
# empty page, §8 #6, #5 and #20 all pass. Two of those carry Criticals.
# So several rows below deliberately mutate the thing that would make
# the result EMPTY, and the row is only meaningful because the positive
# control asserts the page is not.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains, and this harness is untracked until it is
# committed. That cost four amputation rows on another unit a "did not
# land" verdict when all four had landed.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and a mutation that swaps one value can be the same size inside one
# second - in which case the interpreter reuses stale bytecode, the
# mutated code never runs, and the row reports a clean survivor that is
# an instrument fault rather than a finding.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

TOOLS="src/fast_mcp_jobvite/tools/candidates.py"
MODELS="src/fast_mcp_jobvite/models/candidate.py"
NORMALISE="src/fast_mcp_jobvite/utils/normalise.py"
REDACTION="src/fast_mcp_jobvite/utils/redaction.py"
SUITE="tests/test_tools_candidates.py"
OUT=/tmp/u8-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1 (R4-N1). Comparing a
# restore against "$backup" is equal BY CONSTRUCTION after the copy: it
# can detect only a failed `cp`, never "the tree still carries this
# row's mutation". A corrupted backup passes that check and hands every
# later row a mutated tree.
for f in "$TOOLS" "$MODELS" "$NORMALISE" "$REDACTION"; do
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

  # DOES THE SELECTOR STILL RESOLVE? (R4-M3). pytest exits 4 when a
  # selector matches nothing, and this harness treats ANY non-zero exit
  # as a kill - so a renamed, moved or misspelled test would report
  # KILLED on every run, forever, while testing nothing.
  if ! uv run --frozen pytest "$selector" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1; then
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  This row has been reporting KILLED without running. Fix the harness."
    echo
    return
  fi

  # SC2155: declared and assigned separately, so a failing `echo`/`tr`
  # cannot be masked by `local`'s own exit status (task #38).
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

  # LANDED? `cmp`, for the reason in the header.
  if cmp -s "$file" "$backup"; then
    echo "  MUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi

  uv run --frozen pytest "$selector" -q -p no:cacheprovider >"$OUT" 2>&1
  local rc=$?

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

# ===========================================================================
# §8 #19 - FENCING, INCLUDING CONTENT THAT CLOSES ITS OWN FENCE.
# DESIGN.md:797-798 and :754 (merge-gating).
# ===========================================================================

# Only the CLOSING token is stripped. This passes the committed seed
# fixture - whose payload carries a close - and lets content open a
# second block. THE ROW EXISTS BECAUSE THE SEED IS NOT SUFFICIENT.
mutate "M1  only the closing delimiter is stripped" \
  "$REDACTION" \
  "$SUITE::test_case19_red_team_content_cannot_close_its_own_fence" \
  '    "|".join(re.escape(token) for token in (FENCE_OPEN, FENCE_CLOSE)),
    re.IGNORECASE,' \
  '    re.escape(FENCE_CLOSE),
    re.IGNORECASE,'

# The stripper becomes case-sensitive. Passes the seed, whose payload is
# lowercase, and misses `</JOBVITE_CANDIDATE_DATA>`.
mutate "M2  the delimiter stripper is case-sensitive" \
  "$REDACTION" \
  "$SUITE::test_case19_red_team_content_cannot_close_its_own_fence" \
  '    "|".join(re.escape(token) for token in (FENCE_OPEN, FENCE_CLOSE)),
    re.IGNORECASE,
)' \
  '    "|".join(re.escape(token) for token in (FENCE_OPEN, FENCE_CLOSE)),
)'

# WRAP FIRST, THEN STRIP. The fence's own delimiters are removed along
# with the attacker's, producing a value with no fence at all - a
# refusal that looks like a pass.
mutate "M3  the content is wrapped before it is stripped" \
  "$REDACTION" \
  "$SUITE::test_case19_the_seed_fixtures_payload_cannot_close_its_own_fence" \
  '    stripped = _FENCE_TOKENS.sub(FENCE_STRIPPED, text)
    return f"{FENCE_OPEN}\n{stripped}\n{FENCE_CLOSE}"' \
  '    wrapped = f"{FENCE_OPEN}\n{text}\n{FENCE_CLOSE}"
    return _FENCE_TOKENS.sub(FENCE_STRIPPED, wrapped)'

# Fencing is deleted from the walk: an admitted free-text field is
# passed through raw. The record is still populated, so this is only
# visible because the positive control asserts what the value looks
# like rather than only that it is present.
mutate "M4  an admitted free-text field is passed through unfenced" \
  "$REDACTION" \
  "$SUITE::test_positive_control_a_populated_candidate_round_trips" \
  '            out[key] = fence_text(value)
            continue' \
  '            out[key] = value
            continue'

# ===========================================================================
# §8 #20 - AN UNKNOWN NON-STRING FIELD IS DROPPED, NOT STRINGIFIED.
# ===========================================================================

# The tempting implementation: keep everything, render it as text. This
# is the exact behaviour DESIGN.md:804-805 forbids, and it satisfies any
# assertion phrased about the value's TYPE.
mutate "M5  an unregistered field is stringified instead of dropped" \
  "$REDACTION" \
  "$SUITE::test_case20_an_unknown_non_string_field_is_dropped" \
  '        decision = _lookup(path, registry)
        if decision is None:' \
  '        decision = _lookup(path, registry)
        if decision is None:
            out[key] = str(value)
            continue
        if False:'

# A FENCE decision arriving as a non-string is stringified and then
# fenced. Same forbidden move, one branch over.
mutate "M6  a fenced field arriving as a non-string is stringified" \
  "$REDACTION" \
  "$SUITE::test_case20_a_decided_field_arriving_as_a_non_string_is_dropped" \
  '            if not isinstance(value, str):
                # §8 #20. Fencing is defined for strings only, so this' \
  '            if not isinstance(value, str):
                out[key] = fence_text(str(value))
                continue
            if False:
                # §8 #20. Fencing is defined for strings only, so this'

# ===========================================================================
# PATH-KEYED, NOT NAME-KEYED (DESIGN.md:800-802).
# ===========================================================================

# THE COLLISION ITSELF. Lookup falls back to the LEAF NAME, so
# `candidates[].title` and `candidates[].application.job.title` resolve
# to one decision. Every other case in the file still passes.
mutate "M7  the registry is consulted by leaf name, not by path" \
  "$REDACTION" \
  "$SUITE::test_fencing_is_applied_by_path_and_a_colliding_name_is_unaffected" \
  '    if path in registry:
        return registry[path]
    for registered, decision in registry.items():
        if PATH_WILDCARD in registered and _path_matches(path, registered):
            return decision
    return None' \
  '    leaf = path.rsplit(PATH_SEPARATOR, 1)[-1]
    for registered, decision in registry.items():
        if registered.rsplit(PATH_SEPARATOR, 1)[-1] == leaf:
            return decision
    return None'

# The wildcard is consulted BEFORE the exact path, so a `*` shadows the
# decision someone wrote deliberately.
mutate "M8  a wildcard shadows an exact path" \
  "$REDACTION" \
  "$SUITE::test_an_exact_path_is_not_shadowed_by_a_wildcard" \
  '    if path in registry:
        return registry[path]
    for registered, decision in registry.items():
        if PATH_WILDCARD in registered and _path_matches(path, registered):
            return decision
    return None' \
  '    for registered, decision in registry.items():
        if PATH_WILDCARD in registered and _path_matches(path, registered):
            return decision
    if path in registry:
        return registry[path]
    return None'

# ===========================================================================
# §9 HAZARD 4 - EMPTY STRINGS AND NULLS.
# ===========================================================================

# Truthiness instead of a string test. `0` and `False` become `None`,
# which deletes a legitimate zero.
mutate "M9  the blank test uses truthiness and eats a zero" \
  "$NORMALISE" \
  "$SUITE::test_the_unification_does_not_touch_a_non_string" \
  '    if isinstance(value, str) and not value.strip():
        return None
    return value' \
  '    if not value:
        return None
    return value'

# Whitespace stops counting as blank, so `" "` reaches the caller as a
# present value carrying nothing.
mutate "M10 whitespace no longer counts as blank" \
  "$NORMALISE" \
  "$SUITE::test_empty_strings_and_nulls_are_unified_both_directions" \
  '    if isinstance(value, str) and not value.strip():' \
  '    if isinstance(value, str) and value == "":'

# ===========================================================================
# §9 HAZARD 2 - THE DATE ASYMMETRY.
# ===========================================================================

# The milliseconds are treated as seconds. Every date is wrong by a
# factor of a thousand and the value still looks like a date.
mutate "M11 epoch milliseconds are read as seconds" \
  "$NORMALISE" \
  "$SUITE::test_epoch_milliseconds_become_the_request_sides_date_spelling" \
  '    moment = dt.datetime.fromtimestamp(value / _MS_PER_SECOND, tz=dt.UTC)' \
  '    moment = dt.datetime.fromtimestamp(value, tz=dt.UTC)'

# The strict parse becomes a permissive one, so `14/11/2023` is accepted
# and silently means something else.
mutate "M12 a malformed date is guessed rather than refused" \
  "$NORMALISE" \
  "$SUITE::test_a_malformed_date_is_refused_rather_than_guessed" \
  '    try:
        parsed = dt.datetime.strptime(value, DATE_FORMAT).replace(tzinfo=dt.UTC)
    except ValueError as exc:
        msg = f"expected a {DATE_FORMAT_LABEL} date, got {value!r}"
        raise ValueError(msg) from exc' \
  '    parsed = dt.datetime.fromisoformat(value.replace("/", "-")).replace(
        tzinfo=dt.UTC
    )'

# ===========================================================================
# §8 #24 - THE eId/EId CASING ASYMMETRY.
# ===========================================================================

# THE TIDY-UP THE CASE EXISTS TO PREVENT. The write spelling is
# "corrected" to match the read one, which is exactly what
# DESIGN.md:1414 calls "the kind of wart a well-meaning normalisation
# removes".
mutate "M13 the write spelling is tidied into the read one" \
  "$NORMALISE" \
  "$SUITE::test_case24_reads_use_lowercase_eid_and_the_write_uses_capital_eid" \
  'ID_KEY_WRITE: Final = "EId"' \
  'ID_KEY_WRITE: Final = "eId"'

# The reader stops accepting the write spelling, so a create response
# read through this model has no identifier at all.
mutate "M14 the reader accepts only the read spelling" \
  "$NORMALISE" \
  "$SUITE::test_case24_the_reader_accepts_both_spellings_and_prefers_the_read_one" \
  '    for key in (ID_KEY_READ, ID_KEY_WRITE):' \
  '    for key in (ID_KEY_READ,):'

# ===========================================================================
# §8 #6 - EEO FIELDS, ASSERTED AGAINST THE OUTPUT MODELS. C6-I1.
# ===========================================================================

# An EEO field is admitted to the model. This is the failure the case
# exists for, and inspecting a result would not catch it on an empty
# page.
mutate "M15 an EEO field is admitted to the application model" \
  "$MODELS" \
  "$SUITE::test_case6_no_output_model_declares_an_eeo_field" \
  '    workflow_state: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "workflowState", "enumerated workflow state"),
    ] = None' \
  '    workflow_state: Annotated[
        str | None,
        Fenced(_NOT_FREE_TEXT, "workflowState", "enumerated workflow state"),
    ] = None
    veteranStatus: Annotated[  # noqa: N815
        str | None,
        Fenced(_NOT_FREE_TEXT, "veteranStatus", "admitted by mistake"),
    ] = None'

# `extra="allow"` on the application model. Nothing is DECLARED, so a
# test that only reads `model_fields` still passes - and every EEO field
# Jobvite sends is carried anyway.
mutate "M16 the application model allows extra fields" \
  "$MODELS" \
  "$SUITE::test_case6_an_eeo_field_cannot_be_set_on_an_output_model" \
  '    **`gender`, `race` and `veteranStatus` live on this object in every
    fixture we have and are not declared here.** That absence is §6.2'"'"'s
    whole mechanism, and `extra="forbid"` is what makes it unsettable
    rather than merely undeclared.
    """

    model_config = ConfigDict(extra="forbid", strict=True)' \
  '    **`gender`, `race` and `veteranStatus` live on this object in every
    fixture we have and are not declared here.** That absence is §6.2'"'"'s
    whole mechanism, and `extra="forbid"` is what makes it unsettable
    rather than merely undeclared.
    """

    model_config = ConfigDict(extra="allow", strict=True)'

# ===========================================================================
# THE TWO DEPTHS OF `title`, WHICH IS THE PATH-KEYED CASE IN THE MODELS.
# ===========================================================================

# The candidate's own typed title stops being fenced. A name-keyed
# reviewer would call this consistent with the job title one level down.
mutate "M17 the candidate's own title is decided not-free-text" \
  "$MODELS" \
  "$SUITE::test_the_same_name_at_two_depths_gets_two_different_decisions" \
  '    title: Annotated[str | None, Fenced(_FENCE, "title", _CANDIDATE_TYPED)] = None' \
  '    title: Annotated[
        str | None, Fenced(_NOT_FREE_TEXT, "title", "tidied to match the job title")
    ] = None'

# The other direction: the requisition title is fenced too, which is
# the same collision arriving from the safe-looking side.
mutate "M18 the nested job title is fenced like the candidate's" \
  "$MODELS" \
  "$SUITE::test_the_same_name_at_two_depths_gets_two_different_decisions" \
  '        Fenced(
            _NOT_FREE_TEXT,
            "title",
            "requisition title, authored in the operator org - NOT the "' \
  '        Fenced(
            _FENCE,
            "title",
            "requisition title, authored in the operator org - NOT the "'

# ===========================================================================
# THE RESULT CAP AND THE ENVELOPE.
# ===========================================================================

# `total` recomputed from the page. `showing N of N` becomes true on
# every call and the only signal that a page was capped is gone.
mutate "M19 total is counted from the items, not read from the envelope" \
  "$TOOLS" \
  "$SUITE::test_the_cap_reads_total_from_the_envelope_not_from_the_items" \
  '    total = raw_total if isinstance(raw_total, int) else len(items)' \
  '    total = len(items)'

# The cap is never applied to the slice.
mutate "M20 the configured cap is ignored and the whole page is returned" \
  "$TOOLS" \
  "$SUITE::test_the_result_cap_is_applied_to_the_page" \
  '        to_candidate(item) for item in items[:max_results] if isinstance(item, dict)' \
  '        to_candidate(item) for item in items if isinstance(item, dict)'

# ===========================================================================
# THE OUTBOUND REQUEST AND REGISTRATION.
# ===========================================================================

# The id query key is misspelled. Jobvite ignores a parameter it does
# not recognise, so this returns the first PAGE and the tool hands the
# caller a stranger's record.
mutate "M21 the candidateId query key is misspelled" \
  "$TOOLS" \
  "$SUITE::test_the_candidate_id_reaches_the_wire_as_a_query_parameter" \
  'CANDIDATE_ID_PARAM: Final = "candidateId"' \
  'CANDIDATE_ID_PARAM: Final = "candidate_id"'

# The route. Every offline case drives a MockTransport that answers
# whatever it is asked, so the path is free unless a case reads it.
mutate "M22 CANDIDATES_PATH points at a route that does not exist" \
  "$TOOLS" \
  "$SUITE::test_the_candidate_id_reaches_the_wire_as_a_query_parameter" \
  'CANDIDATES_PATH: Final = "/candidate"' \
  'CANDIDATES_PATH: Final = "/not-a-route"'

# The per-tool gate is inverted to a no-op: both tools register whatever
# JOBVITE_TOOLS says.
mutate "M23 registration ignores settings.enabled_tools" \
  "$TOOLS" \
  "$SUITE::test_a_candidate_tool_not_named_is_not_registered" \
  '    if GET_CANDIDATE in wanted:' \
  '    if True:'

# The namespaced `_meta` key loses its namespace. A caller reading the
# documented key finds nothing, and an id a caller cannot reach
# discharges nothing.
mutate "M24 the _meta key is not the namespaced one the design specifies" \
  "$TOOLS" \
  "$SUITE::test_the_meta_key_is_the_one_the_jobs_tool_already_ships" \
  'REQUEST_ID_META_KEY: Final = "com.evolvconsulting.fast-mcp-jobvite/requestId"' \
  'REQUEST_ID_META_KEY: Final = "requestId"'

# The output schema is built in pydantic's DEFAULT mode, so the
# advertised schema loses the computed fields while every result carries
# them.
mutate "M25 the page output schema is built in validation mode" \
  "$TOOLS" \
  "$SUITE::test_both_tools_advertise_serialisation_output_schemas" \
  '            output_schema=CandidateSearchResult.model_json_schema(mode="serialization"),' \
  '            output_schema=CandidateSearchResult.model_json_schema(),'

# ===========================================================================
# THE ROW FLOOR (R4-M4)
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted - or all skipped - reports fully green. Lowering this
# number is a visible diff that has to be defended.
ROW_FLOOR=25
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
