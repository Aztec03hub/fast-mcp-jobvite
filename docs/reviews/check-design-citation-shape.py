#!/usr/bin/env python3
"""Flag `DESIGN.md:N` citations whose target CANNOT be their subject.

    python3 docs/reviews/check-design-citation-shape.py [--sha <ref>]

R4 found ten of eighteen sampled citations in U5 landing **one paragraph
short** of their subject, and recommended a checker over the whole
population rather than finishing 29 more by hand. This is that checker
for the part a machine can decide.

**WHAT IT CANNOT DO, said first because it is the important half.** It
cannot tell whether a citation is RIGHT. Only a reader who knows the
claim can. `docs/reviews/check-design-citations.py` already proves a
citation RESOLVES, and this project has found that "resolves" and
"correct" are different things nine times over.

**WHAT IT CAN DECIDE.** A citation whose range is out of bounds,
entirely blank, or nothing but a code fence or table separator has a
target that cannot be anyone's subject, whatever the claim. And a range
that STARTS on a blank line is the exact shape of the off-by-one R4
measured: the author counted the paragraph break rather than the
paragraph.

Measured when written, against the freeze OF THAT DAY, over
`src/ tests/ scripts/`. The numbers below are that measurement and are
not re-derived. **The current freeze is the `--sha` default and nowhere
else in this file** - it has moved three times, and a second copy of it
in prose went stale on the second move:
399 occurrences, 206 distinct ranges, 0 out of bounds, 8 entirely blank,
11 fence-or-separator only. `DESIGN.md:311` is cited for "a URL
containing a secret is never constructed"; 311 is blank and the sentence
is at 312-313.

**Not a CI gate yet.** It reports a lower bound on a defect population
nobody has finished counting, and wiring a gate whose backlog is unknown
lands red - which this project has refused three times. Run it, fix what
it names, then wire it.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CITE = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")

#: Directories whose citations must resolve against the FROZEN design.
#: `docs/reviews/` is deliberately excluded: a review document cites the
#: design as it stood when the review ran, and re-pointing those would
#: rewrite history to match the present.
LIVE = ("src", "tests", "scripts")

STRUCTURAL = ("```", "|---", "---", "|--", ":--")


def design_lines(sha: str) -> list[str]:
    out = subprocess.run(
        ["git", "show", f"{sha}:docs/DESIGN.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", default="aca9397", help="the frozen DESIGN.md")
    args = parser.parse_args()

    lines = design_lines(args.sha)
    findings: dict[str, list[str]] = collections.defaultdict(list)
    seen = 0

    for sub in LIVE:
        for path in sorted((ROOT / sub).rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            body_lines = path.read_text(errors="replace").splitlines()
            for num, text in enumerate(body_lines, 1):
                for match in CITE.finditer(text):
                    seen += 1
                    start = int(match.group(1))
                    end = int(match.group(2) or match.group(1))
                    where = f"{path.relative_to(ROOT)}:{num}  {match.group(0)}"

                    if end > len(lines):
                        findings["past the end of DESIGN.md"].append(where)
                        continue
                    body = lines[start - 1 : end]
                    if not "".join(body).strip():
                        findings["the entire range is blank"].append(where)
                    elif all(
                        line.strip().startswith(STRUCTURAL)
                        for line in body
                        if line.strip()
                    ):
                        findings["only a fence or table separator"].append(where)
                    elif not body[0].strip():
                        findings[
                            "starts on a BLANK line (the off-by-one shape)"
                        ].append(where)

    if seen == 0:
        print("PARSED ZERO CITATIONS. The selector is broken; a green means nothing.")
        return 1

    print(f"DESIGN.md citations in {'/, '.join(LIVE)}/: {seen}")
    print(f"Checked against {args.sha}, {len(lines)} lines.\n")

    total = sum(len(v) for v in findings.values())
    for reason, rows in sorted(findings.items()):
        print(f"{len(rows):4}  {reason}")
        for row in rows:
            print(f"        {row}")

    print(
        f"\n{total} citation(s) point at something that cannot be their subject.\n"
        "This is a LOWER BOUND on wrong citations, and says nothing about the\n"
        "ones that land on real prose - only a reader who knows the claim can\n"
        "judge those. 'Resolves' and 'correct' are different things."
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
