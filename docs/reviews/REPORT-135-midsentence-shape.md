# REPORT #135 - the mid-sentence citation shape, measured; and the enrichment premise, tested

Measured 2026-09-01 on `review/midsentence-shape`, cut from `main` at
`d862dd4`, in a worktree at `/home/plafayette/claude_projects/fmj-worktrees/midsentence-shape`.
Design read at the freeze: `docs/DESIGN-FREEZE.txt` -> `5d17cd7`, 2133 lines,
never from the working tree.

**Nothing was fixed and nothing was wired.** No citation moved, on this
branch or any other. The detector is named `probe-` on purpose.

---

## THE HEADLINE, both jobs

| | |
|---|---|
| container | **881** citation sites, 165 tracked `.py`/`.sh` files |
| **mid-sentence backlog** | **320** sites (**36.3%**) - not ~90 |
| of those, multi-line | 233 |
| of those, single-line | 87 |
| enrichment: blank-ended | **4 / 47 = 8.5%** wrong |
| enrichment: complement | **2 / 57 = 3.5%** wrong (seeds 134 and 135) |
| Fisher exact, two-sided | **p = 0.41 - too small to separate** |

**Two things in this report correct the team lead, and one corrects
REPORT #134.** They are stated in the two sections headed *"This
corrects the brief"* and *"This corrects #134"*.

---

# JOB 1 - the backlog

## The number is 320, and the guess was low by 3.5x

`docs/reviews/probe-midsentence-shape.py`, run against `5d17cd7`:

```
container: 881 citation sites, 165 tracked files
design:    5d17cd7, 2133 lines

320 site(s) start or end mid-sentence (36.3% of 881)
   233  multi-line ranges
    87  single-line citations (a line inside a paragraph rarely does either)

   235  end:mid-sentence
   178  start:mid-sentence
```

`235 + 178 = 413` verdicts over 320 sites, so **93 sites are cut at
both ends.** Split by range width:

|  | start only | end only | both | total |
|---|---|---|---|---|
| multi-line | 72 | 98 | 63 | **233** |
| single-line | 13 | 44 | 30 | **87** |
| **total** | **85** | **142** | **93** | **320** |

**Zero `start:blank` and zero `end:blank`.** The probe reports those
too - the mid-sentence shape is a strict superset of both - and the
count being zero is exactly what `check-design-citation-shape.py`
exiting 0 on this tree should mean. It is the cheapest available
cross-check that the two selectors agree, and they do.

## This corrects the brief: 4/40 -> ~90 was not a low estimate, it was a different measurement

BRIEF #135 says *"`4/40` extrapolates to roughly 90 sites, but that
number is a guess and the first thing to replace with a real one."*
The real number is **320**. But the gap is not sampling error, and
calling it that would hide the real lesson:

**The `4` in #134's `4/40` was a human aesthetic judgement, not this
rule.** Running the probe over #134's exact forty sites - redrawn at
seed 134 and verified **byte-identical** to the table in
`REPORT-134-citation-rate.md` - flags **13 of 40 (32.5%)**, against a
corpus rate of 36.3%. The sample and the corpus agree with each other
to well within noise. What disagrees is the *reader*: #134 wrote up 4
of those 13 because those four struck a careful human as worth
mentioning. The other 9 are the same shape and went unremarked.

So `4/40 -> ~90` was never an under-estimate of the mechanical rule; it
was a faithful extrapolation of *a different, narrower, unstated
rule*. **A rule and the human judgement that inspired it are not the
same population, and this is the second time on this project that an
extrapolation has silently changed containers between numerator and
denominator** - #134's own report caught the first.

I read all 13 by hand against the freeze. **Every one is a genuine
mid-sentence boundary; I found no false positive in the 13.** Nine
examples that #134 read and scored `CORRECT` without noting the shape:

| site | cited | what the boundary does |
|---|---|---|
| `scripts/check-u7-resilience-controls.sh:339` | `366-370` | 370 ends *"plus a `retry_after`"*; *"hint."* is at 371 |
| `src/fast_mcp_jobvite/models/jobs.py:62` | `811-817` | 817 ends *"delimiter tokens occurring inside"*; completes at 818 |
| `src/fast_mcp_jobvite/utils/redaction.py:594` | `821` | one line inside a paragraph, cut at both ends |
| `tests/conftest.py:11` | `1339-1341` | 1341 ends *"converts each synthetic fixture to a recorded one"*; *"when a key lands"* is 1342 |
| `tests/test_audit.py:532` | `788-790` | 790 ends *"not to the audit stream that"*; completes at 791 |
| `tests/test_file_type_gate.py:412` | `1720-1721` | 1720 opens *"magic-number sniffing,"*, mid-list-sentence from 1719 |
| `tests/test_jobvite_client.py:947` | `312` | ends *"**A URL containing a secret is never"*; *"constructed**"* is 313 |
| `tests/test_repo_hygiene.py:134` | `1353` | ends *"- asserted"*; completes at 1354 |
| `tests/test_shutdown.py:301` | `1088-1096` | cut at both ends: opens mid-`finally` sentence, ends *"against a"* |

All four of #134's N1-N4 are in the 13, so the probe is a **superset of
the class the report raised it from**. It is not a superset of #134's
*reasoning*: N3 (`tests/test_tools_candidates.py:1151`, `990-1007`) is
flagged only at its END. #134 also objected to its START - line 990,
*"pydantic-settings enforces them."*, is a complete sentence that
happens to be the TAIL of the previous paragraph. **The probe cannot
see paragraph membership, only sentence boundaries**, so it
under-detects that shape. That is the clearest known blind spot and it
is in the docstring.

## Per-file distribution (66 of 165 files carry at least one)

```
    28  src/fast_mcp_jobvite/services/jobvite_client.py
    17  tests/test_pagination.py
    17  tests/test_tools_jobs.py
    16  src/fast_mcp_jobvite/config.py
    15  tests/test_tools_job_feed.py
    12  tests/test_resilience.py
    11  src/fast_mcp_jobvite/tools/jobs.py
    10  tests/test_approval_write.py
     9  scripts/check-u5-jobs-amputation.sh
     9  src/fast_mcp_jobvite/audit.py
     8  scripts/check-u6-paging-controls.sh
     8  src/fast_mcp_jobvite/http_hardening.py
     8  tests/test_audit.py
     7  scripts/check_advisories.py
     7  src/fast_mcp_jobvite/server.py
     7  src/fast_mcp_jobvite/tools/candidates.py
     6  scripts/probe-breaker-call-path.py
     6  src/fast_mcp_jobvite/__main__.py
     6  src/fast_mcp_jobvite/utils/redaction.py
     6  tests/test_config.py
     6  tests/test_tools_candidates.py
```

The tail (45 more files, 1-5 each) is in the probe's own output; it is
not copied here, because a hand-copied tail is a second place for the
number to decay.

**`165` is the count with this branch's two new files tracked; the
pre-commit run said `163`.** The 881 SITES are unchanged either way,
which is the number every rate here divides by - `sample-135-complement.py`
carries no `DESIGN.md:N` citation, and `probe-midsentence-shape.py`'s
one is marker-exempted.

**The distribution is not concentrated, and that matters for the sweep
decision.** No file holds more than 9% of the backlog, and 66 files are
involved. There is no cheap 80/20 subset.

**A repeated range is repeated work only once.** `scripts/check-u5-jobs-amputation.sh`
cites `DESIGN.md:786-788` at four separate sites (`:216`, `:237`,
`:266`, `:287`); one decision fixes four. I did not compute the
distinct-range count, and it is on the *did not verify* list.

## First 15 multi-line instances, with the boundary lines

Verbatim from the run (`--limit 15`, path order):

```
  scripts/adr-batch-repoint.py:32  DESIGN.md:12-34  start:mid-sentence
      first  12| that this document is correct. Three carried risks are recorded rather than
      last   34| | `CONFORMANCE-B1-B106.md` | 42 satisfied / 22 partial / 37 unaddressed |
  scripts/check-committed-file-types.py:29  DESIGN.md:1720-1721  start:mid-sentence
      first  1720|   magic-number sniffing, NUL-byte backstop, fail-closed, overrides only via
      last   1721|   the same commit so the exception is reviewable in the diff.
  scripts/check-u0-test-controls.sh:12  DESIGN.md:1564-1569  start:mid-sentence
      first  1564| properties" and "eight positive controls". Both numbers were wrong when writ
      last   1569| the sweep can be pointed at a reverted gate and made to report holes.
  scripts/check-u10-write-amputation.sh:217  DESIGN.md:1199-1203  start:mid-sentence
      first  1199| eras that have been measured; a third case exists - `protocol_version` absen
      last   1203| learns that approval could not be established from a log line, not from a ca
  scripts/check-u10-write-controls.sh:174  DESIGN.md:1195-1198  start:mid-sentence, end:mid-sentence
      first  1195| **populated on both** despite one era being called sessionless. `ctx._is_mod
      last   1198| **An unrecognised protocol version refuses the write.** The discriminator is
  scripts/check-u10-write-controls.sh:195  DESIGN.md:1199-1203  start:mid-sentence
  scripts/check-u10-write-controls.sh:342  DESIGN.md:1471-1474  start:mid-sentence
      first  1471|    tool again after a timeout, or a user approving twice. The `409` shape is
      last   1474|    solved one: we can report a duplicate, not prevent it.
  scripts/check-u12-jobfeed-amputation.sh:325  DESIGN.md:990-1007  end:mid-sentence
      first  990| pydantic-settings enforces them.
      last   1007| §8 states that configuration and carries a required case asserting it, so th
  scripts/check-u12-jobfeed-controls.sh:311  DESIGN.md:315-316  end:mid-sentence
      first  315| `GET /v1/jobFeed` is the exception: it structurally requires `api`, `sc` and
      last   316| parameters. Its URL is classified sensitive - never logged whole, never in a
  scripts/check-u3-audit-amputation.sh:226  DESIGN.md:790-791  start:mid-sentence, end:mid-sentence
      first  790|   emailed.** The audit hole is the lesser harm. **The warning goes to stderr
      last   791|   just failed** - routing it down the channel whose failure it reports is ho
  scripts/check-u3-audit-controls.sh:188  DESIGN.md:657-666  start:mid-sentence
      first  657| problem object's `request_id` and inside its `instance` URN. Where the HTTP
      last   666| a `finally` so an id cannot leak into the next invocation on a reused worker
  scripts/check-u5-jobs-amputation.sh:216  DESIGN.md:786-788  end:mid-sentence
      first  786| - **On a read tool:** log to stderr and continue. A read is recoverable and
      last   788| - **After a successful write:** return **success with a warning**, never an
  scripts/check-u5-jobs-amputation.sh:237  DESIGN.md:786-788  (same range)
  scripts/check-u5-jobs-amputation.sh:266  DESIGN.md:786-788  (same range)
  scripts/check-u5-jobs-amputation.sh:287  DESIGN.md:786-788  (same range)
```

`scripts/adr-batch-repoint.py:32` citing `12-34` is worth a second
look by whoever sweeps: a 23-line range spanning prose into a table is
not a paragraph, and it starts mid-sentence at 12.

## What "sentence" means here, and where the definition is doing questionable work

The brief asked for this rather than a clean number over an
uninspected rule. The decision is **structural**, not grammatical: a
line begins a sentence if it opens a block or its predecessor is blank,
a block, or ends in `.!?:;` (trailing `` ` ``, `"`, `'`, `)`, `]`, `*`,
`_` stripped first); it ends one under the mirror rule.

`probe-midsentence-shape.py --edges` prints what that does at the five
edges the brief names, on real lines of the frozen design:

```
  abbreviation ending a line        NO INSTANCE in the frozen design
  code span ending a line           DESIGN.md:303  kind=text  begins=True  ends=False
      No cache module, no bulk module, no custom logging module. Framework middleware and `log
  colon ending a line               DESIGN.md:12  kind=text  begins=False  ends=True
      that this document is correct. Three carried risks are recorded rather than resolved:
  a list item                       DESIGN.md:14  kind=list  begins=True  ends=False
      - **§8's SIGTERM case is the one required case whose deletion the gate provably cannot s
  a heading                         DESIGN.md:1  kind=heading  begins=True  ends=True
      # fast-mcp-jobvite - Design
  a table row                       DESIGN.md:28  kind=table  begins=True  ends=True
      | Round | Result |
  a line ending in a comma          DESIGN.md:9  kind=text  begins=True  ends=False
```

Read that as five separate answers:

- **Abbreviations: the leniency exists but never fires here.** `e.g.`,
  `i.e.`, `cf.`, `etc.` at end-of-line would be read as terminators and
  the break would go unreported. **There is no such line in the frozen
  design**, so this blind spot contributes exactly zero to the 320
  today. It would start contributing the day someone writes one.
- **Code spans: handled correctly.** `DESIGN.md:303` ends in
  `` `log `` mid-span and is correctly `ends=False`. The decoration
  strip does not swallow a real terminator either - `**done.**` reads
  as terminated.
- **Colons: deliberately LENIENT and this is the weakest rule.**
  `DESIGN.md:12` ends in `:` introducing a list, so `ends=True` is
  right. A mid-clause colon would also read as terminated and go
  unreported. This makes 320 a **lower bound**, which is the direction
  a backlog count should err in.
- **Headings and table rows: treated as self-contained blocks**, so a
  range that starts or ends on one is never flagged. `DESIGN.md:12-34`
  above is flagged for its START only, never for ending on the table
  row at 34.
- **List items: `begins=True`, `ends` only if punctuated or followed by
  a new block.** `DESIGN.md:14` correctly reads `ends=False` because
  its continuation line follows. This is why `786-788` above is flagged
  at its end: 788 opens a bullet whose second line is 789.

**The single-line class is the most arguable 87 of the 320.** A
single-line citation of a line inside a paragraph almost never both
begins and ends a sentence, so the rule flags it nearly by
construction. `check-design-citation-shape.py`'s ends-blank branch
deliberately excludes single-line ranges (`end > start` is called
load-bearing in its own comment); this probe does not, and the summary
splits the two counts so a sweep can decide the classes separately.
**One of the two real defects Job 2 found is a single-line citation**
(`DESIGN.md:1145`), so the class is not empty of substance.

## 7/7 controls, including two negative arms

```
  CONTROL starts mid-sentence (6-7) -> FIRED (start:mid-sentence)
  CONTROL ends mid-sentence (5-6) -> FIRED (end:mid-sentence)
  CONTROL starts blank (2-4) -> FIRED (start:blank, end:blank)
  CONTROL ends blank (1-2) -> FIRED (end:blank)
  CONTROL out of bounds (2142) -> FIRED (out of bounds (not this probe's shape))
  CONTROL a whole paragraph (5-7) -> FIRED (no finding, as required)
  CONTROL a heading alone (1) -> FIRED (no finding, as required)

7/7 controls fired.
```

The two negative arms are the load-bearing half: without them, a
`classify` that returns a finding for everything passes all five
positive arms. All seven line numbers are **searched for** in the
frozen design at run time, never typed in, so re-freezing the design
does not silently kill an arm.

**My first version of the controls was broken and printed 6/7.** It
drew the paragraph's first line, an interior line and its last line by
three independent searches, which produced the range `6-3` - inverted,
scored `out of bounds`, and made the starts-mid-sentence arm look dead.
They are now drawn from ONE paragraph by a single helper. Recorded
because the failure looked exactly like a dead branch and was not.

---

# JOB 2 - the enrichment hypothesis

## This corrects #134, and it corrects the brief in the other direction

**BRIEF #134's independence premise is not refuted by this
measurement, and REPORT #134's case against it is not confirmed
either.** The honest answer is *too small to separate*, and it is worth
saying which way the point estimates lean: **they lean #134's way, at
about 2.4x, on a difference that is nowhere near significant.**

## The two populations, both defined on ONE tree

Both arms are measured at `26973a4^` (`0751016`), the commit before
#126 swept the blank-ended citations. That is the only tree on which
both populations exist: after `26973a4` the blank-ended 47 are
repaired, so the complement cannot be defined by subtraction.
`docs/DESIGN-FREEZE.txt` reads **`5d17cd7` at `26973a4^` and at `main`
alike**, so both arms are judged against the same design and against
the same design #134 used.

`docs/reviews/sample-135-complement.py`, seed **135**, n **20**:

```
rev:        26973a4^ (0751016)
design:     5d17cd7, 2133 lines
container:  882 citation sites
blank-END:  47  <- #126's population, 2 of them WRONG
complement: 835
seed: 135   n: 20
```

**`47` is a positive control on the split.** The reconstruction is
independent of #126's worklog and reproduces its measured number
exactly. If the reconstruction had been wrong, this is where it would
have shown.

## The rubric, stated before the numbers, and applied to BOTH arms

A citation is **WRONG** when the cited range does not contain the claim
the citing site makes. That covers three shapes this project has
already ruled on:

1. the range lands on an unrelated paragraph (#126 F3, #133);
2. the site makes a **two-part claim** and the range holds one part
   (#126 F1, #132 - *"the comment made a TWO-PART claim and the range
   held only half of it"*);
3. the site **quotes** text that extends outside the range (#126 F4).

Anything else - including a range that is boundary-sloppy but whose
claim is fully inside it - is **CORRECT**. This is #134's rubric: its
two positive controls PC-1 and PC-2 are both shape 2, and it scored
both WRONG.

## The numerator on the blank-ended arm is 4, not 2

**#134 cites #126's rate as `2/47`.** Under the rubric above it is
**`4/47`**, because `WORKLOG-126-blank-end-sweep.md` records four
wrong citations, not two - it merely handled them differently:

| | site | why it is wrong under the rubric |
|---|---|---|
| F1 | `config.py:67` cites `207-212` | shape 2 - `JOBVITE_ENABLE_WRITES` is at 227 |
| F2 | `test_tools_jobs.py:312` cites `692-697` | shapes 1+2 - the next paragraph, states none of the error half |
| F3 | `test_http_hardening.py:506` cites `906-907` | shape 1 - 906 is an unrelated sentence; the claim is 908-910 |
| F4 | `redaction.py:149` cites `1143-1144` | shape 3 - the quoted sentence is 1142-1143 |

F1 and F2 were *reported, not repointed*; F3 and F4 were *repointed,
loudly*. **`2` is the count of the ones left open, not the count of the
ones that were wrong.** Both #134 and BRIEF #134 propagated `2/47` as
the wrong-citation rate. Using it as the numerator would have
understated the blank-ended arm by half in a comparison whose whole
point is that arm's height.

**Caveat, and it cuts against my own numerator.** #126 was a SHAPE
sweep, not a claim-by-claim audit: it made 19 end-line decisions over
the 47 and found these four while doing so. Whether a systematic
claim-audit of all 47 would find more than four is unknown, so `4/47`
is a **lower bound** on the blank-ended arm. That direction makes the
enrichment case stronger, not weaker, and it is the single biggest
weakness in this comparison.

## The complement arm: 2 wrong in 20, and 0 wrong in #134's 39

I read all 20 drawn sites against the freeze, claim by claim. **18
CORRECT, 2 WRONG.** Both are recorded below with a suggested fix, per
the standing rule that every finding ships one.

### J2-1 (WRONG, shape 2) - `tests/test_resilience.py:1093` cites `DESIGN.md:674-676`

The test is named
`test_every_breaker_transition_is_logged_with_direction_and_counter`
and asserts both halves: `"failure_count" in line` for every transition
line, and `opened_line["failure_count"] == DEFAULT_BREAKER_FAILURE_THRESHOLD`.

The cited range ends at 676, *"...every breaker transition logs the
direction"*. **The counter half is on 677**, outside the range:
*"(`closed->open`, `open->half_open`, `half_open->closed`) and the
counter that triggered it."*

This is #132 exactly: a two-part claim whose range holds one part.

**Suggested fix:** `DESIGN.md:674-677`.

### J2-2 (WRONG, shape 3) - `src/fast_mcp_jobvite/utils/redaction.py:156` cites `DESIGN.md:1145`

The comment reads *"**There is no tension with DESIGN.md:1145, and
reading half of it manufactured one.** That line says `send_email` "is
also an argument like any other and is subject to §2.1's schema rules;
it defaults to `false` (§2.2)""*.

Line 1145 ends at *"...it defaults"*. **`to `false` (§2.2)` is line
1146.** The quoted sentence is not contained in the cited line.

**This is a comment whose entire subject is that reading half a
sentence manufactures a false conflict, and its own citation names half
the sentence.** Task #82 ruled on this exact tension (*"the tension
dissolves on reading DESIGN.md:1072's full sentence"* - the same
sentence at its pre-re-freeze number). The comment survived a
renumbering with its argument intact and its range one line short.

**Suggested fix:** `DESIGN.md:1145-1146`.

### #134's 39, reused as complement data

**Exactly one of #134's 40 came from the blank-ended population.**
Measured, not assumed: `git blame` at `9b1ca70` attributes
`tests/test_fixture_path.py:16` to `26973a4` and no other of the forty.
So #134's read is **0 wrong in 39 complement sites** under the same
rubric.

**Two of my 20 overlap #134's 40** (`scripts/check_advisories.py:243`
citing `1604-1605`, and `src/fast_mcp_jobvite/models/jobs.py:62` citing
`811-817`). Both were scored `CORRECT` independently by both readers.
Pooling by union, not by sum: **57 distinct complement sites, 2 wrong.**

## The comparison, and why it settles nothing

| population | wrong | read | rate |
|---|---|---|---|
| blank-ended (#126) | 4 | 47 | **8.5%** |
| complement (seeds 134 + 135) | 2 | 57 | **3.5%** |

    Fisher exact, two-sided:  p = 0.4059

**Not significant, and not close.** The point estimates lean toward
enrichment by a factor of about 2.4, which is the direction REPORT #134
argued for, but 4-versus-2 events cannot carry that conclusion. Two
alternative framings, so the sensitivity to my own choices is visible:

| framing | comparison | p |
|---|---|---|
| my rubric, all data | 4/47 vs 2/57 | 0.41 |
| #134's data alone | 4/47 vs 0/39 | 0.12 |
| #134's `2/47` numerator | 2/47 vs 2/57 | 1.00 |

**Every framing fails to reach significance, and one of them - the
numerator #134 and the brief both used - shows literally no difference
at all.** The conclusion does not depend on which I pick, which is the
only reassuring thing about the table.

## The result I did not expect: reader variance is as large as the effect

**I found 2 in 20 where #134 found 0 in 39, and we were applying the
same rubric.** Fisher two-sided on that disagreement alone gives
**p = 0.111** - a difference between two READERS of the same corpus
that is *stronger* than the difference between the two POPULATIONS this
task set out to measure.

I cannot tell from here whether #134 read more leniently, whether my
two are over-called, or whether it is the ordinary luck of 20 draws.
But it means **the enrichment question cannot be settled by adding more
hand reads from a single reader.** Two readers on the same sample,
scored blind, would be worth more than another forty sites read once.

## The premise, answered directly

The brief asked me to say plainly whether its premise was wrong.

**BRIEF #134's premise - that blank-ending and wrong-paragraph are
independent - is not refuted.** REPORT #134's counter-argument is
plausible, its mechanism is real, and the point estimates lean its way;
but at these sample sizes the data does not distinguish it from chance,
and **REPORT #134 was more confident than its own evidence supported**
when it wrote *"I do not think they are independent, and the 0/40 is
evidence"*. `0/40` on a population whose rate is around 3.5% is the
single most likely outcome under either hypothesis.

**What IS refuted, and this is the load-bearing correction: the `2/47`
figure both #134 and BRIEF #134 propagated is not what #126 measured.**
It is 4. The projection *"2/47 -> ~35 wrong ones"* was built on a
numerator that had been halved in transit by counting the findings left
open rather than the findings found.

**The corrected projection.** From the complement rate, which is the
right base rate whether or not enrichment is real:

    881 x 2/57 = ~31 wrong citations corpus-wide

against #126's-rate-as-base-rate of `881 x 4/47 = ~75`. The `~35`
figure survives roughly intact by arithmetic accident - a doubled
numerator and a lower complement rate pulling in opposite directions -
and that coincidence is exactly the kind of thing that keeps a wrong
number alive.

## The mid-sentence shape IS enriched among known-wrong citations

This is the one place Job 1 and Job 2 meet, and it is the strongest
single result here. Six citations on this project are *known* wrong -
#126's F1-F4 plus this report's J2-1 and J2-2. Run both detectors over
their **pre-fix** ranges:

```
#126 F1 / #132  config.py:67                 207-212    probe=CLEAN                            existing=CLEAN
#126 F2 / #133  test_tools_jobs.py:312       692-697    probe=start:mid-sentence               existing=CLEAN
#126 F3         test_http_hardening.py:506   906-907    probe=start:mid-sentence, end:blank    existing=ends on a BLANK line
#126 F4         redaction.py:149             1143-1144  probe=start:mid-sentence, end:blank    existing=ends on a BLANK line
#135 J2-1       test_resilience.py:1093      674-676    probe=end:mid-sentence                 existing=CLEAN
#135 J2-2       redaction.py:156             1145-1145  probe=end:mid-sentence                 existing=CLEAN

5/6 known-wrong citations carry the mid-sentence shape
```

**The existing checker sees 2 of 6. The probe sees 5 of 6.** Against a
corpus base rate of 320/881 = 36.3%, seeing 5 or more of 6 by chance
has probability **0.0265**. Small n, one-sided, and the six are not an
independent sample of wrong citations - four of them were *found by* a
blank-end sweep, so they are enriched for shapes near a blank line by
construction. J2-1 and J2-2 are not, and both are flagged. Take it as
suggestive, not settled.

**The one miss is instructive.** `207-212` (#126 F1 / #132) is clean at
both ends: a well-formed range that simply stops before the paragraph
carrying the second half of its claim. **No structural detector can
find that shape.** It needs a reader who knows the claim, which is what
`check-design-citation-shape.py`'s docstring has said from the first
line all along.

---

# My recommendation on whether a sweep is justified

**No full sweep, and no wiring - but the ordering the project keeps
using is now the wrong tool for this backlog, and I would say so before
another task is written on the assumption that it is.**

1. **320 is not a backlog you can drive to zero and then wire.** #125's
   discipline (measure, fix, wire) assumes a backlog you can clear.
   `4/47`-scale backlogs clear; a 36%-of-everything backlog is a
   **housekeeping rule**, not a defect list. 320 range decisions, each
   a correctness judgement per #126 F3's standing proof that the
   mechanical fix can be wrong, is far more work than the ~20-31
   genuinely wrong citations it is meant to protect.
2. **If anything gets wired, wire it for NEW citations only.** A
   diff-scoped gate - flag a mid-sentence range in the lines a commit
   ADDS - lands green on day one, costs one decision per new citation,
   and stops the population growing. The 320 existing sites then decay
   as files are touched. This is the only version of a gate I would
   recommend today, and it is not what the task describes.
3. **The high-value subset is not the mid-sentence class, it is the
   two-part-claim class**, which is 2 of the 6 known instances (F1,
   J2-1) plus #132, and which **no structural detector can see at all**.
   Every one was found by a human reading a claim against its range.
4. **Do fix the two Job 2 findings.** `674-677` and `1145-1146` are
   both one-line widenings whose correctness I have argued above; they
   are cheap and they are real. That is a #126-style targeted fix, not
   a sweep.
5. **If the enrichment question matters enough to spend another
   session, spend it on two readers over one sample, not one reader
   over two samples.** The reader-variance result above says the
   instrument is noisier than the effect.

---

# Gates, each exit code read on its own line

Run from `/home/plafayette/claude_projects/fmj-worktrees/midsentence-shape`
at the committed tree.

```
uv run --frozen ruff check .                                    0
uv run --frozen ruff format --check .                           0
uv run --frozen mypy                                            0
uv run --frozen python docs/reviews/check-checkers-are-wired.py 0
uv run --frozen python docs/reviews/check-design-citations.py   0
uv run --frozen python docs/reviews/check-design-citation-shape.py          0
uv run --frozen python docs/reviews/check-design-citation-shape.py --controls  0
uv run --frozen python docs/reviews/probe-midsentence-shape.py --controls   0
uv run --frozen python docs/reviews/probe-midsentence-shape.py              0
uv run --frozen python docs/reviews/sample-135-complement.py                0
```

The four gates the brief names are the first four. The rest are the
citation gates this branch could plausibly disturb, run to show it did
not: **the container is 881 sites before and after this branch**, which
required marking the probe's own `DESIGN.md:906` record as
`REPOINT-EXEMPT` - it is a record of where a defect WAS, the same
mechanism `check-design-citation-shape.py:33` already uses for
`DESIGN.md:311`. Without the marker this report's own detector would
have counted its own documentation, which is a shape this project has
measured five times.

**The exemption set moved 23 -> 24, and that is the whole move.** My
first commit took it to 25: `sample-135-complement.py`'s docstring
mentioned the marker by name in ordinary prose, which exempted a line
carrying no citation at all. It is reworded. The exemption set is part
of the result on this project, so a silent +1 in it is the same defect
class as a silent +1 anywhere else.

`check-checkers-are-wired.py` exiting 0 is the specific reason both new
files are named `probe-` and `sample-`: a `check-*` file in
`docs/reviews/` enters that checker's container and would have to be
wired into `ci.yml` or carry an exemption, and wiring a gate with a
320-site backlog lands red.

This is not a code review, so it declares no `REVIEW-COVERS` range.

# What I did NOT verify

- **I did not compute the distinct-RANGE count behind the 320 sites.**
  `check-u5-jobs-amputation.sh` alone cites `786-788` four times, so
  the number of *decisions* a sweep faces is materially smaller than
  320 and I do not know by how much. Anyone sizing a sweep should
  compute it first; my recommendation against a full sweep does not
  turn on it, but the cost estimate does.
- **I did not re-audit #126's 47 claim-by-claim.** My `4/47` numerator
  is what #126's shape sweep happened to notice. A systematic audit
  could only raise it, which strengthens the enrichment case I am
  declining to endorse - so this is the assumption most worth attacking.
- **My two Job 2 findings are one reader's calls.** J2-1 (two-part
  claim) follows #132's precedent directly. J2-2 (quote extending past
  the range) follows #126 F4's. Neither is a judgement #134 was asked to
  make on those sites, and I did not have a second reader.
- **I did not read the 18 CORRECT sites to anyone else.** The
  reader-variance section is the honest statement of what that is worth.
- **The single-line class (87 of 320) is unadjudicated as a class.** I
  hand-read three of them (`821`, `312`, `1353`, all CORRECT) and one
  turned out to be a real defect (`1145`). Whether the class is mostly
  noise or mostly the `1145` shape is unmeasured.
- **I did not measure whether the 320 grows.** The diff-scoped gate in
  recommendation 2 is a proposal, not a measurement; I did not count
  how many mid-sentence citations the last N commits ADDED, and that
  number is what would justify it.
- **I did not run `pytest`.** The brief named four gates and pytest is
  not among them; this branch adds no test and touches no source. The
  suite floor is therefore unverified on this branch.
- **Worktree:** `/home/plafayette/claude_projects/fmj-worktrees/midsentence-shape`
  is **left in place**, not removed, because the team lead merges from
  it and the branch is unpushed. Remove it after the merge.
