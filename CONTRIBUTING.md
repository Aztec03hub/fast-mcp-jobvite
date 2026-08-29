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

**The body does not change.** Ruling C3 fixes the SUBJECT line. The long explanatory bodies in this
history are the part worth reading, and no clause objects to them - a commit here is expected to say
what was measured and what it means, not merely what changed.

**History predating this rule does not conform, and will NOT be rewritten.** Measured at `afaf226`:
**50 of 222** subject lines match, and the conforming ones are almost all recent. That is not drift
to be cleaned up; it is a decision. A gate red on a hundred and seventy commits nobody will rewrite
teaches everyone to ignore the gate, which is the same argument this project already accepted for
the cross-reference gate (wired only on the day it went green) and for `pip-audit`.

So the subject-line rule is enforced by **review**, which is what ruling C3's own
"commitlint / review" column allows. A `commit-msg` hook for NEW commits only may be added later.

**And a caution from the author of that decision.** I broke the rule myself within hours of taking
it - one commit in twenty, written while doing something else. If that rate continues, "enforced by
review" is the wrong answer and a new-commits-only hook becomes the right one. The evidence for
changing course is a measurement, not an opinion:

```bash
git log --format='%s' | grep -cvE '^[a-z]+(\([a-z0-9._/-]+\))?: '
```

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
bash scripts/check-u1-boot-controls.sh     # U1 mutation: every row must fire
bash scripts/check-u1-boot-amputation.sh   # U1 amputation: survivors are the OUTPUT
bash scripts/check-u3-audit-controls.sh    # U3 mutation: every row must be killed
bash scripts/check-u3-audit-amputation.sh  # U3 amputation: survivors are the OUTPUT
bash scripts/check-u4-client-controls.sh   # U4 mutation: every row must be killed
bash scripts/check-u4-client-amputation.sh # U4 amputation: survivors are the OUTPUT
bash scripts/check-suite-floor-amputation.sh  # the guard that floors the suite size
python3 scripts/check-committed-file-types.py --all
uv run --frozen python scripts/check_advisories.py        # the expiry half
uv run --frozen pip-audit $(uv run --frozen python scripts/check_advisories.py)

# The `design-gates` job
python3 docs/reviews/check-coupling.py docs/DESIGN.md
python3 docs/reviews/check-cross-references.py   # every SSn.m resolves in its own document
python3 docs/reviews/check-coupling-controls.py
python3 docs/reviews/check-coupling-sweep.py
python3 docs/reviews/check-obligations.py
python3 docs/reviews/check-obligations.py --controls
python3 docs/reviews/check-plan-measurements.py
python3 docs/reviews/check-resweep-verdicts.py  # the resweep's tally checks itself
```

## Measurements a human runs, which are NOT gates

```bash
bash scripts/check-u1-pid1-shutdown.sh    # needs Docker; exits 2 if unavailable
python3 docs/reviews/check-clause-citations.py  # needs the standards repo; exits 2 if absent
```

**`check-clause-citations.py` resolves the CLAUSE column** - the half of every obligation row that says why the obligation is real. `check-obligations.py` verifies the artifact and says nothing about the clause. It cannot be a CI gate: it reads the `evolv-coder-standards` sibling checkout, which CI does not have. It proves each citation RESOLVES and explicitly does NOT prove the cited line says what the row claims - read the text it prints.

**`check-u1-pid1-shutdown.sh` puts the interpreter at PID 1** in a container with no `--init` and
sends a real SIGTERM via `docker stop -t 15`, on both transports, closing the second of
`DESIGN.md`'s two inherited limits on the shutdown mitigation. (This paragraph opened with "This
puts the interpreter at PID 1" until a second script was added to the block above it, at which point
"this" silently began pointing at the wrong one. A pronoun is a reference that nothing checks.)
**It is deliberately not in `ci.yml`**: CI has no Docker daemon, and a required check that goes red
for reasons nobody caused trains everyone to ignore it.

**"On both transports" is a claim this sentence briefly did not earn, and the fix was to the
harness rather than to the sentence.** R3-M2: the PID-1 assertion used to sit in an `http`-only
branch, because it grepped uvicorn's `Started server process [1]` - a log line `stdio` never emits.
The `stdio` arm asserted only that the lifespan closed inside the grace period, and a process that
is **not** PID 1 satisfies both of those, so this paragraph described coverage the measurement did
not have. Measured, not argued: the pre-fix script with `--init` added puts the interpreter at pid 7
and the `stdio` arm still passes. The entry script now records its own pid in the marker
(`opened pid=<n>`, from `tests/boot_process.py`'s `MARKER_ENTRY`) and **both** arms check it, so the
sentence above is now true of what the script does. An arm that finds no pid in the marker at all
fails with its own distinct message rather than degrading to the weaker check.

It exits **2** when Docker is missing, never 0 - a skip that reports success is a green that tested
nothing. Read the header before trusting a pass; it states exactly what the measurement does and
does not cover, including that the container runs this repository's virtualenv under
`python:3.12-slim` rather than an image built from a Dockerfile this project does not have.

**A sentence here that claims coverage a harness does not have fails in the same way the harness
would.** It occupies the place a reader consults to decide whether a limit is closed, and answers
yes. If you change what one of these measurements covers, this paragraph is part of the change.

**`check-design-citations.py` is NOT a gate, and that is deliberate.** Run it around any edit to
`docs/DESIGN.md`:

```bash
python3 docs/reviews/check-design-citations.py                 # bounds + inventory
python3 docs/reviews/check-design-citations.py --since <sha>   # what your edit moved
python3 docs/reviews/repoint-design-citations.py <sha> --write # apply the MOVED lines
```

There are 847 `DESIGN.md:N` citations across 82 files and a five-line insertion moves most of them,
so an edit that skips this ships hundreds of wrong citations. It is not in CI because **the check
it can perform is not the one that matters**: it verifies that a cited line EXISTS, never that the
line still carries its subject, and a contracted range still resolves and still reads plausibly.
Three such defects were found by hand and none by any instrument. Wiring it would publish a green
that means less than a reader would assume. The repointer skips `BROKEN` lines - where the cited
line itself changed - because only a human re-reading the subject can repoint those, and it skips
any line marked `REPOINT-EXEMPT`, which is how a script that WRITES an example citation says it is
not citing anything.

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
