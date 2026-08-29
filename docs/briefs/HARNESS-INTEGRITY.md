# HARNESS-INTEGRITY - two harnesses that report success over something they did not test

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `harness-integrity`. Your branch is `fix/harness-integrity`. Your report goes to
`docs/worklogs/HARNESS-INTEGRITY-REPORT.md`, committed on your branch.

**Both items here are the same shape: a control that passes without exercising its subject.** That
shape has produced six findings on this project. You are not looking for bugs in the server; you are
looking for places where the *instrument* lies.

## Item 1 - an unexplained amputation survivor (task #20)

`scripts/check-u1-boot-amputation.sh` reports one survivor:

```
tests/test_logging_process.py::test_a_failing_sink_after_a_write_returns_a_warning_not_an_error
```

The harness **exits 0**, because its contract is that survivors are OUTPUT rather than a crash. So
nothing is red, and that is exactly why this needs someone to look.

**What I established, and where I stopped.** The survivor is in the logging subsystem. My own recent
change was to `config.py` and cannot reach it - `grep` for `http_tokens` or `_token_map` in
`tests/test_logging_process.py` returns nothing. `docs/worklogs/FIX-AUDIT-LOGGING-REPORT.md` does not
mention this test name, so whoever wrote the row did not record it as a known survivor.

**What I did NOT establish: whether it is pre-existing or new.** I tried to measure it on a detached
worktree and the harness timed out at 400s there. **My belief that it is pre-existing is REASONING
from file disjointness, not a measurement**, and this project has been burned by exactly that
substitution. Settle it by running it.

**Do this:**

1. Run the harness on a clean worktree at the commit **before** `c7809f6`, with a generous timeout,
   and compare the survivor list to the current one. Report both lists.
2. Read the amputation row and the test. Work out **why** deleting that behaviour leaves the test
   green. Name the mechanism, do not just say "it survived".
3. Decide whether the fix is a better assertion or a better row, and say which and why.

**A precedent that is probably the same shape.** The audit-logging agent found and fixed a vacuous
arm of its own: *"the READ arm survived J/K/L/M and A1, because 'no raise, no warning' is what an
unconfigured logger returns too."* An assertion that passes for a reason unrelated to its name. Check
whether this is a second instance.

**HOLD any edit to `tests/test_logging_process.py`** until I tell you `fix-m5-l1` has merged - it is
live in that file. Investigate and report; if the fix belongs there, write it in the report and I
will hand it over. Everything else you may fix on your branch.

## Item 2 - R3-M2: the PID-1 harness proves PID-1 on one arm of two

`docs/reviews/REVIEW-R3.md`, section R3-M2. Read it there in full - it ships a suggested fix.

`scripts/check-u1-pid1-shutdown.sh` establishes PID 1 on the `http` arm and **not** on the `stdio`
arm, so the stdio row's claim is unproven while reading as proven.

**This one is mine.** I wrote that harness (task #5) and reported "both arms passing". The reviewer
read it and found the claim too strong. Fix the harness so each arm actually establishes what its
name says, and **make it fail loudly if an arm cannot** - an arm that silently degrades to a weaker
check is how this happened.

It exits 2 when Docker is missing and must never exit 0 in that case; preserve that.

## The rule both items serve

**A harness that cannot fail is worse than no harness**, because it occupies the space where a real
check would go and reports success while doing it. For every row you touch, prove it can go red:
break the behaviour it names and show the harness notices.

## In the report

For item 1: both survivor lists, the mechanism you found, and your recommendation. For item 2: what
each arm establishes now, quoted from a real run, and the amputation that proves the fixed arm can
fail. **End with what you could not settle.**
