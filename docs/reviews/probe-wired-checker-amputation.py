#!/usr/bin/env python3
"""Amputate each construct in `check-checkers-are-wired.py`.

**THE FOUR ARMS THIS EXISTS FOR ALL SURVIVED, AND THEY SURVIVED AS
A MARKDOWN TABLE.** R14 measured them by hand, wrote the counts into
a review, and a review is a claim about a measurement rather than the
measurement. The next person to touch `_script_of` would have got no
signal at all. So the arms are a program now.

Read WHICH rows die, never the exit code alone. An arm that kills two
rows for the wrong reason and an arm that kills the right two are the
same integer.

Arm B is INVERSE on purpose. The `--` branch was deleted as
inoperative (R14 L-3), so there is nothing left to amputate; the arm
puts it BACK and asserts nothing changes. A deletion undetectable in
either direction is the proof the branch was dead, and this keeps a
live check on that ruling instead of a sentence about it.

NOT WIRED, deliberately: turning this into a `scripts/check-*.sh`
harness under `ci-harness-gate.sh`, with the canonical
`HARNESS-RESULT` line, is task #149. This is the measurement; the
gate is a separate decision, and a half-formed canonical line would
be worse than none.

Run with `uv run --frozen python` on
`docs/reviews/probe-wired-checker-amputation.py` - CI's interpreter,
not a bare one, which is the defect the subject file exists about.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "docs" / "reviews" / "check-checkers-are-wired.py"

#: The `--` branch as it stood before deletion, and the generic break
#: that already reached the same token. Arm B splices the first back
#: in ahead of the second.
BREAK = '            if not opt.startswith("-") or opt == "-":\n'
BRANCH = '            if opt == "--":\n                j += 1\n                break\n'

#: Every arm's expectation, ASSERTED. A survivor fails this probe; it
#: is not a number somebody has to notice in the output.
EXPECTED = {
    "BASELINE": 0,
    "A _OPT_NO_SCRIPT emptied": 2,
    "B -- branch REINSTATED (inverse)": 0,
    "C _CHECKER_NAME = .*": 1,
    "D _OPT_WITH_VALUE = {-X}": 2,
    "E _MODULE_RUNNERS emptied": 2,
    "F _runner_script always None": 2,
    "G _INTERPRETER loses version suffix": 1,
}


def load() -> types.ModuleType:
    """A FRESH module per arm; one mutated would poison the next."""
    spec = importlib.util.spec_from_file_location(f"wired_{len(sys.modules)}", SRC)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {SRC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reinstate_dashdash(module: types.ModuleType) -> None:
    """Put the deleted `--` branch back, rewriting the real source."""
    src = SRC.read_text(encoding="utf-8")
    count = src.count(BREAK)
    if count != 1:
        raise SystemExit(
            f"anchor occurs {count} times, expected 1. Arm B would "
            "amputate NOTHING and pass for that reason."
        )
    namespace: dict[str, object] = {
        "__file__": str(SRC),
        "__name__": "wired_dashdash",
    }
    patched = src.replace(BREAK, BRANCH + BREAK)
    exec(compile(patched, str(SRC), "exec"), namespace)  # noqa: S102
    module.__dict__.update(namespace)


def _no_script(module: types.ModuleType) -> None:
    module._OPT_NO_SCRIPT = ()  # type: ignore[attr-defined]


def _any_name(module: types.ModuleType) -> None:
    module._CHECKER_NAME = re.compile(r".*")  # type: ignore[attr-defined]


def _one_opt(module: types.ModuleType) -> None:
    module._OPT_WITH_VALUE = frozenset({"-X"})  # type: ignore[attr-defined]


def _no_runners(module: types.ModuleType) -> None:
    module._MODULE_RUNNERS = frozenset()  # type: ignore[attr-defined]


def _runner_blind(module: types.ModuleType) -> None:
    module._runner_script = lambda _: None  # type: ignore[attr-defined]


def _no_version(module: types.ModuleType) -> None:
    module._INTERPRETER = re.compile(r"^python3?$")  # type: ignore[attr-defined]


ARMS: list[tuple[str, object]] = [
    ("BASELINE", None),
    ("A _OPT_NO_SCRIPT emptied", _no_script),
    ("B -- branch REINSTATED (inverse)", reinstate_dashdash),
    ("C _CHECKER_NAME = .*", _any_name),
    ("D _OPT_WITH_VALUE = {-X}", _one_opt),
    ("E _MODULE_RUNNERS emptied", _no_runners),
    ("F _runner_script always None", _runner_blind),
    ("G _INTERPRETER loses version suffix", _no_version),
]


def main() -> int:
    """Run every arm, print the rows it killed, hold it to EXPECTED."""
    failures: list[str] = []
    for label, mutate in ARMS:
        module = load()
        if mutate is not None:
            mutate(module)  # type: ignore[operator]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            module.self_test()
        killed = [
            line.strip()
            for line in buffer.getvalue().splitlines()
            if "CONTROL FAILED" in line
        ]
        print(f"\n{label}: {len(killed)} row(s) killed")
        for line in killed:
            print(f"    {line}")
        want = EXPECTED[label]
        if len(killed) != want:
            failures.append(f"{label}: killed {len(killed)}, expected {want}")

    rows = len(ARMS)
    print(f"\narms={rows} failures={len(failures)}")
    for line in failures:
        print(f"  {line}")
    if failures:
        print("\nAn arm moved. Either a control was lost or a construct")
        print("is now dead code. Read WHICH rows changed before")
        print("touching either file.")
        return 1
    print(f"{rows}/{rows} arms measured as expected. No survivor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
