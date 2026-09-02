# FINDINGS-168: `NONE` decided by range alone, and the two rulings it forced

Agent: `suborch-168`, Tier 1. Task #168, from R17-H1.
Branch `fix/168-range-before-paths`, cut from `origin/main` at **`22c9873`**.
Every number below is re-derived at `22c9873` and says which ref it used.
Not pushed, not merged.

---

## 1. What was wrong, and what the fix is

`check-review-coverage.py` decided `NONE` by RANGE MEMBERSHIP ALONE and
applied the path filter afterwards only to pick `PARTIAL`. A declaration
with a wide range and a narrow path list therefore moved commits out of
`COVERED BY NOTHING` without reading them.

A round now reaches a commit only if it claims **at least one non-record
file the commit actually touches**, and a commit with **no** non-record
file is decided by its CONTENT before any declaration is consulted.

**Measured, `--ref origin/main` = `22c9873`, against an emptied backlog
so the whole outstanding set prints:**

| | outstanding | NONE | PARTIAL | covered | nothing-to-read |
|---|---|---|---|---|---|
| HEAD `22c9873` | 53 | 17 | 36 | 271 | not reported |
| the claiming rule only | 53 | 45 | 8 | 271 | 89 |
| **shipped (claiming + content-first)** | **48** | **40** | **8** | **276** | **89** |

---

## 2. THE COUNT DOES NOT GO UP, AND THE BRIEF SAID IT WOULD

§E of my brief says *"expect your fix to INCREASE the outstanding count.
A fix that leaves it unchanged did nothing."* **That is wrong, and it is
wrong by construction, not by accident.**

A commit whose files nobody claims was ALREADY outstanding - it was
recorded `PARTIAL`, not `NONE`. To become `covered` a commit needs EVERY
file claimed, which a one-file declaration cannot do. So the hole could
never remove a line from the backlog. Measured: with the claiming rule
alone the outstanding SET is **identical**, 53 -> 53, same 53 shas, with
**28 commits moving `PARTIAL` -> `NONE` and none moving the other way**.

R17's own control says the same thing and neither of us read it that
way: `NONE` 26 -> 0 **and** `PARTIAL` 42 -> 62. 26 + 42 = 68 = 0 + 62 +
6 landed-after. The total never moved. **What was manipulable was the
KIND** - which is the half a handoff quotes as "nobody has looked at
these", so the defect is real and the headline was the target. Had I
reported a rising count I would have been reporting something else.

The count does move, **down 5**, for the separate reason in §3.2.

---

## 3. The two rulings, with reasons

### 3.1 A commit that touches ONLY record paths: COVERED, and reported in its own count

`RECORD_PATHS` already rules that a record is *"an account of something
that already happened; the thing it accounts for is reviewed where it
lives"*. Such a commit has no file a round could read, so requiring a
claimed non-record file would be **unsatisfiable** - the test could
never pass, for any declaration, ever.

It is not a third KIND either: adding one changes the backlog format,
`KINDS`, and every recorded line, to express "not outstanding" - which
`covered` already expresses. It is counted, never silent, on a new line:

    Nothing to read - a clean merge's --cc diff is empty and its content
    is scored at the branch commits, or the commit touches only RECORD
    paths: 89

**29 commits at `22c9873`** are record-only.

### 3.2 A MERGE with an empty `--name-only`: covered, decided by CONTENT, before the range

`git show --name-only` defaults to `--cc`, which prints nothing for a
clean merge. **60 of the 69 trunk merges** at `22c9873` are in that
state; the other 9 are evil merges whose merge-unique files `--cc` does
print, and those are scored normally.

I did not re-derive whether that is a defect. **REVIEW-R16 §3** and
**REVIEW-151-R1** each raised it and each WITHDREW it, and R16 settled
it over the whole container, not a sample: for all 60 merges in
`8695101..ccbdaae`, every file in the first-parent diff is either
merge-unique or carried by a branch commit that is itself in the trunk
`rev-list`. **Unaccounted files: 0.**

**The ruling that matters is the ORDER.** My first version kept the
range requirement for these commits, and the new WIDTH arm immediately
caught it: a planted full-range one-file declaration still moved **five
of them** out of `NONE`. That is R17-H1 alive inside the fix for
R17-H1, at reduced scale - the shape this repository keeps re-finding.
So the content test now runs FIRST: a commit with nothing in it to read
is not something any declaration, of any width, can win or lose.

**Consequence, stated plainly:** five clean merges leave the outstanding
set (`22c9873 298ce89 4926296 96249f5 f7772f9`), two of which were
recorded. That is a DELETION from the backlog made by RULING, not by a
clearance, and it is written into the backlog's own header as such.

---

## 4. The arm

`probe-coverage-ratchet.py`, arm **WIDTH**, 9 arms -> 10. PLANT perturbs
a declaration's EXISTENCE; WIDTH perturbs its WIDTH, planting
`8695101..<trunk> PATHS: docs/DESIGN-FREEZE.txt` into a **copy** of
`docs/reviews/` and requiring the `NONE` set to be unmoved.

- **It subtracts rather than assumes.** Commits that genuinely touch the
  claimed file are removed by measurement, so the arm keeps its meaning
  if that file is ever edited again (one commit, `105a979`, ever has).
- **It carries its own non-vacuity check.** "Unmoved" is true of a
  checker that does nothing, so the arm also requires that something was
  exposed to the plant: `exposed: 40 (want >0)`.
- **No arm mutates the tree.** WIDTH uses `--backlog` into a
  `TemporaryDirectory` and `--reviews` into a `copytree`, like the other
  nine.

**Both arms, and WHICH arm - never the exit code:**

| amputation | probe | the arm that moved |
|---|---|---|
| checker reverted to `22c9873` | 9/10 | **WIDTH only**, `NONE 17 -> 0` |
| `claiming = list(in_range)` | 9/10 | **WIDTH only**, `NONE 12 -> 0` |
| range required before the content test | 9/10 | **WIDTH only**, 5 wrongly cleared |
| shipped | **10/10** | - |

The first amputation reproduces R17's control exactly: one declaration
claiming one seven-character file, `COVERED BY NOTHING` to **zero**.

---

## 5. Findings raised while doing this

### 168-F1 (High) - `6d8d02a` was cleared from the backlog by a round whose range does not contain it

`review-coverage-backlog.txt`, the `-8` note; commit `2fe3052`.

That commit deleted eight lines "because R17's declaration, merged just
above, now covers them". For `6d8d02a`:

    $ git merge-base --is-ancestor 6d8d02a 2eb2d2a ; echo $?
    1

R17's range is `8695101..2eb2d2a`, so it never contained `6d8d02a` and
never could have covered it. It measures `NONE` at `22c9873` under BOTH
the old code and the new. This is exactly the hazard the note itself
warned about, one line below where it warned about it.

**Fix (applied):** the line is back in the backlog, and the note is
rewritten in place to say seven of the eight stand and which one did
not. The other seven do stand - and mostly not for the stated reason:
their files are `.github/`, `docs/reviews/` and `scripts/`, which is
**R16's** declaration, not R17's.

### 168-F2 (Medium) - R17's own suggested fix converts 89 commits into a backlog of unreadable commits

`REVIEW-R17.md`, R17-H1 "Suggested fix":

```python
claiming = [r for r in rounds if sha in r.commits
            and any(r.claims(f) for f in files if not is_record(f))]
```

`any()` over an empty sequence is `False`, so every commit with no
non-record file - every clean merge, every record-only commit - becomes
`NONE`. Measured by applying it verbatim: `COVERED BY NOTHING` **17 ->
129**, `PARTIAL` 36 -> 8, and 89 of the 112 new `NONE`s are commits with
nothing in them to read. R17 flagged this itself in its §6 ("whether the
arms still pass with my suggested H1 fix applied" - not verified).

**Fix (applied):** the shipped rule tests `substantive` for emptiness
first and rules on content. Recorded here because the suggested fix is
quoted in the task description and in the brief, and someone will reach
for it again.

### 168-F3 (Low) - two decaying counts in the wiring gate's exemption prose

`check-checkers-are-wired.py`: the `check-review-coverage.py` exemption
said *"it exits 0 today at 58 recorded"* while the file held **43**, and
the `probe-coverage-ratchet.py` exemption said *"nine arms"*.

**Fix (applied):** "nine" -> "ten" (my change caused that one); the "58"
is **deleted rather than retyped**, per `DESIGN.md:1563-1566`
("described rather than counted... a count is a claim that decays on
every change"), with a one-clause note that it had already decayed. Only
the reason string is machine-checked, so neither was going to be caught.

### 168-F4 (nit) - the finding's citation had already drifted two lines

The brief and the task both cite `check-review-coverage.py:428-431`;
at `22c9873` the code is at **`:439-442`**. R17 cited it correctly
against its own pinned `2eb2d2a`. Nobody was wrong; the citation was
copied forward across eleven commits.

**Fix (suggested, not applied):** cite the SUBJECT
(`claiming = [r for r in rounds if sha in r.commits]`) rather than the
line span - the convention #109 applied to `ci.yml`'s 20 citations for
this exact reason. (`check-clause-citations.py` is NOT precedent for it:
I nearly wrote that it was, and it resolves by LINE into a sibling
checkout.) Not applied because the brief and the task description are
not mine to rewrite.

---

## 6. Corrections to my brief

1. **§C/§D: "read `REVIEW-R17.md` §3 before re-deriving the merge
   question" - §3 is not about merges.** R17 §3 is *"The 24 range
   artifacts, named"* and contains no discussion of `--cc`, merges, or
   an empty `--name-only`. The two withdrawals the brief means are
   **`REVIEW-R16.md` §3** and **`REVIEW-151-R1.md`**, "My own mistakes"
   item 2. I read both; the ruling in §3.2 rests on them. Following the
   brief's pointer literally would have found nothing and invited the
   third re-derivation it was written to prevent.
2. **§E: "expect your fix to INCREASE the outstanding count. A fix that
   leaves it unchanged did nothing."** Refuted by measurement - see §2.
   The count cannot rise from this fix; the KIND is what moves. The
   brief's instinct was right that a green report would be suspect, and
   its stated test for that was the wrong instrument.
3. **§C: `:428-431`** - see 168-F4, `:439-442` at `22c9873`.
4. **§B: "Nobody else is in the tree as I write."** Two agents were
   (`suborch-166`, `suborch-167`). I touched none of their files;
   `check-checkers-are-wired.py` (168-F3) is owned by neither.

---

## 7. Gates, each exit code on its own line

Run in `fmj-worktrees/w168` at `22c9873` + this branch:

    ruff check .                                   0
    ruff format --check .                          0
    mypy .                                         0
    pytest -q            887 passed, 0 skipped     0
    pre-commit run --all-files                     0
    check-review-coverage.py                       0   (48 recorded = 48 measured)
    probe-coverage-ratchet.py     10/10 arms       0
    check-checkers-are-wired.py                    0
    check-adr-numbers.py                           0
    check-clause-citations.py                      0
    check-coupling.py docs/DESIGN.md               0
    check-coupling-controls.py                     0
    check-coupling-sweep.py                        0
    check-cross-references.py                      0
    check-design-citation-shape.py                 0
    check-design-citations.py                      0
    check-design-freeze.py                         0
    check-env-vars-are-declared.py                 0
    check-no-errexit.py                            0
    check-no-sigpipe-pipelines.py                  0
    check-obligations.py                           0
    check-plan-measurements.py                     0
    check-resweep-verdicts.py                      0
    check-settings-are-read.py                     0
    check-standards-citations.py                   0

`docs/DESIGN.md` is untouched - no ADR is needed and none is added.

---

## 8. What I did NOT verify, separated from what I did not attempt

**COULD NOT SETTLE:**

- **Whether the 7 surviving clearances of `2fe3052` are each covered for
  the reason its message gives.** I settled that they are covered under
  the NEW rule (they are absent from the measured set, which now
  requires a claimed file), and that their paths match R16's
  `docs/reviews scripts .github`. I did not open each declaration and
  attribute each commit to a named round.
- **Whether `nothing_to_read` should ever be gated.** 89 of 324 trunk
  commits are scored without reading anything, on two prior rounds'
  rulings. That is defensible and it is also a third of the container.
  I did not design a check for it.

**DID NOT ATTEMPT, deliberately:**

- **R17-H2's corrected path list (#169).** §F forbids widening any
  declaration until this lands, and that is right. It is now unblocked.
- **Wiring either script into `ci.yml`.** `ci.yml` belongs to
  `suborch-167` this run, and the gate's own exemption says it belongs
  on pull requests. Unchanged.
- **`CONTRIBUTING.md`.** Its measurement paragraphs describe harnesses,
  not this gate, and `suborch-166` holds docs this run.
