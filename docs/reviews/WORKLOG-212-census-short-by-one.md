# WORKLOG #212 (R21-M2): the fix for a COUNT finding restated a census short by one

Agent: `suborch-212`. Worktree `/tmp/w212-census-short-by-one`, branch `fix/212-census-short-by-one`.
Base: `a52af14`. Written 2026-09-02 01:04 CDT.

This is a fix worklog, not a code review, so it declares no `REVIEW-COVERS` range.

## 1. The finding reproduces, exactly

Measured at the blob, never at HEAD, because the defect IS a figure read at the wrong moment:

    git ls-tree --name-only e3b5c97 docs/adr/ | grep -E '^docs/adr/[0-9]' \
      | while read -r f; do git show "e3b5c97:$f" | grep -h '^\*\*Type:\*\*'; done \
      | sort | uniq -c

Output, verbatim:

          1 **Type:** Correction to a contract statement that an implementer can satisfy while shipping the defect it was written to prevent
          1 **Type:** Correction to a count that is false about its own subject
         17 **Type:** Design change
         14 **Type:** Deviation
          1 **Type:** Standards deviation

ADR file count at that blob: **34** (`git ls-tree --name-only e3b5c97 docs/adr/ | grep -cE
'^docs/adr/[0-9]'` -> `34`, rc=0). `Type:` lines: **34** (1+1+17+14+1). Kinds: **FIVE**.

The document said four kinds, total 33. **Short by one.** The missing row is `Correction to a count
that is false about its own subject`, and I confirmed by selector which file carries it:

    docs/adr/0034-the-adr-count-in-design-md-is-deleted-not-corrected.md

**It is this ADR's own row** - the file `e3b5c97` was adding. Its `Type:` line at that blob reads
`Correction to a count that is false about its own subject`; it reads `Design change` today only
because the normalisation recorded further down that same ADR changed it. So the spelling the
corrected census must name is one the file no longer carries, which is precisely why re-deriving at
the blob and not at HEAD was load-bearing.

**The lead's spelling of the fifth kind was correct**, and so was every figure in the brief. Nothing
in the finding failed to reproduce.

### Where the wrong number came from

`e3b5c97`'s own commit message says *"There are 33"* and *"Fifteen of thirty-three do job 1"*. It had
counted the corpus it was adding TO and not the file it was adding. `2514990` - the R20-M2 fix, itself
a fix for a COUNT finding - retyped that message instead of re-deriving at the blob, and carried the
off-by-one forward.

## 2. One site, not two - and this corrects the task description

The task description and the brief both say the identical four-row list appears a second time and
implies both need the same repair. **Measured: only ONE site carries the defect.**

- `:58-63` (pre-fix) stated the four-row list AND asserted `total 33`. **Defective.** Fixed.
- `:71-73` (pre-fix) states the same four-row list with a trailing ellipsis and then says *"and this
  ADR added a fifth spelling of its own"*. It asserts **no total**, and it explicitly supplies the
  fifth row. **That sentence is TRUE as written.** I did not touch it.

Rewriting a true sentence to look like the one I had just fixed would have been a mechanical repoint
of the kind this project keeps finding, so the second site stands. Reporting the absence as loudly as
the presence: the census defect is one site, not two.

A third occurrence of the four-row list is at `docs/reviews/REVIEW-R20.md:199-200`, quoting the ADR's
prose as R20 found it. **Deliberately untouched**: that is a dated review record of what was read at
the time, and editing it would falsify the record rather than fix anything.

## 3. The ruling: CORRECTED, not deleted - and why

The brief asked for this to be argued from the two rules by name and written into the document rather
than split silently. It is now in the ADR body under the heading *"WHY THIS FIGURE IS CORRECTED AND
NOT DELETED, WHICH IS THE OPPOSITE OF WHAT THIS ADR RULES EVERYWHERE ELSE."* The argument:

**Rule A - "a stale count is DELETED, not corrected."** ADR-0034's own Decision, inherited from #166.
Two reasons it does not reach this line:

1. Its *stated rationale* is *"a corrected count is a count that will be wrong again."* This figure is
   pinned to an immutable blob. Once right, it cannot be wrong again. The rationale has no purchase.
2. Its *prescribed remedy is unavailable here.* DELETE works by pointing at the command that answers
   the question live. **No live command answers what the partition was at `e3b5c97`.** The published
   `grep -h '^\*\*Type:\*\*' docs/adr/[0-9]*.md` reads the working tree; the past needs `git ls-tree`
   plus `git show`. A rule whose remedy cannot be executed is a rule out of its scope.

**Rule B - "a dated, provenanced record is not a live count."** ADR-0034's own fourth outcome class
(*"a historical justification inside a live file"*), and the label eight lines above the defect, where
the `d29937f` table is KEPT as *"the evidence for this ruling and NOT as a live figure."*

**Rule B governs, because Rule A's scope is LIVE counts.** The decisive structural point: **this
document already keeps a blob-pinned census eight lines above the one in question.** Deleting the
`e3b5c97` census while keeping the `d29937f` table would leave two blob-pinned censuses in one file,
one deleted and one kept, on no stated principle. And this census is the *evidence* for the sentence
it sits under - deleting it destroys the proof of the ruling it exists to support.

The dividing question is written into the document as: **not "is this a count?" but "can this figure
be wrong again?"** A dated record takes the arithmetic remedy precisely BECAUSE its provenance is
already pinned; a live count takes deletion precisely because no provenance can pin it.

The ADR now also carries both commands side by side - the live `grep`, and the `git ls-tree`/`git
show` form - with a comment saying the live grep CANNOT answer the historical question.

## 4. A second, smaller defect I introduced and then removed

My first draft cited the fourth outcome class as `:127-130`. **My own insertion had shifted those
lines** - the class is at `:169` after the edit. I replaced the number with a subject phrase rather
than retyping a corrected one, in the ADR that rules against fragile figures. Fixing a count defect
by writing a line number that my own diff had just invalidated would have been the same defect one
column over.

I checked for inbound line-anchored citations to this ADR before editing:

    grep -rnE '0034[a-z0-9-]*\.md:[0-9]+' --include='*.md' --include='*.py' --include='*.sh' --include='*.yml' .

**NONE FOUND**, over the whole worktree, all four extensions. So the line shift dangles nothing.

## 5. Gates - every exit code read on its own line

`docs/DESIGN.md` did NOT move, which the brief required:

    python3 docs/reviews/check-design-freeze.py
    rc=0
      Declared freeze: d1f1a52
      docs/DESIGN.md at d1f1a52: 61e264d39b88784b57b73cc135a5167a9a7641e0
      docs/DESIGN.md at HEAD:    61e264d39b88784b57b73cc135a5167a9a7641e0
      The frozen design and the trunk's design are the same blob.

    git diff --stat a52af14 -- docs/DESIGN.md docs/DESIGN-FREEZE.txt
    rc=0, EMPTY output - neither file is in my diff.

Checker batch, each rc on its own line:

| checker | rc |
| --- | --- |
| `check-coupling.py docs/DESIGN.md` | 0 |
| `check-design-freeze.py` | 0 |
| `check-no-errexit.py` | 0 |
| `check-design-citation-shape.py` | **1 (PRE-EXISTING, see below)** |
| `check-clause-citations.py` | 0 |
| `check-env-vars-are-declared.py` | 0 |
| `check-settings-are-read.py` | 0 |
| `check-standards-citations.py` | 0 |
| `check-cross-references.py` | 0 |
| `check-coupling-controls.py` | 0 |
| `check-obligations.py` | 0 |
| `check-plan-measurements.py` | **0 under `uv run --frozen` (see below)** |
| `check-resweep-verdicts.py` | 0 |
| `check-coupling-sweep.py` | 0 |
| `check-design-citations.py` | 0 |
| `check-row-floors.py` | 0 |
| `check-row-floor-exactness.py` | 0 |
| `check-no-sigpipe-pipelines.py` | 0 |
| `check-landing-published.py` | 0 |
| `check-adr-numbers.py` | 0 |

`docs/OBLIGATIONS.md` was not hand-edited and `check-obligations.py` exits 0, so no anchor moved.

## 6. TWO FINDINGS OUTSIDE MY SCOPE - reported, not fixed, not filed

The preamble rules that out-of-scope work is REPORTED and that filing it as a task needs a mandate the
brief does not grant. Both are reported here and not created.

### 6a. `check-design-citation-shape.py` is RED ON MAIN, and it is a gating step

**Not caused by me.** Proved by running it at the unmodified base in a throwaway detached worktree:

    /tmp/w212-baseline at a52af14, untouched
    python3 docs/reviews/check-design-citation-shape.py   rc=1
    uv run --frozen python docs/reviews/check-design-citation-shape.py   rc=1

Red both ways, so it is not an interpreter artefact. The finding, verbatim:

       2  starts on a BLANK line (the off-by-one shape)
            docs/reviews/probe-204-orphaned-by-repoint.py:7  DESIGN.md:489-490
            docs/reviews/probe-204-orphaned-by-repoint.py:70  DESIGN.md:489-490

`ci.yml:353` runs this as a gating step (`run: python3 docs/reviews/check-design-citation-shape.py`,
no `|| true`), so **main is red on a wired gate.** The file entered main at `04ad8e7` (`#204:
FINDINGS, and ORPHANED-BY-REPOINT - a third citation defect class`). Task #208 is in progress on that
same file, so this may already be in someone's hands.

**Suggested fix:** `DESIGN.md:489-490` starts on a blank line; widen or shift the range to the first
line of the actual prose at both `:7` and `:70`, deriving the new bound by reading `DESIGN.md` at the
declared freeze SHA rather than retyping. If the two citations are illustrative rather than real
subjects, the alternative is an `EXEMPT` entry with a reason, which is the mechanism the checker
already supports and already uses for six other sites.

### 6b. `check-plan-measurements.py` is interpreter-dependent, and `ci.yml` calls it with bare `python3`

My first run of it was a **false red**, and the checker itself printed the reason:

    Re-running 4 plan measurements with /usr/bin/python3
      [STALE] M3 manifest closes the dependency set
      [STALE] M4 guard vs a wholly-deselected file
    rc=1

Same file, same commit, correct interpreter:

    Re-running 4 plan measurements with /tmp/w212-baseline/.venv/bin/python
      [PASS] M1   [PASS] M2   [PASS] M3   [PASS] M4
      Every plan measurement reproduces.
    rc=0

So the code is fine and 4/4 measurements hold. But `ci.yml:665` invokes it as `out=$(python3
docs/reviews/check-plan-measurements.py 2>&1)`, a **bare inherited interpreter** - the same class this
project already fixed at `3082a18`/`4917a94` (task #46, *"an interpreter inherited rather than
chosen"*). It is green in CI today only if CI's `python3` happens to resolve to the synced venv.

**Suggested fix:** change `ci.yml:665` to `uv run --frozen python docs/reviews/check-plan-measurements.py`,
matching the sibling steps at `:303` and `:332` which already do exactly that. **I did not make this
change** - `ci.yml` is the orchestrator's file and this is outside #212.

I could not settle whether this step is currently green in CI; see section 8.

## 7. The diff

One file, one paragraph, rewritten IN PLACE. No rider, no appended correction, no `Co-Authored-By`.

    docs/adr/0034-the-adr-count-in-design-md-is-deleted-not-corrected.md

## 8. What I did NOT verify

- **Whether `check-plan-measurements.py` is actually green in CI.** I measured both interpreters
  locally and established the dependency, but I did not read a CI run log to see which `python3` the
  runner resolves. The risk in 6b is conditional on that and I am not asserting the step is red.
- **The full pytest suite and the harness-anchor floor.** I did not run them. My change is one
  markdown paragraph in `docs/adr/`, touching no Python, no shell, no workflow and no test; the suite
  floor and anchor floor cannot be moved by it. This is a scoping judgement, not a measurement, and
  it is the one place I traded coverage for time.
- **`ruff`/`mypy`.** Same reason - no Python file is in my diff. `git diff --stat` shows exactly one
  `.md` file.
- **Whether `REVIEW-R20.md:199-200` should carry a forward-pointer** to the corrected census. I ruled
  it a dated record and left it, but I did not check whether this project has a convention for
  annotating a superseded review finding. If one exists, that site is a candidate.
- **The other four kinds' exact historical spellings beyond the `Type:` line.** I derived the census
  from the `Type:` lines only. I did not read each of the 34 ADR bodies at `e3b5c97` to confirm the
  `Type:` line describes the file accurately - that is the instrument this project already chose, but
  it is an instrument, and a `Type:` line is a claim its body may not honour.
