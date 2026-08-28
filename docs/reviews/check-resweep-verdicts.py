#!/usr/bin/env python3
"""Emit the final verdict per B-number from CONFORMANCE-RESWEEP.md, and make the count check itself.

CONF-6 finding F-10. This file exists because the resweep's table has already produced one wrong
population, in a report that then drove a work assignment.

The failure was not carelessness. The table has SEVEN columns -

    B | Requires | Clause (re-verified) | Was | Now | Category | Evidence

- and the two that matter sit next to each other. Column 5 (`Now`) is the current verdict; column 6
is `Category`, whose vocabulary is DEFECT / NOT-YET-BUILT / DEFERRED-WITH-REASON / STILL-OPEN. A
parser that takes "the last verdict-looking cell" picks up DEFERRED-WITH-REASON and reports a
DEFERRED *verdict*, which does not exist. That is what happened: five rows - B73, B77, B81, B89,
B103 - moved out of PARTIAL/UNADDRESSED into an invented class, and four of the five are the README
cluster, so the error made the largest remaining gap look smaller than it is.

Six rows (B7, B30, B47, B56, B96, B97) quote markdown tables INSIDE a cell and carry escaped pipes,
so a naive `line.split('|')` gives them the wrong column count and silently shifts every cell after
the escape. Splitting on unescaped pipes only is not a nicety here; it is the difference between
reading column 5 and reading column 4.

WHAT MAKES THIS DIFFERENT FROM THE PARSER THAT WAS WRONG: it does not merely produce a count, it
asserts its count against the one the document states about itself in section 1's "The 59 re-walked"
table. Two independent statements of the same number, one from the prose and one from the rows,
have to agree. A count that checks itself is the only kind that survives being copied forward.

SELECTOR CONTROL, because a wrong zero explains itself: parsing zero rows, or finding no section 1
table, is a FAILURE and never a pass. A search at a path that does not exist returns the same clean
empty as a real absence, and this repository has produced that mistake more than once.

Usage:
    python3 docs/reviews/check-resweep-verdicts.py [path/to/CONFORMANCE-RESWEEP.md]
    python3 docs/reviews/check-resweep-verdicts.py --controls

Exit 0 on success, 1 on any failure. No dependencies.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

DEFAULT_DOC = "docs/reviews/CONFORMANCE-RESWEEP.md"

# Column 5 of the section 3 table. NOT the Category column beside it.
VERDICT_COLUMN = 4  # zero-based

VERDICTS = ("SATISFIED", "PARTIAL", "UNADDRESSED", "NOT-APPLICABLE")

# Section 1's self-description. The heading is the anchor: section 1 carries a SECOND table
# ("Projected across all 106") whose numbers are a different population, and reading that one
# instead would compare 59 rows against a 106-row claim and call the disagreement a defect.
COUNTS_HEADING = "### The 59 re-walked"

# `|` not preceded by a backslash.
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")

ROW_START = re.compile(r"\|\s*\*\*(B\d+)\*\*\s*\|")


def cells(line: str) -> list[str]:
    """Split one markdown table row into cells, honouring backslash-escaped pipes."""
    return [c.strip() for c in UNESCAPED_PIPE.split(line.rstrip())[1:-1]]


def normalise(cell: str) -> str:
    """Strip markdown emphasis and any parenthetical qualifier.

    `**SATISFIED (design)**` and `SATISFIED` are the same verdict; two rows write it differently.
    """
    text = re.sub(r"[*`]", "", cell).strip()
    return re.sub(r"\s*\(.*\)\s*$", "", text).strip()


def parse_rows(text: str) -> tuple[dict[str, str], list[str]]:
    """Return {B-number: final verdict} and a list of problems found while parsing."""
    verdicts: dict[str, str] = {}
    problems: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        match = ROW_START.match(line)
        if not match:
            continue
        bnum = match.group(1)
        row = cells(line)
        if len(row) != 7:
            problems.append(
                f"{DEFAULT_DOC}:{lineno}: {bnum} has {len(row)} cells, expected 7. "
                "An escaped pipe inside a cell shifts every column after it."
            )
            continue
        verdict = normalise(row[VERDICT_COLUMN])
        if verdict not in VERDICTS:
            problems.append(
                f"{DEFAULT_DOC}:{lineno}: {bnum}'s column {VERDICT_COLUMN + 1} reads "
                f"{verdict!r}, which is not a verdict. The Category column is next to it and its "
                "vocabulary (DEFERRED-WITH-REASON, STILL-OPEN, NOT-YET-BUILT) reads like one."
            )
            continue
        if bnum in verdicts:
            problems.append(f"{DEFAULT_DOC}:{lineno}: {bnum} appears twice in the table.")
            continue
        verdicts[bnum] = verdict
    return verdicts, problems


def parse_stated_counts(text: str) -> dict[str, int]:
    """Read section 1's own counts - the last numeric column of the '59 re-walked' table."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == COUNTS_HEADING)
    except StopIteration:
        return {}
    stated: dict[str, int] = {}
    for line in lines[start : start + 20]:
        row = cells(line)
        if len(row) < 2:
            continue
        label = normalise(row[0])
        if label not in VERDICTS:
            continue
        numbers = re.findall(r"\d+", row[-1])
        if numbers:
            stated[label] = int(numbers[-1])
    return stated


def check(path: pathlib.Path) -> int:
    if not path.is_file():
        print(f"FAIL: {path} does not exist. A search at a missing path is not an absence.")
        return 1

    text = path.read_text(encoding="utf-8")
    verdicts, problems = parse_rows(text)
    stated = parse_stated_counts(text)

    failures = list(problems)

    # Selector controls. A zero here means the parser matched nothing, which is indistinguishable
    # from a clean document unless it is called out as a failure.
    if not verdicts:
        failures.append(
            "FAIL: parsed zero rows from section 3. Either the table's shape changed or the row "
            "pattern no longer matches. A green from a parser that read nothing means nothing."
        )
    if not stated:
        failures.append(
            f"FAIL: found no counts under {COUNTS_HEADING!r}. Without the document's own numbers "
            "there is nothing to check the row tally against, and this script degrades into the "
            "unchecked parser it exists to replace."
        )

    counted = {v: sum(1 for x in verdicts.values() if x == v) for v in VERDICTS}

    if verdicts and stated:
        for verdict in VERDICTS:
            want = stated.get(verdict)
            got = counted[verdict]
            if want is None:
                failures.append(f"FAIL: section 1 states no count for {verdict}.")
            elif want != got:
                failures.append(
                    f"FAIL: {verdict}: section 1 says {want}, the rows give {got}. "
                    "The prose and the table disagree; one of them has been edited alone."
                )

    print(f"Rows parsed: {len(verdicts)}")
    for verdict in VERDICTS:
        print(f"  {verdict:<16} rows={counted[verdict]:<3} section 1 says={stated.get(verdict, '-')}")

    open_rows = sorted(
        (b for b, v in verdicts.items() if v in ("PARTIAL", "UNADDRESSED")),
        key=lambda b: int(b[1:]),
    )
    print(f"\nStill open (PARTIAL or UNADDRESSED): {len(open_rows)}")
    print("  " + " ".join(open_rows))

    if failures:
        print()
        for failure in failures:
            print(failure)
        print(f"\n{len(failures)} failure(s).")
        return 1

    print("\nThe row tally and section 1's stated counts agree. OK.")
    return 0


# ---------------------------------------------------------------------------
# Controls. Every check above is made to fire against a deliberately broken copy, because a check
# nobody has seen go red is a check nobody has tested.
# ---------------------------------------------------------------------------

def _mutate_verdict(text: str) -> str:
    """Flip one row's verdict so the rows and section 1 disagree."""
    out = []
    done = False
    for line in text.splitlines():
        match = ROW_START.match(line)
        if match and not done and "**PARTIAL**" in line:
            line = line.replace("**PARTIAL**", "**SATISFIED**", 1)
            done = True
        out.append(line)
    assert done, "control could not find a PARTIAL row to flip"
    return "\n".join(out)


def _mutate_stated_count(text: str) -> str:
    """Change section 1's stated number so the document contradicts itself."""
    return text.replace("| PARTIAL | 24 | **18** |", "| PARTIAL | 24 | **19** |", 1)


def _mutate_drop_rows(text: str) -> str:
    """Remove every section 3 row - the selector control."""
    return "\n".join(line for line in text.splitlines() if not ROW_START.match(line))


def _mutate_drop_counts_heading(text: str) -> str:
    """Remove section 1's heading so its counts cannot be found."""
    return text.replace(COUNTS_HEADING, "### Something else entirely", 1)


def _mutate_column_shift(text: str) -> str:
    """Put a Category value where the verdict belongs.

    This is the exact defect that produced the wrong population: DEFERRED-WITH-REASON read as a
    verdict. The parser must refuse it rather than inventing a class.
    """
    out = []
    done = False
    for line in text.splitlines():
        if ROW_START.match(line) and not done and "**PARTIAL**" in line:
            line = line.replace("**PARTIAL**", "**DEFERRED-WITH-REASON**", 1)
            done = True
        out.append(line)
    assert done, "control could not find a PARTIAL row to shift"
    return "\n".join(out)


CONTROLS = [
    ("a row's verdict flipped", _mutate_verdict),
    ("section 1's stated count edited alone", _mutate_stated_count),
    ("every section 3 row removed (selector control)", _mutate_drop_rows),
    ("section 1's counts heading renamed", _mutate_drop_counts_heading),
    ("a Category value sitting in the verdict column", _mutate_column_shift),
]


def run_controls(path: pathlib.Path) -> int:
    original = path.read_text(encoding="utf-8")

    if check(path) != 0:
        print("\nABORT: the real document is already red, so no control below proves anything.")
        return 1
    print("\n--- controls ---")

    bad = 0
    for name, mutate in CONTROLS:
        with tempfile.TemporaryDirectory() as tmp:
            broken = pathlib.Path(tmp) / path.name
            try:
                mutated = mutate(original)
            except AssertionError as exc:
                print(f"  DID NOT FIRE  {name}: {exc}")
                bad += 1
                continue
            if mutated == original:
                print(f"  DID NOT FIRE  {name}: the mutation changed nothing")
                bad += 1
                continue
            broken.write_text(mutated, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, __file__, str(broken)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"  DID NOT FIRE  {name}")
                bad += 1
            else:
                print(f"  fired         {name}")

    print(f"\n{len(CONTROLS) - bad}/{len(CONTROLS)} controls fired.")
    if bad:
        return 1

    print(f"post-run re-check of the real {path.name}: exit={check(path)}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--controls"]
    path = pathlib.Path(args[0]) if args else pathlib.Path(DEFAULT_DOC)
    if "--controls" in sys.argv[1:]:
        return run_controls(path)
    return check(path)


if __name__ == "__main__":
    sys.exit(main())
