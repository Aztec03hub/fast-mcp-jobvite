"""`get_job_feed` end to end, and the one arm that carries a High.

**C5-I1 is the reason this unit is late rather than part of U5**
(`DESIGN.md:1776`). `GET /v1/jobFeed` structurally requires `api`, `sc`
and `companyId` as **query parameters** (DESIGN.md:312-318), so it is
the one route in this server whose URL is itself a credential.

**THE ABSENCE ARM IS PAIRED, AND THE PAIRING IS THE WHOLE POINT.**
DESIGN.md:1264-1270 states it as two cases that cannot be satisfied by
silence: *"the log stream carries records for an invocation that
produced them ... untestable against a stream nothing proves
non-empty"*, and then *"a secret never reaching a log record, including
the `jobFeed` URL - asserted against the log stream the case above
proves non-empty"*. Against a logger emitting nothing, an assertion
that `sc=` is absent passes trivially and reports a High as mitigated.

So the positive case below - the one whose name ends
`_carrying_its_non_secret_attributes` - and
`test_case2_no_log_record_carries_the_jobfeed_secret` read **the same
captured stream from the same call**, and the positive one asserts
a record produced *by this invocation* is in it - the client's own
`jobvite request` line, carrying the request's method and route, plus
the audit event. Neither can pass on an empty stream.

**The round-trip cases below do NOT close C5-I1.** They prove the tool
returns data; they say nothing about whether the logger emitted
anything, which is exactly the gap the pairing exists to fill.

The sink is a real `loguru` sink added to the logger `src/` writes to,
never a fake logger: an assertion about redaction is worth nothing if
the stream it reads is one the test invented (`test_logging_process.py`
records that failure happening).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import pytest
from fastmcp import Client
from loguru import logger
from pydantic import SecretStr, ValidationError

from fast_mcp_jobvite.audit import AUDIT_EVENT_NAME
from fast_mcp_jobvite.config import GET_JOB_FEED, SEARCH_JOBS, Settings
from fast_mcp_jobvite.models.job_feed import JOB_FEED_ENVELOPE_KEY, JobFeedResult
from fast_mcp_jobvite.models.jobs import JOBS_ENVELOPE_KEY
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.services.jobvite_client import (
    JOBFEED_PATH,
    V1_BASE_URL,
    JobviteClient,
)
from fast_mcp_jobvite.tools.jobs import (
    REQUEST_ID_META_KEY,
    GetJobFeedInput,
    build_feed_result,
)

from .conftest import FIXTURES_DIR

JOBFEED_SUCCESS = "jobfeed_success.json"
JOBFEED_EMPTY = "jobfeed_empty.json"

#: The three credential values this module drives every call with.
#: **Deliberately distinct from `search_jobs`' pair**, because a test
#: that used one value for both could not tell the two credential
#: classes apart - and telling them apart is DESIGN.md:320-321's whole
#: reason for having three (§7.2's token-scoping axis).
FEED_KEY = "feed-key-value-U12"
FEED_SECRET = "feed-secret-value-U12"  # noqa: S105 - a test literal
COMPANY_ID = "company-id-value-U12"
API_KEY = "v2-api-key-not-the-feeds"
API_SECRET = "v2-api-secret-not-the-feeds"  # noqa: S105 - a test literal


@pytest.fixture
def log_records() -> Iterator[list[dict[str, Any]]]:
    """Capture the real loguru stream this server writes to.

    `level="DEBUG"` because the client's request line is emitted at
    DEBUG (`jobvite_client.py:request`), and a sink added at INFO would
    make the positive arm of the C5-I1 pairing fail for a reason that
    has nothing to do with the behaviour under test.
    """
    captured: list[dict[str, Any]] = []

    def sink(message: Any) -> None:
        captured.append(dict(message.record))

    sink_id = logger.add(sink, level="DEBUG")
    try:
        yield captured
    finally:
        logger.remove(sink_id)


def record_text(record: dict[str, Any]) -> str:
    """Render one log record as the text a sink could publish.

    **Message AND `extra` AND the exception**, because a redactor that
    covered only the formatted message would leave the credential in a
    structured field, and a JSON sink publishes every one of them. This
    is what makes the absence assertion below an assertion about the
    RECORD rather than about one of its fields.
    """
    parts = [str(record.get("message", ""))]
    parts.append(json.dumps(record.get("extra", {}), default=str))
    exception = record.get("exception")
    if exception is not None:
        parts.append(str(exception))
    return " ".join(parts)


def settings(**overrides: Any) -> Settings:
    """Build validated-shaped settings for a feed-enabled server."""
    base: dict[str, Any] = {
        "tools": GET_JOB_FEED,
        "feed_key": SecretStr(FEED_KEY),
        "feed_secret": SecretStr(FEED_SECRET),
        "company_id": SecretStr(COMPANY_ID),
    }
    base.update(overrides)
    return Settings(**base)


def client_factory(
    body: bytes,
    status: int = 200,
    seen: list[httpx2.Request] | None = None,
) -> Callable[[], JobviteClient]:
    """A `JobviteClient` on `MockTransport`, with the FEED credentials.

    The factory mirrors what `_register_get_job_feed` builds for a real
    deployment - the feed's key and secret and the `companyId` - so a
    case asserting which credential reached the wire is asserting about
    the same three values the tool would send.
    """

    def make() -> JobviteClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            if seen is not None:
                seen.append(request)
            return httpx2.Response(status, content=body)

        return JobviteClient(
            api_key=SecretStr(FEED_KEY),
            api_secret=SecretStr(FEED_SECRET),
            company_id=SecretStr(COMPANY_ID),
            transport=httpx2.MockTransport(handler),
        )

    return make


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


async def call_feed(
    body: bytes,
    arguments: dict[str, Any] | None = None,
    seen: list[httpx2.Request] | None = None,
    **setting_overrides: Any,
) -> Any:
    """Drive `get_job_feed` over an in-process client, and return it.

    Every case reads what came back over the WIRE rather than the
    `ToolResult` the tool returned, for DESIGN.md:1332-1334's reason:
    `ToolResult.to_mcp_result()` short-circuits on `_raw_mcp_result`
    before it looks at `meta`, so an object-level assertion about
    `_meta` passes while the wire carries nothing.
    """
    server = build_server(
        settings(**setting_overrides),
        client_factory=client_factory(body, seen=seen),
    )
    async with Client(server) as client:
        return await client.call_tool(
            GET_JOB_FEED, {"params": arguments or {}}, raise_on_error=False
        )


# ======================================================================
# C5-I1 - THE PAIR. §8 case #2's shape, one unit later.
# ======================================================================


async def test_case2_the_call_emits_a_log_record_carrying_its_non_secret_attributes(
    log_records: list[dict[str, Any]],
) -> None:
    """THE POSITIVE HALF (DESIGN.md:1264-1268).

    The call emits a record carrying the request's **non-secret**
    attributes: the client's `jobvite request` line, with the HTTP
    method and the route it called. Without this arm, the absence
    assertion beside it passes against a server that logs nothing at
    all, and a High is reported mitigated by silence.

    It asserts on the SAME stream, from the SAME call shape, as
    `test_case2_no_log_record_carries_the_jobfeed_secret`.
    """
    await call_feed(fixture_bytes(JOBFEED_SUCCESS))

    request_lines = [
        record
        for record in log_records
        if record["message"] == "jobvite request"
        and record["extra"].get("method") == "GET"
        and JOBFEED_PATH in str(record["extra"].get("route", ""))
    ]
    assert len(request_lines) == 1, (
        f"expected exactly one jobFeed request line, got {len(request_lines)} "
        f"from {len(log_records)} records. The absence arm beside this test "
        "cannot mean anything against a stream this call did not fill."
    )

    # A SECOND PRODUCER on the same call, so the pairing does not rest
    # on one line either (DESIGN.md:1188-1190's three log producers).
    audit_events = [r for r in log_records if r["message"] == AUDIT_EVENT_NAME]
    assert len(audit_events) == 1, "the invocation emitted no audit event"
    assert audit_events[0]["extra"]["tool_name"] == GET_JOB_FEED


async def test_case2_no_log_record_carries_the_jobfeed_secret(
    log_records: list[dict[str, Any]],
) -> None:
    """THE ABSENCE HALF, and it is only meaningful because of the pair.

    DESIGN.md:315-318: never logged whole, never in an exception
    message, `sc=` redacted before any log line. The assertion is made
    over **every** record the call produced, and over the whole record
    - message, `extra` and exception - because a JSON sink publishes
    all three.

    The pairing is re-established INSIDE this test rather than only in
    the test beside it: a stream that went empty for an unrelated
    reason would otherwise turn this case green.
    """
    await call_feed(fixture_bytes(JOBFEED_SUCCESS))

    rendered = [record_text(record) for record in log_records]
    assert any(
        "jobvite request" in text and JOBFEED_PATH in text for text in rendered
    ), (
        "THE STREAM IS SILENT. Everything below would pass on an empty "
        "list, which is the exact shape ADR-0013 and DESIGN.md:1264-1268 "
        "refuse."
    )

    for text in rendered:
        assert FEED_SECRET not in text, f"the feed secret reached a log record: {text}"
        assert FEED_KEY not in text, f"the feed key reached a log record: {text}"
        assert COMPANY_ID not in text, f"the companyId reached a log record: {text}"
        # THE VALUE, not the token. `sc=[REDACTED]` in a record is the
        # enforcement point having FIRED, and asserting the literal
        # `sc=` were absent would fail on a compliant line and pass on
        # a line that never carried the parameter at all - measured:
        # this assertion was written that way, went green in isolation
        # and red in the full suite, where a THIRD producer
        # (`httpx2`'s own stdlib logger, bridged into loguru by
        # `configure_logging`) had emitted the redacted URL.
        assert f"sc={FEED_SECRET}" not in text, f"`sc=` in the clear: {text}"


async def test_case2_the_url_bearing_producer_emits_it_redacted() -> None:
    """THE ARM THAT MEASURES THE ENFORCEMENT POINT FIRING.

    **`httpx2` logs the request URL itself**, through the stdlib
    logger, at INFO: `HTTP Request: GET <the whole URL> "HTTP/1.1
    200"`. On every other route that line is harmless; on this one it
    carries `api`, `sc` and `companyId`. It is the THIRD log producer
    DESIGN.md:1188-1190 counts and the only one that handles the URL,
    so a C5-I1 arm that never looks at it has not looked at the
    dangerous producer.

    `configure_logging()` is what routes it into loguru, through
    `_InterceptHandler` and `_redact_message`
    (`__main__.py:299-350`) - the second depth at which
    `utils/redaction.py` runs. **This test installs it deliberately
    rather than inheriting it**: in the full suite another module had
    already imported `__main__`, so this record appeared in the stream
    by accident of ordering, and an arm that depends on test order is
    an arm that reports whatever the ordering gives it.

    The assertion is POSITIVE ON BOTH SIDES: the record exists (so the
    stream is not silent and the producer really ran), the URL is in
    it, and `sc=` in that record carries `[REDACTED]` rather than the
    secret. An absence alone could not tell "redacted" from "httpx2
    logged nothing today".
    """
    import logging as stdlib_logging

    from fast_mcp_jobvite.__main__ import configure_logging

    saved_handlers = list(stdlib_logging.root.handlers)
    saved_level = stdlib_logging.root.level
    configure_logging()

    captured: list[dict[str, Any]] = []
    sink_id = logger.add(lambda m: captured.append(dict(m.record)), level="DEBUG")
    try:
        await call_feed(fixture_bytes(JOBFEED_SUCCESS))
    finally:
        logger.remove(sink_id)
        stdlib_logging.root.handlers = saved_handlers
        stdlib_logging.root.setLevel(saved_level)

    http_lines = [
        record
        for record in captured
        if "HTTP Request" in str(record["message"])
        and JOBFEED_PATH in str(record["message"])
    ]
    assert len(http_lines) == 1, (
        f"httpx2's own request line is not in the stream ({len(captured)} records "
        "captured). Without it this test asserts redaction of a line nobody "
        "emitted, which is the silence ADR-0013 refuses."
    )

    message = str(http_lines[0]["message"])
    assert "sc=[REDACTED]" in message, (
        f"the enforcement point did not fire on the URL-bearing line: {message}"
    )
    assert FEED_SECRET not in message
    assert FEED_KEY not in message
    assert COMPANY_ID not in message


async def test_case2_the_url_never_reaches_a_log_record_whole(
    log_records: list[dict[str, Any]],
) -> None:
    """The URL as a whole, not just its secret parameters.

    DESIGN.md:315-316 says *"never logged whole"* as well as *"`sc=`
    redacted"*, and the two are different claims: a line carrying
    `.../v1/jobFeed?api=[REDACTED]&sc=[REDACTED]` has redacted the
    secrets and still published the tenant's feed URL. The client logs
    the ROUTE, and this pins that.
    """
    seen: list[httpx2.Request] = []
    await call_feed(fixture_bytes(JOBFEED_SUCCESS), seen=seen)

    assert len(seen) == 1, "the tool made no request; there is no URL to check"
    sent_url = str(seen[0].url)
    assert "sc=" in sent_url, (
        "the request Jobvite received carries no `sc=`, so this route is not "
        "the one whose URL is a secret and the case below tests nothing"
    )

    request_lines = [r for r in log_records if r["message"] == "jobvite request"]
    assert request_lines, "the stream is silent; everything below passes on nothing"

    for text in (record_text(record) for record in log_records):
        assert sent_url not in text, f"the whole jobFeed URL reached a record: {text}"

    # The route the client logs carries NO query string at all - not a
    # redacted one. `redact_url` would replace the values; logging the
    # route means there is nothing to redact, which is the stronger of
    # the two and the one DESIGN.md:315-316 asks for.
    for record in request_lines:
        route = str(record["extra"]["route"])
        assert "?" not in route, f"the logged route carries a query string: {route}"


# ======================================================================
# THE SEPARATE CREDENTIAL CLASS (DESIGN.md:312-321)
# ======================================================================


async def test_the_feed_credentials_travel_as_query_parameters() -> None:
    """`api`, `sc` and `companyId` in the query string - the exception.

    DESIGN.md:312-314 forbids building a URL containing a credential
    **everywhere else**; DESIGN.md:315 makes this route the one
    structural exception. A test asserting only that the call
    succeeded would pass against a client that sent the v2 headers and
    got a mock's 200 back.
    """
    seen: list[httpx2.Request] = []
    await call_feed(fixture_bytes(JOBFEED_SUCCESS), seen=seen)

    assert len(seen) == 1
    query = dict(seen[0].url.params)
    assert query["api"] == FEED_KEY
    assert query["sc"] == FEED_SECRET
    assert query["companyId"] == COMPANY_ID
    # And the v2 credential headers are NOT sent on this route.
    assert "x-jvi-api" not in {k.lower() for k in seen[0].headers}


async def test_the_route_is_the_v1_base_not_v2() -> None:
    """`/v1/jobFeed`, not `/api/v2/...` (DESIGN.md:434, contract §9).

    Every offline case drives a MockTransport that answers whatever it
    is asked, so the base URL is free unless something asserts it.
    """
    seen: list[httpx2.Request] = []
    await call_feed(fixture_bytes(JOBFEED_SUCCESS), seen=seen)

    assert str(seen[0].url).startswith(f"{V1_BASE_URL}{JOBFEED_PATH}?")


async def test_registering_the_feed_without_its_credentials_refuses_at_boot() -> None:
    """The refusal is at registration, not on the first call.

    `TOOL_REQUIREMENTS[get_job_feed]` already refuses this
    configuration in `validate_settings`, so reaching here is a
    programming error - and the failure belongs where every other
    refusal is (config, at boot) rather than as a 500 the caller sees.
    """
    with pytest.raises(ValueError, match="credentials are unset"):
        build_server(
            Settings(tools=GET_JOB_FEED, feed_key=SecretStr(FEED_KEY)),
        )


# ======================================================================
# THE THIRD ENVELOPE KEY (§9 hazard 3)
# ======================================================================


def test_the_feed_envelope_key_is_jobs_not_requisitions() -> None:
    """Three names for one concept, and this route uses the third.

    Asserted in BOTH directions on the same payload shape: the feed's
    `jobs` array is read, and a `requisitions` array on this route is
    **not** - because a `build_feed_result` that accepted either would
    make the two keys interchangeable, which is precisely the confusion
    §9 hazard 3 records.
    """
    assert JOB_FEED_ENVELOPE_KEY == "jobs"
    assert JOB_FEED_ENVELOPE_KEY != JOBS_ENVELOPE_KEY

    one = {"id": "A", "title": "T"}
    from_feed = build_feed_result({"total": 1, JOB_FEED_ENVELOPE_KEY: [one]}, 50)
    assert [job.eid for job in from_feed.jobs] == ["A"]

    from_v2_key = build_feed_result({"total": 1, JOBS_ENVELOPE_KEY: [one]}, 50)
    assert from_v2_key.jobs == []


async def test_the_caller_sees_one_name_for_the_concept() -> None:
    """The normalisation, asserted on the WIRE payload.

    `search_jobs` returns `jobs`; so does this. Jobvite's third name
    stops at `_to_feed_job` and never reaches a caller, which is what
    "normalise it" means here.
    """
    result = await call_feed(fixture_bytes(JOBFEED_SUCCESS))
    content = result.structured_content
    assert content is not None
    assert "jobs" in content
    assert "requisitions" not in content


# ======================================================================
# ROUND TRIP - the fixtures, both of them
# ======================================================================


async def test_jobfeed_success_round_trips_to_a_typed_result() -> None:
    """`jobfeed_success.json` in, an allow-listed model out."""
    result = await call_feed(fixture_bytes(JOBFEED_SUCCESS))

    content = result.structured_content
    assert content is not None
    assert result.is_error is False
    assert content["total"] == 1
    assert content["showing"] == 1
    assert content["summary"] == "showing 1 of 1"
    job = content["jobs"][0]
    assert job["eid"] == "TESTJOB1"
    assert job["title"] == "Fixture Position"
    assert job["requisition_id"] == "TESTREQ1"
    assert job["job_type"] == "Full-time"
    assert job["location"] == "Fixtureville, ZZ, US"
    assert job["detail_url"] == "https://careers.example.invalid/job/TESTJOB1"
    assert job["apply_url"] == "https://careers.example.invalid/apply/TESTJOB1"
    assert job["brief_description"] == "FIXTURE BRIEF DESCRIPTION"
    assert job["hiring_manager"] == "Fixture Manager"
    # The feed's `date` is a STRING on this route. §9 hazard 2's epoch
    # milliseconds are the v2 side of the same asymmetry.
    assert job["date"] == "2026-01-01"


async def test_jobfeed_empty_round_trips_to_an_empty_page() -> None:
    """`jobfeed_empty.json`: zero jobs is a SUCCESS, not an error.

    The pairing matters on this route more than most: DESIGN.md:502-509
    records that a Jobvite auth failure arrives as an empty-looking
    body, so "empty" must be a shape the tool returns cleanly AND the
    401 case must not reach it. `test_jobvite_client.py` owns the
    second half; this owns the first.
    """
    result = await call_feed(fixture_bytes(JOBFEED_EMPTY))

    content = result.structured_content
    assert content is not None
    assert result.is_error is False
    assert content["jobs"] == []
    assert content["total"] == 0
    assert content["summary"] == "showing 0 of 0"


# ======================================================================
# THE RESULT CAP - the in-tool half only (DESIGN.md:436-438, 469-477)
# ======================================================================


def _payload(count: int, total: int | None = None) -> bytes:
    jobs = [{"id": f"JOB{n}", "title": f"Title {n}"} for n in range(count)]
    body: dict[str, Any] = {JOB_FEED_ENVELOPE_KEY: jobs}
    body["total"] = count if total is None else total
    return json.dumps(body).encode()


async def test_the_result_cap_reports_showing_n_of_total() -> None:
    """A capped page REPORTS the cap; it does not truncate silently."""
    result = await call_feed(_payload(5, total=1240), max_results=2)

    content = result.structured_content
    assert content is not None
    assert content["showing"] == 2
    assert content["total"] == 1240
    assert content["summary"] == "showing 2 of 1,240"


def test_the_cap_reads_total_from_the_envelope_not_from_the_items() -> None:
    """`total` is Jobvite's number, never `len(items)`.

    Counting the items would make `showing N of N` true on every call
    and delete the only signal that a page was capped
    (DESIGN.md:487-489).
    """
    payload = {JOB_FEED_ENVELOPE_KEY: [{"id": "A"}, {"id": "B"}], "total": 900}
    assert build_feed_result(payload, 1).total == 900


def test_the_transport_cap_is_not_reimplemented_here() -> None:
    """U6 owns the 1000 cap; this unit consumes it.

    The design states the `/v1/jobFeed` page cap once, in the client
    layer (DESIGN.md:434), and `services/jobvite_client.py` is not this
    unit's file. A second copy of the number here is the split that
    made the RESULT cap wrong in two halves that were each correct
    alone (U6's F1), so this asserts the absence **by reading the
    module's own source** rather than by trusting that nobody typed it.
    """
    import pathlib

    source = (
        pathlib.Path(__file__).resolve().parents[1]
        / "src"
        / "fast_mcp_jobvite"
        / "tools"
        / "jobs.py"
    ).read_text()
    # The number may appear in PROSE explaining whose it is; what must
    # not appear is a comparison or slice using it.
    for forbidden in ("[:1000]", "min(1000", "1000)", "= 1000"):
        assert forbidden not in source, (
            f"`{forbidden}` in tools/jobs.py: the transport cap is the client's"
        )


# ======================================================================
# THE INPUT MODEL AND THE WIRE
# ======================================================================


async def test_the_filters_reach_the_wire_under_jobvites_own_keys() -> None:
    """`type` and `availableTo`, spelled as contract §9 spells them.

    A parameter Jobvite does not recognise is ignored silently, so a
    misspelling returns an UNFILTERED feed while the caller believes it
    was filtered - a wrong answer that explains itself.
    """
    seen: list[httpx2.Request] = []
    await call_feed(
        fixture_bytes(JOBFEED_SUCCESS),
        arguments={"job_type": "Full-time", "available_to": "Internal"},
        seen=seen,
    )

    query = dict(seen[0].url.params)
    assert query["type"] == "Full-time"
    assert query["availableTo"] == "Internal"


async def test_omitting_the_filters_sends_neither() -> None:
    """The paired direction.

    An implementation that always sent a filter would pass the case
    above and silently filter every unfiltered call.
    """
    seen: list[httpx2.Request] = []
    await call_feed(fixture_bytes(JOBFEED_SUCCESS), seen=seen)

    query = dict(seen[0].url.params)
    assert "type" not in query
    assert "availableTo" not in query


def test_an_unknown_argument_is_refused_not_ignored() -> None:
    """`extra="forbid"`, `strict=True` (ADR-0012, DESIGN.md §2.1)."""
    with pytest.raises(ValidationError):
        GetJobFeedInput(department="Engineering")  # type: ignore[call-arg]


def test_available_to_admits_only_the_two_documented_values() -> None:
    """A value space the contract closes is closed in the model.

    `JOBVITE-CONTRACT.md` §9 documents `External | Internal`, so a
    third value is refused here rather than sent for Jobvite to ignore.
    """
    assert GetJobFeedInput(available_to="External").available_to == "External"
    with pytest.raises(ValidationError):
        GetJobFeedInput(available_to="Everyone")  # type: ignore[arg-type]


# ======================================================================
# CONTAINMENT (DESIGN.md:192-195)
# ======================================================================


def test_an_unadmitted_jobvite_field_is_dropped_not_returned() -> None:
    """A field nobody admitted does not reach the caller."""
    result = build_feed_result(
        {"total": 1, JOB_FEED_ENVELOPE_KEY: [{"id": "A", "salaryBand": "SECRET"}]},
        50,
    )
    assert "SECRET" not in json.dumps(result.model_dump(mode="json"))


def test_an_unadmitted_field_does_not_fail_the_call() -> None:
    """Dropped, not raised on - DESIGN.md:192-195's own direction.

    `extra="forbid"` on the model would take the whole call down on a
    Jobvite schema change, which is the opposite of failing closed
    here.
    """
    result = build_feed_result(
        {"total": 1, JOB_FEED_ENVELOPE_KEY: [{"id": "A", "brandNewKey": 1}]}, 50
    )
    assert [job.eid for job in result.jobs] == ["A"]


# ======================================================================
# REGISTRATION, THE ENABLE GATE, AND request_id
# ======================================================================


async def test_the_feed_tool_is_not_registered_when_it_is_not_named() -> None:
    """The deploy-time control (DESIGN.md:917-934).

    A tool that registers and then refuses is a tool a client can
    still see.
    """
    server = build_server(
        Settings(
            tools=SEARCH_JOBS,
            api_key=SecretStr(API_KEY),
            api_secret=SecretStr(API_SECRET),
        )
    )
    async with Client(server) as client:
        names = {tool.name for tool in await client.list_tools()}
    assert GET_JOB_FEED not in names
    assert SEARCH_JOBS in names


async def test_the_feed_registers_when_search_jobs_is_disabled() -> None:
    """Two tools, two gates, and they are INDEPENDENT.

    The two take different credentials, so a deployment holding only
    the feed credential is a configuration `validate_settings` accepts.
    A single early return covering both would register nothing for it.
    """
    server = build_server(settings())
    async with Client(server) as client:
        names = {tool.name for tool in await client.list_tools()}
    assert GET_JOB_FEED in names
    assert SEARCH_JOBS not in names


async def test_request_id_reaches_the_caller_in_meta(
    log_records: list[dict[str, Any]],
) -> None:
    """The audit id and the wire `_meta` id are the SAME id.

    Read off the wire result, never the returned `ToolResult`
    (DESIGN.md:1332-1334), and matched against the audit event so the
    id a caller could quote actually names the invocation that was
    recorded.
    """
    result = await call_feed(fixture_bytes(JOBFEED_SUCCESS))

    events = [r for r in log_records if r["message"] == AUDIT_EVENT_NAME]
    assert len(events) == 1
    wire_id = (result.meta or {}).get(REQUEST_ID_META_KEY)
    assert wire_id
    assert wire_id == events[0]["extra"]["request_id"]


def test_the_output_schema_is_built_in_serialisation_mode() -> None:
    """`showing` and `summary` are in the ADVERTISED schema.

    pydantic's default `mode="validation"` omits computed fields, and
    `extra="forbid"` renders as `additionalProperties: false`, so the
    client then rejects our own success payload (U5 measured this).
    """
    schema = JobFeedResult.model_json_schema(mode="serialization")
    assert {"showing", "summary", "jobs", "total"} <= set(schema["properties"])
