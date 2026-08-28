# Draft 7 self-audit — six defects the AUTHOR found in his own draft

**Author:** `impl-plan-draft7`. **Date:** 2026-08-28. **Subject:** `docs/plans/IMPLEMENTATION-PLAN.md`
at draft 7, uncommitted.

**Why this file exists rather than the fixes being applied.** `plan-review-r6` is reading the plan
right now. Editing it mid-review would make that round's `file:line` citations stale and is the
"parallel reviewers on one checkout void each other's work" failure this project has already paid
for. **These corrections are held for draft 8 and folded in with round 6's findings.** They are
written down rather than carried in one agent's context because draft 6's author was killed
mid-session holding exactly this kind of pending state, which is why round 5 sat unapplied for six
commits.

**Every one of these is the same failure: a specific number asserted rather than counted.** None was
found by reading the prose. All six came from running `git log`, `git show --numstat` and `ls`
against the claims.

| # | Where | Claim | What is actually true |
|---|---|---|---|
| 1 | `:5`, `:15`, `:1717` | *"seven commits"* went in on top of round 5 | **Five** at the moment draft 7 was written (`299cf8b..ff0bbdf`), **six** now — `5519032` landed during the session. Seven was never true at any moment |
| 2 | `:41` | *"Six of its nine defects have since been fixed in the tree (`2d2e1a3`, `ff0bbdf`)"* | **All nine are disposed of.** F-1/F-2/F-3/F-6/F-7 in `ff0bbdf`, F-4 and C-2 in `2d2e1a3`, F-5 in `35de193`, and C-1 in `5519032` (checkout to `@v6`, with setup-uv's `@v5` deviation recorded as **ADR-0016** rather than silently kept). The attribution omits two commits and the count understates by three |
| 3 | `:465` | `db5c21e` repaired *"one line"* of `scripts/check-u0-test-controls.sh` | `git show --numstat` says **6 insertions, 1 deletion**. I propagated `U15-REPORT.md`'s own *"modified, 1 line"* table cell without checking the diff behind it |
| 4 | `:1717` | gates re-run *"at `ff0bbdf`"* | True when measured and **stale now**: HEAD is `5519032`. That commit touches only `ci.yml` and `docs/adr/`, so no gate or suite number moves — but the SHA a measurement is pinned to is the whole point of pinning it |
| 5 | `:1635` | §8: *"I read `DESIGN.md` end to end, **all eleven ADRs**"* | There are **sixteen**. Five postdate that reading, and **two of them are Accepted** — ADR-0015 (licence gate is a deny-list) and **ADR-0016**. 0012-0014 are Proposed. An Accepted ADR is authority beside the frozen design, so this is a **coverage overclaim in the very section that exists to bound coverage** |
| 6 | `:468` | `ff0bbdf` closed *"five"* `COMPLIANCE-SPEC-PASS` findings | Correct as far as it goes (F-1, F-2, F-3, F-6, F-7) and consistent with the commit's own subject line — **kept, listed here only so the recount in #2 does not silently contradict it** |

## The one that is a real finding rather than a typo

**#5.** Substantively the plan does track the late ADRs — 0012 is named in collision 8, 0013 is Q6,
0014 is behind U0's secret-class-not-emptiness passage, 0015 is described correctly in U0's licence
paragraph. **So the defect is not that the plan ignores them; it is that §8 states a bounded claim
about what was read, and the bound is false.** That section's whole job is to stop an unstated
omission reading as coverage, which makes a wrong number there worse than a wrong number elsewhere.

**Suggested fix for draft 8 (my suggestion, verify before adopting):** state sixteen, name the five
that postdate the reading with their statuses, and say which of them have since been reflected in
the plan and by whom — rather than silently bumping eleven to sixteen, which would assert a reading
that never happened.

## What this says about the draft, stated plainly

Draft 7 fixed round 5's six findings and **introduced five numeric errors of its own**, four of them
in the header paragraph whose subject is the danger of stale numbers. That is not ironic, it is the
mechanism: **the passages that recount history are the ones with the most uncounted numbers in
them**, because narrating a sequence invites rounding it. The plan already carries this lesson about
the controls harness ("21, 32 and 34 to three readers") and about the collision count, and the author
still did it four times in one paragraph.

**No finding here changes a unit, a dependency, an ownership row or a verification arm.** Draft 7's
substance stands; its arithmetic does not. Nothing here should stop U2 or any unit now in flight.
