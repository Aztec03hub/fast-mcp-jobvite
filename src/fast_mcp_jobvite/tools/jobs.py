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
(DESIGN.md:639-650). `_meta` is the protocol's own channel and the
result validator never inspects it, whereas an undeclared top-level
key in structured content is rejected outright.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Final

from fastmcp import Context, FastMCP
from fastmcp.tools.base import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from ..audit import (
    AuditPhase,
    Transport,
    audit_scope,
    emit,
)
from ..config import SEARCH_JOBS, Settings
from ..errors import problem_from_exception
from ..models.jobs import (
    JOBS_ENVELOPE_KEY,
    TOTAL_ENVELOPE_KEY,
    Job,
    JobLocation,
    JobSearchResult,
)
from ..services.jobvite_client import JobviteClient
from ..utils.constraints import JobviteIdentifier

#: The namespaced `_meta` key `request_id` travels to the caller under
#: (DESIGN.md:632-638). `io.modelcontextprotocol/*` is reserved, and
#: the spec's own `SERVER_INFO_META_KEY` is the precedent: server
#: stamped, and documented as display and debugging only, never
#: behaviour or security - which is exactly this value's class.
REQUEST_ID_META_KEY: Final = "com.evolvconsulting.fast-mcp-jobvite/requestId"

#: The v2 route this tool calls (DESIGN.md:137).
JOBS_PATH: Final = "/job"


class SearchJobsInput(BaseModel):
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
        return JobviteClient(
            api_key=api_key,
            api_secret=api_secret,
            company_id=settings.company_id,
            max_results=settings.max_results,
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
