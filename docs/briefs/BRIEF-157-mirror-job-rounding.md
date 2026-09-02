# BRIEF — #157: the sixth billed job, 95% of whose bill is rounding

You are `suborch-157`, a Tier-1 sub-orchestrator.

## §A — Standing rules (read FIRST, in this order)

Read IN FULL before any edit. Where a numbered ADR conflicts with a
standard, the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN, you may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md` — your operating protocol.
5. `CONTRIBUTING.md`
6. `docs/worklogs/WORKLOG-143-ci-minutes.md` — the run that found this,
   and the method you should reuse rather than reinvent.

Hard rules:

- **NEVER print or commit a secret.** This job pushes to a second
  remote, so it touches credentials. Name them, never print them.
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push and you do not merge.** Commit on your branch in
  your own worktree and report; Tier 0 merges.
- **Make your own worktree**, cut from `origin/main` at `ccbdaae` or
  later: `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w157 -b fix/157-mirror-minutes`
- **Run CI's EXACT invocation, flags and all.** `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning` — I read it as red three times
  tonight by omitting that.
- **READ-ONLY AWS/GitHub API reads need no approval; writes do.** You
  may query the Actions API freely. You may NOT disable, re-enable, or
  re-run a workflow, and you may not change a remote or a credential.
- **Report by `SendMessage` to `fastmcp-jobvite`** and write findings to
  a `.md` under `docs/reviews/`.
- **Correct this brief where it is wrong.** Nine of nine
  sub-orchestrators have found an error in their brief and every
  correction held.

## §B — Files you OWN this run

    .github/workflows/<the mirror workflow file>
    docs/reviews/<your report>
    docs/worklogs/<your worklog>

**You do NOT own `.github/workflows/ci.yml`.** `suborch-161` is inside
it right now fixing the step that keeps CI red, and `suborch-156` has
been told the same. Read ci.yml; write nothing in it.

## §C — What was measured, by suborch-143, over 2026-08-28..2026-09-02

Using `evolv-coder-standards/scripts/ci-minutes.py` (which `--self-test`s
20/20 and requests `filter=all`, verified at its line 326 rather than
from its docstring):

    Mirror to personal fork   n=214   214 billed min   median 3s
    runner time actually consumed:  11 min

**95% of that job's bill is per-job minute rounding — proportionally the
worst job in the repository**, worse than any of the five in the ledger
that #143 consolidated. It was omitted from that ledger because the
ledger enumerated ci.yml's jobs and this lives in its own workflow file:
a hand-written list beside its container, blind to the member nobody
added.

**RE-MEASURE IT YOURSELF before you change anything.** #143's figures
are good and its method is written down, but a figure inherited and not
reproduced is how the 1040s number became load-bearing without anyone
checking it (see #154). Say your window, your run count, and how many
runs REACHED the step — a failing trunk under-reports its own durations,
which this project measured at 50x once already.

**CONTEXT THAT MAKES THIS ODD, and worth understanding before you
optimise:** #18 records that this same workflow "never ran once, 119
runs 119 failures" and was fixed at 647442f. It now runs 214 times in
five days at 3 seconds each and bills a whole minute every time.

## §D — The question, which is not "make it cheaper"

Decide what this job is FOR, then price that. Options worth measuring
before choosing, none of them pre-approved:

- Run it on a schedule rather than on every push. What is the mirror's
  purpose — an off-site copy, or a live one? A daily copy costs ~5 min a
  month; a per-push copy costs 214.
- Fold it into a job that already checks out at depth 0. **Check its
  permissions and its remote credentials first** — it pushes to a
  DIFFERENT remote than every other job, and a fold that inherits the
  wrong token fails in a way that looks like a network error.
- Leave it and record 214 min as the deliberate price of an off-site
  copy. **This is a legitimate answer.** If you reach it, say so with
  the number beside it, the way #143 recorded its CodeQL refusal.

Whichever you choose, the choice is RECORDED with its measurement. A
cost change with no number is the thing #143 corrected in its own
committed header.

## §E — How your work will be judged

- **A count without its container is not a measurement.** "214 min"
  needs "over 214 runs in the window 2026-08-28..2026-09-02".
- **If you change the workflow, prove the mirror still mirrors.** A
  cheaper job that silently stops copying is strictly worse than an
  expensive one that works, and #18 is the precedent: this workflow
  failed 119 consecutive times and nobody read it. Whatever you change,
  say how the next person would notice it had stopped.
- `actionlint` with `SHELLCHECK_OPTS=--severity=warning`, plus the
  `docs/reviews` gate set, each exit code on its own line.
- Separate what you COULD NOT settle from what you did not attempt.

## §F — Context you are owed

- `main` has NO branch protection and ZERO rulesets (#158), so renaming
  a job breaks no required check — that is what made #143's rename safe,
  and it applies to you too.
- CI has never produced a green run on this trunk; #161 is closing the
  last red step. Your work must not add a new one.
