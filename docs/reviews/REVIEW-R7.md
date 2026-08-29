# CODE-REVIEW-R7 - U8, U9, U12 and U10, all merged, none reviewed

**Subject SHA: `bc0f958`.** Every finding below cites `bc0f958` and every citation was read with
`git show bc0f958:<path>` or from a `grep -n` inside a worktree pinned at that commit
(`git worktree add --detach /tmp/code-review-r7-work bc0f958`). `u14-arguments` was live in
`/tmp/u14-arguments-work` on the same commit throughout and nothing here touched it.

**Design read as `git show c15b138:docs/DESIGN.md`,** never from a working tree.

**Read-only on `src/`, `tests/`, `scripts/`.** Six mutations were applied inside my own worktree to
measure, each proved to have LANDED (`cmp` against a backup) before the run and RESTORED after
(`cmp` identical **and** `git diff --quiet` clean). No mutation is in any tree now.

---

## Baseline, read from the terminal, each on its own line

Floors DERIVED from `ci.yml` at `bc0f958`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 663
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 371
```

| Gate | Result | Exit |
|---|---|---|
| `uv run --frozen pytest -q` | **663 passed, 0 skipped**, 6 deselected, 63.94s | **0** |

663 passed == the 663 floor. `pydantic 2.13.5`, CPython 3.12.3.

**All eight harnesses of these four units ARE wired.** Verified, not assumed - each of
`check-u8-candidates-{controls,amputation}.sh`, `check-u9-http-{controls,amputation}.sh`,
`check-u12-jobfeed-{controls,amputation}.sh` and `check-u10-write-{controls,amputation}.sh` appears
exactly once in `.github/workflows/ci.yml`, all eight through `scripts/ci-harness-gate.sh`
(`ci.yml:632, 637, 653, 657, 674, 679, 691, 695`). **What is NOT uniform is their row floors - see
H2.**

---

# FINDINGS

## H1 - HIGH. A payload-logging middleware can be added to the production stack and the entire 663-test suite stays green. MEASURED.

**`src/fast_mcp_jobvite/http_hardening.py:156-164` (`EXCLUDED_MIDDLEWARE`, 5 names) and
`tests/test_http_hardening.py:76-82` (`ADOPTED_MIDDLEWARE`, 3 names) at `bc0f958`.**

Two hand-kept lists sit beside a container neither of them enumerates. Measured with the pinned
`fastmcp==4.0.0b4` in the lock, the framework ships **15** concrete `Middleware` subclasses:

```
AuthMiddleware, BaseLoggingMiddleware, DereferenceRefsMiddleware, DetailedTimingMiddleware,
ErrorHandlingMiddleware, LoggingMiddleware, PingMiddleware, RateLimitingMiddleware,
ResponseCachingMiddleware, ResponseLimitingMiddleware, RetryMiddleware,
SlidingWindowRateLimitingMiddleware, StructuredLoggingMiddleware, TimingMiddleware,
ToolInjectionMiddleware
```

3 adopted + 5 excluded = 8. **Seven are in neither list**, and one of them is
`LoggingMiddleware` - the payload-logging sibling of the middleware
`test_structured_logging_is_constructed_with_include_payloads_false`
(`tests/test_http_hardening.py:198-212`) exists to pin at `include_payloads=False` for C2-I1
(`DESIGN.md:1732`). It is a separate class, not a base or subclass of
`StructuredLoggingMiddleware` (measured: `issubclass` is `False` in both directions), so no
`isinstance` check in the file sees it.

**The measurement.** Mutation **M4**, added to `build_middleware` at
`src/fast_mcp_jobvite/http_hardening.py:327`:

```python
        StructuredLoggingMiddleware(include_payloads=False),
+       __import__(
+           "fastmcp.server.middleware.logging", fromlist=["LoggingMiddleware"]
+       ).LoggingMiddleware(include_payloads=True),
```

- `tests/test_http_hardening.py` -> **29 passed**, exit **0**.
- Full suite -> **663 passed, 6 deselected**, exit **0**.

Nothing fails. `ADOPTED_MIDDLEWARE <= present` is a **subset** check, so it is structurally
incapable of noticing an addition, and `EXCLUDED_MIDDLEWARE & present` is empty because
`LoggingMiddleware` was never listed. `test_the_five_excluded_middleware_are_absent`
(`tests/test_http_hardening.py:215-225`) is the tenth instance of the hand-kept-list-beside-its-container
shape on this project.

**Failure this produces.** A dependency bump, a merge, or a well-meaning "let us see the payloads
in staging" adds one line and the server logs raw candidate PII - the exact C2-I1 threat - with
every gate green and no diff in any test.

**Suggested fix (NOT run - see "fixes I did not measure").** Replace the two hand-kept lists with a
container-enumerating assertion: discover every `Middleware` subclass under
`fastmcp.server.middleware` by `pkgutil.iter_modules`, and assert
`set(middleware_names(server)) == ADOPTED_MIDDLEWARE | {"RequestIdMiddleware"}` - **equality, not
subset** - so any addition, adopted or not, is a red test. Keep `EXCLUDED_MIDDLEWARE` as
documentation of *why* five were rejected, and add a second assertion that
`ADOPTED ∪ EXCLUDED ∪ {ours}` accounts for every discovered class, so the seven currently
ungoverned ones have to be classified once rather than left invisible. I did not run this because
it is an edit to `tests/`, which this brief forbids me.

---

## H2 - HIGH. U9's controls harness has NO row floor at either layer, so it is green with one surviving row - and U9 is the unit the brief says no §8 case backs.

**`scripts/check-u9-http-controls.sh:305-306` and `.github/workflows/ci.yml:653` at `bc0f958`.**

```
$ grep -n "controls fired" scripts/check-u9-http-controls.sh
305:echo "$FIRED/$TOTAL controls fired."
306:[ "$TOTAL" -gt 0 ] && [ "$FIRED" -eq "$TOTAL" ] && exit 0
```

`TOTAL > 0` is the only floor. R4-M4's row floor - *"`FIRED -ne TOTAL` is satisfied by 0 == 0, so a
harness whose rows were all deleted reports fully green"* - was applied to three of the four
siblings and **missed U9**:

```
$ for f in u8-candidates u9-http u10-write u12-jobfeed; do
    printf "%-14s ROW_FLOOR: " "$f"; grep -n "ROW_FLOOR" scripts/check-$f-controls.sh | head -1; echo; done
u8-candidates  ROW_FLOOR: 487:ROW_FLOOR=25
u9-http        ROW_FLOOR:
u10-write      ROW_FLOOR: 408:ROW_FLOOR=21
u12-jobfeed    ROW_FLOOR: 299:ROW_FLOOR=17
```

The CI layer does not cover it either. U8 and U12 carry `--min-rows` in `ci.yml`; U9 and U10 do
not - but U10 has the internal floor, so **U9 is the only one of the four with neither**:

```
ci.yml:632-633  check-u8-candidates-controls.sh --controls-fired --min-rows 25 --row-re '^########## M[0-9]+ '
ci.yml:653      check-u9-http-controls.sh --controls-fired
ci.yml:674-675  check-u12-jobfeed-controls.sh --controls-fired --min-rows 17 --row-re '^########## M[0-9]+ '
ci.yml:691      check-u10-write-controls.sh --controls-fired
```

And `scripts/ci-harness-gate.sh:42` states its own contract: `--controls-fired` requires *"an
`N/M controls fired.` line with N == M and M > 0"*. `M > 0` is one row.

**Why it matters here specifically.** The brief's own framing: U9 owns the unit **no §8 case
backs**, so a deleted test there leaves every gate green. Its controls harness is the one
instrument standing in for that missing case, and that instrument can lose 13 of its 14 rows
silently.

**Failure this produces.** A refactor that drops control rows - or an anchor that stops matching, so
a row never registers - reports `1/1 controls fired.` and exits 0. Nobody is told.

**Suggested fix (NOT run).** Add the internal floor, copying `check-u8-candidates-controls.sh:480-493`
verbatim with `ROW_FLOOR=14` (U9's report records 14/14). **Prefer the internal floor over
`--min-rows` here, and the reason is a trap:** U9's tally line at `:305` is
`echo "$FIRED/$TOTAL controls fired."` **without** the `##########` prefix its three siblings use,
so adding `--row-re '^########## M[0-9]+ '` to `ci.yml:653` would match **zero** rows and fail the
step for the wrong reason. If you want the CI layer too, normalise the prefix first. I could not
run either arm: `scripts/` is read-only for me and U9's harness is the ~13-minute one its own report
flags.

---

## H3 - HIGH. U10's wording tripwire misses a plain claim of human approval whenever an unrelated "not" sits within 160 characters - and 24-40% of the files it scans are in that shadow. MEASURED, 6/6 evasions.

**`tests/test_approval_write.py:1152-1199` at `bc0f958`** (`_CLAIMANTS` at `:1152`, `_NEGATORS` at `:1159`,
`_NEGATION_WINDOW = 160` at `:1160`, `_unnegated_claims` at `:1163`).

The scanner suppresses a hit when **any** string in `_NEGATORS` appears anywhere in the preceding
160 characters. It does not check what that negator negates. Run against the real function:

```
$ python -c "from tests.test_approval_write import _unnegated_claims, _HUMAN_CLAIMS; ..."
MISSED    unrelated "not" 40 chars earlier
MISSED    an unrelated denial in the same paragraph
MISSED    contraction n't anywhere before
MISSED    a claimant the list does not know      (a recruiter approved this write.)
MISSED    a verb the list does not know          (a human authorised this write.)
MISSED    hyphenated                             (this write was human-approved.)
```

The first three are the serious ones: they are **the forbidden claim, spelt exactly as
`_HUMAN_CLAIMS[0]` spells it**, silently suppressed. Example 1 in full:

```
the elicitation handler is not optional here. a human approved this write.
```

That returns `[]`.

**And the shadow is not rare - it is most of the corpus.** Sampling every 40 characters of the four
owned files after the same `re.sub(r"\s+", " ", ...)` flattening, the fraction of positions with a
`_NEGATORS` member in the preceding 160 characters:

| File | negator-shadowed |
|---|---|
| `src/fast_mcp_jobvite/approval.py` | 137/425 = **32%** |
| `src/fast_mcp_jobvite/tools/candidates.py` | 190/720 = **26%** |
| `tests/test_approval_write.py` | 276/1140 = **24%** |
| `docs/worklogs/U10-IMPL-REPORT.md` | 216/527 = **40%** |

**The tripwire is blindest exactly where the prose denies the most**, which is the prose the rule
exists to require. The docstring at `:1178-1181` says it *"errs toward flagging"*. Measured, in
these four files it errs toward **silence** a quarter to two-fifths of the time.

**Second half of the same finding: the owned-file list is hand-kept and short.** `:1217-1222` names
four paths. U10 also wrote:

- `src/fast_mcp_jobvite/errors.py` - `class ApprovalRefusedError` at `:201`
- `docs/adr/0028-approval-mechanism-names-a-path-this-design-does-not-use.md` - U10's own ADR,
  renumbered from 0027 on merge (its own header says so)

Neither is scanned. An ADR is precisely the document *"a compliance reader later treats as
authoritative"*, which is the docstring's own stated reason for the rule.

**Failure this produces.** The one claim this project has decided it may never make - that a person
approved a write - can be written into `approval.py`, into the report, or into the ADR, and the
test that exists to catch it stays green.

**Suggested fix (NOT run).** Three parts, cheapest first:

1. **Bound the negator scope to the sentence, not to 160 characters.** Split `flat` on `.`/`;`/`:`
   and search for negators only within the claim's own clause. This kills all three false negatives
   above and is a ~4-line change to `_unnegated_claims`.
2. **Add the two missing paths** to the `owned` list at `:1217-1222`, and - the real fix for the
   shape - derive the list rather than type it: scan `docs/adr/*.md` for the ADRs this unit
   authored plus every file `git log` shows the U10 commits touching, and assert the derived set is
   a subset of what was scanned.
3. **Widen `_CLAIMANTS`/verb forms** to `a reviewer`, `a user`, `an operator`, `someone`,
   `authorised`, `authorized`, `signed off`, and the hyphenated `human-approved`. Keep the
   fragment-assembly so the file still does not match itself.

Part 1 is the one I would land first; parts 2 and 3 are additive. **All three are hypotheses - I
could not run them, because they are edits to `tests/`.**

---

## M1 - MEDIUM. There is a fourth, fifth and sixth dual-declared pydantic default. All three are in `tools/jobs.py`, which the `send_email` fix never touched. MEASURED SURVIVOR.

**`src/fast_mcp_jobvite/tools/jobs.py:121` (`SearchJobsInput.ids`), `:458`
(`GetJobFeedInput.job_type`), `:470` (`GetJobFeedInput.available_to`) at `bc0f958`.**

The brief asks whether there is a fourth anywhere in the repository. **There are three.** An AST
scan of all 88 `.py` files in the tree - every `AnnAssign` inside a `ClassDef` whose annotation
contains a `Field(default=...)` or `Field(default_factory=...)` **and** which also carries an
assignment - returns exactly:

```
DUAL-DEFAULT src/fast_mcp_jobvite/tools/jobs.py:121 class=SearchJobsInput  field=ids           field_kw=['default']
DUAL-DEFAULT src/fast_mcp_jobvite/tools/jobs.py:458 class=GetJobFeedInput  field=job_type      field_kw=['default']
DUAL-DEFAULT src/fast_mcp_jobvite/tools/jobs.py:470 class=GetJobFeedInput  field=available_to  field_kw=['default']
hits: 3   files scanned: 88
```

`tools/candidates.py` is clean, because it was fixed. The comment recording that fix
(`tools/candidates.py:247-254`) says *"These three fields"* - a note beside the three it repaired,
which is why the three in the sibling file were never looked for. **Fix one instance, check its
siblings.**

**The precedence is confirmed, not cited.** Measured on the locked `pydantic 2.13.5`:

```python
class M(BaseModel):
    a: Annotated[bool, Field(default=True)] = False
M().a  ->  False        # the assignment wins, silently; no warning, no error
```

**The surviving mutation.** **M1**: `src/fast_mcp_jobvite/tools/jobs.py:124`,
`default=None` -> `default="R7MUTANT"` inside the `ids` `Field(...)`. Anchor proved unique
(1 occurrence), mutation proved landed (`cmp` differs), full suite:

```
663 passed, 6 deselected in 63.59s
PYTEST_EXIT=0
```

**SURVIVES.** The inert copy can be set to a type-invalid value and nothing notices. Restored,
`git diff --quiet` clean.

**Failure this produces.** Lower blast radius than `send_email` - all three defaults are `None`, so
flipping the inert copy changes no behaviour today. The defect is that **the mechanism is still
live in the repository**: the next field added in this shape may be one that matters, and any
future mutation row aimed at one of these three lines will report a false survivor and cost a
reviewer the diagnosis a second time. It is also the exact two-declarations-of-one-value shape the
project has now hit at four widths.

**Suggested fix (NOT run - `src/` is read-only for me).** Delete `default=None,` from the three
`Field(...)` calls at `:124`, `:461` and `:473`, leaving the `] = None` assignment as the single
declaration, exactly as `tools/candidates.py:255-271` now reads. Then **make it non-recurring**:
the AST scan above is ~25 lines and is the right shape for `scripts/` - it enumerates the container
(every model field) rather than keeping a list beside it. My scan script is reproduced in
"Artefacts" below so it does not have to be rewritten.

---

## M2 - MEDIUM. U12's page-cap guard is a literal-substring scan. A genuine second copy of the cap, spelled `1_000` under another name, survives the whole suite. MEASURED SURVIVOR.

**`tests/test_tools_job_feed.py:616-640` at `bc0f958`**
(`test_the_transport_cap_is_not_reimplemented_here`, forbidden list at `:637`).

The brief asks two questions. **Does the test read the module's source? Yes** - `:629-634` reads
`src/fast_mcp_jobvite/tools/jobs.py` from disk with `.read_text()`, so a path that stopped
resolving would raise `FileNotFoundError` rather than pass on an absent file. That half is sound
and better than most of its kind.

**Would it notice the number arriving under a different name? No.** `:637` is:

```python
    for forbidden in ("[:1000]", "min(1000", "1000)", "= 1000"):
```

Four literal substrings, all containing the digits `1000`.

**The measurement.** Mutation **M3**, a real reimplementation of the transport cap inserted into
`build_feed_result` at `src/fast_mcp_jobvite/tools/jobs.py:543`:

```python
+   _LOCAL_TRANSPORT_CAP = 1_000
+   items = (payload.get(JOB_FEED_ENVELOPE_KEY) or [])[:_LOCAL_TRANSPORT_CAP]
-   items = payload.get(JOB_FEED_ENVELOPE_KEY) or []
```

Anchor unique, mutation landed, `tests/test_tools_job_feed.py tests/test_tools_jobs.py`:

```
68 passed in 1.90s
PYTEST_EXIT=0
```

**SURVIVES.** `1_000` contains none of the four substrings; neither would `items[0:1000]`,
`if n > 1000:`, `cap=1000`, or `1e3`. Restored, `git diff --quiet` clean.

**Failure this produces.** U6-F1 was *"the RESULT cap wrong in two halves that were each correct
alone"*. This test is the guard against that recurring, and the guard is evaded by writing the
number with an underscore in it. The docstring at `:623` claims the assertion is made
*"by reading the module's own source rather than by trusting that nobody typed it"* - it does read
the source, and then trusts that whoever typed it typed it one of four ways.

**Suggested fix (NOT run).** Match on **value, not spelling**: parse the module with `ast` and walk
every `ast.Constant` whose `.value == 1000` (`ast` normalises `1_000`, `0x3E8` and `1000` to the
same int), plus every `ast.Constant` reachable from a `Subscript`/`Compare` in the slicing
positions. Assert none exists outside a docstring. That is spelling-independent by construction and
is roughly the same length as the current loop. A cheaper interim: import `JOBFEED_PAGE_CAP` from
`services/jobvite_client.py` and forbid `str(JOBFEED_PAGE_CAP)` **and** `f"{JOBFEED_PAGE_CAP:_}"` -
but that is another hand-kept list of spellings and I would not ship it as the fix.

---

## M3 - MEDIUM. U12's caller-visible C5-I1 arm is still unbuilt. The behaviour is correct today - I proved it - and nothing holds it there.

**`tests/test_tools_job_feed.py:210-360` at `bc0f958`** covers the **log** stream in three arms and
covers it well. U12's report says the exception-message arm was never built. It is still not built:
**no test asserts that the `detail` a jobFeed failure returns to the MCP caller carries no `sc=`.**

**I probed it.** A `MockTransport` handler raising `httpx2.ReadTimeout` whose message carries the
real feed URL:

```
timed out for url https://api.jobvite.com/v1/jobFeed?api=<key>&sc=<secret>&companyId=<id>
```

Results, both `ReadTimeout` and `ConnectError`:

```
CALLER-VISIBLE detail: "Jobvite did not respond before the configured timeout elapsed.
                        This is an upstream failure, not an open circuit breaker."
  FEED_SECRET in caller payload: False
  'sc=' literal present:         False
  FEED_SECRET anywhere in LOG stream: False
  'sc=[REDACTED]' present in log:     True
  error field -> ReadTimeout: timed out for url
                 https://api.jobvite.com/v1/jobFeed?api=[REDACTED]&sc=[REDACTED]&companyId=[REDACTED]
```

**No leak.** `detail` is enumerated prose, never `str(exc)`, and `redact_text` fired on the log
path - the `sc=[REDACTED]` line is the enforcement point having fired, which is the positive half
the arm needs.

**Failure this produces.** Not a live escape - a missing ratchet. The enumerated `detail` at
`errors.py` is one edit away from `str(exc)` (which is the shape R2-M5/L1 found and fixed on the
other stream), and that edit passes every test in the repository. The shared feed credential would
then reach the model, the model's host, and whatever logs the host keeps.

**Suggested fix - PARTIALLY RUN.** I ran the probe, so the arm's mechanics are proved to work; I did
not add the test, because `tests/` is read-only for me. The arm is:

```python
async def test_case2_a_jobfeed_transport_failure_carries_no_secret_to_the_caller() -> None:
    # positive half FIRST: the exception text really does carry `sc=` before redaction
    url = f"https://api.jobvite.com/v1/jobFeed?api={FEED_KEY}&sc={FEED_SECRET}&companyId={COMPANY_ID}"
    assert f"sc={FEED_SECRET}" in url, "the probe URL carries no secret; this arm would be vacuous"
    ...  # MockTransport handler raising httpx2.ReadTimeout(f"timed out for url {url}", request=request)
    result = await client.call_tool(GET_JOB_FEED, {"params": {}}, raise_on_error=False)
    assert result.is_error, "the call succeeded; the absence below would be vacuous"
    text = json.dumps([b.text for b in result.content])
    assert FEED_SECRET not in text, text
    assert f"sc={FEED_SECRET}" not in text, text
```

The full runnable probe is at "Artefacts" below. **Note the value half:** assert
`f"sc={FEED_SECRET}"` absent, not `"sc="` absent - `tests/test_tools_job_feed.py:280-288` records
by measurement why the literal-token form is the wrong assertion.

---

## M4 - MEDIUM. The audit event cannot answer "did this write email a live person?" `send_email` is redacted to `[REDACTED:bool]`. Fix MEASURED SAFE.

**`src/fast_mcp_jobvite/utils/redaction.py:114-124` (`NON_SENSITIVE_ARGUMENT_KEYS`) at `bc0f958`.**

Probed: one approved `create_candidate` on the handshake era, reading the real loguru stream. Both
audit events carry:

```json
{"first_name": "[REDACTED:str]", "last_name": "[REDACTED:str]", "email": "[REDACTED:str]",
 "job_eid": "[REDACTED:str]", "mobile": "[REDACTED:NoneType]", "source": "[REDACTED:NoneType]",
 "send_email": "[REDACTED:bool]"}
```

The four PII values are correctly absent in the clear (verified individually, and across the whole
log stream, not just the audit event). **`send_email` is redacted too** - and it is a boolean with
no content to protect.

**Why this is a finding rather than a nit.** `DESIGN.md:1719` row **C1-T1** names *"flipping
`send_email` to `true`"* as a **High** threat. `DESIGN.md:242` makes its `false` default a safety
property. The redaction module's own docstring (`utils/redaction.py:39-42`) states the purpose of
`NON_SENSITIVE_ARGUMENT_KEYS`: the record should show *"which arguments were supplied and of what
shape - which is what makes the event auditable"*. For every other argument, shape is enough. For
this one, **the shape IS the value** - `bool` is the whole domain - and redacting it means the
audit trail, the artefact a compliance reader consults after the fact, cannot distinguish a write
that emailed a real human from one that did not.

`DESIGN.md:1072` says `send_email` *"is an argument like any other"*, which is what the current
behaviour implements. I am reporting that the design line and the C1-T1 row pull in opposite
directions on this one field, and that the audit surface is where it matters.

**Suggested fix - RUN, and it is safe.** Add `"send_email"` to `NON_SENSITIVE_ARGUMENT_KEYS` after
`"eId"` (`utils/redaction.py:124`):

```
Mutation F1: anchor unique, landed, full suite -> 663 passed, 6 deselected, PYTEST_EXIT=0
```

Nothing breaks. **The same run also proves the other direction: no test asserts `send_email` is
redacted either**, so the current behaviour is unpinned in both directions. The set's stated
admission rule at `:120-125` is *"structurally an identifier, a bound or a page cursor"* - a bool
flag is none of those, so **the rule needs one sentence widened along with the entry**, or the
comment becomes the next thing that disagrees with its own list. Pair it with an arm asserting the
audit event carries `"send_email": true` on the `send_email=True` path
(`tests/test_approval_write.py:942` already drives that path).

**This is the one suggested fix in this report I actually executed.** The other seven are
hypotheses.

---

## L1 - NIT. The named guard on the era discriminator asserts that two literals the test wrote itself are equal, and never calls the function it claims to protect.

**`tests/test_approval_write.py:315-334` at `bc0f958`**
(`test_the_discriminator_is_protocol_version_and_not_transport_or_session_id`).

The brief asks: can it pass against an implementation that reads the right attribute and then
ignores it? **Yes, trivially** - it never reaches `resolve_approval`. Its body calls only
`observed_protocol_version`, a four-line `getattr` helper (`approval.py:224-243`). Its two "trap"
assertions are:

```
331:    assert sessionless.transport == handshake.transport
332:    assert sessionless.session_id == handshake.session_id
```

on two `_FakeCtx` objects the same test constructs at `:292-298` with the **hardcoded identical
literals** `"streamable-http"` and `"3bd41cb2-0000-0000-0000-000000000000"` (`:282-283`, `:297-298`).
They assert that a literal equals itself. The docstring at `:320-325` claims the case protects
against *"a later refactor swapping the discriminator for one of the two"*; it cannot, because
swapping the discriminator does not change either literal.

**The mitigating measurement, and it is why this is a nit and not a Medium.** The branch IS covered,
by other cases. Mutation **M2** at `src/fast_mcp_jobvite/approval.py:399` - `if version in
MODERN_PROTOCOL_VERSIONS:` -> `if version not in HANDSHAKE_PROTOCOL_VERSIONS:`, i.e. exactly the
`else` the U10 report says was deliberately avoided - was **KILLED**:

```
FAILED tests/test_approval_write.py::test_an_unidentifiable_era_refuses_and_logs_the_observed_value
FAILED tests/test_approval_write.py::test_an_absent_protocol_version_refuses
2 failed, 40 passed in 1.56s      PYTEST_EXIT=1
```

`test_the_discriminator_..._session_id` was among the 40 that passed. The two cases that killed it
are the ones doing the work; the one named for the job is the one that is not.

**Suggested fix (NOT run).** Give the case a body that matches its name: drive `resolve_approval`
with the two fakes and assert the returned `ApprovalDecision.mechanism` differs
(`SAMPLING` vs `ELICITATION`), then re-run with `transport` and `session_id` made **unequal** on the
two fakes and assert the mechanisms are unchanged - the negative control for what must NOT matter.
Delete the two literal-vs-literal assertions; they are the part that reads as rigour.

---

## L2 - NIT. The write's PII-absence assertion checks one of four values, and only `arguments`.

**`tests/test_approval_write.py:754-772` at `bc0f958`.** `:772` is
`assert VALID_ARGS["email"] not in serialised`. `first_name`, `last_name` and `job_eid` - all in
`VALID_ARGS`, all submitted, `first_name`/`last_name` all PII - are not checked. And `:771`
serialises only `[e["arguments"] for e in events]`, where U8's sibling
(`tests/test_tools_candidates.py:943`) serialises the **whole event**.

**Behaviour is correct** - I probed all four across the whole log stream and every one is
`[REDACTED:str]`. This is a partial check that happens to be looking at the leak-free field.

**Answering the brief's other question while I am here: U8's §8 #5 shape does NOT repeat here.** For
`create_candidate` the arguments genuinely ARE the PII, so this assertion is about a real path, not
a vacuous one. I checked the other four `arguments`-absence assertions in the tree
(`tests/test_audit.py:157`, `:211`, `tests/test_logging_process.py:196`,
`tests/test_tools_jobs.py:336`) - all four assert a redacted or admitted **value is present**, not
that something is absent, so none can be vacuous in #5's way. **§8 #5 appears to be the only
instance of that shape**, and I looked at every `arguments` assertion in `tests/`.

**Suggested fix (NOT run).** One line: `for value in VALID_ARGS.values(): assert value not in
serialised, (value, serialised)`, and serialise the whole event rather than `e["arguments"]`.

---

## L3 - NIT. The recorded value of the `ctx.transport` trap is not reproducible in this suite.

**`src/fast_mcp_jobvite/approval.py:32-35` at `bc0f958`** states *"`ctx.transport` is **identical**
on both eras (`'streamable-http'`)"*, and `tests/test_approval_write.py:282` builds the fake with
that literal.

Measured against the real `Context` on the in-memory transport the whole suite uses:

```
=== mode auto     ctx.transport = None   rc.protocol_version = '2026-07-28'
=== mode legacy   ctx.transport = None   rc.protocol_version = '2025-11-25'
transport EQUAL across eras: True
```

`ctx.transport` is `None` on both, not `'streamable-http'`. **The claim's substance holds** - it is
identical on both eras, so it is still useless as a discriminator - and the spike measured over real
streamable-HTTP where `'streamable-http'` is presumably right. But the fake asserts a value this
suite can never produce, so nothing would notice if the framework changed it.

Same probe, second observation worth recording: `session_id` is a **per-session UUID**, different on
every connection - `'12246fe0-...'` vs `'a6bf1451-...'`. The fake gives both eras the *same*
session_id, which makes L1's assertion pass; the real ones differ, which would make a
session_id-keyed discriminator fail loudly rather than quietly. The docstring's *"populated on
both"* is right; *"identical"* is only true of `transport`.

**Suggested fix (NOT run).** Reword `approval.py:32-35` to say `transport` is identical on both eras
**over streamable-HTTP** and `None` in-process, and cite `FASTMCP-SPIKE-4.md` for the former. In the
fake, either drop the `"streamable-http"` literal for `None` (matching what the suite can observe)
or leave it and add a comment saying it is the deployed value, not the measured one.

---

## L4 - NIT. A drained per-client bucket locks that client out at `initialize`, and only the negative arm documents that.

**`tests/test_http_hardening.py:665-676` and `:678-694` at `bc0f958`.**

Answering the brief directly: **yes, the positive arm is sequential-only** - `refusals()` at `:644`
awaits calls in a `for` loop and the two clients run one after the other, `:672` then `:673`.
**Nothing claims otherwise.** `docs/worklogs/U9-IMPL-REPORT.md:294` says *"Every limiter measurement
is sequential and single-client... Behaviour under **simultaneous** callers is unverified"*, and
`docs/adr/0002-in-process-rate-limiting.md:44` says the same. That is an honest record and I found
no overclaim anywhere in `src/`, `tests/`, the report or the ADRs.

What I did find while measuring it: **the bucket survives a reconnect** (good - a noisy integrator
cannot reset its own quota by opening a new session), and the way it survives is that the drained
client **cannot complete `initialize` at all**:

```
arm1 refusals of 12 = 8
SAME-token reconnect -> CONNECT_FAILED  MCPError: Rate limit exceeded for client: aa502ab6c0e58a5e
bystander reconnect  -> connected, 2 calls OK
```

`test_the_framework_default_throttles_everyone` (`:678`) documents the connection-level refusal for
the **global** keying as the thing that makes it worse. The identical behaviour on the **per-client**
keying is undocumented and untested. Note also the id in the message is the digest
(`aa502ab6c0e58a5e`), so `token_client_id` (`http_hardening.py:167`) is doing its job on the path
that actually publishes it.

**Suggested fix (NOT run).** Add one arm to `tests/test_http_hardening.py` asserting the drained
client's reconnect raises and the bystander's does not, in the same `serve_http` block - the
sequence above is the whole test. It pins two properties at once: the bucket is per-token, not
per-connection, and a drained client is locked out rather than degraded. Both are operator-visible
behaviour that nothing currently holds in place.

---

# What I did NOT verify

These are things I could not settle, not things I did not try.

- **The eight harnesses themselves were never executed.** I verified all eight are wired into
  `ci.yml` through `ci-harness-gate.sh` by reading, and I read the row-floor logic in
  `ci-harness-gate.sh:42, 168, 225-229` and in each of the four controls scripts. I did **not** run
  any of them: `scripts/` is read-only for me, a mutation harness owns the working tree for its
  whole run, and U9's is the ~13-minute one. **So H2 is proved by reading the gate's own contract
  and the four scripts, not by making U9's harness go green with rows deleted.** That experiment is
  the one thing that would settle it beyond argument, and it needs someone who may edit `scripts/`.
- **`shellcheck` was not run** - not installed in this environment. I changed no shell, so nothing
  I did could have broken it, but I cannot report an exit code.
- **`docs/reviews/check-standards-citations.py`** - unchanged by me and it needs a corpus at
  `/tmp/evolv-coder-standards/standards` that does not exist on this machine. CI is where its
  verdict comes from.
- **Whether the seven ungoverned framework middleware are individually dangerous.** I established
  that seven exist outside both lists and proved one of them (`LoggingMiddleware`) is both
  admissible and harmful. I did not classify `AuthMiddleware`, `DereferenceRefsMiddleware`,
  `DetailedTimingMiddleware`, `SlidingWindowRateLimitingMiddleware` or `ToolInjectionMiddleware`.
  `ToolInjectionMiddleware` is the one I would look at next, on its name alone: a middleware that
  can add tools sits upstream of the write gate and the scope map, and neither list would see it.
- **Behaviour under simultaneous rate-limited callers.** U9 says it is unverified, ADR-0002 says it
  is unverified, and I did not verify it either. My reconnect probe is still sequential.
- **Whether H3's negation-window fix (clause-scoped negators) has false positives on the real four
  files.** I measured that the current window has false *negatives* and how much of the corpus is
  shadowed. I did not run a clause-scoped variant over those files to see how many denials it would
  newly flag, because that is an edit to `tests/` and because the answer would change the fix's
  shape rather than its direction. **Whoever lands it should run it over the four files first and
  read every new hit** - the docstring's warning that the fix for a flagged denial is to tighten the
  sentence still applies.
- **Whether M4 is a design question rather than an implementation one.** `DESIGN.md:1072` says
  `send_email` is an argument like any other; C1-T1 at `:1719` makes flipping it a High threat. I am
  reporting the tension and the measurement that the fix is safe. Deciding it may be an ADR, and
  **ADR-0029 is the next free number** (`docs/adr/` holds 0001-0028 at `bc0f958`; 0028 records that
  it was renumbered from a collision on merge). I did not write one - the brief asks for a Proposed
  ADR only for a defect in the FROZEN design, and I found none.
- **The four `[INFERRED]` write-route items, `outbound_rate_limit`, and the open questions in
  ADR-0024 through ADR-0028.** Known and excluded by the brief. I did not re-derive them and I found
  nothing treating any of them as verified.

---

# Artefacts

Three runnable probes and one scan, all written to `/tmp` during this review and reproduced here so
they do not have to be rewritten. None was committed to `src/`, `tests/` or `scripts/`.

**1. The dual-default AST scan (M1).** Walks every `ClassDef`/`AnnAssign` in the tree and reports
any field carrying both a `Field(default=...)` and an assignment. 88 files, 3 hits.

```python
import ast, pathlib
for p in sorted(pathlib.Path('.').rglob('*.py')):
    if any(part in ('.git', '.venv') for part in p.parts):
        continue
    for node in ast.walk(ast.parse(p.read_text(), filename=str(p))):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or stmt.value is None:
                continue
            for sub in ast.walk(stmt.annotation):
                if isinstance(sub, ast.Call) and (
                    getattr(sub.func, 'id', None) or getattr(sub.func, 'attr', None)
                ) == 'Field':
                    for kw in sub.keywords:
                        if kw.arg in ('default', 'default_factory'):
                            print(f"DUAL-DEFAULT {p}:{stmt.lineno} "
                                  f"class={node.name} field={stmt.target.id}")
```

**2. The era probe (L1, L3).** Registers a tool that reports `ctx.transport`, `ctx.session_id` and
`ctx.request_context.protocol_version`, then calls it once under `mode="auto"` and once under
`mode="legacy"` against a real `Client`.

**3. The jobFeed-failure probe (M3).** A `JobviteClient` on a `MockTransport` whose handler raises
`httpx2.ReadTimeout(f"timed out for url {URL}", request=request)` where `URL` carries `api=`, `sc=`
and `companyId=`; reads both the caller-visible `result.content` and every loguru record.

**4. The rate-limit reconnect probe (L4).** Drains `JOBS_TOKEN` on `limiter_server(per_client=True)`,
then opens a **new** `Client` with the same token and one with `CANDIDATES_TOKEN`.

Probes 2-4 need `PYTHONPATH` set to the repo root so `tests.*` imports resolve outside pytest.

---

# The six mutations, and the restore proof for each

Every row: anchor asserted unique **before** the write, landing proved by `cmp` against a backup,
restoration proved by `cmp` **and** `git diff --quiet`. `PYTHONDONTWRITEBYTECODE=1` throughout.

| # | File:line (`bc0f958`) | Mutation | Scope run | Result |
|---|---|---|---|---|
| M1 | `tools/jobs.py:124` | `default=None` -> `default="R7MUTANT"` in the inert `Field` copy | full suite | **SURVIVED** 663 passed, exit 0 |
| M2 | `approval.py:399` | `version in MODERN_...` -> `version not in HANDSHAKE_...` | `test_approval_write.py` | **KILLED** 2 failed, exit 1 |
| M3 | `tools/jobs.py:543` | a real transport cap, `_LOCAL_TRANSPORT_CAP = 1_000` | job_feed + jobs | **SURVIVED** 68 passed, exit 0 |
| M4 | `http_hardening.py:327` | `+ LoggingMiddleware(include_payloads=True)` | `test_http_hardening.py` | **SURVIVED** 29 passed, exit 0 |
| M4b | `http_hardening.py:327` | same | full suite | **SURVIVED** 663 passed, exit 0 |
| F1 | `utils/redaction.py:124` | `+ "send_email"` to `NON_SENSITIVE_ARGUMENT_KEYS` | full suite | **fix is SAFE** 663 passed, exit 0 |

Three survivors. Survivors are the output, not a failure - M1, M3 and M4 are H1, M1 and M2.

**Worktrees.** `/tmp/code-review-r7-work` (detached at `bc0f958`, for reading and every mutation)
and `/tmp/code-review-r7-report` (branch `review/r7`, this file only). **Both removed on
completion**, and `git worktree list` was read before either was created - `u14-arguments`,
`r2-fixes`, `r6-fixes` and `u7-resilience` were live and none was touched.
