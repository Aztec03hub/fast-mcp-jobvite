# BRIEF #211 + #213: a merge message stated backwards, and a refusal argued backwards

Read `docs/briefs/PREAMBLE.md` IN FULL first. It is the canon; this file is only the work.

**Worktree:** your own, off `d2159e7` (main). Branch `fix/211-213-record-and-counterfactual`.
**Read the findings first:** `git show 1045edb:docs/reviews/REVIEW-R21.md` (branch `review/r21`).

Two tasks. **#213 is a MEASUREMENT ONLY - the ruling is mine and you must not make it.**

## #211 (M1) - the merge message describes the two versions backwards

Merge `7197271`. `review-r21` verified that **nothing of `410e370`'s work was lost**:
`git diff 410e370 7197271 -- <WORKLOG-199 path>` is empty, all 46 lines landed. The RESOLUTION is
right - it keeps the class statement the revert dropped.

**The MESSAGE has the two versions backwards.** `410e370`'s `BRIEF-199:67` names NONE of the three
reports; the KEPT resolution names two (`WORKLOG-187-floor-container.md`, `REVIEW-R20.md`). So the
"green because those two files happen to exist" property belongs to the side that was KEPT, not
the side that was refused. The record states the trade the wrong way round.

**A merge commit's message cannot be rewritten** - this project has ruled that history is not
rewritten (`0291bac`, CONTRIBUTING). So the remedy is a correction that a reader of that merge
will actually encounter. Decide WHERE that is and argue it: the worklog, the brief, or a record
document. A correction filed where nobody reading the merge will look is not a correction.

Verify the whole finding yourself before you write anything - including the empty diff.

## #213 (M3) - the syntax-split refusal is argued backwards by its own numbers

The citation-vs-quotation ruling (in `check-brief-report-references.py`'s docstring) refused a
syntax split. `review-r21` measured that the stated REASON is the opposite of the numbers:

- **Six names cited BOTH ways are still caught by their path form**, so the split drops none of
  them. That measurement is evidence FOR the split's safety, and the ruling cites it as evidence
  against.
- The split would drop **2 bare-only names**: one tracked, one the in-flight forward reference the
  ruling exists to tolerate. **Zero live detections lost today.**

The conclusion may still be right, on the residual hazard. The stated reason is not.

**YOUR JOB IS THE COUNTERFACTUAL, NOT THE RULING.** Build and run the measurement that would
actually decide it: what does the gate detect today, what would the split-form gate detect, over
the same population - and what is the residual class that only the bare form catches, named
concretely rather than described. Write it to `docs/reviews/FINDINGS-213-syntax-split.md` as a
RUNNABLE probe plus its output, not as prose about a measurement. Prose about a measurement decays
into a claim about one.

**Then stop and report. Do not edit the docstring. Do not rule.** `review-r21` filed no task for
the ruling for exactly this reason.

## Deliverable

Commits for #211's correction and #213's probe+findings. Gates green, exit codes on their OWN
lines, no `&& echo OK`. Then the `git merge --ff-only` command for me.

## Where I think I am wrong

- I have not verified the empty diff on `7197271`, nor the six-both-ways / two-bare-only split.
  Both are `review-r21`'s numbers. Re-derive them; a disagreement is the most valuable thing you
  can bring back.
- I am least sure that a correction document is the right remedy for #211 at all. If you conclude
  the merge message should simply be left as a wrong record with the truth living in the worklog,
  argue it - that may well be right and I would rather have the argument than a document nobody
  reads.
