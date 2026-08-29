# U9 - HTTP transport hardening: implementation report

**Agent:** `u9-http` · **Branch:** `feat/u9-http` · **Base:** `8202d13` · **Design frozen at:** `c15b138`

Read `docs/briefs/U9.md` for the brief. This is what was built, what was measured, and what was not.

---

## 1. The sentence that shaped the unit

`IMPLEMENTATION-PLAN.md` §U9: *"No §8 case owns this unit ... its tests are ours to specify and
nothing in the coupling gate will miss them if they are dropped."*

Every other unit here has a required case that goes red when its behaviour goes. This one does not,
so **the two harnesses are standing where a required case stands elsewhere**, and the amputation
harness deliberately runs **the whole suite** for each row rather than this unit's file - which is
the only way to answer *does anything notice*, and which found that U9 has coverage from `test_boot`
and `test_tools_jobs` it did not know it had.

## 2. What was built

New: **`src/fast_mcp_jobvite/http_hardening.py`** (430 lines), **`tests/test_http_hardening.py`**
(28 cases), **`tests/http_server_process.py`** (a uvicorn-in-a-thread helper),
**`scripts/check-u9-http-controls.sh`** (14 rows), **`scripts/check-u9-http-amputation.sh`**
(14 rows).

Changed: `server.py` (wires `auth=`, `middleware=`, `apply_tool_scopes`), `__main__.py` (one import
plus `**http_run_kwargs(settings)` on the HTTP `mcp.run`), `tests/test_tools_jobs.py` (**one test**,
see finding F2).

`config.py` was **not touched.** Every refusal U9 needs - unset `JOBVITE_HTTP_TOKENS` on `http`,
malformed JSON, an empty token key, an empty scope list, off-loopback without a declared TLS proxy -
already existed in `config._check_transport` and `_token_map_problems`, and `.env.example` already
declares all three variables. There was nothing in the HTTP half of `config.py` left to build.

**A NEW MODULE RATHER THAN MORE OF `server.py`, AND THAT IS A DEVIATION FROM THE BRIEF'S WORDING.**
The brief says *"in `server.py` and the HTTP half of `config.py`"*. `server.py` is 159 lines and
builds the instance for **both** transports; this is ~430 lines every one of which is conditional on
`http`. Keeping it separate makes *"this code does not run on stdio"* a property of an import rather
than of a branch a reader has to trace, and it collides with nobody - no other unit owns the file.
Say so if you want it folded in; it is a `cat` and three import edits.

### The six behaviours

| | Built | Where |
|---|---|---|
| `StaticTokenVerifier` from `JOBVITE_HTTP_TOKENS` at startup | `build_token_verifier` | `http_hardening.py` |
| `require_scopes` on the three data classes of §4.1 | `TOOL_SCOPES` + `apply_tool_scopes` | `http_hardening.py` |
| `allowed_hosts`/`allowed_origins` off loopback | `http_run_kwargs` | `http_hardening.py`, `__main__.py` |
| `RateLimitingMiddleware` with a mandatory `get_client_id` | `build_middleware`, `rate_limit_client_id` | `http_hardening.py` |
| `TimingMiddleware` + `StructuredLoggingMiddleware(include_payloads=False)` | `build_middleware` | `http_hardening.py` |
| Inbound `X-Request-ID` validated as UUIDv4 and echoed | `RequestIdMiddleware` | `http_hardening.py` |

### Three decisions worth your attention

**Scopes are applied ON HTTP ONLY, and that is a design position rather than an optimisation.**
`_RequireScopes.__call__` returns `False` for an **absent** token (`authorization.py:76-77`). stdio
has no token at all, so applying the check there removes **every tool** from the transport
DESIGN.md:844-848 declares fully authorised. Amputation row A5 deletes that guard and **20 tests go
red**; mutation row M7 does the same and its named test dies.

**The `client_id` is a SHA-256 digest of the token, never the token.** `RateLimitingMiddleware`
interpolates `client_id` into the text of the `MCPError` it **raises** on a trip
(`rate_limiting.py:171`), and that error reaches the caller and the log. A raw bearer token there
would publish a credential on the one path whoever is attacking the limiter is guaranteed to hit.
Row M9 swaps the digest for the token and the test dies.

**`allowed_origins` is the EMPTY list off loopback, not omitted.** The framework distinguishes them:
`allowed_origins is not None` is what sets `has_explicit_allowed_origins` (`server/http.py:242`), so
`[]` means *no browser origin is trusted* and `None` means *use the default*. On loopback both lists
are left alone - narrowing `allowed_hosts` there breaks `localhost` against a `127.0.0.1` bind for no
threat that exists inside the host. Both directions are asserted (M11, M12).

## 3. The verification bar, item by item

### The five absences, and the positive controls that give them meaning

`test_the_five_excluded_middleware_are_absent` checks `ResponseCaching`, `ErrorHandling`,
`ResponseLimiting`, `Retry` and `Ping` are absent **on both transports**. On its own it passes
perfectly against a server with no middleware at all, so:

- `test_the_three_adopted_middleware_are_present` - Timing, StructuredLogging, RateLimiting.
- `test_structured_logging_is_constructed_with_include_payloads_false` - **C2-I1's value**
  (`DESIGN.md:1732`).

**A HONEST NOTE ON `include_payloads`.** The framework's own default for that keyword is **also
`False`** (`logging.py:225`), so **deleting** the keyword changes no behaviour and a row that deleted
it could not fire. The mutation therefore **flips it to `True`**, which is the direction the threat
row is written about, and that row kills. The explicit keyword remains in the source so a framework
default flipping is a visible diff here rather than a dependency bump.

### Every other required item

| Required by the brief | Case | Row that proves it can fail |
|---|---|---|
| Missing scope: tool ABSENT from `tools/list`, direct call says "Unknown tool" | `test_a_token_lacking_a_scope_gets_unknown_tool_not_permission` | M6, M8, A4 |
| Two differently scoped tokens see different tool sets | `test_two_differently_scoped_tokens_see_different_tool_sets` | M6 |
| Rate limiting PER CLIENT, not the framework `"global"` | `test_rate_limiting_is_per_client` + `test_the_framework_default_throttles_everyone` | M3, M4, A10 |
| Malformed `X-Request-ID` replaced rather than used (C7-T1) | `test_a_malformed_inbound_request_id_is_replaced` (3 params) | M14, A11 |
| A valid one echoed byte for byte | `test_a_valid_inbound_request_id_reaches_the_tool_unchanged` | M13, A11, A12 |
| `JOBVITE_HTTP_TOKENS` unset on `http` fails at startup naming the variable | `test_boot.py::test_http_without_tokens_exits_rather_than_serving_openly` (U1's, pre-existing) | - |
| Positive control: a well-formed map starts AND its tokens authenticate | `test_boot.py`'s two "positive control N of 2" arms + **`test_a_well_formed_token_map_authenticates_and_the_tool_runs`** (new) | A1, A2 |
| `JOBVITE_MCP_PORT`/`JOBVITE_MCP_HOST` honoured | `test_the_host_and_port_are_honoured` | A14 |
| Non-loopback SETS the guard lists | `test_off_loopback_SETS_the_guard_lists` / `test_loopback_leaves_the_guard_lists_alone` | M11, M12, A13 |

**The "Unknown tool" assertion is made in both directions**: the message contains `Unknown tool`
**and** contains none of `scope`, `permission`, `forbidden`, `unauthorized`. Measured wording:
`Unknown tool: 'search_jobs'`.

**The per-client limiter arm has a NEGATIVE control**, and it is what makes the positive arm mean
anything: `test_the_framework_default_throttles_everyone` builds the same server with
`get_client_id=None` and the bystander does not merely lose a tool call - **it cannot complete the
connection at all**, failing on `initialize` with `Rate limit exceeded for client: global`. Without
that arm, `test_rate_limiting_is_per_client` would pass just as happily against a limiter that never
refuses anybody.

**These tests need a real HTTP server**, because an in-memory transport has no `Authorization`
header, no `X-Request-ID` and no access token. `tests/http_server_process.py` runs uvicorn in a
thread on a free port from `tests/boot_process.py` - a thread, not a subprocess, because nothing here
needs a process and a thread lets the test hold the server object it is asserting about.

## 4. Gate exit codes, read from the terminal

```
uv run --frozen ruff format .          61 files left unchanged
uv run --frozen ruff check .           All checks passed!                 exit 0
uv run --frozen mypy                   Success: no issues found in 49 source files   exit 0
uv run --frozen pytest                 530 passed, 6 deselected           0 skipped
shellcheck --severity=warning (both new harnesses)                        exit 0
python3 scripts/check-harness-anchors.py --self-check --floor 239
                                       267 anchors, all resolve           exit 0
bash scripts/ci-harness-gate.sh check-u9-http-controls.sh --controls-fired
                                       14/14 controls fired.              exit 0
bash scripts/check-u9-http-amputation.sh
                                       ROWS 14, ANCHORS APPLIED 14, VACUOUS 0   exit 0
```

`ruff format` was run **before** the final harness runs, and both harnesses plus
`check-harness-anchors.py` were re-run after it. `git status` shows the tree carries only the
intended files - both harnesses restored with `cp` and verified with `cmp` against a pristine copy
taken before row 1.

### The floors - DERIVED, not retyped. **The `ci.yml` edits are yours.**

`ci.yml` at `8202d13` carries `check-suite-floor.sh 502` (line 418) and
`check-harness-anchors.py --self-check --floor 239` (line 528).

| Floor | At my base `8202d13` | **On this branch** |
|---|---|---|
| suite | 502 | **530** |
| harness anchors | 239 | **267** |

**THESE ARE BRANCH-LOCAL AND `main` HAS MOVED UNDER ME.** U8 merged while this ran and task #56
records floors 560/278 for it; U12 was dispatched at `686820c`. My numbers are what
`feat/u9-http` measures against `8202d13`, which is the only tree I have run. **Re-derive both from
`ci.yml` after the merge** rather than adding my deltas to U8's - that arithmetic is exactly the
retyped constant `PREAMBLE.md` exists to stop. This branch adds **28** passing cases and **28**
harness anchors, and those two deltas are the part that survives a rebase.

### The two ci.yml steps this unit needs, for you to add

```yaml
      - name: U9 HTTP hardening controls, all fired
        run: bash scripts/ci-harness-gate.sh check-u9-http-controls.sh --controls-fired

      - name: U9 HTTP hardening amputation, every row applied
        run: |
          bash scripts/ci-harness-gate.sh check-u9-http-amputation.sh \
            --amputation --min-rows 14 --row-re '^########## A[0-9]+ '
```

`ci-harness-gate.sh check-u9-http-controls.sh --controls-fired` was run locally and exits **0**.
**Note the amputation harness takes ~13 minutes** - it runs the full 530-case suite once per row,
which is the point of it, but it is the slowest step in the file and you may want it on its own job.

## 5. The harness rows

### Mutation - 14 rows, **14 fired, 0 survived**

M1 `include_payloads` → `True` · M2 `ResponseCachingMiddleware` re-added · M3 `get_client_id=None`
· M4 `rate_limit_client_id` returns one constant · M5 burst loses the `+2` · M6 `search_jobs`
scoped to candidate PII · M7 scopes applied on stdio · M8 scopes never applied · M9 client id
becomes the token · M10 every token issued every scope · M11 `allowed_origins=None` · M12 guard
lists set on loopback · M13 header read under the wrong name · M14 inbound id bound unvalidated.

### Amputation - 14 rows, all applied, **0 vacuous**, 62 killing assertions

| Row | killed by |
|---|---|
| A1 the token verifier is never built | **11** |
| A2 the fail-closed check for an unset map deleted | 1 |
| A3 the client id no longer derived from the token | 1 |
| A4 `require_scopes` never put on any tool | 3 |
| A5 the stdio guard deleted | **20** |
| A6 the totality check on `TOOL_SCOPES` deleted | 1 |
| A7 the middleware stack is empty | 8 |
| A8 `StructuredLoggingMiddleware` dropped | 2 |
| A9 `TimingMiddleware` dropped | 1 |
| A10 `RateLimitingMiddleware` dropped | 2 |
| A11 the inbound header never read | 1 |
| A12 the middleware never binds the id | 5 |
| A13 the guard lists never set | 1 |
| A14 host and port ignored | 5 |

**A6 required a test that did not exist.** `test_every_known_tool_has_a_data_class` asserts today's
map is total - and it passes unchanged with `_assert_total` **deleted**, which is precisely this
project's vacuous-assertion shape: the guard that makes a *future* unscoped tool fail at import would
be gone and nothing would say so. `test_the_totality_check_refuses_a_tool_with_no_data_class` drives
the guard in both directions with its own positive control first. Written because A6 would otherwise
have been a vacuous row; the harness earned its place before it ever ran green.

## 6. Findings, each with its fix

**F1 - HIGH. The `request_id` a caller receives is NOT the one the transport validated.**
`tools/jobs.py:360` calls `audit_scope(SEARCH_JOBS, transport, arguments=..., meta=...)` with **no
`inbound_request_id`**, so `resolve_request_id(None)` mints a **fresh** id inside the scope
`RequestIdMiddleware` already bound. The caller's valid `X-Request-ID` is therefore validated,
bound, and then **not** used by the value stamped into `_meta` - the two ids differ on every HTTP
request. **This is U5's call site and I do not own `tools/`, so it is reported rather than fixed.**
Suggested fix, one line in `tools/jobs.py` (plus `from ..utils.correlation import request_id_var`):

```python
        with audit_scope(
            SEARCH_JOBS,
            transport,
            arguments=params.model_dump(mode="json"),
            meta=meta,
            inbound_request_id=request_id_var.get(),
        ) as event:
```

The alternative - making `audit.resolve_request_id` fall back to `request_id_var.get()` - is
`audit.py`, which I also do not own, and is the better fix if you want every future tool to get it
for free rather than each remembering the keyword. **My tests assert what U9 owns**: that the
transport reaches `resolve_request_id` with the header's value and binds the result. They use a
probe tool, and the docstring on `probe_server` says why in exactly these terms rather than implying
the end-to-end echo works.

**F2 - MEDIUM, and I changed a file that is not obviously mine.**
`tests/test_tools_jobs.py::test_the_server_lists_the_same_tools_on_http` asserted the transport
independence of the tool surface **through `client.list_tools()`**, and U9 makes that the wrong
instrument rather than making the property false: `require_scopes` now removes a tool the caller's
token does not hold, and an in-memory client presents no token, so the listing is empty on HTTP
while **registration is identical**. I repointed the assertion at the registry
(`registered_tools(server)`), which is the sentence the test's own docstring already claimed to be
testing, and wrote the history into its docstring. `tests/` was not in the brief's do-not-write list,
but this is U5's file and you should look at the diff. **The token-dependent listing is now covered
over a real HTTP request, where a token exists.**

**F3 - LOW, found while fixing F2.** That test's fixture was `JOBVITE_HTTP_TOKENS={"t":
"client-a"}` - a token mapped to a **string**, not to a list of scopes, which
`config._token_map_problems` refuses at boot. Nothing in that path reached the refusal, so the
fixture had been wrong and invisible since it was written. Fixed to `{"t": ["jobs:read"]}` in the
same edit.

**F4 - LOW, stated rather than defended.** `build_token_verifier` trusts the shape `json.loads`
returns, because `validate_settings` has already refused every malformed shape. A test that
constructs `Settings(...)` directly and skips validation - which several do - can therefore hand it
a malformed map and get a verifier with garbage scopes at exit 0. That is documented in the
function's docstring rather than re-validated, on the same reasoning `tools/jobs.py:245` uses for
its credentials. **Suggested fix if you disagree:** raise on a non-list value there too; it is three
lines and one more test.

**F5 - NIT.** The README line the brief and the plan both require - *a token lacking a scope makes
the tool absent from `tools/list` and a direct call returns "Unknown tool", not a permission error* -
is **not written**, because task #57 records the README as yours. Suggested text:

> **A token that lacks a scope does not get a permission error.** `require_scopes` removes the tool
> from `tools/list` entirely, so a direct call returns `Unknown tool: '<name>'` - the same response
> as for a tool that does not exist. This is correct and it is confusing: if an integrator reports a
> tool "missing", check the scopes on their token before checking `JOBVITE_TOOLS`.

## 7. The inherited limits: what I executed, and what remains a claim

**Executed.**

- **`get_client_id` is mandatory, and the default really is `"global"`.** Measured, not cited: with
  `get_client_id=None` a second client fails `initialize` with
  `Rate limit exceeded for client: global`. That is the negative control, and it fired.
- **Per-client keying works.** One client drained a 6-token bucket, a second was completely
  unaffected. **Still sequential** - the two clients ran one after the other, not at once.

**Consistent-with, and NOT a new measurement.** In the probe that sized the test budget, a burst of
6 yielded **4** tool calls to FastMCP's own client - a connect cost of exactly 2, matching
`DESIGN.md:395-403`. That re-confirms the number **for that one client** and says nothing about any
other. `test_the_burst_is_the_designs_sizing` asserts the **arithmetic** `desired + 2`, not the cost.

**Still claims. Carried, not resolved.**

- **The `2` is FastMCP's own client's connect sequence, not a protocol constant.** A heavier client
  - one that also lists resources or prompts - burns more, at which point `desired + 2`
  **under-provisions and refuses real tool calls**. No client but FastMCP's has been measured, and
  this unit measured none either.
- **Every limiter measurement is sequential and single-client.** Behaviour under **simultaneous**
  callers - the case production actually has - is unverified. Nothing here changed that.
- **`limiters.clear()` was never tested under load**, and it remains the only way to apply new
  limits, so a config reload is still a quota amnesty (C2-D1, accepted residual).
- **The limiter has NEVER been exercised on stdio.** `DESIGN.md:413-416` says so and calls it
  reasoning rather than measurement. `ANONYMOUS_CLIENT_ID` is asserted by a unit test that calls the
  function; **no stdio limiter arm was run**, and the constant's docstring says that in those words
  so no comment upgrades it.

`INBOUND_MAX_REQUESTS_PER_SECOND = 5.0` and `DESIRED_TOOL_CALLS_PER_BURST = 10` are **module
constants, not a sixteenth environment variable** - DESIGN.md's set is closed at fifteen and none of
them is an inbound rate. They are a choice, not a measurement, and nothing in the design names a
number. If you want them configurable that is a design change and an ADR, which is B15's whole
lesson and why I did not invent a variable.

## 8. What I could NOT settle

- **Whether F1's fix belongs in `tools/jobs.py` or in `audit.resolve_request_id`.** Both work; the
  second is better if more tools are coming, and both files are outside my ownership.
- **Whether the amputation harness's ~13-minute runtime is acceptable in CI.** It is the honest
  instrument for a unit with no required case - a per-file run would answer the mutation question a
  second time - but it is a real cost and the decision is yours.
- **Whether `http_hardening.py` should be folded into `server.py`** (see §2). A deviation from the
  brief's wording, made deliberately and reversible in one `cat`.
- **`registered_tools` reaches `server._local_provider._components`.** FastMCP's only public
  accessors are coroutines and `build_server` is synchronous, so there is no public sync path. It is
  a pinned beta (ADR-0001) and `test_scopes_are_applied_on_http` reads the result back through
  `list_tools`, so a rename fails a test rather than scoping nothing - but it is private API and I
  could not find a way to avoid it without making `build_server` async.
- **`X-Request-ID` carrying a bare newline over the wire.** `httpx` refuses to put one in a header
  at all, so the exact C7-T1 payload cannot travel. `tests/test_audit.py` covers the newline against
  `resolve_request_id` directly; what I proved is the half only the transport can - the header's
  value is what reaches the function. Three malformed shapes that DO travel (not-a-uuid, over-long,
  wrong-version) are parameterised.
- **`allowed_hosts`/`allowed_origins` were never exercised against a real off-loopback bind.**
  `http_run_kwargs` is asserted as a mapping; no test binds `0.0.0.0` and sends a bad `Host` header.
  Doing that needs a second interface or a spoofed header against a real bind, and I judged the
  framework's own guard to be the thing under test at that point rather than ours.

**Worktree removed** (`git worktree remove /tmp/u9-http-work`) after the final push.
