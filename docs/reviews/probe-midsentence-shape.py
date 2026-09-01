#!/usr/bin/env python3
"""Count `DESIGN.md:N-M` citations that start or end MID-SENTENCE.

    python3 docs/reviews/probe-midsentence-shape.py [--sha <ref>]
                                                    [--controls]
                                                    [--edges]
                                                    [--limit N]

**DELIBERATELY NOT A GATE, and named `probe-` so it cannot become one by
accident.** `docs/reviews/check-checkers-are-wired.py` puts every
`docs/reviews/check-*` file into a container that must be wired into
`ci.yml` or carry a stated exemption. A gate wired while its backlog is
unknown lands red on the first run, and this project has refused that
four times (#125's discipline: MEASURE, then fix, then wire). This file
is the measuring half. Rename it `check-midsentence-shape.py` and wire
it on the day its backlog is zero - not before.

**THE SHAPE.** `check-design-citation-shape.py` decides five things:
out of bounds, entirely blank, fence-or-separator only, starts on a
blank line, ends on a blank line. Every one of them answers *"this
range CANNOT be anyone's subject"*. None sees a range whose FIRST line
does not BEGIN a sentence, or whose LAST line does not END one. That is
decidable without knowing the claim, and it is a strict superset of the
two blank-line shapes: a blank first line begins no sentence and a
blank last line ends none, so both are reported here too (as
`start:blank` / `end:blank`) rather than silently dropped.

**WHY IT IS WORTH COUNTING.** A range already cut mid-sentence is one
repoint away from losing its claim. #126's F3 is the proof: a clean
`end - 1` applied to `906-907` would have produced an unrelated
sentence that RESOLVES and passes both existing citation gates forever
- `DESIGN.md:906` (REPOINT-EXEMPT: a record of where a defect WAS, and
the marker keeps this line out of the very container this file counts).

**WHAT "SENTENCE" MEANS HERE, because the number is only as good as the
definition.** The decision is structural, made from the neighbouring
lines rather than from grammar:

* A line BEGINS a sentence if it opens a block (heading, fenced or
  indented code, table row, list item, blockquote), or if the line
  before it is blank / a block of one of those kinds / a line that ends
  in `.`, `!`, `?`, `:` or `;` (trailing `` ` ``, `"`, `'`, `)`, `]`,
  `*` and `_` are stripped first, so `**done.**` counts).
* A line ENDS a sentence if it closes a block in the same sense, ends
  in one of that punctuation set, is the last line of the file, or is
  followed by a blank line or the start of a new block.

**Where that definition is LENIENT, i.e. where it under-counts.** An
abbreviation ending a line (`e.g.`, `i.e.`, `cf.`, a numbered `1.`)
reads as a terminator, so a range broken there is NOT reported. A line
ending in `:` is treated as a terminator, which is right for a lead-in
and wrong for a mid-clause colon. `--edges` prints what the definition
actually does at abbreviations, code spans, list items, headings and
table rows against the frozen design, so the number is auditable rather
than asserted.

**Where it is STRICT.** A citation of a SINGLE line inside a paragraph
is reported, because such a line usually neither begins nor ends a
sentence. That is a real property of the range and not a bug, but it is
a different population from the multi-line case, so the summary splits
the two. `check-design-citation-shape.py`'s ends-blank branch excludes
single-line ranges deliberately (`end > start`); this probe does not,
and says so.

Exit code is 0 whatever it finds. This measures; it does not judge.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import pathlib
import re
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent

#: Punctuation that ends a sentence. `;` and `:` are included as
#: LENIENT terminators - see the docstring; they make the count a lower
#: bound rather than an inflated one.
TERMINATORS = ".!?:;"

#: Stripped off the end of a line before looking for a terminator, so
#: `**closed.**`, `(closed.)` and ``a `word`.`` all read correctly.
DECORATION = "`\"'*_)]}"

HEADING = re.compile(r"#{1,6}\s")
LIST = re.compile(r"([-*+]|\d+\.)\s")


def _shape_module() -> types.ModuleType:
    """Import the shape checker so its SELECTOR is reused, not copied.

    A second selector is a second population, and #134 spent a section
    on exactly that hazard. `code_files()`, `CITE` and the `EXEMPT`
    marker all come from there, so this probe's container is the same
    881 sites #126 and #134 sampled.
    """
    path = HERE / "check-design-citation-shape.py"
    spec = importlib.util.spec_from_file_location("_shape", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def line_kinds(lines: list[str]) -> list[str]:
    """One kind per line, with fenced blocks tracked as state.

    A fence's CONTENTS are code even when they are not indented, and a
    line-at-a-time classifier cannot see that. Six fence lines in the
    frozen design open three blocks; without this the prose test would
    run over their contents.
    """
    kinds: list[str] = []
    in_fence = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            kinds.append("fence")
            continue
        if in_fence:
            kinds.append("code")
        elif not stripped:
            kinds.append("blank")
        elif raw.startswith("    "):
            kinds.append("code")
        elif HEADING.match(stripped):
            kinds.append("heading")
        elif stripped.startswith("|"):
            kinds.append("table")
        elif stripped.startswith(">"):
            kinds.append("quote")
        elif LIST.match(stripped):
            kinds.append("list")
        else:
            kinds.append("text")
    return kinds


#: Kinds that are a block of their own: they begin and end whatever
#: they contain, so a range boundary landing on one is not mid-sentence.
BLOCK = frozenset({"heading", "fence", "code", "table"})


def terminated(line: str) -> bool:
    """Does this line end on sentence-ending punctuation?"""
    body = line.rstrip()
    while body and body[-1] in DECORATION:
        body = body[:-1]
    return bool(body) and body[-1] in TERMINATORS


def starts_sentence(num: int, lines: list[str], kinds: list[str]) -> bool:
    """Can line `num` (1-based) be the FIRST line of a subject?"""
    kind = kinds[num - 1]
    if kind == "blank":
        return False
    if kind in BLOCK:
        return True
    if num == 1:
        return True
    prev_kind = kinds[num - 2]
    if prev_kind == "blank" or prev_kind in BLOCK:
        return True
    return terminated(lines[num - 2])


def ends_sentence(num: int, lines: list[str], kinds: list[str]) -> bool:
    """Can line `num` (1-based) be the LAST line of a subject?"""
    kind = kinds[num - 1]
    if kind == "blank":
        return False
    if kind in BLOCK:
        return True
    if terminated(lines[num - 1]):
        return True
    if num == len(lines):
        return True
    next_kind = kinds[num]
    return next_kind == "blank" or next_kind in BLOCK or next_kind == "list"


def classify(
    start: int, end: int, lines: list[str], kinds: list[str]
) -> tuple[str, ...]:
    """The mid-sentence verdicts for one range; empty when it is clean.

    Out-of-bounds ranges are NOT this probe's business -
    `check-design-citation-shape.py` already reports them and reports
    zero today - but they must not crash the scan either, so they come
    back as their own label.
    """
    if start < 1 or end > len(lines) or start > end:
        return ("out of bounds (not this probe's shape)",)
    verdicts: list[str] = []
    if not starts_sentence(start, lines, kinds):
        blank = not lines[start - 1].strip()
        verdicts.append("start:blank" if blank else "start:mid-sentence")
    if not ends_sentence(end, lines, kinds):
        blank = not lines[end - 1].strip()
        verdicts.append("end:blank" if blank else "end:mid-sentence")
    return tuple(verdicts)


def _one_paragraph(lines: list[str], kinds: list[str]) -> tuple[int, int, int]:
    """One prose paragraph as `(first, interior, last)`, from ONE run.

    The interior line is one that neither begins nor ends a sentence,
    which is what makes the two mid-sentence arms of `controls` able to
    fire at all.
    """
    num = 1
    while num <= len(lines):
        if kinds[num - 1] != "text" or (num > 1 and kinds[num - 2] != "blank"):
            num += 1
            continue
        last = num
        while last < len(lines) and kinds[last] == "text":
            last += 1
        for inner in range(num + 1, last):
            if not terminated(lines[inner - 2]) and not terminated(lines[inner - 1]):
                return num, inner, last
        num = last + 1
    raise RuntimeError("no multi-line prose paragraph in the design")


def controls(lines: list[str], kinds: list[str]) -> int:
    """Every branch must FIRE on a range built to trip it.

    R10 measured what a detector with no reachable test is worth:
    deleting the blank-start branch of the sibling checker outright
    left its output byte-identical. Each arm below names the line
    numbers it used, so a reader can check them against the design
    rather than trusting the word FIRED. The negative arms are the
    load-bearing half - without them an arm that returns a finding for
    everything passes every positive arm.
    """
    # Chosen by SEARCH over the frozen design rather than typed in, so
    # these do not go stale when the design is re-frozen. The three
    # numbers must come from ONE paragraph: the first attempt drew them
    # independently and produced `6-3`, an inverted range that scored
    # out-of-bounds and made the arm look dead.
    para_start, mid, para_end = _one_paragraph(lines, kinds)
    blank = next(i for i, k in enumerate(kinds, 1) if k == "blank")
    head = next(i for i, k in enumerate(kinds, 1) if k == "heading")

    cases: list[tuple[str, int, int, str | None]] = [
        (f"starts mid-sentence ({mid}-{para_end})", mid, para_end, "start:mid"),
        (f"ends mid-sentence ({para_start}-{mid})", para_start, mid, "end:mid"),
        (f"starts blank ({blank}-{blank + 2})", blank, blank + 2, "start:blank"),
        (f"ends blank ({blank - 1}-{blank})", blank - 1, blank, "end:blank"),
        (f"out of bounds ({len(lines) + 9})", len(lines) + 9, len(lines) + 9, "bounds"),
        # THE NEGATIVE ARMS. A `classify` that flags everything passes
        # every arm above and fails both of these.
        (f"a whole paragraph ({para_start}-{para_end})", para_start, para_end, None),
        (f"a heading alone ({head})", head, head, None),
    ]

    fired = 0
    for label, start, end, expect in cases:
        got = classify(start, end, lines, kinds)
        ok = not got if expect is None else any(expect in verdict for verdict in got)
        shown = ", ".join(got) if got else "no finding, as required"
        print(f"  CONTROL {label} -> {'FIRED' if ok else 'DID NOT FIRE'} ({shown})")
        fired += ok
    print(f"\n{fired}/{len(cases)} controls fired.")
    return 0 if fired == len(cases) else 1


def edges(lines: list[str], kinds: list[str]) -> int:
    """Show what the DEFINITION does at its known-questionable edges.

    A clean number over a definition nobody has inspected is worth
    less than a smaller number whose blind spots are written down.
    Each row is a real line of the frozen design, found by search.
    """
    probes: list[tuple[str, re.Pattern[str]]] = [
        ("abbreviation ending a line", re.compile(r"(e\.g\.|i\.e\.|cf\.|etc\.)$")),
        ("code span ending a line", re.compile(r"`[^`]+`$")),
        ("colon ending a line", re.compile(r":$")),
        ("a list item", re.compile(r"^\s*[-*+]\s")),
        ("a heading", re.compile(r"^#{1,6}\s")),
        ("a table row", re.compile(r"^\|")),
        ("a line ending in a comma", re.compile(r",$")),
    ]
    for label, pattern in probes:
        hit = next(
            (i for i, t in enumerate(lines, 1) if pattern.search(t.rstrip())), None
        )
        if hit is None:
            print(f"  {label:32}  NO INSTANCE in the frozen design")
            continue
        print(
            f"  {label:32}  DESIGN.md:{hit}  kind={kinds[hit - 1]}  "
            f"begins={starts_sentence(hit, lines, kinds)}  "
            f"ends={ends_sentence(hit, lines, kinds)}"
        )
        print(f"      {lines[hit - 1].strip()[:88]}")
    return 0


def main() -> int:
    shape = _shape_module()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", default=shape.frozen_sha())
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--edges", action="store_true")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    lines = shape.design_lines(args.sha)
    kinds = line_kinds(lines)

    if args.controls:
        return controls(lines, kinds)
    if args.edges:
        return edges(lines, kinds)

    tally: collections.Counter[str] = collections.Counter()
    per_file: collections.Counter[str] = collections.Counter()
    rows: list[tuple[str, int, int, int, tuple[str, ...]]] = []
    seen = 0

    for path in shape.code_files():
        rel = path.relative_to(ROOT).as_posix()
        for num, text in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if shape.EXEMPT in text:
                continue
            for match in shape.CITE.finditer(text):
                seen += 1
                start = int(match.group(1))
                end = int(match.group(2) or match.group(1))
                verdicts = classify(start, end, lines, kinds)
                if verdicts:
                    rows.append((rel, num, start, end, verdicts))
                    per_file[rel] += 1
                    for verdict in verdicts:
                        tally[verdict] += 1

    if seen == 0:
        print("PARSED ZERO CITATIONS. The selector is broken; any count is a lie.")
        return 1

    single = [r for r in rows if r[2] == r[3]]
    multi = [r for r in rows if r[2] != r[3]]

    print(f"container: {seen} citation sites, {len(shape.code_files())} tracked files")
    print(f"design:    {args.sha}, {len(lines)} lines\n")
    print(
        f"{len(rows)} site(s) start or end mid-sentence "
        f"({100 * len(rows) / seen:.1f}% of {seen})"
    )
    print(f"  {len(multi):4}  multi-line ranges")
    print(
        f"  {len(single):4}  single-line citations "
        f"(a line inside a paragraph rarely does either)\n"
    )

    for verdict, count in sorted(tally.items()):
        print(f"  {count:4}  {verdict}")

    print(f"\nper-file distribution ({len(per_file)} files):")
    for rel, count in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:4}  {rel}")

    print(f"\nfirst {args.limit} multi-line instances, in path order:")
    for rel, num, start, end, verdicts in multi[: args.limit]:
        cited = f"{start}" if start == end else f"{start}-{end}"
        print(f"  {rel}:{num}  DESIGN.md:{cited}  {', '.join(verdicts)}")
        print(f"      first  {start}| {lines[start - 1].rstrip()[:76]}")
        print(f"      last   {end}| {lines[end - 1].rstrip()[:76]}")

    print("\nThis is a MEASUREMENT, not a gate: exit 0 whatever the count.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
