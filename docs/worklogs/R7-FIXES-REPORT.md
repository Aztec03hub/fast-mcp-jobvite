# R7-FIXES - closing R7 over U8, U9, U12 and U10

**Branch `fix/r7-findings`, based at `03c4ae6`.** Worktree `/tmp/r7-fixes-work`, created with
`git worktree add` at that SHA. The shared checkout was never touched and no branch was switched.

**Design read as `git show c15b138:docs/DESIGN.md`,** never from a working tree. Nothing here edits
it; the two places where a finding pressed on it are raised as tasks.

**H2 was NOT mine** - `scripts/check-u9-http-controls.sh` is untouched on this branch, and I needed
nothing from it.

---

## Floors, DERIVED from `ci.yml`, never retyped

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 663
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 371
```

## The numbers, read from the terminal

| | Before | After |
|---|---|---|
| `uv run --frozen pytest` | **663 passed**, 0 skipped, 6 deselected, exit 0 | **674 passed**, 0 skipped, 6 deselected, exit 0 |
| `check-harness-anchors.py --self-check --floor 371` | - | **371 anchors resolved**, exit 0 |

**674 against a floor of 663: +11, and 0 skipped.** The eleven are H1 +2, M1 +2, M2 +1, M3 +2,
M4 +2, L3 +1, L4 +1. H3, L1 and L2 rewrote existing cases rather than adding any.

---

# Per finding

## H1 (HIGH) - the payload-logging middleware. FIXED, mutation KILLED.

**BEFORE.** Reproduced rather than taken from the report. R7's M4 adds
`LoggingMiddleware(include_payloads=True)` to `build_middleware`. Anchor asserted unique (1),
mutation proved landed by `cmp` against a backup:

```
tests/test_http_hardening.py -> 29 passed, PYTEST_EXIT=0     SURVIVES
```

**I independently enumerated the container two ways before trusting either.** Importing every module
under `fastmcp.server.middleware` and collecting `Middleware` subclasses returns **15**. Cross-checked
against a grep for `^class ...(Middleware)` over the installed package: 12 direct subclasses plus 3
via `BaseLoggingMiddleware` is the same 15. This matters because a discovery walk that silently
returns a short list gives a green meaning nothing.

**CHANGED.** Two assertions in `tests/test_http_hardening.py`:

- the built stack **EQUALS** its expected set, on both transports. Subset was the whole defect.
- every discovered framework middleware is classified: `discovered == ADOPTED | EXCLUDED |
  FRAMEWORK_INJECTED | UNCLASSIFIED`. `discovered_middleware()` walks the package's own `__path__`.

Two positive controls run **first**, as the brief required: the discovered count must exceed what the
two hand-kept lists name, and `LoggingMiddleware` - the class M4 adds - must be in the discovered set.

**AFTER.** M4 re-applied, proved landed by `cmp`:

```
tests/test_http_hardening.py -> 1 failed, 30 passed, PYTEST_EXIT=1     KILLED
```

Restored, `cmp` identical, `git diff -- src/` empty. **H1's fix is tests-only.**

**R7's suggested fix SURVIVED contact**, in shape. Two departures, both deliberate:

1. R7 proposed `ADOPTED_MIDDLEWARE | {"RequestIdMiddleware"}` as the expected stack. That is
   **wrong against the live tree** - see below.
2. R7 suggested keeping `EXCLUDED_MIDDLEWARE` as documentation and adding a second assertion. I did,
   but the seven ungoverned classes needed a home that is not `EXCLUDED_MIDDLEWARE`: those five carry
   measured ADR-0004 reasons, and quietly adding seven unassessed names beside them would have made
   the constant lie.

### And the equality assertion found a live one on its FIRST run

It failed on the **clean tree**. `DereferenceRefsMiddleware` is in the production stack on both
transports. `FastMCP.__init__` appends it whenever `dereference_schemas` is true and it defaults to
true (`.venv/.../fastmcp/server/server.py:477-482`, `:301`), so the running stack is four framework
middleware and ours - not the three `DESIGN.md` §7.7 enumerates, and not the three the C2 threat-model
heading at `DESIGN.md:1725` names as the stack it analysed. Before this branch the class appeared
**nowhere** in the repository.

R7 counted it among the "seven in neither list" but treated all seven as possible future additions.
One of them was already running. Neither existing assertion could see it: subset cannot notice an
addition, and intersection-with-excluded is empty for anything never listed.

Raised as task **#78**, which has since been **ruled as ADR-0032 (Accepted)** with a C2 row added.
Pinned meanwhile in `FRAMEWORK_INJECTED_MIDDLEWARE` so a bump injecting a second one is a red test.

## H2 - NOT MINE. Untouched.

## H3 (HIGH) - the approval tripwire's blind spot. FIXED, 6/6 -> 0/6, measured per part.

**BEFORE.** Reproduced against the real function, all six of R7's evasions: **6/6 MISSED**.

**The three parts were measured separately, as the brief asked.**

| | evasions | new false positives on the scanned files |
|---|---|---|
| baseline | 6/6 missed | - |
| **+ part 1** (negator scoped to the claim's own clause) | **3/6 missed** | **0** |
| **+ part 3** (claim forms widened) | **0/6 missed** | 1, and it was mine - see below |
| **+ part 2** (scope derived from containers) | 0/6 | 0 |

**Part 1.** `_NEGATION_WINDOW = 160` replaced by `_CLAUSE_BOUNDARY`. A comma is deliberately not a
boundary, because *"we never claim X, only that a response came back"* is one clause and the negator
governs all of it - that denial is an arm of the positive control. R7 asked whoever landed this to run
it over the four files first and read every new hit: **zero new hits**.

**Part 3.** Claimants, verbs and the articled forms are now DERIVED from one tuple of bare nouns.
**And it caught its own author within minutes.** My first draft of the comment explaining the
hyphenated form spelt that form out in full as an illustration, and the scanner reported the comment -
this file's own header warning about "a checker with a hole exactly where its author was standing",
arriving on schedule. The comment is now assembled like everything else.

**Part 2 - R7's suggestion here did NOT survive, and neither did my first instinct.**

R7 proposed deriving the owned list from `git log` over the U10 commits. I did not use it: a squash
merge collapses the history it reads.

I then measured the stronger option - scan the whole repository - and **rejected it on the
measurement**. All 243 tracked `.py`/`.md` files report **18 hits**, every one benign: `README.md`,
this repository's own review and brief documents, and `FASTMCP-SPIKE-4.md` all quote the forbidden
phrasing in order to forbid it. So the rule governs documents that ASSERT how the system behaves, not
documents that discuss the rule, and `docs/reviews`, `docs/briefs` and `docs/research` are out of
scope **by measurement**. That measurement is now in the docstring.

What landed instead: three **containers** plus this file - all of `src/`, all of `docs/adr/`, all of
`docs/worklogs/`. **4 files -> 83.** This closes both files R7 found missing (`errors.py` and
ADR-0028) and the next file nobody thinks to add. Two guards on the derivation, because a glob at a
path that stopped resolving returns empty and the case would pass having read nothing: a floor of 40,
and a positive control asserting R7's two named files are inside what the containers produce.

**AFTER, and the ratchet.** The six evasions are now arms of the positive control. Amputation:
restoring the 160-character window fails `test_positive_control_the_wording_tripwire_can_actually_fire`,
exit 1. Landed and restored by `cmp`.

## M1 (MEDIUM) - three dual-declared pydantic defaults. FIXED, mutation KILLED.

**BEFORE.** R7's M1 sets the inert `Field(default=None)` copy on `SearchJobsInput.ids` to
`"R7MUTANT"`. Landed by `cmp`, **full suite 665 passed, exit 0. SURVIVES.**

**THE POPULATION, enumerated by machine as the brief required.** An AST walk over every annotated
field of every class in all **88** `.py` files finds exactly **3**, all in `tools/jobs.py`:
`:121`, `:458`, `:470`. **There is no fourth.** `tools/candidates.py` is clean because U10's M9 fix
repaired it - and that fix left a note reading *"these three fields"* beside the three it repaired,
which is exactly why the three in the sibling file went unfound for six units. The note was the
sibling check, and a note is not one.

**CHANGED.** Three deletions, plus the walk itself as a test in `tests/test_repo_hygiene.py`,
enumerating the container rather than listing known offenders beside it.

**AFTER.** R7's M1 can no longer be expressed - the inert copy it mutates does not exist. So the
mutation was re-expressed as its inverse: re-introducing a dual default on `ids` fails
`test_no_field_declares_its_default_twice`, naming `src/fast_mcp_jobvite/tools/jobs.py:121`, exit 1.
Landed and restored by `cmp`. Paired with a positive control asserting the walk really reached
`SearchJobsInput`, `GetJobFeedInput` and `CreateCandidateInput`.

**R7's suggested fix SURVIVED**, including its recommendation to make the scan permanent.

## M2 (MEDIUM) - the page cap's literal-substring scan. FIXED, mutation KILLED.

**BEFORE.** R7's M3 inserts a real reimplementation spelt `_LOCAL_TRANSPORT_CAP = 1_000`. Landed by
`cmp`, `test_tools_job_feed.py` + `test_tools_jobs.py` -> **68 passed, exit 0. SURVIVES.**

**CHANGED.** The module is parsed with `ast` and every numeric literal compared **by value** against
`JOBFEED_PAGE_CAP`, **imported** from the client that declares it rather than typed - a hand-typed
`1000` here would be a second declaration of the value inside the test written to forbid second
declarations of it.

**AFTER.** Three mutations, each proved landed and restored:

| spelling | result |
|---|---|
| `1_000` (R7's M3) | 1 failed, exit 1 - **KILLED** |
| `[0:1000]` | 1 failed, exit 1 - **KILLED** |
| `0x3E8` | 1 failed, exit 1 - **KILLED** |

**With the positive control R7 warned about**: the same walk is pointed at
`services/jobvite_client.py` and must find the cap there, because an `ast` walk that finds nothing
also passes. **R7's suggested fix SURVIVED.**

## M3 (MEDIUM) - U12's caller-visible arm. BUILT. **My first amputation was WRONG.**

**BEFORE.** No leak, confirmed by driving it rather than reading: the caller receives
`/problems/service-unavailable` whose `detail` is enumerated prose. A missing ratchet, not an escape -
the finding says so and I confirmed it.

**CHANGED.** Two parametrized arms, `read_timeout` and `connect_error`, with **three** positive halves
before any absence is believed: the probe URL really carries the secret, the exception really carries
it, and the call really failed. Asserts the VALUE `f"sc={FEED_SECRET}"`, never the bare `"sc="` token.

**AFTER, and this is the part worth reading.** My first amputation - making `problem_from_exception`
return `str(exc.__cause__ or exc)`, my guess at the R2-M5/L1 shape - **SURVIVED**: 28 passed, exit 0,
landed by `cmp`. The transport error is raised `from None`, so `__cause__` is unset and `str(exc)` IS
the enumerated detail. **My mutation was wrong, not the arm**, and the way to tell them apart was to
print what the caller actually receives rather than to trust either.

The real edit-away site is `jobvite_client.py:1834`. Amputating `_unavailable_detail` to
`f"{type(exc).__name__}: {exc}"` fails **both** arms, exit 1. Landed and restored by `cmp`,
`git diff --quiet -- src/` clean.

**R7's suggested arm SURVIVED** - its sketch and its warning about the value-not-token assertion were
both right.

## M4 (MEDIUM) - `send_email` redacted. APPLIED. **R7's status line was wrong and the brief was right.**

**BEFORE.** Verified with `git show ad948b3:src/fast_mcp_jobvite/utils/redaction.py`: `send_email`
appears **nowhere**. R7 marks this its one executed fix, *"RUN, and it is safe"*. The measurement
existed; the code did not. R7 was read-only on `src/`, measured it in its worktree and correctly
reverted - the wording is what misleads.

**CHANGED.** `"send_email"` admitted, **and the admission rule widened with it**. The rule read
"structurally an identifier, a bound or a page cursor"; a bool flag is none of those, so the entry
alone would have left the list contradicting the comment directly above it - the two-lists defect at
the width of one comment, in the module that exists because `companyId` sat in two disagreeing lists
eighty lines apart. The fourth clause is guarded: a flag qualifies only when its domain is closed AND
enumerating it discloses nothing about a candidate. `query` is a single value too and is still absent.

**AFTER.** A parametrized arm over `True` and `False`. **Both directions, because R7 measured it
unpinned in both** - no test asserted the value was recorded and none asserted it was redacted, so the
old behaviour was held in place by nothing. It also asserts the three PII arguments beside it are
still `[REDACTED:str]`, so admitting this key cannot quietly admit its neighbours.

Amputation: removing the entry fails both arms, exit 1.

**There was no design tension, and I manufactured one by reading half a sentence.** I raised
`DESIGN.md:1072` against C1-T1 as task **#82**. It was ruled with no ADR needed, because the clause
in full reads *"is also an argument like any other **and is subject to §2.1's schema rules**; it
defaults to `false` (§2.2)"* - scoped to the input model's schema and defaulting, silent on the
audit surface. **A citation trimmed at the comma became a conflict that does not exist**, and it
travelled through R7's report, my task and my first code comment before anyone quoted the sentence
whole.

Read from `git show c15b138:docs/DESIGN.md` myself rather than taken on report:
`DESIGN.md:1070-1071` already requires the elicitation payload to name *"**whether `send_email` is
true**, in those terms"*. **The design mandates showing this value to the approver**, so redacting
it from the record of what was approved was the incoherent half. The change is consistent with an
existing requirement, not a widening of one - which is a better justification than the one I
originally wrote, and I only have it because the half-sentence was caught.

**The admission-rule widening stands**, and is not a licence: the next flag proposed for that list
gets both questions asked out loud, and *"it is a bool"* is not on its own an answer - `approve` is
also a bool and belongs nowhere near it. That sentence is now in the code beside the entry.

## L1 (NIT) - the guard that never called its subject. REWRITTEN.

**BEFORE.** Confirmed: the body reached only `observed_protocol_version` and never
`resolve_approval`. Its two "trap" assertions compared two fakes the test builds from the **same**
hardcoded literals - a literal equalling itself. Swapping the discriminator changes neither literal,
so the refactor its docstring claims to stop would have passed.

**CHANGED.** Drives `resolve_approval` and asserts the two eras resolve to different mechanisms
(`SAMPLING` vs `ELICITATION`), then the **negative control** R7 asked for: make `transport` and
`session_id` DIFFER and require the mechanisms unchanged.

**The name is kept verbatim.** It is a harness anchor - `scripts/check-u10-write-controls.sh:192`
names it - and `async` pushes it one character over the line limit. Shortening it to satisfy a linter
would have silently unhooked the row that proves this case can fail. The `noqa` records why.

**R7's suggested fix SURVIVED**, negative control included.

## L2 (NIT) - one of four values, and only `arguments`. FIXED.

Now every value in `VALID_ARGS`, against the whole event rather than one field. **Amputation:**
admitting `first_name` to `NON_SENSITIVE_ARGUMENT_KEYS` - a value the old form ignored - fails it,
exit 1. So the widening is not decorative.

## L3 (NIT) - a recorded value this suite cannot produce. FIXED, and R7 was RIGHT but INCOMPLETE.

**Measured myself** against the real `Context` on the in-memory transport:

```
mode auto     transport = None   session_id = '728ce0eb-...'   pv = '2026-07-28'
mode legacy   transport = None   session_id = '960c1569-...'   pv = '2025-11-25'
transport EQUAL across eras: True     session_id EQUAL across eras: False
```

Confirms R7: `ctx.transport` is `None` in-process, not `'streamable-http'`. The claim's substance
holds - identical either way, so the trap is real on both transports.

**The prose is REWRITTEN in place, not appended to**, and the second half is corrected too, which R7
noted and which matters more: real `session_id`s **differ** on every connection. It is *"populated on
both"* that makes it useless as a discriminator, never that it is equal - a session_id-keyed guard
would fail loudly rather than quietly. The fake makes them equal, which is a convenience of the fake
that was being read as an observation about the framework.

The fakes keep `'streamable-http'` deliberately, now saying it is the deployed value they stand in
for, and `test_the_traps_agree_on_the_real_context` pins the in-process observation so fake and
framework cannot drift apart unnoticed. It carries a positive control first: the two eras must really
report different protocol versions, or the agreement it asserts is between two identical calls.

## L4 (NIT) - the drained client's connection-level lockout. BUILT.

Two properties in one sequence: the bucket is keyed to the TOKEN (a drained client cannot reset its
quota by reconnecting), and a bystander connecting at the same moment is unaffected - which is what
separates "this client is locked out" from "the server stopped accepting connections". The refusal is
also checked for what it must NOT contain: the bearer token absent, `token_client_id`'s digest
present.

Sequential and single-client, like every limiter measurement in this file. Behaviour under
simultaneous callers stays unverified; `U9-IMPL-REPORT.md:294` and ADR-0002:44 both say so, R7 did not
settle it, and this arm does not claim to.

---

# R7's suggested fixes: which survived contact

| Finding | R7's fix | Verdict |
|---|---|---|
| H1 | discover subclasses, assert equality, second accounting assertion | **SURVIVED** in shape. Its literal expected-set was **WRONG against the live tree** - it omits the framework-injected `DereferenceRefsMiddleware`. Its "keep EXCLUDED as documentation" needed a separate constant for the unassessed seven. |
| H3 part 1 | clause-scoped negators | **SURVIVED.** 6/6 -> 3/6, zero false positives. |
| H3 part 2 | add two paths; derive the list from `git log` | **DID NOT SURVIVE.** A squash merge collapses the history it reads. Replaced with container enumeration; repo-wide was measured and rejected at 18 benign hits. |
| H3 part 3 | widen claimants and verb forms | **SURVIVED.** 3/6 -> 0/6. |
| M1 | delete the three, make the AST scan permanent | **SURVIVED**, both halves. |
| M2 | match on value via `ast`, with a found-the-real-one control | **SURVIVED.** |
| M3 | the arm as sketched, asserting the value not the token | **SURVIVED.** |
| M4 | add the key, widen the rule's sentence, pair with an arm | **SURVIVED.** Its **status line did not**: "RUN, and it is safe" was not in `main`. |
| L1 | drive `resolve_approval`, add a negative control | **SURVIVED.** |
| L2 | check all four values, serialise the whole event | **SURVIVED.** |
| L3 | reword `approval.py`, fix the fake | **SURVIVED**, and understated - the `session_id` half needed correcting too. |
| L4 | one arm, drained reconnect plus bystander | **SURVIVED.** |

**Three did not survive as written:** H3 part 2's `git log` derivation, H1's literal expected-set, and
M4's claim to be landed. My own first M3 amputation was also wrong, and I have said so above rather
than quietly replacing it.

---

# Gates, each judged by exit code on its own line

```
uv lock --check                                    EXIT=0   Resolved 120 packages
uv run --frozen ruff check .                       EXIT=0   All checks passed!
uv run --frozen ruff format --check .              EXIT=0   69 files already formatted
uv run --frozen mypy                               EXIT=0   57 source files
uv run --frozen pytest                             EXIT=0   674 passed, 0 skipped, 6 deselected
python3 scripts/check-harness-anchors.py --self-check --floor 371
                                                   EXIT=0   371 anchors resolved
bash scripts/check-harness-anchors-controls.sh     EXIT=0
uv run --frozen python docs/reviews/check-quickstart.py     EXIT=0
python3 scripts/check-committed-file-types.py --all         EXIT=0
docs/reviews/check-coupling.py docs/DESIGN.md      EXIT=0
docs/reviews/check-cross-references.py             EXIT=0
docs/reviews/check-coupling-controls.py            EXIT=0
docs/reviews/check-coupling-sweep.py               EXIT=0
docs/reviews/check-obligations.py                  EXIT=0
docs/reviews/check-obligations.py --controls       EXIT=0
docs/reviews/check-plan-measurements.py            EXIT=0
docs/reviews/check-resweep-verdicts.py             EXIT=0
```

**mypy found a real defect in my own M1 walk** (`"AST" has no attribute "keywords"` - an
`isinstance` in one operand does not narrow the second) that the focused runs did not, which is the
argument for running the full gate **before** folding rather than after. Fixed in its own commit; the
walk's behaviour is unchanged and its mutation still fails it.

## A KILLED HARNESS STRANDED AN AMPUTATION IN THE TREE, AND IT WAS A SECURITY ONE

**Read this before trusting any tree state on this branch.**

`check-u9-http-amputation.sh` was running in the background when the background tasks were
stopped. A killed mutation harness does not restore itself, and this one did not:

```
$ git status --porcelain
 M src/fast_mcp_jobvite/http_hardening.py

$ git diff -- src/fast_mcp_jobvite/http_hardening.py
-    if settings.mcp_transport != "http":
+    if True:
         return None
```

That is the amputation of `build_token_verifier` - `if True: return None` makes the function
return no verifier at all, so **every bearer token check on the HTTP transport is disabled**. It is
the harness doing exactly its job, frozen at the moment it was interrupted. Left in place it would
have read as an ordinary working-tree edit, and on this project a stranded mutation has already
been recorded as reading like someone else's merge.

**Found by checking `git status --porcelain` immediately on learning the tasks were killed**, not
by noticing later. Restored with `git checkout --`, then verified three ways rather than one:

```
git status --porcelain                      (empty)
git diff --quiet                            CLEAN
git diff --quiet HEAD -- src/ tests/        src/ and tests/ identical to HEAD
uv run --frozen pytest                      674 passed, 6 deselected, EXIT=0
grep -n 'if settings.mcp_transport != "http":'   216, 384   (both call sites intact)
```

**The branch is intact.** Nothing was committed while the mutation was present - the last commit
`0c432de` predates the kill and its diff is one file of my own changes.

## Harnesses re-run, over every file I touched

```
check-u10-write-controls.sh    --controls-fired                     EXIT=0   21/21 controls fired
check-u10-write-amputation.sh  --amputation --min-rows 10           EXIT=0   10 rows, 10 anchors
                                                                             applied, 396 surviving
                                                                             assertions, 0 VACUOUS
check-u12-jobfeed-controls.sh  --controls-fired --min-rows 17       EXIT=0   17/17 controls fired
check-u12-jobfeed-amputation.sh --amputation --anchors-applied      EXIT=0   10 rows, 10 anchors
                                                                             applied, 258 surviving
                                                                             assertions, 0 VACUOUS
check-u3-audit-controls.sh     --result-killed                      EXIT=0   15 killed, 0 not killed
check-u3-audit-amputation.sh   --amputation --min-rows 10           EXIT=0   915 surviving assertions
check-u9-http-controls.sh      --controls-fired                     EXIT=0   14/14 controls fired
```

**Both outstanding harnesses have since been run to completion, one at a time, on the final tree:**

```
check-u9-http-amputation.sh  --amputation --min-rows 14   EXIT=0   14 rows, 14 ANCHORS APPLIED,
                                                                   0 VACUOUS, 124 killing assertions
check-u0-test-controls.sh    --controls-fired             EXIT=0   11/11 controls fired
```

Tree checked after each, by the runner and again live: clean both times, nothing stranded.

**U0's first completed run said `10/11, exit 1`, and that was an instrument defect, not a finding.**
The FIXTURES_DIR row reported *"`test_fixtures_directory_resolves` was NOT the failing test"* while
printing `FAILED tests/test_fixture_path.py::test_fixtures_directory_resolves` twenty-seven lines
below its own verdict. That row emits **89 FAILED lines** - the largest output in the run, and
exactly the size that trips `printf | grep -q` into exit 141 under `set -o pipefail`, which is
recorded on main as its own defect and fixed there. Re-run with main's fixed
`check-u0-test-controls.sh` and `ci-harness-gate.sh` copied in (**borrowed, run, then reverted** -
neither is committed on this branch): **11/11, exit 0**.

A wrong verdict that explains itself is the shape this project keeps recording. The row said the
named test did not fire, which reads as a real gap; the same row's own output contained the test
failing.

**An EARLIER U0 attempt showed `exit 143`, and that was my own kill rather than a verdict.** I
edited and committed `tests/test_http_hardening.py` while that run was in progress, which breaks the
rule that a mutation harness owns the working tree for its whole run. The commit captured only my
own changes - checked, its diff is one file with no foreign sed edit - but the RUN's subject changed
underneath it, so I killed it rather than report a number taken while I was moving what it measured.
A measurement of a moving subject is not a weaker measurement, it is a different one. The tree was
clean immediately after that kill; nothing was stranded by it.

`check-u9-http-controls.sh` completed validly on the final tree - **14/14 controls fired, exit 0**.

`OBLIGATIONS.md` was not hand-edited and `check-obligations.py` exits 0, so no anchor moved.

---

# Tasks raised rather than silently fixed or dropped

- **#78** - `DereferenceRefsMiddleware` live, framework-injected, modelled nowhere. Since **ruled as
  ADR-0032 (Accepted)**, with a C2 row added.
- **#82** - `DESIGN.md:1072` against C1-T1 on `send_email`. **RULED, and no ADR was needed**: the
  tension dissolves on reading the full sentence, which is scoped to §2.1's schema rules. My task
  text and my first code comment both repeated the trimmed citation; both are corrected. The M4
  change and the admission-rule widening stand as landed.

---

# What I could NOT settle

This list is for what I cannot settle, not for what I did not try.

- **Nothing about the harnesses remains unsettled.** All eight of the units' harnesses touching files
  I changed have now completed on the final tree, one at a time, exit 0 each - the table above. This
  bullet previously said two had no verdict; both were subsequently run and are recorded there
  instead. It is kept only to note that **I twice inferred a cause I could not see**: I read three
  simultaneous task stops as a deliberate halt and declined to relaunch, and the premise was wrong -
  nobody had halted anything. The caution cost nothing but the inference was not evidence, and the
  right move would have been to ask rather than conclude.
- **Whether L4's new arm can actually fail.** Its assertions are strong - the refusal must name a
  rate limit and carry `token_client_id`'s digest, the bystander must connect, and `drained > 0` is
  a positive control - but I did not amputate it. Making the limiter key on the connection rather
  than the token is not a one-line mutation, and I did not build one.
- **Whether the six classes in `UNCLASSIFIED_MIDDLEWARE` are individually dangerous.** I established
  the set is closed and that `LoggingMiddleware` is admissible and harmful. R7 flagged
  `ToolInjectionMiddleware` as the next to look at, on the reasoning that a middleware which can add
  tools sits upstream of the write gate and the scope map. I did not assess it, and the constant's
  docstring says the seven are undecided rather than approved.
- **Whether H3's widened claim list has false positives outside the three containers now scanned.**
  Zero inside them, measured. I also measured the whole repository at 18 hits and ruled them benign
  by reading each one - but that reading is mine, and the decision to exclude `docs/reviews`,
  `docs/briefs` and `docs/research` is a scoping judgement a second reader should check.
- **Behaviour under simultaneous rate-limited callers.** Unverified before this branch, unverified
  after. U9's report and ADR-0002 both say so; my L4 arm is sequential like every other.
- **`shellcheck` and `actionlint`** - I changed no shell and no workflow, so nothing I did could
  break them, but I did not run them and cannot report an exit code.
- **`docs/reviews/check-clause-citations.py`** - needs the standards sibling checkout, which is not
  on this machine. CI is where its verdict comes from.

---

# Delivery

Commits on `fix/r7-findings`, in order:

```
47ed850  test(u9): assert the middleware stack EQUALS its expected set, not a superset
680ef16  test(u10): scope the approval-wording negator to its clause, widen the claims, derive the scope
b547a8c  fix(jobs): delete three inert Field defaults, and walk the container so they cannot return
a25b633  test(u12): match the page cap by VALUE, not by four spellings of it
c980e78  test(u12): build C5-I1's caller-visible arm, the one U12 never wrote
a820247  fix(redaction): record send_email as its value, so the audit event can answer C1-T1
87d630a  test(u10): give three nits bodies that match their names
8c6f8ee  test(u9): pin the drained client's connection-level lockout on the per-client keying
```

plus the mypy narrowing fix and this report. **Not merged and not pushed** - that is the
orchestrator's.

Every commit message was written with `git commit -F` and a quoted heredoc delimiter.

**The worktree `/tmp/r7-fixes-work` is clean and can be removed at merge.** Every harness has run;
nothing of mine is executing in it. Verified `git status --porcelain` empty and `git diff --quiet
HEAD` identical after the last run and after reverting the two borrowed scripts. I have left it in
place rather than removing it myself, so the orchestrator can re-run anything before merging.
