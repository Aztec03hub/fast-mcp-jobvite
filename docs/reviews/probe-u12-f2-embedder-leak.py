#!/usr/bin/env python3
"""Measure what an EMBEDDER's log handler receives on the jobFeed route.

    python3 docs/reviews/probe-u12-f2-embedder-leak.py

**U12-F2, turned from prose into a runnable measurement.** `httpx2`
logs `HTTP Request: GET <url>` through the STANDARD LIBRARY logger, and
on `/v1/jobFeed` that URL structurally carries `api`, `sc` and
`companyId` (`DESIGN.md:315-318`).

Our redaction reaches that line through the filter
`__main__.configure_logging()` installs. The shipped server always runs
it at module scope. **An embedder does not**, and `build_server` is a
supported entry point that `tests/test_server.py` itself uses.

**THIS PROBE DOES NOT EVEN CALL `build_server`**, and that is the
finding's real scope: it constructs `JobviteClient` directly, which is
the object that holds the credential. A fix installed in `build_server`
would leave this path exactly as it is.

**It currently DEMONSTRATES the leak**, so it must not be wired as a
gate - gating on it would gate on the defect staying. When the decision
in ADR-0026 lands, invert it into an assertion and wire it, the way
`test_the_breaker_rejection_test_still_passes_against_the_pinned_library`
wires the breaker probe.

Exit 0 means LEAKED - the state measured at `1b2af0c`. Exit 1 means the
credentials did not reach the handler, which is the state a fix
produces and the point at which this file should be inverted.
"""

from __future__ import annotations

import asyncio
import io
import logging
import sys

API_KEY = "PROBEAPIKEYVALUE"  # noqa: S105 - a probe literal, never a credential  # pragma: allowlist secret
API_SECRET = "PROBESECRETVALUE"  # noqa: S105 - a probe literal  # pragma: allowlist secret
COMPANY_ID = "PROBECOMPANYVALUE"


async def _drive(handler_stream: io.StringIO) -> None:
    """Issue one jobFeed request with no logging configuration of ours."""
    import httpx2
    from pydantic import SecretStr

    from fast_mcp_jobvite.services.jobvite_client import JobviteClient

    def respond(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"jobs": [], "total": 0})

    client = JobviteClient(
        api_key=SecretStr(API_KEY),
        api_secret=SecretStr(API_SECRET),
        company_id=SecretStr(COMPANY_ID),
        transport=httpx2.MockTransport(respond),
    )
    async with client:
        await client.request("GET", "/jobFeed", jobfeed=True)


def main() -> int:
    # The precondition IS the experiment: if anything has already
    # imported `__main__`, the filter is installed and this measures the
    # shipped path rather than the embedder's.
    if "fast_mcp_jobvite.__main__" in sys.modules:
        print("ABORT: __main__ is already imported, so configure_logging() has")
        print("run and this would measure the SHIPPED path, not an embedder's.")
        return 2

    captured = io.StringIO()
    root = logging.getLogger()
    root.addHandler(logging.StreamHandler(captured))
    root.setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.INFO)

    asyncio.run(_drive(captured))
    text = captured.getvalue()

    request_lines = [line for line in text.splitlines() if "jobFeed" in line]
    print("Lines an embedder's own handler received, mentioning the route:")
    for line in request_lines:
        print(f"    {line[:160]}")
    if not request_lines:
        print("    (none) - httpx2 logged nothing, so this measured NOTHING.")
        print("A clean stream here is not a pass: it is a broken experiment.")
        return 2

    leaked = [v for v in (API_KEY, API_SECRET, COMPANY_ID) if v in text]
    print(f"\nCredential values in the clear: {leaked or 'none'}")
    if leaked:
        print("LEAKED. An embedder that calls build_server - or, as here, the")
        print("client directly - receives the whole URL. ADR-0026 is the decision.")
        return 0
    print("NOT LEAKED. If this is deliberate, invert this probe into an")
    print("assertion and wire it; a probe that proves a fix is a test.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
