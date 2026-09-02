# MEASURED: the pre-re-tier baseline

**Tag: `baseline/pre-retier` at `305fd05`. Run `33680282835`, conclusion success.**

This is the referent for the CI re-tiering. Every later claim about "faster" or "cheaper"
compares against the figures below, which come from the Actions API rather than from any
document. Re-derive them with the command in the last section rather than trusting this file.

---

## The run

    created  2026-09-02T20:36:20Z
    updated  2026-09-02T20:42:03Z

    total wall       343s  (5.72 min)   <- what a developer waits
    execution wall   338s
    queue              5s
    jobs              16
    steps            238
    WORK            3222s  (53.7 min)   <- what the machines actually did
    parallel speedup 9.5x

**Wall is not work.** The 343s is latency across sixteen machines. Never compare it to a
serial duration - a local run, an agent, a single-lane job - without saying so.

## Billing

The repo is **public**, so GitHub Actions on standard runners is **free** and this run cost
**zero billable minutes**. The figures below are the counterfactual for any private child
repo built on this shape, and they are the reason the re-tier optimises billed minutes rather
than wall clock.

    job-seconds   3274s  (54.6 min of true job time)
    BILLED         61 min   (GitHub rounds EACH JOB up to the whole minute)
    rounding waste  6.4 min  - 10% of the bill, purely from having 16 lanes

## The eight heaviest steps

    325s  U3 audit amputation harness ran every row
    226s  U4 client amputation harness ran every row
    211s  U9 HTTP hardening amputation, every row applied
    209s  U1 boot amputation harness ran every row
    169s  U1 boot mutation controls, all fired
    166s  U3 audit mutation controls, all killed
    148s  Critical-path coverage amputation, every row applied
    125s  Default suite, zero skips

**The product test suite is 125s of 3222s - 3.9%.** Everything above it tests the tests.

## Per-job wall, and what each would bill

    337s ->  6   Harness U3 amputation                      <- sets the wall, ALONE in its job
    330s ->  6   Harness U1 amputation + U8 amputation + gate
    293s ->  5   Harness U4 amputation + U12 amputation
    274s ->  5   Harness U9 amputation + U10 amputation + stranded anchors
    254s ->  5   Harness U3 controls + body cap controls + U15 controls
    250s ->  5   Harness critical-path coverage + U9 controls + body cap
    229s ->  4   Harness U1 controls + U5 amputation + anchor controls
    220s ->  4   Lint, types, tests                         <- the whole Gate tier
    220s ->  4   Harness U10 controls + U0 controls + U15 amputation
    218s ->  4   Harness U7 amputation + U5 controls + U6 controls
    180s ->  3   Harness U8 controls + U7 controls
    160s ->  3   Harness U14 argument sweep + log redaction
    158s ->  3   Harness U12 controls + U4 controls + U6 amputation
     76s ->  2   CodeQL
     55s ->  1   Static gates, supply chain and links
     20s ->  1   The wiring checker can still fail

**`Lint, types, tests` is 220s.** That job is, almost exactly, the Gate tier the re-tier
proposes. The target of "under 3 minutes per push" is therefore roughly today's performance
with the harnesses lifted off the push path - not a new thing to build.

**The U3 lane is a single step.** 325s of step inside a 337s job. A job containing one step
cannot be repacked, which is why sharding U3 is necessary for any target below it and why no
amount of lane rearrangement reaches the mandate on its own.

---

## THE PREVIOUS RUN, AND WHY THE DIFFERENCE IS NOT A RESULT

| | run 33633268593 | run 33680282835 |
|---|---|---|
| sha | `1636f56` | `305fd05` |
| execution wall | 412s | 338s |
| WORK | 3938s | 3222s |
| jobs / steps | 16 / 236 | 16 / 238 |
| largest step | U3 333s | U3 325s |
| U9 amputation | **319s** | **211s** |

Work fell 3938s -> 3222s, an 18% drop, and the wall fell 412s -> 338s. **Do not read that as
an improvement.** The 61 commits between these two runs are harness-correctness fixes and a
`/tmp` path sweep; none of them removes work, and no mechanism in them explains 716 seconds.

The likely explanation is variance, and one column shows it plainly: **U9's amputation moved
319s -> 211s, a 108-second swing on work that did not change.** A prior task recorded the same
step ranging 201-319s across runs. With one run per configuration, a difference of this size
is indistinguishable from noise.

**The rule this baseline exists to enforce:** a re-tier claim must beat these numbers by more
than the observed per-step spread, or be measured over several runs. Pooling runs that straddle
a change and calling the difference a result is an error this project has already made three
times.

---

## Re-derive it

    gh api 'repos/:owner/:repo/actions/runs/33680282835/jobs?per_page=100'

Sum `completed_at - started_at` per step for WORK; take max(completed) - min(started) across
jobs for the execution wall; and for the private-repo bill, `ceil(seconds/60)` **per job**,
never over the run.
