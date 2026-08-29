"""§8 #18: lifespan teardown runs on SIGTERM, on BOTH transports.

DESIGN.md:1340-1346. Three of the design's stated verification gaps
close only on this case: the upstream defect at PrefectHQ/fastmcp#4927,
the `os._exit(0)` workaround, and the uvicorn implementation detail §12
item 5 records.

**Asserted by the teardown SIDE EFFECT, never by the exit code.** A
process that dies uncleanly can still exit 0, so an exit-code assertion
would pass against exactly the failure this case exists to catch.

**Both transports, because they fail differently**
(DESIGN.md:1345-1346). The HTTP arm passes on teardown alone; **only the
stdio arm exercises the `os._exit(0)` half**, where teardown runs but
the process does not die because a non-daemon AnyIO worker thread blocks
interpreter shutdown. A single-transport test would have shipped that
bug.
"""

from __future__ import annotations

import ast
import json
import pathlib
import signal
import socket
import subprocess
import sys
import time

import pytest

from fast_mcp_jobvite.__main__ import EXIT_CONFIGURATION_REFUSED, EXIT_SOFTWARE
from tests.boot_process import (
    GRACE_SECONDS,
    clean_env,
    free_port,
    interpreter_of,
    run_entry,
    spawn_marker_server,
    wait_for_port,
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
    """The teardown side effect is seen after SIGTERM, both transports.

    Without `_install_shutdown_handler` the default disposition kills
    the process outright and the marker never gains its `closed` line,
    which is the resource leak the case is about.
    """
    proc, marker, output = spawn_marker_server(
        tmp_path, _env_for(transport), stdio=transport == "stdio"
    )
    assert "opened" in marker.read_text()
    assert "closed" not in marker.read_text()

    # DESIGN.md:1342-1344: resolve the INTERPRETER via
    # /proc/<pid>/cmdline rather than trusting that the pid we hold is
    # the process we signalled.
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
    """The stdio arm's failure: teardown runs, process survives.

    DESIGN.md:981-983 records that on stdio a non-daemon AnyIO worker
    thread blocks interpreter shutdown, so even an explicit
    `sys.exit(0)` never completes.

    **This arm repeats, and the repetition is not caution - it is a
    measured correction.** Amputating the whole `finally` block and
    running the full U1 suite twice against the amputated tree gave 1
    failed the first time and 2 failed the second: a SINGLE
    spawn-and-signal cycle detected the missing forced exit about half
    the time, because whether the AnyIO worker thread is still alive at
    interpreter shutdown is a race that machine load shifts. Run alone
    the same amputation went red 3 of 3. A one-cycle arm is therefore a
    coin flip on the exact property it exists to hold, and only
    amputation showed that - the equivalent mutation killed it every
    time.

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

    DESIGN.md:986-1025 is explicit that the mitigation this replaced was
    also called verified and was not. A shutdown case that reimplements
    the handler and the `finally` proves only that the test author can
    write them - so this asserts the entry script imports the shipped
    `main`, and that `main`'s own source still carries both halves.
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
    # PARSED, NOT GREPPED (R2-L-6). The sibling test below already made
    # this argument for this same file - "this module's own prose NAMES
    # the defect in order to warn about it, and a substring search
    # cannot tell the warning from the thing it warns against" - and
    # then this test grepped it anyway. `__main__.py`'s module docstring
    # discusses `os._exit(0)`, `os._exit(status)` and the SIGTERM
    # handler at length, so every assertion below was satisfiable by a
    # comment. The two `MARKER_ENTRY` assertions above stay substring
    # checks: those ARE string literals, and a substring search is the
    # right instrument for a string.
    tree = ast.parse(source)

    def _exit_calls() -> list[ast.Call]:
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_exit"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
        ]

    handler_installs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "signal"
        and len(node.args) == 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == "_term"
    ]
    assert handler_installs, "no signal.signal(..., _term) call in the shipped source"

    # The forced exit must be in a `finally`, not on the success path
    # only: DESIGN.md:996-1010 places it there so teardown completes
    # first. `Try.finalbody` is the structure; splitting on the text
    # "finally:" also matched the docstring's discussion of it.
    in_finally = [
        call
        for node in ast.walk(tree)
        if isinstance(node, ast.Try)
        for statement in node.finalbody
        for call in ast.walk(statement)
        if call in _exit_calls()
    ]
    assert in_finally, "no os._exit call inside a `finally`"

    # ADR-0018: the constant is the defect, not the call. A crash must
    # not report itself as a clean stop, so EVERY forced exit takes the
    # status the run earned. Stated as "no literal argument anywhere"
    # rather than "the string `os._exit(0)` is absent": `os._exit(1)`
    # and `os._exit( 0 )` both pass the substring form.
    literal_exits = [
        call
        for call in _exit_calls()
        if any(isinstance(a, ast.Constant) for a in call.args)
    ]
    assert literal_exits == [], (
        "a forced exit passes a literal status, not the earned one"
    )
    assert all(
        isinstance(a, ast.Name) and a.id == "status"
        for call in _exit_calls()
        for a in call.args
    ), "a forced exit passes something other than `status`"

    # The abnormal arm sets that status from the named constant.
    abnormal = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "status" for t in node.targets)
        and isinstance(node.value, ast.Name)
        and node.value.id == "EXIT_SOFTWARE"
    ]
    assert abnormal, "nothing assigns EXIT_SOFTWARE to the exit status"

    # R2-M-3: `assert "EXIT_SOFTWARE = 70" in source` was the ONLY thing
    # in the repository pinning either `sysexits.h` number to its value,
    # and it pinned it by grepping for its own assignment. Rewritten as
    # the real comparison, because a supervisor reads the NUMBER and not
    # our constant's name. Its sibling, `EXIT_CONFIGURATION_REFUSED`, is
    # pinned the same way in `test_boot.py` - it was pinned nowhere at
    # all, and 78 -> 1 survived the whole suite.
    assert EXIT_SOFTWARE == 70


def test_the_handler_does_not_read_ambient_state() -> None:
    """DESIGN.md:969-975: `getsignal(SIGINT)` is the defect.

    A backgrounded process inherits `SIGINT = SIG_IGN`, so the rejected
    one-liner installs "ignore SIGTERM" - in a container the process
    then never stops and is SIGKILLed after the grace period,
    guaranteeing no teardown at all. This asserts the shipped handler
    never reaches for it.
    """
    source = pathlib.Path(
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "fast_mcp_jobvite"
        / "__main__.py"
    ).read_text()
    # Parsed, not grepped: this module's own prose NAMES the defect in
    # order to warn about it, and a substring search cannot tell the
    # warning from the thing it warns against.
    tree = ast.parse(source)
    reads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "getsignal"
    ]
    assert reads == []
    # Positive control for the instrument: the same walk DOES find the
    # call that is there, so an empty result above is an absence and not
    # a broken matcher.
    installs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "signal"
    ]
    assert installs


# ======================================================================
# ADR-0018, discharged BY THE SIDE EFFECT.
# ======================================================================


def test_a_crashing_mcp_run_exits_70_read_from_the_process(
    tmp_path: pathlib.Path,
) -> None:
    """ADR-0018 and DESIGN.md:1015-1023, on the PROCESS's status.

    **The structural assertion above is not a discharge of this.** It
    parses `__main__.py` and finds an `os._exit(status)` call inside a
    `finally`, and `EXIT_SOFTWARE == 70`. Every one of those can hold
    while the process exits 0 - a stray `finally` above, a `status`
    rebound between the assignment and the exit, a swallowed exception -
    and this file's own opening paragraph says why that matters: a
    process that dies uncleanly can still exit 0, which is exactly why
    §8 #18 refuses to assert teardown by exit code. A defect ABOUT exit
    codes cannot be discharged by reading the source for one, parsed or
    grepped.

    So this forces `mcp.run` to fail for a real reason - a bound port,
    the cheapest one, and the one DESIGN.md:1021-1023 names - and reads
    the exit status the supervisor would read.
    """
    # Hold the port for the whole arm. The listen backlog is what makes
    # the child's bind fail rather than race.
    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen(1)
        port = int(held.getsockname()[1])

        env = clean_env(
            JOBVITE_MCP_TRANSPORT="http",
            JOBVITE_MCP_HOST="127.0.0.1",
            JOBVITE_MCP_PORT=str(port),
            JOBVITE_HTTP_TOKENS=TOKENS,
            JOBVITE_TOOLS="search_jobs",
            **V2,
        )
        result = run_entry(tmp_path, env)

    assert result.returncode == EXIT_SOFTWARE, (
        f"a crashing mcp.run reported {result.returncode}; "
        f"stderr:\n{result.stderr[-2000:]}"
    )
    # And it is a REAL failure, not a refusal wearing the same status:
    # the configuration was accepted and the bind is what broke.
    combined = result.stdout + result.stderr
    assert "address already in use" in combined
    assert result.returncode != EXIT_CONFIGURATION_REFUSED


def test_a_clean_stop_still_reports_zero(tmp_path: pathlib.Path) -> None:
    """The positive control for the arm above, on the same instrument.

    Without it, `assert returncode == 70` passes against a `main()` that
    returned 70 unconditionally, which is a different defect with the
    same green. The same construction on a FREE port, stopped with
    SIGTERM, must come back 0.
    """
    port = free_port()
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="http",
        JOBVITE_MCP_HOST="127.0.0.1",
        JOBVITE_MCP_PORT=str(port),
        JOBVITE_HTTP_TOKENS=TOKENS,
        JOBVITE_TOOLS="search_jobs",
        **V2,
    )
    proc, _marker, output = spawn_marker_server(tmp_path, env, stdio=False)
    assert wait_for_port("127.0.0.1", port)
    proc.send_signal(signal.SIGTERM)
    returncode = proc.wait(timeout=GRACE_SECONDS)
    assert returncode == 0, f"a clean stop reported {returncode}: {output.read_text()}"
