# CITATION-READ-SRC - the same read, over `src/` and `scripts/`

**Read `docs/briefs/PREAMBLE.md` first.** Tools, isolation, evidence standards, gates and delivery
rules are there and are not repeated here.

Your agent name is `citation-read-src`. Your report goes to
`docs/reviews/CITATION-READ-SRC-VERDICTS.md`, committed on branch `review/citation-read-src`.
**You are READ-ONLY on `src/`, `tests/` and `scripts/`. Three agents are editing those trees.**

## Read the round that came before you

`docs/reviews/CITATION-READ-VERDICTS.md` is merged on `main`. **It is the method, and you are the
second half of the same job.** It read the 158 occurrences in `tests/` and returned **10 wrong ranges
of 115** - a 9% wrong-range rate over a population where `check-design-citation-shape.py` exits 0.

Its own closing line names your population: *"the same read over `src/` and `scripts/` has not been
done by anyone."* There is no reason to assume those trees are cleaner.

## Your population

`DESIGN.md:N` citations in `src/` and `scripts/`. I measured **279 occurrences, 147 distinct ranges,
29 files** - **enumerate it yourself rather than trusting those numbers**, because a count in a brief
is a retyped constant and one went stale in a live brief this week.

```bash
grep -rnoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' src/ scripts/ | wc -l
grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' src/ scripts/ | sort -u | wc -l
```

## The method, which is the whole job

Per distinct range: read the CITING line and enough around it to know **what claim it supports**;
read the target from `git show c15b138:docs/DESIGN.md`, never the working tree; then answer one
question - **does the target's text say the thing the citing line claims it says?**

Verdicts: **CORRECT**, **WRONG** (with the range whose text IS the subject), **UNSETTLEABLE** (say
why). **Group by RANGE, not by site** - one wrong range at eleven sites is one finding with eleven
locations, and fixing some of eleven is worse than fixing none.

## What the first round learned, so you start where it finished

- **NO CONSTANT OFFSET.** Its deltas were `-307, -305, -26, -4, -3, -1, +3, +5, +22, +40`. Six
  negative, four positive, two crossing a section boundary. **Exactly one would have been touched by
  a `+1` sweep, and it needed `-1`.**
- **THE BIGGEST MISSES WERE §8 NUMBERS STANDING IN FOR §7.4 TEXT**, ~306 lines out. Two separate
  sites. If a citation is in the 1300s and its claim is about boot, shutdown or the interpreter,
  **check §7.4 before believing it.**
- **A COPIED CITATION IS NEVER RE-DERIVED.** One docstring cited a range correctly two paragraphs up
  and wrongly below. **When one site in a file is wrong, read that file's others.**
- **VERIFY THE NUMBERING BASE INDEPENDENTLY.** For a `§8 #N` claim it confirmed the base by checking
  four other `#N` citations that land correctly. Do that rather than assuming.
- **RIGHT LINES, WRONG FILE.** It checked all ten wrong targets against `IMPLEMENTATION-PLAN.md` at
  the same numbers and reported the trap **negative** for its population. Check yours; do not assume
  the same answer.

## A NEGATIVE CONTROL IS REQUIRED

A sweep that finds fault with everything it reads proves nothing. **Name the ranges you judged
CORRECT and say how many you checked in total.** The first round went further and listed ten ranges
it graded CORRECT *with a boundary nit*, which is what makes its control falsifiable - it could not
have done that without reading both endpoints. Do the same.

## One range is already known WRONG and is partly in your tree

`1338-1343` -> **`1335-1339`** (§8 #17). Its sites are `tests/test_audit.py:16` and `:307` **and
`src/fast_mcp_jobvite/audit.py:190`**. It is on the board as task #54 and will be applied in one
pass. **Do not re-file it; do confirm it, since a second independent read of a known answer is worth
having.**

## What you may not do

`u7-resilience` is in `services/jobvite_client.py`, `r2-fixes` is in `src/` and `tests/`, and
`r5-fixes` is in `tests/test_pagination.py`, `tools/jobs.py` and `scripts/check-u6-paging-*.sh`.
**You edit nothing.** Ship every fix as text. **Cite the SHA you read**, say that line numbers may
have moved by the time anyone applies them, and **anchor on the SUBJECT rather than the line** -
four mechanical repoints in one day went to the wrong place because they trusted a line number.

## In the report

A table of distinct ranges with verdicts, the site list per WRONG range, then the negative control.
**End with what you could NOT settle**, and keep that for what is genuinely unsettleable rather than
what you did not reach. The first round left exactly one item there, an ambiguous referent it
declined to repoint on a guess - that is the standard.
