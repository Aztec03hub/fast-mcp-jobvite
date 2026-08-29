#!/usr/bin/env python3
"""Shorten over-long docstring summary lines without losing a sentence.

D205 forbids wrapping a summary, so an over-long one is fixed by moving
its later sentences down into the docstring body. Lines whose FIRST
sentence still exceeds the limit are reported, not touched.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess

LIMIT = 72
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*_\"'§(])")


def protect(text: str, budget: int) -> str:
    """Make short `code spans` unbreakable, so a wrap cannot split."""
    def swap(match: re.Match[str]) -> str:
        span = match.group(0)
        return span.replace(" ", "\x00") if len(span) <= budget else span

    return re.sub(r"`[^`\n]*`", swap, text)


def summary_rows(path: pathlib.Path) -> list[int]:
    tree = ast.parse(path.read_text())
    rows = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            rows.append(body[0].lineno)
    return rows


def split_one(lines: list[str], row: int) -> list[str] | None:
    """Rewrite the docstring starting at `row` so its summary fits."""
    line = lines[row - 1].rstrip()
    if len(line) <= LIMIT:
        return None
    indent = line[: len(line) - len(line.lstrip())]
    stripped = line.strip()
    quote = stripped[:3]
    if quote not in ('"""', "'''"):
        return None

    one_line = stripped.endswith(quote) and len(stripped) > 6
    text = stripped[3:]
    if one_line:
        text = text[:-3]
    text = text.strip()

    parts = SENT.split(text)
    if len(parts) < 2:
        return None
    head, tail = parts[0], " ".join(parts[1:])
    if len(indent) + 3 + len(head) > LIMIT:
        return None

    out = [f"{indent}{quote}{head}", ""]
    out.extend(wrap(tail, indent))
    if one_line:
        out.append(f"{indent}{quote}")
        return out
    # Multi-line docstring: keep everything that followed the summary.
    return out


def wrap(text: str, indent: str) -> list[str]:
    import textwrap

    out = textwrap.wrap(
        protect(text, LIMIT - len(indent) - 2),
        width=LIMIT,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [line.replace("\x00", " ") for line in out]


def process(path: pathlib.Path) -> tuple[int, list[int]]:
    source = path.read_text()
    lines = source.splitlines()
    fixed = 0
    stuck = []
    for row in sorted(summary_rows(path), reverse=True):
        line = lines[row - 1].rstrip()
        if len(line) <= LIMIT:
            continue
        new = split_one(lines, row)
        if new is None:
            stuck.append(row)
            continue
        stripped = line.strip()
        quote = stripped[:3]
        one_line = stripped.endswith(quote) and len(stripped) > 6
        if one_line:
            lines[row - 1 : row] = new
        else:
            # Insert head + blank + carried tail, then a blank before
            # the original body only if the next line is not already
            # blank.
            follow = lines[row : row + 1]
            block = list(new)
            if follow and follow[0].strip():
                block.append("")
            lines[row - 1 : row] = block
        fixed += 1
    candidate = "\n".join(lines) + "\n"
    try:
        ast.parse(candidate)
    except SyntaxError as exc:
        print(f"SKIP {path}: {exc}")
        return 0, stuck
    if candidate != source:
        path.write_text(candidate)
    return fixed, stuck


def main() -> int:
    proc = subprocess.run(
        [
            "uv", "run", "--frozen", "ruff", "check", ".",
            "--select", "W505",
            "--config", "lint.pycodestyle.max-doc-length = 72",
            "--output-format", "concise",
        ],
        capture_output=True, text=True,
    )
    files = sorted({
        line.split(":")[0] for line in proc.stdout.splitlines() if "W505" in line
    })
    total = 0
    remaining: list[str] = []
    for name in files:
        path = pathlib.Path(name)
        fixed, stuck = process(path)
        total += fixed
        remaining.extend(f"{name}:{r}" for r in sorted(stuck))
    print(f"split {total} summaries; {len(remaining)} need hand-shortening")
    for item in remaining:
        print("  ", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
