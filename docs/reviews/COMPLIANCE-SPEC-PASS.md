# COMPLIANCE-SPEC pass — obligation-by-obligation against the built tree

**Pass:** COMPLIANCE-1 · **Date:** 2026-08-28 · **Type:** one-pass diff, not a review round
**Subject:** `docs/research/COMPLIANCE-SPEC.md` (661 lines), read in full
**Checked against:** the working tree at `299cf8b` (see the note on `ci.yml` line numbers below), `docs/plans/IMPLEMENTATION-PLAN.md`,
and `docs/DESIGN.md` read from the frozen object `git show 135c3ac:docs/DESIGN.md`.

## Why this pass exists

`COMPLIANCE-SPEC.md` specifies this repository's obligations and had never been read against the
repository. `DESIGN.md` was written without it and is frozen at revision 6. The plan declares it
unread at `IMPLEMENTATION-PLAN.md:1383`. Five plan review rounds compared the plan to the design;
comparing two documents to each other can confirm consistency and can never find a shared omission.

> **Note on `ci.yml` citations.** U15 landed its two commit-time gates into
> `.github/workflows/ci.yml` *while this pass was running*; the file went from 348 to 402 lines.
> **Every `ci.yml:` citation below was re-derived with `grep -n` against the post-U15 file** and
> re-checked for subject. All three MISSING CI findings (F-1, F-2, F-3) were re-run against the
> new file and still hold: `grep -nE 'cron|schedule|amannn|semantic-pull|lychee|link'` over the
> 402-line `ci.yml` returns nothing.

**Result: it was not a green.** 78 obligations enumerated, **7 MISSING**, **2 CONTRADICTED**,
**5 MET BY ACCIDENT**.

## Classification counts

| Class | Count |
|---|---|
| MET | 41 |
| MET BY ACCIDENT | 5 |
| SCHEDULED (met by a named unit, not yet built) | 6 |
| MISSING | 7 |
| CONTRADICTED | 2 |
| SUPERSEDED | 4 |
| N/A (still non-applicable) | 11 |
| UNVERIFIABLE from this machine | 2 |
| **Total** | **78** |

---

## §1.1 — Triggers and matrix

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 1.1.1 | Trigger on push to default branch | MET | `.github/workflows/ci.yml:33-34` |
| 1.1.2 | Trigger on every PR | MET | `.github/workflows/ci.yml:35` |
| 1.1.3 | **Weekly security schedule, `cron: '0 0 * * 0'`** (`ci-cd.md:455-456`) | **MISSING** | F-1 below |
| 1.1.4 | Python `3.12` | MET | `ci.yml:47` `PYTHON_VERSION: "3.12"`; `pyproject.toml:5` |
| 1.1.5 | `permissions: contents: read` (in the spec's copy-exactly block, `COMPLIANCE-SPEC.md:65-66`) | **MET BY ACCIDENT** | A-1 below |
| 1.1.6 | No version matrix ([REC]) | MET | `ci.yml` has no `strategy.matrix` |

## §1.2 — The 13-job table

| # | Job | Class | Evidence |
|---|---|---|---|
| 1 | `lint` — `ruff check .` | MET | `ci.yml:144-145` |
| 2 | `format` — `ruff format --check .` | MET | `ci.yml:147-148` |
| 3 | `types` — `mypy` | MET | `ci.yml:150-151`; `pyproject.toml:139-143` supplies `files` |
| 4 | `test` + coverage gate | SCHEDULED | pytest MET `ci.yml:157-169`; the coverage step is commented out at `ci.yml:296-297` and owned by U1 (`IMPLEMENTATION-PLAN.md:1106`) |
| 5 | `test` skip assertion, `SKIPPED == 0` | MET | `ci.yml:163-166` greps the output, because pytest exits 0 on a run full of skips |
| 6 | `pip-audit`, blocking, no threshold | SCHEDULED | commented at `ci.yml:279-280`, owned by U11 (`IMPLEMENTATION-PLAN.md:920-922`); ignore-table landed empty at `pyproject.toml:50-51` |
| 7 | `codeql` | MET | `ci.yml:386-402` |
| 8 | `secrets-scan`, TruffleHog, `fetch-depth: 0` | MET | `ci.yml:312-314` (depth), `ci.yml:378-381` (scan) |
| 9 | `sbom` ×2, CycloneDX + SPDX | MET | `ci.yml:357-362`, `ci.yml:364-369` |
| 10 | `license-scan` | SUPERSEDED | ADR-0015 (Accepted) — deny-list, not allow-list; `ci.yml:346-350` |
| 11 | **`pr-title` — `amannn/action-semantic-pull-request@v5`** | **MISSING** | F-2 below |
| 12 | **`links` — a link checker over `*.md`** | **MISSING** | F-3 below |
| 13 | `quickstart` — execute the README Quickstart | SCHEDULED | U13, `IMPLEMENTATION-PLAN.md:1000-1010`, `:1106` |

## §1.3 — Explicit non-applicability

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 1.3.* | All 13 N/A rows (Trivy, cosign, digest pinning, deploy gate, SLSA, Postgres/Redis, alembic, frontend, bundle, npm audit, Codecov, `[FEAT-XXX]`) | N/A — still holds | No Dockerfile, no DB, no frontend, no Node deps, no published artifact in the tree (`find` over the repo). SLSA remains live-on-PyPI-publish (gap G5), unanswered. |

## §1.4 — Branch protection

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 1.4.1 | A skipped required check must fail, not pass | **UNVERIFIABLE** | Needs the GitHub branch-protection API. The `github` MCP server failed to connect this session (`Authorization header is badly formatted`). Not asserted either way. |
| 1.4.2 | Path-filtered jobs are not direct required checks | MET | `ci.yml` declares no `paths:`/`paths-ignore:` filters at all, which is the [REC] route |
| 1.4.3 | `main` protected: PR + ≥1 approval + CI green + no direct pushes | **UNVERIFIABLE** | Same reason |

## §1.5 — Pinned action versions ("copy exactly")

| # | Pin required | In tree | Class |
|---|---|---|---|
| 1.5.1 | `actions/checkout@v6` (`ci-cd.md:81`) | `@v4` at `ci.yml:59,121,312,393` and `mirror.yml:28` | **CONTRADICTED** — C-1 |
| 1.5.2 | `astral-sh/setup-uv@v4` (`ci-cd.md:173`) | `@v5` at `ci.yml:124,317` | **CONTRADICTED** — C-1 |
| 1.5.3 | `actions/upload-artifact@v4` | absent | N/A — `anchore/sbom-action` uploads its own artifact via `artifact-name` |
| 1.5.4 | `github/codeql-action/init@v3` | `ci.yml:395` | MET |
| 1.5.5 | `github/codeql-action/autobuild@v3` | absent | N/A — Python is a non-compiled CodeQL language; `init`+`analyze` is the correct pair |
| 1.5.6 | `github/codeql-action/analyze@v3` | `ci.yml:400` | MET |
| 1.5.7 | `trufflesecurity/trufflehog@v3.88.0` | `ci.yml:379` | MET (known; was `@main`) |
| 1.5.8 | `anchore/sbom-action@v0` | `ci.yml:358,365` | MET |
| 1.5.9 | `amannn/action-semantic-pull-request@v5` | absent | **MISSING** — F-2 |

## §1.6 — Licence allow-list string (verbatim)

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 1.6.1 | `--allow-only 'MIT;Apache-2.0;…'` verbatim | SUPERSEDED | ADR-0015 (Accepted): fifteen spellings for six licences make `--allow-only` red on a clean tree. Deny-list at `ci.yml:346-350`. Known deviation. |

## §2 — `pyproject.toml`

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 2.1.1 | mypy is a dev dependency | MET | `pyproject.toml:37` |
| 2.1.2 | `[tool.mypy]` block exists | MET | `pyproject.toml:139-143`, `strict = true` |
| 2.2.1 | `requires-python = ">=3.12"` | MET | `pyproject.toml:5` |
| 2.2.2 | dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff` | MET | `pyproject.toml:33-36` |
| 2.2.3 | dev: `pip-audit` | SCHEDULED | U11 owns the step and the script |
| 2.2.4 | dev: `pip-licenses` | **MET BY ACCIDENT** | A-2 below |
| 2.2.5 | **ruff `line-length = 88`** (`python.md:35`) | **CONTRADICTED** | `pyproject.toml:124` sets `100` — C-2 |
| 2.2.6 | ruff `target-version = "py312"` | MET | `pyproject.toml:125` |
| 2.2.7 | ruff `select` includes `E`, `F`, `I` | MET | `pyproject.toml:134` |
| 2.2.8 | **ruff `select` includes `W`, `N`, `D`, `DTZ`, `T20`, `ANN`** (all marked `[STD]`) | **MISSING** | `pyproject.toml:134` = `["E","F","I","UP","B","S","ASYNC"]` — F-4 |
| 2.2.9 | ruff `select` includes `UP`, `B`, `S`, `ASYNC` ([REC]) | MET | `pyproject.toml:134` |
| 2.2.10 | `[tool.ruff.lint.pydocstyle] convention = "google"` | **MISSING** | F-4 (moot while `D` is unselected, but it is the same fix) |
| 2.2.11 | `per-file-ignores` for `tests/*` | MET | `pyproject.toml:136-137` (`S101`, plus `S603`/`S607` for the subprocess harnesses) |
| 2.2.12 | pytest `asyncio_mode`, loop scope, `testpaths`, `python_files`, `python_classes`, `python_functions` | **MET BY ACCIDENT** | A-3 below |
| 2.2.13 | pytest `addopts` incl. `--strict-markers` | MET | `pyproject.toml:70-76`; rationale at `:61-69`, `DESIGN.md:1193-1198` |
| 2.2.14 | pytest `markers` declared | MET | `pyproject.toml:78-84` |
| 2.2.15 | `filterwarnings = ["ignore::DeprecationWarning"]` | **MET BY ACCIDENT** | A-4 below |
| 2.2.16 | `[tool.coverage.run]` source / `branch = true` / omit | MET | `pyproject.toml:105-111` |
| 2.2.17 | `[tool.coverage.report]` exclude_lines / `fail_under = 80` / `show_missing` | MET | `pyproject.toml:113-121` |
| 2.3.1 | Per-module coverage targets | SUPERSEDED | ADR-0010 (Accepted), recorded at `pyproject.toml:90-104` |
| 2.4.1 | **`tests/test_collection_guard.py`** (`testing.md:138-141`, `quality-gates.md:76-81` API-03) | **MISSING** | Known as B58 — F-5 |

## §3 — Documentation obligations, per file

| # | File | Class | Evidence |
|---|---|---|---|
| 3.0.1 | `README.md` | SCHEDULED | Absent from the tree; deliberately withheld to U13 — `DESIGN.md:1483-1490`, `IMPLEMENTATION-PLAN.md:992-1010` |
| 3.0.2 | `CHANGELOG.md` | **MET BY ACCIDENT** | A-5 below |
| 3.0.3 | `LICENSE` | SUPERSEDED | Apache-2.0, not the spec's MIT (ruling G2). Superseded by D7/D13, `docs/DECISIONS.md:183-215` — a reasoned, Phil-authorised reversal. `NOTICE` present. |
| 3.0.4 | **`CONTRIBUTING.md` or inlined rules** (`readme-standard.md:56`) | **MISSING** | F-6 |
| 3.0.5 | `SECURITY.md` ([REC]) | MET | `SECURITY.md` present at root |
| 3.0.6 | `CODE_OF_CONDUCT.md` ([REC] optional) | N/A | Optional by the spec's own marking |
| 3.0.7 | `CODEOWNERS` ([REC]) | MISSING ([REC] only) | Noted in F-7, low severity |
| 3.0.8 | **`.github/pull_request_template.md`** (`development-workflow.md:199-242`; `quality-gates.md:50`) | **MISSING** | F-7 |
| 3.0.9 | `.env.example` | MET | `.env.example:1-90`; asserted by `tests/test_repo_hygiene.py:78-108` |
| 3.0.10 | `.gitignore` covers `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`, `secrets/` | MET | `.gitignore:13-16,32-33`; **guarded** by `tests/test_repo_hygiene.py:111-131`, which also forbids any negation but `!.env.example` |
| 3.1.1 | README's 14 sections, exact headings, exact order | SCHEDULED | `IMPLEMENTATION-PLAN.md:992-997` requires all fourteen with headings matching exactly |
| 3.1.2 | README ≤500 lines; every env var in the Configuration table | SCHEDULED | `IMPLEMENTATION-PLAN.md:995-996` (table derived from `.env.example`, not hand-maintained); `DESIGN.md:1507` |
| 3.1.3 | Live CI badge | SCHEDULED | `IMPLEMENTATION-PLAN.md:1021-1025` — legitimate from U0 onward |
| 3.2.1 | Keep a Changelog 1.1.0, `## [Unreleased]`, subsections, no internal-only entries | MET (see A-5 for the recording gap) | `CHANGELOG.md:5`, `:10` |

## §4 — Workflow, branching, tagging

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 4.1 | Branch naming `feature/BE-{ID}-…` | MET | Convention in use; `docs/DECISIONS.md` D14 |
| 4.2 | PR + ≥1 approval; squash merge | UNVERIFIABLE (settings) / decided | D14, ADR-0006 |
| 4.3 | Two-branch `main` + `develop` GitFlow | SUPERSEDED | **ADR-0006 (Accepted)** — single `main` |
| 4.4 | Release tagging `vX.Y.Z` semver ([REC], residual G1) | MET as a decision | `docs/DECISIONS.md` D15 |

## §5 — RFC 9457 × `ToolError`

| # | Obligation | Class | Evidence |
|---|---|---|---|
| 5.1 | Structure carried by `ToolResult(structured_content=…, is_error=True)`, not `ToolError` | MET (design) | `DESIGN.md:524`; ADR-0003 |
| 5.2 | B1–B8 clause set; B3 irreconcilable | MET | **ADR-0003 (Accepted)** — `application/problem+json` cannot be set on an MCP tool error |
| 5.3 | An ADR exists for the transport conflict | MET | `docs/adr/0003-problem-json-on-mcp-transport.md:3` |
| 5.4 | `mask_error_details=True` set explicitly at construction | SCHEDULED | `DESIGN.md:707`; `IMPLEMENTATION-PLAN.md:380` (U1); `docs/DECISIONS.md` D16 |

## §6 — Do-not-copy list (`fast-mcp-jira` anti-patterns)

Items 1–12 concern `src/`, which holds only `__init__.py`; they are **N/A until U1** and are not
credited as met. The seven that bite the tree **today**:

| # | Anti-pattern | Class | Evidence |
|---|---|---|---|
| 6.13 | No `.github/workflows/` | MET (avoided) | `ci.yml`, `mirror.yml` exist |
| 6.14 | Thin tests / no collection guard | PARTIAL | 5 test modules + `pytest-cov` present; **the collection guard is still absent** (2.4.1) |
| 6.15 | `requires-python = ">=3.11"` / `py311` | MET (avoided) | `pyproject.toml:5,125` |
| 6.16 | **`line-length = 100`** | **CONTRADICTED — the anti-pattern was copied** | `pyproject.toml:124` — C-2 |
| 6.17 | **`select` missing `N`,`D`,`ANN`,`DTZ`,`T20`** | **MISSING — partially copied** | `pyproject.toml:134` — F-4 |
| 6.18 | No mypy | MET (avoided) | `pyproject.toml:37,139-143` |
| 6.19 | No `--strict-markers`, no coverage config | MET (avoided) | `pyproject.toml:70-76`, `:105-121` |

## §7 — Reviewer checklist (rollup)

The checklist restates §§1-6 and adds no new obligations. Every item that names an artifact
existing today is covered above. Items naming `src/` behaviour (Tools, Errors, Resilience,
Correlation) are vacuous against an empty package and are **not** credited. Three items are worth
calling out explicitly:

| # | Checklist item | Class | Evidence |
|---|---|---|---|
| 7.1 | ADRs required at design freeze: C5, C6, §5.3 | MET | ADR-0002, ADR-0005, ADR-0003 — all **Accepted** |
| 7.2 | `[REC]` `gitleaks`/`detect-secrets` pre-commit hook installed | MET, **uncommitted** | `.pre-commit-config.yaml` exists and configures `Yelp/detect-secrets@v1.5.0`, but `git ls-files` returns nothing for it — it is untracked in-flight U15 work. Not a finding against this pass; flagged so U15 does not land without it. |
| 7.3 | All 13 jobs from §1.2 present | **NO** | 9 present, 2 scheduled, **2 missing** (F-2, F-3) |

---

# Findings

Every fix below is **my suggestion, to verify** — not an instruction. I edited nothing.

## F-1 — CI has no weekly security schedule (MISSING)

`COMPLIANCE-SPEC.md:45` marks this `[STD]` against `devops/ci-cd.md:455-456`
(subject-verified: that line reads `- cron: '0 0 * * 0'  # Weekly on Sunday`). `ci.yml:32-36`
triggers on push, `pull_request` and `workflow_dispatch` only.

**Positive control:** `grep -rn 'cron'` over `*.md`/`*.yml`/`*.toml` (excluding
`COMPLIANCE-SPEC.md`) returned **zero** hits; the same sweep for `trufflehog` returned
`ci.yml:17` and `ci.yml:326`. The zero is a real absence, not a bad path.

**Why it matters, concretely:** CodeQL and TruffleHog only ever run on a change. A repository
that is not being changed is never re-scanned, so an advisory published against a pinned beta
dependency after the last merge is invisible until someone happens to push. This repo pins a
deliberate beta stack, which is exactly the case the schedule exists for.

**Suggested fix (verify):** add to `ci.yml:32-36`
```yaml
  schedule:
    - cron: '0 0 * * 0'   # weekly security sweep - ci-cd.md:455-456
```
Consider gating the `test` job's cost with `if: github.event_name != 'schedule'` if only the
security jobs are wanted on the sweep.

## F-2 — No semantic PR-title check, though the project decided to have one (MISSING)

`COMPLIANCE-SPEC.md:83` (job 11) and `:143` (pin) require
`amannn/action-semantic-pull-request@v5`, cited to `ci-cd.md:305-321` and ruling C4.
Subject-verified: `ci-cd.md:305` reads `uses: amannn/action-semantic-pull-request@v5`.

**This is the sharpest kind of gap: the decision was taken and never implemented.**
`docs/DECISIONS.md:18` records **D9 — "Commit `type(scope): description` + `Refs:`; semantic PR
titles | Settled | Orchestrator ruling"**. Nothing enforces the second half.

**Positive control:** `grep -rn 'amannn'` and `grep -rn 'semantic-pull-request'` across the repo
(excluding the spec) each returned zero; the control grep for `trufflehog` hit twice.

**Suggested fix (verify):** add a job to `ci.yml`
```yaml
  pr-title:
    name: Semantic PR title
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions: { pull-requests: read }
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        env: { GITHUB_TOKEN: "${{ secrets.GITHUB_TOKEN }}" }
```
Do **not** also add the `[FEAT-XXX]` check — ruling C4 (`COMPLIANCE-SPEC.md:117`) excludes it as
irreconcilable with this job.

## F-3 — No link checker in CI, and the standard makes it merge-blocking (MISSING)

`COMPLIANCE-SPEC.md:84` (job 12) cites `readme-standard.md:69`. Subject-verified, that line reads
*"**Links are checked**: a link checker MUST run in CI; a broken link blocks merge."*

**Positive control:** `grep -rn 'lychee|linkchecker|markdown-link-check|link-check'` across the
repo returned zero hits; control grep hit twice.

**Why it matters here more than in most repos.** This repository is *made of* cross-references:
`docs/` holds 8 research documents, 16 ADRs, 24 review documents and a 1,543-line plan, and the
design's own coupling gates exist because citations here decay. A dangling
`docs/adr/00NN-….md` link is exactly the failure the corpus already measured on this project
(`docs/reviews/CITATION-RANGE-AUDIT.md`). Nothing currently catches one.

**Suggested fix (verify):** a `links` job running `lycheeverse/lychee-action` over `**/*.md`.
Note the spec leaves the tool unspecified (`COMPLIANCE-SPEC.md:659-661` lists this as something it
did *not* pick), so the choice is open — but the outcome is mandated, and the job is absent.
Scope it to relative links first if external-link flakiness is a concern; a flaky required check
trains people to ignore it, which is the failure shape `ci.yml:268-277` already reasons about.

## F-4 — ruff enforces none of the five rule families the spec marks `[STD]` (MISSING)

`pyproject.toml:134` reads `select = ["E", "F", "I", "UP", "B", "S", "ASYNC"]`.

`COMPLIANCE-SPEC.md:205-218` marks six of the missing families **`[STD]`**, each with a citation:

| Family | Spec line | Standard clause it mechanically enforces |
|---|---|---|
| `W` | `:207` | PEP 8 — `python.md:28` |
| `N` | `:209` | naming table — `python.md:62-72` |
| `D` | `:210` | PEP 257 docstrings — `python.md:29` |
| `DTZ` | `:215` | no `datetime.utcnow()` — `python.md:227` |
| `T20` | `:216` | *"no print statements"* — `observability.md:642` |
| `ANN` | `:217` | type hints on all functions — `python.md:76` |

`COMPLIANCE-SPEC.md:514` lists this as **do-not-copy item 17**, the `fast-mcp-jira` anti-pattern
`select = ["E","F","I","W"]` — and the tree reproduces its shape.

**This is a now-or-never item, not a cosmetic one.** `src/` holds only `__init__.py`. Turning
`ANN`, `D` and `N` on against an empty package costs nothing. Turning them on at U8, against a
dozen written modules, is a large mechanical diff that whoever hits it will be tempted to narrow
with `per-file-ignores`. The corpus's own checklist items *"No `print()` in `src/`"*,
*"No `datetime.utcnow()`"* and *"Every public function has type hints and a Google-style
docstring"* (`COMPLIANCE-SPEC.md:546-548`) have **no mechanical enforcement at all** today, and
`DESIGN.md` is frozen without them.

**Suggested fix (verify):**
```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "D", "UP", "B", "S", "ASYNC", "DTZ", "T20", "ANN"]
ignore = ["D203", "D213"]           # mutually exclusive with D211/D212

[tool.ruff.lint.pydocstyle]
convention = "google"               # python.md:97

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S603", "S607", "D103", "ANN"]
```
Run `uv run ruff check .` before landing — the existing test modules will need docstrings and
annotations, which is the point. If any family genuinely does not fit, that is an ADR naming the
family and the reason, not a silent omission.

## F-5 — The collection guard is still absent (MISSING; known as B58)

Restated for completeness, not re-derived. `COMPLIANCE-SPEC.md:297-305` (§2.4),
`backend/testing.md:138-141`, `quality-gates.md:76-81` (API-03) — subject-verified, that clause
reads *"If the guard is absent or if any test file lives outside the configured roots, the CI
backend test job MUST fail."*

`tests/` contains `conftest.py`, `test_file_type_gate.py`, `test_fixture_path.py`,
`test_manifest.py`, `test_markers.py`, `test_repo_hygiene.py` — no guard.
`grep -rn 'collection' tests/*.py` hits only `tests/__init__.py:4` and `test_markers.py:1,69`,
which are about *marker* collection behaviour, not discovery completeness.

**The point this pass exists to make.** B58 is named in **five places across four project
documents**, all subject-verified:

| Document | Line | What it says |
|---|---|---|
| `COMPLIANCE-SPEC.md` | `:297-305` (§2.4) | *"Test-discovery guard (required, easy to forget)"* |
| `STANDARDS.md` | `:434-435` | *"**B58.** A collection-guard meta-test exists inside a configured `testpaths` root and passes in CI."* |
| `STANDARDS.md` | `:998` | summary row — *"Collection guard \| meta-test inside a `testpaths` root, required in CI"* |
| `CONFORMANCE-B1-B106.md` | `:255` | **UNADDRESSED** — *"this is a required-check breach, not a nice-to-have"* |
| `CONFORMANCE-RESWEEP.md` | `:194` | **STILL-OPEN** — *"The mandated guard is still absent"* |

It reached neither the frozen design, the plan, nor the tree. **The project's own conformance
corpus named the obligation twice, escalated it to a required-check breach, and it did not
propagate.** That is the sharpest instance of the failure this pass is auditing — and it is a
stronger claim than "nobody read `COMPLIANCE-SPEC.md`", because two documents that *were* read
also carry it. This is now task #17.

**Do not dismiss it by pointing at the `--collect-only` step.** `CONFORMANCE-B1-B106.md:255`
already anticipated exactly that move and answered it: the credentialed-collect step
(`ci.yml:187-201`, `DESIGN.md:885-888`) proves the *excluded* suite still **imports**. The guard
proves no `test_*.py` is **unreachable from `testpaths` at all**. Different failure modes — *"The
standard's failure mode is a test file nobody runs; §8's failure mode is a test file that rots.
Both are real; only the second is designed for."* The corpus also notes the compounding: §8
deliberately maintains **two** suites with different selection, which is the configuration in
which an orphaned third file is least visible.

**Suggested fix (verify):** `tests/test_collection_guard.py` walking the repo for `test_*.py`
outside `testpaths` and failing on any hit — plus, per the standard's *"must itself live inside a
configured root so that its own absence fails collection"*, a mutation arm in
`scripts/check-u0-test-controls.sh` that deletes the guard and requires the suite to go red.

## F-6 — No `CONTRIBUTING.md`, and the fallback is not scheduled either (MISSING)

`COMPLIANCE-SPEC.md:316` marks this `[STD] REQUIRED *or* inlined`, citing `readme-standard.md:56`.
Subject-verified, `:56` reads *"12. **Contributing** — link to `CONTRIBUTING.md` or equivalent.
Repos without that file must inline the contribution rules under this heading."*

**Positive control:** `find . -iname 'CONTRIBUTING*'` returned nothing; the identical `find` for
`SECURITY*` returned `./SECURITY.md`. Real absence.
`grep -n -iE 'CONTRIBUTING'` over `DESIGN.md` and `IMPLEMENTATION-PLAN.md` returned **zero**.

**The subtle half.** U13 does schedule the README's fourteen headings
(`IMPLEMENTATION-PLAN.md:993-994`), so a `## Contributing` *heading* will exist. But the standard
requires the *rules* to be inlined when the file is absent, and neither U13 nor any other unit
mentions contribution rules. The obligation would be silently discharged by an empty heading.

**Suggested fix (verify):** either add a short `CONTRIBUTING.md` now (branch naming from
`development-workflow.md:58-68`, `type(scope): description` + `Refs:` from ruling C3, squash
merge, ≥1 approval) — or amend U13's brief to say the Contributing section **inlines the rules**,
not merely that the heading exists. The first is cheaper and is not blocked on U1-U12.

## F-7 — No PR template; `quality-gates.md` gates on one (MISSING)

`COMPLIANCE-SPEC.md:320` marks the **content** `[STD] REQUIRED` (body mandated verbatim at
`development-workflow.md:199-242` — subject-verified, `:199` reads `### Pull Request Template` and
`:201-210` is the mandated markdown body) with the **path** `[REC]`. `quality-gates.md:50` gates
Gate 2 on *"Completed PR template"* — subject-verified.

**Positive control:** `find . -iname '*pull_request_template*'` returned nothing;
`.github/` contains only `workflows/ci.yml` and `workflows/mirror.yml`. The control `find` for
`SECURITY*` hit. Zero mentions in the design or the plan.

`CODEOWNERS` is likewise absent, but the spec marks it `[REC] / NOT REQUIRED`
(`COMPLIANCE-SPEC.md:319`), so it is noted, not raised.

**Suggested fix (verify):** add `.github/pull_request_template.md` carrying the body from
`development-workflow.md:201-242`. It is a copy, it blocks nothing, and it is the artifact
`quality-gates.md:50` checks for. Add `.github/CODEOWNERS` at the same time if a review-assignment
mechanism is wanted — it is how GitHub actually enforces `development-workflow.md:73`'s ≥1 approval.

## C-1 — Two pinned action versions do not match §1.5's "copy exactly" (CONTRADICTED)

| Required | Spec line | Standard | In tree |
|---|---|---|---|
| `actions/checkout@v6` | `COMPLIANCE-SPEC.md:135` | `ci-cd.md:81` (subject-verified: `- uses: actions/checkout@v6`) | `@v4` — `ci.yml:59,121,312,393`; `mirror.yml:28` |
| `astral-sh/setup-uv@v4` | `COMPLIANCE-SPEC.md:136` | `ci-cd.md:173` (subject-verified: `uses: astral-sh/setup-uv@v4`) | `@v5` — `ci.yml:124,317` |

These deviate in **opposite directions** — `checkout` is behind the standard, `setup-uv` is ahead
of it — which is the signature of pins chosen from habit rather than from `§1.5`. Nothing in the
design, the plan, the ADRs or `U0-REPORT.md` records either choice: `grep` for `checkout@` and
`setup-uv` over `docs/` produced no rationale.

`ci.yml:371-377` shows the project already reasons carefully about action pinning (TruffleHog was
moved off `@main` citing `devops/log.md:31`). That reasoning simply never reached these two.

**Suggested fix (verify):** bump `actions/checkout@v4` → `@v6` in all five places, and decide
`setup-uv` deliberately: either drop to `@v4` to match `ci-cd.md:173`, or keep `@v5` and record a
one-paragraph note saying the standard's pin is stale and `@v5` is the deliberate forward
deviation. Either is defensible; the current unrecorded state is not. **Verify `checkout@v6`
exists and the workflow still runs before landing** — I did not execute the workflow.

## C-2 — `line-length = 100`: the do-not-copy list's own item 16 was copied (CONTRADICTED)

`pyproject.toml:124` reads `line-length = 100`.

- `COMPLIANCE-SPEC.md:199` marks `line-length = 88` with the citation `python.md:35`.
- Subject-verified at source: `backend/python.md:35` reads
  *"- Maximum line length: **88 characters** (`ruff format` default)"*.
- `COMPLIANCE-SPEC.md:513` lists **do-not-copy item 16 — `line-length = 100`** as a
  `fast-mcp-jira` anti-pattern breaching **B49**, with *"Do instead: 88"*.

**Nothing records the deviation.** `grep -rn 'line-length|line length|100 char|88 char'` over
`DESIGN.md`, `IMPLEMENTATION-PLAN.md`, `docs/adr/*.md`, `docs/DECISIONS.md` and
`docs/worklogs/U0-REPORT.md` returned **zero hits**. Positive control: the same grep style for
`strict-markers` over the design and plan returns 5 and 2 hits respectively. So this is a real
absence — the value was set and never argued.

**Why this one is more than style.** `ruff format` reflows to `line-length`. Setting 100 now and
correcting it to 88 later reformats every file written between here and then, which turns a
one-line config fix into a whole-tree diff that buries real changes in review. `src/` is empty
today; the cost of fixing it is currently zero and rises monotonically.

**The design is frozen**, so if 100 is the intended answer this is an **ADR**, not an edit to
`DESIGN.md`. Note that `DESIGN.md` does not actually specify a line length either way
(the grep above covered it), so an ADR here does not contradict the frozen text — it fills a gap
the freeze left open.

**Suggested fix (verify):** set `pyproject.toml:124` to `line-length = 88`, run
`uv run ruff format .` and `uv run ruff check .`, and land the reflow as its own commit. If 88 is
genuinely wrong for this repo, file **ADR-0016: ruff line length is 100, not the standard's 88**
with the reason — and expect it to answer why B49 and do-not-copy item 16 do not apply.

---

# MET BY ACCIDENT — the dangerous set

These five obligations are **satisfied today**, and **nothing anywhere records them as
obligations**. No test, comment, ADR, design clause or plan line names them. Each would regress
silently: a reviewer deleting or "tidying" any of them would see a green build and no objection.

## A-1 — `permissions: contents: read`

`ci.yml:42-44` sets the least-privilege default token scope. It appears verbatim in the spec's
copy-exactly block at `COMPLIANCE-SPEC.md:65-66`.
**Recording check:** `grep -rn 'contents: read|least privilege|least-privilege'` over `DESIGN.md`,
`IMPLEMENTATION-PLAN.md`, `docs/adr/*.md` and `U0-REPORT.md` → **zero hits**. (Control:
`strict-markers` over the same files → 7 hits.)
**Regression shape:** a future job needing write access gets `permissions: write-all` pasted at the
workflow level, silently widening the token for CodeQL and TruffleHog too. Nothing fails.
**Suggested fix (verify):** a one-line comment above `ci.yml:42` — *"workflow-level least
privilege; widen per-job, never here"* — and keep the two per-job `security-events: write` grants
at `ci.yml:307-308` and `:390-391` as the pattern.

## A-2 — `pip-licenses` is not a dev dependency; the gate works only via `--with`

`COMPLIANCE-SPEC.md:194` lists `pip-licenses` in `[dependency-groups] dev`. `pyproject.toml:32-38`
does **not** include it. The licence gate passes because `ci.yml:348` invokes
`uv run --frozen --with pip-licenses pip-licenses`.
**Recording check:** `docs/adr/0015-licence-gate-is-a-deny-list.md:78` says *"`pip-licenses` is a dev dependency, so the gate is
CI-only"* — which is **not what the manifest says**. The ADR describes a dependency that is absent.
**Regression shape:** two ways. A reader following ADR-0015 runs `uv run pip-licenses` locally and
gets "command not found", concluding the gate is broken. Or `--with` resolves `pip-licenses`
**unpinned at each run**, outside `uv.lock` — so the tool auditing the frozen resolve is itself
not frozen, which is precisely the property `ci.yml:133-142` builds two separate assertions to
guarantee for everything else.
**Suggested fix (verify):** add `"pip-licenses"` to `pyproject.toml:32-38`, `uv lock`, and drop
`--with` from `ci.yml:348` so the gate runs from the frozen resolve. Then ADR-0015:78 becomes true
as written. (Alternatively correct ADR-0015:78 — but pinning the auditor is the better half.)

## A-3 — The pytest discovery keys are verbatim from the standard, and nothing says so

`pyproject.toml:56-59` sets `testpaths`, `python_files`, `python_classes`, `python_functions`
exactly as `COMPLIANCE-SPEC.md:239-242` requires from `backend/testing.md:56-78`.
**Recording check:** `grep -rn 'python_classes|python_functions|testing.md:56'` over the design,
plan, ADRs and worklog → **zero hits**. The surrounding comments at `pyproject.toml:61-76` explain
`--strict-markers` and the `-m` selection in detail and say nothing about these four keys.
**Regression shape:** this is the load-bearing one. `testpaths = ["tests"]` is the root that
**F-5's collection guard is supposed to guard**. If someone adds `tests_integration/` and widens
`testpaths`, or narrows it to `tests/unit`, no guard and no note objects — and the missing guard
(F-5) is exactly what would have caught it. The two gaps compound.
**Suggested fix (verify):** land F-5's guard, and add a comment at `pyproject.toml:56` naming
`backend/testing.md:56-78` and `quality-gates.md:76-81` as the source, so the next editor knows
`testpaths` is a gated value rather than a preference.

## A-4 — `filterwarnings = ["ignore::DeprecationWarning"]`

`pyproject.toml:86-88`, required verbatim by `COMPLIANCE-SPEC.md:255`.
**Recording check:** `grep -rn 'filterwarnings|DeprecationWarning'` over the design, plan, ADRs and
worklog → **zero hits**.
**Regression shape:** worth a second look rather than just a comment. This repo deliberately pins
a **beta** stack (`fastmcp==4.0.0b4`, `mcp==2.1.1`, per `pyproject.toml:15-19` and ADR-0001), and
ADR-0001's stated posture is that beta defects are *"characterised precisely, reproduced minimally,
and reported upstream"*. A blanket `ignore::DeprecationWarning` suppresses the single loudest
signal a beta dependency emits when it is about to break — which is the opposite of that posture.
The spec mandates the line for a general backend; nothing has asked whether it fits **this** repo.
**Suggested fix (verify):** keep the line to stay conformant, but add a comment recording the
tension, or narrow it to third-party modules and let first-party deprecations surface, e.g.
`"ignore::DeprecationWarning:fastmcp.*"`. Either way, record the decision — right now it is
inherited, not chosen.

## A-5 — `CHANGELOG.md` conformance is unrecorded and ungated

`CHANGELOG.md:5` cites Keep a Changelog 1.1.0 and `:10` carries `## [Unreleased]`, satisfying
`COMPLIANCE-SPEC.md:354-358` / `changelog-standard.md:42,84`.
**Recording check:** `grep -rn 'Keep a Changelog|changelog-standard'` over `DESIGN.md`,
`IMPLEMENTATION-PLAN.md`, `docs/adr/*.md` and `U0-REPORT.md` → **zero hits**. `changelog.d/`
exists with a `README.md` but no unit owns the changelog obligation.
**Regression shape:** §3.2 carries clauses no human reliably remembers — *"internal-only changes
MUST NOT appear"* (`:94`), *"dates are publication dates, backdating forbidden"* (`:93`),
*"Security entries carry a CVE where one exists"* (`:92`). The current `[Unreleased]` block is
largely **design and research activity**, which is arguably the internal-only class `:94`
excludes. Nothing checks, and no unit owns it.
**Suggested fix (verify):** assign the changelog obligation to a unit (U13 is the natural home
alongside the other documentation obligations) and, if it is worth gating, add a test asserting
`## [Unreleased]` exists and that release headings parse as `## [X.Y.Z] - YYYY-MM-DD`. Also worth
a ruling on whether the present design-activity entries survive `:94`.

---

# What I read in full, and what I did not

**Read in full:**
- `docs/research/COMPLIANCE-SPEC.md` — all 661 lines, every section including §§1.2, 1.5, 1.6,
  3.1, 5, 6, 7 and the "What I could NOT verify" appendix.
- `pyproject.toml` (143 lines), `.github/workflows/ci.yml` (348 lines), `.gitignore`,
  `.env.example`, `.pre-commit-config.yaml`, `NOTICE`, `tests/` file listing.
- `docs/DECISIONS.md:1-40` (the decision table) and `:180-215` (D7/D13, the licence reversal).
- `docs/adr/0003-problem-json-on-mcp-transport.md` header; the **Status** line of all 15 ADRs.
- `IMPLEMENTATION-PLAN.md:992-1025` (U13) and `:1106-1107` (file ownership).
- Standards read at the cited lines and subject-verified: `backend/python.md:28-40`,
  `documentation/readme-standard.md:43-99`, `devops/ci-cd.md` (the `uses:`/`cron` lines and
  `:452-458`), `devops/quality-gates.md:46-54` and `:74-82`,
  `devops/development-workflow.md:196-212`, `devops/environments.md:610-624`.

**NOT read in full — stated so this pass is not over-credited:**
- `docs/DESIGN.md` (1,994 lines). I read it **by targeted grep** against each obligation
  (README, Quickstart, PR title, link checker, cron, `.gitignore`, `permissions`,
  `mask_error_details`, line length, ruff `select`, licence) plus the hit context. A design clause
  that discusses an obligation in wording none of those greps matched would have been missed.
- `docs/plans/IMPLEMENTATION-PLAN.md` (1,543 lines). Same method; §U13 read in full.
- `docs/research/STANDARDS.md`, the B1-B106 conformance corpus, and the 24 documents in
  `docs/reviews/`. I relied on the brief's statement of what B58 says rather than re-deriving it.
- The full standards corpus. I read only the clauses `COMPLIANCE-SPEC.md` cites, and verified those.

**Could not verify at all:**
- **Branch protection settings** (§1.4.1, §1.4.3, and the checklist's *"No required check is
  configured `skipped == success`"*). These live in GitHub repository settings, not in the tree.
  The `github` MCP server failed to connect this session. Unasserted in both directions.
- **Whether any of the never-executed CI jobs actually pass.** `ci.yml:16-19` states plainly that
  codeql, trufflehog and the anchore SBOM actions have never run. I did not run them either. This
  pass checks that they are *present and correctly pinned*, which is a strictly weaker claim.
- **`src/` obligations** (§6 items 1-12, and the Tools / Errors / Resilience / Correlation blocks
  of §7). `src/fast_mcp_jobvite/` holds only `__init__.py`. Those are vacuously unviolated and are
  **not** credited as met anywhere above.
