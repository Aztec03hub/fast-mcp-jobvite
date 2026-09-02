#!/usr/bin/env python3
"""Does a CI checker's VERDICT depend on which interpreter invokes it?

    python3 docs/reviews/measure-221-interpreter.py
    python3 docs/reviews/measure-221-interpreter.py --self-test

**WHY THIS EXISTS (#221).** `ci.yml` invokes checkers two different
ways and nothing distinguishes them: most sites say
`python3 <script>`, twelve say `uv run --frozen python <script>`.
`python3` is an interpreter
INHERITED from whatever `PATH` offers, not one CHOSEN - the class fixed
at 3082a18/4917a94 for #46, recurring.

`suborch-212` measured one site, `check-plan-measurements.py`, giving
two different verdicts in one tree at one commit:

    /usr/bin/python3          -> [STALE] M3, [STALE] M4, rc=1
    uv run --frozen python    -> [PASS] M1-M4, rc=0

That is a real observation and it is NOT evidence that the invoking
interpreter decides the verdict. This file exists because the two
hypotheses are indistinguishable from one site's exit code, and only
one of them is a defect:

  H1  the invoking interpreter decides - bare `python3` lacks the
      project's dependencies, so checkers that import them misbehave.
  H2  something else that co-varies with the arm decides. `uv run`
      SYNCS `.venv` as a side effect. A checker that locates
      `.venv/bin/python` for itself gets a different answer depending
      on whether that directory EXISTS, and `uv run` is what creates
      it - so the arm looks causal while the venv is doing the work.

**A BLANKET REWRITE IS FORBIDDEN AND THIS IS WHY.** Under H2 the fix
`uv run --frozen python` everywhere is a no-op wearing a fix's clothes:
it changes 25 lines, closes nothing, and retires the observation that
would have found the real cause. Under H2 the actual remedy is in the
checker, not in `ci.yml`.

So: measure first, both arms, every site, and report the three outcomes
the brief asks for - SAME, DIFFERENT, FAILS-TO-RUN.

## The population is DERIVED, never retyped

The 25 line numbers in the task description were correct when written.
This file re-derives them from `ci.yml` on every run, because a retyped
constant decays and a census that goes stale silently is how a site
gets left out. If the derived set disagrees with the recorded one, that
disagreement is printed - it is a finding either way.

## Determinism is a property this file has to EARN

Another probe on this project shipped a 99-line difference between two
runs of an unchanged tree and nobody caught it by reading, because the
cause was per-process hash randomisation - invisible in source. Two
runs here must be byte-identical or the measurement is of the
environment, not the repo. Three things buy that:

- `PYTHONHASHSEED=0` in both arms, so set/dict iteration is fixed.
- `PYTHONDONTWRITEBYTECODE=1`, so no run leaves `__pycache__` behind
  for the next one to find.
- Output normalisation: the absolute repo path and any wall-clock
  duration are replaced with placeholders before comparison, since
  both change between runs without the repo changing.

**Verify it rather than believing this docstring**: run the file twice
into two files and `diff` them. `--self-test` asserts the normaliser
does what the paragraph above claims.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"

#: Timeout for a single arm. `check-plan-measurements.py` re-runs pytest
#: probes and took 8s on the runner; the mutation-adjacent ones are
#: slower. Generous, because a timeout is an unresolved row, not a
#: verdict.
ARM_TIMEOUT_S = 900

#: Tokens that end the invocation. Everything after one of these belongs
#: to the shell, not to the checker's argv.
_STOP = {"2>&1", "||", "&&", ";", "|", ">", ">>", "2>", "&"}

_BARE_RE = re.compile(r"(?<![\w./-])python3\s+((?:docs/reviews|scripts)/[^\s;)]+\.py)")
_UV_RE = re.compile(r"uv run --frozen python\s+((?:docs/reviews|scripts)/[^\s;)]+\.py)")

#: The census as task #221 recorded it, AS AT `2099a72`. Kept ONLY so a
#: disagreement with the derived set is visible; nothing reads it to
#: decide what to run.
#:
#: **LINE NUMBERS DRIFT AND THAT IS NOT A FINDING.** Three of these had
#: already moved by `4f03004` (1566 -> 1575, 1735 -> 1744, 1867 -> 1876)
#: because commits landed above them in `ci.yml`. What must NOT change
#: silently is the COUNT and the SET OF SCRIPTS: a 26th site, or a
#: script leaving the population, is a real census change. So the
#: comparison below is on count and scripts, and line drift is reported
#: as a note.
RECORDED_BARE_LINES = [
    239,
    252,
    265,
    353,
    381,
    394,
    433,
    488,
    516,
    543,
    588,
    614,
    665,
    697,
    715,
    1152,
    1180,
    1183,
    1200,
    1211,
    1224,
    1232,
    1566,
    1735,
    1867,
]


def _args_after(rest: str) -> list[str]:
    """Split the tail of a `run:` line into the checker's argv.

    Stops at the first shell token, so `--controls || exit 1` yields
    `['--controls']` and not a fabricated `exit` argument.
    """
    out: list[str] = []
    for tok in rest.split():
        cleaned = tok.rstrip(");")
        if tok in _STOP or cleaned in _STOP or tok.startswith(")"):
            break
        if not cleaned:
            break
        out.append(cleaned)
    return out


def enumerate_sites() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (bare-python3 sites, uv sites), each with line numbers.

    Lines whose `python3` sits after a `#` are comments and are not
    invocations. A census that counts a name in a comment is the exact
    instrument `check-checkers-are-wired.py` was rewritten to stop
    using.
    """
    bare: list[dict[str, Any]] = []
    uv: list[dict[str, Any]] = []
    for lineno, raw in enumerate(CI_YML.read_text().splitlines(), start=1):
        for regex, sink in ((_BARE_RE, bare), (_UV_RE, uv)):
            m = regex.search(raw)
            if not m:
                continue
            hash_pos = raw.find("#")
            if hash_pos != -1 and hash_pos < m.start():
                continue
            sink.append(
                {
                    "line": lineno,
                    "script": m.group(1),
                    "argv": _args_after(raw[m.end() :]),
                }
            )
    return bare, uv


def normalise(text: str, repo: Path) -> str:
    """Strip everything that changes between runs of an unchanged tree.

    Two substitutions, both load-bearing:

    - the absolute repo path, because a checker that prints the
      interpreter it selected prints `<repo>/.venv/bin/python` and the
      repo path differs per worktree;
    - wall-clock durations, because a probe that reports how long it
      took reports a different number every run.
    """
    out = text.replace(str(repo), "<REPO>")
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    out = re.sub(r"\b\d+\.\d+\s?(?:s|ms|sec|seconds)\b", "<DURATION>", out)
    out = re.sub(r"\bin \d+(?:\.\d+)?s\b", "in <DURATION>", out)
    return out.strip()


def run_arm(prefix: list[str], site: dict[str, Any], repo: Path) -> dict[str, Any]:
    """Run one site under one interpreter and report rc plus output."""
    cmd = [*prefix, site["script"], *site["argv"]]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=ARM_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {"rc": None, "out": f"<TIMEOUT after {ARM_TIMEOUT_S}s>"}
    return {"rc": proc.returncode, "out": normalise(proc.stdout + proc.stderr, repo)}


def _fails_to_run(arm: dict[str, Any]) -> bool:
    """Did the interpreter refuse to execute the file at all?

    An import error is categorically different from a verdict: the
    checker never got to judge anything. `rc` alone cannot tell them
    apart, because a checker's own refusal is also nonzero.
    """
    if arm["rc"] is None:
        return True
    markers = (
        "ModuleNotFoundError",
        "ImportError",
        "SyntaxError",
        "can't open file",
        "No such file or directory",
    )
    return any(m in arm["out"] for m in markers)


def classify(bare: dict[str, Any], uv: dict[str, Any]) -> str:
    if _fails_to_run(bare) or _fails_to_run(uv):
        return "FAILS-TO-RUN"
    if bare["rc"] != uv["rc"]:
        return "DIFFERENT"
    if bare["out"] != uv["out"]:
        return "DIFFERENT-OUTPUT"
    return "SAME"


def first_line(arm: dict[str, Any]) -> str:
    body = arm["out"].splitlines()
    return body[0][:110] if body else "<no output>"


def measure(repo: Path) -> int:
    bare_sites, uv_sites = enumerate_sites()

    derived = sorted(s["line"] for s in bare_sites)
    print(f"CI file:            {CI_YML.relative_to(repo)}")
    print(f"venv present:       {(repo / '.venv' / 'bin' / 'python').exists()}")
    print(f"bare python3 sites: {len(derived)}")
    print(f"uv sites (control): {len(uv_sites)} at {[s['line'] for s in uv_sites]}")
    if len(derived) != len(RECORDED_BARE_LINES):
        print(
            f"CENSUS SIZE CHANGED: {len(RECORDED_BARE_LINES)} recorded at "
            f"2099a72, {len(derived)} here. Re-read the population before "
            f"trusting any row below."
        )
    else:
        print(f"census size agrees with the record ({len(derived)} sites)")
    moved = sorted(set(derived) - set(RECORDED_BARE_LINES))
    if moved:
        gone = sorted(set(RECORDED_BARE_LINES) - set(derived))
        print(f"  line drift since 2099a72 (not a finding): {gone} -> {moved}")
    print(f"  scripts: {len({s['script'] for s in bare_sites})} distinct")
    print()

    tally: dict[str, int] = {}
    rows: list[tuple[dict[str, Any], str, dict[str, Any], dict[str, Any]]] = []
    for site in bare_sites:
        a = run_arm(["python3"], site, repo)
        b = run_arm(["uv", "run", "--frozen", "python"], site, repo)
        verdict = classify(a, b)
        tally[verdict] = tally.get(verdict, 0) + 1
        rows.append((site, verdict, a, b))

    for site, verdict, a, b in rows:
        label = " ".join([site["script"], *site["argv"]])
        print(f"ci.yml:{site['line']:<5} {verdict:<16} {label}")
        print(f"    python3            rc={a['rc']}  {first_line(a)}")
        print(f"    uv run --frozen    rc={b['rc']}  {first_line(b)}")

    print()
    for name in ("SAME", "DIFFERENT", "DIFFERENT-OUTPUT", "FAILS-TO-RUN"):
        print(f"  {name:<17} {tally.get(name, 0)}")

    differing = [r for r in rows if r[1] != "SAME"]
    print()
    if differing:
        print(f"{len(differing)} site(s) are interpreter-sensitive in THIS tree:")
        for site, verdict, _a, _b in differing:
            print(f"  ci.yml:{site['line']} {site['script']} -> {verdict}")
    else:
        print("No site changed its verdict between the two arms in this tree.")
    return 0


def self_test() -> int:
    """Assert the normaliser and argv splitter do what is claimed."""
    failures: list[str] = []

    repo = Path(tempfile.gettempdir()) / "some" / "repo"
    want = "ran <REPO>/.venv/bin/python"
    if normalise(f"ran {repo}/.venv/bin/python", repo) != want:
        failures.append("normalise: repo path not replaced")
    if normalise("took 1.25s", repo) != "took <DURATION>":
        failures.append("normalise: duration not replaced")
    if normalise("plain\n", repo) != "plain":
        failures.append("normalise: not stripped")

    if _args_after(" --controls || exit 1") != ["--controls"]:
        failures.append("argv: shell tail leaked into argv")
    if _args_after(" 2>&1); rc=$?") != []:
        failures.append("argv: redirection leaked into argv")
    if _args_after(" --self-check --floor 464") != ["--self-check", "--floor", "464"]:
        failures.append("argv: flags dropped")
    if _args_after(" docs/DESIGN.md") != ["docs/DESIGN.md"]:
        failures.append("argv: positional dropped")

    #: A comment line must never be counted as an invocation. This is
    #: the mistake two earlier censuses on this project made.
    if _BARE_RE.search("# python3 docs/reviews/check-x.py") is None:
        failures.append(
            "regex: expected to MATCH inside a comment (filter is positional)"
        )

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    print("self-test: 8 assertions, all pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    ns = parser.parse_args()
    if ns.self_test:
        return self_test()
    return measure(REPO_ROOT)


if __name__ == "__main__":
    sys.exit(main())
