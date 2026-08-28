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

## The gates, and how to run them before you push

CI runs these; run them locally first, because CI is slower than you are.

```bash
uv run --frozen ruff check .           # lint
uv run --frozen ruff format --check .  # format
uv run --frozen mypy                   # types
uv run --frozen pytest                 # the default offline suite
uv lock --check                        # the lock still agrees with pyproject.toml
```

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
