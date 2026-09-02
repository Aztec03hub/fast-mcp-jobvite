#!/usr/bin/env bash
# U12 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the behaviour it claims to check is wrong.
#
# THE ROW THAT MATTERS MOST IS M16. C5-I1 is a High whose mitigation is
# "redacted at one enforcement point", and the test that asserts it reads
# a log stream. An absence assertion over a silent stream passes, so the
# ONLY way to know the arm measures anything is to break the enforcement
# point and watch it go red. M16 empties `SECRET_QUERY_PARAMS`; if the
# C5-I1 test survives that, the High is unmitigated and reported clean.
#
# `utils/redaction.py` and `services/jobvite_client.py` are OTHER UNITS'
# FILES and are mutated here, never edited. A harness measures whatever
# the behaviour under test depends on; U5's mutates `models/fencing.py`
# and `utils/constraints.py` on the same reasoning. Every row restores
# with `cp` and verifies with `cmp` against a pristine copy taken before
# row 1 - never `git checkout`, never `git stash`.
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
# still quoting the old one. The names below are separate decisions,
# even where two of them share a value today.
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

TOOLS="src/fast_mcp_jobvite/tools/jobs.py"
MODELS="src/fast_mcp_jobvite/models/job_feed.py"
REDACTION="src/fast_mcp_jobvite/utils/redaction.py"
SUITE="tests/test_tools_job_feed.py"
# THE PYTEST LOG THIS RUN READS ITS VERDICTS OUT OF. Per-RUN, never a fixed
# name. Two worktrees on one machine run these harnesses concurrently, and a
# fixed path gives both the SAME INODE: independent `>` offsets leave a NUL
# hole, `grep` then reports "binary file matches" on STDERR and returns an
# EMPTY capture at exit 0, and a rival's `FAILED <nodeid>` lines are read as
# THIS run's kill. Both directions were reproduced - see
# docs/reviews/probe-284-shared-path-collision.sh, and #262 for the false kill
# this class already produced. CI can never catch a regression here: the runner
# has no second worktree.
OUT="$(mktemp /tmp/u12-mut-XXXXXX)"
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR" "$OUT"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can only detect a failed
# `cp` - a CORRUPTED BACKUP passes it and hands every later row a mutated
# tree.
for f in "$TOOLS" "$MODELS" "$REDACTION"; do
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

# Every selector a row aims at, in row order. Verified ONCE against the INTACT
# tree after the last row - see the block above harness_result_ran.
SELECTORS=()

# ---------------------------------------------------------------------------
# mutate <label> <file> <test-selector> <old> <new>
# ---------------------------------------------------------------------------
mutate() {
  local label="$1" file="$2" selector="$3" old="$4" new="$5"
  TOTAL=$((TOTAL + 1))
  # Recorded for the ONE intact-tree check after the last row (#249/R24-H1).
  # Appended here, beside the TOTAL it must equal, so a row added without a
  # selector shows up as a count mismatch rather than as silent under-coverage.
  SELECTORS+=("$selector")

  echo "########## $label"
  echo "  target: $selector"

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

# ===========================================================================
# THE THIRD ENVELOPE KEY (§9 hazard 3)
# ===========================================================================

# The feed reads the v2 key. Jobvite sends `jobs` on this route, so every
# call returns an EMPTY page from a 200 - the silent wrong answer.
mutate "M1  the feed reads the v2 collection key" \
  "$MODELS" "$SUITE::test_the_feed_envelope_key_is_jobs_not_requisitions" \
  'JOB_FEED_ENVELOPE_KEY = "jobs"' \
  'JOB_FEED_ENVELOPE_KEY = "requisitions"'

# ===========================================================================
# THE RESULT CAP - the in-tool half (DESIGN.md:508-516)
# ===========================================================================

mutate "M2  total is counted from the items, not read from the envelope" \
  "$TOOLS" "$SUITE::test_the_cap_reads_total_from_the_envelope_not_from_the_items" \
  '    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return JobFeedResult(jobs=jobs, total=total)' \
  '    return JobFeedResult(jobs=jobs, total=len(items))'

mutate "M3  the configured cap is ignored and the whole page is returned" \
  "$TOOLS" "$SUITE::test_the_result_cap_reports_showing_n_of_total" \
  '        _to_feed_job(item) for item in items[:max_results] if isinstance(item, dict)' \
  '        _to_feed_job(item) for item in items if isinstance(item, dict)'

mutate "M4  the summary string hardcodes agreement with showing" \
  "$MODELS" "$SUITE::test_the_result_cap_reports_showing_n_of_total" \
  '        return f"showing {self.showing:,} of {self.total:,}"' \
  '        return f"showing {self.showing:,} of {self.showing:,}"'

# ===========================================================================
# THE SEPARATE CREDENTIAL CLASS (DESIGN.md:312-333)
# ===========================================================================

# The v2 pair authenticates the feed. Both pairs are configured in the
# test, so the mutant sends a real credential - it just sends the WRONG
# CLASS, which is §7.2's token-scoping axis collapsed while everything
# still works.
mutate "M5  the v2 credential pair authenticates the feed" \
  "$TOOLS" "$SUITE::test_the_registration_factory_uses_the_FEED_credential_class" \
  '            api_key=feed_key,
            api_secret=feed_secret,' \
  '            api_key=settings.api_key or feed_key,
            api_secret=settings.api_secret or feed_secret,'

# The key and the secret swapped. Both are sent, both are the feed
# class, and the request is simply wrong - which no assertion about
# "three query parameters are present" could see.
mutate "M6  the feed key and secret are swapped" \
  "$TOOLS" "$SUITE::test_the_registration_factory_uses_the_FEED_credential_class" \
  '            api_key=feed_key,
            api_secret=feed_secret,
            company_id=company_id,' \
  '            api_key=feed_secret,
            api_secret=feed_key,
            company_id=company_id,'

# The companyId is not passed. `jobfeed_params` refuses, and the refusal
# is R2-L-4's: an internal-error 500, not a misleading 502.
mutate "M7  the companyId credential never reaches the client" \
  "$TOOLS" "$SUITE::test_the_registration_factory_uses_the_FEED_credential_class" \
  '            company_id=company_id,
            max_results=settings.max_results,' \
  '            max_results=settings.max_results,'

# ===========================================================================
# THE ROUTE (DESIGN.md:473, contract §9)
# ===========================================================================

# The v1 branch is not selected, so the call goes to the v2 base with v2
# HEADERS - and a MockTransport answers whatever it is asked, so nothing
# else in the module would notice.
mutate "M8  the v1 jobfeed branch is not selected" \
  "$TOOLS" "$SUITE::test_the_route_is_the_v1_base_not_v2" \
  '                        jobfeed=True,' \
  '                        jobfeed=False,'

mutate "M9  the tool calls the v2 job route instead of the feed" \
  "$TOOLS" "$SUITE::test_the_route_is_the_v1_base_not_v2" \
  '                        JOBFEED_PATH,
                        params=_feed_params(params),' \
  '                        JOBS_PATH,
                        params=_feed_params(params),'

# ===========================================================================
# THE FILTERS ON THE WIRE
# ===========================================================================

mutate "M10 the filters are validated, audited and never sent" \
  "$TOOLS" "$SUITE::test_the_filters_reach_the_wire_under_jobvites_own_keys" \
  '                        params=_feed_params(params),' \
  '                        params=None,'

mutate "M11 the type query key is misspelled" \
  "$TOOLS" "$SUITE::test_the_filters_reach_the_wire_under_jobvites_own_keys" \
  '            ("type", params.job_type),' \
  '            ("jobtype", params.job_type),'

# The paired direction: an unfiltered call sends a filter anyway.
mutate "M12 an unfiltered call sends availableTo regardless" \
  "$TOOLS" "$SUITE::test_omitting_the_filters_sends_neither" \
  '            ("availableTo", params.available_to),' \
  '            ("availableTo", params.available_to or "External"),'

# ===========================================================================
# REGISTRATION, THE SCHEMA AND CONTAINMENT
# ===========================================================================

mutate "M13 registration ignores settings.enabled_tools" \
  "$TOOLS" "$SUITE::test_the_feed_tool_is_not_registered_when_it_is_not_named" \
  '    if GET_JOB_FEED not in settings.enabled_tools:
        return' \
  '    if False:
        return'

mutate "M14 the output schema is built in validation mode" \
  "$TOOLS" "$SUITE::test_the_output_schema_is_built_in_serialisation_mode" \
  '        output_schema=JobFeedResult.model_json_schema(mode="serialization"),' \
  '        output_schema=JobFeedResult.model_json_schema(),'

# An ADMITTED field forwards the whole raw Jobvite object, so an
# unadmitted key reaches the caller through a field that was allowed.
mutate "M15 an admitted field forwards the whole raw Jobvite object" \
  "$TOOLS" "$SUITE::test_an_unadmitted_jobvite_field_is_dropped_not_returned" \
  '        eid=raw.get("id") or "",' \
  '        eid=str(raw),'

# ===========================================================================
# C5-I1 - THE ENFORCEMENT POINT ITSELF. THE ROW THIS HARNESS EXISTS FOR.
# ===========================================================================
#
# `utils/redaction.py` is U3's file, mutated here and restored. If this
# row SURVIVES, the C5-I1 arm passes against a server that publishes the
# feed credential in the clear, and a High is reported mitigated by a
# test that measures nothing.
mutate "M16 the redactor recognises no secret query parameter" \
  "$REDACTION" "$SUITE::test_case2_the_url_bearing_producer_emits_it_redacted" \
  'SECRET_QUERY_PARAMS: Final[frozenset[str]] = frozenset({"api", "sc", "companyid"})' \
  'SECRET_QUERY_PARAMS: Final[frozenset[str]] = frozenset()'

# The narrower form: `sc` alone is dropped from the set, which is the
# mistake DESIGN.md:315-316's own wording invites - §8 names `sc=` and
# an implementer redacting only what the case names leaves the other two.
mutate "M17 the redactor drops the api key from its set" \
  "$REDACTION" "$SUITE::test_case2_no_log_record_carries_the_jobfeed_secret" \
  'frozenset({"api", "sc", "companyid"})' \
  'frozenset({"sc"})'

# ===========================================================================
# THE ROW FLOOR
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted reported fully green. Lowering this number is a visible
# diff that has to be defended.
ROW_FLOOR=17

# ===========================================================================
# DO ALL THE SELECTORS STILL RESOLVE? ONE process, on the INTACT tree.
# ===========================================================================
#
# The property: a renamed, moved or misspelled test must not report a verdict
# forever while running nothing. Until now it was bought with a SECOND pytest
# process per row - `--collect-only`, inside mutate(), before each mutation
# landed. That doubled the process count of the whole harness, and process
# startup is what a per-row harness is made of.
#
# It also asked the question in the wrong place. The property is about the
# INTACT tree, and mutate() is a loop over MUTATED ones. #244 tried replacing
# the per-row probe with a per-row rule reading pytest's rc plus its
# `^ERROR <file> - <Exception>` line, and R24 measured that rule wrong in BOTH
# directions:
#
#   * A mutation that breaks an import reached from `tests/conftest.py` makes
#     pytest abort at CONFTEST LOAD: rc=4, "ImportError while loading conftest",
#     and NO short-test-summary section - so the discriminating line is absent
#     and a REAL KILL reads as a renamed selector.
#   * A genuinely renamed selector PLUS a mutation that breaks the TEST
#     module's own import DOES print that line, so the guard stayed silent and
#     the row was counted KILLED on a test that does not exist.
#
# Neither direction is answerable from a MUTATED run. So ask the intact tree,
# ONCE, after the last row. Every row above restored its file and compared it
# to the pristine copy (exit 3 if it differed), so the tree here is the tree
# row 1 started on, and one `pytest "${SELECTORS[@]}" --collect-only` covers
# the whole row set: one extra process per HARNESS in place of one per ROW.
#
# The recorded count is checked against TOTAL first, so a row that ran without
# recording its selector cannot pass as covered. It REFUSES rather than
# reporting - exit 3, and `harness_result_emit`'s EXIT trap prints
# `status=refused`, which is the honest word for a harness that cannot aim.
#
# Ported from 84d4959 (R24-H1), which was written, reviewed and never landed.
# The same shape already sits on main in check-u3-audit-controls.sh, arrived at
# from the other direction by #252's per-row selection work.
# `-eq 0` FIRST, and it is not redundant with the mismatch test beside it
# (R249-L2). At TOTAL=0 - every `mutate` call deleted - `0 -ne 0` is FALSE, so
# the mismatch arm alone passes, `pytest "${SELECTORS[@]}" --collect-only` runs
# with NO node ids, collects the WHOLE suite, exits 0, and the success line
# below announces a check that asked nothing. `check-u3-audit-controls.sh:461`
# carries this guard for the same reason; dropping it was this port's own
# defect, not one inherited from 84d4959.
if [ "$TOTAL" -eq 0 ] || [ "${#SELECTORS[@]}" -ne "$TOTAL" ]; then
  echo "########## RECORDED ${#SELECTORS[@]} SELECTORS FOR $TOTAL ROWS."
  echo "The check below covers exactly the selectors it is handed. At zero rows"
  echo "it would collect the whole suite and pass having asked nothing; at a"
  echo "mismatch it cannot cover every row. Either way its pass would mean less"
  echo "than it claims. Fix the harness."
  exit 3
fi
timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "${SELECTORS[@]}" \
  --collect-only -q -p no:cacheprovider >"$OUT" 2>&1
sel_rc=$?
if [ "$sel_rc" -ne 0 ]; then
  echo "########## A SELECTOR DOES NOT RESOLVE ON THE INTACT TREE (pytest rc=$sel_rc)."
  if [ "$sel_rc" -eq 124 ]; then
    echo "Read this, not the lines below: collection NEVER FINISHED within"
    echo "${SELECTOR_TIMEOUT}s. That is a hang, not a rename."
  fi
  echo "At least one row named a test that was renamed or moved, so that row"
  echo "has been reporting a verdict without ever running its killer."
  echo "pytest, on the restored tree:"
  tail -20 "$OUT"
  echo "Any row above whose target appears in those ERROR lines printed a"
  echo "verdict it did not earn - read the target, not the verdict."
  exit 3
fi
echo "########## ALL $TOTAL SELECTORS RESOLVE (one intact-tree process)"
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
