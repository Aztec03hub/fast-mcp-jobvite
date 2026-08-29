"""The two approval legs must agree on what counts as approval (R8-H2).

`resolve_approval` has two legs. The MRTR leg reads a raw dict and
applies `is True` to the wire value; the elicitation leg validates
through `ApprovalAnswer` first and then applies `is True` to the
*validated* field. **Without `strict=True` on that model, pydantic
coerces in between**, so the two legs answered differently for every
truthy string a host might plausibly send.

The comment on the elicitation leg says *"THE SAME CONJUNCTION AS THE
MRTR LEG"*, and it sat exactly at the divergence.

Why this is its own file rather than a case in `test_approval_write.py`:
that file is large and covers the write flow end to end. This is one
narrow invariant about a shape, it is the kind of thing a future reader
looks for by filename, and it must not be lost inside a 1,200-line
module.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from fast_mcp_jobvite.approval import ApprovalAnswer, _approved_by_conjunction

#: Every value a host could plausibly put in the `approve` field.
#:
#: `True` and `False` are the CONTROLS and are not decoration: a test
#: that only fed coercible strings would pass against a model that
#: refuses everything, which approves nothing and is not the fix. The
#: strings are what pydantic's lax mode turned into `True`.
CANDIDATE_ANSWERS = (True, False, "true", "false", "TRUE", "yes", "no", "on", 1, 0)


def _mrtr_leg(value: object) -> bool:
    """What the MRTR leg concludes, through the real function."""
    return _approved_by_conjunction(
        SimpleNamespace(action="accept", content={"approve": value})
    )


def _elicitation_leg(value: object) -> bool:
    """What the elicitation leg concludes, through the real model.

    A validation failure is a REFUSAL, which is what the production
    code does with it: `isinstance(result.data, ApprovalAnswer)` is
    false when the model refused to build, so the conjunction fails.
    """
    try:
        answer = ApprovalAnswer(approve=value)  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 - any validation failure is a refusal
        return False
    return answer.approve is True


@pytest.mark.parametrize("value", CANDIDATE_ANSWERS)
def test_both_approval_legs_agree_on_every_plausible_answer(value: object) -> None:
    """R8-H2: `"yes"` approved a write on one era, refused on the other.

    Measured before the fix, with both real functions:

        wire value    MRTR leg    ELICITATION
        True          True        True
        "true"        False       True           <- DISAGREED
        1             False       True           <- DISAGREED
        "yes"         False       True           <- DISAGREED
        "on"          False       True           <- DISAGREED

    So a host answering `{"approve": "yes"}` authorised a
    `create_candidate` write on the handshake era - **the one tool whose
    failure mode emails a living person** - and was refused on the
    modern one.

    Amputating `strict=True` from `ApprovalAnswer.model_config` turns
    four of these cases red.
    """
    assert _mrtr_leg(value) == _elicitation_leg(value), (
        f"the two approval legs disagree on {value!r}: "
        f"MRTR={_mrtr_leg(value)}, elicitation={_elicitation_leg(value)}"
    )


def test_a_genuine_boolean_still_approves_on_both_legs() -> None:
    """The positive control. The agreement test is vacuous without it.

    `test_both_approval_legs_agree_on_every_plausible_answer` passes
    against an `ApprovalAnswer` that refuses EVERY value, including
    `True` - both legs would then answer `False` everywhere and agree
    perfectly while approving nothing. Agreement is only worth something
    if approval is still reachable.
    """
    assert _mrtr_leg(True) is True
    assert _elicitation_leg(True) is True


def test_a_coercible_string_is_refused_rather_than_approved() -> None:
    """Agreement had two possible directions and only one is safe.

    The legs could have been reconciled by making the MRTR leg coerce
    too. They were reconciled the other way, because a refusal cannot
    email anyone and this is the direction `_answer_for`'s docstring
    already names as the one that fails closed.
    """
    for value in ("true", "yes", "on", 1):
        assert not _elicitation_leg(value), (
            f"{value!r} was approved; the legs now agree by COERCING rather "
            "than by refusing, which is the unsafe direction"
        )
