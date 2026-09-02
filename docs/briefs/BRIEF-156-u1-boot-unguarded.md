# BRIEF — #156 (HIGH): thirteen mutations whose failure nothing consumes

You are `suborch-156`, a Tier-1 sub-orchestrator.

## §A — Standing rules (read FIRST, in this order)

Read IN FULL before any edit. Where a numbered ADR conflicts with a
standard, the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN, you may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md` — your operating protocol.
5. `CONTRIBUTING.md`
6. `docs/worklogs/WORKLOG-152-publishers.md` — the run that found this.

Hard rules:

- **NEVER print or commit a secret.**
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push and you do not merge.** Commit on your branch in
  your own worktree and report; Tier 0 merges.
- **Make your own worktree**, cut from `origin/main` at `ccbdaae` or
  later: `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w156 -b fix/156-u1-boot-guards`
- **Run CI's EXACT invocation, flags and all** — copy the line out of
  `ci.yml`; `uv run --frozen python`, never bare `python3`. I have
  misread a gate three times tonight by dropping a flag, most recently
  by omitting `SHELLCHECK_OPTS=--severity=warning` from actionlint.
- **Report by `SendMessage` to `fastmcp-jobvite`** and write findings to
  a `.md` under `docs/reviews/`.
- **Correct this brief where it is wrong.** Nine of nine
  sub-orchestrators have found an error in their brief and every
  correction held. A report with no correction is the anomaly.

## §B — Files you OWN this run

    scripts/check-u1-boot-amputation.sh
    docs/reviews/<any new probe or report you write>

**You do NOT own `.github/workflows/ci.yml`** — `suborch-161` is in it,
fixing the secret-scan step that keeps CI red. Read it freely; write
nothing. If your fix needs a ci.yml step, STOP and report that.

You do not own the other 36 `scripts/*.sh`. See §D before touching one.

## §C — The defect

`scripts/check-u1-boot-amputation.sh:31` sets `set -uo pipefail` —
deliberately NO errexit, which is this project's rule and is correct.
But **not one of its 13 mutation heredocs is guarded** by `|| exit`,
`if !`, or a `$?` read.

So a row whose anchor has MOVED prints a traceback and then measures an
**UNMUTATED** tree. The harness reports a survivor, and that survivor is
an artefact of the mutation never landing. **Every survivor this harness
has ever named is suspect until the guard exists.** 6 of the 13 have no
uniqueness assertion at all, so nothing else catches it either.

The sibling that already gets this right is
`scripts/check-u15-gate-amputation.sh:140` — `[ $? -eq 0 ] || exit 1`
after the heredoc. Read it before writing anything.

`suborch-152` CORRECTED ITSELF on this and the correction matters: it
first recorded "no landing check anywhere". The harness DOES assert at 7
sites. The defect is the 6 unasserted sites plus the universally
unconsumed exit status — not a total absence. Verify that split yourself
rather than taking either of us on trust.

## §D — Do NOT sweep the siblings on this pattern

`#152`'s central finding is that a shape rule over these files was WRONG
on 4 of the 6 harnesses it named — two of them legitimately behave the
way the rule called a defect. If you find the same unguarded shape
elsewhere, **report it with the landing sites you read**; do not fix it
in this run. One file, read completely, beats 37 changed on a pattern.

## §E — How your work will be judged

- **A POSITIVE CONTROL, both arms, and it is the whole job here.** Move
  an anchor so a mutation cannot land, and require the harness to FAIL
  rather than report a survivor. Then restore it and require the
  harness to pass. Without the first arm the fix is a guess.
- **Read WHICH rows die, never score on the exit code.**
- **Do not strand a mutation.** This harness edits the tree. Two things
  now exist for exactly that: `docs/reviews/restore-stranded-mutation.sh`
  and `--restore-only` (see `docs/worklogs/WORKLOG-146-131-stranded.md`).
  Better still, design your control so it never needs them — point it at
  a copy rather than the tree, the way `check-review-coverage.py
  --backlog` does. **And pass an explicit long timeout to any command
  that runs a suite**: I stranded two plant files tonight by hitting a
  default two-minute timeout on my own probe.
- **Every count carries its container** — "13 heredocs in
  check-u1-boot-amputation.sh at `<sha>`", not "13".
- `ruff`, `ruff format`, `mypy`, `bash -n`, `shellcheck --severity=warning`,
  `pytest` (887 passed, 0 skipped, floor 887), and the `docs/reviews`
  gate set must all be clean, each exit code on its own line.
- Separate what you COULD NOT settle from what you did not attempt.

## §F — Context you are owed

- CI has never produced a green run on this trunk. One step remains
  (#161) and another agent has it. Do not touch it.
- The audit-shape probe hit a neighbouring version of this defect
  tonight (#130): its amputation DELETED a statement that bound a name,
  so the crash it caused itself read as a verdict. Same family — a
  mutation that does not land the way the harness thinks it landed.
