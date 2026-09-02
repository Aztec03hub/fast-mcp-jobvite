#!/usr/bin/env python3
"""Reproduce the environment in which M12 SURVIVED on CI, here.

TASK #243. CI run 33610211810, job "Harness U1 controls", reported

    [M12 no forced exit] SURVIVED (tests/test_shutdown.py::
    test_only_stdio_exercises_the_forced_exit stayed green)
    22/23 controls fired.

while the identical mutation on the identical commit killed that test
locally. This probe names the difference and drives it on demand.

**THE DIFFERENCE IS NOT THE MACHINE, IT IS WHEN THE SIGNAL LANDS.** The
stdio arm's original assertions observed a CONSEQUENCE of the forced
exit being removed: the process hangs, because a non-daemon AnyIO
stdin-reader thread is joined at interpreter shutdown. That thread is
created about 7.5 ms AFTER the lifespan writes its `opened` line, and
`spawn_marker_server` returns the instant `opened` appears. A SIGTERM
delivered inside that window finds a SINGLE-THREADED process: nothing
blocks interpreter shutdown, the mutant exits in milliseconds, and
every timing assertion passes. The thread count at the moment of the
signal is printed per cycle, so the arm is identified rather than
asserted.

Two arms, each runnable against a mutated or an intact tree:

    --tight   signal as soon as `opened` lands  (the runner's verdict)
    --loose   the 50 ms poll `spawn_marker_server` uses (this machine)

and two assertion sets:

    --old     the assertions this arm shipped with: exits inside the
              grace period, and the marker says `closed`
    --new     those, plus: the marker does NOT say `atexit`, which is
              written only by a normal interpreter shutdown and so is
              absent exactly when `os._exit` ran

Exit status is 0 when the named assertion set PASSES (the mutant would
survive) and 1 when it FAILS (the mutant dies), so the two are not
readable as one another.
"""

from __future__ import annotations

import argparse
import functools
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.boot_process import (  # noqa: E402
    GRACE_SECONDS,
    _die_with_parent,
    clean_env,
    write_marker_entry,
)


def _one_cycle(index: int, env: dict[str, str], *, tight: bool, new: bool) -> bool:
    """Run one cycle. True if the named assertion set PASSES."""
    work = pathlib.Path(tempfile.mkdtemp())
    entry = write_marker_entry(work)
    marker = work / "marker.txt"
    output = work / "output.txt"
    with output.open("wb") as sink:
        proc = subprocess.Popen(  # noqa: S603
            [sys.executable, str(entry), str(marker)],
            cwd=str(work),
            env=env,
            stdin=subprocess.PIPE,
            stdout=sink,
            stderr=subprocess.STDOUT,
            preexec_fn=functools.partial(_die_with_parent, os.getpid()),  # noqa: PLW1509
        )
    deadline = time.monotonic() + GRACE_SECONDS
    while time.monotonic() < deadline:
        if marker.exists() and "opened" in marker.read_text():
            break
        if not tight:
            time.sleep(0.05)
    else:
        proc.kill()
        proc.wait()
        print(f"  cycle{index}: the lifespan never opened - not a measurement")
        return False

    threads = len(list(pathlib.Path(f"/proc/{proc.pid}/task").iterdir()))
    proc.send_signal(signal.SIGTERM)
    started = time.monotonic()
    try:
        proc.wait(timeout=GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        print(f"  cycle{index}: threads@SIGTERM={threads} HUNG -> assertions FAIL")
        return False
    elapsed = time.monotonic() - started
    text = marker.read_text()

    verdicts = {
        "exited inside the grace period": elapsed < GRACE_SECONDS,
        "marker says closed": "closed" in text,
    }
    if new:
        verdicts["marker does NOT say atexit"] = "atexit" not in text
    failed = [name for name, ok in verdicts.items() if not ok]
    lines = ", ".join(text.split())
    print(
        f"  cycle{index}: threads@SIGTERM={threads} rc={proc.returncode} "
        f"exited in {elapsed:.2f}s marker=[{lines}] "
        f"-> {'PASS' if not failed else 'FAIL (' + '; '.join(failed) + ')'}"
    )
    return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    arm = parser.add_mutually_exclusive_group(required=True)
    arm.add_argument("--tight", action="store_true", help="signal inside the window")
    arm.add_argument("--loose", action="store_true", help="the 50 ms poll")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--old", action="store_true", help="pre-#243 assertions")
    which.add_argument("--new", action="store_true", help="with the atexit assertion")
    parser.add_argument("--cycles", type=int, default=5)
    args = parser.parse_args()

    # READS THE STATEMENT, NOT A MUTATION MARKER. M12 replaces the call
    # with `pass`, the amputation DELETES the whole `finally` - a marker
    # grep would have called the amputated tree INTACT, and did.
    forced_exit_present = (
        "\n        os._exit(status)\n"
        in (REPO_ROOT / "src" / "fast_mcp_jobvite" / "__main__.py").read_text()
    )
    print(
        f"tree: {'INTACT' if forced_exit_present else 'FORCED EXIT ABSENT'}   "
        f"arm: {'tight (runner-like)' if args.tight else 'loose (this machine)'}   "
        f"assertions: {'NEW' if args.new else 'OLD'}"
    )

    # The two credentials are a dict, not keyword arguments, for the
    # same reason tests/test_shutdown.py builds its `V2` that way: a
    # literal passed to a parameter named `..._SECRET` is S106.
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="stdio",
        JOBVITE_TOOLS="search_jobs",
        **{"JOBVITE_API_KEY": "k", "JOBVITE_API_SECRET": "s"},
    )
    passed = sum(
        _one_cycle(i, env, tight=args.tight, new=args.new) for i in range(args.cycles)
    )
    # THE VERDICT NAMES THE TREE IT RAN ON. "the mutant SURVIVES" over
    # an INTACT tree is not a result, it is a sentence about nothing,
    # and an earlier version of this line printed exactly that.
    subject = "the intact tree" if forced_exit_present else "the removed forced exit"
    if passed == args.cycles:
        print(
            f"VERDICT: assertions PASS {passed}/{args.cycles} - "
            f"{subject} is NOT caught by this set"
        )
        return 0
    print(
        f"VERDICT: assertions FAIL ({passed}/{args.cycles} passed) - "
        f"{subject} IS caught by this set"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
