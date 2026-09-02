#!/usr/bin/env python3
r"""THE COUNTERFACTUAL FOR #213: what would a SYNTAX SPLIT have missed?

    uv run --frozen python docs/reviews/probe-213-syntax-split.py
    uv run --frozen python docs/reviews/probe-213-syntax-split.py \
        --history

**THE QUESTION, AND WHY PROSE COULD NOT ANSWER IT.** The ruling in
`check-brief-report-references.py` refuses a syntax split - counting
only path-qualified citations, treating a bare basename as prose. R21-M3
established that the refusal's stated REASON is backwards: the six names
cited BOTH ways are caught by their path form, so they are evidence FOR
the split's safety. What the split would actually cost is the BARE-ONLY
residual, and nobody had measured that residual over anything but today.

`review-r21` said so itself and filed no task: *"how often a bare-only
citation has named a genuinely missing report across the project's
history ... is the counterfactual that would actually decide the
split."*
This file IS that counterfactual. It is a probe and not a paragraph
because prose about a measurement decays into a claim about one.

**THIS PROBE RULES NOTHING.** It prints two populations and their
difference. The ruling is Tier 0's.

**THE SELECTOR IS IMPORTED, NEVER RETYPED.** `REF` comes from the gate
itself. A probe that re-implements the pattern it is measuring answers a
question about the probe. The left boundary `(?<![A-Za-z0-9._-])` is
load-bearing - without it the pattern matches the TAIL of a longer name
and published a false finding once already - and importing is the only
way to be sure this file has it.

**WHAT "SPLIT GATE" MEANS HERE, STATED SO IT CAN BE CHECKED.** The
current gate's detection set is:

    {name cited anywhere in docs/briefs}  MINUS  {tracked basenames}

The split gate's is the same expression over a narrower citation set:

    {name cited WITH a docs/(reviews|worklogs)/ prefix at least once}

A name cited both ways is in BOTH sets, so it is caught either way. The
DIFFERENCE - what the split loses - is exactly the bare-only names that
are not tracked.

**A HISTORICAL REPLAY IS OVER TREES, NOT WORKING DIRECTORIES.** Every
commit is read with `git ls-tree`/`git show`, so the answer does not
depend on what happens to be checked out, and running this in a dirty
worktree cannot change the history rows. The `--history` pass walks
every commit that touched `docs/briefs`, first-parent order.

**THE RECORD FILE IS DELIBERATELY NOT SUBTRACTED IN THE HISTORY PASS.**
A recorded name is one a human already looked at and accepted; the
question here is what the SPLIT would stop the gate from ever showing a
human in the first place. Subtracting the record would hide exactly the
cases that matter - a name only ever reaches the record because the gate
went red on it. The TODAY pass prints both, so the two are comparable.
"""

from __future__ import annotations

import argparse

# The gate's module name has hyphens, so a plain import cannot reach it.
# Load it by path rather than copying its regex - see the docstring.
import importlib.util
import subprocess
from dataclasses import dataclass
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "brief_report_gate",
    Path(__file__).resolve().parent / "check-brief-report-references.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_GATE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GATE)
REF = _GATE.REF

ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    """Run git at ROOT and return stdout, raising loudly on failure.

    `check=True` on purpose: a git call that fails silently would make
    every population look empty, and an empty population reads exactly
    like a clean answer. That is the failure mode this project has
    recorded more than any other.
    """
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def scan(texts: dict[str, str]) -> tuple[set[str], set[str]]:
    """(names cited with a path at least once, names cited bare too).

    A name can be in both sets; that is the whole point of the
    measurement, so they are returned as overlapping sets rather than a
    partition. The caller derives BOTH/PATH-only/BARE-only.
    """
    with_path: set[str] = set()
    bare: set[str] = set()
    for text in texts.values():
        for m in REF.finditer(text):
            (with_path if m.group(1) else bare).add(m.group(2))
    return with_path, bare


def briefs_at(rev: str | None) -> dict[str, str]:
    """Every docs/briefs/**.md as of `rev`, or the working tree if None.

    Read from the OBJECT store for a rev. A working-tree read at a
    historical commit would silently answer about today.
    """
    if rev is None:
        base = ROOT / "docs/briefs"
        if not base.is_dir():
            raise SystemExit("::error::docs/briefs is not a directory - refusing")
        return {
            str(p.relative_to(ROOT)): p.read_text() for p in sorted(base.rglob("*.md"))
        }
    listing = [
        p
        for p in _git("ls-tree", "-r", "--name-only", rev, "docs/briefs/").split("\n")
        if p.endswith(".md")
    ]
    return {p: _git("show", f"{rev}:{p}") for p in sorted(listing)}


def tracked_at(rev: str | None) -> set[str]:
    """Tracked BASENAMES as of `rev` (working index if None).

    Basenames, not paths, because the gate's `dangling` branch asks the
    basename question. The path question is a separate branch
    (`misplaced`) that a syntax split does not touch.
    """
    if rev is None:
        raw = _git("ls-files", "-z").split("\0")
    else:
        raw = _git("ls-tree", "-r", "--name-only", rev).split("\n")
    return {p.rsplit("/", 1)[-1] for p in raw if p.strip()}


@dataclass(frozen=True)
class Measurement:
    """One revision's two detection sets and their difference.

    A dataclass and not a dict because every consumer below reads these
    by name, and a dict of `object` made the type checker unable to say
    anything about them - which is how a probe's own arithmetic stops
    being checked.
    """

    cited: set[str]
    both: set[str]
    path_only: set[str]
    bare_only: set[str]
    now: set[str]
    split: set[str]
    lost: set[str]


def measure(rev: str | None) -> Measurement:
    """The two detection sets and their difference at one revision."""
    with_path, bare = scan(briefs_at(rev))
    tracked = tracked_at(rev)
    all_cited = with_path | bare

    now_detects = {n for n in all_cited if n not in tracked}
    split_detects = {n for n in with_path if n not in tracked}
    return Measurement(
        cited=all_cited,
        both=with_path & bare,
        path_only=with_path - bare,
        bare_only=bare - with_path,
        now=now_detects,
        split=split_detects,
        lost=now_detects - split_detects,
    )


def _fmt(names: set[str]) -> str:
    return ", ".join(sorted(names)) if names else "(none)"


def today(rev: str | None) -> int:
    m = measure(rev)
    label = rev or "WORKING TREE"
    print(f"===== TODAY at {label} =====")
    print(f"Report names cited:         {len(m.cited)}")
    print(f"  cited BOTH ways:          {len(m.both)}  {_fmt(m.both)}")
    print(f"  cited PATH-qualified only:{len(m.path_only)}")
    print(f"  cited BARE only:          {len(m.bare_only)}  {_fmt(m.bare_only)}")
    print()
    print(f"CURRENT gate detects:       {len(m.now)}  {_fmt(m.now)}")
    print(f"SPLIT gate would detect:    {len(m.split)}  {_fmt(m.split)}")
    print(f"LOST to the split:          {len(m.lost)}  {_fmt(m.lost)}")

    record, _ = _GATE.read_record(_GATE.RECORD)
    recorded = {n for n in m.lost if n in record}
    live = m.lost - recorded
    print()
    print(
        f"Of those lost, already RECORDED as known-missing: "
        f"{len(recorded)}  {_fmt(recorded)}"
    )
    print(
        f"Of those lost, NEVER recorded (a LIVE detection): {len(live)}  {_fmt(live)}"
    )
    return 0


def history() -> int:
    """Replay both gates at every commit that touched docs/briefs.

    First-parent order so a merge counts once, and so the row sequence
    is the trunk a reader would walk. A commit is a ROW; the interesting
    column is `LOST`, the names the current gate would have shown a
    human and the split gate would have swallowed.
    """
    revs = [
        r
        for r in _git(
            "rev-list", "--first-parent", "--reverse", "HEAD", "--", "docs/briefs"
        ).split("\n")
        if r.strip()
    ]
    print(f"===== HISTORY: {len(revs)} first-parent commits touching docs/briefs =====")
    print(
        f"{'commit':9} {'cited':>5} {'both':>4} {'path':>4} {'bare':>4} "
        f"{'now':>4} {'split':>5} {'LOST':>4}  lost names"
    )
    ever_lost: dict[str, list[str]] = {}
    rows = 0
    for rev in revs:
        m = measure(rev)
        rows += 1
        for n in m.lost:
            ever_lost.setdefault(n, []).append(rev[:9])
        print(
            f"{rev[:9]} {len(m.cited):>5} {len(m.both):>4} "
            f"{len(m.path_only):>4} {len(m.bare_only):>4} "
            f"{len(m.now):>4} {len(m.split):>5} {len(m.lost):>4}  "
            f"{_fmt(m.lost)}"
        )

    print()
    print(f"ROWS: {rows}")
    print("A ZERO IN THE 'LOST' COLUMN ON EVERY ROW WOULD BE THE SPLIT'S CASE.")
    print("A NONZERO ROW IS A DETECTION THE SPLIT WOULD HAVE SWALLOWED.")
    print()
    print(f"DISTINCT NAMES EVER LOST TO THE SPLIT: {len(ever_lost)}")
    for n, where in sorted(ever_lost.items()):
        print(f"  {n}")
        print(f"    lost on {len(where)} commit(s), first {where[0]}, last {where[-1]}")
        # Whether the name EVER became tracked is the difference between
        # "a real report that arrived late", where the split only DELAYS
        # the detection - and "a name that never existed", where the
        # split loses it permanently. That distinction is the whole
        # counterfactual, so the query behind it must be exact.
        #
        # THE PATHSPEC HAD A FREE LEFT EDGE AND THIS PROBE PUBLISHED THE
        # FALSE ANSWER ITS OWN SUBJECT FILE IS ABOUT. `-- "*REVIEW-
        # CHECKLIST.md"` matches `docs/CODE-REVIEW-CHECKLIST.md`, so the
        # PHANTOM name - the one that has never existed anywhere, the
        # one `1985471` retracted - was reported as "YES, added". The
        # gate's own docstring records this exact truncation as a
        # published error, forty lines above the ruling being measured,
        # and the probe written to check that ruling reproduced it.
        # `:(glob)**/NAME` anchors at a directory boundary; `*NAME` does
        # not anchor at all.
        log = _git(
            "log", "--oneline", "--all", "--diff-filter=A", "--", f":(glob)**/{n}"
        ).strip()
        print(
            "    ever added to the repo? "
            + ("YES: " + log.splitlines()[0] if log else "NO - NEVER EXISTED")
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="counterfactual for the #213 syntax split")
    ap.add_argument(
        "--rev", default=None, help="measure at this rev (default: working tree)"
    )
    ap.add_argument(
        "--history", action="store_true", help="replay every docs/briefs commit"
    )
    args = ap.parse_args()
    if args.history:
        return history()
    return today(args.rev)


if __name__ == "__main__":
    raise SystemExit(main())
