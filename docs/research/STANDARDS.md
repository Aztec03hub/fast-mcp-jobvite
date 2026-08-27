# Binding evolv-coder-standards for `fast-mcp-jobvite`

**Task:** R3 · **Author:** standards-research · **Date:** 2026-08-27

**Subject:** a NEW standalone Python FastMCP server exposing the Jobvite recruiting
SaaS REST API as MCP tools. No database, no frontend, no Alembic, no ECS deployment.

**Hosting (revised 2026-08-27):** canonical at **`evolvconsulting/fast-mcp-jobvite`** —
an **evolv-owned, PUBLIC** repository — mirrored to `Aztec03hub/fast-mcp-jobvite`.
This replaces the original "Phil's personal repo" framing. Org ownership makes the
company standards bind more firmly, and adds a class of obligation (public disclosure,
outbound licensing, org attribution) that a personal repo would not carry.
**§6 covers those obligations and supersedes the earlier gap note G2.**

**Standards tree read:** `/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/`
All paths below are relative to that directory unless prefixed otherwise.

## Method and authority note (read this first)

The brief states that `priority: required` in the YAML frontmatter is the only
authority marker. I extracted the frontmatter priority of **all 172** markdown files
in the tree. The result materially changes how this report is structured:

| priority | count |
|---|---|
| `required` | 133 |
| `recommended` | 5 |
| `optional` | 8 |
| absent (generated `index.md` / `log.md`) | 26 |

**Every substantive standard in the repository is `priority: required`.** The marker
therefore establishes *that* a document binds, but does **not** discriminate *which
documents bind this project*. `required` is not a scope statement. Applicability here
is decided by each file's own `applicable_to` frontmatter and its Scope section — a
document whose scope is "Next.js components" does not reach a Python MCP server
merely because it is marked `required`.

I have flagged this in §4 as a gap: there is no standard, and no field in the
frontmatter, that says which subset of a 133-file `required` corpus binds a
non-flagship repository.

**TIER-1 file existence:** all 16 standards paths in the brief exist on disk and were
opened in full. The MUST-READ index (`MUST-READ-DOCS.md:44-45`) lists two further
TIER-1 entries the brief omitted — `repos/evolv-coder/docs/adrs/README.md` and
`repos/evolv-coder/docs/adrs/adr-ec-350-04-public-share-rate-limit.md`. Both exist;
both are evolv-coder product ADRs and are dismissed in §3. **No TIER-1 path was
missing.**

Beyond TIER-1 I read, in whole or in the governing sections:
`architecture/security.md`, `architecture/observability.md`,
`architecture/authentication.md`, `architecture/gdpr-data-rights.md`,
`architecture/adr/adr-template.md`, `backend/tech-stack.md`, `backend/testing.md`,
`backend/resilience.md`, `backend/input-validation.md`, `ai/output-handling.md`,
`ai/README.md`, `devops/quality-gates.md`, `devops/supply-chain-security.md`,
`devops/git-workflow.md`, `devops/twelve-factor.md`,
`documentation/readme-standard.md`, `documentation/changelog-standard.md`.

---

## 1. Binding checklist

Each item is written so a reviewer can pass/fail the repository against it.

### Error contract

**B1. Every error surface uses the RFC 9457 Problem Details object; no custom
envelope.**
`architecture/error-contract.md:204` — *"1. **RFC 9457 shape**: All errors use the
Problem Details object. No custom envelopes."*
Fail condition: any tool or endpoint returns `{"success": false, "error": ...}`,
`{"detail": ...}`, or `{"message": ...}`.

> **Design note, not optional.** `fast-mcp-jira`'s `build_response(success, error=...)`
> helper is exactly the v1.0.0 envelope that `error-contract.md:200` (`**Supersedes**:
> v1.0.0 (custom error envelope)`) retired. Copying that helper into
> `fast-mcp-jobvite` starts the repo in violation of B1. See §2/A1 for the adaptation.

**B2. Every error carries all seven elevated fields.**
`architecture/error-contract.md:66` — *"We elevate `type`, `title`, `status`,
`detail`, `instance`, `request_id`, and `timestamp` to required for consistency
across our services."*
Fail condition: an error payload missing any of the seven.

**B3. HTTP error responses set `Content-Type: application/problem+json`.**
`architecture/error-contract.md:44` — *"All error responses MUST use the media
type:"* (followed by `application/problem+json`).

**B4. No stack traces or internal detail in any error returned to a caller.**
`architecture/error-contract.md:206` — *"3. **No stack traces**: 500 errors return a
fixed message. Stack traces are logged, not returned."*
Reinforced at `backend/error-handling.md:383` — *"Never leak raw exception messages
from third-party libraries to API consumers"* — and `:396`, which marks
`raise BadRequestException(str(exc))` as **BAD**.
Fail condition: any handler that passes `str(exc)` from `httpx` or the Jobvite client
into a caller-visible field.

**B5. `type` URIs are relative `/problems/<slug>` and are a frozen contract.**
`architecture/error-contract.md:210` — *"7. **Type URIs are stable**: Once published,
a `type` URI is a contract. Changing it is a breaking change."*
`architecture/error-contract.md:211` — *"8. **Relative type URIs**: Use
`/problems/<slug>`, not absolute URLs."*

**B6. Exceptions derive from a typed hierarchy with `problem_type` + `title` class
attributes; ad-hoc raises pass both explicitly.**
`backend/error-handling.md:205` — *"When raising `AppException` directly for
domain-specific errors, always provide `problem_type` and `title`"*, with the BAD
example at `:217` (`raise AppException(status_code=422, detail="File is empty")`).
The canonical subclass set is `backend/error-handling.md:127-200` (`NotFoundException`,
`ForbiddenException`, `UnauthorizedException`, `ConflictException`,
`BadRequestException`, `UnprocessableEntityException`, `InvalidCursorException`,
`ExternalServiceException`, `RateLimitException`, `ServiceUnavailableException`).

**B7. Upstream (Jobvite) failures map to typed domain exceptions, not raw
pass-through.** `backend/error-handling.md:411-424` maps `>=500` →
`ServiceUnavailableException`, `>=400` → `ExternalServiceException`,
`httpx.TimeoutException` and `httpx.ConnectError` → `ServiceUnavailableException`.
Fail condition: a Jobvite 4xx surfacing as a bare 500 or as an unmapped exception.

**B8. `fastapi.HTTPException` is never raised directly.**
`backend/python.md:126` — *"**Do not raise `fastapi.HTTPException` directly.** FastAPI
serializes it as `{"detail": "..."}`, which violates the [error contract] (RFC 9457
ProblemDetail)."*

### Tool definition (the core of this project)

**B9. Every MCP tool has an explicit typed input schema derived from a Pydantic
model. No free-form parameters.**
`ai/tool-calling.md:48` — *"**Every tool has an explicit, typed input schema** (JSON
Schema, derived from a Pydantic model). No free-form / untyped tool parameters; the
schema is the contract the model is given and the contract you validate against."*
Fail condition: any tool parameter typed as bare `str`/`dict`/`Any` where a
constrained type is expressible.

**B10. Schema fields are constrained — enums for closed sets, bounded numerics, max
string lengths, explicit required/optional.**
`ai/tool-calling.md:52-54` — *"Schema fields are **constrained**: enums for closed
sets, bounded numeric ranges, max string lengths, required vs optional made explicit.
Loose types (bare `string`, `object`) are attack surface."*

**B11. Model-supplied arguments are validated against the schema before the tool body
runs; the body receives the typed object, never the raw dict.**
`ai/tool-calling.md:97-99` — *"**Never pass raw model arguments through to a tool.**
Parse the model-supplied JSON against the tool's schema first; the tool body receives
the **validated, typed object**, never the raw dict/string."*

**B12. A schema violation fails closed with a typed tool error and never reaches the
tool body — and this path is unit-tested.**
`ai/tool-calling.md:100` — *"**Reject on violation** — return a typed tool error back
to the model so it can correct, rather than coercing or best-effort-parsing malformed
input into the call."*
`ai/tool-calling.md:187-189` — *"The per-tool argument-rejection path is unit-tested:
a schema violation must fail closed, not reach the tool body."*
Fail condition: no test asserting that a malformed argument is rejected before the
Jobvite call is issued.

**B13. Tools validate their own inputs independently of the caller.**
`ai/agent-guardrails.md:57-58` — *"**Tools validate their own inputs** independently
of the model; never execute raw model-supplied arguments"*.

**B14. Tool outputs returned to the model are wire-shaped snake_case.**
`ai/tool-calling.md:59-60` — *"Tool **outputs** intended for the model are
wire-shaped **snake_case**, consistent with [`../architecture/error-contract.md`]"*.

**B15. Tool result size is bounded to a documented maximum before return.**
`ai/tool-calling.md:153-155` — *"**Bound result size** before returning it to the
model (truncate to a documented max); an oversized result is both an injection
surface and a context/cost blowout."*
Fail condition: a Jobvite list endpoint whose full response is returned unbounded.
The max must be **documented**, not merely present in code.

**B16. Tool name and description are reviewed like prompts — clear, minimal, no
secrets.** `ai/tool-calling.md:55-57` — *"Tool name + description are part of the
prompt and are **reviewed like prompts** — clear, minimal, no secrets."*

**B17. Every tool invocation is logged with tool name, validated arguments (PII
redacted), result status, latency, and the request correlation id, in snake_case,
with no secrets.**
`ai/tool-calling.md:171-173` and `ai/agent-guardrails.md:121-123` — *"**Log every tool
invocation** with: tool name, validated arguments (PII redacted), result status,
latency, the approval decision if gated, and the request correlation id."*
`ai/tool-calling.md:178-179` — *"Tool logs are wire-shaped **snake_case**
(`tool_name`, `request_id`, `result_status`) and never contain secrets or raw
credentials."*
**PII redaction is not discretionary here** — Jobvite tool arguments and results are
candidate personal data (names, emails, phone numbers, résumés).

**B18. Destructive / irreversible Jobvite operations are default-deny and require an
explicit approval gate; they fail closed with no approver.**
`ai/agent-guardrails.md:70-73` — *"**Default-deny destructive operations.** Any
irreversible or high-blast-radius action (delete, financial transaction, outbound
message to a third party, infra change, mass update) MUST pause for human approval
before execution. Fail closed: no approver, no action."*
`ai/tool-calling.md:140` classifies *"Destructive / irreversible (delete, payment,
send, deploy)"* as **"Approval gate required"**.
Concretely for Jobvite: rejecting a candidate, deleting a requisition, and **any tool
that sends an outbound message to a candidate** are gated. Reads are not.

**B19. Write tools are idempotent or guarded so a retry cannot double-apply.**
`ai/tool-calling.md:133-134` — *"Tools are **idempotent or guarded** so a retry (see
[`./resilience.md`]) cannot double-apply a side effect."*

**B20. The exposed tool set is a minimal explicit allow-list, not a kitchen sink.**
`ai/agent-guardrails.md:47-49` — *"**Minimal tool set.** Bind to an agent only the
tools its task requires. Do not expose a broad "kitchen-sink" toolbox; an unused tool
is attack surface. The callable-tool list is an explicit allow-list per agent."*
Fail condition: tools generated wholesale from the Jobvite API surface with no
curation. (`fast-mcp-jira` ships 47 tools; that count is a warning sign, not a
target.)

**B21. Credentials are scoped, never scoped by prompt.**
`ai/agent-guardrails.md:50-53` — *"**Minimal scope per tool.** Each tool runs with the
narrowest credentials / permissions that work ... Scope the *credential*, never rely
on the prompt to keep the model in bounds."*

**B22. Bounds are configuration, not constants buried in code.**
`ai/agent-guardrails.md:106-107` — *"Bounds are configuration, not constants buried in
code, so they can be tuned per agent and environment."*
Applies to B15's result cap, timeouts, and retry budgets.

**B23. Adversarial cases are merge-gating tests.**
`ai/tool-calling.md:185-187` — *"Adversarial tool cases — invalid/over-budget
arguments, a tool result carrying an injection payload, an unbounded-loop attempt —
are **merge-gating** tests"*.
`ai/prompt-injection.md:138-139` — *"Maintain red-team cases for injection and
jailbreaks as **merge-gating** tests in the eval suite"*.
Fail condition: these tests exist but are not wired to a required CI check.

**B24. Jobvite response content is treated as untrusted indirect input.**
`ai/prompt-injection.md:49-50` — *"Every byte that reaches a model is **untrusted
data**, whether it came from an end user or from the system itself."*
`ai/prompt-injection.md:74-75` — *"Wrap untrusted content in explicit delimiters and
frame it as inert data"*.
This is the sharpest real risk in this project: a candidate-authored résumé or cover
letter stored in Jobvite is attacker-authored text that this server hands to a model.

**B25. Input size and encoding limits are enforced before dispatch.**
`ai/prompt-injection.md:124-125` — *"Enforce input size/encoding limits before
dispatch; reject control characters and oversized payloads"*.

**B26. Secrets and PII are redacted before anything reaches a trace/log backend.**
`ai/prompt-injection.md:127-128` — *"**Redact secrets and PII from untrusted input
before it reaches the trace backend**"*.

### Input validation

**B27. All request/argument models set `ConfigDict(strict=True)`.**
`backend/input-validation.md:37` — *"All request models MUST enable strict mode to
prevent silent type coercion"*. Rule 1 at `:387`.

**B28. Every string field declares an explicit `max_length`.**
`backend/input-validation.md:64` — *"All string fields MUST declare an explicit
`max_length`."* Defaults table at `:66-76` (email 320, url 2048, identifier 64,
free-text 10 000, name/title 100).

**B29. Identifier fields use regex `pattern` constraints.**
`backend/input-validation.md:389` — *"3. **Regex for identifiers** — slugs, handles,
UUIDs must use `pattern` constraints"*.

**B30. Nesting depth ≤ 5, list items ≤ 1 000, dict keys ≤ 100, body ≤ 1 MiB.**
`backend/input-validation.md:221-226` (limits table); enforcement rules at `:391-392`.

**B31. Fail closed — reject anything that cannot be fully validated.**
`backend/input-validation.md:396` — *"10. **Fail closed** — reject requests that
cannot be fully validated"*.

### Outbound calls to Jobvite (resilience)

**B32. Every outbound call sets an explicit connect and read (or total) timeout; no
SDK default.** `backend/resilience.md:71-73` — *"**Every** outbound call MUST set an
**explicit connect and read (or total) timeout**. No call may rely on the client/SDK
default — many default to *no* timeout or a multi-minute one."*

**B33. Timeouts are shorter than the inbound request's own deadline.**
`backend/resilience.md:74-76`.

**B34. Retries use `tenacity` with exponential backoff **and jitter**, a bounded stop
condition, and a total budget ≤ the inbound timeout.**
`backend/resilience.md:92-98` — *"Wrap retryable calls with `tenacity` using
**exponential backoff WITH jitter**"* … *"The total retry budget MUST be ≤ the inbound
request timeout"*.

**B35. Retry only on connection errors, timeouts, HTTP 429 and 5xx — never on a
blanket exception.** `backend/resilience.md:99-101` — *"**Never** retry on a
blanket"* exception. Retry table at `:130`.

**B36. Non-idempotent writes are not blindly retried.**
`backend/resilience.md:143-145` — *"A **non-idempotent `POST`** (create, charge, send)
MUST NOT be blindly"* retried.

**B37. One circuit breaker per dependency, using `circuitbreaker`; caller (4xx)
errors do not trip it.** `backend/resilience.md:159-161`, `:167-169` — *"a caller
error (4xx) is not an outage and MUST NOT"* trip the breaker.

**B38. Composition order is timeout (innermost) → retry → circuit breaker
(outermost).** `backend/resilience.md:209` — *"**timeout (innermost) → retry →
circuit breaker (outermost)**"*, with `:216` — *"Never let a retry loop sit outside
the breaker"*.

**B39. Retries and breaker transitions are logged with the correlation field, never
silent.** `backend/resilience.md:226` — *"`request_id` correlation field. Never retry
or trip silently."*

### Correlation and logging

**B40. The correlation triple is used verbatim: header `X-Request-ID`, log field
`request_id`, ContextVar `request_id_var`.**
`ai/tool-calling.md:173-177` and `ai/agent-guardrails.md:124-127` both mandate *"the
canonical correlation triple — header `X-Request-ID`, log field `request_id`,
ContextVar `request_id_var`"*. Reinforced by `architecture/observability.md:626`.

**B41. A caller-supplied `X-Request-ID` is validated as a UUID v4 and replaced if
invalid.** `backend/request-middleware.md:38` — *"2. **Validate** the value as a UUID
v4 format (reject non-UUID values)"*; rationale at `:60` — without validation a caller
can inject *"newlines for log forging, long strings for log bloat"*.
Rule 2 at `:143` — *"**Always validate**: Never blindly trust caller-supplied
`X-Request-ID` values."*

**B42. Every request gets a request_id; it is echoed on every response, success and
error.** `backend/request-middleware.md:142` and `:144` — *"3. **Always echo**: The
`X-Request-ID` response header is present on every response (success and error)."*

**B43. Exactly one structured log entry per request, carrying method, path, status,
duration, request_id.** `backend/request-middleware.md:145` — *"4. **One log per
request**"*; required-fields table at `:471-477`.

**B44. `loguru` is the logging library.**
`architecture/reference-architecture.md:94` — *"| Logging | **loguru** | — | std +
prod agree; canonical |"*.
Fail condition: stdlib `logging` (which is what `fast-mcp-jira` uses).

**B45. No `print()` and no logging of PII, tokens, or secrets.**
`architecture/observability.md:636` — *"Log sensitive data (passwords, tokens, PII)"*
and `:642` — *"Use print statements instead of loggers"*, both under **Don't**.
`documentation/agentic-coding-standard.md:173` — *"No `console.log` / `print`
debugging statements"*.

### Language, stack and style

**B46. Python floor is `>=3.12`, not 3.11.**
`architecture/reference-architecture.md:83` — *"| Language | Python | `>=3.12` | deep
tier |"*, corroborated by `backend/tech-stack.md:30` (*"**Python 3.12+**"*) and
`backend/tech-stack.md:129` (`requires-python = ">=3.12"`).
**This contradicts the "Python 3.11+" in the project brief.** See §4/C1.

**B47. Blessed libraries: Pydantic `>=2.10`, `httpx`, `tenacity ^9` +
`circuitbreaker ^2`, `uv` packaging, `ruff`/`mypy`/`pytest`.**
`architecture/reference-architecture.md:85, 91, 92, 95, 98`.

**B48. `ruff format` is the formatter; Black is not.**
`architecture/reference-architecture.md:92` — *"ruff format (not Black)"*;
`backend/python.md:368` — *"**ruff format**: Code formatter (opinionated; replaces
Black)"*.

**B49. Line length 88; docstrings/comments wrapped at 72.**
`backend/python.md:35-36`.

**B50. Type hints on all public functions; Google- or NumPy-style docstrings.**
`backend/python.md:76` (*"Always use type hints for function parameters and return
values"*), `:97` (*"Use Google-style or NumPy-style docstrings"*),
`documentation/agentic-coding-standard.md:169` — *"Python has type hints on all public
functions"*.

**B51. `datetime.now(UTC)`; `datetime.utcnow()` is forbidden.**
`backend/python.md:227` — *"Never use `datetime.utcnow()` — deprecated since Python
3.12 (returns naive datetime missing tzinfo)."*

**B52. Naming per the table: snake_case functions/modules, PascalCase classes and
Pydantic models, UPPER_SNAKE_CASE constants.**
`backend/python.md:62-72`.

**B53. Secrets are `SecretStr` in a pydantic-settings `Settings` class, read from
env, accessed via `.get_secret_value()`; a committed `.env.example` carries names
only.** `architecture/security.md:433-463` and `:469` — *"Always use
.get_secret_value() to access secrets"*; `:418` — *".env.example (commit this)"*.
`documentation/agentic-coding-standard.md:127` forbids code that *"Hardcodes secrets,
API keys, or passwords"*.

**B54. Approved crypto libraries only: `cryptography`, `bcrypt`, `argon2-cffi`.**
`documentation/agentic-coding-standard.md:153`. Note `:155` — never MD5/SHA1 for
passwords. (The `hashlib.sha256` API-key hashing at
`architecture/authentication.md:539` is for key lookup, not password storage.)

### Testing

**B55. pytest with `asyncio_mode = "auto"`, `--strict-markers`, declared markers, and
`branch = true` coverage.** `backend/testing.md:56-98` (canonical `pyproject.toml`
block).

**B56. Coverage floor 80% overall, `fail_under = 80`.**
`backend/testing.md:96` (`fail_under = 80`), `:585` (*"| Overall | 80% |"*),
`architecture/testing-strategy.md:322`
(`--cov-fail-under=80`), `devops/quality-gates.md:44` — *"Coverage meets minimum
threshold (80%)"*.
Sub-targets, `backend/testing.md:586-589`: Services 90%, API Routes 85%, Utilities
95%.
`architecture/testing-strategy.md:302-306` adds Backend API 80% line / 70% branch,
Backend Services 85% / 75%, **Critical Paths 95% line / 90% branch**.

**B57. Critical paths carry the 95%/90% bar; "data mutations" and
"security-sensitive operations" are critical paths.**
`architecture/testing-strategy.md:310-314`.
For this repo that is: the auth verifier, the argument-rejection path (B12), and
every Jobvite write tool.

**B58. A collection-guard meta-test exists inside a configured `testpaths` root and
passes in CI.** `backend/testing.md:138-141` — *"**A collection-guard meta-test is
required.** ... The guard must itself live inside a configured root so that its own
absence fails collection"*; `devops/quality-gates.md:76-81` — *"If the guard is absent
or if any test file lives outside the configured roots, the CI backend test job MUST
fail."*

**B59. CI runs pytest with no positional path argument, so `testpaths` is
authoritative.** `backend/testing.md:166-172` — *"CI must run all roots. The CI
`pytest` invocation MUST NOT restrict"* discovery.

**B60. A SKIPPED required check fails the gate; skip count must be 0.**
`devops/quality-gates.md:85-87` — *"A SKIPPED result on a **required** check is not a
passing result — it is an unknown result and MUST fail the gate."*
`devops/ci-cd.md:673-675` — *"A SKIPPED job or test is an **unknown result**, not a
passing one ... a SKIPPED outcome MUST block merge exactly as a FAILED outcome
would."*
`devops/ci-cd.md:679-681` — *"**Do not set `skipped == success` for required
checks.**"*

**B61. Test names follow `test_{what}_{when}_{expected}`.**
`documentation/agentic-coding-standard.md:346-351`.

**B62. External APIs are mocked; own code and business logic are not.**
`architecture/testing-strategy.md:418-424` (Mock / Don't Mock table).

### CI/CD

**B63. CI runs, as separate gates with 0 errors: `ruff check`, `ruff format --check`,
`mypy`, `pytest --cov`.**
`devops/ci-cd.md:181-188`; `devops/quality-gates.md:63-65` — *"| Backend Lint | Ruff |
0 errors |"*, *"| Backend Types | mypy | 0 errors |"*, *"| Backend Tests | pytest |
80%+ coverage, all test roots run |"*.

**B64. Dependencies install frozen: `uv sync --frozen`.**
`devops/ci-cd.md:179`; `devops/supply-chain-security.md:75-77` — *"Reproducible
installs MUST use a **frozen** install everywhere CI"*.

**B65. `uv.lock` is committed and pins transitives.**
`devops/supply-chain-security.md:69-74` — *"**Python**: `uv.lock` MUST be committed"*
… *"**Transitive** dependencies MUST be pinned by the lockfile"*.

**B66. An unpinned/floating install never runs in CI or an image build.**
`devops/supply-chain-security.md:81-83` — *"(unpinned) **MUST NEVER** run in CI or in
an image build. It defeats"* the lockfile.

**B67. `pip-audit` runs in CI on every PR and fails the build on High/Critical.**
`devops/supply-chain-security.md:94-98` — *"`pip-audit` (Python) ... **MUST** run in
CI on every"* PR; *"The scan **MUST FAIL the build** on any known **High** or
**Critical**"*. Note `:99-101`: *"`pip-audit` has **no severity threshold** and fails
on **any** advisory"*.
`devops/ci-cd.md:480-484` gives the concrete step.

**B68. CodeQL analysis runs for Python.**
`devops/ci-cd.md:486-511`; `devops/quality-gates.md:70` — *"| Security Scan |
CodeQL/Trivy | No high/critical |"*.

**B69. Secret scanning (TruffleHog) runs on PRs with `fetch-depth: 0`.**
`devops/ci-cd.md:543-556`.

**B70. Every CI run emits a CycloneDX **and** SPDX SBOM as artifacts; tagged releases
attach them.** `devops/quality-gates.md:262-274` — *"Every CI run MUST produce a
Software Bill of Materials (SBOM) for each shippable artifact"*, formats row
*"CycloneDX JSON **and** SPDX JSON (emit both)"*.
`devops/supply-chain-security.md:139-149`.
Tool and pin fixed at `anchore/sbom-action@v0` (`devops/quality-gates.md:269-270`).

**B71. A license gate runs `pip-licenses` against the allow-list; a
non-allow-listed dependency blocks the build.**
`devops/quality-gates.md:282-294` — allow-list is exactly MIT, Apache-2.0,
BSD-2-Clause, BSD-3-Clause, ISC; *"Dependencies on the flag-list require explicit
legal review and an ADR before merge"* (`:283-284`).
`devops/ci-cd.md:644-651` gives the concrete `pip-licenses --allow-only` invocation.
`devops/supply-chain-security.md:221` — *"**Disallowed licenses MUST block** the
build."*

**B72. A known advisory that cannot be remediated is tracked, not silently
suppressed.** `devops/supply-chain-security.md:130-131`.

**B73. PR titles carry a traceability ID: `[FEAT-XXX] Description`.**
`devops/quality-gates.md:219-229`; `documentation/agentic-coding-standard.md:332-338`.

**B74. No `TODO` without a ticket reference.**
`documentation/agentic-coding-standard.md:171` — *"No `TODO` comments without ticket
reference (e.g., `# TODO(FEAT-001): ...`)"*, with the CI check at `:405-411`.

**B75. No commented-out code blocks.**
`documentation/agentic-coding-standard.md:174`.

**B76. `.github/workflows/` is a protected path — agents do not auto-modify it.**
`documentation/agentic-coding-standard.md:93-96`; `pyproject.toml` and `uv.lock` are
conditionally protected (`:103-110`).

### Documentation (public repo)

**B77. `README.md` contains all 14 required sections, in order, with exact heading
text.** `documentation/readme-standard.md:43` — *"Every README MUST contain the
following sections, in this order. Section headings must match exactly so that
automated checks can locate them."* List at `:45-58`: Title, One-line description,
Status badges, Quickstart, Installation, Configuration, Usage examples, API/CLI
reference link, Development setup, Testing, Deployment, Contributing, License,
Maintainers.
This binds here because `:34-35` requires a README at *"The top level of every Git
repository"* and *"The root of every published package (npm, PyPI, ...)"*.

**B78. The README Configuration table lists every environment variable the server
reads, with columns `Name`, `Required`, `Default`, `Description`, and no real secret
values.** `documentation/readme-standard.md:50`; `:66` — *"every environment variable
read by the component MUST appear in the Configuration table. New variables added in a
PR require the table to be updated in the same PR."*

**B79. README ≤ 500 lines; overflow moves to `docs/`.**
`documentation/readme-standard.md:64`.

**B80. Quickstart commands are exercised by CI on every merge to the default
branch.** `documentation/readme-standard.md:67`.

**B81. Badges point at live sources; static stale SVGs are forbidden.**
`documentation/readme-standard.md:70`.

**B82. A link checker runs in CI and a broken link blocks merge.**
`documentation/readme-standard.md:69`.

**B83. `CHANGELOG.md` follows Keep a Changelog 1.1.0 with a top `## [Unreleased]`
section.** `documentation/changelog-standard.md:42` and `:84` — *"An `## [Unreleased]`
section MUST sit at the top of the file"*.

**B84. Breaking changes are prefixed `BREAKING:` with a migration note and trigger a
major bump.** `documentation/changelog-standard.md:91`.

**B85. Security fixes appear under `### Security` with a CVE when one exists.**
`documentation/changelog-standard.md:92`.

**B86. Internal-only changes (refactors, test-only, CI) do NOT appear in
`CHANGELOG.md`.** `documentation/changelog-standard.md:94`.

**B87. Release dates equal the publication date; backdating is forbidden.**
`documentation/changelog-standard.md:93`.

### PII / GDPR (Jobvite candidate data)

**B88. Candidate PII is never written to logs or traces in the clear.**
Composite of `ai/tool-calling.md:171-172` (arguments logged *"PII redacted"*),
`ai/prompt-injection.md:127-128` (redact before the trace backend), and
`architecture/observability.md:636`.
This is the one obligation most likely to be missed: a Jobvite candidate tool logs
names and emails by default unless redaction is built in from the start.

---

## 2. Applicable with adaptation

**A1. Error contract → MCP tool results.**
`architecture/error-contract.md` is written for HTTP responses ("All API error
responses", `:36`). MCP tool errors travel inside a JSON-RPC result, not an HTTP
body, so `Content-Type: application/problem+json` (B3) cannot apply to a tool error.
**Adaptation:** carry the seven RFC 9457 members (`type`, `title`, `status`, `detail`,
`instance`, `request_id`, `timestamp`) as fields **inside** the tool result payload,
snake_case per B14; apply the real `application/problem+json` content type only to
genuine HTTP surfaces (health endpoint, transport-level auth rejections). The
`instance` member — defined at `:290` as *"URI of the request that generated the
error"* — has no URI for a tool call; use the tool name as a stable substitute and
document the substitution.
The intent (`:204` no custom envelopes, one machine-readable discriminator) is fully
preserved and fully binding.

**A2. Rate limiting → Jobvite-side and process-local.**
`backend/rate-limiting.md:355-356` requires every public endpoint to be rate-limited
by a **Redis-backed** token bucket, and forbids in-memory limiters (*"In-memory
limiters (`@cachetools`, plain dicts, `slowapi` default) are forbidden in production
because they desynchronize across replicas"*, `:94-97`). The stated rationale is
multi-replica desynchronization.
**Adaptation:** a single-process MCP server has no replica-desync problem, so the
rationale for the Redis mandate does not obtain. Introducing Redis into a
zero-dependency personal repo to satisfy a rule whose stated reason is inapplicable is
the wrong trade. The binding residue: (a) an outbound limiter respecting Jobvite's own
quota, since B34's 429 retry path presumes one; (b) the 429 response shape
(`:361-362`, `RateLimitException` → `/problems/rate-limited`) if the server ever
surfaces a rate-limit error. **This deviation requires an ADR** — `:355` says *"Opt-out
requires an ADR"* and `:358` says overrides may only tighten. Recommend writing that
ADR as part of the design rather than discovering it at review.

**A3. Request middleware → MCP transport middleware.**
`backend/request-middleware.md` is Starlette-specific (`request.state`,
`add_middleware`, LIFO ordering at `:481-489`). FastMCP's Streamable HTTP transport is
ASGI, so the mechanism transfers; `request.state.request_id` becomes the
`request_id_var` ContextVar the AI standards already require (B40).
The CORS-outermost rule (`:146`, Rule 5) is inapplicable — no browser origin.
B41-B43 transfer unchanged.

**A4. Authentication → MCP endpoint API key, without the DB.**
`architecture/authentication.md:518-582` gives the machine-to-machine API-key recipe
but stores keys in a Postgres `api_keys` table (`:594-600`). No database here.
**Adaptation:** keep the shape — `X-API-Key` header (`:534`), SHA-256 hashing before
comparison (`:537-539`), `secrets.token_urlsafe(32)` generation (`:544`),
`UnauthorizedException` on missing or invalid (`:555`, `:568`) — and compare against a
hash from configuration instead of a row. **Use `secrets.compare_digest`**, not `==`;
the standard's DB lookup happened to be constant-time-ish by accident, and a naive
port to an in-memory compare reintroduces a timing side channel the original never
had.
Clerk/JWT (`:68-517`) is not applicable — no human users.

**A5. Agent guardrails → tool-provider side.**
`ai/agent-guardrails.md` addresses the *agent loop*. This server is a tool
**provider**, not a host: it does not run a loop, so the autonomy bounds at `:93-99`
(max steps, recursion depth, tool-call budget, token ceiling) have no loop to bound.
**Adaptation:** the guardrails that live on the tool side — B13, B18, B19, B20, B21,
B17 — bind in full. The wall-clock timeout row survives as B32's per-call timeout. The
HITL gate (B18) is the delicate one: this server cannot *implement* an approval UI, so
it must (a) mark destructive tools as such in their schema/annotations so a host can
gate them, and (b) fail closed by default — e.g. destructive tools disabled unless
explicitly enabled by configuration. Shipping an ungated `delete_candidate` and
calling the gate "the host's problem" does not satisfy `:73`'s *"Fail closed: no
approver, no action."*

**A6. Prompt injection → indirect injection via Jobvite content.**
`ai/prompt-injection.md` assumes the reader builds prompts. This server builds none.
**Adaptation:** the applicable half is the trust-classification table at `:56-63`,
which classifies *"Tool / function results"* as **untrusted** and instructs *"Re-enter
these controls on return"*. This server *produces* those results. Concretely: mark
returned Jobvite free-text (résumés, cover letters, interview notes, candidate
comments) as untrusted data — delimit it per `:74-77`, and strip delimiter tokens per
`:79-81` (*"Strip or neutralize the delimiter tokens from untrusted content so it
cannot forge a channel break"*) so a candidate cannot close the wrapper early. B24-B26
capture this.

**A7. Testing strategy pyramid → no E2E tier.**
`architecture/testing-strategy.md:52-57` allocates 10% to E2E via Playwright. There is
no UI. **Adaptation:** redistribute to unit + integration, where "integration" means
tool-through-to-a-mocked-Jobvite. Coverage numbers (B56, B57) are unaffected and
remain binding. The DB fixtures at `:366-412` are inapplicable.

**A8. CI/CD workflow shape → single Python job set.**
`devops/ci-cd.md:58-285` describes a frontend+backend monorepo with Postgres and Redis
service containers and a `./backend` working directory.
**Adaptation:** keep the backend jobs (lint, format-check, mypy, pytest+cov), drop
frontend/E2E/Lighthouse and the service containers, drop the `alembic upgrade head`
step at `:233-236`. The security workflow (`:444-652`) transfers nearly intact —
pip-audit, CodeQL (python only), TruffleHog, SBOM, license-scan — minus the container
jobs. `PYTHON_VERSION: '3.12'` at `:70` corroborates B46.

**A9. Twelve-factor config.**
`devops/twelve-factor.md` is `priority: recommended`, not required — it does not bind.
Its Factor III (`:61`, config in env, secrets never committed) is nonetheless already
mandatory via B53, so following it costs nothing.

**A10. ADR template.**
`architecture/adr/adr-template.md` is `priority: required` and supplies the structure
(Context `:46`, Decision `:56`, Consequences `:64`, Alternatives Considered `:83`).
It binds *conditionally* — only once an ADR is written. Given A2 (rate-limiting
opt-out) and C1 (Python floor), **at least one ADR is required for this repo**, so
this template will be exercised.

---

## 3. Not applicable — listed and dismissed

Dismissed with a reason each, per the brief's preference for explicit dismissal.

| Standard | Priority | Why not applicable |
|---|---|---|
| `frontend/api-client.md` | required | Next.js/React/TypeScript fetch wrapper and OpenAPI codegen. No frontend consumer exists. Its one cross-cutting ask — the backend commits `openapi.json` (`:41`) — presupposes a TS client to generate. |
| `frontend/error-handling.md` | required | React error boundaries, `error.tsx` routes, server actions. `applicable_to: [typescript, react, nextjs]`. |
| `frontend/markdown-rendering.md` | required | `react-markdown` + DOMPurify at a browser DOM sink. This server has no render sink. The adjacent principle (model/third-party content is hostile) binds via B24, sourced from the AI standards instead. |
| `repos/evolv-coder/docs/adrs/README.md` | (TIER-1 #17) | An index of evolv-coder product ADRs. Product-scoped, not a standard. |
| `repos/evolv-coder/docs/adrs/adr-ec-350-04-public-share-rate-limit.md` | (TIER-1 #18) | A decision about evolv-coder's public share-link endpoint. No share links here. |
| `database/*` (9 files) | required | No database. No schema, migrations, multi-tenancy, audit tables, Neo4j, or TimescaleDB. |
| `backend/pagination.md` | required | Cursor pagination for a DB-backed API this project does not serve. Jobvite's own paging is consumed, not implemented. |
| `backend/idempotency.md` | required | The `Idempotency-Key` HTTP recipe is for inbound mutating endpoints. B19's tool-level idempotency covers the residue. |
| `backend/background-jobs.md` | required | No Celery, no queue, no worker. |
| `backend/auth-guard.md`, `backend/openapi-contract.md`, `backend/delete-response.md`, `backend/realtime.md`, `backend/file-storage.md`, `backend/document-*.md` | required / recommended | Each governs a REST/FastAPI surface shape this server does not expose. |
| `backend/{go,rust,java,csharp,cpp,php,ruby,kotlin,swift,dart,typescript}.md` | required | Other languages. |
| `devops/ecs-fargate.md`, `devops/aws.md`, `devops/aws-oidc.md`, `devops/gcp.md`, `devops/azure.md`, `devops/infrastructure-as-code.md` | required | Brief states no ECS deployment. No cloud target. |
| `devops/docker.md` | required | Applies only if a container image ships. Currently out of scope — **but see §4/G3**, because B70's SBOM and the container-scan gate become live the moment one does. |
| `devops/backup-disaster-recovery.md`, `devops/monitoring-alerting.md`, `devops/environments.md` | required | Presume owned running infrastructure with an on-call rotation. A library-style repo has none. |
| `devops/git-workflow.md` | required | Read in full: its scope is maintaining **the standards repository itself** (`:75` — `git add Standards/`, `:89-98` version-tagging that repo). It does not define a general project git workflow. See §4/G1. |
| `ai/bedrock-integration.md`, `ai/model-selection.md`, `ai/provider-integration.md`, `ai/langchain.md`, `ai/rag-vector-stores.md`, `ai/voice-multimodal.md`, `ai/prompt-management.md`, `ai/cost-token-controls.md`, `ai/llm-observability.md` | required | This server never calls a foundation model. It has no prompts, no embeddings, no token spend, no LLM traces. |
| `ai/evaluation-testing.md` | required | Partially reached: B23 and `ai/prompt-injection.md:138` route red-team cases into "the eval suite" defined there. Not read in full — see "What I could NOT verify". |
| `architecture/gdpr-data-rights.md` | required | Read in full. Its obligations attach to systems that **store** personal data — *"Every table containing personal data MUST declare its DSAR/RTBF policy"* (`:50`), erasure dispositions, a `gdpr_erasures` table. This server is stateless and stores nothing; Jobvite is the controller's system of record. **The DSAR/RTBF machinery does not bind.** The residue that does bind is the no-PII-in-logs rule, captured as B88 — because a log file is the one place this stateless server could accidentally become a personal-data store. |
| `architecture/api-versioning.md` | recommended | Not `required`, and no versioned REST surface. |
| `architecture/caching.md` | required | Redis response caching for a DB-backed API. Optional here; if a cache is added it becomes live. |
| `architecture/data-flow.md`, `architecture/threat-modeling.md` | required | Not read in full; both are process/design-artifact standards rather than code obligations. Flagged in "What I could NOT verify". |
| `azure/*`, `snowflake/*` | required (opt-in domains) | Explicitly opt-in and not in force, per the brief and `MUST-READ-DOCS.md:251-253`. Not cited. |
| `documentation/{prd,brd,discovery,specification,onboarding,glossary}-*.md` | required / recommended | Deliverable templates for client engagements, not repo obligations. |

---

## 4. Conflicts and gaps

### Conflicts

**C1. Python floor: brief says 3.11+, the standard says >=3.12.**
`architecture/reference-architecture.md:83` (*"| Language | Python | `>=3.12` |"*) and
`backend/tech-stack.md:129` (`requires-python = ">=3.12"`) versus the task brief's
"Python 3.11+". The reference architecture calls itself *"the **single blessed source
of version truth**"* (`:24`), so 3.12 wins absent an ADR.
There is also a live consequence, not just a number: `backend/python.md:227` forbids
`datetime.utcnow()` *"deprecated since Python 3.12"*, and `from datetime import UTC`
only exists from 3.11 — the standard's own idiom assumes ≥3.12.
**Recommendation: set `requires-python = ">=3.12"` and drop 3.11.** If 3.11 support is
genuinely wanted for reach, it needs an ADR.

**C2. `agentic-coding-standard.md` mandates the error shape every other standard
forbids.**
`documentation/agentic-coding-standard.md:283-294` presents as **Required**:
```python
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
```
This is precisely what `backend/python.md:126` forbids (*"**Do not raise
`fastapi.HTTPException` directly.**"*) and what `architecture/error-contract.md:204`
rules out (*"No custom envelopes"*). Both files are `priority: required`; the
frontmatter offers no tie-break.
**Resolution: `error-contract.md` self-declares primacy** — `:38` — *"**This is the
authoritative source for error format.**"* Follow the error contract. The
agentic-coding-standard example is stale and should be reported upstream.

**C3. Commit message format — three incompatible specifications.**
- `documentation/agentic-coding-standard.md:315` — `[ID] type: description`, e.g.
  `[FEAT-001] feat: add user authentication flow`.
- `devops/quality-gates.md:233-236` — `type(scope): description` with a trailing
  `Refs: FR-XXX`.
- `backend/python.md:426` — *"Commit messages: Use conventional commits format"* with
  bare `feat:`/`fix:` examples and no ID at all.
- **(added on re-sweep)** `devops/development-workflow.md:326` — `git commit -m
  "feat(scope): description"`, and the conventional-commit table at `:335-343`.
All four are `priority: required`. `MUST-READ-DOCS.md:269` already logs this conflict
as open with no owning task.
**The re-sweep strengthens the recommendation:** two of the four required sources
(`quality-gates.md:233-236` and `development-workflow.md:326`) independently specify
`type(scope): description`. That is now the plurality position, not just the most
practical one.
**Recommendation:** `type(scope): description` + `Refs:` (quality-gates), because it
is the only one of the three that survives contact with a repo having no FEAT-XXX
ticket system, and it is conventional-commits-compatible so `amannn/action-semantic-pull-request`
(`devops/ci-cd.md:305-321`) will accept it. Record the choice in the repo's CLAUDE.md.

**C4. PR title traceability assumes a ticket system this repo does not have.**
B73 requires `[FEAT-XXX] Description` and `agentic-coding-standard.md:398-403` gives a
CI check that **fails the build** on a PR title lacking `[FEAT-|FR-|BUG-]`. A personal
public repo has no such ticket namespace. Meanwhile `devops/ci-cd.md:300-321` enforces
a *semantic* (conventional-commit) PR title, which the bracketed-ID format would fail.
The two required CI checks are mutually unsatisfiable as written.
**Worse on re-sweep:** there are three incompatible ID vocabularies, not two —
`agentic-coding-standard.md:334-338` uses `FEAT-/FR-/BUG-`, `quality-gates.md:224-228`
uses `FEAT-/FR-/BUG-/TECH-`, and `development-workflow.md:166` uses a
layer-prefixed `[FE-001]` family (`FE/BE/DB/DO`, per the branch table at `:62-65`).
**Recommendation:** adopt the semantic PR title from `ci-cd.md` and note the deviation
from the ID format; do not install the `:398-403` check.

**C5. Rate limiting mandates Redis; the project has no Redis and no replicas.**
Detailed in §2/A2. `backend/rate-limiting.md:356` (*"No in-memory limiters in
production"*) versus a single-process server for which the stated desync rationale
(`:94-97`) does not apply. Needs an ADR per `:355`.

**C6. `ai/` domain scope arguably excludes this project entirely.**
`ai/README.md:22-24` defines the domain as *"**application LLM engineering** — product
code that *calls* foundation models"*, and `:31-33` scopes it to *"apps that call
foundation models"*. This server calls none. Read literally, `tool-calling.md` and
`agent-guardrails.md` — the two most substantively relevant documents in the entire
corpus — do not bind.
That reading is obviously wrong in spirit: `tool-calling.md` is the only standard that
describes how to define a tool. But it is written wholly from the host's side ("how
application code exposes tools **to a model**", `:22-23`), and no standard addresses a
repo that is the tool provider.
**I have treated `ai/tool-calling.md` and the tool-side clauses of
`ai/agent-guardrails.md` as binding by intent**, and flagged the scope question here
rather than quietly assuming it. A reviewer could legitimately dispute B9-B23 on
`ai/README.md:22`. This deserves a decision, not an assumption. Related: `MUST-READ-DOCS.md:20`
already defines an `[AUTHORITY-UNCLEAR]` flag for exactly this situation.

**C7. Testing-strategy vs backend-testing DB fixture divergence.**
`MUST-READ-DOCS.md:267` logs `devops/ci-cd.md` (alembic) versus
`architecture/testing-strategy.md` (`create_all`) as an open conflict. **Moot here** —
no database — but noted so a reviewer does not raise it as new.

### Gaps — things a reviewer will expect that no standard covers

**G1. ~~There is no general project git-workflow standard.~~ — RESOLVED, see §6.**
*Original finding:* `devops/git-workflow.md` is `priority: required` but scopes itself
to the standards repository (`:75` stages `Standards/`; `:89-98` tags that repo's
versions), leaving branch naming, review requirements and merge strategy undefined.
**Correction:** I have since read `devops/development-workflow.md` (`priority:
required`) in full. It *does* define all of it — branch naming (`:58-68`), branch
protection (`:70-83`), the PR template (`:199-242`) and the code-review checklist
(`:246-309`). My original note flagged this file as unread and explicitly declined to
assert what it contained; that was the right call, and having now read it the gap is
closed. Obligations extracted as **B89-B96** in §6.

**G2. There is no open-source / public-repository release standard.**
*(Superseded and greatly expanded by §6 following the hosting change — §6 is now the
authoritative treatment. Retained here for continuity.)*
I grepped the full tree for "open source", "open-source release", and "public
repository": **zero hits.** This project is going into Phil's personal *public* GitHub.
Nothing in the corpus covers: which LICENSE to choose, whether an evolv copyright
header is required, what may be published under an individual's account versus the
org's, PyPI publication and trusted publishing, CONTRIBUTING/CODE_OF_CONDUCT, security
disclosure policy (`SECURITY.md`), or the vetting that stops an internal client
detail leaking into a public repo. `readme-standard.md:57` requires a License section
with an SPDX identifier but does not say **which** license.
The repo already contains a `LICENSE` (1071 bytes, MIT-sized) chosen without a
governing standard. **This is the largest genuine gap and needs Phil's decision, not a
reviewer's guess.**

**G3. No MCP-specific standard exists at all.**
No document in the corpus mentions MCP, FastMCP, JSON-RPC, or the Model Context
Protocol. Every obligation above reaches this project by analogy from HTTP/FastAPI.
Specifically unaddressed: MCP tool naming conventions, resource/prompt primitives
(neither is mentioned anywhere), transport auth for Streamable HTTP, tool annotations
(`readOnlyHint`/`destructiveHint`) which would be the natural vehicle for B18's gate,
and how MCP protocol-version negotiation interacts with `api-versioning.md`.

**G4. Nothing defines "public-facing surface" for a locally-run server.**
`backend/rate-limiting.md:31-32` says rate limiting is *"required on every
public-facing surface"* but never defines the term. An MCP server run on localhost by
one developer, versus one hosted on the internet, are different risk objects with
identical obligations under the text. This ambiguity is upstream of C5.

**G5. Supply-chain SLSA/signing obligations have no stated floor for a non-container
repo.** `devops/supply-chain-security.md:164-166` requires builds to target SLSA v1.2
with *"the **target level MUST be documented per"*
artifact, and `:190-199` requires cosign signing and digest pinning — all phrased
around container images. A pure-Python package with no image has no stated target
level. If this repo ever publishes to PyPI, the provenance question becomes live and
unanswered.

**G6. No coverage target is defined for a repo whose "services" and "API routes"
categories do not exist.** `backend/testing.md:583-589` sets per-category targets
(Services 90%, API Routes 85%, Utilities 95%, Models 70%) against a layered FastAPI
app. An MCP tool module is none of these. The 80% overall floor (B56) is unambiguous;
the sub-targets require a judgement call. **Recommendation:** treat each tool module as
"API Routes" (85%) and the Jobvite client as "Services" (90%).

**G7. `MUST-READ-DOCS.md:242-245` warns the compiled standards copy is stale.**
The compiled bundle agents actually load
(`repos/evolv-coder/.claude/context/standards/*-standards.md`) is stamped 2026-05-31
and lags the source. Everything in this report is cited from **source**, which is
correct but means an agent working from the compiled context may not see these rules.
Worth knowing before assuming a reviewer shares this baseline.

---

## 5. Tooling the standards mandate

Exact, with versions where the standards pin them.

### Language and packaging

| Item | Mandate | Source |
|---|---|---|
| Python | `>=3.12` (**not 3.11** — see C1) | `architecture/reference-architecture.md:83`; `backend/tech-stack.md:129` |
| Package manager | `uv` | `architecture/reference-architecture.md:91` |
| CI install | `uv sync --frozen` | `devops/ci-cd.md:179`; `devops/supply-chain-security.md:75-77` |
| Lockfile | `uv.lock` committed, pins transitives | `devops/supply-chain-security.md:69-74` |
| Python setup in CI | `astral-sh/setup-uv@v4`, then `uv python install 3.12` | `devops/ci-cd.md:172-176` |
| Runtime `PYTHON_VERSION` in CI env | `'3.12'` | `devops/ci-cd.md:70` |

### Lint / format / types

| Tool | Command | Gate | Source |
|---|---|---|---|
| ruff (lint + import sort) | `uv run ruff check .` | 0 errors | `devops/ci-cd.md:182`; `devops/quality-gates.md:63` |
| ruff format (**not Black**) | `uv run ruff format --check .` | 0 diffs | `devops/ci-cd.md:185`; `backend/python.md:368` |
| mypy | `uv run mypy <pkg>` | 0 errors | `devops/ci-cd.md:188`; `devops/quality-gates.md:64` |
| Line length | 88 chars (72 for comments/docstrings) | — | `backend/python.md:35-36` |
| pre-commit | `astral-sh/ruff-pre-commit` rev **`v0.15.13`**, hooks `ruff` + `ruff-format` | — | `backend/python.md:374-382` |
| Docstring style | Google-style or NumPy-style | — | `backend/python.md:97` |

### Test

| Item | Value | Source |
|---|---|---|
| Runner | `pytest` | `architecture/reference-architecture.md:92` |
| Async | `pytest-asyncio`, `asyncio_mode = "auto"`, `asyncio_default_fixture_loop_scope = "function"` | `backend/testing.md:59-60` |
| Coverage | `pytest-cov`, `branch = true`, `fail_under = 80` | `backend/testing.md:80-96` |
| HTTP test client | `httpx` | `backend/testing.md:45` |
| Factories | `factory-boy` | `backend/testing.md:47` |
| Time mocking | `freezegun` | `backend/testing.md:48` |
| addopts | `-v`, `--strict-markers`, `--tb=short`, `-ra` | `backend/testing.md:65-70` |
| Markers | `slow`, `integration`, `unit` (declared, `--strict-markers`) | `backend/testing.md:71-75` |
| CI invocation | `uv run pytest --cov=<pkg> --cov-report=xml` — **no positional path** | `backend/testing.md:172`; `devops/ci-cd.md:239` |
| Coverage floor | 80% overall; Services 90%, API Routes 85%, Utilities 95% | `backend/testing.md:585-589` |
| Critical-path coverage | 95% line / 90% branch | `architecture/testing-strategy.md:306` |
| Skip policy | required suites report **0 skipped** | `devops/quality-gates.md:89-94`; `devops/ci-cd.md:707-721` |
| Collection guard | meta-test inside a `testpaths` root, required in CI | `backend/testing.md:138-141`; `devops/quality-gates.md:76-81` |
| Test naming | `test_{what}_{when}_{expected}` | `documentation/agentic-coding-standard.md:346` |
| Coverage upload | `codecov/codecov-action@v4` | `devops/ci-cd.md:246` |

### Security / supply chain CI jobs

| Job | Tool + pin | Gate | Source |
|---|---|---|---|
| Dependency audit | `pip-audit` | fails on High/Critical; note: fails on **any** advisory | `devops/supply-chain-security.md:94-101`; `devops/ci-cd.md:484` |
| SAST | `github/codeql-action/{init,autobuild,analyze}@v3`, language `python` | no high/critical | `devops/ci-cd.md:500-511` |
| Secret scan | `trufflesecurity/trufflehog@v3.88.0`, `fetch-depth: 0` | blocks on finding | `devops/ci-cd.md:547-556` |
| SBOM | `anchore/sbom-action@v0` | CycloneDX JSON **and** SPDX JSON, uploaded every run, attached to releases, 1-year retention | `devops/quality-gates.md:269-274`; `devops/ci-cd.md:571-610` |
| License | `pip-licenses --format=json --with-license-file --allow-only 'MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;Apache Software License;MIT License;BSD License;ISC License (ISCL)'` | non-allow-listed dep blocks build | `devops/ci-cd.md:648-651`; `devops/quality-gates.md:286-294` |
| Container scan | `aquasecurity/trivy-action@0.36.0` | only if an image ships | `devops/ci-cd.md:525` |
| Schedule | security workflow also runs weekly, `cron: '0 0 * * 0'` | — | `devops/ci-cd.md:455-456` |

### GitHub Actions versions

`actions/checkout@v6`, `actions/setup-node@v4`, `actions/upload-artifact@v4`,
`actions/cache@v4`, `astral-sh/setup-uv@v4`, `codecov/codecov-action@v4`,
`github/codeql-action/*@v3`, `anchore/sbom-action@v0`,
`amannn/action-semantic-pull-request@v5`, `aquasecurity/trivy-action@0.36.0`,
`trufflesecurity/trufflehog@v3.88.0`.
Sources: `devops/ci-cd.md:81, 85, 125, 157, 173, 246, 306, 501, 525, 552, 571, 741`.

### Runtime libraries

| Concern | Blessed | Source |
|---|---|---|
| Models / validation | Pydantic `>=2.10` (v2 API) | `architecture/reference-architecture.md:85` |
| HTTP client | `httpx` | `architecture/reference-architecture.md:98` |
| Logging | **`loguru`** (canonical; not stdlib `logging`) | `architecture/reference-architecture.md:94` |
| Retry | `tenacity` `^9` | `architecture/reference-architecture.md:95` |
| Circuit breaker | `circuitbreaker` (fabfuel) `^2` | `architecture/reference-architecture.md:95` |
| Settings | `pydantic-settings` + `SecretStr` | `architecture/security.md:429-437` |
| Crypto | `cryptography`, `bcrypt`, `argon2-cffi` only | `documentation/agentic-coding-standard.md:153` |
| HTML sanitization | `nh3` (only if rich text is ever sanitized) | `backend/input-validation.md:390` |

### Commit / PR conventions

- **Commit format** — three conflicting mandates (C3). Recommended:
  `type(scope): description` + `Refs:` line, `devops/quality-gates.md:233-236`.
- **Conventional types** — `feat, fix, docs, style, refactor, perf, test, build, ci,
  chore, revert`, `devops/ci-cd.md:309-320`.
- **PR title** — semantic, enforced by `amannn/action-semantic-pull-request@v5`
  (`devops/ci-cd.md:305-321`). The competing `[FEAT-XXX]` format is C4.
- **CHANGELOG** — Keep a Changelog 1.1.0; CI check that a `release-note`-labelled PR
  updates it (`documentation/changelog-standard.md:97`).

---

## What I could NOT verify

1. **Whether `ai/tool-calling.md` and `ai/agent-guardrails.md` legitimately bind a
   tool *provider*.** `ai/README.md:22-33` scopes the whole domain to code that calls
   foundation models. I treated them as binding by intent (C6) but this is a judgement
   I made, not a rule I read. **This is the single biggest assumption in the report**;
   if it is wrong, B9-B23 lose their cited authority (though not their merit). Needs a
   human decision.

2. ~~**`devops/development-workflow.md` — not read.**~~ **RESOLVED on the re-sweep.**
   Read in full; it supplies the branch/PR/review workflow G1 recorded as missing.
   Obligations extracted as B89-B96. G1 is closed.

3. **`ai/evaluation-testing.md` (`priority: required`) — not read in full.** Two
   binding clauses (B23, and `ai/prompt-injection.md:138`) route red-team cases into
   "the eval suite" that this file defines. The *specific structure* that suite must
   have is therefore uncited in this report.

4. **`architecture/threat-modeling.md`, `architecture/data-flow.md`,
   `backend/testing-patterns.md`, `devops/quality-gates.md` §DoR/DoD (`:140-215`) —
   skimmed via grep only, not read in full.** I cited nothing from them that I did not
   read directly.

5. **`architecture/security.md` was read by section, not cover to cover.** I read
   Input Validation (`:185-270`), Rate Limiting (`:394-404`), Secrets (`:407-474`),
   OWASP mapping (`:643-660`) and the checklist (`:663-682`). The Authorization
   (`:91-184`), XSS/CSP (`:275-343`), CSRF (`:344-392`), Encryption (`:478-552`) and
   Audit Logging (`:553-642`) sections I did not read line-by-line, judging them
   frontend- or DB-scoped. Audit Logging in particular may contain obligations that
   reach B17/B88; **I did not verify that it does not.**

6. **Whether any of these standards are actually enforced anywhere.** I read the
   documents; I did not check any repository for compliance, and I did not verify that
   the CI jobs described in `ci-cd.md` exist in any real workflow file.

7. **The correct license for a public personal repo containing evolv-derived work.**
   No standard covers it (G2). The repo already has a `LICENSE` file I did not open
   or evaluate — deliberately, since choosing it is Phil's call, not mine.

8. **Whether `fast-mcp-jira` is intended as a reference implementation.** I noted
   three places where copying it would start this repo in violation (`build_response`
   envelope vs B1, stdlib `logging` vs B44, 47 tools vs B20). I did not audit that repo
   systematically and make no broader claim about it.
