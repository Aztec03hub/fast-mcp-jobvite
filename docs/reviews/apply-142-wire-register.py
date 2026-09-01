#!/usr/bin/env python3
"""Wire the three exemption consumers onto the register (#142).

Replayable, and every anchor is asserted UNIQUE and PRESENT
before it is replaced - a `str.replace` that matches nothing
succeeds silently and the gate then passes for a reason
unrelated to the change.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

EDITS: list[tuple[str, str, str]] = [
    # ---- check-design-citations.py ------------------------
    (
        "docs/reviews/check-design-citations.py",
        "import difflib\nimport pathlib\nimport re\nimport subprocess\nimport sys\n",
        "import difflib\nimport pathlib\nimport re\nimport subprocess\nimport sys\n"
        "\nimport repoint_exempt\n",
    ),
    (
        "docs/reviews/check-design-citations.py",
        'EXEMPT_MARKER = "REPOINT-EXEMPT"\nEXEMPT_SKIPPED = 0\n',
        "EXEMPT_MARKER = repoint_exempt.MARKER\n"
        "#: CITATIONS skipped, not LINES. #142 changed the unit deliberately:\n"
        "#: the old line count reported 51 while 36 of those lines carried no\n"
        "#: citation at all, so the number that was supposed to make the\n"
        "#: exemption visible was mostly counting prose about the exemption.\n"
        "EXEMPT_SKIPPED = 0\n",
    ),
    (
        "docs/reviews/check-design-citations.py",
        """        for lineno, line in enumerate(text.splitlines(), start=1):
            if EXEMPT_MARKER in line:
                EXEMPT_SKIPPED += 1
                continue
            for m in _CITATION.finditer(line):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                found.append((path, lineno, start, end))
""",
        """        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in _CITATION.finditer(line):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                # #142: the marker selects the LINE and the register
                # grants the CITATION. Neither alone is an exemption,
                # and anything else on the line stays in the
                # population - which is the granularity half of R13-H1.
                if repoint_exempt.is_exempt(line, rel, start, end):
                    EXEMPT_SKIPPED += 1
                    continue
                found.append((path, lineno, start, end))
""",
    ),
    (
        "docs/reviews/check-design-citations.py",
        '    print(f"  lines skipped as {EXEMPT_MARKER}: {EXEMPT_SKIPPED}")\n',
        '    print(f"  citations exempt (marked AND registered): {EXEMPT_SKIPPED}")\n'
        "    print(repoint_exempt.report())\n",
    ),
    # ---- check-design-citation-shape.py -------------------
    (
        "docs/reviews/check-design-citation-shape.py",
        "import re\nimport subprocess\nimport sys\n",
        "import re\nimport subprocess\nimport sys\n\nimport repoint_exempt\n",
    ),
    (
        "docs/reviews/check-design-citation-shape.py",
        '#: Split so this line is not itself exempt.\nEXEMPT = "REPOINT" + "-EXEMPT"\n',
        "#: Necessary, not sufficient, since #142: the marker selects the line\n"
        "#: and docs/reviews/REPOINT-EXEMPT.txt grants the citation.\n"
        "EXEMPT = repoint_exempt.MARKER\n",
    ),
    (
        "docs/reviews/check-design-citation-shape.py",
        """    for path in paths:
        body_lines = path.read_text(errors="replace").splitlines()
        for num, text in enumerate(body_lines, 1):
            # The marker `repoint-design-citations.py` already
            # honours: a line that RECORDS where a defect was must
            # not be repointed, and must not be reported as one
            # either. Kept narrow - it skips the line, not the file.
            if EXEMPT in text:
                exempted += 1
                continue
            for match in CITE.finditer(text):
                seen += 1
                start = int(match.group(1))
                end = int(match.group(2) or match.group(1))
                where = f"{path.relative_to(ROOT)}:{num}  {match.group(0)}"
                verdict = classify(start, end, lines)
                if verdict is not None:
                    findings[verdict].append(where)
""",
        """    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        body_lines = path.read_text(errors="replace").splitlines()
        for num, text in enumerate(body_lines, 1):
            for match in CITE.finditer(text):
                start = int(match.group(1))
                end = int(match.group(2) or match.group(1))
                # #142. A line that RECORDS where a defect was must not
                # be repointed and must not be reported - but it must
                # say WHICH citation it is recording, in the register,
                # or the marker exempts whatever else lands on the line.
                # Kept narrow: it skips the CITATION, not the line.
                if repoint_exempt.is_exempt(text, rel, start, end):
                    exempted += 1
                    continue
                seen += 1
                where = f"{path.relative_to(ROOT)}:{num}  {match.group(0)}"
                verdict = classify(start, end, lines)
                if verdict is not None:
                    findings[verdict].append(where)
""",
    ),
    (
        "docs/reviews/check-design-citation-shape.py",
        '    print(f"{exempted} line(s) skipped as {EXEMPT}.\\n")\n',
        '    print(f"{exempted} citation(s) exempt (marked AND registered).")\n'
        "    print(repoint_exempt.report() + chr(10))\n",
    ),
    # ---- repoint-design-citations.py ----------------------
    (
        "docs/reviews/repoint-design-citations.py",
        """        if "REPOINT-EXEMPT" in cited_line:
            continue
        old_s = int(m["os"])
        old_e = int(m["oe"]) if m["oe"] else old_s
""",
        """        old_s = int(m["os"])
        old_e = int(m["oe"]) if m["oe"] else old_s
        # #142. This test USED to be `"REPOINT-EXEMPT" in cited_line`,
        # at LINE granularity. That was unreachable belt-and-braces
        # while the checker skipped the whole line before emitting a
        # MOVED row for it - and it becomes a live over-suppression the
        # moment the checker skips only the exempt CITATION: a line
        # with one registered citation and one ordinary one would emit
        # a MOVED row that this test then silently refused to apply.
        if repoint_exempt.is_exempt(cited_line, m["file"], old_s, old_e):
            continue
""",
    ),
    (
        "docs/reviews/repoint-design-citations.py",
        "import pathlib\nimport re\nimport subprocess\nimport sys\n",
        "import pathlib\nimport re\nimport subprocess\nimport sys\n"
        "\nimport repoint_exempt\n",
    ),
    # ---- check-checkers-are-wired.py -----------------------
    #
    # NOT part of wiring the register - a defect the register's
    # sibling import EXPOSED. `third_party_imports` docstring says
    # "Local-only names are excluded"; the code excluded nothing but
    # the stdlib, so `import repoint_exempt` read as a missing PyPI
    # package and turned the gate red. A bare `python3
    # docs/reviews/check-x.py` puts that directory on sys.path[0] and
    # DOES find a sibling. Same class as R13-H1: a docstring
    # describing a check nobody wrote.
    (
        "docs/reviews/check-checkers-are-wired.py",
        """    return sorted(
        mod
        for mod in found
        if mod not in sys.stdlib_module_names and mod != "__future__"
    )
""",
        """    local = {p.stem for p in path.parent.glob("*.py")}
    return sorted(
        mod
        for mod in found
        if mod not in sys.stdlib_module_names
        and mod != "__future__"
        and mod not in local
    )
""",
    ),
]


def main() -> int:
    for rel, old, new in EDITS:
        path = ROOT / rel
        text = path.read_text()
        # ASK WHETHER THE RESULT IS PRESENT, never whether the anchor
        # is gone. Every import edit here APPENDS to its anchor, so the
        # anchor survives its own application - a first version of this
        # guard tested `old not in text` and cheerfully applied all
        # three import edits twice.
        if new in text:
            print(f"  already applied: {rel}")
            continue
        count = text.count(old)
        if count != 1:
            print(f"ANCHOR NOT UNIQUE in {rel}: found {count} time(s), need 1")
            print(f"  {old.splitlines()[0][:70]!r}")
            return 1
        path.write_text(text.replace(old, new))
        was, now = len(old.splitlines()), len(new.splitlines())
        print(f"  applied: {rel}  ({was} -> {now} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
