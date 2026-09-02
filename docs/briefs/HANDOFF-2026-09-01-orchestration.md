# HANDOFF — 2026-09-01 08:26 PM CDT, written against compaction

Verified by running it at `3d7a82f`. Trunk is `ccbdaae` on both remotes;
`3d7a82f` is one commit ahead, local, unpushed.

## READ THIS FIRST: this document has been wrong three times

Version 1 said **"Main is GREEN locally, on every gate"** and listed six
gates, all 0. Every number was true and the claim was false: the gate
that had refused the tree for 127 commits was not on the list.

Version 2 said **"15 trunk commits are covered by no round"**. 15 was a
DISPLAY CAP (`untouched[:15]`); the population printed one line above.

Version 3 (this one's predecessor) said main was `09477ee` and listed
five gates that no longer exist under those names, because #143
consolidated three CI jobs into one.

All three are one defect: **a claim about a whole, evidenced by a sample
or a snapshot.** So every count below carries its container and its sha.

## Where the trunk actually is

    origin/main   ccbdaae   pushed to BOTH remotes
    local main    3d7a82f   one ahead, unpushed
    CI            203e5af   in_progress   <-- RUNNING, do not evict
                  ccbdaae   pending       0 jobs, consumes nothing

**THE CI RULE, MEASURED TWICE NOW.** `cancel-in-progress: github.ref !=
'refs/heads/main'` protects a RUNNING run on main. A push evicts PENDING
runs only, and a pending run has 0 jobs started. So pushing on top of a
pending run is free; pushing while you care about a RUNNING one is not.

## Gates at `3d7a82f`, every one run with CI's exact invocation

    ruff check . / format --check / mypy                    0
    scripts/check-committed-file-types.py --all             0   RUN IT WITH --all
    check-cross-references / design-freeze                  0
    check-checkers-are-wired                                0
    check-landing-published                                 0   NEW (#152)
    check-review-coverage                                   0   backlog 86
    probe-coverage-ratchet                                  0   9/9 arms
    probe-ci-checker-steps / -control                       0   34-block bucket now 0
    check-harness-result.sh                                 0   30 print == 30 publish
    control-stranded-mutation.sh                            0   26 arms
    check-no-errexit / no-sigpipe / row-floors / exactness   0
    check-obligations                                       0
    check-harness-anchors --self-check --floor 458          0
    actionlint (SHELLCHECK_OPTS=--severity=warning)         0
    pytest                        887 passed, 0 skipped, 6 deselected
    check-suite-floor.sh 887                                0

**THE ONE RED IS IN CI, NOT HERE, AND IT IS ROOT-CAUSED (#161).**
`Secret scan hook runs clean` fails because detect-secrets **rewrites
the baseline it then checks**: a recorded `line_number` for the literal
`inspect-only-not-a-credential` drifted 1344 -> 1431, the hook updated
`.secrets.baseline` in place, and pre-commit fails when a hook modifies
a file. In CI nothing can be re-staged, so it cannot recover. 22 entries
across 13 live files all carry line numbers. `suborch-161` has it.

**RUN CI'S EXACT INVOCATION, FLAGS AND ALL.** I broke this rule THREE
times in one evening: `check-committed-file-types.py` bare (staged set,
0 files, exit 0 - which hid a red trunk for 127 commits), `python3`
where CI uses `uv run --frozen python`, and `actionlint` without
`SHELLCHECK_OPTS=--severity=warning`, which reads an INFO diagnostic as
a failure. Copy the line out of `ci.yml`.

## Agents live right now

    suborch-161   #161, the secret-scan baseline. OWNS .github/workflows/ci.yml
    suborch-156   #156 (High), scripts/check-u1-boot-amputation.sh
    suborch-157   #157, the mirror workflow ONLY

Each has a brief in `docs/briefs/BRIEF-<n>-*.md`. **Ownership is stated
in each brief's §B and the three do not overlap.** Do not put a fourth
agent in `ci.yml`.

## Unmerged branches

    fix/kind-not-path            1 ahead   SUPERSEDED, kept as a record
    rescue/adr-0024-scan-bound   1 ahead   pre-existing, unexamined
    rescue/r6-probe-half-open    1 ahead   pre-existing, unexamined

Everything else merged at `ccbdaae`: #143, #146/#131, #147, #152, plus
#130 and #151.

## What tonight established

**EVERY SUB-ORCHESTRATOR CORRECTED ITS BRIEF, TEN FOR TEN.** A report
with no correction is now the anomaly, and the corrections have been
load-bearing: #152's showed my shape rule was wrong on 4 of the 6
harnesses it named; #143's found a SIXTH billed job my ledger omitted;
#147's found fourteen steps filed under a reason untrue of them.

**READING THE SITES BEATS A RULE OVER THEIR NAMES, four times.** #152's
shape rule (4 of 6 wrong), my #130 operator (wrong at exactly the
assignment sites), #159's premise (a grep over the WORD `VACUOUS`, when
10 of 10 harnesses already GATE on it at exit nonzero), and #147's
`classify()` counting physical lines.

**THE MERGE FINDS WHAT NO BRANCH CAN SEE.** Wiring #152's flags turned
`check-harness-result.sh` red: the fields were published with no printed
tally beside them. Invisible on its branch BY CONSTRUCTION, because the
field only appears once the flag is passed and the flag lived in a file
it did not own. Also: resolving #152's conflict by taking its hunk whole
would have put back a literal `900` that #116 had replaced with
`$ROW_TIMEOUT`.

**A FIX CAN REBUILD ITS OWN DEFECT ONE COLUMN OVER, twice in one
evening.** #151's ratchet first covered `NONE` and left `PARTIAL` red by
construction; then its CONTROL asserted the trunk was current, so the
probe went red after every push - the same defect relocated from the
checker into its control.

**A CONTROL PASSING IS NOT A CONTROL WORKING.** Three vacuous controls
tonight, all found by asking WHY an arm passed: my PLANT arm (planted
`origin/main` where the regex needs hex, so the plant never parsed),
#146's A2 (the amputated copy was untracked, so the probe aborted having
measured nothing), and both of #147's new pairs.

**MY OWN DEFAULT TIMEOUT IS AN UNNAMED ACTOR.** The Bash tool's
two-minute default killed my probe mid-row and stranded its two plant
files - #131 by my own hand, an hour after briefing an agent on it.
`nohup` and an explicit timeout; better, design the tree-mutation out,
as `--backlog` and `--reviews` do.

## What I would pick up first

1. **Collect `suborch-161`.** It is the last thing between this trunk
   and the first green CI run it has ever had.
2. **#155 + #153 together** - the wiring checker is blind BY PREFIX
   (24 of 28 probes) and BY PATH (`scripts/` excluded). Same checker,
   two dimensions, one fix. Needs `ci.yml`, so it waits for #161.
3. **#154 when the machine is quiet** - the 1800s bound rests on an
   inherited 1040s figure nobody reproduced, and settling it needs one
   unbounded run that must not be killed.
4. **#158 and #9 are PHIL'S**, not mine: no branch protection, and six
   OIDC roles with wildcard subject claims.
