#!/usr/bin/env python3
"""Apply `check-design-citations.py --since <sha>`'s MOVED lines.

The companion to `check-design-citations.py`. That script SAYS which
citations moved; this one MOVES them, from that script's own parsed
output rather than from anything retyped, because retyping a value just
read is the step that has failed repeatedly here.

It refuses to guess:

  - It ignores BROKEN lines entirely. Those are citations whose target
    line CHANGED, and only a human re-reading the subject can repoint
    them.
  - It ignores any line carrying the marker `REPOINT-EXEMPT`. A script
    that WRITES an example citation - a regex test string, a docstring
    illustrating the two forms - is not CITING anything, and repointing
    it corrupts the example silently. Measured: the first pass of this
    batch shifted three of `check-design-citations.py`'s own examples.
  - It keys on (file, line-the-citation-sits-on, old-range), never on a
    naive string replacement, because a single line can carry several
    citations and `DESIGN.md:<n>` can be a prefix of `DESIGN.md:<nn>`.
  - It asserts it parsed a non-zero number of MOVED lines, and fails
    loudly if a citation the report named is not where the report said
    it was.

Usage:
    python3 docs/reviews/repoint-design-citations.py <sha> # dry run
    python3 docs/reviews/repoint-design-citations.py <sha> --write

Exit 0 on success, 1 if anything did not line up. No dependencies.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "docs" / "reviews" / "check-design-citations.py"

#: {(old start, old end): (new start, new end)} for ONE cited line
Pairs = dict[tuple[int, int], tuple[int, int]]
#: {(file, line the citation sits on): Pairs}
MoveMap = dict[tuple[str, int], Pairs]

_CITATION = re.compile(r"DESIGN\.md:(\d+)(?:-(\d+))?")
_MOVED = re.compile(
    r"^\s*MOVED:\s+(?P<file>[^:]+):(?P<lineno>\d+): "
    r"DESIGN\.md:(?P<os>\d+)(?:-(?P<oe>\d+))? -> "
    r"DESIGN\.md:(?P<ns>\d+)(?:-(?P<ne>\d+))?\s*$"
)


class CheckerFailed(RuntimeError):  # noqa: N818 - a refusal, not an error
    """The checker did not run cleanly, so its report is not proof."""


def report(sha: str) -> str:
    """The checker's own output.

    Exit 1 is its normal state when moves exist.

    Which is exactly why the exit code cannot be the health check here.
    A crashed checker also exits 1, and this function used to keep only
    `.stdout`, so a traceback on stderr was discarded and an EMPTY
    report was indistinguishable from "nothing moved". Measured: chmod
    000 on one cited file raises PermissionError inside
    `check-design-citations.py` (it catches UnicodeDecodeError only),
    the report comes back empty, and the caller blames its own parser.
    The checker writes nothing to stderr in normal operation - 0 bytes
    over a run that emitted 970 MOVED lines - so anything on stderr is a
    fault, and a fault is refused.
    """
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--since", sha],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )
    if proc.stderr.strip():
        raise CheckerFailed(
            f"{CHECKER.name} exited {proc.returncode} and wrote to stderr, so "
            f"its report cannot be trusted. Nothing will be repointed.\n"
            f"{proc.stderr.rstrip()}"
        )
    return proc.stdout


def parse(
    text: str,
) -> tuple[
    dict[tuple[str, int], dict[tuple[int, int], tuple[int, int]]],
    list[str],
]:
    """Parse MOVED lines into a move map, plus the unruleable lines.

    The REPOINT-EXEMPT check FAILS CLOSED. If the cited file cannot be
    read, or does not have the line the report named, we do not know
    whether that line is exempt - and "unknown" must not resolve to "not
    exempt, go ahead and rewrite it". The old code swallowed OSError,
    IndexError and UnicodeDecodeError and fell through to the repoint,
    so an unreadable file was silently treated as non-exempt and got
    rewritten anyway. Unreadable lines are now collected and refused by
    the caller.
    """
    moves: dict[tuple[str, int], dict[tuple[int, int], tuple[int, int]]] = {}
    unreadable: list[str] = []
    for line in text.splitlines():
        m = _MOVED.match(line)
        if not m:
            continue
        cited_in = pathlib.Path(REPO_ROOT / m["file"])
        try:
            cited_line = cited_in.read_text().splitlines()[int(m["lineno"]) - 1]
        except (OSError, IndexError, UnicodeDecodeError) as exc:
            unreadable.append(
                f"  UNREADABLE: {m['file']}:{m['lineno']}: "
                f"{type(exc).__name__}: {exc}"
            )
            continue
        if "REPOINT-EXEMPT" in cited_line:
            continue
        old_s = int(m["os"])
        old_e = int(m["oe"]) if m["oe"] else old_s
        new_s = int(m["ns"])
        new_e = int(m["ne"]) if m["ne"] else new_s
        key = (m["file"], int(m["lineno"]))
        moves.setdefault(key, {})[(old_s, old_e)] = (new_s, new_e)
    return moves, unreadable


def apply(moves: MoveMap, write: bool) -> int:
    by_file: dict[str, dict[int, Pairs]] = {}
    for (rel, lineno), pairs in moves.items():
        by_file.setdefault(rel, {})[lineno] = pairs

    applied = missed = 0
    for rel, lines in sorted(by_file.items()):
        path = REPO_ROOT / rel
        text = path.read_text().splitlines(keepends=True)
        for lineno, pairs in lines.items():
            seen: set[tuple[int, int]] = set()

            # ruff B023: `sub` closes over the loop variables `pairs`
            # and `seen` without binding them. That is SAFE HERE and the
            # shape is deliberate: `sub` is never stored, never deferred
            # and never passed anywhere that outlives this iteration -
            # it is handed straight to `_CITATION.sub(...)` on the next
            # statement, which calls it synchronously and discards it
            # before the loop advances. `seen` is then read on the line
            # after that, still in the same iteration.
            #
            # It is fragile rather than wrong: collecting these
            # callables into a list to run later would silently make
            # every one of them use the LAST iteration's `pairs`, and
            # repoint 867 citations against the wrong map. If this loop
            # ever stops invoking `sub` on the very next line, bind the
            # two values as default arguments instead of restructuring
            # around it.
            def sub(m: re.Match[str]) -> str:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                target = pairs.get((start, end))  # noqa: B023 - see above
                if target is None:
                    return m.group(0)
                seen.add((start, end))  # noqa: B023 - see above
                ns, ne = target
                return f"DESIGN.md:{ns}" + (f"-{ne}" if ne != ns else "")

            original = text[lineno - 1]
            text[lineno - 1] = _CITATION.sub(sub, original)
            unseen = set(pairs) - seen
            if unseen:
                missed += len(unseen)
                print(f"  NOT FOUND: {rel}:{lineno}: the report named "
                      f"{sorted(unseen)} but that line does not carry it")
            applied += len(seen)
        if write:
            path.write_text("".join(text))

    print(f"\n  {applied} citation(s) repointed across {len(by_file)} file(s)"
          f"{'' if write else ' (DRY RUN, nothing written)'}")
    if missed:
        print(f"  {missed} the report named and the tree does not carry. NOTHING IS "
              f"TRUSTWORTHY.")
        return 1
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    sha = argv[0]
    try:
        text = report(sha)
    except CheckerFailed as exc:
        print(f"  CHECKER FAILED: {exc}")
        return 1
    moves, unreadable = parse(text)
    if unreadable:
        print("\n".join(unreadable))
        print(f"  {len(unreadable)} cited line(s) could not be read, so whether "
              "they carry REPOINT-EXEMPT is UNKNOWN. Refusing to repoint "
              "anything: an unknown must not resolve to 'not exempt'.")
        return 1
    total = sum(len(v) for v in moves.values())
    if total == 0:
        print("SELECTOR CONTROL: parsed 0 MOVED lines out of "
              f"{len(text.splitlines())} lines of report. The parser is broken, "
              "or there is genuinely nothing to move. Check the report by eye.")
        return 1
    print(f"  parsed {total} MOVED citation(s) from the checker's output")
    return apply(moves, write="--write" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
