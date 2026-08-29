# ADR-0025 report - the tenth ADR: Q1 withdrawn, Q2 and Q3's open half applied

Task **#112**. Branch `fix/adr-0025`, two commits, on top of `167f526`. Not merged, not pushed.
Worktree `/tmp/adr-0025-fix`, removed at the end (see the last section).

| | |
|---|---|
| `aca9397` | the design edit, the ADR corrections, the code comment, 593 repoints |
| `fd3d3b4` | the citation checkers re-frozen at `aca9397`, and five docstring lines rewrapped |

---

## THE DESIGN MOVED. The new freeze is `aca9397`.

**Old freeze `8a9d63c`, DESIGN.md blob `5235d5e58c307764621103257afbe62f5107164e`.**
**New freeze `aca9397`, DESIGN.md blob `e009ac415e530d08fc951445154504291d4fa9e4`.**

`fd3d3b4` does not touch `docs/DESIGN.md`, and the blob check says so - `HEAD:docs/DESIGN.md` is
`e009ac41...`, byte-identical to `aca9397:docs/DESIGN.md`. **So `aca9397` is the SHA to hand the
next agent**, not `fd3d3b4`, and it stays the right answer through any later commit that leaves the
design alone.

```
$ for r in 8a9d63c aca9397 HEAD; do printf '%s %s\n' "$r" "$(git rev-parse $r:docs/DESIGN.md)"; done
8a9d63c 5235d5e58c307764621103257afbe62f5107164e
aca9397 e009ac415e530d08fc951445154504291d4fa9e4
HEAD    e009ac415e530d08fc951445154504291d4fa9e4
```

One pure insertion of **20 lines** in §4.4, 2113 -> 2133 lines. It lands after the outbound-envelope
paragraph and before the Redis paragraph, and it touches no existing line - which is why the repoint
below has **0 MANUAL and 0 ABSORBED**.

## Q1 - WITHDRAWN. I verified the withdrawal rather than taking it on trust.

The brief says Q1's stated reason is measurably false. **It is.** The measurement, from `grep -n`
against the frozen design, not from a `sed` window:

```
$ git grep -n 'the two are related by' 8a9d63c -- docs/DESIGN.md
8a9d63c:docs/DESIGN.md:455:(§7.7); the two are related by `min(transport_cap, configured_result_cap)`.
```

Whole sentence, §4.5, lines 453-455 of `8a9d63c`:

> Offset-based, `start` and `count`. Page cap **500** on v2, **1000** on `/v1/jobFeed`. These are
> the *transport* limits. The *result* limit returned to a model is separate and configurable
> (§7.7); the two are related by `min(transport_cap, configured_result_cap)`.

And the code that implements it, `JobviteClient.result_cap()`:

```
return min(self.transport_cap(jobfeed=jobfeed), self._max_results)
```

**The design states a paging policy and the code follows it.** Nothing about page size is written,
`scan()`'s behaviour is untouched, §4.5 is not amended.

## Q2 and Q3 - WHAT I WROTE, verbatim

Inserted in §4.4, at `aca9397:docs/DESIGN.md`, immediately after "*...is outside what the vendor
documents and should know it.*":

> **That outbound throttle IS NOT IMPLEMENTED. The two rules below constrain whoever builds it; they
> do not describe what runs today** (ADR-0025). `JOBVITE_OUTBOUND_RATE_LIMIT` is declared, typed,
> defaulted, documented in `.env.example` and covered by config tests, and **no code reads it** -
> which is the defect ADR-0025 was raised over. This section states the shape the implementation
> must take so that the unit which builds it does not choose that shape silently.
>
> - **The throttle is PER-PROCESS**, scoped like §4.3's circuit breaker and for the same reason: it
>   exists to protect Jobvite from us, and Jobvite sees our process, not our scans. A per-scan
>   throttle lets N concurrent scans each spend the full allowance, so the rate arriving at Jobvite
>   is N times the limit and the limit means nothing. Two mechanisms with one purpose must not hold
>   opposite ideas of what they are protecting.
> - **Time spent waiting on the throttle SPENDS §4.3's outbound budget.** A bound that excludes the
>   term dominating the wait is not a bound, and a caller does not care whether we were waiting on
>   Jobvite or waiting on ourselves.
>
> **Those two rules compose with §4.5's paging, and that composition is the implementer's to
> check.** ADR-0025 works the arithmetic through on this design's own worked example and is where it
> is recorded. Whoever implements the throttle must either size the defaults so the composition
> holds, or raise it as an ADR against §4.5 - not settle it silently, which is the outcome ADR-0025
> exists to prevent.

**THE SENTENCE SAYING THE THROTTLE IS UNBUILT**, which the brief asked me to quote back:

> **That outbound throttle IS NOT IMPLEMENTED. The two rules below constrain whoever builds it; they
> do not describe what runs today** (ADR-0025).

It is the paragraph's FIRST sentence, in bold, before any rule - so a reader meets "not
implemented" before meeting anything that could be mistaken for a description of behaviour.

### Three deliberate choices in that wording, each of which could have gone the other way

**1. Q3's settled half is CITED, not restated.** The bullet says *"SPENDS §4.3's outbound budget"*
and stops. An earlier draft of mine read *"That budget bounds wall-clock for one tool invocation,
and..."* - which is §4.3's own sentence written a second time, in a second place, free to drift.
The brief forbids writing that half twice and I removed it. The bullet is still readable, because
§4.3 is one section up and named.

**2. The third paragraph does NOT state a page-size policy.** The brief says write nothing about
page size. It names §4.5 as the thing the two rules compose with, and points at ADR-0025 for the
arithmetic, and stops - no numbers, no `min(...)`, no requests-per-scan. I judged that a constraint
on the implementer that omits the composition entirely would be a constraint they cannot act on,
and that a POINTER to where the arithmetic lives is not the same as re-deciding it. **If you read
that differently, delete that paragraph and nothing else moves** - the two rules stand without it.

**3. No test, by instruction.** Filed instead as **task #113**: a tripwire that fails when
`outbound_rate_limit` gains its first reader, in the shape #86 used for `scan()`'s first caller. It
notes that `docs/reviews/check-settings-are-read.py` already knows about this setting and may be
the right home rather than a new test.

## ADR-0025 corrected in place

Every one rewritten, none annotated with a rider. Anchored on the subject text and asserted unique
before each replacement (the script asserts `count == 1` and aborts otherwise).

| # | Where | What changed |
|---|---|---|
| 1 | Status line | "the three questions are ANSWERED below" -> "**Q2 and Q3 answered and APPLIED; Q1 WITHDRAWN**" |
| 2 | Context table, "Where" column | `§7.3, unobserved` -> `§4.5, unobserved` |
| 3 | Decision, opening sentence | "**§7.3 and §4.4 must settle...**" -> "**§4.5 and §4.4 must settle...**" |
| 4 | Decision, question 1 | The false reason rewritten: deleting the branch was right, the recorded REASON was wrong, §4.5 states the policy so the branch was CONTRADICTING it |
| 5 | Ruling header | "accepted, and answered rather than re-deferred" -> "Q2 and Q3 answered; Q1 WITHDRAWN on re-reading the design" |
| 6 | Ruling intro | Rewritten to say two are answered and one is withdrawn |
| 7 | Ruling Q1, whole section | Replaced by "**WITHDRAWN** - it rested on a false reading of the design", carrying §4.5's whole sentence |
| 8 | Ruling Q3, closing paragraph | "**Q1 is what makes Q3 payable**" removed rather than left pointing at a withdrawn section |
| 9 | Ruling, closing paragraph | §4.4 now says in the DESIGN that the throttle is unimplemented; plus the irony paragraph and the tripwire it wants |

**Items 2 and 3 are the two `§7.3` citations the brief named.** §7.3 is *Configuration*; the page
cap and the `min()` rule are in §4.5 *Pagination*. #95 fixed the identical defect in ADR-0024 and
left this one pending your ruling.

**The Decision's own Q1 (item 4) mattered more than it looks.** A reader meets the Decision before
the Ruling, so leaving the false claim there and withdrawing it 60 lines later would have left the
ADR asserting and retracting the same thing - the two-contradictory-claims shape that cost this a
round trip in the first place.

**Item 7 cites the frozen blob without emitting a `DESIGN.md:N` token**, deliberately. It says
"`git show 8a9d63c:docs/DESIGN.md`, §4.5, lines 453-455 of that blob". Writing `DESIGN.md:453-455`
would have created a live citation that `check-design-citations.py` resolves against the CURRENT
file, where those lines are now something else. A SHA-qualified reference cannot go stale.

## The code comment

`src/fast_mcp_jobvite/services/jobvite_client.py`, in `scan()`, anchored on the subject
`A separate "exhaustive scans use the raw transport cap" rule` - unique in the file.

Before:

```python
        # A separate "exhaustive scans use the raw transport cap" rule
        # would be a paging policy this design does not state, invented
        # here, and untestable without a knob invented to test it.
```

After:

```python
        # A separate "exhaustive scans use the raw transport cap" rule
        # would CONTRADICT the policy §4.5 states; it is not a vacuum
        # this would fill. ADR-0025's Q1 said the design stated no
        # policy and was WITHDRAWN for it. Changing this is an ADR
        # amending §4.5, never a branch invented here - and such a
        # branch is untestable without a knob invented to test it.
```

Same conclusion, correct reason. §4.5 is now the authority the code FOLLOWS rather than a vacuum it
declines to fill, and the comment records that the identical mistake was made once at ADR level and
withdrawn - so the next reader tempted by it meets the history rather than repeating it. The
"untestable" clause is kept because it was a second, independent, and still-true reason.
**No behaviour changed.** The three lines above and below it are untouched and `scan()` did not move.

## The repoint

The insertion is 20 lines at 448, so every citation at or past 448 moves +20 and everything before
it is unmoved. Run with the two committed scripts, over the same live set #95 used - `src`, `tests`,
`scripts`, `pyproject.toml`, `.pre-commit-config.yaml`, `.env.example`, **85 files**:

```
$ python3 scripts/adr-batch-repoint.py --old /tmp/DESIGN.before --new docs/DESIGN.md --apply $FILES
TOTAL unmoved=298 moved=593 manual=0
```

**Verified on the content join, NOT by re-running the mapper**, which is the trap
`ADR-BATCH-REPORT.md` records - a second mapper pass re-maps the new numbers as if they were old
ones and prints a confident agreement with itself:

```
$ python3 scripts/adr-batch-verify-repoint.py 167f526 167f526 $FILES
checked=891  widened=0  failed=0
```

`checked=891` is the join's own count of citation pairs: every citation present before is present
after, at a number whose target text is byte-identical. **`widened=0` and `failed=0` are what a
pure insertion outside every cited range should produce**, and the batch's own run produced 26
ABSORBED because its insertions landed INSIDE cited ranges. Mine did not, which is checkable: the
insertion point (447-448) sits between §4.4's prose and §4.5's heading, and no citation spans it.

**Two SHA-pinned checkers had to be re-frozen, and this is the part a green run would not have
caught.** `docs/reviews/check-design-citation-shape.py` resolves `src tests scripts` citations
against a hard-coded `--sha` default. Leaving it at `8a9d63c` would have judged the NEW numbers
against the OLD blob and reported false findings - it is not currently a CI step, so nothing would
have gone red; it would just have started lying. Bumped to `aca9397`.

That same file carried a **SECOND copy of the freeze in its prose**, and that copy was already
stale: it said `c15b138` while the default said `8a9d63c`. I deleted the copy rather than updating
it, so the SHA lives in exactly one place there now. `check-design-citations.py`'s two `--since`
references are bumped for the same reason.

**`.github/workflows/ci.yml` needs NOTHING from me, and I checked rather than assumed:**

```
$ grep -n 'citation-shape\|check-design-citations\|--sha\|--since' .github/workflows/ci.yml
211:      # no instrument until now: check-design-citation-shape.py reads only
726:        run: python3 docs/reviews/check-design-citations.py
```

Line 211 is a comment. Line 726 passes no SHA, and `check-design-citations.py`'s default mode
resolves against the working tree, not against a pinned blob. `check-design-citation-shape.py` is
not a CI step at all. **No `ci.yml` change is requested by this task.**

**Five docstring lines went over 72 columns, and the cause is arithmetic, not prose.** The repoint
widened four ranges from three digits to four (`982-987` -> `1002-1007`), adding two characters to
lines that were already at the limit. This is the same side effect the ten-ADR batch recorded.
Rewrapped in `src/fast_mcp_jobvite/config.py` (4 lines) and `docs/reviews/check-design-citations.py`
(1 line); **no wording changed, only line breaks.** Rewrapping one line at a time cascaded into the
next line twice before I wrapped the whole paragraph, which is worth knowing for the next repoint.

## Gates - every number read from that command's own exit code, on its own line

| gate | exit | result |
|---|---|---|
| `uv run --frozen pytest` | **0** | **868 passed, 0 skipped**, 6 deselected, 50.24s |
| `bash scripts/check-suite-floor.sh 868` | **0** | `suite floor OK: 868 passed, floor 868` |
| `python3 scripts/check-harness-anchors.py --self-check --floor 458` | **0** | `all 458 anchors resolve to exactly one hit in their target file` |
| `uv run --frozen mypy` | **0** | `Success: no issues found in 96 source files` |
| `uv run --frozen ruff check .` | **0** | `All checks passed!` |
| `uv run --frozen ruff format --check .` | **0** | `105 files already formatted` |
| `python3 docs/reviews/check-design-citations.py` | **0** | |
| `python3 docs/reviews/check-design-citation-shape.py` | **0** | |
| `python3 docs/reviews/check-cross-references.py` | **0** | `Every section reference resolves within its own document.` |
| `python3 docs/reviews/check-standards-citations.py` | **0** | |
| `python3 docs/reviews/check-obligations.py` | **0** | `Every mapped anchor still contains its subject.` |
| `python3 docs/reviews/check-settings-are-read.py` | **0** | |
| `python3 docs/reviews/check-env-vars-are-declared.py` | **0** | |
| `python3 scripts/check-committed-file-types.py` | **0** | |

**Both floors were grepped from `ci.yml` at run time, not retyped from the brief:**

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 868
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 458
```

They agree with the brief's 868 and 458, so nothing was stale this time - but the grep is what I
ran the gate on.

**0 skips, and I checked rather than inferring it from the summary line**: `grep -c skipped` over
the pytest output returns 0. The 6 **deselected** are marker deselections at collection
(874 collected, 6 deselected, 868 selected), which is a different thing from a skip and is the same
6 the floor was set against. `check-suite-floor.sh` was fed the run's real output on stdin - it
reads stdin, and calling it without input produces `no passed-count in the output`, which I hit
once and which is a good failure.

**`check-obligations.py` reports no anchor movement**, verbatim:

```
Every mapped anchor still contains its subject. OK.
```

That is expected: obligation anchors carry no line number since `afaf226`, so a 20-line insertion
cannot move them. No repointing of `docs/OBLIGATIONS.md` was needed and none was done.

---

## FINDINGS, each with a suggested fix

### F1 (High, for you) - there is an UNMERGED prior attempt at this task, and it is not junk

`/tmp/adr-0025-work` is a live worktree on branch **`chore/adr-0025-q2q3`**, commit **`ab27abd`**,
authored 2026-08-29 13:04:43, parented on `b079ae5`. It is a complete prior attempt at #112 -
design insertion, ADR corrections, code comment, 593 repoints - plus two uncommitted files that were
mid-way through the SHA bump. **I did not touch it.** Your brief described this work as undone, so
either it is unknown to you or it was rejected and the branch outlived the decision.

**I built `fix/adr-0025` fresh from `167f526` rather than cherry-picking it**, and I read it as
prior art. Two defects in it are why I did not reuse it as-is:

1. **It cites the WRONG FROZEN SHA.** Its Q1 withdrawal quotes `git show c15b138:docs/DESIGN.md`,
   `:434-436`. `c15b138` is the PREVIOUS freeze - `c15b138:docs/DESIGN.md` is blob `8988e8cd...`,
   not `5235d5e5...` - so it quotes a design two freezes back and gives line numbers that do not
   hold at `8a9d63c`. Your brief says `8a9d63c` explicitly, and mine cites `8a9d63c`.
2. **Its Q3 bullet restates §4.3's settled half** ("*That budget bounds wall-clock for one tool
   invocation, and...*"), which is the half the brief says must not be written twice.

Its `git show --stat` looks alarming - 74 files, +694/-623 - and that is NOT churn: it is the same
593-citation repoint mine does, plus `pyproject.toml`, `.pre-commit-config.yaml` and `.env.example`.
**It arrives at 593 independently, which is a real cross-check on my number.**

**Suggested fix:** decide the branch's fate explicitly and record it. If mine lands, delete
`chore/adr-0025-q2q3` and remove `/tmp/adr-0025-work` - but read it first, because a worktree
cleanup on this project was once one command from destroying 513 lines of unreported work.

### F2 (Medium) - four of ADR-0025's own DESIGN.md citations resolve to the wrong sentence

Filed as **task #114** with all five measured. Summary: ADR-0025 cites `DESIGN.md:1572-1575`
(result cap), `:373-375` (budget), `:1576-1581` (throttle) and `:1583-1584` - and against
`8a9d63c` **all four land in the wrong section**, mostly in §10's advisory machinery. They were
written against an older freeze, and #95 left `docs/adr` unrepointed as records.

**I did not fix them**, because the brief named only the two `§7.3` citations and #95's
records-are-not-repointed ruling covers the rest. **This needs your call**: an ADR being corrected
in place is arguably no longer a pure record. **Suggested fix:** repoint all four, or better,
replace the numbers with subject phrases the way #109 did for `ci.yml` so they cannot go stale
again. Task #114 carries the verified replacement targets.

### F3 (Medium) - a LIVE checker carries the same wrong citation, and both citation gates are blind to it

`docs/reviews/check-settings-are-read.py:9` says *"`DESIGN.md:1576-1581` specifies a self-throttle"*.
That range is the advisory-ignore table. The subject is `8a9d63c:docs/DESIGN.md:1637`.

**Why nothing caught it, which is the part worth keeping:** `check-design-citations.py` checks only
that a range is IN BOUNDS. `check-design-citation-shape.py` sets `LIVE = ("src", "tests", "scripts")`
and excludes `docs/reviews` on purpose, with a comment explaining that a REVIEW cites the design as
it stood when the review ran. **That reasoning is right for a review document and wrong for a
checker.** `docs/reviews/check-*.py` are live executables sitting inside a directory whose exclusion
was written for prose. **Suggested fix:** move the checkers out of `docs/reviews/`, or narrow the
exclusion to `*.md` so `docs/reviews/*.py` is swept. Both in task #114.

### F4 (nit) - the repointer repointed its own examples

`scripts/adr-batch-repoint.py:134`'s comment carries `DESIGN.md:551` / `DESIGN.md:551-553` as
ILLUSTRATIONS of the regex, not as citations, and the apply pass moved them to `571`. Harmless -
they illustrate equally well at any number - and it is what #95's run did too, so I left it for
consistency rather than introducing a divergence.

**Suggested fix:** mark them `REPOINT-EXEMPT`, which is the marker
`docs/reviews/check-design-citations.py` already uses for exactly this at its own lines 75 and 248.
One-line change, no behaviour.

---

## WHAT I DID NOT VERIFY

Two items, and both are genuinely unsettleable from here rather than untried.

**1. Whether §4.4's new paragraph survives contact with an implementer.** It constrains a mechanism
nobody has built, so its only test is the first person who builds the throttle. Task #113's tripwire
is the closest available proxy and it checks that the paragraph gets READ, not that it is right.
This is the shape of risk the brief named and the two conditions are the mitigation, not a proof.

**2. Whether `min(transport_cap, configured_result_cap)` is the RIGHT paging policy.** Q1 is
withdrawn on the ground that the design STATES a policy, which is a claim about the text and is
measured above. It is not a claim that the policy is correct, and I made no attempt to settle that -
correctly, since the brief and the ADR both say it needs its own ADR amending §4.5.

Things I could have parked here and settled instead, listed so you can see they were not skipped:
whether `ci.yml` needed a change (**grepped - it does not**); whether the 6 deselected were skips
(**checked - they are marker deselections**); whether `check-obligations.py` needed a repoint (**ran
it - no anchor moved**); whether `ab27abd`'s 74-file diff was formatting churn (**read it - it is
the same repoint**); and whether `c15b138` and `8a9d63c` hold the same design (**blob hashes - they
do not**).

## Worktree

`/tmp/adr-0025-fix` is **removed** (`git worktree remove`), and `git worktree list` confirms it is
gone. `/tmp/adr-0025-work` is **left in place deliberately** - it is not mine, it holds `ab27abd`
plus uncommitted work, and F1 asks you to rule on it before anything deletes it.
