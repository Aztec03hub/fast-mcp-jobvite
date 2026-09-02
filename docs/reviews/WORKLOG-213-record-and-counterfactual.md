# WORKLOG - #211 (R21-M1) + #213 (R21-M3)

Agent: `suborch-213`. Brief:
`docs/briefs/BRIEF-211-213-record-and-counterfactual.md`. Worktree
`/tmp/w211-213-record-and-counterfactual`, branch
`fix/211-213-record-and-counterfactual`, cut from `main` at `a52af14`.
Nothing pushed, nothing merged.

**Headline: I confirmed every number R21 published in M1 and M3, and I
disagree with M1's conclusion and with one of its background claims. The
background claim is the important one - it is false, and the thing it
misses is the root cause of BOTH findings.**

---

## §0 - Two corrections to my own dispatch, before anything else

1. **The brief names `d2159e7` as the base; my dispatch message named
   `a52af14`.** `a52af14` is right and I used it - `d2159e7` is its
   parent, and `a52af14` is the commit that ADDS the brief I was told to
   read. A worktree at `d2159e7` would not contain
   `BRIEF-211-213-record-and-counterfactual.md` at all.

       $ git merge-base --is-ancestor d2159e7 a52af14 ; echo $?
       0

   Not a defect in either document - the brief was written one commit
   before it was committed. It is the sixth count in this population whose
   edge moved by the act of committing it.

2. **`main` at `a52af14` is RED on the brief-report gate, and my own
   deliverable is what makes it green.**

       $ uv run --frozen python docs/reviews/check-brief-report-references.py
       ::error::A BRIEF CITES A REPORT THAT EXISTS NOWHERE IN THE REPO.
         FINDINGS-213-syntax-split.md   cited by BRIEF-211-213-record-and-counterfactual.md
       gate_rc=1

   The brief that dispatched me cites the report it dispatched me to
   write. That is the accepted false positive the #213 ruling is about,
   firing on the brief that asks about it. It is self-clearing and I
   cleared it, but **`main` is red right now** and anyone measuring this
   gate before my branch lands should know why.

---

## §1 - #211: what I verified, and where I part company with R21

### Everything R21 measured, re-measured - all CONFIRMED

    $ git diff 410e370 7197271 -- docs/worklogs/WORKLOG-199-ratchet-defects.md | wc -c
    0
    $ git show 410e370:docs/worklogs/WORKLOG-199-ratchet-defects.md | wc -l
    320
    $ git show 7197271:docs/worklogs/WORKLOG-199-ratchet-defects.md | wc -l
    320

Nothing of `410e370`'s work was lost. Confirmed.

    $ git show 410e370:docs/briefs/BRIEF-199-ratchet-defects.md | grep -nE 'REVIEW-|WORKLOG-|FINDINGS-'
    33:3. `docs/reviews/REVIEW-R20.md` - **M3 and L1 are yours.** Read what R20

    $ git show 7197271:docs/briefs/BRIEF-199-ratchet-defects.md | grep -nE 'REVIEW-|WORKLOG-|FINDINGS-'
    33:3. `docs/reviews/REVIEW-R20.md` - **M3 and L1 are yours.** Read what R20
    67:`1985471`, `WORKLOG-187-floor-container.md`, `REVIEW-R20.md` - and **the

`410e370` names none of the three; the kept side names two. Both confirmed,
line for line.

### The blob map R21 did not draw, and which changes the conclusion

    $ for c in 6f921f8 fa94f77 4be5356 73dd717 410e370 7197271; do \
        printf '%s %s\n' "$c" "$(git rev-parse $c:docs/briefs/BRIEF-199-ratchet-defects.md)"; done
    6f921f8 b48e987...   suborch-199's own hunk   - names 1985471, WORKLOG-187, REVIEW-R20
    fa94f77 748ea90...   "main's wording"         - names NONE
    4be5356 748ea90...   main at the merge        - names NONE
    73dd717 693127f...   the hand resolution      - names 1985471, WORKLOG-187, REVIEW-R20
    410e370 748ea90...   the revert (adopts main) - names NONE
    7197271 693127f...   kept via --ours          - names 1985471, WORKLOG-187, REVIEW-R20

**Three distinct versions, not two.** R21's finding is built on comparing
`410e370` with `7197271`, which are two of the three.

### WHY I DISAGREE WITH M1 AS FILED

R21 says the merge message *"describes the two versions backwards"*. The
message's sentence is:

> `suborch-199` reverted its own BRIEF-199 hunk ... **its version** removed
> only the phantom and left two report names standing as live citations

*"its version"* is `suborch-199`'s HUNK - `b48e987` at `6f921f8` - not the
post-revert tip `748ea90`. About `b48e987` the sentence is **accurate**: it
does name exactly those two. The message is in fact quoting
`suborch-199`'s own worklog, `WORKLOG-199:127-133`, which says the same
thing about itself and is also accurate.

**So the message is not backwards. R21 measured the right blobs and
compared the wrong pair.** Applying R21's suggested correction verbatim
would publish a claim the next careful reader can measure and find wrong -
and this project has already recorded that a derived record decays at every
copy-forward.

**The real defect is different, and worse.** The sentence is offered as the
REASON the kept text is better. The kept text (`693127f`) carries the
identical two live citations. The only version that removes all three names
is `748ea90` - the one the merge REFUSED. **It is a true reason that does
not discriminate between the option taken and the option rejected**, and
the property it praises belongs to the discarded text.

### AND R21'S BACKGROUND CLAIM IS FALSE - this is the root cause

Task #211's description carries this, as an "ALSO CHECKED":

> `git show --cc` on all four merges in the range (`7197271`, `73dd717`,
> `cd8c938`, `b9b59dd`) produces an empty combined diff, i.e. every file in
> each result matches one parent. **No third version was invented at any
> merge.**

Measured:

    $ for m in 7197271 73dd717 cd8c938 b9b59dd; do \
        printf 'merge %s  combined-diff bytes: %s\n' "$m" "$(git show --cc --format='' $m | wc -c)"; done
    merge 7197271  combined-diff bytes: 0
    merge 73dd717  combined-diff bytes: 7226
    merge cd8c938  combined-diff bytes: 0
    merge b9b59dd  combined-diff bytes: 0

    $ git show --cc --format='' 73dd717 | grep -E '^diff --cc'
    diff --cc docs/briefs/BRIEF-199-ratchet-defects.md
    diff --cc docs/briefs/PREAMBLE.md
    diff --cc docs/reviews/check-brief-report-references.py

**`73dd717` invented a third version in three files, one of which is the
file the #213 ruling lives in.** R21's reassurance is exactly the check
that would have caught it, and it was measured wrong. Three of four merges
are clean; the fourth is not, and it is the one that matters.

---

## §2 - #211: WHERE the correction belongs, and the argument

Written to `docs/worklogs/WORKLOG-199-ratchet-defects.md` as a new dated
`§2b`, inserted before `§3`.

**Why not the commit message.** It cannot be edited without rewriting
history, and `0291bac` plus `CONTRIBUTING` rule that history is not
rewritten here. Not available.

**Why not a new record document.** This was my first instinct and I
rejected it. A fresh file is a SECOND COPY of a sentence that already
exists in `WORKLOG-199:127-133`, and the copy would be the one nobody
opens. The failure mode is measured on this project: a derived record
decays at every copy-forward.

**Why `WORKLOG-199` §2, and not §7 or a new file.** §2 is where the
sentence was FIRST WRITTEN. `7197271`'s message quotes it; `REVIEW-R21`
inherited it from the message. It is the upstream copy, and correcting the
source is the only placement that stops the next copy being made.

**Why an inserted section and not a rewrite of §2.** The project rule is to
rewrite prose in place rather than append corrections - and it does not
apply here, because **§2 is not wrong**. Its sentence is true of the blob
it describes. What is missing is what the MERGE did afterwards, which
post-dates the worklog and which its author could not have known. Rewriting
a true historical measurement to carry a later fact would destroy the
record of what was known when. A dated section is the correct shape for
new information about a closed record.

**The honest weakness, stated because the brief asked for the argument
rather than the document.** A reader of the merge will NOT stumble into
this. The only reader who reaches it is a reviewer auditing a range - which
is precisely how this was found, twice now. I considered arguing for
leaving the record wrong with the truth only in the worklog, per the
brief's invitation. I did not, for one reason: **the sentence is being
copied forward.** It has already made three hops (worklog -> commit message
-> review report) and gained an error on the last one. Correcting the head
of that chain is cheap and stops hop four. If it were a dead sentence I
would have left it.

---

## §3 - #213: the counterfactual. NO RULING MADE.

Full output in `docs/reviews/FINDINGS-213-syntax-split.md`; the runnable
artefact is `docs/reviews/probe-213-syntax-split.py`. **I did not edit the
docstring and I did not rule.** Summary of what the probe found:

**R21's partition is exactly right at its own revision.** `22` cited,
`BOTH 6 / PATH-only 14 / BARE-only 2`, and the two bare-only names are the
ones R21 named. Its *"today the split would drop ZERO live detections"*
also holds. No disagreement anywhere in M3's numbers.

**The history answers the question R21 left open.** Over 110 first-parent
commits touching `docs/briefs`, the split loses a detection on 10 of them,
across 3 distinct names:

| name | ever tracked? | cost of the split |
|---|---|---|
| `REVIEW-R20.md` | YES `1237de0` | delay only |
| `REVIEW-R21.md` | YES `1045edb` | delay only |
| `REVIEW-CHECKLIST.md` | **NO, never existed** | **permanent loss** |

`REVIEW-CHECKLIST.md` is a genuine bare-only citation, in real brief prose
at `BRIEF-199:66`, to a report that has never existed on any ref. **So the
residual class the ruling refuses the split for is not hypothetical: it has
occurred once, on two commits, out of 110.** Whether one permanent loss in
110 commits outweighs a false positive that costs a sentence is the ruling,
and it is yours.

**MY OWN PROBE SHIPPED THE DEFECT ITS SUBJECT DOCUMENTS.** My first history
run reported `REVIEW-CHECKLIST.md` as *"YES, added at 1b7975b"*, which
inverted the headline - it made all three names look like delays and the
split look free. The pathspec was `-- "*REVIEW-CHECKLIST.md"`, a free left
edge, and it matched `docs/CODE-REVIEW-CHECKLIST.md`. That is the exact
truncation `check-brief-report-references.py:118-130` records as a
published error, forty lines above the ruling I was auditing. Fixed to
`:(glob)**/NAME` and proved both ways (negative: 0 rows on the phantom;
positive: still finds `REVIEW-R20.md`). **I did not catch it by reading. I
caught it because the answer was too clean.**

---

## §4 - THE ROOT CAUSE JOINING #211 AND #213

The syntax-split bullet - the text #213 is about - **exists in neither
parent of `73dd717` and appears first in the merge commit itself**:

    $ git log -1 --format='%P' 73dd717
    4be53560bc64c80ff397759889de1e7648101deb 6f921f856fb641e715780b7a86b9a2a721324a99

    $ git show 4be5356:docs/reviews/check-brief-report-references.py | grep -c 'A syntax split'
    0
    $ git show 6f921f8:docs/reviews/check-brief-report-references.py | grep -c 'A syntax split'
    0
    $ git show 73dd717:docs/reviews/check-brief-report-references.py | grep -n 'A syntax split'
    69:- **A syntax split**, counting only path-qualified forms as citations

**The backwards reasoning entered the repository inside a merge
resolution.** No branch diff ever showed it as an addition; no reviewer saw
it before it landed; `git log -p` on a branch will not surface it. #211 and
#213 are not two findings - they are one merge, `73dd717`, seen from two
sides. The message of the NEXT merge (`7197271`) names this exact hazard -
*"a merge resolution reintroducing what a branch had fixed"* - while the
instance sits one commit behind it, unlooked at.

**REPORTED, NOT FILED.** My brief grants no `TaskCreate` mandate and
`PROTOCOL-sub-orchestrators.md` rules that filing is Tier 0's call. So,
reported: **there is no gate anywhere in this repository that looks at
merge-invented content.** `git show --cc` over the trunk is a one-line
check, it is already the check R21 reached for by instinct, and R21 ran it
wrong. That is a candidate for a real gate and it is your decision, not
mine.

---

## §5 - Gates, each exit code on its OWN line

No `&& echo OK` anywhere; every exit code below was read on its own line.

    $ uv run --frozen python docs/reviews/check-brief-report-references.py
        Every report a brief cites is committed, or recorded as lost.
    rc=0

    Cited but not in the repo: 3   (was 4 on `main`; my report cleared the fourth)
    Cited at the wrong path:   0

    $ uv run --frozen ruff check .
        All checks passed!
    rc=0

    $ uv run --frozen ruff format --check .
        141 files already formatted
    rc=0

    $ uv run --frozen mypy .
        Success: no issues found in 141 source files
    rc=0

    $ uv run --frozen pytest
        887 passed, 6 deselected in 57.27s
    rc=0

The floor was DERIVED, not retyped:

    $ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
    check-suite-floor.sh 887

**887 passed against a floor of 887, and ZERO skipped.** The 6 deselected
are the `credentialed` marker, deselected by the `addopts` in
`pyproject.toml:157-166` by design and collected with `--collect-only` so
they cannot rot - `893 tests collected` with the marker filter removed.
A deselect is not a skip and I checked which it was rather than assuming.

---

## §6 - What I did NOT verify

- **I did not run `actionlint`, ShellCheck, or the CI harness gates.** My
  change touches no shell, no workflow and no harness. Not attempted, and
  I am not claiming they pass.
- **Whether `73dd717`'s OTHER two merge-invented files carry defects.**
  I proved `check-brief-report-references.py` was hand-edited at that merge
  and traced the one bullet #213 is about. `docs/briefs/PREAMBLE.md` and
  the rest of the checker's 7226-byte combined diff I did NOT read line by
  line. **This is the single most likely place for another finding and I
  am handing it over unread**, because reading it is a review round, not a
  clause of my brief.
- **Whether the same merge-invention exists on merges OUTSIDE
  `c749334..80463a5`.** I checked exactly the four merges R21 named. I did
  not sweep the trunk. My claim of "no gate looks at this" is a claim about
  a `grep` for `--cc` and `show --cc` across `.github/` and `docs/reviews/`,
  which found none - it is not a claim that I read every checker.
- **The counterfactual's `--history` pass walks FIRST-PARENT commits.** A
  citation that existed only on a side branch and never on the trunk is
  invisible to it. I believe that is the right population for "what would
  the gate have shown a human", since CI runs on the trunk, but it is a
  choice and a different choice would give a different denominator.
- **I did not measure how often a bare-only citation is written today
  versus a year ago.** The trend, not the count, is what would tell you
  whether the residual is shrinking. Out of scope and not attempted.

---

## §7 - Worktree

**LEFT IN PLACE** at `/tmp/w211-213-record-and-counterfactual`, per the
dispatch. Not removed. Branch `fix/211-213-record-and-counterfactual`.
