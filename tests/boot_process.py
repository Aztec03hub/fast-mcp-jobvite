"""Process helpers for U1's boot and shutdown cases.

**Not a conftest fixture and not a pytest plugin.**
IMPLEMENTATION-PLAN.md's §4 rule keeps `tests/conftest.py` small and
U0's; this module is imported directly by the two U1 test modules
instead, so no unit's write set overlaps.

Every arm here runs the **real** entry point in a **real** process. A
boot refusal that is asserted by calling `load_settings()` in-process
proves the validator; it does not prove that the process exits, which is
what §8 #10 requires and what a supervisor observes.
"""

from __future__ import annotations

import ctypes
import functools
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time

#: The entry script the shutdown case runs. It composes an observable
#: resource onto the server's own lifespan through the `extra_lifespan`
#: parameter `server.py` exposes, and calls the **shipped** `main()` -
#: so the handler, the `except KeyboardInterrupt` and the
#: `finally: os._exit(0)` under test are the real ones and not a copy
#: written in a test.
#:
#: The `opened` line carries `pid=<n>`. R3-M2: the PID-1 harness could
#: only establish PID 1 on the `http` arm, because it keyed off a
#: uvicorn log string (`Started server process [1]`) that `stdio` never
#: emits - so the stdio row read as proven while being unproven.
#: Recording the PID here makes the assertion transport-independent and
#: removes the dependency on a third-party log format. Downstream
#: readers match the substring `opened`, which is unaffected.
MARKER_ENTRY = """
import os
import pathlib
import sys

from fastmcp.server.lifespan import lifespan

from fast_mcp_jobvite.__main__ import main

MARKER = pathlib.Path(sys.argv[1])


@lifespan
async def marker_lifespan(server):
    with MARKER.open("a") as fh:
        fh.write(f"opened pid={os.getpid()}\\n")
        fh.flush()
    try:
        yield {"marker": str(MARKER)}
    finally:
        with MARKER.open("a") as fh:
            fh.write("closed\\n")
            fh.flush()


sys.exit(main(extra_lifespan=marker_lifespan))
"""

GRACE_SECONDS = 20.0


def free_port() -> int:
    """Return a port nothing is listening on, for the HTTP arms."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def clean_env(**extra: str) -> dict[str, str]:
    """Build an environment holding no inherited `JOBVITE_` value.

    `PYTHONDONTWRITEBYTECODE` is propagated deliberately: the mutation
    harness sets it, and a child that writes `.pyc` files can reuse
    stale bytecode for a same-size mutation made inside the same second,
    so the mutant would never run.

    Args:
        **extra: `JOBVITE_` variables for this arm.

    Returns:
        The environment mapping.
    """
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),  # noqa: S108
        "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE", "1"),
    }
    env.update(extra)
    return env


def run_entry(
    cwd: pathlib.Path, env: dict[str, str], timeout: float = 30.0
) -> subprocess.CompletedProcess[str]:
    """Run `python -m fast_mcp_jobvite` to completion.

    Args:
        cwd: Working directory. A tmp_path, so no developer `.env` is
            read.
        env: The environment from `clean_env`.
        timeout: Seconds to wait before failing the arm.

    Returns:
        The completed process, with stdout and stderr captured as text.
    """
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "fast_mcp_jobvite"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def write_marker_entry(tmp_path: pathlib.Path) -> pathlib.Path:
    """Write the marker entry script into a temporary directory."""
    entry = tmp_path / "entry.py"
    entry.write_text(MARKER_ENTRY)
    return entry


#: `prctl(2)`'s `PR_SET_PDEATHSIG`. Linux-only, which this module
#: already is - `interpreter_of` reads `/proc/<pid>/cmdline`.
_PR_SET_PDEATHSIG = 1

#: Distinct exit codes, because `os._exit(1)` from a `preexec_fn` is
#: indistinguishable to the caller from the entry script failing to
#: import - and those need different diagnoses.
_EXIT_NO_LIBC = 100
_EXIT_PRCTL_FAILED = 101
_EXIT_PARENT_ALREADY_GONE = 102


def _load_libc() -> ctypes.CDLL | None:
    """Resolve libc AT IMPORT, before anything forks.

    **`dlopen` after `fork` can deadlock the child.** It takes the
    loader locks, and a lock held by another thread at the moment of
    the fork is held forever in the child, which has only the forking
    thread. This suite IS multi-threaded at spawn time - AnyIO worker
    threads, which `test_shutdown.py` documents as the reason the stdio
    arm needs a forced exit - so calling `ctypes.CDLL` inside the
    `preexec_fn`, as this first shipped, was a hang waiting for a
    schedule. Resolving here moves it before the fork.

    Returns None rather than raising: a failure here would otherwise
    break COLLECTION of every module importing this one, on a machine
    where the only real consequence is that these process tests cannot
    run.
    """
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
    except OSError:
        return None
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong)
    libc.prctl.restype = ctypes.c_int
    return libc


_LIBC = _load_libc()


def _die_with_parent(parent_pid: int, option: int = _PR_SET_PDEATHSIG) -> None:
    """Ask the kernel to SIGKILL this child when `parent_pid` dies.

    **A `try: ... finally: proc.kill()` cannot do this.** No Python
    cleanup runs when the harness itself is SIGKILLed, and that is the
    case that actually happened: the SAME test orphaned a server twice
    in one day, found alive 2h02m and 1h03m later, still holding a port
    and still running out of a worktree that had been deleted. The
    kernel is the only party that can reap a child whose parent was
    never given a chance to.

    **The parent pid is PASSED IN, not assumed to be 1.** The first
    version asked `os.getppid() == 1`, which is wrong in both
    directions: in a container where pytest is itself PID 1 every child
    sees 1 from birth and would die at spawn, and under a
    `PR_SET_CHILD_SUBREAPER` process manager an orphan reparents to the
    subreaper rather than to 1, so the check never fires. Comparing
    against the actual parent is right in both.

    **`option` EXISTS SO THE FAILURE BRANCH CAN BE REACHED, and that is
    its only purpose.** R11-H2 amputated the return check below and the
    whole 868-test suite stayed green: the case that shipped with this
    function asserts only that the guards do NOT fire, which passes
    just as happily against a guard that has been deleted. With the
    option a parameter, a test passes a bogus one, `prctl` returns `-1`
    with `EINVAL`, and the branch is observable. Production callers
    pass `parent_pid` alone and get `PR_SET_PDEATHSIG`; the seam is one
    default argument rather than a knob invented to be mocked.

    Runs between `fork` and `exec` in the child.

    Args:
        parent_pid: `os.getpid()` read in the PARENT, before the fork.
        option: The `prctl(2)` option. Defaults to `PR_SET_PDEATHSIG`,
            which is the only value any caller outside a test passes.
    """
    if _LIBC is None:
        os._exit(_EXIT_NO_LIBC)
    # The return is CHECKED. A silently failed install leaves the child
    # unprotected, which is the whole defect wearing the fix's name.
    if _LIBC.prctl(option, signal.SIGKILL) != 0:
        os._exit(_EXIT_PRCTL_FAILED)
    # The race prctl cannot close by itself: if the parent died in the
    # window between `fork` and this call, the signal has already been
    # delivered to nobody. Re-parenting is the observable.
    if os.getppid() != parent_pid:
        os._exit(_EXIT_PARENT_ALREADY_GONE)


def spawn_marker_server(
    tmp_path: pathlib.Path,
    env: dict[str, str],
    *,
    stdio: bool,
) -> tuple[subprocess.Popen[bytes], pathlib.Path, pathlib.Path]:
    """Spawn the marker entry script and wait for its lifespan.

    Args:
        tmp_path: Working directory for the process.
        env: The environment from `clean_env`.
        stdio: Whether to keep a pipe on stdin. On stdio the server
            reads stdin, and an immediate EOF would shut it down for a
            reason that is not the signal under test.

    Returns:
        The process, the marker path, and the combined-output path.
    """
    entry = write_marker_entry(tmp_path)
    marker = tmp_path / "marker.txt"
    output = tmp_path / "output.txt"
    with output.open("wb") as sink:
        proc = subprocess.Popen(  # noqa: S603
            [sys.executable, str(entry), str(marker)],
            cwd=str(tmp_path),
            env=env,
            stdin=subprocess.PIPE if stdio else subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
            preexec_fn=functools.partial(_die_with_parent, os.getpid()),  # noqa: PLW1509
        )
    deadline = time.time() + GRACE_SECONDS
    while time.time() < deadline:
        if marker.exists() and "opened" in marker.read_text():
            return proc, marker, output
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    proc.kill()
    proc.wait()
    raise AssertionError(
        f"the server never opened its lifespan. output:\n{output.read_text()}"
    )


def interpreter_of(pid: int) -> str:
    """Return argv[0] of a live process from `/proc/<pid>/cmdline`.

    DESIGN.md:1110-1111 requires the shutdown case to resolve the
    **interpreter** PID rather than a wrapper's. Reading the kernel's
    own record is what makes that claim checkable rather than assumed.

    Args:
        pid: The process id.

    Returns:
        The first `NUL`-separated field of the process command line.
    """
    raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    return raw.split(b"\0")[0].decode()


def wait_for_port(host: str, port: int, timeout: float = GRACE_SECONDS) -> bool:
    """Wait until a TCP port accepts a connection."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.05)
    return False
