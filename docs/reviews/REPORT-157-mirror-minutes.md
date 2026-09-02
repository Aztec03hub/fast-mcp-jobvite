# REPORT — #157: the mirror job, re-measured, and what it is actually for

<!--
DELIBERATELY NO `REVIEW-COVERS` LINE, following WORKLOG-143's precedent
and for its reason. This is an implementation report, not a review
round: nobody has reviewed commit 4aca097, so a declaration here would
manufacture machine-readable coverage for a change no reviewer opened.
-->

Task #157. Branch `fix/157-mirror-minutes`, worktree
`fmj-worktrees/w157`, cut from `main` at `ccbdaae`. Commits `4aca097` (the change) and
`a3fc38f` (a correction to my own header, §4). One file changed:
`.github/workflows/mirror.yml`.

**THE DECISION, up front.** The mirror now runs on a **daily schedule
plus tag pushes plus `workflow_dispatch`**, not on every push. That is
not primarily a cost decision. It is that **the per-push trigger was
buying nothing at all**, and the measurement below is what shows it
rather than argues it.

---

## 1. The measurement, with its container

Window **2026-08-28T00:00:00Z .. 2026-09-02T00:00:00Z**, repository
`evolvconsulting/fast-mcp-jobvite`, workflow id `344103800`
(`.github/workflows/mirror.yml`). Two independent instruments.

**Instrument A — `evolv-coder-standards/scripts/ci-minutes.py`**, the
tool #143 used, run with the same flags. `--self-test` PASSES (20/20,
exit 0). I re-confirmed the `filter=all` request at its **line 326**
(`grep -n`), not from its docstring — the same check #143 records.

    Mirror to personal fork    mirror     n=216   216 bill   med 3s

**Instrument B — my own pull of `/actions/workflows/344103800/runs`
and `/actions/runs/{id}/jobs?filter=all`**, summarised independently:

    runs created in the window                         298
    ... of which billed NOTHING (zero jobs scheduled)   85
    ... of which scheduled a runner and billed         213
    billed minutes                                     213
    runner seconds actually consumed                   656  (10.9 min)
    per-run duration   min 2s   median 3s   p90 4s   max 8s
    rounding share of the bill                       94.9%
    runner labels                     ubuntu-latest, all 213
    re-run attempts (attempt > 1)                        0
    events                              push, all 298 of them
    head branches               main 277, 11 others 21 total

**HOW MANY RUNS REACHED THE STEP — the brief's question, and the
answer is the finding.** Per-step conclusions across all 213 billed
jobs:

    213  Set up job                          success
    213  Report whether the mirror is ...    success
    213  Run actions/checkout@v6             SKIPPED
    213  Push to mirror                      SKIPPED
    213  Complete job                        success

**Zero of 213 runs have ever executed the step that mirrors
anything.** Not "few" — zero, in every run in the window, because
`MIRROR_TOKEN` does not exist and the step-level guard correctly
skips. The 213 minutes bought 213 printed notices.

### The two instruments agree exactly, once the join key is right

216 (A) against 213 (B) is not a disagreement about the data; it is a
disagreement about the window. `ci-minutes.py --until 2026-09-02`
treats that date as **INCLUSIVE** — its own per-day table lists a
`2026-09-02` row. Three mirror runs happened on 2026-09-02 before I
measured. 213 + 3 = 216, and re-running my half-open window as
`2026-08-28 <= d <= 2026-09-02` returns **216**, exactly.

That also explains #143's `214` against my `213`: same measurement,
read at three different moments of a day that was still adding runs.
**Nothing in the conclusion turns on 213 vs 214 vs 216**, and saying
so is cheaper than pretending one of them is canonical.

### The distribution is boring, and that matters

Max 8 seconds against a `timeout-minutes: 10` cap. The failing-trunk
trap (#143's `Link check` 126s, the 50x case) does not apply here:
these 213 runs all *reached* every step they were going to reach, and
the two skipped steps are skipped by design, not by an early death.

---

## 2. What settles it is not the ratio

95% rounding is the worst ratio in the repository and it is still not
the reason to change this. Three measured facts are:

**(a) `MIRROR_TOKEN` does not exist, anywhere.** `actions/secrets`
returns `total_count: 0` at the repository, and
`actions/organization-secrets` returns `total_count: 0` for the
organisation. Re-checked 2026-09-02. So the job cannot push, and does
not.

**(b) The mirror is nevertheless completely current.** `git ls-remote`
against both remotes on 2026-09-02:

    evolvconsulting/fast-mcp-jobvite   20 refs
    Aztec03hub/fast-mcp-jobvite        20 refs
    diff of the two sorted ref lists   EMPTY

Twenty refs, identical SHAs on every one, including `HEAD` at
`ccbdaae`. The copy is delivered entirely by the two-push-URL `origin`
described in this workflow's own opening paragraph. Both repositories
are public, so this check needs no credential — which is why it is now
*inside* the workflow (§4).

**(c) Neither the design nor the decisions record a freshness
requirement.** `docs/DESIGN.md` §10 at the freeze (`5d17cd7`) says
only *"Canonical at `evolvconsulting/fast-mcp-jobvite`, mirrored to
`Aztec03hub/fast-mcp-jobvite`"*. `docs/DECISIONS.md` D8 says
*"Canonical on `evolvconsulting`, auto-mirrored to the personal
fork"*. Neither says how fresh the copy must be. **So per-push was an
unrecorded choice, not a requirement**, and changing the cadence is
not a change of contract and needs no ADR. If Tier 0 disagrees and
thinks D8's "auto-" implies per-commit, that is a ruling, not my call,
and reverting is one commit.

Put together: the per-push trigger paid a per-push price for a
per-push guarantee the job never delivered, and would, once
`MIRROR_TOKEN` exists, only duplicate a push that has already
happened.

---

## 3. What I changed, and what it costs

`on:` becomes `schedule` (`17 4 * * *`), `push: tags: ["**"]`, and
`workflow_dispatch`. Nothing else about the job's shape moves —
`concurrency`, `permissions: contents: read`, `timeout-minutes: 10`,
the step-level `env.MIRROR_TOKEN` guard, `actions/checkout@v6` at
`fetch-depth: 0`, and the push refspec are all unchanged.

| | over a window like this one (5 days) | per month |
|---|---|---|
| BEFORE — per push, at the observed rate | **213 min** | ~1300 min |
| AFTER — one scheduled run a day | **5 min** | **~31 min** |

**Tag pushes are kept, and their measured cost is 0.** Zero tags were
pushed in the window (298 of 298 push events were branch pushes), so
the trigger costs nothing today and buys prompt off-site copying at
the one moment it is worth a minute. That is a judgement, not a
measurement, and it is cheap to revert.

**04:17 UTC, off the hour, on purpose.** GitHub's cron is best-effort
and the top of the hour is its most contended slot. I did not measure
the delay; I state it as the reason for the offset rather than as a
finding.

---

## 4. How the next person notices it has stopped

This is #18's question and a schedule sharpens it, because nobody
looks at a cron the way they look at a red tick beside their own
commit. So the change is not only a trigger change.

**The unconditional first step now also reports whether the mirror is
CURRENT**, by `git ls-remote` against both remotes and diffing the
sorted ref lists. It prints one of three things on every run: the ref
count and "CURRENT"; a `::warning::` naming the two counts and the
diff; or a `::warning::` saying currency is UNKNOWN because a remote
could not be read. Properties worth stating:

- **It needs no token and no working mirror**, so it is meaningful
  today, while the job itself still copies nothing.
- **It would NOT have caught R3-H1, and my first draft of both this
  report and the workflow header claimed it would.** Those 119 runs
  died before any job was scheduled; no step of any kind ran, so
  nothing written inside a step could have spoken. What it adds is the
  **third state**: #18's fix separated *switched off* from *broken*,
  and this separates both from *running but copying nothing* — which
  is precisely the state this repository has been in for 213 billed
  runs with nobody saying so. I corrected the claim in the file at
  `a3fc38f` rather than leaving the stronger version standing.
- **It warns, it does not fail.** A step whose whole purpose is
  legibility must not go red on a transient network read, because that
  trains its reader to ignore it — the habit that let 119 failures go
  unread. The trade-off is stated in the file rather than left implicit.

**Two failure modes remain, and are named in the file rather than
hidden:**

1. GitHub disables a scheduled workflow after **60 days of repository
   inactivity** and emails the owner. That is a real way this stops
   quietly if the project goes dormant.
2. If the workflow stops being *run at all*, no run reports anything.
   Only a check outside this file can see that. **I did not wire one**,
   deliberately: #161 is closing the trunk's last red step and the
   brief says my work must not add a new one. Recorded as a follow-up
   below.

---

## 5. Corrections to my brief

**1. §D's third option is not available today, and it is the one the
brief marks "a legitimate answer".** It reads: *"Leave it and record
214 min as the deliberate price of an off-site copy."* There is no
off-site copy being made by this job. `MIRROR_TOKEN` does not exist,
all 213 runs SKIPPED both the checkout and the push, and the copy that
does exist was made by `origin`'s second push URL. The 214 minutes are
the price of **printing a notice**, and no wording of "record it
deliberately" makes that defensible. Had I taken the option as
offered, I would have recorded a price for a good that was never
delivered.

**2. §C's figures are right within the noise, but the window is
inclusive.** `n=214 / 214 min / median 3s / 11 min runner` against my
`213 / 213 / 3s / 10.9`, and `216` from the same tool run today. The
difference is entirely `--until`'s inclusive boundary plus the passage
of time, and I say so rather than picking a winner.

**3. §B says I own "`.github/workflows/<the mirror workflow file>`".**
The file is `.github/workflows/mirror.yml`; there is exactly one
mirror workflow, so nothing turned on this, but the brief left it as a
blank and blanks are where the wrong file gets edited. Naming it:
`mirror.yml`, id `344103800`.

**4. A smaller one about the brief's framing of "fold it into a job
that already checks out at depth 0".** The brief warns about the
credential. The stronger objection is different and it is not in the
brief: folding an off-site *backup* into a *gate* job couples the
backup to the gate's success. On a trunk that has never produced a
green run, that would mean the mirror stops exactly when the
repository is in the state you most want a copy of. I did not need to
resolve this — the schedule makes the fold moot — but the reason to
refuse it is stronger than the token.

---

## 6. Gate exit codes, each on its own line

Run from the worktree at `4aca097`, invocations copied out of
`ci.yml`, not retyped.

```
actionlint 1.7.7 (SHELLCHECK_OPTS=--severity=warning)  EXIT=0
check-coupling.py docs/DESIGN.md                       EXIT=0
check-design-freeze.py                                 EXIT=0
check-no-errexit.py                                    EXIT=0
check-checkers-are-wired.py                            EXIT=0
check-design-citation-shape.py                         EXIT=0
check-cross-references.py                              EXIT=0
check-coupling-controls.py                             EXIT=0
check-obligations.py                                   EXIT=0
check-obligations.py --controls                        EXIT=0
check-resweep-verdicts.py                              EXIT=0
check-coupling-sweep.py                                EXIT=0
check-env-vars-are-declared.py                         EXIT=0
check-settings-are-read.py                             EXIT=0
check-standards-citations.py                           EXIT=0
check-clause-citations.py                              EXIT=0
check-plan-measurements.py                             EXIT=0
check-no-sigpipe-pipelines.py                          EXIT=0
check-row-floors.py                                    EXIT=0
check-row-floor-exactness.py                           EXIT=0
check-design-citations.py                              EXIT=0
check-adr-numbers.py                                   EXIT=0
check-landing-published.py                             EXIT=0
check-harness-result.sh                                EXIT=0
check-harness-anchors.py --self-check --floor 458      EXIT=0
scripts/check-committed-file-types.py --all            EXIT=0
uv run --frozen pytest (FULL default suite)            EXIT=0
check-suite-floor.sh 887                               EXIT=0
```

**The suite: 887 passed, 0 skipped, 6 deselected, 59.36s.**
`HARNESS-RESULT name=check-suite-floor.sh rows=887 floor=887
status=ok`. The floor is EXACTLY met — this change adds and removes no
tests, which is the expected shape for a workflow trigger change.
CI's own zero-skips guard is `grep -qE '[0-9]+ skipped'`; run against
the captured output it matches nothing.

Both floors were **derived** from `ci.yml` by `grep -oE`, not retyped:
`check-suite-floor.sh 887` and
`check-harness-anchors.py --self-check --floor 458`.

The three workflow-specific tests, run individually as well as in the
suite: `test_workflow_pins.py` 4 passed, `test_workflow_contexts.py`
6 passed, `test_file_type_gate.py` 36 passed.

### The actionlint green is not vacuous — positive control

A green from a linter says nothing unless it can see a defect in *this
file*. I asserted the anchor `    - cron: "17 4 * * *"` was unique
(count == 1), replaced it with a six-field cron, and confirmed the
mutation LANDED by `git diff --numstat` (`1 1
.github/workflows/mirror.yml`). actionlint went to **exit 1**:

    .github/workflows/mirror.yml:83:13: invalid CRON format
    "17 4 * * * *" in schedule event: expected exactly 5 fields,
    found 6: [17 4 * * * *] [events]

Restored with `git checkout --`; `git diff --numstat` then printed
nothing (byte-identical to the commit) and actionlint returned to exit
0. So the linter reads this file, reads the block I changed, and my
cron is valid rather than merely unexamined.

### An instrument error of my own, caught and worth recording

My first run of the file-type gate used `docs/reviews/check-committed
-file-types.py` and got **exit 2** — because that path does not exist;
the script lives under `scripts/`. A search at a path that does not
exist exits clean and looks exactly like a real failure or a real
absence. The gate at its real path exits 0. I mention it because I had
the rule in front of me and still did it.

---

## 7. What I could NOT settle

- **Whether the push step works.** It has never executed — 0 of 213
  runs, and 0 of the 335 runs this workflow has ever had. Its refspec
  `+refs/remotes/origin/*:refs/heads/*` depends on
  `actions/checkout@v6` at `fetch-depth: 0` populating
  `refs/remotes/origin/*`, which I believe it does and did not verify
  in a live run, because verifying it requires creating
  `MIRROR_TOKEN` — a maintainer action, already in NEEDS-PHIL.md, and
  a write I am not permitted to make. **My change neither fixes nor
  worsens this**, and the new currency check is the first thing in the
  file that would notice if the push were wrong.
- **Whether a scheduled run's checkout behaves identically to a
  push-triggered one.** On `schedule`, `github.ref` is the default
  branch; `fetch-depth: 0` should make that irrelevant to a full
  mirror. Unverified for the same reason as above: no token, no live
  push.
- **Whether `cancel-in-progress: true` would have been a viable
  alternative** had per-push been kept. It plausibly collapses the
  bursts (167 runs on one day, 46 on another), but the saving depends
  on queue and run timing I did not model, and the schedule makes the
  question moot. Naming it so nobody re-derives it as a new idea.
- **The 60-day scheduled-workflow disable rule** is GitHub's
  documented behaviour, not something I measured here. It is stated in
  the file as a named hazard, not as an observation.

## 8. What I did NOT attempt, as distinct from could not settle

- **Anything in `.github/workflows/ci.yml`.** `suborch-161` is inside
  it. I read it (to copy the actionlint invocation and derive both
  floors) and wrote nothing.
- **Anything in `scripts/check-u1-boot-amputation.sh`** —
  `suborch-156`'s file. I ran `scripts/check-committed-file-types.py`
  and `scripts/check-harness-anchors.py`; neither is theirs.
- **Wiring an external "is the mirror still running at all" check.**
  Refused on purpose while #161 closes the trunk's last red step. See
  the follow-up below.
- **`check-coverage-floors.py`.** It requires `coverage.json`, which
  CI produces in the test job's `pytest --cov` run. My change touches
  no Python, so coverage cannot move; I did not spend a coverage run
  to prove a tautology. Stating it rather than listing a fake EXIT=0.
- **Creating, reading or printing any secret.** `MIRROR_TOKEN` is
  named throughout and its value was never fetched; the only secret
  API calls I made list `total_count` and names.

## 9. Follow-up worth a task row (Tier 0's call, not mine)

**A mirror that stops being copied is still invisible from outside a
run.** The new in-run currency check reports drift *when a run
happens*. Nothing notices if runs stop happening — the exact shape of
#18, one level up. The cheap version is a step in the existing CI job
that does the same `git ls-remote` diff and warns; it needs no
credential, both repositories being public. **It must land after #161
turns the trunk green, not before.**
