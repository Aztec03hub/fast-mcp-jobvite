"""Every audit call site passes the phase the design assigns it.

**WHY THIS FILE EXISTS, AND WHAT IT IS NOT.**
`docs/reviews/probe-audit-shape-container.py` swept the `AuditPhase`
container and found that **12 of 15 members could be ROTATED to another
phase with the whole suite still green** (`AUDIT-SHAPES-REPORT.md` §3.3,
tasks #127 #128 #129). The three that died were the policy DISPATCHER's
own branches in `audit.py`. So `_on_audit_write_failure` is well tested
and **nothing asserted that a CALL SITE hands it the right phase.**

That is one defect applied twelve times, and the worst instance is
`candidates.py`'s "NO AUDIT, NO WRITE" emission: rotate it to `READ` and
a failed audit write stops failing the call, so the `create_candidate`
POST - which emails a live human - proceeds **UNAUDITED**. That is the
exact inversion DESIGN.md's audit-write-failure policy exists to
prevent ("Before the side effect: fail the call. No audit, no write.").

**THIS ASSERTS THE PHASE, NOT THE EXISTENCE OF A ROW.** A test checking
only that an audit row was written leaves every rotation undetected and
would be a vacuous fix for exactly this finding. Each case below pins
the ORDERED sequence of phases one invocation emits, so a rotation is a
wrong member and an amputation is a missing element - which is why the
same table also closes #127 (`search_candidates`'s success emission)
and #128 (the MRTR pending leg), both of which were emit-shape
survivors for want of any assertion that the row exists at all.

**THE PHASES ARE READ OFF THE DESIGN, NOT OFF THE CODE.** A read tool
is `READ` (an audit failure logs to stderr and the call continues);
everything before a side effect is `BEFORE_SIDE_EFFECT` (fail the call);
the emission after a completed POST is `AFTER_WRITE` (success with a
warning, never an error). Copying today's arguments into the expectation
table would assert only that the code has not changed.

**AND THE TABLE IS CHECKED AGAINST THE CONTAINER.** The last case walks
the `tools/` package with `ast` and asserts the set of
(function, phase) pairs it finds EQUALS the set these cases observed at
runtime. A call site added later with a phase no case exercises fails
that assertion rather than joining the silent twelve.
"""

from __future__ import annotations

import ast
import json
import pathlib
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import pytest
from fastmcp import Client
from pydantic import SecretStr

from fast_mcp_jobvite import audit as audit_module
from fast_mcp_jobvite.audit import AuditPhase
from fast_mcp_jobvite.config import (
    CREATE_CANDIDATE,
    GET_CANDIDATE,
    GET_JOB_FEED,
    SEARCH_CANDIDATES,
    SEARCH_JOBS,
    Settings,
)
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.services.jobvite_client import JobviteClient
from fast_mcp_jobvite.tools import candidates as candidates_module
from fast_mcp_jobvite.tools import jobs as jobs_module

from .conftest import FIXTURES_DIR

#: A 200 whose body will not decode. `test_jobvite_client.py` pins that
#: this raises rather than degrading to an empty result, so it is the
#: shortest path to every tool's ERROR branch.
MALFORMED = "malformed_not_json.txt"
CANDIDATE_LIST_SUCCESS = "candidate_list_success.json"
JOB_LIST_SUCCESS = "job_list_success.json"
JOBFEED_SUCCESS = "jobfeed_success.json"
CREATE_SUCCESS = "candidate_create_success.json"

FEED_KEY = "feed-key"
FEED_SECRET = "feed-secret-phases"  # noqa: S105 - a test literal  # pragma: allowlist secret
COMPANY_ID = "test-company"

VALID_WRITE_ARGS: dict[str, Any] = {
    "first_name": "Testcandidate",
    "last_name": "Omega",
    "email": "testcandidate.omega@example.invalid",
    "job_eid": "TESTJOB1",
}


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def _read_client(body: bytes) -> Callable[[], JobviteClient]:
    """A `JobviteClient` on `MockTransport` (ADR-0007)."""

    def make() -> JobviteClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, content=body)

        return JobviteClient(
            api_key=SecretStr("test-api-key"),
            api_secret=SecretStr("test-api-secret"),
            transport=httpx2.MockTransport(handler),
        )

    return make


def _feed_client(body: bytes) -> Callable[[], JobviteClient]:
    """The same, carrying the FEED credentials the feed tool sends."""

    def make() -> JobviteClient:
        def handler(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, content=body)

        return JobviteClient(
            api_key=SecretStr(FEED_KEY),
            api_secret=SecretStr(FEED_SECRET),
            company_id=SecretStr(COMPANY_ID),
            transport=httpx2.MockTransport(handler),
        )

    return make


class _Ats:
    """A fake Jobvite that COUNTS the rows it was asked to create.

    The counter is on the server side of the transport, so it measures
    the request that reached the wire rather than our own bookkeeping -
    the construction `test_approval_write.py` rests on, and the only
    thing that makes "no row was written" mean anything.
    """

    def __init__(self, *, body: bytes | None = None) -> None:
        self.body = fixture_bytes(CREATE_SUCCESS) if body is None else body
        self.rows: list[dict[str, Any]] = []

    @property
    def count(self) -> int:
        """The number of candidate rows created so far."""
        return len(self.rows)

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        """Record a POST and answer it; refuse anything else loudly."""
        if request.method != "POST":
            msg = f"the fake ATS was asked for {request.method}, not a write"
            raise AssertionError(msg)
        self.rows.append(json.loads(request.content or b"{}"))
        return httpx2.Response(201, content=self.body)

    def factory(self) -> Callable[[], JobviteClient]:
        """The `client_factory` `build_server` takes."""

        def make() -> JobviteClient:
            return JobviteClient(
                api_key=SecretStr("test-api-key"),
                api_secret=SecretStr("test-api-secret"),
                transport=httpx2.MockTransport(self.handler),
            )

        return make


def _read_settings() -> Settings:
    return Settings(
        tools=f"{SEARCH_CANDIDATES},{GET_CANDIDATE},{SEARCH_JOBS}",
        api_key=SecretStr("test-api-key"),
        api_secret=SecretStr("test-api-secret"),
    )


def _feed_settings() -> Settings:
    return Settings(
        tools=GET_JOB_FEED,
        feed_key=SecretStr(FEED_KEY),
        feed_secret=SecretStr(FEED_SECRET),
        company_id=SecretStr(COMPANY_ID),
    )


def _write_settings() -> Settings:
    """Both write gates satisfied: the flag AND the name in `tools`."""
    return Settings(
        tools=CREATE_CANDIDATE,
        enable_writes=True,
        api_key=SecretStr("test-api-key"),
        api_secret=SecretStr("test-api-secret"),
    )


async def approve_everything(
    message: str,
    response_type: type | None,
    params: Any,
    context: Any,
) -> dict[str, Any]:
    """An elicitation handler that answers `approve: true`.

    **A HOST auto-responder and nothing else** (C4-S1): no assertion in
    this file says a human approved anything.
    """
    return {"approve": True}


async def deny_everything(
    message: str,
    response_type: type | None,
    params: Any,
    context: Any,
) -> Any:
    """An elicitation handler that DECLINES."""
    from fastmcp.client.elicitation import ElicitResult

    return ElicitResult(action="decline", content=None)


@pytest.fixture
def phase_spy(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[AuditPhase]]:
    """Record the phase every `emit` call site passes, in order.

    **The real `emit` still runs.** The spy delegates, so the audit row
    is written by the code under test and the policy dispatcher is
    exercised exactly as it would be; what the spy adds is a record of
    the ARGUMENT, which is the thing nothing asserted.

    Yields:
        The phases emitted, in call order, for one invocation.
    """
    seen: list[AuditPhase] = []

    for module in (candidates_module, jobs_module):
        real = module.emit

        def spy(
            event: Any,
            phase: AuditPhase,
            _real: Any = real,
        ) -> list[str]:
            seen.append(phase)
            result: list[str] = _real(event, phase)
            return result

        monkeypatch.setattr(module, "emit", spy)

    yield seen


# ======================================================================
# THE DRIVERS. One per branch that owns an audit emission.
# ======================================================================


async def _drive_read(
    tool: str,
    body: bytes,
    *,
    feed: bool = False,
    arguments: dict[str, Any] | None = None,
) -> Any:
    """Drive one read tool and return the wire result.

    Returns:
        The `CallToolResult`, so the caller can pin WHICH branch ran.
    """
    if feed:
        server = build_server(_feed_settings(), client_factory=_feed_client(body))
    else:
        server = build_server(_read_settings(), client_factory=_read_client(body))
    async with Client(server) as client:
        return await client.call_tool(
            tool, {"params": arguments or {}}, raise_on_error=False
        )


async def _drive_create_candidate(
    *,
    mode: str,
    handler: Any,
    ats: _Ats,
) -> str:
    """Drive one `create_candidate` call and name the shape it produced.

    Returns:
        `"raised"`, `"is_error"` or `"succeeded"`. The sessionless era
        RAISES where the handshake era returns `is_error=True`, so the
        shape is reported rather than asserted here.
    """
    server = build_server(_write_settings(), client_factory=ats.factory())
    async with Client(server, mode=mode, elicitation_handler=handler) as client:
        try:
            result = await client.call_tool(
                CREATE_CANDIDATE,
                {"params": VALID_WRITE_ARGS},
                raise_on_error=False,
            )
        except Exception:  # noqa: BLE001 - the sessionless era RAISES here
            return "raised"
    return "is_error" if result.is_error else "succeeded"


#: `get_candidate` is the one read that takes an argument.
ONE_CANDIDATE: dict[str, Any] = {"candidate_id": "TESTCND1"}


def _ok(result: Any) -> None:
    """The SUCCESS branch ran.

    **Both branches of a read emit `READ`**, so the phase sequence
    alone cannot tell them apart: without this, an "error" case that
    quietly succeeded would still pass and its call site would stay
    unasserted. Which branch ran is pinned here, per case.
    """
    assert result.is_error is False, result.content


def _failed(result: Any) -> None:
    """The ERROR branch ran."""
    assert result.is_error is True, result.content


async def _case_search_candidates_success() -> None:
    _ok(await _drive_read(SEARCH_CANDIDATES, fixture_bytes(CANDIDATE_LIST_SUCCESS)))


async def _case_search_candidates_error() -> None:
    _failed(await _drive_read(SEARCH_CANDIDATES, fixture_bytes(MALFORMED)))


async def _case_get_candidate_success() -> None:
    _ok(
        await _drive_read(
            GET_CANDIDATE,
            fixture_bytes(CANDIDATE_LIST_SUCCESS),
            arguments=ONE_CANDIDATE,
        )
    )


async def _case_get_candidate_error() -> None:
    _failed(
        await _drive_read(
            GET_CANDIDATE, fixture_bytes(MALFORMED), arguments=ONE_CANDIDATE
        )
    )


async def _case_search_jobs_success() -> None:
    _ok(await _drive_read(SEARCH_JOBS, fixture_bytes(JOB_LIST_SUCCESS)))


async def _case_search_jobs_error() -> None:
    _failed(await _drive_read(SEARCH_JOBS, fixture_bytes(MALFORMED)))


async def _case_get_job_feed_success() -> None:
    _ok(await _drive_read(GET_JOB_FEED, fixture_bytes(JOBFEED_SUCCESS), feed=True))


async def _case_get_job_feed_error() -> None:
    _failed(await _drive_read(GET_JOB_FEED, fixture_bytes(MALFORMED), feed=True))


async def _case_create_candidate_pending() -> None:
    """The MRTR FIRST leg: no handler on the sessionless era.

    `ctx.input_responses` is `None`, so `resolve_approval` returns the
    pending result and no side effect is attempted (#128).
    """
    ats = _Ats()
    shape = await _drive_create_candidate(mode="auto", handler=None, ats=ats)
    assert shape != "succeeded", shape
    assert ats.count == 0, "the pending first leg wrote a row"


async def _case_create_candidate_refused() -> None:
    ats = _Ats()
    shape = await _drive_create_candidate(
        mode="legacy", handler=deny_everything, ats=ats
    )
    assert shape == "is_error", shape
    assert ats.count == 0, "a refused approval created a row"


async def _case_create_candidate_written() -> None:
    ats = _Ats()
    shape = await _drive_create_candidate(
        mode="legacy", handler=approve_everything, ats=ats
    )
    assert shape == "succeeded", shape
    assert ats.count == 1, f"expected one row, the counter reads {ats.count}"


async def _case_create_candidate_post_failed() -> None:
    """The POST reached the wire and its ANSWER would not decode.

    The write may or may not have landed, which is why this branch
    carries `AFTER_WRITE`'s policy rather than `BEFORE_SIDE_EFFECT`'s.
    """
    ats = _Ats(body=fixture_bytes(MALFORMED))
    shape = await _drive_create_candidate(
        mode="legacy", handler=approve_everything, ats=ats
    )
    assert shape == "is_error", shape
    assert ats.count == 1, "the POST never reached the wire"


BEFORE = AuditPhase.BEFORE_SIDE_EFFECT
READ = AuditPhase.READ
AFTER = AuditPhase.AFTER_WRITE

#: (case id, driver, the phases the DESIGN assigns that path, in order).
CASES: tuple[tuple[str, Callable[[], Any], tuple[AuditPhase, ...]], ...] = (
    ("search_candidates-success", _case_search_candidates_success, (READ,)),
    ("search_candidates-error", _case_search_candidates_error, (READ,)),
    ("get_candidate-success", _case_get_candidate_success, (READ,)),
    ("get_candidate-error", _case_get_candidate_error, (READ,)),
    ("search_jobs-success", _case_search_jobs_success, (READ,)),
    ("search_jobs-error", _case_search_jobs_error, (READ,)),
    ("get_job_feed-success", _case_get_job_feed_success, (READ,)),
    ("get_job_feed-error", _case_get_job_feed_error, (READ,)),
    ("create_candidate-pending", _case_create_candidate_pending, (BEFORE,)),
    ("create_candidate-refused", _case_create_candidate_refused, (BEFORE,)),
    (
        "create_candidate-written",
        _case_create_candidate_written,
        (BEFORE, AFTER),
    ),
    (
        "create_candidate-post-failed",
        _case_create_candidate_post_failed,
        (BEFORE, AFTER),
    ),
)


@pytest.mark.parametrize(
    ("driver", "expected"),
    [(driver, expected) for _, driver, expected in CASES],
    ids=[case_id for case_id, _, _ in CASES],
)
async def test_each_audit_emission_passes_the_phase_the_design_assigns_it(
    driver: Callable[[], Any],
    expected: tuple[AuditPhase, ...],
    phase_spy: list[AuditPhase],
) -> None:
    """One invocation, one ORDERED sequence of phases.

    A rotation makes a member wrong; an amputation makes the sequence
    short. Both are the survivors this file was written to kill.
    """
    await driver()

    assert phase_spy, (
        "no audit row was emitted on this path at all, so there is "
        "nothing for the failure policy to apply to"
    )
    assert tuple(phase_spy) == expected, (
        f"this path emitted {[p.value for p in phase_spy]}; the design "
        f"assigns it {[p.value for p in expected]}"
    )


# ======================================================================
# THE CONTAINER CHECK. The table above is a hand-kept list, so it is
# compared to the population it claims to cover rather than trusted.
# ======================================================================


#: HOW MANY CALL SITES EACH `(function, phase)` PAIR HAS (R17-M2).
#:
#: The set equality below proves every pair a case drives is present and
#: every present pair is driven. It CANNOT see a 14th call site added
#: inside an already-covered function under an already-covered phase, on
#: a branch no case exercises - deduplication collapses 13 sites into
#: these 6 pairs, and R17 measured that gap.
#:
#: So the multiplicity is recorded here and asserted. A new site changes
#: this mapping and fails the test, which makes covering it a deliberate
#: act. **Update this in the SAME change that adds the site**, and say
#: in the message why the new site is or is not driven by a case.
SITES_PER_PAIR: dict[tuple[str, str], int] = {
    ("create_candidate", "AFTER_WRITE"): 2,
    ("create_candidate", "BEFORE_SIDE_EFFECT"): 3,
    ("get_candidate", "READ"): 2,
    ("get_job_feed", "READ"): 2,
    ("search_candidates", "READ"): 2,
    ("search_jobs", "READ"): 2,
}


def _phases_in(node: ast.AST, owner: str | None) -> list[tuple[str, str]]:
    """Every `AuditPhase.X` under `node`, tagged with the function.

    **The INNERMOST enclosing function**, which is why this recurses
    rather than using `ast.walk`: every tool here is a closure defined
    inside `register`, and a walk would attribute all fifteen sites to
    `register` and make the equality below trivially true.

    Args:
        node: The subtree to read.
        owner: The function this subtree is inside, if any.

    Returns:
        One (function, member) pair per call site.
    """
    found: list[tuple[str, str]] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.AsyncFunctionDef | ast.FunctionDef):
            found += _phases_in(child, child.name)
            continue
        if (
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "AuditPhase"
            and owner is not None
        ):
            found.append((owner, child.attr))
        found += _phases_in(child, owner)
    return found


def _static_phase_sites() -> Counter[tuple[str, str]]:
    """(function, phase) for every `AuditPhase.X` in `tools/`, by `ast`.

    Derived, never grepped: a text match also finds the two COMMENTS
    naming a member, which is how the sweep's raw counts came out two
    higher than its populations.

    A COUNTER, NOT A SET (R17-M2). Deduplicating collapsed 13 call sites
    into 6 distinct `(function, phase)` pairs, so a site ADDED inside an
    already-covered function under an already-covered phase - on a
    branch no case drives - was invisible while the equality below
    printed clean. The pairs still have to match; the MULTIPLICITY now
    has to match too.

    Returns:
        How many call sites each `(function, phase)` pair has.
    """
    package = pathlib.Path(candidates_module.__file__).parent
    found: Counter[tuple[str, str]] = Counter()
    for path in sorted(package.rglob("*.py")):
        found.update(_phases_in(ast.parse(path.read_text()), None))
    return found


def test_every_audit_phase_call_site_is_covered_by_a_case() -> None:
    """The set the cases exercise EQUALS the set the package holds.

    Not a count. A call site added later under a phase no case drives
    fails here, rather than joining the twelve that were rotatable in
    silence.
    """
    covered = {
        (case_id.split("-")[0], phase.name)
        for case_id, _, expected in CASES
        for phase in expected
    }
    sites = _static_phase_sites()
    static = set(sites)

    assert static, "no AuditPhase call site was found; this check is vacuous"
    assert covered == static, (
        f"only these cases exercise the container: "
        f"covered-but-absent={sorted(covered - static)}, "
        f"present-but-uncovered={sorted(static - covered)}"
    )
    # AND THE MULTIPLICITY, which the set equality above cannot see
    # (R17-M2). Adding a 14th call site under an existing pair changes
    # this mapping and fails here, so covering it is a deliberate act
    # rather than something that happens silently. Update the recorded
    # counts in the SAME change that adds the site, and say why.
    assert dict(sites) == SITES_PER_PAIR, (
        f"the number of call sites per (function, phase) moved: "
        f"recorded={SITES_PER_PAIR}, measured={dict(sites)}"
    )


# ======================================================================
# THE ONE THE POLICY IS FOR: NO AUDIT, NO WRITE.
#
# Asserted as BEHAVIOUR and not as an argument, because this is the
# branch DESIGN.md's audit-failure policy exists for. Both arms run in
# one case: a working audit stream writes exactly one row, and a
# FAILING one writes none. Without the first arm the second passes
# against a `create_candidate` that never writes at all.
# ======================================================================


class _ExplodingLogger:
    """A `logger` whose every audit write fails."""

    def bind(self, **fields: Any) -> _ExplodingLogger:
        """Accept the bound fields and return the same failing sink."""
        return self

    def info(self, message: str) -> None:
        """Fail the way a full disk or a closed pipe would."""
        raise OSError("the audit sink is gone")


async def test_a_failed_audit_write_before_the_post_leaves_the_ats_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No audit, no write - and the control that makes it mean anything.

    Rotate that emission to `READ` and the audit failure is swallowed
    to stderr, so the POST proceeds and a live human is emailed with no
    audit record of it. The refusal arm below then sees a row.
    """
    approved = _Ats()
    shape = await _drive_create_candidate(
        mode="legacy", handler=approve_everything, ats=approved
    )
    assert shape == "succeeded", shape
    assert approved.count == 1, (
        "the control never wrote a row, so the refusal arm below would "
        "pass against a tool that cannot write at all"
    )

    monkeypatch.setattr(audit_module, "logger", _ExplodingLogger())

    blocked = _Ats()
    shape = await _drive_create_candidate(
        mode="legacy", handler=approve_everything, ats=blocked
    )
    assert shape != "succeeded", shape
    assert blocked.count == 0, (
        "the audit write failed BEFORE the side effect and the POST "
        "happened anyway: a live human was emailed unaudited"
    )
