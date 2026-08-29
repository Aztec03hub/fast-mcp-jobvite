"""The shared inbound constraints, exercised through a real model.

**This file exists because nothing declared a field of these types.**
R4-H2: `SafeText` was built on a negative lookahead, pydantic-core
compiles patterns with the Rust `regex` crate, and that crate has NO
look-around - so declaring one `SafeText` field raised `SchemaError` at
CLASS-CONSTRUCTION time. The rule was written down, did not compile, and
had no caller, so nothing ever tried it.

Five layers passed over it, and the instructive one is coverage: the
module reported **100%** against ADR-0010's 95% floor. It is entirely
module-level statements, so importing it executes every line. That 100%
proved the file imports. It proved nothing about the types it defines,
which is the cleanest example of a green that tested nothing this
project has produced.

So every test here DECLARES A MODEL and validates through it. A test
that merely imported the names would reproduce the defect exactly.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from fast_mcp_jobvite.utils.constraints import (
    MAX_IDENTIFIER_LENGTH,
    MAX_TEXT_LENGTH,
    JobviteIdentifier,
    SafeText,
)


class _Text(BaseModel):
    """A model with a `SafeText` field.

    Constructing this class IS the assertion for R4-H2: before the fix,
    importing this module raised `SchemaError` and every test here
    errored at collection.
    """

    v: SafeText


class _Ident(BaseModel):
    v: JobviteIdentifier


def test_a_model_with_a_safetext_field_can_be_declared() -> None:
    """The regression test for R4-H2, stated as its own case.

    The other tests would also fail if the type stopped compiling,
    but for a reason a reader has to work out. This one names it.
    """
    assert _Text(v="hello world").v == "hello world"


@pytest.mark.parametrize(
    ("bad", "why"),
    [
        ("a\x00b", "NUL, C0"),
        ("a\x1bb", "ESC, C0"),
        ("a\x7fb", "DEL"),
        ("a\x9bb", "C1"),
        ("a‮b", "right-to-left override"),
        ("a⁦b", "left-to-right isolate"),
    ],
)
def test_a_forbidden_character_is_rejected(bad: str, why: str) -> None:
    """DESIGN.md:178 and B25/B30 - the rule this module exists for."""
    with pytest.raises(ValidationError):
        _Text(v=bad)


@pytest.mark.parametrize(
    ("good", "why"),
    [
        ("a\tb", "tab is explicitly allowed"),
        ("a\nb", "newline is explicitly allowed"),
        ("a\rb", "carriage return is explicitly allowed"),
        ("Ünïcödé and 日本語", "non-ASCII is not a control character"),
    ],
)
def test_an_allowed_character_is_accepted(good: str, why: str) -> None:
    """The negative arm, and it is not decoration.

    DESIGN.md:178 rejects C0/C1 control characters **other than tab,
    newline and carriage return**. A rule that refused those three would
    pass every test above while being wrong, and would reject ordinary
    multi-line text. Without this case the forbidden-character tests
    would also pass against a type that rejects EVERYTHING.
    """
    assert _Text(v=good).v == good


def test_safetext_admits_a_trailing_newline_and_the_identifier_does_not() -> None:
    r"""R4-L3: the anchors' rationale said something untrue.

    The `\A`/`\z` comment used to claim `^...$` was rejected because
    it would admit a string ending in a newline, "the log-forging
    shape C7-T1 records". The anchor choice is right and that reason
    was wrong: newline is in the PERMITTED set, so `\A...\z` admits
    a trailing newline anyway. Asserting it here rather than only
    rewriting the prose, because a comment nothing checks is how the
    wrong claim survived in the first place.

    `JobviteIdentifier` is where that protection is actually real -
    its alphabet has no `\n` - and it is the type the "trailing
    newline" arm in `test_tools_jobs.py` exercises.
    """
    assert _Text(v="ab\n").v == "ab\n"
    with pytest.raises(ValidationError):
        _Ident(v="TESTJOB1\n")


def test_the_length_ceilings_are_enforced_through_a_model() -> None:
    """`max_length` is a constraint, not a comment."""
    assert _Text(v="x" * MAX_TEXT_LENGTH).v
    with pytest.raises(ValidationError):
        _Text(v="x" * (MAX_TEXT_LENGTH + 1))

    assert _Ident(v="x" * MAX_IDENTIFIER_LENGTH).v
    with pytest.raises(ValidationError):
        _Ident(v="x" * (MAX_IDENTIFIER_LENGTH + 1))


def test_an_identifier_rejects_what_is_not_an_identifier() -> None:
    """`JobviteIdentifier` compiled all along - it uses a plain class.

    Kept beside `SafeText` deliberately: the two types sit in one module
    and only one of them was broken, so a test that exercised "the
    constraints module" without declaring both would have looked like
    coverage.
    """
    assert _Ident(v="TESTJOB1").v == "TESTJOB1"
    for bad in ("has space", "has/slash", "has;semi", ""):
        with pytest.raises(ValidationError):
            _Ident(v=bad)
