#!/usr/bin/env python3
"""Advisory-expiry owner. DESIGN.md:1454-1473, step 3 and step 4 only.

WHY THIS EXISTS. `pip-audit` fails on ANY advisory: it has no severity
threshold, so one advisory anywhere in the transitive tree turns a required
check red and blocks every merge, including the merge that fixes it. We
pinned `fastmcp==4.0.0b4` and `mcp==2.1.1` deliberately (B72), so we should
expect advisories and owe them a sanctioned response - because the
unsanctioned response is a blanket ignore, which is the silent suppression
the design forbids and which nobody ever removes.

`pip-audit` has **no expiry concept and no `pyproject.toml` ignore section of
its own**. That gap is the entire reason this script exists. It reads
`[tool.fast-mcp-jobvite.advisory-ignores]`, emits the `--ignore-vuln` flags
`pip-audit` actually takes, and exits non-zero on any expired entry, so an
ignore cannot outlive its justification by drifting.

**THE TABLE IS THE SINGLE SOURCE FOR BOTH THE FLAGS AND THE EXPIRY.** Nothing
here hand-maintains a second list of ids beside it. Two lists that must agree
is the defect DESIGN.md:1469-1471 names, and it fails by going silently stale.

WHAT THIS DOES NOT DO, stated because a control trusted for the wrong thing is
worse than no control. **Step 1 of the policy - reachability - is human
judgement written down, and it is NOT here** (DESIGN.md:1456-1459). This
script cannot tell whether our code reaches a vulnerable path. It enforces the
SHAPE of a recorded judgement: that one was made, was written down, named a
single advisory, and carries an expiry that has not passed. A well-formed
entry with a dishonest `reason` passes this gate cleanly.

THE FOUR FIELDS a legal entry must carry (DESIGN.md:1462-1467):

  id      the advisory id. Required and non-blank. An entry without one is a
          BLANKET ignore - it suppresses every future advisory, not just this
          one - and step 4 forbids it outright.
  date    the date the judgement was recorded. Required, because the 30-day
          budget is measured FROM it.
  reason  a written reason the advisory is unreachable. Required and
          non-blank.
  expires the expiry. Required, no more than 30 days after `date`, and not in
          the past.

WHY THE 30 DAYS IS MEASURED FROM `date` AND NOT FROM NOW. Measured from now,
the budget would refill on every CI run and an entry could sit legal forever,
which is the exact drift the expiry exists to stop. Measured from `date` the
budget is fixed when the judgement is made and cannot be extended without
editing the recorded date, which is visible in a diff.

FAIL-CLOSED. Exit 0 = every entry legal, flags on stdout. Exit 1 = an entry
was refused. Exit 2 = the gate itself could not run. A control that fails open
is worse than none, because it is trusted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MAX_IGNORE_DAYS = 30
"""DESIGN.md:1466 - `an expiry date no more than 30 days out`."""

TABLE_PATH = ("tool", "fast-mcp-jobvite", "advisory-ignores")
"""The single source. Nothing else in this file names an advisory id."""

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_CANNOT_RUN = 2


class AdvisoryTableError(Exception):
    """The table could not be read or is not shaped like a table."""


def _as_date(value: Any, field: str, where: str) -> dt.date:  # noqa: ANN401
    """Coerce a TOML value to a date.

    TOML parses a bare `2026-08-28` to `datetime.date` natively; a quoted one
    arrives as `str`. Both are accepted, anything else is refused rather than
    guessed at.

    Args:
        value: The raw value read from the table.
        field: The field name, for the refusal message.
        where: Which entry this is, for the refusal message.

    Returns:
        The value as a date.

    Raises:
        ValueError: The value is not a date and cannot be read as one.
    """
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError as exc:
            msg = f"{where}: {field} is not an ISO date: {value!r}"
            raise ValueError(msg) from exc
    msg = f"{where}: {field} is not a date: {value!r}"
    raise ValueError(msg)


def load_entries(pyproject: Path) -> list[Any]:
    """Read the ignore table out of `pyproject.toml`.

    Args:
        pyproject: Path to the manifest holding the table.

    Returns:
        The `entries` list, empty if the table is absent.

    Raises:
        AdvisoryTableError: The file is unreadable, is not valid TOML, or the
            table is not shaped as expected.
    """
    try:
        raw = pyproject.read_bytes()
    except OSError as exc:
        msg = f"cannot read {pyproject}: {exc}"
        raise AdvisoryTableError(msg) from exc
    try:
        doc: Any = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        msg = f"cannot parse {pyproject}: {exc}"
        raise AdvisoryTableError(msg) from exc

    for key in TABLE_PATH:
        if not isinstance(doc, dict) or key not in doc:
            return []
        doc = doc[key]
    if not isinstance(doc, dict):
        msg = f"[{'.'.join(TABLE_PATH)}] is not a table"
        raise AdvisoryTableError(msg)

    entries = doc.get("entries", [])
    if not isinstance(entries, list):
        msg = f"[{'.'.join(TABLE_PATH)}] entries is not an array"
        raise AdvisoryTableError(msg)
    return entries


def check_entries(
    entries: Sequence[Any],
    now: dt.date,
) -> tuple[list[str], list[str]]:
    """Validate every entry and derive the flags from the ones that pass.

    The clock is a PARAMETER, never read inside. A test that computes its
    fixture dates from a runtime clock and compares them against a runtime
    clock passes on any implementation, so the boundary cases here are only
    real boundaries if the caller pins both.

    Args:
        entries: The raw `entries` array from the table.
        now: The date to judge expiry against.

    Returns:
        A `(flags, refusals)` pair. `flags` holds the `--ignore-vuln` pairs
        for the entries that passed, derived from the same table rows that
        were validated. `refusals` holds one message per illegal entry.
    """
    flags: list[str] = []
    refusals: list[str] = []

    for index, entry in enumerate(entries):
        where = f"entry {index}"
        if not isinstance(entry, dict):
            refusals.append(f"{where}: not a table")
            continue

        advisory_id = entry.get("id")
        if not isinstance(advisory_id, str) or not advisory_id.strip():
            refusals.append(
                f"{where}: no advisory id - a BLANKET ignore, forbidden by "
                f"DESIGN.md:1472-1473"
            )
            continue
        where = f"entry {index} ({advisory_id})"

        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            refusals.append(f"{where}: no written reason the advisory is unreachable")
            continue

        if "expires" not in entry:
            refusals.append(
                f"{where}: no expiry - an ignore with no expiry never expires"
            )
            continue
        if "date" not in entry:
            refusals.append(f"{where}: no date - the 30-day budget is measured from it")
            continue

        try:
            expires = _as_date(entry["expires"], "expires", where)
            recorded = _as_date(entry["date"], "date", where)
        except ValueError as exc:
            refusals.append(str(exc))
            continue

        budget = (expires - recorded).days
        if budget > MAX_IGNORE_DAYS:
            refusals.append(
                f"{where}: expiry is {budget} days after {recorded.isoformat()}, "
                f"more than the {MAX_IGNORE_DAYS} DESIGN.md:1466 allows"
            )
            continue

        if expires < now:
            refusals.append(
                f"{where}: expired {expires.isoformat()} (today {now.isoformat()}) "
                f"- re-assess reachability or fix it; do not extend the date"
            )
            continue

        flags.extend(["--ignore-vuln", advisory_id])

    return flags, refusals


def main(argv: Sequence[str] | None = None) -> int:
    """Run the gate.

    Args:
        argv: Command line arguments, defaulting to `sys.argv[1:]`.

    Returns:
        0 if every entry is legal, 1 if any was refused, 2 if the gate could
        not run.
    """
    parser = argparse.ArgumentParser(
        description="Advisory-expiry gate. DESIGN.md:1454-1473."
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "pyproject.toml",
        help="the manifest holding the ignore table",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="ISO date to judge expiry against; defaults to today in UTC. "
        "Exists so the boundary cases can be tested against a pinned clock.",
    )
    args = parser.parse_args(argv)

    if args.now is None:
        now = dt.datetime.now(dt.UTC).date()
    else:
        try:
            now = dt.date.fromisoformat(args.now)
        except ValueError:
            print(f"advisory gate: --now is not an ISO date: {args.now!r}")
            return EXIT_CANNOT_RUN

    try:
        entries = load_entries(args.pyproject)
    except AdvisoryTableError as exc:
        print(f"advisory gate: {exc}")
        return EXIT_CANNOT_RUN

    flags, refusals = check_entries(entries, now)

    if refusals:
        for refusal in refusals:
            print(f"advisory gate: REFUSED {refusal}")
        print(
            f"advisory gate: {len(refusals)} illegal entry/entries; no flags emitted."
        )
        return EXIT_REFUSED

    if flags:
        print(" ".join(flags))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
