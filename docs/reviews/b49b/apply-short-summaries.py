#!/usr/bin/env python3
"""Apply the hand-authored short summaries from /tmp/summaries.tsv.

Every anchor is checked before it is written: the target line must still
be the opening line of a docstring and must still be over the limit.
"""

from __future__ import annotations

import ast
import collections
import json
import pathlib
import re
import textwrap

LIMIT = 72


def protect(text: str, budget: int) -> str:
    """Make short `code spans` unbreakable, so wrapping never splits one."""
    def swap(match: re.Match[str]) -> str:
        span = match.group(0)
        return span.replace(" ", "\x00") if len(span) <= budget else span

    return re.sub(r"`[^`\n]*`", swap, text)

ROWS = json.loads(
    pathlib.Path("docs/reviews/b49b/short-summaries.json").read_text()
)


def summary_rows(source: str) -> dict[str, int]:
    """qualname -> line number of the docstring that documents it."""
    out: dict[str, int] = {}

    def opener(node: ast.AST) -> int | None:
        body = getattr(node, "body", [])
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[0].lineno
        return None

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                name = f"{prefix}.{child.name}" if prefix else child.name
                row = opener(child)
                if row is not None:
                    assert name not in out, f"ambiguous qualname {name}"
                    out[name] = row
                walk(child, name)

    tree = ast.parse(source)
    row = opener(tree)
    if row is not None:
        out["<module>"] = row
    walk(tree, "")
    return out


by_file: dict[str, list[tuple[int, str, str]]] = collections.defaultdict(list)
for row in ROWS:
    by_file[row["path"]].append((row["qualname"], row["summary"], row.get("body", "")))

applied = 0
for name, edits in by_file.items():
    path = pathlib.Path(name)
    source = path.read_text()
    lines = source.splitlines()
    anchors = summary_rows(source)
    resolved = []
    for qual, summary, body in edits:
        assert qual in anchors, f"{name}: {qual} has no docstring any more"
        resolved.append((anchors[qual], qual, summary, body))
    for lineno, qual, summary, body in sorted(resolved, reverse=True):
        old = lines[lineno - 1].rstrip()
        assert len(old) > LIMIT, f"{name}:{qual} is already short: {old!r}"
        indent = old[: len(old) - len(old.lstrip())]
        stripped = old.strip()
        quote = stripped[:3]
        assert quote in ('"""', "'''"), f"{name}:{qual} not triple-quoted"
        one_line = stripped.endswith(quote) and len(stripped) > 6

        if one_line and not body:
            new = [f"{indent}{quote}{summary}{quote}"]
        else:
            new = [f"{indent}{quote}{summary}"]
            if body:
                new.append("")
                new.extend(
                    textwrap.wrap(
                        protect(body, LIMIT - len(indent) - 2),
                        width=LIMIT,
                        initial_indent=indent,
                        subsequent_indent=indent,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
            if one_line:
                new.append(f"{indent}{quote}")
            elif lineno < len(lines) and lines[lineno].strip():
                new.append("")

        new = [line.replace("\x00", " ") for line in new]
        for produced in new:
            assert len(produced) <= LIMIT, f"{name}:{qual} still long: {produced!r}"
        lines[lineno - 1 : lineno] = new
        applied += 1

    candidate = "\n".join(lines) + "\n"
    ast.parse(candidate)
    path.write_text(candidate)

print(f"applied {applied} summaries across {len(by_file)} files")
