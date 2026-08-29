# FIX-AUDIT-LOGGING - report

**Branch:** `fix/audit-logging`, five commits on top of `5d48380`.
**Frozen design SHA:** `c15b138` (read as `git show c15b138:docs/DESIGN.md`, never the tree).
**Written:** 2026-08-28 11:36 PM CDT.
**Suite:** baseline `294 passed, 2 deselected, 0 skipped` -> now **`303 passed, 2 deselected,
0 skipped`**.

```
d008c32 docs(obligations): repoint two anchors my ci.yml insertion moved
fe2df6f test(logging): wire U1's harnesses into CI, and kill a vacuous survivor
df8a31e test(harness): wire the process arms into the U1 and U3 harnesses
3cd1ff1 test(logging): observe what the PROCESS writes, not what a fixture's sink saw
16a0bef fix(logging): configure the one log sink, so the audit fields reach the stream
```

Merge:

```bash
git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite merge --no-ff fix/audit-logging
```

---

## 1. What the process writes now, quoted

Both captures are the same script - import the shipped entry point, open one `audit_scope`,
`emit` it - run in a real child process, once against `5d48380` and once against this branch.

**Before** (`/tmp/prefix-check`, a worktree at `5d48380`), the whole event:

```
2026-08-28 23:17:49.566 | INFO     | fast_mcp_jobvite.audit:emit:313 - tool_invocation
```

`tool_name`, `request_id`, `transport`, `result_status`, `latency_ms`, `arguments` and
`caller_attribution` appear nowhere. That is `ai/tool-calling.md:171-179` breached in full.

**After**, the same call, one line (wrapped here):

```json
{"text": "2026-08-28 23:17:52.362 | INFO | fast_mcp_jobvite.audit:emit:313 - tool_invocation\n",
 "record": {"message": "tool_invocation",
   "extra": {"tool_name": "search_jobs",
             "request_id": "d5f80dc1-bbd4-4071-a2ea-cfb82c733816",
             "arguments": {"query": "[REDACTED:str]", "candidate_email": "[REDACTED:str]"},
             "result_status": "success",
             "latency_ms": 0.0026219986466458067,
             "transport": "stdio",
             "caller_attribution": "unavailable:stdio-has-no-caller-token"},
   "level": {"name": "INFO", "no": 20}, "name": "fast_mcp_jobvite.audit", ...}}
```

Every mandated field is in the bytes the process wrote. `test_the_process_writes_the_mandated_audit_fields`
asserts exactly this, parsed out of the child's stderr.

## 2. serialize versus a `{extra}` format - decided, and why

**`serialize=True`.** `ai/tool-calling.md:171-179` cares that the fields *arrive*. A
human-readable format names each field it prints, so the next field added to
`AuditEvent.to_record()` is dropped with no run going red - and `to_record` already omits
optional fields conditionally, so which fields exist varies per call. That is H-1 again wearing
a different hat. `serialize` emits the whole `extra` mapping structurally, so a new field
arrives by construction rather than by somebody remembering to widen a format string. It also
gives the audit stream a parseable shape, which the `jq`-able record above is.

Cost, stated rather than hidden: the stream is no longer pleasant to read by eye. The
human-readable rendering survives inside the `"text"` key, so `jq -r .text` recovers it.

## 3. The two logging systems - decided, and why

`audit.py` and `services/jobvite_client.py` write through loguru; `__main__`, uvicorn, httpx2
and the framework write through stdlib `logging`. Two libraries formatting independently onto
one fd is two record shapes interleaved in one file.

**Decided: forward stdlib into loguru** (`_InterceptHandler`, installed by
`logging.basicConfig(handlers=[...], force=True)`). One sink, one format, one place where a
sink failure surfaces. The alternative - configure both and accept two formats - leaves the
audit stream's destination, level and failure behaviour decided in two places, and `catch=False`
would then apply to only one of them.

`test_python_dash_m_gets_the_same_configured_sink` measures this on the real `python -m`
process rather than inferring it from shared source: the refusal line comes back as a
serialised record whose `record.name` is `logging`, which is only true if the bridge is live.

### 3a. It exposed a real credential leak, and that is a finding

Routing stdlib records into loguru turned `tests/test_jobvite_client.py::test_the_jobfeed_url_never_reaches_a_log_record_whole`
red, on this line:

```
HTTP Request: GET https://api.jobvite.com/v1/jobFeed?api=...&sc=TESTSECRET-not-a-real-credential&companyId=... "HTTP/1.1 200 OK"
```

`httpx2` logs that at INFO through stdlib `logging`, and `__main__`'s `basicConfig(level=INFO)`
was already writing it to stderr **in the clear, in production**. DESIGN.md:312-316 classifies
that URL as sensitive because it structurally carries `api`, `sc` and `companyId`. The client's
own redaction test could not see it, for the same reason the audit tests could not see H-1: the
test installs its own loguru sink and the leak travelled through the other library entirely.
**The same defect shape as H-1 and H-2, in a third place.**

Fixed by redacting at the one sink (`_redact_message`, a loguru `filter` that mutates
`record["message"]` and always returns `True`), calling `redact_text` rather than reimplementing
it, so DESIGN.md:312-316's "enforced in one place" still holds. Silencing `httpx2`'s logger was
rejected: that is an allow-list over producers, and the producer that matters is the one nobody
has thought of. `test_a_third_party_log_line_is_redacted_at_the_sink` deliberately uses a logger
name no dependency owns.

## 4. How the fail-closed branch was proved to run

**The sink is made to fail, not `bind`.** The child's stderr is pointed at `/dev/full`, which
returns `ENOSPC` on every write - what a full disk does. `sys.stderr` is swapped *before*
`__main__` is imported, because `configure_logging` binds the stream object it is given.

Measured on `5d48380`, `BEFORE_SIDE_EFFECT` against a real full sink:

```
child rc=0
PRE-FIX outcome: {"raised": null, "warnings": []}
```

The branch did not fire. On this branch the same script returns
`{"raised": "AuditWriteError", "detail": "... the call was not performed ..."}`.

All three branches of DESIGN.md:712-727 are asserted from a real write failure, each with the
same script against a writable file as its positive control, and every failing-sink arm also
asserts an in-process control described in §6.

**One code change fell out of this.** `audit._warn_on_stderr` is now best effort. The one log
sink *is* stderr, so the failure that kills the audit write kills the report of it too; an
escaping `OSError` would fail the read DESIGN.md:714-715 says must continue, and raise where
:716-727 says a warning must be returned. `BEFORE_SIDE_EFFECT` never reaches that function, so
the fail-closed branch is untouched.

## 5. H-3: the observed exit status

`test_a_crashing_mcp_run_exits_70_read_from_the_process` holds a port, starts the HTTP
transport on it, and reads the child's status.

**Observed: `70`**, with `OSError: [Errno 98] error while attempting to bind on address
('127.0.0.1', 33671): address already in use` on the stream and `the server terminated
abnormally` logged. Paired with `test_a_clean_stop_still_reports_zero`, which measures **`0`**
on the same construction with a free port and a SIGTERM - without it, `== 70` would pass
against a `main()` that returned 70 unconditionally.

**The code was already correct**; what was missing was the discharge. The previous one asserted
that `__main__.py`'s *source text* contains `os._exit(status)` and `EXIT_SOFTWARE = 70`. Every
one of those substrings can be present while the process exits 0. U1's mutation row M14 is
retargeted from the source-grepping test to this arm.

## 6. Harnesses - every row's result

**U1 mutation (`scripts/check-u1-boot-controls.sh`): 19/19 fired.** Five rows are new, and the
three that matter are the falsifiability proof for the whole branch:

| row | mutation | killed by |
|---|---|---|
| M14 (retargeted) | `os._exit(status)` -> `os._exit(0)` | `test_a_crashing_mcp_run_exits_70_read_from_the_process` |
| M15 | `configure_logging()` never called - the shipped H-1 tree | `test_the_process_writes_the_mandated_audit_fields` |
| M16 | `serialize=False` - the record survives, the fields do not | `test_the_process_writes_the_mandated_audit_fields` |
| M17 | `catch=True` - loguru's default, the H-2 defect | `test_a_failing_sink_fails_the_call_before_the_side_effect` |
| M18 | the sink stops redacting | `test_a_third_party_log_line_is_redacted_at_the_sink` |
| M19 | stdlib records bypass the one sink | `test_python_dash_m_gets_the_same_configured_sink` |

Every row asserts its anchor is unique *before* mutating (`assert s.count(anchor) == 1`),
`PYTHONDONTWRITEBYTECODE=1` is exported, and the pre-existing harness compares the restore
against a byte copy taken at the top.

**U1 amputation: 13 rows, all applied, none hung.** The four new rows are relabelled J-M -
they were appended as G/H/I/J and collided with the existing G/H/I, and a duplicate label reads
as a rerun of the earlier row. The `END.` banner moved back to the end.

| row | amputation | failed / passed | survivors among the process arms |
|---|---|---|---|
| J | `configure_logging()` never called | 6 / 65 | none (all 7 die) |
| K | it runs and configures NOTHING | 6 / 65 | none (all 7 die) |
| L | the sink's redactor returns without redacting | 1 / 70 | the six arms that are not about redaction |
| M | stdlib never bridged into loguru | 2 / 69 | the five arms that are not about the bridge |

L's and M's survivors are scope-limited by construction, not vacuous: each amputation removes
one behaviour and only the arms about that behaviour should die.

**U3: `tests/test_logging_process.py` added to both suites.** U3's own assertions all ran
against a sink its fixture installed. With the process arms in the suite, **A1 (`emit()` writes
nothing) now fails 22 and leaves 47**, and the surviving process arms are the three that do not
exercise `emit`'s write.

**Correction to the brief, measured.** The brief says U3's A1 leaves
`test_arm1_before_the_side_effect_the_call_fails` green. **At `5d48380` it does not** - I ran A1
on a clean worktree at that SHA and got `18 failed, 23 passed` with
`FAILED tests/test_audit.py::test_arm1_before_the_side_effect_the_call_fails` among them. That
claim was presumably true at an earlier revision. The *underlying* H-2 defect is real and I
reproduced it directly (§4).

**Other harnesses, unchanged and re-run:** U0 11/11, U15 15/15 controls and amputation exit 0,
U11 15/15, U4 mutation 17 killed / 0 not killed, U4 amputation 398 surviving assertions and no
row failing to apply.

## 7. CI and CONTRIBUTING

**Neither U1 harness had a CI step at all.** Every row in them - the ones predating this branch
included - ran only when somebody remembered. Adding rows to an unrun harness would have built
that defect a third time here, so both are wired into `ci.yml` (U1's block, immediately before
U3's) and into `CONTRIBUTING.md`'s gate list, in the commits that add the rows.

The two step bodies were extracted and run verbatim rather than reasoned about:
`STEP OK: 19 of 19 fired` and `STEP OK: 13 rows ran`, both `exit=0`. The amputation step gates
on rows-applied and on `COULD NOT APPLY` / `anchor is not unique` / `TIMED OUT`, not on the exit
code, because survivors are its output.

## 8. `docs/OBLIGATIONS.md`

My `ci.yml` insertion moved two anchors. The checker's own output, verbatim:

```
FAIL: B75: .github/workflows/ci.yml:563 no longer contains 'name: Capability drift report' - it is now at .github/workflows/ci.yml:598. Repoint the anchor.
FAIL: B82: .github/workflows/ci.yml:733 no longer contains 'Relative links resolve' - it is now at .github/workflows/ci.yml:768. Repoint the anchor.
```

The file is not mine, so I changed **only those two line numbers**, to the values the checker
names; no row's status, subject, standard reference or prose is touched. Handing over a gate I
had broken seemed worse. After: `Mappings: 28 | anchors verified: 21 | recorded as absent: 7`,
exit 0, and `--controls` 9/9 fired. Say the word and I will revert the two values.

This is the second time in this repository that a line-number anchor has decayed under an
insertion, which is task #6's subject.

## 9. Gates, all green, by exit code

```
uv run --frozen pytest                    303 passed, 2 deselected, 0 skipped
uv run --frozen pytest -m network         2 passed, 303 deselected
uv run --frozen pytest -m credentialed --collect-only   exit 5 (empty, as on base)
uv run --frozen ruff check .              exit 0
uv run --frozen ruff format --check .     exit 0, 43 files already formatted
uv run --frozen mypy                      exit 0, 32 source files
check-coupling.py / -controls / -sweep    exit 0
check-cross-references.py                 exit 0
check-obligations.py                      exit 0 ; --controls 9/9
check-plan-measurements.py                exit 0
check-committed-file-types.py --all       exit 0, 176 files
check-u0 11/11  check-u15 15/15 + amp 0   check-u11 15/15
check-u1 19/19 + amp 13 rows              check-u3 15 killed + amp 10 rows
check-u4 17 killed + amp 12 rows
```

`mypy` is the type gate; `pyright`'s editor overlay reports unresolved imports here because it
does not see the `uv` venv, and CONTRIBUTING.md:146-148 says to ignore it.

A changelog fragment is at `changelog.d/12-audit-logging-reaches-the-stream.md` (Fixed x2,
Security x1). The harness and CI changes get no fragment, per `changelog.d/README.md`.

---

## What I did NOT verify

1. **The audit event has never been emitted through a real MCP tool call.** No tool is
   registered yet (`test_the_server_registers_no_tool_yet`), so every arm here calls
   `audit_scope`/`emit` directly in a process configured the shipped way. What is proved is
   that the configured sink carries the fields; what is *not* proved is that a tool boundary
   passes the right values into `audit_scope`. That is U5's.

2. **The HTTP transport's audit record is untested end to end.** `client_id`, the HTTP
   `caller_attribution` (absent) and an inbound `X-Request-ID` are covered only by U3's
   in-process tests, which use a fixture sink. Same gap class, one transport over.

3. **`_redact_message` covers `record["message"]` only.** A credential inside an *exception*
   attached to a record - `record["exception"]`, which `serialize` renders - is not redacted by
   it. `jobvite_client` redacts its own exception text and `diagnose=False` keeps local variable
   values out, so I know of no live path; I did not enumerate the producers to prove there is
   none. **This is the strongest remaining candidate for the next instance of this defect
   shape** and I would file it rather than leave it in a report.

4. **`catch=False` under load.** I proved a sink failure now propagates and that the three audit
   branches handle it. I did not exercise a sink failure raised from inside uvicorn's or
   FastMCP's own logging calls, which now propagate into framework code that never expected a
   logging call to raise. `/dev/full` is the only failure mode I induced.

5. **The performance cost of `serialize=True` plus a per-record regex redaction** was not
   measured. Every record now walks `redact_text`, which splits on whitespace and parses any
   token containing `?` and `=`.

6. **PID 1 / container behaviour** is untouched by me and DESIGN.md still records it as
   unverified; my H-3 arm runs `python -m` as an ordinary child.

7. **CI itself has not run.** Every gate above was run locally with the same commands; I did not
   push, and `gh` was not used.

8. The **`/dev/full`-based arms are Linux-only**. There is no skip guard, so on a platform
   without `/dev/full` they would fail rather than skip - deliberate (a skip is a green that
   tested nothing), but it is a portability assumption nobody has stated before.
