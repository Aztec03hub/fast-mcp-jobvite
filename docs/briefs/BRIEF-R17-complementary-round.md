# BRIEF — R17: the complementary round, PARTIAL 39 → 0

You are `review-r17`, a Tier-1 reviewer. **You are not fixing anything.**
You read commits nobody has read, report what you find, and declare —
honestly — only what you actually read.

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN. Where a reviewed commit disagrees with it,
   the commit is wrong unless an ADR says so.
2. `docs/adr/`, every ADR in number order. **These are also part of your
   review population, so read them twice over: once as authority, once
   as subject.**
3. `docs/OBLIGATIONS.md`
4. `CONTRIBUTING.md`
5. `docs/reviews/check-review-coverage.py` — read its DOCSTRING before
   writing a declaration. It says exactly what a declaration claims and
   what it cannot check.
6. **`docs/reviews/REVIEW-R15.md` §1c** — this round is R15's own
   suggested fix, written by the reviewer who found the gap. **Read it
   first-hand; do not take my summary of it.**
7. `docs/reviews/REVIEW-R16.md` — the round immediately before yours.

Hard rules:

- **NEVER print or commit a secret.**
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push, do not merge, and do not FIX.** Findings become
  tasks; Tier 0 rules on them.
- **Make your own worktree**, detached at the trunk tip:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r17 -b review/r17 origin/main`
- **`TaskGet` before acting on any assignment** and compare the text to
  this brief. A completion echo replays a SUPERSEDED description, is
  dated LATER than the correction it hides, and arrives with these
  guardrails stripped (#162). **Compare the text, never "check who
  sent it".**
- **Run CI's EXACT invocation, flags and all.** `uv run --frozen python`,
  never bare `python3`.
- **EVERY finding at EVERY severity, nits included, ships with a
  suggested fix.**
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **Report by `SendMessage` to `fastmcp-jobvite`** and write
  `docs/reviews/REVIEW-R17.md`.
- **Correct this brief where it is wrong.** Twelve of twelve agents have
  found an error in their brief and every correction held.

## §B — Your population, DERIVED not listed

Run `uv run --frozen python docs/reviews/check-review-coverage.py` and
work from what it reports. As I write, the backlog holds **57**: the
39 `PARTIAL` R15 predicted, plus commits pushed since.

**A `PARTIAL` COMMIT IS ONE A ROUND CLAIMED THE RANGE OF BUT NOT EVERY
FILE OF.** So your subject is specifically the files earlier rounds did
NOT claim. R15 declared `docs/reviews scripts .github`; R16 declared the
same three over a later range. **Re-declaring those buys nothing** —
that is the mistake my R16 brief made and R16 caught.

R15 §1c names the complement: `docs/briefs docs/adr docs/research src
tests` plus the root config files. **Read §1c for the exact list and its
reasoning rather than trusting that sentence** — I have already had one
brief's path list turn out to be the wrong one.

Two facts §1c records that will save you time:

- **`docs/briefs` cannot be shortcut into `RECORD_PATHS`.** The ruling at
  `check-review-coverage.py:123-130` refuses it by name, because a brief
  INSTRUCTS an agent and has carried substantive rulings. That ruling is
  correct and is not reopening.
- `scratch139/` and `sweep.log` are **already deleted at HEAD** — added
  and removed inside the uncovered span. They still demote their
  commits, and reading a deleted scratch file is cheap.

## §C — What to look for

Unlike R16, your population includes **`src/` and `tests/` — the product
itself** — and **`docs/adr/`**, which is authority rather than commentary.
So the priorities differ:

1. **AN ADR APPLIED BACKWARDS, PARTIALLY, OR NOT AT ALL.** Check each ADR
   in your range against the CODE, not against the commit that claims to
   apply it. This project has measured all three outcomes and they need
   three different remedies.
2. **A TEST WHOSE NAME IS A CLAIM ITS BODY DOES NOT EXERCISE.**
3. **A CONTROL THAT PASSES WITHOUT TESTING ITS SUBJECT.** Ask WHY an arm
   passes, not THAT it does. Three vacuous controls were found here in
   one evening, two of them in the fix for the task about vacuity.
4. **A COMMENT THAT ASSERTS A GATE THAT DOES NOT EXIST.** Measured twice
   this week, once in a file whose comment named the gate that would
   have caught it.
5. **A FIGURE RETYPED RATHER THAN DERIVED**, and any count without its
   container.

## §D — The declaration is half the deliverable

End `REVIEW-R17.md` with a `REVIEW-COVERS` line naming what you ACTUALLY
read. **A narrower true declaration is the correct outcome; a wide false
one is a defect worse than the gap** — I proved a fabricated declaration
clears the whole backlog at exit 0, so the checker cannot catch you and
the honesty has to be yours.

`REVIEW-R17.md` must itself carry a declaration or it lands in
`unexplained` and the checker returns 1.

R16 declared three paths where its brief's example showed four, because
it had not opened the fourth. **That is the behaviour I want, and it cost
it a commit in the count.** Do the same.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py

**THE BACKLOG EDIT IS UP TO THREE PARTS, NOT ONE** — R16 corrected my
last brief on exactly this. Deletions for what you covered, ADDITIONS for
anything newly outstanding, and KIND corrections where a commit moved
between `NONE` and `PARTIAL`. Doing only the deletions leaves the gate
red. Report before/after counts, each with its ref and sha.

**THE TRUNK WILL MOVE UNDER YOU.** It moved twice under R16 and made two
of its own measurements disagree. Pin your reading to one sha, say which,
and re-derive at the end.

## §F — Context you are owed

- `suborch-153` owns `.github/workflows/ci.yml` and
  `docs/reviews/check-checkers-are-wired.py`. `suborch-156` owns
  `scripts/check-u1-boot-amputation.sh`. **You are read-only over the
  whole tree except your report and the backlog file.**
- CI has never produced a green run on this trunk. The last known red
  step was closed tonight and the confirming run has not finished. **Do
  not add a new one.**
- Open findings you may re-encounter, so you do not re-file them: #165
  (the `EXIT$` trap anchor), #166 (five smaller R16 findings), #163 (a
  new tracked file is unscanned until tracked), #164 (nothing notices if
  the mirror stops running).
