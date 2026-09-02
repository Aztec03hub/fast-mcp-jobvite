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

**THE RATCHET HAS TWO INPUTS AND MY FIRST EIGHT ARMS PERTURBED ONE
(R1-H1).** Every arm but PLANT pokes the recorded backlog. The MEASURED
side comes from the review documents, and nothing tested it.

**PLANT DOES NOT ASSERT A REFUSAL, BECAUSE THERE IS NONE.** Measured:
one file holding `<!-- REVIEW-COVERS: 8695101..<trunk sha> -->` plus an
emptied backlog takes 63 outstanding commits to 0 and exits 0. That is
BY CONSTRUCTION and it is not closable here - the checker cannot tell a
round that read 263 commits from one that read none, which its own
docstring has always said. Both inputs are author-controlled; this is
bookkeeping, not an adversarial gate.

So PLANT pins what CAN be true: the defeat is silent in the exit code,
so the caveat must be LOUD in the output, on the green path as much as
the red one. It asserts exit 0 AND the presence of the "a declaration is
a claim by its author" sentence. Before R1-H1 that sentence printed only
on failure, so this exact scenario produced the strongest line in the
file - "Every trunk commit ... falls inside a declared round" - with
nothing qualifying it.

**MY FIRST VERSION OF THIS ARM WAS VACUOUS AND PASSED.** It planted
`8695101..origin/main`; the declaration regex requires hex, so the line
never parsed, the plant did nothing, and the arm went green on the 63
commits still entering. A control that passes because its own input was
malformed is the failure this whole directory exists to catch, and I
found it only by reading WHY the arm passed rather than THAT it did.

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

**BASELINE TESTS THE INSTRUMENT, NOT THE TRUNK'S CURRENCY (R1-M6).**
It builds a backlog from what the checker measures right now. My first
version asserted the COMMITTED backlog was current, which made this
control red after every push - a control red by construction, which is
the defect #151 removes, relocated one artifact over. Staleness is the
checker's job to report; a control's job is to prove the checker works.

Exit 0 = every arm behaved as claimed. Exit 1 = one did not.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REVIEWS = ROOT / "docs" / "reviews"
CHECKER = REVIEWS / "check-review-coverage.py"
BACKLOG = REVIEWS / "review-coverage-backlog.txt"
BROKEN_INSTRUMENT = 3

#: The whole container the ratchet measures. A declaration spanning it
#: covers every trunk commit at once, which is what makes it the useful
#: shape to plant.
CONTAINER_BASE = "8695101"


def run(
    backlog: pathlib.Path, reviews: pathlib.Path | None = None
) -> subprocess.CompletedProcess[str]:
    """The checker, against one backlog file, never raising."""
    extra = ["--reviews", str(reviews)] if reviews is not None else []
    return subprocess.run(
        [sys.executable, str(CHECKER), "--backlog", str(backlog), *extra],
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


def derive_backlog(work: pathlib.Path) -> str:
    """A backlog matching what the checker measures right now.

    Built by ASKING THE CHECKER what is outstanding and reformatting its
    own report, so the BASELINE arm tests the instrument rather than the
    trunk's currency. This is NOT a `--write-backlog`: it writes only
    into a temporary directory, and the committed backlog stays a human
    act in a diff. The distinction is the whole reason the checker has
    no such flag - see its docstring.
    """
    empty = work / "derive-empty.txt"
    empty.write_text("# nothing recorded\n", encoding="utf-8")
    reported = run(empty).stdout
    lines: list[str] = []
    for raw in reported.splitlines():
        parts = raw.split()
        if len(parts) >= 3 and len(parts[0]) == 7 and parts[1] in ("NONE", "PARTIAL"):
            lines.append(raw.strip())
    return "# derived for this arm only\n" + "\n".join(lines) + "\n"


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

        # BASELINE. Prove the CHECKER can reach exit 0 at all, so the
        # eight arms below are not all passing against an
        # already-broken instrument.
        #
        # IT DOES NOT ASSERT THE COMMITTED BACKLOG IS CURRENT (R1-M6).
        # My first version did, and that made this control RED AFTER
        # EVERY PUSH: the trunk gains commits, the committed backlog has
        # not been topped up yet, and the arm fails for a reason that is
        # not a defect in anything it tests. Wire that probe and you get
        # a control red by construction after every merge - which is the
        # exact defect #151 exists to remove, relocated one artifact
        # over. It is the same mistake as ratcheting NONE and leaving
        # PARTIAL, made a second time in the same afternoon.
        #
        # So the arm builds a backlog from what the checker measures
        # RIGHT NOW and requires exit 0 against that. Staleness is the
        # CHECKER's job to report, and it does; a control's job is to
        # prove the checker still works.
        current = work / "current.txt"
        current.write_text(derive_backlog(work), encoding="utf-8")
        done = run(current)
        results.append(
            (
                done.returncode == 0,
                "BASELINE",
                f"the checker reaches exit 0 against a backlog matching"
                f" what it measures: exit {done.returncode} (want 0)",
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

        # PLANT (R1-H1). A fabricated declaration over the whole
        # container, plus an emptied backlog. This is NOT refused - see
        # the docstring - so the arm pins the two things that must hold
        # anyway: the run is green, and it still says out loud that a
        # declaration is only a claim.
        #
        # THE HEAD MUST BE A RESOLVED SHA. The regex requires hex; my
        # first version planted `origin/main`, the line never parsed,
        # and the arm passed while measuring nothing.
        trunk = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short=7", "origin/main"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        copies = work / "reviews"
        shutil.copytree(REVIEWS, copies)
        (copies / "REVIEW-R999.md").write_text(
            f"<!-- REVIEW-COVERS: {CONTAINER_BASE}..{trunk} -->\n"
            "A round that read nothing at all.\n",
            encoding="utf-8",
        )
        copy = work / "emptied.txt"
        copy.write_text("# every entry removed\n", encoding="utf-8")
        done = run(copy, reviews=copies)
        landed = "Backlog measured now: 0" in done.stdout
        caveat = "a claim by its author" in done.stdout
        results.append(
            (
                landed and caveat and done.returncode == 0,
                "PLANT   ",
                f"a fabricated declaration clears the backlog by design"
                f" (measured 0: {landed}, exit {done.returncode}) and the"
                f" caveat still prints: {caveat}",
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
