# ADR-BATCH-REPORT - ten ADRs, a re-freeze, and one ruling I would not make for you

**Agent:** `adr-batch`. **Branch:** `chore/adr-batch`. **Base:** `06a4359`. **Task #95.**
Not merged, not pushed. `.github/workflows/ci.yml` not touched.

> **This path already held the EIGHT-ADR batch's report** (task #1, 422 lines, freeze
> `c15b138`). My brief names this exact path, so writing here overwrote it. It is preserved
> byte-identical at **`docs/worklogs/ADR-BATCH-8ADR-REPORT.md`**, whose own title already
> said *"eight Accepted ADRs applied"*. Nothing linked to the old path except the brief,
> which links it for THIS report, so no inbound reference dangles - checked with
> `grep -rn 'ADR-BATCH-REPORT' --exclude-dir=.git .`

## THE NEW FROZEN SHA IS `8a9d63c`

```
$ git log --oneline -1 8a9d63c
8a9d63c Apply nine of ten ADRs to the frozen design, and repoint by content not arithmetic

$ python3 docs/reviews/check-design-citations.py --since 8a9d63c
DESIGN.md is byte-identical to 8a9d63c. No citation can have moved.
```

`8a9d63c` is the commit that changed `docs/DESIGN.md`, and the one commit after it
(`a27597d`) leaves the file untouched, so the SHA stays valid as later work lands on the
branch. `docs/DESIGN.md` went **2045 -> 2113 lines**.

**Two live artifacts declare the frozen SHA and both are updated:**
`docs/reviews/check-design-citation-shape.py:70` (`--sha` default) and
`docs/reviews/check-design-citations.py` (its `--since` example and its prose). Everything
else naming `c15b138` is a RECORD - a brief, a worklog, a review, an ADR - and correctly
names the design it was written against. One live source comment,
`src/fast_mcp_jobvite/models/fencing.py:25`, names `c15b138` inside a historical narrative
about a citation that was in the wrong file; I checked its claim still holds at `8a9d63c`
(`DESIGN.md:881-886` is still the `JOBVITE_HTTP_TOKENS` paragraph) and left it, because
re-stamping a sentence about what was true in the past would make it false.

---

## The ten, one line each

| ADR | what landed | where |
|---|---|---|
| 0023 | **no design change**, per its own Ruling; its self-contradicting bullet REMOVED | `docs/adr/0023` |
| 0024 | the two bounds, ceiling **in RECORDS not pages** | §4.5, after the paging rule |
| 0025 | **HELD - needs your ruling.** Nothing written. See below | - |
| 0026 | `JobviteClient` installs the filter, idempotent, opt-out keyword, `httpx2` | §4.1 |
| 0027 | `JOBVITE_OUTBOUND_BUDGET_SECONDS` + **all five other artifacts** | §10.1 + 5 files |
| 0028 | `sampling` -> `mrtr`, two design sites **and the code** | §5.3, §8 arm, `approval.py` |
| 0030 | the retry hint bullet | §4.3, after `:363` |
| 0031 | the eighth registry row + the shared-slug paragraph | §5.1 |
| 0032 | `DereferenceRefs` adopted, C2 heading, row **C2-T2 L/L -> Low** | §7.7, §11 |
| 0033 | `approval_state`'s four values as a closed set | §5.3 |

All six rulings (R1-R6) applied as ruled. I found no evidence contradicting any of them.
R5 in particular: **§13's deviation list was NOT grown.** Its header says *"The eleven
required at freeze"* and that is a boundary, not a gap.

---

## ADR-0025 - I STOPPED, AND THE REASON IS BIGGER THAN THE BRIEF SAID

The brief told me Q1 contradicts `jobvite_client.py:2046-2049`. It does. **It also
contradicts the frozen design**, which the brief did not know.

That code's comment cites `DESIGN.md:434-436` as its authority and **the citation
resolves**. Whole sentence, `git show c15b138:docs/DESIGN.md`, `grep -n`:

> Offset-based, `start` and `count`. Page cap **500** on v2, **1000** on `/v1/jobFeed`. These
> are the *transport* limits. The *result* limit returned to a model is separate and
> configurable (§7.7); the two are related by `min(transport_cap, configured_result_cap)`.

ADR-0025's Q1 ruling rests on *"the design stated no policy and an implementation must not
invent one. The design now states one."* **That premise is false as written.** §4.5 stated
one, the code implements it, and Q1 reverses it. U6's deleted branch was not filling a
vacuum - it was contradicting §4.5, which is a stronger reason for deleting it than the one
recorded.

So applying Q1 is not a paragraph: it is amending a frozen sentence three ADRs and several
tests cite, changing `scan()`, rewriting a comment that currently argues FOR the shipped
behaviour, tests, and a harness row. **I asked and did not choose.** Three options went to
the orchestrator; my recommendation is **(A) narrow the ruling** - withdraw Q1 to its own
unit and apply Q2/Q3 now - because it is the only one that keeps #95 a documentation batch
and leaves no line of the design disagreeing with the code.

**Q2 and Q3 are also unwritten**, because they are in the same ADR and I did not want to
half-apply it under a ruling that may narrow. Both are ready to go the moment Q1 is settled:

- **Q2, per-process throttle** - stands on its own argument and I found nothing against it.
- **Q3** - the "budget is per-invocation" half is ALREADY at `DESIGN.md:392-394` (new
  numbering) and must not be written twice, exactly as the ruling says. The open half,
  *"throttle waiting spends the budget"*, describes a mechanism **that does not exist**:
  `grep -rn outbound_rate_limit src/` returns the declaration at `config.py:228` and a
  comment at `jobvite_client.py:579` saying what it is not. I intended to write it as a
  constraint on whoever implements the throttle rather than as a description of present
  behaviour, and flagged that for confirmation.

---

## The citation surface, measured, with the command beside every number

**THE BRIEF'S NAMED LIST OF DIRECTORIES IS INCOMPLETE, and this is my second finding.** Its
census names seven directories. I enumerated the CONTAINER instead:

```
$ grep -rno 'DESIGN\.md:[0-9]' --exclude-dir=.git . | sed 's|^\./||; s|/[^/]*$||' \
    | sort | uniq -c | sort -rn
```

Per directory, at `06a4359`, unit = OCCURRENCES (a line can carry two):

| directory | occurrences | in the brief's list? |
|---|---|---|
| `docs/reviews` | 532 | yes |
| `src` | 388 | yes |
| `tests` | 347 | yes |
| `docs/worklogs` | 215 | yes |
| `scripts` | 134 | yes |
| `docs/adr` | 62 | yes |
| `docs/briefs` | 46 | yes |
| **`docs/plans`** | **111** | **NO** |
| **`.github/workflows`** | **20** | **NO** |
| **`pyproject.toml`** | **11** | **NO** |
| **`.pre-commit-config.yaml`** | **5** | **NO** |
| **`CHANGELOG.md`** | **2** | **NO** |
| **`.env.example`** | **1** | **NO** |
| **`docs/research`** | **1** | **NO** |
| **`docs/CODE-REVIEW-CHECKLIST.md`** | **1** | **NO** |

**152 occurrences live outside the brief's list.** This is the hand-kept-list-beside-its-
container shape, in the brief whose own subject is that hand-kept numbers decay.

### What I repointed, and what I did not

**708 occurrences repointed mechanically + 8 by hand = 716**, across `src`, `tests`,
`scripts`, `pyproject.toml`, `.pre-commit-config.yaml` and `.env.example`.

| target | moved and repointed |
|---|---|
| `src/**` | 297 |
| `tests/**` | 287 |
| `scripts/` | 108 |
| `pyproject.toml` | 10 |
| `.pre-commit-config.yaml` | 5 |
| `.env.example` | 1 |
| **total mechanical** | **708** |
| plus by-hand, subject-anchored | 8 |

**`docs/briefs/` got ZERO repoints, and that is the correct answer rather than an omission.**
I derived the live set against the board: every brief carrying a citation belongs to a
`completed` task, so every one is a RECORD. The single exception is `ADR-BATCH.md` itself,
which is live and which the brief forbids repointing because it quotes citations precisely
because they are wrong. `PREAMBLE.md` carries zero.

**`.github/workflows/ci.yml` is NOT repointed and 18 of its 20 citations are now STALE.**
The brief says do not touch it, so I did not - but this is a live file, not a record, and
stale pointers there mislead the next reader. The repoint map for it is reproducible in one
command (below). **This needs you.**

`docs/plans`, `docs/adr`, `docs/worklogs`, `docs/reviews`, `CHANGELOG.md`, `docs/research`
and `docs/CODE-REVIEW-CHECKLIST.md` were left as written, as records.

### How the two numbers were made to agree - and they are not the same instrument

**`scripts/adr-batch-repoint.py`** builds an old-line -> new-line map with
`difflib.SequenceMatcher` and **refuses to rewrite any citation whose subject line was
itself edited**, reporting it `MANUAL` instead. A mapped-but-changed line is exactly the
shape that resolves green while pointing at different words.

**`scripts/adr-batch-verify-repoint.py`** then checks the result on a **different join**:
for every citation it pairs the number the file carried BEFORE with the number it carries
NOW, and asserts

    old_design[old_start:old_end] == new_design[new_start:new_end]

**Re-running the mapper over already-repointed files would have been the wrong check** and I
nearly shipped it: it re-maps the new numbers as if they were old ones and prints a
confident, meaningless agreement with itself. I caught that because its output was
implausibly clean.

```
$ python3 scripts/adr-batch-verify-repoint.py 06a4359 c15b138 $(git diff --name-only ...)
checked=868  widened=26  failed=10
```

`checked=868` is the join's own count of citation pairs and it is what makes the two numbers
agree: every citation present before is present after, at a number whose text matches.

---

## THE SOURCE-INWARD AUDIT, and what it found

A green checker does not prove a citation still covers its subject, so the verifier
classifies each pair into three outcomes rather than pass/fail:

- **`WIDENED`** - the citer's lines are still a contiguous run inside the new range. 0 of
  these, which surprised me until I understood the next one.
- **`ABSORBED` - 26.** My insertions landed **inside** cited ranges rather than around them.
  Every line the citer read is still covered, in order, but no longer adjacent. Nothing fell
  outside; the range now says more than its author did. Recorded, not silently passed.
- **`FAILED` - 10.** The cited TEXT itself changed. **No line number is the right answer
  here**, and these are the audit's real output.

**All ten read, and four of them were prose asserting something the batch had just made
false.** These are rewritten in place, never annotated:

1. **`src/fast_mcp_jobvite/errors.py` `ApprovalRefusedError`** said the registry *"has no row
   for an approval refusal"* and that it *"is not settled by an ADR because the design is
   frozen"*. ADR-0031 added the row. Both claims rewritten.
2. **`tests/test_server.py:243-250`** said C2 *"was written against a stack that is not the
   one that runs"*, present tense. ADR-0032 reconciled it.
3. **`tests/test_http_hardening.py:88-98`** said the live stack is *"not the three DESIGN.md
   §7.7 enumerates"*. §7.7 now enumerates four.
4. **`src/fast_mcp_jobvite/approval.py` `ApprovalState`** said *"These three values"* while
   declaring **four**, and framed itself as deliberately unsettled. ADR-0033 settled it. The
   replacement carries no count at all, so it cannot go stale on a fifth value.

**And one the mechanical pass got RIGHT in the wrong way.** `errors.py` cited
`DESIGN.md:509`, which ADR-0031's audit had already measured as one line off - the sentence
is on `:510`. The repointer faithfully carried the off-by-one forward to `:540`, which
resolves, is inside the same bullet list, and is the WRONG SENTENCE (`:540` is the 502
sentence; `:541-542` is the type-URI-is-a-contract sentence the docstring is citing).
`errors.py:67` in the same file already said `:541-542` for the same claim. **A mechanical
repoint preserves an error rather than fixing it, and the checker cannot see the
difference.** Corrected to `:541-542`.

**A fourth wrong ADR reference, not in the brief's list of three.** ADR-0024 says twice that
**§7.3** should name the bound. §7.3 is *Configuration*. The sentence ADR-0024 quotes,
`DESIGN.md:486-487`, is in **§4.5 Pagination**, which is where the bound landed. Corrected
in place. **ADR-0025 has the same defect** (`§7.3` twice, once in a table's "Where" column)
and I left it, because 0025 is held pending your ruling and I did not want to edit an ADR
whose Decision may be narrowed.

### The three wrong ADR citations from the brief, all fixed

- **`DESIGN.md:1276-1278` at four sites** (`0021:17`, `0028:27`, `0028:61`, `0028:102`),
  where `sampling` is on `:1280`. All four widened to `:1276-1280` in `c15b138`'s numbering,
  because an ADR quotes the design it amends. **I ruled on `0021:17` rather than leaving it
  neither fixed nor explained:** a wrong citation is wrong regardless of the ADR's status,
  and leaving it means the next reader inherits it.
- **`test_repo_hygiene.py:81` at two sites** (`0027:35`, `0027:56`) -> `:82`.
- **`DESIGN.md:509` at one site** (`0031:28`) -> `:510`.

---

## Things I did that the brief did not name, each with why

**1. ADR-0028's code half.** Its ruling requires the design and code to land together and
explicitly forbids renaming the value while leaving the comment that documents the old
mismatch. Applying only the design would have left `approval_mechanism` emitting `"sampling"`
against a design naming `mrtr` - the precise thing the brief forbids for ADR-0025.
`SAMPLING` -> `MRTR` in `approval.py`, both era-parameterised expectations, and **the M18
mutation anchor in `scripts/check-u10-write-controls.sh:359`**, which is a literal string: a
stale anchor there would have made that harness row a silent no-op at exit 0.

**2. ADR-0027's other five artifacts (task #60).** Not a choice. Naming the variable in §10.1
alone turned the suite red:

```
FAILED tests/test_config.py::test_env_example_and_design_declare_the_same_variables
E     Extra items in the right set: 'JOBVITE_OUTBOUND_BUDGET_SECONDS'
```

That is the closed-set test refusing a subset exactly as designed, and I will not hand back a
red branch. Settings field, `.env.example`, README row, `server.json` entry, all three client
factories. `test_repo_hygiene`'s `== 15` is now **derived from `Settings.model_fields`** per
ADR-0027's ruling, never bumped.

**Proved able to fail, both arms, with `PYTHONDONTWRITEBYTECODE=1` and `cmp` against a
backup rather than `grep`:**

| arm | what was amputated | result |
|---|---|---|
| A1 | the `Settings` field itself | **RED** - design names a variable `Settings` does not |
| A2 | the parser's body, so it returns `{}` | **RED** - caught only by the `> 1` control |

A2 is why the equality is paired with a control: **two empty sets are equal**, so the
equality alone would pass against a parser that matched nothing.

**3. One README correction.** `README.md` said `JOBVITE_OUTBOUND_RATE_LIMIT` is *"requests per
second"*. The design, `server.json` and ADR-0025 all say **per minute**. Fixed while adding
the row beneath it.

---

## The gate - every number read from its own exit code, floors grepped not retyped

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 868
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 458
```

| gate | exit | number |
|---|---|---|
| `uv run --frozen pytest` | **0** | **868 passed, 6 deselected, 0 skipped** |
| `check-suite-floor.sh 868` (fed pytest's output on stdin) | **0** | `suite floor OK: 868 passed, floor 868` |
| `uv run --frozen mypy` | **0** | `no issues found in 96 source files` |
| `uv run --frozen ruff format --check .` | **0** | 105 files |
| `uv lock --check` | **0** | - |
| `check-harness-anchors.py --self-check --floor 458` | **0** | 458 anchors |
| `check-design-citations.py` | **0** | - |
| `check-design-citation-shape.py` | **0** | 872 citations vs `8a9d63c`, 2113 lines |
| `check-cross-references.py` | **0** | - |
| `check-standards-citations.py` | **0** | - |
| `check-obligations.py` | **0** | 31 mappings, 25 verified, 6 recorded absent |
| `uv run --frozen ruff check .` | **1** | **15 errors - byte-identical to `06a4359`** |

**On the one red.** `ruff check .` exits 1 on `06a4359` too, with the same 15 errors in the
same two files (`docs/reviews/check-coupling-controls.py` 14, `check-coupling.py` 1). I
measured base explicitly rather than assuming. **This branch adds none** - it briefly added
67 (60 W505 doc-lines, plus B023/S603/S607), every one of which is fixed. Twelve of those 60
were not mine to write: **the repoint itself pushed doc lines over the 72-column rule**, by
turning a three-digit citation into a four-digit one. That is a consequence of a re-freeze
that nothing in the brief anticipates and that a future re-freeze will hit again.

**The shape checker has a positive control**, because a checker repointed at a new SHA that
exits 0 is indistinguishable from one that has stopped looking:

```
$ python3 docs/reviews/check-design-citation-shape.py            # default now 8a9d63c
0 citation(s) point at something that cannot be their subject.   -> EXIT 0
$ python3 docs/reviews/check-design-citation-shape.py --sha c15b138
   3  only a fence or table separator
  87  starts on a BLANK line (the off-by-one shape)               -> EXIT 1
```

It can still fail. It is passing because the citations are right, not because it stopped.

**One instrument error worth recording.** My first run of the four checkers used
`python3 docs/reviews/$c.py || python3 scripts/$c.py`, and reported `$?` from the FALLBACK.
The shape checker's real exit 1 was replaced by an ENOENT 2 from a path that does not exist.
`check-suite-floor.sh` separately reported a false red because I gave it no stdin. **Both
looked like findings about the branch and were findings about my invocation.** Every number
above comes from a re-run with one command per line.

---

## Suggested fixes for everything I could not fix myself

1. **ADR-0025 Q1** - pick (A), (B) or (C) from my message. Recommendation: **(A)**, and
   correct 0025's Q1 reason in place either way, since *"the design stated no policy"* is
   measurably false at `DESIGN.md:434-436`.
2. **`ci.yml`'s 18 stale citations** - I am forbidden to touch the file. The map is one
   command from a checkout of this branch:
   `python3 scripts/adr-batch-repoint.py --old <(git show c15b138:docs/DESIGN.md) --new docs/DESIGN.md --report .github`
   Better durable fix: `ci.yml`'s citations are comments, so **replace the line numbers with
   subject phrases**, the same remedy `docs/OBLIGATIONS.md` already adopted at `afaf226`.
   Then a re-freeze cannot stale them at all.
3. **The brief's directory list** - replace the seven-name list in `ADR-BATCH.md` with the
   container enumeration above, so the next re-freeze cannot miss `docs/plans` (111) the way
   this one nearly did.
4. **The 72-column rule vs. re-freezes** - a re-freeze that adds a digit to a citation breaks
   W505 in files nobody edited. Cheapest fix: run `ruff check --select W505` as part of any
   repoint and rewrap what it names, and say so in the brief.
5. **`ruff check .` is red on main** with 15 pre-existing errors. Not mine, not in scope,
   worth a task: it means the lint gate has been failing and the signal is being read as
   noise.
6. **ADR-0025's `§7.3`** - two references to *Configuration* for a Pagination subject. Fix
   when its ruling is settled, in the same edit.
7. **`docs/plans/IMPLEMENTATION-PLAN.md`** carries 111 citations and was left as a record.
   If it is actually a live document rather than a historical one, it needs a repoint and
   that is a decision, not a default.

---

## What I did NOT verify

These are things I could not settle, not things I skipped.

- **Whether ADR-0025's Q2 and Q3 are right.** I read both arguments and found nothing
  against them, but I did not write them, so nothing about them is tested.
- **`ci.yml` steps.** The brief forbids touching the file and I suggest no new step, so
  there was nothing to run. The two floors I consume are read FROM it at run time.
- **Whether the design's new prose is CORRECT, as opposed to faithful to its ADR.** I
  verified every sentence I wrote against its ruling and against the code it describes. I
  did not review the rulings themselves - the brief says verify, not re-open, and I found no
  contradicting evidence except ADR-0025 Q1, which is reported above.
- **The 26 `ABSORBED` citations one by one.** The verifier proves mechanically that every
  cited line is still inside its range, in order. I did not read all 26 citing passages to
  ask whether the newly-adjacent material changes what the citation implies. That is a
  reader's judgement over 26 sites and it is the natural scope of the review round that
  follows this.
- **`docs/plans`, `docs/adr`, `docs/worklogs`, `docs/reviews`** - left as records by
  instruction. I did not check whether any of them is in fact a live pointer someone is
  about to follow. `docs/plans` at 111 occurrences is the one I would look at first.
- **Runtime behaviour of the new `JOBVITE_OUTBOUND_BUDGET_SECONDS` wiring beyond the suite.**
  The three factories now pass it and the tests pass, but nothing exercises a non-default
  value end to end against a live budget expiry. The client already had the parameter and
  its own tests; what is new is only that `Settings` reaches it.

**Worktree:** `/tmp/adr-batch-work`, removed after this report was committed.
