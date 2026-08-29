# JOBS-GAPS - task #97

Branch `fix/jobs-gaps`, based at `280b689`. Not merged, not pushed.
Worktree `/tmp/jobs-gaps-work`, removed after this report was committed.
Written 2026-08-29 11:28 AM CDT.

Every number below was copied from a terminal on this branch. Nothing here was
predicted from the brief.

---

## 1. THE BRIEF'S SECOND GAP HAD ALREADY CLOSED, AND THAT IS THE FINDING

The task was dispatched with figures measured at `1c54ebc`:

```
tools/jobs.py   93.33% line   91.67% branch
missing lines    [281, 285, 703, 704, 705, 706, 707]
missing branch   280->281
```

Re-measured on this branch at `280b689`, `uv run --frozen pytest --cov
--cov-report=json`:

```
tools/jobs.py   97.44% line   91.67% branch  (11/12)
missing lines    [280, 284]
missing branches [[279, 280]]
```

The registration guard is still uncovered - it moved one line, `281->280`. **The
error arm is gone from the missing-lines list entirely.** Lines 703-707 at
`1c54ebc` were `get_job_feed`'s `except` body (`git show
1c54ebc:src/fast_mcp_jobvite/tools/jobs.py`), and at `280b689` that arm reads
100% covered.

**It was not fixed. It was walked through.**
`test_case2_a_jobfeed_transport_failure_carries_no_secret_to_the_caller`
(`tests/test_tools_job_feed.py:372`) drives a failing feed call through the arm
on its way to a redaction claim, asserts `result.is_error` at `:425`, and then
measures the secret. That is the whole of what it set out to do, and it is done
well. It means the arm is EXECUTED by every run and the row it writes is checked
by nobody: `grep -rn result_status tests/` finds assertions for `search_jobs`
(`test_tools_jobs.py:354`) and for `get_candidate` (`test_tools_candidates.py:1661`)
and none for `get_job_feed`.

**Measured, not argued.** With `event.result_status = "error"` deleted from
`get_job_feed` and NOTHING else, the entire pre-existing suite - my two new cases
deselected - passed:

```
863 passed, 8 deselected in 50.12s
EXIT: 0
```

So the second gap was never a coverage gap by the time it reached me. It was a
100%-covered line with no assertion behind it, which is the shape that no line
number, no floor and no coverage report can express. Had I chased the missing-lines
list I would have reported "already fixed" and closed the task.

---

## 2. Per branch: the test, and the amputation proving it can fail

Both rows below were run by `scripts/check-critical-coverage-amputation.sh`,
which deletes the behaviour and reports the exit code and the NAME of every test
that died. A count cannot tell a row that went red for its own reason from one
that went red for an unrelated one.

### Gap 1 - `tools/jobs.py:279-284`, the registration credential guard (branch `279->280`)

`_register_search_jobs` raises rather than registering `search_jobs` against
credentials that are not there. `validate_settings` refuses the same
configuration at boot, so the guard's only remaining caller is a path where the
boot check was bypassed - a test, a library consumer calling `register`
directly, or a future `build_server` that stops calling `validate_settings`.

- **Test:** `test_registering_search_jobs_without_credentials_refuses`,
  `tests/test_tools_jobs.py:765`. Transferred from #94's candidates case, with
  one addition. It asserts the message NAMES `search_jobs` (a bare
  `pytest.raises(ValueError)` passes against an unrelated `ValueError`) and
  names `validate_settings`; it asserts `validate_settings` still refuses the
  same configuration, so the first line of defence is asserted rather than
  assumed; and it registers WITH credentials as the positive control, so the
  case is not satisfied by a `register` that refuses everything.
- **THE ADDITION: both halves of the disjunction, separately.** The guard is
  `api_key is None or api_secret is None`. A case supplying NEITHER credential
  is satisfied by a guard that reads only the first, so the test also drives a
  configuration holding only `api_key` and one holding only `api_secret`.
- **Amputation A16** (the whole guard deleted): kills that test.
- **Amputation A18** (`or settings.api_secret is None` removed, so the guard
  reads half its pair): kills that test. This is the row that justifies the
  addition - a deployment holding a key and no secret would register the tool,
  and A16 alone cannot distinguish a correct guard from a half one.

### Gap 2 - `tools/jobs.py:700-708`, the feed read's error arm

- **Test:** `test_a_job_feed_read_error_is_a_problem_object_and_an_audit_row`,
  `tests/test_tools_job_feed.py:985`. Two claims, not one: the caller gets a
  problem object rather than a raise (`is_error`, `status == 502`), **and** the
  audit row records `result_status == "error"`. The audit stream is the real
  loguru one the `log_records` fixture captures, and the case asserts there is
  exactly ONE audit event before reading it.
- **Amputation A17** (`event.result_status = "error"` deleted and nothing else):
  kills that test, and only that test. This is A11's shape one module over: it
  proves the AUDIT assertion specifically rather than the error arm generally.
  §1 records the same amputation surviving the whole suite before the case existed.

### Harness result

```
########## ROWS: 18   ANCHORS APPLIED: 18
########## TOTAL SURVIVING ASSERTIONS: 3540
########## VACUOUS ROWS: 1 (declared survivors included)
########## UNDECLARED VACUOUS ROWS: 0
```

Exit 0. The one declared vacuous row is still A1, #94's defensive
no-request-context guard; my three rows all went red, each naming exactly the
case written for it:

```
########## A16 the search_jobs registration credential guard is deleted
  1 failed, 198 passed
  killed: tests/test_tools_jobs.py::test_registering_search_jobs_without_credentials_refuses

########## A17 a failed feed read is audited as a success
  1 failed, 198 passed
  killed: tests/test_tools_job_feed.py::test_a_job_feed_read_error_is_a_problem_object_and_an_audit_row

########## A18 the registration guard reads only half its credential pair
  1 failed, 198 passed
  killed: tests/test_tools_jobs.py::test_registering_search_jobs_without_credentials_refuses
```

`SUITE` in the harness gained `tests/test_tools_jobs.py` and
`tests/test_tools_job_feed.py`, and `$JOBS` was added to the pristine-copy loop
so a failed restore of it stops the run like any other file.

**A17's anchor carries the preceding `result = build_feed_result(...)` line**,
because `except Exception as exc:` and `event.result_status = "error"` each
appear TWICE in this module - once per tool. The harness refuses a non-unique
anchor rather than applying it to the first hit, which would have amputated
`search_jobs`' audit row and produced a plausible wrong verdict.

---

## 3. Coverage, before and after

`uv run --frozen pytest --cov --cov-report=json`, on this branch:

| | line | branch | missing lines | missing branches |
|---|---|---|---|---|
| before (`280b689`) | 97.44% | 91.67% (11/12) | `[280, 284]` | `[[279, 280]]` |
| after | **100.00%** | **100.00%** (12/12) | `[]` | `[]` |

Overall coverage 96.85% -> 97.00%. `docs/reviews/check-coverage-floors.py` exits
0 both before and after, and would have exited 0 for ever - `tools/jobs.py` is
not on `DESIGN.md:1364`'s critical-path list, so ADR-0010 gives it the 85% tool
floor. **That is not a defect in the checker.** It enforces what ADR-0010 sets.
It is a module whose floor is loose enough to hide a known-shape gap, and the
amputation rows are the only instrument that sees the OTHER gap at all, since
that one was at 100%.

---

## 4. THE ROW FLOOR, AND THE FLOORS I DID NOT TYPE

`ROW_FLOOR` in `scripts/check-critical-coverage-amputation.sh` raised **15 ->
18**, read off the run's own `########## ROWS: 18` line, not by adding 3 to 15.
The comment above it now says so and says the previous value.

Floors derived by grep from `.github/workflows/ci.yml`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 863
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 453
```

Measured on this branch:

```
$ uv run --frozen pytest | ... | bash scripts/check-suite-floor.sh 863
865 passed, 6 deselected in 49.94s
suite floor OK: 865 passed, floor 863

$ python3 scripts/check-harness-anchors.py --self-check --floor 453
harnesses scanned: 33
anchors resolved: 456
OK: all 456 anchors resolve to exactly one hit in their target file (floor 453).
```

**865 passed, 6 deselected, 0 skipped.** The word "skipped" does not appear in
the summary line, and 863 + 2 new cases = 865 accounts for the delta exactly.

---

## 5. THE CONTAINER, ENUMERATED - AND TWO SITES NOTHING ASSERTS

### The credential-guard shape: three guards, three covered

The orchestrator's addendum enumerated this one so I did not have to, and I
re-verified its two claims rather than carrying them:

- `src/fast_mcp_jobvite/tools/` holds exactly `jobs.py` and `candidates.py` -
  no third tool module: `ls src/fast_mcp_jobvite/tools/`.
- `grep -rn 'credentials are unset' src/` gives THREE raise sites:
  `candidates.py:566` (closed by #94), `jobs.py:281` (closed here), and
  `jobs.py:614`, the `get_job_feed` guard, covered by
  `tests/test_tools_job_feed.py:574`
  `test_registering_the_feed_without_its_credentials_refuses_at_boot`, which I
  read rather than inferring from coverage's silence.

**Three guards, three covered.** The container is closed.

### The audit-row shape: SIX sites, and TWO of them are asserted by nothing

The addendum enumerated the guards. Nobody had enumerated the OTHER shape this
task closes, so I did - because a sweep that stops where the first two instances
happened to be is the exact failure this task exists to prevent.

`grep -rn 'result_status = "error"' src/` gives SIX sites. Each was deleted one
at a time and the WHOLE suite run. The probe is committed at
`docs/reviews/probe-audit-row-container.sh` - runnable, deriving its own
population, refusing a non-unique anchor, and asserting `git diff --quiet -- src/`
at the end. Its output, verbatim, on this branch AFTER my fix:

```
jobs.py search_jobs                      exit 1  1 failed, 864 passed, 6 deselected
jobs.py get_job_feed                     exit 1  1 failed, 864 passed, 6 deselected
candidates.py search_candidates          exit 0  865 passed, 6 deselected
    *** VACUOUS: the failure is recorded by nobody ***
candidates.py get_candidate              exit 1  1 failed, 864 passed, 6 deselected
candidates.py approval refusal           exit 1  1 failed, 864 passed, 6 deselected
candidates.py create_candidate           exit 0  865 passed, 6 deselected
    *** VACUOUS: the failure is recorded by nobody ***

ROWS: 6   APPLIED: 6   VACUOUS: 2
TREE RESTORED CLEAN
```

`jobs.py get_job_feed` reads exit 1 there because this branch fixed it; §1
records its exit 0 before the case existed.

**Both survivors are in `tools/candidates.py`, which measures 100.00% line AND
100.00% branch and sits on `DESIGN.md:1364`'s critical-path list at the 95/90
floors.** `candidates.py:806` is `create_candidate` - the WRITE - on a path
where the write may or may not have landed, so a failed or ambiguous create is
recorded as a success. Both arms are executed on every run by cases that assert
the caller-visible half and never read the audit row.

**Filed as task #101 with the measured shape of the fix, and deliberately NOT
fixed here** - fix one instance, check its siblings, report the sibling rather
than silently widening scope into a module this task does not name.

---

## 6. GATES, each by exit code on its own line

```
uv run --frozen mypy                                        EXIT 0   Success: no issues found in 62 source files
uv run --frozen ruff check .                                EXIT 0   All checks passed!
uv run --frozen ruff format --check .                       EXIT 0   76 files already formatted
uv run --frozen pytest                                      EXIT 0   865 passed, 6 deselected  (0 skipped)
bash scripts/check-suite-floor.sh 863   (fed real output)   EXIT 0   suite floor OK: 865 passed, floor 863
python3 docs/reviews/check-coverage-floors.py               EXIT 0   Every declared role matches the design, and every floor holds.
python3 docs/reviews/check-row-floors.py                    EXIT 0   Harnesses: 32, not referenced by ci.yml at all: 0
python3 scripts/check-harness-anchors.py --self-check --floor 453   EXIT 0   456 anchors resolve
python3 docs/reviews/check-obligations.py                   EXIT 0   Every mapped anchor still contains its subject. OK.
pre-commit run shellcheck (both changed/new .sh files)      EXIT 0   ShellCheck v0.10.0 Passed
bash scripts/check-critical-coverage-amputation.sh          EXIT 0   18/18 applied, 0 undeclared vacuous
bash docs/reviews/probe-audit-row-container.sh              EXIT 0   6/6 applied, 2 vacuous (reported, §5)
```

**`uv run --frozen mypy`, not `mypy src`** - `ci.yml:422` is the authority.
`check-row-floors.py` still reports 32 harnesses with 0 unwired: the new probe
lives in `docs/reviews/` and is deliberately NOT named `check-*-amputation.sh`,
so it does not enter that checker's `FAMILIES` glob and cannot make the gate red
for lack of a `ci.yml` step it does not need.

**mypy and ruff both caught my first draft**, and both findings were in the test
I wrote: `Settings(tools=SEARCH_JOBS, **{present: value})` is five `arg-type`
errors under mypy (the loop now builds each `Settings` explicitly), and the
docstring's first line was W505 at 76 > 72. Both fixed before anything was
committed.

---

## 7. WHAT `ci.yml` NEEDS FROM ME - AND I RAN IT

`ci.yml` is the orchestrator's file. Three numbers move, and per the PREAMBLE's
new section I ran the one step that is runnable rather than handing over a form
I had only reasoned about.

**1. The harness step's `--min-rows`, `ci.yml:777-778`: 15 -> 18.** The step
itself is unchanged in every other respect - the deliberate absence of
`--amputation` is preserved, and the reason for it still holds.

```yaml
      - name: Critical-path coverage amputation, every row applied
        run: |
          bash scripts/ci-harness-gate.sh check-critical-coverage-amputation.sh \
            --anchors-applied --min-rows 18 --row-re '^########## A[0-9]+ '
```

RUN VERBATIM FROM THIS WORKTREE:

```
GATE EXIT: 0
########## ROWS: 18   ANCHORS APPLIED: 18
########## VACUOUS ROWS: 1 (declared survivors included)
########## UNDECLARED VACUOUS ROWS: 0
```

And the regex checked against the harness's REAL output, not against its source
- a regex matching nothing looks identical to a harness that ran nothing:

```
$ grep -cE '^########## A[0-9]+ ' /tmp/harness-out.txt
18
```

**2. The suite floor, `ci.yml:446`: 863 -> 865.** Two cases added, and
`check-suite-floor.sh 863` already passes at 865, so this is a ratchet, not a
repair.

**3. The anchor floor, `ci.yml`'s `--self-check --floor`: 453 -> 456.** Three
new amputation rows, three new anchors; the self-check already passes at 453.

Both 2 and 3 are ratchets that hold un-raised, so nothing is red if they are
raised in a later commit - but a floor left below the measurement is a floor
that stops noticing the next deletion.

---

## 8. Findings, each with a suggested fix

**F1 (High) - two audit-failure rows in `tools/candidates.py` are asserted by
nothing, one of them on the write.** §5. Filed as task #101 with the fix shape.
Suggested fix, repeated here: add `assert event["result_status"] == "error"` to
the case that already drives each arm, and add two A11-shaped rows to the
amputation harness with anchors made unique by the preceding `result = ...`
line.

**F2 (Medium) - a 100%-covered line can have no assertion behind it, and this
repository's coverage gate is structurally unable to say so.** The `get_job_feed`
arm was at 100% line coverage with its audit row unasserted, and would have
stayed there. Suggested fix: nothing to change in
`check-coverage-floors.py` - coverage is the wrong instrument for this question
and adding a rule to it would be a second copy of the amputation harness's job.
The remedy that fits the repository's grain is the one taken here: a harness row
per behaviour that matters, and `docs/reviews/probe-audit-row-container.sh` as
the pattern for enumerating a SHAPE across the package rather than a file.
If it is wanted as a gate rather than a probe, the change is to make it exit 1
on a vacuous row and give it a `ci.yml` step - but that should follow #101, not
precede it, because it is red today.

**F3 (nit) - the brief's line numbers were three commits stale and one of its two
gaps had changed KIND, not just position.** Suggested fix: this is already
PREAMBLE policy ("a retyped constant decays"), and it worked - the brief told me
to re-measure and I did. Worth recording only because the re-measurement did not
merely shift a number, it changed what the task was: chasing the missing-lines
list would have closed #97 as "already fixed" with the real defect still in the
tree.

---

## 9. WHAT I COULD NOT SETTLE

This list is for what I could not settle, not what I did not try.

1. **The `ci.yml` step numbers 2 and 3 (suite floor, anchor floor) are
   unverified AS `ci.yml` EDITS.** I ran both underlying commands from this
   worktree at their new values' measurements - `check-suite-floor.sh 863`
   against the real 865 output, and the anchor self-check resolving 456 against
   a floor of 453 - so the numbers are measured. What I cannot run is a workflow
   step in a file I must not edit. Step 1 I ran verbatim, because
   `ci-harness-gate.sh` takes a bare harness name and needs no wired `ci.yml`.
2. **Whether `tools/jobs.py` should be on `DESIGN.md:1364`'s critical-path list
   at all.** It is now at 100/100 either way, so the question is not urgent, but
   the module registers both read tools and the answer is a design decision
   behind a numbered ADR, not a working-tree edit. Not filed as a task because
   I do not think it needs one until the module drops below 95.
3. **Whether the two vacuous rows in `candidates.py` have other siblings one
   level up.** I enumerated `result_status = "error"` across `src/` and every
   site is in `tools/`. I did NOT sweep the analogous question for
   `AuditPhase`, `emit(...)` call sites, or the `is_error=True` flag - each is a
   different shape with its own container, and asserting they are clean after
   two greps would be a claim about where I looked. Task #101 covers the shape
   I measured; the others are unmeasured, and I am saying so rather than
   implying they were checked.

---

## 10. Housekeeping

- Worktree `/tmp/jobs-gaps-work` removed after this report was committed.
- Nothing merged, nothing pushed. Branch `fix/jobs-gaps` on `280b689`.
- `docs/OBLIGATIONS.md` not touched, and `check-obligations.py` exits 0 with
  "Mappings: 31 | anchors verified against their subject: 25 | recorded as
  absent: 6" - no anchor of mine moved one.
