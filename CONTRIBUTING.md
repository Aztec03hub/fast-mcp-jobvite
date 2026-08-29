# Contributing to `fast-mcp-jobvite`

`readme-standard.md:56 (B104)` requires a repository to link `CONTRIBUTING.md` **or** inline the
contribution rules under the README's Contributing heading. This file is that document, so the
README's Contributing section links here rather than restating it.

This is a public, evolv-owned repository mirrored to a personal fork. It brokers recruiting PII,
so the rules below are not ceremony.

## Before your first commit

```bash
uv sync --frozen        # install exactly uv.lock; never resolves
pre-commit install      # REQUIRED - see "Commit-time gates" below
```

**`pre-commit install` is not optional.** Two gates run at commit time and neither is redundant
with CI: a secret scan (`detect-secrets`), because on a public remote a pushed secret is
compromised the instant it lands and CI only finds it afterwards; and a committed-file-type gate,
because a confidential vendor PDF carries no high-entropy token and passes every secret scanner
cleanly. That second one exists because it has already happened here once.

## Branches

Single `main`, with no `develop` — **ADR-0006**, a recorded deviation from
`development-workflow.md:48-83`, not drift. Branch from `main`, PR back into `main`.

`development-workflow.md:58-68` sets the naming pattern:

| Type | Pattern |
|---|---|
| Feature | `feature/{PREFIX}-{ID}-short-description` |
| Bugfix | `bugfix/{PREFIX}-{ID}-short-description` |
| Hotfix | `hotfix/{PREFIX}-{ID}-short-description` |
| Release | `release/v{VERSION}` |

**On the `{PREFIX}`, honestly:** the corpus contradicts itself. `agentic-coding-standard.md`
expects `FEAT/FR/BUG/TECH`, `quality-gates.md` adds `TECH`, `development-workflow.md:166` expects
layer prefixes like `[FE-001]`, and this work is tracked as `EC-###`. The project deliberately
declined to invent a prefix to satisfy a clause the standards cannot agree on — see the note at
the end of `docs/adr/README.md`. **Use the `EC-###` ticket id.** If that is ever settled, it is
settled by an ADR, not by whoever branches next.

## Commits

`quality-gates.md:234-236` fixes the format, and ruling C3 adopts it:

```
type(scope): description

Refs: EC-###
```

**Never add a `Co-Authored-By` or "Generated with" trailer.**

## Pull requests

- Fill in `.github/pull_request_template.md`. `quality-gates.md:50` gates PR creation on a
  completed template.
- **The PR title is semantic** — `type(scope): description`. This is checked automatically by
  `.github/workflows/pr-title.yml`; a rejected title can be fixed by editing it, and the check
  re-runs on the edit.
- At least **1 approval** (`development-workflow.md:73`), all CI green, no unresolved threads.
- **Squash merge** (`development-workflow.md:82 (B102; enforcement is branch protection, out of tree: B98)`). Delete the branch after merge.

## Reviewing someone else's pull request

**The reviewer checklist is `docs/CODE-REVIEW-CHECKLIST.md`** (`development-workflow.md:248`,
B101), and it is a different obligation from the template above: the template's `## Checklist` is
the *author's* self-check, which is not a review of anything.

- **Every finding ships with a suggested fix**, at every severity including nits. A finding without
  a remedy costs the author the whole diagnosis a second time.
- **A row you cannot verify is not a row you tick.** Say so in the review instead.
- The checklist names the rows of the standard that have **no subject in this repository** and why,
  rather than dropping them - so a missing row means "considered", never "overlooked".

## The gates, and how to run them before you push

CI runs these; run them locally first, because CI is slower than you are.

```bash
# The `test` job
uv sync --frozen                       # install from the lock, never resolve
uv lock --check                        # the lock still agrees with pyproject.toml
uv run --frozen ruff check .           # lint
uv run --frozen ruff format --check .  # format
uv run --frozen mypy                   # types
uv run --frozen pytest                 # the default offline suite, zero skips
bash scripts/check-u0-test-controls.sh # U0's controls, all must fire
bash scripts/check-u15-gate-controls.sh
bash scripts/check-u15-gate-amputation.sh  # survivors are the OUTPUT, not a failure
bash scripts/check-u11-advisory-controls.sh
bash scripts/check-u3-audit-controls.sh    # U3 mutation: every row must be killed
bash scripts/check-u3-audit-amputation.sh  # U3 amputation: survivors are the OUTPUT
bash scripts/check-u4-client-controls.sh   # U4 mutation: every row must be killed
bash scripts/check-u4-client-amputation.sh # U4 amputation: survivors are the OUTPUT
python3 scripts/check-committed-file-types.py --all
uv run --frozen python scripts/check_advisories.py        # the expiry half
uv run --frozen pip-audit $(uv run --frozen python scripts/check_advisories.py)

# The `design-gates` job
python3 docs/reviews/check-coupling.py docs/DESIGN.md
python3 docs/reviews/check-coupling-controls.py
python3 docs/reviews/check-coupling-sweep.py
python3 docs/reviews/check-obligations.py
python3 docs/reviews/check-obligations.py --controls
python3 docs/reviews/check-plan-measurements.py
```

## Measurements a human runs, which are NOT gates

```bash
bash scripts/check-u1-pid1-shutdown.sh    # needs Docker; exits 2 if unavailable
```

This puts the interpreter at **PID 1** in a container with no `--init` and sends a real SIGTERM via
`docker stop -t 15`, on both transports, closing the second of `DESIGN.md`'s two inherited limits on
the shutdown mitigation. **It is deliberately not in `ci.yml`**: CI has no Docker daemon, and a
required check that goes red for reasons nobody caused trains everyone to ignore it.

It exits **2** when Docker is missing, never 0 - a skip that reports success is a green that tested
nothing. Read the header before trusting a pass; it states exactly what the measurement does and
does not cover.

**`mypy` is the type gate, not `pyright`.** `pyright` may be on your PATH; it is not declared in
`pyproject.toml`, is not what CI runs, and `backend/python.md:370` names mypy. Running it proves
nothing about whether this repository is green, and `uv run --frozen pyright` would resolve a tool
outside the frozen lock - the defect ADR-0015 records for `pip-licenses`.

**This list was five commands until 2026-08-28 and CI ran fifteen.** A contributor who ran the
documented five got a clean result and a red build, which is exactly what happened: a new test that
walked `.github/workflows/` broke `check-u0-test-controls.sh`, whose COPY list omitted `.github`,
and the author did not run it because it was not on this list. **If you add a step to `ci.yml`, add
it here in the same commit.**

Three things about the test suite that will otherwise surprise you:

- **A skip counts as a failure.** CI greps for skipped tests and goes red on any. The credentialed
  and network arms are excluded by *selection* (`-m` in `addopts`), never by `skipif`.
- **`--strict-markers` is on.** An undeclared marker fails collection instead of silently
  selecting nothing. Declare new markers in `pyproject.toml`.
- **A collection guard runs.** Every `test_*.py` must be reachable from the configured `testpaths`.
  A test file outside them fails the build rather than being quietly never run.

## Changelog

Keep a Changelog 1.1.0, under `## [Unreleased]`. User-facing changes only —
`changelog-standard.md:94` forbids internal-only entries. Dates are publication dates; backdating
is not allowed.

## Security

Do not open a public issue for a vulnerability. See [`SECURITY.md`](./SECURITY.md).

Never commit a real Jobvite tenant id, client name, credential, or internal hostname — in code,
tests, fixtures **or** documentation. `.env` is gitignored; `.env.example` carries empty
placeholders on purpose and is scanned like any other file.

## Where the rules actually come from

This file summarises; it is not the authority.

- `docs/DESIGN.md` — **frozen**. Only a numbered ADR may change it.
- `docs/adr/` — the numbered decisions, and the only way to change the design.
- `docs/DECISIONS.md` — the pre-freeze decision log.
- `docs/research/COMPLIANCE-SPEC.md` — this repository's obligations, with citations.

If a rule here disagrees with an ADR, **the ADR wins and this file is wrong** — please fix it.
