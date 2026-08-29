#!/usr/bin/env python3
# mypy: allow-untyped-defs, allow-untyped-calls
# ^ This file is a PROBE: its helpers build throwaway clients and
#   responders whose only caller is the arms below. mypy READS it -
#   that is the point of putting docs/reviews in `files` - and every
#   other strict check applies; only the two annotation knobs the ruff
#   per-file-ignores entry already relaxes for ANN are relaxed here, so
#   the two tools say the same thing about the same population.
"""The two S110 swallows in wired gates catch only what they name.

Ruff S110 (`try`/`except`/`pass`) fired twice inside code CI runs:

  check-standards-citations.py:79   `except Exception: pass` around a
      `git rev-parse` whose only job is to APPEND one more directory to
      the corpus search list.
  probe-r6-breaker-reset.py:88      `except Exception: pass` inside
      `drive_to`, which drives N outage failures on purpose.

Neither was a live defect - both had a correct fallback behind them.
Both were WIDER than the failure they named, which is how a gate
stops gating: a TypeError from a refactor of the guarded lines is
not "git is absent" and not "the upstream returned 500", but the old
catch could not tell the difference and reported a clean run either
way.

Each site gets three rows: the named failure still falls back (so
the narrowing did not break the gate), an UNNAMED failure now
escapes (so the narrowing did something), and the happy path is
untouched.

Run under the project environment - `probe-r6-breaker-reset.py`
imports httpx2:

    uv run --frozen python \
        docs/reviews/probe-gate-swallowed-exceptions.py

Exit 0 = every row behaved. Exit 1 = at least one did not.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from types import ModuleType

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
FAILURES: list[str] = []
RAN: list[str] = []

#: Every row below, counted. A run that ends early - the way the first
#: draft of this file did, on an imported module's SystemExit - must not
#: be able to exit 0 with rows unexecuted.
ROW_FLOOR = 7


def row(name: str, ok: bool, detail: str) -> None:
    """Print one row's verdict and record it."""
    print(f"########## {name} {'PASS' if ok else 'FAIL'}: {detail}")
    RAN.append(name)
    if not ok:
        FAILURES.append(name.split(".")[0])


def load(stem: str) -> ModuleType:
    """Import one docs/reviews script by path, under its own name.

    These scripts have no `if __name__ == "__main__"` guard - they
    run at import and end on `raise SystemExit(...)`. The first
    draft of this probe let that SystemExit propagate: the r6 probe
    ran, exited 0, and took this process with it BEFORE rows E-G had
    run. Every row printed up to that point had passed, so it read
    as a clean exit 0 while three rows had not executed at all - a
    skip wearing a green. Swallow the SystemExit; the module
    namespace is fully populated by then.
    """
    spec = importlib.util.spec_from_file_location(f"_probe_{stem}", HERE / f"{stem}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise
    return mod


# ---- site 1 ----------------------------------------------------
# check-standards-citations.py:_corpus(). It resolves the standards
# corpus; `candidates[0]` is the fallback and absence is still exit 2.
csc = load("check-standards-citations")
real_run = subprocess.run


def _raises(exc):
    def _run(*_a, **_kw):
        raise exc

    return _run


try:
    subprocess.run = _raises(FileNotFoundError(2, "No such file or directory: 'git'"))
    got = csc._corpus()  # noqa: SLF001
    row(
        "A. git ABSENT (OSError) still falls back, does not raise",
        isinstance(got, pathlib.Path) and got.name == "standards",
        f"_corpus() = {got}",
    )

    subprocess.run = _raises(subprocess.CalledProcessError(128, ["git"]))
    got = csc._corpus()  # noqa: SLF001
    row(
        "B. not a repo (CalledProcessError) still falls back, does not raise",
        isinstance(got, pathlib.Path) and got.name == "standards",
        f"_corpus() = {got}",
    )

    # C. The row the narrowing exists for. A TypeError is not "git is
    #    absent"; before the narrowing it was swallowed identically.
    subprocess.run = _raises(TypeError("run() got an unexpected keyword argument"))
    escaped: str | None = None
    try:
        csc._corpus()  # noqa: SLF001
    except TypeError as exc:
        escaped = str(exc)
    row(
        "C. an UNNAMED TypeError now ESCAPES instead of being swallowed",
        escaped is not None,
        f"escaped={escaped!r}",
    )
finally:
    subprocess.run = real_run

# D. Happy path, unpatched: the real resolution still returns a Path and
#    the WIRED gate still exits the way it did.
got = csc._corpus()  # noqa: SLF001
proc = subprocess.run(
    [sys.executable, str(HERE / "check-standards-citations.py")],
    cwd=REPO_ROOT,
    capture_output=True,
    text=True,
    check=False,
)
row(
    "D. happy path unchanged, and the wired gate still exits 0",
    isinstance(got, pathlib.Path) and proc.returncode == 0,
    f"_corpus()={got} gate_rc={proc.returncode}",
)

# ---- site 2 ----------------------------------------------------
# probe-r6-breaker-reset.py:drive_to(). The raise IS the expected
# result of each call, so swallowing is right - for outages only.
try:
    r6 = load("probe-r6-breaker-reset")
except ModuleNotFoundError as exc:
    row(
        "E. drive_to rows",
        False,
        f"could not import probe-r6-breaker-reset ({exc}); "
        "run this under `uv run --frozen python`",
    )
else:
    import asyncio

    class _FakeClient:
        def __init__(self, exc: BaseException | None) -> None:
            self.exc = exc
            self.calls = 0

        async def request(self, *_a, **_kw):
            self.calls += 1
            if self.exc is not None:
                raise self.exc

    outage = r6.JobviteUnavailableError("upstream is down")
    c = _FakeClient(outage)
    asyncio.run(r6.drive_to(c, 4))
    row(
        "E. an OUTAGE error is still swallowed, all 4 calls made",
        c.calls == 4,
        f"calls={c.calls}",
    )

    c = _FakeClient(TypeError("request() takes 2 positional arguments"))
    escaped = None
    try:
        asyncio.run(r6.drive_to(c, 4))
    except TypeError as exc:
        escaped = str(exc)
    row(
        "F. an UNNAMED TypeError now ESCAPES on the FIRST call, not silently",
        escaped is not None and c.calls == 1,
        f"calls={c.calls} escaped={escaped!r}",
    )

    c = _FakeClient(None)
    asyncio.run(r6.drive_to(c, 3))
    row(
        "G. NEGATIVE CONTROL: no exception at all is not an error either",
        c.calls == 3,
        f"calls={c.calls}",
    )

print()
print(f"  {len(RAN)}/{ROW_FLOOR} rows ran.")
if len(RAN) < ROW_FLOOR:
    print(f"  ONLY {len(RAN)} of {ROW_FLOOR} rows ran. A partial run is not a pass.")
    raise SystemExit(1)
if FAILURES:
    print(f"  {len(FAILURES)} row(s) did not behave: {FAILURES}")
    raise SystemExit(1)
print("  every row behaved. Both swallows now catch only what they name.")
raise SystemExit(0)
