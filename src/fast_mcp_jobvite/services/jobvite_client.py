"""The Jobvite client: auth and error detection (DESIGN.md:308-340).

**The load-bearing behaviour in this codebase is `evaluate_response`
below, and everything else in this module exists to feed it.**
DESIGN.md:332-333 states the invariant this module is built around:

    a response is successful only if the body carries no
    `status.code >= 400` **and** the HTTP status is below 400. Both,
    every call.

The trap it defends against is recorded, not hypothetical
(`JOBVITE-CONTRACT.md` §3.1): `api.jobvite.com` answers a rejected
credential with **HTTP 200** and a body of
`{"status":{"code":401,"messages":["Invalid api/secret..."]}}`. A client
branching on `response.status_code` reads that as success, looks for a
`candidates` key, does not find one, and reports **zero candidates for a
credential that was refused**. A wrong zero that explains itself is the
hardest kind to notice, which is why this is C5-S1, the only Critical on
the client.

**The two arms are written as two independent statements on purpose.**
Either one alone passes a plausible-looking test suite:

* Drop the envelope arm and the recorded 200-with-401-body fixture is
  reported as a success.
* Drop the HTTP arm and a transport-level failure carrying a body that
  has no `status` block at all is reported as a success.

`DESIGN.md:332-333` says *both, every call*, so both are here and each
has a case of its own that dies when it is removed.

**Decoding cannot assume JSON and cannot dispatch on content type
either** (DESIGN.md:335-337). Three error encodings are handled on the
routes we call - a JSON status envelope, plain text with **no
`Content-Type` header at all**, and a Tomcat HTML page.
`JOBVITE-CONTRACT.md` §3.3 records that the v1 `jobFeed` 401 sends no
`Content-Type`, which is what rules content-type sniffing out as the
dispatch.

**HR-XML is a hardened fallback, not a handled case**
(DESIGN.md:337-340). It appears on `/v1/candidate`, which we do not
call. If XML ever arrives it is parsed with `defusedxml` and treated as
an **error body** - never as a success - because entity expansion on
attacker-reachable input is not a risk worth taking for a route that
should never respond to us.

**Credentials.** v2 travels as the headers `x-jvi-api` and `x-jvi-sc`,
and **a URL containing a secret is never constructed**
(DESIGN.md:311-312), even though Jobvite's own published sample code
does exactly that. `GET /v1/jobFeed` is the one structural exception: it
requires `api`, `sc` and `companyId` as query parameters, so its URL is
classified sensitive and never reaches a log line whole. Redaction is
not reimplemented here - `utils/redaction.py` is the single enforcement
point DESIGN.md:312-316 requires, and this module calls it.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Final, NoReturn, Protocol, Self

import httpx2
from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring as defused_fromstring
from loguru import logger

from ..errors import JobviteUnavailableError, JobviteUpstreamError
from ..utils.redaction import redact_headers, redact_text, redact_url

# ----------------------------------------------------------------------
# Transport constants. `JOBVITE-CONTRACT.md` §2 records both base URLs
# as [RECORDED]; note the v1 base is `/v1`, NOT `/api/v1`.
# ----------------------------------------------------------------------
V2_BASE_URL: Final = "https://api.jobvite.com/api/v2"
V1_BASE_URL: Final = "https://api.jobvite.com/v1"

#: The v2 credential headers (DESIGN.md:311). `utils/redaction.py`
#: holds the same two names in `SECRET_HEADERS`; a test pins the two
#: lists together so a rename here cannot leave the redactor watching a
#: header that no longer exists.
API_KEY_HEADER: Final = "x-jvi-api"
# noqa on the next line: S105 flags the NAME of a header, not a
# credential. The value never appears in this file; it arrives as a
# SecretValue at construction.
API_SECRET_HEADER: Final = "x-jvi-sc"  # noqa: S105

#: The one route that structurally requires credentials in the query
#: string (DESIGN.md:313-316, `JOBVITE-CONTRACT.md` §2.1 rule 2).
JOBFEED_PATH: Final = "/jobFeed"

#: The threshold in `status.code >= 400` and `http_status < 400`
#: (DESIGN.md:332-333). Named rather than inlined twice, so the two arms
#: cannot drift apart under a later edit.
ERROR_STATUS_THRESHOLD: Final = 400

#: How much of an undecodable body may appear in an exception `detail`.
#: Jobvite's Tomcat HTML page is small, but nothing guarantees the next
#: one is, and this string reaches a log line. Truncation is a bound on
#: the blast radius, not a substitute for `redact_text`, which is
#: applied as well.
MAX_BODY_EXCERPT_CHARS: Final = 500

# ----------------------------------------------------------------------
# The `detail` a transport failure reaches the API consumer with.
# ENUMERATED, never formatted from the exception.
#
# `backend/error-handling.md` is `priority: required` and says at :383
# "Never leak raw exception messages from third-party libraries to API
# consumers" and at :493 "never pass `str(exc)` from third-party
# libraries". This module used to build `JobviteUnavailableError`'s
# detail as `redact_text(f"{type(exc).__name__}: {exc}")`, and that
# detail reaches the caller unchanged through `problem_from_exception`
# -> `build_problem`.
#
# **`redact_text` does not discharge the clause.** It bounds the
# credential classes it knows about - `api`, `sc`, `companyId`, userinfo
# passwords. An httpx2 exception string also carries `_ssl.c` line
# numbers, local socket paths and resolver detail, none of which are
# credential-shaped and all of which are third-party internals arriving
# at a consumer.
#
# **What the design actually requires is preserved**: DESIGN.md:356-360
# says an open breaker and an outage share
# `/problems/service-unavailable` 503 and "what distinguishes them is
# `detail`, which says whether Jobvite failed or whether we have stopped
# calling it". Three stable strings say exactly that, and a caller can
# still branch on them. The breaker's own counterpart string is U7's to
# add when the breaker exists; writing it here would be a constant with
# no producer.
#
# The exception text itself is not lost - it goes to the log line below,
# which is its correct destination.
# ----------------------------------------------------------------------
UNAVAILABLE_TIMEOUT_DETAIL: Final = (
    "Jobvite did not respond before the configured timeout elapsed. "
    "This is an upstream failure, not an open circuit breaker."
)
UNAVAILABLE_TRANSPORT_DETAIL: Final = (
    "Jobvite could not be reached. "
    "This is an upstream failure, not an open circuit breaker."
)
UNAVAILABLE_REQUEST_DETAIL: Final = (
    "The request to Jobvite could not be issued. "
    "This is a client-side transport failure, not an open circuit breaker."
)


def _unavailable_detail(exc: Exception) -> str:
    """Map a transport exception onto its enumerated `detail`.

    Dispatch is on the exception CLASS and the return values are
    constants, so nothing a third-party library wrote into the
    exception's text can reach the value this returns. That is the
    property `error-handling.md:383` and `:493` ask for, and it is a
    property of the function rather than of a redactor applied
    afterwards.

    Args:
        exc: The transport exception caught around the request.

    Returns:
        One of the three module-level `UNAVAILABLE_*_DETAIL` constants.
    """
    if isinstance(exc, httpx2.TimeoutException):
        return UNAVAILABLE_TIMEOUT_DETAIL
    if isinstance(exc, httpx2.TransportError):
        # Every network-layer failure httpx2 raises: connect, read,
        # write, pool, protocol and proxy errors all subclass this.
        return UNAVAILABLE_TRANSPORT_DETAIL
    # `InvalidURL`, `CookieConflict` and `StreamError` sit outside the
    # `HTTPError` hierarchy entirely - see the `except` clause below.
    # Jobvite was never called on this path, so saying "could not be
    # reached" would be a false statement about the upstream service.
    return UNAVAILABLE_REQUEST_DETAIL


class SecretValue(Protocol):
    """The one method this module needs from a secret holder.

    **Structural rather than nominal, and that is deliberate.**
    DESIGN.md:323-324 requires credentials to be `SecretStr` throughout,
    resolved with `.get_secret_value()` only when building a request -
    and `SecretStr` is pydantic's. `pydantic` is present in the resolve
    only as a transitive of `fastmcp`, and U4's dependency slot is
    granted for `httpx2` and `defusedxml` and nothing else, so importing
    it here would either add an undeclared direct import or spend a slot
    that was not granted.

    A `Protocol` satisfies the design's actual requirement - the value
    is opaque until something deliberately unwraps it - and pydantic's
    `SecretStr` satisfies this Protocol structurally, so U1's
    configuration can hand one straight in with no adapter. See
    U4-IMPL-REPORT.md.
    """

    def get_secret_value(self) -> str:
        """Return the wrapped secret."""
        ...


# ======================================================================
# THE INVARIANT (DESIGN.md:332-333). Everything below this block is
# plumbing.
# ======================================================================


def evaluate_response(http_status: int, body: bytes) -> dict[str, Any]:
    """Apply the error-detection rule to one response, and decode it.

    **The invariant (DESIGN.md:332-333): a response is successful only
    if the body carries no `status.code >= 400` AND the HTTP status is
    below 400. Both, every call.**

    Args:
        http_status: The HTTP status line's code. **Not authoritative on
            its own** - see the module docstring and
            `JOBVITE-CONTRACT.md` §3.1.
        body: The raw response bytes. Raw rather than a parsed object,
            because the decision of whether this is even JSON is part of
            the rule.

    Returns:
        The decoded JSON body, when and only when both arms of the
        invariant hold.

    Raises:
        JobviteUpstreamError: On either arm of the invariant failing,
            and on a body that cannot be decoded as a JSON object at all
            - which includes the plain-text, HTML and XML encodings, all
            of which are errors.
    """
    payload = _decode_json_object(http_status, body)

    # ARM 1 - the body's own status envelope. This is the arm the
    # recorded 200-with-401-body fixture exercises, and the reason the
    # HTTP status is not consulted first: at that point the HTTP status
    # is 200 and says nothing.
    envelope_code = _envelope_status_code(payload)
    if envelope_code is not None and envelope_code >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(envelope_code, _envelope_message(payload))

    # ARM 2 - the HTTP status, applied INDEPENDENTLY rather than as an
    # `elif`. A body with no `status` block at all, or with a code under
    # 400, arriving on a 5xx must still fail. `JOBVITE-CONTRACT.md` §3.2
    # records that a status block with a code under 400 has never been
    # observed, so this arm is what covers the shape we cannot rule out.
    if http_status >= ERROR_STATUS_THRESHOLD:
        raise JobviteUpstreamError(http_status, _envelope_message(payload))

    return payload


def _envelope_status_code(payload: Mapping[str, Any]) -> int | None:
    """Return `status.code` if the body carries one, else `None`.

    `None` and a code under 400 are different answers and are kept
    apart: `JOBVITE-CONTRACT.md` §3.2 records that no success body has
    ever been observed, so whether a success carries a `status` block at
    all is unknown (checklist row §13.1). Both are tolerated, and
    neither is treated as an error by this function.
    """
    status = payload.get("status")
    if not isinstance(status, Mapping):
        return None
    code = status.get("code")
    # `bool` is an `int` in Python, and `{"code": true}` is not a status
    # code.
    if isinstance(code, bool) or not isinstance(code, int):
        return None
    return code


def _envelope_message(payload: Mapping[str, Any]) -> str:
    """Join Jobvite's own `status.messages` into one line for `detail`.

    Jobvite's message is preserved rather than discarded -
    DESIGN.md:532-534 puts it in `detail` - but it never reaches the
    problem object's `status`, which comes from the registry
    (`errors.py`).
    """
    status = payload.get("status")
    if not isinstance(status, Mapping):
        return "no message"
    messages = status.get("messages")
    if isinstance(messages, str):
        return redact_text(messages)
    if isinstance(messages, list) and messages:
        return redact_text("; ".join(str(m) for m in messages))
    return "no message"


def _decode_json_object(http_status: int, body: bytes) -> dict[str, Any]:
    """Decode the body as a JSON object, or raise the right typed error.

    **This is the "cannot assume JSON, cannot dispatch on content type"
    half** (DESIGN.md:335-337). Dispatch is on the bytes themselves,
    because the v1 `jobFeed` 401 sends no `Content-Type` header at all
    (`JOBVITE-CONTRACT.md` §3.3), so a content-type dispatch has nothing
    to read on exactly the route that needs it most.

    Every non-JSON encoding is an ERROR. That is not an assumption: v2
    speaks JSON on success, so plain text, HTML and XML are all failure
    shapes, and the two synthetic malformed fixtures must fail loudly
    here rather than degrade to an empty result.
    """
    text = body.decode("utf-8", errors="replace").strip()

    if text.startswith("<"):
        # Markup: the Tomcat HTML page, or HR-XML. Neither is ever a
        # success.
        _raise_from_markup(http_status, text)

    try:
        payload = json.loads(text)
    except ValueError:
        # Plain text with no Content-Type - the recorded v1 `jobFeed`
        # 401 - and the synthetic malformed bodies. FAIL LOUDLY:
        # returning `{}` here is precisely the "wrong zero" this module
        # exists to prevent.
        raise JobviteUpstreamError(
            _upstream_status_or_none(http_status), _excerpt(text)
        ) from None

    if not isinstance(payload, dict):
        # Valid JSON that is not an object: `null`, a bare list, a
        # number. No Jobvite route is documented to return one, and
        # `payload["status"]` would raise a TypeError several frames
        # away from the cause.
        raise JobviteUpstreamError(
            _upstream_status_or_none(http_status),
            f"expected a JSON object, got {type(payload).__name__}",
        )

    return payload


def _raise_from_markup(http_status: int, text: str) -> NoReturn:
    """Treat any markup body as an error, parsing XML with `defusedxml`.

    **HR-XML is a hardened fallback, not a handled case**
    (DESIGN.md:337-340). It appears on `/v1/candidate`, which we do not
    call. So this function's job is not to support XML - it is to make
    sure that if XML ever does arrive, the parse that touches it cannot
    be turned into a denial of service by entity expansion, and that
    whatever comes out is reported as a failure.

    `defusedxml` raising is a SUCCESSFUL outcome for us: it means the
    document carried a DTD, an external entity or an entity bomb, and we
    declined to expand it. Either way the caller gets a
    `JobviteUpstreamError`; the only difference is how much detail we
    can honestly put in it.
    """
    detail = _excerpt(text)
    try:
        root = defused_fromstring(text)
    except (DefusedXmlException, SyntaxError):
        # Not well-formed XML (the Tomcat HTML page), or defused_etree
        # refused it (a DTD or an entity bomb). Both are errors and
        # neither is parsed further. The body excerpt is redacted and
        # truncated, never trusted.
        raise JobviteUpstreamError(
            _upstream_status_or_none(http_status), detail
        ) from None

    # Well-formed XML. Pull the HR-XML `<Error code="N">` shape if it is
    # there; anything else still ends as an error, just with a vaguer
    # detail.
    error = root.find(".//Error")
    if error is not None:
        code = error.get("code")
        message = (error.text or "").strip() or detail
        raise JobviteUpstreamError(
            int(code) if code is not None and code.isdigit() else None,
            redact_text(message),
        )
    raise JobviteUpstreamError(_upstream_status_or_none(http_status), detail)


def _upstream_status_or_none(http_status: int) -> int | None:
    """Report the HTTP status only when it actually indicates a failure.

    `JobviteUpstreamError(None, ...)` renders as "Jobvite returned
    status none", which is the honest thing to say about a body that
    failed to decode on an HTTP 200: Jobvite reported no failing status
    anywhere, and claiming it returned 200 as though 200 were the error
    would invert the meaning of the field.
    """
    return http_status if http_status >= ERROR_STATUS_THRESHOLD else None


def _excerpt(text: str) -> str:
    """Bound and redact a body before it reaches a message or log.

    Both halves matter. `redact_text` is `utils/redaction.py`'s
    exception-message arm (DESIGN.md:314-315): an error body can quote
    back the request URL, and on the `jobFeed` route that URL carries
    `sc=`. Truncation bounds a body we do not control.
    """
    redacted = redact_text(text)
    if len(redacted) <= MAX_BODY_EXCERPT_CHARS:
        return redacted
    return redacted[:MAX_BODY_EXCERPT_CHARS] + "... [truncated]"


# ======================================================================
# The client. One request entry point, feeding the invariant above.
# ======================================================================


class JobviteClient:
    """An `httpx2` client for Jobvite, with one request entry point.

    **`request` is the single method that issues one call, applies the
    invariant and returns a decoded body or raises the typed error**
    (`IMPLEMENTATION-PLAN.md:773-777`). Paging around it is U6's; U4
    owns the one-call path. Without this method U4 would be an
    auth-and-error module with no caller.

    ADR-0007 chose `httpx2`: `fastmcp 4.0.0b4` does not install `httpx`
    at all, and `httpx2` ships `MockTransport` in the box, which is what
    lets the credential-free test strategy add no third-party mocking
    library.
    """

    def __init__(
        self,
        *,
        api_key: SecretValue,
        api_secret: SecretValue,
        company_id: SecretValue | None = None,
        transport: httpx2.AsyncBaseTransport | None = None,
        timeout: httpx2.Timeout | None = None,
    ) -> None:
        """Build the client.

        Args:
            api_key: The v2 `x-jvi-api` credential, and the v1 `api`
                parameter.
            api_secret: The v2 `x-jvi-sc` credential, and the v1 `sc`
                parameter.
            company_id: The job feed's separate credential
                (DESIGN.md:320-321). Required only for `jobFeed`, so it
                is optional here and the failure for a missing one is
                raised at the call.
            transport: Substituted in tests with `httpx2.MockTransport`
                (DESIGN.md:1359-1360, ADR-0007). `None` in production.
            timeout: Explicit and per-phase (DESIGN.md:346). **No SDK
                default and no single scalar**: `httpx2`'s own default
                is a 5-second scalar, which is a resilience decision
                made by a library rather than by us. The full
                retry/breaker ordering of DESIGN.md:342-358 is U7's;
                this is the timeout half, which cannot wait for it
                because the default it would otherwise inherit is
                silent.
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._company_id = company_id
        self._client = httpx2.AsyncClient(
            transport=transport,
            timeout=timeout
            or httpx2.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
            # PINNED, not inherited. httpx2 2.12.0 happens to default
            # this False, so before this line the safety came from a
            # transitive default and nothing else - a review added
            # `follow_redirects=True` and all 294 tests stayed green.
            #
            # A 30x would forward `x-jvi-api` and `x-jvi-sc` to whatever
            # host the `Location` header names, and on the v1 jobFeed
            # route the credentials travel in the QUERY STRING, so a
            # redirect would hand them to a third party in a URL that
            # also lands in that host's access log.
            #
            # server.py states this project's own rule for exactly this
            # class: "a security-relevant default is exactly the kind of
            # thing that must be stated in our own source so a diff
            # shows it moving". It was applied to `mask_error_details`
            # and not here.
            follow_redirects=False,
        )

    async def __aenter__(self) -> Self:
        """Enter the client's context, closing the pool on exit."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the underlying transport."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying `httpx2` client."""
        await self._client.aclose()

    # -- authentication
    # -----------------------------------------------------

    def v2_headers(self) -> dict[str, str]:
        """Build the v2 request headers (DESIGN.md:311).

        `.get_secret_value()` is called **here and only here** for v2,
        which is DESIGN.md:323-324's "resolved only when building a
        request".

        Returns:
            The two credential headers plus `Accept`.
        """
        return {
            API_KEY_HEADER: self._api_key.get_secret_value(),
            API_SECRET_HEADER: self._api_secret.get_secret_value(),
            "Accept": "application/json",
        }

    def jobfeed_params(self) -> dict[str, str]:
        """Build the v1 `jobFeed` params - **the one exception**.

        DESIGN.md:313-316: this route structurally requires `api`, `sc`
        and `companyId` as query parameters, which is why its URL is
        classified sensitive. Every other route puts the credential in a
        header and DESIGN.md:311-312 forbids building a URL that
        contains one.

        Returns:
            The three credential parameters.

        Raises:
            JobviteUpstreamError: If no `company_id` was configured.
                Raised rather than sending the call without it, because
                Jobvite would answer a missing `companyId` with the same
                401 body as a bad credential and the operator would go
                looking for the wrong fault.
        """
        if self._company_id is None:
            raise JobviteUpstreamError(
                None,
                "the jobFeed route requires a companyId credential and none is "
                "configured",
            )
        return {
            "api": self._api_key.get_secret_value(),
            "sc": self._api_secret.get_secret_value(),
            "companyId": self._company_id.get_secret_value(),
        }

    # -- the one request entry point
    # ---------------------------------------

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json_body: Mapping[str, Any] | None = None,
        jobfeed: bool = False,
    ) -> dict[str, Any]:
        """Issue ONE call, apply the invariant, return the body.

        **The single request entry point.** One call, no paging - paging
        around this method is U6's (`IMPLEMENTATION-PLAN.md:775`).

        Args:
            method: The HTTP method.
            path: The path below the base URL, e.g. `/candidate`.
            params: Non-credential query parameters.
            json_body: A JSON request body, for POST routes.
            jobfeed: Select the v1 `jobFeed` route and its
                query-parameter authentication. **A `bool` rather than a
                free-form base URL**: the sensitive-URL path has to be
                one enumerated branch that a test can point at, not a
                value a caller can pass in.

        Returns:
            The decoded body, when both arms of the invariant hold.

        Raises:
            JobviteUpstreamError: On either arm of the invariant, or an
                undecodable body.
            JobviteUnavailableError: If Jobvite could not be reached at
                all.
        """
        if jobfeed:
            url = f"{V1_BASE_URL}{path}"
            headers = {"Accept": "application/json"}
            query = {**dict(params or {}), **self.jobfeed_params()}
        else:
            url = f"{V2_BASE_URL}{path}"
            headers = self.v2_headers()
            query = dict(params or {})

        # The ONLY log line on this path, and it names the route rather
        # than the URL. DESIGN.md:313-316 forbids the jobFeed URL
        # reaching a log whole, and `redact_url` is applied on top
        # rather than instead: the path is already credential-free for
        # v2, so this is belt and braces on the one route where a
        # mistake is unrecoverable.
        logger.debug(
            "jobvite request",
            method=method,
            route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
        )

        try:
            response = await self._client.request(
                method,
                url,
                params=query,
                headers=headers,
                json=dict(json_body) if json_body is not None else None,
            )
        except (
            httpx2.HTTPError,
            # NOT SUBCLASSES OF HTTPError, measured at httpx2 2.12.0
            # rather than assumed: `InvalidURL`, `CookieConflict` and
            # `StreamError` sit outside that hierarchy entirely.
            # `except httpx2.HTTPError` reads like "any transport
            # failure" and is not.
            #
            # An InvalidURL is reachable the moment a later unit
            # interpolates a `path` - U5 and U12 both do - and it would
            # escape this block WITHOUT passing through `redact_text`
            # and without becoming a typed error, so the module's own
            # documented contract ("Raises: JobviteUnavailableError: If
            # Jobvite could not be reached at all") would be false.
            # errors.py contains it at the boundary today, so there is
            # no leak; the defect is the contract, not a live escape.
            httpx2.InvalidURL,
            httpx2.CookieConflict,
            httpx2.StreamError,
        ) as exc:
            # THE LOG IS WHERE THE EXCEPTION TEXT GOES, and the consumer
            # gets an enumerated reason instead
            # (`error-handling.md:383`, `:493`, and the block above
            # `_unavailable_detail`). "Log errors with sufficient
            # context server-side" is the same standard's :494.
            #
            # `httpx` puts the request URL into the text of the
            # exceptions it raises, so on the jobFeed route `str(exc)`
            # carries `sc=`. `redact_text` is the arm of
            # utils/redaction.py that exists for exactly this
            # (DESIGN.md:314-315); without it a timeout on the feed
            # publishes the credential into whatever formats the
            # exception.
            #
            # `redact_headers` is applied because on the v2 branch
            # `headers` IS `v2_headers()` - the resolved `x-jvi-api` and
            # `x-jvi-sc` values, in the clear, in a local variable
            # (DESIGN.md:311). This is the call site that function was
            # written for; before this line it had none, and a header
            # dict was one `logger.debug(headers=headers)` away from the
            # log stream with nothing to stop it.
            #
            # The exception is passed as REDACTED TEXT, not as an
            # exception object: `logger.exception` would put it in
            # `record["exception"]`, which the sink's filter does not
            # reach - see `__main__.py`.
            logger.warning(
                "jobvite transport failure",
                method=method,
                route=redact_url(f"{V1_BASE_URL if jobfeed else V2_BASE_URL}{path}"),
                headers=redact_headers(headers),
                error=redact_text(f"{type(exc).__name__}: {exc}"),
            )
            raise JobviteUnavailableError(_unavailable_detail(exc)) from None
        finally:
            # NO COOKIE JAR (`JOBVITE-CONTRACT.md` §2.3). Jobvite sets
            # four `AWSALBAPP-*` cookies whose values are all the
            # literal string `_remove_`, and the API is
            # credential-authenticated per request: there is no session
            # to carry.
            #
            # **This is not httpx2's default and was measured, not
            # assumed.** A bare `AsyncClient` stores those cookies and
            # sends them back on the next request; the probe that
            # established it is reproduced as a test. Clearing in
            # `finally` rather than after a success means a call that
            # raised cannot leave a jar behind either.
            self._client.cookies.clear()

        return evaluate_response(response.status_code, response.content)
