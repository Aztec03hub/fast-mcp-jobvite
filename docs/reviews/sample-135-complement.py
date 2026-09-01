#!/usr/bin/env python3
"""Draw a sample from the COMPLEMENT of #126's blank-ended population.

    python3 docs/reviews/sample-135-complement.py [--rev 26973a4^]
                                                  [--seed 135] [--n 20]

**The question this exists to answer.** BRIEF #134 asserted that ending
on a blank line and citing the wrong paragraph are INDEPENDENT
properties, and used that premise to project ~35 wrong citations across
881 from #126's *2* in 47 - a numerator this task measures as FOUR (see
the run's own output). REPORT #134 argues the premise is false -
#126's F1-F4 are all paragraph-boundary miscounts by the citing author,
so the blank-ended population would be ENRICHED for the very defect
being extrapolated, and 2/47 was never a base rate. Deciding it means
reading a sample of the sites that were NOT blank-ended and comparing.

**Why the draw is at `26973a4^` and not at `main`.** That is the tree on
which #126's 47 existed; the sweep at `26973a4` repaired them, so on any
later tree the population being compared against no longer exists and
the complement cannot be defined by subtraction. Both arms come
off ONE tree, and `docs/DESIGN-FREEZE.txt` reads `5d17cd7` at `26973a4^`
and at `main` alike, so both arms are judged against the same design.

The container, the citation pattern and the exemption-marker skip are
`check-design-citation-shape.py`'s, read at `--rev` rather than from the
working tree - a second selector would be a second population.

Exit 0 always: this prints a draw, it does not judge one.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import random
import subprocess
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def _shape_module() -> types.ModuleType:
    path = HERE / "check-design-citation-shape.py"
    spec = importlib.util.spec_from_file_location("_shape", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def sites_at(rev: str, shape: types.ModuleType) -> list[tuple[str, int, int, int]]:
    """Every citation site in the tracked `.py`/`.sh` files AT `rev`."""
    names = [
        n
        for n in _git("ls-tree", "-r", "--name-only", rev).split("\n")
        if n and pathlib.Path(n).suffix in shape.CODE_SUFFIXES
    ]
    found: list[tuple[str, int, int, int]] = []
    for name in sorted(names):
        for num, text in enumerate(_git("show", f"{rev}:{name}").split("\n"), 1):
            if shape.EXEMPT in text:
                continue
            for match in shape.CITE.finditer(text):
                start = int(match.group(1))
                end = int(match.group(2) or match.group(1))
                found.append((name, num, start, end))
    return found


def main() -> int:
    shape = _shape_module()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev", default="26973a4^")
    parser.add_argument("--seed", type=int, default=135)
    parser.add_argument("--n", type=int, default=20)
    args = parser.parse_args()

    freeze = _git("show", f"{args.rev}:docs/DESIGN-FREEZE.txt").strip()
    lines = shape.design_lines(freeze)

    sites = sites_at(args.rev, shape)
    if not sites:
        print("PARSED ZERO SITES. The selector is broken; any sample is meaningless.")
        return 1

    blank_end = [
        s
        for s in sites
        if (shape.classify(s[2], s[3], lines) or "").startswith("ends on a BLANK")
    ]
    complement = [s for s in sites if s not in blank_end]

    print(f"rev:        {args.rev} ({_git('rev-parse', '--short', args.rev).strip()})")
    print(f"design:     {freeze}, {len(lines)} lines")
    print(f"container:  {len(sites)} citation sites")
    print(
        f"blank-END:  {len(blank_end)}  <- #126's population. FOUR of them are "
        "wrong citations (F1-F4), not the 2 that #134 and BRIEF #134 both\n"
        "                carried: 2 is the count LEFT OPEN, not the count FOUND."
    )
    print(f"complement: {len(complement)}")
    print(f"seed: {args.seed}   n: {args.n}\n")

    # S311: a reproducible SAMPLE, not a secret. The seed is the point.
    rng = random.Random(args.seed)  # noqa: S311
    drawn = rng.sample(sorted(complement), args.n)
    for i, (rel, num, start, end) in enumerate(sorted(drawn), 1):
        cited = f"{start}" if start == end else f"{start}-{end}"
        print(f"{i:3}  {rel}:{num}  DESIGN.md:{cited}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
