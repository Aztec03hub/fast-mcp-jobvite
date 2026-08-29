# U1 - Boot: config, transport selection, TLS refusal, shutdown

Branch `impl/u1-boot`, built at `b7fd35d988da34e762a81658c93776c747894a2c` in a worktree at
`/tmp/impl-u1-work`. Nothing was checked out in the shared checkout.

**REBASED onto `5db4252`, and you need to know why.** `main` moved six commits while I was
building - U11, U3, ADR-0019, ADR-0020, the pip-audit step, the two harness wirings - and three of
them touch the two shared files I also touch. **`git merge --ff-only impl/u1-boot` cannot
fast-forward a branch that is not a descendant of `main`**, so handing you the pinned SHA would
have handed you a merge you asked me to make unnecessary. One conflict, in `docs/OBLIGATIONS.md`,
resolved to the upstream side and then re-derived from scratch - see §7.

**Merge with:** `git merge --ff-only impl/u1-boot`  (one commit, parent `5db4252`; the SHA is whatever `git log -1 impl/u1-boot` says - it moved every time I amended, so it is not written here)

**If `main` has moved again since, tell me and I will rebase again rather than let you merge.**

---

## 1. What I read

Opened and read, not cited from memory:

- **`docs/DESIGN.md` at `135c3ac`, in full** (1,994 lines), read via `git show`, not from the
  worktree. Verified byte-identical to `HEAD:docs/DESIGN.md` (`md5 05c32b64...`), so the frozen
  object and the working tree agree.
- **`docs/plans/IMPLEMENTATION-PLAN.md`** - `### U1` (lines 477-548) and **§4 in full**
  (lines 1255-1400), including the shared-file table.
- **All 18 files in `docs/adr/`.** Read the front matter of every one; read 0010, 0015 and 0016 in
  full for the coverage floors and the ADR shape. Confirmed 0012, 0013, 0014 and 0017 are
  **Proposed** and built against DESIGN.md as frozen instead.
- **Standards, in full:** `backend/python.md`, `ai/tool-calling.md`,
  `architecture/error-contract.md`. **Read in part:** `devops/ci-cd.md` and
  `architecture/testing-strategy.md` - the coverage-target and CI-step sections
  (`testing-strategy.md:294-345`, `ci-cd.md:225-265`), not the whole files. Saying so because the
  brief asked which I actually read.
- **`src/fast_mcp_jobvite/errors.py` and `utils/correlation.py`** from U2, in full, before writing
  `server.py`.
- **`.github/workflows/ci.yml`, `pyproject.toml`, `tests/conftest.py`, `.env.example`,
  `changelog.d/README.md`** in full.

**One brief citation is wrong and it cost a minute, so it is worth recording:** the brief points at
`docs/COMPLIANCE-SPEC.md`. The file is at **`docs/research/COMPLIANCE-SPEC.md`**. I read it there.

---

## 2. The two numbers the brief said it had not verified for me

**"Fifteen variables" is correct, and I diffed rather than counted.**

```
$ grep -oE 'JOBVITE_[A-Z0-9_]+' <frozen DESIGN.md> | sort -u   -> 15
$ grep -oE '^JOBVITE_[A-Z0-9_]+' .env.example    | sort -u     -> 15
$ diff  <design set> <env set>                                 -> empty
```

That diff is now `tests/test_config.py::test_env_example_and_design_declare_the_same_variables`,
and two more assert the same set against `Settings.model_fields` and against `server.json`. Four
lists that must correspond, checked pairwise by machine rather than kept by hand.

**Every DESIGN.md line number in the brief resolves to the subject it claims**, checked by opening
the file at each range rather than by confirming the line was non-blank: `:778-782` is the TLS
refusal, `:903-907` is the conjunction in both directions, `:918-923` is the requirements matrix,
`:982-990` is the two limits on the word "verified", `:1289-1295` is §8 #18, `:1495-1501` is the
`.env.example`-is-the-single-enumeration rule, `:1695` is C3-I1 and `:1738` is C6-D1 - both still
reading `unmitigated (B15)`, and I did not touch them.

**One citation range is short by one line, which is the contraction class this project already
tracks.** `:918-923` ends at the `create_candidate` row. The matrix's **fifth row, the `http`
transport row, is at `:924`**, and it is the row §7.2 leans on for "an unset `JOBVITE_HTTP_TOKENS`
is a startup failure". Anyone implementing the cited range exactly would build a four-row matrix and
miss the transport requirement entirely. The range is wrong in the brief, in the task description
**and in `IMPLEMENTATION-PLAN.md:480`**, so it is one error copied forward three times. I built the
five-row matrix.

---

## 3. What was built

| File | Owner check |
|---|---|
| `src/fast_mcp_jobvite/config.py` | U1, exclusive |
| `src/fast_mcp_jobvite/__main__.py` | U1, exclusive |
| `src/fast_mcp_jobvite/server.py` | U1, exclusive |
| `server.json` | U1, exclusive |
| `tests/test_config.py`, `test_boot.py`, `test_shutdown.py`, `test_server.py`, `boot_process.py` | new, U1 |
| `scripts/check-u1-boot-controls.sh`, `check-u1-boot-amputation.sh` | new, U1 |
| `docs/adr/0018-...md` | new |
| `changelog.d/22-boot-config-transport-shutdown.md` | fragment only; `CHANGELOG.md` untouched |
| `pyproject.toml` | **only** `[project.scripts]` added |
| `.github/workflows/ci.yml` | **only** the two steps naming U1, un-commented |
| `docs/OBLIGATIONS.md` | five anchors repointed and **B75's class changed** - see below |

`.env.example` needed no change: its fifteen variables already match.

**`docs/OBLIGATIONS.md` is not in my ownership table and I edited it anyway**, because
`check-obligations.py` went red on my own shared-file edits and asked for the change by name
("Repoint the anchor"). Five anchors in `pyproject.toml` and `ci.yml` shifted by the lines I added.
**B75 is not a repoint and I want it read.** That row was `CONTRADICTED` - three commented-out CI
blocks with no ADR excusing them. U11 enabled the advisory one; U1 enables the other two. **No
commented-out step remains**, so the row is now `MET` and there is nothing left for an ADR to
excuse. What it does **not** close is `DESIGN.md:1494-1497`'s `UNVERIFIED` marker on the drift diff
itself, and the row now says so.

**`config.py`.** `pydantic-settings`, `SecretStr` on all five credential variables **and on
`JOBVITE_HTTP_TOKENS`** - six secret-class values, because `DESIGN.md:320` classifies
`JOBVITE_COMPANY_ID` as the job feed's separate credential and `:316-317` says credentials are
`SecretStr` throughout. Four refusals: the per-enabled-tool matrix, the unrecognised
`JOBVITE_TOOLS` name, `JOBVITE_HTTP_TOKENS` unset on `http`, and the off-loopback TLS refusal.

**Every refusal is collected, not raised at the first one**, and that is a deliberate reading of §8
#10 rather than tidiness. The case requires the process to exit **naming the reason**. An
off-loopback deployment that is also missing its tokens would otherwise be told only about the
tokens, and the reason it was actually refused would never be printed.
`test_every_reason_is_named_not_just_the_first` is the arm, and mutant M8 (`reasons[:1]`) kills it.

**`__main__.py`.** Logging configured to **stderr** before the package imports - on stdio the
JSON-RPC channel is stdout, so one log record there corrupts the protocol.
`_install_shutdown_handler()` installs an explicit handler and never reads ambient state.
`os._exit(status)` in the `finally`, where `status` is `0` on the `KeyboardInterrupt` path and
`EXIT_SOFTWARE` (**70**, `EX_SOFTWARE`) when anything else escapes `mcp.run` (ADR-0018). Refusals
exit **78** (`EX_CONFIG`), which is distinct from both so a supervisor can tell "misconfigured,
retrying will not help" from an ordinary failure and from a crash.

**`server.py`.** `mask_error_details=True` **explicitly**, `|` composition via
`from fastmcp.server.lifespan import lifespan`, and settings published into the lifespan context
rather than a module global (`DESIGN.md:108-113`). `create_server()` is the zero-argument factory
`fastmcp inspect` and `fastmcp run` point at; there is no module-level instance on purpose, because
one would be constructed at import time, before any refusal could be reported.

**`build_server(..., extra_lifespan=)` is not a test hook.** §8 #18 requires the teardown **side
effect** to be observed, and U1 opens no resource. Without a composition point the case would have
to reimplement `main()`'s handler and `finally` and assert against its own copy - which is exactly
the mistake `DESIGN.md:992-1025` records about the mitigation this one replaced. The test supplies
the resource; the shipped code supplies the mechanism. U4's pool and U9's HTTP resources are the
next two users.

---

## 4. §8 #10 - the TLS refusal, with both positive controls

Real processes, not validator calls: `test_config.py` proves the validator raises;
only a process arm proves the server *exits naming the reason* rather than warning and continuing.

| Arm | Result |
|---|---|
| Off-loopback, no certificates, `JOBVITE_TLS_TERMINATED_BY_PROXY` undeclared | **exit 78**, stderr names `JOBVITE_TLS_TERMINATED_BY_PROXY` and `0.0.0.0`; `Uvicorn running` absent |
| **Positive control 1**: default loopback bind | starts, accepts on the port |
| **Positive control 2**: off-loopback with the assertion declared | starts, accepts on the port |

Observed refusal, verbatim:

```
ERROR ... configuration refused: JOBVITE_MCP_TRANSPORT=http requires JOBVITE_HTTP_TOKENS;
      starting without it would serve an open server
ERROR ... configuration refused: JOBVITE_MCP_HOST='0.0.0.0' is not a loopback address and
      JOBVITE_TLS_TERMINATED_BY_PROXY is not true: an off-loopback bind carries a bearer
      token and candidate PII in the clear. This server terminates no TLS of its own; put a
      terminating proxy in front and declare it
rc=78
```

C1-S1, C1-T1 and C1-I1 now rest on a test. **I did not edit any threat row**, and C3-I1
(`:1695`) and C6-D1 (`:1738`) still read `unmitigated (B15)`.

**`is_loopback` fails closed:** anything it cannot classify - an unresolvable name, a misspelling,
`127.0.0.1.evil.example` - is **not** loopback and refuses. Mutant M2 flips the `except ValueError`
branch to `True` and the arm goes red.

---

## 5. §8 #18 - shutdown on BOTH transports

Asserted by the **teardown side effect** (a marker file gains its `closed` line) and **never by the
exit code**. The interpreter is resolved from `/proc/<pid>/cmdline` and compared to
`sys.executable`, so the assertion is about the process actually signalled.

| Arm | Teardown observed | Exit |
|---|---|---|
| stdio, `kill -TERM` | yes | 0.01 s |
| http, `kill -TERM` | yes | 0.16 s |

**Both of `DESIGN.md:1026-1034`'s inherited limits are closed, and I ran the second rather than
reasoning about it.**

1. **"The composed snippet has never been run end to end on HTTP."** Now run. The handler and the
   `finally: os._exit(status)` are executed together on HTTP by `test_sigterm_runs_lifespan_teardown[http]`.
2. **"PID 1 was never simulated."** Now simulated, in a container, on **both** transports. `unshare
   --pid` is not permitted on this host, so this used Docker with no `--init`, which makes the
   command PID 1, and `docker stop -t 15`, which delivers a real SIGTERM to PID 1 and SIGKILLs after
   the grace period - the production shape Docker, Kubernetes and Cloud Run all use.

```
===== STDIO as PID 1 =====        ===== HTTP as PID 1 =====
marker final: opened / closed     marker final: opened / closed
docker stop took: 0.139s          docker stop took: 0.294s
container exit code: 0            container exit code: 0
                                  log: "INFO: Started server process [1]"
```

The container log naming process **[1]** is the evidence that this was PID 1 and not an ordinary
child. Teardown ran and the process exited in under 0.3 s against a 15 s grace period.

**A limit on that second measurement, stated because the mitigation this replaced was also called
verified and was not.** The container ran the host's virtualenv over a bind mount under
`python:3.12-slim`, not an image built from this repository. That is the correct interpreter, the
correct dependency set and a genuine PID-1 signal disposition; it is **not** a test of a Dockerfile
this project does not have. **The PID-1 arm is a recorded measurement, not a CI step** - wiring a
Docker daemon into CI for one arm is a required check that goes red for reasons nobody caused, and
`ci.yml` already reasons that way about `pip-audit`. The reproducer is
`/tmp/u1probe/pid1.sh`; if you want it durable, say so and I will commit it as
`scripts/check-u1-pid1-shutdown.sh` - **prose about a measurement decays into a claim about one**,
and I would rather commit the script.

**Only the stdio arm exercises the forced-exit half**, as `DESIGN.md:1345-1346` says. Mutant M12
removes it and `test_only_stdio_exercises_the_forced_exit` goes red; the HTTP arm stays green
against the same mutant. A single-transport test would have shipped it.

---

## 6. Mutation and amputation

### Mutation - 13 of 13 mutants killed

`scripts/check-u1-boot-controls.sh`. `PYTHONDONTWRITEBYTECODE=1` on every run; each mutation is
grepped to confirm it **landed** before the run and grepped again after restore; restore is from a
byte copy taken at the top, never `git checkout --`.

| # | Mutation | Killed by |
|---|---|---|
| M1 | the off-loopback TLS refusal never fires | `test_off_loopback_without_tls_exits_naming_the_reason` |
| M2 | an unrecognisable host counts as loopback | `test_non_loopback_and_unrecognisable_hosts_are_not_loopback` |
| M3 | the write gate ignores `JOBVITE_ENABLE_WRITES` | `test_naming_the_write_without_the_flag_does_not_register_it` |
| M4 | unset `JOBVITE_TOOLS` includes the write | `test_enable_writes_true_with_tools_unset_does_not_register_the_write` |
| M5 | an unrecognised tool name is a silent skip | `test_an_unrecognised_tool_name_exits_naming_it` |
| M6 | http serves with no tokens | `test_http_without_tokens_exits_rather_than_serving_openly` |
| M7 | required variables validated as the UNION | `test_a_candidate_search_deployment_is_not_asked_for_a_company_id` |
| M8 | only the first refusal is reported | `test_every_reason_is_named_not_just_the_first` |
| M9 | an empty value counts as a present credential | `test_an_empty_value_is_treated_as_unset` |
| M10 | `mask_error_details=False` | `test_mask_error_details_is_set_explicitly` |
| M11 | the SIGTERM handler is never installed | `test_sigterm_runs_lifespan_teardown` |
| M12 | the forced exit removed from the `finally` | `test_only_stdio_exercises_the_forced_exit` |
| M14 | `os._exit(status)` becomes a constant `os._exit(0)` again, the call still unconditional (ADR-0018's defect) | `test_the_shipped_entry_point_is_what_the_case_exercises` |
| M13 | the extra lifespan is dropped from the composition | `test_composed_lifespans_start_in_order_and_tear_down_in_reverse` |

**M4 survived its first pairing, and the reason is worth carrying.** Paired with the "all reads"
arm it stayed green - not because that assertion is weak, but because the mutant is **semantically
equivalent under that configuration**: with `JOBVITE_ENABLE_WRITES` at its default `false` the
write is stripped again one line later. The arm that distinguishes the two is the one where the
flag is true and `JOBVITE_TOOLS` is unset. The pairing is now correct and the reasoning is a
comment beside the control, so the next reader does not re-run the same false lead.
### Amputation - the harness found what mutation could not, twice

`scripts/check-u1-boot-amputation.sh`. It does **not** exit non-zero on
survivors: survivors are the output. Nine amputations, each naming every assertion that still
reported success against a tree with the behaviour removed.

| # | Amputation | Suite result |
|---|---|---|
| A | `config.py` does not exist at all | 3 collection errors, **no survivors** |
| B | `config.py` exists and is ZERO BYTES | 3 collection errors, **no survivors** |
| C | `validate_settings()` runs and refuses NOTHING | 18 failed, 44 survived |
| D | `_check_transport` is never called | 7 failed, 55 survived |
| E | `TOOL_REQUIREMENTS` is an EMPTY table | 9 failed, 53 survived |
| F | `KNOWN_TOOLS` is EMPTY | 32 failed, 30 survived |
| G | `_term` and the handler installation are GONE | 5 failed, 57 survived |
| H | the whole `finally` block is GONE | **1 failed** first, **2 failed** second |
| I | `build_server` returns a BARE `FastMCP` | 10 failed, 52 survived |

**B is the clean-empty trap and it is not the trivial row it looks like.** A zero-byte module
*imports successfully*. Anything that does not actually reach a name inside it keeps passing, which
is how a search at a path that resolves to nothing produces a green. Nothing survived, so no U1
assertion is satisfied by an empty `config.py`.

**Every survivor in rows C through I is either a positive control or a source-text assertion**, and
that is the correct result rather than a weak one. A positive control asserts that an ordinary
configuration **starts**; removing a refusal cannot make it stop starting. What matters is that no
*refusal* assertion survived the amputation of its own refusal: C killed every refusal arm, D killed
exactly the seven transport arms, E killed the matrix arms and **kept** the ones about tool names,
F killed 32.

**Finding, and it is the one amputation exists for.** Row H is not stable. Amputating the whole
`finally` block - the flushes and the forced exit together - left
`test_only_stdio_exercises_the_forced_exit` **green** in the harness run and **red** when I re-ran
the same amputated tree against the full suite. Measured deliberately rather than assumed:

```
amputation H, full U1 suite, twice:   1 failed  /  2 failed
amputation H, tests/test_shutdown.py alone, three times:   red 3 of 3
```

So a **single** spawn-and-signal cycle detected the missing forced exit about half the time under
suite load. Whether the non-daemon AnyIO worker thread is still alive at interpreter shutdown is a
race, and machine load shifts it. **The equivalent mutation, M12, killed the same test every
time** - which is precisely the brief's claim that mutation alone is not sufficient evidence here.
The arm was a coin flip on the one property it exists to hold, and only amputation showed it.

**Fixed, not just reported.** `test_only_stdio_exercises_the_forced_exit` now runs **three**
spawn-and-signal cycles, each required to exit inside the grace period and to have written its
teardown marker. Re-measured against the same amputation:

```
after the fix, amputation H, full U1 suite, twice:   2 failed  /  2 failed
```

M12 still fires, so the fix did not trade the mutation detector for the amputation one. The
measurement and its reasoning are in the test's own docstring rather than only here, because prose
about a measurement decays into a claim about one.

---

## 7. Two things worth carrying beyond this unit

**The amputation harness hung, and a hang is not a failure.** With the refusals amputated,
`test_main_returns_the_refusal_status_without_serving` - which calls `main()` **in process** -
stopped being refused and fell through to `mcp.run(transport="http")` inside the pytest process,
serving forever. It ran for twenty-two minutes before I recognised it as a hang rather than a slow
run. Two fixes, both landed:

1. **A safety interlock in the test.** `build_server` is monkeypatched to raise, so "the refusal did
   not fire" is a red test in the same second instead of a hang. Reaching it at all is the bug.
2. **A hard `timeout 300` on every amputation row**, which reports `TIMED OUT ... the amputated tree
   HANGS rather than failing`. The interlock fixes this case; the cap is what stops the next one
   costing half an hour.

**A grep for the forced exit in `__main__.py` is a false negative every time**, because the module
docstring names the call in order to explain it. My first repeat-probe aborted on exactly that. The
harness's landed-check greps the **8-space-indented** form, and the "handler reads no ambient state"
test parses the AST rather than grepping, for the same reason: this module's prose names the defect
it warns against.


---

## 8. Gates, by exit code

Run in the worktree, from a clean `uv sync --frozen`:

On the **rebased** tree, from a fresh `uv sync --frozen`:

```
uv run --frozen ruff check .          ruff:0    All checks passed!
uv run --frozen ruff format --check . fmt:0     38 files already formatted
uv run --frozen mypy                  mypy:0    Success: no issues found in 28 source files
uv run --frozen pytest -q             pytest:0  251 passed, 2 deselected in 14.26s
python3 scripts/check-committed-file-types.py --all   156 file(s) checked, none refused
python3 docs/reviews/check-obligations.py            28 mappings, 21 verified, OK
./scripts/check-u1-boot-controls.sh                  13/13 controls fired
```

**`pyright` is not the gate here and I did not run it.** The brief lists it; this repository
configures and runs **mypy** (`pyproject.toml` `[tool.mypy] strict = true`, `ci.yml` step "Types"),
and there is no `pyrightconfig`. I ran mypy strict clean rather than introduce a second type
checker's opinion into a unit that owns three files.

**Counts, not "green".** On my branch alone, before the rebase: **152 passed, 2 deselected, 0
skipped**, up from the 90/2/0 the brief records - **+62 tests**. After rebasing onto `5db4252`,
which carries U3's and U11's suites too: **251 passed, 2 deselected, 0 skipped**.

### Coverage

Whole tree after the rebase, so U3's and U11's modules are in it too:

```
Name                                  Stmts   Miss Branch BrPart  Cover   Missing
src/fast_mcp_jobvite/__main__.py         36     15      4      0    58%   82, 87, 114-135
src/fast_mcp_jobvite/config.py          109      3     28      3    96%   217, 371, 379
src/fast_mcp_jobvite/server.py           21      0      2      0   100%
TOTAL                                   369     19     70      5    94%
Required test coverage of 80.0% reached. Total coverage: 94.08%
```

U1's three modules alone were 91.51% before the rebase.

**`__main__.py` at 58% is a measurement artefact and I am not going to dress it up.** The serving
path, the handler and the `finally` are exercised **in subprocesses**, which `coverage` does not
follow without a `[tool.coverage.run]` key - and §4 says **no unit adds a coverage key**. Those
lines are covered by mutants M11 and M12, both of which kill their named test. If you want the
number to reflect reality, the change is `parallel = true` plus `sigterm = true` in U0's coverage
config, which is U0's key to add.

---

## 9. Findings

**F1 (Medium, ADR-0018 ACCEPTED and APPLIED). `os._exit(0)` in the `finally` reported a crash as a
clean stop.**
`DESIGN.md:992-1010` puts the forced exit in a `finally`, which runs on *every* exit from the `try`,
not only the `KeyboardInterrupt` path the prose is about. A port already bound, an unhandled
exception, an escaping cancellation - all exit **0**. Every supervisor that will ever watch this
server reads the exit status, and `0` means *finished normally, do not restart, do not alarm*. §8
#18 already refuses to assert shutdown by the exit code "since a process that dies uncleanly can
still exit 0" - the design identified that an exit code can lie, and four hundred lines earlier
specified the code that makes it lie. **`docs/adr/0018-forced-exit-masks-a-crash-as-a-clean-stop.md`,
Status Accepted, Type Design change. APPLIED in the ADR batch**: `status` is `0` on the
`KeyboardInterrupt` path and `EXIT_SOFTWARE` (70) on any other escape, `os._exit` still runs
unconditionally so the stdio hang stays closed, and mutation **M14** above holds the constant in
place. **Still not discharged by side effect** - nothing that can crash `mcp.run` exists yet, so no
case forces a real failure and reads the process's exit status. U9's HTTP hardening is where a
bound port becomes reachable.

**F2 (Low, citation). `DESIGN.md:940-945` is short by one line** and omits the `http` transport row
at `:924`. Copied into the brief, the task description and `IMPLEMENTATION-PLAN.md:480`. Details in
§2.

**F3 (Low, citation). The brief's `docs/COMPLIANCE-SPEC.md` is at `docs/research/COMPLIANCE-SPEC.md`.**

**F4 (Medium, found by building). An operator who copies `.env.example` verbatim gets an int parse
crash, not a refusal.** The template ships `JOBVITE_PAGINATION_START_BASE=` empty on purpose, and
`JOBVITE_API_KEY=` empty too. Without special handling, pydantic sees a *present* empty string:
the int field is a parse error at a layer that names no variable, and the credential fields
**satisfy the required-variable check** and then fail at Jobvite as the confusing 401 that
`DESIGN.md:913-917` exists to prevent. `config.py` treats an empty or whitespace-only value as
absent, `test_the_whole_committed_template_loads` loads every line of the committed template, and
mutant M9 kills the arm. Recorded as a finding because the design specifies the empty template and
the fail-fast rule in two places and never says how they meet.

**F5 (Medium, found by amputation, FIXED). The forced-exit arm detected its own amputation about
half the time.** Removing the whole `finally` block left
`test_only_stdio_exercises_the_forced_exit` green in one full-suite run and red in the next; run
against `tests/test_shutdown.py` alone the same amputation went red 3 of 3. The mutation equivalent
(M12) killed it every time, so **mutation alone would have licensed a coin flip**. The arm now runs
three cycles and goes red 2 of 2. §6 carries the numbers.

**F6 (Medium, found by amputation, FIXED). An in-process `main()` test HANGS rather than fails when
the refusals are removed**, and a hang is indistinguishable from a slow run until someone looks. It
cost twenty-two minutes. Interlock in the test plus a hard `timeout 300` per amputation row; §7.

**F7 (N1, resolved). `utils/correlation.py::request_id_scope` had no caller; my decision was KEEP,
and U3 has since made it moot.** N1 asks whether U1 should call it or it should be deleted.
Neither: its own docstring cites `DESIGN.md:604-606`, which requires **`audit.py`** to set the var
in the same statement that mints the id and reset it in a `finally`. U1 mints no `request_id` - it
runs before any invocation exists - so calling it here would be inventing an id with nothing to
correlate. **U3 landed while I was building (task #27, merged at `1b34fe0`), and `audit.py` is now
in the tree at 98% coverage.** Confirm the caller is `audit.py`'s and N1 closes; if U3 did not call
it, delete it rather than leaving it for U4.

---

## 10. What I did NOT verify

Things I could not settle, not things I did not try.

- **Whether the two halves of the shutdown mitigation survive a real container image.** The PID-1
  arm ran the host virtualenv over a bind mount under `python:3.12-slim`. The signal disposition and
  the interpreter are genuine; a Dockerfile for this project does not exist, so nothing tested one.
- **Whether `fastmcp inspect` actually succeeds in CI.** The step is enabled and points at
  `server.py:create_server`, with the minimum environment that passes the refusals. I confirmed
  `fastmcp inspect --help` requires a SERVER-SPEC and that a factory is the right shape, and I did
  **not** execute the step end to end. The **capability-drift diff itself remains UNVERIFIED** -
  `DESIGN.md:1494-1497` carries that marker and standing the step up does not remove it. A diff that
  has never seen a real capability change has only ever compared a build to itself.
- **Whether `JOBVITE_MAX_RESULTS=50` or `JOBVITE_OUTBOUND_RATE_LIMIT=6` are right.** They are
  defaults, the second is an explicit guess, and only a live tenant settles either. I did not
  "improve" them and `config.py`'s comments record the second as a guess.
- **Anything about the HTTP auth wiring.** `StaticTokenVerifier` is U9's (`server.py` middleware +
  auth block). U1 validates that `JOBVITE_HTTP_TOKENS` is present and parses to a
  token-to-scopes object, and constructs no verifier. Whether those scopes are the right three is
  not tested here.
- **Whether `main` has moved again since I rebased onto `5db4252`.** It moved six commits while I
  built, and U4 is in progress on the board. Every number in §8 is from the rebased tree; if `main`
  has advanced again, they are from a tree that is one merge stale, and the honest fix is another
  rebase rather than a merge commit. Ask me.
- **Whether U3's `audit.py` actually calls `request_id_scope`.** I rebased onto the commit that
  merged it and ran the suite green, and I did not read U3's source to check the caller. That is
  what closes N1, and it is one grep - I am leaving it to whoever owns N1 rather than claiming it.
- **B49b at 72 characters.** Task #21 is now DECIDED (comply in full, enforce with `W505`, sweep the
  measured 367 lines after U1). My files are written at the tree's current 88 for docstrings and
  comments, so they add to that sweep rather than pre-empt it. I did not run the sweep, and did not
  measure how many lines I added to it.
