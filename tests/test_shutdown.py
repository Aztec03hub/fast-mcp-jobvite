"""§8 #18: lifespan teardown runs on SIGTERM, on BOTH transports.

DESIGN.md:1337-1343. Three of the design's stated verification gaps close
only on this case: the upstream defect at PrefectHQ/fastmcp#4927, the
`os._exit(0)` workaround, and the uvicorn implementation detail §12 item 5
records.

**Asserted by the teardown SIDE EFFECT, never by the exit code.** A process
that dies uncleanly can still exit 0, so an exit-code assertion would pass
against exactly the failure this case exists to catch.

**Both transports, because they fail differently** (DESIGN.md:1342-1343).
The HTTP arm passes on teardown alone; **only the stdio arm exercises the
`os._exit(0)` half**, where teardown runs but the process does not die
because a non-daemon AnyIO worker thread blocks interpreter shutdown. A
single-transport test would have shipped that bug.
"""

from __future__ import annotations

import ast
import json
import pathlib
import signal
import subprocess
import sys
import time

import pytest

from tests.boot_process import (
    GRACE_SECONDS,
    clean_env,
    free_port,
    interpreter_of,
    spawn_marker_server,
)

TOKENS = json.dumps({"tok": ["jobs:read"]})
V2 = {"JOBVITE_API_KEY": "k", "JOBVITE_API_SECRET": "s"}


def _env_for(transport: str) -> dict[str, str]:
    extra = {}
    if transport == "http":
        extra = {
            "JOBVITE_MCP_PORT": str(free_port()),
            "JOBVITE_HTTP_TOKENS": TOKENS,
        }
    return clean_env(
        JOBVITE_MCP_TRANSPORT=transport,
        JOBVITE_TOOLS="search_jobs",
        **V2,
        **extra,
    )


@pytest.mark.parametrize("transport", ["stdio", "http"])
def test_sigterm_runs_lifespan_teardown(tmp_path: pathlib.Path, transport: str) -> None:
    """The teardown side effect is observed after SIGTERM, on both transports.

    Without `_install_shutdown_handler` the default disposition kills the
    process outright and the marker never gains its `closed` line, which is
    the resource leak the case is about.
    """
    proc, marker, output = spawn_marker_server(
        tmp_path, _env_for(transport), stdio=transport == "stdio"
    )
    assert "opened" in marker.read_text()
    assert "closed" not in marker.read_text()

    # DESIGN.md:1339-1341: resolve the INTERPRETER via /proc/<pid>/cmdline
    # rather than trusting that the pid we hold is the process we signalled.
    assert interpreter_of(proc.pid) == sys.executable

    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        pytest.fail(
            f"[{transport}] the process survived SIGTERM for "
            f"{GRACE_SECONDS}s. output:\n{output.read_text()}"
        )

    # THE ASSERTION THAT MATTERS. Not the exit code.
    assert "closed" in marker.read_text(), (
        f"[{transport}] the process exited without running lifespan "
        f"teardown. output:\n{output.read_text()}"
    )


def test_only_stdio_exercises_the_forced_exit(tmp_path: pathlib.Path) -> None:
    """The stdio arm's distinctive failure: teardown runs, process survives.

    DESIGN.md:979-981 records that on stdio a non-daemon AnyIO worker thread
    blocks interpreter shutdown, so even an explicit `sys.exit(0)` never
    completes.

    **This arm repeats, and the repetition is not caution - it is a measured
    correction.** Amputating the whole `finally` block and running the full
    U1 suite twice against the amputated tree gave 1 failed the first time
    and 2 failed the second: a SINGLE spawn-and-signal cycle detected the
    missing forced exit about half the time, because whether the AnyIO
    worker thread is still alive at interpreter shutdown is a race that
    machine load shifts. Run alone the same amputation went red 3 of 3.
    A one-cycle arm is therefore a coin flip on the exact property it
    exists to hold, and only amputation showed that - the equivalent
    mutation killed it every time.

    Three cycles, each required to exit inside the grace period.
    """
    cycles = 3
    for cycle in range(cycles):
        work = tmp_path / f"cycle{cycle}"
        work.mkdir()
        proc, marker, output = spawn_marker_server(work, _env_for("stdio"), stdio=True)
        proc.send_signal(signal.SIGTERM)
        started = time.monotonic()
        try:
            proc.wait(timeout=GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail(
                f"stdio survived SIGTERM on cycle {cycle}. "
                f"output:\n{output.read_text()}"
            )
        assert time.monotonic() - started < GRACE_SECONDS
        assert "closed" in marker.read_text()


def test_the_shipped_entry_point_is_what_the_case_exercises() -> None:
    """The arms above run `main()`, not a copy of it written in a test.

    DESIGN.md:984-1023 is explicit that the mitigation this replaced was also
    called verified and was not. A shutdown case that reimplements the
    handler and the `finally` proves only that the test author can write
    them - so this asserts the entry script imports the shipped `main`, and
    that `main`'s own source still carries both halves.
    """
    from tests.boot_process import MARKER_ENTRY

    assert "from fast_mcp_jobvite.__main__ import main" in MARKER_ENTRY
    assert "main(extra_lifespan=marker_lifespan)" in MARKER_ENTRY

    source = pathlib.Path(
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "fast_mcp_jobvite"
        / "__main__.py"
    ).read_text()
    assert "signal.signal(signal.SIGTERM, _term)" in source
    assert "os._exit(status)" in source
    # The forced exit must be in a `finally`, not on the success path only:
    # DESIGN.md:994-1008 places it there so teardown completes first.
    finally_block = source.split("finally:")[-1]
    assert "os._exit(status)" in finally_block
    # ADR-0018: the constant is the defect, not the call. A crash must not
    # report itself as a clean stop, so the status is the one the run earned
    # and the abnormal arm sets it. Asserting the ABSENCE of `os._exit(0)`
    # is what stops this reverting silently.
    assert "os._exit(0)" not in source
    assert "status = EXIT_SOFTWARE" in source
    assert "EXIT_SOFTWARE = 70" in source


def test_the_handler_does_not_read_ambient_state() -> None:
    """DESIGN.md:967-973: `getsignal(SIGINT)` is the defect, not the fix.

    A backgrounded process inherits `SIGINT = SIG_IGN`, so the rejected
    one-liner installs "ignore SIGTERM" - in a container the process then
    never stops and is SIGKILLed after the grace period, guaranteeing no
    teardown at all. This asserts the shipped handler never reaches for it.
    """
    source = pathlib.Path(
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "fast_mcp_jobvite"
        / "__main__.py"
    ).read_text()
    # Parsed, not grepped: this module's own prose NAMES the defect in order
    # to warn about it, and a substring search cannot tell the warning from
    # the thing it warns against.
    tree = ast.parse(source)
    reads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "getsignal"
    ]
    assert reads == []
    # Positive control for the instrument: the same walk DOES find the call
    # that is there, so an empty result above is an absence and not a broken
    # matcher.
    installs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "signal"
    ]
    assert installs
