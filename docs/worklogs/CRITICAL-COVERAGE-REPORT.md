# CRITICAL-COVERAGE - task #94

Branch `fix/critical-coverage`, based at `a44ce90`. Not merged, not pushed.
Worktree `/tmp/critical-coverage-work`, removed after this report was committed.

Every number below was copied from a terminal on this branch, not predicted.

---

## 1. The measurement, re-taken

The brief's figures were taken at `708cbb2` and the tree had moved. Mine, from
`uv run --frozen pytest --cov --cov-report=json` at `a44ce90`:

| module | role | line | branch | verdict |
|---|---|---|---|---|
| `http_hardening.py` | auth | 100.00% | 100.00% | OK |
| `utils/constraints.py` | argument rejection | 100.00% | 100.00% | OK |
| `errors.py` | the error rule | 100.00% | 100.00% | OK |
| `approval.py` | approval | **96.10%** | **78.57%** | BELOW on branch |
| `tools/candidates.py` | the write | **94.04%** | **80.77%** | BELOW on both |

**The brief said `approval.py` was 93.4% line; it is 96.10%.** The tree moved
between the brief and the dispatch, which is exactly what the brief warned would
happen. Its branch figures were exact, and the branch gap is the real one:
`approval.py` clears the 95% line floor and misses the 90% branch floor by
eleven points.

Uncovered branches, from my own run rather than the brief's list:

```
approval.py           281->282, 311->313, 337->338
tools/candidates.py   487->488, 557->558, 567->575, 855->858, 856->855
                      (and lines 684-687, missing entirely)
```

Final state, same command on `1c54ebc`:

```
approval.py              100.00 line  100.00 branch
tools/candidates.py      100.00 line  100.00 branch
http_hardening.py        100.00 line  100.00 branch
utils/constraints.py     100.00 line  100.00 branch
errors.py                100.00 line  100.00 branch
```

`831 passed, 6 deselected` - **0 skipped**. Overall 96.71% line.

---

## 2. Per branch: what it does, its test, and the amputation that kills it

Every row below was run by `scripts/check-critical-coverage-amputation.sh`,
which deletes the behaviour and reports the exit code of the run. It names the
test each row **killed**, not only a count: a row can go red for a reason
unrelated to the branch and a count cannot tell the two apart.

### `approval.py:281->282` - no request context

`observed_protocol_version` returns `None` when `ctx.request_context` is `None`,
which lands in the third case: the era cannot be identified, so nothing
authorises the write.

- **Test:** `test_a_context_with_no_request_context_refuses`. Asserts the whole
  published decision (ADR-0033's vocabulary) - `approved False`, mechanism
  `NO_HANDLER`, state `UNAVAILABLE`, version `None` - not just `approved`.
- **Amputation A1** (the guard deleted): **SURVIVOR.** See §3; this is a finding
  about the source.
- **Amputation A2** (`version = observed_protocol_version(ctx)` replaced by a
  literal era): kills 20 tests including this one. This is the row that proves
  the case can fail.

### `approval.py:311->313` - an unreadable answer container

`_answer_for` accepts a `Mapping` or a pydantic `RootModel`. A third shape must
refuse rather than authorise a write out of a container the server cannot read.

- **Test:** `test_an_input_responses_container_of_an_unreadable_shape_refuses`,
  with a list as the container, plus a positive control in the same test that
  the readable shape still approves.
- **Amputation A3** (type guard deleted, `.get` taken off whatever arrived):
  kills that test.

### `approval.py:337->338` - `content` that is not a dict

An accepted response whose `content` is a JSON string. Without the guard the
`.get` raises inside the write path, and an exception on the approval leg is not
a refusal.

- **Test:** `test_an_accepted_response_whose_content_is_not_a_dict_refuses`, with
  the dict form as its positive control. `action` is `accept` throughout, because
  any other action refuses on the first half of the conjunction and never reaches
  this arm.
- **Amputation A4** (shape guard deleted): kills that test.

### `tools/candidates.py:487->488` - `_int_or_none`

`bool` is a subclass of `int`, so `epoch_ms_to_date(True)` would date an
application to 1970-01-01 in a record a recruiter reads. A string would raise
inside a **read**, which is the recoverable operation.

- **Test:** `test_a_date_field_arriving_as_a_non_integer_becomes_none` - bool arm,
  string arm, and a genuine epoch as the positive control.
- **Amputation A5** (normaliser passes everything through): kills it.
- **Amputation A6** (only the `bool` exclusion removed): kills it. The narrower
  row and the more important one - A6 looks correct and produces a wrong date
  with an explanation, which is worse than an absent one.

### `tools/candidates.py:557->558` - the registration credential guard

`register` raises rather than registering three tools against credentials that
are not there.

- **Test:** `test_registering_the_candidate_tools_without_credentials_refuses`.
  Asserts the message names the enabled tools (a bare `pytest.raises(ValueError)`
  would pass against an unrelated `ValueError`), carries `validate_settings`
  refusing the same configuration as the first line of defence, and registers
  successfully with credentials as the positive control.
- **Amputation A7** (guard deleted): kills it.

### `tools/candidates.py:567->575` - the default client factory

`client_factory=None` is the branch every other case in the file skips by
supplying its own factory. This is where U6-F1 (`max_results` omitted) and R5-M1
(`start_base_overrides` omitted) both lived in `tools/jobs.py` - the same defect
twice in one argument list - and this module has the identical factory with no
case reaching it.

- **Test:** `test_the_default_client_factory_is_built_from_the_settings`.
  `start_base_overrides` is asserted through `scan_start()`, because a keyword
  assertion passes against a client that ignores what it was handed; a silence
  arm asserts an unset base leaves `scan_start` at 0. `max_results` and
  `company_id` have no public reader on the client and are asserted on the
  argument list - the weaker claim, said plainly in the docstring.
- **Amputation A8** (`max_results` dropped): kills it.
- **Amputation A9** (`start_base_overrides` dropped): kills it.

### `tools/candidates.py:855->858` and `856->855` - `_one_record`

The route answers with a PAGE even when asked for one record, and
`JOBVITE-CONTRACT.md:161` records that the record-level "not found" shape is
unknown. So the reader walks rather than indexes, and an exhausted walk yields an
empty `Candidate` rather than an invented error.

- **Test:** `test_get_candidate_skips_a_non_record_and_falls_back_to_an_empty_one`,
  end to end through the tool. Arm one is a page whose first element is a string
  and whose second is the record - the surviving record is the positive control.
  Arm two is a page with no object in it at all.
- **Amputation A10** (walk becomes `to_candidate(items[0])`): kills it.

### `tools/candidates.py:684-687` - the untested error arm

Not a branch gap - four consecutive **lines** with no case at all, while the
sibling tool `search_candidates` had one. Found by reading the missing-lines list
rather than the missing-branches list.

- **Test:** `test_a_get_candidate_read_error_is_a_problem_object_and_an_audit_row`.
  Two claims: the caller gets a problem object rather than a raise, **and** the
  audit row records `result_status == "error"`. A read that fails and is written
  down as a success is a record that lies, and the row is the only evidence
  anyone has afterwards.
- **Amputation A11** (`event.result_status = "error"` deleted): kills it. A case
  asserting `is_error` alone would not have seen this row.

### Harness result

```
########## ROWS: 15   ANCHORS APPLIED: 15
########## TOTAL SURVIVING ASSERTIONS: 1795
########## VACUOUS ROWS: 1 (declared survivors included)
########## UNDECLARED VACUOUS ROWS: 0
```

Exit 0. Three anchors did not apply on the first run and were fixed rather than
dropped: two on indentation, and A11 because `except Exception as exc:` appears
three times in the module - the harness refuses a non-unique anchor rather than
applying it to the first hit, which would have amputated a different tool's audit
row and produced a plausible wrong result.

---

## 3. The one surviving amputation, and why it is not a `# pragma`

**A1: `approval.py:281-282`, `if request_context is None: return None`.**

Deleting it changes nothing an approval caller can observe, because
`getattr(None, "protocol_version", None)` is also `None`. The guard is
**defensive rather than load-bearing**.

This is *not* the "unreachable branch" case the brief asked me to look for. The
branch is reached on every call where `ctx.request_context` is `None`, so
`# pragma: no cover` would be a false claim about reachability, and deleting the
guard would leave the module reading an attribute off `None` by accident rather
than by decision. I left it, covered it, and declared its survival in the
harness header - so the vacuous gate still means something for the other
fourteen rows.

**Suggested fix (not applied - it is a source change outside this task's remit
and wants a reviewer's eye):** either drop the guard and let the `getattr` handle
it, with a comment saying that is deliberate, or keep it and make it
load-bearing by raising rather than returning `None`, so a missing request
context is distinguishable from a context carrying no version. The two cases are
currently indistinguishable in the decision, in the log line, and in the audit
row. I did not change it because both options change behaviour that
`test_an_absent_protocol_version_refuses` already pins.

**No branch anywhere in either module was judged unreachable.** All eight were
reachable and all eight now have a test that dies when the behaviour is deleted.

---

## 4. The checker

`docs/reviews/check-coverage-floors.py`, over `coverage json`.

**Both the floors and the module list are derived, not typed.**

- The floors are parsed out of `DESIGN.md`'s coverage sentence (`:1362-1364`),
  all six of them: overall 80, tool modules 85, the Jobvite client 90, `utils/`
  95, critical paths 95 line and 90 branch. A number written into the checker
  would be a second copy of ADR-0010's decision.
- The critical-path **roles** come from the same sentence's parenthesis.
- **The role-to-module map is not in the checker.** The design names roles, not
  paths. Each module declares its own `COVERAGE_ROLE`, and the checker walks the
  package with `rglob` and asserts the declared set **equals** the design's set,
  in both directions. A checker with a hand-kept list of what it checks is the
  container defect this project has found eight times.

Six modules gained one line: `auth`, `argument rejection`, `the error rule`,
`approval`, `the write`, and `the Jobvite client`.

Its output on this branch:

```
FLOORS, derived from DESIGN.md's coverage sentence:
  overall              80%
  tool modules         85%
  the Jobvite client   90%
  utils/               95%
  critical line        95%
  critical branch      90%

MODULE                                          ROLE                      LINE  FLOOR   BRANCH  FLOOR
src/fast_mcp_jobvite/approval.py                approval               100.00%    95%  100.00%    90%
src/fast_mcp_jobvite/errors.py                  the error rule         100.00%    95%  100.00%    90%
src/fast_mcp_jobvite/http_hardening.py          auth                   100.00%    95%  100.00%    90%
src/fast_mcp_jobvite/services/jobvite_client.py the Jobvite client      98.72%    90%   96.94%      -
src/fast_mcp_jobvite/tools/candidates.py        the write              100.00%    95%  100.00%    90%
src/fast_mcp_jobvite/tools/jobs.py              tool module             93.33%    85%   91.67%      -
src/fast_mcp_jobvite/utils/constraints.py       argument rejection     100.00%    95%  100.00%    90%
src/fast_mcp_jobvite/utils/correlation.py       utils/                 100.00%    95%  100.00%      -
src/fast_mcp_jobvite/utils/normalise.py         utils/                 100.00%    95%  100.00%      -
src/fast_mcp_jobvite/utils/redaction.py         utils/                 100.00%    95%  100.00%      -

Overall: 96.71% line against a 80% floor

Every declared role matches the design, and every floor holds.
```

Exit 0.

### Its controls, and the one that had to be added

`tests/test_coverage_floors.py` runs the checker as a **subprocess** and reads
its exit code, against a synthetic design and a synthetic package driven through
new `--design` and `--package` flags. Not a `--self-check`: a self-test checks
the side of the boundary its author had in mind, measured on this codebase where
three of four mutants survived one and all three were killed by an independent
test.

Ten refusal arms - under floor on line, under floor on branch, a role no module
claims, a role the design does not name, two modules claiming one role, an
unparseable design sentence, an empty report, a missing report, and each of the
two directory families - plus a positive control, because a checker that exited
1 unconditionally would satisfy all ten and enforce nothing.

**And the harness found that ten of them were not enough.** Amputation row A15
replaced the parsed floors with ADR-0010's numbers hard-coded into the checker -
the exact defect its own docstring claims to avoid - and **every control stayed
green**. The row was VACUOUS. The reason is structural: a stricter typed-in floor
refuses everything a looser derived one refuses, so no refusal case can tell them
apart. The eleventh control asserts the checker **prints** the synthetic
design's floors, and that a module sitting *between* the synthetic floor and
ADR-0010's floor **passes**. A15 now dies to exactly that case.

This is the report's most useful line: ten controls, written carefully, could not
see a second copy of a constant. Only deleting the derivation showed it.

### Wiring

**NOT WIRED, and this is the one thing left undone.** `ci.yml` is the
orchestrator's file. Two problems, and the second is a hard coupling:

1. The checker itself needs a step (below).
2. `docs/reviews/check-row-floors.py` reports **any** harness `ci.yml` does not
   mention as `UNWIRED` and exits 1. So `scripts/check-critical-coverage-amputation.sh`
   makes that gate red the moment it lands, and **the harness and its step must
   land in the same commit**. This is the same coupling task #96 hit.

`python3 docs/reviews/check-row-floors.py` on this branch, verbatim:

```
Harnesses: 30
  not referenced by ci.yml at all : 1
  wired but no floor at either layer: 0
    UNWIRED  check-critical-coverage-amputation.sh
```

Everything else on this branch is green. Filed as **task #98** with the same
steps. **The steps you need:**

```yaml
      # The Coverage step already runs `pytest --cov`; add the json report so
      # the floors checker has something to read. The floor still lives in
      # pyproject.toml alone - no `--cov-fail-under` here.
      - name: Coverage
        run: uv run --frozen pytest --cov --cov-report=term-missing --cov-report=json

      # ADR-0010's PER-MODULE floors, which `fail_under` cannot express. It is
      # 80 and the suite measures 96%, so two critical paths sat ten points
      # under their own floor with every gate green (#94). Both the floors and
      # the critical-path list are parsed out of DESIGN.md, so this step has no
      # number in it and cannot go stale. Depends on the json report above.
      - name: ADR-0010's per-module coverage floors hold
        run: |
          set -uo pipefail
          out=$(python3 docs/reviews/check-coverage-floors.py 2>&1); rc=$?
          echo "$out"
          if [ "$rc" -ne 0 ]; then
            echo "::error::a module is under its ADR-0010 floor, or a declared role does not match the design"
            exit 1
          fi

      # #94's amputation harness. --min-rows 15, DERIVED from the run recorded
      # in docs/worklogs/CRITICAL-COVERAGE-REPORT.md (15/15 applied, exit 0).
      # It also carries an internal ROW_FLOOR=15, so it is floored at both
      # layers; check-row-floors.py needs only one, and needs ci.yml to MENTION
      # the harness at all, which is what this step supplies.
      - name: Critical-path amputations, all rows applied
        run: bash scripts/ci-harness-gate.sh scripts/check-critical-coverage-amputation.sh --min-rows 15
```

I did not verify that `ci-harness-gate.sh` parses this harness's summary lines,
because I could not run the gate against a wired `ci.yml` without editing it.
Task #96's report records that its own suggested steps were wrong twice; treat
these the same way and run them before trusting them. The harness's summary
format is copied from `check-u14-arguments-amputation.sh`, which that gate
already drives, with two lines added (`UNDECLARED VACUOUS ROWS`, and the `killed:`
list).

The **suite floor** in this branch's `ci.yml` reads 810 and this branch measures
**831**. `main` has since moved to 831 independently (#96), so after a merge the
floor is the merged count, not either of these - derive it from the merged tree,
do not copy 831 out of this paragraph.

The **anchor floor** in this branch's `ci.yml` reads 421 and this branch resolves
**436**. `main` is at 438 per #96, which is higher than my 436 because my base
predates #81. After a merge the count is the sum, not mine.

---

## 5. Also done

- `pyproject.toml`'s coverage comment is **rewritten in place**, not annotated.
  It no longer claims the per-module floors are "enforced by the units that
  create those modules" (they are now enforced by the checker), it no longer
  repeats ADR-0010's numbers, and it no longer carries `"measured at 92.66% over
  552 statements"` - a measurement that had gone stale by a factor of nearly
  three in its statement count. It says to run the checker instead.
- `.gitignore` gained `coverage.json`. It listed `coverage.xml` and not the json
  form, and the checker makes a json report on every run. An artefact list beside
  a tool is blind to the format nobody added.

---

## 6. Findings, each with a suggested fix

**F1 (Medium) - `approval.py`'s no-request-context guard is inoperative.**
Covered in §3. Suggested fix there; not applied.

**F2 (Medium) - `tools/jobs.py` has the same two gaps this task closed in
`tools/candidates.py`, and is not on any critical path so nothing will catch
them.** Measured on this branch: `tools/jobs.py` is 93.33% line / 91.67% branch,
missing lines `[281, 285, 703-707]` and missing branch `280->281`. `281-285` is
the identical credential guard I covered at `candidates.py:557-562` and `280->281`
is its branch; `703-707` is the identical error arm I covered at
`candidates.py:684-687`. It clears its 85% tool-module floor, so the new checker
passes it and always will. *Fix one instance, check its siblings* - I fixed one
and am reporting the sibling rather than silently widening scope. **Suggested
fix:** the two cases I wrote transfer almost verbatim, and `test_tools_jobs.py`
already has the `monkeypatch`/`recording` pattern the factory case needs. Filed
as task #97.

**F3 (Low) - `config.py` and `models/fencing.py` are governed by no floor but
the 80% aggregate.** Measured: `config.py` 91.54% line / 86.84% branch,
`models/fencing.py` 96.83% / 94.44%. Neither is a critical path, neither is under
`utils/` or `tools/`, and neither declares a `COVERAGE_ROLE`, so the checker
prints no row for either. That is honest rather than hidden - the checker
enforces what ADR-0010 sets and nothing it invents - but `config.py` is the
module that decides what the server will and will not start with, and 86.84%
branch is the lowest branch figure in the package outside `__main__.py`.
**Suggested fix:** if ADR-0010 intends a floor there, it is an ADR amendment plus
a `COVERAGE_ROLE` line, not a rule added to the checker. Not filed as a task - it
is a design question for the orchestrator, not a defect.

**F4 (Nit) - the checker's directory families are matched on `"/tools/" in rel`.**
A module at `src/fast_mcp_jobvite/tools.py` (no directory) would get no floor, and
a hypothetical `src/fast_mcp_jobvite/vendor/tools/x.py` would get one. Neither
exists today. **Suggested fix:** match on `pathlib.PurePath(rel).parts` against
the package-relative parent, which is exact. Left as written because the current
form is readable and the failure needs a directory layout this package does not
have; recorded so the next reader does not have to re-derive it.

---

## 7. What I could NOT settle

- **Whether the three `ci.yml` steps in §4 actually work.** I could not run them:
  editing `ci.yml` is out of scope for this task and `ci-harness-gate.sh` reads a
  wired workflow. Task #96's report had its suggested steps wrong twice. Run them
  before trusting them.
- **Whether `ci-harness-gate.sh` parses this harness's output.** Same reason. Its
  summary block matches `check-u14-arguments-amputation.sh`'s, which that gate
  drives today, but "same shape" is an argument and not a measurement - which is
  the standing complaint in task #91 about nine row floors nobody has watched
  fire. Mine has been watched fire in one direction only: I saw A15 go vacuous and
  the harness exit 1 because of it, so the `UNDECLARED VACUOUS` gate is proven.
  The `ROWS -lt ROW_FLOOR` gate is **not** proven - I never deleted a row and
  watched the floor catch it.
- **Whether the merged anchor and suite floors are right.** My branch is based at
  `a44ce90` and `main` has moved twice since (#81, #96). Both floors must be
  re-derived from the merged tree; §4 says so and deliberately does not name a
  number to copy.
- **Whether `COVERAGE_ROLE` is the right mechanism.** It puts a testing concern
  into six production modules. I judged that better than a role-to-path map inside
  the checker, because that map is the container defect this project keeps
  finding - but it is a judgement, not a measurement, and it is the design
  decision here most worth a second opinion.
- **Whether `tools/jobs.py`'s two gaps are the ONLY siblings.** I checked the
  two modules ADR-0010 puts on the tool-module floor and the module I was sent
  for. I did not sweep the package for every other guard of the same shape, so
  "these are the siblings" is a claim about where I looked: `tools/jobs.py`,
  `tools/job_feed.py` (100%, nothing to find) and `tools/candidates.py`.
