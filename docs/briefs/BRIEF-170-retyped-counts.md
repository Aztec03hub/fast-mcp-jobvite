# BRIEF — #170: a retyped count beside a container that grows, for the third time

You are `suborch-170`. The shape has now been found three times by
three different routes and nobody has ever counted how many instances
exist. **Measuring that container is the deliverable, even if you fix
nothing.**

## §A — Standing rules (read FIRST, in this order)

1. `docs/DESIGN.md` — FROZEN, you may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md` — and read row **BASH-1** in full; it is the
   instance that raised this.
4. `docs/briefs/PROTOCOL-sub-orchestrators.md`
5. `CONTRIBUTING.md`

Hard rules:

- **NEVER print or commit a secret.** No `Co-Authored-By:` or
  "Generated with" trailers, ever, in any repo.
- **You do not push and you do not merge.** Commit on your branch.
- **DO NOT PUSH — a CI run is in flight.** GitHub cancels older QUEUED
  runs in a concurrency group regardless of `cancel-in-progress`, and
  the first run on this trunk ever to reach the deep harness steps is
  running now. Tier 0 will push when it concludes.
- **Own worktree**, from `origin/main`:
  `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w170 -b fix/170-retyped-counts`
  Note that three commits (`9c08427`, `6de1b4a`, `d0bdf2a`) are LOCAL
  ONLY and not on `origin/main`. `d0bdf2a` is the BASH-1 fix and is the
  worked example for this task — read it with
  `git -C <the main checkout> show d0bdf2a`.
- **`TaskGet` before acting on any assignment, and compare the TEXT to
  this brief.** ANY `TaskUpdate` re-emits a task's ORIGINAL description
  as an assignment, timestamped LATER than the completion, `assignedBy`
  naming you. Measured four times (#162). Never "check who sent it".
- **CI's exact invocations.** `uv run --frozen python`, never bare
  `python3`, where CI uses it. If a tool is missing, SAY SO rather than
  claiming the gate.
- **Report by `SendMessage` to `fastmcp-jobvite`**; findings to a `.md`
  under `docs/reviews/`.
- **Correct this brief where it is wrong.** Sixteen of sixteen agents
  have found an error in theirs, and the last four corrections each
  changed what got built.

## §B — Files you OWN

    docs/reviews/<your sweep tool>.py
    docs/reviews/<your findings .md>
    docs/reviews/check-checkers-are-wired.py   (ONE entry, if you leave
                                                the tool unwired)

**NOT yours without saying so first:** `.github/workflows/ci.yml`,
`docs/OBLIGATIONS.md` (BASH-1 is already fixed), anything under `src/`.
If your sweep finds a number worth changing, REPORT it with a suggested
fix. Do not sweep-edit prose across the repo.

## §C — The three instances, and why the third is the interesting one

- **#116** — 70 retyped seconds figures, replaced by derivation.
- **#166** — `docs/README.md:22` "Eleven decision records" and
  `docs/adr/README.md:7` "eleven ADRs" against **33**. Ruled: DELETE
  both numbers, do not replace 11 with 33. Its siblings "Seven reports"
  and "Six further gates" were checked and were CORRECT — say when you
  check something and find it right.
- **BASH-1**, `d0bdf2a` — "all 20 `scripts/*.sh` run `set -uo pipefail`"
  against a measured **39 tracked, 37 with the option**.

**THE THIRD ONE IS WHY THIS TASK EXISTS, and it is not the staleness.**
The word **"all" was false independently of the number**, and replacing
20 with 37 would have HIDDEN that: two members are outside the rule and
both are correct — `scripts/check-pytest-bounded.sh` runs the full
`set -euo pipefail` and is COMPLIANT rather than deviating, and
`scripts/lib/harness-result.sh` is SOURCED and must carry neither a
shebang nor a `set`. A cell that said "37" would still have claimed
every member deviates.

**So a stale number is sometimes the symptom of a false claim, and the
two need different remedies.**

## §D — What to build, IN THIS ORDER

1. **MEASURE THE CONTAINER FIRST, and report it before any finding.**
   Enumerate candidates **BY KIND, never by prefix or path** (#115):
   a number word or digit standing next to a plural noun that names a
   set this repository can enumerate — files matching a glob, rows in a
   table, list members, ADRs, harnesses, tests, arms. **Nobody has this
   number.** A findings list with no container size is a claim about
   where you looked.
2. **Derive the true figure for each candidate** and compare.
3. **Classify into THREE outcomes, because they take three actions:**
   - merely stale → delete the number, or derive it;
   - stale AND the surrounding claim (`all`, `every`, `none`, `only`)
     is false → **rewrite the claim**, do not replace the digit;
   - inside a DATED RECORD (`docs/worklogs`, `docs/plans`, `REPORT-*`,
     a review) → **correct as written, leave it alone.** #166 measured
     this and deliberately left REPORT-147 §6's stale 13 in place.
4. **Ship a RUNNABLE tool, not prose.** Prose about a measurement
   decays into a claim about one. If the tool cannot go red — and a
   census tool usually cannot — leave it UNWIRED and record the reason
   in `check-checkers-are-wired.py`'s register, in the shape the
   entries above it use. Note that the register only sees TRACKED
   files, so `git add` it before you believe an exit 0.

## §E — How your work will be judged

- **Every count carries its container and its sha** — "39 tracked
  `scripts/*.sh` at `d0bdf2a`", never "39".
- **A zero is a finding about your selector until proved otherwise.**
  If the sweep reports few candidates, plant one and require it to be
  found; say what the plant was.
- **Say which candidates you checked AND FOUND CORRECT.** #166's report
  is better because it names the two siblings it cleared.
- All gates green before you report, each exit code on its own line:
  `uv run --frozen ruff check .`, `ruff format --check .`, `mypy`, the
  full suite (887 passed, 0 skipped), `pre-commit run --all-files`.
  **mypy has caught errors in two agents' new files after they reported
  green — run it on anything you add.**
- Separate COULD NOT SETTLE from did not attempt.

## §F — Context you are owed

- `review-r18` is running in another worktree over tonight's gate
  commits. You will not collide: it is read-only outside its own report
  and the backlog file.
- The backlog file `docs/reviews/review-coverage-backlog.txt` is Tier
  0's tonight. **Do not edit it**; if your commits make it grow, say so
  in your report and Tier 0 will record them.
