# ADR-0032: a fifth middleware runs that the design never assessed

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> `FastMCP.__init__` appends `DereferenceRefsMiddleware()` whenever `dereference_schemas` is true,
> and it defaults to true. The live stack on both transports is **five** middleware, not the four
> `build_middleware` returns. §7.7 enumerates three adopted and five "not used", and this one is in
> neither group - so `DESIGN.md:1730`'s C2-T1 ruling, *"No adopted middleware mutates request or
> response payloads"*, is not false about it. It is **unreached**, which is worse, because the row
> reads as covering the stack.

## Context

### Measured, at `a38013f`

```
$ srv = build_server(Settings()); [type(m).__name__ for m in srv.middleware]
RequestIdMiddleware
TimingMiddleware
StructuredLoggingMiddleware
RateLimitingMiddleware
DereferenceRefsMiddleware          <- framework-injected, never adopted
count=5
```

`DESIGN.md:1725` names the stack the C2 rows analysed as exactly *"(§7.7: `Timing`,
`StructuredLogging`, `RateLimiting`)"*. **The threat model was written against a stack that is not
the one that runs.**

And §7.7's own standing rule is that *"on this framework a middleware's default is not a safe
starting point"*. This one arrived **by** default and was never assessed - the rule naming the
hazard did not catch the instance of it.

### What it actually does to us today, and the trap in measuring it

Dereferencing inlines `$ref` in published tool schemas. So the question that decides this ADR is
whether our models produce any.

**AND THE OBVIOUS MEASUREMENT IS THE WRONG ONE, WHICH I MADE FIRST.** Reading the published schemas
through a real `Client` gives zero `$ref` - but that is true *whether or not the models nest*,
because removing them is the middleware's entire job. Measured against a deliberately nested
`SearchJobsInput`:

```
MODEL      $ref count: 1
PUBLISHED  $ref count: 0
```

**A zero on the published side reports the middleware working, not the models being flat.** It is
the reassuring reading of a measurement taken downstream of the thing that guarantees it.

The measurement that answers the question is on the models, upstream of the middleware. All five,
at `a38013f`:

```
  candidates  CreateCandidateInput     $defs=False  $ref=0
  candidates  GetCandidateInput        $defs=False  $ref=0
  candidates  SearchCandidatesInput    $defs=False  $ref=0
  jobs        GetJobFeedInput          $defs=False  $ref=0
  jobs        SearchJobsInput          $defs=False  $ref=0
```

Every field is a bounded scalar, so nothing nests. **The middleware is a live no-op** - it runs on
every request and has nothing to inline.

## Decision

**Adopt it. §7.7 gains a fourth adopted middleware, and C2 gains a row.**

The alternative - passing `dereference_schemas=False` in `build_server` to keep the stack the design
describes - is rejected. It is a behaviour change that **buys nothing measurable**: the middleware
alters no published schema today, so turning it off changes no output. And it points the wrong way:
dereferencing exists because many MCP clients do not resolve `$ref`, so disabling it trades a real
future compatibility property for cosmetic agreement between a document and a stack. **Fix the
document, which is wrong, not the stack, which is fine.**

### C2 gains: *"the schema-dereferencing middleware rewrites published tool schemas"*

Ruled **low**, with the reasoning stated rather than assumed: it rewrites **schemas**, never request
or response payloads, so it cannot carry caller data anywhere. It is downstream of
`RequestIdMiddleware`, so anything it logs is correlated. It has no configuration we set and no
credential.

## Consequences

### THE NO-OP IS A PROPERTY OF TODAY'S MODELS, NOT OF THE MIDDLEWARE

This is the part that decays silently. `$ref` appears the moment any input or output model **nests** -
a sub-model, an enum, a discriminated union. U14 landed a shared `InboundModel` base and its tests
already carry a `NestedProbe`, so nesting is nearer than it looks. On that day the middleware stops
being a no-op and starts rewriting what every caller sees, and **nothing would say so.**

**So the measurement above becomes an assertion, on the side that can actually fail.**
`test_no_input_model_produces_a_ref_for_the_middleware_to_inline` walks every `*Input` model under
`tools/` - discovered by `pkgutil`, not listed - and requires each to be `$ref`-free. Its failure is
not a defect to route around: it is the signal that this ADR's central fact has expired and C2's new
row needs re-reading. That reason is written into the test, because a future reader's cheapest move
is to update the expected number.

**The first version of that test read the PUBLISHED schemas and could not fail.** It was written,
run green, then amputated by nesting a model - and it stayed green, because the middleware inlined
the `$ref` before the assertion saw it. Both arms are proved now: nesting a model fires the
tripwire, and breaking the discovery fires the population guard rather than passing on an empty
set.

That is a tripwire, not a prohibition. A model that legitimately nests is fine; discovering it
after the fact is not.

### `FRAMEWORK_INJECTED_MIDDLEWARE` stays, and is not the same guarantee

`tests/test_http_hardening.py` already pins this class so a framework bump injecting a **second** one
is a red test rather than a silent addition. That pins the roster. It says nothing about behaviour,
and this ADR is the behaviour half. Keep both.

## What this ADR does not claim

**Not that anything was exposed.** A no-op middleware rewrote nothing, on either transport. The
finding is that the threat model described a stack that does not exist, and a row read as covering
something it never reached - **which is exactly the shape of "an unreachable limit reads as
discharged" that ADR-0029 turned on**, applied to a threat row rather than a constraint.
