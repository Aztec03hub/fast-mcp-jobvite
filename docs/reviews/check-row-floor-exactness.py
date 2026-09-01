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

**THE THIRD CLAIM: `--min-rows` MUST EQUAL THE LIVE ROW COUNT TOO
(R12-H2).** The first two claims both read the INTERNAL floor, so the
eight harnesses whose only floor is `--min-rows` in `ci.yml` were
checked by neither - and `ci-harness-gate.sh` compares with `-lt`, a
LOWER bound. Measured when this claim was added: u14's amputation
printed 16 rows against `--min-rows 10` and u7's printed 22 against 19.
Six and three rows deletable with CI green, in the two harnesses that
GREW after their step was wired. That is the same defect the docstring
opens with, on the layer the docstring's own fix could not see, which is
why the population is now the whole of `ci.yml`'s `--min-rows` set.

**HOW THE THIRD CLAIM COUNTS, and why it is not a fourth table.** It
reads the harness's own `echo "########## $label"` row opener, takes the
function that line sits in, collects that function's call sites, and
tests the line each one WILL print against the gate's own `--row-re`.
Nothing about any harness is listed here. A harness whose shape cannot
be read that way is an ERROR, never a skip: skipping is exactly how
those eight went unchecked.

**WHAT THIS STILL DOES NOT COVER, stated because a partial check selects
for the form it cannot see.** The exactness claim reaches only the
harnesses the control table names, and the agreement claim only those
carrying BOTH floors. **The program prints all three counts on every
run** - read them there rather than here, because the counts once
written into this docstring were stale within hours of being typed. It
also cannot tell a floor DERIVED from a run from one that was typed and
happens to be right; only running the harness answers that.
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


def _external_floors() -> dict[str, tuple[int, str]]:
    """`(--min-rows, --row-re)` per harness, off its gate line.

    Continuations are folded first: every one of these invocations wraps
    with a trailing backslash, so a line-at-a-time scan sees the harness
    name and its flags as separate lines and pairs nothing.

    The count is asserted against the number of `--min-rows` FLAGS, not
    every occurrence of the string - three sit inside comments, and
    counting those made a correct join look broken.

    `--row-re` is captured too, because `ci-harness-gate.sh` refuses
    `--min-rows` without it, and the third claim below cannot count rows
    without knowing which printed lines the gate will accept.
    """
    raw = CI.read_text(encoding="utf-8")
    joined = re.sub(r"\\\n\s*", " ", raw)
    found: dict[str, tuple[int, str]] = {}
    for name, tail in re.findall(r"ci-harness-gate\.sh\s+(\S+)([^\n]*)", joined):
        flag = re.search(r"--min-rows\s+(\d+)", tail)
        if not flag:
            continue
        row_re = re.search(r"--row-re\s+'([^']*)'", tail)
        if row_re is None:
            raise SystemExit(
                f"{name}: --min-rows with no --row-re. ci-harness-gate.sh "
                "refuses that pairing at run time, so finding it here means "
                "ci.yml and the gate disagree."
            )
        found[name] = (int(flag.group(1)), row_re.group(1))
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


#: The line every harness prints to open a row. DERIVED, not listed:
#: the emitting function's NAME is read back out of the harness, so a
#: harness that calls its row function something new is still counted.
EMIT = re.compile(r'^\s*echo "##########\s*\$(?:label|1)"', re.M)

#: A shell function definition, `name() {`.
FUNC = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", re.M)


def _live_rows(text: str, row_re: str) -> int | str:
    r"""Rows `--row-re <row_re>` will match when this harness runs.

    Returns the count, or a string saying why it could not be derived.
    **A harness whose shape cannot be read is an ERROR, never a skip** -
    skipping is how the eight externally-floored harnesses went
    unchecked in the first place.

    The method: find the `echo "########## $label"` that opens a row,
    take the function it sits in, collect that function's call sites at
    column 0, and test the line each one WILL print against the gate's
    own regex. Testing the printed line rather than the call site is
    what makes `^########## A[0-9]+ ` and `^########## [A-N]\. ` both
    work, and what keeps the harness's `BASELINE` banner out of the
    count.
    """
    emit = EMIT.search(text)
    if emit is None:
        return 'no `echo "########## $label"` row opener'
    enclosing = [m for m in FUNC.finditer(text) if m.start() < emit.start()]
    if not enclosing:
        return "the row opener is not inside a function"
    fn = enclosing[-1].group(1)
    calls = re.findall(rf'^{re.escape(fn)}\s+"([^"]*)"', text, re.M)
    if not calls:
        return f"row function {fn}() has no call sites at column 0"
    matched = sum(1 for label in calls if re.search(row_re, f"########## {label}"))
    if not matched:
        return (
            f"{fn}() has {len(calls)} call site(s) and the gate's row regex "
            f"{row_re!r} matches NONE of the lines they print. A regex that "
            "matches nothing looks identical to a harness that ran nothing."
        )
    return matched


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
    derived = 0
    print("\n  --min-rows, against the rows the harness will actually print:")
    for name in sorted(set(external)):
        min_rows, row_re = external[name]
        path = SCRIPTS / name
        if not path.exists():
            bad.append(f"{name}: ci.yml passes it --min-rows but it is not on disk")
            continue
        text = path.read_text(encoding="utf-8")

        # CLAIM 3, R12-H2. `--min-rows` is a LOWER bound and nothing
        # compared it to a live count, so the eight harnesses with no
        # internal floor were unchecked in both directions. Measured
        # when this was written: u14's amputation held 16 rows against
        # 10 and u7's held 22 against 19 - six and three rows deletable
        # with CI green. Both grew AFTER their step was wired, which is
        # the merge-produced slack that put u7's CONTROLS at 26 v 31.
        live = _live_rows(text, row_re)
        if isinstance(live, str):
            bad.append(f"{name}: cannot derive a row count - {live}")
        else:
            derived += 1
            print(f"  {name:42} --min-rows {min_rows:3}  rows {live:3}")
            if live > min_rows:
                bad.append(
                    f"{name}: SLACK by {live - min_rows}. It prints {live} "
                    f"rows and ci.yml passes --min-rows {min_rows}, so "
                    f"{live - min_rows} row(s) can be deleted without the "
                    "gate noticing. --min-rows is a LOWER bound; it must "
                    "EQUAL the live count."
                )
            elif live < min_rows:
                bad.append(
                    f"{name}: --min-rows {min_rows} exceeds the {live} rows "
                    "it prints, so this step cannot pass."
                )

        found = FLOOR_RE.search(text)
        if found is None:
            continue
        paired += 1
        internal = int(found.group(1))
        if internal != min_rows:
            bad.append(
                f"{name}: ROW_FLOOR={internal} but ci.yml passes "
                f"--min-rows {min_rows}. Two independent opinions "
                "about one number, and the lower one tolerates losing "
                f"{abs(internal - min_rows)} row(s) the other catches."
            )

    print(f"\nHarnesses checked for exactness: {len(table)}")
    print(f"Harnesses carrying BOTH floors, checked for agreement: {paired}")
    print(f"Harnesses whose --min-rows was compared to a live count: {derived}")
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
