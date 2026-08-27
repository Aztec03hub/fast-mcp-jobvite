# Pending design changes, staged

**Why this file exists.** The 4.0.0b4 runtime spike landed while `design-review-r1` was still
reviewing `DESIGN.md`. Editing the document under a running reviewer produces findings against
text that no longer exists, so these changes are staged here and applied in one pass together
with the round-1 findings. **This file is temporary and is deleted when it is applied.**

Source: `docs/research/FASTMCP-SPIKE-4.md`. Every item below was executed, not read.

---

## P1 - SIGTERM does not run lifespan teardown. Retraction of an earlier finding.

The earlier 3.4.7 spike reported that both SIGINT and SIGTERM run lifespan teardown in reverse
order. **That was wrong**, and the agent retracted it: the harness had signalled a PID that was
not the server, the kill printed `No such process`, and that was not treated as invalidating.
Re-run with file-backed evidence and `/proc/<pid>/cmdline` verification:

**Lifespan teardown runs on SIGINT only. It does not run on SIGTERM.** Deterministic 3 of 3, and
an A/B control arm on 3.4.7 gives the same result, so this is longstanding rather than a 4.0
regression.

Root cause is pinned: uvicorn's own shutdown does run under SIGTERM (`Application shutdown
complete` appears), but the FastMCP lifespan teardown is not driven by the ASGI shutdown event.
Under SIGINT the teardown lines appear *after* `Finished server process`, during the
KeyboardInterrupt unwind. SIGTERM kills the process before that unwind happens.

**Why this matters to us specifically:** Docker, Kubernetes and Cloud Run all stop containers
with SIGTERM. Our Jobvite HTTP client would never close on a normal container stop, and the
previous version of the research would have had us design cleanup we believed was running and
was not.

**Changes to make:**
- `__main__.py` installs the mitigation explicitly, one line, with a comment pointing at the
  upstream issue: `signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))`
- Design states the constraint that survives the mitigation: **even mitigated, teardown runs
  after connections are gone**, so nothing that must complete before connections close may live
  in a lifespan teardown. That rules out flush-on-shutdown designs.

---

## P2 - httpx versus httpx2. DECIDED: keep httpx.

4.0.0b4 does not install `httpx` at all. It installs `httpx2` 2.12.0, and httpx2 reaches the
public API surface (`Client.__init__` is typed `auth: httpx2.Auth`). Verified: httpx 0.28.1 and
httpx2 2.12.0 install side by side as separate modules and coexist cleanly.

**Decision: write the Jobvite client against `httpx`, not `httpx2`.** This becomes ADR-0007.

Reasoning, in the order that decided it:

1. **Our entire test strategy rests on transport mocking.** We hold no credential and no sandbox
   exists, so every success-path test substitutes the transport. httpx's mock transport and the
   surrounding tooling are proven; httpx2 is a fork with a much smaller ecosystem and the agent
   flagged that respx-style tooling may not support it. Adopting httpx2 would put the one thing
   we cannot compromise on - testability without credentials - on unproven ground.
2. **It is a public repository meant to be adopted.** Depending on a fork with a small ecosystem
   is a longevity and supply-chain cost that a consumer inherits from us.
3. The "one stack" argument for httpx2 is weaker than it looks. We never catch FastMCP's
   transport exceptions; its internals are not our concern. The two libraries are used by two
   different layers for two different purposes.

**The trap this creates, and the guard against it.** `except httpx.HTTPError` will *never* catch
a FastMCP-raised exception, because FastMCP raises httpx2 types. That is a silent failure mode:
the handler looks correct and never fires. Guard:

- Every `except httpx.*` lives in `services/jobvite_client.py` and nowhere else, so the choice
  stays reversible in one module.
- That module carries a comment stating plainly that FastMCP raises httpx2 types and that
  catching framework transport errors here is a category error.
- A test asserts no `except httpx.` appears outside that module.

---

## P3 - Packaging. Use verbatim; this trap has already been paid for once.

```toml
dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4"]

[tool.uv]
prerelease = "explicit"
```

Both lines are load-bearing:
- `--prerelease=allow` is **global** in uv and pulled in `pydantic` 2.14.0b1, a beta pydantic
  nobody asked for.
- `prerelease = "explicit"` alone **fails to resolve**, because fastmcp pulls `fastmcp-slim` as a
  transitive prerelease and "explicit" only covers directly-named packages.
- Naming `fastmcp-slim` explicitly resolves pydantic to stable 2.13.4. Verified on 3.11 and 3.12.

**Additionally, pin `mcp`.** See P6.

---

## P4 - Sessionless transport has two undocumented requirements

Verified on the wire. `server/discover` returns `supportedVersions: ["2026-07-28"]`; a bad
version returns `-32022` with `data.supported` and `data.requested`. Two requirements the agent
found only by failing first:

1. `_meta` must carry `io.modelcontextprotocol/clientCapabilities` as well as `protocolVersion`.
2. Routing headers `mcp-method` (and `mcp-name` for `tools/call`) must **mirror the body**, or
   the server returns `-32020`.

**Deployment consequence, which belongs in the README:** any reverse proxy, load balancer or WAF
in front of this server must pass `mcp-method`, `mcp-name` and `MCP-Protocol-Version` through
untouched. A proxy that strips unknown headers breaks the server in a way that looks like our bug.

**Dual-era support is real, and was proven rather than assumed.** "Both clients connected" proves
nothing about which era each used, so the agent probed `on_initialize`, which runs on the
handshake and never on sessionless. Result: `mode="auto"` gives `protocol_version=2026-07-28`
with `on_initialize` never firing; `mode="legacy"` fires it and gives `2025-11-25` with the full
session lifecycle. Both eras, one server, one port, simultaneously.

**Caveat to document:** `server/discover` advertises only `2026-07-28` even though the server
demonstrably serves `2025-11-25` clients.

---

## P5 - ResponseLimitingMiddleware is broken on 4.0 too, and it is a regression

Still raises on any tool with a return type annotation. The exclusion in the design stands, and
the bug report gets much stronger: issues #3743 and #3717 report exactly this, and PR #3756
"fix: ResponseLimitingMiddleware no longer breaks outputSchema tools" was **merged to main on
2026-04-05**.

The fix's mechanism is still present in the source. It relied on a non-`None` `meta` making
`to_mcp_result()` return a `CallToolResult` and thereby bypass SDK validation. But mcp 2.x's
`ClientSession.validate_tool_result` (`mcp/client/session.py:1145`) now validates
**unconditionally** whenever an output schema exists. **The middleware's own code never changed;
the behaviour it depended on was removed underneath it by the mcp 1.x to 2.x upgrade.**

---

## P6 - The strategic guardrail this argues for

The genuinely 4.0-specific hazard is not either bug. It is what P5 *represents*: a fix that was
correct in April silently stopped working because a dependency major-versioned underneath it,
with **zero change to the code that broke**. That is the characteristic failure mode of early
adoption on a freshly major-bumped SDK, and it will happen again.

Two guardrails, both cheap:
1. **Pin `mcp` explicitly**, not just `fastmcp`. The break came from the transitive SDK, so
   pinning only the top of the stack does not see it.
2. **CI diffs `fastmcp inspect` output between builds.** The design already emits it; this makes
   it a gate rather than an artifact. A capability change arriving through a dependency bump
   becomes a visible diff in review instead of a runtime surprise.

---

## P7 - Carried forward, verified on 4.0

- `from fastmcp.server.lifespan import lifespan` and `|` composition **survive into 4.0**. The
  agent's original correction to my brief holds on the target too.
- Auth refusals verified on **both** eras. `require_scopes` still hides the tool from
  `tools/list` and reports "Unknown tool" rather than a permission error - README must say so.
- ToolError x masking: all four combinations identical to 3.4.7. Masking stays client-facing
  only; the masked string still reaches the server log.
- Caching verified by side-effect counter with a negative control. Timing and structured logging
  verified.
- `fastmcp.json` still cannot express a required env var - unset variable, server starts, app
  receives the literal `${JOBVITE_API_KEY}`. pydantic-settings owns required config. Confirmed.
- Python 3.11.15 and 3.12.3 give identical results. 3.10 untested; our floor is 3.12 regardless.

---

## P8 - Standing caution to carry into the plan

**Two of the five middlewares tested so far turned out defective.** RateLimitingMiddleware,
ErrorHandlingMiddleware, RetryMiddleware and PingMiddleware remain untested. Assume nothing about
them; spike any before adopting. This is not pessimism - it is the observed base rate on this
codebase at this version.

---

## P9 - D4 simplifies: use the framework rate limiter, with a mandatory `get_client_id`

`RateLimitingMiddleware` **is** usable, so we do not build our own limiter. D4 changes from
"build in-process rate limiting" to "configure the framework's". The ADR is still required,
because we still decline the standard's mandated Redis token bucket, but it gets shorter.

**Two conditions, both non-obvious, both executed:**

1. **The default is not per-client, despite the docstring saying it is.** With
   `global_limit=False` and no `get_client_id`, every caller shares one bucket - the refusal
   literally reads `Rate limit exceeded for client: global`, and the source returns the literal
   string `"global"`. One noisy integrator would rate-limit every other user of a shared
   deployment. Supplying `get_client_id` derived from the authenticated token's `client_id`
   gives real per-client buckets, proven by draining one client's bucket and showing a second
   client's remained full and unaffected.
2. **It counts every MCP request, not just tool calls.** A counting middleware ahead of it
   recorded `server/discover` + `tools/list` + `tools/call` for a single tool call in a fresh
   session. Measured: burst 3 yields 1 tool call, 5 yields 3, 10 yields 8 - exactly N-2. So
   **burst must be sized as `desired_calls + 2` per session**, and a client that reconnects
   frequently pays that toll every time.

The refusal is a **raised `MCPError`**, a JSON-RPC protocol error, not an `is_error` tool result.
It therefore does not flow through our RFC 9457 problem path, and the README must say what a
rate-limit refusal looks like to a caller.

**Interaction with our transports:** on stdio there is no authenticated token and thus no
`client_id`, but there is also exactly one caller, so the global bucket is correct there.
Per-client bucketing matters only on the HTTP transport, which is where tokens exist.

---

## P10 - `ErrorHandlingMiddleware` is excluded. Its default breaks our error contract.

Do not add it. Verified across three arms with identical tools:

- Baseline, no middleware: failures arrive as `is_error=True` tool results. Correct for us.
- **Default `transform_errors=True`: a plain exception becomes a raised `MCPError` "Invalid
  params", and a clean `ToolError` is relabelled "Internal error".** Strictly worse than no
  middleware: a caller's input problem is reported as a server fault.
- It also breaks `raise_on_error=False`, which is our test pattern.
- `transform_errors=False` restores baseline exactly.

If its `error_callback` is ever wanted, construct it with `transform_errors=False` explicitly.

## P11 - `RetryMiddleware` works, with a usage constraint

Verified: three server-side attempts, client sees success. **Retries are silent**, so pair it
with `TimingMiddleware` or a retry is invisible in the logs, and keep `retry_exceptions` narrow.
It must never cover `create_candidate` - a retry after a successful create duplicates a real
candidate in a real ATS, and no sandbox exists in which to learn what that costs.

---

## P12 - A design principle, earned rather than assumed

Of the seven middlewares now exercised, **three ship a default that is wrong for this project**:
`ResponseLimiting` is broken outright, `ErrorHandling`'s default inverts our error contract, and
`RateLimiting`'s default silently shares one bucket across all clients while its docstring says
otherwise.

**On this framework, a middleware's defaults are not a safe starting point.** Every middleware we
adopt is constructed with explicit arguments, and the design states why each argument is set. No
middleware is added on the strength of its documentation alone.

Scoreboard:
- **Safe:** `ResponseCaching`, `Timing`, `StructuredLogging` (`include_payloads=False`), `Retry`
- **Conditional:** `RateLimiting`, only with `get_client_id`
- **Do not use:** `ErrorHandling` (default), `ResponseLimiting` (broken)
- **Untested:** `Ping`, `Dereference`, `ToolInjection`, `Authorization`

---

## P13 - `RetryMiddleware` is DISQUALIFIED. One tool call created four records.

**This supersedes P11, which said Retry was safe. P11 was wrong and is retracted.** The agent
refuted its own earlier verdict on execution.

**It cannot be scoped to exclude a tool.** There is no `tools=`, `included_tools` or
`excluded_tools` parameter - the full constructor is `(max_retries, base_delay, max_delay,
backoff_multiplier, retry_exceptions, logger)` - and it hooks `on_request`, so it applies to
every tool call on the server.

**Executed, in the exact `create_candidate` shape:** side effect lands, then the connection
drops. Verbatim result: `server-side invocations = 4 / ROWS CREATED = 4 / VERDICT: DUPLICATES
CREATED`. **One tool call, four rows.** Against a real ATS with no sandbox, that is four real
duplicate candidates from one network blip, and a recruiter's problem to clean up.

**Narrowing `retry_exceptions` does not save you.** `_should_retry` unwraps one level of
`__cause__`, and FastMCP wraps tool exceptions as `ToolError(...) from original`. So an
`httpx.ConnectError` raised inside `create_candidate` and surfaced as a `ToolError` still matches
and still retries. **`create_candidate` cannot be protected by configuration at all.**

**Consequence for the design:** retries live INSIDE `services/jobvite_client.py`, per endpoint,
where idempotency is known and `create_candidate` is excluded **by construction** rather than by
configuration. This is not a preference. A config-level exclusion for this tool does not exist.

---

## P14 - RFC 9457 problem objects survive every configuration. Make them the primary channel.

Tested across five arms: the problem objects are **completely unaffected** by
`ErrorHandlingMiddleware`, by `transform_errors`, and by `mask_error_details`. They arrive intact
with full structured content.

**The mechanism is the point: they are RETURNED, not raised, so they never enter the error path
at all.** They are the only error shape in the whole matrix that no configuration can distort.

This is a strong independent argument for D6 beyond mere standards compliance: **problem objects
become our primary error channel for expected conditions** - an unknown candidate id, a rejected
credential, a validation failure. Raising is reserved for genuinely exceptional cases.

Two supporting results:
- `mask_error_details` still works underneath the middleware. They compose; masking is not
  defeated.
- `ErrorHandlingMiddleware`'s default still destroys the raised-error shape regardless of
  masking: a clean `ToolError` becomes `MCPError: Internal error: ...` in both mask arms,
  reporting a caller's input mistake as a server fault. Exclusion confirmed.

---

## P15 - Rate limiter: two further constraints for the ADR

Supplements P9. Both new:

- **It is not runtime-reconfigurable.** Mutating `max_requests_per_second` or `burst_capacity`
  has no effect: each bucket is built with the values current at first use and never re-reads
  them. Only `limiters.clear()` applies new settings. **And clearing resets every client's
  quota** - so a config reload is also a quota amnesty, and repeated reloads are a trivial
  bypass. Limits are set at startup; changing them requires a restart.
- **Identical on both protocol eras.** Same server, same limiter, auto and legacy each yielded
  exactly 4 tool calls from a 6-token bucket. No era interaction.

**And the contractual gap:** a trip raises an `MCPError`, a JSON-RPC protocol error, **not** an
`is_error` tool result. So a rate-limit refusal does **not** carry an RFC 9457 problem object. If
limit refusals must be shaped like our other errors, the limiter cannot be what produces them.
The ADR must say this rather than leave it implied.

**Unverified, and it belongs in the ADR's limitations:** every limiter test was sequential and
single-client. Bucket behaviour under simultaneous callers - the case that actually matters in
production - is unverified, and `limiters.clear()` was not tested under load or checked for a
race with in-flight consumption. If the D4 ADR leans on this limiter, one concurrency test is
worth doing before it is final.

## P16 - `PingMiddleware` is not applicable

`ping()` returns "Method not found" on the sessionless era and works on legacy. Coherent:
keep-alive exists to hold a long-lived session open, and sessionless has none. Harmless, but
there is nothing for it to do. Not adopted.

**Running scoreboard: four of the eight middlewares exercised are unusable or need their defaults
overridden.** P12's principle holds and the base rate did not improve with sample size.

---

## P17 - DESIGN-BLOCKING: `create_candidate` is CUT from v1.0

**The HITL control the design assumed is unavailable, and the obvious implementation of it fails
open. v1.0 ships four read tools. The write is deferred.**

### What was found, by execution

**1. Elicitation does not exist on our default era.** `ctx.elicit()` raises, verbatim:

```
ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections.
```

`context.py:1085-1089` shows this is a deliberate era guard raised before touching the wire,
citing SEP-2577's removal of server-initiated requests. On sessionless - our default - elicitation
is unavailable **by design, not by accident**.

**2. The transport fails closed.** On sessionless it raises; on legacy with no client handler it
raises `MCPError: Elicitation not supported`. The destructive counter stayed at zero in every
arm. Good, and worth stating: an unavailable elicitation cannot silently approve.

**3. But the result types fail OPEN, and this is the real hazard.** All three outcome types are
truthy:

| Type | `bool()` |
|---|---|
| `AcceptedElicitation` | `True` |
| `DeclinedElicitation` | `True` |
| `CancelledElicitation` | `True` |

So the obvious guard - `result = await ctx.elicit(...)` then `if result:` - **treats a refusal as
approval.** Run against a real client on the legacy era:

```
--- HUMAN DECLINES ---   create_naive: CREATED | rows=1
--- HUMAN CANCELS ---    create_naive: CREATED | rows=2
--- HUMAN ACCEPTS but answers 'no' --- create_naive: CREATED | rows=3
```

**Three refusals, three records created**, `is_error=False` every time so nothing upstream would
flag it. A human clicking Decline, a human hitting Cancel, and a human explicitly answering "no"
each produced a write, from a guard that reads as correct in review.

The correct form needs **both** checks:
`isinstance(result, AcceptedElicitation) and result.data == <expected>`. Checking the action
alone is insufficient - the third arm shows an *accepted* elicitation carrying the answer "no" is
still truthy and still has `.data`.

**4. The server cannot compel a human to be asked.** On legacy, elicitation depends on the client
implementing a handler; a client without one gets "Elicitation not supported". So approval is not
something this server can guarantee on **any** era.

### The decision, and why it is not an ADR

**v1.0 ships four read tools: `search_candidates`, `get_candidate`, `search_jobs`,
`get_job_feed`. `create_candidate` is deferred.**

It would be easy to write an ADR saying "we ship the write without HITL because HITL is
impossible here". That ADR should not exist. When the safety control a `priority: required`
standard demands turns out to be unavailable, the correct response is **not to ship the dangerous
thing** - not to document why we shipped it anyway. An ADR records a considered deviation; it is
not a waiver for shipping a destructive capability with its mandated guard missing.

The rest of the case was already uncomfortable and this settles it. `POST /api/v2/candidate`:

- **has a success shape nobody has ever observed** - no credential, no sandbox, so the 201 body
  is a hypothesis;
- **cannot be rehearsed anywhere** - both staging hosts fail DNS;
- **cannot be protected from `RetryMiddleware`** by configuration (P13), and one call was
  measured creating four rows;
- **emails a live human candidate** as its side effect;
- **has unknown duplicate semantics** - the `409` behaviour is inferred, not seen.

Shipping a write against a production applicant tracking system under all six of those conditions
is not a close call.

### What ships instead

- The four read tools, which is the useful core: candidate search, candidate fetch, job search,
  job feed.
- `create_candidate` returns in v1.1, gated on two things: a real credential closing the
  contract questions, and a HITL mechanism that actually exists. The README states the omission
  and the reason plainly, so it reads as a decision rather than a gap.

### Kept regardless

The truthiness trap is documented in the design even though we no longer elicit, because it
applies to any future use and it is exactly the kind of defect that survives code review. It also
warrants an upstream report: `DeclinedElicitation` and `CancelledElicitation` being truthy makes
the obvious guard silently unsafe.

---

## P18 - Correction to P17's reasoning. The cut stands; my framing of the env var was wrong.

P17's decision is unchanged - `create_candidate` is cut from v1.0 - but one line of its reasoning
needs correcting, and the correction came from the agent pushing back on my brief.

### Three further findings

**Stdio does not save us.** Stdio also negotiates the sessionless era by default, so elicitation
is unavailable there too, even with a working handler installed. Verbatim:
`STDIO, mode=auto (DEFAULT) | handler ACCEPTS 'yes': ELICIT_RAISED ... unavailable on 2026-07-28
connections | rows=0`. It works over stdio **only** when the client forces `mode="legacy"` **and**
supplies a handler. The local-desktop case, where a human is most likely actually present, is not
an escape hatch under default settings.

**Annotations are transmitted but purely advisory.** All four hints arrive correctly on both
eras. But nothing acts on them: grepping `destructiveHint` across the entire installed package
returns exactly **one** non-test hit, a field-name alias table in `_compat.py:47`. There is no
enforcement path, and a `destructiveHint=True` tool executed immediately with no interruption.
**We set them - honestly and correctly, because a well-behaved host may prompt on them - but the
design must never count them as satisfying the guardrail.**

**Therefore: there is no MCP-native mechanism by which a server can guarantee a human approved a
write.** Both candidates depend on client cooperation, and a control the server cannot guarantee
is not a control.

### The correction I owe

I briefed this work calling the environment-variable gate "a compliance gap" and elicitation "the
obvious fix". The first half is right. **The second half was wrong, and I would have made the
design worse by acting on it.**

The env var has one property neither alternative has: **it is enforced server-side and cannot be
bypassed by a client.** Elicitation and annotations both require the client to opt in - to force
legacy mode, to supply a handler, to honour a hint - and the server can compel none of it.
Swapping the env var for elicitation would have traded *an enforceable weak control* for *an
unenforceable strong-sounding one*. That is a net loss dressed as a compliance improvement.

The gap is real: an env var is deploy-time, not per-invocation, and does not satisfy the
guardrail's HITL requirement. But elicitation was never the fix, and I had assumed it was.

### Why the cut is the right answer anyway

Because the honest conclusion is that **the mandated control cannot be implemented at all**, not
that we picked the wrong implementation. Combined with the five independent reasons in P17 - a
success shape nobody has observed, nowhere to rehearse, no protection from the retry middleware,
an email to a live human as the side effect, and unknown duplicate semantics - deferring is the
only defensible call.

### The path back, so this is a deferral and not an abandonment

A prohibition needs a substitute. The candidate is a **two-call confirmation pattern**: the first
call returns a short-lived token describing exactly what would be written, and the write requires
that token. It keeps the decision on the human's side of the conversation, never requires the
server to initiate a request, and rides on a plain tool result - the one shape that P14 showed no
era or middleware configuration distorts.

**This is a named candidate, not a verified mechanism.** It is being spiked before it goes in the
design, because "we will figure it out in v1.1" is not a path back, and a pattern presented as a
finding without being executed is exactly what this project has been careful to avoid.
