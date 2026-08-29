"""§8 #10: an off-loopback bind without TLS refuses to START.

DESIGN.md:1297-1300.

Three High threat rows (C1-S1, C1-T1, C1-I1) rest on this refusal, and
none of them rested on a test before.

These arms run the **real process**. `test_config.py` proves the
validator raises; only a process arm proves the server *exits naming the
reason* rather than warning and continuing, which is what the case
actually says.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from fast_mcp_jobvite.__main__ import EXIT_CONFIGURATION_REFUSED
from tests.boot_process import (
    clean_env,
    free_port,
    run_entry,
    spawn_marker_server,
    wait_for_port,
)

TOKENS = json.dumps({"tok": ["candidates:read", "jobs:read", "feed:read"]})
V2 = {"JOBVITE_API_KEY": "k", "JOBVITE_API_SECRET": "s"}


def test_off_loopback_without_tls_exits_naming_the_reason(
    tmp_path: pathlib.Path,
) -> None:
    """§8 #10.

    No certificates configured here, the assertion undeclared.
    """
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="http",
        JOBVITE_MCP_HOST="0.0.0.0",  # noqa: S104
        JOBVITE_MCP_PORT=str(free_port()),
        JOBVITE_HTTP_TOKENS=TOKENS,
        JOBVITE_TOOLS="search_jobs",
        **V2,
    )
    result = run_entry(tmp_path, env)
    assert result.returncode == EXIT_CONFIGURATION_REFUSED
    combined = result.stdout + result.stderr
    # NAMING THE REASON: the variable an operator must set, and the host
    # that triggered it. An exit code alone is a refusal nobody can act
    # on.
    assert "JOBVITE_TLS_TERMINATED_BY_PROXY" in combined
    assert "0.0.0.0" in combined  # noqa: S104
    # And it exited rather than warning and continuing.
    assert "Uvicorn running" not in combined


def test_the_default_loopback_bind_starts_a_real_process(
    tmp_path: pathlib.Path,
) -> None:
    """Positive control for the REAL-PROCESS pair (DESIGN.md:1297-1300).

    Its partner is
    `test_off_loopback_with_the_assertion_declared_starts`. Named for
    its level because `test_config.py` holds the in-process validator
    pair, and the two used to share one name: a reader grepping it found
    "1 of 2" and "2 of 2" under a single identifier and reasonably read
    them as one matched pair (R3-N1).

    IMPLEMENTATION-PLAN.md:504.
    """
    port = free_port()
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="http",
        JOBVITE_MCP_PORT=str(port),
        JOBVITE_HTTP_TOKENS=TOKENS,
        JOBVITE_TOOLS="search_jobs",
        **V2,
    )
    proc, _marker, output = spawn_marker_server(tmp_path, env, stdio=False)
    try:
        assert wait_for_port("127.0.0.1", port), output.read_text()
    finally:
        proc.kill()
        proc.wait()


def test_off_loopback_with_the_assertion_declared_starts(
    tmp_path: pathlib.Path,
) -> None:
    """Positive control 2 of 2.

    The refusal is about TLS, not about binding.

    Binding the wildcard address is what an operator behind a
    terminating proxy actually does, so a refusal that fired here too
    would be a guard that refuses everything (DESIGN.md:1370-1372).
    """
    port = free_port()
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="http",
        JOBVITE_MCP_HOST="0.0.0.0",  # noqa: S104
        JOBVITE_MCP_PORT=str(port),
        JOBVITE_TLS_TERMINATED_BY_PROXY="true",
        JOBVITE_HTTP_TOKENS=TOKENS,
        JOBVITE_TOOLS="search_jobs",
        **V2,
    )
    proc, _marker, output = spawn_marker_server(tmp_path, env, stdio=False)
    try:
        assert wait_for_port("127.0.0.1", port), output.read_text()
    finally:
        proc.kill()
        proc.wait()


def test_http_without_tokens_exits_rather_than_serving_openly(
    tmp_path: pathlib.Path,
) -> None:
    """DESIGN.md:832-834, as a process arm.

    An open server is the alternative.
    """
    env = clean_env(
        JOBVITE_MCP_TRANSPORT="http",
        JOBVITE_MCP_PORT=str(free_port()),
        JOBVITE_TOOLS="search_jobs",
        **V2,
    )
    result = run_entry(tmp_path, env)
    assert result.returncode == EXIT_CONFIGURATION_REFUSED
    assert "JOBVITE_HTTP_TOKENS" in result.stdout + result.stderr


def test_a_missing_credential_exits_naming_the_variable(tmp_path: pathlib.Path) -> None:
    """DESIGN.md:913-917: a missing credential fails at BOOT.

    And the refusal names it.
    """
    env = clean_env(JOBVITE_TOOLS="search_jobs")
    result = run_entry(tmp_path, env)
    assert result.returncode == EXIT_CONFIGURATION_REFUSED
    assert "JOBVITE_API_KEY" in result.stdout + result.stderr


def test_the_refusal_status_is_the_sysexits_ex_config_number() -> None:
    """R2-M-3: a supervisor reads the NUMBER, not our constant's name.

    Every other assertion in the repository compares a return code
    against `EXIT_CONFIGURATION_REFUSED` imported from the module under
    test, so the constant is only ever compared with itself. Measured:
    `EXIT_CONFIGURATION_REFUSED = 78` -> `= 1` left the full suite green
    at 423 passed. 78 is `EX_CONFIG` from `sysexits.h`, and the whole
    point of it (`__main__.py:62-65`) is that it is DISTINCT from a
    generic failure - so `!= 1` is asserted as well as `== 78`, because
    1 is the specific value that erases the distinction.

    Its sibling `EXIT_SOFTWARE` is pinned in
    `test_shutdown.py::test_the_shipped_entry_point_is_what_the_case_exercises`.
    """
    assert EXIT_CONFIGURATION_REFUSED == 78
    assert EXIT_CONFIGURATION_REFUSED != 1


def test_an_unrecognised_tool_name_exits_naming_it(tmp_path: pathlib.Path) -> None:
    """DESIGN.md:931-936, as a process arm.

    Rather than as a validator call.
    """
    env = clean_env(JOBVITE_TOOLS="serch_jobs", **V2)
    result = run_entry(tmp_path, env)
    assert result.returncode == EXIT_CONFIGURATION_REFUSED
    assert "serch_jobs" in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("JOBVITE_MCP_PORT", "99999"),
        ("JOBVITE_MCP_TRANSPORT", "htp"),
        ("JOBVITE_MAX_RESULTS", "0"),
    ],
)
def test_a_constrained_field_is_refused_not_raised(
    tmp_path: pathlib.Path, variable: str, value: str
) -> None:
    """R2-M-2: pydantic's own refusals must use the same door.

    `Settings()` was constructed outside any `try`, and `__main__.py`
    catches only `ConfigurationError`, so the seven constrained fields
    exited **1 with a traceback** while every hand-written refusal
    exited 78. A supervisor cannot tell a mistyped port from a crash,
    which is the exact distinction `__main__.py:62-65` says 78 exists
    for.

    **`input_value` is asserted absent, and that is not cosmetic.**
    pydantic's error text echoes the offending value back, and the fix
    therefore rebuilds each reason from `loc` and `msg` rather than from
    `str(exc)`. No secret-class field carries a constraint today, so
    this is a property held before it is needed rather than after.
    """
    env = clean_env(JOBVITE_TOOLS="search_jobs", **V2)
    env[variable] = value
    result = run_entry(tmp_path, env)
    combined = result.stdout + result.stderr
    assert result.returncode == EXIT_CONFIGURATION_REFUSED, (
        f"exited {result.returncode}; stderr:\n{result.stderr[-2000:]}"
    )
    assert variable in combined, "the refusal does not name the variable to fix"
    assert "Traceback" not in combined
    assert "input_value" not in combined
    # Stdout is the JSON-RPC channel, as the arm below says.
    assert result.stdout == ""


def test_a_refusal_writes_nothing_to_stdout(tmp_path: pathlib.Path) -> None:
    """Stdout is the JSON-RPC channel; diagnostics go to stderr.

    A refusal message on stdout would be indistinguishable from a
    malformed JSON-RPC frame to a client that had already started
    reading.
    """
    env = clean_env(JOBVITE_TOOLS="search_jobs")
    result = run_entry(tmp_path, env)
    assert result.returncode == EXIT_CONFIGURATION_REFUSED
    assert result.stdout == ""
    assert "JOBVITE_API_KEY" in result.stderr


@pytest.mark.parametrize("transport", ["stdio", "http"])
def test_the_server_reaches_serving_on_both_transports(
    tmp_path: pathlib.Path, transport: str
) -> None:
    """The broadest positive control: the unit can actually start.

    DESIGN.md:795-798 records that this section's variables were found
    missing by someone trying to build against it and discovering the
    unit could not be started at all.
    """
    extra = {}
    if transport == "http":
        extra = {
            "JOBVITE_MCP_PORT": str(free_port()),
            "JOBVITE_HTTP_TOKENS": TOKENS,
        }
    env = clean_env(
        JOBVITE_MCP_TRANSPORT=transport,
        JOBVITE_TOOLS="search_jobs",
        **V2,
        **extra,
    )
    proc, marker, _output = spawn_marker_server(
        tmp_path, env, stdio=transport == "stdio"
    )
    try:
        assert "opened" in marker.read_text()
    finally:
        proc.kill()
        proc.wait()
