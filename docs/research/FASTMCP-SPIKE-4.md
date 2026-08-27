# FastMCP 4.0.0b4 — Runtime Spike

Target changed by Phil mid-spike: **`fastmcp==4.0.0b4`** and the sessionless **2026-07-28** MCP spec, as deliberate early adopters. This report supersedes the 3.4.7 version of this file entirely.

- **Ran on:** Python **3.11.15** and **3.12.3** (both arms), `fastmcp==4.0.0b4`, `mcp` **2.1.1**, `mcp-types` 2.1.1, `starlette` 1.6.0, `httpx2` **2.12.0**.
- **Control arm:** a second venv at `fastmcp==3.4.7` was built to A/B one finding. Both deleted — see §10.
- **Evidence rule:** every verdict rests on an exit code or a quoted payload.
- **Credentials:** every token here is an obvious placeholder. No realistic-looking secret appears.

## Scoreboard

| # | Claim | Verdict |
|---|---|---|
| 1 | 4.0.0b4 installs; dependency reality | ✅ **VERIFIED** — **httpx is GONE, replaced by httpx2**. Packaging trap found and solved (§1.3) |
| 2 | `fastmcp.server.lifespan` survives 4.0 | ✅ **VERIFIED — it survives.** Import and `\|` composition both work |
| 3 | Sessionless 2026-07-28 + `server/discover` + dual-era | ✅ **VERIFIED** with wire payloads, incl. two **undocumented required headers** (§3.2) |
| 4 | `StaticTokenVerifier` + `require_scopes` refusals | ✅ **VERIFIED** on both protocol eras |
| 5 | `ToolError` vs plain exception × masking | ✅ **VERIFIED**, all four combinations |
| 6a | `ResponseCachingMiddleware` serves from cache | ✅ **VERIFIED** |
| 6b | `TimingMiddleware` / `StructuredLoggingMiddleware` | ✅ **VERIFIED** |
| 6c | `ResponseLimitingMiddleware` truncates safely | ⛔ **REFUTED — and it is a REGRESSION of a fix that shipped in April.** Bug report drafted (§8.1) |
| 7 | HTTP transport, default path, both client styles | ✅ **VERIFIED**, default path `/mcp` |
| 8 | `fastmcp.json` cannot express a required env var | ✅ **VERIFIED BY BEHAVIOUR**, fails silently |
| 9 | Lifespan teardown runs on shutdown | ⛔ **REFUTED on SIGTERM — resources leak on every container stop.** Not 4.0-specific. Bug report drafted (§8.2). **This retracts a claim from my own earlier spike** |
| 10 | Python floor | ✅ **VERIFIED** on **3.11.15 and 3.12.3** — identical results on both (§10.1) |

---

## ⛔ Retraction of my own earlier finding — read this one first

My previous (3.4.7) spike stated:

> "Both signals run both teardowns in reverse order."

**That was wrong.** It was an artifact of my test harness signalling a PID that was not the server process (the `kill` in that harness printed `No such process`, which I failed to treat as invalidating). I rebuilt the test with file-backed evidence, a verified `/proc/<pid>/cmdline`, and the venv interpreter invoked directly with no `uv run` wrapper. The corrected result:

**On SIGTERM the lifespan teardown does not run. On SIGINT it does.** This holds on **both 4.0.0b4 and 3.4.7** — so it is longstanding behaviour, not a 4.0 regression, and it is a production hazard because **Docker, Kubernetes and Cloud Run all stop containers with SIGTERM.** Full evidence, root cause and a verified one-line mitigation in §9.

I am flagging this prominently because the earlier version of this file would have led us to design cleanup we believed was running and was not.

---

## 1. Install and dependency reality

### 1.1 It installs — ✅

```
uv add "fastmcp==4.0.0b4" --prerelease=allow
ADD_EXIT=0
```

Resolved:

```
fastmcp        4.0.0b4
fastmcp-slim   4.0.0b4
mcp            2.1.1
mcp-types      2.1.1
pydantic       2.14.0b1      <- see 1.3
starlette      1.6.0
uvicorn        0.52.4
httpx2         2.12.0
httpx          NOT INSTALLED
```

Declared floor from PyPI: `requires_python: >=3.10`; `pydantic[email]>=2.12.0`; `mcp<3.0.0,>=2.0.0`; `starlette>=1.0.1`; `httpx2>=2.5.0`.

### 1.2 🚩 The httpx → httpx2 swap is REAL — this affects our Jobvite client

`httpx` is **not installed at all**; `httpx2` 2.12.0 is. It also reaches the **public API surface** — `Client.__init__` is typed `auth: 'httpx2.Auth | Literal["oauth"] | str | None'`.

Tested coexistence, because our Jobvite client is planned around `httpx`:

```
httpx 0.28.1 AND httpx2 2.12.0 -> coexist OK
same module? False
```

They install side by side as **separate modules**. So we have two options, and this is a design decision, not a detail:

- **(a) Write the Jobvite client against `httpx2`.** One HTTP stack, no duplication, matches FastMCP internals. Cost: `httpx2` is a fork with a much smaller ecosystem, and `respx`-style test tooling may not support it.
- **(b) Keep `httpx` for our client.** Familiar, well-supported, and it demonstrably coexists. Cost: two HTTP libraries in the image, and `except httpx.HTTPError` will **never catch** an exception raised by FastMCP internals — a silent trap if we ever wrap a FastMCP call.

Either way, **keep every `except httpx.*` in one module** so the choice is reversible.

### 1.3 🚩 Packaging trap — and the verified recipe that avoids it

`--prerelease=allow` is **global** in uv, so it dragged in **`pydantic 2.14.0b1`**, a *beta pydantic* we never asked for. Constraining it to `prerelease = "explicit"` alone **fails to resolve**:

```
hint: `fastmcp-slim` was requested with a pre-release marker (e.g.,
fastmcp-slim==4.0.0b4), but pre-releases weren't enabled
```

— because `fastmcp` pulls `fastmcp-slim` as a *transitive* prerelease, and `explicit` only covers directly-named packages.

**Verified working recipe** — name `fastmcp-slim` as a direct dependency too:

```toml
[project]
dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4"]

[tool.uv]
prerelease = "explicit"
```

Resolves to:

```
fastmcp 4.0.0b4 | fastmcp-slim 4.0.0b4 | pydantic 2.13.4  <- STABLE | mcp 2.1.1
```

**Recommend this verbatim for our `pyproject.toml`.** It keeps prereleases scoped to the two packages we are deliberately early-adopting, instead of opening the whole graph.

---

## 2. Does `fastmcp.server.lifespan` survive 4.0? — ✅ YES

This was the open question. Answer:

```
OK    fastmcp.server.lifespan -> ['ComposedLifespan', 'ContextManagerLifespan', 'Lifespan',
                                  'LifespanContextManagerFn', 'LifespanFn', 'lifespan', ...]
OK    fastmcp.utilities.lifespan -> ['combine_lifespans', ...]
FAIL  fastmcp.lifespan -> ModuleNotFoundError
```

The import path and the `@lifespan` decorator both survive into 4.0.0b4, and `|` composition works (§9). **My original correction to your brief holds on 4.0 as well** — do not "fix" that import.

(There is also a lower-level `fastmcp.utilities.lifespan.combine_lifespans`; `fastmcp.server.lifespan` is the public one.)

### 2.1 Other 4.0 API changes confirmed by signature

Removed from `FastMCP.__init__`: `sampling_handler`, `sampling_handler_behavior`. Removed from `@mcp.tool`: `exclude_args`. Added: `resource_security` (defaults to `ResourceSecurity(reject_path_traversal=True, reject_absolute_paths=True, reject_null_bytes=True, ...)`), `request_state_security`, `cache_ttl`, `cache_scope`. All import paths we depend on survived:

```
OK  fastmcp.server.auth.StaticTokenVerifier / .require_scopes
OK  fastmcp.exceptions.ToolError
OK  fastmcp.server.middleware.{caching,logging,timing,response_limiting}
```

---

## 3. Sessionless 2026-07-28 protocol

### 3.1 It is live and it is the default

`server/discover`, verbatim:

```json
{"jsonrpc":"2.0","id":2,"result":{
  "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"spike-auth","version":"4.0.0b4"}},
  "ttlMs":0,"cacheScope":"private",
  "supportedVersions":["2026-07-28"],
  "capabilities":{"logging":{},"prompts":{"listChanged":false},
                  "resources":{"subscribe":false,"listChanged":false},
                  "tools":{"listChanged":false},
                  "extensions":{"io.modelcontextprotocol/ui":{}}},
  "resultType":"complete"}}
```

Sessionless `tools/list` (no session ID anywhere):

```json
{"jsonrpc":"2.0","id":1,"result":{"cacheScope":"private","resultType":"complete",
 "tools":[{"description":"Unguarded tool","name":"ping",
           "outputSchema":{"properties":{"result":{"type":"string"}},"required":["result"],
                           "type":"object","x-fastmcp-wrap-result":true},"title":"Ping"}, ...]}}
```

Bad version → **`-32022`**, with the machine-readable negotiation data the spec promises:

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32022,"message":"Unsupported protocol version",
 "data":{"supported":["2026-07-28"],"requested":"1999-01-01"}}}
```

**Verdict: ✅ VERIFIED.**

### 3.2 🚩 Two required headers that are not in the spec text I read

Getting a sessionless request to work took two failures first. Both are worth knowing before anyone writes a raw HTTP client or debugs a proxy:

**(a) `_meta` needs `clientCapabilities`, not just the protocol version:**
```json
{"error":{"code":-32602,"message":"params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities"}}
```

**(b) Routing headers must mirror the body — `mcp-method`, and `mcp-name` for `tools/call`:**
```json
{"error":{"code":-32020,"message":"mcp-method header does not match the request body's method"}}
{"error":{"code":-32020,"message":"mcp-name header does not match the request body's 'name' parameter"}}
```

A working sessionless `tools/call`:

```bash
curl -X POST http://127.0.0.1:8941/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H 'Authorization: Bearer TOKEN-WITH-SCOPE-PLACEHOLDER' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'mcp-method: tools/call' -H 'mcp-name: write_thing' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
        "name":"write_thing","arguments":{},
        "_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28",
                 "io.modelcontextprotocol/clientCapabilities":{}}}}'
```

These headers exist so intermediaries can route without parsing the body — sensible, but it means **any reverse proxy or WAF in front of us must pass `mcp-method`, `mcp-name` and `MCP-Protocol-Version` through untouched.** One for the deployment checklist.

### 3.3 Dual-era backward compatibility — ✅ VERIFIED, not quoted

You asked for this executed rather than cited. I used a middleware probe, because "both clients connected" proves nothing about *which era* they used. `Middleware.on_initialize` is documented to run on the handshake era and never on sessionless, so it is a clean discriminator:

```python
class EraProbe(Middleware):
    async def on_initialize(self, context, call_next):
        print("ERA-PROBE: on_initialize FIRED (handshake era)", flush=True)
        return await call_next(context)
    async def on_call_tool(self, context, call_next):
        pv = context.fastmcp_context.request_context.protocol_version
        print(f"ERA-PROBE: on_call_tool protocol_version={pv}", flush=True)
        return await call_next(context)
```

Server-side output for `Client(mode="auto")` then `Client(mode="legacy")`, verbatim:

```
ERA-PROBE: on_call_tool protocol_version=2026-07-28      <- auto: sessionless, on_initialize NEVER fired
ERA-PROBE: on_initialize FIRED (handshake era)
ERA-PROBE: on_call_tool protocol_version=2025-11-25      <- legacy: handshake era
```

Corroborated by the HTTP access log — the sessionless client made three plain `POST`s; the legacy client ran a full session lifecycle:

```
POST /mcp 200 | POST /mcp 202 Accepted | GET /mcp 200 | POST /mcp 200 | DELETE /mcp 200
```

**Both eras work against one server, on one port, simultaneously.** `ConnectMode` is `Literal['legacy','auto']`, default `'auto'`.

⚠️ One caveat: `server/discover` advertises **`supportedVersions:["2026-07-28"]` only**, despite the server demonstrably serving 2025-11-25 clients. A client that trusts `server/discover` to enumerate everything would wrongly conclude the handshake era is unavailable. Harmless for us; worth knowing.

---

## 4. Auth refusals

Server: `StaticTokenVerifier` with two placeholder tokens, one tool guarded by `require_scopes("jobvite:write")`.

**No token:**
```
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
content-length: 0
```

**Bad token:**
```
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer error="invalid_token", error_description="Authentication failed. The provided bearer token is invalid, expired, or no longer recognized by the server. ..."

{"error": "invalid_token", "error_description": "Authentication failed. ..."}
```

**Good token** — reaches the protocol layer (a `400`, not a `401`), i.e. auth passed.

**Scope refusal, sessionless, limited token:**
```
tools visible: ['ping']
```
```json
{"jsonrpc":"2.0","id":2,"result":{"content":[{"text":"Unknown tool: 'write_thing'","type":"text"}],
 "isError":true,"resultType":"complete"}}
```
Control, same call with the full token:
```json
{"content":[{"text":"wrote","type":"text"}],"isError":false,"structuredContent":{"result":"wrote"}}
```

**Verdict: ✅ VERIFIED on both eras.**

⚠️ Same behavioural note as before, and it survives into 4.0: `require_scopes` **removes the tool from `tools/list`** and reports **`Unknown tool`**, not a permission error. Capability hiding is automatic; the cost is that nobody — including us, in a support ticket — can distinguish "not permitted" from "does not exist". Worth a README line.

---

## 5. ToolError vs plain exception × masking

```
########## mask_error_details=False ##########
--- raise_tool_error ---
  is_error : True
  content  : ['TOOLERROR-DETAIL: candidate_id must match ^[A-Z0-9]+$']
--- raise_plain ---
  is_error : True
  content  : ["Error calling tool 'raise_plain': PLAIN-DETAIL: internal string 12345"]

########## mask_error_details=True ##########
--- raise_tool_error ---
  is_error : True
  content  : ['TOOLERROR-DETAIL: candidate_id must match ^[A-Z0-9]+$']
--- raise_plain ---
  is_error : True
  content  : ["Error calling tool 'raise_plain'"]
```

**Verdict: ✅ VERIFIED**, identical to 3.4.7. `is_error` true in all four; the `ToolError` message is byte-identical masked and unmasked; the plain exception's detail is stripped.

⚠️ Unchanged caveat: masking is **client-facing only**. The full traceback, including the masked string, still reaches the **server log**. Never interpolate a Jobvite credential into an exception message.

---

## 6. Middleware

### 6.1 Caching — ✅ VERIFIED

Opt-in via `call_tool_settings`. Proof by side-effect counter, with a negative control:

```
after call#1 (key=a): 1
after call#2 (key=a): 1 <- CACHE HIT
after call#3 (key=b): 2 <- control MISS
```

### 6.2 Timing and structured logging — ✅ VERIFIED

```
INFO  {"event": "request_start", "method": "tools/call", "source": "client"}
INFO  Request tools/call completed in 2.50ms                       timing.py:47
INFO  {"event": "request_success", "method": "tools/call", "source": "client", "duration_ms": 2.94}
```

Also visible: `server/discover` appears in the log even for the **in-memory** client — confirming the in-memory `Client` uses the sessionless era too.

⚠️ `include_payloads=True` logs tool arguments verbatim, which for Jobvite means candidate data. Leave it at the default `False`.

### 6.3 ⛔ ResponseLimitingMiddleware — REFUTED, and it is a regression

The middleware fires:

```
WARNING  Tool 'huge_annotated' response exceeds size limit: 10163 bytes > 200 bytes,
         truncating                                   response_limiting.py:137
```

and the call then **fails at the client**:

```
huge_annotated:   RAISED RuntimeError: Tool huge_annotated has an output schema but did not return structured content
huge_unannotated: len=150 is_error=False truncated=True
```

Root cause, precisely. The middleware returns a truncated result with **no `structured_content`** while the tool's advertised `outputSchema` remains. Its 4.0 source still relies on the old escape hatch:

```python
# Preserve original meta, falling back to {} when absent. Having
# meta set ensures to_mcp_result() returns a CallToolResult, which
# bypasses MCP SDK outputSchema validation ...
return ToolResult(content=[TextContent(type="text", text=truncated)],
                  meta=meta if meta is not None else {})
```

That escape hatch **no longer exists in `mcp` 2.x**, whose validator is unconditional (`mcp/client/session.py:1145`):

```python
if output_schema is not None:
    if result.structured_content is None:
        raise RuntimeError(f"Tool {name} has an output schema but did not return structured content")
```

**This was already fixed once.** Issue [#3743](https://github.com/PrefectHQ/fastmcp/issues/3743) and [#3717](https://github.com/PrefectHQ/fastmcp/issues/3717) report exactly this; PR [#3756](https://github.com/PrefectHQ/fastmcp/pull/3756) *"fix: ResponseLimitingMiddleware no longer breaks outputSchema tools"* was **merged to `main` on 2026-04-05**. The fix's mechanism is still in the source — but the `mcp` 1.x → 2.x upgrade removed the behaviour it depended on. So this is a **regression via a dependency upgrade**, which is why it slipped through: the middleware's own code never changed.

**Recommendation unchanged: do not use `ResponseLimitingMiddleware`.** Cap sizes inside the tool by paging the Jobvite result and returning "showing 50 of 1,240, use `offset`" — better for the model than a truncated blob anyway. Bug report drafted at §8.1.

---

## 7. Transport, path, client styles

- **In-memory `Client(mcp)`** — ✅ used throughout §§5–6.
- **Network `Client(url)`** — ✅ verified in both `auto` and `legacy` modes (§3.3).
- **Default path** — probed with no `path=` argument:

```
path=/     -> 404
path=/mcp  -> 400     <- reached protocol layer
path=/mcp/ -> 307     <- redirect
```

Banner confirms: `Starting MCP server 'dp' with transport 'http' on http://127.0.0.1:8948/mcp`. **Default is `/mcp`**, unchanged from 3.4.7. `run_http_async` keeps `host`, `port`, `path`, `allowed_hosts`, `allowed_origins`, `host_origin_protection`, `stateless`.

---

## 8. Drafted bug reports

Canonical repo confirmed before citing anything: **`PrefectHQ/fastmcp`**. `api.github.com/repos/jlowin/fastmcp` returns **301**, and PyPI `project_urls.Repository` is `https://github.com/PrefectHQ/fastmcp`. Your caution was warranted.

**FILED upstream** by the team lead on 2026-08-27:

- **[#4926](https://github.com/PrefectHQ/fastmcp/issues/4926)** — `ResponseLimitingMiddleware` regression (§8.1)
- **[#4927](https://github.com/PrefectHQ/fastmcp/issues/4927)** — lifespan teardown not running on SIGTERM (§8.2)

Zero open duplicates existed for either at filing time. One correction to my own draft, established during
filing: I had listed **#4118** ("terminate active streamable-HTTP transports before lifespan shutdown") as
"related but distinct" without checking its timing. It merged **2026-05-10**, *before* 4.0.0b4 was published
on 2026-08-26 — so **that fix is already present in the version tested and the teardown gap survives it**.
That is a stronger statement than "related", and it is now in the filed issue.

### 8.1 Draft — regression

> **Title:** `ResponseLimitingMiddleware` again breaks tools with an `outputSchema` on 4.0.0b4 (regression of #3743 / PR #3756)
>
> **Environment:** `fastmcp==4.0.0b4`, `mcp==2.1.1`, `mcp-types==2.1.1`, Python 3.11.15, Linux.
>
> **Repro:**
> ```python
> import asyncio
> from fastmcp import FastMCP, Client
> from fastmcp.server.middleware.response_limiting import ResponseLimitingMiddleware
>
> mcp = FastMCP(name="repro")
> mcp.add_middleware(ResponseLimitingMiddleware(max_size=200))
>
> @mcp.tool
> def big() -> str:            # return annotation -> FastMCP generates an outputSchema
>     return "X" * 5000
>
> async def main():
>     async with Client(mcp) as c:
>         await c.call_tool("big", {})
>
> asyncio.run(main())
> ```
>
> **Expected:** the response is truncated and returned, per PR #3756.
>
> **Actual:** `RuntimeError: Tool big has an output schema but did not return structured content`, raised from `mcp/client/session.py:1145`. The middleware logs `Tool 'big' response exceeds size limit: 10163 bytes > 200 bytes, truncating` first, so truncation runs and then the result is rejected.
>
> **Analysis:** `_truncate_to_result` returns a `ToolResult` with no `structured_content`, relying on the comment in `response_limiting.py` that a non-`None` `meta` makes `to_mcp_result()` return a `CallToolResult` and thereby "bypasses MCP SDK outputSchema validation". In `mcp` 2.x, `ClientSession.validate_tool_result` validates unconditionally whenever the tool has an output schema, so that bypass no longer exists. The middleware source is unchanged since the fix; the regression arrived with the `mcp` 1.x → 2.x upgrade.
>
> **Suggested fix:** on truncation, either emit a schema-conformant `structured_content` (e.g. re-wrap the truncated text under the schema's `result` key when `x-fastmcp-wrap-result` is set), or strip/override the advertised `outputSchema` for the truncated response, or skip truncation for tools with an output schema and log that it was skipped.
>
> **Workaround:** scope the middleware with `tools=[...]` to tools without return annotations. This avoids the crash only by leaving annotated tools unlimited.

### 8.2 Draft — lifespan teardown on SIGTERM

> **Title:** Lifespan teardown does not run on SIGTERM (only SIGINT), leaking resources on container shutdown
>
> **Environment:** reproduced on `fastmcp==4.0.0b4` (`mcp` 2.1.1) **and** `fastmcp==3.4.7` (`mcp` 1.29.1), Python 3.11.15, Linux, HTTP transport. Not version-specific.
>
> **Repro:**
> ```python
> import pathlib
> from fastmcp import FastMCP
> from fastmcp.server.lifespan import lifespan
>
> EV = pathlib.Path("events.txt")
> def say(m):
>     with EV.open("a") as f: f.write(m + "\n")
>
> @lifespan
> async def a(server):
>     say("A-startup"); yield {"db": 1}; say("A-shutdown")
>
> mcp = FastMCP(name="repro", lifespan=a)
>
> @mcp.tool
> def ping() -> str: return "pong"
>
> if __name__ == "__main__":
>     mcp.run(transport="http", host="127.0.0.1", port=8944)
> ```
> Start it, then `kill -TERM <pid>`. Compare with `kill -INT <pid>`.
>
> **Expected:** `A-shutdown` is written for both signals.
>
> **Actual:** SIGTERM writes only `A-startup` (3 of 3 runs). SIGINT writes `A-startup` then `A-shutdown`. Verified with the venv interpreter invoked directly (no `uv run` wrapper) and the PID confirmed via `/proc/<pid>/cmdline`.
>
> **Analysis:** uvicorn's own shutdown sequence runs in **both** cases — the log shows `Shutting down` / `Waiting for application shutdown.` / `Application shutdown complete.` / `Finished server process` under SIGTERM too. But the FastMCP lifespan teardown is not driven by the ASGI lifespan shutdown event: under SIGINT the teardown lines appear **after** `Finished server process`, i.e. during the Python-level unwind that `KeyboardInterrupt` triggers. SIGTERM terminates the process before that unwind, so teardown never runs.
>
> **Impact:** Docker, Kubernetes and Cloud Run all stop containers with SIGTERM. Any lifespan that closes an HTTP client, flushes a cache, or releases a DB connection silently does not run on normal shutdown.
>
> **Workaround (verified):** `signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))` before `mcp.run(...)` restores teardown under SIGTERM.
>
> **Note:** searched the tracker for an existing report and found none matching (`lifespan+SIGTERM` → 0 results). Related but distinct: #4118, #3480.


### 8.3 Draft — elicitation result types are all truthy (DX / safety trap)

Requested by the team lead for filing. Framed as DX/documentation rather than a defect, because the
types are defensible as dataclass-like results.

> **Title:** `DeclinedElicitation` and `CancelledElicitation` are truthy, so the obvious approval guard silently permits refused actions
>
> **Environment:** `fastmcp==4.0.0b4`, `mcp==2.1.1`, Python 3.12.3, Linux. Also present on 3.4.7.
>
> **What happens:** `ctx.elicit()` returns one of `AcceptedElicitation`, `DeclinedElicitation`,
> `CancelledElicitation`. All three are truthy:
> ```
> Accepted   bool()=True
> Declined   bool()=True
> Cancelled  bool()=True
> ```
> So the natural guard around a destructive action permits it when the user refuses:
> ```python
> result = await ctx.elicit("Create candidate?", response_type=str)
> if result:            # True for Declined AND Cancelled
>     create()
> ```
>
> **Repro** — a tool with a naive guard and a strict guard side by side, against a client whose
> handler declines, cancels, and finally accepts-with-a-negative-answer:
> ```
> --- HUMAN DECLINES ---
>    create_naive:  CREATED via naive guard on DeclinedElicitation  | rows=1
>    create_strict: BLOCKED on DeclinedElicitation                  | rows=1
> --- HUMAN CANCELS ---
>    create_naive:  CREATED via naive guard on CancelledElicitation | rows=2
>    create_strict: BLOCKED on CancelledElicitation                 | rows=2
> --- HUMAN ACCEPTS but answers 'no' ---
>    create_naive:  CREATED via naive guard on AcceptedElicitation  | rows=3
>    create_strict: BLOCKED on AcceptedElicitation                  | rows=3
> ```
> Three refusals, three writes, `is_error=False` on all three.
>
> **Expected:** the obvious guard should not permit a refused action, or the requirement to use
> `isinstance(...)` should be impossible to miss.
>
> **Why it matters:** elicitation's most natural use is confirming a destructive operation, which is
> exactly the case where a silently-permissive guard is worst. The unsafe form reads as correct in
> review.
>
> **Suggested fixes, in preference order:**
> 1. Define `__bool__` on `DeclinedElicitation`/`CancelledElicitation` returning `False`. Cheap,
>    makes the obvious guard correct, though it is a behaviour change for anyone relying on
>    truthiness.
> 2. Failing that, put the `isinstance` requirement in the elicitation docs with an explicit
>    "this is not enough: `if result:`" counter-example.
> 3. Consider a convenience such as `result.accepted` returning a real boolean.
>
> **Note:** the same trap exists on the MRTR / `InputRequiredResult` path, where the caller must
> check both the action **and** the answer value — an accepted elicitation carrying a negative answer
> is still an acceptance.


### 8.4 Draft — `context.py` cites SEP-2577 for a change SEP-2577 did not make

> **Title:** `ctx.elicit()` era-guard comments cite SEP-2577, which deprecated Roots/Sampling/Logging, not the server-initiated request mechanism
>
> **Environment:** `fastmcp==4.0.0b4`. Also present in 3.4.7's equivalent path.
>
> **What happens:** `fastmcp/server/context.py` explains the 2026-07-28 elicitation guard as:
> ```python
> # Foreground push path: server-initiated elicitation needs a back-channel,
> # which the 2026-07-28 era removed (SEP-2577).
> ```
> and similarly at line 947: "The 2026-07-28 era (SEP-2577) has no back-channel for server-initiated…".
>
> **Why it is wrong:** per the official 2026-07-28 changelog, SEP-2577 deprecates the **Roots,
> Sampling and Logging** features. The removal of the back-channel comes from statelessness
> (SEP-2575 / SEP-2567), and the sanctioned replacement for server-initiated requests is **MRTR,
> SEP-2322** — which the *same file* cites correctly at lines 214, 359, 381 and 402.
>
> **Impact:** the runtime error message is accurate and well-judged ("elicitation via
> *server-initiated requests* is unavailable"), but a reader who follows the neighbouring comment to
> SEP-2577 finds a deprecation notice for three unrelated features and no mention of elicitation. In
> our case this contributed to two people independently concluding that human-in-the-loop approval
> was impossible on 2026-07-28 connections, when `InputRequiredResult` — which FastMCP implements —
> is exactly the supported path.
>
> **Suggested fix:** cite SEP-2322 (and optionally SEP-2575) in those two comments, and consider
> adding a one-line pointer in `_ELICIT_MODERN_ERROR` itself, e.g. "…unavailable on 2026-07-28
> connections; return an `InputRequiredResult` instead (SEP-2322)." That turns a dead end into a
> signpost at the exact moment a developer hits it.

---

## 9. Lifespan — composition ✅, teardown ⛔ on SIGTERM

### 9.1 Composition — ✅ VERIFIED

```
LIFESPAN A-startup (db)
LIFESPAN B-startup (cache)
TOOL -> lifespan_context={'db': 'DB-HANDLE', 'cache': 'CACHE-HANDLE'}
LIFESPAN B-shutdown (cache)
LIFESPAN A-shutdown (db)
EXIT=0
```

Left enters first, exit is strict reverse order, dicts shallow-merged. Works on 4.0.

### 9.2 ⛔ Teardown under real signals — REFUTED for SIGTERM

File-backed evidence (flush-proof), venv python invoked directly, PID verified:

```
########## SIGTERM ##########          ########## SIGINT ##########
  EXITED cleanly                         EXITED cleanly
    A-startup                              A-startup
    B-startup                              B-startup
                                           B-shutdown
                                           A-shutdown
```

SIGTERM repeated **3/3, deterministic**. A/B control arm on **fastmcp 3.4.7** with the identical harness gives the **same result** — so this is longstanding, not a 4.0 regression:

```
CONTROL ARM fastmcp 3.4.7
########## 3.4.7 SIGTERM ##########    ########## 3.4.7 SIGINT ##########
    A-startup                              A-startup
    B-startup                              B-startup
                                           B-shutdown
                                           A-shutdown
```

Ruled out as causes: the `uv run` wrapper (reproduced with the venv interpreter directly), output buffering (evidence written to a file with an explicit flush), and a wrong PID (`/proc/<pid>/cmdline` checked).

Root cause and impact are in the draft at §8.2. **Mitigation verified:**

```python
import signal
signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
```
```
sending SIGTERM to 113548
EXITED cleanly
--- events with mitigation ---
  A-startup
  B-startup
  B-shutdown
  A-shutdown
```

⚠️ Even with the mitigation, teardown runs **after** `Finished server process` — it is not part of graceful shutdown, and in-flight requests are already gone. Do not put anything in a lifespan teardown that must complete before connections close.

---

## 10. `fastmcp.json` and required env vars

`fastmcp inspect` auto-detects the file and exits 0:

```
INFO     Using configuration from fastmcp.json     cli.py:67
Server
  Name:         spike-config
  Version:      4.0.0b4
Environment
  FastMCP:      4.0.0b4
  MCP:          2.1.1
INSPECT_EXIT=0
```

Behavioural test of `deployment.env` with `"JOBVITE_API_KEY": "${JOBVITE_API_KEY}"`:

```
########## UNSET ##########
  TOOL -> JOBVITE_API_KEY=${JOBVITE_API_KEY} MODE=spike
  bind-conflicts: 0
########## SET ##########
  TOOL -> JOBVITE_API_KEY=PLACEHOLDER-KEY-VALUE MODE=spike
  bind-conflicts: 0
```

**Verdict: ✅ VERIFIED, and the failure is silent.** With the variable unset the server **starts normally** and the application receives the **literal string `${JOBVITE_API_KEY}`**. No warning, no non-zero exit. A missing credential surfaces later as a confusing Jobvite 401.

(The schema confirms why: `deployment` has exactly `['args','cwd','env','host','log_level','path','port','transport']`, and `env` is a flat `dict[str,str]` with no `required`/`secret` slot.)

**Your design call is confirmed: pydantic-settings owns required-config validation.** Verified substitute:

```
--- UNSET ---
  FAILED FAST: ValidationError
  1 validation error for Settings
  jobvite_api_key
    Field required [type=missing, input_value={}, input_type=dict]
--- SET ---
  OK
```

---

---

## 10.1 Python version matrix — 3.11 and 3.12

Both arms built with the §1.3 prerelease recipe, which held on both:

```
PY 3.11.15 | fastmcp 4.0.0b4 | mcp 2.1.1 | pydantic 2.13.4 | httpx2 2.12.0 | starlette 1.6.0
PY 3.12.3  | fastmcp 4.0.0b4 | mcp 2.1.1 | pydantic 2.13.4 | httpx2 2.12.0 | starlette 1.6.0
```

Every discriminating check re-run on **3.12.3**, verbatim:

```
mask=False te: is_error=True content=['TOOLERROR-DETAIL: placeholder rule']
mask=False pe: is_error=True content=["Error calling tool 'pe': PLAIN-DETAIL: internal 12345"]
mask=True  te: is_error=True content=['TOOLERROR-DETAIL: placeholder rule']
mask=True  pe: is_error=True content=["Error calling tool 'pe'"]
cache: after1=1 after2=1 (HIT) control_diff_arg=2
limiter: RAISED RuntimeError: Tool big has an output schema but did not return structured content
lifespan tool -> ['a', 'b']
lifespan events: ['A-start', 'B-start', 'B-stop', 'A-stop']
```

Signals on 3.12.3 — the SIGTERM gap reproduces identically:

```
SIGTERM: exited   events: A-startup
SIGINT:  exited   events: A-startup A-shutdown
```

Sessionless protocol on 3.12.3:

```
supportedVersions: ['2026-07-28']
{"jsonrpc":"2.0","id":2,"error":{"code":-32022,"message":"Unsupported protocol version",
 "data":{"supported":["2026-07-28"],"requested":"1999-01-01"}}}
```

**Verdict: ✅ no behavioural difference between 3.11 and 3.12.** Both defects (§6.3 limiter, §9.2 SIGTERM) reproduce on both, so neither is interpreter-specific — which strengthens both bug reports.

## 11. Cleanup

`/tmp/fastmcp-spike` and the `/tmp/fastmcp-ab` control arm **have both been deleted**, along with all spike processes and ports. Nothing was written into the repo but this file, and no spike dependency reached the repo — the repo still has no `pyproject.toml`.

---

## 12. Verified snippet library

All executed on 4.0.0b4.

### 12.1 pyproject — the prerelease recipe (§1.3)

```toml
[project]
requires-python = ">=3.11"
dependencies = ["fastmcp==4.0.0b4", "fastmcp-slim==4.0.0b4"]

[tool.uv]
prerelease = "explicit"
```

Naming `fastmcp-slim` explicitly is what keeps `pydantic` on a **stable** release.

### 12.2 Server, auth, and the SIGTERM mitigation

```python
import json, os, signal
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.auth import require_scopes
from fastmcp.server.lifespan import lifespan

verifier = StaticTokenVerifier(tokens=json.loads(os.environ["MCP_TOKENS"]))

@lifespan
async def http_lifespan(server):
    client = make_jobvite_client()
    yield {"jobvite": client}
    await client.aclose()

mcp = FastMCP(
    name="jobvite",
    auth=verifier,
    mask_error_details=True,
    lifespan=http_lifespan,
)

@mcp.tool(description="Read-only")
def get_candidate(candidate_id: str) -> dict: ...

@mcp.tool(description="Mutating", auth=require_scopes("jobvite:write"))
def update_candidate(candidate_id: str) -> dict: ...

def main() -> None:
    s = get_settings()                                            # fails fast (12.5)
    signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))  # REQUIRED - see 9.2
    if s.mcp_transport == "http":
        mcp.run(transport="http", host=s.mcp_host, port=s.mcp_port, path="/mcp")
    else:
        mcp.run()                                                 # stdio for local clients
```

### 12.3 Errors

```python
from fastmcp.exceptions import ToolError

if not CANDIDATE_ID_RE.match(candidate_id):
    raise ToolError(f"candidate_id must match {CANDIDATE_ID_RE.pattern}")   # reaches client
resp.raise_for_status()                                                     # masked generic
```

### 12.4 Middleware — the safe set

```python
mcp.add_middleware(StructuredLoggingMiddleware())      # include_payloads=False
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(ResponseCachingMiddleware(
    call_tool_settings={"enabled": True, "ttl": 300, "included_tools": ["list_jobs"]}))
# DO NOT add ResponseLimitingMiddleware - see 6.3. Page inside the tool instead.
```

### 12.5 Required config

```python
class Settings(BaseSettings):
    jobvite_api_key: str = Field(description="Required")   # no default -> fails fast
    mcp_transport: str = "stdio"
```

### 12.6 Testing

```python
@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c

async def test_bad_id(client):
    r = await client.call_tool("get_candidate", {"candidate_id": "!!"}, raise_on_error=False)
    assert r.is_error and "must match" in r.content[0].text
```

---

## Is 4.0.0b4 usable for our shape of server?

**Yes, with two conditions**, and I want to be plain rather than reassuring.

Nothing we need is missing or broken *by* 4.0. The lifespan API survived, auth and scopes work on both eras, the error contract is unchanged, the sessionless protocol genuinely works and the dual-era claim is real. The prerelease packaging trap has a verified solution.

The two conditions:

1. **The SIGTERM teardown gap must be mitigated explicitly** (§9.2). It is not a 4.0 bug — 3.4.7 has it too — but it would silently defeat our cleanup design on every container stop.
2. **The `httpx` → `httpx2` decision has to be made now, not in implementation** (§1.2), because it shapes the Jobvite client's error handling and test tooling.

The one genuinely 4.0-specific hazard is what the `ResponseLimitingMiddleware` regression *represents*: a fix that was correct in April silently stopped working because a dependency major-versioned underneath it, with no change to the middleware's own code. That is the characteristic failure mode of adopting a beta on top of a freshly major-bumped SDK, and it argues for pinning `mcp` as well as `fastmcp`, and for our CI diffing `fastmcp inspect` output between builds.

---

---

## 13. The previously-untested middleware (D4 input)

Run on Python 3.12.3, `fastmcp==4.0.0b4`. You asked for `RateLimitingMiddleware` specifically because D4 has us doing in-process rate limiting.

### 13.1 ⚠️ RateLimitingMiddleware — works, but the DEFAULT IS NOT PER-CLIENT

```
RateLimitingMiddleware(max_requests_per_second: float = 10.0,
                       burst_capacity: int | None = None,
                       get_client_id: Callable[[MiddlewareContext], str] | ... | None = None,
                       global_limit: bool = False)
```

The docstring says `global_limit: If True, apply limit globally; if False, per-client`. **But with `global_limit=False` and no `get_client_id`, every caller shares one bucket.** The refusal message says so:

```
call 1: RAISED MCPError: Rate limit exceeded for client: global
```

Source confirms — `_get_client_identifier` returns the literal string `"global"` when no `get_client_id` is supplied (`fastmcp/server/middleware/rate_limiting.py:156`). So **the default is a server-wide limit wearing a per-client label.** One noisy integrator would rate-limit every other Jobvite user.

**Second finding: it counts every MCP request, not just tool calls.** A counting middleware placed ahead of it recorded, for a single tool call in a fresh session:

```
requests the limiter counts for ONE tool call in a fresh session:
   - server/discover
   - tools/call
   - tools/list
   total = 3
```

Which means session setup burns tokens before any work happens. Quantified across three bucket sizes:

```
burst_capacity=3:  successful tool calls before refusal = 1  (MCPError at call 2)
burst_capacity=5:  successful tool calls before refusal = 3  (MCPError at call 4)
burst_capacity=10: successful tool calls before refusal = 8  (MCPError at call 9)
```

Exactly **N-2** — the bucket starts full, and `server/discover` + `tools/list` consume two tokens per new session. **Size the burst as `desired_tool_calls + 2` per session**, and note that a client which reconnects frequently pays that toll every time.

**Per-client keying works when you supply it.** Keyed on the authenticated token's `client_id`:

```python
def client_id_from_auth(context) -> str:
    from fastmcp.server.dependencies import get_access_token
    tok = get_access_token()
    return tok.client_id if tok else "anonymous"

mcp.add_middleware(RateLimitingMiddleware(
    max_requests_per_second=2.0, burst_capacity=12,
    get_client_id=client_id_from_auth))
```

```
=== per-client buckets keyed on authenticated client_id ===
  alpha (drains its own bucket): successful tool calls = 6 (None)
  beta  (should be UNAFFECTED by alpha): successful tool calls = 6 (None)
  alpha again (should still be empty): successful tool calls = 2 (MCPError at call 3)
```

Beta was unaffected by alpha's traffic, and alpha on return had only partial refill. **Separate buckets confirmed.**

**Verdict: ✅ USABLE for D4, with a mandatory `get_client_id`.** Do not ship the default. Also note the refusal is a raised `MCPError`, i.e. a JSON-RPC protocol error, not an `is_error=True` tool result — clients see a transport-level failure, not a tool failure.

*(Methodology note: my first per-client run failed with `MCPError: Rate limit exceeded for client: alpha` raised during `initialize`. That was my test being too tight — negotiation traffic drained a 6-token bucket across three sequential connections — not a defect. Re-run with `burst_capacity=12` and it isolated cleanly. Recording it because the failure looked like a bug and was not.)*

### 13.2 ⛔ ErrorHandlingMiddleware — the DEFAULT BREAKS our error contract

Three arms, identical tools, verbatim:

```
--- NO middleware (baseline) ---
   boom: is_error=True content=["Error calling tool 'boom': PLAIN-DETAIL placeholder"]
   terr: is_error=True content=['TOOLERROR-DETAIL placeholder']
--- ErrorHandlingMiddleware(transform_errors=True)  [DEFAULT] ---
   boom: RAISED MCPError: Invalid params: Error calling tool 'boom': PLAIN-DETAIL placeholder
   terr: RAISED MCPError: Internal error: TOOLERROR-DETAIL placeholder
--- ErrorHandlingMiddleware(transform_errors=False) ---
   boom: is_error=True content=["Error calling tool 'boom': PLAIN-DETAIL placeholder"]
   terr: is_error=True content=['TOOLERROR-DETAIL placeholder']
```

With the **default** `transform_errors=True`:

1. A tool failure stops being a tool result and becomes a **raised JSON-RPC `MCPError`**. That undoes the entire `ToolError` contract we standardised on in §5.
2. A clean, actionable `ToolError` is **relabelled "Internal error"** — strictly worse than no middleware, because the message now reads like a server fault rather than the caller's input problem.
3. **`raise_on_error=False` stops working**, since there is no longer a tool result to inspect. That breaks the test pattern in §12.6.

**Verdict: ⛔ do NOT add `ErrorHandlingMiddleware`.** If it is ever wanted for its `error_callback` hook, it must be constructed with `transform_errors=False`.

### 13.3 ⛔ RetryMiddleware — mechanically works, but UNSAFE for us and CANNOT be scoped

It does retry, as documented:

```
--- RetryMiddleware ---
   flaky: is_error=False content=['ok after 3 attempts'] server-side attempts=3
```

**But it cannot be excluded from a single tool, and that is disqualifying.** Full constructor
`[FROM SOURCE]`:

```
RetryMiddleware(max_retries=3, base_delay=1.0, max_delay=60.0,
                backoff_multiplier=2.0,
                retry_exceptions=(ConnectionError, TimeoutError),
                logger=None)
```

There is **no `tools=`, `included_tools` or `excluded_tools` parameter**, and it hooks `on_request`,
so it applies to every tool call on the server. Demonstrated against a non-idempotent tool whose
side effect lands *before* the transient failure — the shape of a real `create_candidate` that
writes the row and then loses the connection:

```
=== Does RetryMiddleware retry a non-idempotent tool? ===
   -> NO tools=/included_tools/excluded_tools parameter exists.
   result: is_error=True content=["Error calling tool 'create_candidate': transient failure AFTER the write landed"]
   server-side invocations of create_candidate = 4
   ROWS CREATED = 4 -> ['PLACEHOLDER-CANDIDATE#1', 'PLACEHOLDER-CANDIDATE#2',
                        'PLACEHOLDER-CANDIDATE#3', 'PLACEHOLDER-CANDIDATE#4']
   VERDICT: DUPLICATES CREATED
```

**One tool call produced four candidate records.** In a real ATS with no sandbox, that is four real
duplicates from a single transient network blip.

Worse, `_should_retry` also unwraps one level of `__cause__` `[FROM SOURCE]`:

```python
if isinstance(error, self.retry_exceptions):
    return True
cause = error.__cause__
return cause is not None and isinstance(cause, self.retry_exceptions)
```

FastMCP wraps tool exceptions as `ToolError(...) from original`, so **an httpx `ConnectError`
raised inside `create_candidate` and surfaced as a `ToolError` still triggers the retry.** Narrowing
`retry_exceptions` does not protect a non-idempotent write; it only changes which transient causes
trip it.

**Verdict: ⛔ DO NOT USE.** If we want retries, they belong **inside the Jobvite client**, per-endpoint,
where idempotency is known and `create_candidate` can be excluded by construction.

### 13.4 Middleware scoreboard after this spike

| Middleware | Verdict |
|---|---|
| `ResponseCachingMiddleware` | ✅ safe (opt-in per tool) |
| `TimingMiddleware` | ✅ safe |
| `StructuredLoggingMiddleware` | ✅ safe with `include_payloads=False` |
| `RetryMiddleware` | ⛔ **cannot exclude a tool** — retries every call, duplicated a non-idempotent write 4x (§13.3) |
| `RateLimitingMiddleware` | ⚠️ usable **only** with an explicit `get_client_id` |
| `ErrorHandlingMiddleware` | ⛔ default breaks the error contract; needs `transform_errors=False` |
| `ResponseLimitingMiddleware` | ⛔ broken (§6.3) |
| `PingMiddleware` | ➖ inert on our default era — the `ping` RPC does not exist in 2026-07-28 (§14.4) |
| `DereferenceMiddleware`, `ToolInjectionMiddleware`, `AuthorizationMiddleware` | ❓ still untested |

**Four of the eight exercised are unusable or need their defaults overridden.** That is the durable lesson: on this framework, a middleware's defaults are not a safe starting point — each one needs its own spike before adoption.


---

## 14. Middleware, round 2 — the D4 questions

Run on Python 3.12.3, `fastmcp==4.0.0b4`. §13 established the basics; this section answers the
specific decision questions. Where it contradicts §13, §13 has been **rewritten in place** — see
§13.3, whose verdict is now REFUTED.

### 14.1 RateLimitingMiddleware — the D4 verdict

**Is the framework's limiter usable instead of building one?** ✅ **Yes, with three constraints.**
Since Jobvite publishes no limits and returns no rate-limit headers, anything we use is purely
client-side and configuration-driven, which is exactly what this middleware is.

**(a) Per-client requires an explicit `get_client_id`** (§13.1). The default keys every caller to the
literal string `"global"`.

**(b) Identical on both protocol eras** — same server, same limiter, `burst_capacity=6`:

```
=== same limiter, both protocol eras ===
   mode=auto  : tool calls before refusal = 4 (MCPError: Rate limit exceeded for client: global)
   mode=legacy: tool calls before refusal = 4 (MCPError: Rate limit exceeded for client: global)
```

Both eras give **4 tool calls from a 6-token bucket** — consistent with the N-2 protocol-overhead
finding in §13.1, and it holds on both, since both run `server/discover` + `tools/list` at
connect. **✅ No era interaction.**

**(c) ⚠️ NOT runtime-reconfigurable by attribute assignment.** The public attributes are
`max_requests_per_second`, `burst_capacity`, `get_client_id`, `global_limit`, `limiters` — but
mutating them does nothing to buckets that already exist:

```
   burst=4 initial: 2 calls (MCPError)
   mutating rl.burst_capacity=20 and rl.max_requests_per_second=50 at runtime
   after mutating attrs: 1 calls (MCPError)          <- NO EFFECT
   existing limiter objects: 1 -> ['global']
   clearing rl.limiters to force rebuild
   after clearing limiters: 12 calls (None)          <- new settings applied
```

Each `TokenBucketRateLimiter` is constructed with the values current at first use and never
re-reads them. A live config change requires `rl.limiters.clear()`, **which resets every client's
quota** — i.e. a config reload is also a quota amnesty, and repeated reloads would be a trivial
bypass. If runtime tuning matters, set limits at startup and restart to change them, or treat
`limiters.clear()` as a deliberate, rate-limited admin action.

**What it returns when it trips:** a **raised `MCPError`**, i.e. a JSON-RPC protocol error, not an
`is_error=True` tool result:

```
MCPError: Rate limit exceeded for client: global
```

Consequence for our contract: a rate-limit refusal does **not** arrive as a tool error and will not
carry an RFC 9457 problem object. A client sees a transport-level failure. If we want limit
refusals to be contractually shaped like our other errors, the limiter cannot be the thing that
produces them.

**Verdict: ✅ USABLE for D4** — the ADR can say the framework limiter replaces a custom one,
provided it documents the explicit `get_client_id`, the `calls + 2` burst sizing, the
restart-to-reconfigure constraint, and that refusals are protocol errors rather than problem objects.

### 14.2 ErrorHandlingMiddleware × `mask_error_details` × RFC 9457

Five arms, verbatim. `problem` returns an RFC 9457 object as a **normal** return value:

```
--- mask=False, NO middleware (baseline) ---
   terr: is_error=True content=['TOOLERROR-DETAIL placeholder']
   plain: is_error=True content=["Error calling tool 'plain': PLAIN-DETAIL placeholder"]
   problem: is_error=False structured={'type': '...', 'title': 'Candidate not found', 'status': 404, ...}
--- mask=True,  NO middleware (baseline) ---
   terr: is_error=True content=['TOOLERROR-DETAIL placeholder']
   plain: is_error=True content=["Error calling tool 'plain'"]
   problem: is_error=False structured={'type': '...', 'title': 'Candidate not found', 'status': 404, ...}
--- mask=False, ErrorHandling(default transform_errors=True) ---
   terr: RAISED MCPError: Internal error: TOOLERROR-DETAIL placeholder
   plain: RAISED MCPError: Invalid params: Error calling tool 'plain': PLAIN-DETAIL placeholder
   problem: is_error=False structured={'type': '...', 'title': 'Candidate not found', 'status': 404, ...}
--- mask=True,  ErrorHandling(default transform_errors=True) ---
   terr: RAISED MCPError: Internal error: TOOLERROR-DETAIL placeholder
   plain: RAISED MCPError: Invalid params: Error calling tool 'plain'
   problem: is_error=False structured={'type': '...', 'title': 'Candidate not found', 'status': 404, ...}
--- mask=True,  ErrorHandling(transform_errors=False) ---
   terr: is_error=True content=['TOOLERROR-DETAIL placeholder']
   plain: is_error=True content=["Error calling tool 'plain'"]
   problem: is_error=False structured={'type': '...', 'title': 'Candidate not found', 'status': 404, ...}
```

Three answers to your contractual questions:

1. **RFC 9457 problem objects are completely unaffected** — by the middleware, by `transform_errors`,
   and by `mask_error_details`, in all five arms. ✅ Because they are **returned, not raised**, they
   never enter the error path at all. **This is a strong argument for making problem objects our
   primary error channel**: they are the only shape in this matrix that no configuration can distort.
2. **`mask_error_details` still works underneath the middleware** — the plain exception's detail is
   stripped under `mask=True` even with `transform_errors=True`. The two compose; masking is not
   defeated. ✅
3. **But the default still destroys the raised-error shape**, and does so regardless of masking:
   a clean `ToolError` becomes `MCPError: Internal error: ...` in both mask arms. A caller's input
   mistake is reported as a server fault.

**Verdict: ⛔ do not add it.** If ever needed for `error_callback`, construct with
`transform_errors=False`, which restores baseline exactly.

### 14.3 RetryMiddleware — see §13.3 (REFUTED)

Answered directly: **it cannot be scoped to exclude a tool.** No `tools=`/`excluded_tools` parameter
exists, it hooks `on_request`, and a non-idempotent tool produced **four rows from one call**.
`_should_retry` also unwraps `__cause__`, so an httpx `ConnectError` surfaced as a `ToolError` still
retries. `create_candidate` cannot be protected by configuration. Full evidence in §13.3.

### 14.4 PingMiddleware — inert on our default era

```
PingMiddleware.__init__: (self, interval_ms: int = 30000)
hooks it overrides: ['on_message']
   mode=auto  : tool OK (ok) | ping() -> MCPError: Method not found
   mode=legacy: tool OK (ok) | ping() -> True
```

The `ping` RPC **does not exist in the sessionless 2026-07-28 era** — it returns `Method not found` —
while it works on the handshake era. That is coherent: keep-alive exists to hold a long-lived
session open, and sessionless has no session to hold. Installing the middleware is harmless (tools
still work in both modes), but on our default era it has nothing to do.

**Verdict: ➖ NOT APPLICABLE for our default configuration.** Only relevant if we ever serve
long-lived handshake-era clients over a connection-dropping intermediary.

### 14.5 Recommendations arising

1. **D4 ADR: adopt `RateLimitingMiddleware`**, do not build a custom limiter. Document the four
   constraints in §14.1.
2. **Do not adopt `RetryMiddleware`.** Put retries in the Jobvite client, per-endpoint, with
   `create_candidate` excluded by construction rather than by config.
3. **Do not adopt `ErrorHandlingMiddleware`.**
4. **`PingMiddleware`: no.**
5. **Prefer RFC 9457 problem objects as returns over raised errors** wherever the condition is
   expected. §14.2 shows returned objects are the only error shape immune to middleware and
   masking configuration.


---

## 15. Elicitation, human-in-the-loop, and tool annotations

Run on Python 3.12.3, `fastmcp==4.0.0b4`. This section exists because `ai/agent-guardrails.md:70`
requires destructive operations to be default-deny **and** human-in-the-loop, **failing closed**, and
`create_candidate` writes a real record to a real ATS and can email a live human.

> ⚠️ **CORRECTED BY §17.** This section's finding about `ctx.elicit()` is accurate, but the
> **conclusion I drew from it was wrong.** Elicitation *is* available on the sessionless era — via
> the MRTR / `InputRequiredResult` pattern, not via `ctx.elicit()`. §15.5's claim that "no
> MCP-native mechanism lets the server guarantee a human approved a write" is **retracted**; see
> §17 for the executed evidence. The fail-open finding in §15.3 stands and still matters.

**Headline: `ctx.elicit()` cannot serve as our HITL control, and the obvious implementation of it
fails OPEN.** Both findings below are independent and both stand. What does *not* follow — and what
I wrongly concluded — is that HITL is impossible on our era. See §17.

### 15.1 ⛔ `ctx.elicit()` is unavailable on the sessionless era — VERIFIED

```
ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections.
```

This is a deliberate era guard, raised **before hitting the wire** (`fastmcp/server/context.py`
~line 1085) `[FROM SOURCE]`:

```python
# which the 2026-07-28 era removed (SEP-2577). Raise a clear era-aware
# error before hitting the wire instead of the SDK's opaque "Method not
# found". Handshake-era behavior is unchanged.
if self._is_modern_protocol():
    raise ToolError(_ELICIT_MODERN_ERROR)
```

Sessionless is **our default era**, so elicitation is unavailable by design in our default
configuration. Note also that `response_type` is now a **required** parameter of `ctx.elicit()`
`[FROM SOURCE]`, confirming the documented 4.0 change.

### 15.2 Availability matrix — VERIFIED across eras and transports

| Transport | Client mode | Handler | Result |
|---|---|---|---|
| HTTP | `auto` (default) | any | ⛔ `ToolError: ... unavailable on 2026-07-28 connections.` |
| HTTP | `legacy` | present | ✅ works |
| HTTP | `legacy` | **absent** | ⛔ `MCPError: Elicitation not supported` |
| **stdio** | `auto` (default) | present | ⛔ `ToolError: ... unavailable on 2026-07-28 connections.` |
| **stdio** | `legacy` | present | ✅ works |
| **stdio** | `legacy` | absent | ⛔ `MCPError: Elicitation not supported` |

Verbatim, stdio:

```
--- STDIO, mode=auto (DEFAULT) ---
   handler ACCEPTS 'yes': ELICIT_RAISED ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections. | rows=0
   handler DECLINES:      ELICIT_RAISED ToolError: ... | rows=0
   NO handler at all:     ELICIT_RAISED ToolError: ... | rows=0
--- STDIO, mode=legacy (forced handshake era) ---
   handler ACCEPTS 'yes': CREATED | rows=1
   handler DECLINES:      BLOCKED on DeclinedElicitation | rows=0
   NO handler at all:     ELICIT_RAISED MCPError: Elicitation not supported | rows=0
```

**This is the load-bearing conclusion.** Elicitation works only when the **client** both forces
`mode="legacy"` *and* supplies an elicitation handler. Both are client-side choices. **The server
cannot compel either.** Even on stdio — the local-desktop case where a human is most likely
actually present — the default negotiation is sessionless and elicitation is unavailable.

**Verdict: ⛔ REFUTED as a HITL mechanism.** A control the server cannot guarantee is not a control.

### 15.3 ⛔ Fails CLOSED at the transport, but the RESULT TYPES fail OPEN — VERIFIED

Two separate questions, two different answers.

**(a) Transport unavailability fails CLOSED. ✅** In every unavailable arm above the destructive
counter stayed at `rows=0`. `ctx.elicit()` *raises*; it does not return a falsy sentinel. The only
way to convert this into a fail-open is to wrap it in a `try/except` that swallows — which is
exactly why `create_candidate` must never catch broadly around its own approval check.

**(b) The result types fail OPEN. ⛔** All three outcomes are **truthy**:

```
Accepted   bool()=True   repr=AcceptedElicitation(action='accept', data={'ok': True})
Declined   bool()=True   repr=DeclinedElicitation(action='decline')
Cancelled  bool()=True   repr=CancelledElicitation(action='cancel')
```

So the natural-looking guard treats a refusal as approval. Constructed deliberately and run against
a real client on the legacy era, with a naive and a strict guard side by side:

```
--- HUMAN DECLINES ---
   create_naive:  CREATED via naive guard on DeclinedElicitation  | rows=1
   create_strict: BLOCKED on DeclinedElicitation                  | rows=1
--- HUMAN CANCELS ---
   create_naive:  CREATED via naive guard on CancelledElicitation | rows=2
   create_strict: BLOCKED on CancelledElicitation                 | rows=2
--- HUMAN ACCEPTS but answers 'no' ---
   create_naive:  CREATED via naive guard on AcceptedElicitation  | rows=3
   create_strict: BLOCKED on AcceptedElicitation                  | rows=3
```

**Three refusals, three records created**, `is_error=False` on all three so nothing upstream would
flag them either. In a real ATS that is three real candidates and three emails to live humans,
produced by a guard that reads as correct in review.

The naive form:

```python
result = await ctx.elicit("Create candidate?", response_type=str)
if result:                     # ⛔ TRUE for Declined AND Cancelled
    create()
```

The correct form needs **both** an action check and a value check — the third arm shows an
*accepted* elicitation carrying the answer `"no"` is still truthy and still has `.data`:

```python
from fastmcp.server.elicitation import AcceptedElicitation

result = await ctx.elicit("Create candidate?", response_type=str)   # let it RAISE if unavailable
if not (isinstance(result, AcceptedElicitation) and result.data == "yes"):
    raise ToolError("Not approved by a human; refusing.")
create()
```

### 15.4 Tool annotations are transmitted, and are PURELY ADVISORY — VERIFIED

Both eras, verbatim:

```
--- tools/list, mode=auto ---
   create_candidate: annotations=title='Create Candidate' read_only_hint=False destructive_hint=True idempotent_hint=False open_world_hint=True
   get_candidate:    annotations=title=None read_only_hint=True destructive_hint=False idempotent_hint=True open_world_hint=True
   calling the destructiveHint=True tool: is_error=False -> created PLACEHOLDER
--- tools/list, mode=legacy ---
   (identical annotations)
   calling the destructiveHint=True tool: is_error=False -> created PLACEHOLDER
```

- ✅ **Transmitted correctly on both eras**, wire-name `destructiveHint` mapping to `destructive_hint`.
- ⛔ **Nothing in FastMCP acts on them.** A grep for `destructiveHint|destructive_hint` across the
  entire installed package returns exactly **one** non-test hit — a field-name alias table in
  `fastmcp/_compat.py:47`. There is no enforcement path, no prompt, no gate.
- The tool annotated `destructiveHint=True` executed immediately, `is_error=False`, with no
  interruption of any kind.

**Verdict: ✅ transmitted / ⛔ advisory only.** Annotations are a *request* to the client, not a
control. **We cannot claim the guardrail is satisfied by annotations.** They should still be set —
correctly and honestly, since a well-behaved host may prompt on them — but the design must not
count them as the HITL control.

### 15.5 What this means for the compliance gap — ⚠️ SUPERSEDED BY §17

The reasoning below was written before I tested the MRTR path, and its conclusion is **retracted**.
It is kept only because the first two points remain true and are load-bearing for §17.

1. **`ctx.elicit()` is not available in our default configuration** and cannot be made available by
   anything the server does. (§15.1, §15.2) — **still true.**
2. **Annotations are advisory** and enforce nothing. (§15.4) — **still true.**
3. ~~Therefore no MCP-native mechanism lets the server guarantee a human approved a write.~~
   **WRONG.** This did not follow. `ctx.elicit()` is one route to elicitation, not the only one.
   The 2026-07-28 spec carries elicitation over the **Multi Round-Trip Requests** pattern, and
   FastMCP 4.0 implements it. **§17 demonstrates HITL working on the sessionless era.**
4. ~~The env-var gate is a weaker control that actually holds.~~ Superseded — we no longer have to
   choose between an enforceable weak control and an unenforceable strong one.

### 15.6 Not a bug report

Nothing in §15 is a FastMCP defect, so I have drafted no issue. The era guard is deliberate and
well-implemented; the annotations are advisory by MCP's own design. The truthiness of
`DeclinedElicitation` is arguably an ergonomic trap worth raising upstream, but it is defensible —
the objects are dataclass-like results, not booleans — and I would rather not file noise against a
project that has just accepted two real reports from us. **Flagging it for your call rather than
deciding unilaterally.**


---

## 16. The confirmation-token HITL pattern — SPIKED

§15.5 named a two-call confirmation-token pattern as the only substitute I could see for elicitation,
and flagged it explicitly as **not verified**. A prohibition needs a working substitute, so I built
and attacked it. This section upgrades it from a named candidate to a **tested one**.

⚠️ **Scope: this is OUR pattern, not a FastMCP feature.** Nothing here is a framework finding. It
uses only plain tool calls and plain returns, which is precisely why it survives both eras.

### 16.1 Shape

Two tools. The first is read-only and mints a short-lived HMAC token **bound to the exact payload**;
the second refuses to write without a matching one.

```python
@mcp.tool(description="Step 1: preview the write. Returns what WOULD happen plus a token.",
          annotations={"readOnlyHint": True, "destructiveHint": False})
def preview_create_candidate(name: str, email: str) -> dict:
    payload = {"name": name, "email": email}
    return {"willCreate": payload,
            "warning": "This will create a real ATS record and may email this person.",
            "confirmationToken": mint(payload),
            "expiresInSeconds": TTL}

@mcp.tool(description="Step 2: perform the write. REQUIRES a token from preview.",
          annotations={"destructiveHint": True, "idempotentHint": False})
def create_candidate(name: str, email: str, confirmation_token: str) -> dict:
    check({"name": name, "email": email}, confirmation_token)   # raises ToolError on any failure
    ROWS.append((name, email))
    return {"created": True, "rows": len(ROWS)}
```

`mint`/`check` are ~20 lines of `hmac` + `secrets` over a server-side secret, carrying an expiry, a
nonce, and a used-token set.

### 16.2 Attack arms — all six, both eras, verbatim

```
===== mode=auto (sessionless 2026-07-28) =====
  no token          : is_error=True ['Malformed confirmation token.']
  forged token      : is_error=True ['Confirmation token does not match this request.']
  token/arg mismatch: is_error=True ['Confirmation token does not match this request.']
  correct token     : is_error=False structured={'created': True, 'rows': 1}
  replay same token : is_error=True ['Confirmation token already used (replay refused).']
  expired token     : is_error=True ['Confirmation token expired; re-confirm.']

===== mode=legacy (handshake 2025-11-25) =====
  no token          : is_error=True ['Malformed confirmation token.']
  forged token      : is_error=True ['Confirmation token does not match this request.']
  token/arg mismatch: is_error=True ['Confirmation token does not match this request.']
  correct token     : is_error=False structured={'created': True, 'rows': 2}
  replay same token : is_error=True ['Confirmation token already used (replay refused).']
  expired token     : is_error=True ['Confirmation token expired; re-confirm.']
```

**12 calls, 10 refusals, 2 writes** — and the server's own row counter went `1` then `2`, incrementing
**only** on the two correct-token calls and on no refusal arm. Each failure mode produces a
*distinct* message, so the refusals are not one blanket rejection wearing six labels.

The **token/arg mismatch** arm is the one that matters most: a token minted for
`{"name": "A", ...}` was replayed against `{"name": "MALLORY", ...}` and refused, because the HMAC
covers the payload. A confirmation the human gave for one write cannot be spent on a different one.

**Verdict: ✅ VERIFIED on both eras.** It needs no server-initiated request, so the sessionless
restriction in §15.1 does not apply, and it rides on plain tool results — the one shape §14.2 showed
no era or middleware configuration distorts.

### 16.3 ⚠️ Positive-control failure I hit first, and why it is recorded

My first run refused **every** arm including the happy path:

```
  correct token     : is_error=True structured=None rows=0
```

**A guard that refuses everything is not a guard, and its refusals prove nothing.** The cause was my
own bug: I joined the token as `f"{exp}.{nonce}.{sig}"`, and `exp` is a float whose repr contains a
`.`, so `token.split(".")` returned four parts and every token parsed as malformed. Switching the
separator to `:` fixed it.

Recording this because the broken run *looked like a total success* — six refusals, zero writes, a
perfect security result — and I would have shipped a pattern whose only demonstrated behaviour was
rejecting everything. The positive control is what distinguishes "correctly refuses attacks" from
"is simply broken".

### 16.4 What this pattern does and does not give us

**Does:**
- Server-side enforcement. The write is impossible without a token the server minted; no client
  cooperation required, unlike elicitation (§15.2) and annotations (§15.4).
- Per-invocation, not deploy-time — the gap you identified in the env-var gate.
- Payload binding, replay refusal, and expiry, all demonstrated above.
- Works identically on both eras and needs nothing from the transport.

**Does NOT:**
- ⛔ **Prove a human was involved.** This is the honest limit. It forces a *deliberate two-step*,
  and the preview returns text stating what will happen — but an autonomous agent can call
  `preview_` and then `create_` with no human in the loop at all. It enforces **confirmation**, not
  **human** confirmation. Against `agent-guardrails.md:70`'s human-in-the-loop requirement this is a
  partial answer, and the design should say so plainly rather than claim more.
- Survive a client that hides the preview's warning text from the human.

**My read, your decision:** this is strictly stronger than the env-var gate (per-invocation,
payload-bound) and strictly stronger than elicitation *in enforceability* (the server cannot be
bypassed), while being strictly weaker than elicitation *in intent* (it cannot prove a human
answered). If the guardrail's human-in-the-loop clause is read literally, **no mechanism available
to us satisfies it**, and that is the finding to take to Phil — not a claim that this one does.


---

## 17. ⚠️ CORRECTION — HITL *does* work on the sessionless era, via MRTR

**This section retracts the central conclusion of §15.** I reported that no MCP-native mechanism
could guarantee human approval on our default era. That was wrong, and the design decision to cut
`create_candidate` from v1.0 rested on it.

### 17.1 How I got it wrong

FastMCP's error message is precise, and I under-read it:

```
ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections.
```

The qualifier **"via server-initiated requests"** is doing real work. What 2026-07-28 removed is
the server's ability to *initiate* a request mid-call — not elicitation itself. I treated
`ctx.elicit()` as the definition of elicitation, found it unavailable, and generalised.

⚠️ **Citation correction, and its origin.** I originally attributed that removal to **SEP-2577**.
That is wrong, and it is worth recording where it came from. Per the official changelog
(`modelcontextprotocol.io/specification/2026-07-28/changelog`), verbatim:

> **Deprecated 1.** "Deprecate the **Roots, Sampling, and Logging** features (SEP-2577)."

SEP-2577 never touched elicitation. The statelessness that removed the back-channel is **SEP-2575**
(remove the `initialize` handshake) with **SEP-2567** (remove sessions), and the replacement
mechanism is **SEP-2322**:

> **Major change 7.** "Multi Round-Trip Requests (MRTR) pattern introduced which **replaces** the
> previous approach of sending server-initiated requests, such as `roots/list`,
> `sampling/createMessage`, or `elicitation/create`. Servers return an `InputRequiredResult`
> (`resultType: "input_required"`) whose `inputRequests` field carries the requests … Clients
> respond with `inputResponses` on a retry of the original request (SEP-2322)."

**I got SEP-2577 from FastMCP's own source comment**, which cites it twice on the `ctx.elicit()`
path (`fastmcp/server/context.py:947` and ~1085) `[FROM SOURCE]`:

```python
# Foreground push path: server-initiated elicitation needs a back-channel,
# which the 2026-07-28 era removed (SEP-2577). Raise a clear era-aware
```

The same file cites **SEP-2322 correctly** for all the MRTR machinery (lines 214, 359, 381, 402).
So the miscitation is internally inconsistent within one file, and it is the proximate cause of two
people independently concluding a capability was impossible. Drafted as a documentation issue in §8.4.

The official spec says so plainly (`https://modelcontextprotocol.io/docs/2026-07-28/learn/client-concepts`):

> "Elicitation follows the **Multi Round-Trip Requests** (MRTR) pattern. When a server needs user
> input while processing a request such as `tools/call`, it responds with an `InputRequiredResult`
> whose `inputRequests` field carries one or more `elicitation/create` requests. The client gathers
> the input and **retries the original request**, attaching the collected `inputResponses` and
> echoing back any `requestState` the server included."

The evidence was also already in this document and I walked past it: §6.3 quotes
`response_limiting.py` guarding `InputRequiredToolResult` with a comment naming **SEP-2322**. I
dumped that source, read it for the limiter bug, and did not register what it implied.

### 17.2 The working pattern — VERIFIED on sessionless

```python
from fastmcp.tools.base import InputRequiredToolResult
import mcp_types

@mcp.tool(annotations={"destructiveHint": True})
async def create_candidate(name: str, ctx: Context) -> dict:
    answers = ctx.input_responses                      # None on the first leg
    if answers is not None:
        resp = answers.root.get("approval")
        action = getattr(resp, "action", None)
        content = getattr(resp, "content", None) or {}
        if not (action == "accept" and content.get("approve") is True):
            raise ToolError(f"Not approved by a human (action={action!r}); refusing to write.")
        ROWS.append(name)
        return {"created": True, "rows": len(ROWS), "approvedVia": "MRTR elicitation"}

    req = mcp_types.ElicitRequest(
        method="elicitation/create",
        params=mcp_types.ElicitRequestFormParams(
            mode="form",
            message=f"Approve creating candidate {name}? This writes a real ATS record.",
            requestedSchema={"type": "object",
                             "properties": {"approve": {"type": "boolean"}},
                             "required": ["approve"]},
        ),
    )
    return InputRequiredToolResult(
        mcp_types.InputRequiredResult(result_type="input_required",
                                      input_requests={"approval": req},
                                      request_state=f"create:{name}")
    )
```

The accessors are **`ctx.input_responses`** and **`ctx.request_state`** on `Context` `[FROM SOURCE]`,
not on `request_context`.

### 17.3 Evidence — all three arms, sessionless (`mode="auto"`)

```
--- SESSIONLESS (auto), handler APPROVES ---
   is_error=False structured={'created': True, 'rows': 1, 'approvedVia': 'MRTR elicitation'}
--- SESSIONLESS (auto), handler DENIES ---
   is_error=True structured=None content=["Not approved by a human (action='decline'); refusing to write."]
--- SESSIONLESS (auto), NO handler ---
   RAISED MCPError: Elicitation not supported
```

- ✅ **Approve → the write happens.** `rows=1`.
- ✅ **Deny → the write is refused**, `is_error=True`, and the row counter did **not** increment.
- ✅ **No client handler → fails CLOSED** with `Elicitation not supported`. The write cannot proceed.

**Verdict: ✅ VERIFIED. Human-in-the-loop approval works on the sessionless 2026-07-28 era, and
fails closed when the client cannot support it.**

### 17.4 A guardrail worth knowing: the round cap

My first attempt looped, because I read the answers from the wrong attribute and therefore re-asked
every round. The client stopped it:

```
InputRequiredRoundsExceededError: Server returned InputRequiredResult for more than 10 rounds;
raise input_required_max_rounds on the Client, or use client.session.<method>(..., allow_input_requ...
```

`Client(input_required_max_rounds=10)` is the default. A guard tool that never consumes its answers
degrades into a bounded loop and then a clean error — not an infinite hang. Worth knowing, and worth
a test on our side asserting the second leg actually consumes `ctx.input_responses`.

### 17.5 What this changes

1. **The compliance gap has a real fix.** `create_candidate` can require per-invocation human
   approval on our default era, failing closed when unavailable. It need not be cut from v1.0 for
   the reason I gave.
2. **§15.3's fail-open finding still stands and still matters.** The result objects are truthy, and
   the MRTR path has the same hazard in a new shape: `action` and the answer *value* must **both**
   be checked. My §17.2 guard checks `action == "accept" and content.get("approve") is True`, and
   that conjunction is not optional — an accepted elicitation carrying `approve: false` is still an
   acceptance.
3. **The confirmation-token pattern (§16) is not dead**, but its role changes. It no longer has to
   substitute for elicitation. It remains useful as **defence in depth** and as the fallback for
   clients that report `Elicitation not supported` — and unlike elicitation it needs no client
   cooperation. The two compose: elicit when the client can, require a token when it cannot.
4. **§15.4 is unaffected.** Annotations remain advisory.

### 17.6 The abandonment arms — does it fail closed on EVERY path?

§17.3 proved approve / deny / no-handler. Those are the paths where the client answers. The harder
question is what happens when a client supports MRTR but the **human never answers** — abandons the
dialog, closes the window, or the handler dies. "Fails closed" has to mean closed on every path.

Four arms, each run in isolation against a live server, with the row count queried **independently
afterwards** so the counter is the server's own and not the probe's:

```
--- cancel (client timeout=None) ---
   is_error=True content=["Not approved (action='cancel'); refusing."]
   server row count AFTER = 0
--- approve_false (client timeout=None) ---
   is_error=True content=["Not approved (action='accept'); refusing."]
   server row count AFTER = 0
--- raises (client timeout=None) ---
   RAISED MCPError: handler crashed / window closed
   server row count AFTER = 0
--- hang (client timeout=5.0) ---
   (hang arm exceeded 60s wall)
   server row count AFTER abandoned approval = 0
```

**Results:**

- ✅ **Cancelled** → refused, no write.
- ✅ **Accepted carrying `approve: False`** → refused, no write. This is the fail-open case in its
  MRTR shape, and the `action == "accept" and content.get("approve") is True` conjunction catches it.
  Note the message reads `action='accept'` — the *action* was an acceptance; only the value check
  saved it.
- ✅ **Handler crashes / window closed** → `MCPError` propagates to the caller, no write.
- ⚠️ **Abandoned (human never answers)** → **the write does NOT happen (`rows = 0`), so it fails
  closed on the thing that matters.** But the *call hangs*: it exceeded a 60s wall clock even with
  `Client(timeout=5)` set.

**Characterising the hang precisely, because "hangs" and "unsafe" are different claims:**

- The **write is safe.** The tool returned `InputRequiredResult` and exited; the second leg never
  arrives, so the write code never runs. Independently confirmed: `rows = 0`.
- **No server resource is pinned.** The server continued serving other requests throughout —
  a concurrent `tools/list` returned **HTTP 200** while the abandoned call was outstanding.
- The hang is **client-side liveness only.** The elicitation handler runs *inside the client
  process*; a handler that never returns blocks that client's own call. `Client(timeout=...)` did
  **not** bound it, which is consistent with that timeout guarding the server round-trip rather than
  the client's own callback.

**Verdict: ✅ fails closed on every path for the write.** ⚠️ **but an abandoned approval hangs the
calling client rather than returning a refusal**, and the client-level `timeout` does not rescue it.

**Design consequence:** we get safety for free, but not liveness. If a caller abandons an approval,
the tool call does not resolve. That is a caller-side concern rather than a server one — but it is
worth one sentence in the README, because "the write silently never completes" is a confusing
failure mode for an integrator, and the obvious mitigation (setting a client timeout) does not work.

### 17.7 The lesson I am recording against myself

The finding in §15 was *correct*; the conclusion was *over-generalised*. I tested one API
(`ctx.elicit()`), found it unavailable, and reported that the capability was unavailable. The
qualifier in the error message, the spec's own client-concepts page, and a source comment I had
already pasted into this document all pointed at the other path. **A negative result about one API
is not a negative result about a capability**, and I should have gone looking for the second route
before telling the lead a design was blocked.


---

## 18. Host survey — which clients can actually do this?

Requested to size the practical picture for v1.1. **This is documentation research, not execution** —
I have not driven these hosts against our server. Sources cited inline; where only secondary sources
exist I say so.

### 18.1 Findings

| Host | Elicitation | Speaks 2026-07-28? | Source |
|---|---|---|---|
| **Claude Code** | ✅ **Yes**, no configuration required | ✅ **Yes**, on its v2 runtime | first-party, `code.claude.com/docs/en/mcp` |
| **Cursor** | ✅ Listed "Supported" in its capability table | ❓ not stated | first-party, `cursor.com/docs/context/mcp` |
| **Claude Desktop** | ⚠️ **Apparently not** — open feature requests | ❓ not stated | secondary only — treat as unconfirmed |

**Claude Code**, quoting its own docs:

> "Servers can request structured input from you mid-task using elicitation. When a server needs
> information it can't get on its own, Claude Code displays an interactive dialog and passes your
> response back to the server. **No configuration is required on your side**: elicitation dialogs
> appear automatically when a server requests them."

and on protocol negotiation:

> "The v2 runtime is the same code on MCP TypeScript SDK 2.0, which adds **MCP protocol revision
> 2026-07-28**. … Asks HTTP and claude.ai connector servers whether they support the newer revision,
> and uses it with those that do. It asks **stdio** servers only if you set
> `MCP_PROTOCOL_NEGOTIATION` to `auto`, and connects to every other server as v1 does."

Two things follow. First, **our primary client supports exactly the mechanism §17 verified**, on
exactly the era we default to. Second — and this is a deployment detail worth capturing — **Claude Code
negotiates 2026-07-28 for HTTP servers automatically, but for stdio only when
`MCP_PROTOCOL_NEGOTIATION=auto`.** A stdio install therefore lands on the handshake era by default,
where `ctx.elicit()` works and MRTR does not. **A guard tool must handle both paths**, which is an
argument for implementing the check once and branching on `ctx.input_responses` being available
rather than assuming an era.

**Cursor**'s docs mark Tools, Prompts, Resources, Roots, Elicitation and Apps all "Supported"; no
protocol version is stated, so whether it reaches MRTR elicitation is unknown.

**Claude Desktop**: I found **no first-party statement**. Secondary sources and several open
Anthropic issues indicate elicitation is not supported there, with an MCP-repo PR updating client
capability docs to credit Claude Code with Elicitation and Claude Desktop with Roots. **I am not
reporting this as established** — it is consistent across sources but none of them is authoritative,
and it is exactly the kind of claim that should be checked against the product before the design
leans on it.

### 18.2 ⚠️ The nuance that limits what we may claim

Claude Code's docs also say:

> "To auto-respond to elicitation requests without showing a dialog, use the `Elicitation` hook."

So even on a host that fully supports elicitation, **the approval can be configured to happen
without a human seeing anything.** That is a legitimate feature, and it means our honest claim is:

> The server **requires an approval response from the host** before writing, and refuses if the host
> cannot or will not provide one.

Not: "a human approved this." We can guarantee the *request* and the *refusal*; we cannot guarantee
a human was on the other end. The design and the README should say the former.

This is the same limit §16.4 recorded for the confirmation-token pattern, arrived at from a different
direction — and it is worth noting the MCP spec itself places human-in-the-loop confirmation on the
**host**, not the server (`docs/2026-07-28/develop/clients/client-best-practices`, Security
Considerations: *"Apply the same human-in-the-loop confirmation policy to sandbox-originated calls
that you apply to direct calls"*).

### 18.3 What this means for v1.1

- The mechanism verified in §17 has **real client support today** in our primary host, on our default
  era, with no user configuration.
- A stdio deployment needs the handshake path too, so build the guard to handle both.
- Claude Desktop support is unconfirmed and may be absent; the fail-closed behaviour (§17.3) means
  such a client simply cannot perform the write, which is the correct outcome.
- Whatever we ship, describe it as *host approval*, not *human approval*.


## What I could NOT verify

- **Python 3.10, and 3.13+.** Ran 3.11.15 and 3.12.3. The declared floor is `>=3.10`; 3.10 untested.
- **Whether the `ResponseLimitingMiddleware` regression also affects the network transport.** Reproduced in-memory; the failing assertion is client-side in `mcp/client/session.py`, so it should be transport-independent, but I did not re-run it over HTTP.
- **Whether the SIGTERM behaviour differs under a real container runtime** (Docker `stop`, Kubernetes `preStop`). Tested with raw `kill -TERM` on Linux. A container adds an init process and a grace period that I did not simulate.
- **Whether the SIGTERM behaviour also affects stdio transport.** Only HTTP was tested.
- ~~`ctx.elicit()` era-gating~~ — **resolved by execution in §15**: it raises on sessionless, on every transport including stdio, and the result types fail open under a naive guard.
- **Tasks / `TasksExtension`, `Depends()` injection, `create_proxy`, `mount`, `OpenAPIProvider`.** None exercised. `exclude_args` removal was confirmed by signature only.
- **`DereferenceMiddleware`, `ToolInjectionMiddleware`, `AuthorizationMiddleware`.** Still not exercised. `RateLimiting`, `ErrorHandling`, `Retry` and `Ping` are covered in §§13–14. Four of the eight tested are unusable or need their defaults overridden, so **assume nothing about the remaining three.**
- ~~A two-call confirmation-token HITL pattern~~ — **now spiked in §16** and verified on both eras. Its remaining limit is stated there: it enforces confirmation, **not human** confirmation. Untested under concurrency, and the token store is in-process (a multi-worker deployment would need shared state).
- **Host behaviour is surveyed from documentation in §18, NOT executed.** I have not driven Claude Code, Cursor or Claude Desktop against our server. Claude Desktop's lack of elicitation support rests on secondary sources only and should be confirmed against the product.
- **Rate limiting under concurrency.** Every limiter test was sequential and single-client; I have not verified bucket behaviour under simultaneous callers, which is the case that matters in production.
- **Whether `limiters.clear()` is safe to call on a live server.** I used it to prove reconfiguration requires it; I did not test it under load or check for a race with in-flight consumption.
- **`JWTVerifier`, `DebugTokenVerifier`, `IntrospectionTokenVerifier`, `OAuthProxy`.** Only `StaticTokenVerifier` was run; the others need an IdP I will not fake.
- **Token expiry**, and **cache TTL expiry** — I proved cache insertion and hit, never eviction.
- **Concurrency.** Every test was single-client and sequential.
- **`server.json` / `mcp-publisher`** — nothing from `FASTMCP.md` §12(b) was executed.
- **Anything about Jobvite.** No Jobvite endpoint was contacted; every tool here is a stub.
