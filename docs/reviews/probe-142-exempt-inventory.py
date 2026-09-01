#!/usr/bin/env python3
"""Enumerate every REPOINT-EXEMPT line across BOTH checkers' containers.

The two wired citation gates do NOT share a container, so "the exemption
count" is two numbers, not one:

  check-design-citations.py       .py .toml .md .yml .yaml .sh
  check-design-citation-shape.py  .py .sh

Prints, per marked line: the container(s) it is in, the file:line, how
many `DESIGN.md:N` citations the line carries, and the line itself. The
citation count is the load-bearing column - a marked line carrying MORE
than the one item being exempted is what makes line granularity a live
defect rather than a theoretical one.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MARKER = "REPOINT" + "-EXEMPT"
CITE = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")

BOUNDS_SUFFIXES = {".py", ".toml", ".md", ".yml", ".yaml", ".sh"}
BOUNDS_SKIP_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
}
SHAPE_SUFFIXES = {".py", ".sh"}


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [n for n in out.split("\0") if n]


def main() -> int:
    rows = []
    n_bounds = n_shape = 0
    for name in tracked():
        p = pathlib.Path(name)
        in_bounds = p.suffix in BOUNDS_SUFFIXES and not any(
            part in BOUNDS_SKIP_PARTS for part in p.parts
        )
        in_shape = p.suffix in SHAPE_SUFFIXES
        if not (in_bounds or in_shape):
            continue
        try:
            text = (ROOT / name).read_text()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if MARKER not in line:
                continue
            if in_bounds:
                n_bounds += 1
            if in_shape:
                n_shape += 1
            cites = CITE.findall(line)
            where = (
                "both"
                if (in_bounds and in_shape)
                else ("bounds" if in_bounds else "shape")
            )
            rows.append((name, lineno, where, len(cites), line.strip()))

    print(f"marked lines in check-design-citations.py container: {n_bounds}")
    print(f"marked lines in check-design-citation-shape.py container: {n_shape}")
    print(f"distinct marked lines (union): {len(rows)}")
    zero = sum(1 for r in rows if r[3] == 0)
    one = sum(1 for r in rows if r[3] == 1)
    many = sum(1 for r in rows if r[3] > 1)
    print(f"  carrying 0 citations: {zero}   (the marker exempts nothing on this line)")
    print(f"  carrying 1 citation:  {one}")
    print(f"  carrying 2+ citations: {many}  (line granularity is live here)")
    print()
    for name, lineno, where, ncites, line in rows:
        print(f"{name}:{lineno}\t[{where}]\tcites={ncites}\t{line[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
