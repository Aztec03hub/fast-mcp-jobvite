# REVIEW-R21 - the two rulings, and four counts that do not derive

<!-- REVIEW-COVERS: c749334..80463a5 -->

Reviewer: `review-r21`, task #206. Brief: `docs/briefs/BRIEF-R21-since-r20.md`.
Worktree `fmj-worktrees/r21`, branch `review/r21`, cut from **LOCAL `main`**
at `80463a5`. Nothing was fixed; nothing was pushed.

`docs/DESIGN.md` was read only as `git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md`
- the SHA DERIVED, never retyped: it resolves to **`d1f1a52`**
(`ADR-0035: the frozen selector could not match Both, ...`).

**2 High, 3 Medium, 3 Low, 4 nits.** Every finding ships a suggested fix.

---

## Corrections to the brief, before anything else

1. **The range is 26 commits, 22 files, +2397/-100 - not 25 / 21 / +2258/-100.**

       $ git rev-list --count c749334..80463a5
       26
       $ git diff --stat c749334..80463a5 | tail -1
       22 files changed, 2397 insertions(+), 100 deletions(-)

   The difference is exactly the brief's own commit `80463a5` and its
   139-line file. The brief's numbers were true when written and stale by
   the act of committing them. Not a defect, but it is the fifth count in
   this population whose edge moved.

2. **There are FOUR merges, not three.** `git log --merges --oneline c749334..80463a5`
   returns `7197271`, `73dd717`, `cd8c938`, `b9b59dd`. §C4 says three;
   `cd8c938` (fix/196-adr-citation-read) is the one not counted. I ran
   `git show --cc` on all four.

3. **`main` moved while I worked.** At dispatch `main` was `80463a5`; it is now
   `a612737` (`72fe217`, `04ad8e7`, `acb0f82`, `831018f`, `a612737`). My
   declaration is pinned to `c749334..80463a5` and nothing after it was
   reviewed. Two of those later commits close things I found - said where.

4. **`origin/main` is 54 commits behind `main`** (`git rev-list --count
   origin/main..main` = 54; `origin/main` is at `6e4fae3`). The brief says
   to derive the gap rather than trust a number; it is 54.

---

## H1 - the docstring's "re-derive without trusting this file" recipe MANUFACTURES the exact false finding the same file records as a published error

`docs/reviews/check-brief-report-references.py:83-86`, edited **in this
population** (the `docs/briefs/*.md` -> `docs/briefs` hunk):

    Re-derive the population without trusting this file:

        grep -rhoE '(REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+[.]md' \
          docs/briefs | sort -u

The gate's own selector, forty lines below at `:127-131`, is:

    REF = re.compile(
        r"(?<![A-Za-z0-9._-])"
        r"(docs/(?:reviews|worklogs)/)?"
        r"((?:REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+\.md)"
    )

and the comment directly above it, at `:117-126`, reads:

> THE LEFT BOUNDARY IS LOAD-BEARING AND ITS ABSENCE PUBLISHED A FALSE
> FINDING. Without `(?<![A-Za-z0-9._-])` this matches the TAIL of a longer
> name: `docs/CODE-REVIEW-CHECKLIST.md`, which exists and is cited by two
> briefs, was reported as `REVIEW-CHECKLIST.md`, which never has.

**The recipe omits that boundary.** Measured over `docs/briefs` at `80463a5`,
both selectors run in one pass:

    loose (the docstring recipe):  23
    tight (the gate's REF):        22
    in loose not tight: ['REVIEW-CHECKLIST.md']
    in tight not loose: []

The published recipe returns `REVIEW-CHECKLIST.md`, a file that has never
existed, which is the retracted false finding of `1985471` reproduced
verbatim by the paragraph that exists so a reader need not trust the file.
A reader who runs it gets 23 against the gate's 22 and reads the gap as a
gate MISS.

This is the population's clearest "a fix rebuilt its own defect one column
over": the same hunk fixed the recipe's *directory* edge (`docs/briefs/*.md`
-> `docs/briefs`, with three lines of prose about why a narrower
re-derivation is dangerous) and left the *left* edge loose. One edge of two.

**Suggested fix** - anchor derived from the file, not retyped. The recipe
must use PCRE for the lookbehind, so `-E` becomes `-P`:

    grep -rhoP '(?<![A-Za-z0-9._-])(?:REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+\.md' \
      docs/briefs | sort -u

and add one sentence: *"the lookbehind is the same one `REF` carries and is
not optional - without it this recipe returns `REVIEW-CHECKLIST.md`, the
name `1985471` retracted."* A recipe that cannot express the gate's
selector should print the gate's own population instead (`--list-names`),
rather than approximate it.

---

## H2 - the "five ADRs" count is right and the CLASS it counts is wrong: one of the five carries no citation at all, and another is the file's own counter-example

`docs/adr/README.md:54-64`:

> **NO SHA IS RETROFITTED INTO THE EXISTING ADRs** ... A "citations are
> against `<sha>`" line NEAR the citations **already exists in five of these
> files** - 0019, 0024, 0025, 0030, 0031, each naming a `DESIGN.md` blob with
> `git show <sha>:docs/DESIGN.md` - **and it does not work.**

The count of five verifies:

    $ grep -lE 'git show [0-9a-f]{7}:docs/DESIGN\.md' docs/adr/00*.md | wc -l
    5

**But the selector counts blob-naming lines, and the paragraph is about a
FORM.** The README says so itself at `:62`: *"The discriminator is naming a
`DESIGN.md` BLOB, not naming a commit."* That discriminator separates
blob-naming from commit-naming. It does **not** separate the NEAR form
(a sha in a nearby paragraph, citations left bare) from the BINDING form
(the sha inside the citation) - which is the only distinction this section
is drawing. Read one at a time with `grep -n`:

| ADR | its blob line | `DESIGN.md:N` citations in the file |
|---|---|---|
| 0019:18 | `Verified against the frozen object `git show 135c3ac:...`` | 4, all `:603` |
| 0024:15 | `` `git show c15b138:...`, lines 486-487: `` | 5 |
| 0025:117 | `` `git show 8a9d63c:...`, §4.5, lines 453-455 of that blob `` | 3 |
| 0030:29 | `The frozen design, `git show c15b138:...`, puts it in two places` | **0** |
| 0031:16 | `` `git show c15b138:...`, immediately above the table: `` | 3 |

Two of the five cannot support the claim:

- **`0030` carries ZERO `DESIGN.md:N` citations** (`grep -nE 'DESIGN\.md:[0-9]+'
  docs/adr/0030-*.md` returns nothing). A file with no line-numbered citation
  cannot demonstrate that a near-sha convention fails to stop citations
  drifting. It is a member of the count and not a member of the class.
- **`0025:117` is the README's own exemplar of the form that WORKS.** Twelve
  lines later, at `:71-73`, the same document says *"THE FORM THAT BINDS PUTS
  THE SHA INSIDE THE CITATION, and that exists too. `ADR-0025:117`:"* and
  quotes that identical line. `:117` is 0025's only blob-naming line. So 0025
  is simultaneously an instance of the failing NEAR form and the exemplar of
  the working BINDING form, in one file.

`0024:15` and `0031:16` also anchor within the named blob rather than sitting
apart from bare citations. **Genuinely NEAR-form-with-drifting-citations: one
- `0019` - which is the case the README already calls "the proof."**

The conclusion (*"do not retrofit"*) is not overturned by this; the evidence
for it is one measured case, not five. And the paragraph that makes this
error is the paragraph boasting about catching a loose selector two
sentences earlier (`:60-64`, twelve-versus-five). That is the class one
column over.

**Suggested fix** - rewrite `:54-64` in place (never append) to state what was
measured:

> A "citations are against `<sha>`" line already appears in five of these
> files - 0019, 0024, 0025, 0030, 0031 - but only **`0019`** carries it in the
> NEAR form this section is about: a sha in one paragraph and bare
> `DESIGN.md:N` citations elsewhere in the file. **0024, 0025 and 0031 anchor
> INSIDE the named blob, and 0030 carries no line-numbered citation at all.**
> So the near-form evidence is one file, and it is decisive: `ADR-0019:18`
> names `git show 135c3ac:docs/DESIGN.md` and all four of its `DESIGN.md:603`
> citations drifted anyway.

and delete `0025` from the sentence that indicts the near form, since `:71-73`
holds it up as the opposite.

**The two worked commands in the ruling both produce what it says.** Run
verbatim from the worktree:

    $ git log -S'DESIGN.md:2063' --reverse -- docs/adr/0034-*.md
    commit e3b5c97267799ac011c51edb8648121b49f40f94
        ADR-0034: DESIGN.md's "all eleven ADRs" is DELETED, not corrected
    rc=0
    $ git show e3b5c97^:docs/DESIGN.md | sed -n '2063p'
    1. **Recording a deviation from a `priority: required` standard.** This is the job all eleven ADRs
    rc=0

and `git show e3b5c97:docs/DESIGN.md | sed -n '2063p'` gives `... This is the
job the`, so the ADR's own applied change did falsify its own citation exactly
as claimed. The `git blame` warning is sound and I did not need to re-derive it.

---

## M1 - merge `7197271` describes the two versions BACKWARDS, and the resolution it kept is the one carrying the live citations

§C4 asks whether anything of `410e370`'s work was lost. **Nothing was.**

    $ git diff 410e370 7197271 -- docs/worklogs/WORKLOG-199-ratchet-defects.md
    (empty)

All 46 of the branch's worklog lines landed byte-identical. That half of the
message is true.

The *characterisation* is inverted. The commit message says:

> `suborch-199` reverted its own BRIEF-199 hunk ... **its version** removed
> only the phantom and **left two report names standing as live citations** -
> green, but green BECAUSE those two files happen to exist.

Measured on the blobs, with `grep -n` on each side:

    $ git show 410e370:docs/briefs/BRIEF-199-ratchet-defects.md | grep -nE 'REVIEW-|WORKLOG-'
    33:3. `docs/reviews/REVIEW-R20.md` - **M3 and L1 are yours.**

    $ git show 7197271:docs/briefs/BRIEF-199-ratchet-defects.md | grep -nE 'REVIEW-|WORKLOG-'
    33:3. `docs/reviews/REVIEW-R20.md` - **M3 and L1 are yours.**
    67:`1985471`, `WORKLOG-187-floor-container.md`, `REVIEW-R20.md` - and **the

`410e370`'s line 67 reads *"one phantom name that a regex invented, one
in-flight worklog, and one in-flight review report"* - **it names none of the
three.** The KEPT resolution is the one that writes out
`WORKLOG-187-floor-container.md` and `REVIEW-R20.md`, i.e. the one whose
green depends on those two files continuing to exist. The property the
message assigns to the revert belongs to the side that was kept.

That does not make the resolution wrong - it also kept the class statement
and the forward pointer, which the revert dropped, and the ruling committed
the same hour says the false positive is ACCEPTED anyway. But the merge
message is the only record of this decision and it states the trade backwards,
so the next reader will believe the kept text is the more robust of the two.

**Suggested fix** - one sentence rewritten in place in the merge's own record.
Since a commit message cannot be edited without a rewrite (and `CONTRIBUTING`
records that history is not rewritten here), correct it where it will be read:
add to `docs/worklogs/WORKLOG-199-ratchet-defects.md` a dated line -

> **Correction to `7197271`'s message.** It says the revert *"left two report
> names standing as live citations"*. Measured on both blobs, `410e370`'s
> BRIEF-199:67 names none of the three and the KEPT resolution names two
> (`WORKLOG-187-floor-container.md`, `REVIEW-R20.md`). The resolution is still
> the right one - it keeps the class statement the revert dropped - but the
> robustness point runs the other way.

---

## M2 - the fix for R20-M2, a COUNT finding, restates a count that is short by one and omits its own row

`docs/adr/0034-the-adr-count-in-design-md-is-deleted-not-corrected.md:58-60`,
added in this population at `2514990`:

> **THIS TABLE IS NOT THE ACCEPTANCE CENSUS AND SAID IT WAS.** It was labelled
> "AT ACCEPTANCE" until R20-M2 checked: at `e3b5c97` the partition read
> `17 / 14 / 1 Standards deviation / 1 Correction to a contract statement`,
> **total 33.**

Measured at `e3b5c97`, over every ADR file in the tree at that commit:

    ADR files:            34
    **Type:** lines:      34
     1  Correction to a contract statement that an implementer can satisfy ...
     1  Correction to a count that is false about its own subject
    17  Design change
    14  Deviation
     1  Standards deviation

**Five kinds, total 34.** The amendment lists four kinds and totals 33. The
missing row is `Correction to a count that is false about its own subject`,
and the file carrying it is `docs/adr/0034-...md` - **this ADR itself**, the
one being added by `e3b5c97`. The same omission is in `e3b5c97`'s own commit
message (*"There are 33"*), and the R20-M2 fix copied it forward instead of
re-deriving. The identical four-row list appears a second time at `:72`.

The kept table is correct: at `d29937f` the partition really is
`19 Design change / 15 Deviation`, total 34, which is what `:49-55` now claims.
Only the historical census is wrong.

**Suggested fix** - rewrite `:58-60` and `:72` with the derived figure:

>  ... at `e3b5c97` the partition read `17 Design change / 14 Deviation /
> 1 Standards deviation / 1 Correction to a contract statement / 1 Correction
> to a count that is false about its own subject`, **total 34 - and the fifth
> row is this ADR.** `e3b5c97`'s own message says 33 because it counted the
> corpus it was adding to and not the file it was adding.

Re-derive rather than retype, with the file's own command pointed at the blob:

    git ls-tree --name-only e3b5c97 docs/adr/ | grep -E '^docs/adr/[0-9]' \
      | while read -r f; do git show "e3b5c97:$f" | grep -h '^\*\*Type:\*\*'; done \
      | sort | uniq -c

---

## M3 - the citation-vs-quotation ruling's SECOND refusal is argued backwards by its own measurement

`docs/reviews/check-brief-report-references.py:69-72`:

> - **A syntax split**, counting only path-qualified forms as citations and
>   treating a bare basename as prose. Refused because it is FALSE HERE:
>   `suborch-199` measured six names cited BOTH ways, so the bare form carries
>   real citations and **the split would drop them.**

The measurement is right. Partitioning the 22 cited names by whether each
appears with a `docs/(reviews|worklogs)/` prefix, without a prefix, or both:

    BOTH ways:  6  REVIEW-R16/R17/R18/R19/R20.md, WORKLOG-187-floor-container.md
    PATH only: 14
    BARE only:  2  FINDINGS-168-range-before-paths.md, REVIEW-R21.md

**A name cited BOTH ways is still caught by its path-qualified citation.** A
syntax split drops nothing for those six - they are the evidence *for* the
split's safety, not against it. What a split would actually drop is the
bare-only set: two names, of which `docs/reviews/FINDINGS-168-range-before-paths.md`
is tracked (so it is not a detection at all), and `REVIEW-R21.md` is the
in-flight forward reference the ruling exists to tolerate. **Today the split
would drop ZERO live detections.**

The conclusion may still be right - a split invites a bare-only citation to a
genuinely lost report to pass silently, and that is a real hazard - but the
stated reason is the opposite of what the numbers say, and it is the reason
the next reader will inherit.

**Suggested fix** - rewrite the bullet:

> - **A syntax split**, counting only path-qualified forms as citations. The
>   six names `suborch-199` measured as cited BOTH ways would still be caught
>   by their path form, so the split loses nothing there. It is refused for
>   the residual: **2 of 22 names are cited ONLY bare**, and a split makes a
>   bare-only citation to a genuinely lost report pass in silence - the exact
>   defect this gate was built after. A hole that opens only for the careless
>   citation form is worse than a false positive that costs a sentence.

**The other two refusals hold and I checked both.** The `EXEMPT`-marker
precedent (47 -> 61 purely from prose about the marker) is the recorded
measurement and the argument transfers exactly: this docstring would itself
inflate the population. And
`docs/reviews/brief-report-refs-known-missing.txt:9-12` does say *"Recording a
line is NOT a waiver"*, so recording a name that never existed is refused for
the reason given.

---

## L1 - `ci.yml`'s new comment credits #187 with a widening it did not finish, and freezes a live count into prose

`.github/workflows/ci.yml:1203`, added at `a6430ba`:

    # #187 widened that checker's container from 25 members to 32, and a

`789d3be`, suborch-187's own commit, says:

    CONTAINER, BEFORE: 25 checked for exactness, exit 0.
    CONTAINER, AFTER:  30 checked, exit 0.

and `65fabe4` (the fold, in this population) says *"suborch-187 widened
check-row-floor-exactness.py's container from 25 members to 32 by KIND. **I
had, on the other side of the merge, added two** ..."* - the sentence names
the second author in its own next clause and still attributes the whole
delta to the first. **#187 did 25 -> 30; the merge did 30 -> 32.** The
`ci.yml` comment copied the wrong-edged sentence forward.

Second half: 32 is a live figure. The checker prints it -

    $ uv run --frozen python docs/reviews/check-row-floor-exactness.py
    CONTAINER: tracked .py, .sh under docs/reviews/, scripts/ carrying a literal floor
      members (floor > 0)                                   32
    exactness_rc=0

- and it moves whenever a harness gains a floor. Writing it into a YAML comment
makes a second copy, in the same population where
`check-checkers-are-wired.py` **deleted its own digits** for exactly this
reason (*"The property is stated; the digits are not"*). The sibling was not
swept.

**Suggested fix** - replace `:1203` with the property:

    # THE SIXTEEN ARMS OF THE STEP ABOVE, run by nobody until this landed.
    # #187 rebuilt that checker's container as a KIND rather than a glob, and
    # the fold at 65fabe4 added two more members; the live census is printed
    # by the step above under `CONTAINER:`. A container change to a gate with
    # its own control table is exactly the thing whose arms need running.

(The "sixteen arms" in that same comment IS derivable and IS current - the
`--self-test` prints `rows=16 floor=16 fired=16/16` - and
`check-row-floor-exactness.py` gates its own floor at equality, so it cannot
drift silently. Left as written.)

---

## L2 - the ruling's "all 64 citations in this directory" was falsified by the commit that wrote it

`docs/adr/README.md:28-29`:

> **MEASURED, all 64 `DESIGN.md:N` citations in this directory read one at a
> time ... 46 DRIFTED, 14 CORRECT, 2 WRONG, 2 boundary.**

Present tense, "in this directory". Measured at `80463a5`:

    $ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l
    68
    $ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l
    20

Excluding `README.md` it is exactly 64 across 19 - the read really was
complete. The extra four are `README.md:38`, `:47`, `:65`, `:67`, all added by
`ec57a65`, the ruling itself. **The paragraph asserting that 64 citations were
read added four more to the directory it is counting**, which is precisely the
ADR-0034 shape it narrates eight lines below (*"The ADR's own accepted change
falsified its own citation"*).

It is also the OTHER ruling's class: those four are quotations, not citations,
and the two rulings are in tension about whether a selector can tell them
apart.

**Suggested fix** - name the population's boundary instead of leaving it to a
naive grep:

> **MEASURED, all 64 `DESIGN.md:N` citations carried by the ADRs themselves -
> `docs/adr/0*.md`, 19 of the 35 files - read one at a time
> (`docs/reviews/CITATION-READ-ADR-VERDICTS.md`): 46 DRIFTED, 14 CORRECT,
> 2 WRONG, 2 boundary.** (This README quotes four more while discussing them;
> a bare `grep` over the directory now returns 68, which is the
> citation-versus-quotation class ruled in
> `check-brief-report-references.py`'s docstring, one corpus over.)

---

## L3 - the ruling's own evidence document still prescribes the remedy the ruling refuses

`ec57a65` rules that DRIFTED ADR citations **are not repointed**. Its evidence
document, merged one commit earlier at `cd8c938`, still says at
`docs/reviews/CITATION-READ-ADR-VERDICTS.md:56-57`:

> ... point at text that was the cited subject when the citation was written
> and is something else today. **The remedy is a repoint;** the remedy for a
> WRONG one is a repoint *and* an explanation ...

The document is internally consistent about what it DID (`:159`, `:237-238`:
*"I did NOT repoint these"*), but the sentence a reader lands on when checking
what a DRIFTED verdict means still prescribes repointing 46 sites. A verdict
document is the operating instruction for the next sweep; this one and the
ruling now disagree about what a DRIFTED row obliges.

Separately, the *"enumerated rather than inherited"* block at `:29-35` prints
`64 / 19 / 36`. Those were true at `9b3e85f` and are `68 / 20 / 36` now, for
the reason in L2. A dated measurement block is legitimate - it is not labelled
as one.

**Suggested fix** - two edits in place, no appendix:

- `:56-57`: *"... and is something else today. **The remedy is NOT a repoint:
  `#203` ruled at `ec57a65` that an ADR's citations are as at its acceptance
  and stay** (`docs/adr/README.md`, the as-at-acceptance section). A WRONG one
  is a different defect - it never named its subject - and is repointed, with
  an explanation of how the author read the wrong paragraph."*
- `:26`: head the command block **`THE POPULATION AS AT 9b3e85f`**, so a reader
  who re-runs it and gets 68 knows why.

---

## Nits

**N1 - `docs/adr/README.md`'s index table stops at 0023; twelve ADRs are missing
from it.** The table runs `:81-105`, last row `[0023]`. `ls docs/adr/[0-9]*.md
| wc -l` is 35. ADRs 0024-0035 are absent, including `0034` and `0035`, which
the new ruling section cites by number twenty lines above the table. This
pre-dates the population, but the ruling made the README a document readers
now open. The same file argues at `:19-21` that *"a classification that lives
only in the index is not carried by the artifact a reader opens"*; the inverse
now holds too. **Fix:** the table is a derived record - generate it, or add the
twelve rows and a line saying the index is checked (a five-line checker over
`ls docs/adr/[0-9]*.md` versus `grep -c '^| \[' README.md` would gate it, and
`check-row-floor-exactness.py`'s both-directions equality is the pattern).

**N2 - at `80463a5` the tree is RED on a gate CI runs.** Read on its own line:

    $ uv run --frozen python docs/reviews/check-brief-report-references.py
    ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
      REVIEW-R21.md   cited by BRIEF-R21-since-r20.md
    brefs_rc=1

The record file holds zero entries (comments only), so `80463a5` shipped a
brief whose forward reference had no in-flight line. **Already closed at
`72fe217`**, outside my range, which records it and says the routine now lives
in the record file - *"the line belongs in the same commit as the brief."*
Reported because it was true at my population head and because the remedy is
the right one. **Fix:** none needed; `72fe217` did it. My report landing clears
the citation.

**N3 - `check-review-coverage.py` measures `origin/main`, so none of this
population is visible to it.** Its own output says *"Trunk commits on
origin/main since 8695101: 370"*, and `origin/main` is 54 commits behind. The
backlog holds at 66 and every gate passes, but the R21 declaration in this file
is inert until the push lands - it certifies nothing today, and will certify
`c749334..80463a5` the moment `main` is pushed. Worth saying because a holding
ratchet over a 54-commit-stale trunk reads as coverage it is not yet providing.
**Fix:** nothing to change; the checker is behaving correctly. If it is worth a
line, have it print `origin/main is N commits behind main - N commits are not
yet in this population` so the gap is visible in the gate's own output rather
than derivable only by hand.

**N4 - `A21`/`A22` hand-roll the row line, and it is fine - I checked.**
`check-brief-report-refs-controls.sh:288-319` increments `ROWS` and `FIRED`
inline instead of calling `row`, which the file's own header at `:41-42` warns
about (*"Hand-rolling the line is what made this floor unwatchable (#194)"*).
That warning is about the canonical `HARNESS-RESULT` line, not about row
accounting, and these two arms have to bypass `run()` because it hardcodes
`--briefs "$tmp/briefs"`. Both counters are maintained correctly - the harness
prints `rows=22 floor=22 fired=22/22` and `ROWS -ne ROW_FLOOR` would catch a
lost row. `b7b58b0`'s message already records the consequence (`grep -c '^ *row
"'` is 20 against a floor of 22, tracked as `EXTRA 2`), and I confirmed both:
`grep -c '^ *row "'` returns 20, a run prints `rows=22`. **Fix (optional):**
give `run()` an optional briefs-dir argument so A21/A22 can use `row`, and
`EXTRA` drops to 0 - one fewer standing exception in the control table.

---

## Things I checked and AGREED with R20 / the fixes

- **`set -uo pipefail` does not disable errexit** (§C6). Re-measured myself,
  under the shell GitHub uses, each exit code on its own line:

      $ bash -e /tmp/r21e1.sh      # set -uo pipefail; false; echo REACHED
      e1_rc=1                      # nothing printed - errexit STILL ON
      $ bash -e /tmp/r21e2.sh      # set +e; false; echo REACHED
      REACHED
      e2_rc=0                      # errexit OFF

  `check-checkers-are-wired.py`'s rewritten paragraph is correct, and its
  conclusion - the selector is a SUPERSET so the zero survives - follows.

- **The `|| exit 1` removal on the brief-report step** (`ci.yml:1276`) is right
  and its stated reason is right: `|| exit 1` would map exit 2 onto 1 and
  collapse the refusal that arm A5 exists to prove. Verified A5 returns 2 and
  A20 (its amputation) returns 1.

- **Both `-lt` -> equality floor changes** (`probe-131-gate-state.sh:333`,
  `probe-wired-checker-amputation.py:392`) close the exact hole #193 named:
  these two are the only container members whose row count is COMPUTED, so the
  exactness checker cannot see a slack floor in them. Confirmed by the census:
  *"of those, row count COMPUTED at run time (#193): 2"*, naming those two files.

- **`probe-mirror-zero-refs.sh`'s defaulted `$1`** is not a convenience: with
  `${1:?}` the floor control ran it with no argument and got exit 3, so its
  floor could never be watched. Correct diagnosis, correct fix.

- **`check-row-floor-controls.sh`'s `basename` fix** (`:380-388`) is the real
  #194 root cause - `harness_result_emit` uses `basename "$0"` and the grep
  composed the expected `name=` from a path-qualified `$TARGET`. The two facts
  were introduced separately and never joined, exactly as the comment says.

- **The four merges.** `b9b59dd` and `cd8c938` are clean. `7197271` is
  covered in M1 above; `73dd717` is covered in the correction below,
  which is where its combined diff is finally read.

  > **CORRECTION, 2026-09-02, by the orchestrator ruling #231B.** This bullet
  > used to say *"`git show --cc` on all four produces an empty combined diff,
  > i.e. every file in each result matches one parent - no third version was
  > invented at any merge."* **That is false, and one command shows it:**
  > `git show --cc --format= 73dd717 | wc -c` returns **7226**, and the combined
  > diff carries a third version of `docs/briefs/BRIEF-199-ratchet-defects.md`
  > present in neither parent. **`--format=` is load-bearing**: without it the
  > commit message is in the count, which is where this correction's own first
  > version got 11376. 7226 is what `check-merge-invented.py` prints as
  > `cc=7226B` and what `#222` recorded. The two CLEAN verdicts are correct and
  > are kept - the detector independently reports `invented=0` for both
  > `b9b59dd` and `cd8c938`. What is removed is the UNIVERSAL.
  >
  > **AND THIS REPORT DID NOT CONTRADICT ITSELF ELSEWHERE, WHICH IS WORSE.** The
  > first version of this note said item 2 of *"Corrections to the brief"* had
  > already contradicted the universal. It does not: it corrects the BRIEF's
  > merge COUNT to four and ends *"I ran `git show --cc` on all four"* - this
  > report asserting it ran the very command that refutes it. Found by
  > `review-231b`, which also measured that the two passages are ten headings
  > apart, not the eighteen first claimed.
  >
  > The correction is here rather than in a later document because this
  > sentence is load-bearing: this report's whole-tree
  > `REVIEW-COVERS: c749334..80463a5` is what clears `73dd717` in
  > `check-review-coverage.py`, so a reader reaches a coverage green through
  > this claim. See #231B for the ruling it produced.
  >
  > **WHY THIS IS A RIDER AND NOT A REWRITE, which #93 would otherwise
  > forbid.** #93 governs a stale ADDRESS - a citation that rotted as the
  > tree moved, where the original wording was right when written. This
  > sentence was FALSE THE DAY IT WAS WRITTEN, and the bullet above it is
  > rewritten in place accordingly. What is kept as a dated block is the
  > EVIDENCE and the provenance, because a reader who finds a coverage
  > green through this document needs to know it was corrected and by
  > what measurement. `docs/reviews` is deliberately NOT in the live
  > gate's RECORD_PATHS, so a review document here is work, not an
  > unedited record.

- **Counts in the 26 commit messages that DO derive**, each re-run:
  `grep -lE 'git show [0-9a-f]{7}:docs/DESIGN\.md' docs/adr/00*.md` -> 5;
  19 ADR files carrying a `DESIGN.md:N` citation; 46/64 = 72%;
  20 of 22 cited names path-qualified; six names cited both ways;
  `grep -c '^ *row "'` = 20 against `rows=22`;
  `WRONG-SUBJECT-REGISTER.md`'s `grep -c '^| WS-'` = 33 and its
  10+19-1+3+2 = 33 arithmetic and its 18+9+1+1+1+1+2 = 33 `Where` tally both
  close; ADR-0034's `d29937f` partition 19/15 = 34.

---

## §E gates, each exit code on its own line

Run from `fmj-worktrees/r21` at `80463a5`, clean tree, no `&& echo OK` anywhere.

    uv run --frozen python docs/reviews/check-review-coverage.py
    coverage_rc=0        # backlog 66 recorded / 66 measured, 0 entered, 0 cleared

    uv run --frozen python docs/reviews/probe-coverage-ratchet.py
    ratchet_rc=0         # 10/10 arms, backlog entries drawn from: 66

    uv run --frozen python docs/reviews/check-brief-report-references.py
    brefs_rc=1           # RED - REVIEW-R21.md cited by BRIEF-R21; see N2

    bash docs/reviews/check-brief-report-refs-controls.sh
    controls_rc=0        # 22/22 fired, rows=22 floor=22 status=ok

    uv run --frozen python docs/reviews/check-row-floor-exactness.py
    exactness_rc=0       # 32 harnesses, 8 both-floors, 16 --min-rows compared

    python3 docs/reviews/check-row-floor-exactness.py --self-test
    selftest_rc=0        # rows=16 floor=16 fired=16/16 status=ok

`brefs_rc=1` is the only red and it is N2. Committing this report is what
clears it; I re-ran the gate after committing and recorded the result in my
delivery message.

**actionlint is NOT installed in this environment.** I did not run it and I do
not claim that gate. I also did not run `pytest`, `ruff`, `mypy` or
`shellcheck` - see below.

---

## What I did NOT verify

- **The suite and the anchor floor.** I did not run `uv run --frozen pytest`
  or `check-harness-anchors.py --self-check`. This population touches no
  `src/` or `tests/` file (`git diff --stat` lists only `.github`, `docs/`),
  so neither floor can have moved from this range - but I did not prove that
  by running them, and "no test file changed" is an argument, not a measurement.
- **actionlint on the two `ci.yml` hunks.** Not installed here. The new
  `--self-test` step's command I DID run directly (`selftest_rc=0`), and the
  `|| exit 1` removal I reasoned about from the checker's exit codes rather
  than from a workflow parse.
- **Whether the `0024`/`0031` blob lines are "binding" in the strong sense.**
  `0024:15` names a blob and then quotes `lines 486-487`; `0031:16` names a
  blob and says *"immediately above the table"*. Both anchor inside the named
  object, which is why I excluded them from the NEAR class - but neither uses
  `0025:117`'s explicit *"of that blob"* wording, so a stricter reading could
  put them back. I state the ambiguity rather than resolve it; `0030` (zero
  citations) is not ambiguous and settles the finding on its own.
- **Whether the syntax split in M3 is the right call.** I measured that its
  stated reason is backwards. I did not measure the counterfactual - how often a
  bare-only citation names a genuinely missing report over the project's whole
  history - which is what would actually decide it. That is a Tier 0 ruling,
  not a finding, and I have not filed a task for it.
- **The five commits after `80463a5`.** `72fe217`, `04ad8e7`, `acb0f82`,
  `831018f`, `a612737` landed while I worked and are outside my declared range.
  I read `72fe217`'s message only, to check whether N2 was already closed.
- **CI.** Nothing in this population has run through CI once. The trunk's one
  green run (`33582613697`) predates all of it.

---

Worktree `fmj-worktrees/r21` is **left in place** - the report is committed on
`review/r21`, and Tier 0 removes the branch's worktree when it merges or
discards it. Nothing outside `docs/reviews/REVIEW-R21.md` was written.

**Range declared once, in the HTML comment directly under the heading**, which
is where `check-review-coverage.py` reads it (`PREAMBLE.md`, "How to deliver").
The brief's §D asks for it at the END; a second copy is a second place for a
range to drift, so there is one. **No `PATHS:` filter** - the brief gave me no
path split and I read the whole 22-file tree over `c749334..80463a5`, which is
the broad claim and is true.
