"""The dual-era approval guard and `create_candidate`, end to end.

**THE ROW COUNTER AND THE APPROVED-WRITE CONTROL ARE THE FIRST TWO
THINGS IN THIS FILE AND THEY WERE WRITTEN BEFORE `approval.py` EXISTED.**
`IMPLEMENTATION-PLAN.md` §U10 says why, and it is not a style
preference: four refusal arms below all assert *the row count did not
move*, and every one of them passes perfectly against a
`create_candidate` that is broken and never writes at all - the
guard-that-refuses-everything of DESIGN.md:1370-1371.
`FASTMCP-SPIKE-4.md:1431` is the spike recording exactly that failure
against itself: a first run refused all six arms, looked like a perfect
security result, and was a token-parsing bug.

So `_JobviteRows` counts rows on the server side of a
`httpx2.MockTransport`, exactly as the spike ran it, and
`test_positive_control_*` asserts an APPROVED write moves that counter
**by exactly one, on both eras**. Nothing else in this file means
anything without them.

**WHAT THIS FILE MAY NEVER ASSERT, AND THE RULE IS ABSOLUTE.** It
asserts that the server requires an approval response from the host and
refuses to write without one. It never asserts, implies or names a
human: a host may auto-respond with no person present, which is C4-S1,
a **High residual** that is **not mitigable server-side**
(DESIGN.md:1754, ADR-0009).

A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite (DESIGN.md:1258-1260). The
`201` body here is `docs/research/fixtures/candidate_create_success.json`
and it is synthetic - `JOBVITE-CONTRACT.md:260` marks the whole write
contract `[INFERRED]`, and checklist row 10 is what replaces it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import pytest
from fastmcp import Client
from loguru import logger
from pydantic import SecretStr

from fast_mcp_jobvite.audit import AUDIT_EVENT_NAME
from fast_mcp_jobvite.config import CREATE_CANDIDATE, Settings
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.services.jobvite_client import JobviteClient

from .conftest import FIXTURES_DIR

#: The two eras, by the name the client's own `mode` argument takes.
#: `auto` negotiates the sessionless `2026-07-28`; `legacy` pins the
#: handshake `2025-11-25` (`FASTMCP-SPIKE-4.md:2066-2068`).
SESSIONLESS_MODE = "auto"
HANDSHAKE_MODE = "legacy"
BOTH_ERAS = (SESSIONLESS_MODE, HANDSHAKE_MODE)

CREATE_SUCCESS = "candidate_create_success.json"

VALID_ARGS: dict[str, Any] = {
    "first_name": "Testcandidate",
    "last_name": "Omega",
    "email": "testcandidate.omega@example.invalid",
    "job_eid": "TESTJOB1",
}


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def settings(**overrides: Any) -> Settings:
    """Build validated-shaped settings for a write-enabled server.

    Both gates are satisfied here on purpose: `JOBVITE_ENABLE_WRITES`
    **and** the name in `JOBVITE_TOOLS` (DESIGN.md:925). The cases that
    withhold one of them do so explicitly.
    """
    base: dict[str, Any] = {
        "tools": CREATE_CANDIDATE,
        "enable_writes": True,
        "api_key": SecretStr("test-api-key"),
        "api_secret": SecretStr("test-api-secret"),
    }
    base.update(overrides)
    return Settings(**base)


# ======================================================================
# THE SERVER-SIDE ROW COUNTER. WRITTEN FIRST, BEFORE `approval.py`
# EXISTED, BECAUSE EVERY REFUSAL ARM BELOW IS AN ASSERTION ABOUT IT.
# ======================================================================


class _JobviteRows:
    """A fake Jobvite that counts the rows it was asked to create.

    **This is the control the whole file rests on**, and it is the
    construction `FASTMCP-SPIKE-4.md:2118-2143` ran: a counter on the
    server side of the transport, read before and after each arm.

    It counts the **request that reached the wire**, not a call the tool
    made to itself, which is the difference between measuring the write
    and measuring our own bookkeeping. A non-`POST` on this route is a
    hard failure rather than a quiet 200: this fake exists to notice a
    write, and a read arriving here means the tool did something other
    than the thing under test.
    """

    def __init__(self, *, status: int = 201, body: bytes | None = None) -> None:
        self.status = status
        self.body = fixture_bytes(CREATE_SUCCESS) if body is None else body
        #: One entry per POST that reached the transport. `len()` is the
        #: row count; the bodies are kept so an arm can assert what was
        #: actually sent.
        self.rows: list[dict[str, Any]] = []
        self.requests: list[httpx2.Request] = []

    @property
    def count(self) -> int:
        """The number of candidate rows created so far."""
        return len(self.rows)

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if request.method != "POST":
            msg = f"the fake ATS was asked for {request.method}, not a write"
            raise AssertionError(msg)
        self.rows.append(json.loads(request.content or b"{}"))
        return httpx2.Response(self.status, content=self.body)

    def factory(self) -> Callable[[], JobviteClient]:
        def make() -> JobviteClient:
            return JobviteClient(
                api_key=SecretStr("test-api-key"),
                api_secret=SecretStr("test-api-secret"),
                transport=httpx2.MockTransport(self.handler),
            )

        return make


async def approve_everything(
    message: str,
    response_type: type | None,
    params: Any,  # noqa: ANN401 - the framework's own params union
    context: Any,  # noqa: ANN401 - the SDK's client request context
) -> dict[str, Any]:
    """An elicitation handler that answers `approve: true`.

    **It is a HOST auto-responder and nothing else.** That is exactly
    C4-S1's shape - a host may answer with no person present - and it is
    why no assertion in this file says a human approved anything.
    """
    return {"approve": True}


async def deny_everything(
    message: str,
    response_type: type | None,
    params: Any,  # noqa: ANN401 - the framework's own params union
    context: Any,  # noqa: ANN401 - the SDK's client request context
) -> Any:  # noqa: ANN401 - an ElicitResult, typed by the framework
    """An elicitation handler that DECLINES."""
    from fastmcp.client.elicitation import ElicitResult

    return ElicitResult(action="decline", content=None)


async def accept_but_refuse(
    message: str,
    response_type: type | None,
    params: Any,  # noqa: ANN401 - the framework's own params union
    context: Any,  # noqa: ANN401 - the SDK's client request context
) -> Any:  # noqa: ANN401 - an ElicitResult, typed by the framework
    """`action == "accept"` carrying `approve: false`.

    **The arm people drop.** An accepted elicitation carrying
    `approve: false` is still an acceptance, which is why
    DESIGN.md:1075-1078 makes the guard a conjunction rather than an
    action check.
    """
    from fastmcp.client.elicitation import ElicitResult

    return ElicitResult(action="accept", content={"approve": False})


@pytest.fixture
def audit_records() -> Iterator[list[dict[str, Any]]]:
    """Capture the real loguru stream this server writes to."""
    captured: list[dict[str, Any]] = []

    def sink(message: Any) -> None:  # noqa: ANN401 - loguru's own message type
        captured.append(dict(message.record))

    sink_id = logger.add(sink, level="DEBUG")
    try:
        yield captured
    finally:
        logger.remove(sink_id)


def audit_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every `tool_invocation` record's structured fields, in order."""
    return [dict(r["extra"]) for r in records if r["message"] == AUDIT_EVENT_NAME]


# ======================================================================
# 1. THE POSITIVE CONTROL. WRITTEN FIRST, ON BOTH ERAS.
#    IMPLEMENTATION-PLAN.md §U10, DESIGN.md:1370-1371.
# ======================================================================


@pytest.mark.parametrize("mode", BOTH_ERAS)
async def test_positive_control_an_approved_write_moves_the_row_counter_by_one(
    mode: str,
) -> None:
    """An APPROVED write creates exactly one row, on both eras.

    **This is the case the whole unit is ordered around.** Four refusal
    arms below assert that the row counter did not move, and every one
    of them passes against a `create_candidate` that never writes at
    all. This case is what makes them mean something, so it asserts the
    opposite: the counter moves, by exactly one, and the identifiers
    Jobvite minted reach the caller.

    **It says nothing about a human.** The handler is a host
    auto-responder (C4-S1).
    """
    ats = _JobviteRows()
    server = build_server(settings(), client_factory=ats.factory())

    assert ats.count == 0, "the counter is not at zero before the write"

    async with Client(
        server, mode=mode, elicitation_handler=approve_everything
    ) as client:
        result = await client.call_tool(CREATE_CANDIDATE, {"params": VALID_ARGS})

    assert result.is_error is False, result.content
    assert ats.count == 1, (
        f"expected exactly one row on {mode}; the counter went 0 -> {ats.count}"
    )

    content = result.structured_content
    assert content is not None
    assert content["candidate_eid"] == "TESTCND9"
    assert content["application_eid"] == "TESTAPP9"
