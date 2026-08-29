#!/usr/bin/env python3
"""Refuse two ADRs with one number, and a gap in the sequence.

    python3 docs/reviews/check-adr-numbers.py

**Written because it happened.** `u10-write` checked `git log --all`
before choosing a number, found 0026 taken and 0027 free, and was
correct at the moment it looked. I created a different 0027 afterwards,
on another branch. **Neither of us did anything wrong and both files
merged cleanly**, because they have different filenames and git has no
opinion about the digits in them.

**A duplicate number is worse than it sounds.** Every inbound reference
- a code comment, a report, a task, a commit message - resolves to
"ADR-0027" and there are now two of them. The reader who follows one
gets a coherent document about the wrong subject, which is the same
failure mode as a citation landing on real prose that is not its
subject, and this project has now recorded that eleven times.

A GAP is also refused, because ADR numbers are cited from code and a
missing number is either a deleted decision - which should be a
superseding ADR, not a hole - or a reference nobody can follow.

**What it cannot do**: it reads filenames. An ADR whose FILENAME says
0028 and whose HEADING says 0027 passes here, so the heading is checked
too - that mismatch is exactly what a renumbering leaves behind when it
is done by `git mv` alone.
"""

from __future__ import annotations

import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ADR_DIR = ROOT / "docs" / "adr"
FILENAME = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
HEADING = re.compile(r"^#\s*ADR-(\d{4})\b")


def main() -> int:
    if not ADR_DIR.is_dir():
        print(f"NO ADR DIRECTORY at {ADR_DIR}. Exiting 2, not 0.")
        return 2

    numbers: dict[int, list[str]] = collections.defaultdict(list)
    mismatched: list[str] = []
    for path in sorted(ADR_DIR.glob("*.md")):
        match = FILENAME.match(path.name)
        if match is None:
            continue  # README.md and anything else deliberately unnumbered
        number = int(match.group(1))
        numbers[number].append(path.name)

        first = path.read_text(encoding="utf-8").splitlines()[0]
        heading = HEADING.match(first)
        if heading is None:
            mismatched.append(f"{path.name}: first line is not `# ADR-NNNN`")
        elif int(heading.group(1)) != number:
            mismatched.append(
                f"{path.name}: filename says {number:04d}, heading says {heading.group(1)}"
            )

    if not numbers:
        print("MATCHED ZERO ADRs. The selector is broken; a green means nothing.")
        return 1

    duplicates = {n: names for n, names in numbers.items() if len(names) > 1}
    lowest, highest = min(numbers), max(numbers)
    gaps = [n for n in range(lowest, highest + 1) if n not in numbers]

    print(f"ADRs: {sum(len(v) for v in numbers.values())}, numbered {lowest:04d}-{highest:04d}")

    for number, names in sorted(duplicates.items()):
        print(f"  DUPLICATE {number:04d}:")
        for name in names:
            print(f"      {name}")
    for number in gaps:
        print(f"  GAP       {number:04d} - no ADR carries this number")
    for problem in mismatched:
        print(f"  HEADING   {problem}")

    if duplicates or gaps or mismatched:
        print(
            f"\n{len(duplicates)} duplicate(s), {len(gaps)} gap(s), "
            f"{len(mismatched)} heading mismatch(es)."
        )
        print("An ADR number is cited from code. Two documents cannot share one.")
        return 1

    print("Every ADR number is unique, contiguous, and matches its own heading.")
    _report_branches(highest)
    return 0


def _branch_numbers() -> dict[int, set[str]]:
    """ADR numbers claimed on EVERY local branch, not just this one.

    **R8-L1: this checker read only the working tree, so it reported
    0030 as free on a branch where another branch had already taken
    it.** A reviewer on `review/r8` was told "ADRs: 29, numbered
    0001-0029, exit 0" while ADR-0030 was already Accepted on `main`,
    which was not an ancestor of its base. The checker was right about
    the tree and wrong about the question anyone asks it, which is
    "may I take the next number?".

    That is the two-agents-both-correct-when-they-looked collision this
    project has already had once, with U10 and me both taking 0027.
    """
    import subprocess

    claimed: dict[int, set[str]] = collections.defaultdict(set)
    branches = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    for branch in branches:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", branch, "--", "docs/adr/"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        for path in listing.stdout.splitlines():
            match = re.search(r"docs/adr/(\d{4})-", path)
            if match:
                claimed[int(match.group(1))].add(branch)
    return claimed


def _report_branches(highest_here: int) -> None:
    """Say what the NEXT FREE number is across every branch."""
    claimed = _branch_numbers()
    if not claimed:
        print("\nNo branches scanned; the cross-branch check did not run.")
        return

    highest = max(claimed)
    print(f"\nAcross {len({b for v in claimed.values() for b in v})} local branch(es): "
          f"highest ADR number claimed anywhere is {highest:04d}.")

    elsewhere = sorted(n for n in claimed if n > highest_here)
    for number in elsewhere:
        print(f"  ELSEWHERE {number:04d} exists on {', '.join(sorted(claimed[number]))}")
        print("            but NOT in this checkout - do not reuse this number.")

    print(f"NEXT FREE ADR NUMBER: {max(highest, highest_here) + 1:04d}")
    if elsewhere:
        print("Take it from THIS line, not from the count above: a number can be")
        print("claimed on a branch this checkout cannot see.")


if __name__ == "__main__":
    sys.exit(main())
