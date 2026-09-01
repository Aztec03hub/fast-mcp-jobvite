"""`search_jobs` against a real Jobvite tenant.

**THE FIRST CREDENTIALED ARM IN THIS REPOSITORY**, and the first test
file whose tests are ALL marker-excluded. CI never runs these and never
skips them: they are excluded by *selection* - the `credentialed` marker
deselected by the `-m` in `addopts` - because a skip counts as a failure
(DESIGN.md:1310-1312).

**CI does `--collect-only` against this file** (DESIGN.md:1325-1330). A
suite that is excluded and never collected rots silently: an import
error or a renamed fixture here is invisible until the day someone
finally has a credential. That is why this module must import cleanly
with **no credential present**.

**Every credential read is inside a test body, never at module scope**
(`tests/credentialed/README.md`). Collection IMPORTS every module in
`testpaths`, so a module-scope read executes during collection - on
every offline run that deliberately deselects these tests, and in CI.
Measured and settled elsewhere: this is **not** caused by the `-m`
selector; a module planted here is imported with it and without it,
identically.

**What these cases settle that the offline suite cannot.** The offline
suite passes against synthetic fixtures, which proves the client is
self-consistent, not that it speaks Jobvite (DESIGN.md:1339-1341). These
are the rows `docs/CREDENTIAL-CHECKLIST.md` converts from synthetic to
recorded the day a key lands - in particular whether the `requisitions`
envelope key, the `total` member and the requisition field names are
what the research `[INFERRED]` them to be.

**That conversion happens in
`test_the_live_envelope_uses_the_inferred_keys`, against the RAW
payload, and not in the tool-level cases.** The tool drops the envelope,
so once it has, a wrong envelope key and an empty tenant are the same
observation. R4-H3 measured the earlier arrangement against a payload
under a different key: it returned `showing 0 of 0` and every assertion
in both tool-level cases passed. **These cases require a tenant with at
least one open requisition**; without it `showing 0 of 0` is a correct
answer and the arm settles nothing. The precondition is stated in
`docs/CREDENTIAL-CHECKLIST.md`.
"""

from __future__ import annotations

import os

import pytest
from fastmcp import Client
from pydantic import SecretStr

from fast_mcp_jobvite.config import SEARCH_JOBS, Settings
from fast_mcp_jobvite.models.jobs import (
    JOBS_ENVELOPE_KEY,
    TOTAL_ENVELOPE_KEY,
    JobSearchResult,
)
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.services.jobvite_client import JobviteClient
from fast_mcp_jobvite.tools.jobs import JOBS_PATH, REQUEST_ID_META_KEY

pytestmark = pytest.mark.credentialed


@pytest.fixture
def live_settings() -> Settings:
    """Build settings from the real environment.

    **The credential read lives here, in a fixture body**, which is
    the whole of what `tests/credentialed/README.md` asks for: a
    fixture is not evaluated at collection, so importing this module
    with no credential set does nothing and cannot fail.

    `pytest.fail` rather than `pytest.skip`: a skip is a green that
    tested nothing, and these tests are reached only when someone has
    deliberately selected `-m credentialed`. Someone who asked for the
    live arm and has no key should be told, not quietly passed.
    """
    api_key = os.environ.get("JOBVITE_API_KEY")
    api_secret = os.environ.get("JOBVITE_API_SECRET")
    if not api_key or not api_secret:
        pytest.fail(
            "the credentialed arm was selected but JOBVITE_API_KEY and "
            "JOBVITE_API_SECRET are not both set"
        )
    return Settings(
        tools=SEARCH_JOBS,
        api_key=SecretStr(api_key),
        api_secret=SecretStr(api_secret),
    )


async def test_the_live_envelope_uses_the_inferred_keys(
    live_settings: Settings,
) -> None:
    """Checklist rows 1-4, asserted on the RAW payload (R4-H3).

    **This is the case that converts `job_list_success.json` from
    synthetic to recorded, and it has to live one level below the
    tool.** The case below used to make that claim and could not
    keep it: `build_result` reads
    `payload.get(JOBS_ENVELOPE_KEY) or []` and falls back to
    `len(items)` for `total`, so a payload under a DIFFERENT envelope
    key yields `jobs=[], total=0` - which validates happily and
    renders as `showing 0 of 0`. Measured against a tenant returning
    1,240 real jobs under another key: every assertion in both live
    cases passed.

    That is fail-closed-on-error and **fails-open-on-empty**. The
    error path is handled; the empty path is not, and a wrong
    envelope key is indistinguishable from an empty tenant once the
    tool has dropped the envelope. So the contract is settled here,
    against what Jobvite actually sent.
    """
    assert live_settings.api_key is not None
    assert live_settings.api_secret is not None
    async with JobviteClient(
        api_key=live_settings.api_key, api_secret=live_settings.api_secret
    ) as client:
        payload = await client.request("GET", JOBS_PATH)

    assert JOBS_ENVELOPE_KEY in payload, (
        f"the envelope key is not {JOBS_ENVELOPE_KEY!r}; "
        f"the research [INFERRED] mark was wrong. Keys: {sorted(payload)}"
    )
    assert TOTAL_ENVELOPE_KEY in payload, (
        f"the {TOTAL_ENVELOPE_KEY!r} member is absent. Keys: {sorted(payload)}"
    )
    assert isinstance(payload[TOTAL_ENVELOPE_KEY], int), (
        f"{TOTAL_ENVELOPE_KEY!r} is {type(payload[TOTAL_ENVELOPE_KEY]).__name__}, "
        "not an int"
    )
    assert isinstance(payload[JOBS_ENVELOPE_KEY], list)
    assert payload[JOBS_ENVELOPE_KEY], (
        "the tenant returned zero requisitions, so the two cases below prove "
        "nothing either way - see the precondition in "
        "docs/CREDENTIAL-CHECKLIST.md"
    )


async def test_search_jobs_against_a_real_tenant(live_settings: Settings) -> None:
    """The whole path, with no transport substituted.

    **The envelope contract is NOT settled here** - see the case
    above, which is where it is settled and why. This case asserts
    what the tool does with a real payload, and it is non-vacuous
    only under the precondition the checklist now states: the tenant
    must hold at least one open requisition. `total >= 1` rather than
    `>= 0` is what makes that precondition load-bearing instead of
    decorative - `>= 0` is satisfied by the wrong-envelope-key
    failure this pair exists to detect.
    """
    server = build_server(live_settings)
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    assert result.is_error is False, f"live call failed: {result.structured_content}"
    content = result.structured_content
    assert content is not None
    parsed = JobSearchResult.model_validate(
        {"jobs": content["jobs"], "total": content["total"]}
    )
    assert parsed.total >= 1
    assert parsed.showing >= 1
    assert parsed.summary == f"showing {parsed.showing:,} of {parsed.total:,}"
    # SS8 #16's read arm, against the real transport rather than a mock.
    assert result.meta is not None
    assert result.meta[REQUEST_ID_META_KEY]


async def test_the_result_cap_holds_against_a_real_page(
    live_settings: Settings,
) -> None:
    """The cap is applied to what Jobvite actually returns.

    The offline arm caps a two-item fixture. This is the arm that
    would catch a tenant whose page is larger than the cap and whose
    `total` therefore exceeds `showing` - the `showing 50 of 1,240`
    shape DESIGN.md:513-515 uses as its worked example, which no
    synthetic fixture in this repository is big enough to produce.

    `showing == 1`, not `showing <= 1` (R4-H3). The `<=` form is
    satisfied by `showing 0 of 0`, which is what a wrong envelope key
    produces - so the assertion that exists to prove the cap holds
    passed hardest in exactly the case the cap was never applied. It
    is meaningful only under the checklist's stated precondition:
    **the tenant must have at least one open requisition.**
    """
    capped = live_settings.model_copy(update={"max_results": 1})
    server = build_server(capped)
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    content = result.structured_content
    assert content is not None
    assert content["showing"] == 1
    assert content["showing"] <= content["total"]


async def test_a_rejected_credential_is_a_502_not_a_401(
    live_settings: Settings,
) -> None:
    """C5-S1 live: the only Critical on the client.

    `api.jobvite.com` answers a rejected credential with **HTTP 200**
    and a body of `{"status":{"code":401,...}}`. A client branching on
    `response.status_code` reads that as success and reports **zero jobs
    for a credential that was refused**.

    The offline suite asserts this against a recorded capture. This
    asserts it against the live service, which is the only place the
    behaviour can change without our fixture changing with it.
    """
    broken = live_settings.model_copy(
        update={"api_secret": SecretStr("definitely-not-a-valid-secret")}
    )
    server = build_server(broken)
    async with Client(server) as client:
        result = await client.call_tool(
            SEARCH_JOBS, {"params": {}}, raise_on_error=False
        )

    assert result.is_error is True, (
        "a rejected credential was reported as success - C5-S1 is live"
    )
    problem = result.structured_content
    assert problem is not None
    assert problem["status"] == 502
    assert problem["type"] == "/problems/external-service-error"
