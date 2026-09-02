# #236 MEASURED: the conflation confirmed, the replacement shape proved, and the count corrected

**Measured by the orchestrator, 2026-09-02.** `#236` shipped three ready hunks from `#232` and said
plainly that **all three were UNMEASURED** - `#232` had run the CURRENT bodies to prove they
conflate and had not run the replacements, and two of them change `|| { ... }` into an rc read,
which is the exact shape that has measured wrong three times in this session.

**`ci.yml` IS NOT TOUCHED HERE.** `blackthorn-revamp` owns that file for `#238`. This document is
the measurement, so that whoever edits the file next applies a proved hunk instead of re-deriving
one.

## The conflation, reproduced

`check-pytest-bounded.sh` was driven to its REAL refusal - a scratch git tree containing no pytest
invocation at all, which is the condition its exit 2 exists for - and then `ci.yml`'s **exact
current step body** was run over that same tree.

    ARM 1  the script alone
           MATCHED ZERO pytest invocations. The selector is broken; a green
           here would mean nothing.
           HARNESS-RESULT name=check-pytest-bounded.sh rows=0 floor=0 status=refused
           rc=2

    ARM 2  ci.yml's current body, verbatim, same tree
           ...the refusal above, then:
           ::error::a pytest invocation runs unbounded; see #108
           rc=1

**CONFIRMED, and narrower than `#236` states.** The script's honest diagnosis DOES reach the log -
it writes to stdout and nothing captures it. What conflates is **the `::error::` annotation and the
exit code**, and the annotation is what GitHub surfaces in the run summary and the checks UI to a
reader who never opens the log. That reader is told a pytest call runs unbounded, and pointed at a
ticket about unbounded calls, when the truth is that the selector matched nothing.

## The replacement, proved in both directions and with a positive control

The rc-read form was run over three trees. **All three arms, not the one that flatters it:**

    ARM 3a  zero-match tree   -> "the bounded-pytest guard REFUSED ... This is
                                 NOT an unbounded call; see the refusal above"   rc=2
    ARM 3b  one real unbounded call in a tracked .sh
                              -> "1 pytest invocation(s) run unbounded", then
                                 "::error::a pytest invocation runs unbounded"   rc=1
    ARM 3c  the real repository (positive control)                               rc=0

**3b is the arm that matters and is the one a fix like this usually fails.** Making a body
distinguish exit 2 is easy; keeping it able to still catch the thing it was written for is where
the previous three suggested remedies went wrong. It catches it.

**3c is not decoration.** Without it, 3a and 3b together are consistent with a body that refuses
everything.

## ARM 4: run it the way GitHub runs it, and amputate the one line that matters

3a-3c ran in a subshell. GitHub runs every `run:` block as **`bash -e {0}`**, and that is precisely
where this shape dies: under `-e` the ASSIGNMENT `out=$(cmd)` is itself the failing command, the
shell exits there, and every branch below becomes unreachable. `#232` ran its arms under
`/usr/bin/bash -e` for that reason. So the body was written to a file and executed the same way.

    ARM 4a  proposed body, `bash -e`, zero-match tree
            -> refusal printed, "...REFUSED ... NOT an unbounded call"      rc=2
    ARM 4b  proposed body, `bash -e`, one real unbounded call
            -> "1 pytest invocation(s) run unbounded", then the annotation  rc=1
    ARM 4c  AMPUTATED: the same body with `set +e` DELETED, `bash -e`, zero-match tree
            -> PRINTS NOTHING AT ALL                                        rc=2

**ARM 4c IS THE FINDING, AND IT IS WORSE THAN THE DEFECT IT CONTROLS FOR.** Delete one line and the
body still exits 2 - **the correct code, produced by the wrong mechanism**, because the shell died
at the assignment rather than reaching the branch that decides. A reviewer checking "does it exit 2
on a refusal?" would pass it. The only thing that gives it away is the **absent output**, and a
silent step whose exit code looks right is the shape this repository has been bitten by all night.

So `set +e` is not hygiene here; it is the whole fix, and 4c is what proves 4a is not vacuous.

## The count is THREE annotations, not three lost diagnoses

`#236` reads as though the three steps lose the script's message. They do not, and the reason
differs per step, which is worth knowing before anyone edits them:

- `check-adr-numbers.py` **has already been converted** to `set +e; out=$(...); rc=$?; echo "$out"`,
  so its diagnosis is printed explicitly. Its `if [ "$rc" -ne 0 ]` still gives one annotation for
  both 1 and 2, so it conflates in the annotation only.
- `check-pytest-bounded.sh` and `check-committed-file-types.py` use `cmd || { ... }`, where the
  script's output reaches the log because nothing captures it. Same residue: the annotation.

So the defect is **uniform and is about the annotation and the exit code**, and the `set +e` rc-read
conversion is what fixes it in all three, not a rescue of a lost message.

## What is NOT measured here

- **Only `check-pytest-bounded.sh` was driven to a real exit 2.** The other two hunks are unproved.
  `check-committed-file-types.py` needs a `git ls-files` failure, and `check-adr-numbers.py` needs
  an absent ADR directory; neither was staged.
- **Nothing was applied to `ci.yml`.** These arms ran the body text as a file, not as a workflow
  step. Everything else about the shell was made faithful (see ARM 4).
- `#232`'s biggest open question stands: whether 45 is the complete set of `ci.yml` script
  invocations. A path built from a variable is invisible to that regex, and it already
  under-reported once, by twelve.
