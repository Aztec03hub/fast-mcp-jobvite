"""The suite-floor guard, exercised against real pytest summary lines.

`ci.yml`'s original guard was `grep -qE '[1-9][0-9]* passed'`, which is satisfied
by "1 passed". These tests exist because that guard's defect was invisible to
every other check in the pipeline: the exit code was 0, the zero-skip grep found
no skips, and coverage is a RATIO, so deleting a test together with the code it
covered can raise it.

The tests below drive `scripts/check-suite-floor.sh` as a subprocess and read its
exit code, rather than reimplementing its parsing here. A test that reimplements
the logic it is checking agrees with itself by construction.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check-suite-floor.sh"

#: A real summary line, copied verbatim from a run rather than hand-written. A
#: hand-written fixture tests the format the author had in mind.
#:
#: `noqa: E501` rather than a reflow: pytest's own summary is 97 columns wide and
#: its exact bytes are the fixture. Wrapping it, or trimming the `=` padding to
#: fit, would make this a line resembling pytest's output instead of one of them -
#: and the padding is precisely what the guard's regex has to survive.
REAL_SUMMARY = (
    "====================== 333 passed, 2 deselected in 21.73s ======================"  # noqa: E501
)

#: DERIVED from REAL_SUMMARY, never written twice.
#:
#: These were literals until updating REAL_SUMMARY to a fresher run left them
#: behind. The damage was not a red test - it was that
#: `test_a_run_below_the_floor_fails` would have fed a 333-test summary against a
#: floor of 323, which the guard correctly PASSES. The test asserting the guard
#: rejects a shrunken suite would have been asserting the opposite, and its name
#: would still have read correctly. A test name is an unverified claim about its
#: body, and a stale literal is how the two come apart.
COUNT = int(re.search(r"(\d+) passed", REAL_SUMMARY).group(1))  # type: ignore[union-attr]
ABOVE = str(COUNT + 1)
AT = str(COUNT)
BELOW = str(COUNT - 22)


def run(output: str, floor: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), floor],
        input=output,
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_script_exists_and_is_the_one_ci_runs() -> None:
    """Guards the whole module against a rename.

    Every other test here would pass vacuously if the path were wrong: bash exits
    127, the assertions on non-zero exit codes still hold, and the suite stays
    green while checking nothing. A search at a path that does not exist returns a
    clean empty, which is indistinguishable from a real absence.
    """
    assert SCRIPT.is_file(), f"{SCRIPT} is missing; the rest of this module is vacuous"
    ci = (SCRIPT.parent.parent / ".github" / "workflows" / "ci.yml").read_text()
    assert "check-suite-floor.sh" in ci, "the script exists but ci.yml does not call it"


def test_a_run_at_the_floor_passes() -> None:
    assert run(REAL_SUMMARY, AT).returncode == 0


def test_a_run_above_the_floor_passes() -> None:
    assert run(REAL_SUMMARY, BELOW).returncode == 0


def test_a_run_below_the_floor_fails() -> None:
    """The defect this whole file exists for."""
    result = run(REAL_SUMMARY, ABOVE)
    assert result.returncode == 1
    assert f"{COUNT} passed, but the floor is {ABOVE}" in result.stderr


def test_the_original_guards_blind_spot_is_now_caught() -> None:
    """`grep -qE '[1-9][0-9]* passed'` accepts this. The floor must not.

    This is the exact scenario L6 named: a suite that has lost almost every test
    still prints a passing summary, and the old guard could not tell it from a
    healthy run.
    """
    one_test = "======================== 1 passed in 0.04s ========================"
    assert run(one_test, AT).returncode == 1


def test_output_with_no_summary_line_is_a_failure_not_a_pass() -> None:
    """Fail closed on garbage.

    An empty or truncated capture must not read as success. The failure mode this
    forbids is a guard that treats "I could not find a count" as "the count was
    fine" - which is how an except-branch that fails closed still fails OPEN on
    empty input.
    """
    for junk in ("", "INTERNALERROR> the run died", "collected 0 items"):
        result = run(junk, "1")
        assert result.returncode == 1, f"a floor guard passed on {junk!r}"


def test_a_tests_own_stdout_cannot_spoof_the_count() -> None:
    """The summary is the LAST match, not the first.

    A test that prints something resembling a summary line - this suite has tests
    that assert on pytest output - would otherwise be read as the run's own
    result, and it appears EARLIER than the real summary.
    """
    spoofed = f"a test printed '999 passed' while running\n{REAL_SUMMARY}"
    result = run(spoofed, ABOVE)
    assert result.returncode == 1, "the guard read a test's stdout as the run's summary"
    assert f"{COUNT} passed" in result.stderr


@pytest.mark.parametrize("bad_floor", ["", "abc", "-1", "3.5"])
def test_a_floor_that_is_not_a_count_is_a_usage_error(bad_floor: str) -> None:
    """Exit 2, distinct from the exit 1 that means the suite shrank.

    Collapsing these would make a typo in ci.yml look like a real regression, and
    the person debugging it would go looking for deleted tests that do not exist.
    """
    assert run(REAL_SUMMARY, bad_floor).returncode == 2
