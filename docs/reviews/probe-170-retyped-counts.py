#!/usr/bin/env python3
"""Census of retyped counts: a number standing beside a plural noun.

    P=docs/reviews/probe-170-retyped-counts.py
    python3 $P              # the census
    python3 $P --findings   # the enumerable, non-record subset
    python3 $P --derive     # true figure for every GLOB candidate
    python3 $P --tallies    # prose counts vs the file's own ROW_FLOOR
    python3 $P --self-test

**READ THE `<-- QUOTED` MARKER BEFORE ACTING ON A HIT.** A run of
`--derive` found ELEVEN glob hits and SIX were in this file - its own
fixtures, and its prose quoting the text BASH-1 removed. That is the
sixth instance on this project of a defect-grep finding its own
documentation. The fix is NOT a narrower pattern, because narrowing
stops matching a real instance before it stops matching a quotation,
and it is NOT a path self-exclusion, because that is the filter-by-path
mistake #115 exists to prevent. A hit whose number AND noun both sit
inside `"`-delimited runs is a QUOTATION of a count rather than a claim
of one, and is MARKED - never dropped, because a real instance can be
quoted too.

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

#: **WHAT MAKES A FILE A DATED RECORD HERE** (#183, and the classifier
#: was widened only after answering this).
#:
#: A record is a document that states what was true at ONE MOMENT and is
#: superseded by WRITING A NEW ONE rather than by being edited. The
#: operative distinction is **maintained vs superseded** - not whether a
#: date appears in it.
#:
#: **THE TEMPTING SIGNAL IS THE WRONG ONE, AND IT FAILS TOWARD
#: SILENCE.** Matching a date or sha in the CONTENT - "measured at
#: <sha>", "Seeded: <date>" - was tried and measured first: it selects
#: 19 and 2 files respectively, and among them are `CONTRIBUTING.md`,
#: `docs/OBLIGATIONS.md`, ADR-0023, ADR-0025 and a live brief. Those are
#: maintained canon, and two of #170's three HIGH findings lived in
#: exactly those two files. A content-date heuristic would have
#: reclassified them as records and hidden both. **Refused, with the
#: numbers, rather than tuned.**
#:
#: So the three signals below are structural, and each is a way of
#: being bound to a moment that a maintained document cannot be.

#: 1. A directory that IS the record boundary.
RECORD_DIRS = (
    "docs/worklogs/",
    "docs/plans/",
    "docs/research/",
    "docs/reviews/ledgers/",
)

#: 2. A name whose STEM ends in a word naming a finished act of
#: recording. This is the KIND rule the prefix list below could not
#: express: `DESIGN-DELTA-REVIEW`, `SPIKE-CLAIM-AUDIT`,
#: `COMPLIANCE-SPEC-PASS`, `F10-RULING`, `R2-LEFTOVER-VERDICTS` and
#: `FREEZE-DISMISSAL-RETEST` share no prefix and are all records.
RECORD_STEM_SUFFIXES = (
    "-RULING",
    "-VERDICTS",
    "-AUDIT",
    "-REPORT",
    "-PASS",
    "-RETEST",
    "-REVIEW",
    "-SWEEP",
)

#: **AND IT APPLIES TO DOCUMENTS ONLY.** The first version of this rule
#: silenced FIVE LIVE CHECKERS - `check-coupling-sweep.py` and
#: `check-resweep-verdicts.py` are CI gates named in `CONTRIBUTING.md`,
#: and `check-review-coverage.py`, `probe-142-exempt-inventory.py` and
#: `probe-coverage-ratchet.py` are live instruments. They end in
#: `-SWEEP`
#: and `-VERDICTS` because that is what they CHECK, not what they are.
#: **An executable is never a record, whatever it is called.**
#: `-INVENTORY` was dropped outright: it caught
#: `docs/data-inventory.md`,
#: the Article 30 record of processing, which is maintained compliance
#: prose.
RECORD_STEM_EXTENSIONS = (".md", ".txt")

#: 3. A `REVIEW-COVERS:` declaration - the repository's OWN marker
#: that a
#: document covers one commit range. **Measured: 13 files carry it and
#: the name rules already catch all 13**, so it changes nothing today.
#: It is here because it is the only signal that does not depend on
#: somebody following a naming convention, and a review document that
#: skips the convention still declares its range.
REVIEW_COVERS = "REVIEW-COVERS:"

#: 4. Keep a Changelog structure. `CHANGELOG.md` is a dated record by
#: construction - `changelog-standard.md` forbids backdating and each
#: entry is written once about a release - and the classifier did not
#: know it, which is where #183 started.
CHANGELOG_HEADING = re.compile(r"^##\s*\[(Unreleased|\d)", re.M)

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
    # Added by #183, each an act of recording bound to a task or run:
    "EVIDENCE-",  # a captured inventory, e.g. EVIDENCE-142-*
    "TASK-",  # a task's own write-up, e.g. TASK-139-*
    "LEDGER-",  # before/after snapshots
    "DESIGN-1",  # DESIGN-142-*; `DESIGN-R` above missed the numbered form
    "FIX-",  # FIX-3-REPORT and siblings
    "probe-156-arm-",  # captured probe output, committed as evidence
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
#: `$` and `{` also drop a SHELL POSITIONAL. `local label="$1" file="$2"
#: old="$3" new="$4"` sits one line above `ROWS=$((ROWS + 1))` in nine
#: amputation harnesses, and `$3`/`$4` were being read as "3 rows" and
#: "4 rows" - 14 confident false tallies, every one of them a variable.
#: `=` drops an ASSIGNMENT: `ROWS=0` beside `APPLIED=0` was read as a
#: claim of "0 rows" in six harnesses, and `ROW_FLOOR=15` was read as
#: the very claim it is the derivation FOR - the instrument agreeing
#: with itself, which is the one agreement that proves nothing.
NUMBER_TOKEN = re.compile(r"(?<![\w.,:/${=-])(" + _NUM + r")(?![\w-])", re.IGNORECASE)

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


def quoted_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges of `"`-delimited runs, for the QUOTED signal.

    Parity over `"` only. Apostrophes are excluded deliberately: prose
    here is full of possessives and contractions, and treating `'` as a
    delimiter would mark half the corpus.
    """
    spans: list[tuple[int, int]] = []
    open_at: int | None = None
    for i, ch in enumerate(text):
        if ch != '"':
            continue
        if open_at is None:
            open_at = i
        else:
            spans.append((open_at, i))
            open_at = None
    return spans


def _is_quoted(text: str, start: int, end: int) -> bool:
    """Are BOTH ends of the number..noun span inside quoted runs?

    **Both ends, not one span**, because a CONCATENATED literal is still
    a quotation: `"13 of the 15" + " " + "`scripts/*.sh` exceed"` puts
    the number in one string and the noun in the next, and requiring a
    single enclosing span left two of this file's own fixtures unmarked.
    Requiring the number to be quoted keeps the test tight - a bare
    count beside a quoted noun is still a claim and stays visible.
    """
    spans = quoted_spans(text)

    def within(pos: int) -> bool:
        return any(a <= pos <= b for a, b in spans)

    return within(start) and within(max(start, end - 1))


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


def is_record(relpath: str, text: str = "") -> bool:
    """A dated record: correct as written, never a finding.

    `text` is optional so the classifier stays callable from a path
    alone; the two CONTENT signals simply do not fire without it, and
    the caller in `scan()` always supplies it.
    """
    if relpath.startswith(RECORD_DIRS):
        return True
    # **`docs/briefs/` IS RULED NOT A RECORD CLASS** - Tier 0, on the
    # precedent that `check-review-coverage.py` refuses `docs/briefs` as
    # a RECORD path by name, because a brief INSTRUCTS and has carried
    # substantive rulings. One ruling, one place: no name rule below may
    # quietly readmit it. Measured: without it, `EVIDENCE-`, `FIX-`
    # and `-SWEEP` pulled 47 candidates out of six live briefs.
    if relpath.startswith("docs/briefs/"):
        return False
    name = relpath.rsplit("/", 1)[-1]
    if name.startswith(RECORD_PREFIXES):
        return True
    if name.endswith(RECORD_STEM_EXTENSIONS):
        stem = name.rsplit(".", 1)[0].upper()
        if stem.endswith(RECORD_STEM_SUFFIXES):
            return True
    if text:
        if REVIEW_COVERS in text[:4000]:
            return True
        if name == "CHANGELOG.md" and CHANGELOG_HEADING.search(text):
            return True
    return False


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

    __slots__ = (
        "path",
        "line",
        "number",
        "noun",
        "glob",
        "text",
        "record",
        "quoted",
    )

    def __init__(
        self,
        path: str,
        line: int,
        number: str,
        noun: str,
        glob: bool,
        text: str,
        quoted: bool = False,
        record: bool | None = None,
    ) -> None:
        """Record one adjacency and classify its file."""
        self.path = path
        self.line = line
        self.number = number
        self.noun = noun
        self.glob = glob
        self.text = text.strip()
        #: Computed once per FILE by `scan()` and passed in, because the
        #: CHANGELOG and REVIEW-COVERS signals read content, and
        #: re-reading per hit would be quadratic. `None` derives
        #: from the path alone, as the self-test's synthetic Hits do.
        self.record = is_record(path) if record is None else record
        #: The span sits inside a `"`-delimited run, so it is a
        #: QUOTATION of a count rather than a claim of one. **Marked,
        #: never excluded** - a real instance can be quoted too, and a
        #: filter that drops it would trade a misleading report for a
        #: silent one.
        self.quoted = quoted

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
        # ONE classification per file: the CHANGELOG and REVIEW-COVERS
        # signals read content, and re-deriving per hit would be
        # quadratic over a 22,000-candidate corpus.
        rec = is_record(rel, text)
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
                # The span runs from the number to the end of the noun.
                noun_end = joined.find(noun, m.end())
                end = noun_end + len(noun) if noun_end >= 0 else m.end()
                hits.append(
                    Hit(
                        rel,
                        idx + 1,
                        m.group(1),
                        noun,
                        glob,
                        joined,
                        _is_quoted(joined, m.start(), end),
                        record=rec,
                    )
                )
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


#: A harness's own declared floor. Same pattern `check-row-floors.py`
#: uses, deliberately - two readers of one literal must not disagree
#: about what a floor looks like.
FLOOR = re.compile(r"^\s*ROW_FLOOR=(\d+)\s*$", re.M)

#: Nouns whose claims sit beside a FLOOR, so a stale one means a floor
#: carrying slack rather than merely a wrong sentence.
TALLY_NOUNS = {"rows", "arms", "controls"}


def derive_tallies(hits: list[Hit]) -> list[tuple[Hit, int, int]]:
    """Prose tallies in a file that declares its own `ROW_FLOOR`.

    **THIS IS THE HALF NO GATE COVERS.** `check-row-floors.py` compares
    a harness's internal `ROW_FLOOR` against `ci.yml`'s `--min-rows`,
    and `check-row-floor-exactness.py` compares the floor against the
    table. **Neither reads the PROSE.** A docstring saying "34/34 rows"
    beside `ROW_FLOOR=20` is either a stale sentence or a floor carrying
    fourteen rows of slack, and nothing in the tree can tell which - so
    this reports the disagreement rather than picking a side.

    A claim that differs from the floor is NOT automatically wrong: most
    of these sentences are about a different set (arms of one control,
    rows of a table elsewhere). That is exactly why this reports.
    """
    floors: dict[str, int] = {}
    out: list[tuple[Hit, int, int]] = []
    for h in hits:
        if h.noun not in TALLY_NOUNS:
            continue
        if h.path not in floors:
            try:
                text = (ROOT / h.path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                floors[h.path] = -1
                continue
            found = FLOOR.search(text)
            floors[h.path] = int(found.group(1)) if found else -1
        floor = floors[h.path]
        if floor < 0:
            continue  # the file declares no floor: nothing to compare
        try:
            claimed = int(h.number.replace(",", ""))
        except ValueError:
            continue  # a quantifier, not a tally
        out.append((h, floor, claimed))
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
    # THE TALLY FALSE POSITIVES, both of which produced CONFIDENT WRONG
    # NUMBERS against a real ROW_FLOOR before they were excluded.
    probe("shell positional", 'old="$3" new="$4"   ROWS=$((ROWS + 1))', None)
    probe("assignment", "APPLIED=0 ROWS=0", None)
    probe("floor assignment", "ROW_FLOOR=15 ROWS=$((PASS + FAIL))", None)
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

    # #183's classifier. THE NEGATIVES ARE THE ARMS THAT MATTER: the
    # first version of this widening silenced five live checkers and a
    # compliance document, which is the direction the content-date
    # heuristic was refused for.
    def rec(label: str, path: str, want: bool, text: str = "") -> None:
        got = is_record(path, text)
        checks.append((f"RECORD? {label}: {path} -> {got}", got == want))

    rec("CHANGELOG by structure", "CHANGELOG.md", True, "## [Unreleased]\n")
    rec("a numbered DESIGN- write-up", "docs/reviews/DESIGN-142-scoped.md", True)
    rec("a stem naming an act of recording", "docs/reviews/SPIKE-AUDIT.md", True)
    rec("a ledger snapshot", "docs/reviews/ledgers/LEDGER-120-after.txt", True)
    rec("a live CI gate named -sweep", "docs/reviews/check-coupling-sweep.py", False)
    rec("a live gate named -verdicts", "docs/reviews/check-resweep-verdicts.py", False)
    rec("a live probe named -inventory", "docs/reviews/probe-142-inventory.py", False)
    rec("the Article 30 record, which is MAINTAINED", "docs/data-inventory.md", False)
    rec("a brief - RULED not a record class", "docs/briefs/B49B-SWEEP.md", False)
    rec("a brief the OLD prefix rule recorded", "docs/briefs/CODE-REVIEW-R2.md", False)
    rec(
        "CONTRIBUTING.md, which says 'measured'",
        "CONTRIBUTING.md",
        False,
        "it read 1987 citations - measured at abc1234",
    )
    rec(
        "OBLIGATIONS.md, which says 'Seeded:'",
        "docs/OBLIGATIONS.md",
        False,
        "**Owner:** CONF-6 - **Seeded:** 2026-08-28",
    )

    # POSITIVE CONTROL FOR `--tallies`. Every one of the 17 real tallies
    # either agrees with its floor or is an explicitly dated narrative,
    # so the finding list is EMPTY - and an empty finding list is a
    # claim about the selector until a planted defect is required back.
    # The plant is synthetic rather than a tree mutation on purpose: a
    # harness that edits its own repository has to prove it restored,
    # and this proves the same property with nothing to restore.
    real = ROOT / "scripts/check-u7-resilience-controls.sh"
    if real.exists():
        planted = Hit(
            "scripts/check-u7-resilience-controls.sh",
            1,
            "26",
            "controls",
            False,
            "26/26 controls fired",
        )
        got = derive_tallies([planted])
        checks.append(
            (
                f"PLANTED a stale '26 controls' against that file's real "
                f"ROW_FLOOR -> {[(f, c) for _, f, c in got]}",
                len(got) == 1 and got[0][1] == 31 and got[0][2] == 26,
            )
        )
        # And the negative half: a file with NO floor yields nothing,
        # rather than a zero that looks like agreement.
        nofloor = Hit("README.md", 1, "26", "controls", False, "x")
        checks.append(
            (
                "a file declaring NO ROW_FLOOR yields no tally, not a 0",
                derive_tallies([nofloor]) == [],
            )
        )

    # THE QUOTATION SIGNAL. Tier 0 ran `--derive` cold and found SIX of
    # eleven hits were in THIS FILE - its own fixtures and its prose
    # quoting BASH-1's removed text. That is the sixth instance on this
    # project of a defect-grep finding its own documentation, and the
    # recorded fix is NOT a narrower pattern: narrowing stops matching a
    # real instance before it stops matching a quotation.
    def quoted(label: str, line: str, want: bool) -> None:
        ms = list(NUMBER_TOKEN.finditer(line))
        got = False
        for m in ms:
            f = _noun_after(line, m.end())
            if f is None:
                continue
            ne = line.find(f[0], m.end())
            end = ne + len(f[0]) if ne >= 0 else m.end()
            if _is_quoted(line, m.start(), end):
                got = True
        checks.append((f"QUOTED {label}: {line[:52]!r} -> {got}", got == want))

    quoted(
        "prose quoting BASH-1",
        'BASH-1 said "all 20 `scripts/*.sh`" beside a population of 39',
        True,
    )
    quoted(
        "a probe() fixture",
        '    probe("BASH-1 glob", "all 20 `scripts/*.sh` run x", "y")',
        True,
    )
    quoted(
        "a REAL claim is NOT quoted",
        "You do not own the other 36 `scripts/*.sh`. See section D.",
        False,
    )
    quoted(
        "an unquoted tally is NOT quoted",
        "13 of the 15 `scripts/*.sh` exceed 100 lines",
        False,
    )
    # The signal must survive the line-join, because the quote that
    # opens this file's own docstring closes on the NEXT line.
    quoted(
        "quote spanning the join",
        'this shape - "all 20' + " " + '`scripts/*.sh`" against 39',
        True,
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
    ap.add_argument(
        "--tallies",
        action="store_true",
        help="prose row/arm/control counts against the file's own "
        "ROW_FLOOR - the half no gate reads",
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
    print(
        f'  ...of those, QUOTED - inside a `"`-run, so a quotation of a '
        f"count\n     rather than a claim of one: "
        f"{len([h for h in live if h.quoted])}"
    )
    print()

    if args.tallies:
        tallies = derive_tallies(live)
        tally_files = {h.path for h, _, _ in tallies}
        print(
            f"PROSE TALLIES in a file declaring its own ROW_FLOOR, at "
            f"{sha}: {len(tallies)} in {len(tally_files)} files"
        )
        print(
            "  A claim differing from the floor is NOT automatically "
            "wrong - most\n   are about a different set. It is either a "
            "stale sentence or a floor\n   carrying slack, and no gate "
            "reads either.\n"
        )
        for h, floor, claimed in sorted(
            tallies, key=lambda r: (-abs(r[2] - r[1]), r[0].path, r[0].line)
        ):
            mark = "==" if claimed == floor else f"delta {claimed - floor:+d}"
            print(
                f"{h.path}:{h.line}  claims {claimed} {h.noun}, "
                f"ROW_FLOOR={floor}  [{mark}]"
            )
            print(f"    {h.text[:130]}")
        return 0

    if args.derive:
        rows = derive_globs(live)
        print(f"GLOB candidates with a DERIVED population, at {sha}: {len(rows)}")
        print(
            "  (a glob is the one class where the true figure is "
            "mechanical; every\n   other noun needs a human to say "
            "which set it names)\n"
        )
        for h, git_n, shell_n, claim in sorted(
            rows, key=lambda r: (r[0].path, r[0].line)
        ):
            pop = (
                f"{git_n}"
                if git_n == shell_n
                else f"{git_n} (git) / {shell_n} (shell glob)"
            )
            if claim is None:
                verdict = f"QUANTIFIER `{h.number}` over {pop} tracked"
            elif claim in (git_n, shell_n):
                verdict = f"AGREES ({claim}) against {pop}"
            else:
                verdict = f"CLAIMS {claim}, TRACKED {pop}  <-- CHECK"
            if h.quoted:
                verdict += "   <-- QUOTED"
            print(f"{h.path}:{h.line}  `{h.noun}`  {verdict}")
            print(f"    {h.text[:140]}")
        return 0

    if args.findings:
        for h in sorted(live, key=lambda h: (h.path, h.line)):
            mark = ("Q" if h.quantified else " ") + ("q" if h.quoted else " ")
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
