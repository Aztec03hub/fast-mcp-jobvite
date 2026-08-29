"""U9: the HTTP transport's hardening.

**Read `IMPLEMENTATION-PLAN.md` §U9 before deleting anything here.** No
§8 case owns this unit: §8 #10 is the only required case on the HTTP
transport and it covers the TLS refusal alone. Everything in this file
is a design obligation from §7.2 and §4.4 with **no required case behind
it**, so a silently deleted test here leaves every gate green. That is
why `scripts/check-u9-http-amputation.sh` deletes each behaviour from
the source and requires a named test to die: the amputation harness is
the only thing standing where a required case stands for every other
unit.

**The five-absence assertion is the reason the positive controls
exist.** `ResponseCaching`, `ErrorHandling`, `ResponseLimiting`, `Retry`
and `Ping` must be absent, each for a measured reason (ADR-0004 and
DESIGN.md's *"Not used"* paragraph). Five absences measured against a
stack nobody proved non-empty cannot tell *excluded* from *no middleware
at all*, so `test_the_three_adopted_middleware_are_present` and
`test_structured_logging_is_constructed_with_include_payloads_false` are
what give the absence its meaning. An earlier draft of this unit
positively verified only `RateLimitingMiddleware`, leaving `Timing` and
`StructuredLogging` - including the `include_payloads` value threat row
C2-I1 exists for - with no assertion at all.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client
from fastmcp.client.transports.http import StreamableHttpTransport
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.utilities.authorization import _RequireScopes
from pydantic import SecretStr

import fast_mcp_jobvite.http_hardening as hardening
from fast_mcp_jobvite.config import (
    GET_CANDIDATE,
    KNOWN_TOOLS,
    SEARCH_JOBS,
    Settings,
)
from fast_mcp_jobvite.http_hardening import (
    ANONYMOUS_CLIENT_ID,
    DESIRED_TOOL_CALLS_PER_BURST,
    EXCLUDED_MIDDLEWARE,
    INBOUND_BURST_CAPACITY,
    REQUEST_ID_HEADER,
    SCOPE_CANDIDATES,
    SCOPE_FEED,
    SCOPE_JOBS,
    TOOL_SCOPES,
    apply_tool_scopes,
    build_middleware,
    build_token_verifier,
    http_run_kwargs,
    rate_limit_client_id,
    registered_tools,
    token_client_id,
)
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.tools.jobs import REQUEST_ID_META_KEY
from fast_mcp_jobvite.utils.correlation import request_id_var
from tests.http_server_process import serve_http

#: The three adopted middleware of DESIGN.md §7.7, by class name.
#: **`RequestIdMiddleware` is ours and is deliberately not in this
#: set**: this constant is the framework's adopted three, which is what
#: the design's §7.7 heading enumerates and what ADR-0004's exclusions
#: are the complement of.
ADOPTED_MIDDLEWARE = frozenset(
    {
        "TimingMiddleware",
        "StructuredLoggingMiddleware",
        "RateLimitingMiddleware",
    }
)

#: A UUIDv4, as `audit._UUID4_RE` accepts one. Written out here rather
#: than imported: this file asserts what a CALLER observes, and
#: importing the server's own pattern would make the assertion agree
#: with the implementation by construction.
UUID4 = re.compile(
    r"\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z",
    re.IGNORECASE,
)

#: Two provisioned bearer tokens, differing only in the data class
#: they hold. `S105` is suppressed because these ARE tokens - the rule
#: has found exactly what it looks for, in the one place a literal
#: token is correct.
JOBS_TOKEN = "token-that-holds-jobs-only"  # noqa: S105
CANDIDATES_TOKEN = "token-that-holds-candidates-only"  # noqa: S105

TOKEN_MAP = {
    JOBS_TOKEN: [SCOPE_JOBS],
    CANDIDATES_TOKEN: [SCOPE_CANDIDATES],
}


def http_settings(**overrides: Any) -> Settings:
    """Build settings for the HTTP transport, tokens included.

    Args:
        overrides: Fields to replace, e.g. `mcp_host`.

    Returns:
        Settings that would pass `validate_settings`.
    """
    fields: dict[str, Any] = {
        "mcp_transport": "http",
        "http_tokens": SecretStr(json.dumps(TOKEN_MAP)),
        "api_key": SecretStr("key"),
        "api_secret": SecretStr("secret"),
        "tools": SEARCH_JOBS,
    }
    fields.update(overrides)
    return Settings(**fields)


def stdio_settings() -> Settings:
    """Build settings for stdio, which carries no tokens at all."""
    return Settings(
        mcp_transport="stdio",
        api_key=SecretStr("key"),
        api_secret=SecretStr("secret"),
        tools=SEARCH_JOBS,
    )


def middleware_names(server: FastMCP[Any]) -> list[str]:
    """Return the class names of a built server's middleware stack."""
    return [type(item).__name__ for item in server.middleware]


def probe_server(settings: Settings) -> FastMCP[Any]:
    """Build a server whose tools report the bound correlation id.

    **A probe rather than `search_jobs`, and the reason is a real
    seam.** `tools/jobs.py` calls `audit_scope` without an
    `inbound_request_id`, so the id it stamps into `_meta` is minted
    inside the scope this middleware already bound rather than being
    the one the middleware resolved. That is U5's call site and this
    unit does not own it; the report carries it as a finding with its
    one-line fix. What U9 owns and what this probe measures is that the
    TRANSPORT reaches `resolve_request_id` with the header's value and
    binds the result.

    Args:
        settings: Settings for the transport under test.

    Returns:
        A server carrying U9's auth, middleware and scopes, and two
        tools whose names appear in `TOOL_SCOPES`.
    """
    server: FastMCP[Any] = FastMCP(
        name="u9-probe",
        auth=build_token_verifier(settings),
        middleware=build_middleware(settings),
    )

    @server.tool(name=SEARCH_JOBS)
    def _search_jobs() -> str:
        return request_id_var.get() or "unbound"

    @server.tool(name=GET_CANDIDATE)
    def _get_candidate() -> str:
        return request_id_var.get() or "unbound"

    apply_tool_scopes(server, settings)
    return server


# ======================================================================
# The middleware stack. The absences and the positive controls that give
# them meaning.
# ======================================================================


def test_the_three_adopted_middleware_are_present() -> None:
    """POSITIVE CONTROL for every absence assertion in this file.

    Without it, `test_the_five_excluded_middleware_are_absent` passes
    perfectly against a server with NO middleware at all - which is
    exactly the regression the absence assertion exists to catch,
    wearing the shape of a pass.
    """
    server = build_server(http_settings())
    present = set(middleware_names(server))
    assert ADOPTED_MIDDLEWARE <= present, present


def test_structured_logging_is_constructed_with_include_payloads_false() -> None:
    """C2-I1 (DESIGN.md:1732): flipped to `True` this sends raw PII.

    The second half of the positive control, and the half an earlier
    draft omitted: it verified `RateLimitingMiddleware` alone, leaving
    the one value with a threat row of its own unasserted.
    """
    server = build_server(http_settings())
    logging_middleware = [
        item
        for item in server.middleware
        if isinstance(item, StructuredLoggingMiddleware)
    ]
    assert len(logging_middleware) == 1
    assert logging_middleware[0].include_payloads is False


def test_the_five_excluded_middleware_are_absent() -> None:
    """ADR-0004 and DESIGN.md's *"Not used"* paragraph.

    Each of the five was excluded for a measured reason and re-adding
    one is a silent regression. Meaningful only beside the two
    positive controls above.
    """
    for transport_settings in (http_settings(), stdio_settings()):
        server = build_server(transport_settings)
        present = set(middleware_names(server))
        assert not (EXCLUDED_MIDDLEWARE & present), present


def test_the_rate_limiter_has_a_get_client_id() -> None:
    """DESIGN.md:392-394: `get_client_id` is MANDATORY.

    Left unset, `_get_client_identifier` returns the literal string
    `"global"` (`rate_limiting.py:157`) despite the docstring implying
    per-client, and one noisy integrator throttles everyone.
    `test_rate_limiting_is_per_client` measures the consequence; this
    pins the wiring.
    """
    server = build_server(http_settings())
    limiters = [
        item for item in server.middleware if isinstance(item, RateLimitingMiddleware)
    ]
    assert len(limiters) == 1
    assert limiters[0].get_client_id is rate_limit_client_id
    assert limiters[0].global_limit is False


def test_the_burst_is_the_designs_sizing() -> None:
    """DESIGN.md:395-403's `desired_calls + 2`.

    **The `2` is FastMCP's own client's connect sequence, not a
    protocol constant**, and a heavier client burns more, at which
    point this sizing under-provisions and refuses real tool calls.
    Nothing here measures that; the constant is carried from the
    design.
    """
    assert INBOUND_BURST_CAPACITY == DESIRED_TOOL_CALLS_PER_BURST + 2


def test_rate_limit_client_id_falls_back_where_there_is_no_token() -> None:
    """A caller with no token is billed to one shared bucket.

    stdio has no token, and therefore no client id.

    One bucket is correct there because there is exactly one caller -
    **which DESIGN.md:413-416 calls reasoning, not measurement.** The
    limiter has never been exercised on stdio at all.
    """
    assert rate_limit_client_id(None) == ANONYMOUS_CLIENT_ID  # type: ignore[arg-type]


# ======================================================================
# Scopes: the three data classes of §4.1.
# ======================================================================


def test_every_known_tool_has_a_data_class() -> None:
    """The map is checked against its CONTAINER, not a second list.

    A hand-kept list beside its container is blind to the member nobody
    added. `KNOWN_TOOLS` is the container; a tool added there without a
    scope here would otherwise register unscoped.
    """
    assert frozenset(TOOL_SCOPES) == KNOWN_TOOLS


def test_the_totality_check_refuses_a_tool_with_no_data_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The check itself, not only the map it happens to accept.

    `test_every_known_tool_has_a_data_class` asserts today's map is
    total. It would pass unchanged with `_assert_total` DELETED, which
    is the shape this project calls a vacuous assertion: the guard that
    makes a future tool fail at import would be gone and nothing would
    say so. This drives the guard.

    Both directions, because both are defects: a tool with no scope
    registers unscoped, and a scope for no tool is a rule nothing
    enforces.
    """
    complete = dict(hardening.TOOL_SCOPES)

    # POSITIVE CONTROL FIRST. Without it, the two arms below pass
    # against an `_assert_total` that raises unconditionally - which is
    # the guard-that-refuses-everything shape.
    hardening._assert_total()  # noqa: SLF001

    incomplete = dict(complete)
    incomplete.pop(SEARCH_JOBS)
    monkeypatch.setattr(hardening, "TOOL_SCOPES", incomplete)
    with pytest.raises(RuntimeError, match="TOOL_SCOPES"):
        hardening._assert_total()  # noqa: SLF001

    extra = dict(complete)
    extra["a_tool_that_does_not_exist"] = SCOPE_JOBS
    monkeypatch.setattr(hardening, "TOOL_SCOPES", extra)
    with pytest.raises(RuntimeError, match="TOOL_SCOPES"):
        hardening._assert_total()  # noqa: SLF001


def test_the_scopes_are_the_three_data_classes() -> None:
    """DESIGN.md:833-834: candidate PII, public job data, job feed."""
    assert set(TOOL_SCOPES.values()) == {SCOPE_CANDIDATES, SCOPE_JOBS, SCOPE_FEED}


async def test_scopes_are_applied_on_http() -> None:
    """And the framework ACTS on them.

    `http_hardening.registered_tools` reaches a private attribute,
    because FastMCP's public accessors are coroutines and
    `build_server` is synchronous. Reading the result back through
    `list_tools` is what makes a rename of that attribute a failing
    test rather than a scope silently applied to nothing.
    """
    server = build_server(http_settings())
    registered = registered_tools(server)
    assert registered
    for tool in registered:
        check = tool.auth
        assert isinstance(check, _RequireScopes), tool.name
        assert check.required_scopes == frozenset({TOOL_SCOPES[tool.name]})

    # THE READ-BACK, and it is not decoration: `list_tools` applies
    # the check, and there is no token in this context, so an applied
    # scope makes the list EMPTY. That is the same removal a scopeless
    # caller sees over HTTP, measured without a server. If
    # `registered_tools` ever returned objects the framework does not
    # actually consult, this list would still be full.
    assert await server.list_tools(run_middleware=False) == []


async def test_scopes_are_NOT_applied_on_stdio() -> None:
    """DESIGN.md:844-848: stdio is unauthenticated BY DESIGN.

    Not an optimisation. `_RequireScopes.__call__` returns `False` for
    an ABSENT token (`authorization.py:76-77`), and stdio has no token
    at all - so applying the check there would remove every tool from
    the transport the design declares fully authorised. This assertion
    is the one that fails if somebody "simplifies" the transport
    branch away.
    """
    server = build_server(stdio_settings())
    tools = await server.list_tools(run_middleware=False)
    assert tools
    for tool in tools:
        assert tool.auth is None, tool.name


# ======================================================================
# The verifier built from JOBVITE_HTTP_TOKENS.
# ======================================================================


def test_no_verifier_on_stdio() -> None:
    """`None`, not an empty verifier.

    A verifier holding no tokens would refuse every call on a
    transport the design says is fully authorised - a guard that
    refuses everything.
    """
    assert build_token_verifier(stdio_settings()) is None


def test_the_verifier_carries_each_token_and_its_scopes() -> None:
    """POSITIVE CONTROL for the startup refusal in `test_boot.py`.

    `test_http_without_tokens_exits_rather_than_serving_openly`
    asserts the refusal; without this, that refusal is satisfied by a
    server that never accepts any token either.
    """
    verifier = build_token_verifier(http_settings())
    assert verifier is not None
    assert set(verifier.tokens) == set(TOKEN_MAP)
    for token, scopes in TOKEN_MAP.items():
        assert verifier.tokens[token]["scopes"] == scopes


def test_the_client_id_is_never_the_token() -> None:
    """The limiter puts `client_id` into the error text it RAISES.

    `rate_limiting.py:171` interpolates it into the `MCPError` message,
    which reaches the caller and the log. A raw bearer token there
    would publish a credential on the one path whoever is attacking the
    limiter is guaranteed to hit.
    """
    verifier = build_token_verifier(http_settings())
    assert verifier is not None
    for token in TOKEN_MAP:
        client_id = verifier.tokens[token]["client_id"]
        assert client_id == token_client_id(token)
        assert token not in client_id
        assert client_id not in token


def test_http_without_tokens_raises_rather_than_building_an_open_server() -> None:
    """`validate_settings` should have refused it; this fails closed.

    Reaching here with `http_tokens` unset is a programming error, not
    an operator's input, so it raises naming the variable rather than
    quietly returning `None` - which on the HTTP path is an open
    server.
    """
    settings = Settings(
        mcp_transport="http",
        api_key=SecretStr("key"),
        api_secret=SecretStr("secret"),
        tools=SEARCH_JOBS,
    )
    with pytest.raises(ValueError, match="JOBVITE_HTTP_TOKENS"):
        build_token_verifier(settings)


# ======================================================================
# The bind: JOBVITE_MCP_HOST / JOBVITE_MCP_PORT and the guard lists.
# ======================================================================


def test_the_host_and_port_are_honoured() -> None:
    """The two variables the design NAMED (DESIGN.md:1565)."""
    kwargs = http_run_kwargs(http_settings(mcp_host="10.1.2.3", mcp_port=9101))
    assert kwargs["host"] == "10.1.2.3"
    assert kwargs["port"] == 9101


def test_off_loopback_SETS_the_guard_lists() -> None:
    """Rather than leaving them at the framework default.

    `allowed_origins` is the EMPTY list, not omitted: the framework
    distinguishes them - `allowed_origins is not None` is what sets
    `has_explicit_allowed_origins` (`server/http.py:242`) - so `[]`
    means *no browser origin is trusted* and `None` means *use the
    default*.
    """
    settings = http_settings(
        mcp_host="0.0.0.0",  # noqa: S104
        mcp_port=9101,
        tls_terminated_by_proxy=True,
    )
    kwargs = http_run_kwargs(settings)
    assert kwargs["allowed_hosts"] == ["0.0.0.0", "0.0.0.0:9101"]  # noqa: S104
    assert kwargs["allowed_origins"] == []


def test_loopback_leaves_the_guard_lists_alone() -> None:
    """The other direction, and it is not decoration.

    Narrowing `allowed_hosts` on a loopback bind breaks `localhost`
    against a `127.0.0.1` bind for no threat that exists inside the
    host. Without this arm, unconditionally setting the lists would
    pass the arm above.
    """
    kwargs = http_run_kwargs(http_settings(mcp_host="127.0.0.1"))
    assert "allowed_hosts" not in kwargs
    assert "allowed_origins" not in kwargs


# ======================================================================
# Over the wire. Everything below needs a real HTTP request: an
# in-memory transport has no Authorization header, no X-Request-ID and
# no access token.
# ======================================================================


async def test_two_differently_scoped_tokens_see_different_tool_sets() -> None:
    """DESIGN.md:836-839, and the whole point of §7.2's scope axis."""
    with serve_http(probe_server(http_settings())) as url:
        async with Client(StreamableHttpTransport(url, auth=JOBS_TOKEN)) as client:
            jobs_tools = {tool.name for tool in await client.list_tools()}
        async with Client(
            StreamableHttpTransport(url, auth=CANDIDATES_TOKEN)
        ) as client:
            candidate_tools = {tool.name for tool in await client.list_tools()}
    assert jobs_tools == {SEARCH_JOBS}
    assert candidate_tools == {GET_CANDIDATE}


async def test_a_token_lacking_a_scope_gets_unknown_tool_not_permission() -> None:
    """The confusing-but-correct behaviour the README must document.

    `require_scopes` removes the tool from `tools/list` ENTIRELY, so a
    direct call cannot distinguish it from a tool that does not exist.
    **Asserted in both directions**: the wording is "Unknown tool", and
    it carries none of the words a support conversation would start
    from if it were a permission error.
    """
    with serve_http(probe_server(http_settings())) as url:
        async with Client(
            StreamableHttpTransport(url, auth=CANDIDATES_TOKEN)
        ) as client:
            listed = {tool.name for tool in await client.list_tools()}
            assert SEARCH_JOBS not in listed
            with pytest.raises(Exception) as caught:  # noqa: B017, PT011
                await client.call_tool(SEARCH_JOBS, {})
    message = str(caught.value)
    assert "Unknown tool" in message, message
    lowered = message.lower()
    for permission_word in ("scope", "permission", "forbidden", "unauthorized"):
        assert permission_word not in lowered, message


async def test_a_well_formed_token_map_authenticates_and_the_tool_runs() -> None:
    """POSITIVE CONTROL for every refusal on this transport.

    Four assertions above are refusals - no scope, no token, no
    variable. All four pass against a server that refuses EVERYTHING,
    which is the guard-that-refuses-everything DESIGN.md:1370-1372
    names. This is the arm that says the door opens.
    """
    with serve_http(probe_server(http_settings())) as url:
        async with Client(StreamableHttpTransport(url, auth=JOBS_TOKEN)) as client:
            result = await client.call_tool(SEARCH_JOBS, {})
    assert UUID4.match(result.content[0].text)


async def test_an_unknown_token_is_refused() -> None:
    """`StaticTokenVerifier` returns `None` and the transport 401s."""
    with serve_http(probe_server(http_settings())) as url:
        with pytest.raises(Exception):  # noqa: B017, PT011
            async with Client(
                StreamableHttpTransport(url, auth="a-token-nobody-provisioned")
            ) as client:
                await client.list_tools()


async def test_a_valid_inbound_request_id_reaches_the_tool_unchanged() -> None:
    """The transport path REACHES `resolve_request_id` and echoes.

    DESIGN.md:597-599: a valid UUIDv4 is echoed BYTE FOR BYTE, case
    included. The upper-case arm is deliberate - R2's nit-4 records a
    `.lower()` surviving the whole suite because the only test used an
    all-digit literal.
    """
    inbound = "11111111-2222-4333-8ABC-555555555555"
    with serve_http(probe_server(http_settings())) as url:
        async with Client(
            StreamableHttpTransport(
                url, auth=JOBS_TOKEN, headers={REQUEST_ID_HEADER: inbound}
            )
        ) as client:
            result = await client.call_tool(SEARCH_JOBS, {})
    assert result.content[0].text == inbound


@pytest.mark.parametrize(
    "malformed",
    [
        pytest.param("not-a-uuid", id="not-a-uuid"),
        pytest.param("11111111-2222-4333-8abc-5555555555555", id="over-long"),
        pytest.param("11111111-2222-1333-8abc-555555555555", id="wrong-version"),
    ],
)
async def test_a_malformed_inbound_request_id_is_replaced(malformed: str) -> None:
    """C7-T1 (DESIGN.md:1797). REPLACED, not refused.

    A malformed correlation header is not a reason to fail a tool
    call. What it must never do is reach the audit stream: a value
    carrying a newline writes a second, attacker-authored line into it.

    **A bare newline is not parameterised here** and that is a limit,
    not an oversight: `httpx` refuses to put one in a header at all, so
    the wire cannot carry the exact C7-T1 payload. `tests/test_audit.py`
    covers the newline against `resolve_request_id` directly. What this
    proves is the half only the transport can: the header's value is
    the one that reaches the function.
    """
    with serve_http(probe_server(http_settings())) as url:
        async with Client(
            StreamableHttpTransport(
                url, auth=JOBS_TOKEN, headers={REQUEST_ID_HEADER: malformed}
            )
        ) as client:
            result = await client.call_tool(SEARCH_JOBS, {})
    seen = result.content[0].text
    assert seen != malformed
    assert UUID4.match(seen), seen


# ======================================================================
# Rate limiting, per client. DESIGN.md:392-394.
# ======================================================================

#: Budget for the two limiter arms. Small and slow-refilling so the
#: drain is deterministic in well under a second: at 0.01 requests per
#: second the bucket gains nothing measurable while the arm runs.
DRAIN_BURST = 6
DRAIN_REFILL_PER_SECOND = 0.01
DRAIN_CALLS = 12


def limiter_server(*, per_client: bool) -> FastMCP[Any]:
    """A server whose limiter is small enough to drain in a test.

    **`get_client_id` is the production callable**, not a stand-in -
    the keying is the behaviour under test. Only the budget is
    shrunk, because `INBOUND_BURST_CAPACITY` would take twelve seconds
    of real requests to exhaust.

    Args:
        per_client: `False` builds the framework's DEFAULT keying,
            which is the negative control.

    Returns:
        The server.
    """
    settings = http_settings()
    server: FastMCP[Any] = FastMCP(
        name="u9-limiter-probe",
        auth=build_token_verifier(settings),
        middleware=[
            RateLimitingMiddleware(
                max_requests_per_second=DRAIN_REFILL_PER_SECOND,
                burst_capacity=DRAIN_BURST,
                get_client_id=rate_limit_client_id if per_client else None,
            )
        ],
    )

    @server.tool(name=SEARCH_JOBS)
    def _search_jobs() -> str:
        return "ok"

    return server


async def refusals(url: str, token: str, calls: int) -> int:
    """Call the probe tool `calls` times and count the refusals.

    Args:
        url: The served endpoint.
        token: The bearer token to present.
        calls: How many tool calls to attempt.

    Returns:
        How many of them were refused.
    """
    refused = 0
    async with Client(StreamableHttpTransport(url, auth=token)) as client:
        for _ in range(calls):
            try:
                await client.call_tool(SEARCH_JOBS, {})
            except Exception:  # noqa: BLE001, PERF203
                refused += 1
    return refused


async def test_rate_limiting_is_per_client() -> None:
    """One client drains its bucket; the other is UNAFFECTED.

    DESIGN.md:392-394's first constraint. The failure this prevents is
    one noisy integrator throttling everyone.
    """
    with serve_http(limiter_server(per_client=True)) as url:
        drained = await refusals(url, JOBS_TOKEN, DRAIN_CALLS)
        bystander = await refusals(url, CANDIDATES_TOKEN, 2)
    assert drained > 0, "the first client never drained; the arm proves nothing"
    assert bystander == 0


async def test_the_framework_default_throttles_everyone() -> None:
    """NEGATIVE CONTROL, and it is what makes the arm above non-vacuous.

    With `get_client_id` unset the framework keys every caller to the
    literal string `"global"` (`rate_limiting.py:157`). Measured here:
    the bystander does not merely lose a tool call, it cannot COMPLETE
    THE CONNECTION - the refusal lands on `initialize`. Without this
    arm, `test_rate_limiting_is_per_client` would pass just as happily
    against a limiter that never refuses anybody.
    """
    with serve_http(limiter_server(per_client=False)) as url:
        drained = await refusals(url, JOBS_TOKEN, DRAIN_CALLS)
        with pytest.raises(Exception) as caught:  # noqa: B017, PT011
            await refusals(url, CANDIDATES_TOKEN, 2)
    assert drained > 0
    message = str(caught.value).lower()
    assert "global" in message or "rate limit" in message, message


# ======================================================================
# U9-F1: the caller's id must be the one that comes back
# ======================================================================


async def test_a_valid_inbound_request_id_is_the_one_stamped_into_meta() -> None:
    """U9-F1, end to end over a real HTTP request.

    **U9's probe deliberately stops one step short of this.** It proves
    the TRANSPORT reaches `resolve_request_id` with the header's value
    and binds the result - which is what U9 owned. What nothing proved
    is the half a caller actually experiences: that the id it sent is
    the id that comes back in `_meta`.

    It was not. All three `audit_scope` call sites - `search_jobs` and
    both candidate tools - omit `inbound_request_id`, so
    `resolve_request_id(None)` MINTED A FRESH ID inside the scope the
    middleware had already bound. A caller's valid `X-Request-ID` was
    validated, bound, and then discarded.

    **The fix is the fallback in `resolve_request_id`, not an argument
    at each call site**, and this case is what holds it: a per-call-site
    fix would need three edits today and a fourth for the next tool,
    which is a hand-kept obligation beside a container.

    Asserted as an EQUALITY against a known id, not as "some id is
    present" - a `_meta` carrying any UUID passes the weaker form, and
    the weaker form is exactly what was green while this was broken.
    """
    sent = "0e1f2a3b-4c5d-4e6f-8a9b-0c1d2e3f4a5b"
    from tests.test_tools_jobs import JOB_LIST_SUCCESS, client_factory, fixture_bytes

    factory = client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    server = build_server(http_settings(), client_factory=factory)
    with serve_http(server) as url:
        async with Client(
            StreamableHttpTransport(
                url, auth=JOBS_TOKEN, headers={"X-Request-ID": sent}
            )
        ) as client:
            result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    echoed = (result.meta or {}).get(REQUEST_ID_META_KEY)
    assert echoed == sent, f"sent {sent!r}, got {echoed!r}"
