# CODE-REVIEW-R8 - U14, merged and never reviewed

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `code-review-r8`. Your branch is `review/r8`. Your report goes to
`docs/reviews/REVIEW-R8.md`, committed on your branch. **Do not merge and do not push to `main`.**

## Subject

**U14, the argument layer.** Merged at `f2447ed`; the unit's own commits are `01669e3`, `cb9b042`
and `2c6ff19`. Review it at the current `main` tip and state the SHA you read in your report.

Principal files: `src/fast_mcp_jobvite/utils/constraints.py`, the `InboundModel` base and its five
subclasses under `src/fast_mcp_jobvite/tools/`, `tests/test_arguments_sweep.py` (783 lines),
`scripts/check-u14-arguments-{controls,amputation}.sh`, and
`docs/adr/0029-the-body-size-limit-has-no-middleware-to-live-in.md`.

**Read `docs/worklogs/U14-IMPL-REPORT.md` - and treat every claim in it as a claim.** It is unusually
candid, which is a reason to check it rather than to trust it. Six of its harness rows failed on
first run and all six were defects in its own arms; that is a good sign about the author and tells
you nothing about the rows you have not re-run.

## READ-ONLY on `src/`, `tests/` and `scripts/`

You may apply mutations inside **your own worktree** to measure, and you MUST restore each one and
prove the restore. Use `cmp` against a backup, never `git diff` alone - `git diff --quiet` reports
NO DIFF for an untracked file, which made four amputations look like they had not landed when all
four had. `ci.yml` is the orchestrator's.

## What this project has learned that bears directly on U14

Aim at these; they are where the defects have actually been.

**A hand-kept list beside its container.** Ten measured instances, the most recent being R7-H1: a
payload-logging middleware added to the production stack left all 663 tests green. U14 claims to
have avoided this by enumerating with two independent AST walks asserted EQUAL. **Test that claim.**
Its own amputation A4 replaced route B with a call to route A and nothing went red - the equality
assertion was comparing a set with itself, the unit's own failure mode inside its own instrument.
U14 says the `OrphanInput` arm closes that. Verify it does, and verify the guard cannot be satisfied
vacuously.

**The scoping question U14 raised against itself, which is task #80 item 1.** Both routes are scoped
to `src/fast_mcp_jobvite/tools/`. A model outside that directory reached by another path is
invisible to both. U14 found none and says "I looked in one directory" is what the claim is worth.
**Go and look.** If there is an inbound model outside `tools/`, that is a High.

**A test whose name is a claim its body never exercises.** R7-L1 found one; U12 and U1 each had one.
`tests/test_arguments_sweep.py` is 783 lines of parametrised sweep - the shape where a case can
parametrise over an empty set and pass. U14 says INPUT_MODELS resolves at import so a broken
enumeration fails collection, and that its string-field sweep was silently finding 5 of 9 fields
until a hand-written population assertion caught it. **Check every derived parametrisation for a
population assertion, and check that each assertion could actually fail.**

**An accepting arm that reads its expectation out of the code under test.** U14's M11 survived for
exactly this reason and it says it fixed every arm to use the design's literal. **Verify no arm
imports its expectation from its subject**, and that the literals match `DESIGN.md:162-164` rather
than matching `constraints.py`.

**Fail-closed by accident.** U14's own honest caveat: pre-U14 all five models already refused all
four limits, because every field is a bounded scalar under `strict=True`. The protection evaporates
the first time any model declares a dict or list field. `NestedProbe` is where the limits are
load-bearing. **Decide whether the sweep would still fail if the limits were removed** - amputation
A6 claims to test exactly this (97 survivors). Re-run it.

## Questions I want answered

1. **Is five the whole inbound surface?** The brief, the plan and the gating task all said four.
   Enumerate from a different direction than U14 did and say what you find.
2. **Can `check_structural_limits` be reached with a payload it does not measure?** U14 says
   `MAX_PAYLOAD_BYTES` re-serialises with `json.dumps`, so it measures different bytes than arrived.
   Is there a payload where the difference matters - a large string with heavy escaping, say?
3. **Does the depth check terminate?** A cyclic structure, a deeply nested one built to blow the
   recursion limit before the depth check fires. What does the caller get?
4. **ADR-0029 says the 1 MiB body cap has no middleware to live in.** Verify that claim yourself
   against the frozen design and the tree. If a body cap IS reachable somewhere, the ADR is wrong.

## The design is FROZEN at `c15b138`

Read it as `git show c15b138:docs/DESIGN.md`, never from a working tree. If you find a defect in the
DESIGN rather than the code, that is an ADR, and **ADR-0030 is the next free number** - but check
`python3 docs/reviews/check-adr-numbers.py` before claiming it, because two units have collided on a
number here before, both correct when they looked.

## Evidence standard

Every finding cites `file:line` read from `grep -n` or a `Read`, never counted inside a `sed -n`
window. Every severity ships a **suggested fix**, nits included - and label it a hypothesis unless
you ran it. Seven of R7's eight were hypotheses and it said so; four suggested fixes on this project
have failed on measurement.

**A surviving mutation is the strongest finding you can produce.** R7 produced three. Prefer
measurement over reading wherever the two are both available.

## In the report

Baseline first, read from the terminal, each on its own line, with floors DERIVED from `ci.yml` by
grep. Findings as CRITICAL / HIGH / MEDIUM / LOW with `file:line` and a fix each. Then the
mutations you applied, whether each was killed or survived, and proof of restore. **End with what
you could not settle** - the things you CANNOT establish, not the ones you did not try.
