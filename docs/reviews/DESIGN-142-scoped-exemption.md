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

Tier 0 independently measured **52** at `20d5763`, one commit further on,
after marking one more line. Both measurements are right; the number is
simply not stable, and §8 says why that is the finding rather than a
nuisance.

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

> **This section is the record of what was PUT to Tier 0, not of what
> shipped.** Tier 0 ruled Option 2. Section 9 records what was built,
> and the one measured departure from the form described here.

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

## 8. Tier 0's two open questions, answered

Written after Tier 0's measurement crossed with this document. Their 52 at
`20d5763` and my 51 at `ee20c94` agree; the count moved by one because one
more line was marked in between. **That the number moves when people WRITE
ABOUT the marker is not noise around the measurement - it is the
measurement.**

### Q1 - should a line that merely MENTIONS the marker be exempt at all?

**No, and the mechanic in §3 settles it without a ruling being needed.**
Requiring `REPOINT-EXEMPT(` retires all 36 mention-only lines at once,
edits none of them, and grandfathers nothing. Tier 0's distribution says
the same thing from the other end: the three largest holders are
`check-design-citations.py` (8), `probe-repoint-fail-closed.py` (6) and
`DOCS-LINT-REPORT.md` (5) - the checker, its probe, and the report about
the probe. The tooling that implements the exemption is the biggest
consumer of it. None of those lines has a citation to exempt.

This is also why the count is unstable in the specific direction observed:
the population grows every time someone documents the mechanism, and it
can only grow, because nobody deletes a review record. A count that
ratchets upward from prose cannot be a ratchet on anything.

### Q2 - should the count exclude records? Is the container the cleaner fix?

**It is a real defect, it is worth its own ticket, and it is NOT a
substitute for the scoped form.** Three reasons, in order of weight.

**a. One container feeds THREE consumers, not two.**
`repoint-design-citations.py` does not enumerate files at all - it parses
`check-design-citations.py --since` output (`repoint-design-citations.py:198-226`).
Narrowing the bounds checker's suffix set therefore also decides what the
REPOINTER will and will not rewrite. Dropping `.md` would stop prose being
repointed, which is what `check-design-citation-shape.py:69-84` argues is
correct for a record - and would simultaneously stop `CONTRIBUTING.md`,
`README.md` and every live brief being bounds-checked at all.

**b. `.md` is not a kind, it is two kinds.** `REVIEW-R10.md` is a frozen
record. `docs/briefs/BRIEF-142-scope-the-exemption.md` is a live
instruction that a reader will act on, and its wrong citation went red
today for a good reason. Excluding by suffix would silence the live half
to quiet the frozen half - which is precisely the mistake
`check-design-citation-shape.py:82-84` records in its own comment: *"A path
list cannot see the KIND of the thing at the path."* Trading a path list
for a suffix list does not fix that; it renames it.

**c. The scoped form subsumes it, per citation instead of per suffix.**
`REPOINT-EXEMPT(DESIGN.md:99999: quotes the planted citation as evidence)`
says "this one is a record" at the exact granularity the question is
about, with a reason attached, in the one place a reader is already
looking. A suffix rule guesses the same thing from a filename.

**Suggested fix, and it is a ticket, not part of #142:** leave the
container alone until the scoped form lands, then re-measure how many
`.md` exemptions remain. If a large residue is still purely "this file is
a record", that is the evidence for a container change and it will be
measured rather than argued. Filing it now against a container nobody has
re-measured would be a fix chosen before its defect was sized.

### One implementation hazard the scoped form introduces, found by reading

`repoint-design-citations.py:123` does its OWN bare-substring test on the
citing line, re-read from disk, independently of the checker's. Today that
is unreachable belt-and-braces: the bounds checker skips the whole line
before it can emit a `MOVED` row for it.

Under the subset rule in §3 the two stop agreeing. A line with one scoped
citation and one unscoped one WILL emit a `MOVED` row for the unscoped
one - and the repointer's line-level test would then refuse to repoint it,
silently, because the line carries a marker for a different citation. **The
repointer must match at RANGE granularity too, not just the checker.** It
is in the plan as the third file; this records why it is not optional and
what breaks if a Tier-2 worker changes only the two gates.

Its fail-closed unreadable-line handling
(`repoint-design-citations.py:100-107`, `:209-215`) must survive unchanged.

## 9. WHAT WAS BUILT, and the one departure from §3

Tier 0 ruled Option 2 (the register), with one refinement: **no line
number in the key.** Built at `c38fe4d`.

### The departure: the `(` requirement was dropped, and the bare marker kept

§3 proposed requiring `REPOINT-EXEMPT(<address>)`. **I did not build
that, and the reason is a measurement Tier 0 asked for and I had not yet
made.** Tier 0's refinement said: if two lines in one file legitimately
exempt the same address, propose a tiebreak rather than inventing one. So
I measured the collision instead of assuming it away:

| measured over the tree at `e499f7e` | count |
|---|---|
| distinct `(path, address)` pairs currently exempt | 15 |
| pairs that ALSO appear on an **unmarked** line in the same file | **3** |
| pairs exempt on more than one line in the same file | 7 |

The three collisions are `check-design-citations.py` (`603`, unmarked at
`:12`), `probe-repoint-fail-closed.py` (`100`, unmarked at `:59`) and
this document. **A register keyed on `(path, address)` ALONE would have
exempted those unmarked lines too** - a silent widening, measured, in
three files on the day it landed.

So the marker stays, as the LINE selector, and the register decides the
CITATION:

    exempt  ==  marker on the line  AND  (path, address) registered

That is strictly better than either §3 option and strictly smaller:

- **Line granularity is preserved exactly.** No widening; the three
  collisions stay in the population, as today.
- **Zero edits to any of the 15 exempt lines.** They already carry the
  marker. There is no apply-at-scale pass at all - the ~15 sites Tier 0
  accepted as mine turned out to be ~15 register ROWS, which is the
  fifteen reasons, and nothing else.
- **The 36 mention-only lines are retired for free**, exactly as §3
  promised, by a different route: they carry the marker and cite
  nothing, so they grant nothing.
- **No new syntax**, so no migration and no grandfather clause.

The `(` form would have required editing 15 lines, several of them inside
frozen records, to buy a granularity the marker already provides.

### The recursion: structural, and the register file's suffix

Tier 0 asked for a control proving that prose describing the mechanism
cannot exempt anything. It is an arm of the probe and it passes - but the
guarantee is structural, not policed: prose is not the register.

The register is **`.txt`**. `.tsv` was the first choice and is **not on
`scripts/check-committed-file-types.py`'s allowlist**; `.txt` is, and has
the property that matters - it is in neither gate's suffix set
(`_SEARCH_SUFFIXES` = `.py .toml .md .yml .yaml .sh`, `CODE_SUFFIXES` =
`.py .sh`). The register header says why converting it to `.py`, `.json`,
`.md` or `.yaml` reopens the hole.

### The count now means something

The unit changed from LINES to CITATIONS, deliberately. The old count
read 51 while 36 of those lines carried no citation.

    check-design-citations.py       51 lines  ->  37 citations
    check-design-citation-shape.py  25 lines  ->  11 citations

Both gates now print the whole register with its reasons on every run.
`highest line cited` fell from `99999` to `1971 of 2133`, because the
out-of-bounds records are exempt per citation rather than hiding a whole
line.

### Two defects found on the way, both fixed here

**A. `check-checkers-are-wired.py` reported a sibling module as a missing
PyPI package** and turned red on `import repoint_exempt`. Its
`third_party_imports` docstring says *"Local-only names are excluded"*
and the code excluded only `sys.stdlib_module_names`. Same class as
R13-H1: a docstring describing a check nobody wrote. A bare `python3
docs/reviews/check-x.py` puts that directory on `sys.path[0]` and does
find a sibling. Fixed in the applier's last entry.

**B. My own applier applied three edits twice.** Its first idempotency
guard asked whether the ANCHOR was gone rather than whether the RESULT
was present - and every import edit APPENDS to its anchor, so the anchor
survives its own application. Three duplicated imports, caught by running
`grep -c`, repaired, and the guard now tests the result. Recorded because
"assert the anchor is unique" proves the anchor, never the outcome.

### Controls - `docs/reviews/probe-142-exempt-controls.py`, 9/9

Every arm plants into a real tracked file, runs the real wired gate as a
subprocess, reads its exit code, restores, and asks **git** whether the
restore landed. Addresses and the marker are built by concatenation, so
the probe needs no exemption of its own - a control that must exempt
itself from the thing it controls is the defect.

| arm | result |
|---|---|
| NEGATIVE the registered exemptions still skip; both gates green | bounds 0, shape 0, 37 exempt |
| POSITIVE a BARE marker no longer exempts anything | exit 1, plant named |
| POSITIVE a marker on an UNREGISTERED path is refused | exit 1, plant named |
| RECURSION prose describing the mechanism exempts nothing | exit 1, plant named |
| NEGATIVE an unmarked, unregistered citation is checked as normal | exit 1, plant named |
| MISMATCH a registered scope does NOT cover the other citation beside it | exit 1, exempt 37 -> 38 |
| **AMPUTATE** restore the bare-substring test and the plant PASSES again | exit 0, the defect is back |
| COUNT one added row moves the printed count | 37 -> 38 |
| RESTORE register and victim back as git has them | exit 0, count 37 |

The AMPUTATE arm is the one that makes the rest mean anything: without
it every positive arm would also pass against a checker that simply
reported everything.

### Gates, each read on its own line

    ruff check                                  0
    ruff format --check                         0
    mypy                                        0   120 files
    pytest                                      0   887 passed, 0 skipped, floor 887
    check-design-citations                      0   (was 1 at ee20c94)
    check-design-citation-shape                 0
    check-design-citations --controls           0
    check-design-citation-shape --controls      0
    check-checkers-are-wired                    0
    check-committed-file-types                  0
    check-harness-anchors --self-check --floor 458   0   458 anchors
    repoint_exempt (register + stale + self-check)   0
    probe-142-exempt-controls                   0   9/9 arms

Both floors were derived from `ci.yml` rather than retyped, per the
preamble. `pytest` lands exactly ON the floor of 887, not above it.

### For Tier 0: the ci.yml step, run before handing it over

    uv run --frozen python docs/reviews/repoint_exempt.py

exits **0**, prints the 15 rows with reasons, reports no stale rows, and
runs 4/4 self-checks. It goes to **1** on a stale row and **2** on a
malformed register, so the two are not the same exit code. It is not a
`check-*.py`, so `check-checkers-are-wired.py` does not require it to be
wired - wiring it is a choice, and it is Tier 0's.

**A row-count ratchet is NOT recommended.** The register's length is
already printed by both gates on every run and every row carries a
sentence, which is the visibility a ratchet would buy; a hard floor on
its length would additionally have to be lowered by hand every time a
record is legitimately retired, and a number people routinely lower is
not a ratchet. The stale check is the half that actually rots.

### Not settled

- Whether the `.md` container disagreement in §8 Q2 becomes a ticket.
  My recommendation stands: re-measure after this lands, not before.
- Whether `repoint_exempt.py` should be wired into `ci.yml`, and where.
  `ci.yml` is Tier 0's.

### Not attempted

- Nothing in the brief remains unattempted.
