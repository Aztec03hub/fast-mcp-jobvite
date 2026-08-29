#!/usr/bin/env python3
"""Does the locked uvicorn bound a request body? Measured, not read.

**This probe exists because ADR-0029's ruling ends with "I did not
look".** The question it leaves open is whether `uvicorn_config` can
enforce `DESIGN.md:165`'s 1 MiB body cap, which would be cheaper and
more correct than a middleware this repository maintains. The answer
decides whether task #81 is a unit or a one-line config change, so it
is answered by running uvicorn rather than by reading its docs.

**Why a probe and not a sentence in a report.** Prose about a
measurement decays into a claim about one. The locked version moves;
`uvicorn.Config` gains parameters; re-running this file is how the next
reader re-establishes the answer instead of trusting this one.

Two arms, because they fail differently:

1. **`Content-Length: 2 MiB`.** The declared-length case. If uvicorn
   had any body ceiling at all it would fire here first.
2. **Chunked, no `Content-Length`.** The case an attacker uses: a
   framing that never declares a size, so a header check has nothing
   to read.

`h11_max_incomplete_event_size` is set to 1 KiB deliberately - it is
the only `uvicorn.Config` parameter whose name suggests a size ceiling
on an inbound request, and this probe is the positive control that it
is NOT one. It bounds the buffer for an INCOMPLETE h11 event, which is
the request line and headers; body data arrives as complete `Data`
events and is never held against it.

Exit code is the finding: 0 if uvicorn passed both oversized bodies
through to the application (no ceiling), 1 if it refused either (a
ceiling exists and the middleware may be unnecessary).
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from collections.abc import Iterator

import httpx2
import uvicorn
from starlette.types import Receive, Scope, Send

#: The cap `DESIGN.md:165` asks for. This probe sends twice it.
ONE_MEBIBYTE = 1024 * 1024

#: How long to wait for uvicorn to bind before giving up.
STARTUP_TIMEOUT_SECONDS = 10.0


async def counting_app(scope: Scope, receive: Receive, send: Send) -> None:
    """Drain the body and answer with the byte count it actually saw.

    The count is the measurement: if uvicorn bounded anything, the
    application never sees the full 2 MiB, and if it bounded nothing
    the number that comes back is exactly what was sent.
    """
    if scope["type"] != "http":
        return
    total = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            break
        total += len(message.get("body", b""))
        if not message.get("more_body", False):
            break
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": str(total).encode()})


def _free_port() -> int:
    """Bind port 0, read the port the kernel chose, release it."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


def _two_mebibytes_in_chunks() -> Iterator[bytes]:
    """A generator body, which makes httpx use chunked transfer.

    No `Content-Length` reaches the wire for this arm, so anything
    that only reads the header has nothing to read.
    """
    for _ in range(2048):
        yield b"x" * 1024


def main() -> int:
    """Run both arms against a live uvicorn and report what it did."""
    port = _free_port()
    config = uvicorn.Config(
        counting_app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        http="h11",
        # The parameter this probe is the positive control for.
        h11_max_incomplete_event_size=1024,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        print("ABORT: uvicorn did not bind; the probe measured nothing.")
        return 3

    url = f"http://127.0.0.1:{port}/"
    print(f"uvicorn {uvicorn.__version__}, h11_max_incomplete_event_size=1024")
    print(f"the cap DESIGN.md:165 asks for: {ONE_MEBIBYTE} bytes")
    print()
    bounded = False
    try:
        declared = httpx2.post(url, content=b"x" * (2 * ONE_MEBIBYTE), timeout=60)
        print(
            f"  A. Content-Length: {2 * ONE_MEBIBYTE}"
            f" -> HTTP {declared.status_code}, the app saw {declared.text} bytes"
        )
        bounded = bounded or declared.status_code != 200

        chunked = httpx2.post(url, content=_two_mebibytes_in_chunks(), timeout=60)
        print(
            f"  B. chunked, NO Content-Length "
            f" -> HTTP {chunked.status_code}, the app saw {chunked.text} bytes"
        )
        bounded = bounded or chunked.status_code != 200
    finally:
        server.should_exit = True
        thread.join(timeout=STARTUP_TIMEOUT_SECONDS)

    print()
    if bounded:
        print("FINDING: uvicorn REFUSED an oversized body. It has a ceiling -")
        print("         a middleware may be unnecessary. Re-open the question.")
        return 1
    print("FINDING: uvicorn passed BOTH oversized bodies through untouched.")
    print("         There is no request-body ceiling in `uvicorn.Config`, so")
    print("         `uvicorn_config` cannot discharge DESIGN.md:165 and the")
    print("         ASGI middleware seat is the answer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
