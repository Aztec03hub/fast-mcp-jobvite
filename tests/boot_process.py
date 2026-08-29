"""Process helpers for U1's boot and shutdown cases.

**Not a conftest fixture and not a pytest plugin.** IMPLEMENTATION-PLAN.md's
§4 rule keeps `tests/conftest.py` small and U0's; this module is imported
directly by the two U1 test modules instead, so no unit's write set overlaps.

Every arm here runs the **real** entry point in a **real** process. A boot
refusal that is asserted by calling `load_settings()` in-process proves the
validator; it does not prove that the process exits, which is what §8 #10
requires and what a supervisor observes.
"""

from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
import time

#: The entry script the shutdown case runs. It composes an observable
#: resource onto the server's own lifespan through the `extra_lifespan`
#: parameter `server.py` exposes, and calls the **shipped** `main()` - so
#: the handler, the `except KeyboardInterrupt` and the `finally: os._exit(0)`
#: under test are the real ones and not a copy written in a test.
MARKER_ENTRY = """
import pathlib
import sys

from fastmcp.server.lifespan import lifespan

from fast_mcp_jobvite.__main__ import main

MARKER = pathlib.Path(sys.argv[1])


@lifespan
async def marker_lifespan(server):
    with MARKER.open("a") as fh:
        fh.write("opened\\n")
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
    """Build a process environment holding no inherited `JOBVITE_` value.

    `PYTHONDONTWRITEBYTECODE` is propagated deliberately: the mutation
    harness sets it, and a child that writes `.pyc` files can reuse stale
    bytecode for a same-size mutation made inside the same second, so the
    mutant would never run.

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
        cwd: Working directory. A tmp_path, so no developer `.env` is read.
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


def spawn_marker_server(
    tmp_path: pathlib.Path,
    env: dict[str, str],
    *,
    stdio: bool,
) -> tuple[subprocess.Popen[bytes], pathlib.Path, pathlib.Path]:
    """Spawn the marker entry script and wait until its lifespan has opened.

    Args:
        tmp_path: Working directory for the process.
        env: The environment from `clean_env`.
        stdio: Whether to keep a pipe on stdin. On stdio the server reads
            stdin, and an immediate EOF would shut it down for a reason
            that is not the signal under test.

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
    """Return argv[0] of a live process, read from `/proc/<pid>/cmdline`.

    DESIGN.md:1342-1344 requires the shutdown case to resolve the
    **interpreter** PID rather than a wrapper's. Reading the kernel's own
    record is what makes that claim checkable rather than assumed.

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
