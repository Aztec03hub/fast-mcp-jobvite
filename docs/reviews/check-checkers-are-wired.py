#!/usr/bin/env python3
"""Every checker in `docs/reviews/` runs in CI, or says why it does not.

    python3 docs/reviews/check-checkers-are-wired.py
    python3 docs/reviews/check-checkers-are-wired.py --self-test

**WHY THIS EXISTS.** Three checkers here were written, measured,
committed - and never wired into CI. Nothing said so. They sat green and
inert while being cited as gates, which is strictly worse than not
having them: an unwired checker is a claim of coverage that costs
nothing to make and nobody can see is false.

**IT IS THE SAME MISTAKE TWICE, WITH THE SAME INSTRUMENT.** The obvious
census is `grep <basename> .github/workflows/ci.yml`. That counts a name
in a COMMENT as wired. Review R12 used it and mislabelled three files; I
used it earlier the same day and reported
`check-design-citation-shape.py` as WIRED, then spent hours calling an
unwired scan a gate. My replacement parser was ALSO wrong: it matched
only block-form `run: |` and missed every single-line `run:`, reporting
`check-coupling.py` as unwired twenty minutes after I had read its step.
The contradiction between two wrong instruments is the only reason
either was caught.

So this file does not grep the workflow. It **parses the YAML** and
reads `jobs.*.steps[].run` - the only place a step can actually execute
- and strips shell comments from those bodies before looking for a name.

**THE EXEMPTION IS A DECISION, NOT A HOLE.** A checker may be unwired on
purpose: `check-review-coverage.py` reports a real backlog and exits 1
until that backlog clears. Being unwired is fine. Being unwired *and
unrecorded* is the defect. So an exemption needs a non-empty reason, and
a blank one is refused.

**IT ALSO CHECKS THE REVERSE, which nothing else here does.** An
exemption naming a checker that IS wired is stale - the reason has
outlived the condition, and a stale exemption is how a list stops
describing the thing it lists. That is a failure too, not a nit.

## Scope, stated rather than assumed

The container is `docs/reviews/check-*.py` and
`docs/reviews/check-*.sh`, enumerated from git. It deliberately does NOT
include `scripts/check-*.sh` - those are the per-unit mutation and
control HARNESSES, and they reach CI through
`scripts/ci-harness-gate.sh` (32 call sites in `ci.yml`), which is its
own container with its own gate. Two different populations with two
different wiring mechanisms; conflating them would make this checker
report on files it cannot judge.

**WHAT IT CANNOT DO.** It proves a checker is INVOKED, not that its exit
code gates the job. A step that runs a checker and swallows its status
reads as WIRED here. That is a real gap, and the four non-gating
shell forms this repo has shipped are the reason to say so out loud
rather than let "wired" imply "gating".
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shlex
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Checkers that are deliberately not wired, each with the reason. **A
#: bare name is refused: the reason IS the exemption**, the same shape
#: `check-no-errexit.py` and `check-settings-are-read.py` use.
UNWIRED_BY_DECISION: dict[str, str] = {
    "check-review-coverage.py": (
        "no longer waiting on a zero: #151 made it a RATCHET against "
        "docs/reviews/review-coverage-backlog.txt, so it exits 0 today "
        "at 58 recorded and fails only when the unread set changes "
        "unrecorded. It is unwired for a different reason now - it "
        "belongs on PULL REQUESTS against origin/main (a merge cannot "
        "record its own sha), and ci.yml is owned by another agent this "
        "run. Wire it with #153's widening, in one ci.yml change."
    ),
    "check-row-floor-control.sh": (
        "a control OF a control: it proves `check-row-floors.py` can still "
        "fail, by breaking a floor on purpose. Running it in CI would "
        "mutate the tree mid-job. Invoked by hand when the floor checker "
        "changes."
    ),
    "check-row-floor-controls.sh": (
        "the plural sibling of the above, same reason: it mutates floors "
        "to watch the checker fire. A control that must break its subject "
        "cannot share a job with the subject."
    ),
    "check-harness-result-controls.sh": (
        "proves `check-harness-result.sh` rejects malformed HARNESS-RESULT "
        "lines by feeding it malformed ones - it must break its subject, "
        "so it cannot share a job with it. Run by hand when the canonical "
        "line changes; 8/8 controls fire as of 2026-09-01."
    ),
}

#: `check-design-citation-shape.py` was here, exempted while #126's 47
#: blank-END citations were swept. The sweep landed, it went green, it
#: was wired, and this entry was deleted in the same commit. That is the
#: exemption working as designed: a reason with a stated end condition,
#: removed when the condition ended rather than left to rot. Had it been
#: left, the stale-exemption check below would have failed the build -
#: which is the point of checking the reverse direction.


def _reasons_are_non_empty() -> None:
    """A blank reason is not an exemption."""
    blank = [k for k, v in UNWIRED_BY_DECISION.items() if not v.strip()]
    if blank:
        raise SystemExit(f"blank exemption reason(s): {blank}")


def checkers() -> list[str]:
    """Basenames of every checker in `docs/reviews/`, from git.

    Enumerated from the CONTAINER, never a hand-kept list beside it -
    a list maintained next to the thing it describes is blind to the
    member nobody added, which is how three checkers went unwired.
    """
    done = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "docs/reviews/check-*.py",
            "docs/reviews/check-*.sh",
        ],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        print(f"git ls-files failed: {done.stderr.strip()}")
        print("This is a BROKEN INSTRUMENT, not a finding. Exit 3.")
        raise SystemExit(3)
    #: THIS FILE IS IN ITS OWN POPULATION, deliberately - a checker that
    #: exempts itself from its own container is the precise blind spot
    #: it exists to catch. **That is ASSERTED by control 4, not claimed
    #: here**, because this comment was INERT when it was written: git
    #: lists only TRACKED files, the checker was still untracked, and it
    #: excluded itself for a reason no line of code mentions. The census
    #: read 26 and became 27 on the commit that tracked it.
    return sorted(pathlib.PurePath(p).name for p in done.stdout.split())


def strip_comments(body: str) -> str:
    """Drop shell comments, so a `#` line does not read as wired.

    This is the exact false positive that mislabelled three checkers
    twice. The rule is deliberately blunt: from an unquoted `#` to end
    of line. A `#` inside a quoted string would be over-stripped, which
    can only ever cause a FALSE 'unwired' - the safe direction for a
    gate whose job is to find things nobody wired.
    """
    return re.sub(r"(?m)(?<!\$)#.*$", "", body)


#: Shell operators that END one command and begin the next. A step body
#: is not one command: `out=$(python3 x.py 2>&1); rc=$?` is three, and
#: without this split the first token is `out=$(python3`, which no
#: interpreter test can match. Sixteen of ci.yml's checker steps are
#: written in exactly that capture-and-check shape.
_SEGMENT = re.compile(r"\$\(|`|\)|\(|&&|\|\||;|\||\{|\}|\n")

#: Runners that reach the PROJECT environment, so a `python` token after
#: one of them is NOT bare, however many flags sit in between.
#:
#: **This is a TOKEN test, and that is the whole fix.** The old form
#: was two negative lookbehinds, `(?<!uv run )(?<!uv run --frozen )`.
#: A Python lookbehind must be FIXED WIDTH, so it can spell exactly
#: one prefix and no other, so
#: exact prefix - `uv run  --frozen` with two spaces and
#: `uv run --frozen -- python` both slipped past it and were reported as
#: bare interpreters, failing the build for a reason that was not about
#: the code. Neither can be expressed as a lookbehind at all.
_PROJECT_RUNNERS = frozenset({"uv", "poetry", "pipenv", "hatch", "tox"})

#: A token that IS a bare interpreter, by basename: `python`, `python3`,
#: `python3.12`, and any path to one of them.
_INTERPRETER = re.compile(r"^python(?:\d+(?:\.\d+)*)?$")

#: Interpreter options that consume the FOLLOWING token, so what comes
#: after them is an option ARGUMENT and not the script.
#:
#: `-X faulthandler` is why this set exists. "the first token after the
#: interpreter that does not start with `-`" - the obvious rule, and the
#: one suggested to me - picks `faulthandler` as the script and the
#: detector goes quiet again, one flag later.
_OPT_WITH_VALUE = frozenset({"-X", "-W", "--check-hash-based-pycs"})

#: Options after which there is no script path to find at all.
_OPT_NO_SCRIPT = ("-c", "-m")

#: `-m` modules that RUN A SCRIPT GIVEN FURTHER RIGHT, so `-m` does NOT
#: mean "no script path" for them.
#:
#: `python3 -m coverage run <checker>` executes the checker under a BARE
#: interpreter and ships the identical `ModuleNotFoundError` this file
#: exists to prevent - and it read SILENT until R14 measured it. It is
#: the next spelling of the founding defect: not exotic, just one the
#: rule had not been written against, exactly like the `-u` before it.
_MODULE_RUNNERS = frozenset({"coverage", "trace", "cProfile", "profile", "pdb"})

#: The script token must BE a checker, not merely contain the name.
_CHECKER_NAME = re.compile(r"^check-[\w-]+\.py$")

#: `import x` / `from x import ...` at the start of a line - top-level
#: imports only, which is where an unavailable module kills the process.
_IMPORT = re.compile(r"^(?:import|from)\s+([\w.]+)", re.MULTILINE)


def third_party_imports(name: str) -> list[str]:
    """Modules a checker imports that the stdlib does not ship.

    Local-only names are excluded: this asks what a BARE interpreter
    would fail to find, not what is merely unusual.
    """
    path = ROOT / "docs" / "reviews" / name
    if not path.exists() or path.suffix != ".py":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    found = {m.group(1).split(".")[0] for m in _IMPORT.finditer(text)}
    local = {p.stem for p in path.parent.glob("*.py")}
    return sorted(
        mod
        for mod in found
        if mod not in sys.stdlib_module_names
        and mod != "__future__"
        and mod not in local
    )


def _commands(text: str) -> list[list[str]]:
    """Every command in `text`, as a list of argv tokens.

    Segmented on shell operators first, then `shlex.split`. Tokenising
    is what makes the walk below flag-tolerant; a regex cannot be, which
    is the entire lesson of the defect this replaced.
    """
    out: list[list[str]] = []
    for chunk in _SEGMENT.split(text):
        stripped = chunk.strip()
        if not stripped:
            continue
        try:
            tokens = shlex.split(stripped, comments=True)
        except ValueError:
            #: An unbalanced quote inside ONE segment. A whitespace
            #: split keeps the command visible; dropping it would make
            #: the detector silently blind to exactly the body it could
            #: not parse, which is the failure shape this file is about.
            tokens = stripped.split()
        if tokens:
            out.append(tokens)
    return out


def _runner_script(rest: list[str]) -> str | None:
    """The script a `-m` runner module executes, if there is one.

    A runner takes its OWN sub-commands and options before the script,
    and they are not interpreter options: `coverage run <checker>` puts
    a bare `run` in the way. The interpreter walk in `_script_of` stops
    at the first token not starting with `-`, so handing it `rest` after
    the module name returns `run` - a plausible-looking answer that is
    not a script, and the row would pass for the wrong reason.

    R14's suggested fix did exactly that; it was measured before it was
    applied. So scan right instead, past options and sub-commands, for
    the first token that could BE a script. `.py` is the same suffix
    `_CHECKER_NAME` demands, so this narrows nothing a caller could use.
    """
    for token in rest:
        if token.startswith("-"):
            continue
        if pathlib.PurePath(token).suffix == ".py":
            return token
    return None


def _script_of(tokens: list[str]) -> str | None:
    """The script a BARE interpreter in `tokens` runs, if there is one.

    `None` when the command runs no bare interpreter, when a project
    runner supplies the environment, or when `-c`/`-m` means there is no
    script path at all.
    """
    for i, token in enumerate(tokens):
        if not _INTERPRETER.match(pathlib.PurePath(token).name):
            continue
        if any(t in _PROJECT_RUNNERS for t in tokens[:i]):
            return None
        rest = tokens[i + 1 :]
        j = 0
        while j < len(rest):
            opt = rest[j]
            # `--` NEEDS NO BRANCH OF ITS OWN, and it used to have one.
            # The branch could only change the answer for a token
            # starting with `-`, and `_CHECKER_NAME` rejects exactly
            # those - so no input existed for which it moved
            # `bare_python_steps`'s output, and deleting it killed no
            # control. The generic break below reaches the same token.
            if not opt.startswith("-") or opt == "-":
                break
            if opt.startswith(_OPT_NO_SCRIPT):
                after = rest[j + 1 : j + 2]
                if opt == "-m" and after and after[0] in _MODULE_RUNNERS:
                    return _runner_script(rest[j + 2 :])
                return None
            j += 2 if opt in _OPT_WITH_VALUE else 1
        return rest[j] if j < len(rest) else None
    return None


def bare_python_steps(text: str) -> list[tuple[str, list[str]]]:
    r"""Checkers run by a bare interpreter that need more than stdlib.

    **THIS EXISTS BECAUSE I SHIPPED EXACTLY THIS AND TURNED main RED.**
    Every other checker in `docs/reviews/` is stdlib-only, so the family
    convention is `run: python3 ...`. This one imports `yaml`; I tested
    it with `uv run`, wired it as `python3`, and my local `python3`
    happened to have pyyaml while the runner's did not. It died with
    `ModuleNotFoundError` on the commit that wired it.

    A convention that is safe for every existing member is not safe for
    the member that breaks the assumption the convention rests on.

    **AND IT WAS DEFEATED BY ONE FLAG FOR ITS WHOLE FIRST DAY.** The
    original was a regex whose path segment was `\S*?`, which cannot
    cross a space, so `python3 -u <checker>` - an ordinary thing to
    write for a step whose Actions output you want unbuffered -
    shipped the identical defect and this said nothing. Widening the
    regex was the tempting repair and it is the wrong one: `-\w+\s+`
    still misses `-X faulthandler`, and nothing pattern-shaped can
    cover `python3.12`.
    So the invocation is TOKENISED and walked instead. The spellings are
    controls in `--self-test`, one per spelling, including the negative
    arm - a detector that fires on everything is as useless as one that
    fires on nothing, and only the negative arm tells them apart.
    """
    problems: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for tokens in _commands(text):
        script = _script_of(tokens)
        if script is None:
            continue
        name = pathlib.PurePath(script).name
        if not _CHECKER_NAME.match(name) or name in seen:
            continue
        needed = third_party_imports(name)
        if needed:
            seen.add(name)
            problems.append((name, needed))
    return problems


def run_bodies() -> tuple[str, int]:
    """Every `jobs.*.steps[].run` in every workflow, comment-stripped.

    Returns the concatenated text and the number of run steps seen. The
    count exists so a parse that silently yields nothing cannot report
    'nothing is wired' with a straight face.
    """
    bodies: list[str] = []
    steps = 0
    for path in sorted(WORKFLOWS.glob("*.yml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            continue
        for job in (loaded.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    steps += 1
                    bodies.append(strip_comments(step["run"]))
    return "\n".join(bodies), steps


def _control_subjects() -> tuple[str, str]:
    """A checker needing a third-party module, and one that does not.

    **DERIVED from the population, never named.** A name written into
    the control here would invert SILENTLY the day that checker's
    imports changed - the row would keep printing PASS while
    asserting the opposite of what it says. That is the same failure
    the census itself is built to avoid, one level up.
    """
    pys = [n for n in checkers() if n.endswith(".py")]
    needs = [n for n in pys if third_party_imports(n)]
    stdlib = [n for n in pys if not third_party_imports(n)]
    if not needs or not stdlib:
        raise SystemExit(
            "cannot build the spelling controls: the population holds "
            f"{len(needs)} checker(s) needing a third-party module and "
            f"{len(stdlib)} stdlib-only. Both arms need at least one; "
            "without the stdlib arm a detector that fires on EVERY "
            "line would pass every row below."
        )
    return f"docs/reviews/{needs[0]}", f"docs/reviews/{stdlib[0]}"


def _non_checker_subject() -> str:
    """A `docs/reviews/` script needing a third party, not a checker.

    This is the subject of the `_CHECKER_NAME` control, and it has to be
    a file that EXISTS: `third_party_imports` returns `[]` for a path
    that does not resolve, so a fabricated name stays silent whatever
    `_CHECKER_NAME` does and the row would kill nothing. (R14 suggested
    a fabricated `notacheck-...py`; measured, it kills nothing.)

    **The test is `startswith("check-")`, deliberately NOT
    `_CHECKER_NAME`.** A control that selects its own subject THROUGH
    the construct it is testing is vacuous by construction: amputate
    `_CHECKER_NAME` to `.*` and this would find no subject at all
    rather than a failing row.
    """
    for path in sorted((ROOT / "docs" / "reviews").glob("*.py")):
        if path.name.startswith("check-"):
            continue
        if third_party_imports(path.name):
            return f"docs/reviews/{path.name}"
    raise SystemExit(
        "cannot build the `_CHECKER_NAME` control: no non-checker "
        "script under docs/reviews/ imports a third-party module. "
        "Without one, nothing separates 'the script token must BE a "
        "checker' from 'any script token will do'."
    )


def _spelling_controls() -> list[tuple[str, bool]]:
    """One `(step body, must it fire?)` pair per interpreter spelling.

    The positive rows are the ways a bare interpreter can be spelled;
    every one of them ships the `ModuleNotFoundError` this file exists
    to prevent, and the regex this replaced caught only four of them.

    The `uv` rows are the FALSE-POSITIVE direction: a safe invocation
    reported as bare fails the build for a reason that is not about the
    code, which is how the two-space form (`uv run  --frozen`) behaved.

    The last two rows are the NEGATIVE ARM and they are the load-bearing
    ones. Every positive row above would also pass for a detector that
    simply returned True for any line containing a checker name. Only a
    stdlib-only checker, invoked bare, staying SILENT separates a
    detector from a rubber stamp.
    """
    needs, stdlib = _control_subjects()
    notachecker = _non_checker_subject()
    return [
        # Bare interpreters. All must fire.
        (f"python3 {needs}", True),
        (f"python {needs}", True),
        (f"python3 -u {needs}", True),
        (f"python3 -X faulthandler {needs}", True),
        (f"python3 -B {needs}", True),
        (f"python3.12 {needs}", True),
        (f"/usr/bin/python3 {needs}", True),
        (f"env python3 {needs}", True),
        (f"python3 -- {needs}", True),
        (f"python3 {needs} --self-test", True),
        (f"out=$(python3 {needs} 2>&1); rc=$?", True),
        (f"cd docs/reviews && python3 {pathlib.PurePath(needs).name}", True),
        # THE OTHER TWO MEMBERS OF `_OPT_WITH_VALUE`. Only `-X` was
        # covered, so the set could be reduced to `{"-X"}` and every
        # control still passed. A set with an uncovered member is a
        # list nobody is checking the rest of.
        (f"python3 -W error {needs}", True),
        (f"python3 --check-hash-based-pycs always {needs}", True),
        # THE RUNNER IDIOM. `-m` normally means there is no script, but
        # these run one, under a bare interpreter, with the third-party
        # import unavailable. All three read SILENT until R14. This row
        # is also the ONLY thing standing behind `_OPT_NO_SCRIPT`: see
        # the `-m pytest` row below, which does not do that job.
        (f"python3 -m coverage run {needs}", True),
        (f"python3 -m cProfile -o /tmp/prof.out {needs}", True),
        # The project environment. None may fire.
        (f"uv run python {needs}", False),
        (f"uv run --frozen python {needs}", False),
        (f"uv run  --frozen python {needs}", False),
        (f"uv run --frozen python3 {needs}", False),
        (f"uv run --frozen -- python {needs}", False),
        # No interpreter at all, and no script to find.
        (f"{needs}", False),
        # NOT A CONTROL FOR `_OPT_NO_SCRIPT`, THOUGH IT LOOKS LIKE ONE.
        # Empty `_OPT_NO_SCRIPT` and the walk yields `pytest`, which
        # `_CHECKER_NAME` rejects - so this row passes either way, for a
        # reason that has nothing to do with the `-m` guard. It sat in
        # the space where the real control belonged, which is worse
        # than an empty space. `-m coverage run` above is the control.
        ("python3 -m pytest", False),
        # THE NEGATIVE ARM. A stdlib-only checker must stay silent.
        (f"python3 {stdlib}", False),
        (f"python3 -u {stdlib}", False),
        (f"/usr/bin/python3 -X faulthandler {stdlib}", False),
        # A REAL SCRIPT THAT IS NOT A CHECKER. Without this the name
        # test could be `.*` and nothing would notice: every other
        # negative row is a file that is either stdlib-only or does not
        # exist, so none of them can see the difference.
        (f"python3 -u {notachecker}", False),
    ]


def self_test() -> int:
    """Controls, each aimed at a way this checker could lie."""
    text, steps = run_bodies()
    failures: list[str] = []

    # 1. A name I have read a step for must read WIRED. Without this the
    #    parser could return nothing and every answer would be
    #    'unwired'.
    if "check-design-citations.py" not in text:
        failures.append("check-design-citations.py is wired but reads UNWIRED")

    # 2. A name that exists nowhere must read UNWIRED. A checker that
    #    finds everything is as useless as one that finds nothing.
    if "check-a-name-nobody-has-written.py" in text:
        failures.append("a fabricated name reads WIRED")

    # 3. The comment strip must actually strip. This is THE defect that
    #    produced two wrong censuses, so it gets a control of its own.
    if "zzz" in strip_comments("echo hi  # zzz\n"):
        failures.append("strip_comments left a commented name behind")

    # 4. THIS FILE MUST BE IN ITS OWN POPULATION, asserted rather than
    #    commented. The comment in `checkers()` claimed it already was,
    #    and the claim was INERT when I wrote it: `git ls-files` lists
    #    only TRACKED files, and the checker was still untracked, so it
    #    excluded itself for a reason the code never mentions. The
    #    census
    #    read 26 and silently became 27 on the commit that tracked it.
    #    A rename that stops matching the glob would do the same thing.
    me = pathlib.Path(__file__).name
    if me not in checkers():
        failures.append(f"{me} is NOT in its own population")

    # 5. ONE CONTROL PER INTERPRETER SPELLING, WITH A NEGATIVE ARM.
    #    The detector this replaced was a regex, and it was defeated by
    #    a single `-u` for its whole first day - in the function whose
    #    docstring says it exists because that exact defect turned main
    #    red. There is no spelling below that a reader can look at and
    #    call unreasonable, and that is the point: the failure was never
    #    an exotic invocation, it was an ordinary one the pattern had
    #    not been written against.
    spellings = _spelling_controls()
    for body, must_fire in spellings:
        fired = bool(bare_python_steps(body))
        if fired != must_fire:
            wanted = "fire" if must_fire else "stay silent"
            failures.append(f"spelling `{body}` should {wanted}, got fired={fired}")

    total = 4 + len(spellings)
    # NAME THE CONTAINER BESIDE THE COUNT (R14 review, L-1). This
    # walks EVERY workflow; probe-ci-checker-steps.py pins ci.yml
    # alone. Both were right and neither said so, so 80 vs 78 read
    # as a contradiction and cost a reviewer a detour to settle.
    parsed_from = ", ".join(sorted(w.name for w in WORKFLOWS.glob("*.yml")))
    print(f"run steps parsed: {steps}  (across {parsed_from})")
    for line in failures:
        print(f"  CONTROL FAILED: {line}")
    if failures:
        print(f"\n{len(failures)} of {total} control(s) failed. The instrument")
        print("is wrong.")
        return 1
    print(f"{total}/{total} controls passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="are the checkers wired?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    _reasons_are_non_empty()
    if args.self_test:
        return self_test()

    names = checkers()
    if not names:
        print("MATCHED ZERO checkers. An empty population reports full")
        print("coverage, which would mean nothing here. Exit 2.")
        return 2

    text, steps = run_bodies()
    if steps == 0:
        print("PARSED ZERO run steps out of the workflows. Every checker")
        print("would read as unwired for a reason that is not about the")
        print("checkers. This is a BROKEN INSTRUMENT. Exit 3.")
        return 3

    wired = [n for n in names if n in text]
    unwired = [n for n in names if n not in text]

    excused = [n for n in unwired if UNWIRED_BY_DECISION.get(n, "").strip()]
    unexplained = [n for n in unwired if n not in excused]
    stale = [n for n in UNWIRED_BY_DECISION if n in wired]
    unknown = [n for n in UNWIRED_BY_DECISION if n not in names]

    print(f"Checkers in docs/reviews/: {len(names)}")
    print(f"Run steps parsed from {WORKFLOWS.name}/: {steps}")
    print(f"WIRED: {len(wired)}")
    print(f"UNWIRED, with a stated reason: {len(excused)}")
    for name in excused:
        print(f"  EXEMPT   {name}: {UNWIRED_BY_DECISION[name]}")

    problems = False
    if unexplained:
        problems = True
        print(f"\n{len(unexplained)} checker(s) are UNWIRED and unexplained:")
        for name in unexplained:
            print(f"  {name}")
        print(
            "\nAn unwired checker is a claim of coverage nobody can see is\n"
            "false. Either wire it - after measuring it GREEN, because a\n"
            "gate that lands red is one people learn to ignore - or add it\n"
            "to UNWIRED_BY_DECISION with the reason."
        )

    if stale:
        problems = True
        print(f"\n{len(stale)} exemption(s) name a checker that IS wired:")
        for name in stale:
            print(f"  {name}")
        print("The reason has outlived the condition. Delete the entry.")

    bare = bare_python_steps(text)
    if bare:
        problems = True
        print(f"\n{len(bare)} checker(s) run by a BARE interpreter but need")
        print("more than the standard library:")
        for name, needed in bare:
            print(f"  {name}  needs {', '.join(needed)}")
        print(
            "\nA bare `python3` reaches only the standard library. The step\n"
            "passes wherever the module happens to be installed and dies\n"
            "with ModuleNotFoundError on a clean runner. Use\n"
            "`uv run --frozen python ...`, and declare the module in\n"
            "pyproject's dev group - a transitive dependency is a fact\n"
            "nobody promised you."
        )

    if unknown:
        problems = True
        print(f"\n{len(unknown)} exemption(s) name a file that does not exist:")
        for name in unknown:
            print(f"  {name}")
        print("A renamed or deleted checker leaves its exemption behind.")

    if problems:
        return 1

    print("\nEvery checker is wired, or unwired for a recorded reason.")
    print("NOTE: this proves each is INVOKED, not that its exit code gates")
    print("the job. A step that runs a checker and swallows its status")
    print("reads as WIRED here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
