#!/usr/bin/env python3
"""Every checker and probe we ship runs in CI, or says why it does not.

    python3 docs/reviews/check-checkers-are-wired.py
    python3 docs/reviews/check-checkers-are-wired.py --self-test

**WHY THIS EXISTS.** Three checkers here were written, measured,
committed - and never wired into CI. Nothing said so. They sat green and
inert while being cited as gates, which is strictly worse than not
having them: an unwired checker is a claim of coverage that costs
nothing to make and nobody can see is false.

**IT IS THE SAME MISTAKE TWICE, WITH THE SAME INSTRUMENT.** The obvious
census is `grep <basename> .github/workflows/ci.yml`. That counts a name
in a COMMENT as wired. Review R12 used it and mislabelled three files; I
used it earlier the same day and reported
`check-design-citation-shape.py` as WIRED, then spent hours calling an
unwired scan a gate. My replacement parser was ALSO wrong: it matched
only block-form `run: |` and missed every single-line `run:`, reporting
`check-coupling.py` as unwired twenty minutes after I had read its step.
The contradiction between two wrong instruments is the only reason
either was caught.

So this file does not grep the workflow. It **parses the YAML** and
reads `jobs.*.steps[].run` - the only place a step can actually execute
- and strips shell comments from those bodies before looking for a name.

**THE EXEMPTION IS A DECISION, NOT A HOLE.** A checker may be unwired on
purpose: `check-review-coverage.py` reports a real backlog and exits 1
until that backlog clears. Being unwired is fine. Being unwired *and
unrecorded* is the defect. So an exemption needs a non-empty reason, and
a blank one is refused.

**IT ALSO CHECKS THE REVERSE, which nothing else here does.** An
exemption naming a checker that IS wired is stale - the reason has
outlived the condition, and a stale exemption is how a list stops
describing the thing it lists. That is a failure too, not a nit.

## Scope: the CONTAINER, not a prefix inside it (#153, #155, #149)

The container is **every tracked `.py` or `.sh` under `docs/reviews/`
and `scripts/`**, enumerated from git. Membership is decided by KIND -
a runnable script file, by suffix - and never by what its name starts
with. That is #115's doctrine, and until 2026-09-01 this file was the
loudest violation of it.

**IT USED TO BE TWO GLOBS WEARING A CONTAINER'S NAME**:
`docs/reviews/check-*.py` and `docs/reviews/check-*.sh`. Measured at
`2d886a4`, that selected 28 of the 123 files here, and it printed
*"Every checker is wired"* about the other 95.

It was blind in three directions at once, and they are three separate
mistakes that happened to share a line:

- **BY PATH (#153).** `scripts/` was excluded, with a stated reason:
  those are per-unit mutation HARNESSES reaching CI through
  `scripts/ci-harness-gate.sh`, a second container with its own gate.
  The reason was true and the exclusion still did harm, because
  `scripts/` had stopped holding only harnesses. Two real gates live
  there now, and one of them - `check-timeout-literals.py` - was
  committed UNWIRED by the very task that built it, at exit 0.
- **BY PREFIX (#155).** `probe-*` was never in the population, so
  nobody was ever ASKED for a reason. 33 of the 34 probes here are
  unwired. `measure-*` and `sample-*` were a third and fourth prefix
  nobody had noticed at all.
- **BY ITS OWN ESCAPE HATCH (#149).** `probe-midsentence-shape.py`
  says in its docstring that it is named `probe-` *"so it cannot
  become a gate by accident"* - it was using the prefix filter AS a
  mechanism. The widening removes that hatch on purpose: a file opts
  out by RECORDING A REASON, which someone can read and argue with,
  never by choosing a name this checker cannot see.

**THE PATH SCOPE IS STILL A PATH, AND THAT IS NOT THE DEFECT.** A
container has to be bounded somewhere. The defect was filtering by NAME
inside the bound, because a name is a thing an author picks and a
container is not.

**MOST MEMBERS ARE NOT GATES AND MUST NOT BECOME ONE.** A control that
breaks its subject, a one-shot whose question is settled, a reporting
instrument that must never refuse - each is a legitimate reason to be
unwired, and each is now WRITTEN DOWN in `UNWIRED_BY_DECISION` instead
of being implied by a filename. `scripts/*` harnesses reached through
`ci-harness-gate.sh` read as WIRED here for free, because that gate
names each one in a `run:` body.

**WHAT IT CANNOT DO.** It proves a checker is INVOKED, not that its exit
code gates the job. A step that runs a checker and swallows its status
reads as WIRED here. That is a real gap, and the four non-gating
shell forms this repo has shipped are the reason to say so out loud
rather than let "wired" imply "gating".
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shlex
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Checkers that are deliberately not wired, each with the reason. **A
#: bare name is refused: the reason IS the exemption**, the same shape
#: `check-no-errexit.py` and `check-settings-are-read.py` use.
UNWIRED_BY_DECISION: dict[str, str] = {
    "check-review-coverage.py": (
        "no longer waiting on a zero: #151 made it a RATCHET against "
        "docs/reviews/review-coverage-backlog.txt, so it exits 0 at "
        "whatever that file records and fails only when the unread set "
        "changes unrecorded. **The size is deliberately not retyped "
        "here**: it read 58 while the file held 43, a count decaying in "
        "prose exactly as DESIGN.md:1563-1566 says it will. It is "
        "unwired for a different reason now - it "
        "belongs on PULL REQUESTS against origin/main (a merge cannot "
        "record its own sha), and ci.yml is owned by another agent this "
        "run. Wire it with #153's widening, in one ci.yml change."
    ),
    "check-row-floor-control.sh": (
        "a control OF a control: it proves `check-row-floors.py` can still "
        "fail, by breaking a floor on purpose. Running it in CI would "
        "mutate the tree mid-job. Invoked by hand when the floor checker "
        "changes."
    ),
    "check-row-floor-controls.sh": (
        "the plural sibling of the above, same reason: it mutates floors "
        "to watch the checker fire. A control that must break its subject "
        "cannot share a job with the subject."
    ),
    "check-harness-result-controls.sh": (
        "proves `check-harness-result.sh` rejects malformed HARNESS-RESULT "
        "lines by feeding it malformed ones - it must break its subject, "
        "so it cannot share a job with it. Run by hand when the canonical "
        "line changes; 8/8 controls fire as of 2026-09-01."
    ),
    # ---------------------------------------------------------------
    # EVERYTHING BELOW ARRIVED WITH #153's WIDENING, 2026-09-01.
    #
    # These files did not change. The CONTAINER did: it was
    # `docs/reviews/check-*` and it is now every tracked `.py`/`.sh`
    # under `docs/reviews/` and `scripts/`. 52 members that had never
    # been asked for a reason were asked for one, and each reason below
    # is read out of the file it describes rather than inferred from
    # its name - the brief's own attempt to classify them by grepping
    # for `write_text|sed -i|cp` mislabelled `probe-coverage-ratchet.py`
    # as a tree-mutator when all nine of its arms write only into a
    # `TemporaryDirectory`. A static grep cannot see a write's target.
    #
    # MOST OF THESE ARE NOT GATES AND MUST NOT BECOME ONE. That is the
    # honest state of a reviews directory, and it is why the register
    # exists: an unwired file is fine, an unwired file nobody had to
    # justify is not.
    # ---------------------------------------------------------------
    #
    # -- CONTROLS THAT MUST BREAK THEIR SUBJECT ----------------------
    # A control that mutates the tree cannot share a job with the thing
    # it mutates. This is the same reason the four entries above carry,
    # and it is the largest single group.
    "probe-142-exempt-controls.py": (
        "plants a marker into real tracked files and runs the wired "
        "citation gates against them as subprocesses. It mutates the "
        "tree by design and restores by asking git; it cannot share a "
        "job with the gates it drives."
    ),
    "probe-audit-row-container.sh": (
        "deletes `result_status` lines from `src/` one at a time and "
        "runs the whole suite per row. A mutation sweep over shipped "
        "code cannot run in a job that is also testing that code."
    ),
    "probe-audit-shape-container.py": (
        "the #104 mutation sweep over `emit(...)`, `is_error=True` and "
        "`AuditPhase.X`. Same reason as the row container above: it "
        "edits `src/` per row and runs the suite each time."
    ),
    "probe-156-u1-landing-guard.sh": (
        "runs check-u1-boot-amputation.sh THREE times against scratch "
        "copies - pre-fix with a moved anchor, post-fix with a moved "
        "anchor, and post-fix intact - and scores on WHICH lines appear, "
        "because two of the three arms exit 1 and mean opposite things. "
        "It must move an anchor to measure anything, so it cannot share "
        "a job with the harness it controls. Run by hand when that "
        "harness's rows change; 3/3 arms as of 2026-09-01."
    ),
    "probe-audit-shape-controls.py": (
        "plants three `emit(...)` call sites into `src/` to prove the "
        "sweep's population is derived and not cached. It must break "
        "its subject, so it cannot share a job with it."
    ),
    "probe-bash-namespace-amputation.sh": (
        "deletes BASH-1's subject from the artifact it cites and "
        "requires `check-obligations.py` to go RED. An amputation of a "
        "wired gate cannot run beside that gate."
    ),
    "probe-ci-checker-steps-control.py": (
        "MUTATES `.github/workflows/ci.yml` to plant a bare interpreter "
        "and requires its subject to detect it. Its own docstring says "
        "why it is `probe-` and not `check-`: it must never share a job "
        "with the workflow it edits."
    ),
    "probe-floor-checker-planted-defect.sh": (
        "plants a defect into a subject harness's canonical line and "
        "requires `check-row-floor-controls.sh` to go red for the "
        "stated reason. It sets ROW_FLOOR_CONTROL_ALLOW_PLANTED=1 to "
        "get past the dirty-subject guard, which is exactly the state "
        "no CI job may be in."
    ),
    "probe-preflight-guards-refuse.sh": (
        "stages a change to each harness's own subject file and asserts "
        "the harness REFUSES. It deliberately leaves worktree == index "
        "mid-run, so it cannot share a checkout with anything else."
    ),
    "probe-r4-m5-n1-the-gates-can-fire.sh": (
        "renames a test so row A14 becomes vacuous, to watch the "
        "vacuous-row gate fire. It breaks its subject on purpose."
    ),
    "probe-r4-unmutated-anchors.sh": (
        "mutation rows against the shipped tool, one value at a time, "
        "running the whole suite per row. Same class as the audit "
        "containers."
    ),
    "probe-repoint-fail-closed.py": (
        "row E makes a real cited file unreadable with chmod and runs "
        "the real repoint tool against it. A job whose checkout has a "
        "chmod-ed file in it is a job with a bomb in it."
    ),
    "probe-wired-checker-amputation.py": (
        "amputates each construct in THIS file and reads which rows "
        "die. It cannot share a job with its subject, and its own "
        "docstring already recorded this exemption in prose: "
        "'NOT WIRED, deliberately'. Turning it into a "
        "`scripts/check-*.sh` harness under `ci-harness-gate.sh` is "
        "task #149, which is open."
    ),
    #
    # -- ONE-SHOTS WHOSE QUESTION IS SETTLED -------------------------
    # A tool whose question has been answered is a one-shot, and wiring
    # it would add a gate with nothing left to guard. Each names the
    # commit that ended it, so the claim is checkable.
    "apply-142-wire-register.py": (
        "one-shot: it wired #142's three exemption consumers onto the "
        "register and that landed at 76bc497. Kept because the edit is "
        "replayable and anchor-asserted, not because it still has work "
        "to do."
    ),
    "apply-short-summaries.py": (
        "one-shot for the B49b docstring sweep, which landed at "
        "f0c3764. It reads a hand-authored /tmp/summaries.tsv that no "
        "longer exists."
    ),
    "reflow-doc-lines.py": (
        "one-shot for the B49b reflow, landed at f0c3764. The property "
        "it established is now held by ruff's W505 at line 72, which "
        "IS wired."
    ),
    "split-long-summaries.py": (
        "one-shot for the B49b D205 summaries, landed at f0c3764. Same "
        "sweep, same end condition."
    ),
    "classify-w505.py": (
        "one-shot, and its own docstring says so at :210-215: the "
        "question 'is complying with B49b cheap, or does the clause "
        "need a scoped ADR?' was answered - 1608 violations, exemption "
        "list empty, sweep landed at f0c3764. Declared a one-shot at "
        "4ce55d3 (#23)."
    ),
    "adr-batch-repoint.py": (
        "ONE-SHOT for #95, stated in its own docstring. It exists so "
        "the repoint map is a runnable artefact rather than a paragraph "
        "claiming a map was built. The re-freeze it served landed at "
        "b079ae5."
    ),
    "adr-batch-verify-repoint.py": (
        "ONE-SHOT for #95, stated in its own docstring, and the "
        "verifier half of the pair above. Not the inverse of it, "
        "deliberately - it joins on TEXT so the instrument cannot agree "
        "with itself."
    ),
    "apply-143-consolidation.py": (
        "one-shot for #143's job consolidation, landed at ccbdaae. It "
        "asserts ci.yml's exact length (1637 lines) and twelve exact "
        "anchors as they stood at 9e04411, so it REFUSES on any later "
        "tree by construction - which is the behaviour it was built "
        "for, and it makes wiring meaningless."
    ),
    "apply-116-timeout-names.py": (
        "one-shot, stated in its own docstring: it has run, and the "
        "property it established is held from here by "
        "`scripts/check-timeout-literals.py`, which #153 wires in this "
        "same change. A one-shot whose successor is a live gate is the "
        "shape this register wants."
    ),
    #
    # -- REPORTING INSTRUMENTS THAT MUST NOT REFUSE ------------------
    # A gate refuses; these report. Wiring one would turn a number
    # somebody has to read into a build failure, which is how a real
    # measurement gets deleted rather than acted on.
    "measure-xref-population.py": (
        "its own docstring: 'IT IS NOT A GATE and must not become one. "
        "It reports; it does not refuse.' It re-derives #139's numbers "
        "so the next reader gets the same answer or a different one "
        "they can argue with. `check-cross-references.py` is the gate, "
        "and its population is deliberately narrower."
    ),
    "probe-167-mutation-site-census.py": (
        "a census, not a refusal: it counts every mutation site in every "
        "harness's Python heredocs by KIND, so the anchor checker's "
        "count can be compared against the container it samples from. "
        "It always exits 0 unless it cannot parse something, and a step "
        "that cannot fail is a step that guards nothing. The refusing "
        "half is `scripts/check-harness-anchors.py --floor`, which is "
        "wired. Kept runnable because the number it produces - 3 of 44 "
        "sites hidden at 22c9873 - is the evidence for #167's floor "
        "rise, and prose about a measurement decays into a claim about "
        "one."
    ),
    "probe-142-exempt-inventory.py": (
        "an inventory, not a refusal: it prints every REPOINT-EXEMPT "
        "line across BOTH citation gates' containers so the two numbers "
        "can be compared. The refusing half is the register, which is "
        "wired."
    ),
    "compare-harness-exit-codes.sh": (
        "takes two ledger paths as arguments and compares them on their "
        "intersection. There are no ledgers in a CI job to compare, and "
        "producing them is `probe-harness-exit-codes.sh`, which is "
        "hours of runtime."
    ),
    "probe-harness-exit-codes.sh": (
        "runs EVERY harness in the container to build a before/after "
        "ledger, with a default per-script timeout of 1800s. It is the "
        "instrument that reads the harnesses, not one of them, and its "
        "runtime is measured in hours."
    ),
    "probe-gate-swallowed-exceptions.py": (
        "the record of an R-round analysis of two S110 swallows in "
        "wired gates. Both were narrowed when it was written; this is "
        "the evidence for that ruling, re-runnable, not a condition to "
        "keep checking."
    ),
    "sample-134-citations.py": (
        "draws #134's random sample of citation sites at seed 134 so "
        "the verdicts can be checked against the sites they were "
        "written about. A sample draw is a record; a gate would mean "
        "failing the build when a random draw moves."
    ),
    "sample-135-complement.py": (
        "draws #135's complement sample at `26973a4^`, the one tree on "
        "which #126's 47-site population still exists. Pinned to a "
        "historical tree by necessity, so it can never be a statement "
        "about HEAD."
    ),
    #
    # -- THE MEASURING HALF: WIRE IT WHEN ITS BACKLOG IS ZERO --------
    # #125's discipline, which this project has now applied five times:
    # MEASURE, then fix, then wire. A gate wired while its backlog is
    # unknown lands red on its first run, and a gate that lands red is
    # one people learn to ignore. This repo has watched that happen for
    # 119 consecutive runs.
    "probe-midsentence-shape.py": (
        "the measuring half of a citation-shape rule whose backlog is "
        "320 of 881 (36.3%, #135). Wire it as `check-midsentence-shape` "
        "on the day that backlog is zero, not before. "
        "**ITS DOCSTRING'S STATED MECHANISM IS NOW WRONG AND MUST BE "
        "REWRITTEN**: it says it is named `probe-` 'so it cannot become "
        "a gate by accident', which relied on this checker's `check-*` "
        "prefix filter. #153 removed that filter. The name protects "
        "nothing now; THIS ENTRY is what keeps it out, and an entry is "
        "better because a reader can see it and argue with it."
    ),
    #
    # -- REACHED BY A DIFFERENT MECHANISM ----------------------------
    # Wired, but not through a `run:` body, so this checker's parser
    # cannot see it. Recorded rather than left to read as a hole.
    "probe-breaker-call-path.py": (
        "RUN IN CI, but by pytest rather than by a `run:` body: "
        "`tests/test_resilience.py` executes it, which its own "
        "docstring states as the point - a `circuitbreaker` bump that "
        "moves half-open expiry onto a background timer turns the suite "
        "red instead of leaving a stale paragraph behind. This parser "
        "reads `jobs.*.steps[].run` and cannot see a pytest import, so "
        "the exemption records a wiring that exists rather than one "
        "that does not."
    ),
    #
    # -- NEEDS AN ENVIRONMENT THE JOB DOES NOT HAVE ------------------
    "check-u1-pid1-shutdown.sh": (
        "needs Docker with NO `--init` so the interpreter is really "
        "PID 1, plus `docker stop -t 15` to deliver a real SIGTERM. "
        "`unshare --pid` is not permitted on this host (verified: "
        "'unshare failed: Operation not permitted'), so there is no "
        "lighter shape. UNSETTLED, not ruled: GitHub runners do have "
        "Docker, and nobody has measured what this costs or whether it "
        "is stable there. Handed back by #153 rather than wired blind."
    ),
    "probe-secrets-baseline.py": (
        "runs under `uv run --no-project --with detect-secrets==1.5.0`, "
        "a different environment from the job's locked one, and carries "
        "an amputation arm the checker cannot carry about itself. The "
        "fast synthetic half IS wired, as "
        "`check-secrets-baseline.py --controls`."
    ),
    "probe-uvicorn-body-limit.py": (
        "binds a real uvicorn server and streams a 2 MiB body at it, "
        "twice. It answered ADR-0029's open question - uvicorn has no "
        "body ceiling - and that answer is now held by the middleware "
        "and tests #81 built."
    ),
    "probe-scan-bounds.py": (
        "stands up two fake paging servers and drives a scan to its "
        "bound on each, one of which never advances. Minutes of "
        "wall-clock to re-derive an ADR-0024 answer that the wired "
        "record-ceiling tests now hold."
    ),
    "probe-r6-wait-burns-budget.py": (
        "arm 1 SLEEPS the whole outbound budget in real wall-clock to "
        "measure whether the `Retry-After` clamp burns it. Also has no "
        "shebang and no `__main__`: it is driven by hand, not executed."
    ),
    #
    # -- EVIDENCE FOR A CLOSED FINDING -------------------------------
    # Committed so a measurement stays re-derivable instead of decaying
    # into a claim that one was made. The finding is closed; the file
    # is the receipt.
    "probe-control-restore-guard.py": (
        "loads the PRE-FIX source out of git for its BEFORE arm. It is "
        "pinned to a historical blob by construction, so it measures "
        "the past and cannot gate the present."
    ),
    "probe-coverage-ref-resolves.py": (
        "reproduces R15-H1 by building an `init`+`fetch`+`detach` "
        "clone, the shape `actions/checkout` leaves. The defect is "
        "invisible in any normal clone because `git clone` CREATES a "
        "local `main`. UNSETTLED, not ruled: this looks wirable and "
        "cheap, and #153 did not run it. Handed back rather than wired "
        "on the strength of reading it."
    ),
    "probe-r14-manifest-marker.py": (
        "pins R14-H1: `check-settings-are-read.py` now sees the "
        "PUBLISHED manifest. The condition is asserted by that "
        "checker's own wired arm; this is the evidence the arm was "
        "needed."
    ),
    "probe-r4-h3-live-arm-cannot-detect.py": (
        "an OFFLINE substitute for a credentialed arm nobody can run - "
        "no one holds a Jobvite key, so the arm is marker-excluded and "
        "has never executed. It demonstrated the gap; the fix that "
        "closed it is in the suite."
    ),
    "probe-r6-arm1c-tautology.py": (
        "R6's analysis of whether another probe's arm 1c was a real "
        "control. It was not, and that was fixed. No shebang and no "
        "`__main__`; it is read and driven by hand."
    ),
    "probe-r6-breaker-reset.py": (
        "the R6 measurement that found the breaker RESETTING on a 4xx "
        "(#58 H1). Fixed at b42e34b, with the behaviour now asserted by "
        "`tests/test_resilience.py`. No shebang and no `__main__`."
    ),
    "probe-r6-post-escape.py": (
        "the R6 measurement of what escapes `request()` when a "
        "non-retryable method 5xxs. Closed; the type is now asserted in "
        "the suite. No shebang and no `__main__`."
    ),
    "probe-u12-f2-embedder-leak.py": (
        "measures what an embedder's log handler receives on the "
        "jobFeed route. It was INVERTED when ADR-0026 landed and the "
        "redaction install became idempotent; the live property is held "
        "by the wired log-redaction probe."
    ),
    "probe-set-e-vs-harness.sh": (
        "the positive control for ADR-0023's claim, and its ARM B is "
        "EXPECTED to exit non-zero - that IS the observation. A probe "
        "that cannot survive its own finding proves nothing, and a job "
        "step that must fail is a step that fails the job."
    ),
    "probe-coverage-ratchet.py": (
        "ten arms proving the #151 review-coverage ratchet fires in "
        "every direction it claims, all of them writing exclusively "
        "into a `TemporaryDirectory` - it does NOT mutate the tree, "
        "which #153's brief asserted from a grep and got wrong. It is "
        "unwired because its SUBJECT is: "
        "`check-review-coverage.py` belongs on pull requests, and a "
        "control has no job to share until the gate has one."
    ),
    #
    # -- TOOLS THAT WRITE, AND LIBRARIES THAT DO NOT RUN -------------
    "repoint-design-citations.py": (
        "it REWRITES citations across the tree - that is its whole "
        "purpose. A job step that rewrites the checkout is not a gate, "
        "it is an edit nobody reviewed. `check-design-citations.py` is "
        "the wired half that SAYS which citations moved."
    ),
    "restore-stranded-mutation.sh": (
        "a recovery tool: it puts back a mutation a SIGKILLed harness "
        "stranded, by reading the run-state file. It writes to the tree "
        "on purpose. Its `--check` mode is the read-only half and is "
        "reached through `ci-harness-gate.sh`."
    ),
    "repoint_exempt.py": (
        "a MODULE, not a script: it is the register that grants "
        "citation exemptions and it is imported by the gates that are "
        "wired. It has no `__main__` and running it does nothing."
    ),
    "harness-state.sh": (
        "a sourced LIBRARY - the one place the run-state file's path "
        "and format are derived. It is not executed; it is `source`d by "
        "the probes that own a mutation."
    ),
    "harness-result.sh": (
        "a sourced LIBRARY holding the one canonical HARNESS-RESULT "
        "line. No shebang, no `__main__`, executed by nothing: every "
        "harness `source`s it. `check-harness-result.sh` is the wired "
        "gate that reads what it emits."
    ),
    "probe-exception-redaction.py": (
        "task #15's finding, and it EXITS 1 BY DESIGN on the tree where "
        "it was written - 'At the time of writing it exits 1, which is "
        "the finding.' The defect was fixed at c54dc72 and the live "
        "property is held by the wired log-redaction probe. Wiring a "
        "file whose documented success condition is a failure is how a "
        "red gate gets switched off."
    ),
    #
    # -- THE ONE #153 RULED ON AGAINST ITS BRIEF ---------------------
    "probe-ci-checker-steps.py": (
        "**RULED, and #153's brief expected the opposite.** Its purpose "
        "is to execute ci.yml's checker steps VERBATIM so a local green "
        "means what a CI green means - its audience is the terminal "
        "BEFORE a push. Running it inside CI is a tautology: it would "
        "re-run, in the job, the very steps the job is already running, "
        "doubling the bill for no new signal, and it cannot fail in a "
        "way the real steps would not have failed first. The gap #155 "
        "names is real - its improvements only fire when a human types "
        "the command - but the remedy is a pre-push hook, not a CI "
        "step. Raised as its own task rather than settled here."
    ),
}

#: `check-design-citation-shape.py` was here, exempted while #126's 47
#: blank-END citations were swept. The sweep landed, it went green, it
#: was wired, and this entry was deleted in the same commit. That is the
#: exemption working as designed: a reason with a stated end condition,
#: removed when the condition ended rather than left to rot. Had it been
#: left, the stale-exemption check below would have failed the build -
#: which is the point of checking the reverse direction.


def _reasons_are_non_empty() -> None:
    """A blank reason is not an exemption."""
    blank = [k for k, v in UNWIRED_BY_DECISION.items() if not v.strip()]
    if blank:
        raise SystemExit(f"blank exemption reason(s): {blank}")


#: The container's BOUND. A container must be bounded somewhere; what
#: it must not do is filter by NAME inside the bound, because a name is
#: a thing an author picks. Adding a directory here is a decision;
#: adding a file to one of them is not.
CONTAINER_DIRS = ("docs/reviews", "scripts")

#: The KIND. A runnable script file, by suffix. `.md`, `.txt`, `.toml`
#: and the rest are not things that could be wired into a `run:` body,
#: so asking whether they are wired is not a question.
CONTAINER_SUFFIXES = (".py", ".sh")


def container() -> list[str]:
    """Every tracked runnable script under `CONTAINER_DIRS`, as paths.

    Enumerated from the CONTAINER, never a hand-kept list beside it -
    a list maintained next to the thing it describes is blind to the
    member nobody added, which is how three checkers went unwired.

    **AND NEVER BY NAME PREFIX**, which is the same defect wearing a
    container's clothes: the prefix `check-` was the filter here for
    months, and `probe-`, `measure-` and `sample-` files sat outside
    the population while this file printed that everything was wired.
    """
    done = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", *CONTAINER_DIRS],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        print(f"git ls-files failed: {done.stderr.strip()}")
        print("This is a BROKEN INSTRUMENT, not a finding. Exit 3.")
        raise SystemExit(3)
    return sorted(
        p
        for p in done.stdout.split()
        if pathlib.PurePath(p).suffix in CONTAINER_SUFFIXES
    )


def path_of() -> dict[str, str]:
    """Basename -> path, for the whole container.

    **The basename is the key everywhere below, and that is a claim
    this file has to earn.** A step invokes `docs/reviews/check-x.py`,
    so the basename is the substring to look for; but two directories
    can hold the same basename, and if they ever did, one member's
    wiring would silently answer for the other's. Control 6 asserts
    they do not collide. It is 123 distinct basenames over 123 paths at
    `2d886a4`; the day that stops being true, the control fails rather
    than the census quietly merging two files into one row.
    """
    index: dict[str, str] = {}
    for p in container():
        index.setdefault(pathlib.PurePath(p).name, p)
    return index


def checkers() -> list[str]:
    """Basenames of every container member.

    Derived from `container()` rather than re-running the enumeration,
    so the two can never answer different questions. A second selector
    that agreed today and drifted tomorrow is the shape #142 measured:
    two gates, two containers, and one number reported as if it were
    both.
    """
    #: THIS FILE IS IN ITS OWN POPULATION, deliberately - a checker that
    #: exempts itself from its own container is the precise blind spot
    #: it exists to catch. **That is ASSERTED by control 4, not claimed
    #: here**, because this comment was INERT when it was written: git
    #: lists only TRACKED files, the checker was still untracked, and it
    #: excluded itself for a reason no line of code mentions. The census
    #: read 26 and became 27 on the commit that tracked it.
    return sorted(pathlib.PurePath(p).name for p in container())


def strip_comments(body: str) -> str:
    """Drop shell comments, so a `#` line does not read as wired.

    This is the exact false positive that mislabelled three checkers
    twice. The rule is deliberately blunt: from an unquoted `#` to end
    of line. A `#` inside a quoted string would be over-stripped, which
    can only ever cause a FALSE 'unwired' - the safe direction for a
    gate whose job is to find things nobody wired.
    """
    return re.sub(r"(?m)(?<!\$)#.*$", "", body)


#: Shell operators that END one command and begin the next. A step body
#: is not one command: `out=$(python3 x.py 2>&1); rc=$?` is three, and
#: without this split the first token is `out=$(python3`, which no
#: interpreter test can match. Sixteen of ci.yml's checker steps are
#: written in exactly that capture-and-check shape.
_SEGMENT = re.compile(r"\$\(|`|\)|\(|&&|\|\||;|\||\{|\}|\n")

#: Runners that reach the PROJECT environment, so a `python` token after
#: one of them is NOT bare, however many flags sit in between.
#:
#: **This is a TOKEN test, and that is the whole fix.** The old form
#: was two negative lookbehinds, `(?<!uv run )(?<!uv run --frozen )`.
#: A Python lookbehind must be FIXED WIDTH, so it can spell exactly
#: one prefix and no other, so
#: exact prefix - `uv run  --frozen` with two spaces and
#: `uv run --frozen -- python` both slipped past it and were reported as
#: bare interpreters, failing the build for a reason that was not about
#: the code. Neither can be expressed as a lookbehind at all.
_PROJECT_RUNNERS = frozenset({"uv", "poetry", "pipenv", "hatch", "tox"})

#: A token that IS a bare interpreter, by basename: `python`, `python3`,
#: `python3.12`, and any path to one of them.
_INTERPRETER = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")

#: Interpreter options that consume the FOLLOWING token, so what comes
#: after them is an option ARGUMENT and not the script.
#:
#: `-X faulthandler` is why this set exists. "the first token after the
#: interpreter that does not start with `-`" - the obvious rule, and the
#: one suggested to me - picks `faulthandler` as the script and the
#: detector goes quiet again, one flag later.
_OPT_WITH_VALUE = frozenset({"-X", "-W", "--check-hash-based-pycs"})

#: Options after which there is no script path to find at all.
_OPT_NO_SCRIPT = ("-c", "-m")

#: `-m` modules that RUN A SCRIPT GIVEN FURTHER RIGHT, so `-m` does NOT
#: mean "no script path" for them.
#:
#: `python3 -m coverage run <checker>` executes the checker under a BARE
#: interpreter and ships the identical `ModuleNotFoundError` this file
#: exists to prevent - and it read SILENT until R14 measured it. It is
#: the next spelling of the founding defect: not exotic, just one the
#: rule had not been written against, exactly like the `-u` before it.
_MODULE_RUNNERS = frozenset({"coverage", "trace", "cProfile", "profile", "pdb"})


#: The script token must BE one of OURS, not merely contain the name.
#:
#: **THIS USED TO BE `^check-[\w-]+\.py$` AND THAT WAS THE SAME DEFECT
#: ONE COLUMN OVER.** Widening the population while leaving the
#: bare-interpreter arm matching `check-*` would have rebuilt the
#: prefix blindness inside the fix for it: a `probe-*.py` needing
#: `httpx2`, wired as bare `python3`, would ship the founding
#: `ModuleNotFoundError` and this arm would stay silent. Ten container
#: members need a third-party module and only one of them is a
#: `check-*` file.
#:
#: So membership in the container IS the test, and it is a set lookup
#: rather than a pattern - a pattern is the thing that keeps being
#: defeated by one flag here.
def _is_ours(name: str) -> bool:
    """Is this script token a member of our container?"""
    return name in path_of()


#: `import x` / `from x import ...` at the start of a line - top-level
#: imports only, which is where an unavailable module kills the process.
_IMPORT = re.compile(r"^(?:import|from)\s+([\w.]+)", re.MULTILINE)


def third_party_imports(name: str) -> list[str]:
    """Modules a checker imports that the stdlib does not ship.

    Local-only names are excluded: this asks what a BARE interpreter
    would fail to find, not what is merely unusual.
    """
    #: RESOLVED THROUGH THE CONTAINER, not by joining a hardcoded
    #: directory. This read `ROOT/"docs"/"reviews"/name` while the
    #: population was that one directory; the moment `scripts/` joined,
    #: that join returned a path that does not exist for every member
    #: of the new half - and this function answers `[]` for a path it
    #: cannot resolve. Every `scripts/` checker would have read
    #: 'stdlib-only', and the bare-interpreter arm would have gone
    #: silent about exactly the files the widening was for. A wrong
    #: ZERO that explains itself.
    #:
    #: **AND IT FALLS BACK TO THE TOKEN AS A PATH, WHICH IS NOT A
    #: CONVENIENCE.** If this resolved ONLY container members, it would
    #: share its entire domain with `_is_ours`, and the control that
    #: proves `_is_ours` is not `True` would be vacuous BY
    #: CONSTRUCTION: amputate the membership test and a non-member
    #: would still report no imports, so the row would stay silent
    #: either way. A control whose subject is selected through the
    #: construct it is testing kills nothing - this file already
    #: records that lesson one function down, and it applies here.
    relative = path_of().get(name, name)
    path = ROOT / relative
    if not path.exists() or path.suffix != ".py":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    found = {m.group(1).split(".")[0] for m in _IMPORT.finditer(text)}
    local = {p.stem for p in path.parent.glob("*.py")}
    return sorted(
        mod
        for mod in found
        if mod not in sys.stdlib_module_names
        and mod != "__future__"
        and mod not in local
    )


def _commands(text: str) -> list[list[str]]:
    """Every command in `text`, as a list of argv tokens.

    Segmented on shell operators first, then `shlex.split`. Tokenising
    is what makes the walk below flag-tolerant; a regex cannot be, which
    is the entire lesson of the defect this replaced.
    """
    out: list[list[str]] = []
    for chunk in _SEGMENT.split(text):
        stripped = chunk.strip()
        if not stripped:
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            #: An unbalanced quote inside ONE segment. A whitespace
            #: split keeps the command visible; dropping it would make
            #: the detector silently blind to exactly the body it could
            #: not parse, which is the failure shape this file is about.
            tokens = stripped.split()
        if tokens:
            out.append(tokens)
    return out


def _runner_script(rest: list[str]) -> str | None:
    """The script a `-m` runner module executes, if there is one.

    A runner takes its OWN sub-commands and options before the script,
    and they are not interpreter options: `coverage run <checker>` puts
    a bare `run` in the way. The interpreter walk in `_script_of` stops
    at the first token not starting with `-`, so handing it `rest` after
    the module name returns `run` - a plausible-looking answer that is
    not a script, and the row would pass for the wrong reason.

    R14's suggested fix did exactly that; it was measured before it was
    applied. So scan right instead, past options and sub-commands, for
    the first token that could BE a script. `.py` is the same suffix
    `_is_ours` implies for a `.py` member, so this narrows nothing.
    """
    for token in rest:
        if token.startswith("-"):
            continue
        if pathlib.PurePath(token).suffix == ".py":
            return token
    return None


def _script_of(tokens: list[str]) -> str | None:
    """The script a BARE interpreter in `tokens` runs, if there is one.

    `None` when the command runs no bare interpreter, when a project
    runner supplies the environment, or when `-c`/`-m` means there is no
    script path at all.
    """
    for i, token in enumerate(tokens):
        if not _INTERPRETER.match(pathlib.PurePath(token).name):
            continue
        if any(t in _PROJECT_RUNNERS for t in tokens[:i]):
            return None
        rest = tokens[i + 1 :]
        j = 0
        while j < len(rest):
            opt = rest[j]
            # `--` NEEDS NO BRANCH OF ITS OWN, and it used to have one.
            # The branch could only change the answer for a token
            # starting with `-`, and `_is_ours` rejects exactly
            # those - so no input existed for which it moved
            # `bare_python_steps`'s output, and deleting it killed no
            # control. The generic break below reaches the same token.
            if not opt.startswith("-") or opt == "-":
                break
            if opt.startswith(_OPT_NO_SCRIPT):
                after = rest[j + 1 : j + 2]
                if opt == "-m" and after and after[0] in _MODULE_RUNNERS:
                    return _runner_script(rest[j + 2 :])
                return None
            j += 2 if opt in _OPT_WITH_VALUE else 1
        return rest[j] if j < len(rest) else None
    return None


def bare_python_steps(text: str) -> list[tuple[str, list[str]]]:
    r"""Checkers run by a bare interpreter that need more than stdlib.

    **THIS EXISTS BECAUSE I SHIPPED EXACTLY THIS AND TURNED main RED.**
    Every other checker in `docs/reviews/` is stdlib-only, so the family
    convention is `run: python3 ...`. This one imports `yaml`; I tested
    it with `uv run`, wired it as `python3`, and my local `python3`
    happened to have pyyaml while the runner's did not. It died with
    `ModuleNotFoundError` on the commit that wired it.

    A convention that is safe for every existing member is not safe for
    the member that breaks the assumption the convention rests on.

    **AND IT WAS DEFEATED BY ONE FLAG FOR ITS WHOLE FIRST DAY.** The
    original was a regex whose path segment was `\S*?`, which cannot
    cross a space, so `python3 -u <checker>` - an ordinary thing to
    write for a step whose Actions output you want unbuffered -
    shipped the identical defect and this said nothing. Widening the
    regex was the tempting repair and it is the wrong one: `-\w+\s+`
    still misses `-X faulthandler`, and nothing pattern-shaped can
    cover `python3.12`.
    So the invocation is TOKENISED and walked instead. The spellings are
    controls in `--self-test`, one per spelling, including the negative
    arm - a detector that fires on everything is as useless as one that
    fires on nothing, and only the negative arm tells them apart.
    """
    problems: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for tokens in _commands(text):
        script = _script_of(tokens)
        if script is None:
            continue
        name = pathlib.PurePath(script).name
        if not _is_ours(name) or name in seen:
            continue
        #: The TOKEN, not the basename. A container member resolves
        #: either way, but the negative control's subject lives outside
        #: the container and only its written path can find it.
        needed = third_party_imports(script)
        if needed:
            seen.add(name)
            problems.append((name, needed))
    return problems


def wired_names(text: str) -> set[str]:
    """Basenames that appear as a real TOKEN in a run body.

    **THIS WAS `name in text`, A BARE SUBSTRING, AND #153's WIDENING
    PROVED IT UNSOUND ON THE FIRST RUN.**
    `scripts/lib/harness-result.sh` read WIRED because
    `docs/reviews/check-harness-result.sh` is invoked at `ci.yml:272`
    and the shorter name is a SUBSTRING of the longer one. A member
    reported as wired because a DIFFERENT member's name contains it is
    a false GREEN - the direction this file exists to prevent - and it
    was invisible while every member was `check-*` with names that
    happened not to nest.

    The old test survived only because its population was small enough
    for the collision not to have happened yet. That is not a property
    anyone chose; it is one that expired.

    So the bodies are TOKENISED - the same `_commands` walk the
    interpreter test uses, which is already the sound instrument in
    this file - and a name counts as wired when it is the BASENAME of
    an actual argv token. `check-harness-result.sh` and
    `harness-result.sh` are different tokens, and a token cannot be
    half of another one.
    """
    seen: set[str] = set()
    for tokens in _commands(text):
        for token in tokens:
            seen.add(pathlib.PurePath(token).name)
    return seen


def run_bodies() -> tuple[str, int]:
    """Every `jobs.*.steps[].run` in every workflow, comment-stripped.

    Returns the concatenated text and the number of run steps seen. The
    count exists so a parse that silently yields nothing cannot report
    'nothing is wired' with a straight face.
    """
    bodies: list[str] = []
    steps = 0
    for path in sorted(WORKFLOWS.glob("*.yml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            continue
        for job in (loaded.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    steps += 1
                    bodies.append(strip_comments(step["run"]))
    return "\n".join(bodies), steps


def _control_subjects() -> tuple[str, str]:
    """A checker needing a third-party module, and one that does not.

    **DERIVED from the population, never named.** A name written into
    the control here would invert SILENTLY the day that checker's
    imports changed - the row would keep printing PASS while
    asserting the opposite of what it says. That is the same failure
    the census itself is built to avoid, one level up.
    """
    #: PATHS, not basenames, because the container spans two
    #: directories now and `docs/reviews/{name}` was a hardcoded join
    #: that would have built control bodies naming files that do not
    #: exist the moment the chosen subject came from `scripts/`.
    pys = [p for p in container() if p.endswith(".py")]
    needs = [p for p in pys if third_party_imports(p)]
    stdlib = [p for p in pys if not third_party_imports(p)]
    if not needs or not stdlib:
        raise SystemExit(
            "cannot build the spelling controls: the population holds "
            f"{len(needs)} member(s) needing a third-party module and "
            f"{len(stdlib)} stdlib-only. Both arms need at least one; "
            "without the stdlib arm a detector that fires on EVERY "
            "line would pass every row below."
        )
    return needs[0], stdlib[0]


def _non_member_subject() -> str:
    """A real `.py` OUTSIDE the container that needs a third party.

    This is the subject of the `_is_ours` control, and it has to be a
    file that EXISTS: `third_party_imports` returns `[]` for a path
    that does not resolve, so a fabricated name stays silent whatever
    `_is_ours` does and the row would kill nothing. (R14 suggested a
    fabricated `notacheck-...py`; measured, it kills nothing.)

    **AND IT MUST BE OUTSIDE THE CONTAINER, which is a CHANGE, not a
    rewording.** The old subject was a `docs/reviews/` file that merely
    did not start with `check-`. Under the widened population every
    such file is now a MEMBER, so that subject would fire rather than
    stay silent and the control would assert the opposite of what it
    says. The discriminator moved from the name to the container, so
    the control's subject has to move with it - a control that keeps
    its old subject across a rule change is the shape that goes on
    passing while testing nothing.

    Selected by walking `src/`, which is the one tree here that is
    neither container nor test and is guaranteed to import `httpx2`.

    **THE MEMBERSHIP TEST HERE IS `path_of()` DIRECTLY, DELIBERATELY
    NOT `_is_ours`, and that is not a style choice - it was MEASURED.**
    The first version of this function called `_is_ours` to skip
    container members. Arm C of `probe-wired-checker-amputation.py`
    amputates `_is_ours` to always-True; every file then looked like a
    member, this function found no subject at all, and it raised
    `SystemExit` instead of producing a failing row. A control that
    selects its own subject THROUGH the construct it is testing does
    not fail when that construct dies - it disappears, which reads as
    an instrument error rather than a kill. The predecessor of this
    function carried the same warning about `_CHECKER_NAME`, and I
    reintroduced the defect one identifier over while rewriting it.
    """
    members = path_of()
    for path in sorted((ROOT / "src").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if path.name in members:
            continue
        if third_party_imports(relative):
            return relative
    raise SystemExit(
        "cannot build the `_is_ours` control: no `.py` outside the "
        "container imports a third-party module. Without one, nothing "
        "separates 'the script token must BE one of ours' from 'any "
        "script token will do'."
    )


def _spelling_controls() -> list[tuple[str, bool]]:
    """One `(step body, must it fire?)` pair per interpreter spelling.

    The positive rows are the ways a bare interpreter can be spelled;
    every one of them ships the `ModuleNotFoundError` this file exists
    to prevent, and the regex this replaced caught only four of them.

    The `uv` rows are the FALSE-POSITIVE direction: a safe invocation
    reported as bare fails the build for a reason that is not about the
    code, which is how the two-space form (`uv run  --frozen`) behaved.

    The last two rows are the NEGATIVE ARM and they are the load-bearing
    ones. Every positive row above would also pass for a detector that
    simply returned True for any line containing a checker name. Only a
    stdlib-only checker, invoked bare, staying SILENT separates a
    detector from a rubber stamp.
    """
    needs, stdlib = _control_subjects()
    notamember = _non_member_subject()
    return [
        # Bare interpreters. All must fire.
        (f"python3 {needs}", True),
        (f"python {needs}", True),
        (f"python3 -u {needs}", True),
        (f"python3 -X faulthandler {needs}", True),
        (f"python3 -B {needs}", True),
        (f"python3.12 {needs}", True),
        (f"/usr/bin/python3 {needs}", True),
        (f"env python3 {needs}", True),
        (f"python3 -- {needs}", True),
        (f"python3 {needs} --self-test", True),
        (f"out=$(python3 {needs} 2>&1); rc=$?", True),
        # The directory is DERIVED from the chosen subject. It was
        # hardcoded `cd docs/reviews`, which stops being the subject's
        # directory the moment the container spans two of them.
        (
            f"cd {pathlib.PurePath(needs).parent} && "
            f"python3 {pathlib.PurePath(needs).name}",
            True,
        ),
        # THE OTHER TWO MEMBERS OF `_OPT_WITH_VALUE`. Only `-X` was
        # covered, so the set could be reduced to `{"-X"}` and every
        # control still passed. A set with an uncovered member is a
        # list nobody is checking the rest of.
        (f"python3 -W error {needs}", True),
        (f"python3 --check-hash-based-pycs always {needs}", True),
        # THE RUNNER IDIOM. `-m` normally means there is no script, but
        # these run one, under a bare interpreter, with the third-party
        # import unavailable. All three read SILENT until R14. This row
        # is also the ONLY thing standing behind `_OPT_NO_SCRIPT`: see
        # the `-m pytest` row below, which does not do that job.
        (f"python3 -m coverage run {needs}", True),
        (f"python3 -m cProfile -o /tmp/prof.out {needs}", True),
        # The project environment. None may fire.
        (f"uv run python {needs}", False),
        (f"uv run --frozen python {needs}", False),
        (f"uv run  --frozen python {needs}", False),
        (f"uv run --frozen python3 {needs}", False),
        (f"uv run --frozen -- python {needs}", False),
        # No interpreter at all, and no script to find.
        (f"{needs}", False),
        # NOT A CONTROL FOR `_OPT_NO_SCRIPT`, THOUGH IT LOOKS LIKE ONE.
        # Empty `_OPT_NO_SCRIPT` and the walk yields `pytest`, which
        # `_is_ours` rejects - so this row passes either way, for a
        # reason that has nothing to do with the `-m` guard. It sat in
        # the space where the real control belonged, which is worse
        # than an empty space. `-m coverage run` above is the control.
        ("python3 -m pytest", False),
        # THE NEGATIVE ARM. A stdlib-only member must stay silent.
        (f"python3 {stdlib}", False),
        (f"python3 -u {stdlib}", False),
        (f"/usr/bin/python3 -X faulthandler {stdlib}", False),
        # A REAL SCRIPT THAT IS NOT ONE OF OURS. Without this the
        # membership test could be `True` and nothing would notice:
        # every other negative row is a file that is either stdlib-only
        # or does not exist, so none of them can see the difference.
        # The subject is a `src/` module - it EXISTS and it needs
        # `httpx2`, so the ONLY thing keeping this row silent is that
        # it is not in the container.
        (f"python3 -u {notamember}", False),
    ]


def self_test() -> int:
    """Controls, each aimed at a way this checker could lie."""
    text, steps = run_bodies()
    failures: list[str] = []

    # 1. A name I have read a step for must read WIRED. Without this the
    #    parser could return nothing and every answer would be
    #    'unwired'.
    invoked = wired_names(text)
    if "check-design-citations.py" not in invoked:
        failures.append("check-design-citations.py is wired but reads UNWIRED")

    # 2. A name that exists nowhere must read UNWIRED. A checker that
    #    finds everything is as useless as one that finds nothing.
    if "check-a-name-nobody-has-written.py" in invoked:
        failures.append("a fabricated name reads WIRED")

    # 2b. A NAME THAT IS ONLY A SUBSTRING OF A WIRED ONE MUST READ
    #     UNWIRED. This is not hypothetical and it is not a nit:
    #     `scripts/lib/harness-result.sh` read WIRED under the old
    #     `name in text` test because `check-harness-result.sh` is
    #     invoked at ci.yml:272 and contains it. A FALSE GREEN, found
    #     by #153's widening on its first run, and invisible for as
    #     long as the population happened to hold no nested names.
    #
    #     The subject is BUILT BY CONCATENATION from a name that really
    #     is wired, so this row cannot go stale by pointing at a file
    #     somebody renamed - it re-derives the collision every run.
    real = "check-design-citations.py"
    if real not in invoked:
        failures.append("control 2b's premise failed: its subject is not wired")
    elif real[len("check-") :] in invoked:
        failures.append(
            f"`{real[len('check-') :]}` reads WIRED, but it is only a "
            f"SUBSTRING of `{real}`. The wiring test is matching text, "
            "not tokens."
        )

    # 3. The comment strip must actually strip. This is THE defect that
    #    produced two wrong censuses, so it gets a control of its own.
    if "zzz" in strip_comments("echo hi  # zzz\n"):
        failures.append("strip_comments left a commented name behind")

    # 4. THIS FILE MUST BE IN ITS OWN POPULATION, asserted rather than
    #    commented. The comment in `checkers()` claimed it already was,
    #    and the claim was INERT when I wrote it: `git ls-files` lists
    #    only TRACKED files, and the checker was still untracked, so it
    #    excluded itself for a reason the code never mentions. The
    #    census
    #    read 26 and silently became 27 on the commit that tracked it.
    #    A rename that stops matching the glob would do the same thing.
    me = pathlib.Path(__file__).name
    if me not in checkers():
        failures.append(f"{me} is NOT in its own population")

    # 5. ONE CONTROL PER INTERPRETER SPELLING, WITH A NEGATIVE ARM.
    #    The detector this replaced was a regex, and it was defeated by
    #    a single `-u` for its whole first day - in the function whose
    #    docstring says it exists because that exact defect turned main
    #    red. There is no spelling below that a reader can look at and
    #    call unreasonable, and that is the point: the failure was never
    #    an exotic invocation, it was an ordinary one the pattern had
    #    not been written against.
    spellings = _spelling_controls()
    for body, must_fire in spellings:
        fired = bool(bare_python_steps(body))
        if fired != must_fire:
            wanted = "fire" if must_fire else "stay silent"
            failures.append(f"spelling `{body}` should {wanted}, got fired={fired}")

    # 6. NO BASENAME COLLISIONS. The basename is the key everywhere in
    #    this file, and that is safe only while it is unique across the
    #    container. Two directories, two chances to hold the same name -
    #    and if they ever did, one member's wiring would silently answer
    #    for the other's, which is a WRONG GREEN rather than a wrong
    #    red. Asserted, because the widening is what made it possible.
    paths = container()
    seen_names: dict[str, str] = {}
    for p in paths:
        n = pathlib.PurePath(p).name
        if n in seen_names:
            failures.append(f"basename collision: {seen_names[n]} and {p}")
        seen_names[n] = p

    # 7. THE CONTAINER SPANS BOTH DIRECTORIES AND BOTH PREFIXES.
    #    Without this, `CONTAINER_DIRS` could be trimmed back to
    #    `docs/reviews` and every control above would still pass: the
    #    spelling rows derive their subjects FROM the container, so they
    #    move with it. A population that shrinks quietly is exactly the
    #    defect #153 fixed, and it must not be able to come back by an
    #    edit no control notices.
    if not any(p.startswith("scripts/") for p in paths):
        failures.append("the container holds NOTHING under scripts/")
    if not any(pathlib.PurePath(p).name.startswith("probe-") for p in paths):
        failures.append("the container holds NO probe-* member")
    if not any(pathlib.PurePath(p).name.startswith("check-") for p in paths):
        failures.append("the container holds NO check-* member")

    # 8. A SET, NOT A COUNT. `main` partitions the container into wired,
    #    excused and unexplained; assert here that the partition is
    #    exhaustive and disjoint. A count lets one member entering and
    #    another leaving cancel - #151 measured that exact cancellation
    #    on the coverage ratchet, and it is why that gate is a set.
    text_now, _ = run_bodies()
    names_now = set(checkers())
    invoked_now = wired_names(text_now)
    wired_now = {n for n in names_now if n in invoked_now}
    unwired_now = names_now - wired_now
    excused_now = {n for n in unwired_now if UNWIRED_BY_DECISION.get(n, "").strip()}
    unexplained_now = unwired_now - excused_now
    if wired_now | excused_now | unexplained_now != names_now:
        failures.append("the three buckets do not cover the container")
    if wired_now & excused_now or wired_now & unexplained_now:
        failures.append("the buckets overlap; a member is counted twice")

    total = 8 + len(spellings)
    # NAME THE CONTAINER BESIDE THE COUNT (R14 review, L-1). This
    # walks EVERY workflow; probe-ci-checker-steps.py pins ci.yml
    # alone. Both were right and neither said so, so 80 vs 78 read
    # as a contradiction and cost a reviewer a detour to settle.
    parsed_from = ", ".join(sorted(w.name for w in WORKFLOWS.glob("*.yml")))
    print(f"run steps parsed: {steps}  (across {parsed_from})")
    for line in failures:
        print(f"  CONTROL FAILED: {line}")
    if failures:
        print(f"\n{len(failures)} of {total} control(s) failed. The instrument")
        print("is wrong.")
        return 1
    print(f"{total}/{total} controls passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="are the checkers wired?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    _reasons_are_non_empty()
    if args.self_test:
        return self_test()

    names = checkers()
    if not names:
        print("MATCHED ZERO checkers. An empty population reports full")
        print("coverage, which would mean nothing here. Exit 2.")
        return 2

    text, steps = run_bodies()
    if steps == 0:
        print("PARSED ZERO run steps out of the workflows. Every checker")
        print("would read as unwired for a reason that is not about the")
        print("checkers. This is a BROKEN INSTRUMENT. Exit 3.")
        return 3

    invoked = wired_names(text)
    wired = [n for n in names if n in invoked]
    unwired = [n for n in names if n not in invoked]

    excused = [n for n in unwired if UNWIRED_BY_DECISION.get(n, "").strip()]
    unexplained = [n for n in unwired if n not in excused]
    stale = [n for n in UNWIRED_BY_DECISION if n in wired]
    unknown = [n for n in UNWIRED_BY_DECISION if n not in names]

    #: SET EQUALITY, NOT A COUNT. Every member must land in exactly one
    #: of the three buckets, and the three together must BE the
    #: container. A count would let one member entering and another
    #: leaving cancel to the same total while the sets diverged - the
    #: exact shape #151 measured on the coverage ratchet. This is an
    #: assertion about the partition, so a future edit that drops a
    #: member from every bucket fails here rather than reporting a
    #: smaller, quieter, greener population.
    examined = set(wired) | set(excused) | set(unexplained)
    if examined != set(names):
        missing = sorted(set(names) - examined)
        extra = sorted(examined - set(names))
        print("THE EXAMINED SET IS NOT THE ENUMERATED SET. Exit 3.")
        print(f"  enumerated but not examined: {missing}")
        print(f"  examined but not enumerated: {extra}")
        print("This is a BROKEN INSTRUMENT, not a finding.")
        return 3

    dirs = ", ".join(f"{d}/" for d in CONTAINER_DIRS)
    kinds = ", ".join(CONTAINER_SUFFIXES)
    print(f"Container: tracked {kinds} under {dirs}")
    print(f"Members: {len(names)}")
    print(f"Run steps parsed from {WORKFLOWS.name}/: {steps}")
    print(f"WIRED: {len(wired)}")
    print(f"UNWIRED, with a stated reason: {len(excused)}")
    for name in excused:
        print(f"  EXEMPT   {name}: {UNWIRED_BY_DECISION[name]}")

    problems = False
    if unexplained:
        problems = True
        print(f"\n{len(unexplained)} checker(s) are UNWIRED and unexplained:")
        for name in unexplained:
            print(f"  {name}")
        print(
            "\nAn unwired checker is a claim of coverage nobody can see is\n"
            "false. Either wire it - after measuring it GREEN, because a\n"
            "gate that lands red is one people learn to ignore - or add it\n"
            "to UNWIRED_BY_DECISION with the reason."
        )

    if stale:
        problems = True
        print(f"\n{len(stale)} exemption(s) name a checker that IS wired:")
        for name in stale:
            print(f"  {name}")
        print("The reason has outlived the condition. Delete the entry.")

    bare = bare_python_steps(text)
    if bare:
        problems = True
        print(f"\n{len(bare)} checker(s) run by a BARE interpreter but need")
        print("more than the standard library:")
        for name, needed in bare:
            print(f"  {name}  needs {', '.join(needed)}")
        print(
            "\nA bare `python3` reaches only the standard library. The step\n"
            "passes wherever the module happens to be installed and dies\n"
            "with ModuleNotFoundError on a clean runner. Use\n"
            "`uv run --frozen python ...`, and declare the module in\n"
            "pyproject's dev group - a transitive dependency is a fact\n"
            "nobody promised you."
        )

    if unknown:
        problems = True
        print(f"\n{len(unknown)} exemption(s) name a file that does not exist:")
        for name in unknown:
            print(f"  {name}")
        print("A renamed or deleted checker leaves its exemption behind.")

    if problems:
        return 1

    print("\nEvery checker is wired, or unwired for a recorded reason.")
    print("NOTE: this proves each is INVOKED, not that its exit code gates")
    print("the job. A step that runs a checker and swallows its status")
    print("reads as WIRED here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
