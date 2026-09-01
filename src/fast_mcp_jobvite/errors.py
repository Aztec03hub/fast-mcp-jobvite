"""The exception hierarchy and RFC 9457 problems (DESIGN.md:542-600).

Two rules govern everything in this module, and both were corrections to
an earlier revision of the design rather than defaults:

**`type` and `status` come from the registry at
`error-contract.md:96-108`, never from Jobvite** (DESIGN.md:553-594). A
Jobvite `401` reaching the caller as `401` tells them *their* credential
failed, when the credential that failed is the one *this server* holds
and the caller cannot touch. The registry's answer is
`/problems/external-service-error` **502**. Validation is **422**, not
400. Jobvite's own status and message are not discarded: they go in
`detail`.

**Problem objects are returned, never raised** (DESIGN.md:596-600). That
is the property that makes them the one error shape no configuration can
distort - being returned, they are untouched by
`ErrorHandlingMiddleware`, by `transform_errors` and by
`mask_error_details`. Nothing in this module raises a problem object.

The exception classes below are the *internal* signalling hierarchy: the
client and the tool bodies raise them, and the tool boundary converts
one into a problem object with `problem_from_exception` and returns it.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Final

INSTANCE_PREFIX: Final = "urn:fast-mcp-jobvite:invocation:"

#: The seven members `error-contract.md:66` elevates to required, in
#: the order the design lists them (DESIGN.md:546-547).
REQUIRED_MEMBERS: Final[tuple[str, ...]] = (
    "type",
    "title",
    "status",
    "detail",
    "instance",
    "request_id",
    "timestamp",
)


@dataclass(frozen=True)
class ProblemKind:
    """One row of the registry at `error-contract.md:96-108`.

    Attributes:
        type: The relative `/problems/<slug>` URI, or `about:blank` for
            an unmapped HTTP status received from Jobvite (ADR-0017).
        title: The registry's title. Stable per `type`, never
            per-instance (`error-contract.md:73`).
        status: The registry's status. Never Jobvite's.
    """

    type: str
    title: str
    status: int


# ----------------------------------------------------------------------
# The registry. Every entry is a verbatim row of
# `error-contract.md:96-108`; nothing here is minted locally.
# DESIGN.md:561-562 makes a published `type` URI a contract we would owe
# forever, so inventing a slug is not available to us even when the
# condition feels unlike anything in the table.
# ----------------------------------------------------------------------
EXTERNAL_SERVICE_ERROR: Final = ProblemKind(
    "/problems/external-service-error", "External Service Error", 502
)
SERVICE_UNAVAILABLE: Final = ProblemKind(
    "/problems/service-unavailable", "Service Unavailable", 503
)
VALIDATION_ERROR: Final = ProblemKind(
    "/problems/validation-error", "Validation Error", 422
)
RESOURCE_NOT_FOUND: Final = ProblemKind(
    "/problems/resource-not-found", "Resource Not Found", 404
)
#: This module's own claim to a coverage role from DESIGN.md:1443-1445,
#: read by `docs/reviews/check-coverage-floors.py`. The design names the
#: roles and not the paths, and the claim lives HERE rather than in a
#: role-to-module map in the checker, which would be a hand-kept list
#: beside its container. The checker asserts the two sets are EQUAL.
COVERAGE_ROLE: Final = "the error rule"

CONFLICT: Final = ProblemKind("/problems/conflict", "Conflict", 409)
FORBIDDEN: Final = ProblemKind("/problems/forbidden", "Forbidden", 403)
INTERNAL_ERROR: Final = ProblemKind(
    "/problems/internal-error", "Internal Server Error", 500
)

#: `error-contract.md:115` and RFC 9457 4.2.1: the fallback for an
#: unmapped **HTTP status received from Jobvite**, and for nothing
#: else. ADR-0017 settled this: U2 read the design's table (then
#: `DESIGN.md:566`) as routing an unhandled exception in our own tool
#: body here, and that reading is replaced - the registry already names
#: that condition `/problems/internal-error`, which is what
#: `problem_from_exception` now returns.
#:
#: **No code path reaches this today**, and it stays anyway: SS5.1's
#: registry maps every status this client is known to receive, so the
#: fallback may be unreachable in practice, and an unreachable fallback
#: that is correct beats a reachable one that is wrong (ADR-0017).
#: Establishing reachability needs the live-tenant observations the
#: credential checklist gates.
UNMAPPED: Final = ProblemKind("about:blank", "Internal Server Error", 500)


class FastMcpJobviteError(Exception):
    """Base of the internal exception hierarchy.

    Carries the registry row its condition maps to, so the mapping is
    decided at the point the condition is *known* rather than re-derived
    from a status code at the boundary, which is how Jobvite's status
    leaked into `status` in the revision DESIGN.md:553-560 corrects.
    """

    kind: ProblemKind = INTERNAL_ERROR

    def __init__(self, detail: str) -> None:
        """Store the occurrence-specific explanation.

        Args:
            detail: Human-readable explanation specific to this
                occurrence (`error-contract.md:75`).
        """
        super().__init__(detail)
        self.detail = detail


class JobviteUpstreamError(FastMcpJobviteError):
    """Any Jobvite failure, **including its 4xx** (DESIGN.md:566).

    Jobvite's own status and message are preserved on the instance and
    reproduced in `detail` (DESIGN.md:592-594). They are never allowed
    to reach `status`.

    **`retry_after` carries a `Retry-After` JOBVITE SENT, and nothing
    else** (ADR-0030, DESIGN.md:376-382). A 5xx arriving with a hint we
    cannot afford inside the outbound budget stops the retry loop -
    correctly - and used to surface as a bare 502, telling the caller
    *"Jobvite failed"* when we had been told *"Jobvite failed, and it
    will keep failing for fifteen minutes"*. That is strictly less than
    we knew.

    **It is NEVER computed.** ADR-0030 is explicit: a synthesised hint
    on a 502 would be this server inventing a prediction and dressing
    it as the upstream's, which is worse than the omission it fixes.
    The open breaker's hint is different in kind - it is computed from
    our own remaining window, and is ours to compute precisely because
    it describes our own state.
    """

    kind = EXTERNAL_SERVICE_ERROR

    def __init__(
        self,
        upstream_status: int | None,
        upstream_message: str,
        retry_after: float | None = None,
    ) -> None:
        """Record what Jobvite said, and build a `detail` that keeps it.

        Args:
            upstream_status: The status Jobvite reported - the HTTP
                status or the `status.code` of its JSON envelope
                (DESIGN.md:344-345). `None` when Jobvite gave no status
                at all.
            upstream_message: Jobvite's own message text.
            retry_after: Seconds, parsed from a `Retry-After` Jobvite
                actually sent. `None` means we were not told - never
                *do not retry*, and never a number of our own.
        """
        shown = "none" if upstream_status is None else str(upstream_status)
        super().__init__(f"Jobvite returned status {shown}: {upstream_message}")
        self.upstream_status = upstream_status
        self.upstream_message = upstream_message
        self.retry_after = retry_after


class JobviteUnavailableError(FastMcpJobviteError):
    """Jobvite unreachable, breaker open, or budget exhausted.

    An open breaker and a real outage share this row deliberately
    (DESIGN.md:367-370): what distinguishes them is `detail`, not a
    minted type.
    """

    kind = SERVICE_UNAVAILABLE


class ValidationError(FastMcpJobviteError):
    """A validation failure detected **inside** the tool body.

    Not the pre-dispatch path. DESIGN.md:608-628 records that FastMCP
    rejects bad arguments before the body runs, so no pre-dispatch
    rejection can *return* anything and none carries a problem object.
    This row serves the other half: a semantically invalid argument
    combination, or a validation error Jobvite itself returns.
    """

    kind = VALIDATION_ERROR


class ResourceNotFoundError(FastMcpJobviteError):
    """A candidate or job id that does not exist (DESIGN.md:569)."""

    kind = RESOURCE_NOT_FOUND


class DuplicateCandidateError(FastMcpJobviteError):
    """Duplicate candidate on create.

    DESIGN.md:570 and DESIGN.md:1469-1474. The second half was `877`,
    which is 511 lines away in §7.2 and about the idempotency
    dismissal rather than the 409 shape.
    """

    kind = CONFLICT


class ScopeDeniedError(FastMcpJobviteError):
    """The caller's token lacks this tool's scope (DESIGN.md:571)."""

    kind = FORBIDDEN


class ApprovalRefusedError(FastMcpJobviteError):
    """The host returned no approval for `create_candidate`.

    **NO NEW SLUG IS MINTED HERE, and that is the decision.**
    `DESIGN.md:561-562` makes a published `type` URI a promise this
    project owes forever, and `/problems/internal-error` is the
    alternative the "anything unmapped" row would otherwise select -
    which would tell a caller this server is broken when a refusal is
    the control working exactly as designed.

    **U10 reported this as a GAP in the registry, and ADR-0031 closed
    it.** The registry at `DESIGN.md:564-573` now carries its own row -
    *"An approval was required and none was returned"* -> 403 - so
    `/problems/forbidden` names two conditions under one slug and
    `detail` carries the distinction the slug cannot. Reusing
    `FORBIDDEN` is no longer a widening of the scope row past the
    *"caller's token lacks the scope"* condition its table names; it is
    the row the registry now has for this.

    It never names a person: the refusal is *no approval response from
    the host*, and C4-S1 means an approval that DID arrive would not
    have named one either (ADR-0009).
    """

    kind = FORBIDDEN


def _timestamp() -> str:
    """Return an ISO 8601 UTC timestamp with the `Z` suffix.

    `error-contract.md:85` requires ISO 8601 UTC and its example
    (`error-contract.md:62`) ends in `Z`, which `datetime.isoformat`
    renders as `+00:00`.
    """
    now = _dt.datetime.now(tz=_dt.UTC)
    return now.isoformat().replace("+00:00", "Z")


def build_problem(
    kind: ProblemKind,
    detail: str,
    request_id: str,
    **extensions: object,
) -> dict[str, Any]:
    """Build a complete RFC 9457 problem - **returned, never raised**.

    `request_id` is required rather than read from `request_id_var`. The
    var is a correlation carrier for code that never sees the invocation
    (DESIGN.md:661-666); reading it here would let a caller that forgot
    to set it produce a problem object with `None` where a required
    member belongs.

    Args:
        kind: The registry row. Never derived from an upstream status.
        detail: The occurrence-specific explanation.
        request_id: The UUIDv4 minted by `audit.py` for this invocation
            (DESIGN.md:655-657).
        **extensions: RFC 9457 extension members, e.g. the `retry_after`
            hint DESIGN.md:370 attaches to a 503, or `errors` for a 422
            (`error-contract.md:86`). They may not shadow a required
            member.

    Returns:
        The problem object: the seven required members plus any
        extensions.

    Raises:
        ValueError: If an extension would shadow one of the seven
            required members. That is a programming error at the call
            site, not a runtime condition, and silently letting it
            overwrite `status` is the exact failure DESIGN.md:553
            corrects.
    """
    clashes = sorted(set(extensions) & set(REQUIRED_MEMBERS))
    if clashes:
        msg = f"extension members may not shadow required members: {clashes}"
        raise ValueError(msg)
    problem: dict[str, Any] = {
        "type": kind.type,
        "title": kind.title,
        "status": kind.status,
        "detail": detail,
        "instance": f"{INSTANCE_PREFIX}{request_id}",
        "request_id": request_id,
        "timestamp": _timestamp(),
    }
    problem.update(extensions)
    return problem


def problem_from_exception(
    exc: BaseException,
    request_id: str,
    **extensions: object,
) -> dict[str, Any]:
    """Convert an exception to a problem - **returned, never raised**.

    An exception outside this module's hierarchy is
    `/problems/internal-error`, 500 (DESIGN.md:573, ADR-0017): it is a
    bug in our own code, the registry names it, and `about:blank` is RFC
    9457's way of saying *no additional semantics* when we have
    semantics. Its `detail` names the exception class rather than its
    message: an arbitrary exception's `str()` can carry a URL, a
    credential fragment or an upstream body, and this value reaches the
    caller.

    **A `retry_after` an exception is CARRYING is attached here, and
    that is why it is here rather than at the six call sites**
    (ADR-0030, R11-H1). DESIGN.md:376-382 says a hint the upstream
    volunteered *"is passed on, on whatever problem shape results"*,
    and DESIGN.md:368-370 says the open breaker's 503 carries one.
    Neither reached a caller: every call site is
    `problem_from_exception(exc, event.request_id)` with no extensions,
    and the only code that passed the member was the tests, which
    handed themselves the value they then asserted. Attaching it at the
    six sites would have been six chances to forget, and the seventh
    site would have been written without it.

    **An explicit `extensions` entry WINS over the carried one.** The
    caller is stating something about this occurrence and the exception
    is stating something about itself; the more specific wins, and
    `{"retry_after": hint, **extensions}` is that order.

    Args:
        exc: The exception to convert.
        request_id: The UUIDv4 minted by `audit.py` for this invocation.
        **extensions: RFC 9457 extension members. An explicit
            `retry_after` here overrides one carried by `exc`.

    Returns:
        The problem object.
    """
    if isinstance(exc, FastMcpJobviteError):
        hint = getattr(exc, "retry_after", None)
        if hint is not None:
            extensions = {"retry_after": hint, **extensions}
        return build_problem(exc.kind, exc.detail, request_id, **extensions)
    return build_problem(
        INTERNAL_ERROR,
        f"An unexpected {type(exc).__name__} occurred.",
        request_id,
        **extensions,
    )
