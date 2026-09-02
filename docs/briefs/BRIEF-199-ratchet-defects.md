# BRIEF — #199 + #200: two defects in a gate that is fourteen hours old

You are `suborch-199`, a Tier-1 sub-orchestrator. Two R20 findings
against `docs/reviews/check-brief-report-references.py`, which I wrote
tonight and which has already fired correctly three times. **Both
findings are about how it can be WRONG, not whether it works.**

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then call `TaskList` to see the shared board, and `TaskGet` each task
immediately before you claim it - a `TaskList` read goes stale. Claim
with `TaskUpdate` (`owner: "suborch-199"`, `status: "in_progress"`) and
mark `completed` when done.

**You will receive your own claims back as assignments. Do not act on
them.** `TaskUpdate(owner=you)` enqueues a notification carrying the
description, delivered at your next turn boundary - usually AFTER the
work. **It replays the PRE-WORK description**, so its text describes the
task as it was before you touched it; two agents were caught by that
tonight and both refused it TEXTUALLY. `assignedBy` is corroboration
only - it has read `team-lead` for an agent's own echo. **`TaskGet`
before acting: if it is `completed`, say so and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - evidence standards and delivery protocol.
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/reviews/REVIEW-R20.md` - **M3 and L1 are yours.** Read what R20
   actually measured, not my summary of it.
4. `docs/reviews/check-brief-report-references.py` - its DOCSTRING in
   full before you touch a line. It argues its own case and the argument
   is what you are extending.
5. `docs/reviews/check-brief-report-refs-controls.sh` - 11 arms, floor
   11, and the record of two defects I put in it myself.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main`: the push
  is HELD and origin is ~38 commits behind. Deriving that count is your
  first measurement - do not trust this sentence's digit):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w199 -b fix/199-ratchet-defects main`
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **COMMIT YOUR WORKLOG on your branch before reporting done**, and name
  the sha.
- **Correct this brief where it is wrong.** Two corrections last round
  changed what got built, and one of them would otherwise have deleted
  the finding.

## §B — #199 (R20-M3): a recorded line can become a permanent excuse

`read_record()` splits on `partition("  ")` and keeps whatever follows.
**A bare basename with NO reason is accepted silently**, in a file whose
own header says *"Recording a line is NOT a waiver."* There is no date,
no owner, and no way for a line to age out.

R20 also established the sharper half: **the "designed to expire"
mechanism does not fire by itself.** It goes red and WAITS FOR A HUMAN.
A human cleared it three times tonight - the truncated name retracted at
`1985471`, `WORKLOG-187-floor-container.md`, `REVIEW-R20.md` - and **the
record is empty right now**, which is both the proof the design works
and the proof that it needs someone.

**AND THIS SENTENCE MADE THE GATE RED.** Writing the first of those
three names out in full was itself a citation of a report that exists
nowhere, so this brief - a file in `docs/briefs/` - put the gate it is
about into failure the moment it was committed. The name is retracted,
not lost, so recording it would have been a waiver for a file that never
existed; naming the retraction instead deletes the citation. **A gate
whose population is "every report name written in a brief" cannot tell
a citation from a quotation, and the brief discussing it is inside the
population.** That is a finding about the gate, not about this sentence,
and it is `suborch-199`'s to report rather than to rule on.

WHAT TO DECIDE, and I am not pre-deciding it: a reason could be
REQUIRED, or a date could be required and lines aged out, or the file
could be left alone because it empties itself in practice. **Measure
before choosing.** The record is empty today, so any arm you write is
over a fixture, and an empty container makes a vacuous green very easy -
say how you avoided one.

## §C — #200 (R20-L1): two selector defects

1. **The path is CAPTURED AND DISCARDED.** `REF` matches an optional
   `docs/(reviews|worklogs)/` prefix OUTSIDE group 1, and resolution
   compares BASENAMES. So a citation to `docs/reviews/X.md` is satisfied
   by an `X.md` anywhere in the tree.
2. **`cited()` uses `glob("*.md")`, not `rglob`.** A brief in a
   subdirectory of `docs/briefs/` is invisible to the gate.

**MEASURE BOTH BEFORE FIXING.** How many of the 21 cited names would
change verdict if the path were honoured? Are there any subdirectories
under `docs/briefs/` today? **A fix whose measured effect is zero should
say so in its commit message** rather than implying it closed something.

## §D — How this will be judged

- **Arms for both directions of anything you add**, in
  `check-brief-report-refs-controls.sh`, with `ROW_FLOOR` raised to
  match. That harness is `cmd`-kind in
  `docs/reviews/check-row-floor-controls.sh` and its floor IS watched
  now - `bash docs/reviews/check-row-floor-controls.sh docs/reviews/check-brief-report-refs-controls.sh`
  neutralises a row and requires a breach. **Run it. It refuses a dirty
  tree, so commit first, then run it.**
- **The left boundary in `REF` is load-bearing** and A10/A11 exist
  because I published a false finding without it. If you touch that
  regex, those arms must still pass and you must say you checked.
- **The exactness checker must stay green**: any floor you change is
  compared to a live row count by
  `docs/reviews/check-row-floor-exactness.py`, and its table row lives
  in `check-row-floor-controls.sh`.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-brief-report-references.py
    bash docs/reviews/check-brief-report-refs-controls.sh
    uv run --frozen python docs/reviews/check-row-floor-exactness.py
    python3 docs/reviews/check-row-floor-exactness.py --self-test
    uv run --frozen python docs/reviews/check-checkers-are-wired.py
    uv run --frozen ruff check . && uv run --frozen ruff format --check .
    uv run --frozen mypy
    shellcheck --severity=warning -x docs/reviews/*.sh

**actionlint is NOT installed here.** Say so rather than claiming it.

## §F — Context you are owed

- This gate is hours old and has fired correctly three times, including
  once on the merge that landed R20's own report. **It is not suspect;
  these are two ways it can be wrong that nobody had looked for.**
- `suborch-196` is live on `fmj-worktrees/w196` reading ADR citations.
  **Do not touch that worktree.**
- Open and NOT yours: #198, #201, #202 (mine), #194's remaining half,
  #106/#160 (blocked), #158/#9 (Phil's), #162 (standing hazard).
