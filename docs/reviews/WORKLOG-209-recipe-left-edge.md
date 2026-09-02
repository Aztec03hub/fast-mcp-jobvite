# WORKLOG #209 (R21-H1) - the re-derivation recipe now IS the gate's selector

Agent: `suborch-209`. Task #209. Branch `fix/209-recipe-left-edge`,
worktree `/tmp/w209-recipe-left-edge`, cut from `main` at `a52af14`.
Nothing pushed, nothing merged.

**Commits:** `5a1cb0d` (the fix and its three arms), `66b703a` (the row-floor
registry, which could not see them).

## 1. The finding REPRODUCES, at a different pair of numbers

R21 measured 23 loose against 22 tight at `80463a5`. At `a52af14` -
`80463a5` plus the nine R21 briefs - the same two selectors give:

    loose (the published recipe):  27 names
    REF (the gate's own):          26 names
    in loose not REF: ['REVIEW-CHECKLIST.md']
    in REF not loose: []

Same shape, same single difference, same phantom. The recipe's output
was ALSO checked against the gate by running `REF` in Python over
`docs/briefs/**/*.md`: `tightP == gateREF` is `True`, 26 == 26, and the
sets are equal in both directions. So the loose recipe was over by
exactly one name and that name is `REVIEW-CHECKLIST.md`, which `1985471`
retracted and which has never been a file.

## 2. R21's suggested fix is INSUFFICIENT, and the brief's preferred one is INCOMPLETE

**R21 suggested `-E` -> `-P`.** It closes the left edge. It leaves two
things standing:

- **A THIRD LOOSE EDGE.** `grep -r` over a directory reads EVERY file;
  `cited()` reads `*.md`. Today `docs/briefs` holds 83 files and all 83
  are `.md`, so this costs nothing NOW - which is exactly the state the
  directory edge was in before it bit. `find docs/briefs -type f ! -name
  '*.md'` returns nothing; `find docs/briefs -type f | wc -l` is 83 and
  `-name '*.md'` is also 83.
- **THE SECOND IMPLEMENTATION.** Two hand-written selectors that must
  agree is the defect class, not the instance. `-P` fixes today's
  disagreement and leaves the mechanism that produced it.

**The brief leaned toward `--list-names` alone,** and asked what the
recipe is still FOR if it stops re-deriving anything. That question has
a real answer, and it is why `--list-names` ALONE is not enough either:
a recipe that just calls the checker does not "re-derive the population
without trusting this file" - it trusts the file completely. Replacing
the grep with a call to the gate would delete the paragraph's stated
purpose while keeping its heading.

**What shipped instead.** The selector is written ONCE and both consumers
are composed from it:

    BOUNDARY = r"(?<![A-Za-z0-9._-])"
    NAME = r"(?:REVIEW|WORKLOG|FINDINGS)-[A-Za-z0-9._-]+\.md"
    REF = re.compile(BOUNDARY + r"(docs/(?:reviews|worklogs)/)?" + f"({NAME})")
    RECIPE = "grep -rhoP --include='*.md' '" + BOUNDARY + NAME + "' {briefs} | sort -u"

`--recipe` prints that one-liner rendered for whatever `--briefs` it is
given (`shlex.quote`d); `--list-names` prints the gate's own population,
one name per line. Both sit BELOW the missing-directory refusal - a
recipe pointed at a path that does not exist and an empty population read
off one are both the clean zero this file already refuses once - and
ABOVE `tracked_index`, because neither needs git and refusing them on an
unreadable index would make the controls depend on something they are not
testing.

**And the honest answer to the brief's question,** written into the
docstring rather than left implied: the recipe no longer checks the
SELECTOR independently and by construction cannot. What it still checks
is everything AROUND the selector, with a standard tool and a traversal
this file does not control - that `cited()` walks the directory the
recipe walks, opens the files it opens, and that the count printed is the
count of that population. Those are falsifiable by grep, and two of them
(the `glob`/`rglob` edge, the `*.md` edge) have been wrong here.

## 3. Three arms, each loosening ONE edge and NAMING the name

"They differ" would have been satisfied by either loose edge - which is
the A8 confound this harness has now hit three times. The comparison is
set-wise, in both directions, and the expected difference is stated:

    A23 --recipe == --list-names -> identical      (identical, 3 names)
    A24 AMP loose recipe -> A23 goes red           (adds exactly REVIEW-CHECKLIST.md)
    A25 AMP no --include -> A23 goes red           (adds exactly FINDINGS-NOT-A-BRIEF.md)

A24 KEEPS `--include='*.md'` although the real pre-fix line did not: the
real pre-fix recipe had BOTH edges loose, and an arm asserting only "they
differ" would have passed on the file-type edge alone while claiming to
test the boundary. A25 keeps the boundary for the mirror-image reason.

The `recipe_row` helper runs the checker's OWN printed text through
`bash -c "set -o pipefail; $cmd"`. **The `pipefail` is load-bearing:**
without it the pipeline's status is `sort`'s, so an unsupported `-P` or a
bad pattern would exit 0 with an empty result and read as "the gate found
nothing" - a clean zero that explains itself. grep's rc=1 (no matches) is
admitted as a legitimate answer; anything above 1 is reported as a broken
instrument instead of being compared.

**`grep -P` availability, which the brief asked me to check.** Present in
both environments I can reach: locally `ugrep 7.8.4 ... -P:pcre2jit`;
`ubuntu-latest`'s GNU grep is built with PCRE. I did NOT run it on a CI
runner - see §6. If it were ever absent, A23 fails LOUDLY with "the
recipe command exited 2 (broken instrument)" rather than passing over two
empty files.

## 4. A11's anchor HAD to move, and this is the interesting part

A11 amputated the left boundary with `sed '/(?<!/d'` - delete every line
containing the lookbehind. That was safe while the lookbehind appeared
once in a comment and once inline in `re.compile`. It is now a NAMED
CONSTANT, so deleting its line raises `NameError` at import: the arm
would still be red at rc=1, for a reason that has nothing to do with the
boundary. **Same colour, different subject.** It now empties the constant
(`s/^BOUNDARY = .*$/BOUNDARY = ""/`), which removes the boundary from
both consumers and from nothing else.

This is a fix moving a control's anchor out from under itself, and the
only thing that would have caught it is reading the arm's output rather
than its exit code. `check-harness-anchors.py` cannot: its Shape D reads
`sed -i` command strings, and this harness uses `sed` writing to a new
file. The anchor count is 464 on this branch and 464 at `a52af14`,
unchanged, because none of this harness's anchors were ever in it. The
`amputate` helper's own "ANCHOR NOT FOUND" guard is what covers it.

## 5. The gate, exit codes read on their own lines

    ruff check .                          rc=0   All checks passed
    ruff format --check .                 rc=0   140 files already formatted
    mypy .                                rc=0   140 source files
    shellcheck --severity=warning -x      rc=0   both changed shell files
    uv run --frozen pytest                rc=0   887 passed, 6 deselected,
                                                 0 SKIPPED (floor 887, EQUAL)
    check-harness-anchors --floor 464     rc=0   464 anchors (floor 464)
    check-brief-report-refs-controls.sh   rc=0   25/25 fired, ROW_FLOOR 25 (EQUAL)
    check-row-floor-controls.sh <this>    rc=0   CONTROL FIRED, rows=24 floor=25
                                                 status=breach, exit 1
    check-row-floor-exactness.py          rc=0   32 harnesses, every floor equals
                                                 its live row count
    check-obligations.py                  rc=0   31 mappings, 25 verified, 6 absent
    check-review-coverage.py              rc=0   backlog holds at 66
    probe-docs-lint-amputation.py         rc=0   every amputation caught

Both floors DERIVED from `ci.yml`, not retyped:

    grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
      -> check-suite-floor.sh 887
    grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
      -> check-harness-anchors.py --self-check --floor 464

## 6. TWO THINGS THAT ARE RED OR WRONG AND ARE NOT MINE TO FIX

### 6a. THE BARE GATE IS RED, AT THE BASE COMMIT TOO

    uv run --frozen python docs/reviews/check-brief-report-references.py
    rc=1

    ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
      FINDINGS-213-syntax-split.md   cited by BRIEF-211-213-record-and-counterfactual.md

**This predates my branch.** Run in a detached worktree at `a52af14`
with nothing of mine in it, it exits 1 with identical numbers - 83
scanned, 26 cited, 4 dangling, 3 recorded. My change does not move the
population by a single name (26 before, 26 after, sets equal).

It closes when #213's report is committed, or by a line in
`brief-report-refs-known-missing.txt`. I did NOT add that line: it is a
statement about ANOTHER task's deliverable, and PREAMBLE says work
outside my scope is reported, not silently fixed.

### 6b. THE ROW-FLOOR REGISTRY COULD NOT SEE MY THREE NEW ARMS

`check-row-floor-controls.sh`'s entry matched only `^ *row "`, and the
new arms go through `recipe_row`. It predicted 22 rows against a floor of
25 and REFUSED at exit 9:

    ::error::the floor is at or above the row count already; this harness is
             RED before any deletion and the control cannot attribute an exit.

**It refused rather than passing, which is why this was cheap.** A
control that had quietly counted 22 and deleted rows until it saw a
breach would have reported a fired control over an enumeration wrong by
three. Widened to `^ *(row|recipe_row) "` in `66b703a`; third column stays
2, because A21 and A22 are still the only inline rows.

**The class is live and unfixed:** every row-invocation helper a harness
invents is invisible to this registry until somebody hand-edits a table.
That is a named list selecting for the name nobody thought of. Reporting
it, not filing it - my brief grants no `TaskCreate` mandate.

## 7. Where a reviewer should push on this

- `RECIPE` still hard-codes `grep`'s traversal semantics next to
  `rglob`'s. They agree on `-r`/`rglob`, on `*.md`, and on symlink
  behaviour by accident rather than by proof; A23 would catch a
  divergence only if the fixture contained one.
- `--list-names` prints `sorted(refs)`, the basenames. The gate ALSO
  tracks `cited_paths`, and the recipe cannot express that half at all -
  `grep -o` with the optional prefix in the pattern would emit the
  prefixed form and stop matching `--list-names`. The path claim is
  therefore unchecked by any recipe.

## 8. WHAT I DID NOT VERIFY

- **`grep -P` on an actual CI runner.** I read `ugrep`'s banner locally
  and know GNU grep on `ubuntu-latest` carries PCRE, but I did not
  execute the recipe in the CI image. A23 fails loudly rather than
  silently if it is ever missing, so the residual is a red step, not a
  false green.
- **That the pre-fix CHECKER fails A23.** It cannot: the pre-fix file has
  no `--recipe` or `--list-names` to run. A24 is the honest substitute -
  the defect put back in a line, with the fixed flags around it. The
  direct pre-fix-vs-fixed measurement is §1's 27-vs-26.
- **Whether any OTHER document republishes the loose recipe.** I checked
  the checker and its controls. I did not sweep `docs/` for a copied
  paste of the `-E` one-liner.
- **CI end to end.** Nothing here has run on a runner; every number above
  is from this worktree.
- **`d2159e7` vs `a52af14`.** The brief names `d2159e7` as the base; the
  dispatch and the shared checkout say `a52af14`. `d2159e7` IS an
  ancestor, one commit back, and the one commit between them
  (`a52af14`, the R21 briefs) adds nine brief files - i.e. it MOVES the
  population this task measures. I cut from `a52af14` because that is
  what `main` is. The brief's SHA was correct when written and went
  stale by one commit before it was sent.

## 9. Merge

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
      merge --ff-only fix/209-recipe-left-edge

Worktree LEFT IN PLACE at `/tmp/w209-recipe-left-edge`.
A second, detached worktree at `a52af14` was created at `/tmp/w209-base`
to measure §6a and should be removed with
`git worktree remove /tmp/w209-base`.
