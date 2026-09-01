#!/usr/bin/env python3
"""Flag a `Settings` field that NOTHING outside `config.py` reads.

    python3 docs/reviews/check-settings-are-read.py

**This exists because the question it asks has produced two findings in
one day and no gate here asked it.** §4.3's "a total outbound budget,
configured" was promised and nothing implemented one until U7.
§10.1's variable list specifies a self-throttle and
**`outbound_rate_limit` is still read by nothing** - it is declared,
typed, defaulted, documented in `.env.example` and covered by config
tests, every one of which passes on a setting no code consumes.

**THE `STALE EXEMPTION` ARM IS THE TRIPWIRE FOR THAT ONE.** DESIGN.md
§4.4 now carries rules for a throttle nobody has built, which is the
same shape as a setting nothing reads unless something makes the
implementer read them. The moment `outbound_rate_limit` gains a reader
it leaves the unread set, its exemption goes STALE, and this exits 1
pointing at §4.4. Verified by planting a reader: the arm fires.

**A declared-and-unread setting is worse than a missing one.** A missing
setting fails loudly at the first attempt to use it. A declared one
ships in `.env.example`, an operator sets it, and it silently does
nothing - and `server.json` advertises it to registry consumers as a
knob that works.

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

Fields may be exempted with a reason in `EXEMPT`, and an exemption
without a reason is refused - which is the shape `.file-type-allowlist`
already uses for the committed-file-type gate.
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONFIG = ROOT / "src" / "fast_mcp_jobvite" / "config.py"

#: Fields that are deliberately not read by `src/`, each with the reason
#: a reader needs. A bare name is refused: the reason IS the exemption.
EXEMPT: dict[str, str] = {
    "outbound_rate_limit": (
        "ADR-0025 (ACCEPTED, applied): the self-throttle does not exist "
        "yet. This entry records that it is KNOWN unread, not that it is "
        "fine. WHOEVER GIVES IT ITS FIRST READER: the STALE EXEMPTION arm "
        "below fires on you, and that is deliberate - read DESIGN.md "
        "§4.4's throttle rules FIRST. They are written to constrain the "
        "implementer and say in bold that the throttle is not built: it "
        "is PER-PROCESS, and time spent waiting on it SPENDS §4.3's "
        "outbound budget. Drop this entry in the same commit that "
        "implements them, not before."
    ),
}

#: **THE OPERATOR-FACING HALF, AND IT IS SYMMETRIC** (R11-M2). An
#: exemption above is a note between maintainers; `README.md` and
#: `.env.example` are what the person deploying this reads, and both
#: described `JOBVITE_OUTBOUND_RATE_LIMIT` as a working control while
#: `EXEMPT` recorded that nothing reads it. Someone who set it to 1
#: because they were worried about their tenant got no protection and
#: no signal - switched-off and working rendered identically.
#:
#: So an exempt-as-unimplemented field owes a marker in every artefact
#: below, and the rule runs BOTH WAYS: while the field is unread the
#: marker must be PRESENT, and the moment it gains a reader the marker
#: must be GONE. **The second direction is the one that matters.**
#: Without it the throttle ships and these two files keep telling
#: operators it does not work - the same defect pointing the other way,
#: which is exactly how the first one survived a split review.
#:
#: The variable name and the marker must share a LINE, so this cannot
#: pass on a sentence about something else that happens to contain the
#: phrase.
UNIMPLEMENTED_MARKER: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "outbound_rate_limit": (
        "JOBVITE_OUTBOUND_RATE_LIMIT",
        "NOT YET IMPLEMENTED",
        ("README.md", ".env.example"),
    ),
}


def marker_lines(variable: str, marker: str, name: str) -> list[int]:
    """Lines of `name` carrying BOTH `variable` and `marker`.

    Refuses a path that does not resolve rather than reporting zero
    hits: a search at a missing file exits clean-empty, which is
    indistinguishable from a real absence and would make the
    "marker present" arm pass by never looking.
    """
    path = ROOT / name
    if not path.is_file():
        message = f"{name} does not exist, so this check would pass vacuously"
        raise SystemExit(message)
    body = path.read_text(encoding="utf-8").splitlines()
    return [n for n, line in enumerate(body, 1) if variable in line and marker in line]


def settings_fields() -> dict[str, int]:
    """Every annotated `Settings` field, mapped to its own line."""
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
    body = path.read_text(encoding="utf-8").splitlines()
    return [line.split("#", 1)[0] for line in body]


def references(field: str, declaration_line: int) -> list[str]:
    """Every reference to `field` that is not its declaration."""
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
    print(
        f"Referenced in src/ outside their own declaration: "
        f"{len(fields) - len(unread)}",
    )

    bad = [f for f in unread if f not in EXEMPT]
    stale = [f for f in EXEMPT if f not in unread]

    # The operator-facing half (R11-M2), in both directions.
    missing: list[str] = []
    lingering: list[str] = []
    for field, (variable, marker, artefacts) in UNIMPLEMENTED_MARKER.items():
        for name in artefacts:
            found = marker_lines(variable, marker, name)
            if field in unread and not found:
                missing.append(
                    f"{name} does not say {variable} is {marker!r}, but nothing "
                    "reads it - an operator setting it gets no protection and "
                    "no signal"
                )
            if field not in unread and found:
                lingering.append(
                    f"{name}:{found[0]} still says {variable} is {marker!r}, but "
                    "it has a reader now - the marker is the stale half"
                )

    for field in sorted(unread):
        if field in EXEMPT:
            print(f"  EXEMPT   {field}\n           {EXEMPT[field]}")
        else:
            print(f"  UNREAD   {field} - declared, defaulted, and consumed by nothing")

    for field in sorted(stale):
        print(f"  STALE EXEMPTION  {field} is read now; drop its EXEMPT entry")

    for problem in missing + lingering:
        print(f"  MARKER   {problem}")

    if bad or stale or missing or lingering:
        print(
            f"\n{len(bad)} unread field(s), {len(stale)} stale exemption(s), "
            f"{len(missing) + len(lingering)} marker problem(s)."
        )
        print("A declared-and-unread setting ships in .env.example and does nothing.")
        return 1

    print(
        "Unimplemented-marker artefacts checked: "
        f"{sum(len(v[2]) for v in UNIMPLEMENTED_MARKER.values())}"
    )
    print("\nEvery Settings field is referenced somewhere but its own declaration,")
    print("or exempt with a reason. NOTE: this proves the NAME is referenced, not")
    print("that the value changes behaviour - a field read into an unused variable")
    print("passes here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
