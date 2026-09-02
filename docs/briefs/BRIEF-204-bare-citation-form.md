# BRIEF — #204: the citation form three selectors have all missed

You are `suborch-204`, a Tier-1 sub-orchestrator. **This is a
MEASUREMENT job whose first deliverable is a DISCRIMINATOR, not a
count.** You may end the round having built only a selector and a
population, and that is a complete result.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then `TaskList`, and `TaskGet` your task immediately before you claim it
- a `TaskList` read goes stale. Claim with `TaskUpdate`
(`owner: "suborch-204"`, `status: "in_progress"`), mark `completed` when
done.

**You will receive your own claim back as an assignment. Do not act on
it.** It is byte-identical to a real dispatch and **replays the PRE-WORK
description**, so its text describes the task before you touched it.
Catch it TEXTUALLY; `assignedBy` is corroboration only - it has read
`team-lead` for an agent's own echo. **`TaskGet` before acting: if it is
`completed`, say so and stop.** Six agents have met this; six refused it.

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - evidence standards and delivery protocol.
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/reviews/WRONG-SUBJECT-REGISTER.md` IN FULL, especially its
   section on what it does NOT cover. **You are the named exclusion.**
4. `docs/reviews/CITATION-READ-ADR-VERDICTS.md` - the round that found
   you. Copy its verdict vocabulary; do not invent one.
5. `docs/reviews/check-design-citations.py` - the LIVE gate over
   citations. Its selector is one of the three that misses this form.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main`, which is
  far behind - **derive the gap, do not trust any digit in this brief;
  a brief's count has gone stale between writing and reading twice
  tonight**):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w204 -b fix/204-bare-citation-form main`
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **COMMIT YOUR REPORT on your branch before reporting done**, and name
  the sha. **Do NOT write a report's BASENAME into a brief or a doc
  casually**: `check-brief-report-references.py` treats that as a
  CITATION and will require the file to exist. It went red on my own
  brief tonight for exactly that.
- **Correct this brief where it is wrong.** Every agent has.

## §B — The finding

`suborch-196` read all 64 `DESIGN.md:N` citations in `docs/adr/`. It
then named what it had NOT read, and that is you:

**Seven ADRs - 0002, 0008, 0009, 0011, 0015, 0023, 0030 - carry ONLY the
bare `:NNN` form and were outside that sweep entirely.**

**THE PROOF IT MATTERS IS ONE LINE.** `ADR-0017:67`:

> "`DESIGN.md:515` is amended, and `:489-490`'s seven-member
> requirement then holds"

`:489-490` is a citation into the design. **Three independent selectors
miss it**: mine, `suborch-196`'s, and the register's own population
query. Each was written to find the qualified form; the bare form is
what a human writes when the file is already named in the sentence.

**THIS IS THE CONTAINER QUESTION, INVERTED.** Tonight a selector with no
left boundary matched MORE than its subject and I published a false
finding from it. Here three anchored selectors match LESS. Both were
invisible until someone read a line instead of running a pattern.

## §C — What to build, in this order

1. **THE DISCRIMINATOR FIRST, and it is the hard part.** A bare `:NNN`
   also matches line numbers in prose, ports, times, ranges, and every
   `file.py:123` citation's tail. **Derive what makes a bare form a
   CITATION rather than a number** - most likely proximity to a naming
   sentence, but MEASURE that rather than assuming it. **A selector you
   cannot defend is worse than no selector**; say so and stop if you
   cannot build one.
2. **Then the population by KIND**, repo-wide and not only `docs/adr/`:
   which files, how many sites, and crucially **which sites have NO
   nearby sentence naming a file**, because those are unresolvable by
   any reader.
3. **Then classify what you can**, using the vocabulary of
   `CITATION-READ-ADR-VERDICTS.md`: `CORRECT` / `WRONG` / `DRIFTED` /
   `BOUNDARY`. **DRIFTED and WRONG stay separate classes** - drift is
   right-when-written, wrong never named its subject, and they need
   different remedies. If you cannot date a citation, `git log -S
   --reverse` on the citing line is the instrument; **`git blame` is
   NOT** - it returns the last commit to TOUCH the line, which for prose
   is a later rewrite, and it produced a three-day error in #196.

## §D — Two questions I want answered, and I am not pre-answering them

- **Is an UNANCHORED bare citation a defect in itself?** A citation a
  reader cannot resolve without guessing the file is arguably worse than
  one that drifted, because there is nothing to check it against.
- **Should this form enter the wrong-subject register at all?** It may
  be a different defect class deserving its own record. Describe it and
  let Tier 0 rule; **do NOT create a task for a decision I should take.**

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-design-citations.py
    uv run --frozen python docs/reviews/check-clause-citations.py
    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/check-brief-report-references.py

**Read each exit code on its own line.** Do not write
`cmd >/dev/null && echo OK` - under `set -e` only the LAST command of an
AND-list triggers errexit, and that pattern hid a real red from me twice
tonight. **actionlint is NOT installed here**; say so rather than
claiming it.

If you add rows to `WRONG-SUBJECT-REGISTER.md`, its arithmetic section
changes too or the file contradicts itself, and `grep -c '^| WS-'` must
match what that section says.

## §F — Context you are owed

- `suborch-199` is live in `fmj-worktrees/w199` on the brief-report
  gate. **Do not touch that worktree or its files.**
- **The push is HELD** and only Phil pushes. You commit to your branch
  and stop.
- Open and NOT yours: #203 (the 46 DRIFTED ruling, mine), #194's
  remaining half, #106/#160 (blocked), #158/#9 (Phil's), #162 (standing
  board hazard).
