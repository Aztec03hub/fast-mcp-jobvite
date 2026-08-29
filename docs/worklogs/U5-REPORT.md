# U5 - `search_jobs` end to end, plus the fencing-decision registry

**Agent:** `u5-search-jobs` **Branch:** `feat/u5-search-jobs`
**Base:** `f83bf7a`, rebased onto `origin/main` at `4ce55d3`
**Frozen design SHA:** `c15b138`, read only as `git show c15b138:docs/DESIGN.md`

---

## What I actually read

Named rather than implied, because a brief that says "say which of these you read" is asking for
a list that can be checked.

- **`docs/DESIGN.md` at `c15b138`**, via `git show`, never from the working tree. In full: §2
  and §2.1 (tool surface, schemas, the four structural limits), §2.2, §3 (module layout), §4.1,
  §4.5 (pagination and the result cap), §5.1, §5.2, §5.3 (the whole of the audit and `request_id`
  section), §6.1, §6.2, §7.1, §7.3, §8 (every required case), §9, §10.
- **`docs/plans/IMPLEMENTATION-PLAN.md`** - `### U5` in full, `### U6` (because the cap is split
  across the two units), §4's shared-file table in full, and §4's `conftest.py` and dependency
  rows.
- **`src/fast_mcp_jobvite/`** in full before writing a line: `config.py`, `server.py`, `audit.py`,
  `errors.py`, `utils/redaction.py`, `utils/correlation.py`, `services/jobvite_client.py`.
- **`docs/adr/0012-shared-inbound-constraints-module.md`** in full, and the ADR status table at
  `IMPLEMENTATION-PLAN.md:1945`. See finding **F3** - they disagree.
- **`tests/credentialed/README.md`**, `CONTRIBUTING.md`'s gate list, `pyproject.toml`'s pytest and
  ruff configuration, `.github/workflows/ci.yml`'s credentialed and harness steps.
- **`docs/research/JOBVITE-CONTRACT.md` §7** and **`JOBVITE-API.md` §8.1** - the request
  parameters and response field map for `GET /api/v2/job`.
- `scripts/check-u4-client-amputation.sh` and `check-u3-audit-controls.sh`, as the harness
  pattern.

**Not read:** the TIER-1 standards at `/home/plafayette/claude_projects/evolv/MUST-READ-DOCS.md`.
That path is outside both my worktree and the shared checkout. I did not open them, so nothing
below cites them directly; every clause I rely on is cited through `DESIGN.md`'s own quotation of
it. **This is a gap in my evidence, not a claim that they do not bind** - see "What I did not
verify".

---

## Baseline, and a disagreement worth recording

`uv run --frozen pytest` on the untouched tree at `f83bf7a`:

```
====================== 360 passed, 2 deselected in 24.05s ======================
```

**This matches the dispatch message and contradicts `docs/briefs/PREAMBLE.md`**, which says
*"Suite baseline: 322 passed, 2 deselected, 0 skipped (measured at `0d34c66`)"*. The PREAMBLE
exists because "a retyped constant decays", and this is that file's own constant having decayed.
The dispatch is right; the PREAMBLE's line is stale. **Suggested fix:** PREAMBLE stops naming a
number and points at `ci.yml`'s `check-suite-floor.sh` argument, which is the one place the floor
has to be correct anyway.

**Final, after rebase onto `4ce55d3`:** `397 passed, 5 deselected, 0 skipped`. The 5 deselected
are 2 `network` and **3 `credentialed`** - the three arms this unit adds.

---

## The work, and where each piece landed

| File | What |
|---|---|
| `src/fast_mcp_jobvite/models/jobs.py` | The allow-listed output model. Every field carries a `Fenced` decision |
| `src/fast_mcp_jobvite/models/fencing.py` | The mechanism that GENERATES fencing paths from output models |
| `src/fast_mcp_jobvite/models/__init__.py` | Package; states the one-file-per-tool rule |
| `src/fast_mcp_jobvite/tools/jobs.py` | `search_jobs` only. `get_job_feed` is U12's half of this file |
| `src/fast_mcp_jobvite/tools/__init__.py` | Package |
| `src/fast_mcp_jobvite/utils/constraints.py` | ADR-0012's module. The character rule only - see **F3** |
| `src/fast_mcp_jobvite/server.py` | Registration wired to `settings.enabled_tools` |
| `tests/test_tools_jobs.py` | 35 cases, all on the wire |
| `tests/credentialed/test_search_jobs_live.py` | The first credentialed arm |
| `scripts/check-u5-jobs-controls.sh` | Mutation, 12 rows |
| `scripts/check-u5-jobs-amputation.sh` | Amputation, 11 rows |
| `.github/workflows/ci.yml` | The credentialed tightening, plus both harness steps |
| `CONTRIBUTING.md` | Both harnesses in the gate list |
| `changelog.d/02-search-jobs-end-to-end.md` | Fragment |
| `tests/test_server.py` | **One case rewritten** - see "Files outside my list" |

---

## Every verification item, and its result

### Required by the brief

| # | Item | Result |
|---|---|---|
| 1 | In-process `Client` calls `search_jobs` against `MockTransport`, gets a typed result | **PASS** - `test_search_jobs_returns_a_typed_result_over_the_wire` |
| 2 | Same call against `error_auth_200_body401.json` returns `/problems/external-service-error` **502**, `is_error=True` | **PASS** - `test_the_recorded_200_with_401_body_is_a_502_problem` |
| 3 | §8 #16 read arm: `request_id` on the WIRE under the namespaced key, matched to the audit event's id, **and** structured content still validates | **PASS** - `test_case16_read_arm_request_id_on_the_wire_meta` |
| 4 | §8 #16 error arm: the problem object's **own `request_id` member** matches the audit id, on the wire | **PASS** - `test_case16_error_arm_request_id_in_the_problem_object` |
| 5 | The cap fires and reports `showing N of total` rather than truncating | **PASS** - `test_the_result_cap_reports_showing_n_of_total`, `showing 1 of 2` |
| 6 | Every field on the job model has a fencing decision; deleting one fails the suite | **PASS** - `test_every_job_model_field_has_a_fencing_decision` + `test_deleting_a_fencing_decision_fails` |
| 7 | The server starts on stdio and on HTTP and lists exactly the enabled tools | **PARTIAL** - see below |

**On item 7, stated precisely rather than ticked.** The tool surface is asserted to be exactly
`{search_jobs}` on **both** transport configurations
(`test_the_server_lists_exactly_the_enabled_tools`, `test_the_server_lists_the_same_tools_on_http`),
and a paired case proves the gate can still refuse (`test_a_tool_not_named_is_not_registered`).
**What I did NOT do is bind a socket.** Both cases build the server and drive an in-process client;
the HTTP one sets `mcp_transport=http` with a loopback host and a token map so it passes
`config.py`'s refusals, but nothing listens on a port. The property under test - registration - is
settled before any socket exists, and binding one would make this a `network` test. **A reviewer
who reads "starts on HTTP" as "bound and served over HTTP" would be over-reading my evidence.**

### Additional cases I judged the design required

- The audit event is emitted and carries its mandated fields - **positive control** for items 3
  and 4, so neither can be satisfied by silence.
- The failing arm records `result_status: "error"` - paired with the above, since a status that is
  always `"success"` passes the positive case alone.
- An uncapped page is **not** reported as capped - the cap does not fire on every call, which
  `DESIGN.md:469-473` says would train everyone to ignore it.
- `total` is read from the envelope, driven with a `total` that disagrees with the page
  (`showing 1 of 1,240`), since "reported and never trusted" only has teeth when the two differ.
- Containment: an unadmitted Jobvite field is **dropped**, and - the paired direction that
  matters - **does not fail the call**.
- The generated fencing paths are in **Jobvite's** key space (`requisitions[].applyLink`), and our
  snake_case attribute names do **not** appear.
- Inbound rejection: six parametrised arms (NUL, bell, C1, bidi override, bidi isolate, trailing
  newline), each with the positive control that an ordinary identifier still passes, plus a case
  proving a rejected argument never reaches the transport and never audits.
- The tool advertises a **serialisation** output schema.
- **A gate for the rule that had none:** `test_no_module_scope_credential_read_in_the_tool_module`
  walks the AST of `tools/jobs.py` for a module-scope `os.environ`/`getenv`. It walks the AST
  rather than grepping precisely because a grep would match its own docstring - the vacuous shape
  amputation found in U3.

---

## The three composition risks

**All three are now closed, and one of them changed my code.**

### 1. `config.py`'s `SecretStr` reaching `jobvite_client.py`'s `SecretValue` Protocol - **CLOSED**

`test_config_secretstr_satisfies_the_clients_protocol` builds real `Settings` with real
`SecretStr` values, passes them into `JobviteClient`, drives a call, and reads the credentials
back off the request the transport saw:

```
seen[0].headers["x-jvi-api"] == "live-api-key"
seen[0].headers["x-jvi-sc"] == "live-api-secret"
```

The Protocol is satisfied structurally with no adapter, and `mypy` accepts it - `Success: no
issues found in 43 source files`. U4's declaration was correct.

**It did change my code.** `Settings.api_key` is `SecretStr | None`, and the `SecretValue`
Protocol is not optional, so mypy refused the composition until I resolved the credentials at
**registration** and refused loudly if absent. That refusal is a boot-time `ValueError`, not a
runtime problem object, because `validate_settings` has already refused such a configuration -
reaching it is a programming error, which is the same class R3-L1 moved out of `missing_for`'s
`.get` fallback.

### 2. U3's transport spellings vs U1's transport selection - **CLOSED, they agree**

The brief said *"One grep settles whether the audit event's `transport` field agrees with the rest
of the server. Nothing currently fails if it does not."* I made it fail:
`test_composition_risk2_the_transport_spellings_agree` compares
`{t.value for t in audit.Transport}` against `get_args(Settings.model_fields["mcp_transport"].annotation)`
**for equality**, not membership - a subset relation is satisfied by a spelling either side has
and the other does not. They are equal: `{"stdio", "http"}`.

`tools/jobs.py` therefore writes `Transport(settings.mcp_transport)` rather than an `if/else`, so
a future divergence raises at registration instead of silently recording the wrong transport.

### 3. U3's `ctx.request_context.meta` against a LIVE context - **CLOSED, U3's call site is correct**

U3 tested its parse call site against the wire contract because no server existed to get a context
from. There is one now. Measured with a committed probe first and then pinned as a test:

```
ctx.request_context.meta type: <class 'dict'>
.get('traceparent') -> 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

It is a plain `dict` of the wire `_meta`, carrying the caller's `traceparent` verbatim beside the
reserved `io.modelcontextprotocol/*` keys. `parse_trace_context(meta)` reads it correctly.
`test_composition_risk3_the_live_context_meta_is_the_wire_meta` asserts the audit event carries
the right `trace_id` and `span_id`, and its paired arm asserts both are **absent** when the caller
sends none.

---

## Mutation harness: 12/12, and two rows that did not fire first time

`scripts/check-u5-jobs-controls.sh`. Final run:

```
########## 12/12 controls fired.
```

**Two rows survived the first run. They are recorded rather than quietly swapped, because they
failed for opposite reasons and only one was a finding about the code.**

### M3 - a REAL DEFECT IN MY TEST

Mutating `REQUEST_ID_META_KEY` from the namespaced key to `"requestId"` left
`test_case16_read_arm_request_id_on_the_wire_meta` **passing**. The test read
`result.meta[REQUEST_ID_META_KEY]` - the same constant the mutation changed - so the assertion
moved with the mutation. The test passed against a server publishing the id under a key no caller
could guess, which is exactly what `DESIGN.md:646-650` forbids: *"the README must document the
key, because a caller cannot guess it, and an id a caller cannot reach discharges nothing."*

**An assertion that reads the constant under test cannot see it change.** Fixed: the test now
spells the key out as a literal and separately asserts the constant equals it.

### M9 - an INSTRUMENT FAULT, not a finding

`return Job.model_construct(**raw)` survived. Diagnosed before "fixing" the test, and the test was
right:

```
model_construct dump: {"title": "One", ...}
leaks SECRET? False
```

`model_construct` sets extras on the instance, but `model_dump` iterates the **declared** fields,
so the mutation created no leak to detect. Same shape as the U4 harness's A12 note. Replaced by
two rows that are real in both directions - **M9a** leaks through an admitted field
(`title=str(raw)`), **M9b** fails the call instead of dropping the field (`Job(**raw)`). Both fire.

The other ten rows fired first time: the envelope `total`, the cap slice, a fresh-uuid problem
object, validation-mode output schema, the enable gate, a defaulting fencing decision, snake_case
generated paths, a permissive identifier pattern, and a non-derived summary string.

---

## Amputation harness: 11 rows, 11 anchors applied, and the survivor that matters

`scripts/check-u5-jobs-amputation.sh`. **Survivors are the output, not the verdict.**

```
########## ROWS: 11   ANCHORS APPLIED: 11
########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: 345
```

Baseline 34 passed (35 after a later case was added; the harness re-runs its own baseline).
Per-row kill counts:

| Row | Behaviour deleted | Result |
|---|---|---|
| A1 | The result cap entirely; `total` recomputed to agree | 2 failed, 32 passed |
| A2 | `_meta` never set on the success result | 1 failed, 33 passed |
| A3 | The error path raises instead of returning a problem | 2 failed, 32 passed |
| A4 | No audit event is ever emitted | 4 failed, 30 passed |
| A5 | `fencing_paths` returns nothing for every model | 5 failed, 29 passed |
| A6 | A field with no fencing decision is silently skipped | 1 failed, 33 passed |
| A7 | Registration ignores the enable gate | 1 failed, 33 passed |
| A8 | An admitted field forwards the raw Jobvite object | 2 failed, 32 passed |
| A9 | Inbound identifiers accept any character | 7 failed, 27 passed |
| A10 | The caller-facing summary string is removed | 3 failed, 31 passed |
| A11 | The live request `_meta` is never read | 1 failed, 33 passed |

**No row survived 34/34**, which is the vacuous shape. Every row killed at least one case, so no
assertion in this suite is passing against a tree with its subject deleted.

**The informative survivor is A11's.** Deleting the read of the live request `_meta` kills the
trace-context **present** arm and leaves the **absent** arm passing. That is not a defect - it is
precisely what `DESIGN.md:663-665` predicts: *"a field that is always absent and a field that is
always synthesised each pass a single-arm test."* The two arms are why the deletion is visible at
all. A suite with only the absent arm would have reported this amputation as fully green.

**A4's four kills** are the other half worth naming: both `request_id` cases match the wire against
the audit event's own id, and with no event there is nothing to match. That row is what proves the
two id cases are not asserting against silence.

---

## My `ci.yml` edits, and a measurement that caught my own mistake

### The credentialed-collect tightening - the edit the brief names

Was: exit `0` **or** `5` accepted, with `5` printing *"the credentialed suite is still empty
(U0)"*. Now: **exit 0 AND at least 3 collected.**

U0 left it accepting 5 because it could not tell *"the suite is empty"* from *"the suite is
healthy"* - the two rendered identically, which is the failure mode where a switched-off check and
a broken one look the same. This unit adds the arm, so the distinction now exists.

**Floored rather than merely non-empty**, for the same reason the network arm is: a count catches
the HALF-empty case, where one arm stops being collected and the rest still pass. The `3` was
derived by running the command on this branch, not from the "deselected" figure in the default
run, which also counts `network`.

**My first version of the count parse was wrong, and running it is how I know.** I anchored the
pattern with `^`. pytest prints the count inside a banner padded with `=` on both sides:

```
=============== 3/400 tests collected (397 deselected) in 0.63s ================
```

so the anchored pattern matched nothing and the step would have failed **every run**. I then
executed all three step bodies verbatim as shell before committing: `collected=3`,
`fired=12 total=12`, `rows=11 applied=11`.

### The two harness steps - and the tension in my brief, stated rather than resolved silently

**My brief contains a contradiction and I am flagging it rather than picking quietly.** The
dispatch says *"ONE ci.yml edit (tightening the credentialed-collect step)"*, and §4's table says
*"U5 additionally tightens the credentialed-collect step"*. But standing requirement 2 says both
harnesses must be *"wired into `ci.yml` and `CONTRIBUTING.md` in the same commit. Two harnesses
ran nowhere here for days."*

**I wired them**, because not doing so reproduces a measured failure this project has already had,
because every prior unit's harnesses are in `ci.yml`, and because the steps are a non-adjacent
region from the credentialed one and from anything `harness-integrity` touches. If you wanted the
literal one-edit reading, the two steps are a contiguous block and are trivial to drop.

The mutation step gates on every row firing. **The amputation step gates on every row having
APPLIED ITS ANCHOR, not on the exit code**, because survivors are its output.

---

## `docs/OBLIGATIONS.md`

My `ci.yml` edit shifted two anchors. I repointed them **by parsing the checker's own output**,
never by retyping a number - a narrowed anchor still resolves to plausible text, so a
transcription error is invisible at exit 0. Verbatim, before:

```
Mappings: 29  |  anchors verified against their subject: 20  |  recorded as absent: 7

FAIL: B75: .github/workflows/ci.yml:655 no longer contains 'name: Capability drift report' - it is now at .github/workflows/ci.yml:701. Repoint the anchor.
FAIL: B82: .github/workflows/ci.yml:825 no longer contains 'Relative links resolve' - it is now at .github/workflows/ci.yml:871. Repoint the anchor.

2 failure(s).
```

**Then the rebase made the whole repoint unnecessary**, which is the better outcome. `origin/main`
had landed task #6 - obligation anchors no longer carry a line number, so they cannot drift - and
the rebase conflicted on exactly the two rows I had repointed. I resolved by taking main's side
and discarding my line numbers entirely. Verbatim, after:

```
9/9 controls fired.
Mappings: 29  |  anchors verified against their subject: 22  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
post-run re-check of the real OBLIGATIONS.md: exit=0
```

---

## Files I touched outside my brief's list

**One, and it was forced.**

`tests/test_server.py::test_the_server_registers_no_tool_yet` asserted
`await client.list_tools() == []`. Registering `search_jobs` - which my dispatch explicitly
sanctions - makes that false, and leaving the suite red is not an option.

I **rewrote it in place** rather than deleting it or appending a second case. Its assertion was a
true statement about a server with no tool modules rather than a property anyone wanted to keep;
what it was actually protecting is that registration goes through `settings.enabled_tools` and not
around it. It now asserts that, and a **paired** case
(`test_a_server_with_no_enabled_tool_registers_nothing`) keeps the half worth keeping - a
`register` that ignored the gate would pass the first and fail the second.

**I did not touch** `utils/redaction.py`, `README.md`, `docs/DESIGN.md`, any other unit's harness,
or `tests/conftest.py`. On `conftest.py` specifically: §4 sanctions
`tests/fixtures/tools.py` plus one `pytest_plugins` entry, and **I did not need it.** No fixture
of mine is shared with another unit yet, so they live in my own test file and the shared file
stays untouched. When U8 needs the `MockTransport` factory, that is the moment to hoist it.

---

## Findings (tasks #25 and #26). Every one ships with a suggested fix.

### PRE-EXISTING RED ON MAIN - **task #25**, and this is the one to read first

**`bash scripts/check-u3-audit-controls.sh` exits 1 on current `main`, and CI gates on it.**

```
M8  a read surfaces a warning it must not surface: COULD NOT APPLY - the anchor moved. Fix the harness.
########## RESULT: 14 killed, 1 not killed
```

`ci.yml`'s "U3 audit mutation controls, all killed" step contains
`if ... grep -q 'COULD NOT APPLY'; then echo "::error::..."; exit 1; fi`. **So main is red today.**

**Not caused by me, and proven rather than asserted.** `check-u3-audit-controls.sh:162` looks for
`# ... A read is recoverable and` / `# losing the tool is worse...`. `audit.py:363-365` says
`# ... A read is recoverable` / `# and losing the tool is worse...`. The wrap moved - that is
B49b's W505 `max-doc-length = 72` reflow. `git diff --stat f83bf7a..HEAD -- src/fast_mcp_jobvite/audit.py`
on my branch is **empty**. It still fails after rebasing onto `4ce55d3`, which includes
harness-integrity's completed work.

**Suggested fix:** re-wrap the anchor in `scripts/check-u5...`— sorry, in
`scripts/check-u3-audit-controls.sh:162-164` to match `audit.py` as it now reads. One row, no
behaviour change.

**Why I did not apply it:** it is U3's harness, and task #20 was live on exactly this class of
defect while I was working. A second agent editing `scripts/check-u3-*` is the collision §4
exists to prevent.

**The general lesson is worth more than the row.** A mutation harness anchors on **source text**,
so any formatting sweep silently invalidates rows. B49b reflowed 1608 lines and nothing checked
whether any were harness anchors. The `COULD NOT APPLY` gate exists in the U3 and U5 steps but
**not in every unit's step**, so the same breakage elsewhere would be invisible. A sweep across
all six control/amputation scripts is worth one pass.

### F1 (LOW) - `ids` is over-redacted in the audit event - **task #26**

`search_jobs`'s `ids` argument reaches the audit event as `[REDACTED:str]`, because
`NON_SENSITIVE_ARGUMENT_KEYS` is a fail-closed allow-list and `ids` is not on it. **That is the
module working as specified**, not a defect in it. But `ids` is a Jobvite job `eId` - public job
data, the same class as `job_id`, `requisition_id` and `eId`, all of which **are** listed.
Redacting it protects nothing and costs the audit event its debugging value on the only read tool
that exists.

**Suggested fix:** add `"ids"` to `NON_SENSITIVE_ARGUMENT_KEYS` in `utils/redaction.py`, and
update `test_the_audit_event_records_this_invocation`, which currently pins the redacted value
with a comment explaining why. **Not applied:** adding a row to a fail-closed *security*
allow-list is the deliberate act its owner should make, not a passing unit's.

### F2 (LOW) - `README.md` now says something false, and nothing gates it - **task #26**

`README.md:11` and `:109` say the server exposes no tool and `fastmcp inspect` reports `Tools: 0`.
It now reports one - CI's capability-drift step already runs with `JOBVITE_TOOLS: search_jobs`.
**No test asserts the tool count**, so this will rot: `test_readme.py` checks sections, the
variable table, links, the line cap and placeholder prose, and none of those move.

**Suggested fix:** rewrite the two passages in place (not append), documenting `search_jobs`, its
`ids` argument, the `showing N of total` result, and **the `_meta` key**
`com.evolvconsulting.fast-mcp-jobvite/requestId` - which `DESIGN.md:646-650` explicitly requires
the README to document because a caller cannot guess it. Then add a `test_readme.py` case tying
the documented tool set to what is registered, so the next tool cannot land without the README
moving. **Not applied:** `README.md` is U13's and this is not a gate failure.

### F3 (INFORMATIONAL) - the three structural limits have no owner, and the plan misreports ADR-0012

`utils/constraints.py` holds the **character rule** (`DESIGN.md:172-175`). It does **not** hold
nesting depth 5, 1,000 list items or 100 dict keys (`:162-164`), because no input model in the
tree is deeper than one flat object - the code would have no caller and no reachable test, and an
unreachable limit with a test that cannot exercise it **reads as discharged when it is not**.
§8 requires "one arm per limit" and that case is currently owned by nobody.

**The plan is stale here and two places gate on it.** `IMPLEMENTATION-PLAN.md:2178` says *"0012 is
still Proposed, and until Phil accepts it the per-tool specification stands"*, and `:1945`'s table
says **Proposed**. The ADR itself reads **`Status: Accepted`** and *"Accepted and APPLIED"*, and
`DESIGN.md` §3 at `c15b138` lists `utils/constraints.py` in its module block. I built the module
on the ADR and the frozen design, not on the plan's prose.

**Suggested fix:** give the three structural limits to U8 or U12 - the next units to write an
input model, and the first with a **nested** one - name it in §4's table, and repoint
`IMPLEMENTATION-PLAN.md:1945` and `:2170-2185` to say Accepted.

---

## Design defects found by building

The brief said to expect one. I found **no defect in `DESIGN.md` itself** and therefore filed **no
ADR** - the next free number is **0022**, unused. What I found instead were two places where the
design is right and the *stack* behaves in a way the design does not mention, and both fail in
ways that mislead:

1. **An output schema must be built with `mode="serialization"`.** pydantic's default is
   `mode="validation"`, which omits `computed_field`s. `DESIGN.md:639-650` reasons carefully about
   `additionalProperties: false` rejecting an undeclared top-level `request_id` - and the *same*
   mechanism rejects our own success payload if the advertised schema is built in the default
   mode, because `showing` and `summary` are then undeclared. Measured: *"Additional properties
   are not allowed"*. The design's reasoning is correct; the mode is the part nobody would guess.
2. **`model_validate` is the wrong instrument for a serialised payload with computed fields.** It
   fails with *"Extra inputs are not permitted"* under `extra="forbid"`. A model with computed
   fields does not round-trip through its own validator by construction. A reviewer reaching for
   the obvious assertion gets a red that looks like a design failure and is an instrument failure.

Both are recorded in the source and in `tests/test_tools_jobs.py` rather than only here. **Neither
needs an ADR** - the design says nothing false about either. If you want them in `DESIGN.md` §8 as
implementation notes, that is a Proposed ADR and I have not written it.

---

## Gate results, by exit code, after the rebase

```
uv lock --check                                EXIT=0
ruff check .                                   EXIT=0
ruff format --check .                          EXIT=0
mypy                                           EXIT=0    Success: no issues found in 43 source files
pytest                                         397 passed, 5 deselected in 23.87s
check-committed-file-types.py --all            EXIT=0
check_advisories.py                            EXIT=0
check-u0-test-controls.sh                      EXIT=0
check-u15-gate-controls.sh                     EXIT=0
check-u11-advisory-controls.sh                 EXIT=0
check-u1-boot-controls.sh                      EXIT=0
check-u3-audit-controls.sh                     EXIT=1    PRE-EXISTING - task #25
check-u4-client-controls.sh                    EXIT=0
check-u5-jobs-controls.sh                      EXIT=0    12/12 controls fired
check-u5-jobs-amputation.sh                    EXIT=0    ROWS 11, ANCHORS APPLIED 11
check-suite-floor-amputation.sh                EXIT=0
check-coupling.py docs/DESIGN.md               EXIT=0
check-cross-references.py                      EXIT=0
check-coupling-controls.py                     EXIT=0
check-coupling-sweep.py                        EXIT=0
check-obligations.py                           EXIT=0
check-obligations.py --controls                EXIT=0
check-plan-measurements.py                     EXIT=0
check-resweep-verdicts.py                      EXIT=0
```

**Zero skips.** The 5 deselected are 2 `network` + 3 `credentialed`, both by selection.

---

## The merge command

```bash
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
    merge --no-ff feat/u5-search-jobs
```

Four commits, already rebased onto `4ce55d3`:

```
e29c65d ci(u5): tighten the credentialed collect, wire both U5 harnesses
8abeb53 test(u5): mutation and amputation harnesses, 12/12 and 11/11
f4c072e test(u5): search_jobs on the wire, plus the first credentialed arm
33ded1f feat(u5): search_jobs end to end, with the fencing-decision registry
```

**One thing to do at merge time, deliberately left to you:** `ci.yml:294` floors the default suite
at **360**. My branch measures **397**. I did not raise it, because the correct floor depends on
what else lands in the same merge and because it is a second region of a file another agent may be
in. **Suggested:** raise it to the measured post-merge count in the merge commit.

**Worktree removed:** yes - `git worktree remove /tmp/u5-work` after this report was committed.

---

## What I did NOT verify

This section is for what I **could not settle**, not for what I did not try.

1. **The TIER-1 standards themselves.** `/home/plafayette/claude_projects/evolv/MUST-READ-DOCS.md`
   is outside my worktree and outside the shared checkout I was told not to touch. I never opened
   `ai/tool-calling.md`, `ai/prompt-injection.md`, `architecture/error-contract.md` or
   `backend/python.md`. **Every standards clause in my code comments is quoted from `DESIGN.md`'s
   own citation of it, not verified against the source.** If a clause has moved or was
   mis-transcribed into the design, I would have propagated it. Task #21 covers exactly this class
   and says 26 such citations are unverified repo-wide.
2. **Whether `search_jobs` actually speaks Jobvite.** Everything offline passes against
   **synthetic** fixtures except the 200-with-401-body trap, which is recorded. The envelope key
   `requisitions`, the `total` member and every requisition field name are `[INFERRED]` in the
   research. The three credentialed arms exist to settle it and **have never run** - no credential
   exists. I verified they *collect*; I did not verify they *pass*.
3. **Whether `pytest.fail` is the right refusal in the credentialed fixture.** I chose it over
   `skip` because a skip is a green that tested nothing, and these tests are only reached by
   someone who deliberately selected `-m credentialed`. Nobody has run that path with a real key,
   so the ergonomics are unmeasured.
4. **The HTTP transport as a served socket.** See item 7 above - I asserted registration, not
   serving. `DESIGN.md`'s §8 case about an off-loopback bind without TLS refusing to start is U1's
   and I did not re-run it.
5. **Whether `ids` accepts a comma-separated list.** `JOBVITE-CONTRACT.md` §7 says explicitly this
   is **unknown**. My input model admits a single identifier and the docstring says so. Checklist
   row 5 settles it.
6. **The date filter.** I offer none, because the parameter names are `[ASSUMED]`. I did not probe
   whether Jobvite silently ignores an unknown query parameter - if it does, guessing would have
   produced an unfiltered page presented as a filtered one. Checklist row 6.
7. **My own `ci.yml` steps in GitHub Actions.** I executed all three step bodies verbatim as local
   shell and they pass. I have not seen them run on a runner, where `uv` caching and the checkout
   differ. The credentialed count parse is the one I would watch, since I already got it wrong
   once locally.
8. **Nothing about coverage - I nearly parked it here and then measured it instead.** This list is
   for what cannot be settled, and coverage was one command. Run:

   ```
   src/fast_mcp_jobvite/models/fencing.py      55   2  16  1   96%   143-144
   src/fast_mcp_jobvite/models/jobs.py         36   0   0  0  100%
   src/fast_mcp_jobvite/server.py              25   0   2  0  100%
   src/fast_mcp_jobvite/tools/jobs.py          54   3   6  2   92%   231-235, 247
   src/fast_mcp_jobvite/utils/constraints.py   13   0   0  0  100%
   TOTAL                                      714  41 138 12   94%
   Required test coverage of 80.0% reached. Total coverage: 93.54%
   ```

   Against ADR-0010's floors: tool modules 85% -> `tools/jobs.py` **92%**; `utils/` 95% ->
   `constraints.py` **100%** (`redaction.py` and `correlation.py` are both 100%); the client 90%
   -> **95%**; overall 80% -> **93.54%**. **Every floor clears.** The three uncovered lines in
   `tools/jobs.py` are the boot-time credential refusal and the real-client construction branch -
   both unreachable when a `client_factory` is injected, which every offline test does. The live
   arms cover them and have never run, so those three lines are genuinely exercised only by
   item 2 above.
