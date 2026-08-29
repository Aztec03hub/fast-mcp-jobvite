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

A HAND CHECK, done once when this was written: every citation resolved and all
but two pointed at normative text. The two are recorded in `docs/OBLIGATIONS.md`
rather than here, because they are findings about the map: B53 points at a
comment inside an example block, and B102 at a line of an ASCII box diagram.
Both are weak anchors - a diagram is not a requirement - and neither is wrong
about the obligation.

**The count is not written here.** It was "all 22" for one commit and was 29 the
moment the selector stopped silently dropping ABSENT rows. Run the script.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import sys

EX_INPUT_UNAVAILABLE = 2

DEFAULT_STANDARDS = pathlib.Path(
    "/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards"
)

CITE = re.compile(r"^(?P<rel>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def _rows(map_path: pathlib.Path) -> list[dict[str, str]]:
    """Parse OBLIGATIONS.md with `check-obligations.py`'s OWN parser.

    **This script used to carry a second regex over the same table, and
    the two disagreed.** Mine required a BACKTICKED artifact and subject,
    but an ABSENT row must carry `-` in both - so every ABSENT row failed
    my regex and was silently skipped, and its clause column, which for
    an ABSENT row is the ENTIRE row, was checked by nothing at all. A row
    whose subject merely contained a backtick was dropped the same way.

    Nobody could have noticed from either script's output. It was found
    by comparing the two counts: 31 mappings against 23 clause citations,
    a difference that looked like arithmetic and was a silent exclusion.

    So there is now ONE selector. Importing it removes the disagreement
    class rather than fixing this instance of it - the other script
    already parses and stores `clause` and simply does not use it.
    """
    spec = importlib.util.spec_from_file_location(
        "_obligations", pathlib.Path(__file__).with_name("check-obligations.py")
    )
    if spec is None or spec.loader is None:  # pragma: no cover - import plumbing
        message = "could not load check-obligations.py to share its parser"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows, problems = module.parse(map_path.read_text(encoding="utf-8"))
    if problems:
        for problem in problems:
            print(f"  {problem}")
    return list(rows)


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
    rows = _rows(here / "OBLIGATIONS.md")

    # Selector control: a wrong zero explains itself. Zero rows parsed would
    # print "0 problems" and exit 0, which is indistinguishable from a clean run.
    if not rows:
        print("PARSED ZERO ROWS. The selector is broken; a green here means nothing.")
        return 1

    # SECOND selector control, aimed at the exact defect this script had.
    #
    # An earlier regex here silently dropped every ABSENT row, because those
    # carry `-` where other rows carry a backticked artifact. The output looked
    # identical to a clean run - a smaller number, with nothing saying it was
    # smaller. For an ABSENT row the clause citation IS the entire row, so those
    # were the rows least able to afford being skipped.
    #
    # A partial selector cannot report itself. This one is checked from the
    # OUTSIDE: the map has ABSENT rows, so a parse that finds none has lost
    # them, whatever it thinks it did.
    absent = [row for row in rows if row.get("class") == "ABSENT"]
    if not absent:
        print(
            "PARSED NO ABSENT ROWS. docs/OBLIGATIONS.md contains them, so the "
            "selector is dropping a class - which is how the clause column of "
            "every ABSENT row went unchecked before."
        )
        return 1

    problems: list[str] = []
    for row in rows:
        bnum, clause = row["b"], row["clause"]
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
