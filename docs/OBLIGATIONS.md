# Obligations map: B-number to the artifact that discharges it

**Owner:** CONF-6 · **Seeded:** 2026-08-28 · **Checked by:** `docs/reviews/check-obligations.py`

**ABSENT rows last READ against their clauses: 2026-08-29.** The checker verifies that a
MAPPED row's anchor still contains its subject. **An ABSENT row has no anchor, so nothing
checks it and its prose decays silently** - which is how BASH-2 sat stale in three ways it
named itself, and how B79 below claimed the 500-line cap was "named nowhere" while a test
enforced it. A green from the checker is not evidence about these rows. **Re-read them when a
unit lands that could discharge one**, and record the date here.

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
that discharges it, and **a subject string that must appear in that artifact**. The script asserts
the subject, not merely that a path resolves: an anchor that resolves to *some* line is exactly how
a citation rots, and `docs/reviews/CITATION-RANGE-AUDIT.md` records that failure happening in this
corpus already.

**Anchors carry NO line number, and that is deliberate.** They used to. In a single day, four
separate repointing operations were needed - a `ci.yml` insertion moved two anchors, a docstring
reflow moved a third, and deleting two stale comment lines moved eight - and **every one was
mechanical, carried no information, and risked retyping a number just read.** A line number pins
nothing the subject does not already pin, and it is the only part of an anchor that drifts.

**The subject must therefore be UNIQUE in the file, and the checker refuses ambiguity rather than
resolving it to the first hit** - a first hit is not evidence of anything. If a subject appears
twice, quote more of the line. That is a strictly stronger property than "appears at line N", which
any duplicate would also have satisfied.

`file:line` is still parsed, for a subject that genuinely cannot be made unique. Nothing uses it
today, and a row that reverts to one is a row that reintroduces the drift.

**The CLAUSE column is a different half, and it is weaker.** The artifact column says what
discharges an obligation; the clause column says why the obligation is real. Until
`docs/reviews/check-clause-citations.py`, nothing verified it at all - and it cites `file:line` into
a **sibling checkout this project neither controls nor pins**, so a standards edit silently repoints
every row at once.

That script resolves all 22 and **exits 2, never 0, when the standards repo is absent** - it cannot
be a CI gate, because CI does not have that repo. It is listed in `CONTRIBUTING.md` under the
measurements a human runs, beside the PID-1 harness, which has exactly the same shape.

**It proves each citation RESOLVES. It does not prove the line says what the row claims**, and those
are different things - nine wrong-subject citations have been found here, four of them inside the ADR
documenting that defect class.

**A hand check of all 22 found two weak anchors.** Neither is wrong about its obligation; both point
at text that is not normative:

- **B53** cites `architecture/security.md:418`, which is `# .env.example (commit this)` - a comment
  inside an example block.
- **B102** cites `devops/development-workflow.md:192`, which is a line of an **ASCII box diagram**.
  A diagram is not a requirement.

They are recorded rather than repointed because choosing a better line is a judgement about someone
else's document, and a citation moved without reading its neighbourhood is how ranges contract.

**Two controls guard the scheme.** `_c_duplicate_subject` proves ambiguity is caught. And
`_n_move_subject` is a NEGATIVE control - shifting a cited file by five lines must leave the map
**green**. Without it the scheme's central claim would be untested, and every other control would
still pass against a checker that had quietly gone back to matching line numbers. It replaced two
controls that line-free anchors had made unfirable, and which reported themselves as not firing.

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
| B16 | ABSENT | - | - | `ai/tool-calling.md:55-57` | **Its first half is now false and the row stays ABSENT for its SECOND half.** Three tools ship names and descriptions (`search_jobs`, `search_candidates`, `get_candidate`), so "no tool descriptions exist yet" expired when U5 landed. What is still absent is the clause's actual requirement: they are **reviewed like prompts**, and no unit, gate or checklist schedules that review. Re-read when U10 or U12 adds a tool |
| B49 | MET | `pyproject.toml` | `line-length = 88` | `backend/python.md:35` | The code half. The comment/docstring half is B49b below, met in the same commit that swept it |
| B49b | MET | `pyproject.toml` | `max-doc-length = 72` | `backend/python.md:36` | `W505`, enabled in the same commit as the 1608-line sweep so the gate was never knowingly red. W505 is INERT without this setting, so this row anchors on it, not on the `W505` select entry |
| B50 | MET | `pyproject.toml` | `convention = "google"` | `backend/python.md:97` | Type-hint half is `ANN` at `pyproject.toml:158` |
| B51 | MET | `pyproject.toml` | `no datetime.utcnow` | `backend/python.md:227` | The `DTZ` rule family. This row is the reason the file exists: deleting it must now break something that names B51 |
| B52 | MET | `pyproject.toml` | `pep8-naming` | `backend/python.md:64-71` | The `N` rule family |
| B53 | MET | `.env.example` | `JOBVITE_API_KEY=` | `architecture/security.md:418` | Committed template, names only, every value empty |
| B58 | MET | `tests/test_collection_guard.py` | `test_every_test_file_is_reachable_from_testpaths` | `backend/testing.md:138` | The only obligation in this map whose fix already carried its own B-number |
| B59 | MET | `.github/workflows/ci.yml` | `uv run --frozen pytest 2>&1` | `backend/testing.md:166` | No positional path, so `testpaths` stays authoritative |
| B61 | ABSENT | - | - | `documentation/agentic-coding-standard.md:346` | Test names are descriptive sentences, not `test_{what}_{when}_{expected}`; the convention is stated nowhere |
| B73 | SUPERSEDED | `docs/research/COMPLIANCE-SPEC.md` | `by ruling C4` | `devops/quality-gates.md:49` | Ruling C4 excludes the `[FEAT-XXX]` check as irreconcilable with semantic titles |
| B74 | ABSENT | - | - | `documentation/agentic-coding-standard.md:171` | No TODO in code and no CI check. Inherits B73's prefix problem and nothing connects them |
| B75 | MET | `.github/workflows/ci.yml` | `name: Capability drift report` | `documentation/agentic-coding-standard.md:173` | **Was three commented-out step blocks with no ADR.** U11 enabled the advisory audit; U1 enabled the capability-drift diff and the coverage floors. `grep -n '^\s*#\s*-\s*name:'` over `ci.yml` now returns NOTHING, so the obligation is discharged by each owning unit enabling its own block rather than by anyone deleting them. **Residue: `ERA` is still unselected in ruff**, so nothing stops a NEW commented-out block - the rule is met by the tree's state, not by a gate |
| B76 | ABSENT | - | - | `documentation/agentic-coding-standard.md:66` | The protected-path rule is stated nowhere outside the audit corpus |
| B77 | MET | `tests/test_readme.py` | `test_the_required_sections_are_present_in_the_prescribed_order` | `documentation/readme-standard.md:43` | Sections present in order, enforced by a test rather than by review |
| B78 | SUPERSEDED | `docs/plans/IMPLEMENTATION-PLAN.md` | `headings matching exactly` | `documentation/readme-standard.md:50` | U13 checks the table against `.env.example` rather than hand-keeping it |
| B79 | MET | `tests/test_readme.py` | `LENGTH_CAP = 500` | `documentation/readme-standard.md:64` | The cap is enforced by a test, not by review. **The row said "named nowhere" and was stale**: U13 named it when it landed, and an ABSENT row has no anchor for `check-obligations.py` to check, so nothing could notice. Both of its citing sites said `:63`, which is BLANK; the cap is at `:64`, which this row had right and the test had wrong |
| B81 | SUPERSEDED | `docs/plans/IMPLEMENTATION-PLAN.md` | `A CI status badge` | `documentation/readme-standard.md:70` | Deferred until CI exists, with the deferral distinguished from an excuse |
| B82 | MET | `.github/workflows/ci.yml` | `Relative links resolve` | `documentation/readme-standard.md:69` | Uncommitted when seeded |
| B84 | ABSENT | - | - | `documentation/changelog-standard.md:91` | No breaking-change discipline anywhere. B5's type-URI stability half depends on it |
| B89 | MET | `README.md` | `## License` | `documentation/readme-standard.md:57` | SPDX id and a link to LICENSE, in the required section |
| B96 | ABSENT | - | - | `devops/environments.md:636` | No rotation policy or runbook, in a server whose reason to exist is holding third-party API keys. **RE-VERIFIED 2026-08-29 and still absent**: the clause sets QUARTERLY rotation for third-party API keys with a vendor-breach trigger, and `grep -ic rotat docs/CREDENTIAL-CHECKLIST.md` returns **0** - the one document that would carry it does not use the word. The sharpest of the ABSENT rows and the least likely to be discharged by a unit, because no unit owns it |
| B98 | SUPERSEDED | `docs/adr/0006-single-main-branch.md` | `squash merge` | `devops/development-workflow.md:73` | Prose half only. The wiring is a GitHub settings object no file here can hold |
| B100 | MET | `.github/pull_request_template.md` | `Completed PR template` | `devops/quality-gates.md:50` | Untracked when seeded. Closing this does NOT close B101 |
| B101 | MET | `docs/CODE-REVIEW-CHECKLIST.md` | `Reviewers must verify` | `devops/development-workflow.md:248` | The PR template's checklist is the AUTHOR's self-check (B100); this is the reviewer's. Kept out of the template deliberately. The rows of the standard with no subject here are listed with reasons rather than dropped |
| B102 | MET | `CONTRIBUTING.md` | `Squash merge` | `devops/development-workflow.md:192` | Untracked when seeded. Enforcement is branch protection, which is out of tree |
| B103 | MET | `README.md` | `# fast-mcp-jobvite` | `documentation/readme-standard.md:32-35` | README.md exists at the repository top level |
| B104 | MET | `CONTRIBUTING.md` | `readme-standard.md:56` | `documentation/readme-standard.md:56` | Untracked when seeded |
| B105 | SUPERSEDED | `SECURITY.md` | `security@evolvconsulting.com` | `documentation/readme-standard.md:58` | Team-lead ruling: `:58` allows "people **or team aliases**" and this alias is published, so no person need be named in a public repo. CONF-6 had called this ABSENT; the clause's own wording overrides that. Residual, small: the alias is published for vulnerability REPORTING, and `:58` asks for the owner responsible for review and release. U13 should carry it under the Maintainers heading in that second sense |
| BASH-1 | SUPERSEDED | `docs/adr/0023-harnesses-drop-e-from-strict-mode.md` | `the clause admits no exception` | `devops/bash.md:36-41` | `bash.md:36-41` mandates `set -euo pipefail` and admits no exception. ADR-0023 records the `-e` half as a DEVIATION for harnesses, not as compliance: `out=$(cmd); rc=$?` exits before `rc` is read, so a control cannot tell a fired mutation from an unfired one, and `restore` never runs. Both arms measured by `docs/reviews/probe-set-e-vs-harness.sh`. **NO COUNT IS CARRIED HERE, AND THE ONE THAT WAS IS WHY.** The cell said "all 20 `scripts/*.sh`" beside its own instruction to derive rather than retype, and by 2026-09-02 the population was 39 - so the number was stale AND the word "all" was false. DERIVE IT: list tracked `scripts/*.sh`, and count those whose source contains `set -uo pipefail`. **THE DEVIATION IS NOT UNIVERSAL, which the old cell asserted and the measurement refutes.** Two members are outside it, both correctly and for different reasons: `scripts/check-pytest-bounded.sh` runs the FULL `set -euo pipefail` - it reads no `rc=$?`, so ADR-0023's reason does not apply to it and it is COMPLIANT rather than deviating; and `scripts/lib/harness-result.sh` is SOURCED, not executed, so it carries neither a shebang nor a `set` - imposing shell options on every caller is what a sourced file must not do. A future member with neither, and neither reason, is the finding this cell exists to make visible. A pipe cannot appear in this cell, which is why the commands are described instead of pasted |
| BASH-2 | MET | `.pre-commit-config.yaml` | `koalaman/shellcheck-precommit` | `devops/bash.md:734` | "All scripts MUST pass ShellCheck with zero warnings." Wired at `--severity=warning`, the threshold the clause's own CI form (`:741`) and pre-commit block (`:767`) specify for themselves, and the one `ci.yml` already passes to actionlint's embedded shellcheck. **Measured before wiring, with the hook's own image**: 22 tracked `.sh` files, ZERO output, exit 0. POSITIVE CONTROL, because a linter reporting nothing looks identical to one that did not run - at the DEFAULT severity the same command over the same files reports 17 findings, all `note`. **The population is by FILE, not by directory**: `types: [shell]` is pre-commit's identify pass, so it covers four probes under `docs/reviews/` and excludes `ci.yml`; measuring `scripts/*.sh` (18) is wrong in both directions. Left ABSENT until it was green - it was 4 warnings that morning - because `ci.yml` runs `pre-commit run --all-files`, so a red hook is red CI. CEILING: `language: docker_image`, so it needs a Docker daemon at every commit; that is what the clause prescribes verbatim |

## Adding a row

1. Read the clause at its source in `evolv-coder-standards/standards/`, not a digest of it.
2. Find the artifact and take the line number from `grep -n` or a `Read`, never counted off a
   `sed -n X,Yp` window.
3. Pick a subject that is **distinctive on that line** and at least six characters. The script
   rejects a subject too short to be evidence.
4. Run the script. If it is green on a row you have just invented, break the artifact deliberately
   and confirm it goes red before believing the green.

## A clause of `bash.md` that is GUIDANCE, recorded rather than dropped

**`devops/bash.md:799` - ">100 lines of logic - rewrite in Python or Go". NEARLY EVERY
TRACKED `scripts/*.sh` EXCEEDS 100 LINES, and the count is not carried here: derive it
with `git ls-files -- 'scripts/*.sh'` and `grep -c ''` per file. It read "13 of the 15
... the largest is 469" until 2026-09-02, when all three figures were stale at once -
the population was 39, the breach count 38, and the largest 598 lines. THE "13 of 15"
FRAMING ALSO IMPLIED TWO MEMBERS SIT UNDER THE GUIDELINE; there is ONE, and it is
`scripts/check-suite-floor.sh` at 66 lines.**

It gets no row above, and the class check is what settled that: the table's vocabulary is MET /
ABSENT / CONTRADICTED / SUPERSEDED, and every one of those asserts something about an *obligation*.
This is not one. `:795` heads the section **"When NOT to Use Bash"**, `:798` opens *"Bash is the
wrong tool when:"*, and `:807` labels the whole block **Guideline** - in a document that writes
*"Every script MUST begin with"* at `:36` when it means MUST. So there is no deviation and no ADR.

**The substance is still weighed, because "it is only guidance" is not a reason to stop reading.**
The section's other bullets are complex data structures, JSON/YAML processing, cross-platform
behaviour, concurrency and HTTP. These harnesses do none of that: they mutate one file, run pytest,
and read an exit code, which is what shell is actually good at.

**One bullet does bite.** *"Error handling matters - `set -e` has surprising edge cases; use a
language with try/catch."* BASH-1 is exactly such an edge case, and it is measured, not hypothetical:
`docs/reviews/probe-set-e-vs-harness.sh` shows `-e` aborting before `rc=$?` is read and leaving the
mutation in the working tree. That is the guidance being right, and it is recorded here rather than
argued away.

**The decision is not to rewrite.** 3374 lines of amputation-verified harness carry every other gate
in this repository, and replacing them to satisfy a guideline would put those gates at risk in order
to comply with something that does not require compliance. If a harness is ever rewritten for its own
reasons, this is a reason to write it in Python.

