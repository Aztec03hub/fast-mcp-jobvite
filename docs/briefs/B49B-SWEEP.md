# B49b - comply with the doc-line-length rule, and enable it in the same commit

**Read `docs/briefs/PREAMBLE.md` first.** It carries the task tools, isolation, evidence standards,
gates and delivery rules, and they are not repeated here.

Your agent name is `b49b-sweep`. Your branch is `chore/b49b-line-length`. Your report goes to
`docs/worklogs/B49B-SWEEP-REPORT.md`.

## The decision is already made. You are implementing it, not re-opening it.

`docs/worklogs/B49B-DECISION.md` holds it: **comply in full, and enable the rule in the SAME commit
as the sweep.** Read it before you start. Do not re-argue it - if you find something that genuinely
invalidates it, that is a report, not a unilateral change of course.

The obligation is B49b in `docs/OBLIGATIONS.md`. Read the clause it cites, at its source, and quote
it in your report.

## Where the violations actually are, and a correction that matters

**MEASURED at the 72-char threshold, whose authority is `backend/python.md:36`** - *"For comments
and docstrings: **72 characters**"*, `priority: required`:

```
1654 errors:  tests/ 907    src/ 638    scripts/ 109    docs/ ZERO
```

**W505 is `doc-line-too-long` and it flags DOCSTRINGS IN PYTHON FILES.** An earlier revision of this
brief said the sweep "touches nearly every documentation file in the tree" and devoted a section to
repointing `DESIGN.md:N` citations. **That was wrong and is deleted.** Markdown is not linted by
ruff, `docs/` contributes zero violations, and `DESIGN.md` is not in scope at all - so there is
nothing there to exempt and no citations to repoint.

**A second claim of mine in this brief was also wrong, and the agent caught it.** I wrote that
`pyproject.toml:185` "names" the 72-char threshold. That line sets `line-length = 88` - the CODE half,
`python.md:35` - and merely mentioned 72 in a comment pointing at this task. **Before the sweep
commit, no key in `pyproject.toml` set 72 at all**, which is exactly why the clause was unenforced
and why the count grew unchecked. `W505` is INERT without `max-doc-length`, even with `"W"` selected.
The key that enables it now lives at `pyproject.toml:227`.

**The real consequence of that error was a collision.** The sweep lands in exactly the files a
concurrent agent was editing, and both were dispatched believing their trees were disjoint. **Check
`git worktree list` and ask before touching `src/` or `tests/`.**

## Why the sequencing matters, because it changed on re-measurement

The decision was taken against **367** violations. **Verify the current count yourself before you
start and put your own number in the report** - my successive figures have been 367, then 1343, then
1654, each measured differently, and at least two of them were wrong when written.

The count grows with every unit and **ten more units remain**, so deferring costs thousands of
further lines. Enabling `W505` is the only thing that stops the growth. That is why this sits ahead
of a feature in the queue.

## What to do

1. **Enable the rule** in `pyproject.toml` - `W505` with `max-doc-length`. Match the value to the
   line length the project already uses; do not invent a second number.
2. **Sweep every violation.** Reflow prose. Do not solve a violation by deleting the sentence.
3. **The exemption list stays empty unless you can defend an entry.** All 81 lines a previous pass
   classified as "unbreakable" were checked and every one was a divider - the classifier's label was
   not trusted, and neither should yours be. If you add an exemption, name the line and say why it
   cannot break.
4. **One commit** with the rule and the sweep together. A sweep without the rule regrows.

## The trap in this specific task

**A docstring is not a comment, and reflowing one can change behaviour.** Two shapes to handle with
care rather than with `fmt`:

- **A docstring that a test asserts on.** This project has tests that read module docstrings and
  harnesses whose anchors are docstring text. `str.replace` in a harness silently no-ops when its
  anchor moves, which turns a control into a green that tests nothing.
- **The first line.** Ruff's `D415` requires it to end in `.`, `?` or `!`, and `D400`/`D205` govern
  the blank line after it. A reflow that pushes a word onto the summary line can trip these, and the
  cheapest fix is to delete words - which is how a reflow quietly becomes a rewrite.

**Do not solve a violation by deleting the sentence.** The prose in this codebase carries the reason
a thing exists, and several comments are the only record of a defect that was measured once.

## Gates specific to you

Beyond the standard set, the ones a mass docstring edit is most likely to break:

- **The suite-size floor**, `scripts/check-suite-floor.sh`, wired into `ci.yml`. A reflow must not
  change the test count, so this is a free check on your sweep - if it goes red, you removed a test.
- **Every mutation and amputation harness in `scripts/`**, because their anchors are source text.
  Run all of them, by exit code, and treat a `DID NOT LAND` or `ANCHOR MISSING` line as red even
  though the harness may still exit 0 on it.
- `check-obligations.py`. **No longer for the reason this brief first gave** - anchors carried
  `file:line` when it was written and no longer do (task #6), precisely because a reflow like
  this one kept moving them. It still matters because an anchor's SUBJECT is source text, and a
  reflow can break a subject across two lines.

## In the report

The count you measured and how, the threshold and the pyproject key you set, the exemption list with
a defence per entry or the word "empty", every harness's verbatim output, and the final
passed-count - which must not have moved.
