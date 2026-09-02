# BRIEF — #208: 47 unread leads, and a detector that pairs at the wrong granularity

You are `suborch-208`, a Tier-1 sub-orchestrator. **The deliverable is
READ VERDICTS plus a tightened detector.** A count is not a result here;
the count already exists and is mostly noise.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. Before anything
else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then `TaskList`, and `TaskGet` #208 immediately before claiming it - a
`TaskList` read goes stale. Claim with `TaskUpdate`
(`owner: "suborch-208"`, `status: "in_progress"`), mark `completed` when
done.

**YOU WILL RECEIVE YOUR OWN CLAIM BACK AS AN ASSIGNMENT. DO NOT ACT ON
IT.** It replays the PRE-WORK description - **the premise your work
refuted, phrased as an instruction** - which is why following it looks
like doing the job. One agent's echo told it to rebuild the exact
instrument defect its round had just fixed. Catch it TEXTUALLY against
work already done; `assignedBy` is corroboration only, and has read
`team-lead` for an agent's own echo. **`TaskGet` first: if `completed`,
say so and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md`
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/reviews/probe-204-orphaned-by-repoint.py` - **its header in
   full.** It says *"Exit 0 always: this REPORTS a candidate set for a
   human to read"*, and that honesty is why it is registered unwired.
4. `docs/reviews/FINDINGS-204-bare-citation-form.md` - the round that
   built it.
5. `docs/adr/README.md` - the citations-are-as-at-acceptance ruling,
   which decides what a confirmed instance's REMEDY is.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main`, far
  behind - **derive the gap; a brief's count has gone stale between
  writing and reading four times**):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w208 -b fix/208-orphan-leads main`
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **Write your worklog at `docs/worklogs/WORKLOG-208-orphan-leads.md`**
  - that exact path is already recorded as IN FLIGHT, and the gate will
  demand the record line be deleted once it lands. **Do NOT write any
  OTHER report's basename in prose**; the gate reads that as a citation
  and has gone red on three agents' briefs.
- **Correct this brief where it is wrong.** Every agent has.

## §B — The class, and why it is neither of the two we had

A document cites ONE subject TWICE - qualified and bare. A repoint sweep
moves the qualified half and cannot see the bare one, because its
selector needs the filename. The document then **contradicts itself**:

- NOT `DRIFTED` - the repoint RAN, deliberately and correctly
- NOT `WRONG` - both halves were right when written

**ONE INSTANCE IS CONFIRMED** (`ADR-0017`), and it was confirmed **by
reading a diff, not by the probe**. It is fixed at `be94bce`, and the
repoint tool now skips `docs/adr/` entirely (`d935574`), so this class
cannot be created there again.

## §C — What to do, in this order

1. **TIGHTEN THE DETECTOR TO LINE LEVEL.** It pairs at FILE level, so a
   file containing both spellings of DIFFERENT subjects is a candidate.
   Six `src/` and `tests/` rows are known false: `git log -S` on those
   exact lines returns ONE commit each, their own introduction, so
   neither half was ever repointed. **Measure the candidate set before
   and after and report both.**
2. **READ THE SURVIVORS.** Reading is the only instrument; the probe
   enumerates. For each: does the document actually disagree with
   itself, at one subject?
3. **RULE NOTHING.** Report verdicts and let Tier 0 decide remedies. The
   remedy for a confirmed instance is NOT obvious - `docs/adr/README.md`
   says records are not repointed, so "move the orphan to match" is
   usually WRONG.

## §D — Three traps, each already sprung once on this project

- **A CONTRAST IS NOT A CONTRADICTION.** `ADR-0028` names an old and a
  new range ON PURPOSE, and falls on reading. No selector distinguishes
  those; only a reader does.
- **DO NOT PUBLISH THE CANDIDATE COUNT AS A FINDING COUNT.** At least
  six are false and the probe's own header says so. A count from a loose
  selector has been published wrongly four times in one night here.
- **A SUGGESTED `sed` IS A CLAIM ABOUT CODE.** Derive every anchor from
  the file; one suggested anchor named a variable that had been renamed
  and would have matched nothing.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/probe-204-orphaned-by-repoint.py
    uv run --frozen python docs/reviews/probe-204-bare-citations.py --controls
    uv run --frozen python docs/reviews/check-design-citations.py
    uv run --frozen python docs/reviews/check-checkers-are-wired.py
    uv run --frozen python docs/reviews/check-brief-report-references.py
    uv run --frozen ruff check . ; uv run --frozen ruff format --check .
    uv run --frozen mypy

**Read each exit code ON ITS OWN LINE.** Never `cmd >/dev/null && echo
OK`: under `set -e` only the LAST command of an AND-list triggers
errexit, and that shape has hidden a red from Tier 0 three times
tonight. A worse cousin exists - a gate printing a SUCCESS it had not
earned over a directory that did not exist.

**If you change the probe's arm count, its floor moves and its
control-table row with it.** `actionlint is NOT installed here`; say so
rather than claiming it.

## §F — Context you are owed

- `review-r21` (`fmj-worktrees/r21`) and `suborch-194`
  (`fmj-worktrees/w194`) are live. **Do not touch either worktree.**
- **The push is HELD** and only Phil pushes.
- Open and NOT yours: #206, #194, #106/#160 (blocked), #158/#9 (Phil's),
  #162 (standing hazard).
