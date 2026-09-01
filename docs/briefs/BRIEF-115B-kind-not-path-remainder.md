# BRIEF #115B — finish "population by KIND, not by path"

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full first, and follow it.** Read the
design at the freeze, never the working tree:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

## §B — There is prior work, and it is UNVERIFIED. Read it as a lead.

Branch `fix/kind-not-path`, single commit `f7aa6e8`. Its own message is
the honest account: the agent working #115 was killed mid-task by an
account usage limit, never reported, and the work is *"UNREPORTED,
UNFINISHED and UNVERIFIED"*. It was committed only so a worktree cleanup
could not destroy it.

    git show f7aa6e8 --stat

**DO NOT MERGE, REBASE OR RESUME THAT BRANCH.** It is cut from `dad014e`,
now **104 commits behind main**, and the file it edits most heavily -
`docs/reviews/check-design-citation-shape.py` - has since been rewritten
by #126, wired into CI, and given a fifth detector's worth of context.
Rebasing 158 changed lines across that is a merge exercise, not the task.

Treat `f7aa6e8` as a **lead to re-derive on today's main**: read what it
was reaching for, then decide for yourself what is still true.

## §C — What is actually still undone, measured on main today

    docs/reviews/check-env-vars-are-declared.py:91
    docs/reviews/check-settings-are-read.py:161
        for path in sorted((ROOT / "src").rglob("*.py")):

Both pick their population with a **path glob**. That is the defect
#115 named: a population selected by PATH is blind to the member that
lives somewhere the glob does not reach, and blind to an untracked or
newly-moved file. The rule this repo has settled on is to enumerate the
CONTAINER - `git ls-files` - and select by KIND.

`docs/reviews/check-design-citations.py` already does it that way; use it
as the shape rather than inventing a second one that can disagree with it.

**FIRST, MEASURE WHETHER IT MATTERS.** For each of the two checkers,
compare the population the glob yields against the population `git
ls-files` yields. **If the sets are identical today, say so** - the fix is
then about the defect that cannot yet have happened, which is a weaker
but still legitimate case, and it must be argued as such rather than
dressed up as a live bug. If they differ, name the members the glob
misses; those are the finding.

`check-cross-references.py` showed no glob at all in my scan. Establish
what it actually does before changing it - a third file changed on a
guess is how a sweep acquires a defect.

## §D — The second half of `f7aa6e8`, and it is a different task

Much of that WIP is not population selection at all: it rewrites
line-number citations into SECTION anchors - `DESIGN.md:373-375` becoming
`§4.3`, and so on. That is the "anchor on the subject, not the line"
discipline, and it is worth doing, but it is a separate change with a
different risk profile.

**Do them as separate commits.** If you judge the anchor rewrite too large
to carry here, say so and leave it - a task that reports what it did not
do is worth more than one that half-does two things.

## §E — Constraints

- Branch `fix/kind-not-path-2` off current `main`. Do NOT reuse the old
  branch.
- **Do not merge, do not push.** I merge and push, always.
- No `Co-Authored-By` or "Generated with" trailer.
- Do not `git stash` — other agents are live on this tree.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- A new `docs/reviews/check-*` enters the wired-checker container and must
  then be wired or carry a stated exemption — `check-checkers-are-wired.py`
  enforces that now, and it did not exist when `f7aa6e8` was written.
- Gate before committing, each exit code on its own line: `ruff check`,
  `ruff format --check`, `mypy`, `pytest`, and
  `check-checkers-are-wired.py`. Do not chain them with `&&` — errexit
  does not fire for a non-final command in an AND-list, and that shape has
  hidden a red gate four times here today.
- Cite `file:line` only from `grep -n` or a numbered Read.

## §F — Report back

`SendMessage` to `team-lead`: the two population comparisons with their
actual numbers, what you changed and what you deliberately did not, every
exit code, and anything you could not settle. **If `f7aa6e8` turns out to
be right about something I have described here as undone, say so** — it
was written by someone who could not report, and it deserves a fair
reading rather than a convenient one.
