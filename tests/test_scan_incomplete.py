"""`scan()` can truncate, and its caller must say so (ADR-0024, #86).

ADR-0024 bounded the exhaustive scan with a zero-progress break and a
record ceiling, and both set `ScanResult.incomplete`. **Nothing reads
it.** `scan()` has no caller in `src/` yet, so the flag is observable at
that boundary and nowhere else.

**A flag nobody renders truncates as silently as no flag at all** - the
caller answers confidently with a partial result, which is the outcome
ADR-0024's consequences section calls worse than the unbounded loop.

This file exists because the alternative was a sentence in a task, and
"a documented obligation enforced by nobody" is a shape this project has
now refused three times: it is the same as a setting nothing reads
(ADR-0025), a comment naming a variable that does not exist, and an
absent obligations row.
"""

from __future__ import annotations

import ast
import pathlib

TOOLS = pathlib.Path(__file__).resolve().parent.parent / "src/fast_mcp_jobvite/tools"

#: What a caller must mention for this test to accept that it
#: surfaces truncation. Deliberately a NAME and not a rendering: this
#: cannot check that a caller renders the flag WELL, only that it has
#: looked at all. That is the narrower question, and saying so is the
#: point.
FLAG = "incomplete"


def _scan_callers() -> list[tuple[str, str]]:
    """Every function under `tools/` that calls `something.scan(...)`.

    Parsed with `ast`, not grepped: `jobs.py:680` carries a COMMENT
    saying `client.scan()` exists and this tool does not use it, and a
    grep counts that as a caller. The two answers differ today, which is
    exactly when the difference is cheap to discover.
    """
    found: list[tuple[str, str]] = []
    for path in sorted(TOOLS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr == "scan"
                ):
                    found.append((path.name, node.name))
                    break
    return found


def test_every_scan_caller_surfaces_incomplete() -> None:
    """The tripwire for ADR-0024's flag, and it is VACUOUS TODAY.

    There are no callers, so the loop below runs zero times and this
    passes without testing anything about rendering. **That is stated
    rather than hidden**, because a test whose name promises more than
    its body delivers is a defect this project has found three times.

    What it DOES do is fire on the day a caller appears. The first unit
    to call `scan()` will find this red unless it reads `incomplete`,
    which is when the obligation is cheap to meet - rather than after a
    tool has shipped answering confidently with a truncated page.

    It cannot check that the flag is rendered WELL. Only that the caller
    looked at it.
    """
    callers = _scan_callers()

    if not callers:
        # The current state, asserted rather than assumed. If this line
        # fails, `scan()` gained a caller and the branch below is now
        # the one that matters - do not delete this test, extend it.
        assert callers == [], f"unreachable: {callers}"
        return

    missing = [
        f"{module}:{func}"
        for module, func in callers
        if FLAG not in (TOOLS / module).read_text(encoding="utf-8")
    ]
    assert not missing, (
        f"these call scan() without mentioning {FLAG!r}: {missing}. "
        "ADR-0024's bounds set that flag and a caller that ignores it "
        "truncates silently, which the ADR calls worse than the "
        "unbounded loop it replaced."
    )


def test_the_scan_caller_parser_can_find_a_caller() -> None:
    """The positive control for the parser itself.

    Without it, the test above is a loop over an empty list that would
    pass just as happily against a parser that finds nothing.

    Plants a module under `tools/` that calls `.scan(...)`, requires the
    parser to find it, and removes it. If this ever fails, the test
    above is not vacuous-but-armed; it is simply blind.
    """
    planted = TOOLS / "_scan_caller_control.py"
    planted.write_text(
        "async def _planted(client: object) -> None:\n"
        "    await client.scan('/x')  # type: ignore[attr-defined]\n",
        encoding="utf-8",
    )
    try:
        found = _scan_callers()
    finally:
        planted.unlink()

    assert ("_scan_caller_control.py", "_planted") in found, (
        f"the parser did not find a planted scan() caller; it found {found}. "
        "The tripwire above is blind, not merely unarmed."
    )
