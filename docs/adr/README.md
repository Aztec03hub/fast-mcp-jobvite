# Architecture Decision Records

An ADR here does **two different jobs**, and they must stay distinguishable:

1. **`Deviation`** - records a decision that departs from a `priority: required` standard, or that a
   reviewer would otherwise be right to file as a defect. **This is independent of the freeze.** A
   deviation is recorded when it is decided; that is why eleven ADRs exist against a design that is
   not yet frozen, which is correct rather than contradictory.
2. **`Design change`** - after the freeze, an ADR is the only instrument that may change
   `docs/DESIGN.md`. This job begins at the freeze and not before.

**Every ADR from 0012 onward carries a `Type:` field** - `Deviation`, `Design change`, or `Both` -
because after the freeze "is this a deviation or a design change?" must have an answer, and the
freeze rule's teeth depend on telling them apart. **ADR-0001 to ADR-0011 are all `Deviation`**, recorded
before any freeze. `DESIGN.md` §13 states the same split.

Format: Status, Type, Context, Decision, Consequences. Every ADR cites the clause it deviates from
at its `file:line`, and says what evidence the decision rests on.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-target-fastmcp-4-beta.md) | Target `fastmcp 4.0.0b4` and the sessionless spec, not the stable line | Accepted |
| [0002](0002-in-process-rate-limiting.md) | In-process rate limiting instead of the mandated Redis token bucket | Accepted |
| [0003](0003-problem-json-on-mcp-transport.md) | `problem+json` cannot be set on an MCP tool error | Accepted |
| [0004](0004-exclude-response-limiting-middleware.md) | `ResponseLimitingMiddleware` excluded; size bounded in-tool | Accepted |
| [0005](0005-ai-domain-binds-by-intent.md) | The `ai/` standards domain binds this repository by intent | Accepted |
| [0006](0006-single-main-branch.md) | Single `main` branch rather than the mandated `main`+`develop` | Accepted |
| [0007](0007-httpx2-not-httpx.md) | `httpx2` rather than `httpx` | Accepted |
| [0008](0008-eeo-fields-excluded.md) | Special-category EEO fields excluded from output models | Accepted |
| [0009](0009-approver-identity-unknowable.md) | Approver identity cannot be recorded; caller identity can | Accepted |
| [0010](0010-coverage-targets-remapped.md) | Coverage targets remapped from the standard's category model | Accepted |
| [0011](0011-three-log-producers-not-one.md) | Three log producers per invocation, not the mandated one | Accepted |
| [0012](0012-shared-inbound-constraints-module.md) | A shared `utils/constraints.py` for the inbound constraints | **Proposed** |
| [0013](0013-secret-absence-case-needs-a-pairing.md) | §8's secret-absence case needs a positive pairing, as the audit cases have | **Proposed** |
| [0014](0014-c8-i1-empty-values-is-wrong.md) | C8-I1 says `.env.example` has empty values; seven of fifteen carry one | **Proposed** |
| [0015](0015-licence-gate-is-a-deny-list.md) | The licence gate is a deny-list; four packages sit on neither list | Accepted |
| [0016](0016-setup-uv-v5-not-the-standards-v4.md) | `astral-sh/setup-uv@v5`, where the standard pins `@v4` | Accepted |

## Acknowledged non-conformances without an ADR

One obligation is knowingly unmet and deliberately has no ADR, because an ADR would imply a
decision we are not entitled to make:

- **`threat-modeling.md:146`** requires mitigations to become numbered functional requirements.
  The corpus contradicts itself about the ticket prefix - `agentic-coding-standard.md` expects
  `FEAT/FR/BUG/TECH`, `quality-gates.md` adds `TECH`, `development-workflow.md:166` expects
  layer-prefixed `[FE-001]`, and this work is tracked as `EC-###`. **Inventing a prefix to satisfy
  a clause the standards cannot agree on would move the defect rather than fix it.** Recorded here
  so it is visible rather than skipped.

