# CONF-6: did the conformance corpus propagate, or was B58 alone?

**Task:** CONF-6 · **Author:** conf6-propagation-audit · **Date:** 2026-08-28
**Subject:** `docs/reviews/CONFORMANCE-RESWEEP.md` against `docs/DESIGN.md` (FROZEN),
`docs/plans/IMPLEMENTATION-PLAN.md`, and the repository **as it stands at `2d2e1a3` plus the
uncommitted working tree**.

**Answer up front: B58 was not alone, and the failure is structural rather than incidental.**
The obligations that failed to propagate are not a random 28 of 40 - they are, almost exactly,
**the repository-process tail of the corpus (B48-B106)**, and they failed for a mechanical reason
visible in the artifacts: *the only obligations that reached a work unit were the ones a document
somebody actually executed against happened to name.*

> **Method note.** Every verdict below was taken from `grep -n` or a `Read` and then
> subject-verified - the line re-read to confirm it contains what it is cited for. Every absence
> carries a **positive control**: the same search re-run in a form known to hit. Verdicts are
> against the tree, and where an artifact is **untracked or uncommitted** the row says so, because
> another agent owns `.github/` and `CONTRIBUTING.md` right now and those files could still change.
>
> Line numbers here were re-derived at HEAD. Several of the resweep's own anchors have drifted since
> revision 4 - its `DESIGN.md:1114-1117` for the README deferral is now **`DESIGN.md:1533-1534`**.

---

## 0. Two corrections to the brief, both material

### 0.1 The population is 28, not 23. The missing five came from a column offset.

`CONFORMANCE-RESWEEP.md` §3's table has **seven** columns -
`B | Requires | Clause (re-verified) | Was | Now | Category | Evidence` (`CONFORMANCE-RESWEEP.md:142`).
The current verdict is column **5** (`Now`). Column **6** is `Category`, whose vocabulary is
`DEFECT / NOT-YET-BUILT / DEFERRED-WITH-REASON / STILL-OPEN` (`CONFORMANCE-RESWEEP.md:138`).

Parsing column 5, and splitting on `|` **not preceded by a backslash** (six rows - B7, B30, B47,
B56, B96, B97 - quote markdown tables inside a cell and carry escaped pipes), gives:

| Verdict | Count |
|---|---|
| SATISFIED (including 2 written "SATISFIED (design)") | **16** |
| PARTIAL | **18** |
| UNADDRESSED | **22** |
| NOT-APPLICABLE | **3** |
| **Total** | **59** |

**This reproduces the document's own §1 counts exactly** (`CONFORMANCE-RESWEEP.md:56-60`:
16 / 18 / 22 / 3). An independent parse landing on the document's stated numbers is the positive
control that it read the right column.

The brief's parse (15 / 16 / 20 / **5 DEFERRED** / 3) has no DEFERRED verdict to find - the verdict
vocabulary does not contain one. Those five are `DEFERRED-WITH-REASON` rows of column 6 leaking into
the verdict tally: **B73, B77, B81, B89, B103**. (B78 is the sixth `DEFERRED-WITH-REASON` row; the
brief kept it, which is why five went missing and not six.)

So **open = 40**, not 36, and **uncited by number in both `DESIGN.md` and the plan = 28**, not 23.
The five extras are all in this audit's table.

> Not a scoring quibble. Four of the five extras (B77, B81, B89, B103) are the README cluster, and a
> parse that drops them makes the README gap look four rows smaller than it is.

### 0.2 B49 is only half fixed.

Commit `2d2e1a3` set `line-length = 88` (`pyproject.toml:134`) and the tree is clean under it:
`uv run --frozen ruff check .` → *All checks passed!*, exit 0. The single 113-character line, at
`tests/test_file_type_gate.py:45`, carries a justified `# noqa: E501` on a PDF byte literal.

**But `backend/python.md:36` also fixes comments and docstrings at 72 characters, and nothing
enforces that.** `[tool.ruff.lint.pycodestyle] max-doc-length` is not set, so `W505` cannot fire even
though `"W"` is selected (`pyproject.toml:145`). Measured over the tracked `src/`, `tests/` and
`scripts/` Python: **68 comment lines exceed 72 characters.**

Treat B49 as a worked example of **a CONTRADICTED obligation whose fix closed the half that had a
lint rule and left the half that needed a configuration line** - the same shape as everything else
in this report.

---

## 1. The 28-row classification

Class key: **MET** = met in substance · **ABSENT** = not met, not scheduled ·
**CONTRADICTED** = the tree or a frozen document does the opposite · **SUPERSEDED** = a numbered ADR
or a recorded decision overrides it.

*"Recorded as this obligation?"* asks whether **anything in the tree ties the artifact back to the
obligation**. A "no" means it is **met by accident**: correct today, with nothing that would notice
a regression.

| B | Obligation (short) | Class | Evidence `file:line` | Recorded as this obligation? |
|---|---|---|---|---|
| **B16** | Tool name + description reviewed like prompts; no secrets | **ABSENT** | No tool descriptions exist yet (`src/fast_mcp_jobvite/` holds only `__init__.py`); zero mentions in the plan - U5 (`IMPLEMENTATION-PLAN.md:555`), U8 (`:726`) and U14 (`:1028`) all specify schemas and never descriptions. Control: `grep -in 'manifest'` on the plan returns 10 hits, so file and search are live | No |
| **B49** | Line length 88; comments/docstrings 72 | **MET (code half) / ABSENT (doc half)** | `pyproject.toml:134` `line-length = 88`; `ruff check .` exit 0. **`max-doc-length` unset**; 68 comment lines >72 | Comment at `pyproject.toml:129-133` cites `python.md:35` and `COMPLIANCE-SPEC.md:513` - **not B49** |
| **B50** | Type hints on public functions; Google/NumPy docstrings | **MET** | `pyproject.toml:151` `"D"` (pydocstyle), `:158` `"ANN"`, `:163` `convention = "google"  # python.md:97`; gated in CI at `.github/workflows/ci.yml:163` | Standard cited inline; **not B50** |
| **B51** | `datetime.now(UTC)`; `utcnow()` forbidden | **MET** | `pyproject.toml:156` `"DTZ",  # naive datetimes [STD] python.md:227, no datetime.utcnow` | Standard cited inline; **not B51** |
| **B52** | Naming per `python.md:64-71` | **MET** | `pyproject.toml:150` `"N",  # pep8-naming [STD] python.md:62-72` | Standard cited inline; **not B52** |
| **B53** | `SecretStr` + committed `.env.example`, names only | **MET** | `.env.example` is tracked (`git ls-files`); every credential value is empty, with the reason at `.env.example:5-6` | Design covers the code half (`DESIGN.md:247-248`); the file half is tied to nothing |
| **B58** | Collection-guard meta-test in a configured root, passing in CI | **MET** | `tests/test_collection_guard.py:139` `test_every_test_file_is_reachable_from_testpaths`; `testpaths = ["tests"]` at `pyproject.toml:62`; runs in CI at `ci.yml:175-187`. Verified by running it: **3 passed** | **Yes** - built as B58 (commit `35de193`). The only row in this table whose fix carries its B-number |
| **B59** | CI runs pytest with no positional path | **MET** | `.github/workflows/ci.yml:178` `out=$(uv run --frozen pytest 2>&1)` - no path argument, so `testpaths` stays authoritative | No |
| **B61** | Test names `test_{what}_{when}_{expected}` | **ABSENT** | Names are descriptive sentences, not the three-part form: `tests/test_file_type_gate.py:236` `test_the_gate_does_NOT_stop_confidential_prose_in_markdown`; `tests/test_collection_guard.py:118` `test_the_guard_can_see_anything_at_all`. The convention is stated nowhere | No |
| **B73** | PR titles carry a traceability ID | **SUPERSEDED** | Ruling **C4**, `docs/research/COMPLIANCE-SPEC.md:117` - *"`[FEAT-XXX]` PR-title check … **[N/A] by ruling C4** — conflicts irreconcilably with job 11"* (subject-verified). Semantic titles enforced instead by `.github/workflows/pr-title.yml` (**untracked**) | Yes, by ruling number. Note `docs/adr/README.md:38-48`'s non-conformance entry is written about `threat-modeling.md:146`, **not** about B73 |
| **B74** | No `TODO` without a ticket reference | **ABSENT** | No `TODO` in any code file and no CI check. Control: `git grep -n '\bTODO\b'` returns 5 hits, all research prose, so the search works. Inherits B73's prefix problem and nothing connects the two | No |
| **B75** | No commented-out code blocks | **CONTRADICTED** | Three commented-out step blocks at `.github/workflows/ci.yml:297-298, 307-308, 314-315`, verified against `git show HEAD:` so this is committed state. Ruff's `ERA` rule is **not selected** - control: `"ANN"` matches twice in the same file, `ERA` zero times. No ADR | No |
| **B76** | `.github/workflows/` is a protected path agents do not auto-modify | **ABSENT** | Zero hits for `Always Protected` / `auto-modify` / `protected path` outside the audit corpus itself. Controls: the same grep hits `docs/research/STANDARDS.md:523` and `docs/reviews/CONFORMANCE-B1-B106.md:278`, so pattern and walk are live; `grep -c 'the'` returns 905 / 760 / 27 on `DESIGN.md` / the plan / `CONTRIBUTING.md`, so those paths resolve | No |
| **B77** | README has all fourteen sections, exact headings | **SUPERSEDED (deferred, reason recorded)** | No root `README.md` (`git ls-files` shows `docs/README.md` only). Reason at `DESIGN.md:1533-1534` - *"**The README is not written yet, deliberately**"*. Scheduled as **U13** (`IMPLEMENTATION-PLAN.md:992-994`) | Yes - via §10.1 and U13, by subject not by number |
| **B78** | Configuration table lists every env var | **SUPERSEDED (deferred with B77)** | U13 makes the table *"**checked against `.env.example`**"* (`IMPLEMENTATION-PLAN.md:996`), removing the hand-kept enumeration the resweep found wrong | Yes, by subject |
| **B79** | README ≤ 500 lines; overflow to `docs/` | **ABSENT** | Zero hits for `500 lines` / `Length cap` in `DESIGN.md`, the plan or `CONTRIBUTING.md`. Control: those three return 905 / 760 / 27 hits for `the`. U13 loads the README with 14 sections, a 15-variable table and six behaviours and never mentions the cap | No |
| **B81** | Badges point at live sources | **SUPERSEDED (deferred, reason recorded)** | `IMPLEMENTATION-PLAN.md:1020-1023` - *"**A CI status badge cannot be live until CI exists**"*, with `readme-standard.md:70` cited and the deferral distinguished from an excuse | Yes, by subject |
| **B82** | A link checker runs in CI; a broken link blocks merge | **MET (uncommitted)** | `.github/workflows/ci.yml:454-470`, job `links`, `lycheeverse/lychee-action@v2`, `fail: true`. **Working tree only** - `git diff --stat` shows `ci.yml` modified and this job is that diff | Yes - `ci.yml:432` quotes `readme-standard.md:69` verbatim. Standard cited, not B82 |
| **B84** | `BREAKING:` prefix + migration note + major bump | **ABSENT** | Zero hits for `BREAKING` in `CHANGELOG.md`, `changelog.d/README.md`, `DESIGN.md`, the plan or `CONTRIBUTING.md`. Control: `grep -c 'Added' changelog.d/README.md` = 2, so file and search resolve. B5's `type`-URI stability half still has no enforcement anywhere | No |
| **B89** | README License section names an SPDX id | **SUPERSEDED (deferred with B77)** | `LICENSE` and `NOTICE` tracked; `pyproject.toml:6-7` declares `license = "Apache-2.0"` and `license-files`. Only the README **section** is outstanding | Yes, by subject |
| **B96** | Third-party API keys rotate quarterly; enforced, with a runbook | **ABSENT** | No rotation policy or runbook. Control: `grep -rni 'rotat'` hits `docs/research/JOBVITE-API.md:279`, `:331` and `STANDARDS.md:1294-1299`, so the search is live - **every hit is research prose or the corpus itself, none is a policy**. `SECURITY.md` and `docs/CREDENTIAL-CHECKLIST.md` both hit on `credential`; neither mentions rotation | No |
| **B98** | `main` protected: PR, ≥1 approval, CI green, no direct pushes | **MET in prose / ABSENT in wiring** | Stated at `CONTRIBUTING.md:63` (**untracked**) and `docs/adr/0006-single-main-branch.md:24`. **Nothing configures branch protection**, and no artifact in this repo can - it is a GitHub settings object | Yes - ADR-0006 |
| **B100** | A PR template with the mandated sections | **MET (untracked)** | `.github/pull_request_template.md`, body copied from `development-workflow.md:201-241`. **Untracked** - `git status` shows `?? .github/pull_request_template.md` | Yes - its header comment cites `quality-gates.md:50` and `COMPLIANCE-SPEC.md:320` |
| **B101** | Reviewers verify the code-review checklist before approving | **ABSENT** | `.github/pull_request_template.md`'s `## Checklist` is the **author's** self-check (*"Self-review completed"*), i.e. `development-workflow.md:201-241`, not `:248`'s reviewer checklist; and nobody has said which subset binds here. Control: `grep -in 'reviewer'` hits `DESIGN.md:20,74,1989`, so the search works and none is a review checklist | No |
| **B102** | Squash merge; delete the branch after merge | **MET (untracked)** | `CONTRIBUTING.md:64` - *"**Squash merge** (`development-workflow.md:82`). Delete the branch after merge."* Squash also at `docs/adr/0006-single-main-branch.md:24` | Standard cited; not B102 |
| **B103** | A README exists at the repo root | **SUPERSEDED (deferred with B77)** | Same disposition as B77; U13 (`IMPLEMENTATION-PLAN.md:992`) owns it | Yes, by subject |
| **B104** | `CONTRIBUTING.md` or inlined contribution rules | **MET (untracked)** | `CONTRIBUTING.md:3` opens by naming the clause and cites `readme-standard.md:56`. **Untracked** - `git status` shows `?? CONTRIBUTING.md` | Standard cited; not B104 |
| **B105** | Named maintainers | **SUPERSEDED** *(was ABSENT - I over-called it)* | `readme-standard.md:58` reads *"named owners (**people or team aliases**)"*, and `SECURITY.md:9` publishes `security@evolvconsulting.com`. **A team alias satisfies the clause on its own wording.** I read the hits for "maintainer" and never re-read the clause's parenthetical - see F-6 | Yes - `SECURITY.md:9` |

### Counts

| Class | Count | Rows |
|---|---|---|
| **MET IN SUBSTANCE** | **12** | B49 (code half), B50, B51, B52, B53, B58, B59, B82, B98 (prose half), B100, B102, B104 |
| **GENUINELY ABSENT** | **8 rows + 2 halves** | B16, B61, B74, B76, B79, B84, B96, B101 - plus **B49's 72-character half** and **B98's wiring half** |
| **CONTRADICTED** | **1** | B75 |
| **SUPERSEDED / deferred with a recorded reason** | **7** | B73, B77, B78, B81, B89, B103, **B105** (reclassified - see F-6; I had over-called it ABSENT) |

**Of the 12 MET, exactly one - B58 - is recorded against its B-number.** Two more (B73, B98) are
recorded against a ruling or an ADR. **Nine are met by accident**: correct today because somebody
independently followed the standard, with nothing in the tree that would notice a regression.

---

## 2. Is there a pattern? Yes, and it is sharper than the hypothesis.

### 2.1 The hypothesis, tested

The brief's hypothesis: *the design and the plan were written against the STANDARDS, not against the
corpus that audited the design against the standards, so anything the corpus discovered after the
design was drafted had no route in.*

**I tried to falsify it. It survives, with one correction.** `DESIGN.md` cites **30 distinct
B-numbers**, so a route from the corpus into the design plainly existed:

```
B1 B2 B3 B4 B5 B6 B7 B12 B15 B17 B19 B21 B23 B25 B30 B37 B39 B40 B41 B42 B47
B72 B88 B90 B91 B97 B99 B106 B107 B108
```

Look at where they stop. **Twenty-one of the thirty are B1-B47. Between B48 and B71 the design cites
nothing at all**, and above B72 it cites eight scattered rows. The plan cites four in total:
`B15 B37 B47 B108`.

The corpus's own §3 section numbering explains the cut exactly:

| Corpus section | Range | Subject | Cited in `DESIGN.md`? |
|---|---|---|---|
| §3.1-§3.4 | B1-B47 | Error contract, tool guardrails, input validation, resilience | **Densely - 21 rows** |
| §3.5-§3.6 | B48-B63 | Python style, blessed libraries, testing configuration | **Zero** |
| §3.7-§3.10 | B64-B106 | CI/supply chain, documentation, hygiene, workflow | Sparse - 8 rows |

**Every one of the 28 uncited-open rows sits in §3.5-§3.10. Not one is in §3.1-§3.4.** That is the
pattern, and it is not a coincidence of subject matter - it is a coincidence of **artifact type**.

### 2.2 The mechanism: two lossy joins, and neither is the corpus's fault

**Join 1 - obligation → `DESIGN.md`.** `DESIGN.md` is a design document. It has a section for every
*decision* and no section for a *file* or a *configuration line*. B1-B47 are decisions (what status
code, what limit, what the breaker does) and they landed. B49-B52 are `pyproject.toml` lines.
B58/B59/B61 are pytest configuration. B77/B100/B104/B105 are files to write. **There was nowhere for
them to go**, so they were pushed into §10.1's "the README must document…" - which is why the README
cluster is four rows of this table - or they went nowhere at all.

**Join 2 - `DESIGN.md` → the plan.** The plan states its own scheduling key at
`IMPLEMENTATION-PLAN.md:1408-1409`: *"**What is scheduled against every case is the §8 list, not the
threat table**"*. §8 is `DESIGN.md`'s required-test-case list. **So an obligation reached a work unit
only if it first became a §8 case.** And the plan closes the other route explicitly, in its own
words, at `IMPLEMENTATION-PLAN.md:1376-1385`:

> *"**I did not read the standards corpus.** Every `standards/...:line` citation in this plan is
> quoted **from `DESIGN.md` or an ADR**, not verified at its source"* … *"I did **not** read
> `COMPLIANCE-SPEC.md`, `STANDARDS.md` … or any of the **17 documents in `docs/reviews/`** beyond
> the three gate scripts' docstrings."*

`CONFORMANCE-RESWEEP.md` is one of those 17. **The plan says, in writing, that it never read the
document that audited the thing it was planning from.** The hypothesis is not merely supported; it
is a stated property of the artifact.

### 2.3 The control that proves the mechanism rather than merely fitting it

A pattern that only fits is a story. This one has a **positive control**, and it fires.

`docs/research/COMPLIANCE-SPEC.md` is a *second* obligation corpus, and unlike the resweep it **was**
executed against - by COMPLIANCE-1, whose output is `docs/reviews/COMPLIANCE-SPEC-PASS.md`, and by
U0. It cites these B-numbers:

```
B1 B2 B3 B4 B5 B6 B7 B8 B9 B17 B20 B23 B27 B28 B32 B34 B37 B40 B44 B45 B46
B49 B50 B51 B55 B56 B58 B63 B72 B88 B91
```

**B49, B50, B51, B55, B58** - five rows out of the §3.5-§3.6 dead zone. And those are precisely the
rows that got fixed:

- `pyproject.toml:129-133` justifies `line-length = 88` by citing **`COMPLIANCE-SPEC.md:513`**, not
  the resweep's B49 row.
- `pyproject.toml:148-158`'s rule block is headed *"COMPLIANCE-SPEC.md:205-218 verbatim. Five [STD]
  families were missing"* - that is B50/B51/B52 closing, sourced from COMPLIANCE-SPEC.
- B55's pytest configuration landed the same way (the brief's own worked example of an obligation
  addressed without ever being cited).

**So the rule is not "the corpus failed to propagate". It is: an obligation propagated if and only if
a document somebody actually executed against happened to name it.** The design named B1-B47.
COMPLIANCE-SPEC named a scattered set including five style rows. `CONFORMANCE-RESWEEP.md` named all
59 and **was never executed against by anyone until this task** - which is why its unique
contribution, the §3.5-§3.10 tail, is the exact set that reached nothing.

B58 is the one row that escaped, and it escaped because `quality-gates.md:79` phrases it as a
**required-check breach** - loud enough that a human read the row directly. **Loudness is not a
propagation mechanism.**

### 2.4 A secondary axis, worth stating because it predicts the next miss

Cutting the same 28 by *what kind of thing would satisfy them*, rather than by standard:

| Kind | Rows | Propagated? |
|---|---|---|
| A line in `pyproject.toml` | B49, B50, B51, B52, B75 | 4 of 5 - **and only via COMPLIANCE-SPEC** |
| A file at the repository root | B77, B100, B103, B104, B105 | Only after a human went looking, this week |
| A CI job or step | B59, B74, B76, B82 | 2 of 4 |
| A GitHub **settings** object | B98, B102 | **Never - no artifact in this repo can hold them** |
| A policy nobody owns | B96, B101, B105 | **None** |

**B98 and B102 are the interesting cell.** They cannot be satisfied by any file, so no work unit can
ever close them, so they will read as open forever. That is not a propagation failure - it is a
category the tracking system has no state for.

---

## 3. Findings, each with a suggested fix

> Every fix below is **my suggestion, to verify** - not an instruction. None has been applied: this
> task edited nothing and committed nothing.

**F-1 · B75 is CONTRADICTED, and the contradiction is deliberate.**
`.github/workflows/ci.yml:297-298, 307-308, 314-315` hold three commented-out CI steps, each with a
written reason and an owning unit. `agentic-coding-standard.md:173` forbids commented-out code
blocks, and no ADR records the deviation.
**Suggested fix (verify):** an ADR - *"deferred CI steps are commented in place, not deleted"* -
arguing that a deleted step loses both its reasoning and its owning unit where a commented one
carries them to the unit that enables it. Then select ruff's `ERA` rule so the *code* half is
enforced while the *workflow* half is a recorded deviation. **Do not simply delete the three
blocks:** the reasoning inside them is load-bearing (`ci.yml:286-295` argues, correctly, against
`pip-audit || true`).

**F-2 · B49's second half is unenforced.** `max-doc-length` is unset, `W505` cannot fire, 68 comment
lines exceed 72.
**Suggested fix (verify):** add `[tool.ruff.lint.pycodestyle] max-doc-length = 72` plus `"W505"` in
`select` (owner's call - I did not edit `pyproject.toml`). **Expect it red on its first run against
68 lines**, so either reflow in the same commit the way `2d2e1a3` reflowed for 88, or file an ADR
narrowing B49 to code lines. Landing the rule without the reflow makes CI red on arrival, which
`ci.yml:286-295` already argues is the worst available outcome.

**F-3 · B96 has no rotation policy, and this server exists to hold third-party API keys.**
`environments.md:626` says rotation *"MUST be enforced (not aspirational)"* and `:636` sets quarterly
plus *"key found in logs"* as an unscheduled trigger. The design builds the detection (§4.1's
redaction) and not the response.
**Suggested fix (verify):** a **Rotation** section in `docs/CREDENTIAL-CHECKLIST.md`, which already
owns the credential lifecycle, carrying the four runbook steps of `environments.md:656-665` - plus an
ADR recording the hard constraint `docs/research/JOBVITE-API.md:279` establishes: *"The credentials
are long-lived static secrets; rotation is a support ticket."* Quarterly self-service rotation is
**not available from this vendor**, so the honest artifact is a runbook naming the support path and
the trigger list, not a schedule nobody can keep.

**F-4 · B76 is unstated, and it is the rule that stops an agent editing the gate that is failing
it.** Zero occurrences of the protected-path rule outside the audit corpus - and while this audit
ran, agents were writing into `.github/`.
**Suggested fix (verify):** one section in `CONTRIBUTING.md` (untracked and owned by another agent
right now, so coordinate) listing `.github/workflows/`, `pyproject.toml`, `uv.lock`,
`.pre-commit-config.yaml` and `docs/DESIGN.md` as paths an agent may propose but not commit
unreviewed, citing `agentic-coding-standard.md:66`. The cheapest real enforcement is a `CODEOWNERS`
file, which converts the prose into a required review.

**F-5 · B84 has no breaking-change discipline, and B5 depends on it.**
`error-contract.md:210` makes a published `type` URI a contract whose change is breaking. Nothing
anywhere says `BREAKING:`.
**Suggested fix (verify):** add `BREAKING:` to `changelog.d/README.md`'s permitted-heading list with
the mandated `Migration` sub-bullet, and a sentence in `CONTRIBUTING.md` tying a `BREAKING:` entry to
a major bump. This closes B84 **and** gives B5's stability half its first enforcement point anywhere.

**F-6 · B105 — WITHDRAWN. I over-called this one.** I reported that nobody is named and that the
value is a person rather than a heading. The clause does not say that: `readme-standard.md:58` reads
*"named owners (**people or team aliases**) responsible for review and release"*, and
`SECURITY.md:9` already publishes `security@evolvconsulting.com`. **A team alias satisfies the
clause on its own wording**, and naming an individual in a public repository would be a cost the
standard never asked for. Team-lead ruling; `docs/OBLIGATIONS.md` now records B105 as SUPERSEDED
against that anchor rather than ABSENT.
**Residual, small and worth carrying:** the alias is published for **vulnerability reporting**, and
`:58` asks for the owner responsible for **review and release**. U13 should carry the alias under
the Maintainers heading in that second sense, so the row is discharged by an artifact that says what
the clause asks.

**F-7 · B101: the PR template's checklist is the author's, not the reviewer's.** This is the row most
likely to be mis-closed - `.github/pull_request_template.md` *has* a `## Checklist`, and it is
`development-workflow.md:201-241`'s author checklist, not `:248`'s reviewer checklist.
**Suggested fix (verify):** a `## For reviewers` block in the same template naming the binding subset
of `:248` - the Security and Type Safety items - and stating that the frontend items are N/A here.
Whoever closes B100 should be told explicitly that **B101 is not closed with it**.

**F-8 · B98 and B102 cannot be satisfied by any file in this repository.** Branch protection is a
GitHub settings object.
**Suggested fix (verify):** record the intended settings as a checklist in a new
`docs/REPO-SETTINGS.md` - required checks by job name, 1 approval, squash-only, auto-delete branch -
and mark B98/B102 in any future sweep as **OUT-OF-TREE** rather than open, so they stop reading as
unfinished work. Note `COMPLIANCE-SPEC.md:119-129` already specifies two [STD] properties of that
wiring - a skipped required check must fail, and no path-filtered job may be a direct required check
- that nothing has applied.

**F-9 · Nine of the twelve MET rows are met by accident.** B50, B51, B52, B53, B59, B75 (in part),
B82, B102 and B104 are correct today with nothing tying them to the obligation. Delete `"DTZ"` from
`pyproject.toml:156` and B51 breaks with no check anywhere mentioning B51.
**BUILT — see §5.** `docs/OBLIGATIONS.md` and `docs/reviews/check-obligations.py` now hold the map
and re-check it. The remaining half - extending the inline `# [STD] python.md:227` convention to
name the B-number - lands in files owned by other agents and is handed off at §6.

**F-10 · The resweep's table cannot be parsed naively, and it has already produced one wrong
population.** Six rows carry escaped pipes; the `Category` column sits one cell from the verdict,
shares no vocabulary with it, and reads like one.
**BUILT — see §5.** `docs/reviews/check-resweep-verdicts.py` emits the per-B final verdict and
asserts its totals against the counts the document states about itself.

---

## 4. What I did not settle

- **B16 cannot be fully judged yet.** No tool descriptions exist, so *"reviewed like prompts"* has no
  referent. I classified it ABSENT because **nothing schedules the review** - U5, U8 and U14 all
  specify schemas and never descriptions - not because the descriptions are wrong.
- **`.github/` and `CONTRIBUTING.md` were being written by another agent while this ran.** B82, B100,
  B102 and B104 are classed MET against a working tree that is not committed. If that work is
  abandoned, all four revert to ABSENT.
- **I did not re-verify the 16 SATISFIED, the 3 NOT-APPLICABLE, or the 12 open-but-cited rows.** The
  brief scoped me to the uncited population, and §5 of the resweep already states what it skipped.
- **The action-pin drift** (`checkout@v4` against `COMPLIANCE-SPEC.md:135`'s `@v6`) is real but
  already recorded as C-1 in `docs/reviews/COMPLIANCE-SPEC-PASS.md:88-89`; not re-reported here.

---

## 5. The mechanism fix, built

Three artifacts, in the tree, uncommitted, verified by running them.

### 5.1 `docs/OBLIGATIONS.md` + `docs/reviews/check-obligations.py`

The map: B-number → the artifact that discharges it at `file:line` → **a subject string that must
appear on that line**. 28 rows, seeded from this audit's population: 19 with anchors, 9 recorded as
`ABSENT` with no anchor.

```
$ python3 docs/reviews/check-obligations.py
Mappings: 28  |  anchors verified against their subject: 19  |  recorded as absent: 9
Every mapped anchor still contains its subject. OK.                          # exit 0
```

The script checks the **subject**, not the line number. Checking that an anchor resolves to *some*
line passes against any edit that shifts the file, which is exactly how a citation rots -
`docs/reviews/CITATION-RANGE-AUDIT.md` records that failure happening in this corpus already. When a
subject has moved rather than vanished, the failure names the line it moved to, so a drifted anchor
costs one edit and not one investigation.

**Nine controls, all fired**, each mutating a copy of the tree and requiring the named check to go
red:

```
  fired         anchor repointed at line 1 (B49)
  fired         cited file deleted (B49)
  fired         subject removed from the artifact (B49)
  fired         artifact shifted by five lines (B49)
  fired         subject weakened to a single character (B49)
  fired         the DTZ rule deleted from pyproject.toml (B51's own claim)
  fired         one B-number mapped twice
  fired         an ABSENT row given an artifact (B16)
  fired         every mapping removed (selector control)

9/9 controls fired.
post-run re-check of the real OBLIGATIONS.md: exit=0
```

Five of those break the **map**; two break the **target**. That split is deliberate. The generic
controls all land on B49 because it is the first mapped row, and a control that only ever breaks the
first row proves the machinery works without proving the claim. So `_c_regress_b51_dtz` is named
rather than generic: it deletes `"DTZ",` from a copy of `pyproject.toml` and requires the checker to
go red, which is the specific sentence this file asserts about itself - *delete DTZ and B51 silently
reverts, with no check anywhere mentioning B51.* **That sentence is now false, and the control is
what makes it false.**

> **Measured while building it, and it is the best evidence the map is worth keeping.** On its first
> run the checker went **red on six of nineteen anchors** - four in `pyproject.toml` (shifted 7
> lines) and two in `IMPLEMENTATION-PLAN.md` (shifted 145 lines, the file having grown by 402 lines
> while this audit ran). **Every one of those citations was written by me, correct, within the
> previous hour.** Hand-maintained `file:line` evidence in a repository with live agents does not rot
> in weeks; it rots in minutes. It also caught a genuinely weak row: B78's subject was
> `checked against`, which matched line 16 of a different section - the failure message named the
> wrong line, which is how I found it.

### 5.2 `docs/reviews/check-resweep-verdicts.py` (finding F-10)

Emits the final verdict per B-number from `CONFORMANCE-RESWEEP.md`, and **asserts its own tally
against the counts §1 states about itself**:

```
$ python3 docs/reviews/check-resweep-verdicts.py
Rows parsed: 59
  SATISFIED        rows=16  section 1 says=16
  PARTIAL          rows=18  section 1 says=18
  UNADDRESSED      rows=22  section 1 says=22
  NOT-APPLICABLE   rows=3   section 1 says=3

Still open (PARTIAL or UNADDRESSED): 40
The row tally and section 1's stated counts agree. OK.                       # exit 0
```

Two independent statements of the same number - one from the prose, one from the rows - have to
agree. **Five controls, all fired**, including the one that matters: a `DEFERRED-WITH-REASON` value
placed in the verdict column is **refused** rather than reported as a new verdict class, which is
the exact defect that produced the wrong population in the first place. The selector controls (zero
rows parsed; §1's heading renamed) are failures, never passes.

It also anchors §1's counts on the heading `### The 59 re-walked`, because §1 carries a **second**
table ("Projected across all 106") whose numbers are a different population. Reading that one would
compare 59 rows against a 106-row claim and report the disagreement as a defect.

---

## 6. Hand-off: the inline convention (F-9's second half)

Every edit below lands in a file owned by another agent - `pyproject.toml`, `.github/`,
`CONTRIBUTING.md` - so none has been applied. The convention already exists in `pyproject.toml`
(`# [STD] python.md:227`); the change is to **append the B-number**, so the record survives someone
reading only the file.

Each is a comment-only, one-line edit. **My suggestion, to verify.**

| File | Line | Current | Append |
|---|---|---|---|
| `pyproject.toml` | 141 | `line-length = 88` (comment above cites `python.md:35`) | `(B49 - code half only; the 72-char half is B49b)` |
| `pyproject.toml` | 157 | `"N",        # pep8-naming       [STD] python.md:62-72` | `(B52)` |
| `pyproject.toml` | 163 | `"DTZ",      # naive datetimes   [STD] python.md:227, no datetime.utcnow` | `(B51)` |
| `pyproject.toml` | 165 | the `"ANN"` line | `(B50, type-hint half)` |
| `pyproject.toml` | 170 | `convention = "google"       # python.md:97` | `(B50, docstring half)` |
| `pyproject.toml` | 6 | `license = "Apache-2.0"` | `# B89 - SPDX id; the README section is deferred with B77` |
| `.env.example` | header | the file comment | `# Discharges B53 and B91` |
| `.github/workflows/ci.yml` | 175-178 | the `Default suite, zero skips` step | `# B59 - no positional path, so testpaths stays authoritative` |
| `.github/workflows/ci.yml` | 432 | the `links` job's header comment, which already quotes `readme-standard.md:69` (the job itself is at `:454`) | `(B82)` |
| `.github/workflows/ci.yml` | 297-315 | the three commented-out step blocks | `# B75 - a recorded deviation from agentic-coding-standard.md:173, pending an ADR` |
| `.github/pull_request_template.md` | 3 | already cites `quality-gates.md:50` | `(B100 - and note this does NOT close B101)` |
| `CONTRIBUTING.md` | 3 | already cites `readme-standard.md:56` | `(B104)` |
| `CONTRIBUTING.md` | 64 | `**Squash merge** (development-workflow.md:82)` | `(B102 - enforcement is branch protection, out of tree: B98)` |

**Whoever applies these should re-run `python3 docs/reviews/check-obligations.py` afterwards**, since
a comment insert shifts every anchor below it in that file. The checker will name the new line for
each, so the fix-up is mechanical.

**Not applied, deliberately, and not a hand-off:** B75 needs a decision, not an edit. Deleting the
three commented CI blocks would destroy `ci.yml:286-295`'s load-bearing argument against
`pip-audit || true`, so the right shape is an ADR plus `ERA` on Python only. That is a scope call
above this task.
