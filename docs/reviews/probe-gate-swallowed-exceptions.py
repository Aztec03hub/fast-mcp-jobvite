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
import re
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


def verdict(ran: int, floor: int, failures: list[str]) -> tuple[list[str], int]:
    """The lines and the exit code, in ONE place.

    Split out of the tail of this file so `--self-test` arms THE SAME
    rules rather than a copy of them. A self-check that re-implements
    the comparison it is checking passes for as long as the two copies
    agree, which is until one of them is edited.

    **EQUALITY, NOT A LOWER BOUND (#223).** `len(RAN) < ROW_FLOOR` was
    blind in the ADD direction: a row added without raising the floor
    left it slack, and a slack floor says nothing when rows go later.
    `check-row-floor-exactness.py` does statically count this file's
    labelled `row(` sites and would report the slack, so this is the
    harness failing on its own evidence rather than a hole nothing
    else could see.

    **NEITHER HALF CAN SEE THE OTHER'S CASE, so both are asserted.**
    Delete a row and `ran` falls below `floor` while `failures` stays
    EMPTY - a reader watching the failure list sees a clean run. Break
    a row and `failures` fills while `ran == floor` is satisfied - a
    reader watching the count sees a full one. The first is what this
    floor exists for; the second is what `probe-docs-lint-amputation.py`
    already watches, by amputating the two guarded call sites and
    asserting WHICH rows die.
    """
    lines = [f"  {ran}/{floor} rows ran."]
    if ran < floor:
        lines.append(f"  ONLY {ran} of {floor} rows ran. A partial run is not a pass.")
        return (lines, 1)
    if ran > floor:
        lines.append(
            f"  {ran} rows ran against a floor of {floor}. Rows were ADDED "
            f"and the floor was not raised: it is slack by {ran - floor}, "
            f"so that many can be deleted unnoticed. Raise it to {ran}."
        )
        return (lines, 1)
    if failures:
        lines.append(f"  {len(failures)} row(s) did not behave: {failures}")
        return (lines, 1)
    lines.append("  every row behaved. Both swallows now catch only what they name.")
    return (lines, 0)


#: THE ARM SET, NAMED. This is a floor by another mechanism, and the
#: mechanism is deliberate: a second `*_floor = <int>` in this file is
#: a HARD FAILURE of `check-row-floor-exactness.py` for a mode=static
#: row - "2 floor assignments (ROW_FLOOR, arm_floor) and nothing says
#: which one the table's row count is about", exit 1, MEASURED under
#: #223 by planting one. The two-floor permission #194 added is for
#: COMPUTED rows only, and this row's count is static.
#:
#: A name list buys what an integer floor buys - defeating it takes a
#: TWO-PLACE edit, delete the arm AND delete its name - while carrying
#: no integer for the container to be ambiguous about. #194's own S9
#: arm is the same device.
SELF_TEST_ARMS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")


def self_test() -> int:
    """Arm `verdict()` in memory. Runs no rows and mutates nothing."""
    seen: list[str] = []
    bad: list[str] = []

    def check(label: str, ok: bool, meaning: str) -> None:
        seen.append(label)
        print(f"{'PASS' if ok else 'FAIL'}  {label}  {meaning}")
        if not ok:
            bad.append(label)

    full = verdict(ROW_FLOOR, ROW_FLOOR, [])
    check("S1", full[1] == 0, "a full row set with no failures is exit 0")

    lost = verdict(ROW_FLOOR - 1, ROW_FLOOR, [])
    check("S2", lost[1] == 1, "DELETE one row and the floor BREACHES: exit 1")
    check(
        "S3",
        any("ONLY" in line for line in lost[0]),
        "the breach SAYS a row was lost rather than exiting quietly",
    )
    check(
        "S4",
        verdict(ROW_FLOOR + 1, ROW_FLOOR, [])[1] == 1,
        "an ADDED row against an unraised floor also breaches",
    )
    check(
        "S5",
        verdict(ROW_FLOOR, ROW_FLOOR, ["C"])[1] == 1,
        "THE OTHER DIRECTION: the floor is SATISFIED and only the "
        "failure list catches a row that ran and misbehaved",
    )
    check(
        "S6",
        verdict(0, ROW_FLOOR, [])[1] == 1,
        "a run that executed NO rows is a breach, not a green",
    )
    own = pathlib.Path(__file__).read_text(encoding="utf-8")
    check(
        "S7",
        len(re.findall(r"(?m)^ROW_FLOOR = \d+$", own)) == 1,
        "ROW_FLOOR is exactly ONE literal assignment the container "
        "can see - two would be a hard failure for a static row",
    )
    check(
        "S8",
        tuple(seen) + ("S8",) == SELF_TEST_ARMS and len(set(seen)) == len(seen),
        "SELF_TEST_ARMS names exactly these arms, in order, with no "
        "duplicate label - deleting an arm takes a two-place edit",
    )

    print(f"  {len(seen)}/{len(SELF_TEST_ARMS)} self-test arms ran.")
    if bad:
        print(f"  {len(bad)} arm(s) did not behave: {bad}")
        return 1
    return 0


if "--self-test" in sys.argv:
    raise SystemExit(self_test())


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
# rc 2 is the gate's SANCTIONED "corpus absent" state, not a failure -
# `ci.yml` turns it into a warning by design, because the standards
# corpus is a private repo needing STANDARDS_TOKEN (#106). Asserting
# rc == 0 encoded a LOCAL-ONLY precondition: this row passed on a
# machine that has the corpus checked out beside the repo, and failed
# on every runner that does not. It went red the first time CI ran it,
# and its failure then contaminated the A3/A4 amputation rows, which
# compare which rows die.
#
# What this row actually wants is "the wired gate did not CRASH".
# rc 1 would be a real finding and still fails here.
row(
    "D. happy path unchanged, and the wired gate did not crash",
    isinstance(got, pathlib.Path) and proc.returncode in (0, 2),
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
REPORT, CODE = verdict(len(RAN), ROW_FLOOR, FAILURES)
for report_line in REPORT:
    print(report_line)
raise SystemExit(CODE)
