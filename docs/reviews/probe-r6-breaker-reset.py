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

ARM 3  HALF-OPEN, which R6 recorded as unestablished: "a neutral
       exception in half-open must leave the breaker half-open rather
       than closing it, and I have not established what `circuitbreaker`
       does there under the proposed shape". Drive the breaker OPEN,
       expire the window so `state` reads `half_open`, then issue ONE
       non-outage and read state and counter.
ARM 3c positive control for arm 3: the same shape with an OUTAGE in the
       trial slot must leave the breaker OPEN with a higher counter, so
       arm 3 is a reading of a live state machine and not a constant.

**THIS PROBE GATES.** It exits non-zero if any arm reads the defect or
any control fails to fire, so it can be wired the way
`test_the_breaker_rejection_test_still_passes_against_the_pinned_library`
wires the rejection probe. It did NOT gate when R6 committed it, on
purpose: it demonstrated the defect then, and gating on it would have
gated on the bug staying.
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


def _verdict(before: int, after: int) -> str:
    """The one place an ARM 1 / ARM 2 counter reading is judged.

    A verdict string and a gate condition that answer the same question
    in two places drift apart, and the drift is invisible while the
    behaviour is correct: both say "ok" until the day one is wrong.
    """
    if after == before:
        return "not counted (ok)"
    if after == 0 and before > 0:
        return "RESET (defect)"
    return f"COUNTED (defect): {before} -> {after}"


async def half_open_arm(name, trial):
    """Open the breaker, expire the window, then issue ONE call.

    The recovery timeout is shortened for the length of the arm only.
    `state` is a PROPERTY computing `half_open` from `open_remaining`,
    so expiring the window is all it takes - there is no timer to wait
    for and nothing writes the state behind us.
    """
    jc.reset_breaker_for_test()
    outage = httpx2.Response(500, content=b'{"status":{"code":500}}')
    c = client(responder([outage] * T + [trial]))
    real = jc._JOBVITE_BREAKER._recovery_timeout  # noqa: SLF001
    try:
        await drive_to(c, T)
        opened_state = jc._JOBVITE_BREAKER.state  # noqa: SLF001
        # Expire the open window. 0.01 rather than 0: `__init__` folds a
        # falsy recovery_timeout away as `or RECOVERY_TIMEOUT`, which is
        # the mistake this probe's arm 2 sibling records making.
        jc._JOBVITE_BREAKER._recovery_timeout = 0.01  # noqa: SLF001
        await asyncio.sleep(0.05)
        before_state = jc._JOBVITE_BREAKER.state  # noqa: SLF001
        before = jc._JOBVITE_BREAKER.failure_count  # noqa: SLF001
        try:
            await c.request("GET", JOBS_PATH)
        except (JobviteUnavailableError, JobviteUpstreamError):
            pass
        after = jc._JOBVITE_BREAKER.failure_count  # noqa: SLF001
        after_state = jc._JOBVITE_BREAKER.state  # noqa: SLF001
    finally:
        jc._JOBVITE_BREAKER._recovery_timeout = real  # noqa: SLF001
        await c.aclose()
    print(
        f"{name}: {opened_state} -> {before_state} -> {after_state}, "
        f"failure_count {before} -> {after}"
    )
    return before_state, after_state, before, after


async def main() -> int:
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
    # Each verdict is derived from the SAME predicate the gate below
    # uses, so the line a human reads and the exit code a machine reads
    # cannot disagree. They DID disagree: these strings were written for
    # the RESET defect and only ever asked "did it go to zero?", so an
    # amputation that made a 4xx COUNT printed "not counted (ok)" beside
    # a counter that had just moved 4 -> 5. The gate caught it; the
    # verdict line said it was fine.
    v1 = _verdict(b1, a1)
    v2 = _verdict(b2, a2)
    print(f"ARM 1 verdict : {b1} -> {a1}  {v1}")
    print(f"ARM 2 verdict : {b2} -> {a2}  {v2}")

    print()
    s3, e3, hb3, ha3 = await half_open_arm(
        "ARM 3  half_open, then a 404 (non-outage)",
        httpx2.Response(404, content=b'{"status":{"code":404}}'),
    )
    s3c, e3c, hb3c, ha3c = await half_open_arm(
        "ARM 3c half_open, then a 500 (outage)    ",
        httpx2.Response(500, content=b'{"status":{"code":500}}'),
    )
    print()
    control3 = s3c == "half_open" and e3c == "open" and ha3c > hb3c
    print(
        f"ARM 3c control: {s3c} -> {e3c}, {hb3c} -> {ha3c}  "
        f"(must be half_open -> open, counting) "
        f"{'PASS' if control3 else 'FAIL - harness measures nothing'}"
    )
    if e3 == "closed":
        v3 = "CLOSED by a call that never reached Jobvite (defect)"
    elif e3 != "half_open":
        v3 = f"left half_open for {e3} (defect)"
    elif ha3 != hb3:
        v3 = "COUNTED against the breaker in half_open (defect)"
    else:
        v3 = "still half_open, counter untouched (ok)"
    print(f"ARM 3 verdict : {s3} -> {e3}, {hb3} -> {ha3}  {v3}")

    # THE GATE. Every arm must read the fixed behaviour AND both
    # controls must fire; a control that stopped firing makes the other
    # arms unreadable, so it fails the same way a defect does.
    failures = []
    if a3 != T:
        failures.append("ARM 1c control did not reach the threshold")
    if not control3:
        failures.append("ARM 3c control did not count from half_open")
    if a1 != b1:
        failures.append(f"ARM 1: a 4xx moved the counter {b1} -> {a1}")
    if a2 != b2:
        failures.append(f"ARM 2: an exhausted budget moved it {b2} -> {a2}")
    if s3 != "half_open" or e3 != "half_open" or ha3 != hb3:
        failures.append(
            f"ARM 3: a non-outage took the breaker {s3} -> {e3}, {hb3} -> {ha3}"
        )
    print()
    if failures:
        for f in failures:
            print(f"*** FAIL *** {f}")
        print("VERDICT: a non-outage is NOT neutral to the breaker.")
        return 1
    print("VERDICT: a non-outage is NEUTRAL to the breaker - not counted,")
    print("         and not treated as evidence of health either.")
    return 0


sys.exit(asyncio.run(main()))
