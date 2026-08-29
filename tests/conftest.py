"""Shared test paths.

**How tests reach the fixtures, settled here rather than invented
later** (PLAN-REVIEW-R2.md:315-323, finding L1). The fifteen fixtures
live in `docs/research/fixtures/` and tests read them **from there, by
path**. They are NOT copied under `tests/`, because U4 asserts five of
them byte-exact against real recorded Jobvite transport, and a second
copy of a byte-exact ground truth can drift from the first silently.

A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite (DESIGN.md:1319-1321).
"""

from __future__ import annotations

import pathlib
from collections.abc import Iterator

import pytest

from fast_mcp_jobvite.services import jobvite_client

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "docs" / "research" / "fixtures"
PYPROJECT = REPO_ROOT / "pyproject.toml"
UV_LOCK = REPO_ROOT / "uv.lock"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
GITIGNORE = REPO_ROOT / ".gitignore"


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> pathlib.Path:
    return FIXTURES_DIR


# ======================================================================
# U7's TWO SUITE-WIDE FIXTURES, and both are here rather than in
# `tests/test_resilience.py` because U7 added module state and a real
# sleep to a client that EVERY other suite drives.
#
# EACH ONE HAS ITS OWN MEASUREMENT, taken by disabling that fixture
# alone and reading the result:
#
#   * `_closed_breaker`. Disabled, the FULL suite reports **19 failed,
#     458 passed** - every one of them in `tests/test_tools_jobs.py`,
#     which collects after `tests/test_resilience.py` and inherits the
#     breaker that file deliberately trips. The breaker being module
#     state is CORRECT in production: it records what the DEPENDENCY
#     has been doing and must survive a client being rebuilt, which is
#     once per invocation in the shapes `tools/` uses. So the fix
#     belongs in the suite rather than in the design.
#   * `_no_backoff_sleeps`. Disabled, `tests/test_jobvite_client.py`
#     alone goes from **13.79s to 31.68s**, still 42 passed. U4's
#     transport cases retry now, and they sleep while doing it.
#
# **THE FIRST DIAGNOSIS OF THIS WAS WRONG AND THE CORRECTION IS THE
# POINT.** It was read off a run that ALSO reported 2 failures in
# `test_jobvite_client.py`, attributed to the breaker, and written up
# as such. Those failures were an instrument fault: a U4 mutation
# harness was running in the background against this same working
# tree, so the suite was being run against a mutated `src/`. Re-run on
# a tree proved clean with `grep`, the file passes 42/42 with the
# breaker fixture off. Only the timing half of that run was real.
# ======================================================================


@pytest.fixture(autouse=True)
def _closed_breaker() -> Iterator[None]:
    """Give every test in the whole suite a closed breaker.

    Reset on the way OUT as well as in, so a case that trips it cannot
    leak into the next file either.

    Yields:
        Nothing; this is a setup/teardown fixture.
    """
    jobvite_client.reset_breaker_for_test()
    yield
    jobvite_client.reset_breaker_for_test()


@pytest.fixture(autouse=True)
def _no_backoff_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the jittered retry backoff zero for the whole suite.

    **This patches the WAIT, not the retry decision.** Every case still
    runs the real `AsyncRetrying`, the real predicate and the real
    attempt count; what is removed is only wall-clock delay.
    `test_the_backoff_is_exponential_with_jitter` is the case that
    covers what this hides, and it reads the unpatched object rather
    than driving a call - so zeroing the wait here does not leave the
    jitter requirement untested.

    Args:
        monkeypatch: pytest's patcher.
    """
    monkeypatch.setattr(jobvite_client, "_JITTERED_BACKOFF", lambda _state: 0.0)
