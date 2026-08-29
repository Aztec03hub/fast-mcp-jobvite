# Freeze re-test of every dismissal in `docs/research/STANDARDS.md`

**Scope:** §13's freeze procedure requires every conditional dismissal in the standards analysis to
be re-tested at freeze. That procedure had a 0-for-2 record: `architecture/caching.md` and
`backend/idempotency.md` both went live unnoticed and were caught by later sweeps, not by it. Only
those two had ever been re-tested, and only because a reviewer named them. **Nobody had ever
enumerated the rest. This document is that enumeration, its classification, and the result of
re-testing every row.**

**Method.** Enumerate first, classify second, test third. No row was skipped for looking obviously
dead, and **tested-and-standing is recorded as a distinct outcome from untested**. Every line
number below was re-derived with `grep -n` against the files as they are today; none was forwarded
from an earlier report.

**Not run:** the three `check-coupling*.py` gates, at the team lead's instruction (concurrent
modification). Nothing in this document depends on their result. If a freeze stamp needs them
green, the team lead reports that separately.

---

## 1. The enumeration

The dismissal table is `docs/research/STANDARDS.md:768-796`: a header at `:772-773` and
**23 dismissal rows at `:774-796`**, covering roughly 62 individual standard files. Two further
dismissals live inline in §2 and are enumerated in §5 below, because the freeze criterion says
*every* dismissal and the table is not the only place they occur.

| # | Line | Standard(s) | Stated rationale (abridged) | Class |
|---|---|---|---|---|
| D1 | `:774` | `frontend/api-client.md` | No frontend consumer; its one cross-cutting ask (backend commits `openapi.json`) presupposes a TS client | CONDITIONAL |
| D2 | `:775` | `frontend/error-handling.md` | `applicable_to: [typescript, react, nextjs]` | UNCONDITIONAL |
| D3 | `:776` | `frontend/markdown-rendering.md` | No browser DOM render sink; the adjacent principle "binds via B24" | CONDITIONAL + DELEGATING |
| D4 | `:777` | `repos/evolv-coder/docs/adrs/README.md` | An index of product ADRs, not a standard | UNCONDITIONAL |
| D5 | `:778` | `adr-ec-350-04-public-share-rate-limit.md` | "No share links here" | CONDITIONAL |
| D6 | `:779` | `database/*` (9 files) | "No database. No schema, migrations, multi-tenancy, audit tables" | CONDITIONAL |
| D7 | `:780` | `backend/pagination.md` | Cursor pagination for a DB-backed API this project does not serve; "Jobvite's own paging is consumed, not implemented" | CONDITIONAL + DELEGATING |
| D8 | `:781` | `backend/idempotency.md` | Already reopened as B108 and disposed | **previously TRIPPED** |
| D9 | `:782` | `backend/background-jobs.md` | "No Celery, no queue, no worker" | CONDITIONAL |
| D10 | `:783` | `backend/auth-guard.md`, `openapi-contract.md`, `delete-response.md`, `realtime.md`, `file-storage.md`, `document-*.md` | "Each governs a REST/FastAPI surface shape this server does not expose" | CONDITIONAL |
| D11 | `:784` | `backend/{go,rust,java,…}.md` (11 files) | Other languages | UNCONDITIONAL |
| D12 | `:785` | `devops/ecs-fargate.md`, `aws.md`, `aws-oidc.md`, `gcp.md`, `azure.md`, `infrastructure-as-code.md` | No cloud target | CONDITIONAL |
| D13 | `:786` | `devops/docker.md` | Applies only if a container image ships | **previously re-tested, STANDING** |
| D14 | `:787` | `devops/backup-disaster-recovery.md`, `monitoring-alerting.md`, `environments.md` | "Presume owned running infrastructure with an on-call rotation. A library-style repo has none" | CONDITIONAL |
| D15 | `:788` | `devops/git-workflow.md` | Read in full; its scope is the standards repository itself. See §4/G1 | UNCONDITIONAL + DELEGATING |
| D16 | `:789` | `ai/bedrock-integration.md`, `model-selection.md`, `provider-integration.md`, `langchain.md`, `rag-vector-stores.md`, `voice-multimodal.md`, `prompt-management.md`, `cost-token-controls.md`, `llm-observability.md` | "This server never calls a foundation model" | CONDITIONAL |
| D17 | `:790` | `ai/evaluation-testing.md` | "Partially reached… Not read in full" | DELEGATING + **self-declared untested** |
| D18 | `:791` | `architecture/gdpr-data-rights.md` | Obligations attach to systems that store personal data; residue is B88 | CONDITIONAL + DELEGATING |
| D19 | `:792` | `architecture/api-versioning.md` | Not `required`, and no versioned REST surface | CONDITIONAL |
| D20 | `:793` | `architecture/caching.md` | "Optional here; if a cache is added it becomes live" | CONDITIONAL (**tripped once already**) |
| D21 | `:794` | `architecture/data-flow.md`, `architecture/threat-modeling.md` | "Not read in full; both are process/design-artifact standards rather than code obligations" | DELEGATING + **self-declared untested** |
| D22 | `:795` | `azure/*`, `snowflake/*` | Explicitly opt-in domains, not in force | UNCONDITIONAL |
| D23 | `:796` | `documentation/{prd,brd,discovery,specification,onboarding,glossary}-*.md` | Deliverable templates for client engagements | CONDITIONAL |

**Counts.** 23 rows. **5 UNCONDITIONAL** (D2, D4, D11, D15, D22 — D15 is unconditional on a
reading of the file plus a delegation, so it is tested anyway). **18 CONDITIONAL or DELEGATING**,
of which 6 carry a delegating leg (D3, D7, D15, D17, D18, D21). Two (D8, D13) were tested by
earlier rounds and are not re-done. **16 rows were re-tested here; 2 carry forward; 5 are
unconditional and were read but need no design test.** Nothing is left untested.

---

## 2. Why the three classes are tested differently

- **UNCONDITIONAL** — the rationale is a property of the standard, not of our design
  (`applicable_to` frontmatter, a different language, an opt-in domain). It cannot go live by
  anything we build. Read once, note, move on.
- **CONDITIONAL** — "not applicable *because* X" where X is a property of *our* design. **These are
  dated claims.** The test is: name X, then go read the current design for X. This is the class
  `architecture/caching.md` was in, and the reason it failed is that nobody ever performed the
  second half.
- **DELEGATING** — "X is covered by Y". The test is **read what Y is actually satisfied by, not
  what Y is named.** `backend/idempotency.md` failed exactly here: B19 was named "tool-level
  idempotency" and was in fact satisfied by *the server never auto-retrying*, which does not touch
  the caller-replay residue. Both halves read sound in isolation; only the composition was wrong.

---

## 3. Results

### 3.1 Hand-check 1 — `backend/pagination.md` (D7): **STANDING**

Two legs: a conditional one ("a DB-backed API this project does not serve") and a delegating one
("Jobvite's own paging is consumed, not implemented").

1. **Frontmatter.** `standards/backend/pagination.md:6-10` is
   `applicable_to: [fastapi, express, dotnet, rest-api]`. This server exposes MCP tools; its HTTP
   mode is a FastMCP ASGI transport (`docs/DESIGN.md:768-772`), not FastAPI routes.
2. **What the standard actually obliges.** `pagination.md:31` — all paginated *endpoints* must use
   shared dependency functions; `:138` — "No inline pagination params: Every paginated endpoint
   must use `PaginationDep`"; `:80-81`, `:129` — an opaque base64url `cursor` and a `next_cursor`
   in the response envelope.
3. **What the design does.** `docs/DESIGN.md:411-466` is entirely about *consuming* Jobvite's
   offset paging: `start`/`count`, base-agnostic scans from `start=0`, a per-scan seen set, a
   completeness check against `total`. The caller-facing surface has **no cursor and no offset**:
   `docs/DESIGN.md:1175-1177` — "Result size is bounded inside each tool… a page is capped and the
   result says `showing 50 of 1,240`."
4. **The delegating leg checked by mechanism, not by name.** "Consumed, not implemented" is not a
   restatement of the dismissal; it is checkable, and it checks out — no `PaginationParams`, no
   cursor, no `next_cursor` reaches an MCP caller.

**Verdict: STANDING.** Re-arm condition, which the row does not currently carry: *if any tool ever
accepts a caller-supplied offset or cursor, or returns a continuation token, this standard's
envelope and parameter names become live.*

Observation, not a finding against the dismissal: the capped result (`showing 50 of 1,240`) gives a
caller **no way to ask for the rest** short of an exhaustive scan. That is a product question for
§4.5, not a standards obligation.

### 3.2 Hand-check 2 — `architecture/gdpr-data-rights.md` (D18): **TRIPPED** (already remediated in DESIGN.md; the dismissal row is stale)

1. **Frontmatter.** `standards/architecture/gdpr-data-rights.md:6-9` is
   `applicable_to: [system-design, all]`, `priority: required`. An `all` declaration is the same
   shape that made `threat-modeling.md` bind after being dismissed unread.
2. **The conditional leg holds.** The DSAR/RTBF machinery is table-scoped —
   `:50` ("Every table containing personal data MUST declare its DSAR/RTBF policy"), `:55-56`,
   `:60`, `:88`, `:113-117`. This server stores nothing (`docs/DESIGN.md:747-751`), and
   `docs/DESIGN.md:242-247` records that a durable server-side seen-set was **considered and not
   taken** precisely because it would need durable state. So statelessness is still true today.
3. **The delegating leg is where it fails.** The row at `STANDARDS.md:791` states that the residue
   which binds is *the no-PII-in-logs rule, captured as B88* — and names nothing else. That is
   incomplete. `gdpr-data-rights.md:119-129` (records of processing, Article 30) is field-level,
   names downstream processors, and is satisfied by neither statelessness nor B88.
   `docs/DESIGN.md:753-755` says so in the design's own words — *"What does bind, and is not
   waived: `:119-129`… so `docs/data-inventory.md` records the categories handled, the purpose, and
   the recipients"* — and `docs/data-inventory.md:1-6` exists and cites the same range.

**Verdict: TRIPPED.** A required standard's obligation escaped this dismissal and was recovered by
a *different* instrument (ADR-0008, §6.2, `data-inventory.md`), which never fed the correction back
into §3. **The obligation is discharged; the sentence dismissing it is false.** This is a
documentation defect, not an open design obligation — see §4/F1 for the fix.

### 3.3 Hand-check 3 — `ai/evaluation-testing.md` (D17): **STANDING**, and this closes a "could NOT verify" item

The row concedes it was never read. `STANDARDS.md:1065-1068` carries the same admission as item 3
of "What I could NOT verify". I read the file in full (170 lines).

- `standards/ai/evaluation-testing.md:6` — `applicable_to: [llm, langfuse]`.
- `:20-28` — its purpose is *automated model-output evaluation*, golden datasets and LLM-as-judge
  metrics, as the control for OWASP LLM09.
- `:30-33` — it explicitly distinguishes itself from human-review rubrics; it is "an executable gate
  on *model behaviour*".
- **The file contains zero `MUST` clauses** (`grep -c MUST` → 0).

This server produces no model output to regress. B23's own fail condition
(`STANDARDS.md:246-252`) is *"these tests exist but are not wired to a required CI check"* — a
pytest-and-CI obligation, discharged by `docs/DESIGN.md:733` ("Red-team cases live in the main suite
and are merge-gating"). The phrase "the eval suite" in `ai/prompt-injection.md:138-139` does not
import this file's golden-dataset structure into a server that judges nothing.

**Verdict: STANDING**, now on a full reading rather than an admission. See §4/F4.

### 3.4 `architecture/data-flow.md` and `architecture/threat-modeling.md` (D21): **threat-modeling TRIPPED** (already remediated); data-flow STANDING

`threat-modeling.md:6-8` is `applicable_to: all`, `priority: required`. The row's rationale —
"process/design-artifact standards rather than code obligations" — was already found wrong by
`docs/reviews/CONFORMANCE-DESIGN-ARTIFACT.md:44` ("`architecture/threat-modeling.md` — BINDS") and
`:344` ("dismissed UNREAD"). `docs/DESIGN.md:1562` now states the model is "Required by
`architecture/threat-modeling.md`", §11 supplies the STRIDE grid, and B110 tracks it.

`data-flow.md:6` is `applicable_to: [system-design]`;
`CONFORMANCE-DESIGN-ARTIFACT.md:209-211` records that the same rationale produced a correct verdict
for it "by luck". Correct verdict, wrong reason, and the wrong reason is still the one printed in
the table.

**Verdict: TRIPPED on `threat-modeling.md`** — remediated in the design, stale in `STANDARDS.md`.
See §4/F2.

### 3.5 `architecture/caching.md` (D20): **STANDING today**, and the re-arm condition is written down

This is the row that failed once. Re-tested rather than assumed:
`docs/DESIGN.md:1131` — "**`ResponseCachingMiddleware` is NOT adopted, and this reverses an earlier
revision**"; `:63` — "It caches no Jobvite response (§7.7)"; `:1732` — the cache-disclosure threat
row was removed from the model entirely rather than mitigated. `grep -n -i "cache" docs/DESIGN.md`
returns no adopted cache anywhere.

Note the difference in quality from the original dismissal: `docs/DESIGN.md:1148-1152` now states
the re-arm condition *in the design* — a key derivation established by execution and a two-token
isolation test before any cache ships. That is what makes this row testable rather than
discretionary.

### 3.6 The remaining re-tested rows

| # | Standard(s) | Test performed | Result |
|---|---|---|---|
| D1 | `frontend/api-client.md` | `grep -n -i openapi docs/DESIGN.md` → one hit, `:86`, saying no OpenAPI document exists for *Jobvite*. We publish no REST surface and generate no TS client | STANDING |
| D3 | `frontend/markdown-rendering.md` | Delegating leg tested by source, not by name: B24 (`STANDARDS.md:254-258`) is sourced from `ai/prompt-injection.md:49-50` and `:74-75`, an independent standard, and is discharged by `docs/DESIGN.md:723-724` (fencing, delimiter stripping). No circularity: the covering obligation does not rest on the dismissal | STANDING |
| D5 | `adr-ec-350-04` | The project now *has* inbound rate limiting (`docs/DESIGN.md:368-372`, ADR-0002), so this was worth re-reading. The ADR is scoped to evolv-coder's `/api/v1/public/reports/{shareToken}` behind Clerk-bypassing share tokens, with a Redis store. No share tokens, different product | STANDING |
| D6 | `database/*` | Tested against the two places the design flirts with durable state: `docs/DESIGN.md:242-247` (durable seen-set considered and **not taken**) and `:1069` (a store that is per-connection on stdio — rejected with §7.6). Nothing persists | STANDING |
| D9 | `backend/background-jobs.md` | `grep -n -iE "create_task\|background task\|celery\|worker"` — every hit concerns rate-limit buckets per worker process or an AnyIO thread at shutdown (`docs/DESIGN.md:74-79`, `:913-915`). No queue, no job, no worker role | STANDING |
| D10 | `backend/auth-guard.md` et al. | This row was worth a real check because §7.2 now *does* have authentication and scopes. `standards/backend/auth-guard.md:14-22` is a Clerk-JWT `get_current_user` dependency guaranteeing `db_id: UUID` and a `tenant_id` claim; `:6-9` is `applicable_to: [fastapi, express, dotnet, rest-api]`. `docs/DESIGN.md:796-801` uses `StaticTokenVerifier` and `require_scopes` — no users, no JWT, no tenant rows. `openapi-contract.md` is `priority: recommended` with zero `MUST` clauses | STANDING |
| D12 | cloud/IaC | `ls .github/workflows` → `mirror.yml` only, a git mirror job, no deploy. No Dockerfile, no IaC, no cloud target | STANDING |
| D14 | backup-DR / monitoring / environments | See §4/F3 — standing, with a residue the rationale over-dismisses | STANDING (residue) |
| D15 | `devops/git-workflow.md` | Delegating leg: the workflow gap it leaves is closed by `devops/development-workflow.md`, extracted as B89-B96 (`STANDARDS.md:1061-1063`), not by the dismissal itself. Non-circular | STANDING |
| D16 | `ai/*` (9 files) | `grep -n -iE "bedrock\|anthropic\|openai\|langchain\|embedding\|foundation model" docs/DESIGN.md` → **zero hits**. The server is a tool provider; it calls no model, holds no prompt template, spends no tokens | STANDING |
| D19 | `architecture/api-versioning.md` | `standards/architecture/api-versioning.md:6-11` is `applicable_to: [fastapi, express, dotnet, nextjs, rest-api]`, `priority: recommended`, zero `MUST`. MCP protocol eras (`docs/DESIGN.md:787-792`) are the framework's versioning axis, not a URL-versioned REST surface of ours | STANDING |
| D23 | documentation templates | `docs/DESIGN.md:1467-1507` (§10.1) commits to `readme-standard.md`'s fourteen sections and to `docs/adr/`. No PRD/BRD/discovery/onboarding/glossary deliverable is produced or promised | STANDING |

---

## 4. Findings

Every finding carries a suggested fix. **The fix sentences below are MY SUGGESTION and must be
verified before adoption** — I did not edit `DESIGN.md` and I committed nothing.

### F1 — Medium. The GDPR dismissal row states a residue set that the design has since outgrown.

`docs/research/STANDARDS.md:791` says the residue that binds is the no-PII-in-logs rule "captured as
B88", and names nothing else. `docs/DESIGN.md:753-755` and `docs/data-inventory.md:1-6` both record
that `gdpr-data-rights.md:119-129` (Article 30 records of processing) **also** binds and is
discharged by `docs/data-inventory.md`. A reader who trusts §3 gets a false picture of what this
required standard costs us, and the next person to re-derive the dismissal will re-derive the same
gap.

**Suggested fix (my suggestion — verify before adoption).** Replace the final sentence of the row
at `STANDARDS.md:791` with:

> **Two residues bind and neither is waived.** `:119-129`, records of processing under Article 30,
> is field-level and names downstream processors — routing candidate PII to a model is exactly
> that, and `docs/data-inventory.md` discharges it (ADR-0008 makes the scope argument for the
> DSAR/RTBF machinery and explicitly does not extend to this one). The second is the no-PII-in-logs
> rule, captured as B88, because a log file is the one place this stateless server could
> accidentally become a personal-data store.

### F2 — Medium. The `threat-modeling.md` dismissal row is false and its "could NOT verify" entry is stale.

`docs/research/STANDARDS.md:794` still reads "Not read in full; both are process/design-artifact
standards rather than code obligations. Flagged in 'What I could NOT verify'." That is contradicted
by `docs/reviews/CONFORMANCE-DESIGN-ARTIFACT.md:44` and by `docs/DESIGN.md:1562`, where §11 exists
*because* the standard binds. `STANDARDS.md:1070-1073` (item 4) repeats the stale claim.

**Suggested fix (my suggestion — verify before adoption).** Rewrite the row at `STANDARDS.md:794`
in place — do not append a correction beneath it — as two rows:

> \| `architecture/threat-modeling.md` \| required \| **Dismissal overturned by the design-artifact
> conformance sweep.** `:6-8` is `applicable_to: all`; it binds and is discharged by DESIGN §11's
> STRIDE grid and threshold disposition (B110). Listed here only so the original dismissal is not
> re-derived. \|
>
> \| `architecture/data-flow.md` \| required \| `:6` is `applicable_to: [system-design]`. Read for
> scope: it governs a data-flow artifact, and the flows it would document are recorded in DESIGN
> §11's trust boundaries and `docs/data-inventory.md`. **The verdict stands; the original
> rationale ("not read in full") did not support it.** \|

And amend item 4 at `STANDARDS.md:1070-1073` to strike `architecture/threat-modeling.md` from the
unread list, since it has since been read and cited.

### F3 — Low. `devops/environments.md` is dismissed on a rationale that covers only part of it.

The row at `docs/research/STANDARDS.md:787` dismisses three files together as presuming "owned
running infrastructure with an on-call rotation". That is right for
`backup-disaster-recovery.md` and `monitoring-alerting.md`, and right for the *rotation* half of
`environments.md` (`standards/devops/environments.md:626-654` — cadence tables, a secret store with
`last-rotated-at` metadata, `T-30` alerts, an on-call runbook). It is **not** right for the rest of
the file: `:141`/`:230` (`.env.example`), `:291` (a Settings class), `:612-622` (never commit
secrets) are repo-shaped obligations, and this repo defines five credential variables plus static
bearer tokens (`docs/DESIGN.md:796`, `.env.example`).

The dismissal does not trip, because the repo already conforms incidentally: `.env.example` exists
and is deliberately empty-valued, `.gitignore:13-15` ignores `.env`/`.env.*` while keeping
`.env.example`, and §7.3 uses `pydantic-settings`. **Verdict: STANDING with residue** — the risk is
that a correct verdict is resting on a rationale that does not reach the clauses, which is the
`data-flow.md` failure shape.

**Suggested fix (my suggestion — verify before adoption).** Split the row at `STANDARDS.md:787` and
give `environments.md` its own:

> \| `devops/environments.md` \| required \| Its rotation machinery (`:626-654` — cadence tables, a
> secret store with `last-rotated-at`, `T-30` alerts, an on-call runbook) presumes owned running
> infrastructure this repo does not have; secret rotation is an operator concern on the same
> footing as §7.2's read-only-key instruction. **Its repo-shaped clauses are not dismissed and are
> already met**: `.env.example` (`:141`, `:230`), a settings class (`:291`), and never-commit-
> secrets (`:612-622`) are satisfied by `.env.example`, `.gitignore` and §7.3's `pydantic-settings`. \|

### F4 — Low. "What I could NOT verify" item 3 can be closed.

`docs/research/STANDARDS.md:1065-1068` records `ai/evaluation-testing.md` as not read in full. It
has now been read in full (§3.3 above): `applicable_to: [llm, langfuse]`, zero `MUST` clauses, and a
scope confined to automated evaluation of model output.

**Suggested fix (my suggestion — verify before adoption).** Rewrite item 3 at `:1065-1068` in place:

> 3. ~~**`ai/evaluation-testing.md` (`priority: required`) — not read in full.**~~ **RESOLVED at the
>    freeze re-test.** Read in full: `:6` is `applicable_to: [llm, langfuse]`, `:20-33` scopes it to
>    automated evaluation of *model output* (golden datasets, LLM-as-judge, OWASP LLM09), and the
>    file contains no `MUST` clause. B23's fail condition is a merge-gating CI wiring, not this
>    file's suite structure, and §6.1 discharges it. The dismissal stands on a reading rather than
>    an admission.

### F5 — Low, process. §3 records no re-test state, which is why this had to be reconstructed from scratch.

Every row states a rationale and none states when it was last checked or what would re-arm it. The
two rows that have been repaired (`:781`, `:793`) carry their re-arm condition in prose only because
a reviewer wrote it there by hand.

**Suggested fix (my suggestion — verify before adoption).** Add one sentence under the table header
at `docs/research/STANDARDS.md:770`:

> **Re-test state lives in `docs/reviews/FREEZE-DISMISSAL-RETEST.md`, which enumerates every row in
> this table with its class (unconditional / conditional / delegating) and its result at the last
> freeze. A row whose rationale names a property of *our* design is a dated claim: the freeze
> procedure re-reads that property, it does not re-read this sentence.**

---

## 5. Appendix — dismissals outside the §3 table

The freeze criterion says *every* dismissal, and two substantial ones are inline in §2. Both were
re-tested and both stand.

| Where | Dismissal | Class | Test | Result |
|---|---|---|---|---|
| `STANDARDS.md:700` | "Clerk/JWT (`:68-517`) is not applicable — no human users" | CONDITIONAL | `docs/DESIGN.md:796` — HTTP auth is `StaticTokenVerifier` from environment; `:783-786` — stdio is unauthenticated by design, trust boundary is the OS. No human identity anywhere | STANDING |
| `STANDARDS.md:702-715` | The `ai/agent-guardrails.md` / `ai/tool-calling.md` loop-bound clause set is disposed of because "this server runs no loop" | CONDITIONAL | Re-tested against §7.5, which is the one place a loop could have appeared: MRTR is a **client** retry of the original call (`docs/DESIGN.md:983-991`), driven by `ctx.input_responses`. The server still runs no agent loop, so max-steps, recursion depth and tool-call budget still have nothing to bound | STANDING |

Also noted, and deliberately **not** re-done per instruction: `backend/idempotency.md` (D8,
TRIPPED, disposed as B108) and `devops/docker.md` (D13, re-tested STANDING).

---

## 6. What this method would have caught, and when

**`architecture/caching.md`.** The classification step files it CONDITIONAL and extracts the trigger
verbatim from its own rationale — *"if a cache is added it becomes live"*. The test is then a single
mechanical act: grep the current design for a cache. At the revision where
`ResponseCachingMiddleware` was adopted, that grep returns the adoption, and the row trips the same
day. **No reviewer discretion is involved, which is the point** — it was caught the first time only
because a second sweep happened to look.

**`backend/idempotency.md`.** The classification step files it DELEGATING on the leg "B19's
tool-level idempotency covers the residue", and the DELEGATING rule forces the question *what is B19
actually satisfied by?* — not *what is B19 called?* B19 is discharged by `create_candidate` never
being auto-retried. Set that against the residue the dismissal was covering, a **caller** replaying
the write, and the two do not touch. The circularity is visible in one step, and it is visible
without knowing in advance that this row was the guilty one.

**What neither would have needed:** a reviewer naming the row by hand. That discretion is exactly
what §13 now forbids, and it is what this document replaces.

---

## 7. Verdict

**One dismissal has tripped: `architecture/gdpr-data-rights.md` (D18), and a second row is false as
written for `architecture/threat-modeling.md` (D21).**

**Neither is an open design obligation.** Both escaped obligations were independently recovered
before this re-test — Article 30 by ADR-0008 / §6.2 / `docs/data-inventory.md`, and STRIDE by
DESIGN §11 and B110 — and both are discharged in the design today. What has tripped is the
**record**: `STANDARDS.md:791` and `:794` state dismissals the design no longer holds, and
`:1070-1073` repeats one of them.

**All 21 other rows are tested and STANDING**, including the two carried forward. No untested
dismissal remains, and none of the 16 rows re-tested here produced a new obligation on the design.

**On the freeze.** The design's substance is clear on this criterion: no dismissal has put a live,
undischarged obligation back on `DESIGN.md`. **The freeze blocker is F1 and F2 — two false
sentences in `docs/research/STANDARDS.md`** — because §13's own procedure treats that table as the
authoritative dismissal register, and freezing with a register that misdescribes two required
standards preserves the exact defect that produced the caching and idempotency failures. They are
prose corrections to one file, not design changes. **Fix F1 and F2 in place (do not append), and
this criterion is clear.** F3, F4 and F5 are improvements that reduce the chance of a third
recurrence and do not gate the freeze.
