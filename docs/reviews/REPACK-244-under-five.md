# REPACK-244: the queue gap, measured, and what it costs to meet the mandate

Task #244, branch `ci/242-under-five`, worktree
`/home/plafayette/claude_projects/evolv/fmj-worktrees/w244`, off `main` at
`5cca9eb`.

Phil, verbatim: "FULL CI IS NOT TO TAKE MORE THAN 5 MINS WHEN REVAMP IS
DONE." "ci is for the fucking project code, not the docs." Full CI means
every check on every trigger, nothing gated away, nothing moved off the push
path. Deleting or skipping a check is not an acceptable answer, and nothing
below deletes one.

Figures are marked **(G)** where they are read from the GitHub API for run
`33610211810` (head `cb625f3`), **(L)** where I measured them locally this
session, and **(P)** where they are a prediction. **This branch has not been
pushed, so no wall-clock figure for the new shape is a measurement.**

---

## 1. THE QUEUE GAP, MEASURED - and the ceiling is not ours

REVAMP-238 §7 recorded 306s of run 33610211810's 846s wall that no job's
duration explained, and named runner queueing as an unverified hypothesis.
It is right, and here is the measurement. Per-job `started_at` minus the
run's `run_started_at`, from `/actions/runs/{id}/jobs` (G):

    12 jobs started within 4s
     1 job  (Harness U10 + U12)          waited  30s
     1 job  (Harness gate, floor, misc)  waited  51s
     1 job  (Harness U3 controls)        waited  56s
     1 job  (Harness U5 + U8)            waited 305s   <- the whole gap

The 306s is one job's wait. Wall 846s = 305s queued + 540s running, and the
pole job is the one that was queued longest. `q_own` (started_at minus
created_at) is 304s for that job, so it was created with all the others and
simply did not get a runner: not a `needs:` edge, a genuine wait.

**The concurrency ceiling, named.** `GET /orgs/evolvconsulting` reports
`plan.name = "free"`. GitHub's hosted-runner concurrency on the Free plan is
an **organisation-wide** limit, and this organisation contains ~100
repositories, so the ceiling is shared with every other repo in it and is
not a property of this one. What we can say from measurement is the
**observed** capacity: 12 runners at once, a 13th within 30s, a 16th only
after five minutes.

**This is n=1 and I want to be exact about that.** I checked the last 100 CI
runs: `33610211810` is the ONLY run this repository has ever had with 16
jobs. Every other recent run has 4. So the queue profile above rests on a
single observation, and the honest statement is "12 is what we got, once",
not "12 is the ceiling". A second 16-job run would settle it; I cannot make
one.

**The consequence for strategy, which is the point of measuring it:** the
brief's option (c), widening the fan-out, is refuted by its own premise.
Adding jobs past the observed capacity does not add parallelism, it adds
queue, and the 16th job's 305s wait is what that costs. The fan-out has a
ceiling and it had never been measured before being adopted.

## 2. WHAT THE BRIEF GOT RIGHT, AND WHAT IT GOT WRONG

The brief asked to be corrected. Four corrections, one of them large.

**§C claim 1 - "rebalancing alone cannot meet the mandate" - HOLDS, and the
real reason is stronger than the one given.** The brief argued from the
average: 3869s over 12 jobs is ~322s, over 300. True, but the binding
constraint is not the average, it is **the largest single step**. A step
cannot be split across runners, so wall >= max(step). `check-u3-audit-
amputation.sh` is 332s (G) on its own. No packing, and no number of jobs,
puts a run containing that step under 300s. The brief's arithmetic reached
the right verdict by the wrong route.

**§C claim 2 - the 306s gap - CONFIRMED**, and its hypothesis was right:
runner queueing. See §1.

**Lever (d), #241's single `--cov` run, IS ALREADY SPENT.** The brief lists
it as available. It landed in `620407f` ("One --cov suite run"), which is on
`main`. Run 33610211810's `test` job has exactly one `Default suite, zero
skips` step at 123s. There is no second suite run left to remove.

**Lever (a) rests on a proxy that does not measure what it is read as.**
REVAMP-238 §7 says "of 33 real `ci-harness-gate.sh` calls in ci.yml, 16
carry `--row-re` and 17 are bare", and reads the bare 17 as the ones that
"never received the per-row selection". `--row-re` is a ROW-COUNTING flag
passed to the gate; it says nothing about whether the harness selects tests
per row. Measured by reading the harnesses instead: eight controls harnesses
(U5, U8, U10, U12, U14, U9, U7, body-cap) were ALREADY running one selected
test per row and had been all along. The population needing selection was
much smaller than the proxy suggested - and, as §3 shows, the cost in those
eight was never test execution at all.

## 3. WHAT THE COST ACTUALLY IS

#240 measured that execution is 96.6% of a harness row and that per-row
selection holds the verdict. That is true of the rows it sampled. It is not
true of the eight controls harnesses above, and the difference decides the
whole task.

Measured (L) on this tree:

    pytest, whole 3-file U3 suite                9.28s
    pytest, same suite, `-k <one test>`          0.24s
    pytest, one test file, collect-only          1.10s
    `uv run --frozen` overhead per call          0.02s

Two things follow. First, `uv run --frozen` is NOT a per-row tax - I
expected it to be and it is not, 0.02s. Second, once a row already runs one
test, what remains is **process startup and collection**, roughly 1s per
pytest invocation. And each of those eight harnesses was starting **two**
pytest processes per row: a `--collect-only` pre-flight on the intact tree,
then the real run.

So the lever in those eight is not narrower selection. It is one fewer
process.

## 4. WHAT CHANGED

Two commits, both on `ci/242-under-five`.

### `eceeadf` - U3 controls selection, and the pre-flight

**U3 controls** ran the whole three-file `$SUITE` for each of 15 rows, to
answer a question its verdict has always narrowed to one named test. Now
`-k "$want"`. **176s -> 19s (L)**; the runner step was 488s (G), the
second-largest job in the run.

`-k` rather than a `::` node id, because M7's `test_arm3` and M11's
`test_case2` each name three tests deliberately and a node id refuses both.
My first version derived the defining file by grep and demanded exactly one
match; it reported those two rows as unlocatable, which is how I learned
they were prefixes and not truncations.

The verdict was `grep -q "$want"` over the whole output, **unanchored**. It
is now the anchored `FAILED` line for a node whose test name starts with
`$want`. **AMPUTATION, run both ways:** with `$want` set to `tests` - a
string present in every FAILED line's PATH and not a test name at all - the
**pre-fix code exits 0 and prints "15 killed, 0 not killed, status=ok"**. A
complete false green, 176s spent to produce it. The new code exits 1. A
renamed killer gives rc=5 and is reported rather than counted.

**The pre-flight**, in eight harnesses. The property it bought - "the named
test still exists, so a rename cannot report KILLED forever while testing
nothing" - is kept. The second process is gone. u8: **64s -> 33s (L)**,
25/25 rows still firing.

**My first rule for it was wrong, and U14 caught it.** I read pytest rc 4 or
5 as "the selector did not resolve". But U14's M7 mutates `GetJobFeedInput`
onto an undefined base, the module fails to import, and pytest exits 4 for
that too - a real kill, reported as a broken harness. Measured, three ways:

    absent node id          rc=4   `ERROR: not found: <path>`
    `-k` matching nothing   rc=5   "N deselected"
    mutation breaks import  rc=4   `ERROR: found no collectors for ...`
                                   AND `ERROR <file> - NameError: ...`

The discriminator is the collection-error line, not the exit code. Both
directions are proved on u8: a genuinely renamed selector still gives 24/25
rc=1, **identical to the pre-fix code**; U14 M7 is still a kill, 20/20.

All nine changed harnesses, through `ci-harness-gate.sh` with ci.yml's exact
flags, every row firing, exit codes on their own lines (L):

    u8c   rc=0  35s  25/25    u9c    rc=0  26s  14/14
    u5c   rc=0  24s  16/16    u7c    rc=0  22s  31/31
    u12c  rc=0  26s  17/17    bcapc  rc=0  19s  12/12
    u10c  rc=0  31s  21/21    u3c    rc=0  19s  15/15 killed
    u14c  rc=0  21s  20/20

No row floor moved: every row count is unchanged, which is the point.

`SELECTOR_TIMEOUT` is deleted where nothing reads it any more. ShellCheck
SC2034 found all eight; two harnesses keep theirs because they still use it.

### `735b1e4` - the fan-out, re-packed by measured cost

16 jobs -> 12. **All 76 gate invocations are byte-identical before and
after** (the parsed `run:` bodies diff empty). The only step-count change is
15 `Install uv` / `Install from the frozen lock` pairs becoming 11.

Twelve jobs, not more, because twelve is what the run actually got a runner
for within 4 seconds (§1). Packed LPT by measured per-step cost rather than
by unit name: the old split was 23s to 540s, a 23x spread, so one runner set
the wall while the rest sat idle. The new lanes are 360, 361, 366, 366, 368,
362, 360, 366. A lane is no longer "one unit", so each is named for what it
carries.

## 5. THE PREDICTED WALL (P), WITH THE ARITHMETIC

Runner scaling, derived from four harnesses I did **not** change - local on
this box today against their runner times in run 33610211810 (G):

    u3-amputation  124s L -> 332s  x2.68
    u9-amputation  141s L -> 249s  x1.77
    u5-amputation   24s L ->  85s  x3.54
    critical-cov    87s L -> 215s  x2.47

The spread is 1.77x to 3.54x, and it is not noise: the startup-dominated
steps scale worst. The changed steps are now MORE startup-dominated than
anything in that list, so the prediction below uses **x3.54**, the worst
observed factor. That is deliberately conservative - it predicts a bigger
wall, not a flattering one.

    step    was (G)    now (P)
    u3c        488         67
    u8c        214        124
    u10c       176        110
    u12c       150         92
    u5c        139         85
    u14c       132         74
    u9c        123         92
    u7c        104         78
    bcapc      100         67
    TOTAL     1626        789      saving (P) 837s

    harness lane total   3740s (G) -> 2909s (P)
    largest lane          540s (G) ->  368s (P)

    WALL (P) = 4s (start) + ~12s (checkout/uv/sync) + 368s = ~384s = 6.4 min

Against 846s = 14.10 min (G). A 2.2x improvement, and **it misses the
mandate by 1.28x.**

### Verify it with

    ID=<the run id for this branch's first push>
    gh api "repos/:owner/:repo/actions/runs/$ID" \
      --jq '{run_started_at, head_sha}'
    gh api "repos/:owner/:repo/actions/runs/$ID/jobs?per_page=100" --jq \
      '.jobs[] | {name, started_at, completed_at}'

Wall is `max(completed_at) - run_started_at`. Per job, `started_at` minus
`run_started_at` is the queue wait: **if all 12 start within a few seconds
the packing holds; if any lane waits, the shared ceiling moved and the
packing has to be redone against the new number.** Do not use
`gh run view --json jobs` - it carries no step timestamps.

## 6. WHAT I COULD NOT GET UNDER 300s, AND WHY

**`check-u3-audit-amputation.sh`, 332s (G), one step.** It is the whole
remaining gap. With it, the floor is ~348s no matter how the fan-out is
arranged; without it the next pole is u9-amputation at 249s and the mandate
becomes reachable.

**It cannot take the selection its own controls file just took, and this is
a refusal with a reason, not an omission.** U3 controls asks "did the NAMED
test notice", so running only that test asks the identical question. U3
amputation's product is its **survivor list**: every assertion that still
reported success against the amputated tree, printed for a human to read and
explain. Its own closing line says so - "Survivors are the OUTPUT. Read each
one and say why it survived." Narrowing the run to the covering set would
shrink that population by construction, and the report would say less while
CI stayed green, because the CI gate reads `rows` and `applied`, not
survivors. That is the exact shape this project keeps getting caught by: a
green gate that no longer covers what it used to. Making that step cheap
needs a decision about what the survivor report is FOR, and that is Tier 0's
call, not mine to take inside a performance task.

The other three steps over 200s - u9-amputation 249s, critical-path coverage
215s, u1-boot-amputation 208s - all fit under a 300s wall once U3's
amputation is dealt with, so none of them needs anything today.

## 7. WHAT I DID NOT VERIFY

- **No run of this shape has executed.** Every figure in §5 is (P). The
  first push is the positive control.
- **The concurrency ceiling is n=1.** One 16-job run exists in the last 100.
  "12 runners at once" is one observation, not a measured limit, and the
  Free-plan ceiling is shared org-wide with ~100 repositories, so it can
  differ run to run for reasons that have nothing to do with this repo.
- **x3.54 is the worst of four ratios, not a law.** If the real factor for
  the changed steps is nearer x2.7, the largest lane is ~280s and the wall
  ~296s - which would MEET the mandate. I did not predict that number
  because I have no basis for choosing the kinder factor.
- **The eight pre-flight removals are proved in both directions on u8
  only.** The other seven are proved green with every row firing, which is
  weaker: it shows nothing broke, not that each still catches a rename.
- **`check-u1-boot-controls.sh` and `check-u6-paging-controls.sh` still
  carry the pre-flight.** Their verdict blocks have a different shape and I
  did not convert them; u1c is 116s (G) and u6c 47s (G), so neither is on
  the critical path today.
- **REVAMP-238 §7's `--row-re` sentence is left as written.** It is a dated
  record of that task and citations there are as-at acceptance (ec57a65).
  The correction is §2 of this document, not an edit to that one.
