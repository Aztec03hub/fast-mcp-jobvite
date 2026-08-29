# CODE-REVIEW-R3 - a fresh round, because the round-1 report was destroyed

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r3`. Your report goes to `docs/reviews/REVIEW-R3.md`, committed on
branch `review/r3`. **You are READ-ONLY on the source tree** - see "What you may not do".

## Why this round exists, and it is not because round 1 was bad

A sudden restart destroyed the session scratchpad. Round 1's report - **nineteen findings with their
evidence and their suggested fixes** - lived only there, and is gone. Board task #4 is a summary
somebody happened to have copied out, and it says so.

**Do not try to reconstruct round 1's findings.** A wrong reconstruction is worse than an honest
re-derivation, and this project's rule is a fresh reviewer every round regardless. **You are not
being asked to remember. You are being asked to look.**

One finding did survive and is already fixed, so do not re-report it: **L6**, that nothing floored
the test count. `ci.yml`'s guard was `grep -qE '[1-9][0-9]* passed'`, satisfied by "1 passed". It is
now `scripts/check-suite-floor.sh` with a ratchet, plus an amputation harness.

## Scope

**Everything merged on `main`**, which is seven units: U0, U1, U2, U3, U4, U11, U15.

```
src/fast_mcp_jobvite/
  __main__.py   config.py   server.py        <- U1: boot, TLS refusal, shutdown, logging
  errors.py     utils/correlation.py         <- U2: RFC 9457 contract, request_id_var
  audit.py      utils/redaction.py           <- U3: audit event, single-point redaction
  services/jobvite_client.py                 <- U4: auth, the error-detection invariant
```

Plus `scripts/` (13 harnesses), `docs/reviews/` (8 checkers), `ci.yml`, and the test suite.

**Two areas are being actively edited and are OUT OF SCOPE for findings** - report anything you see
there to me in the message instead, but do not write it up as a finding:

- `src/fast_mcp_jobvite/__main__.py`, `services/jobvite_client.py`, `utils/redaction.py` and their
  tests - `fix-m5-l1` is mid-change.
- Docstring line lengths anywhere - `b49b-sweep` owns that, 1654 known violations.

## What I already know, so you spend your time on what I do not

Do not re-derive these. **Do challenge them if you find them wrong** - two have been wrong already.

- **`record["exception"]` reaches the sink unredacted.** Confirmed, probe committed at
  `scripts/probe-exception-redaction.py`, exits 1 today. Task #15. `fix-m5-l1` owns the fix.
- **`str(exc)` from httpx2 reaches the API consumer**, a `priority: required` breach. Task #14, in
  flight.
- The audit trail records nothing until `configure_logging()` runs; its fail-closed branch could not
  fire; `httpx2` logged the jobFeed URL at INFO in the clear. **All three fixed and merged.**

## Where the defects have actually been on this project

This is the highest-value part of the brief. Every item below names a shape that has produced a real
finding here, more than once. **Hunt these before you read for style.**

1. **A control that is not wired is not a control.** Six instances. The newest: two harnesses that
   were committed, listed in `CONTRIBUTING.md`, and invoked by nothing. **For every gate, harness and
   checker, find the thing that RUNS it.** A `CONTRIBUTING.md` line is not a runner.
2. **A green that tested nothing.** A skip; a selection that matched nothing; an assertion that
   passes against an absent file; a `grep` at a path that does not exist, which exits clean-empty
   and is indistinguishable from real absence.
3. **A test NAME is an unverified claim about its BODY.** Read bodies. Two collisions and one
   inverted assertion were exactly this.
4. **The positive control depends on the leak.** A real one here: a redaction test asserts
   `"jobvite.com" in detail` to prove it is not vacuous - so fixing the leak breaks the control.
   **Look for other controls that are load-bearing on a defect.**
5. **A citation that resolves but is wrong.** Nine wrong-subject citations found, four of them inside
   the ADR documenting that defect class. **Check citations by SUBJECT**, never by confirming the
   line is non-blank.
6. **An allow-list selects for the member nobody thought of.** Four instances. Wherever a rule,
   sweep or copy NAMES its members, ask what is not on the list.
7. **Fail-closed on error still fails OPEN on empty.** An `except` branch that raises does not cover
   the case where nothing was found at all.

## What you may not do

- **No edits to `src/`, `tests/` or `scripts/`.** Findings, not fixes - two agents are live in there.
- **`docs/DESIGN.md` is FROZEN** at `c15b138`. Read it as `git show c15b138:docs/DESIGN.md`. A defect
  in it is a **Proposed** ADR in your report, never an edit.
- Your report and a changelog fragment are the only files you create.

## Every finding ships with a suggested fix

At every severity, nits included. That is a standing project rule: a finding without a remedy costs
the author the whole diagnosis a second time.

Rank by severity. For each: the evidence (`file:line` from `grep -n` or a numbered read), the failure
it produces, and the fix you suggest. **Prove what you can prove** - a surviving mutation is the
strongest finding you can bring me, and you may run the existing harnesses read-only to get one.

**End with what you did NOT verify**, and keep that list for what you could not settle rather than
what you did not try.
