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

THE SHARD COSTS ARE NOW REFIT PER RUN TOO, and that closes the last
column. They used to be two constants - U3 -> 2 x 163.3s, U9 -> 2 x
219.5s - fitted against dcb2725 alone, so the MIN and MAX tables
differenced a re-fitted unsharded floor against a median-vintage shard
cost. That is two different measurements subtracted, and the verdicts
were withheld ('n/a') rather than printed.

They are recoverable, and from the runs already accepted. Each run's
log carries pytest's own session duration on EVERY invocation
(`===== 13 failed, 119 passed in 10.85s =====`) and the harness prints
a banner per row, so splitting the log at the first banner measures,
per run and in CI:

  B     the baseline invocation
  R     the sum of the row invocations
  ovh   (step wall - B - R) / invocations, a RESIDUAL

Measured over the three accepted runs:

  U3  B 22.3-28.5s   R 221.3-288.9s  ovh 1.26-1.42s  2-shard 141-181s
  U9  B 107.3-181.3s R  71.7-106.4s  ovh 1.47-2.08s  2-shard 155-251s

Two things fall out that the old constants hid. U9's 2-shard cost is
236s at the median against the published 219.5s, so the constant
flattered sharding by 17s at the step that binds. And U9's divisible
share measures 0.42-0.47 against 7a.2's 0.527 - #278's contested
figure of 0.431 sits INSIDE the measured range and 7a.2's does not.

What this does NOT establish: nothing has ever run sharded. k=1
reproduces the wall BY CONSTRUCTION and carries no information. The
model still assumes each shard reruns the whole baseline (#268's
design) and that the residual is per-invocation.

WHAT IS NOT RECOVERABLE, checked and stated: per-ROW wall time. The
harness's stdout reaches Actions in one buffered flush, so all 14 row
banners and the HARNESS-RESULT carry timestamps within 0.005s of each
other at the END of a 298s step. Log timestamps are receive times.
pytest's self-reported duration is the only intra-step clock there is,
which is why the decomposition is built on it.
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

# One list, used for BOTH columns. Two lists would be how the columns
# drift apart again.
PICKERS = (("MIN", min), ("MEDIAN", statistics.median), ("MAX", max))
# Sum-of-medians, which is NOT any run's total: it exceeds all three
# (3316 / 3313 / 3493) because it takes each step's middle
# independently. Recorded as a band so the ground moving is loud.
EXPECT_MEDIAN_TOTAL = 3413.0
MEDIAN_TOTAL_TOLERANCE = 60.0

# The two steps #268 designed a shard for, each mapped to the harness
# script whose log carries its per-row timings and to its DECLARED row
# count. The row count is an expectation, not a discovery: a harness
# that gains or loses a row must stop this probe, not quietly re-derive
# a different shard cost.
SHARDABLE = {
    "U3 audit amputation harness ran every row": ("check-u3-audit-amputation", 10),
    "U9 HTTP hardening amputation, every row applied": (
        "check-u9-http-amputation",
        14,
    ),
}
SHARD_K = 2

# pytest's own session line, e.g.
#   ===== 889 passed, 6 deselected in 172.74s (0:02:52) =====
# and  ===== 13 failed, 119 passed in 10.85s =====
PYTEST_SUMMARY = re.compile(r"=+.*?\b\d+ (?:passed|failed|error)\b.*?\bin ([\d.]+)s")
ROW_BANNER = re.compile(r"#{5,} A\d+\b")

# Measured 2-shard costs move with the fit, so a band rather than a
# literal: if the logs change shape these move and the reader should see
# it. Recorded from the three accepted runs on 2026-09-02.
EXPECT_SHARD_BAND = {
    "U3 audit amputation harness ran every row": (130.0, 195.0),
    "U9 HTTP hardening amputation, every row applied": (145.0, 265.0),
}

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


_LOG_CACHE: dict[str, bytes] = {}


def read_logs(run: str) -> bytes:
    """The run's log zip. Cached: two readers want the same download."""
    if run not in _LOG_CACHE:
        result = subprocess.run(
            ["gh", "api", f"repos/:owner/:repo/actions/runs/{run}/logs"],
            capture_output=True,
            cwd=REPO,
        )
        if result.returncode != 0 or not result.stdout:
            raise SystemExit(f"REFUSING: could not fetch logs for run {run}")
        _LOG_CACHE[run] = result.stdout
    return _LOG_CACHE[run]


def shard_profile(run: str, walls: dict[str, float]) -> dict[str, float]:
    """This run's OWN 2-shard cost for each shardable harness.

    The shard cost used to be two constants fitted to ONE run, so the
    MIN and MAX tables differenced a re-fitted unsharded column against
    a median-vintage sharded one. It is measured per run instead, from
    the run's own log, because pytest prints its session duration on
    every invocation and the harness prints a banner per row:

        B     the baseline invocation, before the first row banner
        R     the sum of the row invocations, after it
        ovh   (step wall - B - R) / invocations, a RESIDUAL: uv spawn,
              pytest import, the cp/anchor/cmp file work, log flush

    A shard reruns the baseline and 1/k of the rows, so

        step(k) = B + R/k + ovh * (1 + rows/k)

    and k=1 reproduces the measured wall BY CONSTRUCTION - that closure
    carries no information and is not offered as validation. What is
    measured is the DECOMPOSITION, per run, in CI, at n=3.

    NOTHING HAS EVER RUN SHARDED. This is still a model; it is now a
    model whose terms were measured on the machine that will run it,
    rather than transferred from a local box at a fitted scale.
    """
    costs: dict[str, float] = {}
    with zipfile.ZipFile(io.BytesIO(read_logs(run))) as archive:
        for step_name, (script, expect_rows) in SHARDABLE.items():
            found = False
            for entry in archive.namelist():
                if "/" in entry:
                    continue
                lines = archive.read(entry).decode("utf-8", "replace").splitlines()
                hits = [i for i, line in enumerate(lines) if script in line]
                if not hits:
                    continue
                segment = lines[hits[0] : hits[-1] + 1]
                if not any(ROW_BANNER.search(line) for line in segment):
                    continue
                baseline, rows_seen, seen = [], [], False
                for line in segment:
                    if ROW_BANNER.search(line):
                        seen = True
                    matched = PYTEST_SUMMARY.search(line)
                    if matched:
                        target = rows_seen if seen else baseline
                        target.append(float(matched.group(1)))
                # A regex that stops matching returns a CLEAN ZERO here:
                # B = R = 0, the whole wall becomes residual, and the
                # shard cost silently collapses. Refuse instead.
                if len(baseline) != 1 or len(rows_seen) != expect_rows:
                    raise SystemExit(
                        f"REFUSING: run {run} {script} parsed "
                        f"{len(baseline)} baseline and {len(rows_seen)} row "
                        f"pytest summaries, expected 1 and {expect_rows}. The "
                        "shard cost is derived from them and would be void."
                    )
                b, r = baseline[0], sum(rows_seen)
                ovh = (walls[step_name] - b - r) / (1 + expect_rows)
                costs[step_name] = b + r / SHARD_K + ovh * (1 + expect_rows / SHARD_K)
                found = True
                break
            if not found:
                raise SystemExit(
                    f"REFUSING: run {run} has no log segment for {script}. "
                    "Its shard cost cannot be measured from this run."
                )
    return costs


def work_signature(run: str) -> str:
    """Hash the run's own HARNESS-RESULT (name, rows) multiset."""
    rows: list[bytes] = []
    with zipfile.ZipFile(io.BytesIO(read_logs(run))) as archive:
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


def accept_runs() -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """Print every candidate with its verdict, then refuse or return.

    Returns the per-run step populations AND the per-run 2-shard costs,
    so both columns of every table are fitted from the same three runs.
    """
    accepted: dict[str, dict[str, float]] = {}
    shards: dict[str, dict[str, float]] = {}
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
        shards[run] = shard_profile(run, accepted[run])
        costs = " ".join(f"{n.split()[0]} {c:.1f}s" for n, c in shards[run].items())
        print(f"  accept {run} {short}: {len(accepted[run])} steps, shard {costs}")
    return accepted, shards


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
        for label, pick in PICKERS
    }


def fit_shards(shards: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """The SAME three pickers over the SAME three runs' shard costs.

    This is the asymmetry the previous round left open. Fitting the
    unsharded column from MIN/MEDIAN/MAX and holding the sharded column
    at one run's value made every delta but the median a difference
    between two unlike measurements.
    """
    names = sorted(SHARDABLE)
    fitted = {
        label: {n: pick([s[n] for s in shards.values()]) for n in names}
        for label, pick in PICKERS
    }
    for name in names:
        low, high = EXPECT_SHARD_BAND[name]
        for label, costs in fitted.items():
            if not low <= costs[name] <= high:
                raise SystemExit(
                    f"REFUSING: {label} 2-shard cost for {name!r} is "
                    f"{costs[name]:.1f}s, outside the recorded {low:.0f}-"
                    f"{high:.0f}s band. Every sharded cell derives from it."
                )
    return fitted


def shard(items: dict[str, float], costs: dict[str, float]) -> list[float]:
    """Replace each shardable step by SHARD_K copies of THIS fit's cost.

    `costs` is fitted by the same MIN/MEDIAN/MAX picker over the same
    three runs as `items`, so both columns are the same envelope of the
    same population. That is the whole point: differencing a MIN-fit
    unsharded floor against a median-vintage shard cost was subtracting
    two different measurements.
    """
    out: list[float] = []
    for name, duration in items.items():
        if name in costs:
            out += [costs[name]] * SHARD_K
        else:
            out.append(duration)
    return out


def table(
    label: str, items: dict[str, float], costs: dict[str, float]
) -> dict[int, float]:
    unsharded = list(items.values())
    sharded = shard(items, costs)
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
        verdict = "WINS" if delta < -0.5 else ("loses" if delta > 0.5 else "wash")
        deltas[lanes] = delta
        print(
            f"{lanes:5} | {u_lb:7.1f} {u_lpt:6.1f} {u_best:6.1f}{u_mark} "
            f"| {s_lb:7.1f} {s_lpt:6.1f} {s_best:6.1f}{s_mark} "
            f"| {delta:+6.1f}s {verdict}"
        )
    print()
    return deltas


def main() -> int:
    accepted, shards = accept_runs()
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

    shard_fits = fit_shards(shards)
    print("2-shard costs, fitted by the SAME picker over the SAME three runs:")
    for name in sorted(SHARDABLE):
        per_run = " ".join(f"{s[name]:7.1f}" for s in shards.values())
        line = " ".join(
            f"{label} {shard_fits[label][name]:6.1f}" for label, _ in PICKERS
        )
        print(f"  {name[:46]:<48} runs {per_run}  ->  {line}")
    print()

    deltas = {
        label: table(label, fits[label], shard_fits[label]) for label, _ in PICKERS
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
    print("THE SHARDED COLUMN IS NOW REFIT PER FIT, so every verdict is")
    print("stated. B, R and the per-invocation residual are read from each")
    print("run's OWN log - pytest prints its session duration on every")
    print("invocation - so both columns are the same envelope over the same")
    print("three runs. The old 2 x 163.3s / 2 x 219.5s constants came from")
    print("ONE run via a local-box profile scaled by a fitted 1.567x/1.703x;")
    print("the measured CI decomposition puts U9's 2-shard cost at 236s")
    print("median, 17s ABOVE the constant, so the old figure flattered")
    print("sharding at the step that binds.")
    print()
    print("WHAT IS STILL NOT ESTABLISHED. Nothing has ever run sharded. The")
    print("k=1 identity closes BY CONSTRUCTION and validates nothing; the")
    print("model assumes each shard reruns the whole baseline (#268's design)")
    print("and that the residual is per-invocation. Those are assumptions,")
    print("now carried on measured terms rather than unsourced ones.")
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
    lo = {n: min(deltas[k][n] for k, _ in PICKERS) for n in deltas["MEDIAN"]}
    hi = {n: max(deltas[k][n] for k, _ in PICKERS) for n in deltas["MEDIAN"]}
    flips = [n for n in sorted(lo) if lo[n] < 0 < hi[n]]
    firm = sorted(set(lo) - set(flips))
    print(f"DETERMINATE at {firm} lanes: every fit agrees on the sign, so the")
    print("verdict there does not depend on which run was sampled.")
    print(f"NOT DETERMINATE at {flips}.")
    print()
    print("Refitting the sharded column did NOT settle 12 lanes; it narrowed")
    print(f"it, from a 31.7s envelope (+19.0/-12.7) to {hi[12] - lo[12]:.1f}s.")
    print("The 13-lane cell DID close - it read +1.5/-27.0/-37.0 and is now a")
    print("win in all three fits. What 12 lanes still needs is not a better")
    print("fit of these three runs: their spread alone is wider than the")
    print("margin. It needs a sharded run to exist, so the model can be")
    print("checked against something other than the k=1 identity it")
    print("reproduces by construction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
