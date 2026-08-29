"""`search_jobs`: the first end-to-end tool (DESIGN.md:137).

**`get_job_feed` is U12's and shares this file.** This module holds
only the `search_jobs` half; the plan's SS4 ownership table splits the
file between the two units, so nothing here anticipates the feed.

**Why jobs and not candidates.** `search_jobs` is the **public job
data** class, so this slice exercises transport selection, config
fail-fast, the error contract, the audit path, the result cap and
`_meta` **without** depending on EEO exclusion, candidate PII
redaction, or red-team fencing content. It is the smallest end-to-end
path through every cross-cutting mechanism on the least dangerous data
class.

**The IN-TOOL half of the result cap only** (DESIGN.md:469-477).
`JOBVITE_MAX_RESULTS` is applied here to a single page's items, and
the result reports `showing N of total` from the envelope's own
`total` rather than truncating silently. **The
`min(transport_cap, configured_result_cap)` composition is U6's**, so
one behaviour is not built twice: U6 owns the outbound page cap and
the `min()` that composes them, and does not re-implement this
module's reporting string.

**The error path returns, never raises** (DESIGN.md:536-540). Every
typed failure becomes an RFC 9457 problem object carried in
`ToolResult(structured_content=problem, is_error=True)`. Measured on
this stack rather than assumed: a problem object returned that way
reaches the wire **unvalidated against the output schema**, so the
seven required members survive even though they satisfy no field of
`JobSearchResult`. That is the property DESIGN.md:536-540 claims and
it is what makes a problem object the one error shape no
configuration can distort.

**`request_id` is stamped into `_meta`, not into the model**
(DESIGN.md:629-637). `_meta` is the protocol's own channel and the
result validator never inspects it, whereas an undeclared top-level
key in structured content is rejected outright.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Final, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.base import ToolResult
from pydantic import ConfigDict, Field

from ..audit import (
    AuditPhase,
    Transport,
    audit_scope,
    emit,
)
from ..config import GET_JOB_FEED, SEARCH_JOBS, Settings
from ..errors import problem_from_exception
from ..models.job_feed import (
    JOB_FEED_ENVELOPE_KEY,
    FeedJob,
    JobFeedResult,
)
from ..models.jobs import (
    JOBS_ENVELOPE_KEY,
    TOTAL_ENVELOPE_KEY,
    Job,
    JobLocation,
    JobSearchResult,
)
from ..services.jobvite_client import JOBFEED_PATH, JobviteClient
from ..utils.constraints import InboundModel, JobviteIdentifier

#: The namespaced `_meta` key `request_id` travels to the caller under
#: (DESIGN.md:624-627). `io.modelcontextprotocol/*` is reserved, and
#: the spec's own `SERVER_INFO_META_KEY` is the precedent: server
#: stamped, and documented as display and debugging only, never
#: behaviour or security - which is exactly this value's class.
REQUEST_ID_META_KEY: Final = "com.evolvconsulting.fast-mcp-jobvite/requestId"

#: The v2 route this tool calls (DESIGN.md:137).
JOBS_PATH: Final = "/job"

#: **Every route this module asks the client for**, and the container
#: the start-base overrides below are built from rather than a second
#: hand-kept copy of the same knowledge.
#:
#: `JOBVITE_PAGINATION_START_BASE` is a SCALAR
#: (`config.py:pagination_start_base`) and the client takes a per-route
#: `Mapping` (DESIGN.md:478-480), so something has to name the routes
#: the scalar applies to. A list written beside the call site would be
#: blind to the route nobody added to it - the defect this project has
#: recorded seven times - so
#: `test_the_client_routes_tuple_lists_every_route_this_module_asks_for`
#: enumerates the CONTAINER, parsing every client call in this file,
#: and asserts the two sets are EQUAL rather than merely overlapping.
CLIENT_ROUTES: Final = (JOBS_PATH, JOBFEED_PATH)


class SearchJobsInput(InboundModel):
    """Arguments for `search_jobs`.

    **Deliberately narrow, and the narrowness is evidence-bound rather
    than an oversight.** `JOBVITE-CONTRACT.md` SS7 documents exactly
    three request parameters for `GET /api/v2/job`: `ids`, `start` and
    `count`. `start` and `count` are **U6's** - paging around the
    client's one request entry point belongs to that unit - which
    leaves `ids`.

    **No date filter is offered**, and that is the load-bearing
    omission. The research says an integration README claims
    "date-filtered GET" is supported but **does not name the
    parameters**, and marks `datestart`/`dateend` as `[ASSUMED]` by
    analogy with `/candidate`. Sending a parameter whose name we
    guessed would be silently ignored by Jobvite, and the tool would
    then return an **unfiltered** page while the caller believed it
    was filtered - a wrong answer that explains itself. Checklist row 6
    is what settles the names.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    ids: Annotated[
        JobviteIdentifier | None,
        Field(
            default=None,
            description=(
                "Fetch one job by its Jobvite `eId`. Omit to list the "
                "first page of jobs. A single id only: whether the "
                "route accepts a comma-separated list is unverified."
            ),
        ),
    ] = None


def _to_job(raw: dict[str, Any]) -> Job:
    """Map one Jobvite requisition onto the allow-listed model.

    **The allow-list is applied here, by naming each key**, rather
    than by handing Jobvite's object to pydantic and trusting
    `extra="forbid"` to reject it. The two differ in the direction
    that matters: `extra="forbid"` would make a **new Jobvite field**
    an error and take the whole call down, while DESIGN.md:192-195
    requires it to be **dropped** - "a new Jobvite field is dropped
    until someone admits it deliberately". Failing closed here means
    dropping the field, not failing the tool.

    Args:
        raw: One element of the `requisitions` array.

    Returns:
        The admitted subset, as a `Job`.
    """
    locations = raw.get("locations") or []
    return Job(
        eid=raw.get("eId") or "",
        title=raw.get("title") or "",
        description=raw.get("description"),
        apply_link=raw.get("applyLink"),
        job_state=raw.get("jobState"),
        department=raw.get("department"),
        category=raw.get("category"),
        locations=[
            JobLocation(
                city=item.get("city"),
                state=item.get("state"),
                country=item.get("country"),
            )
            for item in locations
            if isinstance(item, dict)
        ],
        last_updated_date=raw.get("lastUpdatedDate"),
        sent_date=raw.get("sentDate"),
    )


def build_result(payload: dict[str, Any], max_results: int) -> JobSearchResult:
    """Apply the in-tool result cap to one page (DESIGN.md:469-477).

    **Reports rather than truncates.** A capped result is a mismatch
    against `total` **by design** - DESIGN.md:474-476's own worked
    example is `showing 50 of 1,240` - so the cap is surfaced in the
    result's `summary` and is explicitly *not* an anomaly to be
    logged. DESIGN.md:469-473 is emphatic that wiring a completeness
    alarm to every call would fire it on the default path and train
    everyone to ignore it.

    **`total` comes from the envelope, never from `len(items)`.**
    DESIGN.md:487-489: `total` is reported and never trusted as a loop
    condition. Counting the returned items instead would make
    `showing N of N` true on every call and delete the only signal
    that a page was capped.

    Args:
        payload: The decoded Jobvite envelope.
        max_results: `JOBVITE_MAX_RESULTS`, the configured half of
            DESIGN.md:436-438's `min(transport_cap,
            configured_result_cap)`. U6 adds the transport half.

    Returns:
        The capped page, with the cap reported.
    """
    items = payload.get(JOBS_ENVELOPE_KEY) or []
    jobs = [_to_job(item) for item in items[:max_results] if isinstance(item, dict)]
    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return JobSearchResult(jobs=jobs, total=total)


def register(
    server: FastMCP[Any],
    settings: Settings,
    *,
    client_factory: Callable[[], JobviteClient] | None = None,
) -> None:
    """Register this module's tools, each behind its OWN enable gate.

    **Two tools, two gates, one entry point.** `server.py` calls this
    module once (`server.py:137`), so `get_job_feed` needs no line of
    its own there - which is what keeps U12 out of a file another agent
    holds. The dispatch is a pair of calls rather than one function
    with two early returns, because `search_jobs` being disabled must
    not stop `get_job_feed` registering: the two tools take
    **different credentials** (DESIGN.md:312-321), so a deployment
    holding only the feed credential is a configuration
    `validate_settings` accepts and this function has to serve.

    Args:
        server: The instance to register on.
        settings: Settings that have already passed
            `validate_settings`.
        client_factory: Builds the `JobviteClient` for one invocation.
            Substituted in tests to inject `httpx2.MockTransport`
            (DESIGN.md:1359-1360). `None` uses the real client.
    """
    _register_search_jobs(server, settings, client_factory=client_factory)
    _register_get_job_feed(server, settings, client_factory=client_factory)


def _register_search_jobs(
    server: FastMCP[Any],
    settings: Settings,
    *,
    client_factory: Callable[[], JobviteClient] | None = None,
) -> None:
    """Register `search_jobs`, if it is enabled.

    **The gate is `settings.enabled_tools`, and it is checked here**
    rather than inside the tool body: DESIGN.md:917-934 makes
    registration the deploy-time control, and a tool that registers
    and then refuses is a tool a client can still see.

    Args:
        server: The instance to register on.
        settings: Settings that have already passed
            `validate_settings`.
        client_factory: Builds the `JobviteClient` for one invocation.
            Substituted in tests to inject `httpx2.MockTransport`
            (DESIGN.md:1359-1360). `None` uses the real client.
    """
    if SEARCH_JOBS not in settings.enabled_tools:
        return

    # DESIGN.md:698-700's two spellings, and they agree with U1's
    # `mcp_transport` literal by construction rather than by luck:
    # `Transport` is a StrEnum whose members are exactly `"stdio"` and
    # `"http"`, and `Literal["stdio", "http"]` is what config.py
    # declares. A test pins the two sets equal, because nothing else
    # would fail if they drifted.
    transport = Transport(settings.mcp_transport)

    # Resolved ONCE, at registration, and refused loudly if absent.
    #
    # `validate_settings` has already refused a configuration that
    # enables `search_jobs` without these, so reaching here with
    # `None` is a programming error rather than a user's input -
    # exactly the class R3-L1 moved out of `missing_for`'s `.get`
    # fallback and into a `KeyError`. Failing at boot keeps the
    # refusal where config.py puts every other one; deferring it to
    # the first call would turn a misconfiguration into a 500 the
    # caller sees.
    if settings.api_key is None or settings.api_secret is None:
        msg = (
            f"{SEARCH_JOBS} is enabled but its credentials are unset; "
            f"validate_settings should have refused this configuration"
        )
        raise ValueError(msg)
    api_key = settings.api_key
    api_secret = settings.api_secret

    def _client() -> JobviteClient:
        if client_factory is not None:
            return client_factory()
        # THE COMPOSITION POINT U4 COULD NOT EXERCISE. `api_key` is a
        # pydantic `SecretStr`; `JobviteClient` declares a structural
        # `SecretValue` Protocol rather than importing pydantic. This
        # is the first shipped code that passes one through, and mypy
        # checks the satisfaction here.
        #
        # `max_results` IS PASSED, and leaving it out was U6's F1. The
        # result cap is one behaviour split across two files: this
        # module applies it in-tool at :317 and owns the
        # `showing N of total` string, while the client bounds what
        # leaves the transport. With it omitted the client fell back to
        # its own default, so `JOBVITE_MAX_RESULTS=200` moved one half
        # and not the other - and NO TEST COULD SEE IT, because each
        # half is correct in isolation. That is the exact shape
        # DESIGN.md:434-436 warns about when it says neither unit owns
        # all of it.
        #
        # `company_id` is passed for the same reason and is latent
        # today: only `jobFeed` needs it (DESIGN.md:320-321) and this
        # tool does not call that route. Wiring it here rather than
        # when U12 arrives keeps the factory's argument list a
        # description of the settings, not of the current caller.
        #
        # `start_base_overrides` IS PASSED, and leaving it out was
        # R5-M1 - F1's sibling in the argument list F1 was fixed in.
        # `grep -rn "pagination_start_base" src/` returned exactly one
        # line, its own definition: the knob `.env.example` documents
        # for an operator who has ESTABLISHED the base against a live
        # tenant reached no code at all. Latent like `company_id`,
        # because `scan()` has no caller in `src/` yet (U8/U12), and
        # wired now for the same reason: the factory's argument list
        # should describe the settings, not the current caller.
        #
        # **The scalar is applied to every route this module uses, not
        # made global**, because the client's contract is per-route and
        # widening it is U6-F2's decision, not this call site's. Guarded
        # on `is not None` so an unset variable leaves `SCAN_START`
        # alone - an override written as 0 is still an override.
        return JobviteClient(
            api_key=api_key,
            api_secret=api_secret,
            company_id=settings.company_id,
            max_results=settings.max_results,
            start_base_overrides=(
                None
                if settings.pagination_start_base is None
                else dict.fromkeys(CLIENT_ROUTES, settings.pagination_start_base)
            ),
        )

    @server.tool(
        name=SEARCH_JOBS,
        # `mode="serialization"`, and the default is WRONG here in a
        # way that fails loudly only because the client validates.
        # pydantic's default is `mode="validation"`, which omits
        # `computed_field`s - so `showing` and `summary` would be
        # absent from the advertised schema while every result carried
        # them, and `extra="forbid"` renders as
        # `additionalProperties: false`. Measured:
        # `ClientSession.validate_tool_result` then rejects our own
        # success payload with "Additional properties are not
        # allowed". An output schema is a claim about what we SERIALISE.
        output_schema=JobSearchResult.model_json_schema(mode="serialization"),
        # Advisory only (DESIGN.md:270-274). Verified: one non-test
        # reference exists in the whole framework and nothing acts on
        # them. Set because a well-behaved host may prompt on them;
        # never counted as a control.
        annotations={"readOnlyHint": True},
    )
    async def search_jobs(
        params: SearchJobsInput,
        ctx: Context,
    ) -> ToolResult:
        """Search Jobvite requisitions.

        Returns a single page of jobs, capped at the server's
        configured result limit and reporting `showing N of total`
        rather than truncating silently.
        """
        # `ctx.request_context.meta` is a plain mapping of the wire
        # `_meta`. MEASURED against a live FastMCP context on
        # fastmcp 4.0.0b4, which is what U3 could not do: it had no
        # server to get a context from and tested its parse call site
        # against the wire contract instead. A `traceparent` sent by
        # the caller arrives here verbatim, beside the reserved
        # `io.modelcontextprotocol/*` keys.
        #
        # NAMED ATTRIBUTE ACCESS, not `getattr(..., "meta", None)`
        # (R4-L2). The old form turned a future library RENAME into
        # amputation row A11 - trace context silently dropped from
        # every audit event, at exit 0, with no error anywhere. Reading
        # `.meta` by name makes a rename an `AttributeError` at the
        # call site, which is the louder and therefore correct failure
        # for a property the audit trail depends on.
        #
        # THE `None` BRANCH IS NOT THE SAME GUARD, and R4-L2's
        # suggested one-liner did not type-check: fastmcp declares
        # `request_context` as `FastMCPRequestContext | None`, so this
        # is a DECLARED optional rather than a defensive default. It is
        # written out explicitly so the two cases stay distinguishable
        # - a context we were never given is not a renamed attribute.
        request_context = ctx.request_context
        meta = request_context.meta if request_context is not None else None
        with audit_scope(
            SEARCH_JOBS,
            transport,
            arguments=params.model_dump(mode="json"),
            meta=meta,
        ) as event:
            try:
                async with _client() as client:
                    payload = await client.request(
                        "GET",
                        JOBS_PATH,
                        params=(
                            {"ids": params.ids} if params.ids is not None else None
                        ),
                    )
                result = build_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                # AuditPhase.READ: a read is recoverable and losing the
                # tool is worse than losing one audit line
                # (DESIGN.md:713-715). The warnings it can return are
                # for a POST-WRITE failure only, so a read discards
                # them - there is no success payload to attach them to
                # on this branch.
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )


class GetJobFeedInput(InboundModel):
    """Arguments for `get_job_feed`.

    **Narrow on purpose, and narrower than the evidence permits.**
    `JOBVITE-CONTRACT.md` §9 is the only complete `[OFFICIAL]`
    parameter table in the whole document - `type`, `availableTo`,
    `category`, `location`, `region`, `department`, `start`, `count`.
    `start` and `count` are **U6's**, and of the remaining six only
    these two are offered:

    - `job_type` and `available_to` have documented value spaces. A
      wrong `available_to` is refused by the model rather than sent.
    - `category`, `location`, `region` and `department` are
      **tenant-configured vocabularies**. Nothing in the research
      records one tenant's values, so a model would be guessing the
      value rather than the parameter name, and Jobvite answers a
      filter it cannot match with an empty feed - a wrong answer that
      explains itself, which is the same failure `SearchJobsInput`
      withholds its date filter to avoid. Adding them later is
      additive and costs no caller anything; removing them would not
      be.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    job_type: Annotated[
        JobviteIdentifier | None,
        Field(
            default=None,
            description=(
                "Filter by employment type, e.g. `Full-time`, "
                "`Part-time`, `Contractor`, `Intern`. Jobvite's own "
                "list is open-ended, so this is not an enumeration."
            ),
        ),
    ] = None

    available_to: Annotated[
        Literal["External", "Internal"] | None,
        Field(
            default=None,
            description=(
                "Which audience the postings are visible to. Jobvite "
                "defaults to `External` when the parameter is omitted."
            ),
        ),
    ] = None


def _to_feed_job(raw: dict[str, Any]) -> FeedJob:
    """Map one v1 feed job onto the allow-listed model.

    **Each key is named here**, for the reason `_to_job` gives: a new
    Jobvite field must be *dropped* (DESIGN.md:192-195), not turned
    into an error that takes the whole call down.

    **This is where the third name stops travelling.** Jobvite's keys
    on this route (`id`, `jobtype`, `detail-url`, `briefdescription`)
    are read exactly once, here, and everything downstream sees the
    same attribute names `search_jobs` returns.

    Args:
        raw: One element of the feed's `jobs` array.

    Returns:
        The admitted subset, as a `FeedJob`.
    """
    return FeedJob(
        eid=raw.get("id") or "",
        title=raw.get("title") or "",
        requisition_id=raw.get("requisitionid"),
        category=raw.get("category"),
        job_type=raw.get("jobtype"),
        location=raw.get("location"),
        date=raw.get("date"),
        detail_url=raw.get("detail-url"),
        apply_url=raw.get("apply-url"),
        brief_description=raw.get("briefdescription"),
        description=raw.get("description"),
        hiring_manager=raw.get("hiringManager"),
    )


def build_feed_result(payload: dict[str, Any], max_results: int) -> JobFeedResult:
    """Apply the in-tool result cap to a feed page (DESIGN.md:469-477).

    The same shape as `build_result`, reading `JOB_FEED_ENVELOPE_KEY`
    where that one reads `JOBS_ENVELOPE_KEY` - **the whole of the
    difference between the two routes' envelopes** (§9 hazard 3).

    **`total` comes from the envelope, never from `len(items)`**
    (DESIGN.md:487-489). Counting the returned items would make
    `showing N of N` true on every call and delete the only signal
    that a page was capped.

    **THE TRANSPORT CAP IS NOT APPLIED HERE AND MUST NOT BE.** The
    1000-record `/v1/jobFeed` page cap is stated once, in the client
    layer (DESIGN.md:434), and `services/jobvite_client.py` enforces
    it at `JOBFEED_PAGE_CAP`. This is the *configured result cap*, the
    other half of DESIGN.md:436-438's `min(transport_cap,
    configured_result_cap)`. Re-applying 1000 here would be a second
    copy of one number in a file that does not own it.

    Args:
        payload: The decoded Jobvite envelope.
        max_results: `JOBVITE_MAX_RESULTS`.

    Returns:
        The capped page, with the cap reported.
    """
    items = payload.get(JOB_FEED_ENVELOPE_KEY) or []
    jobs = [
        _to_feed_job(item) for item in items[:max_results] if isinstance(item, dict)
    ]
    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
    total = raw_total if isinstance(raw_total, int) else len(items)
    return JobFeedResult(jobs=jobs, total=total)


def _feed_params(params: GetJobFeedInput) -> dict[str, str] | None:
    """Build the non-credential query parameters for the feed call.

    Returns `None` when nothing was supplied, so an unfiltered call
    sends no filter at all rather than an empty one: a `type=` with no
    value is a filter Jobvite may match nothing against, and an empty
    feed for a caller who asked for everything is the silent wrong
    answer this module keeps refusing to produce.

    **The credentials are NOT built here.** `api`, `sc` and
    `companyId` are added by `JobviteClient.jobfeed_params()`, inside
    the client, which is the one place a URL carrying a secret is
    constructed (DESIGN.md:312-318).

    Args:
        params: The validated arguments.

    Returns:
        The query mapping, or `None` when no filter was supplied.
    """
    query = {
        key: value
        for key, value in (
            ("type", params.job_type),
            ("availableTo", params.available_to),
        )
        if value is not None
    }
    return query or None


def _register_get_job_feed(
    server: FastMCP[Any],
    settings: Settings,
    *,
    client_factory: Callable[[], JobviteClient] | None = None,
) -> None:
    """Register `get_job_feed`, if it is enabled.

    **The separate credential class, resolved once at registration**
    (DESIGN.md:320-321). `feed_key`, `feed_secret` and `company_id`
    are a different class from `search_jobs`' `api_key`/`api_secret`,
    and `TOOL_REQUIREMENTS[GET_JOB_FEED]` already refuses a deployment
    that enables this tool without all three - so reaching the
    `ValueError` below is a programming error, not a user's input, and
    it is raised at boot rather than turned into a 500 on first call.

    Args:
        server: The instance to register on.
        settings: Settings that have already passed
            `validate_settings`.
        client_factory: Builds the `JobviteClient` for one invocation.
            Substituted in tests to inject `httpx2.MockTransport`.
    """
    if GET_JOB_FEED not in settings.enabled_tools:
        return

    transport = Transport(settings.mcp_transport)

    if (
        settings.feed_key is None
        or settings.feed_secret is None
        or settings.company_id is None
    ):
        msg = (
            f"{GET_JOB_FEED} is enabled but its credentials are unset; "
            f"validate_settings should have refused this configuration"
        )
        raise ValueError(msg)
    feed_key = settings.feed_key
    feed_secret = settings.feed_secret
    company_id = settings.company_id

    def _client() -> JobviteClient:
        if client_factory is not None:
            return client_factory()
        # THE FEED CREDENTIAL, IN ITS OWN CLASS. `api_key` and
        # `api_secret` here are the FEED's key and secret, not
        # `search_jobs`' pair: the client's parameter names describe
        # the position in the request, and on this route that position
        # is the `api` and `sc` QUERY PARAMETERS
        # (`jobvite_client.py:jobfeed_params`). Passing the v2 pair
        # would authenticate the feed with a credential the design
        # keeps separate precisely so the two can be scoped apart
        # (DESIGN.md:320-321, §7.2).
        #
        # `company_id` IS NOT LATENT ON THIS PATH, unlike the
        # `search_jobs` factory: the route refuses without it, and the
        # refusal is a `RuntimeError` mapped to
        # `/problems/internal-error` rather than a misleading 502.
        return JobviteClient(
            api_key=feed_key,
            api_secret=feed_secret,
            company_id=company_id,
            max_results=settings.max_results,
            start_base_overrides=(
                None
                if settings.pagination_start_base is None
                else dict.fromkeys(CLIENT_ROUTES, settings.pagination_start_base)
            ),
        )

    @server.tool(
        name=GET_JOB_FEED,
        output_schema=JobFeedResult.model_json_schema(mode="serialization"),
        annotations={"readOnlyHint": True},
    )
    async def get_job_feed(
        params: GetJobFeedInput,
        ctx: Context,
    ) -> ToolResult:
        """Read the public career-site job feed.

        Returns a single page of the v1 job feed, capped at the
        server's configured result limit and reporting
        `showing N of total` rather than truncating silently.
        """
        request_context = ctx.request_context
        meta = request_context.meta if request_context is not None else None
        with audit_scope(
            GET_JOB_FEED,
            transport,
            arguments=params.model_dump(mode="json"),
            meta=meta,
        ) as event:
            try:
                async with _client() as client:
                    # ONE PAGE, NOT A SCAN, AND THE CHOICE IS
                    # DELIBERATE. `client.scan()` exists and this tool
                    # does not call it: ADR-0024 records that a scan
                    # has no bound, and U8 measured that even a
                    # BOUNDED scan is unbounded against a server
                    # answering full pages of already-seen records. A
                    # single `request` incurs neither exposure - its
                    # worst case is one page - and the feed's first
                    # page is what a career-site reader wants. A
                    # paging caller is a later decision with an ADR
                    # behind it, not a default.
                    #
                    # `jobfeed=True` selects the v1 base AND the
                    # query-parameter credentials in one enumerated
                    # branch (`jobvite_client.py:request`). The
                    # sensitive-URL path is that branch and nothing
                    # else, which is what lets one test point at it.
                    payload = await client.request(
                        "GET",
                        JOBFEED_PATH,
                        params=_feed_params(params),
                        jobfeed=True,
                    )
                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"
                emit(event, AuditPhase.READ)
                problem = problem_from_exception(exc, event.request_id)
                return ToolResult(
                    structured_content=problem,
                    meta={REQUEST_ID_META_KEY: event.request_id},
                    is_error=True,
                )
            emit(event, AuditPhase.READ)
            return ToolResult(
                structured_content=result.model_dump(mode="json"),
                meta={REQUEST_ID_META_KEY: event.request_id},
            )
