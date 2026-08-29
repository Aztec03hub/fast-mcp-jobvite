"""Entry point: logging, transport selection, signal handling, forced exit.

**Logging is configured before anything else is imported** (DESIGN.md:281),
and it goes to **stderr**. On stdio the JSON-RPC channel *is* stdout, so a
single log record written there corrupts the protocol for the rest of the
connection. `logging.basicConfig` defaults to stderr, but the default is the
thing a later import changes, so it is stated.

**The SIGTERM problem, and why the obvious fix is worse than none**
(DESIGN.md:960-1023). Lifespan teardown does not run under SIGTERM, only
SIGINT - verified 3 of 3 with process identity checks and reproduced on the
previous major, filed upstream as PrefectHQ/fastmcp#4927. Docker, Kubernetes
and Cloud Run all stop containers with SIGTERM.

An earlier draft proposed `signal.signal(SIGTERM, signal.getsignal(SIGINT))`.
It is actively dangerous: `getsignal(SIGINT)` returns whatever is installed
at that moment, and a backgrounded process inherits `SIGINT = SIG_IGN`, so
the one-liner installs **"ignore SIGTERM"** - the opposite of the intent. In
a container the process then does not stop on `docker stop` and is SIGKILLed
after the grace period, guaranteeing no teardown at all. `_install_shutdown_handler`
installs an explicit handler instead and never reads ambient state.

**`os._exit(0)` in the `finally` is required on stdio** (DESIGN.md:979-981):
teardown runs there but the process does not die, because a non-daemon AnyIO
worker thread blocks interpreter shutdown - even an explicit `sys.exit(0)`
never completes. Teardown completes before `os._exit`, so skipping atexit
handlers costs nothing we rely on.

**A limit of the shape DESIGN.md:990-1023 mandates, recorded rather than
smoothed over:** because `os._exit(0)` sits in a `finally`, an exception
escaping `mcp.run` also exits **0**, so a crash is indistinguishable from a
clean stop to a supervisor. That is what the frozen design specifies and it
is what is built here. ADR-0018 proposes the change and is **Proposed**, so
it is not applied.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from types import FrameType

logging.basicConfig(
    # stderr, explicitly. stdout is the JSON-RPC channel on stdio.
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from fastmcp.server.lifespan import Lifespan  # noqa: E402

from fast_mcp_jobvite.config import (  # noqa: E402
    ConfigurationError,
    load_settings,
)
from fast_mcp_jobvite.server import build_server  # noqa: E402

logger = logging.getLogger(__name__)

#: Exit status for a refused configuration. Distinct from 1 so a supervisor
#: can tell "this deployment is misconfigured, retrying will not help" from
#: an ordinary failure.
EXIT_CONFIGURATION_REFUSED = 78


def _term(signum: int, frame: FrameType | None) -> None:
    """Turn SIGTERM into the interrupt the framework already unwinds on.

    Do NOT replace this with `signal.getsignal(SIGINT)`: it returns whatever
    is installed at that moment, which is `SIG_IGN` for a backgrounded
    process, and installing that under SIGTERM means the process never stops.

    Args:
        signum: The delivered signal number, supplied by the runtime.
        frame: The interrupted stack frame, supplied by the runtime.

    Raises:
        KeyboardInterrupt: Always. This is the whole mechanism.
    """
    raise KeyboardInterrupt


def _install_shutdown_handler() -> None:
    """Install the explicit SIGTERM handler (DESIGN.md:984-988)."""
    signal.signal(signal.SIGTERM, _term)


def main(*, extra_lifespan: Lifespan | None = None) -> int:
    """Load configuration, select the transport, and serve until stopped.

    **This function does not return on the serving path.** The `finally`
    calls `os._exit(0)`, which DESIGN.md:979-981 requires because a
    non-daemon AnyIO thread blocks interpreter shutdown on stdio. It returns
    a status only on the configuration-refusal path, which happens before
    the handler is installed and before anything is served.

    Args:
        extra_lifespan: A lifespan composed onto the server's own. U4 and U9
            pass their resources here; §8 #18 passes the observable resource
            its assertion needs.

    Returns:
        `EXIT_CONFIGURATION_REFUSED` if configuration was refused.
    """
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        for reason in exc.reasons:
            logger.error("configuration refused: %s", reason)
        return EXIT_CONFIGURATION_REFUSED

    _install_shutdown_handler()
    mcp = build_server(settings, extra_lifespan=extra_lifespan)

    try:
        if settings.mcp_transport == "http":
            logger.info("serving http on %s:%s", settings.mcp_host, settings.mcp_port)
            mcp.run(
                transport="http",
                host=settings.mcp_host,
                port=settings.mcp_port,
                show_banner=False,
            )
        else:
            logger.info("serving stdio")
            mcp.run(transport="stdio", show_banner=False)
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        # DESIGN.md:979-981. Teardown has already completed by here.
        os._exit(0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
