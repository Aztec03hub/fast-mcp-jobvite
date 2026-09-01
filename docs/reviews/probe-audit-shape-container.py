#!/usr/bin/env python3
"""THE AUDIT-SHAPE CONTAINER PROBE (task #104).

WHY THIS EXISTS. `docs/reviews/probe-audit-row-container.sh` opens by
arguing that *"a hand-kept list of the places to look is blind to the
member nobody added, so the population here is derived"* - and then
derives that population for exactly ONE shape,
`result_status = "error"`. It is itself a hand-kept list of one. Three
sibling shapes carry the same class of claim and have never been swept:

    emit(...)          does anything assert this audit row EXISTS?
    is_error=True      does anything assert this failure is FLAGGED?
    AuditPhase.X       does anything assert this row's failure POLICY?

`emit(` is first on purpose. Deleting a `result_status` line asks
whether a failure was recorded AS a failure. Deleting an `emit(...)`
asks whether the row exists at all, and a tool that emits no audit row
is strictly worse than one emitting a row with the wrong status.

THE MECHANISM IS THE FIRST DELIVERABLE, NOT A DETAIL. The shell probe's
six rows each carry a hand-written multi-line before/after literal,
because single-line anchors are not unique in these modules (#101
records the bare `except` appearing 3x and the `result_status` line 4x
in one file). Hand-writing forty such literals is precisely the
error-prone step a probe exists to remove, and #91 watched a
row-removal mechanism cut a row in half and still pass `cmp`, `bash -n`
AND a correct row count.

So NO EXTENT IS EVER COMPUTED HERE. `ast` locates the node, the node's
own `end_lineno`/`end_col_offset` give the exact source segment, and
every mutation is followed by two assertions the parser makes for us:

  1. the file still PARSES, and
  2. exactly ONE node of the shape went away (and, for a statement
     deletion, the module's total statement count fell by exactly one).

A row that fails either assertion is REFUSED and reports that it
measured nothing. It never reports a verdict.

THE VERDICT IS THE WHOLE SUITE'S EXIT CODE. A site whose amputation
leaves the suite green is a behaviour the repository has no assertion
about. **Survivors are the OUTPUT, not a failure** - the fix for one is
a test, which is a task and not a build break - so this probe REPORTS
and exits 0 unless it could not run.

PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
and a one-line edit can leave the same size inside one second, in which
case stale bytecode runs and the row fakes a clean result.
"""

from __future__ import annotations

import argparse
import ast
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"

PYTEST_CMD = ["uv", "run", "--frozen", "pytest", "-q", "-p", "no:cacheprovider"]

def _audit_phases() -> tuple[str, ...]:
    """The `AuditPhase` members, READ FROM THE ENUM.

    THIS WAS A HAND-KEPT LIST OF THREE, sitting beside the container it
    describes - the exact shape this probe exists to refuse. It happened
    to be correct, which is how such a list reads right up until someone
    adds a fourth phase: the new member would then be silently excluded
    from `_matches`, its call sites would never enter the population, and
    the sweep would report a clean zero over a set that had quietly
    shrunk. Derived instead, and empty is a hard failure rather than a
    quiet one.
    """
    tree = ast.parse((SRC / "fast_mcp_jobvite" / "audit.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "AuditPhase":
            members = tuple(
                t.id
                for stmt in node.body
                if isinstance(stmt, ast.Assign)
                for t in stmt.targets
                if isinstance(t, ast.Name)
            )
            if not members:
                raise SystemExit("AuditPhase has no members - the derivation broke")
            return members
    raise SystemExit("AuditPhase not found in audit.py - the derivation broke")


AUDIT_PHASES = _audit_phases()


@dataclass(frozen=True)
class Site:
    """One member of a derived population."""

    shape: str
    path: Path
    lineno: int
    col: int
    label: str

    @property
    def key(self) -> str:
        rel = self.path.relative_to(REPO_ROOT)
        return f"{self.shape}|{rel}:{self.lineno}:{self.col}"


@dataclass
class Verdict:
    site: Site
    applied: bool = False
    refused: str = ""
    rc: int | None = None
    tail: str = ""
    killed: list[str] = field(default_factory=list)
    note: str = ""


# ---------------------------------------------------------------------------
# POPULATION DERIVATION. Every shape is derived by walking the parsed
# module, never by a text match: a grep for `emit(` also finds the two
# `def emit(` DEFINITIONS and would count them as call sites, and a grep
# for `is_error=True` finds it inside two docstrings. Both are recorded
# in the report as the reason the raw grep counts are supersets.
# ---------------------------------------------------------------------------


def _source_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def _callee_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _enclosing_stmt(tree: ast.AST, target: ast.AST) -> ast.stmt | None:
    """The nearest ancestor statement of `target`, found by the parser.

    This is the reason no extent is written by hand: the statement that
    OWNS a call is whatever `ast` says owns it, including when the call
    spans several physical lines.
    """
    best: ast.stmt | None = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        for child in ast.walk(node):
            if child is target:
                if best is None or node.lineno >= best.lineno:
                    best = node
                break
    return best


def derive(shape: str) -> list[Site]:
    sites: list[Site] = []
    for path in _source_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not _matches(node, shape):
                continue
            sites.append(Site(shape, path, node.lineno, node.col_offset, _label(node)))
    return sorted(sites, key=lambda s: (str(s.path), s.lineno, s.col))


def _matches(node: ast.AST, shape: str) -> bool:
    if shape == "emit":
        return isinstance(node, ast.Call) and _callee_name(node) == "emit"
    if shape == "is_error":
        return (
            isinstance(node, ast.keyword)
            and node.arg == "is_error"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        )
    if shape == "audit_phase":
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "AuditPhase"
            and node.attr in AUDIT_PHASES
        )
    raise SystemExit(f"unknown shape {shape!r}")


def _label(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return "emit(...)"
    if isinstance(node, ast.keyword):
        return "is_error=True"
    if isinstance(node, ast.Attribute):
        return f"AuditPhase.{node.attr}"
    return "?"


def _find_node(tree: ast.AST, site: Site) -> ast.AST:
    """Re-find a site's node in a freshly parsed tree.

    Position identifies it. Two nodes of one shape cannot share a
    (line, column), so this is unique by construction - and it is
    asserted here rather than assumed.
    """
    hits = [
        n
        for n in ast.walk(tree)
        if getattr(n, "lineno", None) == site.lineno
        and getattr(n, "col_offset", None) == site.col
        and _matches(n, site.shape)
    ]
    if len(hits) != 1:
        raise LookupError(f"{len(hits)} nodes at {site.key}, expected exactly 1")
    return hits[0]


def _offsets(source: str, node: ast.AST) -> tuple[int, int]:
    """Character offsets of a node's exact source segment.

    Taken from the node's OWN end positions. Nothing here counts lines.
    """
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    begin = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    return begin, end


def _count(tree: ast.AST, shape: str) -> int:
    return sum(1 for n in ast.walk(tree) if _matches(n, shape))


def _stmts(tree: ast.AST) -> int:
    return sum(1 for n in ast.walk(tree) if isinstance(n, ast.stmt))


# ---------------------------------------------------------------------------
# THE OPERATORS. One per shape, each chosen so the question it asks is
# the question the shape carries.
# ---------------------------------------------------------------------------


def mutate(source: str, site: Site) -> tuple[str, str]:
    """Return (mutated source, a one-line description of what was done).

    Raises `AssertionError` unless the parser confirms BOTH claims: the
    result parses, and exactly one node of the shape went away.
    """
    tree = ast.parse(source)
    before_shape = _count(tree, site.shape)
    before_stmts = _stmts(tree)
    node = _find_node(tree, site)

    if site.shape == "emit":
        # AMPUTATION: delete the statement that OWNS the call, so the
        # row is never written at all. `ast` names the statement; the
        # deletion leaves a whitespace-only line, which the tokenizer
        # ignores, so no block is ever re-indented by this probe.
        stmt = _enclosing_stmt(tree, node)
        if stmt is None:
            raise LookupError(f"no enclosing statement for {site.key}")
        begin, end = _offsets(source, stmt)
        mutated = source[:begin] + source[end:]
        what = "deleted the statement owning the emit(...) call"
        expect_stmt_delta = 1
    elif site.shape == "is_error":
        # AMPUTATION: remove the keyword. `ToolResult`'s default is
        # false, so the call still constructs - the failure simply
        # stops being FLAGGED as one to the caller. The trailing comma
        # goes with it; that this is legal is not assumed, it is what
        # the re-parse below checks.
        begin, end = _offsets(source, node)
        tail = source[end:]
        eaten = 0
        while eaten < len(tail) and tail[eaten] in " \t":
            eaten += 1
        if eaten < len(tail) and tail[eaten] == ",":
            eaten += 1
        mutated = source[:begin] + source[end + eaten :]
        what = "removed the is_error=True keyword"
        expect_stmt_delta = 0
    elif site.shape == "audit_phase":
        # SUBSTITUTION, not deletion: deleting this argument would only
        # break the call's arity, which every test would kill for a
        # reason that has nothing to do with auditing. Rotating the
        # member asks the question the shape actually carries - is this
        # row's FAILURE POLICY asserted by anything?
        current = node.attr
        nxt = (AUDIT_PHASES.index(current) + 1) % len(AUDIT_PHASES)
        replacement = AUDIT_PHASES[nxt]
        begin, end = _offsets(source, node)
        mutated = source[:begin] + f"AuditPhase.{replacement}" + source[end:]
        what = f"substituted AuditPhase.{current} -> AuditPhase.{replacement}"
        expect_stmt_delta = 0
    else:  # pragma: no cover - guarded by the CLI choices
        raise SystemExit(f"unknown shape {site.shape!r}")

    # ASSERTION 1 - IT STILL PARSES. A mutation that cannot be parsed
    # kills the whole suite and would be read as a strong verdict.
    after = ast.parse(mutated)

    # ASSERTION 2 - EXACTLY ONE NODE WENT AWAY. This is what #91's
    # half-cut row would have failed. A substitution keeps the count, so
    # it is held to a different pair of claims instead.
    after_shape = _count(after, site.shape)
    if site.shape == "audit_phase":
        if after_shape != before_shape:
            raise AssertionError(
                f"{site.key}: substitution changed the shape count "
                f"{before_shape} -> {after_shape}"
            )
        if mutated == source:
            raise AssertionError(f"{site.key}: substitution was a no-op")
    elif after_shape != before_shape - 1:
        raise AssertionError(
            f"{site.key}: expected exactly one {site.shape} node to go away, "
            f"count went {before_shape} -> {after_shape}"
        )

    after_stmts = _stmts(after)
    if after_stmts != before_stmts - expect_stmt_delta:
        raise AssertionError(
            f"{site.key}: expected the statement count to fall by "
            f"{expect_stmt_delta}, it went {before_stmts} -> {after_stmts}"
        )
    return mutated, what


# ---------------------------------------------------------------------------


def run_suite() -> tuple[int, str]:
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        PYTEST_CMD,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def killed_tests(out: str) -> list[str]:
    return sorted(
        {ln.split(" ")[1] for ln in out.splitlines() if ln.startswith("FAILED ")}
    )


def probe(site: Site, backup_dir: Path, dry: bool) -> Verdict:
    verdict = Verdict(site=site)
    backup = backup_dir / f"{site.lineno}_{site.col}_{site.path.name}"
    shutil.copy2(site.path, backup)
    original = site.path.read_text()
    try:
        try:
            mutated, what = mutate(original, site)
        except (AssertionError, LookupError, SyntaxError) as exc:
            verdict.refused = f"{type(exc).__name__}: {exc}"
            return verdict
        verdict.note = what
        site.path.write_text(mutated)

        # LANDING IS COMPARED, NOT ASSUMED. A write that changed nothing
        # exits 0 and the suite then passes for an unrelated reason.
        if filecmp.cmp(str(site.path), str(backup), shallow=False):
            verdict.refused = "mutation did not land despite a successful write"
            return verdict
        verdict.applied = True
        if dry:
            return verdict
        verdict.rc, out = run_suite()
        verdict.tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
        verdict.killed = killed_tests(out)
        if verdict.rc != 0 and "NameError" in out:
            verdict.note += "  [a NameError appears in the output - see the report]"
        return verdict
    finally:
        # RESTORE BY BYTE COMPARISON AGAINST A BACKUP, never by a
        # reverse edit: a `sed` that matches nothing succeeds silently.
        shutil.copy2(backup, site.path)
        if not filecmp.cmp(str(site.path), str(backup), shallow=False):
            print(f"!!! RESTORE FAILED for {site.key}", flush=True)


def tree_is_clean() -> bool:
    """Both trees, not just `src/`.

    The shell probe checks `src/` alone, which is adequate for its own
    mutations and would not be for a wider sweep.
    """
    ok = True
    for area in ("src/", "tests/"):
        proc = subprocess.run(  # noqa: S603
            ["git", "diff", "--quiet", "--", area], cwd=REPO_ROOT, check=False
        )
        if proc.returncode != 0:
            ok = False
            print(f"TREE LEFT DIRTY UNDER {area} - a restore failed.")
            subprocess.run(  # noqa: S603
                ["git", "diff", "--stat", "--", area], cwd=REPO_ROOT, check=False
            )
        status = subprocess.run(  # noqa: S603
            ["git", "status", "--porcelain", "--", area],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        untracked = [ln for ln in status.stdout.splitlines() if ln.startswith("??")]
        if untracked:
            ok = False
            print(f"UNTRACKED FILES LEFT UNDER {area}: {untracked}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="the audit-shape container probe")
    ap.add_argument(
        "--shape",
        action="append",
        choices=["emit", "is_error", "audit_phase"],
        help="repeatable; default is all three, emit first",
    )
    ap.add_argument("--list", action="store_true", help="print the population and stop")
    ap.add_argument(
        "--only",
        action="append",
        default=None,
        metavar="SUBSTRING",
        help=(
            "repeatable; sweep only sites whose key contains SUBSTRING. THE "
            "SWEPT SET IS STILL COMPARED TO THE FULL DERIVED POPULATION, so a "
            "chunked run prints the sites it did not cover instead of "
            "reporting a clean sweep of a set it quietly shrank. Exists "
            "because a 34-row run takes ~43 minutes and a harness killed "
            "mid-row leaves its mutation in the tree."
        ),
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="apply and restore every mutation without running the suite",
    )
    args = ap.parse_args()
    shapes = args.shape or ["emit", "is_error", "audit_phase"]

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    population: dict[str, list[Site]] = {s: derive(s) for s in shapes}
    # THE SELECTION IS SEPARATE FROM THE POPULATION, always. `--only` narrows
    # what is RUN; it never narrows what the run is JUDGED against, so a
    # chunked sweep cannot report a clean zero over a set it quietly shrank.
    selected: dict[str, list[Site]] = {
        s: [
            site
            for site in population[s]
            if not args.only or any(frag in site.key for frag in args.only)
        ]
        for s in shapes
    }

    print("THE DERIVED POPULATION - every site must appear as a row below:")
    for shape in shapes:
        print(f"\n  [{shape}]  {len(population[shape])} sites")
        for site in population[shape]:
            rel = site.path.relative_to(REPO_ROOT)
            mark = "   " if site in selected[shape] else "  (not selected)"
            print(f"    {rel}:{site.lineno}:{site.col}  {site.label}{mark}")
    if args.only:
        total_sel = sum(len(selected[s]) for s in shapes)
        total_pop = sum(len(population[s]) for s in shapes)
        print(
            f"\n  --only IS IN FORCE: {total_sel} of {total_pop} sites selected. "
            "THIS IS A PARTIAL RUN and says so in the tally below."
        )
    print(flush=True)
    if args.list:
        return 0

    verdicts: list[Verdict] = []
    backup_dir = Path(tempfile.mkdtemp(prefix="audit-shapes-"))
    try:
        for shape in shapes:
            print(f"========== SHAPE: {shape}", flush=True)
            for site in selected[shape]:
                verdict = probe(site, backup_dir, args.dry_run)
                verdicts.append(verdict)
                rel = site.path.relative_to(REPO_ROOT)
                label = f"{rel}:{site.lineno} {site.label}"
                if verdict.refused:
                    print(f"  {label:<62} REFUSED: {verdict.refused}", flush=True)
                    continue
                if args.dry_run:
                    print(f"  {label:<62} APPLIED  ({verdict.note})", flush=True)
                    continue
                print(f"  {label:<62} exit {verdict.rc}  {verdict.tail}")
                if verdict.note:
                    print(f"      {verdict.note}")
                for name in verdict.killed:
                    print(f"      killed: {name}")
                if verdict.rc == 0:
                    print("      *** VACUOUS: nothing in the suite asserts this ***")
                sys.stdout.flush()
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)

    print()
    rc = 0
    for shape in shapes:
        rows = [v for v in verdicts if v.site.shape == shape]
        applied = [v for v in rows if v.applied]
        vacuous = [v for v in applied if v.rc == 0]
        print(
            f"{shape:<12} POPULATION: {len(population[shape]):<3} "
            f"ROWS: {len(rows):<3} APPLIED: {len(applied):<3} "
            f"VACUOUS: {len(vacuous)}"
        )
        # THE SWEPT SET MUST EQUAL THE DERIVED POPULATION. Not a count -
        # the SETS, so a row that silently probed the wrong site is a
        # failure rather than an arithmetic coincidence. Under `--only` the
        # shortfall is NAMED rather than tolerated: an unswept site is
        # printed every run, so a partial sweep can never be mistaken for a
        # complete one by reading the tally.
        swept = {v.site.key for v in rows}
        derived = {s.key for s in population[shape]}
        if swept != derived:
            for key in sorted(derived - swept):
                print(f"  NOT SWEPT (no verdict exists for this site): {key}")
            for key in sorted(swept - derived):
                print(f"  SWEPT BUT NOT IN THE POPULATION: {key}")
            if not args.only:
                rc = 3
        if len(applied) != len(rows):
            print("  A ROW DID NOT APPLY. It measured nothing and said so.")
            rc = 3

    # AND THE POPULATION IS RE-DERIVED FROM THE RESTORED TREE, so a
    # mutation that survived restoration cannot hide by having changed
    # the population it is measured against.
    for shape in shapes:
        if {s.key for s in derive(shape)} != {s.key for s in population[shape]}:
            print(f"POPULATION MOVED DURING THE RUN for {shape}. STOPPING.")
            rc = 3

    if not tree_is_clean():
        return 3
    print("TREE RESTORED CLEAN UNDER src/ AND tests/")
    return rc


if __name__ == "__main__":
    sys.exit(main())
