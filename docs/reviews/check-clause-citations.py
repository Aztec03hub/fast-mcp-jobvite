#!/usr/bin/env python3
"""Resolve every standard-clause citation in OBLIGATIONS.md against the standards repo.

    python3 docs/reviews/check-clause-citations.py [--standards PATH]

**NOT a CI gate, and it cannot be one.** It reads a SIBLING CHECKOUT that CI
does not have, so wiring it would make the pipeline depend on a repository
outside it. It follows the same shape as `scripts/check-u1-pid1-shutdown.sh`,
which needs Docker: listed in CONTRIBUTING.md under measurements a human runs,
and **exiting 2 when its input is unavailable, never 0**. A skip that reports
success is a green that tested nothing.

WHY IT EXISTS. `check-obligations.py` verifies the ARTIFACT column - the thing
that discharges an obligation. It says nothing at all about the CLAUSE column,
which is the JUSTIFICATION: the standards text asserting the obligation is real.
So the half of every row that explains WHY was, until this script, entirely
unverified, and it cites by line into a repository this project neither controls
nor pins. A standards edit silently repoints all of them at once.

WHAT IT CHECKS, AND WHAT IT DELIBERATELY DOES NOT.

Checked: the cited file exists under `standards/`, and the cited line (or range)
is within it. That catches a renamed file, a deleted file, and a citation past
the end - the failures that make a clause unreachable.

**NOT checked: that the line SAYS what the row claims.** This project has found
nine wrong-subject citations, four of them inside the ADR documenting that very
defect class, so "resolves" must never be reported as "correct". The script
prints the cited text so a human can read it, and says so in its own summary
rather than letting a green imply more than it measured.

A HAND CHECK OF ALL 22, done once when this was written: every one resolved and
twenty pointed at normative text. Two did not, and are recorded in
`docs/OBLIGATIONS.md` rather than here, because they are findings about the map:
B53 points at a comment inside an example block, and B102 at a line of an ASCII
box diagram. Both are weak anchors - a diagram is not a requirement - and neither
is wrong about the obligation.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

EX_INPUT_UNAVAILABLE = 2

DEFAULT_STANDARDS = pathlib.Path(
    "/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards"
)

ROW = re.compile(
    r"^\| (?P<b>B\S+) \| (?P<cls>\w+) \| `[^`]+` \| `[^`]+` \| `(?P<clause>[^`]+)` \|",
    re.M,
)
CITE = re.compile(r"^(?P<rel>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def resolve(standards: pathlib.Path, rel: str) -> pathlib.Path | None:
    """Find a clause file under `standards/`, by exact path then by name."""
    exact = standards / "standards" / rel
    if exact.is_file():
        return exact
    matches = list((standards / "standards").glob(f"**/{pathlib.Path(rel).name}"))
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standards", type=pathlib.Path, default=DEFAULT_STANDARDS)
    parser.add_argument(
        "--quiet", action="store_true", help="only print problems and the summary"
    )
    args = parser.parse_args()

    if not (args.standards / "standards").is_dir():
        print(f"standards repo not found at {args.standards}")
        print(
            "Exiting 2, NOT 0: this measurement did not run, and a skip that "
            "reports success is a green that tested nothing."
        )
        return EX_INPUT_UNAVAILABLE

    here = pathlib.Path(__file__).resolve().parent.parent
    rows = ROW.findall((here / "OBLIGATIONS.md").read_text(encoding="utf-8"))

    # Selector control: a wrong zero explains itself. Zero rows parsed would
    # print "0 problems" and exit 0, which is indistinguishable from a clean run.
    if not rows:
        print("PARSED ZERO ROWS. The selector is broken; a green here means nothing.")
        return 1

    problems: list[str] = []
    for bnum, _cls, clause in rows:
        cite = CITE.match(clause)
        if not cite:
            problems.append(f"{bnum}: clause {clause!r} carries no line number")
            continue

        path = resolve(args.standards, cite.group("rel"))
        if path is None:
            problems.append(
                f"{bnum}: {clause} - no such file under standards/, or the name "
                "is ambiguous. A renamed standard silently unmoors every row "
                "citing it."
            )
            continue

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        start = int(cite.group("start"))
        end = int(cite.group("end") or start)
        if end > len(lines):
            problems.append(
                f"{bnum}: {clause} is past the end of the file ({len(lines)} lines)"
            )
            continue

        if not args.quiet:
            text = " ".join(lines[start - 1 : end]).strip()
            print(f"  {bnum:6} {clause:44} {text[:80]}")

    print(f"\nClause citations: {len(rows)}  |  unresolvable: {len(problems)}")
    for problem in problems:
        print(f"  FAIL: {problem}")

    print(
        "\nThis proves each citation RESOLVES. It does NOT prove the line says "
        "what the row claims -\nnine wrong-subject citations have been found on "
        "this project, four of them inside the ADR\nthat documents the defect. "
        "Read the text above; do not take the exit code for agreement."
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
