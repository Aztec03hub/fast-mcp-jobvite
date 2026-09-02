# BRIEF #214 (R21-L1): ci.yml credits #187 with a widening it did not finish

Read `docs/briefs/PREAMBLE.md` IN FULL first. It is the canon; this file is only the work.

**Worktree:** your own, off `d2159e7` (main). Branch `fix/214-ci-comment-census`.
**Read the finding first:** `git show 1045edb:docs/reviews/REVIEW-R21.md` (branch `review/r21`).

## The finding

`.github/workflows/ci.yml:1203` credits task #187 with a container widening of **25 -> 32**.
`789d3be` says **25 -> 30**, and `65fabe4` says the last two were added on the OTHER side of the
merge. So the comment attributes to one commit a result two commits produced.

**And 32 is a LIVE CENSUS frozen into a comment** - in the same population where
`check-checkers-are-wired.py` deleted its own digits for exactly that reason.

## Two defects, and they want different remedies

1. **The attribution** is a historical claim and it is simply wrong about which commit did what.
   Fix it or delete it; a credit line that names the wrong commit is worse than no credit line.
2. **The frozen census** is the one this project has ruled on repeatedly: a live count in a
   comment goes stale unread. The sibling checker DELETED its digits rather than maintaining them.
   Follow the sibling unless you can argue the case is different.

**Check the siblings before you scope this to one line.** This project's dominant recurrence is a
fix landing on one instance while its twin survives one file over. Grep `ci.yml` and the checkers
for other frozen censuses and other task-credit lines, report what you find, and say explicitly
whether you fixed them or left them and why.

## Deliverable

The fix, committed. **`actionlint` is NOT installed here** - do NOT claim you ran it. Say plainly
in your report that the two `ci.yml` hunks in this population have never been through actionlint
and that CI's run of it will be their first test. That gap is first-class information, not a
footnote.

Run the gates you CAN run, exit codes on their own lines, no `&& echo OK`. Then the
`git merge --ff-only` command for me.

## Where I think I am wrong

- I have not checked whether `65fabe4` is the right commit for the last two members. Derive it.
- I do not know how many other frozen censuses live in `ci.yml`. If the answer is "many", stop and
  report rather than sweeping - a blanket rewrite of 14 sites where only 6 were wrong would have
  BROKEN 8, which is a thing that has already nearly happened here.
