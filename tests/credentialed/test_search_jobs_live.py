"""`search_jobs` against a real Jobvite tenant.

**THE FIRST CREDENTIALED ARM IN THIS REPOSITORY**, and the first test
file whose tests are ALL marker-excluded. CI never runs these and
never skips them: they are excluded by *selection* - the `credentialed`
marker deselected by the `-m` in `addopts` - because a skip counts as a
failure (DESIGN.md:1229-1232).

**CI does `--collect-only` against this file** (DESIGN.md:1244-1249). A
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
self-consistent, not that it speaks Jobvite (DESIGN.md:1258-1260).
These are the rows `docs/CREDENTIAL-CHECKLIST.md` converts from
synthetic to recorded the day a key lands - in particular whether the
`requisitions` envelope key, the `total` member and the requisition
field names are what the research `[INFERRED]` them to be.
"""

from __future__ import annotations

import os

import pytest
from fastmcp import Client
from pydantic import SecretStr

from fast_mcp_jobvite.config import SEARCH_JOBS, Settings
from fast_mcp_jobvite.models.jobs import JobSearchResult
from fast_mcp_jobvite.server import build_server
from fast_mcp_jobvite.tools.jobs import REQUEST_ID_META_KEY

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


async def test_search_jobs_against_a_real_tenant(live_settings: Settings) -> None:
    """The whole path, with no transport substituted.

    Checklist rows 1-4 are blocking, and this is the case that
    converts the `job_list_success.json` fixture from synthetic to
    recorded: if the envelope key is not `requisitions`, or `total` is
    absent, the result model refuses the payload here and the research
    `[INFERRED]` marks were wrong.
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
    assert parsed.total >= 0
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
    shape DESIGN.md:474-476 uses as its worked example, which no
    synthetic fixture in this repository is big enough to produce.
    """
    capped = live_settings.model_copy(update={"max_results": 1})
    server = build_server(capped)
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})

    content = result.structured_content
    assert content is not None
    assert content["showing"] <= 1
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
