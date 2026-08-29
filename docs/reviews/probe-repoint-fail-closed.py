#!/usr/bin/env python3
"""The REPOINT-EXEMPT check in repoint-design-citations.py fails CLOSED.

The defect this pins. `parse()` reads the cited line to see whether
it carries the `REPOINT-EXEMPT` marker. That read can fail - the
file may be unreadable, the report may name a line the file does not
have, the bytes may not decode. The original code caught OSError,
IndexError and UnicodeDecodeError and did nothing, so control fell
through to the repoint: "I could not tell whether this line is
exempt" resolved to "it is not exempt, rewrite it". That is a
fail-open on error in the tool that rewrites 867 citations.

Every row is falsifiable. Rows A-D drive `parse()` directly with a
synthetic report so each failure mode is reached deliberately. Row E
is the end-to-end arm the brief asks for: a real cited file is made
unreadable with chmod and the real tool is run, and it must refuse
rather than repoint. Rows C and D are the negative controls - if the
refusal were blanket they would fail, and a gate that refuses
everything is not a gate.

Exit 0 = every row behaved. Exit 1 = at least one row did not.
No dependencies. Nothing is written: the tool runs in DRY RUN.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TOOL = HERE / "repoint-design-citations.py"

_spec = importlib.util.spec_from_file_location("_repoint_probe", TOOL)
assert _spec is not None and _spec.loader is not None
repoint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(repoint)

FAILURES: list[str] = []


def row(name: str, ok: bool, detail: str) -> None:
    """Print one row's verdict and record it."""
    print(f"########## {name} {'PASS' if ok else 'FAIL'}: {detail}")
    if not ok:
        FAILURES.append(name)


def moved(rel: str, lineno: int) -> str:
    """One MOVED line in exactly the shape the checker emits."""
    # REPOINT-EXEMPT: these are example citations the probe WRITES,
    # not citations of anything. Repointing them corrupts the probe.
    return f"  MOVED: {rel}:{lineno}: DESIGN.md:100 -> DESIGN.md:200"


# A. The cited file does not exist at all -> OSError inside the read.
missing = "docs/reviews/__no_such_file_probe__.py"
assert not (REPO_ROOT / missing).exists(), "the probe's 'missing' path exists"
moves, unreadable = repoint.parse(moved(missing, 1))
row(
    "A. missing file -> OSError is REFUSED, not repointed",
    moves == {} and len(unreadable) == 1 and "UNREADABLE" in unreadable[0],
    f"moves={moves!r} unreadable={unreadable!r}",
)

# B. The report names a line the file does not have -> IndexError.
real = "docs/reviews/repoint-design-citations.py"
nlines = len((REPO_ROOT / real).read_text().splitlines())
moves, unreadable = repoint.parse(moved(real, nlines + 5000))
row(
    "B. line past EOF -> IndexError is REFUSED, not repointed",
    moves == {} and len(unreadable) == 1,
    f"file has {nlines} lines; moves={moves!r} unreadable={unreadable!r}",
)

# C. NEGATIVE CONTROL. A readable line with no marker must still be
#    collected for repointing. If this row fails the refusal is blanket
#    and the tool has been broken rather than fixed.
with tempfile.TemporaryDirectory(dir=REPO_ROOT) as td:
    plain = pathlib.Path(td) / "plain.txt"
    plain.write_text("a citation lives here: DESIGN.md:100\n")  # REPOINT-EXEMPT
    rel_plain = str(plain.relative_to(REPO_ROOT))
    moves, unreadable = repoint.parse(moved(rel_plain, 1))
    row(
        "C. readable, unmarked line IS repointed (negative control)",
        moves == {(rel_plain, 1): {(100, 100): (200, 200)}} and unreadable == [],
        f"moves={moves!r} unreadable={unreadable!r}",
    )

    # D. NEGATIVE CONTROL. The exemption itself must still work, and
    #    must be distinguishable from the refusal: excluded from
    #    moves AND absent from the unreadable list.
    marked = pathlib.Path(td) / "marked.txt"
    marked.write_text("DESIGN.md:100  # REPOINT" + "-EXEMPT\n")  # REPOINT-EXEMPT
    rel_marked = str(marked.relative_to(REPO_ROOT))
    moves, unreadable = repoint.parse(moved(rel_marked, 1))
    row(
        "D. REPOINT-EXEMPT line is skipped and is NOT called unreadable",
        moves == {} and unreadable == [],
        f"moves={moves!r} unreadable={unreadable!r}",
    )

# E. END TO END, the arm the brief asks for. Take a file the live report
#    really names, make it unreadable, and run the real tool. It must
#    refuse (exit 1, says UNREADABLE) and must NOT report repointing
#    anything.
SHA = "28be78adcca7f81e98307743640490f061fae3a9"
report_text = repoint.report(SHA)
cited = [
    m.group("file")
    for m in (repoint._MOVED.match(li) for li in report_text.splitlines())  # noqa: SLF001
    if m is not None
]
victim_rel = next(
    (c for c in cited if (REPO_ROOT / c).is_file() and c.endswith(".md")),
    None,
)
if victim_rel is None:
    row("E. end-to-end chmod refusal", False, "no cited .md file to use")
else:
    victim = REPO_ROOT / victim_rel
    before_mode = stat.S_IMODE(victim.stat().st_mode)
    before_bytes = victim.read_bytes()

    # A control on the control: the SAME command with the file readable
    # must NOT refuse, or row E proves nothing about the chmod.
    baseline = subprocess.run(
        [sys.executable, str(TOOL), SHA],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    row(
        "E0. readable baseline does NOT refuse (control on the control)",
        "UNREADABLE" not in baseline.stdout
        and re.search(r"\d+ citation\(s\) repointed", baseline.stdout) is not None,
        f"rc={baseline.returncode} tail={baseline.stdout.strip().splitlines()[-1:]!r}",
    )

    try:
        os.chmod(victim, 0o000)
        assert not os.access(victim, os.R_OK), "chmod did not make the file unreadable"
        run = subprocess.run(
            [sys.executable, str(TOOL), SHA],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
    finally:
        os.chmod(victim, before_mode)

    restored = os.access(victim, os.R_OK) and victim.read_bytes() == before_bytes
    # The victim is a file the UPSTREAM checker also has to read, so
    # chmod 000 kills the checker (it catches UnicodeDecodeError only)
    # and the report comes back empty. Before the fix that empty report
    # reached the parser and the tool blamed its own selector. It must
    # now say the checker failed, and say so by NAME.
    row(
        "E. unreadable cited file -> the tool REFUSES and repoints nothing",
        run.returncode == 1
        and "CHECKER FAILED" in run.stdout
        and "PermissionError" in run.stdout
        and "SELECTOR CONTROL" not in run.stdout
        and "citation(s) repointed" not in run.stdout,
        f"rc={run.returncode} victim={victim_rel} "
        f"tail={run.stdout.strip().splitlines()[-1:]!r}",
    )
    row(
        "E1. the probe restored the victim file (mode and bytes)",
        restored,
        f"mode={oct(before_mode)} bytes={len(before_bytes)}",
    )

print()
if FAILURES:
    print(f"  {len(FAILURES)} row(s) did not behave: {FAILURES}")
    raise SystemExit(1)
print("  every row behaved. The exempt check fails CLOSED.")
raise SystemExit(0)
