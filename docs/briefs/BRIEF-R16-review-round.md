# BRIEF — R16: review the 86 trunk commits no round covers

You are `review-r16`, a Tier-1 reviewer. **You are not fixing anything.**
You are reading commits nobody has read, reporting what you find, and
declaring — honestly — what you actually read.

## §A — Standing rules (read FIRST, in this order)

Read IN FULL before any finding. Where a numbered ADR conflicts with a
standard, the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN. It is the authority; where a reviewed
   commit disagrees with it, the commit is wrong unless an ADR says so.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `CONTRIBUTING.md`
5. `docs/reviews/check-review-coverage.py` — read its DOCSTRING before
   you write a declaration. It explains exactly what a declaration
   claims and what it cannot check.
6. `docs/briefs/HANDOFF-2026-09-01-orchestration.md` — current state.

Hard rules:

- **NEVER print or commit a secret.**
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push, do not merge, and do not FIX.** Report findings;
  Tier 0 rules on them and dispatches the fixes.
- **Make your own worktree**, detached at the trunk tip:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r16 -b review/r16 origin/main`
- **Run CI's EXACT invocation, flags and all.** `uv run --frozen python`,
  never bare `python3`; `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning`.
- **EVERY finding at EVERY severity, nits included, ships with a
  suggested fix.**
- **Cite `file:line` only from `grep -n` or a numbered read.** Never
  read a line number off an unnumbered window.
- **Report by `SendMessage` to `fastmcp-jobvite`**, and write
  `docs/reviews/REVIEW-R16.md`.
- **Correct this brief where it is wrong.** Ten of ten agents have found
  an error in their brief and every correction held.

## §B — Your population, and it is DERIVED not listed

`docs/reviews/review-coverage-backlog.txt` records **86 commits** that no
review round covers: 47 `NONE` (no round's range contains them) and 39
`PARTIAL` (a round claimed the range but not every file they touch).
That file is your worklist. **Re-derive it** — run
`uv run --frozen python docs/reviews/check-review-coverage.py` and work
from what it reports, not from a list I typed.

Their 235 file touches, measured:

     55  docs/reviews          22  docs/briefs        14  docs/worklogs
     12  .github/workflows      7  src/fast_mcp_jobvite
      6  .secrets.baseline     the rest: scripts/*.sh, one or two each

**THE LEAST-REVIEWED CODE HERE IS THE CODE THAT DOES THE REVIEWING.**
That is the finding this backlog exists to answer, and it is why you are
reading `docs/reviews` and `scripts` rather than `src`.

`docs/worklogs` is already an exempt RECORD path — you need not claim
it. `docs/briefs` is deliberately NOT exempt: a brief INSTRUCTS an agent
and has carried substantive rulings, so a wrong brief produces wrong
work rather than merely misdescribing it.

## §C — What to look for, in priority order

The recent work in this range is checkers, probes and controls. Its
characteristic failures, all measured here in the last day:

1. **A CONTROL THAT PASSES WITHOUT TESTING ITS SUBJECT.** Three found in
   one evening. For any arm claiming to prove something, ask WHY it
   passes, not THAT it does. Amputate: put the defect back and require
   the arm to go red.
2. **A SELECTOR THAT CANNOT SEE ITS OWN POPULATION** — a hand-kept list
   beside its container, a prefix filter, a path glob, a newline count.
   Assert set equality against the container, never a sample.
3. **A CLAIM IN A COMMENT THAT THE CODE DOES NOT KEEP.** The most
   expensive defects here have all been things the code said about
   itself: a comment asserting a gate that never existed, a citation
   range holding half its claim, a figure retyped rather than derived.
4. **A GATE RUN WITHOUT CI'S FLAGS**, which asks a different, weaker
   question. Three instances in one evening, one of them mine while
   merging the task about it.
5. **A NUMBER WITHOUT ITS CONTAINER**, and any figure inherited rather
   than reproduced.

## §D — The declaration, which is the deliverable's other half

End `REVIEW-R16.md` with a `REVIEW-COVERS` line naming what you ACTUALLY
read:

    <!-- REVIEW-COVERS: <base>..<head> PATHS: docs/reviews scripts .github docs/briefs -->

**DECLARE ONLY WHAT YOU READ.** A declaration is a claim by its author
and the checker cannot verify it — I proved that with a planted
declaration that cleared 63 outstanding commits at exit 0. Over-claiming
manufactures coverage for code nobody opened, which is worse than the
visible gap, because an absence you can see beats a false presence you
cannot.

So: if you read `docs/reviews` and `scripts` but not `.github`, declare
the two. If you read only part of the range, declare that part. **A
narrower true declaration is the correct outcome; a wide false one is a
defect.** Say in the report which commits you skimmed versus read.

`REVIEW-R16.md` must itself carry a declaration or it lands in
`unexplained` and the checker returns 1.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py

The first should show the backlog SHRINKING by however many commits your
declaration legitimately covers, and will list what your declaration
does NOT cover as `CLEARED, still recorded` — **remove exactly those
lines from `review-coverage-backlog.txt`, and no others.** Report the
before and after counts, each with its ref and sha.

## §F — Context you are owed

- Three agents are live: `suborch-161` owns `.github/workflows/ci.yml`,
  `suborch-156` owns `scripts/check-u1-boot-amputation.sh`,
  `suborch-157` owns the mirror workflow. **You edit none of them** —
  you are read-only over the whole tree except your report and the
  backlog file.
- CI has never produced a green run on this trunk. #161 is closing the
  last red step. Do not add one.
- If you find something that needs fixing, it becomes a task, not a
  commit. Say so plainly in the report.
