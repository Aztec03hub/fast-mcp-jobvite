#!/usr/bin/env python3
"""Measure what an EMBEDDER's log handler receives on the jobFeed route.

    python3 docs/reviews/probe-u12-f2-embedder-leak.py

**U12-F2, turned from prose into a runnable measurement, then INVERTED
when ADR-0026 landed.** `httpx2` logs `HTTP Request: GET <url>` through
the STANDARD LIBRARY logger, and on `/v1/jobFeed` that URL structurally
carries `api`, `sc` and `companyId` (`DESIGN.md:312-318`).

Our own process gets redaction from `__main__.configure_logging()`. The
shipped server always runs it, at module scope. **An embedder does
not**, and `build_server` is a supported entry point that
`tests/test_server.py` itself uses.

**THIS PROBE DOES NOT EVEN CALL `build_server`**, and that is the
finding's real scope: it constructs `JobviteClient` directly, which is
the object that holds the credential. A fix installed in `build_server`
would leave this path exactly as it was.

## What changed

At `1b2af0c` this file **demonstrated** the leak and exited 0 when it
leaked, deliberately unwired, because gating on it would have gated on
the defect staying - the same call R6 made about its own two probes.
ADR-0026 is now Accepted (option 1: `JobviteClient.__init__` installs
the filter, opt-out keyword, idempotent), so the file is inverted:

**THIS PROBE NOW GATES.** It exits non-zero if any arm reads the defect
or either control fails to fire.

ARM 1  the embedder path with the constructor's default. The
       credentials must NOT reach a handler that is not ours.
ARM 1c positive control: the SAME shape with `install_log_redaction=
       False`, which must LEAK. Without it, "no credentials in the
       stream" passes just as well against a probe that captured
       nothing at all - and this probe's ancestor's whole value was
       that it could read a leak.
ARM 2  idempotence. `JobviteClient` is built once per invocation from
       three call sites, so an unguarded `addFilter` stacks one filter
       per tool call forever. Build N clients; the count of OUR filters
       on `httpx2`'s logger must be exactly 1.
ARM 2c positive control for the counter: append N filters by hand and
       read N back, so ARM 2's `== 1` is a reading of a live list and
       not a constant.

**Every arm's verdict string is derived from the same predicate the
gate uses**, the treatment `probe-r6-breaker-reset.py` got at `3ef01f5`
after it printed `not counted (ok)` beside a counter that had moved.
"""

from __future__ import annotations

import asyncio
import io
import logging
import sys

API_KEY = "PROBEAPIKEYVALUE"  # noqa: S105 - a probe literal, never a credential  # pragma: allowlist secret
API_SECRET = "PROBESECRETVALUE"  # noqa: S105 - a probe literal  # pragma: allowlist secret
COMPANY_ID = "PROBECOMPANYVALUE"

#: How many clients ARM 2 and ARM 2c build. Larger than the two or
#: three a unit test would build, because the growth this arm exists to
#: catch is per-construction and a handful of clients is exactly what
#: hid it.
N_CLIENTS = 25


def _redaction():
    """Import the redaction module late, after the abort check."""
    from fast_mcp_jobvite.utils import redaction

    return redaction


def _our_filters() -> list[logging.Filter]:
    """Every filter of OURS currently on `httpx2`'s logger.

    Counted by TYPE rather than by length: a foreign filter someone
    else installed on the same logger is not our leak, and a count of
    `logger.filters` would blame us for it.
    """
    redaction = _redaction()
    logger = logging.getLogger(redaction.HTTPX_LOGGER_NAME)
    return [f for f in logger.filters if isinstance(f, redaction.RedactingLogFilter)]


def _clear_our_filters() -> None:
    """Leave `httpx2`'s logger as we found it, between arms."""
    logger = logging.getLogger(_redaction().HTTPX_LOGGER_NAME)
    for existing in _our_filters():
        logger.removeFilter(existing)


async def _drive(*, install: bool) -> None:
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
        install_log_redaction=install,
    )
    async with client:
        await client.request("GET", "/jobFeed", jobfeed=True)


def leak_arm(name: str, *, install: bool) -> tuple[list[str], int]:
    """Run one request through a handler that is not ours, and read it.

    Returns:
        The credential values that reached the handler in the clear,
        and the number of lines mentioning the route. A zero line count
        means the experiment measured NOTHING and is reported as such
        rather than as a pass.
    """
    _clear_our_filters()
    captured = io.StringIO()
    root = logging.getLogger()
    handler = logging.StreamHandler(captured)
    root.addHandler(handler)
    previous_level = root.level
    root.setLevel(logging.DEBUG)
    logging.getLogger(_redaction().HTTPX_LOGGER_NAME).setLevel(logging.INFO)
    try:
        asyncio.run(_drive(install=install))
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)
    text = captured.getvalue()

    route_lines = [line for line in text.splitlines() if "jobFeed" in line]
    print(f"{name}: lines an embedder's own handler received, mentioning the route:")
    for line in route_lines:
        print(f"    {line[:160]}")
    if not route_lines:
        print("    (none) - httpx2 logged nothing, so this arm measured NOTHING.")
    leaked = [v for v in (API_KEY, API_SECRET, COMPANY_ID) if v in text]
    return leaked, len(route_lines)


def _leak_verdict(leaked: list[str], lines: int, *, expect_leak: bool) -> str | None:
    """The ONE place a leak arm is judged - verdict string and gate.

    Returns:
        `None` when the arm read what it must, or the failure text. The
        printed line and the exit code are computed from this single
        call, so they cannot drift apart while both say "ok".
    """
    if lines == 0:
        return "the arm captured no route line at all, so it measured nothing"
    if expect_leak and not leaked:
        return (
            "the CONTROL did not leak with the install opted OUT, so this "
            "harness cannot read a leak and the other arm proves nothing"
        )
    if not expect_leak and leaked:
        return f"credentials reached a foreign handler in the clear: {leaked}"
    return None


def idempotence_arm() -> int:
    """Build N clients on the default path; count OUR filters."""
    _clear_our_filters()

    async def build() -> None:
        import httpx2
        from pydantic import SecretStr

        from fast_mcp_jobvite.services.jobvite_client import JobviteClient

        def respond(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, json={})

        for _ in range(N_CLIENTS):
            client = JobviteClient(
                api_key=SecretStr(API_KEY),
                api_secret=SecretStr(API_SECRET),
                company_id=SecretStr(COMPANY_ID),
                transport=httpx2.MockTransport(respond),
            )
            await client.aclose()

    asyncio.run(build())
    return len(_our_filters())


def counter_control_arm() -> int:
    """Append N filters BY HAND and read the count back.

    ARM 2 asserts a constant, `1`. A counter that always returns 1 -
    because it reads the wrong logger, or because `_our_filters`
    matches nothing - satisfies it perfectly. This arm makes the list
    grow on purpose, so ARM 2's reading is known to be live.
    """
    _clear_our_filters()
    redaction = _redaction()
    logger = logging.getLogger(redaction.HTTPX_LOGGER_NAME)
    for _ in range(N_CLIENTS):
        logger.addFilter(redaction.RedactingLogFilter())
    count = len(_our_filters())
    _clear_our_filters()
    return count


def main() -> int:
    # The precondition IS the experiment: if anything has already
    # imported `__main__`, the loguru configuration is installed and
    # this would measure the SHIPPED path rather than the embedder's.
    if "fast_mcp_jobvite.__main__" in sys.modules:
        print("ABORT: __main__ is already imported, so configure_logging() has")
        print("run and this would measure the SHIPPED path, not an embedder's.")
        return 2

    failures: list[str] = []

    leaked1, lines1 = leak_arm("ARM 1  default (redaction installed) ", install=True)
    v1 = _leak_verdict(leaked1, lines1, expect_leak=False)
    print(f"        credential values in the clear: {leaked1 or 'none'}")
    print(f"ARM 1  verdict: {v1 or 'NOT LEAKED (ok)'}")
    if v1:
        failures.append(f"ARM 1: {v1}")

    print()
    leaked1c, lines1c = leak_arm("ARM 1c control (install_log_redaction=False)", install=False)
    v1c = _leak_verdict(leaked1c, lines1c, expect_leak=True)
    print(f"        credential values in the clear: {leaked1c or 'none'}")
    print(f"ARM 1c control: {v1c or f'LEAKED {leaked1c} - the arm can read a leak (PASS)'}")
    if v1c:
        failures.append(f"ARM 1c control: {v1c}")

    print()
    installed = idempotence_arm()
    counted = counter_control_arm()
    # Same predicate for the printed verdict and the gate below.
    v2 = None if installed == 1 else f"{N_CLIENTS} clients left {installed} filters"
    v2c = None if counted == N_CLIENTS else f"appending {N_CLIENTS} filters read back {counted}"
    print(f"ARM 2  {N_CLIENTS} clients -> {installed} filter(s) on "
          f"{_redaction().HTTPX_LOGGER_NAME}: {v2 or 'exactly 1 (ok)'}")
    print(f"ARM 2c control: hand-appended {N_CLIENTS} -> read {counted}: "
          f"{v2c or 'the counter is live (PASS)'}")
    if v2:
        failures.append(f"ARM 2: the install is NOT idempotent - {v2}")
    if v2c:
        failures.append(f"ARM 2c control: the counter reads nothing - {v2c}")

    _clear_our_filters()
    print()
    if failures:
        for failure in failures:
            print(f"*** FAIL *** {failure}")
        print("VERDICT: ADR-0026's guarantee does not hold on the embedder's path.")
        return 1
    print("VERDICT: an embedder who never runs configure_logging() gets the")
    print("         jobFeed credentials redacted, and the install does not stack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
