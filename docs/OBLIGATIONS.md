# Obligations map: B-number to the artifact that discharges it

**Owner:** CONF-6 · **Seeded:** 2026-08-28 · **Checked by:** `docs/reviews/check-obligations.py`

## Why this file exists

CONF-6 measured how obligations from the conformance corpus reached the repository, and found the
rule to be: **an obligation propagated if and only if a document somebody actually executed against
happened to name it.** `DESIGN.md` named B1-B47 and those landed. `COMPLIANCE-SPEC.md` named a
scattered set including five style rows and those landed. `CONFORMANCE-RESWEEP.md` named all 59 and
was executed against by nobody, so its unique contribution - the repository-process tail, B48-B106 -
reached nothing at all.

The corollary is the part this file fixes. Of the twelve obligations CONF-6 found **met**, exactly
**one** - B58 - has its B-number recorded anywhere near the artifact that satisfies it. The other
nine are **met by accident**: correct today because somebody independently followed the standard,
with nothing in the tree that would notice a regression. Delete `"DTZ",` from `pyproject.toml` and
B51 silently reverts; no check anywhere mentions B51.

So this file is the executable version of that record. Each row names an obligation, the artifact
that discharges it at `file:line`, and **a subject string that must appear on that line**. The
script asserts the third, not merely the second: an anchor that resolves to *some* line is exactly
how a citation rots, and `docs/reviews/CITATION-RANGE-AUDIT.md` records that failure happening in
this corpus already.

```
python3 docs/reviews/check-obligations.py            # verify every mapping
python3 docs/reviews/check-obligations.py --controls # prove each check can go red
```

## What a green here does and does not mean

**It means:** the evidence CONF-6 recorded still points at what CONF-6 said it pointed at.

**It does not mean the repository is conformant.** Judging whether a clause is satisfied is a human
reading a standard against an artifact; `docs/reviews/CONF-6-PROPAGATION-AUDIT.md` is that reading,
and this script only checks that the reading has not rotted underneath itself. A green is worth
exactly the quality of the row it re-checks.

## Scope, stated so the gaps are not mistaken for coverage

Seeded from CONF-6's population: **the 28 open obligations cited by number in neither `DESIGN.md`
nor the implementation plan.** It is **not** the whole corpus. B1-B47 are largely cited in
`DESIGN.md` already and were not re-verified by CONF-6, so mapping them here would import claims
nobody checked. **Rows are added when somebody verifies them, never in bulk.**

Four rows - B82, B100, B102, B104 - point at files that were **untracked or uncommitted** when this
map was seeded. If that work is abandoned those four obligations silently revert to absent, and this
script going red is the correct signal rather than a nuisance: that is the exact regression class
the map exists to make visible.

## Classes

| Class | Meaning | Artifact column |
|---|---|---|
| `MET` | Discharged by an artifact in the tree | required |
| `CONTRADICTED` | The tree does the opposite; needs an ADR | required - cite the offending line |
| `SUPERSEDED` | A numbered ADR or a recorded ruling overrides or defers it | required - cite the record |
| `ABSENT` | Not met, not scheduled | must be `-` |

## The map

| B | Class | Artifact | Subject | Standard clause | Note |
|---|---|---|---|---|---|
| B16 | ABSENT | - | - | `ai/tool-calling.md:55-57` | No tool descriptions exist yet and no unit schedules their review |
| B49 | MET | `pyproject.toml:159` | `line-length = 88` | `backend/python.md:35` | Code half only. The 72-character comment/docstring half of `python.md:36` is unenforced - see task B49b |
| B50 | MET | `pyproject.toml:188` | `convention = "google"` | `backend/python.md:97` | Type-hint half is `ANN` at `pyproject.toml:158` |
| B51 | MET | `pyproject.toml:181` | `no datetime.utcnow` | `backend/python.md:227` | The `DTZ` rule family. This row is the reason the file exists: deleting it must now break something that names B51 |
| B52 | MET | `pyproject.toml:175` | `pep8-naming` | `backend/python.md:64-71` | The `N` rule family |
| B53 | MET | `.env.example:16` | `JOBVITE_API_KEY=` | `architecture/security.md:418` | Committed template, names only, every value empty |
| B58 | MET | `tests/test_collection_guard.py:173` | `test_every_test_file_is_reachable_from_testpaths` | `backend/testing.md:138` | The only obligation in this map whose fix already carried its own B-number |
| B59 | MET | `.github/workflows/ci.yml:257` | `uv run --frozen pytest 2>&1` | `backend/testing.md:166` | No positional path, so `testpaths` stays authoritative |
| B61 | ABSENT | - | - | `documentation/agentic-coding-standard.md:346` | Test names are descriptive sentences, not `test_{what}_{when}_{expected}`; the convention is stated nowhere |
| B73 | SUPERSEDED | `docs/research/COMPLIANCE-SPEC.md:117` | `by ruling C4` | `devops/quality-gates.md:49` | Ruling C4 excludes the `[FEAT-XXX]` check as irreconcilable with semantic titles |
| B74 | ABSENT | - | - | `documentation/agentic-coding-standard.md:171` | No TODO in code and no CI check. Inherits B73's prefix problem and nothing connects them |
| B75 | MET | `.github/workflows/ci.yml:509` | `name: Capability drift report` | `documentation/agentic-coding-standard.md:173` | **Was three commented-out step blocks with no ADR.** U11 enabled the advisory audit; U1 enabled the capability-drift diff and the coverage floors. `grep -n '^\s*#\s*-\s*name:'` over `ci.yml` now returns NOTHING, so the obligation is discharged by each owning unit enabling its own block rather than by anyone deleting them. **Residue: `ERA` is still unselected in ruff**, so nothing stops a NEW commented-out block - the rule is met by the tree's state, not by a gate |
| B76 | ABSENT | - | - | `documentation/agentic-coding-standard.md:66` | The protected-path rule is stated nowhere outside the audit corpus |
| B77 | SUPERSEDED | `docs/DESIGN.md:1484` | `not written yet, deliberately` | `documentation/readme-standard.md:43` | Deferred with a recorded reason; scheduled as U13 |
| B78 | SUPERSEDED | `docs/plans/IMPLEMENTATION-PLAN.md:1308` | `headings matching exactly` | `documentation/readme-standard.md:50` | U13 checks the table against `.env.example` rather than hand-keeping it |
| B79 | ABSENT | - | - | `documentation/readme-standard.md:64` | The 500-line cap is named nowhere, and U13 loads the README heavily |
| B81 | SUPERSEDED | `docs/plans/IMPLEMENTATION-PLAN.md:1353` | `A CI status badge` | `documentation/readme-standard.md:70` | Deferred until CI exists, with the deferral distinguished from an excuse |
| B82 | MET | `.github/workflows/ci.yml:679` | `Relative links resolve` | `documentation/readme-standard.md:69` | Uncommitted when seeded |
| B84 | ABSENT | - | - | `documentation/changelog-standard.md:91` | No breaking-change discipline anywhere. B5's type-URI stability half depends on it |
| B89 | SUPERSEDED | `pyproject.toml:6` | `license = "Apache-2.0"` | `documentation/readme-standard.md:57` | Substance settled; only the README section is deferred with B77 |
| B96 | ABSENT | - | - | `devops/environments.md:636` | No rotation policy or runbook, in a server whose reason to exist is holding third-party API keys |
| B98 | SUPERSEDED | `docs/adr/0006-single-main-branch.md:24` | `squash merge` | `devops/development-workflow.md:73` | Prose half only. The wiring is a GitHub settings object no file here can hold |
| B100 | MET | `.github/pull_request_template.md:3` | `Completed PR template` | `devops/quality-gates.md:50` | Untracked when seeded. Closing this does NOT close B101 |
| B101 | MET | `docs/CODE-REVIEW-CHECKLIST.md:3` | `Reviewers must verify` | `devops/development-workflow.md:248` | The PR template's checklist is the AUTHOR's self-check (B100); this is the reviewer's. Kept out of the template deliberately. The rows of the standard with no subject here are listed with reasons rather than dropped |
| B102 | MET | `CONTRIBUTING.md:64` | `Squash merge` | `devops/development-workflow.md:192` | Untracked when seeded. Enforcement is branch protection, which is out of tree |
| B103 | SUPERSEDED | `docs/DESIGN.md:1484` | `not written yet, deliberately` | `documentation/readme-standard.md:32-35` | Same disposition as B77 |
| B104 | MET | `CONTRIBUTING.md:3` | `readme-standard.md:56` | `documentation/readme-standard.md:56` | Untracked when seeded |
| B105 | SUPERSEDED | `SECURITY.md:9` | `security@evolvconsulting.com` | `documentation/readme-standard.md:58` | Team-lead ruling: `:58` allows "people **or team aliases**" and this alias is published, so no person need be named in a public repo. CONF-6 had called this ABSENT; the clause's own wording overrides that. Residual, small: the alias is published for vulnerability REPORTING, and `:58` asks for the owner responsible for review and release. U13 should carry it under the Maintainers heading in that second sense |

## Adding a row

1. Read the clause at its source in `evolv-coder-standards/standards/`, not a digest of it.
2. Find the artifact and take the line number from `grep -n` or a `Read`, never counted off a
   `sed -n X,Yp` window.
3. Pick a subject that is **distinctive on that line** and at least six characters. The script
   rejects a subject too short to be evidence.
4. Run the script. If it is green on a row you have just invented, break the artifact deliberately
   and confirm it goes red before believing the green.
