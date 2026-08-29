# CODE-REVIEW-R7 - four merged units nobody has reviewed

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r7`. Your report goes to `docs/reviews/REVIEW-R7.md`, committed on
branch `review/r7`. **You are READ-ONLY on `src/`, `tests/` and `scripts/`.**

## The subject: U8, U9, U12 and U10, all merged, none reviewed

**Review the merged state at `bc0f958`.** `u14-arguments` is live in the input models of
`tools/jobs.py` and `tools/candidates.py`, so **read with `git show bc0f958:<path>` and say which SHA
every finding is against.** A citation read off the working tree will be wrong within the hour.

Every unit reviewed on this project has produced a High, and the carefully-built ones produced the
sharpest. All four of these were built carefully.

## Start where each unit says it stopped

Each report ends with what it could not settle. **That list is a map of where to push**, not a list
to re-read:

- **U8** wrote its positive control before any source file existed, and row A1 measures that **52 of
  56 assertions survive a tool returning an empty page.** It corrected the plan in BOTH directions -
  and found that **§8 #5 survives A1**, because the PII it asserts absent was never an ARGUMENT: it
  is in the RESPONSE, and the audit event records arguments. **That is still open.** Is it the only
  case of that shape?
- **U9** owns the unit **no §8 case backs**, so a deleted test there leaves every gate green. Its
  five middleware-absence assertions are made meaningful by a presence control - **check that the
  control actually covers all three adopted middleware**, and that `include_payloads=False` is
  asserted rather than merely passed.
- **U12** proved its C5-I1 arm against a stream proven non-empty by three producers, including
  httpx2's own record. **Its exception-message arm was never built** - a jobFeed timeout's `detail`
  is not asserted to carry no `sc=`. It said so.
- **U10** is the write. Its wording rule is a TEST that scans for claims a human approved something.
  **Attack that scanner**: it reads each hit with the text before it so a denial is not a claim, and
  assembles patterns from fragments so it does not match itself. Both are clever and both are places
  a false negative hides.

## The claims most worth attacking

1. **U10's era discriminator.** `protocol_version`, not `ctx.transport` or `session_id` - both of
   which are populated on BOTH eras and are measured traps. The assertion that the discriminator IS
   `protocol_version` exists. **Can it pass against an implementation that reads the right attribute
   and then ignores it?**
2. **U10's `send_email` default.** A mutation survived here because the field carried
   `Field(default=False)` AND `= False`, and pydantic takes the assignment - so the mutation flipped
   an inert copy. **That was fixed on three fields. Is there a fourth anywhere in the repository?**
3. **U9's per-client rate limiting.** The framework default keys everyone to the literal `"global"`.
   The negative control proves a bystander fails with that exact message. **Is the positive arm
   sequential-only, and does anything claim otherwise?**
4. **U12's page cap.** It CONSUMES U6's 1000 and a test refuses a second copy of the number in that
   module. **Does that test read the module's source, and would it notice the number arriving under a
   different name?**

## The shapes that have produced findings here

Each has produced a real finding on this project, most more than once.

1. **A control that is not wired.** All eight harnesses of these four units are wired - verify, do
   not assume.
2. **A green that tested nothing** - a skip, a selector matching nothing, an assertion passing
   against an absent file, a grep at a path that does not exist.
3. **A test NAME is an unverified claim about its BODY.**
4. **A hand-kept list beside the container it describes.** NINE instances now.
5. **The positive control depends on the defect.**
6. **Fail-closed on error still fails OPEN on empty.**
7. **A constant a test reads the same way the code does.**
8. **A suggested fix is a hypothesis.** FOUR of them failed on measurement today - two of R6's, one
   of R4's, and one of U12's that would have missed the path it aimed at. **Ship fixes, and say which
   you ran.**

## What is already known, so you do not re-derive it

- **ADR-0024 through ADR-0028 are all Proposed** and each records an open question: the unbounded
  scan, the page-size/budget/throttle contradiction, the embedder log leak, the budget's
  configurability against a closed variable set, and `approval_mechanism` naming a path this design
  does not use. **Not findings.** A finding that one of their ARGUMENTS is wrong IS one.
- **`outbound_rate_limit` is read by nothing** and is exempted with that reason in a wired gate.
- **The four `[INFERRED]` items on the write route** - body, 201 shape, EId casing, 409 - are marked
  and known. A finding that they are unverified is already recorded; a finding that something treats
  one as verified is not.
- U9's inherited limiter limits are carried, not resolved, and its report says which it executed.

## What you may not do

- **No edits to `src/`, `tests/` or `scripts/`.** Pin `bc0f958` in your own worktree for any harness
  run - **a mutation harness owns the working tree for its whole run**, and `u14-arguments` is
  editing this one.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. A defect there is a **Proposed** ADR in your report;
  **ADR-0029 is the next free number and a wired gate refuses a duplicate.**

## Every finding ships with a suggested fix

At every severity, nits included. Rank by severity, cite `file:line` from `grep -n` or a numbered
read, and state the failure each produces. **A surviving mutation is the strongest finding you can
bring me.**

**End with what you did NOT verify**, and keep that for what you could not settle rather than what
you did not try.
