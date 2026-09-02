# REVIEW-R19 — twenty-three commits, most of them fixes to R18's findings

<!-- REVIEW-COVERS: e845839..6f1d2ea PATHS: scripts .github/workflows/ci.yml docs/reviews docs/adr docs/DESIGN.md docs/DESIGN-FREEZE.txt docs/README.md -->

Reviewer: `review-r19` (Tier 1). Worktree `fmj-worktrees/r19`, branch
`review/r19`, cut from `6f1d2ea` — the trunk tip when I started, and the
head the brief's §B named. **Nothing was pushed, nothing was merged,
nothing was fixed.**

**The trunk moved under me.** By the time I ran the coverage checker,
`origin/main` was `6e4fae3` and `e845839..origin/main` was **27**
commits, not 23. The four extras are `2945f5e` (the R19 brief),
`d0f8d85`, `32aa9a8` (handoff v6) and `6e4fae3` — all after my pin. My
reading is pinned to `6f1d2ea` throughout and my declaration stops
there, so those four remain outstanding and are not mine to claim.

Every number below was measured in this worktree. Where I corrected my
own instrument mid-review, I say so.

---

## Summary

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 3 |
| Low | 2 |
| Nit | 2 |
| **Total** | **7** |

**No Highs.** Seven of the eight R18 fixes I could measure are real and
I checked them by execution rather than by reading the diff. Three of
the fixes left a residue that is the same class one column over, which
is what §C1 told me to assume, and I found three rather than one.

---

## 1. MEDIUM — M1: the fix for R18-L1 prints a false all-clear over its own skip line

`scripts/check-secrets-baseline.py:344-351` against `:273-278`
(commit `9fbef31`).

R18-L1 asked that each silent `return` announce itself. It does — and
`9fbef31` correctly found a **fourth** instance R18 had missed, inside
the fix for R18-H1. That half is right.

The residue is in the CALLER. `_untracked_paths` returns `[]` both when
the listing is genuinely empty and when `git ls-files` **failed**:

```python
    except (OSError, subprocess.CalledProcessError) as exc:
        # ... An empty list and a failed listing must not be confused
        # by the CALLER either ...
        print(f"\n  (untracked pre-check skipped: {type(exc).__name__})")
        return []
```

The comment states the requirement and the return value defeats it. The
caller has only `if not listed:` to work with, and its branch prints a
positive claim:

```python
    if not listed:
        # NOT a skip: there is genuinely nothing untracked. ...
        print("\n  (no untracked files to check ahead of tracking)")
```

**Measured, two arms, differing only in whether `git ls-files`
succeeds.** Arm A ran `_warn_untracked` with a stub `git` on `PATH` that
`exec`s the real one for every subcommand except `ls-files`, where it
exits 128. Arm B is a real, genuinely clean `git init` repository:

| Arm | `git ls-files` | Output |
|---|---|---|
| A | exits 128 | `(untracked pre-check skipped: CalledProcessError)` **followed by** `(no untracked files to check ahead of tracking)` |
| B (control) | succeeds, empty | `(no untracked files to check ahead of tracking)` **only** |

Arm B fires, so arm A is not vacuous: the all-clear sentence is emitted
in **both** cases and therefore distinguishes nothing. This is R18-H1's
own class — a reassuring line printed precisely where the gate failed to
look — rebuilt one column over, inside the commit that fixed R18-L1.

**Why Medium and not High.** R18-H1 was High because the all-clear was
the *only* output. Here the skip line is printed immediately above it,
so a human reading the log can tell. What is broken is that the second
sentence is false, that the code comment claims the caller cannot be
confused, and that anything grepping for the all-clear line gets a false
positive.

**Suggested fix.** Make the two cases different values, which is what
the comment already asks for:

```python
def _untracked_paths(git: str) -> list[str] | None:
    """... None means COULD NOT LOOK; [] means genuinely nothing."""
    ...
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"\n  (untracked pre-check skipped: {type(exc).__name__})")
        return None
```

and in `_warn_untracked`:

```python
    listed = _untracked_paths(git)
    if listed is None:
        return          # the skip was announced by the callee
    if not listed:
        print("\n  (no untracked files to check ahead of tracking)")
        return
```

Add a control arm (see M2) that drives `_untracked_paths` with a failing
`git` and requires `None`, so this cannot come back.

---

## 2. MEDIUM — M2: nothing gates the arm COUNT of `--controls`, so C7-C9 can be deleted with CI green

`.github/workflows/ci.yml:1680`, `scripts/check-secrets-baseline.py:503`
(commit `451faeb`).

`451faeb` closed R18-M4 by adding C7-C9 — the arms that exist *because*
R18-H1 shipped. They run: `ci.yml:1680` invokes
`python3 scripts/check-secrets-baseline.py --controls || exit 1`, and I
watched all nine pass. **But nothing holds the count.**

A claimed absence is a claim about where I looked, so: I looked in three
places and the path resolves in all three.

- `grep -n "floor\|FLOOR\|min_rows\|min-rows"` over
  `scripts/check-secrets-baseline.py` — the only hit is the tally line
  itself at `:503`. No floor in the file.
- `ci.yml:1680` passes no `--min-rows`, and the step is **not** routed
  through `scripts/ci-harness-gate.sh`, so it gets no floor from there.
- `docs/reviews/check-row-floor-controls.sh`'s `TABLE` does not name it,
  and `check-row-floor-exactness.py` enumerates `SCRIPTS.glob("*.sh")` —
  this is a `.py`, so it is outside that container by construction.

**AMPUTATION, run and read.** I copied the tree, deleted the `C7-C9`
block outright, and ran CI's exact step body against it:

| Arm | Output | Exit |
|---|---|---|
| Baseline (control) | `secrets-baseline-controls: arms=9 failed=0` | **0** |
| C7-C9 amputated | `secrets-baseline-controls: arms=6 failed=0` | **0** |

**SURVIVOR.** The three arms that catch R18-H1 were removed and the step
stayed green. That is verbatim R18-M4's own defect one column over: M4
was *"nothing makes it run"*, and this is *"nothing makes it keep
existing"*. The tally line prints the number and no reader is a gate.

**Suggested fix.** Give `--controls` a floor and gate on it, matching the
`ROW_FLOOR` vocabulary the `.sh` harnesses use. In
`check-secrets-baseline.py`'s `controls()`:

```python
ARM_FLOOR = 9  # C1-C9. Raise it in the same commit that adds an arm.
...
    print(f"secrets-baseline-controls: arms={len(arms)} failed={len(failed)}"
          f" floor={ARM_FLOOR}"
          f" status={'ok' if len(arms) >= ARM_FLOOR and not failed else 'breach'}")
    if len(arms) < ARM_FLOOR:
        print(f"::error::{len(arms)} arms against a floor of {ARM_FLOOR}"
              " - an arm was deleted, which is what the floor is for")
        return 1
```

Then extend `check-row-floor-exactness.py`'s container past `*.sh` so
the new floor is compared to a live count, which is also L1 below.

---

## 3. MEDIUM — M3: ADR-0034 made `Type: Deviation` load-bearing in a frozen document whose own vocabulary it cannot match

`docs/DESIGN.md` §13 at the freeze SHA (derived, `e3b5c97`), lines
**2064** and **2075-2076**; `docs/adr/README.md:12`.

This answers §C5's question directly: **`Both` is a problem the fix
created, not one it left open.**

The frozen paragraph now names a SELECTOR where it used to name a count:

```
2064:   **`Type: Deviation`** ADRs below do - NOT all of them, and the count is deliberately not
2075: teeth depend on it. **Every ADR from 0012 onward carries a `Type:` field**, `Deviation`,
2076: `Design change`, or `Both`. ...
```

Eleven lines apart, the same frozen paragraph (a) makes `Type:
Deviation` the instrument that decides which ADRs do job 1, and (b)
publishes a three-value vocabulary whose third value that instrument
does not match. `docs/adr/README.md:12` publishes the same three.

**Measured census at `6f1d2ea`:** 34 ADR files, `19` `Design change`,
`15` `Deviation`, `0` `Both`, and every file carries the line. So the
selector selects 15 today and `d29937f`'s claim that it "selects exactly
15" HOLDS.

The exposure is the first ADR ever typed `Both`. It would do job 1 — that
is what `Both` means — and the frozen sentence would silently stop being
true about it, exactly as `ADR-0023`'s `Standards deviation` did in
`d29937f`. `d29937f` fixed that instance by normalising three outliers
onto the published vocabulary; it did not close the class, because the
vocabulary still contains a value the selector cannot see.

`d29937f`'s message says this is **"NOT RULED HERE, deliberately:
whether a checker should gate the Type vocabulary ... `Both` is
published and used by nobody."** That frames it as a missing checker. The
sharper statement is that the frozen document's selector is incomplete
against the frozen document's own published vocabulary, and no checker
can repair a frozen sentence — only another ADR can.

**Correcting my own instrument:** my first census grepped `^Type:` and
returned **zero** hits across all 34 files, which would have been a
spectacular false finding. The field is `**Type:** X`. I re-derived
before writing anything down.

**Suggested fix — a decision for you, and it is cheap either way.**

1. *Preferred:* **retire `Both`.** It is used by no ADR, both README and
   the frozen design would then publish exactly the two values the
   selector matches, and `docs/adr/README.md:12` is not frozen so half
   the fix needs no ADR. The DESIGN.md half still needs one, so fold it
   into option 2's ADR and do both in one.
2. Or **keep `Both` and widen the selector**, which needs a Proposed ADR
   changing `:2064` to name `Type: Deviation` *or* `Type: Both`. More
   words, and it keeps a value nobody uses.

Either way, add the vocabulary checker `d29937f` declined: one selector
over `docs/adr/0*.md` asserting every `**Type:**` value is in the
published set, with a positive control that plants a fourth spelling and
requires red. That is what would have caught `ADR-0023` on the day.

---

## 4. LOW

### L1 — `probe-131-gate-state.sh` is the one CI-wired harness whose floor nothing checks for exactness

`docs/reviews/probe-131-gate-state.sh:330` (`ROW_FLOOR=12`),
`docs/reviews/check-row-floor-exactness.py:213`.

I measured the container rather than reasoning about it:

```
$ grep -rln "^ROW_FLOOR=" --include=*.sh .
26 files: 25 under scripts/, and docs/reviews/probe-131-gate-state.sh
```

`check-row-floor-exactness.py` builds `on_disk` from
`SCRIPTS.glob("*.sh")`, so `probe-131` is outside its population — while
being **wired into CI** at `ci.yml:1243`. Its floor is 12 and its live
count is 12, so there is no slack **today**; what is missing is the
thing that keeps them equal. The floor still protects against a deleted
row (12 rows against floor 12 breaches at 11), so this is Low, not
Medium: what it cannot catch is a floor *lowered* alongside a deletion,
which is the case `check-row-floor-exactness.py` exists for.

Task #149 ruled the container "STAYS `scripts/*.sh`". That ruling was
made when `9c08427` was **not on the trunk** — R18's §9 correction #2
says so explicitly — so the exempt set was empty when it was decided. It
is now one, and that member is in CI.

**Suggested fix.** Widen the container to the union of `scripts/*.sh`
and the `docs/reviews/*.sh` files `ci.yml` actually runs, and add
`probe-131-gate-state.sh|^(row|amputate) "|...` to
`check-row-floor-controls.sh`'s `TABLE`. If you would rather keep the
narrow container, the alternative is to say so *in the checker*: add an
`EXEMPT_BY_DECISION` dict with `probe-131-gate-state.sh` and its reason,
so the exemption is visible where the population is built rather than
implied by a glob. I prefer the first — #149's reason for the narrow
container was that the probe had a job of its own, and it now has a
floor of its own too.

### L2 — the frozen design carries the "from 0012 onward" boundary that `d29937f` deleted one file over

`docs/DESIGN.md` at the freeze SHA, lines **5-6** and **2075**.

`d29937f` deleted this clause from `docs/README.md:22` with an explicit
reason: *"ALL 34 carry it, ADR-0001 included ... The boundary clause is
DELETED rather than repaired: a boundary that has to be maintained is
the same defect as a count."* Its own message names why it did not reach
further — *"a DIFFERENT FILE from the one that ADR was about"* — and
then does not check the frozen design, which is the document ADR-0034 is
about and which `e3b5c97` had just edited.

Both surviving sites:

```
   5: ... ADR-0012 onward carries a
   6: `Type:` field, because an ADR does two different jobs here ...
2075: teeth depend on it. **Every ADR from 0012 onward carries a `Type:` field**, ...
```

**Measured:** all 34 ADRs carry `**Type:**`, ADR-0001 through ADR-0011
included, and I listed all eleven individually rather than trusting a
count.

**This is Low and I want to be precise about why: the sentence is not
false.** "Every ADR from 0012 onward carries a `Type:` field" is
literally true; it is a boundary that misleads by implicature and that
must be maintained forever. `docs/README.md`'s twin was deleted for
being exactly that. I am reporting the sibling, not claiming a lie.

I also checked the adjacent claim at `:2076` — *"The eleven below are
all `Deviation`"* — and it **HOLDS**: ADRs 0001-0011 are all typed
`Deviation`, including after `d29937f` renamed three others.

**Suggested fix.** `DESIGN.md` is frozen, so per PREAMBLE this is a
**Proposed ADR plus this report, not an edit**. Fold it into M3's ADR —
both changes are in §13, both are one sentence, and one ADR covering the
paragraph beats two touching adjacent lines. The edit is to drop "from
0012 onward" / "ADR-0012 onward" at both sites, leaving "Every ADR
carries a `Type:` field", which is what `docs/README.md` now says.

---

## 5. NITS

### N1 — the mirror step's skip path is green, printed, and unread

`.github/workflows/ci.yml:892-898` (commit `46b09c4`).

The fork guard is **right**, and I want to say so first: a branch inside
the `run:` block rather than an `if:` on the step is the correct call for
exactly the reason the commit gives, and I checked that `github.repository`
at `:889` is still the only repository-identity-dependent call in the
file.

The residue: the skip path `exit 0`s after four `echo`s. If this
repository is ever renamed or moved, the step prints "SKIPPED" forever
in a **green** step, and nobody reads the log of a green step. That is a
weaker form of the same "switched-off and broken render identically"
failure the guard was written to avoid — better, because a human who
looks will see it, but still invisible to anyone who does not.

**Suggested fix.** One word. Make the first line an Actions annotation so
it surfaces in the run summary rather than only in log text:

```bash
echo "::warning::SKIPPED: $THIS_REPO is not the repository the mirror copies FROM"
```

Keep the remaining three `echo`s as they are — the explanation belongs in
the log, the signal belongs in the summary.

### N2 — ADR-0034's blockquote says 33 where its own census says 34

`docs/adr/0034-...md:7` against `:43`.

The blockquote reads *"There are **33**"*; the census table eleven lines
down reads `34  total   (this ADR included)`. Both are defensible — the
blockquote is the finding as raised, before the ADR existed — but
`d29937f` rewrote the census **in place** and left the blockquote, so one
document now states two populations without saying they are measured at
different moments. This is the "a rewrite loses sentence-sized findings"
shape, at nit scale.

I checked the history rather than assuming: `git ls-tree` at `e3b5c97`
gives **34** ADR files and at `e3b5c97^` gives **33**, so the blockquote
is counting the population *before* this ADR and the table is counting
it after. Both numbers are true of different instants.

**Suggested fix.** Three words in the blockquote: *"There are **33**
others"*. That makes both figures true of the same instant and preserves
the finding as it was raised.

---

## 6. What I checked and found CORRECT

Measured, not read. This section is deliberately long: §A says agreeing
with R18 is not a wasted line.

**R18-H1 — the `-z` fix. CORRECT.** `scripts/check-secrets-baseline.py`
now uses `git ls-files -z` and `split("\0")`. All nine control arms pass,
exit 0. C7 (`"with space.md" in found`), C8 (`len(found) == 3`) and C9
(ignored file excluded) are a sound triple: C9 in particular blocks the
wrong fix ("stop excluding"), which is the arm most authors would not
have written.

**R18-H2 — the transport rows. CORRECT, and I re-measured it with R18's
own instrument rather than trusting either of you.** I planted
`raise SystemExit("!!! _gh WAS REACHED !!!")` as `_gh`'s first statement
and ran the harness:

```
::error::  FAIL  NO-GH     ... exit 1 (want 4)   !!! _gh WAS REACHED !!!
::error::  FAIL  GH-FAILS  ... exit 1 (want 4)   !!! _gh WAS REACHED !!!
14/16 fired ... rows=16 floor=16 fired=14/16 status=breach
```

Exactly two rows die and the other fourteen do not, which is the correct
result in both directions: the new rows reach the transport, the
fixture-fed ones still do not, by design. The mutation was proved landed
against `git diff --stat` before running and `RESTORED CLEAN` after.

**But two of three producers, not three.** `fd500c7`'s message names
three `UnmeasurableError` producers in `_gh` — no `gh` on `PATH` (`:88`),
non-zero exit (`:95-99`), unparseable JSON (`:100-105`) — and adds two
rows. I tripwired the third:

```
$ # raise SystemExit as the first statement of `except json.JSONDecodeError`
16/16 controls fired ... status=ok
$ grep -c "JSON BRANCH WAS REACHED"   ->  0
```

The harness is fully green with that branch amputated, so no row reaches
it. The commit message does not *claim* all three, so this is not a false
claim — it is a residual gap, and a third `transport` row closes it:
a stub `gh` that exits 0 printing `not json`, expecting exit 4 and
"unparseable", floor 16 → 17. I am recording it here rather than as a
separate finding because it is the same remedy as M2's family and you
may want them in one commit.

**R18-M1 — the ordering contradiction. CORRECT.** `per_page=10` → `100`,
and — this is the part that matters — the comment now **states the
residual** rather than implying it is gone: *"WIDENING REDUCES THE
EXPOSURE AND CANNOT REMOVE IT."* The two halves of the file now agree
about what they assume, which was R18's actual complaint. The commit is
also honest that R18 filed this as could-not-settle and that this is not
a fix for an observed failure.

**R18-M2 — the fork guard. CORRECT, and the reasoning is better than the
finding.** R18 suggested `if: github.repository == ...`; `46b09c4`
refused it and gave a reason that holds — an `if:` goes silently off on a
rename, which is the shape that hid 119 red mirror runs. Residue at N1.

**R18-M3 and R18-L2 — probe-131. CORRECT.** 12/12, floor 12, exit 0.
ARM 5 (`AMP-DIRTY`) is the amputation R18-M3 asked for and it is the
stronger of the two remedies R18 offered — it makes the dirty-tree branch
load-bearing rather than annotating that it is. ARMS 6-7 amputate the
library and take down ARM 1's and ARM 2's assertions respectively, so
L2's three amputations are present and each names which row it kills.

**R18-M4 — the missing controls. CORRECT as to existence** (C7-C9 exist
and run). The count is ungated: M2 above.

**R18-M5 / `1abb362` — the RECORD_PATHS ruling. I CHECKED YOUR CHECK AND
IT HOLDS.** Three things, each measured:

1. *Is the backlog genuinely a record?* Yes. Its content is derived from
   what the checker itself measures, and the four-commit self-reference
   loop `e6333ef → 39bfab8 → a36883f → e845839` is real and is quoted
   accurately in the reason string.
2. *Does `substantive` drop record paths so only an EMPTY remainder
   skips?* Yes — `check-review-coverage.py:502-503`,
   `substantive = [f for f in files if not is_record(f)]` then
   `if not substantive:`. A commit touching the backlog **and** a real
   file is still scored on the real file. Your check is correct.
3. *Can anything be smuggled past the gate beside a top-up?* **No, and I
   looked at the two ways it could be.** `is_record` matches
   `path == p or path.startswith(p.rstrip("/") + "/")`; for the
   file-shaped key that second form becomes
   `"docs/reviews/review-coverage-backlog.txt/"`, which no real path can
   match, so the key cannot widen into a directory. And the ledger cannot
   be silently trimmed: deleting an entry for a still-outstanding commit
   puts that sha in `measured` but not `recorded`, which is `entered`,
   which exits non-zero. I ran the case implicitly — the checker is
   currently red for exactly that reason on two *new* commits.

So the ruling is sound and the ratchet is not weaker than believed.

**R18-N1 — path normalisation. CORRECT, and fixed in BOTH places.**
`harness-state.sh:64` gets `repo="${repo%/}"` for any other caller, and
`restore-stranded-mutation.sh:83` gets
`REPO="$(cd "$2" && pwd || printf %s "${2%/}")"`, which is strictly
stronger than R18's suggestion because it also resolves symlinks and
`..`. R18 suggested one site; two were needed.

**`control-stranded-mutation.sh` A8/A9.** 32/32 passed, 0 failed, exit 0.
A2 is a real amputation that proves A1 can fail ("the amputated probe
blames the INNOCENT harness"), so the 32 is not a count of tautologies.

---

## 7. The floors, watched firing

§C3 says *watch each fire; do not read it.* All four, plus the two
PREAMBLE floors, derived from `ci.yml` rather than retyped:

| Floor | Green | Under mutation | Slack |
|---|---|---|---|
| `ROW_FLOOR=16` mirror controls | `rows=16 floor=16 fired=16/16 status=ok` | `fired=14/16 status=breach`, exit 1 | **0** |
| `ROW_FLOOR=12` probe-131 | `rows=12 floor=12 fired=12/12 status=ok` | — (not mutated; exactness unchecked, L1) | **0** |
| `arms=9` secrets controls | `arms=9 failed=0`, exit 0 | `arms=6 failed=0`, **exit 0** | **NO FLOOR** (M2) |
| `32` stranded-mutation | `32 passed, 0 failed`, exit 0 | A2 amputation kills A1 | **0** |
| suite floor `887` (from `ci.yml`) | `887 passed, 6 deselected in 56.28s`, 0 skipped | — | **0** |
| anchor floor `464` (from `ci.yml`) | `anchors resolved: 464`, exit 0 | — | **0** |

The middle row is the finding. Three of the four §C3 floors are exact
and one of them is not a floor at all.

`check-row-floor-exactness.py` exits 0: 25 harnesses checked, 8 carrying
both floors agree, 16 `--min-rows` compared to a live count, *"Every
floor equals its harness's live row count."*

---

## 8. The commit-message claims I checked

§C6 named eight numbers. **Seven HOLD; one is not a number I can call
wrong, and one number in §C3 is misdescribed** (see §9).

| Claim | Source | Measured here | Verdict |
|---|---|---|---|
| 887 tests, 0 skipped | several | `887 passed, 6 deselected in 56.28s` | **HOLDS** |
| 34 ADRs | `d29937f` | `ls docs/adr/0*.md \| wc -l` → 34 | **HOLDS** |
| 19 / 15 Type census | `d29937f` | 19 `Design change`, 15 `Deviation`, 0 `Both` | **HOLDS** |
| selector "selects exactly 15" | `d29937f` | 15 `Type: Deviation` | **HOLDS** |
| floor 16 | `fd500c7` | `rows=16 floor=16`, breaches at 14 | **HOLDS** |
| floor 12 | `9fbef31` | `rows=12 floor=12 fired=12/12` | **HOLDS** |
| arms 9 | `451faeb` | `arms=9 failed=0` | **HOLDS as a count** — but nothing gates it (M2) |
| arms 32 | — | `32 passed, 0 failed` | **HOLDS** |
| backlog 78 | brief §C6 | `Backlog recorded ...: 78`, and `probe-coverage-ratchet.py` prints `Backlog entries the arms were drawn from: 78` | **HOLDS**, by two instruments |

Three further claims from the same messages, checked:

- **`fd500c7`'s "the old ones still do not [reach the transport], by
  design" HOLDS** — my tripwire killed exactly 2 of 16.
- **`9fbef31`'s "L1 was FOUR silent returns not three" HOLDS.** Three are
  in `_warn_untracked` and the fourth is in `_untracked_paths`, added
  after R18 read the file. The in-function comment says "these three",
  which is correct *for that function*; the message says four, correct
  for the change. Not a contradiction.
- **`d29937f`'s "DESIGN.md IS UNTOUCHED AND NEEDS NO SECOND ADR" HOLDS.**
  `docs/DESIGN-FREEZE.txt` reads `e3b5c97`; `git log -1 --format=%H --
  docs/DESIGN.md` returns `e3b5c97267799...`. Derived, not retyped. The
  freeze is intact — which is precisely why L2 and M3 need an ADR rather
  than an edit.

---

## 9. Corrections to my brief

§A required these. Three:

1. **§B's population went stale while I worked.** It says 23 commits
   `e845839..origin/main`; `origin/main` is now `6e4fae3` and the range
   is 27. The brief was right when written. Flagging it because §E asks
   me to re-derive at the end, and the answer changed.

2. **§C3 calls "16, 12, 9 and 32" four floors. Two of them are not
   floors.** 16 (`check-mirror-liveness-controls.sh`) and 12
   (`probe-131-gate-state.sh`) are literal `ROW_FLOOR`s. **9** is an arm
   count with no floor of any kind — which is M2, and I would not have
   found it if the brief had not asked me to watch it fire. **32** is
   `control-stranded-mutation.sh`'s passed-count, gated by its own
   `failed` check rather than by a floor. Reading §C3 alone, one would
   think four floors guard these harnesses; two do.

3. **§C5 asks whether `Both` is "a problem I have left open or one I
   have created".** The dichotomy is not quite the shape of it. `Both`
   being unused is **pre-existing** and harmless. `Both` being
   *unmatchable by a selector in a frozen document* is **created**, by
   `e3b5c97`, and survived `d29937f`. Same value, two different facts,
   and only the second needs an ADR. M3.

---

## 10. The backlog, before and after

Pinned to `6f1d2ea` for the reading; re-derived against `origin/main`
(`6e4fae3`) at the end, as §E asks.

**Before**, with no R19 declaration present:

```
Backlog recorded in review-coverage-backlog.txt: 78
Backlog measured now: 80
ENTERED, unrecorded: 2
CLEARED, still recorded: 0
CHANGED KIND: 0
SUBJECT disagrees with the commit: 0
  2945f5e NONE BRIEF for R19, and #131 CLOSED by ruling on the half tha
  32aa9a8 NONE HANDOFF v6, and it is the first version whose predecesso
```

exit **1**. `probe-coverage-ratchet.py`: **10/10 arms, exit 0.**

**The two entrants are not mine and I am not clearing them.** They
landed after my pin; `2945f5e` is the brief for this very round and
`32aa9a8` is the handoff. They are the N+1 lag the checker's own
docstring describes, and they need the backlog top-up that whoever lands
this makes — not a declaration from me. **I have made no edit to
`review-coverage-backlog.txt`**, deliberately: the deletions my
declaration earns and the additions these two require belong in the same
commit as the merge, and R18's §9 correction #3 warns against following
the instruction literally when the tool says otherwise.

**After** this document's declaration is present, with the ledger
deliberately unedited:

```
Backlog recorded in review-coverage-backlog.txt: 78
Backlog measured now: 68
ENTERED, unrecorded: 2
CLEARED, still recorded: 12
CHANGED KIND: 2
SUBJECT disagrees with the commit: 0
```

exit **1**, and every one of those 14 lines is an instruction for the
landing commit, not a defect:

| Part | Lines | Detail |
|---|---|---|
| Deletions | 12 | the commits in `e845839..6f1d2ea` this round covers in full |
| KIND corrections | 2 | `4c29b98` and `6de1b4a`, `NONE` → `PARTIAL` |
| Additions | 2 | `2945f5e`, `32aa9a8` — after my pin, not mine to clear |

**The two KIND corrections are the declaration doing its job**, and they
are exactly the two I predicted in §11 before running it: `4c29b98`
touches `docs/briefs/HANDOFF-2026-09-01-orchestration.md` and `6de1b4a`
touches `docs/briefs/BRIEF-R18-tonights-gates.md`, neither of which I
read. The record now says PARTIAL rather than reading as a clean sweep.

I did **not** apply any of the three parts — see §11.

Refs: before and after, trunk `6e4fae3`, worktree pinned `6f1d2ea`, plus
one untracked file (`docs/reviews/REVIEW-R19.md`) committed on
`review/r19`. **Nothing pushed, nothing merged.**

---

## 11. What I could NOT settle

Kept separate from what I did not attempt.

1. **The backlog's post-EDIT state.** §10 reports the measured
   after-state with my declaration present and the ledger unedited, which
   is a real reading (68 measured against 78 recorded, 12/2/2). What I
   cannot report is the state after the three-part edit is applied,
   because I did not apply it: the deletions my round earns and the
   additions the two post-pin commits require belong in the landing
   commit, and applying half of it here would leave a ledger that
   disagrees with both states. Whoever lands this gets the settled
   number in one run. This is a deliberate hand-off, not a gap I failed
   to close.

2. **`actionlint`.** **NOT INSTALLED on this machine** — `command -v
   actionlint` returns nothing. CI runs it with
   `SHELLCHECK_OPTS=--severity=warning`. I did not run it and I am not
   claiming that gate. `46b09c4` says the same thing about itself, so
   `ci.yml` has now been changed twice by parties who could not lint it.

3. **Whether the mirror step behaves as designed on a real fork.** Same
   limit R18 recorded. I read the guard and traced both branches, and I
   did not fork the repository and push to it.

4. **Whether `Both` would actually be chosen by a future author.** M3 is
   a statement about what the frozen text permits, not a prediction. If
   you rule that `Both` is retired, the question dissolves rather than
   being answered.

**Not attempted, and deliberately:** `src/` and `tests/` — no commit in
my population touches either, which I verified with `--name-only` over
the whole range. `CONTRIBUTING.md`, `docs/OBLIGATIONS.md`,
`pyproject.toml` and the three `docs/briefs/` files ARE in my
population and I did not read them, so the commits touching them are
`PARTIAL` under my declaration and I am not claiming otherwise:
`30be0ce` and `d0bdf2a` (OBLIGATIONS, CONTRIBUTING), `f38f7c3`
(pyproject), `8986e64`, `1cddd76`, `6de1b4a` and `4c29b98` (briefs and
the handoff). The `#170` count fixes in those files are therefore
**unreviewed by me** — I read their commit messages and their `docs/`
halves only.

---

## 12. Declaration

I read in full, or drove by measured execution:

`scripts/check-secrets-baseline.py`,
`scripts/check-mirror-liveness.py`,
`scripts/check-mirror-liveness-controls.sh`,
`scripts/ci-harness-gate.sh` (the `#131` region),
`.github/workflows/ci.yml` (the mirror step and its guard, the secrets
step, the harness block, and both floor declarations),
`docs/reviews/probe-131-gate-state.sh`,
`docs/reviews/control-stranded-mutation.sh`,
`docs/reviews/restore-stranded-mutation.sh` (the `repo=` and `--repo`
regions),
`docs/reviews/lib/harness-state.sh`,
`docs/reviews/check-review-coverage.py`,
`docs/reviews/check-row-floor-exactness.py`,
`docs/reviews/check-row-floor-controls.sh`,
`docs/reviews/check-checkers-are-wired.py` (the diff),
`docs/reviews/measure-ci-step-durations.py` (the docstring and its
wiring exemption),
`docs/reviews/probe-coverage-ratchet.py` (by execution),
`docs/adr/` — the `**Type:**` line of all 34, `0034` in full, `0022`
and `0023`'s diffs,
`docs/adr/README.md`,
`docs/DESIGN.md` §13 and its header, **at the derived freeze SHA**,
`docs/DESIGN-FREEZE.txt`,
`docs/README.md` (the diff).

I did **not** read `CONTRIBUTING.md`, `docs/OBLIGATIONS.md`,
`pyproject.toml`, `docs/briefs/BRIEF-170-retyped-counts.md`,
`docs/briefs/BRIEF-R18-tonights-gates.md` or
`docs/briefs/HANDOFF-2026-09-01-orchestration.md`, all of which are in
my range. The commits touching them are PARTIAL under this declaration
and I am not claiming otherwise — a narrower true declaration beats a
wide false one.

The range ends at `6f1d2ea`. The four commits after it
(`2945f5e`, `d0f8d85`, `32aa9a8`, `6e4fae3`) are outside this round and
remain outstanding.

**Worktree `fmj-worktrees/r19` removed after this report was committed.**
