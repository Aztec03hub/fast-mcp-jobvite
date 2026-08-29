#!/usr/bin/env python3
"""Repoint `DESIGN.md:<n>` citations across a DESIGN.md re-freeze.

ONE-SHOT, for task #95. Not wired into CI and not intended to be: it
exists so that the repoint map is a runnable artefact rather than a
paragraph claiming a map was built, and so a reviewer can re-derive
every number in the report by running it instead of trusting it.

The map is built by `difflib.SequenceMatcher` over the two versions'
lines, and **every repoint is verified by content, not by arithmetic**:
a mapped line is only accepted when the old file's text at the old
number is byte-identical to the new file's text at the new number. A
citation whose subject line was itself edited has no honest mechanical
answer and is reported as MANUAL rather than moved, because a
mapped-but-changed line is exactly the shape that resolves green while
pointing at different words than the citer read.

Usage:
    adr-batch-repoint.py --old <file> --new <file> --report
    adr-batch-repoint.py --old F --new F --apply <path> [<path>...]
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys
from collections.abc import Iterator

#: A citation is `DESIGN.md:12` or `DESIGN.md:12-34`. The optional
#: second half is captured separately so a range is repointed at BOTH
#: ends: a range that is repointed only at its start silently contracts,
#: and a contracted range still resolves, which is the hazard this whole
#: task exists downstream of.
CITATION = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")


def build_map(old: list[str], new: list[str]) -> dict[int, int]:
    """Map 1-indexed old line -> new line, unchanged lines only.

    Lines inside a `replace` or `delete` opcode are deliberately
    absent from the map. Their citers have to be looked at by a
    human, because the text they cited is not the text that now
    lives anywhere.
    """
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    mapping: dict[int, int] = {}
    for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
        if tag != "equal":
            continue
        for offset in range(i2 - i1):
            mapping[i1 + offset + 1] = j1 + offset + 1
    return mapping


def classify(
    start: int,
    end: int | None,
    mapping: dict[int, int],
    old: list[str],
    new: list[str],
) -> tuple[str, str]:
    """Return (verdict, replacement). Verdict is one of three.

    UNMOVED - every endpoint maps to itself. Nothing to do. MOVED -
    every endpoint maps, and the content at each new number is
    byte-identical to the content at the old one. MANUAL - an
    endpoint is out of bounds, or fell inside an edited region, or
    mapped to a line whose text differs. Never rewritten here.
    """
    endpoints = [start] if end is None else [start, end]
    if any(n < 1 or n > len(old) for n in endpoints):
        return "MANUAL", ""
    if any(n not in mapping for n in endpoints):
        return "MANUAL", ""
    moved = [mapping[n] for n in endpoints]
    for before, after in zip(endpoints, moved, strict=True):
        if old[before - 1] != new[after - 1]:
            return "MANUAL", ""
    if moved == endpoints:
        return "UNMOVED", ""
    text = f"DESIGN.md:{moved[0]}"
    if end is not None:
        text = f"DESIGN.md:{moved[0]}-{moved[1]}"
    return "MOVED", text


def scan(
    path: pathlib.Path,
    mapping: dict[int, int],
    old: list[str],
    new: list[str],
) -> Iterator[tuple[int, int, str, str, str]]:
    """Yield (lineno, index, matched, verdict, repl) per file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return
    for lineno, line in enumerate(lines, start=1):
        for index, match in enumerate(CITATION.finditer(line)):
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else None
            verdict, replacement = classify(start, end, mapping, old, new)
            yield lineno, index, match.group(0), verdict, replacement


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--apply", nargs="*", default=[])
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    old = pathlib.Path(args.old).read_text(encoding="utf-8").splitlines()
    new = pathlib.Path(args.new).read_text(encoding="utf-8").splitlines()
    mapping = build_map(old, new)

    targets = [pathlib.Path(p) for p in (args.apply or args.paths)]
    files: list[pathlib.Path] = []
    for target in targets:
        if target.is_dir():
            files.extend(sorted(p for p in target.rglob("*") if p.is_file()))
        elif target.is_file():
            files.append(target)

    tally = {"UNMOVED": 0, "MOVED": 0, "MANUAL": 0}
    for path in files:
        # keyed (lineno, occurrence-index-on-that-line) -> replacement
        # text. The index is load-bearing: `str.replace` on a line
        # carrying both `DESIGN.md:551` and `DESIGN.md:551-553` rewrites
        # the wrong one, because the shorter form is a prefix of the
        # longer.
        edits: dict[tuple[int, int], str] = {}
        for lineno, index, matched, verdict, replacement in scan(
            path, mapping, old, new
        ):
            tally[verdict] += 1
            if verdict != "UNMOVED":
                print(f"{path}:{lineno}\t{matched}\t{verdict}\t{replacement}")
            if verdict == "MOVED":
                edits[(lineno, index)] = replacement
        if edits and args.apply:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            for lineno in {ln for ln, _ in edits}:
                counter = iter(range(10_000))

                # Every name the closure uses is bound as a DEFAULT,
                # `edits` included. Leaving `edits` free would be a
                # late-binding read of a variable the enclosing loop
                # is still walking (ruff B023).
                def rewrite(
                    match: re.Match[str],
                    lineno: int = lineno,
                    counter: Iterator[int] = counter,
                    edits: dict[tuple[int, int], str] = edits,
                ) -> str:
                    key = (lineno, next(counter))
                    return edits.get(key) or match.group(0)

                lines[lineno - 1] = CITATION.sub(rewrite, lines[lineno - 1])
            path.write_text("".join(lines), encoding="utf-8")

    print(
        f"\nTOTAL unmoved={tally['UNMOVED']} moved={tally['MOVED']} "
        f"manual={tally['MANUAL']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
