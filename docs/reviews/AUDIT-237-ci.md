# AUDIT-237: the complete CI audit, and the restructure priced in minutes

Task #237. Phil, verbatim: "ci is for the fucking project code, not the docs.
clean that shit up, I want a complete audit done."

Written by `blackthorn-ci` on branch `ci/237-audit`, worktree `/tmp/w237-ci-audit`,
audited against main at `661acfe` (which landed the lead's restructure while this
audit ran - section 4 reviews it and section 5 fixes its holes).

Timing sources, marked per row: **(G)** = per-step wall-clock from the one fully
green run `33582613697` (the only run of the current shape that ever concluded
green with all steps); **(L)** = measured locally this session (uv 0.11.3,
Python 3.12.3) for steps added after that run; **(C)** = job-level from run
`33586402689`. A predicted number appears nowhere in this document.

## 1. The headline arithmetic, measured

From run 33582613697, summing per-step timestamps the jobs API returns:

    job                                    wall      steps
    Lint, types, tests                    5191s      66 then, 70 now
    CodeQL                                  67s      3
    Static gates, supply chain and links    44s      27 then, 30 now
    wiring-probe (from run 33586402689)    ~17s      6
    -------------------------------------------------------
    run wall-clock = the test job's        86.5 min
    billed job-minutes                     ~90 min

Inside the test job's 5191s:

    the harness lane (41 steps, mutation/amputation + their controls)   4969s = 82.8 min
    everything else the job does (lint, types, suite, coverage,
    audits, static guards - 29 steps)                                    222s =  3.7 min

So the ratio the task states is real but its numerator is understated: the
product path is **222 seconds, not 60** - the "1 minute" was the suite step
alone (83s (G)); coverage re-runs the suite (82s (G)), mypy is 9s, the audits
and quickstart the rest. Cold-cache caveat the lead asked for: locally the
suite is 55s and on the green runner 83s; a recent loaded run took 161 min for
the whole job, i.e. the RATIO (product ~4%, harnesses ~96%) is what holds, not
the absolute minutes.

Run history, because absence is a finding: of **284 concluded CI runs ever, 2
succeeded, 93 failed, 187 were cancelled** (API, 2026-09-02; plus 2 pending).
The trunk pays ~86-161 min per push for a record that has reached a green
conclusion twice in the project's life. Cancellations are dominated by
push-over-push superseding; the cost is billed regardless.

## 2. The partition

Every one of the 111 steps is classified in the table (section 6):

- **PROJECT (47 steps)**: the product cannot ship without it. This includes
  the 28 U-harness steps, deliberately: **the lead's guess that harnesses are
  a docs-adjacent tax is wrong - what they WATCH is src/ and tests/**. Their
  problem was never their class, it was their CADENCE: they re-run covering
  tests once per row, so they cost ~83 min while answering a question that
  changes only when the code they mutate changes.
- **INFRASTRUCTURE (43 steps)**: CI/supply-chain correctness - the harness
  gate's own controls, floors, anchors, actionlint, SBOM, secret scan,
  CodeQL, mirror liveness. Cheap (nearly all 0-7s) and correctly always-on.
- **CONVENTION (20 steps)**: prose and record integrity - citations,
  cross-references, obligations, ADR numbering, resweep tallies, plan
  measurements, brief-report references. **Measured total: ~30 seconds.**
  The user's complaint is right about what CI gates on and wrong about where
  the minutes go: the docs checkers cost half a minute; the 83 minutes were
  PROJECT-class harnesses running on prose-only pushes.

Two of the 20 CONVENTION steps are INERT on every runner today - "Standard
clause citations resolve" and "Standards citations resolve" both exit 2
(private corpus, no STANDARDS_TOKEN, #106) and are converted to a loud
warning. They gate nothing in CI and never have.

The lead flagged `check-design-freeze.py` as possibly closer to a project
invariant than to prose. Half right: it guards the DESIGN document against
moving without an ADR - the SUBJECT is prose, the INVARIANT is governance. It
is classified CONVENTION here because its failure breaks no shipped artifact,
and kept always-on because it costs 0s (G).

If it never runs again, what breaks - the honest one-line version per class:
PROJECT: the product breaks and ships. INFRASTRUCTURE: a gate goes vacuous
and its next green lies. CONVENTION: **a document becomes internally
inconsistent** - said plainly, as asked. That is a real cost on a repo whose
docs outweigh src 3.66x, but it is not a trunk-blocking cost, and it prices
at ~30 seconds, not 83 minutes.

## 3. What the restructure does (661acfe + this branch)

`661acfe` (the lead, landed while this audit ran) added a `changes` job and
step-level `if: needs.changes.outputs.code == 'true'` on 41 harness steps.
Steps stay in ci.yml because several checkers parse this file by path -
verified independently here: `check-row-floors.py:48` and
`check-row-floor-exactness.py:137` pin `.github/workflows/ci.yml`; moving
steps to a second workflow strands both. Gating in place is the right shape.

**Measured before/after, docs-only push** (the dominant push: src/ unchanged
for 118 commits; the board records 73 docs files grown in one day against 0
product commits):

    BEFORE: wall 86.5 min (green run; 161 observed under load)
            billed ~90 job-min
    AFTER:  test job 5191 - 4969 (skipped harness steps) = 222s = 3.7 min
            wall = max(test 3.7, codeql 1.1, static ~0.8, changes ~0.3) = ~4 min
            billed = changes 1 + static 1 + test 4 + codeql 2 + wiring 1 = ~9 job-min
    SAVING per docs-only push: ~82 min wall, ~81 billed job-min (~90%)

**Code push**: all 41 steps run exactly as before; the changes job adds ~15s
wall and 1 billed minute (rounding). ~90 -> ~91 billed. Note for Tier 0: the
changes job is a new always-on billed job, the exact rounding class #143
killed three of. It cannot be folded into a consumer of its output (a job
output is only readable via `needs:`), so 1 min/run is the price of the
lever; one skipped docs push repays ~80 of them.

**#143 interplay, checked as ordered**: #143's lever was job-count rounding
(634 -> 214 min measured there); this lever is per-step execution inside
surviving jobs. They do not overlap and the savings do not double-count: no
job #143 folded is re-split, and the only job-count change here is +1.

**The green-means-less problem (#231's open half)** is handled by making the
weakening loud, not invisible: on a docs-only push the changes job emits a
`::warning::` in the run stating exactly what this green does NOT re-certify,
and all 41 skipped steps render as skipped in the checks UI, not green. The
residual - the README badge reads only the run conclusion - is #231's and
stays open there; nothing here papers over it.

**The harnesses are not deleted and this document does not argue they were a
waste.** They caught #127, #128, #130 and R7's payload-logging middleware that
all 887 tests ignored. Cadence after this change: every code push, every
weekly sweep (Sundays 00:00 UTC), every workflow_dispatch, and every push
touching the harnesses or their subjects. The maximum unre-certified window
for a pure-prose stretch is 7 days, and the run says so while it is open.

## 4. Review of 661acfe - findings, each with its fix

Range read: `804b2f7..661acfe` (one commit; it touches only ci.yml). This
file deliberately carries NO `REVIEW-COVERS` declaration:
`check-review-coverage.py` reads only files whose stem matches
`REVIEW.*-R<n>`, so a declaration here would be a machine-looking line that
nothing reads - a false presence. 661acfe therefore still shows NONE in the
coverage report and belongs in the next numbered round's range (R23), which
can use this section as its input for that commit.

- **H1. The printed warning promised a schedule that does not exist.** The
  docs-only `::warning::` said "The nightly schedule ... restore[s] the full
  claim"; the only cron in the file is `0 0 * * 0` - WEEKLY, Sundays. The
  commit message makes the same nightly claim. A reader believed staleness
  of at most a day; the truth is at most seven. FIXED on this branch: the
  warning says "weekly sweep (Sundays 00:00 UTC)". Alternative Tier 0 may
  prefer instead: add a real nightly cron - that costs ~90 billed min x 7 a
  week against ~90 for weekly, and then the original sentence becomes true.
- **H2. The trigger pattern missed the harnesses whose subject is not code.**
  The pattern was `^(src|tests|scripts)/|^\.github/|^pyproject\.toml$|^uv\.lock$`.
  Seven gated steps run harnesses living under `docs/reviews/` (the coupling
  sweep, obligation controls, docs-lint amputations, brief-report and
  bare-citation controls), and the coupling/obligation controls' SUBJECTS are
  `docs/DESIGN.md` and `docs/OBLIGATIONS.md`. A push editing
  `docs/reviews/check-coupling.py` - or an ADR application editing DESIGN.md -
  read as "docs-only" and skipped the exact harness that watches that change.
  This is the trap the brief named: a harness whose subject is not under src/
  breaks the src/-only assumption. FIXED: the pattern now includes
  `^docs/reviews/[^ ]*\.(py|sh)$` and `^docs/(DESIGN|OBLIGATIONS)\.md$`.
- **M1. A git failure skipped the harnesses, violating the commit's own
  fail-open rule.** `n=$(git diff ... | grep -c ...) || n=0` under pipefail:
  a git error fails the whole pipeline, `|| n=0` converts it to zero, and
  zero means SKIP - while the commit message promises "a gate that cannot
  tell must run the harnesses". FIXED: the diff and the count are separate
  commands; a diff that cannot be computed runs everything, loudly.
- **L1. `actions/checkout@v4` in the changes job; every other checkout in the
  file is `@v6`.** Two pins for one action is the two-lists shape. FIXED: v6.
- **L2. `${{ }}` interpolated directly into the run block** (event name, both
  SHAs) where the file's own convention (the mirror-liveness step) passes
  values via `env:`. Not exploitable - SHAs and event names - but one
  convention beats two. FIXED: `env:` block.
- **L3 (latent, in tests, found by building my own variant first).**
  `tests/test_workflow_contexts.py`'s `CONTEXT` regex read every `word.` as a
  context, so the VALID job-level expression `needs.<job>.outputs.<name>` -
  whose `needs` context the test's own allowlist permits - was flagged on its
  path segments (`lanes`, `outputs`). Measured: a job-level
  `if: needs.changes.outputs.code == 'true'` fails that test while actionlint,
  which models contexts properly, passes it at rc=0. 661acfe's step-level
  `if:`s dodge it by accident; the first future job-level fan-out hits it.
  FIXED: `(?<!\.)` lookbehind plus a two-direction control test
  (`test_the_context_finder_reads_only_the_head_of_a_path`) - R3-H1's exact
  expression must still be caught, the needs-outputs path must not. Suite
  887 -> 888; floor raised in ci.yml, the one place it lives.
- **N1. Five "NEVER EXECUTED" comments had become false**: both SBOM steps,
  the secret scan, lychee, and the CodeQL job banner all executed green in
  33582613697. A stale "never ran" over a step that ran is
  switched-off-looking-like-broken, mirrored. FIXED in place with the run id
  and date; the mirror-push "NEVER EXECUTED" is still true (no MIRROR_TOKEN)
  and stands unchanged.

## 5. Verification of this branch (every exit code read on its own line)

    actionlint (pinned 1.7.7, SHELLCHECK_OPTS=--severity=warning)   rc=0
    ruff check / ruff format --check / mypy                         rc=0 / 0 / 0
    pytest default suite                     888 passed, 0 skipped, rc=0
    check-suite-floor.sh 888                 "888 passed, floor 888" rc=0
    check-checkers-are-wired.py (+ --self-test)                     rc=0 / 0
    check-row-floors.py / check-row-floor-exactness.py (+ --self-test)  all 0
    check-harness-anchors.py --self-check --floor 464               rc=0
    check-no-sigpipe-pipelines.py / check-no-errexit.py             rc=0 / 0
    check-landing-published.py / check-timeout-literals.py (+ --self-test) all 0
    check-pytest-bounded.sh / check-env-vars-are-declared.py        rc=0 / 0
    check-obligations.py (+ --controls)                             rc=0 / 0
    coupling gate / design-freeze / design-citations / citation-shape /
    adr-numbers / cross-references / committed-file-types --all     all 0
    probe-ci-checker-steps.py                                       rc=0
    probe-wired-checker-amputation.py --self-test                   rc=0

The battery ran after every structural change, not once at the end.
probe-ci-checker-steps-control.py exits 2 on a dirty tree by design and was
excluded while edits were in flight.

## 6. The complete step table - all 111 steps

"gated" = carries `if: needs.changes.outputs.code == 'true'` (runs only when
the change set touches code/infra, on any schedule, or on dispatch).

### Job `changes`

| step | runs | measured | watches | if it never runs again | class | gated |
|---|---|---|---|---|---|---|
| actions/checkout@v6 | `actions/checkout@v6` | 2s (G) | - | prologue | INFRASTRUCTURE | no |

### Job `static-gates`

| step | runs | measured | watches | if it never runs again | class | gated |
|---|---|---|---|---|---|---|
| actions/checkout@v6 | `actions/checkout@v6` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | `astral-sh/setup-uv@v5` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | `actions/setup-python@v5` | ~0s | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | `uv sync` | 2s (G) | uv.lock | prologue; drift caught by later steps | PROJECT | no |
| Lint the workflows | `actionlint` | 1s (G) | .github/workflows/* | the next R3-H1-class expression error ships unlinted; 119 silent failures was the price last time | INFRASTRUCTURE | no |
| Coupling gate | `docs/reviews/check-coupling.py` | 0s (G) | DESIGN.md vs src/tests | a design-coupled test can be deleted with the design still claiming it exists | CONVENTION | no |
| The design at its declared freeze is the design on main | `docs/reviews/check-design-freeze.py` | 0s (G) | docs/DESIGN.md vs DESIGN-FREEZE.txt | the frozen design and its pointer drift apart unnoticed (happened for a full day once) | CONVENTION | no |
| No harness enables errexit | `docs/reviews/check-no-errexit.py` | 0s (G) | scripts/*.sh | a harness gains set -e and its timeout arms become dead code silently | INFRASTRUCTURE | no |
| Every harness emits the canonical HARNESS-RESULT line | `docs/reviews/check-harness-result.sh` | 1s (G) | scripts/*.sh output contract | a harness stops emitting its machine line and downstream gates read nothing | INFRASTRUCTURE | no |
| Every checker is wired, or says why it is not | `docs/reviews/check-checkers-are-wired.py` | 1s (G) | this file vs docs/reviews+scripts | a checker is built, cited as a gate, and never runs - the founding defect, 6 instances so far | INFRASTRUCTURE | no |
| The wiring checker's own controls still fire | `docs/reviews/check-checkers-are-wired.py` | 0s (G) | check-checkers-are-wired.py | the wiring gate itself can no longer fail and nobody knows | INFRASTRUCTURE | no |
| No abort message retypes a seconds figure | `scripts/check-timeout-literals.py` | 1s (G) | scripts/ abort messages | an abort message lies about its timeout after a retune; a reader debugs the wrong number | CONVENTION | no |
| Design citations have a plausible shape | `docs/reviews/check-design-citation-shape.py` | 0s (G) | DESIGN.md citations | citations point at blank lines/dividers again (47 found at wiring) | CONVENTION | no |
| Standard clause citations resolve | `docs/reviews/check-clause-citations.py` | 0s (G) | OBLIGATIONS.md clause column | a clause citation stops resolving; INERT in CI (exit 2, no corpus) - it certifies nothing on a runner today | CONVENTION | no |
| Every env var is declared | `docs/reviews/check-env-vars-are-declared.py` | 0s (G) | workflow env usage | a step reads an env var nobody declares and dies at runtime | INFRASTRUCTURE | no |
| Every Settings field is consumed by something | `docs/reviews/check-settings-are-read.py` | 0s (G) | src/ config.py | a declared setting ships that no code reads; an operator sets it and it does nothing | PROJECT | no |
| Standards citations resolve | `docs/reviews/check-standards-citations.py` | 0s (G) | src/tests/scripts inline standards citations | 13 of 88 were wrong once; INERT in CI (exit 2, no corpus) until STANDARDS_TOKEN (#106) | CONVENTION | no |
| Section cross-references resolve | `docs/reviews/check-cross-references.py` | 1s (G) | docs internal SSn.m refs | a section reference dangles; a document becomes internally inconsistent - plainly, that is all | CONVENTION | no |
| Coupling controls, all fired | `docs/reviews/check-coupling-controls.py` | 1s (G) | check-coupling.py + DESIGN.md | the coupling gate can pass without being able to fail; its green becomes vacuous | CONVENTION | **yes** |
| Obligation anchors still resolve to their subjects | `docs/reviews/check-obligations.py` | 0s (G) | OBLIGATIONS.md anchors into pyproject/ci/env | the obligations map decays the moment a unit edits an anchor file | CONVENTION | no |
| Obligation checker controls, all fired | `docs/reviews/check-obligations.py` | 1s (G) | check-obligations.py | same vacuous-green risk one level up | CONVENTION | **yes** |
| Plan measurements still reproduce | `docs/reviews/check-plan-measurements.py` | 8s (G) | IMPLEMENTATION-PLAN.md probe claims | a decision rests on a measurement that no longer reproduces; prose decays into a claim | CONVENTION | no |
| Resweep verdicts agree with the document's own count | `docs/reviews/check-resweep-verdicts.py` | 0s (G) | CONFORMANCE-RESWEEP.md | a document contradicts its own tally; a work assignment gets driven off a wrong population again | CONVENTION | no |
| Coupling mutation sweep, no holes | `docs/reviews/check-coupling-sweep.py` | 7s (G) | check-coupling.py hole-space | the coupling gate grows a hole and nothing sweeps for it | CONVENTION | **yes** |
| Licence gate | `pip-licenses` | 0s (G) | uv.lock licences | a copyleft dependency ships; a legal problem, not a prose one | INFRASTRUCTURE | no |
| SBOM (CycloneDX) | `anchore/sbom-action@v0` | 4s (G) | .venv frozen resolve | no SBOM artifact for compliance consumers | INFRASTRUCTURE | no |
| SBOM (SPDX) | `anchore/sbom-action@v0` | 3s (G) | .venv frozen resolve | same, SPDX side | INFRASTRUCTURE | no |
| Secret scan | `trufflesecurity/trufflehog@v3.88.0` | 5s (G) | full git history | a committed-then-removed secret stays unnoticed in history | INFRASTRUCTURE | no |
| Relative links resolve | `lycheeverse/lychee-action@v2` | 1s (G) | **/*.md relative links | markdown links rot; documents become internally inconsistent - plainly, prose integrity only | CONVENTION | no |
| The mirror workflow is still running | `scripts/check-mirror-liveness.py` | 1s (L) | mirror.yml run state via API | the mirror stops (60-day disable) and pushes go uncopied silently | INFRASTRUCTURE | no |

### Job `test`

| step | runs | measured | watches | if it never runs again | class | gated |
|---|---|---|---|---|---|---|
| actions/checkout@v6 | `actions/checkout@v6` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | `astral-sh/setup-uv@v5` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | `actions/setup-python@v5` | ~0s | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | `uv sync` | 2s (G) | uv.lock | prologue; drift caught by later steps | PROJECT | no |
| No lock drift | `uv lock` | 0s (G) | pyproject vs uv.lock | a dependency edit without relock resolves differently later | PROJECT | no |
| Lint | `ruff` | 0s (G) | src/tests/scripts | style/correctness lint rot | PROJECT | no |
| Format | `ruff` | 0s (G) | formatting | formatting drift | PROJECT | no |
| Types | `mypy` | 9s (G) | src/tests type surface | type errors ship | PROJECT | no |
| Default suite, zero skips | `pytest` | 83s (G) | THE PRODUCT: src/ via 888 tests, floored, zero skips | the product breaks and ships; this is the one step the user calls CI for | PROJECT | no |
| Network-dependent arms | `pytest` | 3s (G) | the fastmcp-slim pin negative arm | the pin constraint stops being tested; resolve rot invisible | PROJECT | no |
| The README's Quickstart still works | `docs/reviews/check-quickstart.py` | 1s (G) | README.md commands, executed | the Quickstart lies to the first user | PROJECT | no |
| Docs-lint amputations, every row caught | `docs/reviews/probe-docs-lint-amputation.py` | 3s (G) | docs/reviews lint probes | the docs-lint probes go dead again (were dead 45 commits once) | CONVENTION | **yes** |
| Collect the credentialed suite | `pytest` | 2s (G) | tests/credentialed imports | the credentialed suite rots uncollected until someone has a credential | PROJECT | no |
| Harness anchors still resolve | `scripts/check-harness-anchors.py` | 0s (G) | harness anchors vs src | a reformat kills a harness anchor and rows silently stop landing | INFRASTRUCTURE | no |
| Every DESIGN.md citation resolves to a line that exists | `docs/reviews/check-design-citations.py` | 0s (G) | DESIGN.md:N citations tree-wide | citations dangle after design edits | CONVENTION | no |
| Every harness is wired and has a row floor | `docs/reviews/check-row-floors.py` | 0s (G) | ci.yml + scripts floors | a harness loses its floor; rows become deletable green | INFRASTRUCTURE | no |
| Every checked row floor EQUALS its harness's live row count | `docs/reviews/check-row-floor-exactness.py` | 0s (G) | ci.yml --min-rows vs live rows | merge-produced slack returns (u14 was 6 rows deletable) | INFRASTRUCTURE | no |
| The floor container's own arms | `docs/reviews/check-row-floor-exactness.py` | 0s (L) | check-row-floor-exactness.py | the exactness checker itself can no longer fail | INFRASTRUCTURE | no |
| No SIGPIPE-prone pipeline judges a gate | `docs/reviews/check-no-sigpipe-pipelines.py` | 0s (G) | ci.yml + scripts pipelines | a gate guard fails open on long output again | INFRASTRUCTURE | no |
| A harness that diagnoses a landing failure publishes it | `docs/reviews/check-landing-published.py` | 0s (G) | harness landing flags | a landing failure is diagnosed and published nowhere | INFRASTRUCTURE | no |
| Stranded-mutation control | `docs/reviews/control-stranded-mutation.sh` | 7s (G) | ci-harness-gate.sh state file | a killed harness strands a mutation in the tree unnoticed | INFRASTRUCTURE | **yes** |
| The gate records who is mutating | `docs/reviews/probe-131-gate-state.sh` | 0s (L) | ci-harness-gate.sh run-state | same restore machinery, the recording half | INFRASTRUCTURE | no |
| The mirror refuses a zero-ref push | `docs/reviews/probe-mirror-zero-refs.sh` | 0s (L) | mirror.yml guard, extracted | the mirror can force-push nothing over everything | INFRASTRUCTURE | no |
| Every report a brief cites is committed | `docs/reviews/check-brief-report-references.py` | 0s (L) | docs/briefs vs tracked reports | a 48KB report dies in a worktree again | CONVENTION | no |
| Controls for the brief-report reference gate | `docs/reviews/check-brief-report-refs-controls.sh` | 1s (L) | check-brief-report-references.py | that gate goes vacuous | CONVENTION | **yes** |
| The bare-citation discriminator's controls | `docs/reviews/probe-204-bare-citations.py` | 0s (L) | probe-204-bare-citations.py | the discriminator goes vacuous | CONVENTION | **yes** |
| Harness anchor checker controls, all fired | `scripts/ci-harness-gate.sh` | 1s (G) | check-harness-anchors.py | the anchor checker goes vacuous | INFRASTRUCTURE | **yes** |
| Mirror liveness controls, all fired | `scripts/ci-harness-gate.sh` | 1s (L) | check-mirror-liveness.py exit codes | the liveness checker misclassifies mirror states | INFRASTRUCTURE | **yes** |
| Harness gate controls, all fired | `scripts/ci-harness-gate-controls.sh` | 1s (G) | ci-harness-gate.sh 23 arms | the gate every harness step rides through can rot | INFRASTRUCTURE | **yes** |
| U5 jobs controls, all fired | `scripts/ci-harness-gate.sh` | 43s (G) | src/ + tests/ for search_jobs; the harness script under scripts/ | a test covering search_jobs can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U5 jobs amputation, every anchor applied | `scripts/ci-harness-gate.sh` | 31s (G) | src/ + tests/ for search_jobs; the harness script under scripts/ | a test covering search_jobs can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U6 paging controls, all fired | `scripts/ci-harness-gate.sh` | 12s (G) | src/ + tests/ for offset paging; the harness script under scripts/ | a test covering offset paging can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U6 paging amputation, every anchor applied | `scripts/ci-harness-gate.sh` | 5s (G) | src/ + tests/ for offset paging; the harness script under scripts/ | a test covering offset paging can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U7 resilience controls, all fired | `scripts/ci-harness-gate.sh` | 31s (G) | src/ + tests/ for timeout/retry/breaker; the harness script under scripts/ | a test covering timeout/retry/breaker can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U7 resilience amputation, every row applied | `scripts/ci-harness-gate.sh` | 72s (G) | src/ + tests/ for timeout/retry/breaker; the harness script under scripts/ | a test covering timeout/retry/breaker can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U8 candidate controls, all fired | `scripts/ci-harness-gate.sh` | 66s (G) | src/ + tests/ for candidate reads; the harness script under scripts/ | a test covering candidate reads can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U8 candidate amputation, every row applied | `scripts/ci-harness-gate.sh` | 33s (G) | src/ + tests/ for candidate reads; the harness script under scripts/ | a test covering candidate reads can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U9 HTTP hardening controls, all fired | `scripts/ci-harness-gate.sh` | 45s (G) | src/ + tests/ for HTTP transport hardening; the harness script under scripts/ | a test covering HTTP transport hardening can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U9 HTTP hardening amputation, every row applied | `scripts/ci-harness-gate.sh` | 1270s (G) | src/ + tests/ for HTTP transport hardening; the harness script under scripts/ | a test covering HTTP transport hardening can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U12 job feed controls, all fired | `scripts/ci-harness-gate.sh` | 51s (G) | src/ + tests/ for get_job_feed redaction; the harness script under scripts/ | a test covering get_job_feed redaction can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U12 job feed amputation, every row applied | `scripts/ci-harness-gate.sh` | 21s (G) | src/ + tests/ for get_job_feed redaction; the harness script under scripts/ | a test covering get_job_feed redaction can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U10 write controls, all fired | `scripts/ci-harness-gate.sh` | 61s (G) | src/ + tests/ for the approval-guarded write; the harness script under scripts/ | a test covering the approval-guarded write can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U10 write amputation, every row applied | `scripts/ci-harness-gate.sh` | 27s (G) | src/ + tests/ for the approval-guarded write; the harness script under scripts/ | a test covering the approval-guarded write can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U14 argument sweep controls, all fired | `scripts/ci-harness-gate.sh` | 52s (G) | src/ + tests/ for the input models; the harness script under scripts/ | a test covering the input models can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U14 argument sweep amputation, every row applied | `scripts/ci-harness-gate.sh` | 24s (G) | src/ + tests/ for the input models; the harness script under scripts/ | a test covering the input models can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| Log redaction amputation, every row applied | `scripts/ci-harness-gate.sh` | 5s (G) | the ADR-0026 redaction install | the api key logs on httpx2 again and nothing notices | PROJECT | **yes** |
| Body cap controls, all fired | `scripts/ci-harness-gate.sh` | 37s (G) | the 1 MiB ASGI body cap | the cap silently stops rejecting oversized bodies | PROJECT | **yes** |
| Body cap amputation, every row applied | `scripts/ci-harness-gate.sh` | 24s (G) | same, amputation side | same | PROJECT | **yes** |
| Critical-path coverage amputation, every row applied | `scripts/ci-harness-gate.sh` | 93s (G) | critical-path assertions | coverage stays 100% while asserting nothing | PROJECT | **yes** |
| ADR numbers are unique and contiguous, and the index matches | `docs/reviews/check-adr-numbers.py` | ~0s | docs/adr/ | two ADRs share a number; code cites an ambiguous decision | CONVENTION | no |
| U0 test controls, all fired | `scripts/ci-harness-gate.sh` | 927s (G) | src/ + tests/ for the test-infrastructure assertions (manifest, markers, tree); the harness script under scripts/ | a test covering the test-infrastructure assertions (manifest, markers, tree) can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| Every pytest invocation is bounded by a timeout | `scripts/check-pytest-bounded.sh` | 0s (G) | scripts pytest calls | a hung suite eats the 6-hour job ceiling | INFRASTRUCTURE | no |
| Committed file types, whole tree | `scripts/check-committed-file-types.py` | 0s (G) | tracked file types | a --no-verify binary lives in the tree | INFRASTRUCTURE | no |
| U15 gate controls, all fired | `scripts/ci-harness-gate.sh` | 17s (G) | src/ + tests/ for the commit-time gates; the harness script under scripts/ | a test covering the commit-time gates can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U15 gate amputation, every row applied | `scripts/ci-harness-gate.sh` | 4s (G) | src/ + tests/ for the commit-time gates; the harness script under scripts/ | a test covering the commit-time gates can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U11 advisory controls, all fired | `scripts/ci-harness-gate.sh` | 6s (G) | src/ + tests/ for the advisory gate; the harness script under scripts/ | a test covering the advisory gate can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U1 boot mutation controls, all fired | `scripts/ci-harness-gate.sh` | 118s (G) | src/ + tests/ for server boot (server.py); the harness script under scripts/ | a test covering server boot (server.py) can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U1 boot amputation harness ran every row | `scripts/ci-harness-gate.sh` | 620s (G) | src/ + tests/ for server boot (server.py); the harness script under scripts/ | a test covering server boot (server.py) can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U3 audit mutation controls, all killed | `scripts/ci-harness-gate.sh` | 190s (G) | src/ + tests/ for the audit trail; the harness script under scripts/ | a test covering the audit trail can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U3 audit amputation harness ran every row | `scripts/ci-harness-gate.sh` | 131s (G) | src/ + tests/ for the audit trail; the harness script under scripts/ | a test covering the audit trail can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| Suite-floor guard amputation, every row killed | `scripts/ci-harness-gate.sh` | 2s (G) | check-suite-floor.sh | the floor guard dies quietly, everything green | INFRASTRUCTURE | **yes** |
| U4 client mutation controls, all killed | `scripts/ci-harness-gate.sh` | 497s (G) | src/ + tests/ for the HTTP client; the harness script under scripts/ | a test covering the HTTP client can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| U4 client amputation harness ran every row | `scripts/ci-harness-gate.sh` | 442s (G) | src/ + tests/ for the HTTP client; the harness script under scripts/ | a test covering the HTTP client can silently stop killing planted mutations; the suite stays green while no longer guarding what it names | PROJECT | **yes** |
| Secret scan hook runs clean | `scripts/check-secrets-baseline.py` | 25s (G) | .secrets.baseline + tree | a new secret-shaped finding lands unaudited | INFRASTRUCTURE | no |
| Advisory audit - the expiry half | `scripts/check_advisories.py` | 0s (G) | advisory-ignores table | an expired ignore silences advisories forever | INFRASTRUCTURE | no |
| Dependency audit | `scripts/check_advisories.py` | 6s (G) | uv.lock advisories via pip-audit | a known CVE ships in the frozen resolve | PROJECT | no |
| Capability drift report | `fastmcp inspect` | 2s (G) | server capability surface | a capability regression has no artifact to diff against | PROJECT | no |
| Upload the capability report | `actions/upload-artifact@v4` | 1s (G) | - | same, upload half | PROJECT | no |
| Coverage | `pytest` | 82s (G) | src/ coverage floors (fail_under=80, branch) | coverage rots below the ADR-0010 floor | PROJECT | no |
| ADR-0010's per-module coverage floors | `docs/reviews/check-coverage-floors.py` | 0s (G) | per-module floors from DESIGN.md | a critical path sinks under its floor behind a green aggregate | PROJECT | no |

### Job `codeql`

| step | runs | measured | watches | if it never runs again | class | gated |
|---|---|---|---|---|---|---|
| actions/checkout@v6 | `actions/checkout@v6` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| github/codeql-action/init@v3 | `github/codeql-action/init@v3` | 13-51s (G) | src/ security queries | static security analysis stops | INFRASTRUCTURE | no |
| github/codeql-action/analyze@v3 | `github/codeql-action/analyze@v3` | 13-51s (G) | src/ security queries | same | INFRASTRUCTURE | no |

### Job `wiring-probe`

| step | runs | measured | watches | if it never runs again | class | gated |
|---|---|---|---|---|---|---|
| actions/checkout@v6 | `actions/checkout@v6` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | `astral-sh/setup-uv@v5` | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | `actions/setup-python@v5` | ~0s | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | `uv sync` | 2s (G) | uv.lock | prologue; drift caught by later steps | PROJECT | no |
| The probe's arms all still fire | `docs/reviews/probe-wired-checker-amputation.py` | 9s (L) | check-checkers-are-wired.py amputations | the wiring checker cannot fail and nobody knows | INFRASTRUCTURE | no |
| That probe's own floor still fires | `docs/reviews/probe-wired-checker-amputation.py` | 1s (L) | probe-wired-checker-amputation.py floor | the probe rots row by row | INFRASTRUCTURE | no |
## 7. What I could NOT settle

- **No CI run of the gated workflow has executed.** DO NOT PUSH stood for
  this whole task (a queued run, then Phil's clean run 33602302499).
  Everything above is actionlint plus local execution of every step body I
  changed; the `changes` job's live behaviour on a real push event -
  `github.event.before` resolution on the runner in particular - cannot be
  settled without a push. 661acfe is in the same position.
- **The docs-only skip path has never fired anywhere.** The first docs-only
  push after this merges is the positive control for the whole lever: watch
  that run for the ::warning:: and the 41 skipped steps.
- **Cold-cache product-path timing on a runner.** 222s is from a run with a
  warm uv cache; a cache-miss run was not available to measure.
- **Whether GitHub bills a skipped step at zero.** Assumed (skipped steps do
  not execute); the ~9 billed-minute figure is wall-clock arithmetic plus
  per-job rounding, not a billing-API readback.
- **The two corpus gates.** check-clause-citations and
  check-standards-citations exit 2 here (no sibling corpus on this box),
  exactly as on every runner - nothing about them can be settled until
  STANDARDS_TOKEN exists (#106).

## 8. Merge

Branch `ci/237-audit`, one commit on top of 661acfe. Worktree left in place
at `/tmp/w237-ci-audit`.

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
      merge --no-ff ci/237-audit

Hold any push until run 33602302499 concludes - never push over a queued run.
