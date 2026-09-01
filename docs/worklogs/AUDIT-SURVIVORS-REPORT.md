# AUDIT-SURVIVORS (#127, #128, #129) - the fourteen survivors, killed and measured

Branch `fix/audit-survivors`, worktree
`/home/plafayette/claude_projects/fmj-worktrees/audit-survivors`, base `92cb89b`.
Commits: `c5dc463` (the tests), and this report.
**Not merged, not pushed, not rebased.**

**Headline.** All fourteen rows the sweep left VACUOUS are now killed: the twelve
`AuditPhase` rotations (#129) and the two `emit(...)` amputations (#127, #128). One new test
module does it, `tests/test_audit_phase_sites.py`, 14 tests, suite **873 -> 887, 0 skipped**.
Every kill is measured by re-running `docs/reviews/probe-audit-shape-container.py` against that
site and reading its exit code, per site, before and after.

**And the sweep's open question is settled: `candidates.py:832` is NOT a third `emit` survivor.**
Measured with the operator #130's report proposed and never ran. §5.

**No phase is wrong in the code.** I read all fifteen against DESIGN.md and they are correct
today. This closes the absence of a guard, not a live defect. Nothing here is a Critical.

---

## 1. THE BEFORE STATE, RE-MEASURED AT MY BASE - not inherited from the sweep

`AUDIT-SHAPES-REPORT.md` measured at `dad014e`. My base is `92cb89b`, so every survivor was
re-measured here rather than carried over. Baseline first:
`873 passed, 6 deselected in 75.43s`, **0 skipped**, matching `ci.yml`'s floor derived by grep
(`check-suite-floor.sh 873`).

Full `--shape audit_phase` sweep (15 of 15 rows) and a targeted `--shape emit` run over the two
survivors, both exit 0, both ending `TREE RESTORED CLEAN UNDER src/ AND tests/`:

| shape | POPULATION | ROWS | APPLIED | VACUOUS |
|---|---|---|---|---|
| `audit_phase` | 15 | 15 | 15 | **12** |
| `emit` (2 selected of 13) | 13 | 2 | 2 | **2** |

The fourteen survivors and the three kills reproduce the sweep's §3.3 exactly, at a different
SHA and 5 tests later. Nothing had drifted.

---

## 2. WHAT I BUILT, AND WHY IT IS NOT A ROW-EXISTS TEST

`tests/test_audit_phase_sites.py`. Three mechanisms, all in one file:

1. **A phase spy over the ORDERED sequence.** A fixture wraps `emit` in
   `tools/candidates.py` and `tools/jobs.py` - **delegating to the real `emit`**, so the row is
   still written and the policy dispatcher still runs - and records the `AuditPhase` each call
   site passes. Twelve parametrised cases each drive one branch and assert the exact ordered
   tuple of phases that branch emits. **A rotation is a wrong member; an amputation is a missing
   element.** That is the same test closing #129's rotations and #127/#128's amputations, which
   is why one table replaced fourteen near-identical cases.

   The expectations are read off DESIGN.md ("Audit-write failure has a stated policy"), not off
   the code: a read is `READ`, anything before a side effect is `BEFORE_SIDE_EFFECT`, the
   emission after a completed POST is `AFTER_WRITE`. Copying today's arguments in would have
   asserted only that the code had not changed.

2. **A container check.** `_static_phase_sites()` walks the `tools/` package with `ast` and
   returns the (function, member) pairs; the test asserts that set EQUALS the set the twelve
   cases exercise. It recurses rather than using `ast.walk` **because every tool is a closure
   inside `register`**, and a walk would attribute all fifteen sites to `register` and make the
   equality trivially true. A site added later under an undriven phase fails here.

3. **The behavioural case for the one the policy exists for.**
   `test_a_failed_audit_write_before_the_post_leaves_the_ats_untouched` runs the approved write
   twice against a row-counting fake ATS: once with a working audit sink (**exactly one row** -
   the control, without which the second arm passes against a tool that cannot write at all),
   then with `audit.logger` replaced by one whose every write raises. The second arm asserts the
   counter did **not** move. Rotate `candidates.py:796` to `READ` and the failure is swallowed to
   stderr, the POST proceeds, and this arm sees a row.

**Both branches of a read emit `READ`**, so the phase sequence alone cannot tell a success case
from an error case: each read case additionally pins `is_error` on the wire result. Without that,
an "error" case that quietly succeeded would still pass and its call site would stay unasserted.

---

## 3. SURVIVOR -> KILLED, PER SITE. Not a summary

`python3 docs/reviews/probe-audit-shape-container.py --shape audit_phase` (run in four `--only`
chunks after a kill, §6; every chunk printed `TREE RESTORED CLEAN UNDER src/ AND tests/`).

| site | phase | BEFORE | AFTER | killed by |
|---|---|---|---|---|
| `audit.py:381` | BEFORE_SIDE_EFFECT | killed, 7 failed | killed, 8 failed | the dispatcher's own tests, +1 of mine |
| `audit.py:403` | AFTER_WRITE | killed, 5 failed | killed, 5 failed | unchanged |
| `candidates.py:648` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[search_candidates-error]`, container |
| `candidates.py:656` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[search_candidates-success]`, container |
| `candidates.py:694` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[get_candidate-error]`, container |
| `candidates.py:702` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[get_candidate-success]`, container |
| `candidates.py:768` | BEFORE_SIDE_EFFECT | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[create_candidate-pending]`, container |
| `candidates.py:780` | BEFORE_SIDE_EFFECT | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[create_candidate-refused]`, container |
| `candidates.py:796` | BEFORE_SIDE_EFFECT | **SURVIVOR** exit 0 | **KILLED** exit 1, 4 failed | `test_a_failed_audit_write_before_the_post_leaves_the_ats_untouched`, `[create_candidate-written]`, `[create_candidate-post-failed]`, container |
| `candidates.py:818` | AFTER_WRITE | **SURVIVOR** exit 0 | **KILLED** exit 1, 1 failed | `[create_candidate-post-failed]` |
| `candidates.py:832` | AFTER_WRITE | killed, 1 failed | killed, 2 failed | `test_case16_the_audit_failure_warning_branch_carries_request_id`, `[create_candidate-written]` |
| `jobs.py:419` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[search_jobs-error]`, container |
| `jobs.py:426` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[search_jobs-success]`, container |
| `jobs.py:704` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[get_job_feed-error]`, container |
| `jobs.py:711` | READ | **SURVIVOR** exit 0 | **KILLED** exit 1, 2 failed | `[get_job_feed-success]`, container |

`[x]` is the parametrised id of
`test_each_audit_emission_passes_the_phase_the_design_assigns_it`; "container" is
`test_every_audit_phase_call_site_is_covered_by_a_case`.

`audit_phase POPULATION: 15 ROWS: 15 APPLIED: 15 **VACUOUS: 0**` across the four chunks.

**The `emit` shape**, `--shape emit --only "candidates.py:656" --only "candidates.py:768"`:

| site | BEFORE | AFTER | killed by |
|---|---|---|---|
| `candidates.py:656` (#127) | **SURVIVOR** exit 0, 873 passed | **KILLED** exit 1, 1 failed | `[search_candidates-success]` |
| `candidates.py:768` (#128) | **SURVIVOR** exit 0, 873 passed | **KILLED** exit 1, 1 failed | `[create_candidate-pending]` |

`emit POPULATION: 13 ROWS: 2 APPLIED: 2 **VACUOUS: 0**`, and the eleven unselected sites printed
as `NOT SWEPT`, so this partial run cannot read as a complete one.

**Two rows are killed by ONE test each and I am not treating that as a weakness**: `818`'s
rotation and both `emit` amputations move exactly one assertion, which is the assertion written
for them. `796` - the one that matters - takes four tests down.

---

## 4. THE INSTRUMENT WAS RE-PROVEN AFTER MY CHANGE, NOT ASSUMED

A change to the tests after the measurement is exactly what quietly invalidates one, so
`docs/reviews/probe-audit-shape-controls.py` was re-run **with my test file in the tree**, exit
**0**, verbatim:

```
population BEFORE planting: 13
population AFTER planting:  16
A PASS: the derivation grew by exactly 3 and named the plants
B: applied=True rc=1 killed=['tests/test_probe_control_plant.py::test_asserted_site_emits_its_audit_row'] tail='============ 1 failed, 887 passed, 6 deselected in 79.43s (0:01:19) ============'
B PASS: the asserted plant was killed, by its own test
C: applied=True rc=0 killed=[] tail='================= 888 passed, 6 deselected in 82.07s (0:01:22) ================='
C PASS: the unasserted plant survived - a survivor is real
D1: applied=False refused="IndentationError: expected an indented block after 'if' statement on line 24 (<unknown>, line 25)" rc=None
D1 PASS: refused, no verdict - IndentationError: expected an indented block after 'if' statement on line 24 (<unknown>, line 25)
D2: applied=False refused='mutation did not land despite a successful write' rc=None
D2 PASS: a write that changed nothing was refused, not scored

ALL FOUR CONTROLS PASS. Population restored to 13 emit sites.
```

**Control C is the one that matters here.** My tests could have made every row report "killed"
by being sensitive to any edit at all. C plants an unasserted `emit(...)` site, byte-identical to
B's asserted twin, and it **still survives** at `888 passed`. So a survivor is still detectable
in this tree, and §3's fourteen flips are the tests, not a spoiled instrument.

---

## 5. #130 SETTLED BY MEASUREMENT: `candidates.py:832` IS NOT A THIRD SURVIVOR

The brief asked me to say so if my work made the confounded row cleanly measurable. It did not -
the probe's `emit` operator still deletes the statement and still raises `NameError` - so I ran
**the operator #130's own report proposed and never measured**: replace the CALL with a
same-shaped literal and keep the binding.

    -                warnings = emit(event, AuditPhase.AFTER_WRITE)
    +                warnings = []

The mutation landed (verified against `git diff --stat`: 1 file, 1 insertion, 1 deletion) and
the suite ran twice:

| arm | result | verdict |
|---|---|---|
| **without** `tests/test_audit_phase_sites.py` (`--ignore`) | `1 failed, 872 passed, 6 deselected` | **KILLED**, by `test_approval_write.py::test_case16_the_audit_failure_warning_branch_carries_request_id` |
| with my tests | `2 failed, 885 passed, 6 deselected` | killed, +`[create_candidate-written]` |

**So the row was ALREADY asserted before my work, by an audit test, and the sweep's headline of 2
`emit` survivors is correct - not understated by one.** The confound hid a real kill, not a
missing one. `test_case16_the_audit_failure_warning_branch_carries_request_id` asserts the
post-write warning reaches the caller, which is precisely what deleting this emission destroys.

**Suggested fix for #130, now backed by a measurement rather than a hypothesis:** adopt the
`ast.Assign` branch in `mutate()` - when the enclosing statement is an `Assign` whose value IS
the matched call, replace the CALL with `[]` and set `expect_stmt_delta` to 0. It lands cleanly,
both of the probe's existing assertions still apply, and the verdict it produces here is KILLED.
I did not change the probe: that is #130's work, and editing the instrument inside the run that
uses it is the failure this repo has already recorded twice.

`candidates.py:832` was restored by `cmp` against a pre-run backup afterwards, byte-identical.

---

## 6. THE HARNESS WAS KILLED AGAIN, AND IT AGAIN LEFT A LIVE MUTATION IN `src/`

Recording it because it is #131's evidence and the second occurrence in this file's history.

The AFTER sweep was launched as one background run of both shapes plus the #130 arms. It was
**stopped at row 1**, and `git status --porcelain` immediately afterwards read:

```
 M src/fast_mcp_jobvite/audit.py
```

`cmp` against the pre-run backup located it at **byte 15405, line 381** - the `AuditPhase`
rotation of the very first row. `candidates.py` and `jobs.py` were byte-identical. **SIGKILL runs
no `finally`**, so the probe's restore never ran. Restored by `cp` from the backup plus `cmp`,
never `git checkout --`, and the tree was proved clean before anything else happened. **No
verdict in this report was measured against that dirty tree**: `audit.py:381`'s row was re-run
from the restored tree in chunk A.

The remaining rows were then run in four foreground `--only` chunks small enough to finish inside
a timeout, which is what `--only` exists for. **The durable answer is still #131's `--restore-only`
mode; nothing here fixes it.**

---

## 7. GATES

Each on its own line, exit code read on its own line, never chained and never
`cmd; echo "EXIT=$?"`.

```
uv run --frozen ruff check .          -> All checks passed!            RUFF_CHECK_EXIT=0
uv run --frozen ruff format --check . -> 111 files already formatted   RUFF_FORMAT_EXIT=0
uv run --frozen mypy                  -> Success: no issues found in 111 source files
                                                                       MYPY_EXIT=0
```

`ruff check` first failed on my file with `S105 Possible hardcoded password assigned to:
"FEED_SECRET"` and was fixed the way `test_tools_job_feed.py:78` already handles it, not by
weakening the rule.

**Suite: `887 passed, 6 deselected in 76.46s`, 0 skipped**, from `873 passed` at the base. The
floor was derived from `ci.yml` by grep (`check-suite-floor.sh 873`), never retyped.

**I RATCHETED THE FLOOR IN `ci.yml`, 873 -> 887, and watched it fire both ways** rather than
predicting it:

```
887 passed / floor 887 -> suite floor OK: 887 passed, floor 887
                          HARNESS-RESULT ... status=ok        AT_887_EXIT=0
887 passed / floor 888 -> ::error::887 passed, but the floor is 888.
                          HARNESS-RESULT ... status=breach    AT_888_EXIT=1
```

So the new floor is tight - no slack, the defect `chore/floor-controls` found on `u7`.

**Harness anchors**, floor DERIVED from `ci.yml` (458), verbatim tail:

```
harnesses scanned: 34
anchors resolved: 458
OK: all 458 anchors resolve to exactly one hit in their target file (floor 458).
```
exit 0. No shell harness changed here, so that population is unmoved.

**`docs/OBLIGATIONS.md` was not hand-edited, and the checker was run rather than assumed** -
verbatim:

```
Mappings: 31  |  anchors verified against their subject: 25  |  recorded as absent: 6
Every mapped anchor still contains its subject. OK.
```
exit 0.

No `ci.yml` step is proposed beyond the floor ratchet above, which I ran.

**Two doc checkers are RED on this branch and neither is mine**, stated here rather than left for
someone to attribute to this work:

- `check-design-citations.py` exit 1, both problems in `docs/reviews/REVIEW-R10.md:353` and
  `:416` (`DESIGN.md:99999 is past the end`).  <!-- REPOINT-EXEMPT: quotes the planted citation as evidence -->
- `check-design-citation-shape.py` exit 1, 47 ranges ending on a blank line - the population
  #126 was working through. **Zero of its findings name `AUDIT-SURVIVORS-REPORT.md` or
  `tests/test_audit_phase_sites.py`** (`grep -c` over its output: 0), and my test module cites
  DESIGN.md by SUBJECT PHRASE with no line numbers, so it cannot enter that population at all.

`check-cross-references.py` exits 0.

---

## 8. FINDINGS

### F1 (Medium, REPORTED not fixed - #130) - the confounded row is measurable, and it is a kill

§5. The suggested fix is the `ast.Assign` branch, now measured rather than hypothesised. Left to
#130 because it edits the instrument.

### F2 (Medium, REPORTED - #131) - a killed harness left a live mutation in `src/` for the second time

§6. Suggested fix unchanged and unbuilt: `--restore-only`, writing its backup manifest somewhere
durable before the first mutation, so recovery is one command rather than a `git status` a human
has to remember to run.

### F3 (nit, FIXED here) - a read tool's two branches are indistinguishable by phase alone

Both emit `READ`, so a case table keyed only on phases cannot tell whether it drove the success
branch or the error branch - and an "error" case that silently succeeded would still pass while
its call site stayed unasserted. Fixed by pinning `is_error` on the wire result in every read
case, before the phase assertion.

---

## 9. WHAT I DID NOT VERIFY

For what I could not settle, not for what I did not try.

1. **The killed-test NAMES for `audit.py:381` and `audit.py:403` in the AFTER run.** I have their
   exit codes and failure counts (8 and 5) but the first chunk's output filter ate the
   `killed:` lines, and re-running two rows costs ~150s for names that are not load-bearing:
   both were killed BEFORE my change and remain killed. The BEFORE run names all twelve of
   `381`'s and all five of `403`'s.
2. **Whether the twelve phases are correct in production.** Unchanged from the sweep's position:
   I read all fifteen against DESIGN.md and they look right today. This work closes the absence
   of an assertion, not a live bug. **I found no wrong phase, so there is no Critical to stop for.**
3. **Whether the container check would catch a call site added in a NEW module** under
   `tools/`. It globs `tools/**/*.py`, so it should, but the only evidence I have is that it
   catches sites in the two modules that exist - I did not plant a third module.

Settled rather than parked, in case any of these look like candidates:

- **The instrument, after my change**: §4, controls re-run with my file present, C still shows a
  survivor.
- **Whether the mutations landed and were restored**: every chunk printed
  `TREE RESTORED CLEAN UNDER src/ AND tests/`, and the one that did not (§6) was caught by
  `git status` plus `cmp` against a backup taken before the first run.
- **Whether the new floor is tight**: watched firing at 888 and passing at 887, §7.

---

## 10. DELIVERY

Committed on `fix/audit-survivors`. **Not merged, not pushed, not rebased.** The worktree is the
one the brief assigned and is left in place; I did not create or remove any other.

Tasks #127, #128 and #129 are closed by measurement. #130 is answered but stays open for the
probe change. #131 gains a second occurrence.
