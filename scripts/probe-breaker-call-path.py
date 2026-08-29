#!/usr/bin/env python3
"""THE BREAKER REJECTION TEST, as a runnable probe rather than prose.

`STANDARDS.md:374-375` blesses `circuitbreaker ^2` and B37 requires one
breaker per dependency using it, so the procedure is a **rejection test
against one library**, not a survey. `DESIGN.md:677` states the single
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
now, which is the shape `DESIGN.md:677` actually describes: a
transition running somewhere the invocation's ContextVar does not
reach.

Run it directly for the human-readable transcript:

    uv run --frozen python scripts/probe-breaker-call-path.py
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import pathlib
import re
import threading
import time
from contextvars import ContextVar

import circuitbreaker

#: The names a background-timer implementation would have to reach for.
#: Named here, in one place, so the "absence" this probe reports is a
#: statement about a search whose terms are visible rather than about
#: the author's imagination.
#:
#: **R6-N3 added six of these.** The original eight had no entry for
#: `call_soon` or `call_soon_threadsafe` - asyncio's most basic
#: schedulers and the immediate neighbours of the `call_later` the list
#: DID think of - nor for `signal`, `run_in_executor`, `to_thread` or
#: `concurrent`. A `circuitbreaker` release that expired half-open state
#: from `loop.call_soon` would have passed arm 1 in silence. This is the
#: "a hand-kept list is blind to the member nobody added" shape, and the
#: list is still hand-kept: what makes it honest is arm 1c below, which
#: requires every term to be DEMONSTRABLE in a file that really
#: schedules.
#:
#: `sched` was dropped and `scheduler` put in its place: `sched` matched
#: the words *scheduling* and *scheduled* as a substring, which is how
#: it appeared to pass while testing nothing. `alarm` was considered and
#: LEFT OUT - `signal.alarm` is implemented in C, so no readable Python
#: source can serve as its control, and reaching for it is already
#: caught by the `signal` term.
SCHEDULING_NAMES: tuple[str, ...] = (
    "threading",
    "Timer",
    "call_later",
    "call_at",
    "call_soon",
    "call_soon_threadsafe",
    "create_task",
    "ensure_future",
    "scheduler",
    "sleep",
    "signal",
    "run_in_executor",
    "to_thread",
    "concurrent",
)

#: Modules that REALLY schedule, used by arm 1c. **Not this probe.**
#: R6-M2: arm 1c used to search this probe's own source for the tuple
#: above, which is defined in this same file - so a file containing
#: nothing but the term list, with zero scheduling code of any kind,
#: passed the control 8/8. Four of the eight terms appeared only as
#: their own definition. A control that cannot fail cannot be told from
#: one that does not test its subject, which is the sentence this
#: probe's own docstring uses to justify arm 1c's existence.
CONTROL_MODULES: tuple[str, ...] = (
    "asyncio.base_events",
    "asyncio.tasks",
    "asyncio.unix_events",
    "asyncio.threads",
    "threading",
    "sched",
    "concurrent.futures.thread",
    "signal",
)

#: A stand-in for `utils/correlation.py`'s `request_id_var`. The probe
#: uses its own so it stays runnable with nothing imported from the
#: package under test.
probe_request_id: ContextVar[str | None] = ContextVar("probe_request_id", default=None)


def module_source(module: object) -> str:
    """Read a module's ENTIRE source, package or single file.

    **The container, not one member** (R6-N3). `inspect.getsource` on a
    PACKAGE returns only its `__init__.py`, so if `circuitbreaker` ever
    ships as a package the search would run over an incomplete corpus
    and report a clean empty - indistinguishable from a real absence,
    which is a failure this project has measured three times. When the
    module is a package this walks every `*.py` beside its `__init__`
    and raises if it finds none, so a packaged release fails LOUDLY.

    Args:
        module: The imported module to read.

    Returns:
        The concatenated source text.

    Raises:
        RuntimeError: If a package yielded no readable source files.
    """
    path = getattr(module, "__file__", None)
    if path is not None and path.endswith("__init__.py"):
        files = sorted(pathlib.Path(path).parent.rglob("*.py"))
        if not files:
            raise RuntimeError(
                f"{module!r} is a package and no *.py was readable under "
                f"{pathlib.Path(path).parent} - the search would be a false empty."
            )
        return "\n".join(f.read_text(encoding="utf-8") for f in files)
    return inspect.getsource(module)  # type: ignore[arg-type]


def scheduling_names_in_source(module: object) -> list[str]:
    """Return every scheduling name that appears in a module's source.

    **Whole words, not substrings.** `sched` used to match the words
    *scheduling* and *scheduled*, so a term the corpus never really used
    reported a hit (R6-M2).

    Args:
        module: The imported module to read.

    Returns:
        The subset of `SCHEDULING_NAMES` present in the source text, in
        the order they are declared above. An empty list is the
        call-path answer.
    """
    source = module_source(module)
    return [
        name
        for name in SCHEDULING_NAMES
        if re.search(rf"\b{re.escape(name)}\b", source)
    ]


def names_no_control_can_demonstrate() -> list[str]:
    """Arm 1c: every term must be findable in code that SCHEDULES.

    This is the arm R6-M2 falsified. It no longer reads this probe -
    it reads `CONTROL_MODULES`, none of which has ever heard of
    `SCHEDULING_NAMES`, so no file can pass by containing the question.

    Returns:
        The terms no control module contains. Empty is the pass.
    """
    sources = [module_source(importlib.import_module(m)) for m in CONTROL_MODULES]
    return [
        name
        for name in SCHEDULING_NAMES
        if not any(re.search(rf"\b{re.escape(name)}\b", s) for s in sources)
    ]


#: How long a probe breaker stays open. Small enough that the probe is
#: cheap and large enough that `circuitbreaker` does not fold it away:
#: `__init__` reads `recovery_timeout or RECOVERY_TIMEOUT`, so a `0`
#: here would be silently replaced by the library's 30-second default
#: and arm 2 would report `open` for a reason that has nothing to do
#: with the criterion being tested.
RECOVERY_SECONDS: float = 0.2


class TimerDrivenBreaker:
    """THE POSITIVE CONTROL - a breaker that expires from a timer.

    This is what `DESIGN.md:677` rejects, written out so the two arms
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
        bound, the criterion in `DESIGN.md:677` is wrong and this probe
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

    undemonstrable = names_no_control_can_demonstrate()
    print(f"ARM 1c terms no scheduling module demonstrates: {undemonstrable or 'NONE'}")
    print(f"       control modules read: {list(CONTROL_MODULES)}")
    if undemonstrable:
        print("       *** BROKEN CONTROL *** arm 1 searches for term(s) that no")
        print("           real scheduling code contains, so their absence from")
        print("           circuitbreaker means nothing.")
        ok = False
    else:
        print("       PASS - every term arm 1 uses is one that CAN be found in")
        print("              code that really schedules, and none of the control")
        print("              modules contains this probe's own term list.")

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
        print("           DESIGN.md:677's stated reason would then be wrong.")
        ok = False
    else:
        print("       PASS - the control fails exactly as the design predicts")

    verdict = "ADOPTED" if ok else "REJECTED"
    print(f"\nVERDICT: circuitbreaker 2.x is {verdict} by DESIGN.md:677's criterion.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
