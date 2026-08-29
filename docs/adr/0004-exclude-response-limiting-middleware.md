# ADR-0004: `ResponseLimitingMiddleware` excluded; response size bounded in-tool

**Status:** Accepted
**Type:** Deviation

## Context

The framework ships a middleware for bounding response size. Executing it shows it raises
`RuntimeError: ... did not return structured content` on any tool with a return type annotation -
which is the documented style and what we write.

It is a **regression**: PR #3756 fixed exactly this on 2026-04-05, and the middleware's own source
is unchanged since. `mcp` 2.x now validates output schemas unconditionally, removing the bypass the
fix depended on.

## Decision

Do not adopt it. Bound response size inside each tool: cap the page and report `showing 50 of 1,240`.

## Consequences

The failure mode is why this is an ADR rather than a preference: **it fires only on the oversized
path**, so it passes every small-payload test and fails on the first large candidate list, in
production.

The in-tool bound is better for the caller anyway - a model can act on "50 of 1,240" and cannot act
on a truncated JSON blob. Reported upstream as PrefectHQ/fastmcp#4926.

