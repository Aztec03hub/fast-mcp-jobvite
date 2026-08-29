# mypy: allow-untyped-defs, allow-untyped-calls
# ^ This file is a PROBE: its helpers build throwaway clients and
#   responders whose only caller is the arms below. mypy READS it -
#   that is the point of putting docs/reviews in `files` - and every
#   other strict check applies; only the two annotation knobs the ruff
#   per-file-ignores entry already relaxes for ANN are relaxed here, so
#   the two tools say the same thing about the same population.
"""R6: what escapes `request()` when a non-retryable method 5xxs?

`_attempt` wraps any retryable status in `_RetryableUpstream` regardless
of the HTTP method. On the retrying branch `_attempt_with_retry`
converts it back. On the NON-retrying branch (line 1445-1456) there is
no converter.

ARM 1 POST + 503 -> what type leaves `request()`, and what problem does
       `problem_from_exception` build for it?
ARM 1c GET + 503 -> the same drive on the retrying branch, which must
       produce the documented public type, proving the harness observes
       a real difference rather than a broken fixture.
ARM 2 does the POST failure count toward the breaker?
"""

from __future__ import annotations

import asyncio
import sys

import httpx2

sys.path.insert(0, "src")

from fast_mcp_jobvite.errors import problem_from_exception  # noqa: E402
from fast_mcp_jobvite.services import jobvite_client as jc  # noqa: E402

RID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class _Secret:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
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


async def always_503(_req: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(503, content=b'{"status":{"code":503}}')


async def arm(name, method):
    jc.reset_breaker_for_test()
    c = client(always_503)
    try:
        try:
            await c.request(method, "/candidate", json_body={"a": 1})
            raise AssertionError("no exception")
        except BaseException as exc:  # noqa: BLE001
            shown: tuple[str, ...]
            cls = type(exc).__name__
            module = type(exc).__module__
            try:
                problem = problem_from_exception(exc, RID)
                shown = (problem["type"], problem["status"], problem["detail"][:70])
            except Exception as inner:  # noqa: BLE001
                shown = (f"problem_from_exception raised {type(inner).__name__}",)
        count = jc._JOBVITE_BREAKER.failure_count  # noqa: SLF001
    finally:
        await c.aclose()
    print(f"{name}")
    print(f"    escaping type : {module}.{cls}")
    print(f"    problem       : {shown}")
    print(f"    failure_count : {count}")
    return cls, shown


async def main() -> None:
    print("all responses are HTTP 503 with a 503 envelope\n")
    a = await arm("ARM 1c GET  (retrying branch)", "GET")
    print()
    b = await arm("ARM 1  POST (non-retrying branch)", "POST")
    print()
    print(f"same escaping type on both branches? {a[0] == b[0]}")


asyncio.run(main())
