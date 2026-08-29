"""R6 probe: does a NON-outage exception RESET the Jobvite breaker?

Two arms plus a positive control.

ARM 1  drive the breaker to threshold-1 with real outages, then issue ONE
       4xx.  Read failure_count.  "does not count" predicts it stays at
       threshold-1.  "resets" predicts 0.
ARM 2  same, but the non-outage is an EXHAUSTED OUTBOUND BUDGET, which is
       the case tests/test_resilience.py:316 says does not count.
ARM 1c positive control: the same shape with an OUTAGE in the last slot
       must leave failure_count at threshold, proving the harness can
       observe a count at all.
"""

from __future__ import annotations

import asyncio
import sys

import httpx2

sys.path.insert(0, "src")

from fast_mcp_jobvite.errors import (  # noqa: E402
    JobviteUnavailableError,
    JobviteUpstreamError,
)
from fast_mcp_jobvite.services import jobvite_client as jc  # noqa: E402

JOBS_PATH = "/job"
T = jc.DEFAULT_BREAKER_FAILURE_THRESHOLD


class _Secret:
    def __init__(self, value):
        self._value = value

    def get_secret_value(self):
        return self._value


def client(handler, **kw):
    return jc.JobviteClient(
        api_key=_Secret("k"),
        api_secret=_Secret("s"),
        company_id=_Secret("c"),
        transport=httpx2.MockTransport(handler),
        retry_max_attempts=1,
        **kw,
    )


def responder(seq):
    box = {"i": 0}

    async def handler(_req: httpx2.Request) -> httpx2.Response:
        item = seq[min(box["i"], len(seq) - 1)]
        box["i"] += 1
        if isinstance(item, Exception):
            raise item
        return item

    return handler


async def drive_to(c, n):
    """n consecutive outage-class failures."""
    for _ in range(n):
        try:
            await c.request("GET", JOBS_PATH)
        except Exception:  # noqa: BLE001
            pass


async def arm(name, last, *, budget=False):
    jc.reset_breaker_for_test()
    outage = httpx2.Response(500, content=b'{"status":{"code":500}}')
    seq: list = [outage] * (T - 1) + [last]
    c = client(responder(seq))
    try:
        await drive_to(c, T - 1)
        before = jc._JOBVITE_BREAKER.failure_count  # noqa: SLF001
        if budget:
            with jc.outbound_budget_scope(0.001):
                await asyncio.sleep(0.01)
                try:
                    await c.request("GET", JOBS_PATH)
                except (JobviteUnavailableError, JobviteUpstreamError):
                    pass
        else:
            try:
                await c.request("GET", JOBS_PATH)
            except (JobviteUnavailableError, JobviteUpstreamError):
                pass
        after = jc._JOBVITE_BREAKER.failure_count  # noqa: SLF001
        state = jc._JOBVITE_BREAKER.state  # noqa: SLF001
    finally:
        await c.aclose()
    print(f"{name}: failure_count before={before} after={after} state={state}")
    return before, after


async def main() -> None:
    print(f"threshold = {T}")
    ok = httpx2.Response(200, content=b"{}")
    b1, a1 = await arm(
        "ARM 1  last call is a 404 (non-outage)",
        httpx2.Response(404, content=b'{"status":{"code":404}}'),
    )
    b2, a2 = await arm("ARM 2  last call exhausts the budget   ", ok, budget=True)
    b3, a3 = await arm(
        "ARM 1c last call is a 500 (outage)     ",
        httpx2.Response(500, content=b'{"status":{"code":500}}'),
    )
    print()
    verdict3 = "PASS" if a3 == T else "FAIL - harness measures nothing"
    print(f"ARM 1c control: {b3} -> {a3}  (must be {T - 1} -> {T}) {verdict3}")
    v1 = "RESET (defect)" if a1 == 0 and b1 > 0 else "not counted (ok)"
    v2 = "RESET (defect)" if a2 == 0 and b2 > 0 else "not counted (ok)"
    print(f"ARM 1 verdict : {b1} -> {a1}  {v1}")
    print(f"ARM 2 verdict : {b2} -> {a2}  {v2}")


asyncio.run(main())
