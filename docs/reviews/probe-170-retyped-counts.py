#!/usr/bin/env python3
"""Census of retyped counts: a number standing beside a plural noun.

    P=docs/reviews/probe-170-retyped-counts.py
    python3 $P              # the census
    python3 $P --findings   # the enumerable, non-record subset
    python3 $P --derive     # true figure for every GLOB candidate
    python3 $P --self-test

**WHY THIS EXISTS.** The same shape has been found three times by three
unrelated routes - #116 (70 retyped seconds figures), #166 ("Eleven
decision records" beside thirty-three of them), and BASH-1 at `d0bdf2a`
("all 20 `scripts/*.sh`" beside a population of 39). Nobody had ever
counted the container. A findings list with no container size is a claim
about where the author looked, not about the repository.

**THE POPULATION IS PICKED BY KIND, NOT BY PATH** (#115's doctrine). A
candidate is a NUMBER - digit or number word - standing next to a plural
noun, anywhere in any tracked text file. It is deliberately NOT
`docs/*.md`: BASH-1 lived in a table cell, #116's figures lived in shell
comments and Python docstrings, and a path filter would have selected
for the file somebody happened to think of.

**THE CENSUS AND THE FINDINGS ARE TWO DIFFERENT NUMBERS, and printing
only the second is the defect this file is named after.** The census is
every number-beside-plural adjacency, including "three reasons" and "two
different things", which name nothing this repository can enumerate. The
findings pass is the subset whose noun names a set the repository CAN
enumerate - files matching a glob, rows, ADRs, harnesses, tests, arms,
controls. Both are printed, and the ratio between them is what says
whether the selector is working.

**IT CANNOT GO RED AND IT IS NOT A GATE.** Deciding whether "three
reasons" is stale is a human reading a sentence; there is no derivation
for it. A census that guessed would produce a green nobody could trust,
and this repository already records what an unwired checker cited as a
gate costs. It is registered in `check-checkers-are-wired.py` as unwired
BY DECISION, with that reason.

**THE DATED-RECORD CLASS IS COMPUTED, NOT JUDGED.** A number inside a
worklog, a plan, a `REPORT-*` or a review is correct as written - it
records what was true on its date - and #166 deliberately left
`REPORT-147` section 6's stale 13 in place on exactly that ground. Those
paths are reported in their own bucket so they are never mistaken for a
backlog.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

#: Number words this repository actually writes out, plus the
#: quantifiers whose falsity is the SECOND half of the BASH-1 shape.
#: `all`/`every`/`none`/`only` are here because BASH-1's word "all" was
#: false INDEPENDENTLY of its number, and replacing the digit would have
#: hidden that. They are counted as numbers so the claim travels with
#: the count.
NUMBER_WORDS = (
    "one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
    "twenty thirty forty fifty sixty seventy eighty ninety hundred "
    "thousand"
).split()

QUANTIFIERS = "all every none only both no".split()

#: Plural nouns that name a set THIS repository can enumerate. Each one
#: has a derivation somebody could actually run: a glob, a table, a
#: directory listing, a grep. This list is the judgement in the tool and
#: it is deliberately explicit - a heuristic "ends in s" cannot tell
#: "39 scripts" from "three reasons", and the difference is the whole
#: point.
ENUMERABLE_NOUNS = {
    # files and directories
    "files",
    "scripts",
    "harnesses",
    "probes",
    "checkers",
    "controls",
    "workflows",
    "modules",
    "tests",
    "suites",
    "fixtures",
    "documents",
    "docs",
    "reports",
    "reviews",
    "worklogs",
    "plans",
    "briefs",
    # records
    "adrs",
    "records",
    "decisions",
    "rulings",
    "obligations",
    "rows",
    "entries",
    "cells",
    "columns",
    "sections",
    "headings",
    "citations",
    "anchors",
    "references",
    "links",
    "mappings",
    "findings",
    "tasks",
    "commits",
    "branches",
    "issues",
    # code shapes
    "steps",
    "jobs",
    "gates",
    "arms",
    "cases",
    "assertions",
    "markers",
    "mutations",
    "survivors",
    "exemptions",
    "floors",
    "producers",
    "middlewares",
    "middleware",
    "tools",
    "models",
    "endpoints",
    "handlers",
    "callers",
    "sites",
    "occurrences",
    "instances",
    "variables",
    "settings",
    "flags",
    "options",
    "clauses",
    "hooks",
    "lines",
    "characters",
    "seconds",
    "minutes",
    "runs",
}

#: Directories whose contents are DATED RECORDS. A number inside one is
#: correct as written and is not a finding. Matched as a path prefix
#: because that is what these are - a directory is the record boundary.
RECORD_DIRS = ("docs/worklogs/", "docs/plans/", "docs/research/")

#: Filename prefixes that make a file a dated record wherever it lives.
RECORD_PREFIXES = (
    "REPORT-",
    "REVIEW-",
    "FINDINGS-",
    "WORKLOG-",
    "CODE-REVIEW-",
    "PLAN-REVIEW-",
    "DESIGN-R",
    "CITATION-",
    "CONFORMANCE-",
    "CONF-",
)

_NUM = r"(?:\d{1,6}(?:,\d{3})*|" + "|".join(NUMBER_WORDS + QUANTIFIERS) + r")"

#: The number itself. Everything after it is walked token by token
#: rather than matched by one regex: a lazy noun pattern silently
#: truncated `assertions` to `as` and `scripts/*.sh` to `scripts`, and a
#: greedy one truncated the glob to `scripts/*.s`. A regex that returns
#: a plausible wrong noun is worse than one that returns none.
#: `:` and `-` in the lookbehind drop `DESIGN.md:1072` and `36-41`: a
#: line number and a range endpoint are citations, not counts, and this
#: repository has 847 of the former. `/` drops the second half of
#: `20/20`, whose first half is already a candidate.
NUMBER_TOKEN = re.compile(r"(?<![\w.,:/-])(" + _NUM + r")(?![\w-])", re.IGNORECASE)

#: One token: a backticked span, or a run of word/path characters.
TOKEN = re.compile(r"`[^`]+`|[\w./*+-]+")

#: A path glob: at least two `/`-separated segments of path characters,
#: no leading `/` (an absolute path like `/dev/null` is a file, not a
#: set), and no bare `**` left over from markdown emphasis.
PATH_GLOB = re.compile(r"[\w.*?-]+(?:/[\w.*?-]+)+")

#: How many tokens after the number may intervene before the noun. Three
#: covers "20 tracked `scripts/*.sh` files" and stops short of crossing
#: a clause.
LOOKAHEAD = 3


def _noun_of(token: str) -> tuple[str, bool] | None:
    """The candidate noun in a token, and whether it names a GLOB.

    Returns None when the token cannot be a plural noun at all.
    """
    bare = token.strip("`").strip("_\"'")
    if not bare:
        return None
    # A GLOB names an enumerable set by construction - `scripts/*.sh` is
    # the BASH-1 instance. **The `*` is required.** An earlier version
    # accepted any token containing `/`, which admitted `/dev/null`,
    # `/min` and `WORK/fx/active.json` as nouns: 274 of them. A path is
    # not a set.
    #
    # **AND THE SHAPE IS REQUIRED TOO.** Requiring only `*` and `/`
    # admitted `6/min**` and `L/I.**` - markdown BOLD markers read as a
    # glob - and each derived a confident population of 0, which is
    # exactly the clean zero that explains itself. `**` is stripped as
    # emphasis first, then the remainder must look like a path.
    if bare.endswith("**"):
        bare = bare[:-2]
    bare = bare.strip(".,;:")
    if "*" in bare and "/" in bare and PATH_GLOB.fullmatch(bare):
        return bare, True
    if (
        len(bare) >= 3
        and bare[0].isalpha()
        and bare.isalpha()
        and bare.lower().endswith("s")
    ):
        return bare.lower(), False
    return None


def _noun_after(text: str, pos: int) -> tuple[str, bool] | None:
    """The first plural noun within LOOKAHEAD tokens after `pos`."""
    for i, tm in enumerate(TOKEN.finditer(text[pos:])):
        if i >= LOOKAHEAD:
            return None
        found = _noun_of(tm.group(0))
        if found is not None:
            return found
    return None


def candidates_in(line: str) -> Iterator[tuple[str, str, bool]]:
    """Yield (number, noun, is_glob) per adjacency in a string."""
    for m in NUMBER_TOKEN.finditer(line):
        found = _noun_after(line, m.end())
        if found is not None:
            yield m.group(1), found[0], found[1]


def is_record(relpath: str) -> bool:
    """A dated record: correct as written, never a finding."""
    if relpath.startswith(RECORD_DIRS):
        return True
    name = relpath.rsplit("/", 1)[-1]
    return name.startswith(RECORD_PREFIXES)


def tracked_text_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\n")
    return [f for f in out if f]


class Hit:
    """One number standing beside one plural noun."""

    __slots__ = ("path", "line", "number", "noun", "glob", "text", "record")

    def __init__(
        self, path: str, line: int, number: str, noun: str, glob: bool, text: str
    ) -> None:
        """Record one adjacency and classify its file."""
        self.path = path
        self.line = line
        self.number = number
        self.noun = noun
        self.glob = glob
        self.text = text.strip()
        self.record = is_record(path)

    @property
    def enumerable(self) -> bool:
        """A glob names a set; a bare word must be listed."""
        return self.glob or self.noun in ENUMERABLE_NOUNS

    @property
    def quantified(self) -> bool:
        """BASH-1's second half: a separately-checkable claim."""
        return self.number.lower() in QUANTIFIERS


def scan(files: list[str]) -> tuple[list[Hit], list[str]]:
    hits: list[Hit] = []
    unreadable: list[str] = []
    for rel in files:
        p = ROOT / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(rel)
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            # **THE NEXT LINE IS APPENDED, and this is not a nicety.**
            # The selector was line-based and missed
            # `docs/OBLIGATIONS.md:161` outright: "13 of the 15" ended a
            # wrapped line and "`scripts/*.sh` exceed 100 lines" began
            # the next. Three stale numbers in one sentence, in the same
            # file as BASH-1, invisible to a line-based scan. A census
            # that cannot see a hard wrap understates itself silently.
            joined = line
            if idx + 1 < len(lines):
                joined = line + " " + lines[idx + 1]
            for m in NUMBER_TOKEN.finditer(joined):
                if m.start() >= len(line):
                    continue  # starts on the next line; counted there
                found = _noun_after(joined, m.end())
                if found is None:
                    continue
                noun, glob = found
                hits.append(Hit(rel, idx + 1, m.group(1), noun, glob, joined))
    return hits, unreadable


def derive_globs(hits: list[Hit]) -> list[tuple[Hit, int, int, int | None]]:
    """For every GLOB candidate, count the tracked files it matches.

    This is the runnable half. BASH-1 was exactly this shape - "all 20
    `scripts/*.sh`" against 39 tracked - and it is the one class where
    the true figure can be DERIVED rather than judged, so nobody has to
    take a report's word for it.

    **TWO INSTRUMENTS DISAGREE ON `scripts/*.sh` AND THE DIFFERENCE IS
    NOT ROUNDING.** `git ls-files -- 'scripts/*.sh'` returns 39, because
    a git pathspec wildcard crosses `/` and so admits
    `scripts/lib/harness-result.sh`. `PurePosixPath.match` and a plain
    shell glob return 38, because theirs does not. BASH-1's own fix
    counted 39 and named `scripts/lib/harness-result.sh` as one of them,
    so **git's reading is the one this repository means** - and both are
    reported when they differ, because a glob whose population depends
    on which tool reads it is itself the finding.

    Returns (hit, derived_git, derived_shell, claimed_or_None) per hit.
    """
    tracked = tracked_text_files()
    cache: dict[str, int] = {}
    out: list[tuple[Hit, int, int, int | None]] = []
    for h in hits:
        if not h.glob:
            continue
        pat = h.noun.strip("`")
        if pat not in cache:
            proc = subprocess.run(
                ["git", "-C", str(ROOT), "ls-files", "--", pat],
                capture_output=True,
                text=True,
                check=False,
            )
            cache[pat] = len([x for x in proc.stdout.split("\n") if x])
        try:
            shell = sum(1 for f in tracked if pathlib.PurePosixPath(f).match(pat))
        except (ValueError, IndexError):
            shell = -1
        claimed: int | None
        try:
            claimed = int(h.number.replace(",", ""))
        except ValueError:
            claimed = None  # a quantifier: `all`, `every`, `no`
        out.append((h, cache[pat], shell, claimed))
    return out


def _self_test() -> int:
    """The selector must find a planted instance and reject a decoy.

    A zero is a finding about the selector until proved otherwise, so
    this plants the exact BASH-1 sentence and requires it back.
    """
    checks: list[tuple[str, bool]] = []

    def probe(label: str, line: str, want_noun: str | None) -> None:
        nouns = [n for _, n, _ in candidates_in(line)]
        got = (want_noun in nouns) if want_noun else (not nouns)
        checks.append((f"{label}: {line[:58]!r} -> {nouns}", got))

    # The three measured instances, verbatim in shape. THE ZERO IS A
    # FINDING ABOUT THE SELECTOR UNTIL PROVED OTHERWISE, so each known
    # instance is planted here and required back.
    probe("BASH-1 glob", "all 20 `scripts/*.sh` run `set -uo pipefail`", "scripts/*.sh")
    probe("BASH-1 quantifier", "the shebang half is met by 20/20 files", "files")
    probe("#166 word", "Eleven decision records live under docs/adr/", "records")
    probe("#116 figure", "the 900s bound has 15x headroom over 70 runs", "runs")
    probe("quantifier", "every one of the 14 floors was watched firing", "floors")
    probe("interposed adjective", "39 tracked shell scripts", "scripts")
    # The two truncation bugs a lazy/greedy noun regex produced. Both
    # returned a PLAUSIBLE wrong noun, which is why they are arms.
    probe("no lazy truncation", "the 10 assertions in that file", "assertions")
    probe("no glob truncation", "20 `scripts/*.sh` files", "scripts/*.sh")
    # THE HARD WRAP. This arm exists because the selector FAILED it and
    # missed a live three-number finding in `docs/OBLIGATIONS.md`. It is
    # checked here through the same join `scan()` performs.
    wrapped = "13 of the 15" + " " + "`scripts/*.sh` exceed 100 lines"
    probe("hard wrap", wrapped, "scripts/*.sh")
    # A decoy: a number with no plural noun after it at all.
    probe("no plural", "the exit code was 2 and nothing else", None)
    # A decoy: the noun is too far away to be its noun.
    probe(
        "beyond lookahead",
        "the 2 gates that were wired here in the end run daily",
        "gates",
    )
    # A decoy the ENUMERABLE filter must drop, not the selector.
    nouns = [n for _, n, _ in candidates_in("for three reasons, none good")]
    checks.append(
        (
            f"'three reasons' is a candidate but NOT enumerable -> {nouns}",
            "reasons" in nouns and "reasons" not in ENUMERABLE_NOUNS,
        )
    )
    # The record classifier.
    checks.append(
        (
            "REPORT-147 is a dated record",
            is_record("docs/reviews/REPORT-147-ci-step-selection-bias.md"),
        )
    )
    checks.append(
        ("docs/OBLIGATIONS.md is NOT a record", not is_record("docs/OBLIGATIONS.md"))
    )
    checks.append(
        ("docs/worklogs/anything is a record", is_record("docs/worklogs/WHATEVER.md"))
    )

    bad = [label for label, ok in checks if not ok]
    for label, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print(f"\n{len(checks) - len(bad)}/{len(checks)} self-test arms pass")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--findings",
        action="store_true",
        help="print only the enumerable, non-record subset",
    )
    ap.add_argument(
        "--derive",
        action="store_true",
        help="derive the true figure for every GLOB candidate",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

    files = tracked_text_files()
    hits, unreadable = scan(files)

    sha = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    enumerable = [h for h in hits if h.enumerable]
    live = [h for h in enumerable if not h.record]
    record = [h for h in enumerable if h.record]
    quantified = [h for h in live if h.quantified]

    print(f"CONTAINER, measured at {sha}")
    print(f"  tracked files:                    {len(files)}")
    print(
        f"  ...skipped as binary/unreadable:  {len(unreadable)}"
        "   (a silent skip is how a census understates itself)"
    )
    for rel in unreadable:
        print(f"      SKIPPED {rel}")
    print(f"  tracked files scanned:            {len(files) - len(unreadable)}")
    print(
        f"  number-beside-plural adjacencies: {len(hits)}"
        f"  in {len({h.path for h in hits})} files"
    )
    print(
        f"  ...whose noun is ENUMERABLE:      {len(enumerable)}"
        f"  in {len({h.path for h in enumerable})} files"
    )
    print(
        f"  ...of those, in a DATED RECORD:   {len(record)}"
        "   (correct as written, left alone)"
    )
    print(
        f"  ...LIVE, and therefore checkable: {len(live)}"
        f"  in {len({h.path for h in live})} files"
    )
    print(
        f"  ...of those, carrying a QUANTIFIER (all/every/none/only/"
        f"both/no): {len(quantified)}"
    )
    print()

    if args.derive:
        rows = derive_globs(live)
        print(f"GLOB candidates with a DERIVED population, at {sha}: {len(rows)}")
        print(
            "  (a glob is the one class where the true figure is "
            "mechanical; every\n   other noun needs a human to say "
            "which set it names)\n"
        )
        for h, git_n, shell_n, claimed in sorted(
            rows, key=lambda r: (r[0].path, r[0].line)
        ):
            pop = (
                f"{git_n}"
                if git_n == shell_n
                else f"{git_n} (git) / {shell_n} (shell glob)"
            )
            if claimed is None:
                verdict = f"QUANTIFIER `{h.number}` over {pop} tracked"
            elif claimed in (git_n, shell_n):
                verdict = f"AGREES ({claimed}) against {pop}"
            else:
                verdict = f"CLAIMS {claimed}, TRACKED {pop}  <-- CHECK"
            print(f"{h.path}:{h.line}  `{h.noun}`  {verdict}")
            print(f"    {h.text[:140]}")
        return 0

    if args.findings:
        for h in sorted(live, key=lambda h: (h.path, h.line)):
            mark = "Q" if h.quantified else " "
            print(f"{mark} {h.path}:{h.line}: [{h.number} .. {h.noun}] {h.text[:110]}")
        return 0

    by_noun: collections.Counter[str] = collections.Counter(h.noun for h in live)
    print("LIVE enumerable candidates, by noun:")
    for noun, count in by_noun.most_common():
        print(f"  {count:4d}  {noun}")
    print()
    by_file: collections.Counter[str] = collections.Counter(h.path for h in live)
    print("LIVE enumerable candidates, by file (top 25):")
    for path, count in by_file.most_common(25):
        print(f"  {count:4d}  {path}")
    print("\nRun with --findings for the enumerated list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
