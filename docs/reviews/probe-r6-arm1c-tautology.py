# mypy: allow-untyped-defs, allow-untyped-calls
# ^ This file is a PROBE: its helpers build throwaway clients and
#   responders whose only caller is the arms below. mypy READS it -
#   that is the point of putting docs/reviews in `files` - and every
#   other strict check applies; only the two annotation knobs the ruff
#   per-file-ignores entry already relaxes for ANN are relaxed here, so
#   the two tools say the same thing about the same population.
"""R6: is probe-breaker-call-path.py arm 1c a real control?

Arm 1c searches the probe's OWN source for SCHEDULING_NAMES and passes
when every name is found. But SCHEDULING_NAMES is *defined in that same
source*, so each term is present as its own definition.

ARM A which of the 8 names survive when the SCHEDULING_NAMES tuple
       literal and every docstring/comment are removed? Those are
       the only ones the probe's code actually exercises.
ARM B a file that contains SCHEDULING_NAMES and NOTHING ELSE - zero
       scheduling - must FAIL a real positive control. Does arm 1c's
       predicate pass it?
"""

from __future__ import annotations

import ast
import io
import pathlib
import tokenize

PROBE = pathlib.Path("scripts/probe-breaker-call-path.py")
NAMES = (
    "threading",
    "Timer",
    "call_later",
    "call_at",
    "create_task",
    "ensure_future",
    "sched",
    "sleep",
)

src = PROBE.read_text()

# --- ARM A: strip comments, docstrings and the SCHEDULING_NAMES literal
# ----
out = []
for tok in tokenize.generate_tokens(io.StringIO(src).readline):
    if tok.type == tokenize.COMMENT:
        continue
    out.append(tok)
stripped = tokenize.untokenize(out)

tree = ast.parse(src)
doc_spans = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        assert node.end_lineno is not None
        doc_spans.add((node.lineno, node.end_lineno))

lines = src.splitlines()
keep = []
skip: set[int] = set()
for lo, hi in doc_spans:
    skip.update(range(lo, hi + 1))
# also drop the SCHEDULING_NAMES assignment block
in_names = False
for i, line in enumerate(lines, 1):
    if line.startswith("SCHEDULING_NAMES"):
        in_names = True
    if in_names:
        skip.add(i)
        if line.strip() == ")":
            in_names = False
for i, line in enumerate(lines, 1):
    if i not in skip:
        keep.append(line)
code_only = "\n".join(keep)

present_full = [n for n in NAMES if n in src]
present_code = [n for n in NAMES if n in code_only]

print("ARM A - names found in the probe's FULL source (what arm 1c reads):")
print(f"    {present_full}  ({len(present_full)}/8)")
print("ARM A - names found once docstrings/comments/the NAMES tuple are cut:")
print(f"    {present_code}  ({len(present_code)}/8)")
print(f"    exercised by nothing: {sorted(set(present_full) - set(present_code))}")

# --- ARM B: a file with the term list and no scheduling whatsoever
# --------
decoy = "SCHEDULING_NAMES = " + repr(NAMES) + "\n"
decoy_found = [n for n in NAMES if n in decoy]
print()
print("ARM B - a file containing ONLY the term list, zero scheduling code:")
print(f"    arm 1c's predicate finds {len(decoy_found)}/8 -> "
      f"{'PASSES (control is tautological)' if len(decoy_found) == 8 else
         'fails (control is real)'}")
