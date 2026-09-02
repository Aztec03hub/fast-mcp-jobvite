# CITATION-READ-ADR - the same read, over `docs/adr/`

**THIS ROUND DECLARES NO `REVIEW-COVERS` RANGE, DELIBERATELY.** It is not a code
review of a commit range: it reads one corpus at one SHA and rules on citations.
Declaring `6e4fae3..b7de853 PATHS: docs/adr` would tell
`check-review-coverage.py` that somebody read every change to `docs/adr/` across
31 held commits, and nobody did. **I measured that the declaration is inert here
either way** - backlog 66 with it, 66 without it, gate exit 0 both times - so it
would have bought nothing and asserted something false. Its two prior rounds
(`CITATION-READ-VERDICTS.md`, `CITATION-READ-SRC-VERDICTS.md`) declare no range
either, which is the precedent.

Agent: `suborch-196`, task #196. Brief: `docs/briefs/BRIEF-196-adr-citation-read.md`.
Worktree `fmj-worktrees/w196`, branch `fix/196-adr-citation-read`, cut from **LOCAL
`main`**. Targets read from **`git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md`**
- the SHA was derived, never retyped - which resolves to **`d1f1a52`**, 2134 lines.
Nothing outside `docs/reviews/` was edited.

**This is the third round of one job and the first over `docs/adr/`.**
`CITATION-READ-VERDICTS.md` read `tests/`; `CITATION-READ-SRC-VERDICTS.md` read
`src/` and `scripts/`. Neither touched an ADR, which is why
`WRONG-SUBJECT-REGISTER.md` had no row naming one.

**Line numbers in the CITING files may move. Anchor on the SUBJECT quoted in each
finding, not on the site line number** - every citing site was located with
`grep -n`, and every target was read from the frozen object.

## The population, enumerated rather than inherited - AS AT `9b3e85f`

```
$ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l
64
$ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md | wc -l
19
$ ls docs/adr/*.md | wc -l
36
```

**64 occurrences across 19 of the 36 ADRs.** The brief said 64 across 19 and it is
64 across 19. **All 64 were read individually**, per site and not per range - two
lines carry two citations each (`0021:33` and `0021:64`), so a per-range grouping
would have hidden four sites behind two.

**RE-RUN THAT BLOCK TODAY AND THE FIRST TWO NUMBERS ARE HIGHER, AND NOTHING IS
WRONG.** `docs/adr/README.md` has since ruled on ADR citations, which meant
QUOTING several of them, and `docs/adr/*.md` includes the README. The population
this document read is the ADRs THEMSELVES:

```
$ grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l   # 64, unchanged
$ grep -rlE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l    # 19, unchanged
```

The heading above carries its SHA so that a reader who gets a different number
knows which of the two questions they just asked.

## Tally

| Verdict | Sites |
|---|---|
| **DRIFTED** - right when written, `DESIGN.md` moved under it | **46** |
| **CORRECT** at the frozen SHA | **14** |
| **WRONG** - resolves, names a different subject, and always did | **2** |
| **BOUNDARY-NIT** - right paragraph, range misaligned | **2** |
| UNSETTLEABLE | 0 |

**DRIFTED IS THE DOMINANT CLASS AND IT IS NOT A SUBSPECIES OF WRONG.** 46 of 64 -
**72%** - point at text that was the cited subject when the citation was written
and is something else today. **In an ADR the remedy is NOT a repoint.** `#203`
ruled at `ec57a65` that an ADR's citations are AS AT its acceptance and stay
(`docs/adr/README.md`, the as-at-acceptance section): an ADR is a decision record,
and repointing it rewrites the evidence for a decision already taken. A WRONG one
is a different defect - it never named its subject, so there is no as-at reading
to preserve - and IS repointed, with an explanation of how the author read the
wrong paragraph. They are different defects with different causes and the brief
was right to insist they not be folded.

**THIS SENTENCE USED TO READ *"the remedy is a repoint"*, and it survived the
ruling that refuses one.** It was written before `ec57a65` and stayed true-looking
afterwards, because the paragraphs recording what this round actually DID (below:
*"I did NOT repoint these"*) are not the ones a reader lands on when checking what
a DRIFTED verdict OBLIGES. A verdict document is the operating instruction for the
next sweep, so the definition is where the ruling has to land.

## How DRIFTED was distinguished from WRONG, since no grep can do it

`DESIGN.md` has **52 committed versions**, growing 349 -> 2134 lines. For each
site I read the cited lines at the frozen SHA, and - where they did not carry the
claim - at the commit that INTRODUCED that citation string into that ADR:

```bash
git log --reverse --format=%H -S 'DESIGN.md:<range>' -- docs/adr/<file>
git show <that-commit>:docs/DESIGN.md | sed -n '<range>p'
```

**`git blame` on the citing line is the WRONG instrument here and I used it first.**
Blame returns the last commit that touched the line, which for these files is
usually a later prose rewrite or a bulk repoint - it dated ADR-0019's citations to
`89aceee` (2026-09-01) when the citation was introduced at `90bade0` (2026-08-28).
Reading the design at the blame commit therefore compares against a version the
author never saw. `git log -S`, reversed, dates the citation itself.

**A quote-matching sweep across all 52 versions was built and then DEMOTED to an
enumerator**, because it produced false negatives I could see: it scored ADR-0019's
`:603` as NEVER-MATCHED when the target matched verbatim, because the ADR quotes
`(**§5.4**)` with markdown emphasis the design does not carry, and it attributed
one site's quote to its neighbour through an over-wide window. Both were fixed and
it still cannot be trusted alone. **Every verdict below came from reading.**

## The two WRONG citations

Both resolve, both pass `check-design-citations.py`, and both name a **different
member of the same list** - which is the shape that makes this class invisible.

### W-1. ADR-0013 `:13` cites `DESIGN.md:1223` - the wrong §8 case

`docs/adr/0013-secret-absence-case-needs-a-pairing.md:13`:

> §8 case **#2** (`DESIGN.md:1223`) reads, in full:
> > *"a secret never reaching a log record, including the `jobFeed` URL;"*

At `135c3ac` - the freeze ADR-0019 names as its own reference, and the era this ADR
was written in - `1221` is that case. **`1223` is inside the NEXT bullet:**

```
1221: - a secret never reaching a log record, including the `jobFeed` URL;
1222: - **`.gitignore` covers the credential patterns and `.env.example` carries no real value** - asserted
1223: against the committed files, since the row this covers is about what reaches a log ...
```

So the citation names the `.gitignore`/`.env.example` case while the sentence
around it quotes the secret case. **It has never resolved to its subject at any of
the 52 versions**: the subject sits at 996, 1221, 1267, 1269, 1270, 1331, 1351 -
never 1223.

**Fix:** `DESIGN.md:1223` -> `DESIGN.md:1351` (its position at the frozen SHA).
Anchor phrase: *"a secret never reaching a log record, including the `jobFeed` URL"*.

### W-2. ADR-0014 `:13` cites `DESIGN.md:1763` - the wrong threat row

`docs/adr/0014-c8-i1-empty-values-is-wrong.md:13`:

> `DESIGN.md:1763`, threat row **C8-I1**, rated **Critical**, states that
> `.env.example` is *"committed with empty values"*

At `135c3ac`, C8-I1 is at `1760`. **`1763` is row `C8-E2`** - *"`JOBVITE_TLS_TERMINATED_BY_PROXY=true`
asserted where no proxy terminates TLS"* - a different row, a different STRIDE
category, and rated Medium rather than Critical. The three rows between them
(`C8-D1`, `C8-E1`) are also not C8-I1. Across all 52 versions C8-I1 sits at 1162,
1176, 1190, ... 1760, 1808, 1810, 1811, 1879, 1899 - **never 1763.**

**Fix:** `DESIGN.md:1763` -> `DESIGN.md:1899`. Anchor phrase: *"A real credential
or a `.env` reaches the public repository"*.

## The two BOUNDARY-NITs (not register rows, by the register's own rule)

### B-1. ADR-0018 `:47` cites `DESIGN.md:1011`, which is a BLANK LINE

The ADR quotes *"Teardown completes before `os._exit`, so skipping atexit handlers
costs nothing we rely on"*. At `28be78a` that sentence is at **1010**; **1011 is
empty**. The citation was off by one onto a blank line the day it was written, and
the subject is now at 1085.

This is the class `#126` swept for elsewhere (`fix/blank-end-citations`). It is not
a wrong SUBJECT - there is no subject there to be wrong - and the register
explicitly excludes boundary nits, so **I did not add a row.** Flagging it rather
than filing it is a call Tier 0 may overrule.

**Fix:** `DESIGN.md:1011` -> `DESIGN.md:1085`.

### B-2. ADR-0021 `:50` cites `DESIGN.md:1361-1364`, one line late and three long

The claim is about *"the mechanism that produced it"*. At the frozen SHA that
phrase is at **1360**, one line ABOVE the range; the range then runs to 1364, past
the end of the vocabulary and into the PII case. The cited range does sit inside
the same §8 audit-event bullet, so the paragraph is right and the window is wrong.

**Fix:** `DESIGN.md:1361-1364` -> `DESIGN.md:1359-1361`.

## The 46 DRIFTED sites

Grouped by ADR. Every one was read at the frozen SHA and at the commit that
introduced it. **I did NOT repoint these** - 46 edits across 17 ADRs is a sweep,
and ADRs are records of decisions rather than live code, which is the distinction
`#111` ruled on for `docs/plans`. That ruling is Tier 0's to extend or refuse.

| ADR | Sites | Cited | What it says now at the frozen SHA |
|---|---|---|---|
| 0017 | 3 | `495-496`, `515` x2 | §4.5 paging base-agnosticism; the registry row moved |
| 0018 | 4 | `992-1010`, `981-983` x2, `1341-1342` | §7.3 `JOBVITE_TOOLS`; the operator-instruction ceiling |
| 0019 | 4 | `603` x4 | §5.1's "three honest exceptions to uniformity" |
| 0020 | 2 | `1513-1518`, `1518` | the lockfile paragraph and `--prerelease=allow` |
| 0021 | 10 | `1276-1280`, `1756` x2, `678-684`, `582-735`, `611`, `510-511`, `1278`, `678-682`, `692-695` | middleware prose, `about:blank` scope, a blank line |
| 0024 | 5 | `486-487` x2, `469-477`, `373-375`, `425-427` | base detection, §4.5 head, the 429 mapping |
| 0025 | 3 | `373-375` x3 | the 429 mapping |
| 0027 | 2 | `373-375` x2 | the 429 mapping |
| 0028 | 4 | `510-511`, `1276-1280` x2, `1051-1054` | paging ids, middleware prose, uvicorn `capture_signals` |
| 0029 | 1 | `510-511` | paging ids |
| 0031 | 3 | `513-521`, `510`, `356-359` | the paging cap; §4.3's ordered timeout/retry/breaker |
| 0032 | 2 | `1730`, `1725` | the threat-modeling requirement; a blank line |
| 0033 | 2 | `678`, `1756` | the `jobFeed` URL line; a blank line |
| 0034 | 1 | `2063` | see below - **the ADR's own application moved it** |

**ADR-0034 `:6` is the sharpest instance in the set.** It cites `DESIGN.md:2063`
for the words *"all eleven ADRs"*. At `e3b5c97^` line 2063 reads *"This is the job
all eleven ADRs"* - exactly right. `e3b5c97` is the commit that APPLIED ADR-0034,
deleting that count. **The ADR's own accepted change falsified its own citation**,
and the re-freeze then made the stale reading the official one. No sweep that
looks only at the current freeze can tell that apart from carelessness.

**Four DRIFTED sites now land on BLANK LINES** (`0021:20`, `0021:64` -> `1756`;
`0032:27` -> `1725`; `0033:29` -> `1756`), which is drift plus the B-1 shape.

## The 14 CORRECT sites

| ADR | Sites | Cited | Subject at the frozen SHA |
|---|---|---|---|
| 0012 | 1 | `172-175` | control-character and bidi rejection before dispatch |
| 0026 | 1 | `315-318` | the `jobFeed` URL classified sensitive, `sc=` redacted |
| 0029 | 6 | `165` x6 | `\| Max total request body size \| 1 MiB \|` |
| 0029 | 2 | `181-190` x2 | what a caller receives when a §2.1 limit fires |
| 0029 | 1 | `186-188` | 422 rather than 400 for a structural limit |
| 0034 | 1 | `2061-2070` | the two jobs an ADR does |
| 0035 | 2 | `2064`, `2076` | the `Deviation`/`Both` selector and the three values |

**The zero-elsewhere is non-vacuous and here is why.** ADR-0029 alone carries 9 of
the 14, and it is the NEWEST heavy citer (`cb9b042`, `a1d81e7`). ADR-0035 and
ADR-0034's surviving sites were written days ago against the current freeze.
**Correctness here tracks AGE, not care** - the recently-written citations are
right and the old ones have drifted, which is what a drift hypothesis predicts and
a carelessness hypothesis does not.

## ADR-0030: two sites READ but OUTSIDE the 64, added by `#224`

**This section is not part of the sweep above and deliberately does not join its
counts.** The tally, the 46/14/2/2 split and the 64/19 population all describe one
SPELLING, `DESIGN.md:N`. ADR-0030's citations are written in the BARE form, so a
selector requiring the filename could never see them, and folding them into the
totals would silently redefine what those totals measure. They are recorded here
instead, with the same evidence standard.

| ADR | Sites | Cited | Verdict | What it says now at the frozen SHA |
|---|---|---|---|---|
| 0030 | 2 | `:356-359`, `:361-362` | **DRIFTED** (both) | the ordered timeout/retry/breaker paragraph, and the excluded-from-retry rule |

**Re-measured for `#224` by `suborch-224`, independently of `#210`, and the two
measurements AGREE.** The blob the ADR names is at `0030:29`, three lines above
the citations; the freeze was derived from `docs/DESIGN-FREEZE.txt` and never
retyped:

```bash
$ grep -n ':[0-9]\+\(-[0-9]\+\)\?`' docs/adr/0030-*.md
31:- `:356-359` - an open breaker and an outage share `/problems/service-unavailable` ...
33:- `:361-362` - *"Jobvite's `429`, if it exists, is retried and then mapped to 503 ...

$ FREEZE=$(cat docs/DESIGN-FREEZE.txt); echo "$FREEZE"
d1f1a52

$ git show c15b138:docs/DESIGN.md | sed -n '356,359p'
- **An open breaker is distinguishable from an outage without inventing a type.** Both use
  `/problems/service-unavailable` at 503, per the registry; what distinguishes them is `detail`,
  which says whether Jobvite failed or whether we have stopped calling it, plus a `retry_after`
  hint. An earlier revision minted two slugs for this. The distinction is real and worth making;

$ git show "$FREEZE":docs/DESIGN.md | sed -n '356,359p'
Ordered timeout, then retry, then circuit breaker.

- **Timeouts explicit and per-phase.** No SDK default, no single scalar.
- **Retries live inside this module**, via `tenacity` with jitter, and only for connection errors,

$ git show c15b138:docs/DESIGN.md | sed -n '361,362p'
- **Jobvite's `429`, if it exists, is retried and then mapped to 503**, honouring `Retry-After`
  when present. No 429 has ever been observed and no rate-limit header is returned (§4.4), so this

$ git show "$FREEZE":docs/DESIGN.md | sed -n '361,362p'
  inbound request's deadline, because there is no inbound deadline here - see the note below.
- **`create_candidate` is excluded from retry by construction**, not by configuration. This is
```

Both citations are EXACT at the blob ADR-0030 names and land on unrelated prose at
the freeze. That is DRIFTED, not WRONG, and under `#203`'s ruling at `ec57a65` an
ADR's citations are AS AT acceptance and are NOT repointed. **Nothing here obliges
an edit to ADR-0030.**

### Which selector missed them, and why naming it matters

Three selectors were run over this corpus and all three require the filename:

- this document's own, `DESIGN\.md:[0-9]+(-[0-9]+)?`, quoted in the population block above;
- `BRIEF-196-adr-citation-read.md`'s, which is the same regex;
- the register's population query, recorded in the *"What I did NOT verify"* section below.

A bare citation inherits its target from the prose that last named a document, so
no regex over the citing line can resolve it. **`#204`'s discriminator is the
instrument that reads the surrounding prose, and it is what would have caught
these two.**

**ADR-0030 IS NOT THE ONLY ONE.** This document's own closing section already
names seven ADRs carrying a bare form and no `DESIGN.md:N` form at all: 0002,
0008, 0009, 0011, 0015, 0023 and 0030. **Adding this row closes ONE of those
seven.** The other six remain unread, and a row that recorded 0030 without saying
so would leave the next selector free to miss them - which is the whole reason
this section names the blindness and not just the finding.

## The qualifier: what I measured, and what I am NOT ruling

The claim under audit is *"nine wrong-subject citations have been found on this
project, **four of them inside the ADR documenting that defect class**"*.

**The ADR documenting that defect class is ADR-0019** - *"`DESIGN.md:603` cites
`§5.4`, and there is no §5.4"*. Measured:

    4   DESIGN.md citations inside ADR-0019       all four are `:603`
    0   of them are WRONG by this register's definition
    4   of them are DRIFTED - correct at `90bade0`, stale since

**The "four" is arithmetically exact and semantically empty.** ADR-0019 does carry
exactly four `DESIGN.md` citations, which is almost certainly where the digit came
from - but **not one of them is a wrong-subject citation.** All four pointed at the
right sentence when written. And the one defect ADR-0019 actually records, the
`§5.4` cross-reference, **this register already excludes on purpose**, because
`§5.4` resolves to nothing and a gate catches it.

**Across the whole ADR corpus the wrong-subject count is 2**, in ADR-0013 and
ADR-0014 - two ADRs, neither of them the one the qualifier names.

**I am not ruling on the sentence.** Per the brief, the number goes to Tier 0. What
I will say plainly is that the qualifier is not four-in-ADR-0019 under any reading
I could construct, and that it did not come out tidy.

## What I did NOT verify

- **I did not repoint the 46 DRIFTED sites.** That is a sweep and a ruling, not a
  reading, and it interacts with `#111`'s records-are-not-repointed decision.
- **I did not read the ADRs' non-`DESIGN.md` citations** - `agent-guardrails.md:122`,
  `error-contract.md:115` and the rest. The brief scoped me to `DESIGN.md:N`, and
  those are a real population nobody has read either.
- **THE BARE-`:NNN` FORM IS INVISIBLE TO THIS ROUND'S SELECTOR, AND I MEASURED THE
  GAP RATHER THAN NOTING IT.** ADR-0017 `:67` writes *"`DESIGN.md:515` is amended,
  and `:489-490`'s seven-member requirement then holds"* - a citation into
  `DESIGN.md` that my regex, my brief's regex, and the register's own population
  query all miss:

      58  bare `:NNN` / `:NNN-MMM` citations in docs/adr/, across 16 files
       7  ADRs carry a bare form and NO `DESIGN.md:N` form at all, so they were
          entirely outside this sweep: 0002, 0008, 0009, 0011, 0015, 0023, 0030

  Not all 58 target `DESIGN.md` - a bare form inherits whatever document the
  surrounding prose last named, which is exactly why it cannot be counted by grep
  and why it is the harder half. **So "64 citations across 19 files" is the
  population of ONE SPELLING, and my report's headline inherits that limit.** The
  corpus this task was told to close is not closed.
- **`actionlint` is not installed here**, so I ran none of the workflow linting.
- I did not re-run the full pytest suite; nothing I changed is executable.
