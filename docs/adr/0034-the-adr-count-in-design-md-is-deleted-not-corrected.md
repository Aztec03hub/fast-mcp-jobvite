# ADR-0034: DESIGN.md's ADR count is DELETED, not corrected, and "all" was the worse half

**Status:** Accepted (orchestrator, 2026-09-02)
**Type:** Design change

> `DESIGN.md:2063` and `:2067` say **"all eleven ADRs"** and **"eleven ADRs exist"**. Eleven is
> not the population and has not been for a long time; **this ADR deliberately does not say what
> the population is**, because a corrected count is a count that goes stale, and
> `ls docs/adr/[0-9]*.md | wc -l` answers it at any moment.
>
> **THIS BLOCKQUOTE HAS BEEN WRONG TWICE, IN THE ADR THAT FORBIDS THE MISTAKE.** It said **33** at
> acceptance; R19-N2 read it against the census eight lines below and corrected it to **34**; that
> was false one commit later when ADR-0035 landed. A count written inside the record that rules
> counts out is the strongest evidence the ruling is right.
>
> And the count is the smaller error: **"all"** is false independently of it, because the sentence
> is describing ONE OF TWO JOBS an ADR does here and the same paragraph names the other job three
> lines below. Replacing eleven with a larger number would have kept the false claim and made it
> larger.

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

Every ADR carries a `**Type:**` line, so the population can be partitioned without guessing. The
partition AT ACCEPTANCE, recorded as the evidence for this ruling and NOT as a live figure - the
set has grown since, and the command below is the live answer:

    19  Design change
    15  Deviation
    --
    34  total   (this ADR included)

    grep -h '^\*\*Type:\*\*' docs/adr/[0-9]*.md | sort | uniq -c

**A MINORITY OF ADRs DO JOB 1** - fifteen of thirty-four when this was written. A word-grep would
have said 16, because `deviat` appears in ADRs that merely discuss the concept, which is why the
`Type:` line is the instrument and the grep is not.

**THAT TABLE IS NOT WHAT I FIRST WROTE, AND THE DIFFERENCE IS A DEFECT THIS ADR CAUSED.** The census
at acceptance read `17 / 14 / 1 Standards deviation / 1 Correction to a contract statement...`, and
this ADR added a fifth spelling of its own. Naming `Type: Deviation` in a FROZEN document made that
field load-bearing, and **`ADR-0023` - a real deviation from `devops/bash.md:36-41` - was spelled
`Standards deviation` and so fell outside the very selector written to include it.** The sentence
written to stop a false claim about ADRs was false about one ADR, by one word. Found by
`suborch-170` verifying the fix rather than accepting it.

The three outliers are normalised to the two values `docs/adr/README.md:12` already publishes, in
the commit that carries this paragraph: `ADR-0023` to `Deviation` (its body argues exactly that),
`ADR-0022` and this ADR to `Design change` (a correction to the design IS a change to it). The
published vocabulary is unchanged; the ADRs now conform to it.

Six of the `Design change` ADRs are unambiguous, and reading them is what settles it rather than
the tally:
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
- The two-job distinction is preserved verbatim. **This ADR changes no design decision** - it
  removes a false claim - but it is typed `Design change` rather than inventing a third value,
  because a correction to the design is a change to it and the vocabulary is published.
- **THE SELECTOR IS NOW LOAD-BEARING.** A frozen document names `Type: Deviation`, so a new ADR
  spelling that field a fifth way silently falls outside a sentence in `DESIGN.md`. Whether that
  deserves a checker is NOT ruled here: a gate over a vocabulary is worth having only once someone
  has decided the vocabulary is final, and `Both` is published and used by nobody.
- A reader who wants the count runs `ls docs/adr/[0-9]*.md | wc -l`, or partitions it with the
  `Type:` line. The document no longer offers a stale answer to a question a command answers.

## What this ADR does NOT do

- It does not rule on whether `Type: Design change` and `Type: Deviation` are the right two classes,
  nor on `Both`, which `docs/adr/README.md:12` publishes and no ADR uses. They are the classes in
  use; naming them is not endorsing them, and normalising three outliers onto them is conforming to
  a published list rather than choosing it.
- It does not sweep the other 2,361 live candidates `suborch-170` measured. Those are reported in
  `docs/reviews/FINDINGS-170-retyped-counts.md`, in three outcome classes plus a fourth that report
  identified - **a historical justification inside a live file**, where the digit is evidence for a
  decision already taken and the remedy is tense rather than arithmetic.
- It does not touch `pyproject.toml:345` or the three LOW sites, which are that fourth class.
