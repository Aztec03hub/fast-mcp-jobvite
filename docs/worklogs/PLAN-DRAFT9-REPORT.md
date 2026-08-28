# PLAN-DRAFT9-REPORT - round 7 applied, and the review cycle closed

Agent: `impl-plan-draft9`. Task **#25**.
Worktree: `/tmp/plan-draft9-work`, created with `git worktree add` at the pinned SHA
`ff9461ae75d6a994dd3ca4e97c828f4361aca125`, branch **`plan/draft9`**.
**The shared checkout at `/home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite` was never
checked out, never edited, and never had a branch moved in it.** The only write to it was none; the
only reads were `git -C <shared> log/status/diff`.
**One file changed: `docs/plans/IMPLEMENTATION-PLAN.md`.** Plus this report.
Commit: **`258ba37`**.

---

## The thing the brief could not have told me, and that changes how this reads

**The brief says the plan is at draft 8, committed at `40959c8`, 2,040 lines. All three are wrong,
and the commit message is the reason.**

```
$ git show 40959c8:docs/plans/IMPLEMENTATION-PLAN.md | sed -n 3p
Status: **DRAFT 9.** Revised against `PLAN-REVIEW-R7.md` (0C / 1H / 1M / 5L).
$ git show 40959c8:docs/plans/IMPLEMENTATION-PLAN.md | wc -l
2096
$ git log -1 --format=%s 40959c8
Draft 8 final, round 7, and the measurements harness
```

`40959c8` is titled *"Draft 8 final ... at 2,040 lines"* in a message **whose opening paragraph
corrects `4e5a1b2` for being titled draft 7 while containing draft 8** - and its own content is
draft 9 at 2,096 lines, with most of round 7 already applied. **The commit correcting a mislabelled
draft is itself mislabelled, in the draft number and in the line count.**

This is round 7's L5 recurring one commit later, and it is not cosmetic: the brief I was given, the
task description on the board, and R7's own header (*"2,000 lines"*) all inherited it. I verified
every line count and the tally from the objects before starting, which is why this did not turn into
a second agent re-applying an applied round - the failure `40959c8`'s message describes.

**Consequence for the work:** draft 9's body already existed. My job became (a) finish the parts of
round 7 that were missing, (b) rewrite everything `ff9461a` had made false, (c) write the exit
section, (d) fix the numbers. Not a fresh application.

---

## Round 7, finding by finding

### H1 - collision 11, the collection guard - **ADOPTED-MODIFIED**

**Verified before adopting.** Ran the harness first, as instructed:

```
$ python3 docs/reviews/check-plan-measurements.py
  [OPEN] M4 guard vs a wholly-deselected file
         a wholly-credentialed/network file reads as an ORPHAN and reds the suite -
         collision 11, and U5 is scheduled to create exactly this file
Every plan measurement reproduces. Known-open items are listed as OPEN above.   exit 0
```

Re-derived the mechanism at source rather than accepting R7's citations:
`tests/test_collection_guard.py:82` passes `-m "not credentialed and not network"` to the collection
subprocess; `:139` is the test; `:147-148` is the comment asserting the opposite; `:152` is the
assertion; `:40-48` is `_SKIP_DIRS`; `pyproject.toml:69` is `testpaths = ["tests"]`. **All six
correct on subject.** `ls tests/credentialed/` is `README.md` only, so the branch has never run.

**What was already applied at `40959c8`:** collision 11 as list item 11, the §4 *"reds the suite on
TWO things"* rewrite, and the M4 probe.

**What was missing, and is the modification.** R7's fix asked for a shared-file row, and the brief
was explicit that the constraint must sit *"where U5's implementer will hit it, not only in the
collisions list"*. **Neither existed.** U5's section said *"U5 adds the FIRST credentialed arm"* and
said nothing about the guard. Draft 9 now carries **both**:

1. A **seventh shared-file row** for `tests/test_collection_guard.py` and the marker set, in the
   container-and-rows form R7 proposed, naming U5 as the unit that lands the first such file and
   requiring the `-m` drop plus a planted-file control **in the same commit as the arm**.
2. A **new bullet in U5's own "Verified by" list**, which is where a U5 agent will actually be
   reading. It states the failure message is a *false diagnosis*, names the two cheap greens that
   must not be taken (`_SKIP_DIRS`, or hiding the arm in a file with an unmarked test), and makes
   **M4 flipping OPEN -> PASS U5's discharge receipt**. I verified that flip is real before
   promising it: `check-plan-measurements.py:20-23` and `KNOWN_OPEN` at `:195` say M4 passes once
   the guard drops `-m`.

**Rejected from R7's fix:** the part directing edits to `tests/credentialed/README.md`. Not my file
(brief: my only file is the plan). It is in the recommendations below.

### M1 - the unwired obligation checker - **ADOPTED-MODIFIED (inverted, because the tree moved)**

**Verified against the tree, not the report, as instructed.** `ff9461a` wired all three steps into
`ci.yml`'s `design-gates` job. Read at source rather than inferred from the commit message:
`check-obligations.py` at `ci.yml:131`, `--controls` at `:149`, `check-plan-measurements.py` at
`:112`. **So every sentence in the plan calling these hand-run was false**, including the shared-file
row draft 9 had just added to record M1.

Rewritten **in place**, in four places: the header bullet, the §4 shared-file row, the amendment
table's `b7fd35d` row, and U0's CI list (which named the three coupling scripts individually and now
names the `design-gates` job and all six of its steps). R7's fix part 2 - *"a unit that edits a line
`docs/OBLIGATIONS.md` anchors to updates the mapping in the same commit"* - is now the rule inside
that shared-file row, **with the gate behind it**, plus the clause that a unit whose edit moves an
anchor **into the plan** reports the new line rather than repointing it.

### L1 - the count behind its own table - **ADOPTED, by deleting the number**

Draft 9 as committed said *"the **six** in the shared-file table"*, and the table had six rows -
correct at the time. **Collision 11's row made it seven while I was writing.** Draft 8 had left the
standing instruction *"if a seventh row lands and this sentence still says six, delete the number
instead of incrementing it"*. **A seventh row landed, and this is that deletion**: the sentence now
reads *"every row of it, and no others"* and states that the table is the count. The paragraph
records the full series without asserting how many drafts were wrong.

### L2 - "three places" gate on ADR-0012 - **ALREADY APPLIED, verified**

`:64` reads *"**two** places"*; `:1645` reads *"in **both** places the plan gates on an ADR"*. Both
read at source in the committed object. I also ran the brief's wider check that no ADR gate reverted
to existence: `grep -ni "adr" ... | grep -i exist` returns five hits, **all narrating the old defect
or the register, none a live gate** - `:1641` and `:2127` both gate on **ACCEPTED**. Not
half-applied.

### L3 - the amendment table vs its own verification command - **ADOPTED-MODIFIED, and it was worse than R7 measured**

R7 said the table was two commits short. **At `ff9461a` it was three short and one long**, and the
long one is the interesting half: `196512b` sat *in* the table while the plan's own command could not
return it, because the command named `.github/workflows/` and omitted `.gitignore`. **A verification
command that disagrees with the table it verifies in both directions.**

Fixed by adding `b993ada`, `1b7975b` and `ff9461a` as rows and widening the command to `.github/`,
`.gitignore` and `.env.example`. **Verified by set comparison, not by counting:**

```
$ CMD=$(git log --format=%h b53886e..HEAD -- pyproject.toml uv.lock .github/ tests/ \
        scripts/ docs/OBLIGATIONS.md .gitignore .env.example | sort)
$ TBL=$(<the table's commit column>, sorted)
cmd count: 14   tbl count: 14
--- in command, not in table ---   (empty)
--- in table, not in command ---   (empty)
```

The prose still states **no count** for the table, and now adds: *"if the command returns a commit
this table does not have, the table is wrong and the command is right."*

### L4 - F-6 vs the MET-BY-ACCIDENT A-5 - **ALREADY APPLIED, verified**

`:104-107` names **F-6** and **A-5** separately and says A-5 *"is a MET BY ACCIDENT row and not a
defect at all"*, which is exactly R7's suggested wording. Read at source. Nothing to do.

### L5 - the mislabelled commit - **ADOPTED-MODIFIED, per the brief's instruction not to re-litigate**

The brief said `40959c8` corrects it forward and the plan should not re-litigate. It does correct it
forward, in detail. **But `40959c8` then repeated the shape** (see the top of this report), so the
footer note is **rewritten in place** rather than deleted: it records that `4e5a1b2` was corrected
forward and needs no further litigation, then records the recurrence with the two commands that
falsify it, and draws the lesson at the level that would actually stop it - *derive the draft number
and line count from the file in the same command that writes the message*. **I did that for my own
commit and said so in it.** No citation anywhere in the plan calls `4e5a1b2` draft 7.

---

## The accepted-items checklist, checked off against the finished text

Carried through the rewrite deliberately, because a rewrite silently reverts sentence-sized
findings. Every row re-read in the committed object at `258ba37`, not from memory.

| # | Item | Source | In the finished text? |
|---|---|---|---|
| 1 | Collision 11 in the collisions list, both arms measured | R7 H1 | yes, item 11 |
| 2 | §4 "the guard reds on TWO things" rewrite | R7 H1 | yes |
| 3 | Shared-file row for the guard, naming U5 | R7 H1 | **yes, new** |
| 4 | The constraint inside U5's own section | brief | **yes, new** |
| 5 | "Do not add to `_SKIP_DIRS`" | R7 H1 | yes, in both places |
| 6 | Obligation checker described as WIRED | tree at `ff9461a` | **yes, 4 sites rewritten** |
| 7 | The `design-gates` job in U0's CI list | R7 M1 | **yes, new** |
| 8 | "Edit an anchored line, repoint in the same commit" | R7 M1 | **yes, new** |
| 9 | Shared-file count deleted, not incremented | R7 L1 + draft 8's own rule | **yes** |
| 10 | "two places" / "both places" on the ADR gate | R7 L2 | yes, verified |
| 11 | Every ADR gate reads Accepted, not exists | brief | yes, swept |
| 12 | Amendment table complete against its command | R7 L3 | **yes, 14 = 14** |
| 13 | Command widened past one-file-in-a-directory | R7 L3 | **yes** |
| 14 | F-6 and A-5 named separately | R7 L4 | yes, verified |
| 15 | No citation calls `4e5a1b2` draft 7 | R7 L5 | yes, verified |
| 16 | `mirror.yml` residue rewritten, row kept | R7 "tree moved" | yes, verified at `:1406` |
| 17 | The species turned into a standing check | brief | **yes, new, in §4** |
| 18 | The exit section | brief | **yes, new §10** |
| 19 | Status line reads draft 9 against R7 | brief | yes |
| 20 | Footer reads draft 9, re-pinned to `ff9461a` | brief | **yes, rewritten** |
| 21 | Measurement block re-pinned and re-run | brief | **yes, `ff9461a`** |
| 22 | "all eleven closed-set assertions" number deleted | brief | **yes** |
| 23 | "Two of the ten collisions above" number deleted | own sweep | **yes** |
| 24 | Suite trajectory carries 93, not 90 | own re-run | **yes** |

Bold rows are what this draft added or changed; the rest were verified as surviving.

---

## Two things I found by running, that no reading would have caught

### 1. `scripts/check-u0-test-controls.sh` is RED at `ff9461a`, and CI gates on it

```
$ bash scripts/check-u0-test-controls.sh
FAILED tests/test_workflow_pins.py::test_the_walk_found_workflows_and_pins
1 failed, 92 passed, 2 deselected
ABORT: the unmutated copy is already red. Fix that before running controls.
exit 1
```

**So the honest reading is 0/11, not the `11/11` rounds 6 and 7 both recorded** - and both were
right when they measured. `9ca76fe` broke it afterwards.

**Root cause, diagnosed rather than predicted.** The harness stages a copy of the tree from a
hard-coded list at `scripts/check-u0-test-controls.sh:47`:
`COPY=(pyproject.toml uv.lock .env.example .gitignore src tests docs scripts)` - **no `.github`**.
`9ca76fe` added `tests/test_workflow_pins.py`, whose `test_the_walk_found_workflows_and_pins` is a
*positive control on its own instrument*: it fails when the walk finds no workflow files, which is
precisely what it finds in a staged tree with no `.github/`. **The positive control worked** - it
detected a vacuous walk and said so. This is the fourth appearance on this repository of *a file
list that names one thing selecting for what it does not name*.

**`ci.yml:296` runs this harness and gates on its exit code**, so the `test` job is red at HEAD.
Fix is one entry: append `.github` to `COPY`. **`scripts/` is U0's, not mine** - recorded in §8 and
recommended below, not fixed.

### 2. R7's own "eleven closed-set assertions" is a count behind its own list

R7's sweep table names **thirteen** sites in **ten** rows and the prose above it says *"eleven
sites"*. The plan had inherited *"all eleven closed-set assertions"*. **The number is deleted** and
replaced by the §4 standing check, which does not depend on any sweep having been complete.

---

## What draft 9 adds beyond applying round 7

- **§4 standing check.** Every unit greps the suite for assertions that close a set its change grows
  (the exact grep is in the plan) and then **opens the body and reads it - not the name**. Both
  expensive collisions were invisible from the name and obvious from the body. This replaces
  predicting the twelfth collision.
- **§10, the exit.** The count is a floor, with the series **re-derived from the committed objects**
  (`git log --format=%h --reverse -- docs/plans/IMPLEMENTATION-PLAN.md`, then line 3 and the
  collisions headline of each) rather than recited - and it says plainly that drafts 3-5 were never
  committed here, so those three counts **cannot** be re-derived. Why the cycle closes at round 7.
  What replaces it, **with five explicit statements of what the two gates do not cover**. The
  four-item standing rule for every unit brief.
- **No round 8 is requested anywhere**, in the plan or in this report.

---

## `check-obligations.py`: the two anchors, and a finding about the scheme

**The rewrite moved both, exactly as the brief predicted. New line numbers:**

| B | Subject | Old | **New** |
|---|---|---|---|
| B78 | `headings matching exactly` | `docs/plans/IMPLEMENTATION-PLAN.md:1229` | **`:1268`** |
| B81 | `A CI status badge` | `docs/plans/IMPLEMENTATION-PLAN.md:1274` | **`:1313`** |

Not repointed - `docs/OBLIGATIONS.md` is not my file. The checker names both new lines itself, so
this costs one edit each.

**On the mechanism, since the brief asked.** The brief says the scheme *"has now rotted on every
single plan edit"*. It has, and `ff9461a` rotted five more when it wired the gate. **But I would not
replace it, and here is the distinction I think matters:** the anchors that rot are the ones pointing
into **prose that is being rewritten**, and the file:line map is doing exactly what it was built to
do there - it caught both, named the destination, and cost two lines. The scheme is not the problem;
**anchoring into a document under active rewrite is.** Two narrower changes would remove nearly all
the churn without giving up the gate:

1. **Let a mapping cite a stable anchor instead of a line.** B78 and B81 both point at prose in U13.
   A `#### U13` heading plus the subject string would survive any rewrite that does not delete the
   subject - which is the only case the gate should fire on. The checker already searches the whole
   file for the subject when the line misses, so most of the machinery exists.
2. **Prefer anchoring an obligation to the artifact that DISCHARGES it, not to the plan that
   describes it.** B78's real subject is a README section U13 has not written yet; the plan is
   standing in for a missing artifact. Those are the anchors that will rot every time either
   document moves, and `README.md` is already task #5.

I would not act on this without your call, so it is a recommendation, not a change.

---

## Recommendations - not my files, so not done

I have not created board tasks for these; say the word and I will, or fold them into existing ones.

1. **`scripts/check-u0-test-controls.sh:47` - append `.github` to `COPY`.** One entry. **CI is red
   at HEAD without it** (`ci.yml:296`). U0 follow-up. **Highest priority item in this report**, and
   the only one that is currently breaking a build.
2. **`tests/test_collection_guard.py`** - drop `-m` from `_collected_test_files()` (`:82`), add the
   planted-wholly-credentialed-file control, and correct the false comment at `:147-148`. The plan
   now assigns this to U5's arm commit; if you would rather it land as a U0 follow-up before U5 is
   dispatched, that is strictly safer and the plan's U5 bullet still reads correctly (M4 would
   already be PASS when U5 starts).
3. **`tests/credentialed/README.md:12-19`** - add the guard as a fourth bullet to *"the contract for
   a unit adding an arm here"*. R7 asked for this; it is not my file.
4. **`docs/OBLIGATIONS.md`** - repoint B78 to `:1268` and B81 to `:1313`.
5. **Consider the anchor-stability change above.**

---

## Merge command

```
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite merge --no-ff plan/draft9
```

Branch **`plan/draft9`** at **`258ba37`**, **rebased onto `origin/main`** before reporting.
**No `--ff-only` is promised** - `main` moves under me and two implementation agents are on it.
**I did not merge and did not push.**

Worktree `/tmp/plan-draft9-work` **removed** after reporting; the branch remains.

---

## What I did NOT verify

For what I could not settle, not for what I did not try.

1. **Whether dropping `-m` from `_collected_test_files()` has a cost at import time.** R7 left this
   open and I did not close it: collection **imports** the module, and a credentialed arm doing real
   work at module scope would then run during collection. `tests/credentialed/README.md:16-17`
   forbids module-scope credential reads, but that is a convention with no gate. **I did not build
   the probe**, because the fix is `tests/`, which is not my file, and a probe for a fix I am not
   allowed to make would have been theatre. It is the one open question on H1's remedy.
2. **Whether `ci.yml`'s `design-gates` job actually passes on a runner.** I read the six steps at
   source and ran all six scripts locally. **I ran no workflow.** The same limit rounds 6 and 7
   declared, and `ci.yml:16-19` still says several jobs have never run.
3. **Whether the `test` job is red on GitHub right now.** Locally `check-u0-test-controls.sh` exits
   1 and `ci.yml:296` gates on it, so it should be. **I could not check the run**: the `github` MCP
   server failed to connect this session (*"Authorization header is badly formatted"*) - the same
   failure round 7 recorded. Unasserted in the other direction.
4. **The collision counts for drafts 3, 4 and 5** (four, five, six). Those drafts were never
   committed to this repository - `git log -- docs/plans/IMPLEMENTATION-PLAN.md` shows drafts 1, 2,
   6, 7, 8, 9 only - so the three earliest numbers in the series **cannot be re-derived**. §10.1
   says so in the document rather than presenting the whole series as derived.
5. **How many `standards/...` citations in the plan hold at source.** Unchanged from round 7: an
   unmeasured population, ten verified by round 6, two more by round 7, and §8 still declares the
   class unverified. I added none and checked none.
6. **Whether `uv lock` with the four new direct dependencies still resolves 72 packages.** Same
   reason as rounds 6 and 7: it writes `uv.lock` in a tree other agents are building on.
7. **Whether the four Proposed ADRs (0012, 0013, 0014, 0017) will be accepted.** I verified all
   seventeen statuses against their files (`grep -m1 '^\*\*Status'` over `docs/adr/0*.md`) and that
   the plan's register table matches on all six rows it carries. Whether they get accepted is yours.

---

*`impl-plan-draft9`, 2026-08-28. Worktree pinned at `ff9461a`, branch `plan/draft9`, one file
changed plus this report. `docs/DESIGN.md` read only from the frozen object `135c3ac` and not
edited. The shared checkout was never written to and never had a branch moved in it. Nothing was
pushed and nothing was merged.*
