# Register: citations that RESOLVE and name the WRONG SUBJECT

**Seeded 2026-09-02 by `suborch-170`, task #180.** Every row is one
instance, cited to the round or commit that found it. **The count is
derived from the rows, never written in prose:**

```bash
grep -c '^| WS-' docs/reviews/WRONG-SUBJECT-REGISTER.md
```

## Why this file exists

Six live sites, an ADR, a workflow comment and a reviewer checklist all
said **"nine wrong-subject citations have been found on this project,
four of them inside the ADR documenting that defect class"** — and
**nothing anywhere enumerated them.** The count could not be checked by
anyone, could only grow, and was hand-maintained in nine places.

**IT WAS NEVER DERIVED, NOT EVEN ONCE.** `git log -S'nine wrong-subject'`
puts its origin at `90bade0` ("ADR-0019 and the cross-reference checker"),
and that commit introduces the sentence with no list behind it. The
number was an assertion at birth. Two ADRs still carry the earlier
spelling — `six` — which is the drift visible without leaving the
corpus: the set grew, and two sites never moved with it.

**#180 ruled a register rather than deletion, and the distinction is
worth keeping.** #166 ruled DELETE for "eleven decision records" because
that digit was decoration. This digit is **evidence** — it is the
argument that citations go wrong often enough to justify a checker.
Delete it and the argument goes too. So the container gets built instead,
and the prose points here.

**It also settles the sharpest sub-claim, at the third attempt.**
"Four of them inside the ADR documenting that defect class" was
verifiable by nobody. This file's first answer read *"with rows carrying
a `Where` column it is a grep"* — written without being executed, and
the grep returns ZERO. Its second answer, after #191, was that the zero
was a **corpus exclusion** rather than a measurement, because no round
had read `docs/adr/`. **#196 read it, and the answer is still zero — but
now it is a measurement.** Two rows entered the register from ADRs
(WS-32, WS-33) and neither is in the ADR the claim names. Three
different answers to one question, and only the third came from reading
the documents it is about.

## The arithmetic, and how to re-check it without trusting these rows

    33  rows                                  grep -c '^| WS-'
    10  cite CITATION-READ-VERDICTS.md        its own tally line :32 says WRONG 10
    19  cite CITATION-READ-SRC-VERDICTS.md    its own tally line :33 says WRONG 19
     2  cite CITATION-READ-ADR-VERDICTS.md    its own tally says WRONG 2
     1  cites BOTH  (WS-04)
     3  cite neither (WS-29, WS-30, WS-31)

    10 + 19 - 1 = 28 distinct ranges,  + 3 = 31,  + 2 (WS-32, WS-33) = 33 rows

**Two instruments, same answer**: the row provenance and the verdict
documents' own summary tables agree without being joined to each other.
Verified independently by Tier 0 at `23280e2`.

**AND THE OVERLAP IS NOT AN INFERENCE — the src round stated it.**
`CITATION-READ-SRC-VERDICTS.md:37`: *"One of the 19 - `1338-1343` - is
the range already on the board as task #54. **18 WRONG ranges at 24
sites are new.**"* That round knew it was re-reporting a known range and
said so, **and the knowledge then died in a document nobody joined to
the other one.** Carrying it here is the clearest single argument for a
register over a digit: a number cannot hold "this one is a duplicate",
and a row can.

## What counts as a row

**A citation that RESOLVES and names the wrong subject.** The line or
range exists, so every gate in this repository passes over it, and only
a human reading the target can tell. That is the whole defect class:
`check-design-citations.py` proves a cited line EXISTS and says so out
loud, and `check-cross-references.py` proves an `§n.m` resolves.

Two kinds are tracked separately, because they fail differently:

- **`RANGE`** — a `DESIGN.md:N-M` citation whose lines resolve and whose
  text is not the claim being cited. The bulk of the register.
- **`XREF`** — a `§n.m` cross-reference naming the wrong section.

**NOT a row:** a citation that resolves to a line that does not exist
(that is a broken reference, which a gate already catches), and a
CORRECT range carrying only a boundary nit — both verdict documents
below count those separately and so does this file.

## What this register does NOT cover

**`docs/adr/` IS NOW COVERED. It was the exclusion this section existed to
name, and #196 closed it.** `CITATION-READ-VERDICTS.md` read `tests/`;
`CITATION-READ-SRC-VERDICTS.md` read `src/` and `scripts/`;
`CITATION-READ-ADR-VERDICTS.md` read all 64 `DESIGN.md:N` citations across
the 19 ADRs that carry one. The `Where` column across all 33 rows now
takes eight values:

    18  `src/`          9  `tests/`        1  `tests/` + `src/`
     1  two sites       1  a report        1  a comment
     2  an ADR  (WS-32, WS-33)

So `grep '^| WS-' | grep -i adr` returns **2**, and the two rows are a
measurement rather than a boundary. **The previous zero was a corpus
exclusion**, which is the shape this project has learned to distrust: the
answer arrives with a plausible story attached and the story is about the
instrument.

**WHAT THE ADR ROUND FOUND, AND WHY THE SUB-CLAIM STILL DOES NOT DERIVE.**
Of the 64 ADR citations: **2 WRONG, 46 DRIFTED, 14 CORRECT, 2 boundary
nits.** Only the 2 WRONG are rows here - a DRIFTED citation was right when
written and is a repoint, not a misreading, and folding the two together
would triple this register with a different defect.

**The qualifier "four of them inside the ADR documenting that defect
class" measured ZERO.** That ADR is ADR-0019. It carries exactly four
`DESIGN.md` citations - which is very likely where the digit came from -
and **all four are DRIFTED, none is wrong-subject.** The two real ones are
in ADR-0013 and ADR-0014, neither of which is the ADR the claim names.
**The sub-claim is now REFUTED rather than uncheckable**, and the ruling
on what to do with the sentence is Tier 0's.

### The exclusion that REPLACES it, so this section does not go quiet again

**Only the `DESIGN.md:N` SPELLING was read.** `docs/adr/` also carries **58
bare `:NNN` citations across 16 files**, and **7 ADRs (0002, 0008, 0009,
0011, 0015, 0023, 0030) carry a bare form and no `DESIGN.md:N` form at
all** - so they were outside #196's sweep entirely. A bare form inherits
its document from the surrounding prose, so it cannot be attributed by
grep. **That is the next unread corpus, and naming it here is the whole
point of this section.**

## The register

| ID | Kind | Cited | Should be | Where / corpus | Found by |
|---|---|---|---|---|---|
| WS-01 | RANGE | `1342-1344` | `1037-1038` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-1 |
| WS-02 | RANGE | `1345-1346` | `1038-1040` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-2 |
| WS-03 | RANGE | `1323` | `1297-1300` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-3 |
| WS-04 | RANGE | `1338-1343` | `1335-1339` | `tests/` + `src/` | #52 W-4 / SRC W-18 — **one range, both corpora, and the src round said so itself at `CITATION-READ-SRC-VERDICTS.md:37`** |
| WS-05 | RANGE | `1341-1343` | `1337-1339` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-5 |
| WS-06 | RANGE | `986-1025` | `1026-1034` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-6 |
| WS-07 | RANGE | `701-705` | `723-727` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-7 |
| WS-08 | RANGE | `1432` | `1437-1439` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-8 |
| WS-09 | RANGE | `792-795` | `795-798` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-9 |
| WS-10 | RANGE | `938-939` | `937-938` | `tests/` | #52 `CITATION-READ-VERDICTS.md` W-10 |
| WS-11 | RANGE | `108-113` | `88-90` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-1 |
| WS-12 | RANGE | `281` | `282` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-2 |
| WS-13 | RANGE | `289-291` | `292-297` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-3 |
| WS-14 | RANGE | `291` | `293` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-4 |
| WS-15 | RANGE | `313` | `315-316` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-5 |
| WS-16 | RANGE | `317-319` | `320-321` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-6 |
| WS-17 | RANGE | `339-344` | `332-333` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-7 |
| WS-18 | RANGE | `632-638` | `624-627` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-8 |
| WS-19 | RANGE | `639-650` | `629-637` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-9 |
| WS-20 | RANGE | `656-662` | `664-666` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-10 |
| WS-21 | RANGE | `663-665` | `668-669` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-11 |
| WS-22 | RANGE | `676-680` | `688-690` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-12 |
| WS-23 | RANGE | `745-748` | `747-749` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-13 |
| WS-24 | RANGE | `747-750` | `744-745` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-14 |
| WS-25 | RANGE | `826-829` | `828-831` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-15 |
| WS-26 | RANGE | `877` | `1388-1393` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-16 |
| WS-27 | RANGE | `958` | `960-961` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-17 |
| WS-28 | RANGE | `1517` | `1515-1516` | `src/` | `CITATION-READ-SRC-VERDICTS.md` W-19 |
| WS-29 | XREF | `§16.3` | corrected | a report | `362350c`, found by the new cross-reference gate |
| WS-30 | RANGE | `207-212` | `207-229` | a comment | #132, fixed at `fe237d5` |
| WS-31 | RANGE | `692-697` | `681-687` | two sites | #133, fixed at `fe237d5` |
| WS-32 | RANGE | `1223` | `1351` | `docs/adr/0013-secret-absence-case-needs-a-pairing.md:13` | #196 `CITATION-READ-ADR-VERDICTS.md` W-1 - names the `.gitignore` §8 case while quoting the secret case |
| WS-33 | RANGE | `1763` | `1899` | `docs/adr/0014-c8-i1-empty-values-is-wrong.md:13` | #196 `CITATION-READ-ADR-VERDICTS.md` W-2 - names threat row `C8-E2` while quoting `C8-I1` |

**`DESIGN.md:603`'s `(§5.4)` is deliberately NOT a row.** ADR-0019
records it, and it is the instance that motivated the sentence this
register replaces — but §5.4 **does not exist**, so it resolves to
nothing. That is a broken reference, which `check-cross-references.py`
catches, not a citation that resolves and lies. Keeping the two apart is
the point of the `Kind` column, and putting it in would inflate this
register with the one instance a gate already covers.

## What this register is NOT

**It is a FLOOR, not a census.** Rows come from the audits that happened
to enumerate their findings. Rounds that fixed citations without listing
them individually are not represented, and neither is anything nobody
looked for. **Do not write "there are exactly N wrong-subject
citations"** — write that the register records N, which is a claim about
this file and is true.

**THE FIGURE IT REPLACES WAS WRONG BY MORE THAN A FACTOR OF THREE**, and
the evidence had been sitting in two committed documents the whole time.
Nobody was careless; the count simply had nowhere to live, so it stayed
at whatever it was when somebody last guessed.

**"Four of them inside the ADR documenting that defect class" IS NOW
DERIVABLE, AND IT DERIVES TO ZERO.** #196 read all 64 `DESIGN.md:N`
citations in `docs/adr/`. The ADR documenting the defect class is
ADR-0019; it carries exactly four `DESIGN.md` citations, all of them to
`:603`, and **every one was correct when written** — they are DRIFT, not
wrong subject. The corpus's two genuine wrong-subject citations are
WS-32 and WS-33, in ADR-0013 and ADR-0014, neither of which is the ADR
the claim names.

So the sentence failed twice over: **"nine" was wrong by more than 3x,
and "four of them inside the ADR" is zero.** Both halves were assertions
at birth; the second survived longer only because no round had ever read
the corpus it was about. **What to do with the sentence is a ruling, and
not this file's to make.**

## Adding a row

1. One row per instance. If a range is cited from several files, that is
   one row — both verdict documents group that way and the rows above
   inherit it.
2. `Found by` names a task, round or sha. A row nobody can trace is a
   number with extra steps.
3. **Never restate the count in prose.** Point here, or run the `grep -c`
   at the top.
