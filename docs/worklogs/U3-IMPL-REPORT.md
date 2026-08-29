# U3 - Audit event and single-point secret redaction

**Agent:** `impl-u3-audit` · **Task:** #27 · **Branch:** `impl/u3-audit` · **Date:** 2026-08-28
**Worktree:** `/tmp/impl-u3-work` at `94330db`, rebased onto `origin/main` at `00bb4f4`

---

## 1. What I read

- **`docs/DESIGN.md`, frozen, read via `git show 135c3ac:docs/DESIGN.md`** and never from the
  worktree. §3 (module layout), §4.1, §5.1-5.3 in full, §6, §8 in full, §11's C6 and C7 blocks,
  §12. `:676-705` and `:1226-1232` read line by line.
- **`docs/plans/IMPLEMENTATION-PLAN.md`**: `### U3` in full, §4's shared-file table and the wave
  tables, Wave B, and **Q6** in full.
- **TIER-1 standards** from `MUST-READ-DOCS.md`: `ai/tool-calling.md` (`:160-180` read in full,
  which is where `:171-173`, `:173-175`, `:176-177` and `:178-179` live), `ai/agent-guardrails.md`
  `:36-44` and `:118-126`, `architecture/error-contract.md` via `errors.py`'s citations,
  `backend/python.md` via `pyproject.toml`'s `[tool.ruff]` block, which quotes it clause by clause.
- **`src/fast_mcp_jobvite/utils/correlation.py` and `errors.py`**, both in full, before writing
  anything.
- **All ADRs on `origin/main`**: 0001-0017, 0019, 0020 (0018 is unused). Statuses checked;
  0012, 0013, 0014, 0017, 0019 are **Proposed** and therefore not in force.
- `CONTRIBUTING.md`'s gate list, `changelog.d/README.md`, `.github/workflows/ci.yml`,
  `tests/conftest.py`, `tests/test_correlation.py`.

**Every `DESIGN.md` and `ai/tool-calling.md` line number in my brief was confirmed by subject.**
All were correct. Two citations *inside the design* were not - see §6.

---

## 2. Verification: each item and its result

### §8 #4 (positive) and #5 (absence), as a pair - **PASS**

`DESIGN.md:1279-1282` requires the pairing. Implemented as the plan specifies: **#5 asserts against
the record #4 proves exists, inside the same test**, not against a stream some other test blessed.

| Test | Asserts |
|---|---|
| `test_case4_the_audit_event_is_emitted_at_all` | exactly one record reached a real loguru sink |
| `test_case4_the_event_carries_every_mandated_field` | `tool_name`, `arguments`, `result_status`, `latency_ms`, `request_id`, `transport`, `client_id` |
| `test_case4_the_field_names_are_wire_shaped_snake_case` | `ai/tool-calling.md:178-179`, by regex over every key |
| `test_case4_the_write_records_approval_state_and_its_mechanism` | `approval_state` + `approval_mechanism` on the write |
| `test_case5_candidate_pii_never_reaches_the_audit_record` | **positive first** (`len(records) == 1`, `tool_name`, `job_id` present), then the absence on that same serialised record |
| `test_case5_the_event_object_itself_never_holds_the_raw_arguments` | redaction happens on the way *in*, so a traceback or `repr` cannot print the candidate |

**The pairing is not decorative, and A1 measured it.** Amputating `emit()` to write nothing killed
all six of these plus every other §8-case test - 18 in total. There is no assertion in this file
that survives a silent audit stream.

### §8 #2 - a secret never reaches a log record, including the whole `jobFeed` URL - **PASS**

Asserted against **a log stream proven non-empty in the same test**, which is Q6's construction and
the plan's rather than the design's (ADR-0013 already carries this as **Proposed**; I did not file
a duplicate).

`test_case2_the_sc_value_is_absent_from_a_record_proven_non_empty` runs one `get_job_feed`
invocation carrying the full URL, then:

1. **positive** - `len(audit_records) == 1`, and that record carries `tool_name`, `transport`,
   `client_id` and a v4 `request_id`. Against a misconfigured logger emitting nothing this line
   fails, so the absence below cannot be satisfied by silence.
2. **absence** - none of `sc`, `api` or `companyId`'s values appears anywhere in that record.

Two further arms: `test_case2_the_whole_url_is_covered_not_just_the_sc_parameter` (the whole URL
string, since `DESIGN.md:312-316` classifies the URL and not one parameter), and
`test_case2_a_stderr_failure_report_carries_no_credential`, which covers the exception-message path
of `DESIGN.md:314-315` - `httpx` puts the request URL into the text of the exceptions it raises,
so the audit-failure report is exactly where an unredacted URL would otherwise escape. That arm is
also paired: it asserts stderr is non-empty before asserting what is not in it.

### §8 #17 - trace context, both arms - **PASS**

- **arm 1**: `traceparent` in `_meta` → `trace_id` and `span_id` recorded, and the test asserts they
  equal **the values from the header**, not merely that a 32-hex string is present. That is what
  makes a synthesised id fail.
- **arm 2**: no `_meta` → both keys **absent from the record**, not present as `None`. The test
  asserts the record's other fields first, so this is the absence of a field and not the absence of
  a record.
- Six malformed `traceparent` values yield `None` rather than a guess (all-zero trace id, all-zero
  span id, wrong version, short trace id, empty, garbage), with
  `test_case17_a_valid_traceparent_parses_the_positive_control` as their positive control - without
  it every one of those six passes against `return None`.

`trace_id`/`span_id` are **never synthesised**. Mutation M4 (synthesise when the caller sent none)
and M3 (emit `None` instead of omitting) are both killed by arm 2.

### The audit-failure policy, three arms - **PASS**

| Branch | `DESIGN.md` | Behaviour | Test |
|---|---|---|---|
| Before the side effect | `:690` | raises `AuditWriteError`; the call fails, no write | `test_arm1_before_the_side_effect_the_call_fails` |
| On a read | `:691-692` | writes stderr, returns `[]`, call continues | `test_arm2_on_a_read_it_logs_to_stderr_and_continues` |
| After a successful write | `:693-705` | writes stderr **and** returns a warning; `attach_audit_warnings` puts a `warnings` array in structured content | `test_arm3_*` (four tests) |

The third branch's **shape** is asserted, not just its existence: `is_error` is never set,
the payload keeps its own keys, and **none of the seven required problem members appears** - the
test enumerates `type`, `title`, `status`, `detail`, `instance`, `timestamp` and asserts each is
absent, because `DESIGN.md:720-727` says the failure mode is returning a problem object.
`test_arm3_the_warning_tells_the_caller_not_to_retry` asserts the warning text says so, since a
retry is what emails a second live human and preventing that is the branch's whole reason.
`test_a_successful_audit_adds_no_warnings_key_at_all` is the paired positive: no failure, no key.

**The warning goes to stderr, not to the audit stream that just failed** (`DESIGN.md:717-718`) -
amputation A10 deleted the stderr write and killed three tests.

### The stdio arm - marker, not `"global"` - **PASS**

`test_stdio_never_records_the_literal_global` passes `client_id="global"` in (simulating an
implementer who wired `get_client_id` on stdio) and asserts three things: `caller_attribution` is
the marker, `client_id` is **absent from the record**, and the string `"global"` does not appear
anywhere in the serialised record. It also asserts `"global"` is not a substring of the marker
itself, so the marker cannot be renamed into the failure it exists to prevent.
`test_http_records_the_client_id_and_no_marker` is the paired positive: attribution *is* recorded
where it is knowable.

---

## 3. Mutation harness - `scripts/check-u3-audit-controls.sh`

**15 mutations, 15 killed, 0 survived.** Each row names the test that must fail, and a run that
goes red at a *different* test is reported as a coincidence rather than a control.

```
M1  stdio records the literal "global"                  killed by test_stdio_never_records_the_literal_global
M2  stdio keeps the client id                           killed by test_stdio_never_records_the_literal_global
M3  trace fields emitted as None not omitted            killed by test_case17_arm2_...
M4  trace id SYNTHESISED when the caller sent none      killed by test_case17_arm2_...
M5  all-zero traceparent accepted as a real join        killed by test_case17_a_malformed_traceparent_...
M6  pre-write audit failure no longer fails the call    killed by test_arm1_...
M7  post-write audit failure returns no warning         killed by test_arm3
M8  a read surfaces a warning it must not               killed by test_arm2_...
M9  inbound request id echoed WITHOUT validation        killed by test_an_invalid_inbound_request_id_...
M10 the var is set directly, losing the finally         killed by test_audit_scope_calls_request_id_scope_...
M11 sc= dropped from the secret parameter set           killed by test_case2
M12 the parameter match becomes case-sensitive          killed by test_uppercase_parameter_names_...
M13 arguments become a DENY-list                        killed by test_an_unlisted_argument_key_is_redacted
M14 allow-list becomes leaf-keyed not path-keyed        killed by test_a_container_under_an_unlisted_key_is_redacted_WHOLE
M15 the exception-message arm stops redacting           killed by test_a_url_embedded_in_an_exception_message_...
```

`PYTHONDONTWRITEBYTECODE=1` is exported. Each mutation is proved to have **landed** before the
suite runs and the file is proved **restored** after, and the harness aborts if the target files
are dirty on entry, because `git checkout --` is how a mutation harness silently discards the fix
it was meant to be testing.

**Two instrument defects found in my own harness, both worth recording because both produced a
believable wrong answer:**

- The landed/restored checks used `grep -F` against the replacement text. **`grep -F` with a
  multi-line pattern treats each line as a separate alternative**, so M4 - whose replacement began
  with an unchanged `if not meta:` - matched the *restored* file and reported `RESTORE FAILED`. The
  tree was fine; the instrument was wrong. Both checks now compare against git.
- M10's anchor was not unique: the `with request_id_scope(...)` line appears twice, because
  `audit.py`'s module docstring **quotes** it. The harness refused to guess, which is the correct
  behaviour and is how I found the vacuous test below.

---

## 4. Amputation harness - `scripts/check-u3-audit-amputation.sh`

**10 amputations. Every one killed at least one test. Survivors are the output.**

| | Amputation | Killed |
|---|---|---|
| A1 | `emit()` writes NOTHING - the audit stream is silent | **18** |
| A2 | `redact_arguments` not called on the way in | 4 |
| A3 | `caller_attribution` always `None` | 2 |
| A4 | the `traceparent` is never read | 1 |
| A5 | the three-branch failure policy deleted | 6 |
| A6 | `attach_audit_warnings` returns the payload untouched | 1 |
| A7 | `request_id_var` is never bound | 2 |
| A8 | `redact_url` returns its input unchanged | 5 |
| A9 | `redact_arguments` returns its input unchanged | 10 |
| A10 | nothing is written to stderr | 3 |

**A1 is the headline.** It is U11's exact failure shape - delete the emission outright - and it
killed all 18 tests that claim the event exists or carries anything. Every §8 case in this unit
dies against a silent stream, which is the property the #4/#5 pairing exists to guarantee and which
I would otherwise only have been able to assert.

### The vacuous assertion amputation found

**A7 deleted the `request_id_scope` call entirely and
`test_audit_scope_calls_request_id_scope_rather_than_setting_the_var_itself` still passed.**

It searched the file's text for `"request_id_scope(resolve_request_id("`. That string was still
there - in `audit.py`'s **module docstring**, which quotes the line as the proof that the mint and
the bind are one statement. The test was asserting that the documentation existed. It now walks the
AST: it finds the `audit_scope` function, collects the names of every `with` context call inside
it, and requires `request_id_scope` among them; separately it requires zero `request_id_var.set`
attribute nodes anywhere in the module. An AST walk sees code and cannot see prose. A7 now kills 2.

### Survivors I checked and accepted

- **A4 leaves `test_case17_arm2` (trace absent) passing.** Correct and expected: with the
  `traceparent` never read, the fields are absent, which is what arm 2 asserts. **This is precisely
  why arm 2 alone is not the case** - it is the single-arm test `DESIGN.md:1337-1342` warns about,
  and arm 1 is what dies.
- **A7 leaves both `test_the_scope_resets_request_id_var_*` passing.** Same shape: with the var
  never bound it reads `None` on the way out, which is what those tests assert. They are paired
  with `test_the_scope_binds_request_id_var_to_the_id_it_minted`, which A7 kills. The pair holds;
  either half alone would not.
- Every other survivor is a pure-function test of a different subject (`resolve_request_id`,
  `parse_trace_context`, the `redaction.py` unit tests under an `audit.py` amputation). Genuinely
  independent.

---

## 5. `request_id_scope` (N1) - **DECISION: call it**

**I called it, and it is the right mechanism.** `audit_scope`'s body is one line:

```python
with request_id_scope(resolve_request_id(inbound_request_id)) as request_id:
```

`DESIGN.md:604-606` requires `audit.py` to set the var *"in the same statement that mints the id"*
and to reset it *"in a `finally`"*. Calling `request_id_scope` makes the first requirement
literally true of one line, and satisfies the second **in shipped code in `correlation.py`** rather
than in a `try/finally` restated at each future call site - `correlation.py`'s own docstring gives
that as the reason it exists, and it is right: a leak test that only exercises a `finally` written
inside the test proves nothing about the server.

Deleting it would have meant writing `request_id_var.set()` plus a hand-rolled `finally` in
`audit.py` - strictly more code, discharging the same clause less directly, and moving the reset to
the one place a later refactor would be most tempted to drop it.

Guarded two ways so the decision cannot rot: mutation M10 (replace the scope with a bare `set()`)
and amputation A7 (never bind at all) both go red, via the AST test described above.

---

## 6. Design defects found by building

### D1 - `DESIGN.md:605` cites `§5.4`, which does not exist

Reported to the lead early; **already filed as ADR-0019 by the lead**, so I did not duplicate it.
§5 runs 5.1 (`:487`), 5.2 (`:555`), 5.3 (`:567`), then §6 at `:714`. The subject cited - the v1
`jobFeed` URL being itself a secret - is §4.1, `DESIGN.md:312-316`.

### D2 - the approval "mechanism" is required by two rows and defined nowhere → **ADR-0021 (Proposed)**

`DESIGN.md:1277` (§8's audit-event case) and `DESIGN.md:1755` (threat row **C4-R1**, rated
**High**) both require the event to carry *"the mechanism that produced"* `approval_state`, and both
cite **§5.3**. Grepping `mechanism` across §5.3's entire range (`:567-713`) returns **one** hit,
`:596`, which is about the `ContextVar`. §5.3's approval paragraph (`:663-669`) settles *what* is
recorded and *who* cannot be, and says nothing about a mechanism.

This is worse than a dangling reference: the citation *resolves*, to a real and relevant paragraph,
so a reader gets no signal that the specific thing is missing - and it is a High row's mitigation.
ADR-0021 proposes defining `approval_mechanism` in §5.3 with a closed vocabulary
(`elicitation` / `sampling` / `no_handler`, from §7.5's dual-era treatment) and repointing both
rows.

**What U3 shipped meanwhile:** `approval_mechanism` exists as an optional field, omitted when
unset, **with no vocabulary enforced**. U3 does not call the approval guard and has nothing to
enforce against; a closed set invented by the unit that cannot exercise it is a guess that later
reads as a decision. The vocabulary is U10's to emit and ADR-0021's to define.

### D3 - two control harnesses run nowhere (repository defect, not a design one)

`scripts/check-u15-gate-amputation.sh` and `scripts/check-u11-advisory-controls.sh` appear in
**neither `.github/workflows/ci.yml` nor `CONTRIBUTING.md`'s gate list** (`grep -c` = 0 in all four
combinations). `check-u11-advisory-controls.sh` was in my brief's list but not in CONTRIBUTING,
which the brief told me to prefer - so the two disagree, and the one I was told to trust is the one
missing it. This is the exact defect `CONTRIBUTING.md:108-112` documents about itself. Both pass
today (11/11 and 15/15 fired) - the finding is that nothing would notice if they stopped.

Filed as a task rather than an ADR; neither file is mine.

---

## 7. Implementation notes worth carrying forward

**`redact_arguments` is a fail-closed allow-list, not a deny-list of PII key names.** A deny-list
fails *open* on the argument nobody thought of, which is the direction `DESIGN.md:1787` (C6-I2)
already rejects for output fields. An unlisted key's value becomes `[REDACTED:<type>]` - the type
is not sensitive, and keeping it is what lets the audit event answer *"was a résumé body supplied
on this call"* without answering *"what did it say"*. `query` is deliberately not on the list: a
`search_candidates` query is free text, and a name is what you search for.

**The allow-list is path-keyed, and it was not at first.** The mutation harness found this: M14's
first form removed the container walk and *survived*, which said the walk was not doing what its
test believed. It was descending into a container whose own key nothing had allowed, then emitting
any leaf carrying an allow-listed name - so `job_id` escaped from inside a blob called
`secretBlob`. Measured, before the fix:

```
redact_arguments({"secretBlob": {"job_id": "LEAKED-job-42", "email": "a@b.invalid"}})
  -> {"secretBlob": {"job_id": "LEAKED-job-42", "email": "[REDACTED:str]"}}
```

A container under an unlisted key is now redacted whole. `test_a_container_under_an_ALLOW_LISTED_key_is_still_walked`
is the paired positive, so the fix cannot quietly turn the walk into dead code.

**Three secret query parameters are redacted, not one.** `DESIGN.md:313` names `api`, `sc` and
`companyId`, and `:311-313` makes `companyId` a credential class of its own. §8 #2 names `sc=`
because that is what an implementer reaches for first; redacting only it would satisfy the case and
leave two credentials in the log line.

**Every absence assertion in both test files is secret-safe.** `assert FAKE_SC not in line` fails
by printing both operands - so the test that exists to prove a credential never reaches a log would
publish it into CI output at exactly the moment one is leaking. Each check computes a bool first
and asserts on the bool, so a red test prints `assert not True`.

**A URL with nothing to redact is returned byte-identical**, rather than reassembled through
`urlencode`, which would re-encode innocent values. And `urlencode(..., safe="[]")` keeps the
sentinel literal: without it the brackets become `%5BREDACTED%5D` and every downstream grep for
`[REDACTED]` - in a test, in a log search, in an incident - misses it.

---

## 8. Gates

`uv sync --frozen` on `origin/main`'s lock; **`mypy` is the type gate, `pyright` was not run.**
Every row judged by exit code, re-run **after** the rebase onto `00bb4f4`.

```
uv lock --check                                   exit=0
uv run --frozen ruff check .                      exit=0   All checks passed!
uv run --frozen ruff format --check .             exit=0   29 files already formatted
uv run --frozen mypy                              exit=0   no issues in 20 source files
uv run --frozen pytest                            exit=0   189 passed, 2 deselected, 0 skipped
bash scripts/check-u0-test-controls.sh            exit=0   11/11 controls fired
bash scripts/check-u15-gate-controls.sh           exit=0
bash scripts/check-u15-gate-amputation.sh         exit=0
bash scripts/check-u11-advisory-controls.sh       exit=0   15/15 controls fired
bash scripts/check-u3-audit-controls.sh           exit=0   15 killed, 0 not killed
python3 scripts/check-committed-file-types.py --all exit=0 141 files, none refused
python3 docs/reviews/check-coupling.py docs/DESIGN.md exit=0
python3 docs/reviews/check-coupling-controls.py   exit=0
python3 docs/reviews/check-coupling-sweep.py      exit=0
python3 docs/reviews/check-plan-measurements.py   exit=0
python3 docs/reviews/check-obligations.py         exit=1   <- see below, NOT mine to fix
python3 docs/reviews/check-obligations.py --controls exit=1 <- aborts because the map above is red
```

**189 passed, 2 deselected, 0 skipped.** Baseline was **127**; this unit adds **62**
(41 in `test_audit.py`, 21 in `test_redaction.py`). 127 + 62 = 189, and the arithmetic closes.

### The two shifted obligation anchors - `docs/OBLIGATIONS.md` is not mine

Adding the U3 block to `ci.yml` moved two anchored lines. **The new line numbers, measured after
the rebase onto `00bb4f4`:**

| Obligation | Subject | Was | **Now** |
|---|---|---|---|
| **B75** | `# - name: Capability drift diff` | `ci.yml:402` | **`ci.yml:437`** |
| **B82** | `Relative links resolve` | `ci.yml:555` | **`ci.yml:590`** |

I **proved the repoint and reverted it** rather than committing it. Applying exactly those two
substitutions to `docs/OBLIGATIONS.md` takes `check-obligations.py` to **exit=0** (21 anchors
verified, up from 19) and `--controls` to **exit=0**. `git status` confirms `OBLIGATIONS.md` is
untouched on my branch.

```
sed -i 's|\.github/workflows/ci\.yml:402|.github/workflows/ci.yml:437|; \
        s|\.github/workflows/ci\.yml:555|.github/workflows/ci.yml:590|' docs/OBLIGATIONS.md
```

---

## 9. Files

**Written (mine exclusively):**
`src/fast_mcp_jobvite/audit.py`, `src/fast_mcp_jobvite/utils/redaction.py`,
`tests/test_audit.py`, `tests/test_redaction.py`,
`scripts/check-u3-audit-controls.sh`, `scripts/check-u3-audit-amputation.sh`,
`docs/adr/0021-approval-mechanism-is-required-by-two-rows-and-defined-nowhere.md`,
`changelog.d/27-audit-event-and-redaction.md`, this file.

**Shared, one block each, per §4's rule:** `.github/workflows/ci.yml` (a new non-adjacent U3 block,
two steps), `CONTRIBUTING.md` (two rows in the gate list, same commit as the CI steps).

**Not touched:** `pyproject.toml`, `uv.lock`, `tests/test_manifest.py` (the lead took the
dependency slot and added `loguru==0.7.3`), `docs/DESIGN.md`, `docs/OBLIGATIONS.md`, `CHANGELOG.md`,
`config.py`, `__main__.py`, `server.py`, `server.json`, `.env.example`, `utils/correlation.py`.

**Merge:**

```
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite merge --no-ff impl/u3-audit
```

Rebased onto `origin/main` at `00bb4f4` and the full gate re-run after the rebase. Not `--ff-only`:
`main` moves. Worktree `/tmp/impl-u3-work` removed after reporting.

---

## 10. What I did NOT verify

Things I could not settle, not things I did not try.

- **That a real MCP host puts a `traceparent` in `_meta`.** `DESIGN.md:656-662` cites
  `mcp/shared/jsonrpc_dispatcher.py:390` and `fastmcp/server/telemetry.py:95`, and `:651-653`
  already records that *"whether a given host injects at all is unverified"*. I read from
  `ctx.request_context.meta` as the design instructs and tested against the **wire contract** - a
  plain mapping with a `traceparent` key. I did not stand up a host, and I did not read
  `ctx.request_context` off a live FastMCP context, because no server exists to get one from until
  U5. **If FastMCP's `meta` is not a plain mapping of the `_meta` object, my parse call site is
  wrong and no test here would say so.** U5 or U9 should assert this against a real context.
- **That `logger.bind(**fields).info(msg)` is how this project will actually configure loguru.**
  `__main__.py` owns logging setup (`DESIGN.md:283`) and is U1's. I tested against a sink I added
  to the real `logger`, which proves the record carries the fields, not that the shipped sink
  serialises them into the audit stream the way an operator will read. **`ADR-0011` (three log
  producers, not one) is directly relevant and I did not reconcile my emission against it** - I
  read it for status only.
- **That `get_client_id` returns what §4.4 says on HTTP.** `services/` and the rate limiter do not
  exist. I take a `client_id: str | None` parameter and discard it on stdio; whether the value
  handed in is the *resolved* client id is U9's to establish.
- **Coverage against ADR-0010's 95% floor for `utils/`.** The coverage step is commented out in
  `ci.yml` with a U1 reference, and `[tool.coverage]`'s `fail_under` is the 80% overall floor. I did
  not run `pytest --cov` and therefore cannot state `redaction.py`'s number. Cheap for whoever
  turns the step on; I left it rather than reporting a figure from a differently-configured run.
- **Whether `AuditWriteError` reaching the tool boundary produces the right problem object.** I
  reasoned it maps through `problem_from_exception`'s `about:blank` path and wrote that in the
  docstring, and **ADR-0017 is Proposed and would change that answer to `/problems/internal-error`.**
  There is no tool boundary yet to test it against. Whoever writes it should assert this, and should
  re-read ADR-0017's status first.
- **The `Transport` value on a live server.** I defined the enum with `"stdio"` and `"http"`.
  `DESIGN.md` names the transports but I did not check that U1's transport selection uses the same
  two spellings, because `config.py` is U1's and in flight. **If U1 spells one differently, the
  audit event's `transport` field disagrees with the rest of the server and nothing currently
  fails.** Worth one grep once U1 lands.
