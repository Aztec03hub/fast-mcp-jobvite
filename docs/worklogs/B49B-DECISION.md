# B49b decided: comply with the 72-character clause in full, no exemptions

**Date:** 2026-08-28. **Decided by:** team lead, under standing authority.
**Obligation:** `backend/python.md:36` - *"For comments and docstrings: **72 characters**"* - in a
document whose frontmatter is `priority: required`. Tracked as the second half of **B49**; the code
half (`line-length = 88`, `python.md:35`) has been met since U0.

## The decision

1. **Comply.** No ADR, no narrowing, no exemption list.
2. **Enforce it** with ruff's `W505` (`doc-line-too-long`) and
   `[tool.ruff.lint.pycodestyle] max-doc-length = 72`. The clause has been unenforced since U0,
   which is the entire reason the violation count grows.
3. **Enable the rule in the same commit as the sweep**, so the gate is never knowingly red.
4. **Sequence it after U1 and draft 8 land.** Ten of the sixteen affected files are ones `impl-u1-boot`
   may touch, and a 367-line reflow landing under a live agent is the
   parallel-work-voids-itself failure this project has already paid for.

## Why this was not obvious, and what changed it

The recorded figure was **"135 lines across 11 files"**. That number was wrong, and it was wrong in
the direction that made the decision look cheap. The real figure, measured with the rule that
actually defines the obligation:

```
uv run --frozen ruff check . --select W505 \
    --config 'lint.pycodestyle.max-doc-length = 72'
  -> 367 violations across 16 files
```

**The reason to hesitate was never the count.** It was that these docstrings are deliberately
prose-heavy, carrying incident history and reasoning, and W505 counts *every* line inside a
docstring - fenced code blocks, markdown tables, pasted transcript output. None of those can be
rewrapped: wrapping a fenced line breaks the code, and wrapping a table destroys the alignment that
makes it readable. If a large share of the 367 were structural, compliance would mean mangling the
artifacts, and **that** would have been a real argument for a scoped ADR.

So the split was measured rather than guessed, with `docs/reviews/classify-w505.py`:

| Kind | Count | Share |
|---|---|---|
| docstring, flowing prose | 278 | 76% |
| comment, flowing prose | 71 | 19% |
| comment, single unbreakable token | 18 | 5% |
| **docstring or comment inside a fenced block** | **0** | - |
| **markdown table row** | **0** | - |

**The argument for an ADR evaporated on contact with the measurement.** There is no structural
content over 72 characters anywhere in this repository. Everything is flowing prose, and flowing
prose at 72 characters is exactly what PEP 8's rule is for.

## Two places this measurement could have lied, and what was done about each

**A zero is the shape of result this project has learned to distrust**, because a broken instrument
and a clean tree produce the same output.

1. **"Zero fenced blocks, zero tables" could have been a classifier whose branches never fire.**
   Controlled with a fixture containing one deliberately-overlong line of each kind. All five
   branches fired and labelled correctly, so the two zeros are a real absence rather than a claim
   about my instrument. The classifier also fails loudly if ruff reports no W505 at all, so it
   cannot pass vacuously against a clean tree.
2. **The 18 "unbreakable token" lines were labelled, not read.** Reading them showed they are not
   the URLs and long paths the branch was written for - **all 18 are 79-character `# -----` section
   dividers**, which shorten to 72 in one pass. So even the 5% needs no `noqa`, and the exemption
   list this decision might have carried is empty.

**That second check is the one that changed the decision's shape**, and it cost one command. The
label was accurate and the conclusion drawn from it would have been wrong.

## What the sweep must do

- Reflow **349** flowing-prose lines to 72.
- Shorten **18** dash dividers from 79 to 72.
- Add `"W505"` to the ruff select list and `max-doc-length = 72` under
  `[tool.ruff.lint.pycodestyle]`, with a comment naming B49b.
- Update `docs/OBLIGATIONS.md`'s B49 row from *"Code half only"* to met in full, and
  `pyproject.toml:141`'s inline comment likewise.

**Do not reflow by line number.** A previous attempt at exactly this broke four test files with
unterminated string literals, because an edit keyed on a line number lands in the middle of a
string literal that a later edit has already moved. **Validate every file with `ast.parse` before
writing it**, prefer shortening a sentence to wrapping it, and run the full suite afterwards - a
docstring is not syntax-checked by anything else.

## What this decision does NOT settle

**Whether 367 is the final count.** It grows with every file written, and it grew by 23 during the
hour this was measured, from `tests/test_workflow_pins.py` - a file written by the same person
making this decision, after the measurement began. That is not an aside: it is the direct evidence
that the clause is unenforced, and the reason enforcement ships with the sweep rather than after it.
