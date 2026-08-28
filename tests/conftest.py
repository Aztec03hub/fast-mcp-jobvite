"""Shared test paths.

**How tests reach the fixtures, settled here rather than invented later**
(PLAN-REVIEW-R2.md:315-323, finding L1). The fifteen fixtures live in
`docs/research/fixtures/` and tests read them **from there, by path**. They are
NOT copied under `tests/`, because U4 asserts five of them byte-exact against
real recorded Jobvite transport, and a second copy of a byte-exact ground truth
can drift from the first silently.

A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite (DESIGN.md:1214-1216).
"""

from __future__ import annotations

import pathlib

import pytest

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
