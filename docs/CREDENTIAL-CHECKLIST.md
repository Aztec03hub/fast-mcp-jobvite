# Day-one credential checklist

**Read this before trusting any success-path behaviour in this repository.**

Nobody who built `fast-mcp-jobvite` held a Jobvite credential. Jobvite publishes no API
documentation and operates no sandbox, so **no success response from Jobvite has ever been
observed by this project.** Every request shape here was derived from working third-party
clients and Jobvite's own 2014-era documentation; every success response shape is a hypothesis.

The test suite reflects that honestly. Error-path fixtures are byte-exact recordings of real
Jobvite transport. Success-path fixtures are synthetic. **A green suite proves this client is
internally consistent. It does not prove this client speaks Jobvite.**

This document is how that gets fixed. Work the rows in order the day a real key exists, capture
each full response, and replace the corresponding synthetic fixture with the recording.

Provenance labels used below match `docs/research/JOBVITE-CONTRACT.md`: `[RECORDED]` observed,
`[INFERRED]` from a working third-party client, `[ASSUMED]` reasoned but unverified.

---

## Blocking rows

**Rows 1-4 block any claim that the success path is verified.** Until they are ticked, treat
`search_candidates`, `get_candidate`, `search_jobs` and `get_job_feed` as unproven against the
live API, and say so in any report.

| # | Check | Why it blocks | What observing it settles |
|---|---|---|---|
| 1 | `GET /api/v2/candidate?count=1` — capture the **full** response, headers and body | The entire success-path contract is unobserved | Whether a success body carries a `status` block at all; the real envelope keys, field names and types; and whether any rate-limit header exists |
| 2 | `GET /api/v2/candidate?count=1&start=0` versus `&start=1`, comparing returned `eId`s | A silent off-by-one skips or duplicates a record on **every** page, and no synthetic fixture can catch it | Whether `start` is 0-based or 1-based. We ship 1-based on Jobvite's own v1 documentation; three third-party clients disagree with each other |
| 3 | `GET /api/v2/candidate?count=501` | We enforce a 500 page cap client-side purely on third-party say-so | Whether 500 is a real server limit, and whether exceeding it errors or **silently truncates** |
| 4 | `GET /api/v2/candidate?candidateId=<nonexistent>` | We cannot currently distinguish "no such record" from "no such route" from "empty page" | The record-level not-found shape. A route-level `404` means the endpoint does not exist, which is a different thing |

---

## Ask this when the key is requested, not after

**Row 0 is not an observation against the API. It is a question to a human, and it must be asked
before a key is issued rather than discovered afterwards**, because the answer changes what a
deployment is allowed to claim and there is no way to establish it from our side.

| # | Ask Jobvite Customer Success | Why it cannot wait, and why we cannot answer it ourselves |
|---|---|---|
| 0 | **Does Jobvite issue a read-only API key, and if so, request one for every deployment that runs with `JOBVITE_ENABLE_WRITES=false`.** Record the answer here either way | DESIGN.md §7.2 requires a read-only key where writes are disabled, and C5-E1 is a **High** residual precisely because we cannot enforce it. **No Jobvite endpoint reports a key's own permissions**, so a read-only key and a write-capable key are indistinguishable to us; establishing it by attempting a write is the destructive probe §1.1 forbids. **If the answer is no, the exposure is undiminished** and the Residual Risks entry stands as written - which is the outcome to record plainly, not to leave as an unticked box that reads like an oversight |

---

## Non-blocking rows

| # | Check | What observing it settles |
|---|---|---|
| 5 | `GET /api/v2/job?ids=<a>,<b>` | Whether `ids` accepts a list, and whether it silently ignores extras |
| 6 | `GET /api/v2/job` with `datestart` / `dateend` | Whether job date filtering exists and under what parameter names. Incremental sync depends on this and the names are pure assumption |
| 7 | `GET /api/v2/<resource>?count=1` for each of the 13 undocumented v2 resources | Their envelope keys and field shapes. **The single highest-yield step for expanding tool coverage** beyond the five operations we ship |
| 8 | `PUT` and `DELETE /api/v2/candidate` **with a deliberately invalid id** | Whether these methods are implemented at all |
| 9 | Repeated `GET` at increasing rate | Whether a `429` exists, what it returns, and whether it carries backoff guidance. Jobvite documents no limit and returns no rate-limit headers |
| 10 | One `POST /api/v2/candidate` in a customer-agreed window | The `201` shape, the `EId` casing asymmetry, and the `409` duplicate behaviour on an intentional repeat |

---

## Two rows that carry safety conditions

**Row 8 — use an invalid id, always.** The `OPTIONS` response cannot answer whether `DELETE` is
implemented: it returns an identical `Allow: GET,HEAD,POST,PUT,DELETE,OPTIONS` header for routes
that do not exist, because it is a servlet-container default describing the dispatcher rather
than any handler. That was tested and confirmed against a garbage path. The only way to confirm
`DELETE` by success is to destroy a customer record, so **never** do that: probe with an invalid
id and read the error.

**Row 9 — run it last, and stop at the first `429`.** It is a deliberate rate-limit probe against
a production system with no documented limit. Do not run it in parallel with anything else, and
do not "confirm" the limit by exceeding it repeatedly.

**Row 10 — there is no sandbox.** This creates a real candidate record in a real applicant
tracking system, and Jobvite's create endpoint can email a human candidate. It requires the
customer's explicit agreement, a named test job, and an agreed cleanup path **before** it runs,
not after. `send_email` defaults to `false` in this client precisely because the destructive side
effect of this endpoint is not the database row.

---

## Closing a row

For each row:

1. Capture the full response — status line, all headers, exact body bytes.
2. Redact credentials before the capture touches disk. This repository is public and has already
   had one incident of confidential material reaching a published commit.
3. Replace the synthetic fixture with the recording, and relabel it `[RECORDED]`.
4. If the observation contradicts `docs/research/JOBVITE-CONTRACT.md`, **edit that document to
   say the right thing.** Do not append a correction beneath the wrong text; a document holding
   two contradictory claims cannot be reviewed.
5. Tick the row here with the date and who ran it.

When rows 1-4 are closed, remove the unverified-success-path caveat from `README.md` — and not
before.
