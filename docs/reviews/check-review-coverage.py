#!/usr/bin/env python3
"""Report the commits on the trunk that NO review round has covered.

    python3 docs/reviews/check-review-coverage.py [--ref origin/main]

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

**WHY IT REFUSES TO GUESS.** Deriving a round's coverage from whatever
SHA its document happens to cite would **manufacture coverage for code
nobody read** and certify it forever - strictly worse than the gap,
because an absence you can see beats a false presence you cannot.

## PATHS, and why a range alone was not enough

Two reviewers found the same hole independently. A round is dispatched
over a commit range AND a path filter: R11 took `src tests docs/adr
docs/DESIGN.md`, R12 took `docs/reviews scripts .github`, over the SAME
45 commits. Union the ranges and ignore the paths, and **either
declaration alone makes all 45 read as covered** while half the files
were never opened. That is manufactured coverage arriving from the
AUTHOR's side rather than the inferrer's - the very thing the paragraph
above refuses.

So a declaration may name the paths it read:

    <!-- REVIEW-COVERS: f699f74..dad014e PATHS: docs/reviews scripts -->
    <!-- REVIEW-COVERS: 8695101..f699f74 -->        (no PATHS = all)

A commit counts as covered only when **every file it touches** is
claimed by some round whose range contains it. Two path-split rounds
compose; either alone leaves the commit PARTIALLY covered, reported
separately from untouched - a half-read commit and an unread one are
different facts and must not print the same.

Omitting PATHS still means the whole tree, so older declarations keep
working and the broad claim stays the default.

## Defects review R12 found in this file, and the fix for each

**THE CONTAINER BASE IS FIXED, NOT DERIVED (R12-H3).** It was
`min(declared bases)`, which made the metric MANIPULABLE IN THE WRONG
DIRECTION: deleting a declaration moved the base forward and dropped
`COVERED BY NOTHING` from 59 to 2. A gate whose number IMPROVES when you
remove a declaration teaches the behaviour it exists to prevent.

**THE TRUNK IS A NAMED REF, NOT `HEAD` (R12-H3, second half).** Under
`actions/checkout` HEAD is the PR's merge commit, so wiring it as-is
would turn every pull request red for its own not-yet-trunk commits.

**THE POPULATION IS A REGEX OVER EVERY `.md` HERE (R12-M4).** The glob
`*REVIEW-R*.md` silently missed `REVIEW-CODE-R2.md` - a real round, in
no bucket at all. Third pattern-shaped population loss in one day, in
the file written to enforce container thinking.

**AN EXEMPTION NEEDS A NON-EMPTY REASON (R12-M5), A GIT FAILURE EXITS 3
(R12-L3), AND TWO DECLARATIONS REFUSE (R12-N2).**

**WHAT IT STILL CANNOT DO.** It checks that a commit's files fall inside
some round's declared range and paths. It cannot check the round READ
them. A declaration is a claim by its author; this only makes the claim
explicit, total, and composable.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REVIEWS = ROOT / "docs" / "reviews"

#: The commit from which review coverage is claimed. **A CONSTANT, never
#: derived from the declarations** - see R12-H3. Moving it FORWARD hides
#: commits, so it changes only with a recorded reason.
CONTAINER_BASE = "8695101"

IS_REVIEW = re.compile(r"REVIEW.*-R\d+", re.IGNORECASE)
NOT_A_COMMIT_REVIEW = re.compile(r"^PLAN-REVIEW|REVIEW$", re.IGNORECASE)

DECLARATION = re.compile(
    r"^<!--\s*REVIEW-COVERS:\s*"
    r"(?P<base>[0-9a-f]{7,40})\.\.(?P<head>[0-9a-f]{7,40})"
    r"(?:\s+PATHS:\s*(?P<paths>[^>]*?))?\s*-->\s*$",
    re.MULTILINE,
)

#: Rounds that reviewed a UNIT at a tree state and have no range to
#: recover. **A blank reason is not an exemption** (R12-M5).
UNDECLARED_BY_HISTORY: dict[str, str] = {
    "REVIEW-CODE-R2.md": "reviewed U1/U3/U4 at a pinned SHA, not a range",
    "REVIEW-R3.md": "reviewed 'the seven merged units', not a range",
    "REVIEW-R4.md": "reviewed U5 at 555bad6, a tree state, not a range",
    "REVIEW-R5.md": "reviewed U6 at d0abd10, a tree state, not a range",
    "REVIEW-R6.md": "reviewed U7 at ec38835, a tree state, not a range",
    "REVIEW-R7.md": "reviewed U8/U9/U12/U10 at bc0f958, a tree state",
    "REVIEW-R8.md": "reviewed U14 at 2c6ff19, a tree state, not a range",
}
assert all(v.strip() for v in UNDECLARED_BY_HISTORY.values()), (
    "a blank reason is not an exemption"
)


#: Paths that are RECORDS OF WORK rather than the work, each with the
#: reason. A record is an account of something that already happened;
#: the thing it accounts for is reviewed where it lives. **A bare path
#: is refused: the reason IS the exemption**, the same shape every other
#: exemption in `docs/reviews/` uses.
#:
#: THIS IS A RULING, NOT A CONVENIENCE, and the line it draws is
#: narrow. `docs/briefs/` is deliberately NOT here: a brief INSTRUCTS an
#: agent and has carried substantive rulings (ADR-BATCH.md), so a wrong
#: brief produces wrong work rather than merely misdescribing it. Nor
#: are `pyproject.toml`, `.env.example`, `.pre-commit-config.yaml`,
#: `server.json` or `README.md` - dependencies, secret-class values,
#: hook config and the published manifest are load-bearing and stay in
#: scope.
RECORD_PATHS: dict[str, str] = {
    "CHANGELOG.md": (
        "a dated account of changes that are themselves reviewed where "
        "they live. Reviewing it means re-reading a summary of reviewed "
        "code, which is coverage theatre rather than coverage."
    ),
    "docs/worklogs": (
        "reports of measurements already made. The measurement's SUBJECT "
        "is in src/, tests/ or scripts/ and is covered there; the report "
        "is the record that it happened."
    ),
    "docs/plans": (
        "ruled a RECORD at 0ec4c85 (task #111) - not repointed, not "
        "rewritten, and the SHA that makes that safe is guarded. A record "
        "that must not change cannot meaningfully be re-reviewed."
    ),
}
assert all(v.strip() for v in RECORD_PATHS.values()), (
    "a blank reason is not an exemption"
)


def is_record(path: str) -> bool:
    """Is this path a record of work rather than the work itself?"""
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in RECORD_PATHS)


class Round:
    """One round's claim: which commits, and which paths it read."""

    def __init__(self, name: str, commits: set[str], paths: list[str]) -> None:
        """Empty `paths` means the whole tree - the broad default."""
        self.name = name
        self.commits = commits
        #: Empty means the WHOLE TREE - the broad, honest default.
        self.paths = paths

    def claims(self, path: str) -> bool:
        """Does this round's path filter cover `path`?"""
        if not self.paths:
            return True
        return any(
            path == claim or path.startswith(claim.rstrip("/") + "/")
            for claim in self.paths
        )


def git(*args: str) -> str:
    """Run git; return stdout, or exit 3.

    A broken instrument is not a finding and must not share an exit
    code with one (R12-L3).
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


def declared_rounds(docs: list[pathlib.Path]) -> tuple[list[Round], list[str]]:
    """Each document's claim, and the documents declaring none."""
    rounds: list[Round] = []
    undeclared: list[str] = []
    for path in docs:
        found = DECLARATION.findall(path.read_text(encoding="utf-8"))
        if len(found) > 1:
            print(f"\n{path.name} carries {len(found)} REVIEW-COVERS lines.")
            print("Only the first would be read. Refusing rather than")
            print("picking one. Exit 2.")
            raise SystemExit(2)
        if not found:
            undeclared.append(path.name)
            continue
        base, head, raw_paths = found[0]
        commits = set(git("rev-list", f"{base}..{head}").split())
        paths = raw_paths.split()
        rounds.append(Round(path.name, commits, paths))
        claim = " ".join(paths) if paths else "(whole tree)"
        print(f"  DECLARED  {path.name}: {base}..{head}")
        print(f"            {len(commits)} commits, paths: {claim}")
    return rounds, undeclared


def main() -> int:
    parser = argparse.ArgumentParser(description="review coverage")
    parser.add_argument(
        "--ref",
        # origin/main, NOT main (R15-H1). R12-H3 moved this off HEAD
        # for the right reason - under actions/checkout, HEAD is the
        # PR's merge commit - and stopped one step short. That action
        # also leaves a DETACHED HEAD and creates NO local `main`.
        #
        # Reproduced in an init+fetch+detach clone, the shape the
        # action actually leaves: `main` does not resolve, `origin/main`
        # does, and this checker then exits 3, the code it reserves for
        # a BROKEN INSTRUMENT. Wiring the gate with the old default
        # would have failed every PR with "broken instrument" and
        # taught nobody anything. The docstring has said origin/main
        # since this file was written; only the default disagreed.
        #
        # Pinned by docs/reviews/probe-coverage-ref-resolves.py, whose
        # first version was VACUOUS - it ran the source tree's copy
        # with cwd set to the clone, and this checker derives its repo
        # from __file__, not the working directory.
        default="origin/main",
        help="trunk ref; never HEAD - under checkout that is a merge commit",
    )
    args = parser.parse_args()

    docs, skipped = review_documents()
    print(f"Review documents in the population: {len(docs)}")
    print(f"Excluded, with a reason: {len(skipped)}")
    if not docs:
        print("MATCHED ZERO review documents. An empty population reports")
        print("full coverage, which would mean nothing. Exit 2.")
        return 2

    rounds, undeclared = declared_rounds(docs)

    unexplained: list[str] = []
    for name in sorted(undeclared):
        reason = UNDECLARED_BY_HISTORY.get(name, "").strip()
        if reason:
            print(f"  HISTORIC  {name}: no range - {reason}")
        else:
            unexplained.append(name)
            print(f"  UNDECLARED {name}: no REVIEW-COVERS, and no reason")

    if not rounds:
        print("\nNo document declares a range, so nothing can be checked.")
        return 2

    trunk = git("rev-list", f"{CONTAINER_BASE}..{args.ref}").split()
    untouched: list[str] = []
    partial: list[tuple[str, list[str]]] = []
    records_skipped = 0
    for sha in trunk:
        claiming = [r for r in rounds if sha in r.commits]
        if not claiming:
            untouched.append(sha)
            continue
        files = git("show", "--name-only", "--pretty=format:", sha).split()
        unread = [
            f
            for f in files
            if not any(r.claims(f) for r in claiming) and not is_record(f)
        ]
        records_skipped += sum(
            1 for f in files if not any(r.claims(f) for r in claiming) and is_record(f)
        )
        if unread:
            partial.append((sha, unread))

    covered = len(trunk) - len(untouched) - len(partial)
    print(f"\nTrunk commits on {args.ref} since {CONTAINER_BASE}: {len(trunk)}")
    print(f"Fully covered - range AND every path: {covered}")
    print(f"PARTIALLY covered - some files claimed by nobody: {len(partial)}")
    print(f"COVERED BY NOTHING: {len(untouched)}")
    # COUNTED, NEVER SILENT. An exemption nobody reports is how a
    # population shrinks without anyone noticing, and this one was added
    # in the same session that found 22 commits reading as fully covered
    # because a path filter went undeclared.
    print(f"Record files skipped (not the work, an account of it): {records_skipped}")
    for name, why in sorted(RECORD_PATHS.items()):
        print(f"  RECORD   {name}: {why}")

    for sha in untouched[:15]:
        print(f"  NONE     {git('log', '-1', '--format=%h %s', sha)[:78]}")
    for sha, unread in partial[:10]:
        print(f"  PARTIAL  {git('log', '-1', '--format=%h %s', sha)[:62]}")
        print(f"           {len(unread)} file(s) unclaimed, e.g. {unread[0]}")

    if untouched or partial or unexplained:
        print(
            "\nNOTE: this proves a commit's files fall inside some round's\n"
            "declared range and paths, NOT that the round read them - a\n"
            "declaration is a claim by its author."
        )
        return 1

    print("\nEvery trunk commit is fully covered by a declared round.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
