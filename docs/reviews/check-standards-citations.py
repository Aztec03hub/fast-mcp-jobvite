#!/usr/bin/env python3
"""Resolve inline `<standard>.md:N` citations against the standards corpus.

    python3 docs/reviews/check-standards-citations.py

**Nothing checked these until now, and one of them was wrong.**
`check-design-citation-shape.py` reads only `DESIGN.md:N`.
`check-clause-citations.py` reads only the CLAUSE column of
`docs/OBLIGATIONS.md`. **Inline standards citations in `src/`, `tests/`
and `scripts/` are a third population that no instrument covered** -
found when `tests/test_readme.py` was seen citing
`readme-standard.md:63`, which is BLANK; the 500-line cap it names is at
`:64`, which `OBLIGATIONS.md` had right and the test had wrong.

**WHAT IT DECIDES, and it is deliberately the same narrow question the
DESIGN.md shape checker answers.** A target that is out of bounds,
entirely blank, or only a fence or table separator cannot be anyone's
subject, whatever the claim. **It CANNOT tell whether a citation is
right** - only a reader who knows the claim can, and this project has
now found that "resolves" and "correct" are different things eleven
times.

**Two citation FORMS exist here and only one is resolvable.** The
directory form - `backend/resilience.md:91-94` - names a file under
`standards/`. The bare form - `bash.md:741` - does not say which
directory, and is resolved by searching for a unique basename; an
ambiguous basename is REFUSED rather than guessed.

**The corpus is a sibling checkout and its absence is exit 2, never 0.**
A checker that reports "all clear" because it could not find the thing
it checks is the failure `check-clause-citations.py` was written to
avoid, and this file takes the same position.
"""

from __future__ import annotations

import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CORPUS = ROOT.parent / "evolv-coder-standards" / "standards"
LIVE = ("src", "tests", "scripts")
STRUCTURAL = ("```", "|---", "---", "|--", ":--")

#: `<dir>/<file>.md:N` or `<file>.md:N`, with an optional range end.
CITE = re.compile(r"\b(?:([a-z][a-z-]*)/)?([a-z][a-z0-9-]*\.md):(\d+)(?:-(\d+))?")

#: Documents that are OURS, not the corpus. A citation to one of these is
#: a different population with its own checker, or none.
OURS = {
    "design.md", "readme.md", "contributing.md", "changelog.md",
    "jobvite-api.md", "jobvite-contract.md", "fastmcp.md", "standards.md",
    "implementation-plan.md", "obligations.md", "decisions.md",
}


def resolve(directory: str | None, basename: str) -> pathlib.Path | None:
    """The corpus file a citation names, or `None` if it is ambiguous."""
    if directory:
        candidate = CORPUS / directory / basename
        return candidate if candidate.is_file() else None
    matches = sorted(CORPUS.rglob(basename))
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    if not CORPUS.is_dir():
        print(f"CORPUS ABSENT at {CORPUS}")
        print("Exiting 2, NOT 0: a checker that cannot find its subject has")
        print("not checked anything, and a green from it would be a lie.")
        return 2

    findings: dict[str, list[str]] = collections.defaultdict(list)
    seen = 0
    for sub in LIVE:
        for path in sorted((ROOT / sub).rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            for num, text in enumerate(path.read_text(errors="replace").splitlines(), 1):
                for directory, basename, start, end in CITE.findall(text):
                    if basename.lower() in OURS:
                        continue
                    seen += 1
                    cite = f"{directory + '/' if directory else ''}{basename}:{start}"
                    where = f"{path.relative_to(ROOT)}:{num}  {cite}"
                    target = resolve(directory or None, basename)
                    if target is None:
                        findings["no unique file in the corpus"].append(where)
                        continue
                    lines = target.read_text(errors="replace").splitlines()
                    lo, hi = int(start), int(end or start)
                    if hi > len(lines):
                        findings["past the end of the standard"].append(where)
                    elif not "".join(lines[lo - 1 : hi]).strip():
                        findings["the entire range is blank"].append(where)
                    elif all(
                        line.strip().startswith(STRUCTURAL)
                        for line in lines[lo - 1 : hi]
                        if line.strip()
                    ):
                        findings["only a fence or table separator"].append(where)
                    elif not lines[lo - 1].strip():
                        findings["starts on a BLANK line"].append(where)

    if seen == 0:
        print("PARSED ZERO CITATIONS. The selector is broken; a green means nothing.")
        return 1

    print(f"Standards citations in {'/, '.join(LIVE)}/: {seen}")
    print(f"Corpus: {CORPUS}\n")

    total = sum(len(v) for v in findings.values())
    for reason, rows in sorted(findings.items()):
        print(f"{len(rows):4}  {reason}")
        for row in rows:
            print(f"        {row}")

    if total:
        print(f"\n{total} citation(s) point at something that cannot be their subject.")
        print("This is a LOWER BOUND. A citation landing on real prose that")
        print("happens to be the WRONG prose is invisible here.")
        return 1

    print("Every standards citation resolves to text that could be its subject.")
    print("NOTE: that is not a claim any of them is CORRECT - only a reader who")
    print("knows the claim can judge that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
