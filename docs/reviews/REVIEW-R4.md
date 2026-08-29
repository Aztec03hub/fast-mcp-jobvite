# REVIEW-R4 - U5, `search_jobs`, reviewed for the first time

**Agent:** `code-review-r4` **Branch:** `review/r4` **Base SHA:** `555bad6`
**Frozen design:** `c15b138`, read only as `git show c15b138:docs/DESIGN.md`
**Worktree:** `/tmp/r4-work`, removed after this report was committed - see the last line.
**Scope:** READ-ONLY on `src/`, `tests/`, `scripts/`. Nothing under those three was edited. The
only file this branch adds outside this report is `docs/reviews/probe-r4-unmutated-anchors.sh`,
which is a probe, not a fix.

---

## The headline

**Four mutations of `search_jobs`'s shipped behaviour survive the entire 398-case suite**, and
three of them change what the tool actually asks Jobvite for. Separately, the module that holds
the inbound character rule **cannot be used at all** - the first model that declares its
`SafeText` type raises at class-construction time - and five independent verification layers each
reported that module as clean.

Both were reachable only by measurement. Neither is visible in the source, in the 12/12 mutation
result, in the 11/11 amputation result, or in the 100% coverage figure.

### On the two beliefs I was asked to challenge

**"12/12 mutation and 11/11 amputation mean its tests are sound."** They do not, and the way
they do not is specific rather than general. Both harnesses are *complete over the rows they
declare*, and the rows are well chosen. What neither harness contains is a single row about the
**outbound HTTP request**. The route, the query key and the query value are all unasserted, so
all three can be broken without a single test noticing (**R4-H1**). A harness proves its declared
rows fire; it says nothing about the rows nobody declared, which is the same shape as the U1
harness reporting "all fired" while its word for survivor meant "passed".

**"The areas I marked already-known are settled."** Two are not, and I have kept off the parts
that are:
- `ids` in `NON_SENSITIVE_ARGUMENT_KEYS` (`fbaa971`) - **not re-reported.** But `ids` is also
  never sent (**R4-H1**), so the argument that was deliberately un-redacted for its debugging
  value is recording a value that never leaves the process.
- The three structural limits "absent and RECORDED as absent" (`efd0fef`) - **the record is
  wrong**, which the brief says would be a new finding. The record says only the character rule
  is implemented and the structural limits are not. In fact the character rule is not
  implemented either: it is written down, it does not compile, and nothing calls it
  (**R4-H2**).

---

## Findings

Ranked by severity. Every one carries a suggested fix. `file:line` is from `grep -n` or a
numbered read throughout.

---

### R4-H1 (HIGH) - nothing asserts the outbound request, so the tool's only argument can be deleted and the suite stays green

**Measured, not argued.** `docs/reviews/probe-r4-unmutated-anchors.sh` on this branch, base
`555bad6`, whole suite per row, `PYTHONDONTWRITEBYTECODE=1`, restore checked with `cmp` against
a pristine copy taken before row 1:

```
########## BASELINE
====================== 398 passed, 5 deselected in 39.95s ======================

########## R4-P1 the ids query parameter never reaches the wire
  *** SURVIVED *** ====================== 398 passed, 5 deselected in 39.88s ======================

########## R4-P2 the ids query key is misspelled
  *** SURVIVED *** ====================== 398 passed, 5 deselected in 43.41s ======================

########## R4-P3 JOBS_PATH points at a route that does not exist
  *** SURVIVED *** ====================== 398 passed, 5 deselected in 45.55s ======================

########## R4-P4 JOBS_ENVELOPE_KEY names a key Jobvite never sends
  KILLED   ================= 4 failed, 394 passed, 5 deselected in 46.17s =================

########## R4-P5 TOTAL_ENVELOPE_KEY names a key Jobvite never sends
  KILLED   ================= 1 failed, 397 passed, 5 deselected in 45.81s =================

########## R4-P6 the read-only annotation is inverted
  *** SURVIVED *** ====================== 398 passed, 5 deselected in 47.46s ======================

########## ROWS: 6   SURVIVED: 4
TREE RESTORED - both files match the pristine pre-run copies.
```

The three that matter are P1, P2 and P3. All three mutate
`src/fast_mcp_jobvite/tools/jobs.py:294-300`:

```
294:                    payload = await client.request(
295:                        "GET",
296:                        JOBS_PATH,
297:                        params=(
298:                            {"ids": params.ids} if params.ids is not None else None
299:                        ),
300:                    )
```

- **P1** replaces the whole `params=(...)` expression with `params=None`.
- **P2** changes the query key to `{"id": params.ids}`.
- **P3** changes `JOBS_PATH: Final = "/job"` (`tools/jobs.py:75`) to `"/not-a-route"`.

**The failure each produces.** A caller asks for one job by `eId`. Jobvite receives no `ids`
parameter (P1), or one it does not recognise and therefore ignores (P2), and answers with the
**entire first page of requisitions**. The tool returns them, and the result says
`showing 50 of 1,240` - a wrong answer that explains itself and looks exactly like a correct one.
P3 is louder in production but equally invisible offline.

This is precisely the failure mode `SearchJobsInput`'s own docstring says the date filter was
withheld to avoid (`tools/jobs.py:88-96`): *"Sending a parameter whose name we guessed would be
silently ignored by Jobvite, and the tool would then return an unfiltered page while the caller
believed it was filtered - a wrong answer that explains itself."* The reasoning is right. It was
applied to the parameter that was **not** shipped and not to the one that **was**.

**Why nothing caught it.** Every offline case drives a `MockTransport` that answers whatever it
is asked. The suite already has the instrument: `client_factory(..., seen=seen)` collects the
`httpx2.Request` objects, and `tests/test_tools_jobs.py:720-721` uses it to assert the
credential headers. **No case ever reads `seen[0].url`.** Verified with `grep -n` over the whole
test file: the only `seen[0]` references are lines 720 and 721, both headers.

`readOnlyHint` (P6) also survives, but `tools/jobs.py:262-265` already states it is advisory and
never counted as a control, so I am not raising it - it is recorded here so the row is not read
as an oversight.

**Suggested fix.** One case, using the mechanism that is already there, plus its paired arm:

```python
async def test_the_ids_argument_reaches_the_wire_as_a_query_parameter() -> None:
    seen: list[httpx2.Request] = []
    server = build_server(
        settings(), client_factory=client_factory(fixture_bytes(JOB_LIST_SUCCESS), seen=seen)
    )
    async with Client(server) as client:
        await client.call_tool(SEARCH_JOBS, {"params": {"ids": "TESTJOB1"}})
    assert seen[0].url.path.endswith(JOBS_PATH)
    assert seen[0].url.params["ids"] == "TESTJOB1"


async def test_omitting_ids_sends_no_ids_parameter() -> None:
    # The paired direction: a default call must not send an empty filter.
    ...
    assert "ids" not in seen[0].url.params
```

Then add P1, P2 and P3 as rows to `scripts/check-u5-jobs-controls.sh`, so the new case cannot
rot back into a name without a body. The anchors are in the probe script on this branch and are
copy-pasteable.

---

### R4-H2 (HIGH) - `SafeText` cannot be used: the inbound character rule is written down, does not compile, and has no caller

`src/fast_mcp_jobvite/utils/constraints.py:82` builds the character rule out of a **negative
lookahead**:

```
82:_NO_FORBIDDEN = f"\\A(?:(?![{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]).)*\\z"
```

pydantic-core compiles patterns with the Rust `regex` crate, which has **no look-around at all**.
Declaring one `SafeText` field raises at class-construction time. Verbatim:

```
pydantic_core._pydantic_core.SchemaError: Error building "model" validator:
  SchemaError: Error building "model-fields" validator:
  SchemaError: Field "v":
  SchemaError: Error building "str" validator:
  SchemaError: regex parse error:
    \A(?:(?![\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f‪-‮⁦-⁩]).)*\z
         ^^^
error: look-around, including look-ahead and look-behind, is not supported
```

**Five verification layers each passed over this, and each was defective in a different way.**

1. **Nothing calls it.** `grep -rn "SafeText\|PositiveCount\|FORBIDDEN_CHARACTERS\|MAX_TEXT_LENGTH"
   --include=*.py .` over the repo (excluding `.venv`) returns **six hits, all inside
   `constraints.py` itself** - lines 65, 79, 87, 100, 103, 122. Zero references in any other
   source file and zero in any test. So the pattern is never handed to pydantic and never
   raises.
2. **The coverage figure certified it.** U5's report records `utils/constraints.py 13 0 0 0 100%`
   against ADR-0010's 95% floor. The module is entirely module-level statements, so **importing
   it executes every line**. 100% here proves the file imports; it proves nothing about the types
   it defines. This is the strongest example in the unit of a green that tested nothing.
3. **The mutation harness aims at the wrong type.** `scripts/check-u5-jobs-controls.sh:237-240`
   (row M10) mutates `JobviteIdentifier`'s `pattern=r"\A[A-Za-z0-9_-]+\z"`. That is the
   identifier alphabet, not the character rule. `_NO_FORBIDDEN` has no row.
4. **The test named for the character rule does not exercise it.** `tests/test_tools_jobs.py:636`
   is `test_a_control_character_or_bidi_override_is_rejected`, its docstring cites the
   control-character clause, and its body is `SearchJobsInput(ids=value)` - so all six arms (NUL,
   bell, C1, RLO, RLI, trailing newline) are refused by `JobviteIdentifier`'s **alphabet**, which
   admits only `[A-Za-z0-9_-]`. Delete the character rule entirely and every arm still passes.
   **This is the sibling of the M3 defect U5 found itself** - an assertion whose name claims one
   subject and whose body exercises another.
5. **The module's own "MEASURED" comment measured the wrong thing.** `constraints.py:73-81`
   correctly records that `\z` and not `\Z` is required because the Rust engine rejects `\Z` - and
   then never checks whether the surrounding pattern compiles. A measurement of one token inside
   an expression that does not compile.

**The failure this produces.** `constraints.py:149-152` names the trigger: *"whichever unit lands
the first model with a nested field owns implementing these three."* U8's `create_candidate`
carries free text, will import `SafeText` exactly as the module instructs, and will get a
`SchemaError` at import - a crash that looks like U8's bug and is four units old.

**Suggested fix, measured rather than proposed.** The lookahead is not needed; a negated character
class expresses the same rule and both engines spell it identically:

```python
_NO_FORBIDDEN = f"\\A[^{_CONTROL_CHARACTERS}{_BIDI_OVERRIDES}]*\\z"
```

Measured on this stack:

```
proposed pattern: '\\A[^\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f-\\x9f‪-‮⁦-⁩]*\\z'
model built OK
  plain        ACCEPTED
  tab          ACCEPTED
  newline      ACCEPTED
  CR           ACCEPTED
  NUL          REJECTED
  bidi RLO     REJECTED
  bidi FSI     REJECTED
  DEL          REJECTED
```

That is exactly `DESIGN.md:178-179`'s rule: C0/C1 rejected **except** tab, newline and carriage
return; bidi overrides and isolates rejected; DEL rejected.

And the test that would have caught it, which is the more important half of the fix - it must
**declare a model**, because that is the only act that compiles the pattern:

```python
def test_safetext_can_actually_be_declared_on_a_model() -> None:
    """The pattern is compiled at class construction, not at validation.
    A type nobody declares is a rule nobody has run."""
    class Probe(BaseModel):
        model_config = ConfigDict(strict=True)
        v: SafeText
    assert Probe(v="ordinary text").v == "ordinary text"

@pytest.mark.parametrize(("label", "value"), [
    ("tab", "a\tb"), ("newline", "a\nb"), ("CR", "a\rb"),
])
def test_the_three_permitted_control_characters_pass(label, value): ...

@pytest.mark.parametrize(("label", "value"), [
    ("NUL", "a\x00b"), ("DEL", "a\x7fb"), ("RLO", "a‮b"), ("FSI", "a⁨b"),
])
def test_safetext_rejects_the_forbidden_set(label, value): ...
```

Plus a mutation row on `_NO_FORBIDDEN` itself, and a coverage note: **`constraints.py`'s 100% is
an import, not a test**, so its ADR-0010 floor should be read as unmet until the cases above
exist.

---

### R4-H3 (HIGH) - the credentialed arm cannot detect the one thing it exists to detect

`tests/credentialed/test_search_jobs_live.py:79-83` states its own purpose:

```
79:    Checklist rows 1-4 are blocking, and this is the case that
80:    converts the `job_list_success.json` fixture from synthetic to
81:    recorded: if the envelope key is not `requisitions`, or `total` is
82:    absent, the result model refuses the payload here and the research
83:    `[INFERRED]` marks were wrong.
```

**The result model does not refuse it.** `tools/jobs.py:181-185`:

```
181:    items = payload.get(JOBS_ENVELOPE_KEY) or []
182:    jobs = [_to_job(item) for item in items[:max_results] if isinstance(item, dict)]
183:    raw_total = payload.get(TOTAL_ENVELOPE_KEY)
184:    total = raw_total if isinstance(raw_total, int) else len(items)
185:    return JobSearchResult(jobs=jobs, total=total)
```

A missing envelope key gives `items = []`; a missing `total` falls back to `len(items)`. The
model is handed `jobs=[], total=0` and validates happily. Measured against a tenant that returned
1,240 real jobs under a different envelope key:

```
result: {'total': 0, 'showing': 0, 'summary': 'showing 0 of 0'} jobs: 0

test_search_jobs_against_a_real_tenant assertions:
  is_error is False              -> True
  parsed.total >= 0              -> True
  summary == showing N of total  -> True
test_the_result_cap_holds_against_a_real_page assertions (max_results=1):
  showing <= 1                   -> True
  showing <= total               -> True
```

**Every assertion in both live cases passes.** `parsed.total >= 0` is satisfied by `0`;
`showing <= 1` is satisfied by `0`; `summary` is self-consistent because it is derived. This is
the fail-closed-on-error / **fails-open-on-empty** shape: the error path is handled, the empty
path is not, and a wrong envelope key produces an empty page rather than an error.

The consequence is larger than one test. `docs/research` marks the `requisitions` key, the `total`
member and every requisition field name as `[INFERRED]`, and this arm is the **only** mechanism
in the repository that converts them to recorded. It has never run, so nobody has seen that it
cannot.

**Suggested fix.** The tool deliberately drops the envelope, so the live arm cannot settle the
contract by looking at the tool's output. Settle it one level down, at the payload:

```python
async def test_the_live_envelope_uses_the_inferred_keys(live_settings: Settings) -> None:
    """Checklist rows 1-4. Asserted on the RAW payload, because the tool
    drops the envelope and an absent key is indistinguishable from an
    empty tenant once it has."""
    async with JobviteClient(
        api_key=live_settings.api_key, api_secret=live_settings.api_secret
    ) as client:
        payload = await client.request("GET", JOBS_PATH, params=None)
    assert JOBS_ENVELOPE_KEY in payload, f"envelope key is not {JOBS_ENVELOPE_KEY}: {sorted(payload)}"
    assert TOTAL_ENVELOPE_KEY in payload, f"total member absent: {sorted(payload)}"
    assert isinstance(payload[TOTAL_ENVELOPE_KEY], int)
```

and add to `docs/CREDENTIAL-CHECKLIST.md` the precondition that makes the existing cases
non-vacuous: **the tenant used must have at least one open requisition**, otherwise
`showing 0 of 0` is a correct answer and the arm proves nothing either way. Then change
`test_search_jobs_against_a_real_tenant`'s `parsed.total >= 0` to `parsed.total >= 1` and
`test_the_result_cap_holds_against_a_real_page`'s `showing <= 1` to `showing == 1`, which are
only meaningful with that precondition stated.

---

### R4-M1 (MEDIUM) - the fencing registry is rooted at a hand-named model, so the payload model itself has no decisions

The brief asks whether the fencing registry is an enumeration of something the code already
knows. It is not. Every call site names `Job` as the root by hand:

```
tests/test_tools_jobs.py:468:    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
tests/test_tools_jobs.py:483:    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
tests/test_tools_jobs.py:541:    paths = fencing_paths(Job, JOBS_ENVELOPE_KEY + "[]")
```

`JobSearchResult` is the model that is actually serialised to the caller, and it is not in that
set. Measured:

```
JobSearchResult fields: ['jobs', 'total']
JobSearchResult computed: ['showing', 'summary']
RAISES: JobSearchResult.jobs carries 0 fencing decisions; exactly one Fenced
        annotation is required (DESIGN.md:202-205)
```

So the top-level output model **cannot pass its own registry**, and no test asks it to. Its
`summary` field is a caller-facing string built from data, and `fencing_paths` walks
`model_fields` only (`models/fencing.py:177`) - `model_computed_fields` is never visited, so a
computed field can never carry a decision at all.

`DESIGN.md:202-205` says *"a test fails when any model field has no fencing decision"*. Today the
test fails when any field of the one model somebody remembered to name has no decision. When U8
adds `models/candidate.py` - the model where the answer is `FENCE` rather than `NOT_FREE_TEXT` -
it gets zero coverage until someone widens a literal, which is the failure the generated design
exists to prevent, moved up one level.

**Suggested fix.** Enumerate the container and assert the two sets are equal, rather than naming
members:

```python
def _output_models() -> set[type[BaseModel]]:
    """Every BaseModel defined in fast_mcp_jobvite.models.*, discovered."""
    found = set()
    for mod in pkgutil.iter_modules(fast_mcp_jobvite.models.__path__):
        m = importlib.import_module(f"fast_mcp_jobvite.models.{mod.name}")
        found |= {
            o for o in vars(m).values()
            if isinstance(o, type) and issubclass(o, BaseModel) and o.__module__ == m.__name__
        }
    return found

def test_every_output_model_in_the_package_has_a_complete_fencing_registry() -> None:
    for model in _output_models():
        fencing_paths(model, model.__name__)   # raises if any field is undecided
```

That requires a decision on `JobSearchResult.jobs`, `.total`, and - once `fencing_paths` also
walks `model_computed_fields` - on `showing` and `summary`. All four are `NOT_FREE_TEXT`
(container, integer, integer, derived string), so the fix is four annotations plus the walker
change, and after it the registry is closed by construction rather than by memory.

If a model must legitimately be exempt, the exemption belongs in an explicit named set that the
same test asserts is a subset of the discovered container - never in the absence of a call.

---

### R4-M2 (MEDIUM) - ten inline `DESIGN.md` citations point at the wrong paragraph, consistently landing one paragraph short

The brief asked me to spot-check U5's standards citations. **They are clean** - see "What I
checked and found correct" below. What is not clean is the population next to them: U5's own
`DESIGN.md:N-M` citations. There are **47 distinct ranges** across the unit and the ones I
resolved fail in a consistent direction - they name the paragraph *before* the subject.

All ranges below are from `git show c15b138:docs/DESIGN.md`, read with `grep -n`.

| Cited as | Used for | Where the subject actually is | Uses |
|---|---|---|---|
| `DESIGN.md:186-190` | "a new Jobvite field is dropped until someone admits it deliberately" | **192-195**. 186-190 is the inbound-rejection status-code paragraph (400 vs 422) - a different subject entirely | **7** |
| `DESIGN.md:181-183` | "tab, newline and carriage return, the three permitted ones"; bidi named beside the control characters | **178-179**. 181-183 is *"What a caller receives when one of these limits fires"* | 2 |
| `DESIGN.md:156` | "explicit `max_length` on every string"; "a regex on every identifier" | **152-154**. 156 is the four-structural-limits sentence. The unit cites the correct `:154` once, so it spells one clause two ways | 2 |
| `DESIGN.md:216-220` | "the only unconditionally enforceable gate this design has" | **228-229**. 214-222 is the destructive-operations approval clause | 2 |
| `DESIGN.md:296` | "allow-listed OUTPUT models, one file per tool" | **291**. 296 is a continuation line of the `utils/constraints.py` row | 1 |
| `DESIGN.md:294-296` | "Tool bodies and their INPUT models" | **289-290**. 294-296 is `utils/normalise.py` and `utils/constraints.py` | 1 |

The seven `186-190` uses, from `grep -rn "DESIGN.md:186-190" src tests scripts`:

```
src/fast_mcp_jobvite/models/jobs.py:1
src/fast_mcp_jobvite/models/jobs.py:6
src/fast_mcp_jobvite/tools/jobs.py:121
tests/test_tools_jobs.py:420
tests/test_tools_jobs.py:441
scripts/check-u5-jobs-controls.sh:223
scripts/check-u5-jobs-amputation.sh:234
```

`DESIGN.md:216-220` is at `server.py:111` (`git blame` confirms `33ded1f6`, U5's own commit) and
`scripts/check-u5-jobs-amputation.sh:221`. `DESIGN.md:181-183` is at `constraints.py:49` and
`:56`; `DESIGN.md:156` at `constraints.py:84` and `:109`.

**Why this matters more than tidiness.** `DESIGN.md` is frozen at `c15b138` and U5 read it at
`c15b138`, so these are not drift - they were wrong when written. A citation that resolves to a
plausible neighbouring paragraph is the failure mode this project has already recorded twice:
it reads as verified, and the next agent propagates it. It is also the exact population
`check-clause-citations.py` does **not** cover - that checker resolves `OBLIGATIONS.md`'s clause
column, which is a different set.

**Suggested fix.** Two parts, and the second is the one that lasts.

1. Repoint the ten sites above, **by parsing** rather than by retyping: for each, `grep -n` the
   subject phrase in `git show c15b138:docs/DESIGN.md` and take the number the grep prints.
2. Stop citing line numbers into a frozen document from source comments, and cite the **section**
   instead - `DESIGN.md §2.2 "Outputs are allow-listed models"`. A section heading is unique,
   survives a reflow, and a checker can resolve it by searching for the heading text rather than
   by trusting an integer. If line numbers are kept, they need the same treatment
   `OBLIGATIONS.md` got at `afaf226`: an anchor phrase that must be present, not a number that
   silently still resolves to something.

---

### R4-M3 (MEDIUM) - a mutation row whose test has been renamed reports KILLED forever

`scripts/check-u5-jobs-controls.sh:95-113` runs one named selector and treats any non-zero exit
as a kill:

```
 95:  uv run --frozen pytest "$selector" -q -p no:cacheprovider >"$OUT" 2>&1
 96:  local rc=$?
...
106:  if [ "$rc" -ne 0 ]; then
107:    FIRED=$((FIRED + 1))
108:    echo "  KILLED - the named test went red, as it must"
```

pytest exits **4** when a selector matches nothing. Positive control, run on this branch:

```
collected 0 items

============================ no tests ran in 1.18s =============================
EXIT=4
```

So a renamed, moved or misspelled test makes its row report `KILLED` on every run, forever, while
testing nothing - and the CI step's `fired == total` check passes. The row would then be a green
that tested nothing sitting inside the harness whose whole purpose is to find greens that tested
nothing.

**All eleven selectors resolve today** - I checked each with `grep -c "def <name>" tests/test_tools_jobs.py`
and every one returned `1` - so this is latent, not live. It is specific to U5: `check-u3-audit-controls.sh:97`
and `check-u4-client-controls.sh:86` run the whole `$SUITE`, where a rename is caught by the
baseline instead.

**Suggested fix.** One guard in `mutate()`, before the mutation is applied, so the harness refuses
rather than reporting:

```bash
  if ! uv run --frozen pytest "$selector" --collect-only -q -p no:cacheprovider \
       >/dev/null 2>&1; then
    echo "  SELECTOR DOES NOT RESOLVE - the test was renamed or moved. Fix the harness."
    return          # TOTAL is already incremented, so fired != total and CI fails
  fi
```

The same guard belongs in `check-u1-boot-controls.sh:73`, which also runs a named selector.

---

### R4-M4 (MEDIUM) - both U5 CI steps pass against a harness with zero rows

`.github/workflows/ci.yml:394-398`:

```
394:          line=$(printf '%s\n' "$out" | grep -oE '[0-9]+/[0-9]+ controls fired\.' | tail -1)
395:          [ -n "$line" ] || { echo "::error::no 'N/M controls fired.' line"; exit 1; }
396:          fired=${line%%/*}; rest=${line#*/}; total=${rest%% *}
397:          [ "$fired" = "$total" ] || {
398:            echo "::error::only $fired of $total U5 controls fired"; exit 1; }
```

`0 = 0` satisfies line 397, and `check-u5-jobs-controls.sh:254` (`[ "$FIRED" -ne "$TOTAL" ]`)
exits 0 for the same reason. `ci.yml:406-411` has the identical hole: `ROWS: 0 ANCHORS APPLIED: 0`
passes. **A harness whose rows were all deleted or all silently skipped is fully green.**

This is the same argument U5 itself made, correctly, three steps earlier for the credentialed
collect (`ci.yml:361-365`): *"FLOORED, not merely non-empty ... a count is what catches the
HALF-empty case."* The reasoning was applied to the credentialed step and not to the unit's own
two harness steps.

**Suggested fix.** One line per step, the same shape as `check-suite-floor.sh`:

```bash
          [ "$total" -ge 12 ] || { echo "::error::U5 mutation harness has only $total rows"; exit 1; }
```

```bash
          [ "$rows" -ge 11 ] || { echo "::error::U5 amputation harness has only $rows rows"; exit 1; }
```

Lowering either number is then a visible diff that has to be defended, which is the property the
suite floor already has. **Note:** `fix/harness-gates` merged at `b0d7729`, after my base
`555bad6`, and routes all 13 steps through `scripts/ci-harness-gate.sh`. Check whether the row
floor landed with it before filing; the hole itself is independent of the refactor.

---

### R4-M5 (MEDIUM) - the amputation harness reports the vacuous shape and gates on something else

`scripts/check-u5-jobs-amputation.sh:283-288` gates only on `APPLIED == ROWS`. The property the
harness exists to establish is stated in its own header (`:15-18`) and in U5's report - *"No row
survived 34/34, which is the vacuous shape"* - and **nothing checks it**. A row that kills zero
tests prints its survivors and passes CI.

The per-row kill count is already computed: the run's `tail -1` line is captured at `:112` and
the survivor list at `:114`. The failing count is one `grep` away.

**Suggested fix.** Track it and gate on it, keeping survivors as output:

```bash
  local killed
  killed=$(grep -cE '^FAILED ' "$OUT" || true)
  if [ "$killed" -eq 0 ]; then
    echo "  *** VACUOUS ROW *** the behaviour was deleted and nothing went red."
    VACUOUS=$((VACUOUS + 1))
  fi
```

then `[ "$VACUOUS" -eq 0 ] || exit 1` beside the existing anchor gate, and a matching
`grep -q 'VACUOUS ROW'` in `ci.yml:400-411`. Use `grep -cE '^FAILED '` rather than the summary
line: `grep -c "^FAILED"` on pytest misses `ERROR` entirely, so pair it with an `ERROR` check or
read the exit code of the run.

---

### R4-L1 (LOW) - `_to_job` is a hand-kept list beside `Job`, and a field added to one and not the other is silently always-null

`tools/jobs.py:132-152` names all ten `Job` fields by hand. `Job.model_fields` is:

```
['apply_link', 'category', 'department', 'description', 'eid', 'job_state',
 'last_updated_date', 'locations', 'sent_date', 'title']
```

The two agree today. Nothing makes them agree tomorrow: add `salary` to `Job` with a `Fenced`
annotation and every fencing test passes, `_to_job` never sets it, the field defaults to `None`,
and **every result silently omits it**. The allow-list is correct to be explicit - `tools/jobs.py:117-124`
argues that well - but explicit is not the same as checked.

**Suggested fix.** One case asserting the two sets are equal, driven from the model rather than
from a literal:

```python
def test_to_job_maps_every_admitted_field() -> None:
    """A field on the model that _to_job never sets is silently always-null."""
    raw = {f.alias or f.metadata[0].jobvite_key: "x" for name, f in Job.model_fields.items()}
    # simpler and more direct: drive a raw object carrying every Jobvite key
    # the annotations name, and assert no admitted field came back None.
    raw = {_decision_of(Job, n).jobvite_key: _sample_for(Job, n) for n in Job.model_fields}
    job = _to_job(raw)
    unset = [n for n in Job.model_fields if getattr(job, n) in (None, "", [])]
    assert not unset, f"_to_job never sets: {unset}"
```

The `Fenced.jobvite_key` annotations already carry Jobvite's spelling for every field, so the
Jobvite-side key set is derivable and does not need a second literal list.

---

### R4-L2 (LOW) - `getattr(ctx.request_context, "meta", None)` turns a library rename into silent trace loss

`tools/jobs.py:285`:

```
285:        meta = getattr(ctx.request_context, "meta", None)
```

The comment two lines above records that this attribute was **measured** to exist on
fastmcp 4.0.0b4. Given that, the `None` default guards against nothing that is currently true and
converts a future rename into exactly amputation row A11 - trace context silently dropped from
every audit event, at exit 0, with no error anywhere.

The suite does catch it (`test_composition_risk3_the_live_context_meta_is_the_wire_meta`), which
is why this is Low rather than Medium: the failure would surface at the next dependency bump, in
a test rather than in production. But the default makes the *runtime* fail open on a property the
audit trail depends on.

**Suggested fix.** Read the attribute directly - `meta = ctx.request_context.meta` - so a rename
is an `AttributeError` at the call site rather than a silently absent trace id. If the defensive
form is wanted for a reason I cannot see, the reason belongs in the comment, since the comment
currently argues the opposite.

---

### R4-L3 (LOW) - the `\A`/`\z` rationale promises something `SafeText` does not deliver

`constraints.py:67-71`:

```
67:#: A pattern admitting only strings that contain no forbidden
68:#: character. `\A` and `\z` rather than `^`/`$`: in Python `$` also
69:#: matches before a trailing newline, so `^...$` would admit a string
70:#: ending in one - and a trailing newline in a field that reaches a
71:#: log line is the log-forging shape C7-T1 records.
```

The anchor choice is right, but newline is in the **permitted** set, so `\A...\z` admits
`"ab\n"` anyway. Measured against the corrected pattern from R4-H2: `trailing NL ACCEPTED`. The
log-forging protection the comment claims is real only for `JobviteIdentifier`, whose alphabet
excludes `\n` - and it is `JobviteIdentifier` that the "trailing newline" test arm at
`tests/test_tools_jobs.py:633` actually exercises.

**Suggested fix.** Rewrite the comment in place (not append) to say what is true: `\z` is required
because `\Z` does not exist in the Rust engine and because `$` would make the anchor meaningless,
and note that a trailing newline is **admitted** by `SafeText` by design since newline is
permitted. If a trailing newline should in fact be refused in log-bound fields, that is a separate
constraint type and a separate decision - not a property of this anchor.

---

### R4-N1 (NIT) - the restore check in both harnesses cannot fail on the path it describes

`check-u5-jobs-controls.sh:100-104` and `check-u5-jobs-amputation.sh:106-110`:

```
100:  cp "$backup" "$file"
101:  if ! cmp -s "$file" "$backup"; then
102:    echo "  RESTORE FAILED - $file still differs. STOPPING."
```

After `cp b f`, `cmp f b` compares equal by construction. The check detects only a failed `cp`
(which, with `set -uo pipefail` and no `-e`, would otherwise pass silently) - it cannot detect a
corrupted backup, which is what "the tree still carries this row's mutation" would actually mean.
The **landing** check at `:88` / `:96` is real and is the one doing the work.

**Suggested fix.** Compare against a pristine copy taken before row 1, as
`docs/reviews/probe-r4-unmutated-anchors.sh` on this branch does:

```bash
cp "$F" "$PRISTINE_DIR/tools_jobs.py"     # once, before any row
...
cmp -s "$F" "$PRISTINE_DIR/tools_jobs.py" || { echo "::error::TREE IS DIRTY"; exit 3; }
```

Or keep the per-row `cp` and check its exit code directly, which is what the current form is
really testing.

---

## What I checked and found correct

Recorded because a negative result is evidence, and because the first of these was the brief's
top-priority item.

**U5's standards citations resolve at source.** This was U5's own sharpest self-reported gap and
the team lead's highest-value item. I opened the TIER-1 standards at
`/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/` and resolved
every standards clause U5 relies on, directly or through `DESIGN.md`:

| Citation | Where cited | Verdict at source |
|---|---|---|
| `ai/tool-calling.md:171-173` | `tests/test_tools_jobs.py:302` | **Correct.** 171-173 is *"Log every tool invocation - tool name, validated arguments (PII redacted), result status, latency, and the request correlation id"*, which is exactly the four fields the test asserts |
| `ai/tool-calling.md:176-177` | via `DESIGN.md:657` | **Correct, verbatim.** *"Also attach the LLM trace/span id so a tool call ties back to its turn (trace IDs are separate from `request_id`)"* |
| `ai/prompt-injection.md:124-125` | via `DESIGN.md:173-174` | **Correct, verbatim.** *"Enforce input size/encoding limits before dispatch; reject control characters and oversized payloads"* |
| `backend/input-validation.md:220-226` | via `DESIGN.md:157` | **Correct.** The four-limit table (depth 5, 1,000 items, 100 keys, 1 MiB) is at 221-226 |
| `ai/prompt-injection.md` (unversioned) | `models/jobs.py:87` | **Correct in substance** - the standard does address the outside-the-organisation authored class. No line number is given, so nothing can be mis-transcribed |
| `error-contract.md` (unversioned) | `models/fencing.py:52`, `tests/test_tools_jobs.py:288` | **Correct in substance**; no line number given |

**Nine wrong-subject citations have been found on this project, four of them inside the ADR
recording that defect class. U5's standards citations are not among them.** The defect it feared
is not there; the same defect in the population next to it is (R4-M2), which is worth knowing as
a fact about where to look next time.

Also checked and correct:

- **`DESIGN.md:202-205`, `:469-477`, `:487-489`, `:639-650`, `:646-650`, `:162-164`, `:471-473`,
  `:917-934`** all resolve to their claimed subject at `c15b138`. The wrong ones in R4-M2 are a
  minority of the 47.
- **All eleven mutation selectors resolve** (`grep -c "def <name>"` returned 1 for each) - the
  R4-M3 defect is latent, not live.
- **The envelope constants are load-bearing.** R4-P4 and R4-P5 both killed, 4 and 1 failures
  respectively, because `docs/research/fixtures/job_list_success.json` pins the literal strings
  `"requisitions"` and `"total"` rather than building the fixture from the constants. Three
  in-file fixtures (`tests/test_tools_jobs.py:405`, `:422`, `:448`) *do* build from
  `JOBS_ENVELOPE_KEY` and would move with a mutation - the M3 shape - but the on-disk fixture
  saves them.
- **The `_meta` / structured-content split is right and is measured.** The `mode="serialization"`
  finding and the `model_validate` note in U5's report both reproduce.
- **The AST-based module-scope credential check** does walk the AST rather than grepping, which
  is the correct instrument for the reason U5 gives.

---

## Design defects

**None found in `docs/DESIGN.md` at `c15b138`, so I file no ADR.** The next free number is
**0022** and it is still unused.

R4-M2 is a defect in citations *into* the design, not in the design. R4-H2 is a defect in code
that the design describes correctly. `DESIGN.md:152-154`'s *"explicit `max_length` on every
string, regex on every identifier"* is right; the implementation of the first half is what does
not work.

One thing worth Phil's judgement rather than an ADR: **`DESIGN.md:202-205` says "a test fails
when any model field has no fencing decision" and does not say over which models.** R4-M1 is a
correct reading of it and so is U5's. If the intent is "every output model in the package", the
sentence would carry more if it said so - but that is an editorial improvement to a frozen
document, and it does not change what R4-M1 asks for.

---

## Outside my stated scope

R3 found its High outside its scope and said so; this is the same, said the same way.

**`check-u1-boot-controls.sh:73` runs a named selector** in the same shape as R4-M3 and has the
same exit-4 hole. I did not enumerate its selectors and I did not run it. **U3 and U4's harnesses
do not have this defect** - both run the whole `$SUITE`, verified at
`check-u3-audit-controls.sh:97` and `check-u4-client-controls.sh:86`. So the population is U1 and
U5, not all six. The fix in R4-M3 applies unchanged.

---

## Gates

Not run in full: this is a read-only review and my base `555bad6` is behind `main` (task #32
records `harness-gates` merged at `b0d7729` afterwards). What I did run, by exit code:

```
pytest tests/ -q                             398 passed, 5 deselected, 0 skipped     EXIT=0
pytest <nonexistent selector>                0 collected                             EXIT=4
docs/reviews/probe-r4-unmutated-anchors.sh   ROWS 6, SURVIVED 4, tree restored       EXIT=0
```

The floor derived from `ci.yml` per the PREAMBLE:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 398
```

**398 measured against a floor of 398, 0 skipped.** No `OBLIGATIONS.md` anchor was moved by this
branch - it adds two files under `docs/reviews/` and touches nothing else - so
`check-obligations.py` was not re-run.

---

## What I did NOT verify

For what I could not settle, not for what I did not try.

1. **Whether R4-M4's row floor already landed on `main`.** `fix/harness-gates` merged at
   `b0d7729`, after my base, and rewrote all 13 harness steps through
   `scripts/ci-harness-gate.sh`. I was told not to check anything out in the shared checkout and
   my worktree is pinned at `555bad6`, so I could not read the merged version. The hole is real at
   `555bad6`; whether it survived the refactor needs one read of `ci-harness-gate.sh` on `main`.
2. **Whether the R4-H1 fix would actually pass against Jobvite.** My suggested assertions pin
   `?ids=` as a query parameter on `GET /api/v2/job`, which is what `JOBVITE-CONTRACT.md` §7
   documents - but the contract also says whether `ids` accepts a comma-separated list is
   **unknown**, and I have no credential. The new case would pin our *outbound* behaviour, which
   is the gap; it does not settle whether Jobvite reads it that way. Checklist row 5 still owns
   that.
3. **The other 37 `DESIGN.md` citations in U5.** I resolved 10 wrong and 8 correct out of 47
   distinct ranges by reading `c15b138` directly. The remaining 29 I did not open. Given a 10/18
   error rate in the sample, **the true count is probably higher than ten** and R4-M2's table
   should be read as a lower bound, not a census. A one-pass checker over the whole population
   would settle it and is worth more than my finishing the list by hand.
4. **Whether `fencing_paths` recursing into `model_computed_fields` is safe on every model.** My
   R4-M1 fix asks for it; I did not implement or run it, and a computed field returning a nested
   `BaseModel` would need the same unwrapping `_nested_model` does for declared annotations. I do
   not know whether pydantic exposes the return annotation there in a form `_nested_model` can
   walk.
5. **The HTTP transport as a served socket.** U5 recorded this as unverified and I did not close
   it either - I asserted nothing about a bound port. Its statement of the limit is accurate and I
   am carrying it forward rather than re-deriving it.
6. **Whether R4-H3's suggested live case compiles against `JobviteClient`'s real signature.** I
   read `services/jobvite_client.py`'s Protocol satisfaction through U5's test but did not write
   or run the case, and the credentialed suite cannot be run without a key. Its `--collect-only`
   floor of 3 in `ci.yml:381` would need raising to 4 if the case is added.
7. **`readOnlyHint` surviving (R4-P6).** I recorded it and did not chase it. `tools/jobs.py:262-265`
   says it is advisory and never counted as a control, and I did not verify that claim against the
   framework myself - U5 says it did, and I took that.

---

**Worktree:** `/tmp/r4-work` removed after this report and the probe were committed on `review/r4`.
