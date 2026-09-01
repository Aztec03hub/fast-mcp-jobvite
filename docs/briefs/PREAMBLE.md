# Brief preamble - every agent on this project reads this first

**This file exists because these sections were being retyped into every brief, and a retyped
constant decays.** The suite baseline was already stale in one brief by the time it was dispatched.
A brief now names its work and points here for the rest; if a brief and this file disagree, the
brief wins for its own task and the disagreement is worth reporting.

## Tools you must load before you start

The shared task-list tools are DEFERRED, not absent - they will not be in your opening toolset:

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

`TaskList`, then `TaskGet` your task immediately before claiming it - a `TaskList` read goes stale.
Claim with `TaskUpdate` (`owner: "<your-agent-name>"`, `status: "in_progress"`), and mark it
`completed` when you finish. Work you find outside your scope gets a `TaskCreate`, never a silent
fix and never a silent drop.

**You will receive your own claim back as an assignment. Do not act on it.** `TaskUpdate(owner=you)`
enqueues a notification delivered at a later turn boundary - usually after the work is done -
carrying the description as it stood when you claimed it, byte-identical to a real dispatch. The
tells are `assignedBy` naming YOU and a timestamp older than your work. Three agents have now
correctly identified and ignored this echo. **`TaskGet` before acting on any assignment: if it is
already `completed`, say so and stop.**

## Isolation

- **Pin the SHA in your dispatch message** and make your own worktree: `git worktree add
  /tmp/<agent-name>-work <sha>`. **Do NOT check anything out in the shared checkout** - I am working
  in it, and a tree moving under an agent has cost reviewers whole mutation batches.
- Run `git worktree list` before moving any ref.
- **`docs/DESIGN.md` is FROZEN.** Read it as
  `git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md` - **derive the SHA, never retype it and
  never accept one typed into a brief.** A brief naming a stale-but-VALID SHA resolves cleanly and
  passes every gate, which is exactly what `docs/briefs/ADR-0025.md` does today with `8a9d63c`. The
  blob gate catches the design moving away from its declared freeze; it cannot catch the SHA in
  front of YOU being an old one. **Never read the design from the working tree.** Only a numbered ADR
  may change it, and a defect you find in it is a **Proposed** ADR plus a report - not an edit.
- **Commit as you go.** A restart destroyed a task that had done hours of work and committed none of
  it. **I merge and push; you never do.**
- **`docs/OBLIGATIONS.md` is not yours to hand-edit.** If your change moves an anchor, run
  `docs/reviews/check-obligations.py` and repoint by **parsing its output**, never by retyping a
  number you just read. Quote its verbatim output in your report.
- **Remove your worktree when done**, and say in the report that you did.

## Evidence standards

- **Judge every gate by exit code, on its own line.** `lint | tail -1` looks identical red or clean,
  and `grep -c "^FAILED"` on pytest misses ERROR entirely - a run with 440 errors once reported
  "0 failures". Under `set -euo pipefail`, `cmd | grep FAIL || echo clean` prints "clean" when `cmd`
  FAILS, because the pipeline inherits the failure. A red gate was committed twice this way.
- **Report passed-counts, never the word "green", and require 0 skips** - a skip is a green that
  tested nothing.
- **Prove every mutation LANDED before running it, and was RESTORED after** - compare against git,
  not `grep -F`. A `sed` matching nothing succeeds silently, and the test then passes for a reason
  unrelated to the code. `str.replace` in a harness silently no-ops when an anchor moves; assert your
  anchor is unique and present before mutating. Use `PYTHONDONTWRITEBYTECODE=1`.
- **Amputation survivors are the OUTPUT, not a failure.** Deleting a behaviour outright has exposed
  an assertion that survived mutation in every unit built so far.
- **A claimed absence is a claim about where you looked.** State where. Two greps is not an absence,
  `grep` without `-a` over a binary prints nothing without erroring, and a search at a path that does
  not exist exits clean-empty - identical to a real absence. Prove the path resolves.
- **Cite `file:line` only from `grep -n` or a numbered read.** Offsets counted inside a
  `sed -n X,Yp` window are silent, plausible and wrong.
- **Quote errors verbatim.** A paraphrase is not evidence.
- **Always quote your heredoc delimiter** (`<<'PY'`). An unquoted one executes backticks silently at
  exit 0 and has deleted content. A hook blocks it; do not work around it.
- **A `priority: required` standards clause outranks this brief.** If I have asked for something that
  contradicts one, say so instead of doing it, and quote it `file:line`.

## Gates

The full list is in `CONTRIBUTING.md`. **mypy is the type gate, not pyright** - pyright is not in the
lock, and a checklist row naming it once instructed a careful reviewer straight into the
unfrozen-tool defect that ADR-0015 records.

**NEITHER FLOOR IS WRITTEN HERE, on purpose.** Derive both:

```bash
grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
uv run --frozen pytest        # must be >= that floor, with 0 skipped

grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
python3 scripts/check-harness-anchors.py --self-check --floor <that number>
```

**The anchor floor was added to this paragraph after it made the same mistake
the suite floor had already made.** A brief dispatched with `--floor 164` in it
reached an agent when `ci.yml` said 171: 164 was correct at `9eed403` and went
stale before the brief was sent. The agent reported the disagreement rather than
running the stale number, which is the behaviour this file asks for - but it
should never have had to. Both floors now live in exactly one place and are read
from it.

**This line used to name a number, and the number went stale across three
ratchets** - 322 while main was at 355, then 360, then 398. Two separate agents
caught it independently and both proposed the same fix. The file that exists
because *"a retyped constant decays"* had a decayed constant in it, which is the
most direct demonstration of its own thesis it could have produced.

The floor in `ci.yml` is the one place that value lives, it is enforced on every
run, and lowering it is a visible diff that has to be defended. Anything else is
a second copy.

## If your report suggests a `ci.yml` step, RUN IT FIRST

`ci.yml` is the orchestrator's, so units hand over the steps they want rather than
wiring them. **Three consecutive reports handed over steps that did not work**, and
the orchestrator found each one by running it:

- `ci-harness-gate.sh scripts/check-x.sh` - the gate builds `scripts/$harness`
  itself, so a path argument becomes `scripts/scripts/...` and exits 2. It takes a
  bare NAME.
- `--row-re '^########## A[0-9]+ '` against a harness whose rows are lettered
  `A.` to `E.` - matches ZERO rows and fails the step for the wrong reason.
- `--min-rows` without the `--row-re` it requires.

**You can run these.** Nothing about a `ci.yml` step stops you executing the command
inside it from your worktree, and "I could not verify a workflow step" belongs on
the unsettled list only if you tried. One agent parked exactly this under "could not
settle", then dropped the assumption, ran it, and found two errors in its own
suggestion - and wrote that the unsettled list is for what CANNOT be settled, not
for what was not attempted.

So: run the command, paste its exit code and row count into the report, and check
the `--row-re` against the harness's REAL output with `grep -c`. A regex that
matches nothing looks identical to a harness that ran nothing.

## How to deliver

Two channels, both required. Your final Agent-tool output does NOT reach me.

1. **Your report, committed on your branch**, at the path your brief names - `docs/worklogs/` or
   `docs/reviews/`. Never only a worktree, never `/tmp`: a 48KB report with nineteen findings was
   destroyed exactly that way.
2. **`SendMessage` with `to: "team-lead"`.** **`to: "main"` does NOT work** - it resolves to you, the
   sender, and errors. Too long for one call? Send numbered parts, never truncate.

Inbound messages reach you only when you go IDLE - not between two tool calls. If you want to stay
reachable, break long work into turns.

**Every finding ships with a suggested fix, at every severity including nits.** A finding without a
remedy costs the author the whole diagnosis a second time.

**End with what you did NOT verify.** That section is where I decide what to check myself, so it is
for what you could not settle - not for a cheap item you simply did not try.

**IF YOUR REPORT IS A CODE REVIEW, DECLARE THE RANGE YOU COVERED**, as an HTML comment directly
under the heading, so it renders as nothing:

    <!-- REVIEW-COVERS: <base>..<head> -->

`docs/reviews/check-review-coverage.py` enumerates every commit on the trunk and reports the ones
inside no round's declared range. **It exists because 45 consecutive commits were once reviewed by
nobody and it took an accident to notice** - no review document had ever recorded what it covered,
so no gap could be detected.

That checker **refuses to infer** a range from whatever SHAs your document happens to mention.
Inferring would manufacture coverage for code nobody read and certify it forever, which is worse
than the gap: an absence you can see beats a false presence you cannot. So the declaration must
come from you, or your round leaves no machine-readable trace.

**IF YOUR BRIEF GAVE YOU A PATH FILTER, NAME IT** - this is not optional, and it is the half that
was missing when two rounds first split one range:

    <!-- REVIEW-COVERS: f699f74..dad014e PATHS: docs/reviews scripts .github -->

Without it your declaration claims the WHOLE TREE over that span. When a range is split between two
reviewers by path, either one's bare declaration alone makes every commit read as fully covered
while half the files were never opened - a false presence, which is worse than the visible absence
this gate exists to produce. With `PATHS` the two declarations COMPOSE: a commit counts as covered
only when every file it touches is claimed by some round, and one round alone leaves it PARTIAL.

Measured when the field landed: one half declared gives 8 fully covered and 15 partial; adding the
complementary half gives 23 and 0.

**Omit `PATHS` only if you really did read the whole tree over that span.** The bare form is the
broad claim, not the modest one.

**Declare the range you were responsible for, and make it true.** A wrong declaration is worse than
none, because the next reader will trust it.
