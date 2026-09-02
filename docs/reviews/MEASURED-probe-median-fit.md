# MEASURED: the packing probe fits BOTH columns from three runs, and
# one published verdict still does not survive its own spread

`docs/reviews/probe-273-packing.py` was fitted to ONE historical run
(`33630968540`, head `dcb2725`). It adjudicated 12-lane margins of 0s to
8s. Its own instrument's run-to-run spread on a single step is 118s.
This record is the measurement of that spread and what it does to every
figure the probe published.

Re-run: `python3 docs/reviews/probe-273-packing.py` (~41s, three fits at
`RESTARTS = 10000`, plus four `gh api` calls and three log downloads).

## 1. The accepted population, and why each candidate is in or out

Two gates, both enforced in code on every execution, both printed:

- **(a) same code, by ancestry.** `5f46303` "U3 controls select per row"
  must be an ancestor of the run's head. Verified with
  `git merge-base --is-ancestor`, not by date.
- **(b) same work, from the run's own logs.** The `(name, rows)` multiset
  of the 77 `HARNESS-RESULT` lines must hash to
  `efaac90b99ac435a979d133aebb7f4b6`.

| run | head | ancestry | work signature | verdict |
|---|---|---|---|---|
| 33629034552 | `a849f7f` | ancestor | `efaac90b…` | **accepted** |
| 33630968540 | `dcb2725` | ancestor | `efaac90b…` | **accepted** |
| 33633268593 | `1636f56` | ancestor | `efaac90b…` | **accepted** |
| 33614887374 | `0d2c945` | **NOT an ancestor** | `81cb7001…` | **REJECTED** |

`0d2c945` fails BOTH gates independently. The probe short-circuits on
ancestry, so that is the printed reason; the work signature was measured
separately and differs on three lines:

    check-mirror-liveness-controls.sh   rows=17  (accepted runs: 23)
    check-pytest-bounded.sh             rows=78  (accepted runs: 81)
    check-suite-floor.sh                rows=888 (accepted runs: 889)

**A job-bundling difference is not a second population.** `a849f7f` ran
the same 12 lanes under a completely different job bundling — it shares
no harness *job* name with the other two — and is accepted, because its
`HARNESS-RESULT` multiset is byte-identical. That was the settled call
and the measurement confirms it.

## 2. What the join keys on, and why

**The step name.** It cannot be `(job, step)`: the repack renamed every
harness job, so `a849f7f` shares no job name with the other two runs and
a job-scoped key would join nothing at all.

Keying on a name is exactly how the previous hand-built version of this
table lost a step. Two guards now stand on it:

- **Uniqueness is asserted, not assumed.** A duplicate step name inside a
  run is a refusal, never a silent dict overwrite.
- **The root cause is fixed, not just guarded.** `Install from the frozen
  lock` is per-job dependency installation. It runs 12 times in every
  run and was missing from `WRAP`. It is per-job overhead, not movable
  work, so it now sits in `WRAP` — which is why the duplicate no longer
  arises in the first place.

**A second population bug was found in the same place.** The old `>= 5s`
duration floor was a threshold artefact: `U15 gate amputation` reads 4s
in two runs and 5s in the third, so the floor made the population 33
steps in two runs and 34 in another — a difference that reads exactly
like a code change. The floor is removed. With it gone and the
frozen-lock install in `WRAP`, **all three accepted runs carry the same
35 step names**, and that identity is asserted.

Reconciliation with the raw figures quoted in the brief:

| run | brief (old filter) | this probe (no floor, frozen lock in WRAP) |
|---|---|---|
| `a849f7f` | 35 steps 3323s largest 304s | 35 steps 3316s largest 304s |
| `dcb2725` | 33 steps 3311s largest 298s | 35 steps 3313s largest 298s |
| `1636f56` | 33 steps 3492s largest 333s | 35 steps 3493s largest 333s |

The brief's raw figures reproduce exactly under the old filter. The step
counts converge to 35 only after both population bugs are fixed.

## 3. Per-step spread across the three accepted runs

Identical work. Every difference below is the instrument, not the code.

| step | min | med | max | spread | ratio |
|---|---:|---:|---:|---:|---:|
| U3 audit amputation harness ran every row | 258 | 304 | 333 | 75 | 1.29 |
| U9 HTTP hardening amputation, every row applied | 201 | 298 | 319 | **118** | **1.59** |
| U4 client amputation harness ran every row | 227 | 239 | 242 | 15 | 1.07 |
| U1 boot amputation harness ran every row | 189 | 191 | 211 | 22 | 1.12 |
| Critical-path coverage amputation, every row applied | 126 | 206 | 209 | 83 | **1.66** |
| U1 boot mutation controls, all fired | 197 | 200 | 205 | 8 | 1.04 |
| U10 write controls, all fired | 137 | 157 | 181 | 44 | 1.32 |
| U8 candidate controls, all fired | 151 | 154 | 179 | 28 | 1.19 |
| U3 audit mutation controls, all killed | 117 | 150 | 168 | 51 | 1.44 |
| U12 job feed controls, all fired | 132 | 145 | 150 | 18 | 1.14 |
| U5 jobs controls, all fired | 118 | 121 | 146 | 28 | 1.24 |
| U14 argument sweep controls, all fired | 116 | 116 | 134 | 18 | 1.16 |
| U7 resilience amputation, every row applied | 114 | 121 | 131 | 17 | 1.15 |
| U0 test controls, all fired | 88 | 104 | 126 | 38 | 1.43 |
| U9 HTTP hardening controls, all fired | 119 | 124 | 126 | 7 | 1.06 |
| U4 client mutation controls, all killed | 106 | 107 | 115 | 9 | 1.08 |
| Body cap controls, all fired | 66 | 105 | 110 | 44 | **1.67** |
| U7 resilience controls, all fired | 78 | 79 | 99 | 21 | 1.27 |
| U8 candidate amputation, every row applied | 74 | 86 | 87 | 13 | 1.18 |
| U5 jobs amputation, every anchor applied | 53 | 54 | 69 | 16 | 1.30 |
| U10 write amputation, every row applied | 60 | 63 | 68 | 8 | 1.13 |
| U14 argument sweep amputation, every row applied | 53 | 54 | 64 | 11 | 1.21 |
| U12 job feed amputation, every row applied | 51 | 57 | 59 | 8 | 1.16 |
| U6 paging controls, all fired | 40 | 43 | 47 | 7 | 1.18 |
| Body cap amputation, every row applied | 41 | 42 | 42 | 1 | 1.02 |
| U15 gate controls, all fired | 17 | 17 | 19 | 2 | 1.12 |
| U11 advisory controls, all fired | 8 | 17 | 18 | 10 | **2.25** |
| U6 paging amputation, every anchor applied | 16 | 18 | 18 | 2 | 1.12 |
| Log redaction amputation, every row applied | 13 | 13 | 15 | 2 | 1.15 |
| Stranded-mutation control | 7 | 7 | 7 | 0 | 1.00 |
| Suite-floor guard amputation, every row killed | 5 | 7 | 7 | 2 | 1.40 |
| Harness anchor checker controls, all fired | 6 | 6 | 6 | 0 | 1.00 |
| U15 gate amputation, every row applied | 4 | 4 | 5 | 1 | 1.25 |
| Mirror liveness controls, all fired | 2 | 3 | 3 | 1 | 1.50 |
| Harness gate controls, all fired | 0 | 1 | 1 | 1 | - |

Population totals: **MIN 2990s, MEDIAN 3413s, MAX 3719s.**

The sum-of-medians (3413s) exceeds every real run total (3316 / 3313 /
3493) because each step's middle is taken independently. MIN and MAX are
likewise envelopes no single run produced. They bound the instrument;
they are not predictions of a run.

**Per-lane setup was re-measured** as job wall minus the population steps
in that job, so it captures the gaps a step-duration sum cannot see. The
36 accepted lanes read **8-19s, median 11.0**. `SETUP = 13.0` is kept
unchanged, because every absolute in `REVAMP-238-ci.md` 7a.2 carries it
and moving it would move all of them; it is added to both columns and so
cancels in every delta.

## 4. Both floors

**Single-run fit (before), 12 lanes unsharded:**
`max(298, 3311/12 = 275.9) + 13.0 = ` **311.0s**, and BEST met it (`=`).

**Median fit (after), 12 lanes unsharded:**
`max(304, 3413/12 = 284.4) + 13.0 = ` **317.0s**, and BEST met it (`=`).

**The brief's hand calculation reaches 317s by a route that does not
hold.** It uses `3323/12 = 276.9` — `a849f7f`'s *run total*, not the
sum-of-medians, which is 3413 and gives `3413/12 = 284.4`. Both routes
land on 317 only because the largest median step (304s) dominates the
area term either way, so the wrong total is never load-bearing. The
answer is right; the derivation should not be reused, because at 11
lanes and below the area term does become load-bearing.

**Whole floor envelope: 271.0s (MIN) to 346.0s (MAX)** — a **75s** band
on a quantity whose published margins are 0-8s.

## 5. What the spread does to each published conclusion

Deltas (sharded BEST minus unsharded BEST) by lane count. **Both columns
are now fitted by the same MIN/MEDIAN/MAX picker over the same three
runs** - see §6 for how the sharded column became measurable. The
`n/a` verdicts are gone; every cell is stated.

| lanes | MIN fit | MEDIAN fit | MAX fit | |
|---|---:|---:|---:|---|
| 11 | +11.0 | +18.4 | +20.0 | same sign - a LOSS |
| 12 | **+5.0** | **-1.0** | **-4.0** | **SIGN FLIPS** |
| 13 | -16.0 | -24.8 | -26.0 | same sign - a WIN |
| 14 | -25.0 | -43.0 | -44.0 | same sign - a WIN |
| 15 | -28.0 | -55.0 | -66.0 | same sign - a WIN |
| 16 | -31.0 | -65.0 | -81.0 | same sign - a WIN |

Against the previous round, which held the sharded column at one run:

| lanes | before (MIN/MED/MAX) | after | change |
|---|---|---|---|
| 11 | +27.5 / +15.0 / +10.0 | +11.0 / +18.4 / +20.0 | still a loss |
| 12 | +19.0 / -5.0 / -12.7 | +5.0 / -1.0 / -4.0 | **still flips**, envelope 31.7s -> 9.0s |
| 13 | +1.5 / -27.0 / -37.0 | -16.0 / -24.8 / -26.0 | **CLOSES - now a win in all three** |
| 14 | -20.7 / -43.0 / -54.7 | -25.0 / -43.0 / -44.0 | still a win |
| 15 | -28.0 / -55.0 / -69.0 | -28.0 / -55.0 / -66.0 | still a win |
| 16 | -31.0 / -65.0 / -81.0 | -31.0 / -65.0 / -81.0 | still a win |

- **13 lanes is now DETERMINATE.** It previously flipped only at the
  extreme MIN envelope (+1.5). With the sharded column refit it reads
  -16.0 at MIN, and sharding wins in every fit.
- **12 lanes is STILL NOT DETERMINATE, and this is the residual.** The
  envelope narrowed 3.5x, from 31.7s to 9.0s, and the median moved from
  -5.0s to **-1.0s** - a one-second margin on an instrument whose
  run-to-run spread on a single step is 118s. Refitting removed the
  cross-column vintage error; it did not and cannot remove the fact
  that these three runs' own spread is wider than the margin being
  adjudicated.
- **The 11-lane loss SURVIVES and got larger** (+11.0 / +18.4 / +20.0).
  Note the MIN fit moved the *wrong* way for it: it was +27.5 and is now
  +11.0, so the loss is narrower at MIN than the previous round said.
- **14, 15 and 16 lanes SURVIVE**, with margins far outside the spread.
- **Every ABSOLUTE published from the single-run fit remains void.** The
  12-lane unsharded floor is 271-346s, median 317s.

**Consequence: no repack or shard decision at 12 lanes is supportable
today.** 13 lanes now is. That is the whole change in decision surface.

## 6. THE DEFECT THE LAST ROUND NAMED IS CLOSED, and here is how

The previous round left this open and was right to: `U3_SHARD = 163.3`
and `U9_SHARD = 219.5` were two constants fitted to ONE run, so pairing
them with a MIN- or MAX-fit unsharded column subtracted two different
measurements. The verdicts were withheld (`n/a`) on every fit but the
median.

### 6a. What was checked, and what each check returned

The brief's premise was that `B` / `R` / `ovh` come from task #240's
harness profile, which profiled one run, so a per-run refit might be
impossible. **That premise is wrong in a way that matters**, and three
checks establish it.

**Check 1 - is the shard cost even sensitive to the profile?** No.
`step_ci(k) = scale * (B + (R+ovh)/k)` with `scale = k1/(B+R+ovh)`
makes the 2-shard cost a scale-free FRACTION of the observed unsharded
time:

    U3: (1 - 0.9254/2) = 0.537298, and 0.537298 x 304 = 163.34
    U9: (1 - 0.5270/2) = 0.736516, and 0.736516 x 298 = 219.48

Both reproduce the published constants exactly. `scale` cancels. So the
profile's absolute seconds were never load-bearing; only the
dimensionless divisible share was, and `scale` was always the per-run
knob the probe declined to turn.

**Check 2 - is a per-RUN scale defensible?** No, and this refutes the
lazy version of the refit. If runs were uniformly fast or slow, each
run's ratio-to-median across steps would be near-constant. Over the 25
steps with median >= 40s (smaller ones are quantization-dominated at
GitHub's 1s step resolution):

    run 33629034552   ratios 0.612 - 1.278   (2.09x within ONE run)
    run 33630968540   ratios 0.629 - 1.212
    run 33633268593   ratios 0.873 - 1.207

There is no per-run scale factor. A refit that multiplied every step by
one per-run constant would have been fiction.

**Check 3 - are B and R recoverable per run from the runs' own logs?**
**YES**, and this is the finding. Two things are in every accepted run's
log already:

- pytest prints its own session duration on EVERY invocation
  (`===== 13 failed, 119 passed in 10.85s =====`);
- the harness prints `########## A<n>` once per row.

Splitting each step's log segment at the first row banner separates the
baseline invocation from the row invocations, per run, measured in CI on
the machine that will run the shards - not transferred from a local box
at a fitted 1.567x / 1.703x.

### 6b. What is NOT recoverable, and how that was established

**Per-ROW wall time.** Actions log lines carry timestamps, so per-row
duration looks available. It is not: the harness's stdout reaches
Actions in ONE buffered flush. In run 33630968540's U9 amputation step,
all 14 row banners and the `HARNESS-RESULT` line carry timestamps
between `12:42:39.785` and `12:42:39.790` - **5 milliseconds spanning a
298-second step**. Log timestamps are receive times, not emission
times. The same holds for U3 (10 banners in 0.058s of a 258s step).

pytest's self-reported session duration is the only intra-step clock
that exists in this data, which is why the decomposition is built on it
and not on the timestamps.

### 6c. The measurement

| harness | run | B | R | residual | ovh/invocation | 2-shard |
|---|---|---:|---:|---:|---:|---:|
| U3 amputation | a849f7f | 25.60 | 264.58 | 13.8 | 1.26 | 165.4 |
| U3 amputation | dcb2725 | 22.34 | 221.30 | 14.4 | 1.31 | 140.8 |
| U3 amputation | 1636f56 | 28.52 | 288.89 | 15.6 | 1.42 | 181.5 |
| U9 amputation | a849f7f | 107.25 | 71.69 | 22.1 | 1.47 | 154.9 |
| U9 amputation | dcb2725 | 172.74 | 101.54 | 23.7 | 1.58 | 236.2 |
| U9 amputation | 1636f56 | 181.31 | 106.44 | 31.2 | 2.08 | 251.2 |

`ovh` is a RESIDUAL - `(step wall - B - R) / invocations` - so it
absorbs uv spawn, pytest import, the cp/anchor-replace/cmp file work and
log flush. A shard reruns the baseline and 1/k of the rows, so
`step(k) = B + R/k + ovh * (1 + rows/k)`; k=1 reproduces the wall BY
CONSTRUCTION and is offered as arithmetic, not validation.

Fitted by the same three pickers as the unsharded column:

| harness | MIN | MEDIAN | MAX | old constant |
|---|---:|---:|---:|---:|
| U3 2-shard | 140.8 | 165.4 | 181.5 | 163.3 |
| U9 2-shard | 154.9 | **236.2** | 251.2 | **219.5** |

**U3's old constant was very close to the measured median** (163.3 vs
165.4). **U9's was 16.7s too low** - and U9 is the step that binds. The
old constant flattered sharding at exactly the cell under dispute.

### 6d. What this does NOT establish

- **Nothing has ever run sharded.** This is still a model. It is now a
  model whose terms were measured in CI at n=3 rather than transferred
  from one local box at a fitted scale.
- **The k=1 identity carries no information** and is not evidence.
- The model assumes **each shard reruns the whole baseline** (#268 §3's
  design, which charges it deliberately) and that the **residual is
  per-invocation**. Both are assumptions. They are now assumptions over
  measured terms.
- **This is why 12 lanes did not close.** The residual is not a fitting
  error any longer; it is the spread of the three runs themselves.

## 6e. The two live disputes, carried rather than inherited

**Task #278's overhead term.** #278 measures the per-invocation cost at
**130ms** against 7a.2's fitted **2.24-2.64s**. The measured residual
here is **1.26-1.42s (U3) and 1.47-2.08s (U9)** - between the two, and
nearer 7a.2. Both disputants are answering different questions: #278
timed the `uv run` exec alone, while the residual is everything the step
spends outside pytest's own session clock. **Neither figure should be
quoted as the other.**

Where it lands on the quantity that actually matters, the divisible
share computed 7a.2's own way, `(R+ovh)/(B+R+ovh)`:

| harness | a849f7f | dcb2725 | 1636f56 | 7a.2 | #278's correction |
|---|---:|---:|---:|---:|---:|
| U3 | 0.9158 | 0.9134 | 0.9144 | 0.9254 | - |
| U9 | 0.4664 | 0.4203 | 0.4316 | **0.5270** | **0.431** |

**#278's 0.431 sits INSIDE the measured range; 7a.2's 0.5270 sits
outside it, above every run.** On this quantity #278 is vindicated and
7a.2's figure is refuted by direct measurement.

**The claim that #278's low end reverses the 11-lane result is REFUTED,
and it points the wrong way.** It was swept rather than argued. If the
per-invocation cost really is 130ms, the rest of the measured residual
is not per-invocation, and the adverse attribution is that every shard
pays it in full. Sweeping both ends (`RESTARTS = 2000`, a sweep and not
the published table, so cells sit within ~1s of §5):

| attribution | 11 lanes | 12 lanes | 13 lanes |
|---|---|---|---|
| residual per-invocation (shipped) | +11.9 / +18.4 / +20.0 | +5.0 / -0.8 / -4.0 | -16.0 / -24.8 / -26.0 |
| #278 at 130ms, remainder per-invocation | +11.2 / +19.0 / +19.8 | +5.0 / -1.1 / -4.0 | -16.0 / -25.0 / -26.2 |
| #278 at 130ms, remainder PER-STEP fixed | +14.0 / +22.0 / +23.0 | +5.7 / **+1.0** / -0.1 | -14.8 / -17.0 / -25.0 |

- **11 lanes never reverses.** It is a loss in every fit under every
  attribution, and #278's low end makes the loss LARGER (+14.0/+22.0/
  +23.0), not smaller. The brief's premise is backwards on this point.
- **13 lanes is determinate under every attribution.** That is the
  strongest form of the closure in §5.
- **12 lanes gets worse, not better.** Under the adverse attribution its
  MEDIAN flips to a LOSS (+1.0). So 12 lanes is unresolved in two
  independent ways: across the run spread, and across #278.

**An instrument note, reported because it is the failure this project
keeps measuring.** The first two rows of that sweep were originally
three, including a "residual fully per-step" arm at the measured `ovh`.
It produced numbers IDENTICAL to the shipped arm - correctly, because
when `ovh` IS the measured per-invocation residual there is no remainder
left to attribute, so the treatment never fired. It is dropped rather
than reported as agreement.

**`SETUP = 13.0`.** Unchanged, and the reasoning is unchanged: the 36
accepted lanes read 8-19s with median 11.0, but every published absolute
in `REVAMP-238-ci.md` 7a.2 carries 13.0, and it is added to BOTH columns
so it cancels in every delta. **The refit did not change which
quantities are absolute** - it changed only the sharded column's inputs,
and every delta in §5 is still SETUP-free. So there is nothing here to
revisit; if SETUP is ever re-derived, it moves the absolutes in §4 and
no delta in §5.

## 7. The guards, watched firing

Every guard below was planted on the committed branch, observed to
refuse, and reverted; `git status --porcelain` was empty after each.

1. **Fewer than `MIN_RUNS` comparable runs.** Planted `EXPECT_WORK_SIG =
   "000...0"`:
   `REFUSING: 0 comparable runs, not 3. A spread fitted from fewer is not a spread.`
   exit 1.
2. **Duplicate step name.** Planted by removing `Install from the frozen
   lock` from `WRAP`:
   `REFUSING: run 33629034552 has two steps named 'Install from the frozen lock'. The join keys on the step name; a dict would drop one.`
   exit 1.
3. **Medians outside the recorded band.** Planted `EXPECT_MEDIAN_TOTAL =
   3200.0`:
   `REFUSING: sum-of-medians is 3413s, outside 3200+-60s. Every figure below is derived from it and would be void.`
   exit 1.
4. **Populations differ between accepted runs.** Driven against the
   file's own `fit()` with a doctored population:
   `REFUSING: run r2's population differs by ['Y', 'Z']. A per-step median needs the same steps in every run.`
   exit 1. **Positive control:** the same call with matching populations
   returns the three fits, exit 0 - so the refusal is the doctoring, not
   the driver.

Two guards are NEW with this change, because the shard column is now
derived from a regex over a log rather than from a literal:

5. **The pytest-summary regex stops matching - a CLEAN ZERO.** Without
   this, `B = R = 0`, the entire wall becomes residual, and the shard
   cost silently collapses with a plausible story attached. Planted a
   never-matching pattern:
   `REFUSING: run 33629034552 check-u3-audit-amputation parsed 0 baseline and 0 row pytest summaries, expected 1 and 10. The shard cost is derived from them and would be void.`
   exit 1. Planted instead as a row-count change (10 -> 9), the same
   guard reports `parsed 1 baseline and 10 row pytest summaries, expected
   1 and 9`, exit 1 - so it discriminates a broken parse from a changed
   harness.
6. **A fitted 2-shard cost leaves its recorded band.** Planted U9's band
   as `(145.0, 240.0)` against a measured MAX of 251.2:
   `REFUSING: MAX 2-shard cost for 'U9 HTTP hardening amputation, every row applied' is 251.2s, outside the recorded 145-240s band. Every sharded cell derives from it.`
   exit 1. **Positive control:** unmodified, the probe emits zero
   `REFUSING` lines.

The comparability gates are exercised on every ordinary run:
`0d2c945` is deliberately left in `CANDIDATES`.

## 8. Verification

- **`0d2c945` still fails BOTH gates, measured independently.** Ancestry:
  `5f46303` is not an ancestor of `0d2c945`. Same-work: its signature is
  `81cb700109828ffdfd2d80931fa5d350` against the expected
  `efaac90b99ac435a979d133aebb7f4b6`. The probe short-circuits on
  ancestry, so only the first is printed in an ordinary run.
- **The three-run acceptance holds.** `a849f7f`, `dcb2725` and `1636f56`
  are each an ancestor-descendant of `5f46303` and each hash to
  `efaac90b…`.
- `ruff check` - All checks passed.
- `ruff format --check` - 1 file already formatted.
- Test-merged onto `main` `d314283` in a detached worktree: `Automatic
  merge went well`, zero conflicting paths.
- The packing algorithm (`lpt`, `lower_bound`, `descend`, `best`) is
  carried across byte-identical. Only the shard-cost derivation and the
  reporting layer changed.

## 9. What I did NOT verify

- **That any of this predicts a sharded run.** Nothing has ever run
  sharded; §6d is the standing caveat and it is the reason 12 lanes is
  still open.
- **The row invocations' test counts.** U9's rows run 132 / 22 / 21 / 16
  tests while its baseline runs 895, and U3's rows and baseline both run
  107. That asymmetry is stable across all three runs, so it does not
  disturb the decomposition, but I did not open the harnesses to explain
  why the amputation rows are not running the full suite that
  `PROFILE-240` and `MEASURED-268` both describe. **If those documents
  are still right about `$SUITE`, something has changed underneath them
  and it is worth its own task.**
- **`SHARD_K = 2` only.** #268 §3c measured k=2 and k=3 as identical for
  U3 and shipped 2. I did not re-derive that under the refit.
- **The per-lane `SETUP` figure**, carried forward unchanged from #266.
- **Whether 12-16 lanes are admitted promptly** by an org-wide runner
  pool. Unchanged and still external.
