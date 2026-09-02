# BRIEF — R20: twenty-five held commits, four of them building NEW GATES nobody has read

You are `review-r20`, a Tier-1 reviewer. **You are not fixing anything.**
You read, you measure, you report. Findings become tasks; Tier 0 rules
on them.

**You are a FRESH reviewer on purpose.** R19 found defects; I fixed them;
I then built two new gates and merged two branches. The rule here is that
the fixer is never the checker. If you agree with R19 about something,
say you checked it and agreed - that is not a wasted line.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then call `TaskList` to see the shared board, and `TaskGet` your task
immediately before you claim it - a `TaskList` read goes stale, and the
tool's own docs say to re-read latest state before updating. Claim with
`TaskUpdate` (`owner: "review-r20"`, `status: "in_progress"`), and mark
it `completed` when you finish.

**FINDINGS GO IN YOUR REPORT AND ON THE BOARD**, self-contained, no
owner, `pending`. **Do NOT create a task for a decision you think I
should take; describe it and let me rule.**

**You will receive your own claim back as an assignment. Do not act on
it.** `TaskUpdate(owner=you)` enqueues a notification addressed to you
carrying the full description, delivered at your next turn boundary -
usually AFTER the work. It is byte-identical to a real dispatch. Catch
it TEXTUALLY by comparing the text to work you have already done; do NOT
rely on `assignedBy`, which has read `team-lead` for an agent's own echo.
**Before acting on any assignment, `TaskGet` it: if it is already
`completed`, say so plainly and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - the evidence standards and the delivery
   protocol. **Read §"How to deliver" twice.** It is the rule this round
   exists partly to test.
2. `docs/DESIGN.md` - FROZEN at the SHA in `docs/DESIGN-FREEZE.txt`.
   **Derive that SHA, do not retype it.**
3. `docs/adr/`, every ADR in number order. **ADR-0034 and ADR-0035 are
   both in your population and ADR-0034 was edited twice tonight.**
4. `docs/OBLIGATIONS.md` and `CONTRIBUTING.md`
5. `docs/briefs/PROTOCOL-sub-orchestrators.md`
6. `docs/reviews/REVIEW-R19.md` - the round whose fixes you grade. It IS
   committed on main now; read it from the repo, **not from a worktree**.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push, do not merge, and do not FIX.**
- **Own worktree**, cut from the local trunk tip (NOT `origin/main` -
  the work you are reviewing is HELD and is not on the remote):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r20 -b review/r20 main`
- **CI's EXACT invocations.** `uv run --frozen python`, never bare
  `python3`. `actionlint` needs `SHELLCHECK_OPTS=--severity=warning` and
  **is NOT installed on this machine - say so rather than claiming it.**
- **EVERY finding at EVERY severity, nits included, ships with a
  suggested fix.**
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **COMMIT YOUR REPORT ON YOUR BRANCH BEFORE YOU REPORT DONE**, and name
  the sha in your completion message. This is not boilerplate: R18's
  report sat untracked in a worktree and I declared it destroyed. See §C6.
- **Correct this brief where it is wrong.** Every agent on this project
  has found an error in theirs.

## §B — Your population: `origin/main..main`, 25 commits

Derive it with `git log --oneline origin/main..main`. `origin/main` is
`6e4fae3` and the push is HELD, so none of this is on the remote.

Roughly: R19's seven findings closed, ADR-0035 plus a re-freeze,
ADR-0034 edited AGAIN, two branch merges (`fix/170-retyped-counts` at
`39c3e2e`, `review/r19` at `33fc977`), two NEW GATES with controls, a
handoff rewrite, and a rescued review report.

**`4a51a23` is R19's own report** and arrives inside your population via
the merge. Read it as the round you are grading, not as new work.

## §C — What to look for, in priority order

1. **THE TWO NEW GATES, WHICH NO REVIEWER HAS SEEN.**
   - `docs/reviews/check-brief-report-references.py` + its controls
     (`check-brief-report-refs-controls.sh`, 9 arms, floor 9)
   - `docs/reviews/probe-mirror-zero-refs.sh` (3 arms, floor 3)
   Both are WIRED in `ci.yml`. **Neither has ever run in CI**, because
   the push is held. Ask of every arm: WHY does it pass? Watch the
   floors FIRE; do not read them.
2. **A CONTROL THAT PASSES WITHOUT TESTING ITS SUBJECT.** I found two
   such defects in my OWN controls tonight by watching them: an
   amputation arm whose fixture tripped two failure branches so the
   amputation proved nothing, and backticks inside a double-quoted
   string that ran as command substitution. **Assume there is a third.**
3. **THE MIRROR CHANGE (`b4e6d06`).** `mirror.yml`'s push step has NEVER
   EXECUTED - there is no MIRROR_TOKEN. I changed unexercised code and
   proved it with a probe that EXTRACTS the guard by `awk`. Is the
   extraction anchored well enough to fail loudly if the block moves?
   Does the `GITHUB_STEP_SUMMARY` write work when that variable is
   unset, which is exactly what happens outside Actions?
4. **THE TWO MERGES.** Every merge on this project has found something
   neither branch could see alone, five for five. `39c3e2e` brought
   2015 lines. Check the merged result, not the branches.
5. **A COUNT THAT WENT STALE INSIDE ITS OWN FIX.** ADR-0034's blockquote
   said 33, was "fixed" to 34, and `ls docs/adr/[0-9]*.md | wc -l`
   returns 35. It states no population now. **Check that its remaining
   figures - the 19/15/34 census and "six of the `Design change` ADRs" -
   are right, and that my TENSE remedy did not just hide a wrong
   number.** Same question for `check-checkers-are-wired.py`'s "87
   `run:` steps", which I changed twice in one hour.
6. **THE DELIVERY RULE ITSELF.** `PREAMBLE.md:133` has required reports
   to be committed since the first one was lost. It was not enough.
   `check-brief-report-references.py` is my answer. **Is the ratchet
   sound, and can anything be smuggled past it?** Its record file is
   `docs/reviews/brief-report-refs-known-missing.txt`. Ask specifically:
   does a recorded line ever become a permanent excuse?
7. **A CLAIM IN A COMMIT MESSAGE THE CODE DOES NOT SUPPORT.** I wrote
   twenty-five long ones. Check the numbers: backlog 80 -> 66, 138 mypy
   files, 131 -> 133 wiring members, floors 9/3, 31 register rows,
   ADR census 20/15/35.

## §D — The declaration is half the deliverable

End `REVIEW-R20.md` with a `REVIEW-COVERS` line naming what you ACTUALLY
read. **A narrower true declaration is the correct outcome; a wide false
one is a defect worse than the gap.** A round covers a commit only if it
claims at least one non-record file that commit touches.

`REVIEW-R20.md` must itself carry a declaration or it lands in
`unexplained` and `check-review-coverage.py` returns 1.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py
    uv run --frozen python docs/reviews/check-brief-report-references.py
    bash docs/reviews/check-brief-report-refs-controls.sh

The backlog reads 66 and was 80 before the two reports landed. Report
before/after with refs and shas. **The trunk may move under you.** Pin
your reading to one sha, say which, and re-derive at the end.

**mypy has caught errors in agents' new files after they reported green
three times on one branch.** Run it on anything you touch.

## §F — Context you are owed

- **The trunk has ONE green CI run ever** (`33582613697`). Everything in
  your population is unpushed and therefore untested by CI.
- `suborch-187` is live on `fix/187-floor-container` in
  `fmj-worktrees/w187`. **Do not touch that worktree.** It has already
  filed #193 and #194.
- **`review/r18` must NOT be merged**: its `probe-131-gate-state.sh` is
  190 lines against main's 341. Its report was rescued separately.
- Open tasks you may re-encounter, so you do not re-file them: #106 and
  #160 (blocked), #158 and #9 (Phil's), #162 (a standing board hazard),
  #191, #193, #194 (open, owned).
