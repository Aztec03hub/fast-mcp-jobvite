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
| D6 | Full RFC 9457 problem object, delivered via `ToolError`. No envelope. | Settled | Standard + Phil ruling |
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

## D6 - full RFC 9457, delivered via `ToolError`

**Decision.** Tool failures raise `ToolError`. Its structured payload is a complete RFC 9457
problem object carrying all seven mandated fields: `type`, `title`, `status`, `detail`,
`instance`, `request_id`, `timestamp`. The `build_response(success=, error=)` envelope is not
used anywhere in this repository.

**This was briefly marked provisional. That was my error.** Phil's standing ruling, 2026-08-27:
where a reference project does not follow a standard, we follow the standard and do it right,
and the only thing that overrides a standard is a specifically in-scope numbered ADR. A
reference project is a source of patterns, never of authority. There was no dilemma here to
adjudicate - the hierarchy already settled it, and `fast-mcp-jira` doing otherwise is a finding
about `fast-mcp-jira`.

**The two open questions, now resolved rather than deferred.** RFC 9457 requires `type` and
`instance` to be URIs, and MCP has no request URI to hang them on:

- **`type`** is a relative, stable, slugged reference as `architecture/error-contract.md:210-211`
  already requires: `/problems/<slug>`, for example `/problems/jobvite-auth-failed`. The
  standard's own choice of relative references is what makes this transport-independent, so
  nothing needs inventing.
- **`instance`** identifies the specific occurrence. With no request URI available, it is a URN:
  `urn:fast-mcp-jobvite:invocation:<request_id>`. A URN is a URI, it is stable, and it
  identifies exactly one tool invocation. This is an adaptation of the transport, not a
  deviation from the contract, so it needs no ADR.
- **`status`** carries the upstream Jobvite HTTP status where one exists, and the
  semantically-equivalent code otherwise (400 for input validation, 503 for an upstream 5xx per
  `backend/error-handling.md:411-424`).

**Why `ToolError` is the delivery mechanism and not a competing design.** `ToolError` is how
MCP signals failure - it is what makes a client observe `isError: true`. That is protocol
plumbing and is orthogonal to error *shape*. Returning a success-shaped dict on failure, as the
reference project does, means every upstream 4xx is reported to the model as a success. The two
requirements compose; they never conflicted.

**Consequence.** A reviewer should fail this repo if any tool returns a failure as a normal
result, if any problem object is missing one of the seven fields, or if a stack trace or
upstream detail leaks into `detail`.
