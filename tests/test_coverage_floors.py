"""Controls for `docs/reviews/check-coverage-floors.py` (#94).

**A GATE NOBODY HAS WATCHED FAIL IS NOT KNOWN TO WORK.** This project
has measured that twice over: `check-u9-http-controls.sh` printed
*"1/1 controls fired"* with thirteen of its fourteen rows deleted,
because `FIRED -ne TOTAL` is satisfied by `0 == 0`; and #94's own
subject was an obligation written in a comment that no artefact read.
A checker that reports OK is evidence of nothing until each of its
refusal arms has been driven, one at a time.

**WHY THESE ARE PYTEST CASES AND NOT A `--self-check` FLAG.** A
self-test checks the side of the boundary its author had in mind -
measured on this codebase, where three of four mutants survived a
`--self-check` and all three were killed by an independent test. These
cases run the checker as a SUBPROCESS and read its exit code, so what
is under test is the artefact CI runs, not a function that shares its
author's assumptions.

**Each arm is driven by a synthetic design and a synthetic package**,
through the checker's `--design` and `--package` flags. The real
repository cannot be pushed into these states without breaking it, and
a control that cannot reach the arm it names is decoration.

The positive control is the LAST case: the same synthetic inputs with
nothing wrong exit 0. Without it, every refusal below is satisfied by a
checker that refuses everything - which enforces no floor at all and is
the failure this file exists to rule out.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from typing import Any

import pytest

CHECKER = (
    pathlib.Path(__file__).resolve().parent.parent
    / "docs/reviews/check-coverage-floors.py"
)

#: A design sentence in the real one's shape. The floors here are
#: DELIBERATELY not ADR-0010's numbers: if the checker ignored this file
#: and read the repository's own design instead, every case below would
#: still pass and prove nothing. Different numbers make that
#: substitution visible.
SYNTHETIC_DESIGN = """
Coverage: 50% floor overall, 60% tool modules, 70% the Jobvite client,
**75% on `utils/` - kept rather than remapped** - and 80% line with 88%
branch on critical paths (alpha, beta).
"""

#: The two roles the synthetic design names, plus the client role the
#: checker requires in addition.
SYNTHETIC_MODULES = {
    "alpha.py": 'from typing import Final\n\nCOVERAGE_ROLE: Final = "alpha"\n',
    "beta.py": 'from typing import Final\n\nCOVERAGE_ROLE: Final = "beta"\n',
    "client.py": (
        'from typing import Final\n\nCOVERAGE_ROLE: Final = "the Jobvite client"\n'
    ),
}


def summary(statements: int, covered: int, branches: int, hit: int) -> dict[str, Any]:
    """One `coverage json` file entry, in the real report's shape."""
    return {
        "summary": {
            "num_statements": statements,
            "covered_lines": covered,
            "num_branches": branches,
            "covered_branches": hit,
        }
    }


def build(
    tmp_path: pathlib.Path,
    *,
    design: str = SYNTHETIC_DESIGN,
    modules: dict[str, str] | None = None,
    files: dict[str, dict[str, Any]] | None = None,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    """Lay out a synthetic design, package and coverage report."""
    # The checker reports a module path relative to the package's
    # grandparent, mirroring `src/<package>`, so the synthetic package
    # is nested the same way rather than dropped at the root.
    package = tmp_path / "src" / "synthetic"
    package.mkdir(parents=True)
    for name, body in (SYNTHETIC_MODULES if modules is None else modules).items():
        (package / name).write_text(body)

    design_path = tmp_path / "DESIGN.md"
    design_path.write_text(design)

    if files is None:
        files = {
            "src/synthetic/alpha.py": summary(100, 100, 20, 20),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        }
    report = tmp_path / "coverage.json"
    report.write_text(
        json.dumps(
            {
                "files": files,
                "totals": {
                    "num_statements": sum(
                        f["summary"]["num_statements"] for f in files.values()
                    )
                    or 1,
                    "covered_lines": sum(
                        f["summary"]["covered_lines"] for f in files.values()
                    ),
                },
            }
        )
    )
    return report, design_path, package


def run(
    report: pathlib.Path, design: pathlib.Path, package: pathlib.Path
) -> subprocess.CompletedProcess[str]:
    """The checker, as a subprocess, judged by its EXIT CODE.

    `capture_output` and not a pipe into `grep`: under a pipeline the
    exit code read is the last command's, and a red gate has been
    committed here twice that way.
    """
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            str(report),
            "--design",
            str(design),
            "--package",
            str(package),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_checker_exists_where_this_file_says_it_does() -> None:
    """A search at a path that does not exist exits clean-empty.

    Every case below would then run `python3 <missing>` and read a
    non-zero exit as the refusal it was hoping for. This is the arm that
    separates "the gate fired" from "the gate is not there".
    """
    assert CHECKER.is_file(), f"{CHECKER} does not exist"


def test_a_critical_path_under_the_branch_floor_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """THE DEFECT #94 WAS OPENED FOR, reproduced against the checker.

    Line coverage is perfect and branch coverage is one point under. The
    aggregate `fail_under` cannot see this - it is 80 against a suite
    measuring 95%+ - which is exactly how two critical paths sat ten
    points below their own floor with every gate green.
    """
    report, design, package = build(
        tmp_path,
        files={
            "src/synthetic/alpha.py": summary(100, 100, 100, 87),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)
    assert result.returncode == 1, result.stdout
    assert "87.00% branch" in result.stdout


def test_a_critical_path_under_the_line_floor_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """The other half, and it is not the same arm.

    A checker reading only `covered_branches` would pass this, and a
    checker reading only `covered_lines` would pass the case above. The
    design sets both numbers, so both are driven.
    """
    report, design, package = build(
        tmp_path,
        files={
            "src/synthetic/alpha.py": summary(100, 79, 20, 20),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)
    assert result.returncode == 1, result.stdout
    assert "79.00% line" in result.stdout


def test_a_role_the_design_names_that_no_module_claims_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """THE UNENFORCED FLOOR, which is #94's second half exactly.

    `beta` is dropped from the package while the design still names it.
    Every remaining module is at 100%, so a checker that only compared
    numbers would report a clean pass while one of the design's floors
    was enforced by nothing at all - the state the checker exists to
    end, quietly restored.
    """
    modules = dict(SYNTHETIC_MODULES)
    del modules["beta.py"]
    report, design, package = build(
        tmp_path,
        modules=modules,
        files={
            "src/synthetic/alpha.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)
    assert result.returncode == 1, result.stdout
    assert "NAMES A ROLE NO MODULE CLAIMS" in result.stdout
    assert "beta" in result.stdout


def test_a_role_the_design_does_not_name_is_refused(tmp_path: pathlib.Path) -> None:
    """The other direction of the same join, and a different defect.

    A module claiming `gamma` is claiming a floor ADR-0010 never set.
    An equality that only checked one direction would admit it, and the
    module would then read as governed by a decision nobody made.
    """
    modules = dict(SYNTHETIC_MODULES)
    modules["gamma.py"] = 'from typing import Final\n\nCOVERAGE_ROLE: Final = "gamma"\n'
    report, design, package = build(
        tmp_path,
        modules=modules,
        files={
            "src/synthetic/alpha.py": summary(100, 100, 20, 20),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
            "src/synthetic/gamma.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)
    assert result.returncode == 1, result.stdout
    assert "A ROLE THE DESIGN DOES NOT NAME" in result.stdout


def test_two_modules_claiming_one_role_are_refused(tmp_path: pathlib.Path) -> None:
    """A floor applied to the wrong module reads as discharged.

    Both directions of the set equality PASS here - the two sets are
    equal - so this arm is invisible to the join and needs its own
    check. That is the shape of a defect a set comparison cannot see.
    """
    modules = dict(SYNTHETIC_MODULES)
    modules["alpha_twin.py"] = (
        'from typing import Final\n\nCOVERAGE_ROLE: Final = "alpha"\n'
    )
    report, design, package = build(
        tmp_path,
        modules=modules,
        files={
            "src/synthetic/alpha.py": summary(100, 100, 20, 20),
            "src/synthetic/alpha_twin.py": summary(100, 100, 20, 20),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)
    assert result.returncode == 1, result.stdout
    assert "CLAIM THE SAME ROLE" in result.stdout


def test_a_design_whose_coverage_sentence_does_not_parse_is_a_hard_stop(
    tmp_path: pathlib.Path,
) -> None:
    """A pattern that stops matching must STOP, never skip a floor.

    This is the failure mode `check-harness-anchors.py` records: when a
    parser shape stops matching, everything that still parses resolves
    perfectly and the checker reports OK on a fraction of its coverage.
    The reworded sentence here still contains percentages, so a lenient
    parser would find *some* numbers and carry on.
    """
    report, design, package = build(
        tmp_path,
        design="Coverage: we aim for about 95% everywhere, give or take.\n",
    )
    result = run(report, design, package)
    assert result.returncode != 0, result.stdout
    assert "DID NOT PARSE" in result.stdout + result.stderr


def test_an_empty_coverage_report_is_a_hard_stop(tmp_path: pathlib.Path) -> None:
    """A report measuring nothing satisfies every floor vacuously.

    The wrong ZERO that explains itself: no files means no module below
    its floor, and a checker that returned 0 here would be green on the
    run where the instrument failed.
    """
    report, design, package = build(tmp_path, files={})
    result = run(report, design, package)
    assert result.returncode == 2, result.stdout
    assert "ZERO FILES" in result.stdout


def test_a_missing_coverage_report_is_a_hard_stop(tmp_path: pathlib.Path) -> None:
    """A path that does not exist must not read as a pass."""
    _, design, package = build(tmp_path)
    result = run(tmp_path / "nowhere.json", design, package)
    assert result.returncode == 2, result.stdout


@pytest.mark.parametrize("family", ["tools", "utils"])
def test_a_directory_family_under_its_floor_is_refused(
    tmp_path: pathlib.Path, family: str
) -> None:
    """`tools/` and `utils/` are floored by DIRECTORY, not by role.

    A module in either directory carries a floor without declaring
    anything, so these two arms are reached by a path rule rather than
    by the join - and a checker that only ever looked at declared roles
    would leave both families ungoverned while reporting a clean pass.
    """
    report, design, pkg = build(tmp_path)
    (pkg / family).mkdir()
    (pkg / family / "plain.py").write_text("VALUE = 1\n")

    files = json.loads(report.read_text())
    files["files"][f"src/synthetic/{family}/plain.py"] = summary(100, 55, 20, 20)
    report.write_text(json.dumps(files))

    result = run(report, design, pkg)
    assert result.returncode == 1, result.stdout
    assert "55.00% line" in result.stdout


def test_positive_control_the_same_inputs_with_nothing_wrong_pass(
    tmp_path: pathlib.Path,
) -> None:
    """THE PAIRING FOR EVERY REFUSAL ABOVE.

    A checker that exited 1 unconditionally would satisfy all nine of
    them, enforce no floor, and be indistinguishable from the working
    one until the day someone lowered a number and it said nothing.
    """
    report, design, package = build(tmp_path)
    result = run(report, design, package)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "every floor holds" in result.stdout


def test_the_floors_are_read_from_the_design_and_not_typed_into_the_checker(
    tmp_path: pathlib.Path,
) -> None:
    """THIS CASE EXISTS BECAUSE ITS ABSENCE WAS MEASURED.

    Amputation row A15 replaced `parse_design`'s floors with ADR-0010's
    numbers hard-coded into the checker and **every other case in this
    file stayed green**. That is precisely the defect the checker's
    docstring claims to avoid - a second copy of a decision, which this
    repository has watched rot in a brief, two obligation rows, a CI
    comment and three harness floors - and nine controls could not see
    it, because a stricter typed-in floor refuses everything a looser
    derived one refuses.

    Two arms, and the second is the one that kills A15:

    - the checker PRINTS the floors it derived, and they must be the
      synthetic design's numbers rather than the repository's;
    - a module BETWEEN the two must PASS. At 85% line it clears the
      synthetic design's 80% critical floor and fails ADR-0010's 95%,
      so a checker reading the design exits 0 here and a checker
      carrying its own copy exits 1.
    """
    report, design, package = build(
        tmp_path,
        files={
            "src/synthetic/alpha.py": summary(100, 85, 100, 89),
            "src/synthetic/beta.py": summary(100, 100, 20, 20),
            "src/synthetic/client.py": summary(100, 100, 20, 20),
        },
    )
    result = run(report, design, package)

    assert "critical line        80%" in result.stdout, (
        "the checker did not report the synthetic design's line floor, so it "
        "is reading a number from somewhere other than the design"
    )
    assert "critical branch      88%" in result.stdout
    assert "overall              50%" in result.stdout
    assert result.returncode == 0, (
        "a module at 85% line and 89% branch was refused. Those clear the "
        "synthetic design's 80/88 and fail ADR-0010's 95/90, so the floors "
        "being applied are a second copy inside the checker\n" + result.stdout
    )
