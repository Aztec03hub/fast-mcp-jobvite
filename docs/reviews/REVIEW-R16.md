# REVIEW-R16 — the trunk commits no round covers: 86, then 101

<!-- REVIEW-COVERS: 0b149b9..2d886a4 PATHS: docs/reviews scripts .github -->

Round R16, Tier-1, against the backlog `check-review-coverage.py`
records. Worktree `fmj-worktrees/r16`, branch `review/r16`, cut from
`origin/main` at **`ccbdaae`**. Zero Tier-2 workers.

**Verdict: 0 Critical, 1 High, 3 Medium, 5 Nits, and one finding of my
own WITHDRAWN by measurement before it left this document.**

**TWO REFS, AND EVERY NUMBER SAYS WHICH.** `origin/main` moved twice
under this round: `ccbdaae` at dispatch, `6e07131`, then `2d886a4`.
§1 to §8 were measured against **`ccbdaae`**, the trunk the brief
named. §9 is the **extension to `2d886a4`**, added after Tier 0 asked
me to re-derive, and the declaration at the top of this file is the
extended one.

**A ref moving FORWARD under a running agent is a real instrument
hazard and it bit me before I saw it.** Two of my own measurements
disagreed — 287 trunk commits / 60 merges, then 300 / 62 — from the
same command minutes apart. The checker's docstring warns that
`origin/main` can be STALE; this is the opposite shape and it is not
recorded anywhere. Reproduce anything in §1-§8 with `--ref ccbdaae`
and anything in §9 with `--ref 2d886a4`.

**Tier 0's own count and mine also disagreed, for the same reason:**
`ENTERED, unrecorded: 13` at `6e07131`, **15** at `2d886a4`.
`ccbdaae..6e07131` is 13 commits and `ccbdaae..2d886a4` is 15. Same
instrument, same backlog, different ref — the arithmetic was right on
both sides and only the population differed.

---

## 1. Corrections to my brief

### 1a. The backlog file records 63, not 86

§B says *"`docs/reviews/review-coverage-backlog.txt` records **86
commits**"*. It records **63** (24 `NONE` + 39 `PARTIAL`, measured by
`awk '!/^#/ && NF {print $2}' … | sort | uniq -c`). **86 is what the
checker MEASURES** (47 `NONE` + 39 `PARTIAL`), and the difference is
the checker's own headline:

    Backlog recorded in review-coverage-backlog.txt: 63
    Backlog measured now: 86
    ENTERED, unrecorded: 23

The split `47 NONE / 39 PARTIAL` in the brief is exactly right; only
its container is wrong. That matters because the brief then says the
file *"is your worklist"* — the file is 23 commits short of the
worklist, and re-deriving (which §B also instructs) is what surfaces
them.

### 1b. The 235-touch tally is exactly right

Re-derived over the 86 commits, every figure in §B reproduces to the
unit: 235 total touches, `docs/reviews` 55, `docs/briefs` 22,
`docs/worklogs` 14, `.github/workflows` 12, `src/fast_mcp_jobvite` 7,
`.secrets.baseline` 6. Recorded because a brief whose numbers hold is
worth saying so about.

### 1c. THE CORRECTION THAT MATTERS: these paths are already declared

§B steers this round at `docs/reviews` and `scripts` *"rather than
`src`"*, and §D's example declaration is
`PATHS: docs/reviews scripts .github docs/briefs`.

**`REVIEW-R15.md` already declares `8695101..0b149b9 PATHS:
docs/reviews scripts .github`.** So for the 39 `PARTIAL` commits — all
of which live inside R15's range — re-declaring those three paths
clears **nothing**, by construction: they are partial *because of* the
paths R15 did not claim. `REVIEW-R15.md` §1c already names the round
that closes them, and names it precisely:

> one complementary round over `docs/briefs docs/adr docs/research src
> tests` plus the five root config files takes PARTIAL 39 → 0.

Measured with my declaration in place (`--reviews` a copy, tree
untouched):

    COVERED BY NOTHING   47 -> 0
    PARTIALLY covered    39 -> 42
    Fully covered       201 -> 245
    Backlog measured     86 -> 42

So this round closes the `NONE` half and moves three commits
`NONE → PARTIAL`. **It cannot close the `PARTIAL` half and no
declaration I could honestly write would.** That is a job for the
round R15 specified, and my brief did not carry it forward.

I also measured what adding `docs/briefs` would buy — one further
commit, 42 → 41 — and I have **not** declared it, because I read only
`PREAMBLE.md` and `HANDOFF-2026-09-01-orchestration.md` of the nine
briefs the population touches. See §5.

### 1d. §E names one of the three backlog edits that are needed

§E says the run *"will list what your declaration does NOT cover as
`CLEARED, still recorded` — remove exactly those lines and no
others."* Removing exactly those leaves the gate **red**. The same run
also reports:

    ENTERED, unrecorded: 2      b567974, c6e3cda  (both PARTIAL)
    CLEARED, still recorded: 23
    CHANGED KIND: 1             cca19be  recorded NONE, measured PARTIAL

The ratchet compares **sets**, so recorded must equal measured: 23
deletions, 2 additions, 1 kind change. I have made all three (§4).
Doing only the deletions would leave the checker at exit 1 and invite
the next reader to conclude the ratchet is broken.

### 1e. `probe-coverage-ratchet.py`'s BASELINE arm: red at `ccbdaae`, green at `2d886a4`, and both readings are correct

At `ccbdaae`, with the backlog 23 short:

    FAIL  BASELINE the committed backlog agrees with the trunk: exit 1 (want 0)
    8/9 arms passed.                                          EXIT=1

At `2d886a4`, after §9:

    9/9 arms passed.
    Backlog entries the arms were drawn from: 49              EXIT=0

**The arm did not start working because I topped the backlog up.** It
was REWRITTEN at `3d7a82f` — one of the 15 commits in §9 — and that
commit's own title is the finding: *"R1-M6: the control's BASELINE arm
asserted the TRUNK was current, not that the instrument works."* The
old arm built its backlog from the committed file, so it went red after
every push; the new one derives a backlog from what the checker
measures right now and requires exit 0 against that. Its comment names
the class exactly: *"a control red by construction, which is the defect
#151 removes, relocated one artifact over."*

I read that diff for §9 and it is the right fix. Recorded because my
first pass had it as an open red I was about to hand back, and the
answer was already on the trunk one commit later — which is what a
moving ref does to a reviewer's snapshot.

---

## 2. Findings

### R16-H1 (High) — `check-harness-result.sh` cannot see a multi-line `EXIT` trap, so the canonical line can be disarmed at exit 0

`docs/reviews/check-harness-result.sh:99-105`

```bash
traps=$(grep -cE '^[[:space:]]*trap .*[[:space:]]EXIT$' "$f")
chained=$(grep -cE '^[[:space:]]*trap .*harness_result_emit.*[[:space:]]EXIT$' "$f")
if [ "$traps" -eq "$chained" ]; then
  armed=$((armed + 1))
```

Both counters are **anchored on `EXIT` at end of line**. A `trap` split
across a backslash continuation matches neither, so `traps` and
`chained` are both `0`, they are equal, and the file is counted
**armed**. The file's own comment three lines up states exactly what
that costs:

> bash has no trap stack: a later `trap … EXIT` REPLACES the one the
> shared file arms at source time, so a trap that does not chain
> `harness_result_emit` silently disarms the whole mechanism for that
> script - and disarmed looks exactly like passing.

**Two scripts in the tree carry such a trap today** — both of the U1
boot harnesses, whose restore paths are the longest in the family:

    scripts/check-u1-boot-amputation.sh:57
    scripts/check-u1-boot-controls.sh:51

**Measured, both arms, in a scratch clone of `ccbdaae` (nothing in the
review tree was touched):**

| arm | mutation | `every EXIT trap chains the emitter` | exit |
|---|---|---|---|
| baseline | none | 37 | 0 |
| **A** | drop `harness_result_emit;` from `check-u1-boot-amputation.sh`'s **multi-line** trap | **37** | **0** |
| B (positive control) | the same drop on `check-u5-jobs-controls.sh`'s **single-line** trap | 36 | 1 |

Arm A is the finding: a harness whose emitter is gone still reads
`EQUAL: all 37 scripts in the container emit the canonical line`. Arm B
is what makes A a defect rather than a claim — the identical edit one
file over is caught.

The replacement mechanism is not inferred; it was run:

    $ bash -c 'trap "echo ARMED" EXIT; trap "echo REPLACED" EXIT INT TERM; true'
    REPLACED

That second line is the **sibling blind spot**: `trap … EXIT INT TERM`
also fails `EXIT$`, and also replaces the armed trap. None exists in
the tree today (`grep -nE '^[[:space:]]*trap .*EXIT[[:space:]]+[A-Z]'`
over `scripts/*.sh` and `docs/reviews/*.sh` returns nothing), so that
half is latent; the multi-line half is live in two files.

**Why this is High and not Medium.** `check-harness-result.sh` is the
container gate whose whole claim is a **set equality** — *"{ scripts
that emit the line } == { scripts that exist }"* — and 2 of the 37
members are outside what either counter can see while being reported
inside the set. Everything downstream starts from the canonical line:
`ci-harness-gate.sh`'s three tally flags read it by `name=`, and a
harness that emits no line at all fails those flags with the *"printed
no HARNESS-RESULT line naming itself"* message — a red for a cause the
static gate has already certified as impossible.

**Suggested fix — join continuations, and stop requiring `EXIT` last.
Verified in the scratch clone, both directions:**

```bash
  joined=$(sed -e :a -e '/\\$/N; s/\\\n//; ta' "$f")
  traps=$(grep -cE '^[[:space:]]*trap .*[[:space:]]EXIT([[:space:]]|$)' <<< "$joined")
  chained=$(grep -cE '^[[:space:]]*trap .*harness_result_emit.*[[:space:]]EXIT([[:space:]]|$)' <<< "$joined")
```

With that change: clean tree → `37`, `EQUAL`, exit 0; arm A →
`36`, `check-u1-boot-amputation.sh (0 of 1 EXIT traps chain the
emitter)`, exit 1. It also closes the `EXIT INT TERM` half in the same
line. Add both shapes as rows to
`docs/reviews/check-harness-result-controls.sh`, which is the layer
that already runs artifacts and reads their real output.

### R16-M1 (Medium) — `scripts/check-timeout-literals.py` runs nowhere, and the wiring gate prints "Every checker is wired"

`scripts/check-timeout-literals.py` landed at `816007f` (in this
population) as a *"#116 container gate"*, green, with a three-arm
`--self-test`. It is invoked by **no workflow step**:

    $ grep -n 'check-timeout-literals' .github/workflows/*.yml
    (no output)

    $ uv run --frozen python scripts/check-timeout-literals.py
    scanned 38 scripts, 1017 echo lines
    0 retyped seconds figures. Every bound appears once. (#116)     EXIT=0

    $ uv run --frozen python scripts/check-timeout-literals.py --self-test
    3/3 arms                                                         EXIT=0

And the gate that exists to notice this cannot:

    $ uv run --frozen python docs/reviews/check-checkers-are-wired.py
    Run steps parsed from workflows/: 81
    WIRED: 24
    UNWIRED, with a stated reason: 4
    Every checker is wired, or unwired for a recorded reason.        EXIT=0

    $ … | grep -c 'timeout-literals'
    0

This is the **live instance** of rulings #153 (*"the wiring checker
selects BY PATH (docs/reviews only), so a checker under `scripts/` can
be unwired forever at exit 0"*) and #155. Both are recorded as pending;
what is new is that a checker has since landed in exactly that blind
spot and is sitting there green and unrun, while the wiring gate emits
its strongest sentence.

**Suggested fix**, and it is one commit, not two:

1. Wire it beside the other `python3 scripts/check-*.py` steps in
   `ci.yml`'s `test` job — it is green today, so this is the
   wire-it-the-day-it-goes-green rule, satisfied.
2. Land that step **with** #153's widening of
   `check-checkers-are-wired.py`'s container from `docs/reviews/` to
   `git ls-files 'docs/reviews/check-*.py' 'docs/reviews/check-*.sh'
   'scripts/check-*.py'`, plus a `--self-test` row asserting a
   `scripts/` checker absent from every workflow reads **UNWIRED**.
   Without that row the widening is a change nothing measures.

**A smaller, second-order note on the same file, offered rather than
filed:** `scan_text` skips any line without the literal `echo`, so a
bound retyped inside a `printf` is invisible. The docstring says
*"a shell `echo`"*, so the code keeps its stated scope; it is worth one
extra alternation (`(echo|printf)`) when someone is next in the file.

### R16-M2 (Medium) — `check-landing-published.py` enforces one half of the invariant it states

`docs/reviews/check-landing-published.py:138-139,185-189`

The docstring states the gated invariant as:

> A harness that diagnoses a per-row anchor-landing failure must not
> let that row continue silently. Either the branch is FATAL, or the
> harness publishes a named tally.

The code reports a finding **only when the window contains `return`**:

```python
        if any(FATAL.search(w) for w in window):
            continue
        if any(NONFATAL.search(w) for w in window):
            out.append((i + 1, line.strip()))
```

A branch that prints the diagnostic and then simply **falls through** —
no `exit`, no `return`, no tally — is neither fatal nor counted, and is
not reported. That is the *stronger* form of the same defect: the row
carries on inside the same function body rather than merely at the
caller.

**Measured, both arms, in the scratch clone.** One planted tracked
script under `scripts/`, one landing diagnostic, no tally:

| arm | branch disposition | findings | exit |
|---|---|---|---|
| 1 | falls through | **0** | **0** |
| 2 (positive control) | `return 1` added, nothing else changed | 1, named at `:5` | 1 |

*(My first attempt at arm 1 was itself vacuous: `container()` reads
`git ls-files`, so the untracked plant was invisible and the run
reported `37 scripts scanned` — the count that told me. `git add` first;
the arm then reads `38 scripts scanned`.)*

**Latent, not live.** Re-deriving over the container: 37 scripts, 7
publish no tally, and among those 5 landing branches are fatal, 0
`return`, 4 "neither" — and all 4 are the vocabulary array in
`scripts/ci-harness-gate.sh:74-77`, which is a definition and not a
branch. So the gate's `0 finding(s)` is a true zero today. It is one
refactor from being a silent one.

**Suggested fix:** invert the test — report unless the branch is
*positively* disposed of.

```python
        if any(FATAL.search(w) for w in window):
            continue
        out.append((i + 1, line.strip()))
```

and change the printed remedy line from *"The branch `return`s"* to
*"The branch neither exits nor is counted"*. That admits the four
`ci-harness-gate.sh` vocabulary lines as findings, so exempt that file
by name **with its reason** — it defines the vocabulary and emits none
of it, which is the same distinction `check-harness-result.sh:154-167`
already draws for the identical file. Add both shapes (fall-through,
and the vocabulary definition) as arms so neither direction is a claim.

### R16-M3 (Medium) — `CONTRIBUTING.md` says "thirteen harnesses"; the command beside it returns 32

`CONTRIBUTING.md`, "The gates, and how to run them before you push":

> THE HARNESSES. This used to be a hand-typed list of the same
> **thirteen** scripts CI runs, which is the two-lists defect in its
> plainest form … It is now DERIVED from `ci.yml`, so it cannot
> disagree with what CI actually runs.
>
> Read it before you run it - it is **thirteen** harnesses and takes a
> while.

The paragraph is right about the mechanism and its own count went
stale anyway. Running the command it prescribes, at `ccbdaae`:

    $ grep -hoE "scripts/ci-harness-gate\.sh [^\"]*" .github/workflows/ci.yml | wc -l
    32

32 invocations, 32 distinct harnesses, no duplicates. The "thirteen"
dates from `3def07e` (*"One shared harness gate, called by all 13
steps"*) and has drifted by 19.

**This is a costing, not a nit.** The block's instruction is *"run
them, one at a time, stopping to read anything that fails"*, and the
reader budgets from the number in the sentence. The slowest single
member measured on this project is `check-u9-http-amputation.sh` at
1040s (`probe-harness-exit-codes.sh`'s usage text), and `u0` alone is
711s (#108). A reader planning for thirteen is planning for well under
half the run.

**Suggested fix — delete the number, exactly as `PREAMBLE.md` does for
the two floors** (*"NEITHER FLOOR IS WRITTEN HERE, on purpose"*):

```
# Read it before you run it - the command above says how many there
# are (`| wc -l`), and they take a while: the slowest single member
# measured is ~1040s.
```

The same stale 13 appears once more, in
`docs/reviews/REPORT-147-ci-step-selection-bias.md` §6 (*"the thirteen
`ci-harness-gate.sh` harnesses"*). That one is a dated record of what
one agent did not run, so it is correct as written and should be left
alone — recorded here only so the sweep is not repeated.

### R16-N1 (Nit) — the W505 reflow at `5028cae` put `#` inside a docstring and orphaned twenty words

`docs/reviews/check-landing-published.py:6-13,19-20,87-104`

`5028cae` ("#152: reflow the checker to the W505 72-column limit")
rewrapped the new gate's docstring mechanically. `ruff check` passes —
W505 measures width and nothing else — and the prose is damaged:

    :19  # 152 proposed deriving the EXPECTED publishers from each harness's
    :20  # SHAPE and
    :21  asserting set equality against the observed ones - `check-*-controls.sh`

Two lines **inside a `"""` docstring** now start with `# `, which is
not a comment there but literal text, and the sentence is broken across
them. Separately, the reflow left ~20 single-word lines (`canonical`,
`ACTUALLY`, `flag`, `by`, `FIELD.`, `incremented`, `sweep,` …) in the
first 80 lines. The pre-reflow text at `2b245d3` reads cleanly; the
gate that forced the change is satisfied by both.

**Suggested fix:** re-wrap that docstring by hand at phrase boundaries
and restore `#152` (no space, no `# ` prefix) at `:19`. `ruff check`
stays green either way, so the check on the fix is reading it.

### R16-N2 (Nit) — "Three names because the arms are three separate decisions" sits in 32 files; 10 declare three

`scripts/one-shot/apply-116-timeout-names.py:2694-2698` emits this
block into every harness it rewrites:

```
# Timeout bounds - each declared ONCE and interpolated into the abort
# message that explains it, so a changed bound cannot leave prose behind
# still quoting the old one. Three names because the arms are three
# separate decisions, even where two of them share a value today.
```

but then emits **only the names that file actually uses**. Measured
over the 32 files carrying the sentence:

| names declared | files |
|---:|---:|
| 3 | 10 |
| 2 | 19 |
| 1 | 2 |
| 0 | 1 (the applier itself) |

So 21 of the 31 harnesses carry a sentence that misdescribes them, in
the sweep whose stated purpose is that *"a changed bound cannot leave
prose behind still quoting the old one"*.

**Suggested fix:** make the template count-free, and fix it at the
applier so it cannot be re-emitted —
*"One name per arm (baseline / row / selector); arms that share a value
today are still separate decisions, so they keep separate names."*

### R16-N3 (Nit) — `ci.yml`'s no-errexit comment says 43 tracked `.sh`; the checker counts 54

`.github/workflows/ci.yml:250` (landed at `328ffec`, in this
population):

```
      # WIRED THE DAY IT WENT GREEN. 43 tracked .sh, none enabling errexit;
```

    $ uv run --frozen python docs/reviews/check-no-errexit.py
    Tracked shell scripts checked: 54
    EXEMPT   scripts/check-pytest-bounded.sh: a CHECKER, not a harness …
    None enables errexit.                                            EXIT=0

The **checker** derives its container from `git ls-files '*.sh'` and is
correct; only the comment beside it carries a frozen number. Harmless
today and it is the shape §C.5 names.

**Suggested fix:** `# WIRED THE DAY IT WENT GREEN, on a container this
checker derives from `git ls-files '*.sh'` and prints on every run;
none enabled errexit then and the run says so now.` — i.e. delete the
figure rather than refresh it.

### R16-N4 (Nit) — the lychee block's "27 relative markdown links across 63 files" is now 54 across 7

`.github/workflows/ci.yml`, the `Relative links resolve` header
(carried into `static-gates` by `8be39b4`, in this population):

> The PROPERTY it asserts was verified locally against the current tree
> with an equivalent offline walk: 27 relative markdown links across 63
> files, 0 dangling … Only 27 links in the whole tree are even in scope.

Re-measured at `ccbdaae` with an equivalent walk (inline `[x](y)`,
excluding `http(s)`, `mailto:` and bare `#`):

    relative markdown links: 54 across 7 files (of 231 tracked .md)
    dangling: 0

**The property still holds — the zero is real.** What has drifted is
the scale (27 → 54) and the phrasing: "across 63 files" reads as
*link-bearing* files and was in fact the whole `.md` population at the
time, which is now 231. The step has still never executed.

**Suggested fix:** state the property and drop the frozen pair —
*"verified locally with an equivalent offline walk: every relative
markdown link resolves on disk, 0 dangling; the walk was
positive-controlled against a deliberately broken link before its zero
was believed. Re-run the walk rather than trusting this sentence."*

### R16-N5 (Nit) — one reason is given for a warn-not-fail choice that covers two branches, and only one of them is transient

`.github/workflows/mirror.yml`, the `Report whether the mirror is
configured, and whether it is current` step (added at `4aca097`, in the
§9 extension). `docs/reviews/REPORT-157-mirror-minutes.md` §4 states the
choice and its reason:

> **It warns, it does not fail.** A step whose whole purpose is
> legibility must not go red on a transient network read, because that
> trains its reader to ignore it — the habit that let 119 failures go
> unread.

The reason names ONE branch — the `git ls-remote` read failing — and
the code applies the choice to TWO. A mirror that is genuinely **STALE
or DIVERGED** is also a `::warning::` on a green run, and divergence is
not transient: it is the exact state the check was added to detect,
now reported at exit 0 inside a daily cron that the same document says
"nobody looks at ... the way they look at a red tick beside their own
commit."

**I am NOT claiming the behaviour is wrong, and this is the reason the
finding is a nit rather than a Medium.** There is a strong unstated
counter-argument on the other side: with `MIRROR_TOKEN` absent, nothing
in CI can *clear* a divergence, and a red nobody can act on is the same
habit-forming failure the quoted sentence is about. That argument
happens to be the stronger one, and it appears nowhere.

**Suggested fix — a sentence, not a behaviour change.** In
`mirror.yml`'s header and in `REPORT-157` §4, split the reason:

    UNKNOWN warns because a remote read is transient. DIVERGED also
    warns, for a different reason: with no MIRROR_TOKEN nothing in CI
    can clear a divergence, so a red here would be a red nobody can
    act on. If the token ever exists, revisit THIS branch - divergence
    then becomes actionable and a warning becomes the weaker signal.

The last clause is the part worth writing down: the correct disposition
of that branch **changes** when the token lands, and nothing currently
records that it should be re-read then.

---

## 3. The finding I WITHDREW, and why it is in this document anyway

**I nearly filed a High that says a merge commit is scored fully
covered without any of its files being checked.** It reproduces, and it
is not a defect. It is here because the reproduction is cheap and the
next reviewer will find it too — `REVIEW-151-R1.md` §"My own mistakes"
records the same withdrawal, so this is the second reviewer to walk
into it.

**What I measured first.** `check-review-coverage.py:432` reads a
commit's files with `git show --name-only --pretty=format: <sha>`,
which on a merge defaults to `--cc` and prints nothing for a clean
merge:

    $ git show --name-only --pretty=format: fc6c508
    (empty)
    $ git diff --name-only fc6c508^1 fc6c508 | wc -l
    4

At `ccbdaae`, **51 of the 60 trunk merges** have an empty `--name-only`
and a non-empty first-parent diff. Swapping in
`git show --first-parent --name-only …` moves **7 commits, all
merges**, from `Fully covered` to `PARTIAL` (like-for-like in one
scratch clone: 201/39 → 194/46, `COVERED BY NOTHING` unchanged at 52).
`3914dca` is the sharpest: claimed only by `REVIEW-R15.md`
(`docs/reviews scripts .github`), first-parent diff touching three
`docs/adr/` files, two `docs/research/` files and `scratch139/`.

**Why it is not a defect.** `rev-list` enumerates the branch commits
individually, and they are scored individually. For `3914dca`, all five
branch commits are in the trunk rev-list, and `89aceee` and `d3fbe22`
carry exactly the `docs/adr`, `docs/research` and `scratch139` files —
both already recorded `PARTIAL` in the backlog. The gap is *already
visible*, against the commit that introduced it. And the one thing a
merge holds that no branch commit does — a conflict resolution — is
precisely what `--cc` prints: `92cb89b` (an evil merge) reports 4 files
where `203e5af` (a clean one) reports 0.

**Settled over the container, not a sample:** for all **60** merges in
`8695101..ccbdaae`, every file in the first-parent diff is either
merge-unique (printed by `--cc`) or carried by a branch commit that is
itself in the trunk rev-list. **Unaccounted files: 0.**

So the `--first-parent` "fix" would have added 7 redundant `PARTIAL`
rows for gaps already recorded elsewhere, and grown the backlog to
record the same fact twice. `--cc` is the right default and the
docstring's *"every file it touches"* is true in the sense that
matters.

---

## 4. Verification, before and after, each with its ref and sha

**Before**, on the untouched tree:

    $ uv run --frozen python docs/reviews/check-review-coverage.py --ref ccbdaae
    Trunk ref: ccbdaae = ccbdaae
    Trunk commits on ccbdaae since 8695101: 287
    Fully covered - range AND every path: 201
    PARTIALLY covered: 39
    COVERED BY NOTHING: 47
    Backlog recorded in review-coverage-backlog.txt: 63
    Backlog measured now: 86
    ENTERED, unrecorded: 23
    CLEARED, still recorded: 0
    CHANGED KIND: 0
    SUBJECT disagrees with the commit: 0                             EXIT=1

**After** this document's declaration and the backlog edit:

    $ uv run --frozen python docs/reviews/check-review-coverage.py --ref ccbdaae
    Trunk ref: ccbdaae = ccbdaae
      DECLARED  REVIEW-R16.md: 0b149b9..ccbdaae
                48 commits, paths: docs/reviews scripts .github
    Trunk commits on ccbdaae since 8695101: 287
    Fully covered - range AND every path: 245
    PARTIALLY covered: 42
    COVERED BY NOTHING: 0
    Backlog recorded in review-coverage-backlog.txt: 42
    Backlog measured now: 42
    ENTERED, unrecorded: 0
    CLEARED, still recorded: 0
    CHANGED KIND: 0
    SUBJECT disagrees with the commit: 0
    The backlog holds at 42, every commit recorded.
    A HOLDING RATCHET IS NOT FULL COVERAGE.                          EXIT=0

**Backlog 63 → 42. `COVERED BY NOTHING` 47 → 0. `PARTIAL` 39 → 42.**

**That was the state at the end of the first pass, and it is not where
this round stops.** §9 extends the declaration to `2d886a4` and tops the
backlog up to **49**; the run against the live default ref is in §9 and
exits 0. Both readings are kept because §E asks for a before and an
after with their refs, and "before" has two legitimate ones.

**`probe-coverage-ratchet.py`, §E's second command, at `2d886a4`:**

    9/9 arms passed.
    Backlog entries the arms were drawn from: 49              EXIT=0

At `ccbdaae` it was 8/9 with `BASELINE` red — see §1e, where the reason
turns out to be a fix that landed on the trunk while I was reading.

**The backlog edit, all three parts** (§1d):

- **23 lines deleted**, exactly those the run named `CLEARED`:
  `00a4264 10ac6cf 13a4a65 203e5af 273d5d0 39af3ce 3d9445c 52023ff
  6fe2d73 8132017 816007f 8bc6391 9e04411 a0cd343 aa893a2 ae924ca
  b27a01e cd567e9 d15e218 dbad618 eef2b4e f5247a1 f6951be`
- **2 lines added**, both `PARTIAL`: `b567974`, `c6e3cda`
- **1 kind changed**: `cca19be` `NONE` → `PARTIAL`

Recorded 63 → **42**, which equals the measured set.

---

## 5. The declaration, and exactly what is behind it

    <!-- REVIEW-COVERS: 0b149b9..2d886a4 PATHS: docs/reviews scripts .github -->

**The range is narrow at the base and honest at the head.**
`8695101..0b149b9` is already `REVIEW-R15.md`'s for these same three
paths; re-declaring it would claim work I did not redo. So the base is
`0b149b9`.

`0b149b9..ccbdaae` is 48 commits, 47 of them my original population
(the 48th, `e9702ff`, is `REVIEW-151-R1.md`'s). The head then moved to
`2d886a4`, adding 15 more; I read those over these same three paths and
extended rather than leaving them, which §9 sets out in full. Total
declared: **63 commits**.

**The paths are three, not four.** `docs/briefs` is deliberately
absent — see below.

**READ IN FULL, every one:**

- **`.github`** — the complete diff of all 8 non-merge population
  commits touching it (`105a979 328ffec 306dfe7 dbad618 f6951be
  8be39b4 9422844 ccbdaae`), plus the current text of every step those
  diffs land in.
- **`scripts`** — the complete population diff, 3968 lines across 12
  commits. Read closely: `ci-harness-gate.sh`'s `read_tally` rewrite,
  `ci-harness-gate-controls.sh`'s new arms, `lib/harness-result.sh`,
  the eleven widened pre-flight guards. Read as the repeated mechanical
  substitution it is: the `#116` `BASELINE_TIMEOUT`/`ROW_TIMEOUT`
  rename across 30 files. Read whole from the tree, not only as a
  diff: `check-timeout-literals.py`, `check-harness-result.sh`.
- **`docs/reviews`** — the complete population diff of every non-`.md`
  file, 4672 lines. Read whole from the tree:
  `check-review-coverage.py`, `check-landing-published.py`,
  `check-harness-result.sh`. Read in full as documents:
  `REVIEW-R15.md` (428), `REVIEW-151-R1.md` (351),
  `REPORT-147-ci-step-selection-bias.md` (267), both `ledgers/*.txt`,
  `review-coverage-backlog.txt`.

**SKIMMED rather than read** — stated because §D asks: the `#116`
timeout-rename hunks after the first three files, which are
byte-identical substitutions I verified by pattern rather than by
reading each of the 30; and `probe-audit-shape-container.py`'s
formatting-only hunks at `41150a1`.

**NOT READ, and therefore NOT DECLARED:**

- **`docs/briefs`** (22 touches, 9 files). I read `PREAMBLE.md` and
  `HANDOFF-2026-09-01-orchestration.md` in full and opened neither
  `PROTOCOL-sub-orchestrators.md` (7 touches, 297 lines) nor the seven
  others. Declaring the path would claim all nine. It is worth exactly
  one commit (§1c) and it is not worth a false claim.
- **`src`, `tests`, `docs/adr`, `docs/research`, `.secrets.baseline`,
  `pyproject.toml`, `README.md`, `CONTRIBUTING.md`, `.env.example`,
  `.pre-commit-config.yaml`, `scratch139/`, `sweep.log`.** I read
  `CONTRIBUTING.md` as canon and filed M3 against it, but reading one
  file is not reviewing a path across 48 commits, so it is not
  declared. These are the complementary round's, per `REVIEW-R15.md`
  §1c.

---

## 6. What I verified as CORRECT

- **`ci-harness-gate.sh`'s three tally names really are kept apart.**
  Amputated both `read_tally` field readers to `^[a-z]*=` — the
  collapse the design refuses — and re-ran the controls:
  `C28 a tally of the WRONG kind does not satisfy the flag` **SURVIVED**
  (27/28), and only C28. The first version of my amputation changed one
  of the two readers and all 28 still fired; the control is not
  vacuous, my first arm was.
- **`check-landing-published.py`'s five line-numbered citations all
  resolve and carry their subject** — `harness-result.sh:163` (the one
  `printf`), `:157-162`, `:24-44`, `:113-126`, and
  `check-u4-client-amputation.sh:21`. Checked because this repo has
  found nine wrong-subject citations, four inside the ADR about them.
- **`PREAMBLE.md`'s two derive commands still match.**
  `check-suite-floor.sh 887` and
  `check-harness-anchors.py --self-check --floor 458` both return a
  value; neither is the clean-empty a moved anchor would give.
- **`ADR-0023`'s scope is by PURPOSE, and the tree obeys it.**
  `scripts/check-pytest-bounded.sh:30` runs `set -euo pipefail`, which
  looks like a violation of a path-scoped reading and is correct under
  the ADR's own scope (`:137`, *"Everything else in this repository
  gets `set -euo pipefail`"*). `check-no-errexit.py` records the
  exemption with a reason.
- **`.venv` markdown is not a lychee hazard.** The merged `static-gates`
  job populates `.venv` (22 `.md` files) before the link step, but
  lychee honours `.gitignore` by default and `.venv/` is ignored. I
  went looking for this as a consequence of `#143` and it is not one.
- **`R15-H2`'s fix landed, and its *suggested* fix was overruled by
  measurement.** R15 proposed `git diff HEAD` and `git checkout HEAD
  --` at all five sites. The tree instead moved only the pre-flight to
  `git status --porcelain` and left the landing/restore checks
  index-relative, with the reason recorded in place
  (`check-u3-audit-controls.sh`): `git checkout HEAD --` rewrites the
  index and silently destroys staged work. The implementers were right
  and said why.

---

## 7. What I could NOT settle, and what I did not attempt

**Could not settle:**

- **Whether the numbers hold on a trunk that is still moving.** They
  held at `2d886a4`: §9's run against the live default ref exits 0 with
  all four difference counts at zero. That is a claim about a MOMENT,
  not a property. `origin/main` moved twice under this round already —
  `ccbdaae`, `6e07131`, `2d886a4` — and the next push makes the ratchet
  red again by construction, at N+1 for a merge of N. **That is the
  gate working, and the lines belong to whoever pushes them.** What I
  cannot settle is whether it is still 0 by the time anyone reads this.
- **Whether R16-H1 has ever fired.** The two multi-line traps in the
  tree today both *do* chain the emitter, so the blind spot is real and
  currently unexercised. I did not check every historical revision of
  those two files, so I cannot say a disarmed emitter never went
  unreported in the past.
- **Whether the 39 `PARTIAL` commits contain anything.** I read none of
  the files holding them back, for the reason in §1c and §5. That is
  the complementary round's job and I am not claiming it.

**Not gated but worth Tier 0's eye — OUT OF MY DECLARED RANGE.**
`docs/OBLIGATIONS.md` is canon I was told to read and no commit in my
population touches it, so this is reported, not declared, and not
covered by anything above. Its `BASH-1` row says *"all **20**
`scripts/*.sh` run `set -uo pipefail`"* and *"the shebang half … is met
by **20/20**"*, having itself recorded that the count *"was 15 and went
stale"* and that *"it is a POPULATION, so COUNT … rather than carrying
the number forward"*. Measured at `ccbdaae`: **37** files, **36**
carrying the line (the 37th is `check-pytest-bounded.sh`, correct under
ADR-0023's purpose scope), **37/37** shebangs. The guidance block below
it says *"13 of the 15 `scripts/*.sh` exceed 100 lines; the largest is
469"*; measured, **36 of 37**, largest **579**. `check-obligations.py`
anchors on subjects and cannot see any of this. Suggested fix: replace
each figure with the command that produces it, exactly as the row's own
sentence instructs.

**Did not attempt:**

- The suite, the floors, or any of the 32 harnesses. My paths are the
  checkers; no floor moves from a review document, and three agents are
  live in this repo. Tier 0 runs the full gate before folding.
- Any fix. Every finding above is a task, not a commit — R16-H1 and
  R16-M1 in particular are one-line changes I deliberately did not make.
- Any edit outside `docs/reviews/REVIEW-R16.md` and
  `docs/reviews/review-coverage-backlog.txt`. `ci.yml`,
  `scripts/check-u1-boot-amputation.sh` and the mirror workflow belong
  to `suborch-161`, `suborch-156` and `suborch-157`; every amputation
  in this document ran in `/tmp/r16-scratch`, a `git archive` of
  `ccbdaae` into a fresh repo, and `git status --porcelain` in the
  review worktree names only the two files above.
- Any push, any merge, any ref outside `review/r16`.

---

## 9. THE EXTENSION TO `2d886a4`, added after the trunk moved

Tier 0 re-derived while §1-§8 were being written and asked whether I
would claim the new commits. **`ccbdaae..2d886a4` is 15 commits**, and
14 of the 15 touch at least one of my three declared paths. I read
them, so the declaration head moves from `ccbdaae` to `2d886a4`.

**READ IN FULL, from `git show`, in a scratch `git archive` of
`2d886a4` — the review worktree was not used as a subject:**

- `scripts/check-secrets-baseline.py` (333 lines, cumulative over its
  three commits)
- `docs/reviews/probe-secrets-baseline.py` (233 lines)
- `docs/reviews/FINDINGS-161-secret-scan-baseline.md` (302)
- `docs/reviews/REPORT-157-mirror-minutes.md` (431)
- `docs/reviews/probe-coverage-ratchet.py` and
  `docs/reviews/review-coverage-backlog.txt`, the `3d7a82f` diffs
- `.github/workflows/ci.yml`, the `c276a45` diff and the whole
  `Secret scan hook runs clean` step
- `.github/workflows/mirror.yml`, the cumulative `ccbdaae..2d886a4`
  diff (three commits)

**NOT read and NOT declared:** the five `docs/briefs/` files,
`CONTRIBUTING.md`'s and `.pre-commit-config.yaml`'s diffs, and
`docs/worklogs/` (an exempt record path). Those are what hold the seven
residual commits at `PARTIAL`.

**Verified by running, not by reading:**

    python3 scripts/check-secrets-baseline.py --controls
      C1..C6 all PASS, arms=6 failed=0                             EXIT=0
    uv run --no-project --with detect-secrets==1.5.0 python \
        docs/reviews/probe-secrets-baseline.py
      A0..A4 all PASS, arms=5 failed=0                             EXIT=0

**A4 is the arm worth naming.** It amputates the digest out of the
comparison key in a COPY of the checker and requires the planted secret
to then PASS — so `A2`'s red is evidence about the comparison rather
than about a checker that fails on anything. It asserts its anchor is
unique first and refuses rather than no-opping. That is the shape §C.1
asks for, built without being asked.

**And I checked the two blind spots #161 declared, rather than taking
them.** `check-checkers-are-wired.py` at `2d886a4` prints *"Every
checker is wired, or unwired for a recorded reason"* and names neither
`scripts/check-secrets-baseline.py` (0 matches) nor
`docs/reviews/probe-secrets-baseline.py`. **Neither is a live gap**:
`--controls` is invoked by name at `ci.yml:1546`, and the bare gate
runs through `pre-commit run --all-files` in the same step, so CI asks
BOTH questions — the pattern `REPORT-147` §5 calls the correct one.
This does not weaken **R16-M1**: `check-timeout-literals.py` is in the
same blind spot and is invoked by nothing at all.

**The effect on the backlog, measured:**

    --ref 2d886a4, declaration 0b149b9..2d886a4
    Trunk commits since 8695101: 302
    Fully covered  245 -> 253      (8 of the 15 fully covered)
    PARTIALLY       42 ->  49      (7 of the 15)
    COVERED BY NOTHING: 15 -> 0
    Backlog recorded 42 -> 49, measured 49
    ENTERED 0   CLEARED 0   CHANGED KIND 0   SUBJECT 0        EXIT=0

The seven added rows carry a dated `#` note in the backlog naming why
it grew and which paths hold them, as the file's own header requires.

**WHAT THIS DOES NOT CLAIM.** The 15 are read over three paths, not
reviewed whole. `docs/briefs/PROTOCOL-sub-orchestrators.md`,
`BRIEF-R16-review-round.md` (my own brief, edited at `ffd36c7`) and
three handoff rewrites are unread by me and unread by anyone. They are
in the backlog, which is where an unread commit belongs.

---

## 8. Worktree

`fmj-worktrees/r16`, branch `review/r16`, detached from `origin/main`
at `ccbdaae`. It holds this document and the backlog edit and nothing
else. Remove it after the merge.
