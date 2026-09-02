# ADR-0034: DESIGN.md's ADR count is DELETED, not corrected, and "all" was the worse half

**Status:** Accepted (orchestrator, 2026-09-02)
**Type:** Correction to a count that is false about its own subject

> `DESIGN.md:2063` and `:2067` say **"all eleven ADRs"** and **"eleven ADRs exist"**. There are
> **33**. And the count is the smaller error: **"all"** is false independently of it, because the
> sentence is describing ONE OF TWO JOBS an ADR does here and the same paragraph names the other
> job three lines below. Replacing 11 with 33 would have kept the false claim and made it larger.

## Context

### The finding, and where it came from

`suborch-170` measured every number-beside-a-plural in the repository by kind: **485 tracked files,
20,566 adjacencies, 6,762 with an enumerable noun, 4,401 inside dated records, 2,361 live and
checkable across 298 files.** These two sites came out of that sweep as its only HIGH in a frozen
file.

**This is #166's own finding, recurring in the document the two files it fixed both describe.**
#166 corrected `docs/README.md:22` ("Eleven decision records") and `docs/adr/README.md:7` ("eleven
ADRs") and ruled: **DELETE the number, do not replace 11 with 33.** It never reached `DESIGN.md`,
which says it twice, and which nobody could have fixed in passing because the file is frozen.

### What the passage actually claims

`DESIGN.md:2061-2070` distinguishes two jobs an ADR does in this project:

1. recording a deviation from a `priority: required` standard - *"This is the job **all eleven
   ADRs** below do"*;
2. being the sole instrument that may change a frozen `DESIGN.md`.

The paragraph is RIGHT about the distinction and it is the reason the distinction is written down
at all. It is wrong about the population doing job 1.

### Measured by KIND, not by a grep over a word

Every ADR carries a `**Type:**` line, so the population can be partitioned without guessing:

    17  Design change
    14  Deviation
     1  Standards deviation
     1  Correction to a contract statement ...
    --
    33  total

**Fifteen of thirty-three do job 1.** Seventeen do job 2. A word-grep would have said 16 - `deviat`
appears in ADRs that merely discuss the concept - which is why the `Type:` line is the instrument
and the grep is not.

Six of the seventeen are unambiguous, and reading them is what settles it rather than the tally:
**ADR-0019** (a citation to a `§5.4` that does not exist), **ADR-0021** (`approval_state`'s
mechanism required by two rows and defined nowhere), **ADR-0028** (a closed set naming a `sampling`
path this design does not have), **ADR-0029** (a body limit placed at a middleware this design does
not have), **ADR-0031** (no registry row for a refused approval), **ADR-0033** (a published
vocabulary). None of them records a standards deviation. All of them change the design.

## Decision

**DELETE both numbers and repair the universal.** The passage keeps its two-job structure, which is
its value, and stops asserting a population.

`:2063` becomes: *"This is the job the **Deviation** ADRs below do"* - the class named by their own
`Type:` line, which cannot go stale as the set grows.

`:2067` becomes a statement about the mechanism rather than a headcount: *"That is why deviation
ADRs exist against a document that is not frozen..."*.

**No number replaces either one.** #166 ruled that on this exact sentence in two other files and the
ruling holds here: a corrected count is a count that will be wrong again, and this is the third and
fourth site of one claim.

## Consequences

- `docs/DESIGN.md` changes, so **the freeze SHA is re-derived** and `docs/DESIGN-FREEZE.txt` is
  updated in the same commit. That is what this ADR exists to authorise.
- The two-job distinction is preserved verbatim. **This ADR changes no design decision**, which is
  why it is a correction and not a Design change.
- A reader who wants the count runs `ls docs/adr/[0-9]*.md | wc -l`, or partitions it with the
  `Type:` line. The document no longer offers a stale answer to a question a command answers.

## What this ADR does NOT do

- It does not rule on whether `Type: Design change` and `Type: Deviation` are the right two classes.
  They are the classes in use; naming them is not endorsing them.
- It does not sweep the other 2,361 live candidates `suborch-170` measured. Those are reported in
  `docs/reviews/FINDINGS-170-retyped-counts.md`, in three outcome classes plus a fourth that report
  identified - **a historical justification inside a live file**, where the digit is evidence for a
  decision already taken and the remedy is tense rather than arithmetic.
- It does not touch `pyproject.toml:345` or the three LOW sites, which are that fourth class.
