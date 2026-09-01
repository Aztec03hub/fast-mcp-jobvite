#!/usr/bin/env python3
"""Report the commits on the trunk that NO review round has covered.

    python3 docs/reviews/check-review-coverage.py

**WHY THIS EXISTS.** On 2026-09-01 I found 45 consecutive commits that
no review round had examined - 133 files, +7787/-2561 - including nine
ADRs applied to the frozen design, a tenth applied after it, and the
fixes an earlier round had itself demanded. I found them by accident,
while checking whether a filename collided.

**IT WAS NOT AN OVERSIGHT, IT WAS THE MODEL.** Every round through R8
reviewed a UNIT - `REVIEW-R4` says *"U5, search_jobs"*. R9 was the first
to review a RANGE. So fixes, chores, checkers, CI and ADR application
were never in any round's scope by construction. Of those 45 commits,
zero mention a unit; all 18 merges are `fix/*` or `chore/*`. **The
least-reviewed code here is the code that does the reviewing.**

**WHY IT REFUSES TO GUESS.** The obvious implementation derives each
round's coverage from the SHA its document cites. That is not sound: of
the code-review documents, only `CODE-REVIEW-R9` states a range. The
rest cite the tree state they read AT, and all but one are plain
commits, so there is no `M^1..M` to expand. A checker that inferred
would **manufacture coverage for code nobody read** and certify it
forever - strictly worse than the gap, because an absence you can see
beats a false presence you cannot.

## Four defects review R12 found in this file, and the fix for each

**THE CONTAINER BASE IS FIXED, NOT DERIVED (R12-H3).** It used to be
`min(declared bases)`, which made the metric MANIPULABLE IN THE WRONG
DIRECTION: deleting a `REVIEW-COVERS` line moved the base forward and
dropped `COVERED BY NOTHING` from 59 to 2. A gate whose number IMPROVES
when you remove a declaration teaches exactly the behaviour it exists to
prevent. `CONTAINER_BASE` is now a constant, so removing a declaration
can only make the number worse.

**THE POPULATION IS A REGEX OVER EVERY `.md` HERE (R12-M4).** The glob
`*REVIEW-R*.md` silently missed `REVIEW-CODE-R2.md` - a real round, in
no bucket at all, neither declared nor exempt. That is the third time in
one day a pattern-shaped population lost a member, and this file exists
to enforce container thinking. The census is printed so the population
is visible rather than assumed.

**AN EXEMPTION NEEDS A NON-EMPTY REASON (R12-M5).** Membership and
truthiness were tested separately, so a blank reason made a document
exempt AND reported as unexplained at once.

**A GIT FAILURE EXITS 3, NOT 1 (R12-L3).** A broken instrument and a
real finding must not share an exit code.

**ONLY ONE DECLARATION PER DOCUMENT (R12-N2).** A second was silently
ignored; two now refuse.

**WHAT IT STILL CANNOT DO.** It checks that a commit falls inside some
round's declared range. It cannot check the round READ that commit. R12
put it precisely: its own declaration credits 45 commits to a round that
read 62 of 133 files, because two agents split that range by PATH. A
`PATHS` field would let such rounds compose; until then a declaration is
a claim about the range an author was RESPONSIBLE for, and this gate
only makes the claim explicit and total.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REVIEWS = ROOT / "docs" / "reviews"

#: The commit from which review coverage is claimed. **A CONSTANT, never
#: derived from the declarations** - see R12-H3 above. Moving it FORWARD
#: hides commits, so it changes only with a recorded reason.
#: `8695101` is the base `CODE-REVIEW-R9` states in its own heading, and
#: the oldest point any round declares.
CONTAINER_BASE = "8695101"

#: A code-review document: the word REVIEW plus a round number, anywhere
#: in the name. Catches `REVIEW-R3`, `CODE-REVIEW-R9` and the
#: `REVIEW-CODE-R2` spelling a glob missed.
IS_REVIEW = re.compile(r"REVIEW.*-R\d+", re.IGNORECASE)

#: Excluded, with the reason. `PLAN-REVIEW-*` review the plan and
#: `DESIGN-*-REVIEW` the design: neither reviews merged commits, so a
#: commit range is not a thing they could declare.
NOT_A_COMMIT_REVIEW = re.compile(r"^PLAN-REVIEW|REVIEW$", re.IGNORECASE)

DECLARATION = re.compile(
    r"^<!--\s*REVIEW-COVERS:\s*"
    r"(?P<base>[0-9a-f]{7,40})\.\.(?P<head>[0-9a-f]{7,40})\s*-->\s*$",
    re.MULTILINE,
)

#: Rounds that reviewed a UNIT at a tree state and have no range to
#: recover. Inventing one for them is the single thing this checker must
#: never do. **A blank reason is not an exemption** (R12-M5).
UNDECLARED_BY_HISTORY: dict[str, str] = {
    "REVIEW-CODE-R2.md": "reviewed U1/U3/U4 at a pinned SHA, not a range",
    "REVIEW-R3.md": "reviewed 'the seven merged units', not a range",
    "REVIEW-R4.md": "reviewed U5 at 555bad6, a tree state, not a range",
    "REVIEW-R5.md": "reviewed U6 at d0abd10, a tree state, not a range",
    "REVIEW-R6.md": "reviewed U7 at ec38835, a tree state, not a range",
    "REVIEW-R7.md": "reviewed U8/U9/U12/U10 at bc0f958, a tree state",
    "REVIEW-R8.md": "reviewed U14 at 2c6ff19, a tree state, not a range",
}


def git(*args: str) -> str:
    """Run git in the repo; return stdout, or exit 3 with its stderr.

    Exit 3, not 1: a broken instrument and a real finding must not share
    an exit code (R12-L3).
    """
    done = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    )
    if done.returncode != 0:
        print(f"git {' '.join(args)} failed: {done.stderr.strip()}")
        print("This is a BROKEN INSTRUMENT, not a finding. Exit 3.")
        raise SystemExit(3)
    return done.stdout.strip()


def review_documents() -> tuple[list[pathlib.Path], list[str]]:
    """The code-review documents, and what was excluded and why."""
    kept: list[pathlib.Path] = []
    skipped: list[str] = []
    for path in sorted(REVIEWS.glob("*.md")):
        if not IS_REVIEW.search(path.stem):
            skipped.append(f"{path.name} (no round number)")
        elif NOT_A_COMMIT_REVIEW.search(path.stem):
            skipped.append(f"{path.name} (reviews a document, not commits)")
        else:
            kept.append(path)
    return kept, skipped


def main() -> int:
    docs, skipped = review_documents()
    print(f"Review documents in the population: {len(docs)}")
    print(f"Excluded, with a reason: {len(skipped)}")
    if not docs:
        print("MATCHED ZERO review documents. An empty population reports")
        print("full coverage, which would mean nothing. Exit 2.")
        return 2

    ranges: dict[str, tuple[str, str]] = {}
    undeclared: list[str] = []
    for path in docs:
        found = DECLARATION.findall(path.read_text(encoding="utf-8"))
        if len(found) > 1:
            print(f"\n{path.name} carries {len(found)} REVIEW-COVERS lines.")
            print("Only the first would be read, so the rest are invisible.")
            print("Refusing rather than picking one. Exit 2.")
            return 2
        if found:
            ranges[path.name] = found[0]
        else:
            undeclared.append(path.name)

    covered: set[str] = set()
    for name, (base, head) in sorted(ranges.items()):
        commits = git("rev-list", f"{base}..{head}").split()
        covered.update(commits)
        print(f"  DECLARED  {name}: {base}..{head} ({len(commits)} commits)")

    unexplained: list[str] = []
    for name in sorted(undeclared):
        reason = UNDECLARED_BY_HISTORY.get(name, "").strip()
        if reason:
            print(f"  HISTORIC  {name}: no range - {reason}")
        else:
            unexplained.append(name)
            print(f"  UNDECLARED {name}: no REVIEW-COVERS, and no reason")

    trunk = git("rev-list", f"{CONTAINER_BASE}..HEAD").split()
    uncovered = [c for c in trunk if c not in covered]

    print(f"\nTrunk commits since {CONTAINER_BASE} (a CONSTANT): {len(trunk)}")
    print(f"Inside a declared review range: {len(trunk) - len(uncovered)}")
    print(f"COVERED BY NOTHING: {len(uncovered)}")

    if uncovered:
        print("\nThe most recent 25 with no review round:")
        for sha in uncovered[:25]:
            print(f"  {git('log', '-1', '--format=%h %s', sha)[:88]}")

    if uncovered or unexplained:
        print(
            "\nA commit inside no round's declared range has been read by\n"
            "nobody. NOTE: this proves a commit falls in a declared range,\n"
            "NOT that the round read it - a declaration is a claim."
        )
        return 1

    print("\nEvery trunk commit falls inside some round's declared range.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
