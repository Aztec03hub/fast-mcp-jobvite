# ADR-BATCH - ten Accepted ADRs, a re-freeze, and 829 citations

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `adr-batch`. Your branch is `chore/adr-batch`. Your report goes to
`docs/worklogs/ADR-BATCH-REPORT.md`, committed on your branch. Your task record is **#95**.

## DO NOT START WHILE ANY OTHER AGENT IS IN FLIGHT

Every agent is dispatched with *"the design is FROZEN at `c15b138`, read it as
`git show c15b138:docs/DESIGN.md`"*. **Re-freezing points their citations at a ref that no longer
carries what they read.** Confirm with the orchestrator that the board is quiet before the first
edit. This is the one task on the board that cannot run concurrently with anything.

## The ten, and the ruling is the decision

| ADR | subject |
|---|---|
| 0023 | harnesses drop `-e`, scoped by PURPOSE not by artifact type |
| 0024 | the scan bound - **the ruling says RECORDS, the body says `MAX_PAGES`** |
| 0025 | page size / throttle scope / budget - **its ruling ANSWERS all three; the body answers none** |
| 0026 | log redaction - **its correction says the logger is `httpx2`, the body said `httpx` three times** |
| 0027 | the budget variable becomes configurable |
| 0028 | `sampling` -> `mrtr`, set closed at three |
| 0030 | the upstream's retry hint is passed on wherever we have one |
| 0031 | the approval-refusal registry row, no new slug |
| 0032 | the fifth middleware is adopted and C2 gains a row |
| 0033 | `approval_state`'s four values are a published vocabulary |

**Several carry a ruling that contradicts or corrects the body. APPLY THE RULING.** 0024, 0025 and
0026 are the ones where reading only the Decision section produces the wrong edit.

## The citation surface, measured at `9c41009` rather than estimated

```
src               370        <- repoint
tests             336        <- repoint
scripts           125        <- repoint
docs/briefs        42        <- repoint only THREE of these (see below)
docs/adr           60        <- LEAVE (an ADR quotes the design it is amending)
docs/worklogs     170        <- LEAVE (a worklog records what that unit saw)
docs/reviews      519        <- LEAVE (a review cites the design as it stood)
```

**834 to repoint, 788 to leave alone**, and the split is a judgement you should re-derive rather
than inherit. `check-design-citation-shape.py` already excludes `docs/reviews/` for exactly this
reason and says so; the same argument covers `docs/worklogs/` and applied ADRs.

**`docs/briefs/` splits INSIDE itself, which is why its 42 is not 42.** A brief is an instruction
while its task is open - a stale line number then sends an agent to the wrong text. Once the unit is
done the brief is a RECORD of what that agent was told, and repointing it rewrites history exactly
as repointing a worklog would. Measured: 19 brief files carry citations, `PREAMBLE.md` carries
**ZERO**, and only two briefs belong to open tasks - `ADR-BATCH.md` (1) and `CRITICAL-COVERAGE.md`
(2). **So the live brief set is 3 citations, not 42.** Re-derive that list at the time; more tasks
will have closed.

## The recorded hazards, every one measured on this project

- **A REPOINT MAP CAN BE WRONG.** One was, over 49 occurrences in a single pass (#37).
- **CITATION RANGES CONTRACT ON EACH COPY-FORWARD, AND A NARROWED RANGE STILL RESOLVES.** A green
  checker does not prove the citation still covers its subject. **Audit from the SOURCE inward** -
  start at the design line and ask who cites it, not at the citation and ask whether it resolves.
- **ANCHOR ON THE SUBJECT, NOT THE LINE NUMBER**, and require the subject to be unique. Four
  mechanical repoints in one day went wrong this way.
- **NEVER read a line number off an unnumbered window.** Only from `grep -n` or a Read. Offsets
  counted inside a `sed -n X,Yp` window are silent, plausible and wrong.
- **A citation trimmed at a comma is not a citation.** `DESIGN.md:1072` cost an ADR that was not
  needed because three readers carried half a sentence - the scoping clause was in the half that
  got trimmed.

## Two checkers gate this and neither is sufficient alone

`check-design-citation-shape.py` decides only what a machine can: out of bounds, blank, fence-only,
or starting on a blank line. It says in its own docstring that *"resolves" and "correct" are
different things* and that this project has found that nine times. `check-standards-citations.py`
covers the 97 standards citations and **exits 2 when its corpus is absent** - it now resolves that
corpus through `git rev-parse --git-common-dir`, so it works in a `/tmp` worktree.

**A green from both is necessary and not sufficient.** The completeness question - did every citation
that MOVED get repointed - needs the source-inward audit above.

## After the re-freeze

`#60` becomes a normal five-artifact change: the design's §7.6 list, the `Settings` field,
`.env.example`, the README table and `server.json`, plus **all three** client factories
(`tools/jobs.py` twice, `tools/candidates.py` once). The closed-set tests refuse any subset.
`tests/test_repo_hygiene.py`'s `assert len(variables) == 15` must be **DERIVED from `Settings`**, not
bumped - ADR-0027's ruling says so, and this project has watched a retyped constant rot in a brief,
two obligation rows, a CI comment and three harness floors.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped. **0 skips.** Run the gate's OWN commands,
argument for argument - `uv run --frozen mypy`, NOT `mypy src`; `ci.yml:422` is the authority.

**A review round follows this**, per the standing rule that nothing lands unreviewed, and this is
the largest single change since the last freeze.

## In the report

The new frozen SHA. Per directory: how many citations moved, how many were repointed, and how you
established that the two numbers agree. The source-inward audit and what it found. Then what you
could not settle.
