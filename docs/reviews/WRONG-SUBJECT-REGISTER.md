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

**It also makes the sharpest sub-claim checkable for the first time.**
"Four of them inside the ADR documenting that defect class" was
verifiable by nobody, and **THIS FILE DOES NOT SETTLE IT EITHER.** That
sentence read *"with rows carrying a `Where` column it is a grep"* until
the grep was run. It returns ZERO, and the zero is a corpus exclusion
rather than a measurement - see "What this register does NOT cover"
below. A claim about how to check a claim is itself a claim, and this one
was written without being executed.

## The arithmetic, and how to re-check it without trusting these rows

    31  rows                                  grep -c '^| WS-'
    10  cite CITATION-READ-VERDICTS.md        its own tally line :32 says WRONG 10
    19  cite CITATION-READ-SRC-VERDICTS.md    its own tally line :33 says WRONG 19
     1  cites BOTH  (WS-04)
     3  cite neither (WS-29, WS-30, WS-31)

    10 + 19 - 1 = 28 distinct ranges,  + 3 = 31 rows

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

## What this register does NOT cover, and why its zero is not a zero

**EVERY ROW COMES FROM ONE OF TWO SWEEPS, AND NEITHER SWEPT `docs/adr/`.**
`CITATION-READ-VERDICTS.md` read `tests/`; `CITATION-READ-SRC-VERDICTS.md`
read `src/` and `scripts/` and says so in its own first line. The `Where`
column across all 31 rows takes exactly six values:

    18  `src/`          9  `tests/`        1  `tests/` + `src/`
     1  two sites       1  a report        1  a comment

**No row names an ADR, and no row CAN**, because no round has ever read
one for this defect. So:

    grep '^| WS-' WRONG-SUBJECT-REGISTER.md | grep -i adr   ->  0 rows

is a statement about the sweep's boundary, not about ADRs. **It is a
clean zero that explains itself**, which is the shape this project has
learned to distrust: the answer arrives with a plausible story attached
and the story is about the instrument.

**THE SUB-CLAIM IS THEREFORE NEITHER CONFIRMED NOR REFUTED HERE.** ADRs
carry 64 `DESIGN.md:N` citations across 19 files today
(`grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l`).
Settling "four of them inside the ADR" means READING those, because
wrong-subject is not greppable by construction - a wrong-subject
citation resolves, which is the entire defect. That is tracked as its
own task rather than left as an implication of this file's silence.

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

**"Four of them inside the ADR documenting that defect class" is NOT yet
derivable and no row asserts it.** That sub-claim needs each row to
carry the file it lives in, and the two verdict documents group by
RANGE rather than by site. Re-deriving it means re-reading their site
lists. **Recorded as unfinished rather than dropped, and rather than
carried forward as prose nobody can check** — which is the failure this
file exists to end.

## Adding a row

1. One row per instance. If a range is cited from several files, that is
   one row — both verdict documents group that way and the rows above
   inherit it.
2. `Found by` names a task, round or sha. A row nobody can trace is a
   number with extra steps.
3. **Never restate the count in prose.** Point here, or run the `grep -c`
   at the top.
