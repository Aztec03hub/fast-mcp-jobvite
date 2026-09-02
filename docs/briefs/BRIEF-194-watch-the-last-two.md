# BRIEF — #194: the last two floors nobody has watched, and they need DIFFERENT mechanisms

You are `suborch-194`, a Tier-1 sub-orchestrator. Two floors are checked
for EXACTNESS and have never been watched FIRE. **They are unwatched for
two different reasons and each needs its own mechanism.** Both are ruled;
you are building, not deciding.

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. Before anything
else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then `TaskList`, and `TaskGet` #194 immediately before claiming it - a
`TaskList` read goes stale. Claim with `TaskUpdate`
(`owner: "suborch-194"`, `status: "in_progress"`), mark `completed` when
done.

**You will receive your own claim back as an assignment. DO NOT ACT ON
IT.** It replays the PRE-WORK description, so its text is a description
of the QUESTION, not the answer - and agents have been caught by exactly
that, one of them nearly re-editing a register against a premise its own
round had refuted. Catch it TEXTUALLY by comparing against work already
done. `assignedBy` is corroboration only; it has read `team-lead` for an
agent's own echo. **`TaskGet` first: if `completed`, say so and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md`
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/reviews/check-row-floor-exactness.py` - its DOCSTRING, and its
   `--self-test`, which is the SHAPE you are copying for part 2.
4. `docs/reviews/check-row-floor-controls.sh` - the control you are
   extending for part 1. Read its `mode=static` refusal: it now states
   each member's ACTUAL reason, and those two sentences are your spec.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from LOCAL `main` (NOT `origin/main`, which is
  far behind - **derive the gap; a brief's count has gone stale between
  writing and reading four times**):
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w194 -b fix/194-watch-last-two main`
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **DERIVE EVERY ANCHOR FROM THE FILE.** A suggested `sed` is a claim
  about code: one in an earlier round named a variable that had been
  renamed and would have matched nothing.
- **COMMIT YOUR WORKLOG before reporting done** and name the sha. Write
  it at `docs/worklogs/WORKLOG-194-watch-last-two.md`; that path is
  already recorded as IN FLIGHT and the gate will demand the record line
  be deleted once the file lands. **Do NOT write any OTHER report's
  basename in prose** - the brief-report gate reads that as a citation
  and has gone red on three agents' briefs.
- **Correct this brief where it is wrong.** Every agent has.

## §B — Part 1: `probe-131-gate-state.sh` — a COMPUTED count IS watchable

The floor control refuses it because its row count is COMPUTED at run
time, so the control has no static count to predict and cannot say what
a deletion should produce.

**THAT IS A LIMIT OF THE CURRENT MODE, NOT OF THE HARNESS.** You do not
need to predict the count. **Read it.**

    run it once            -> rows=N floor=N status=ok
    delete ONE row         -> require rows=N-1 AND status=breach AND rc=1
    restore                -> byte-identical to the backup AND to the index

Build that as a mode in `check-row-floor-controls.sh` - the `COMPUTED`
token is already in the table's ERE column, so the dispatch point
exists. **The restore assertion is not optional**: this control mutates
a tracked file, and a killed harness that leaves a mutation behind is a
defect this project has measured four times.

## §C — Part 2: `probe-wired-checker-amputation.py` — its own `--self-test`

A bash control cannot drive a Python harness; an arm there would measure
the interpreter. **The shape already exists and already runs in CI:**
`check-row-floor-exactness.py --self-test`, wired at `ci.yml`, floor 16,
16/16.

Copy that shape. The self-test must:

- delete one arm from an in-memory or scratch copy and require the floor
  to breach;
- carry its OWN `arm_floor`, which puts it in
  `check-row-floor-exactness.py`'s container and therefore requires a
  control-table row like every other member. **That is deliberate - the
  checker checking itself is how #187 closed the same gap.**

## §D — How this will be judged

- **BOTH floors WATCHED FIRING**, red then green, with the tree restored
  byte-identical. A floor you only read is a floor you have not tested.
- **`fired=N/N` IN A BREACH IS THE TRAP.** When a row is deleted every
  SURVIVING row still fires, so a fired-count check passes a harness that
  has lost a row. **Only the floor catches it.** Say which assertion
  caught what.
- **ISOLATE EACH ARM TO ONE BRANCH.** Three arms in a sibling harness
  were confounded - each red for a branch it did not name. If an arm can
  go red two ways, it proves neither.
- **Run the full gate BEFORE folding**, each exit code on its own line.
  Never `cmd >/dev/null && echo OK`: under `set -e` only the LAST command
  of an AND-list triggers errexit, and that hid a real red twice.

## §E — Verify before you finish

    uv run --frozen python docs/reviews/check-row-floor-exactness.py
    python3 docs/reviews/check-row-floor-exactness.py --self-test
    uv run --frozen python docs/reviews/check-checkers-are-wired.py
    bash docs/reviews/check-row-floor-controls.sh --list
    uv run --frozen ruff check . ; uv run --frozen ruff format --check .
    uv run --frozen mypy ; shellcheck --severity=warning -x docs/reviews/*.sh

The floor control **refuses a dirty tree at exit 3** - that is correct
and protects other agents. Commit first, THEN run it.

**actionlint is NOT installed here.** Say so rather than claiming it.

## §F — Context you are owed

- `review-r21` is live in `fmj-worktrees/r21`. **Do not touch it.**
- **The push is HELD** and only Phil pushes.
- Open and NOT yours: #207, #208 (citation work), #106/#160 (blocked),
  #158/#9 (Phil's), #162 (standing hazard).
