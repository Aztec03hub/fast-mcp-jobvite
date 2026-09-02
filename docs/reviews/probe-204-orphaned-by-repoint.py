#!/usr/bin/env python3
"""ORPHANED-BY-REPOINT: one citation, two spellings, only one repointed.

**THE INSTANCE THIS EXISTS FOR.** `docs/adr/0017-...` names ONE range
twice - qualified at `:16` and bare at `:67`:

    :16  **The contradiction (D1).** `DESIGN.md:489-490` states that ...
    :67  - **`DESIGN.md:515` is amended**, and `:489-490`'s seven-member
         requirement then holds ...

Commit `b0e86b8` - *"Repoint 713 DESIGN.md citations, from the checker's
own parsed output"* - moved the qualified one to `:495-496` and walked
past the bare one, **because the checker whose parsed output drove the
sweep requires the filename.** Both lines are still in the file and they
now disagree with each other.

**THIS IS A THIRD CLASS, not DRIFTED and not WRONG.** A DRIFTED citation
was right when written and the target moved under it; the remedy is a
repoint. A WRONG one never named its subject. This one was right when
written, the target moved, the repoint RAN, and it fixed half the
instance - so the file contradicts itself and the surviving half is
invisible to the tool that would fix it.

## What this probe does, and the two ways it lied first

It replays every commit that changed a qualified `<file>.ext:N` citation
and asks whether the OLD number still stands, in BARE form, in the same
file, anchored to the SAME document.

**Both of those last two conditions were missing from my first version
and it reported 72 candidates.** Reading them killed two whole shapes:

  - no exclusion ladder, so a JSON body's `{"code":401}` inside
    `docs/DESIGN.md` was reported as an orphaned `:401`;
  - no document check, so a bare `:153` anchored to
    `agentic-coding-standard.md` was matched against a repoint of
    `readme-standard.md:153`.

A third shape survives both fixes and cannot be settled by a machine:
prose that DISCUSSES the old range on purpose - `CONFORMANCE-RESWEEP.md`
writes *"`:153` rather than `:153-155`"* as a record of the change.
Those are reported and MARKED, not filtered, because a filter for
them would be a filter for the finding too.

## THIS PRODUCES CANDIDATES, NOT FINDINGS

The file-level pairing above is not tight enough to publish a count
from: it asks "was this range repointed anywhere in this file, and does
a bare form of the old value still stand anywhere in this file", and
those two anywheres need not be the same citation. **#208 added the two
tests below, which narrow the candidate set from 55 to 35 by asking the
question per LINE rather than per FILE.**

**TEST A - COEXISTENCE.** Did the bare line itself, byte for byte, exist
in the file at the repoint commit's PARENT? If it did not, the two
spellings never stood together when the sweep ran, so the sweep cannot
have walked past this line and it is not an orphan.

This is the mechanised form of the `git log -S` read that was previously
prescribed as manual work. Measured at 55 candidates: it drops 19, and
those 19 include **all six** of the known-false `src/` and `tests/`
continuation comments, such as

    # U7 - RESILIENCE (DESIGN.md:354-370, :373-375, :617).

which matched only because `DESIGN.md:373-375` was repointed ELSEWHERE
in the same file. It also drops `docs/adr/0028-...`, whose contrast of
an old and a new range is deliberate - **not because it can tell a
contrast from a contradiction, which no selector can, but because that
line postdates its repoint.** Do not read that as the trap being solved.

**TEST B - DISAGREES TODAY.** In the file as it stands, is the cited
document named in QUALIFIED form at some value OTHER than the bare one?
Only then does the document actually contradict itself. If every
qualified mention agrees with the bare half, there is nothing to find.

**This test exists because the one CONFIRMED instance was still being
reported after it was fixed.** `docs/adr/0017-...` carried
`DESIGN.md:489-490` qualified and bare; `b0e86b8` moved the qualified
half to `:495-496`; `be94bce` restored it to `489-490`, so the ADR
agrees with itself again. The probe went on listing it FIRST, because it
reads history and never looked at the present state of the other half. A
detector whose headline row is its own closed instance teaches the
reader to discount the whole list.

**THE `->` DESTINATION WAS NONDETERMINISTIC AND IS NO LONGER PRINTED.**
It was never evidence - when one commit repoints several ranges in one
file it pairs an arbitrary removal with an arbitrary addition - but it
was worse than that: `removed[f] - added[f]` is a set of `str` tuples,
iterated in hash order, and Python randomises string hashing per
process. Two runs over an IDENTICAL tree differed on **99 lines**, all
of them destinations. So no two readers saw the same output and a diff
between two runs meant nothing. The pairing is now sorted, and the row
prints only the SHA, which is the part that is real.

Treat every surviving row as a lead to be READ, as at the moment it was
written - `docs/adr/README.md:65-72`, never `git blame`.

Usage:
    python3 docs/reviews/probe-204-orphaned-by-repoint.py

Exit 0 always: this REPORTS a candidate set for a human to read. It is
not a gate, and the ruling on what to do about an orphan has not been
made.
"""

from __future__ import annotations

import collections
import importlib.util
import pathlib
import re
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "probe204", pathlib.Path(__file__).with_name("probe-204-bare-citations.py")
)
assert _spec is not None and _spec.loader is not None
_p204 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_p204)

_QUAL = re.compile(
    r"(?P<name>[A-Za-z0-9_.\-/]+\.(?:md|py|yml|yaml|sh|toml))"
    r":(?P<a>\d+)(?:-(?P<b>\d+))?"
)

#: Words that mark a line as DISCUSSING a repoint rather than making a
#: citation. Reported, never filtered - see the docstring.
_DISCUSSION = ("rather than", "->", "narrowed", "widened", "was `:", "used to")


def _git(*a: str) -> str:
    return subprocess.run(
        ["git", *a], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    ).stdout


def repoint_history() -> dict[tuple[str, str, str], list[tuple[str, str]]]:
    """(file, cited-document, old-range) -> [(new-range, sha), ...]."""
    diff = _git(
        "log",
        "--format=%H",
        "-p",
        "--unified=0",
        "--no-color",
        "--",
        "*.md",
        "*.py",
        "*.sh",
        "*.yml",
    )
    out: dict[tuple[str, str, str], list[tuple[str, str]]] = collections.defaultdict(
        list
    )
    sha = ""
    cur = ""
    removed: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    added: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)

    def flush() -> None:
        # SORTED, because these are sets of str tuples and Python
        # randomises string hashing per process. Unsorted, two runs over
        # one tree disagreed on 99 output lines - see the docstring.
        for f in sorted(set(removed) | set(added)):
            for name, rng in sorted(removed[f] - added[f]):
                for n2, r2 in sorted(added[f] - removed[f]):
                    if n2 == name and r2 != rng:
                        out[(f, name, rng)].append((r2, sha))
        removed.clear()
        added.clear()

    for line in diff.splitlines():
        if re.fullmatch(r"[0-9a-f]{40}", line):
            flush()
            sha = line
        elif line.startswith("+++ b/"):
            cur = line[6:]
        elif line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("-"):
            for m in _QUAL.finditer(line):
                rng = m.group("a") + ("-" + m.group("b") if m.group("b") else "")
                removed[cur].add((m.group("name"), rng))
        elif line.startswith("+"):
            for m in _QUAL.finditer(line):
                rng = m.group("a") + ("-" + m.group("b") if m.group("b") else "")
                added[cur].add((m.group("name"), rng))
    flush()
    return out


def _same_document(anchored: str, cited: str) -> bool:
    """One document however it is spelled; the basename decides."""
    return anchored.rsplit("/", 1)[-1] == cited.rsplit("/", 1)[-1]


_BLOB: dict[tuple[str, str], str | None] = {}


def _blob(rev: str, path: str) -> str | None:
    """The file at a revision, or None if it did not exist there.

    None and "" are kept DISTINCT on purpose: a path that did not exist
    is not a file that was empty, and collapsing them would make TEST A
    pass vacuously on every file the repoint commit created.
    """
    key = (rev, path)
    if key not in _BLOB:
        r = subprocess.run(
            ["git", "show", f"{rev}:{path}"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        _BLOB[key] = r.stdout if r.returncode == 0 else None
    return _BLOB[key]


def coexisted(path: str, line: str, sha: str) -> bool:
    """TEST A: did this exact line stand in the file when the sweep ran?

    False means the line POSTDATES its own repoint, so the two spellings
    were never both in the file, so the sweep cannot have skipped it.
    """
    parent = _blob(sha + "^", path)
    return parent is not None and line.rstrip("\n") in parent


def disagrees_today(path: str, doc: str, old: str) -> bool:
    """TEST B: does the file cite this document at a DIFFERENT value?

    The self-contradiction is between the bare half and a QUALIFIED half
    that says something else. If a qualified mention carries the same
    value as the bare one, the halves agree and the instance is closed -
    which is what `be94bce` did to ADR-0017.
    """
    text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
    base = doc.rsplit("/", 1)[-1]
    quals = {
        m.group("a") + ("-" + m.group("b") if m.group("b") else "")
        for m in _QUAL.finditer(text)
        if m.group("name").rsplit("/", 1)[-1] == base
    }
    return bool(quals) and old not in quals


def main() -> int:
    hist = repoint_history()
    sites, _shapes, _excl = _p204.scan()
    anchors = _p204.anchor(sites)

    print(f"repointed (file, document, old-range) triples in history: {len(hist)}")
    print(f"bare-form citation sites: {len(sites)}\n")

    rows = []
    for s in sites:
        rung, detail = anchors[(s.path, s.lineno, s.start)]
        old = s.token[1:]
        for (f, doc, o), moves in hist.items():
            if f != s.path or o != old:
                continue
            if not any(_same_document(d.strip(), doc) for d in detail.split(",") if d):
                continue
            _new, sha = moves[-1]
            discusses = any(w in s.line for w in _DISCUSSION)
            rows.append((s, doc, old, sha, rung, detail, discusses))
            break

    # BOTH counts are printed. The file-level number is what this probe
    # reported before #208, and it is kept so the narrowing is visible
    # rather than asserted - a detector that shows only its tightened
    # figure cannot be checked against the one it replaced.
    kept, dropped_a, dropped_b = [], 0, 0
    for r in rows:
        s, doc, old, sha = r[0], r[1], r[2], r[3]
        if not coexisted(s.path, s.line, sha):
            dropped_a += 1
        elif not disagrees_today(s.path, doc, old):
            dropped_b += 1
        else:
            kept.append(r)

    print(f"file-level candidates (the pre-#208 figure): {len(rows)}")
    print(f"  -{dropped_a}  TEST A: the bare line POSTDATES its own repoint")
    print(f"  -{dropped_b}  TEST B: every qualified half AGREES with it today")
    print(f"\nORPHANED-BY-REPOINT leads to READ: {len(kept)}")

    live = [r for r in kept if not r[-1]]
    talk = [r for r in kept if r[-1]]
    print(f"  {len(live)}  a citation being MADE")
    print(
        f"  {len(talk)}  a line that DISCUSSES the old range (reported, not filtered)"
    )
    for label, group in (("MAKING A CITATION", live), ("DISCUSSING THE CHANGE", talk)):
        print(f"\n===== {label} =====")
        for s, doc, old, sha, rung, detail, _ in group:
            subject = _git("log", "-1", "--format=%s", sha).strip()
            print(f"\n{s.path}:{s.lineno}   anchor {rung} -> {detail}")
            print(f"    bare `:{old}` survives; `{doc}:{old}` was repointed away")
            print(f"    at {sha[:7]}  {subject[:76]}")
            print(f"    | {s.line.strip()[:118]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
