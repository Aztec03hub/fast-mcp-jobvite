"""DESIGN.md §8 case #12 - an undeclared marker fails collection.

It does not merely select nothing.

This is the `--strict-markers` guarantee the whole exclusion strategy
rests on (DESIGN.md:1318-1323). Without it, a typo in the exclusion
marker's name selects nothing and the run goes green having tested less
than it claimed - the live suite excluded by accident rather than by
design.

Both arms are required and neither is sufficient alone:
  - negative: pytest against a file marked with a name absent from
    `markers` exits non-zero;
  - positive control: the declared marker still selects its tests, so
    the negative arm cannot be satisfied by a pytest that refuses
    everything.

Each arm runs pytest as a SUBPROCESS against a generated file. Asserting
on this process's own config would be asserting that a dict we just read
says what it says; the property under test is what pytest DOES with it.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

from .conftest import PYPROJECT


def _isolated_project(tmp_path: pathlib.Path, test_body: str) -> pathlib.Path:
    """A temp project inheriting the real pyproject.

    So the real config is what is tested.
    """
    shutil.copy(PYPROJECT, tmp_path / "pyproject.toml")
    (tmp_path / "src" / "fast_mcp_jobvite").mkdir(parents=True)
    (tmp_path / "src" / "fast_mcp_jobvite" / "__init__.py").touch()
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_generated.py").write_text(test_body)
    return tmp_path


def _run_pytest(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


UNDECLARED = """
import pytest

@pytest.mark.jobvite_credentialed_typo
def test_marked_with_a_name_that_is_not_declared():
    assert True
"""

DECLARED = """
import pytest

@pytest.mark.credentialed
def test_carrying_the_declared_marker():
    assert True

def test_unmarked():
    assert True
"""


def test_an_undeclared_marker_fails_collection(tmp_path: pathlib.Path) -> None:
    project = _isolated_project(tmp_path, UNDECLARED)
    proc = _run_pytest(project)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        "pytest accepted an undeclared marker. --strict-markers is not in effect, "
        f"a typo in the exclusion marker would now select nothing silently:\n{combined}"
    )
    assert "jobvite_credentialed_typo" in combined, (
        f"non-zero, but not because of the undeclared marker:\n{combined}"
    )


def test_the_declared_marker_still_selects_its_tests(tmp_path: pathlib.Path) -> None:
    """Positive control.

    A pytest that failed on everything would pass the arm above.
    """
    project = _isolated_project(tmp_path, DECLARED)
    proc = _run_pytest(project, "-m", "credentialed", "--collect-only", "-q")
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"the declared marker did not select cleanly:\n{combined}"
    )
    assert "test_carrying_the_declared_marker" in combined, combined
    assert "test_unmarked" not in combined, (
        f"-m credentialed took an unmarked test; marker not filtering:\n{combined}"
    )


def test_the_default_selection_deselects_the_credentialed_arm(
    tmp_path: pathlib.Path,
) -> None:
    """Zero skips (DESIGN.md:1310-1313), asserted on behaviour.

    The credentialed test must be DESELECTED, not skipped: pytest must
    report `1 deselected` and zero skips.
    """
    project = _isolated_project(tmp_path, DECLARED)
    proc = _run_pytest(project, "-q")
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined
    assert "1 deselected" in combined, (
        f"the credentialed test was not deselected:\n{combined}"
    )
    assert "skipped" not in combined, (
        f"a skip is a green that tested nothing:\n{combined}"
    )
