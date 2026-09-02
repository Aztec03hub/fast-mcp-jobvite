# BRIEF — #153 + #155 + #149: one checker, blind in three directions

You are `suborch-153`, a Tier-1 sub-orchestrator. Three open tasks are
three rows of one column, and fixing them separately would touch the
same file three times.

## §A — Standing rules (read FIRST, in this order)

Read IN FULL before any edit. Where a numbered ADR conflicts with a
standard, the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN, you may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md` — your operating protocol.
5. `CONTRIBUTING.md`
6. `docs/reviews/check-checkers-are-wired.py` — your subject. Read its
   docstring, especially :41-45, before you change one line of it.

Hard rules:

- **NEVER print or commit a secret.**
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push and you do not merge.** Commit on your branch in
  your own worktree; Tier 0 merges.
- **Make your own worktree**, cut from `origin/main` at `2d886a4` or
  later: `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w153 -b fix/153-wiring-container`
- **`TaskGet` before acting on any assignment**, and compare the text to
  this brief. A completion echo replays a SUPERSEDED description, is
  dated LATER than the correction it hides, and arrives with these
  guardrails stripped. Seven agents have had to catch that; #162 records
  it. **Never "check who sent it" — compare the text.**
- **Run CI's EXACT invocation, flags and all.** `uv run --frozen python`,
  never bare `python3`; `actionlint` needs
  `SHELLCHECK_OPTS=--severity=warning`. I have misread a gate four times
  in one evening by dropping a flag, once while merging the task about
  exactly that.
- **Report by `SendMessage` to `fastmcp-jobvite`** and write findings to
  a `.md` under `docs/reviews/`.
- **Correct this brief where it is wrong.** Eleven of eleven agents have
  found an error in their brief and every correction held.

## §B — Files you OWN this run

    docs/reviews/check-checkers-are-wired.py
    docs/reviews/probe-wired-checker-amputation.py
    .github/workflows/ci.yml
    docs/reviews/<your report>

`suborch-156` owns `scripts/check-u1-boot-amputation.sh`. `review-r16`
owns `docs/reviews/review-coverage-backlog.txt` and writes
`docs/reviews/REVIEW-R16.md`. Touch none of those three.

**You own `ci.yml` — you are the only agent in it.** That is why this
work is possible now; #161 vacated it an hour ago.

## §C — The defect, in three directions

`check-checkers-are-wired.py:129-130` enumerates its container as:

    "docs/reviews/check-*.py",
    "docs/reviews/check-*.sh",

**That is two filters wearing a container's name.** It then prints
*"Every checker is wired, or unwired for a recorded reason."*

**#155 — BLIND BY PREFIX.** Measured at `ccbdaae` by asking which
basenames appear anywhere under `.github/workflows/`:

    docs/reviews/check-*   tracked   28   (its own count agrees)
    docs/reviews/probe-*   tracked   28
    probes NAMED in a workflow           4
    probes named NOWHERE                24

Four probes ARE wired, so probes are not categorically unwirable. The
sharpest instance: **`probe-ci-checker-steps.py` is in no workflow** —
the probe whose stated purpose is to run CI's checker steps verbatim
*so that a local green means what a CI green means*. Neither is its
control.

**#153 — BLIND BY PATH.** `scripts/` is excluded. The docstring states
that exclusion AND its reason, so it was ruled, not overlooked — but
`scripts/check-secrets-baseline.py` landed there this evening precisely
because a pre-commit-only checker appears in no `run:` body, and it is
invisible to this gate as a result. Re-examine whether the original
reason still holds now that `scripts/` holds two real gates.

**#149 — ONE ROW OF THE SAME COLUMN.** The wired-checker self-test and
its four amputations are neither wired nor a harness: 26 controls that
only ever run by hand. `probe-wired-checker-amputation.py` is one of
the 24.

## §D — What to build

**Enumerate the CONTAINER and assert set equality.** Every tracked,
runnable checker or probe under `docs/reviews/` and `scripts/`, selected
by KIND rather than by name — that is the #115 doctrine this file
violates. A future `verify-*.py` or `measure-*.py` must not be able to
appear outside the population the way `probe-*` did.
`docs/reviews/measure-xref-population.py` is ALREADY a third prefix, so
the list is incomplete by one at the moment you read this.

**THEN EVERY NEW MEMBER NEEDS A REASON, READ OUT OF THE FILE.** Expect
most of the 24 to be short and honest — "run by hand when X changes",
"mutates the tree, cannot share a job with its subject". Expect at least
one (`probe-ci-checker-steps.py`) to deserve a real step instead.

**I TRIED TO PRE-CLASSIFY THEM FOR YOU AND THE INSTRUMENT WAS TOO CRUDE
TO SHIP.** Grepping `write_text|sed -i|cp` to separate "mutates the
tree" from "writes only a temp file" flagged `probe-coverage-ratchet.py`
as a tree-mutator when all nine of its arms write exclusively into a
`TemporaryDirectory`. A static grep cannot see a write's TARGET. So you
get the container measurement, which is exact, and no classification,
which would not be. **Read them one at a time.**

## §E — How your work will be judged

- **THE GATE MUST BE GREEN WHEN YOU FINISH**, or it lands red and people
  learn to ignore it — the failure this repo has measured twice (127
  commits, 119 runs). Widening the container makes it red until every
  new member has a step or a reason. **Both halves land together.**
- **A positive control, both arms.** Add a file that should be caught
  and require RED; record a reason and require GREEN. Read WHICH arm
  fails, never score on the exit code.
- **Set equality, not a count.** A count lets one addition and one
  removal cancel. Assert the examined set EQUALS the enumerated one.
- **Every count carries its container** — "28 probes tracked under
  `docs/reviews/` at `<sha>`", never "28".
- All gates clean before you report, each exit code on its own line,
  including `pre-commit run --all-files` (which now passes and must keep
  passing — it was the trunk's red until an hour ago) and the full suite
  (887 passed, 0 skipped, floor 887).
- Separate what you COULD NOT settle from what you did not attempt.

## §F — Context you are owed

- **CI has still never produced a green run on this trunk.** #161 closed
  the last known red step tonight and the confirming run has not
  finished. **Do not add a new one.** If your widening cannot be made
  green in this run, land the ENUMERATION with every current member
  exempted-with-reason and hand back the ones you could not settle.
- `check-review-coverage.py` reports outstanding trunk commits and is
  deliberately unwired; it is a PR gate awaiting #153. If your work
  makes wiring it possible, say so — do not wire it silently.
- The four already-recorded `UNWIRED_BY_DECISION` reasons are your
  template for tone and specificity.
