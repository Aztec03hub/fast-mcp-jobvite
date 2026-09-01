#!/usr/bin/env python3
"""Re-derive the unresolved section references outside the record paths.

    python3 docs/reviews/measure-xref-population.py

**THIS EXISTS BECAUSE A NUMBER NOBODY CAN RE-DERIVE IS NOT A
MEASUREMENT.** A review round of mine reported "115 bare continuations"
with no command recorded; the next reader tried five reasonable
definitions and got 0, 64, 77, 910 and 957, none of them 115. The
figure was unfalsifiable and had to be withdrawn. This script is the
command that produces #139's numbers, kept so the next person gets the
same answer, or a different one they can argue with.

**IT IS NOT A GATE and must not become one.** It reports; it does not
refuse. `check-cross-references.py` is the gate, and its population is
`DEFAULT_TARGETS`, deliberately narrower than this.

WHAT IT MEASURES: every tracked `*.md` outside the RECORD paths ruled at
`a1773e8`, with `docs/adr/*` resolved against `docs/DESIGN.md` because
an ADR cites the design's numbering rather than its own. Files whose
heading set is empty on both sides print as SKIP - those are the twelve
that would become failure LINES rather than skips if the gate's
population were widened, which is why widening costs 58 and not 46.
"""

import pathlib
import subprocess
import sys

sys.path.insert(0, "docs/reviews")
import importlib.util

spec = importlib.util.spec_from_file_location(
    "x", "docs/reviews/check-cross-references.py"
)
# REFUSE rather than proceed on a half-loaded module: if the checker
# cannot be imported this script would otherwise measure nothing and
# report a confident zero.
if spec is None or spec.loader is None:
    sys.exit("cannot load check-cross-references.py; refusing to report a count")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

root = pathlib.Path(".").resolve()
tracked = subprocess.run(
    ["git", "ls-files", "*.md"], capture_output=True, text=True, check=True
).stdout.split()
EXCL_DIRS = ("docs/worklogs/", "docs/plans/", "docs/reviews/", "docs/briefs/")
pop = [p for p in tracked if not p.startswith(EXCL_DIRS) and p != "CHANGELOG.md"]
total = 0
files = 0
for p in sorted(pop):
    text = (root / p).read_text()
    ref = "docs/DESIGN.md" if p.startswith("docs/adr/") else None
    try:
        miss = m.unresolved(text, ref, p)
    except ValueError as e:
        print(f"SKIP {p}: {e}")
        continue
    if miss:
        files += 1
        total += len(miss)
        print(f"\n=== {p}  ({len(miss)} unresolved) ===")
        lines = text.splitlines()
        for ln, r in miss:
            print(f"{p}:{ln}: §{r}  |  {lines[ln - 1].strip()[:200]}")
print(f"\nTOTAL: {total} unresolved across {files} files; population {len(pop)} files")
