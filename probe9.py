"""ORPHANED-BY-REPOINT detector.

Replay every commit that changed a QUALIFIED `<file>.md:N` citation in a
file, and ask: does the OLD number still stand in that same file today,
in BARE form? If so, the repoint moved one spelling of a citation and
left the other behind - and the two now disagree inside one document.
"""

import collections
import pathlib
import re
import subprocess

QUAL = re.compile(
    r"(?P<name>[A-Za-z0-9_.\-/]+\.(?:md|py|yml|yaml|sh|toml))"
    r":(?P<a>\d+)(?:-(?P<b>\d+))?"
)
BARE = re.compile(r"(?<![A-Za-z0-9_./\\-]):(\d+)(?:-(\d+))?\b")


def git(*a: str) -> str:
    return subprocess.run(
        ["git", *a], capture_output=True, text=True, check=True
    ).stdout


# every commit touching a tracked .md/.py/.sh, newest last
shas = git("log", "--format=%H", "--reverse").split()
print("commits scanned:", len(shas))

# old-range -> (new-range, sha, file) for every repoint we can see
repoints: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)

diff = git(
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
sha = ""
cur_file = ""
removed: dict[str, set[str]] = collections.defaultdict(set)
added: dict[str, set[str]] = collections.defaultdict(set)


def flush() -> None:
    for f in set(removed) | set(added):
        gone = removed[f] - added[f]
        came = added[f] - removed[f]
        for g in gone:
            name, rng = g.split("\x00")
            for c in came:
                n2, r2 = c.split("\x00")
                if n2 == name and r2 != rng:
                    repoints[(f, rng)].append((r2, sha))
    removed.clear()
    added.clear()


for line in diff.splitlines():
    if re.fullmatch(r"[0-9a-f]{40}", line):
        flush()
        sha = line
        continue
    if line.startswith("+++ b/"):
        cur_file = line[6:]
        continue
    if line.startswith("--- ") or line.startswith("+++ "):
        continue
    if line.startswith("-") and not line.startswith("---"):
        for m in QUAL.finditer(line):
            rng = m.group("a") + ("-" + m.group("b") if m.group("b") else "")
            removed[cur_file].add(f"{m.group('name')}\x00{rng}")
    elif line.startswith("+") and not line.startswith("+++"):
        for m in QUAL.finditer(line):
            rng = m.group("a") + ("-" + m.group("b") if m.group("b") else "")
            added[cur_file].add(f"{m.group('name')}\x00{rng}")
flush()

print("repointed (file, old-range) pairs seen in history:", len(repoints))

# now: which of those OLD ranges still stand as a BARE form in that file?
orphans = []
for (f, old), moves in sorted(repoints.items()):
    p = pathlib.Path(f)
    if not p.exists():
        continue
    try:
        text = p.read_text()
    except (UnicodeDecodeError, OSError):
        continue
    for i, line in enumerate(text.splitlines(), 1):
        for m in BARE.finditer(line):
            if m.group(0) == ":" + old:
                orphans.append((f, i, old, moves[-1][0], moves[-1][1], line.strip()))

print(f"\nORPHANED-BY-REPOINT candidates: {len(orphans)}")
for f, i, old, new, sha, line in orphans:
    print(f"\n{f}:{i}")
    print(f"    bare `:{old}` survives; the qualified form went :{old} -> :{new}")
    print(f"    at {sha[:7]}  {git('log', '-1', '--format=%s', sha).strip()[:80]}")
    print(f"    | {line[:120]}")
