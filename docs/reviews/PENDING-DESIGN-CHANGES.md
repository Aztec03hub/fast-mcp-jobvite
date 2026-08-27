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
