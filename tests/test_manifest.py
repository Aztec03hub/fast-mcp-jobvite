"""DESIGN.md §8 case #11 - the manifest pins `mcp` and the frozen resolve has no lock drift.

Three arms, and the third is the one that earns the case its keep:

1. `mcp` is present in `[project].dependencies` with an `==` pin. DESIGN.md:1352-1356
   pins it explicitly rather than relying on `fastmcp` to hold it, because the
   `ResponseLimiting` regression arrived through the transitive SDK with zero change
   to the code that broke.
2. `uv lock --check` exits 0 without amending `uv.lock` - the same lock CI installs
   with `uv sync --frozen`. Asserted by hashing the file either side, because a
   command that rewrites the lock and then reports agreement has proven nothing.
3. **The negative arm.** A manifest with the `fastmcp-slim` line removed FAILS to
   resolve. That comment - "transitive prerelease; must be named or resolution
   fails" - is the only justification the line carries, and a pin whose only
   justification is a comment is one refactor from deletion. This arm is what stops
   a future tidy-up dropping an apparently redundant transitive
   (IMPLEMENTATION-PLAN.md:266-276).
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import shutil
import subprocess
import tomllib

import pytest

from .conftest import PYPROJECT, UV_LOCK


def _dependencies() -> list[str]:
    with PYPROJECT.open("rb") as fh:
        deps = tomllib.load(fh)["project"]["dependencies"]
    assert isinstance(deps, list)
    return [str(d) for d in deps]


def test_mcp_is_pinned_with_a_double_equals() -> None:
    deps = _dependencies()
    mcp = [d for d in deps if re.match(r"^mcp\b", d)]
    assert mcp == ["mcp==2.1.1"], f"expected an == pin on mcp, dependencies are {deps}"


def test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version() -> None:
    """The three-pin block of DESIGN.md:1358-1362, checked as a set not as prose."""
    assert set(_dependencies()) == {
        "fastmcp==4.0.0b4",
        "fastmcp-slim==4.0.0b4",
        "mcp==2.1.1",
    }


def test_prerelease_is_explicit() -> None:
    """`--prerelease=allow` is global in uv and pulls in a beta pydantic (DESIGN.md:1381-1383)."""
    with PYPROJECT.open("rb") as fh:
        assert tomllib.load(fh)["tool"]["uv"]["prerelease"] == "explicit"


def test_the_fastmcp_slim_justification_comment_survives() -> None:
    """The comment IS the specification here; arm 3 below is what makes it true."""
    text = PYPROJECT.read_text()
    assert "must be named or resolution fails" in text


def test_uv_lock_check_passes_without_amending_the_lockfile() -> None:
    before = hashlib.sha256(UV_LOCK.read_bytes()).hexdigest()
    proc = subprocess.run(
        ["uv", "lock", "--check"],
        cwd=PYPROJECT.parent,
        capture_output=True,
        text=True,
    )
    after = hashlib.sha256(UV_LOCK.read_bytes()).hexdigest()
    assert proc.returncode == 0, f"uv lock --check failed:\n{proc.stdout}\n{proc.stderr}"
    assert before == after, "uv lock --check rewrote uv.lock; its agreement proves nothing"


@pytest.mark.network
def test_removing_fastmcp_slim_breaks_the_resolve(tmp_path: pathlib.Path) -> None:
    """The control proving the fastmcp-slim pin is load-bearing rather than decorative.

    Marked `network` and deselected from the default offline suite: it performs a
    real resolve. CI runs it as its own step. It is excluded by SELECTION, never
    by skipif - a skip is a green that tested nothing (DESIGN.md:1185-1188).
    """
    manifest = PYPROJECT.read_text()
    mutated = "\n".join(line for line in manifest.splitlines() if "fastmcp-slim" not in line)
    assert mutated != manifest, "mutation was a no-op; this control would be vacuous"

    (tmp_path / "src" / "fast_mcp_jobvite").mkdir(parents=True)
    (tmp_path / "src" / "fast_mcp_jobvite" / "__init__.py").touch()
    (tmp_path / "pyproject.toml").write_text(mutated)

    proc = subprocess.run(["uv", "lock"], cwd=tmp_path, capture_output=True, text=True)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        "removing the fastmcp-slim pin STILL resolved. Either uv's behaviour changed "
        "or the pin is no longer load-bearing; DESIGN.md:1358-1360 needs an ADR "
        f"before the line is touched. Output:\n{combined}"
    )
    assert "fastmcp-slim" in combined, f"failed, but not for the stated reason:\n{combined}"


@pytest.mark.network
def test_the_unmutated_manifest_still_resolves(tmp_path: pathlib.Path) -> None:
    """Positive control for the arm above.

    A refusal-path test is not a guard unless the happy path still succeeds
    (DESIGN.md:1319-1321). Without this, a `uv` that failed on EVERYTHING - a
    broken binary, no network, a bad cache - would make the control above pass.
    """
    (tmp_path / "src" / "fast_mcp_jobvite").mkdir(parents=True)
    (tmp_path / "src" / "fast_mcp_jobvite" / "__init__.py").touch()
    shutil.copy(PYPROJECT, tmp_path / "pyproject.toml")

    proc = subprocess.run(["uv", "lock"], cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"the real manifest failed to resolve:\n{proc.stdout}\n{proc.stderr}"
    )
