#!/usr/bin/env python3
"""Task #152 - an anchor-landing outcome must not be discarded.

WHY THIS EXISTS, AND WHY IT IS NARROWER THAN THE TASK THAT ASKED FOR IT.

`scripts/lib/harness-result.sh:163` is the one `printf` that emits the
canonical HARNESS-RESULT line, and everything downstream starts from
what it ACTUALLY EMITS: the #120 census, the field-name checker,
`ci-harness-gate.sh`'s flag reader. So "which harnesses publish a
tally?" has always been answered by grepping OUTPUT - and a harness that
computes a tally and never prints it is invisible to every one of them.
#120 fixed what happens to a tally ONCE PRINTED. It said nothing about
one never printed.

#152 proposed deriving the EXPECTED publishers from each harness's
SHAPE and asserting set equality against the observed ones:
`check-*-controls.sh` publishes `fired=`, `-amputation.sh` publishes
`applied=`. THAT RULE WAS MEASURED AND IT IS WRONG, on 4 of the 6
harnesses it would have named:

  - `check-body-cap-amputation.sh` and `check-u15-gate-amputation.sh`
    `exit 1` on a non-landing row. `applied < rows` is IMPOSSIBLE at
    exit 0, so an `applied=` field would be a fabricated N/N - the exact
    thing `harness-result.sh:157-162` refuses ("a fabricated `fired=0/0`
    would be read as a harness that held zero controls - a false
    finding").
  - `check-suite-floor-amputation.sh` computes `fired`/`total`, which is
    a KILLED tally, not an anchor tally. The shape rule names the wrong
    FIELD.
  - `check-u1-boot-amputation.sh` verified anchors with `assert count ==
    1` inside 13 unguarded Python heredocs under `set -uo pipefail`. It
    had no landing tally to publish because it never CONSUMED the
    failure at all - a different and worse defect, which the shape rule
    would have papered over by demanding a field. Closed by #156, which
    also found the failure was never SILENT: the harness went red naming
    three correct tests as false instruments.

A rule that fires on N harnesses is a SEARCH. The wider rule "every
incremented counter must reach the canonical line" was also measured: 12
of 37 files, 11 of them the single `VACUOUS` class. #159 then ruled that
one out by reading every site - 10 of the 10 that compute a vacuity
counter already GATE on it at exit nonzero, so a published field would
have had no job. It is deliberately NOT gated here.

WHAT IS GATED IS THE ONE INVARIANT THAT SURVIVED READING EVERY SITE:

    A harness that diagnoses a per-row anchor-landing failure must not
    let that row continue silently. Either the branch is FATAL, or the
    harness publishes a named tally, so that the row reaches the
    canonical line as a short count.

Both arms are real: `exit` makes the invariant structural, a published
tally makes it counted. What is forbidden is the third option - print
prose, continue, and count the row as if its anchor had landed. That is
what `check-u4-client-amputation.sh` and `check-u3-audit-amputation.sh`
did, and `check-u4-client-amputation.sh:21` asserted a CI gate that read
the anchor tally while no counter, no field and no `--anchors-applied`
flag existed anywhere.

Exit codes: 0 clean, 1 findings, 2 the container came back empty or
unreadable. An instrument failure must never render as a clean tree.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# The vocabulary a harness uses to say an anchor did not land. Selected
# by
# reading all 17 `-amputation.sh` files, not guessed: these are the
# phrases
# that actually appear at a landing branch.
LANDING_DIAGNOSTIC = re.compile(
    r"DID NOT LAND|COULD NOT APPLY|ANCHOR NOT UNIQUE|ANCHOR MISSING",
    re.IGNORECASE,
)

# A harness publishes SOME named tally with this call.
# `harness_result_tally`
# validates the NAME itself (lib/harness-result.sh:113-126), so this
# cannot
# drift into accepting an unknown field.
#
# WHY ANY TALLY AND NOT `applied` SPECIFICALLY. The first draft of this
# checker
# demanded `applied=` and reported 26 findings across 14 files - the
# whole
# `-controls.sh` family. That was a SEARCH, not a diagnosis. A controls
# harness
# mutates in order to prove a control FIRES, and a mutation that does
# not land
# leaves `FIRED < TOTAL`, so the landing failure IS counted - in the
# `fired`
# tally, under the only name that fits its meaning. Demanding `applied=`
# there
# would have forced a second field with a fourth meaning into harnesses
# that
# already report the fact, which is the collapse
# lib/harness-result.sh:24-44
# exists to refuse.
#
# WHAT THAT LEAVES UNSETTLED, stated rather than gated: for a harness
# publishing `killed=$PASS/$((PASS + FAIL))`, a row that never landed
# may be
# counted in NEITHER `PASS` nor `FAIL`, which would shrink the
# denominator
# instead of failing the tally. That is a real question about 14 files
# and it
# was not settled by reading all of them, so it is reported, not
# enforced here.
PUBLISHES_TALLY = re.compile(r"^\s*harness_result_tally\s+\w+\s", re.M)

# How far past a diagnostic to look for the branch's disposition. Every
# landing
# branch measured is 1-4 lines long (`echo`, optional `echo`, optional
# restore
# `cp`, then the disposition), so 5 covers them with a line to spare.
DISPOSITION_WINDOW = 5
FATAL = re.compile(r"^\s*(exit\s+\d+|sys\.exit\(\d*\)|die\b)")
NONFATAL = re.compile(r"^\s*return\b")


def container() -> list[Path]:
    """Enumerate the container, never a hand-written list (#115).

    `scripts/lib/` holds the sourced library, not harnesses; it
    defines the diagnostics rather than emitting them.
    """
    out = subprocess.run(
        ["git", "ls-files", "scripts/*.sh"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [Path(f) for f in out if not f.startswith("scripts/lib/")]


def findings_for(path: Path) -> list[tuple[int, str]]:
    """Landing diagnostics whose branch neither exits nor is counted."""
    text = path.read_text()
    if PUBLISHES_TALLY.search(text):
        # The harness publishes a named tally, so a non-landing row
        # reaches
        # the canonical line as a short count for the gate to read. A
        # non-fatal branch is then legitimate. What this gate forbids is
        # a
        # landing failure in a harness that publishes NOTHING - where
        # the row
        # is counted in `rows=` exactly as if its anchor had landed, and
        # no
        # field anywhere records that it did not.
        return []

    lines = text.splitlines()
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not LANDING_DIAGNOSTIC.search(line):
            continue
        # A comment is prose ABOUT the diagnostic, not the diagnostic.
        # This
        # repo has measured five times that a grep for a defect pattern
        # finds
        # the comment forbidding it.
        if line.lstrip().startswith("#"):
            continue
        window = lines[i + 1 : i + 1 + DISPOSITION_WINDOW]
        if any(FATAL.search(w) for w in window):
            continue
        if any(NONFATAL.search(w) for w in window):
            out.append((i + 1, line.strip()))
    return out


def main() -> int:
    files = container()
    if not files:
        print(
            "::error::check-landing-published: the container `git ls-files "
            "'scripts/*.sh'` came back EMPTY.\n"
            "         That is an instrument failure, not a clean tree, so this "
            "exits 2 rather than 0.",
            file=sys.stderr,
        )
        return 2

    total = 0
    for path in sorted(files):
        for lineno, snippet in findings_for(path):
            total += 1
            print(
                f"::error file={path},line={lineno}::{path}:{lineno} "
                f"an anchor-landing failure is diagnosed and then discarded"
            )
            print(f"    {snippet}")
            print(
                "    The branch `return`s, so the row is counted as having run "
                "with an anchor that never landed."
            )
            print(
                "    FIX: either make the branch fatal (`exit 1`), or count "
                "landings and call"
            )
            print(
                '         `harness_result_tally applied "$APPLIED" "$ROWS"` so '
                "the gate can read"
            )
            print("         it with `--anchors-applied`.")

    scanned = len(files)
    published = sum(1 for p in files if PUBLISHES_TALLY.search(p.read_text()))
    print(
        f"check-landing-published: {scanned} scripts scanned, "
        f"{published} publish a tally, {total} finding(s)"
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
