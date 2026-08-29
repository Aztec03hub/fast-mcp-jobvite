"""The per-invocation correlation ContextVar (DESIGN.md:599-610).

**The name `request_id_var` is not a choice.** `ai/tool-calling.md:173-175`
mandates the canonical triple verbatim - HTTP header `X-Request-ID`, log field
`request_id`, ContextVar `request_id_var` - so using it discharges the clause
rather than merely resembling it. Renaming this variable breaks compliance, not
only imports.

**Why a ContextVar and not a module global** (DESIGN.md:606-610): `asyncio` runs
invocations concurrently on one thread, and a module global would interleave. Two
candidates fetched in parallel would each log the other's id about half the time,
and the corruption is silent - every line still carries a well-formed UUID. That
is the failure this mechanism exists to prevent, which is why the tests assert
under concurrency rather than on a single call.

**Why it exists at all** (DESIGN.md:599-602, B40): the retry and circuit-breaker
hooks are called *by the resilience library*, not by our call site, so there is
no parameter to thread the id through at the point the log line is written.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id_var", default=None)


@contextmanager
def request_id_scope(request_id: str) -> Iterator[str]:
    """Bind `request_id_var` for the duration of one invocation, then reset it.

    DESIGN.md:602-604 requires that `audit.py` set the var in the same statement
    that mints the id and reset it **in a `finally`**, so an id cannot leak into
    the next invocation on a reused worker task. The `finally` lives here, in
    shipped code, rather than being restated at each call site: a leak test that
    only exercises a `try/finally` written inside the test proves nothing about
    what the server does.

    `ContextVar.reset(token)` is used rather than `set(None)`, so a nested scope
    restores the enclosing id instead of erasing it.

    Args:
        request_id: The UUIDv4 minted for this invocation.

    Yields:
        The same `request_id`, so the caller can bind and use it in one statement.
    """
    token = request_id_var.set(request_id)
    try:
        yield request_id
    finally:
        request_id_var.reset(token)
