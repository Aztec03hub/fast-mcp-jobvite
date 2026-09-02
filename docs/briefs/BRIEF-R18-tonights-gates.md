# BRIEF — R18: four gates I built tonight and nobody has reviewed

You are `review-r18`, a Tier-1 reviewer. **You are not fixing anything.**
You read, you measure, you report. Findings become tasks; Tier 0 rules
on them.

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN. Where a reviewed commit disagrees with
   it, the commit is wrong unless a numbered ADR says otherwise.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `CONTRIBUTING.md`
5. `docs/briefs/PROTOCOL-sub-orchestrators.md`
6. `docs/reviews/check-review-coverage.py` — read its DOCSTRING before
   writing your declaration. It says exactly what a declaration claims
   and what it cannot check.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push, do not merge, and do not FIX.**
- **Make your own worktree**, cut from the trunk tip:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r18 -b review/r18 origin/main`
  Note that one of your five commits (`9c08427`) is **LOCAL ONLY** and
  not on `origin/main`. Read it from the main checkout with
  `git show 9c08427`, or cherry-pick it into your worktree — but do not
  push it and do not merge it.
- **`TaskGet` before acting on any assignment** and compare the TEXT to
  this brief. Any `TaskUpdate` re-emits a task's ORIGINAL description as
  an assignment, dated LATER than the completion, `assignedBy` naming
  the completing agent. Measured four times (#162). **Compare the text,
  never "check who sent it".**
- **CI's EXACT invocations.** `uv run --frozen python`, never bare
  `python3`, where CI uses it. `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning` — and if a tool is missing, SAY
  SO rather than claiming the gate.
- **EVERY finding at EVERY severity, nits included, ships with a
  suggested fix.**
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **Report by `SendMessage` to `fastmcp-jobvite`** and write
  `docs/reviews/REVIEW-R18.md`.
- **Correct this brief where it is wrong.** Sixteen of sixteen agents
  have found an error in theirs, and the last four corrections each
  changed what got built.

## §B — Your population, and it is exactly five commits

    3987403  #163  warn on untracked secret-scan findings
    6f858ea  #164  scripts/check-mirror-liveness{,-controls}.py/sh
    fd300ec  #149  the wiring probe gets a job and a floor
    9c08427  #131  the shared gate records who is mutating  (LOCAL ONLY)
    e6333ef 39bfab8 a36883f e845839   backlog top-ups (records; skim)

All five were written by Tier 0 in one sitting, by hand, with no
reviewer at any point. That is the whole reason you exist. Read the
commit messages — they are long on purpose and they state what was
measured, what was refused, and what I got wrong; **treat every one of
those claims as a claim, not as evidence.**

## §C — What to look for, in priority order

1. **A CONTROL THAT PASSES WITHOUT TESTING ITS SUBJECT.** Ask WHY each
   arm passes, not THAT it does. `check-mirror-liveness-controls.sh`
   has 14 arms that ALL feed injected JSON; its own commit message
   admits none of them could see a live URL bug. Are there other
   classes those arms are structurally blind to, and does the file say
   so? Same question for `probe-131-gate-state.sh`'s nine assertions —
   two of them assert an ABSENCE, which is what you also get from code
   that never runs.
2. **A FLOOR THAT CARRIES SLACK.** Three new floors landed tonight:
   `ROW_FLOOR=14` in check-mirror-liveness-controls.sh, `floor = 14` in
   probe-wired-checker-amputation.py, `ROW_FLOOR=9` in
   probe-131-gate-state.sh. #91 found a floor carrying five rows of
   slack. Watch each one FIRE, do not read it.
3. **A GATE THAT CANNOT GO RED IN CI.** `check-mirror-liveness.py` is
   wired as a live API call needing `actions: read`. What happens on a
   fork, on a `pull_request` from a fork, or when the token lacks the
   scope? Exit 4 is a deliberate failure — is that right, or does it
   make CI red for something no commit contains?
4. **THE #131 CHANGE TOUCHES EVERY HARNESS.** `scripts/ci-harness-gate.sh`
   now writes a state file and both `git status` calls gained `-C
   "$REPO"`. That second change alters what the tree comparison
   measures for anyone invoking the gate from another directory.
   **Is there a caller for whom that is a behaviour change rather than
   a fix?** And: the state file is keyed by a `cksum` of the repo path,
   with `HARNESS_STATE_FILE` overriding — what happens when two
   worktrees of the same repo run harnesses at once?
5. **A CLAIM IN A COMMIT MESSAGE THAT THE CODE DOES NOT SUPPORT.**
   I wrote a lot of prose tonight. Check the numbers: 887 tests, 464
   anchors, 38 container members, 31 tallies, backlog 65.

## §D — The declaration is half the deliverable

End `REVIEW-R18.md` with a `REVIEW-COVERS` line naming what you
ACTUALLY read. **A narrower true declaration is the correct outcome; a
wide false one is a defect worse than the gap.** Since #168 landed, a
round covers a commit only if it claims at least one non-record file
that commit touches — so a declaration that reads nothing now clears
nothing.

`REVIEW-R18.md` must itself carry a declaration or it lands in
`unexplained` and the checker returns 1.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py

The backlog edit is up to three parts: deletions for what you covered,
ADDITIONS for anything newly outstanding, and KIND corrections. Report
before/after counts, each with its ref and sha.

## §F — Context you are owed

- **CI run 33582613697 (head 22c9873) is IN FLIGHT and has been for
  ~90 minutes.** DO NOT PUSH ANYTHING. GitHub cancels older QUEUED runs
  in a concurrency group regardless of `cancel-in-progress`, and one
  run is already queued behind it. This is the first run on this trunk
  ever to reach the deep harness steps.
- The trunk has NEVER had a green CI run. The last known red step was
  closed at 2d886a4 and this in-flight run is the confirmation.
- Open tasks you may re-encounter, so you do not re-file them: #154
  (timeout bounds, being measured from that run), #158 and #9 (Phil's),
  #160 and #106 (blocked), #162 (the board hazard).
