#!/usr/bin/env python3
"""Mechanically check DESIGN.md section 11's threat model against itself and against section 8.

Why this exists: the coupling claim in section 11 ("every mitigated Critical or High row has a
required test in section 8") was hand-checked and wrong on three consecutive review rounds, and
the disposition tables silently dropped six rows that had been added to the analysis. Both are
checkable properties of the document. This script checks them.

Checks, in order:
  1. Every STRIDE row id is unique and matches C<n>-<STRIDE letter><k>.
  2. Every component covers all six STRIDE categories.
  3. Every mitigated Critical or High row names a section 8 case in its Test column, and the named
     case text appears verbatim in section 8's required-cases list.
  4. Every Critical or High row that is NOT mitigated appears either in the must-mitigate table or
     in Residual Risks.
  5. Every row id referenced anywhere in section 11 outside the STRIDE tables is defined by them.
  6. The "Already mitigated at Critical or High" roster matches the set the tables imply, exactly.

Usage: python3 docs/reviews/check-coupling.py [path/to/DESIGN.md]
Exit code 0 on success, 1 on any failure. No dependencies.
"""

from __future__ import annotations

import pathlib
import re
import sys

ID_RE = re.compile(r"^C(\d+)-([STRIDE])(\d+)$")
REF_RE = re.compile(r"\bC\d+-[STRIDE]\d*\b")
CATEGORIES = ["S", "T", "R", "I", "D", "E"]


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def slice_section(text: str, start: str, end: str | None) -> str:
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


def main(path: pathlib.Path) -> int:
    text = path.read_text()
    s8 = slice_section(text, "\n## 8. Testing", "\n## 9.")
    s11 = slice_section(text, "\n## 11. Threat model", "\n## 12.")

    stride = slice_section(s11, "\n### STRIDE Analysis", "\n### Threshold disposition")
    closing = s11[s11.index("\n### Threshold disposition"):]

    failures: list[str] = []
    rows: dict[str, dict[str, str]] = {}

    for line in stride.splitlines():
        if not line.startswith("| C"):
            continue
        c = cells(line)
        if len(c) != 7:
            failures.append(f"row has {len(c)} columns, expected 7: {c[0]!r}")
            continue
        rid, threat, risk, mitigation, test = c[0], c[1], c[4], c[5], c[6]
        if not ID_RE.match(rid):
            failures.append(f"id {rid!r} does not match C<n>-<STRIDE letter><k>")
            continue
        if rid in rows:
            failures.append(f"duplicate row id {rid!r}")
            continue
        rows[rid] = {"threat": threat, "risk": risk, "mitigation": mitigation, "test": test}

    if not rows:
        print("FAIL: no STRIDE rows parsed; the table shape changed")
        return 1

    # 2. six categories per component
    seen: dict[str, set[str]] = {}
    for rid in rows:
        m = ID_RE.match(rid)
        assert m
        seen.setdefault(m.group(1), set()).add(m.group(2))
    for comp in sorted(seen, key=int):
        missing = [k for k in CATEGORIES if k not in seen[comp]]
        if missing:
            failures.append(f"component C{comp} has no row for STRIDE {','.join(missing)}")

    # required-case bullets in section 8
    s8_required = s8[s8.index("Required cases"):]

    high = {r for r, v in rows.items() if "Critical" in v["risk"] or "High" in v["risk"]}
    mitigated = {r for r in high if "Mitigated" in rows[r]["mitigation"]}
    unmitigated = high - mitigated

    # 3. mitigated Critical/High must name a section 8 case that exists
    for rid in sorted(mitigated):
        test = rows[rid]["test"]
        if not test.startswith("§8:"):
            failures.append(
                f"{rid} is a mitigated {rows[rid]['risk'].strip('*')} row but its Test cell "
                f"names no §8 case: {test!r}"
            )
            continue
        case = test.split("§8:", 1)[1].strip()
        needle = re.sub(r"\s+", " ", case)
        haystack = re.sub(r"\s+", " ", s8_required)
        if needle not in haystack:
            failures.append(f"{rid} names §8 case {case!r}, which does not appear in §8")

    # 4. unmitigated Critical/High must be disposed of
    must = closing[closing.index("Must mitigate before implementation proceeds"):]
    must = must[: must.index("\n\n**", must.index("| Row |"))]
    residual = closing[closing.index("### Residual Risks"):]
    for rid in sorted(unmitigated):
        if rid not in must and rid not in residual:
            failures.append(
                f"{rid} is an unmitigated {rows[rid]['risk'].strip('*')} row and appears in "
                f"neither the must-mitigate table nor Residual Risks"
            )

    # 5. every id referenced outside the STRIDE tables is defined
    for ref in sorted(set(REF_RE.findall(closing))):
        if ref not in rows:
            failures.append(f"closing tables reference {ref!r}, which no STRIDE row defines")

    # 6. the "already mitigated" roster matches the tables exactly
    roster_start = closing.index("**Already mitigated at Critical or High**")
    roster = closing[roster_start: closing.index("### Residual Risks", roster_start)]
    claimed = set(REF_RE.findall(roster))
    if claimed != mitigated:
        for extra in sorted(claimed - mitigated):
            failures.append(f"roster claims {extra} is a mitigated Critical/High row; it is not")
        for missing in sorted(mitigated - claimed):
            failures.append(f"roster omits {missing}, a mitigated Critical/High row")

    print(f"{path}: {len(rows)} STRIDE rows, {len(high)} Critical/High "
          f"({len(mitigated)} mitigated, {len(unmitigated)} not).")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS: ids unique, STRIDE coverage complete, every mitigated Critical/High row names a "
          "§8 case that exists, every unmitigated one is disposed of, and every id the closing "
          "tables name is defined.")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "docs/DESIGN.md"
    sys.exit(main(pathlib.Path(arg)))
