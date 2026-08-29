#!/usr/bin/env python3
"""R4-H3 offline: the live arm cannot see a wrong envelope key.

**Why a probe and not a test.** The credentialed arm is marker-excluded
and has never run - nobody holds a Jobvite key. So "its assertions
cannot fail in the way it says they can" cannot be settled by running
it, and a fix to it cannot be shown to work by running it either. This
substitutes a `MockTransport` serving a payload under a DIFFERENT
envelope key - exactly the condition the arm exists to detect - and runs
BOTH the old assertions and the new ones against it.

EXPECTED: every OLD assertion passes; the NEW raw-payload assertions
fail. That gap is the finding, and closing it is the fix.

    python3 docs/reviews/probe-r4-h3-live-arm-cannot-detect.py

Exit 0 when the probe demonstrated what it claims, 1 if it did not
(which would mean the finding is wrong, or this probe is), 3 if it could
not run.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from collections.abc import Callable

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

try:
    import httpx2
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
    from fast_mcp_jobvite.tools.jobs import JOBS_PATH
except Exception as exc:  # noqa: BLE001 - a probe reports, it does not raise
    print(f"COULD NOT RUN: {exc}")
    raise SystemExit(3) from exc

# A tenant holding 1,240 real jobs that returns them under `jobs`, not
# `requisitions`. Nothing about this body is malformed; it is simply not
# the envelope the research [INFERRED].
WRONG_ENVELOPE = json.dumps(
    {
        "jobs": [{"eId": f"REAL{n:04d}", "title": "A Real Job"} for n in range(50)],
        "count": 1240,
    }
).encode()


def settings() -> Settings:
    return Settings(
        tools=SEARCH_JOBS,
        api_key=SecretStr("probe-api-key"),
        api_secret=SecretStr("probe-api-secret"),
    )


def handler(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, content=WRONG_ENVELOPE)


def make_client() -> JobviteClient:
    return JobviteClient(
        api_key=SecretStr("probe-api-key"),
        api_secret=SecretStr("probe-api-secret"),
        transport=httpx2.MockTransport(handler),
    )


def check(label: str, fn: Callable[[], None]) -> bool:
    try:
        fn()
    except AssertionError as exc:
        print(f"  FAILED   {label}   -> {exc}")
        return False
    print(f"  passed   {label}")
    return True


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def main() -> int:
    print("########## the payload this probe serves")
    print(f"  keys it actually carries: {sorted(json.loads(WRONG_ENVELOPE))}")
    print(
        f"  keys the tool looks for:  ['{JOBS_ENVELOPE_KEY}', '{TOTAL_ENVELOPE_KEY}']",
    )
    print()

    server = build_server(settings(), client_factory=make_client)
    async with Client(server) as client:
        result = await client.call_tool(SEARCH_JOBS, {"params": {}})
    content = result.structured_content
    if content is None:
        print("COULD NOT RUN: the tool returned no structured content")
        return 3
    parsed = JobSearchResult.model_validate(
        {"jobs": content["jobs"], "total": content["total"]}
    )
    print(f"########## what the TOOL returned: {content['summary']!r}")
    print()

    print("########## the assertions the live arm carried BEFORE R4-H3")
    old = [
        check(
            "is_error is False",
            lambda: require(result.is_error is False, "is_error"),
        ),
        check(
            "parsed.total >= 0",
            lambda: require(parsed.total >= 0, f"total={parsed.total}"),
        ),
        check(
            "summary == showing N of total",
            lambda: require(
                parsed.summary == f"showing {parsed.showing:,} of {parsed.total:,}",
                "summary disagrees with the numbers",
            ),
        ),
        check(
            "showing <= 1 (the max_results=1 arm)",
            lambda: require(parsed.showing <= 1, f"showing={parsed.showing}"),
        ),
    ]
    print()

    print("########## the assertions R4-H3 adds, on the RAW payload")
    live = settings()
    assert live.api_key is not None
    assert live.api_secret is not None
    async with JobviteClient(
        api_key=live.api_key,
        api_secret=live.api_secret,
        transport=httpx2.MockTransport(handler),
    ) as raw_client:
        payload = await raw_client.request("GET", JOBS_PATH)

    new = [
        check(
            f"'{JOBS_ENVELOPE_KEY}' in payload",
            lambda: require(
                JOBS_ENVELOPE_KEY in payload,
                f"the envelope key is not '{JOBS_ENVELOPE_KEY}': {sorted(payload)}",
            ),
        ),
        check(
            f"'{TOTAL_ENVELOPE_KEY}' in payload",
            lambda: require(
                TOTAL_ENVELOPE_KEY in payload,
                f"the '{TOTAL_ENVELOPE_KEY}' member is absent: {sorted(payload)}",
            ),
        ),
    ]
    print()

    print("########## VERDICT")
    if all(old) and not any(new):
        print("  R4-H3 CONFIRMED. Every assertion the live arm carried before this")
        print("  finding PASSED against a payload it exists to reject; the")
        print("  raw-payload assertions that replace them FAILED, as they must.")
        print("  The tool drops the envelope, so once it has, a wrong key and an")
        print("  empty tenant are the same observation.")
        return 0
    if not all(old):
        print("  NOT DEMONSTRATED: an OLD assertion failed, so the arm could have")
        print("  detected this after all. Re-read the finding before trusting it.")
        return 1
    print("  NOT DEMONSTRATED: a NEW assertion passed against the wrong envelope,")
    print("  so the replacement does not close the gap either.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
