# Task #143 - per-job minute rounding

<!--
DELIBERATELY NO `REVIEW-COVERS` LINE. I drafted one and removed it. This
is an implementation worklog, not a review round: nobody has reviewed
these commits, so a declaration here would manufacture machine-readable
coverage for code no reviewer opened. PREAMBLE.md's own reasoning applies
directly - "an absence you can see beats a false presence you cannot".
These commits SHOULD show as uncovered until a reviewer declares them.
-->

Branch `fix/143-ci-minutes`, worktree `fmj-worktrees/w143`, cut from
`origin/main` at `9e04411`.

## What the measurement actually said

Tool: `evolv-coder-standards/scripts/ci-minutes.py`. It was reachable,
`--self-test` PASSES (20/20 checks, exit 0), and it already requests
`filter=all` - the trap the brief names is handled at its line 61-66 and
I confirmed it at line 326 rather than trusting the docstring.

Window `2026-08-28..2026-09-02`, `evolvconsulting/fast-mcp-jobvite`:
**578 runs, 1326 jobs, 2528 billable minutes.** Runner time actually
consumed was 1586 min, so **942 min - 37% of the bill - is per-job
rounding.**

### The five CI jobs, before

| job | n | billed | median | p90 | max |
|---|---|---|---|---|---|
| Lint, types, tests | 219 | 1283 min | 87s | 546s | 7522s |
| CodeQL | 220 | 354 min | 64s | 73s | 80s |
| Supply chain | 220 | 220 min | 26s | 31s | 39s |
| Design coupling gates | 220 | 220 min | 11s | 28s | 34s |
| Link check | 210 | 214 min | 6s | 8s | 126s |

## Corrections to the brief

**1. There is a SIXTH billed job, and the brief's ledger omits it.**
`Mirror to personal fork` billed **214 min over 214 runs at a median of
3s**. It consumed 11 minutes of runner time, so **95% of its bill is
rounding** - proportionally the worst job in the repository, worse than
any of the five the brief lists. It is a separate workflow file, outside
my mandate; reported, not touched.

**2. `Link check`'s max is 126s, not 9s.** The brief and the `timeout-minutes`
comment on the old job both said "observed max 9s". The median is 6s, but
the maximum over this window is 126s, and 4 of its 210 runs billed 2
minutes rather than 1 (214 billed over 210 runs). The 10-minute cap was
never in danger, but the stated observation was wrong by 14x.

**3. `CodeQL` is not a trivial job that rounding inflates.** The brief
lists it at "max 80s" alongside three sub-40s jobs. It is the
**second-largest line in the bill at 354 min**, and its median of 64s is
genuinely over the minute boundary - it is not a rounding artefact and
consolidating it away does not work the way it does for the other three.

**4. "Four of five jobs finish in under 90 seconds combined" holds** -
median 11+26+6 = 43s - but the brief's framing "bill four whole minutes"
counts CodeQL among them. Three of them bill three minutes; CodeQL's two
are mostly real.

## What I changed

`design-gates`, `supply-chain` and `links` are now one job, `static-gates`
("Static gates, supply chain and links").

**The ledger, per job, over the 210 run-attempts that carried all three:**

| | billed |
|---|---|
| BEFORE - `design-gates` + `supply-chain` + `links`, each rounded up | **634 min** |
| AFTER - one job, rounded up | **214 min** |
| SAVING | **420 min (66%)** |

**How the "after" was derived, since a modelled number needs its method
stated.** The jobs API returns per-STEP timestamps. For each run-attempt
I split every job's steps into prologue (`Set up job`, checkout, `Install
uv`, setup-python, `uv sync --frozen`, plus the `Post `/`Complete job`
steps) and work. The merged job is modelled as **one prologue (the
largest of the three) plus the sum of all three jobs' work steps** -
which is conservative, because it charges the merged job the slowest
observed prologue. Result: median 28s, p90 42s, max 148s, and only **2 of
210 run-attempts would cross 60s** and bill 2 minutes. Those two are
included in the 214.

**The second saving is the shared prologue.** `design-gates` and
`supply-chain` ran byte-identical prologues - checkout at `fetch-depth: 0`,
setup-uv with the cache, setup-python, `uv sync --frozen`. The merged job
runs it once.

**`fetch-depth: 0` was the trap the brief warned about, and it resolves
cleanly rather than by compromise.** Both merged jobs already required
full history for different reasons (the freeze gate resolves a SHA a
shallow clone does not contain; TruffleHog needs history to see a secret
removed in a later commit). `links` had the default depth 1 and does not
care. The merged checkout is the strictest of the three, so no job
inherits a *shallower* clone than it had.

## What I REFUSED

**Folding `CodeQL` in, and I have the number rather than a hunch.**
A four-way merge measures **423 min against the three-way's 557 over the
same 210 run-attempts - a further 134 min, 0.64 min/run.** That is real
money and I still refused it: CodeQL's `analyze` step scans the workspace,
and this job populates `.venv` via `uv sync --frozen` before it would run.
Changing what a **security** gate scans to save 0.64 min/run needs a
before/after on CodeQL's *findings*, not a note in a cost commit. Tier 0
can overrule this with the figure in front of it.

**This is a correction of my own first write-up.** The header comment I
committed at `8be39b4` said "saving ~1 min/run" and dismissed it. That
was an estimate standing where a measurement belonged; `9422844` replaces
it in place - in `ci.yml` and in the applier together - with the measured
134.

**Merging anything into `test`.** Median 87s, max 7522s. It is the long
pole; coupling a 5-second gate to a 2-hour matrix buys nothing.

**Narrowing the permissions.** The merged job takes the **union**:
`security-events: write` came from `supply-chain` and now also covers the
design-gate steps. That is a widening, it is stated in the header rather
than buried, and it is preserved unchanged rather than narrowed on a
guess - I did not measure whether TruffleHog and the SBOM steps need it
(they upload no SARIF, which is a reason to suspect they do not, not
evidence that they do not).

## Evidence the merge lost nothing

Step-by-step set comparison, before (3 jobs, 32 steps) vs after (1 job,
27 steps): **zero steps ADDED, and the only steps DROPPED are the
duplicated prologue** - 2 extra `actions/checkout`, 1 `Install uv`, 1
`setup-python`, 1 `uv sync --frozen`. All 23 real gate steps survive, in
order.

**Positive control - the green is not vacuous.** A green from the wiring
gate means nothing unless it can see a lost step, so I amputated one:
deleted the `Coupling gate` step from the merged job (asserting the anchor
was unique first). `check-checkers-are-wired.py` went to **exit 1** and
named `check-coupling.py`; `probe-ci-checker-steps.py` went to **exit 1**.
Restored, and `git diff --numstat` printed nothing - byte-identical to the
commit.

**The applier is replayable, and that is tested, not asserted.** Running
`scripts/apply-143-consolidation.py` against `ci.yml` as it stood at
`9e04411` in a scratch tree reproduces the committed file **byte-for-byte**
(`diff -q`, no output). It was re-run after the lint rewrite and again
after the CodeQL correction; identical all three times, which is what
keeps the applier and `ci.yml` from drifting apart.

## Gate exit codes, each on its own line

Run from the worktree, invocations copied out of `ci.yml`, not retyped.

```
actionlint (SHELLCHECK_OPTS=--severity=warning)   EXIT=0
check-coupling.py                                 EXIT=0
check-design-freeze.py                            EXIT=0
check-checkers-are-wired.py                       EXIT=0
check-design-citation-shape.py                    EXIT=0
check-cross-references.py                         EXIT=0
check-coupling-controls.py                        EXIT=0
check-obligations.py                              EXIT=0
check-obligations.py --controls                   EXIT=0
check-resweep-verdicts.py                         EXIT=0
check-coupling-sweep.py                           EXIT=0
check-env-vars-are-declared.py                    EXIT=0
check-no-errexit.py                               EXIT=0
check-settings-are-read.py                        EXIT=0
check-standards-citations.py                      EXIT=0
check-clause-citations.py                         EXIT=0
check-plan-measurements.py                        EXIT=0
check-no-sigpipe-pipelines.py                     EXIT=0
check-row-floors.py                               EXIT=0
check-row-floor-exactness.py                      EXIT=0
probe-ci-checker-steps.py                         EXIT=0
probe-ci-checker-steps-control.py                 EXIT=0
check-harness-result.sh                           EXIT=0
check-harness-anchors.py --self-check --floor 458 EXIT=0
check-committed-file-types.py --all               EXIT=0
Licence gate (pip-licenses, verbatim --fail-on)   EXIT=0
ruff check .                                      EXIT=0
ruff format --check .                             EXIT=0
mypy .                                            EXIT=0  (127 source files)
pytest tests/test_workflow_pins.py                EXIT=0
pytest tests/test_workflow_contexts.py            EXIT=0
pytest tests/test_file_type_gate.py               EXIT=0
pytest tests/test_suite_floor.py                  EXIT=0
uv run --frozen pytest (FULL default suite)       EXIT=0
check-suite-floor.sh 887                          EXIT=0
```

The full suite is the fold gate, so it was run whole rather than on the
adjacent files: **887 passed, 0 skipped, 6 deselected, 56.46s.**
`HARNESS-RESULT name=check-suite-floor.sh rows=887 floor=887 status=ok`.
The floor is EXACTLY met, not exceeded - this change adds no tests and
removes none, which is the expected shape for a workflow restructure.
CI's own zero-skips guard is `grep -qE '[0-9]+ skipped'`; run against the
captured output it matches nothing. "6 deselected" is not a skip.

Both floors were DERIVED from `ci.yml`, not retyped: `check-suite-floor.sh
887` and `check-harness-anchors.py --self-check --floor 458`.

## One gate is RED, and it is red on `origin/main` too

`docs/reviews/check-review-coverage.py` exits **1**. I checked whether
that was mine by running it from a detached worktree at `origin/main`:
**exit 1 there as well, with byte-identical counts** - 200 fully covered,
39 partial, 19 covered by nothing. So my branch neither causes nor worsens
it; it is the pre-existing state task #151 ruled on. It is also **not
wired into `ci.yml`** (`grep` finds no step), so it gates nothing today.
Reported rather than "fixed", because making it green is #151's call and
not a cost commit's.

## What I could NOT settle

- **The three supply-chain actions still have never executed.** `SBOM
  (CycloneDX)`, `SBOM (SPDX)` and `Secret scan` are GitHub-hosted actions
  that cannot run on a developer machine. Moving them between jobs does
  not change that, and their first real run is still their first evidence.
  The `Licence gate`, which *can* run locally, I ran (exit 0).
- **Whether `security-events: write` is needed by the supply-chain steps
  at all.** Not measured. Preserved as-is.
- **CodeQL's findings before and after a four-way merge.** That is the
  measurement my refusal above says is required, and I did not make it.

## What I did NOT attempt, as distinct from could not settle

- The `Mirror to personal fork` workflow (finding 1). Out of mandate.
- Any edit under `scripts/*.sh` - `suborch-116` was live on those.

## Anything I would have needed in `scripts/` - reported, not done

**Nothing.** The consolidation needed no `scripts/*.sh` change. The one
file I added under `scripts/` is a new `.py` applier, which collides with
nothing `suborch-116` was rewriting, and which is outside
`check-checkers-are-wired.py`'s container (that gate enumerates
`docs/reviews/check-*.py|sh`, verified by reading its docstring at lines
41-45, not by assuming).
