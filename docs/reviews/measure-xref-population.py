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
# WHY EACH EXCLUSION, because R17-M1 found this list contradicting a
# live ruling and the docstring above it.
#
# docs/worklogs, docs/plans: RECORD paths in check-review-coverage.py.
#
# docs/reviews: RECORDS too, by the same argument and by #111 - a review
# is a dated account and is not repointed. MEASURED: 67 tracked files
# carrying 2824 section references, 34x the briefs population R17 named,
# and every one a quotation of what the design said AT THE TIME.
# Resolving them against today's design is ADR-0014's destructive-
# correction shape.
#
# docs/briefs: NOT a record. The ruling in check-review-coverage.py
# refuses it BY NAME, because a brief INSTRUCTS an agent. It is excluded
# from RESOLUTION for a different reason, and reported below rather than
# hidden.
EXCL_DIRS = ("docs/worklogs/", "docs/plans/", "docs/reviews/")
UNRESOLVABLE_REFERENT = ("docs/briefs/",)
pop = [p for p in tracked if not p.startswith(EXCL_DIRS) and p != "CHANGELOG.md"]
total = 0
files = 0
measured = 0
skipped: list[str] = []
no_referent: list[tuple[str, int]] = []
for p in sorted(pop):
    text = (root / p).read_text()
    # DEFER TO THE GATE'S OWN TABLE where it has an entry, so the two
    # instruments cannot drift apart. They already did once: adding
    # data-inventory.md and STANDARDS.md to DEFAULT_TARGETS made them
    # clean for the GATE while this script, hard-coding referent=None
    # for everything outside docs/adr/, still counted their 19
    # references as unresolved. Two numbers for one question is the
    # defect this file exists to prevent.
    ref = m.DEFAULT_TARGETS.get(
        p, "docs/DESIGN.md" if p.startswith("docs/adr/") else None
    )
    # A BRIEF HAS NO SINGLE REFERENT, MEASURED RATHER THAN ASSUMED.
    # R17-M1 proposed giving briefs one. Of the 83 section references in
    # docs/briefs, 55 name NO document on their line at all, and the
    # remaining 28 name FIVE different ones - DESIGN.md,
    # IMPLEMENTATION-PLAN.md, REVIEW-R15.md, U7-IMPL-REPORT.md,
    # STANDARDS.md. Hard-coding `docs/DESIGN.md` would resolve 55
    # against a document they may not mean and be outright wrong for at
    # least 6. So they are COUNTED AND NAMED as unresolvable rather than
    # silently scored clean - which is what the old exclusion did.
    if p.startswith(UNRESOLVABLE_REFERENT):
        # `m._REFERENCE` is the checker's OWN pattern, imported rather
        # than re-typed. My first version guarded it with `hasattr` and
        # a 0 fallback - which would have reported "0 references" for
        # every brief, the same vacuous zero this whole change removes,
        # introduced by the guard meant to make it safe.
        hits = len(m._REFERENCE.findall(text))  # noqa: SLF001
        if hits:
            no_referent.append((p, hits))
        continue
    try:
        miss = m.unresolved(text, ref, p)
    except ValueError as e:
        skipped.append(f"{p}: {e}")
        print(f"SKIP {p}: {e}")
        continue
    measured += 1
    if miss:
        files += 1
        total += len(miss)
        print(f"\n=== {p}  ({len(miss)} unresolved) ===")
        lines = text.splitlines()
        for ln, r in miss:
            print(f"{p}:{ln}: §{r}  |  {lines[ln - 1].strip()[:200]}")
# EVERY ZERO CARRIES ITS MEASURED COUNT. R17 nearly published "0 across
# 0 files" from this tool after an `except ValueError: continue` had
# swallowed the whole population. A zero over an empty population is the
# defect, not the result.
print(
    f"\nTOTAL: {total} unresolved across {files} files;"
    f" population {len(pop)}, MEASURED {measured}, skipped {len(skipped)}"
)
if no_referent:
    refs = sum(n for _, n in no_referent)
    print(
        f"NOT RESOLVED - no single referent: {len(no_referent)} files,"
        f" {refs} section references. These are NOT clean; nothing"
        f" checked them."
    )
    for path, n in sorted(no_referent):
        print(f"  {path}: {n}")
if measured == 0:
    print("MEASURED ZERO FILES. That is an instrument failure, not a clean tree.")
    raise SystemExit(2)
