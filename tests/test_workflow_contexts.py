"""A workflow expression can be invalid and fail before any job runs.

R3-H1: `mirror.yml` carried a job-level
`if: ${{ secrets.MIRROR_TOKEN != '' }}`. The `secrets` context is NOT
available in a job-level `if:` - GitHub allows `github`, `needs`, `vars`
and `inputs` there - so the expression could not be evaluated, the run
died before a runner was scheduled, and **119 consecutive runs failed
with zero jobs.** Nobody read them, because the file's own comment said
it was "inert until the repository defines a MIRROR_TOKEN secret", and a
broken workflow looked exactly like a switched-off one.

Nothing here could have caught it. `test_workflow_pins.py` checks action
REFS; the suite had no opinion about EXPRESSIONS. A YAML lint would not
help either - the file is valid YAML and the expression is well-formed.
It is invalid only in that one position.

**Why a static check and not "did the last run pass?".** Asking the
Actions API needs the network and credentials, and goes red for reasons
unrelated to the commit under test. This failure is fully determined by
the file, so the file is what gets checked.

**Why this parses by indentation instead of importing PyYAML.** PyYAML
is not a declared dependency. It is present transitively, and a test
that imports it would pass today and break silently the day that
transitive edge moves - which is the same defect already found here
once, with `pydantic-settings`. Adding it to the lock is possible but
the runtime dependency set is a deliberately serialised slot. A
two-level key lookup does not justify either, so `_job_keys` reads the
structure directly and `test_the_parser_sees_the_structure_it_assumes`
fails loudly if the shape it relies on ever changes.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"

#: Contexts GitHub allows in a JOB-level `if:`. `secrets` is
#: deliberately absent - that absence is the whole finding.
JOB_IF_CONTEXTS = frozenset(
    {"github", "needs", "vars", "inputs", "always", "success", "failure", "cancelled"}
)

# `(?<!\.)` is load-bearing: a context is the HEAD of a dotted path,
# and without the lookbehind this read `lanes` and `outputs` out of
# the valid job-level `needs.lanes.outputs.harness` and flagged it
# (#237). The finding this exists for is unaffected: `secrets` heads
# its path.
CONTEXT = re.compile(r"(?<!\.)\b([a-z]+)\s*\.")
JOB_NAME = re.compile(r"^  (?P<name>[A-Za-z_][\w-]*):\s*$")
JOB_KEY = re.compile(r"^    (?P<key>[a-z-]+):(?P<value>.*)$")


def workflows() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def _job_keys(path: Path) -> dict[str, dict[str, str]]:
    """Map each job name to its top-level keys, by indentation.

    Jobs sit at two spaces under `jobs:` and their keys at four. A
    step-level `if:` is indented deeper and is deliberately not
    collected
    - guarding a secret at the step level via `env:` is the SUPPORTED
      pattern and must not be flagged.
    """
    jobs: dict[str, dict[str, str]] = {}
    current: str | None = None
    in_jobs = False

    for line in path.read_text().splitlines():
        if line.startswith("jobs:"):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        # Any non-indented, non-blank line ends the jobs block.
        if line and not line.startswith(" "):
            break
        if m := JOB_NAME.match(line):
            current = str(m.group("name"))
            jobs[current] = {}
            continue
        if current and (m := JOB_KEY.match(line)):
            jobs[current][m.group("key")] = m.group("value").strip()

    return jobs


def test_the_walk_finds_workflows() -> None:
    """Without this, every check below is vacuous over an empty list.

    A glob at a path that does not exist returns a clean empty, which is
    indistinguishable from "no workflow has this defect".
    """
    found = workflows()
    assert found, f"no workflow files under {WORKFLOWS}; every test here is vacuous"
    names = [p.name for p in found]
    assert "mirror.yml" in names, f"mirror.yml is missing; found {names}"


def test_the_parser_sees_the_structure_it_assumes() -> None:
    """The positive control for `_job_keys`.

    Every other test here passes when the parser returns NOTHING, so a
    reformat or a rename could make the whole module vacuous without one
    assertion changing. This pins that the parser really does find jobs
    and really does read their keys.
    """
    jobs = _job_keys(WORKFLOWS / "mirror.yml")
    assert "mirror" in jobs, f"parser found no `mirror` job, only {sorted(jobs)}"
    assert jobs["mirror"].get("runs-on"), "parser found the job but read no `runs-on`"

    ci = _job_keys(WORKFLOWS / "ci.yml")
    assert len(ci) >= 2, f"parser found {len(ci)} jobs in ci.yml; it has more than that"


def test_the_context_finder_reads_only_the_head_of_a_path() -> None:
    """The positive AND negative control for `CONTEXT` (#237).

    The pre-fix regex extracted every `word.` token, so the valid
    job-level expression `needs.<job>.outputs.<name>` - whose `needs`
    context the allowlist above explicitly permits - was flagged on its
    path segments. Both directions are pinned: the regex must still see
    `secrets` heading R3-H1's exact expression, and must see nothing
    forbidden in a needs-outputs path.
    """
    r3h1 = "${{ secrets.MIRROR_TOKEN != '' }}"
    assert "secrets" in set(CONTEXT.findall(r3h1)), (
        "the regex no longer sees `secrets` heading R3-H1's expression; "
        "every check below is blind to the defect this module exists for"
    )
    valid = "${{ needs.lanes.outputs.harness == 'true' }}"
    assert set(CONTEXT.findall(valid)) - JOB_IF_CONTEXTS == set(), (
        "a path segment of a valid needs-outputs expression reads as a "
        "context; job-level fan-out via `needs` becomes impossible"
    )


@pytest.mark.parametrize("path", workflows(), ids=lambda p: p.name)
def test_no_job_level_if_reads_a_context_it_cannot_see(path: Path) -> None:
    """The exact defect R3-H1 found, generalised to every workflow."""
    for job_name, keys in _job_keys(path).items():
        expr = keys.get("if")
        if not expr:
            continue
        forbidden = set(CONTEXT.findall(expr)) - JOB_IF_CONTEXTS
        assert not forbidden, (
            f"{path.name}: job {job_name!r} has a job-level `if:` reading "
            f"{sorted(forbidden)}, which is not available in that position. "
            "The expression fails to evaluate and the run dies before any "
            "job is scheduled - a failure indistinguishable from being "
            "switched off. Guard at the step level via `env:` instead."
        )


def test_the_mirror_reports_its_own_state_on_every_run() -> None:
    """A configured-off mirror and a broken one must not look alike.

    119 red runs went unread because they did. This pins the step that
    makes the two distinguishable without opening the logs, so removing
    it is a deliberate act rather than a quiet regression.
    """
    text = (WORKFLOWS / "mirror.yml").read_text()
    steps = text.split("steps:", 1)
    assert len(steps) == 2, "mirror.yml has no steps block"

    first, _, rest = steps[1].partition("- uses:")
    assert "MIRROR_TOKEN" in first, (
        "the mirror's first step should report whether MIRROR_TOKEN is set, "
        "before anything conditional runs"
    )
    assert "if:" not in first, (
        "the mirror's first step is conditional, so a run with no token "
        "reports nothing at all - the state that hid the defect for 119 runs"
    )
    assert rest, "expected a checkout step after the reporting step"
