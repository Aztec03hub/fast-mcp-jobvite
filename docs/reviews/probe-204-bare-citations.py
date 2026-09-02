#!/usr/bin/env python3
"""The BARE `:NNN` citation form: a discriminator and a population.

**WHY THIS EXISTS.** `check-design-citations.py` matches the design's
name followed by a colon and digits - the filename is REQUIRED,
on purpose, "so this does not match a bare
number". `check-standards-citations.py` and `check-clause-citations.py`
are anchored on a filename the same way, and so is the population query
in `WRONG-SUBJECT-REGISTER.md`. Three independent selectors, one blind
spot: **the form a human writes once the file is already named in the
sentence.**

`docs/adr/0017-...:67` is the instance that made it visible:

    "`DESIGN.md:515` is amended, and `:489-490`'s seven-member
     requirement then holds"

`:489-490` is a citation into `DESIGN.md`. Every gate in this repository
walks past it.

**THE DISCRIMINATOR IS THE HARD PART, AND IT IS THE
DELIVERABLE.** A bare `:NNN` also matches Python slices, JSON
bodies, IPv6 literals, f-string format specs and GitHub Actions
workflow commands. A selector with a
loose edge published a FALSE FINDING on this project on 2026-09-02, so
this file states its rule, names every shape it excludes, and counts
each exclusion so none of them can be silent.

## The rule, in one sentence

A bare-form citation is `:N` or `:N-M` whose colon is **not**
preceded by a filename character, minus six NAMED non-citation shapes.

The left-boundary half does the heavy lifting and it is not arbitrary:

  - `DESIGN.md:515`  colon preceded by `d`  -> QUALIFIED, not bare
  - `localhost:8080` colon preceded by `t`  -> a port
  - `10:30`          colon preceded by `0`  -> a time
  - `:489-490`       colon preceded by a backtick -> a candidate

**Times and ports are excluded BY CONSTRUCTION, not by a blocklist**,
because both carry a name or a digit to the left of the colon. That is
the whole reason the boundary is written as a character class rather
than as a list of things to skip: a blocklist selects for the shape
nobody thought of.

## The three arms, and why they are separate

**ARM A - CODE-SPAN.** The token is the entire content of a markdown
code span: `` `:489-490` ``. **This is a signal the language already
carries** - the author typed backticks to say "this is a token, not
prose". It is by far the dominant form and it is the one with a hard
left AND right boundary.

**ARM B - CONTINUATION.** A bare token on a line that already carries a
qualified `file.ext:N` citation earlier on it: `DESIGN.md:354-370,
:373-375, :617`. This is the form the register's population query
misses even when the filename IS present, because the query counts
matches of the qualified pattern and the trailing members are not
matches.

**ARM C - PROSE-BARE.** Everything left. This is the arm with no right
boundary and it is where the exclusions live.

Usage:
    python3 docs/reviews/probe-204-bare-citations.py            # census
    python3 docs/reviews/probe-204-bare-citations.py --sites
    python3 docs/reviews/probe-204-bare-citations.py --excluded
    python3 docs/reviews/probe-204-bare-citations.py --unanchored
    python3 docs/reviews/probe-204-bare-citations.py --controls

Exit 0 on a census, 1 if a control does not fire. **This is a PROBE, not
a gate**, and it is deliberately not wired: what to do about an
unanchored citation is a ruling nobody has made yet.
"""

from __future__ import annotations

import collections
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

_SEARCH_SUFFIXES = {".py", ".toml", ".md", ".yml", ".yaml", ".sh"}
_SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".ruff_cache", ".pytest_cache"}

#: The left boundary. A colon preceded by any of these belongs to a
#: QUALIFIED citation, a host:port, or a clock time - never to a bare
#: form. This is the same character class `check-design-citations.py`
#: requires a filename to sit in, read the other way round.
_FILENAME_CHAR = r"[A-Za-z0-9_./\\-]"

_BARE = re.compile(rf"(?<!{_FILENAME_CHAR}):(\d+)(?:-(\d+))?\b")

#: A QUALIFIED citation - the form all three existing selectors find.
#: The suffix list is closed on purpose: `foo.bar:12` where `bar` is not
#: a file type is not a citation, and an open `\.\w+` would swallow
#: `object.attribute:12`.
_QUALIFIED = re.compile(
    r"(?P<name>[A-Za-z0-9_.\-/]+\.(?:md|py|yml|yaml|sh|toml|txt|cfg|ini|json))"
    r":(\d+)(?:-(\d+))?"
)

#: ===================== THE EXCLUSIONS =====================
#: Every one is a SHAPE with a name and a count. A shape excluded
#: without being counted is how a population shrinks with nobody
#: noticing - `check-design-citations.py` learned that at R13-H1,
#: where a counter was incremented and read nowhere.
#:
#: Each is keyed by the character immediately LEFT of the colon, except
#: the two that need more than one character of context.
_PREV_CHAR_SHAPES = {
    "[": (
        "SLICE",
        "a Python slice or display cap - `reasons[:1]`, `untouched[:15]`",
    ),
    '"': (
        "JSON",
        'a JSON key/value pair - `{"status":{"code":401}}`',
    ),
    ":": (
        "DOUBLE-COLON",
        "IPv6 `[::1]` or a GitHub Actions command `::error::4/5`",
    ),
}


def _tracked_files() -> list[tuple[str, pathlib.Path]]:
    """Every tracked file worth scanning.

    `git ls-files` is the authority.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    ).stdout
    files = []
    for name in out.split("\0"):
        if not name:
            continue
        path = REPO_ROOT / name
        if path.suffix not in _SEARCH_SUFFIXES:
            continue
        if any(part in _SKIP_PARTS for part in pathlib.Path(name).parts):
            continue
        files.append((name, path))
    return files


def _format_spec(line: str, start: int, end: int) -> bool:
    """`f"...{len(rows):4}..."` - a format spec, not a citation.

    The test is structural rather than a character: the token must sit
    inside a `{...}` that OPENS to its left with no `}` between, and the
    line must carry an f-string prefix. Both halves are required - a
    markdown table cell can contain braces, and a plain `{...}` in prose
    is not a format spec.
    """
    if "f'" not in line and 'f"' not in line:
        return False
    left = line[:start]
    open_brace = left.rfind("{")
    if open_brace == -1:
        return False
    if "}" in left[open_brace:]:
        return False
    close = line.find("}", end)
    return close != -1


def _log_line(line: str, start: int) -> bool:
    """`| INFO | __main__:<module>:2 - tool_invocation` - loguru.

    Quoted verbatim in four places as EVIDENCE. The `:2` is a source
    line number in a log record, not a citation into a document.
    """
    return "<module>" in line[:start]


def _grep_pattern(line: str, start: int) -> bool:
    """`grep -rn ':1276-1278' docs/adr/` - a citation as SEARCH TEXT.

    It is a citation-shaped literal being searched FOR, not a citation
    being made, and repointing it would break the command.

    **MY FIRST VERSION OF THIS RULE WAS `"grep" in line[:start]` AND IT
    EXCLUDED 21 SITES, 20 OF THEM REAL CITATIONS.** Lines like *"`grep
    -n` puts that word at the end of `:172`"* mention the tool and then
    make a citation. The rule needs the token to be INSIDE the quoted
    argument, not merely downstream of the word. Exactly one site in
    this tree is the real shape, and the count went 21 -> 1 when the
    rule was tightened - which is why every exclusion here is printed
    with `--excluded` rather than trusted.
    """
    return start > 0 and line[start - 1] == "'" and "grep" in line[:start]


def excluded_shape(line: str, start: int, end: int) -> str | None:
    """The one place the exclusions are decided.

    **`controls()` and `scan()` MUST call this same function.** An
    earlier draft of this file had the ladder written out twice - once
    in the scan and once in the controls - which is a control that
    tests a COPY of its subject. It would have gone on passing after
    the scan's copy changed.
    """
    prev = line[start - 1 : start] if start else ""
    shape = _PREV_CHAR_SHAPES.get(prev)
    if shape is not None:
        return shape[0]
    if _format_spec(line, start, end):
        return "FORMAT-SPEC"
    if _log_line(line, start):
        return "LOG-LINE"
    if _grep_pattern(line, start):
        return "GREP-PATTERN"
    return None


Site = collections.namedtuple("Site", "path lineno arm token start end line")


def scan() -> tuple[
    list[Site], collections.Counter[str], list[tuple[str, int, str, str]]
]:
    """Every site, its arm, and every exclusion with its shape."""
    sites: list[Site] = []
    excluded: list[tuple[str, int, str, str]] = []
    shapes: collections.Counter[str] = collections.Counter()

    for name, path in _tracked_files():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            qual_ends = [m.end() for m in _QUALIFIED.finditer(line)]
            for m in _BARE.finditer(line):
                start, end = m.start(), m.end()
                prev = line[start - 1 : start] if start else ""
                nxt = line[end : end + 1]

                shape = excluded_shape(line, start, end)
                if shape is not None:
                    shapes[shape] += 1
                    excluded.append((name, lineno, shape, line.strip()))
                    continue

                if prev == "`" and nxt == "`":
                    arm = "A-CODE-SPAN"
                elif any(q <= start for q in qual_ends):
                    arm = "B-CONTINUATION"
                else:
                    arm = "C-PROSE-BARE"
                sites.append(Site(name, lineno, arm, m.group(0), start, end, line))
    return sites, shapes, excluded


#: **THE WINDOW IS NOT ONE NUMBER, AND PICKING ONE IS THE RULING.**
#: A first draft of this file asked a single question - "is a filename
#: named within 8 lines, stopping at a blank line?" - and answered
#: UNANCHORED for 58% of the corpus. That figure is an artefact of the
#: window, not a property of the corpus: much of `docs/reviews/` names
#: its subject in a SECTION HEADING and then cites bare forms for forty
#: lines beneath it, which a reader resolves without difficulty and a
#: blank-line window cannot see.
#:
#: So the probe reports a LADDER, tightest scope first, and Tier 0 rules
#: on where the line falls. Each rung is a different claim about how far
#: a reader carries a filename.
_PARAGRAPH_WINDOW = 8
#: How far back to look for the enclosing markdown heading before giving
#: up. Beyond this the "section" is not a section a reader holds in
#: their head either.
_SECTION_WINDOW = 120

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")

LADDER = ("SAME-LINE", "PARAGRAPH", "SECTION", "FILE", "UNANCHORED")

#: **THE ANCHOR IS A FILENAME, NOT A CITATION - AND MY FIRST VERSION GOT
#: THIS WRONG IN EXACTLY THE WAY THIS TASK IS ABOUT.** Anchoring on
#: `_QUALIFIED` asked "is there another `file.ext:N` nearby", which is
#: the same filename-plus-colon shape the three existing selectors are
#: built on. It reported 19 UNANCHORED sites. Reading two of them by
#: hand killed the rule:
#:
#:   `docs/briefs/BRIEF-187-floor-container.md:88` cites `:201-202` two
#:   lines under *"`check-row-floor-exactness.py` enumerates..."* - the
#:   file is named, with no line number, so `_QUALIFIED` walked past it.
#:
#:   `docs/worklogs/PLAN-DRAFT7-SELF-AUDIT.md:20` cites `:5` in a table
#:   whose header line 3 reads *"**Subject:**
#:   `docs/plans/IMPLEMENTATION-PLAN.md`"*. Same shape.
#:
#: A reader resolves a bare citation from the last FILE NAMED,
#: however it was named. So the anchor pattern drops the `:N`.
_FILE_MENTION = re.compile(
    r"(?P<name>[A-Za-z0-9_.\-/]+\.(?:md|py|yml|yaml|sh|toml|txt|cfg|ini|json))\b"
)


def _names_in(text_lines: list[str]) -> list[str]:
    return [
        m.group("name") for line in text_lines for m in _FILE_MENTION.finditer(line)
    ]


def anchor(sites: list[Site]) -> dict[tuple[str, int, int], tuple[str, str]]:
    """For each site, the TIGHTEST scope in which its file is named.

    Returns (rung, detail). Rungs, tightest first:
      SAME-LINE   a qualified citation earlier on the citing line
      PARAGRAPH   within the blank-line-bounded block above
      SECTION     within the enclosing markdown section
      FILE        somewhere else in the file, and exactly one candidate
      UNANCHORED  named nowhere - unresolvable without guessing

    A rung is suffixed `-AMBIGUOUS` when that scope names two or more
    DIFFERENT files, because "resolvable" and "resolvable to one thing"
    are not the same claim.
    """
    by_file: dict[str, list[str]] = {}
    for name, path in _tracked_files():
        try:
            by_file[name] = path.read_text().splitlines()
        except UnicodeDecodeError:
            pass

    def verdict(rung: str, names: list[str]) -> tuple[str, str]:
        distinct = sorted(set(names))
        if len(distinct) == 1:
            return (rung, distinct[0])
        return (f"{rung}-AMBIGUOUS", ", ".join(distinct[:4]))

    out: dict[tuple[str, int, int], tuple[str, str]] = {}
    for s in sites:
        key = (s.path, s.lineno, s.start)
        lines = by_file.get(s.path, [])
        idx0 = s.lineno - 1  # 0-based index of the citing line

        same = _names_in([s.line[: s.start]])
        if same:
            # the LAST one before the token is the one a reader carries
            out[key] = (
                "SAME-LINE",
                same[-1] if len(set(same)) == 1 else ", ".join(sorted(set(same))[:4]),
            )
            continue

        para: list[str] = []
        for back in range(1, _PARAGRAPH_WINDOW + 1):
            i = idx0 - back
            if i < 0 or not lines[i].strip():
                break
            para.append(lines[i])
        # a reader reads forward on the citing line too
        para += [s.line[s.end :]]
        got = _names_in(para)
        if got:
            out[key] = verdict("PARAGRAPH", got)
            continue

        section: list[str] = []
        for back in range(1, _SECTION_WINDOW + 1):
            i = idx0 - back
            if i < 0:
                break
            section.append(lines[i])
            if _HEADING.match(lines[i]):
                break
        got = _names_in(section)
        if got:
            out[key] = verdict("SECTION", got)
            continue

        got = _names_in(lines)
        if got:
            out[key] = verdict("FILE", got)
            continue

        out[key] = ("UNANCHORED", "")
    return out


def controls() -> int:
    """Prove the discriminator admits and refuses in BOTH directions.

    **A selector's controls must fire in BOTH directions.** A regression
    check that only asserts "admits every observed caller" is monotone
    and cannot catch over-permission, which is the exact defect this
    file exists because of.
    """
    admit = [
        ("`:489-490`", "the ADR-0017 instance, code-span form"),
        ("see `:1223` there", "code-span in prose"),
        ("DESIGN.md:354-370, :373-375, :617", "continuation form"),
        ("the standard says at :383 that", "prose-bare, no ticks"),
        ("The corpus's set is `{:86}`", "brace-wrapped, NOT a format spec"),
    ]
    refuse = [
        ("reasons[:1]", "SLICE"),
        ("untouched[:15]", "SLICE"),
        ('b\'{"status":{"code":401}}\'', "JSON"),
        ('["127.0.0.1", "::1", "[::1]"]', "DOUBLE-COLON"),
        ('echo "::error::4/5 ROWS"', "DOUBLE-COLON"),
        ('print(f"{len(rows):4}  {reason}")', "FORMAT-SPEC"),
        ("| INFO | __main__:<module>:2 - tool_invocation", "LOG-LINE"),
        ("`grep -rn ':1276-1278' docs/adr/`", "GREP-PATTERN"),
        ("DESIGN.md:515 is amended", "QUALIFIED - not a bare form at all"),
        ("http://localhost:8080/mcp", "a port"),
        ("2026-08-28 22:15:26 the run", "a clock time"),
    ]

    def classify(line: str) -> list[str]:
        """The SAME ladder `scan()` runs, via the SAME function."""
        return [
            m.group(0)
            for m in _BARE.finditer(line)
            if excluded_shape(line, m.start(), m.end()) is None
        ]

    fired = total = 0
    print("ADMIT - each must yield at least one citation:")
    for line, why in admit:
        total += 1
        got = classify(line)
        ok = bool(got)
        fired += ok
        print(f"  {'FIRED    ' if ok else 'DID NOT  '} {why:42} {got}")
    print("\nREFUSE - each must yield NOTHING:")
    for line, why in refuse:
        total += 1
        got = classify(line)
        ok = not got
        fired += ok
        print(f"  {'FIRED    ' if ok else 'DID NOT  '} {why:42} {got}")
    print(f"\n{fired}/{total} controls fired.")
    return 0 if fired == total else 1


def main(argv: list[str]) -> int:
    if "--controls" in argv:
        return controls()

    sites, shapes, excluded = scan()

    if "--excluded" in argv:
        for name, lineno, shape, line in excluded:
            print(f"{shape:13} {name}:{lineno}  {line[:110]}")
        return 0

    anchors = anchor(sites)

    if "--sites" in argv:
        for s in sites:
            verdict, detail = anchors[(s.path, s.lineno, s.start)]
            print(f"{s.arm:15} {verdict:11} {detail:34} {s.path}:{s.lineno}  {s.token}")
        return 0

    if "--unanchored" in argv:
        for s in sites:
            verdict, _ = anchors[(s.path, s.lineno, s.start)]
            if verdict == "UNANCHORED":
                print(f"{s.path}:{s.lineno}  {s.token}  {s.line.strip()[:100]}")
        return 0

    print("BARE-FORM CITATION CENSUS")
    print(f"  {len(sites)} sites in {len({s.path for s in sites})} files\n")
    print("  by ARM:")
    for arm, n in sorted(collections.Counter(s.arm for s in sites).items()):
        files = len({s.path for s in sites if s.arm == arm})
        print(f"    {arm:15} {n:6}  in {files:4} files")
    print("\n  by ANCHOR - what file does the reader inherit?")
    ac = collections.Counter(v for v, _ in anchors.values())
    order = {rung: i for i, rung in enumerate(LADDER)}
    for verdict, n in sorted(
        ac.items(), key=lambda kv: (order[kv[0].removesuffix("-AMBIGUOUS")], kv[0])
    ):
        print(f"    {verdict:20} {n:6}")
    one = sum(n for v, n in ac.items() if not v.endswith("-AMBIGUOUS"))
    print(f"    {'-> resolves to ONE file':20} {one:6}  ({one * 100 // len(sites)}%)")
    print("\n  the inherited file, where there is one:")
    named = collections.Counter(
        d for v, d in anchors.values() if v in ("SAME-LINE", "BLOCK")
    )
    for name, n in named.most_common(12):
        print(f"    {n:6}  {name}")
    print(f"    ({len(named)} distinct files inherited in all)")
    print("\n  EXCLUDED as a named non-citation shape:")
    for shape, n in sorted(shapes.items(), key=lambda kv: -kv[1]):
        print(f"    {shape:14} {n:6}  {dict(v for v in _SHAPE_WHY.items())[shape]}")
    print(f"    {sum(shapes.values()):20}  total excluded")
    print(
        "\nNOTE: this is a PROBE, not a gate. It says which sites are "
        "citations and\nwhat file each inherits. It does NOT say whether "
        "any of them is CORRECT -\nthat needs reading, exactly as #196 read "
        "the qualified form."
    )
    return 0


_SHAPE_WHY = {
    "SLICE": _PREV_CHAR_SHAPES["["][1],
    "JSON": _PREV_CHAR_SHAPES['"'][1],
    "DOUBLE-COLON": _PREV_CHAR_SHAPES[":"][1],
    "FORMAT-SPEC": "an f-string replacement field - `{len(rows):4}`",
    "LOG-LINE": "loguru output quoted as evidence - `__main__:<module>:2`",
    "GREP-PATTERN": "the citation as a SEARCH STRING inside a grep",
}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
