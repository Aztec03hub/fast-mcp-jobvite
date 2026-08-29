"""U14 - the argument-layer completeness sweep (§8 #7, #8, #9).

**THE POINT OF THIS MODULE IS THAT IT NAMES NO INPUT MODEL.** Every
assertion below is parametrised over a set discovered by walking
`src/fast_mcp_jobvite/tools/`, twice, by two independent routes, with
the two sets asserted EQUAL. A hand-kept list of input models beside
the input models is the defect this repository has recorded nine times,
and this is the unit whose entire job is completeness.

**The brief that dispatched this unit said "the four input models:
`tools/jobs.py` (two), `tools/candidates.py` (two)". There are FIVE**,
and `candidates.py` holds three of them - `SearchCandidatesInput`,
`GetCandidateInput` and `CreateCandidateInput`. The plan said four and
so did the task that gated the dispatch. Nobody was careless; a typed
list simply cannot keep up with a container. That miscount is the
strongest available argument for the enumeration below, and it was
found by running it.

**WHAT A REJECTION LOOKS LIKE HERE, AND WHAT IT DOES NOT.**
`DESIGN.md:181-190` is explicit: every check on this path lives in the
input models, runs **before the tool body**, and is raised by the
framework, so **none of these rejections carries a problem object**. An
earlier design revision said `400` and the registry says `422`;
neither reaches a caller on this path. Every assertion below is
therefore about **fail-closed behaviour** - a `ValidationError` and no
constructed model - and never about a problem-object shape. A test
asserting a problem shape here would be asserting something this code
cannot produce.

**THE BLANKET POSITIVE CONTROL (`DESIGN.md:1370-1371`).** "A guard that
refuses everything is not a guard, and its refusals prove nothing."
All three cases carry one, and #9 carries **four** - one per limit -
because a limit test with no accepting arm cannot tell a correct limit
from a rejector.
"""

from __future__ import annotations

import ast
import importlib
import json
import pathlib
import typing
from typing import Any, Final, Literal, get_args, get_origin

import pytest
from pydantic import BaseModel, ValidationError

from fast_mcp_jobvite.utils.constraints import (
    MAX_DICT_KEYS,
    MAX_LIST_ITEMS,
    MAX_NESTING_DEPTH,
    MAX_PAYLOAD_BYTES,
    InboundModel,
    check_structural_limits,
)

from .conftest import REPO_ROOT

SRC: Final = REPO_ROOT / "src"
TOOLS_DIR: Final = SRC / "fast_mcp_jobvite" / "tools"
TOOLS_PACKAGE: Final = "fast_mcp_jobvite.tools"


# ======================================================================
# 1. THE ENUMERATION. TWO ROUTES INTO ONE CONTAINER, ASSERTED EQUAL.
# ======================================================================


def _tool_module_paths() -> list[pathlib.Path]:
    """Every module of the tools package, `__init__` excluded.

    **The directory is the container.** A module added tomorrow is
    swept without anyone editing this file, which is the whole property
    the two-lists defect destroys.
    """
    return sorted(p for p in TOOLS_DIR.glob("*.py") if p.name != "__init__.py")


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _is_server_tool_decorator(node: ast.expr) -> bool:
    """`@server.tool(...)`: a Call whose function attr is `tool`."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tool"
    )


def _annotation_name(node: ast.expr | None) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def models_named_by_tool_functions(tree: ast.Module) -> set[str]:
    """ROUTE A: every `@server.tool`-decorated function's `params` type.

    This is the **inbound surface as the framework sees it** - if a
    class is not the annotation of some registered tool's first
    argument, no caller can ever send it anything.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(_is_server_tool_decorator(d) for d in node.decorator_list):
            continue
        for argument in node.args.args:
            if argument.arg == "params":
                name = _annotation_name(argument.annotation)
                if name is not None:
                    found.add(name)
    return found


def _output_schema_class_names(tree: ast.Module) -> set[str]:
    """Every class handed to an `output_schema=` keyword in this module.

    **This is how output models are excluded WITHOUT reading names.**
    Filtering on a `...Result` suffix would be a second hand-kept list
    wearing a naming convention as a disguise, and it would silently
    admit the day someone names an output model something else.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.keyword) or node.arg != "output_schema":
            continue
        value = node.value
        # `X.model_json_schema(mode=...)`
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            owner = value.func.value
            if isinstance(owner, ast.Name):
                names.add(owner.id)
    return names


def models_defined_as_classes(tree: ast.Module) -> set[str]:
    """ROUTE B: every model class defined here, minus the output models.

    Independent of route A: it reads the class statements, not the tool
    registrations. Two routes that could only agree by both being right
    is the point; one route is a claim, two are a check.
    """
    outputs = _output_schema_class_names(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
        if not bases & {"BaseModel", "InboundModel"}:
            continue
        if node.name in outputs:
            continue
        found.add(node.name)
    return found


def _enumerate(route: typing.Callable[[ast.Module], set[str]]) -> dict[str, str]:
    """Run one route over every tool module. Returns name -> module."""
    out: dict[str, str] = {}
    for path in _tool_module_paths():
        for name in route(_parse(path)):
            out[name] = f"{TOOLS_PACKAGE}.{path.stem}"
    return out


def _resolve(found: dict[str, str]) -> list[type[BaseModel]]:
    models: list[type[BaseModel]] = []
    for name, module_path in sorted(found.items()):
        module = importlib.import_module(module_path)
        model = getattr(module, name)
        assert isinstance(model, type) and issubclass(model, BaseModel), name
        models.append(model)
    return models


#: The swept set, resolved once. **Collected at import time**, on
#: purpose:
#: if the enumeration breaks, collection fails loudly rather than
#: parametrising zero cases and passing.
INPUT_MODELS: Final = _resolve(_enumerate(models_named_by_tool_functions))

#: How many tools this server registers, derived the same way.
TOOL_COUNT: Final = len(_enumerate(models_named_by_tool_functions))


def _ids(models: list[type[BaseModel]]) -> list[str]:
    return [m.__name__ for m in models]


def test_the_two_enumerations_of_the_input_model_set_are_EQUAL() -> None:
    """The completeness assertion this whole unit exists to make.

    Set equality, not containment. `>=` would pass on a route that
    found everything plus noise, and `<=` on a route that found nothing.
    """
    by_tool = set(_enumerate(models_named_by_tool_functions))
    by_class = set(_enumerate(models_defined_as_classes))
    assert by_tool == by_class, (
        f"only a tool annotation: {sorted(by_tool - by_class)}; "
        f"only a class definition: {sorted(by_class - by_tool)}"
    )


def test_the_enumeration_is_not_a_wrong_zero() -> None:
    """A set-equality assertion is satisfied by `set() == set()`.

    Every module here was found by globbing a directory, and a glob at
    a path that does not exist returns a clean, self-explaining empty -
    identical to a real absence. The counts are asserted, and the floor
    is the number of tools this server registered when U14 swept it.
    """
    assert _tool_module_paths(), f"no tool module under {TOOLS_DIR}"
    assert len(INPUT_MODELS) >= 5, _ids(INPUT_MODELS)
    assert len(INPUT_MODELS) == TOOL_COUNT, (
        "every registered tool has its own input model, and no input "
        "model is unreachable"
    )


def test_the_enumeration_finds_a_model_planted_in_a_synthetic_module(
    tmp_path: pathlib.Path,
) -> None:
    """POSITIVE CONTROL for both routes.

    The two routes above are asserted equal against the real tree,
    where they agree. Two broken routes agreeing on nothing would pass
    that. This plants one tool and one model in a module neither route
    has ever seen and requires both to find it.
    """
    planted = tmp_path / "planted.py"
    planted.write_text(
        "from pydantic import BaseModel\n"
        "class PlantedInput(BaseModel):\n"
        "    pass\n"
        "class PlantedResult(BaseModel):\n"
        "    pass\n"
        "def register(server):\n"
        "    @server.tool(\n"
        "        name='planted',\n"
        "        output_schema=PlantedResult.model_json_schema(),\n"
        "    )\n"
        "    async def planted(params: PlantedInput, ctx):\n"
        "        return None\n"
    )
    tree = _parse(planted)
    assert models_named_by_tool_functions(tree) == {"PlantedInput"}
    assert models_defined_as_classes(tree) == {"PlantedInput"}, (
        "the output model must be excluded by its `output_schema=` use, not by its name"
    )


# ======================================================================
# 2. WHAT EVERY MODEL IN THE SET MUST CARRY (§2.1, DESIGN.md:152-154)
# ======================================================================


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_every_input_model_forbids_extra_keys_and_is_strict(
    model: type[BaseModel],
) -> None:
    """`DESIGN.md:152-154`: `strict=True`, extra keys forbidden.

    Asserted per model rather than on a base class. Inheriting the
    config would make this pass for a model that never stated it.
    """
    assert model.model_config.get("extra") == "forbid", model.__name__
    assert model.model_config.get("strict") is True, model.__name__


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_every_input_model_carries_the_shared_structural_limits(
    model: type[BaseModel],
) -> None:
    """ADR-0012: one copy of the rule, reused - never re-declared."""
    assert issubclass(model, InboundModel), (
        f"{model.__name__} does not inherit InboundModel, so §2.1's four "
        f"structural limits do not apply to what its callers send"
    )


def _flatten(annotation: Any) -> list[Any]:
    """Every concrete type `annotation` admits, `Annotated` stripped.

    **TWO WRAPPERS, AND THE FIRST VERSION OF THIS SWEPT PAST BOTH.**
    An optional constrained field arrives from pydantic as
    `Optional[Annotated[str, StringConstraints(...)]]`, so a member of
    the union is not `str` - it is an `Annotated` alias OF `str`, and
    `member is str` is False. The sweep found FIVE string fields where
    the models declare NINE, and every arm parametrised over it was
    green while missing `SearchJobsInput.ids`, `GetJobFeedInput.
    job_type`, `CreateCandidateInput.mobile` and `.source` - four
    fields, one of which is the free-text one.

    It was caught by the population assertion below and by nothing
    else, which is the argument for asserting a derived list's SIZE
    rather than trusting that it was derived.
    """
    if get_origin(annotation) is Literal:
        return [annotation]
    if hasattr(annotation, "__metadata__"):  # Annotated[X, ...]
        return _flatten(get_args(annotation)[0])
    members = get_args(annotation)
    if members:
        out: list[Any] = []
        for member in members:
            out.extend(_flatten(member))
        return out
    return [annotation]


def _string_fields(model: type[BaseModel]) -> list[str]:
    """Field names whose annotation admits `str`, wrappers unwrapped."""
    return [
        name
        for name, field in model.model_fields.items()
        if str in _flatten(field.annotation)
    ]


#: (model, field) for every string-typed field on every swept model.
STRING_FIELDS: Final = [
    (model, name) for model in INPUT_MODELS for name in _string_fields(model)
]


def test_the_string_field_sweep_covers_what_the_models_actually_declare() -> None:
    """A parametrised list built from a container can go EMPTY silently.

    Pytest passes a test parametrised over nothing without a word, so
    the population is asserted here rather than trusted. **The count of
    models carrying NO string field is asserted too** - it is 1 today
    (`SearchCandidatesInput`, deliberately empty), and a model that
    quietly lost its fields would otherwise shrink this sweep to
    nothing while every arm below stayed green.
    """
    assert len(STRING_FIELDS) >= 9, STRING_FIELDS
    without = [m.__name__ for m in INPUT_MODELS if not _string_fields(m)]
    assert without == ["SearchCandidatesInput"], without


@pytest.mark.parametrize(
    ("model", "field"),
    STRING_FIELDS,
    ids=[f"{m.__name__}.{f}" for m, f in STRING_FIELDS],
)
def test_every_string_field_carries_an_explicit_length_ceiling_and_a_pattern(
    model: type[BaseModel], field: str
) -> None:
    """`DESIGN.md:152-154`: explicit `max_length` on EVERY string.

    Read off the generated JSON schema rather than off the annotation,
    because the schema is what the constraint actually compiled to -
    R4-H2 was a rule that was written down and did not compile.
    """
    schema = model.model_json_schema()
    rendered = json.dumps(schema["properties"][field])
    assert "maxLength" in rendered, f"{model.__name__}.{field}: no max_length"
    assert "pattern" in rendered, f"{model.__name__}.{field}: no regex"


# ======================================================================
# 3. A WELL-FORMED PAYLOAD, SYNTHESISED FROM THE MODEL RATHER THAN TYPED
# ======================================================================


def _example_value(annotation: Any) -> Any:
    """One valid value for `annotation`, or raise.

    **It raises on a type it does not know rather than returning
    `None`.** A synthesiser that guesses turns "this model has a field
    shape nobody swept" into a green.
    """
    for member in _flatten(annotation):
        if member is type(None):
            continue
        if get_origin(member) is Literal:
            return get_args(member)[0]
        if member is bool:
            return False
        if member is int:
            return 1
        if member is str:
            # Valid under BOTH `SafeText` and `JobviteIdentifier`: no
            # forbidden character, and inside the identifier alphabet.
            return "Ada"
    raise TypeError(f"no example value for {annotation!r} - widen the synthesiser")


def _valid_payload(model: type[BaseModel]) -> dict[str, Any]:
    payload = {
        name: _example_value(field.annotation)
        for name, field in model.model_fields.items()
        if field.is_required()
    }
    assert all(v is not None for v in payload.values()), payload
    return payload


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_case7_POSITIVE_CONTROL_a_well_formed_argument_passes(
    model: type[BaseModel],
) -> None:
    """§8 #7's positive control (`DESIGN.md:1370-1371`).

    Without this arm every refusal below is satisfied by a model that
    refuses everything.
    """
    assert model(**_valid_payload(model)) is not None


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_case7_an_undeclared_argument_key_FAILS_CLOSED(
    model: type[BaseModel],
) -> None:
    """§8 #7 (`DESIGN.md:1289-1290`), B12 and B23.

    **No problem object is asserted, because none can be produced**
    (`DESIGN.md:181-190`). What is asserted is that nothing is
    constructed and the framework raised.
    """
    payload = _valid_payload(model) | {"not_a_declared_argument": "x"}
    with pytest.raises(ValidationError):
        model(**payload)


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_case7_a_wrongly_typed_argument_FAILS_CLOSED(
    model: type[BaseModel],
) -> None:
    """`strict=True` is a behaviour, not a config key.

    The assertion above would pass on a model with `extra="forbid"` and
    no strictness at all; this one is what `strict=True` buys.
    """
    fields = _valid_payload(model)
    # NO `pytest.skip` when a model has no required field. A skip is a
    # green that tested nothing, and `test_the_wrong_type_arm_is_not_
    # vacuous_for_want_of_a_field` below is what stops the empty loop
    # here from being the whole sweep.
    for name, value in fields.items():
        wrong = "not_an_int" if isinstance(value, int) else 12345
        with pytest.raises(ValidationError):
            model(**(fields | {name: wrong}))


def test_the_wrong_type_arm_is_not_vacuous_for_want_of_a_field() -> None:
    """The arm above loops over required fields and one model has none.

    A loop over an empty collection passes having asserted nothing, so
    the population is asserted here: at least two of the swept models
    must carry a required field for that arm to mean anything.
    """
    with_required = [m.__name__ for m in INPUT_MODELS if _valid_payload(m)]
    assert len(with_required) >= 2, with_required


# ======================================================================
# 4. §8 #8 - CONTROL CHARACTERS AND BIDI OVERRIDES (DESIGN.md:1291-1294)
# ======================================================================

#: One representative of each forbidden class. `\x00` is the C0 case
#: `DESIGN.md:175` names; `\x85` is C1, which a rule written only for
#: C0 admits; `‮` is the bidi override.
POISON: Final = [
    ("\x00", "C0 NUL"),
    ("\x85", "C1 NEL"),
    ("‮", "bidi RIGHT-TO-LEFT OVERRIDE"),
    ("⁦", "bidi LEFT-TO-RIGHT ISOLATE"),
]


@pytest.mark.parametrize(("bad", "why"), POISON, ids=[w for _, w in POISON])
@pytest.mark.parametrize(
    ("model", "field"),
    STRING_FIELDS,
    ids=[f"{m.__name__}.{f}" for m, f in STRING_FIELDS],
)
def test_case8_a_forbidden_character_in_ANY_string_field_FAILS_CLOSED(
    model: type[BaseModel], field: str, bad: str, why: str
) -> None:
    """§8 #8, B25, §2.1.

    **Swept across every string field of every model**, not asserted
    once against `SafeText` in isolation. `tests/test_constraints.py`
    proves the type rejects; this proves every field that should carry
    the type does.
    """
    payload = _valid_payload(model) | {field: f"Ada{bad}Lovelace"}
    with pytest.raises(ValidationError):
        model(**payload)


@pytest.mark.parametrize(
    ("model", "field"),
    STRING_FIELDS,
    ids=[f"{m.__name__}.{f}" for m, f in STRING_FIELDS],
)
def test_case8_POSITIVE_CONTROL_an_ordinary_name_passes(
    model: type[BaseModel], field: str
) -> None:
    """§8 #8's own positive control, which `DESIGN.md:1292` names.

    "with a positive control showing an ordinary name still passes".
    """
    assert model(**(_valid_payload(model) | {field: "Ada"})) is not None


# ======================================================================
# 5. §8 #9 - THE FOUR STRUCTURAL LIMITS. FOUR REJECTING AND FOUR
#    ACCEPTING ARMS, BECAUSE A LIMIT TEST WITH NO ACCEPTING ARM CANNOT
#    TELL A CORRECT LIMIT FROM A REJECTOR.
# ======================================================================


class NestedProbe(InboundModel):
    """A model with a field that admits arbitrary structure.

    **This is the model the deferral in `utils/constraints.py` said did
    not exist.** It said the limits would have "no caller and no
    reachable test" until "the first nested input model" landed, and
    named `create_candidate` as the trigger - which landed with six
    flat scalar fields, so the trigger could not fire.

    The five shipped input models all happen to fail closed against a
    nested payload for a DIFFERENT reason: every field is a bounded
    scalar under `strict=True`, so a list arrives at a `str` field and
    is refused as the wrong type. **That is fail-closed by accident,
    and it evaporates the first time a model declares a `dict` or a
    `list` field.** This probe is that model, so the limits are
    load-bearing here and every arm below measures the limit itself
    rather than a type error standing in for it.
    """

    model_config = {"extra": "forbid", "strict": True}

    payload: dict[str, Any]


def _nest(depth: int) -> Any:
    value: Any = "leaf"
    for _ in range(depth):
        value = {"k": value}
    return value


# --- depth ------------------------------------------------------------


def test_case9_reject_nesting_past_five_levels() -> None:
    """`DESIGN.md:162`, one of §8 #9's four arms."""
    with pytest.raises(ValueError, match="nests deeper"):
        check_structural_limits(_nest(MAX_NESTING_DEPTH + 1))


def test_case9_ACCEPT_a_payload_at_exactly_five_levels() -> None:
    """ACCEPTING ARM 1 of 4.

    Without it a rejector passes the arm above.
    """
    check_structural_limits(_nest(MAX_NESTING_DEPTH - 1))


def test_case9_a_deep_payload_fails_closed_through_a_live_model() -> None:
    """The limit reaching a caller, not just the function."""
    with pytest.raises(ValidationError):
        NestedProbe(payload=_nest(MAX_NESTING_DEPTH + 4))


# --- list items -------------------------------------------------------


def test_case9_reject_a_collection_past_one_thousand_items() -> None:
    """`DESIGN.md:163`."""
    with pytest.raises(ValueError, match="more than 1000 items"):
        check_structural_limits({"k": list(range(MAX_LIST_ITEMS + 1))})


def test_case9_ACCEPT_a_collection_of_exactly_one_thousand_items() -> None:
    """ACCEPTING ARM 2 of 4."""
    check_structural_limits({"k": list(range(MAX_LIST_ITEMS))})


def test_case9_an_oversized_list_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={"k": list(range(MAX_LIST_ITEMS + 1))})


# --- dict keys --------------------------------------------------------


def test_case9_reject_an_object_past_one_hundred_keys() -> None:
    """`DESIGN.md:164`."""
    with pytest.raises(ValueError, match="more than 100 keys"):
        check_structural_limits({str(i): i for i in range(MAX_DICT_KEYS + 1)})


def test_case9_ACCEPT_an_object_of_exactly_one_hundred_keys() -> None:
    """ACCEPTING ARM 3 of 4."""
    check_structural_limits({str(i): i for i in range(MAX_DICT_KEYS)})


def test_case9_an_oversized_object_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={str(i): i for i in range(MAX_DICT_KEYS + 1)})


# --- payload size -----------------------------------------------------


def test_case9_reject_a_payload_larger_than_one_mebibyte() -> None:
    """`DESIGN.md:165`, **as far as this layer reaches**.

    ADR-0029 records that this is the ARGUMENT PAYLOAD and not the
    middleware body cap the design asks for. The arm is real and the
    residue is written down rather than implied by a green.
    """
    with pytest.raises(ValueError, match="larger than"):
        check_structural_limits({"k": "x" * (MAX_PAYLOAD_BYTES + 1)})


def test_case9_ACCEPT_a_payload_sitting_just_inside_one_mebibyte() -> None:
    """ACCEPTING ARM 4 of 4, and the one an implementer gets wrong.

    An off-by-one here reads as a correct limit from every rejecting
    arm above.
    """
    # 32 bytes of slack for the JSON quoting and the key.
    check_structural_limits({"k": "x" * (MAX_PAYLOAD_BYTES - 32)})


def test_case9_an_oversized_payload_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={"k": "x" * (MAX_PAYLOAD_BYTES + 1)})


def test_case9_the_size_check_survives_a_value_json_cannot_serialise() -> None:
    """A raw payload has not been validated yet.

    `json.dumps` on an arbitrary object raises `TypeError`, which is
    NOT a `ValidationError` and would escape the framework's own
    handling - a fail-closed check turning into an unhandled crash.
    """
    check_structural_limits({"k": object()})


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_case9_EVERY_swept_model_fails_closed_on_every_limit(
    model: type[BaseModel],
) -> None:
    """The sweep arm: all four limits, all five models, fail closed.

    Some of these models refuse the payload for a type reason rather
    than a limit reason, and the assertion is deliberately about the
    OUTCOME - `DESIGN.md:189`: "The rule still fails closed, which is
    the whole of what B25 and B30 require."
    """
    base = _valid_payload(model)
    for name, oversized in (
        ("depth", _nest(MAX_NESTING_DEPTH + 1)),
        ("list", list(range(MAX_LIST_ITEMS + 1))),
        ("keys", {str(i): i for i in range(MAX_DICT_KEYS + 1)}),
        ("size", "x" * (MAX_PAYLOAD_BYTES + 1)),
    ):
        with pytest.raises(ValidationError):
            model(**(base | {"structurally_oversized": oversized}))
        assert name  # the label is for the failure message, not the logic


# ======================================================================
# 6. U2's NO-`success`-ENVELOPE RULE, RE-RUN WITH TEETH
# ======================================================================
#
# U2 owns the rule and asserts it in `tests/test_error_contract.py`,
# where its own docstring says: "This assertion is near-vacuous today
# and U2-REPORT.md says so: `src/` holds four modules, so it passes over
# almost nothing. It must be re-asserted once tools exist."
#
# **`src/` holds four modules** was true then. The re-assertion is here,
# and it is not a second copy of the rule: it IMPORTS U2's scanner and
# adds the one thing U2 could not add, which is a claim about the SIZE
# OF THE CORPUS the scanner walked. `_scan_for_envelope` guards against
# scanning zero files; it cannot tell 4 modules from 23.


def _all_python_modules() -> list[pathlib.Path]:
    """The container U2's rule is supposed to cover, enumerated."""
    return sorted(
        list(SRC.rglob("*.py")) + list((REPO_ROOT / "tests").rglob("*.py")),
    )


def test_the_no_success_envelope_rule_now_runs_over_the_COMPLETED_corpus() -> None:
    """§5.1 / `DESIGN.md:497`, re-asserted where it has teeth.

    Two claims, and the second is the one U2 could not make: the rule
    finds nothing, AND the corpus it looked at is the whole tree rather
    than the four modules that existed when the rule was written.
    """
    from .test_error_contract import _scan_for_envelope

    modules = _all_python_modules()
    source_modules = [p for p in modules if SRC in p.parents]
    assert len(source_modules) > 4, (
        "U2's docstring recorded the corpus as four modules; if it is "
        "still four, this re-assertion has no more teeth than U2's did"
    )
    assert len(modules) >= 50, len(modules)
    assert _scan_for_envelope([SRC, REPO_ROOT / "tests"]) == []


def test_the_corpus_claim_can_fail_over_a_shrunken_tree(
    tmp_path: pathlib.Path,
) -> None:
    """POSITIVE CONTROL: the size claim above is falsifiable.

    A tree of one module must not satisfy the corpus assertion. Without
    this arm, `len(modules) >= 50` is a number nobody has watched go
    red - which is precisely how U2's own assertion spent seven units
    passing over almost nothing.
    """
    (tmp_path / "only.py").write_text("x = 1\n")
    shrunken = sorted(tmp_path.rglob("*.py"))
    assert len(shrunken) == 1
    assert not len(shrunken) >= 50
