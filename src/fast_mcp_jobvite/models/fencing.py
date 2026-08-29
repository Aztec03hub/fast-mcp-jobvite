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
here as `DESIGN.md:901-906`, which was the right LINES in the wrong
FILE: `DESIGN.md:901-906` at the frozen `c15b138` is the
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

#: Separator between path segments, matching DESIGN.md:820-822's own
#: example key `candidates[].application.job.title`.
PATH_SEPARATOR: Final = "."

#: Suffix marking a repeated element, as in `candidates[]`.
LIST_MARKER: Final = "[]"


class FencingDecision(enum.StrEnum):
    """What U8 must do with an admitted field.

    A closed set, for the reason `error-contract.md`'s registry is
    closed (DESIGN.md:761-763): a value that governs a security
    control is a contract, and an open string invites a second
    spelling of the first answer.
    """

    #: Attacker-authored free text. U8 fences it, and strips
    #: delimiter tokens occurring inside the content so the content
    #: cannot close its own fence (DESIGN.md:817-818).
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
    return _single(model, field_name, list(model.model_fields[field_name].metadata))


def _computed_decision_of(model: type[BaseModel], name: str) -> Fenced:
    """Return a COMPUTED field's `Fenced`, or refuse.

    **Computed fields were invisible to this walker until R4-M1**, and
    the gap was not cosmetic: `JobSearchResult.summary` is a
    caller-facing string built from data, which is precisely the kind
    of value a fencing decision is about, and it could never carry one
    because nothing looked. A registry that cannot see half a model's
    output surface is a registry that is complete over what it
    enumerates and silent about the rest.

    A computed field has no `FieldInfo.metadata`, so the decision
    lives in its RETURN annotation: `-> Annotated[str, Fenced(...)]`.
    Measured on this stack: the extra metadata does not reach
    `model_json_schema(mode="serialization")`.

    Args:
        model: The output model the computed field belongs to.
        name: The computed field's attribute name.

    Returns:
        The single `Fenced` in the return annotation's metadata.

    Raises:
        MissingFencingDecisionError: If it carries no `Fenced`, or
            more than one.
    """
    annotation = model.model_computed_fields[name].return_type
    metadata = (
        list(get_args(annotation)[1:]) if get_origin(annotation) is Annotated else []
    )
    return _single(model, name, metadata)


def _single(model: type[BaseModel], name: str, metadata: list[Any]) -> Fenced:
    """Pull exactly one `Fenced` out of a metadata list, or refuse.

    Args:
        model: The model, for the error message.
        name: The field name, for the error message.
        metadata: The annotation metadata to search.

    Returns:
        The single `Fenced` found.

    Raises:
        MissingFencingDecisionError: If there is not exactly one.
    """
    found = [item for item in metadata if isinstance(item, Fenced)]
    if len(found) != 1:
        msg = (
            f"{model.__name__}.{name} carries {len(found)} fencing "
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

    **Computed fields are walked too (R4-M1).** They are part of what
    a caller receives, so leaving them out made the registry complete
    over `model_fields` and silent about the rest - and the field it
    was silent about, `JobSearchResult.summary`, is a caller-facing
    string built from data.

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
    for name in model.model_computed_fields:
        decision = _computed_decision_of(model, name)
        paths[f"{prefix}{PATH_SEPARATOR}{decision.jobvite_key}"] = decision
    return paths
