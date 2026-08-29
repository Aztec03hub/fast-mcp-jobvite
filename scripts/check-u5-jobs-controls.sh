#!/usr/bin/env bash
# U5 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the behaviour it claims to check is wrong,
# which is the vacuous-assertion shape this project has found in every
# unit so far.
#
# The AMPUTATION harness beside this one asks the different question -
# remove the behaviour ENTIRELY, does anything still report success -
# and its survivors are output rather than failure.
#
# LANDING AND RESTORE ARE CHECKED WITH `cmp`, NOT WITH `git diff`.
# `git diff --quiet` reports NO DIFFERENCE for an UNTRACKED file
# whatever that file contains, and this harness is untracked until it is
# committed. That cost four amputation rows on another unit a "did not
# land" verdict when all four had landed, and the contradiction was
# visible in the same output: the mutating step had already asserted its
# anchor was present and unique. A pristine backup is kept to restore
# from anyway, so the correct instrument is already here.
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

TOOLS="src/fast_mcp_jobvite/tools/jobs.py"
MODELS="src/fast_mcp_jobvite/models/jobs.py"
FENCING="src/fast_mcp_jobvite/models/fencing.py"
CONSTRAINTS="src/fast_mcp_jobvite/utils/constraints.py"
SUITE="tests/test_tools_jobs.py"
OUT=/tmp/u5-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1 (R4-N1). The restore check
# used to be `cp backup file; cmp file backup`, which compares equal BY
# CONSTRUCTION after the copy: it could only ever detect a failed `cp`,
# never the thing its message claims - "the tree still carries this row's
# mutation". A CORRUPTED BACKUP passes that check and hands every later
# row a mutated tree. Comparing against a copy taken before any row ran
# is the only form that can see it.
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
  # as a kill - so a renamed, moved or misspelled test made its row
  # report KILLED on every run, forever, while testing nothing. A green
  # that tested nothing, sitting inside the harness whose whole purpose
  # is to find greens that tested nothing.
  #
  # TOTAL is already incremented, so returning here makes fired != total
  # and the run exits 1. That is deliberate: a harness that cannot aim
  # must fail, not report.
  if ! uv run --frozen pytest "$selector" --collect-only -q \
       -p no:cacheprovider >/dev/null 2>&1; then
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved."
    echo "  This row has been reporting KILLED without running. Fix the harness."
    echo
    return
  fi

  local backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
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

  # RESTORED? Against the PRISTINE copy taken before row 1, never
  # against "$backup" - see the note beside PRISTINE_DIR. The harness
  # stops if not: every later row would run against a tree carrying
  # this row's mutation.
  cp "$backup" "$file"
  local pristine="$PRISTINE_DIR/$(echo "$file" | tr / _)"
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
# THE RESULT CAP
# ===========================================================================

# `total` recomputed from the page instead of read from the envelope.
# This is the mutation that makes `showing N of N` true on every call and
# deletes the only signal that a page was capped.
mutate "M1  total is counted from the items, not read from the envelope" \
  "$TOOLS" "$SUITE::test_the_cap_reads_total_from_the_envelope_not_from_the_items" \
  '    total = raw_total if isinstance(raw_total, int) else len(items)' \
  '    total = len(items)'

# The cap is not applied to the slice. Everything Jobvite returned is
# forwarded, and `showing` equals the page size.
mutate "M2  the configured cap is ignored and the whole page is returned" \
  "$TOOLS" "$SUITE::test_the_result_cap_reports_showing_n_of_total" \
  '    jobs = [_to_job(item) for item in items[:max_results] if isinstance(item, dict)]' \
  '    jobs = [_to_job(item) for item in items if isinstance(item, dict)]'

# ===========================================================================
# request_id ON THE WIRE (SS8 #16)
# ===========================================================================

# The namespaced key is misspelled. A caller reading the documented key
# finds nothing, and an id a caller cannot reach discharges nothing.
mutate "M3  the _meta key is not the namespaced one the design specifies" \
  "$TOOLS" "$SUITE::test_case16_read_arm_request_id_on_the_wire_meta" \
  'REQUEST_ID_META_KEY: Final = "com.evolvconsulting.fast-mcp-jobvite/requestId"' \
  'REQUEST_ID_META_KEY: Final = "requestId"'

# The problem object gets a FRESH id rather than the invocation's own,
# so it correlates with nothing. Every member is still present and
# well-formed, which is what makes this the quiet failure.
mutate "M4  the problem carries a fresh uuid, not the invocation's id" \
  "$TOOLS" "$SUITE::test_case16_error_arm_request_id_in_the_problem_object" \
  '                problem = problem_from_exception(exc, event.request_id)' \
  '                import uuid as _u

                problem = problem_from_exception(exc, str(_u.uuid4()))'

# ===========================================================================
# THE OUTPUT SCHEMA
# ===========================================================================

# The default mode. The advertised schema loses the computed fields
# while every result still carries them.
mutate "M5  the output schema is built in validation mode" \
  "$TOOLS" "$SUITE::test_the_tool_advertises_a_serialisation_output_schema" \
  '        output_schema=JobSearchResult.model_json_schema(mode="serialization"),' \
  '        output_schema=JobSearchResult.model_json_schema(),'

# ===========================================================================
# REGISTRATION AND THE ENABLE GATE
# ===========================================================================

# The gate is inverted to a no-op: the tool registers whatever
# JOBVITE_TOOLS says.
mutate "M6  registration ignores settings.enabled_tools" \
  "$TOOLS" "$SUITE::test_a_tool_not_named_is_not_registered" \
  '    if SEARCH_JOBS not in settings.enabled_tools:
        return' \
  '    if False:
        return'

# ===========================================================================
# THE FENCING-DECISION REGISTRY
# ===========================================================================

# A missing decision DEFAULTS instead of raising. This is the exact
# fails-open-on-empty shape R3-L1 removed from `missing_for`, and it is
# the tempting "safe" fix - defaulting to FENCE looks conservative and
# silently admits a field nobody decided about.
mutate "M7  a missing fencing decision defaults instead of raising" \
  "$FENCING" "$SUITE::test_deleting_a_fencing_decision_fails" \
  '    if len(found) != 1:' \
  '    if not found:
        return Fenced(FencingDecision.FENCE, field_name, "defaulted")
    if len(found) != 1:'

# The generated path uses OUR attribute name instead of Jobvite's key.
# The paths look right and match nothing Jobvite ever sends.
mutate "M8  the generated path uses the snake_case model attribute" \
  "$FENCING" "$SUITE::test_the_generated_paths_are_in_jobvites_key_space" \
  '        path = f"{prefix}{PATH_SEPARATOR}{decision.jobvite_key}"' \
  '        path = f"{prefix}{PATH_SEPARATOR}{name}"'

# ===========================================================================
# CONTAINMENT AND INBOUND CONSTRAINTS
# ===========================================================================

# The allow-list leaks for real: an ADMITTED field carries the whole raw
# object, so an unadmitted key reaches the caller through a field that
# was allowed.
#
# THIS ROW REPLACED AN INSTRUMENT FAULT, recorded rather than quietly
# swapped. It was `return Job.model_construct(**raw)`, which SURVIVED -
# and the survivor was not a finding about the test. Measured:
# `model_construct` sets the extras on the instance but `model_dump`
# iterates the DECLARED fields, so nothing extra is ever emitted and
# the mutation created no leak to detect. The test was right and the
# mutation was wrong, which is the same shape U4's A12 row hit.
mutate "M9a an admitted field forwards the whole raw Jobvite object" \
  "$TOOLS" "$SUITE::test_an_unadmitted_jobvite_field_is_dropped_not_returned" \
  '        title=raw.get("title") or "",' \
  '        title=str(raw),'

# The other direction, and it is the one DESIGN.md:186-190 actually
# specifies: an unknown field must be DROPPED, not raised on. Handing
# Jobvite's object straight to the model keeps the field out of the
# result by taking the whole call down on a Jobvite schema change.
mutate "M9b an unadmitted field FAILS the call instead of being dropped" \
  "$TOOLS" "$SUITE::test_an_unadmitted_field_does_not_fail_the_call" \
  '    locations = raw.get("locations") or []' \
  '    return Job(**raw)
    locations = raw.get("locations") or []'

# The character rule is gone from the identifier type. Length and
# alphabet still bound it, so a NUL-bearing value is still refused -
# but a bidi override in a LONGER free-text field would not be, which
# is why SafeText carries the rule separately.
mutate "M10 the identifier pattern admits any character" \
  "$CONSTRAINTS" "$SUITE::test_a_control_character_or_bidi_override_is_rejected" \
  '        pattern=r"\A[A-Za-z0-9_-]+\z",' \
  '        pattern=r"\A.*\z",'

# ===========================================================================
# THE MODEL
# ===========================================================================

# `summary` stops being derived and hardcodes agreement, so the string a
# caller reads no longer follows the numbers beside it.
mutate "M11 the summary string is not derived from showing and total" \
  "$MODELS" "$SUITE::test_the_result_cap_reports_showing_n_of_total" \
  '        return f"showing {self.showing:,} of {self.total:,}"' \
  '        return f"showing {self.showing:,} of {self.showing:,}"'

# ===========================================================================
# THE OUTBOUND REQUEST (R4-H1)
# ===========================================================================
#
# These three rows did not exist, and their absence was the whole of
# R4-H1: the route, the query key and the query value could each be
# broken with the WHOLE suite green - measured at 413 passed, three
# survivors, by docs/reviews/probe-r4-unmutated-anchors.sh. A harness is
# complete over the rows it declares and says nothing about the rows
# nobody declared, so the fix is the test AND the row that stops the
# test rotting back into a name without a body.

# The argument is accepted, validated, audited - and never sent. Jobvite
# answers with the entire first page, the tool returns it, and the
# result says `showing 50 of 1,240`: a wrong answer that explains
# itself. This is exactly the failure SearchJobsInput's own docstring
# says the date filter was withheld to avoid.
mutate "M12 the ids query parameter never reaches the wire" \
  "$TOOLS" "$SUITE::test_the_ids_argument_reaches_the_wire_as_a_query_parameter" \
  '                        params=(
                            {"ids": params.ids} if params.ids is not None else None
                        ),' \
  '                        params=None,'

# The key Jobvite reads is misspelled. Jobvite ignores a parameter it
# does not recognise, so this is silent in production and identical to
# M12 from the caller's side.
mutate "M13 the ids query key is misspelled" \
  "$TOOLS" "$SUITE::test_the_ids_argument_reaches_the_wire_as_a_query_parameter" \
  '{"ids": params.ids} if params.ids is not None else None' \
  '{"id": params.ids} if params.ids is not None else None'

# The route. Every offline case drives a MockTransport that answers
# whatever it is asked, so the path was free.
mutate "M14 JOBS_PATH points at a route that does not exist" \
  "$TOOLS" "$SUITE::test_the_ids_argument_reaches_the_wire_as_a_query_parameter" \
  'JOBS_PATH: Final = "/job"' \
  'JOBS_PATH: Final = "/not-a-route"'

# The paired direction. An implementation that always sent a filter
# would pass M12-M14 and silently filter every unfiltered listing.
mutate "M15 a default call sends an ids filter anyway" \
  "$TOOLS" "$SUITE::test_omitting_ids_sends_no_ids_parameter" \
  '                            {"ids": params.ids} if params.ids is not None else None' \
  '                            {"ids": params.ids or ""}'

# ===========================================================================
# THE ROW FLOOR (R4-M4)
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted - or all skipped - reported fully green. This is the same
# argument this project already applied to the credentialed collect
# ("FLOORED, not merely non-empty ... a count is what catches the
# HALF-empty case") and did not apply to its own harness steps.
#
# Lowering this number is a visible diff that has to be defended, which
# is the property scripts/check-suite-floor.sh already has.
ROW_FLOOR=16
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
