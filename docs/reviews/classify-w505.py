#!/usr/bin/env python3
"""Classify every W505 violation as flowing prose vs a structure 72 was never about.

PEP 8's 72-character limit is a readability rule for FLOWING TEXT. W505 counts every
line inside a docstring or comment, including fenced code blocks, markdown tables, and
transcript output pasted as evidence - none of which can be rewrapped without either
breaking the code or destroying the alignment that makes the table readable.

The point of this script is to decide whether complying is cheap or whether the clause
needs a scoped ADR, by MEASURING the split instead of guessing at it.

Reads `ruff check --select W505` output, then re-reads each cited line in context.

**THIS IS A ONE-SHOT ANALYSIS TOOL. It is deliberately NOT wired into
CI, and it cannot be.** Its question - "is complying with B49b cheap, or
does the clause need a scoped ADR?" - was answered: 1608 violations, no
shape genuinely unbreakable, exemption list empty, and the sweep landed
at `f0c3764`. A tool whose question is settled is a one-shot, and wiring
it would add a gate with nothing left to guard.

**On a swept tree it exits 1**, reporting "POSITIVE CONTROL FAILED: ruff
reported no W505 at all". That is the control WORKING, not a bug: a
classifier that reports a clean zero it cannot distinguish from a broken
selector is worthless, and this project has found wrong zeros
repeatedly. **Do not "fix" that by deleting the positive control.** If
this ever needs to run against a clean tree, add an `--allow-empty` flag
so an empty result passes only when the caller has declared it expected.

This paragraph exists because `check-resweep-verdicts.py` was a one-shot
that did NOT say so, and the result was that nothing invoked it and
nobody could tell "deliberately unwired" from "overlooked" - a review
found it, and it was wired at `ff7a923`. An undeclared one-shot is
indistinguishable from an unwired gate.
"""

from __future__ import annotations

import ast
import collections
import json
import pathlib
import subprocess
import sys
import tokenize

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def violations() -> list[tuple[pathlib.Path, int]]:
    """Every (file, line) W505 flags, from ruff's own JSON output."""
    proc = subprocess.run(
        [
            "uv", "run", "--frozen", "ruff", "check", ".",
            "--select", "W505",
            "--config", "lint.pycodestyle.max-doc-length = 72",
            "--output-format", "json",
        ],
        capture_output=True, text=True, cwd=REPO,
    )
    return [
        (REPO / item["filename"], item["location"]["row"])
        for item in json.loads(proc.stdout or "[]")
    ]


def string_spans(path: pathlib.Path) -> list[tuple[int, int]]:
    """Line ranges of every string literal, so we can tell docstring from comment."""
    spans = []
    with path.open("rb") as handle:
        for tok in tokenize.tokenize(handle.readline):
            if tok.type == tokenize.STRING:
                spans.append((tok.start[0], tok.end[0]))
    return spans


def classify(lines: list[str], row: int, spans: list[tuple[int, int]]) -> str:
    """What KIND of long line is this?"""
    text = lines[row - 1]
    stripped = text.strip()

    if stripped.startswith("#"):
        kind_prefix = "comment"
    elif any(start <= row <= end for start, end in spans):
        kind_prefix = "docstring"
    else:
        return "other"

    # A markdown table row: leading and trailing pipes with a pipe inside.
    if stripped.startswith("|") and stripped.count("|") >= 2:
        return f"{kind_prefix}: table"

    # Inside a fenced block? Count fences opened before this row within the docstring.
    fences = 0
    for probe in range(row - 1):
        if lines[probe].strip().startswith("```"):
            fences += 1
    if fences % 2 == 1:
        return f"{kind_prefix}: fenced code"

    # A single token longer than the limit cannot be wrapped at all. In this
    # repository all 18 turned out to be 79-character `# ---` section dividers
    # rather than the URLs and paths this branch was written for, which is why
    # the measurement had to be read rather than trusted to its own label.
    longest = max((len(word) for word in stripped.split()), default=0)
    if longest > 60:
        return f"{kind_prefix}: unbreakable token"

    return f"{kind_prefix}: flowing prose"


def main() -> int:
    counts: collections.Counter[str] = collections.Counter()
    per_file: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    cache: dict[pathlib.Path, tuple[list[str], list[tuple[int, int]]]] = {}

    found = violations()
    if not found:
        print("POSITIVE CONTROL FAILED: ruff reported no W505 at all.")
        return 1

    for path, row in found:
        if path not in cache:
            source = path.read_text()
            ast.parse(source)  # the file must be valid before we reason about it
            cache[path] = (source.splitlines(), string_spans(path))
        lines, spans = cache[path]
        kind = classify(lines, row, spans)
        counts[kind] += 1
        per_file[path.relative_to(REPO).as_posix()][kind] += 1

    total = sum(counts.values())
    print(f"W505 violations at max-doc-length=72: {total}\n")
    for kind, count in counts.most_common():
        print(f"  {count:4d}  {kind}   ({count / total:.0%})")

    rewrappable = sum(v for k, v in counts.items() if k.endswith("flowing prose"))
    print(f"\n  rewrappable by reflowing text:      {rewrappable}")
    print(f"  NOT rewrappable (structure/tokens): {total - rewrappable}")

    print("\nper file:")
    for name, kinds in sorted(per_file.items(), key=lambda kv: -sum(kv[1].values())):
        detail = ", ".join(f"{k.split(': ')[-1]} {v}" for k, v in kinds.most_common())
        print(f"  {sum(kinds.values()):4d}  {name}  [{detail}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
