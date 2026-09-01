#!/usr/bin/env python3
"""Controls for #142: only the register grants an exemption.

Every arm PLANTS into a real tracked file, runs the real wired gate as a
subprocess, reads its exit code, and restores the file - then proves the
restore landed by asking git, not by comparing strings.

Addresses and the marker are BUILT BY CONCATENATION, never written as
literals, so this probe does not need an exemption of its own. A control
that has to exempt itself from the thing it is controlling is the defect
(#142).

    python3 docs/reviews/probe-142-exempt-controls.py
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BOUNDS = "docs/reviews/check-design-citations.py"
SHAPE = "docs/reviews/check-design-citation-shape.py"
REGISTER = ROOT / "docs" / "reviews" / "REPOINT-EXEMPT.txt"

MARKER = "REPOINT" + "-EXEMPT"
OOB = "DESIGN" + ".md:" + "99999-99999"
REGISTERED = "DESIGN" + ".md:" + "373-383"

#: A tracked file with no citations of its own, so a plant is the only
#: thing the gate can be reacting to.
VICTIM = ROOT / "src" / "fast_mcp_jobvite" / "audit.py"


def run(checker: str) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, checker],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return done.returncode, done.stdout + done.stderr


def bounds_exempt_count(out: str) -> int:
    for line in out.splitlines():
        if "citations exempt (marked AND registered):" in line:
            return int(line.rsplit(":", 1)[1])
    return -1


def plant(path: pathlib.Path, text: str) -> None:
    path.write_text(text + path.read_text())


def restored(rel: str) -> bool:
    return (
        subprocess.run(
            ["git", "diff", "--quiet", "--", rel], cwd=ROOT, check=False
        ).returncode
        == 0
    )


def main() -> int:
    victim_rel = VICTIM.relative_to(ROOT).as_posix()
    assert restored(victim_rel), f"{victim_rel} is dirty before the probe starts"
    original = VICTIM.read_text()
    register_original = REGISTER.read_text()

    base_rc, base_out = run(BOUNDS)
    base_n = bounds_exempt_count(base_out)
    shape_rc, _ = run(SHAPE)

    results: list[tuple[str, bool, str]] = [
        (
            "NEGATIVE  the registered exemptions still skip: both gates green",
            base_rc == 0 and shape_rc == 0 and base_n > 0,
            f"bounds exit {base_rc}, shape exit {shape_rc}, {base_n} exempt",
        )
    ]

    arms: list[tuple[str, str, bool]] = [
        # label, planted line, must the bounds gate go RED?
        (
            "POSITIVE  a BARE marker no longer exempts anything",
            f"# PLANT {OOB} {MARKER}\n",
            True,
        ),
        (
            "POSITIVE  a marker on an UNREGISTERED path is refused",
            f"# PLANT {OOB} {MARKER}  (registered for another file, not this one)\n",
            True,
        ),
        (
            "RECURSION  prose DESCRIBING the mechanism exempts nothing",
            f'# The register grants exemptions; a line saying "{MARKER}" does not.\n'
            f"# {OOB}\n",
            True,
        ),
        (
            "NEGATIVE  a citation with no marker and no row is checked as "
            "normal (the plant is seen at all)",
            f"# PLANT {OOB}\n",
            True,
        ),
    ]

    for label, planted, must_be_red in arms:
        try:
            plant(VICTIM, planted)
            rc, out = run(BOUNDS)
        finally:
            VICTIM.write_text(original)
        ok = (rc != 0) if must_be_red else (rc == 0)
        named = victim_rel in out
        results.append(
            (label, ok and named, f"exit {rc}, plant named in output: {named}")
        )
        if not restored(victim_rel):
            results.append((f"RESTORE after {label!r}", False, "git says still dirty"))

    # THE TRUE MISMATCH ARM. The earlier arms plant an address
    # registered for NO path; this one registers 373-383 FOR THE
    # VICTIM and plants a line carrying both it and an
    # unregistered address. The registered one must be skipped and
    # the other must still be reported - the granularity half of
    # R13-H1, tested rather than asserted.
    try:
        REGISTER.write_text(
            register_original
            + f"{victim_rel}\t373-383\ta probe row for the scope-mismatch arm\n"
        )
        plant(VICTIM, f"# PLANT {REGISTERED} and {OOB} {MARKER}\n")
        rc, out = run(BOUNDS)
        mismatch_n = bounds_exempt_count(out)
    finally:
        VICTIM.write_text(original)
        REGISTER.write_text(register_original)
    results.append(
        (
            "MISMATCH  a registered scope on the line does NOT cover the other "
            "citation beside it",
            rc != 0 and victim_rel in out and mismatch_n == base_n + 1,
            f"exit {rc}, exempt {base_n} -> {mismatch_n}"
            " (the registered half WAS skipped)",
        )
    )

    # AMPUTATION. Put the OLD behaviour back - the bare-substring
    # test - and the positive arms above must DIE. Without this,
    # every arm passes on a checker that reports everything.
    loader = ROOT / "docs" / "reviews" / "repoint_exempt.py"
    loader_original = loader.read_text()
    anchor = "    return MARKER in line and reason(rel_path, start, end) is not None"
    assert loader_original.count(anchor) == 1, "amputation anchor is not unique"
    try:
        loader.write_text(loader_original.replace(anchor, "    return MARKER in line"))
        plant(VICTIM, f"# PLANT {OOB} {MARKER}\n")
        amp_rc, _ = run(BOUNDS)
    finally:
        VICTIM.write_text(original)
        loader.write_text(loader_original)
    results.append(
        (
            "AMPUTATE  restoring the bare-substring test makes the plant PASS "
            "again, so the arms above are reading the register",
            amp_rc == 0,
            f"exit {amp_rc} (0 = the R13-H1 defect is back, as required)",
        )
    )

    # The count arm. Adding one legitimate row must move the
    # printed number, and removing it must move it back. A count
    # that never moves is a constant with a plausible story.
    try:
        REGISTER.write_text(
            register_original
            + f"{victim_rel}\t99999-99999\ta probe row proving the count moves\n"
        )
        plant(VICTIM, f"# PLANT {OOB} {MARKER}\n")
        rc, out = run(BOUNDS)
        moved_n = bounds_exempt_count(out)
    finally:
        VICTIM.write_text(original)
        REGISTER.write_text(register_original)
    results.append(
        (
            "COUNT     one added row moves the printed count and greens the plant",
            rc == 0 and moved_n == base_n + 1,
            f"exit {rc}, count {base_n} -> {moved_n}",
        )
    )

    back_rc, back_out = run(BOUNDS)
    results.append(
        (
            "RESTORE   the register and the victim are back as git has them",
            back_rc == 0
            and bounds_exempt_count(back_out) == base_n
            and restored(victim_rel)
            and restored("docs/reviews/REPOINT-EXEMPT.txt"),
            f"exit {back_rc}, count {bounds_exempt_count(back_out)}",
        )
    )

    fired = 0
    for label, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}  ({detail})")
        fired += ok
    print(f"\n{fired}/{len(results)} control arms passed.")
    return 0 if fired == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
