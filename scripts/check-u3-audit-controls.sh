#!/usr/bin/env bash
# U3 MUTATION harness: change one value, require a NAMED test to go red.
#
# This is half of U3's control story. The other half is
# `check-u3-audit-amputation.sh`, which asks the different and harder question
# ("delete the behaviour outright - does anything still report success?").
# U11 found that deleting its flag emission entirely still exited 0, so a
# harness that only mutates values would have passed it.
#
# Each row below names the test that MUST fail. A mutation that turns the suite
# red somewhere else is not a pass: it would prove only that the suite is
# sensitive to something, not that the assertion the design relies on is the one
# watching. That is the difference between a control and a coincidence.
#
# PYTHONDONTWRITEBYTECODE=1 is not optional. `.pyc` invalidation keys on
# (mtime, size), and several mutations here are the same size as the line they
# replace; inside one second the interpreter would reuse stale bytecode and the
# mutant would never run.
#
# Every mutation is grepped for BEFORE the suite runs (it landed) and the file
# is grepped again AFTER the restore (it is gone), because `git checkout --` is
# how a mutation harness silently reverts the fix it was meant to be testing.
#
# PER-ROW SELECTION (task #252). Each row runs only the tests that actually
# EXECUTED the lines it mutates, derived from a coverage map the baseline below
# builds on the pristine tree. The mechanism is `scripts/lib/select-covering-tests.py`
# and it is the same one `check-u9-http-amputation.sh` and
# `check-u4-client-amputation.sh` already use; its docstring carries the argument
# for why this asks the identical question. Two things about it are load-bearing
# HERE and are stated at the call site rather than left to be re-derived:
#   * the WIDE fallback. `rc=4` from the deriver means "no in-process test
#     covered these lines" and the row runs the whole `$SUITE`. This project
#     measures NO coverage inside a child process, and one of the three files in
#     `$SUITE` exists precisely because it drives one - so the map is blind to
#     that file by construction and the fallback is the only thing that can see
#     past it.
#   * the verdict is unchanged and stays FAIL-CLOSED under narrowing. A row
#     passes only when the NAMED test goes red. If a selection ever dropped that
#     test, its row could not silently pass: it would report SURVIVED, or "red
#     but not at $want", and either way `FAIL` goes up and the harness exits 1.
#     Narrowing here cannot manufacture a green, which is why the selection that
#     is refused on the amputation harness - where narrowing shrinks the SURVIVOR
#     LIST, its product, by construction - is admissible on this one.

set -uo pipefail

# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. The names below are separate decisions,
# even where two of them share a value today.
BASELINE_TIMEOUT=900
ROW_TIMEOUT=900
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

AUDIT="src/fast_mcp_jobvite/audit.py"
REDACT="src/fast_mcp_jobvite/utils/redaction.py"
# tests/test_logging_process.py is in the suite deliberately. U3's assertions
# all ran against a sink the FIXTURE installed, which is a real loguru stream
# and not the one the server writes to - so A1 (emit() writes nothing) left
# `test_arm1_before_the_side_effect_the_call_fails` green. The process arms
# observe what the child actually wrote, so an amputated emit() has nowhere
# to hide.
SUITE="tests/test_audit.py tests/test_redaction.py tests/test_logging_process.py"

# THE COVERAGE MAP. Built by the baseline below, on the PRISTINE tree, and read
# once per row to pick the tests that executed the lines that row is about to
# mutate. The database is this run's own, so it cannot be stale against the tree
# being mutated - the same construction as
# `scripts/check-u9-http-amputation.sh` (COVDB at :93, map build at :94-95) and
# `scripts/check-u4-client-amputation.sh` (:88-90).
COVDB="$(mktemp /tmp/u3-controls-covdb-XXXXXX)"
# PER PROCESS, for the same reason as $COVDB above and as #262's $OUT, and this
# is #262's review finding rather than housekeeping. These three used to be the
# fixed paths under /tmp named u3-base, u3-mut and u3-sel .txt. EVERY worktree
# of this repo on this box carries this harness (82 of 82 today, 75 of 77 an
# hour earlier - the number moves, the direction does not; DIAG-262 §3.1 has
# the derivation), and four scripts invoke it, so a second concurrent run
# opening the same path with `>` is the normal state here. Two
# writers then hold independent offsets on one inode and $BASE_OUT/$MUT_OUT/
# $SEL_OUT stop describing THIS run.
#
# $MUT_OUT is the dangerous one: `run_mutation`'s `^(FAILED|ERROR) [^ ]*$want`
# branch reads a VERDICT out of it. A rival truncating it inside a row's window
# costs this run a kill it really made; a rival WRITING there writes the very
# `FAILED <nodeid>` lines that grep accepts, which is a false kill manufactured
# from another process's bytes. Both were reproduced - see
# docs/reviews/DIAG-262-probe-nondeterminism.md §5.2.
#
# Written ONCE into a variable and read everywhere, so `run_mutation`'s pytest
# redirect and its verdict grep cannot drift apart the way a repeated literal
# can. Deliberately NOT a line-number cite: this comment outlives the offsets.
BASE_OUT="$(mktemp /tmp/u3-base-XXXXXX)"
MUT_OUT="$(mktemp /tmp/u3-mut-XXXXXX)"
SEL_OUT="$(mktemp /tmp/u3-sel-XXXXXX)"
# `harness_result_emit` FIRST. `lib/harness-result.sh` armed an EXIT trap at
# source time and bash has no trap stack, so this trap REPLACES it - chaining
# the emitter into the front is what keeps an abort from rendering as silence.
# The mktemp'd files are removed here too: a per-RUN name that is never deleted
# is unbounded accretion, which is a different defect from the shared one.
trap 'harness_result_emit; rm -f "$COVDB" "$BASE_OUT" "$MUT_OUT" "$SEL_OUT"' EXIT

PASS=0
FAIL=0

# Every node id any row aimed at, and a count of the rows that recorded one.
# Verified ONCE against the INTACT tree after the last row - see the block
# above ROW_FLOOR. The shape is 84d4959's (R24-H1): one `--collect-only` per
# HARNESS, never one per row, because #244 measured the per-row probe as
# doubling the process count and process startup is what a per-row harness is
# made of.
SELECTORS=()
SEL_ROWS=0

# `git status --porcelain`, NOT `git diff --quiet`. `git diff` compares the
# worktree to the INDEX, so a file edited and then `git add`-ed reads CLEAN
# and this guard waves it through. Measured: modify + `git add` gives
# `git diff --quiet` exit 0 and `--porcelain` a non-empty `M `.
#
# ONLY THIS GUARD MOVES. The landing and restore checks below stay on
# `git diff` ON PURPOSE: they are paired with `git checkout --`, which
# restores from the INDEX, so index-relative is the reading that matches
# the restore.
if [ -n "$(git status --porcelain -- "$AUDIT" "$REDACT")" ]; then
  echo "ABORT: $AUDIT or $REDACT has uncommitted changes (staged or not)."
  echo "This harness mutates them and restores with 'git checkout --', so it"
  echo "would measure your edit rather than HEAD. Commit or stash first."
  exit 3
fi

echo "########## BASELINE - the intact tree"
# The baseline DOUBLES as the coverage-map build: `--cov-context=test` records
# which test executed which line, and every row below selects out of exactly
# this run of exactly this tree. `--cov-report=` suppresses the report (the map
# is the product, not the percentage) and `--cov-fail-under=0` stops
# pyproject's `fail_under` turning a three-file slice of the suite into a red
# baseline it was never meant to satisfy.
COVERAGE_FILE="$COVDB" timeout "$BASELINE_TIMEOUT" uv run --frozen pytest $SUITE -q \
  -p no:cacheprovider --cov --cov-context=test --cov-report= --cov-fail-under=0 \
  >"$BASE_OUT" 2>&1
baseline_rc=$?
if [ "$baseline_rc" -eq 124 ]; then
  echo "ABORT: THE BASELINE HUNG - ${BASELINE_TIMEOUT}s with no result, on the INTACT tree."
  echo "       This is NOT a red suite: it never finished. Nothing below ran."
  echo "       Rationale for the bound: scripts/check-u9-http-amputation.sh."
  exit 4
fi
if [ "$baseline_rc" -ne 0 ]; then
  echo "ABORT: the intact suite is red; every row below would be meaningless."
  tail -20 "$BASE_OUT"
  exit 3
fi
tail -1 "$BASE_OUT"
echo

# ---------------------------------------------------------------------------
# run_mutation <id> <file> <old> <new> <test-that-must-fail>
# ---------------------------------------------------------------------------
run_mutation() {
  local id="$1" file="$2" old="$3" new="$4" want="$5"

  # WHICH TESTS EXECUTED THE LINES THIS ROW IS ABOUT TO MUTATE. Derived from the
  # PRISTINE tree and BEFORE the write below, because the deriver locates the
  # anchor by text and converts it to line numbers - and the numbers have to be
  # the ones the map was built from.
  #
  # rc=4 is "no in-process test covered these lines" and falls back WIDE to the
  # whole `$SUITE`. Any other non-zero rc is a broken precondition and STOPS the
  # harness: a selection computed from a wrong precondition is a silent wrong
  # zero, and here it would be a silent wrong KILL.
  #
  # The selector is PRINTED, one line per row. A count cannot show which row
  # narrowed to what, and every wrong reading of this column in this project so
  # far has survived being counted and died on being listed.
  local sel sel_rc
  sel=$(printf '%s' "$old" | COVERAGE_DB="$COVDB" \
    python3 scripts/lib/select-covering-tests.py "$file")
  sel_rc=$?
  if [ "$sel_rc" -eq 4 ]; then
    sel="$SUITE"
    echo "$id: SELECTOR fallback=WIDE (no in-process coverage), want=$want -> \$SUITE"
  elif [ "$sel_rc" -ne 0 ]; then
    echo "$id: SELECTOR FAILED (rc=$sel_rc) - fix the harness. STOPPING."
    exit 3
  else
    # THE SELECTION MUST CONTAIN THIS ROW'S NAMED KILLER, or it is not a
    # selection this row can use. MEASURED, and it is why this branch exists
    # rather than being reasoned into the file: M10's killer is
    # `test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself`,
    # which `ast.parse`s audit.py and asserts over the TREE. It never EXECUTES
    # the lines M10 mutates, so no arc is attributed to it and the map cannot
    # name it - and the first run of this conversion took M10 from `killed` to
    # `red, but NOT at $want`.
    #
    # That refutes, in this tree today, the premise
    # `scripts/lib/select-covering-tests.py` states for itself: "a test that
    # never EXECUTES the mutated statements cannot go red because of them". A
    # source-READING test can, and 16 of the test modules here import `ast` or
    # call `inspect.getsource`. The deriver has no way to know that; the caller
    # does, because a CONTROLS row names the test it requires.
    #
    # Matching is the SAME substring rule the verdict below uses (`grep -q
    # "$want"`), on purpose: two different rules for one name is how a row
    # passes one check and fails the other. `$want` is sometimes a prefix
    # (`test_arm3`, `test_case2`) and both sites must read it the same way.
    case "$sel" in
      *"$want"*)
        local -a sel_nodes
        # Word-splitting is WANTED: the deriver prints a space-separated node-id
        # list and `pytest $sel` below consumes it the same way, exactly as
        # `check-u9-http-amputation.sh:186` does.
        # shellcheck disable=SC2206
        sel_nodes=($sel)
        echo "$id: SELECTOR ${#sel_nodes[@]} node(s), want=$want: $sel"
        # Recorded for the ONE intact-tree resolution check after the last row.
        # Only the node-id rows are recorded: a wide-fallback row's selector is
        # $SUITE, three FILE paths that resolve by construction, and adding
        # them would pad the check with members that cannot fail it.
        SELECTORS+=("${sel_nodes[@]}")
        SEL_ROWS=$((SEL_ROWS + 1))
        ;;
      *)
        sel="$SUITE"
        echo "$id: SELECTOR fallback=WIDE, want=$want NOT NAMED by the map -> \$SUITE"
        ;;
    esac
  fi

  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
if s.count(old) != 1:
    print(f"  ANCHOR NOT UNIQUE ({s.count(old)} hits): {old!r}", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
  then
    echo "$id: COULD NOT APPLY - the anchor moved. Fix the harness."
    FAIL=$((FAIL + 1))
    return
  fi

  # The mutation LANDED. This is the control on the control: a replace that
  # silently did nothing gives a green run that means nothing.
  #
  # Compared against GIT, not with grep. An earlier revision of this harness
  # grepped for the replacement text, and `grep -F` with a MULTI-LINE pattern
  # treats each line as a separate alternative - so a multi-line mutation whose
  # first line was an unchanged `if not meta:` matched the RESTORED file and
  # reported a restore failure that had not happened. The instrument was wrong,
  # not the code. `git diff` compares the WHOLE FILE, so no multi-line
  # pattern can be partially matched, which is the failure above.
  #
  # BUT NOT "against the commit" - THAT SENTENCE USED TO STAND HERE AND IT
  # IS FALSE. `git diff` compares the worktree to the INDEX. So did the
  # pre-flight guard at the top of this file, which is why a STAGED edit
  # walked straight past it for months; that guard is now
  # `git status --porcelain` and this check is the one that may stay
  # index-relative. It may stay because the restore is `git checkout --`,
  # which also reads the INDEX - the question has to match the answer the
  # restore writes from. And once the pre-flight has refused every dirty
  # tree, index and HEAD agree anyway.
  #
  # Do NOT "fix" this to `git diff HEAD`, and do NOT change the restore to
  # `git checkout HEAD --`: measured, the latter rewrites the index too and
  # SILENTLY DESTROYS the operator's staged work. Refuse at the door
  # instead.
  if git diff --quiet -- "$file"; then
    echo "$id: MUTATION DID NOT LAND despite a successful write"
    FAIL=$((FAIL + 1))
    return
  fi

  # `$sel` is the covering node-id list derived above, or the whole `$SUITE` on
  # the wide fallback. Unquoted on purpose - it is a LIST, and quoting it would
  # hand pytest one impossible node id.
  timeout "$ROW_TIMEOUT" uv run --frozen pytest $sel -q -p no:cacheprovider -rf >"$MUT_OUT" 2>&1
  local rc=$?
  if [ "$rc" -eq 124 ]; then
    echo "  TIMED OUT after ${ROW_TIMEOUT}s - this row NEVER FINISHED. Not a kill,"
    echo "  not a survivor: no verdict below is a measurement of this row."
  fi

  git checkout -- "$file"
  if ! git diff --quiet -- "$file"; then
    echo "$id: RESTORE FAILED - $file still differs from the commit. STOPPING."
    exit 3
  fi

  # rc 4 and 5 mean the SELECTION did not run, and neither is ever a kill.
  #
  # MEASURED, and this branch exists because the bare form could not reach it
  # and the selecting form can. Planting `this_name_is_undefined_at_import_time`
  # in audit.py and running one row both ways:
  #
  #   pytest $SUITE          rc=2  "Interrupted: 1 error during collection"
  #                                $want appears 0 times
  #   pytest <node id>       rc=4  "ERROR: found no collectors for
  #                                 .../test_audit.py::test_arm3_the_warning_..."
  #                                $want appears 1 time
  #
  # The second is the trap. pytest echoes the NODE ID in its own error line,
  # and a node id CONTAINS the test name - so a bare `grep -q "$want"` matches
  # pytest complaining that it could not collect the test, and the row would
  # report `killed by $want` for a test that never ran. That is the lying green
  # this whole harness exists to prevent, and per-row selection is what makes
  # it reachable: at rc=2 the bare form printed no node id at all.
  #
  # TWO INDEPENDENT GUARDS, because either alone leaves a hole:
  #   * this rc check - a selection that resolved nothing cannot have run the
  #     killer, whatever the text says;
  #   * the verdict grep below, now anchored to a RESULT line (`^FAILED` /
  #     `^ERROR`) rather than to any occurrence of the name.
  if [ "$rc" -eq 4 ] || [ "$rc" -eq 5 ]; then
    echo "$id: THE SELECTION DID NOT RUN (pytest rc=$rc). Not a kill and not a"
    echo "  survivor - the named test never executed, so this row measured"
    echo "  nothing. pytest said:"
    grep -E "^ERROR|no tests ran|Interrupted" "$MUT_OUT" | sed 's/^/      /' | head -3
    FAIL=$((FAIL + 1))
    return
  fi

  if [ "$rc" -eq 0 ]; then
    echo "$id: SURVIVED - the selected tests stayed green. NOT A CONTROL."
    FAIL=$((FAIL + 1))
  # ANCHORED TO A RESULT LINE. `-rf` prints `FAILED <nodeid> - <reason>` in the
  # short summary; an erroring test prints `ERROR <nodeid>`. Matching those two
  # forms - rather than the whole log - is what stops pytest's own diagnostics
  # from being read as a verdict about the code.
  elif grep -qE "^(FAILED|ERROR) [^ ]*$want" "$MUT_OUT"; then
    echo "$id: killed by $want"
    PASS=$((PASS + 1))
  else
    echo "$id: the selected tests went red, but NOT at $want - a coincidence, not a control"
    grep -E '^FAILED' "$MUT_OUT" | sed 's/^/      /' | head -5
    FAIL=$((FAIL + 1))
  fi
}

echo "########## MUTATIONS"

# --- the stdio attribution marker (DESIGN.md:771-776) ----------------------
run_mutation "M1  stdio records the literal \"global\"" "$AUDIT" \
  'ATTRIBUTION_UNAVAILABLE: Final = "unavailable:stdio-has-no-caller-token"' \
  'ATTRIBUTION_UNAVAILABLE: Final = "global"' \
  'test_stdio_never_records_the_literal_global'

run_mutation "M2  stdio keeps the client id instead of discarding it" "$AUDIT" \
  'client_id=client_id if transport is Transport.HTTP else None,' \
  'client_id=client_id,' \
  'test_stdio_never_records_the_literal_global'

# --- trace context, both arms (DESIGN.md:728-729, DESIGN.md:1416-1420) ---------------
run_mutation "M3  trace fields emitted as None instead of omitted" "$AUDIT" \
  'record.update({key: v for key, v in optional.items() if v is not None})' \
  'record.update(optional)' \
  'test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none'

run_mutation "M4  trace id SYNTHESISED when the caller sent none" "$AUDIT" \
  '    if not meta:
        return None' \
  '    if not meta:
        return uuid.uuid4().hex, uuid.uuid4().hex[:16]' \
  'test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none'

run_mutation "M5  an all-zero traceparent accepted as a real join" "$AUDIT" \
  'r"\A00-(?!0{32})([0-9a-f]{32})-(?!0{16})([0-9a-f]{16})-[0-9a-f]{2}\Z"' \
  'r"\A00-([0-9a-f]{32})-([0-9a-f]{16})-[0-9a-f]{2}\Z"' \
  'test_case17_a_malformed_traceparent_yields_nothing_rather_than_a_guess'

# --- the three-branch failure policy (DESIGN.md:784-800) -------------------
run_mutation "M6  a pre-write audit failure no longer fails the call" "$AUDIT" \
  '    if phase is AuditPhase.BEFORE_SIDE_EFFECT:' \
  '    if False:' \
  'test_arm1_before_the_side_effect_the_call_fails'

run_mutation "M7  a post-write audit failure returns no warning" "$AUDIT" \
  '    if phase is AuditPhase.AFTER_WRITE:' \
  '    if False:' \
  'test_arm3'

run_mutation "M8  a read surfaces a warning it must not surface" "$AUDIT" \
  '    # AuditPhase.READ: log to stderr and continue. A read is recoverable
    # and losing the tool is worse than losing one audit line.
    return []' \
  '    return ["audit write failed"]' \
  'test_arm2_on_a_read_it_logs_to_stderr_and_continues'

# --- request_id (DESIGN.md:657-666) ----------------------------------------
run_mutation "M9  an inbound request id echoed WITHOUT validation" "$AUDIT" \
  '    if inbound_request_id is not None and _UUID4_RE.match(inbound_request_id):' \
  '    if inbound_request_id is not None:' \
  'test_an_invalid_inbound_request_id_is_replaced_rather_than_used'

# The anchor carries the comment line above it. The `with` line ALONE appears
# twice - once in the module docstring, which quotes it as the proof that the
# mint and the bind are one statement - and the harness refused to guess which.
run_mutation "M10 the var is set directly, losing correlation.py's finally" "$AUDIT" \
  '    # DESIGN.md:664-666: minted and bound in the same statement.
    with request_id_scope(resolve_request_id(inbound_request_id)) as request_id:' \
  '    request_id = resolve_request_id(inbound_request_id)
    request_id_var.set(request_id)
    if True:' \
  'test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself'

# --- redaction (DESIGN.md:312-318) -----------------------------------------
run_mutation "M11 sc= dropped from the secret parameter set" "$REDACT" \
  'frozenset({"api", "sc", "companyid"})' \
  'frozenset({"api", "companyid"})' \
  'test_case2'

run_mutation "M12 the parameter match becomes case-sensitive" "$REDACT" \
  'if key.lower() in SECRET_QUERY_PARAMS else value' \
  'if key in SECRET_QUERY_PARAMS else value' \
  'test_uppercase_parameter_names_are_still_redacted'

run_mutation "M13 arguments become a DENY-list: unlisted keys pass through" "$REDACT" \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS' \
  '                if key not in ("password",)' \
  'test_an_unlisted_argument_key_is_redacted'

# M14 is the row that EARNED this harness. Its first form removed the container
# walk and SURVIVED - which was not a weak test but a wrong mutation: with the
# walk gone the container was redacted whole, so nothing leaked. Chasing that
# down found the real defect the walk was hiding, and this is the mutation that
# reinstates it.
run_mutation "M14 the allow-list becomes leaf-keyed instead of path-keyed" "$REDACT" \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS
                else _redacted_value(value)' \
  '                if key in NON_SENSITIVE_ARGUMENT_KEYS
                or isinstance(value, Mapping | list)
                else _redacted_value(value)' \
  'test_a_container_under_an_unlisted_key_is_redacted_WHOLE'

# The anchor was `out.append(redact_url(token) if ... else token)` until R2's
# nit-3 split the trailing-punctuation run off the token, which turned that
# expression into an if/else block. Repointed at the redacting call itself,
# which is the SUBJECT of the mutation and the smallest thing that survives a
# reflow of the lines around it.
run_mutation "M15 the exception-message arm stops redacting" "$REDACT" \
  'out.append(redact_url(core) + token[len(core) :])' \
  'out.append(token)' \
  'test_a_url_embedded_in_an_exception_message_is_redacted'

echo
# ===========================================================================
# DO ALL THE DERIVED NODE IDS STILL RESOLVE? ONE process, on the INTACT tree.
# ===========================================================================
#
# The shape is 84d4959's (R24-H1), and the reason it is one-per-harness rather
# than one-per-row is that commit's: #244 removed a per-row `--collect-only`
# because it doubled the process count, and R24 then measured the per-row
# rc-plus-grep rule that replaced it as wrong in BOTH directions. Neither
# question is answerable from a MUTATED run, so ask the intact tree once.
# Every row above restored its file and compared it to the index (exit 3 if it
# differed), so the tree here is the tree row 1 started on.
#
# WHY THIS HARNESS NEEDS IT AT ALL, which is not the same reason the hand-written
# harnesses do. Their selectors are TYPED and can go stale against a rename.
# Mine are DERIVED from a coverage map built minutes earlier in this same run,
# so a stale selector is not the risk - a bad ROUND TRIP is. The map stores a
# test's context string and this harness hands it back to pytest as a node id,
# and nothing until now checked that the two forms agree. MEASURED at the time
# of writing: 75 distinct ids across the selecting rows, all 75 collected,
# rc=0, zero ERROR lines - including two that carry a literal backslash-n from
# a parametrised id, which were the two I expected to fail and did not.
#
# The check is NOT vacuous, and that was measured too rather than assumed:
# an absent node id gives rc=4 `ERROR: not found: ...`, and still rc=4 when it
# is mixed in with a valid one - so one bad id among seventy-five is caught.
if [ "$SEL_ROWS" -gt 0 ]; then
  if [ "${#SELECTORS[@]}" -eq 0 ]; then
    echo "########## $SEL_ROWS ROW(S) SELECTED AND RECORDED NO NODE IDS."
    echo "The check below would pass over an empty list, which is a green that"
    echo "asked nothing. Fix the harness."
    exit 3
  fi
  if ! timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "${SELECTORS[@]}" \
       --collect-only -q -p no:cacheprovider >"$SEL_OUT" 2>&1; then
    echo "########## A DERIVED NODE ID DOES NOT RESOLVE ON THE INTACT TREE."
    echo "The coverage map named a test that pytest will not collect, so at"
    echo "least one row narrowed to a selector that could not run what it"
    echo "aimed at. ${#SELECTORS[@]} id(s) from $SEL_ROWS selecting row(s)."
    echo "pytest, on the restored tree:"
    tail -20 "$SEL_OUT"
    exit 3
  fi
  # The count is id SLOTS, not distinct ids - rows overlap, so the same test is
  # usually named by several of them. Said plainly because an unqualified
  # "209 node ids" against a 107-test suite is a number that invites the wrong
  # arithmetic.
  echo "########## ALL ${#SELECTORS[@]} DERIVED NODE ID SLOTS RESOLVE" \
       "($SEL_ROWS selecting row(s), ids repeat across rows, one intact-tree process)"
fi

echo "########## RESULT: $PASS killed, $FAIL not killed"
# The canonical result line's tally, from the SAME two counters the line
# above prints and the harness's own gate compares - never a recount.
harness_result_tally killed "$PASS" "$((PASS + FAIL))"

# THE ROW FLOOR. `FAIL -eq 0` is satisfied by a harness with no rows at
# all: delete every `run_mutation` call and this prints "0 killed, 0 not
# killed" and exits 0. The row count is PASS + FAIL, since every row
# lands in exactly one of them. DERIVED: this harness printed
# "########## RESULT: 15 killed, 0 not killed" at e5883a0. Lowering this
# number is a visible diff that has to be defended.
ROW_FLOOR=15
ROWS=$((PASS + FAIL))
# The canonical result line's numbers, taken from the harness's own
# counter and its own floor - never a second copy. Called BEFORE the
# comparison below, because that branch exits.
harness_result_ran "$ROWS" "$ROW_FLOOR"
if [ "$ROWS" -lt "$ROW_FLOOR" ]; then
  echo "########## $ROWS/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi

[ "$FAIL" -eq 0 ] || exit 1
