#!/usr/bin/env python3
"""Amputate each construct in `check-checkers-are-wired.py`.

**THE FOUR ARMS THIS EXISTS FOR ALL SURVIVED, AND THEY SURVIVED AS
A MARKDOWN TABLE.** R14 measured them by hand, wrote the counts into
a review, and a review is a claim about a measurement rather than the
measurement. The next person to touch `_script_of` would have got no
signal at all. So the arms are a program now.

Read WHICH rows die, never the exit code alone. An arm that kills two
rows for the wrong reason and an arm that kills the right two are the
same integer.

Arm B is INVERSE on purpose. The `--` branch was deleted as
inoperative (R14 L-3), so there is nothing left to amputate; the arm
puts it BACK and asserts nothing changes. A deletion undetectable in
either direction is the proof the branch was dead, and this keeps a
live check on that ruling instead of a sentence about it.

WIRED, in a JOB OF ITS OWN (#149 M-4), and the shape is the ruling.

The container arms `git add -f` a fixture into the index and remove it
in a `finally`. That is why this could not be a step beside its
subject: a job whose index is being staged and unstaged under other
steps is a job with a bomb in it, and SIGKILL runs no `finally`. But
"cannot share a job" is not "cannot run in CI" - a runner's checkout is
disposable and nothing else reads it - so this gets a job with its own
checkout, and the objection is answered without a scratch-clone
refactor of a file that is measuring correctly.

IT IS NOT A `scripts/*.sh` HARNESS, AND THAT CONTAINER STAYS AS IT IS.
`check-harness-result.sh` enforces three properties - sourcing
`lib/harness-result.sh`, chaining the emitter onto an `EXIT` trap, and
calling `harness_result_ran` - and all three are bash constructs with
no Python meaning. The thing they buy, that an ABORTED harness cannot
render identically to a pass, Python already has: an interrupted run
raises and exits nonzero with a traceback. Widening that container to
23 Python probes would be a large unasked sweep whose members could not
satisfy the properties being checked. So the ruling is: the container
stays `scripts/*.sh`, and this file prints the canonical line anyway,
so #120's census can count it if that ever changes.

WHAT WAS MISSING WAS THE FLOOR, not the format. `failures == 0` is
satisfied by zero arms; `main()` now holds `rows` to a floor.

Run with `uv run --frozen python` on
`docs/reviews/probe-wired-checker-amputation.py` - CI's interpreter,
not a bare one, which is the defect the subject file exists about.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import subprocess
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "docs" / "reviews" / "check-checkers-are-wired.py"

#: The `--` branch as it stood before deletion, and the generic break
#: that already reached the same token. Arm B splices the first back
#: in ahead of the second.
BREAK = '            if not opt.startswith("-") or opt == "-":\n'
BRANCH = '            if opt == "--":\n                j += 1\n                break\n'

#: Every arm's expectation, ASSERTED. A survivor fails this probe; it
#: is not a number somebody has to notice in the output.
EXPECTED = {
    "BASELINE": 0,
    "A _OPT_NO_SCRIPT emptied": 2,
    "B -- branch REINSTATED (inverse)": 0,
    "C _is_ours always True": 1,
    "D _OPT_WITH_VALUE = {-X}": 2,
    "E _MODULE_RUNNERS emptied": 2,
    "F _runner_script always None": 2,
    "G _INTERPRETER loses version suffix": 1,
    "H CONTAINER_DIRS loses scripts/": 1,
    "I wired_names back to a substring": 1,
}


def load() -> types.ModuleType:
    """A FRESH module per arm; one mutated would poison the next."""
    spec = importlib.util.spec_from_file_location(f"wired_{len(sys.modules)}", SRC)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {SRC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reinstate_dashdash(module: types.ModuleType) -> None:
    """Put the deleted `--` branch back, rewriting the real source."""
    src = SRC.read_text(encoding="utf-8")
    count = src.count(BREAK)
    if count != 1:
        raise SystemExit(
            f"anchor occurs {count} times, expected 1. Arm B would "
            "amputate NOTHING and pass for that reason."
        )
    namespace: dict[str, object] = {
        "__file__": str(SRC),
        "__name__": "wired_dashdash",
    }
    patched = src.replace(BREAK, BRANCH + BREAK)
    exec(compile(patched, str(SRC), "exec"), namespace)  # noqa: S102
    module.__dict__.update(namespace)


def _no_script(module: types.ModuleType) -> None:
    module._OPT_NO_SCRIPT = ()  # type: ignore[attr-defined]


def _any_name(module: types.ModuleType) -> None:
    """Every script token is one of ours.

    REPOINTED by #153: the construct was `_CHECKER_NAME`, a regex over
    `check-*`, and it is now `_is_ours`, a container-membership test.
    Amputating the name that no longer exists would have set a NEW
    attribute on the module, changed nothing, and read as a survivor -
    an arm that passes for the wrong reason, which this probe's own
    docstring warns is the same integer as a real one.
    """
    module._is_ours = lambda _: True  # type: ignore[attr-defined]


def _narrow_container(module: types.ModuleType) -> None:
    """Take `scripts/` back out of the container.

    THE EXACT DEFECT #153 FIXED, put back on purpose. Every spelling
    control derives its subject FROM the container, so they all move
    with it and stay green - which is why control 7 had to be written
    as an explicit assertion about the container's SPAN, and why this
    arm is what proves control 7 is not decoration.
    """
    module.CONTAINER_DIRS = ("docs/reviews",)  # type: ignore[attr-defined]


def _substring_wiring(module: types.ModuleType) -> None:
    """Match a name anywhere in the text, as the old test did.

    This is the false GREEN #153's widening surfaced on its first run:
    `harness-result.sh` read WIRED because `check-harness-result.sh`
    is invoked and contains it.
    """
    collision = "check-design-citations.py"[len("check-") :]

    def substring(text: str) -> set[str]:
        return {n for n in module.checkers() if n in text} | {collision}

    module.wired_names = substring  # type: ignore[attr-defined]


def _one_opt(module: types.ModuleType) -> None:
    module._OPT_WITH_VALUE = frozenset({"-X"})  # type: ignore[attr-defined]


def _no_runners(module: types.ModuleType) -> None:
    module._MODULE_RUNNERS = frozenset()  # type: ignore[attr-defined]


def _runner_blind(module: types.ModuleType) -> None:
    module._runner_script = lambda _: None  # type: ignore[attr-defined]


def _no_version(module: types.ModuleType) -> None:
    module._INTERPRETER = re.compile(r"^python3?$")  # type: ignore[attr-defined]


ARMS: list[tuple[str, object]] = [
    ("BASELINE", None),
    ("A _OPT_NO_SCRIPT emptied", _no_script),
    ("B -- branch REINSTATED (inverse)", reinstate_dashdash),
    ("C _is_ours always True", _any_name),
    ("D _OPT_WITH_VALUE = {-X}", _one_opt),
    ("E _MODULE_RUNNERS emptied", _no_runners),
    ("F _runner_script always None", _runner_blind),
    ("G _INTERPRETER loses version suffix", _no_version),
    ("H CONTAINER_DIRS loses scripts/", _narrow_container),
    ("I wired_names back to a substring", _substring_wiring),
]


#: A name chosen to be a FOURTH prefix - not `check-`, not `probe-`,
#: not `measure-`. Under the old population it could never have been
#: seen; under the container it must be, and that is the whole point of
#: selecting by kind. It is built by concatenation so this file does
#: not itself contain a name the checker would enumerate if the probe
#: were ever tracked mid-run.
NEW_MEMBER = "verify-" + "container-arm.py"

#: BOTH HALVES OF THE CONTAINER GET THE ARMS, and that is R16-M1's
#: point rather than symmetry for its own sake. `scripts/` is the half
#: that was excluded, and `scripts/check-timeout-literals.py` is the
#: real file that sat unwired and INVISIBLE there while this checker
#: printed "Every checker is wired". A control that only ever plants
#: into `docs/reviews/` proves the enumeration works in the half that
#: was never broken.
#:
#: Planting a fixture is used rather than naming a real `scripts/`
#: member, because a row naming one would go stale the day somebody
#: wires it - and asserting "some scripts/ member is still unwired"
#: would be red BY CONSTRUCTION once they all are.
CONTAINER_HALVES = (
    ROOT / "docs" / "reviews",
    ROOT / "scripts",
)


def _run_checker() -> tuple[int, str]:
    """Run the REAL checker as a subprocess and read ITS exit code.

    A subprocess, not an import: the claim is about what CI's step
    does, and an in-process call would test a function rather than the
    artifact. This project has already recorded that a control which
    never runs the artifact tests a proxy.
    """
    done = subprocess.run(
        [sys.executable, str(SRC)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return done.returncode, done.stdout + done.stderr


def container_arms(directory: pathlib.Path) -> list[str]:
    """THE POSITIVE CONTROL, BOTH ARMS, in one half of the container.

    #153 §E, and R16-M1 for the `scripts/` half.

    A widened population is worth nothing unless a NEW member actually
    lands in it and actually fails the gate. Both directions, because
    either alone is consistent with a broken instrument:

      ARM 1 (RED)   a newly tracked file with no recorded reason must
                    make the checker exit 1 AND NAME IT. Reading only
                    the exit code would let any other failure - a stale
                    exemption, a bare interpreter - pass for this one.
      ARM 2 (GREEN) the same file with a reason recorded must exit 0.
                    Without this arm, a checker that simply always
                    failed would pass arm 1.

    **RUN ONCE PER DIRECTORY, and that is the load-bearing part rather
    than tidiness.** The half that was excluded is `scripts/`, and the
    real file that sat unwired and invisible there is
    `scripts/check-timeout-literals.py` (R16-M1) - committed unwired by
    the task that built it, at exit 0. A control that only ever plants
    into `docs/reviews/` proves the enumeration works in the half that
    was never broken, and would pass unchanged on the OLD code for the
    directory that mattered.

    The file is `git add`ed because `git ls-files` lists only TRACKED
    files - an untracked file is invisible to the container, which is
    the same mechanism that made this checker's own self-exclusion
    comment inert for a commit, and the same one that made an R16 arm
    vacuous. Restored in a `finally`, and the tree is asserted clean by
    asking git afterwards rather than by trusting the unlink.
    """
    problems: list[str] = []
    new_path = directory / NEW_MEMBER
    where = new_path.relative_to(ROOT).as_posix()
    try:
        new_path.write_text(
            "#!/usr/bin/env python3\n"
            '"""A member with no recorded reason. Probe fixture."""\n',
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "-C", str(ROOT), "add", "-f", str(new_path)],
            check=True,
            capture_output=True,
        )

        code, out = _run_checker()
        if code == 0:
            problems.append(
                f"ARM 1: a new tracked `{where}` with no reason left "
                "the checker GREEN. The container is not seeing new "
                "members in that directory."
            )
        elif NEW_MEMBER not in out:
            problems.append(
                f"ARM 1: the checker exited {code} but never named "
                f"`{where}`. It went red for another reason, so this "
                "arm proves nothing about the container."
            )

        # ARM 2: record a reason, in the shape the register uses.
        module = load()
        module.UNWIRED_BY_DECISION[NEW_MEMBER] = (
            "probe fixture: the GREEN arm of the container control."
        )
        names = set(module.checkers())
        if NEW_MEMBER not in names:
            problems.append(
                f"ARM 2: `{where}` is not in the enumerated container "
                "at all, so the arm cannot mean anything."
            )
        else:
            text, _ = module.run_bodies()
            invoked = module.wired_names(text)
            unwired = names - invoked
            excused = {
                n for n in unwired if module.UNWIRED_BY_DECISION.get(n, "").strip()
            }
            if NEW_MEMBER not in excused:
                problems.append(
                    f"ARM 2: `{where}` has a recorded reason and is "
                    "still not excused. A reason does not settle it."
                )
            if unwired - excused:
                problems.append(
                    "ARM 2: other members are unexplained, so a GREEN "
                    "here would not be attributable to the reason: "
                    f"{sorted(unwired - excused)}"
                )
    finally:
        subprocess.run(
            ["git", "-C", str(ROOT), "rm", "-f", "--quiet", str(new_path)],
            capture_output=True,
        )
        new_path.unlink(missing_ok=True)

    dirty = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", str(new_path)],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if dirty:
        problems.append(
            f"the fixture was not fully restored: `{dirty}`. Fix the "
            "tree before trusting any verdict above."
        )
    return problems


def main() -> int:
    """Run every arm, print the rows it killed, hold it to EXPECTED."""
    failures: list[str] = []
    for label, mutate in ARMS:
        module = load()
        if mutate is not None:
            mutate(module)  # type: ignore[operator]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            module.self_test()
        killed = [
            line.strip()
            for line in buffer.getvalue().splitlines()
            if "CONTROL FAILED" in line
        ]
        print(f"\n{label}: {len(killed)} row(s) killed")
        for line in killed:
            print(f"    {line}")
        want = EXPECTED[label]
        if len(killed) != want:
            failures.append(f"{label}: killed {len(killed)}, expected {want}")

    print("\nCONTAINER POSITIVE CONTROL (#153 §E, R16-M1), both arms,")
    print("ONCE PER HALF OF THE CONTAINER:")
    halves = 0
    for directory in CONTAINER_HALVES:
        halves += 1
        where = directory.relative_to(ROOT).as_posix()
        container_problems = container_arms(directory)
        if container_problems:
            for line in container_problems:
                print(f"    FAILED [{where}/]: {line}")
            failures.extend(container_problems)
        else:
            print(f"    {where}/  ARM 1 (no reason -> RED, and NAMED): ok")
            print(f"    {where}/  ARM 2 (reason recorded -> excused):  ok")

    rows = len(ARMS) + 2 * halves
    print(f"\narms={rows} failures={len(failures)}")
    for line in failures:
        print(f"  {line}")

    # THE ROW FLOOR (#149 M-4). `failures == 0` is satisfied by zero
    # arms, so a probe whose ARMS list was emptied - or whose container
    # halves stopped being iterated - reports fully green. Derived from
    # a run at the commit that adds this: ten ARMS plus two arms in each
    # of two container halves. Lowering it is a visible diff that has to
    # be defended.
    floor = 14
    status = "ok" if not failures and rows >= floor else "breach"
    # The SAME canonical line every harness in `scripts/` prints (#107),
    # deliberately, rather than a second shape. The container that
    # `check-harness-result.sh` enforces is `scripts/*.sh` and this file
    # is outside it by construction - see the ruling in this file's
    # header - but printing the same line means #120's census can count
    # it the day that container grows, and a reader does not have to
    # learn a second format to read this one.
    print(
        f"HARNESS-RESULT name={pathlib.Path(__file__).name} rows={rows} "
        f"floor={floor} fired={rows - len(failures)}/{rows} status={status}"
    )
    if rows < floor:
        print(f"\n{rows}/{floor} ROWS - THE PROBE LOST ARMS. A probe with")
        print("fewer arms than its floor is green for the wrong reason.")
        return 1
    if failures:
        print("\nAn arm moved. Either a control was lost or a construct")
        print("is now dead code. Read WHICH rows changed before")
        print("touching either file.")
        return 1
    print(f"{rows}/{rows} arms measured as expected. No survivor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
