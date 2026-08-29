#!/usr/bin/env python3
"""Apply `check-design-citations.py --since <sha>`'s MOVED lines to the tree.

The companion to `check-design-citations.py`. That script SAYS which citations
moved; this one MOVES them, from that script's own parsed output rather than
from anything retyped, because retyping a value just read is the step that has
failed repeatedly here.

It refuses to guess:

  - It ignores BROKEN lines entirely. Those are citations whose target line
    CHANGED, and only a human re-reading the subject can repoint them.
  - It ignores any line carrying the marker `REPOINT-EXEMPT`. A script that
    WRITES an example citation - a regex test string, a docstring illustrating
    the two forms - is not CITING anything, and repointing it corrupts the
    example silently. Measured: the first pass of this batch shifted three of
    `check-design-citations.py`'s own examples.
  - It keys on (file, line-the-citation-sits-on, old-range), never on a naive
    string replacement, because a single line can carry several citations and
    `DESIGN.md:<n>` can be a prefix of `DESIGN.md:<nn>`.
  - It asserts it parsed a non-zero number of MOVED lines, and fails loudly if
    a citation the report named is not where the report said it was.

Usage:
    python3 docs/reviews/repoint-design-citations.py <sha>          # dry run
    python3 docs/reviews/repoint-design-citations.py <sha> --write

Exit 0 on success, 1 if anything did not line up. No dependencies.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "docs" / "reviews" / "check-design-citations.py"

_CITATION = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")
_MOVED = re.compile(
    r"^\s*MOVED:\s+(?P<file>[^:]+):(?P<lineno>\d+): "
    r"DESIGN\.md:(?P<os>\d+)(?:-(?P<oe>\d+))? -> "
    r"DESIGN\.md:(?P<ns>\d+)(?:-(?P<ne>\d+))?\s*$"
)


def report(sha: str) -> str:
    """The checker's own output. Exit 1 is its normal state when moves exist."""
    return subprocess.run(
        [sys.executable, str(CHECKER), "--since", sha],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    ).stdout


def parse(text: str) -> dict[tuple[str, int], dict[tuple[int, int], tuple[int, int]]]:
    moves: dict[tuple[str, int], dict[tuple[int, int], tuple[int, int]]] = {}
    for line in text.splitlines():
        m = _MOVED.match(line)
        if not m:
            continue
        cited_in = pathlib.Path(REPO_ROOT / m["file"])
        try:
            if "REPOINT-EXEMPT" in cited_in.read_text().splitlines()[int(m["lineno"]) - 1]:
                continue
        except (OSError, IndexError, UnicodeDecodeError):
            pass
        old_s = int(m["os"])
        old_e = int(m["oe"]) if m["oe"] else old_s
        new_s = int(m["ns"])
        new_e = int(m["ne"]) if m["ne"] else new_s
        moves.setdefault((m["file"], int(m["lineno"])), {})[(old_s, old_e)] = (new_s, new_e)
    return moves


def apply(moves, write: bool) -> int:
    by_file: dict[str, dict[int, dict]] = {}
    for (rel, lineno), pairs in moves.items():
        by_file.setdefault(rel, {})[lineno] = pairs

    applied = missed = 0
    for rel, lines in sorted(by_file.items()):
        path = REPO_ROOT / rel
        text = path.read_text().splitlines(keepends=True)
        for lineno, pairs in lines.items():
            seen: set[tuple[int, int]] = set()

            def sub(m: re.Match[str]) -> str:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                target = pairs.get((start, end))
                if target is None:
                    return m.group(0)
                seen.add((start, end))
                ns, ne = target
                return f"DESIGN.md:{ns}" + (f"-{ne}" if ne != ns else "")

            original = text[lineno - 1]
            text[lineno - 1] = _CITATION.sub(sub, original)
            unseen = set(pairs) - seen
            if unseen:
                missed += len(unseen)
                print(f"  NOT FOUND: {rel}:{lineno}: the report named "
                      f"{sorted(unseen)} but that line does not carry it")
            applied += len(seen)
        if write:
            path.write_text("".join(text))

    print(f"\n  {applied} citation(s) repointed across {len(by_file)} file(s)"
          f"{'' if write else ' (DRY RUN, nothing written)'}")
    if missed:
        print(f"  {missed} the report named and the tree does not carry. NOTHING IS TRUSTWORTHY.")
        return 1
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    sha = argv[0]
    text = report(sha)
    moves = parse(text)
    total = sum(len(v) for v in moves.values())
    if total == 0:
        print("SELECTOR CONTROL: parsed 0 MOVED lines out of "
              f"{len(text.splitlines())} lines of report. The parser is broken, "
              "or there is genuinely nothing to move. Check the report by eye.")
        return 1
    print(f"  parsed {total} MOVED citation(s) from the checker's output")
    return apply(moves, write="--write" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
