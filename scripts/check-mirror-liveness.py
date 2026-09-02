#!/usr/bin/env python3
"""Notice when a SCHEDULED workflow has STOPPED, which no run reports.

THE POPULATION IS DERIVED, NOT NAMED (#246). This file was written when
`mirror.yml` was the only cron in the repository, so it named that path
as its default. `ci.yml` acquired `schedule:` later and nothing re-read
the default, so the checker built to catch a silently-disabled cron
could not see the disabling of the workflow it is invoked from - the
"a path allowlist selects for the path nobody thought of" shape, which
this project has now measured eight times. With no `--workflow` the
default is therefore every workflow in `.github/workflows` that carries
a `schedule:` trigger, and a derivation that finds NONE refuses (exit
4) rather than reporting a green over an empty population.

THE TREE IS THE AUTHORITY, not the Actions API. The API lists what
GitHub still remembers, which includes workflows deleted from the tree;
the tree is what a reviewer edits and what a `schedule:` key means to
say. A cron that is not in the tree cannot run, so it is not a cron
this check is answerable for. The cost is stated rather than hidden:
the tree read is of the CHECKED-OUT ref, while the crons GitHub
actually fires come from the default branch, so a schedule added on a
branch is watched one merge before it can fire - early, not late.

`.github/workflows/mirror.yml` reports three states from inside a run:
configured-off, broken, and running-but-copying-nothing. It cannot
report the fourth - that it is not running at all - because the report
lives in a step, and a workflow that does not run has no steps. Its own
header names that residual and says a check outside the file is the
only thing that can see it. This is that check.

WHAT IT READS, and why two things rather than one:

  * the workflow's `state`. GitHub disables a scheduled workflow after
    60 days without repository activity, and that is the documented way
    a cron stops. Reading the state is a DIRECT read of the failure
    mode rather than a proxy for it, so it fires on the first run after
    the disable, whatever the age of the last run happens to be.
  * the age of the most recent run of any event. This catches the stops
    GitHub does not label: a cron silently dropped, a workflow file
    edited into a shape that never triggers, a repository setting that
    suspends Actions.

WHY A CI STEP AND NOT A CRON OF ITS OWN. A cron watching a cron
inherits the whole defect one level up: nobody looks at it either,
which is #18 exactly. Wiring it into CI couples it to pushes, and that
coupling is CORRECT rather than a compromise - the mirror exists to
copy commits, so a stopped mirror matters precisely when there are
commits to copy, which is precisely when CI runs. The 60-day disable is
the sharpest case: during those 60 days nothing needs mirroring, and
the very first push afterwards runs CI, which reads the state and says
so before that push goes uncopied.

WHAT IT DELIBERATELY DOES NOT DO. It does not check that the mirror is
CURRENT. mirror.yml's own first step already compares the two remotes'
refs on every run, needing no token, and duplicating that here would be
a second instrument for one question. This one answers only: is that
step still speaking?

THRESHOLD. Two missed schedules, not one. GitHub's scheduled dispatch
is best-effort and delayable under load, so a 26h window would go red
on a slow morning and teach its readers to ignore it. A stop that
matters persists; 48h catches it on the second day.

EXIT CODES are distinct on purpose, because a configured-off state and
a broken state must not render identically - the lesson mirror.yml
itself was built from:

  0  the workflow is active and has run within the window
  1  STALE: active, but the newest run is older than the window
  2  NEVER RUN: the workflow exists and has no runs at all
  3  DISABLED: the workflow's state is not `active`
  4  COULD NOT MEASURE: the API call failed or was unreadable, or
     the population could not be derived at all

With more than one workflow in the population every one is checked
and the WORST code is returned, because a run that stopped at the
first failure would report on a subset and say nothing about it.

Exit 4 is a failure, not a pass. An instrument that cannot see reports
that it cannot see; it never reports the thing it could not look at.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

DEFAULT_REPO = "evolvconsulting/fast-mcp-jobvite"
DEFAULT_WORKFLOW_DIR = Path(__file__).resolve().parent.parent / ".github/workflows"
DEFAULT_MAX_AGE_HOURS = 48

OK, STALE, NEVER_RUN, DISABLED, UNMEASURABLE = 0, 1, 2, 3, 4


class UnmeasurableError(Exception):
    """The instrument could not look.

    Distinct from looking and finding nothing, which is what the
    NEVER_RUN branch reports.
    """


def scheduled_workflows(directory: Path) -> list[str]:
    """Every workflow under `directory` carrying a `schedule:` trigger.

    PARSED, NOT GREPPED. `grep -l schedule:` counts the word in a
    comment and in a job step name, and this repository has already
    mislabelled four checkers that way; `check-checkers-are-wired.py`
    carries the same reasoning and the same pyyaml dependency.

    `on:` IS THE KEY `True`. YAML 1.1 - which pyyaml implements -
    resolves the bare token `on` to a boolean, so a workflow's trigger
    block arrives under the key `True` and NOT under `"on"`. A lookup
    of only `"on"` returns nothing for every workflow ever written and
    would make this function a confident empty. Both spellings are read
    so a quoted `"on":` is also seen.

    A FILE THAT WILL NOT PARSE IS A MEASUREMENT FAILURE, not a file
    without a schedule. Skipping it would let a broken workflow drop
    silently out of the population, which is the exact silence this
    checker exists to break.
    """
    if not directory.is_dir():
        raise UnmeasurableError(f"{directory} is not a directory")
    found: list[str] = []
    for path in sorted(directory.iterdir()):
        if path.suffix not in (".yml", ".yaml") or not path.is_file():
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise UnmeasurableError(f"{path}: {exc}") from exc
        if not isinstance(doc, dict):
            continue
        triggers = doc.get(True, doc.get("on"))
        if isinstance(triggers, dict):
            names: list[Any] = list(triggers)
        elif isinstance(triggers, list):
            names = list(triggers)
        else:
            names = [triggers]
        if "schedule" in names:
            # RELATIVE WHERE IT CAN BE. The default directory is
            # resolved from `__file__`, so an absolute path is what
            # every message would otherwise carry - and the reader of
            # a CI log wants `.github/workflows/ci.yml`, which is also
            # what the rest of this repository's checkers print.
            try:
                found.append(str(path.relative_to(Path.cwd())))
            except ValueError:
                found.append(str(path))
    return found


def _gh(path: str) -> dict[str, Any]:
    """One `gh api` call, parsed, or raise UnmeasurableError."""
    exe = shutil.which("gh")
    if exe is None:
        raise UnmeasurableError("`gh` is not on PATH, so the API cannot be read")
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [exe, "api", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        # stderr can carry an API message; it never carries the token.
        lines = (proc.stderr or "").strip().splitlines()
        detail = lines[0] if lines else "no output"
        raise UnmeasurableError(f"gh api {path} exited {proc.returncode}: {detail}")
    try:
        parsed: dict[str, Any] = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise UnmeasurableError(
            f"gh api {path} returned unparseable JSON: {exc}"
        ) from exc
    return parsed


def _load(path: Path | None, fetch: str) -> dict[str, Any]:
    if path is not None:
        try:
            loaded: dict[str, Any] = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise UnmeasurableError(f"{path}: {exc}") from exc
        return loaded
    return _gh(fetch)


def _newest_run(runs: dict[str, Any]) -> datetime | None:
    """The newest `created_at`, or None when there are no runs.

    The API returns newest-first, but that ordering is not a documented
    guarantee and an injected fixture need not honour it, so this takes
    the max rather than the head. A run with an unparseable timestamp
    is a measurement failure, not a run to skip - skipping it would
    make a malformed page look like a quiet workflow.
    """
    entries = runs.get("workflow_runs")
    if not isinstance(entries, list):
        raise UnmeasurableError("runs payload has no `workflow_runs` list")
    stamps: list[datetime] = []
    for entry in entries:
        raw = entry.get("created_at")
        if not isinstance(raw, str):
            raise UnmeasurableError(
                f"a run has no readable `created_at`: {entry.get('id')!r}"
            )
        try:
            stamps.append(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError as exc:
            raise UnmeasurableError(f"unreadable `created_at` {raw!r}: {exc}") from exc
    return max(stamps) if stamps else None


def check(
    repo: str,
    workflow: str,
    max_age: timedelta,
    workflow_json: Path | None,
    runs_json: Path | None,
    now: datetime,
) -> int:
    # THE API TAKES THE FILE NAME, NOT THE PATH.
    # `actions/workflows/{id}` accepts a numeric id or a workflow FILE
    # NAME; the full `.github/workflows/...` path 404s. My first live
    # run did exactly that, and the fixture-fed controls could not have
    # caught it - every one of them injects JSON and so never builds a
    # URL. The full path stays in the messages, where a reader wants it.
    name = workflow.rsplit("/", 1)[-1]
    try:
        meta = _load(workflow_json, f"repos/{repo}/actions/workflows/{name}")
        state = meta.get("state")
        if not isinstance(state, str):
            raise UnmeasurableError("workflow payload has no `state`")
        if state != "active":
            print(f"DISABLED: {workflow} is in state {state!r}, not 'active'.")
            print(
                "  GitHub disables a scheduled workflow after 60 days of"
                " repository inactivity and emails the owner. Re-enable"
                " it in the Actions tab."
            )
            return DISABLED

        wf_id = meta.get("id")
        if not isinstance(wf_id, int):
            raise UnmeasurableError("workflow payload has no numeric `id`")
        # THE PAGE SIZE IS THE ORDERING ASSUMPTION, WRITTEN DOWN
        # (R18-M1). `_newest_run` takes the max rather than the head
        # because the API documents no ordering guarantee - and this
        # query then DEPENDS on the ordering that comment distrusts,
        # because the newest run must be ON THE PAGE for a max over
        # the page to find it. The two halves contradicted each
        # other and only one said so.
        #
        # WIDENING REDUCES THE EXPOSURE AND CANNOT REMOVE IT. At 100
        # - the API's maximum for one page - the newest run is
        # missed only if 100 runs were created out of order, a
        # different failure from "the list is not sorted". One
        # request either way, so it is free.
        #
        # Not paginated further ON PURPOSE. This answers "has it run
        # lately", and a workflow whose newest run is past page one
        # of 100 has run plenty; walking pages would spend requests
        # sharpening a number already answered.
        runs = _load(
            runs_json,
            f"repos/{repo}/actions/workflows/{wf_id}/runs?per_page=100&filter=all",
        )
        newest = _newest_run(runs)
    except UnmeasurableError as exc:
        print(f"COULD NOT MEASURE: {exc}")
        print(
            "  This is a failure, not a pass. Nothing here observed"
            f" {workflow}, so nothing here may report on it."
        )
        return UNMEASURABLE

    if newest is None:
        print(f"NEVER RUN: {workflow} is active and has no runs at all.")
        return NEVER_RUN

    age = now - newest
    hours = age.total_seconds() / 3600
    # `g` rather than a fixed precision: the default 48 must not print
    # as "48.0", and a control passing --max-age-hours 0.5 must not
    # print as "0". The first draft used `.0f` and told a positive
    # control it had breached a "0h window", which is the kind of line
    # a reader stops believing.
    limit = f"{max_age.total_seconds() / 3600:g}"
    if age > max_age:
        print(
            f"STALE: {workflow} last ran {hours:.1f}h ago"
            f" ({newest.isoformat()}), over the {limit}h window."
        )
        # THE CADENCE IS NOT ASSUMED (#246). This line used to read
        # "it is scheduled daily, so at least N scheduled run(s) did
        # not happen", which was true of mirror.yml's 04:17 daily cron
        # and FALSE of ci.yml's Sunday one - the same widening that
        # made the population derived made that sentence a guess. The
        # age is measured; how many schedules it swallowed is not, so
        # only the age is printed.
        print(
            f"  That is {hours / 24:.1f} day(s) without a run of any"
            " event. Check the Actions tab and the workflow's own"
            " `schedule:` before assuming it is still firing."
        )
        return STALE

    print(
        f"{workflow}: active, last ran {hours:.1f}h ago"
        f" ({newest.isoformat()}), within the {limit}h window."
    )
    return OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    # REPEATABLE, and empty by default. The default is DERIVED (#246),
    # so there is no path literal here to go stale the next time a
    # workflow acquires a `schedule:`.
    parser.add_argument(
        "--workflow",
        action="append",
        default=[],
        help="check this workflow only; repeatable. Default: every"
        " scheduled workflow in --workflows-dir",
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=DEFAULT_WORKFLOW_DIR,
        help="where the population is derived from when --workflow is absent",
    )
    parser.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    # PAIRED WITH THE POPULATION, IN ORDER, one of each per workflow.
    # The controls feed N workflows N fixtures; a count that disagrees
    # is refused rather than zipped short, because a short zip would
    # leave a workflow unchecked and print nothing about it.
    parser.add_argument(
        "--workflow-json",
        type=Path,
        action="append",
        default=[],
        help="read the workflow object from a file, not the API (controls)",
    )
    parser.add_argument(
        "--runs-json",
        type=Path,
        action="append",
        default=[],
        help="read the runs page from a file, not the API (controls)",
    )
    parser.add_argument(
        "--now",
        help="ISO instant to measure age against, for controls",
    )
    args = parser.parse_args(argv)

    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(UTC)
    )

    try:
        workflows = args.workflow or scheduled_workflows(args.workflows_dir)
    except UnmeasurableError as exc:
        print(f"COULD NOT MEASURE: {exc}")
        print("  The population could not be derived, so nothing was checked.")
        return UNMEASURABLE

    # A DERIVED POPULATION MUST REFUSE ITS OWN EMPTY. Without this the
    # loop below runs zero times and the max over nothing is 0 - a
    # green printed by an instrument that looked at no workflow at
    # all, which is the failure this whole file exists to break. This
    # project has measured a clean zero from a bad path three times in
    # one day; a mistyped --workflows-dir is exactly that path.
    if not workflows:
        print(
            f"COULD NOT MEASURE: no scheduled workflow found in {args.workflows_dir}."
        )
        print(
            "  A repository with a cron has at least one. Either the"
            " directory is wrong or every `schedule:` has been removed;"
            " both are findings, and neither is a pass."
        )
        return UNMEASURABLE

    fixtures = (
        ("--workflow-json", args.workflow_json),
        ("--runs-json", args.runs_json),
    )
    for name, given in fixtures:
        if given and len(given) != len(workflows):
            print(
                f"COULD NOT MEASURE: {len(given)} {name} fixture(s) given"
                f" for a population of {len(workflows)}."
            )
            print("  " + ", ".join(workflows))
            return UNMEASURABLE

    codes = [
        check(
            repo=args.repo,
            workflow=workflow,
            max_age=timedelta(hours=args.max_age_hours),
            workflow_json=args.workflow_json[i] if args.workflow_json else None,
            runs_json=args.runs_json[i] if args.runs_json else None,
            now=now,
        )
        for i, workflow in enumerate(workflows)
    ]
    # THE WORST CODE, not the first and not the last. Every workflow is
    # checked before anything is returned, so a disabled ci.yml is
    # still reported when mirror.yml is healthy. The codes are ordered
    # by severity already - OK 0 < STALE 1 < NEVER_RUN 2 < DISABLED 3 <
    # UNMEASURABLE 4 - so `max` IS "the worst"; that ordering is a
    # property of the constants above and moves if they do.
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())
