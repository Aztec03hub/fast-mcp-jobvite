# ADR-0007: Use `httpx2`, the client FastMCP ships

**Status:** Accepted, reversing an earlier decision
**Type:** Deviation

## Context

`fastmcp 4.0.0b4` does not install `httpx` at all; it installs `httpx2`. An earlier revision chose
`httpx` on the belief that httpx2 was "a fork with a much smaller ecosystem" whose mocking support
was unproven, and that our credential-free test strategy could not rest on it.

**That characterisation came from a research note, was repeated without checking, and was false on
every point.**

## Decision

Write the Jobvite client against `httpx2`.

## Consequences

Verified: `httpx2` is authored by Tom Christie, httpx's own author, published under the **pydantic**
organisation, and its README states that Pydantic picked up stewardship because *httpx itself has
seen limited activity*. It ships regular releases where `httpx` ships only prereleases. **And it
ships `MockTransport` in the box**, which collapses the original argument entirely - the
credential-free test strategy needs no third-party mocking library.

Choosing `httpx` would have meant two HTTP stacks and two TLS surfaces in one image, a dependency
with limited upstream activity in the critical path, and a self-inflicted hazard: `except
httpx.HTTPError` can never catch a FastMCP-raised exception. Adopting httpx2 **removes** that hazard
rather than guarding it, so the module-confinement rule and its AST test were dropped as
unnecessary.

