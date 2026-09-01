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

Every mutation checks its anchor is unique BEFORE it writes, checks the
file actually changed after (a `str.replace` that matches nothing no-ops
in silence), and restores from an in-memory copy in a `finally`. The
last row re-runs both probes against the restored tree, because a
harness that leaves its own mutation behind reads as somebody else's
merge.

    uv run --frozen python docs/reviews/probe-docs-lint-amputation.py

Exit 0 = every mutation was caught and the tree came back clean.

**THIS IS A GATING PROBE, NOT A ONE-SHOT, and it says so because the
alternative has already cost this file.** It is wired in `ci.yml`. Any
probe here that is deliberately unwired must declare that in its own
docstring, as `classify-w505.py` does - an undeclared unwired probe
cannot be told from an overlooked one, and this one rotted for exactly
that reason.

**R12-H1: IT WAS DEAD FROM `449968f` TO `dad014e` AND NOTHING NOTICED.**
A1's anchor quoted this two-line f-string out of
`repoint-design-citations.py`:

    f"  UNREADABLE: {m['file']}:{m['lineno']}: "
    f"{type(exc).__name__}: {exc}"

`449968f` reflowed it onto one line. Measured against the blobs: the
anchor occurs once at `d5340b7`, zero times at `449968f`, zero at
`dad014e`. Two separate defects fell out of one reflow, and both are
fixed here:

  1. **The anchor was reflowable.** A1 now anchors on the `continue`
     that ENDS the except block plus the `if` line under it - three
     short lines no formatter rewraps - and mutates the `continue`
     rather than the message. Never anchor on a wrapped expression.
  2. **One stale anchor took the whole file down.** `amputate()` used
     `assert`, so A1 raising meant A2, A3, A4 and the A5 NEGATIVE
     CONTROL never ran at all, and the closing tree-clean re-check never
     ran either. A dead row is now a recorded PROBLEM and the harness
     continues. **The restore check stays an `assert`** - a mutation
     left in the tree is the one failure that must stop everything.
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

ORIGINAL: dict[pathlib.Path, str] = {p: p.read_text() for p in (REPOINT, STANDARDS, R6)}
PROBLEMS: list[str] = []


def run_probe(probe: pathlib.Path) -> tuple[int, list[str], str]:
    """Run one probe; return exit code, FAILED rows, and its stdout.

    The stdout is returned rather than discarded because a caller that
    reports `exit=1 failed=none` has thrown away the only thing that
    could explain the exit.
    """
    proc = subprocess.run(
        [sys.executable, str(probe)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    failed = [
        line.split()[1].rstrip(".")
        for line in proc.stdout.splitlines()
        if " FAIL:" in line
    ]
    return proc.returncode, failed, proc.stdout


def amputate(
    name: str,
    path: pathlib.Path,
    old: str,
    new: str,
    probe: pathlib.Path,
    expect: set[str],
) -> None:
    """Delete one behaviour and check the right rows die.

    A dead anchor is RECORDED and skipped, never raised: raising took
    four rows and a negative control down with it for 45 commits (see
    the module docstring, R12-H1).
    """
    before = ORIGINAL[path]
    count = before.count(old)
    if count != 1:
        print(
            f"########## {name} DEAD ROW: its anchor appears {count} time(s) "
            f"in {path.name}, not once. The row did NOT run - a stale anchor "
            "is a defect in this harness, not a pass."
        )
        PROBLEMS.append(f"anchor:{name}")
        return
    try:
        path.write_text(before.replace(old, new))
        if path.read_text() == before:
            print(f"########## {name} DEAD ROW: the mutation DID NOT LAND")
            PROBLEMS.append(f"did-not-land:{name}")
            return
        rc, failed, _ = run_probe(probe)
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


# A1 - THE FAIL-CLOSED READ FAILS OPEN AGAIN.
#
# The `continue` that ends the except block is what stops an UNREADABLE
# citation reaching the repointer. Replacing it with `cited_line = ""`
# lets an unreadable line fall through to the exemption test, where the
# empty string is not exempt, and it gets repointed - which is the
# b0e2e19 defect exactly: "unknown" resolving to "not exempt, go ahead".
#
# THE ANCHOR IS THREE SHORT LINES ON PURPOSE - a bare `)`, a bare
# `continue`, and a 48-character `if`. None of them is a wrapped
# expression, so `ruff format` has nothing to rewrap. Anchoring on the
# f-string above them is what killed this row at 449968f. Verified
# unique: the three-line anchor occurs once, while the indented
# `continue` alone occurs three times in that file.
amputate(
    "A1 fail-open REPOINT-EXEMPT read restored",
    REPOINT,
    """            )
            continue
        if "REPOINT-EXEMPT" in cited_line:""",
    """            )
            cited_line = ""
        if "REPOINT-EXEMPT" in cited_line:""",
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
    rc, failed, detail = run_probe(probe)
    print(f"  post-run re-check of {probe.name}: exit={rc} failed={failed or 'none'}")
    if rc != 0:
        PROBLEMS.append(f"post-run:{probe.name}")
        # `exit=1 failed=none` IS THE WORST THING THIS CAN PRINT, and it
        # printed it. A non-zero exit with no row named says only that
        # something went wrong somewhere, and the output that would say
        # WHAT was captured and thrown away one line above.
        #
        # PROBE_FAILCLOSED's own source already calls this out - a
        # runner produced `exit=1 failed=none` once before and it was
        # fixed for the AssertionError path. It came back through a
        # different path, and cost a whole CI round to see, because the
        # harness reports a verdict it will not evidence.
        #
        # So on failure the probe's own words are printed. Diagnosing
        # from a summary is diagnosing from a paraphrase.
        for line in detail.strip().splitlines()[-12:]:
            print(f"      | {line}")

print()
if PROBLEMS:
    print(f"  {len(PROBLEMS)} problem(s): {PROBLEMS}")
    raise SystemExit(1)
print("  every amputation was caught, the control survived, the tree is clean.")
raise SystemExit(0)
