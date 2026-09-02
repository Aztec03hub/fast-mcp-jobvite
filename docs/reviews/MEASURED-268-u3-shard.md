# MEASURED-268: sharding `check-u3-audit-amputation`'s ten rows

Branch `ci/268-u3-shard`, based at `dcb2725`. Worktree `/tmp/u3-shard-work`.

**HEADLINE: I did not ship the shard, and the reason is a measurement, not a
blocker.** Sharding this step is worth **6 seconds** of the LPT floor, against a
95-second gap to the mandate, on a lane whose own run-to-run noise is 44s. The
brief's premise - "one indivisible 304s step binds, and that step is yours" -
was fitted to a single run in which the step that actually binds drew its low
value. This is #266's sampling lesson repeating one level up, and the brief
warned me about exactly this failure in the paragraph above the one that
assigned me the work.

The design, the two hazards, and the one real blocker are all below, measured
in both directions, so the follow-up that DOES pay can be dispatched without
re-deriving any of it.

## 0. Canon read

- `MUST-READ-DOCS.md` - read. TIER-1 row 11 is `standards/devops/ci-cd.md`.
- `standards/devops/ci-cd.md` (`priority: required`, v1.3.5) - read in full.
  Two clauses bear on this work and neither is contradicted below:
  **Required-Gate Integrity, "Skipped is not green" (`ci-cd.md:669-729`)** is
  the clause hazard 1 lives under - a shard that ran zero rows is a check that
  produced no result, and `:673-675` says such an outcome MUST block exactly as
  a failure would. **Matrix Builds (`ci-cd.md:772-780`)** sanctions the
  `strategy.matrix` form the design uses, and **"Run jobs in parallel when
  possible" (`ci-cd.md:749-756`)** is the best practice the whole exercise acts
  on.
- `standards/devops/bash.md` (`priority: required`, v1.0.2, and NOT in the
  TIER-1 table as the brief warned) - read in full. It governs the harness body.
  The clauses the design is written against are `:150` (every expansion
  quoted), `:490` (`[[ ]]` not `[ ]`), `:734` (ShellCheck, zero warnings) and
  `:138` (constants UPPER_SNAKE_CASE). No shipped byte of shell changed, so
  none is currently at issue.
- `docs/DESIGN.md` is FROZEN - not touched. `docs/adr/0*.md` - none governs job
  packing or harness sharding.
- `docs/reviews/MEASURED-266-lane-rebalance.md` - read in full, including its
  own transformer defect (§4) and its §9 "what I did NOT verify", which
  pre-states the error this report confirms.
- `scripts/check-u3-audit-amputation.sh` (290 lines) and
  `scripts/check-u3-audit-controls.sh` - both read in full, plus
  `scripts/ci-harness-gate.sh` and `scripts/lib/harness-result.sh`, which turn
  out to matter more than either harness.

**I could not find any doc I was told to read and failed to locate.**

## 1. Sharding vs selection - the distinction holds, and I did not blur it

The brief asked me to stop if my design blurred this line. It does not, and the
distinction is worth stating precisely because it is the only reason this task
was permitted at all:

- **Per-row SELECTION** narrows the tests a row runs. An amputation's product
  is its SURVIVOR LIST - the set of assertions that still passed against a
  mutilated tree - so narrowing the suite shrinks that population *by
  construction*. Refused at #254 and #259; the refusal stands and I did not
  reopen it.
- **SHARDING THE ROW SET** changes only which lane executes which rows. Every
  row still runs the whole `$SUITE` (`check-u3-audit-amputation.sh:56`,
  unchanged). The union of the shards is the identical row set, so the survivor
  list is preserved by construction.

The design below preserves that: the shard predicate gates *which
`amputate` calls execute*, and never touches `$SUITE`, `-rA`, or the
`grep -E '^PASSED '` survivor extraction at `:166`.

## 2. THE REFUTATION - what the runs actually say

Every figure is recomputed from the runs' own payloads
(`gh api repos/:owner/:repo/actions/runs/<id>/jobs?per_page=100`), never read
back from prose. Three runs carry the 16-job shape:
`33614887374`, `33629034552`, `33630968540`.

### 2a. The four largest harness steps, per draw

| step | 7374 | 4552 | 8540 | **median** | swing |
|---|---|---|---|---|---|
| U3 audit amputation | 317s | 304s | 258s | **304s** | 1.23x |
| U9 HTTP hardening amputation | 300s | **201s** | 298s | **298s** | 1.49x |
| U4 client amputation | 235s | 242s | 227s | **235s** | 1.07x |
| Critical-path coverage amputation | 206s | **126s** | 209s | **206s** | 1.66x |

**U3 and U9 are a statistical tie.** U3 ranges 258-317s, U9 ranges 201-300s.
Calling U3 "the largest single step" is true of run `33629034552` and of the
median by 6 seconds - it is not a property of the workload.

**#266 fitted its packing to run `33629034552`, and that is the run in which
U9 drew 201s and critical-path coverage drew 126s** - both at the bottom of
their range, simultaneously. Those two steps are the entire explanation for
#266's 317s prediction missing at 390s, and they are why the brief believed the
binding step was mine.

### 2b. The measured post-repack run, by job

Run `33630968540`, the green 6.58-minute run the brief cites:

```
390s  Harness critical-path coverage + U9 controls + body cap amputation   <- POLE
380s  Harness U9 amputation + U10 amputation + stranded and suite-floor
329s  Harness U1 amputation + U8 amputation + gate, advisory and mirror
300s  Harness U10 controls + U0 controls + U15 amputation
296s  Harness U4 amputation + U12 amputation
284s  Harness U7 amputation + U5 controls + U6 controls
284s  Harness U12 controls + U4 controls + U6 amputation
271s  Harness U3 amputation                                     <- MINE, 8th
264s  Harness U1 controls + U5 amputation + anchor controls
243s  Harness U8 controls + U7 controls
214s  Harness U3 controls + body cap controls + U15 controls
194s  Harness U14 argument sweep + log redaction
161s  Lint, types, tests
 62s  CodeQL      52s  Static gates      19s  Wiring checker
```

**`Harness U3 amputation` was the EIGHTH slowest job at 271s.** Deleting it
outright would have taken the wall from 395s to 390s. Queueing was 3-5s on
every job, so the wall is the pole plus a handful of seconds; it is not hiding
anything.

### 2c. LPT over the medians, with steps made divisible

35 harness work steps, median sum 3442s, 13s per-lane setup (#266's figure,
the mean of 12 observations spanning 6-15s). Shard costs use #259's local
split - baseline B=14.47s rebuilt per shard, rows R=153.11s divided - scaled to
CI by 304/167.6 = 1.814x, so a 2-shard u3 costs 165s per shard rather than
152s. The baseline rebuild is *charged*, not assumed away.

| scenario | 12 lanes | 13 | 14 | 16 |
|---|---|---|---|---|
| nothing sharded | 317 | 317 | 317 | 317 |
| **u3 x2 (this task)** | 325 | **311** | **311** | **311** |
| u3 x2 + u9 x2 | 325 | 289 | **276** | 252 |
| u3 x2 + u9 x2 + critcov x2 | 329 | 293 | 276 | 248 |

**u3 x2 alone: 317s -> 311s. Six seconds, and it never reaches 300s at any
lane count**, because U9's 298s median becomes the binding indivisible step the
moment mine is divided. At 12 lanes it is *worse* (325s), because the extra
shard has to fit somewhere.

**u3 x2 + u9 x2 at 14 lanes: 276s.** That is under the 300s mandate. Sharding
U9 is not an optimisation on top of this task - it is the half that carries the
result.

### 2d. Why I did not ship a 6-second gain

The lane I would be changing drew 315s and 271s in consecutive runs - **44
seconds of noise on a 6-second gain.** The change is unmeasurable in the
instrument that would have to confirm it. Shipping it would add a job to an
externally-contended pool (~100 sibling repos, per the brief) and regenerate a
lane name under #267, in exchange for a number no run could distinguish from
zero. I could not defend that in the direction the brief asked me to defend it.

## 3. The design, complete and ready to apply

Stated precisely enough to implement without re-deriving it, because it is
correct and it is what U9 needs.

### 3a. Inputs, and why environment variables rather than flags

`ci-harness-gate.sh:190` runs `bash "$HARNESS_PATH"` with **no arguments**.
Adding argument pass-through to the shared gate would put 41 wired steps in the
blast radius. Environment variables cross `bash` unchanged and touch nothing:

```bash
# --- SHARDING ------------------------------------------------------------
# Which rows THIS invocation runs. Defaults are the unsharded harness.
SHARD_INDEX="${U3_SHARD_INDEX:-1}"
SHARD_COUNT="${U3_SHARD_COUNT:-1}"
```

Both validated as integers with `1 <= SHARD_INDEX <= SHARD_COUNT`, refusing
with exit 3 otherwise - an unparseable shard spec must not silently become 1/1,
which would run every row in every lane and look like success.

### 3b. The partition, and the assertion that it is one

Assignment is `shard_of(i) = ((i - 1) % SHARD_COUNT) + 1` over the 1-based
declared row ordinal. `amputate()` increments a DECLARED counter for every call
and returns immediately - **before printing its `########## $label` banner** -
when the row is not this shard's. The early return must precede the banner:
`ci.yml` counts rows with `--row-re '^########## A[0-9]+ '`, so a skipped row
that printed its banner would be counted as having run.

Four counters, because they are four different facts and the existing harness
already learned that lesson twice (`:100-113`):

| counter | meaning |
|---|---|
| `DECLARED` | every `amputate` call site - 10, identical in every shard |
| `MINE` | rows `shard_of` assigns to this shard - the per-shard floor |
| `HR_COUNTED_ROWS` | rows this shard actually entered |
| `HR_APPLIED` | rows whose anchor landed (existing, unchanged) |

Closing assertions, each failing loudly with exit 3:

1. **Union and disjointness, ASSERTED not assumed.** For every `i` in
   `1..DECLARED`, count the shards `s` in `1..SHARD_COUNT` with
   `shard_of(i) == s`. Every count must be exactly 1. This is computable inside
   a single shard because it is a pure function of `DECLARED` and
   `SHARD_COUNT`, and it is a property check over the assignment function's
   *output* rather than a restatement of it - a predicate narrowed to
   `i <= 8`, or off by one in a way that drops an index, fails here.
2. **The per-shard floor.** `MINE > 0`. This is the floor the harness has never
   had, and it is a *derived* count, not a literal - it cannot go slack against
   the row set the way a typed integer does.
3. **`HR_COUNTED_ROWS == MINE`**, exactly. Not `>=`; #223 measured that a `>=`
   floor reports `status=ok` at arms=10 floor=9.
4. `harness_result_ran "$HR_COUNTED_ROWS" "$MINE"` replaces
   `harness_result_ran "$HR_COUNTED_ROWS" 0` at `:274`, so the canonical line
   carries a floor that can actually be breached.

### 3c. The ci.yml shape

```yaml
  harness-u3-amputation:
    name: Harness U3 amputation
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2]
    steps:
      # ... preamble unchanged ...
      - name: U3 audit amputation harness ran every row in its shard
        env:
          U3_SHARD_INDEX: ${{ matrix.shard }}
          U3_SHARD_COUNT: ${{ strategy.job-total }}
        run: bash scripts/ci-harness-gate.sh check-u3-audit-amputation.sh --amputation --anchors-applied --min-rows 5 --row-re '^########## A[0-9]+ '
```

`strategy.job-total` rather than a literal `2`: the shard count is then derived
from the matrix GitHub already built, so the two cannot diverge. That is one
fewer hand-kept number, and it is the language carrying the signal rather than
a marker invented beside it.

**No step moves between lanes**, so #267's lane-name regeneration is not
triggered and I am not the third repack. The matrix splits one lane in place.

**Two shards, not three, and the reason is measured:** §2c shows k=2 and k=3
give the *identical* 311s floor. The third shard buys nothing and costs a job.

## 4. The two hazards, both measured, and one of them is not what the brief said

### 4a. Hazard 1 - the zero-row shard. TRUE of the harness, FALSE of the step.

The brief states the harness declares no ROW_FLOOR (its own comment at `:271-273`
says the floor is 0) and that "a shard running zero rows would exit 0 today".

**The first half is true. The second half is false at the wired step, and I
measured it rather than reading it.** A stand-in harness emitting exactly what a
mis-partitioned shard would emit - `rows=0 floor=0 applied=0/0 status=ok`,
exit 0 - was run through the real gate with the real flags from the `ci.yml`
step named **`U3 audit amputation harness ran every row`** (`:1671` at
`fb9cad2`, `:1673` after this branch lands - which is why the step NAME is the
citation and the offset is only a convenience):

```
$ bash scripts/ci-harness-gate.sh check-probe268-zero-rows.sh \
      --amputation --anchors-applied --min-rows 5 --row-re '^########## A[0-9]+ '
HARNESS-RESULT name=check-probe268-zero-rows.sh rows=0 floor=0 applied=0/0 status=ok
::error::check-probe268-zero-rows.sh ran ZERO rows; a green from it means nothing
::error::check-probe268-zero-rows.sh: only 0 rows ran, expected at least 5
rc=1
```

**Two independent outer layers already refuse it**: `--anchors-applied` reaches
`ci-harness-gate.sh:402`, whose comment says a harness reporting 0/0 passes
every equality check and must be caught by a zero test placed first; and
`--min-rows` reaches `:419`. Re-run without `--anchors-applied` and
without `--min-rows`, the same probe still exits 1 - but only on the anchor
vocabulary, which is a different question and would not fire for a real shard.

So the hazard is **real but already double-covered at the only place the
harness is invoked**. The intrinsic floor in §3b is still worth adding, because
both existing layers live in `ci.yml`'s flags: a future edit dropping
`--anchors-applied` would remove them silently, and a floor inside the harness
cannot be dropped by editing a workflow. That is hardening, not a closure, and
naming it as a closure would have been the overstatement this project keeps
measuring.

*Suggested fix:* §3b assertion 2, and it is worth doing on its own merits
whether or not anything is ever sharded - `harness_result_ran "$HR_COUNTED_ROWS" 0`
at `:274` is a floor of 0 in a harness with 10 fixed rows, which
`check-row-floor-exactness.py` registers as a "0-means-absent" site rather than
a finding.

### 4b. Hazard 2 - the union. Real, and the design closes it by assertion.

A row falling into no shard vanishes silently: the surviving shards each report
`applied=N/N` and `status=ok`, and the union is short by one with nothing
comparing it to `DECLARED`. This is the "a named list misses the unlisted"
shape, and neither existing outer layer sees it - `--min-rows 5` is a *lower*
bound, so a shard running 4 of its 5 rows while another runs 5 would need the
per-shard count to drop below 5 before anything spoke.

§3b assertion 1 closes it, and closes it as a property over `1..DECLARED`
rather than as a second copy of the assignment rule.

## 5. THE BLOCKER, planted and measured rather than read

`docs/reviews/check-row-floor-exactness.py` claim 3 (its docstring, `:37-46`)
requires `--min-rows` to **EQUAL** the harness's live row count, where the live
count is derived statically from the `amputate` call sites
(`_live_rows`, `:376-411`). A sharded step passes `--min-rows 5` while the
harness still declares 10 call sites.

I planted the change and read the exit code:

```
before:  check-u3-audit-amputation.sh  --min-rows  10  rows  10     rc=0
after:   check-u3-audit-amputation.sh  --min-rows   5  rows  10     rc=1
         SLACK by 5. It prints 10 rows and ci.yml passes --min-rows 5,
         so 5 row(s) can be deleted without the gate noticing.
```

`ci.yml` was reverted and `git status --short` is empty. **This gate goes red
on any sharded step, and it is wired** at `ci.yml:1186`.

*Suggested fix, and it strengthens rather than weakens the claim:* teach
`_external_floors()` (`:323-352`) to read the step's `env:` block for a shard
count, and have claim 3 assert `live == min_rows * shards` - still an equality,
so a deleted row still turns it red (9 != 5*2). The unsharded case is
`shards = 1` and is unchanged. It needs an arm in the 16-arm `--self-test`
(`:601`) for each direction. **This work is a precondition for sharding ANY
step, u9 included** - it is not specific to u3, and it should be its own task
sequenced before whichever sharding task is dispatched.

## 6. Findings, each with a fix

**F1 (High, NOT fixed - this is the report).** The brief's binding-constraint
premise is refuted: `check-u3-audit-amputation` is not the binding step, and
sharding it reaches 311s against a 300s mandate. *Fix:* shard
`check-u9-http-amputation.sh` as well; §2c measures u3+u9 at 14 lanes at 276s.
The design in §3 transfers unchanged apart from the variable names.

**F2 (High, NOT fixed - blocker).** `check-row-floor-exactness.py` turns red on
any sharded `--min-rows`, measured in §5. *Fix:* §5's equality against
`min_rows * shards`, plus two self-test arms. Sequence it before any sharding.

**F3 (Medium, NOT fixed - reported).** #266's 12-lane optimum was fitted to a
single run in which two steps simultaneously drew their minimum. The same
method on medians over three runs gives a different pole and a different lane
count. *Fix:* fit packings to a median over >=3 runs, and where a single-run
figure is used, label it - as #266's own §9 did, and as this report does.

**F4 (Medium, NOT fixed - reported).** The brief's "a shard running zero rows
would exit 0 today" is true of the harness and false of the wired step (§4a).
Both existing layers are `ci.yml` flags. *Fix:* the intrinsic floor of §3b,
which is worth landing independently of sharding.

**F5 (Low, NOT fixed - reported).** `scripts/lib/harness-result.sh:79` derives
`HR_NAME` from `basename BASH_SOURCE[1]`, so every shard of one harness emits
`name=check-u3-audit-amputation.sh`. `ci-harness-gate.sh:348` selects the
canonical line by `name=`, which is unambiguous *per invocation* and therefore
correct today. It stops being unambiguous the moment two shards' logs are
concatenated by any future aggregator. *Fix:* if an aggregator is ever built,
add a `shard=i/n` field to the canonical line via a named accessor in
`harness-result.sh`, never a second format literal.

**F6 (Nit, NOT fixed - reported).** With sharding wired, `--min-rows 5` is a
hand-kept number derived from 10/2. If an 11th row is added, shard 1 gets 6 and
shard 2 gets 5, and `--min-rows 5` still passes as a lower bound. *Fix:* this
is exactly why §3b assertion 3 is an equality inside the harness; the outer
literal is the loose layer and should not be the only one.

## 7. Gates, each read by exit code

    check-row-floor-exactness.py            rc=0   (baseline, and rc=1 planted - §5)
    ci-harness-gate.sh on a 0-row stand-in  rc=1   (§4a, both flag sets)
    git status --short                      empty, after every run

**actionlint: UNRUN.** It is not installed locally and CI fetches a pinned
tarball. I did not fetch it. **This is not a green - it is an absence.** It is
also not currently load-bearing: `.github/workflows/ci.yml` is byte-identical to
`dcb2725` on this branch (the §5 plant was reverted and verified), so there is
no workflow change for it to judge. It becomes mandatory the moment §3c is
applied.

**pytest, ruff, mypy, ShellCheck: NOT RUN**, and no shipped byte of Python or
shell changed on this branch, so they are not in the blast radius. I did not
run them.

**The harness itself was never executed in this worktree.** It mutates `src/`
in place; the only things run here were the gate against a stand-in and the
static floor checker.

## 8. Merge

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only ci/268-u3-shard

This branch adds one file - this report. It changes no code, no workflow and no
gate.

## 9. What I did NOT verify

- **That the §3 design works**, in either direction. It is written, argued and
  costed; it was never implemented or run. The two hazard proofs the brief asked
  for were obtained against a stand-in harness and a planted `ci.yml`, not
  against a sharded `check-u3-audit-amputation.sh`. **A shard missing a row and
  a shard running zero rows were therefore NOT proved red on the real harness** -
  §4a proves the second one red at the *gate*, which is a weaker claim than the
  one the brief asked for, and §4b's union assertion is unbuilt and unproved.
- **The 276s figure for u3+u9 at 14 lanes.** It is LPT over medians, with U9's
  shard cost modelled on U3's local baseline/row split (#259) because I did not
  measure U9's own baseline. U9's baseline may be a larger fraction of its
  runtime, which would make 2 shards worth less than modelled. #251 measured
  u9-http-amputation's baseline at 82.79s against 60.93s of rows - **the
  opposite ratio to u3's** - so this figure is soft in a direction that matters,
  and it should be re-derived from U9's own numbers before anything is
  dispatched on it.
- **Whether 14 lanes are admitted promptly.** Concurrency is external and
  org-wide across ~100 sibling repos. Queueing was 3-5s in all three runs read
  here; that is three draws in one morning and says nothing about a busy hour.
- **The 13s per-lane setup overhead** is #266's figure, carried forward, not
  re-derived.
- **Whether `strategy.job-total` is accepted by actionlint 1.7.7.** It is a
  documented GitHub context; I did not run actionlint (§7).
- **The zero-row probe is not committed.** It has to live under `scripts/` for
  `ci-harness-gate.sh:109` to find it, and a file there joins the floor
  container and `check-harness-result.sh`'s set equality. I chose the smaller
  harm and deleted it; §4a carries the command and its full output, and the
  script is 10 lines that recreate from the transcript. That is a real
  weakening of the "runnable probe, not prose" rule and I am naming it rather
  than pretending the report is equivalent.
