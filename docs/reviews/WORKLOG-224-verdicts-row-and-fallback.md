# WORKLOG #224 - the row the selector could not see, and a fallback that could never fire

Agent `suborch-224`. Task #224. Worktree `/tmp/w224-verdicts-row`, branch
`fix/224-verdicts-row-and-fallback`, cut from `main` at **`4f03004`** (derived with
`git rev-parse main`, not typed from the brief).

This is a FIX worklog, not a code review, so it declares no `REVIEW-COVERS` range.

Two items, both from `suborch-210`'s *"Other findings, reported not fixed"* list in
`docs/reviews/WORKLOG-210-adr-ruling-evidence.md`. Both fixed here.

---

## PART 1 - ADR-0030's drift, RE-DERIVED rather than copied

**The instruction was to measure it myself and report a disagreement as the finding.
There is no disagreement. My measurement reproduces `suborch-210`'s exactly**, in
both directions, at both blobs.

### The citing sites, located with `grep -n`

    $ grep -n ':[0-9]\+\(-[0-9]\+\)\?`' docs/adr/0030-*.md
    16:`src/fast_mcp_jobvite/services/jobvite_client.py:835-850` - `public_error()` ...
    31:- `:356-359` - an open breaker and an outage share `/problems/service-unavailable` ...
    33:- `:361-362` - *"Jobvite's `429`, if it exists, is retried and then mapped to 503 ...
    52:schema. Measured, it is not. `src/fast_mcp_jobvite/errors.py:259` documents ...

`0030:29` is the blob line, two lines above the first citation:

    The frozen design, `git show c15b138:docs/DESIGN.md`, puts it in two places and both are 503s:

**Correction to my own brief's wording, and to `#210`'s.** Both say the citations sit
*"three lines under"* the blob line. `grep -n` puts the blob line at 29 and the
citations at 31 and 33, so the first is TWO lines under. The claim it supports - that
this is the tightest sha-to-citation proximity in `docs/adr/` - is unaffected, and if
anything it is tighter than stated. Recorded because a number nobody re-derives is how
this project's citations decay.

### The freeze SHA, DERIVED

    $ cat docs/DESIGN-FREEZE.txt
    d1f1a52

### The four reads

    $ git show c15b138:docs/DESIGN.md | sed -n '356,359p'
    - **An open breaker is distinguishable from an outage without inventing a type.** Both use
      `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail`,
      which says whether Jobvite failed or whether we have stopped calling it, plus a `retry_after`
      hint. An earlier revision minted two slugs for this. The distinction is real and worth making;

    $ git show d1f1a52:docs/DESIGN.md | sed -n '356,359p'
    Ordered timeout, then retry, then circuit breaker.

    - **Timeouts explicit and per-phase.** No SDK default, no single scalar.
    - **Retries live inside this module**, via `tenacity` with jitter, and only for connection errors,

    $ git show c15b138:docs/DESIGN.md | sed -n '361,362p'
    - **Jobvite's `429`, if it exists, is retried and then mapped to 503**, honouring `Retry-After`
      when present. No 429 has ever been observed and no rate-limit header is returned (§4.4), so this

    $ git show d1f1a52:docs/DESIGN.md | sed -n '361,362p'
      inbound request's deadline, because there is no inbound deadline here - see the note below.
    - **`create_candidate` is excluded from retry by construction**, not by configuration. This is

**Both citations are EXACT at `c15b138`** - the ADR's prose at `:31` and `:33` quotes
the target text verbatim - **and both land on unrelated prose at the freeze.** That is
DRIFTED, not WRONG. Under `#203`'s ruling at `ec57a65` an ADR's citations are AS AT
acceptance and are NOT repointed, so **nothing here obliges an edit to ADR-0030 and I
made none.**

### The brief asked me to check that no row already exists. It does not - but the file is not silent

`grep -n '0030' docs/reviews/CITATION-READ-ADR-VERDICTS.md` returns exactly ONE hit,
at `:274`, and it is not a row. It is inside that document's own
*"What I did NOT verify"* section:

>      7  ADRs carry a bare form and NO `DESIGN.md:N` form at all, so they were
>         entirely outside this sweep: 0002, 0008, 0009, 0011, 0015, 0023, 0030

**So the finding "0030 has no verdict row" is TRUE, and the sharper statement is that
0030 is one of SEVEN ADRs in that position, named by the document itself.** Adding
this row closes one of seven. The section I wrote says so, because a row that recorded
0030 and not the other six would leave the next selector free to miss them.

### Which selector missed them

All three selectors run over this corpus require the filename:

- the verdict document's own `DESIGN\.md:[0-9]+(-[0-9]+)?`, quoted in its population block;
- `BRIEF-196-adr-citation-read.md`'s, the same regex;
- the register's population query, named in the same *"did NOT verify"* section.

A bare `:NNN` inherits its target from whatever document the surrounding prose last
named, so no regex over the citing LINE can resolve it. `#204`'s discriminator reads
the surrounding prose and is the instrument that would have caught these two.

### THE ROW IS NOT ADDED TO THE 46-SITE TABLE, AND THAT IS THE DECISION THE BRIEF ASKED ABOUT

The lead asked: *"I do not know whether adding a row moves any count that document
publishes."* **It would have, and that is why the row is in its own section.**

`CITATION-READ-ADR-VERDICTS.md` publishes, at minimum: a Tally of 46/14/2/2, the
sentence *"46 of 64 - 72%"*, and a population block of 64 sites across 19 files with
the command that produces it. Adding two sites to the DRIFTED table would have made
the table 48 while every one of those figures still said 46, and it would have
redefined what "64" measures without saying so - the finding rebuilding itself one
column over inside its own remedy, which is exactly what `#215` measured happening to
`suborch-210`.

So the new section states in its first paragraph that it does not join those counts,
and why: they describe **one spelling**, and these two sites are in the other one.

**I also kept the citations in the BARE form inside the new section, deliberately.**
Writing them as `DESIGN.md:356-359` would have entered them into a population defined
by that regex. Measured before and after my edit:

    $ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l
    64      (before)   64      (after)
    $ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l
    19      (before)   19      (after)

The count is unmoved, which is the property the section claims for itself.

**No checker or workflow references this document by name**
(`grep -rn 'CITATION-READ-ADR-VERDICTS' --include=*.py --include=*.sh --include=*.yml .`
exits 1 with no output, run from the worktree root, so the path resolves), so the new
table cannot break a parser. Every doc checker was run anyway, below.

---

## PART 2 - `check-adr-numbers.py` raised where it meant to report

### CONFIRMED BY RUNNING IT, not by reading

`docs/` was copied to `/tmp/224-nogit-PRE`, which has no `.git` and no parent that is a
repo (`git -C /tmp/224-nogit-PRE rev-parse --show-toplevel` prints
`fatal: not a git repository (or any of the parent directories): .git`). Verbatim, at
`4f03004`:

    nogit_pre_rc=1
    ...
      File ".../check-adr-numbers.py", line 206, in _branch_numbers
        branches = subprocess.run(
    subprocess.CalledProcessError: Command '['git', 'for-each-ref', '--format=%(refname:short)', 'refs/heads/']' returned non-zero exit status 128.

**The exit code is the sharp part.** A `CalledProcessError` traceback exits **1** -
the SAME code the checker uses for a real duplicate, gap, heading mismatch or index
breakage. So outside a repo this gate goes red, and red for a reason its own output
never names, while the considered answer it holds for exactly this case
(*"No branches scanned; the cross-branch check did not run."*) can never be printed.

### The fix, and why it is not literally the suggested one

The task suggested `check=False` and letting the existing empty-result branch report
it. `check=False` is applied. **The empty-result branch alone is not enough**, because
it would make "there is no repo here" render identically to "this is a real repo with
no branches" - the switched-off-and-broken-must-not-render-identically shape this
project has recorded. So:

- `_branch_numbers()` returns **`None`** when `git for-each-ref` fails, and prints
  `BRANCH SCAN COULD NOT RUN: ... exited 128 in <ROOT>` followed by git's own stderr,
  verbatim;
- an empty-but-real repo still returns `{}` and still gets *"No branches scanned"*;
- `_report_branches()` handles `None` first and says the numbering and index checks
  above are unaffected.

`None` for a failure and empty for empty is the split `R19-M1` established in
`check-harness-anchors.py`; this follows the precedent rather than inventing a
convention. The type is now `dict[int, set[str]] | None`; mypy is clean.

**The branch scan is ADVISORY** - it answers "which number may I take next" - so its
failure must not decide the gate. That is why the fix is fail-loud, not fail-closed.

### After, verbatim, same non-repo directory

    ADRs: 35, numbered 0001-0035
    Every ADR number is unique, contiguous, and matches its own heading, and README.md's table lists all 35 of them and nothing else.

    BRANCH SCAN COULD NOT RUN: `git for-each-ref` exited 128 in /tmp/224-nogit-POST2.
      git: fatal: not a git repository (or any of the parent directories): .git
    The ADR numbering and index checks above are unaffected; only
    the next-free-number advice is missing.

    ARM7 rc=0

---

## Controls - `#217`'s six index arms, BEFORE and AFTER, unchanged

Run by `/tmp/224-arms.sh` against a COPY of the tree under `/tmp` (`git init`ed, so
the empty-repo path is exercised), never in the worktree, so no mutation could be
stranded. Each exit code read on its own line.

| Arm | What is mutated | PRE (`4f03004`) | POST |
|---|---|---|---|
| 0 | nothing | rc=0, *"No branches scanned"* | rc=0, *"No branches scanned"* |
| 1 | a FILE with no ROW (0035's row deleted) | rc=1 `NO ROW 0035` | rc=1 `NO ROW 0035` |
| 2 | a ROW with no FILE (0036 invented) | rc=1 `NO FILE 0036` | rc=1 `NO FILE 0036` |
| 3 | a row whose LINK points at another ADR's file | rc=1 `BAD LINK 0034` | rc=1 `BAD LINK 0034` |
| 4 | the index ABSENT | rc=1 `NO INDEX` | rc=1 `NO INDEX` |
| 5 | the index present with ZERO rows | rc=1 `MATCHED ZERO INDEX ROWS` | rc=1 `MATCHED ZERO INDEX ROWS` |
| 6 | one ADR listed TWICE | rc=1 `lists these twice: 0030` | rc=1 `lists these twice: 0030` |
| **7** | **run OUTSIDE a git repo** | **rc=1, `CalledProcessError` traceback** | **rc=0, reason PRINTED** |
| restore | copy vs source | `diff` rc=0 | `diff` rc=0 |

**Arm 7 is the only cell that moves, and arm 0 is the one that proves the fix did not
buy its result by disabling the empty case.** Six of six index arms still fire.

---

## Gates, each exit code on its OWN line, at the final tree

    python3 docs/reviews/check-adr-numbers.py                        adr_numbers_rc=0
      "35 ... README.md's table lists all 35 of them and nothing else."
    python3 docs/reviews/check-design-citations.py                   design_citations_rc=0
    python3 docs/reviews/check-design-freeze.py                      design_freeze_rc=0
    python3 docs/reviews/check-design-citation-shape.py              citation_shape_rc=0
    python3 docs/reviews/check-cross-references.py                   cross_references_rc=0
    python3 docs/reviews/check-coupling-sweep.py                     coupling_sweep_rc=0
    python3 docs/reviews/check-resweep-verdicts.py                   resweep_rc=0
    python3 docs/reviews/check-review-coverage.py                    review_coverage_rc=0
    python3 docs/reviews/check-row-floor-exactness.py                row_floor_exactness_rc=0
    python3 docs/reviews/check-row-floors.py                         row_floors_rc=0
    python3 docs/reviews/check-landing-published.py                  landing_rc=0
    python3 docs/reviews/check-clause-citations.py                   clause_rc=0
    python3 docs/reviews/check-obligations.py                        obligations_rc=0
    python3 docs/reviews/check-brief-report-references.py            brefs_rc=0
    bash docs/reviews/check-brief-report-refs-controls.sh            brefs_controls_rc=0
      HARNESS-RESULT name=check-brief-report-refs-controls.sh rows=25 floor=25 fired=25/25 status=ok
    bash docs/reviews/check-harness-result.sh                        harness_result_rc=0
      EQUAL: all 38 scripts in the container emit the canonical line.
    uv run --frozen python docs/reviews/check-checkers-are-wired.py           wired_rc=0
    uv run --frozen python docs/reviews/check-checkers-are-wired.py --self-test  wired_selftest_rc=0
      run steps parsed: 94; 35/35 controls passed.
    python3 scripts/check-harness-anchors.py --self-check --floor 464         anchors_rc=0
      floor DERIVED: `grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml`
      "OK: all 464 anchors resolve in their target file (floor 464)."
    uv run --frozen ruff check .                                     ruff_rc=0   ("All checks passed!")
    uv run --frozen ruff format --check .                            ruff_format_rc=0  (141 files)
    uv run --frozen mypy                                             mypy_rc=0   (141 source files)
    python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"  yaml_rc=0
    uv run --frozen pytest -q                                        pytest_rc=0
      887 passed, 6 deselected in 57.65s - ZERO skipped.
      Floor DERIVED: `grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml`
      -> `check-suite-floor.sh 887`. 887 >= 887. The 6 deselected are `ci.yml`'s own
      marker deselection, which is not a skip.

**`ruff check` was RED on my own work before it was green.** Seven `W505 Doc line too
long (73 > 72)` in the docstring paragraph I had just written at
`check-adr-numbers.py:203-213`. Rewrapped, re-run to `rc=0`. Recorded because this is
the second consecutive round in which this file's docstring did it.

**`actionlint` is NOT installed here** (`command -v actionlint` finds nothing). It was
not run and nothing above claims it was.

---

## ONE RED THAT IS NOT MINE, AND MAIN IS CARRYING IT

    python3 docs/reviews/check-no-errexit.py                         no_errexit_rc=1
    1 script(s) enable errexit:
      docs/reviews/probe-stale-branch-regression.sh:50  set -euo pipefail

**Confirmed pre-existing**, by running the same checker in a detached worktree of
`4f03004` itself: `no_errexit_on_main_rc=1`, same single line. That file is not in my
diff (`git status --porcelain` shows exactly two modified files, neither of them it),
and editing another unit's harness is how a merge puts damage back. Not fixed.

`check-design-citation-shape.py`, which `suborch-210` reported RED, is **green here**
(`citation_shape_rc=0`). Something closed it between `a52af14` and `4f03004`.

---

## Files changed

    docs/reviews/CITATION-READ-ADR-VERDICTS.md    new section, before "The qualifier"
    docs/reviews/check-adr-numbers.py             _branch_numbers/_report_branches
    docs/reviews/WORKLOG-224-verdicts-row-and-fallback.md   this file

`docs/OBLIGATIONS.md` was not touched and no anchor moved; `check-obligations.py`
exits 0 and `check-harness-anchors.py --self-check --floor 464` reports all 464
anchors resolving.

---

## What I did NOT verify

- **I did not read the other six bare-form ADRs** (0002, 0008, 0009, 0011, 0015,
  0023). I confirmed the seven-member list is the verdict document's own and that
  0030 is in it; I did not open the other six or measure their citations. That is a
  sweep, not a reading, and it is the work `#204`'s discriminator exists to do.
- **I did not re-measure any of the 46 DRIFTED sites or the 14 CORRECT ones.** My
  brief scoped me to 0030's two, which I measured end to end at both blobs.
- **I did not verify that `c15b138` is the blob ADR-0030 was ACCEPTED against**, only
  that it is the blob the ADR names at `:29` and that both citations are exact there.
  Establishing the acceptance blob independently would mean dating the citation with
  `git log -S`, which I did not run.
- **I did not run `actionlint`.** It is not installed here.
- **I did not run the full CI workflow**, only the individual gate commands listed
  above from this worktree.
- **I did not test the no-repo path under a `git` binary that is absent rather than
  failing.** `FileNotFoundError` from `subprocess.run` is a different exception and
  `check=False` does not catch it; I judged that out of scope and am naming it rather
  than implying the function is now total.
