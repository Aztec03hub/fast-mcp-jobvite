"""U2: `request_id_var` (DESIGN.md:586-597, IMPLEMENTATION-PLAN.md:471-478).

**The leak test is the known trap.** "The var is `None` after the invocation"
passes perfectly against a `ContextVar` that was never set at any point - and
against a module that does not set it at all. Every leak assertion here is
therefore paired with the positive arm: inside the scope the var reads back the
id that was set. Without the pair, the negative arm measures nothing.
"""

from __future__ import annotations

import ast
import asyncio
import pathlib
import re

import pytest

from fast_mcp_jobvite.utils import correlation

CORRELATION_PY = (
    pathlib.Path(__file__).resolve().parents[1]
    / "src"
    / "fast_mcp_jobvite"
    / "utils"
    / "correlation.py"
)

RID_A = "11111111-1111-4111-8111-111111111111"
RID_B = "22222222-2222-4222-8222-222222222222"


def test_the_contextvar_is_named_request_id_var_verbatim() -> None:
    """ai/tool-calling.md:173-175 mandates the canonical triple verbatim.

    Asserted on the attribute *and* on the var's own name, because
    `ContextVar("something_else")` bound to an attribute called
    `request_id_var` would satisfy an attribute check alone, and the var's name
    is what appears in a debugger and a traceback.
    """
    assert hasattr(correlation, "request_id_var")
    assert correlation.request_id_var.name == "request_id_var"


def test_the_contextvar_is_typed_str_or_none_and_defaults_to_none() -> None:
    assert correlation.request_id_var.get() is None
    source = CORRELATION_PY.read_text()
    assert "request_id_var: ContextVar[str | None]" in source


def test_the_positive_arm_the_var_reads_back_the_id_inside_the_scope() -> None:
    """Without this, every assertion below passes on a var nobody ever sets."""
    with correlation.request_id_scope(RID_A):
        assert correlation.request_id_var.get() == RID_A


def test_the_id_does_not_leak_past_the_scope() -> None:
    """DESIGN.md:590-591 - a reused worker task must not inherit the last id.

    Paired: the positive arm inside the scope is what makes the negative arm
    after it mean anything.
    """
    assert correlation.request_id_var.get() is None
    with correlation.request_id_scope(RID_A):
        assert correlation.request_id_var.get() == RID_A
    assert correlation.request_id_var.get() is None


def test_the_id_does_not_leak_when_the_invocation_raises() -> None:
    """The reset is in a `finally`, so an exception must not strand the id."""
    with pytest.raises(RuntimeError), correlation.request_id_scope(RID_A):
        assert correlation.request_id_var.get() == RID_A
        raise RuntimeError("the tool body failed")
    assert correlation.request_id_var.get() is None


def test_the_reset_is_lexically_in_a_finally() -> None:
    """Structural arm.

    A `set(None)` after the `yield` would pass every behavioural test above on
    the happy path and strand the id on the error path in production, where the
    exception is not the one the test raises. DESIGN.md:590-591 asks for a
    `finally` specifically, so the `finally` is asserted directly.
    """
    tree = ast.parse(CORRELATION_PY.read_text())
    tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
    assert tries, "no try/finally in correlation.py"
    finally_bodies = [ast.dump(s) for t in tries for s in t.finalbody]
    assert any("reset" in body for body in finally_bodies), finally_bodies


def test_a_nested_scope_restores_the_enclosing_id_rather_than_erasing_it() -> None:
    """`reset(token)`, not `set(None)`."""
    with correlation.request_id_scope(RID_A):
        with correlation.request_id_scope(RID_B):
            assert correlation.request_id_var.get() == RID_B
        assert correlation.request_id_var.get() == RID_A
    assert correlation.request_id_var.get() is None


async def test_concurrent_invocations_never_read_each_others_id() -> None:
    """DESIGN.md:593-597 - the failure a module global would cause, silently.

    Two candidates fetched in parallel would each log the other's id about half
    the time under a module global, and every line would still carry a
    well-formed UUID. Asserted under concurrency, not on a single call, and with
    an interleaving forced by `sleep(0)` so the two tasks are guaranteed to be
    open at the same time rather than merely started together.
    """
    observed: list[tuple[str, str | None]] = []

    async def invocation(request_id: str) -> None:
        with correlation.request_id_scope(request_id):
            for _ in range(5):
                await asyncio.sleep(0)
                observed.append((request_id, correlation.request_id_var.get()))

    await asyncio.gather(invocation(RID_A), invocation(RID_B))

    assert len(observed) == 10
    assert {rid for rid, _ in observed} == {RID_A, RID_B}, "both tasks ran"
    mismatched = [pair for pair in observed if pair[0] != pair[1]]
    assert mismatched == [], mismatched
    assert correlation.request_id_var.get() is None


async def test_the_concurrency_test_would_catch_a_module_global() -> None:
    """Positive control: the same shape, with a module global, must fail.

    Otherwise the test above is a test of `asyncio.gather`, not of the
    ContextVar. This runs the identical interleaving against a mutable holder
    and asserts the corruption actually appears.
    """
    holder: dict[str, str | None] = {"request_id": None}
    observed: list[tuple[str, str | None]] = []

    async def invocation(request_id: str) -> None:
        previous = holder["request_id"]
        holder["request_id"] = request_id
        try:
            for _ in range(5):
                await asyncio.sleep(0)
                observed.append((request_id, holder["request_id"]))
        finally:
            holder["request_id"] = previous

    await asyncio.gather(invocation(RID_A), invocation(RID_B))
    mismatched = [pair for pair in observed if pair[0] != pair[1]]
    assert mismatched, "the control did not corrupt; the real test proves nothing"


def test_correlation_declares_exactly_one_contextvar() -> None:
    """DESIGN.md:589 - "a single ContextVar". A second one is a second truth."""
    source = CORRELATION_PY.read_text()
    assert len(re.findall(r"ContextVar\(", source)) == 1, source
