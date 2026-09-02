# MEASURED-252: check-u3-audit-controls converted to coverage-map selection

Task #252. Worktree `/tmp/u3-selection-work`, branch `fix/252-u3-selection`,
pinned at `7431bb5` and rebased onto `main` at `5b00bfe` when main moved under
me. Every number below is from a run in that worktree; nothing is reconstructed.

## THE HEADLINE

The conversion **is done and it holds**, but it did not hold on the first run,
and the row that broke it is the most useful thing in this report.

- Paired back-to-back, one worktree, both `rc=0` `killed=15/15`:
  **264.91s -> 88.72s, a 2.99x speed-up, 66.5% off.** Labelled **(1)**.
- **All 15 verdicts identical**, row by row, across six runs - the same test
  NAMED as each row's killer, not merely the same count.
- **The deriver's own stated premise is FALSE in this tree**, and M10 is the
  counter-example. A test that READS the source can go red for a mutation it
  never executes. 16 of the test modules here import `ast` or call
  `inspect.getsource`.

## WHAT I READ

Read in full, and I am naming them because the brief asked which I actually
opened rather than cited:

- `standards/devops/bash.md` (v1.0.2, `priority: required`) - all 829 lines.
- `standards/devops/ci-cd.md` (v1.3.5, `priority: required`) - all 792 lines.
- `standards/architecture/testing-strategy.md` (v1.2.5, `priority: required`) -
  all 692 lines.
- `docs/adr/0023-harnesses-drop-e-from-strict-mode.md` in full.
- `docs/reviews/REVIEW-R23.md` on `review/r23` at `028d80f` - **H4** (`:166-358`)
  and **X4b** (`:551-606`), the current rewritten versions.
- `scripts/check-u3-audit-controls.sh`, `scripts/lib/select-covering-tests.py`,
  `scripts/lib/harness-result.sh`, and BOTH existing call sites:
  `check-u9-http-amputation.sh:88-95,:126-142` and
  `check-u4-client-amputation.sh:88-90,:134-143`, plus
  `check-u4-client-controls.sh:118-124` (the `"$SUITE::$want"` pattern).
- Board tasks #250, #251, #253 for the census, the u9 split and the
  per-invocation floor.

**Looked for and did not find:** `standards/devops/bash.md` is not in
`MUST-READ-DOCS.md`'s TIER 1 table - the brief named it as binding and it is
(`priority: required`), but a reader working from the index alone would not
reach it. Not a finding against this task; recorded because the brief told me
to flag what I looked for and could not find where I expected it.

**No standard clause contradicts this work.** The nearest binding one is
ci-cd.md's *"Skipped is not green"* (`:669-729`): a skipped check is an unknown
result, not a pass. That argues FOR the wide fallback and against any selection
that can quietly run nothing, which is the shape the design below preserves.

## THE CONVERSION

`scripts/check-u3-audit-controls.sh`, three changes, the u9/u4 pattern:

1. The baseline doubles as the coverage-map build -
   `COVERAGE_FILE="$COVDB" ... pytest $SUITE --cov --cov-context=test
   --cov-report= --cov-fail-under=0` on the pristine tree. `COVDB` is a
   `mktemp` file removed by an EXIT trap that chains `harness_result_emit`
   first, because that trap REPLACES the one `lib/harness-result.sh` armed at
   source time.
2. Each row derives its tests BEFORE the mutation lands. `rc=4` falls back WIDE
   to `$SUITE`; any other non-zero rc STOPS the harness.
3. The row body runs `pytest $sel` instead of `pytest $SUITE`.

`ROW_FLOOR` unchanged at 15. No row added or removed. **`ci.yml` untouched.**

## 1. BEFORE, unconverted

    rc=0   rows=15   floor=15   killed=15/15   status=ok   WALL=259.54s

## 2. AFTER - and the FIRST run was a DEFECT, reported rather than smoothed over

The first converted run came back **`killed=14/15`, `status=breach`, rc=1**.

    M10 the var is set directly, losing correlation.py's finally:
      SELECTOR 28 node(s): [none of them the row's killer]
      the selected tests went red, but NOT at
      test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself
      - a coincidence, not a control

**Diagnosis, from the test's own body** (`tests/test_audit.py:607-637`):

```python
tree = ast.parse(pathlib.Path(audit.__file__).read_text(encoding="utf-8"))
```

M10's killer **parses `audit.py` as text and asserts over the AST**. It never
EXECUTES the lines M10 mutates, so no `arc` row is attributed to it and the
coverage map cannot name it. Its own docstring says why it is written that way:
an earlier substring version passed against an amputated call because the module
docstring quotes the line, so it was rewritten to read the tree.

**This refutes, in this tree today, the premise
`scripts/lib/select-covering-tests.py:8-14` states for itself:**

> "A test that never EXECUTES the mutated statements cannot go red because of
> them, so running only the tests that did execute them asks the identical
> question at a fraction of the cost."

A source-READING test can. Measured breadth of the class:

    test modules importing `ast` or calling `inspect.getsource`   16

**The harness FAILED CLOSED**, which is why this is a fix and not a retraction.
A controls row passes only when its NAMED test goes red, so a selection that
drops the killer yields SURVIVED or "red but not at `$want`" - `FAIL` goes up
and the harness exits 1. Narrowing here cannot manufacture a green. That is the
property that makes selection admissible on the CONTROLS harness and is exactly
what is absent from the amputation sibling, whose product is its survivor list.

**The fix** is a precondition, not a workaround: the row requires the map to
NAME its killer, and falls back WIDE when it does not. Matching uses the SAME
substring rule as the verdict `grep -q "$want"`, deliberately - `$want` is
sometimes a prefix (`test_arm3`, `test_case2`) and two different rules for one
name is how a row passes one check and fails the other.

## 3. AFTER, converted - ONE ROW PER MUTATION

Never a bare total. Selector width and verdict, from the final run:

| row | selector | verdict |
|---|---|---|
| M1  | WIDE (no in-process coverage) | killed by `test_stdio_never_records_the_literal_global` |
| M2  | 28 nodes | killed by `test_stdio_never_records_the_literal_global` |
| M3  | 22 nodes | killed by `test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none` |
| M4  | 35 nodes | killed by `test_case17_arm2_trace_context_is_ABSENT_when_the_caller_supplies_none` |
| M5  | WIDE (no in-process coverage) | killed by `test_case17_a_malformed_traceparent_yields_nothing_rather_than_a_guess` |
| M6  | 7 nodes  | killed by `test_arm1_before_the_side_effect_the_call_fails` |
| M7  | 5 nodes  | killed by `test_arm3` |
| M8  | 2 nodes  | killed by `test_arm2_on_a_read_it_logs_to_stderr_and_continues` |
| M9  | 37 nodes | killed by `test_an_invalid_inbound_request_id_is_replaced_rather_than_used` |
| M10 | WIDE (**the map does not name** `test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself`) | killed by that test |
| M11 | WIDE (no in-process coverage) | killed by `test_case2` |
| M12 | 22 nodes | killed by `test_uppercase_parameter_names_are_still_redacted` |
| M13 | 17 nodes | killed by `test_an_unlisted_argument_key_is_redacted` |
| M14 | 17 nodes | killed by `test_a_container_under_an_unlisted_key_is_redacted_WHOLE` |
| M15 | 17 nodes | killed by `test_a_url_embedded_in_an_exception_message_is_redacted` |

**11 select, 4 fall back wide.** Verdicts diffed mechanically against BEFORE
across four separate converted runs (post-fix, paired, rebased, final):
**identical every time, 15/15.**

## 4. THE AMPUTATION ARM - `docs/reviews/probe-252-selection-can-fail.sh`

Same verdicts would also be produced by a selection that could never fail, so
the probe breaks the test the map SELECTED and requires the row to flip.

**The break is an assertion-ectomy, not a deletion, and that choice is the whole
point.** A deleted test stops executing the mutated lines, drops out of the map,
and takes the row down the WIDE fallback - proving the fallback works, not that
the selected path can fail. Removing only the assertion leaves the test in the
map, still named in the selector line, and unable to fail.

    ARM M6   selector 7 nodes, still names its killer
             killed -> "red, but NOT at test_arm1_..."   harness rc=1 breach
    ARM M8   selector 2 nodes, still names its killer
             killed -> "SURVIVED - the selected tests stayed green"  rc=1 breach
    ARM M14  selector 17 nodes, still names its killer
             killed -> "red, but NOT at test_a_container_..."  rc=1 breach

    ARMS: 3/3 passed
    HARNESS-RESULT name=probe-252-selection-can-fail.sh rows=3 floor=3 fired=3/3 status=ok

`tests/` verified byte-identical to both the index and HEAD after every run.

The probe also refuses two ways it could lie: an arm is VOID if the row took the
wide fallback, and VOID if the selector stopped naming the killer.

## 5. THE FALLBACK ARM - it occurs NATURALLY, three times, unfabricated

M1, M5 and M11 hit `rc=4` and print:

    no in-process test covered src/fast_mcp_jobvite/audit.py:75-75; caller must
    fall back to the full suite
    M1  stdio records the literal "global": SELECTOR fallback=WIDE (no
    in-process coverage) -> $SUITE

All three are module-level anchors (`audit.py:75`, `audit.py:101`,
`redaction.py:104`) - constants and a regex, executed at IMPORT time, which
`--cov-context=test` attributes to no test context. **Nothing was constructed to
make this branch fire.** M10 exercises the second, new fallback branch.

## 6. TIMING (1)

    PAIRED, back-to-back in one worktree, minutes apart:
      HEAD harness (git show HEAD:... to a temp path)   264.91s   killed=15/15
      converted harness                                  88.72s   killed=15/15
      ratio 0.335 -> 2.99x, 66.5% off

    INDEPENDENT EARLIER PAIR, ~40 min apart:
      259.54s -> 92.78s   ratio 0.357 -> 2.80x

    Other converted runs: 86.98s (rebased), 92.25s (final).

Labelled **(1)**: single draws on a box running a dozen agents. **The RATIO
inside the paired run is the robust part; no absolute here is.** I did not apply
any runner factor - R23-M1 is right that the standing ~1.9x divides a JOB by a
HARNESS.

The BEFORE baseline is `107 passed in 13.71s`; the harness's cost was never the
baseline, it was 15 whole-suite row runs. That is what selection removed.

## 7. TWO GATES THAT WENT RED ONLY AFTER THE COMMIT

Worth its own section, because it is a measurement about my own method.

I ran the full gate battery **before** committing and got 13/13 green. After
`git add` + commit, two went red:

    check-checkers-are-wired.py    probe-252-selection-can-fail.sh UNWIRED and
                                   unexplained
    check-row-floor-exactness.py   it carries a literal floor and the control
                                   TABLE does not name it

Both checkers select **tracked** files, so an untracked new probe is invisible
to them. A pre-commit gate run is not the same question as a post-commit one for
any checker whose population is `git ls-files`.

Then a third, from the floor CONTROL rather than the checker: it deleted an arm,
watched my floor fire correctly (`2/3`, exit 1) and **still refused the run** -

    ::error::the harness printed NO 'HARNESS-RESULT
             name=probe-252-selection-can-fail.sh ...' line.
             A missing line is NOT a pass: nothing here can say whether the
             floor fired.

It was right. All three fixed; the control now reports
`CONTROL FIRED: ... loses 1 row(s), reported rows=2 floor=3 status=breach,
exiting 1` at rc=0.

**A fourth, and it is two instruments disagreeing about one object:**
`check-row-floor-exactness.py` accepted my `ARM_FLOOR=3`;
`check-row-floor-controls.sh` aborts with `no literal ROW_FLOOR=<n>`. Measured:
28 shell members use `ROW_FLOOR` and only the two PYTHON members use
`arm_floor`, so the shell convention is `ROW_FLOOR` and the disagreement was
mine to resolve. Renamed.

## 8. THE FULL GATE, on the final tree, by EXIT CODE

    ruff check .                                    rc=0
    ruff format --check .                           rc=0
    check-checkers-are-wired.py                     rc=0
    check-checkers-are-wired.py --self-test         rc=0
    check-harness-anchors.py --self-check --floor 464   rc=0
    check-row-floors.py                             rc=0
    check-row-floor-exactness.py                    rc=0
    check-row-floor-exactness.py --self-test        rc=0
    shellcheck --severity=warning scripts/*.sh      rc=0
    shellcheck --severity=warning docs/reviews/*.sh rc=0
    check-no-errexit.py                             rc=0
    scripts/check-pytest-bounded.sh                 rc=0
    actionlint (SHELLCHECK_OPTS=--severity=warning) rc=0
    check-row-floor-controls.sh <the probe>         rc=0, CONTROL FIRED

    git status --short   (empty)

The `SC2206` directive on the selector's array split is **operative, not
decorative**: deleting it makes `shellcheck --severity=warning` - the gate's own
threshold - exit 1 on that line. Measured both ways.

## 9. HANDOFF

    cd /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite
    git merge --ff-only fix/252-u3-selection

Three commits on `fix/252-u3-selection`, rebased onto `main` at `5b00bfe`, so
the fast-forward is available as written. `main` moving under me touched none of
my files or their inputs - verified with `git diff --stat 7431bb5..main` over
the harness, the selector library, all three `$SUITE` files and both mutated
source files: empty.

Worktree `/tmp/u3-selection-work` **removed** after this report was committed.

## 10. WHAT I DID NOT VERIFY

- **Nothing here ran on the runner.** Every figure is local. The 488s/499s split
  in the brief is R23's measurement from run 33610211810 and I never reproduced
  it; my BEFORE is 259.54s locally. The 2.99x RATIO is what I would carry
  forward, not any second.
- **I did not re-check the other two selecting harnesses against the
  source-reading class.** `check-u9-http-amputation.sh` and
  `check-u4-client-amputation.sh` use the same deriver and have no
  killer-in-selection precondition, because an amputation row names no killer.
  Whether either has an anchor whose only killer reads source is UNMEASURED. It
  would be a false SURVIVOR there, not a false green - loud, not silent - but it
  is unmeasured either way. Filed as its own task.
- **I did not measure the `--cov-context` overhead on THIS suite.** #251 measured
  ~9% on the 889-test suite; I assumed it transfers and did not re-derive it on
  the three-file suite. It is inside the 88.72s either way.
- **The four wide-fallback rows are the residual cost and I did not price
  them.** Four whole-suite runs remain in the 88.72s; how much of it they are is
  unmeasured.
- **I did not run the full pytest suite**, only the three files `$SUITE` names.
  Nothing here claims anything about the other test modules.
- **I did not touch `check-u3-audit-amputation.sh`**, which the brief refused for
  conversion and which #259 now names as the binding constraint at 317s. Nothing
  in this report bears on whether that refusal is right.
- **My probe's three arms are the three I chose.** They are all rows whose
  selector is narrow and whose killer is unique; I did not attempt an arm on a
  wide-fallback row or on `M7`/`M11`, whose `$want` is a prefix matching several
  tests.
