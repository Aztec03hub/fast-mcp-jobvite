#!/usr/bin/env python3
"""A row floor must EQUAL its harness's row count, not bound it.

    python3 docs/reviews/check-row-floor-exactness.py

**THE DEFECT, and it was found in this repository rather than
imagined.** `check-u7-resilience-controls.sh` carried 31 rows against
`ROW_FLOOR=26`. Five rows could have been deleted with CI silent.
Neither branch was wrong: the 26 was honestly derived on
`chore/row-floors`, the five extra rows arrived on `feat/scan-bound`,
and `git merge-base --is-ancestor` says neither commit is an ancestor of
the other. **The MERGE produced the slack floor, and no instrument in
the repository compared a floor to a live count.**

A floor that is too HIGH fails loudly on the next run. A floor that is
too LOW says nothing, forever, which is why this direction needs a
checker and the other one does not.

**THE TABLE IS NOT COPIED HERE.** The row-invocation pattern for each
harness is parsed out of `check-row-floor-controls.sh`, which already
carries it. A second copy of that table is precisely the defect the
floors themselves keep producing - a number typed twice diverges at the
first merge.

**THE SECOND CLAIM: TWO FLOORS FOR ONE HARNESS MUST AGREE.** A floor
lives in two places - `ROW_FLOOR=<n>` inside the harness, and
`--min-rows <n>` on its `ci-harness-gate.sh` line in `ci.yml`. They are
derived at different times by different people, so where a harness has
both, they are two independent opinions about one number and any
disagreement is a defect in at least one of them.

This is not hypothetical either: `check-critical-coverage-amputation.sh`
carried `ROW_FLOOR=18` against `--min-rows 15` for as long as both
existed, and the external floor tolerated the loss of three rows the
internal one would have caught.

**WHAT THIS DOES NOT COVER, stated because a partial check selects for
the form it cannot see.** 24 harnesses carry a literal `ROW_FLOOR`. The
control table names 9, so the exactness claim covers 9. Only 8 harnesses
carry BOTH floors, so the agreement claim covers 8 - the other 16 have a
single number with nothing to check it against, and 8 more are floored
only in `ci.yml`. **Neither claim reaches the majority of harnesses.**
That gap is task #102; it is not closed by this file, and this file
passing does not mean it is.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONTROLS = ROOT / "docs/reviews/check-row-floor-controls.sh"
SCRIPTS = ROOT / "scripts"
CI = ROOT / ".github/workflows/ci.yml"

#: The floor as the harness declares it. Deliberately the same anchored
#: form `check-row-floors.py` uses, so a harness cannot satisfy one
#: checker and not the other.
FLOOR_RE = re.compile(r"^\s*ROW_FLOOR=(\d+)\s*$", re.M)


def _table() -> list[tuple[str, str, int]]:
    """`(harness, row-invocation ERE, rows the ERE cannot match)`.

    Split from the LAST delimiters inward, not the first: one ERE in the
    table is `^control (MUT|AMP) `, and a `cut -f2` would truncate it at
    the `|` inside its own alternation. The control script documents
    that trap and this parser has to honour it too.
    """
    body = re.search(r'TABLE="\n(.*?)\n"', CONTROLS.read_text(encoding="utf-8"), re.S)
    if body is None:
        return []
    rows: list[tuple[str, str, int]] = []
    for line in body.group(1).splitlines():
        if not line.strip():
            continue
        name, rest = line.split("|", 1)
        rest = rest.rsplit("|", 1)[0]  # drop mode
        rest = rest.rsplit("|", 1)[0]  # drop the floor-breach exit code
        rest, extra = rest.rsplit("|", 1)
        rows.append((name, rest, int(extra)))
    return rows


def _external_floors() -> dict[str, int]:
    """`--min-rows` per harness, read off its `ci-harness-gate.sh` line.

    Continuations are folded first: every one of these invocations wraps
    with a trailing backslash, so a line-at-a-time scan sees the harness
    name and its flags as separate lines and pairs nothing.

    The count is asserted against the number of `--min-rows` FLAGS, not
    every occurrence of the string - three sit inside comments, and
    counting those made a correct join look broken.
    """
    raw = CI.read_text(encoding="utf-8")
    joined = re.sub(r"\\\n\s*", " ", raw)
    found: dict[str, int] = {}
    for name, tail in re.findall(r"ci-harness-gate\.sh\s+(\S+)([^\n]*)", joined):
        flag = re.search(r"--min-rows\s+(\d+)", tail)
        if flag:
            found[name] = int(flag.group(1))
    flags = sum(
        1
        for line in raw.splitlines()
        if "--min-rows" in line and not line.lstrip().startswith("#")
    )
    if len(found) != flags:
        raise SystemExit(
            f"parsed {len(found)} --min-rows values but ci.yml carries {flags} "
            "as flags. The join is wrong, and a wrong join here reports a "
            "reassuring zero rather than an error."
        )
    return found


def main() -> int:
    table = _table()
    if not table:
        print(f"PARSED ZERO ROWS out of {CONTROLS.relative_to(ROOT)}.")
        print("An empty parse and a clean table are the same green, so")
        print("this is exit 2 rather than a pass.")
        return 2

    bad: list[str] = []
    for name, ere, extra in table:
        path = SCRIPTS / name
        if not path.exists():
            bad.append(f"{name}: named by the control table but not on disk")
            continue
        text = path.read_text(encoding="utf-8")
        found = FLOOR_RE.search(text)
        if found is None:
            bad.append(f"{name}: no literal ROW_FLOOR=<n>")
            continue
        floor = int(found.group(1))
        rows = sum(1 for line in text.splitlines() if re.search(ere, line)) + extra
        print(f"  {name:42} floor {floor:3}  rows {rows:3}")
        if rows > floor:
            bad.append(
                f"{name}: SLACK by {rows - floor}. It has {rows} rows and a "
                f"floor of {floor}, so {rows - floor} row(s) can be deleted "
                "without the floor noticing. This is the direction that "
                "never announces itself."
            )
        elif rows < floor:
            bad.append(
                f"{name}: floor {floor} exceeds its {rows} rows, so the "
                "harness cannot pass its own floor."
            )

    external = _external_floors()
    paired = 0
    for name in sorted(set(external)):
        path = SCRIPTS / name
        if not path.exists():
            continue
        found = FLOOR_RE.search(path.read_text(encoding="utf-8"))
        if found is None:
            continue
        paired += 1
        internal = int(found.group(1))
        if internal != external[name]:
            bad.append(
                f"{name}: ROW_FLOOR={internal} but ci.yml passes "
                f"--min-rows {external[name]}. Two independent opinions "
                "about one number, and the lower one tolerates losing "
                f"{abs(internal - external[name])} row(s) the other catches."
            )

    print(f"\nHarnesses checked for exactness: {len(table)}")
    print(f"Harnesses carrying BOTH floors, checked for agreement: {paired}")
    if not bad:
        print("Every floor equals its harness's live row count. OK.")
        return 0

    print(f"\n{len(bad)} floor(s) wrong:")
    for line in bad:
        print(f"  {line}")
    print(
        "\nDerive the floor from a run of the harness and write that number "
        "in, rather\nthan adjusting it until this passes - the count and the "
        "floor agreeing for the\nwrong reason is how u7 reached 26 against 31."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
