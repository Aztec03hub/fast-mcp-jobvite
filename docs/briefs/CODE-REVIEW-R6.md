# CODE-REVIEW-R6 - U7, the unit the plan calls the riskiest

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r6`. Your report goes to `docs/reviews/REVIEW-R6.md`, committed on
branch `review/r6`. **You are READ-ONLY on `src/`, `tests/` and `scripts/`.**

## Why this round exists

**U7 is merged at `ec38835` and nobody has reviewed it.** `§6` of the plan names it **the riskiest
unit**, and `DESIGN.md:64-68` names the circuit breaker as one of two mechanisms **never executed**,
sitting among measured results and borrowing their credibility - a state U7's tests were supposed to
end.

It was built well. The breaker rejection test carries a positive control on its own search; two of
its own probe arms were wrong on the first run and it caught both; two harness rows paid for
themselves before the first green run. **Every unit reviewed on this project has produced a High, and
the carefully-built ones produced the sharpest.**

## Where to look first: its own ledger of what it did NOT execute

`docs/worklogs/U7-IMPL-REPORT.md` §3 is an unusually honest list. **Start there and attack the
boundary**, not the list itself:

- *"The 30-second recovery window is never waited out at its real length"* - the `open->half_open`
  case shortens `_recovery_timeout` to `0.01s`. **What does that shortening also change?** A timeout
  that small can make a transition fire for a reason the real one would not.
- *"An exhausted budget does not count toward the breaker."* Executed - **but check the converse: can
  a breaker-refused call consume budget?**
- *"In-process, per-replica breaker state."* Inherited from the library and untested.
- *"429 has never been observed from Jobvite."* The path is exercised, by us, against our own script.

## The claims worth attacking, because the unit rests on them

1. **The rejection test's conclusion.** `circuitbreaker 2.1.3` evaluates half-open expiry on the call
   path. The probe's arm 1 is a **grep that returns nothing**, made meaningful by arm 1c, a positive
   control proving the search term is findable. **Is arm 1's term list the right list?** A scheduling
   mechanism it does not name would pass silently.
2. **`create_candidate` is excluded from retry BY CONSTRUCTION, via HTTP-method dispatch.** Find the
   path where a non-idempotent call reaches the retrying branch anyway - a POST that is not
   `create_candidate`, or a retry wrapper applied above the dispatch.
3. **One scan shares one budget.** A2 was VACUOUS until U7 noticed every other budget case drove a
   single request. **Look for the same shape elsewhere**: an assertion whose fixture cannot reach the
   branch it guards.
4. **A5 is admitted vacuous behaviourally and killed structurally** - `_attempt`'s pre-attempt budget
   check subsumes `stop_after_delay`, so the two caps `backend/resilience.md:88-90` requires cannot
   be separated by driving calls. **Is "structurally killed" enough, or does one of the two caps have
   no behavioural evidence at all?**

## The shapes that have produced findings here

Each has produced a real finding on this project, most more than once.

1. **A control that is not wired.** U7's two harnesses ARE wired (`ec38835`) - verify, do not assume.
2. **A green that tested nothing** - a skip, a selector matching nothing, an assertion passing
   against an absent file, a grep at a path that does not exist.
3. **A test NAME is an unverified claim about its BODY.**
4. **A hand-kept list beside the container it describes.** EIGHT instances here.
5. **The positive control depends on the defect.**
6. **Fail-closed on error still fails OPEN on empty.** Resilience is full of empties: a zero-length
   `Retry-After`, a `None` deadline, an exception with no status. **What does each do?**
7. **A constant a test reads the same way the code does**, so the assertion moves with the value.

## What is already known, so you do not re-derive it

- **`outbound_rate_limit` is read by nothing and the self-throttle does not exist.** ADR-0025
  (Proposed) records it, and `docs/reviews/check-settings-are-read.py` gates it with that exemption.
  **Not a finding.** A finding that the ADR's arithmetic is wrong IS one.
- **`scan()` has no bound.** ADR-0024 (Proposed). Not a finding; its interaction with the budget is.
- **60s, 5 retries and 30s recovery are CHOICES, not measurements**, and are recorded as such. A
  finding that one is wrong needs evidence about Jobvite, which nobody has.
- R5-M2 and R5-N1 were fixed at `2fd3892`; **R5-H3 is deliberately still open** and is not yours.

## What you may not do

- **No edits to `src/`, `tests/` or `scripts/`.** `u8-candidates` and `u9-http` are both live.
  **Review the merged state at `ec38835`**, cite against it with `git show ec38835:<path>`, and
  expect the working tree to move under you. Say which SHA every finding is against.
- **Do not run a mutation harness against the shared checkout.** Pin `ec38835` in your own worktree.
  A harness owns the tree for its whole run, and two agents are editing this one.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. A defect there is a **Proposed** ADR in your report.

## Every finding ships with a suggested fix

At every severity, nits included. Rank by severity, cite `file:line` from `grep -n` or a numbered
read, and state the failure each produces. **A surviving mutation is the strongest finding you can
bring me.**

**End with what you did NOT verify**, and keep that for what you could not settle rather than what
you did not try.
