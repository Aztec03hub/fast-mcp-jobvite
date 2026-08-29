# CITATION-READ - the ~160 citations no checker can judge

**Read `docs/briefs/PREAMBLE.md` first.** Tools, isolation, evidence standards, gates and delivery
rules are there and are not repeated here.

Your agent name is `citation-read`. Your report goes to `docs/reviews/CITATION-READ-VERDICTS.md`,
committed on branch `review/citation-read`. **You are READ-ONLY on `src/`, `tests/` and `scripts/`.**

## Why this exists, and what it is NOT

`docs/reviews/check-design-citation-shape.py` exits **0** today. That is not a claim the citations
are correct. It decides only what a machine can: a target that cannot be ANYONE's subject - out of
bounds, blank, a bare fence, or starting on a blank line. **A citation landing on real prose that
happens to be the WRONG prose is invisible to it.**

The base rate is not low, and it is measured rather than feared:

- R4 sampled **18** of U5's citations and found **10 wrong**, all one paragraph short.
- `r4-fixes` then read the **whole** U5 population and found **ten more** beyond R4's sample.
- Its repoint deltas were `+6, +11, -3, -4, -2, -4, -5, -5, -4`, one widened, and **-598** -
  `1219-1221` to `621-622`, a different SECTION. **No constant offset would have found most of them.**
- A separate sweep of 49 shape-detectable occurrences ran this morning. **Those are a different
  population** and are already fixed. You are not re-doing them.
- Nine wrong-subject citations have been found on this project before, **four of them inside the ADR
  documenting that defect class.**

## Your population

**The `DESIGN.md:N` citations in the seven test modules outside `tests/test_tools_jobs.py`**, which
`r4-fixes` read and named as unverified in its own report. Roughly 160 occurrences. Enumerate them
yourself rather than trusting that number - a count in a brief is a retyped constant.

```bash
grep -rnoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' tests/ | grep -v test_tools_jobs.py | wc -l
```

`tests/test_pagination.py` is U6's and is also unreviewed; include it.

## The method, and it is the whole job

For each distinct range, in this order:

1. Read the CITING line and enough around it to know **what claim it is supporting**.
2. Read the TARGET from `git show c15b138:docs/DESIGN.md` - never the working tree.
3. Ask one question: **does the target's text say the thing the citing line claims it says?**

Return a verdict per distinct range: **CORRECT**, **WRONG** (with the range whose text IS the
subject), or **UNSETTLEABLE** (say why).

**Group by RANGE, not by site.** One wrong range cited at eleven sites is one finding with eleven
locations, and fixing some of eleven is worse than fixing none - a reader who greps the string then
gets two answers with no way to tell which is current.

## Three traps, each of which has already caught someone here

1. **DO NOT PROPOSE A CONSTANT OFFSET.** Most errors here are one line short, which makes `+1` look
   like the answer. It is not: one known case is short in the OPPOSITE direction, and `+1` there
   lands on real prose belonging to a different sentence, **silencing the shape checker while making
   the citation worse**. `docs/reviews/CITATION-REPOINT-MAP.md` records that case and one the map
   itself got wrong.
2. **A NEGATIVE CONTROL IS REQUIRED.** A sweep that finds something wrong with everything it looks
   at proves nothing. Name the ranges you read and judged CORRECT - `r4-fixes` listed 29 - and say
   how many you checked in total. Without that, a verdict list is unfalsifiable.
3. **RIGHT LINES, WRONG FILE.** One citation gave `DESIGN.md:828-833` for text that is at
   `IMPLEMENTATION-PLAN.md:831-832`. Both resolve. If a target reads plausibly but is about the wrong
   subject, **check whether the numbers belong to a different document.**

## You may not edit anything under src/, tests/ or scripts/

Three agents are live: `u7-resilience` in `services/jobvite_client.py`, `r2-fixes` in `src/` and
`tests/`, and `code-review-r5` reading. **Ship every fix as text in your report.** Cite the current
`main` SHA for each site and say that line numbers may have moved by the time anyone applies them -
**anchor on the SUBJECT, not the line**, which is the rule that exists because four mechanical
repoints in one day went to the wrong place.

## In the report

A table of distinct ranges with verdicts, then the site list per WRONG range. Then the negative
control. **End with what you could NOT settle**, and keep that for what is genuinely unsettleable
rather than what you did not get to - a cheap item parked there reads as rigour and is not.
