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

  unsharded  largest 298s > 3311/12 = 275.9  a meeting packing EXISTS
  sharded    largest 227s < 3521/12 = 293.4  AREA-bound, upper bound

So the "regression" was an exact number differenced against an upper
bound. Sweeping the INPUTS could never reveal it, because both columns
were computed with the same biased estimator and the bias moved with
them. The algorithm was the variable nobody varied.

WHAT THIS COMPUTES, per column and lane count:

  LB    max(largest item, total / lanes)     a true lower bound
  LPT   the greedy result                    an upper bound
  BEST  LPT + steepest descent, restarts     a tighter upper bound
  '='   BEST met LB, so that cell is PROVED rather than estimated

A bracket is the honest object here. Where BEST meets LB the answer is
certain; where it does not, the true value lies between them and the
direction of any remaining slack is stated rather than hidden.

WHAT IT IS NOT. Not a gate. Its inputs are one historical GitHub run,
so nothing in this repository can regress it, and wiring it would gate
the trunk on the Actions API being reachable. Re-run it by hand when
the step population, the lane count, or the fitted shard costs change.

IT ASSERTS ITS OWN POPULATION AND ABORTS IF IT MOVES. An earlier
version hard-coded a plausible-looking list of 31 step durations; it
summed to 3824s against the real 3311s, because the
durations were invented. Printing both totals is the only reason that
was caught, so the count and the total are now assertions and every
duration is fetched from the run. 31 matched no real subset: the
population is 33 steps, of which 15 are amputation-named and 18 are
not.

THE SHARD COSTS ARE FITTED, NOT MEASURED. U3 -> 2 x 163.3s and
U9 -> 2 x 219.5s come from a model whose overhead term task #278
contests by a factor of 17-20. The sharded column inherits that
uncertainty; the unsharded column does not.
"""

import datetime
import json
import random
import subprocess
from typing import Any

REPO = "/home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite"

# The only post-repack run. Mixing it with earlier runs would
# average two packings - a separate error this section made once.
RUN = "33630968540"

# GitHub's own per-job wrapper steps. Per-job overhead, not work
# that can move between lanes, so not part of the population.
WRAP = (
    "Set up job",
    "Complete job",
    "Post ",
    "Checkout",
    "Install uv",
    "Set up Python",
    "Run actions/",
    "setup-python",
)

# per-lane setup. THIS RUN'S 12 LANES READ 8-17s (median 11.5); 13.0
# is one lane, not the middle. Added to BOTH columns, so it cancels in
# every delta and biases only the absolutes. NOT moved to the median on
# purpose: every absolute published in REVAMP-238-ci.md 7a.2 carries
# 13.0, and changing it here would move all of them.
SETUP = 13.0
EXPECT_STEPS = 33
EXPECT_TOTAL = 3311.0
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


def harness_steps() -> list[tuple[str, float]]:
    """Steps in a harness-* job of >= 5s, wrappers excluded."""
    steps: list[tuple[str, float]] = []
    jobs = api(f"repos/:owner/:repo/actions/runs/{RUN}/jobs?per_page=100")
    for job in jobs["jobs"]:
        if not job["name"].lower().startswith("harness"):
            continue
        for step in job.get("steps") or []:
            if not (step.get("started_at") and step.get("completed_at")):
                continue
            seconds = (
                parse_time(step["completed_at"]) - parse_time(step["started_at"])
            ).total_seconds()
            named = step["name"]
            if seconds < 5:
                continue
            if any(named.startswith(w) or w in named for w in WRAP):
                continue
            steps.append((named, seconds))
    return steps


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


def main() -> int:
    steps = harness_steps()
    total = sum(d for _, d in steps)
    largest = max(d for _, d in steps)
    print(f"population: {len(steps)} steps, {total:.0f}s, largest {largest:.0f}s")

    if len(steps) != EXPECT_STEPS:
        raise SystemExit(
            f"REFUSING: population is {len(steps)}, not {EXPECT_STEPS}. "
            "Every figure below is derived from it and would be void."
        )
    if abs(total - EXPECT_TOTAL) > 1.5:
        raise SystemExit(
            f"REFUSING: total is {total:.0f}s, not {EXPECT_TOTAL:.0f}s. "
            "Every figure below is derived from it and would be void."
        )

    unsharded = [d for _, d in steps]
    sharded: list[float] = []
    for name, duration in steps:
        if "U3 audit amputation" in name:
            sharded += [U3_SHARD, U3_SHARD]
        elif "U9 HTTP hardening amputation" in name:
            sharded += [U9_SHARD, U9_SHARD]
        else:
            sharded.append(duration)
    print(
        f"sharded:    {len(sharded)} items, {sum(sharded):.0f}s, "
        f"largest {max(sharded):.0f}s"
    )
    print()

    header = f"{'lanes':>5} | {'UNSHARDED LB/LPT/BEST':^26} | "
    header += f"{'SHARDED LB/LPT/BEST':^26} | delta"
    print(header)
    print("-" * 5 + "-+-" + "-" * 26 + "-+-" + "-" * 26 + "-+------")

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
        verdict = "WINS" if delta < -0.5 else ("loses" if delta > 0.5 else "wash")
        print(
            f"{lanes:5} | {u_lb:7.1f} {u_lpt:6.1f} {u_best:6.1f}{u_mark} "
            f"| {s_lb:7.1f} {s_lpt:6.1f} {s_best:6.1f}{s_mark} "
            f"| {delta:+6.1f}s {verdict}"
        )

    print()
    print("'=' means BEST met the lower bound: that cell is PROVED.")
    print("All figures include the per-lane setup. Sharded cells are UPPER")
    print("BOUNDS, so each could be a few seconds better - which only widens")
    print("any win. Shard costs are FITTED; see task #278.")
    print("Absolutes carry the setup spread (306-315s unsharded); deltas do not.")
    print("11 lanes is a proved loss UNDER THE FITTED SHARD COSTS, not a search")
    print("artefact: the sharded LOWER bound (333.05) exceeds an EXHIBITED")
    print("unsharded packing (316.00), so no search budget can overturn it.")
    print("It is NOT input-independent. Re-fitting in #278's direction (the")
    print("overhead term deleted) WIDENS the loss to 20.17s; at ZERO shard")
    print("overhead the same bound REVERSES - 314.00 against the exhibited")
    print("316.00 - and an exhibited zero-overhead packing reaches 315.00, a")
    print("1.0s win. #278 measures that term at 130ms against the 2.24-2.64s")
    print("fitted here, so the reversing end of the range is the one the")
    print("evidence points at. This row is budget-independent, not")
    print("input-independent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
