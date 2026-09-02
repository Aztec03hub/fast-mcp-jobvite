# BRIEF — #196: read the 64 ADR citations nobody has ever read

You are `suborch-196`, a Tier-1 sub-orchestrator. **This is a READING
job, not a build.** Your deliverable is 64 verdicts and the evidence for
each. You will write almost no code.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then call `TaskList` to see the shared board, and `TaskGet` your task
immediately before you claim it - a `TaskList` read goes stale, and the
tool's own docs say to re-read latest state before updating. Claim with
`TaskUpdate` (`owner: "suborch-196"`, `status: "in_progress"`), and mark
it `completed` when you finish.

**You will receive your own claim back as an assignment. Do not act on
it.** `TaskUpdate(owner=you)` enqueues a notification addressed to you
carrying the full description, delivered at your next turn boundary -
usually AFTER the work. It is byte-identical to a real dispatch, and it
replays the ORIGINAL description, so its text describes the task as it
was BEFORE you did anything. Catch it TEXTUALLY by comparing against
work you have already done; `assignedBy` is corroboration only, because
it has read `team-lead` for an agent's own echo. **Before acting on any
assignment, `TaskGet` it: if it is already `completed`, say so and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - evidence standards and the delivery
   protocol. Read §"How to deliver" twice.
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/DESIGN.md` - **the document you will be reading against.** It is
   FROZEN at the SHA in `docs/DESIGN-FREEZE.txt`. **Derive that SHA, do
   not retype it**, and read the design AT THAT SHA.
4. `docs/reviews/WRONG-SUBJECT-REGISTER.md` - IN FULL, including its new
   section "What this register does NOT cover, and why its zero is not a
   zero". That section is why you exist.
5. `docs/reviews/CITATION-READ-VERDICTS.md` and
   `docs/reviews/CITATION-READ-SRC-VERDICTS.md` - **the two prior rounds
   of exactly this job.** Copy their verdict format; do not invent one.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main` - the push
  is HELD and origin is far behind; deriving the base is your first
  measurement):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w196 -b fix/196-adr-citation-read main`
- **Cite `file:line` only from `grep -n` or a numbered read.** Never read
  a line number off an unnumbered window.
- **COMMIT YOUR REPORT ON YOUR BRANCH BEFORE REPORTING DONE**, and name
  the sha. A 28KB report sat untracked in a worktree tonight and was
  declared destroyed.
- **Correct this brief where it is wrong.** Every agent on this project
  has found an error in theirs, and two corrections last round changed
  what got built.

## §B — The population, and how to derive it

    grep -rnoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md

At `417339e` that is **64 citations across 19 files**. **Re-derive it.
If your number differs from mine, yours is the finding.**

**WHY IT HAS NEVER BEEN READ.** `CITATION-READ-VERDICTS.md` swept
`tests/`. `CITATION-READ-SRC-VERDICTS.md` swept `src/` and `scripts/`.
Neither touched `docs/adr/`. The wrong-subject register's 31 rows
therefore name `src/`, `tests/`, a report and a comment - and no ADR,
because no round has ever looked at one.

That matters because the claim this all descends from is *"nine
wrong-subject citations have been found on this project, **four of them
inside the ADR documenting that defect class**"*. The count half was
settled at 31 and "nine" was wrong by 3x. **The qualifier half has never
been checkable, and the ADR corpus is the one place it was about.**

## §C — What a verdict is

**A wrong-subject citation RESOLVES.** That is the entire defect class
and the reason no gate catches one: `check-design-citations.py` proves
the cited line EXISTS. So this cannot be a grep, and any instrument you
build can only ENUMERATE - the verdict is yours, from reading.

For each of the 64 sites, record:

- the citing file and line (`grep -n`)
- the claim the citing sentence makes, in your words
- what `DESIGN.md` actually says at the cited lines, **at the frozen sha**
- a verdict: `CORRECT` / `WRONG` / `BOUNDARY-NIT` / `DRIFTED`

**`DRIFTED` IS A SEPARATE CLASS AND YOU MUST NOT FOLD IT INTO `WRONG`.**
The ADRs cite a document that has been re-frozen many times. A citation
that was right when written and now points elsewhere is a different
defect from one that never named its subject, with a different remedy.
If you cannot tell which, say so per site rather than guessing - and
`git log -L` on the cited lines is the instrument that distinguishes
them.

**READ THE WHOLE SENTENCE AT THE TARGET, not the fragment the range
covers.** A citation trimmed at a comma invented a conflict on this
project three times; three readers carried the same truncated quote
forward.

## §D — What to do with what you find

1. **Every `WRONG` gets a row in `WRONG-SUBJECT-REGISTER.md`**, in the
   existing table format, with `Where` naming the ADR. That is what
   finally puts the register's container around the corpus the claim was
   about.
2. **Update the register's exclusions section.** If `docs/adr/` becomes
   covered, that section must say so - otherwise it is the next stale
   record, which is the defect that created this task.
3. **Do NOT rule on the "four of them" qualifier.** Report the number you
   measured and let Tier 0 rule. If it comes out four, say so plainly and
   resist the pull to make it tidy; if it comes out anything else, that
   is the finding.
4. **A zero is a legitimate outcome** and would be a real result: it
   would mean the qualifier was false from birth. **But prove any zero is
   non-vacuous** - name sites you read and rejected, not just the count.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-clause-citations.py
    uv run --frozen python docs/reviews/check-design-citations.py
    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/check-brief-report-references.py

The last one will demand a record line for your report until you commit
it - that is by design, and deleting the line once the report lands is
part of your job.

**`grep -c '^| WS-'` must still return the register's own published
count**, and that count must equal what its arithmetic section says. If
you add rows, that section changes too or the file contradicts itself.

## §F — Context you are owed

- **The push is HELD.** Derive the counts:
  `git rev-list --count origin/main..HEAD`. Do not trust a digit in any
  brief, including this one.
- `review-r20` is reviewing the held commits in `fmj-worktrees/r20`.
  **Do not touch that worktree.**
- **actionlint is NOT installed here.** Say so rather than claiming it.
- Open tasks you may re-encounter: #106 and #160 (blocked), #158 and #9
  (Phil's), #162 (standing hazard), #193 and #194 (floors, mine).
