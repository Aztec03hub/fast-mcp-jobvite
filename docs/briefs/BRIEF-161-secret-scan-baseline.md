# BRIEF — #161: the secret-scan step fails because the hook rewrites the baseline it then checks

You are `suborch-161`, a Tier-1 sub-orchestrator. Read this whole file
before touching anything. **This is the single step keeping CI red.**

## §A — Standing rules (read FIRST, in this order)

Read these IN FULL before any edit. They are the canon; where a numbered
ADR conflicts with a standard, the ADR wins WITHIN ITS SCOPE only.

1. `docs/DESIGN.md` — FROZEN. You may not change it.
2. `docs/adr/`, every ADR in number order.
3. `docs/OBLIGATIONS.md`
4. `docs/briefs/PROTOCOL-sub-orchestrators.md` — your operating protocol.
5. `CONTRIBUTING.md`

Hard rules:

- **NEVER print or commit a secret.** This task is *about* a secret
  scanner. A test that prints a failing value publishes it. Compare
  HASHES, never plaintext; if you plant a test secret it must be an
  obvious synthetic that never lands in a commit.
- **NO `Co-Authored-By:` or "Generated with" trailers.** Ever.
- **You do not push and you do not merge.** Commit on your own branch in
  your own worktree and report. Tier 0 merges.
- **Make your own worktree**, cut from `origin/main` at `ccbdaae` or
  later: `git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite worktree add ../../fmj-worktrees/w161 -b fix/161-secret-baseline`
- **Run CI's EXACT invocation, flags and all.** Copy the line out of
  `ci.yml`. `uv run --frozen python`, never bare `python3`; and note
  that I misread actionlint as red three times tonight by omitting
  `SHELLCHECK_OPTS=--severity=warning`.
- **Report by `SendMessage` to `fastmcp-jobvite`**, and write findings
  to a `.md` under `docs/reviews/`.
- **Correct this brief where it is wrong.** Eight of eight
  sub-orchestrators have found an error in their brief and every
  correction held. A report with no correction is the anomaly.

## §B — Files you OWN this run

    .github/workflows/ci.yml          (the secret-scan step ONLY)
    .pre-commit-config.yaml
    .secrets.baseline
    docs/reviews/check-secrets-baseline.py       (new, if you build it)
    docs/reviews/probe-secrets-baseline.py       (new, its control)

Nobody else is in the tree right now. If that changes you will be told.

## §C — The defect, already root-caused. Verify it, do not re-derive it

Full statement on task #161. The short form, measured by me in a
detached worktree at `203e5af` with CI's exact command:

`ci.yml` runs `uv tool run pre-commit@4.6.2 run --all-files
--show-diff-on-failure`. Three hooks run; two pass. `detect-secrets`
FAILS, and the diff it prints is **its own rewrite of
`.secrets.baseline`**:

    -        "line_number": 1344,
    +        "line_number": 1431,
    -  "generated_at": "2026-09-01T20:33:41Z"
    +  "generated_at": "2026-09-02T01:09:42Z"

The entry is `.github/workflows/ci.yml`, `is_secret: false` — the
literal `inspect-only-not-a-credential`. **Not a secret, and never
was.** `ci.yml` grew, the recorded line number drifted, detect-secrets
updated the baseline in place, and pre-commit fails whenever a hook
modifies a file. Run it a second time and it fails differently —
*"Your baseline file (.secrets.baseline) is unstaged"*.

In a developer's shell you `git add` and move on. **In CI nothing can be
staged**, so the step goes red on the first line-drift after each
regeneration and cannot recover. The baseline holds 22 entries across 13
live, frequently-edited files, so a bare regeneration buys days at most —
and #143 has just moved `ci.yml` substantially again.

## §D — What to build

`ci.yml:1330-1332` already states the intent:

> What this step genuinely covers is the secret scan over every file,
> and .secrets.baseline staying in step with the tree - a new finding
> nobody audited turns this red.

**A NEW FINDING should turn it red. A LINE NUMBER MOVING should not.**
So gate on the SET of `(filename, hashed_secret)` pairs: fail on a pair
the baseline does not contain. `line_number` and `generated_at` carry no
security information and are the only two fields that move on their own.

Also check the direction nobody has: **an entry in the baseline whose
finding is no longer in the tree is a stale allowance**, invisible
today. Report it. Decide, with a reason, whether it fails or only warns.

Suggested shape, not a ruling: copy the baseline to a temp file, scan
with `--baseline <the copy>` so the tool rewrites the COPY and the tree
is never touched, then compare sets. That is the same trick that let
`probe-coverage-ratchet.py` test a ratchet without mutating anything —
see `check-review-coverage.py --backlog` for the pattern and the reason.

**REFUSE the shortcuts, all three:** do NOT `git add` the baseline
inside CI (that is the gate rewriting its own baseline — measured three
times in one hour in this repo); do NOT `|| true`; do NOT drop the hook.

## §E — How your work will be judged

- **A POSITIVE CONTROL, both arms.** Plant a synthetic new secret →
  require RED. Move a recorded line number → require GREEN. Without both
  the fix is a guess. Read WHICH arm fails, never score on exit code.
- **The new checker must be WIRED in the same commit**, or it is
  inoperative code. `check-checkers-are-wired.py` will tell you; note
  that it enumerates `docs/reviews/check-*.py|sh` by PREFIX (#155), so a
  `probe-*` file is invisible to it — say so rather than relying on it.
- **Every count carries its container.** "22 entries" needs "across 13
  files in `.secrets.baseline` at `<sha>`".
- **`ruff check .`, `ruff format --check .`, `mypy`, `pytest` (887
  passed, 0 skipped, floor 887), `actionlint` with `SHELLCHECK_OPTS`,
  and the full `docs/reviews` gate set must all be clean** before you
  report. Each exit code on its own line.
- Say plainly what you could NOT settle, kept separate from what you did
  not attempt.

## §F — Context you are owed

- CI has **never** produced a green run on this trunk. Until tonight it
  could not: a whole-tree file-type gate refused every commit for 127
  commits. That is fixed. **This step is what remains.**
- The last CI run (`46dafe0`) was 4 of 5 jobs green, failing only here.
- `#143` has just consolidated three jobs into `static-gates`; `ci.yml`
  is freshly rewritten, so read it rather than recalling it.
- Related: `#103` (a fail-open gate, and a second one found proving it),
  `#147` (this step is a multi-line block, which is why the CI-step
  probe could not run it until tonight).
