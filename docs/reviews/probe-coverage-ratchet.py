#!/usr/bin/env python3
"""Prove the review-coverage ratchet fires in every direction it claims.

    uv run --frozen python docs/reviews/probe-coverage-ratchet.py

**WHY A RATCHET AT ALL (#151).** `check-review-coverage.py` used to
return 1 whenever any trunk commit was uncovered. On a trunk anyone is
still committing to that gate is red BY CONSTRUCTION: every merge adds
commits no round has yet examined. A gate that can never be green gets
switched off, and this repository has already watched 119 consecutive CI
failures go unread for exactly that reason.

So the gate now enforces a recorded SET - `review-coverage-backlog.txt`
- and fails on any DIFFERENCE from what it measures. That turns "is
everything reviewed?" (unanswerable yes) into "did the unread set change
without anyone saying so?" (answerable, and the thing worth gating).

**A SET, NOT A COUNT.** A count lets one commit entering and another
clearing cancel to zero. Arm CANCEL below is that exact case, and it is
the arm a count-based ratchet would fail.

**BOTH KINDS.** NONE (no round's range contains it) and PARTIAL (a round
claimed the range but not every file) are different facts and the
backlog records which. A commit moving NONE -> PARTIAL is real progress
and must not pass silently; arm KIND covers it.

**NOTHING IN THE TREE IS MODIFIED.** Every arm points `--backlog` at a
file in a temporary directory. The obvious way to write this probe is to
edit the real backlog and put it back, and a harness killed mid-row then
leaves the edit behind for the next run to blame on someone else - the
defect of #131 and #146, which I reproduced by hand tonight by timing
out my own probe and stranding its two plant files.

Exit 0 = every arm behaved as claimed. Exit 1 = one did not.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "docs" / "reviews" / "check-review-coverage.py"
BACKLOG = ROOT / "docs" / "reviews" / "review-coverage-backlog.txt"
BROKEN_INSTRUMENT = 3


def run(backlog: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """The checker, against one backlog file, never raising."""
    return subprocess.run(
        [sys.executable, str(CHECKER), "--backlog", str(backlog)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def entries(text: str) -> list[str]:
    """The backlog's data lines, comments and blanks dropped."""
    return [
        line
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main() -> int:
    """Run every arm against a temporary copy and report."""
    source = BACKLOG.read_text(encoding="utf-8")
    rows = entries(source)
    if len(rows) < 2:
        print(f"The backlog holds {len(rows)} entries. Arms that delete one")
        print("and flip another need at least two, and an arm that cannot")
        print("run must not report PASS. Exit 1.")
        return 1

    results: list[tuple[bool, str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)

        # BASELINE. The committed backlog must already agree with the
        # measurement, or every arm below is measuring a tree that was
        # broken before the probe touched it.
        copy = work / "baseline.txt"
        copy.write_text(source, encoding="utf-8")
        done = run(copy)
        results.append(
            (
                done.returncode == 0,
                "BASELINE",
                f"the committed backlog agrees with the trunk: exit"
                f" {done.returncode} (want 0)",
            )
        )

        # ENTERED. Delete a recorded line. The commit is still
        # outstanding, so it must be reported as having entered the
        # backlog unrecorded.
        dropped = rows[0].split()[0]
        copy = work / "entered.txt"
        copy.write_text(
            "\n".join(
                line for line in source.splitlines() if not line.startswith(dropped)
            ),
            encoding="utf-8",
        )
        done = run(copy)
        results.append(
            (
                done.returncode == 1 and dropped in done.stdout,
                "ENTERED ",
                f"dropping {dropped} is caught: exit {done.returncode}"
                f" (want 1), names it: {dropped in done.stdout}",
            )
        )

        # CLEARED. A sha that is not outstanding must not sit in the
        # backlog unnoticed, or the baseline grows stale in the
        # direction that flatters it.
        fake = "0000000"
        copy = work / "cleared.txt"
        copy.write_text(f"{source}\n{fake} NONE a commit that is not outstanding\n")
        done = run(copy)
        results.append(
            (
                done.returncode == 1 and fake in done.stdout,
                "CLEARED ",
                f"a stale entry is caught: exit {done.returncode}"
                f" (want 1), names it: {fake in done.stdout}",
            )
        )

        # CANCEL. One entry dropped AND one stale entry added. The
        # recorded COUNT is unchanged, so a count-based ratchet passes
        # here. Both errors must still be reported.
        copy = work / "cancel.txt"
        kept = [line for line in source.splitlines() if not line.startswith(dropped)]
        copy.write_text(
            "\n".join(kept) + f"\n{fake} NONE a commit that is not outstanding\n"
        )
        done = run(copy)
        results.append(
            (
                done.returncode == 1 and dropped in done.stdout and fake in done.stdout,
                "CANCEL  ",
                f"an entry and a clearance do NOT cancel: exit"
                f" {done.returncode} (want 1), names both:"
                f" {dropped in done.stdout and fake in done.stdout}",
            )
        )

        # KIND. Flip a recorded kind. NONE and PARTIAL are different
        # facts; recording the wrong one is a wrong record, not a
        # rounding error.
        flipped = next((r for r in rows if r.split()[1] == "PARTIAL"), None)
        if flipped is None:
            results.append(
                (False, "KIND    ", "no PARTIAL entry to flip - arm did not run")
            )
        else:
            sha = flipped.split()[0]
            copy = work / "kind.txt"
            copy.write_text(
                source.replace(flipped, flipped.replace("PARTIAL", "NONE", 1)),
                encoding="utf-8",
            )
            done = run(copy)
            results.append(
                (
                    done.returncode == 1 and sha in done.stdout,
                    "KIND    ",
                    f"PARTIAL recorded as NONE is caught: exit"
                    f" {done.returncode} (want 1), names it:"
                    f" {sha in done.stdout}",
                )
            )

        # MISSING. An absent baseline must not read as an empty one.
        # That is the failure mode where a gate reports full compliance
        # because its own record is gone.
        done = run(work / "does-not-exist.txt")
        results.append(
            (
                done.returncode == BROKEN_INSTRUMENT,
                "MISSING ",
                f"an absent backlog is a broken instrument: exit"
                f" {done.returncode} (want {BROKEN_INSTRUMENT})",
            )
        )

        # MALFORMED. A line whose kind is neither NONE nor PARTIAL must
        # refuse, not be skipped - skipping shrinks the baseline
        # silently, which is the same false green as MISSING.
        copy = work / "malformed.txt"
        copy.write_text(f"{source}\n1234567 MAYBE a kind that does not exist\n")
        done = run(copy)
        results.append(
            (
                done.returncode == BROKEN_INSTRUMENT,
                "MALFORM ",
                f"an unknown kind refuses rather than skipping: exit"
                f" {done.returncode} (want {BROKEN_INSTRUMENT})",
            )
        )

        # DUPLICATE. Two lines for one commit make the recorded count
        # disagree with the recorded set, and only one can be right.
        copy = work / "duplicate.txt"
        copy.write_text(f"{source}\n{rows[0]}\n")
        done = run(copy)
        results.append(
            (
                done.returncode == BROKEN_INSTRUMENT,
                "DUPLICAT",
                f"a repeated sha refuses: exit {done.returncode}"
                f" (want {BROKEN_INSTRUMENT})",
            )
        )

    for ok, arm, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {arm} {detail}")
    passed = sum(1 for ok, _, _ in results if ok)
    print(f"\n{passed}/{len(results)} arms passed.")
    print(f"Backlog entries the arms were drawn from: {len(rows)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
