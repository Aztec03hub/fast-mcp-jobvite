"""Every `test_*.py` in this repository is reachable from the configured `testpaths`.

`backend/testing.md:138-141` makes this a required meta-test, and
`devops/quality-gates.md:76-81` (API-03) makes its *absence* a CI failure in its own
right: "A collection-guard meta-test ... MUST be present in a configured root and MUST
pass in CI."

**This guard lives inside `tests/`, which is the single configured root, deliberately.**
The standard requires that placement so the guard's own disappearance fails collection
rather than passing silently. A guard outside `testpaths` cannot report its own absence.

Why this repository needs the *thorough* variant rather than the minimal one
(`backend/testing.md:162-165`): the minimal form asserts only that
`pytest --collect-only` exits 0, and collection exits 0 perfectly happily while a test
file sits outside `testpaths` and is never collected at all. That is precisely the
defect API-03 names, so the minimal form does not detect it.

The stakes here are higher than in a normal project, because **this suite's entire
strategy is selection-based**: the default run is
`-m "not credentialed and not network"`, plus a `tests/credentialed/` subtree, and CI
enforces zero skips. Under that design a file outside
`testpaths`, or a single marker typo, yields **a green over fewer tests than anyone
believes** — and green is currently this repository's only evidence.

**A sentence here used to say the credentialed subtree is "collected but never
run", and that was false.** It was never tested, because the subtree held only a
README, so no file existed that could contradict it. Under the default selector such a
file is NOT collected - and the guard, which passed that same selector, called it an
orphan. That is collision 11, fixed in `_collected_test_files` and pinned by
`test_a_wholly_credentialed_file_is_not_reported_as_an_orphan` below.

Tracked as **B58** in the project's conformance corpus, where it was recorded as a
required-check breach and then reached neither the design, the plan, nor the tree until
now.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories that legitimately contain no collectable tests and must not be walked.
# `.venv` holds third-party test suites; the rest are not source.
_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
}


def _discovered_test_files() -> set[Path]:
    """Every `test_*.py` in the working tree, by walking the filesystem."""
    found: set[Path] = set()
    for path in REPO_ROOT.rglob("test_*.py"):
        if any(part in _SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        found.add(path.resolve())
    return found


def _collected_test_files() -> set[Path]:
    """Every file pytest actually collects, parsed from `--collect-only -q`."""
    # `-p no:cacheprovider` keeps this from writing to .pytest_cache mid-run.
    # `-o addopts=` is LOAD-BEARING: pyproject's addopts carries `-v`, which overrides
    # `-q` and turns the output into a tree of `<Function ...>` nodes with no paths.
    # Parsing that tree looked like six orphaned files on the first run - the parser was
    # broken, not the tree. Clearing addopts pins the machine-readable node-id format
    # regardless of what someone later adds to it.
    #
    # NO `-m` SELECTOR HERE, and its absence is the fix for collision 11.
    #
    # This call used to pass `-m "not credentialed and not network"`, mirroring the
    # default run. That made the guard ask "is this file SELECTED?" when the property
    # it exists to check is "is this file REACHABLE?" - and the two differ for exactly
    # one shape of file: one whose tests are ALL credentialed or all network. Such a
    # file is discovered by the walk, produces no node ids under the selector, and was
    # reported as an orphan "not reachable from testpaths" while sitting inside
    # `tests/`. The message was false and the suite went red.
    #
    # It survived seven review rounds because `tests/credentialed/` held only a
    # README, so no file of that shape had ever existed. U5 is scheduled to create the
    # first one. The module docstring below asserted the opposite behaviour - that the
    # credentialed subtree "appears in --collect-only output" - which was true only
    # because nothing was there to appear.
    #
    # Marker selection is irrelevant to reachability, so the selector was never right
    # here, not merely inconvenient.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "--tb=no",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    collected: set[Path] = set()
    for line in result.stdout.splitlines():
        # With addopts cleared, `-q` reports node ids as `path/to/test_x.py::test_name`.
        if "::" not in line:
            continue
        candidate = REPO_ROOT / line.split("::", 1)[0].strip()
        if candidate.suffix == ".py":
            collected.add(candidate.resolve())
    return collected


def test_collection_succeeds() -> None:
    """The minimal form from the standard, kept as the floor.

    This is necessary and NOT sufficient - see the module docstring. It catches a broken
    conftest or an import error; it does not catch a file nobody collects.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        "pytest collection failed - check testpaths covers all test roots.\n"
        + result.stdout
        + result.stderr
    )


def test_the_guard_can_see_anything_at_all() -> None:
    """Positive control on this module's own instrument.

    Both assertions below compare two sets. If the walker matched nothing, or the
    collection parser matched nothing, the comparison passes vacuously and this file
    becomes a green that checks nothing - the exact failure it exists to prevent, one
    level up. So both sides must be non-empty before either is trusted.
    """
    discovered = _discovered_test_files()
    collected = _collected_test_files()
    assert discovered, (
        "the filesystem walk found no test_*.py at all - the walker is broken"
    )
    assert collected, (
        "parsed no collected files from --collect-only - the parser is broken"
    )
    assert __file__ and Path(__file__).resolve() in discovered, (
        "the walker missed this very file, so it cannot be trusted about any other"
    )


def test_every_test_file_is_reachable_from_testpaths() -> None:
    """The thorough variant: nothing on disk is invisible to collection.

    A file here means a test that exists, is never run, and whose absence from the
    results nobody notices - because the suite is green either way.
    """
    discovered = _discovered_test_files()
    collected = _collected_test_files()
    # Collection runs WITHOUT the marker selector (see `_collected_test_files`), so
    # every file inside `testpaths` appears here regardless of how its tests are
    # marked - including a wholly-credentialed one. Anything discovered and NOT
    # collected is genuinely unreachable, which is the defect.
    orphans = sorted(
        p.relative_to(REPO_ROOT).as_posix() for p in discovered - collected
    )
    assert not orphans, (
        "test files exist but are not reachable from `testpaths`, so they never run "
        "and the suite is green without them:\n  " + "\n  ".join(orphans)
    )


def test_a_wholly_credentialed_file_is_not_reported_as_an_orphan() -> None:
    """Collision 11, pinned so it cannot come back.

    A file whose tests are ALL `credentialed` is inside `testpaths` and perfectly
    reachable, but produces no node ids under the default run's `-m` selector. The
    guard used to pass that selector, so such a file was reported as "not reachable
    from `testpaths`" and turned the suite red on a correct change.

    **It survived seven review rounds because no file of this shape existed** -
    `tests/credentialed/` held only a README, so the case was unreachable by
    inspection and invisible to every green run. U5 is scheduled to create the first
    one. This test creates it on demand instead of waiting for U5.

    The file is written inside the repository rather than into a `tmp_path`, because
    the guard walks `REPO_ROOT` and a file outside it would not exercise the walk at
    all - it would pass vacuously, which is the failure this whole module exists to
    prevent one level up.

    It goes in `tests/` and NOT `tests/credentialed/`, which is where U5's real file
    will live. First attempt wrote it to `tests/credentialed/` and raised
    `FileNotFoundError` wherever that directory does not exist - including the scratch
    copy that `docs/reviews/check-plan-measurements.py` builds, whose control arm went
    red and reported the probe vacuous. **That is the same assumed-path defect this
    commit fixes elsewhere, reintroduced inside the regression test for it.** `tests/`
    is `testpaths`, so it always exists, and the property under test does not depend on
    the subdirectory.
    """
    probe = REPO_ROOT / "tests" / "test_collision_11_probe.py"
    probe.write_text(
        '"""Written by the guard\'s own regression test. Removed in its finally."""\n'
        "\nimport pytest\n\n\n@pytest.mark.credentialed\n"
        "def test_needs_a_live_tenant() -> None:\n    assert True\n"
    )
    try:
        discovered = _discovered_test_files()
        collected = _collected_test_files()
        assert probe.resolve() in discovered, (
            "the walk did not find the probe file, so this test proves nothing "
            "about the comparison below"
        )
        assert probe.resolve() in collected, (
            "a wholly-credentialed file inside `testpaths` was not collected. The "
            "guard is selecting rather than checking reachability - collision 11 has "
            "regressed, and U5's test file will red the suite."
        )
    finally:
        probe.unlink(missing_ok=True)
