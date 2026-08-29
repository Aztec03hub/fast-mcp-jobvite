"""U6 - paging (DESIGN.md:432-487, `IMPLEMENTATION-PLAN.md` U6).

**Every assertion here is on BEHAVIOUR observed at the transport.** The
handlers below record the exact `start` and `count` each scan asked for,
so "every scan starts at 0" is read off the wire rather than off the
source. U3's amputation harness found a test that passed with its
behaviour deleted because it grepped the module for a string the
module's own docstring quoted; nothing here reads the source.

**THE THREE THINGS THIS SUITE EXISTS TO PIN DOWN.**

1. **De-duplication is a defence against OVER-reading only**
   (DESIGN.md:465-468). `test_de_duplication_cannot_recover_a_record...`
   is the LIMITATION case: a server that never returns record zero
   still comes back short, and no amount of de-duplicating changes
   that. Without it a later author reads the seen set as the safety
   mechanism and moves the start to 1.
2. **The completeness check has TWO arms** (DESIGN.md:469-477). It
   fires on an exhaustive scan with a missing record and it must NOT
   fire on a capped call, because `showing 50 of 1,240` is §7.7's own
   worked example and DESIGN.md:474 says alarming on the default path
   trains everyone to ignore the alarm. A single-armed suite passes on
   an implementation that alarms on everything.
3. **The result cap is ONE behaviour across TWO files.** U5 owns the
   in-tool half and the `showing N of total` string in `tools/jobs.py`;
   this suite exercises the transport half and the `min()` only, and
   asserts nothing about U5's reporting.

**What is NOT asserted here, because it is not established.** That
`start` is 1-based is a VENDOR CLAIM (DESIGN.md:451) and not an
observation. The one observation is `JOBVITE-API.md:399` - `start=0` is
accepted and returns records, in one genuine `200` - which falsifies
"1-based and strict" and separates "0-based" from "1-based with
clamping" not at all. Whether 500 and 1000 are real server limits is
unobserved; the cases below assert the CONFIGURED figures reach the
wire, which is a claim about this client and not about Jobvite.
"""

from __future__ import annotations

from typing import Any

import httpx2
import pytest
from loguru import logger

from fast_mcp_jobvite.services import jobvite_client as jc

API_KEY = "TESTKEY-not-a-real-credential"
API_SECRET = "TESTSECRET-not-a-real-credential"  # noqa: S105 - a test literal
COMPANY_ID = "TESTCOMPANY"

JOBS_PATH = "/job"
ITEMS_KEY = "requisitions"


class _Secret:
    """A minimal `SecretValue`, mirroring `SecretStr`'s one method."""

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


class Recorder:
    """A fake Jobvite that serves a record set and records every ask.

    **The record set is a real list, sliced by the offset the client
    sends**, rather than a scripted sequence of canned pages. A scripted
    sequence answers whatever it is asked in the order it was written,
    so it cannot tell a scan that started at 0 from one that started at
    1 - which is the single fact this suite exists to observe.
    """

    def __init__(
        self,
        *,
        records: list[dict[str, Any]],
        base: int = 0,
        total: int | None = None,
    ) -> None:
        """Build the fake.

        Args:
            records: The whole result set, index 0 first.
            base: The server's own base, and the two values are the two
                hypotheses DESIGN.md:460-462 says the evidence cannot
                separate. `0` serves `records[start:]`. `1` is
                1-based-WITH-CLAMPING - it serves
                `records[max(start, 1) - 1:]`, so `start=0` is answered
                with page one rather than an error, which is what
                `JOBVITE-API.md:399` observed. "1-based and strict" is
                not modelled because that observation falsified it.
            total: What the envelope reports. Defaults to the true
                length; a DIFFERENT value is how a lying `total` is
                tested.
        """
        self.records = records
        self.base = base
        self.total = len(records) if total is None else total
        self.asks: list[tuple[int, int]] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        """Answer one page and record what was asked for."""
        start = int(request.url.params["start"])
        count = int(request.url.params["count"])
        self.asks.append((start, count))
        offset = start if self.base == 0 else max(start, 1) - 1
        page = self.records[offset : offset + count]
        return httpx2.Response(
            200,
            json={
                ITEMS_KEY: page,
                "total": self.total,
                "status": {"code": 200, "messages": []},
            },
        )


class DropsRecordZero:
    """A server that NEVER returns record zero, whatever it is asked.

    This is the shape a 1-based-and-strict server presents to a caller
    that starts at 1: the record exists, it is counted in `total`, and
    it is in no page. It is the case de-duplication cannot fix.
    """

    def __init__(self, records: list[dict[str, Any]]) -> None:
        """Hold the full set; serve only `records[1:]`."""
        self.records = records
        self.asks: list[tuple[int, int]] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        """Answer one page from the reachable tail of the set."""
        start = int(request.url.params["start"])
        count = int(request.url.params["count"])
        self.asks.append((start, count))
        reachable = self.records[1:]
        page = reachable[start : start + count]
        return httpx2.Response(
            200,
            json={
                ITEMS_KEY: page,
                "total": len(self.records),
                "status": {"code": 200, "messages": []},
            },
        )


def records(n: int, *, offset: int = 0) -> list[dict[str, Any]]:
    """`n` records with opaque-looking 8-character ids."""
    return [
        {"eId": f"E{i + offset:07d}", "title": f"job {i + offset}"} for i in range(n)
    ]


def client(
    handler: Any,
    *,
    max_results: int = jc.DEFAULT_MAX_RESULTS,
    start_base_overrides: dict[str, int] | None = None,
) -> jc.JobviteClient:
    """Build a client on `httpx2.MockTransport` (ADR-0007)."""
    return jc.JobviteClient(
        api_key=_Secret(API_KEY),
        api_secret=_Secret(API_SECRET),
        company_id=_Secret(COMPANY_ID),
        transport=httpx2.MockTransport(handler),
        max_results=max_results,
        start_base_overrides=start_base_overrides,
    )


def _capture_extras() -> tuple[int, list[dict[str, Any]]]:
    """Add a sink keeping a COPY of each record's `extra`.

    A copy, not the record: loguru reuses the record object, so a list
    of references reads back whatever the last record held.
    """
    captured: list[dict[str, Any]] = []
    sink_id = logger.add(
        lambda message: captured.append(dict(message.record["extra"])),
        level="DEBUG",
    )
    return sink_id, captured


# ======================================================================
# start=0 - the whole mechanism, and it is one character
# ======================================================================


async def test_every_scan_starts_at_zero_on_the_wire() -> None:
    """DESIGN.md:455. Read off the transport, not off the source.

    Asserted on the FIRST ask of the scan. A later ask is an advance
    and says nothing about the base.
    """
    server = Recorder(records=records(7))
    async with client(server) as c:
        await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert server.asks[0][0] == 0


async def test_start_zero_holds_on_the_jobfeed_route_too() -> None:
    """The base is per RESOURCE (DESIGN.md:478-480), the start is not.

    `/v1/jobFeed` is the one route the vendor documents as 1-based, so
    it is the route most likely to acquire a `start=1` in a later edit.
    """
    server = Recorder(records=records(4))
    async with client(server) as c:
        await c.scan("/jobFeed", items_key=ITEMS_KEY, jobfeed=True)
    assert server.asks[0][0] == 0


async def test_a_zero_based_server_returns_record_zero() -> None:
    """Starting at 0 is what makes record zero reachable at all.

    The paired direction of DESIGN.md:463-464: *starting at 1 is the
    only choice that can silently lose a record*.
    """
    server = Recorder(records=records(5), base=0)
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert [item["eId"] for item in result.items][0] == "E0000000"
    assert len(result.items) == 5


async def test_the_structural_assertion_start_zero_is_accepted() -> None:
    """`JOBVITE-API.md:399`, and NOTHING MORE THAN IT.

    The one genuine Jobvite `200` in our evidence recorded
    `GET /api/v2/candidate?count=5&start=0&format=json` returning
    records. That falsifies "1-based and strict". It does **not**
    establish the base, and this case asserts only what was observed:
    a `start=0` request is answered with records and a `status.code`
    of 200, in the envelope shape `JOBVITE-API.md:397` records.
    """
    server = Recorder(records=records(5))
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY, limit=5)
    assert server.asks[0][0] == 0
    assert result.items != []


# ======================================================================
# de-duplication, AND THE LIMITATION THAT IS THE POINT OF IT
# ======================================================================


async def test_an_overlapping_page_drops_duplicates() -> None:
    """DESIGN.md:465-466, the behaviour half.

    A 1-based server that clamps `start=0` to `1` re-serves the
    boundary record on every advance. The seen set drops it, so the
    scan returns each record once.
    """
    server = Recorder(records=records(9), base=1)
    async with client(server, max_results=4) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    ids = [item["eId"] for item in result.items]
    assert len(ids) == len(set(ids))
    assert result.duplicates_dropped > 0


async def test_de_duplication_cannot_recover_a_never_returned_record() -> None:
    """DESIGN.md:465-468, **THE LIMITATION, WHICH IS THE POINT**.

    *De-duplication defends against over-reading only. It cannot
    recover a record that was never returned, which is exactly why the
    fix is starting at 0 rather than de-duplicating harder.*

    Against a server that never serves record zero, the scan comes back
    SHORT and the seen set changes nothing about that. A suite that
    only showed duplicates being dropped would let a later author
    conclude the seen set is the safety mechanism and move the start
    to 1 - at which point this is what every scan looks like, silently.
    """
    all_records = records(6)
    server = DropsRecordZero(all_records)
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)

    assert result.total == 6
    assert len(result.items) == 5
    assert "E0000000" not in [item["eId"] for item in result.items]
    # The seen set did not fire at all here: there was nothing to
    # over-read. It is the wrong instrument for this failure.
    assert result.duplicates_dropped == 0
    # And the scan SAYS SO rather than reporting five of six as a
    # clean answer.
    assert result.incomplete is True


async def test_records_without_an_id_are_kept_not_collapsed() -> None:
    """The over-reading defence must not cause an under-read.

    Every id-less record shares one `None` key, so a seen set that
    swallowed them would drop all but the first - de-duplication
    deleting real records, which is the failure DESIGN.md:465-468 is
    warning about arriving from the other side.
    """
    page = [{"title": "no id here"}, {"title": "nor here"}]
    server = Recorder(records=page, total=2)
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert len(result.items) == 2
    assert result.unidentified == 2


# ======================================================================
# termination: a short page, and NEVER `total`
# ======================================================================


async def test_the_scan_terminates_on_a_short_page() -> None:
    """DESIGN.md:486. `len(items) < count` is the only stop rule."""
    server = Recorder(records=records(7))
    async with client(server, max_results=3) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert len(result.items) == 7
    assert result.pages == 3
    assert [ask[0] for ask in server.asks] == [0, 3, 6]


async def test_a_total_that_understates_does_not_end_the_loop_early() -> None:
    """DESIGN.md:487. `total` is reported and never a loop condition.

    The server reports `total=1` while holding seven records. A loop
    that believed `total` would stop after one and report six missing
    records as a complete answer.
    """
    server = Recorder(records=records(7), total=1)
    async with client(server, max_results=3) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert len(result.items) == 7
    assert result.total == 1


async def test_a_total_that_overstates_does_not_extend_the_loop() -> None:
    """The paired direction, and it is the one that hangs.

    The server reports `total=10_000` and answers a short page on the
    first request. A loop that paged until it had `total` records would
    request forever against a server that keeps answering.
    """
    server = Recorder(records=records(2), total=10_000)
    async with client(server, max_results=50) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert result.pages == 1
    assert len(result.items) == 2
    # `total` is READ FROM THE ENVELOPE, never recomputed from the page.
    # `JOBVITE-API.md:398` records it as the full result-set size: a
    # call
    # requesting 5 reported a `total` in the hundreds of thousands. A
    # client that recounts it makes every scan agree with itself and
    # deletes the only number the completeness check has to compare
    # against.
    assert result.total == 10_000


async def test_a_full_page_of_duplicates_is_not_a_short_page() -> None:
    """The short-page test reads the RAW page, not the kept records.

    A page that is full but entirely duplicated is not short. Measuring
    `len(items) < count` against the DE-DUPLICATED count would end a
    scan early on exactly the clamping hypothesis the seen set exists
    to absorb.
    """
    duplicated = [{"eId": "E0000000", "title": "same"} for _ in range(3)]
    duplicated += records(2, offset=1)
    server = Recorder(records=duplicated, total=3)
    async with client(server, max_results=3) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert result.pages == 2
    assert result.duplicates_dropped == 2


# ======================================================================
# the completeness check - BOTH ARMS, AND THE SECOND IS THE ONE
# EVERYONE SKIPS
# ======================================================================


async def test_completeness_fires_on_an_exhaustive_scan_with_a_gap() -> None:
    """ARM ONE (DESIGN.md:469-473).

    The caller asked for everything, the scan terminated on a short
    page, and it holds fewer unique records than `total` reports. That
    is a real check because it compares a COUNT: `eId` is opaque and
    you cannot find a hole in a set of opaque ids.
    """
    server = Recorder(records=records(4), total=9)
    sink_id, captured = _capture_extras()
    try:
        async with client(server) as c:
            result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    finally:
        logger.remove(sink_id)

    assert result.incomplete is True
    anomalies = [
        extra
        for extra in captured
        if extra.get("reported_total") == 9 and extra.get("unique") == 4
    ]
    assert anomalies != []


async def test_completeness_does_not_fire_on_a_capped_call() -> None:
    """ARM TWO, AND IT IS THE REQUIRED HALF PEOPLE LEAVE OUT.

    DESIGN.md:473-477: a capped call is a mismatch **by design** -
    §7.7's own worked example is `showing 50 of 1,240` - and wiring the
    check to every call *"would fire the alarm on the default path and
    train everyone to ignore it"*.

    **TWO SUB-CASES, AND THE FIRST ONE ALONE IS NOT ENOUGH.** A capped
    call that stops because it filled its limit never reaches a short
    page, so `not exhaustive` is not the condition that keeps it quiet
    and an implementation missing that condition still passes. The
    second sub-case is a capped call that DOES terminate on a short
    page and still mismatches `total`, which is the only shape where
    the exhaustive test is load-bearing. Measured: without the second,
    deleting `not exhaustive` from the guard survived this case.
    """
    filled = Recorder(records=records(1240), total=1240)
    sink_id, captured = _capture_extras()
    try:
        async with client(filled) as c:
            result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY, limit=50)
    finally:
        logger.remove(sink_id)

    assert result.capped is True
    assert len(result.items) == 50
    assert result.total == 1240
    assert result.incomplete is False
    assert [extra for extra in captured if "reported_total" in extra] == []

    # SUB-CASE TWO: capped, short page, and a mismatch. The caller asked
    # for at most 50 and Jobvite served 30 of a claimed 1,240. Still not
    # an anomaly: the caller did not ask for everything.
    short = Recorder(records=records(30), total=1240)
    sink_id, captured = _capture_extras()
    try:
        async with client(short) as c:
            result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY, limit=50)
    finally:
        logger.remove(sink_id)

    assert result.exhaustive is False
    assert len(result.items) == 30
    assert result.total == 1240
    assert result.incomplete is False
    assert [extra for extra in captured if "reported_total" in extra] == []


async def test_completeness_is_silent_when_an_exhaustive_scan_is_whole() -> None:
    """The positive control for arm one.

    Without it, arm one passes against a check that never fires, which
    is the same defect as a check that always fires wearing the other
    face.
    """
    server = Recorder(records=records(5))
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert result.exhaustive is True
    assert result.incomplete is False


async def test_completeness_is_silent_when_no_total_was_reported() -> None:
    """No `total` is not a gap. There is nothing to compare against."""
    server = Recorder(records=records(3))
    server.total = "not a number"  # type: ignore[assignment]
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert result.total is None
    assert result.incomplete is False


# ======================================================================
# the page caps, and min(transport_cap, configured_result_cap)
# ======================================================================


def test_the_transport_caps_are_the_designs_figures() -> None:
    """DESIGN.md:434. 500 on v2, 1000 on `/v1/jobFeed`.

    **A claim about this client, not about Jobvite.** Whether either is
    a real server limit is unobserved.
    """
    c = client(Recorder(records=[]))
    assert c.transport_cap() == 500
    assert c.transport_cap(jobfeed=True) == 1000


def test_the_result_cap_is_the_min_of_the_two_halves() -> None:
    """DESIGN.md:434-436, the `min()` this unit owns.

    U5 applies `JOBVITE_MAX_RESULTS` in-tool and owns
    `showing N of total`; this composes the configured half with the
    transport half. Both directions of the `min` are exercised, because
    a `min` written as either operand alone passes a one-sided test.
    """
    small = client(Recorder(records=[]), max_results=10)
    assert small.result_cap() == 10
    assert small.result_cap(jobfeed=True) == 10

    huge = client(Recorder(records=[]), max_results=100_000)
    assert huge.result_cap() == 500
    assert huge.result_cap(jobfeed=True) == 1000


async def test_the_wire_page_size_is_the_min_of_the_two_caps() -> None:
    """The `min()` observed ON THE WIRE, both directions.

    `result_cap` alone is a pure function and a test of it can agree
    with a `scan` that never uses it. These two arms watch the `count`
    the transport actually carries: the configured half binds when it
    is the smaller, and the transport half binds when it is.
    """
    configured_binds = Recorder(records=records(3))
    async with client(configured_binds, max_results=7) as c:
        await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert configured_binds.asks[0][1] == 7

    transport_binds = Recorder(records=records(3))
    async with client(transport_binds, max_results=100_000) as c:
        await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    assert transport_binds.asks[0][1] == 500


async def test_the_jobfeed_route_uses_its_own_transport_cap() -> None:
    """1000 on `/v1/jobFeed`, per resource (DESIGN.md:434).

    Asserted with a configured cap ABOVE both transport caps, so the
    only thing that can produce 1000 rather than 500 is the route.
    """
    server = Recorder(records=records(3))
    async with client(server, max_results=100_000) as c:
        await c.scan("/jobFeed", items_key=ITEMS_KEY, jobfeed=True)
    assert server.asks[0][1] == 1000


async def test_a_capped_call_stops_asking_once_it_is_full() -> None:
    """A limited call must not pull 300 records to return 50.

    **The request COUNT is the assertion, and it was missing.** The
    amputation harness found it: deleting the in-loop cap break changed
    nothing observable, because the final truncation still returned 50
    records. Only the number of requests distinguishes a scan that
    stopped from one that paged the whole resource and threw the rest
    away - which against a self-throttled client (DESIGN.md:425-427) is
    six requests a minute spent to discard 250 records.
    """
    server = Recorder(records=records(300), total=300)
    async with client(server) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY, limit=50)
    assert server.asks[0][1] == 50
    assert len(server.asks) == 1
    assert result.pages == 1
    assert len(result.items) == 50


async def test_a_limit_above_the_configured_cap_is_clamped_to_it() -> None:
    """The caller does not get to raise `JOBVITE_MAX_RESULTS`."""
    server = Recorder(records=records(300), total=300)
    async with client(server, max_results=25) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY, limit=1000)
    assert len(result.items) == 25
    assert result.capped is True


# ======================================================================
# the start base: per resource, not global
# ======================================================================


def test_the_scan_start_defaults_to_zero_for_every_resource() -> None:
    """DESIGN.md:455. No resource ships a declared base of 1.

    The vendor's 1-based claim is not written into a default, because a
    declared 1 never requests record zero and loses it on a 0-based
    server with nothing reporting the loss.
    """
    c = client(Recorder(records=[]))
    assert c.scan_start(JOBS_PATH) == 0
    assert c.scan_start("/jobFeed") == 0
    assert c.scan_start("/candidate") == 0


async def test_an_override_is_per_resource_and_not_global() -> None:
    """DESIGN.md:478-480 - the base is per-resource, not global.

    A global override is the failure this asserts against: overriding
    `/jobFeed`, the one route with an [OFFICIAL] base, must not move
    the v2 resources whose base is [INFERRED].
    """
    c = client(Recorder(records=[]), start_base_overrides={"/jobFeed": 1})
    assert c.scan_start("/jobFeed") == 1
    assert c.scan_start(JOBS_PATH) == 0

    server = Recorder(records=records(3), base=1)
    async with client(server, start_base_overrides={"/jobFeed": 1}) as feed:
        await feed.scan("/jobFeed", items_key=ITEMS_KEY, jobfeed=True)
    assert server.asks[0][0] == 1


@pytest.mark.parametrize("base", [0, 1])
async def test_a_scan_is_whole_under_both_surviving_hypotheses(base: int) -> None:
    """The base-agnostic claim, asserted against BOTH live hypotheses.

    DESIGN.md:460-462 says the evidence cannot separate "0-based" from
    "1-based with clamping", and that `start=0` is safe under both.
    This case is that sentence: the same scan, against both servers,
    returns every record exactly once.
    """
    server = Recorder(records=records(11), base=base)
    async with client(server, max_results=4) as c:
        result = await c.scan(JOBS_PATH, items_key=ITEMS_KEY)
    ids = [item["eId"] for item in result.items]
    assert sorted(ids) == sorted(item["eId"] for item in records(11))
    assert result.incomplete is False
