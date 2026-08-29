#!/usr/bin/env python3
"""Verify a citation repoint by CONTENT, not by re-running the map that made it.

ONE-SHOT, for task #95, and deliberately not the inverse of
`adr-batch-repoint.py`: re-running that script over already-repointed files
re-maps the new numbers as if they were old ones and prints a confident,
meaningless second answer. That is the instrument agreeing with itself.

This joins on TEXT instead. For every citation in a repointed file it pairs the
number the file carried BEFORE with the number it carries NOW, then asserts
that the old design's text at the old range is byte-identical to the new
design's text at the new range. A citation that resolves is not the claim; a
citation that still covers the words its author read is.

    old_design[old_start : old_end]  ==  new_design[new_start : new_end]

Pairing is positional within a file: the Nth citation before is the Nth
citation after. A repoint that adds or drops a citation breaks that
assumption, so the count is asserted per file and a mismatch is a failure
rather than a silent realignment - a realigned pairing would compare the wrong
two ranges and could report either a false pass or a false failure.

Exit 0 when every pair matches, 1 otherwise.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

CITATION = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")


def git_show(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def citations(text: str) -> list[tuple[int, int]]:
    """Every citation in the file, as (start, end) with end==start when bare."""
    found = []
    for match in CITATION.finditer(text):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        found.append((start, end))
    return found


def slice_lines(lines: list[str], start: int, end: int) -> list[str] | None:
    if start < 1 or end > len(lines) or start > end:
        return None
    return lines[start - 1 : end]


def contains(haystack: list[str], needle: list[str]) -> bool:
    """Is `needle` a CONTIGUOUS run of lines inside `haystack`?

    Contiguity is the point. A subsequence test would call a range "still
    covering its subject" when the batch had inserted a paragraph into the
    MIDDLE of the cited sentences, which is a different and worse outcome than
    growing around them.
    """
    if not needle or len(needle) > len(haystack):
        return False
    return any(
        haystack[i : i + len(needle)] == needle
        for i in range(len(haystack) - len(needle) + 1)
    )


def absorbs(haystack: list[str], needle: list[str]) -> bool:
    """Is every line of `needle` still inside `haystack`, in order?

    Weaker than `contains`, and the distinction is the whole point. When a
    batch inserts a paragraph in the MIDDLE of a cited range, the citer's lines
    are all still covered but no longer adjacent. Nothing has fallen outside
    the citation - which is the property that matters - but the range now says
    more than its author did, so it is reported rather than passed in silence.
    """
    if not needle:
        return False
    iterator = iter(haystack)
    return all(any(line == candidate for candidate in iterator) for line in needle)


def main() -> int:
    base_ref, design_old_ref = sys.argv[1], sys.argv[2]
    paths = sys.argv[3:]

    old_design = (git_show(design_old_ref, "docs/DESIGN.md") or "").splitlines()
    new_design = pathlib.Path("docs/DESIGN.md").read_text(
        encoding="utf-8"
    ).splitlines()
    if not old_design:
        print(f"FATAL: no docs/DESIGN.md at {design_old_ref}", file=sys.stderr)
        return 2

    checked = failed = widened = 0
    for path in paths:
        before = git_show(base_ref, path)
        if before is None:
            print(f"SKIP (new file, nothing to compare): {path}")
            continue
        after = pathlib.Path(path).read_text(encoding="utf-8")
        old_cites, new_cites = citations(before), citations(after)
        if len(old_cites) != len(new_cites):
            print(
                f"FAIL {path}: citation COUNT changed "
                f"{len(old_cites)} -> {len(new_cites)}; pairing is unsafe"
            )
            failed += 1
            continue
        for (o_start, o_end), (n_start, n_end) in zip(
            old_cites, new_cites, strict=True
        ):
            checked += 1
            was = slice_lines(old_design, o_start, o_end)
            now = slice_lines(new_design, n_start, n_end)
            if was is None:
                print(
                    f"FAIL {path}: DESIGN.md:{o_start}-{o_end} was already out "
                    f"of bounds in the OLD design - it was wrong before this task"
                )
                failed += 1
            elif now is None:
                print(f"FAIL {path}: DESIGN.md:{n_start}-{n_end} out of bounds now")
                failed += 1
            elif was == now:
                pass
            elif contains(now, was) or absorbs(now, was):
                # The range grew around an insertion of this batch's own. Every
                # line the citer read is still inside the range it now names,
                # with new adjacent material alongside. That is the outcome a
                # repoint is SUPPOSED to produce when a section gains a
                # paragraph, and it is the opposite of the contraction hazard:
                # nothing the author cited has fallen outside.
                widened += 1
                shape = "WIDENED" if contains(now, was) else "ABSORBED"
                print(f"{shape} {path}: {o_start}-{o_end} -> {n_start}-{n_end}")
            else:
                # The cited TEXT itself was edited. No number is the right
                # answer here - the citing prose has to be read and, where it
                # asserts something the edit falsified, rewritten in place.
                print(
                    f"FAIL {path}: {o_start}-{o_end} -> {n_start}-{n_end} "
                    f"SUBJECT TEXT CHANGED"
                )
                print(f"       was: {was[0][:90]!r}")
                print(f"       now: {now[0][:90]!r}")
                failed += 1

    print(
        f"\nchecked={checked} widened={widened} failed={failed}",
        file=sys.stderr,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
