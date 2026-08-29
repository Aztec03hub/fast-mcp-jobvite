"""What the PROCESS actually writes, and what happens when its sink fails.

**Every assertion in this module observes a real process's real stream.** The
suite already had audit tests, they were correct about the API, and they were
silent about the deployment: each installed its own loguru sink and read
`record["extra"]` out of it. A sink a test invents is a real loguru stream -
just not the one the server writes to - so it passed unchanged while nothing
in `src/` configured loguru at all and every mandated field
(`ai/tool-calling.md:171-179`) was dropped on the way to the real handler.

So these arms spawn the entry point in a subprocess, the way
`tests/boot_process.py` does, and read what came back off its file
descriptors:

- **H-1** asserts `tool_name`, `request_id` and `transport` are IN the bytes
  the process wrote, parsed as the JSON the shipped sink emits.
- **H-2** makes the process's OWN sink fail - stderr redirected to
  `/dev/full`, which is what a full disk does to a write - rather than making
  `bind()` raise, which is not what fails when a disk fills. Loguru handlers
  default to `catch=True` and swallow it, so before `catch=False` the
  `BEFORE_SIDE_EFFECT` branch of DESIGN.md:712-718 could not fire at all.
- Each failing-sink arm is paired with the SAME script against an ordinary
  file, because "the call raised" proves nothing if the call raises anyway.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any

from tests.boot_process import clean_env, run_entry

#: Emit one complete audit event from a process configured the shipped way.
#:
#: `import fast_mcp_jobvite.__main__` and not a `logger.add` of its own: the
#: configuration under test is the one `python -m` runs, and a script that
#: configured its own sink would be the defect this module exists to close.
EMIT_ENTRY = """
import fast_mcp_jobvite.__main__  # noqa: F401 - configures the one log sink

from fast_mcp_jobvite.audit import AuditPhase, Transport, audit_scope, emit

with audit_scope(
    "search_jobs",
    Transport.STDIO,
    arguments={"query": "engineer", "candidate_email": "ada@example.invalid"},
) as event:
    emit(event, AuditPhase.READ)
"""

#: Emit with the process's stderr pointed at a device that fails every write.
#:
#: `sys.stderr` is replaced BEFORE `__main__` is imported, because
#: `configure_logging` binds the stream object it is given at configuration
#: time; swapping it afterwards would leave the sink on the original fd and
#: the arm would prove nothing.
#:
#: The outcome goes to a FILE. stderr is the thing under test and stdout is
#: the JSON-RPC channel, so neither can carry the result.
FAILING_SINK_ENTRY = """
import json
import os
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1])
PHASE_NAME = sys.argv[2]
SINK_PATH = sys.argv[3]

sink = open(SINK_PATH, "w")
os.dup2(sink.fileno(), 2)
sys.stderr = sink

import fast_mcp_jobvite.__main__  # noqa: F401 - configures the one log sink

from fast_mcp_jobvite.audit import AuditPhase, Transport, audit_scope, emit

phase = AuditPhase(PHASE_NAME)
outcome = {}
try:
    with audit_scope("create_candidate", Transport.STDIO, arguments={}) as event:
        outcome = {"raised": None, "warnings": emit(event, phase)}
except BaseException as exc:
    outcome = {"raised": type(exc).__name__, "detail": str(exc)}
OUT.write_text(json.dumps(outcome))

# Put stderr back on a device that accepts writes before the interpreter
# shuts down. CPython flushes stderr at exit and reports a FAILURE TO FLUSH
# as exit status 120, so without this every arm below would exit 120 for a
# reason that has nothing to do with the branch under test - a status that
# looks exactly like the script having crashed.
devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull, 2)
sys.stderr = open(os.devnull, "w")
"""


def _run_script(
    tmp_path: pathlib.Path, source: str, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a script in a real child process, with no inherited JOBVITE_ value."""
    script = tmp_path / "entry.py"
    script.write_text(source)
    return subprocess.run(  # noqa: S603
        [sys.executable, str(script), *args],
        cwd=str(tmp_path),
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _serialised_records(stream: str) -> list[dict[str, Any]]:
    """Parse the shipped sink's output: one JSON object per line."""
    records = []
    for line in stream.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            records.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return records


# ---------------------------------------------------------------------------
# H-1: the mandated fields reach the stream the process actually writes to.
# ---------------------------------------------------------------------------


def test_the_process_writes_the_mandated_audit_fields(
    tmp_path: pathlib.Path,
) -> None:
    """`ai/tool-calling.md:171-179`, asserted against the process's own stderr.

    The measured failure this replaces: the whole event arrived as
    `... | INFO | __main__:<module>:2 - tool_invocation`, with `tool_name`,
    `request_id` and `transport` nowhere in the line.
    """
    result = _run_script(tmp_path, EMIT_ENTRY)
    assert result.returncode == 0, result.stderr

    records = _serialised_records(result.stderr)
    # POSITIVE half first: the process wrote SOMETHING the shipped sink shaped.
    # Against a silent stream every field assertion below would be about an
    # empty list, and `all(...)` over nothing is True.
    assert records, (
        f"the process emitted no serialised record at all: {result.stderr!r}"
    )

    audit_records = [
        record
        for record in records
        if record.get("record", {}).get("message") == "tool_invocation"
    ]
    assert len(audit_records) == 1, f"expected exactly one audit record: {records}"
    extra = audit_records[0]["record"]["extra"]

    assert extra["tool_name"] == "search_jobs"
    assert extra["transport"] == "stdio"
    assert isinstance(extra["request_id"], str) and extra["request_id"]
    assert extra["result_status"] == "success"
    assert isinstance(extra["latency_ms"], float)
    # The stdio attribution marker, and never the literal "global".
    assert extra["caller_attribution"] == "unavailable:stdio-has-no-caller-token"
    assert "global" not in extra["caller_attribution"]
    # And the redaction happened on the way in, so it is what REACHED the
    # stream and not something a fixture applied afterwards.
    assert extra["arguments"]["candidate_email"] == "[REDACTED:str]"


def test_python_dash_m_gets_the_same_configured_sink(
    tmp_path: pathlib.Path,
) -> None:
    """The module identity gap, closed by measurement rather than by reasoning.

    `python -m fast_mcp_jobvite` executes `__main__.py` as the module named
    `__main__`, which is a DIFFERENT module object from the one the arm above
    imports. Same source, so the same configuration runs - but that is an
    inference, and this asserts it instead: the refusal path's own log line
    comes back as a serialised record with the stdlib logger's name in it,
    which is only true if `configure_logging` ran AND `_InterceptHandler` is
    carrying stdlib records into the same sink.
    """
    result = run_entry(tmp_path, clean_env(JOBVITE_TOOLS="not_a_tool"))
    assert result.returncode != 0

    records = _serialised_records(result.stderr)
    assert records, f"python -m wrote no serialised record: {result.stderr!r}"
    refusals = [
        record
        for record in records
        if "configuration refused" in record.get("record", {}).get("message", "")
    ]
    assert refusals, f"the refusal line was not serialised: {result.stderr!r}"
    # It came through the intercept, not through a second stdlib handler
    # writing its own format to the same fd.
    assert refusals[0]["record"]["name"] == "logging"
    assert "not_a_tool" in refusals[0]["record"]["message"]


# ---------------------------------------------------------------------------
# H-2: the failure policy fires because the SINK fails, not because bind does.
# ---------------------------------------------------------------------------


def test_a_failing_sink_fails_the_call_before_the_side_effect(
    tmp_path: pathlib.Path,
) -> None:
    """DESIGN.md:712-713, reached through a real write failure.

    `/dev/full` returns ENOSPC on every write, which is what a full disk does
    - and a full disk is the failure this branch was written for. The previous
    arm raised from `bind()`, which is not a thing that fails when a disk
    fills, and U3's own A1 amputation confirmed the gap: deleting `emit()`
    entirely left `test_arm1_before_the_side_effect_the_call_fails` green.
    """
    outcome = tmp_path / "outcome.json"
    result = _run_script(
        tmp_path,
        FAILING_SINK_ENTRY,
        str(outcome),
        "before_side_effect",
        "/dev/full",
    )
    assert result.returncode == 0, result.stdout
    recorded = json.loads(outcome.read_text())
    assert recorded["raised"] == "AuditWriteError"
    assert "the call was not performed" in recorded["detail"]


def test_the_same_script_against_a_writable_sink_does_not_fail(
    tmp_path: pathlib.Path,
) -> None:
    """The positive control for the arm above, on the SAME construction.

    A test that asserts "the call raised" proves nothing unless the identical
    script leaves it alone when the sink works. This also re-proves H-1 on the
    write path: the record that lands in the file carries the mandated fields.
    """
    outcome = tmp_path / "outcome.json"
    sink = tmp_path / "stderr.log"
    result = _run_script(
        tmp_path,
        FAILING_SINK_ENTRY,
        str(outcome),
        "before_side_effect",
        str(sink),
    )
    assert result.returncode == 0, result.stdout
    recorded = json.loads(outcome.read_text())
    assert recorded["raised"] is None
    assert recorded["warnings"] == []

    records = _serialised_records(sink.read_text())
    assert len(records) == 1
    assert records[0]["record"]["extra"]["tool_name"] == "create_candidate"


def test_a_failing_sink_on_a_read_does_not_fail_the_read(
    tmp_path: pathlib.Path,
) -> None:
    """DESIGN.md:714-715: a read is recoverable, losing the tool is worse.

    This arm is why `_warn_on_stderr` is best effort. The one log sink IS
    stderr, so the failure that kills the audit write kills the report of it
    too, and an escaping OSError would fail the read that the policy says must
    continue.
    """
    outcome = tmp_path / "outcome.json"
    result = _run_script(
        tmp_path, FAILING_SINK_ENTRY, str(outcome), "read", "/dev/full"
    )
    assert result.returncode == 0, result.stdout
    recorded = json.loads(outcome.read_text())
    assert recorded["raised"] is None
    assert recorded["warnings"] == []


def test_a_failing_sink_after_a_write_returns_a_warning_not_an_error(
    tmp_path: pathlib.Path,
) -> None:
    """DESIGN.md:716-727: success with a warning, never an error.

    An error makes the model retry, and a retry emails a second live human.
    Asserted against a real sink failure, so it is the branch running and not
    a fake exception routed into it.
    """
    outcome = tmp_path / "outcome.json"
    result = _run_script(
        tmp_path, FAILING_SINK_ENTRY, str(outcome), "after_write", "/dev/full"
    )
    assert result.returncode == 0, result.stdout
    recorded = json.loads(outcome.read_text())
    assert recorded["raised"] is None
    assert len(recorded["warnings"]) == 1
    warning = recorded["warnings"][0]
    assert "Do not retry" in warning
    assert "create_candidate" in warning


#: A stdlib log record carrying the credential-bearing feed URL, emitted from
#: a process configured the shipped way. `httpx2` emits this exact shape at
#: INFO for every request, and DESIGN.md:312-316 classifies the `jobFeed` URL
#: as sensitive because it structurally carries `api`, `sc` and `companyId`.
LEAK_ENTRY = """
import logging

import fast_mcp_jobvite.__main__  # noqa: F401 - configures the one log sink

logging.getLogger("some.third.party").info(
    "HTTP Request: GET https://api.jobvite.com/v1/jobFeed"
    "?api=LEAKKEY-not-a-real-credential&sc=LEAKSECRET-not-a-real-credential"
    '&companyId=LEAKCOMPANY "HTTP/1.1 200 OK"'
)
"""


def test_a_third_party_log_line_is_redacted_at_the_sink(
    tmp_path: pathlib.Path,
) -> None:
    """The leak routing stdlib records into loguru made visible.

    `httpx2` logs the request URL at INFO through stdlib `logging`, and
    `basicConfig(level=INFO)` was already writing it to stderr in the clear.
    `tests/test_jobvite_client.py`'s log-redaction case could not see it: that
    case installs its own loguru sink, and the leak travelled through the
    other library entirely.

    **The producer here is deliberately not `httpx2`.** Naming the library we
    happened to find would be an allow-list over producers, and the one that
    matters is the one nobody has thought of yet. Redaction is at the sink, so
    any producer is covered, and this arm asserts that by using a logger name
    no dependency owns.
    """
    result = _run_script(tmp_path, LEAK_ENTRY)
    assert result.returncode == 0, result.stderr

    records = _serialised_records(result.stderr)
    # POSITIVE half: the line really was emitted. Against a process that
    # logged nothing, every absence below would pass on silence.
    emitted = [
        record
        for record in records
        if "jobFeed" in record.get("record", {}).get("message", "")
    ]
    assert emitted, f"the third-party line was never logged: {result.stderr!r}"

    # ABSENCE half, computed as a bool first so a red run prints no credential.
    whole = result.stderr
    leaked = [
        needle
        for needle in (
            "LEAKSECRET-not-a-real-credential",
            "LEAKKEY-not-a-real-credential",
            "LEAKCOMPANY",
        )
        if needle in whole
    ]
    assert not leaked, f"{len(leaked)} of 3 credentials survived to the stream"
