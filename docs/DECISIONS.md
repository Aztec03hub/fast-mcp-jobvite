# Decision log (pre-freeze)

Decisions taken during design. At design freeze each of these becomes a numbered ADR in
`docs/adr/`, after which only a new numbered ADR may change project design.

Sources: `docs/research/FASTMCP.md`, `docs/research/STANDARDS.md`, `docs/research/JOBVITE-API.md`.

| # | Decision | Status | Authority |
|---|---|---|---|
| D1 | Target `fastmcp==4.0.0b4` and the 2026-07-28 sessionless MCP spec | Settled | Phil, 2026-08-27 |
| D2 | Python floor `>=3.12` | Settled | Standard |
| D3 | `ai/` domain standards bind this repo by intent | Settled | Orchestrator ruling |
| D4 | In-process rate limiting, opting out of the mandated Redis token bucket | Settled, needs ADR | Orchestrator ruling |
| D5 | `error-contract.md` outranks `agentic-coding-standard.md` on error shape | Settled | Standard self-declaration |
| D6 | `ToolError` carrying an RFC 9457 problem object | Provisional | Orchestrator, under review |
| D7 | MIT, `Copyright (c) 2026 evolv Consulting` | Settled | Phil, 2026-08-27 |
| D8 | Canonical on `evolvconsulting`, auto-mirrored to the personal fork | Settled | Phil, 2026-08-27 |
| D9 | Commit `type(scope): description` + `Refs:`; semantic PR titles | Settled | Orchestrator ruling |
| D10 | v1.0 ships tools for the five EVIDENCED Jobvite operations only | Settled | Orchestrator ruling |
| D11 | Default transport is stdio; HTTP is opt-in | Settled | Orchestrator ruling |
| D12 | Live-credential tests are a separate opt-in suite, never skipped in CI | Settled | Orchestrator ruling |
| D13 | Licence choice reopened pending an org-wide survey | OPEN | Phil, 2026-08-27 |

---

## D1 - fastmcp 4.0.0b4, not 3.4.7

**Decision.** Build against `fastmcp==4.0.0b4` and MCP spec revision `2026-07-28`.

**Context.** Research recommended the opposite: pin the stable `3.4.7`, which speaks spec
`2025-11-25`, and revisit at 4.0 GA. The latest spec revision is only reachable through the
4.0 beta line, which also forces `mcp>=2.0`, `pydantic>=2.12`, Starlette 1.x and swaps
`httpx` for `httpx2`.

**Why the reversal.** Phil's call, on appetite rather than analysis: we are deliberately early
adopters. Bugs found in the beta are to be characterised precisely, reproduced minimally, and
reported upstream as issues or PRs rather than worked around silently.

**Consequences.** Every 4.0 claim in `FASTMCP.md` came from the upgrade guide rather than
executed code, so all of it is unverified until the runtime spike lands. Two specific risks:
whether `fastmcp.server.lifespan` survives into 4.0 is unknown, and the `httpx` -> `httpx2`
swap reaches the Jobvite client directly.

## D3 - the `ai/` standards bind, by intent

**Decision.** `ai/tool-calling.md` and `ai/agent-guardrails.md` bind this repository.

**Context.** `ai/README.md:22-33` scopes the domain to product code that *calls* foundation
models. This server calls none; models call it. Read literally, the two documents that contain
the estate's only rules on how to define a tool do not reach the one component that is
entirely tools.

**Why.** The risk model those documents govern is tool-definition safety, destructive-operation
gating, and injection through attacker-authored content. An MCP server is precisely that
surface with the direction of the call reversed. Excusing ourselves on a scoping technicality
would ship a tool catalogue for a model, governed by nothing.

**Consequence.** Obligations B9-B26 apply in full, including typed schemas per tool,
default-deny on destructive operations, and treating candidate-authored content as hostile.

## D4 - in-process rate limiting

**Decision.** Rate limit in process. Do not require Redis.

**Context.** `backend/rate-limiting.md:355-356` mandates a Redis token bucket on every
public-facing surface and forbids in-memory limiting, with an ADR required to opt out.

**Why.** The standard's own stated rationale is desynchronisation across replicas. A
single-process MCP server has no replicas to desynchronise. The standard also never defines
"public-facing surface" (gap G4), so a localhost developer tool and an internet-hosted service
carry identical obligations under its text.

**Consequence.** This needs a real ADR at freeze, not a silent omission. A reviewer finding
in-memory limiting with no ADR is a legitimate finding.

## D10 - ship only the evidenced Jobvite surface

**Decision.** v1.0 exposes tools for exactly five operations: `GET /api/v2/candidate`,
`POST /api/v2/candidate`, `GET /api/v2/job`, `POST /api/v2/task`, and the v1 job feed. No tool
is written for any other Jobvite resource.

**Context.** Jobvite publishes no public API documentation. `developer.jobvite.com` never
existed - the Wayback Machine holds zero snapshots, and a third-party client citing it
fabricated the citation. `help.jobvite.com` is login-gated and returns 401. No OpenAPI exists.
A live probe of ~180 unauthenticated requests mapped 17 v2 resources by distinguishing 401
(exists) from 404 (does not), but only the five above have a known request and response
contract. The rest are route names.

**Why.** A tool built against a guessed schema fails in the user's hands rather than in ours,
and it fails after the model has already told the user it would work. Five tools that work is a
better product than seventeen where twelve are speculative. This also satisfies the standards'
minimal-allow-list rule directly: an unused or unreliable tool is attack surface.

**Consequence.** The README must state the scope and the reason plainly, so the limitation
reads as a decision rather than an oversight. Expanding scope requires either credentials or
documentation access, both of which are logged as blockers.

## D11 - stdio by default, HTTP opt-in

**Decision.** The server runs stdio unless configured otherwise. HTTP is selected at runtime.

**Why.** A public repo serves two audiences: local client users (Claude Desktop, Claude Code,
Cursor) for whom stdio must work with no configuration, and hosted deployments that need HTTP.
`fast-mcp-jira` hardcodes HTTP with no stdio path at all, which locks out every local client.
The MCP Registry's package model also assumes local execution.

## D12 - live tests are opt-in, not skipped

**Decision.** Tests requiring real Jobvite credentials live in a separate suite excluded from
the default selection. They are never marked `skip` in the default run.

**Why.** We hold no credential and no sandbox exists, so the default suite must be green
without network access. But the testing standard treats a SKIP as a FAIL and requires a skip
count of zero, so the usual `skipif` idiom would turn CI red. Exclusion by selection satisfies
both: CI has zero skips, and the live suite still exists for whoever holds a key.

## D6 - `ToolError` carrying an RFC 9457 problem object (PROVISIONAL)

**Decision, provisional.** Tool failures `raise ToolError`, whose structured payload is an
RFC 9457 problem object carrying all seven mandated fields.

**Context.** `architecture/error-contract.md` mandates RFC 9457 `application/problem+json` and
explicitly retires the `build_response(success=, error=)` envelope that `fast-mcp-jira` uses.
But MCP tools return protocol results, not HTTP responses, and FastMCP's native failure signal
is `ToolError` - which is what makes a client see `isError: true`. Returning a success-shaped
dict on failure, as `fast-mcp-jira` does, reports every upstream 4xx as a success.

**Why provisional.** Whether this satisfies B1-B8 *as written* is out for review. If it cannot
be reconciled with the letter of the standard, it needs an ADR rather than a clever reading.

**Open question.** RFC 9457 requires `instance` and `type` as URIs. What those mean for a
transport with no request URI is unresolved.
