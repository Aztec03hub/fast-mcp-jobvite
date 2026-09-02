# BRIEF — R21: twenty-five commits since R20, nine of them fixes to R20's own findings

You are `review-r21`, a Tier-1 reviewer. **You are not fixing anything.**
You read, you measure, you report. Findings become tasks; Tier 0 rules.

**You are a FRESH reviewer on purpose.** R20 found the defects; I fixed
them; the rule is that the fixer is never the checker. If you agree with
R20 about something, say you checked it and agreed - that is not a
wasted line.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. Before anything
else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then `TaskList`, and `TaskGet` your task immediately before claiming it -
a `TaskList` read goes stale. Claim with `TaskUpdate`
(`owner: "review-r21"`, `status: "in_progress"`), mark `completed` when
done.

**FINDINGS GO IN YOUR REPORT AND ON THE BOARD**, self-contained, no
owner, `pending`. **YOUR BRIEF GRANTS THAT MANDATE EXPLICITLY** - that
distinction was ruled tonight, because `PREAMBLE.md` and
`PROTOCOL-sub-orchestrators.md` disagreed about it and an agent was
caught between them. The obligation is REPORTING; filing is granted here.
**Do NOT create a task for a decision I should take; describe it.**

**You will receive your own claim back as an assignment. Do not act on
it.** It replays the PRE-WORK description, so its text describes the task
before you touched it. Catch it TEXTUALLY; `assignedBy` is corroboration
only. **`TaskGet` before acting: if `completed`, say so and stop.**
Measured SEVEN times; seven agents refused it correctly.

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - evidence standards and delivery protocol.
2. `docs/DESIGN.md` - FROZEN at the SHA in `docs/DESIGN-FREEZE.txt`.
   **Derive that SHA.**
3. `docs/adr/`, every ADR in number order, **and `docs/adr/README.md`,
   which gained a RULING tonight about citation drift.**
4. `docs/OBLIGATIONS.md`, `CONTRIBUTING.md`
5. `docs/briefs/PROTOCOL-sub-orchestrators.md`
6. `docs/reviews/REVIEW-R20.md` - the round whose fixes you grade. It is
   committed on `main`; read it from the repo.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push, do not merge, and do not FIX.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main` - the push
  is HELD and origin is far behind. **Derive the gap; a brief's count has
  gone stale between writing and reading three times tonight**):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r21 -b review/r21 main`
- **CI's EXACT invocations.** `uv run --frozen python`. **actionlint is
  NOT installed here - say so rather than claiming that gate.**
- **EVERY finding at EVERY severity ships with a suggested fix.** And
  **a suggested `sed` is a CLAIM ABOUT CODE**: R20-N3's proposed anchor
  named a variable that had been renamed and would have matched nothing.
  Derive anchors from the file.
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **COMMIT YOUR REPORT on your branch before reporting done**, name the
  sha. **Do NOT write a report's BASENAME casually in prose**:
  `check-brief-report-references.py` treats that as a CITATION and will
  require it to exist. It went red on two different agents' briefs
  tonight, and that false positive is RULED ACCEPTED - see its docstring.
- **Correct this brief where it is wrong.** Every agent has.

## §B — Your population: `c749334..main`, 25 commits

Derive it with `git log --oneline c749334..main`. 21 files,
+2258/-100. R20 declared `6e4fae3..c749334`, so this is everything since.

Roughly: nine fixes to R20's own findings (M1, M2, M3, L1, L2, L3, N1,
N2, N3), two rulings (#203 citations-as-at-acceptance, and the
citation-vs-quotation class), three merges, the ADR citation read, and
#205.

## §C — What to look for, in priority order

1. **THE TWO RULINGS, WHICH NO REVIEWER HAS SEEN.**
   - `docs/adr/README.md`: ADR citations are as-at acceptance and are
     NOT repointed. **Check its two worked commands actually produce
     what it says**, and check the count "five ADRs" - I got that wrong
     as twelve on my first attempt with a loose selector.
   - `check-brief-report-references.py`'s docstring: the
     citation-vs-quotation false positive is ACCEPTED, with three
     alternatives refused. **Is any of those three refusals wrong?**
2. **A FIX THAT REBUILT ITS OWN DEFECT ONE COLUMN OVER.** It has
   happened repeatedly on this project. **Assume there is one here.**
3. **THE NEW ARMS.** `check-brief-report-refs-controls.sh` went 11 -> 22
   rows in two steps, by two authors. **Watch the floor FIRE; do not
   read it.** Ask of every arm WHY it passes - three arms in that file
   have already been found confounded, each red for a branch it did not
   name.
4. **THREE MERGES**, including one whose conflict I resolved by hand
   (`7197271`) KEEPING my side over an agent's revert. **Check I did not
   lose anything of its work.** `git show --cc` on all three.
5. **A COUNT I RETYPED.** I have now been wrong on a count four times
   tonight, each from a selector with a loose or missing edge. Check
   every number in the 25 commit messages against the tree.
6. **`set -uo pipefail` DOES NOT DISABLE ERREXIT** - measured, and
   `check-checkers-are-wired.py` now says so. Verify that claim yourself
   under `bash -e`; it contradicts what that file said for weeks.

## §D — The declaration is half the deliverable

End `REVIEW-R21.md` with a `REVIEW-COVERS` line naming what you ACTUALLY
read. **A narrower true declaration is the correct outcome; a wide false
one is a defect worse than the gap.** The report must carry a
declaration or it lands in `unexplained` and the coverage checker
returns 1.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py
    uv run --frozen python docs/reviews/check-brief-report-references.py
    bash docs/reviews/check-brief-report-refs-controls.sh
    uv run --frozen python docs/reviews/check-row-floor-exactness.py
    python3 docs/reviews/check-row-floor-exactness.py --self-test

**Read each exit code on its own line.** Do NOT write
`cmd >/dev/null && echo OK` - under `set -e` only the LAST command of an
AND-list triggers errexit, and that pattern hid a real red from me twice
tonight. A third form is worse: a gate printing a SUCCESS IT HAD NOT
EARNED, which is #205.

## §F — Context you are owed

- **The trunk has ONE green CI run ever** (`33582613697`). Everything in
  your population is unpushed and has never been through CI.
- `suborch-204` is live in `fmj-worktrees/w204`. **Do not touch it.**
- **`review/r18` must NOT be merged** - superseded; its
  `probe-131-gate-state.sh` is 190 lines against main's 341.
- Open, not yours: #194's remaining half, #204, #106/#160 (blocked),
  #158/#9 (Phil's), #162 (standing hazard).
