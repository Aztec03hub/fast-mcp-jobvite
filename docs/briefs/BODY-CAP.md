# BODY-CAP - `DESIGN.md:165`'s 1 MiB body limit has a seat and has never been sat in

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `body-cap`. Your branch is `feat/body-cap`. Your report goes to
`docs/worklogs/BODY-CAP-REPORT.md`, committed on your branch. Your task record is **#81**.

**Read `docs/adr/0029-*.md` in full, INCLUDING its "Ruling, 2026-08-29" section**, which corrects the
ADR's own title and central claim.

## The state of it

`DESIGN.md:165` requires a **1 MiB max request body**. ADR-0029 says it has *"no middleware to live
in"*. The ruling corrects that: measured against the locked `fastmcp 4.0.0b4`,

```
FastMCP.run_http_async(..., uvicorn_config, middleware, ...)
http_app:  middleware: list[ASGIMiddleware] | None = None
```

**`ASGIMiddleware` sees the raw request body.** Our own `Middleware` objects are MCP-protocol
middleware and see a parsed message, which is why `build_middleware` cannot host this - two different
layers, and the ADR conflated "no middleware WE have" with "no middleware". `__main__.py:438` already
calls `mcp.run(transport="http", **http_run_kwargs(settings))`, so `http_run_kwargs` in
`http_hardening.py:390` is the function that gains it.

**The ADR's refusal stands and is the half that matters**: `MAX_PAYLOAD_BYTES` is NOT this cap and
must not be relabelled as it.

## CHECK THIS FIRST - it may make the whole unit unnecessary

`run_http_async` also takes `uvicorn_config`. **If uvicorn already offers a request-body limit, that
is a cheaper and more correct answer than a middleware we maintain.** I did not look. Find out before
writing code, and put the answer in your report either way - "I checked and it does not" is a result.

## What the cap must do

- Reject a body over 1 MiB **before** it is read into memory. A cap that buffers the whole body to
  measure it has not bounded anything - prefer `Content-Length` where present, and enforce a running
  bound on the streamed body where it is not, because a chunked request can omit the header entirely.
  **That second case is the one an attacker uses.**
- Return a problem object. **Unlike the argument path, this rejection CAN produce one:**
  `DESIGN.md:181-190` says no problem object can be produced pre-dispatch, which is why every §8 #9
  argument arm asserts a `ValidationError` - but an ASGI middleware sits at the HTTP layer where the
  registry's rows are reachable. **Pick the row deliberately and say why in the report.** 413 and 422
  are both defensible; picking whichever is nearest is not.
- **HTTP only, by construction.** There is no body on stdio, so `MAX_PAYLOAD_BYTES` remains the only
  bound on that path. **The two are not duplicates - do not remove the payload cap as one.**

## Rewrite the prose it makes stale, in place

`src/fast_mcp_jobvite/utils/constraints.py` carries a caveat saying the body limit "is still not
discharged here", and the §8 #9 size arms repeat it. Once it IS discharged elsewhere, those are
wrong. **Rewrite them in place**; appending a correction leaves two contradictory claims, and this
project rewrote a whole review document rather than do that.

`constraints.py` also now records R8-M2: `MAX_PAYLOAD_BYTES` under-measures the wire by up to **6x**
because it re-serialises with `ensure_ascii=False` and a client may `\u`-escape printable ASCII. **A
byte-exact bound is exactly what your middleware can provide and that module cannot** - say in your
report whether yours is exact, and if so, that the residue is now bounded at the right layer.

## Testing it

**A test that posts a 2 MiB body and gets a rejection is not enough** - it passes against a server
that rejects everything. You need the accepting arm at the boundary, both sides:
`1 MiB - 1` accepted, `1 MiB + 1` refused. That is how U14's four structural limits are tested and it
is the shape here.

Then **amputate the cap** and confirm the refusing arm goes red. A limit whose removal changes no
test result is not enforced.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - 801 and 415 as this was written and they move
daily. **0 skips.**

**Run the gate's OWN commands, argument for argument.** `uv run --frozen mypy`, NOT `mypy src` - I
reported "mypy clean" for a day from a command checking 23 files while CI checks 65, and shipped a
type error to `main` that way. `ci.yml:422` is the authority.

You will need a harness pair with a **derived** ROW_FLOOR - run it, read its own count from its own
output, never copy a number. `ci.yml` is the orchestrator's; put the steps you need in your report.

## In the report

Whether `uvicorn_config` could have done this instead. The registry row you chose and why. The
boundary measurements, both sides. The amputation. Then what you could not settle.
