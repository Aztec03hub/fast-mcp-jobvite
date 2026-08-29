#!/usr/bin/env python3
"""Flag a `Settings` field that NOTHING outside `config.py` reads.

    python3 docs/reviews/check-settings-are-read.py

**This exists because the question it asks has produced two findings in one
day and no gate here asked it.** `DESIGN.md:373-375` promised a total
outbound budget and nothing implemented one until U7. `DESIGN.md:1576-1581`
specifies a self-throttle and **`outbound_rate_limit` is still read by
nothing** - it is declared, typed, defaulted, documented in `.env.example`
and covered by config tests, every one of which passes on a setting no
code consumes.

**A declared-and-unread setting is worse than a missing one.** A missing
setting fails loudly at the first attempt to use it. A declared one ships
in `.env.example`, an operator sets it, and it silently does nothing - and
`server.json` advertises it to registry consumers as a knob that works.

**THE RULE IS "READ ANYWHERE BUT ITS OWN DECLARATION", AND MY FIRST
VERSION HAD IT WRONG.** I began with "read outside `config.py`", which
reported FIVE findings - and four were false. `tls_terminated_by_proxy`
and `http_tokens` are consumed by `validate_settings` in `config.py`
itself: refusing to boot IS their behaviour, and no other module needs
to see them. `feed_key`, `feed_secret` and `enable_writes` appear in
`TOOL_REQUIREMENTS`, which is how a deployment is refused for missing
them. A rule that called those unread would have landed a knowingly red
gate on four false positives, which is the failure this project has
refused four times.

**WHAT THIS STILL CANNOT DO.** It proves a NAME is referenced in code,
not that the value changes behaviour. A field read into a variable that
is never used passes here. That is the same "resolves is not correct"
gap the citation checkers have, said out loud rather than discovered
later.

Fields may be exempted with a reason in `EXEMPT`, and an exemption without
a reason is refused - which is the shape `.file-type-allowlist` already
uses for the committed-file-type gate.
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONFIG = ROOT / "src" / "fast_mcp_jobvite" / "config.py"

#: Fields that are deliberately not read by `src/`, each with the reason a
#: reader needs. A bare name is refused: the reason IS the exemption.
EXEMPT: dict[str, str] = {
    "outbound_rate_limit": (
        "ADR-0025 (Proposed): the self-throttle does not exist yet, and the "
        "page size, budget and throttle have to be settled together. This "
        "entry is the record that it is KNOWN unread, not that it is fine."
    ),
}


def settings_fields() -> dict[str, int]:
    """Every annotated `Settings` field, mapped to its declaration line."""
    tree = ast.parse(CONFIG.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Settings":
            return {
                stmt.target.id: stmt.lineno
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and not stmt.target.id.startswith("_")
            }
    message = "no `Settings` class in config.py - the selector is broken"
    raise SystemExit(message)


def _code_lines(path: pathlib.Path) -> list[str]:
    """`path`'s lines with comments stripped.

    A COMMENT MENTIONING THE NAME IS NOT A READ, and that is exactly why
    the `outbound_rate_limit` gap was invisible: `jobvite_client.py`
    names it once, in a comment, to say what it is NOT.
    """
    return [line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()]


def references(field: str, declaration_line: int) -> list[str]:
    """Every code reference to `field` that is not its own declaration."""
    hits = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        for num, code in enumerate(_code_lines(path), 1):
            if path == CONFIG and num == declaration_line:
                continue
            if field in code:
                hits.append(f"{path.relative_to(ROOT)}:{num}")
    return hits


def main() -> int:
    fields = settings_fields()
    if not fields:
        print("PARSED ZERO FIELDS. A green here would mean nothing.")
        return 1

    unread = {f: references(f, line) for f, line in fields.items()}
    unread = {f: h for f, h in unread.items() if not h}

    print(f"`Settings` fields: {len(fields)}")
    print(f"Referenced in src/ outside their own declaration: {len(fields) - len(unread)}")

    bad = [f for f in unread if f not in EXEMPT]
    stale = [f for f in EXEMPT if f not in unread]

    for field in sorted(unread):
        if field in EXEMPT:
            print(f"  EXEMPT   {field}\n           {EXEMPT[field]}")
        else:
            print(f"  UNREAD   {field} - declared, defaulted, and consumed by nothing")

    for field in sorted(stale):
        print(f"  STALE EXEMPTION  {field} is read now; drop its EXEMPT entry")

    if bad or stale:
        print(f"\n{len(bad)} unread field(s), {len(stale)} stale exemption(s).")
        print("A declared-and-unread setting ships in .env.example and does nothing.")
        return 1

    print("\nEvery Settings field is referenced somewhere but its own declaration,")
    print("or exempt with a reason. NOTE: this proves the NAME is referenced, not")
    print("that the value changes behaviour - a field read into an unused variable")
    print("passes here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
