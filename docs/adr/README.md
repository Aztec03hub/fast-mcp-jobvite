# Architecture Decision Records

Each ADR records a decision that deviates from a `priority: required` standard, or that a reviewer
would otherwise be right to file as a defect. **After the design freeze, an ADR is the only
instrument that may change `docs/DESIGN.md`.**

Format: Status, Context, Decision, Consequences. Every ADR cites the clause it deviates from at its
`file:line`, and says what evidence the decision rests on.

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

## Acknowledged non-conformances without an ADR

One obligation is knowingly unmet and deliberately has no ADR, because an ADR would imply a
decision we are not entitled to make:

- **`threat-modeling.md:146`** requires mitigations to become numbered functional requirements.
  The corpus contradicts itself about the ticket prefix - `agentic-coding-standard.md` expects
  `FEAT/FR/BUG/TECH`, `quality-gates.md` adds `TECH`, `development-workflow.md:166` expects
  layer-prefixed `[FE-001]`, and this work is tracked as `EC-###`. **Inventing a prefix to satisfy
  a clause the standards cannot agree on would move the defect rather than fix it.** Recorded here
  so it is visible rather than skipped.

