#!/usr/bin/env bash
# U10 AMPUTATION harness. A DIFFERENT question from the mutation one.
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
# defect this harness exists to find, one layer up from the suite. On
# THIS unit a vacuous row means a control could be deleted from the one
# tool that writes to a live ATS and the suite would not notice.
#
# A1 IS THE ROW THAT MATTERS: it deletes the approval guard outright, so
# `create_candidate` writes with no approval at all. If anything in the
# suite still passes there, that assertion is not what stands between a
# caller and an unauthorised record in a real ATS.
#
# `config.py` is U0's file. It is amputated and restored with `cp`,
# verified with `cmp` against a pristine copy taken before row 1; never
# `git checkout`, never `git stash`. It is not edited on this branch,
# only measured.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and an amputation replacing a body with a shorter one can be the same
# size inside one second, in which case stale bytecode runs and the row
# fakes a clean result.

set -uo pipefail

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

APPROVAL="src/fast_mcp_jobvite/approval.py"
TOOLS="src/fast_mcp_jobvite/tools/candidates.py"
CONFIG="src/fast_mcp_jobvite/config.py"
SUITE="tests/test_approval_write.py"
OUT=/tmp/u10-amp.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

for f in "$APPROVAL" "$TOOLS" "$CONFIG"; do
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
# A1 - THE APPROVAL GUARD DOES NOT EXIST. `create_candidate` writes on
# every call, on every era, with no approval requested and none
# required. This is the whole of DESIGN.md §2.2's second gate deleted,
# and it is the row this harness exists for.
# ---------------------------------------------------------------------------
amputate "A1  the approval guard does not exist at all" "$APPROVAL" \
  '    version = observed_protocol_version(ctx)

    if version in MODERN_PROTOCOL_VERSIONS:' \
  '    version = observed_protocol_version(ctx)

    return ApprovalDecision(
        approved=True,
        mechanism=ApprovalMechanism.ELICITATION,
        state=ApprovalState.APPROVED,
        protocol_version=version,
    )

    if version in MODERN_PROTOCOL_VERSIONS:'

# ---------------------------------------------------------------------------
# A2 - THE ERA BRANCH DOES NOT EXIST. Every call takes the MRTR path,
# which DESIGN.md:1158-1159 measured as raising on EVERY arm of the
# handshake era. A single-mechanism guard is broken on one era whichever
# it picks, and this is the picking.
# ---------------------------------------------------------------------------
amputate "A2  there is one mechanism, not two" "$APPROVAL" \
  '    if version in MODERN_PROTOCOL_VERSIONS:
        answers = ctx.input_responses' \
  '    if True:
        answers = ctx.input_responses'

# ---------------------------------------------------------------------------
# A3 - THE CONJUNCTION DOES NOT EXIST on the MRTR leg. Any response at
# all authorises the write: a decline, an acceptance carrying
# `approve: false`, an answer to some other question.
# ---------------------------------------------------------------------------
amputate "A3  any response whatsoever authorises the write" "$APPROVAL" \
  '    if getattr(response, "action", None) != "accept":
        return False
    content = getattr(response, "content", None) or {}
    if not isinstance(content, dict):
        return False
    return content.get("approve") is True' \
  '    return response is not None'

# ---------------------------------------------------------------------------
# A4 - THE UNIDENTIFIABLE-ERA REFUSAL DOES NOT EXIST. A version nobody
# has measured falls through to `ctx.elicit()` on the strength of being
# unrecognised, which is exactly the quiet degradation DESIGN.md:1199-1203
# forbids.
# ---------------------------------------------------------------------------
amputate "A4  an unrecognised era falls through instead of refusing" "$APPROVAL" \
  '    if version in HANDSHAKE_PROTOCOL_VERSIONS:
        result = await ctx.elicit(message, response_type=ApprovalAnswer)' \
  '    if True:
        result = await ctx.elicit(message, response_type=ApprovalAnswer)'

# ---------------------------------------------------------------------------
# A5 - THE APPROVAL REQUEST DESCRIBES NOTHING. The host is asked to
# authorise "this write" with no candidate, no job and no mention of the
# email. DESIGN.md:1134-1143: an approver shown a database row
# authorises an email nobody named.
# ---------------------------------------------------------------------------
amputate "A5  the approval request names neither the person nor the email" "$APPROVAL" \
  '    return (
        f"Create candidate {candidate} in the live Jobvite ATS, "
        f"applying to job {job}, {email_clause}. "
        f"This creates a real record and cannot be undone."
    )' \
  '    return "Approve this write?"'

# ---------------------------------------------------------------------------
# A6 - THE `409` MAPPING DOES NOT EXIST. A duplicate is an anonymous
# upstream failure, so C4-D2's "detection, not prevention" becomes
# neither.
# ---------------------------------------------------------------------------
amputate "A6  a duplicate is indistinguishable from any other failure" "$TOOLS" \
  '    if (
        isinstance(exc, JobviteUpstreamError)
        and exc.upstream_status == DUPLICATE_CANDIDATE_STATUS
    ):' \
  '    if False:'

# ---------------------------------------------------------------------------
# A7 - THE SUCCESS RESULT CARRIES NO `_meta`. §8 #16's write arm has
# nothing to read: an id a caller cannot reach discharges nothing.
#
# THE ANCHOR IS THE WHOLE TAIL BLOCK. The four lines that matter are
# nearly identical in the two READ tools above it in this same file, and
# the short form would match three times - which is U12 breaking eight
# of U5's anchors, arriving one unit later in the file the brief warned
# about.
# ---------------------------------------------------------------------------
amputate "A7  the successful write carries no _meta at all" "$TOOLS" \
  '                warnings = emit(event, AuditPhase.AFTER_WRITE)
                return ToolResult(
                    structured_content=attach_audit_warnings(
                        result.model_dump(mode="json"), warnings
                    ),
                    meta={REQUEST_ID_META_KEY: event.request_id},
                )' \
  '                warnings = emit(event, AuditPhase.AFTER_WRITE)
                return ToolResult(
                    structured_content=attach_audit_warnings(
                        result.model_dump(mode="json"), warnings
                    ),
                )'

# ---------------------------------------------------------------------------
# A8 - NO AUDIT EVENT IS EMITTED ON THE APPROVED PATH. The write happens
# and the trail says nothing about the approval that authorised it,
# which is C4-R1 - a High - unmitigated, and R2-H1's shape on a new
# tool.
# ---------------------------------------------------------------------------
amputate "A8  the approved write emits no audit event before or after" "$TOOLS" \
  '                emit(event, AuditPhase.BEFORE_SIDE_EFFECT)

                try:
                    async with _client() as client:' \
  '                try:
                    async with _client() as client:'

# ---------------------------------------------------------------------------
# A9 - `send_email` IS NEVER FORWARDED. The argument is validated,
# disclosed in the approval request, and then dropped. Safe in the
# outcome and a lie in the disclosure, which is the direction that is
# hard to see.
# ---------------------------------------------------------------------------
amputate "A9  the send_email flag is disclosed and then dropped" "$TOOLS" \
  '            "sendEmail": params.send_email,' \
  '            "sendEmail": False,'

# ---------------------------------------------------------------------------
# A10 - THE DEPLOY-TIME GATE DOES NOT EXIST. `config.py` is U0's file.
# DESIGN.md:227-229 calls this the only unconditionally enforceable gate
# in the design, and it is the one a client cannot bypass.
# ---------------------------------------------------------------------------
amputate "A10 the deploy-time write gate does not exist" "$CONFIG" \
  '        if not self.enable_writes:' \
  '        if False:'

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
