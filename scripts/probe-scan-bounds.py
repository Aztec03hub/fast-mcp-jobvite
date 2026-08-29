#!/usr/bin/env python3
"""WHAT ACTUALLY BOUNDS A SCAN, measured rather than argued.

R5-H2 measured that `scan()` has no bound and aborted its own probe at
200 requests. **ADR-0024 (Proposed) says the outbound budget is a
mitigation and not a fix.** This probe is the instrument for deciding
that, because the budget exists on `feat/u7-resilience` and did not
exist at `8d7af64` where R5 looked.

It runs the same shape R5 ran, plus the case R5's fake cannot produce,
against a client that HAS the budget - and it reports, for each, which
bound fired, after how many requests, and **what the caller ends up
holding**. That last column is the one the argument turns on: a bound
that returns records with `incomplete=True` and a bound that raises a
503 are both "bounded", and they are not the same answer.

THE TWO SERVERS, and they fail in genuinely different directions:

* NON-ADVANCING - ignores `start` and answers the same full page every
  time. `seen` de-duplicates, `items` stops growing, the loop runs
  forever making no progress. This is R5's fake.
* ADVANCING-FOREVER - honours `start` and answers a full page of NEW
  records every time, forever. `seen` and `items` grow without bound.
  **R5's fake cannot produce this**, and it is why ADR-0024 says the
  ceiling and the zero-progress break are not substitutes.

WHAT IT MEASURED BEFORE THE FIX, and the reason this file exists:

    A1  budget 60s   requests issued: 2001   *** UNBOUNDED ***
    A2  budget  2s   requests issued: 2001   *** UNBOUNDED ***

**The two-second budget did not fire.** It bounds wall clock, and a
`MockTransport` answers thousands of requests inside two seconds. So the
budget is not merely "a mitigation" as ADR-0024 puts it - against a fast
non-advancing server it does not bound the request count at all.

Run it directly for the transcript, or with `--assert` (which
`tests/test_resilience.py` does) to gate on the numbers:

    uv run --frozen python scripts/probe-scan-bounds.py --assert
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import httpx2

from fast_mcp_jobvite.errors import JobviteUnavailableError
from fast_mcp_jobvite.services import jobvite_client as jc

#: The probe's own abort, so a genuinely unbounded loop reports rather
#: than hanging this script. **Reaching it is the finding**, exactly as
#: R5's 200 was, and it is deliberately larger than R5's so a bound that
#: merely raised the number is not mistaken for a bound.
PROBE_ABORT_REQUESTS = 2_000

PAGE_SIZE = 50

#: Each run's `(requests, records, outcome)`, keyed by row id, so
#: `--assert` can check the numbers this file's prose quotes rather than
#: trusting that they were re-read after the last change.
RESULTS: dict[str, tuple[int, int, str]] = {}


class _Secret:
    """A minimal `SecretValue`."""

    def __init__(self, value: str) -> None:
        """Hold the value.

        Args:
            value: The credential text.
        """
        self._value = value

    def get_secret_value(self) -> str:
        """Return the value.

        Returns:
            The credential text.
        """
        return self._value


class ProbeAbort(Exception):  # noqa: N818 - a probe signal, not an error
    """Raised by a handler when the probe's own ceiling is reached."""


def non_advancing(page_size: int) -> tuple[Any, list[int]]:
    """A server that IGNORES `start` and repeats one full page forever.

    This is R5's fake. Every page is full, so the short-page exit never
    fires; every record is already in `seen`, so the scan makes no
    progress at all.

    Args:
        page_size: Records per page.

    Returns:
        The handler and a one-element list holding the request count.
    """
    count = [0]

    def handler(_request: httpx2.Request) -> httpx2.Response:
        count[0] += 1
        if count[0] > PROBE_ABORT_REQUESTS:
            raise ProbeAbort
        body = {
            "requisitions": [{"eId": f"E{i}"} for i in range(page_size)],
            "total": page_size,
        }
        return httpx2.Response(200, content=json.dumps(body).encode())

    return handler, count


def advancing_forever(page_size: int) -> tuple[Any, list[int]]:
    """A server that HONOURS `start` and never runs out of records.

    **R5's fake cannot produce this shape**, and it is the case
    ADR-0024's second mechanism exists for: every page is full and every
    record is NEW, so a zero-progress break can never fire, `seen` and
    `items` grow without bound, and the only thing at risk is memory.

    Args:
        page_size: Records per page.

    Returns:
        The handler and a one-element list holding the request count.
    """
    count = [0]

    def handler(request: httpx2.Request) -> httpx2.Response:
        count[0] += 1
        if count[0] > PROBE_ABORT_REQUESTS:
            raise ProbeAbort
        start = int(request.url.params.get("start", "0"))
        body = {
            "requisitions": [{"eId": f"E{start + i}"} for i in range(page_size)],
            "total": 10**9,
        }
        return httpx2.Response(200, content=json.dumps(body).encode())

    return handler, count


async def run(
    label: str,
    make_server: Any,  # noqa: ANN401 - a factory returning (handler, counter)
    *,
    budget: float,
    page_size: int = PAGE_SIZE,
) -> None:
    """Run one exhaustive scan and report which bound fired.

    Args:
        label: What to print.
        make_server: `non_advancing` or `advancing_forever`.
        budget: `JOBVITE_OUTBOUND_BUDGET_SECONDS` for this run.
        page_size: `JOBVITE_MAX_RESULTS` for this run.
    """
    handler, count = make_server(page_size)
    client = jc.JobviteClient(
        api_key=_Secret("k"),
        api_secret=_Secret("s"),  # noqa: S106 - a probe literal
        transport=httpx2.MockTransport(handler),
        max_results=page_size,
        outbound_budget_seconds=budget,
    )
    outcome = ""
    records = 0
    try:
        result = await client.scan("/job", items_key="requisitions")
    except ProbeAbort:
        outcome = f"*** UNBOUNDED *** probe aborted at {PROBE_ABORT_REQUESTS} requests"
    except JobviteUnavailableError as exc:
        detail = "budget" if "budget" in exc.detail else "other"
        outcome = (
            f"bounded by the OUTBOUND BUDGET ({detail}); "
            "caller gets a 503 and NO RECORDS"
        )
    else:
        outcome = (
            f"bounded IN THE CLIENT; caller gets {len(result.items)} records, "
            f"incomplete={result.incomplete}"
        )
        records = len(result.items)
    finally:
        await client.aclose()

    print(f"{label}")
    print(f"    page size      : {page_size}")
    print(f"    budget         : {budget}s")
    print(f"    requests issued: {count[0]}")
    print(f"    records held   : {records}")
    print(f"    outcome        : {outcome}")
    print()
    RESULTS[label.split()[0]] = (count[0], records, outcome)


async def main() -> None:
    """Run every combination the decision turns on."""
    print("=" * 70)
    print("A server that IGNORES start (R5's fake)")
    print("=" * 70)
    await run("A1  budget 60s, the shipped default", non_advancing, budget=60.0)
    await run("A2  budget 2s, a deliberately tight one", non_advancing, budget=2.0)

    print("=" * 70)
    print("A server that HONOURS start and never runs out")
    print("(R5's fake cannot produce this; it is ADR-0024 mechanism 2's case)")
    print("=" * 70)
    await run("B1  budget 60s, 50 records per page", advancing_forever, budget=60.0)
    await run(
        "B2  budget 60s, 500 records per page - the OTHER page size",
        advancing_forever,
        budget=60.0,
        page_size=500,
    )


def check() -> int:
    """Assert the measurements this probe's prose depends on.

    Run with `--assert` (which `tests/test_resilience.py` does) so a
    change that quietly alters any of these numbers fails rather than
    leaving the report and the ADR discussion quoting figures nothing
    reproduces.

    Returns:
        `0` if every expectation holds, `1` otherwise.
    """
    failures: list[str] = []

    for row in ("A1", "A2"):
        requests, records, _ = RESULTS[row]
        if requests != 2:
            failures.append(f"{row}: expected 2 requests, got {requests}")
        if records != PAGE_SIZE:
            failures.append(f"{row}: expected {PAGE_SIZE} records, got {records}")

    # THE AMENDMENT: equal RECORDS across page sizes, unequal requests.
    # A page ceiling would invert both halves of this.
    b1_requests, b1_records, _ = RESULTS["B1"]
    b2_requests, b2_records, _ = RESULTS["B2"]
    if b1_records != b2_records:
        failures.append(
            f"the ceiling admitted {b1_records} records at 50/page and "
            f"{b2_records} at 500/page; a record ceiling must hold them equal"
        )
    if b1_records != jc.MAX_SCAN_RECORDS:
        failures.append(
            f"expected the ceiling's {jc.MAX_SCAN_RECORDS}, got {b1_records}"
        )
    if b1_requests != b2_requests * 10:
        failures.append(
            f"expected a tenfold request difference, got {b1_requests} vs {b2_requests}"
        )

    for row, (_, _, outcome) in RESULTS.items():
        if "UNBOUNDED" in outcome:
            failures.append(f"{row}: still unbounded")

    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        return 1
    print("All expectations hold.")
    return 0


if __name__ == "__main__":
    asyncio.run(main())
    if "--assert" in sys.argv:
        raise SystemExit(check())
