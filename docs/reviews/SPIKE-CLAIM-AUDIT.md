# SPIKE-CLAIM-AUDIT - every executed claim in DESIGN.md checked against its spike

Auditor: `spike-auditor`. Date: 2026-08-27. Task #28.

Sources opened at the lines cited: `docs/DESIGN.md` (1257 lines),
`docs/research/FASTMCP-SPIKE-4.md` (2354 lines), plus `docs/research/JOBVITE-API.md`
and `docs/DECISIONS.md` where the design's citation pointed outside the spike.

This is the first pass reading `FASTMCP-SPIKE-4.md` in full against `DESIGN.md`. Rounds 2, 3 and 4
each named the spike in their "what I did NOT review" sections.

Every line number below was taken from `grep -n` output, never counted inside a window.

Verdict key:

- **SUPPORTED** - the spike says what the design says it says, at the claimed strength.
- **OVERSTATED** - the spike supports something narrower; the design speaks more generally.
- **UNSUPPORTED** - the spike does not establish it, though nothing contradicts it.
- **NOT FOUND** - no supporting passage exists in the spike at all.
- **STALE** - the design contradicts itself, or carries a claim its own later text retracted.

`[REASONED]` marks my inference, kept out of the quotation columns.

## Counts

| Verdict | Count |
|---|---|
| SUPPORTED | 39 |
| OVERSTATED | 8 |
| UNSUPPORTED | 3 |
| NOT FOUND | 2 |
| STALE (self-contradiction) | 4 |

**Nothing was invented.** Not one claim describes a result the spike does not contain in some form.
Every OVERSTATED item is this project's characteristic failure: a narrow measurement spoken
universally, or a composition of two measurements reported as one measurement.

**Revision note.** The two claims the round-4 reviewer named as load-bearing - §4.4's burst
arithmetic and §7.5's era table - were re-opened at the source after the first pass had marked both
SUPPORTED. **Both moved to OVERSTATED on the second look** (**O-7**, **O-8**), for the same reason
in both cases: a result measured against one client's connect sequence, stated as a property of the
protocol. A closure pass over the document's self-claims added **S-4**. The first pass verified that
each number was *reproduced correctly*; it did not ask *what the number was a property of*. That
distinction is where both upgrades came from, and it is worth carrying into the next audit.

---

## 1. §4.3 Resilience

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 1.1 | **L216**: *"the retry check unwraps one level of `__cause__`. Measured: one call, **four rows created**."* | §13.3, **spike:999**: `ROWS CREATED = 4 -> ['PLACEHOLDER-CANDIDATE#1', 'PLACEHOLDER-CANDIDATE#2',` ... and above it `server-side invocations of create_candidate = 4` / `VERDICT: DUPLICATES CREATED`. `_should_retry` source in §13.3 shows `cause = error.__cause__`. | **SUPPORTED** |
| 1.2 | **L212-214**: *"`RetryMiddleware` cannot be scoped to exclude a tool"* | **spike:989**: *"There is **no `tools=`, `included_tools` or `excluded_tools` parameter**, and it hooks `on_request`,"* (sentence continues: *"so it applies to every tool call on the server."*) | **SUPPORTED** |
| 1.3 | **L217-222**: *"**One circuit breaker for Jobvite. 4xx must not trip it**"* and *"**An open breaker is distinguishable from an outage** ... `/problems/jobvite-circuit-open` with `status` 503 and a `retry_after` hint"* | `grep -n "breaker\|circuit"` over all 2354 lines of the spike returns **nothing**. `grep -n "tenacity"` likewise returns nothing. Neither the breaker nor the retry stack that precedes it has ever been executed in any form. | **NOT FOUND**, and stated loudly per the reporting instruction. §4.3 does **not** claim these as measured, so there is no false claim here - but §4.3 is a section whose one headline result *is* executed (the four rows), which lends its unexecuted neighbours borrowed credibility. See **S-4**: §12 L1219 asserts no reasoned-but-unexecuted claims about our own stack remain, and this is one of several. |
| 1.4 | **L223-225**: *"No 429 has ever been observed and no rate-limit header is returned"* | `JOBVITE-API.md` §14: *"`[ABSENT]` I did **not** observe a 429 from Jobvite"*; *"The response headers contain **no** `X-RateLimit-*`, `RateLimit-*`, or `Retry-After` header."* | **SUPPORTED** (evidence correctly lives in JOBVITE-API, not the spike) |

---

## 2. §4.4 Rate limiting - the four constraints

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 2.1 | **L235-237**: *"`get_client_id` is mandatory. The default keys every caller to the literal string `"global"` despite the docstring implying per-client."* | **spike:895**: `call 1: RAISED MCPError: Rate limit exceeded for client: global`. **spike:898**: *"Source confirms - `_get_client_identifier` returns the literal string `"global"` when no `get_client_id` is supplied (`fastmcp/server/middleware/rate_limiting.py:156`). So **the default is a server-wide limit wearing a per-client label.**"* | **SUPPORTED** |
| 2.2 | **L238-239**: *"Burst is sized `desired_calls + 2` per session. It counts every MCP request, not just tool calls. Measured: burst 3 yields 1 tool call, 5 yields 3, 10 yields 8."* | The arithmetic reproduces exactly. **spike:913** onward: `burst_capacity=3:  successful tool calls before refusal = 1  (MCPError at call 2)` and the 5→3, 10→8 rows; **spike:918**: *"Exactly **N-2**"*. Corroborated independently at **spike:1058** with `burst_capacity=6` → 4 on both eras. **But the `2` is sourced at spike:904-906** to a specific client's connect sequence: `- server/discover` / `- tools/call` / `- tools/list`, `total = 3`; and **spike:1067** attributes it to *"both run `server/discover` + `tools/list` at"* connect. **spike:198**'s raw `curl -X POST` sessionless `tools/call` issues neither. | **OVERSTATED** - see **O-7**. Four data points, two eras, all consistent; all with FastMCP's own `Client`. The `+2` is a property of that client's connect sequence, not of the limiter or the protocol. |
| 2.3 | **L240-242**: *"Limits are startup-only. Mutating them has no effect; only `limiters.clear()` applies new values, **and that resets every client's quota**"* | **spike:1080**: `after clearing limiters: 12 calls (None)          <- new settings applied`, preceded by `after mutating attrs: 1 calls (MCPError)          <- NO EFFECT` and `existing limiter objects: 1 -> ['global']`. **spike:1084**: *"A live config change requires `rl.limiters.clear()`, **which resets every client's quota**"* | **SUPPORTED**. `[REASONED]` note only: the measured run held exactly **one** bucket (`['global']`), so "every client's" is structural reasoning about `dict.clear()`. The spike words it identically, so the design added nothing. |
| 2.4 | **L243-245**: *"A trip raises `MCPError`, not an `is_error` result, so a rate-limit refusal does **not** carry an RFC 9457 problem object."* | **spike:1093**: `MCPError: Rate limit exceeded for client: global`, with §14.1 prose: *"a rate-limit refusal does **not** arrive as a tool error and will not carry an RFC 9457 problem object. A client sees a transport-level failure."* | **SUPPORTED** |
| 2.5 | **L250-253**: *"**Every one of those measurements was sequential and single-client.** ... and `limiters.clear()` was never tested under load."* | **spike:2348**: *"**Rate limiting under concurrency.** Every limiter test was sequential and single-client; I have not verified bucket behaviour under simultaneous callers, which is the case that matters in production."* **spike:2349**: *"**Whether `limiters.clear()` is safe to call on a live server.** ... I did not test it under load"* | **SUPPORTED** - the design absorbing the spike's own limitation, verbatim in substance. This is the model the rest of the document should follow. |
| 2.6 | **L247-248**: *"On stdio there is no token and thus no `client_id`, but there is exactly one caller, so the global bucket is correct there."* | No limiter arm was ever run on stdio. §13.1 and §14.1 ran in-memory and over HTTP (`mode=auto` / `mode=legacy`). The "exactly one caller" premise rests on a *different* finding, **spike:2313**: *"**stdio spawns a fresh server process per client connection**"*. | **UNSUPPORTED as measured** - see **U-2**. The conclusion is sound `[REASONED]`; the arm does not exist and the design does not say so. |
| 2.7 | **L255-261**: the outbound envelope, *"as-needed basis, and anything more frequent than once a day must be filtered"* | `JOBVITE-API.md` §14 `[OFFICIAL]`: *"Jobvite expects the API to be called on an as-needed basis, and that any customer needing to call it **more often than once a day** is required to constrain the call with at least one of: a workflow-state date filter, a bounded page size ..."* | **SUPPORTED** |

**Should have crossed and did not (§4.4):** **spike:1062-1063** measured the limiter across eras -
`mode=auto  : tool calls before refusal = 4` and `mode=legacy: ... = 4` - concluding *"✅ No era
interaction."* Given how much of §7.5 turns on era differences, an executed "no era interaction"
result for the limiter is worth one clause and is currently unused. Also unused, **spike:918**:
*"a client which reconnects frequently pays that toll every time"* - see **X-6**.

---

## 3. §7.4 Lifespan and shutdown

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 3.1 | **L559-560**: *"startup in order, teardown in strict reverse, verified."* | §9.1, from **spike:600**: `LIFESPAN A-startup (db)` / `B-startup (cache)` / `B-shutdown (cache)` / `A-shutdown (db)` / `EXIT=0`, with *"Left enters first, exit is strict reverse order, dicts shallow-merged."* | **SUPPORTED** |
| 3.2 | **L562-563**: *"Lifespan teardown does not run under SIGTERM - only SIGINT. Verified 3 of 3 with process identity checks, and reproduced on the previous major"* | **spike:623**: *"SIGTERM repeated **3/3, deterministic**. A/B control arm on **fastmcp 3.4.7** with the identical harness gives the **same result** - so this is longstanding, not a 4.0 regression"*, plus §9.2's ruled-out causes including *"a wrong PID (`/proc/<pid>/cmdline` checked)"*. | **SUPPORTED** |
| 3.3 | **L564**: *"Docker, Kubernetes and Cloud Run all stop containers with SIGTERM."* | **spike:484** says the same. **But spike:2341**: *"**Whether the SIGTERM behaviour differs under a real container runtime** (Docker `stop`, Kubernetes `preStop`). Tested with raw `kill -TERM` on Linux ... A container adds an init process, PID 1 semantics and a grace period that I did not simulate - **and PID 1 changes default signal dispositions, which §19.2 shows this mitigation is sensitive to.**"* | **OVERSTATED** - see **O-2**. |
| 3.4 | **L570-573**: *"`getsignal(SIGINT)` returns whatever is installed at that moment. A backgrounded process inherits `SIGINT = SIG_IGN`, so the one-liner installs **"ignore SIGTERM"**"* | **spike:1819**: `mitigation-installed: SIGINT handler was <Handlers.SIG_IGN: 1>` followed by `SIGTERM handler now <Handlers.SIG_IGN: 1>`, with §19.2 prose: *"**A backgrounded process inherits `SIGINT = SIG_IGN`, so the one-liner set `SIGTERM = SIG_IGN`: "ignore SIGTERM".**"* | **SUPPORTED** |
| 3.5 | **L576-580**: *"Uvicorn does overwrite both handlers during `run()`, confirmed from inside a live server ... uvicorn's `capture_signals` *restores* the original handlers and *re-raises* the captured signal."* | **spike:1784**: `INSIDE running server: {` ... `"SIGINT": "<bound method AppStatus.handle_exit ...>", "SIGTERM": "<bound method AppStatus.handle_exit ...>"}`, plus uvicorn source `[FROM SOURCE]` in §19.1 showing the `original_handlers` restore loop and `signal.raise_signal(captured_signal)`. | **SUPPORTED** |
| 3.6 | **L581-583**: *"On stdio there is no uvicorn at all, and teardown runs but **the process does not die** - a non-daemon AnyIO worker thread blocks interpreter shutdown, so even an explicit `sys.exit(0)` never completes."* | **spike:1858**: `variant=explicit          A-startup / A-shutdown          -> STILL ALIVE after SIGTERM`; §19.4 also shows `about to sys.exit(0)` → `STILL ALIVE`. **spike:1874**: `non-main threads still alive: ['AnyIO worker thread']` with `daemon flags: [('AnyIO worker thread', False)]`. | **SUPPORTED** |
| 3.7 | **L584-599**: *"**The verified implementation** installs an explicit handler rather than copying SIGINT's, and forces exit after teardown"* (code block: `_term` raising `KeyboardInterrupt`, plus `os._exit(0)`) | Verified in two separate halves. HTTP, **spike:1844**: `variant=explicit          SIGINT=default_int_handler   SIGTERM=<function _term>` → teardown runs, **no `os._exit` in that arm**. stdio, **spike:1884**: `  EXITED cleanly after SIGTERM` under the `os._exit(0)` remedy. | **OVERSTATED** - see **O-3**. The composed snippet as printed was never run end-to-end on HTTP. |
| 3.8 | **L601-605**: *"The test must assert both halves, on both transports ... The HTTP path passes on teardown alone; **only stdio catches the exit failure**"* | **spike:1932**: *"...alone; only stdio catches the exit failure."*, in §19.5's test mandate which also specifies resolving the interpreter pid *"via `/proc/<pid>/cmdline`"*. | **SUPPORTED** |
| 3.9 | **L607-613**: *"even when teardown runs, it runs *after* connections are gone. **Nothing that must complete before connections close may live in a lifespan teardown.**"* | **spike:657**: *"teardown runs **after** `Finished server process` - it is not part of graceful shutdown, and in-flight requests are already gone. Do not put anything in a lifespan teardown that must complete before connections close."* | **SUPPORTED** |
| 3.10 | §12 open question 6, **L1214-1218**: *"Shutdown depends on a uvicorn implementation detail ... that is behaviour uvicorn does not guarantee."* | **spike:1810**: *"**That is a dependency on a uvicorn implementation detail**, not on anything FastMCP or the stdlib guarantees."* | **SUPPORTED** |

---

## 4. §7.5 Human approval (MRTR)

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 4.1 | **L620-622**: *"Verified end to end on our default era: approve writes, deny refuses with the row count unchanged, no client handler fails closed."* | §17.3, from **spike:1577**: `--- SESSIONLESS (auto), handler APPROVES ---` → `is_error=False structured={'created': True, 'rows': 1, ...}`; **spike:1579** `--- SESSIONLESS (auto), handler DENIES ---` → `is_error=True`; and **spike:1587**: *"✅ **No client handler → fails CLOSED** with `Elicitation not supported`. The write cannot proceed."* | **SUPPORTED** |
| 4.2 | **L624-626**: *"Accessors are `ctx.input_responses` and `ctx.request_state` on `Context`, **not** on `request_context`."* | **spike:1568**: *"The accessors are **`ctx.input_responses`** and **`ctx.request_state`** on `Context` `[FROM SOURCE]`, not on `request_context`."* | **SUPPORTED** |
| 4.3 | **L637-640**: *"The guard must check the action AND the value: `action == "accept" and content.get("approve") is True`. An *accepted* elicitation carrying `approve: false` is still an acceptance."* | §17.6, **spike:1636**: `is_error=True content=["Not approved (action='accept'); refusing."]` with `server row count AFTER = 0`, and the spike's note that *"the *action* was an acceptance; only the value check saved it."* | **SUPPORTED** |
| 4.4 | **L644-650**: the era table - sessionless: MRTR works / `ctx.elicit()` raises; handshake: MRTR **raises, every arm including approve** / `ctx.elicit()` works. Framed *"Executed on both"* | All four cells reproduce. §20.2, **spike:2019**: `MRTR approve  -> RAISED MCPError: Tool 'create_candidate' returned an InputRequiredResult ...` with `server rows after this era's arms = 1   <- unchanged: NO write on legacy`; sessionless MRTR at §17.3; `ctx.elicit()` raising on sessionless at §15.1. **But the "works" cell is conditional.** §15.2's matrix has a third column the design's table does not: **spike:1229** `| HTTP | \`legacy\` | present | ✅ works |` versus **spike:1230** `| HTTP | \`legacy\` | **absent** | ⛔ \`MCPError: Elicitation not supported\` |`. **spike:1248**: *"Elicitation works only when the **client** both forces"* `mode="legacy"` *and supplies an elicitation handler.* | **OVERSTATED** - see **O-8**. The design collapsed a two-axis result (era × handler) onto one axis. **The mechanism is unaffected** - §20.4's verified guard refuses on no-handler on both eras, and §7.5 L621 and §8 L797-802 both carry the fail-closed behaviour. This is the table, not the guard. |
| 4.5 | **L652-654**: FastMCP's error quoted - *"only exists at MCP 2026-07-28 ... Use `ctx.elicit()` for server-initiated input on handshake-era connections."* | **spike:2041** `[FROM SOURCE]` (`fastmcp/server/mixins/mcp_operations.py:277-292`): `"(SEP-2322) only exists at MCP 2026-07-28; this connection "` and the following lines carrying the `ctx.elicit()` remedy. | **SUPPORTED** |
| 4.6 | **L656-659**: *"Claude Code negotiates `2026-07-28` automatically over HTTP, but for stdio only when `MCP_PROTOCOL_NEGOTIATION=auto` - so **a default stdio install lands on the handshake era**"* | **spike:1715** quotes Claude Code's own docs for exactly that, and **spike:1720** draws the conclusion. **But spike:1691**: *"Requested to size the practical picture for v1.1. **This is documentation research, not execution** -"* (continues: *"I have not driven these hosts against our server."*), and **spike:2347**: *"**Host behaviour is surveyed from documentation in §18, NOT executed.**"* | **OVERSTATED** - see **O-1**, the top finding. |
| 4.7 | **L659-660**: *"a sessionless-only guard would be broken for **the majority of local users** while passing every test we had."* | §20.2 says *"a sessionless-only guard would fail exactly where most local users are"*. Neither document holds any measurement of the user population. | **UNSUPPORTED** - see **U-1**. |
| 4.8 | **L660-663**: *"The discriminator is `ctx.request_context.protocol_version` ... `ctx.transport` is **identical** on both eras (`'streamable-http'`), and `session_id` is **populated on both**"* | §20.3, **spike:2067**: `rc_protocol_version        =  '2026-07-28'     '2025-11-25'`, with the `ctx_transport` row `'streamable-http'` on both and `session_id` populated on both; plus *"`MODERN_PROTOCOL_VERSIONS == ('2026-07-28',)`"*. | **SUPPORTED**. `[REASONED]` minor: that table was measured over HTTP only, so the parenthesised literal `'streamable-http'` is HTTP-specific. `transport` still cannot discriminate *era*, so the design's conclusion holds. |
| 4.9 | **L664-671**: *"An unrecognised protocol version refuses the write ... The discriminator is correct for the two eras that have been measured; a third case exists"* | No spike arm exercises an absent or unknown `protocol_version`. | **SUPPORTED as written** - the design states its own limit and presents this as a rule, not a measurement. |
| 4.10 | **L672-677**: *"That branch was inert - `input_responses` and `request_state` are class-level properties, so `hasattr` is True on every era"* | **spike:1991-1992**: `input_responses is a class-level property: True` / `request_state  is a class-level property: True`; **spike:2001**: `hasattr_input_responses          =  True                 True` measured in-tool on both eras. | **SUPPORTED** |
| 4.11 | **L679-683**: *"A host can auto-respond to elicitation without showing anyone a dialog ... the claim is *"the server requires an approval response from the host"* - **never** *"a human approved this."*"* | **spike:1739**, quoting Claude Code's docs: *"To auto-respond to elicitation requests without showing a dialog, use the `Elicitation` hook."* plus §18.2's honest-claim formulation. | **SUPPORTED** - documentation-sourced, but phrased as a capability rather than a host fact, so the §18 caveat does not bite here. |
| 4.12 | **L684-688**: *"the write is safe on every refusal path including abandonment, with `rows=0` independently confirmed. But an abandoned approval **hangs the call**, and a client-side timeout does not bound it"* | §17.6, **spike:1642**: `   (hang arm exceeded 60s wall)` followed by `server row count AFTER abandoned approval = 0`, and the spike's *"`Client(timeout=...)` did **not** bound it"*. | **SUPPORTED** |

**Should have crossed and did not (§7.5):** the unswallowable-era-check finding, §20.7. See **X-1**,
the highest-value omission in this audit.

---

## 5. §7.7 Middleware

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 5.1 | **L727-729**: *"`ResponseLimiting` (broken - raises on any tool with a return annotation)"* | **spike:348**: `huge_annotated:   RAISED RuntimeError: Tool huge_annotated has an output schema but did not return structured content`, with the control `huge_unannotated: len=150 is_error=False truncated=True`. | **SUPPORTED**. `[REASONED]` FastMCP derives `outputSchema` from the return annotation, so "return annotation" and "output schema" name the same set here. |
| 5.2 | **L729-730**: *"`ErrorHandling` (its default converts a caller's input problem into a raised server fault)"* | §13.2: `--- ErrorHandlingMiddleware(transform_errors=True)  [DEFAULT] ---` → `terr: RAISED MCPError: Internal error: TOOLERROR-DETAIL placeholder`, with *"A clean, actionable `ToolError` is **relabelled "Internal error"** - strictly worse than no middleware"*. | **SUPPORTED** |
| 5.3 | **L730**: *"`Ping` (inert on our era)"* | §14.4: `mode=auto  : tool OK (ok) | ping() -> MCPError: Method not found` vs `mode=legacy: tool OK (ok) | ping() -> True`. | **SUPPORTED** |
| 5.4 | **L737-739**: *"on this framework a middleware's default is not a safe starting point. **Four of the eight exercised were unusable or needed their defaults overridden.**"* | **spike:1038**: *"**Four of the eight exercised are unusable or need their defaults overridden.**"* Scoreboard rows counted independently: Retry ⛔, ErrorHandling ⛔, ResponseLimiting ⛔, RateLimiting ⚠️ = four. | **SUPPORTED** - count re-derived from the table, not taken from the sentence. |
| 5.5 | **L710-720**: *"§4.4 **measured** that this framework's sibling middleware defaults every caller to the literal string `"global"`"* + *"We have not executed its key derivation, and the honest position is that we do not need to"* | The `"global"` half is 2.1 above. The caching key derivation is genuinely unexecuted: **spike:320** proves only insertion and hit (`after call#2 (key=a): 1 <- CACHE HIT`), and the spike's could-not-verify list says *"cache TTL expiry - I proved cache insertion and hit, never eviction."* | **SUPPORTED** - the design labels the inference as inference. This is how the rest should read. |
| 5.6 | **L731-736**: the never-cache-one-time-state standing rule, *"**Measured on the confirmation-token preview before that mechanism was cut (§7.6)**"* | §16.2's six token arms ran with **no caching middleware installed anywhere**; **spike:1407** is the replay arm: `replay same token : is_error=True ['Confirmation token already used (replay refused).']`. The caching footgun appears only as prose in §20.8, citing §16.2 for a run §16.2 does not contain. | **OVERSTATED** - see **O-4**. |
| 5.7 | **L741-744**: *"**Result size is bounded inside each tool**, not by middleware ... `showing 50 of 1,240`"* | **spike:372**: *"Cap sizes inside the tool by paging the Jobvite result and returning "showing 50 of 1,240, use `offset`" - better for the model than a truncated blob anyway."* | **SUPPORTED** - the design lifted the spike's own recommendation, example string included. |
| 5.8 | **L707-708**: *"Adopted, each constructed with explicit arguments: `Timing`, `StructuredLogging` with `include_payloads=False`, and `RateLimiting` with `get_client_id`."* | §6.2 verified Timing and StructuredLogging, with *"`include_payloads=True` logs tool arguments verbatim, which for Jobvite means candidate data. Leave it at the default `False`."* §13.1 verified per-client keying: `beta  (should be UNAFFECTED by alpha): successful tool calls = 6` after alpha drained its own bucket. | **SUPPORTED** |

---

## 6. §1.1 and the one recorded Jobvite `200`

| # | DESIGN claim | Evidence | Verdict |
|---|---|---|---|
| 6.1 | **L55-59**: *"**One** genuine Jobvite `200` exists in our evidence: a third-party VCR cassette recorded against a live tenant (`JOBVITE-API.md` §6.1) ... contains real candidate data including EEO fields"* | `JOBVITE-API.md:393`, §6.1 heading `[RECORDED-3P]`, and its Handling note at `:402`: *"That cassette is a third-party artifact containing an `api`/`sc` credential pair in the recorded request URI, and candidate records including EEO attributes."* | **SUPPORTED** |
| 6.2 | **L286-291** (§4.5): *"a 1-based server **clamps 0 to 1** - **confirmed** against the one genuine Jobvite `200` in our evidence (`JOBVITE-API.md:401`)"* | `JOBVITE-API.md:399`, verbatim: *"**`start=0` is accepted and returns records**, rather than erroring. That falsifies the "1-based and strict" hypothesis, **though it still does not distinguish "0-based" from "1-based with clamping"**"* | **OVERSTATED**, and the citation is wrong: `JOBVITE-API.md:401` is a blank line; the content is at `:399`. See **O-5**. |
| 6.3 | §12 open question 4, **L1211**: *"**Whether success bodies carry a `status` block at all.** The parser tolerates both."* | `JOBVITE-API.md:397`: *"**A success body DOES carry a `status` block.** ... **This closes the open question** in the contract document's error rule."* And DESIGN's own **L761-763** (§8): *"whether a success body carries a `status` block. That last point already answers what was an open question."* | **STALE** - see **S-2**. |

---

## 7. §10 dependency and packaging

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 7.1 | **L843-861**: the packaging block, introduced *"Packaging, verbatim, because both lines are load-bearing"*, containing three pins including `mcp==2.1.1` (**L849**) | The **verified** recipe (§1.3, repeated at §12.1) is two dependencies plus `prerelease = "explicit"`. **spike:110** is the resolve *result*: `fastmcp 4.0.0b4 | fastmcp-slim 4.0.0b4 | pydantic 2.13.4  <- STABLE | mcp 2.1.1` - `mcp` was *resolved to* 2.1.1, never *pinned to* it as an input. | **OVERSTATED** - see **O-6**. The block as printed has never been resolved. |
| 7.2 | **L866-869**: *"`--prerelease=allow` is global in uv and pulls in a beta pydantic; `explicit` alone fails to resolve because `fastmcp-slim` arrives transitively."* | **spike:88**: *"`--prerelease=allow` is **global** in uv, so it dragged in **`pydantic 2.14.0b1`**, a *beta pydantic* we never asked for. Constraining it to `prerelease = "explicit"` alone **fails to resolve**"*, with the uv hint quoted immediately after. | **SUPPORTED** |
| 7.3 | **L838-842**: *"**`mcp` is pinned explicitly** ... the `ResponseLimiting` regression arrived through the transitive SDK with zero change to the code that broke"* | **spike:370**: *"the `mcp` 1.x → 2.x upgrade removed the behaviour it depended on. So this is a **regression via a dependency upgrade**, which is why it slipped through: the middleware's own code never changed."* | **SUPPORTED** |
| 7.4 | **L872-885**: four httpx2 claims - Tom Christie authorship, pydantic stewardship plus README quote, releases through 2.12.0 vs httpx's `1.0.devN`, `MockTransport` built in - introduced by *"That characterisation was wrong and was never checked. **Verified:**"* | **None of this is in the spike.** **spike:81** says the opposite: *"Cost: `httpx2` is a fork with a much smaller ecosystem, and `respx`-style test tooling may not support it."* The four claims live in `docs/DECISIONS.md` D17 (`:219-240`), sourced there as *"Verified against PyPI and the repository"*. | **NOT FOUND in the spike**, **SUPPORTED elsewhere** - see **U-3**. This is a spike characterisation the design correctly *reversed*; only the citation is missing. |
| 7.5 | **L889-899**: *"`fastmcp inspect` output is emitted and **diffed between builds**"* + *"**UNVERIFIED:** that this actually catches the drift it is meant to catch is reasoning, not an executed result"* | §10 verified `fastmcp inspect` runs (`INSPECT_EXIT=0`). Nothing verifies the diff. | **SUPPORTED** - correctly labelled UNVERIFIED at its point of use, as the front matter promises. |
| 7.6 | **L836**: *"Python `>=3.12`."* | §10.1 ran 3.11.15 and 3.12.3: *"✅ no behavioural difference between 3.11 and 3.12."* Spike §12.1's snippet says `requires-python = ">=3.11"`. | **SUPPORTED** - a floor above the tested range is conservative, not a claim. The divergence from the snippet is deliberate and harmless. |

---

## 8. Other executed claims across the document

| # | DESIGN claim | Spike evidence | Verdict |
|---|---|---|---|
| 8.1 | **L142-146** (§2.2): *"**Annotations are advisory only** - verified: one non-test reference exists in the entire framework, a field-name alias table, and nothing acts on them."* | **spike:1327**: *"entire installed package returns exactly **one** non-test hit - a field-name alias table in"* `fastmcp/_compat.py:47`, with *"There is no enforcement path, no prompt, no gate."* | **SUPPORTED** |
| 8.2 | **L133-136** (§2.2): *"a measured defect on our default transport: stdio spawns a fresh server process per connection, so an in-process token store is per-connection there."* | **spike:2313**: *"incrementing to 2, because **stdio spawns a fresh server process per client connection**, so"* in-process state resets between arms. | **SUPPORTED** |
| 8.3 | **L331-336** (§5.1): *"Verified across five arms: because they are *returned* rather than *raised*, they are untouched by `ErrorHandlingMiddleware`, by `transform_errors`, and by `mask_error_details`."* | **spike:1134**: *"**RFC 9457 problem objects are completely unaffected** - by the middleware, by `transform_errors`,"* and by `mask_error_details`, *"in all five arms."* Five labelled arms present in §14.2, `problem:` row identical in each. | **SUPPORTED** - arms counted in the transcript, not taken from the sentence. |
| 8.4 | **L497-503** (§7.1): *"**Sessionless `2026-07-28` is the default era**, with the handshake era served simultaneously - verified on one server, one port"*, plus the proxy-header and `server/discover` consequences | **spike:229**: `ERA-PROBE: on_call_tool protocol_version=2026-07-28      <- auto: sessionless, on_initialize NEVER fired` then the handshake lines. **spike:240**: *"**Both eras work against one server, on one port, simultaneously.**"* Proxy headers from §3.2's `-32020` errors; the `server/discover` caveat from §3.3. | **SUPPORTED** |
| 8.5 | **L511-513** (§7.2): *"**`require_scopes` removes an unauthorised tool from `tools/list` entirely**, and a direct call returns "Unknown tool", not a permission error."* | **spike:272**: `{"jsonrpc":"2.0","id":2,"result":{"content":[{"text":"Unknown tool: 'write_thing'","type":"text"}],` preceded by `tools visible: ['ping']`. §4's note: *"`require_scopes` **removes the tool from `tools/list`** and reports **`Unknown tool`**, not a permission error."* | **SUPPORTED** |
| 8.6 | **L524-528** (§7.3): *"`fastmcp.json` **cannot** express a required environment variable: with one unset the server starts normally and the tool receives the literal string `${JOBVITE_API_KEY}`"* | **spike:680**: `  TOOL -> JOBVITE_API_KEY=${JOBVITE_API_KEY} MODE=spike` under the `UNSET` arm. §10: *"**VERIFIED, and the failure is silent.** ... No warning, no non-zero exit."* plus the schema note that `env` is a flat `dict[str,str]` with no `required` slot. | **SUPPORTED** |
| 8.7 | **L797-802** (§8): *"**approval on BOTH eras**, because the no-handler arm surfaces differently on each ... **The test asserts the invariant that matters - the row count did not change - not the error shape.**"* | §20.5's per-era table (**spike:2159**: `| sessionless | **raises** `MCPError: Elicitation not supported` |`) and **spike:2165**: *"lesson from §16.3 in a new form - assert the effect, not the error shape."* | **SUPPORTED** - a spike lesson that crossed cleanly. |
| 8.8 | **L790-791** (§8): *"the second leg actually consumes `ctx.input_responses`"* | **spike:1604**: *"a test on our side asserting the second leg actually consumes `ctx.input_responses`."* (§17.4, the `InputRequiredRoundsExceededError` round cap). | **SUPPORTED** |
| 8.9 | **L785** (§8): *"token replay, expiry, and payload mismatch each refused;"* listed among **required** test cases | §16.2 verified those arms - but §7.6 (**L689-690**) and §2.2 (**L127**) record the token as **cut**, and §20.8 recommends *"Drop token-always."* | **STALE** - see **S-3**. |
| 8.10 | **L806-807** (§8): *"**A guard that refuses everything is not a guard, and its refusals prove nothing.** Every refusal-path test is paired with a positive control"* | **spike:1439**: *"**A guard that refuses everything is not a guard, and its refusals prove nothing.** The cause was my"* own bug (§16.3's `exp` float separator, which made every arm refuse). | **SUPPORTED** - the spike's self-caught positive-control failure became a testing rule. |
| 8.11 | **L1090** (§11, C4-E): *"The discriminator is measured rather than inferred (§7.5)"* | §20.3, as at 4.8. | **SUPPORTED** |
| 8.12 | **L1141** (§11, C9-T): *"an `mcp` major bump removed the behaviour a merged upstream fix depended on, and broke a middleware whose own source never changed"* | **spike:370**, including PR #3756 *"merged to `main` on 2026-04-05"*. | **SUPPORTED** |
| 8.13 | §12 open question 2, **L1208-1210**: *"**The `start` base.** Now probed at runtime (§4.5), but the probe itself is unverified against a live server."* | DESIGN **L281-292** (§4.5) **removed** the probe: *"An earlier revision proposed a runtime probe and its logic was inverted ... **What we do instead, and it needs no probe.**"* | **STALE** - see **S-1**. |

---

# Ranked findings - OVERSTATED and UNSUPPORTED

## O-1 (highest) - §7.5's host-negotiation claim is documentation research presented as execution

**DESIGN L644** opens the era block: *"**The two mechanisms are exactly complementary, and a
single-mechanism guard is broken on one era whichever it picks.** Executed on both:"* - true, and
supported by §20.2. **DESIGN L656-659** then continues in the same voice:

> *"**This matters most where most users are.** Claude Code negotiates `2026-07-28` automatically
> over HTTP, but for stdio only when `MCP_PROTOCOL_NEGOTIATION=auto` - so **a default stdio install
> lands on the handshake era**, and a sessionless-only guard would be broken for the majority of
> local users while passing every test we had."*

The spike's §18 carries a framing sentence the design dropped, **spike:1691**:

> *"Requested to size the practical picture for v1.1. **This is documentation research, not
> execution** - I have not driven these hosts against our server."*

and repeats it in the could-not-verify list, **spike:2347**:

> *"**Host behaviour is surveyed from documentation in §18, NOT executed.** I have not driven Claude
> Code, Cursor or Claude Desktop against our server."*

**Why it matters.** The design's front matter (**L16-17**) promises *"Every claim about FastMCP or
the MCP protocol is executed."* This claim is not about FastMCP or the protocol - it is about a
**host's negotiation behaviour**, read from that host's own documentation. It is load-bearing:
it is the stated reason the dual-era guard exists at all, and the stated reason a sessionless-only
guard would have shipped broken.

`[REASONED]` The guard itself stays correct either way - §20.2 proved MRTR raises on handshake, so
both arms are needed regardless of who negotiates what. What moves if the doc is stale or the
behaviour changes is the *justification*, not the mechanism. The remedy is one clause marking it as
first-party documentation rather than execution, the way §18.1 does. Note the design already handles
the Claude Desktop half honestly at §12 question 5 (*"No first-party statement found"*); the Claude
Code half got no such treatment.

## O-2 - the SIGTERM mitigation's container behaviour is asserted, and the spike flags PID 1 as untested

**DESIGN L562-565** states the gap, then *"Docker, Kubernetes and Cloud Run all stop containers with
SIGTERM"*, and **L584** presents *"The verified implementation"*. **spike:2341**:

> *"**Whether the SIGTERM behaviour differs under a real container runtime** (Docker `stop`,
> Kubernetes `preStop`). Tested with raw `kill -TERM` on Linux, including the stdio hang in §19.4.
> A container adds an init process, PID 1 semantics and a grace period that I did not simulate -
> **and PID 1 changes default signal dispositions, which §19.2 shows this mitigation is sensitive
> to.**"*

**Why it matters.** §19.2 is the section proving the *previous* mitigation silently inverted itself
depending on ambient signal disposition. The spike explicitly names PID 1 as the next candidate for
that same hazard class. The design carries the conclusion (containers use SIGTERM) and the fix, but
not the open flank.

`[REASONED]` The explicit handler is materially safer than the one-liner precisely because it does
not read ambient state, so I expect it to hold under PID 1 - but that is my reasoning, not a
measurement, and §7.4 should say which it is. One sentence.

## O-3 - "the verified implementation" was verified in two halves, never as printed

**DESIGN L584-599** prints the `_term` handler plus `os._exit(0)` and calls it *"The verified
implementation"*. The halves were run separately:

- HTTP, **spike:1844**: `variant=explicit          SIGINT=default_int_handler   SIGTERM=<function _term>` → teardown runs. **No `os._exit` in that arm.**
- stdio, **spike:1884**: `  EXITED cleanly after SIGTERM` under the `os._exit(0)` remedy.

**Why it matters.** `[REASONED]` This is the mild form of the exact error §19.7 records against the
spike author: *"**A mitigation that produces the desired outcome in one environment is not a
verified mitigation**"*. The composed snippet is very likely fine - `os._exit` after a completed
teardown is transport-agnostic - but "verified" is doing more work than the transcripts support.
§7.4's own test mandate (**L601-605**) would settle it in one CI run, which is the cheapest possible
close.

## O-4 - "Measured on the confirmation-token preview" was not measured

**DESIGN L731-736** states the standing rule and closes: *"**Measured** on the confirmation-token
preview before that mechanism was cut (§7.6)"*. **DESIGN L697-699** (§7.6) repeats it as *"a caching
footgun (a cached preview re-issues a spent token and disables the write for the cache TTL, on a
tool annotated `readOnlyHint=True`)"*.

§16.2's six arms ran with **no caching middleware installed**. The footgun appears only as prose in
§20.8, citing §16.2 for a run §16.2 does not contain. What *was* measured is §6.1 (**spike:320**:
`after call#2 (key=a): 1 <- CACHE HIT`) and §16.2 (**spike:1407**: `replay same token :
is_error=True ['Confirmation token already used (replay refused).']`).

**Why it matters.** §7.7 states this explicitly as a **standing rule that outlives the mechanism
that produced it** - i.e. it is meant to govern future tools nobody has designed yet. A standing
rule carried past a design freeze on mislabelled provenance is exactly how a false "measured"
becomes permanent.

`[REASONED]` The composition is sound and the rule should stay. *"Derived from two measured
behaviours (§6.1 caching serves from cache; §16.2 a spent token is refused)"* is both honest and
just as persuasive.

## O-5 - §4.5 says the cassette "confirmed" clamping; the cassette explicitly does not distinguish it

**DESIGN L286-291:**

> *"a 1-based server **clamps 0 to 1** - **confirmed** against the one genuine Jobvite `200` in our
> evidence (`JOBVITE-API.md:401`), which is the strongest citation available for this paragraph and
> was previously unused"*

**`JOBVITE-API.md:399`:**

> *"**`start=0` is accepted and returns records**, rather than erroring. That falsifies the
> "1-based and strict" hypothesis, **though it still does not distinguish "0-based" from "1-based
> with clamping"** - see the contract document's pagination section."*

Two defects:

1. **Strength.** The cassette confirms `start=0` **works**. It does not confirm **clamping** - the
   source says so in the same sentence. The design's *decision* (always start at 0) is fully
   supported and correct either way; only the word "confirmed" attached to the clamping *mechanism*
   is overstated.
2. **Citation.** `JOBVITE-API.md:401` is a blank line. The content is at `:399`.

`[REASONED]` Note the shape of this one. The design is congratulating itself for surfacing an unused
strongest citation - a genuine R3/R4 finding about the design under-using its own evidence - and in
doing so read that citation one notch stronger than it reads. The prose at L288-291 is also garbled
(*"and was previously unused and returns the same first page it would have anyway"*), which suggests
an edit landed mid-sentence and was never re-read. Worth a look independent of this audit.

## O-6 - the packaging block called "verbatim" was never resolved as printed

**DESIGN L843** introduces the block with *"Packaging, verbatim, because both lines are
load-bearing"* and prints three dependencies. The spike's verified recipe (§1.3, repeated at §12.1)
is two:

```toml
dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4"]
[tool.uv]
prerelease = "explicit"
```

`mcp 2.1.1` appears in the spike only as a resolve **result** (**spike:110**: `fastmcp 4.0.0b4 |
fastmcp-slim 4.0.0b4 | pydantic 2.13.4  <- STABLE | mcp 2.1.1`), never as an input pin.

**Why it matters.** The paragraph immediately below (**L863-865**) exists because *"A previous
revision claimed in prose that `mcp` was pinned and then omitted it from this block, which was
presented as verbatim. Anyone implementing that block exactly would have reproduced the regression
class the paragraph exists to prevent."* The block was corrected in content and is still labelled
"verbatim" while no longer matching any executed resolve.

`[REASONED]` Adding a hard `==` pin inside a `prerelease = "explicit"` resolve is the single change
in this file most likely to fail to resolve - which is precisely what §1.3 found when `explicit`
alone was tried. The design's own remedy is the right one and would produce the evidence: **L866**,
*"`uv.lock` is committed, CI runs `uv sync --frozen`"*. One `uv lock` closes this.

## O-7 - the `desired + 2` burst rule is a property of FastMCP's client, stated as a property of the protocol

Flagged by the round-4 reviewer as claim 1 of 2. The first pass marked it SUPPORTED. **It is not.**

The arithmetic itself is impeccable and I want to say that plainly before the criticism: four data
points, two eras, all consistent. **spike:913** onward gives `burst_capacity=3: successful tool
calls before refusal = 1 (MCPError at call 2)`, then 5→3 and 10→8; **spike:918** derives *"Exactly
**N-2**"*; and **spike:1058** independently corroborates with `burst_capacity=6` → 4 tool calls on
*both* eras. Nothing in DESIGN L238-239 misreports a number.

**The problem is what the `2` is a property of.** Its provenance, **spike:903-907**:

```
requests the limiter counts for ONE tool call in a fresh session:
   - server/discover
   - tools/call
   - tools/list
   total = 3
```

and **spike:1067** names the mechanism: the era-independence holds *"since both run `server/discover`
+ `tools/list` at"* connect. So the toll is **two non-tool requests issued by FastMCP's own `Client`
during connect** - not by the limiter, not by the protocol, not by the era. Every one of the four
measurements used that client.

A different caller pays a different toll. **spike:198**'s working raw sessionless request is a
single `curl -X POST` carrying `tools/call` with neither `server/discover` nor `tools/list`:

```bash
curl -X POST http://127.0.0.1:8941/mcp \
  -H 'mcp-method: tools/call' -H 'mcp-name: write_thing' \
```

That caller's toll is **zero**, and `desired + 2` over-provisions its bucket by two.

**DESIGN L238** states the rule with no such qualifier: *"**Burst is sized `desired_calls + 2` per
session.**"*

**Why it matters, and the blast radius the reviewer predicted.** ADR-0002 is named at **L261** and
**L1226-1229** as carrying the limiter's constraints, so it inherits this. `[REASONED]` The
practical risk is not a security failure - over-provisioning by two is harmless, and the design's
sizing is *conservative* for a thinner client. The real exposure is the opposite direction: **an MCP
client whose connect sequence is heavier than FastMCP's** - one that also calls `resources/list` and
`prompts/list`, both of which the sessionless `server/discover` at **spike:222-229** advertises
capabilities for - burns more than two, and `desired + 2` then under-provisions and refuses real
tool calls. Nobody has measured any client but FastMCP's.

The fix is a qualifier, not a redesign: state it as measured against FastMCP's client, and note that
a client with a heavier connect sequence needs a larger burst. §4.4 already carries exactly this
kind of honest hedge for concurrency at **L250-253**; this needs the same sentence.

**One further consequence nobody has joined up:** the toll is *per session*, and **spike:2313**
establishes that stdio spawns a fresh process - hence a fresh session and a fresh bucket - **per
connection**. See **X-6**, which this upgrade makes more pointed rather than less.

## O-8 - §7.5's era table collapses a two-axis result onto one axis

Flagged by the round-4 reviewer as claim 2 of 2, and named as the claim already over-generalised
once. The first pass marked it SUPPORTED. **All four cells reproduce; the table is still
overstated**, and in the same direction as the original error.

The design's table, **L646-650**:

| Era | MRTR | `ctx.elicit()` |
|---|---|---|
| sessionless `2026-07-28` | works | raises |
| handshake `2025-11-25` | **raises, every arm including approve** | works |

The spike's matrix for `ctx.elicit()` has **three** columns, not two. **spike:1229-1230**:

```
| HTTP | `legacy` | present | ✅ works |
| HTTP | `legacy` | **absent** | ⛔ `MCPError: Elicitation not supported` |
```

and **spike:1233** repeats it for stdio. The spike states the conclusion as load-bearing at
**spike:1248**: *"Elicitation works only when the **client** both forces `mode="legacy"` **and**
supplies an elicitation handler. Both are client-side choices. **The server cannot compel
either.**"*

So the "works" cell is not an era property. It is `era AND handler`. The design's table presents
availability as determined by the era alone.

**What is NOT wrong here, stated first so this is not read as bigger than it is.** The *mechanism*
is unaffected. §20.4's verified guard refuses on the no-handler arm on both eras, DESIGN **L621**
carries *"no client handler fails closed"* for the sessionless arm, and DESIGN **L797-802** (§8)
carries the full per-era no-handler asymmetry into the test mandate. The design **has** this
information. `create_candidate` is safe.

**Why it still matters.** The table is the artifact a reader lifts out of §7.5 - it is the compact
summary the section builds to, and §13's ADR list will likely reproduce it. A reader taking it at
face value concludes "on handshake, elicitation works", which is exactly the shape of the original
error the reviewer cited: a conditional result read as unconditional. `[REASONED]` The remedy is one
word in the cell - *"works (with a client handler)"* - or a third column. Given that this specific
table is the one the freeze-blocker resolution rests on, spending a word there is cheap insurance
against the next reader generalising it the way the last one did.

## U-1 - "the majority of local users" is a population claim with no evidence

**DESIGN L659-660.** Neither document measures who runs what transport. The spike says the same
thing in the same unevidenced way, so the design did not invent it. `[REASONED]` It is a plausible
inference from "stdio default lands on handshake", but "majority" is a claim about a user
population, not about a protocol. A word like "many" costs nothing and is defensible.

## U-2 - the rate limiter was never run on stdio

**DESIGN L247-248.** See table row 2.6. Every limiter arm ran in-memory or over HTTP. The
conclusion (one caller on stdio, so a global bucket is correct) follows from **spike:2313**'s
per-connection-process finding `[REASONED]`, but no limiter-on-stdio measurement exists and the
design reads as though the whole §4.4 block is measured.

## U-3 - §10's httpx2 verification is not in the spike

**DESIGN L872-885.** See table row 7.4. The claims are correct and sourced from `DECISIONS.md` D17,
while the spike (**spike:81**) asserts the *opposite* characterisation the design is reversing.
A reader following the design's own evidence list (**L11**, which names `FASTMCP-SPIKE-4.md`) lands
on text that contradicts the paragraph. A citation to D17 at **L875** closes it.

---

# STALE - the design contradicting itself

## S-1 - §12 open question 2 describes a runtime probe that §4.5 deleted

- **L1208-1210:** *"**The `start` base.** Now probed at runtime (§4.5), but the probe itself is unverified against a live server."*
- **L281-292** (§4.5): *"**An earlier revision proposed a runtime probe and its logic was inverted.** ... **What we do instead, and it needs no probe.**"*

The probe does not exist. This is the highest-visibility stale line in the document: §12 is what a
reviewer reads to learn what is unresolved, and it advertises a removed mechanism as the current
one.

## S-2 - §12 open question 4 lists a question the evidence closed

- **L1211:** *"**Whether success bodies carry a `status` block at all.** The parser tolerates both."*
- **`JOBVITE-API.md:397`:** *"**A success body DOES carry a `status` block.** ... **This closes the open question**"*
- **DESIGN L761-763** (§8) already treats it as answered: *"whether a success body carries a `status` block. That last point already answers what was an open question."*

The parser tolerating both remains correct engineering. The *question* is not open, and §8 and §12
of the same document now disagree.

## S-3 - §8 mandates tests for the cut confirmation token

- **L785:** *"token replay, expiry, and payload mismatch each refused;"* in the required-cases list.
- **L689-690** (§7.6): *"Cut, after being designed and spiked."*
- **L127** (§2.2): *"**A confirmation-token mechanism was designed, spiked, and then cut.**"*

`[REASONED]` §8's framing is *"Required cases, each failing if its defence is removed"*. The defence
was removed, so the required test cannot be written. Either the list drops the row, or §7.6 is not
final.

## S-4 - §12's closing sentence is contradicted by §10 and by §12's own item 6

Found on a closure pass over the document's self-claims, prompted by the instruction to treat
absence as a finding.

**DESIGN L1219**, closing §12 Open questions:

> *"All are external unknowns. **None is a reasoned-but-unexecuted claim about our own stack.**"*

Two contradictions, one of them inside §12 itself:

1. **§12's own item 6** (**L1214-1218**) is *"Shutdown depends on a uvicorn implementation detail
   (§7.4)"*. That is a claim about **our own stack** - our shutdown path's dependency on a
   third-party library's internals. It is not an external unknown in the sense the other five are
   (a Jobvite credential, a response shape, a host's capability).
2. **§10 L896-899** labels its own capability-drift diff **UNVERIFIED**: *"that this actually
   catches the drift it is meant to catch is **reasoning, not an executed result**"*. That is,
   verbatim, a reasoned-but-unexecuted claim about our own stack. The design says so in one section
   and denies any exist in another.

And beyond those two, a whole class the sentence overlooks: **§4.3's circuit breaker and retry
stack** (row 1.3 - `grep` for `breaker`, `circuit` and `tenacity` across the entire spike returns
nothing), **§4.5's de-duplication seen-set and completeness-versus-`total` check**, and **§2.1's
generated fencing paths**. All designed here, none executed anywhere.

`[REASONED]` The individual sections are honest - §4.3 never claims measurement, and §10 flags
itself. The defect is the **blanket closing assertion**, which is precisely the self-certification
the design's own front matter warns against at **L13-14**: *"stated precisely because a blanket
compliance claim is exactly the kind of self-certification that has already been wrong once on this
project."* The document opens by naming that failure mode and closes by committing it.

The cheap fix is to scope the sentence to the six listed items and drop the universal second clause.

---

# Should have crossed over and did not

Ranked by what the design loses.

## X-1 (highest) - the era check is unswallowable, proven by deliberate construction (§20.7)

The spike built the two worst plausible shapes - including a `swallowing_guard` that, **spike:2187**,
*"wraps its own approval request in"* `try/except Exception` and proceeds to the write if it raises -
and ran both on both eras with no client handler. **spike:2193-2201**, every arm:

```
   naive_mrtr_only     RAISED MCPError: ...
                       rows 0 -> 0   no write
   swallowing_guard    RAISED MCPError: ...
                       rows 0 -> 0   no write
```

And the structural explanation, which is the valuable half, **spike:2214**:

> *"`_ask()` merely *constructs and returns* an object; it does not raise. **The era check fires in
> the framework's result-serialization layer, after the tool has already returned.** So a tool
> physically cannot swallow it with a `try/except` around its own approval request - the exception
> is not raised in a scope the tool controls. That makes the failure mode unswallowable by the
> obvious mistake, which is a much better property than a loud error a careless caller could still
> catch."*

`grep -n "swallow" docs/DESIGN.md` returns **no hits.** §7.5 and §11 both reason about the approval
guard's failure modes without it. This is an executed, structural, *positive* safety property of the
write path - the strongest single thing the design can say about `create_candidate` - and it is
sitting unused in a research file.

`[REASONED]` It carries its own residual, which should cross with it: *"this protects the **first**
leg. A tool that reaches its second leg and mis-validates the answer is still on its own"* - which
is exactly why §7.5's `action AND value` conjunction (**L637-640**) is mandatory. Carried together,
the design gains an executed justification for a rule it currently asserts.

## X-2 - §15.3's fail-open trap in its `ctx.elicit()` shape

§15.3 ran the naive guard against a real client on the legacy era. **spike:1277-1283**:

```
   create_naive:  CREATED via naive guard on DeclinedElicitation  | rows=1
   create_naive:  CREATED via naive guard on CancelledElicitation | rows=2
   create_naive:  CREATED via naive guard on AcceptedElicitation  | rows=3
```

**spike:1287**: *"**Three refusals, three records created**, `is_error=False` on all three so nothing
upstream would flag them either."* Filed upstream as **#4929**.

DESIGN **L637-640** states the `action AND value` conjunction for the **MRTR** arm only. The
handshake arm of the design's own guard uses `ctx.elicit()`, where the trap is *worse*: all three
result types are truthy, so `if result:` permits an outright **decline**, not merely an
accepted-false. §20.4's verified guard handles it with `isinstance(res, AcceptedElicitation) and
res.data is True`, and the design never says why that shape is required.

`[REASONED]` Someone implementing §7.5 from DESIGN alone would get the MRTR arm right and could
easily write the handshake arm wrong. Three measured records is a cheap and vivid sentence.

## X-3 - the upstream filings are cited more weakly than the spike supports

DESIGN cites **#4926** (**L727**) and **#4927** (**L565**) with no note that, **spike:400**,
*"⚠️ **This issue was filed carrying a workaround that §19 later proved unsafe.** It needs a"*
correction comment. Two further filings are absent from the design entirely: **#4929**
(elicitation result types truthy - the trap in X-2) and **#4930** (the SEP-2577 miscitation).

`[REASONED]` #4929 is directly about the design's own approval guard and belongs beside it. #4927's
outstanding correction is also a live task, not just a citation detail.

## X-4 - the SEP miscitation, and the lesson under it

§17.1 records that FastMCP's own source cites **SEP-2577** for the elicitation removal; that
**spike:1497** quotes the official changelog, *"**Deprecated 1.** "Deprecate the **Roots, Sampling,
and Logging** features (SEP-2577).""*; that the real chain is SEP-2575/SEP-2567 with **SEP-2322** as
the replacement; and that *"the miscitation is internally inconsistent within one file, and it is
the proximate cause of two people independently concluding a capability was impossible."*

The design mentions no SEP anywhere. `[REASONED]` It does not need the numbers. It arguably needs the
*shape*: an impossibility conclusion on this project came from a framework's own source comment
being wrong. That is the strongest available argument for §7.5's insistence on **measuring** the
discriminator rather than reading it off documentation - an argument §7.5 currently makes on its own
authority.

## X-5 - the limiter has no era interaction

**spike:1062-1063**, covered under §4.4 above. One clause, currently unused, and it forecloses a
question any reviewer reading §4.4 next to §7.5 would reasonably ask.

## X-6 - the reconnect toll, and its collision with stdio

**spike:918**: *"a client which reconnects frequently pays that toll every time."* Combined with
**spike:2313** (*"stdio spawns a fresh server process per client connection"*), every stdio
connection pays the two-token setup cost against a **fresh** bucket.

`[REASONED]` This is the one place the `desired + 2` sizing rule interacts with the design's default
transport, and neither §4.4 nor §1's per-connection-state footnote joins them up. §4.4 currently
says only *"there is exactly one caller, so the global bucket is correct there"*, which is about
keying, not about sizing.

---

# What I did NOT check

Stated so the next reviewer knows this pass's boundary, and separated from what I could not settle.

**Deliberately out of scope, and a real gap someone should close:**

- **The standards citations.** `readme-standard.md:67/70/83`, `architecture/caching.md:833/841`,
  `rate-limiting.md:361-362`, `ai/agent-guardrails.md:47-49/70`, `ai/tool-calling.md:54`,
  `error-contract.md:44`. I did not open the standards repo. That is a separate audit and a
  warranted one: this pass found a two-line citation error (**O-5**) in the one external citation it
  *did* check.
- **§6 (untrusted content) and §11 (threat model)** were read but not line-audited. Their claims are
  about our own design and standards clauses rather than spike results. The threat-model rows that
  *do* rest on spike results (C4-E, C4-D, C9-T, C2-D) are in the tables above.
- **`JOBVITE-CONTRACT.md`, `STANDARDS.md`, `COMPLIANCE-SPEC.md`** - not opened. §9's hazards and
  §4.2's three error encodings cite Jobvite evidence I checked only where §1.1 and §4.5 pointed.

**Structurally unavailable:**

- **There is no code.** The repo has no `pyproject.toml` and no implementation, so every verdict here
  is document-against-document. **O-6** in particular cannot be settled by reading; it needs one
  `uv lock`.
