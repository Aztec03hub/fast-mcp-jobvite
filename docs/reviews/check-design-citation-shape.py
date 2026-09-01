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

Measured when written, against the freeze OF THAT DAY, and over the
NARROWER population it scanned then - `src/ tests/ scripts/`, before the
scan was widened to every tracked `.py`/`.sh` including the checkers in
`docs/reviews/`. The numbers below are that measurement and are not
re-derived. **The current freeze is the `--sha` default and nowhere
else in this file** - it has moved three times, and a second copy of it
in prose went stale on the second move:
399 occurrences, 206 distinct ranges, 0 out of bounds, 8 entirely blank,
11 fence-or-separator only. A record of where a defect WAS, so it does
not move: `DESIGN.md:311` (REPOINT-EXEMPT) was cited for "a URL
containing a secret is never constructed"; 311 was blank and the
sentence was at 312-313.

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

#: The population is chosen by KIND, not by PATH. Every tracked `.py`
#: or `.sh` file is CODE, wherever it lives, and its citations are
#: claims about the design as it is NOW. Prose is excluded by SUFFIX: a
#: review or worklog `.md` cites the design as it stood when it was
#: written, and re-pointing those would rewrite history to match the
#: present.
#:
#: This was `LIVE = ("src", "tests", "scripts")`, and it excluded
#: `docs/reviews/` for exactly the prose reason above. That reasoning is
#: right for a review DOCUMENT and wrong for the ~40 CHECKERS in the
#: same directory - wired CI gates, linted and type-checked, whose
#: citations had never been scanned by anything.
#: `check-settings-are-read.py:9` carried a citation that RESOLVED and
#: named the wrong sentence; both citation gates passed it and a reader
#: found it (#114, fixed at dad014e). A path list cannot see the KIND of
#: the thing at the path.
CODE_SUFFIXES = {".py", ".sh"}

STRUCTURAL = ("```", "|---", "---", "|--", ":--")

#: Split so this line is not itself exempt.
EXEMPT = "REPOINT" + "-EXEMPT"


def code_files() -> list[pathlib.Path]:
    """Every tracked code file, enumerated from the CONTAINER.

    `git ls-files` is the authority rather than a list of directories,
    so a new directory of checkers is scanned the day it lands. A
    hand-kept list is blind to the member nobody adds to it.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(
        ROOT / name
        for name in out.split("\0")
        if name and pathlib.Path(name).suffix in CODE_SUFFIXES
    )


def design_lines(sha: str) -> list[str]:
    out = subprocess.run(
        ["git", "show", f"{sha}:docs/DESIGN.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.splitlines()


def classify(start: int, end: int, lines: list[str]) -> str | None:
    """Why this citation cannot be its subject, or None if it can be.

    LIFTED OUT OF `main`'s LOOP so it can be exercised directly. While
    this logic lived inline, the only way to reach it was to scan the
    whole tree, which meant nothing tested it - and R10 measured the
    consequence: deleting the blank-start branch outright left the
    scan's output byte-identical at 148 files / 875 citations / 0
    findings, with both population controls still printing FIRED. A
    detector no test can reach is a detector whose absence is invisible.
    """
    if end > len(lines):
        return "past the end of DESIGN.md"
    body = lines[start - 1 : end]
    if not "".join(body).strip():
        return "the entire range is blank"
    if all(line.strip().startswith(STRUCTURAL) for line in body if line.strip()):
        return "only a fence or table separator"
    if not body[0].strip():
        return "starts on a BLANK line (the off-by-one shape)"
    return None


def detector_controls(lines: list[str]) -> tuple[int, int]:
    """Each detector must FIRE on a citation built to trip it.

    Built from the frozen design in memory, so this costs nothing and
    writes no files. These are the controls whose absence R10-M2
    recorded: the two below prove the POPULATION is right and say
    nothing about whether anything is still being detected in it.
    """
    blank = next(i for i, t in enumerate(lines, 1) if not t.strip())
    starts_blank = next(
        i
        for i, t in enumerate(lines, 1)
        if not t.strip()
        and i < len(lines)
        and lines[i].strip()
        and not lines[i].strip().startswith(STRUCTURAL)
    )
    solid = next(
        i
        for i, t in enumerate(lines, 1)
        if t.strip() and not t.strip().startswith(STRUCTURAL)
    )

    cases: list[tuple[str, int, int, str | None]] = [
        ("past the end", len(lines) + 1000, len(lines) + 1000, "past the end"),
        ("entirely blank", blank, blank, "entire range is blank"),
        ("starts on a blank line", starts_blank, starts_blank + 2, "starts on a BLANK"),
        # THE NEGATIVE CONTROL. Without it every arm above passes on a
        # `classify` that simply returns a finding for everything.
        ("a citation that RESOLVES", solid, solid, None),
    ]

    fired = 0
    for label, start, end, expect in cases:
        got = classify(start, end, lines)
        ok = (got is None) if expect is None else (got is not None and expect in got)
        if ok:
            fired += 1
            print(f"  DETECTOR {label} -> FIRED ({got or 'no finding, as required'})")
        else:
            print(f"  DETECTOR {label} -> DID NOT FIRE; the branch is dead (got {got})")
    return fired, len(cases)


def controls(lines: list[str]) -> int:
    """Prove the population is by KIND, and that it is still scanned.

    A narrowed exclusion that STILL misses `docs/reviews/` looks exactly
    like one that was removed - both print a clean run. These say which
    it is, and they go red if the selector is re-narrowed to a directory
    list. The detector arm answers the other half: a right population
    that nothing examines also prints a clean run.
    """
    names = {p.relative_to(ROOT).as_posix() for p in code_files()}
    fired = total = 0

    total += 1
    checkers = sorted(n for n in names if n.startswith("docs/reviews/"))
    if checkers:
        fired += 1
        print(f"  CONTROL the checkers are IN ({len(checkers)} files) -> FIRED")
    else:
        print("  CONTROL the checkers are IN -> DID NOT FIRE, the scan skips them")

    total += 1
    prose = [n for n in names if n.endswith(".md")]
    if not prose:
        fired += 1
        print("  CONTROL prose (.md) stays OUT -> FIRED")
    else:
        print(f"  CONTROL prose (.md) stays OUT -> DID NOT FIRE ({len(prose)} in)")

    det_fired, det_total = detector_controls(lines)
    fired += det_fired
    total += det_total

    print(f"\n{fired}/{total} controls fired.")
    return 0 if fired == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", default="aca9397", help="the frozen DESIGN.md")
    parser.add_argument(
        "--controls", action="store_true", help="prove the population is by kind"
    )
    args = parser.parse_args()

    lines = design_lines(args.sha)

    if args.controls:
        return controls(lines)

    findings: dict[str, list[str]] = collections.defaultdict(list)
    seen = 0
    exempted = 0

    paths = code_files()
    for path in paths:
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

    if seen == 0:
        print("PARSED ZERO CITATIONS. The selector is broken; a green means nothing.")
        return 1

    print(f"DESIGN.md citations in {len(paths)} tracked .py/.sh files: {seen}")
    print(f"Checked against {args.sha}, {len(lines)} lines.")
    # THE EXEMPTION SET IS PART OF THE RESULT. Any line can opt out of
    # this checker with a comment marker, and a growing exemption set
    # would otherwise be invisible in the very report that depends on
    # it - including from a genuinely wrong citation sharing the line.
    print(f"{exempted} line(s) skipped as {EXEMPT}.\n")

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
