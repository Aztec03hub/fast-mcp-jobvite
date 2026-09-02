#!/usr/bin/env python3
r"""Size a CI timeout from runs that reached the step, and say how many.

#154 asks for timeout bounds. The wrong way to answer it is the way I
answered it once already: rank the last N runs' step durations and cap
from the maximum. On a trunk that has never been green, that maximum is
a property of how far the job got before dying, not of the job.

MEASURED TWICE ON THIS PROJECT. A cap sized from twelve runs gave a
151s maximum against a true 7522s - fifty times out - because all
twelve died at an early gate. Then on 2026-09-02 I published that "the
U4 client amputation harness is the step holding CI past 73 minutes",
and the first run to survive its early gates measured U9's amputation
at 1270s and U0's controls at 927s with U4's amputation NOT YET RUN.

So this tool refuses to print a maximum without printing the number of
runs that REACHED the step it belongs to. A duration with no reach
count is the shape that produced both errors.

WHAT IT DOES NOT DO. It does not choose the cap. A cap is a decision
about how much headroom a step deserves and what a timeout costs when
it fires, and that belongs to whoever is deciding, in writing, with
this table beside them.

    uv run --frozen python docs/reviews/measure-ci-step-durations.py \\
        [--repo OWNER/NAME] [--workflow ci.yml] [--runs N] [--job NAME]

Reads the Actions API through `gh`. Read-only; it writes nothing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

DEFAULT_REPO = "evolvconsulting/fast-mcp-jobvite"
DEFAULT_WORKFLOW = "ci.yml"


def gh(path: str) -> dict[str, Any]:
    exe = shutil.which("gh")
    if exe is None:
        raise SystemExit("`gh` is not on PATH, so the Actions API cannot be read.")
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [exe, "api", path], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        lines = (proc.stderr or "").strip().splitlines()
        detail = lines[0] if lines else ""
        raise SystemExit(f"gh api {path} exited {proc.returncode}: {detail}")
    parsed: dict[str, Any] = json.loads(proc.stdout)
    return parsed


def seconds(started: str | None, completed: str | None) -> float | None:
    """Duration, or None when either end is missing.

    A step that is still running, or was never reached, has no duration.
    Returning None rather than 0 keeps it OUT of the maxima - a zero
    would silently drag an average down and would count as a reach.
    """
    if not started or not completed:
        return None
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        a = datetime.strptime(started, fmt).replace(tzinfo=UTC)
        b = datetime.strptime(completed, fmt).replace(tzinfo=UTC)
    except ValueError:
        return None
    return (b - a).total_seconds()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument(
        "--runs", type=int, default=20, help="how many recent runs to read"
    )
    parser.add_argument("--job", help="only this job name")
    parser.add_argument("--top", type=int, default=20, help="how many steps to print")
    args = parser.parse_args(argv)

    listing = gh(
        f"repos/{args.repo}/actions/workflows/{args.workflow}"
        f"/runs?per_page={args.runs}&filter=all"
    )
    runs = listing.get("workflow_runs") or []
    if not runs:
        print("NO RUNS. An empty population and a fast workflow are the same")
        print("zero here, so this is a failure rather than a clean result.")
        return 2

    # per (job, step) -> list of durations; and per job -> total per run
    durations: dict[tuple[str, str], list[float]] = defaultdict(list)
    job_totals: dict[str, list[float]] = defaultdict(list)
    # EVERY step the API mentioned, whether or not it ever finished. The
    # ranked table below can only list steps that HAVE a duration, so on
    # its own it reports the absence of a slow step as the absence of a
    # problem - which is the error this whole file was written after, in
    # its own instrument. A step that appears here and not there is one
    # nobody has timed.
    seen: set[tuple[str, str]] = set()
    runs_read = 0
    runs_with_jobs = 0

    for run in runs:
        runs_read += 1
        jobs = gh(f"repos/{args.repo}/actions/runs/{run['id']}/jobs").get("jobs") or []
        if jobs:
            runs_with_jobs += 1
        for job in jobs:
            name = job.get("name", "?")
            if args.job and name != args.job:
                continue
            total = seconds(job.get("started_at"), job.get("completed_at"))
            if total is not None:
                job_totals[name].append(total)
            for step in job.get("steps") or []:
                key = (name, step.get("name", "?"))
                seen.add(key)
                d = seconds(step.get("started_at"), step.get("completed_at"))
                if d is not None:
                    durations[key].append(d)

    print(f"repo     : {args.repo}")
    print(f"workflow : {args.workflow}")
    print(f"runs read: {runs_read}")
    print(
        f"runs that scheduled ANY job: {runs_with_jobs}"
        "   (the rest died before a runner existed and time nothing)"
    )
    if not durations:
        print()
        print("NO STEP EVER COMPLETED in these runs. This is the failure this")
        print("tool exists for: a maximum over an empty set is not a bound.")
        return 2

    print()
    print("JOB TOTALS  (max, n = runs in which the job COMPLETED):")
    for name, values in sorted(job_totals.items(), key=lambda kv: -max(kv[1])):
        top = max(values)
        print(f"  {top:8.0f}s  ({top / 60:6.1f} min)  n={len(values):3}  {name}")

    print()
    print(f"SLOWEST STEPS  (max, n = runs that REACHED the step), top {args.top}:")
    ranked = sorted(durations.items(), key=lambda kv: -max(kv[1]))
    for (job, step), values in ranked[: args.top]:
        top = max(values)
        print(
            f"  {top:8.0f}s  ({top / 60:6.1f} min)  n={len(values):3}  {job} >> {step}"
        )

    # THE WARNING IS NOT OPTIONAL. A reader who takes the table above
    # and nothing else will size a cap from a step that half the runs
    # never reached, which is exactly what this file was written after.
    thin = [(j, s, len(v)) for (j, s), v in ranked if len(v) < runs_with_jobs]
    print()
    if thin:
        print(f"{len(thin)} step(s) were reached by FEWER runs than scheduled a job.")
        print("Their maxima are lower bounds, not bounds. The five thinnest:")
        for job, step, n in sorted(thin, key=lambda t: t[2])[:5]:
            print(f"  n={n:3} of {runs_with_jobs}   {job} >> {step}")
    else:
        print(
            f"Every step was reached by all {runs_with_jobs} runs that scheduled a job."
        )
    never = sorted(seen - set(durations))
    print()
    if never:
        print(f"{len(never)} step(s) EXIST in these runs and have NEVER COMPLETED.")
        print("They have no duration at all, so they cannot appear above. A")
        print("ranking that omits them is a ranking of what finished:")
        for job, step in never[:10]:
            print(f"  never timed   {job} >> {step}")
        if len(never) > 10:
            print(f"  ... and {len(never) - 10} more")
    else:
        print("Every step the API mentioned completed at least once.")

    print()
    print("A MAXIMUM WITHOUT ITS REACH COUNT IS NOT A BOUND. Size a cap from")
    print("runs that reached the step, and record how many did beside it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
