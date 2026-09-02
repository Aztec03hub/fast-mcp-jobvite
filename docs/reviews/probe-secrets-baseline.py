#!/usr/bin/env python3
"""End-to-end arms for `scripts/check-secrets-baseline.py`, in a scratch tree.

    uv run --no-project --with detect-secrets==1.5.0 python \
        docs/reviews/probe-secrets-baseline.py

**WHY THIS IS A SEPARATE FILE FROM THE CHECKER'S `--controls`.** Those
controls exercise the comparison with synthetic dictionaries: fast, no
scanner, wired into `ci.yml`. They cannot answer the question that
actually matters, which is whether the REAL scanner driving the REAL
checker goes red on a new secret and stays green when a line moves. And
a control that shares a file with its subject shares its author's blind
spot - three of four mutants have survived a `--self-test` in this
repository before. So this probe drives the checker as a subprocess and
carries an AMPUTATION arm the checker cannot carry about itself.

**IT NEVER TOUCHES THIS REPOSITORY.** Every arm runs in a temporary
directory holding a copy of the checker, its own generated baseline and
one sample file. Nothing here writes inside the checkout, so an
interrupted run leaves nothing behind to restore - which matters,
because `SIGKILL` runs no `finally` and this project has already lost a
mutation to that.

**THE PLANTED SECRETS EXIST ONLY AT RUNTIME, AND THAT IS STRUCTURAL.**
A file that contains a literal secret-shaped line would be found by the
very scan it is testing, so committing this probe would add an unaudited
finding to `.secrets.baseline` and turn the gate red - the recursion
this repository has already measured on an exemption marker, where the
most careful writers expanded the hole fastest. Every planted value here
is CONCATENATED from fragments at runtime, so no line of this file
matches a detector and the recursion cannot occur at all. A control for
that would be weaker than the structure; the proof is that the gate is
green on the commit that adds this file.

**THE ARMS**

    A1  a recorded line number MOVES        -> exit 0   (the whole point)
    A2  a genuinely new secret appears      -> exit 1   (the gate still bites)
    A3  a recorded finding is DELETED       -> exit 0, and says STALE
    A4  the digest is AMPUTATED from the key -> A2 goes GREEN

A4 is what makes A2 evidence. Without it, A2 passing is consistent with
a checker that fails on absolutely anything.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "scripts" / "check-secrets-baseline.py"

#: Assembled at runtime. See the docstring: a literal here would be a
#: finding in this file, and the gate would refuse the probe that proves
#: the gate works.
_KEYWORD = "pass" + "word"
_VALUE_ONE = "PROBE" + "-SYNTHETIC-ONE-" + "NOT-A-CREDENTIAL"
_VALUE_TWO = "PROBE" + "-SYNTHETIC-TWO-" + "NOT-A-CREDENTIAL"


def _plant(value: str) -> str:
    """One secret-shaped line, built rather than written."""
    return f'{_KEYWORD} = "{value}"\n'


def _run(cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    """Run the scratch tree's copy of the checker, as CI would."""
    return subprocess.run(
        [sys.executable, str(cwd / "scripts" / "check-secrets-baseline.py")],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _scratch(tmp: pathlib.Path, checker_source: str) -> pathlib.Path:
    """A tree with one planted secret, its own baseline, and the checker.

    It is a real git repository because `detect-secrets scan` picks its
    population with `git ls-files`: in a plain directory it finds NOTHING
    and reports an empty result at exit 0, which is a clean zero that
    explains itself. `A0` and the entry-count guard below exist so that
    zero can never be mistaken for a passing arm.
    """
    tree = tmp / "tree"
    (tree / "scripts").mkdir(parents=True)
    (tree / "scripts" / "check-secrets-baseline.py").write_text(checker_source)
    (tree / "sample.py").write_text("# a sample module\n" + _plant(_VALUE_ONE))
    subprocess.run(["git", "init", "-q", "."], cwd=tree, check=True)
    # ONLY `sample.py` IS TRACKED, so only `sample.py` is scanned. Adding
    # the checker copy here made the fixture hold 3 entries and then 2:
    # a file explaining a secret-keyword defect attracts that detector,
    # in its code and in its prose. The fixture must depend on what this
    # probe plants, not on how the checker's docstring is worded.
    subprocess.run(["git", "add", "sample.py"], cwd=tree, check=True)
    baseline = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan"],
        cwd=tree,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    (tree / ".secrets.baseline").write_text(baseline)
    return tree


def _recorded_line(tree: pathlib.Path) -> int:
    results = json.loads((tree / ".secrets.baseline").read_text())["results"]
    entries = [e for v in results.values() for e in v]
    if len(entries) != 1:
        raise SystemExit(
            f"scratch baseline holds {len(entries)} entries, expected exactly 1 - "
            "the probe's own fixture is wrong, so its arms would mean nothing"
        )
    return int(entries[0]["line_number"])


def main() -> int:
    if importlib.util.find_spec("detect_secrets") is None:
        print(
            "detect-secrets is not importable, so no arm can run. This probe "
            "must not report success it did not measure. Run it as:\n"
            "  uv run --no-project --with detect-secrets==1.5.0 python "
            "docs/reviews/probe-secrets-baseline.py",
            file=sys.stderr,
        )
        return 2

    checker_source = CHECKER.read_text()
    arms: list[tuple[str, bool, str]] = []

    with tempfile.TemporaryDirectory(prefix="probe-secrets-") as raw:
        tmp = pathlib.Path(raw)
        tree = _scratch(tmp, checker_source)

        before = _run(tree)
        arms.append(
            (
                "A0 the fixture starts clean",
                before.returncode == 0,
                f"exit {before.returncode}; the arms below would measure a "
                "broken fixture rather than the checker",
            )
        )
        recorded = _recorded_line(tree)

        # A1  MOVE THE LINE. Twenty comment lines above it, nothing else.
        sample = tree / "sample.py"
        sample.write_text("# pad\n" * 20 + sample.read_text())
        moved = _run(tree)
        now = recorded + 20
        drifted = _plant(_VALUE_ONE) in sample.read_text().splitlines(keepends=True)[
            now - 1
        ]
        arms.append(
            (
                "A1 a line number moving stays GREEN",
                moved.returncode == 0 and drifted,
                f"exit {moved.returncode}, recorded {recorded}, actually "
                f"{now}, drift confirmed={drifted}; this is the defect that "
                "kept the trunk red and it would be back",
            )
        )

        # A2  A GENUINELY NEW SECRET. A different synthetic, so a different
        #     digest - not the audited one moved somewhere else.
        sample.write_text(sample.read_text() + _plant(_VALUE_TWO))
        planted = _run(tree)
        arms.append(
            (
                "A2 a new secret turns it RED",
                planted.returncode == 1 and "UNAUDITED" in planted.stderr,
                f"exit {planted.returncode}; a secret nobody audited would "
                "reach a public remote with the gate green",
            )
        )

        # A3  DELETE THE AUDITED FINDING. Stale, and by decision a warning.
        sample.write_text("# a sample module\n")
        emptied = _run(tree)
        arms.append(
            (
                "A3 a removed finding WARNS and stays green",
                emptied.returncode == 0 and "STALE" in emptied.stdout,
                f"exit {emptied.returncode}; either the stale direction is "
                "invisible, or deleting a file turns the trunk red",
            )
        )

        # A4  AMPUTATION. Take the digest out of the key entirely, so the
        #     comparison can only see filenames. A2's planted secret lives
        #     in a file the baseline already records, so a checker keyed on
        #     the filename alone MUST let it through. If A2 still goes red
        #     here, A2 was never measuring the comparison.
        anchor = '        (filename, str(entry["type"]), str(entry["hashed_secret"]))'
        if checker_source.count(anchor) != 1:
            raise SystemExit(
                "the amputation anchor is not unique in the checker, so this "
                "arm would silently no-op - fix the anchor, do not skip A4"
            )
        amputated = _scratch(
            tmp / "amputated",
            checker_source.replace(anchor, "        (filename, filename, filename)"),
        )
        (amputated / "sample.py").write_text(
            (amputated / "sample.py").read_text() + _plant(_VALUE_TWO)
        )
        survived = _run(amputated)
        arms.append(
            (
                "A4 amputating the digest makes A2 GREEN",
                survived.returncode == 0,
                f"exit {survived.returncode}; A2 goes red with the comparison "
                "REMOVED, so A2 proves nothing about the comparison",
            )
        )

    failed = [a for a in arms if not a[1]]
    for name, ok, detail in arms:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -> {detail}"))
    print(f"probe-secrets-baseline: arms={len(arms)} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
