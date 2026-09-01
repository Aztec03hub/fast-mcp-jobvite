import pathlib, sys

def edit(path, pairs, expect_each=1):
    p = pathlib.Path(path); t = p.read_text(); orig = t
    for old, new in pairs:
        n = t.count(old)
        if n != expect_each:
            sys.exit(f"ANCHOR FAIL {path}: {n} occurrences of {old!r}, expected {expect_each}")
        t = t.replace(old, new)
    assert t != orig
    p.write_text(t)
    print(f"edited {path}")

# --- A. FASTMCP.md: the [SPIKE §n] shorthand names no file, and 8 of its 23
# references silently resolve against FASTMCP.md's OWN headings instead.
f = pathlib.Path("docs/research/FASTMCP.md"); t = f.read_text()
n = t.count("[SPIKE §")
assert n == 23, n
t = t.replace("[SPIKE §", "[FASTMCP-SPIKE-4.md §")
old_legend = ("Claims marked **[SPIKE]** were executed — see\n"
              "[`FASTMCP-SPIKE-4.md`](FASTMCP-SPIKE-4.md) for the evidence.")
new_legend = ("Claims marked **[SPIKE]** were executed; a\n"
              "**[FASTMCP-SPIKE-4.md §n]** tag names the section of\n"
              "[`FASTMCP-SPIKE-4.md`](FASTMCP-SPIKE-4.md) holding the evidence. The section number\n"
              "belongs to THAT document, never to this one - both files number their sections from\n"
              "1, so a bare `§7` here would read as this document's §7 and point at the wrong text.")
assert t.count(old_legend) == 1
t = t.replace(old_legend, new_legend)
f.write_text(t); print(f"edited docs/research/FASTMCP.md ({n} tags)")

# --- B. ADR-0022: all four §2.3 cite JOBVITE-CONTRACT.md §2.3 "Response headers".
edit("docs/adr/0022-no-cookie-jar-is-a-disable-not-an-omission.md", [
    ("correctly follows §2.3 as written ships a client",
     "correctly follows `JOBVITE-CONTRACT.md` §2.3 as written ships a client"),
    ("does, and §2.3 says there is no session to carry",
     "does, and `JOBVITE-CONTRACT.md` §2.3 says there is no session to carry"),
    ("- **Anything about the other four response headers** §2.3 records",
     "- **Anything about the other four response headers** `JOBVITE-CONTRACT.md` §2.3 records"),
    ("- **The rate-limit finding in the same section.** §2.3's \"there is no rate-limit",
     "- **The rate-limit finding in the same section.** `JOBVITE-CONTRACT.md` §2.3's \"there is no rate-limit"),
])

# --- C. JOBVITE-CONTRACT.md: §13 is a TABLE OF ROWS, not subsections. §13.1
# means row 1 of §13 and there is no heading it can ever resolve to.
edit("docs/research/JOBVITE-CONTRACT.md", [
    ("Checklist row §13.1 settles it.", "Checklist §13 row 1 settles it."),
    ("Checklist row §13.4.", "Checklist §13 row 4."),
    ("Gate on checklist row §13.2 before", "Gate on checklist §13 row 2 before"),
])

# --- D. ADR-0019: the line number is 603 at the blob the ADR itself names
# (`git show 135c3ac:docs/DESIGN.md` -> :603). Three sites said 605.
edit("docs/adr/0019-design-603-cites-a-section-that-does-not-exist.md", [
    ("# ADR-0019: `DESIGN.md:605` cites `§5.4`, and there is no §5.4",
     "# ADR-0019: `DESIGN.md:603` cites `§5.4`, and there is no §5.4"),
    ("Found by **building U3**, not by reading. `DESIGN.md:605` reads:",
     "Found by **building U3**, not by reading. `DESIGN.md:603` reads:"),
    ("**`DESIGN.md:605`'s `(§5.4)` becomes `(§4.1)`.**",
     "**`DESIGN.md:603`'s `(§5.4)` becomes `(§4.1)`.**"),
    ("  the claim `:603` attributes to `§5.4`.",
     "  the claim `DESIGN.md:603` attributes to `§5.4`."),
])

# --- E. ADR-0017: "RFC 9457 §4.2.1" split across a blockquote wrap, so the
# line carrying the reference names neither a document nor the RFC.
edit("docs/adr/0017-unmapped-errors-are-internal-error-not-about-blank.md", [
    ("> *\"**`about:blank` fallback**: For unmapped **HTTP** errors, use `about:blank` as the type (per RFC\n> 9457 §4.2.1)\"*",
     "> *\"**`about:blank` fallback**: For unmapped **HTTP** errors, use `about:blank` as the type\n> (per RFC 9457 §4.2.1)\"*"),
])
