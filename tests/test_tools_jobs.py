"""`search_jobs` end to end, against the wire (DESIGN.md:1325-1337).

**Every assertion about `request_id` is made on the WIRE RESULT, never
on the `ToolResult` the tool returned.** DESIGN.md:1332-1334 is
explicit that the object-level assertion would pass while the wire
carried nothing, because `ToolResult.to_mcp_result()` short-circuits on
`_raw_mcp_result` before it looks at `meta`. Every case here therefore
drives an in-process `fastmcp.Client` and reads what came back.

A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite (DESIGN.md:1258-1260).
`error_auth_200_body401.json` is the one exception in this file: it is
a **recorded** capture of real Jobvite transport, and the trap it
carries is the only Critical on the client.
"""

from __future__ import annotations

import ast
import json
import pathlib
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import pytest
from fastmcp import Client
from loguru import logger
from pydantic import SecretStr, ValidationError

from fast_mcp_jobvite.audit import AUDIT_EVENT_NAME, Transport
from fast_mcp_jobvite.config import READ_TOOLS, SEARCH_JOBS, Settings
from fast_mcp_jobvite.errors import EXTERNAL_SERVICE_ERROR, REQUIRED_MEMBERS
from fast_mcp_jobvite.models.fencing import (
    Fenced,
    FencingDecision,
    MissingFencingDecisionError,
    fencing_paths,
)
from fast_mcp_jobvite.models.jobs import (
    JOBS_ENVELOPE_KEY,
    Job,
    JobSearchResult,
)
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.services.jobvite_client import JobviteClient
from fast_mcp_jobvite.tools.jobs import (
    JOBS_PATH,
    REQUEST_ID_META_KEY,
    SearchJobsInput,
    build_result,
)

from .conftest import FIXTURES_DIR

TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
SPAN_ID = "00f067aa0ba902b7"

TOOLS_SOURCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "src"
    / "fast_mcp_jobvite"
    / "tools"
    / "jobs.py"
)


@pytest.fixture
def audit_records() -> Iterator[list[dict[str, Any]]]:
    """Capture the real loguru stream this server writes to.

    A capturing sink and not a fake logger: an assertion that the
    audit id matches the wire id is worth nothing if the audit stream
    it reads is one the test invented.
    """
    captured: list[dict[str, Any]] = []

    def sink(message: Any) -> None:
        captured.append(dict(message.record))

    sink_id = logger.add(sink, level="DEBUG")
    try:
        yield captured
    finally:
        logger.remove(sink_id)


def audit_event(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the one `tool_invocation` record's structured fields.

    Asserts there is exactly one **before** reading it, so a case that
    matches an id against "the audit event" cannot silently be
    matching against the first of several, or against none.
    """
    events = [r for r in records if r["message"] == AUDIT_EVENT_NAME]
    assert len(events) == 1, f"expected one audit event, got {len(events)}"
    return dict(events[0]["extra"])


def settings(**overrides: Any) -> Settings:
    """Build validated-shaped settings for a jobs-only server."""
    base: dict[str, Any] = {
        "tools": SEARCH_JOBS,
        "api_key": SecretStr("test-api-key"),
        "api_secret": SecretStr("test-api-secret"),
    }
    base.update(overrides)
    return Settings(**base)


def client_factory(
    body: bytes,
    status: int = 200,
    seen: list[httpx2.Request] | None = None,
) -> Callable[[], JobviteClient]:
    """Build a `JobviteClient` on `MockTransport` (ADR-0007).

    No third-party mocking library, which matters because a
    credential-free test strategy cannot afford to depend on one
    (DESIGN.md:1359-1360).
    """

    def make() -> JobviteClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            if seen is not None:
                seen.append(request)
            return httpx2.Response(status, content=body)

        return JobviteClient(
            api_key=SecretStr("test-api-key"),
            api_secret=SecretStr("test-api-secret"),
            transport=httpx2.MockTransport(handler),
        )

    return make


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


JOB_LIST_SUCCESS = "job_list_success.json"
ERROR_200_BODY_401 = "error_auth_200_body401.json"


# ======================================================================
# THE TOOL, END TO END. DESIGN.md:1325-1337 and the plan's U5 bullets.
# ======================================================================


async def test_search_jobs_returns_a_typed_result_over_the_wire() -> None:
    """An in-process Client gets a typed result from MockTransport."""
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    content = result.structured_content
    assert content is not None
    assert [job["eid"] for job in content["jobs"]] == ["TESTJOB1", "TESTJOB2"]
    assert content["jobs"][0]["title"] == "Fixture Position"
    assert content["jobs"][0]["locations"][0]["city"] == "Fixtureville"
    # Epoch milliseconds pass through as integers. SS9 hazard 2's
    # normalisation is U8's `utils/normalise.py`, not this unit's.
    assert content["jobs"][0]["last_updated_date"] == 1700000004000
    assert result.is_error is False


async def test_the_recorded_200_with_401_body_is_a_502_problem() -> None:
    """The trap: HTTP 200, `status.code` 401 (C5-S1).

    The registry's answer is `/problems/external-service-error` **502**
    - never Jobvite's own 401, which would tell the caller *their*
    credentials failed when the credential that failed is the one this
    server holds (DESIGN.md:502-509).
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(ERROR_200_BODY_401))
    )
    async with Client(server) as client:
        result = await client.call_tool(
            SEARCH_JOBS, {"params": {}}, raise_on_error=False
        )

    assert result.is_error is True
    problem = result.structured_content
    assert problem is not None
    assert problem["type"] == EXTERNAL_SERVICE_ERROR.type
    assert problem["status"] == 502
    assert set(REQUIRED_MEMBERS) <= set(problem)
    # Jobvite's own status is preserved in `detail`, never in `status`
    # (DESIGN.md:532-534).
    assert "401" in problem["detail"]
    assert problem["status"] != 401


# ======================================================================
# SS8 #16 - request_id, on the WIRE, matched against the audit event.
# The two arms travel by DIFFERENT channels and are different
# assertions rather than a repetition (DESIGN.md:632-638).
# ======================================================================


async def test_case16_read_arm_request_id_on_the_wire_meta(
    audit_records: list[dict[str, Any]],
) -> None:
    """Success: the id is in `_meta`, and matches the audit event.

    **And the structured content still validates against the output
    model**, which is the half that catches the tempting fix of
    declaring `request_id` as a model field: `additionalProperties` is
    false, so an undeclared top-level key is rejected outright
    (DESIGN.md:639-650).
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    assert result.meta is not None, "no _meta reached the wire at all"

    # THE KEY IS SPELLED OUT, not read from the constant the source
    # uses. Found by mutation: renaming `REQUEST_ID_META_KEY` moved
    # this assertion with it, so the test passed against a server
    # publishing the id under a key no caller could guess - and
    # DESIGN.md:646-650 makes the documented key the whole point,
    # because "an id a caller cannot reach discharges nothing".
    # An assertion that reads the constant under test cannot see it
    # change.
    assert REQUEST_ID_META_KEY == "com.evolvconsulting.fast-mcp-jobvite/requestId"
    wire_id = result.meta["com.evolvconsulting.fast-mcp-jobvite/requestId"]
    assert wire_id == audit_event(audit_records)["request_id"]

    content = result.structured_content
    assert content is not None
    assert "request_id" not in content

    # The content validated against the output model, and the STRONG
    # half of that claim is already discharged above: this call used
    # `raise_on_error=True`, and `ClientSession.validate_tool_result`
    # validates structured content against the cached output schema
    # unconditionally. A payload that did not satisfy the schema would
    # have raised before reaching this line - measured, by pointing a
    # tool at a schema its result violates and watching the client
    # refuse it.
    #
    # `model_validate` is the obvious instrument here and is the WRONG
    # one: a serialised payload carries the two `computed_field`s, and
    # re-validating it under `extra="forbid"` fails with "Extra inputs
    # are not permitted" for `showing` and `summary`. That failure
    # would say the design is broken when what is broken is the
    # instrument - a model with computed fields does not round-trip
    # through its own validator by construction.
    #
    # So the explicit arm asserts the schema's own `required` set is
    # satisfied, which needs no dependency this project has not pinned.
    schema = JobSearchResult.model_json_schema(mode="serialization")
    assert set(schema["required"]) <= set(content)


async def test_case16_error_arm_request_id_in_the_problem_object(
    audit_records: list[dict[str, Any]],
) -> None:
    """Error: the id travels in the problem's own `request_id` member.

    A different channel from the read arm's `_meta`, and therefore a
    different assertion (DESIGN.md:632-638). The `instance` URN is
    built from the same id, so a mismatch between them would mean the
    problem was assembled from two invocations.
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(ERROR_200_BODY_401))
    )
    async with Client(server) as client:
        result = await client.call_tool(
            SEARCH_JOBS, {"params": {}}, raise_on_error=False
        )

    problem = result.structured_content
    assert problem is not None
    audited = audit_event(audit_records)["request_id"]
    assert problem["request_id"] == audited
    assert problem["instance"].endswith(audited)
    # DESIGN.md:621-622 requires the id on EVERY result, so the
    # error arm carries it in `_meta` as well - but the problem
    # member is what `error-contract.md` specifies and is asserted
    # above in its own right.
    assert result.meta is not None
    assert result.meta[REQUEST_ID_META_KEY] == audited


async def test_the_audit_event_records_this_invocation(
    audit_records: list[dict[str, Any]],
) -> None:
    """POSITIVE CONTROL for the two id cases above.

    Both match an id against "the audit event". Against a server that
    emits no audit event at all, `audit_event` would fail - but a
    reader cannot see that from those cases. This one states it:
    the mandated fields of `ai/tool-calling.md:171-173` are present.
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        requested_id = "TESTJOB1"
        await client.call_tool(SEARCH_JOBS, {"params": {"ids": requested_id}})

    event = audit_event(audit_records)
    assert event["tool_name"] == SEARCH_JOBS
    assert event["result_status"] == "success"
    assert event["latency_ms"] >= 0
    assert event["transport"] == "stdio"

    # `ids` is now IN THE CLEAR, and the deliberate act U5 declined to
    # take has been taken by the allow-list's owner: its value is a
    # Jobvite `eId`, structurally the same identifier as `eId` and
    # `job_id`, which were already admitted. U5 was right to report it
    # rather than edit a fail-closed security allow-list from a passing
    # unit.
    #
    # This assertion pins the VALUE, not merely that the key is present.
    # `{"ids": "[REDACTED:str]"}` and `{"ids": "abc123"}` are both
    # dict-shaped and both truthy, so an assertion on the key alone
    # would pass whichever way the allow-list went.
    assert event["arguments"] == {"ids": requested_id}


async def test_the_audit_event_records_an_error_as_an_error(
    audit_records: list[dict[str, Any]],
) -> None:
    """The failing arm is recorded as `error`, not as `success`.

    Paired with the case above: a `result_status` that is always
    `"success"` passes that one, and only a failing invocation can
    tell the difference.
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(ERROR_200_BODY_401))
    )
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {}}, raise_on_error=False)

    assert audit_event(audit_records)["result_status"] == "error"


# ======================================================================
# THE RESULT CAP. Reports, never truncates silently.
# ======================================================================


async def test_the_result_cap_reports_showing_n_of_total() -> None:
    """A capped page says so rather than truncating (DESIGN.md:469-477).

    `total` is the ENVELOPE's own value, so `showing 1 of 2` is only
    reachable if the cap is applied to the items and the total is read
    from Jobvite. Counting the returned items instead would make
    `showing N of N` true on every call.
    """
    server = build_server(
        settings(max_results=1),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS)),
    )
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    content = result.structured_content
    assert content is not None
    assert content["showing"] == 1
    assert content["total"] == 2
    assert content["summary"] == "showing 1 of 2"
    assert len(content["jobs"]) == 1


async def test_an_uncapped_page_is_not_reported_as_capped() -> None:
    """POSITIVE CONTROL for the cap: it does not fire on every call.

    DESIGN.md:469-473 says wiring the completeness signal to every
    call would fire it on the default path and train everyone to
    ignore it. Without this arm a cap that always fired would pass the
    case above.
    """
    server = build_server(
        settings(max_results=50),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS)),
    )
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    content = result.structured_content
    assert content is not None
    assert content["summary"] == "showing 2 of 2"


def test_the_cap_reads_total_from_the_envelope_not_from_the_items() -> None:
    """`total` is Jobvite's, and is never recomputed.

    Driven directly rather than through the wire because it needs a
    `total` that disagrees with the page - DESIGN.md:487-489's "total
    is reported and never trusted" only has teeth when the two differ.
    """
    payload = {
        JOBS_ENVELOPE_KEY: [{"eId": "A", "title": "One"}],
        "total": 1240,
    }
    result = build_result(payload, max_results=50)
    assert result.total == 1240
    assert result.showing == 1
    assert result.summary == "showing 1 of 1,240"


# ======================================================================
# CONTAINMENT. The output allow-list drops what it does not admit.
# ======================================================================


def test_an_unadmitted_jobvite_field_is_dropped_not_returned() -> None:
    """An unadmitted Jobvite field is dropped (DESIGN.md:192-195)."""
    payload = {
        JOBS_ENVELOPE_KEY: [
            {
                "eId": "A",
                "title": "One",
                "salaryBand": "SECRET-INTERNAL-BAND",
                "gender": "unexpected-eeo-field",
            }
        ],
        "total": 1,
    }
    dumped = json.dumps(build_result(payload, max_results=50).model_dump(mode="json"))
    assert "SECRET-INTERNAL-BAND" not in dumped
    assert "salaryBand" not in dumped
    assert "gender" not in dumped


def test_an_unadmitted_field_does_not_fail_the_call() -> None:
    """PAIRED with the case above, and it is the direction that matters.

    DESIGN.md:192-195 requires an unknown field to be **dropped**, not
    to be an error. A model handed Jobvite's object directly with
    `extra="forbid"` would also keep the field out of the result - by
    raising, and taking the whole call down on a Jobvite schema
    change. The absence assertion above cannot tell those apart.
    """
    payload = {
        JOBS_ENVELOPE_KEY: [{"eId": "A", "title": "One", "brandNewField": 1}],
        "total": 1,
    }
    result = build_result(payload, max_results=50)
    assert [job.eid for job in result.jobs] == ["A"]


# ======================================================================
# THE FENCING-DECISION REGISTRY (DESIGN.md:202-205).
# ======================================================================


def test_every_job_model_field_has_a_fencing_decision() -> None:
    """The case DESIGN.md:202-205 requires, over the whole model.

    Generated, never hand-listed: the paths are derived from the model
    itself, so a field added tomorrow is covered by this case on the
    day it is added rather than on the day someone remembers to widen
    a literal.
    """
    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
    assert paths, "no fencing paths were generated at all"
    for path, decision in paths.items():
        assert isinstance(decision, Fenced)
        assert decision.reason.strip(), f"{path} has a decision with no reason"


def test_the_generated_paths_are_in_jobvites_key_space() -> None:
    """CamelCase Jobvite paths, not snake_case model attributes.

    DESIGN.md:202-205's whole reason for generating rather than
    hand-maintaining is that the two lists live in different key
    spaces. A generator that emitted our attribute names would look
    correct and match nothing Jobvite ever sends.
    """
    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
    assert "requisitions[].eId" in paths
    assert "requisitions[].applyLink" in paths
    assert "requisitions[].lastUpdatedDate" in paths
    # The nested model is reached through its list, and the marker
    # says so.
    assert "requisitions[].locations[].city" in paths
    # Our snake_case attribute names must NOT appear.
    assert "requisitions[].apply_link" not in paths
    assert "requisitions[].last_updated_date" not in paths


def test_deleting_a_fencing_decision_fails() -> None:
    """The case that gives the registry teeth.

    DESIGN.md:202-205 requires a test that fails when any model field
    has no fencing decision. Asserted by building a model whose field
    carries none, rather than by mutating `Job` - the property is
    about the mechanism, and a mechanism that only refuses the one
    model we happen to ship is not the mechanism the design asks for.
    """
    from typing import Annotated

    from pydantic import BaseModel

    class Undecided(BaseModel):
        decided: Annotated[str, Fenced(FencingDecision.FENCE, "decided", "why")]
        forgotten: str

    with pytest.raises(MissingFencingDecisionError, match="forgotten"):
        fencing_paths(Undecided, "root")


def test_a_decided_model_still_generates() -> None:
    """POSITIVE CONTROL: the refusal above is not refusing everything.

    A guard that refuses everything is not a guard and its refusals
    prove nothing (DESIGN.md:1370-1371).
    """
    from typing import Annotated

    from pydantic import BaseModel

    class Decided(BaseModel):
        decided: Annotated[str, Fenced(FencingDecision.FENCE, "decided", "why")]

    assert fencing_paths(Decided, "root") == {
        "root.decided": Fenced(FencingDecision.FENCE, "decided", "why")
    }


def test_job_fields_take_an_explicit_not_free_text_decision() -> None:
    """Job data is not the attacker-authored class (plan SS U5).

    U8 is where fencing actually fires, on candidate free text. This
    case pins that the decision here was **made** rather than
    defaulted - the distinction the module refuses to blur.
    """
    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
    assert {d.decision for d in paths.values()} == {FencingDecision.NOT_FREE_TEXT}


# ======================================================================
# REGISTRATION AND THE TOOL SURFACE.
# ======================================================================


async def test_the_server_lists_exactly_the_enabled_tools() -> None:
    """`JOBVITE_TOOLS` is the allow-list (DESIGN.md:917-934)."""
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        listed = {tool.name for tool in await client.list_tools()}
    assert listed == {SEARCH_JOBS}


async def test_a_tool_not_named_is_not_registered() -> None:
    """PAIRED with the case above: the gate can also say no.

    `get_candidate` is a read tool, so it is in `READ_TOOLS` and would
    be enabled by default - naming only `search_jobs` must exclude it.
    Without this arm, a `register` that ignored the gate entirely
    would pass the case above.
    """
    assert SEARCH_JOBS in READ_TOOLS
    server = build_server(
        settings(tools="get_candidate"),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS)),
    )
    async with Client(server) as client:
        listed = {tool.name for tool in await client.list_tools()}
    assert SEARCH_JOBS not in listed


async def test_the_server_lists_the_same_tools_on_http() -> None:
    """The tool surface does not depend on the transport (SS7.1).

    Built rather than bound: binding a port in the suite would make
    this a network test, and the property under test is registration,
    which happens before any socket exists.
    """
    server = build_server(
        settings(
            mcp_transport="http",
            mcp_host="127.0.0.1",
            http_tokens=SecretStr('{"t": "client-a"}'),
        ),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS)),
    )
    async with Client(server) as client:
        listed = {tool.name for tool in await client.list_tools()}
    assert listed == {SEARCH_JOBS}


async def test_the_tool_advertises_a_serialisation_output_schema() -> None:
    """The advertised schema must include the computed fields.

    MEASURED: pydantic's default `mode="validation"` omits
    `computed_field`s, and `extra="forbid"` renders as
    `additionalProperties: false` - so the client rejects our own
    success payload with "Additional properties are not allowed". The
    failure is loud but its cause is not, so it is pinned here.
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        tool = next(t for t in await client.list_tools() if t.name == SEARCH_JOBS)

    assert tool.outputSchema is not None
    properties = tool.outputSchema["properties"]
    assert "showing" in properties
    assert "summary" in properties


# ======================================================================
# INBOUND ARGUMENT REJECTION (ADR-0012, DESIGN.md:176-183).
# Every refusal is paired with a positive control.
# ======================================================================


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("NUL", "AB\x00CD"),
        ("bell", "AB\x07CD"),
        ("C1", "AB\x85CD"),
        ("bidi override RLO", "AB‮cd"),
        ("bidi isolate RLI", "AB⁧cd"),
        ("trailing newline", "ABCD\n"),
    ],
)
def test_a_control_character_or_bidi_override_is_rejected(
    label: str, value: str
) -> None:
    """A well-formed short string that every length check admits.

    B25 and DESIGN.md:172-179: `max_length` does not cover this and
    the output allow-list cannot, because it is an output filter.
    """
    with pytest.raises(ValidationError):
        SearchJobsInput(ids=value)


def test_an_ordinary_identifier_still_passes() -> None:
    """POSITIVE CONTROL for the rejections (DESIGN.md:1370-1371)."""
    assert SearchJobsInput(ids="TESTJOB1").ids == "TESTJOB1"


def test_an_unknown_argument_is_refused() -> None:
    """`extra="forbid"`: never a free-form dict (DESIGN.md:152-153)."""
    with pytest.raises(ValidationError):
        SearchJobsInput(datestart="2026-01-01")  # type: ignore[call-arg]


async def test_a_rejected_argument_fails_closed_before_the_tool_body(
    audit_records: list[dict[str, Any]],
) -> None:
    """Pre-dispatch rejection reaches no tool body (DESIGN.md:548-568).

    **And carries no problem object**, which is SS5.1's third
    exception: the rejection is *raised* by the framework rather than
    returned, so nothing can return one. Asserted by the audit stream
    being empty - the body never ran, so it never audited.
    """
    seen: list[httpx2.Request] = []
    server = build_server(
        settings(),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS), seen=seen),
    )
    async with Client(server) as client:
        with pytest.raises(Exception):  # noqa: B017, PT011 - the shape is the point
            await client.call_tool(SEARCH_JOBS, {"params": {"ids": "AB\x00CD"}})

    assert seen == [], "a rejected argument still reached the transport"
    assert not [r for r in audit_records if r["message"] == AUDIT_EVENT_NAME]


# ======================================================================
# THE OUTBOUND REQUEST (R4-H1).
#
# Nothing in this file read `seen[0].url` before these three cases:
# the route, the query key and the query value were all unasserted,
# so all three could be broken and the whole suite stayed green.
# Measured by `docs/reviews/probe-r4-unmutated-anchors.sh` - rows P1,
# P2 and P3 all SURVIVED 413 passed.
#
# The failure they admit is the one `SearchJobsInput`'s own docstring
# says the date filter was withheld to avoid: Jobvite ignores a
# parameter it does not recognise and answers with the whole first
# page, so a caller asking for one job gets 50 and the result says so
# - a wrong answer that explains itself.
# ======================================================================


async def test_the_ids_argument_reaches_the_wire_as_a_query_parameter() -> None:
    """The route AND the query key AND the value, on the wire.

    All three in one case on purpose: they are one decision - "this
    tool asks Jobvite for this job at this route" - and splitting
    them would let two thirds of it be deleted with one row still
    green.
    """
    seen: list[httpx2.Request] = []
    server = build_server(
        settings(),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS), seen=seen),
    )
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {"ids": "TESTJOB1"}})

    # THE ROUTE IS PINNED AS A LITERAL, not as JOBS_PATH. Asserting
    # against the constant was MEASURED to survive mutating that
    # constant - the assertion moves with it, which is the M3 defect
    # this harness exists to catch, reappearing inside its own fix.
    assert len(seen) == 1
    assert JOBS_PATH == "/job"
    assert seen[0].url.path.endswith("/job")
    assert seen[0].url.params["ids"] == "TESTJOB1"


async def test_omitting_ids_sends_no_ids_parameter() -> None:
    """The paired direction, and it is not decoration.

    A default call must send NO filter. An implementation that always
    sent `ids=` - empty, or a sentinel - would pass the case above and
    would silently filter every unfiltered listing to nothing.
    """
    seen: list[httpx2.Request] = []
    server = build_server(
        settings(),
        client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS), seen=seen),
    )
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {}})

    assert len(seen) == 1
    assert "ids" not in seen[0].url.params
    assert seen[0].url.path.endswith("/job")


# ======================================================================
# THE THREE COMPOSITION RISKS THE EARLIER UNITS COULD NOT CLOSE.
# ======================================================================


async def test_config_secretstr_satisfies_the_clients_protocol() -> None:
    """COMPOSITION RISK 1: `SecretStr` -> `SecretValue`.

    U4 declared a structural Protocol rather than importing pydantic,
    and nothing had ever passed one through. This drives the real
    credential into the real header builder and reads it back off the
    request the transport saw.
    """
    seen: list[httpx2.Request] = []
    real = Settings(
        tools=SEARCH_JOBS,
        api_key=SecretStr("live-api-key"),
        api_secret=SecretStr("live-api-secret"),
    )

    def make() -> JobviteClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(200, content=fixture_bytes(JOB_LIST_SUCCESS))

        assert real.api_key is not None
        assert real.api_secret is not None
        return JobviteClient(
            api_key=real.api_key,
            api_secret=real.api_secret,
            transport=httpx2.MockTransport(handler),
        )

    server = build_server(real, client_factory=make)
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {}})

    assert len(seen) == 1
    assert seen[0].headers["x-jvi-api"] == "live-api-key"
    assert seen[0].headers["x-jvi-sc"] == "live-api-secret"


def test_composition_risk2_the_transport_spellings_agree() -> None:
    """COMPOSITION RISK 2: U3's `Transport` vs U1's `mcp_transport`.

    "One grep settles whether the audit event's `transport` field
    agrees with the rest of the server. Nothing currently fails if it
    does not." This is that check, as an assertion: the two sets are
    compared for EQUALITY rather than one being tested for membership
    in the other, because a subset relation is satisfied by a spelling
    either side has and the other does not.
    """
    from typing import get_args

    declared = set(get_args(Settings.model_fields["mcp_transport"].annotation))
    assert {t.value for t in Transport} == declared


async def test_composition_risk3_the_live_context_meta_is_the_wire_meta(
    audit_records: list[dict[str, Any]],
) -> None:
    """COMPOSITION RISK 3: `ctx.request_context.meta` on a LIVE context.

    U3 tested its parse call site against the wire contract because no
    server existed to get a context from. There is one now. If `meta`
    were not a plain mapping of the wire `_meta`, U3's call site would
    be wrong and no existing test would say so.
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        await client.call_tool(
            SEARCH_JOBS, {"params": {}}, meta={"traceparent": TRACEPARENT}
        )

    event = audit_event(audit_records)
    assert event["trace_id"] == TRACE_ID
    assert event["span_id"] == SPAN_ID


async def test_trace_context_is_absent_when_the_caller_sends_none(
    audit_records: list[dict[str, Any]],
) -> None:
    """The second arm SS8 requires, and it is the one that matters.

    A field that is always absent and a field that is always
    synthesised each pass a single-arm test. A minted id in a field
    named for the host's trace looks like a join and is not one
    (DESIGN.md:663-665).
    """
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS))
    )
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {}})

    event = audit_event(audit_records)
    assert "trace_id" not in event
    assert "span_id" not in event


# ======================================================================
# THE RULE WITH NO GATE - now it has one.
# ======================================================================


def test_no_module_scope_credential_read_in_the_tool_module() -> None:
    """Collection IMPORTS every module in `testpaths`.

    `tests/credentialed/README.md` forbids module-scope credential
    reads, and the rule had no gate. A credential read at module scope
    executes during collection - on every offline run that
    deliberately deselects those tests, and in CI.

    **Walks the AST rather than grepping**, because a grep for
    `os.environ` matches this docstring, and a test that passes
    because its own prose contains the string it searches for is the
    exact vacuous shape amputation found in U3.
    """
    tree = ast.parse(TOOLS_SOURCE.read_text())
    offenders = []
    for node in tree.body:
        # Only module-scope statements. A read inside a function body
        # is exactly what the README asks for.
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Attribute) and inner.attr in {
                "environ",
                "getenv",
            }:
                offenders.append(ast.unparse(inner))
    assert offenders == []
