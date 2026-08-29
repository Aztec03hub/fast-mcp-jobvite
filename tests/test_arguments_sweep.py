"""U14 - the argument-layer completeness sweep (§8 #7, #8, #9).

**THE POINT OF THIS MODULE IS THAT IT NAMES NO INPUT MODEL.** Every
assertion below is parametrised over a set discovered by walking a
container: `src/fast_mcp_jobvite/tools/` twice, by two independent
routes whose results are asserted EQUAL, and then the WHOLE PACKAGE
once more for the models a tool annotation cannot reach. A hand-kept
list of input models beside the input models is the defect this
repository has recorded nine times, and this is the unit whose entire
job is completeness.

**AND ENUMERATING A CONTAINER IS ONLY AS GOOD AS CHOOSING THE RIGHT
CONTAINER, which is what R8-H1 cost.** The first version of this module
did the thing this repository keeps asking for - it replaced the
hand-kept list with an enumerated directory - and then asserted a
property about *the inbound surface* while enumerating *one directory*.
`ApprovalAnswer` is filled in by the host through
`ctx.elicit(..., response_type=...)`, lives in `approval.py`, and was
therefore invisible to both routes: deleting its `extra="forbid"` left
all 768 tests green. The set below is now the UNION of route A and
route C, and section 1c names the one inbound path that has no model
for any route to find.

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

**THE BLANKET POSITIVE CONTROL (`DESIGN.md:1431-1432`).** "A guard that
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


# ======================================================================
# 1b. ROUTE C. THE SECOND WAY A MODEL RECEIVES DATA FROM OUTSIDE, AND
#     A CONTAINER THAT IS THE WHOLE PACKAGE RATHER THAN ONE DIRECTORY.
# ======================================================================
#
# **R8-H1 IS WHY THIS EXISTS, AND THE SHAPE MATTERS MORE THAN THE FIX.**
# Routes A and B replaced a hand-kept LIST with an enumerated CONTAINER,
# which is what this repository keeps asking for, and the container they
# chose - `tools/` - is NARROWER than the property this module asserts.
# `ApprovalAnswer` (`approval.py`) is populated by
# `ctx.elicit(..., response_type=ApprovalAnswer)`, so it is inbound, and
# it lives outside `tools/`. Setting its `extra="forbid"` to
# `extra="allow"` left the entire suite green.
#
# Route C therefore enumerates a DIFFERENT container - every module of
# the package - and selects inside it by USE, exactly as route B keeps
# output models out by their `output_schema=` use and not by their name.
# The use it looks for is the second way a model receives outside data:
# being named as the response type of a request this server makes of its
# host.


SRC_PACKAGE_DIR: Final = SRC / "fast_mcp_jobvite"

#: The keywords through which this server hands a schema to its host and
#: is handed data back. **Not a naming convention** - a name filter is a
#: second hand-kept list in a disguise, and amputation M4 already kills
#: that idea for route B.
OUTSIDE_RESPONSE_KEYWORDS: Final = ("response_type", "requested_schema")


def _package_module_paths() -> list[pathlib.Path]:
    """Every module of the package - **the package is the container**.

    A tool argument is not the only way outside data reaches a model,
    so one directory cannot be the container for a claim about all of
    them.
    """
    return sorted(SRC_PACKAGE_DIR.rglob("*.py"))


def _module_path_of(path: pathlib.Path) -> str:
    parts = list(path.relative_to(SRC).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _schema_call_owner(value: ast.expr | None) -> str | None:
    """`X.model_json_schema(...)` -> `"X"`, anything else -> `None`."""
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "model_json_schema"
        and isinstance(value.func.value, ast.Name)
    ):
        return value.func.value.id
    return None


def _schema_aliases(tree: ast.Module) -> dict[str, str]:
    """`APPROVAL_SCHEMA = ApprovalAnswer.model_json_schema()`.

    **THE MRTR LEG REACHES ITS MODEL THROUGH EXACTLY THIS INDIRECTION**
    (`approval.py`), so a route that only reads a bare `Name` off the
    keyword sees the elicitation leg and not the MRTR one. It
    would have found `ApprovalAnswer` anyway today, by the other
    keyword, and the day those two stop naming the same model is the
    day that coincidence stops covering for the gap.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        owner = _schema_call_owner(value)
        if owner is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                aliases[target.id] = owner
    return aliases


def models_named_as_an_outside_response(tree: ast.Module) -> set[str]:
    """ROUTE C: every class named as the response type of a request.

    Route A asks *"what can a tool caller send?"*. This asks *"what can
    the HOST send back?"* - the same question about the other
    direction, which had no route at all.
    """
    aliases = _schema_aliases(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.keyword):
            continue
        if node.arg not in OUTSIDE_RESPONSE_KEYWORDS:
            continue
        value = node.value
        if isinstance(value, ast.Name):
            found.add(aliases.get(value.id, value.id))
            continue
        owner = _schema_call_owner(value)
        if owner is not None:
            found.add(owner)
    return found


def _enumerate_package(
    route: typing.Callable[[ast.Module], set[str]],
) -> dict[str, str]:
    """Run one route over every package module. name -> module."""
    out: dict[str, str] = {}
    for path in _package_module_paths():
        for name in route(_parse(path)):
            out[name] = _module_path_of(path)
    return out


def _resolve_outside_responses(found: dict[str, str]) -> list[type[BaseModel]]:
    """Like `_resolve`, but it REFUSES a non-model response type.

    `ctx.elicit(..., response_type=bool)` is legal and would give this
    server an inbound path with no model, no `extra="forbid"` and no
    `strict=True` - the very shape route C exists to find. Resolving one
    to something that is not a `BaseModel` therefore fails loudly here
    rather than being quietly dropped for want of a config to assert.
    """
    models: list[type[BaseModel]] = []
    for name, module_path in sorted(found.items()):
        module = importlib.import_module(module_path)
        model = getattr(module, name)
        assert isinstance(model, type) and issubclass(model, BaseModel), (
            f"{module_path}.{name} is named as an outside response type and is "
            f"not a pydantic model, so it carries no config for this sweep to "
            f"assert - it is an inbound path with nothing on it"
        )
        models.append(model)
    return models


#: name -> module for every model the HOST is asked to fill in.
OUTSIDE_RESPONSE_MODELS: Final = _enumerate_package(models_named_as_an_outside_response)


#: The swept set, resolved once. **Collected at import time**, on
#: purpose:
#: if the enumeration breaks, collection fails loudly rather than
#: parametrising zero cases and passing.
#: **THE UNION OF ROUTE A AND ROUTE C**, which is what this name has
#: claimed since U14 wrote it: every model this server exposes to data
#: it did not produce, whichever direction that data arrives from.
INPUT_MODELS: Final = _resolve(
    _enumerate(models_named_by_tool_functions)
) + _resolve_outside_responses(OUTSIDE_RESPONSE_MODELS)

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

    **ROUTE C GETS THE SAME GUARD AND NEEDS IT MORE**, because its
    container is wider and its selector is narrower: one renamed keyword
    and it finds nothing, silently, and every arm below goes back to
    sweeping exactly what it swept before R8-H1 was found.
    """
    assert _tool_module_paths(), f"no tool module under {TOOLS_DIR}"
    assert _package_module_paths(), f"no module under {SRC_PACKAGE_DIR}"
    assert len(_package_module_paths()) > len(_tool_module_paths()), (
        "route C's container must be WIDER than route A's, or it is the "
        "same enumeration under a second name"
    )
    assert OUTSIDE_RESPONSE_MODELS, (
        f"route C found no model named by any of {OUTSIDE_RESPONSE_KEYWORDS} "
        f"under {SRC_PACKAGE_DIR}; this server does ask its host to fill one "
        f"in, so an empty result is a broken route and not an absence"
    )
    assert len(INPUT_MODELS) >= 5, _ids(INPUT_MODELS)
    assert TOOL_COUNT >= 5, TOOL_COUNT
    assert len(INPUT_MODELS) == TOOL_COUNT + len(OUTSIDE_RESPONSE_MODELS), (
        "every registered tool has its own input model, no input model is "
        "unreachable, and the two routes' results are disjoint so the sum "
        "is the union"
    )


def test_route_C_reaches_a_model_route_A_structurally_cannot() -> None:
    """The arm that would have failed on R8-H1, and the anti-tautology.

    Asserting "every model route C finds is in the swept set" is true by
    construction now that the swept set is their union - it would pass
    against a route C that found nothing, which is precisely the state
    this module was in when the mutation survived. What is NOT true by
    construction is that route C reaches outside route A's container, so
    that is what is asserted, without naming the model.
    """
    by_tool = set(_enumerate(models_named_by_tool_functions))
    outside = set(OUTSIDE_RESPONSE_MODELS) - by_tool
    assert outside, (
        "route C found only models route A had already found, so the wider "
        "container is buying nothing and R8-H1 could recur unseen"
    )
    for name in outside:
        module_path = OUTSIDE_RESPONSE_MODELS[name]
        assert not module_path.startswith(f"{TOOLS_PACKAGE}."), (
            f"{name} is in {module_path}, inside route A's own container"
        )


def test_the_two_routes_into_the_swept_set_are_disjoint() -> None:
    """`INPUT_MODELS` is a CONCATENATION.

    The count arithmetic above only reads as a union while the two
    routes share nothing.

    A model that is both a tool's `params` and a `response_type=` is a
    legitimate thing to write; it would appear TWICE in the swept set,
    parametrise every arm twice under a duplicate id, and quietly turn
    the sum assertion above into a false statement about a union. If
    this ever fails, deduplicate the concatenation - do not relax it.
    """
    by_tool = set(_enumerate(models_named_by_tool_functions))
    assert not (by_tool & set(OUTSIDE_RESPONSE_MODELS)), sorted(
        by_tool & set(OUTSIDE_RESPONSE_MODELS)
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
        "class OrphanInput(BaseModel):\n"
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
    by_tool = models_named_by_tool_functions(tree)
    by_class = models_defined_as_classes(tree)

    assert by_tool == {"PlantedInput"}
    assert by_class == {"PlantedInput", "OrphanInput"}, (
        "the output model must be excluded by its `output_schema=` use, "
        "and NOT by its name"
    )

    # THE TWO ROUTES MUST BE ABLE TO DISAGREE, and this is the arm that
    # proves it. `OrphanInput` is a model class no tool registers - the
    # dead-input-model shape - and route B sees it while route A cannot.
    #
    # **AMPUTATION A4 IS WHY THIS ARM EXISTS.** Deleting route B's body
    # and having it call route A left the equality assertion comparing a
    # set with itself: true by construction, and the whole harness went
    # green on a deleted behaviour. Two instruments that cannot disagree
    # are one instrument reported twice.
    assert by_class - by_tool == {"OrphanInput"}


def test_route_C_finds_both_keyword_shapes_in_a_synthetic_module(
    tmp_path: pathlib.Path,
) -> None:
    """POSITIVE CONTROL for route C, with two negative arms.

    The real tree names its one model through BOTH keywords, so a route
    handling only one of them still finds it and the gap only opens
    later. This plants a module where the two keywords name DIFFERENT
    models and requires both, reaches one of them through the
    `X.model_json_schema()` alias the MRTR leg actually uses, and
    requires that an `output_schema=` model and an unused class are NOT
    picked up - the exclude-by-USE rule, in the direction that would
    otherwise sweep every model in the package.
    """
    planted = tmp_path / "planted_responses.py"
    planted.write_text(
        "from pydantic import BaseModel\n"
        "class ElicitedAnswer(BaseModel):\n"
        "    pass\n"
        "class SampledAnswer(BaseModel):\n"
        "    pass\n"
        "class PlantedResult(BaseModel):\n"
        "    pass\n"
        "class NeverAskedFor(BaseModel):\n"
        "    pass\n"
        "SAMPLED_SCHEMA = SampledAnswer.model_json_schema()\n"
        "async def ask(ctx):\n"
        "    await ctx.request(requested_schema=SAMPLED_SCHEMA)\n"
        "    await ctx.report(output_schema=PlantedResult.model_json_schema())\n"
        "    return await ctx.elicit('m', response_type=ElicitedAnswer)\n"
    )
    found = models_named_as_an_outside_response(_parse(planted))
    assert found == {"ElicitedAnswer", "SampledAnswer"}, sorted(found)


def test_route_C_refuses_a_response_type_that_is_not_a_model() -> None:
    """`response_type=bool` is legal, and is a path with nothing on it.

    No `extra="forbid"`, no `strict=True`, no structural limits.

    The resolver must go RED rather than drop it, because dropping it
    reproduces R8-H1 exactly: a path outside every assertion that a
    future reader assumes the sweep reached.
    """
    with pytest.raises(AssertionError, match="not a pydantic model"):
        _resolve_outside_responses({"getattr": "builtins"})


# ======================================================================
# 1c. THE INBOUND PATH THAT HAS NO MODEL AT ALL, ENUMERATED BECAUSE NO
#     ROUTE OVER MODELS CAN SEE IT.
# ======================================================================
#
# **A ROUTE THAT ENUMERATES MODELS CANNOT SEE A PATH THAT HAS NONE.**
# The MRTR leg of `resolve_approval` reads `ctx.input_responses` and
# takes `content.get("approve")` off a RAW DICT, so no model, no
# `extra="forbid"`, no `strict=True` and no structural limit applies to
# it. Routes A, B and C are all blind to it by construction.
#
# **THE DECISION, WRITTEN DOWN RATHER THAN IMPLIED BY A GREEN.** No
# model is introduced there, for two measured reasons and one design
# one:
#
#   1. Its acceptance rule is already the strictest available.
#      `_approved_by_conjunction` applies `is True` to the WIRE value,
#      which is exactly what `ApprovalAnswer`'s `strict=True` was added
#      (R8-H2, `fd1057a`) to reproduce on the other leg.
#      `tests/test_approval_strictness.py` pins the two legs to agree on
#      every plausible answer, so a regression on EITHER goes red.
#   2. The four structural limits have nothing to bound there. That code
#      reads one key and compares identity: it never recurses, never
#      re-serialises and never stores the payload. A model placed there
#      would validate a body the transport has already accepted in
#      full, so the bound that matters for this path is the 1 MiB body
#      cap at the middleware seat - ADR-0029 as corrected - and no
#      model can stand in for it. **That cap is now LANDED**, as
#      `http_hardening.BodySizeLimitMiddleware`, so this path is bounded
#      on the HTTP transport by something that runs before any model.
#   3. Putting a model there where there is none is a new contract - it
#      decides what shape a host response must have before this server
#      will read one key out of it - and inventing that in a fix is what
#      an ADR exists to prevent. This path needs no new contract to be
#      safe today. (Contrast `ApprovalAnswer`, which HAS a model: giving
#      it `InboundModel` completes §2.1's set on a class that already
#      declared two thirds of it, and adds a refusal rather than a
#      shape.)
#
# What WAS missing is enumeration: nothing told a reader that this path
# exists and is outside every route. The census below is that, and it
# turns "an unenumerated path" into a one-element set that goes red the
# day a second one appears.


def _walk_not_entering_nested_functions(node: ast.AST) -> list[ast.AST]:
    """`ast.walk` that stops at a nested `def`.

    A read is then attributed to the function that performs it.
    """
    out: list[ast.AST] = []
    for child in ast.iter_child_nodes(node):
        out.append(child)
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        out.extend(_walk_not_entering_nested_functions(child))
    return out


#: The attribute through which a host response arrives with no model
#: around it.
RAW_HOST_RESPONSE_ATTRIBUTE: Final = "input_responses"


def raw_host_response_reads(tree: ast.Module, module_path: str) -> set[str]:
    """Every read of `ctx.input_responses`, anchored to its function.

    **Anchored to the function name, never to a line number.** A line
    number in an expected set is a citation that drifts on the next edit
    and is then repointed mechanically; a function name is the subject.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in _walk_not_entering_nested_functions(node):
            if (
                isinstance(inner, ast.Attribute)
                and inner.attr == RAW_HOST_RESPONSE_ATTRIBUTE
            ):
                found.add(f"{module_path}:{node.name}")
    return found


#: Every place in the package where a host response is read with no
#: model between the wire and the code.
MODELLESS_INBOUND_READS: Final = sorted(
    read
    for path in _package_module_paths()
    for read in raw_host_response_reads(_parse(path), _module_path_of(path))
)


def test_the_modelless_inbound_paths_are_exactly_the_reasoned_one() -> None:
    """The seventh inbound path, enumerated (R8's answer to Q1).

    This is an EXPECTED-VALUE list, not a search space: the container is
    every module of the package and the selector is an AST attribute
    read, so a new site cannot be missed by anyone forgetting to add it
    here - it appears, and this goes red. The reasoning for the one site
    that exists is in the section comment above; a second site has not
    been reasoned about by anybody and must not arrive silently.

    Comments and docstrings mentioning `ctx.input_responses` are
    invisible to this by construction, which is why it is an AST
    census and not a grep - `approval.py` mentions the attribute in
    four places and reads it in one.
    """
    assert MODELLESS_INBOUND_READS == ["fast_mcp_jobvite.approval:resolve_approval"], (
        MODELLESS_INBOUND_READS
    )


def test_the_modelless_census_finds_a_read_planted_in_a_synthetic_module(
    tmp_path: pathlib.Path,
) -> None:
    """POSITIVE CONTROL for the census.

    Without it the assertion above passes on a census that can only ever
    return the one entry it was written against - and an expected-value
    list whose instrument cannot see anything else is a hand-kept list
    with extra steps.
    """
    planted = tmp_path / "planted_raw.py"
    planted.write_text(
        "async def handler(ctx):\n"
        "    answers = ctx.input_responses\n"
        "    return answers\n"
        "def unrelated(ctx):\n"
        "    return ctx.something_else\n"
    )
    found = raw_host_response_reads(_parse(planted), "planted_raw")
    assert found == {"planted_raw:handler"}, sorted(found)


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
    # TWO models carry no string field, and for different reasons that
    # are both deliberate: `SearchCandidatesInput` declares only
    # non-string filters, and `ApprovalAnswer` is one `bool`. Naming
    # both is what stops a model that quietly lost its fields from
    # shrinking this sweep to nothing while every arm below stays green.
    assert without == ["SearchCandidatesInput", "ApprovalAnswer"], without


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
    """§8 #7's positive control (`DESIGN.md:1431-1432`).

    Without this arm every refusal below is satisfied by a model that
    refuses everything.
    """
    assert model(**_valid_payload(model)) is not None


@pytest.mark.parametrize("model", INPUT_MODELS, ids=_ids(INPUT_MODELS))
def test_case7_an_undeclared_argument_key_FAILS_CLOSED(
    model: type[BaseModel],
) -> None:
    """§8 #7 (`DESIGN.md:1350-1351`), B12 and B23.

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
# 4. §8 #8 - CONTROL CHARACTERS AND BIDI OVERRIDES (DESIGN.md:1352-1355)
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
    """§8 #8's own positive control, which `DESIGN.md:1353` names.

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


def _payload_of_depth(levels: int) -> Any:
    """A payload whose deepest element sits at exactly `levels`.

    `check_structural_limits` counts the argument object itself as
    level 1, so a scalar leaf inside one dict is at level 2.

    **THE ARMS BELOW USE LITERAL 5, 1000, 100 AND 1048576, NEVER THE
    IMPORTED CONSTANTS, AND THE HARNESS IS WHY.** The first version
    wrote `_nest(MAX_NESTING_DEPTH - 1)`; mutation M11 moved
    `MAX_NESTING_DEPTH` from 5 to 4 and the accepting arm MOVED WITH IT
    and passed. A test that reads its expectation out of the code it is
    testing cannot fail when that code changes - it is a restatement,
    not an assertion. `test_the_limits_are_the_designs_own_numbers`
    below is the one place the constants are checked, against the
    numbers `DESIGN.md:162-165` writes down.
    """
    value: Any = "leaf"
    for _ in range(levels - 1):
        value = {"k": value}
    return value


def test_the_limits_are_the_designs_own_numbers() -> None:
    """`DESIGN.md:162-165`, the §2.1 table, transcribed once.

    Every arm below is a literal. This is the single place those
    literals are joined to the constants the code uses, so a limit
    changed in `constraints.py` fails HERE, by name, instead of
    silently redefining what every other arm means.
    """
    assert MAX_NESTING_DEPTH == 5
    assert MAX_LIST_ITEMS == 1_000
    assert MAX_DICT_KEYS == 100
    assert MAX_PAYLOAD_BYTES == 1024 * 1024


# --- depth ------------------------------------------------------------


def test_case9_reject_nesting_past_five_levels() -> None:
    """`DESIGN.md:162`, one of §8 #9's four arms."""
    # EXACTLY ONE LEVEL PAST, never two. The first version rejected a
    # payload two levels over, and mutation M15 - which loosened the
    # check by exactly one - survived it. A rejecting arm with slack in
    # it cannot see an off-by-one, which is the only way this check
    # realistically goes wrong.
    with pytest.raises(ValueError, match="nests deeper"):
        check_structural_limits(_payload_of_depth(6))


def test_case9_ACCEPT_a_payload_at_exactly_five_levels() -> None:
    """ACCEPTING ARM 1 of 4.

    Without it a rejector passes the arm above.
    """
    check_structural_limits(_payload_of_depth(5))


def test_case9_a_deep_payload_fails_closed_through_a_live_model() -> None:
    """The limit reaching a caller, not just the function."""
    with pytest.raises(ValidationError):
        NestedProbe(payload=_payload_of_depth(6))


# --- list items -------------------------------------------------------


def test_case9_reject_a_collection_past_one_thousand_items() -> None:
    """`DESIGN.md:163`."""
    with pytest.raises(ValueError, match="more than 1000 items"):
        check_structural_limits({"k": list(range(1001))})


def test_case9_ACCEPT_a_collection_of_exactly_one_thousand_items() -> None:
    """ACCEPTING ARM 2 of 4."""
    check_structural_limits({"k": list(range(1000))})


def test_case9_an_oversized_list_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={"k": list(range(1001))})


# --- dict keys --------------------------------------------------------


def test_case9_reject_an_object_past_one_hundred_keys() -> None:
    """`DESIGN.md:164`."""
    # THE VALUES ARE ALL THE SAME, DELIBERATELY. The first version
    # used `{str(i): i ...}`, whose 101 values are 101 DISTINCT values -
    # so mutation M13, which counted distinct values instead of keys,
    # survived it. A fixture whose key count and value count agree
    # cannot tell the two quantities apart.
    with pytest.raises(ValueError, match="more than 100 keys"):
        check_structural_limits({str(i): "same" for i in range(101)})


def test_case9_ACCEPT_an_object_of_exactly_one_hundred_keys() -> None:
    """ACCEPTING ARM 3 of 4."""
    check_structural_limits({str(i): "same" for i in range(100)})


def test_case9_an_oversized_object_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={str(i): "same" for i in range(101)})


# --- payload size -----------------------------------------------------


def test_case9_reject_a_payload_larger_than_one_mebibyte() -> None:
    """`DESIGN.md:165`, **as far as this layer reaches**.

    ADR-0029 records that this is the ARGUMENT PAYLOAD and not the
    middleware body cap the design asks for. **That cap now exists** -
    `http_hardening.BodySizeLimitMiddleware`, with its own boundary arms
    in `tests/test_body_cap.py` - so the residue this docstring used to
    name is bounded on the HTTP transport.

    **This arm is not made redundant by it and must not be deleted.**
    The body cap is HTTP-only by construction, and this one runs on both
    transports: on stdio it is the only inbound size bound there is.
    """
    with pytest.raises(ValueError, match="larger than"):
        check_structural_limits({"k": "x" * (1024 * 1024 + 1)})


def test_case9_ACCEPT_a_payload_sitting_just_inside_one_mebibyte() -> None:
    """ACCEPTING ARM 4 of 4, and the one an implementer gets wrong.

    An off-by-one here reads as a correct limit from every rejecting
    arm above.
    """
    # 32 bytes of slack for the JSON quoting and the key.
    check_structural_limits({"k": "x" * (1024 * 1024 - 32)})


def test_case9_an_oversized_payload_fails_closed_through_a_live_model() -> None:
    with pytest.raises(ValidationError):
        NestedProbe(payload={"k": "x" * (1024 * 1024 + 1)})


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
        ("depth", _payload_of_depth(6)),
        ("list", list(range(1001))),
        ("keys", {str(i): "same" for i in range(101)}),
        ("size", "x" * (1024 * 1024 + 1)),
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
    """§5.1 / `DESIGN.md:528`, re-asserted where it has teeth.

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
