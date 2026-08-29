"""Secret redaction - the single enforcement point (DESIGN.md:312-316).

**This module holds the SECRET half only.** DESIGN.md:291 gives
`utils/redaction.py` two jobs, "log redaction; untrusted-content fencing", and
`IMPLEMENTATION-PLAN.md:1497` assigns the fencing half to U8. Nothing here
fences.

**Why one place.** DESIGN.md:312-316 classifies the v1 `GET /v1/jobFeed` URL as
sensitive - it structurally requires `api`, `sc` and `companyId` as query
parameters, so unlike every other Jobvite call the credential is *in the URL* -
and states the rule as "never logged whole, never in an exception message,
`sc=` redacted before any log line. Enforced in one place, `utils/redaction.py`,
with a test that fails if a secret can reach a log record." A second redactor
elsewhere is the defect this sentence exists to prevent, because the two drift
and the one that drifts is the one nobody reads.

**Three parameters are redacted, not one.** DESIGN.md:313 names `api`, `sc` and
`companyId` as the three the URL structurally carries, and DESIGN.md:317-319
makes `companyId` a credential class of its own ("the job feed's separate
`companyId` credential"). §8's required case names `sc=` because that is the
one an implementer is most likely to reach for; redacting only it would satisfy
the case and leave two credentials in the log line, so the case is the floor
here and not the specification.

**Arguments are redacted by allow-list, and the direction is deliberate.**
DESIGN.md:1793 rates C7-I1 - candidate PII written to logs in the clear -
**Critical**, and `ai/tool-calling.md:171-172` requires the audit event to carry
"validated arguments (PII redacted)". A deny-list of known PII key names fails
*open*: the argument nobody thought of is emitted in the clear, which is the
failure mode DESIGN.md:1788 (C6-I2) already rejects for output fields in favour
of "path-keyed allow-list fails closed: an unlisted field is dropped until
someone adds it deliberately". The same reasoning applies with more force on
the audit path, because `create_candidate`'s arguments **are** the candidate.
So an argument whose key is not on `NON_SENSITIVE_ARGUMENT_KEYS` has its value
replaced by a type marker, and the audit record still shows *which* arguments
were supplied and of what shape - which is what makes the event auditable -
without showing any of their content.
"""

from __future__ import annotations

import re
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Final

#: The value shape a validated tool argument can take. Recursive, because
#: `create_candidate`'s payload is nested and a redactor typed only at the top
#: level would be typed for the case that does not matter. `Any` is not
#: available: `ANN401` is on (`pyproject.toml`, ruff `ANN`), and it would also
#: switch mypy off exactly where the fail-closed walk needs checking.
type JsonValue = (
    str | int | float | bool | None | Mapping[str, JsonValue] | Sequence[JsonValue]
)

#: What replaces a redacted scalar. A fixed sentinel rather than a length-
#: preserving mask: a mask that preserves length leaks the length, and a
#: credential's length is a real hint.
REDACTED: Final = "[REDACTED]"

#: A URL carrying credentials in its USERINFO - `scheme://user:password@host`.
#:
#: Round 2 found this surviving: `redact_text` only inspected tokens containing
#: both `?` and `=`, so a proxy URL - which has neither - passed through whole
#: and reached the caller's problem `detail`. Measured before the fix:
#: `https://user:hunter2@proxy.internal:8080/path` came back unchanged.
#:
#: `://` before the `@` is what separates this from an email address, which must
#: not be touched: `someone@example.com` has no scheme and no colon-password.
_USERINFO: Final = re.compile(
    r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.\-]*://)(?P<user>[^/@\s:]+):(?P<pw>[^/@\s]*)@"
)

#: Query parameters on the `jobFeed` URL that carry a credential
#: (DESIGN.md:312-319). Compared case-insensitively, because a URL a human
#: assembled will not always match Jobvite's casing and a redactor that misses
#: `SC=` has failed open.
SECRET_QUERY_PARAMS: Final[frozenset[str]] = frozenset({"api", "sc", "companyid"})

#: Request headers that carry a v2 credential (DESIGN.md:311). Lower-cased;
#: callers must lower-case the key before lookup.
SECRET_HEADERS: Final[frozenset[str]] = frozenset({"x-jvi-api", "x-jvi-sc"})

#: Argument keys whose values may appear in an audit record in the clear.
#:
#: **Fail-closed: anything absent from this set is redacted.** Every member is
#: here because its value is structurally an identifier, a bound or a page
#: cursor rather than anything a candidate typed or that identifies one. A tool
#: added later contributes its arguments to the audit event redacted, and stays
#: that way until someone adds the key here deliberately - which is the point.
#:
#: `query` is deliberately ABSENT. A `search_candidates` query is free text a
#: caller composed, and the obvious thing to search for is a person's name.
NON_SENSITIVE_ARGUMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "candidate_id",
        "job_id",
        "requisition_id",
        "workflow_state",
        "limit",
        "start",
        "count",
        "page",
        "eId",
        "companyId",
    }
)


def redact_url(url: str) -> str:
    """Redact every credential-bearing query parameter in a URL.

    The `jobFeed` URL is the reason this exists (DESIGN.md:312-316), but the
    function is not restricted to it: a URL is passed in and every parameter in
    `SECRET_QUERY_PARAMS` comes back redacted, whatever the host. Restricting
    it to a recognised `jobFeed` host would fail open on a staging host, a
    tenant-specific host, or a URL assembled slightly differently.

    Parameter ORDER and every non-secret parameter are preserved, so a redacted
    URL is still useful for debugging - which is what stops someone logging the
    raw one instead.

    Args:
        url: The URL to redact. May be a fragment, a full URL, or a string that
            is not a URL at all; a string with no query part is returned
            unchanged.

    Returns:
        The URL with each secret parameter's value replaced by `REDACTED`.
    """
    split = urllib.parse.urlsplit(url)
    if not split.query:
        return url
    pairs = urllib.parse.parse_qsl(split.query, keep_blank_values=True)
    if not any(key.lower() in SECRET_QUERY_PARAMS for key, _ in pairs):
        # Returned byte-identical rather than reassembled. `urlencode` would
        # re-encode every innocent value, so a URL with nothing to redact would
        # still come back altered - and a redactor that rewrites what it had no
        # reason to touch is one nobody trusts to be transparent.
        return url
    redacted = [
        (key, REDACTED if key.lower() in SECRET_QUERY_PARAMS else value)
        for key, value in pairs
    ]
    # `safe="[]"` keeps the sentinel literal. Without it `urlencode` percent-
    # encodes the brackets to `%5BREDACTED%5D`, and every downstream grep for
    # `[REDACTED]` - in a test, in a log search, in an incident - misses it.
    query = urllib.parse.urlencode(redacted, safe="[]")
    return urllib.parse.urlunsplit(split._replace(query=query))


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact the v2 credential headers (DESIGN.md:311).

    Args:
        headers: Request headers. Keys are matched case-insensitively.

    Returns:
        A new mapping with `x-jvi-api` and `x-jvi-sc` values replaced. The
        original is not mutated, because a redactor that mutates its input
        redacts the request that is about to be sent.
    """
    return {
        key: (REDACTED if key.lower() in SECRET_HEADERS else value)
        for key, value in headers.items()
    }


def redact_text(text: str) -> str:
    """Redact any credential-bearing URL embedded in free text.

    This is the arm that covers an **exception message** (DESIGN.md:314-315).
    `httpx` puts the request URL into the text of the exceptions it raises, so
    a `jobFeed` timeout carries `sc=` in `str(exc)` and any handler that
    formats the exception into a log line publishes the credential. Redacting
    only at the URL-argument boundary would miss exactly that path.

    Args:
        text: Arbitrary text that may contain a URL.

    It also redacts **userinfo** - `scheme://user:password@host` - which the
    query-parameter arm cannot reach, because such a URL carries neither `?` nor
    `=`. An httpx proxy misconfiguration puts exactly that into an exception
    message. The username is kept: the password is the secret and the user is
    the diagnosis, the same split this project applies to a failing assertion.

    Returns:
        The text with every embedded URL's secret parameters and userinfo
        password redacted.
    """
    out: list[str] = []
    for token in _split_keeping_whitespace(text):
        out.append(redact_url(token) if "?" in token and "=" in token else token)
    # Userinfo is a SECOND credential shape in the same text, and it is not
    # reached by the query-parameter arm above: a proxy URL has no `?` and no
    # `=`, so it never entered `redact_url` at all. Applied to the joined text
    # rather than per token so a URL split across the whitespace splitter is
    # still caught.
    return _USERINFO.sub(
        lambda m: f"{m.group('scheme')}{m.group('user')}:{REDACTED}@", "".join(out)
    )


def redact_arguments(arguments: JsonValue) -> JsonValue:
    """Redact a tool's validated arguments for the audit event.

    Fail-closed by allow-list, for the reason in the module docstring. Nested
    containers are walked, because `create_candidate`'s payload is nested and a
    top-level-only redactor would emit the whole candidate one level down.

    A redacted scalar becomes `"[REDACTED:<type>]"` rather than a bare
    sentinel. The type is not sensitive, and keeping it is what makes the audit
    event answer "was a résumé body supplied on this call" - which is an
    auditing question - without answering "what did it say".

    Args:
        arguments: The validated arguments, or any value nested inside them.

    Returns:
        A redacted copy. The input is never mutated.
    """
    if isinstance(arguments, Mapping):
        return {
            key: (
                redact_arguments(value)
                if key in NON_SENSITIVE_ARGUMENT_KEYS
                else _redacted_value(value)
            )
            for key, value in arguments.items()
        }
    if isinstance(arguments, list):
        return [redact_arguments(item) for item in arguments]
    return arguments


def _redacted_value(value: JsonValue) -> str:
    """Replace one value with a marker naming only its type.

    **Containers are redacted whole, not descended into**, and that is the
    path-aware half of the allow-list. An earlier revision descended into any
    container regardless of its key, which meant an allow-listed key nested
    under an UNLISTED one was emitted in the clear:

        {"secretBlob": {"job_id": "...", "email": "..."}}
          -> {"secretBlob": {"job_id": "...", "email": "[REDACTED:str]"}}

    The `job_id` survived because `job_id` is allow-listed, even though nothing
    had allowed `secretBlob`. DESIGN.md:1788 calls C6-I2's mechanism a
    **path-keyed** allow-list for exactly this reason: membership has to be
    judged on the path, not on the leaf name in isolation.

    Found by the mutation harness rather than by reading - `M14` survived,
    which said the mutation was not a leak, which said the walk it removed was
    doing something other than what the test believed.
    """
    return f"[REDACTED:{type(value).__name__}]"


def _split_keeping_whitespace(text: str) -> list[str]:
    """Split on whitespace, keeping the separators so the text reassembles.

    `str.split()` discards the whitespace it split on, so rejoining with a
    single space would silently rewrite a log line's formatting - including a
    multi-line traceback, which is exactly the text this function is asked to
    redact.
    """
    tokens: list[str] = []
    current: list[str] = []
    for char in text:
        if char.isspace():
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(char)
        else:
            current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens
