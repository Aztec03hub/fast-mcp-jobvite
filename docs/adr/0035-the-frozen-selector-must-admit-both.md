# ADR-0035: the frozen selector must admit `Both`, and the `0012 onward` boundary is deleted

**Status:** Accepted (orchestrator, 2026-09-02)
**Type:** Design change

> ADR-0034 replaced a stale count in `DESIGN.md` §13 with a SELECTOR - `Type: Deviation`. Eleven
> lines below, **the same frozen paragraph publishes `Both` as a legal value for an ADR doing that
> same job**, and the selector cannot match it. The first ADR ever typed `Both` would silently
> falsify a frozen sentence, and only an ADR could repair it. Found by `review-r19` verifying
> ADR-0034 rather than accepting it.

## Context

### This is ADR-0034's defect, one column over, and it is the second time on the same paragraph

ADR-0034 deleted "all eleven ADRs" correctly. What it did not do was **derive the selector it put
in the count's place.** `d29937f` then found one half of that - `ADR-0023` spelled `Standards
deviation`, outside the selector - and normalised three outliers onto the published vocabulary.

**It stopped one step short.** `d29937f` framed the residue as *"should there be a checker?"* and
left it. The sharper statement, which `review-r19` supplied, is that **the frozen selector is
incomplete against the frozen document's own vocabulary** - not a question about tooling but a
sentence that is already wrong about a case nobody has written yet.

### The two sentences, read at the freeze

`DESIGN.md:2064` (the selector ADR-0034 installed):

> This is the job the **`Type: Deviation`** ADRs below do - NOT all of them, and the count is
> deliberately not written here

`DESIGN.md:2076` (untouched since long before, and publishing three values):

> **Every ADR from 0012 onward carries a `Type:` field**, `Deviation`, `Design change`, or `Both`.

**Two defects, one paragraph:**

1. `Both` is legal and unmatchable. An ADR recording a standards deviation that also changes the
   design is exactly what `Both` is for, and `:2064` would not count it.
2. **`from 0012 onward` is FALSE.** Measured: **34 of 34 ADRs carry the field**, `ADR-0001`
   included. This is the same boundary clause `d29937f` deleted from `docs/README.md:22` **in the
   same commit** - and it did not reach here, because that fix was about a different file. Third
   instance tonight of a repair not reaching its sibling site, and the second time this specific
   claim has been fixed in one place and left in another.

### What I checked and found CORRECT, because two sentences look like the same defect and are not

The same paragraph says *"The eleven below are all `Deviation`"* and *"The eleven required at
freeze:"*. **Both are true and neither is touched.** The list below them is exactly eleven items,
`ADR-0001` through `ADR-0011`, and all eleven carry `Type: Deviation` - verified by reading every
one. A count that names an enumerated list of that length is not a retyped population figure; it
is a description of the list beneath it, and "fixing" it would have introduced an error.

## Decision

**1. THE SELECTOR ADMITS `Both`.** `:2064` becomes *"the job the `Type: Deviation` and
`Type: Both` ADRs below do"*. The vocabulary is right - an ADR genuinely can be both - so the
defect is that the selector was narrower than the vocabulary it was written beside, and the
selector is what moves.

**`Both` IS NOT RETIRED, though it has zero users today.** Retiring it would force a future ADR
that is genuinely both to pick one and lose the distinction, and the freeze rule's teeth depend on
that question having an answer. A published value with no users is not a defect; a selector that
cannot see a published value is.

**2. `from 0012 onward` IS DELETED**, not corrected to `0001`. Same ruling as `d29937f` applied to
`docs/README.md:22`: a boundary that has to be maintained is the same defect as a count. The
sentence becomes *"Every ADR carries a `Type:` field"*, which is true now and stays true as the set
grows.

## Consequences

- `docs/DESIGN.md` changes, so **the freeze SHA is re-derived** and `docs/DESIGN-FREEZE.txt` is
  updated in the same commit. That is what this ADR exists to authorise.
- The frozen paragraph's selector and the frozen paragraph's vocabulary now agree. **Nothing else
  in §13 moves**, and the two "eleven" sentences are deliberately untouched.
- **`docs/adr/README.md:12` needs no change** - it already publishes all three values and always
  did. The disagreement was never between the two documents; it was inside one paragraph.

## What this ADR does NOT do

- It does not add a checker over the `Type:` vocabulary. That was left open by ADR-0034 and stays
  open: a gate over a vocabulary is worth having once someone decides the vocabulary is final, and
  nothing here decides that. What this removes is the trap where writing the first `Both` ADR
  silently breaks a frozen sentence - which was the actual cost of the gap, and it is now gone
  whether or not a checker ever exists.
- It does not revisit ADR-0034's ruling that the count is deleted rather than corrected. That
  ruling stands and this ADR depends on it.
