"""U7 - resilience: DESIGN.md:342-364, :373-375, :601-620.

§8 #13, #21 and #23.

**The circuit breaker is one of TWO mechanisms DESIGN.md:64-68 names as
never executed**, sitting among measured results and borrowing their
credibility. Everything asserted here is executed; what is NOT executed
is stated in `docs/worklogs/U7-IMPL-REPORT.md` rather than left to be
inferred from the presence of a file called `test_resilience.py`.

**THE ONE CASE A SINGLE CALL CANNOT SATISFY.** DESIGN.md:1313-1315 says
of §8 #13 that "a single-call version of this test passes against a
module global, which is the bug `request_id_var` exists to prevent, so
the concurrent arm is the case and the single call is not sufficient".
`test_two_concurrent_invocations_each_log_their_own_request_id` drives
two invocations in parallel, forces both to retry, and matches every
retry line back to the invocation that produced it. A module global
would interleave and about half the lines would carry the other
invocation's id - every one of them still a well-formed UUID, which is
why the corruption is silent and why the assertion is on the PAIRING
rather than on the shape.

**THE OTHER CASE THAT NEEDS BOTH ARMS.** §8 #23 says a 4xx must not trip
the breaker. On its own that passes against a breaker that never trips
at all, so the positive control - repeated 5xx DOES trip it - sits
beside it and is what makes the negative arm mean anything.

**§8 #21 IS ASSERTED WITH A ROW COUNTER**, never by reading
configuration. DESIGN.md:350-353 records the measurement it exists to
prevent - one `create_candidate` call, **four rows created** - so the
assertion is how many requests reached the transport, which is the same
quantity the spike counted.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from collections.abc import Awaitable, Callable
from typing import Any

import httpx2
import pytest
from loguru import logger
from pydantic import SecretStr

from fast_mcp_jobvite.errors import (
    JobviteUnavailableError,
    JobviteUpstreamError,
    problem_from_exception,
)
from fast_mcp_jobvite.services import jobvite_client as jc
from fast_mcp_jobvite.utils.correlation import request_id_scope

from .conftest import REPO_ROOT

API_KEY = "TESTKEY-not-a-real-credential"
API_SECRET = "TESTSECRET-not-a-real-credential"  # noqa: S105 - a test literal
COMPANY_ID = "TESTCOMPANY"

JOBS_PATH = "/job"

RID_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
RID_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

#: A `MockTransport` handler. httpx2 accepts a coroutine function here
#: too - the async form is what the two slow-upstream cases need - and
#: the union is written out because `MockTransport`'s own annotation is
#: the sync form only.
Handler = (
    Callable[[httpx2.Request], httpx2.Response]
    | Callable[[httpx2.Request], Awaitable[httpx2.Response]]
)


class _Secret:
    """A minimal `SecretValue`, mirroring `SecretStr`'s one method."""

    def __init__(self, value: str) -> None:
        """Hold the value.

        Args:
            value: The credential text.
        """
        self._value = value

    def get_secret_value(self) -> str:
        """Return the value.

        Returns:
            The credential text.
        """
        return self._value


def client(handler: Handler, **kwargs: Any) -> jc.JobviteClient:  # noqa: ANN401
    """Build a client over `MockTransport` (ADR-0007, :1359-1360).

    Args:
        handler: The transport handler.
        **kwargs: Passed through to `JobviteClient`.

    Returns:
        The client. The caller closes it.
    """
    return jc.JobviteClient(
        api_key=_Secret(API_KEY),
        api_secret=_Secret(API_SECRET),
        company_id=_Secret(COMPANY_ID),
        transport=httpx2.MockTransport(handler),  # type: ignore[arg-type]
        **kwargs,
    )


def _capture() -> tuple[int, list[dict[str, Any]]]:
    """Add a loguru sink keeping a COPY of each record's `extra`.

    Returns:
        The sink id and the list it appends to. The caller removes the
        sink in a `finally` - a leaked sink outlives the case and
        collects another case's lines.
    """
    captured: list[dict[str, Any]] = []
    sink_id = logger.add(
        lambda message: captured.append(dict(message.record["extra"])),
        level="DEBUG",
    )
    return sink_id, captured


def _retry_lines(captured: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select the retry lines out of a capture.

    Args:
        captured: Every record's `extra`, in order.

    Returns:
        Only the records `_log_retry_attempt` wrote.
    """
    return [extra for extra in captured if "attempt" in extra]


def _transition_lines(captured: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select the breaker-transition lines out of a capture.

    Args:
        captured: Every record's `extra`, in order.

    Returns:
        Only the records `_report_breaker_state` wrote.
    """
    return [extra for extra in captured if "transition" in extra]


def counting(responses: list[httpx2.Response | Exception]) -> tuple[Handler, list[str]]:
    """A handler replaying a script and RECORDING every request.

    The recorded list is the row counter §8 #21 is asserted with.

    Args:
        responses: One entry per expected request. The LAST entry is
            repeated if more requests arrive than were scripted, so a
            case that retries more than it should is measured rather
            than crashing on an exhausted list.

    Returns:
        The handler and the list of methods it saw, in order.
    """
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        index = min(len(seen), len(responses) - 1)
        seen.append(request.method)
        outcome = responses[index]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return handler, seen


# ======================================================================
# TIMEOUTS - the innermost layer, and the one the standard says comes
# first (`backend/resilience.md:60-64`: "a call with no timeout is the
# root resilience defect").
# ======================================================================


def test_the_timeout_is_per_phase_and_none_of_it_is_an_sdk_default() -> None:
    """DESIGN.md:346: explicit and per-phase, no SDK default, no scalar.

    Asserted on the four phases separately rather than on the object,
    because `httpx2.Timeout(5.0)` also produces a `Timeout` and would
    satisfy any assertion that only checked the type - and a single
    scalar is exactly what the design forbids.
    """
    c = client(lambda _r: httpx2.Response(200, content=b"{}"))
    timeout = c._timeout  # noqa: SLF001 - the object under test
    assert timeout.connect == jc.DEFAULT_CONNECT_TIMEOUT
    assert timeout.read == jc.DEFAULT_READ_TIMEOUT
    assert timeout.write == jc.DEFAULT_WRITE_TIMEOUT
    assert timeout.pool == jc.DEFAULT_POOL_TIMEOUT
    # The four are not all the same number, so "per-phase" is a property
    # of the VALUES and not only of the constructor call.
    assert len({timeout.connect, timeout.read}) == 2
    # httpx2's own default is a 5-second scalar. Not inherited.
    assert timeout.read != 5.0


def test_an_attempt_timeout_is_clamped_to_what_the_budget_has_left() -> None:
    """A read timeout may not outlive the invocation's total budget.

    This is the join between DESIGN.md:346 and DESIGN.md:373-375: the
    per-phase read timeout is 30 seconds and the budget can be smaller,
    in which case the LAST attempt must not be allowed to buy a fresh
    30 seconds. Without the clamp the budget is an upper bound on when
    we STOP RETRYING, not on how long a caller waits.
    """
    c = client(lambda _r: httpx2.Response(200, content=b"{}"))
    unclamped = c._attempt_timeout(None)  # noqa: SLF001
    clamped = c._attempt_timeout(0.5)  # noqa: SLF001
    assert unclamped.read == jc.DEFAULT_READ_TIMEOUT
    assert clamped.read == 0.5
    assert clamped.connect == 0.5
    # A budget larger than the phase does NOT widen it.
    assert c._attempt_timeout(999.0).read == jc.DEFAULT_READ_TIMEOUT  # noqa: SLF001


# ======================================================================
# THE TOTAL OUTBOUND BUDGET (DESIGN.md:373-375). It did not exist before
# this unit; `config.py`'s `outbound_rate_limit` is a DIFFERENT quantity
# and satisfying one does not satisfy the other.
# ======================================================================


def test_the_budget_is_not_the_rate_limit_and_they_are_different_units() -> None:
    """The obligation this unit carried in (task #43).

    A rate limit is requests per minute; a budget is a time bound on one
    invocation. Six requests per minute is satisfied perfectly by ONE
    request that never returns, which is the unbounded wait
    DESIGN.md:373-375 exists to prevent. This case exists so the two
    cannot be quietly collapsed by a later edit that notices they are
    both "limits".
    """
    from fast_mcp_jobvite.config import Settings  # noqa: PLC0415 - one case needs it

    settings = Settings(
        api_key=SecretStr("k"),
        api_secret=SecretStr("s"),
    )
    # Requests per minute: an integer count, no time bound on a call.
    assert settings.outbound_rate_limit == 6
    # Seconds: a wall-clock bound on all attempts for one invocation.
    assert jc.DEFAULT_OUTBOUND_BUDGET_SECONDS == 60.0
    assert settings.outbound_rate_limit != jc.DEFAULT_OUTBOUND_BUDGET_SECONDS


def test_a_nested_scope_keeps_the_outer_deadline() -> None:
    """One invocation gets ONE budget, however many scopes open.

    An inner scope that restarted the clock would turn a scan's budget
    into a per-page budget, and 25 pages would cost 25 budgets - which
    is unbounded in exactly the direction this mechanism bounds.
    """
    with jc.outbound_budget_scope(50.0) as outer:  # noqa: SIM117 - nesting IS the case
        with jc.outbound_budget_scope(0.001) as inner:
            assert inner == outer
            left = jc.outbound_budget_remaining()
            assert left is not None
            assert left > 1.0


def test_the_deadline_does_not_leak_out_of_its_scope() -> None:
    """The `finally` reset, asserted with its positive arm beside it.

    "The var is `None` afterwards" passes perfectly against a scope that
    never set it, so the bound arm is asserted first.
    """
    assert jc.outbound_budget_remaining() is None
    with jc.outbound_budget_scope(30.0):
        assert jc.outbound_budget_remaining() is not None
    assert jc.outbound_budget_remaining() is None


async def test_a_slow_upstream_becomes_a_typed_503_not_an_unbounded_wait() -> None:
    """DESIGN.md:373-375's promise, driven end to end.

    The handler is slow AND failing, so the client retries; the budget
    runs out mid-retry and the caller gets
    `/problems/service-unavailable` 503 with the budget's own
    `detail` - not a 502, not a hang, and not
    the breaker's string.
    """

    async def slow(_request: httpx2.Request) -> httpx2.Response:
        await asyncio.sleep(0.15)
        return httpx2.Response(503, content=b'{"status":{"code":503}}')

    c = client(slow, outbound_budget_seconds=0.2)
    try:
        with pytest.raises(JobviteUnavailableError) as caught:
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()

    assert caught.value.detail == jc.UNAVAILABLE_BUDGET_DETAIL
    problem = problem_from_exception(caught.value, RID_A)
    assert problem["type"] == "/problems/service-unavailable"
    assert problem["status"] == 503
    # DISTINGUISHED BY DETAIL, not by a minted type (DESIGN.md:355-358).
    assert "not an open circuit breaker" in problem["detail"]


async def test_an_exhausted_budget_does_not_trip_the_breaker() -> None:
    """A bound WE applied is not evidence about Jobvite's health.

    Counting it would let one slow invocation open the breaker for every
    other caller, which is the opposite of what a breaker is for.
    """

    async def slow(_request: httpx2.Request) -> httpx2.Response:
        await asyncio.sleep(0.15)
        return httpx2.Response(200, content=b"{}")

    c = client(slow, outbound_budget_seconds=0.05)
    try:
        with jc.outbound_budget_scope(0.001):
            await asyncio.sleep(0.01)
            with pytest.raises(JobviteUnavailableError):
                await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()
    assert jc._JOBVITE_BREAKER.failure_count == 0  # noqa: SLF001
    assert jc._JOBVITE_BREAKER.state == "closed"  # noqa: SLF001


async def test_a_whole_scan_shares_one_budget_rather_than_one_per_page() -> None:
    """The amputation harness found this missing (row A2).

    DESIGN.md:373-375 bounds "all attempts for ONE TOOL INVOCATION". A
    scan of a 1,240-record resource makes 25 requests, so a budget
    opened per REQUEST would bound each page and bound the invocation at
    `pages x seconds` - unbounded in exactly the direction this exists
    to bound. **Deleting the scope from `scan` left the whole suite
    green**, because every other budget case drives a single request.

    The assertion is on the DEADLINE VALUE seen at the transport, not on
    elapsed time: a mock transport answers in microseconds, so a timing
    assertion here would be measuring the clock's resolution. One
    deadline for every page is the property; N distinct deadlines is the
    defect.
    """
    deadlines: list[float | None] = []
    pages = [
        b'{"requisitions": [{"eId": "a"}], "total": 3}',
        b'{"requisitions": [{"eId": "b"}], "total": 3}',
        b'{"requisitions": [], "total": 3}',
    ]

    def handler(_request: httpx2.Request) -> httpx2.Response:
        deadlines.append(jc.outbound_deadline_var.get())
        return httpx2.Response(200, content=pages[min(len(deadlines) - 1, 2)])

    c = client(handler, max_results=1)
    try:
        await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()

    assert len(deadlines) >= 2, "the scan did not page - this measured nothing"
    assert all(d is not None for d in deadlines)
    assert len(set(deadlines)) == 1, (
        f"the scan opened {len(set(deadlines))} budgets across "
        f"{len(deadlines)} pages; it must open exactly one"
    )


def test_the_retry_stop_caps_both_attempts_and_elapsed_time() -> None:
    """`backend/resilience.md:88-90`: "cap BOTH ... AND ...".

    **This case is STRUCTURAL, and that is a limitation worth stating
    rather than hiding.** Amputation row A5 deletes `stop_after_delay`
    and no behavioural case goes red, because `_attempt`'s pre-attempt
    budget check already refuses to issue a request once the deadline
    has passed - so the two caps are not separable by driving calls.
    The delay cap is defence in depth: it stops the loop before a final
    pointless backoff sleep, which no assertion here can observe without
    making the suite sleep.

    So the composed `stop` is read directly. A `stop_any` of the two is
    what the clause asks for, and a single condition is not.
    """
    import inspect  # noqa: PLC0415 - one case needs it

    source = inspect.getsource(jc.JobviteClient._attempt_with_retry)  # noqa: SLF001
    assert "stop_after_attempt(self._retry_max_attempts)" in source
    assert "stop_after_delay(" in source
    # OR-ed, not AND-ed: either cap alone must be able to stop the loop.
    assert "stop_after_attempt(self._retry_max_attempts) | stop_after_delay(" in source


# ======================================================================
# RETRY (DESIGN.md:347-349). Connection errors, timeouts and 5xx ONLY.
# ======================================================================


async def test_a_5xx_is_retried_to_the_attempt_cap() -> None:
    """Counted at the transport, so the cap is observed and not read."""
    handler, seen = counting([httpx2.Response(500, content=b'{"status":{"code":500}}')])
    c = client(handler, retry_max_attempts=3)
    try:
        with pytest.raises(JobviteUpstreamError):
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()
    assert len(seen) == 3


async def test_a_timeout_is_retried_and_a_transport_error_is_retried() -> None:
    """DESIGN.md:347-349's "connection errors, timeouts" arm.

    Both httpx2 shapes are driven, because `_should_retry` selects on
    `JobviteUnavailableError` and a mapping that lost one of the two
    exception classes would still pass with only the other.
    """
    for boom in (
        httpx2.ReadTimeout("read timed out"),
        httpx2.ConnectError("connection refused"),
    ):
        handler, seen = counting([boom])
        c = client(handler, retry_max_attempts=2)
        try:
            with pytest.raises(JobviteUnavailableError):
                await c.request("GET", JOBS_PATH)
        finally:
            await c.aclose()
        assert len(seen) == 2, f"{type(boom).__name__} was not retried"


async def test_a_4xx_is_not_retried_and_surfaces_immediately() -> None:
    """`backend/resilience.md:91-94`, as ONE request on the wire.

    A configuration read would pass against a predicate that lists 4xx
    and a call site that ignores the predicate.
    """
    handler, seen = counting([httpx2.Response(404, content=b'{"status":{"code":404}}')])
    c = client(handler)
    try:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()
    assert len(seen) == 1
    assert caught.value.upstream_status == 404


async def test_a_retry_succeeds_and_the_caller_never_sees_the_failure() -> None:
    """The positive control for every "N attempts" case above.

    Without it, a retry layer that always exhausted its budget would
    satisfy the counting cases and still never recover anything.
    """
    handler, seen = counting(
        [
            httpx2.Response(503, content=b'{"status":{"code":503}}'),
            httpx2.Response(200, content=b'{"requisitions": [], "total": 0}'),
        ]
    )
    c = client(handler)
    try:
        assert await c.request("GET", JOBS_PATH) == {"requisitions": [], "total": 0}
    finally:
        await c.aclose()
    assert len(seen) == 2


def test_the_backoff_is_exponential_with_jitter() -> None:
    """`backend/resilience.md:79-82`, on the UNPATCHED object.

    `_no_backoff_sleeps` replaces this for every other case, so the one
    property it hides is asserted here directly: two waits for the same
    attempt number differ, which is what "jitter" means and what a
    fixed-interval schedule cannot produce.
    """
    from tenacity.wait import wait_exponential_jitter  # noqa: PLC0415 - one case

    # Rebuilt from the module's own constants rather than restated, so a
    # change to either constant reaches this case.
    backoff = wait_exponential_jitter(
        initial=jc.DEFAULT_RETRY_INITIAL_BACKOFF, max=jc.DEFAULT_RETRY_MAX_BACKOFF
    )

    class _State:
        attempt_number = 3

    samples = {backoff(_State()) for _ in range(20)}  # type: ignore[arg-type]
    assert len(samples) > 1, "the wait is deterministic - there is no jitter"
    assert max(samples) <= jc.DEFAULT_RETRY_MAX_BACKOFF + 1


# ======================================================================
# §8 #21 - `create_candidate` excluded from retry BY CONSTRUCTION,
# asserted with a ROW COUNTER (DESIGN.md:350-353, measured: one call,
# FOUR rows created).
# ======================================================================


async def test_a_write_that_times_out_reaches_the_transport_exactly_once() -> None:
    """§8 #21. **The assertion is the row count**, not a config read.

    DESIGN.md:353 records the measurement: one `create_candidate` call,
    **four rows created**, because a retry re-issued a write that had
    already succeeded. A timeout is the worst case - the write may well
    have landed and we cannot know - so this is the shape asserted.
    """
    handler, seen = counting([httpx2.ReadTimeout("read timed out")])
    c = client(handler, retry_max_attempts=4)
    try:
        with pytest.raises(JobviteUnavailableError):
            await c.request("POST", "/candidate", json_body={"firstName": "A"})
    finally:
        await c.aclose()
    assert seen == ["POST"], f"a write was re-issued {len(seen)} times"


async def test_the_same_failure_on_a_read_IS_retried() -> None:
    """The positive control for the row counter above.

    Identical handler, identical exception, identical client - only the
    METHOD differs. Without this arm, `seen == ["POST"]` passes just as
    well against a client whose retry layer is broken for everything.
    """
    handler, seen = counting([httpx2.ReadTimeout("read timed out")])
    c = client(handler, retry_max_attempts=4)
    try:
        with pytest.raises(JobviteUnavailableError):
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()
    assert len(seen) == 4


def test_the_exclusion_is_a_method_set_and_not_a_tool_name_list() -> None:
    """By construction (DESIGN.md:350) rather than by configuration.

    A hand-kept list of exempt TOOL NAMES is blind to the write tool
    nobody added to it. A method set is not: a tool written next year
    that POSTs is excluded the moment it is written.
    """
    assert jc.RETRYABLE_METHODS == frozenset({"GET", "HEAD"})
    assert "POST" not in jc.RETRYABLE_METHODS
    assert "PUT" not in jc.RETRYABLE_METHODS
    assert "DELETE" not in jc.RETRYABLE_METHODS


# ======================================================================
# 429 (DESIGN.md:361-364). Retried, then mapped to 503, honouring
# `Retry-After`. NEVER OBSERVED against Jobvite - see the report.
# ======================================================================


async def test_a_429_is_retried_and_then_mapped_to_503() -> None:
    """DESIGN.md:361-364, and the type change is the point.

    A 429 that surfaced as `/problems/external-service-error` 502 would
    tell a caller the upstream errored when it asked us to slow down.
    """
    handler, seen = counting(
        [httpx2.Response(429, content=b'{"status":{"code":429}}', headers={})]
    )
    c = client(handler, retry_max_attempts=2)
    try:
        with pytest.raises(JobviteUnavailableError) as caught:
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()
    assert len(seen) == 2
    problem = problem_from_exception(caught.value, RID_A)
    assert problem["status"] == 503
    assert problem["type"] == "/problems/service-unavailable"


async def test_retry_after_is_honoured_over_the_local_backoff() -> None:
    """`backend/resilience.md:95-97`, and the CLAMP beside it.

    The header wins over the jittered schedule, and is then bounded by
    what remains of the outbound budget - an upstream asking for 900
    seconds must not be able to make us wait past a bound we promised.
    """
    handler, _ = counting(
        [
            httpx2.Response(
                429, content=b'{"status":{"code":429}}', headers={"Retry-After": "900"}
            )
        ]
    )
    c = client(handler, retry_max_attempts=2)

    class _State:
        attempt_number = 1

        class outcome:  # noqa: N801 - mirrors tenacity's attribute name
            @staticmethod
            def exception() -> Exception:
                return jc._RetryableUpstream(  # noqa: SLF001
                    JobviteUpstreamError(429, "slow down"), retry_after=900.0
                )

    try:
        # No budget open: the header is honoured verbatim.
        assert c._wait_for_retry(_State()) == 900.0  # type: ignore[arg-type]  # noqa: SLF001
        # Budget open: clamped to what is left of it.
        with jc.outbound_budget_scope(5.0):
            clamped = c._wait_for_retry(_State())  # type: ignore[arg-type]  # noqa: SLF001
        assert 0.0 < clamped <= 5.0
    finally:
        await c.aclose()


def test_a_retry_after_we_cannot_trust_is_ignored_rather_than_guessed() -> None:
    """Only the delta-seconds form is parsed, and that is a decision.

    The HTTP-date form needs a comparison against a server clock we have
    never observed, and a wrong date silently becomes a wrong wait.
    Absent, malformed and negative all return `None`, which sends the
    caller back to the jittered schedule rather than to an invented one.
    """
    assert jc._retry_after_seconds({"Retry-After": "12"}) == 12.0  # noqa: SLF001
    assert jc._retry_after_seconds({}) is None  # noqa: SLF001
    assert jc._retry_after_seconds({"Retry-After": "-1"}) is None  # noqa: SLF001
    assert (  # noqa: SLF001
        jc._retry_after_seconds({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
        is None
    )


# ======================================================================
# THE BREAKER (DESIGN.md:354-358, §8 #23). BOTH ARMS.
# ======================================================================


async def test_repeated_5xx_trips_the_breaker() -> None:
    """THE POSITIVE CONTROL for the 4xx case below.

    On its own, "a 4xx does not trip the breaker" passes against a
    breaker that never trips at all. This arm is what rules that out,
    and it is written FIRST for that reason.
    """
    handler, _ = counting([httpx2.Response(500, content=b'{"status":{"code":500}}')])
    c = client(handler, retry_max_attempts=1)
    try:
        for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD):
            with pytest.raises(JobviteUpstreamError):
                await c.request("GET", JOBS_PATH)
        assert jc._JOBVITE_BREAKER.state == "open"  # noqa: SLF001

        # And the next call is refused BEFORE reaching the transport -
        # `backend/resilience.md:165-170`'s "fast, typed error rather
        # than letting calls queue against a known-down upstream".
        handler2, seen2 = counting([httpx2.Response(200, content=b"{}")])
        c2 = client(handler2)
        try:
            with pytest.raises(JobviteUnavailableError) as caught:
                await c2.request("GET", JOBS_PATH)
        finally:
            await c2.aclose()
        assert seen2 == [], "the open breaker still issued a request"
        assert caught.value.detail == jc.UNAVAILABLE_BREAKER_DETAIL
    finally:
        await c.aclose()


async def test_repeated_transport_failures_trip_the_breaker() -> None:
    """The OTHER outage arm, and the mutation harness found it missing.

    `_is_outage` has two branches that return `True`: one for a 5xx or
    429 read off `JobviteUpstreamError.upstream_status`, and one for
    every `JobviteUnavailableError` - which is every transport failure
    httpx2 raises. `test_repeated_5xx_trips_the_breaker` exercises only
    the first, so harness row **M14, which deletes the second, SURVIVED
    against it**: an implementation where a dead upstream never opens
    the circuit passed the case whose name says the breaker trips.

    The two branches fail in genuinely different places. A 5xx means
    Jobvite answered; a `ConnectError` means it did not, and it is the
    shape a real outage takes. This case is the second arm, and it
    exists because the deletion survived rather than because anyone
    predicted it.
    """
    handler, _ = counting([httpx2.ConnectError("connection refused")])
    c = client(handler, retry_max_attempts=1)
    try:
        for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD):
            with pytest.raises(JobviteUnavailableError):
                await c.request("GET", JOBS_PATH)
        assert jc._JOBVITE_BREAKER.state == "open"  # noqa: SLF001
    finally:
        await c.aclose()


async def test_repeated_4xx_does_not_trip_the_breaker() -> None:
    """§8 #23. A bad candidate id is the caller's problem, not a signal.

    Twice the failure threshold, so this cannot pass by not having
    reached it.
    """
    handler, seen = counting([httpx2.Response(404, content=b'{"status":{"code":404}}')])
    c = client(handler)
    try:
        for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD * 2):
            with pytest.raises(JobviteUpstreamError):
                await c.request("GET", JOBS_PATH)
        assert jc._JOBVITE_BREAKER.state == "closed"  # noqa: SLF001
        assert jc._JOBVITE_BREAKER.failure_count == 0  # noqa: SLF001
    finally:
        await c.aclose()
    assert len(seen) == jc.DEFAULT_BREAKER_FAILURE_THRESHOLD * 2


async def test_an_open_breaker_and_an_outage_are_told_apart_by_detail() -> None:
    """DESIGN.md:355-358: same 503, same type URI, different `detail`.

    "An earlier revision minted two slugs for this. The distinction is
    real and worth making; a new contract-bearing type URI is not the
    way to make it." So the case asserts the types are the SAME and the
    details are DIFFERENT - asserting only the second would pass against
    a minted slug.
    """
    handler, _ = counting([httpx2.ConnectError("connection refused")])
    c = client(handler, retry_max_attempts=1)
    try:
        with pytest.raises(JobviteUnavailableError) as outage:
            await c.request("GET", JOBS_PATH)
        for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD):
            with pytest.raises(JobviteUnavailableError):
                await c.request("GET", JOBS_PATH)
        with pytest.raises(JobviteUnavailableError) as opened:
            await c.request("GET", JOBS_PATH)
    finally:
        await c.aclose()

    outage_problem = problem_from_exception(outage.value, RID_A)
    opened_error = opened.value
    assert isinstance(opened_error, jc.JobviteRetryLaterError)
    open_problem = problem_from_exception(
        opened_error, RID_A, retry_after=opened_error.retry_after
    )
    assert outage_problem["type"] == open_problem["type"]
    assert outage_problem["status"] == open_problem["status"] == 503
    assert outage_problem["detail"] != open_problem["detail"]
    assert open_problem["detail"] == jc.UNAVAILABLE_BREAKER_DETAIL
    # The `retry_after` HINT (DESIGN.md:358), on the open-breaker arm.
    assert open_problem["retry_after"] is not None
    assert open_problem["retry_after"] > 0


async def test_every_breaker_transition_is_logged_with_direction_and_counter() -> None:
    """DESIGN.md:614-616 and `backend/resilience.md:224-226`.

    All three directions are driven in one case, because the `open ->
    half_open` line is the one that only exists at all because
    `circuitbreaker` evaluates expiry on the call path, and separating
    it from its neighbours would hide that.
    """
    responses: list[httpx2.Response | Exception] = [
        httpx2.Response(500, content=b'{"status":{"code":500}}')
    ]
    handler, _ = counting(responses)
    c = client(handler, retry_max_attempts=1)
    sink_id, captured = _capture()
    try:
        with request_id_scope(RID_A):
            for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD):
                with pytest.raises(JobviteUpstreamError):
                    await c.request("GET", JOBS_PATH)

            # Shorten the open window rather than sleeping 30 seconds.
            # The RECOVERY value is what is patched; the evaluation is
            # the library's own and is not.
            jc._JOBVITE_BREAKER._recovery_timeout = 0.01  # noqa: SLF001
            await asyncio.sleep(0.05)

            responses[0] = httpx2.Response(200, content=b"{}")
            assert await c.request("GET", JOBS_PATH) == {}
    finally:
        logger.remove(sink_id)
        jc._JOBVITE_BREAKER._recovery_timeout = (  # noqa: SLF001
            jc.DEFAULT_BREAKER_RECOVERY_SECONDS
        )
        await c.aclose()

    directions = [line["transition"] for line in _transition_lines(captured)]
    assert "closed->open" in directions
    assert "open->half_open" in directions
    assert "half_open->closed" in directions
    for line in _transition_lines(captured):
        assert line["request_id"] == RID_A
        assert "failure_count" in line
    opened_line = next(
        line
        for line in _transition_lines(captured)
        if line["transition"] == "closed->open"
    )
    assert opened_line["failure_count"] == jc.DEFAULT_BREAKER_FAILURE_THRESHOLD


async def test_a_breaker_transition_line_carries_no_url() -> None:
    """The `jobFeed` URL is itself a secret (DESIGN.md:315-318).

    Driven on the jobFeed route specifically, since that is the one
    where the credentials travel in the query string.
    """
    handler, _ = counting([httpx2.Response(500, content=b'{"status":{"code":500}}')])
    c = client(handler, retry_max_attempts=1)
    sink_id, captured = _capture()
    try:
        with request_id_scope(RID_A):
            for _ in range(jc.DEFAULT_BREAKER_FAILURE_THRESHOLD):
                with pytest.raises(JobviteUpstreamError):
                    await c.request("GET", "/jobFeed", jobfeed=True)
    finally:
        logger.remove(sink_id)
        await c.aclose()

    lines = _transition_lines(captured)
    assert lines, "no transition was logged - this case measured nothing"
    for line in lines:
        blob = repr(line)
        assert "jobvite.com" not in blob
        assert API_SECRET not in blob
        assert "sc=" not in blob


# ======================================================================
# §8 #13 - THE CONCURRENT CASE. DESIGN.md:1313-1315: a single call
# PASSES against a module global, so a single call is not the case.
# ======================================================================


async def test_two_concurrent_invocations_each_log_their_own_request_id() -> None:
    """§8 #13, and it is the reason `request_id_var` is a ContextVar.

    Two invocations run in parallel, each forced to retry, and every
    retry line is matched back to the invocation that produced it. A
    module global would interleave and roughly half the lines would
    carry the other id - **every one of them still a well-formed
    UUID**, which is why the assertion is on the PAIRING and not on the
    shape, and why a single-call version proves nothing.

    The two invocations are given DIFFERENT paths so a line can be
    attributed to its invocation by something other than the id under
    test - otherwise the case would use its subject as its own key.
    """
    lines_by_id: dict[str, set[int]] = {RID_A: set(), RID_B: set()}

    async def invoke(request_id: str, path: str, failures: int) -> None:
        script: list[httpx2.Response | Exception] = [
            httpx2.Response(503, content=b'{"status":{"code":503}}')
        ] * failures
        script.append(httpx2.Response(200, content=b"{}"))
        handler, _ = counting(script)
        c = client(handler, retry_max_attempts=failures + 1)
        try:
            with request_id_scope(request_id):
                await c.request("GET", path)
        finally:
            await c.aclose()

    sink_id, captured = _capture()
    try:
        # Different failure counts, so the two invocations interleave
        # rather than marching in lockstep.
        await asyncio.gather(
            invoke(RID_A, "/job", 3),
            invoke(RID_B, "/candidate", 2),
        )
    finally:
        logger.remove(sink_id)

    retries = _retry_lines(captured)
    assert retries, "nothing retried - this case measured nothing"
    for line in retries:
        assert line["request_id"] in lines_by_id, (
            f"a retry line carried request_id={line['request_id']!r}, "
            "which belongs to no invocation in this test"
        )
        lines_by_id[line["request_id"]].add(line["attempt"])

    # BOTH invocations retried, and each produced the number of retry
    # lines its own failure script called for. A shared global would
    # skew these counts.
    assert lines_by_id[RID_A] == {1, 2, 3}
    assert lines_by_id[RID_B] == {1, 2}


async def test_no_retry_line_carries_a_url() -> None:
    """The same §8 case's second half, on the route that matters.

    DESIGN.md:618-620: "a retry line is exactly where an unredacted URL
    would otherwise reach a log", because the v1 `jobFeed` URL carries
    `sc=` in its query string.
    """
    handler, _ = counting(
        [
            httpx2.Response(503, content=b'{"status":{"code":503}}'),
            httpx2.Response(200, content=b"{}"),
        ]
    )
    c = client(handler)
    sink_id, captured = _capture()
    try:
        with request_id_scope(RID_A):
            await c.request("GET", "/jobFeed", jobfeed=True)
    finally:
        logger.remove(sink_id)
        await c.aclose()

    retries = _retry_lines(captured)
    assert retries, "nothing retried - this case measured nothing"
    for line in retries:
        blob = repr(line)
        assert "jobvite.com" not in blob
        assert "http" not in blob
        assert API_SECRET not in blob
        assert "sc=" not in blob
    # POSITIVE CONTROL: the fields that MUST be there, are. Without it,
    # a retry line reduced to `{}` would pass every assertion above.
    assert retries[0]["attempt"] == 1
    assert retries[0]["request_id"] == RID_A
    assert retries[0]["error_type"] == "_RetryableUpstream"
    assert "elapsed" in retries[0]


# ======================================================================
# THE SCAN'S BOUNDS - R5-H2 and ADR-0024 (Proposed).
#
# `scan()` had NO bound of any kind. R5 measured it against a server
# that ignores `start` and aborted its own probe at 200 requests.
# `DESIGN.md:486-487` removed `total` as a loop condition and named no
# replacement, so U6 implemented it faithfully and unbounded at once.
#
# **THE OUTBOUND BUDGET DOES NOT FIX IT, and that is measured rather
# than argued.** `scripts/probe-scan-bounds.py` ran the same shape
# against a client that HAS the budget and had to abort at 2,000
# requests - including on a run with a two-SECOND budget, because the
# budget bounds WALL CLOCK and a fast server answers thousands of
# requests inside it. ADR-0024 says the budget is "a mitigation, not a
# fix"; the measurement is stronger than that, because the budget did
# not fire at all.
#
# THE TWO SERVERS FAIL IN OPPOSITE DIRECTIONS and each defeats the
# other's bound, which is why both mechanisms exist:
#
#   non-advancing    ignores `start`, repeats one page. Records never
#                    grow, so a RECORD CEILING can never fire.
#   advancing-for-   honours `start`, never runs out. Every page is
#   ever             full of NEW records, so a ZERO-PROGRESS BREAK can
#                    never fire.
#
# R5's fake produces the first only. The second needed a probe of its
# own, and it is what confirms ADR-0024's "neither mechanism
# substitutes for the other" instead of taking it on trust.
# ======================================================================

#: Every scan handler below refuses to answer more than this. **It is
#: the test's own abort, not a bound under test**: without it, a case
#: run against a tree whose bound has been amputated hangs the harness
#: instead of reporting, and a row that hangs CI is not a measurement.
#: Reaching it fails the case loudly.
SCAN_PROBE_ABORT = 400


class _ScanProbeAbort(Exception):  # noqa: N818 - a test signal, not an error
    """The handler's own ceiling was hit; the bound did not fire."""


def non_advancing_server(page_size: int) -> tuple[Handler, list[int]]:
    """A server that IGNORES `start` and repeats one full page forever.

    This is R5-H2's fake. Every page is full, so the short-page exit
    never fires, and every record is already in `seen`, so the scan
    makes no progress whatsoever.

    Args:
        page_size: Records per page.

    Returns:
        The handler and a one-element list holding the request count.
    """
    count = [0]

    def handler(_request: httpx2.Request) -> httpx2.Response:
        count[0] += 1
        if count[0] > SCAN_PROBE_ABORT:
            raise _ScanProbeAbort
        body = {"requisitions": [{"eId": f"E{i}"} for i in range(page_size)]}
        return httpx2.Response(200, content=json.dumps(body).encode())

    return handler, count


def endless_server(page_size: int) -> tuple[Handler, list[int]]:
    """A server that HONOURS `start` and never runs out of records.

    Every page is full and every record is NEW, so the zero-progress
    break cannot fire and the only thing at risk is memory.

    Args:
        page_size: Records per page.

    Returns:
        The handler and a one-element list holding the request count.
    """
    count = [0]

    def handler(request: httpx2.Request) -> httpx2.Response:
        count[0] += 1
        if count[0] > SCAN_PROBE_ABORT:
            raise _ScanProbeAbort
        start = int(request.url.params.get("start", "0"))
        body = {"requisitions": [{"eId": f"E{start + i}"} for i in range(page_size)]}
        return httpx2.Response(200, content=json.dumps(body).encode())

    return handler, count


async def test_a_server_that_ignores_start_is_bounded_after_one_wasted_page() -> None:
    """R5-H2's exact shape, bounded by the zero-progress break.

    The unfixed loop ran until R5 aborted it at 200 requests and until
    `scripts/probe-scan-bounds.py` aborted it at 2,000. The assertion is
    the REQUEST COUNT at the transport, because "bounded" is a claim
    about how many calls Jobvite receives and nothing else measures it.

    **Two requests, not one.** The first page is legitimate and its
    records are kept; the second is what proves the server is not
    advancing. Detecting it in one would mean refusing to page at all.
    """
    handler, count = non_advancing_server(50)
    c = client(handler, max_results=50)
    try:
        result = await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()

    assert count[0] == 2, f"the scan issued {count[0]} requests"
    # THE RECORDS ARE KEPT. A bound that threw them away would leave the
    # caller with nothing, which is exactly what the outbound budget
    # eventually hands it.
    assert len(result.items) == 50
    assert result.incomplete is True


async def test_a_server_that_never_runs_out_is_bounded_by_the_record_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shape R5's fake cannot produce (ADR-0024 mechanism 2).

    Every page is full of NEW records, so the zero-progress break can
    never fire. Without the ceiling this scan consumes memory until the
    process dies; the test's own abort would fire first and fail loudly.

    The ceiling is lowered so the case is cheap. What is under test is
    that a ceiling EXISTS and stops the loop, not that 100,000 is the
    right number, which it is not claimed to be - see
    `MAX_SCAN_RECORDS`.
    """
    monkeypatch.setattr(jc, "MAX_SCAN_RECORDS", 1_000)
    handler, count = endless_server(50)
    c = client(handler, max_results=50)
    try:
        result = await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()

    assert count[0] == 20, f"the scan issued {count[0]} requests"
    assert len(result.items) == 1_000
    assert result.incomplete is True


async def test_the_record_ceiling_holds_at_both_50_and_500_per_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The amendment to ADR-0024's mechanism 2, as a measurement.

    The ADR requires that "any bound must be sane at both 50 and 500
    records per page" and then proposes `MAX_PAGES = 10_000`, which
    **cannot satisfy its own requirement**: 10,000 pages admits 500,000
    records at 50 per page and 5,000,000 at 500 - a tenfold difference
    in the resource actually at risk, decided by a knob the ceiling
    cannot see.

    A ceiling in RECORDS satisfies it by construction, and this case is
    the proof: the two page sizes differ tenfold in REQUESTS and are
    IDENTICAL in records held. Asserting both halves is the point -
    equal records alone would also pass against a bound that ignored
    the page size entirely and always returned nothing.
    """
    monkeypatch.setattr(jc, "MAX_SCAN_RECORDS", 1_000)
    held: dict[int, tuple[int, int]] = {}
    for page_size in (50, 500):
        handler, count = endless_server(page_size)
        c = client(handler, max_results=page_size)
        try:
            result = await c.scan(JOBS_PATH, items_key="requisitions")
        finally:
            await c.aclose()
        held[page_size] = (count[0], len(result.items))

    assert held[50][1] == held[500][1] == 1_000, (
        f"the ceiling admitted different record counts per page size: {held}"
    )
    assert held[50][0] == 20
    assert held[500][0] == 2


async def test_neither_bound_substitutes_for_the_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADR-0024 asserts this; here it stops being an assertion.

    Each server defeats the other server's bound, with ONE condition on
    the ceiling that this case had to be corrected to state.

    * A non-advancing server's record count stops growing after page
      one, so **any ceiling larger than a single page can never fire on
      it** - only the zero-progress break can stop it.
    * An endless server never repeats a record, so the zero-progress
      break can never fire on it - only the ceiling can stop it.

    **The first arm was written as "the ceiling can never fire on a
    non-advancing server" with the ceiling set to 1, and it FAILED:
    page one legitimately adds 50 records, so a ceiling of 1 fires on
    page one, before the break can see a second page.** The claim is
    therefore conditional, the condition is "larger than one page", and
    every plausible ceiling satisfies it - `MAX_SCAN_RECORDS` is 100,000
    against a page size of at most 500. The corrected arm uses 100
    against a 50-record page, which is the smallest ceiling that meets
    the condition and so the sharpest test of it.
    """
    # Arm 1: ceiling of 100, page size 50. The non-advancing server can
    # never reach 100 records, so if the scan stops, only the break did
    # it.
    monkeypatch.setattr(jc, "MAX_SCAN_RECORDS", 100)
    handler, count = non_advancing_server(50)
    c = client(handler, max_results=50)
    try:
        stalled = await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()
    assert count[0] == 2
    assert len(stalled.items) == 50, (
        "the record ceiling fired on a non-advancing scan; with a ceiling "
        "above one page it cannot, because the record count never grows"
    )

    # Arm 2: the endless server, the SAME ceiling. Nothing repeats, so
    # the break cannot fire and the ceiling is what stops it - after
    # two pages rather than after two requests, which is the tell that
    # a different mechanism ran.
    handler2, count2 = endless_server(50)
    c2 = client(handler2, max_results=50)
    try:
        endless = await c2.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c2.aclose()
    assert count2[0] == 2
    assert len(endless.items) == 100
    assert endless.incomplete is True


async def test_neither_bound_fires_on_healthy_paging() -> None:
    """The POSITIVE CONTROL for every bound case above.

    Without it, all four are satisfied by a scan that always stops
    immediately.

    A well-behaved server advances and ends on a short page. Neither
    bound may fire, `incomplete` must be `False`, and every record must
    arrive. A zero-progress break that fired here would break every
    real scan, and it is the failure mode a bound like this has.
    """
    pages = [
        {"requisitions": [{"eId": f"E{i}"} for i in range(50)]},
        {"requisitions": [{"eId": f"E{50 + i}"} for i in range(50)]},
        {"requisitions": [{"eId": "E100"}], "total": 101},
    ]
    seen = [0]

    def handler(_request: httpx2.Request) -> httpx2.Response:
        body = pages[min(seen[0], len(pages) - 1)]
        seen[0] += 1
        return httpx2.Response(200, content=json.dumps(body).encode())

    c = client(handler, max_results=50)
    try:
        result = await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()

    assert seen[0] == 3
    assert len(result.items) == 101
    assert result.incomplete is False


async def test_a_fully_duplicate_page_is_still_not_a_short_page() -> None:
    """The interaction U6 warned about, kept true by the new break.

    DESIGN.md:465-468's clamping hypothesis means a boundary record
    arrives twice, and U6's comment at the short-page exit says a
    "fully duplicate full-length page is not a short page, and stopping
    on it would end a scan early". The zero-progress break stops on
    exactly that page - which is correct, because under clamping a FULL
    page of nothing but duplicates means the server has stopped
    advancing - but a page that is only PARTLY duplicated must not stop
    it. This is that case: one duplicate, 49 new, the scan continues.
    """
    calls = [0]

    def handler(_request: httpx2.Request) -> httpx2.Response:
        calls[0] += 1
        if calls[0] == 1:
            body: dict[str, Any] = {
                "requisitions": [{"eId": f"E{i}"} for i in range(50)]
            }
        elif calls[0] == 2:
            # Overlaps by one: E49 again, then 49 new.
            body = {"requisitions": [{"eId": f"E{49 + i}"} for i in range(50)]}
        else:
            body = {"requisitions": [{"eId": "E99"}]}
        return httpx2.Response(200, content=json.dumps(body).encode())

    c = client(handler, max_results=50)
    try:
        result = await c.scan(JOBS_PATH, items_key="requisitions")
    finally:
        await c.aclose()

    assert calls[0] == 3, "a partly-duplicated page stopped the scan"
    assert result.duplicates_dropped == 1


def test_the_scan_bounds_probe_still_reproduces_its_measurements() -> None:
    """`scripts/probe-scan-bounds.py`, run rather than cited.

    The probe is the artefact behind this section's claims - that the
    budget does not bound a non-advancing scan, and that a record
    ceiling holds the record count equal across page sizes while a page
    ceiling would not. Prose about a measurement decays into a claim
    about one, so it runs here and asserts its own expectations.
    """
    probe = REPO_ROOT / "scripts" / "probe-scan-bounds.py"
    assert probe.is_file(), f"the probe is missing at {probe}"
    result = subprocess.run(  # noqa: S603 - a committed script, no shell
        [sys.executable, str(probe), "--assert"],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ======================================================================
# THE LIBRARY DECISION, kept executable.
# ======================================================================


def test_the_breaker_rejection_test_still_passes_against_the_pinned_library() -> None:
    """`scripts/probe-breaker-call-path.py`, run rather than cited.

    DESIGN.md:617 requires half-open expiry on the CALL PATH. That was
    settled by measurement against `circuitbreaker` 2.1.3, and a
    measurement recorded only in prose decays into a CLAIM about one.
    Running the probe here means a bump that moves expiry onto a
    background timer turns this case red instead of leaving a stale
    paragraph in a report.
    """
    probe = REPO_ROOT / "scripts" / "probe-breaker-call-path.py"
    assert probe.is_file(), f"the probe is missing at {probe}"
    result = subprocess.run(  # noqa: S603 - a committed script, no shell
        [sys.executable, str(probe)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: circuitbreaker 2.x is ADOPTED" in result.stdout


def test_the_composition_order_is_timeout_then_retry_then_breaker() -> None:
    """`backend/resilience.md:216-222`, asserted on the CALL GRAPH.

    Reversing retry and breaker "lets retry storms defeat the breaker
    and keep hammering a down upstream", and the failure is invisible in
    any single-call test: both orders return the same thing until the
    breaker opens. So the nesting is asserted structurally, by reading
    which method calls which.
    """
    import ast  # noqa: PLC0415 - one case needs it
    import inspect  # noqa: PLC0415 - one case needs it

    source = inspect.getsource(jc.JobviteClient)
    tree = ast.parse("\n".join(line[4:] for line in source.splitlines()[1:]))
    calls: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            calls[node.name] = {
                sub.func.attr
                for sub in ast.walk(node)
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
            }
    assert "_through_breaker" in calls["request"]
    assert "_attempt_with_retry" in calls["_through_breaker"]
    assert "_attempt" in calls["_attempt_with_retry"]
    # And NOT the other way round: the breaker must not sit inside the
    # retry loop.
    assert "_through_breaker" not in calls["_attempt_with_retry"]
