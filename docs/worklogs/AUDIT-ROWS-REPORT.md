# AUDIT-ROWS (task #101) - the container is closed, and a CI guard has been inert since #85

**Agent:** `audit-rows` | **Branch:** `fix/audit-rows` | **Base:** `21207b1` | **2026-08-29 12:07 PM CDT**

Two of the six `result_status = "error"` sites in `src/` were asserted by nothing. Both were in
`tools/candidates.py`, and one was `create_candidate` - the write. Both now have an assertion, both
assertions are proved able to fail by amputation, and the derived population is at **0 vacuous**.

While running the gate stack argument for argument I found that `ci.yml`'s **"Default suite, zero
skips" step has not checked for skips since commit `1e2e48e`.** That is section 5, it is in the
lead's file, and it ships with a one-line fix and two controls.

---

## 0. A correction to my dispatch before anything else

The dispatch message said main was at `1a51107`. It was at **`21207b1`** when I branched -
`1a51107`'s child, the commit that added `docs/briefs/AUDIT-ROWS.md`. I branched off `21207b1`
because `1a51107` does not contain my own brief. Nothing else turned on it, but the number in a
dispatch is the kind of constant `PREAMBLE.md` exists to warn about, so it is recorded rather than
silently corrected.

    $ git -C <repo> rev-parse main
    21207b1e541bbfa4b2d70114bcd78d720a3b43ac

---

## 1. The probe, run on my branch BEFORE anything was touched

Per the brief: the table was verified, not trusted. `docs/reviews/probe-audit-row-container.sh`,
verbatim, at `21207b1` with a clean tree:

```
THE DERIVED POPULATION:
src/fast_mcp_jobvite/tools/candidates.py:646:                    event.result_status = "error"
src/fast_mcp_jobvite/tools/candidates.py:692:                    event.result_status = "error"
src/fast_mcp_jobvite/tools/candidates.py:778:                    event.result_status = "error"
src/fast_mcp_jobvite/tools/candidates.py:806:                    event.result_status = "error"
src/fast_mcp_jobvite/tools/jobs.py:411:                event.result_status = "error"
src/fast_mcp_jobvite/tools/jobs.py:701:                event.result_status = "error"

jobs.py search_jobs                      exit 1  1 failed, 866 passed, 6 deselected in 70.94s
jobs.py get_job_feed                     exit 1  1 failed, 866 passed, 6 deselected in 70.51s
candidates.py search_candidates          exit 0  867 passed, 6 deselected in 70.89s
    *** VACUOUS: the failure is recorded by nobody ***
candidates.py get_candidate              exit 1  1 failed, 866 passed, 6 deselected in 71.06s
candidates.py approval refusal           exit 1  1 failed, 866 passed, 6 deselected in 70.73s
candidates.py create_candidate           exit 0  867 passed, 6 deselected in 71.38s
    *** VACUOUS: the failure is recorded by nobody ***

ROWS: 6   APPLIED: 6   VACUOUS: 2
TREE RESTORED CLEAN
```

**The brief's table holds exactly.** Six sites, six anchors applied, two vacuous, and they are the
two the brief named. The line numbers in the population output are printed by `grep -rn` inside the
probe, so they are cited rather than counted.

---

## 2. Arm one - `search_candidates`

**The case that already drove the arm:** `tests/test_tools_candidates.py`
`test_a_candidate_read_error_is_a_problem_object_not_a_raise`. It builds a server whose transport
returns `b"not json at all"`, calls `search_candidates`, and asserts `is_error` and `status == 502`.
It walked the error arm on every run and never read the row it writes.

**The assertion added** (the fixture and helper already existed in that file):

```python
    event = audit_event(audit_records)
    assert event["result_status"] == "error", (
        "the audit row recorded a failed candidate search as anything other "
        "than an error, so the only surviving evidence of the failure is wrong"
    )
```

**The amputation.** Deleting `event.result_status = "error"` from `search_candidates` - anchored on
the preceding `result = build_result(payload, settings.max_results)` line, because the `except` line
alone appears three times in that module and the `result_status` line four times:

```
--- A19 search_candidates: amputation LANDED, diff:
646d645
<                     event.result_status = "error"
FAILED tests/test_tools_candidates.py::test_a_candidate_read_error_is_a_problem_object_not_a_raise
============================== 1 failed in 1.15s ===============================
A19 search_candidates: pytest EXIT 1
A19 search_candidates: RESTORED byte-identical
```

Restored by `cmp` against a backup taken before the write, not by a reverse `sed`.

---

## 3. Arm two - `create_candidate`, and the shape a naive assertion would have missed

**The case that already drove the arm:** `tests/test_approval_write.py`
`test_an_approved_write_that_times_out_is_attempted_exactly_once`. An approved write whose transport
raises `ConnectTimeout`; it asserted `is_error` and that exactly one attempt was made. This is the
path where the write may or may not have landed, `AFTER_WRITE`'s policy never fails the call by
design, and the audit row is therefore the only surviving evidence.

**My first assertion was WRONG, and the reason is worth more than the fix.** I wrote
`assert len(events) == 1` and `events[0]["result_status"] == "error"`, on the model of the read
tools. It failed, and the failure output is the finding:

```
E   AssertionError: expected one audit event, got [
      {... 'result_status': 'success', ... 'approval_state': APPROVED ...},
      {... 'result_status': 'error',   ... 'approval_state': APPROVED ...}]
E   assert 2 == 1
```

**The write emits TWICE.** `BEFORE_SIDE_EFFECT` is written before the POST is attempted - NO AUDIT,
NO WRITE - and is *correctly* `success`, because nothing had failed yet. Only the `AFTER_WRITE` row
can carry the outcome. **An assertion aimed at `events[0]` would have read the pre-write row, passed
on the amputated code, and shipped as a test that tests nothing** - the exact defect this task
exists to close, reproduced inside its own fix. What made it visible is that I ran the assertion
before believing it.

**The assertion as it stands:**

```python
    events = audit_events(audit_records)
    assert len(events) == 2, (
        f"expected the BEFORE_SIDE_EFFECT and AFTER_WRITE rows, got {events}"
    )
    assert events[0]["result_status"] == "success", (...)
    assert events[-1]["result_status"] == "error", (
        "the audit row recorded a write that may or may not have landed as "
        "anything other than an error, so the only surviving evidence of the "
        "failure is wrong"
    )
```

The middle claim is not decoration: it pins WHICH row carries the verdict, so if a later change
moves the verdict onto the pre-write row the test says so instead of quietly still passing.

**The amputation:**

```
--- A20 create_candidate: amputation LANDED, diff:
806d805
<                     event.result_status = "error"
FAILED tests/test_approval_write.py::test_an_approved_write_that_times_out_is_attempted_exactly_once
============================== 1 failed in 1.13s ===============================
A20 create_candidate: pytest EXIT 1
A20 create_candidate: RESTORED byte-identical
```

---

## 4. The harness rows, and the floor derived from my own run

Two rows added to `scripts/check-critical-coverage-amputation.sh` on A11's model - each deletes ONE
`event.result_status = "error"` line and nothing else, so each proves the audit assertion
specifically rather than the error arm generally:

- **A19** `a failed candidate search is audited as a success`
- **A20** `a failed or ambiguous write is audited as a success`

Both anchors carry the preceding `result = ...` line, so they are unique; the harness refuses a
non-unique anchor rather than applying it to the first hit.

From the harness's own output, both rows killed exactly one test each and nothing else:

```
########## A19 a failed candidate search is audited as a success
  ======================== 1 failed, 198 passed in 3.26s =========================
  killed:
    tests/test_tools_candidates.py::test_a_candidate_read_error_is_a_problem_object_not_a_raise
########## A20 a failed or ambiguous write is audited as a success
  ======================== 1 failed, 198 passed in 3.27s =========================
  killed:
    tests/test_approval_write.py::test_an_approved_write_that_times_out_is_attempted_exactly_once
```

### ROW_FLOOR, read off the run

```
########## ROWS: 20   ANCHORS APPLIED: 20
########## TOTAL SURVIVING ASSERTIONS: 3936
########## VACUOUS ROWS: 1 (declared survivors included)
########## UNDECLARED VACUOUS ROWS: 0
```

`ROW_FLOOR=18` -> **`ROW_FLOOR=20`**, taken from that `ROWS: 20` line. Adding two to eighteen would
have produced the same number here by luck; the comment above the constant now records that it is
read off a run each time, and says so precisely because the coincidence makes the wrong method look
correct. The one vacuous row is `A1`, the declared survivor; undeclared vacuous is 0.

### The `ci.yml` numbers you need (I do not edit that file)

**`ci.yml:804` - `--min-rows 18` must become `--min-rows 20`.** I ran the step's exact command from
my worktree before suggesting it:

```
$ bash scripts/ci-harness-gate.sh check-critical-coverage-amputation.sh \
    --anchors-applied --min-rows 20 --row-re '^########## A[0-9]+ '
GATE EXIT: 0
```

and checked the `--row-re` against the harness's REAL output rather than against the harness source:

```
$ grep -cE '^########## A[0-9]+ ' <the run's output>
20
```

**`check-harness-anchors.py --self-check --floor 456` must become `--floor 458.`** My two rows add
two anchors; the checker already reports the new number and is green because a floor is a minimum:

```
harnesses scanned: 33
anchors resolved: 458
OK: all 458 anchors resolve to exactly one hit in their target file (floor 456).
```

Leaving it at 456 is not red, but it is two rows of slack - which is precisely the drift #91
measured on u7 and #102 is open about.

---

## 5. FINDING (High, in `ci.yml`, which is yours): the zero-skips guard has been inert since `1e2e48e`

`.github/workflows/ci.yml:433`, inside the step named **"Default suite, zero skips"**:

```yaml
          if grep -qE '[0-9]+ skipped'; then <<< "$out"
```

The herestring is on the wrong side of `then`. It redirects the first command of the `then` block;
`grep` gets the step's own stdin, which in a CI runner is empty, so it matches nothing and the guard
never fires. **`bash -n` accepts it and actionlint accepts it** - it is valid shell that does the
wrong thing, which is why seven months of green says nothing about it.

**Provenance, from `git log -L 433,433`.** This was introduced by `1e2e48e`, *"The SIGPIPE sweep
stopped at the scripts/ boundary: ELEVEN more sites in ci.yml"* - task #85 - which rewrote a guard
that had worked since `b53886e`:

```
-          if printf '%s\n' "$out" | grep -qE '[0-9]+ skipped'; then
+          if grep -qE '[0-9]+ skipped'; then <<< "$out"
```

The SIGPIPE concern was real and the rewrite was the right kind of rewrite. It landed one keyword
too far right. `ci.yml:598-607` even names this exact pattern as an instance that "failed OPEN" and
was fixed - **the comment describing the fix is accurate about the intent and wrong about the
result, and it is sitting eight lines below a checker that is green.**

**Proof, run rather than reasoned.** The step's own shape, with input that plainly contains a skip
count, stdin closed as a CI step has it:

```
$ bash /tmp/skipguard-probe.sh < /dev/null      # out="=== 5 passed, 3 skipped in 1.00s ==="
GUARD DID NOT FIRE on output that plainly contains '3 skipped'
RUN_EXIT: 0
```

**Suggested fix - one line, move the herestring onto the `grep`:**

```yaml
          if grep -qE '[0-9]+ skipped' <<< "$out"; then
```

**Positive control** (corrected shape, same skip-carrying input) and **negative control**
(corrected shape, real skip-free output), both run:

```
--- POSITIVE CONTROL: GUARD FIRED: the suite skipped tests.       POS_EXIT: 1
--- NEGATIVE CONTROL: guard correctly silent on skip-free output. NEG_EXIT: 0
```

**Siblings: none.** `grep -rn 'then <<<\|then  *<<<' --include=*.yml --include=*.yaml --include=*.sh .`
over the whole repo returns exactly this one line, and `grep -n 'if grep\|if ! grep'` over `ci.yml`
returns exactly this one site. The population is one.

**Blast radius today is zero, and I checked rather than assuming it.** I ran the skip check myself
with the herestring attached to the `grep`, against the real suite output: `0 SKIPPED` on
`867 passed, 6 deselected`. So the inert guard has not been hiding a skip - it has been failing to
be able to notice one. The 6 are `deselected`, which is selection by `-m` and is not a skip.

---

## 6. Closure: the container, re-measured

`docs/reviews/probe-audit-row-container.sh` re-run on my branch after the fix:

```
jobs.py search_jobs                      exit 1  1 failed, 866 passed, 6 deselected in 51.40s
jobs.py get_job_feed                     exit 1  1 failed, 866 passed, 6 deselected in 51.95s
candidates.py search_candidates          exit 1  1 failed, 866 passed, 6 deselected in 51.96s
candidates.py get_candidate              exit 1  1 failed, 866 passed, 6 deselected in 52.62s
candidates.py approval refusal           exit 1  1 failed, 866 passed, 6 deselected in 51.59s
candidates.py create_candidate           exit 1  1 failed, 866 passed, 6 deselected in 52.44s

ROWS: 6   APPLIED: 6   VACUOUS: 0
TREE RESTORED CLEAN
```

**Every member of the derived population is now killed by an assertion.** 2 vacuous -> 0. The
population is derived by `grep -rn` inside the probe on each run, so a seventh site added tomorrow
appears as a row rather than being missed by a hand-kept list.

Neither module's coverage moved, and nothing here was expected to move it: both were already 100.00%
line and 100.00% branch before I started, which is the whole reason an amputation was the only
instrument that could see this.

---

## 7. Gates, each read from its own exit code on its own line

Floors grepped out of `ci.yml` at run time, never retyped:

    $ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
    check-suite-floor.sh 867
    $ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
    check-harness-anchors.py --self-check --floor 456

| Gate | Command | Exit |
|---|---|---|
| Default suite | `uv run --frozen pytest` -> `867 passed, 6 deselected` | **0** |
| Zero skips | `grep -qE '[0-9]+ skipped' <<< "$out"` -> `0 SKIPPED` | n/a |
| Suite floor | `check-suite-floor.sh 867` -> `suite floor OK: 867 passed, floor 867` | **0** |
| ruff check | `uv run --frozen ruff check .` -> `All checks passed!` | **0** |
| ruff format | `uv run --frozen ruff format --check .` -> `77 files already formatted` | **0** |
| mypy | `uv run --frozen mypy` -> `Success: no issues found in 63 source files` | **0** |
| ShellCheck | `shellcheck --severity=warning` on both scripts I touched | **0** |
| Harness anchors | `check-harness-anchors.py --self-check --floor 456` -> `458 resolved` | **0** |
| Obligations | `check-obligations.py` -> `Mappings: 31 \| verified: 25 \| absent: 6` | **0** |
| Row floors wired | `check-row-floors.py` -> `Harnesses: 32, no floor at either layer: 0` | **0** |
| Row floor exactness | `check-row-floor-exactness.py` -> `Every floor equals its live row count` | **0** |
| Amputation harness | `check-critical-coverage-amputation.sh` -> `20/20, undeclared vacuous 0` | **0** |
| The suggested CI step | `ci-harness-gate.sh ... --min-rows 20 --row-re '^########## A[0-9]+ '` | **0** |
| Container probe | `probe-audit-row-container.sh` -> `6/6, VACUOUS: 0` | **0** |

**867 passed, 0 skipped, 6 deselected.** The suite count did not move because both changes added
assertions to existing cases rather than adding cases, so the 867 floor is met exactly and needs no
raise.

`ruff check` was **red on its first run** - `W505 Doc line too long (79 > 72)` on my new docstring
summary at `tests/test_approval_write.py:1294`. Rewritten, re-run, clean. Recorded because a report
that only shows the final green is a report that hides how many runs it took.

---

## 8. What I did NOT verify

1. **I did not run `actionlint` against `ci.yml`.** It is not on this machine's PATH and I did not
   install it. This matters specifically for §5: I am claiming actionlint accepts the broken guard,
   and my basis for that is `bash -n` accepting it plus the fact that the line has been merged and
   green since `1e2e48e` - not an actionlint run of my own. The defect itself is proved by execution
   and does not depend on this; only the sentence about actionlint does.
2. **I did not run the suggested `ci.yml` edits inside a real GitHub Actions runner.** I ran both
   commands from my worktree, which is what `PREAMBLE.md` asks for, but a runner differs in one way
   that is directly relevant here - stdin - and that difference is the whole mechanism of §5. My
   `< /dev/null` is a model of the runner's stdin, not the runner's stdin.
3. **I did not check whether any OTHER `ci.yml` step's guard reads stdin it does not have.** I swept
   for this defect's exact shape (misplaced `<<<`, and every `if grep` in the file) and the
   population is one. A guard broken some other way would not be in that sweep. Naming the shape I
   looked for is the honest boundary of the claim.
4. **I did not touch `docs/DESIGN.md`, `ci.yml`, or `docs/OBLIGATIONS.md`.** No anchor of mine moved,
   and `check-obligations.py` is green, so no repoint was needed.
5. **`create_candidate`'s 409 and 500 cases still assert only the caller-visible half.** A20 is
   killed by the timeout case, so the row is not vacuous and the container is closed. But those two
   cases drive the same arm and remain silent about the row. That is not a gap in the population -
   it is a redundancy nobody has - and I am recording it rather than widening scope into it.

**The worktree at `/tmp/audit-rows-work` is removed.** I did not push and did not merge.
