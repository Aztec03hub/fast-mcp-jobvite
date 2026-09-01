#!/usr/bin/env python3
"""Draw the #134 random sample of DESIGN.md citation SITES.

    python3 docs/reviews/sample-134-citations.py [--seed 134] [--n 40]

**Why a script and not a list in a report.** A sample recorded only as
prose is a CLAIM about a draw. This redraws it: same seed, same
container, same forty sites, so anyone can check the verdicts against
the sites they were actually written about.

**The container is `check-design-citation-shape.py`'s, imported, not
re-implemented.** That module's `code_files()` enumerates every tracked
`.py`/`.sh` from `git ls-files`, its `CITE` is the citation pattern, and
its `EXEMPT` marker skip is honoured here line-for-line. A second
selector that disagreed with the checker's would make the rate a rate of
a different population than the one #126 sampled.

**Why NOT `check-design-citations.py`'s selector**, which BRIEF #134
§C names: that one also scans `.md`, and reports 1917 citations across
202 files rather than 881 across 161. The extra thousand are prose -
reviews, worklogs, briefs - which cite the design AS IT STOOD when
they were written and must not be repointed. #126's 47-site population
and the brief's own "~880" arithmetic are both the CODE population.
Mixing the two puts numerator and denominator in different containers.

The draw is over SITES, not distinct ranges: each site is a separate
claim by a separate author, and a range cited five times can be right at
one site and wrong at another.

Exit 0 always; this prints, it does not judge.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import random
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def _shape_module() -> types.ModuleType:
    """Import the shape checker so its selector is REUSED, not copied.

    A second selector is a second population.
    """
    path = HERE / "check-design-citation-shape.py"
    spec = importlib.util.spec_from_file_location("_shape", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def container() -> list[tuple[str, int, int, int]]:
    """Every citation site as (relpath, line-it-sits-on, start, end)."""
    shape = _shape_module()
    sites: list[tuple[str, int, int, int]] = []
    for path in shape.code_files():
        for num, text in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if shape.EXEMPT in text:
                continue
            for match in shape.CITE.finditer(text):
                start = int(match.group(1))
                end = int(match.group(2) or match.group(1))
                sites.append((path.relative_to(ROOT).as_posix(), num, start, end))
    return sites


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=134)
    parser.add_argument("--n", type=int, default=40)
    args = parser.parse_args()

    sites = container()
    if not sites:
        print("PARSED ZERO SITES. The selector is broken; any sample is meaningless.")
        return 1

    print(f"container: {len(sites)} citation sites")
    print(f"seed: {args.seed}   n: {args.n}\n")

    # S311: this is a reproducible SAMPLE, not a secret. A seeded
    # `random.Random` is the point - the draw must be redrawable.
    rng = random.Random(args.seed)  # noqa: S311
    drawn = rng.sample(sorted(sites), args.n)
    for i, (rel, num, start, end) in enumerate(sorted(drawn), 1):
        cited = f"{start}" if start == end else f"{start}-{end}"
        print(f"{i:3}  {rel}:{num}  DESIGN.md:{cited}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
