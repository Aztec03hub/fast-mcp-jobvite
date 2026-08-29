"""The single redaction point (DESIGN.md:312-316, §8 required case #2).

**Every assertion in this file is written so a FAILURE cannot print the secret
it was checking for.** The obvious form,

    assert FAKE_SC not in line

fails by printing both operands, so the test that exists to prove a credential
never reaches a log record publishes it into CI's output the moment it goes
red - and it goes red exactly when a credential *is* leaking, which is the
worst possible moment. Every check below therefore computes a bool first and
asserts on the bool, so the failure output is `assert not True`.

**Nothing here is a real credential.** These are the shapes, not the values.
"""

from __future__ import annotations

from fast_mcp_jobvite.utils.redaction import (
    NON_SENSITIVE_ARGUMENT_KEYS,
    REDACTED,
    redact_arguments,
    redact_headers,
    redact_text,
    redact_url,
)

#: Obvious non-values. `CONTRIBUTING.md:133-135` forbids a real tenant id,
#: client name or credential anywhere in the repository, tests included.
FAKE_API = "FAKE-API-KEY-0000"
FAKE_SC = "FAKE-SC-SECRET-1111"
FAKE_COMPANY = "FAKE-COMPANY-2222"

JOB_FEED_URL = (
    "https://api.jobvite.com/api/v2/jobFeed"
    f"?api={FAKE_API}&sc={FAKE_SC}&companyId={FAKE_COMPANY}&page=2"
)


def _leaks(haystack: str, *needles: str) -> bool:
    """True if any secret survived. Returns a bool so a failure prints no secret."""
    return any(needle in haystack for needle in needles)


# ---------------------------------------------------------------------------
# redact_url - the absence, and its paired positive
# ---------------------------------------------------------------------------


def test_the_whole_jobFeed_url_loses_every_credential_parameter() -> None:
    out = redact_url(JOB_FEED_URL)
    leaked = _leaks(out, FAKE_API, FAKE_SC, FAKE_COMPANY)
    assert not leaked, "a credential query parameter survived redact_url"


def test_redact_url_is_not_vacuous_it_returns_a_usable_url() -> None:
    """The paired positive for the absence above.

    A `redact_url` that returned `""`, or that dropped the query string
    entirely, would pass the absence test and destroy the debugging value the
    design keeps. This arm pins what must SURVIVE.
    """
    out = redact_url(JOB_FEED_URL)
    assert out.startswith("https://api.jobvite.com/api/v2/jobFeed?")
    assert "page=2" in out
    assert out.count(REDACTED) == 3
    # The parameter NAMES survive: which credentials were on the URL is not
    # itself a secret, and losing them makes the redacted URL unreadable.
    for name in ("api=", "sc=", "companyId="):
        assert name in out


def test_parameter_order_is_preserved() -> None:
    out = redact_url(JOB_FEED_URL)
    names = [pair.split("=")[0] for pair in out.split("?", 1)[1].split("&")]
    assert names == ["api", "sc", "companyId", "page"]


def test_uppercase_parameter_names_are_still_redacted() -> None:
    """A case-sensitive redactor fails open on a URL a human assembled."""
    out = redact_url(f"https://example.invalid/jobFeed?SC={FAKE_SC}&API={FAKE_API}")
    leaked = _leaks(out, FAKE_SC, FAKE_API)
    assert not leaked, "an upper-cased credential parameter survived redact_url"


def test_a_url_with_no_query_is_returned_unchanged() -> None:
    url = "https://api.jobvite.com/api/v2/candidate"
    assert redact_url(url) == url


def test_a_url_carrying_no_secret_is_untouched() -> None:
    """Positive control: the redactor does not mangle innocent URLs.

    DESIGN.md:1369-1370 - a guard that refuses everything is not a guard.
    """
    url = "https://api.jobvite.com/api/v2/jobs?count=50&start=0"
    assert redact_url(url) == url


# ---------------------------------------------------------------------------
# redact_text - the exception-message arm (DESIGN.md:314-315)
# ---------------------------------------------------------------------------


def test_a_url_embedded_in_an_exception_message_is_redacted() -> None:
    message = (
        f"ReadTimeout: timed out requesting {JOB_FEED_URL} after 10s; "
        "retrying attempt 2"
    )
    out = redact_text(message)
    leaked = _leaks(out, FAKE_API, FAKE_SC, FAKE_COMPANY)
    assert not leaked, "a credential survived redaction of an exception message"


def test_redact_text_keeps_the_rest_of_the_message_intact() -> None:
    """Paired positive: the message is still the message.

    A `redact_text` that returned `"[REDACTED]"` for the whole string would
    pass the absence arm above and destroy every log line in the server.
    """
    message = (
        f"ReadTimeout: timed out requesting {JOB_FEED_URL} after 10s; "
        "retrying attempt 2"
    )
    out = redact_text(message)
    assert out.startswith("ReadTimeout: timed out requesting https://")
    assert out.endswith("after 10s; retrying attempt 2")


def test_redact_text_preserves_newlines_so_a_traceback_survives() -> None:
    message = f"line one\n  {JOB_FEED_URL}\nline three"
    out = redact_text(message)
    assert out.startswith("line one\n  https://")
    assert out.endswith("\nline three")
    assert out.count("\n") == 2


# ---------------------------------------------------------------------------
# redact_headers - the v2 credential headers (DESIGN.md:311)
# ---------------------------------------------------------------------------


def test_the_v2_credential_headers_are_redacted() -> None:
    out = redact_headers(
        {"x-jvi-api": FAKE_API, "X-JVI-SC": FAKE_SC, "accept": "application/json"}
    )
    leaked = _leaks("".join(out.values()), FAKE_API, FAKE_SC)
    assert not leaked, "a v2 credential header survived redact_headers"


def test_redact_headers_keeps_non_secret_headers_and_does_not_mutate() -> None:
    original = {"x-jvi-api": FAKE_API, "accept": "application/json"}
    out = redact_headers(original)
    assert out["accept"] == "application/json"
    assert original["x-jvi-api"] == FAKE_API, "redact_headers mutated the live request"


# ---------------------------------------------------------------------------
# redact_arguments - fail-closed by allow-list
# ---------------------------------------------------------------------------


def test_an_unlisted_argument_key_is_redacted() -> None:
    """Fail closed. The argument nobody thought of is the one that leaks."""
    out = redact_arguments({"firstName": "Ada", "email": "ada@example.invalid"})
    leaked = _leaks(repr(out), "Ada", "ada@example.invalid")
    assert not leaked, "an unlisted argument value survived redact_arguments"


def test_a_key_added_by_a_later_tool_is_redacted_without_anyone_updating_this() -> None:
    """The property that makes the allow-list direction worth its cost.

    A deny-list would emit this in the clear; the fail-closed set redacts it
    until someone adds the key deliberately.
    """
    out = redact_arguments({"someFieldInventedInU10": "a resume body"})
    leaked = _leaks(repr(out), "a resume body")
    assert not leaked, "a newly invented argument key was emitted in the clear"


def test_allow_listed_keys_survive_so_the_event_is_still_auditable() -> None:
    """Paired positive.

    A `redact_arguments` that redacted EVERYTHING would pass both absence
    arms above and make the audit event useless - it would record that a call
    happened and nothing about which one.
    """
    out = redact_arguments({"candidate_id": "cand-123", "limit": 50})
    assert out == {"candidate_id": "cand-123", "limit": 50}


def test_the_redacted_marker_names_the_type_but_not_the_value() -> None:
    out = redact_arguments({"coverLetter": "please hire me", "age": 31})
    assert out == {"coverLetter": "[REDACTED:str]", "age": "[REDACTED:int]"}


def test_a_candidate_one_level_down_is_not_emitted() -> None:
    out = redact_arguments(
        {"candidate": {"firstName": "Ada", "contact": {"email": "a@example.invalid"}}}
    )
    leaked = _leaks(repr(out), "Ada", "a@example.invalid")
    assert not leaked, "PII nested inside an argument survived redact_arguments"


def test_a_container_under_an_unlisted_key_is_redacted_WHOLE() -> None:
    """The allow-list is path-keyed, not leaf-keyed.

    **Found by the mutation harness, not by reading.** `M14` removed the
    container walk and the suite stayed green, which meant the walk was not
    doing what the test above believed. It was descending into a container
    whose OWN key nothing had allowed, and then emitting any leaf that happened
    to carry an allow-listed name - so `job_id` escaped from inside a blob
    called `secretBlob`.

    DESIGN.md:1787 describes C6-I2's mechanism as a **path-keyed** allow-list
    for this reason: membership is a property of the path, not of the leaf name
    in isolation.
    """
    out = redact_arguments({"secretBlob": {"job_id": "job-42", "email": "a@b.invalid"}})
    assert out == {"secretBlob": "[REDACTED:dict]"}
    leaked = _leaks(repr(out), "job-42", "a@b.invalid")
    assert not leaked, "a leaf escaped from inside an unlisted container"


def test_a_list_under_an_unlisted_key_is_redacted_WHOLE() -> None:
    out = redact_arguments({"candidates": [{"lastName": "Lovelace"}]})
    assert out == {"candidates": "[REDACTED:list]"}
    leaked = _leaks(repr(out), "Lovelace")
    assert not leaked, "PII inside a list argument survived redact_arguments"


def test_a_container_under_an_ALLOW_LISTED_key_is_still_walked() -> None:
    """The paired positive for the two absences above.

    A `redact_arguments` that replaced EVERY container with a marker would
    pass both, and would stop the walk being reachable at all - which is how a
    fix for an over-permissive rule quietly becomes dead code.
    """
    out = redact_arguments({"job_id": ["job-1", "job-2"]})
    assert out == {"job_id": ["job-1", "job-2"]}


def test_the_allow_list_does_not_contain_query() -> None:
    """`search_candidates`'s query is free text, and a name is what you search for."""
    assert "query" not in NON_SENSITIVE_ARGUMENT_KEYS


def test_redact_arguments_does_not_mutate_its_input() -> None:
    original = {"firstName": "Ada"}
    redact_arguments(original)
    assert original == {"firstName": "Ada"}
