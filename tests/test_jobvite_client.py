"""DESIGN.md §8 case #1 and U4's contract (DESIGN.md:308-352).

**Every assertion here is on BEHAVIOUR, not on source text.** U3's
amputation harness found a test that still passed with the behaviour
deleted, because it searched the module's own file for a string that the
module's docstring quoted - it was asserting that the documentation
existed. Where this suite has to inspect the source at all it walks the
AST (`test_no_module_grep_...` below is the one place, and it is
checking for the *absence* of a construct, not for prose).

**A suite passing only against synthetic fixtures proves the client is
self-consistent, not that it speaks Jobvite** (DESIGN.md:1319-1321). The
five recorded fixtures are the ground truth and are asserted byte-exact.
The two malformed fixtures are INVENTED (`JOBVITE-CONTRACT.md` §1), so
they are asserted to fail loudly and are given no ground-truth weight:
their bytes are not pinned.

Transport substitution is `httpx2`'s built-in `MockTransport`
(DESIGN.md:1420-1421, ADR-0007). No third-party mocking library is used.
"""

from __future__ import annotations

import ast
import json
import pathlib
from collections.abc import Callable
from typing import Any

import httpx2
import pytest
from loguru import logger

from fast_mcp_jobvite.errors import (
    EXTERNAL_SERVICE_ERROR,
    RESOURCE_NOT_FOUND,
    JobviteUnavailableError,
    JobviteUpstreamError,
    problem_from_exception,
)
from fast_mcp_jobvite.services import jobvite_client as jc
from fast_mcp_jobvite.utils.redaction import REDACTED, SECRET_HEADERS

from .conftest import FIXTURES_DIR

#: A fixed UUIDv4 for the one case that builds a problem object here.
_L4_REQUEST_ID = "44444444-4444-4444-8444-444444444444"

API_KEY = "TESTKEY-not-a-real-credential"
API_SECRET = "TESTSECRET-not-a-real-credential"  # noqa: S105 - a test literal
COMPANY_ID = "TESTCOMPANY"


class _Secret:
    """A minimal `SecretValue`, so the suite needs no pydantic import.

    Mirrors `pydantic.SecretStr`'s one relevant method.
    `fakes must mirror real types`: the production type U1 will pass in
    is `SecretStr`, and this satisfies the same `Protocol` the client
    declares, so a client change that broke `SecretStr` compatibility
    would break this too.
    """

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


def read_fixture(name: str) -> bytes:
    """Read a fixture as RAW BYTES from `docs/research/fixtures`.

    Bytes, not text: "byte-exact" is the claim, and `read_text` would
    normalise a line ending on some platforms and quietly make the claim
    false.
    """
    return (FIXTURES_DIR / name).read_bytes()


def client(
    handler: Any,
    *,
    with_company_id: bool = True,
) -> jc.JobviteClient:
    """Build a client on `httpx2.MockTransport` (ADR-0007)."""
    return jc.JobviteClient(
        api_key=_Secret(API_KEY),
        api_secret=_Secret(API_SECRET),
        company_id=_Secret(COMPANY_ID) if with_company_id else None,
        transport=httpx2.MockTransport(handler),
    )


def responder(
    status: int, body: bytes, headers: list[tuple[str, str]] | None = None
) -> Callable[[httpx2.Request], httpx2.Response]:
    """Return a MockTransport handler serving exactly these bytes."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status, content=body, headers=headers or [])

    return handler


# ======================================================================
# §8 #1 - THE 200-WITH-401-BODY TRAP. C5-S1, the only Critical on the
# client.
# ======================================================================


def test_the_recorded_200_with_401_body_fixture_is_byte_exact() -> None:
    """Pin the ground truth before asserting behaviour on it.

    `error_auth_200_body401.json` is a [RECORDED] capture. If someone
    regenerates or "tidies" it, the case below would still pass against
    the tidied bytes while no longer testing the transport Jobvite
    actually emits.
    """
    assert read_fixture("error_auth_200_body401.json") == (
        b'{"status":{"code":401,"messages":["Invalid api/secret. Try again with '
        b'a valid api/secret"]}}\n'
    )


async def test_C5_S1_an_http_200_carrying_a_401_body_is_NOT_a_success() -> None:
    """DESIGN.md:344-345 arm 1, against the recorded fixture VERBATIM.

    This is the whole reason the module exists. A client branching on
    `response.status_code` returns this body as a success, finds no
    `candidates` key and reports zero candidates for a REFUSED
    credential.
    """
    body = read_fixture("error_auth_200_body401.json")
    async with client(responder(200, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")

    # Jobvite's OWN status is preserved (DESIGN.md:572-574)...
    assert caught.value.upstream_status == 401
    assert "Invalid api/secret" in caught.value.upstream_message
    # ...and it maps to the registry's row, NOT to a 401 for the caller.
    # The credential that failed is the one THIS SERVER holds.
    assert caught.value.kind is EXTERNAL_SERVICE_ERROR
    assert caught.value.kind.status == 502


async def test_positive_control_a_200_with_status_code_200_SUCCEEDS() -> None:
    """The paired positive control for the case above.

    A guard that refuses everything is not a guard
    (DESIGN.md:1431-1433). Without this, an `evaluate_response` that
    raised on every input would pass the C5-S1 case. This body is
    SYNTHETIC - no success body has ever been observed
    (`JOBVITE-CONTRACT.md` §3.2) - so it is a hypothesis and carries no
    ground-truth weight.
    """
    body = json.dumps(
        {"status": {"code": 200, "messages": []}, "candidates": []}
    ).encode()
    async with client(responder(200, body)) as c:
        result = await c.request("GET", "/candidate")
    assert result["candidates"] == []


async def test_positive_control_a_200_with_no_status_block_at_all_SUCCEEDS() -> None:
    """The second unknown `JOBVITE-CONTRACT.md` §3.2 records, tolerated.

    Whether a success body carries a `status` block is unknown
    (checklist row §13.1), so BOTH shapes must pass. A client that
    required the block would turn every real success into an error the
    day a credential lands.
    """
    async with client(responder(200, b'{"requisitions": []}')) as c:
        assert await c.request("GET", "/job") == {"requisitions": []}


# ======================================================================
# The four remaining RECORDED fixtures, byte-exact. With #1 above that
# is five, and the recorded tier is exactly five files - all of them.
# ======================================================================


def test_the_recorded_tier_is_exactly_these_five_files() -> None:
    """The count itself, asserted rather than remembered.

    `IMPLEMENTATION-PLAN.md:786-789` claims the recorded tier is five
    files and that the list is exhaustive. A test that asserted only the
    five it knew about would pass if a sixth were added and never
    noticed.
    """
    recorded = {
        "error_auth_200_body401.json",
        "error_auth_401.json",
        "error_route_404.json",
        "error_task_400.html",
        "error_v1_auth_401.txt",
    }
    on_disk = {p.name for p in FIXTURES_DIR.iterdir() if p.name.startswith("error_")}
    assert on_disk == recorded, "the recorded tier changed; U4's ground truth moved"


def test_recorded_error_fixtures_are_byte_exact() -> None:
    """All four remaining [RECORDED] captures, pinned as raw bytes."""
    assert read_fixture("error_auth_401.json") == (
        b'{"status":{"code":401,"messages":["Invalid api/secret. Try again with '
        b'a valid api/secret"]}}\n'
    )
    assert read_fixture("error_route_404.json") == (
        b'{"status":{"code":404,"messages":["Invalid URL Cannot find API."]}}\n'
    )
    assert read_fixture("error_task_400.html") == (
        b'<!doctype html><html lang="en"><head><title>HTTP Status 400 \xe2\x80\x93 '
        b"Bad Request</title></head><body><h1>HTTP Status 400 \xe2\x80\x93 Bad "
        b"Request</h1></body></html>\n"
    )
    # NOTE the absence of a trailing newline, where the other four have
    # one. This assertion was written with a `\n` and the byte-exact
    # check caught it, which is the whole argument for pinning bytes
    # rather than parsed content: every one of these fixtures
    # round-trips identically through `json.loads`.
    assert read_fixture("error_v1_auth_401.txt") == (
        b"Invalid api/secret. Try again with a valid api/secret"
    )


def test_the_two_auth_fixtures_are_byte_identical_only_http_status_differs() -> None:
    """The discriminator for C5-S1 is the HTTP STATUS, not the bytes.

    Worth pinning explicitly: `error_auth_200_body401.json` and
    `error_auth_401.json` are the same bytes. A reader who assumed the
    fixture NAME carried the 200 would write a test that passes while
    loading the wrong file, and it would still be green.
    """
    assert read_fixture("error_auth_200_body401.json") == read_fixture(
        "error_auth_401.json"
    )


async def test_a_json_envelope_401_on_an_http_401_fails() -> None:
    """`error_auth_401.json` - conventional, both arms agree."""
    body = read_fixture("error_auth_401.json")
    async with client(responder(401, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.upstream_status == 401


async def test_a_tomcat_html_error_page_fails_loudly() -> None:
    """`error_task_400.html` - the third encoding (DESIGN.md:347-349).

    HTML is not well-formed XML, so `defusedxml` refuses it; the point
    is that it becomes an error rather than being decoded, sniffed, or
    returned empty.
    """
    body = read_fixture("error_task_400.html")
    async with client(responder(400, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("POST", "/task", json_body={"bad": "envelope"})
    assert caught.value.upstream_status == 400


async def test_plain_text_with_no_content_type_fails_loudly() -> None:
    """`error_v1_auth_401.txt` - the second handled encoding.

    `JOBVITE-CONTRACT.md` §3.3 records that this response carries **no
    `Content-Type` header at all**, which is what rules content-type
    sniffing out as the dispatch. The MockTransport response here sends
    none either, so the test exercises that condition rather than
    describing it.
    """
    body = read_fixture("error_v1_auth_401.txt")
    async with client(responder(401, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", jc.JOBFEED_PATH, jobfeed=True)
    assert caught.value.upstream_status == 401
    assert "Invalid api/secret" in caught.value.upstream_message


# ======================================================================
# §9 hazard 7 - a route-level 404 is NOT a record-level not-found.
# ======================================================================


async def test_a_route_level_404_is_not_reported_as_a_record_not_found() -> None:
    """`error_route_404.json`, and the distinction §9 hazard 7 draws.

    `404 "Invalid URL Cannot find API."` means the ROUTE does not exist.
    The record-level not-found shape is unknown (`JOBVITE-CONTRACT.md`
    §3.4, checklist row §13.4). Mapping this to `RESOURCE_NOT_FOUND`
    would tell the caller their candidate id was wrong when the truth is
    that we called a URL that is not there - a bug in this server
    reported as the caller's mistake.
    """
    body = read_fixture("error_route_404.json")
    async with client(responder(404, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")

    assert caught.value.kind is EXTERNAL_SERVICE_ERROR
    assert caught.value.kind is not RESOURCE_NOT_FOUND
    assert caught.value.kind.status == 502, (
        "a route-level 404 must not surface to the caller as a 404"
    )


async def test_an_http_404_with_NO_status_envelope_is_also_not_a_record_not_found() -> (
    None
):
    """The second arm, and the amputation harness is why it exists.

    A12 in `check-u4-client-amputation.sh` INTRODUCES the mapping hazard
    7 forbids. Its first revision injected that mapping after the
    envelope arm, where arm 1 already raises for the recorded fixture's
    404 envelope - the branch was unreachable, the whole suite stayed
    green, and the row tested nothing. Repositioning it killed the case
    above.

    That still left one shape uncovered: an HTTP 404 carrying no
    `status` block at all reaches arm 2 rather than arm 1, so the case
    above says nothing about it. This arm covers it, and the
    record-level not-found shape being UNKNOWN (`JOBVITE-CONTRACT.md`
    §3.4) is exactly why neither may be guessed at.
    """
    async with client(responder(404, b'{"message": "nope"}')) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.kind is EXTERNAL_SERVICE_ERROR
    assert caught.value.kind is not RESOURCE_NOT_FOUND


# ======================================================================
# The two SYNTHETIC malformed bodies - fail loudly, no ground-truth
# weight. Their BYTES ARE DELIBERATELY NOT PINNED: they are invented,
# not captured.
# ======================================================================


@pytest.mark.parametrize("name", ["malformed_not_json.txt", "malformed_truncated.json"])
async def test_a_malformed_body_fails_loudly_rather_than_degrading(name: str) -> None:
    """Neither may become an empty result.

    The failure this rules out is the one C5-S1 is about, arriving by a
    different road: an `except ValueError: return {}` turns an
    undecodable body into "no candidates found".
    """
    async with client(responder(200, read_fixture(name))) as c:
        with pytest.raises(JobviteUpstreamError):
            await c.request("GET", "/candidate")


async def test_a_malformed_body_on_a_200_reports_no_upstream_status() -> None:
    """A 200 whose body will not decode reports NO upstream status.

    Claiming `upstream_status == 200` would say the failure WAS the 200,
    which inverts the field's meaning.
    """
    async with client(responder(200, b"this is not JSON at all")) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.upstream_status is None


async def test_valid_json_that_is_not_an_object_fails() -> None:
    """A bare list or `null` decodes and is not a Jobvite body."""
    for body in (b"null", b"[1, 2, 3]", b'"a string"'):
        async with client(responder(200, body)) as c:
            with pytest.raises(JobviteUpstreamError):
                await c.request("GET", "/candidate")


# ======================================================================
# THE INVARIANT'S SECOND ARM, in isolation. DESIGN.md:344-345 says BOTH.
# ======================================================================


async def test_arm_2_an_http_500_with_a_passing_envelope_still_fails() -> None:
    """The HTTP arm, exercised where the ENVELOPE arm cannot catch it.

    Without this case, deleting `if http_status >= 400` from the client
    leaves every other test in this file green: the recorded fixtures
    all carry a failing `status.code`, so arm 1 catches them all. This
    body is synthetic.
    """
    body = json.dumps({"status": {"code": 200, "messages": ["fine"]}}).encode()
    async with client(responder(503, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.upstream_status == 503


async def test_arm_2_an_http_500_with_no_status_block_at_all_still_fails() -> None:
    """The same arm against the other shape that reaches it."""
    async with client(responder(500, b'{"requisitions": []}')) as c:
        with pytest.raises(JobviteUpstreamError):
            await c.request("GET", "/job")


async def test_arm_1_fires_even_when_the_http_status_is_a_success() -> None:
    """Symmetric to the above: the arm where HTTP cannot help.

    Together these two are what make "both, every call" a tested claim
    rather than a sentence in a docstring.
    """
    body = json.dumps({"status": {"code": 409, "messages": ["duplicate"]}}).encode()
    async with client(responder(201, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("POST", "/candidate", json_body={})
    assert caught.value.upstream_status == 409


def test_a_status_code_under_400_in_the_envelope_is_not_an_error() -> None:
    """The boundary itself, at 399/400, on the function directly."""
    assert jc.evaluate_response(200, b'{"status":{"code":399}}') == {
        "status": {"code": 399}
    }
    with pytest.raises(JobviteUpstreamError):
        jc.evaluate_response(200, b'{"status":{"code":400}}')


def test_a_boolean_status_code_is_not_read_as_an_integer() -> None:
    """`bool` is an `int`, and a true `code` is not a status."""
    assert jc._envelope_status_code({"status": {"code": True}}) is None


# ======================================================================
# HR-XML: a HARDENED FALLBACK, not a handled case (DESIGN.md:349-352).
# ======================================================================


async def test_hr_xml_is_treated_as_an_error_body_never_as_a_success() -> None:
    """XML never becomes a success, whatever the HTTP status says."""
    body = (
        b'<?xml version="1.0"?><Errors><Error code="101">Bad request</Error></Errors>'
    )
    async with client(responder(200, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.upstream_status == 101
    assert "Bad request" in caught.value.upstream_message


async def test_an_xml_entity_bomb_is_REFUSED_rather_than_expanded() -> None:
    """The reason `defusedxml` is a dependency at all.

    A billion-laughs document expands to gigabytes under the stdlib
    parser. The assertion that matters is that we get a typed error
    quickly instead of an expanded document - and note this arrives on
    an HTTP 200, so nothing about the transport warned us first.
    """
    bomb = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
        b'<!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">]>'
        b"<lolz>&lol2;</lolz>"
    )
    async with client(responder(200, bomb)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    # The expansion never happened: nothing that long reached the
    # message.
    assert len(caught.value.upstream_message) <= jc.MAX_BODY_EXCERPT_CHARS + 20


async def test_positive_control_defusedxml_still_parses_an_ordinary_document() -> None:
    """Paired positive control: the hardening is not "refuse all XML".

    Without this, a `_raise_from_markup` that ignored its parse entirely
    would pass the bomb case above.
    """
    body = b"<Errors><Error code='204'>Candidate exists</Error></Errors>"
    async with client(responder(200, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert caught.value.upstream_status == 204
    assert "Candidate exists" in caught.value.upstream_message


# ======================================================================
# Authentication: v2 headers, and the v1 query-parameter exception.
# ======================================================================


async def test_v2_credentials_travel_as_headers_and_NEVER_in_the_url() -> None:
    """DESIGN.md:312-313, on the request the transport saw."""
    seen: dict[str, httpx2.Request] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["request"] = request
        return httpx2.Response(200, content=b"{}")

    async with client(handler) as c:
        await c.request("GET", "/candidate", params={"count": "50"})

    request = seen["request"]
    assert request.headers[jc.API_KEY_HEADER] == API_KEY
    assert request.headers[jc.API_SECRET_HEADER] == API_SECRET
    # The whole URL, credentials included, is the claim being tested.
    url = str(request.url)
    assert API_SECRET not in url
    assert API_KEY not in url
    assert "sc=" not in url
    assert url == "https://api.jobvite.com/api/v2/candidate?count=50"


async def test_the_jobfeed_route_is_the_ONE_url_that_carries_credentials() -> None:
    """DESIGN.md:315-318 - the exception, only for this route."""
    seen: dict[str, httpx2.Request] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["request"] = request
        return httpx2.Response(200, content=b'{"jobs": []}')

    async with client(handler) as c:
        assert await c.request("GET", jc.JOBFEED_PATH, jobfeed=True) == {"jobs": []}

    url = str(seen["request"].url)
    assert url.startswith("https://api.jobvite.com/v1/jobFeed")
    assert f"sc={API_SECRET}" in url
    assert f"api={API_KEY}" in url
    assert f"companyId={COMPANY_ID}" in url


async def test_the_jobfeed_route_refuses_without_a_company_id() -> None:
    """A missing `companyId` is OUR fault, not Jobvite's.

    **This case was R2-L-4 and it asserted the defect.** It used
    to require `JobviteUpstreamError`, which `errors.py` maps to
    `/problems/external-service-error` **502** and renders as *"Jobvite
    returned status none: ..."* - telling the caller the upstream failed
    when the deployment is misconfigured and Jobvite was never called.

    `errors.py` has no configuration row and DESIGN.md:541-542 forbids
    minting a slug, so the honest answer is an exception outside the
    hierarchy, which ADR-0017 routes to `/problems/internal-error` 500.
    **The problem object is asserted, not just the exception class**:
    the finding was about what reaches the caller, and the class alone
    would leave that unmeasured.
    """
    async with client(responder(200, b"{}"), with_company_id=False) as c:
        with pytest.raises(RuntimeError) as caught:
            await c.request("GET", jc.JOBFEED_PATH, jobfeed=True)
    assert "companyId" in str(caught.value)
    assert not isinstance(caught.value, JobviteUpstreamError)

    problem = problem_from_exception(caught.value, _L4_REQUEST_ID)
    assert problem["type"] == "/problems/internal-error"
    assert problem["status"] == 500
    # ADR-0017: the detail names the CLASS, never the message - an
    # arbitrary exception's `str()` can carry a URL or a credential
    # fragment, and this value reaches the caller.
    assert problem["detail"] == "An unexpected RuntimeError occurred."
    assert "companyId" not in problem["detail"]


def test_the_client_and_the_redactor_name_the_SAME_two_headers() -> None:
    """Pins the two lists together (fix one, check its siblings).

    Renaming a header here while `utils/redaction.py` keeps the old name
    leaves the redactor watching a header that no longer exists - and it
    fails OPEN, silently, because a redactor that matches nothing still
    returns a mapping.
    """
    assert {jc.API_KEY_HEADER, jc.API_SECRET_HEADER} == set(SECRET_HEADERS)


# ======================================================================
# §8 #2 - no secret reaches a log record. Joins U3's case.
# ======================================================================


async def test_the_jobfeed_url_never_reaches_a_log_record_whole() -> None:
    """DESIGN.md:315-318, asserted against CAPTURED log output.

    The absence assertion has a paired positive below: against a silent
    logger every "the secret is not in the log" test passes vacuously,
    which is the failure mode DESIGN.md:1431-1433 pairs controls to
    prevent.
    """
    records: list[str] = []
    sink_id = logger.add(records.append, level="DEBUG")
    try:
        async with client(responder(200, b'{"jobs": []}')) as c:
            await c.request("GET", jc.JOBFEED_PATH, jobfeed=True)
    finally:
        logger.remove(sink_id)

    logged = "".join(records)
    # POSITIVE half: the logger really did emit something for this call.
    assert "jobvite request" in logged, (
        "nothing was logged at all; every absence below would pass vacuously"
    )
    # ABSENCE half: and none of it carried a credential.
    assert API_SECRET not in logged
    assert API_KEY not in logged
    assert COMPANY_ID not in logged


def _capture_extras() -> tuple[int, list[dict[str, Any]]]:
    """Add a sink keeping each record's `extra`, and return both.

    A COPY of `extra` rather than the record: loguru reuses the record
    object, and a list of references would read back whatever the last
    record held.
    """
    captured: list[dict[str, Any]] = []
    sink_id = logger.add(
        lambda message: captured.append(dict(message.record["extra"])),
        level="DEBUG",
    )
    return sink_id, captured


async def test_a_transport_error_on_the_jobfeed_route_is_redacted() -> None:
    """The exception text goes to the LOG, never to the consumer.

    `httpx` puts the request URL into its exception text
    (DESIGN.md:315-318), so a timeout on the feed carries `sc=` in
    `str(exc)`.

    **The positive control moved, and this is the whole point of the
    case.** It used to be `assert "jobvite.com" in detail` - proving the
    redaction assertion was not vacuous by requiring that something real
    had reached `detail`. `backend/error-handling.md` is `priority:
    required` and forbids that at :383 ("Never leak raw exception
    messages from third-party libraries to API consumers") and :493
    ("never pass `str(exc)` from third-party libraries"): `redact_text`
    bounds the credential classes it knows, and an httpx2 exception also
    carries `_ssl.c` line numbers, socket paths and resolver detail,
    none of which are credential-shaped.

    So the consumer now gets an enumerated reason, and the control is
    pointed at the log record - which is where the text went. It still
    proves redaction ran over REAL content rather than over an empty
    string, because the same string it checks for `jobvite.com` in is
    the one it checks the credentials are absent from.
    """

    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectTimeout(f"timed out connecting to {request.url}")

    sink_id, captured = _capture_extras()
    try:
        async with client(handler) as c:
            with pytest.raises(JobviteUnavailableError) as caught:
                await c.request("GET", jc.JOBFEED_PATH, jobfeed=True)
    finally:
        logger.remove(sink_id)

    # -- THE CONSUMER'S HALF: an enumerated reason and nothing of
    # httpx2's. --
    detail = caught.value.detail
    assert detail == jc.UNAVAILABLE_TIMEOUT_DETAIL
    # The negative arm DESIGN.md:368-372 requires: `detail` still
    # distinguishes an upstream failure from an open breaker, so the fix
    # did not make it useless in the course of making it safe.
    assert "not an open circuit breaker" in detail
    assert detail != jc.UNAVAILABLE_REQUEST_DETAIL
    # And nothing the library wrote is in it - not the URL, not the
    # class name.
    assert "jobvite.com" not in detail
    assert "ConnectTimeout" not in detail
    assert "timed out connecting" not in detail
    assert API_SECRET not in detail
    assert API_KEY not in detail
    assert COMPANY_ID not in detail

    # -- THE LOG'S HALF: the text is here, redacted. --
    errors = [extra["error"] for extra in captured if "error" in extra]
    assert errors, f"the failure was never logged at all: {captured}"
    logged = "".join(errors)
    # POSITIVE control, relocated: the log line really does still carry
    # the URL, so the absences below are about redaction and not an
    # empty string.
    assert "jobvite.com" in logged
    assert "ConnectTimeout" in logged
    assert REDACTED in logged
    assert API_SECRET not in logged
    assert API_KEY not in logged
    assert COMPANY_ID not in logged


async def test_an_error_body_quoting_a_credential_is_redacted_before_detail() -> None:
    """The body is attacker-influenced text in an exception."""
    body = f"failed for https://api.jobvite.com/v1/jobFeed?sc={API_SECRET}".encode()
    async with client(responder(401, body)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", jc.JOBFEED_PATH, jobfeed=True)
    assert API_SECRET not in caught.value.detail
    assert REDACTED in caught.value.detail


async def test_an_enormous_error_body_is_truncated_before_reaching_detail() -> None:
    """A body we do not control must not be an unbounded log line."""
    async with client(responder(500, b"x" * 100_000)) as c:
        with pytest.raises(JobviteUpstreamError) as caught:
            await c.request("GET", "/candidate")
    assert len(caught.value.upstream_message) < 600
    assert caught.value.upstream_message.endswith("[truncated]")


# ======================================================================
# No cookie jar (`JOBVITE-CONTRACT.md` §2.3).
# ======================================================================


async def test_no_cookie_jar_is_carried_between_requests() -> None:
    """The `AWSALBAPP-*` values are the literal `_remove_`.

    There is no session behind them.

    **This is not httpx2's default.** A bare `AsyncClient` stores these
    and sends them back, which the positive control below measures
    directly rather than asserting from memory.
    """
    sent: list[str | None] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(request.headers.get("cookie"))
        return httpx2.Response(
            200,
            content=b"{}",
            headers=[
                ("set-cookie", "AWSALBAPP-0=_remove_; Path=/"),
                ("set-cookie", "AWSALBAPP-1=_remove_; Path=/"),
            ],
        )

    async with client(handler) as c:
        await c.request("GET", "/candidate")
        await c.request("GET", "/candidate")
        await c.request("GET", "/job")
        assert dict(c._client.cookies) == {}

    assert sent == [None, None, None], f"a cookie was carried forward: {sent}"


async def test_positive_control_httpx2_DOES_carry_cookies_by_default() -> None:
    """The measurement that makes the test above non-vacuous.

    If httpx2 kept no jar of its own, the assertion above would pass
    against a client that did nothing, and "no cookie jar" would be an
    untested claim about someone else's default. This asserts the
    default IS to carry them, so the clearing above is doing real work.
    It is the control on the control.
    """
    sent: list[str | None] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(request.headers.get("cookie"))
        return httpx2.Response(
            200, content=b"{}", headers=[("set-cookie", "AWSALBAPP-0=_remove_; Path=/")]
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as bare:
        await bare.get("https://api.jobvite.com/api/v2/candidate")
        await bare.get("https://api.jobvite.com/api/v2/candidate")

    assert sent[1] is not None and "AWSALBAPP-0" in sent[1], (
        "httpx2 no longer carries cookies by default; the clearing in "
        "JobviteClient.request may now be dead code - check before deleting it"
    )


async def test_the_jar_is_cleared_even_when_the_call_RAISED() -> None:
    """Clearing is in a `finally`, so a failed call leaves nothing."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            content=read_fixture("error_auth_200_body401.json"),
            headers=[("set-cookie", "AWSALBAPP-0=_remove_; Path=/")],
        )

    async with client(handler) as c:
        with pytest.raises(JobviteUpstreamError):
            await c.request("GET", "/candidate")
        assert dict(c._client.cookies) == {}


# ======================================================================
# Structural guards. The one place this suite inspects source - via the
# AST.
# ======================================================================


def test_the_module_declares_an_explicit_per_phase_timeout() -> None:
    """DESIGN.md:358 - "explicit and per-phase.

    No SDK default, no single scalar".

    Asserted on the CONSTRUCTED client's timeout object, not by reading
    the source for the word "Timeout".
    """
    c = jc.JobviteClient(api_key=_Secret("k"), api_secret=_Secret("s"))
    timeout = c._client.timeout
    assert timeout.connect is not None
    assert timeout.read is not None
    assert timeout.write is not None
    assert timeout.pool is not None
    assert len({timeout.connect, timeout.read}) == 2, (
        "every phase set to one value is a single scalar wearing four names"
    )


def test_no_third_party_mocking_library_is_imported_anywhere_in_the_suite() -> None:
    """ADR-0007 and DESIGN.md:1420-1421, enforced by walking the AST.

    Not a grep: a grep for "respx" matches this docstring, which is
    exactly the failure U3's amputation found - a test that asserted its
    own documentation existed. `ast` sees imports and nothing else.
    """
    banned = {"respx", "responses", "requests_mock", "aioresponses", "pytest_httpx"}
    tree = ast.parse(pathlib.Path(__file__).read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "httpx2" in imported, "positive control: the AST walk found no imports"
    assert not (imported & banned), f"third-party mocking library imported: {imported}"


# ======================================================================
# Redirects are refused, not inherited (round 2's surviving mutation 1).
# ======================================================================


async def test_a_redirect_is_not_followed_so_credentials_cannot_be_forwarded() -> None:
    """A 30x must NOT be followed: it hands the credentials away.

    **This was a surviving mutation.** Setting `follow_redirects=True`
    left all 294 tests green, because the safety came entirely from
    httpx2 2.12.0's default and nothing in this repository asserted it.

    What following would cost: `x-jvi-api` and `x-jvi-sc` are forwarded
    to whatever host the `Location` names, and on the v1 jobFeed route
    the credentials are QUERY PARAMETERS, so they would land in that
    host's access log as well.

    Asserted on BEHAVIOUR - one request issued, the 30x returned to the
    caller - not on the constructor argument. Reading the argument back
    would assert only that the line I wrote is the line I wrote.
    """
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(str(request.url))
        return httpx2.Response(
            302, headers=[("location", "https://evil.example/redirected")]
        )

    async with client(handler) as c:
        response = await c._client.get("https://api.jobvite.com/v2/anything")

    assert response.status_code == 302, (
        f"the redirect was followed instead of returned. Requests: {seen}"
    )
    assert len(seen) == 1, f"more than one request was issued: {seen}"
    assert not any("evil.example" in url for url in seen), (
        f"a request reached the redirect target, carrying the credentials: {seen}"
    )


async def test_positive_control_httpx2_WOULD_follow_a_redirect_if_asked() -> None:
    """The measurement that makes the test above non-vacuous.

    If httpx2 could not follow redirects at all, the assertion above
    would pass against a client that did nothing and "redirects are
    refused" would be an untested claim about someone else's behaviour.
    This drives the same handler with `follow_redirects=True` and
    requires the chase to happen - so the refusal above is doing real
    work. It is the control on the control, the same shape the
    cookie-jar pair above uses.
    """
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(str(request.url))
        if "evil.example" in str(request.url):
            return httpx2.Response(200, content=b"{}")
        return httpx2.Response(
            302, headers=[("location", "https://evil.example/redirected")]
        )

    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler), follow_redirects=True
    ) as bare:
        response = await bare.get("https://api.jobvite.com/v2/anything")

    assert response.status_code == 200, "httpx2 did not chase the redirect at all"
    assert any("evil.example" in url for url in seen), (
        f"the redirect target was never reached, so the control proves nothing: {seen}"
    )


# httpx2 exceptions outside the HTTPError hierarchy (round 2's L-5).
# ======================================================================


async def test_an_invalid_url_becomes_a_typed_error_not_an_escape() -> None:
    """`except httpx2.HTTPError` reads as any transport failure.

    It is not.

    Measured at httpx2 2.12.0: `InvalidURL`, `CookieConflict` and
    `StreamError` are NOT subclasses of `HTTPError`. An `InvalidURL` is
    reachable the moment a unit interpolates a `path` - U5 and U12 both
    will - and before the fix it escaped `request()` without passing
    through `redact_text` and without becoming a typed error, so this
    module's documented contract was false.

    A NUL byte in the path is the cheapest real trigger, and it never
    reaches the transport, so no mock is involved in producing it.
    """
    sink_id, captured = _capture_extras()
    try:
        async with client(lambda request: httpx2.Response(200, content=b"{}")) as c:
            with pytest.raises(JobviteUnavailableError) as excinfo:
                await c.request("GET", "/candidate\x00")
    finally:
        logger.remove(sink_id)

    # The consumer gets the enumerated reason for this class of failure,
    # and it is the one that says Jobvite was never called - "could not
    # be reached" would be a false statement about the upstream service.
    assert excinfo.value.detail == jc.UNAVAILABLE_REQUEST_DETAIL

    # The class identification moved to the log, because it was the only
    # thing the old assertion was reading out of `str(exc)` and
    # `backend/error-handling.md:493` bars that string from the
    # consumer.
    errors = [extra["error"] for extra in captured if "error" in extra]
    assert errors, f"the failure was never logged at all: {captured}"
    assert "InvalidURL" in "".join(errors), (
        f"the exception was not identified by class in the log: {errors}"
    )


async def test_the_v2_credential_headers_are_redacted_in_the_failure_log() -> None:
    """L-1: `redact_headers`' call site, on the log it now guards.

    On the v2 branch the local `headers` IS `v2_headers()` - the
    resolved `x-jvi-api` and `x-jvi-sc` in the clear (DESIGN.md:312).
    The failure log line carries them, so `redact_headers` has a caller
    for the first time and this is the case that fails if anyone removes
    it.

    The trigger is the NUL-byte `InvalidURL` above rather than a mock
    raising: it fails before the transport, so the v2 headers are real
    and nothing had to be faked to make them so.
    """
    sink_id, captured = _capture_extras()
    try:
        async with client(lambda request: httpx2.Response(200, content=b"{}")) as c:
            with pytest.raises(JobviteUnavailableError):
                await c.request("GET", "/candidate\x00")
    finally:
        logger.remove(sink_id)

    logged_headers = [extra["headers"] for extra in captured if "headers" in extra]
    assert logged_headers, f"no headers reached the log at all: {captured}"
    headers = logged_headers[0]
    # POSITIVE half: the credential headers really were on this request,
    # so the absence below is about redaction and not about an empty
    # dict.
    assert set(SECRET_HEADERS) <= set(headers), (
        f"the v2 credential headers were never on the request: {headers}"
    )
    for name in SECRET_HEADERS:
        assert headers[name] == REDACTED
    # A non-secret header is untouched, so the redactor is selective
    # rather than replacing the whole mapping.
    assert headers["Accept"] == "application/json"
    leaked = [
        needle for needle in (API_KEY, API_SECRET) if needle in json.dumps(headers)
    ]
    assert not leaked, f"{len(leaked)} v2 credentials survived to the log"


def test_the_escaping_classes_are_still_outside_HTTPError() -> None:
    """The control on the fix: needed only while this holds.

    If a future httpx2 folded these under `HTTPError`, the wider
    `except` above would be harmless but the reason for it would have
    evaporated, and the next reader would have no way to tell. This
    asserts the premise rather than leaving it in a comment - and if it
    ever fails, the comment is what needs rewriting, not the code.
    """
    outside = [
        name
        for name in ("InvalidURL", "CookieConflict", "StreamError")
        if not issubclass(getattr(httpx2, name), httpx2.HTTPError)
    ]
    assert outside == ["InvalidURL", "CookieConflict", "StreamError"], (
        f"httpx2 changed its hierarchy; only {outside} remain outside HTTPError"
    )
