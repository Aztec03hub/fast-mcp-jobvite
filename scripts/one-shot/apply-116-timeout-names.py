#!/usr/bin/env python3
"""#116 one-shot: bind each harness timeout bound to ONE name.

The name is used by both the `timeout` call and the abort message
that explains it.

THE DEFECT. `timeout 900 ...` and `echo "...900s with no result..."`
are two copies of one decision. Change the call and the message
lies, at exit 0, in the exact output a reader turns to when
something has gone wrong.

THREE NAMES, NOT ONE. The arms are different decisions - baseline,
row, selector - and must stay separately adjustable even where two
of them share a value today. Measured on this tree: the row arm is
900 in 17 files and 300 in 14, so one global name would have
flattened a distinction that is already live.

Enumerates the container via `git ls-files`; never a hand-written
file list. Recorded as a one-shot: it has run, and the property it
established is held from here by scripts/check-timeout-literals.py.
"""

import re
import subprocess
import sys

INV = re.compile(r"\btimeout\b((?:\s+(?:-k\s+\d+\w?|-s\s+\S+|--\S+))*)\s+(\d+)\b")
FIG = re.compile(r"\b(\d+)s\b")
SET = re.compile(r"^set -[a-z]*uo pipefail\s*$")
VAR = {
    "BASELINE": "BASELINE_TIMEOUT",
    "ROW": "ROW_TIMEOUT",
    "SELECTOR": "SELECTOR_TIMEOUT",
}

Classified = tuple[dict[int, str], dict[int, str], dict[str, str]]


def arm_of(line: str) -> str:
    """Name the arm from the message that reports its timeout."""
    if "BASELINE HUNG" in line or "re-check HUNG" in line:
        return "BASELINE"
    if "SELECTOR PROBE" in line:
        return "SELECTOR"
    return "ROW"


def classify(lines: list[str]) -> Classified:
    """Pair each timeout call with the message that explains it.

    Returns `(inv index -> arm, echo index -> arm, arm -> value)`.
    """
    inv_arm: dict[int, str] = {}
    echo_arm: dict[int, str] = {}
    vals: dict[str, str] = {}
    pend: tuple[int, str] | None = None
    for i, line in enumerate(lines):
        m = None
        for m2 in INV.finditer(line):
            m = m2
        if m:
            pend = (i, m.group(2))
        if "echo" in line and FIG.search(line) and pend is not None:
            a = arm_of(line)
            inv_arm[pend[0]] = a
            echo_arm[i] = a
            if a in vals and vals[a] != pend[1]:
                sys.exit(
                    f"REFUSED: {a} arm has two values in one file: "
                    f"{vals[a]} and {pend[1]}"
                )
            vals[a] = pend[1]
            pend = None
    return inv_arm, echo_arm, vals


def main() -> None:
    """Rewrite every script in the container, then report the counts."""
    changed = inv_n = echo_n = 0
    # S603/S607: a fixed argv, no shell, and `git` from PATH.
    files = subprocess.check_output(  # noqa: S603
        ["git", "ls-files", "scripts/*.sh"],  # noqa: S607
        text=True,
    ).split()
    for f in files:
        with open(f) as fh:
            lines = fh.read().splitlines(keepends=True)
        inv_arm, echo_arm, vals = classify([x.rstrip("\n") for x in lines])
        if not vals:
            continue
        out: list[str] = []
        for i, line in enumerate(lines):
            new = line
            if i in inv_arm:
                m = None
                for m2 in INV.finditer(new):
                    m = m2
                if m is None:
                    sys.exit(f"REFUSED: anchor vanished at {f}:{i + 1}")
                s, e = m.span(2)
                new = new[:s] + f'"${VAR[inv_arm[i]]}"' + new[e:]
                inv_n += 1
            if i in echo_arm:
                name = VAR[echo_arm[i]]
                new = FIG.sub("${" + name + "}s", new, count=1)
                echo_n += 1
            out.append(new)
        idx = next(j for j, x in enumerate(out) if SET.match(x.rstrip("\n")))
        block = [
            "\n",
            "# Timeout bounds - each declared ONCE and interpolated into the abort\n",
            "# message that explains it, so a changed bound cannot leave prose "
            "behind\n",
            "# still quoting the old one. Three names because the arms are three\n",
            "# separate decisions, even where two of them share a value today.\n",
        ]
        for a in ("BASELINE", "ROW", "SELECTOR"):
            if a in vals:
                block.append(f"{VAR[a]}={vals[a]}\n")
        out[idx + 1 : idx + 1] = block
        with open(f, "w") as fh:
            fh.write("".join(out))
        changed += 1
    print(
        f"files rewritten: {changed}   timeout calls bound: {inv_n}   "
        f"messages derived: {echo_n}"
    )


if __name__ == "__main__":
    main()
