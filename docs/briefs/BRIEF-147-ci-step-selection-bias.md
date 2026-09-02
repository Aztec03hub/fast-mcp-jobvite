# BRIEF — #147: the CI-step probe's selection is biased toward the steps that cannot differ

You are `suborch-147`, a Tier-1 sub-orchestrator. Read this whole file
before touching anything.

## §A — Standing rules (read FIRST, in this order)

Read these IN FULL before any edit. They are the canon; nothing you do
may contradict them, and where a numbered ADR conflicts with a standard,
the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN. You may not change it. Only a numbered ADR may.
2. `docs/adr/` — every ADR, in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md` — your operating protocol.
5. `CONTRIBUTING.md`

Hard rules:

- **NEVER print or commit a secret.** A test that prints a failing value
  publishes it.
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push and you do not merge.** Commit on your own branch in
  your own worktree and report. Tier 0 merges.
- **Make your own worktree.** The one you are dispatched into is often
  cut from the wrong repo. `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w147 -b fix/147-ci-step-selection`
- **Run CI's EXACT invocation, flags and all.** Copy the line out of
  `.github/workflows/ci.yml`. `uv run --frozen python`, not `python3`.
  Running a gate without CI's flags is a different, weaker question —
  that is literally the defect you are fixing.
- **Report by `SendMessage` to `fastmcp-jobvite`** when done, and write
  your findings to a `.md` in `docs/reviews/`. A report that lives only
  in your chat is stranded work.
- **Correct this brief where it is wrong.** Every sub-orchestrator so far
  has found an error in its brief and every correction held. A report
  with no correction is the anomaly, not the norm.

## §B — Files you OWN (nobody else may touch them this run)

    docs/reviews/probe-ci-checker-steps.py
    docs/reviews/probe-ci-checker-steps-control.py
    docs/reviews/<any new .md you write>

**You do NOT own `.github/workflows/ci.yml`.** `suborch-143` is editing
it right now. READ it as much as you like; do not write one byte of it.
If your fix genuinely requires a ci.yml change, STOP and report that —
do not make it.

## §C — The task

See task #147 on the board for the full statement. The short form:

`probe-ci-checker-steps.py` runs CI's checker steps verbatim so that a
local green means what a CI green means. It runs 12 of 78. It skips 36
as "multi-line block, has its own setup".

**The 36 it skips are not a random 36.** A step is multi-line PRECISELY
because it carries a flag, an env var, or `|| exit 1` handling — and a
flag is exactly what makes CI's invocation differ from a bare local one.
The 12 it runs are single-line no-argument invocations: the case that
cannot go wrong this way. So the probe is blind in precisely the
direction that matters, and it proved it: it could not run
`Committed file types, whole tree`, the step that refused the tree for
127 commits.

Two deliverables:

1. **Shrink the 36 honestly.** Extract the checker invocation LINE out
   of a multi-line `run:` block whose only other shell is trivial
   (`set -uo pipefail`, a trailing `|| { echo ...; exit 1; }`). Report
   what remains genuinely unrunnable WITH ITS REASON.
   **REFUSE to shrink the bucket by loosening `_SHELLY` into accepting
   real shell.** If you cannot extract a block safely, it stays counted.

2. **Add the arm that would have caught this.** For every checker CI
   invokes WITH arguments, assert that the same checker invoked WITHOUT
   them is not silently a different, weaker question.
   `check-committed-file-types.py` bare vs `--all` is the measured
   instance. **Nobody has looked for others.** Look. Report the count
   and the container you enumerated to get it.

## §D — How your work will be judged

- **Enumerate the container, assert set equality.** A hand-kept list
  beside its container is blind to the member nobody added. If you write
  a list of step names, something must prove it equals the set of steps.
- **Every count carries its container.** "78 steps" is meaningless
  without "in ci.yml alone" — a sibling count of 80 exists for "all
  workflows" and the two have been confused here before.
- **Controls before claims.** A control that never runs its subject
  passes for free. Amputate: put the defect BACK and watch the probe go
  red. If it stays green, your control is vacuous and you must say so.
- **Read WHICH rows die, never score a kill on the exit code.**
- **`ruff check .`, `ruff format --check .`, `mypy`, and `pytest` must
  all be clean before you report.** Run them with CI's exact invocation.

## §E — Context you are owed

- Tonight's trunk was red for 127 commits behind a gate nobody ran with
  its flags. Tier 0 then repeated the same mistake an hour after
  recording it, using `python3` where CI uses `uv run --frozen python`.
  This class of error is live, not historical.
- A partial fix landed at `be13055`: the gate now prints `[staged set]`
  or `[whole tree]` and shouts when a staged run examined zero files.
  That stops THIS instance recurring and does nothing about the
  selection bias, which is your task.
- Related open work: #125 (checkers-are-wired, same family one level
  up), #153 (that checker selects BY PATH, so a checker under `scripts/`
  can be unwired forever at exit 0). Do not fix #153; note anything you
  learn about it.
