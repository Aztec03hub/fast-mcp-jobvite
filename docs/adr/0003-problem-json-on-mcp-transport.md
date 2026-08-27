# ADR-0003: `application/problem+json` cannot be set on an MCP tool error

**Status:** Accepted

## Context

`architecture/error-contract.md:44` requires the media type `application/problem+json` on all error
responses. An MCP tool error travels inside a 200 OK JSON-RPC body whose content type the transport
fixes.

## Decision

Carry the complete RFC 9457 problem object as the tool result's structured content, and do not set
the media type. Apply `problem+json` properly wherever a real HTTP surface exists.

## Consequences

**The clause is violated in the letter and no implementation can satisfy it.** This is not a
preference.

**State the smaller true thing:** the real HTTP surfaces are transport-level auth rejections, which
exist only on the opt-in HTTP transport. **On the default stdio transport, `problem+json` is
honoured nowhere at all.** An earlier draft claimed a health endpoint as mitigation; none was ever
specified, and the claim was removed rather than a health endpoint invented to justify it.

Two adaptations, neither a deviation: `type` stays a relative `/problems/<slug>` reference, which is
what makes the contract transport-independent; `instance` is a URN, since MCP has no request URI
(`error-contract.md:83` defines it as the URI of the request that generated the error).

