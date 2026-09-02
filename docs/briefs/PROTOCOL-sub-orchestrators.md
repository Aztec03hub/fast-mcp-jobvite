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

**A Tier-1 agent's task tools are DEFERRED, NOT ABSENT — and this
paragraph asserted the opposite as measured fact until a sixth run
checked it.** It said `TaskCreate/TaskGet/TaskUpdate` "resolve to
nothing in a subagent session". That is false. `PREAMBLE.md` already
said the right thing — *"the shared task-list tools are DEFERRED, not
absent"* — so two canon documents contradicted each other and the wrong
one was the one being pasted into briefs.

**What is actually verified**, stated at the width it was tested:
`ToolSearch select:TaskGet,TaskList` returns both schemas from a Tier-1
session; `TaskGet <id>` returns the live row; and `TaskUpdate` writes
`status`, `owner`, `subject` and `description` (measured by
`suborch-170` closing #170, under a brief that explicitly granted the
write mandate). **`TaskCreate` has NOT been tested from Tier 1** — the
agent that could have declined, because deciding what becomes a task is
Tier 0's, not because the tool was thought absent.

**THE PREVIOUS SENTENCE ASKED NOT TO BE WIDENED WITHOUT A MEASUREMENT,
AND THAT IS EXACTLY HOW IT GOT WIDENED.** It read *"`TaskUpdate` and
`TaskCreate` have NOT been tested from Tier 1"* and gave the reason as
*"writing to a board it does not own is not its call"* — one reason
covering two tools, which hid that they are untested for **different**
reasons. `TaskUpdate` on an agent's OWN task was never a board it does
not own; it was simply never tried. A brief that granted the mandate got
it measured in one call. **`TaskCreate` remains untested for the reason
that actually applies, and that reason is a RULING, not a gap**: Tier 1
reports findings and Tier 0 decides what becomes a task, so a Tier-1
agent has no occasion to call it. Do not "fix" that by testing it.

This is the third canon claim about tool behaviour on this project to be
wrong in prose that no gate reads, and the second inside this file.

**A TIER-1 AGENT MUST `TaskGet` ITS OWN TASK BEFORE ACTING ON ANY
ASSIGNMENT.** That is the check the false claim suppressed, and it is
exactly what catches a stale assignment echo: the sixth run received an
echo carrying a SUPERSEDED description, dated later than the work it
hid, and identified it only by comparing against the live row.

**MEASURED TWICE MORE ON 2026-09-01, and the obvious tell FAILED once.**
Runs nine and ten each received a completion echo and each refused it.
Three facts, because agents keep having to rediscover them:

- **The echo is timestamped LATER than the correction it hides.** One
  replayed three figures its own run had just measured wrong. Recency is
  the WRONG tiebreak here.
- **`assignedBy` naming YOU is not a reliable tell.** It fired for one
  run and not the other, whose echo said `assignedBy: team-lead`. What
  caught that one was comparing the echo's TEXT to the live row, and
  finding the echo predated even the dispatch brief that replaced it.
- **THE GUARDRAILS DO NOT TRAVEL.** An echo carries no §A canon list and
  no §B file ownership. Four agents were live in this tree that evening
  with disjoint ownership stated only in their briefs; an agent acting
  on an echo would have edited a workflow file another agent was in.
  **That makes the echo strictly more dangerous than the brief it
  impersonates.**

So the rule is TEXTUAL, never social: `TaskGet`, then compare the
description against your brief. Never "check who sent it". And when you
complete a task, write the final subject and description BEFORE marking
it complete, so the echo at least replays something true.

**The operative rule is unchanged: `SendMessage` to `team-lead` IS the
reporting channel**, and Tier 0 owns every task row on its behalf. That
was always right. What was wrong was the mechanism given for it — and a
wrong mechanism in a canon document is the exact class this repo keeps
finding, because no gate reads a claim about how a tool behaves.

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

---

## What the first two Tier-1 runs measured, 2026-09-01

**BOTH SPAWNED ZERO TIER-2 WORKERS.** Each judged nothing warranted a
pane; one said so outright — *"~15 sites, not worth a pane"*. **The value
of this tier is JUDGEMENT and ISOLATION, not fan-out.** Do not measure the
protocol by how many agents it starts. The worktree and the bring-me-the-
ruling gate did the work; the fan-out permission went unused and was still
right to grant.

**HANDING A NUMBER AS AN EXPLICIT HYPOTHESIS IS WHAT PRODUCED THE
CORRECTIONS.** Both briefs said *"the count is N — verify it, do not repeat
it"*, and both agents returned a different, better number with its reason.
One found the count was never a single number: the two gates it spanned do
not share a container (51 sites vs 25). **A brief with no checkable number
in it cannot produce that**, which is why the rule about reports that
correct their own brief only works if the brief contains something to
correct.

**WITHHOLDING THE RULING PRODUCED A BETTER DESIGN THAN SPECIFYING ONE.** A
sub-orchestrator told to bring the choice back with trade-offs returned
with the fact that *settles* it — one candidate form provably could not
meet the brief's own acceptance criterion. Ruling on its argument beat
ruling on taste.

**WHEN YOU ASK FOR A CONTROL, ASK FIRST WHETHER THE THING CAN BE MADE
IMPOSSIBLE.** I asked for a control proving that documentation of a new
marker could not itself become an exemption. The agent chose a data file
with a suffix neither scanner reads, so the recursion cannot occur at all.
A structural answer beats a control; the control then costs nothing and
documents that the structure is doing the work.

**AN EXEMPTION MARKER INFLATES FROM ITS OWN DOCUMENTATION.** Measured in
one day: 47 marked lines, 51 after two briefs *discussing* the marker, 60
after merging the review that *found* the defect, 61 now. Every increment
was prose, not an exemption. A bare-substring marker makes writing about
it load-bearing — so **the most careful writers expand the hole fastest.**

---

## Runs 3 to 5, and the pattern that only shows up with five

Three more Tier-1 dispatches (`suborch-144` on two detector tasks, and
two adversarial reviewers). Adding them changes two of the conclusions
above and adds one a smaller sample could not support.

**STILL ZERO TIER-2 WORKERS, ACROSS ALL FIVE RUNS.** Every agent judged
that nothing warranted a pane; two said so unprompted, in nearly the
same words - *every step was one or two tool calls*. **Stop budgeting
for fan-out at this tier.** The permission costs nothing to grant and
has now gone unused five times out of five; the value is the worktree,
the isolation, and the obligation to bring back a measurement.

**EVERY ONE OF THE FIVE CORRECTED ITS OWN BRIEF, AND EVERY CORRECTION
HELD.** That is no longer a hopeful sign, it is the expected output:

- one measured that my "still misses" list named two spellings that are
  DETECTED today, so my conclusion survived on two of its four examples;
- one rejected the option I framed because measurement falsified its
  premise, and settled a question I had deliberately left open;
- one found that a fix of mine was an AMPUTATION SURVIVOR whose own
  stated justification was false;
- one found a number of mine was a DISPLAY CAP I had read as a
  population.

**A REPORT WITH NO CORRECTION IN IT IS NOW THE ANOMALY.** If one
arrives, suspect the brief contained nothing checkable rather than that
the work was flawless.

### THE NEW RULE, and it is the strongest thing five runs taught

**DISPATCH THE REVIEWER BEFORE THE MERGE, NOT AFTER THE PUSH.** Both
review dispatches found HIGH findings in work that was already green on
every gate - one of them in a fix I had written an hour earlier and
argued for in three places. Green gates and a passing probe caught
neither, because both defects were in what the code CLAIMED about
itself, and no gate reads claims.

The corollary is uncomfortable and worth stating: **my own work needs
the same fresh-reviewer treatment as an agent's, and it is the work I am
least likely to send.** The R14 round found two of my defects; its
reviewer then found two more IN MY FIX for the first two.

### What a reviewer must be told, learned the hard way

- **Hand it the numbers as HYPOTHESES and say so.** Both reviewers
  re-measured, and both found a wrong one. A brief with no checkable
  number in it cannot produce that.
- **Name the thing you did not chase.** I gave one reviewer a
  discrepancy I had noticed and skipped - two instruments reporting two
  counts of one container - and flagged it as its highest-value item.
  Handing over a known loose end beats hoping it gets noticed.
- **Tell it to amputate DIFFERENTLY than the probe does.** The R14
  reviewer deleted a whole dispatch branch in a scratch repo rather than
  re-running the probe's own arm, and that is what exposed the survivor.
  **A probe cannot amputate its own subject**: it refuses to run against
  a modified checker, so its guard and its coverage are in tension.
- **Say which worktrees are LIVE and must not be touched.** With three
  agents running, "do not clean anything outside your own scope" stops
  being boilerplate.

### The trap that cost the most, twice in one evening

**RUN THE INVOCATION CI RUNS, ARGUMENTS AND ALL.** A gate run bare when
CI runs it with a flag is a different, weaker question. Measured twice:
a whole-tree file-type gate run without `--all` selects the STAGED set,
empty on a clean tree, so it exits 0 having opened nothing - that hid a
red trunk for 127 commits. An hour after recording the lesson I did it
again with `python3` where CI uses `uv run --frozen python`, and read a
missing-dependency failure as a defect. **Copy the line out of the
workflow file. Knowing the rule is not following it.**
