# U12 - `get_job_feed`, and the High that must not rest on an absence

Branch `feat/u12-jobfeed`, from `686820c`. Worktree `/tmp/u12-jobfeed-work`, removed when this
landed. `docs/DESIGN.md` read only as `git show c15b138:docs/DESIGN.md`.

## What was built

| File | What |
|---|---|
| `src/fast_mcp_jobvite/models/job_feed.py` | NEW. `FeedJob`, `JobFeedResult`, `JOB_FEED_ENVELOPE_KEY` |
| `src/fast_mcp_jobvite/tools/jobs.py` | the `get_job_feed` half: `GetJobFeedInput`, `_to_feed_job`, `build_feed_result`, `_feed_params`, `_register_get_job_feed` |
| `tests/test_tools_job_feed.py` | NEW. 25 cases |
| `scripts/check-u12-jobfeed-controls.sh` | NEW. 17 mutation rows |
| `scripts/check-u12-jobfeed-amputation.sh` | NEW. 10 amputation rows |
| `scripts/check-u5-jobs-{controls,amputation}.sh` | REPAIRED - 8 anchors my code made ambiguous. See "What I broke". |

**No line was needed in `server.py`.** `server.py:137` already calls `jobs.register(...)` once, and
`register()` now dispatches to `_register_search_jobs` and `_register_get_job_feed`, each behind its
own enable gate. **Two gates, not one early return**: the two tools take different credentials, so a
deployment holding only the feed's is a configuration `validate_settings` accepts, and a single
`SEARCH_JOBS not in enabled_tools` return would register nothing for it.
`test_the_feed_registers_when_search_jobs_is_disabled` is that case.

**The credential class was declared and reached no code.** `config.py:203-205` already had
`feed_key`, `feed_secret`, `company_id`, and `TOOL_REQUIREMENTS[GET_JOB_FEED]` already refused a
deployment enabling this tool without all three. This unit is the first code that reads them.

## HOW THE C5-I1 ARM PROVES THE LOG STREAM NON-EMPTY

Three arms over one captured `loguru` stream, all from the same call, none able to pass on silence.

1. `test_case2_the_call_emits_a_log_record_carrying_its_non_secret_attributes` - **the positive
   half**. Asserts exactly one record with `message == "jobvite request"`,
   `extra["method"] == "GET"` and `/jobFeed` in `extra["route"]` - the request's non-secret
   attributes - **and** exactly one `tool_invocation` audit event whose `extra["tool_name"]` is
   `get_job_feed`. Two producers, one call.
2. `test_case2_no_log_record_carries_the_jobfeed_secret` - **the absence half**, which
   re-establishes the pairing INSIDE itself (`assert any("jobvite request" in text ...)`) before
   asserting the feed key, the feed secret and the `companyId` appear in no record's message,
   `extra` or exception.
3. `test_case2_the_url_bearing_producer_emits_it_redacted` - **the arm that measures the enforcement
   point firing**. `httpx2` logs the whole URL through the stdlib logger; on this route that URL is
   the credential. The record is asserted **PRESENT** (so the dangerous producer really ran) and
   asserted to carry `sc=[REDACTED]` with none of the three values in it. An absence cannot tell
   "redacted" from "httpx2 logged nothing".

Plus `test_case2_the_url_never_reaches_a_log_record_whole`: the URL as sent is in no record, and the
route the client logs carries no query string at all - which is stronger than a redacted one, and is
what `DESIGN.md:315-316`'s "never logged whole" asks for.

**The `log_records` fixture calls `configure_logging()` first, and that is load-bearing.** It is
what routes the stdlib records into loguru (`__main__.py:299-350`). **MEASURED**: with the bridge
left to arrive by test ordering, mutation row M17 - `SECRET_QUERY_PARAMS` reduced to `{"sc"}` -
**SURVIVED**, because the only producer that could leak the api key had never written to the stream
the arm was reading. The fix is in the fixture, and M17 now fires.

**A second measured defect in my own first draft**, recorded because it is the same shape: the
absence arm first asserted the literal `sc=` was absent from every record. It passed alone and went
**RED in the full suite**, where another module had already imported `__main__`: httpx2's line
reached the stream carrying `sc=[REDACTED]`, which is the COMPLIANT state. The assertion was on the
token, not on the value. It now asserts `f"sc={FEED_SECRET}"` is absent.

## Gate exit codes, read from the terminal

```
uv run --frozen ruff check .          All checks passed!                 RUFF_RC=0
uv run --frozen ruff format .         64 files left unchanged            (run BEFORE the final harness runs)
uv run --frozen mypy                  Success: no issues found in 52 source files   MYPY_RC=0
uv run --frozen pytest -q             587 passed, 6 deselected in 40.86s  (0 skipped)
python3 scripts/check-harness-anchors.py --self-check --floor 278
                                      OK: all 305 anchors resolve ...    ANCHOR_RC=0
python3 docs/reviews/check-obligations.py
                                      Mappings: 31  |  anchors verified against their subject: 25  |  recorded as absent: 6
                                      Every mapped anchor still contains its subject. OK.   OBLIG_RC=0
python3 docs/reviews/check-design-citation-shape.py                      SHAPE_RC=0
bash scripts/ci-harness-gate.sh check-u12-jobfeed-controls.sh \
  --controls-fired --min-rows 17 --row-re '^########## M[0-9]+ '         GATE_CONTROLS_RC=0
bash scripts/ci-harness-gate.sh check-u12-jobfeed-amputation.sh \
  --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '  GATE_AMP_RC=0
```

## The new floors, DERIVED not retyped

`ci.yml` at `686820c` says `check-suite-floor.sh 562` and
`check-harness-anchors.py --self-check --floor 278`. Both were read with the `grep -oE` commands in
`PREAMBLE.md`, never typed from memory.

| Floor | At 686820c | On this branch | Delta |
|---|---|---|---|
| suite | 562 | **587** | +25 |
| harness anchors | 278 | **305** | +27 |

**These are BRANCH-LOCAL.** `main` has moved since my base - task #61 reports `fix/r6-findings`
merged with floors 567/285, and #63 and #66 have landed since. The numbers above are what THIS
branch measures; whoever raises `ci.yml` (yours) must re-measure on the merge result, not add my
delta to a number from a different tree. `ci.yml` is untouched here.

## Every harness row, and whether it fired

### `check-u12-jobfeed-controls.sh` - **17/17 fired**

| Row | What it breaks | Fired |
|---|---|---|
| M1 | the feed reads the v2 collection key | KILLED |
| M2 | `total` counted from items, not the envelope | KILLED |
| M3 | the configured cap is ignored | KILLED |
| M4 | the summary hardcodes agreement with `showing` | KILLED |
| M5 | the v2 credential pair authenticates the feed | KILLED |
| M6 | the feed key and secret swapped | KILLED |
| M7 | the `companyId` never reaches the client | KILLED |
| M8 | the v1 `jobfeed` branch is not selected | KILLED |
| M9 | the tool calls the v2 job route | KILLED |
| M10 | the filters are validated, audited and never sent | KILLED |
| M11 | the `type` query key is misspelled | KILLED |
| M12 | an unfiltered call sends `availableTo` anyway | KILLED |
| M13 | registration ignores `enabled_tools` | KILLED |
| M14 | the output schema is built in validation mode | KILLED (**survived first - see below**) |
| M15 | an admitted field forwards the whole raw object | KILLED |
| M16 | the redactor recognises no secret query parameter | KILLED |
| M17 | the redactor drops the api key from its set | KILLED (**survived first - see below**) |

**Two rows were written, run against the unfixed tests, and SURVIVED. Both are recorded rather than
quietly fixed**, because the survivor is the finding:

- **M14** survived because `test_the_output_schema_is_built_in_serialisation_mode` called
  `JobFeedResult.model_json_schema(mode="serialization")` **itself** and asserted on the result -
  an assertion that pydantic does what it does, passing whatever `@server.tool` was actually given.
  Fixed by reading the schema back off the registered tool over the wire
  (`client.list_tools()[...].outputSchema`), which is the only place the argument's value is
  observable. The row then died.
- **M17** survived for the fixture reason in the C5-I1 section above. Fixed in the fixture, not in
  the assertion. The row then died.

M16 is the row this harness exists for: with `SECRET_QUERY_PARAMS` emptied, the C5-I1 arm must go
red, and it does. If it ever survives, the High is being reported mitigated by a test that measures
nothing.

### `check-u12-jobfeed-amputation.sh` - **10 rows, 10 anchors applied, 0 vacuous, 228 surviving assertions**

| Row | Behaviour deleted | Red | Survivors |
|---|---|---|---|
| A1 | the in-tool result cap | 2 | 23 |
| A2 | `_meta` on the success result | 1 | 24 |
| A3 | the success-path audit event | 2 | 23 |
| A4 | the separate feed credential class | 1 | 24 |
| A5 | the v1 route selection | 7 | 18 |
| A6 | `redact_url` returns its input (the enforcement point) | 3 | 22 |
| A7 | no argument reaches the query string | 1 | 24 |
| A8 | the optional-field mapping | 1 | 24 |
| A9 | the enable gate | 1 | 24 |
| A10 | the derived `showing N of total` | 3 | 22 |

Survivors are the OUTPUT, not a failure: 228 assertions still passed across the ten rows, which is
expected - most of this module's cases are about other behaviours. What matters is that **no row was
vacuous**: every deleted behaviour took at least one assertion down with it. A6 is the one to watch -
three arms die when the redactor is amputated, and they are the three C5-I1 arms.

`utils/redaction.py` (U3's) and `services/jobvite_client.py` are **measured, never edited**. Every
row restores with `cp` and verifies with `cmp` against a pristine copy taken before row 1. No
`git stash`, no `git checkout <path>`. `git status --short` after both harnesses shows only my own
files.

## What I broke, and repaired: 8 of U5's anchors

`check-harness-anchors.py` went from OK to **`FAIL: 8 of 305 anchors do not resolve uniquely`** as
soon as `get_job_feed` landed. My half of `tools/jobs.py` contains lines that are BYTE-IDENTICAL to
`search_jobs`' - `emit(event, AuditPhase.READ)`, `problem = problem_from_exception(exc,
event.request_id)`, `title=raw.get("title") or ""`, the whole success-return block - so eight U5
rows would have printed `ANCHOR NOT UNIQUE` and measured nothing.

**This is the "anchor on the subject and require uniqueness" rule seen from the other side**: the
anchors were fine until a sibling appeared, and nothing about the U5 harness changed. Each was
widened with a line that is unique to `search_jobs` (`build_result`, `eid=raw.get("eId")`,
`audit_scope(SEARCH_JOBS,`), never shortened. Re-measured after the repair:
`check-u5-jobs-controls.sh` **16/16 fired**, `check-u5-jobs-amputation.sh` **14 rows, 14 applied, 0
vacuous**. My own A2/A3 rows hit the same thing in the opposite direction and are anchored on the
block starting at `build_feed_result`.

## What I consumed and did NOT build

- **U6's 1000-record `/v1/jobFeed` page cap.** Stated once, in the client layer
  (`DESIGN.md:434`), enforced at `jobvite_client.py:JOBFEED_PAGE_CAP`. This unit applies only the
  configured RESULT cap - the other half of `min(transport_cap, configured_result_cap)`.
  `test_the_transport_cap_is_not_reimplemented_here` reads this module's own source and refuses a
  second copy of the number, so the split is asserted rather than remembered.
- **U3's redaction enforcement point.** Relied on, not touched.
- **U6's per-resource start base.** `JOBFEED_PATH` was added to `CLIENT_ROUTES`, which
  `test_the_client_routes_tuple_lists_every_route_this_module_asks_for` checks by parsing every
  `client.request`/`client.scan` call in the file and asserting the two sets are EQUAL. That test
  went red the moment I called a new route without declaring it, which is the container-enumeration
  discipline working.

## Carried, not resolved

- **ADR-0025 (Proposed)** - page size, outbound budget and self-throttle contradict each other and
  nothing reads `outbound_rate_limit`. Not implemented, not worked around. This route's 1000 is the
  arm of that arithmetic that fits, and I consumed it without touching the throttle.
- **ADR-0024 (Proposed)** - `scan()` has no bound, and U8 measured that even a BOUNDED scan is
  unbounded against a server answering full pages of already-seen records. **I gave `scan()` no
  caller.** `get_job_feed` issues ONE `request`, so its worst case is one page and it incurs neither
  exposure. That is a decision, not an omission: a paging feed reader is a later unit with an ADR
  behind it, and building it here would have put an unbounded loop on the one route whose URL is a
  credential.
- **500 and 1000 are UNOBSERVED as server limits**, and `/v1/jobFeed` being `[OFFICIAL]` 1-based
  while the v2 routes are `[INFERRED]` is a provenance label. Neither is upgraded into a measurement
  anywhere in my code or tests. Scans still start at `SCAN_START` regardless - U6's mechanism is
  base-agnostic and I did not change it.
- **`ADR-0026` was not claimed.** `docs/adr/` still ends at 0025 on this branch; I found no defect
  in the frozen design that needed one.

## Findings, each with a suggested fix

**F1 (nit, mine, already fixed).** `test_the_output_schema_is_built_in_serialisation_mode` asserted
on pydantic rather than on the registered tool. *Fix applied*: read `outputSchema` off
`client.list_tools()`. **The sibling was swept and is CLEAN**: `grep -rn "model_json_schema" tests/`
returns exactly one other site, `test_tools_jobs.py:266`, and it is a different shape - it asserts
the schema's `required` set against a payload that came off the WIRE, inside a case U5's M5 row
kills. No fix owed there. `test_tools_candidates.py` has no such call.

**F2 (low, not mine).** `httpx2`'s stdlib request line carries the full jobFeed URL, and it is
redacted **only when `configure_logging()` has run**. In the shipped server it always has
(`__main__.py` calls it at module scope). But an embedder importing `fast_mcp_jobvite.server`
directly - which `build_server` supports and `test_server.py` does - gets no bridge and no
`_redact_message` filter, so httpx2's line reaches whatever handler the host installed, unredacted.
*Suggested fix*: have `build_server` install the redacting filter, or document in the README's
deployment section that embedding requires calling `configure_logging()`. **I did not implement
either**: `server.py` is `u9-http`'s file and the README is U13's. Raising it here rather than
silently.

**F3 (nit).** `GetJobFeedInput` offers only `job_type` and `available_to` of the six documented
filters. `category`, `location`, `region` and `department` are tenant-configured vocabularies with
no recorded values, so a model would be guessing the VALUE rather than the parameter name.
*Suggested fix*: add them when `CREDENTIAL-CHECKLIST.md` gets a live tenant to enumerate against.
Additive, costs no caller anything.

## What I did NOT verify

- **`shellcheck` did not run**: the binary is not on this machine (`shellcheck: command not found`)
  and it is not in the lock. My two new scripts are modelled line-for-line on
  `check-u5-jobs-*.sh`, which passes at `--severity=warning`, and they use the same
  declare-then-assign form for every `local` (SC2155), but **that is an argument, not a
  measurement**. CI's `actionlint`/ShellCheck step is where this gets settled.
- **No credentialed run.** Every case here is offline on `httpx2.MockTransport`. Whether Jobvite's
  live `/v1/jobFeed` returns the field set `jobfeed_success.json` carries is `CREDENTIAL-CHECKLIST.md`
  row territory and is unchanged by this unit. In particular **the `id`/`requisitionid` split and
  `hiringManager`'s presence are `[OFFICIAL]` from a 2014 PDF plus a synthetic fixture**, not
  `[RECORDED]`.
- **The exception-message arm of C5-I1 was not re-measured here.** `DESIGN.md:315-318` covers "never
  in an exception message" as well, and `redact_text` plus `probe-exception-redaction.py` are U3's
  and U7's measurements of it. I asserted the LOG arm on this route and did not build a failing-call
  case, because the retry/breaker path belongs to `tests/test_resilience.py`, which `r6-fixes`
  holds. Someone should confirm a `jobFeed` timeout's `detail` carries no `sc=` on THIS route
  specifically; I could not do it without entering that file.
- **`check-standards-citations.py`** was not run as a gate - it was reported failing with nine known
  findings on another branch when I was dispatched (task #63 has since been marked done, on a branch
  that is not mine). Nothing I wrote adds a standards citation.
