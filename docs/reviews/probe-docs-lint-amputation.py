#!/usr/bin/env python3
"""Amputation harness for the four behaviour fixes this branch makes.

A probe that passes proves nothing on its own - it has to be shown
failing when the thing it watches is removed. Each row below DELETES one
fix from the tree, re-runs the probe that is supposed to catch it, and
records which rows died. Deleting the behaviour is deliberate:
changing a value has repeatedly left assertions that pass for the
wrong reason.

    A1  the fail-closed REPOINT-EXEMPT read      -> kills rows A, B
    A2  the upstream checker's stderr health check -> kills row E
    A3  the narrowed catch in `_corpus()`        -> kills row C
    A4  the narrowed catch in `drive_to()`       -> kills row F
    A5  NEGATIVE CONTROL: a comment-only edit    -> must kill NOTHING

Every mutation asserts its anchor is unique BEFORE it writes,
asserts the file actually changed after (a `str.replace` that
matches nothing no-ops in silence), and restores from an in-memory
copy in a `finally`. The last row re-runs both probes against the
restored tree, because a harness that leaves its own mutation behind
reads as somebody else's merge.

    uv run --frozen python docs/reviews/probe-docs-lint-amputation.py

Exit 0 = every mutation was caught and the tree came back clean.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

REPOINT = HERE / "repoint-design-citations.py"
STANDARDS = HERE / "check-standards-citations.py"
R6 = HERE / "probe-r6-breaker-reset.py"

PROBE_FAILCLOSED = HERE / "probe-repoint-fail-closed.py"
PROBE_SWALLOW = HERE / "probe-gate-swallowed-exceptions.py"

ORIGINAL: dict[pathlib.Path, str] = {
    p: p.read_text() for p in (REPOINT, STANDARDS, R6)
}
PROBLEMS: list[str] = []


def run_probe(probe: pathlib.Path) -> tuple[int, list[str]]:
    """Run one probe; return its exit code and the rows that FAILED."""
    proc = subprocess.run(
        [sys.executable, str(probe)],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    failed = [
        line.split()[1].rstrip(".")
        for line in proc.stdout.splitlines()
        if " FAIL:" in line
    ]
    return proc.returncode, failed


def amputate(
    name: str,
    path: pathlib.Path,
    old: str,
    new: str,
    probe: pathlib.Path,
    expect: set[str],
) -> None:
    """Delete one behaviour and check the right rows die."""
    before = ORIGINAL[path]
    count = before.count(old)
    assert count == 1, f"{name}: anchor appears {count} times, not once"
    try:
        path.write_text(before.replace(old, new))
        assert path.read_text() != before, f"{name}: the mutation DID NOT LAND"
        rc, failed = run_probe(probe)
        killed = set(failed)
        ok = killed == expect and (rc != 0 if expect else rc == 0)
        print(
            f"########## {name} {'CAUGHT' if ok else 'SURVIVOR'}: "
            f"probe rc={rc}, rows killed = {sorted(killed) or 'NONE'} "
            f"(expected {sorted(expect) or 'NONE'})"
        )
        if not ok:
            PROBLEMS.append(name)
    finally:
        path.write_text(before)
        assert path.read_text() == before, f"{name}: RESTORE FAILED - tree is dirty"


amputate(
    "A1 fail-open REPOINT-EXEMPT read restored",
    REPOINT,
    """        try:
            cited_line = cited_in.read_text().splitlines()[int(m["lineno"]) - 1]
        except (OSError, IndexError, UnicodeDecodeError) as exc:
            unreadable.append(
                f"  UNREADABLE: {m['file']}:{m['lineno']}: "
                f"{type(exc).__name__}: {exc}"
            )
            continue
        if "REPOINT-EXEMPT" in cited_line:
            continue""",
    """        try:
            cited = cited_in.read_text().splitlines()[int(m["lineno"]) - 1]
            if "REPOINT-EXEMPT" in cited:
                continue
        except (OSError, IndexError, UnicodeDecodeError):
            pass""",
    PROBE_FAILCLOSED,
    {"A", "B"},
)

amputate(
    "A2 checker stderr health check deleted",
    REPOINT,
    "    if proc.stderr.strip():\n        raise CheckerFailed(",
    "    if False:\n        raise CheckerFailed(",
    PROBE_FAILCLOSED,
    {"E"},
)

amputate(
    "A3 _corpus() catch widened back to Exception",
    STANDARDS,
    "    except (OSError, CalledProcessError):",
    "    except Exception:  # noqa: BLE001",
    PROBE_SWALLOW,
    {"C"},
)

amputate(
    "A4 drive_to() catch widened back to Exception",
    R6,
    # The bare `except (JobviteUnavailableError, JobviteUpstreamError):`
    # line appears FOUR times in this file, so the anchor carries the
    # call above it. The uniqueness assert caught that on the first run.
    """            await c.request("GET", JOBS_PATH)
        except (JobviteUnavailableError, JobviteUpstreamError):
            pass


async def arm(""",
    """            await c.request("GET", JOBS_PATH)
        except Exception:  # noqa: BLE001
            pass


async def arm(""",
    PROBE_SWALLOW,
    {"F"},
)

amputate(
    "A5 NEGATIVE CONTROL, comment-only edit",
    REPOINT,
    "REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]",
    "REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]  # amputation no-op",
    PROBE_FAILCLOSED,
    set(),
)

print()
for path, text in ORIGINAL.items():
    same = path.read_text() == text
    print(f"  restored {path.name}: {'yes' if same else 'NO - TREE IS DIRTY'}")
    if not same:
        PROBLEMS.append(f"restore:{path.name}")

for probe in (PROBE_FAILCLOSED, PROBE_SWALLOW):
    rc, failed = run_probe(probe)
    print(f"  post-run re-check of {probe.name}: exit={rc} failed={failed or 'none'}")
    if rc != 0:
        PROBLEMS.append(f"post-run:{probe.name}")

print()
if PROBLEMS:
    print(f"  {len(PROBLEMS)} problem(s): {PROBLEMS}")
    raise SystemExit(1)
print("  every amputation was caught, the control survived, the tree is clean.")
raise SystemExit(0)
