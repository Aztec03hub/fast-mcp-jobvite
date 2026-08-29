# R5-FIXES - the four findings that are NOT in U7's file

**Read `docs/briefs/PREAMBLE.md` first.** Tools, isolation, evidence standards, gates and delivery
rules are there and are not repeated here.

Your agent name is `r5-fixes`. Your branch is `fix/r5-findings`. Your report goes to
`docs/worklogs/R5-FIXES-REPORT.md`, committed on your branch.

`docs/reviews/REVIEW-R5.md` is merged on `main`. **It is the authority, not this brief.** Every
finding there carries a measurement and a suggested fix.

## Your four, and NOTHING ELSE

R5 filed 3 High, 4 Medium and 4 nits. **H2, H3, M2 and N1 are in
`src/fast_mcp_jobvite/services/jobvite_client.py`, which `u7-resilience` owns right now. They are
not yours and you must not touch that file.** Yours are:

- **H1** (High) - a surviving amputation. `jobvite_client.py:997-999` truncates a capped result, and
  **deleting all three lines leaves the whole suite green.** I re-measured it myself: 447 passed, 6
  deselected, restore `cmp`-verified. **THE CODE IS RIGHT AND THE CASE IS MISSING** - your fix is a
  TEST in `tests/test_pagination.py`, not an edit to the client.
- **M1** (Medium) - `JOBVITE_PAGINATION_START_BASE` reaches nothing. `grep -rn
  "pagination_start_base" src/` returns one line: its own definition. `tools/jobs.py` passes
  `api_key`, `api_secret`, `company_id`, `max_results` - and not `start_base_overrides`.
- **M3** (Medium) - amputation row A7's comment claims it deletes "both the loop break and the final
  truncation"; the anchor deletes only the break. **That is WHY H1 was never found.**
- **M4** (Medium) - mutation row M11's title names a mutation that is a **provable no-op**.

## Why H1 and M3 are ONE piece of work, and must be done together

M3 is the reason H1 exists. The harness comment says a row amputates two things; it amputates one.
So the row passed, the truncation was never exercised, and a live behaviour sat unprotected behind a
control that claimed to cover it.

R5's suggested fix: split A7 into **A7a** (the loop break) and **A7b** (the final truncation), and
raise that harness's row floor 10 -> 11. **A7b will report VACUOUS until H1's test case lands. That
is the harness working, not a failure** - and it is the order you should do it in, because it proves
A7b can fail before you make it pass.

For H1 the case R5 specifies: a server returning `[A, A, A, B]` plus four fresh records, `limit=4`,
`max_results=4`, asserting `len(items) == 4` **and** `pages == 2`. The shape that reaches the
truncation is a full wire page yielding fewer than `effective_limit` NEW records - ordinary clamping,
which is the whole reason this unit exists. R5's probe: `limit=4` over `[A,A,A,B,C,D,E,F]` returns 4
intact and **SIX** amputated, with `capped` True in both, **so the result object cannot tell them
apart.** Assert on the item count, not on `capped`.

## M4, and read the measurement before you touch it

R5 measured that `len(items)` is **identically** `len(seen) + unidentified` on that path, so M11's
titled mutation cannot fail - 447 passed. Its BODY forces `unique = total`, which is M10's behaviour.
**So 16 rows hold 15 distinct behaviours.** R5 measured the replacement it proposes,
`unique = len(seen) + unidentified + duplicates`, as KILLED (1 failed, 446 passed).

**Re-measure both before and after rather than trusting those numbers.** R5 said plainly it recorded
the count and not the node id, so **read the failing test's name off your own run** and put it in
your report.

## M1 is my miss, and knowing that tells you where to look

I fixed U6-F1 - the same factory omitting `max_results` and `company_id` - and did not check the rest
of the argument list. **M1 is F1's sibling in the very argument list F1 was fixed in.** So:

- Do not just add one argument. **Enumerate `JobviteClient.__init__`'s parameters against what the
  factory passes** and report the two sets. A hand-kept argument list beside a constructor is the
  seven-times-recorded defect on this project.
- Your test must be able to fail. F1's does (`client_factory=None` is its whole point); model
  yours on it and **prove it by amputation**.
- **F2 is NOT yours to settle** - whether `pagination_start_base` should be a scalar or per-resource
  is a contract decision. R5 notes M1 ranks above F2 because "F2 argues about the shape of a value
  nobody reads". Wire the value through as it is today; say in your report what F2 then costs.

## Isolation - three agents are live and one owns a file you will want

- **`src/fast_mcp_jobvite/services/jobvite_client.py` is OFF LIMITS.** `u7-resilience` is in it.
- `r2-fixes` is in `src/` and `tests/` but not in `tests/test_pagination.py`, `tools/jobs.py` or
  `scripts/check-u6-paging-*.sh`. Those are yours.
- `ci.yml` is MINE. The row floor 10 -> 11 lives **inside** the harness at `:296-300`, so that one is
  yours; the suite and anchor floors are ci.yml and are **reported, not edited**. Derive them - the
  command is in `PREAMBLE.md`, never retype a floor.

## Standing requirements

- **Every fix ships with the mutation or amputation that proves the test can fail.** Write the
  control, run it against the UNFIXED code, watch it survive, then fix, then watch it die.
- **Restore with `cp` from a backup and verify with `cmp`.** Never `git stash`, never
  `git checkout <path>`.
- **Run `ruff format` BEFORE your final harness run** - it broke an amputation anchor after a green
  run once already.
- `docs/DESIGN.md` is FROZEN at `c15b138`; cite by subject from `git show c15b138:docs/DESIGN.md`.
  `check-design-citation-shape.py` exits 0 today - do not take it back to 1.
- **No `Co-Authored-By:` or "Generated with" trailer. Ever.**

## How to deliver

Commit and push your branch. **Do NOT merge to main, do NOT push main.** `SendMessage` to
`"team-lead"` as your FINAL action: per finding what you measured before, what you changed, the
control proving it, the failing test's NAME for M4, the new floors, and **what you could not settle**.
