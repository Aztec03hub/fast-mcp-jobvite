#!/usr/bin/env python3
"""Reflow comments and docstrings to a 72-character doc line limit (B49b).

Structure-preserving: fenced blocks, tables, dividers, bullets, Google
sections and anything indented deeper than its paragraph are left alone.
Every file is `ast.parse`d before it is written.
"""

from __future__ import annotations

import ast
import io
import pathlib
import re
import sys
import textwrap
import tokenize

LIMIT = 72

BULLET = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
FIELD = re.compile(
    r"^\s*(Args|Arguments|Parameters|Returns|Yields|Raises|Attributes|"
    r"Note|Notes|Example|Examples|Warning|Warnings|Warns|See Also|Todo|"
    r"References):\s*$"
)
DIVIDER = re.compile(r"^(\s*)#\s*([-=~*_#])\2{5,}\s*$")
ARGITEM = re.compile(r"^(\s*)(\*{0,2}[A-Za-z_][A-Za-z0-9_]*)\s*:\s+\S")


def protect(text: str, budget: int) -> str:
    """Make short `code spans` unbreakable, so wrapping never splits one."""
    def swap(match: re.Match[str]) -> str:
        span = match.group(0)
        return span.replace(" ", "\x00") if len(span) <= budget else span

    return re.sub(r"`[^`\n]*`", swap, text)


def is_table(s: str) -> bool:
    return s.strip().startswith("|") and s.strip().count("|") >= 2


def is_fence(s: str) -> bool:
    return s.strip().startswith("```")


def wrap_paragraph(
    lines: list[str], indent: str, hang: str, width: int
) -> list[str]:
    """Join `lines` into one paragraph and re-wrap it under `indent`."""
    text = " ".join(line.strip() for line in lines)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return list(lines)
    text = protect(text, width - len(hang) - 2)
    out = textwrap.wrap(
        text,
        width=width,
        initial_indent=indent,
        subsequent_indent=hang,
        break_long_words=False,
        break_on_hyphens=False,
        drop_whitespace=True,
    )
    return [line.replace("\x00", " ") for line in out] or list(lines)


def reflow_block(lines: list[str], width: int = LIMIT) -> list[str]:
    """Reflow a run of plain text lines (already stripped of any `#`)."""
    out: list[str] = []
    para: list[str] = []
    para_indent = ""
    para_hang = ""
    in_fence = False
    section_indent: int | None = None

    def flush() -> None:
        nonlocal para, para_indent, para_hang
        if para:
            out.extend(wrap_paragraph(para, para_indent, para_hang, width))
            para = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if is_fence(line):
            flush()
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if not stripped:
            flush()
            out.append("")
            continue
        if is_table(line):
            flush()
            out.append(line)
            continue
        if FIELD.match(line):
            flush()
            section_indent = len(line) - len(line.lstrip())
            out.append(line)
            continue

        cur_indent = line[: len(line) - len(line.lstrip())]
        if section_indent is not None and len(cur_indent) <= section_indent:
            section_indent = None

        # Inside an Args:/Returns:/Raises: section, `name: description` starts
        # a new item; its continuations hang four further columns.
        if section_indent is not None:
            item = ARGITEM.match(line)
            if item:
                flush()
                para = [line]
                para_indent = cur_indent
                para_hang = cur_indent + "    "
                continue

        bullet = BULLET.match(line)

        if bullet:
            flush()
            para = [line]
            para_indent = cur_indent
            para_hang = cur_indent + " " * (len(bullet.group(0)) - len(cur_indent))
            continue

        if para:
            # A deeper-indented line is structure (code sample, continuation
            # of an indented listing); do not fold it into the paragraph.
            if cur_indent != para_hang and cur_indent != para_indent:
                flush()
                para = [line]
                para_indent = para_hang = cur_indent
            else:
                para.append(line)
            continue

        para = [line]
        para_indent = para_hang = cur_indent

    flush()
    while out and out[-1] == "":
        out.pop()
    return out


def reflow_comment_run(run: list[tuple[int, str]]) -> list[str] | None:
    """Reflow a run of full-line comments sharing one indent.

    `#:` IS PRESERVED AS A MARKER, not eaten as body text. It is the
    Sphinx attribute-documentation prefix and this project uses it for
    module-level constants. Stripping only the `#` left the `:` at the
    front of the content, so a rewrapped line came back as `# : text` -
    a marker turned into punctuation, and the continuation lines lost it
    entirely.

    MEASURED: valid `#:` markers in the tree went from 22 to 3 across the
    B49b sweep and the follow-up passes that used this tool. Nothing
    caught it - not ruff, not mypy, not the suite. It is the same shape
    as this tool's F-2 (inline code spans split across a wrap): a reflow
    quietly becoming a rewrite, invisible to every gate.

    A run that MIXES `#:` and `#` is refused rather than normalised.
    Guessing which the author meant is how a reflow turns into an edit.
    """
    indent = run[0][1][: len(run[0][1]) - len(run[0][1].lstrip())]
    marker = "#:" if run[0][1].strip().startswith("#:") else "#"

    body: list[str] = []
    for _, text in run:
        stripped = text.strip()
        if not stripped.startswith("#"):
            return None
        if (stripped.startswith("#:")) != (marker == "#:"):
            return None  # mixed run: leave it alone
        content = stripped[len(marker) :]
        if content.startswith(" "):
            content = content[1:]
        body.append(content)

    reflowed = reflow_block(body, width=LIMIT - len(indent) - len(marker) - 1)
    return [
        f"{indent}{marker}" if not b else f"{indent}{marker} {b}" for b in reflowed
    ]


def fix_dividers(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        m = DIVIDER.match(line)
        if m and len(line.rstrip()) > LIMIT:
            ind, ch = m.group(1), m.group(2)
            body = LIMIT - len(ind) - 2
            out.append(f"{ind}# {ch * body}")
        else:
            out.append(line)
    return out


def comment_runs(source: str) -> list[list[int]]:
    """Indices (0-based) of full-line comments, grouped into runs."""
    lines = source.splitlines()
    is_comment = [False] * len(lines)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            row = tok.start[0] - 1
            if lines[row][: tok.start[1]].strip() == "":
                is_comment[row] = True

    runs: list[list[int]] = []
    cur: list[int] = []
    for i, flag in enumerate(is_comment):
        if flag and not DIVIDER.match(lines[i]):
            same = not cur or (
                len(lines[i]) - len(lines[i].lstrip())
                == len(lines[cur[0]]) - len(lines[cur[0]].lstrip())
            )
            if same:
                cur.append(i)
                continue
            runs.append(cur)
            cur = [i]
        else:
            if cur:
                runs.append(cur)
                cur = []
    if cur:
        runs.append(cur)
    return runs


def docstring_nodes(source: str) -> list[ast.Expr]:
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = getattr(node, "body", [])
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            found.append(body[0])
    return found


def rebuild_docstring(raw_lines: list[str], indent: str) -> list[str]:
    """Reflow the interior of a triple-quoted docstring, quotes included."""
    first = raw_lines[0]
    open_q = first.strip()[:3]
    if open_q not in ('"""', "'''"):
        return raw_lines
    if len(raw_lines) == 1:
        return raw_lines

    last = raw_lines[-1]
    closing_alone = last.strip() == open_q

    summary = first.strip()[3:].rstrip()
    if summary.endswith(open_q):
        summary = summary[: -3].rstrip()

    interior = raw_lines[1:-1] if closing_alone else raw_lines[1:]
    if not closing_alone:
        tail = interior[-1].rstrip()
        if tail.endswith(open_q):
            interior = interior[:-1] + [tail[: -3].rstrip()]

    normalised = []
    for line in interior:
        if line.strip() and not line.startswith(indent):
            normalised.append(indent + line.strip())
        else:
            normalised.append(line.rstrip())

    body = reflow_block(normalised)

    out = [f"{indent}{open_q}{summary}" if summary else f"{indent}{open_q}"]
    out.extend(body)
    out.append(f"{indent}{open_q}")
    return out


def reflow_file(path: pathlib.Path) -> bool:
    source = path.read_text()
    original = source
    lines = source.splitlines()

    # 1. docstrings, bottom-up so line numbers stay valid
    for node in sorted(docstring_nodes(source), key=lambda n: n.lineno, reverse=True):
        start, end = node.lineno - 1, node.end_lineno - 1
        raw = lines[start : end + 1]
        indent = raw[0][: len(raw[0]) - len(raw[0].lstrip())]
        if max((len(x.rstrip()) for x in raw), default=0) <= LIMIT:
            continue
        new = rebuild_docstring(raw, indent)
        lines[start : end + 1] = new

    source = "\n".join(lines) + "\n"
    try:
        ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover - guard
        print(f"SKIP {path}: docstring pass broke syntax: {exc}")
        return False

    # 2. dividers
    lines = fix_dividers(source.splitlines())
    source = "\n".join(lines) + "\n"

    # 3. comment runs, bottom-up
    for run in sorted(comment_runs(source), key=lambda r: r[0], reverse=True):
        lines = source.splitlines()
        block = [(i, lines[i]) for i in run]
        if max(len(t.rstrip()) for _, t in block) <= LIMIT:
            continue
        new = reflow_comment_run(block)
        if new is None:
            continue
        lines[run[0] : run[-1] + 1] = new
        candidate = "\n".join(lines) + "\n"
        try:
            ast.parse(candidate)
        except SyntaxError as exc:  # pragma: no cover - guard
            print(f"SKIP {path}:{run[0] + 1} comment run: {exc}")
            continue
        source = candidate

    if source == original:
        return False
    ast.parse(source)
    path.write_text(source)
    return True


def main() -> int:
    targets = [pathlib.Path(a) for a in sys.argv[1:]]
    changed = 0
    for path in targets:
        if reflow_file(path):
            changed += 1
    print(f"rewrote {changed} of {len(targets)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
