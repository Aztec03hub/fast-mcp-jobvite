# Data inventory: records of processing

Required by `architecture/gdpr-data-rights.md:119-129` (records of processing, GDPR Article 30),
which is field-level and names downstream processors. ADR-0008 excuses this project from that
standard's DSAR and right-to-be-forgotten machinery **on scope grounds** - we store nothing, and
Jobvite is the controller's system of record - but explicitly does **not** excuse it from this.

**Status: describes the design, not a running system.** No implementation exists. Revisit at first
release and whenever an output model changes, because the models are what actually decide this.

---

## 1. Roles

| Role | Who |
|---|---|
| Controller | The Jobvite customer whose tenant the credentials belong to |
| Processor | This server, acting on that customer's instruction |
| **Downstream processor** | **The LLM host and model the tool results are returned to** |
| Source of record | Jobvite (Employ Inc.) |

**The third row is the unusual one and the reason this document exists.** A conventional integration
sends personal data to a database or another service. This one sends it into a language model's
context, on infrastructure the operator chose and we do not control. That is a disclosure to a
downstream processor and it should be recorded as such rather than treated as an implementation
detail of "returning a result".

## 2. Categories of personal data processed

Only fields on an allow-listed output model (§2.1) can leave this server. This table is generated
from those models; a field absent from a model is absent from processing.

| Category | Fields | Source |
|---|---|---|
| Identity | first name, last name | Jobvite candidate record |
| Contact | email, mobile, work phone, home phone | Jobvite candidate record |
| Employment history | work experience entries | Jobvite candidate record |
| Education | education entries | Jobvite candidate record |
| Application linkage | candidate id, application id, job id | Jobvite |
| **Candidate free text** | résumé body, cover letter, notes | **Authored by the data subject** |

**Free text is both personal data and untrusted input.** It is the only category that is a security
control surface as well as a privacy one, and §6.1 fences it before it reaches a model.

## 3. Categories deliberately NOT processed

| Category | Fields | Why |
|---|---|---|
| Special-category data | gender, race, veteran status | Present in Jobvite responses; **excluded from every output model, so never leave the server.** ADR-0008 |

The exclusion is structural rather than procedural: the fields are not on the models, so there is no
code path that emits them and no configuration that re-enables them.

## 4. Purpose

To let an authorised operator query their own Jobvite tenant through a language model - searching
candidates, retrieving a candidate, searching jobs, reading the public job feed, and optionally
creating a candidate.

**No secondary purpose.** Nothing is processed for analytics, training, product improvement, or
aggregation. This server does not send data anywhere except back to the caller that asked for it.

## 5. Retention

**None.** The server holds no candidate data between calls (§1). What outlives a call is an HTTP
connection pool and rate-limiter token buckets, neither of which holds personal data. There is no
cache: `ResponseCachingMiddleware` was considered and rejected, partly for this reason (§7.7).

**The one exception, and it is real:** the audit event (§5.3) records the approval request for a
write, which describes the candidate about to be created. **The audit stream therefore holds
candidate personal data by construction**, and carries the same handling class as the log stream -
single-point redaction, treated as sensitive. Log and audit retention is the operator's, set by
wherever they send those streams. That is outside our control and inside their responsibility, and
the README says so.

## 6. Recipients and transfers

| Recipient | What they receive | Control |
|---|---|---|
| The calling MCP client and its model | Allow-listed fields for the tools their token permits | Bearer token, three scopes by data class (§7.2) |
| The operator's log and audit sink | Redacted records; PII in the audit event for write approvals | Single-point redaction (§4.1) |
| Jobvite | Only what a write sends, and only with approval | HTTPS, header credentials, never in a URL (§4.1) |

**No transfer outside the operator's own infrastructure is initiated by this server.** Where the
model runs, and therefore where candidate data is processed, is determined entirely by the
operator's choice of host. We cannot see it and do not control it.

## 7. Security measures, by reference

Not duplicated here, per the single-source rule. Transport encryption and the off-loopback refusal
(§7.1); authentication and scoping (§7.2); allow-listed output models (§2.1); fencing of
attacker-authored content (§6.1); single-point redaction (§4.1); audit logging (§5.3). The threat
model at §11 rates the disclosure paths and names which are mitigated and which are residual.

## 8. What this document cannot tell you

- **Whether the model host retains what it is sent.** Outside our boundary, and the operator's
  question to their host.
- **What Jobvite retains.** They are the source of record and their retention is the controller's
  arrangement with them.
- **Whether a field we have never observed carries personal data.** No success response from Jobvite
  has been observed except one (§1.1), so this inventory describes the fields our models admit, not
  necessarily every field Jobvite returns. **A field Jobvite adds does not reach a caller** - the
  allow-list drops it - but this table would not know about it either.
