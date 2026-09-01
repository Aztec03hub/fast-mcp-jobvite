"""The spawned server must not outlive a SIGKILLed harness (#100).

**This is a defect that was found in the wild twice in one day, not a
hypothetical.** `spawn_marker_server` starts a real server in a real
process; when the pytest run was killed rather than allowed to finish,
that server was still alive 2h02m later, holding its port and running
out of a worktree that had already been deleted. The identical orphan
appeared again the same day from the same test.

A `try: ... finally: proc.kill()` cannot close this. `SIGKILL` runs no
Python. Only the kernel can reap a child whose parent was never given a
chance to, which is what `boot_process._die_with_parent` asks it to do.
"""

from __future__ import annotations

import functools
import os
import pathlib
import signal
import subprocess
import sys
import textwrap
import time

from tests.boot_process import (
    _EXIT_NO_LIBC,
    _EXIT_PARENT_ALREADY_GONE,
    _EXIT_PRCTL_FAILED,
    _LIBC,
    _die_with_parent,
)

#: The parent script. It starts a long-lived child through the SAME
#: `_die_with_parent` the real spawner installs - not a copy of the
#: prctl call written here, which would pass against a spawner that
#: never installs it.
PARENT = textwrap.dedent(
    """
    import functools, os, subprocess, sys, time
    sys.path.insert(0, {tests!r})
    from boot_process import _die_with_parent

    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)  # {tag}"],
        preexec_fn=functools.partial(_die_with_parent, os.getpid()),
    )
    print(proc.pid, flush=True)
    time.sleep(60)
    """
)

TESTS = str(pathlib.Path(__file__).resolve().parent)


def _alive(pid: int, tag: str) -> bool:
    """True while `pid` is live and its argv still carries `tag`.

    Keyed on the tag rather than on existence alone: a bare
    `/proc/<pid>` check would report a recycled pid as the child still
    running, and this test's whole claim is about a pid going away.
    """
    try:
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return False
    return tag.encode() in raw


def _run_parent(tag: str) -> tuple[subprocess.Popen[bytes], int]:
    """Start the parent and return it with the grandchild's pid.

    **The parent gets `_die_with_parent` too, and the reason is that
    this file failed its own sibling check.** Enumerating every `Popen`
    in the repo rather than the sites #100 named turned up three, and
    the third was here: a 300-second process this test spawns from
    pytest with no protection at all. A test about orphans that can
    orphan is the same defect wearing the fix's name. The sleeps are
    also 60s rather than 300s, so the residue is bounded even on the
    day `prctl` is the thing that is broken.
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", PARENT.format(tests=TESTS, tag=tag)],
        stdout=subprocess.PIPE,
        preexec_fn=functools.partial(_die_with_parent, os.getpid()),  # noqa: PLW1509
    )
    assert proc.stdout is not None
    child_pid = int(proc.stdout.readline().strip())
    assert _alive(child_pid, tag), "the grandchild never started"
    return proc, child_pid


def _gone_within(pid: int, tag: str, seconds: float) -> float | None:
    """Seconds until the pid drops `tag`, or None if it never does."""
    started = time.monotonic()
    deadline = started + seconds
    while time.monotonic() < deadline:
        if not _alive(pid, tag):
            return time.monotonic() - started
        time.sleep(0.05)
    return None


def test_sigkilling_the_harness_reaps_the_spawned_server() -> None:
    """The defect itself: parent dies violently, child must die too.

    SIGKILL, deliberately - the signal that runs no handler and no
    `finally`. If this passes only under SIGTERM the fix is a Python
    cleanup path and the real orphan is still possible.
    """
    tag = "orphan-kill"
    parent, child_pid = _run_parent(tag)
    try:
        parent.send_signal(signal.SIGKILL)
        parent.wait(timeout=10)
        elapsed = _gone_within(child_pid, tag, 10.0)
    finally:
        parent.kill()
        parent.wait()
        if _alive(child_pid, tag):  # pragma: no cover - only on failure
            os.kill(child_pid, signal.SIGKILL)

    assert elapsed is not None, (
        f"pid {child_pid} outlived its SIGKILLed parent by over 10s. "
        "That is the orphan from #100: a live server holding a port "
        "with nobody left to stop it."
    )


def test_the_orphan_detector_sees_a_live_child() -> None:
    """The positive control, and without it the test above is empty.

    `_gone_within` returning a number means "the pid stopped carrying
    the tag". A detector that never sees a live process returns that
    immediately and the assertion above passes against a broken fix.
    Here the parent is left ALIVE, so the child must NOT disappear.
    """
    tag = "orphan-control"
    parent, child_pid = _run_parent(tag)
    try:
        assert _gone_within(child_pid, tag, 1.0) is None, (
            f"pid {child_pid} vanished while its parent was still "
            "running, so the detector is not measuring what the test "
            "above believes it measures."
        )
    finally:
        parent.kill()
        parent.wait()
        _gone_within(child_pid, tag, 5.0)


def test_a_healthy_child_takes_none_of_the_bail_out_exits() -> None:
    """The arm the race check never had: prove it does NOT misfire.

    `_die_with_parent` has three ways to kill a child before `exec` -
    no libc, prctl failed, parent already gone. Each is correct when it
    fires and catastrophic when it fires wrongly: the first version
    asked `os.getppid() == 1`, which in a container where pytest is
    itself PID 1 is true for EVERY child from birth, and every
    server-spawning test would have died at spawn.

    Nothing tested that. The orphan test above proves the kill path
    works; this proves the healthy path is not the kill path.
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(0)"],
        preexec_fn=functools.partial(_die_with_parent, os.getpid()),  # noqa: PLW1509
    )
    rc = proc.wait(timeout=30)

    assert rc not in {_EXIT_NO_LIBC, _EXIT_PRCTL_FAILED, _EXIT_PARENT_ALREADY_GONE}, (
        f"a healthy child exited {rc}, which is one of _die_with_parent's own "
        "bail-out codes. The guard fired on a child whose parent was alive and "
        "whose prctl should have succeeded."
    )
    assert rc == 0, f"expected a clean child exit, got {rc}"


# ======================================================================
# THE TWO POSITIVE ARMS (R11-H2).
#
# The case above is NEGATIVE-ONLY: it asserts the guards do not fire.
# That is a real property and it is not coverage, because a deleted
# guard satisfies it perfectly. Measured on `dad014e`: amputating the
# `prctl` return check, and separately amputating the whole re-parenting
# check, each left all 868 tests passing. Both arms below were measured
# to fire BEFORE being written as tests - rc 102, and `prctl` returning
# -1/EINVAL on a bogus option - so neither is a guess about what the
# kernel would do.
#
# Amputate either guard in `boot_process._die_with_parent` and the
# matching case here goes red. That is the whole point of the pair.
# ======================================================================


def test_the_race_check_fires_when_the_parent_is_not_ours() -> None:
    """`os.getppid() != parent_pid` must be able to FIRE.

    The check exists for the window `prctl` cannot close: if the parent
    died between `fork` and the call, `PR_SET_PDEATHSIG` was armed
    against a parent that is already gone and the signal was delivered
    to nobody. Re-parenting is the only observable, so the child asks
    whether its parent is still the one that forked it.

    **Reproducing that race directly would be flaky** - it needs the
    parent to die inside a window measured in microseconds. The
    property under test is not the race; it is that the comparison
    fires when it is false. Handing it a pid that is provably not our
    parent tests exactly that, deterministically, through the same
    `preexec_fn` path production uses.
    """
    not_our_parent = 999_999
    assert not_our_parent != os.getpid(), "the sentinel must not be this process"

    proc = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(0)"],
        preexec_fn=functools.partial(_die_with_parent, not_our_parent),  # noqa: PLW1509
    )
    rc = proc.wait(timeout=30)

    assert rc == _EXIT_PARENT_ALREADY_GONE, (
        f"the child exited {rc}, not {_EXIT_PARENT_ALREADY_GONE}. The "
        "re-parenting check did not fire against a parent pid that is not "
        "ours, so nothing detects it being deleted."
    )


def test_an_unchecked_prctl_would_leave_the_child_unprotected() -> None:
    """The `prctl` return check must be able to FIRE.

    `prctl` reports failure by returning `-1` and setting `errno`; a
    call whose return nobody reads leaves the child with no
    `PR_SET_PDEATHSIG` installed and no sign that anything went wrong -
    the orphan defect wearing the fix's name. `_die_with_parent` takes
    the option as a parameter precisely so this branch is reachable.

    **The control is checked first**, on this machine's own libc,
    because a test asserting `_EXIT_PRCTL_FAILED` would also pass if
    the child had died for some unrelated reason before `exec`.
    """
    bogus_option = 0xFFFF
    assert _LIBC is not None, "no libc, so this case cannot measure its subject"
    assert _LIBC.prctl(bogus_option, 0) != 0, (
        f"prctl({bogus_option:#x}) succeeded on this kernel, so the option is "
        "not bogus here and this case would assert against a branch it never "
        "reached. Pick an option this kernel rejects."
    )

    proc = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(0)"],
        preexec_fn=functools.partial(  # noqa: PLW1509
            _die_with_parent, os.getpid(), bogus_option
        ),
    )
    rc = proc.wait(timeout=30)

    assert rc == _EXIT_PRCTL_FAILED, (
        f"the child exited {rc}, not {_EXIT_PRCTL_FAILED}. A failing prctl "
        "did not stop the child, so a silently unprotected child is "
        "indistinguishable from a protected one."
    )
