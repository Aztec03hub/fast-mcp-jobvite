"""The HTTP transport's hardening: auth, scopes, middleware, request id.

U9. **No §8 case owns this unit** - `IMPLEMENTATION-PLAN.md` §U9 says so
in as many words, and adds that *"nothing in the coupling gate will miss
them if they are dropped."* Every other unit here has a required case
that fails when its behaviour goes; this one does not. A silently
deleted test in this module leaves every gate green, which is why every
behaviour below has an amputation row proved able to fail rather than a
mutation of a constant.

**Why this is a module and not more of `server.py`.** `server.py` builds
the instance and its lifespan for BOTH transports. Everything here is
conditional on `http`, and keeping it separate makes "this code does not
run on stdio" a property of an import rather than of a branch a reader
has to trace.

**stdio is unauthenticated by design** (DESIGN.md:844-848): anything
able to spawn the process may call every tool, and the trust boundary is
the operating system's. That is not a gap this module closes - it is the
reason `require_scopes` is applied only when the transport is `http`.
`_RequireScopes` denies an ABSENT token, so applying it on stdio would
remove every tool from a transport the design says is fully authorised.

**The five NOT-adopted middleware** - `ResponseCaching`,
`ErrorHandling`, `ResponseLimiting`, `Retry`, `Ping` - are each
excluded for a measured
reason (ADR-0004, DESIGN.md's *"Not used"* paragraph), and re-adding one
is a silent regression. Their absence is asserted, and the assertion is
worth nothing on its own: five absences measured against a stack nobody
proved non-empty cannot tell *excluded* from *no middleware at all*. The
positive control is `test_http_hardening.py`'s assertion that the three
ADOPTED middleware are present and that `StructuredLoggingMiddleware`
carries `include_payloads=False`, which is threat row C2-I1's value.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Final

from fastmcp import FastMCP
from fastmcp.server.auth import require_scopes
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.dependencies import get_access_token, get_http_headers
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.middleware import (
    CallNext,
    Middleware,
    MiddlewareContext,
)
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.tools.base import Tool

from .audit import resolve_request_id
from .config import (
    CREATE_CANDIDATE,
    GET_CANDIDATE,
    GET_JOB_FEED,
    KNOWN_TOOLS,
    SEARCH_CANDIDATES,
    SEARCH_JOBS,
    Settings,
    is_loopback,
)
from .utils.correlation import request_id_scope

#: The three data classes of DESIGN.md §4.1, which DESIGN.md:828-829
#: also writes out as the token map's example scope list. The scope
#: names are the design's, not invented here - B15's lesson is that
#: guessing a name that happens to match is still guessing.
SCOPE_CANDIDATES: Final = "candidates:read"
SCOPE_JOBS: Final = "jobs:read"
SCOPE_FEED: Final = "feed:read"

#: Every tool, mapped to the data class it reads. **Keyed on the
#: container, not on a hand-kept list**: `_assert_total` below asserts
#: this map's key set is EQUAL to `KNOWN_TOOLS`, so a tool added to
#: `config.py` without a scope here fails at import rather than
#: registering unscoped. A hand-kept list beside its container is blind
#: to the member nobody added, and that is the shape this project has
#: measured most often.
#:
#: `create_candidate` writes candidate records, so it holds the
#: candidate-PII class. DESIGN.md:833-835 records that the earlier axis
#: - "a read-only token never sees the write tool" - COLLAPSED whenever
#: the write was out of scope, and that the surviving axis is the data
#: class. On stdio the write rests on the deploy-time flag plus
#: approval rather than on this scope (DESIGN.md:846-848).
TOOL_SCOPES: Final[dict[str, str]] = {
    SEARCH_CANDIDATES: SCOPE_CANDIDATES,
    GET_CANDIDATE: SCOPE_CANDIDATES,
    CREATE_CANDIDATE: SCOPE_CANDIDATES,
    SEARCH_JOBS: SCOPE_JOBS,
    GET_JOB_FEED: SCOPE_FEED,
}


def _assert_total() -> None:
    """Refuse to import with a tool that has no data class.

    Raises:
        RuntimeError: If `TOOL_SCOPES` and `KNOWN_TOOLS` differ in
            either direction. Both directions matter: a missing key is
            an unscoped tool, and an extra key is a scope nothing
            enforces.
    """
    if frozenset(TOOL_SCOPES) != KNOWN_TOOLS:
        unscoped = sorted(KNOWN_TOOLS - frozenset(TOOL_SCOPES))
        unknown = sorted(frozenset(TOOL_SCOPES) - KNOWN_TOOLS)
        msg = (
            f"TOOL_SCOPES must cover exactly KNOWN_TOOLS; "
            f"unscoped={unscoped} unknown={unknown}"
        )
        raise RuntimeError(msg)


_assert_total()

#: Requests per second the inbound limiter sustains, and the burst it
#: allows. **No environment variable declares these**: DESIGN.md's
#: variable set is closed at fifteen and none of them is an inbound
#: rate, so these are module constants rather than a sixteenth variable
#: invented here (B15).
#:
#: **`+ 2` is FastMCP's own client's connect sequence, not a protocol
#: constant** (DESIGN.md:395-403). The limiter counts every MCP request,
#: not just tool calls, and the two are `server/discover` plus
#: `tools/list`. **A client whose connect sequence is heavier burns
#: more, and this sizing then UNDER-PROVISIONS and refuses real tool
#: calls.** No client but FastMCP's has ever been measured. Nothing in
#: this file measures it either - the constant is carried from the
#: design, not established here.
DESIRED_TOOL_CALLS_PER_BURST: Final = 10
INBOUND_BURST_CAPACITY: Final = DESIRED_TOOL_CALLS_PER_BURST + 2
#: This module's own claim to a coverage role from DESIGN.md:1362-1364,
#: read by `docs/reviews/check-coverage-floors.py`. The design names the
#: roles and not the paths, and the claim lives HERE rather than in a
#: role-to-module map in the checker, which would be a hand-kept list
#: beside its container. The checker asserts the two sets are EQUAL.
COVERAGE_ROLE: Final = "auth"

INBOUND_MAX_REQUESTS_PER_SECOND: Final = 5.0

#: The `client_id` a caller with no access token is billed to. stdio has
#: no token and thus no client id, but it has exactly one caller, so one
#: bucket is correct there. **DESIGN.md:413-416 calls that REASONING,
#: not measurement** - every limiter arm was run in-memory or over HTTP
#: and the limiter has never been exercised on stdio at all.
ANONYMOUS_CLIENT_ID: Final = "anonymous"

#: The canonical inbound correlation header
#: (`ai/tool-calling.md:173-175`). `get_http_headers` lower-cases every
#: name, so the lookup is lower-case and the constant is not.
REQUEST_ID_HEADER: Final = "X-Request-ID"

#: The middleware classes that must NEVER appear in the stack, each
#: excluded for a measured reason (ADR-0004 and DESIGN.md's *"Not
#: used"* paragraph). Named as strings rather than imported, because
#: importing a module in order to prove we do not use it is the one
#: import a linter is entitled to delete.
EXCLUDED_MIDDLEWARE: Final[frozenset[str]] = frozenset(
    {
        "ResponseCachingMiddleware",
        "ErrorHandlingMiddleware",
        "ResponseLimitingMiddleware",
        "RetryMiddleware",
        "PingMiddleware",
    }
)


def token_client_id(token: str) -> str:
    """Return the non-secret client id a bearer token is billed to.

    **A digest, not the token.** `RateLimitingMiddleware` puts the
    client id into the text of the `MCPError` it raises on a trip
    (`rate_limiting.py:171`), and that error reaches the caller and the
    log. A raw bearer token there would publish a credential on the one
    path guaranteed to be hit by whoever is attacking the limiter.

    **Stable across restarts**, unlike an enumeration index: two
    processes reading the same `JOBVITE_HTTP_TOKENS` bill the same
    caller to the same id, so a log from one is joinable to a log from
    the other.

    Args:
        token: One bearer token from `JOBVITE_HTTP_TOKENS`.

    Returns:
        A 16-character hex digest of the token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def build_token_verifier(settings: Settings) -> StaticTokenVerifier | None:
    """Build the `StaticTokenVerifier` from `JOBVITE_HTTP_TOKENS`.

    **Returns `None` on stdio, which is not the same as an empty
    verifier.** DESIGN.md:844-848 makes stdio unauthenticated by design;
    a verifier holding no tokens would refuse every call on a transport
    the design says is fully authorised.

    **This never refuses.** Every refusal for this variable already
    happened in `config.validate_settings` - unset, malformed JSON, an
    empty token key, an empty scope list - so reaching here with an
    unusable value is a programming error rather than an operator's
    input. `settings.http_tokens` being `None` while the transport is
    `http` therefore raises rather than quietly building an open server.

    Args:
        settings: Settings that have already passed
            `validate_settings`.

    Returns:
        The verifier, or `None` when the transport is not `http`.

    Raises:
        ValueError: If the transport is `http` and `http_tokens` is
            unset. `validate_settings` should have refused it.
    """
    if settings.mcp_transport != "http":
        return None
    if settings.http_tokens is None:
        msg = (
            "JOBVITE_MCP_TRANSPORT=http requires JOBVITE_HTTP_TOKENS; "
            "validate_settings should have refused this configuration"
        )
        raise ValueError(msg)
    parsed: dict[str, list[str]] = json.loads(settings.http_tokens.get_secret_value())
    return StaticTokenVerifier(
        tokens={
            token: {"client_id": token_client_id(token), "scopes": list(scopes)}
            for token, scopes in parsed.items()
        }
    )


def rate_limit_client_id(context: MiddlewareContext[Any]) -> str:
    """Return the bucket a request is billed to.

    **This function is the whole point of the limiter being adopted at
    all.** `RateLimitingMiddleware`'s `get_client_id` is optional, and
    with it unset `_get_client_identifier` returns the literal string
    `"global"` (`rate_limiting.py:157`) despite the docstring implying
    per-client. One noisy integrator would then throttle everyone,
    which is DESIGN.md:392-394's first constraint and the defect the
    per-client test exists for.

    Args:
        context: The middleware context, unused. The identity comes
            from the access token in the request's own context, which
            is where FastMCP puts it; the parameter is part of the
            framework's callback signature.

    Returns:
        The token's `client_id`, or `ANONYMOUS_CLIENT_ID` where there
        is no token.
    """
    del context
    token = get_access_token()
    if token is None:
        return ANONYMOUS_CLIENT_ID
    return token.client_id


class RequestIdMiddleware(Middleware):
    """Bind the request's correlation id for the whole request.

    **The transport half of `resolve_request_id`.** `audit.py` owns the
    validation - an inbound `X-Request-ID` is echoed only if it is a
    valid UUIDv4, and anything else is discarded and replaced (C7-T1,
    DESIGN.md:1797). Nothing reached that function from a header
    before this class: `get_http_headers` is the only place the header
    exists, and it is an HTTP-transport dependency.

    **A malformed id is REPLACED, not refused.** A bad correlation
    header is not a reason to fail a tool call. The failure it prevents
    is log forging: a value carrying a newline writes a second,
    attacker-authored line into the audit stream.

    On stdio `get_http_headers` returns an empty mapping, so the
    inbound id is `None` and a fresh one is minted - the same result
    the tools got before this middleware existed.
    """

    async def on_request(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:  # noqa: ANN401
        """Resolve and bind the correlation id, then run the request.

        Args:
            context: The middleware context.
            call_next: The rest of the chain.

        Returns:
            Whatever the rest of the chain returned.
        """
        inbound = get_http_headers().get(REQUEST_ID_HEADER.lower())
        with request_id_scope(resolve_request_id(inbound)):
            return await call_next(context)


def build_middleware(settings: Settings) -> list[Middleware]:
    """Build the middleware stack, outermost first.

    Three adopted, and the order is the order DESIGN.md §7.7 lists
    them. `RequestIdMiddleware` is ours and runs first so every log
    line the other two emit carries the correlation id.

    Args:
        settings: Settings that have already passed
            `validate_settings`.

    Returns:
        The stack. Identical on both transports except for the
        limiter's client id, which has no token to read on stdio.
    """
    del settings
    return [
        RequestIdMiddleware(),
        TimingMiddleware(),
        # `include_payloads=False` is C2-I1's value (DESIGN.md:1732)
        # and is passed EXPLICITLY. The framework's default is also
        # `False` today, so this keyword changes no behaviour right
        # now - it is here so that a framework default flipping, or
        # somebody flipping this, is a visible diff in our own source
        # rather than a dependency bump. ADR-0011 records what the
        # value costs: the middleware emits no arguments at all, so
        # `audit.py` emits redacted ones itself.
        StructuredLoggingMiddleware(include_payloads=False),
        RateLimitingMiddleware(
            max_requests_per_second=INBOUND_MAX_REQUESTS_PER_SECOND,
            burst_capacity=INBOUND_BURST_CAPACITY,
            # MANDATORY. See `rate_limit_client_id`.
            get_client_id=rate_limit_client_id,
        ),
    ]


def registered_tools(server: FastMCP[Any]) -> list[Tool]:
    """Return the live `Tool` objects registered on a server.

    **Private-API access, stated rather than hidden.** FastMCP's only
    public accessors - `list_tools` and `get_tool` - are coroutines,
    and `build_server` is synchronous by design (`server.py` builds
    before any loop exists). The objects here are the same objects
    those coroutines return; `test_http_hardening.py` asserts the scope
    it sets is visible through the public `list_tools`, so a rename of
    this attribute fails a test instead of silently scoping nothing.

    Args:
        server: The instance to read.

    Returns:
        Every registered tool, in registration order.
    """
    components = server._local_provider._components  # noqa: SLF001
    return [item for item in components.values() if isinstance(item, Tool)]


def apply_tool_scopes(server: FastMCP[Any], settings: Settings) -> None:
    """Put `require_scopes` on every registered tool, on HTTP only.

    **`require_scopes` removes an unauthorised tool from `tools/list`
    entirely, and a direct call returns "Unknown tool" rather than a
    permission error** (DESIGN.md:836-839). Good behaviour, confusing
    failure mode; the README documents it or every support conversation
    starts in the wrong place.

    **Not applied on stdio, and that is a design position rather than
    an optimisation.** `_RequireScopes.__call__` returns `False` for an
    absent token (`authorization.py:76-77`), and stdio has no token at
    all, so applying it there would hide every tool on the transport
    DESIGN.md:844-848 declares fully authorised.

    Args:
        server: The instance whose tools are already registered.
        settings: Settings that have already passed
            `validate_settings`.

    Raises:
        KeyError: If a registered tool has no entry in `TOOL_SCOPES`.
            `_assert_total` makes that unreachable from `config.py`'s
            names; a tool registered under some other name should fail
            loudly rather than serve unscoped.
    """
    if settings.mcp_transport != "http":
        return
    for tool in registered_tools(server):
        tool.auth = require_scopes(TOOL_SCOPES[tool.name])


def http_run_kwargs(settings: Settings) -> dict[str, Any]:
    """Return the keyword arguments `mcp.run(transport="http")` takes.

    **`allowed_hosts` and `allowed_origins` are SET whenever the bind
    is not loopback**, rather than left at the framework default. They
    address DNS-rebinding and browser-origin confusion; they do nothing
    about plaintext, which is why `config._check_transport` refuses an
    off-loopback bind without a declared TLS proxy as a separate
    refusal.

    `allowed_origins` is set to the EMPTY list, not omitted. The
    framework distinguishes the two: `allowed_origins is not None` is
    what sets `has_explicit_allowed_origins` (`server/http.py:242`), so
    `[]` means *no browser origin is trusted* while `None` means *use
    the default*. Empty is the fail-closed value for a server no
    browser is meant to reach.

    On loopback both are omitted deliberately: the framework's own
    default already admits the loopback names, and narrowing it here
    would break `localhost` against a `127.0.0.1` bind for no threat
    that exists inside the host.

    Args:
        settings: Settings that have already passed
            `validate_settings`.

    Returns:
        `host` and `port` always; `allowed_hosts` and `allowed_origins`
        only off loopback.
    """
    kwargs: dict[str, Any] = {
        "host": settings.mcp_host,
        "port": settings.mcp_port,
    }
    if not is_loopback(settings.mcp_host):
        host = settings.mcp_host
        kwargs["allowed_hosts"] = [host, f"{host}:{settings.mcp_port}"]
        kwargs["allowed_origins"] = []
    return kwargs


__all__ = [
    "ANONYMOUS_CLIENT_ID",
    "DESIRED_TOOL_CALLS_PER_BURST",
    "EXCLUDED_MIDDLEWARE",
    "INBOUND_BURST_CAPACITY",
    "INBOUND_MAX_REQUESTS_PER_SECOND",
    "REQUEST_ID_HEADER",
    "SCOPE_CANDIDATES",
    "SCOPE_FEED",
    "SCOPE_JOBS",
    "TOOL_SCOPES",
    "RequestIdMiddleware",
    "apply_tool_scopes",
    "build_middleware",
    "build_token_verifier",
    "http_run_kwargs",
    "rate_limit_client_id",
    "registered_tools",
    "token_client_id",
]
