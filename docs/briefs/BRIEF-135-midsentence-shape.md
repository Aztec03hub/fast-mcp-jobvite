# BRIEF #135 — the mid-sentence citation shape: MEASURE, do not sweep

## §A — Read the canon FIRST

**Read `docs/briefs/PREAMBLE.md` in full first, and follow it.** Read the
design at the freeze, never the working tree:

    git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md

Then read, in order:

1. `docs/reviews/REPORT-134-citation-rate.md` — in particular
   *"The near-miss class"* and *"My view on whether this justifies a full
   sweep"*. This brief exists because of it.
2. `docs/reviews/check-design-citation-shape.py` — the four existing
   detectors, and what each decides.
3. `docs/reviews/sample-134-citations.py` — the sampler, seed 134.

## §B — The shape

Every existing detector decides *"this range CANNOT be anyone's
subject"*: out of bounds, entirely blank, fence-or-separator only,
starts-blank, ends-blank.

**None sees a range whose first line does not BEGIN a sentence, or whose
last line does not END one.** That is decidable without knowing the
claim, and it is a strict superset of the blank-start and blank-end
shapes two of those detectors already implement.

It matters because it is the population the wrong-paragraph class
(#114, #132, #133) is drawn from. A range already cut mid-sentence is one
repoint away from losing its claim: #126's F3 is the proof — a clean
`end - 1` on `906-907` would have produced `DESIGN.md:906`, an unrelated
sentence that resolves and passes both citation gates forever.

## §C — Job 1: MEASURE THE BACKLOG. Do not fix anything.

Write the detector, run it over the whole corpus, and **report the
count**. That is the deliverable.

`4/40` extrapolates to roughly 90 sites, but **that number is a guess and
the first thing to replace with a real one.** Report the actual count,
the per-file distribution, and the first ~15 instances with enough
context to judge them.

**Do NOT repoint anything, and do NOT wire the detector.** #125's
discipline, which this project has now refused to break four times:
measure the backlog, fix it, and wire the gate only once it is green. A
gate that lands red is one people learn to ignore.

Note that #134 already read four instances and suggested a range for
each; those are in the task and the report. **Treat them as hypotheses to
check, not as answers** — two of #126's mechanical fixes would have been
wrong.

## §D — Job 2: test the enrichment hypothesis, which corrects ME

BRIEF #134 asserted that ending on a blank line and citing the wrong
paragraph are **INDEPENDENT** properties, and projected ~35 wrong
citations from #126's 2/47. **The report argues that premise is false**:
#126's F1–F4 are all paragraph-boundary miscounts by the citing author,
so the blank-ended population is *enriched* for exactly the defect being
extrapolated. If so, 2/47 was never a base rate.

Test it: sample from the **complement** of the blank-ended population and
compare the rates. Record the seed. Report both rates with numerators and
denominators, and say plainly whether the difference is large enough to
conclude anything at these sample sizes — an honest *"too small to
separate"* is a real answer and is better than a number with false
confidence.

**I wrote the premise this job exists to test. If it is wrong, say so
directly.** The previous three agents each corrected me on something and
each was right.

## §E — Constraints

- Branch `review/midsentence-shape` off current `main`.
- **Do not merge, do not push.** I merge and push, always.
- **Do not edit any citation.** This is measurement.
- No `Co-Authored-By` or "Generated with" trailer.
- Do not `git stash` — other agents are live on this tree.
- `git commit -F` with a **quoted** heredoc (`<<'MSG'`).
- A new file in `docs/reviews/` named `check-*` enters the wired-checker
  container and must then be wired or exempted. While the backlog is
  unknown, name the detector `probe-*` or `sample-*` instead — and say in
  its docstring that it is deliberately not a gate yet, and why.
- Cite `file:line` only from `grep -n` or a numbered Read. Never count
  offsets inside a `sed -n X,Yp` window.
- Report to `docs/reviews/REPORT-135-midsentence-shape.md`.

## §F — Report back

`SendMessage` to `team-lead`: the backlog count and its distribution, the
enrichment result with both rates and seeds, your recommendation on
whether a sweep is justified, and anything you could not settle. If the
detector's own definition of "sentence" is doing questionable work —
abbreviations, code spans, list items, headings — say so and show what it
does at those edges rather than reporting a clean number over a
definition nobody has inspected.
