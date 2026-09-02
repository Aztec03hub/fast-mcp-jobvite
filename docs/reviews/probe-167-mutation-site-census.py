#!/usr/bin/env python3
"""Census of Python-heredoc mutation sites in every harness.

WHY THIS EXISTS. `scripts/check-harness-anchors.py` reports how many
anchors it RESOLVED. That number is a sample from a container nobody had
measured, and a sample cannot report the size of what it was drawn from:
its own `--self-check` tally counts only the sites its own selectors
already matched, so a shape no selector reads contributes zero to BOTH
sides of the comparison and the completeness check comes out clean.

This probe measures the container INDEPENDENTLY. It deliberately does
not import or reuse the checker: it parses every quoted heredoc in every
`check-*.sh` with `ast` and classifies every expression that produces a
mutated copy of the source text, by KIND. The checker's coverage is then
the intersection, and the difference is the blind spot.

It is a MEASUREMENT, not a gate: it always exits 0 unless it cannot
parse something, which is a defect in the probe and is reported as
exit 2. Nothing in CI depends on it.

Usage:
  uv run --frozen python \
    docs/reviews/probe-167-mutation-site-census.py
"""

from __future__ import annotations

import ast
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# The same heredoc form the checker reads, deliberately: if the
# harnesses ever used an unquoted delimiter this probe would
# under-report too, and that is stated here rather than found later.
HEREDOC_RE = re.compile(
    r"<<'(?P<tag>[A-Za-z_][A-Za-z0-9_]*)'\n(?P<body>.*?)\n(?P=tag)\n", re.S
)

# The literal test `check-harness-anchors.py` applies to a heredoc BODY
# before it will even parse it (`_shape_b`). A body failing this test is
# skipped whole - every site in it, of every kind.
CHECKER_BODY_GATE = (".replace(", "re.sub(")

# `python3 - "<path>"` on the line that OPENS the heredoc: the mark of a
# heredoc that is Python source rather than a `@@` spec table. The
# checker does not test this - it decides on the body gate alone, so a
# spec row whose OLD text happened to contain `.replace(` would be fed
# to `ast.parse` and reported as a parser gap. This probe tests it,
# which is why the population below is heredocs that ARE Python.
PY_INVOKE_RE = re.compile(r'python3\s+-\s+"(?P<path>[^"]+)"')


def _top_level_add_chains(tree: ast.AST) -> list[ast.BinOp]:
    """Every `+` chain that is not itself an operand of another `+`."""
    inner: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            for side in (node.left, node.right):
                if isinstance(side, ast.BinOp) and isinstance(side.op, ast.Add):
                    inner.add(id(side))
    return [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and id(n) not in inner
    ]


def classify(body: str) -> Counter[str]:
    """Count the mutation-producing expressions in one heredoc body."""
    kinds: Counter[str] = Counter()
    tree = ast.parse(body)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr == "replace":
                kinds["str.replace"] += 1
            elif (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
                and attr in ("sub", "subn")
            ):
                kinds[f"re.{attr}"] += 1
    # An index-and-slice splice: `s[:i] + NEW + s[j:]`. It is a mutation
    # with an anchor - the anchor is whatever `i` and `j` were computed
    # from - but it is not a call, so no call-shaped selector sees it.
    for chain in _top_level_add_chains(tree):
        if any(
            isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Slice)
            for n in ast.walk(chain)
        ):
            kinds["slice-splice"] += 1
    return kinds


def main() -> int:
    harnesses = [
        h
        for h in sorted(SCRIPTS.glob("check-*.sh"))
        if not h.name.startswith("check-harness-anchors")
    ]
    if not harnesses:
        print(f"ERROR: no harnesses under {SCRIPTS}")
        return 2

    total: Counter[str] = Counter()
    inside_gate: Counter[str] = Counter()
    gate_skipped: list[tuple[str, int, dict[str, int]]] = []
    per_harness: list[tuple[str, int, bool, dict[str, int]]] = []

    for h in harnesses:
        src = h.read_text()
        for m in HEREDOC_RE.finditer(src):
            body = m.group("body")
            line = src.count("\n", 0, m.start()) + 1
            head = src[: m.start()].rsplit("\n", 1)[-1]
            if PY_INVOKE_RE.search(head) is None:
                continue  # a `@@` spec table or a plain data heredoc
            opened = any(tok in body for tok in CHECKER_BODY_GATE)
            try:
                kinds = classify(body)
            except SyntaxError as exc:
                print(f"PROBE GAP: {h.name}:{line} does not parse: {exc}")
                return 2
            if not kinds:
                continue
            per_harness.append((h.name, line, opened, dict(kinds)))
            for k, v in kinds.items():
                total[k] += v
                if opened:
                    inside_gate[k] += v
            if not opened:
                gate_skipped.append((h.name, line, dict(kinds)))

    print(f"harnesses scanned: {len(harnesses)}")
    print("mutation sites in python heredocs, by KIND:")
    for k in sorted(total):
        print(
            f"  {k:14s} total={total[k]:4d}"
            f"   in a heredoc the checker opens={inside_gate[k]:4d}"
        )
    print()
    print("heredocs the checker's body gate skips WHOLE, though they mutate:")
    for name, line, skipped_kinds in gate_skipped:
        print(f"  {name}:{line}  {skipped_kinds}")
    if not gate_skipped:
        print("  (none)")
    print()
    print("per heredoc:")
    for name, line, opened, seen_kinds in per_harness:
        print(f"  {name}:{line:4d}  checker_opens={str(opened):5s}  {seen_kinds}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
