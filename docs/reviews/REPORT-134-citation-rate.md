# REPORT #134 - the wrong-paragraph citation RATE, measured

Measured 2026-09-01 on `review/citation-rate`, cut from `main` at `9b1ca70`.
Design read at the freeze: `docs/DESIGN-FREEZE.txt` -> `5d17cd7`, 2133 lines,
verified byte-identical to the working tree's `docs/DESIGN.md`.

**Nothing was fixed. This task measures.** No citation moved, on this branch or
any other.

## The headline

| | |
|---|---|
| seed | **134** (`docs/reviews/sample-134-citations.py`, default) |
| container | **881** citation sites in 161 tracked `.py`/`.sh` files |
| drawn | **40** |
| `CORRECT` | **40** |
| `WRONG-PARAGRAPH` | **0** |
| `UNJUDGEABLE` | **0** |
| rate | **0/40** |

**0/40 does not mean the rate is zero, and it does not refute #126's 4%.** It
bounds it. Read the arithmetic section before deciding anything - the honest
summary is that this sample rules out a *large* rate and cannot separate 0%
from 4%.

## The sample was drawn from a container the brief did not name, and why

BRIEF #134 §C.1 says to reuse `check-design-citations.py`'s selector. **That
selector disagrees with the brief's own arithmetic**, measured at `9b1ca70`:

```
docs/reviews/check-design-citations.py         1917 citations, 202 files   (.py .toml .md .yml .yaml .sh)
docs/reviews/check-design-citation-shape.py     881 citations, 161 files   (.py .sh)
```

The brief's §B reasoning - "~880 citations", "two in 47 is ~4%" - is the
**shape** checker's population, and #126's 47 blank-ended sites were drawn from
it too. The extra ~1030 sites are prose: reviews, worklogs and briefs, which
`check-design-citation-shape.py:69-84` excludes by SUFFIX on the stated ground
that a review cites the design *as it stood when it was written* and repointing
one would rewrite history. A `WRONG-PARAGRAPH` verdict on such a site is not a
defect and is not actionable.

Drawing from 1917 would have put the numerator (#132 and #133, both code sites)
and the denominator in different containers, and would have spent roughly half
the forty reads on historical prose that is `UNJUDGEABLE` for a structural
reason rather than a real one.

**So the draw is over the 881 CODE sites - the same container #126 sampled.**
This is still a reuse and not a third selector: `sample-134-citations.py`
imports `code_files()`, `CITE` and the `EXEMPT` skip from
`check-design-citation-shape.py` itself. The team lead was told this before the
forty reads were spent, not after.

**The unit is the SITE, not the distinct range.** A range cited at five sites
is five separate authors' claims and can be right at one and wrong at another;
#133 was two sites sharing one range and both were wrong, which is only
visible if sites are the unit.

**Nothing was drawn on a property a checker already tests.** Not blank-ended,
not near a boundary, not "looks suspicious" - `random.Random(134).sample` over
the whole sorted container. Adding this report's own script to the tree changed
the container by **zero** citations (881 before, 881 after), and the draw is
byte-identical before and after the script was reformatted for lint.

## The instrument was controlled before its zero was believed

A clean zero that explains itself is exactly the result this project has
learned to distrust, so the reading procedure was run against the two citations
already KNOWN to be wrong-paragraph.

**They are not in my population.** `fe237d5` ("Repoint three citations that
RESOLVE and name the wrong paragraph (#132, #133)") is an ancestor of
`9b1ca70`, so every known instance was already repaired before the draw. The
control therefore ran against `fe237d5^`:

- **PC-1 (fires).** `tests/test_tools_jobs.py:312` at `fe237d5^` claimed *"the
  two arms travel by DIFFERENT channels and are different assertions"* and
  cited `DESIGN.md:692-697`. That range is the *"Not a field on the output
  models"* paragraph, which explains why `_meta` rather than a model field and
  states nothing about the error arm's channel. The channel split is at
  `DESIGN.md:681-687`. **Scored `WRONG-PARAGRAPH`.**
- **PC-2 (fires).** `src/fast_mcp_jobvite/config.py:67` at `fe237d5^` claimed
  the write is *"the only one gated by `JOBVITE_ENABLE_WRITES`"* and cited
  `DESIGN.md:207-212` - the §2.2 heading, the no-sandbox sentence and the
  governing-clause line. `JOBVITE_ENABLE_WRITES` first appears at
  `DESIGN.md:227`. **Scored `WRONG-PARAGRAPH`.**
- **The negative arm (does not fire).** Both repaired forms score `CORRECT`:
  `681-687` contains *"The error half is the problem object's own `request_id`
  member ... The success half goes in the result's `_meta`"*, and `207-229`
  reaches the deploy-time gate bullet at 227.

So the procedure detects the class on the only two instances anyone has
confirmed, and does not fire on their repairs. **The zero is a property of the
sample, not of a blind reader.**

## The forty, with verdicts

Every design line below was read from `git show 5d17cd7:docs/DESIGN.md` with
real line numbers attached, never counted inside a window.

| # | site | cited | verdict |
|---|---|---|---|
| 1 | `scripts/check-u10-write-controls.sh:224` | `1148-1151` | CORRECT - the `action AND value` conjunction is verbatim at 1148-1150 |
| 2 | `scripts/check-u10-write-controls.sh:401` | `794-800` | CORRECT - success-with-a-warning's SHAPE, and the retry-emails-a-second-human harm, both at 794-799 |
| 3 | `scripts/check-u5-jobs-amputation.sh:255` | `596-600` | CORRECT - "the only error shape no configuration can distort" at 599 |
| 4 | `scripts/check-u7-resilience-controls.sh:339` | `366-370` | CORRECT - "One circuit breaker for Jobvite. 4xx must not trip it" at 366 |
| 5 | `scripts/check-u8-candidates-amputation.sh:252` | `1434` | CORRECT - "the kind of wart a well-meaning normalisation removes" verbatim |
| 6 | `scripts/check_advisories.py:243` | `1604-1605` | CORRECT, boundary-sloppy - see N1 |
| 7 | `src/fast_mcp_jobvite/config.py:61` | `992-994` | CORRECT - "unset means all **read** tools and never the write" at 993-994 |
| 8 | `src/fast_mcp_jobvite/errors.py:139` | `592-594` | CORRECT - "not discarded - they go in `detail`" verbatim |
| 9 | `src/fast_mcp_jobvite/http_hardening.py:182` | `165` | CORRECT - the `Max total request body size \| 1 MiB` table row |
| 10 | `src/fast_mcp_jobvite/models/__init__.py:1` | `291` | CORRECT - the `models/` layout line |
| 11 | `src/fast_mcp_jobvite/models/candidate.py:314` | `513-515` | CORRECT, boundary-sloppy - see N2 |
| 12 | `src/fast_mcp_jobvite/models/fencing.py:219` | `202-205` | CORRECT - "a test fails when any model field has no fencing decision" at 204 |
| 13 | `src/fast_mcp_jobvite/models/jobs.py:62` | `811-817` | CORRECT - §6.1's attacker-authored definition |
| 14 | `src/fast_mcp_jobvite/services/jobvite_client.py:1417` | `553-560` | CORRECT - the Jobvite-401-reaching-the-caller-as-401 inversion at 557-560 |
| 15 | `src/fast_mcp_jobvite/tools/jobs.py:256` | `1440-1441` | CORRECT - `MockTransport`, verbatim |
| 16 | `src/fast_mcp_jobvite/utils/constraints.py:302` | `181-190` | CORRECT - the what-the-caller-receives paragraph, "the rule still fails closed" at 189 |
| 17 | `src/fast_mcp_jobvite/utils/correlation.py:1` | `661-672` | CORRECT - the `request_id_var` ContextVar paragraphs |
| 18 | `src/fast_mcp_jobvite/utils/normalise.py:20` | `1434` | CORRECT - the quoted phrase is on that line |
| 19 | `src/fast_mcp_jobvite/utils/redaction.py:594` | `821` | CORRECT - "`customField[]` is open-ended" is on 821 |
| 20 | `tests/conftest.py:11` | `1339-1341` | CORRECT - quoted verbatim from 1339-1340 |
| 21 | `tests/test_approval_write.py:1122` | `1806` | CORRECT - C1-T1, "flipping `send_email` to `true`", **High** |
| 22 | `tests/test_arguments_sweep.py:849` | `1370-1371` | CORRECT - "an argument-schema violation failing closed", B12 and B23 |
| 23 | `tests/test_audit.py:532` | `788-790` | CORRECT - "the model would retry, and **a second live human would be emailed**" |
| 24 | `tests/test_config.py:123` | `1010-1011` | CORRECT - the quoted `companyId` sentence, verbatim |
| 25 | `tests/test_file_type_gate.py:412` | `1720-1721` | CORRECT - "an allowlist entry in the same commit so the exception is reviewable in the diff" |
| 26 | `tests/test_fixture_path.py:16` | `1332-1337` | CORRECT - the three tiers, heading and all three bullets |
| 27 | `tests/test_http_hardening.py:292` | `1820` | CORRECT - C2-I1, `include_payloads` flipped to `True` |
| 28 | `tests/test_jobvite_client.py:127` | `344-345` | CORRECT - the invariant, both arms |
| 29 | `tests/test_jobvite_client.py:947` | `312` | CORRECT - "v2 credentials travel as headers, `x-jvi-api` and `x-jvi-sc`" |
| 30 | `tests/test_pagination.py:1` | `471-526` | CORRECT - §4.5 begins at 471 and ends at 526 exactly |
| 31 | `tests/test_repo_hygiene.py:134` | `1353` | CORRECT - "`.env.example` carries no real value" is on 1353 |
| 32 | `tests/test_resilience.py:29` | `362-365` | CORRECT - "Measured: one call, **four rows created**" at 365 |
| 33 | `tests/test_resilience.py:192` | `358` | CORRECT - "Timeouts explicit and per-phase. No SDK default, no single scalar" verbatim |
| 34 | `tests/test_resilience.py:244` | `392-394` | CORRECT - "a total outbound budget ... rather than an unbounded wait" |
| 35 | `tests/test_resilience.py:1143` | `315-318` | CORRECT - the jobFeed URL classified sensitive |
| 36 | `tests/test_shutdown.py:301` | `1088-1096` | CORRECT - "**This must be tested by the side effect**" at 1095-1096 |
| 37 | `tests/test_tools_candidates.py:136` | `1440-1441` | CORRECT - quoted verbatim |
| 38 | `tests/test_tools_candidates.py:1151` | `990-1007` | CORRECT, boundary-sloppy - see N3 |
| 39 | `tests/test_tools_job_feed.py:257` | `315-318` | CORRECT - quoted verbatim from 316-317 |
| 40 | `tests/test_tools_jobs.py:397` | `681-682` | CORRECT, boundary-sloppy - see N4 |

## The near-miss class: 4 of 40 are boundary-sloppy but claim-contained

**None of these is a `WRONG-PARAGRAPH` and none is counted as one.** They are
recorded because they are the population the defect class is drawn FROM: a
range that already starts or ends mid-sentence is one repoint away from losing
its claim entirely, which is precisely what a mechanical `end - 1` did to
`906-907` in #126.

- **N1 - `scripts/check_advisories.py:243` cites `1604-1605`.** Line 1604 is
  the tail of item 3 (*"owner, which is the construction that hides a missing
  mechanism."*); the blanket-ignore claim is item 4, which spans **1605-1606**.
  The range holds the first line of a two-line bullet and one line of an
  unrelated one. **Suggested fix:** `DESIGN.md:1605-1606`.
- **N2 - `src/fast_mcp_jobvite/models/candidate.py:314` cites `513-515`.** The
  worked-example sentence begins at 512 (*"§7.7's own worked example is"*) and
  the literal `showing 50 of 1,240` opens 513. The claim survives; the sentence
  is cut. **Suggested fix:** `DESIGN.md:512-516`.
- **N3 - `tests/test_tools_candidates.py:1151` cites `990-1007`.** It opens on
  *"pydantic-settings enforces them."* - the tail of the previous paragraph -
  and closes mid-sentence at 1007, which completes at 1008. **Suggested fix:**
  `DESIGN.md:992-1008`.
- **N4 - `tests/test_tools_jobs.py:397` cites `681-682`.** 682 ends on *"The
  error half is the problem"*; the sentence completes at 683. The cited claim
  ("requires the id on EVERY result") is fully inside 681-682, so this is
  correct as written - but it is the same file and the same paragraph #133 just
  repointed TO, and it stops five lines short of it. **Suggested fix:**
  `DESIGN.md:681-687`, matching the range #133 landed on.

## The arithmetic, and what 40 does and does not buy

**0 wrong in 40 reads.** Point estimate 0%. The 95% one-sided upper bound is

    1 - 0.05^(1/40) = 7.2%

so **a true rate as high as 7.2% - about 64 wrong citations across 881 - is not
excluded by this sample.** In the other direction:

| if the true rate were | P(seeing 0 in 40) |
|---|---|
| 4.26% (#126's 2/47) | 0.176 |
| 4% | 0.195 |
| 2% | 0.446 |
| 1% | 0.669 |

**A clean 40 is therefore fully compatible with #126's 4%** - it would happen
about one time in five - and this task cannot distinguish 0% from 4%. Saying
otherwise would be the "confidently wrong number" the brief asked me to refuse.

**What it does buy.** Pooling the two reads of the same container - #126's 47
plus this 40 - gives **2 wrong in 87**, a point estimate of 2.3%, or about
**20 of 881**. That is the best estimate available today, and its whole weight
sits on #126's two.

## The premise this result puts pressure on

The brief's argument rests on *"ending blank and citing the wrong paragraph are
INDEPENDENT properties"*, which is what makes #126's 47 an accidental random
sample. **I do not think they are independent, and the 0/40 is evidence.**

Read `WORKLOG-126-blank-end-sweep.md`'s four findings together: F1, F2, F3 and
F4 are all **paragraph-boundary miscounts by the citing author**. A range that
ends on a blank line is a range whose author counted the paragraph break
instead of the paragraph - which is the same error that produces a
wrong-paragraph citation, and is stated as such in
`check-design-citation-shape.py`'s own docstring about the blank-START shape
("the author counted the paragraph break rather than the paragraph").

If that is right, **#126's 47 was an ENRICHED sample, not a neutral one**, its
2/47 overstates the base rate for the other 834, and 0/40 over an unenriched
draw is what you would expect to see. That is a hypothesis, not a measurement -
but it is the reading most consistent with both numbers, and it matters,
because the entire "~35 wrong ones" projection assumes independence.

## My view on whether this justifies a full sweep

**No - not a full 881-site read, and not now.**

- The measured cost is real: forty sites took a full working session of careful
  reading. 881 is roughly twenty times that, and it would be done by a reader
  who has just measured the hit rate at 0.
- The expected yield is ~20 sites (pooled estimate), and the upper bound is ~64.
  Neither is nothing, but every instance found so far has been **harmless in
  isolation** - a reader lands one paragraph off and reads the surrounding
  prose. The compounding harm named in #126 is that a wrong range can be
  mechanically WIDENED or TRIMMED into something worse, which is a hazard of
  repointing, not of reading.
- **The cheap, high-value subset is the near-miss class, and a machine can find
  it.** All four of N1-N4 share a shape no current checker tests: a range that
  starts or ends **mid-sentence** - the first line does not begin a sentence, or
  the last line does not end one. That is decidable without knowing the claim,
  it is a strict superset of the blank-start and blank-end shapes both existing
  detectors already implement, and it names exactly the citations a future
  repoint can turn into a #114. **My recommendation is a fifth detector in
  `check-design-citation-shape.py` for the mid-sentence boundary, measured
  first and wired only once its backlog is zero** - the discipline #125 already
  established - rather than 881 hand reads.
- If a hand sweep is wanted anyway, **sample again before committing to it**.
  Another 40 at a different recorded seed costs one more session and would
  halve the upper bound; two clean rounds of 40 would put it near 3.7%.

## Gates, each exit code read on its own line

Run from `/tmp/citation-rate-work` at the sampled tree. Floors derived from
`.github/workflows/ci.yml`, not retyped from any brief.

```
ruff check .                                          0
ruff format --check .                                 0   112 files already formatted
pytest                                                0   873 passed, 0 skipped, 6 deselected
check-suite-floor.sh floor (ci.yml)                 873   met exactly by 873 passed
check-harness-anchors.py --self-check --floor 458     0
check-design-citations.py                             0   1917 citations, 202 files, all resolve
check-design-citation-shape.py                        0   881 citations, 161 files, 0 findings
check-design-citation-shape.py --controls             0   7/7 controls fired
sample-134-citations.py                               0   881 sites, seed 134, 40 drawn
```

**mypy exits 1 on this branch, and the cause is ALREADY FIXED on `main`.**
The single remaining error is `docs/reviews/check-checkers-are-wired.py:65:
error: Library stubs not installed for "yaml"  [import-untyped]`, on a file
this branch does not touch. It is not mine and it is not open: the team lead
landed `0606ea5` ("Fix the red trunk I created: the wired-checker step needs
the project env"), which adds `types-PyYAML>=6` to `pyproject.toml`, **three
minutes after `9b1ca70`** - the base this branch was cut from and the tree the
sample was drawn against. So the type gate should read 0 once this is merged,
and I did not rebase to confirm it, because rebasing would move the tree the
measurement is pinned to.

**The sample is unaffected by that commit.** `0606ea5` touches `ci.yml`,
`pyproject.toml`, `uv.lock` and `check-checkers-are-wired.py`; that checker
carries **zero** `DESIGN.md` citations at both `9b1ca70` and `main`, so the
881-site container is identical either side of it.

**Both errors this branch introduced were fixed:** `sample-134-citations.py:45`
missing a return annotation and `:58` an untyped call.

This is not a code review, so it declares no `REVIEW-COVERS` range.

## What I did NOT verify

- **I did not verify that 0/40 generalises**, and the arithmetic section says
  so numerically rather than in prose. This sample cannot separate 0% from 4%.
- **The enrichment hypothesis is reasoning, not a measurement.** Testing it
  properly means reading a sample drawn from the blank-ended population's
  COMPLEMENT and comparing rates, which is a second task, not a sentence here.
- **I did not judge the ~1030 prose citations** in
  `check-design-citations.py`'s wider population. That is a deliberate scope
  call argued above, not an omission - but if the team lead wants a rate over
  the wider container, this measurement does not supply it.
- **N1-N4's suggested ranges are suggestions.** I read each against the frozen
  design and I am confident the current ranges are boundary-sloppy, but I
  repointed nothing, so nothing here proves those are the ranges the team lead
  wants. Applying them is a separate decision, and #126's F3 is the standing
  proof that a mechanical repoint can manufacture the defect it is fixing.
- **The proposed mid-sentence detector is unmeasured.** I did not implement it
  and I do not know its backlog. Its value rests on 4 of my 40 sites having the
  shape; whether that generalises is exactly the thing this report has just
  demonstrated a 40-sample cannot settle.
- **Worktree removed** when this landed; see the commit.
