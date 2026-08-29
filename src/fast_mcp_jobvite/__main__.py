"""Entry point: logging, transport selection, signal handling, forced exit.

**Logging is configured before anything else is imported** (DESIGN.md:281),
and it goes to **stderr**. On stdio the JSON-RPC channel *is* stdout, so a
single log record written there corrupts the protocol for the rest of the
connection. `logging.basicConfig` defaults to stderr, but the default is the
thing a later import changes, so it is stated.

**There is ONE log stream, and `configure_logging` is the only thing that
configures it.** Before this module configured loguru, `audit.py` and
`services/jobvite_client.py` wrote through loguru while this module
configured stdlib `logging` - a different library - so every audit record
went to loguru's autoinit handler, whose format carries no `{extra}`. The
whole audit event reached the stream as the six-character word
`tool_invocation` and `tool_name`, `request_id` and `transport` appeared
nowhere, in breach of `ai/tool-calling.md:171-179`. The suite passed
throughout because its fixture installed its own sink: correct about the
API, silent about the deployment. `configure_logging` removes the autoinit
handler, adds one serialising stderr sink with `catch=False`, and routes
stdlib records into it through `_InterceptHandler`, so the two libraries
produce one stream in one shape.

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

**`os._exit` in the `finally` is required on stdio** (DESIGN.md:979-981):
teardown runs there but the process does not die, because a non-daemon AnyIO
worker thread blocks interpreter shutdown - even an explicit `sys.exit(0)`
never completes. Teardown completes before `os._exit`, so skipping atexit
handlers costs nothing we rely on.

**The exit status is the one the run earned** (ADR-0018, DESIGN.md:990-1023).
`finally` runs on every exit from the `try`, not only the `KeyboardInterrupt`
path, so a constant `0` would report a bound port, a misconfiguration or an
escaping cancellation as a clean stop, and every supervisor that reads an exit
status would believe it. `os._exit` still runs **unconditionally**, so the stdio
hang above is still closed and nothing about the SIGTERM mitigation changes;
only the constant moves. `70` is `EX_SOFTWARE`, matching the `EX_CONFIG` 78
already used on the refusal path.

**And it is tested BY THE SIDE EFFECT, which it was not before.** ADR-0018
requires a case that forces `mcp.run` to fail for a real reason and reads the
process's exit status, on the same reasoning SS8 #18 applies to teardown; until
that case existed, the discharge was a test asserting that this file's SOURCE
contains the string `os._exit(status)`, which is the weakest possible way to
settle a defect about exit codes.
`test_a_crashing_mcp_run_exits_70_read_from_the_process` binds a port, starts
the HTTP transport on it, and reads the status a
supervisor would read: **measured 70**, with `address already in use` on the
stream and a clean-stop arm measuring 0 on the same construction.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from types import FrameType
from typing import TYPE_CHECKING, TextIO

from loguru import logger as _loguru

if TYPE_CHECKING:  # pragma: no cover - typing only
    from loguru import Record

# A LEAF import, taken before the framework imports on purpose. It pulls in
# `urllib.parse` and nothing of this project's, so it cannot drag the server
# in ahead of the logging configuration it exists to protect.
from fast_mcp_jobvite.utils.redaction import redact_text

#: The one sink. **`serialize=True` and not a `{extra}` format**, decided
#: because `ai/tool-calling.md:171-179` cares that the mandated fields ARRIVE,
#: not that a line is readable. A human-readable format names each field it
#: prints, so a field added to `AuditEvent.to_record()` later - or one whose
#: value contains the format's own separator - is dropped without any run
#: going red: that is H-1 a second time, in a different disguise. `serialize`
#: emits the whole `extra` mapping structurally, so a new field arrives by
#: construction rather than by somebody remembering to widen a format string.
#:
#: `catch=False` (H-2). Loguru handlers default to `catch=True`, which prints
#: `--- End of logging error ---` to stderr and lets `.info()` RETURN
#: NORMALLY. Under that default `audit.emit`'s `except` is unreachable and the
#: `BEFORE_SIDE_EFFECT` branch of DESIGN.md's audit-failure policy - no audit,
#: no write, the branch that stops a second live candidate being emailed -
#: cannot fire in production no matter what the tests say. The policy is only
#: a policy if the failure reaches the code that implements it.
#:
#: `diagnose=False`: loguru's variable-value annotations would put local
#: values into the traceback, and §5.3 treats the log stream as sensitive.
_LOG_LEVEL = "INFO"


def _redact_message(record: Record) -> bool:
    """Redact every record's message at the sink, and never drop one.

    **A containment control, not an allow-list.** Routing stdlib records into
    loguru made a pre-existing production leak visible: `httpx2` logs
    `HTTP Request: GET <url>` at INFO, and the `jobFeed` URL structurally
    carries `api`, `sc` and `companyId` (DESIGN.md:312-316). That line was
    already reaching stderr in the clear through `basicConfig(level=INFO)`;
    the client's own test could not see it because the test installs its own
    loguru sink and the leak travelled through a different library.

    Silencing `httpx2`'s logger would fix the producer we happened to find and
    leave every producer nobody has thought of. Redacting at the one sink
    covers all of them, and it calls `redact_text` rather than reimplementing
    it, so DESIGN.md:312-316's "enforced in one place" still holds.

    Args:
        record: The loguru record, mutated in place before formatting.

    Returns:
        `True` always. This is a redactor, not a filter: dropping a record
        would turn a leak into silence, which is the other way to lose an
        audit trail.
    """
    message = record.get("message")
    if isinstance(message, str):
        record["message"] = redact_text(message)
    return True


def _redact_json(value: object) -> object:
    """Redact every string anywhere inside one decoded JSON document.

    Walks rather than pattern-matching the line, so the redaction can never
    corrupt the JSON: `redact_url` percent-encodes what it reassembles, and a
    URL sitting next to a closing quote in the raw text would have that quote
    swallowed into the redacted parameter value. Redacting the DECODED strings
    and re-encoding keeps the record parseable by construction.

    Args:
        value: A decoded JSON value, or anything nested inside one.

    Returns:
        The same structure with every string redacted. Non-strings - numbers,
        booleans, `None` - are returned unchanged; none of them can carry a
        credential.
    """
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {key: _redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value


def _redact_serialised(line: str) -> str:
    """Redact one serialised record - EVERY field, not just `message`.

    **`_redact_message` above reaches one field and `serialize=True` renders
    several.** Measured at this commit, on a process configured the shipped
    way: a stdlib `logger.exception` whose exception text carried
    `?api=...&sc=...&companyId=...` arrived on stderr with the credentials in
    the clear **twice** - once in `record.exception.value` and once in the
    rendered `text`, which carries the formatted traceback. `_redact_message`
    saw neither, because neither is `record["message"]`.

    `_InterceptHandler` forwards `record.exc_info` for **every** stdlib logger
    in the process, so the producers are not enumerable: any dependency that
    calls `logger.exception` or `logger.error(..., exc_info=True)` reaches
    this. `__main__.main` itself is one (`logger.exception` on the abnormal
    termination path). Naming the producers is the allow-list that let the
    `httpx2` leak sit unseen; this redacts the CONTAINER instead - whatever
    `serialize` rendered, whatever produced it.

    Args:
        line: One serialised record as loguru handed it to the sink,
            newline included.

    Returns:
        The redacted line, newline restored.
    """
    try:
        payload = json.loads(line)
    except ValueError:
        # `serialize=True` makes this unreachable by construction, so the
        # fallback is here to FAIL CLOSED rather than because a case is known:
        # returning `line` unchanged would publish whatever could not be
        # parsed. The text arm can mangle punctuation adjacent to a URL; a
        # mangled line beats a leaked one.
        return redact_text(line)
    return json.dumps(_redact_json(payload)) + "\n"


def _redacting_sink(stream: TextIO) -> object:
    """Build the one sink: redact the serialised record, then write it.

    **The stream is captured HERE, at configuration time**, which is the
    binding `logger.add(sys.stderr, ...)` had and which
    `tests/test_logging_process.py`'s failing-sink arms depend on: they replace
    `sys.stderr` before importing this module and expect the sink to stay on
    the object they installed.

    **The write is flushed explicitly.** A stream sink is flushed by loguru; a
    function sink is not, and an unflushed write to a full disk returns
    normally and raises later at interpreter shutdown - which is exactly the
    failure `catch=False` exists to route into `audit.emit`'s policy
    (DESIGN.md:712-718). Without the flush, H-2's `/dev/full` arm would stop
    measuring anything.

    Args:
        stream: The text stream to write to - `sys.stderr` in production.

    Returns:
        The sink callable to hand to `logger.add`.
    """

    def sink(message: str) -> None:
        stream.write(_redact_serialised(str(message)))
        stream.flush()

    return sink


class _InterceptHandler(logging.Handler):
    """Forward stdlib `logging` records into loguru.

    **The reconciliation of the two logging systems.** `audit.py` and
    `services/jobvite_client.py` write through loguru; `__main__`, uvicorn,
    httpx and the framework write through stdlib `logging`. Two libraries
    formatting independently onto one fd is two record shapes interleaved in
    one file, and no consumer can parse it.

    The alternative - configure both and accept two formats - was rejected:
    it leaves the audit stream's own destination, level and failure behaviour
    determined in two places, and `catch=False` would then apply to only one
    of them. Forwarding gives one sink, one format, and one place where a
    sink failure surfaces.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Re-emit one stdlib record through loguru at the same level."""
        try:
            level: str | int = _loguru.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        _loguru.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    """Install the single log sink, before anything else is imported.

    **Called at module scope below, not from `main()`.** `python -m` and an
    `import fast_mcp_jobvite.__main__` must both get the configured stream:
    a call inside `main()` would leave every record emitted during import
    going to loguru's autoinit handler, which is the handler that has no
    `{extra}` in its format and is exactly what dropped every mandated field.
    """
    # loguru autoinits handler 0 on import, with a format carrying no
    # `{extra}`. Removing it is what closes H-1: an added sink does not
    # replace it, and the default would keep writing field-less duplicates.
    _loguru.remove()
    _loguru.add(
        # stderr, explicitly, through the redacting sink. stdout is the
        # JSON-RPC channel on stdio, and a single log record written there
        # corrupts the protocol.
        #
        # A SINK rather than the bare stream, because `filter=` below reaches
        # `record["message"]` and `serialize` renders more than that field -
        # `record["exception"]` and the formatted `text` among them. Both are
        # kept: the filter cleans the record for any handler, and the sink
        # cleans everything that was actually rendered. Both call
        # `redact_text`, so DESIGN.md:312-316's "enforced in one place" holds -
        # there is one redactor, applied at two depths, not two redactors.
        _redacting_sink(sys.stderr),
        level=_LOG_LEVEL,
        serialize=True,
        catch=False,
        filter=_redact_message,
        backtrace=False,
        diagnose=False,
    )
    # `force=True` replaces any handler an earlier import already installed;
    # without it `basicConfig` is a no-op once anything has configured the
    # root logger, and the stdlib records would keep their own format.
    logging.basicConfig(
        handlers=[_InterceptHandler()],
        level=_LOG_LEVEL,
        force=True,
    )


configure_logging()

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

#: `EX_SOFTWARE` from `sysexits.h`: the serving path ended abnormally. ADR-0018:
#: a crash must not report itself as a clean stop, because Docker restart
#: policies, Kubernetes `restartPolicy` and systemd `Restart=on-failure` all
#: read the exit status and `0` means *do not restart, do not alarm*.
EXIT_SOFTWARE = 70


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
    calls `os._exit(status)`, which DESIGN.md:979-981 requires because a
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

    status = 0
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
    except BaseException:
        logger.exception("the server terminated abnormally")
        status = EXIT_SOFTWARE
        # Never reaches a caller - the `finally` below forces the exit first.
        # It is here so the traceback is not swallowed if that `finally` is
        # ever removed; the logging call is what actually records the failure.
        raise
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        # DESIGN.md:979-981. Teardown has already completed by here, and the
        # call is unconditional so the stdio hang stays closed (ADR-0018).
        os._exit(status)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
