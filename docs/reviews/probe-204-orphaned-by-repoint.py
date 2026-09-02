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

## THIS PRODUCES CANDIDATES, NOT FINDINGS, AND HERE IS THE WEAKNESS

**The pairing is at FILE level, not at LINE level, and that is not
tight enough to publish a count from.** The probe asks "was this range
repointed anywhere in this file, and does a bare form of the old value
still stand anywhere in this file". Those two anywheres need not be the
same citation.

Measured: it reported six sites in `src/` and `tests/` - continuation
comments like

    # U7 - RESILIENCE (DESIGN.md:354-370, :373-375, :617).

`git log -S` on that exact comment returns ONE commit, its own
introduction. **The line has never been repointed at all**, in either
half, so the two spellings do not disagree and it is not an orphan. It
matched only because `DESIGN.md:373-375` was repointed ELSEWHERE in the
same file. All six fall the same way.

**So the `->` destination this probe prints is not evidence
either**: when one commit repoints several ranges in one file, it
pairs an arbitrary removal with an arbitrary addition.

**One instance is CONFIRMED, and it was confirmed by reading a diff, not
by this probe.** `docs/adr/0017-...` at `02245b1` carried
`DESIGN.md:489-490` at `:15` and bare `:489-490` at `:66`; `b0e86b8`
changed the first to `:495-496` and left the second. Both lines are in
the file today. That is a real self-contradiction inside one document.

Treat every other row as a lead to be read, and read it with
`git log -S '<the exact line>' -- <file>`.

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
        for f in set(removed) | set(added):
            for name, rng in removed[f] - added[f]:
                for n2, r2 in added[f] - removed[f]:
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
            new, sha = moves[-1]
            discusses = any(w in s.line for w in _DISCUSSION)
            rows.append((s, doc, old, new, sha, rung, detail, discusses))
            break

    live = [r for r in rows if not r[-1]]
    talk = [r for r in rows if r[-1]]
    print(f"ORPHANED-BY-REPOINT candidates: {len(rows)}")
    print(f"  {len(live)}  a citation being MADE")
    print(
        f"  {len(talk)}  a line that DISCUSSES the old range (reported, not filtered)"
    )
    for label, group in (("MAKING A CITATION", live), ("DISCUSSING THE CHANGE", talk)):
        print(f"\n===== {label} =====")
        for s, doc, old, new, sha, rung, detail, _ in group:
            subject = _git("log", "-1", "--format=%s", sha).strip()
            print(f"\n{s.path}:{s.lineno}   anchor {rung} -> {detail}")
            print(f"    bare `:{old}` survives; `{doc}:{old}` -> `:{new}`")
            print(f"    at {sha[:7]}  {subject[:76]}")
            print(f"    | {s.line.strip()[:118]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
