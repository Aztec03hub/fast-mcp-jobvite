import pathlib, subprocess, sys
sys.path.insert(0, "docs/reviews")
import importlib.util
spec = importlib.util.spec_from_file_location("x", "docs/reviews/check-cross-references.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

root = pathlib.Path(".").resolve()
tracked = subprocess.run(["git","ls-files","*.md"],capture_output=True,text=True,check=True).stdout.split()
EXCL_DIRS = ("docs/worklogs/","docs/plans/","docs/reviews/","docs/briefs/")
pop = [p for p in tracked if not p.startswith(EXCL_DIRS) and p != "CHANGELOG.md"]
total=0; files=0
for p in sorted(pop):
    text = (root/p).read_text()
    ref = "docs/DESIGN.md" if p.startswith("docs/adr/") else None
    try:
        miss = m.unresolved(text, ref, p)
    except ValueError as e:
        print(f"SKIP {p}: {e}")
        continue
    if miss:
        files+=1; total+=len(miss)
        print(f"\n=== {p}  ({len(miss)} unresolved) ===")
        lines = text.splitlines()
        for ln, r in miss:
            print(f"{p}:{ln}: §{r}  |  {lines[ln-1].strip()[:200]}")
print(f"\nTOTAL: {total} unresolved across {files} files; population {len(pop)} files")
