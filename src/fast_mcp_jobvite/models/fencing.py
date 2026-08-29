"""Fencing paths, GENERATED from the output models (DESIGN.md:202-205).

**The two lists live in different key spaces.** Models are snake_case;
fencing paths are camelCase Jobvite paths. DESIGN.md:202-205 therefore
requires the paths to be *generated from the output models* rather than
maintained beside them, "and a test fails when any model field has no
fencing decision. Two hand-maintained lists that must correspond is a
defect waiting for the first schema change."

**Containment is not fencing** (DESIGN.md:197-200). Allow-listing
decides *whether* a field leaves; fencing decides *how* an admitted
field is presented to a model. A field can be correctly admitted and
still carry an injection payload, so the two mechanisms are separate
and each field carries its own explicit answer to the second question.

**This module registers decisions; it does not fence.** U8 owns the
code that actually fences, in `utils/redaction.py`. Job fields take an
explicit "not free text" decision, and U8 is where fencing fires - on
candidate free text, which is the attacker-authored class.

The source of that decision is
`docs/plans/IMPLEMENTATION-PLAN.md`, under **"Why the
fencing-decision registry lands here and not in U8"**. It was cited
here as `DESIGN.md:828-833`, which was the right LINES in the wrong
FILE: `DESIGN.md:828-833` at the frozen `c15b138` is the
`JOBVITE_HTTP_TOKENS` paragraph, a different subject entirely. The
plan is not frozen and those lines have already moved once, so it is
cited by heading rather than by number.

**Why a missing decision RAISES rather than defaulting.** A default
would be the same shape as the defect R3-L1 removed from
`config.py.missing_for`: a rule that names its members, sitting on a
branch that fails open when a member is unlisted. Defaulting to
"fence" would be safe and still wrong, because it would silently admit
a field nobody decided about - which is the condition
DESIGN.md:202-205's test exists to detect, not to paper over.
"""

from __future__ import annotations

import dataclasses
import enum
import types
import typing
from typing import Annotated, Any, Final, get_args, get_origin

from pydantic import BaseModel

#: Separator between path segments, matching DESIGN.md:745-748's own
#: example key `candidates[].application.job.title`.
PATH_SEPARATOR: Final = "."

#: Suffix marking a repeated element, as in `candidates[]`.
LIST_MARKER: Final = "[]"


class FencingDecision(enum.StrEnum):
    """What U8 must do with an admitted field.

    A closed set, for the reason `error-contract.md`'s registry is
    closed (DESIGN.md:676-680): a value that governs a security
    control is a contract, and an open string invites a second
    spelling of the first answer.
    """

    #: Attacker-authored free text. U8 fences it, and strips
    #: delimiter tokens occurring inside the content so the content
    #: cannot close its own fence (DESIGN.md:747-750).
    FENCE = "fence"

    #: Not free text: an identifier, an enumerated state, a URL, an
    #: epoch timestamp, or a container. Passed through as-is. **The
    #: decision is recorded rather than inferred**, so admitting a
    #: field is never the same act as deciding it is safe.
    NOT_FREE_TEXT = "not_free_text"


@dataclasses.dataclass(frozen=True)
class Fenced:
    """One field's fencing decision, carried in its annotation.

    Attributes:
        decision: What U8 does with the field.
        jobvite_key: The field's key **in Jobvite's own casing**,
            which is what the generated path is built from. Our model
            attribute is snake_case and this is not.
        reason: Why this decision, in one line. A decision with no
            reason is a decision nobody can review.
    """

    decision: FencingDecision
    jobvite_key: str
    reason: str


class MissingFencingDecisionError(TypeError):
    """A model field carries no `Fenced` annotation.

    Raised at generation time rather than defaulted, so the field is
    impossible to ship undecided (DESIGN.md:202-205).
    """


def _decision_of(model: type[BaseModel], field_name: str) -> Fenced:
    """Return the field's `Fenced`, or refuse.

    Args:
        model: The output model the field belongs to.
        field_name: The snake_case attribute name.

    Returns:
        The single `Fenced` in the field's annotation metadata.

    Raises:
        MissingFencingDecisionError: If the field carries no `Fenced`,
            or carries more than one.
    """
    field = model.model_fields[field_name]
    found = [item for item in field.metadata if isinstance(item, Fenced)]
    if len(found) != 1:
        msg = (
            f"{model.__name__}.{field_name} carries {len(found)} fencing "
            f"decisions; exactly one Fenced annotation is required "
            f"(DESIGN.md:202-205)"
        )
        raise MissingFencingDecisionError(msg)
    return found[0]


def _nested_model(annotation: Any) -> tuple[type[BaseModel] | None, bool]:  # noqa: ANN401
    """Find a nested output model inside an annotation.

    Unwraps `Annotated`, unions (including `X | None`) and the generic
    containers a Jobvite response can produce, because a decision must
    be found for `locations: list[JobLocation] | None` exactly as for
    a bare `JobLocation`.

    Args:
        annotation: The field's declared type.

    Returns:
        The nested model and whether it was reached through a list.
        `(None, False)` when the field holds no model.
    """
    seen_list = False
    stack: list[Any] = [annotation]
    while stack:
        current = stack.pop()
        origin = get_origin(current)
        if origin is Annotated:
            stack.append(get_args(current)[0])
            continue
        if origin in (typing.Union, types.UnionType):
            stack.extend(get_args(current))
            continue
        if origin in (list, tuple, set, frozenset):
            seen_list = True
            stack.extend(get_args(current))
            continue
        if isinstance(current, type) and issubclass(current, BaseModel):
            return current, seen_list
    return None, seen_list


def fencing_paths(model: type[BaseModel], prefix: str) -> dict[str, Fenced]:
    """Generate every fencing path reachable from an output model.

    Walks the model depth-first. **Every field gets a path**, not only
    the string ones: DESIGN.md:202-205 requires a decision per field,
    and a container's decision is what says its own value is not free
    text while its children answer separately.

    Args:
        model: The output model to walk.
        prefix: The path already accumulated, e.g. `requisitions[]`.

    Returns:
        Every generated path mapped to its decision.

    Raises:
        MissingFencingDecisionError: If any field reachable from
            `model` carries no `Fenced` annotation.
    """
    paths: dict[str, Fenced] = {}
    for name in model.model_fields:
        decision = _decision_of(model, name)
        path = f"{prefix}{PATH_SEPARATOR}{decision.jobvite_key}"
        paths[path] = decision
        nested, through_list = _nested_model(model.model_fields[name].annotation)
        if nested is not None:
            child_prefix = f"{path}{LIST_MARKER}" if through_list else path
            paths.update(fencing_paths(nested, child_prefix))
    return paths
