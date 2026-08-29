"""The `FastMCP` instance and lifespan composition (DESIGN.md:958-960).

DESIGN.md:959-960 states "startup in order, teardown in strict reverse,
verified". That property had no test, and its two halves fail
differently: an out-of-order startup is usually visible, an out-of-order
teardown is usually not.
"""

from __future__ import annotations

import pathlib
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastmcp import Client, FastMCP
from fastmcp.server.lifespan import Lifespan, lifespan
from pydantic import SecretStr

from fast_mcp_jobvite.__main__ import EXIT_CONFIGURATION_REFUSED, main
from fast_mcp_jobvite.config import READ_TOOLS, Settings, load_settings
from fast_mcp_jobvite.server import (
    build_server,
    create_server,
    make_base_lifespan,
)

V2 = {"JOBVITE_API_KEY": "k", "JOBVITE_API_SECRET": "s"}


@pytest.fixture
def clean_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> pytest.MonkeyPatch:
    """Remove every JOBVITE_ variable and move off any real `.env`."""
    import os

    for name in list(os.environ):
        if name.startswith("JOBVITE_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return monkeypatch


def _settings() -> Settings:
    return Settings(
        tools="search_jobs",
        api_key=SecretStr("k"),
        api_secret=SecretStr("s"),  # noqa: S106
    )


def test_mask_error_details_is_set_explicitly() -> None:
    """Never left to the framework default.

    Asserted on the built instance AND on the source, because a
    framework whose default happened to be True would satisfy the first
    alone - and the point of this case is that a dependency bump must
    not be able to change it silently.
    """
    server = build_server(_settings())
    assert server._mask_error_details is True
    source = (
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "fast_mcp_jobvite"
        / "server.py"
    ).read_text()
    assert "mask_error_details=True" in source


async def test_composed_lifespans_start_in_order_and_tear_down_in_reverse() -> None:
    """DESIGN.md:959-960, which had no test before this one.

    Two composed lifespans, not one: with a single extra the sequence is
    up-then-down whatever the operator does, so a one-lifespan arm
    cannot tell "strict reverse" from "same order" and would pass
    against either.
    """
    order: list[str] = []

    def recorder(label: str) -> Lifespan:
        @lifespan
        async def _one(server: FastMCP[Any]) -> AsyncIterator[dict[str, Any]]:
            order.append(f"{label}-up")
            try:
                yield {label: True}
            finally:
                order.append(f"{label}-down")

        return _one

    server = build_server(_settings(), extra_lifespan=recorder("a") | recorder("b"))
    async with Client(server):
        pass

    assert order == ["a-up", "b-up", "b-down", "a-down"]


async def test_the_base_lifespan_publishes_the_settings() -> None:
    """Settings reach tools through the lifespan, not a global."""
    settings = _settings()
    server = build_server(settings)
    async with make_base_lifespan(settings)(server) as context:
        assert context["settings"] is settings
        assert context["enabled_tools"] == frozenset({"search_jobs"})


def test_create_server_builds_from_the_environment(
    clean_env: pytest.MonkeyPatch,
) -> None:
    """The factory `fastmcp inspect` and `fastmcp run` point at."""
    for key, value in V2.items():
        clean_env.setenv(key, value)
    clean_env.setenv("JOBVITE_FEED_KEY", "fk")
    clean_env.setenv("JOBVITE_FEED_SECRET", "fs")
    clean_env.setenv("JOBVITE_COMPANY_ID", "c1")
    server = create_server()
    assert server._mask_error_details is True
    assert load_settings().enabled_tools == READ_TOOLS


def test_create_server_refuses_a_bad_environment(
    clean_env: pytest.MonkeyPatch,
) -> None:
    """The refusal is not bypassed by going through the factory."""
    from fast_mcp_jobvite.config import ConfigurationError

    clean_env.setenv("JOBVITE_TOOLS", "not_a_tool")
    with pytest.raises(ConfigurationError):
        create_server()


def test_main_returns_the_refusal_status_without_serving(
    clean_env: pytest.MonkeyPatch,
) -> None:
    """`main` returns on the refusal path, BEFORE `os._exit`.

    **The `build_server` stub is a safety interlock, not a mock, and it
    was added because the amputation harness needed it.** With the
    refusals amputated, this call falls through to
    `mcp.run(transport="http")` inside the pytest process and serves
    forever - a hang, not a failure, and one that took twenty-two
    minutes to be recognised as a hang rather than a slow run. The stub
    turns "the refusal did not fire" into a red test in the same second.
    Reaching it at all is the bug.
    """

    def _must_not_be_reached(*_args: object, **_kwargs: object) -> None:
        message = "main() got past the refusal and was about to serve"
        raise AssertionError(message)

    clean_env.setattr("fast_mcp_jobvite.__main__.build_server", _must_not_be_reached)
    clean_env.setenv("JOBVITE_MCP_TRANSPORT", "http")
    clean_env.setenv("JOBVITE_TOOLS", "search_jobs")
    for key, value in V2.items():
        clean_env.setenv(key, value)
    assert main() == EXIT_CONFIGURATION_REFUSED


async def test_the_server_registers_no_tool_yet() -> None:
    """U1 owns the enable GATE, not the tools (DESIGN.md:919-936).

    A tool registered here would mean U1 had written outside the files
    §4's table gives it. The gate itself is asserted in
    `test_config.py`.
    """
    server = build_server(_settings())
    async with Client(server) as client:
        assert await client.list_tools() == []
    assert _settings().enabled_tools == frozenset({"search_jobs"})
