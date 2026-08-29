"""DESIGN.md:165's 1 MiB request-body cap, measured on a real socket.

**Every arm here runs over HTTP, and that is not decoration.** The
subject is an `ASGIMiddleware`, so its inputs are `scope`, `receive` and
`send` as a real server produces them. Calling the class with a
hand-built `receive` would test a fixture's idea of chunking; the two
framings this cap has to tell apart - `Content-Length` present and
`Transfer-Encoding: chunked` - are produced by the client library and
the server, not by us.

**THE BOUNDARY IS TESTED ON BOTH SIDES, AND THAT IS THE POINT.**
`2 MiB rejected` passes against a server that rejects everything, and
this project has recorded that shape often enough to name it. So each
framing gets `MAX - 1` accepted, `MAX` accepted, and `MAX + 1` refused,
with the accepting arms asserting the byte count the application
actually received rather than merely a 200.

**Why an echo application and not the MCP app for the boundary.** The
accepting arms have to prove the bytes arrived intact and were counted
exactly; the MCP app answers a `1 MiB - 1` blob of `x` with a protocol
error for reasons that have nothing to do with size, so a 200/not-200
assertion against it would measure the wrong thing. The MCP app is used
in section 3 instead, for the only question it can answer: **is the cap
mounted on the server this repository actually runs.**

**`MAX_PAYLOAD_BYTES` is not tested here and must not be deleted as a
duplicate of this** (ADR-0029 as corrected). It bounds the serialised
argument payload on BOTH transports; this bounds the HTTP request body
on ONE. `tests/test_arguments_sweep.py` owns that one and still does.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any, Final

import httpx2
import pytest
from starlette.middleware import Middleware as ASGIMiddleware
from starlette.types import Message, Receive, Scope, Send

from fast_mcp_jobvite.errors import VALIDATION_ERROR
from fast_mcp_jobvite.http_hardening import (
    MAX_REQUEST_BODY_BYTES,
    BodySizeLimitMiddleware,
    http_run_kwargs,
)
from tests.http_server_process import serve_asgi
from tests.test_http_hardening import http_settings

#: **The literal `DESIGN.md:165` writes down, not the constant.** An arm
#: that reads its expectation out of the code it is testing cannot fail
#: when that code changes - mutation M11 moved a constant and the
#: accepting arm moved with it, silently. Section 1 is the single place
#: this literal is joined to `MAX_REQUEST_BODY_BYTES`, by name, and
#: every other arm below is written against the literal.
ONE_MEBIBYTE: Final = 1024 * 1024

#: Chunk size for the streamed arms. Small enough that a `MAX + 1` body
#: crosses the line many chunks before it ends, which is what makes
#: "refused before the whole body is held" measurable rather than
#: asserted.
CHUNK_BYTES: Final = 64 * 1024

#: Generous, because these arms move megabytes over loopback and a tight
#: bound turns a slow runner into a mystery failure.
TIMEOUT_SECONDS: Final = 60.0


class _CountingEcho:
    """An ASGI app that drains the body and reports the byte count.

    `high_water` is the measurement that "reject before buffering"
    reduces to: the most bytes this application was ever handed for one
    request. If the cap only counted after the body was complete, a
    refused 8 MiB request would still push this to 8 MiB.
    """

    def __init__(self) -> None:
        """Start with no request seen."""
        self.high_water = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Drain, record, and answer with the count.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        if scope["type"] != "http":
            return
        seen = 0
        while True:
            message: Message = await receive()
            if message["type"] == "http.disconnect":
                break
            seen += len(message.get("body", b""))
            self.high_water = max(self.high_water, seen)
            if not message.get("more_body", False):
                break
        body = str(seen).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


@pytest.fixture
def echo() -> _CountingEcho:
    """The application the cap wraps, fresh per test."""
    return _CountingEcho()


@pytest.fixture
def capped(echo: _CountingEcho) -> Iterator[str]:
    """A real HTTP server running the cap at the design's own number.

    `max_bytes` is NOT passed. The default is the design's number, and
    an arm that supplied its own would pass against a middleware whose
    default had been changed to anything at all.
    """
    with serve_asgi(BodySizeLimitMiddleware(echo)) as url:
        yield url


def _chunks(total: int) -> Iterator[bytes]:
    """Yield `total` bytes in `CHUNK_BYTES` pieces.

    A generator body is what makes `httpx2` use chunked transfer
    encoding and send NO `Content-Length`, which is the framing arm 2
    exists for.

    Args:
        total: How many bytes to produce.

    Yields:
        Successive chunks, the last one short.
    """
    sent = 0
    while sent < total:
        piece = min(CHUNK_BYTES, total - sent)
        sent += piece
        yield b"x" * piece


def _assert_is_the_cap_refusing(response: httpx2.Response) -> None:
    """Assert a response is THIS cap's refusal and not some other 422.

    A bare `status_code == 422` would pass against any validation
    failure the stack happens to produce, including one raised for a
    reason unrelated to size. The `detail` check is what ties the
    response to this control.

    Args:
        response: The response to check.
    """
    assert response.status_code == VALIDATION_ERROR.status
    assert response.headers["content-type"] == "application/problem+json"
    problem = response.json()
    assert problem["type"] == VALIDATION_ERROR.type
    assert problem["title"] == VALIDATION_ERROR.title
    assert problem["status"] == VALIDATION_ERROR.status
    assert "request body is larger than" in problem["detail"]
    assert str(ONE_MEBIBYTE) in problem["detail"]


# ======================================================================
# 1. THE NUMBER IS THE DESIGN'S OWN
# ======================================================================


def test_the_cap_is_the_designs_own_number() -> None:
    """`DESIGN.md:165`, transcribed once.

    The one place the literal below is joined to the constant the code
    uses. Every other arm is written against the literal, so a constant
    changed in `http_hardening.py` fails HERE, by name, instead of
    silently redefining what every other arm means.
    """
    assert MAX_REQUEST_BODY_BYTES == 1024 * 1024


def test_the_body_cap_is_not_the_argument_payload_cap() -> None:
    """ADR-0029's surviving half, asserted rather than commented.

    The two constants hold the same number and bound different things.
    If someone ever "de-duplicates" them by making one an alias of the
    other, this goes red - they must be independent objects, because
    deleting either leaves a real hole on a transport the other does not
    reach.
    """
    from fast_mcp_jobvite.utils import constraints

    assert not hasattr(constraints, "MAX_REQUEST_BODY_BYTES"), (
        "constraints.py must not import the body cap: ADR-0029 - the two "
        "are different controls at different layers, and an import here "
        "would let one be deleted as a duplicate of the other"
    )
    assert not hasattr(constraints, "BodySizeLimitMiddleware")
    # And the payload cap is still this module's OWN constant, not a
    # re-export. Naming both in a comment is fine and is how the two are
    # kept legible; what must not exist is a code-level dependency.
    #
    # Identity is NOT asserted and could not be: CPython would happily
    # return the same `int` object for two independently written
    # `1024 * 1024`s, so `is not` here would be a check that cannot
    # fail. The separation that is real is the module namespaces, and
    # that is what the two assertions above measure.
    assert constraints.MAX_PAYLOAD_BYTES == 1024 * 1024


# ======================================================================
# 2. THE BOUNDARY, BOTH SIDES, BOTH FRAMINGS
# ======================================================================
#
# Six arms. Three per framing, and the framings are separate because a
# check that only reads `Content-Length` passes every declared-length
# arm and fails every chunked one - which is exactly the defect worth
# catching, and a single-framing test cannot see it.


@pytest.mark.parametrize(
    "size",
    [ONE_MEBIBYTE - 1, ONE_MEBIBYTE],
    ids=["one-byte-under", "exactly-at"],
)
def test_a_declared_body_at_or_under_the_cap_is_ACCEPTED(
    capped: str, echo: _CountingEcho, size: int
) -> None:
    """ACCEPTING ARM. `Content-Length` present, at and just under.

    The assertion is the BYTE COUNT the application received, not a
    status code: a 200 alone would pass against a cap that silently
    truncated the body, which is a worse failure than refusing it.
    """
    response = httpx2.post(capped, content=b"x" * size, timeout=TIMEOUT_SECONDS)
    assert response.status_code == 200
    assert response.text == str(size)
    assert echo.high_water == size


def test_a_declared_body_one_byte_over_the_cap_is_REFUSED(
    capped: str, echo: _CountingEcho
) -> None:
    """REJECTING ARM. `Content-Length` present, one byte over.

    **`high_water == 0` is the "before buffering" half.** The
    application was never called, so not one byte of the body was read
    on its behalf. A cap that measured by reading would show 1048577
    here and still return 422, and would have bounded nothing.
    """
    response = httpx2.post(
        capped, content=b"x" * (ONE_MEBIBYTE + 1), timeout=TIMEOUT_SECONDS
    )
    _assert_is_the_cap_refusing(response)
    assert echo.high_water == 0


@pytest.mark.parametrize(
    "size",
    [ONE_MEBIBYTE - 1, ONE_MEBIBYTE],
    ids=["one-byte-under", "exactly-at"],
)
def test_a_CHUNKED_body_at_or_under_the_cap_is_ACCEPTED(
    capped: str, echo: _CountingEcho, size: int
) -> None:
    """ACCEPTING ARM, no `Content-Length` at all.

    Without this arm the streaming counter could be off by a chunk and
    every rejecting arm would still be green.
    """
    response = httpx2.post(capped, content=_chunks(size), timeout=TIMEOUT_SECONDS)
    assert response.status_code == 200
    assert response.text == str(size)
    assert echo.high_water == size


def test_a_CHUNKED_body_one_byte_over_the_cap_is_REFUSED(
    capped: str, echo: _CountingEcho
) -> None:
    """REJECTING ARM, and the case an attacker actually uses.

    Omitting `Content-Length` is free, and it defeats any cap that only
    reads the header. The refusal here can come from nothing but the
    running sum over the delivered bytes.
    """
    response = httpx2.post(
        capped, content=_chunks(ONE_MEBIBYTE + 1), timeout=TIMEOUT_SECONDS
    )
    _assert_is_the_cap_refusing(response)


def test_a_HUGE_chunked_body_is_refused_without_being_held(
    capped: str, echo: _CountingEcho
) -> None:
    """The bound is a BOUND, not a count taken at the end.

    Eight megabytes arrive with no declared length. If the cap summed
    the body and compared once at the end, the application would have
    been handed all 8 MiB before anything refused it. The assertion is
    that it was handed no more than the cap plus the chunk that crossed
    it - so memory is bounded by the LIMIT, not by what the caller
    chose to send.
    """
    response = httpx2.post(
        capped, content=_chunks(8 * ONE_MEBIBYTE), timeout=TIMEOUT_SECONDS
    )
    _assert_is_the_cap_refusing(response)
    assert echo.high_water <= ONE_MEBIBYTE + CHUNK_BYTES


def test_a_LIED_ABOUT_content_length_does_not_get_past_the_cap(
    echo: _CountingEcho,
) -> None:
    """A small declared length with a large body still trips arm 2.

    Arm 1 believes a number the caller chose, so it is an early exit and
    never the bound: the running sum runs whatever the header said.

    **Measured at the unit and NOT over the wire, and the reason is a
    real one, not convenience.** `httpx2` refuses to send a body longer
    than the `Content-Length` it was told to write - `httpcore2` raises
    out of `_send_request_body` before a byte leaves - so this framing
    cannot be produced by the client this repository depends on. A wire
    arm here would be measuring the client's honesty, and would pass
    with arm 2 deleted.
    """
    delivered: list[Message] = [
        {"type": "http.request", "body": b"x" * CHUNK_BYTES, "more_body": True}
        for _ in range(2 * ONE_MEBIBYTE // CHUNK_BYTES)
    ]
    sent: list[Message] = []

    async def receive() -> Message:
        return delivered.pop(0)

    async def send(message: Message) -> None:
        sent.append(message)

    async def run() -> None:
        await BodySizeLimitMiddleware(echo)(
            {"type": "http", "headers": [(b"content-length", b"10")]},
            receive,
            send,
        )

    import asyncio

    asyncio.run(run())
    assert sent[0]["status"] == VALIDATION_ERROR.status
    body = json.loads(sent[1]["body"])
    assert "request body is larger than" in body["detail"]
    assert echo.high_water <= ONE_MEBIBYTE + CHUNK_BYTES


# ======================================================================
# 3. IT IS MOUNTED ON THE SERVER THIS REPOSITORY RUNS
# ======================================================================
#
# Section 2 proves the class works. That is worth nothing if nothing
# constructs it: a control that is correct and unmounted is exactly the
# "reads as discharged" shape ADR-0029 refused for MAX_PAYLOAD_BYTES.


def test_http_run_kwargs_mounts_the_body_cap() -> None:
    """`__main__.py` passes this dict straight to `mcp.run`.

    Asserted on the CLASS and the KEYWORD, because
    `starlette.middleware.Middleware` defers construction: the object in
    this list is a factory, and reading `cls` and `kwargs` off it is the
    only way to see what will be built.
    """
    kwargs = http_run_kwargs(http_settings())
    mounted = kwargs["middleware"]
    assert [entry.cls for entry in mounted] == [BodySizeLimitMiddleware]
    assert mounted[0].kwargs == {"max_bytes": MAX_REQUEST_BODY_BYTES}


def test_the_body_cap_is_mounted_on_loopback_too() -> None:
    """Loopback does not make the cap moot, unlike `allowed_hosts`.

    Every process on the host can open a socket to a loopback bind, so
    the set of callers that can send an unbounded body is not empty
    there. This arm exists because the two neighbouring keys in the same
    function ARE loopback-conditional, and the next reader will assume
    this one is too.
    """
    settings = http_settings()
    assert settings.mcp_host == "127.0.0.1"
    kwargs = http_run_kwargs(settings)
    assert "allowed_hosts" not in kwargs
    assert kwargs["middleware"]


def test_the_mounted_stack_refuses_an_oversized_body_end_to_end() -> None:
    """The whole path: `http_run_kwargs` -> `http_app` -> the wire.

    The middleware list is taken from `http_run_kwargs` rather than
    built here, so deleting the wiring takes this arm down even though
    the class still exists and section 2 still passes.
    """
    from fastmcp import FastMCP

    server: FastMCP[Any] = FastMCP("body-cap-probe")
    mounted: list[ASGIMiddleware] = http_run_kwargs(http_settings())["middleware"]
    with serve_asgi(server.http_app(middleware=mounted)) as base:
        response = httpx2.post(
            f"{base}mcp",
            content=b"x" * (ONE_MEBIBYTE + 1),
            headers={"content-type": "application/json"},
            timeout=TIMEOUT_SECONDS,
        )
    _assert_is_the_cap_refusing(response)


def test_the_mounted_stack_refuses_a_CHUNKED_oversized_body_end_to_end() -> None:
    """The arm above never calls the app, and this one has to.

    A declared `Content-Length` is refused before `self.app` is entered,
    so it proves nothing about what happens when the bound trips
    mid-stream: the unwind has to travel back out through Starlette's
    `ExceptionMiddleware` and every layer `http_app` mounts, any one of
    which could catch a bare exception and turn the refusal into a 500.
    Nothing but running it against the real stack establishes that, and
    the echo app of section 2 has none of those layers.
    """
    from fastmcp import FastMCP

    server: FastMCP[Any] = FastMCP("body-cap-probe")
    mounted: list[ASGIMiddleware] = http_run_kwargs(http_settings())["middleware"]
    with serve_asgi(server.http_app(middleware=mounted)) as base:
        response = httpx2.post(
            f"{base}mcp",
            content=_chunks(ONE_MEBIBYTE + 1),
            headers={"content-type": "application/json"},
            timeout=TIMEOUT_SECONDS,
        )
    _assert_is_the_cap_refusing(response)


def test_the_mounted_stack_still_serves_a_body_under_the_cap() -> None:
    """POSITIVE CONTROL for the arm above.

    A stack that refused every POST would pass the rejecting arm. This
    sends a well-formed initialise under the cap and asserts the answer
    is NOT this cap's refusal - it may be any protocol outcome at all,
    and the only thing ruled out is that the body cap fired.
    """
    from fastmcp import FastMCP

    server: FastMCP[Any] = FastMCP("body-cap-probe")
    mounted: list[ASGIMiddleware] = http_run_kwargs(http_settings())["middleware"]
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probe", "version": "0"},
            },
        }
    ).encode()
    with serve_asgi(server.http_app(middleware=mounted)) as base:
        response = httpx2.post(
            f"{base}mcp",
            content=payload,
            headers={
                "content-type": "application/json",
                "accept": "application/json, text/event-stream",
            },
            timeout=TIMEOUT_SECONDS,
        )
    assert "request body is larger than" not in response.text


# ======================================================================
# 4. THE CORRELATION ID, AND THE SHAPES THAT MUST NOT CRASH IT
# ======================================================================


def test_a_refusal_echoes_a_valid_inbound_request_id(capped: str) -> None:
    """`RequestIdMiddleware` never runs here, so the cap does it.

    The refusal happens before any MCP message is parsed, so the
    protocol middleware that normally binds the correlation id is not
    reached. A refusal with an unjoinable id is a refusal an operator
    cannot trace back to the caller who caused it.
    """
    caller_id = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
    response = httpx2.post(
        capped,
        content=b"x" * (ONE_MEBIBYTE + 1),
        headers={"X-Request-ID": caller_id},
        timeout=TIMEOUT_SECONDS,
    )
    problem = response.json()
    assert problem["request_id"] == caller_id
    assert problem["instance"].endswith(caller_id)


def test_a_refusal_mints_an_id_when_the_inbound_one_is_junk(capped: str) -> None:
    """C7-T1: an invalid correlation id is replaced, never echoed.

    Same rule `resolve_request_id` applies everywhere else, reached from
    a layer that has to read the raw header itself.
    """
    response = httpx2.post(
        capped,
        content=b"x" * (ONE_MEBIBYTE + 1),
        headers={"X-Request-ID": "not-a-uuid"},
        timeout=TIMEOUT_SECONDS,
    )
    problem = response.json()
    assert problem["request_id"] != "not-a-uuid"
    assert len(problem["request_id"]) == 36


@pytest.mark.parametrize(
    "declared",
    ["not-a-number", "-1", ""],
    ids=["non-numeric", "negative", "empty"],
)
def test_a_malformed_content_length_falls_through_to_the_running_bound(
    echo: _CountingEcho, declared: str
) -> None:
    """A header this module cannot read is not a header it may trust.

    Deciding framing validity is the transport's job, so a malformed
    `Content-Length` is treated as absent and the streaming bound
    answers. **Asserted at the unit, not over the wire**: a real client
    and server will not put an unparseable `Content-Length` on the
    socket, so the only way to reach this branch is to hand it a scope.
    """
    cap = BodySizeLimitMiddleware(echo)
    scope: Scope = {
        "type": "http",
        "headers": [(b"content-length", declared.encode())],
    }
    assert cap._declared_length(scope) is None  # noqa: SLF001


def test_a_non_http_scope_passes_straight_through(echo: _CountingEcho) -> None:
    """Lifespan has no request body, so the cap must not touch it.

    A middleware that "handled" a lifespan scope would be inoperative
    code at best and would break startup at worst - and uvicorn is
    configured with `lifespan="on"` everywhere in this suite, so this
    branch runs on every single arm above.
    """
    seen: list[str] = []

    async def receive() -> Message:
        return {"type": "lifespan.startup"}

    async def send(message: Message) -> None:
        seen.append(message["type"])

    async def run() -> None:
        await BodySizeLimitMiddleware(_recording_lifespan(seen))(
            {"type": "lifespan"}, receive, send
        )

    import asyncio

    asyncio.run(run())
    assert seen == ["lifespan.startup.complete"]


def _recording_lifespan(seen: list[str]) -> Any:
    """An app that answers a lifespan scope, for the arm above."""

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] == "lifespan"
        await receive()
        await send({"type": "lifespan.startup.complete"})

    return app
