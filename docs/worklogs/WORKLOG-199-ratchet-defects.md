# WORKLOG — #199 (R20-M3) + #200 (R20-L1), and R20-N3

`suborch-199`, branch `fix/199-ratchet-defects`, cut from LOCAL `main` at
`6e56d21`. Fix at `5bcdb45`. Not merged, not pushed.

**Headline: of the three defects, ONE has a live effect today and TWO
measure exactly ZERO.** They are still worth fixing, but a fix whose
measured effect is zero must not be written up as a closure.

---

## §1 — What I measured BEFORE fixing

### The brief's numbers, re-derived

| Claim in the brief | Measured | Verdict |
|---|---|---|
| origin is "~38 commits behind" | `git rev-list --count origin/main..main` = **39** | close, and it moved |
| controls have 11 arms, floor 11 | 11 rows, `ROW_FLOOR=11` | correct |
| "the record is empty right now" | 0 non-comment lines | correct |
| "21 cited names" (§C) | **22** at my branch point | wrong, and the 22nd was the brief itself |
| R20-M3: "the record has two entries today" | **zero** | R20 was stale by the time I read it |
| task #199: "the record has one entry today" | **zero** | also stale |

Three documents gave three different counts of one file, and all three
were wrong in the same direction. The file empties itself faster than
anything describing it can keep up — which is itself the evidence for
the ruling in §3.

### #199 — is a bare recorded line really accepted?

**YES. Confirmed by probe, exit code read on its own line.**

    record contains exactly:  REVIEW-ABSENT.md
    ...
    Recorded as known-missing: 1
    Every report a brief cites is committed, or recorded as lost.
    rc=0

**And the neighbouring form is NOT a defect, which narrows the finding.**
A single-space separator (`REVIEW-ABSENT.md single-space reason`) makes
`partition("  ")` put the WHOLE LINE in the name, which then matches no
citation and trips *two* loud branches:

    ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
    ::error::A RECORDED ENTRY IS NO LONGER CITED BY ANY BRIEF.
    rc=1

So the silent hole is exactly the no-reason form, not "sloppy separators"
generally. R20 did not distinguish these and the fix would have been
wider than the defect if I had not checked.

### #199 second half — do lines actually go stale?

`git log` on the record file: **4 commits, all inside 2 days**, ending
`900daf5 "The in-flight record is EMPTY: every entry it ever held has now
expired"`. Every line the file has ever held expired within about a day.

**The permanent excuse is a HAZARD, not an observation.** I am not
willing to call it absent — 4 commits over 2 days is a sample that can
support neither conclusion — but nothing in the record's history shows a
line surviving.

### #200 — both halves measure ZERO

Over the 73 briefs at my branch point:

- **22** distinct report names cited; **20** citations carry a
  `docs/(reviews|worklogs)/` prefix.
- Honouring the path changes **0** verdicts: all 20 resolve at exactly
  the path written.
- **0** report basenames are tracked at more than one path, so the
  basename comparison had nothing to get wrong yet.
- **0** subdirectories exist under `docs/briefs/`; `glob` and `rglob`
  both find 73 files.

Also measured, and it matters for the record's vocabulary: **6 names are
cited BOTH ways**, bare in one brief and prefixed in another. That is why
I kept the record keyed on the BASENAME and added the path check as a
separate branch, rather than re-keying the record on the citation string
as R20's fix implied. Re-keying would have split those 6 into two keys
each and forced a migration for no measured gain.

---

## §2 — THE GATE WAS RED ON `main`, AND THE BRIEF IS WHY

First bare run in my worktree:

    ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
      REVIEW-CHECKLIST.md   cited by BRIEF-199-ratchet-defects.md
    rc=1

`BRIEF-199` §B lists the three names a human cleared from the record, and
the first of them is `REVIEW-CHECKLIST.md` — the truncated name this very
checker's docstring exists to warn about, retracted at `1985471`, a file
that has never existed. **Writing the retracted name out in full was
itself a citation**, so the brief about the gate put the gate into
failure the moment it was committed.

**Fixed by rewriting the brief's prose in place** to name the retraction
rather than reproduce the token. Recording the line was the wrong remedy:
it would have been a waiver for a file that never existed, in a file
whose header says recording is not a waiver.

**The class is not fixed and is not mine to rule on.** The gate's
population is "every report-shaped name written in a brief", and it
cannot distinguish a CITATION from a QUOTATION. Any brief that discusses
the gate is inside its own population. `fa94f77` on `main` shows
team-lead hit the same thing independently and in the same hours
(*"The gate went red on my own brief"*), so this is at least twice
measured. An `EXEMPT`-style marker is the obvious remedy and I think it
is the wrong one — this project has already measured a bare-substring
marker inflating 47 → 61 purely from prose *about* the marker, so the
most careful writers would widen the hole fastest.

---

## §3 — The ruling on #199, and what I deliberately did NOT build

The brief left the choice open: require a reason, require a date and age
lines out, or leave the file alone.

**Required: a reason, with a leading ISO date.** `read_record` refuses a
line that is not `<basename>  <ISO date> <reason>` with **exit 2** — the
broken-instrument code, not a failure — for the same reason an unreadable
index refuses: the gate cannot say anything about the briefs until its
own record parses. Migration cost was zero because the record is empty.

**REFUSED: expiring a line on a timer.** The date buys only its VISIBLE
half — the summary now prints `recorded NNNd ago` per line, proved on a
fixture:

      recorded   19d ago  REVIEW-ABSENT.md

A gate that goes red by the calendar is red by construction, and this
project's own record is that such gates get switched off. R20 asked for
aging; it gets visibility, and the human stays in the loop deliberately.
That is a partial refusal of my brief's suggested fix and it is stated
here rather than quietly implemented.

**The anti-vacuity problem the brief named, and how I avoided it.** The
record is empty, so every arm is over a fixture, and two of my three new
#199 arms expect a REFUSAL — which a checker that refuses *everything*
would also satisfy. **A18 exists solely to kill that**: a well-formed
line must still be ADMITTED at rc=0. Without it the pair is vacuous.

---

## §4 — What changed

| File | Change |
|---|---|
| `check-brief-report-references.py` | prefix CAPTURED; `tracked_index` returns paths + basenames; `read_record` returns `(record, malformed)` and refuses; `cited()` uses `rglob` and returns cited paths; new `misplaced` branch; age display |
| `check-brief-report-refs-controls.sh` | 11 → **20** rows, `ROW_FLOOR` 11 → **20**; every existing fixture reason given an ISO date |
| `brief-report-refs-known-missing.txt` | header documents the enforced format and says the date does NOT expire a line |
| `BRIEF-199-ratchet-defects.md` | the dangling citation removed, and §2 above recorded in it |

**THE LEFT BOUNDARY IS UNTOUCHED.** The change is on the line BELOW the
lookbehind: `(?:docs/...)?` → `(docs/...)?`. A10 and A11 both still pass
and I checked that specifically because the brief told me to.

New arms, every one paired in both directions:

| Arm | Proves |
|---|---|
| A12 → 1 | a citation at the WRONG path fails |
| A13 AMP `misplaced` → A12 at 0 | ...and that branch is what does it |
| A14 → 1 | a brief in a SUBDIRECTORY is scanned |
| A15 AMP `rglob`→`glob` → A14 at 0 | ...and recursion is what does it |
| A16 → 2 | a bare name with NO reason REFUSES |
| A17 → 2 | a reason with no ISO date REFUSES |
| A18 → 0 | **a well-formed line is still ADMITTED** (anti-vacuity) |
| A19 AMP well-formedness → A16 at 0 | ...and this is exactly the pre-fix rc=0 |
| A20 AMP refusal → A5 at 1 | R20-N3: the refusal is REACHED, not merely reachable |

---

## §5 — MY OWN FIX SHIPPED A DEFECT, AND ITS OWN ARM CAUGHT IT

A19 failed on its first run: `rc=1, wanted 0`. Reproduced:

    File ".../amp.py", line 236, in main
        stamp = reason.split()[0]
                ~~~~~~~~~~~~~~^^^
    IndexError: list index out of range

The age display assumed the refusal above it had already rejected an
empty reason. **A16 could not see this** — the refusal fires first and
returns 2 before the display runs. Only A19, which *removes* that
refusal, exposed it, turning the expected rc=0 into a traceback at rc=1.

Two things worth keeping:

- **A guard that holds only while its neighbour holds is not a guard.**
  My display was correct exactly as long as the code above it stayed put.
- **The arm that found it was written to test the neighbour, not the
  display.** The amputation earned its keep against the same commit that
  introduced it, which is the second time this file has done that (A8 was
  the first).

---

## §6 — Gates, each exit code read on its own line

    uv run --frozen python docs/reviews/check-brief-report-references.py   rc=0
    bash docs/reviews/check-brief-report-refs-controls.sh                  rc=0  20/20
    uv run --frozen python docs/reviews/check-row-floor-exactness.py       rc=0
    python3 docs/reviews/check-row-floor-exactness.py --self-test          rc=0  16/16
    uv run --frozen python docs/reviews/check-checkers-are-wired.py        rc=0
    uv run --frozen ruff check .                                           rc=0
    uv run --frozen ruff format --check .                                  rc=0  138 files
    uv run --frozen mypy                                                   rc=0  138 files
    shellcheck --severity=warning -x docs/reviews/*.sh                     rc=0

The floor control, run AFTER committing because it refuses a dirty tree:

    bash docs/reviews/check-row-floor-controls.sh \
      docs/reviews/check-brief-report-refs-controls.sh                     rc=0
    HARNESS-RESULT ... rows=19 floor=20 fired=19/19 status=breach
    CONTROL FIRED: ... loses 1 row(s) ... exiting 1.
    restored: byte-identical to the backup
    restored: and identical to the index

**`actionlint` is NOT installed in this environment** (`command -v
actionlint` found nothing). I did not run it and I am not claiming it.

The gate itself, bare, is now GREEN where it was RED at my branch point:
73 briefs, 21 names cited, 0 dangling, 0 misplaced.

### Checked against CURRENT `main`, not just my base

`main` moved 6 commits under me while I worked. My stricter checker run
against `main`'s tree — 74 briefs, `git ls-tree` of `main` as the index —
gives **21 cited, 0 dangling, 0 misplaced, rc=0**. The merge will not
red the trunk on this gate.

I did NOT run the full `pytest` suite. Nothing in `tests/` or `src/`
references any changed file (`grep -rn` for the four names returned
nothing), and the branch touches only `docs/`. That is a stated reason,
not a skip: if the fold wants the floor re-measured it is Tier 0's run.

---

## §7 — Findings I am reporting rather than fixing

1. **A gate cannot tell a citation from a quotation** (§2). Twice
   measured in one night, by me and by team-lead independently. Needs a
   ruling, and I argue against a substring marker.

2. **`--briefs` at a nonexistent path exits 0 having scanned nothing.**
   I hit this on myself: a bad `git archive` extraction gave
   `Briefs scanned: 0 ... rc=0`. `rglob` on a missing directory returns
   empty without erroring, identical to a clean tree. CI runs the gate
   BARE so the default path is right and this is not live — but
   `tracked_index` already distinguishes unreadable from empty and
   `--briefs` does not. **Suggested fix:** refuse with exit 2 when
   `args.briefs` does not exist, plus one arm. I left it because it is
   outside both my tasks and belongs on the board, not in a silent fix.

3. **R20-N3's suggested `sed` would have matched nothing.** It proposed
   `s/^    if names is None:$/    if False:/`; #200 renamed that variable
   to `index`. The arm would have printed `ANCHOR NOT FOUND` rather than
   running — the harness catches that, which is why A20 is honest, but
   the suggestion as written was already stale.

---

## §8 — What I did NOT verify

- **`actionlint`** — not installed here. Not attempted, not claimed.
- **The full `pytest` suite and its floor** — reasoned around (§6), not
  run. If the fold disagrees with my reasoning, this is the item to run.
- **Whether the permanent-excuse hazard is real over a long horizon.**
  The record is 2 days old with 4 commits. I can say no line has yet
  survived; I cannot say none will. This is genuinely unsettleable today,
  not something I skipped.
- **CI behaviour of the new exit-2 path.** I ran the checker's exit 2
  locally and the controls assert it, but I did not watch a CI run
  distinguish exit 2 from exit 1 in the workflow step. The step calls the
  script directly, so any nonzero fails it either way; what I have not
  proven is that the *distinction* survives into CI's reporting.
