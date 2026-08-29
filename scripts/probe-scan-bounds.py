#!/usr/bin/env python3
"""WHAT ACTUALLY BOUNDS A SCAN, measured rather than argued.

R5-H2 measured that `scan()` has no bound and aborted its own probe at
200 requests. **ADR-0024 (Accepted, 2026-08-29) says the outbound budget
is a mitigation and not a fix.** This probe is the instrument for that
claim, because the budget exists now and did not exist at `8d7af64`
where R5 looked.

It runs the shape R5 ran, plus the case R5's fake cannot produce,
against a client that HAS the budget - and it reports, for each, which
bound fired, after how many requests, and **what the caller ends up
holding**. That last column is the one the argument turns on: a bound
that returns records with `incomplete=True` and a bound that raises a
503 are both "bounded", and they are not the same answer.

THE TWO SERVERS, and they fail in genuinely different directions:

* NON-ADVANCING - ignores `start` and answers the same full page every
  time. `seen` de-duplicates, `items` stops growing, the loop runs
  forever making no progress. This is R5's fake, and a RECORD CEILING
  can never fire on it.
* ADVANCING-FOREVER - honours `start` and answers a full page of NEW
  records every time, forever. `seen` and `items` grow without bound.
  **R5's fake cannot produce this**, and a ZERO-PROGRESS BREAK can never
  fire on it. It is why ADR-0024 says the two are not substitutes.

WHAT IT MEASURED ON `5eb64b0`, BEFORE THE FIX, and the reason this file
exists (re-measured by `scan-bound`, not inherited):

    A1  budget 60s   requests issued: 2001   *** UNBOUNDED ***
    A2  budget  2s   requests issued: 2001   *** UNBOUNDED ***
    B1  budget 60s   requests issued: 2001   *** UNBOUNDED ***
    B2  budget 60s   requests issued: 2001   *** UNBOUNDED ***

**The two-second budget did not fire.** It bounds wall clock, and a
`MockTransport` answers thousands of requests inside two seconds - the
whole four-arm run takes under a second. So the budget is not merely "a
mitigation" as ADR-0024 puts it: against a fast non-advancing server it
does not bound the request count at all.

**EVERY ARM'S PRINTED VERDICT AND THE EXIT CODE COME FROM ONE
PREDICATE**, `judge()`. `docs/reviews/probe-r6-breaker-reset.py` records
why: a verdict string and a gate condition that answer the same question
in two places drift apart invisibly, because both say "ok" until the day
one is wrong. That probe printed `not counted (ok)` beside a counter
that had just moved.

Run it for the transcript, or with `--assert` (which
`tests/test_resilience.py` does) to gate on the numbers:

    uv run --frozen python scripts/probe-scan-bounds.py --assert
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, NamedTuple

import httpx2
from loguru import logger

from fast_mcp_jobvite.errors import JobviteUnavailableError
from fast_mcp_jobvite.services import jobvite_client as jc

# The client logs one DEBUG line per request and this probe issues
# thousands. Left on, the transcript is 236KB of noise around twenty
# lines that matter, which is a report nobody reads.
logger.remove()

PAGE_SIZE = 50
BIG_PAGE_SIZE = 500

#: The probe's own abort, so a genuinely unbounded loop reports rather
#: than hanging this script. **Reaching it is the finding**, exactly as
#: R5's 200 was.
#:
#: **DERIVED, and it has to be.** The rescued version of this file hard
#: coded 2,000 - which is exactly the request count arm B1 issues when
#: the ceiling works (100,000 records at 50 per page). The abort and the
#: correct answer sat on the same number, so a ceiling raised by one
#: record would have made a WORKING bound print `*** UNBOUNDED ***`. The
#: doubling is the margin; the derivation is what keeps it.
PROBE_ABORT_REQUESTS = (jc.MAX_SCAN_RECORDS // PAGE_SIZE) * 2


class Observation(NamedTuple):
    """One arm's raw readings, before anything judges them."""

    requests: int
    records: int
    bound: str
    incomplete: bool | None


#: Each arm's `Observation`, keyed by row id.
RESULTS: dict[str, Observation] = {}


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
    progress at all and the record ceiling can never be reached.

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
    row: str,
    label: str,
    make_server: Any,  # noqa: ANN401 - a factory returning (handler, counter)
    *,
    budget: float,
    page_size: int = PAGE_SIZE,
) -> None:
    """Run one exhaustive scan and RECORD what happened.

    It deliberately renders no verdict. `judge()` is the only thing that
    decides whether a reading is good or bad.

    Args:
        row: The row id `judge()` keys expectations by.
        label: What to print above the readings.
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
    records = 0
    incomplete: bool | None = None
    try:
        result = await client.scan("/job", items_key="requisitions")
    except ProbeAbort:
        bound = "unbounded"
        holds = f"nothing; the probe aborted at {PROBE_ABORT_REQUESTS} requests"
    except JobviteUnavailableError as exc:
        bound = "budget" if "budget" in exc.detail else "other-exception"
        holds = "a 503 and NO RECORDS"
    else:
        bound = "client"
        records = len(result.items)
        incomplete = result.incomplete
        holds = f"{records} records, incomplete={result.incomplete}"
    finally:
        await client.aclose()

    RESULTS[row] = Observation(count[0], records, bound, incomplete)
    print(f"{row}  {label}")
    print(f"    page size      : {page_size}")
    print(f"    budget         : {budget}s")
    print(f"    requests issued: {count[0]}")
    print(f"    bound by       : {bound}")
    print(f"    caller holds   : {holds}")
    print()


def judge() -> list[tuple[str, list[str]]]:
    """THE ONE PLACE ANY READING IS JUDGED.

    Every printed verdict and the process exit code are both derived
    from this, so the line a human reads and the code a machine reads
    cannot disagree. See the module docstring for the probe that proved
    they otherwise do.

    Returns:
        One `(row, problems)` per judged row; an empty `problems` list
        is a pass.
    """
    per_page = {"A1": PAGE_SIZE, "A2": PAGE_SIZE}
    judged: list[tuple[str, list[str]]] = []

    # The non-advancing arms. TWO requests, not one: page one is
    # legitimate and its records are kept, page two is what proves the
    # server is not advancing. The RECORDS ARE KEPT is the half that
    # separates this bound from the budget's 503-and-nothing.
    for row, page in per_page.items():
        obs = RESULTS[row]
        problems = []
        if obs.bound != "client":
            problems.append(f"bound by {obs.bound!r}, expected the client's own break")
        if obs.requests != 2:
            problems.append(f"{obs.requests} requests, expected 2")
        if obs.records != page:
            problems.append(f"{obs.records} records held, expected {page}")
        if obs.incomplete is not True:
            problems.append(f"incomplete={obs.incomplete}, expected True")
        judged.append((row, problems))

    # The advancing-forever arms, one per page size.
    for row, page in (("B1", PAGE_SIZE), ("B2", BIG_PAGE_SIZE)):
        obs = RESULTS[row]
        expected_requests = jc.MAX_SCAN_RECORDS // page
        problems = []
        if obs.bound != "client":
            problems.append(f"bound by {obs.bound!r}, expected the record ceiling")
        if obs.records != jc.MAX_SCAN_RECORDS:
            problems.append(
                f"{obs.records} records held, expected the ceiling's "
                f"{jc.MAX_SCAN_RECORDS}"
            )
        if obs.requests != expected_requests:
            problems.append(f"{obs.requests} requests, expected {expected_requests}")
        if obs.incomplete is not True:
            problems.append(f"incomplete={obs.incomplete}, expected True")
        judged.append((row, problems))

    # THE AMENDMENT ITSELF, as its own row: equal RECORDS across the two
    # page sizes, unequal REQUESTS. A ceiling in PAGES inverts both
    # halves, which is why both are asserted - equal records alone would
    # also pass against a bound that always returned nothing.
    b1, b2 = RESULTS["B1"], RESULTS["B2"]
    ratio = BIG_PAGE_SIZE // PAGE_SIZE
    problems = []
    if b1.records != b2.records:
        problems.append(
            f"the ceiling admitted {b1.records} records at {PAGE_SIZE}/page and "
            f"{b2.records} at {BIG_PAGE_SIZE}/page; a RECORD ceiling holds them equal"
        )
    if b1.requests != b2.requests * ratio:
        problems.append(
            f"expected a {ratio}-fold request difference, got {b1.requests} "
            f"vs {b2.requests}"
        )
    judged.append(("RECORDS-NOT-PAGES", problems))

    return judged


async def main() -> int:
    """Run every combination the decision turns on, then judge them.

    Returns:
        `0` if every judged row passes, `1` otherwise.
    """
    print("=" * 70)
    print("A server that IGNORES start (R5's fake)")
    print("=" * 70)
    await run("A1", "budget 60s, the shipped default", non_advancing, budget=60.0)
    await run("A2", "budget 2s, a deliberately tight one", non_advancing, budget=2.0)

    print("=" * 70)
    print("A server that HONOURS start and never runs out")
    print("(R5's fake cannot produce this; it is ADR-0024 mechanism 2's case)")
    print("=" * 70)
    await run(
        "B1",
        f"budget 60s, {PAGE_SIZE} records per page",
        advancing_forever,
        budget=60.0,
    )
    await run(
        "B2",
        f"budget 60s, {BIG_PAGE_SIZE} records per page - the OTHER page size",
        advancing_forever,
        budget=60.0,
        page_size=BIG_PAGE_SIZE,
    )

    print("=" * 70)
    print("VERDICTS - the same predicate the exit code below uses")
    print("=" * 70)
    judged = judge()
    for row, problems in judged:
        if problems:
            print(f"{row:<18} *** FAIL ***")
            for problem in problems:
                print(f"                   {problem}")
        else:
            print(f"{row:<18} bounded as ADR-0024 requires (ok)")

    if any(problems for _, problems in judged):
        print()
        print("VERDICT: the scan is NOT bounded the way ADR-0024 requires.")
        return 1
    print()
    print("VERDICT: both mechanisms fire, on the arm each exists for, and the")
    print("         ceiling holds the record count equal across page sizes.")
    return 0


if __name__ == "__main__":
    code = asyncio.run(main())
    if "--assert" in sys.argv:
        raise SystemExit(code)
