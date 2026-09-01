# ADR-0022: "Do not implement a cookie jar" is a DISABLE, not an omission

**Status:** Accepted

**Type:** Correction to a contract statement that an implementer can satisfy while shipping the defect it was written to prevent

## Context

`JOBVITE-CONTRACT.md` §2.3 records, as `[RECORDED]` ground truth:

> The `Set-Cookie: AWSALBAPP-*` values are all the literal string `_remove_`.
> **Do not implement a cookie jar.** The API is credential-authenticated per
> request; there is no session to carry.

The instruction is phrased as a prohibition on writing code. Read literally, an
implementer discharges it by **doing nothing** - by not reaching for a cookie
jar, not configuring persistence, and not thinking about cookies at all.

**Doing nothing produces the opposite of the intended behaviour.** Measured
during U4 against the pinned resolve (`httpx2` 2.12.0), with `MockTransport`
standing in for the network:

```
jar after 1st response:      {'AWSALBAPP-0': '_remove_', 'AWSALBAPP-1': '_remove_'}
Cookie header sent on 2nd:   AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_
```

A bare `httpx2.AsyncClient` **has** a cookie jar, stores what Jobvite sets, and
sends it back on every subsequent request for the life of the client. This is
`httpx`'s documented behaviour and `httpx2` inherits it. So the implementer who
correctly follows `JOBVITE-CONTRACT.md` §2.3 as written ships a client that carries a session Jobvite
told us not to carry.

This is the same failure shape the design already names elsewhere and is worth
stating in its own right: **a requirement discharged by absence is not
enforceable, and cannot be tested without a positive control.** A test asserting
"we do not carry cookies" passes against a client that carries them if the test
never issues a second request, and passes vacuously against any client at all if
the underlying library happens not to persist. The property only becomes
testable once it is restated as an action.

## Decision

Restate the contract statement as an action rather than an omission:

> **Clear the cookie jar after every request.** The API is credential-
> authenticated per request and there is no session to carry, and the HTTP
> client's default is to persist and resend what Jobvite sets. Disabling that is
> an explicit step, not the result of leaving cookie handling alone.

U4 implements this in `JobviteClient.request`, in a `finally` block so that a
call which raised cannot leave a jar behind either. Two tests hold it:
`test_no_cookie_jar_is_carried_between_requests` asserts the property across
three requests, and
`test_positive_control_httpx2_DOES_carry_cookies_by_default` asserts that a bare
`httpx2.AsyncClient` **does** carry them - which is what stops the first test
becoming vacuous if a future `httpx2` changes its default. That second test
fails loudly with a message naming the clearing as possibly-dead-code rather
than silently going green.

## Consequences

The requirement becomes enforceable and is enforced. An implementer reading the
restated sentence cannot satisfy it by inaction, and the mutation harness row
M15 confirms that removing the single clearing line turns the suite red.

The positive control couples us to an `httpx2` implementation detail on purpose.
If `httpx2` ever stops persisting cookies by default, that test fails - and the
correct response is to read it, confirm the default changed, and decide whether
the clearing is still worth keeping, rather than to delete either one silently.
A control that fails when the world changes underneath it is doing its job.

`JOBVITE-CONTRACT.md` §2.3's `[RECORDED]` observations are untouched: the four
`AWSALBAPP-*` cookies and their `_remove_` values are real and this ADR does not
revisit them. Only the instruction derived from them changes.

## What this does NOT settle

- **Whether any Jobvite route requires a cookie.** Nothing observed suggests one
  does, and `JOBVITE-CONTRACT.md` §2.3 says there is no session to carry, but every response captured
  in `JOBVITE-CONTRACT.md` §10 is an **error** response captured without a
  credential. No success response has ever been observed
  (`JOBVITE-CONTRACT.md` §1), so "no route needs a cookie" remains an inference
  from the error path. If a credentialed run ever shows a route that breaks
  without one, this ADR is the thing to revisit first.
- **Whether clearing per request or disabling persistence outright is better.**
  `httpx2` exposes no documented switch to construct a client with no jar, so
  clearing is what is available today. If a later version offers one, preferring
  it would remove a line of per-request work; that is a refinement, not a
  correction, and it needs its own decision.
- **Anything about the other four response headers** `JOBVITE-CONTRACT.md` §2.3 records
  (`Server`, `X-JOBVITE-PROXY`, `Pragma`, `Cache-Control`). None is acted on by
  U4 and none is examined here.
- **The rate-limit finding in the same section.** `JOBVITE-CONTRACT.md` §2.3's "there is no rate-limit
  header of any kind" drives client-side throttling, which is U7's, and this ADR
  takes no position on it.
