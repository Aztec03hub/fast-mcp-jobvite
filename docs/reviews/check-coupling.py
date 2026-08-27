#!/usr/bin/env python3
"""Mechanically check DESIGN.md section 11's threat model against itself and against section 8.

Why this exists: the coupling claim in section 11 ("every mitigated Critical or High row has a
required test in section 8") was hand-checked and wrong on three consecutive review rounds, and
the disposition tables silently dropped six rows that had been added to the analysis. Both are
checkable properties of the document. This script checks them.

Checks, in order:
  1. Every STRIDE row id is unique and matches C<n>-<STRIDE letter><k>.
  2. Every component covers all six STRIDE categories.
  3. Every mitigated row of ANY severity accounts for itself in its Test column, either by naming a
     section 8 case that appears verbatim in section 8's required-cases list, or by carrying an
     explicit "not required (<rating>)" disposition. Critical and High rows may not use that
     disposition: at those ratings a mitigation must have a test.
  4. Every Critical or High row that is NOT mitigated appears either in the must-mitigate table or
     in Residual Risks.
  5. Every row id referenced anywhere in section 11 outside the STRIDE tables is defined by them.
  6. The "Already mitigated at Critical or High" roster matches the set the tables imply, exactly.
  7. Every Test cell, on every row of every severity, is drawn from the recognised vocabulary, so a
     typo or an invented disposition cannot pass as one. Any section 8 reference resolves, whether
     the row is mitigated or not.

Why check 3 covers every severity: it originally covered Critical and High only, which left the
property it exists to enforce - a row naming a test that exists - hand-checked at Medium and Low.
Two Medium rows were added carrying section 8 cases the script could not see. Hand-checking is what
was wrong three rounds running, so the band it is done in does not make it reliable.

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

# The closed vocabulary a Test cell may use when it does not name a §8 case. Anything outside this
# is rejected by check 7 rather than silently accepted, so an invented or mistyped disposition
# cannot pass for a real one. Derived from the dispositions the document actually uses.
NOT_REQUIRED_RE = re.compile(r"^not required \((Critical|High|Medium|Low)\)$")
DISPOSITION_RE = re.compile(
    r"^(?:"
    r"no credible threat"
    r"|residual"
    r"|accepted(?: \(B\d+(?:, ?B\d+)*\))?"
    r"|unmitigated(?: \(B\d+(?:, ?B\d+)*\))?"
    r"|not required \((?:Critical|High|Medium|Low)\)"
    r")$"
)


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

    haystack = re.sub(r"\s+", " ", s8_required)

    def names_missing_case(test: str) -> str | None:
        """Return the §8 case named by this Test cell if it is absent from §8, else None."""
        case = test.split("§8:", 1)[1].strip()
        return None if re.sub(r"\s+", " ", case) in haystack else case

    high = {r for r, v in rows.items() if "Critical" in v["risk"] or "High" in v["risk"]}
    all_mitigated = {r for r, v in rows.items() if "Mitigated" in v["mitigation"]}
    mitigated = high & all_mitigated
    unmitigated = high - mitigated

    # 3. every mitigated row, at ANY severity, accounts for itself: it either names a §8 case that
    #    exists, or carries an explicit "not required (<rating>)". Critical/High may not use the
    #    latter - at those ratings a mitigation must have a test.
    for rid in sorted(all_mitigated):
        test = rows[rid]["test"]
        rating = rows[rid]["risk"].strip("* ")
        if test.startswith("§8:"):
            missing = names_missing_case(test)
            if missing is not None:
                failures.append(f"{rid} names §8 case {missing!r}, which does not appear in §8")
        elif NOT_REQUIRED_RE.match(test):
            if rid in high:
                failures.append(
                    f"{rid} is a mitigated {rating} row and may not use {test!r}: at Critical and "
                    f"High a mitigation must name a §8 case"
                )
        else:
            failures.append(
                f"{rid} is a mitigated {rating} row but its Test cell neither names a §8 case nor "
                f"carries a 'not required (<rating>)' disposition: {test!r}"
            )

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

    # 7. every Test cell on every row is drawn from the recognised vocabulary, and any §8 reference
    #    resolves even on a row that is not mitigated. A dangling reference is a defect regardless
    #    of severity, and an invented disposition must not read as a real one.
    for rid in sorted(rows):
        test = rows[rid]["test"]
        if test.startswith("§8:"):
            if rid not in all_mitigated:
                missing = names_missing_case(test)
                if missing is not None:
                    failures.append(f"{rid} names §8 case {missing!r}, which does not appear in §8")
        elif not DISPOSITION_RE.match(test):
            failures.append(
                f"{rid} has an unrecognised Test cell {test!r}; expected a '§8: <case>' reference "
                f"or one of: no credible threat / residual / accepted / unmitigated / "
                f"not required (<rating>)"
            )

    tested = sum(1 for r in all_mitigated if rows[r]["test"].startswith("§8:"))
    print(f"{path}: {len(rows)} STRIDE rows, {len(high)} Critical/High "
          f"({len(mitigated)} mitigated, {len(unmitigated)} not); "
          f"{len(all_mitigated)} mitigated at all severities, {tested} naming a §8 case.")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS: ids unique, STRIDE coverage complete, every mitigated row AT EVERY SEVERITY names "
          "a §8 case that exists or an explicit disposition, every unmitigated Critical/High row is "
          "disposed of, every Test cell uses the recognised vocabulary, and every id the closing "
          "tables name is defined.")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "docs/DESIGN.md"
    sys.exit(main(pathlib.Path(arg)))
