# WORKLOG #210 #215 #216 #217 - the ADR-citation ruling's EVIDENCE

Agent `suborch-210`. Brief: `docs/briefs/BRIEF-210-adr-ruling-evidence.md`.
Worktree `/tmp/w210-adr-ruling-evidence`, branch `fix/210-adr-ruling-evidence`, cut from
`a52af14`. Findings read from `git show 1045edb:docs/reviews/REVIEW-R21.md`.

This is a FIX worklog, not a code review, so it declares no `REVIEW-COVERS` range.

**THE RULING IS UNTOUCHED.** ADR citations are AS AT acceptance and are NOT repointed
(`ec57a65`). Every edit below is to the EVIDENCE.

---

## HEADLINE: R21-H2 reached the right conclusion by a route that is wrong in BOTH halves

`review-r21` concluded that only `ADR-0019` carries the near form and that the README's
"five" is a count without a class. **That conclusion holds.** Its two stated reasons do
not, and its suggested replacement prose would have installed two new false statements in
the document it was fixing.

### Reason 1 - "0030 carries no line-numbered citation at all" is FALSE

`ADR-0030` carries TWO, three lines under its blob line, in the BARE form:

    $ grep -n '`:[0-9]\+\(-[0-9]\+\)\?`' docs/adr/0030-the-upstreams-retry-hint-is-dropped-on-every-shape-but-two.md
    31:- `:356-359` - an open breaker and an outage share `/problems/service-unavailable`...
    33:- `:361-362` - *"Jobvite's `429`, if it exists, is retried and then mapped to 503...

They omit the filename, so `grep -E 'DESIGN\.md:[0-9]+'` returns a clean zero for that
file - **the exact class task #204 exists for.** R21 ran that selector, got the zero, and
read it as an absence.

**Both drifted, and I measured it in both directions.** Against the blob 0030 names at
`:29` (`c15b138`) and against the freeze derived from `docs/DESIGN-FREEZE.txt` (`d1f1a52`):

    $ git show c15b138:docs/DESIGN.md | sed -n '356,359p'
    - **An open breaker is distinguishable from an outage without inventing a type.** Both use
      `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail`,
      ... plus a `retry_after` hint.
    $ git show d1f1a52:docs/DESIGN.md | sed -n '356,359p'
    Ordered timeout, then retry, then circuit breaker.
    - **Timeouts explicit and per-phase.** No SDK default, no single scalar.
    ...
    $ git show c15b138:docs/DESIGN.md | sed -n '361,362p'
    - **Jobvite's `429`, if it exists, is retried and then mapped to 503**, honouring `Retry-After`
    $ git show d1f1a52:docs/DESIGN.md | sed -n '361,362p'
      inbound request's deadline, because there is no inbound deadline here - see the note below.

**So `ADR-0030` is not the member of the count that cannot join the class. It is the
TIGHTEST case in the set** - the sha is three lines above the citations, which is the
strongest proximity binding anywhere in `docs/adr/`, and it still failed. Deleting it
from the evidence, as R21 proposed, would have deleted the best instance.

It was also never READ. `CITATION-READ-ADR-VERDICTS.md` selected on `DESIGN\.md:[0-9]+`,
so 0030's two sites are outside the 64 and carry no verdict row.

### Reason 2 - "0024, 0025 and 0031 anchor INSIDE the named blob" is INCOMPLETE

True of the ONE line R21 read in each; false of the files. Each of those blob lines is a
QUOTE INTRODUCER binding one quotation, and each file separately carries bare
`DESIGN.md:N` citations, **every one of which DRIFTED**
(`CITATION-READ-ADR-VERDICTS.md`, the DRIFTED table at its `| ADR | Sites |` rows):

    0024  5 sites  486-487 x2, 469-477, 373-375, 425-427   all DRIFTED
    0025  3 sites  373-375 x3                              all DRIFTED
    0031  3 sites  513-521, 510, 356-359                   all DRIFTED

Spot-checked three of those against the freeze by hand; the verdict document's "what it
says now" column is accurate for each.

Writing R21's sentence - *"0024, 0025 and 0031 anchor INSIDE the named blob"* - into the
README would have asserted that eleven drifted citations do not exist.

### The discriminator that actually separates the five

Read one at a time, the five split by **what the sha line CLAIMS**, not by where it sits:

    0019:18  "Verified against the frozen object `git show 135c3ac:docs/DESIGN.md`:"
             a SCOPE declaration - the only one
    0024:15  "`git show c15b138:docs/DESIGN.md`, lines 486-487:"          quote introducer
    0025:117 "`git show 8a9d63c:docs/DESIGN.md`, §4.5, lines 453-455 of that blob"  ditto
    0030:29  "The frozen design, `git show c15b138:docs/DESIGN.md`, puts it in two places"  ditto
    0031:16  "`git show c15b138:docs/DESIGN.md`, immediately above the table:"     ditto

So the README's phrase *"a citations-are-against-`<sha>` line ... exists in five of these
files"* describes ONE of them. **But its conclusion is stronger than either document
said**: all five carry line-numbered citations that drifted anyway, whether the sha
declared a scope (0019), introduced a quotation (0024/0025/0031), or sat three lines above
them (0030). The near form fails in every shape it takes here.

### 0025 as its own counter-example - R21 was RIGHT, and the resolution is not deletion

`0025:117` is quoted by the same README as THE FORM THAT BINDS. R21 asked for 0025 to be
struck from the sentence indicting the near form. **It does not need striking; it needs
its scope stated.** `:117` binds ITS OWN quotation and nothing else, and the file's three
`DESIGN.md:373-375` citations sit outside it and all drifted. That is not a contradiction
- it is the boundary of the binding form, and saying it makes the section stronger.

---

## What was changed

### `docs/adr/README.md` - the near-form section, REWRITTEN IN PLACE

No rider, no appendix. The section now states the split above, names 0030 as the tightest
case with its two-blob command pair, gives the per-file drift table, and ends the
binding-form paragraph with the scope sentence. The loose-selector parenthetical is kept
and **corrected**: it used to record one loose edge; it now records that the SECOND
selector was loose too, one column over - it counts blob-naming LINES where the section is
about a FORM, which is how four quote-introducers became scope declarations and how 0030's
bare citations became an absence.

Also fixed the typo `a agent` in that parenthetical, which the rewrite subsumed.

### `docs/adr/README.md:28-` - #215, the population boundary

*"all 64 in this directory"* is now *"all 64 carried by the ADRs THEMSELVES -
`docs/adr/0*.md`, 19 of the 35 numbered files"*, and it carries the command that produces
it. Measured at `a52af14`:

    $ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l
    64
    $ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l
    19
    $ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l
    68

**I DISAGREE WITH THE BRIEF'S PREFERENCE HERE, AND SAY SO IN THE OPEN.** The brief said
*"prefer DELETING the number to correcting it"* under ADR-0034. ADR-0034's remedy applies
to a count that CANNOT be maintained. `64/19` is exact today over a population named by
path, and the verdict document that produced it is cited; it is a dated measurement, not a
live census. So the figure stays and carries its command, which the brief explicitly
permits.

**A number I did DELETE, and the reason is the finding eating its own fix.** My first draft
wrote `# 68` beside the directory-wide grep. My own rewrite quotes three more citations
while explaining them, so the directory total became **71 the moment I saved the file** -
the finding rebuilt one column over inside its own remedy. There is now no total for
`docs/adr/*.md` in the README at all: it moves whenever the file discusses a citation, so
under ADR-0034 it is deleted, not corrected. The `docs/adr/0*.md` figure is unaffected
because the README is not in that population, which is the whole point of naming it.

### `docs/reviews/CITATION-READ-ADR-VERDICTS.md` - #216, two edits in place

- The DRIFTED definition no longer prescribes a repoint. It now states the `#203` ruling
  at `ec57a65` by name and section, keeps the WRONG-is-repointed half with its reason
  (a WRONG citation never named its subject, so there is no as-at reading to preserve),
  and records WHY the sentence survived the ruling: the paragraphs saying what this round
  DID are not the ones a reader lands on when checking what a verdict OBLIGES.
- The population block's heading is now **AS AT `9b3e85f`**, with a following paragraph
  saying the first two numbers are higher today and nothing is wrong, and giving the
  `docs/adr/0*.md` form that still returns 64/19.

### #217 - the index table, and the gate

Twelve rows added (0024-0035), each derived by reading the file's own `# ADR-NNNN:`
heading and `**Status:**` line, not invented. Measured before:

    $ grep -cE '^\| \[[0-9]{4}\]' docs/adr/README.md     23
    $ ls docs/adr/[0-9]*.md | wc -l                      35

**Nothing regenerated this table, and nothing would have caught it going stale again.**
The brief asked me to say which. Answer: nothing did, so I wired one.

**The gate is folded into `check-adr-numbers.py`, which is ALREADY wired at `ci.yml:1553`,
rather than being a new checker.** That is a deliberate departure from the R21 suggestion
("a five-line checker"): a new `docs/reviews/check-*.py` becomes a member of
`check-checkers-are-wired.py`'s container the moment it lands, so a new file would have
demanded a new `ci.yml` step - and `ci.yml` is the orchestrator's. Folding it in adds a
gate and zero wiring surface. The step's `name:` and its `::error::` line are widened to
say so; no new step.

It compares `ls docs/adr/[0-9]*.md` against the table's `| [NNNN](file.md) |` rows
**equal in both directions, plus the link target**, because the failures are different: a
file with no row is an ADR the index cannot find; a row with no file is a link that 404s;
a row pointing at the wrong file resolves and lies.

---

## Controls - the gate proved able to FAIL, six ways, plus the pre-fix arm

Run against a COPY of the tree under `/tmp` so no mutation could be stranded in the
worktree. Each exit code read on its own line.

    ARM 1  a FILE with no ROW (0035's row deleted)              rc=1  NO ROW   0035
    ARM 2  a ROW with no FILE (0036 invented)                   rc=1  NO FILE  0036
    ARM 3  a row whose LINK points at another ADR's file        rc=1  BAD LINK 0034
    ARM 4  the index ABSENT                                     rc=1  NO INDEX (refusal, not a clean zero)
    ARM 5  the index present with ZERO rows                     rc=1  MATCHED ZERO INDEX ROWS
    ARM 6  one ADR listed TWICE                                 rc=1  lists these twice: 0030
    RESTORE  unmutated copy byte-identical to source            diff rc=0

**THE PRE-FIX ARM IS THE ONE THAT MATTERS.** The new checker, run against
`git show a52af14:docs/adr/README.md` (23 rows):

    prefix_rc=1, naming all twelve: NO ROW 0024 ... NO ROW 0035

and the OLD checker from `a52af14`, against that same 23-row README:

    ADRs: 35, numbered 0001-0035
    Every ADR number is unique, contiguous, and matches its own heading.
    oldchecker_rc=0

**The gap was invisible to the gate that existed.** That is the finding, measured rather
than asserted.

---

## §E gates, each exit code on its OWN line

Run from the worktree at the final tree.

    python3 docs/reviews/check-adr-numbers.py                     adr_numbers_rc=0
      "35 ... README.md's table lists all 35 of them and nothing else."
    python3 docs/reviews/check-design-citations.py                design_citations_rc=0
    python3 docs/reviews/check-design-freeze.py                   design_freeze_rc=0
      d1f1a52 and HEAD are the same blob 61e264d3...
    python3 docs/reviews/check-cross-references.py                cross_references_rc=0
    python3 docs/reviews/check-coupling-sweep.py                  coupling_sweep_rc=0
    python3 docs/reviews/check-resweep-verdicts.py                resweep_rc=0
    python3 docs/reviews/check-review-coverage.py                 review_coverage_rc=0
      "The backlog holds at 66, every commit recorded."
    python3 docs/reviews/check-row-floor-exactness.py             row_floor_exactness_rc=0
    python3 docs/reviews/check-row-floors.py                      row_floors_rc=0
    python3 docs/reviews/check-landing-published.py               landing_rc=0
    python3 docs/reviews/check-clause-citations.py                clause_rc=0
    python3 docs/reviews/check-no-errexit.py                      no_errexit_rc=0
    bash docs/reviews/check-brief-report-refs-controls.sh         brefs_controls_rc=0
      HARNESS-RESULT ... rows=22 floor=22 fired=22/22 status=ok
    bash docs/reviews/check-harness-result.sh                     harness_result_rc=0
      EQUAL: all 38 scripts in the container emit the canonical line.
    uv run --frozen python docs/reviews/check-checkers-are-wired.py            wired_rc=0
    uv run --frozen python docs/reviews/check-checkers-are-wired.py --self-test  wired_selftest_rc=0
      run steps parsed: 93; 35/35 controls passed.
    python3 scripts/check-harness-anchors.py --self-check --floor 464          anchors_rc=0
      floor DERIVED from ci.yml, never retyped
    uv run --frozen ruff check .                                  ruff_rc=0
    uv run --frozen ruff format --check .                         ruff_format_rc=0  (140 files)
    uv run --frozen mypy                                          mypy_rc=0  (140 source files)
    python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"  yaml_rc=0
    uv run --frozen pytest -q                                     pytest_rc=0
      887 passed, 6 deselected in 57.03s - ZERO skipped.
      Floor DERIVED: `grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml`
      -> `check-suite-floor.sh 887`. 887 >= 887. The 6 deselected are `ci.yml`'s own
      marker deselection, which is not a skip.

**`actionlint` is NOT INSTALLED in this environment** (`command -v actionlint` finds
nothing). It was not run and nothing here claims it was.

**`ruff check` was RED on my own work before it was green.** `W505 Doc line too long
(73 > 72)` at `check-adr-numbers.py:69`, in a docstring I had just written. Rewrapped, then
re-run to `rc=0`. Recorded because a gate run only after the commit message is written is
the failure this project keeps measuring.

---

## TWO REDS THAT ARE NOT MINE, AND MAIN IS CARRYING BOTH

Reported loudly per the brief. Neither is in a file I touched; my diff is four files
(`git diff --stat a52af14` below) and neither red is in any of them.

### RED 1 - `check-design-citation-shape.py` exits 1, on `main` and at `a52af14`

    citation_shape_rc=1
       2  starts on a BLANK line (the off-by-one shape)
            docs/reviews/probe-204-orphaned-by-repoint.py:7   DESIGN.md:489-490
            docs/reviews/probe-204-orphaned-by-repoint.py:70  DESIGN.md:489-490

Entered at `04ad8e7` (*"#204: FINDINGS, and ORPHANED-BY-REPOINT"*). Both sites QUOTE
ADR-0017's citation as their subject matter - **the quotation-versus-citation class, which
is task #213's ruling** - and need registering as exemptions, not repointing. Confirmed
still red in the shared checkout at `ebaf6c8`: `BASELINE_rc=1`, same two lines.

### RED 2 - `check-brief-report-references.py` exits 1, same shape as R21-N2

    brefs_rc=1
    ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
      FINDINGS-213-syntax-split.md   cited by BRIEF-211-213-record-and-counterfactual.md

R21's N2 recorded this exact shape at `80463a5` and said `72fe217` had closed it by making
the in-flight line land in the same commit as the brief. **It has recurred**: the #211/#213
brief shipped with a forward reference and no record line. It closes when #213's findings
document lands, or with a line in `brief-report-refs-known-missing.txt`. Not mine to write
- #213 is another agent's.

---

## THE SHARED CHECKOUT MOVED WHILE I WORKED, so `--ff-only` will REFUSE

`main` was `a52af14` when I was dispatched and is `ebaf6c8` now:

    ebaf6c8 A merge can silently delete work, and the branch it caught was a LIVE one
    69f8d12 The R21 register entry resolves, and my own new brief needed one
    30d8b68 Merge review/r21: the R21 report, one file, no fixes
    1045edb REVIEW-R21: 2 High, 3 Medium, 3 Low, 4 nits over c749334..80463a5

`a52af14` is an ancestor of `ebaf6c8` (`git merge-base --is-ancestor` rc=0), so my branch
is BEHIND, not diverged. **A bare `git merge --ff-only` from `main` will refuse.**
Measured overlap: NONE of my four files was touched by those four commits
(`git diff --name-only a52af14 ebaf6c8 -- <my four>` prints nothing), so both a rebase and
an ordinary merge are conflict-free. The commands are at the end.

**The brief named base `d2159e7`; the dispatch message named `a52af14`.** They disagree.
`d2159e7` is `a52af14`'s parent and both resolve, so neither would have failed a gate -
this is the "a stale-but-VALID SHA passes every check" shape the preamble warns about. I
used `a52af14`, the dispatch SHA, because it is the commit that CONTAINS the brief I was
told to read. Reported rather than silently resolved.

---

## Other findings, reported not fixed (my brief grants no `TaskCreate` mandate)

1. **`check-adr-numbers.py`'s `_branch_numbers()` crashes outside a git repo.** It calls
   `subprocess.run(..., check=True)`, so `git for-each-ref` failing raises
   `CalledProcessError` and the function's own `if not claimed:` fallback
   (*"No branches scanned; the cross-branch check did not run"*) is never reached. It IS
   reached inside an empty repo, so it is not dead code - the unreachable case is
   "no repo at all". Pre-existing, untouched by me. **Suggested fix:** `check=False`, and
   let the existing empty-result branch report it.
2. **`CITATION-READ-ADR-VERDICTS.md` has no row for `ADR-0030`** because its selector
   requires the filename, so 0030's two bare citations were never read and carry no
   verdict. Both are DRIFTED, measured above. **Suggested fix:** add a 0030 row (2 sites,
   `:356-359` and `:361-362`, both DRIFTED), noting the selector that missed them - the
   #204 discriminator is the instrument that would have caught it.
3. **The README's own claim that the count was caught "because two numbers disagreed" is
   now true three times over**, and every one of those catches was a human comparison, not
   a gate. Nothing here checks a prose count against its own command. Noted, not proposed.

---

## What I did NOT verify

- **I did not re-read all 46 DRIFTED verdicts.** I read the five files this finding names,
  measured 0030's two sites end to end myself, and spot-checked three of 0024/0025/0031's
  eleven against the freeze. The remaining eight I take from
  `CITATION-READ-ADR-VERDICTS.md`, which read all 64 one at a time and whose rows I
  verified against the files.
- **I did not verify that the twelve new index rows' Decision prose is the best summary of
  each ADR** - only that each is faithful to that file's own `# ADR-NNNN:` heading, which I
  read. A better one-line summary is a matter of taste, not correctness.
- **I could not run `actionlint`.** It is not installed here.
- **I did not fix either pre-existing red.** Both sit in other agents' files
  (`probe-204-orphaned-by-repoint.py`, and #213's missing findings document), and editing
  them is how a merge puts damage back.
- **I did not check whether `check-adr-numbers.py`'s new index check interacts with the
  `mirror.yml` or `pr-title.yml` workflows.** `check-checkers-are-wired.py --self-test`
  parses all three and passes 35/35, which is the closest thing to a check that exists.
