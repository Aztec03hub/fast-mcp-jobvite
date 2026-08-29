# ADR-0029: §2.1's 1 MiB body limit is placed at a middleware this design does not have

**Status:** Accepted in part (orchestrator, 2026-08-29) - see the ruling
**Type:** Design change

> `DESIGN.md:165` puts *"Max total request body size — 1 MiB"* in §2.1's table of inbound
> structural limits, and ADR-0012 records it as **"already placed, at the middleware, and
> therefore C2 rather than C3"**. **There is no middleware here that sees a request body.**
> U14 implemented the other three limits and could implement only a *bounded relative* of this
> one, so the residue is written down rather than left inside a green.

## Context

### What U14 found, and how

U14 is the argument-layer completeness sweep. `utils/constraints.py` carried a recorded decision
that three of §2.1's four structural limits were deliberately absent, with the fourth annotated
`<- middleware, not this module`. U14 implemented the three and then went looking for the
middleware the fourth was assigned to.

`src/fast_mcp_jobvite/http_hardening.py` is the only middleware module in the tree. It holds
`RateLimitingMiddleware` and the client-id resolver, and **nothing in it reads or bounds a body
size.** Measured, on the tree at `bc0f958`:

```
$ grep -rn 'MiB\|1048576\|1024 \* 1024\|max_body\|body_size\|Content-Length' src/ scripts/
src/fast_mcp_jobvite/utils/constraints.py:171:#     Max request body    1 MiB      <- middleware, not this module
```

**One hit, and it is the comment saying the limit lives somewhere else.** The path resolves and the
other five patterns return zero against it, so this is a real absence rather than a bad search.

### The two places it could live, and why neither is discharged

1. **A `Content-Length` / streaming cap in the HTTP transport.** This is what `backend/input-
   validation.md:391-392` means by *"body size at the middleware"*, and it is the only placement
   that bounds a body **before** it is buffered — which is the point of a body cap. It does not
   exist.
2. **A cap on the serialised argument payload, inside the input models.** This is what U14 built
   (`MAX_PAYLOAD_BYTES`, `check_structural_limits`). It is real, it fails closed, and it has both
   a rejecting and an accepting arm.

**They are not the same control and the difference is not cosmetic.** A body that never becomes an
argument payload — a malformed frame, a body the JSON parser rejects, a body on a non-tool route,
a body on stdio where there is no HTTP request at all — is bounded by (1) and invisible to (2). By
the time (2) runs, the bytes have already been read and parsed.

### Why this is an ADR rather than a fix

`ci.yml`, `http_hardening.py` and the transport are not U14's files, and adding a body-size
middleware is a change to what the server mounts. More importantly, **the design places this
control and does not specify it**: it gives a number and a layer, and the layer it names does not
exist in §3's module list. Choosing where to put it, on which transports, and what a caller sees
when it fires are design decisions, and three units on this project have already been told to
refuse exactly that kind of silent choice.

## Decision

**Record that `DESIGN.md:165` is unplaced, and that `MAX_PAYLOAD_BYTES` is not it.**

`utils/constraints.py` bounds the serialised argument payload at 1 MiB, and its module comment
says in terms that this is not the middleware cap. `tests/test_arguments_sweep.py`'s §8 #9 size
arms cite the same caveat. **Nothing in the tree claims the body limit is discharged.**

The middleware half is filed as its own task and is not closed by U14.

## The alternative, and why it is rejected

**Declare `MAX_PAYLOAD_BYTES` the discharge of `DESIGN.md:165` and close the row.**

Rejected because it is the failure mode this repository has recorded most often: a control that is
*adjacent* to the required one, reported as the required one, with a green test beside it. §8 #9
asks for "a body past 1 MiB rejected"; a payload cap answers a question that resembles it. The
argument for rejecting the shortcut is `utils/constraints.py`'s own earlier note, written by U5
about these same limits: **"an unreachable limit is worse than absent: it reads as discharged."**
A *misplaced* limit reads as discharged in exactly the same way, and costs the next reader the
whole diagnosis a second time.

## Consequences

- **§8 #9 has four arms and only three of them test what §2.1's fourth row names.** The size arm
  tests the payload cap, which is what exists. The report says so.
- **The residue is bounded and stated**: bodies that never become argument payloads, on the HTTP
  transport. On stdio there is no request body and the row is vacuous by construction, which is
  itself worth writing down — a body cap "at the middleware" is a claim about one of two
  transports.
- **No threat row changes rating or disposition.** C3's rows stay where they are; this ADR moves
  no control, it records that one has no home.
- **If the decision is to build it**, the shape is a `Content-Length` check plus a streaming byte
  counter in the HTTP transport, refusing before the body is buffered, and it needs its own arm.
  That is a unit, not a patch, and it is why this is Proposed rather than applied.

## What this ADR does not settle

What a caller sees when a body cap fires. On the argument-payload path the answer is settled by
`DESIGN.md:181-190` — the framework raises, no problem object reaches the caller. A middleware
rejection is on the other side of that boundary and could return one; the registry's `422` row
exists and is reachable there. **That is a real choice and this ADR does not make it**, because
making it would be specifying the control rather than recording its absence.

## Ruling, 2026-08-29 - accepted on the refusal, CORRECTED on the claim

### Accepted, and this is the important half

**`MAX_PAYLOAD_BYTES` is NOT the discharge of `DESIGN.md:165`, and the row stays open.** The ADR's
reasoning for refusing the shortcut is exactly right and is the reason this project keeps finding
things: a control *adjacent* to the required one, reported as the required one, with a green test
beside it. U5's own earlier note about these same limits says it best - **"an unreachable limit is
worse than absent: it reads as discharged"** - and a misplaced limit reads as discharged in the same
way. `constraints.py` and the §8 #9 size arms both carry the caveat, so nothing in the tree claims
otherwise. That stands.

### Corrected: there IS a seat for it. It is unimplemented, not unplaceable.

The ADR's title and its central claim are that the body cap *"has no middleware to live in"*.
Measured against the locked framework rather than against our own stack, that is too strong:

```
$ uv run python -c "import inspect; from fastmcp import FastMCP; \
    print(list(inspect.signature(FastMCP.run_http_async).parameters))"
[..., 'path', 'uvicorn_config', 'middleware', 'json_response', ...]

$ # and the type of that parameter, from http_app's own source:
        middleware: list[ASGIMiddleware] | None = None,
```

**`ASGIMiddleware` sees the raw request body**; our own `Middleware` objects are MCP-protocol
middleware and see a parsed message, which is why `build_middleware` cannot host this. The two are
different layers and the ADR conflates "no middleware WE have" with "no middleware".

The seat is already plumbed: `__main__.py:438` calls `mcp.run(transport="http",
**http_run_kwargs(settings))`, and `http_run_kwargs` is the function that decides what the HTTP
transport is handed. A body cap is an `ASGIMiddleware` added to that dictionary.

**So the correct statement is:** `DESIGN.md:165` is undischarged and implementable, and U14 was right
not to claim it and right to refuse the shortcut. It is a gap, not an impossibility. This matters
because an impossibility invites a design change and a gap invites a unit, and those are different
pieces of work - **an impossibility claim needs a higher bar than the one that was met here.**

### Two consequences the implementing unit must not discover late

- **The cap is HTTP-only by construction.** There is no body on stdio, so `DESIGN.md:165` bounds
  nothing there. `constraints.py`'s payload bound is the only limit on the stdio path and remains
  necessary rather than redundant. **The two limits are not duplicates**, and whoever lands the
  middleware must not remove the payload cap as one.
- **Unlike the argument path, this rejection CAN return a problem object.** `DESIGN.md:181-190` says
  no problem object can be produced pre-dispatch, which is why every §8 #9 argument arm asserts a
  `ValidationError`; an ASGI middleware sits at the HTTP layer where the registry's 413/422 row is
  reachable. The ADR deliberately declined to make that call and was right to; the implementing unit
  makes it, and must pick the row deliberately rather than by whichever is nearest.

### What I did not settle

Whether `uvicorn_config` offers a body limit that would make an explicit middleware unnecessary. I
did not look; if it does, that is a cheaper answer and the implementing unit should find it before
writing one.
