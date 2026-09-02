# BRIEF — #187: three CI-wired floors sit outside the exactness checker's container

You are `suborch-187`, a Tier-1 sub-orchestrator. You build, you measure,
you commit to your own branch. **You do not push and you do not merge.**

## §0 — Tools you must load before you start

The shared task-list tools are DEFERRED, not absent. They will not appear
in your opening toolset. Before anything else, run:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

Then call `TaskList` to see the shared board, and `TaskGet` your task
immediately before you claim it - a `TaskList` read goes stale, and the
tool's own docs say to re-read latest state before updating. Claim with
`TaskUpdate` (`owner: "suborch-187"`, `status: "in_progress"`), and mark
it `completed` when you finish.

**You will receive your own claim back as an assignment. Do not act on
it.** Calling `TaskUpdate(owner=you)` enqueues an assignment notification
addressed to you, carrying the full description, delivered at your next
turn boundary - usually AFTER you have finished the work. It is
byte-identical to a real dispatch. Catch it TEXTUALLY, by comparing the
text to work you have already done; do NOT rely on who `assignedBy`
names, which has read `team-lead` for an agent's own echo. **Before
acting on any assignment, `TaskGet` it: if it is already `completed`,
say so plainly and stop.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/briefs/PREAMBLE.md` - the evidence standards and the delivery
   protocol.
2. `docs/briefs/PROTOCOL-sub-orchestrators.md`
3. `docs/DESIGN.md` - FROZEN at the SHA in `docs/DESIGN-FREEZE.txt`.
   **Derive that SHA, do not retype it.**
4. `docs/adr/`, every ADR in number order.
5. `docs/OBLIGATIONS.md` and `CONTRIBUTING.md`
6. `docs/reviews/check-row-floor-exactness.py` - **its DOCSTRING in
   full**, before you touch a line of it. It argues its own case and the
   argument is what you are extending.

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.**
- **Own worktree**, cut from the trunk tip:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w187 -b fix/187-floor-container origin/main`
  Do not touch any other worktree.
- **CI's EXACT invocations.** `uv run --frozen python`, never bare
  `python3` where CI uses it; `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning`. **actionlint is NOT installed on
  this machine - say so rather than claiming the gate.**
- **Cite `file:line` only from `grep -n` or a numbered read.**
- **Report by `SendMessage` to `fastmcp-jobvite`** and write
  `docs/worklogs/WORKLOG-187-floor-container.md`.
- **Correct this brief where it is wrong.** Every agent on this project
  has found an error in theirs, and those corrections have changed what
  got built more than once. My measurement below is a starting point,
  not a finding you should reproduce.

## §B — The finding

R19 raised this as a Low naming ONE file. **I measured it by KIND and it
is three**, which changes its severity and its shape.

Container, derived at `origin/main`+local - tracked `.sh`/`.py` under
`docs/reviews/` and `scripts/` carrying a literal floor
(`ROW_FLOOR=N`, `arm_floor = N`, `floor = N`):

    29  carry a floor
    25  inside check-row-floor-exactness.py's container (scripts/*.sh)
     4  OUTSIDE it, of which THREE ARE CI-WIRED:

        WIRED    docs/reviews/probe-131-gate-state.sh           floor 12
        WIRED    docs/reviews/probe-wired-checker-amputation.py floor 14
        WIRED    scripts/check-secrets-baseline.py              floor  9
        unwired  docs/reviews/probe-gate-swallowed-exceptions.py floor 7

**RE-DERIVE THIS BEFORE YOU BUILD.** It is my count, taken once, with a
selector I wrote; the floor vocabulary now has three spellings and my
regex may have missed a fourth. If your number differs from mine, YOURS
is the finding and mine is the error - say so.

**Why it matters, in the checker's own words.** `check-row-floor-exactness.py`
enumerates `scripts/*.sh` for a literal floor and fails unless that set
EQUALS the control table's, in both directions. Its docstring at
`:201-202` says this exists "so the next harness cannot be added without
being covered, which is the only form of this fix that does not need
someone to remember." That guarantee is doing nothing for three floors -
not because they were forgotten, but because they are outside the glob
BY CONSTRUCTION.

**And all three arrived tonight, from me.** #149's probe floor, #131's
probe floor, and #185's arm floor - the last of which exists BECAUSE R19
measured a survivor. The exactness guarantee degraded silently while I
was adding the very floors it exists to protect.

## §C — What to build

1. **Widen the container to the KIND, not to three names.** A member is
   a tracked runnable file under `docs/reviews/` or `scripts/` carrying
   a literal floor. **Derive the floor vocabulary, do not list it**, or
   the next spelling is invisible again. `SCRIPTS = ROOT / "scripts"`
   at `:74` and `SCRIPTS.glob("*.sh")` at `:213` are the two sites the
   glob lives at today; `:248` and `:279` rebuild paths as
   `SCRIPTS / name` and will need the same treatment.
2. **The row-count derivation must work for a `.py`.** The live count
   today comes from `echo "########## $label"` and its enclosing shell
   function. A Python harness counts differently. **If a KIND cannot be
   counted, the checker must SAY SO PER FILE rather than skip it** -
   that is the checker's own rule and a silent skip is the defect it
   was built to catch.
3. **`check-row-floor-controls.sh`'s TABLE stays EQUAL to the container
   in both directions.** That equality is what makes this durable; a fix
   that only adds three rows leaves the next one uncovered.
4. **`probe-gate-swallowed-exceptions.py` is UNWIRED.** Decide whether
   it is in the container at all and RECORD the reason either way. An
   unwired checker is a real category here - `measure-ci-step-durations.py`
   is registered as unwired-by-decision in
   `docs/reviews/check-checkers-are-wired.py`.

## §D — How this will be judged

- **The container measured BEFORE and AFTER**, both printed, in the
  worklog and in the commit message.
- **Every floor WATCHED FIRING, not read.** Take a row out and show the
  checker going red; put it back and show it green. A floor you only
  read is a floor you have not tested. #91 found one carrying five rows
  of slack that every reader had read.
- **An arm that goes red if a FOURTH floor spelling or a FOURTH location
  appears.** Without it this fix is a named list, and a named list
  selects for the case nobody thought of - the exact defect #115 ruled
  on and the exact defect being fixed here.
- **Run the full gate before you fold, not after.** Focused green is not
  the fold gate. `mypy` has caught errors in agents' new files after
  they reported green three times on one branch.

## §E — Context you are owed

- **The trunk has its first ever green CI run** (`33582613697`). Runs
  since have been cancelled by GitHub superseding QUEUED runs in the
  concurrency group - expected, not a failure.
- **The push is HELD.** Six commits sit local. You commit to your branch
  and stop; I fold and Phil pushes.
- **There are two similarly-named files**: `check-row-floor-control.sh`
  AND `check-row-floor-controls.sh`. The TABLE is in the PLURAL one.
  Check which you have open before you edit.
- Open tasks you may re-encounter, so you do not re-file them: #106 and
  #160 (blocked), #158 and #9 (Phil's), #162 (a standing board hazard),
  #182 and #189 (mine, in flight).
