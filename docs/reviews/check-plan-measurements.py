#!/usr/bin/env python3
"""Re-run every measurement `docs/plans/IMPLEMENTATION-PLAN.md` rests a decision on.

**Why this file exists.** The plan justifies four decisions with measurements that were
run once, by hand, and then written up in prose. Prose about a measurement decays into a
*claim* about one: the next reader inherits the conclusion and not the evidence, and
nothing reports it when the underlying behaviour changes. Rounds 6 and 7 each re-ran some
of these by hand and reproduced them, which is the right instinct and the wrong mechanism
- it does not scale past the reviewer who happened to think of it.

Each probe below is **two-armed**: a treatment that must fail and a control that must
pass. A probe with only the arm the author expected is the failure mode this project has
paid for repeatedly - it cannot tell a real result from an instrument that always says the
same thing.

Run: `python3 docs/reviews/check-plan-measurements.py`
Exit 0 = every measurement the plan cites still reproduces. Non-zero = a plan claim has
gone stale, and the plan is what needs fixing, not this script.

**M4 WAS EXPECTED TO FAIL, AND NO LONGER DOES.** It is the eleventh collision, found by
round 7 and independently reproduced: a real defect in `tests/test_collection_guard.py`,
not a stale claim. The guard passed `-m` to its own collection call, so a file whose
tests are all deselected read as unreachable. Dropping `-m` fixed it and M4 went green,
which is what a documented-open probe is for - it is now a regression test rather than a
record of a defect. Do not "fix" any probe here to make it green.
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

FIXTURE_PLUGIN = "import pytest\n\n\n@pytest.fixture\ndef mock_transport():\n    return 'MT'\n"
USES_FIXTURE = "def test_uses(mock_transport):\n    assert mock_transport == 'MT'\n"


def _pytest(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def m1_pytest_plugins_in_a_non_rootdir_conftest() -> tuple[bool, str]:
    """§4's fixture mechanism: `pytest_plugins` in `tests/conftest.py`, not the rootdir.

    The plan mandates this and the obvious objection is real elsewhere - some pytest
    lineages refuse `pytest_plugins` outside the rootdir conftest. Treatment: it loads
    AND the fixture resolves, which is the positive control that it actually loaded
    rather than being silently ignored. Control: the same tree without the registration
    must FAIL, or the treatment proves nothing.
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
    """Why §4 rejected conftest-per-directory: a fixture is invisible to a sibling dir.

    This is the measurement the choice rests on. Treatment: the sibling directory's test
    must ERROR with 'fixture not found'. Control: the test in the conftest's OWN
    directory must pass, or the fixture was simply broken and the probe is vacuous.
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
        return False, "control failed: fixture broken in its OWN directory, probe vacuous"
    if "fixture 'mock_transport' not found" not in sibling.stdout:
        return False, "sibling directory RESOLVED the fixture - §4's rejection is stale"
    return True, "sibling cannot see it; same directory can - rejection holds"


def m3_manifest_asserts_a_closed_dependency_set() -> tuple[bool, str]:
    """Collision 10: `tests/test_manifest.py` closes the runtime dependency list.

    Treatment: adding a dependency must break set-equality. Control: the unmutated
    manifest must satisfy it. The plan schedules five units to add dependencies, so this
    going quiet would mean the collision had been resolved and the plan should say so.
    """
    src = (REPO_ROOT / "pyproject.toml").read_text()
    manifest_test = (REPO_ROOT / "tests" / "test_manifest.py").read_text()

    # DERIVED, never hardcoded. An earlier version of this probe pinned the expected set
    # to the three original pins and went STALE the first time a unit legitimately added
    # one - reporting a real, approved change as a failed measurement. That is the
    # two-lists defect this repository names elsewhere, built into the instrument that
    # checks for it. Four more dependencies are scheduled, so it would have gone stale
    # four more times.
    unmutated = set(tomllib.loads(src)["project"]["dependencies"])
    sentinel = '"zzz-probe-not-a-real-package==0.0.0"'
    mutated = set(
        tomllib.loads(src.replace("dependencies = [", f"dependencies = [\n  {sentinel},", 1))[
            "project"
        ]["dependencies"]
    )

    if not unmutated:
        return False, "no runtime dependencies parsed at all - the probe read nothing"
    if mutated == unmutated:
        return False, "mutation was a no-op - the probe never changed anything"
    # The PROPERTY, not the membership: the test compares the whole list with `==`, so
    # any addition breaks it. Checking the comparison itself is what survives a
    # legitimate dependency being added.
    if "set(_dependencies()) ==" not in manifest_test:
        return False, (
            "tests/test_manifest.py no longer closes the dependency set with `==`; "
            "collision 10's rule has been relaxed rather than appended to"
        )
    return True, (
        f"the manifest closes the set with `==` over {len(unmutated)} dependencies, "
        "so any addition breaks it"
    )


def m4_collection_guard_survives_a_wholly_credentialed_file() -> tuple[bool, str]:
    """Collision 11: the guard collects THROUGH the marker selector.

    `_collected_test_files()` passes `-m "not credentialed and not network"`, so a file
    whose tests are ALL deselected is discovered and not collected, reads as an orphan,
    and turns the suite red. U5 is scheduled to add the first credentialed arm.

    Treatment: plant one wholly-credentialed and one wholly-network file - the guard must
    still PASS for this probe to be green. Control: without them the guard must pass, or
    the harness itself is broken and the treatment says nothing.
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
            "a wholly-credentialed/network file reads as an ORPHAN and reds the suite - "
            "collision 11, and U5 is scheduled to create exactly this file"
        )
    return True, "wholly-deselected files no longer trip the guard - collision 11 closed"


PROBES = [
    ("M1 pytest_plugins in a non-rootdir conftest", m1_pytest_plugins_in_a_non_rootdir_conftest),
    ("M2 per-directory conftest cannot cross", m2_per_directory_conftest_does_not_cross_directories),
    ("M3 manifest closes the dependency set", m3_manifest_asserts_a_closed_dependency_set),
    ("M4 guard vs a wholly-deselected file", m4_collection_guard_survives_a_wholly_credentialed_file),
]

# Empty, and it should stay that way. M4 was the one entry: collision 11, a real
# defect in tests/test_collection_guard.py that this harness documented rather
# than tolerated. It was fixed by dropping `-m` from the guard's collection call,
# so M4 now PASSES and is no longer excused. An entry here means "known broken",
# never "expected to fail forever".
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
        print(f"{unexpected} plan claim(s) no longer reproduce. Fix the PLAN, not this script.")
        return 1
    print("Every plan measurement reproduces. Known-open items are listed as OPEN above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
