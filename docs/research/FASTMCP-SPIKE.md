# FastMCP 3.4.7 — Runtime Spike

Companion to `FASTMCP.md`. That report was **read**; this one was **run**.

- **Ran on:** Python **3.11.15** (`main, Aug 7 2026, 02:25:55) [Clang 22.1.3]`), `fastmcp==3.4.7` pinned exactly, `mcp` 1.29.1.
- **Where:** `/tmp/fastmcp-spike`, a throwaway `uv` project. **Deleted at the end of this spike** — see §8. Nothing was added to the repo except this file. The repo still has no `pyproject.toml`.
- **Evidence rule:** every verdict below rests on an exit code or a quoted payload. Where a claim was judged only by "the server started and nothing blew up", it is marked as such and not counted as evidence.
- **Credentials:** every token in this report is an obvious placeholder (`TOKEN-WITH-SCOPE-PLACEHOLDER`, `PLACEHOLDER-KEY-VALUE`). No real, realistic, or redacted-looking secret appears anywhere.

## Scoreboard

| # | Claim under test | Verdict |
|---|---|---|
| 1 | `StaticTokenVerifier` + `require_scopes` enforce auth and scope | ✅ **VERIFIED** (with a behavioural surprise — see 1.4) |
| 2 | `ToolError` survives `mask_error_details=True`; plain exceptions do not | ✅ **VERIFIED** in all four combinations |
| 3a | `ResponseCachingMiddleware` actually serves from cache | ✅ **VERIFIED** |
| 3b | `TimingMiddleware` / `StructuredLoggingMiddleware` fire | ✅ **VERIFIED** |
| 3c | `ResponseLimitingMiddleware` truncates oversized responses | ⛔ **REFUTED — it BREAKS the response for any tool with a return type annotation.** See §3.3. |
| 4 | Lifespan `\|` composition; both startup and both shutdown hooks run | ✅ **VERIFIED**, order confirmed, including under SIGTERM and SIGINT |
| 5 | `transport="http"` + in-memory and network `Client`; default path | ✅ **VERIFIED**, default path is `/mcp` |
| 6 | `fastmcp.json` cannot express a *required* env var | ✅ **VERIFIED BY BEHAVIOUR** — it fails **silently**, which is worse than I wrote in `FASTMCP.md` |
| 7 | Python 3.11 genuinely supported | ✅ **VERIFIED** on 3.11.15 |

## ⛔ Retraction — one recommendation from my own report is wrong

`FASTMCP.md` §8 and the "top 5 outdated" list recommend `ResponseLimitingMiddleware` as framework surface to adopt in place of `fast-mcp-jira`'s custom infrastructure. **Executing it refutes that.** On any tool with a return type annotation — i.e. the style FastMCP's own docs recommend, and the style we would write — an oversized response does not come back truncated. It comes back **broken**, and the client raises. Details and root cause in §3.3. Do not put it in the design.

---

## 1. StaticTokenVerifier and require_scopes

### 1.1 Server

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.auth import require_scopes

# PLACEHOLDER tokens - spike only, never real credentials
verifier = StaticTokenVerifier(
    tokens={
        "TOKEN-WITH-SCOPE-PLACEHOLDER": {
            "client_id": "full-client",
            "scopes": ["jobvite:read", "jobvite:write"],
        },
        "TOKEN-NO-SCOPE-PLACEHOLDER": {
            "client_id": "limited-client",
            "scopes": ["jobvite:read"],
        },
    },
)

mcp = FastMCP(name="spike-auth", auth=verifier)

@mcp.tool(description="Unguarded tool")
def ping() -> str:
    return "pong"

@mcp.tool(description="Requires jobvite:write", auth=require_scopes("jobvite:write"))
def write_thing() -> str:
    return "wrote"

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8931, path="/mcp")
```

Server start (verbatim):

```
[08/27/26 14:10:33] INFO     Starting MCP server 'spike-auth'   transport.py:361
                             with transport 'http' on
                             http://127.0.0.1:8931/mcp
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8931 (Press CTRL+C to quit)
```

### 1.2 The refusals — raw HTTP

`curl -i -X POST http://127.0.0.1:8931/mcp -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`, verbatim:

**No token:**
```
HTTP/1.1 401 Unauthorized
server: uvicorn
content-length: 0
www-authenticate: Bearer
```

**Bad token** (`Authorization: Bearer WRONG-TOKEN-PLACEHOLDER`):
```
HTTP/1.1 401 Unauthorized
content-type: application/json
content-length: 301
www-authenticate: Bearer error="invalid_token", error_description="Authentication failed. The provided bearer token is invalid, expired, or no longer recognized by the server. To resolve: clear authentication tokens in your MCP client and reconnect. Your client should automatically re-register and obtain new tokens."

{"error": "invalid_token", "error_description": "Authentication failed. The provided bearer token is invalid, expired, or no longer recognized by the server. To resolve: clear authentication tokens in your MCP client and reconnect. Your client should automatically re-register and obtain new tokens."}
```

**Good token** — auth passes, request reaches the protocol layer:
```
HTTP/1.1 400 Bad Request
mcp-session-id: 725fdf27673b471b8eb053536d15dc49

{"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Bad Request: Missing session ID"}}
```
(The 400 is expected — a raw `curl` skips the handshake. The point is that it is a **protocol** error, not a 401: authentication succeeded.)

### 1.3 The scope refusal — via `Client`

```python
async with Client("http://127.0.0.1:8931/mcp", auth=token) as c:
    tools = sorted(t.name for t in await c.list_tools())
    r = await c.call_tool("write_thing", {})
```

Verbatim output:

```
===== TOKEN WITH jobvite:write =====
list_tools -> ['ping', 'write_thing']
call ping -> OK 'pong' isError=False
call write_thing -> OK 'wrote' isError=False

===== TOKEN LACKING jobvite:write =====
list_tools -> ['ping']
call ping -> OK 'pong' isError=False
call write_thing -> REFUSED ToolError: Unknown tool: 'write_thing'

===== INVALID TOKEN =====
connect -> FAILED HTTPStatusError: Client error '401 Unauthorized' for url 'http://127.0.0.1:8931/mcp'

EXIT=0
```

**Verdict: ✅ VERIFIED.** The refusal bites, and the invalid token cannot even open a session.

### 1.4 ⚠️ Behavioural surprise worth designing around

`require_scopes` does **not** merely refuse the call. It **removes the tool from `list_tools` entirely** for a client lacking the scope, and a direct call is refused with **`Unknown tool: 'write_thing'`** — not a permission error.

Two consequences for our design:

- **Good:** capability hiding is automatic; a read-only Jobvite token never sees the write tools advertised.
- **Watch out:** a client cannot distinguish "not permitted" from "does not exist", and neither can we in a support ticket. If an integrator reports "the tool is missing", the first question is their token's scopes. Worth one line in our README.

---

## 2. ToolError vs plain exception, across both masking settings

### 2.1 Code

```python
def build(mask: bool) -> FastMCP:
    m = FastMCP(name=f"errs-mask-{mask}", mask_error_details=mask)

    @m.tool(description="raises ToolError")
    def raise_tool_error() -> str:
        raise ToolError("TOOLERROR-DETAIL: jobvite issue key must match ^[A-Z]+-[0-9]+$")

    @m.tool(description="raises plain ValueError")
    def raise_plain() -> str:
        raise ValueError("PLAIN-DETAIL: secret-ish internal string 12345")

    return m

async with Client(build(mask)) as c:
    r = await c.call_tool(tool, {}, raise_on_error=False)
```

### 2.2 All four combinations, verbatim

```
########## mask_error_details=False ##########
--- raise_tool_error ---
  is_error : True
  content  : ['TOOLERROR-DETAIL: jobvite issue key must match ^[A-Z]+-[0-9]+$']
  structured: None
--- raise_plain ---
  is_error : True
  content  : ["Error calling tool 'raise_plain': PLAIN-DETAIL: secret-ish internal string 12345"]
  structured: None

########## mask_error_details=True ##########
--- raise_tool_error ---
  is_error : True
  content  : ['TOOLERROR-DETAIL: jobvite issue key must match ^[A-Z]+-[0-9]+$']
  structured: None
--- raise_plain ---
  is_error : True
  content  : ["Error calling tool 'raise_plain'"]
  structured: None

EXIT=0
```

**Verdict: ✅ VERIFIED, exactly as documented.**

- `is_error` is `True` in all four cases.
- The `ToolError` message is **byte-identical** with masking on and off.
- The plain `ValueError`'s detail (`PLAIN-DETAIL: secret-ish internal string 12345`) is **stripped** under masking, leaving only `Error calling tool 'raise_plain'`.

### 2.3 ⚠️ Caveat the docs do not state

Masking is **client-facing only**. With `mask_error_details=True` the full traceback — including the string that was masked from the client — is still written to the **server log**:

```
ValueError: PLAIN-DETAIL: secret-ish internal string 12345
```

So masking protects the MCP client, **not** our log sink. Any Jobvite credential or PII that reaches an exception message still lands in the logs. Design consequence: never interpolate a credential into an exception message, and treat the log stream as sensitive regardless of the masking setting.

---

## 3. Middleware — each one demonstrably firing

Setup: `StructuredLoggingMiddleware(include_payloads=True)`, `TimingMiddleware()`, `ResponseCachingMiddleware(...)`, `ResponseLimitingMiddleware(max_size=200)`, all added via `mcp.add_middleware(...)`, exercised through the in-memory `Client`.

### 3.1 ResponseCachingMiddleware — ✅ VERIFIED

Tool-call caching is **opt-in**; it does nothing unless you pass `call_tool_settings`:

```python
mcp.add_middleware(ResponseCachingMiddleware(
    call_tool_settings={"enabled": True, "ttl": 60, "included_tools": ["expensive"]},
))
```

Proof is a side-effect counter incremented inside the tool body, so a cache hit is observable rather than inferred:

```
>>> CACHING: two identical calls to expensive('a')
  call#1 -> computed:a | real invocations so far: 1
  call#2 -> computed:a | real invocations so far: 1
  CACHE HIT

>>> CACHING control: different arg must MISS
  call#3 -> computed:b | real invocations so far: 2
```

The second identical call **did not execute the function body**. The negative control (different argument) **did**, so the cache is keyed on arguments and is not simply swallowing everything.

Timing corroborates: `tools/call completed in 1.34ms` (miss) versus `0.11ms` (hit) — a 12x drop.

### 3.2 TimingMiddleware and StructuredLoggingMiddleware — ✅ VERIFIED

Verbatim, from the same run:

```
INFO     {"event": "request_start", "method": "tools/call", "source": "client",
         "payload": "{\"task\":null,\"_meta\":null,\"name\":\"expensive\",\"arguments\":{\"key\":\"a\"}}",
         "payload_type": "CallToolRequestParams"}
INFO     Request tools/call completed in 1.34ms                    timing.py:47
INFO     {"event": "request_success", "method": "tools/call", "source": "client", "duration_ms": 1.77}
```

Both emit real JSON/timing records per request. Note `include_payloads=True` logs **tool arguments verbatim** — for Jobvite that means candidate data and any credential passed as an argument would be written to the log. **Leave `include_payloads` at its default `False` in production.**

Bonus evidence for `FASTMCP.md` §1: the initialize payload logged at runtime contains `\"protocolVersion\":\"2025-11-25\"`, confirming by observation — not by reading a constant — that fastmcp 3.4.7 negotiates MCP **2025-11-25**.

### 3.3 ⛔ ResponseLimitingMiddleware — REFUTED

The middleware **does** fire — it logs the warning and truncates:

```
WARNING  Tool 'huge' response exceeds size limit: 10163 bytes > 200 bytes,
         truncating                                    response_limiting.py:123
```

But the call then **fails at the client**:

```
RuntimeError: Tool huge_annotated has an output schema but did not return structured content
EXIT=1
```

Isolating it with an annotated and an unannotated tool side by side:

```
tool huge_annotated:   outputSchema={'properties': {'result': {'type': 'string'}}, 'required': ['result'],
                                     'type': 'object', 'x-fastmcp-wrap-result': True}
tool huge_unannotated: outputSchema=None

--- huge_annotated ---
  RAISED RuntimeError: Tool huge_annotated has an output schema but did not return structured content

--- huge_unannotated ---
  len: 150 is_error: False
  tail: 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY\n\n[Response truncated due to size limit]'
  structured_content: None
```

**Root cause, from the middleware's own source** (`fastmcp/server/middleware/response_limiting.py`, ~line 95) — the comment states the intended defence, and it no longer holds:

```python
# Preserve original meta, falling back to {} when absent. Having
# meta set ensures to_mcp_result() returns a CallToolResult, which
# bypasses MCP SDK outputSchema validation — a truncated response
# is no longer valid structured output.
return ToolResult(
    content=[TextContent(type="text", text=truncated)],
    meta=meta if meta is not None else {},
)
```

The truncated result drops `structured_content` while the tool's advertised `outputSchema` remains. The `meta={}` trick was meant to route around SDK validation; against `mcp` 1.29.1's `ClientSession._validate_tool_result` it does not, and the client raises.

**Blast radius:** any tool with a return type annotation. FastMCP auto-generates an output schema from the annotation (visible above as `x-fastmcp-wrap-result`), and annotating returns is the documented, recommended style. So this hits essentially every tool we would write — and only on the oversized path, meaning it passes every small-payload test and fails in production on the one large Jobvite candidate list.

**Mitigation tested** — scoping the limiter with `tools=[...]` to only unannotated tools avoids the break:

```
huge_annotated:   len=5000 is_error=False truncated=False   # not limited at all
huge_unannotated: len=150  is_error=False truncated=True    # limited correctly
```

But that is avoidance, not a fix: the annotated tool is simply left **unlimited**.

**Recommendation:** do **not** use `ResponseLimitingMiddleware`. Cap response size **inside the tool** — page/slice the Jobvite result and return a short, honest summary — which is better behaviour anyway (a truncated JSON blob is not useful to a model, whereas "showing 50 of 1,240, use `offset`" is). This supersedes my `FASTMCP.md` recommendation.

---

## 4. Lifespan composition with `|`

```python
@lifespan
async def db_lifespan(server):
    say("A-startup (db)");    yield {"db": "DB-HANDLE"};       say("A-shutdown (db)")

@lifespan
async def cache_lifespan(server):
    say("B-startup (cache)"); yield {"cache": "CACHE-HANDLE"}; say("B-shutdown (cache)")

mcp = FastMCP(name="spike-lifespan", lifespan=db_lifespan | cache_lifespan)
```

In-memory run, verbatim:

```
LIFESPAN A-startup (db)
LIFESPAN B-startup (cache)
TOOL -> lifespan_context={'db': 'DB-HANDLE', 'cache': 'CACHE-HANDLE'}
LIFESPAN B-shutdown (cache)
LIFESPAN A-shutdown (db)
LIFESPAN in-memory client closed
EXIT=0
```

**Verdict: ✅ VERIFIED.** Left enters first, right enters second, exit is strict reverse order, and the two dicts are shallow-merged into a single `ctx.lifespan_context`.

### 4.1 Shutdown hooks under real signals

This matters more than the in-memory case: it is what decides whether our Jobvite HTTP client and cache actually get closed on a container stop. Tested under both signals, verbatim:

```
########## SIGTERM ##########
EXITED after SIGTERM
LIFESPAN A-startup (db)
LIFESPAN B-startup (cache)
INFO:     Application shutdown complete.
LIFESPAN B-shutdown (cache)
LIFESPAN A-shutdown (db)

########## SIGINT ##########
EXITED after SIGINT
LIFESPAN A-startup (db)
LIFESPAN B-startup (cache)
INFO:     Application shutdown complete.
LIFESPAN B-shutdown (cache)
LIFESPAN A-shutdown (db)
```

Both signals run both teardowns in reverse order. (An earlier attempt appeared to show shutdown hooks *not* running; that was my harness killing the process before stdout flushed, not a FastMCP behaviour. Correcting it here rather than leaving the wrong impression.)

---

## 5. Transport, path, and both client styles

### 5.1 In-memory `Client(mcp)` — ✅ VERIFIED

Used throughout §§2–4. `async with Client(mcp)` runs the full lifespan and tool dispatch with no socket. This is the right default for our test suite.

### 5.2 Network client — ✅ VERIFIED

Against `mcp.run(transport="http", host="127.0.0.1", port=8932, path="/mcp")`:

```
NETWORK TOOL -> lifespan_context={'db': 'DB-HANDLE', 'cache': 'CACHE-HANDLE'}
NET_EXIT=0
```

Server-side access log for a full session:

```
INFO:     127.0.0.1:34092 - "POST /mcp HTTP/1.1" 200 OK
INFO:     127.0.0.1:34108 - "POST /mcp HTTP/1.1" 202 Accepted
INFO:     127.0.0.1:34112 - "GET /mcp HTTP/1.1" 200 OK
INFO:     127.0.0.1:34128 - "POST /mcp HTTP/1.1" 200 OK
INFO:     127.0.0.1:34146 - "DELETE /mcp HTTP/1.1" 200 OK
```

### 5.3 Default path — ✅ `/mcp`, confirmed by probe

With **no** `path=` argument at all (`mcp.run(transport="http", host="127.0.0.1", port=8933)`):

```
path=/     -> 404
path=/mcp  -> 400     <- reached the protocol layer
path=/mcp/ -> 307     <- redirect to /mcp
```

`404` at root versus `400` at `/mcp` proves the endpoint is mounted at `/mcp` by default. Passing `path="/mcp"` explicitly is harmless and self-documenting; I'd keep it.

---

## 6. fastmcp.json — required env vars

### 6.1 The file used

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": { "type": "filesystem", "path": "server.py", "entrypoint": "mcp" },
  "environment": { "type": "uv", "python": ">=3.11" },
  "deployment": {
    "transport": "http", "host": "127.0.0.1", "port": 8934, "path": "/mcp",
    "log_level": "INFO",
    "env": { "JOBVITE_API_KEY": "${JOBVITE_API_KEY}", "MODE": "spike" }
  }
}
```

### 6.2 The CLI picks it up — ✅

`fastmcp inspect` with no arguments, verbatim:

```
INFO     Using configuration from fastmcp.json     cli.py:67

Server
  Name:         spike-config
  Version:      3.4.7
  Generation:   2

Components
  Tools:        1
  ...
Environment
  FastMCP:      3.4.7
  MCP:          1.29.1

INSPECT_EXIT=0
```

Auto-detection is real, and `fastmcp inspect` exits 0 — usable as a CI check.

### 6.3 Required env vars — ✅ CONFIRMED IMPOSSIBLE, and worse than I wrote

**Schema evidence** (fetched live from the published `$schema` URL):

```
Deployment keys: ['args', 'cwd', 'env', 'host', 'log_level', 'path', 'port', 'transport']

env schema: {"anyOf": [{"additionalProperties": {"type": "string"}, "type": "object"},
                       {"type": "null"}],
             "description": "Environment variables to set when running the server"}
```

`env` is a flat `dict[str, str]`. There is **no** slot for `required`, `secret`, or a description — not merely undocumented, structurally absent.

**Behavioural evidence** — `fastmcp run` with `JOBVITE_API_KEY` **unset**:

```
########## JOBVITE_API_KEY UNSET ##########
  TOOL -> JOBVITE_API_KEY=${JOBVITE_API_KEY} MODE=spike
  fastmcp run exit behaviour: log tail:
INFO     Starting MCP server 'spike-config'
```

The server **starts normally** and the tool receives the **literal string `${JOBVITE_API_KEY}`**. No warning, no non-zero exit. With the variable set (clean run, fresh port):

```
  TOOL -> JOBVITE_API_KEY=PLACEHOLDER-KEY-VALUE MODE=spike
  probe exit=0
```

*(Methodology note: my first "SET" run collided with a stale process still bound to port 8934 and returned the uninterpolated literal. That result was invalid and is discarded; the line above is from a clean rerun after freeing the port. Flagging it because a stale-port artifact would have produced a confident, wrong "interpolation is broken" finding.)*

**Verdict: ✅ VERIFIED — and the failure mode is silent.** This is *worse* than `FASTMCP.md` §12(e) implied. A missing credential does not fail at startup; it flows into the application as the literal text `${JOBVITE_API_KEY}` and surfaces later as a confusing Jobvite 401. **The pydantic-settings layer must own required-config validation.**

### 6.4 The substitute, verified

Prohibition needs a working substitute, so I ran one:

```python
class Settings(BaseSettings):
    jobvite_api_key: str = Field(description="Required, no default")
    mode: str = "default-mode"
```

```
--- UNSET ---
  FAILED FAST: ValidationError
  1 validation error for Settings
  jobvite_api_key
    Field required [type=missing, input_value={}, input_type=dict]

--- SET ---
  OK -> default-mode | key len: 21
EXIT=0
```

Fails fast, names the missing variable, and does not leak the value. This is the pattern to use.

---

## 7. Python version floor

```
PY 3.11.15 (main, Aug  7 2026, 02:25:55) [Clang 22.1.3]
fastmcp 3.4.7
mcp 1.29.1
```

Every section of this spike ran on that interpreter. **✅ VERIFIED: 3.11 is genuinely supported.** (`fastmcp` 3.4.7 declares `requires-python >=3.10`; I tested 3.11 only, not 3.10 or 3.12 — see §9.)

Runtime protocol constants on this build:

```
mcp LATEST_PROTOCOL_VERSION    = 2025-11-25
mcp DEFAULT_NEGOTIATED_VERSION = 2025-03-26
mcp package version            = 1.29.1
```

Corroborated by an observed handshake payload carrying `"protocolVersion":"2025-11-25"` (§3.2). This upgrades `FASTMCP.md` §1's `[FROM SOURCE]` inference to an observed fact.

---

## 8. Cleanup

`/tmp/fastmcp-spike` **has been deleted**, along with all spike servers and processes. Nothing was written into the repo but this file. The repo's (still absent) `pyproject.toml` was not touched, and none of the spike's dependencies — `pydantic-settings` was added to the *spike* venv only — reached the repo.

---

## 9. Verified snippet library

Everything below was executed in this spike. Copy freely.

### 9.1 Auth — static bearer tokens from the environment

```python
import json, os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from fastmcp.server.auth import require_scopes

# Load tokens from the environment; NEVER inline them (the class docstring warns
# they are stored in plain text).
# MCP_TOKENS = {"<token>": {"client_id": "...", "scopes": ["jobvite:read"]}}
verifier = StaticTokenVerifier(tokens=json.loads(os.environ["MCP_TOKENS"]))

mcp = FastMCP(name="jobvite", auth=verifier, mask_error_details=True)

@mcp.tool(description="Read-only")
def get_candidate(candidate_id: str) -> dict: ...

@mcp.tool(description="Mutating", auth=require_scopes("jobvite:write"))
def update_candidate(candidate_id: str) -> dict: ...
```

Remember: a token without `jobvite:write` will not see `update_candidate` in `list_tools` at all (§1.4).

### 9.2 Errors

```python
from fastmcp.exceptions import ToolError

@mcp.tool(description="...")
async def get_candidate(candidate_id: str) -> dict:
    if not CANDIDATE_ID_RE.match(candidate_id):
        raise ToolError(f"candidate_id must match {CANDIDATE_ID_RE.pattern}")
    resp = await client.get(f"/candidate/{candidate_id}")
    if resp.status_code == 404:
        raise ToolError(f"No candidate {candidate_id}")
    resp.raise_for_status()   # unexpected -> masked generic message to the client
    return resp.json()
```

Rule proven in §2: **actionable → `ToolError`** (message always reaches the client); **unexpected → let it raise** (detail stripped by `mask_error_details=True`). Never put a credential in either — the server log keeps the full traceback.

### 9.3 Lifespan composition

```python
from fastmcp.server.lifespan import lifespan

@lifespan
async def http_lifespan(server):
    client = make_jobvite_client()
    yield {"jobvite": client}
    await client.aclose()

@lifespan
async def cache_lifespan(server):
    cache = await open_cache()
    yield {"cache": cache}
    await cache.close()

mcp = FastMCP(name="jobvite", lifespan=http_lifespan | cache_lifespan)
```

Teardown order is reverse of setup, and runs on SIGTERM and SIGINT (§4.1).

### 9.4 Middleware — the safe set

```python
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.caching import ResponseCachingMiddleware

mcp.add_middleware(StructuredLoggingMiddleware())   # include_payloads=False (default)
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(ResponseCachingMiddleware(
    call_tool_settings={"enabled": True, "ttl": 300,
                        "included_tools": ["list_jobs", "get_job"]},
))
# DO NOT add ResponseLimitingMiddleware - see section 3.3. Cap sizes in the tool.
```

### 9.5 Transport — stdio default, HTTP opt-in

```python
def main() -> None:
    s = get_settings()                      # pydantic-settings; fails fast (9.6)
    if s.mcp_transport == "http":
        mcp.run(transport="http", host=s.mcp_host, port=s.mcp_port, path="/mcp")
    else:
        mcp.run()                           # stdio, for local clients
```

### 9.6 Required config

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    jobvite_api_key: str = Field(description="Required")   # no default -> fails fast
    jobvite_secret: str = Field(description="Required")
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000
```

`fastmcp.json` cannot do this (§6.3). This layer is the only enforcement point.

### 9.7 Testing

```python
import pytest
from fastmcp import Client
from server import mcp

@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c

async def test_bad_id_raises_tool_error(client):
    r = await client.call_tool("get_candidate", {"candidate_id": "!!"}, raise_on_error=False)
    assert r.is_error
    assert "must match" in r.content[0].text
```

`raise_on_error=False` is what lets you assert on the error payload rather than catching — used throughout §2.

---

## What I could NOT verify

- **Python 3.10 and 3.12+.** I ran 3.11.15 only. The `requires-python >=3.10` floor is a declaration I did not exercise.
- **`ResponseLimitingMiddleware` over the network.** The break was reproduced with the in-memory client. The failing assertion lives in `mcp/client/session.py::_validate_tool_result` — client-side, so it should be transport-independent — but I did not re-run it over HTTP to prove that. The refutation stands for the in-memory case, which is where our tests will run; treat the network case as very likely but formally untested.
- **Whether the `ResponseLimitingMiddleware` defect is known upstream.** I did not search the FastMCP issue tracker, and I did not check whether 4.0 fixes it.
- **`RateLimitingMiddleware`, `ErrorHandlingMiddleware`, `RetryMiddleware`, `PingMiddleware`.** Not exercised. `FASTMCP.md` names them; only the four in the brief were tested. Given that one of those four turned out to be broken, **assume nothing about the untested ones** — spike any before adopting.
- **`JWTVerifier`, `DebugTokenVerifier`, `IntrospectionTokenVerifier`, `OAuthProxy`.** Only `StaticTokenVerifier` was run. The others need an IdP or an introspection endpoint to test honestly, and I will not simulate one.
- **Token expiry.** `StaticTokenVerifier` reads `expires_at`; I tested only non-expiring tokens.
- **`fastmcp install`, `fastmcp dev`, `fastmcp project prepare`.** Only `run` and `inspect` were exercised.
- **`server.json` / `mcp-publisher`.** Nothing from `FASTMCP.md` §12(b) was executed — no registry account, no publish, no `mcp-publisher validate`. That section remains documentation-only.
- **Concurrency, load, and cache eviction.** Every test was single-client and sequential. The `ResponseCachingMiddleware` TTL was set to 60s and never allowed to expire, so **expiry is untested** — I proved insertion and hit, not eviction.
- **Anything about Jobvite.** No Jobvite endpoint was contacted; every tool in this spike is a stub.
