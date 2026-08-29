"""Boundary normalisation for Jobvite's own contract hazards (§9).

**This module exists because §9 names four asymmetries and says each is
"normalised at the boundary".** A normaliser per call site is how one
concept acquires two spellings, so every conversion lives here and
every caller imports it.

**Each conversion runs in BOTH directions**, and that is deliberate
rather than symmetry for its own sake. This unit reads, so it only
needs response -> tool. U10 writes, so it needs tool -> request. A
one-way converter shipped now is a converter U10 has to write a second
half of, beside the first, in a different file - which is exactly the
two-lists defect `models/fencing.py` exists to avoid one layer up.

**The `eId`/`EId` asymmetry is JOBVITE'S, NOT OURS**
(`JOBVITE-CONTRACT.md:321`, DESIGN.md:1379-1380). Reads return `eId`;
the create response returns `EId`. **It looks like a typo and is not**,
which is why the two spellings are separate named constants: a
refactor that tidies them into one has to delete an assertion rather
than merely edit a literal. DESIGN.md:1353 puts it as "the kind of wart
a well-meaning normalisation removes".
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from typing import Any, Final

#: Jobvite's key for an identifier **on a read**
#: (`JOBVITE-CONTRACT.md:244`). Lowercase `e`.
ID_KEY_READ: Final = "eId"

#: Jobvite's key for the same identifier **on the create response**
#: (`JOBVITE-CONTRACT.md:318-321`). Capital `E`.
#:
#: NOT A TYPO. §8 #24 requires this asymmetry pinned so a later
#: refactor cannot tidy it into a bug. Both refer to the same
#: identifier space, so a shared model normalises them onto one
#: attribute - and the two constants stay two.
ID_KEY_WRITE: Final = "EId"

#: The date spelling the REQUEST side takes
#: (`JOBVITE-CONTRACT.md:233`, `dateFormat=yyyy-MM-dd`). Responses
#: return epoch milliseconds instead, which is §9 hazard 2.
DATE_FORMAT: Final = "%Y-%m-%d"

#: How the request spelling reads to a human, for error messages. Kept
#: in Jobvite's own notation rather than strftime's, because that is
#: what an operator reading `.env.example` or the contract sees.
DATE_FORMAT_LABEL: Final = "yyyy-MM-dd"

_MS_PER_SECOND: Final = 1000


def read_identifier(record: Mapping[str, Any]) -> str | None:
    """Return a record's Jobvite identifier, whichever way it is spelt.

    **The read spelling wins when a body carries both.** Every route
    this unit calls is a read, so `eId` is the authoritative one here;
    accepting `EId` as well is what lets one model serve both eras
    without U10 writing a second reader.

    Args:
        record: One Jobvite record.

    Returns:
        The identifier, or `None` when the record carries neither
        spelling. **`None` is not an error here**: a record with no id
        is a real shape the client's scan already handles by keeping it
        in the `unidentified` branch rather than dropping it.
    """
    for key in (ID_KEY_READ, ID_KEY_WRITE):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def epoch_ms_to_date(value: int | None) -> str | None:
    """Convert a response's epoch milliseconds to the request spelling.

    §9 hazard 2, the response direction. Jobvite answers in epoch
    milliseconds and takes `yyyy-MM-dd` on the way in, so a tool
    surface that forwarded the integer would make one concept have two
    spellings depending on which way the caller was going.

    **UTC, explicitly.** A naive local-time conversion moves a date by
    one day for half the planet, and a date that is silently wrong by a
    day is the failure that explains itself.

    Args:
        value: Epoch milliseconds, or `None`.

    Returns:
        The `yyyy-MM-dd` spelling, or `None` when the input was `None`.
    """
    if value is None:
        return None
    moment = dt.datetime.fromtimestamp(value / _MS_PER_SECOND, tz=dt.UTC)
    return moment.strftime(DATE_FORMAT)


def date_to_epoch_ms(value: str | None) -> int | None:
    """Convert the request spelling back to epoch milliseconds.

    §9 hazard 2, the **other** direction. This unit does not call it -
    it reads - and it is here so U10's write path finds a converter
    rather than writing the inverse of `epoch_ms_to_date` beside it.

    Args:
        value: A `yyyy-MM-dd` date, or `None`.

    Returns:
        Epoch milliseconds at midnight UTC, or `None`.

    Raises:
        ValueError: If the string is not `yyyy-MM-dd`. **Refused rather
            than guessed**: `14/11/2023` and `11/14/2023` are the same
            bytes to a permissive parser and different days.
    """
    if value is None:
        return None
    try:
        parsed = dt.datetime.strptime(value, DATE_FORMAT).replace(tzinfo=dt.UTC)
    except ValueError as exc:
        msg = f"expected a {DATE_FORMAT_LABEL} date, got {value!r}"
        raise ValueError(msg) from exc
    return int(parsed.timestamp() * _MS_PER_SECOND)


def blank_to_none(value: Any) -> Any:  # noqa: ANN401 - walks arbitrary JSON values
    """Unify Jobvite's empty strings with nulls (§9 hazard 4).

    "Phone fields use `""`. Treated identically at the boundary"
    (DESIGN.md:1384-1385). A caller that has to test both `is None` and
    `== ""` for the same absence has been handed the vendor's problem.

    **Whitespace counts as blank.** `" "` in a phone field is the same
    absence with a stray keystroke in it, and leaving it through would
    make the unification depend on the operator's typing.

    **A NON-STRING IS RETURNED UNTOUCHED**, and that is the case worth
    stating: `0` and `False` are falsy and are values, not blanks. A
    truthiness test here would delete a legitimate zero total.

    Args:
        value: Any decoded JSON value.

    Returns:
        `None` for a blank string, the value unchanged otherwise.
    """
    if isinstance(value, str) and not value.strip():
        return None
    return value


def none_to_blank(value: str | None) -> str:
    """The request direction of the same unification (§9 hazard 4).

    Jobvite's own fields use `""` where a null belongs, so a body we
    SEND uses the vendor's spelling rather than ours. U10's, like
    `date_to_epoch_ms`, and here so the pair stays in one file.

    Args:
        value: A string or `None`.

    Returns:
        The string, or `""` when it was `None`.
    """
    return "" if value is None else value
