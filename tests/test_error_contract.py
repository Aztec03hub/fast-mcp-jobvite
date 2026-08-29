"""U2: the error contract (DESIGN.md:491-540).

IMPLEMENTATION-PLAN.md:447-470.

The table below is the design's registry table (DESIGN.md:513-521)
restated as data, so a change to either side shows up as a diff here
rather than as a sentence nobody re-reads.
"""

from __future__ import annotations

import ast
import pathlib
import re
from collections.abc import Callable

import pytest

from fast_mcp_jobvite import errors

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

RID = "550e8400-e29b-41d4-a716-446655440000"

# (condition, exception factory, expected type, expected status)
REGISTRY_CASES: list[tuple[str, Callable[[], BaseException], str, int]] = [
    (
        "any Jobvite failure, including its 4xx",
        lambda: errors.JobviteUpstreamError(401, "Invalid API key"),
        "/problems/external-service-error",
        502,
    ),
    (
        "Jobvite unreachable, breaker open, timeout",
        lambda: errors.JobviteUnavailableError("circuit breaker is open"),
        "/problems/service-unavailable",
        503,
    ),
    (
        "argument or schema validation inside the body",
        lambda: errors.ValidationError("startDate is after endDate"),
        "/problems/validation-error",
        422,
    ),
    (
        "candidate or job id not found",
        lambda: errors.ResourceNotFoundError("no candidate with id abc"),
        "/problems/resource-not-found",
        404,
    ),
    (
        "duplicate candidate on create",
        lambda: errors.DuplicateCandidateError("candidate already exists"),
        "/problems/conflict",
        409,
    ),
    (
        "caller's token lacks the scope",
        lambda: errors.ScopeDeniedError("token lacks candidates:write"),
        "/problems/forbidden",
        403,
    ),
    (
        "anything unmapped",
        lambda: RuntimeError("something nobody modelled"),
        "/problems/internal-error",
        500,
    ),
]


@pytest.mark.parametrize(
    ("condition", "factory", "expected_type", "expected_status"),
    REGISTRY_CASES,
    ids=[c[0] for c in REGISTRY_CASES],
)
def test_every_registry_row_maps_to_its_registry_type_and_status(
    condition: str,
    factory: Callable[[], BaseException],
    expected_type: str,
    expected_status: int,
) -> None:
    problem = errors.problem_from_exception(factory(), RID)
    assert problem["type"] == expected_type, condition
    assert problem["status"] == expected_status, condition


def test_a_jobvite_401_is_a_502_and_not_a_401() -> None:
    """DESIGN.md:506-509: a 401 blames the wrong credential.

    The caller cannot hold the credential it blames.
    """
    problem = errors.problem_from_exception(
        errors.JobviteUpstreamError(401, "Invalid API key"), RID
    )
    assert problem["status"] == 502
    assert problem["status"] != 401
    assert problem["title"] == "External Service Error"
    assert not problem["type"].startswith("/problems/jobvite-")


def test_validation_is_422_and_not_400() -> None:
    """DESIGN.md:534: validation is 422 per the registry, not 400."""
    problem = errors.problem_from_exception(errors.ValidationError("bad range"), RID)
    assert problem["status"] == 422
    assert problem["status"] != 400


def test_every_problem_carries_all_seven_required_members() -> None:
    """error-contract.md:66 elevates these seven to required.

    DESIGN.md:495-496.
    """
    assert errors.REQUIRED_MEMBERS == (
        "type",
        "title",
        "status",
        "detail",
        "instance",
        "request_id",
        "timestamp",
    )
    for condition, factory, _type, _status in REGISTRY_CASES:
        problem = errors.problem_from_exception(factory(), RID)
        missing = [m for m in errors.REQUIRED_MEMBERS if m not in problem]
        assert not missing, f"{condition}: missing {missing}"
        empty = [m for m in errors.REQUIRED_MEMBERS if problem[m] in (None, "")]
        assert not empty, f"{condition}: empty {empty}"


def test_instance_is_the_urn_and_request_id_matches_it() -> None:
    """DESIGN.md:499-500."""
    problem = errors.build_problem(errors.CONFLICT, "duplicate", RID)
    assert problem["instance"] == f"urn:fast-mcp-jobvite:invocation:{RID}"
    assert problem["request_id"] == RID
    assert problem["instance"].endswith(problem["request_id"])


def test_timestamp_is_iso_8601_utc() -> None:
    """error-contract.md:85; its example at :62 ends in Z."""
    stamp = errors.build_problem(errors.CONFLICT, "duplicate", RID)["timestamp"]
    assert stamp.endswith("Z")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", stamp), stamp


def test_jobvites_own_status_and_message_are_in_detail_and_not_discarded() -> None:
    """DESIGN.md:532-534."""
    exc = errors.JobviteUpstreamError(401, "Invalid API key or company id")
    problem = errors.problem_from_exception(exc, RID)
    assert "401" in problem["detail"]
    assert "Invalid API key or company id" in problem["detail"]
    # Preserved on the exception too, for the audit event
    # (DESIGN.md:532-533).
    assert exc.upstream_status == 401
    assert exc.upstream_message == "Invalid API key or company id"


def test_a_jobvite_failure_with_no_status_still_keeps_its_message() -> None:
    """The plain-text and Tomcat-HTML encodings carry no status.

    DESIGN.md:345-347.
    """
    problem = errors.problem_from_exception(
        errors.JobviteUpstreamError(None, "Service Temporarily Unavailable"), RID
    )
    assert "Service Temporarily Unavailable" in problem["detail"]
    assert problem["status"] == 502


def test_an_unmapped_exception_does_not_leak_its_message_to_the_caller() -> None:
    """An exception's str() can carry a URL or a credential."""
    problem = errors.problem_from_exception(
        RuntimeError("connect failed to https://api.jobvite.com?api=SECRETKEY"), RID
    )
    assert "SECRETKEY" not in problem["detail"]
    assert "RuntimeError" in problem["detail"]


def test_a_problem_object_is_returned_never_raised() -> None:
    """DESIGN.md:536-540 - being returned resists configuration.

    Two arms, because the first alone passes on a function that returns
    None.
    """
    result = errors.problem_from_exception(errors.ValidationError("bad"), RID)
    assert isinstance(result, dict)
    assert result["type"] == "/problems/validation-error"

    for condition, factory, expected_type, _status in REGISTRY_CASES:
        # If the call raised instead of returning, this never reaches
        # the assert.
        problem = errors.problem_from_exception(factory(), RID)
        assert isinstance(problem, dict), condition
        assert problem["type"] == expected_type, condition


def test_no_problem_construction_function_raises_a_problem_object() -> None:
    """Static arm: nothing in errors.py is on the right of a `raise`.

    The behavioural arm above cannot see a `raise` on a path it does not
    take. The only permitted `raise` in this module is the ValueError
    guarding extension-member shadowing, which is a programming error at
    the call site.
    """
    tree = ast.parse((SRC / "fast_mcp_jobvite" / "errors.py").read_text())
    raised = [n for n in ast.walk(tree) if isinstance(n, ast.Raise) and n.exc]
    names = []
    for node in raised:
        exc = node.exc
        assert exc is not None
        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            names.append(exc.func.id)
        else:  # pragma: no cover - defensive; no such form exists today
            names.append(ast.dump(exc))
    assert names == ["ValueError"], names


def test_an_extension_member_cannot_shadow_a_required_member() -> None:
    with pytest.raises(ValueError, match="shadow"):
        errors.build_problem(errors.CONFLICT, "dup", RID, status=200)


def test_extension_members_survive_alongside_the_seven() -> None:
    """DESIGN.md:358 attaches a retry_after hint to the 503."""
    problem = errors.build_problem(
        errors.SERVICE_UNAVAILABLE, "breaker open", RID, retry_after=30
    )
    assert problem["retry_after"] == 30
    assert all(m in problem for m in errors.REQUIRED_MEMBERS)


# `error-contract.md:96-108`, pinned here as data. It is pinned rather
# than read from the standards checkout because CI does not check that
# repository out - a test that reads it would hard-fail in CI, and one
# that tolerates its absence would be a wrong zero. Drift between this
# table and the standard is caught by the project's citation audit, not
# by this suite; that limit is stated in docs/worklogs/U2-REPORT.md.
REGISTRY_TABLE: dict[str, tuple[str, int]] = {
    "/problems/resource-not-found": ("Resource Not Found", 404),
    "/problems/forbidden": ("Forbidden", 403),
    "/problems/conflict": ("Conflict", 409),
    "/problems/validation-error": ("Validation Error", 422),
    "/problems/external-service-error": ("External Service Error", 502),
    "/problems/internal-error": ("Internal Server Error", 500),
    "/problems/service-unavailable": ("Service Unavailable", 503),
}


def _defined_kinds() -> dict[str, tuple[str, int]]:
    """Every ProblemKind defined, minus the about:blank one."""
    return {
        v.type: (v.title, v.status)
        for v in vars(errors).values()
        if isinstance(v, errors.ProblemKind) and v.type != "about:blank"
    }


def test_the_registry_constants_match_the_standards_table_verbatim() -> None:
    """error-contract.md:96-108 is the source of the titles.

    A drifted title is a contract break.
    """
    assert _defined_kinds() == REGISTRY_TABLE


def test_no_type_uri_is_minted_locally() -> None:
    """DESIGN.md:510-511: a published type URI is owed forever.

    The count is asserted first. Without it, deleting every registry
    constant makes this loop iterate zero times and pass - which is how
    a repo-wide "nothing bad exists" assertion goes vacuous.
    """
    defined = _defined_kinds()
    assert len(defined) == 7, defined
    for uri in defined:
        assert uri in REGISTRY_TABLE, f"{uri} is not a row of error-contract.md:96-108"
    assert errors.UNMAPPED.type == "about:blank", "error-contract.md:115"


ENVELOPE = re.compile(r'["\']?success["\']?\s*[:=]\s*(true|false|True|False)')


def _scan_for_envelope(roots: list[pathlib.Path]) -> list[str]:
    """Return `path:line` for every `success` envelope under `roots`.

    `success: true` and `success: false` both count.

    A `git grep` was the first form of this and it was wrong: it
    searches **tracked** files only, so a brand-new untracked module
    returns a clean, self-explaining zero.
    """
    hits: list[str] = []
    scanned = 0
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if path == pathlib.Path(__file__):
                continue
            scanned += 1
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if ENVELOPE.search(line):
                    hits.append(f"{path}:{number}: {line.strip()}")
    if scanned == 0:
        hits.append(f"WRONG ZERO: no .py file was scanned under {roots}")
    return hits


def test_the_envelope_scanner_finds_an_envelope_when_one_is_present(
    tmp_path: pathlib.Path,
) -> None:
    """Positive control for the scanner used by the assertion below."""
    (tmp_path / "planted.py").write_text('RESULT = {"success": true}\n')
    assert _scan_for_envelope([tmp_path])


def test_the_envelope_scanner_reports_a_wrong_zero_on_an_empty_tree(
    tmp_path: pathlib.Path,
) -> None:
    """A tree with no .py file must not read as a clean pass."""
    assert _scan_for_envelope([tmp_path]) == [
        f"WRONG ZERO: no .py file was scanned under [{tmp_path!r}]"
    ]


def test_no_success_true_false_envelope_exists_anywhere_in_the_repository() -> None:
    """DESIGN.md:497.

    **This assertion is near-vacuous today and U2-REPORT.md says so**:
    `src/` holds four modules, so it passes over almost nothing. It must
    be re-asserted once tools exist. The two controls above are what
    keep it from being a wrong zero.
    """
    assert _scan_for_envelope([SRC, REPO_ROOT / "tests"]) == []
