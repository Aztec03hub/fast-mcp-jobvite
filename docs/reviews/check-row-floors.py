#!/usr/bin/env python3
"""Every controls harness must declare a ROW FLOOR.

    python3 docs/reviews/check-row-floors.py

**The defect this exists for, measured.** `FIRED -ne TOTAL` is satisfied
by `0 == 0`, so a harness whose rows were all deleted reports fully
green. R4-M4 recorded that and the floor was added to the harnesses
someone was looking at.

R7-H2 then found `check-u9-http-controls.sh` still had none, and framed
it as three of four siblings fixed and one missed. **That framing is
itself the defect.** R7 enumerated the four units in its own brief.
Enumerating the CONTAINER - every `scripts/check-*-controls.sh` - finds
NINE of fourteen without a floor, not one of four.

That is the shape this project has now measured seven times: a hand-kept
list beside its container is blind to the member nobody added. A review
scoped to four units is such a list, and so is any future fix that walks
the harnesses somebody remembers.

**So this checker does not carry a list of harnesses.** It globs the
directory and requires each one it finds to declare `ROW_FLOOR=<n>`. The
tenth harness written next month is covered on the day it lands, by
existing, which is the only property that survives nobody remembering.

**What it deliberately does NOT check: whether the floor is RIGHT.** A
floor is only honest if it was DERIVED from a run of that harness rather
than typed, and no static reader can tell those apart - branch-local
floors have been wrong on this project four times. This answers the
narrower question completely and says so, which is the difference
between a gate and a green that means something else.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HARNESSES = "scripts/check-*-controls.sh"

#: `ROW_FLOOR=25`, and it must be a literal integer. A floor computed at
#: run time from the rows the harness just counted is not a floor: it
#: equals TOTAL by construction and passes with every row deleted.
FLOOR = re.compile(r"^\s*ROW_FLOOR=(\d+)\s*$", re.M)

#: The floor has to be READ as well as declared. A harness that sets
#: ROW_FLOOR and never compares it is the inoperative-code shape, and it
#: would satisfy a checker that only looked for the assignment.
USES = re.compile(r'\$\{?ROW_FLOOR\}?')


def main() -> int:
    found = sorted(ROOT.glob(HARNESSES))
    if not found:
        print(f"MATCHED ZERO HARNESSES at {HARNESSES!r}.")
        print("A search at a path that does not exist returns a clean")
        print("empty, which is indistinguishable from real absence.")
        return 2

    missing: list[str] = []
    inert: list[str] = []
    ok: list[tuple[str, int]] = []

    for path in found:
        name = path.name
        text = path.read_text(encoding="utf-8", errors="replace")
        match = FLOOR.search(text)
        if match is None:
            missing.append(name)
            continue
        # Uses BEYOND the assignment line itself.
        if len(USES.findall(text)) < 1:
            inert.append(name)
            continue
        ok.append((name, int(match.group(1))))

    print(f"Controls harnesses found: {len(found)}\n")
    for name, floor in ok:
        print(f"  ok       {name:<44} ROW_FLOOR={floor}")
    for name in inert:
        print(f"  INERT    {name:<44} declared but never compared")
    for name in missing:
        print(f"  MISSING  {name:<44} no ROW_FLOOR")

    bad = len(missing) + len(inert)
    print(f"\n{len(ok)}/{len(found)} declare and read a row floor.")
    if bad:
        print(
            f"\n{bad} harness(es) can report fully green with every row\n"
            "deleted, because `FIRED -ne TOTAL` is satisfied by 0 == 0.\n"
            "A floor must be DERIVED from a run of that harness. Do not\n"
            "type one in to clear this check: a wrong floor passes here\n"
            "and buys nothing."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
