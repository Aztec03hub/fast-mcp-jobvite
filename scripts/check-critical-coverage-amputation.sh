#!/usr/bin/env bash
# CRITICAL-COVERAGE AMPUTATION harness (#94).
#
# THE QUESTION THIS ANSWERS, AND WHY IT IS NOT "IS COVERAGE HIGH".
# Task #94 raised two critical-path modules from 78.57% and 80.77%
# BRANCH to 100%. A branch is "covered" the moment a test walks through
# it, asserting nothing - and this project's record is exactly that:
# R3-M2 and R7-L1 were assertions that could not fail, U1 had a
# surviving amputation under a green suite, and R7's M4 put a
# payload-logging middleware into the production stack with all 663
# tests passing.
#
# So every branch closed by #94 gets a row here that DELETES the
# behaviour it covers. A row that goes red is a branch that is tested.
# A VACUOUS ROW - deleted behaviour, nothing red - is a branch that was
# merely walked through, and it is the finding this harness exists for.
#
# ONE ROW IS EXPECTED TO SURVIVE AND IT IS DECLARED, NOT DISCOVERED.
# A1 deletes `approval.py`'s `if request_context is None: return None`,
# and `getattr(None, "protocol_version", None)` is ALSO `None`, so the
# guard's observable behaviour is identical to its absence. That is a
# real finding about the SOURCE, not about the test, and A2 is the row
# that proves the same test can fail: it amputates the reading of the
# discriminator itself. Declaring A1's survival here is what keeps the
# vacuous gate meaningful for the other ten rows - a harness that
# tolerated any survivor would report nothing.
#
# SURVIVORS ARE THE OUTPUT. Each row prints the counts and names every
# test that still passed.
#
# It exits non-zero if it could not run, if the intact baseline is red,
# if a row did not apply its anchor, if the tree was left dirty, if
# fewer than ROW_FLOOR rows ran, or if a row other than A1 went vacuous.
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
# ONLY 0 AND 1 ARE MEASUREMENTS (#254). One sourced copy, never retyped -
# the reasoning and the measurement that established it live in the file.
# shellcheck source=lib/verdict-guard.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/verdict-guard.sh" || {
  echo "::error::scripts/lib/verdict-guard.sh could not be sourced. Without it every"
  echo "         row below scores a broken pytest run as a perfect kill (#254). A"
  echo "         missing source is SILENT: 'command not found' is not fatal without"
  echo "         'set -e' (ADR-0023), shellcheck at --severity=warning does not"
  echo "         follow a source, and the harness would exit 0 with status=ok."
  exit 3
}

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

# DERIVED FROM A RUN, not typed in: twenty rows are defined below and
# `########## ROWS: 20   ANCHORS APPLIED: 20` is what the run printed
# when this was last raised (task #101; it was 18 before, and 15
# before that). The new value is READ OFF THE RUN each time rather
# than added to the old number - adding two to eighteen would have
# produced the same 20 here by luck, and would have been a prediction
# rather than a measurement. `FIRED -ne TOTAL` is satisfied by
# `0 == 0`, so a harness with every row deleted reports "0/0" and
# exits clean without a floor.
ROW_FLOOR=20

#: The one row whose survival is a declared finding rather than a
#: defect. Everything else going vacuous fails this harness.
EXPECTED_SURVIVOR="A1"

APPROVAL="src/fast_mcp_jobvite/approval.py"
CANDIDATES="src/fast_mcp_jobvite/tools/candidates.py"
JOBS="src/fast_mcp_jobvite/tools/jobs.py"
CHECKER="docs/reviews/check-coverage-floors.py"
SUITE="tests/test_approval_write.py tests/test_tools_candidates.py \
tests/test_tools_jobs.py tests/test_tools_job_feed.py \
tests/test_coverage_floors.py"
# THE PYTEST LOG THIS RUN READS ITS VERDICTS OUT OF. Per-RUN, never a fixed
# name. Two worktrees on one machine run these harnesses concurrently, and a
# fixed path gives both the SAME INODE: independent `>` offsets leave a NUL
# hole, `grep` then reports "binary file matches" on STDERR and returns an
# EMPTY capture at exit 0, and a rival's `FAILED <nodeid>` lines are read as
# THIS run's kill. Both directions were reproduced - see
# docs/reviews/probe-284-shared-path-collision.sh, and #262 for the false kill
# this class already produced. CI can never catch a regression here: the runner
# has no second worktree.
OUT="$(mktemp /tmp/critical-coverage-amp-XXXXXX)"
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR" "$OUT"' EXIT

for f in "$APPROVAL" "$CANDIDATES" "$JOBS" "$CHECKER"; do
  cp "$f" "$PRISTINE_DIR/$(echo "$f" | tr / _)" ||
    { echo "COULD NOT TAKE PRISTINE COPY of $f"; exit 3; }
done

echo "########## BASELINE - the intact tree"
# shellcheck disable=SC2086 # SUITE is two paths and must word-split
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
UNEXPECTED_VACUOUS=0

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

  # A `sed`/`replace` that matched nothing succeeds silently, so LANDING
  # is compared against the backup rather than assumed from exit 0.
  if cmp -s "$file" "$backup"; then
    echo "  AMPUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    echo
    return
  fi
  APPLIED=$((APPLIED + 1))

  # shellcheck disable=SC2086 # SUITE is two paths and must word-split
  timeout "$ROW_TIMEOUT" uv run --frozen pytest $SUITE -q -p no:cacheprovider -rA >"$OUT" 2>&1
  local rc=$?

  cp "$backup" "$file"
  local pristine
  pristine="$PRISTINE_DIR/$(echo "$file" | tr / _)"
  if ! cmp -s "$file" "$pristine"; then
    echo "  RESTORE FAILED - $file still differs from the pristine copy taken"
    echo "  before row 1. STOPPING."
    exit 3
  fi

  verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"

  tail -1 "$OUT" | sed 's/^/  /'

  # The verdict is the RUN'S EXIT CODE, never `grep -c "^FAILED"`: that
  # grep misses ERROR entirely, and a collection error is a row going
  # red for a real reason.
  if [ "$rc" -eq 0 ]; then
    VACUOUS=$((VACUOUS + 1))
    case "$label" in
      "$EXPECTED_SURVIVOR "*)
        echo "  *** SURVIVOR, DECLARED *** see the header: this guard's"
        echo "      observable behaviour is identical to its absence."
        ;;
      *)
        echo "  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red."
        echo "      Every assertion below survived. This row measures nothing."
        UNEXPECTED_VACUOUS=$((UNEXPECTED_VACUOUS + 1))
        ;;
    esac
  fi
  # WHICH TEST DIED, NAMED. A row going red is not yet evidence: it
  # could have gone red for a reason unrelated to the branch, and a
  # count cannot tell the two apart. The report quotes these names.
  local killed
  killed=$(grep -E '^FAILED ' "$OUT" | sed 's/^FAILED //; s/ - .*//' || true)
  if [ -n "$killed" ]; then
    echo "  killed:"
    printf '%s\n' "$killed" | sed 's/^/    /'
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
# A1 - THE NO-REQUEST-CONTEXT GUARD IS GONE. Declared survivor, and the
# reason is worth reading: `getattr(None, "protocol_version", None)`
# returns `None`, so deleting this guard changes nothing an approval
# caller can observe. The guard is defensive rather than load-bearing.
# It is NOT unreachable - a context with no request context reaches it
# on every call - so `# pragma: no cover` would be a lie; the row that
# proves the test can fail is A2.
# ---------------------------------------------------------------------------
amputate "A1 the no-request-context guard is deleted" "$APPROVAL" \
  '    request_context = ctx.request_context
    if request_context is None:
        return None
    version = getattr(request_context, "protocol_version", None)' \
  '    request_context = ctx.request_context
    version = getattr(request_context, "protocol_version", None)'

# ---------------------------------------------------------------------------
# A2 - THE DISCRIMINATOR IS NEVER READ. The era is assumed to be the
# modern one, so a context carrying no version at all is answered as a
# first MRTR leg instead of being refused. This is the behaviour the
# no-request-context case actually asserts, and it is what makes that
# case falsifiable.
# ---------------------------------------------------------------------------
amputate "A2 the protocol era is assumed rather than read" "$APPROVAL" \
  '    version = observed_protocol_version(ctx)' \
  '    version = "2026-07-28"'

# ---------------------------------------------------------------------------
# A3 - THE ANSWER CONTAINER'S TYPE GUARD IS GONE. `_answer_for` takes
# `.get` off whatever it was handed. A container shape the pinned
# library does not produce stops being a refusal and becomes an
# AttributeError inside the write path.
# ---------------------------------------------------------------------------
amputate "A3 the answer container is read without a type guard" "$APPROVAL" \
  '    container = getattr(answers, "root", answers)
    if isinstance(container, Mapping):
        return container.get(key)
    return None' \
  '    container = getattr(answers, "root", answers)
    return container.get(key)'

# ---------------------------------------------------------------------------
# A4 - THE CONJUNCTION'S SHAPE GUARD IS GONE. An accepted response
# whose `content` is a JSON string is `.get`-ed directly.
# ---------------------------------------------------------------------------
amputate "A4 the approval conjunction drops its content shape guard" "$APPROVAL" \
  '    content = getattr(response, "content", None) or {}
    if not isinstance(content, dict):
        return False
    return content.get("approve") is True' \
  '    content = getattr(response, "content", None) or {}
    return content.get("approve") is True'

# ---------------------------------------------------------------------------
# A5 - THE DATE NORMALISER IS GONE ENTIRELY. Whatever the envelope
# carried is passed to `epoch_ms_to_date`.
# ---------------------------------------------------------------------------
amputate "A5 the date normaliser passes every value through" "$CANDIDATES" \
  '    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value' \
  '    return value  # type: ignore[return-value]'

# ---------------------------------------------------------------------------
# A6 - ONLY THE BOOL HALF IS GONE. The narrower row, and the one that
# matters most: `bool` is a subclass of `int`, so this version looks
# correct and reports `True` as 1970-01-01 in a record a recruiter
# reads. A wrong date with an explanation is worse than an absent one.
# ---------------------------------------------------------------------------
amputate "A6 the date normaliser stops excluding bool" "$CANDIDATES" \
  '    if isinstance(value, bool) or not isinstance(value, int):' \
  '    if not isinstance(value, int):'

# ---------------------------------------------------------------------------
# A7 - THE REGISTRATION CREDENTIAL GUARD IS GONE. Three tools register
# against credentials that are not there.
# ---------------------------------------------------------------------------
amputate "A7 the registration credential guard is deleted" "$CANDIDATES" \
  '    if settings.api_key is None or settings.api_secret is None:
        msg = (
            f"{sorted(wanted)} enabled but credentials are unset; "
            f"validate_settings should have refused this configuration"
        )
        raise ValueError(msg)
    api_key = settings.api_key' \
  '    api_key = settings.api_key'

# ---------------------------------------------------------------------------
# A8 - THE DEFAULT FACTORY LOSES `max_results`. THIS IS U6-F1 REPRODUCED
# IN THIS MODULE: the client falls back to its own default and
# JOBVITE_MAX_RESULTS moves the in-tool half of the cap and not the
# transport half.
# ---------------------------------------------------------------------------
amputate "A8 the default client factory drops max_results" "$CANDIDATES" \
  '            company_id=settings.company_id,
            max_results=settings.max_results,' \
  '            company_id=settings.company_id,'

# ---------------------------------------------------------------------------
# A9 - THE DEFAULT FACTORY LOSES `start_base_overrides`. THIS IS R5-M1,
# the same defect as A8 in the same argument list, and the reason the
# case asserts `scan_start()` rather than the keyword.
# ---------------------------------------------------------------------------
amputate "A9 the default client factory drops the pagination start base" "$CANDIDATES" \
  '            start_base_overrides=(
                None
                if settings.pagination_start_base is None
                else dict.fromkeys(CLIENT_ROUTES, settings.pagination_start_base)
            ),
        )' \
  '        )'

# ---------------------------------------------------------------------------
# A10 - THE PAGE WALK BECOMES AN INDEX. `payload["candidates"][0]` is
# the naive reading, and it hands a non-object straight to the mapper.
# ---------------------------------------------------------------------------
amputate "A10 the single-record reader indexes instead of walking" "$CANDIDATES" \
  '    for item in items:
        if isinstance(item, dict):
            return to_candidate(item)
    return Candidate()' \
  '    if items:
        return to_candidate(items[0])
    return Candidate()'

# ---------------------------------------------------------------------------
# A11 - THE FAILED READ IS NOT RECORDED AS A FAILURE. The caller still
# gets its problem object; only the audit row lies, which is the arm a
# case asserting `is_error` alone cannot see.
# ---------------------------------------------------------------------------
#
# The anchor carries `record = _one_record(payload)` because the
# `except` line alone appears THREE times in this module - one per tool -
# and a non-unique anchor is refused rather than applied to the first
# hit, which would have amputated a different tool's audit row.
amputate "A11 a failed read is audited as a success" "$CANDIDATES" \
  '                    record = _one_record(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
  '                    record = _one_record(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

# ---------------------------------------------------------------------------
# ROWS A12 TO A15 AMPUTATE THE CHECKER, NOT THE SERVER.
#
# `check-coverage-floors.py` is the artefact that makes ADR-0010's
# per-module floors enforceable rather than documented, and #94's whole
# subject is that an obligation nobody reads is not an obligation. A
# checker whose refusal arms have never been watched fire is the same
# defect one level up: it reports OK, and OK is what it would report
# either way. `tests/test_coverage_floors.py` drives each arm; these
# rows delete the arms and require those cases to notice.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A12 - THE FLOOR COMPARISONS ARE GONE. Every number is read, printed,
# and compared against nothing. THIS IS THE STATE THE REPOSITORY WAS
# ALREADY IN before #94: pyproject.toml's comment said the per-module
# floors were "enforced by the units that create those modules", and
# they were enforced by nobody, which is how two critical paths sat ten
# points under their floor with every gate green.
# ---------------------------------------------------------------------------
amputate "A12 the per-module floor comparisons are deleted" "$CHECKER" \
  '        if line < line_floor:
            failures.append(f"{rel}: {line:.2f}% line, below {line_floor}%")
        if branch_floor and branch < branch_floor:
            failures.append(f"{rel}: {branch:.2f}% branch, below {branch_floor}%")' \
  '        pass'

# ---------------------------------------------------------------------------
# A13 - THE BRANCH FLOOR ALONE IS GONE. The narrower row, and the one
# that matters most here: BOTH of #94's misses were on branch and
# neither was on line, so a checker keeping only the line comparison
# would have reported a clean pass over the exact defect that opened
# this task. Line coverage is the half people look at.
# ---------------------------------------------------------------------------
amputate "A13 only the branch floor comparison is deleted" "$CHECKER" \
  '        if branch_floor and branch < branch_floor:' \
  '        if False and branch_floor and branch < branch_floor:'

# ---------------------------------------------------------------------------
# A14 - THE ROLE JOIN NO LONGER LOOKS FOR UNCLAIMED ROLES. A floor the
# design sets and no module claims goes back to being enforced by
# nothing - silently, with every remaining module at 100% and the
# checker exiting 0. This is #94's second half restored.
# ---------------------------------------------------------------------------
amputate "A14 the join stops noticing a role no module claims" "$CHECKER" \
  '    unclaimed = expected - declared_role_set' \
  '    unclaimed = set()'

# ---------------------------------------------------------------------------
# A15 - THE DESIGN IS NOT PARSED; THE FLOORS ARE TYPED IN. Every number
# still appears, the table still prints, and the checker still refuses a
# module under a floor - so nine of the ten control arms stay green. It
# is a SECOND COPY of ADR-0010's decision, which is the failure mode
# this repository has watched rot in a brief, two obligation rows, a CI
# comment and three harness floors. The control that catches it is the
# synthetic design, whose floors are deliberately not ADR-0010's.
# ---------------------------------------------------------------------------
amputate "A15 the floors are typed in rather than read from the design" "$CHECKER" \
  '    floors, design_role_set = parse_design(design.read_text(encoding="utf-8"))' \
  '    _, design_role_set = parse_design(design.read_text(encoding="utf-8"))
    floors = {
        "overall": 80,
        "tool modules": 85,
        "the Jobvite client": 90,
        "utils/": 95,
        "critical line": 95,
        "critical branch": 90,
    }'

# ---------------------------------------------------------------------------
# ROWS A16 TO A18 ARE TASK #97: THE SAME TWO SHAPES, IN `tools/jobs.py`.
#
# #94 closed the registration credential guard and a read tool's error
# arm in `tools/candidates.py`. `tools/jobs.py` carries both shapes and
# is NOT on DESIGN.md:1445's critical-path list, so ADR-0010 gives it
# the 85% tool-module floor - it measured 97.44% line and 91.67% branch
# with the guard entirely untested, and `check-coverage-floors.py`
# passed it and always would. The floor is not defective; it is loose,
# which is what makes a harness row the only instrument that sees this.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A16 - `search_jobs`' REGISTRATION CREDENTIAL GUARD IS GONE. The tool
# registers against credentials that are not there and reaches for them
# on the first call, turning a misconfiguration into a 500 the caller
# sees. This is A7's shape one module over.
# ---------------------------------------------------------------------------
amputate "A16 the search_jobs registration credential guard is deleted" "$JOBS" \
  '    if settings.api_key is None or settings.api_secret is None:
        msg = (
            f"{SEARCH_JOBS} is enabled but its credentials are unset; "
            f"validate_settings should have refused this configuration"
        )
        raise ValueError(msg)
    api_key = settings.api_key' \
  '    api_key = settings.api_key'

# ---------------------------------------------------------------------------
# A17 - THE FEED READ'S FAILURE IS AUDITED AS A SUCCESS. A11's shape,
# and the row this task exists for: the arm was already at 100% LINE
# coverage before task #97, because a redaction case drives a failing
# call through it on the way to asserting something else. Coverage
# could not distinguish "executed" from "asserted"; this row can.
# ---------------------------------------------------------------------------
#
# The anchor carries `result = build_feed_result(...)` because the
# `except` line and the `result_status` line appear TWICE in this module
# - once per tool - and a non-unique anchor is refused rather than
# applied to the first hit, which would amputate `search_jobs`' audit
# row instead.
amputate "A17 a failed feed read is audited as a success" "$JOBS" \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"' \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem'

# ---------------------------------------------------------------------------
# A18 - ONLY HALF THE GUARD'S DISJUNCTION IS GONE. The narrower row and
# the more interesting one: a guard reading `api_key` alone still
# refuses the configuration that supplies neither credential, so A16's
# broad deletion is satisfied by a case that never separates the two.
# A deployment holding a key and no secret registers the tool.
# ---------------------------------------------------------------------------
amputate "A18 the registration guard reads only half its credential pair" "$JOBS" \
  '    if settings.api_key is None or settings.api_secret is None:' \
  '    if settings.api_key is None:'

# ---------------------------------------------------------------------------
# ROWS A19 AND A20 ARE TASK #101: THE LAST TWO AUDIT ROWS IN THE
# CONTAINER, AND ONE OF THEM IS ON THE WRITE.
#
# #97 did not stop at the two files its brief named. It derived the
# population - `grep -rn 'result_status = "error"' src/` gives SIX
# sites - deleted each one at a time and ran the WHOLE suite. That
# probe is committed at `docs/reviews/probe-audit-row-container.sh` and
# it found TWO survivors, both here in `tools/candidates.py`:
# `search_candidates` and `create_candidate`. A11 and A17 close two of
# the other four; these rows close the last two, and after them every
# member of the derived population is killed by an assertion.
#
# **`tools/candidates.py` measures 100.00% LINE AND 100.00% BRANCH.**
# It is on DESIGN.md:1445's critical-path list at ADR-0010's 95/90
# floors, and both arms below are EXECUTED on every run by cases that
# assert the caller-visible half (`is_error`, the problem object) and
# never read the row. This is what a coverage-invisible gap looks like
# in a module with a perfect number: the only instrument that can see
# it is an amputation.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A19 - `search_candidates`' FAILED READ IS AUDITED AS A SUCCESS.
# A11's shape on the sibling read tool.
# ---------------------------------------------------------------------------
#
# The anchor carries `result = build_result(...)` because the `except`
# line alone appears THREE times in this module and the
# `result_status` line FOUR times; a non-unique anchor is refused
# rather than applied to the first hit, which would amputate a
# different tool's row and produce a plausible wrong verdict.
amputate "A19 a failed candidate search is audited as a success" "$CANDIDATES" \
  '                    result = build_result(payload, settings.max_results)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
  '                    result = build_result(payload, settings.max_results)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

# ---------------------------------------------------------------------------
# A20 - THE WRITE'S FAILURE IS AUDITED AS A SUCCESS. **The most
# serious row in this harness.** This is `create_candidate` on the one
# path where the write may or may not have landed: `AFTER_WRITE`'s
# policy never raises and never fails the call, deliberately, because
# an error that makes the model retry emails a second live human. That
# makes the audit row the ONLY surviving evidence anyone has
# afterwards that the attempt did not succeed - and deleting this line
# records a failed or ambiguous create as a success.
#
# The write emits TWICE. The `BEFORE_SIDE_EFFECT` row is written
# before the POST is attempted and is correctly `success`, so a case
# reading the FIRST row passes on the amputated code; the assertion
# this row proves reads the LAST one.
# ---------------------------------------------------------------------------
amputate "A20 a failed or ambiguous write is audited as a success" "$CANDIDATES" \
  '                    result = build_create_result(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
  '                    result = build_create_result(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

# ---------------------------------------------------------------------------
# THE GATE.
# ---------------------------------------------------------------------------
echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally applied "$APPLIED" "$ROWS"
echo "########## TOTAL SURVIVING ASSERTIONS: $TOTAL_SURVIVORS"
echo "########## VACUOUS ROWS: $VACUOUS (declared survivors included)"
echo "########## UNDECLARED VACUOUS ROWS: $UNEXPECTED_VACUOUS"

# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "ONLY $ROWS ROWS RAN against a floor of $ROW_FLOOR. Rows were deleted"
  echo "or a parser shape stopped matching; either way this is not a green."
  exit 1
fi
if [ "$ROWS" -ne "$APPLIED" ]; then
  echo "A ROW DID NOT APPLY ITS ANCHOR. It measured nothing and said so."
  exit 1
fi
if [ "$UNEXPECTED_VACUOUS" -ne 0 ]; then
  echo "A VACUOUS ROW IS A FINDING: a deleted behaviour that nothing noticed."
  exit 1
fi
