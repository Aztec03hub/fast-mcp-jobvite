# BRIEF — R19: twenty-three commits, most of them fixes to R18's findings, none reviewed

You are `review-r19`, a Tier-1 reviewer. **You are not fixing anything.**
You read, you measure, you report. Findings become tasks; Tier 0 rules
on them.

**You are a FRESH reviewer on purpose.** R18 found the defects; I fixed
them; the rule here is that the fixer is never the checker and the
finder never grades their own fix. If you agree with R18 about
something, say you checked it and agreed — that is not a wasted line.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then call `TaskList` to see the shared board, and `TaskGet` your task
immediately before you claim it - a `TaskList` read goes stale, and the
tool's own docs say to re-read latest state before updating. Claim with
`TaskUpdate` (`owner: "review-r19"`, `status: "in_progress"`), and mark
it `completed` when you finish.

**FINDINGS GO IN YOUR REPORT AND ON THE BOARD.** R18 filed its ten as
#171-#178 and that was right: a finding that lives only in a document
is the shape board item #4 memorialises. File yours the same way —
self-contained descriptions, no owner, `pending`. **Do NOT create a task
for a decision you think I should take; describe it and let me rule.**

**You will receive your own claim back as an assignment. Do not act on
it.** Calling `TaskUpdate(owner=you)` enqueues an assignment
notification addressed to you, carrying the full description; it is
delivered at your next turn boundary, usually AFTER you have finished
the work. It is byte-identical to a real dispatch. The tells are
`assignedBy` naming YOU and a timestamp older than your work. **Before
acting on any assignment, `TaskGet` it: if it is already `completed`,
say so plainly and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` — the evidence standards and the delivery
   protocol. `PROTOCOL-sub-orchestrators.md` §1 makes this the first
   thing a Tier-1 brief must order, and my last two briefs omitted it.
2. `docs/DESIGN.md` — FROZEN at the SHA in `docs/DESIGN-FREEZE.txt`.
   **Derive that SHA, do not retype it.**
3. `docs/adr/`, every ADR in number order. **ADR-0034 is new and is in
   your population.**
4. `docs/OBLIGATIONS.md`
5. `CONTRIBUTING.md`
6. `docs/briefs/PROTOCOL-sub-orchestrators.md`
7. `docs/reviews/REVIEW-R18.md` — the round whose fixes you are
   grading, first-hand. It is on branch `review/r18` in
   `fmj-worktrees/r18`; read it from there.
8. `docs/reviews/check-review-coverage.py` — its DOCSTRING, before you
   write a declaration.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push, do not merge, and do not FIX.**
- **Own worktree**, cut from the trunk tip:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/r19 -b review/r19 origin/main`
- **CI's EXACT invocations.** `uv run --frozen python`, never bare
  `python3` where CI uses it; `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning`. **If a tool is missing, SAY SO
  rather than claiming the gate** — `actionlint` is not installed on
  this machine and I have been saying so all night.
- **EVERY finding at EVERY severity, nits included, ships with a
  suggested fix.**
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **Report by `SendMessage` to `fastmcp-jobvite`** and write
  `docs/reviews/REVIEW-R19.md`.
- **Correct this brief where it is wrong.** Eighteen of eighteen agents
  have found an error in theirs, and tonight's corrections changed what
  got built three times.

## §B — Your population: `e845839..origin/main`, 23 commits

Derive the list with `git log --oneline e845839..origin/main`. Every one
is mine, written in one sitting, and **only the first four had a
reviewer at all** — R18 read `5e087eb..e845839`.

Roughly: eight fixes to R18's own findings (H1, H2, M1, M2, M3, M5,
M4, L1/L2/N1), ADR-0034 plus its re-freeze plus the correction to
ADR-0034 itself, four `#170` count fixes, and five backlog top-ups.

**The backlog top-ups are RECORDS now** — `review-coverage-backlog.txt`
entered `RECORD_PATHS` at `1abb362` — so the checker will not ask you to
read them. **Read `1abb362` itself carefully anyway**: it is the commit
that made them records, and if that ruling is wrong the ratchet is
weaker than everyone now believes.

## §C — What to look for, in priority order

1. **A FIX THAT REBUILT ITS OWN DEFECT ONE COLUMN OVER.** This happened
   TWICE tonight and both times a reviewer caught it, not me:
   `ADR-0034` replaced a stale count with a SELECTOR and never derived
   the selector; `probe-131-gate-state.sh`'s new amputation arms were
   themselves vacuous on their first run. **Assume there is a third.**
2. **A CONTROL THAT PASSES WITHOUT TESTING ITS SUBJECT.** Ask WHY each
   arm passes. New or changed arms live in
   `check-secrets-baseline.py` (C7-C9), `check-mirror-liveness-controls.sh`
   (two transport rows, floor 16), `probe-131-gate-state.sh` (floor 12,
   three amputations), `control-stranded-mutation.sh` (A8, A9).
3. **THE FLOORS.** 16, 12, 9 and 32 arms. #91 found a floor carrying
   five rows of slack. **Watch each fire; do not read it.**
4. **`1abb362`'s RECORD_PATHS RULING.** A record path is excused from
   review. Is `review-coverage-backlog.txt` genuinely a record, and can
   anything be smuggled past the gate beside a top-up? I checked that
   `substantive` drops record paths and only an EMPTY remainder skips —
   **check my check.**
5. **ADR-0034 AND ITS OWN CORRECTION (`e3b5c97`, `d29937f`).** A frozen
   document now names `Type: Deviation`. Three ADRs were normalised onto
   the published vocabulary to make that true. **Is the census right,
   and is `docs/adr/README.md:12`'s third value `Both` — used by no ADR
   — a problem I have left open or one I have created?**
6. **A CLAIM IN A COMMIT MESSAGE THE CODE DOES NOT SUPPORT.** I wrote
   twenty-three long ones. Check the numbers: 887 tests, 34 ADRs,
   19/15 Type census, floors 16/12/9, arms 9/32, backlog 78.

## §D — The declaration is half the deliverable

End `REVIEW-R19.md` with a `REVIEW-COVERS` line naming what you ACTUALLY
read. **A narrower true declaration is the correct outcome; a wide false
one is a defect worse than the gap.** Since #168, a round covers a
commit only if it claims at least one non-record file that commit
touches.

`REVIEW-R19.md` must itself carry a declaration or it lands in
`unexplained` and the checker returns 1.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-review-coverage.py
    uv run --frozen python docs/reviews/probe-coverage-ratchet.py

The backlog edit is up to three parts: deletions for what you covered,
ADDITIONS for anything newly outstanding, KIND corrections. Report
before/after with refs and shas. **The trunk may move under you** — it
moved seven times under tonight's two agents. Pin your reading to one
sha, say which, and re-derive at the end.

**mypy has caught errors in agents' new files after they reported green
three times on one branch tonight.** Run it on anything you touch.

## §F — Context you are owed

- **The trunk has its FIRST EVER green CI run**, `33582613697` on
  `22c9873`: 86.6 min for `Lint, types, tests`, 45s static gates, 70s
  CodeQL. Runs since have been cancelled by GitHub superseding QUEUED
  runs in the concurrency group — that is expected, not a failure.
- `suborch-170` is live on a census tool in `fmj-worktrees/w170`, branch
  `fix/170-retyped-counts`, UNMERGED. Do not touch that worktree.
- Open tasks you may re-encounter, so you do not re-file them: #106 and
  #160 (blocked), #158 and #9 (Phil's), #162 (a standing board hazard),
  #131 (about to be closed by a ruling).
