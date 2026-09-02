# AUDIT-237: the complete CI audit, and the restructure priced in minutes

Task #237. Phil, verbatim: "ci is for the fucking project code, not the docs.
clean that shit up, I want a complete audit done." And mid-task: "why would I
never even go over 5 mins TOTAL? THIS IS A TOOL."

Written by `blackthorn-ci` on branch `ci/237-audit`, worktree
`/tmp/w237-ci-audit`. Main moved TWICE while this ran - `661acfe` (path-gated
harnesses) and then `5699c31` (harnesses off the push path entirely,
schedule/dispatch only). This document audits the structure as it stands at
`5699c31`, reviews both commits (section 4), and this branch fixes what those
reviews found (section 5). An earlier revision of this audit against 661acfe
is preserved at branch `ci/237-audit-661acfe`; its H2/M1/L1/L2 findings died
with the `changes` job and are recorded in section 4 as history.

Timing sources, marked per row: **(G)** = per-step wall-clock from the one
fully green full run `33582613697`; **(L)** = measured locally this session
(uv 0.11.3, Python 3.12.3) for steps added since. The post-restructure push
number is not modelled: run at `5699c31` went GREEN IN 4.7 MINUTES (#234).

## 1. The headline arithmetic, measured

From run 33582613697 (the full shape), summing per-step timestamps:

    job                                    wall      steps then
    Lint, types, tests                    5191s      66
    CodeQL                                  67s      3
    Static gates, supply chain and links    44s      27
    wiring-probe (run 33586402689)         ~17s      6
    -------------------------------------------------------
    run wall-clock = the test job's        86.5 min

Inside the test job's 5191s: the 41 steps now schedule-only measured 4980s =
83.0 min; everything else ~211s. The task's "1 minute of product tests"
understated the product path: suite 83s (G) + coverage 82s (G) + mypy 9s +
audits/quickstart/collect = ~3.7 min. Locally the suite is 54s; the ratio
(product ~4%, harness apparatus ~96%) is what held, not the absolutes - a
loaded run of the old shape took 161 min.

Run history, because absence is a finding: of 285+ concluded CI runs, 3 have
ever been green - 33582613697 (full, 86.5 min), 33586402689, and the
4.7-minute run at 5699c31. ~93 failed, ~187 were cancelled by push-over-push
superseding, billed regardless.

## 2. The partition - all 110 steps classified (table, section 6)

- **PROJECT (47)**: the product must not ship without it - including the 28
  U-harness steps, deliberately: what they WATCH is src/ and tests/. The
  lead's guess that they are docs-adjacent tax is wrong; their defect was
  CADENCE (83 min re-answering a question that changes only when the code
  they mutate changes), and 5699c31 fixed the cadence, not the class.
- **INFRASTRUCTURE (43)**: CI/supply-chain correctness - floors, anchors,
  the harness gate's own controls, actionlint, SBOM, secret scan, CodeQL,
  mirror liveness. Nearly all 0-7s, correctly always-on.
- **CONVENTION (20)**: prose and record integrity - citations,
  cross-references, obligations, ADR numbering, plan measurements,
  brief-report references. **Measured total: ~30 seconds.** Phil's complaint
  is right about what CI gates on and wrong about where the minutes went:
  the docs checkers cost half a minute; the 83 minutes were PROJECT-class
  harnesses running on every push.

Two CONVENTION steps are INERT on every runner (exit 2, private standards
corpus, #106): "Standard clause citations resolve" and "Standards citations
resolve". They have never gated anything in CI.

`check-design-freeze.py`, which the lead flagged as possibly project-class:
its SUBJECT is prose, its INVARIANT is governance (only an ADR moves the
design). Classified CONVENTION, kept always-on at 0s (G).

If a class never runs again: PROJECT - the product breaks and ships.
INFRASTRUCTURE - a gate goes vacuous and its next green lies. CONVENTION -
**a document becomes internally inconsistent**, said plainly. Real on a repo
whose docs outweigh src 3.66x; priced at ~30 seconds, not 83 minutes.

## 3. The structure at 5699c31, and what this branch adds

5699c31: 41 harness steps carry
`if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`;
the `changes` job is deleted; the push path is setup, lint, format, types,
the floored 888 suite, coverage, security, and the fast static checkers.
Steps stay in ci.yml - correct, and independently verified here:
`check-row-floors.py:48` and `check-row-floor-exactness.py:137` pin
`.github/workflows/ci.yml` by path, so relocation strands them.

**Measured before/after, ANY push**:

    BEFORE  86.5 min wall (green run; 161 min observed under load)
    AFTER   4.7 min wall - MEASURED, the green run at 5699c31 (#234)
    SAVING  ~82 min per push (~95%), docs and code pushes alike

**Answers to the lead's direct questions:**

- *"Attack my selector - which steps did I gate that should not be, which
  did I leave that should be gated?"* Under schedule-only gating the
  path-subject mismatches I found in 661acfe are MOOT - nothing depends on a
  path filter any more. Checked all 41 against the harness inventory: the
  set is exactly the mutation/amputation harnesses plus their controls, no
  more, no less. Two judgement calls both come out fine: the cheap
  harness-integrity controls (~50s total: stranded-mutation, gate-state,
  anchor/mirror/gate controls, U11, U15, suite-floor amp, log redaction)
  are gated with their expensive siblings - acceptable because the STATIC
  guards (anchors resolve, row floors, exactness + self-arms, sigpipe,
  landing) stay on every push and notice rot cheaply; and nothing ungated
  re-runs the suite except Coverage, which is product path and fits the
  5-minute ceiling. No misgated step found.
- *"Does the ~85 min figure hold per-step against the new structure?"* Yes:
  the 41 schedule-only steps sum to 4980s = 83.0 min against the green run's
  per-step timestamps, and 86.5 - 4.7 = 81.8 min measured end to end.

**#143 interplay, checked as ordered**: #143's lever was job-count rounding
(634 -> 214 measured there). This lever is per-step execution inside
surviving jobs; no folded job is re-split, job count is unchanged at 4, the
savings do not double-count.

**What this branch adds on top of 5699c31** (each from a section-4 finding):

1. **The nightly cron that two commits claimed and neither added.** 661acfe
   and 5699c31 both say the harnesses "run nightly at 06:00 UTC"; the only
   cron was `0 0 * * 0` - weekly, Sundays. The 41 schedule-only steps were
   therefore running WEEKLY: max staleness 7 days where every reader was
   told 1. Added `- cron: '0 6 * * *'`. Cost: the full ~86-min sweep runs
   nightly (~600 billed min/week); that is the design Phil accepted twice.
   Prefer weekly? Delete the new cron line AND fix both commit messages'
   claim where it is restated in comments.
2. **The visible-weakening step (#231's open half, a non-negotiable in the
   task).** 5699c31 made EVERY push green the narrower claim and deleted
   the ::warning:: that said so. Added a 0s always-on push/PR step, "What
   this push green does and does not certify", printing exactly what the
   green covers and that the 41 harness steps run on the sweep. Skipped
   steps are visible only to a reader who opens the job; this line is for
   the one who does not. The badge residual stays with #231.
3. **The latent test defect that blocks job-level fan-out.**
   `tests/test_workflow_contexts.py`'s CONTEXT regex read every `word.` as
   a context, so the VALID `needs.<job>.outputs.<name>` job-level form -
   whose `needs` context its own allowlist permits - failed on its path
   segments. Measured: my 661acfe-era job-level variant failed the test
   while actionlint passed rc=0; 5699c31's step-level `if:`s dodge it by
   accident. Fixed with a `(?<!\.)` lookbehind plus a two-direction control
   (R3-H1's exact expression still caught). Suite 887 -> 888, floor raised
   in ci.yml, its one home.
4. **Five stale "NEVER EXECUTED" comments** (SBOM x2, secret scan, lychee,
   CodeQL banner) rewritten in place with the run id - all executed green
   in 33582613697. The mirror-push one is still true and stands.

## 4. Review of 661acfe and 5699c31

661acfe (superseded; findings recorded because they are the audit trail):
H1 nightly-schedule claim false (still false at 5699c31, fixed here);
H2 trigger pattern missed harnesses whose subjects live under docs/reviews
and docs/DESIGN.md|OBLIGATIONS.md (moot - the pattern is deleted);
M1 a git failure yielded code=false and SKIPPED, against its own fail-open
rule (moot); L1 checkout@v4 odd pin (moot); L2 `${{ }}` interpolated into
run blocks (moot). The lead's own actionlint catch (needs edge missing on
static-gates) is confirmed fixed in the landed version.

5699c31: F1 the nightly claim repeated, cron still weekly (fixed here, item
1 above); F2 the weakening made permanent AND invisible - the warning
deleted with the changes job (fixed here, item 2); F3 correct and worth
saying: gating in place preserved every ci.yml-parsing checker, all
re-verified at rc=0 on this tree.

This file deliberately carries NO REVIEW-COVERS declaration:
check-review-coverage.py's population regex is `REVIEW.*-R<n>`, so a
declaration here would be read by nothing - a false presence. Both commits
still show NONE in the coverage report and belong in R23's range; this
section is R23's input for them.

## 5. Verification of this branch (every exit code on its own line)

    actionlint (pinned 1.7.7, SHELLCHECK_OPTS=--severity=warning)   rc=0
    ruff check / ruff format --check / mypy                         0 / 0 / 0
    pytest default suite                     888 passed, 0 skipped, rc=0
    check-suite-floor.sh 888                 "888 passed, floor 888" rc=0
    check-checkers-are-wired.py (+ --self-test)                     0 / 0
    check-row-floors.py / check-row-floor-exactness.py (+ --self-test)  all 0
    check-harness-anchors.py --self-check --floor 464               rc=0
    check-no-sigpipe-pipelines / check-no-errexit / check-landing-published  all 0
    check-timeout-literals / check-pytest-bounded / check-env-vars  all 0
    check-obligations (+ --controls)                                0 / 0
    probe-ci-checker-steps.py                                       rc=0

Run after every structural change, not once at the end.

## 6. The complete step table - all 110 steps at this branch's tip

"schedule-only" = carries the 5699c31 gate (runs on the nightly sweep, the
weekly Sunday sweep, and workflow_dispatch - never on a push).

### Job `static-gates`

| step | measured | watches | if it never runs again | class | schedule-only |
|---|---|---|---|---|---|
| actions/checkout@v6 | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | 0s (G) | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | 2s (G) | uv.lock | prologue | PROJECT | no |
| Lint the workflows | 1s (G) | .github/workflows/* | the next R3-H1-class expression error ships unlinted (119 silent failures last time) | INFRASTRUCTURE | no |
| Coupling gate | 0s (G) | DESIGN.md vs src/tests | a design-coupled test is deletable with the design still claiming it exists | CONVENTION | no |
| The design at its declared freeze is the design on main | 0s (G) | DESIGN.md vs DESIGN-FREEZE.txt | the frozen design and its pointer drift apart unnoticed (happened for a day once) | CONVENTION | no |
| No harness enables errexit | 0s (G) | scripts/*.sh | a harness gains set -e; its timeout arms become dead code silently | INFRASTRUCTURE | no |
| Every harness emits the canonical HARNESS-RESULT line | 1s (G) | scripts/*.sh output contract | a harness stops emitting its machine line; downstream gates read nothing | INFRASTRUCTURE | no |
| Every checker is wired, or says why it is not | 1s (G) | workflows vs docs/reviews+scripts | a checker is built, cited as a gate, and never runs - 6 instances so far | INFRASTRUCTURE | no |
| The wiring checker's own controls still fire | 0s (G) | check-checkers-are-wired.py | the wiring gate itself can no longer fail | INFRASTRUCTURE | no |
| No abort message retypes a seconds figure | 1s (G) | scripts/ abort messages | an abort message lies about its timeout after a retune | CONVENTION | no |
| Design citations have a plausible shape | 0s (G) | DESIGN.md citations | citations point at blank lines again (47 found at wiring) | CONVENTION | no |
| Standard clause citations resolve | 0s (G) | OBLIGATIONS.md clause column | INERT in CI (exit 2, no corpus, #106) - certifies nothing on a runner today | CONVENTION | no |
| Every env var is declared | 0s (G) | workflow env usage | a step reads an undeclared env var and dies at runtime | INFRASTRUCTURE | no |
| Every Settings field is consumed by something | 0s (G) | src/ config.py | a declared setting ships that no code reads | PROJECT | no |
| Standards citations resolve | 0s (G) | inline standards citations in src/tests/scripts | INERT in CI (exit 2, no corpus, #106); 13 of 88 were wrong once | CONVENTION | no |
| Section cross-references resolve | 1s (G) | docs internal SSn.m refs | a document becomes internally inconsistent - plainly, that is all | CONVENTION | no |
| Coupling controls, all fired | 1s (G) | check-coupling.py + DESIGN.md | the coupling gate can pass without being able to fail | CONVENTION | **yes** |
| Obligation anchors still resolve to their subjects | 0s (G) | OBLIGATIONS.md anchors into pyproject/ci/env | the obligations map decays the moment a unit edits an anchor file | CONVENTION | no |
| Obligation checker controls, all fired | 1s (G) | check-obligations.py | same vacuous-green risk one level up | CONVENTION | **yes** |
| Plan measurements still reproduce | 8s (G) | IMPLEMENTATION-PLAN.md probe claims | a decision rests on a measurement that no longer reproduces | CONVENTION | no |
| Resweep verdicts agree with the document's own count | 0s (G) | CONFORMANCE-RESWEEP.md | a document contradicts its own tally; work gets assigned off a wrong population | CONVENTION | no |
| Coupling mutation sweep, no holes | 7s (G) | check-coupling.py hole-space | the coupling gate grows a hole nothing sweeps for | CONVENTION | **yes** |
| Licence gate | 0s (G) | uv.lock licences | a copyleft dependency ships - legal, not prose | INFRASTRUCTURE | no |
| SBOM (CycloneDX) | 4s (G) | .venv frozen resolve | no SBOM artifact for compliance consumers | INFRASTRUCTURE | no |
| SBOM (SPDX) | 3s (G) | .venv frozen resolve | same, SPDX side | INFRASTRUCTURE | no |
| Secret scan | 5s (G) | full git history | a committed-then-removed secret stays unnoticed in history | INFRASTRUCTURE | no |
| Relative links resolve | 1s (G) | **/*.md relative links | markdown links rot; prose integrity only | CONVENTION | no |
| The mirror workflow is still running | 1s (L) | mirror.yml run state via API | the mirror stops (60-day disable) and pushes go uncopied silently | INFRASTRUCTURE | no |

### Job `test`

| step | measured | watches | if it never runs again | class | schedule-only |
|---|---|---|---|---|---|
| actions/checkout@v6 | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | 0s (G) | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | 2s (G) | uv.lock | prologue | PROJECT | no |
| No lock drift | 0s (G) | pyproject vs uv.lock | a dependency edit without relock resolves differently later | PROJECT | no |
| Lint | 0s (G) | src/tests/scripts | lint rot ships | PROJECT | no |
| Format | 0s (G) | formatting | formatting drift | PROJECT | no |
| Types | 9s (G) | src/tests type surface | type errors ship | PROJECT | no |
| Default suite, zero skips | 83s (G) | THE PRODUCT: src/ via 888 floored tests, zero skips | the product breaks and ships - the one step the mandate is about | PROJECT | no |
| What this push green does and does not certify | 0s (L) | the reader of a push green | the narrowing 5699c31 made permanent goes back to being invisible (#231) | INFRASTRUCTURE | no |
| Network-dependent arms | 3s (G) | the fastmcp-slim pin negative arm | the pin constraint stops being tested | PROJECT | no |
| The README's Quickstart still works | 1s (G) | README.md commands, executed | the Quickstart lies to the first user | PROJECT | no |
| Docs-lint amputations, every row caught | 3s (G) | docs/reviews lint probes | the docs-lint probes go dead again (dead 45 commits once) | CONVENTION | **yes** |
| Collect the credentialed suite | 2s (G) | tests/credentialed imports | the credentialed suite rots uncollected | PROJECT | no |
| Harness anchors still resolve | 0s (G) | harness anchors vs src | a reformat kills an anchor; rows silently stop landing | INFRASTRUCTURE | no |
| Every DESIGN.md citation resolves to a line that exists | 0s (G) | DESIGN.md:N citations tree-wide | citations dangle after design edits | CONVENTION | no |
| Every harness is wired and has a row floor | 0s (G) | ci.yml + scripts floors | a harness loses its floor; rows become deletable green | INFRASTRUCTURE | no |
| Every checked row floor EQUALS its harness's live row count | 0s (G) | ci.yml --min-rows vs live rows | merge-produced slack returns (u14: 6 rows deletable) | INFRASTRUCTURE | no |
| The floor container's own arms | 0s (L) | check-row-floor-exactness.py | the exactness checker itself can no longer fail | INFRASTRUCTURE | no |
| No SIGPIPE-prone pipeline judges a gate | 0s (G) | ci.yml + scripts pipelines | a gate guard fails open on long output again | INFRASTRUCTURE | no |
| A harness that diagnoses a landing failure publishes it | 0s (G) | harness landing flags | a landing failure is published nowhere | INFRASTRUCTURE | no |
| Stranded-mutation control | 7s (G) | ci-harness-gate.sh state file | a killed harness strands a mutation unnoticed | INFRASTRUCTURE | **yes** |
| The gate records who is mutating | 0s (L) | ci-harness-gate.sh run-state | the restore machinery goes blind | INFRASTRUCTURE | no |
| The mirror refuses a zero-ref push | 0s (L) | mirror.yml guard, extracted | the mirror can force-push nothing over everything | INFRASTRUCTURE | no |
| Every report a brief cites is committed | 0s (L) | docs/briefs vs tracked reports | a 48KB report dies in a worktree again | CONVENTION | no |
| Controls for the brief-report reference gate | 1s (L) | check-brief-report-references.py | that gate goes vacuous | CONVENTION | **yes** |
| The bare-citation discriminator's controls | 0s (L) | probe-204-bare-citations.py | the discriminator goes vacuous | CONVENTION | **yes** |
| Harness anchor checker controls, all fired | 1s (G) | check-harness-anchors.py | the anchor checker goes vacuous | INFRASTRUCTURE | **yes** |
| Mirror liveness controls, all fired | 1s (L) | check-mirror-liveness.py exit codes | the liveness checker misclassifies mirror states | INFRASTRUCTURE | **yes** |
| Harness gate controls, all fired | 1s (G) | ci-harness-gate.sh 23 arms | the gate every harness step rides through rots | INFRASTRUCTURE | **yes** |
| U5 jobs controls, all fired | 43s (G) | src/ + tests/ for search_jobs; its harness under scripts/ | a test covering search_jobs can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U5 jobs amputation, every anchor applied | 31s (G) | src/ + tests/ for search_jobs; its harness under scripts/ | a test covering search_jobs can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U6 paging controls, all fired | 12s (G) | src/ + tests/ for offset paging; its harness under scripts/ | a test covering offset paging can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U6 paging amputation, every anchor applied | 5s (G) | src/ + tests/ for offset paging; its harness under scripts/ | a test covering offset paging can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U7 resilience controls, all fired | 31s (G) | src/ + tests/ for timeout/retry/breaker; its harness under scripts/ | a test covering timeout/retry/breaker can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U7 resilience amputation, every row applied | 72s (G) | src/ + tests/ for timeout/retry/breaker; its harness under scripts/ | a test covering timeout/retry/breaker can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U8 candidate controls, all fired | 66s (G) | src/ + tests/ for candidate reads; its harness under scripts/ | a test covering candidate reads can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U8 candidate amputation, every row applied | 33s (G) | src/ + tests/ for candidate reads; its harness under scripts/ | a test covering candidate reads can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U9 HTTP hardening controls, all fired | 45s (G) | src/ + tests/ for HTTP transport hardening; its harness under scripts/ | a test covering HTTP transport hardening can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U9 HTTP hardening amputation, every row applied | 1270s (G) | src/ + tests/ for HTTP transport hardening; its harness under scripts/ | a test covering HTTP transport hardening can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U12 job feed controls, all fired | 51s (G) | src/ + tests/ for get_job_feed redaction; its harness under scripts/ | a test covering get_job_feed redaction can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U12 job feed amputation, every row applied | 21s (G) | src/ + tests/ for get_job_feed redaction; its harness under scripts/ | a test covering get_job_feed redaction can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U10 write controls, all fired | 61s (G) | src/ + tests/ for the approval-guarded write; its harness under scripts/ | a test covering the approval-guarded write can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U10 write amputation, every row applied | 27s (G) | src/ + tests/ for the approval-guarded write; its harness under scripts/ | a test covering the approval-guarded write can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U14 argument sweep controls, all fired | 52s (G) | src/ + tests/ for the input models; its harness under scripts/ | a test covering the input models can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U14 argument sweep amputation, every row applied | 24s (G) | src/ + tests/ for the input models; its harness under scripts/ | a test covering the input models can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| Log redaction amputation, every row applied | 5s (G) | the ADR-0026 redaction install | the api key logs on httpx2 again unnoticed | PROJECT | **yes** |
| Body cap controls, all fired | 37s (G) | the 1 MiB ASGI body cap | the cap silently stops rejecting oversized bodies | PROJECT | **yes** |
| Body cap amputation, every row applied | 24s (G) | same, amputation side | same | PROJECT | **yes** |
| Critical-path coverage amputation, every row applied | 93s (G) | critical-path assertions | coverage stays 100% while asserting nothing | PROJECT | **yes** |
| ADR numbers are unique and contiguous, and the index matches | 0s (G) | docs/adr/ | two ADRs share a number; code cites an ambiguous decision | CONVENTION | no |
| U0 test controls, all fired | 927s (G) | src/ + tests/ for the test-infrastructure assertions; its harness under scripts/ | a test covering the test-infrastructure assertions can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| Every pytest invocation is bounded by a timeout | 0s (G) | scripts pytest calls | a hung suite eats the job ceiling | INFRASTRUCTURE | no |
| Committed file types, whole tree | 0s (G) | tracked file types | a --no-verify binary lives in the tree | INFRASTRUCTURE | no |
| U15 gate controls, all fired | 17s (G) | src/ + tests/ for the commit-time gates; its harness under scripts/ | a test covering the commit-time gates can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U15 gate amputation, every row applied | 4s (G) | src/ + tests/ for the commit-time gates; its harness under scripts/ | a test covering the commit-time gates can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U11 advisory controls, all fired | 6s (G) | src/ + tests/ for the advisory gate; its harness under scripts/ | a test covering the advisory gate can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U1 boot mutation controls, all fired | 118s (G) | src/ + tests/ for server boot (server.py); its harness under scripts/ | a test covering server boot (server.py) can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U1 boot amputation harness ran every row | 620s (G) | src/ + tests/ for server boot (server.py); its harness under scripts/ | a test covering server boot (server.py) can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U3 audit mutation controls, all killed | 190s (G) | src/ + tests/ for the audit trail; its harness under scripts/ | a test covering the audit trail can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U3 audit amputation harness ran every row | 131s (G) | src/ + tests/ for the audit trail; its harness under scripts/ | a test covering the audit trail can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| Suite-floor guard amputation, every row killed | 2s (G) | check-suite-floor.sh | the floor guard dies quietly, everything green | INFRASTRUCTURE | **yes** |
| U4 client mutation controls, all killed | 497s (G) | src/ + tests/ for the HTTP client; its harness under scripts/ | a test covering the HTTP client can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| U4 client amputation harness ran every row | 442s (G) | src/ + tests/ for the HTTP client; its harness under scripts/ | a test covering the HTTP client can silently stop killing planted mutations; the suite stays green while guarding less than it names | PROJECT | **yes** |
| Secret scan hook runs clean | 25s (G) | .secrets.baseline + tree | a new secret-shaped finding lands unaudited | INFRASTRUCTURE | no |
| Advisory audit - the expiry half | 0s (G) | advisory-ignores table | an expired ignore silences advisories forever | INFRASTRUCTURE | no |
| Dependency audit | 6s (G) | uv.lock advisories via pip-audit | a known CVE ships in the frozen resolve | PROJECT | no |
| Capability drift report | 2s (G) | server capability surface | a capability regression has no artifact to diff against | PROJECT | no |
| Upload the capability report | 1s (G) | - | same, upload half | PROJECT | no |
| Coverage | 82s (G) | src/ coverage floors (fail_under=80, branch) | coverage rots below the ADR-0010 floor | PROJECT | no |
| ADR-0010's per-module coverage floors | 0s (G) | per-module floors from DESIGN.md | a critical path sinks under its floor behind a green aggregate | PROJECT | no |

### Job `codeql`

| step | measured | watches | if it never runs again | class | schedule-only |
|---|---|---|---|---|---|
| actions/checkout@v6 | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| github/codeql-action/init@v3 | 13s (G) | src/ security queries | static security analysis stops | INFRASTRUCTURE | no |
| github/codeql-action/analyze@v3 | 51s (G) | src/ security queries | same | INFRASTRUCTURE | no |

### Job `wiring-probe`

| step | measured | watches | if it never runs again | class | schedule-only |
|---|---|---|---|---|---|
| actions/checkout@v6 | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| Install uv | 2s (G) | - | prologue | INFRASTRUCTURE | no |
| actions/setup-python@v5 | 0s (G) | - | prologue | INFRASTRUCTURE | no |
| Install from the frozen lock | 2s (G) | uv.lock | prologue | PROJECT | no |
| The probe's arms all still fire | 9s (L) | check-checkers-are-wired.py amputations | the wiring checker cannot fail and nobody knows | INFRASTRUCTURE | no |
| That probe's own floor still fires | 1s (L) | probe-wired-checker-amputation.py floor | the probe rots row by row | INFRASTRUCTURE | no |
## 7. What I could NOT settle

- **The nightly cron has never fired.** It was added on this branch; its
  first 06:00 UTC firing is its positive control. A cron in a workflow is
  also subject to GitHub's 60-day-inactivity disable, which the
  mirror-liveness step watches for the mirror but nothing watches for CI's
  own schedule.
- **The notice step has not run in CI** (DO NOT PUSH stood throughout);
  its body is a single echo, run locally, but the ::notice:: rendering on a
  real run is unverified until the first push after merge.
- **Whether GitHub bills a skipped step at zero** - assumed; the 4.7-min
  green at 5699c31 is the wall-clock evidence, not a billing readback.
- **Cold-cache product-path timing** - 4.7 min was one run; no cache-miss
  sample exists yet.
- **The two corpus gates** (clause/standards citations) exit 2 everywhere
  until STANDARDS_TOKEN exists (#106); nothing about them can be settled
  here.

## 8. Merge

Branch `ci/237-audit`, one commit on top of 5699c31. Worktree left in place
at `/tmp/w237-ci-audit`. The superseded 661acfe-based revision is at branch
`ci/237-audit-661acfe`; delete it after merge if unwanted.

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
      merge --no-ff ci/237-audit

Never push over a queued run.
