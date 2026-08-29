# ADR-0001: Target fastmcp 4.0.0b4 and the sessionless MCP spec

**Status:** Accepted (Phil, 2026-08-27)
**Type:** Deviation

## Context

Latest stable `fastmcp` is 3.4.7 and speaks MCP spec `2025-11-25`. The current published spec is
`2026-07-28`, reachable only through the 4.0 beta line, which additionally forces `mcp>=2.0`,
`pydantic>=2.12`, Starlette 1.x, and swaps `httpx` for `httpx2`.

Research recommended pinning the stable line. Phil overruled it: we are deliberate early adopters,
and bugs found are to be characterised precisely and reported upstream rather than worked around
silently.

## Decision

Pin `fastmcp==4.0.0b4` and target the sessionless `2026-07-28` spec.

## Consequences

Every framework claim had to be established by execution rather than documentation, because the
upgrade guide was the only written source. That produced four upstream issues
(PrefectHQ/fastmcp #4926, #4927, #4929, #4930) and refuted three documented behaviours.

**The characteristic cost is visible and named:** a correct upstream fix silently stopped working
because `mcp` major-versioned underneath it, with zero change to the code that broke. `mcp` is
therefore pinned explicitly and a `fastmcp inspect` capability diff runs between builds.

