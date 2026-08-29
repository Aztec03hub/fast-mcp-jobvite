#!/usr/bin/env bash
# U12 AMPUTATION harness. A DIFFERENT question from the mutation one.
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
# `utils/redaction.py` is U3's file. A6 amputates it and restores it with
# `cp`, verified with `cmp` against a pristine copy taken before row 1;
# never `git checkout`, never `git stash`. It is not edited on this
# branch, only measured.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation replacing a body with a shorter one can be the same
# size inside one second, in which case stale bytecode runs and the row
# fakes a clean result.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

TOOLS="src/fast_mcp_jobvite/tools/jobs.py"
MODELS="src/fast_mcp_jobvite/models/job_feed.py"
REDACTION="src/fast_mcp_jobvite/utils/redaction.py"
SUITE="tests/test_tools_job_feed.py"
OUT=/tmp/u12-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

for f in "$TOOLS" "$MODELS" "$REDACTION"; do
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
# A1 - THE RESULT CAP DOES NOT EXIST. Every item Jobvite returned is
# forwarded and `total` is recomputed to agree, so `showing N of N` is
# true on every call and the cap reports nothing because there is
# nothing to report.
# ---------------------------------------------------------------------------
amputate "A1  the in-tool result cap does not exist" "$TOOLS" \
  '    items = payload.get(JOB_FEED_ENVELOPE_KEY) or []
    jobs = [
        _to_feed_job(item) for item in items[:max_results] if isinstance(item, dict)
    ]
    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return JobFeedResult(jobs=jobs, total=total)' \
  '    items = payload.get(JOB_FEED_ENVELOPE_KEY) or []
    jobs = [_to_feed_job(item) for item in items if isinstance(item, dict)]
    return JobFeedResult(jobs=jobs, total=len(jobs))'

# ---------------------------------------------------------------------------
# A2 - THE SUCCESS RESULT CARRIES NO `_meta`. §8 #16's read arm has
# nothing to read: an id a caller cannot reach discharges nothing.
# ---------------------------------------------------------------------------
# THE ANCHOR IS THE WHOLE TAIL BLOCK, and it has to be: the four lines
# that matter are BYTE-IDENTICAL in `search_jobs` one function above, so
# the short form matched twice and the row measured nothing. The block
# starting at `build_feed_result` is unique to this tool.
amputate "A2  the success result carries no _meta at all" "$TOOLS" \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )' \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
            )'

# ---------------------------------------------------------------------------
# A3 - THE AUDIT EVENT IS NEVER EMITTED on the success path. The
# invocation happens and the trail says nothing, which is R2-H1's shape
# on a new tool.
# ---------------------------------------------------------------------------
amputate "A3  the success path emits no audit event" "$TOOLS" \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )' \
  '                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )'

# ---------------------------------------------------------------------------
# A4 - THE CREDENTIAL CLASS IS COLLAPSED. The feed authenticates with
# the v2 pair, which is DESIGN.md:320-321's whole three-class structure
# deleted while every call still succeeds against a mock.
# ---------------------------------------------------------------------------
amputate "A4  the separate feed credential class does not exist" "$TOOLS" \
  '        return JobviteClient(
            api_key=feed_key,
            api_secret=feed_secret,
            company_id=company_id,' \
  '        return JobviteClient(
            api_key=settings.api_key or feed_key,
            api_secret=settings.api_secret or feed_secret,
            company_id=company_id,'

# ---------------------------------------------------------------------------
# A5 - THE v1 ROUTE SELECTION IS GONE. The tool calls the v2 base with
# v2 headers, so the sensitive-URL path does not exist at all - and
# every C5-I1 arm that reads a stream should notice there is no longer a
# jobFeed URL in it.
# ---------------------------------------------------------------------------
amputate "A5  the v1 jobfeed route selection does not exist" "$TOOLS" \
  '                        JOBFEED_PATH,
                        params=_feed_params(params),
                        jobfeed=True,' \
  '                        JOBS_PATH,
                        params=_feed_params(params),'

# ---------------------------------------------------------------------------
# A6 - THE ENFORCEMENT POINT DOES NOT EXIST. `redact_url` returns its
# input. DESIGN.md:312-318's "enforced in one place" deleted outright,
# and the row that says whether C5-I1's arms measure anything at all.
# ---------------------------------------------------------------------------
amputate "A6  the URL redactor returns its input unchanged" "$REDACTION" \
  '    split = urllib.parse.urlsplit(url)
    if not split.query:
        return url' \
  '    return url
    split = urllib.parse.urlsplit(url)
    if not split.query:
        return url'

# ---------------------------------------------------------------------------
# A7 - THE FILTERS DO NOT EXIST. Accepted, validated, audited, never
# sent. The tool returns an unfiltered feed while the caller believes it
# was filtered.
# ---------------------------------------------------------------------------
amputate "A7  no argument ever reaches the query string" "$TOOLS" \
  '                        params=_feed_params(params),' \
  '                        params=None,'

# ---------------------------------------------------------------------------
# A8 - THE ENVELOPE NORMALISATION DOES NOT EXIST. `_to_feed_job` admits
# nothing but the two required fields, so every optional field Jobvite
# sent is silently dropped - containment turned into data loss.
# ---------------------------------------------------------------------------
amputate "A8  the feed job mapping admits nothing optional" "$TOOLS" \
  '        requisition_id=raw.get("requisitionid"),
        category=raw.get("category"),
        job_type=raw.get("jobtype"),
        location=raw.get("location"),
        date=raw.get("date"),
        detail_url=raw.get("detail-url"),
        apply_url=raw.get("apply-url"),
        brief_description=raw.get("briefdescription"),
        description=raw.get("description"),
        hiring_manager=raw.get("hiringManager"),
    )' \
  '    )'

# ---------------------------------------------------------------------------
# A9 - THE ENABLE GATE DOES NOT EXIST. The tool registers whatever
# `JOBVITE_TOOLS` says, which is DESIGN.md:917-934's deploy-time control
# deleted.
# ---------------------------------------------------------------------------
amputate "A9  registration has no enable gate" "$TOOLS" \
  '    if GET_JOB_FEED not in settings.enabled_tools:
        return' \
  '    if False:
        return'

# ---------------------------------------------------------------------------
# A10 - THE `showing`/`summary` DERIVATION DOES NOT EXIST. Both become
# constants, so the string a caller reads follows nothing.
# ---------------------------------------------------------------------------
amputate "A10 the reported cap is a constant, not derived" "$MODELS" \
  '        return f"showing {self.showing:,} of {self.total:,}"' \
  '        return "showing all results"'

# ---------------------------------------------------------------------------
# THE GATE. `ROWS == APPLIED` says every row measured something; VACUOUS
# says whether any row measured NOTHING. Reporting survivors without
# gating on the vacuous count is how a row that deletes a behaviour and
# kills nothing passes CI.
# ---------------------------------------------------------------------------
echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"
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
