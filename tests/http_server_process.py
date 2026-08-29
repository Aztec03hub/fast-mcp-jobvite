"""Run a `FastMCP` instance over real HTTP, for the duration of a test.

**In-memory transport cannot test any of U9.** `FastMCPTransport` never
builds an HTTP request, so it has no `Authorization` header for
`StaticTokenVerifier` to read, no `X-Request-ID` for
`RequestIdMiddleware` to find, and no access token for
`rate_limit_client_id` to bill. Every behaviour this unit owns lives on
the wire, so the tests put a server on the wire.

**uvicorn in a thread, not a subprocess.** `tests/boot_process.py`
already owns the subprocess shape and uses it for what only a process
can show - exit codes, signals, PID 1. Nothing here needs a process:
these tests assert what a CLIENT observes, and a thread lets the test
hold the server object it is asserting about.

**A free port, never a fixed one.** `free_port` is
`tests/boot_process.py`'s, reused rather than reimplemented: two suites
racing for 8000 is a flake that looks like a real bind failure.
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator
from typing import Any

import uvicorn
from fastmcp import FastMCP

from tests.boot_process import free_port, wait_for_port

#: How long to wait for uvicorn to bind before calling it a failure.
#: Generous on purpose - a tight bound here turns a slow CI runner into
#: a mystery failure in a test about scopes.
STARTUP_TIMEOUT_SECONDS = 20.0


@contextlib.contextmanager
def serve_http(server: FastMCP[Any]) -> Iterator[str]:
    """Serve `server` over HTTP on a free loopback port.

    Args:
        server: The instance to serve.

    Yields:
        The MCP endpoint URL, ready for `StreamableHttpTransport`.

    Raises:
        RuntimeError: If uvicorn did not bind within the timeout. A
            silent yield of an unbound URL would surface as a confusing
            connection error inside whichever assertion ran first.
    """
    port = free_port()
    config = uvicorn.Config(
        server.http_app(),
        host="127.0.0.1",
        port=port,
        log_level="error",
        lifespan="on",
    )
    http = uvicorn.Server(config)
    thread = threading.Thread(target=http.run, daemon=True)
    thread.start()
    try:
        if not wait_for_port("127.0.0.1", port, timeout=STARTUP_TIMEOUT_SECONDS):
            msg = f"uvicorn did not bind 127.0.0.1:{port}"
            raise RuntimeError(msg)
        yield f"http://127.0.0.1:{port}/mcp/"
    finally:
        http.should_exit = True
        thread.join(timeout=STARTUP_TIMEOUT_SECONDS)
