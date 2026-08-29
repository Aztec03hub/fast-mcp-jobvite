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

## Why the sequencing matters, because it changed on re-measurement

The decision was taken against **367** violations. There are now **1343** - U1, U3 and U4 added
roughly 325 each. **Ten more units remain.** Deferring the sweep costs roughly 3000 further lines,
and enabling `W505` is the only thing that stops the growth. That is why this runs BEFORE U5 rather
than after it, and it is the whole reason your task is ahead of a feature in the queue.

**Verify that 1343 yourself before you start** and put your own number in the report. It is my count,
it is hours old, and a merge has landed since.

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

**This touches nearly every documentation file in the tree, and `DESIGN.md:N` citations are counted
in lines.** 841 such citations exist across 81 files, and a five-line insertion once moved 723 of
them.

**`docs/DESIGN.md` is frozen - reflowing it is a design edit and you may not do it.** If `W505` fires
inside `DESIGN.md`, the answer is an exemption for that file plus a line in your report, **not** an
edit and **not** an ADR. Say clearly in the report how many violations live there.

For every other doc you reflow, run `docs/reviews/check-design-citations.py --since <your base sha>`
afterwards and repoint what moved, **by parsing its output**. Then run
`docs/reviews/check-cross-references.py` - it validates the `Section n.m` pointers, which reflowing
can also disturb.

## Gates specific to you

Beyond the standard set: `check-obligations.py`, `check-design-citations.py`,
`check-cross-references.py`, and `check-plan-measurements.py` all read documents by line and are the
ones your change is most likely to break. Run each, by exit code, and quote the output.

## In the report

The count you measured, the value you set, how many violations were in `DESIGN.md` and what you did
about them, the exemption list with a defence per entry or the word "empty", every checker's verbatim
output, and the final passed-count.
