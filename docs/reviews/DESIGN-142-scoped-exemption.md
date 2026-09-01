# #142 - give `REPOINT-EXEMPT` a scope and a reason: the measurement, and the choice

Tier-1, branch `fix/142-exempt-scope`, based on `ee20c94`.
**Nothing has been applied. This document exists to get Tier 0's ruling
before a wired gate changes shape.**

## 1. The measurement, and where the brief was stale

Probe: `docs/reviews/probe-142-exempt-inventory.py`.
Raw output: `docs/reviews/EVIDENCE-142-exempt-inventory.txt`.

The brief says the printed skip count "reads **47**". **47 was true at
`93d1c93` and is stale on `main`.** It was also only ever one of two
numbers, because the two wired gates do not share a container:

| container | suffixes scanned | at `93d1c93` | at `ee20c94` (`main`) |
|---|---|---|---|
| `check-design-citations.py` | `.py .toml .md .yml .yaml .sh` | **47** | **51** |
| `check-design-citation-shape.py` | `.py .sh` | **25** | **25** |

The four new marked lines are all in `docs/briefs/BRIEF-142-scope-the-exemption.md`,
the brief itself.

### The load-bearing column

Of the 51 marked lines in the wider container:

| marked lines carrying | count | share |
|---|---|---|
| **0** `DESIGN.md:N` citations | **36** | 71% |
| exactly 1 citation | 13 | 25% |
| 2 citations | 2 | 4% |

**36 of 51 exemptions exempt nothing.** The marker is a bare substring,
so every line that merely *names* it exempts itself: the constant's own
definition (`check-design-citations.py:122`), the docstrings describing
the mechanism, the source line that implements the check
(`repoint-design-citations.py:123`), the review findings about the
defect. This is the "a grep for a defect pattern finds the comment that
forbids it" shape, wired into a gate.

### The question the brief called load-bearing

*Does any marked line carry anything OTHER than the item being exempted?*

**No. Zero live instances.** The only two lines with more than one
citation are `check-design-citations.py:78` and `:319`, and in both the
two citations ARE the exempted item - example data the pattern is meant
to match. Every other marked line carries at most one citation, and that
citation is the record being protected.

**Line granularity is a theoretical defect in this tree, not a live one.**
It is still worth closing, because closing it is the same code as the
scope check - but it should not be sold as a bug being fixed.

## 2. THREE CORRECTIONS TO THE BRIEF

**C1. `main` is RED right now, and the brief commit made it red.**

    $ python3 docs/reviews/check-design-citations.py
      1964 DESIGN.md citations across 208 files
      highest line cited: 99999 of 2133
      lines skipped as REPOINT-EXEMPT: 51

    1 problem(s):
      FAIL: docs/briefs/BRIEF-142-scope-the-exemption.md:62: DESIGN.md:99999 is past the end of DESIGN.md (2133 lines)  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    EXIT=1

`BRIEF-142-scope-the-exemption.md:21` carries the marker and is skipped;
`:62` writes the same citation in §C.4 and does not. This is Tier 0's to
fix and is independent of my change. **I have not touched it** - #111
says a record is not rewritten to make a gate green, and I have no
ruling on whether the brief gets an exemption or a rewrite.

**C2. §C.4's positive arm is not satisfiable as written.** It asks that
"a scoped marker must not exempt `DESIGN.md:99999-99999`". Three  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
committed records legitimately cite exactly that, as evidence:

    docs/reviews/REVIEW-R10.md:353
    docs/reviews/REVIEW-R10.md:416
    docs/worklogs/WORKLOG-115B-kind-not-path.md:169

(plus `docs/worklogs/AUDIT-SURVIVORS-REPORT.md:266`). The plant and the
record are **byte-identical in citation value**. No rule keyed on the
VALUE can separate them. Only a rule keyed on IDENTITY can - which is
what Option 2 below is, and why I recommend it.

**C3. The Tier-2 "apply at scale" step is much smaller than the brief
assumes, and under the recommended form it is ~15 sites, not 47 or 51.**
See §4. I do not expect to spawn a worker for it; the protocol says not
to spend a pane on what one tool call does.

## 3. THE CHOICE

Both options share one mechanic, and it is the one that pays for itself:

> **The marker must be immediately followed by `(`.** The regex becomes
> `REPOINT-EXEMPT\(([^)]*)\)` instead of the substring `REPOINT-EXEMPT`.

That single change retires all 36 zero-citation "exemptions" **without
editing one character of them**. `EXEMPT_MARKER = "REPOINT-EXEMPT"` and
`if "REPOINT-EXEMPT" in cited_line:` stop being exemptions and become
what they always were: prose and code that happen to name a string. No
record is rewritten, nothing is grandfathered, and the printed count
falls from 51 to the real ones - which is what makes the count mean
something.

A bare `REPOINT-EXEMPT` afterwards means **nothing at all**: the line is
not skipped, and it is not reported either. It falls into the normal
population. If it carries a bad citation the gate reports that citation,
which is correct and is not silent. This is why no grandfather clause is
needed - the 36 are silent because they have nothing to say.

**Scope matching is a SUBSET rule, not set equality.** Only the citations
named inside the parentheses are skipped; anything else on the line stays
in the population. That is requirement (c) and the granularity fix in one
rule, and it means a citation added to an already-exempt line tomorrow is
scanned.

### Option 1 - inline scope and inline reason. No new files.

    REPOINT-EXEMPT(DESIGN.md:373-383: a record of where a defect WAS)

- Three files change: both wired gates and `repoint-design-citations.py`.
- ~15 marked lines converted.
- Meets (a) still skips, (c) refuses a mismatched scope, (d) count is
  non-vacuous.
- **Does NOT meet (b).** A plant author writes a matching scope and a
  plausible reason and passes at exit 0. The only defence is a human
  reading the diff - which is the defence that failed for the bare
  marker.
- Cheapest thing that could work. Roughly a 40-line diff.

### Option 2 - Option 1 plus a keyed register. RECOMMENDED.

Everything in Option 1, and additionally the pair
`(path, citation)` must appear in a register with a non-blank reason, or
the exemption is refused.

    docs/reviews/REPOINT-EXEMPT.tsv     the register (data)
    docs/reviews/repoint_exempt.py      one loader, imported by all three consumers

- **Meets (b).** Planting `DESIGN.md:99999-99999` now requires adding a  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
  row to a file whose length is a ratchet, in a diff nobody can call
  incidental. `REVIEW-R10.md::DESIGN.md:99999` is in the register with a  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
  reason; a new `src/.../audit.py::DESIGN.md:99999` is not, and is  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
  refused - identity, not value, which is the only thing that can
  separate C2's three records from the plant.
- Mirrors this repo's own two precedents:
  `check-checkers-are-wired.py:73` (`UNWIRED_BY_DECISION`) and
  `check-no-errexit.py:88-95` (`EXEMPT`, with
  `assert all(v.strip() ...), "a blank reason is not an exemption"`).
- Register is **`.tsv` on purpose**: it is in neither gate's suffix set,
  so a register full of `DESIGN.md:99999` strings is not itself scanned.  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
  A `.py` register would be in the shape gate's container and would need
  to exempt itself - the self-reference this whole ticket is about.
- Add a **stale-entry check**, copied from `check-checkers-are-wired.py:305-306`:
  a register row that matches no line in the tree is reported. Without it
  the register rots the way every hand-kept list beside its container
  rots.
- Cost over Option 1: one data file, one ~30-line loader, three import
  lines, and ~15 reasons I have to write by hand. Those reasons are
  correctness calls, so they are mine, not a Tier-2 worker's.

### What I recommend, and why

**Option 2.** Option 1 is genuinely cheaper and I would take it if (b)
were not in the brief - but (b) is in the brief, C2 shows why only
identity can deliver it, and this repo has already built the same
register twice for the same reason. The marginal cost is one small data
file and a loader.

**If Tier 0 rules Option 1**, say so explicitly and I will record that
(b) is knowingly unmet, rather than shipping a control that appears to
pass.

## 4. The sites, enumerated (for whichever option is ruled)

15 lines carry both the marker and at least one citation. Under the new
regex these are exactly the lines that must be converted; every other
marked line needs no edit.

    docs/briefs/BRIEF-142-scope-the-exemption.md:21   DESIGN.md:99999-99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    docs/briefs/BRIEF-142-scope-the-exemption.md:47   DESIGN.md:373-383
    docs/reviews/REVIEW-R10.md:353                    DESIGN.md:99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    docs/reviews/REVIEW-R10.md:416                    DESIGN.md:99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    docs/reviews/check-design-citation-shape.py:33    DESIGN.md:311
    docs/reviews/check-design-citation-shape.py:45    DESIGN.md:373-383
    docs/reviews/check-design-citations.py:14         DESIGN.md:918-923
    docs/reviews/check-design-citations.py:78         DESIGN.md:603, DESIGN.md:918-924
    docs/reviews/check-design-citations.py:201        DESIGN.md:99999-99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    docs/reviews/check-design-citations.py:319        DESIGN.md:918-924, DESIGN.md:603
    docs/reviews/probe-midsentence-shape.py:32        DESIGN.md:906
    docs/reviews/probe-repoint-fail-closed.py:87      DESIGN.md:100
    docs/reviews/probe-repoint-fail-closed.py:100     DESIGN.md:100
    docs/worklogs/AUDIT-SURVIVORS-REPORT.md:266       DESIGN.md:99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->
    docs/worklogs/WORKLOG-115B-kind-not-path.md:169   DESIGN.md:99999  <!-- REPOINT-EXEMPT: quotes the out-of-bounds citation as evidence -->

Plus one line that needs an exemption it does not have today:
`docs/briefs/BRIEF-142-scope-the-exemption.md:62` (C1).

Two of these are in `docs/briefs/BRIEF-142-scope-the-exemption.md` -
Tier 0's own file. I will not edit it without being told to.

**Every one of the 15 is still needed even where the citation resolves
cleanly**, because the marker also stops `repoint-design-citations.py`
rewriting a historical record. "Would the gate go red without it" is not
the test.

## 5. The controls I will build (§C.4), and what each actually proves

| arm | plant | required result |
|---|---|---|
| negative | the 15 converted sites, untouched | both gates exit 0, count = 15 |
| positive - bare | `# PLANT DESIGN.md:99999-99999 REPOINT-EXEMPT` | bounds gate exit 1, names the line |
| positive - scoped, unregistered | `# PLANT DESIGN.md:99999-99999 REPOINT-EXEMPT(DESIGN.md:99999-99999)` | exit 1, "not in the register" (Option 2 only) |
| mismatched scope | `DESIGN.md:99999 ... REPOINT-EXEMPT(DESIGN.md:373-383)` | exit 1, the 99999 is NOT skipped |
| count non-vacuous | add one legitimate exemption | printed count moves 15 -> 16 |

The count arm is the one that is easy to fake and I will run it by
adding and removing a real row, comparing printed integers, not by
reading the code.

## 6. Not settled

- Whether `BRIEF-142-scope-the-exemption.md` gets an exemption or a
  rewrite for C1. Tier 0's file, Tier 0's call.
- Whether the register should be ratcheted in `ci.yml` by row count.
  That is a `ci.yml` step and `ci.yml` is Tier 0's; I will hand over the
  command having run it, per PREAMBLE.

## 7. Not attempted yet

- The apply pass and the controls. Both wait on the ruling.
