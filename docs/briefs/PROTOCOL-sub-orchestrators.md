# PROTOCOL — sub-orchestrators, and who is allowed to spawn whom

Three tiers. Each tier exists because the tier above it is too expensive
to spend on the work below it.

    TIER 0  main orchestrator (me)   merges, pushes, rules, holds the board
    TIER 1  sub-orchestrator  OPUS   one LARGE piece, its OWN worktree
    TIER 2  worker            SONNET grunt work with a stated acceptance test
    TIER 2  trivial worker    HAIKU  mechanical, verifiable at a glance

## What only Tier 0 does, and it is not negotiable

**Merging and pushing.** No sub-orchestrator merges to `main`, pushes to
any remote, or moves another agent's branch. This is not ceremony: five
branches merged today and *every one of those merges surfaced a defect no
branch could see alone*. That only works if one reader sees them all.

**Ruling.** A frozen design changes only by numbered ADR. A
sub-orchestrator that thinks the design is wrong reports it and stops; it
does not decide.

**The board.** Tier 0 keeps the task list. Tier 1 reports findings; Tier 0
decides what becomes a task.

## Tier 1: sub-orchestrator (opus)

Dispatched with `subagent_type: general-purpose`, `model: "opus"`,
`isolation: "worktree"`.

**THE WORKTREE IS THE POINT.** Today a sweep was blocked for a day because
three agents shared one checkout, and separately a live sandbox was
destroyed mid-run taking hours of uncommitted work with it. An isolated
worktree removes the first problem. It does **not** remove the second —
see the commit rule below.

A Tier-1 brief must carry:

1. **§A canon** — read `docs/briefs/PREAMBLE.md` first, in full. Read the
   design at the freeze, never the working tree.
2. **One large piece with a decomposition.** If it cannot be split into
   at least two independently checkable sub-pieces, it is not Tier-1
   work — do it directly and save the process.
3. **The measurement it must make FIRST**, before any fix. Numbers in the
   brief are hypotheses; the brief says so and says to replace them.
4. **What it must NOT do**: merge, push, rebase another branch, `git
   stash`, wire a new gate before its backlog is zero.
5. **Its own budget**: how many Tier-2 agents it may spawn at once.

### Tier 1's obligations

- **COMMIT AS YOU GO, on your own branch, from the first working
  increment.** A worktree with zero commits has nothing in the object
  database; deleting the directory deletes the work outright. This is
  measured, not theoretical — it happened today and cost a rebuild.
- **Script your edits.** The one task that survived its sandbox being
  destroyed survived *because every edit was applied by a script and could
  be replayed*. Hand-typed edits are unrecoverable.
- **Re-measure every number you were given.** Six agents corrected me
  today and every one was right. A brief's numbers are the author's best
  guess at dispatch time.
- **Report what you could NOT settle**, separately from what you did not
  attempt.
- **CLOSE EVERY WORKER YOU SPAWN, THE MOMENT IT IS DONE.** `TaskStop` it
  as soon as you have its result and that result is committed on your
  branch. A finished agent holds a pane forever otherwise, and panes are
  the binding constraint (below) - an idle worker of yours is a Tier-1
  dispatch somewhere else that silently never starts.

  **Before stopping any worker, check what would die with it.** Stopping
  an agent does not delete its commits, but it does destroy anything it
  has not committed and not reported. So: take the report, confirm the
  work is committed, THEN stop. Never stop a worker to tidy up while it
  is still running.

### Two environment traps, both measured on the FIRST Tier-1 dispatch

**`isolation: "worktree"` cuts from the SESSION's outer repo, not from the
one you mean.** The first sub-orchestrator was pinned to a worktree of a
different repository entirely — no `docs/briefs`, nothing it had been sent
to read — and the write guard refuses `git -C` back out of it. **So every
Tier-1 brief must name the absolute repo path and say to `cd` there and
create its own worktree if the one it is given is wrong.** The agent
worked this out unaided and said so; the next one should not have to.

**A Tier-1 agent has no task tools.** `TaskCreate/TaskGet/TaskUpdate`
resolve to nothing in a subagent session, so a sub-orchestrator cannot
claim its own task or file findings on the board. **`SendMessage` to
`team-lead` IS its board**, and Tier 0 owns every task row on its behalf.
Say this in the brief; otherwise the agent reports, correctly, that the
task was never claimed and cannot tell whether that matters.

### The process list is SHARED. It is other people's data.

With several agents live in different worktrees of one repo, `ps`, `pgrep`
and shared `/tmp` paths stop being evidence about YOUR work.

Measured, self-caught by a review agent on the same day: it backgrounded a
suite run, then read "still running" four times. Its subshell had never
survived, so the output file was **empty — and an empty file is
byte-identical to a not-yet-flushed one**. The `pytest` processes it could
see belonged to a *different agent*. The instrument confirmed a job that
had never started, using a sibling's process as the proof.

**So**: write a start marker into your output file before the work begins,
so "empty" and "never started" are distinguishable. Capture the PID you
actually spawned and check that. Prefer waiting on your own child over
polling anything global. And never restore, clean, or kill on the strength
of a shared process list — a harness owns its tree for the whole run, and
the tree you are looking at may be someone else's.

## Tier 2: workers (sonnet), trivial workers (haiku)

Spawned BY a Tier-1 agent, inside its worktree.

**SONNET — grunt work with a stated acceptance test.** Mechanical sweeps
across many files, running a harness and tabulating results, drafting a
report section from measurements the parent supplies. The parent must give
it: the exact container, the acceptance test, and the instruction to
report the number it actually got rather than the one expected.

**HAIKU — trivial and verifiable at a glance.** Reformat a table, count
occurrences, extract fields, rename a symbol at N sites the parent has
already enumerated. If checking the output costs more than doing it, it
was the wrong tier.

**NEITHER TIER JUDGES.** A worker that hits an ambiguity reports it
upward; it does not decide. A correctness call — is this citation right,
should this range widen, is this exemption legitimate — is Tier 1 at
minimum, and often Tier 0.

## The budget, and the one hard constraint

**Panes are finite.** Dispatch fails with `no space for new pane` and the
failure is not queued — the work simply does not start. Every tier costs
one.

    Tier 0 concurrent Tier 1:   2      (3 only if two are read-only)
    Tier 1 concurrent Tier 2:   2
    worst case:                 2 + 4 = 6 panes

**Tier 1 must not spawn a Tier 2 for work it could finish in one tool
call.** A haiku agent that costs a pane to save thirty seconds is a net
loss, and it is the loss that is easiest to talk yourself into.

## How Tier 0 decides the tier

| The work | Tier |
|---|---|
| Touches a frozen artefact, or rules something | 0 |
| Large, decomposable, needs its own tree | 1 |
| Mechanical over a container the parent enumerated | 2 sonnet |
| Verifiable at a glance | 2 haiku |
| Needs one tool call | nobody — just do it |

## Reporting

Tier 2 reports to its Tier-1 parent. Tier 1 reports to `team-lead` by
`SendMessage`, with: what it measured and what the number actually was,
what it changed, what it deliberately did NOT change, every gate exit code
read on its own line, and what it could not settle.

**A Tier-1 report that contains no correction of its own brief is
suspicious.** Every substantial agent report today corrected something.
