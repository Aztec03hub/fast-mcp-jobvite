"""Task #15: does an exception's text reach the serialized sink unredacted?

    uv run --frozen python scripts/probe-exception-redaction.py

Exits 0 if the sink redacted the planted secrets, 1 if they reached the stream in
the clear. **At the time of writing it exits 1**, which is the finding.

WHY THIS IS A SCRIPT AND NOT A PARAGRAPH. The fourth audit-logging defect - httpx2
logging the jobFeed URL at INFO in the clear - was invisible for exactly one
reason: every check looked at a sink the checker configured, not at the sink the
process actually writes to. A prose note saying "record['exception'] looks
unredacted" would decay into a claim about a measurement nobody can repeat. This
runs.

THE MECHANISM. `configure_logging()` installs one stderr sink with
`serialize=True`, which renders `record["message"]` AND `record["exception"]`.
`_redact_message` assigns only `record["message"]`. Two producers reach the
exception field:

  1. Our own `__main__.py`'s `logger.exception("the server terminated
     abnormally")` - anything that propagates that far.
  2. `_InterceptHandler.emit`, which forwards EVERY stdlib record with
     `exception=record.exc_info`. That is every third-party library in the
     process, including the one whose INFO-level logging was the fourth defect.

WHAT THIS DOES NOT SHOW, and the distinction is the honest part: it proves the
FIELD is unredacted, using planted secrets. It does not prove that a real Jobvite
credential reaches an exception message today. `diagnose=False` and
`backtrace=False` are set, so loguru renders neither local variable values nor
extended frames - which bounds the exposure to the exception's own text and the
source line that raised it. Whether a live credential lands in that text is a
separate question about the producers, not about this sink.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import textwrap

#: Shaped like a real jobFeed URL, because that is the string the fourth defect
#: was actually leaking. The tokens are nonsense; the SHAPE is the fixture.
SECRET_URL = "https://api.jobvite.com/api/v2/job?api=PROBEKEY123&sc=PROBECOMPANY"  # noqa: S105
TOKENS = ("PROBEKEY123", "PROBECOMPANY")

CHILD = f"""
import logging
from loguru import logger
from fast_mcp_jobvite.__main__ import configure_logging

configure_logging()
SECRET = {SECRET_URL!r}

# Producer 1: our own code path.
try:
    raise RuntimeError(f"connection failed to {{SECRET}}")
except RuntimeError:
    logger.exception("the server terminated abnormally")

# Producer 2: any third-party library, forwarded by _InterceptHandler.
try:
    raise ConnectionError(f"could not reach {{SECRET}}")
except ConnectionError:
    logging.getLogger("some.third.party").error("upstream failed", exc_info=True)
"""


def main() -> int:
    # A REAL CHILD PROCESS. Configuring logging in-process and reading a fixture's
    # sink is the exact idiom that hid this defect class twice.
    proc = subprocess.run(  # noqa: S603 - the child source is a literal in this file
        [sys.executable, "-c", textwrap.dedent(CHILD)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 and not proc.stderr:
        print(f"the probe child died with no output (rc={proc.returncode})")
        return 2

    written = proc.stderr
    leaked = [t for t in TOKENS if t in written]

    print(f"redaction markers in the stream: {written.count('REDACTED')}")
    for token in TOKENS:
        print(f"  {token:<14} {'LEAKED' if token in written else 'redacted'}")

    if not leaked:
        print("\nOK: the sink redacted the exception field.")
        return 0

    for line in written.splitlines():
        if leaked[0] in line:
            i = line.index(leaked[0])
            print(f"\nfirst leak site:\n  ...{line[max(0, i - 100) : i + 40]}...")
            break

    print(
        "\nFINDING: the exception field reached the stream in the clear.\n"
        "  Fix: redact record['exception'] at the same point as record['message'],\n"
        "  rather than enumerating which producers are believed to be safe."
    )
    return 1


if __name__ == "__main__":
    # Keep THIS process quiet; the child is the subject.
    logging.disable(logging.CRITICAL)
    sys.exit(main())
