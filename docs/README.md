# Documentation index

This directory holds more documents than anyone will read. This page exists so a reader knows which
are **current**, which are **historical record**, and which three they should actually read.

*(An earlier version of this line opened with a document count and a byte total. Both were true when
written and neither survived the afternoon - in the index whose closing section is about documents
that no longer match their own stated state. Counted nothing here on purpose.)*

## Read these three

| Document | What it is |
|---|---|
| [`DESIGN.md`](DESIGN.md) | **The authority, and FROZEN at revision 6.** Tool surface, module layout, Jobvite client, error contract, testing strategy, threat model. **Only a numbered ADR may change it** - a finding against it is no longer an edit request. Its status block names three risks the freeze carries rather than resolves; read those before trusting it. Everything else either supports it or records how it got that way. |
| [`plans/IMPLEMENTATION-PLAN.md`](plans/IMPLEMENTATION-PLAN.md) | Ordered work units turning the design into a server, each with its verification. **Start here to build.** Still under review; U0 is being implemented against it. Where a built unit contradicts its section here, **the build wins** and this document is corrected from it. |
| [`CREDENTIAL-CHECKLIST.md`](CREDENTIAL-CHECKLIST.md) | What to observe the day a Jobvite credential first exists. **Rows 1-4 block** any claim that the success path is verified; row 0 must be asked *before* a key is issued. |

## Current, and consulted rather than read through

| Document | What it is |
|---|---|
| [`adr/`](adr/) | Eleven decision records, each citing the clause it deviates from. `adr/README.md` explains the two jobs an ADR does here. From ADR-0012 each carries a `Type:` field. |
| [`DECISIONS.md`](DECISIONS.md) | D1-D17, what was decided and the evidence behind it. |
| [`data-inventory.md`](data-inventory.md) | The Article 30 record of processing. Names the language-model host as a downstream processor, which is the disclosure a conventional integration does not make. |
| [`research/`](research/) | Seven reports: the Jobvite API surface and client contract, FastMCP capabilities, two executed runtime spikes, the binding standards, the licensing survey. `STANDARDS.md` carries the **dismissal register** §13's freeze procedure re-tests. |
| [`reviews/check-coupling*.py`](reviews/) | The three gates. `check-coupling.py` enforces §11 against §8; the controls harness proves each check can fail; the sweep is subject-free. Run from the repository root. **They do not run in CI yet** - standing that up is the first unit of implementation. |

## Historical record

**The review documents below are dated artifacts, not current statements.** Where one disagrees with
`DESIGN.md`, the design wins - these record what was found at the time, and most findings have since
been applied. They are kept because a review's *reasoning* outlives its verdict, and because
deleting them would destroy the only account of why several decisions look the way they do.

- `reviews/DESIGN-R1.md` … `DESIGN-R7-CONFIRM.md` - seven adversarial rounds on the design.
- `reviews/DESIGN-FREEZE-REVIEW.md` - the last one, which the freeze rests on.
- `reviews/PLAN-REVIEW-R1.md`, `-R2.md`, … - rounds on the **implementation plan**, a separate document from the design and reviewed separately. Two of round 1's findings were design defects rather than plan defects, which is why the plan's rounds are worth reading next to the design's rather than after them.
- `reviews/DESIGN-DELTA-REVIEW.md` - the 118 lines added after round 7, reviewed separately.
- `reviews/F10-RULING.md`, `reviews/FREEZE-DISMISSAL-RETEST.md` - single-question rulings.
- `reviews/CONFORMANCE-*.md`, `reviews/CITATION-*.md` - the obligation corpus and its audits.
  `CONFORMANCE-RESWEEP.md` is the live obligation state; the others are its history.
- `reviews/SPIKE-CLAIM-AUDIT.md`, `reviews/FIX-3-REPORT.md`, `reviews/THREAT-MODEL-DRAFT.md` -
  a claim audit, a work report, and the draft that became §11.

## One thing this index exists to prevent

`reviews/PENDING-CONFORMANCE-FIXES.md` staged a set of fixes and said, in its own opening lines,
*"This file is deleted when applied."* It was applied. It was not deleted. It then sat for a day
carrying a live finding - that two `priority: required` standards had been dismissed **without being
read** - under a heading that made the file look finished.

**Nobody re-read it, because a staging file that has served its purpose looks like clutter rather
than like a record with something still in it.** That finding was eventually closed only because a
different agent rediscovered it independently a day later. The file has now been removed, its
content preserved in git history, and the finding lives where findings belong: as `B110` in the
obligation corpus and as §11's grid in the design.

**A document that describes its own end state should be checked against that state, not trusted to
have reached it.**
