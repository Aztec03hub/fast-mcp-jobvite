# `fast-mcp-jobvite` — Repository Compliance Spec

**Task:** R3b · **Author:** standards-research · **Date:** 2026-08-27
**Companion:** [`STANDARDS.md`](./STANDARDS.md) — that document says *what binds and
why*, with `file:line` evidence. **This document says what to build.** It is written to
be executable without re-reading the standards corpus.

**Repo:** `evolvconsulting/fast-mcp-jobvite` — evolv-owned, **public**, mirrored to
`Aztec03hub/fast-mcp-jobvite`. Single Python package. **No database, no container image,
no frontend, no deployed environment.**

## Settled inputs (rulings — do not re-argue)

| # | Ruling | Effect here |
|---|---|---|
| C1 | Python floor **`>=3.12`** | `requires-python`, ruff `target-version`, CI matrix |
| C2 | `error-contract.md` wins over `agentic-coding-standard.md:283-294` | never `raise HTTPException`; RFC 9457 only |
| C3 | Commit format `type(scope): description` + `Refs:` trailer | commitlint / review |
| C4 | PR title semantic/conventional; **do not** install the `[FEAT-XXX]` check | CI job list |
| C5 | Redis rate-limiter **opted out, with an ADR** | no Redis; ADR required at design freeze |
| C6 | `ai/tool-calling.md` + `ai/agent-guardrails.md` **bind, by intent** | B9-B23 are in force; ADR at design freeze |
| G2 | **Apache-2.0**, `Copyright (c) 2026 evolv Consulting` | **Settled by D13, and this row said MIT until 2026-08-28.** MIT was the default this repo started from, not a choice; `docs/DECISIONS.md` D13 decided Apache-2.0 on the express patent grant, and the tree has been Apache-2.0 since (`pyproject.toml:6`, `LICENSE`, `NOTICE`) |

> **Note on the Python floor.** The task brief for this spec says "the repo targets
> Python 3.11+", but ruling C1 (issued later, and explicit) sets `>=3.12`. **I have
> built this spec to `>=3.12`.** If 3.11 is genuinely required for reach, that reverses
> C1 and needs an ADR — flagged rather than silently reconciled.

**Marking convention.** Every line is one of:
**[STD]** — mandated by a standard, with `file:line` and quote.
**[REC]** — my recommendation where the corpus is **SILENT**. Not a citation.
**[N/A]** — an obligation that cannot apply here, with the reason.

---

## 1. CI workflow spec

Single workflow file is sufficient for this repo; split into `ci.yml` + `security.yml`
if you prefer to match `devops/ci-cd.md`'s layout (`:41-52`).

### 1.1 Triggers and matrix

**[STD]** Trigger on push to the default branch and on every PR.
`devops/ci-cd.md:62-66` — `on: push: branches: [main, develop]` / `pull_request:`.
**[STD]** Weekly security schedule. `devops/ci-cd.md:455-456` — `cron: '0 0 * * 0'`.
**[STD]** Python `3.12`. `devops/ci-cd.md:70` — `PYTHON_VERSION: '3.12'`; floor from
`architecture/reference-architecture.md:83` — *"| Language | Python | `>=3.12` |"*.

**[REC] No version matrix.** The standards define a single pinned `PYTHON_VERSION`, not
a matrix; `devops/ci-cd.md:772-779` shows matrices only as a "Best Practices" example.
A published library arguably *should* test the range it claims to support — if
`requires-python` says `>=3.12`, test `['3.12', '3.13']`. Corpus is **SILENT** on
libraries; single-version is the compliant minimum and the matrix is my recommendation.

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'   # weekly security sweep — ci-cd.md:455-456
env:
  PYTHON_VERSION: '3.12'
permissions:
  contents: read
```

### 1.2 Job table

| # | Job | Command | Goes red when | Blocking? | Source |
|---|---|---|---|---|---|
| 1 | `lint` | `uv run ruff check .` | any lint error | **Blocking** | `ci-cd.md:182`; `quality-gates.md:63` *"\| Backend Lint \| Ruff \| 0 errors \|"* |
| 2 | `format` | `uv run ruff format --check .` | any file would be reformatted | **Blocking** | `ci-cd.md:185` |
| 3 | `types` | `uv run mypy src` | any type error | **Blocking** | `ci-cd.md:188`; `quality-gates.md:64` *"\| Backend Types \| mypy \| 0 errors \|"* |
| 4 | `test` | `uv run pytest --cov=src/fast_mcp_jobvite --cov-report=xml` | test failure, coverage <80%, **or any skip** | **Blocking** | `ci-cd.md:239`; `quality-gates.md:65` |
| 5 | `test` (skip assert) | assert reported `SKIPPED == 0` | any skipped test in a required suite | **Blocking** | `quality-gates.md:89-94`; `ci-cd.md:707-721` |
| 6 | `pip-audit` | `uv run pip-audit` | **any** advisory (no severity threshold) | **Blocking** | `supply-chain-security.md:94-101` |
| 7 | `codeql` | `github/codeql-action/analyze@v3`, language `python` | high/critical finding | **Blocking** | `ci-cd.md:500-511`; `quality-gates.md:70` |
| 8 | `secrets-scan` | `trufflesecurity/trufflehog@v3.88.0`, `fetch-depth: 0` | any verified secret | **Blocking** | `ci-cd.md:547-556` |
| 9 | `sbom` | `anchore/sbom-action@v0` ×2 (CycloneDX + SPDX) | action failure | **Blocking** (artifact required) | `quality-gates.md:262-274` |
| 10 | `license-scan` | `uv run pip-licenses --allow-only '…'` | dep outside allow-list | **Blocking** | `ci-cd.md:648-651`; `quality-gates.md:282` |
| 11 | `pr-title` | `amannn/action-semantic-pull-request@v5` | non-conventional PR title | **Blocking** | `ci-cd.md:305-321`; ruling C4 |
| 12 | `links` | link checker over `*.md` | broken link | **Blocking** | `readme-standard.md:69` *"a link checker MUST run in CI; a broken link blocks merge"* |
| 13 | `quickstart` | execute the README Quickstart | Quickstart commands fail | **Blocking** on default branch | `readme-standard.md:67` |

**Advisory (non-blocking):** none of the above is advisory under the standards. The one
place the corpus explicitly permits `continue-on-error` is the **frontend** `npm audit`
(`ci-cd.md:474`), which is **[N/A]** here. `pip-audit` has **no** such escape:
`supply-chain-security.md:96` — *"The scan **MUST FAIL the build** on any known **High**
or **Critical**"*, tightened by `:99-101` — *"`pip-audit` has **no severity threshold**
and fails on **any** advisory"*.

> **Practical warning, [REC]:** because `pip-audit` fails on *any* advisory, job 6 will
> eventually go red on a transitive dependency with no fix available. The standard
> anticipates this: `supply-chain-security.md:130-131` requires an unremediable advisory
> to be **tracked**, not suppressed. Plan for an `--ignore-vuln` list that is reviewed,
> not a `continue-on-error`.

### 1.3 Jobs that CANNOT work here — explicit non-applicability

Listed rather than silently omitted, per the brief.

| Obligation | Source | Verdict |
|---|---|---|
| Container image scan (Trivy) | `ci-cd.md:513-541`; `quality-gates.md:70` | **[N/A] — no container image is built or published by this repo.** Becomes live the day a Dockerfile lands. |
| Cosign / Sigstore image signing | `supply-chain-security.md:190-196` — *"Container images **MUST** be signed with **Sigstore / cosign**"* | **[N/A] — obligation is scoped to container images ("Container images MUST be signed"), and there are none.** |
| Immutable digest pinning (`@sha256:…`) | `supply-chain-security.md:199` | **[N/A] — digest pinning applies to image references; this repo publishes no image.** |
| Deploy pipeline rejects unsigned artifacts | `supply-chain-security.md:196` | **[N/A] — there is no deploy pipeline.** |
| SLSA v1.2 provenance attestation | `supply-chain-security.md:164-173` | **[N/A] for now, with a caveat** — phrased around a build platform producing a release artifact. No artifact is published today. **If this is ever published to PyPI, this becomes live and is unanswered** (gap G5). |
| Postgres / Redis service containers | `ci-cd.md:196-220` | **[N/A] — no database, no Redis (ruling C5).** |
| `alembic upgrade head` | `ci-cd.md:233-236` | **[N/A] — no database, no migrations.** |
| Frontend lint/test/build, Playwright E2E, Lighthouse | `ci-cd.md:74-160`, `:251-284`, `:381-440` | **[N/A] — no frontend.** |
| Bundle-size check | `ci-cd.md:362-372` | **[N/A] — no bundle.** |
| `npm audit`, `license-checker` | `ci-cd.md:471-473`, `:632-638` | **[N/A] — no Node dependencies.** |
| Codecov upload | `ci-cd.md:245-249` | **[REC] optional** — the standard shows it, but coverage is already gated locally by `--cov-fail-under`. Adding it requires a token on a public repo; not worth it. Corpus does not independently mandate Codecov. |
| `[FEAT-XXX]` PR-title check | `agentic-coding-standard.md:398-403` | **[N/A] by ruling C4** — conflicts irreconcilably with job 11. |

### 1.4 Branch protection wiring

**[STD]** A skipped required check must fail, not pass.
`devops/ci-cd.md:679-681` — *"**Do not set `skipped == success` for required checks.**"*
**[STD]** Path-filtered jobs must not be direct required checks.
`devops/ci-cd.md:723-726` — *"**Path-filtered jobs that skip are not required checks.**
A job that may legitimately not run … must not be a direct branch-protection
requirement. Gate it through an aggregator"*.

**[REC]** This repo is small enough to have **no path filters at all**, which sidesteps
the aggregator entirely. Run every job on every PR. Simplest thing that satisfies both
clauses.

### 1.5 Pinned action versions (copy exactly)

```
actions/checkout@v6                          # ci-cd.md:81
astral-sh/setup-uv@v4                        # ci-cd.md:173
actions/upload-artifact@v4                   # ci-cd.md:157
github/codeql-action/init@v3                 # ci-cd.md:501
github/codeql-action/autobuild@v3            # ci-cd.md:506
github/codeql-action/analyze@v3              # ci-cd.md:509
trufflesecurity/trufflehog@v3.88.0           # ci-cd.md:552
anchore/sbom-action@v0                       # quality-gates.md:270 (major-tag pin is deliberate)
amannn/action-semantic-pull-request@v5       # ci-cd.md:306
```

### 1.6 Licence allow-list string (verbatim)

`devops/ci-cd.md:648-651`:
```
MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;Apache Software License;MIT License;BSD License;ISC License (ISCL)
```
Canonical SPDX set: `quality-gates.md:288-294` — MIT, Apache-2.0, BSD-2-Clause,
BSD-3-Clause, ISC. Flag-list requires legal review **and an ADR** (`:283-284`).

---

## 2. `pyproject.toml` — ready to paste

### 2.1 The type checker: **mypy**, and it is not currently installed

**[STD] The mandated type checker is `mypy`.**
`architecture/reference-architecture.md:92` — *"| Lint / type / test | ruff / mypy /
pytest | — | ruff format (not Black) |"*
`backend/python.md:371` — *"**mypy**: Static type checking"*
`devops/quality-gates.md:64` — *"| Backend Types | mypy | 0 errors |"*

**Explicitly named, as requested:** `fast-mcp-jira` has **no mypy** in its dev
dependencies and no `[tool.mypy]` block. If this repo is scaffolded from that one, mypy
will be missing and CI job 3 cannot run. **It must be added.**

**[REC] Strictness.** The corpus mandates *that* mypy runs with **0 errors**
(`quality-gates.md:64`) but **is SILENT on which flags**. There is no `[tool.mypy]`
block anywhere in the standards. `backend/python.md:76` requires type hints on all
function parameters and returns, and `agentic-coding-standard.md:169` requires *"Python
has type hints on all public functions"* — `disallow_untyped_defs` is the flag that
mechanically enforces exactly that, so I recommend it as the closest faithful
implementation. `strict = true` is my recommendation for a greenfield repo, not a
citation.

### 2.2 Blocks

```toml
[project]
requires-python = ">=3.12"          # reference-architecture.md:83; ruling C1

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov",                   # testing.md:46 — coverage is a required gate
    "mypy",                         # reference-architecture.md:92 — MISSING in fast-mcp-jira
    "ruff>=0.8",
    "pip-audit",                    # supply-chain-security.md:94
    "pip-licenses",                 # ci-cd.md:648
]

# ---------------------------------------------------------------- ruff
[tool.ruff]
line-length = 88                    # python.md:35 "Maximum line length: 88 characters"
target-version = "py312"            # ruling C1

[tool.ruff.lint]
# python.md:368-371 mandates ruff for lint + import sorting (replaces isort/flake8).
# The specific rule set is NOT specified by any standard -> [REC] below.
select = [
    "E", "W",      # pycodestyle       [STD] PEP 8 — python.md:28
    "F",           # pyflakes          [STD] lint — quality-gates.md:63
    "I",           # isort             [STD] import order — python.md:54-58
    "N",           # pep8-naming       [STD] naming table — python.md:62-72
    "D",           # pydocstyle        [STD] PEP 257 — python.md:29
    "UP",          # pyupgrade         [REC]
    "B",           # bugbear           [REC] catches mutable defaults — python.md:193-206
    "S",           # bandit            [REC] security lint; supports agentic-coding-standard.md:123-135
    "ASYNC",       # async correctness [REC]
    "DTZ",         # naive datetimes   [STD] enforces python.md:227 (no datetime.utcnow)
    "T20",         # flake8-print      [STD] observability.md:642 "no print statements"
    "ANN",         # annotations       [STD] python.md:76 type hints required
]
ignore = ["D203", "D213"]           # mutually exclusive with D211/D212

[tool.ruff.lint.pydocstyle]
convention = "google"               # python.md:97 "Google-style or NumPy-style"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "D103", "ANN"] # [REC] asserts and undocumented tests are fine

# ---------------------------------------------------------------- mypy
[tool.mypy]                         # [REC] — corpus mandates mypy, is SILENT on flags
python_version = "3.12"
strict = true
disallow_untyped_defs = true        # closest mechanical enforcement of python.md:76
warn_unused_ignores = true
warn_return_any = true

# ---------------------------------------------------------------- pytest
[tool.pytest.ini_options]           # verbatim from backend/testing.md:56-78
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "-ra",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "adversarial: red-team cases; merge-gating (tool-calling.md:185)",   # [REC] marker
]
filterwarnings = ["ignore::DeprecationWarning"]

# ---------------------------------------------------------------- coverage
[tool.coverage.run]                 # backend/testing.md:80-87
source = ["src/fast_mcp_jobvite"]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]              # backend/testing.md:89-97
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80                     # [STD] testing.md:96, :585; quality-gates.md:44
show_missing = true
```

### 2.3 Coverage targets per module category (gap G6 resolved)

**[STD] 80% overall is the hard floor** — `backend/testing.md:96` (`fail_under = 80`),
`:585` *"| Overall | 80% |"*, `quality-gates.md:44`.

The corpus's sub-categories (Services / API Routes / Utilities / Models,
`backend/testing.md:586-589`) are written for a layered FastAPI app and **none of them
names an MCP tool module** — that was gap G6. **[REC] mapping**, carrying the numbers
the team asked for:

| Module | Target | Mapped from | Basis |
|---|---|---|---|
| `tools/*.py` | **85%** | "API Routes 85%" | `backend/testing.md:587` — tools are this server's request surface |
| `services/jobvite_client.py` | **90%** | "Services 90%" | `backend/testing.md:586` — business logic / orchestration |
| `utils/*.py` | **95%** | "Utilities 95%" | `backend/testing.md:588` — pure functions |
| overall | **80%** | floor | `backend/testing.md:96` |
| auth verifier, argument-rejection path, every write tool | **95% line / 90% branch** | "Critical Paths" | `architecture/testing-strategy.md:306`, and `:310-314` defines critical paths to include *"Data mutations"* and *"Security-sensitive operations"* |

`fail_under = 80` is the only threshold that is mechanically enforceable in one number;
**[REC]** enforce the per-module targets in review (§5 checklist) rather than inventing
a bespoke coverage plugin. Adding per-module gates is possible via `coverage`'s
`[tool.coverage.paths]` only awkwardly — not worth the machinery.

### 2.4 Test-discovery guard (required, easy to forget)

**[STD]** `backend/testing.md:138-141` — *"**A collection-guard meta-test is required.**
… The guard must itself live inside a configured root so that its own absence fails
collection"*. `quality-gates.md:76-81` — *"If the guard is absent or if any test file
lives outside the configured roots, the CI backend test job MUST fail."*

Create `tests/test_collection_guard.py` asserting no `test_*.py` exists outside
`testpaths`.

---

## 3. Documentation obligations, per file

| File | Status | Source / note |
|---|---|---|
| `README.md` | **[STD] REQUIRED** | `readme-standard.md:34` — *"The top level of every Git repository"* |
| `CHANGELOG.md` | **[STD] REQUIRED** | `changelog-standard.md:42` Keep a Changelog 1.1.0 |
| `LICENSE` | **[STD] REQUIRED** | `readme-standard.md:57` - SPDX id + link. **Settled: Apache-2.0, `Copyright (c) 2026 evolv Consulting`** (D13; this line said MIT until 2026-08-28, after the tree had already changed) |
| `CONTRIBUTING.md` | **[STD] REQUIRED *or* inlined** | `readme-standard.md:56` — *"link to `CONTRIBUTING.md` or equivalent. Repos without that file must inline the contribution rules under this heading."* |
| `SECURITY.md` | **SILENT** → **[REC] add** | 0 hits corpus-wide. A public repo brokering recruiting PII with no disclosure route is indefensible; ~10 lines. |
| `CODE_OF_CONDUCT.md` | **SILENT** → **[REC] optional** | 0 hits. Conventional for public org repos; low value for a solo-maintained integration. |
| `CODEOWNERS` | **SILENT / NOT REQUIRED** | 0 hits. Nearest obligation is `readme-standard.md:58` — *"14. **Maintainers** — named owners"* — satisfied **in the README**, not by this file. **[REC]** add anyway: it is how GitHub actually enforces `development-workflow.md:73`'s ≥1 approval on an org repo. |
| `.github/pull_request_template.md` | **[STD] content REQUIRED, path SILENT** | Template body mandated verbatim `development-workflow.md:199-242`; `quality-gates.md:50` gates on *"Completed PR template"*. 0 hits for `pull_request_template` → path is **[REC]** GitHub convention. |
| `.env.example` | **[STD] REQUIRED** | `environments.md:141-144`, `:230-233`; `security.md:418` — *"# .env.example (commit this)"* |
| `.gitignore` | **[STD] REQUIRED content** | `environments.md:614-622` — `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`, `secrets/` |

### 3.1 README — required sections, exact order

**[STD]** `readme-standard.md:43` — *"Every README MUST contain the following sections,
in this order. Section headings must match exactly so that automated checks can locate
them."* (`:45-58`)

1. Title — `# fast-mcp-jobvite`
2. One-line description — *"no marketing language"* (`:46`)
3. Status badges — *"At least one CI status badge is required"* (`:47`); **[STD]** badges
   must be live, `:70` — *"Static SVGs that no longer reflect reality are forbidden"*
4. Quickstart — *"fewer than five commands"* (`:48`)
5. Installation
6. Configuration — table with columns **`Name`, `Required`, `Default`, `Description`**;
   *"Secrets are referenced by name only; never include real values"* (`:50`)
7. Usage examples — *"copy-paste runnable"* (`:51`)
8. API / CLI reference link
9. Development setup
10. Testing — *"the single command that runs the test suite"* (`:54`)
11. Deployment — **[N/A] content**, but the heading is required by `:43`'s "must match
    exactly"; **[REC]** keep the heading and state "not deployed; consumed as an MCP
    server" rather than delete it
12. Contributing
13. License - **`Apache-2.0` (SPDX)** + link to `LICENSE`. **Not MIT** - D13, and the LICENSE file in the tree is the Apache 2.0 text
14. Maintainers

**[STD]** ≤500 lines (`:64`); every env var appears in the Configuration table and new
vars update it in the same PR (`:66`).

### 3.2 CHANGELOG

**[STD]** Keep a Changelog 1.1.0 (`changelog-standard.md:42`); `## [Unreleased]` at top
(`:84`); subsections `Added/Changed/Deprecated/Removed/Fixed/Security`, empty ones
omitted (`:82`); `BREAKING:` prefix + migration note + major bump (`:91`); Security
entries carry a CVE where one exists (`:92`); dates are publication dates, backdating
forbidden (`:93`); **internal-only changes MUST NOT appear** (`:94`).

---

## 4. The G1 question — RESOLVED, G1 CLOSES

I read `devops/development-workflow.md` (`priority: required`) in full. **It defines
three of the four things asked, and does not define the fourth.**

**Branch naming — YES.** `:58-68`:
> *"| Feature (Backend) | `feature/BE-{ID}-short-description` | `feature/BE-001-user-api` |"*
with `bugfix/`, `hotfix/`, and `release/v{VERSION}` rows, prefixes FE / BE / DB / DO.

**PR review requirements — YES.** `:73` — *"Requires PR with at least 1 approval"*;
`:183-187` — *"At least 1 approval from team member / All review comments addressed /
No unresolved threads / Reviewer verifies code review checklist"*; `:248` — *"Reviewers
must verify all items before approving"*.

**Merge strategy — YES.** `:82` — *"Squash merge required"*; `:192-194` — *"Squash and
merge / … / Delete feature branch after merge"*.

**Release tagging — NO.** The file's branch table has `release/v{VERSION}` (`:68`) but
nothing on tag format, when to tag, or how versions are decided. The only tagging
guidance in the corpus is `devops/git-workflow.md:89-98`, which is scoped to versioning
**the standards repository itself**. **Release tagging for a product repo remains
uncovered** — a narrowed G1 survives.

**Verdict: G1 closes on branch naming, review and merge strategy; a residual gap remains
on release tagging.** Not stretched to fit.

**[REC]** for the residue: semver tags `vX.Y.Z` matching the CHANGELOG release header,
since `changelog-standard.md:91` already ties a breaking change to *"a major-version
bump"* — that clause presumes semver without stating it.

### 4.1 Branch protection to configure

**[STD]** `main` (`development-workflow.md:70-77`): PR required · ≥1 approval · all CI
checks pass · no direct pushes. Signed commits are *(recommended)* — **not binding**.
**[STD]** `develop` (`:79-83`): PR · ≥1 approval · CI green · **squash merge** · branch
up to date before merge.

**Decision needed [REC]:** `:48-56` mandates a two-branch `main` + `develop` GitFlow.
This repo currently has `dev`. For a solo-maintained public integration, a single
`main` with PR protection is defensible — but it **is** a deviation from a `required`
standard and should be a recorded decision, not drift. Either rename `dev`→`develop`
and adopt the model, or record the simplification.

---

## 5. The RFC 9457 × `ToolError` question

**Asked:** does "raise `ToolError` **and** carry an RFC 9457-shaped problem object as
its structured payload" satisfy B1-B8?

**Answer: not as literally stated — `ToolError` cannot carry a structured payload — and
even with the correct mechanism, one clause is unsatisfiable. This needs an ADR.**

### 5.1 Mechanism correction (verified against installed source)

```
ToolError.__init__(self, *args: object, log_level: int = 40) -> None
```
`ToolError` accepts **a message string and a log level. There is no structured-content
parameter.** So the intended ruling cannot be implemented via `raise ToolError` alone.

The mechanism that *does* carry structure:
```
ToolResult.__init__(content=None, structured_content=None, meta=None, is_error=False)
```
→ `return ToolResult(structured_content=<problem object>, is_error=True)` satisfies both
"client sees an error" and "payload is the problem object".

> **Verification caveat — important.** I verified this against **fastmcp 3.4.7** in the
> `fast-mcp-jira` virtualenv (Python 3.11). **The target is fastmcp 4.0.0b4**, which I
> did **not** verify; a beta may well change these signatures. Task **R2b** owns runtime
> verification against 4.0.0b4 and should re-confirm both signatures before the design
> is frozen. I am reporting what I ran, not what I assume.

### 5.2 Clause-by-clause

| Clause | Verdict |
|---|---|
| **B1** — `error-contract.md:204` *"All errors use the Problem Details object. **No custom envelopes.**"* | **SATISFIED.** The JSON-RPC/`ToolResult` wrapper is the *protocol's* envelope, not an application-invented one. The clause's target is ad-hoc app envelopes — `:242` enumerates them: *"No endpoint may return a bare `{"detail": "..."}`, `{"message": "..."}`, `{"error": {...}}`, or any other ad-hoc error shape."* MCP's transport framing is not in that class. |
| **B2** — `:66` seven fields elevated to required | **SATISFIED for 5 of 7; STRAINED for 2.** `type`, `title`, `detail`, `request_id`, `timestamp` map cleanly. **`status`** is defined at `:280` as *"HTTP status code (duplicated in body for convenience)"* — a tool error has no HTTP status; any value is synthesised. **`instance`** is defined at `:290` as *"URI of the request that generated the error"* — a tool call has no URI. |
| **B3** — `:44` *"All error responses MUST use the media type:"* `application/problem+json` | **VIOLATED — and unfixable.** An MCP tool error is not an HTTP response. It rides inside a `200 OK` JSON-RPC body whose content type is fixed by the MCP transport (`application/json` / `text/event-stream`). Setting `application/problem+json` would break protocol conformance. **This is a genuine, irreconcilable conflict, not a reading problem.** |
| **B4** — `:206` no stack traces; `error-handling.md:383` no raw third-party messages | **SATISFIABLE — but see §5.4, it is NOT the default.** |
| **B5** — `:210-211` stable relative `/problems/<slug>` URIs | **SATISFIED.** Independent of transport. |
| **B6** — typed exception hierarchy with `problem_type` + `title` | **SATISFIED.** Nothing prevents a `JobviteProblem` hierarchy mapped onto `ToolResult`. |
| **B7** — upstream 5xx→ServiceUnavailable, 4xx→ExternalService | **SATISFIED.** Pure mapping logic. |
| **B8** — never `raise HTTPException` | **SATISFIED trivially** — no FastAPI routes. |

### 5.3 Verdict

**The ruling is substantively right and should proceed — but it cannot be adopted as a
"clever reading", because B3 is violated in the letter and cannot be satisfied by any
implementation.** `status` and `instance` are additionally synthetic.

**This requires an ADR**, exactly as you anticipated. Suggested scope: *"RFC 9457 problem
semantics are carried in the MCP tool-result structured payload; the
`application/problem+json` media type (B3) is inapplicable to the MCP transport, and
`status` / `instance` are recorded as a synthesised HTTP-equivalent status and the tool
name respectively."* That ADR also cleanly covers the `instance` substitution already
flagged in STANDARDS.md §2/A1.

**[REC]** apply `application/problem+json` properly on the genuine HTTP surfaces that do
exist — the health endpoint and transport-level auth rejections — so B3 is honoured
everywhere it *can* be.

### 5.4 A trap worth more than the rest of this section

**FastMCP's `mask_error_details` defaults to `False`.** Verified in
`fastmcp/settings.py:268-282`:
> *"If True, error details from user-supplied functions (tool, resource, prompt) will be
> masked before being sent to clients. … If False (default), all error details will be
> included in responses"*

and the raise path at `fastmcp/server/server.py:1356-1358`:
```python
if self._mask_error_details:
    raise ToolError(f"Error calling tool {name!r}") from e
raise ToolError(f"Error calling tool {name!r}: {e}") from e
```

**Out of the box, the full text of any unhandled exception — including `httpx` internals
and anything a Jobvite error body contains — is returned to the client.** That directly
violates B4 (`error-contract.md:206`, `backend/error-handling.md:383`).

**[STD-derived, mandatory]** Construct the server with **`mask_error_details=True`** and
route every client-visible message through the typed problem hierarchy.
`fast-mcp-jira` does **not** set it (grep: absent) and is therefore leaking by default.

---

## 6. Do-not-copy list — `fast-mcp-jira` anti-patterns

Audited `repos/fast-mcp-jira/src/fast_mcp_jira/` (27 modules, 8,075 LOC). Each item is a
pattern a reviewer would fail against these standards.

| # | Pattern | Evidence | Breaks | Do instead |
|---|---|---|---|---|
| 1 | **`build_response(success, **data)` custom envelope** | `utils/validation.py:678-697` → `{"success": bool, **data}` | **B1** — `error-contract.md:204` *"No custom envelopes"*; the shape `{"success": false}` is named in the v1.0.0 migration table `:372` | RFC 9457 problem object (§5) |
| 2 | **`code="VALIDATION_ERROR"` string error codes** | `errors.py:47` and the module docstring `:7-12` (`VALIDATION_ERROR`, `RATE_LIMIT_ERROR`, `UNKNOWN_ERROR`) | **B5** — these are *literally* the left column of the v1.0.0→v2 mapping at `error-contract.md:390-404`; the repo is a textbook pre-migration implementation | `/problems/<slug>` URIs |
| 3 | **86 × `error=str(e)` returned to the caller** | e.g. `tools/issues.py:105,107,147` | **B4** — `error-handling.md:396` marks `BadRequestException(str(exc))` as **BAD**, *"Exposes library internals"* | Controlled messages; map upstream errors |
| 4 | **`mask_error_details` never set → defaults False** | absent from `src/`; default at `fastmcp/settings.py:282` | **B4** — raw exception text reaches clients | `mask_error_details=True` (§5.4) |
| 5 | **stdlib `logging`, zero `loguru`** | `auth.py:19`, `logging_config.py:26`, `services/jira_client.py:20`; 0 hits for loguru | **B44** — `reference-architecture.md:94` *"\| Logging \| **loguru** \| — \| std + prod agree; canonical \|"* | loguru |
| 6 | **`correlation_id_var`, no `X-Request-ID`** | `logging_config.py:33`; 0 hits for `request_id_var` / `X-Request-ID` | **B40** — `tool-calling.md:173-177` requires the triple **verbatim**: header `X-Request-ID`, field `request_id`, ContextVar `request_id_var` | Rename to the canonical triple |
| 7 | **No retry, no backoff, no circuit breaker** | 0 hits for `tenacity` / `circuitbreaker` across `src/` | **B34, B37** — `resilience.md:92-98`, `:159-161` | tenacity `^9` + circuitbreaker `^2`, composed timeout→retry→breaker (`:209`) |
| 8 | **Single scalar timeout, not per-phase** | `services/jira_client.py:218` `timeout=self.settings.request_timeout` (30.0) | **B32 partially** — `resilience.md:84-86` shows `httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0)`. *Fair note:* httpx applies a bare float to all phases, so this is not "relying on the SDK default" — it is under-specified, not absent | Explicit per-phase `httpx.Timeout` |
| 9 | **51 tools** (CLAUDE.md claims 47 — also stale) | `grep -c "@mcp.tool" tools/` → 51 | **B20** — `agent-guardrails.md:47-49` *"Do not expose a broad "kitchen-sink" toolbox; an unused tool is attack surface"* | Curate to the minimal Jobvite set |
| 10 | **158 `Field(` but only 18 `max_length`** | `grep` across `src/` | **B28** — `input-validation.md:64` *"All string fields MUST declare an explicit `max_length`"* | max_length on every string field |
| 11 | **No `ConfigDict(strict=True)` on tool argument models** | only `SettingsConfigDict` (`config.py:192`) and one `ConfigDict` import in `validation.py:19` | **B27** — `input-validation.md:37` *"All request models MUST enable strict mode"* | `model_config = ConfigDict(strict=True)` |
| 12 | **70 × `except Exception`** | across `src/` | **B4 risk** — `error-handling.md:502` *"Catch and swallow exceptions silently"* under **Don't**; `python.md:141` *"Be specific when possible"* | Narrow excepts; typed mapping |
| 13 | **No `.github/workflows/` at all** | directory does not exist | **B63-B72 entirely unmet** — no lint, type, test, audit, CodeQL, secret-scan, SBOM or licence gate | Build §1 |
| 14 | **3 test files for 8,075 LOC** | `tests/` = `test_auth.py`, `test_security.py`, `__init__.py` | **B56** — 80% floor (`testing.md:96`); no collection guard (**B58**), no `pytest-cov` dependency | §2 |
| 15 | **`requires-python = ">=3.11"`, ruff `target-version = "py311"`** | `pyproject.toml` | **B46** — `reference-architecture.md:83` `>=3.12`; ruling C1 | `>=3.12` / `py312` |
| 16 | **`line-length = 100`** | `pyproject.toml [tool.ruff]` | **B49** — `python.md:35` *"Maximum line length: **88 characters**"* | 88 |
| 17 | **`select = ["E","F","I","W"]` only** | `pyproject.toml [tool.ruff.lint]` | **B50/B51/B45** unenforced — no `N` (naming), `D` (docstrings), `ANN` (hints), `DTZ` (naive datetime), `T20` (print) | §2.2 rule set |
| 18 | **No mypy anywhere** | absent from deps and config | **B63** — `quality-gates.md:64` *"\| Backend Types \| mypy \| 0 errors \|"* | Add mypy + `[tool.mypy]` |
| 19 | **No `--strict-markers`, no coverage config** | `[tool.pytest.ini_options]` has only `asyncio_mode`, `testpaths` | **B55** — `testing.md:65-97` | §2.2 block |

**Two things `fast-mcp-jira` gets right** — worth copying: a real log-redaction helper
(`logging_config.py:39-79`, `[REDACTED]` on sensitive field names) which is the seed of
B88; and a committed `.env.example` (B91).

> **Scope note:** this is a standards-conformance audit, not a quality judgement of
> `fast-mcp-jira`. Several items (no CI, thin tests) may be deliberate for an internal
> tool. They are listed because the *new* repo is public, org-owned, and will be
> reviewed against the corpus.

---

## 7. Reviewer pass/fail checklist

One line each; markable without interpretation.

**Packaging & language**
- [ ] `requires-python = ">=3.12"`
- [ ] `uv.lock` committed
- [ ] CI installs with `uv sync --frozen`
- [ ] No unpinned/floating install anywhere in CI

**Lint / format / types**
- [ ] `uv run ruff check .` exits 0
- [ ] `uv run ruff format --check .` exits 0
- [ ] `[tool.ruff] line-length = 88`, `target-version = "py312"`
- [ ] ruff `select` includes `N`, `D`, `ANN`, `DTZ`, `T20`
- [ ] `mypy` is a dev dependency and `[tool.mypy]` exists
- [ ] `uv run mypy src` exits 0
- [ ] No `print()` in `src/`
- [ ] No `datetime.utcnow()`; `datetime.now(UTC)` only
- [ ] Every public function has type hints and a Google-style docstring

**Testing**
- [ ] `[tool.pytest.ini_options]` matches `backend/testing.md:56-78` (incl. `--strict-markers`)
- [ ] `[tool.coverage.report] fail_under = 80`; `branch = true`
- [ ] `tests/test_collection_guard.py` exists inside `testpaths`
- [ ] CI runs pytest with **no positional path argument**
- [ ] Required suites report **0 skipped**
- [ ] Adversarial/red-team cases exist and are wired to a **required** check
- [ ] A test asserts a malformed tool argument is rejected **before** any Jobvite call

**Tools**
- [ ] Every tool has a Pydantic-derived typed schema; no bare `str`/`dict`/`Any` params
- [ ] Every tool arg model sets `ConfigDict(strict=True)`
- [ ] Every string field declares `max_length`
- [ ] Tool result size is bounded and the max is **documented**
- [ ] Tool outputs are snake_case
- [ ] Every tool invocation is logged with `tool_name`, `request_id`, `result_status`, latency
- [ ] No candidate PII appears in any log line
- [ ] Destructive tools are default-deny / disabled unless explicitly enabled
- [ ] Tool set is curated, not generated wholesale from the Jobvite API

**Errors**
- [ ] No `build_response`-style `{"success": ...}` envelope anywhere
- [ ] Error payloads carry `type`, `title`, `status`, `detail`, `instance`, `request_id`, `timestamp`
- [ ] `type` values are relative `/problems/<slug>`
- [ ] No `str(e)` from a third-party library reaches a client
- [ ] Server is constructed with `mask_error_details=True`
- [ ] Jobvite 5xx → ServiceUnavailable; 4xx → ExternalService
- [ ] The RFC 9457 × MCP transport ADR exists (§5.3)

**Resilience**
- [ ] Explicit per-phase `httpx.Timeout` on the Jobvite client
- [ ] `tenacity` retry with exponential backoff **and jitter**, bounded
- [ ] Retries only on connect/timeout/429/5xx — never blanket
- [ ] One `circuitbreaker` per dependency; 4xx does not trip it
- [ ] Composition order timeout → retry → breaker

**Correlation & secrets**
- [ ] Header `X-Request-ID`, log field `request_id`, ContextVar `request_id_var` — verbatim
- [ ] Inbound `X-Request-ID` validated as UUID v4, replaced when invalid
- [ ] `loguru` is the logger; stdlib `logging` is not used
- [ ] `.gitignore` covers `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`, `secrets/`
- [ ] `.env.example` committed, placeholders only, no real secret
- [ ] Secrets are `SecretStr`, read via `.get_secret_value()`, never logged
- [ ] No hardcoded credential anywhere in `src/`, `tests/`, or docs
- [ ] **[REC]** `gitleaks`/`detect-secrets` pre-commit hook installed

**CI**
- [ ] All 13 jobs from §1.2 present
- [ ] Action versions match §1.5 exactly
- [ ] `pip-audit` blocking; unremediable advisories tracked, not silenced
- [ ] TruffleHog runs with `fetch-depth: 0`
- [ ] SBOM emits **both** CycloneDX and SPDX
- [ ] `pip-licenses` allow-list matches §1.6
- [ ] No required check is configured `skipped == success`

**Docs & repo**
- [ ] README has all 14 sections, exact headings, correct order
- [ ] README ≤500 lines
- [ ] Configuration table lists every env var with Name/Required/Default/Description
- [ ] README License section says **Apache-2.0** (SPDX) and links `LICENSE`. **A README saying MIT is the specific defect this line used to cause** - it said MIT until 2026-08-28 while the tree shipped Apache-2.0
- [ ] `LICENSE` reads `Copyright (c) 2026 evolv Consulting`
- [ ] At least one live CI badge
- [ ] `CHANGELOG.md` is Keep a Changelog 1.1.0 with `## [Unreleased]`
- [ ] Internal-only changes absent from CHANGELOG
- [ ] `CONTRIBUTING.md` exists or rules inlined under Contributing
- [ ] PR template present with the mandated sections
- [ ] `main` protected: PR + ≥1 approval + CI green + no direct pushes
- [ ] Commits follow `type(scope): description` with `Refs:`
- [ ] PR titles are semantic/conventional
- [ ] **[REC]** `SECURITY.md` present
- [ ] No real Jobvite tenant ID, client name, or internal hostname anywhere in the repo

**ADRs required at design freeze**
- [ ] C5 — Redis rate-limiter opt-out
- [ ] C6 — `ai/` domain binds by intent
- [ ] §5.3 — RFC 9457 carried in MCP tool-result payload

---

## What I could NOT verify

1. **fastmcp 4.0.0b4 behaviour.** Everything in §5.1/§5.4 was verified against **fastmcp
   3.4.7** on Python 3.11 in the `fast-mcp-jira` venv. The target is **4.0.0b4**, which I
   did not install or inspect. `ToolError`/`ToolResult` signatures and the
   `mask_error_details` default may differ in a beta. **R2b owns this**; re-confirm
   before design freeze. I report what I ran.
2. **Whether `mask_error_details=True` suppresses *explicitly raised* `ToolError`
   messages too.** The docstring says masking applies to *"error details from
   user-supplied functions"* and that *"Only error messages from explicitly raised
   ToolError … will be included"* — implying explicit ToolError text still passes. I read
   the setting and the raise path but did **not** execute a tool to observe the wire
   output.
3. **mypy strictness.** `[tool.mypy]` in §2.2 is **[REC]**, not cited. No standard
   specifies mypy flags; only that it must report 0 errors.
4. **Per-module coverage enforcement.** The §2.3 mapping is **[REC]** — the corpus's
   categories do not name MCP tool modules (gap G6). Only the 80% floor is cited.
5. **Release tagging.** Genuinely uncovered (§4). The `vX.Y.Z` suggestion is **[REC]**.
6. **`evaluation-testing.md` applicability.** Read it (closing an earlier honesty item).
   It governs **LLM output regression** — golden datasets (`:49`), LLM-as-judge (`:88`),
   metric thresholds. This server produces no model output, so most is **[N/A]**. The
   part that reaches us is `:126-134`: red-team cases live in the same suite and are
   **merge-gating**. I have **not** designed that suite's structure.
7. **`architecture/security.md` Audit Logging — now read cover to cover** (closing the
   second honesty item). `:553-639` is entirely a SQLAlchemy `audit_logs` table model and
   a DB-writing `AuditLogger`. **It adds no obligation beyond B17/B88** and is **[N/A]**
   for a stateless server. My earlier flag that it *might* reach B17/B88 is resolved: it
   does not.
8. **Whether `fast-mcp-jira`'s anti-patterns are deliberate.** I audited conformance, not
   intent. Some may be conscious trade-offs for an internal tool.
9. **The link-checker and Quickstart-execution jobs (§1.2 #12, #13).** The standard
   mandates the *outcome* (`readme-standard.md:67`, `:69`) but names no tool. Choice of
   implementation is unspecified and I did not pick one.
