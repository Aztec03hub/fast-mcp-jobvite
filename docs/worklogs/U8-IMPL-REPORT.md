# U8 - Candidate reads: models, normalisation, EEO exclusion, fencing

**Branch** `feat/u8-candidates`, from `187c210`. Worktree `/tmp/u8-candidates-work`, removed on
completion. Design read as `git show c15b138:docs/DESIGN.md` throughout; the working tree copy was
never used for a citation.

---

## 1. THE ORDERING RULE: what was written first, and what it proved

**The positive control was written first, and it was written before any source file existed.**
`tests/test_tools_candidates.py` was created with the positive control as its first case and the
structural assertions as its second section. Running it at that point produced:

```
tests/test_tools_candidates.py:44: in <module>
    from fast_mcp_jobvite.models.candidate import (
E   ModuleNotFoundError: No module named 'fast_mcp_jobvite.models.candidate'
=========================== short test summary info ============================
ERROR tests/test_tools_candidates.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

Then `utils/normalise.py`, then the fencing half of `utils/redaction.py`, then
`models/candidate.py`, then `tools/candidates.py`.

### What the control proved, MEASURED rather than argued

The plan's claim is that against a `search_candidates` returning an empty page, §8 #6, #5 and #20
all pass. **Amputation row A1 is that claim turned into an experiment**: `build_result` is
amputated so `items` is always `[]`, whatever Jobvite sent. Of 56 assertions, **exactly four go
red**:

```
FAILED test_positive_control_a_populated_candidate_round_trips
FAILED test_case19_the_fence_survives_the_whole_tool_path
FAILED test_the_cap_reads_total_from_the_envelope_not_from_the_items
FAILED test_the_result_cap_is_applied_to_the_page
```

**52 assertions survived a tool that returns nothing.** The plan was right, and the positive
control is one of only four things standing between this unit and a green suite over an empty tool.

### One correction to the plan's framing, and it cuts BOTH ways

The plan says #6, #5 and #20 are vacuous against an empty page. Measured, that is **true at the
tool level and false at the mapper level**: `test_case6_eeo_fields_in_the_payload_do_not_reach_the_result`
and the #20 cases drive `to_candidate` and `fence_payload` DIRECTLY on a fixture record, so they
are insensitive to what the tool returns and are not vacuous in the way the plan describes. They
have their own non-emptiness assertion inside them
(`assert emitted["eid"] == "TESTCND1", "the record is empty; this arm is vacuous"`).

**But #5 is worse than the plan says, and this is a finding.** `test_case5_candidate_pii_never_reaches_the_audit_record`
SURVIVES A1. It survives because the PII it asserts absent was never an argument in the first
place - the candidate's email and résumé are in the RESPONSE, and the audit event records
ARGUMENTS. So the assertion is true whether the tool returns two records or none, and the audit
event's own non-emptiness (which the paired positive case does assert) does not rescue it.

**Suggested fix, not applied because it belongs to whoever owns the audit surface:** the case that
would not survive is one asserting that a response-side PII value reaches a place we can prove the
redactor SAW - e.g. an arm that puts a candidate email into an argument (`search_candidates` has no
`query` today, deliberately) or a probe asserting `redact_arguments` was called with the record.
Today the honest statement is: **§8 #5 on this path asserts that the audit event carries no
response-side PII, and the mechanism guaranteeing that is that response data never enters the audit
event at all.** That is a real property and a weaker one than the case's name implies.

---

## 2. What was built

| File | What |
|---|---|
| `src/fast_mcp_jobvite/utils/normalise.py` | NEW. §9 hazards 1, 2 and 4, each in **both directions** |
| `src/fast_mcp_jobvite/models/candidate.py` | NEW. Allow-listed, `strict=True`, snake_case, **no EEO fields** |
| `src/fast_mcp_jobvite/utils/redaction.py` | The **fencing half** appended. U3's secret half untouched |
| `src/fast_mcp_jobvite/tools/candidates.py` | NEW. `search_candidates` and `get_candidate` |
| `src/fast_mcp_jobvite/server.py` | One import, one `register` call |
| `tests/test_tools_candidates.py` | NEW. 60 cases |
| `tests/test_server.py` | ONE existing case repointed - see §6 |
| `scripts/check-u8-candidates-controls.sh` | NEW. 25 mutation rows |
| `scripts/check-u8-candidates-amputation.sh` | NEW. 14 amputation rows |

### The five things the brief said were most likely to go wrong

1. **PATH-KEYED, NOT NAME-KEYED.** `candidates[].title` is FENCE (a job title the candidate typed
   into a form); `candidates[].application.job.title` is NOT_FREE_TEXT (a requisition title
   authored in the operator org, the same decision `models/jobs.py` records). Asserted both on the
   registry and by driving the real `fence_payload` over a payload carrying both. Mutation **M7**
   replaces the exact lookup with a leaf-name lookup and is killed.
2. **#19's red-team cases go past the seed.** Eight parametrised rows, including a bare OPENING
   delimiter (the seed carries only a close), **case variants** (`</JOBVITE_CANDIDATE_DATA>`,
   `<Jobvite_Candidate_Data>`), a repeated pair, the delimiter as the entire value, and a
   newline-framed close. Plus the committed seed end to end through a real `Client`. M1 (strip only
   the close) and M2 (case-sensitive stripper) both pass the seed and are killed by the new rows -
   which is the measurement that the seed is not sufficient.
3. **#6 is asserted AGAINST THE MODELS.** Four cases: no model field or Jobvite key is an EEO name;
   `extra="forbid"` REFUSES setting one (undeclared and unsettable are different properties); the
   fixture's EEO fields do not survive `to_candidate`; no generated fencing path names one.
   Amputation **A9** admits all three EEO fields to the application model and kills four cases.
4. **#24 the `eId`/`EId` asymmetry is PINNED** as two named constants, `ID_KEY_READ` and
   `ID_KEY_WRITE`, with the read spelling winning when a body carries both. Mutation M13 performs
   exactly the tidy-up DESIGN.md:1353 warns about and is killed; amputation A8 does it structurally.
5. **#20 asserts the DROP.** `assert key not in candidate`, never `isinstance(value, str)`, and
   `assert "42" not in json.dumps(candidate)` so a stringifier cannot pass. M5 and M6 are the two
   stringifying implementations and both die.

### Two things that are worth naming because they are decisions

**`search_candidates` takes NO arguments.** `JOBVITE-CONTRACT.md:225-236` documents nine request
parameters and every one is `[INFERRED]` or `[ASSUMED]`; `start`/`count` are U6's. `datestart`/
`dateend` are the parameters `SearchJobsInput` refused, and the analogy that made them `[ASSUMED]`
there runs FROM this route. Jobvite silently ignores a parameter it does not recognise, so a
guessed filter returns an unfiltered page while the caller believes it was filtered. Checklist rows
6 and 13.4 settle the names.

**Every candidate-typed field is fenced, not only the résumé.** DESIGN.md:740-742 defines the class
as "any free-text field a candidate typed", so names, email, phones, self-reported location and the
candidate's own `title` are all fenced. The result is noisier and it is what the design says. The
positive control reads through an `unfenced()` helper that ASSERTS the fence before comparing the
value, so a bare `== "Testcandidate"` cannot silently become a claim that the field is not fenced.

---

## 3. Gate exit codes, read from the terminal

| Gate | Command | Exit |
|---|---|---|
| lint | `uv run --frozen ruff check .` | **0** (`All checks passed!`) |
| format | `uv run --frozen ruff format --check .` | **0** (`62 files already formatted`) |
| types | `uv run --frozen mypy` | **0** (`Success: no issues found in 50 source files`) |
| suite | `uv run --frozen pytest` | **0** - `560 passed, 6 deselected` — **0 skipped** |
| suite floor | `check-suite-floor.sh 560` | **0** (`suite floor OK: 560 passed, floor 560`) |
| anchors | `check-harness-anchors.py --self-check --floor 278` | **0** (`all 278 anchors resolve`) |
| anchor controls | `check-harness-anchors-controls.sh` | **0** |
| quickstart | `check-quickstart.py` | **0** |
| file types | `check-committed-file-types.py --all` | **0** |
| citation shape | `check-design-citation-shape.py` | **0** |
| coupling | `check-coupling.py docs/DESIGN.md` | **0** |
| cross-refs | `check-cross-references.py` | **0** |
| obligations | `check-obligations.py` | **0** - verbatim below |
| obligations controls | `check-obligations.py --controls` | **0** |
| plan measurements | `check-plan-measurements.py` | **0** |
| U8 controls, gated | `ci-harness-gate.sh check-u8-candidates-controls.sh --controls-fired --min-rows 25 --row-re '^########## M[0-9]+ '` | **0** |
| U8 amputation, gated | `ci-harness-gate.sh check-u8-candidates-amputation.sh --amputation --anchors-applied --min-rows 14 --row-re '^########## A[0-9]+ '` | **0** |

`check-obligations.py`, verbatim:

```
Mappings: 31  |  anchors verified against their subject: 24  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
```

Nothing in this change moved an obligation anchor, so nothing was repointed.

### THE TWO FLOORS, DERIVED FROM `ci.yml`, NEVER RETYPED

`ci.yml` at `187c210` says **500** and **239**. Measured on this branch:

```bash
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 500
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 239
```

**The new numbers are 560 and 278.** `ci.yml` is yours; I did not touch it.

### Coverage

`utils/redaction.py` **100%**, `utils/normalise.py` **100%**, `models/candidate.py` **100%**,
`tools/candidates.py` **87%** (target 85%). Overall **95%**. DESIGN.md:1362-1368's 95% floor on
`utils/` is met on both files this unit touched.

---

## 4. Every harness row, and whether it fired

### `check-u8-candidates-controls.sh` - **25/25 controls fired**, all KILLED

| Row | Mutation | Killed by |
|---|---|---|
| M1 | only the closing delimiter is stripped | `test_case19_red_team_content_cannot_close_its_own_fence` |
| M2 | the delimiter stripper is case-sensitive | same |
| M3 | the content is wrapped before it is stripped | `test_case19_the_seed_fixtures_payload...` |
| M4 | an admitted free-text field is passed through unfenced | **the positive control** |
| M5 | an unregistered field is stringified instead of dropped | `test_case20_an_unknown_non_string_field_is_dropped` |
| M6 | a fenced field arriving as a non-string is stringified | `test_case20_a_decided_field_arriving_as_a_non_string_is_dropped` |
| M7 | the registry is consulted by leaf name, not by path | `test_fencing_is_applied_by_path_and_a_colliding_name_is_unaffected` |
| M8 | a wildcard shadows an exact path | `test_an_exact_path_is_not_shadowed_by_a_wildcard` |
| M9 | the blank test uses truthiness and eats a zero | `test_the_unification_does_not_touch_a_non_string` |
| M10 | whitespace no longer counts as blank | `test_empty_strings_and_nulls_are_unified_both_directions` |
| M11 | epoch milliseconds are read as seconds | `test_epoch_milliseconds_become_the_request_sides_date_spelling` |
| M12 | a malformed date is guessed rather than refused | `test_a_malformed_date_is_refused_rather_than_guessed` |
| M13 | the write spelling is tidied into the read one | `test_case24_reads_use_lowercase_eid_and_the_write_uses_capital_eid` |
| M14 | the reader accepts only the read spelling | `test_case24_the_reader_accepts_both_spellings...` |
| M15 | an EEO field is admitted to the application model | `test_case6_no_output_model_declares_an_eeo_field` |
| M16 | the application model allows extra fields | `test_case6_an_eeo_field_cannot_be_set_on_an_output_model` |
| M17 | the candidate's own title is decided not-free-text | `test_the_same_name_at_two_depths_gets_two_different_decisions` |
| M18 | the nested job title is fenced like the candidate's | same |
| M19 | total is counted from the items, not the envelope | `test_the_cap_reads_total_from_the_envelope_not_from_the_items` |
| M20 | the configured cap is ignored | `test_the_result_cap_is_applied_to_the_page` |
| M21 | the candidateId query key is misspelled | `test_the_candidate_id_reaches_the_wire_as_a_query_parameter` |
| M22 | CANDIDATES_PATH points at a route that does not exist | same - **see below** |
| M23 | registration ignores settings.enabled_tools | `test_a_candidate_tool_not_named_is_not_registered` |
| M24 | the _meta key is not the namespaced one | `test_the_meta_key_is_the_one_the_jobs_tool_already_ships` |
| M25 | the page output schema is built in validation mode | `test_both_tools_advertise_serialisation_output_schemas` |

**THE FIRST RUN WAS 21/25, and three of the four gaps were instrument faults while one was a real
defect in my own test.** Recorded rather than quietly fixed:

- **M22 SURVIVED, and it was a REAL FINDING.** The test asserted
  `seen[0].url.path.endswith(CANDIDATES_PATH)` - the constant against itself. Mutating
  `CANDIDATES_PATH` to `/not-a-route` moved the assertion along with the code, so the route could
  be broken with the case green. Fixed by asserting the LITERAL `/candidate` (the route is
  `[RECORDED]`) and separately asserting the constant equals it, which are two different claims.
- **M7 SURVIVED as an instrument fault.** The mutation ADDED a leaf-name fallback after the exact
  match, so it was a no-op for a path that is exactly registered. Rewritten to REPLACE the exact
  lookup, which is what a name-keyed implementation actually looks like. It then killed.
- **M18 SURVIVED as an instrument fault.** The mutation added `_unused_marker: str = ""`, and
  pydantic IGNORES an underscore-prefixed attribute, so nothing changed. Rewritten to flip the
  nested job title's decision to `FENCE`, which is the collision arriving from the safe-looking
  side.
- **M25 COULD NOT APPLY.** `ruff format` collapsed the multi-line call after the row was written -
  the anchor was correct when typed and stale by the time it ran. Re-anchored on the formatted
  text. This is the argument for running `ruff format` BEFORE the final harness run, which the
  brief asks for and which I did.

### `check-u8-candidates-amputation.sh` - **14 rows, 14 anchors applied, 0 VACUOUS**

Every row killed something, so none is a hollow measurement. Survivor counts, out of 56 (60 after
the last four cases were added):

| Row | Amputation | Went red |
|---|---|---|
| A1 | the tool returns an empty page whatever Jobvite sent | 4 |
| A2 | `fence_text` is the identity function | 16 |
| A3 | content is wrapped but delimiters are no longer stripped | 10 |
| A4 | the walk admits every field regardless of its path | 3 |
| A5 | `to_candidate` reads the raw record, never the fenced one | 4 |
| A6 | the blank/null unification does not exist | 2 |
| A7 | epoch milliseconds are never converted to a date | 3 |
| A8 | the eId/EId asymmetry is tidied away | 2 |
| A9 | every EEO field is admitted to the application model | 4 |
| A10 | both title fields take one decision, as name-keying would | 4 |
| A11 | the result cap does not exist; total recomputed to agree | 2 |
| A12 | the `get_candidate` success result carries no `_meta` | 1 |
| A13 | registration ignores the enabled-tools gate entirely | 1 |
| A14 | `to_candidate` silently stops mapping one admitted field | 1 |

**A1's first run reported `ANCHOR NOT UNIQUE (2 hits)`** - the bare
`items = payload.get(CANDIDATES_ENVELOPE_KEY) or []` appears in both `build_result` and
`_one_record`. That is the uniqueness check doing its job on the single most important row in the
file, and it is why the anchor is now the two-line form. A row that silently applied to the wrong
function would have measured nothing while printing a clean result.

**A3 is the row worth reading.** It deletes only the delimiter STRIPPER and keeps the wrapper, so
every value is still fenced and any test asserting "the value is wrapped" passes. Ten cases die -
all eight red-team rows plus the seed and the end-to-end path - which is the measurement that the
red-team set is testing the second clause of DESIGN.md:744-745 and not just the first.

### CI WIRING - **`ci.yml` IS YOURS, so here are the two steps to add, verbatim**

```yaml
      - name: U8 candidate controls
        run: "bash scripts/ci-harness-gate.sh check-u8-candidates-controls.sh --controls-fired --min-rows 25 --row-re '^########## M[0-9]+ '"
      - name: U8 candidate amputation
        run: "bash scripts/ci-harness-gate.sh check-u8-candidates-amputation.sh --amputation --anchors-applied --min-rows 14 --row-re '^########## A[0-9]+ '"
```

Both were run through `ci-harness-gate.sh` locally at those exact flags and both exited **0**. The
gate derived its vocabulary from each harness's own source, so neither is an inoperative gate.

---

## 5. What I was asked to report and did NOT implement

### `DEFAULT_ID_KEY` is `eId` - and MY FIXTURES CANNOT CONFIRM IT. Three units are still waiting.

The brief asked me to say so explicitly if my fixtures settled this. **They do not, and the reason
matters more than the answer.**

`docs/research/fixtures/candidate_list_success.json` uses `eId`, and so does
`JOBVITE-CONTRACT.md:244`. But that fixture is **synthetic** - `IMPLEMENTATION-PLAN.md` §1 lists it
in the synthetic tier explicitly, and DESIGN.md:1258-1260 says a suite passing only against
synthetic fixtures proves the client is self-consistent, not that it speaks Jobvite. **Our fixture
says `eId` because someone wrote `eId` in it.** That is not evidence.

The one genuine observation is the VCR cassette at `JOBVITE-API.md:393-402`, and what it settles is
recorded there: the envelope keys, that a success body carries `status`, that `total` is the
result-set size, and that `start=0` returns records. **The candidate field map derived from it is
marked `[INFERRED]` at `JOBVITE-CONTRACT.md:229-236`, not `[RECORDED]`**, and the cassette's body
is not in this repository, so I could not read it. `test_case24_the_client_default_id_key_is_the_read_spelling`
pins `DEFAULT_ID_KEY == ID_KEY_READ` so the two cannot drift, which is all that is testable
credential-free.

**So: `eId` is neither confirmed nor refuted by this unit. It remains checklist row 2's job.** I am
recording that as a negative result rather than letting a synthetic fixture read as a confirmation,
because a fixture that agrees with the constant it was written from is the circular measurement
this project has already been burned by.

### ADR-0024 - I did NOT give `scan()` a caller, and that is a decision

**`tools/candidates.py` calls `client.request`, not `client.scan`.** `grep -n "\.scan(" src/` still
returns nothing outside the client itself. Reasoning, since the brief expected the opposite:

- ADR-0025 says outright: *"That is the argument for settling it before U8 and U12 give it a
  caller"* - and *"Implementing it before this is settled turns a latent contradiction into a live
  one"*. Both ADRs are **Proposed** and I was told to implement neither.
- **No design clause requires this tool to page.** DESIGN.md:469-477 specifies exactly what
  `search_candidates` does: cap one page and report `showing N of total`. That is what it does, and
  it is what `tools/jobs.py` does on the same mechanism.

**The exposure IF a caller is added, stated so it does not have to be re-derived.** I read
`_scan_pages` (`services/jobvite_client.py:1876-1930`) rather than reasoning from the ADR:

- With `limit=None` (exhaustive) the ADR-0024 defect is exactly as recorded: no bound at all.
- **With `limit` set, it is still unbounded, and the ADR does not say this.** The loop breaks on
  `len(page) < count` or `len(items) >= effective_limit`. A server that answers a full page of
  records the seen-set has ALREADY seen advances neither: `page` is full so it is not short, and
  `items` does not grow so the cap is never reached. `start += count` and it loops forever. **A
  bounded scan is bounded against a healthy server and unbounded against a non-advancing one**,
  which is a narrower version of ADR-0024's finding and one its "zero-progress break" remedy would
  also close.
- R5-H3's wrong-key exposure interacts with this in the OPPOSITE direction: with a wrong `id_key`,
  every record is `unidentified`, all are kept, `items` grows by `count` per page, so the loop
  terminates FAST and hands the caller duplicates with `duplicates_dropped=0`. **The two failure
  modes cancel each other's symptom**, which is why a key error would present as duplicate records
  rather than as a hang.

### ADR-0025 - the same, and one measurement

`grep -rn "outbound_rate_limit" src/` still returns two hits: the declaration in `config.py:228`
and a comment in `jobvite_client.py:579` saying what it is not. **The self-throttle still does not
exist.** Since this unit makes exactly ONE request per invocation, none of the three contradicting
figures binds it today - which is the same reason ADR-0025 gives for the contradiction being
invisible so far, and is not evidence that it is resolved.

### DESIGN.md:747's WILDCARD clause has a tested mechanism and NO production path-holder

The allow-list is "path-keyed **with wildcards**", and `customField[]` is the open-ended key the
design names. **`customField` is not admitted by this unit.** Its element shape is undocumented -
`JOBVITE-CONTRACT.md`'s response map does not list it and our own fixture has it empty - and
inventing one is the defect `SearchJobsInput` declined for the date parameters.

So the wildcard matcher is implemented (`_path_matches`, `PATH_WILDCARD`), is exercised by two
cases including a negative control that an exact path is not shadowed, and **is not reached by any
production registry entry today**. That is a deliberate gap, stated rather than papered over with a
decision about a shape nobody has seen. **Suggested fix:** checklist row 4's live call is what
would settle `customField`'s element shape; whoever admits it should add
`candidates[].application.customField[].*` and nothing else changes.

---

## 6. One file outside my ownership changed, and why

`tests/test_server.py::test_a_server_with_no_enabled_tool_registers_nothing` named
**`get_candidate`** as a tool that is declared in `KNOWN_TOOLS` and has no implementation. U8
implements it, so the case started asserting the opposite of its own name and went red.

**Repointed to `create_candidate`** (U10's, still unimplemented), with the history written into the
docstring rather than appended beside it, and with the case's expiry stated: it is pinned to "a
declared tool with no implementation", and **when U10 lands there is none left and the case should
be DELETED rather than repointed a third time**. Flagging rather than silently repointing again is
the point.

---

## 7. What I did NOT verify

These are things I could not settle, not things I did not try.

- **Whether Jobvite's candidate response actually uses `eId`.** §5 above. No credential exists; the
  cassette's body is not in this repository. Checklist row 2.
- **Whether `candidateId` is the right query parameter for one candidate.** `[INFERRED]`
  (`JOBVITE-CONTRACT.md:229`). If it is wrong, Jobvite ignores it and returns the first PAGE, and
  `_one_record` hands the caller the first record of that page - **a stranger's record, with no
  error**. This is the one place in the unit where a wrong inference produces a confidently wrong
  answer rather than a visible failure, and no offline test can distinguish the two. Checklist row
  4.
- **The record-level "not found" shape.** `JOBVITE-CONTRACT.md:161` records it as unknown. An empty
  `candidates` array currently yields an empty `Candidate` rather than a problem object, because
  guessing an error shape for a response nobody has observed is how a wrong answer acquires an
  explanation. Checklist row §13.4. **Suggested fix once observed:** a `/problems/not-found` at
  404, decided in `errors.py` rather than here.
- **Whether the fence delimiters are the right ones.** `<jobvite_candidate_data>` matches the
  committed seed fixture and nothing else specifies them. A model's actual susceptibility to this
  framing is not something a unit test measures.
- **ShellCheck on the two new harnesses.** `shellcheck` is not installed in this environment -
  `/bin/bash: line 5: shellcheck: command not found`, exit 127. Both harnesses are copied from
  `check-u5-jobs-*.sh`, which passes the gate, and both keep the `SC2155` split-declaration form
  those files document. **CI runs it and will tell you; I could not.**
- **Behaviour on the HTTP transport.** Every case here drives stdio. U9 owns that surface.
- **Whether fencing every candidate-typed field is the right usability trade.** It is what
  DESIGN.md:740-742 says, and it makes `first_name` a 60-character string. If that is wrong it is a
  design question, not an implementation one, and it is an ADR rather than a quiet narrowing of the
  fenced set.
