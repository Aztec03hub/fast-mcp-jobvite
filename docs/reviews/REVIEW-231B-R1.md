# REVIEW-231B-R1 - the ruling's conclusion survives; its stated GROUND does not, and its own prescribed command cannot return the zero it promises

<!-- REVIEW-COVERS: 7e8adfa..830d299 -->

Reviewer: `review-231b`, task #231 (Part B). Fresh - I did not write the subject.
Worktree `/tmp/review-231b`, branch `review/231b`, cut from `main` at `830d299`.
Subject: commit `830d299` - `docs/reviews/RULING-231B-merge-coverage.md` (new) and an
in-place correction inside `docs/reviews/REVIEW-R21.md`.

Verdict: **2 High, 4 Medium, 1 Low, 1 Nit.** All six of the brief's checkable claims
were re-derived; five hold exactly, one (claim 6) is wrong. The ruling's three
DECISIONS all survive - decision 2 survives on a different argument than the one
written, and decision 3 survives with a measurement that weakens the reason given.

---

## §1 The six claims, re-derived

Every command below was run in `/tmp/review-231b` at `830d299`. Exit codes on their own line.

| # | Claim | Verdict |
|---|---|---|
| 1 | `git show --cc 73dd717 \| wc -c` -> 11376; third version of `BRIEF-199-ratchet-defects.md` in neither parent | **CONFIRMED** |
| 2 | `invented=0` for `b9b59dd` AND `cd8c938` | **CONFIRMED** |
| 3 | `REVIEW-R21.md:3` declares a bare range, and that declaration is what clears `73dd717` | **CONFIRMED, causally** |
| 4 | `REVIEW-R22.md:3` declares range PLUS `PATHS:` | **CONFIRMED** |
| 5 | 21 merges / 53 invented lines over `c749334..HEAD` | **CONFIRMED** (but see M2 - wrong container) |
| 6 | R21's own §2 named `73dd717` as needing separate treatment, above the universal | **WRONG** - see M4 |

**Claim 1.**

    $ git show --cc 73dd717 | wc -c
    11376
    $ git show --cc 73dd717 | grep -n '^diff --'
    73:diff --cc docs/briefs/BRIEF-199-ratchet-defects.md
    125:diff --cc docs/briefs/PREAMBLE.md
    151:diff --cc docs/reviews/check-brief-report-references.py

The `BRIEF-199` hunk carries `++` lines (in neither parent), beginning
`**AND THIS SENTENCE MADE THE GATE RED, TWICE, INDEPENDENTLY.**`. Read, not inferred.

**Claim 2.**

    $ uv run --frozen python docs/reviews/check-merge-invented.py b9b59dd cd8c938 73dd717
    b9b59dd  parents=3975d53,1237de0  cc=0B     paths_scanned=11  invented=0
    cd8c938  parents=fa94f77,9b3e85f  cc=0B     paths_scanned=15  invented=0
    73dd717  parents=4be5356,6f921f8  cc=7226B  paths_scanned=15  invented=53
    TOTAL merges=3 invented_lines=53
    rc=0

The two CLEAN verdicts are independently correct and were rightly kept.

**Claim 3 - the CAUSAL half, which the brief asked me not to take on syntax.**
`check-review-coverage.py` has a `--reviews` flag that reads the review documents from a
directory that is NOT the tree (added for exactly this kind of control, per its own
comment at :445-452). Two arms, neither of which touched the working tree
(`git status --porcelain` empty, verified):

    ARM 1 (as committed):
      Fully covered 375 | PARTIAL 23 | NONE 97
      73dd717 appears in NEITHER the NONE nor the PARTIAL list.

    ARM 2 (copy of docs/reviews with ONLY line 3 of REVIEW-R21.md deleted):
      Fully covered 353 | PARTIAL 23 | NONE 119
      73dd717 NONE Merge #199/#200/N3, resolve a conflict we both created,

**Removing that one line moves `73dd717` from covered to `COVERED BY NOTHING`, and moves
22 commits in total.** The mechanism was asserted correctly and it is now run, not reasoned.

Two riders worth recording, both checked:
- The correction block at `REVIEW-R21.md:563` restates `REVIEW-COVERS: c749334..80463a5`
  inside a blockquote. It does NOT create a second declaration: the parser is
  `^<!--\s*REVIEW-COVERS:` (`check-review-coverage.py:196`) and :563 begins `  > \``. So the
  correction does not trip the "carries N REVIEW-COVERS lines" refusal at :392.
- `RULING-231B-merge-coverage.md` is NOT in the coverage population - `IS_REVIEW` is
  `REVIEW.*-R\d+` (:192) and the name does not match. It lands in "Excluded, with a
  reason", 63 -> 64. **The subject introduces no new gate red**: the checker exits 1 at
  `830d299` AND at its parent `7e8adfa` (`--reviews` from `git archive 7e8adfa`), so
  rc=1 is pre-existing, from the backlog ratchet and an UNDECLARED `REVIEW-218-R1.md`.

**Claim 4.** `REVIEW-R22.md:3` is a range plus a 16-path `PATHS:` list, and `REVIEW-R22.md:476`
opens `## What I did NOT verify`, whose :485 reads *"**Merge-INVENTED content.** #222 owns
it and I deliberately did not"*. The ruling's characterisation of R22 is accurate.

**Claim 5.** `--range c749334..HEAD` -> `TOTAL merges=21 invented_lines=53`, and filtering
the per-merge rows for non-zero returns exactly one: `73dd717`. So over that range, 53 of
53 invented lines sit in one merge. Correct as stated. See **M2** for why that range is
not the gate's container.

---

## §2 Findings

### H1 - Decision 2's "a fact, not a policy preference" framing is REFUTED by measurement. The conclusion survives; the ground written under it does not.

`RULING-231B-merge-coverage.md` decision 2 says a merge's third version *"appears in no
branch diff, in no `git log -p`, and in no per-commit review - it is visible only to
`--cc`."* The brief asked whether any ordinary reviewing practice would surface it without
`--cc`. **Three do.** Each arm greps for one invented line
(`Work you find outside your scope is REPORTED` in `PREAMBLE.md`, or the `BRIEF-199`
sentence), counting matches:

    ARM A  git diff 73dd717^1 73dd717 -- docs/briefs/PREAMBLE.md   -> 1   (two-dot, mainline)
    ARM B  git show 73dd717                                        -> 1   (NO flag typed)
    ARM C  git log -p c749334..80463a5                             -> 0   (the ruling's case)
    ARM D  git log -p --cc c749334..80463a5                        -> 1
    ARM E  git diff 73dd717^2 73dd717 -- docs/briefs/PREAMBLE.md   -> 1   (two-dot, branch side)

ARM B is decisive against the phrase "visible only to `--cc`": `git show` **defaults** to
the combined diff on a merge, so the reviewer never types the flag. ARM A is decisive
against "appears in no branch diff": diffing a merge against its own mainline parent is
about as ordinary as reviewing gets, and it prints every invented line.

Only ARM C - the default per-commit walk - is blind, and that is the true and narrow
version of the claim. **Whether a reviewer sees merge-invented content is therefore a
function of which command they ran, which is a PRACTICE.** A rule about what "reading a
range" must include is a policy choice, and the ruling makes it while denying that it is
one. This matters beyond wording: the ruling's own §"What a reviewer must do from now on"
already imposes a new obligation (run the command, say what you found), which only makes
sense as policy.

**The conclusion is untouched and should be restated on the ground that actually holds:**
a range declaration records the range, not the commands. It cannot distinguish a reviewer
who ran `git show` on each merge from one who ran `git log -p` over the span, so it must
not clear merge-invented content on its own. That is epistemic, and it is airtight.

**Suggested fix.** In decision 2, delete *"This is a statement about what a reviewer's
reading physically contains, not a policy preference"* and the sentence ending
*"it is visible only to `--cc`"*, and write:

> **2. A RANGE DECLARATION DOES NOT COVER A MERGE'S INVENTED CONTENT.** A declaration
> records the SPAN a reviewer read, never the commands they ran, and the two default
> readings disagree: `git log -p c749334..80463a5` prints none of `73dd717`'s invented
> lines (0 matches, measured), while `git show 73dd717`, `git diff 73dd717^1 73dd717` and
> `git log -p --cc` each print them (1 match each). **This is a policy choice and it is
> made deliberately:** because a bare range cannot tell those readings apart, it must not
> be allowed to clear merge-invented content. The visible absence is worth more than a
> declaration that might mean either.

### H2 - the ruling prescribes a reviewer command whose promised ZERO is unreachable by construction, and the same conflation produced its own headline number

`RULING-231B-merge-coverage.md`, "What a reviewer must do from now on":

>     git show --cc <merge> | wc -c
>
> and say what you found. **A zero there is a real result and cheap to produce.**

Measured on the two merges the ruling itself certifies as clean:

    $ git show --cc b9b59dd | wc -c
    236
    $ git show --cc cd8c938 | wc -c
    248

**That command can never return 0 for any merge that exists**, because its output always
carries the commit header and message. A reviewer who follows the instruction literally
gets a non-zero on a clean merge, has been told a zero is the clean result, and must now
invent a threshold - which is the "clean zero that explains itself" failure mode running
in reverse.

The same conflation is the ruling's headline: **11376** is diff plus message. The combined
DIFF is 7226 bytes, which is what the detector reports as `cc=7226B`, and what `#222`
recorded as *"false by 7226 bytes"*. The ruling and the detector look like they disagree
by 4150 bytes and do not.

**Suggested fix.** Suppress the message, which makes the zero real - measured:

    $ git show --cc --format= b9b59dd | wc -c
    0
    $ git show --cc --format= cd8c938 | wc -c
    0
    $ git show --cc --format= 73dd717 | wc -c
    7226

Replace the prescribed command with `git show --cc --format= <merge> | wc -c`, and in the
evidence section replace *"`git show --cc 73dd717 | wc -c` -> 11376"* with
*"`git show --cc --format= 73dd717 | wc -c` -> 7226, the same figure the detector reports
as `cc=7226B`"*. The 11376 form may be kept as a parenthetical only if it says what the
extra bytes are. **The same edit is needed at `REVIEW-R21.md:553`**, which carries the
11376 figure into the corrected record.

### M1 - "That entry stays accurate" is FALSE: the wiring exemption still says the question is OPEN, and this ruling closed it

The ruling states: *"`check-checkers-are-wired.py` already records the checker as
`UNWIRED_BY_DECISION` with the reason above. That entry stays accurate."*

`docs/reviews/check-checkers-are-wired.py:421-432` reads, verbatim:

> "... Whether merge-invented content should be GATED, and at what threshold, is Tier 0's
> ruling and **is open on task #222**; the instrument ships first so the ruling is made on
> a measurement. It carries `--strict` for the day that ruling arrives ..."

After `830d299` that is no longer true. The ruling IS the ruling that entry is waiting
for: it decides the mechanism (a set-ratchet over `(merge, path)`) and refuses the
zero-demand. What is still outstanding is the BASELINE, not the ruling. Leaving the entry
as-is is the exact defect class this repository keeps finding - an exemption reason that
describes a state the tree has left.

**Suggested fix.** Rewrite the reason in place (never append):

> "its own docstring: it reports a population to READ, and a reflow that re-wraps a
> paragraph surfaces there as many 'invented' lines while the sentence is unchanged.
> **RULED on 2026-09-02 (#231B, `docs/reviews/RULING-231B-merge-coverage.md`): the gate is
> a SET-RATCHET over `(merge, path)` pairs and `--strict` is REFUSED as a zero-demand.**
> Wiring now waits on the BASELINE, not on the ruling: the baseline is a claim that
> someone read the population, and it is not written yet. `--strict`, `--self-test` and
> `--synthetic-test` are runnable now."

### M2 - the ruling's population, the gate's container and the refusal's evidence are THREE different containers, and none of them is named as the baseline's

- The ruling's stated population: **21 merges / 53 invented lines**, over `c749334..HEAD` -
  which is R21's REVIEW RANGE.
- `check-review-coverage.py`'s container is `CONTAINER_BASE` = `8695101` (fixed, not
  derived - R12-H3). Measured there:

      $ uv run --frozen python docs/reviews/check-merge-invented.py --range 8695101..HEAD
      73dd717  cc=7226B   paths_scanned=15  invented=53
      92cb89b  cc=7429B   paths_scanned=91  invented=22
      a881344  cc=13279B  paths_scanned=42  invented=38
      f2a7bce  cc=2151B   paths_scanned=60  invented=6
      TOTAL merges=95 invented_lines=119

  **95 merges, 119 invented lines, FOUR non-zero merges** - none of which appears in the
  ruling.
- The refusal to write a baseline is argued from a THIRD population: *"`#222` left 9 of its
  10 flagged merges unexamined"*, which comes from #222's 133-merge / 224-line sweep
  reaching BEFORE this trunk.

So the ruling justifies withholding a baseline for an unnamed container using an
unread-population fact from a container it does not share with either of the other two.
Over the range it DOES name, the entire population is one merge, and `#222` records that
merge as "READ IN FULL". The stated blocker does not bind the stated population.

**Suggested fix.** Name the container once, in the ruling, and give its number:

> The baseline's container is `check-review-coverage.py`'s `CONTAINER_BASE` (`8695101`),
> because a merge-coverage ratchet and a review-coverage ratchet that disagree about their
> population will disagree about their backlog. Measured there today: **95 merges, 119
> invented lines, in 4 merges** - `73dd717` (53), `a881344` (38), `92cb89b` (22),
> `f2a7bce` (6). `#222` read `73dd717` in full; the other three are unread, and that -
> not the size of the number - is why the baseline waits.

That is a smaller and more honest gap than "9 of 10 unexamined" implies, and it names
exactly what a future agent has to do.

### M3 - decision 3's reflow argument was never measured, and measuring it weakens the reason without touching the conclusion

The ruling refuses `--strict` because *"a reflow that re-wraps a paragraph surfaces as many
invented lines while the sentence is unchanged"*, alongside *"53 invented lines exist
across 21 merges today"* - a juxtaposition that reads as though today's 53 are largely
reflow noise. Nobody measured it. I did.

Probe: for each non-zero merge, take every non-blank line in the merge's blob of a file
that is in NEITHER parent's blob of that file (the detector's own discriminator), then
classify it REFLOW if its whitespace-normalised text is a substring of a parent's
whitespace-normalised blob - which is exactly what a re-wrap produces - and CONTENT
otherwise.

    73dd717: invented=53 reflow=6  content=47
    92cb89b: invented=23 reflow=3  content=20
    a881344: invented=40 reflow=4  content=36
    f2a7bce: invented=6  reflow=0  content=6
    TOTAL invented=122 reflow=13 content=109   reflow_share=10.7%

**Roughly 11% reflow, 89% genuine content.** The five reflow lines in `73dd717` are all
re-wraps of the `AND THIS SENTENCE MADE THE GATE RED` paragraph; the sixth, in
`PREAMBLE.md`, is `` `completed` when you finish. ``.

This does NOT overturn decision 3. The sound form of the argument is forward-looking - a
zero-demand goes red on the FIRST future re-wrapped paragraph, whatever today's mix is, and
this repo has 119 consecutive unread red mirror runs as evidence of what happens next. But
as written the refusal leans on an implication about the current population that is false,
and the ruling's own "how many are reflow and how many are content is **not** [measured]"
turns out to be one command away.

**Suggested fix.** In decision 3 replace *"53 invented lines exist across 21 merges today
and the checker's own wiring exemption says why - a reflow that re-wraps a paragraph
surfaces as many invented lines while the sentence is unchanged"* with:

> Measured over the gate's container: 119 invented lines in 4 merges, of which ~11% are
> re-wraps of a sentence present in a parent (13 of 122 by the substring test) and ~89% are
> genuine content. **So the refusal is NOT that today's population is mostly noise - it is
> not.** It is that a zero-demand goes red on the FIRST future re-wrapped paragraph, and
> this repository has already measured what happens to a gate that is red by construction:
> 119 consecutive mirror failures went unread, because a switched-off gate and a failing
> gate render identically.

That also removes the stated obstacle to writing the baseline, which is M2's other half.

### M4 - claim 6 is WRONG in substance and in structure: R21 has no §2, and the item it means does not contradict the universal - it repeats it

The ruling and the correction both assert: *"Its own §2 had already named `73dd717` as
needing separate treatment, eighteen sections above"* / *"this report's own §2 had already
contradicted by naming `73dd717` as one of the two 'covered above'"*.

Three things are wrong.

**(a) R21 has no §2.** Every `§` in the file refers to the BRIEF's sections:

    $ grep -n "§" docs/reviews/REVIEW-R21.md
    32:  ... §C4 says three;
    192: §C4 asks whether anything of `410e370`'s work was lost. ...
    514: - **`set -uo pipefail` does not disable errexit** (§C6). ...
    578: ## §E gates, each exit code on its own line
    647: The brief's §D asks for it at the END; ...

(:558 and :131 are the correction's own text and a table cell.) The referent is **item 2
of the ordered list under `## Corrections to the brief, before anything else`**,
`REVIEW-R21.md:31-34`.

**(b) That item does not contradict the universal - it asserts it.** Verbatim:

> 2. **There are FOUR merges, not three.** `git log --merges --oneline c749334..80463a5`
>    returns `7197271`, `73dd717`, `cd8c938`, `b9b59dd`. §C4 says three;
>    `cd8c938` (fix/196-adr-citation-read) is the one not counted. **I ran
>    `git show --cc` on all four.**

It corrects the BRIEF's merge COUNT, and its last sentence is R21 claiming it ran the very
command that refutes its own conclusion. That is a sharper indictment than the one the
ruling wrote - and it is the opposite of "already contradicted".

**(c) "eighteen sections above" is wrong.**

    $ awk 'NR>32 && NR<546 && /^#+ /{c++} END{print c+0}' docs/reviews/REVIEW-R21.md
    10

Ten headings, at every heading level.

**Suggested fix.** In both the ruling and the `REVIEW-R21.md` correction block, replace the
"§2 ... eighteen sections above" sentence with:

> `REVIEW-R21.md:31-34` (item 2 of "Corrections to the brief") lists all four merges by sha
> and closes *"I ran `git show --cc` on all four."* That is not a contradiction the report
> contained - it is the claim that the refuting command was run. The contradiction is
> between the report and the detector, and it was available to anyone who re-ran the
> command the report says it ran.

### L1 - the corrected bullet keeps "`73dd717` ... covered above", and that half is not true

The bullet now reads: *"`b9b59dd` and `cd8c938` are clean; `73dd717` and `7197271` are
covered above."* The universal was removed; this clause was not touched.

    $ grep -n "73dd717" docs/reviews/REVIEW-R21.md
    32:   returns `7197271`, `73dd717`, `cd8c938`, `b9b59dd`. §C4 says three;
    553:  > `git show --cc 73dd717 | wc -c` returns **11376**, ...
    558:  > report's own §2 had already contradicted by naming `73dd717` as one of the
    563:  > `REVIEW-COVERS: c749334..80463a5` is what clears `73dd717` in

`7197271` is genuinely covered above, in M1 at :190. `73dd717` is not: :32 is the
merge-count list, and :553-563 are the new correction, which is BELOW. So the surviving
clause sends a reader upward to nothing.

**Suggested fix.** Rewrite the bullet as:

> - **The four merges.** `b9b59dd` and `cd8c938` are clean; `7197271` is covered in M1
>   above; `73dd717` is corrected immediately below.

### N1 - the correction is a rider inside a bullet whose prose was also rewritten, which sits against #93's precedent; say which convention governs

`830d299` does two things to one bullet: it DELETES the false universal from the prose, and
it ADDS a blockquote that re-quotes the deleted sentence. #93 records the opposite habit -
*"corrected IN PLACE at all three sites, not annotated with a rider"* - while #231 Part A
established the provenance-note shape for exactly this kind of archaeological correction,
and `docs/reviews` is deliberately NOT in `check-review-coverage.py`'s `RECORD_PATHS`
(which holds only `CHANGELOG.md`, `docs/worklogs`, `review-coverage-backlog.txt` and
`docs/plans`), so a review document is treated by the live gate as work, not as a record
that must stand unedited.

I think the hybrid is right here and the ruling's reason for it is sound - `#203` and
`#111` both govern addresses that ROT as the tree moves, whereas this sentence was false
when written, so neither applies. But the block does not say which precedent it is
following, and a future reader who knows #93 will read it as a violation.

**Suggested fix.** Add one sentence to the correction block:

> This is the same shape as `#231` Part A's provenance note: the false sentence is deleted
> from the prose and quoted here, because a reader who arrives via `check-review-coverage.py`
> needs to know what the green they are looking at was resting on. `#93`'s
> "no rider" rule governs a correction with nothing to preserve; this one has a live gate
> resolving through it.

---

## §3 What the ruling asserts that the tree DOES support

Checked so the report is not one-sided:

- `check-merge-invented.py` really does carry `--strict`: `:356`,
  `ap.add_argument("--strict", action="store_true", help="exit 1 on any finding")`.
- The wiring exemption really does give the reflow reason the ruling attributes to it
  (`check-checkers-are-wired.py:421-432`) - only its "is open" clause has gone stale (M1).
- `#151`'s set-ratchet really is the proved shape:
  `check-review-coverage.py:106`, `## IT IS A RATCHET, NOT A DEMAND FOR ZERO (#151)`.
- `review-r22` really did choose the narrow form AND list what it had not read
  (`REVIEW-R22.md:3` and `:476-485`), so decision 1's "the instrument already supports the
  honest shape" is correct.
- Decision 1 itself survives attack: banning the bare form would not stop a false `PATHS:`
  list, and R22 demonstrates the honest form is reachable. Nothing in my measurements
  touches it.
- `830d299` introduces no new gate red: `check-review-coverage.py` exits 1 at the subject
  AND at its parent `7e8adfa`.

---

## §4 Gates

Only the gates whose subject this commit touches were run. Each exit code on its own line.

    $ uv run --frozen python docs/reviews/check-merge-invented.py b9b59dd cd8c938 73dd717
    rc=0
    $ uv run --frozen python docs/reviews/check-review-coverage.py    # at 830d299
    rc=1     (PRE-EXISTING: same rc=1 at parent 7e8adfa via --reviews)
    $ uv run --frozen python docs/reviews/check-review-coverage.py --reviews /tmp/rev-parent
    rc=1

I did NOT run the full suite, mypy, ruff or the harness floors: the subject is two markdown
files and touches no code path any of them read. That is a scoping decision, not a claim
they pass.

---

## §5 My own instrument failures, recorded

1. **My reflow probe and the checker disagree by 3 lines of 122** (`92cb89b` 23 vs 22,
   `a881344` 40 vs 38). My probe counts every non-blank line of the merge blob absent from
   both parent blobs; the checker's per-path accounting evidently differs slightly. 2.5%,
   and it does not move the 11% conclusion in either direction, but the two numbers are not
   the same measurement and I am not asserting that they are.
2. **My first attempt at the counterfactual deleted BOTH `REVIEW-COVERS` occurrences** in
   the copied `REVIEW-R21.md` - line 3 and the correction's quotation at :563 - which would
   have made the arm untrustworthy if the parser had been loose. I re-ran with `sed '3d'`
   only, after checking the parser is anchored at `^<!--`. The looser version happened to
   give the same answer; I am reporting the shape, not the outcome.
3. `git branch -r --contains` is blocked by this environment's write-guard hook as a
   mutating command. I used `git merge-base --is-ancestor` instead (rc=0: `73dd717` is an
   ancestor of `origin/main`).

---

## §6 What I did NOT verify

- **Whether a `(merge, path)` set-ratchet is the RIGHT mechanism.** I checked that #151's
  set-ratchet exists and works and that the ruling describes it accurately. I did not
  design or prototype the merge-invented ratchet, did not write a backlog file, and have
  no opinion on its row format. Decision 3's mechanism choice is unreviewed by me.
- **The other three non-zero merges' 66 invented lines** (`a881344` 38, `92cb89b` 22,
  `f2a7bce` 6). I classified them reflow-vs-content mechanically. **I did not read one of
  them as prose**, so I cannot say whether any is a rule change of the `PREAMBLE.md` kind.
  That is the same gap the ruling declines to close, and it is where I would look next.
- **`#222`'s wider 133-merge / 224-line sweep.** I could not reproduce its container from
  the ruling or the task text (which base? which ref?) and did not guess one. The three
  populations in M2 are the three I could actually derive.
- **Whether `check-merge-invented.py`'s discriminator is itself correct.** I used it as an
  oracle for claims 2 and 5 and cross-checked it once by hand against the `--cc` output for
  `73dd717`. Its `--self-test` and `--synthetic-test` exist; I did not run them.
- **The N>2-parent path.** Every merge in every container I measured has exactly two
  parents. An octopus merge is untested by anything I ran.
- **Whether `git show`'s default-to-`--cc` behaviour holds under every config.** ARM B is
  measured in THIS repo with THIS git. A `diff.*` or `merge.*` config, or an older git,
  could in principle change it; I did not test another environment. H1's ARM A and ARM E
  do not depend on that default and carry the finding on their own.

---

Worktree: `/tmp/review-231b`, branch `review/231b`, this report committed there.
Removed after commit. Nothing pushed, nothing merged, neither subject file edited.
