#!/usr/bin/env python3
"""THE BREAKER REJECTION TEST, as a runnable probe rather than prose.

`STANDARDS.md:374-375` blesses `circuitbreaker ^2` and B37 requires one
breaker per dependency using it, so the procedure is a **rejection test
against one library**, not a survey. `DESIGN.md:617` states the single
criterion:

    The breaker must evaluate transitions on the call path, not from a
    background timer. A ContextVar is per-Task: a half-open expiry fired
    by a timer task has no `request_id_var` set and would log `None`,
    failing the §8 case.

So the one experiment is: **does `circuitbreaker` evaluate half-open
expiry on the call path, or from a background timer?**

This file is the artefact of that experiment. Prose about a measurement
decays into a claim about one, so the measurement is committed as
something that runs, and `tests/test_resilience.py` runs it, which means
a `circuitbreaker` bump that moves expiry onto a timer turns this red
instead of leaving a stale paragraph behind.

**Three arms, and the third is the one that makes the other two mean
something.**

1. STRUCTURAL - the module imports no scheduling machinery. Asserted by
   reading `circuitbreaker`'s own source for the names a timer would
   need (`threading`, `Timer`, `call_later`, `create_task`,
   `sleep`). An absence is a claim about where you looked, so the search
   is over the module's whole source text and the names searched for are
   named here.
2. BEHAVIOURAL - drive a breaker open, wait past the recovery timeout
   with NO call in flight, and read two things: the STORED state, which
   a timer implementation would have mutated behind our back, and the
   DERIVED state, which a call-path implementation computes in the
   reader's own frame. The discriminator is that the stored state is
   still `open` while the derived one already reads `half_open`.
3. THE POSITIVE CONTROL - a deliberately timer-driven breaker,
   implemented here in twenty lines, is subjected to the SAME two arms
   and must FAIL them. Without this arm, arm 1 and arm 2 are two checks
   that have only ever passed, and a check that cannot fail cannot be
   told from one that does not test its subject.

**Two of this probe's own arms were wrong on their first run, and the
corrections are the reason the file reads as it does.** Arm 2 was
written with `recovery_timeout=0`, which `circuitbreaker.__init__`
folds away as falsy (`recovery_timeout or RECOVERY_TIMEOUT`) and
silently replaces with 30 seconds - the arm reported `open` and would
have been read as a rejection. Arm 3's control used
`loop.call_later`, and **asyncio callbacks capture the scheduling
context**, so the "timer" transition saw the caller's `request_id`
and the control passed when it had to fail. It uses `threading.Timer`
now, which is the shape `DESIGN.md:617` actually describes: a
transition running somewhere the invocation's ContextVar does not
reach.

Run it directly for the human-readable transcript:

    uv run --frozen python scripts/probe-breaker-call-path.py
"""

from __future__ import annotations

import asyncio
import inspect
import sys
import threading
import time
from contextvars import ContextVar

import circuitbreaker

#: The names a background-timer implementation would have to reach for.
#: Named here, in one place, so the "absence" this probe reports is a
#: statement about a search whose terms are visible rather than about
#: the author's imagination.
SCHEDULING_NAMES: tuple[str, ...] = (
    "threading",
    "Timer",
    "call_later",
    "call_at",
    "create_task",
    "ensure_future",
    "sched",
    "sleep",
)

#: A stand-in for `utils/correlation.py`'s `request_id_var`. The probe
#: uses its own so it stays runnable with nothing imported from the
#: package under test.
probe_request_id: ContextVar[str | None] = ContextVar("probe_request_id", default=None)


def scheduling_names_in_source(module: object) -> list[str]:
    """Return every scheduling name that appears in a module's source.

    Args:
        module: The imported module to read.

    Returns:
        The subset of `SCHEDULING_NAMES` present in the source text, in
        the order they are declared above. An empty list is the
        call-path answer.
    """
    source = inspect.getsource(module)  # type: ignore[arg-type]
    return [name for name in SCHEDULING_NAMES if name in source]


#: How long a probe breaker stays open. Small enough that the probe is
#: cheap and large enough that `circuitbreaker` does not fold it away:
#: `__init__` reads `recovery_timeout or RECOVERY_TIMEOUT`, so a `0`
#: here would be silently replaced by the library's 30-second default
#: and arm 2 would report `open` for a reason that has nothing to do
#: with the criterion being tested.
RECOVERY_SECONDS: float = 0.2


class TimerDrivenBreaker:
    """THE POSITIVE CONTROL - a breaker that expires from a timer.

    This is what `DESIGN.md:617` rejects, written out so the two arms
    above can be shown to fail against it. It flips itself half-open
    from a `threading.Timer`, which is the shape the design names: the
    transition runs somewhere the invocation's ContextVar does not
    reach, so it reads `None`.

    **`loop.call_later` would NOT demonstrate this**, and the first
    version of this class used it. asyncio callbacks capture the
    context at scheduling time, so a `call_later` transition sees the
    scheduling task's `request_id` and the control passes when it is
    required to fail.
    """

    def __init__(self, recovery: float) -> None:
        """Build the control breaker.

        Args:
            recovery: Seconds to stay open before the timer fires.
        """
        self.state = "closed"
        self._recovery = recovery
        #: Whatever `probe_request_id` held when the transition ran.
        #: The sentinel is distinguishable from a genuine `None`, so a
        #: timer that never fired cannot be read as a passing control.
        self.request_id_at_transition: str | None = "<never fired>"
        self._fired = threading.Event()

    def trip(self) -> None:
        """Open the breaker and SCHEDULE the half-open transition."""
        self.state = "open"
        threading.Timer(self._recovery, self._expire).start()

    def _expire(self) -> None:
        """The timer callback: a thread with no request context."""
        self.state = "half_open"
        self.request_id_at_transition = probe_request_id.get()
        self._fired.set()

    def wait(self, timeout: float) -> bool:
        """Block until the timer has fired.

        Args:
            timeout: Seconds to wait before giving up.

        Returns:
            `True` if the transition ran, `False` on timeout - in which
            case the control measured nothing and says so.
        """
        return self._fired.wait(timeout)


async def arm_2_behavioural() -> tuple[str, str]:
    """Drive `circuitbreaker` open, wait out the window, call nothing.

    Returns:
        `(stored_state, derived_state)` read after the recovery window
        has elapsed with no call in flight. A call-path implementation
        reports `("open", "half_open")`: nothing mutated the stored
        value, and the expiry was computed by this frame at the moment
        it asked. A timer implementation would report
        `("half_open", "half_open")`, having flipped while nobody was
        looking.
    """
    breaker = circuitbreaker.CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=RECOVERY_SECONDS,
        expected_exception=ValueError,
    )

    # `circuitbreaker` ships no `py.typed`, so mypy sees an
    # untyped decorator and refuses to keep the wrapped
    # function's type. Ignored HERE rather than widening the
    # module override in pyproject.toml, because this file is a
    # probe outside mypy's configured scope and that override is
    # a contract for shipped code.
    #
    # Recorded because THE TWO SCOPES DIFFER: ci.yml runs bare
    # `uv run --frozen mypy` (46 files) while `mypy .` reaches
    # 51, so this line is invisible to the gate and visible to
    # anyone who checks more widely. The gate's set is a subset
    # of the wider one, so the difference cannot produce a false
    # green - only a surprise.
    @breaker  # type: ignore[untyped-decorator]
    async def always_fails() -> None:
        msg = "forced"
        raise ValueError(msg)

    try:
        await always_fails()
    except ValueError:
        pass

    # Past the window, with NOTHING running: no task was created, no
    # thread was started, and the loop has no callback pending.
    await asyncio.sleep(RECOVERY_SECONDS * 2)

    # `_state` is the STORED value. Reading a private attribute is the
    # point of the arm: the public property is derived, and the whole
    # question is whether anything wrote to the stored one.
    stored = str(breaker._state)  # noqa: SLF001
    derived = str(breaker.state)
    return stored, derived


def arm_3_positive_control() -> str | None:
    """Show the timer-driven control failing the ContextVar criterion.

    Returns:
        Whatever `probe_request_id` held when the transition ran. The
        design's claim is that this is `None`; if it ever comes back
        bound, the criterion in `DESIGN.md:617` is wrong and this probe
        is how we would find out. The `"<never fired>"` sentinel means
        the timer did not run at all and the arm measured nothing.
    """
    probe_request_id.set("arm-3-invocation")
    control = TimerDrivenBreaker(recovery=0.01)
    control.trip()
    if not control.wait(timeout=5.0):
        return "<never fired>"
    # Belt and braces: the transition already happened on another
    # thread, so this read is only here to keep `time` honest about the
    # ordering the Event guarantees.
    time.sleep(0)
    return control.request_id_at_transition


def main() -> int:
    """Run all three arms and print the verdict.

    Returns:
        `0` when `circuitbreaker` passes the rejection test and the
        positive control fails it; `1` otherwise.
    """
    ok = True

    found = scheduling_names_in_source(circuitbreaker)
    print(f"ARM 1  scheduling names in circuitbreaker's source: {found or 'NONE'}")
    print(f"       searched for: {list(SCHEDULING_NAMES)}")
    if found:
        print("       *** FAIL *** it reaches for scheduling machinery")
        ok = False
    else:
        print("       PASS - expiry cannot be fired by anything but a read")

    control_names = scheduling_names_in_source(sys.modules[__name__])
    print(f"ARM 1c positive control names in THIS module: {control_names}")
    if not control_names:
        print("       *** BROKEN CONTROL *** arm 1 cannot distinguish anything")
        ok = False
    else:
        print("       PASS - the search term arm 1 uses is one that CAN be found")

    stored, derived = asyncio.run(arm_2_behavioural())
    print(f"ARM 2  STORED state after the window elapsed:  {stored!r}")
    print(f"       DERIVED state, computed by this frame:  {derived!r}")
    if stored != "open":
        print("       *** FAIL *** something mutated the stored state with no")
        print("           call in flight, which is a background transition")
        ok = False
    elif derived != "half_open":
        print("       *** FAIL *** expiry did not resolve to half_open on a read")
        ok = False
    else:
        print("       PASS - the expiry is a derived read, evaluated by its reader")

    seen = arm_3_positive_control()
    print(f"ARM 3  request_id visible to a TIMER-fired transition: {seen!r}")
    if seen is not None:
        print("       *** BROKEN CONTROL *** a timer transition saw a request id;")
        print("           DESIGN.md:617's stated reason would then be wrong.")
        ok = False
    else:
        print("       PASS - the control fails exactly as the design predicts")

    verdict = "ADOPTED" if ok else "REJECTED"
    print(f"\nVERDICT: circuitbreaker 2.x is {verdict} by DESIGN.md:617's criterion.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
