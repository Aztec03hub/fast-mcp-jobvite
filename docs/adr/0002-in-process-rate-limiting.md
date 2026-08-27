# ADR-0002: In-process rate limiting instead of a Redis token bucket

**Status:** Accepted

## Context

`backend/rate-limiting.md:356` mandates a token bucket via Redis and forbids in-memory limiters in
production; `:355` requires an ADR to opt out of rate-limiting a public endpoint. Those two rules
are terse and carry no rationale.

**The rationale is at `:94-97`**, and it is specific enough to test our situation against rather
than paraphrase. In-memory limiters are *"forbidden in production because they desynchronize across
replicas"*, and the standard gives the worked case: *"a 4-replica deployment with in-memory limits
gives each client 4× the intended quota."* That is the whole objection, and it is a statement about
replica count.

The standard also never defines "public-facing surface", so a localhost developer tool and an
internet-hosted service carry identical obligations under its text.

## Decision

Use FastMCP's own `RateLimitingMiddleware`, in process. Do not require Redis.

## Consequences

A single-process server has no replicas to desynchronise, so the clause's rationale does not obtain
at one replica. **But it obtains exactly as written at more than one**, and the standard's own
worked example is the failure mode: 4 replicas, 4x the intended quota. **Single-process is therefore
load-bearing and is stated in the design**: running multi-worker multiplies the effective limit by
the worker count while every log line still reports the configured number. That is not an analogy to
`:94-97`, it is the same defect with workers substituted for replicas, which is why the deviation is
safe only while the process count stays at one.

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

