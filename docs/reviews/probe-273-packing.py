#!/usr/bin/env python3
"""Bracket CI's makespan rather than estimate it with a heuristic.

WHY THIS EXISTS. Task #273 was wrong TWICE, both times from treating
the output of LPT (longest-processing-time-first) as a measurement:

  - it first said the shard plan needed 15 lanes;
  - it then said sharding at 12 lanes was a 12-second REGRESSION.

Neither held. LPT is a heuristic in BOTH regimes; what differs is how
loose. When one item dominates - largest > total/lanes - the area
bound falls away and max(item) is often achievable, so a packing that
MEETS the bound can usually be exhibited; when none dominates, LPT is
only a loose upper bound. This is EXHIBITION, not a theorem: for
m=5 over [27,23,22,16,13,9,8,6] the largest item dominates and LPT
still returns 28 against an optimum of 27. See REVAMP-238-ci.md 7a.2.

So the "regression" was an exact number differenced against an upper
bound. Sweeping the INPUTS could never reveal it, because both columns
were computed with the same biased estimator and the bias moved with
them. The algorithm was the variable nobody varied.

AND THEN THE INPUTS WERE WRONG TOO. Every figure this file once
printed came from ONE historical run. Three comparable runs of the
SAME code doing the SAME work read:

  a849f7f  U9 amputation 201s   U3 amputation 258s
  dcb2725  U9 amputation 298s   U3 amputation 304s
  1636f56  U9 amputation 319s   U3 amputation 333s

That is a 118s spread on U9 - 1.59x - on work whose own
HARNESS-RESULT line is byte-identical in all three
(`rows=14 floor=0 applied=14/14 status=ok`). The 12-lane margins this
file adjudicates are 0s to 8s: an ORDER OF MAGNITUDE below its own
instrument's run-to-run noise. A single-run fit could not see that,
and every absolute derived from it was a coincidence of which run got
picked. This file now fits from N runs and publishes the spread beside
every figure.

WHAT THIS COMPUTES, per column and lane count, on three fits of the
same population - MIN, MEDIAN and MAX of each step across the
accepted runs:

  LB    max(largest item, total / lanes)     a true lower bound
  LPT   the greedy result                    an upper bound
  BEST  LPT + steepest descent, restarts     a tighter upper bound
  '='   BEST met LB, so that cell is PROVED rather than estimated

A bracket is the honest object here. Where BEST meets LB the answer is
certain for THAT fit; where the MIN and MAX tables disagree about a
cell's verdict, the conclusion is not supportable at all and the file
says so rather than printing the median and stopping.

COMPARABILITY IS ENFORCED, NOT ASSUMED. A run joins the population
only if BOTH hold:

  (a) SAME CODE, by ancestry not by date. REQUIRE_ANCESTOR names the
      commit whose absence would make a run measure a landed
      optimisation as if it were noise.
  (b) SAME WORK, from the run's own HARNESS-RESULT lines. The
      (name, rows) multiset must hash to EXPECT_WORK_SIG.

Run 0d2c945 fails BOTH and is rejected; it is left in CANDIDATES on
purpose so that every execution exercises the rejection rather than
asserting it once in a report. A configuration difference that does
NOT change the work is a data point, not a second population: a849f7f
ran the 12 lanes under a DIFFERENT job bundling than the other two and
is accepted, because its HARNESS-RESULT multiset is identical.

THE JOIN KEY IS THE STEP NAME, AND UNIQUENESS IS ASSERTED. It cannot
be (job, step): the repack renamed every harness job, so a849f7f
shares no job name with the other two and a job-scoped key would join
nothing. The step name is the only identifier stable across the
repack. Keying on a name is exactly how the first attempt at this
table lost a step - `d[step["name"]] = seconds` silently dropped one
of a849f7f's TWO `Install from the frozen lock` steps and published a
population of 34/3318 for a run that is really 35/3323 - so the
duplicate is now a REFUSAL, not a silent overwrite.

That duplicate also had a root cause worth keeping fixed: `Install
from the frozen lock` is per-job dependency installation, runs 12
times in every run, and was missing from WRAP. It is wrapper
overhead, not movable work, so it belongs there.

THE >= 5s FLOOR WAS REMOVED, and that was the second population bug.
`U15 gate amputation` reads 4s in two runs and 5s in the third, so the
floor made the population 33 steps in two runs and 34 in the other -
a threshold artefact that reads exactly like a code change. With the
floor gone and the frozen-lock install in WRAP, all three runs carry
the SAME 35 step names. That identity is asserted.

WHAT IT IS NOT. Not a gate. Its inputs are historical GitHub runs, so
nothing in this repository can regress it, and wiring it would gate
the trunk on the Actions API being reachable. Re-run it by hand when
the step population, the lane count, or the fitted shard costs change.

THE SHARD COSTS ARE STILL FITTED TO ONE RUN. U3 -> 2 x 163.3s and
U9 -> 2 x 219.5s were fitted against dcb2725's 304s and 298s, and
this file does NOT refit them per fit. So the SHARDED column under the
MIN and MAX tables pairs a re-fitted unsharded input with a
median-vintage shard cost, and its deltas there are not meaningful.
Fixing the unsharded column and leaving this one is the same defect
one column over; it is named here rather than hidden, and the printed
verdict for the sharded column is withheld on any fit but the median.
Task #278 separately contests the overhead term.
"""

import datetime
import hashlib
import io
import json
import random
import re
import statistics
import subprocess
import zipfile
from typing import Any

REPO = "/home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite"

# Named, not discovered. Discovery would silently re-pool as new runs
# land and would move every published absolute under a reader's feet;
# a fixed list is reproducible and its rejections are re-run every
# time. Add a run here by hand after checking it against both gates.
CANDIDATES = (
    "33629034552",  # a849f7f
    "33630968540",  # dcb2725
    "33633268593",  # 1636f56
    "33614887374",  # 0d2c945 - rejected, kept to exercise the gates
)

# "U3 controls select per row". Not an ancestor of 0d2c945 and an
# ancestor of the other three, so pooling that run would average a
# landed optimisation with the code that lacks it.
REQUIRE_ANCESTOR = "5f46303"

# md5 of the sorted, counted (name, rows) multiset from the run's own
# HARNESS-RESULT lines: 77 lines, identical in all three accepted
# runs. 0d2c945 differs on three of them (mirror-liveness 17 vs 23,
# pytest-bounded 78 vs 81, suite-floor 888 vs 889), so the same-work
# gate rejects it INDEPENDENTLY of the ancestry gate.
EXPECT_WORK_SIG = "efaac90b99ac435a979d133aebb7f4b6"
RESULT_LINE = re.compile(rb"HARNESS-RESULT name=(\S+) rows=(\d+)")

# GitHub's own per-job wrapper steps, plus the per-job dependency
# install. Per-job overhead, not work that can move between lanes, so
# not part of the population.
WRAP = (
    "Set up job",
    "Complete job",
    "Post ",
    "Checkout",
    "Install uv",
    "Set up Python",
    "Run actions/",
    "setup-python",
    "Install from the frozen lock",
)

# per-lane setup, measured as job wall MINUS the population steps in
# that job, so it captures the gaps a step-duration sum cannot see.
# The 36 accepted lanes read 8-19s, median 11.0. 13.0 is kept because
# every absolute published in REVAMP-238-ci.md 7a.2 carries it and
# changing it would move all of them; it is added to BOTH columns, so
# it cancels in every delta and biases only the absolutes.
SETUP = 13.0
SETUP_RANGE = (8.0, 19.0)

MIN_RUNS = 3
EXPECT_NAMES = 35
# Sum-of-medians, which is NOT any run's total: it exceeds all three
# (3316 / 3313 / 3493) because it takes each step's middle
# independently. Recorded as a band so the ground moving is loud.
EXPECT_MEDIAN_TOTAL = 3413.0
MEDIAN_TOTAL_TOLERANCE = 60.0

U3_SHARD = 163.3
U9_SHARD = 219.5

# CHOSEN BY MEASURING WHERE THE TABLE STOPS MOVING, not by picking a
# bigger number. All twelve printed BEST cells were swept over
# R = 1, 10, 60, 100, 200, 400, 1000, 3000, 10000, 40000. Eleven settle
# by R = 200; the SHARDED 11-LANE cell does not - it reads 335.5 at 400,
# 335.0 at 1000, 334.3 at 3000 and 334.0 from 10000 onward (unchanged at
# 40000 and 100000), which is why 400 was too low. At 10000 the whole
# table costs 8.8s of search (median of 5, this host) against a wall
# already dominated by one `gh api` call, on a probe nothing gates.
# That sweep was run on the single-run fit; three fits cost 3x.
# NOT swept here: the fitted-cost refits quoted in REVAMP-238-ci.md
# 7a.2, which this file does not compute.
RESTARTS = 10000


def parse_time(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def api(path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", path], capture_output=True, text=True, cwd=REPO
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise SystemExit(f"REFUSING: gh api failed for {path}")
    parsed: dict[str, Any] = json.loads(result.stdout)
    return parsed


def is_wrapper(name: str) -> bool:
    return any(name.startswith(w) or w in name for w in WRAP)


def work_signature(run: str) -> str:
    """Hash the run's own HARNESS-RESULT (name, rows) multiset."""
    result = subprocess.run(
        ["gh", "api", f"repos/:owner/:repo/actions/runs/{run}/logs"],
        capture_output=True,
        cwd=REPO,
    )
    if result.returncode != 0 or not result.stdout:
        raise SystemExit(f"REFUSING: could not fetch logs for run {run}")
    rows: list[bytes] = []
    with zipfile.ZipFile(io.BytesIO(result.stdout)) as archive:
        for entry in archive.namelist():
            rows += RESULT_LINE.findall(archive.read(entry))
    if not rows:
        raise SystemExit(f"REFUSING: run {run} emitted no HARNESS-RESULT lines")
    joined = b"\n".join(sorted(b"%s %s" % pair for pair in rows))
    return hashlib.md5(joined, usedforsecurity=False).hexdigest()


def harness_steps(run: str) -> dict[str, float]:
    """Every non-wrapper step in a harness-* job, keyed by step name.

    No duration floor: a floor at 5s put `U15 gate amputation` (4-5s)
    in the population of one run and out of another's. A duplicate
    name is a REFUSAL, because a dict would silently drop one.
    """
    steps: dict[str, float] = {}
    jobs = api(f"repos/:owner/:repo/actions/runs/{run}/jobs?per_page=100")
    for job in jobs["jobs"]:
        if not job["name"].lower().startswith("harness"):
            continue
        for step in job.get("steps") or []:
            if not (step.get("started_at") and step.get("completed_at")):
                continue
            named = step["name"]
            if is_wrapper(named):
                continue
            if named in steps:
                raise SystemExit(
                    f"REFUSING: run {run} has two steps named {named!r}. "
                    "The join keys on the step name; a dict would drop one."
                )
            steps[named] = (
                parse_time(step["completed_at"]) - parse_time(step["started_at"])
            ).total_seconds()
    return steps


def is_ancestor(commit: str, sha: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, sha],
            capture_output=True,
            cwd=REPO,
        ).returncode
        == 0
    )


def accept_runs() -> dict[str, dict[str, float]]:
    """Print every candidate with its verdict, then refuse or return."""
    accepted: dict[str, dict[str, float]] = {}
    print(f"comparability gates: ancestor {REQUIRE_ANCESTOR}, work {EXPECT_WORK_SIG}")
    for run in CANDIDATES:
        sha = api(f"repos/:owner/:repo/actions/runs/{run}")["head_sha"]
        short = sha[:7]
        if not is_ancestor(REQUIRE_ANCESTOR, sha):
            print(f"  REJECT {run} {short}: {REQUIRE_ANCESTOR} is not an ancestor")
            continue
        signature = work_signature(run)
        if signature != EXPECT_WORK_SIG:
            print(f"  REJECT {run} {short}: work signature {signature}")
            continue
        accepted[run] = harness_steps(run)
        print(f"  accept {run} {short}: {len(accepted[run])} steps")
    return accepted


def lpt(items: list[float], lanes: int) -> float:
    loads = [0.0] * lanes
    for duration in sorted(items, reverse=True):
        loads[min(range(lanes), key=lambda k: loads[k])] += duration
    return max(loads)


def lower_bound(items: list[float], lanes: int) -> float:
    return max(max(items), sum(items) / lanes)


def descend(items: list[float], lanes: int, seed: int) -> float:
    """LPT from a perturbed order, then steepest descent.

    Moves one item out of the makespan lane, or swaps a pair between
    it and another lane, accepting only strict improvements.
    """
    # noqa reason: the seed only perturbs a restart order for a
    # packing heuristic. Nothing here is security-relevant.
    rng = random.Random(seed)  # noqa: S311
    order = sorted(items, reverse=True)
    for _ in range(len(order) // 4 if seed else 0):
        a = rng.randrange(len(order))
        b = rng.randrange(len(order))
        order[a], order[b] = order[b], order[a]

    loads = [0.0] * lanes
    lane_items: list[list[float]] = [[] for _ in range(lanes)]
    for duration in order:
        target = min(range(lanes), key=lambda k: loads[k])
        loads[target] += duration
        lane_items[target].append(duration)

    improved = True
    while improved:
        improved = False
        peak = max(range(lanes), key=lambda k: loads[k])
        current = loads[peak]

        for item in list(lane_items[peak]):
            for other in range(lanes):
                if other == peak:
                    continue
                if max(loads[peak] - item, loads[other] + item) < current - 1e-9:
                    lane_items[peak].remove(item)
                    lane_items[other].append(item)
                    loads[peak] -= item
                    loads[other] += item
                    improved = True
                    break
            if improved:
                break
        if improved:
            continue

        for item in list(lane_items[peak]):
            for other in range(lanes):
                if other == peak:
                    continue
                for swap in list(lane_items[other]):
                    if swap >= item:
                        continue
                    after_peak = loads[peak] - item + swap
                    after_other = loads[other] - swap + item
                    if max(after_peak, after_other) < current - 1e-9:
                        lane_items[peak].remove(item)
                        lane_items[other].remove(swap)
                        lane_items[peak].append(swap)
                        lane_items[other].append(item)
                        loads[peak] = after_peak
                        loads[other] = after_other
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
    return max(loads)


def best(items: list[float], lanes: int) -> float:
    return min(descend(items, lanes, seed) for seed in range(RESTARTS))


def fit(accepted: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """MIN/MEDIAN/MAX of each step across the accepted runs.

    Refuses unless every accepted run carries the SAME step names: a
    median over a name one run lacks is a median over a smaller
    sample, and nothing downstream would say so.
    """
    names = sorted(next(iter(accepted.values())))
    for run, steps in accepted.items():
        if sorted(steps) != names:
            missing = set(names) ^ set(steps)
            raise SystemExit(
                f"REFUSING: run {run}'s population differs by {sorted(missing)}. "
                "A per-step median needs the same steps in every run."
            )
    if len(names) != EXPECT_NAMES:
        raise SystemExit(
            f"REFUSING: population is {len(names)} steps, not {EXPECT_NAMES}. "
            "Every figure below is derived from it and would be void."
        )
    return {
        label: {n: pick([steps[n] for steps in accepted.values()]) for n in names}
        for label, pick in (
            ("MIN", min),
            ("MEDIAN", statistics.median),
            ("MAX", max),
        )
    }


def shard(items: dict[str, float]) -> list[float]:
    out: list[float] = []
    for name, duration in items.items():
        if "U3 audit amputation" in name:
            out += [U3_SHARD, U3_SHARD]
        elif "U9 HTTP hardening amputation" in name:
            out += [U9_SHARD, U9_SHARD]
        else:
            out.append(duration)
    return out


def table(label: str, items: dict[str, float], trust_sharded: bool) -> dict[int, float]:
    unsharded = list(items.values())
    sharded = shard(items)
    print(
        f"[{label}] unsharded {len(unsharded)} items {sum(unsharded):.0f}s "
        f"largest {max(unsharded):.0f}s | sharded {len(sharded)} items "
        f"{sum(sharded):.0f}s largest {max(sharded):.0f}s"
    )
    header = f"{'lanes':>5} | {'UNSHARDED LB/LPT/BEST':^26} | "
    header += f"{'SHARDED LB/LPT/BEST':^26} | delta"
    print(header)
    print("-" * 5 + "-+-" + "-" * 26 + "-+-" + "-" * 26 + "-+------")
    deltas: dict[int, float] = {}
    for lanes in (11, 12, 13, 14, 15, 16):
        u_lb = lower_bound(unsharded, lanes) + SETUP
        u_lpt = lpt(unsharded, lanes) + SETUP
        u_best = best(unsharded, lanes) + SETUP
        s_lb = lower_bound(sharded, lanes) + SETUP
        s_lpt = lpt(sharded, lanes) + SETUP
        s_best = best(sharded, lanes) + SETUP
        u_mark = "=" if u_best <= u_lb + 1e-9 else "~"
        s_mark = "=" if s_best <= s_lb + 1e-9 else "~"
        delta = s_best - u_best
        if trust_sharded:
            verdict = "WINS" if delta < -0.5 else ("loses" if delta > 0.5 else "wash")
        else:
            verdict = "n/a  "
        deltas[lanes] = delta
        print(
            f"{lanes:5} | {u_lb:7.1f} {u_lpt:6.1f} {u_best:6.1f}{u_mark} "
            f"| {s_lb:7.1f} {s_lpt:6.1f} {s_best:6.1f}{s_mark} "
            f"| {delta:+6.1f}s {verdict}"
        )
    print()
    return deltas


def main() -> int:
    accepted = accept_runs()
    if len(accepted) < MIN_RUNS:
        raise SystemExit(
            f"REFUSING: {len(accepted)} comparable runs, not {MIN_RUNS}. "
            "A spread fitted from fewer is not a spread."
        )

    fits = fit(accepted)
    total = sum(fits["MEDIAN"].values())
    if abs(total - EXPECT_MEDIAN_TOTAL) > MEDIAN_TOTAL_TOLERANCE:
        raise SystemExit(
            f"REFUSING: sum-of-medians is {total:.0f}s, outside "
            f"{EXPECT_MEDIAN_TOTAL:.0f}+-{MEDIAN_TOTAL_TOLERANCE:.0f}s. "
            "Every figure below is derived from it and would be void."
        )
    print(f"\npopulation: {len(fits['MEDIAN'])} steps, joined on the step name")
    print(
        f"per-lane setup {SETUP:.0f}s (measured "
        f"{SETUP_RANGE[0]:.0f}-{SETUP_RANGE[1]:.0f}s over the accepted lanes), "
        "added to BOTH columns\n"
    )

    print(f"{'step':<48}{'min':>7}{'med':>7}{'max':>7}{'spread':>8}{'x':>7}")
    for name in sorted(fits["MEDIAN"], key=lambda n: -fits["MAX"][n]):
        low, mid, high = (fits[k][name] for k in ("MIN", "MEDIAN", "MAX"))
        ratio = high / low if low else float("inf")
        print(
            f"{name[:46]:<48}{low:7.0f}{mid:7.0f}{high:7.0f}"
            f"{high - low:8.0f}{ratio:7.2f}"
        )
    print()

    deltas = {
        label: table(label, fits[label], trust_sharded=label == "MEDIAN")
        for label in ("MIN", "MEDIAN", "MAX")
    }

    print("'=' means BEST met the lower bound: that cell is PROVED for THAT fit.")
    print("Three fits of ONE population, not three populations: MIN/MEDIAN/MAX")
    print("are taken per step across the accepted runs, so the MIN and MAX")
    print("tables are envelopes no single run produced. Sum-of-medians")
    print(f"({total:.0f}s) exceeds every real run total (3316/3313/3493) for the")
    print("same reason - each step's middle is taken independently.")
    print()
    print("WHAT SURVIVES THE SPREAD. The unsharded LB is max(largest step,")
    print("total/lanes) + setup. At 11-16 lanes the LARGEST STEP dominates in")
    print("every fit, so the unsharded floor is set by ONE step whose own")
    print("run-to-run spread is 118s - and the floor moves with it, from")
    print(
        f"{max(fits['MIN'].values()) + SETUP:.0f}s to "
        f"{max(fits['MAX'].values()) + SETUP:.0f}s. Any margin smaller than that"
    )
    print("is not a finding. The 12-lane margins this file was built to")
    print("adjudicate are 0-8s.")
    print()
    print("THE SHARDED COLUMN IS NOT REFIT. U3 -> 2 x 163.3s and U9 -> 2 x")
    print("219.5s were fitted against ONE run's 304s and 298s. Pairing them")
    print("with MIN or MAX unsharded inputs compares a re-fitted column to a")
    print("stale one, so those verdicts are withheld ('n/a') rather than")
    print("printed. Only the MEDIAN row's verdicts are stated, and even those")
    print("carry #278's contested overhead term.")
    print()
    print("WHICH LANE COUNTS CHANGE SIGN ACROSS THE FITS. Read as a bound on")
    print("what the spread alone can do, NOT as three verdicts:")
    for lanes in sorted(deltas["MEDIAN"]):
        row = [deltas[label][lanes] for label in ("MIN", "MEDIAN", "MAX")]
        flips = "SIGN FLIPS" if min(row) < 0 < max(row) else "same sign"
        print(
            f"  {lanes:2} lanes  min {row[0]:+7.1f}  med {row[1]:+7.1f}  "
            f"max {row[2]:+7.1f}   {flips}"
        )
    print()
    print("The 11-lane loss this file used to call a proved loss was proved")
    print("against ONE run. Re-run the argument per fit before quoting it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
