#!/usr/bin/env python3
"""Run the README's Quickstart, taking the commands FROM the README.

    python3 docs/reviews/check-quickstart.py

`documentation/readme-standard.md:66` is `priority: required` and says
**"Quickstart parity: the Quickstart commands MUST be exercised by CI on
every merge to the default branch."** Nothing did. `tests/test_readme.py`
checks the README's structure, links, configuration table and tool count;
none of that runs a command.

**THE COMMANDS ARE PARSED OUT OF `README.md`, NOT COPIED HERE.** A copy
would be a second list: the README changes, the copy does not, and the
copy keeps passing. That is the defect this project has now recorded in
five places, so the checker reads the fenced block under `## Quickstart`
and runs what it finds.

**Two commands are deliberately skipped, and skipping is stated rather
than silent.** `git clone` cannot run against the repository it is
already inside, and `uv sync --frozen` is what CI has already done to
reach this point. Both are recognised by prefix and REPORTED as skipped;
an unrecognised command is a FAILURE, not a skip, so a new Quickstart
line cannot be quietly ignored.

**Exit code is not enough for the one command that matters.** `fastmcp
inspect` prints an ERROR and exits 0 when pointed at a path with no
server object - measured, and it is how a wrong factory path looks
identical to a working one. So the output is asserted too.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"

#: Prefixes that are correct to skip in CI, each with the reason a reader
#: needs. Anything not matching one of these is a failure.
SKIPPABLE: dict[str, str] = {
    "git clone": "cannot run against the repository it is already inside",
    "uv sync": "CI has already done this to reach this step",
}

#: What the inspect command must print. Exit code alone is not enough:
#: `fastmcp inspect` exits 0 while printing an ERROR when it finds no
#: server object at the given path.
MUST_PRINT = ("fast-mcp-jobvite", "Tools:")
MUST_NOT_PRINT = ("ERROR", "Traceback")


def quickstart_commands() -> list[str]:
    """The fenced bash block under `## Quickstart`, as whole commands."""
    text = README.read_text(encoding="utf-8")
    block = re.search(r"^## Quickstart\b.*?```bash\n(.*?)^```", text, re.S | re.M)
    if block is None:
        message = "no fenced bash block under '## Quickstart' in README.md"
        raise SystemExit(message)

    # Join continuation lines so a `\`-wrapped command is one command.
    joined = block.group(1).replace("\\\n", " ")
    return [line.strip() for line in joined.splitlines() if line.strip()]


def main() -> int:
    commands = quickstart_commands()
    if not commands:
        print("PARSED ZERO COMMANDS. A green here would mean nothing.")
        return 1

    print(f"Quickstart commands found in README.md: {len(commands)}")
    ran = 0

    for command in commands:
        skip = next((why for p, why in SKIPPABLE.items() if command.startswith(p)), None)
        if skip:
            print(f"  SKIP  {command[:58]:<58} {skip}")
            continue

        print(f"  RUN   {command[:58]}")
        result = subprocess.run(  # noqa: S602 - the command comes from our own README
            command, shell=True, cwd=ROOT, capture_output=True, text=True, check=False
        )
        ran += 1
        output = result.stdout + result.stderr

        if result.returncode != 0:
            print(f"        FAILED, exit {result.returncode}")
            print("\n".join(f"        {line}" for line in output.splitlines()[:15]))
            return 1

        for needle in MUST_PRINT:
            if needle not in output:
                print(f"        exit 0 but {needle!r} is not in the output.")
                print("        A Quickstart that exits 0 while printing the wrong")
                print("        thing is the failure this assertion exists for.")
                return 1
        for needle in MUST_NOT_PRINT:
            if needle in output:
                print(f"        exit 0 but the output contains {needle!r}.")
                return 1
        print("        ok")

    if ran == 0:
        print("EVERY command was skipped. The Quickstart is not being exercised.")
        return 1

    print(f"\nOK: {ran} Quickstart command(s) ran and printed what they should.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
