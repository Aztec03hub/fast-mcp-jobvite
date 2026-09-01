# CODE-REVIEW-R11 - the 45-commit hole, code and design half

<!-- REVIEW-COVERS: f699f74..dad014e PATHS: src tests docs/adr docs/DESIGN.md -->

**Range:** `git diff f699f74..dad014e -- src tests docs/adr docs/DESIGN.md`, 56 files, +1052/-727.
**Worktree:** `/home/plafayette/claude_projects/fmj-worktrees/r11-code`, branch `review/r11`, detached
from `dad014e`. **Frozen design read as `git show aca9397:docs/DESIGN.md`**, which is byte-identical
to the working tree's copy (`git show aca9397:docs/DESIGN.md | cmp - docs/DESIGN.md` -> identical).

### What the coverage declaration above does and does not claim

`check-review-coverage.py` reads the `REVIEW-COVERS` line as `git rev-list f699f74..dad014e` - the 45
commits, `f699f74` exclusive and `dad014e` inclusive. That is the range **I was made responsible
for**, and declaring it is what stops this stretch of trunk from looking unreviewed again.

**It is not a claim that I read every line of those 45 commits, and the difference is a path filter.**
This round was dispatched with the scope `-- src tests docs/adr docs/DESIGN.md`, which is 56 of the
133 files the range touches. The other half - the checkers, `scripts/`, and `.github/workflows/` - went
to `review-r12` over the same commit range, so the span is covered by two documents with
complementary path filters rather than by this one alone. If `review-r12`'s document ends up without
a `REVIEW-COVERS` line, this declaration will make the range read as fully covered when only the
`src`/`tests`/design slice of it was mine, and that is the failure mode worth watching: the checker's
own docstring says it proves a commit falls inside a declared range and never that anyone read it.

Two things I noticed inside `review-r12`'s half and deliberately did not chase are listed under
**What I did NOT verify**, at the end.

## Outcome: all eight fixed on this branch

Every finding was accepted and worked in the order the orchestrator set. Commit per row, and the
gate numbers below are the REVIEW's; the fixes' own numbers are at the bottom of this section.

| Finding | Commit | What proves it |
|---|---|---|
| R11-H1 | `5e45709` | 4 amputations red, incl. ADR-0030's own "change the fake's number" |
| R11-H2 | `afd2937` | both guards re-amputated, one arm each, no collateral |
| R11-M1 | `ece3dbd` | source-level guard; retyping the literal goes red |
| R11-M2 | `40aca53` | 4 arms on the marker rule, both directions |
| R11-M3 | `ece3dbd` | the new range contains the sentence the docstring quotes |
| R11-M4 | `105a979` | fixed independently by the orchestrator; see that row |
| R11-L1 | `ece3dbd` | reverting the fix turns its case red |
| R11-N1 | `ece3dbd` | reflowed in place |

**Gates after the fixes**, each from its own exit code: `pytest` 0 - **873 passed**, 6 deselected,
**0 skipped**; `mypy` 0 - 96 files; `ruff check .` 0; `ruff format --check .` 0;
`check-harness-anchors.py --self-check --floor 458` 0; `check-settings-are-read.py` 0.

**The suite floor moves 868 -> 873** and `ci.yml`'s `check-suite-floor.sh 868` is the orchestrator's
to advance.

### Three things went wrong while fixing, and each is the finding's own shape pointing at me

- **A vacuous amputation I nearly recorded as a survivor** (H1). I mutated `retry_after`'s default in
  `JobviteUpstreamError.__init__`; `public_error()` assigns that field *after* construction, so my
  own fix overwrote the mutation and the suite stayed green for a reason unrelated to the test.
  Moving the mutation to the assigning line turned it red. **A mutation that never reaches the
  behaviour is indistinguishable from a test that cannot see it** - which is precisely H2.
- **A guard that could not fail** (M1). My first was `HTTPX_LOGGER_NAME is _httpx2_logger.name`. It
  SURVIVED: CPython interns short identifier-shaped literals, so `"httpx2" is logger.name` is `True`
  and the check passes against the exact code it was written to refuse. Replaced with an `ast`
  assertion over the module's own source, because **a claim about what the source SAYS has to read
  the source**.
- **I destroyed an uncommitted change with `git checkout -- <path>`** (M2). Restoring a mutation that
  way discards the whole edit when the file is not staged - there is nothing to restore *to*. Caught
  by grepping for the symbol afterwards rather than by trusting the restore. Every other arm in this
  round used `cp` against a backup taken first.

---

## Gates at the time of REVIEW, each read from its own exit code

```
uv run --frozen pytest         -> 0    868 passed, 6 deselected, 0 SKIPPED   (ci.yml floor 868)
uv run --frozen mypy           -> 0    Success: no issues found in 96 source files
uv run --frozen ruff check .   -> 0
uv run --frozen ruff format --check . -> 0
scripts/check-harness-anchors.py --self-check --floor 458 -> 0
                                      harnesses scanned: 33 / anchors resolved: 458
```

Both floors were grepped out of `.github/workflows/ci.yml` at run time, not retyped:
`check-suite-floor.sh 868` and `check-harness-anchors.py --self-check --floor 458`.

---

## R11-H1 (High) - FIXED at 5e45709 - ADR-0030 has no code half, and its tests manufacture the evidence

**The frozen design states the behaviour in the present tense and nothing implements it.**
`docs/DESIGN.md:376-382`, applied by `8a9d63c` in this range:

> **A `Retry-After` the upstream volunteered is passed on, on whatever problem shape results**
> (ADR-0030).

and the older promise it widens, `docs/DESIGN.md:368-370`:

> what distinguishes them is `detail` ... plus a `retry_after` hint.

**Measured.** The only problem-building call production makes is
`problem_from_exception(exc, event.request_id)` - no extensions - at `src/fast_mcp_jobvite/tools/jobs.py:420`,
`:705` and `src/fast_mcp_jobvite/tools/candidates.py:650`, `:696`, `:782`, `:820`. Those are all six
sites. `grep -rn "retry_after" src/fast_mcp_jobvite/tools/` returns nothing.
`JobviteUpstreamError` (`src/fast_mcp_jobvite/errors.py:135`) has no `retry_after` attribute at all,
so `_RetryableUpstream.public_error()` (`services/jobvite_client.py:894-910`) drops the parsed header
on every non-429 shape - which is the exact defect ADR-0030 is titled after.

Runtime probe, production's call shape with a positive control (`/tmp/r11-probe-retry-after.py`):

```
ARM 1 production shape   : ['detail', 'instance', 'request_id', 'status', 'timestamp', 'title', 'type']
  retry_after present?   : False
  the exception HAS it   : 30.0
ARM 2 test shape         : [..., 'retry_after', ...]
  retry_after present?   : True = 30.0
VERDICT: HINT IS DROPPED
```

**The tests cannot see it because they build the object themselves.**
`tests/test_resilience.py:1073-1075` is `problem_from_exception(opened_error, RID_A, retry_after=opened_error.retry_after)`
- a call shape no production site makes - and then asserts `open_problem["retry_after"] > 0` at
`:1081-1082` under the comment *"The `retry_after` HINT (DESIGN.md:370)"*. `tests/test_error_contract.py:225-230`
does the same with a literal 30, under a docstring claiming *"DESIGN.md:370 attaches a retry_after
hint to the 503"*. Both test `build_problem`'s `**extensions` plumbing, which works; neither tests
the claim in its own docstring.

### The asymmetry inside `8a9d63c`, which is the transferable part

The same commit applied two ADRs for mechanisms that did not exist, and marked only one of them.
ADR-0025's paragraph opens `**That outbound throttle IS NOT IMPLEMENTED. The two rules below
constrain whoever builds it; they do not describe what runs today**` (`docs/DESIGN.md:448`).
ADR-0030's paragraph, eighty lines earlier, is written in the plain present tense and reads as a
description of behaviour.

**Nothing about the two rulings justifies the difference.** Neither had an implementation when it
was applied. What differed was that ADR-0025's own ruling ends by saying the throttle is still
unimplemented and the design should say so, and ADR-0030's does not - so the marker was inherited
from the ADR's closing paragraph rather than decided by the applier. A design that states an
unbuilt mechanism in the present tense has no reader who can tell it apart from one that runs, and
that is exactly what happened here: three review rounds and a machine gate read `DESIGN.md:376-382`
and none of them asked whether any code did it.

**The rule that generalises**: when an ADR is applied to the frozen design ahead of its
implementation, the applied paragraph says so in its own first sentence. `ADR-0025`'s form is the
model. This is cheaper than a checker and it is the thing a checker cannot do, because "is this
paragraph describing code that exists?" is not decidable from the text.

**Suggested fix - at the rule, not the six call sites** (task #66's lesson). In
`errors.problem_from_exception`, merge the exception's own hint before delegating, with an explicit
caller extension winning:

```python
if isinstance(exc, FastMcpJobviteError):
    hint = getattr(exc, "retry_after", None)
    if hint is not None:
        extensions = {"retry_after": hint, **extensions}
    return build_problem(exc.kind, exc.detail, request_id, **extensions)
```

Then land ADR-0030's other half: give `JobviteUpstreamError` a `retry_after` attribute and have
`_RetryableUpstream.public_error()` attach `self.retry_after` to `self.cause` on the non-429 branch,
so a 502 carries what the upstream actually sent. **Only the upstream's own value** - the ADR is
explicit that a synthesised hint on a 502 is worse than the omission.

Finally, replace both existing assertions with ones taken at the **tool boundary** - invoke the tool
against a fake that returns `Retry-After: 900` and read `structured_content["retry_after"]` off the
`ToolResult` - and amputate as ADR-0030 requires: return a different number from the fake and confirm
the arm goes red. A test that passes the value in cannot fail.

---

## R11-H2 (High) - FIXED at afd2937 - two of R9's three PDEATHSIG fixes are amputation survivors

`449968f` landed three fixes in `tests/boot_process.py`. One of them (the dlopen-after-fork move to
import time) is structural. The other two are guards, and **deleting either leaves the whole
868-test suite green.**

Each mutation was proved to have LANDED (`cmp` against a backup, not `grep -F`), run under
`PYTHONDONTWRITEBYTECODE=1`, and restored by `cp` + `cmp`.

| Amputation | What was deleted | Result |
|---|---|---|
| A | the zero-progress break (`jobvite_client.py:2219`) | **KILLED** - 3 failures |
| B | the record ceiling (`jobvite_client.py:2246`) | **KILLED** - 4 failures |
| C | the idempotence guard (`redaction.py:521-522`) | **KILLED** - 3 failures |
| **D** | **the prctl return check (`boot_process.py:203-204`)** | **SURVIVOR - suite green** |
| **E** | **the whole post-fork race check (`boot_process.py:207-208`)** | **SURVIVOR - suite green** |

**Why nothing sees them.** The case `449968f` added,
`tests/test_spawn_orphan.py:150 test_a_healthy_child_takes_none_of_the_bail_out_exits`, asserts only
that the guards do **not** fire (`assert rc not in {...}`). A negative-only control passes trivially
against a deleted guard - it is structurally incapable of detecting the deletion. The comment above
the prctl check reads *"The return is CHECKED. A silently failed install leaves the child
unprotected, which is the whole defect wearing the fix's name"*, and nothing holds it to that.

**Both are cheaply testable and I measured the controls** (`/tmp/r11-probe-guards.py`):

```
race-check control      : rc=102 expected=102 -> FIRES
prctl(bogus option)     : returns -1 errno=22 -> a non-zero IS observable
```

**Suggested fix.** Two positive arms beside the existing negative one:

```python
def test_the_race_check_fires_when_the_parent_is_not_ours() -> None:
    """Amputating this check left the suite green (R11-H2)."""
    proc = subprocess.Popen(
        [sys.executable, "-c", "raise SystemExit(0)"],
        preexec_fn=functools.partial(_die_with_parent, 999_999),  # noqa: PLW1509
    )
    assert proc.wait(timeout=30) == _EXIT_PARENT_ALREADY_GONE
```

For the prctl arm, give `_die_with_parent` an `option: int = _PR_SET_PDEATHSIG` keyword (it is
already the only caller-visible constant) and pass `0xFFFF` from a test, asserting
`_EXIT_PRCTL_FAILED`. Measured above: `prctl(0xFFFF, 0)` returns `-1` with `EINVAL`, so the arm is
real rather than hypothetical.

---

## R11-M1 (Medium) - FIXED at ece3dbd - ADR-0026 requires the logger name DERIVED; the code retypes it

ADR-0026, `docs/adr/0026-...md:161-163`, under *"Two things follow for anything built on this ADR"*:

> **The implementation must derive the logger name from the imported module, not retype it.** The
> package is vendored as `httpx2` and a future rename would silently detach the filter again.

`8a9d63c` applied that to the frozen design as fact, `docs/DESIGN.md:327-328`:

> **The logger name is derived from the imported module rather than retyped**

The code retypes it. `src/fast_mcp_jobvite/utils/redaction.py:489`:

```python
HTTPX_LOGGER_NAME: Final = "httpx2"
```

It is not unguarded - `tests/test_redaction.py:535` asserts
`HTTPX_LOGGER_NAME == httpx2._client.logger.name` - and that test is why I rank this Medium rather
than High. But the ruling's code half is not landed and the **frozen** design asserts a property the
code does not have, which is the shape a decision document acquires when it is checked against the
commit message instead of the code. `docs/briefs/ADR-BATCH.md:80` records this row as *"ALREADY
IMPLEMENTED, and correctly"*, quoting the retyped literal as the evidence.

**Suggested fix - the code route, which needs no ADR:**

```python
from httpx2._client import logger as _httpx2_logger  # noqa: SLF001

#: Derived, never retyped (ADR-0026). A rename upstream follows the
#: import instead of silently detaching the filter.
HTTPX_LOGGER_NAME: Final[str] = _httpx2_logger.name
```

Keep `tests/test_redaction.py:535` - with the name derived it becomes a tautology, so replace its
body with the inverted probe's assertion (a credential-bearing URL comes out redacted), which is what
ADR-0026:164-166 says the assertion has to be anyway. The alternative - amending
`docs/DESIGN.md:327-328` to say "retyped and asserted against the library's own logger object" -
needs a numbered ADR, and is the worse trade for the same outcome.

---

## R11-M2 (Medium) - FIXED at 40aca53 - the design says the throttle is not implemented; README and `.env.example` say it works

`8a9d63c` added to the frozen design, `docs/DESIGN.md:448-451`:

> **That outbound throttle IS NOT IMPLEMENTED. The two rules below constrain whoever builds it; they
> do not describe what runs today** (ADR-0025). `JOBVITE_OUTBOUND_RATE_LIMIT` is declared, typed,
> defaulted, documented in `.env.example` and covered by config tests, and **no code reads it**

Verified: `grep -rn "outbound_rate_limit" src/` returns exactly one hit,
`src/fast_mcp_jobvite/config.py:229`, the declaration.

The two artefacts an operator actually reads say the opposite. `README.md:82`:

> `JOBVITE_OUTBOUND_RATE_LIMIT` | No | `6` | Outbound requests per **minute** to Jobvite, minimum 1.

`.env.example:91-96` gives it five lines of prose about the vendor's envelope and sets
`JOBVITE_OUTBOUND_RATE_LIMIT=6`. `grep -n "not implemented\|NOT IMPLEMENTED\|unimplemented" README.md .env.example`
returns nothing. An operator who sets this to `1` because they are worried about their tenant gets no
protection and no signal - switched-off and working render identically, which is the failure this
repo has already recorded once over the jobvite mirror.

**Scope note:** `README.md` and `.env.example` are outside my named diff scope and are not
`review-r12`'s either. `README.md` was edited by `a27597d` in this range, so the batch touched the
file and did not correct the row.

**Suggested fix.** In `README.md:82`, make the state explicit in the description cell:
*"**Declared but NOT YET IMPLEMENTED** (ADR-0025): nothing reads it today. Sets the intended rate
once the outbound self-throttle is built."* Same sentence as the first line of `.env.example`'s
block, above the assignment. Neither needs an ADR - both describe the design accurately rather than
changing it. Task #113's tripwire already fires when `outbound_rate_limit` gains its first reader;
extend it to also assert that both artefacts still carry the marker, so the marker is removed in the
same commit that makes it false.

---

## R11-M3 (Medium) - FIXED at ece3dbd - a citation that resolves and names the wrong sentence, in live code, of the class #114 closed at `dad014e`

`src/fast_mcp_jobvite/approval.py:192-193`:

```
    **The set is CLOSED**, for the reason `error-contract.md`'s registry
    is closed (DESIGN.md:561-562): a value emitted into an audit record
    is a contract, and an open string invites a fourth spelling of the
```

`docs/DESIGN.md:561-562` is a different sentence, in §5.1's registry discussion:

> - **`:210` makes a published `type` URI a contract**, so inventing slugs is a promise we would owe
>   forever. The registry already has a type for every condition we produce.

The sentence the docstring quotes **verbatim** is `docs/DESIGN.md:761-762`:

> The set is closed for the reason `error-contract.md`'s registry is closed:
> a value emitted into an audit record is a contract, and an open string invites a fourth spelling of

It resolves, it is thematically adjacent (both sentences contain "a contract"), and it is 200 lines
away in the wrong section. **It was repointed twice inside this range** and each repoint carried the
error forward faithfully:

```
8a9d63c: DESIGN.md:510-511 -> DESIGN.md:541-542
aca9397: DESIGN.md:541-542 -> DESIGN.md:561-562
```

At `f699f74` the design's `:510-511` was already the `:210` sentence, and the intended one was at
`:688`. So the repointer was correct - it preserved content, which is what
`8a9d63c`'s *"repoint by content not arithmetic"* claims - and preserving the content of a wrong
citation is how one survives a sweep. `6ea6c6f` / task #114 closed this class at `dad014e` with
*"FOUR not five - they all RESOLVED and named the wrong sentence"*; this is a fifth.

**I checked the whole repointed population rather than stopping at one.** A script paired every
removed/added line in the `src`+`tests` diff that differed only in its citation, then compared the
text at the OLD range in `f699f74:docs/DESIGN.md` against the text at the NEW range in
`aca9397:docs/DESIGN.md`: **445 repoint pairs, and every content difference was a deliberate
widening** (e.g. `486-489 -> 525-540`, which absorbs ADR-0024's new paragraph). No repoint moved a
citation onto unrelated text. The defect is inherited, not introduced - but it is live and it is in
`src/`.

**Suggested fix.** `DESIGN.md:561-562` -> `DESIGN.md:761-762` at `approval.py:193`. Then re-run
#114's sweep with a stronger predicate than "does it resolve": for a citation followed by text the
design also contains, require the cited range to **contain that text**. That predicate finds this one
mechanically and finds the next one; "resolves to a non-blank line" cannot.

---

## R11-M4 (Medium) - FIXED INDEPENDENTLY at `105a979` - nothing in the repo records the current freeze SHA, and the design's own header still names the first one

`docs/DESIGN.md:3` is unchanged through both re-freezes:

```
Status: **FROZEN, revision 6.** Frozen 2026-08-28 03:04 PM CDT.
```

The document has since been changed twice by numbered ADRs - `8a9d63c` (nine ADRs) and `aca9397`
(ADR-0025) - so the recorded freeze date predates the current text. `grep -rn "aca9397"` across
`docs/adr`, `docs/briefs`, `docs/plans`, `scripts` and `.github` outside worklogs and review reports
returns **nothing**: no artefact names the object that is actually frozen. What the repo does contain
is two stale copies of the previous one - `docs/briefs/ADR-0025.md:9` (*"The design is FROZEN at
`8a9d63c`"*) and `docs/adr/0025-...md:117` - and `docs/plans/IMPLEMENTATION-PLAN.md:20` naming
`c15b138` before that.

This is the PREAMBLE's own thesis - *"a retyped constant decays"* - applied to the one constant every
brief in this project opens by retyping. It has already decayed twice.

**Suggested fix.** The header edit needs an ADR (only a numbered ADR may change `DESIGN.md`), so do
the cheap half first: add a `Re-frozen at:` line to `docs/adr/README.md`, which is not frozen, is
already the ADR index, and is the natural place a reader looks for what an ADR batch did. Have the
ADR-batch procedure update it in the same commit that re-freezes, and have `PREAMBLE.md`'s
*"Read it as `git show <SHA>:docs/DESIGN.md`"* point at that line rather than leaving the SHA to the
dispatcher. Then fold the header edit into the next ADR that touches the design anyway - a
`**Re-frozen 2026-08-29 at `aca9397` (ADR-0025).**` line under `:3` - rather than spending an ADR on
it alone.

---

## R11-L1 (Low) - FIXED at ece3dbd - the three bail-out exit codes are inoperative on the path that spawns every server

`449968f` introduced `_EXIT_NO_LIBC = 100`, `_EXIT_PRCTL_FAILED = 101` and
`_EXIT_PARENT_ALREADY_GONE = 102` at `tests/boot_process.py:137-140`, with the comment:

```
#: Distinct exit codes, because `os._exit(1)` from a `preexec_fn` is
#: indistinguishable to the caller from the entry script failing to
#: import - and those need different diagnoses.
```

`grep -rn "_EXIT_NO_LIBC\|_EXIT_PRCTL_FAILED\|_EXIT_PARENT_ALREADY_GONE"` shows the only reader is
`tests/test_spawn_orphan.py`. The function that spawns every server under test,
`spawn_marker_server`, never looks at them - `tests/boot_process.py:246-253`:

```python
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    proc.kill()
    proc.wait()
    raise AssertionError(
        f"the server never opened its lifespan. output:\n{output.read_text()}"
    )
```

If the guard fires, the child dies before `exec`, `output` is empty, and every one of the three
distinct diagnoses renders as the same message with a blank body - the outcome the codes were added
to prevent, one call frame away from the codes themselves.

**Suggested fix:**

```python
    rc = proc.poll()
    named = {
        _EXIT_NO_LIBC: "libc.so.6 could not be loaded, so PDEATHSIG was never installed",
        _EXIT_PRCTL_FAILED: "prctl(PR_SET_PDEATHSIG) returned non-zero",
        _EXIT_PARENT_ALREADY_GONE: "the parent died between fork and the race check",
    }.get(rc)
    raise AssertionError(
        f"the server never opened its lifespan (rc={rc}"
        + (f": {named}" if named else "")
        + f"). output:\n{output.read_text()}"
    )
```

---

## R11-N1 (nit) - FIXED at ece3dbd - a mechanical rewrap left a two-word orphan line

`aca9397` rewrapped the comment at `src/fast_mcp_jobvite/__main__.py:461-464` by splitting rather
than reflowing:

```
461:        # DESIGN.md:1052-1054. Teardown has already completed by
462:        # here, and the call is unconditional so the stdio hang stays
463:        # closed
464:        # (ADR-0018).
```

Lines 463-464 fit on one line inside 72 columns.

**Suggested fix:** reflow the paragraph rather than splitting the overflow -
`# closed (ADR-0018).` as one line. A sibling of the same shape predates this range at
`src/fast_mcp_jobvite/services/jobvite_client.py:2266-2273` (`# for`, `# scan`, `# incomplete`, three
orphan lines from `1e55129`); worth the same pass since the fix is identical.

---

## What I verified and found sound

These are here because a review that reports only defects gives no information about what was
checked.

- **ADR-0024, both bounds.** The zero-progress break and the record ceiling are implemented as ruled
  at `services/jobvite_client.py:2219-2256`, the ceiling counts **records** (`MAX_SCAN_RECORDS`) and
  not pages, and `incomplete` is `_check_completeness(...) or stalled or ceiling_hit` at `:2274-2283`
  so neither bound reads `total`. Amputating each **separately** killed the suite (3 and 4 failures),
  including `test_neither_bound_substitutes_for_the_other` on both - so the "neither substitutes"
  claim is itself enforced.
- **ADR-0026's idempotence.** `install_log_redaction` (`utils/redaction.py:498-524`) is guarded by a
  module lock and returns a bool. Amputating the check killed 3 cases.
- **ADR-0025's Q1 withdrawal, checked against the code rather than the ruling.** The ADR withdraws Q1
  on the ground that §4.5 states `min(transport_cap, configured_result_cap)` and
  `result_cap()` implements exactly it. `services/jobvite_client.py:1989` is
  `return min(self.transport_cap(jobfeed=jobfeed), self._max_results)`. The withdrawal holds.
- **ADR-0032's central fact, checked against the library.** `inspect.getsource(fastmcp.FastMCP.__init__)`
  on `fastmcp 4.0.0b4` shows `dereference_schemas: bool = True` and
  `self.middleware.append(DereferenceRefsMiddleware())` under it - framework-injected by default,
  exactly as `docs/DESIGN.md:1243-1249` now says. Its tripwire
  (`tests/test_server.py:272`) reads the **models**, carries a `len(models) >= 5` population floor,
  and so cannot pass by discovering nothing.
- **ADR-0028, ADR-0031, ADR-0033 code halves are present.** `ApprovalMechanism.MRTR = "mrtr"`
  (`approval.py:216`), the four `ApprovalState` members (`:252-257`), `ApprovalRefusedError.kind =
  FORBIDDEN` reaching 403 (`errors.py:232`, `FORBIDDEN` at `:91`), and the refusal returned at
  `tools/candidates.py:782`.
- **ADR-0027's budget is read at every construction site.** All three `JobviteClient(...)` calls in
  `src/` pass `outbound_budget_seconds=settings.outbound_budget_seconds`
  (`tools/jobs.py:334`, `tools/jobs.py:645`, `tools/candidates.py:587`).
- **The ~19 `src/` files with balanced insertions and deletions are not a rewrite.** Normalising every
  `DESIGN.md:<n>` to a placeholder and diffing collapses the change to comment reflow plus exactly one
  behavioural line, `mechanism=ApprovalMechanism.MRTR`.
- **445 citation repoints in `src` and `tests` are content-preserving** (method in R11-M3).

---

## The residual hole in the freeze fix, which the orchestrator asked me to look for

`105a979` is a better fix than the one M4 proposed, and it caught drift I had not found: `86ab20e`
edited `DESIGN.md` and no pointer moved, which `check-design-freeze.py` now detects by BLOB IDENTITY
rather than by line count. Both halves of M4 are closed - `docs/DESIGN-FREEZE.txt` is the single
record, and `check-design-citation-shape.py` reads it instead of carrying its own `--sha` default.

**One hole remains, and it is the half a blob comparison cannot reach.** The gate answers *"has
`DESIGN.md` moved away from the declared freeze?"* It cannot answer *"is the SHA in front of this
reader the current one?"* - and that second question is where the decay actually happened. Measured
on `main`:

```
$ git grep -ln "DESIGN-FREEZE" main
  .github/workflows/ci.yml   docs/README.md   docs/briefs/AUDIT-SHAPES.md
  docs/reviews/check-design-citation-shape.py   docs/reviews/check-design-citations.py
  docs/reviews/check-design-freeze.py
```

`docs/briefs/PREAMBLE.md` is not in that list. Its rule still reads:

> **`docs/DESIGN.md` is FROZEN.** Read it as `git show <SHA>:docs/DESIGN.md`, never from the working
> tree.

**The SHA is still the dispatcher's to type**, so every future brief re-enters the decay by hand, and
a brief naming a stale-but-valid SHA resolves cleanly and passes every gate - which is exactly what
`docs/briefs/ADR-0025.md:9` does today with `8a9d63c`. Fourteen briefs on `main` name `c15b138`; those
are records and correct as records. The live risk is the fifteenth.

**Suggested fix, one line in `PREAMBLE.md`:** replace `<SHA>` with
`` `git show "$(cat docs/DESIGN-FREEZE.txt)":docs/DESIGN.md` ``. Then the file is read rather than
retyped by everyone who follows the preamble, which is everyone, and it costs nothing. This is
`PREAMBLE.md`'s own thesis - *"a retyped constant decays"* - applied to the constant it retypes. It
is your file, so I have not touched it.

---

## What I did NOT verify

- **The shape ADR-0030's 502 half should take.** I established that `JobviteUpstreamError` carries no
  hint and proposed where to attach it, but I did not design or measure the 502 arm end to end
  against a fake sending `Retry-After` on a 5xx. R11-H1's fix needs that arm written and amputated.
- **Whether `docs/DESIGN.md:3`'s header should be edited at all**, versus recording the freeze SHA
  only outside the frozen document. That is a Phil ruling about what the freeze rule permits, not a
  measurement, and R11-M4 gives both routes rather than picking one.
- **The 33 harness scripts individually.** I ran `check-harness-anchors.py --self-check --floor 458`
  (exit 0, 458 anchors) and no other harness, because they are `review-r12`'s half.
- **Two things I saw in `review-r12`'s scope and left alone.**
  `docs/reviews/check-design-citation-shape.py:24-26` says *"The current freeze is the `--sha` default
  and nowhere else"*, which is a third place the SHA lives and is relevant to R11-M4;
  `docs/reviews/check-settings-are-read.py:54` exempts `outbound_rate_limit` with ADR-0025 as its
  reason, which must be un-exempted in the commit that gives the throttle its first reader (R11-M2).
- **The credentialed suite.** 6 tests deselected, not skipped; no tenant exists.
