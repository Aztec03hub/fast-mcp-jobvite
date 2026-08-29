#!/usr/bin/env python3
"""Re-run every measurement IMPLEMENTATION-PLAN.md rests a decision on.

**Why this file exists.** The plan justifies four decisions with
measurements that were run once, by hand, and then written up in prose.
Prose about a measurement decays into a *claim* about one: the next
reader inherits the conclusion and not the evidence, and nothing reports
it when the underlying behaviour changes. Rounds 6 and 7 each re-ran
some of these by hand and reproduced them, which is the right instinct
and the wrong mechanism
- it does not scale past the reviewer who happened to think of it.

Each probe below is **two-armed**: a treatment that must fail and a
control that must pass. A probe with only the arm the author expected is
the failure mode this project has paid for repeatedly - it cannot tell a
real result from an instrument that always says the same thing.

Run: `python3 docs/reviews/check-plan-measurements.py` Exit 0 = every
measurement the plan cites still reproduces. Non-zero = a plan claim has
gone stale, and the plan is what needs fixing, not this script.

**M4 WAS EXPECTED TO FAIL, AND NO LONGER DOES.** It is the eleventh
collision, found by round 7 and independently reproduced: a real defect
in `tests/test_collection_guard.py`, not a stale claim. The guard passed
`-m` to its own collection call, so a file whose tests are all
deselected read as unreachable. Dropping `-m` fixed it and M4 went
green, which is what a documented-open probe is for - it is now a
regression test rather than a record of a defect. Do not "fix" any probe
here to make it green.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_PY = REPO_ROOT / ".venv" / "bin" / "python"
PYTHON = str(VENV_PY if VENV_PY.exists() else sys.executable)

FIXTURE_PLUGIN = (
    "import pytest\n\n\n@pytest.fixture\n"
    "def mock_transport():\n    return 'MT'\n"
)
USES_FIXTURE = "def test_uses(mock_transport):\n    assert mock_transport == 'MT'\n"


def _pytest(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def m1_pytest_plugins_in_a_non_rootdir_conftest() -> tuple[bool, str]:
    """§4's fixture mechanism: `pytest_plugins` in `tests/conftest.py`.

    The plan mandates this and the obvious objection is real elsewhere -
    some pytest lineages refuse `pytest_plugins` outside the rootdir
    conftest. Treatment: it loads AND the fixture resolves, which is the
    positive control that it actually loaded rather than being silently
    ignored. Control: the same tree without the registration must FAIL,
    or the treatment proves nothing.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tests" / "fixtures").mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "probe"\nversion = "0"\n'
            '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        )
        (root / "tests" / "__init__.py").touch()
        (root / "tests" / "fixtures" / "__init__.py").touch()
        (root / "tests" / "fixtures" / "transport.py").write_text(FIXTURE_PLUGIN)
        (root / "tests" / "test_uses.py").write_text(USES_FIXTURE)

        (root / "tests" / "conftest.py").write_text(
            'pytest_plugins = ["tests.fixtures.transport"]\n'
        )
        treatment = _pytest(root, "-W", "error")

        (root / "tests" / "conftest.py").write_text("")
        control = _pytest(root)

    if treatment.returncode != 0:
        return False, f"registered plugin did NOT load (rc={treatment.returncode})"
    if control.returncode == 0:
        return False, "control passed without registration - the probe proves nothing"
    return True, "loads under -W error; unregistered control fails as required"


def m2_per_directory_conftest_does_not_cross_directories() -> tuple[bool, str]:
    """Why §4 rejected conftest-per-directory: siblings cannot see it.

    This is the measurement the choice rests on. Treatment: the sibling
    directory's test must ERROR with 'fixture not found'. Control: the
    test in the conftest's OWN directory must pass, or the fixture was
    simply broken and the probe is vacuous.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tests" / "tools").mkdir(parents=True)
        (root / "tests" / "client").mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "probe"\nversion = "0"\n'
            '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        )
        (root / "tests" / "tools" / "conftest.py").write_text(FIXTURE_PLUGIN)
        (root / "tests" / "tools" / "test_here.py").write_text(USES_FIXTURE)
        (root / "tests" / "client" / "test_there.py").write_text(USES_FIXTURE)

        same_dir = _pytest(root, "tests/tools")
        sibling = _pytest(root, "tests/client")

    if same_dir.returncode != 0:
        return False, (
            "control failed: fixture broken in its OWN directory, probe vacuous"
        )
    if "fixture 'mock_transport' not found" not in sibling.stdout:
        return False, "sibling directory RESOLVED the fixture - §4's rejection is stale"
    return True, "sibling cannot see it; same directory can - rejection holds"


def m3_manifest_asserts_a_closed_dependency_set() -> tuple[bool, str]:
    """Collision 10: `test_manifest.py` closes the dependency list.

    **This probe RUNS the test. An earlier version graded a SUBSTRING of
    it, and a review demonstrated the difference.** It checked
    `"set(_dependencies()) ==" in manifest_test`, which is a grep of the
    test's source. Renaming the function so pytest stops collecting it -
    the most realistic form of "someone disabled a test" - left the
    string in place, so M3 stayed PASS with identical output while the
    suite quietly ran one test fewer. `assert ... or True`, `if False:`,
    and deleting the function while its docstring still quoted the line
    all survived too.

    That is a citation check dressed as a measurement, in the file whose
    premise is that prose about a measurement decays into a claim about
    one. The machinery to do it properly already existed three functions
    down, in M4.

    Treatment: add a dependency to a COPY of the manifest and the test
    must FAIL. Control: against the unmutated copy the same test must
    PASS, or the treatment proves nothing.
    """
    src = (REPO_ROOT / "pyproject.toml").read_text()
    if not tomllib.loads(src)["project"]["dependencies"]:
        return False, "no runtime dependencies declared at all - the probe read nothing"

    # THE NODE ID, not the file. Running the whole module passes for the
    # wrong reason: test_manifest.py holds five tests, so renaming the
    # closed-set one leaves four others, and one of THOSE also reddens
    # on an added dependency. The first version of this fix graded the
    # file and stayed green through the exact mutation it was written to
    # catch. A node id that does not exist makes pytest exit non-zero,
    # so a renamed or deleted test fails the CONTROL arm, which is where
    # it should be caught.
    node = (
        "tests/test_manifest.py::"
        "test_the_runtime_dependency_set_is_exactly_these_and_nothing_else"
    )

    def run_in(root: Path) -> subprocess.CompletedProcess[str]:
        return _pytest(root, node, "-p", "no:cacheprovider")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tests").mkdir()
        shutil.copy(REPO_ROOT / "uv.lock", root / "uv.lock")
        for name in ("conftest.py", "__init__.py", "test_manifest.py"):
            shutil.copy(REPO_ROOT / "tests" / name, root / "tests" / name)
        (root / "docs" / "research" / "fixtures").mkdir(parents=True)

        (root / "pyproject.toml").write_text(src)
        control = run_in(root)

        sentinel = '  "zzz-probe-not-a-real-package==0.0.0",\n'
        mutated = src.replace("dependencies = [\n", "dependencies = [\n" + sentinel, 1)
        if mutated == src:
            return False, "the mutation did not apply - the probe changed nothing"
        (root / "pyproject.toml").write_text(mutated)
        treatment = run_in(root)

    if control.returncode != 0:
        return False, (
            "control failed: the closed-set test is red, missing or no longer "
            "collected on an UNMUTATED copy. If it was renamed or deleted, "
            "collision 10's rule is enforced by nothing"
        )
    if treatment.returncode == 0:
        return False, (
            "adding a dependency did NOT turn test_manifest.py red - the closed-set "
            "assertion is gone, disabled, or no longer collected. Collision 10's rule "
            "is enforced by nothing"
        )
    return True, (
        "the manifest test PASSES unmutated and FAILS when a dependency is added - "
        "run, not grepped"
    )


def m4_collection_guard_survives_a_wholly_credentialed_file() -> tuple[bool, str]:
    """Collision 11: the guard collects THROUGH the marker selector.

    `_collected_test_files()` passes
    `-m "not credentialed and not network"`, so a file whose tests are
    ALL deselected is discovered and not collected, reads as an orphan,
    and turns the suite red. U5 is scheduled to add the first
    credentialed arm.

    Treatment: plant one wholly-credentialed and one wholly-network file
    - the guard must still PASS for this probe to be green. Control:
    without them the guard must pass, or the harness itself is broken
    and the treatment says nothing.
    """
    guard = REPO_ROOT / "tests" / "test_collection_guard.py"
    if not guard.exists():
        return False, "tests/test_collection_guard.py is missing entirely"

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tests").mkdir()
        shutil.copy(REPO_ROOT / "pyproject.toml", root / "pyproject.toml")
        for name in ("conftest.py", "__init__.py", "test_collection_guard.py"):
            shutil.copy(REPO_ROOT / "tests" / name, root / "tests" / name)
        (root / "docs" / "research" / "fixtures").mkdir(parents=True)

        control = _pytest(root, "tests/test_collection_guard.py")

        (root / "tests" / "test_all_credentialed.py").write_text(
            "import pytest\n\n\n@pytest.mark.credentialed\ndef test_x() -> None:\n"
            "    assert True\n"
        )
        (root / "tests" / "test_all_network.py").write_text(
            "import pytest\n\n\n@pytest.mark.network\ndef test_y() -> None:\n"
            "    assert True\n"
        )
        treatment = _pytest(root, "tests/test_collection_guard.py")

    if control.returncode != 0:
        return False, "control failed: the guard is red on a clean tree, probe vacuous"
    if treatment.returncode != 0:
        return False, (
            "a wholly-credentialed/network file reads as an ORPHAN and reds the suite "
            "- collision 11, and U5 is scheduled to create exactly this file"
        )
    return True, (
        "wholly-deselected files no longer trip the guard - collision 11 closed"
    )


PROBES = [
    ("M1 pytest_plugins in a non-rootdir conftest",
     m1_pytest_plugins_in_a_non_rootdir_conftest),
    ("M2 per-directory conftest cannot cross",
     m2_per_directory_conftest_does_not_cross_directories),
    ("M3 manifest closes the dependency set",
     m3_manifest_asserts_a_closed_dependency_set),
    ("M4 guard vs a wholly-deselected file",
     m4_collection_guard_survives_a_wholly_credentialed_file),
]

# Empty, and it should stay that way. M4 was the one entry: collision
# 11, a real defect in tests/test_collection_guard.py that this harness
# documented rather than tolerated. It was fixed by dropping `-m` from
# the guard's collection call, so M4 now PASSES and is no longer
# excused. An entry here means "known broken", never "expected to fail
# forever".
KNOWN_OPEN: set[str] = set()


def main() -> int:
    print(f"Re-running {len(PROBES)} plan measurements with {PYTHON}\n")
    unexpected = 0
    for label, probe in PROBES:
        ok, detail = probe()
        if ok:
            status = "PASS"
        elif label in KNOWN_OPEN:
            status = "OPEN"
        else:
            status = "STALE"
            unexpected += 1
        print(f"  [{status}] {label}\n         {detail}")

    print()
    if unexpected:
        print(
            f"{unexpected} plan claim(s) no longer reproduce. "
            "Fix the PLAN, not this script."
        )
        return 1
    print(
        "Every plan measurement reproduces. Known-open items are listed as OPEN above.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
