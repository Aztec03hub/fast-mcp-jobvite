# ADR-0002: In-process rate limiting instead of a Redis token bucket

**Status:** Accepted

## Context

`backend/rate-limiting.md:355-356` mandates a Redis token bucket on every public-facing surface and
forbids in-memory limiting, requiring an ADR to opt out. Its stated rationale is desynchronisation
across replicas.

The standard also never defines "public-facing surface", so a localhost developer tool and an
internet-hosted service carry identical obligations under its text.

## Decision

Use FastMCP's own `RateLimitingMiddleware`, in process. Do not require Redis.

## Consequences

A single-process server has no replicas to desynchronise, so the clause's rationale does not obtain.
**Single-process is therefore load-bearing and is stated in the design**: running multi-worker
multiplies the effective limit by the worker count while every log line still reports the configured
number.

**Two further clauses this ADR must also dispose of**, since substituting the mechanism does not
dispose of them:

- **`:361-362` rule 6 requires a 429 to use a problem detail.** A limiter trip raises `MCPError`,
  a JSON-RPC protocol error, so it carries no RFC 9457 object. This is one of three admitted gaps in
  error-contract uniformity.
- **Rule 5's `RateLimit-*` response headers** are not emitted.

**Limitation, recorded rather than implied away:** every supporting measurement was sequential and
single-client. Behaviour under simultaneous callers is unverified, and `limiters.clear()` was never
tested under load. `clear()` is also the only way to apply new settings and it resets every client's
quota, so a config reload doubles as a quota amnesty.

