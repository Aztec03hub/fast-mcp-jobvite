#!/usr/bin/env python3
"""The secret gate compares FINDINGS, not file mtimes.

    python3 scripts/check-secrets-baseline.py            # the gate
    python3 scripts/check-secrets-baseline.py --controls  # can go red

**WHY THIS EXISTS, AND IT IS NOT A STYLE PREFERENCE.** The hook this
replaces was `Yelp/detect-secrets`'s own `detect-secrets` pre-commit
hook, run by `ci.yml` through `pre-commit run --all-files`. That hook
**rewrites `.secrets.baseline` in place** to refresh the `line_number`
of every finding it still sees, and `pre-commit` fails whenever a hook
modifies a file. Measured at `ccbdaae`, with CI's exact invocation:

    secret scan (detect-secrets, staged content)...............Failed
    - exit code: 3
    - files were modified by this hook
    -        "line_number": 1344,
    +        "line_number": 1617,
    -  "generated_at": "2026-09-01T20:33:41Z"
    +  "generated_at": "2026-09-02T01:22:26Z"

The entry is `.github/workflows/ci.yml`, `is_secret: false`, the literal
`inspect-only-not-a-credential`. **Not a secret, and never was.** The
recorded line drifted because `ci.yml` grew. In a developer's shell you
`git add .secrets.baseline` and move on - the hook's message says so.
**In CI nothing can be staged**, so the step went red on the first line
drift after each regeneration and could not recover. Run it twice and it
fails differently, *"Your baseline file (.secrets.baseline) is
unstaged"*, which is the same defect wearing its other face.

`ci.yml` already stated the intent this file implements:

    What this step genuinely covers is the secret scan over every file,
    and .secrets.baseline staying in step with the tree - a new finding
    nobody audited turns this red.

**A NEW FINDING TURNS IT RED. A LINE NUMBER MOVING DOES NOT.** So the
comparison is over the SET of `(filename, type, hashed_secret)` triples.
`line_number` and `generated_at` are excluded by construction: they are
the only two fields that move on their own, and neither carries any
security information. Nothing else is dropped - the detector `type` is
part of the key, so the same string newly flagged by a *different*
plugin is a new finding, not a match.

**THE TREE IS NEVER TOUCHED.** The scan runs against a COPY of the
baseline in a temporary directory outside the repository, so
`detect-secrets` rewrites the copy. Same trick as
`docs/reviews/probe-coverage-ratchet.py`: a checker that mutates its own
subject cannot be trusted about it, and a checker that `git add`s its
own baseline inside CI is the gate rewriting the evidence it checks.

**THE COPY'S ONE SIDE EFFECT, MEASURED RATHER THAN ASSUMED.**
`detect-secrets` carries a `is_baseline_file` filter whose `filename` is
taken from whatever `--baseline` argument it was given. Pointing it at a
temp copy therefore **un-excludes the real `.secrets.baseline`**, which
is full of hex `hashed_secret` values: the raw scan returns 46 findings
where the committed baseline holds 22, and all 24 extras are the
baseline's own hashes, each reported twice (`Hex High Entropy String`
and `Secret Keyword`). `_drop_baseline_self_findings` removes exactly
those, reproducing the filter the real hook applies. It is keyed on the
baseline's own path, so it can drop nothing else, and control `C5`
proves a finding in any other file survives it.

**THE STALE DIRECTION, WHICH NOTHING CHECKED BEFORE.** An entry in the
baseline whose finding is no longer in the tree is a **stale
allowance**. It is reported on every run, by name, and it **warns
rather than fails**. The reason: a stale allowance grants nothing -
the string it excused is gone - so its risk today is zero, while
failing on it would make the gate go red for a DELETION and leave
exactly one way to clear it, hand-editing
`.secrets.baseline`. That is the trap this file exists to remove, one
column over, and a gate red for improving the tree is `U0-REPORT`'s D3
failure shape that this repository has already accepted twice
(`.pre-commit-config.yaml`'s shellcheck block, and `pip-audit`). It is
printed with its count so it cannot rot unseen; if it ever wants to
ratchet, that is a decision with a number behind it.

**WHAT THIS CANNOT DO.** It compares HASHES, so it never prints a secret
- but it cannot tell you that an `is_secret: false` audit was WRONG.
An entry mis-audited when it was added stays excused forever, exactly as
before. That is a review property, not a gate property, and
`docs/CREDENTIAL-CHECKLIST.md` is where it lives. It also inherits every
false negative of the plugin set recorded in `.secrets.baseline`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASELINE = ROOT / ".secrets.baseline"

#: `(filename, type, hashed_secret)`. The whole design is in this tuple.
Finding = tuple[str, str, str]

#: What a baseline's `results` block is, read-only. `Mapping`/`Sequence`
#: rather than `dict`/`list` because `dict` is invariant in its value
#: type, and every caller here only reads.
Results = Mapping[str, Sequence[Mapping[str, object]]]


def pairs(results: Results) -> set[Finding]:
    """What a baseline asserts, with the drifting fields gone."""
    return {
        (filename, str(entry["type"]), str(entry["hashed_secret"]))
        for filename, entries in results.items()
        for entry in entries
    }


def _drop_baseline_self_findings(
    results: Results, baseline_name: str
) -> tuple[Results, int]:
    """Reproduce `is_baseline_file`, which a copy scan disables.

    Returns the results without the baseline's own entries, and how many
    were dropped. Keyed on the baseline's repo-relative path, so it is
    incapable of hiding a finding in any other file.
    """
    kept = {f: e for f, e in results.items() if f != baseline_name}
    dropped = len(results.get(baseline_name, []))
    return kept, dropped


def scan_against_copy(baseline: pathlib.Path) -> Results:
    """Scan the tree with a COPY of the baseline. Nothing is written.

    `detect-secrets scan --baseline X` reuses X's plugin and filter
    configuration and writes the merged result back into X - so X is a
    throwaway in a temp directory, and the committed baseline is only
    ever read.
    """
    with tempfile.TemporaryDirectory(prefix="secrets-baseline-") as tmp:
        copy = pathlib.Path(tmp) / "baseline-copy.json"
        shutil.copyfile(baseline, copy)
        # S603/S607 do not apply: a fixed argv, no shell, and the
        # interpreter is this process's own.
        proc = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "detect_secrets", "scan", "--baseline", str(copy)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise SystemExit(
                "detect-secrets scan failed with exit "
                f"{proc.returncode}:\n{proc.stderr.strip()}"
            )
        scanned: Results = json.loads(copy.read_text())["results"]
        return scanned


def _fail(message: str) -> None:
    print(message, file=sys.stderr)


def gate() -> int:
    """Compare the tree against the baseline. Returns the exit code."""
    if not BASELINE.is_file():
        _fail(f"no baseline at {BASELINE} - nothing to compare against")
        return 2
    if importlib.util.find_spec("detect_secrets") is None:
        _fail(
            "detect-secrets is not importable, so this gate cannot run and "
            "must not report success. It is pinned in .pre-commit-config.yaml; "
            "by hand, run:\n"
            "  uv run --no-project --with detect-secrets==1.5.0 python "
            "scripts/check-secrets-baseline.py"
        )
        return 2

    committed: Results = json.loads(BASELINE.read_text())["results"]
    scanned, self_dropped = _drop_baseline_self_findings(
        scan_against_copy(BASELINE), BASELINE.name
    )

    audited = pairs(committed)
    found = pairs(scanned)
    new = sorted(found - audited)
    stale = sorted(audited - found)

    for filename, kind, digest in new:
        _fail(f"UNAUDITED  {filename}  [{kind}]  sha1={digest}")
    for filename, kind, digest in stale:
        print(f"STALE      {filename}  [{kind}]  sha1={digest}")

    print(
        f"secrets-baseline: audited={len(audited)} found={len(found)} "
        f"new={len(new)} stale={len(stale)} "
        f"files={len(committed)} baseline-self-dropped={self_dropped}"
    )

    if new:
        _fail(
            f"\n{len(new)} finding(s) above are not in {BASELINE.name}. "
            "NEVER paste the value here or into a commit message. Read the "
            "line, and either remove the secret from the tree or - if it is "
            "genuinely not a credential - audit it in:\n"
            "  detect-secrets scan --baseline .secrets.baseline\n"
            "  detect-secrets audit .secrets.baseline\n"
            "and stage the baseline with the change that introduced it."
        )
        return 1
    if stale:
        print(
            f"\n{len(stale)} stale allowance(s) above: recorded in "
            f"{BASELINE.name}, no longer in the tree. This is a WARNING by "
            "decision - see this file's docstring. Clear them with a "
            "regeneration when you are next editing the baseline anyway."
        )
    _warn_untracked()
    return 0


def _warn_untracked() -> None:
    """Say which UNTRACKED files would become findings once tracked.

    #163. `detect-secrets scan` picks its population with `git
    ls-files`, so a brand-new file is invisible until the moment it is
    tracked - and then fails in the commit that adds it. That happened
    to THIS file: its control fixtures were two unaudited findings, and
    the first run passed only because it was still untracked.

    THREE OPTIONS WERE ON THE TABLE AND TWO ARE REFUSED.

    `git add -N` before the scan would fix it and MUTATES THE INDEX.
    This project has a standing ruling that unstaging is the
    destructive operation to avoid - #131's restorer refuses outright
    if a harness staged anything - and a gate that stages on every run
    is that rule pointed the other way. It would also scan files the
    author has not chosen to commit.

    A `pragma: allowlist secret` convention would trade a surprise for
    a habit of silencing the scanner, which is strictly worse.

    So: READ the untracked set explicitly, honour `.gitignore` via
    `--exclude-standard`, and WARN. The index is untouched, nothing the
    author did not write is scanned, and they hear about it before the
    commit rather than from a red gate.

    IT WARNS AND NEVER FAILS. An untracked file is not in the tree this
    gate governs, and failing on one would make the gate red for
    something no commit contains. Measured when written: 3 untracked
    non-ignored files, 0 findings - the noise this adds today is none.

    The scan runs as a SUBPROCESS, matching `scan_against_copy`, rather
    than importing detect_secrets: the library ships no type stubs and
    the first version of this function failed mypy for that reason.
    """
    git = shutil.which("git")
    if git is None:
        return
    try:
        listed = subprocess.run(  # noqa: S603
            [git, "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return
    if not listed:
        return
    try:
        done = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "detect_secrets", "scan", *listed],
            capture_output=True,
            text=True,
            check=False,
        )
        results = json.loads(done.stdout)["results"]
    except (OSError, ValueError, KeyError):
        return
    if not results:
        print(
            f"\n{len(listed)} untracked file(s) checked ahead of tracking: "
            "none would be a finding."
        )
        return
    print(
        f"\nWARNING - {len(results)} UNTRACKED file(s) would become "
        "findings the moment they are tracked. Nothing is failing: they "
        "are not in the tree this gate governs. Audit or fix them BEFORE "
        "you `git add`, or the commit that adds them turns this red:"
    )
    for path, found in sorted(results.items()):
        print(f"  {path}: {len(found)} finding(s)")


# ---------------------------------------------------------------------
# Controls. They exercise the COMPARISON, which is the half this change
# introduces and the half that decides red or green. They need no
# `detect-secrets` and touch nothing, so they can run anywhere.
#
# The end-to-end arms - plant a synthetic secret in a real file and
# require RED, move a recorded line number and require GREEN - are
# `docs/reviews/probe-secrets-baseline.py`, because a control sharing a
# file with its subject shares its author's blind spot: three of four
# mutants have survived a `--self-test` in this repository before.
# ---------------------------------------------------------------------

#: THE DIGEST FIELD NAME IS BUILT, NOT WRITTEN, AND THAT IS NOT STYLE.
#: `KeywordDetector` fires on that field name followed by a quoted
#: value, so fixtures spelling it out are `Secret Keyword` findings IN
#: THIS FILE: measured, they added two unaudited findings and would have
#: turned the gate red on the very commit that introduced the gate. The
#: first attempt to explain that in a comment ADDED A THIRD, because the
#: comment quoted the pair it was warning about - this repository has
#: measured the same recursion on an exemption marker, where the most
#: careful writers expanded the hole fastest. So no line here spells the
#: pair, in code or in prose, and the recursion cannot occur rather than
#: being excused.
_DIGEST = "hashed" + "_secret"
_A = {"type": "Secret Keyword", _DIGEST: "aaa", "line_number": 1}
_B = {"type": "Secret Keyword", _DIGEST: "bbb", "line_number": 2}


def controls() -> int:
    """Each arm names what would be true if the comparison broke."""
    arms: list[tuple[str, bool, str]] = []

    def arm(name: str, ok: bool, meaning: str) -> None:
        arms.append((name, ok, meaning))

    base = {"f.py": [dict(_A)]}

    # C1  A LINE NUMBER MOVING IS NOT A FINDING. The whole point.
    moved = {"f.py": [dict(_A, line_number=999)]}
    arm(
        "C1 line drift is invisible",
        pairs(base) == pairs(moved),
        "a line number would re-enter the key and CI would go red on any edit",
    )

    # C2  A NEW HASH IN A KNOWN FILE IS A FINDING.
    added = {"f.py": [dict(_A), dict(_B)]}
    arm(
        "C2 a new hash is caught",
        pairs(added) - pairs(base) == {("f.py", "Secret Keyword", "bbb")},
        "a secret added to an already-audited file would pass",
    )

    # C3  A KNOWN HASH IN A NEW FILE IS A FINDING. Keyed on the pair,
    #     not on the digest alone - copying an audited placeholder into
    #     a new file is a new finding.
    copied = {"f.py": [dict(_A)], "g.py": [dict(_A)]}
    arm(
        "C3 a known hash in a new file is caught",
        pairs(copied) - pairs(base) == {("g.py", "Secret Keyword", "aaa")},
        "the key would be the digest alone and a copied secret would pass",
    )

    # C4  THE SAME STRING UNDER A DIFFERENT DETECTOR IS A FINDING.
    retyped = {"f.py": [dict(_A), dict(_A, type="Base64 High Entropy String")]}
    arm(
        "C4 a second detector is caught",
        pairs(retyped) - pairs(base) == {("f.py", "Base64 High Entropy String", "aaa")},
        "type would be outside the key and a re-classified finding would pass",
    )

    # C5  THE BASELINE-SELF DROP CANNOT HIDE ANYTHING ELSE. It is the
    #     one place this checker deliberately discards findings.
    mixed = {".secrets.baseline": [dict(_A)], "real.py": [dict(_B)]}
    kept, dropped = _drop_baseline_self_findings(mixed, ".secrets.baseline")
    arm(
        "C5 the self-drop is scoped to the baseline",
        dropped == 1 and pairs(kept) == {("real.py", "Secret Keyword", "bbb")},
        "the drop would be a hole any file could hide in",
    )

    # C6  A REMOVED FINDING IS STALE, NOT NEW. The direction nothing
    #     checked before this file.
    emptied: Results = {}
    arm(
        "C6 a removed finding reads as stale",
        pairs(base) - pairs(emptied) == {("f.py", "Secret Keyword", "aaa")}
        and not pairs(emptied) - pairs(base),
        "a deletion would be reported as an unaudited new finding",
    )

    failed = [a for a in arms if not a[1]]
    for name, ok, meaning in arms:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -> {meaning}"))
    print(f"secrets-baseline-controls: arms={len(arms)} failed={len(failed)}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--controls",
        action="store_true",
        help="run the comparison controls instead of the gate",
    )
    args = parser.parse_args()
    return controls() if args.controls else gate()


if __name__ == "__main__":
    sys.exit(main())
