#!/usr/bin/env python3
r"""A brief must cite a report that EXISTS in the repository.

    uv run --frozen python docs/reviews/check-brief-report-references.py

**THE DEFECT.** `REVIEW-R18.md` - 28KB, ten findings, the only narrative
record of its round - sat UNTRACKED in `fmj-worktrees/r18` for hours
while nothing in the repository could see it. `PREAMBLE.md:133` already
required the opposite: a report must be *"committed on your branch ...
Never only a worktree, never `/tmp`: a 48KB report with nineteen
findings was destroyed exactly that way"*. So the rule was written after
one loss and did not prevent the next near-loss. **A rule nothing checks
is a rule that documents its own violations.**

**AND THE BRIEF ITSELF OVERRODE THE RULE.**
`BRIEF-R19-the-fix-round.md` §A told the reviewer to read R18's report
*"on branch `review/r18` in `fmj-worktrees/r18`; read it from there"*.
It was not on that branch. A brief that names a WORKTREE path points at
something that stops existing when the agent finishes.

**THE SECOND DEFECT IS MINE, AND IT IS WHY THIS FILE EXISTS RATHER THAN
A EULOGY.** I searched every ref with `git cat-file -e` and every add
with `git log --all --diff-filter=A`, got nothing from both, and wrote
that the report was LOST. Both measurements were correct: it is in no
commit and in no dangling blob, because it was never `git add`ed.
**"In no git object" is not "gone".** An untracked file lives in the
FILESYSTEM - the one place a search over refs and objects cannot look -
and `suborch-170` looked there and found it.

The premise that carried the error was never measured at all. I wrote
"the worktree is gone"; `.git/worktrees` held fourteen entries and r18
was one of them. **A loss claim needs its own evidence, and it needs to
name all three places: refs, objects, filesystem.** An alarming
conclusion gets re-checked least, because re-checking feels like
doubting a loss.

**WHY THIS IS A RATCHET AND NOT A ZERO.** A brief legitimately names the
report its agent has not written yet. Demanding zero would be red by
construction and switched off within a day. So the gate records the
KNOWN-unresolvable set and fails when a NEW one appears.

**IT FAILS IN BOTH DIRECTIONS, which is the half that rots otherwise.**
A recorded entry that now RESOLVES is an error, and so is one nothing
cites any more. The record must shrink when the world does, or it
becomes a permanent excuse list nobody re-reads - the failure mode of
every allowlist this project has built. That is not theoretical here:
the entry for an in-flight worklog is designed to go red the moment the
agent commits it, which is how it deletes itself.

Re-derive the population without trusting this file:

    grep -rhoE '(REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+[.]md' \
      docs/briefs/*.md | sort -u
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = ROOT / "docs/briefs"
RECORD = ROOT / "docs/reviews/brief-report-refs-known-missing.txt"

# --briefs/--record/--tracked exist so the CONTROLS can point this at
# fixtures rather than mutating the real tree to watch a gate fail. CI
# runs it BARE, which is the real container - a control needing a flag
# CI does not pass asks a different question from the one CI asks, so
# the defaults are not conveniences, they ARE the gate.

# The KIND is a report the briefs treat as a deliverable: a review, a
# worklog or a findings document. Matched by NAME, not by directory, so
# a citation that omits the path is still a citation.
REF = re.compile(
    r"(?:docs/(?:reviews|worklogs)/)?"
    r"((?:REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+\.md)"
)


def tracked_basenames(listing: Path | None = None) -> set[str] | None:
    """Every tracked file's basename, or None if git could not be read.

    None and empty must stay distinguishable: an empty set would make
    every reference dangling and the report would be spectacular and
    wrong. R18-M1 measured that exact shape one file over.
    """
    if listing is not None:
        if not listing.exists():
            return None
        raw = listing.read_text().split("\n")
    else:
        try:
            out = subprocess.run(
                ["git", "-C", str(ROOT), "ls-files", "-z"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        raw = out.stdout.split("\0")
    return {p.rsplit("/", 1)[-1] for p in raw if p.strip()}


def read_record(record: Path) -> dict[str, str]:
    """Map each recorded name to the reason it is unresolvable."""
    if not record.exists():
        return {}
    out: dict[str, str] = {}
    for line in record.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, reason = line.partition("  ")
        out[name.strip()] = reason.strip()
    return out


def cited(briefs: Path) -> dict[str, set[str]]:
    """Map each cited basename to the briefs citing it."""
    refs: dict[str, set[str]] = {}
    for p in sorted(briefs.glob("*.md")):
        for m in REF.finditer(p.read_text()):
            refs.setdefault(m.group(1), set()).add(p.name)
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--briefs", type=Path, default=BRIEFS)
    ap.add_argument("--record", type=Path, default=RECORD)
    ap.add_argument("--tracked", type=Path, default=None)
    args = ap.parse_args()

    names = tracked_basenames(args.tracked)
    if names is None:
        print("::error::could not read `git ls-files`, so NOTHING was checked.")
        print("This is a refusal, not a pass - an unreadable index would")
        print("otherwise make every reference look dangling.")
        return 2

    refs = cited(args.briefs)
    record = read_record(args.record)

    dangling = {n: s for n, s in refs.items() if n not in names}
    unrecorded = sorted(set(dangling) - set(record))
    resolved = sorted(n for n in record if n in names)
    unreferenced = sorted(n for n in record if n not in refs)

    print(f"Briefs scanned:            {len(list(args.briefs.glob('*.md')))}")
    print(f"Report names cited:        {len(refs)}")
    print(f"Cited but not in the repo: {len(dangling)}")
    print(f"Recorded as known-missing: {len(record)}")

    failed = False

    if unrecorded:
        failed = True
        print()
        print("::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.")
        for n in unrecorded:
            print(f"  {n}   cited by {', '.join(sorted(dangling[n]))}")
        print("Either commit the report, or record it in")
        print(f"  {args.record}")
        print("with the reason it cannot be committed. Recording it is not a")
        print("waiver - it is a statement that the loss is known and accepted.")

    if resolved:
        failed = True
        print()
        print("::error::A RECORDED ENTRY NOW RESOLVES, so the record is stale.")
        for n in resolved:
            print(f"  {n}   is tracked now; delete its line")
        print("An excuse list that only grows stops being read. It must")
        print("shrink when the world does.")

    if unreferenced:
        failed = True
        print()
        print("::error::A RECORDED ENTRY IS NO LONGER CITED BY ANY BRIEF.")
        for n in unreferenced:
            print(f"  {n}   nothing cites it; delete its line")

    if failed:
        return 1

    print()
    print("Every report a brief cites is committed, or recorded as lost.")
    print("NOTE: this proves the FILE EXISTS. It does not prove the file is")
    print("the report the brief meant, and it cannot: a brief cites a name.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
