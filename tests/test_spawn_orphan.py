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

import os
import pathlib
import signal
import subprocess
import sys
import textwrap
import time

from tests.boot_process import _die_with_parent

#: The parent script. It starts a long-lived child through the SAME
#: `_die_with_parent` the real spawner installs - not a copy of the
#: prctl call written here, which would pass against a spawner that
#: never installs it.
PARENT = textwrap.dedent(
    """
    import subprocess, sys, time
    sys.path.insert(0, {tests!r})
    from boot_process import _die_with_parent

    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)  # {tag}"],
        preexec_fn=_die_with_parent,
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
        preexec_fn=_die_with_parent,  # noqa: PLW1509
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
