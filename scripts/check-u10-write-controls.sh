#!/usr/bin/env bash
# U10 MUTATION harness. Change one value - does the NAMED test notice?
#
# Every row here must be KILLED. A surviving row means the named test
# passes against a tree where the behaviour it claims to check is wrong.
#
# THE ROWS THAT MATTER MOST ARE M4, M5 AND M6 - the approval conjunction.
# DESIGN.md:1148-1151 requires `action == "accept" AND approve is True`,
# and either half alone admits a refusal as an approval. On this tool
# that means a write nobody authorised, in a live ATS, possibly emailing
# a person. Every one of them is broken here and watched to go red.
#
# AND THE ONE THAT MAKES THE REST MEAN ANYTHING IS NOT HERE AT ALL: the
# positive control, `an APPROVED write moves the row counter by exactly
# one on both eras`. Without it every refusal row below asserts nothing,
# because a `create_candidate` that never writes satisfies all of them.
# FASTMCP-SPIKE-4.md:1431 is the spike recording that against itself.
#
# `config.py` and `utils/normalise.py` are OTHER UNITS' FILES and are
# mutated here, never edited - a harness measures whatever the behaviour
# under test depends on, which is why U12's mutates `utils/redaction.py`
# and U5's mutates `models/fencing.py`. Every row restores with `cp` and
# verifies with `cmp` against a pristine copy taken before row 1 - never
# `git checkout`, never `git stash`.
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

APPROVAL="src/fast_mcp_jobvite/approval.py"
TOOLS="src/fast_mcp_jobvite/tools/candidates.py"
CONFIG="src/fast_mcp_jobvite/config.py"
SUITE="tests/test_approval_write.py"
OUT=/tmp/u10-mut.txt
BACKUP_DIR=$(mktemp -d)
PRISTINE_DIR=$(mktemp -d)
trap 'harness_result_emit; rm -rf "$BACKUP_DIR" "$PRISTINE_DIR"' EXIT

# THE PRISTINE COPIES, TAKEN ONCE BEFORE ROW 1. `cp backup file; cmp file
# backup` compares equal BY CONSTRUCTION and can only detect a failed
# `cp` - a CORRUPTED BACKUP passes it and hands every later row a mutated
# tree.
for f in "$APPROVAL" "$TOOLS" "$CONFIG"; do
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
# THE ERA DISCRIMINATOR (DESIGN.md:1195-1198, FASTMCP-SPIKE-4.md:2063-2074)
# ===========================================================================

# The sessionless tuple swallows the handshake era, so a handshake call
# takes the MRTR path - which DESIGN.md:1159 measured as raising on
# EVERY arm, approve included.
mutate "M1  the modern tuple swallows the handshake era" \
  "$APPROVAL" "$SUITE::test_positive_control_a_recognised_era_approves" \
  'MODERN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ("2026-07-28",)' \
  'MODERN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ("2026-07-28", "2025-11-25")'

# The handshake tuple is emptied, so the era falls into the
# unidentifiable branch and every handshake call refuses. This is the
# guard-that-refuses-everything, and the POSITIVE control is the only
# thing that can see it.
mutate "M2  the handshake era is no longer recognised" \
  "$APPROVAL" \
  "$SUITE::test_positive_control_an_approved_write_moves_the_row_counter_by_one" \
  'HANDSHAKE_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ("2025-11-25",)' \
  'HANDSHAKE_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ()'

# The third case APPROVES instead of refusing. DESIGN.md:1199-1203 says
# an era that cannot be identified must not degrade quietly, and this is
# the quiet degradation.
mutate "M3  an unidentifiable era approves instead of refusing" \
  "$APPROVAL" \
  "$SUITE::test_an_unidentifiable_era_refuses_and_logs_the_observed_value" \
  '    return ApprovalDecision(
        approved=False,
        mechanism=ApprovalMechanism.NO_HANDLER,
        state=ApprovalState.UNAVAILABLE,
        protocol_version=version,
    )' \
  '    return ApprovalDecision(
        approved=True,
        mechanism=ApprovalMechanism.NO_HANDLER,
        state=ApprovalState.UNAVAILABLE,
        protocol_version=version,
    )'

# The discriminator becomes `transport`, which FASTMCP-SPIKE-4.md:2066-2074
# measured as IDENTICAL on both eras. Every call then looks like one era.
mutate "M4  the discriminator is ctx.transport, a measured trap" \
  "$APPROVAL" \
  "$SUITE::test_the_discriminator_is_protocol_version_and_not_transport_or_session_id" \
  '    version = getattr(request_context, "protocol_version", None)' \
  '    version = getattr(request_context, "transport", None)'

# ===========================================================================
# THE CONJUNCTION. THE ROWS THIS HARNESS EXISTS FOR.
# DESIGN.md:1148-1151: `action == "accept" AND approve is True`.
# ===========================================================================

# THE VALUE HALF IS DROPPED on the MRTR leg: an acceptance carrying
# `approve: false` now writes.
mutate "M5  the MRTR leg checks the action and not the value" \
  "$APPROVAL" \
  "$SUITE::test_case22_the_second_leg_actually_consumes_ctx_input_responses" \
  '    return content.get("approve") is True' \
  '    return True'

# THE ACTION HALF IS DROPPED, the mirror of M5. A declined response
# carrying `approve: true` now writes.
#
# **THIS ROW SURVIVED ON ITS FIRST RUN** against
# `test_case22_the_second_leg_actually_consumes_ctx_input_responses`,
# whose three arms are all `action="accept"` - so deleting the action
# check changed nothing any of them could see. The finding was the
# missing arm, not the mutation; the arm below now exists and this row
# is pointed at it.
mutate "M6  the MRTR leg checks the value and not the action" \
  "$APPROVAL" \
  "$SUITE::test_case22_a_declined_answer_carrying_approve_true_refuses" \
  '    if getattr(response, "action", None) != "accept":
        return False' \
  '    if getattr(response, "action", None) == "never-matches":
        return False'

# THE VALUE HALF IS DROPPED on the `ctx.elicit()` leg. Same defect, other
# era - and a harness that only broke the MRTR leg would have missed it,
# which is the fix-one-miss-the-sibling shape.
mutate "M7  the elicit leg accepts any acceptance whatever it carries" \
  "$APPROVAL" \
  "$SUITE::test_case22_an_acceptance_carrying_approve_false_refuses" \
  '        approved = (
            isinstance(result, AcceptedElicitation)
            and isinstance(result.data, ApprovalAnswer)
            and result.data.approve is True
        )' \
  '        approved = isinstance(result, AcceptedElicitation)'

# An answer filed under another key is read as ours, so a host that
# answered a different question authorises this one.
mutate "M8  any answer in the container is read as the approval" \
  "$APPROVAL" "$SUITE::test_case22_an_answer_filed_under_another_key_refuses" \
  '    if isinstance(container, Mapping):
        return container.get(key)' \
  '    if isinstance(container, Mapping):
        return next(iter(container.values()), None)'

# ===========================================================================
# THE EMAIL. `send_email` DEFAULTS FALSE AND THE APPROVAL DISCLOSES IT.
# ===========================================================================

# **THIS ROW SURVIVED ON ITS FIRST RUN** and the survivor was real. The
# field carried `Field(default=False)` AND a trailing `= False`;
# pydantic takes the assignment, so the mutation flipped an INERT copy
# and the test passed against it - on the one field in this server that
# decides whether a live person receives an email. The `Field` copy is
# now gone and this row mutates the declaration that actually decides.
mutate "M9  send_email defaults to true" \
  "$TOOLS" "$SUITE::test_send_email_defaults_to_false_on_the_wire" \
  '                "Setting it true sends mail to a real human being."
            ),
        ),
    ] = False' \
  '                "Setting it true sends mail to a real human being."
            ),
        ),
    ] = True'

# The body hardcodes `false`, so the flag is validated, disclosed in the
# approval request, and then ignored - which makes the disclosure a lie
# in the safe direction.
mutate "M10 the send_email argument never reaches the body" \
  "$TOOLS" "$SUITE::test_send_email_true_is_forwarded_and_not_quietly_dropped" \
  '            "sendEmail": params.send_email,' \
  '            "sendEmail": False,'

# The approval request stops naming the email. DESIGN.md:1134-1143: an
# approver shown "create candidate Jane Doe" approves a database row and
# thereby authorises an email nobody mentioned.
mutate "M11 the approval request no longer discloses the email" \
  "$APPROVAL" \
  "$SUITE::test_the_approval_message_names_the_candidate_the_job_and_the_email" \
  '    email_clause = (
        "AND JOBVITE WILL EMAIL THIS PERSON (send_email=true)"
        if send_email
        else "no email will be sent (send_email=false)"
    )' \
  '    email_clause = "no email will be sent (send_email=false)"'

# ===========================================================================
# THE WIRE BODY AND THE CASING ASYMMETRY (§9 hazards 1 and 4)
# ===========================================================================

mutate "M12 the request direction of the blank unification is dropped" \
  "$TOOLS" "$SUITE::test_the_body_reaches_the_wire_under_jobvites_own_keys" \
  '            "mobile": none_to_blank(params.mobile),' \
  '            "mobile": params.mobile,'

mutate "M13 the write response is read with the READ casing only" \
  "$TOOLS" "$SUITE::test_the_write_response_capital_eid_is_read" \
  '    candidate = application.get(CREATE_CANDIDATE_KEY)
    return CreateCandidateResult(
        application_eid=read_identifier(application),
        candidate_eid=(
            read_identifier(candidate) if isinstance(candidate, dict) else None
        ),
    )' \
  '    candidate = application.get(CREATE_CANDIDATE_KEY)
    return CreateCandidateResult(
        application_eid=application.get("eId"),
        candidate_eid=(candidate.get("eId") if isinstance(candidate, dict) else None),
    )'

# ===========================================================================
# C4-D2 - THE 409. DETECTION, NOT PREVENTION, AND EVEN THE DETECTION IS
# `[INFERRED]` (DESIGN.md:1471-1474).
# ===========================================================================

mutate "M14 the duplicate status is the wrong number" \
  "$TOOLS" "$SUITE::test_a_409_surfaces_as_problems_conflict_naming_the_duplicate" \
  'DUPLICATE_CANDIDATE_STATUS: Final = 409' \
  'DUPLICATE_CANDIDATE_STATUS: Final = 410'

mutate "M15 every upstream failure is dressed up as a conflict" \
  "$TOOLS" \
  "$SUITE::test_a_non_409_upstream_failure_is_not_dressed_up_as_a_conflict" \
  '    if (
        isinstance(exc, JobviteUpstreamError)
        and exc.upstream_status == DUPLICATE_CANDIDATE_STATUS
    ):' \
  '    if isinstance(exc, JobviteUpstreamError):'

# ===========================================================================
# REGISTRATION, ANNOTATIONS AND THE AUDIT RECORD
# ===========================================================================

# `config.py` IS U0's FILE and is mutated, not edited. The deploy-time
# flag is DESIGN.md:227-229's only unconditionally enforceable gate.
mutate "M16 the JOBVITE_ENABLE_WRITES gate does not gate" \
  "$CONFIG" "$SUITE::test_the_write_is_not_registered_without_the_writes_flag" \
  '        if not self.enable_writes:' \
  '        if False:'

mutate "M17 the write advertises itself as read-only" \
  "$TOOLS" "$SUITE::test_the_write_declares_all_three_annotations" \
  '                "destructiveHint": True,
                "idempotentHint": False,
                "readOnlyHint": False,' \
  '                "destructiveHint": True,
                "idempotentHint": False,
                "readOnlyHint": True,'

# C4-R1: the mechanism is hardcoded, so the audit record cannot say
# which path answered - which is the whole thing ADR-0021 exists to make
# recordable.
mutate "M18 the audit mechanism is hardcoded to one era's path" \
  "$APPROVAL" \
  "$SUITE::test_c4r1_the_audit_event_records_approval_state_and_its_mechanism" \
  '            mechanism=ApprovalMechanism.MRTR,' \
  '            mechanism=ApprovalMechanism.ELICITATION,'

# A refused write leaves no trace at all - R2-H1's shape on a new tool.
mutate "M19 a refusal is never audited" \
  "$TOOLS" "$SUITE::test_c4r1_a_refusal_is_audited_too_and_names_the_mechanism" \
  '                    event.result_status = "error"
                    emit(event, AuditPhase.BEFORE_SIDE_EFFECT)
                    return ToolResult(
                        structured_content=problem_from_exception(
                            ApprovalRefusedError(' \
  '                    event.result_status = "error"
                    return ToolResult(
                        structured_content=problem_from_exception(
                            ApprovalRefusedError('

# DESIGN.md:794-800: a post-write audit failure must be SUCCESS WITH A
# WARNING. Under `BEFORE_SIDE_EFFECT` it raises instead, the caller sees
# an error, and the model's reasonable answer is to retry - which emails
# a second live human. This row is the branch existing to prevent that.
mutate "M20 a post-write audit failure fails the call instead of warning" \
  "$TOOLS" \
  "$SUITE::test_case16_the_audit_failure_warning_branch_carries_request_id" \
  '                warnings = emit(event, AuditPhase.AFTER_WRITE)' \
  '                warnings = emit(event, AuditPhase.BEFORE_SIDE_EFFECT)'

# §8 #16: the id a caller cannot reach discharges nothing.
mutate "M21 the successful write returns no request_id on the wire" \
  "$TOOLS" \
  "$SUITE::test_case16_a_successful_write_carries_request_id_on_the_wire" \
  '                return ToolResult(
                    structured_content=attach_audit_warnings(
                        result.model_dump(mode="json"), warnings
                    ),
                    meta={REQUEST_ID_META_KEY: event.request_id},
                )' \
  '                return ToolResult(
                    structured_content=attach_audit_warnings(
                        result.model_dump(mode="json"), warnings
                    ),
                )'

# ===========================================================================
# THE ROW FLOOR
# ===========================================================================
#
# `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose rows were
# all deleted reported fully green. Lowering this number is a visible
# diff that has to be defended.
ROW_FLOOR=21

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
