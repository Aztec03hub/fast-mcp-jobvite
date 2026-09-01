# WORKLOG #115B - population by KIND, not by path: the remainder

Branch `fix/kind-not-path-2`, cut from `main` at `9b00879`. Code commit `93b1553`.
Brief: `docs/briefs/BRIEF-115B-kind-not-path-remainder.md`. Design read at the freeze
`5d17cd7`, derived from `docs/DESIGN-FREEZE.txt`, never from the working tree.

## 1. The two population comparisons, with their actual numbers

Both checkers selected their population with `(ROOT / "src").rglob("*.py")` -
`check-env-vars-are-declared.py:91` and `check-settings-are-read.py:161` on `main` at
`9b00879`, both cited from `grep -n`.

**The sets are IDENTICAL today. The symmetric difference is EMPTY.**

| population | count |
| --- | --- |
| `(ROOT / "src").rglob("*.py")` | 23 |
| `git ls-files` filtered to `src/**.py` | 23 |
| in the glob, not tracked | 0 |
| tracked, not in the glob | 0 |

For context, and it is the reason the glob is not simply widened: `git ls-files` lists
**116** tracked `.py` in total, **93** of them outside `src/`. Those 93 are tests,
checkers, probes and scripts. Neither checker wants them - `mentioned()` asks about
`JOBVITE_*` literals *in the shipped package*, and a `JOBVITE_*` string in a test fixture
is not an operator-facing knob. So `src/` is a real semantic scope and stays; what changed
is that the scope is now applied to the tracked container rather than to the filesystem.

Before and after on an unmodified tree, both checkers produce **byte-identical output at
exit 0** (`diff` reported no difference for either).

**So this is the weaker case, and I am arguing it as such: it closes a defect that cannot
yet have happened, not a live bug.** No file is missed today and none is spuriously
included. There is no finding here, and I am not going to manufacture one.

## 2. What the change actually buys, proved by a positive control

The glob's blindness is *not* to location. `rglob` under `src/` is exhaustive, so there is
no member "living somewhere the glob does not reach" while `src/` exists. Its blindness is
to **trackedness**: an untracked `.py` under `src/` is read as though it were committed
source. I planted one and measured both arms rather than reasoning about them.

**`check-env-vars-are-declared.py`** - plant carries
`JOBVITE_A_NAME_NO_TRACKED_SOURCE_HAS`:

| form | names in `src/` | exit |
| --- | --- | --- |
| old (`rglob`) | 14 | **1**, `UNDECLARED JOBVITE_A_NAME_NO_TRACKED_SOURCE_HAS` |
| new (`git ls-files`) | 13 | **0** |

**`check-settings-are-read.py`** - plant mentions `outbound_rate_limit`, the one field
ADR-0025 records as KNOWN unread:

| form | refs to `outbound_rate_limit` | referenced fields | exit |
| --- | --- | --- | --- |
| old (`rglob`) | 1 (`src/fast_mcp_jobvite/_ctl_scratch.py:8`) | 16 | **1**, `STALE EXEMPTION  outbound_rate_limit is read now; drop its EXEMPT entry` |
| new (`git ls-files`) | 0 | 15 | **0** |

The second is the sharper one. A file nobody committed would have told the checker that
`outbound_rate_limit` has a reader, which contradicts ADR-0025 and would have fired the
tripwire that exists to catch its *first real* reader. The same mechanism in the other
direction - an untracked file supplying the only reference to a genuinely unread field -
is a **false negative**: the gap the checker exists to find would go unreported.

Both helpers now `raise SystemExit` on an empty population, so a package that moves out of
`src/` fails loudly instead of returning a silent, self-explaining zero.

The controls were planted in my own worktree only, and removed; `git status --porcelain`
after cleanup showed exactly the two intended modifications and nothing else.

## 3. `check-cross-references.py` - established, not changed

The brief was right that it has no glob. Establishing what it *does*: its population is a
hand-written three-entry dict, `DEFAULT_TARGETS` at `check-cross-references.py:107-111`
(`grep -n`), overridable by `argv` at `:229-230`.

Measured over the tracked container:

- tracked `.md` files: **206**
- tracked `.md` containing at least one `§n.m` reference: **133**
- covered by `DEFAULT_TARGETS`: **3**
- **carrying section references and checked by nobody: 130**

That is the "a named list is blind to the member nobody added" shape. **I did not change
it, and I do not think it should be changed on this evidence.** The largest unchecked
files are `docs/reviews/DESIGN-R2.md` (262 refs), `CONFORMANCE-B1-B106.md` (273),
`SPIKE-CLAIM-AUDIT.md` (183) - review documents, which cite the design *as it stood*. That
is the reasoning #115 had to overturn for the *checkers* at that path, and it remains
correct for the *documents*. Widening this population would produce a large red gate made
almost entirely of correct historical references.

**Suggested fix, for whoever rules on it:** do not widen the target set. Instead widen only
to documents that are themselves live specifications rather than records - candidates worth
reading are `docs/research/FASTMCP-SPIKE-4.md` (119 refs) and `docs/reviews/THREAT-MODEL-DRAFT.md`
(106) - and decide each by hand, with the reason recorded next to it, exactly as
`DEFAULT_TARGETS` already does for its three. A task should carry that decision; it is not
a sweep.

## 4. `f7aa6e8` deserves a fair reading, and it earns one

The brief describes the WIP's second half - line citations rewritten to section anchors -
as an outstanding separate task I might leave undone. **It is not outstanding. It is
already on `main`, byte-identical.**

Every line `f7aa6e8` added to the three docstrings is present at `HEAD` verbatim,
checked with `grep -qF` per added line:

- `check-env-vars-are-declared.py`: `§4.3 requires "a total outbound budget, configured",` - PRESENT
- `check-settings-are-read.py`: `§4.3's "a total outbound budget, / configured" was promised and nothing implemented one until U7.` - PRESENT
- `check-cross-references.py`: all three lines of the `§5.4` provenance rewrite - PRESENT

So `f7aa6e8`'s anchor work reached the trunk, presumably carried through #115's `f668b1a`.
The agent that was killed at the usage limit was right about that half and its work is not
lost. **The only thing it never got to was the population selection in the two files -
which is exactly what this task did.**

## 5. A near-miss I am recording because it nearly became a filed finding

While checking whether the anchor rewrite was still needed, I read `DESIGN.md:373-375` at
the freeze and found it is the **429-mapping** paragraph, not the outbound budget. The
budget sentence - *"a total outbound budget, configured, that bounds all attempts for one
tool invocation"* - is at **line 393** of the frozen blob. I was one step from filing
"nine sites cite the wrong paragraph".

Two things stopped it, and both are the reason it is written down:

1. **The two checkers do not cite `373-375` at all any more.** `grep -n 'DESIGN\.md:[0-9]'`
   over both files and over `check-cross-references.py` returns NOTHING. I had inferred the
   citation's presence from the brief's description of the WIP rather than from the file.
2. **The one live-code site that still cites it is CORRECT.**
   `tests/test_tools_jobs.py:255` cites `373-375` for *"Jobvite returns no rate-limit header
   on any observed call"*, and frozen `:374` says exactly *"no 429 has ever been observed and
   no rate-limit header is returned"*. Right paragraph, right claim.

What remains are record documents - `docs/plans/IMPLEMENTATION-PLAN.md:941`,
`docs/briefs/U7.md:33`, and several `docs/reviews/` and `docs/worklogs/` reports - which
cite `373-375` for the *budget* claim. Those ranges were correct at an earlier freeze and
have not been repointed **by decision**: #111 ruled `docs/plans` is a RECORD. I am
reporting this rather than sweeping it, and I do not think it needs a fix.

This is the class `check-design-citations.py` explicitly cannot see - a citation that
resolves to real prose which is the wrong prose - so it is invisible to every gate and only
a reader gets it. That is stated in #115's own closure and it held here.

## 6. Gates - each exit code read on its own line, no `&&` chaining

    uv run --frozen ruff check .                              EXIT=0
    uv run --frozen ruff format --check .                     EXIT=0   (116 files already formatted)
    uv run --frozen mypy                                      EXIT=0   (no issues in 116 source files)
    uv run --frozen pytest -q                                 EXIT=0   (887 passed, 0 skipped, 6 deselected)
    uv run --frozen python docs/reviews/check-checkers-are-wired.py   EXIT=0
    uv run --frozen python docs/reviews/check-env-vars-are-declared.py EXIT=0
    uv run --frozen python docs/reviews/check-settings-are-read.py     EXIT=0
    uv run --frozen python docs/reviews/check-cross-references.py      EXIT=0

The suite floor derived from `ci.yml` is `check-suite-floor.sh 887`; the run measured 887
passed with 0 skipped, so it sits exactly on the floor and does not move it.

**No new `check-*` file was created**, so the wired-checker container is unchanged and no
exemption is needed. `check-checkers-are-wired.py` exits 0 and prints its own caveat, which
I am repeating rather than paraphrasing: *"this proves each is INVOKED, not that its exit
code gates the job. A step that runs a checker and swallows its status reads as WIRED
here."*

### One red that is NOT mine, and I checked rather than assumed

    uv run --frozen python docs/reviews/check-design-citations.py   EXIT=1
      FAIL: docs/worklogs/AUDIT-SURVIVORS-REPORT.md:266:
            DESIGN.md:99999 is past the end of DESIGN.md (2133 lines)  <!-- REPOINT-EXEMPT: quotes a checker failure as evidence -->

That is **pre-existing at my base `9b00879`** and nothing to do with this branch.
`git show 9b00879:docs/worklogs/AUDIT-SURVIVORS-REPORT.md` line 266 carries the planted
citation with **no** `REPOINT-EXEMPT` marker. It was fixed on `main` at **`3411812`**
(`git log -S` over the marker text), and the shared checkout has since moved to `216466b`
- **two commits ahead of my base**. The same checker run in the shared checkout exits 0.

Do not read this as a red I introduced and do not read the shared checkout's green as
covering my branch: they are different trees. `check-design-citation-shape.py` exits 0 on
my branch, `check-obligations.py` exits 0 (*"Mappings: 31 | anchors verified against their
subject: 25 | recorded as absent: 6"*), and the merge will pick up `3411812`'s fix. If you
want the citation gate green on this branch before merging, merge `main` into it first;
I did not, because the brief says you merge.

## 7. What I deliberately did NOT do

- **No sweep of `373-375` citations in record documents.** Ruled out by #111. Reported in
  §5 with the evidence so it can be overruled if wanted.
- **No change to `check-cross-references.py`.** §3: measured, argued, left. Changing a
  third file on a guess is how a sweep acquires a defect, which the brief said and I agree
  with.
- **No shared population helper module.** The two helpers are near-duplicates of each
  other and of `check-design-citations.py:88-110`, which is a third copy of one rule.
  *Suggested fix:* the checkers are hyphen-named and so not importable without
  `importlib.util` machinery, which is why every one of them is standalone today; a shared
  `docs/reviews/_population.py` would need that machinery in three call sites. That is a
  structural change larger than this task, it collides with nothing today, and it should be
  its own ticket. Each helper names `check-design-citations.py` as the shape it copies and
  says in its docstring that a disagreement between them IS the bug, so the drift is at
  least visible to a reader.
- **No merge, no push, no rebase of `fix/kind-not-path`, no `git stash`.**

## 8. What I could not settle

- **Whether the 130 unchecked `§n.m`-carrying documents contain any genuinely broken
  reference.** I counted the population; I did not resolve the references. Resolving all
  130 is a real measurement and it is somebody's task, not a line in this one. I did not
  attempt it, and I am listing it here only because I am naming it as work rather than
  claiming an absence: I have NOT shown those references are fine.
- **Whether `docs/briefs/U7.md:33`'s `373-375` should be repointed.** #111's ruling names
  `docs/plans`; a brief is arguably a record too, but that is the lead's call, not mine.
