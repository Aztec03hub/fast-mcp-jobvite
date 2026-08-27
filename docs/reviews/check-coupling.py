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
     disposition: at those ratings a mitigation must have a test. Where the disposition is used,
     the rating it names must be the row's own, so an exemption cannot be granted against a band
     the row does not sit in.
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

A green from this script is only worth what its failure modes are worth, so every check has been
made to fire against a deliberately broken copy. Those controls used to live here as prose telling
a reader to "copy DESIGN.md and apply one break", which is a control nobody runs. They are now
executable:

    python3 docs/reviews/check-coupling-controls.py

Fifteen mutations of a temp copy, one per failure mode, each required to produce exit 1 AND its
expected message. DESIGN.md is opened read-only and never written. Run it whenever this file
changes; a check that cannot be shown to fail is not a check.

What this script does NOT check, stated so a green is not read as more than it is:
  - Whether a §8 case a row names actually TESTS what the row claims. The check is that the case
    text exists in §8, not that the test behind it is adequate, or written at all.
  - Whether a row's risk RATING is right. A Critical threat rated Medium escapes the Critical/High
    strictness entirely, and nothing here can see that.
  - Whether a mitigation described in the Mitigation column is real, implemented, or sufficient.
  - Anything in §11 outside the STRIDE and closing tables: the prose, the counts written out in
    it, and the Residual Risks rationales are all unchecked.
  - ONE property still depends on the prose keyword, and it cannot be made not to (FIX-8, below).
    A row that describes a real mitigation without using the word "Mitigated" AND disposes of
    itself as "residual"/"unmitigated"/"accepted" is not caught. Every other check reaches it.

FIX-8, and the part of it that is not closeable here. Check 3 used to iterate only rows whose
Mitigation column contained the literal word "Mitigated". Eight rows describe a real mitigation
without ever using it - C1-D1's reads "`RateLimitingMiddleware` with a mandatory `get_client_id`,
sized per session" - so they were skipped in silence. The check was right; the selector decided it
never ran. Check 3 now iterates EVERY row, and vocabulary, band matching, the Critical/High
exemption ban and §8 resolution are all keyed on the rating or on the Test cell itself, never on
prose. Nothing can be made invisible by wording.

The keyword survives in exactly one place: a row that DOES say "Mitigated" may not dispose of
itself with a disposition meaning "not mitigated". Inverting the loop alone silently lost that
property - controls 3, 10 and 11 went green - so it is kept, and it is used only to ADD a
requirement to rows that carry the keyword, never to decide whether a row is checked at all. That
direction is fail-safe: dropping the keyword loses one check instead of all of them.

Closing it completely needs mitigation status to be DATA rather than prose - an explicit status
token per row in §11. That is an edit to DESIGN.md, not to this script, and it is the lead's call.
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
# Dispositions that assert the row is NOT mitigated. A row claiming a mitigation may not use one.
NOT_MITIGATED_RE = re.compile(r"^(?:residual|accepted(?: \(B\d+(?:, ?B\d+)*\))?"
                              r"|unmitigated(?: \(B\d+(?:, ?B\d+)*\))?)$")
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

    # 3. EVERY row disposes of itself. This loop iterates all rows rather than a selected subset,
    #    because the selection is what failed: this check used to run only over rows whose
    #    Mitigation column contained the literal word "Mitigated", and eight rows describe a real
    #    mitigation without ever using it (C1-D1's is "`RateLimitingMiddleware` with a mandatory
    #    `get_client_id`, sized per session"). Those rows were skipped in silence, and the check
    #    was correct the whole time - the selector decided it never ran. Nothing below consults
    #    mitigation prose, so no future wording can make a row invisible again.
    for rid in sorted(rows):
        test = rows[rid]["test"]
        rating = rows[rid]["risk"].strip("* ")
        if test.startswith("§8:"):
            missing = names_missing_case(test)
            if missing is not None:
                failures.append(f"{rid} names §8 case {missing!r}, which does not appear in §8")
        elif (m := NOT_REQUIRED_RE.match(test)) is not None:
            if rid in high:
                # "not required" is an exemption from having a test. At Critical and High there is
                # no such exemption: the row either names a §8 case, or says plainly that it is not
                # mitigated (residual / unmitigated / accepted). Keyed on the rating, not on prose.
                failures.append(
                    f"{rid} is a {rating} row and may not use {test!r}: at Critical and High a row "
                    f"either names a §8 case or declares itself unmitigated"
                )
            elif m.group(1) != rating:
                # The disposition names the band it is claiming exemption at. If that band is not
                # the row's own rating, the exemption was granted against a rating the row does not
                # have, which is how a Medium mitigation gets waved through as though it were Low.
                failures.append(
                    f"{rid} is rated {rating} but its disposition {test!r} claims exemption at "
                    f"{m.group(1)}; the rating in the disposition must match the row's own"
                )
        elif not DISPOSITION_RE.match(test):
            failures.append(
                f"{rid} has an unrecognised Test cell {test!r}; expected a '§8: <case>' reference "
                f"or one of: no credible threat / residual / accepted / unmitigated / "
                f"not required (<rating>)"
            )
        elif rid in all_mitigated and NOT_MITIGATED_RE.match(test):
            # A row that claims a mitigation may not dispose of itself with a disposition that
            # means "not mitigated". This is the ONE place the prose keyword is still consulted,
            # and it is deliberately used to ADD a requirement, never to decide whether the row is
            # checked at all - which is the direction that produced FIX-8. A row that drops the
            # keyword loses this extra check but keeps every other one above; see the limitation
            # recorded in the module docstring.
            failures.append(
                f"{rid} states a mitigation but its Test cell is {test!r}, which means the row is "
                f"NOT mitigated; a mitigated row names a §8 case or carries 'not required "
                f"(<rating>)'"
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

    # (The former check 7 - vocabulary, and §8 resolution on rows that are not mitigated - is now
    #  part of check 3, which iterates every row. Keeping it separate is what let the two loops
    #  disagree about which rows they covered.)

    tested = sum(1 for r in rows if rows[r]["test"].startswith("§8:"))
    print(f"{path}: {len(rows)} STRIDE rows, {len(high)} Critical/High "
          f"({len(mitigated)} mitigated by the roster's reckoning, {len(unmitigated)} not); "
          f"all {len(rows)} rows checked for disposition, {tested} naming a §8 case.")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS: ids unique, STRIDE coverage complete, all {len(rows)} rows at EVERY severity "
          "dispose of themselves by naming a §8 case that exists or carrying a recognised "
          "disposition at their own rating, no Critical/High row claims exemption from having a "
          "test, every unmitigated Critical/High row is disposed of, and every id the closing "
          "tables name is defined.")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "docs/DESIGN.md"
    sys.exit(main(pathlib.Path(arg)))
