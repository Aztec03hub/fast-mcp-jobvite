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
- **`docs/DESIGN.md` is FROZEN.** Read it as `git show <SHA>:docs/DESIGN.md`, never from the working
  tree. Only a numbered ADR may change it, and a defect you find in it is a **Proposed** ADR plus a
  report - not an edit.
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

**The suite baseline is NOT written here, on purpose.** Derive it:

```bash
grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
uv run --frozen pytest        # must be >= that floor, with 0 skipped
```

**This line used to name a number, and the number went stale across three
ratchets** - 322 while main was at 355, then 360, then 398. Two separate agents
caught it independently and both proposed the same fix. The file that exists
because *"a retyped constant decays"* had a decayed constant in it, which is the
most direct demonstration of its own thesis it could have produced.

The floor in `ci.yml` is the one place that value lives, it is enforced on every
run, and lowering it is a visible diff that has to be defended. Anything else is
a second copy.

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
