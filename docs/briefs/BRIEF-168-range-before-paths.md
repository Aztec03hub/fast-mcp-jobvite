# BRIEF — #168 (HIGH): NONE is decided by range alone, so a declaration that reads nothing clears it

You are `suborch-168`. The defect is in a gate **I** built, and it makes
the number every handoff quotes manipulable.

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN, you may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md`
5. `CONTRIBUTING.md`
6. **`docs/reviews/REVIEW-R17.md` §3** — the finding and its control, first-hand.
7. `docs/reviews/check-review-coverage.py` — your subject, whole docstring.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` trailers, ever.
- **You do not push and you do not merge.** Commit on your branch; Tier 0 merges.
- **Own worktree**, cut from `origin/main` at `22c9873` or later:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w168 -b fix/168-range-before-paths`
- **`TaskGet` before acting on any assignment**, and compare the TEXT to
  this brief. A completion echo replays a superseded description, dated
  LATER, addressed back to you under your own name (#162, measured three
  times). Never "check who sent it".
- **CI's exact invocations.** `uv run --frozen python`, never bare
  `python3`; `actionlint` needs `SHELLCHECK_OPTS=--severity=warning`.
- **Report by `SendMessage` to `fastmcp-jobvite`**; findings to a `.md`
  under `docs/reviews/`.
- **Correct this brief where it is wrong.** Thirteen of thirteen agents
  have found an error in theirs and every correction held.

## §B — Files you OWN

    docs/reviews/check-review-coverage.py
    docs/reviews/probe-coverage-ratchet.py
    docs/reviews/review-coverage-backlog.txt
    docs/reviews/<your findings .md>

Nobody else is in the tree as I write. If that changes you will be told.

## §C — The defect, already controlled by R17

`check-review-coverage.py:428-431` decides `NONE` by whether any round's
**RANGE** contains the commit, and applies the **PATH** filter only
afterwards, to decide `PARTIAL`.

**So a wide range with a narrow path list moves commits out of `NONE`
without anyone reading them.** R17's control: one declaration over the
whole container range claiming a single 7-character file
(`docs/DESIGN-FREEZE.txt`) takes `COVERED BY NOTHING` **26 → 0** and
`PARTIAL` 42 → 62.

**This is R12-H3 one column over.** R12-H3 was "the metric IMPROVES when
you DELETE a declaration" — fixed by pinning `CONTAINER_BASE`. This is
the same defect from the other side: it improves when you ADD a
declaration that reads nothing.

`NONE` is the number every handoff I have written quotes as "nobody has
looked at these". R17 applied this to its OWN work rather than banking
it: of its 26 `NONE`-clears only **2** are real, and REVIEW-R17.md §3
names all 24 artifacts.

## §D — What to build

**A commit counts as covered by a round only if that round claims at
least one non-record file the commit actually touches.** A commit whose
every touched file falls outside every claiming round's paths has been
read by nobody and is `NONE`, not `PARTIAL`.

Think about, and RULE on, these before coding:

- A commit that touches ONLY record paths (`CHANGELOG.md`,
  `docs/worklogs`, `docs/plans`). Today `records_skipped` counts those.
  Under the new rule, is such a commit covered, `NONE`, or a third
  thing? **State the answer in the file**, with the reason.
- A MERGE whose `--name-only` is empty. R17 and REVIEW-151-R1 BOTH
  investigated `--cc` and BOTH withdrew it as not-a-defect — read §3
  before you re-derive it a third time.

**The existing PLANT arm does NOT cover this.** It perturbs a
declaration's EXISTENCE; this defect is about its WIDTH. Add an arm that
plants a full-range, one-file declaration and requires the commits it
"clears" to stay outstanding.

## §E — How your work will be judged

- **Both arms.** The new arm must go RED on the current code and GREEN
  on yours. Amputate your own fix and require the arm to fail; read
  WHICH arm, never the exit code.
- **NO ARM MAY MUTATE THE TREE.** `--backlog` and `--reviews` exist
  precisely so a control can point at a temp copy. Every one of the
  existing 9 arms obeys that; yours must too.
- **The backlog will move under you.** Re-derive at the end, and expect
  your fix to INCREASE the outstanding count — a fix that leaves it
  unchanged did nothing. Report before/after with refs and shas.
- All gates green before you report, each exit code on its own line,
  including `pre-commit run --all-files` and the full suite (887
  passed, 0 skipped).
- Separate COULD NOT SETTLE from did not attempt.

## §F — Context

- **DO NOT apply R17-H2's corrected path list** (#169). Widening any
  declaration before this fix banks artifacts at scale. Your fix is what
  unblocks it.
- The backlog file's header already records that, until this is closed,
  a line LEAVING it is weaker evidence than a line entering it. **Update
  that note when you close it.**
- CI's first-ever deep run is in flight; do not add a red step.
