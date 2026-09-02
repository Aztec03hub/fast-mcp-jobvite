<!-- REVIEW-COVERS: 203e5af..e9702ff -->

# REVIEW-151-R1 — the coverage gate becomes a ratchet

Fresh adversarial round over the single unpushed commit `e9702ff` on `main`.
Reviewer: `review-151`. Date: 2026-09-01. Nothing here was written by the author
of the subject, and nothing in it was taken on the author's word.

**Verdict: 0 Critical, 2 High, 5 Medium, 2 Nits.** The mechanism is sound and the
probe is not vacuous — all 8 arms die under their own amputation, and the 58-entry
baseline reproduces exactly from git without running the checker. The two Highs
are (H1) the ratchet's *clearance* direction, which no arm perturbs and which one
one-line file can walk from 58 to 0 at exit 0, and (H2) a prose claim about the
one-merge lag that is already false by 6 in this tree.

## What I ran

Everything below was executed in a detached worktree at `e9702ff`
(`fmj-worktrees/rev151`), so nothing touched the shared tree. CI's invocation
(`uv run --frozen python ...`) throughout.

| Question | Method | Result |
|---|---|---|
| 8 arms vacuous? | put each defect **back** into `check-review-coverage.py`, run the probe, read WHICH arms report FAIL | 8/8 die under their own amputation, 0 survivors |
| Baseline honest? | independent re-derivation from git; the checker never run | 58 derived = 58 recorded, 19 NONE / 39 PARTIAL, 0 kind disagreements, 0 subject mismatches, all 58 ancestors of `origin/main` |
| Ratchet defeatable? | constructed the attacks | one **does** work (H1); `--backlog /dev/null`, an empty backlog alone, and quoted declaration examples all fail closed |
| One-merge lag | ran the checker against local `main` | `ENTERED, unrecorded: 6`, not 1 |
| Gates | `ruff check`, `ruff format --check`, `mypy` on both files | 0, 0, 0 |

### The amputation matrix (question 2 — none of the arms is vacuous)

Each row puts one defect back and lists the arms that went FAIL. Probe exit was 1
in every row; **I scored on WHICH arms died, never on the exit code.**

| defect restored in `check-review-coverage.py` | arms that DIED |
|---|---|
| ratchet always returns 1 | `BASELINE` |
| `entered = []` | `ENTERED`, `CANCEL` |
| `cleared = []` | `CLEARED`, `CANCEL` |
| **set comparison replaced by a COUNT comparison** | `CANCEL`, `KIND` |
| `moved = []` | `KIND` |
| absent backlog returns `{}` instead of exit 3 | `MISSING` |
| malformed kind `continue`s instead of exit 3 | `MALFORM` |
| duplicate sha `pass`es instead of exit 3 | `DUPLICAT` |

The fourth row is the author's central claim tested by construction rather than
taken: a count-based ratchet **does** pass the CANCEL case (and the KIND case),
and a set-based one does not. The claim holds.

### The baseline, re-derived without the checker (question 3)

I re-implemented the measurement with different mechanics (line-scan harvesting of
declarations rather than a `re.MULTILINE` regex, `git log`/`rev-list` walked
separately) and compared to `review-coverage-backlog.txt`:

    derived 58 outstanding; recorded 58
    in derived, NOT recorded: []
    recorded, NOT derived  : []
    kind disagreements     : {}
    derived  NONE=19 PARTIAL=39
    recorded NONE=19 PARTIAL=39
    recorded subjects that do NOT match git: 0
    recorded shas NOT ancestors of origin/main: []

`UNDECLARED_BY_HISTORY` is **not stale**: its 7 names are exactly the 7 population
documents my independent scan found carrying no declaration. `RECORD_PATHS` is
**not stale**: its 3 entries account for all 35 skipped record files, and the
`docs/briefs` exclusion from it is consistent with this commit (see L1). The
rewritten exemption reason in `check-checkers-are-wired.py:76` is accurate about
the ratchet — but see M1 for its surviving twin.

---

## Findings

### H1 — The ratchet has two inputs and all 8 arms perturb only one. Clearance is free, and the green path drops the caveat.

`docs/reviews/probe-coverage-ratchet.py:99-221` — every arm (ENTERED, CLEARED,
CANCEL, KIND, MISSING, MALFORM, DUPLICAT) perturbs the **recorded** side. Not one
perturbs the **measured** side, i.e. the declarations that produce it. That is the
blind spot, and it is exploitable.

**Measured, not argued.** In the worktree I created one file,
`docs/reviews/REVIEW-R99.md`, whose entire content is:

    <!-- REVIEW-COVERS: 8695101..9e04411 -->

    # R99

and pointed `--backlog` at a file holding one comment line. The checker printed:

    PARTIALLY covered - some files claimed by nobody: 0
    COVERED BY NOTHING: 0
    Backlog recorded in empty.txt: 0
    Backlog measured now: 0
    Every trunk commit is fully covered by a declared round.
    exit 0

58 → 0, with nothing read by anyone, in one new file plus one deletion.

The docstring at `check-review-coverage.py:101-104` does say the checker cannot
prove a round read anything, and that limit is honestly stated. Two things make
this a High anyway:

1. **#151 changes the incentive.** Before this commit green was unattainable, so
   nobody had a reason to clear a line. Now green is the normal state and the
   only way to shrink the backlog is a declaration nobody checks.
2. **The output is most reassuring exactly where the evidence is weakest.** The
   caveat at `check-review-coverage.py:466-469` ("a declaration is a claim by its
   author") is printed **only on the failure path**. On the green path with an
   empty measured set, line 477 prints the single strongest sentence the file
   contains — `Every trunk commit is fully covered by a declared round.` — with no
   caveat at all. The docstring's promise at line 80, "a HOLDING RATCHET IS NOT
   FULL COVERAGE **and the output says so**", is true at lines 473-475 and false
   at line 477.

**Fix, three parts:**

- Move the `NOTE:` block out of the `if entered or cleared or moved or unexplained:`
  branch at `check-review-coverage.py:464-469` so it prints on **every** exit,
  green included.
- Change line 477 to state what was actually established, e.g.
  `Every trunk commit falls inside some declared round's range and paths.` and
  print the population beside it (`N documents, M declaring`), so a one-line plant
  is visible in the output a reader skims.
- Add a **9th arm, `PLANT`**, to `probe-coverage-ratchet.py`: write a
  `REVIEW-R99.md` carrying only a broad declaration into a temporary directory
  passed via a new `--reviews PATH` flag (the same shape as `--backlog`, and for
  the same reason — no arm may touch the tree), and assert the checker names the
  plant document in its output. That converts a documented limit into a measured
  one and closes the arms' one-sided container.

Longer term this wants a ruling rather than code: a line **leaving** the backlog
should name the round that cleared it, the way a line arriving must name why it
grew. Worth its own task.

### H2 — "red for exactly one commit every time" is wrong; it is every commit the push adds, and it is 6 right now.

`docs/reviews/check-review-coverage.py:97-99`, repeated at
`docs/reviews/review-coverage-backlog.txt:18-21` and in the commit message
("On a push to main it would be red for exactly one commit every time").

The reasoning that a commit cannot record its own sha is right, and the conclusion
that this belongs on pull requests is right. The *quantity* is wrong. `rev-list
CONTAINER_BASE..ref` enumerates every commit a push adds, not just the tip: a
merge of N branch commits adds N+1 unrecorded shas at once. Measured on this tree:

    $ uv run --frozen python docs/reviews/check-review-coverage.py --ref main
    Backlog recorded: 58
    Backlog measured now: 64
    ENTERED, unrecorded: 6
      203e5af NONE Merge fix/116-timeouts: ...
      3d9445c NONE #116: the worklog, ...
      6fe2d73 NONE #116: bring both new checkers ...
      816007f NONE #116: the pid1 wait bound, ...
      aa893a2 NONE #116: bind each timeout bound ...
      e9702ff NONE #151: the coverage gate becomes a ratchet ...

Six, not one. The backlog was measured against `origin/main` (`9e04411`), which is
five commits behind local `main`; the commit message's "58 recorded, 58 measured,
exit 0" is true **only against `origin/main`** and does not say so. The moment
this is pushed the gate is red at 6, and "exactly one" is the sentence that would
make a reader treat that as a bug in the checker.

**Fix:** rewrite the docstring sentence and the backlog header in place (do not
append) to say: *"Run it on a push to main instead and it is red for every commit
that push added — a merge of N branch commits makes it N+1 at once."* And state
the ref in the commit message and worklog wherever "58 measured" appears:
"58 measured **against `origin/main` at 9e04411**". Separately, the five #116
commits are already on local `main` and are not in the backlog; either push them
and record them, or record them now, so that the lag really is one commit.

### M1 — the rewritten exemption reason has a surviving twin in `docs/README.md:26`

The commit correctly rewrote (rather than annotated) the stale reason in
`check-checkers-are-wired.py:76`. It missed the same claim one file over:

    docs/README.md:26 | ... `check-review-coverage.py` is built and deliberately
    UNWIRED - it exits 1 today, and a gate that lands red is one people learn to
    ignore.

`it exits 1 today` is false as of this commit; it exits 0. Two artifacts now state
opposite facts about the same gate, and the README is the one a newcomer reads.

**Fix:** rewrite that sentence in `docs/README.md:26` in place to match the new
exemption reason — unwired because it belongs on pull requests against
`origin/main` and `ci.yml` is owned elsewhere this run, not because it is red.

### M2 — the backlog header documents a line format the parser rejects

`docs/reviews/review-coverage-backlog.txt:3-4`:

    # The trunk commits that no review round covers, one per line, as
    # `<short sha> <subject>`.

The actual format is `<short sha> <KIND> <subject>`, and `read_backlog`
(`check-review-coverage.py:236-242`) exits **3** — broken instrument — on a line
whose second field is not `NONE` or `PARTIAL`. A reader who follows the header's
own stated format bricks the gate. The worklog gets this right
(`WORKLOG-151-coverage-ratchet.md:22`), so the two records disagree.

**Fix:** `# \`<short sha> <NONE|PARTIAL> <subject>\`. A line with no kind field is
a broken instrument, not a shorter line: the checker exits 3.`

### M3 — the recorded subject is never checked against git, and no arm covers it

`check-review-coverage.py:248` stores the subject, and the ratchet at lines
438-442 compares only shas and kinds. Nothing ever compares a recorded subject to
`git log -1 --format=%s`. A backlog line can carry any text at all — a subject
copied from the wrong commit, or one that went stale — and the gate stays green.
The probe has no arm for it either.

I verified independently that all 58 subjects currently match git, so this is a
missing guard rather than a present error. But the subject is the only part of
the record a human reads to decide whether an entry still makes sense, and it is
the only field with no gate.

**Fix:** in the ratchet block, add
`wrong = [sha for sha in set(recorded) & set(measured) if not git("log", "-1", "--format=%s", sha).startswith(recorded[sha][1])]`,
print `SUBJECT <sha> recorded ... measured ...` for each, and include `wrong` in
the `return 1` condition at line 464. Add a `SUBJECT` arm to the probe that
rewrites one entry's subject in a temporary backlog and asserts exit 1.

### M4 — the new 8-arm control is invisible to the checker that finds unwired controls

`check-checkers-are-wired.py:131-133` enumerates its container as
`docs/reviews/check-*.py` and `docs/reviews/check-*.sh`. `probe-coverage-ratchet.py`
begins with `probe-`, so it is outside that container: it is not wired into
`ci.yml`, and — unlike `check-review-coverage.py`, which at least sits in the
exemption register with a reason — **no gate can ever report it as unwired**. It
exists only as a thing a person remembers to run.

This is the class already recorded as tasks #149 and #155, but this commit adds a
new instance of it, and the worklog's "NOT DONE" section
(`WORKLOG-151-coverage-ratchet.md:82-92`) discusses wiring the *checker* and is
silent about the *probe*.

**Fix:** add a sentence to the worklog's NOT DONE section naming the probe as
hand-run-only, and name `docs/reviews/probe-coverage-ratchet.py` explicitly in
#155's widening so it lands with a step or an exemption rather than silently.

### M5 — the short-sha width is not pinned, so the whole baseline can invalidate at once

`check-review-coverage.py:434` and `:436` call `git rev-parse --short`, which
honours `core.abbrev=auto` — git lengthens the default abbreviation as the object
count grows. The backlog stores 7-character shas as literal dictionary keys. The
day git picks 8, every measured sha stops matching every recorded one: 58 ENTERED
and 58 CLEARED in a single run.

It fails **closed** (red), which is the right direction, so this is a Medium and
not a High. But it fails as an uninterpretable 116-line diff that looks like the
instrument broke, and the repo's own history says a gate that looks broken gets
switched off.

**Fix:** `git("rev-parse", f"--short={SHORT}", sha)` with `SHORT = 7` as a named
module constant beside `CONTAINER_BASE` and a comment saying why it is fixed
rather than derived (the same argument as R12-H3), or normalise the recorded side
through `git rev-parse` before comparing so both sides are full shas.

### N1 — a bare declaration line inside a review document is indistinguishable from a real one

Measured against a planted `REVIEW-R99.md` (four bodies, one run each):

| body of the line | counted as a real declaration |
|---|---|
| `<!-- REVIEW-COVERS: ... -->` at column 0 | **yes** |
| the same, indented four spaces | no |
| the same, wrapped in backticks | no |
| the same, with trailing prose | no |

The anchors in `DECLARATION` (`check-review-coverage.py:126-131`) are doing real
work and the three quoted forms are correctly ignored. The residual risk is narrow
but real: a future review document that teaches the format by pasting an
unindented example creates a phantom round covering whatever range the example
names. `REVIEW-R12.md:576` already quotes a full declaration and is safe only
because it is backticked with prose after it.

**Fix:** add one sentence to the docstring's PATHS section (around line 37, whose
own examples are already indented): *"An example of this line must be indented or
fenced. At column 0 it is not an example, it is a declaration."* Optionally
require the declaration within the first 5 lines of the document.

### N2 — a count printed without its container

`check-review-coverage.py:417` prints
`Record files skipped (not the work, an account of it): 35` with no denominator.
35 out of how many files examined? The house rule this repo enforces everywhere
else is that a count without its container is not a measurement — and this exact
file names that rule at lines 413-416 while printing a bare number one line later.

**Fix:** track the total files examined and print
`Record files skipped: {records_skipped} of {files_examined} files in partially-claimed commits`.

### L1 — an unmentioned 110-line brief rides along in the commit

`docs/briefs/BRIEF-147-ci-step-selection-bias.md` is +110 lines in `e9702ff` and
the commit message — which is otherwise exhaustive, down to why there is no
`--write-backlog` — never mentions it. `docs/briefs` is deliberately **not** in
`RECORD_PATHS` precisely because a brief instructs an agent and has carried
substantive rulings (`check-review-coverage.py:156-158`), so this is in-scope
content landing unannounced in a commit about something else.

**Fix:** add one line to the commit message naming the brief and why it is here
(`suborch-147`'s dispatch, written the same session), or split it into its own
commit before pushing.

---

## What I tried that did NOT break it

Reported because an absence is a claim about where I looked.

- `--backlog /dev/null` → exit 1. Fails closed.
- An empty backlog with the real declarations → exit 1, 58 ENTERED. Fails closed.
- A planted declaration with the **real** backlog left in place → exit 1,
  `CLEARED, still recorded: 58`. The plant alone is not enough; H1 needs both
  halves, which is the set-vs-count property working as designed.
- Deleting a declaration to move coverage → produces CLEARED entries, red.
- Quoted / indented / trailing-prose declaration examples → not counted (N1).
- `ruff check`, `ruff format --check`, `mypy` on both files → clean.

## My own mistakes, corrected

Three, all mine, all caught before they reached a finding.

1. **I nearly filed a Critical that was my instrument, not the subject.** My
   independent harvester used an unanchored regex and reported
   `REVIEW-R12.md: 2 declaration(s)` — which, if true, would mean the
   duplicate-declaration refusal at `check-review-coverage.py:308-312` was blind
   to a real second declaration. Reading `REVIEW-R12.md:576` showed the second
   occurrence is backtick-quoted with trailing prose, and the checker's
   `^<!--...-->\s*$` anchors exclude it correctly. My looser regex was wrong; the
   subject was right. It survives only as N1, which is a much smaller claim.
2. **I wrote up "a clean merge reports zero files, so it is scored fully covered
   without any path check" and withdrew it.** `git show --name-only` defaults to
   `--cc` on a merge: `92cb89b` prints 4 files (an evil merge), `203e5af` prints
   0 (a clean one). But `rev-list` already enumerates each branch commit
   individually, so the merged content *is* path-checked where it lives, and my
   independent run found **zero** clean merges sitting inside a declared range
   with zero files. No finding.
3. **I expected `--backlog` to be an override that could be pointed somewhere
   harmless.** Every substitution I tried fails closed. The flag is what its
   comment at lines 354-359 says it is.

## One consequence of this document

`REVIEW-151-R1.md` matches the checker's population regex, so it enters the
population the moment it lands. It carries a `REVIEW-COVERS` declaration at line 1
for exactly that reason — a document in the population with no declaration and no
`UNDECLARED_BY_HISTORY` entry lands in `unexplained` and returns 1. Verified: with
this file present the checker still exits 0 against `origin/main`.
