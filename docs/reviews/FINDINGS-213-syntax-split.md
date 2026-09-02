# FINDINGS #213 - the counterfactual that would decide the syntax split

Agent: `suborch-213`, tasks #211 and #213. Brief:
`docs/briefs/BRIEF-211-213-record-and-counterfactual.md`. Worktree
`/tmp/w211-213-record-and-counterfactual`, branch
`fix/211-213-record-and-counterfactual`, cut from `main` at `a52af14`.

**THIS DOCUMENT RULES NOTHING.** `review-r21` filed no task for the ruling
and my brief repeats the instruction in capitals. The docstring is not
edited here. What follows is the measurement and nothing else; the call
is Tier 0's.

**THE PROBE IS THE ARTEFACT.** `docs/reviews/probe-213-syntax-split.py`
is committed beside this file and every number below is its output,
pasted. Prose about a measurement decays into a claim about one, so the
prose here is confined to what the probe cannot print: what the numbers
mean and where the instrument failed.

    uv run --frozen python docs/reviews/probe-213-syntax-split.py --rev 80463a5
    uv run --frozen python docs/reviews/probe-213-syntax-split.py --rev a52af14
    uv run --frozen python docs/reviews/probe-213-syntax-split.py --history

---

## The question

`check-brief-report-references.py:69-72` refuses a syntax split - counting
only path-qualified forms as citations, treating a bare basename as prose -
*"because it is FALSE HERE: `suborch-199` measured six names cited BOTH
ways, so the bare form carries real citations and the split would drop
them."*

R21-M3 established that this reason is backwards: a name cited both ways is
still caught by its path form, so the six are evidence FOR the split's
safety. R21 then said, correctly, what it could not settle:

> **NOT SETTLED, AND IT IS A RULING NOT A FINDING:** how often a bare-only
> citation has named a genuinely missing report across the project's
> history. That is the counterfactual that would actually decide the split.

That is what the probe measures.

---

## 1. R21's numbers, re-derived at R21's own revision - ALL CONFIRMED

```
$ uv run --frozen python docs/reviews/probe-213-syntax-split.py --rev 80463a5
===== TODAY at 80463a5 =====
Report names cited:         22
  cited BOTH ways:          6  REVIEW-R16.md, REVIEW-R17.md, REVIEW-R18.md, REVIEW-R19.md, REVIEW-R20.md, WORKLOG-187-floor-container.md
  cited PATH-qualified only:14
  cited BARE only:          2  FINDINGS-168-range-before-paths.md, REVIEW-R21.md

CURRENT gate detects:       1  REVIEW-R21.md
SPLIT gate would detect:    0  (none)
LOST to the split:          1  REVIEW-R21.md

Of those lost, already RECORDED as known-missing: 1  REVIEW-R21.md
Of those lost, NEVER recorded (a LIVE detection): 0  (none)
```

R21 said `BOTH 6 / PATH-only 14 / BARE-only 2`, and named
`FINDINGS-168-range-before-paths.md` and `REVIEW-R21.md` as the bare-only
pair. Confirmed exactly, name for name. R21's *"today the split would drop
ZERO live detections"* is also confirmed: the one lost name was already
recorded as known-missing, so no live detection was at stake.

**I found no disagreement with R21 anywhere in this partition.**

## 2. The same measurement at `main` today

```
$ uv run --frozen python docs/reviews/probe-213-syntax-split.py --rev a52af14
===== TODAY at a52af14 =====
Report names cited:         26
  cited BOTH ways:          7  REVIEW-R16.md, REVIEW-R17.md, REVIEW-R18.md, REVIEW-R19.md, REVIEW-R20.md, REVIEW-R21.md, WORKLOG-187-floor-container.md
  cited PATH-qualified only:18
  cited BARE only:          1  FINDINGS-168-range-before-paths.md

CURRENT gate detects:       4  FINDINGS-213-syntax-split.md, REVIEW-R21.md, WORKLOG-194-watch-last-two.md, WORKLOG-208-orphan-leads.md
SPLIT gate would detect:    4  FINDINGS-213-syntax-split.md, REVIEW-R21.md, WORKLOG-194-watch-last-two.md, WORKLOG-208-orphan-leads.md
LOST to the split:          0  (none)

Of those lost, already RECORDED as known-missing: 0  (none)
Of those lost, NEVER recorded (a LIVE detection): 0  (none)
```

`LOST 0` today as well - for a different reason than at `80463a5`: the
bare-only set has shrunk to one name and that name is tracked. Note the
population moved from 22 to 26 names between two commits. **A one-revision
answer to this question is worth very little**, which is the case for the
history pass rather than a second snapshot.

## 3. THE COUNTERFACTUAL: every commit that ever touched `docs/briefs`

```
$ uv run --frozen python docs/reviews/probe-213-syntax-split.py --history
===== HISTORY: 110 first-parent commits touching docs/briefs =====
commit    cited both path bare  now split LOST  lost names
70cd2cae5     0    0    0    0    0     0    0  (none)
e62f65aa8     0    0    0    0    0     0    0  (none)
3f313ceef     1    0    1    0    1     1    0  (none)
524035430     1    0    1    0    1     1    0  (none)
1b59551e8     1    0    1    0    0     0    0  (none)
025aa5590     1    0    1    0    0     0    0  (none)
8b74053ee     1    0    1    0    0     0    0  (none)
61d117195     2    0    2    0    1     1    0  (none)
667db50c1     2    0    2    0    0     0    0  (none)
f83bf7ac5     2    0    2    0    0     0    0  (none)
530449fdf     2    0    2    0    0     0    0  (none)
e585d6509     2    0    2    0    0     0    0  (none)
eb4d25466     2    0    2    0    0     0    0  (none)
9760d6172     2    0    2    0    0     0    0  (none)
555bad6b6     3    0    3    0    1     1    0  (none)
c5bdeb6e5     3    0    3    0    0     0    0  (none)
d25ceeaf9     3    0    3    0    0     0    0  (none)
1fef5bed1     3    0    3    0    0     0    0  (none)
268e0192f     3    0    3    0    0     0    0  (none)
7bfd3ebb4     3    0    3    0    0     0    0  (none)
8401cb913     3    0    3    0    0     0    0  (none)
1501033c0     3    0    3    0    0     0    0  (none)
d0abd10e3     4    0    4    0    1     1    0  (none)
bb546bae8     4    0    4    0    1     1    0  (none)
a99238b09     4    0    4    0    0     0    0  (none)
90d68f6d6     4    0    4    0    0     0    0  (none)
187c210b4     4    0    4    0    0     0    0  (none)
8202d131f     4    0    4    0    0     0    0  (none)
0fe4628ab     5    0    5    0    1     1    0  (none)
a48adf86a     5    0    5    0    0     0    0  (none)
686820cf7     5    0    5    0    0     0    0  (none)
7bfe24bdb     5    0    5    0    0     0    0  (none)
bc0f958eb     5    0    5    0    0     0    0  (none)
a409a326d     6    0    6    0    1     1    0  (none)
03c4ae629     6    0    6    0    0     0    0  (none)
20e71eda8     7    0    7    0    1     1    0  (none)
5eb64b043     7    0    7    0    1     1    0  (none)
5e439ccb4     7    0    7    0    0     0    0  (none)
9fae4bba3     7    0    7    0    0     0    0  (none)
27c6944f9     7    0    7    0    0     0    0  (none)
a44ce90de     7    0    7    0    0     0    0  (none)
a07a6d084     7    0    7    0    0     0    0  (none)
2cf76a51f     7    0    7    0    0     0    0  (none)
280b6896c     7    0    7    0    0     0    0  (none)
21207b1e5     7    0    7    0    0     0    0  (none)
e9a668d78     7    0    7    0    0     0    0  (none)
2ef396031     7    0    7    0    0     0    0  (none)
a47dce654     7    0    7    0    0     0    0  (none)
f699f74a2     7    0    7    0    0     0    0  (none)
06a435940     7    0    7    0    0     0    0  (none)
167f52619     7    0    7    0    0     0    0  (none)
3e0c8aeb8     7    0    7    0    0     0    0  (none)
e3780b4a4     7    0    7    0    0     0    0  (none)
105a97948     7    0    7    0    0     0    0  (none)
52363e4ba     7    0    7    0    0     0    0  (none)
7f0b1c511     7    0    7    0    0     0    0  (none)
b1086e83c     7    0    7    0    0     0    0  (none)
5256e46e6     7    0    7    0    0     0    0  (none)
07510169e     8    0    8    0    1     1    0  (none)
251e30650     8    0    8    0    1     1    0  (none)
9b1ca70b6     8    0    8    0    0     0    0  (none)
d862dd454     8    0    8    0    0     0    0  (none)
6abcf1c5b     9    0    9    0    1     1    0  (none)
9b008793c     9    0    9    0    1     1    0  (none)
dc913b3c7     9    0    9    0    1     1    0  (none)
0b72ea205     9    0    9    0    1     1    0  (none)
ee20c9488     9    0    9    0    1     1    0  (none)
20d576308     9    0    9    0    1     1    0  (none)
a824d54b9     9    0    9    0    1     1    0  (none)
6de45e92f     9    0    9    0    1     1    0  (none)
5c391d9e9     9    0    9    0    0     0    0  (none)
56f69002f     9    1    8    0    0     0    0  (none)
46dafe082    10    0   10    0    1     1    0  (none)
e119e752f    10    0   10    0    0     0    0  (none)
09477ee86    10    0   10    0    0     0    0  (none)
0b149b91c     9    0    9    0    0     0    0  (none)
cca19bed8     9    0    9    0    0     0    0  (none)
e9702ffa5     9    0    9    0    0     0    0  (none)
3d7a82f38    12    0   12    0    0     0    0  (none)
3aad1a38e    12    0   12    0    0     0    0  (none)
ffd36c7d6    13    1   12    0    1     1    0  (none)
401689e2e    13    1   12    0    1     1    0  (none)
0256438e7    13    1   12    0    1     1    0  (none)
3a5dbe938    13    1   12    0    1     1    0  (none)
2eb2d2af3    15    2   13    0    1     1    0  (none)
ac4b36c14    16    2   13    1    0     0    0  (none)
39874036a    17    2   14    1    0     0    0  (none)
6de1b4a11    18    3   14    1    1     1    0  (none)
1cddd76af    18    3   14    1    1     1    0  (none)
8986e643d    18    3   14    1    1     1    0  (none)
4c29b982b    18    3   14    1    1     1    0  (none)
2945f5e81    19    4   14    1    2     2    0  (none)
32aa9a89b    19    4   14    1    2     2    0  (none)
d9eb3b3fc    20    4   15    1    3     3    0  (none)
39c3e2ec7    20    4   15    1    3     3    0  (none)
ad58d8f41    20    4   15    1    2     2    0  (none)
1985471dd    21    4   15    2    2     1    1  REVIEW-R20.md
b7de85314    21    4   15    2    1     0    1  REVIEW-R20.md
6e56d21f5    22    6   14    2    1     0    1  REVIEW-CHECKLIST.md
db90e18cf    22    6   14    2    1     0    1  REVIEW-CHECKLIST.md
fa94f77ef    21    5   15    1    0     0    0  (none)
c5520273f    21    5   15    1    0     0    0  (none)
73dd71747    21    6   14    1    0     0    0  (none)
80463a540    22    6   14    2    1     0    1  REVIEW-R21.md
831018f3d    22    6   14    2    1     0    1  REVIEW-R21.md
7b4b59877    22    6   14    2    1     0    1  REVIEW-R21.md
ed8bc60c3    23    6   15    2    2     1    1  REVIEW-R21.md
43fca5f0b    25    6   17    2    3     2    1  REVIEW-R21.md
d2159e711    25    6   17    2    3     2    1  REVIEW-R21.md
a52af14d8    26    7   18    1    4     4    0  (none)

ROWS: 110
A ZERO IN THE 'LOST' COLUMN ON EVERY ROW WOULD BE THE SPLIT'S CASE.
A NONZERO ROW IS A DETECTION THE SPLIT WOULD HAVE SWALLOWED.

DISTINCT NAMES EVER LOST TO THE SPLIT: 3
  REVIEW-CHECKLIST.md
    lost on 2 commit(s), first 6e56d21f5, last db90e18cf
    ever added to the repo? NO - NEVER EXISTED
  REVIEW-R20.md
    lost on 2 commit(s), first 1985471dd, last b7de85314
    ever added to the repo? YES: 1237de0 REVIEW-R20: 2 High (both closed at 65fabe4 while I ran), 3 Medium, 3 Low, 3 nits
  REVIEW-R21.md
    lost on 6 commit(s), first 80463a540, last d2159e711
    ever added to the repo? YES: 1045edb REVIEW-R21: 2 High, 3 Medium, 3 Low, 4 nits over c749334..80463a5
```

---

## What the history says

**110 first-parent commits. 10 of them carry a nonzero `LOST`. Three
distinct names have ever been lost to the split, and they do not divide
the way today's snapshot suggests.**

| name | ever tracked? | what the split costs |
|---|---|---|
| `REVIEW-R20.md` | YES, at `1237de0` | DELAY - the report arrived, the gate would have caught it late |
| `REVIEW-R21.md` | YES, at `1045edb` | DELAY - same |
| `REVIEW-CHECKLIST.md` | **NO - never existed anywhere** | **PERMANENT LOSS** |

`REVIEW-CHECKLIST.md` is the phantom. It is a real bare-only citation in
real brief prose, not an artefact of my scan:

    $ git show 6e56d21f5:docs/briefs/BRIEF-199-ratchet-defects.md | grep -n 'REVIEW-CHECKLIST'
    66:A human cleared it three times tonight - `REVIEW-CHECKLIST.md`,

    $ git show 6e56d21f5:docs/briefs/BRIEF-199-ratchet-defects.md \
        | grep -c 'docs/reviews/REVIEW-CHECKLIST.md'
    0

It is cited bare, it is cited nowhere with a path, and it names a report
that has never existed in this repository in any commit on any ref. **It is
exactly the class the ruling's refusal names**, and it is on the board
twice (`6e56d21f5`, `db90e18cf`) rather than zero times.

**So the answer to R21's open question is: once, out of 110 commits.** Not
never, and not often. Whether one permanent loss in 110 commits justifies
keeping a false positive that costs a sentence is the ruling, and it is
not mine.

**Two things the numbers do NOT say, stated because the shape invites
them.** First, the split's cost is not "3 detections": two of the three are
delays, not losses, and a delayed detection still fires. Second, `LOST 0`
at both snapshots is a real result and not a refutation of the residual -
the residual is rare by construction, and a rare hazard is invisible to any
single-revision measurement, which is why R21 was right to refuse to settle
it on today's tree.

---

## THE INSTRUMENT FAILED FIRST, IN THE EXACT WAY ITS SUBJECT DOCUMENTS

My first history run printed this:

      REVIEW-CHECKLIST.md
        ever added to the repo? YES: 1b7975b B101: the reviewer checklist, ...

**That is the false answer, and it inverted the headline** - it made all
three names look like mere delays and the split look free over the whole
history. The query behind it was:

    git log --oneline --all --diff-filter=A -- "*REVIEW-CHECKLIST.md"

`*REVIEW-CHECKLIST.md` has a free left edge and matched
`docs/CODE-REVIEW-CHECKLIST.md`, which does exist:

    $ git log --all --diff-filter=A --name-only --format='%h' -- '*REVIEW-CHECKLIST.md' | grep '\.md$'
    docs/CODE-REVIEW-CHECKLIST.md

This is the SAME defect that `check-brief-report-references.py:118-130`
records as a published error - a pattern with a free left edge matching the
tail of a longer name, `docs/CODE-REVIEW-CHECKLIST.md` read as
`REVIEW-CHECKLIST.md`. The probe written to audit that ruling reproduced
the defect the ruling's own file is built around, forty lines below the
warning. I did not notice it from reading; I noticed it because the answer
was too clean.

**The fix, and both controls:**

    # NEGATIVE - the phantom, anchored at a directory boundary
    $ git log --oneline --all --diff-filter=A -- ':(glob)**/REVIEW-CHECKLIST.md' | wc -l
    0

    # POSITIVE - a real report, same anchored form, still found
    $ git log --oneline --all --diff-filter=A -- ':(glob)**/REVIEW-R20.md'
    1237de0 REVIEW-R20: 2 High (both closed at 65fabe4 while I ran), ...

The negative alone would have been satisfied by a pathspec matching
nothing at all, which is why the positive is there.

---

## A NOTE THAT BELONGS TO #211 AND CHANGES WHAT #213 IS

The syntax-split bullet **does not appear in either parent of the merge
that introduced it.** It was written during a merge resolution:

    $ git log -1 --format='%P' 73dd717
    4be53560bc64c80ff397759889de1e7648101deb 6f921f856fb641e715780b7a86b9a2a721324a99

    $ git show 4be5356:docs/reviews/check-brief-report-references.py | grep -c 'A syntax split'
    0
    $ git show 6f921f8:docs/reviews/check-brief-report-references.py | grep -c 'A syntax split'
    0
    $ git show 73dd717:docs/reviews/check-brief-report-references.py | grep -n 'A syntax split'
    69:- **A syntax split**, counting only path-qualified forms as citations

**The backwards reasoning R21-M3 found entered the repository inside a
merge resolution, in text no branch diff ever showed as an addition and no
reviewer saw before it landed.** That is not a second defect in the ruling;
it is the answer to how the first one got in. The full argument, and the
measurement refuting R21's claim that no merge in the range invented a
third version, is in
`docs/reviews/WORKLOG-213-record-and-counterfactual.md`.
