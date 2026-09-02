import importlib.util
spec = importlib.util.spec_from_file_location(
    "p204", "docs/reviews/probe-204-bare-citations.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sites, shapes, excl = m.scan()
anch = m.anchor(sites)
for s in sites:
    if not s.path.startswith("docs/adr/"):
        continue
    v, d = anch[(s.path, s.lineno, s.start)]
    print(f"{s.path.split('/')[-1][:34]:34}:{s.lineno:<4} {s.token:12} {v:20} {d}")
    print(f"      | {s.line.strip()[:150]}")
