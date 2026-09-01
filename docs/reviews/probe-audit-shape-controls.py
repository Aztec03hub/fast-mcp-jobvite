#!/usr/bin/env python3
"""CONTROLS FOR THE AUDIT-SHAPE CONTAINER PROBE (task #104).

WHY THIS EXISTS AS A SEPARATE, RUNNABLE FILE. `probe-audit-shape-container.py`
reports survivors, and a survivor is indistinguishable from a probe that
mutated nothing: both print a clean suite. Prose asserting "the probe works"
decays into a claim that it once did, so the controls are a script, run
before any verdict from that probe is believed.

Four controls, each aimed at a different way the sweep could be vacuous:

  A. THE POPULATION IS LIVE, NOT CACHED. Three `emit(...)` call sites are
     planted in `src/` and the derivation must grow by exactly three and
     name them. A derivation frozen into a literal would not move.
  B. A PLANTED SITE THAT MUST BE KILLED IS KILLED. The plant is asserted by
     a planted test, so deleting it MUST take the suite red. If this passes
     green the probe's verdict channel is broken and every "VACUOUS" it has
     ever printed is meaningless.
  C. A PLANTED SITE THAT MUST SURVIVE SURVIVES. Identical shape, identical
     operator, differing ONLY in that no test asserts it. This is the arm
     that proves a survivor is a property of the SUITE and not an artefact
     of the probe - B and C differ by one test file and nothing else.
  D. A ROW WHOSE MUTATION DOES NOT LAND IS REFUSED, NOT SCORED. Two
     independent ways for a row not to land, because they refuse at
     different lines:
       D1 the mutation cannot be parsed (an `emit` that is the sole
          statement of an `if` block; deleting it empties the block), so
          the row is refused BEFORE anything is written;
       D2 the write itself silently does nothing, which is the failure a
          `str.replace` against a moved anchor produces. Forced here by
          neutering `Path.write_text`, and caught by the probe's byte
          comparison against its backup.
     A refused row must report `applied=False` and carry NO exit code. A
     refusal scored as a verdict would read as a survivor.

Exits 0 only if all four hold. Removes its plants and asserts the tree is
clean under BOTH src/ and tests/.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANT_SRC = REPO_ROOT / "src" / "fast_mcp_jobvite" / "_probe_control.py"
PLANT_TEST = REPO_ROOT / "tests" / "test_probe_control_plant.py"

# The three plants live in one file so that B and C are the SAME shape under
# the SAME operator. `asserted_site` and `unasserted_site` have byte-identical
# bodies; the only difference in the whole experiment is that a test names one
# of them.
PLANT_SRC_TEXT = '''"""CONTROL PLANT - written and deleted by docs/reviews/probe-audit-shape-controls.py.

If this file is present in a commit, the control script died without cleaning
up and the tree is dirty. It is not part of the server.
"""

from fast_mcp_jobvite.audit import AuditEvent, AuditPhase, emit


def asserted_site(event: AuditEvent) -> None:
    """CONTROL B. A planted test asserts this emit. Deleting it MUST go red."""
    emit(event, AuditPhase.READ)


def unasserted_site(event: AuditEvent) -> None:
    """CONTROL C. Nothing asserts this emit. Deleting it MUST stay green."""
    emit(event, AuditPhase.READ)


def refused_site(event: AuditEvent, flag: bool) -> None:
    """CONTROL D1. The emit is the sole statement of the block, so deleting
    the statement leaves an empty block and the mutation cannot parse."""
    if flag:
        emit(event, AuditPhase.READ)
'''

PLANT_TEST_TEXT = '''"""CONTROL PLANT - written and deleted by docs/reviews/probe-audit-shape-controls.py."""

from unittest.mock import patch

from fast_mcp_jobvite import _probe_control


def test_asserted_site_emits_its_audit_row() -> None:
    with patch.object(_probe_control, "emit") as spy:
        _probe_control.asserted_site(object())  # type: ignore[arg-type]
    assert spy.call_count == 1, "the planted audit row was not emitted"
'''


def load_probe():
    path = REPO_ROOT / "docs" / "reviews" / "probe-audit-shape-container.py"
    if not path.exists():  # a search at a path that does not exist exits clean
        raise SystemExit(f"the probe under test is not at {path}")
    spec = importlib.util.spec_from_file_location("_shape_probe", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # REGISTERED BEFORE EXECUTION: `@dataclass` resolves its annotations through
    # `sys.modules[cls.__module__]`, so a module executed without being
    # registered raises AttributeError on the first dataclass.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _fn_of(site) -> str:
    """Which planted function a site falls in, by reading the source."""
    lines = PLANT_SRC.read_text().splitlines()
    current = ""
    for i, line in enumerate(lines, start=1):
        if line.startswith("def "):
            current = line[4:].split("(")[0]
        if i == site.lineno:
            return current
    return ""


def find(sites, name: str):
    hits = [s for s in sites if s.path == PLANT_SRC and _fn_of(s) == name]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly 1 planted emit in {name}, got {len(hits)}")
    return hits[0]


def tree_clean() -> bool:
    out = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "status", "--porcelain", "--", "src/", "tests/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if out.stdout.strip():
        print("TREE NOT CLEAN under src/ and tests/:")
        print(out.stdout)
        return False
    return True


def main() -> int:
    if not tree_clean():
        print("REFUSING TO START: src/ or tests/ is already dirty.")
        return 3

    probe_mod = load_probe()
    before = probe_mod.derive("emit")
    print(f"population BEFORE planting: {len(before)}")

    PLANT_SRC.write_text(PLANT_SRC_TEXT)
    PLANT_TEST.write_text(PLANT_TEST_TEXT)
    backup_dir = Path(tempfile.mkdtemp(prefix="audit-shape-controls-"))
    failures: list[str] = []
    try:
        # ------------------------------------------------- CONTROL A
        after = probe_mod.derive("emit")
        print(f"population AFTER planting:  {len(after)}")
        grew = len(after) - len(before)
        planted = [s for s in after if s.path == PLANT_SRC]
        if grew != 3 or len(planted) != 3:
            failures.append(
                f"A: derivation grew by {grew} and found {len(planted)} planted "
                "sites, expected 3 and 3 - the population is not live"
            )
        else:
            print("A PASS: the derivation grew by exactly 3 and named the plants")

        asserted = find(after, "asserted_site")
        unasserted = find(after, "unasserted_site")
        refused = find(after, "refused_site")

        # ------------------------------------------------- CONTROL B
        v = probe_mod.probe(asserted, backup_dir, False)
        print(f"B: applied={v.applied} rc={v.rc} killed={v.killed} tail={v.tail!r}")
        if not v.applied:
            failures.append(f"B: the mutation did not apply: {v.refused}")
        elif v.rc == 0:
            failures.append(
                "B: DELETING AN ASSERTED AUDIT ROW LEFT THE SUITE GREEN. The "
                "probe's verdict channel is broken; no VACUOUS it prints means "
                "anything."
            )
        elif not any("_probe_control" in k or "probe_control_plant" in k for k in v.killed):
            failures.append(
                f"B: the suite went red but the planted test is not among the "
                f"killed tests {v.killed} - it died for an unrelated reason"
            )
        else:
            print("B PASS: the asserted plant was killed, by its own test")

        # ------------------------------------------------- CONTROL C
        v = probe_mod.probe(unasserted, backup_dir, False)
        print(f"C: applied={v.applied} rc={v.rc} killed={v.killed} tail={v.tail!r}")
        if not v.applied:
            failures.append(f"C: the mutation did not apply: {v.refused}")
        elif v.rc != 0:
            failures.append(
                f"C: the unasserted plant was killed (rc={v.rc}, {v.killed}). The "
                "operator has a side effect beyond the audit row, so every "
                "survivor this probe reports is understated."
            )
        else:
            print("C PASS: the unasserted plant survived - a survivor is real")

        # ------------------------------------------------- CONTROL D1
        v = probe_mod.probe(refused, backup_dir, False)
        print(f"D1: applied={v.applied} refused={v.refused!r} rc={v.rc}")
        if v.applied or not v.refused or v.rc is not None:
            failures.append(
                f"D1: an unparseable mutation was SCORED, not refused "
                f"(applied={v.applied}, rc={v.rc})"
            )
        else:
            print(f"D1 PASS: refused, no verdict - {v.refused}")

        # ------------------------------------------------- CONTROL D2
        # The write silently does nothing. This is the `str.replace` against a
        # moved anchor failure, and it must be caught by the byte comparison.
        def _write_nothing(*_args: object, **_kwargs: object) -> int:
            return 0

        with patch.object(Path, "write_text", _write_nothing):
            v = probe_mod.probe(unasserted, backup_dir, False)
        print(f"D2: applied={v.applied} refused={v.refused!r} rc={v.rc}")
        if v.applied or "did not land" not in v.refused or v.rc is not None:
            failures.append(
                f"D2: a mutation that never landed was SCORED, not refused "
                f"(applied={v.applied}, refused={v.refused!r}, rc={v.rc})"
            )
        else:
            print("D2 PASS: a write that changed nothing was refused, not scored")
    finally:
        PLANT_SRC.unlink(missing_ok=True)
        PLANT_TEST.unlink(missing_ok=True)
        shutil.rmtree(backup_dir, ignore_errors=True)

    if not tree_clean():
        failures.append("the plants were not fully removed")
    restored = probe_mod.derive("emit")
    if {s.key for s in restored} != {s.key for s in before}:
        failures.append("the population did not return to its pre-plant set")

    print()
    if failures:
        for f in failures:
            print(f"CONTROL FAILED - {f}")
        return 3
    print(f"ALL FOUR CONTROLS PASS. Population restored to {len(restored)} emit sites.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
