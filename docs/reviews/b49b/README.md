# B49b: how the 1608-line sweep was produced

Run in this order from the repository root, against the base tree:

    python3 docs/reviews/b49b/reflow-doc-lines.py $FILES   # $FILES = every file ruff reports W505 for
    python3 docs/reviews/b49b/split-long-summaries.py
    python3 docs/reviews/b49b/apply-short-summaries.py

1. **`reflow-doc-lines.py`** rewraps comment runs and docstring bodies to 72,
   leaving fenced blocks, tables, bullets, Google sections, deeper-indented
   listings and `# -----` dividers structurally intact (dividers are shortened
   to 72, not rewrapped). Short `` `code spans` `` are made unbreakable so a
   wrap never splits one. Every file is `ast.parse`d before it is written.
   1608 -> 179.

2. **`split-long-summaries.py`** fixes over-long docstring SUMMARY lines that
   carry more than one sentence, by moving the later sentences into the body.
   A summary cannot simply be wrapped: `D205` requires the summary to be one
   line. 179 -> 149.

3. **`apply-short-summaries.py`** applies the 149 hand-authored summaries in
   `short-summaries.json`. Each object is `{path, qualname, summary,
   body?}`. **The anchor is the qualified name, not a line number** - the
   first draft of this table was keyed by line number and every anchor shifted
   the moment step 1's wrapping changed by one character.

`docs/reviews/classify-w505.py` exits 1 with `POSITIVE CONTROL FAILED` against
a swept tree, by design: it refuses to report a split it did not measure.
