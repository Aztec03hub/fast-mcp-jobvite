# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Timestamps are America/Chicago.

## [Unreleased]

No release yet. **The server runs.** `fast-mcp-jobvite` boots on stdio and HTTP and exposes four
read tools - `search_jobs`, `get_job_feed`, `search_candidates`, `get_candidate` - plus
`create_candidate`, which is registered only when writes are enabled AND the tool is named, and
which pauses for an approval the host must answer. Its Quickstart is executed by CI on every merge.
Entries below record both the design decisions the implementation was built against and the units
built so far.

**Nothing here proves a human approved anything.** The approval is answered by the host, and this
server cannot tell a person from a handler - see the README's disclosures.

### Security

- **`DESIGN.md:165`'s 1 MiB request-body limit now exists**, as an ASGI middleware on the HTTP
  transport. It refuses **before the application is entered** - measured: an 8 MiB chunked body with
  no declared length is refused with the app handed 917,504 bytes, fewer than the cap, because the
  chunk that crosses never reaches it. Refusals are `/problems/validation-error` **422**, not 413:
  the error registry has no 413 row and a new `type` URI is a promise owed forever, so the reason
  lives in `detail` (ADR-0029, ADR-0031). **HTTP only** - there is no body on stdio, where the
  separate argument-payload bound applies; the two are not duplicates. (2026-08-29 10:32 AM CDT)

- **The log redaction now installs itself from `JobviteClient`'s constructor**, on `httpx2`'s
  standard-library logger, so an embedder who never calls
  `fast_mcp_jobvite.__main__.configure_logging()` no longer receives the job feed URL's `api`, `sc`
  and `companyId` in the clear. **The shipped server was never exposed** - `configure_logging()`
  runs on every shipped path - and this closes an *embedder's* exposure. The install is idempotent:
  the client is rebuilt once per invocation, so a filter appended per construction would grow
  without bound. ADR-0026. (2026-08-29 10:32 AM CDT)

### Added

- `JobviteClient(install_log_redaction=False)` opts out of that side effect for an embedder who
  wants their logging configuration untouched. **A constructor argument, never a setting** - a
  setting nothing reads is what ADR-0025 is about. (2026-08-29 10:32 AM CDT)

- **The three structural limits `DESIGN.md:162-164` names and nothing enforced** - nesting depth 5,
  1,000 list items, 100 dict keys - plus a 1 MiB bound on the serialised argument payload, in
  `utils/constraints.py` and applied to every tool input model through a shared `InboundModel` base
  rather than per model. The sweep that proves it runs over an input-model set discovered by **two
  independent AST walks asserted equal**, never over a list: the brief said four models and the
  discovery found **five**. (2026-08-29 09:04 AM CDT)
- **ADR-0029**, recording that §2.1's body-size limit belongs at a middleware this design does not
  have, and that the argument payload cap is not that limit. (2026-08-29 09:04 AM CDT)

- **`search_candidates` and `get_candidate`.** Two tools rather than one, because the shapes differ:
  one returns a page and one returns a record, and a single tool cannot advertise two return
  schemas. Candidate records are **allow-listed** - a field Jobvite returns that is not declared
  does not reach the caller - and **no EEO field can be carried at all**, which is a property of the
  output model rather than a filter that could be forgotten. Free-text fields are fenced, including
  content that tries to close its own fence. (2026-08-29 08:41 AM CDT)
- **`get_job_feed`**, the public job feed, on its own credential class
  (`JOBVITE_FEED_KEY`, `JOBVITE_FEED_SECRET`, `JOBVITE_COMPANY_ID`). It is the one route whose URL
  structurally carries its credentials, so that URL never reaches a log record whole and `sc=` is
  redacted before any line is written - asserted against a log stream proven non-empty by the same
  call, including the HTTP library's own record. (2026-08-29 08:41 AM CDT)
- **`create_candidate`, behind an approval the host must answer**, and registered only when writes
  are enabled AND the tool is named. The request names the candidate, the target job, and whether an
  email will be sent. **`send_email` defaults to false; setting it true mails a real person.** A
  duplicate is reported as `/problems/conflict` naming the duplicate. **The server requires an
  approval response and refuses to write without one - it cannot and does not claim a human
  approved anything.** (2026-08-29 08:41 AM CDT)
- **Bearer-token authentication and per-token scopes on the HTTP transport.** A tool the caller's
  token does not hold is absent from the tool list entirely, so a direct call reports it unknown
  rather than forbidden - documented in the README, because it is correct and surprising. Rate
  limiting is **per client** rather than the framework's default of one shared bucket, and the
  inbound `X-Request-ID` is validated as a UUIDv4 before use and echoed back on every result. (2026-08-29 08:41 AM CDT)

- **Resilience on every outbound call: per-phase timeouts, then retry, then a circuit breaker**, in
  that order. Retries use jitter and fire only for connection errors, timeouts and 5xx; a `429` is
  retried and then reported as a 503 honouring `Retry-After`. **`create_candidate` is excluded from
  retry by construction rather than by configuration**, so no setting can turn it back on - a
  retried write emails a second live human. (2026-08-29 06:18 AM CDT)
- **A total outbound budget bounding every attempt for one tool invocation.** A slow upstream now
  becomes a typed 503 rather than an unbounded wait, and one scan shares one budget rather than
  opening a fresh one per page. (2026-08-29 06:18 AM CDT)
- An open circuit and an upstream outage both return `/problems/service-unavailable`, distinguished
  by their `detail` and carrying a `retry_after` hint, so a caller can tell "Jobvite is down" from
  "this server has stopped calling Jobvite for now". (2026-08-29 06:18 AM CDT)

- **Base-agnostic offset paging in the Jobvite client.** Every scan starts at `start=0`, which is
  the whole mechanism and is one character: a 0-based server returns record zero, and a 1-based
  server returns the same first page it would have returned anyway. Starting at 1 is the only
  choice that can silently lose a record. Returned ids are checked against a per-scan seen set, so
  a clamped or overlapping page drops duplicates - **de-duplication defends against over-reading
  only and cannot recover a record that was never returned**, which is why the fix is starting at
  zero rather than de-duplicating harder. A scan terminates on a short page and never on the
  reported `total`, so a `total` that lies neither shortens nor extends it. (2026-08-29 05:12 AM CDT)
- Completeness is checked against `total` **only on an exhaustive scan**. A capped call is a
  mismatch by design - it reports `showing 50 of 1,240` - so wiring the check to every call would
  fire the alarm on the default path and train everyone to ignore it. (2026-08-29 05:12 AM CDT)
- The pagination start base, with `JOBVITE_PAGINATION_START_BASE` as an override for anyone who has
  established which base a resource actually uses. The client's own override is per-resource; the
  environment variable is one value, applied to every route the calling tool asks the client for.
  **Whether `start` is 0- or 1-based remains unestablished as a fact about Jobvite**: the vendor
  documents 1-based, and what is observed is only that `start=0` is accepted and returns records.
  Correctness does not rest on which is true. (2026-08-29 05:12 AM CDT)

- **`search_jobs`, and with it the first runnable server.** The tool composes every cross-cutting
  mechanism the earlier units built - configuration fail-fast, the RFC 9457 error contract, the
  audit path, the result cap and `_meta` - on the public job-data class, which is the least
  dangerous one in the tool surface. A single page is returned, capped at `JOBVITE_MAX_RESULTS` and
  reporting `showing N of total` rather than truncating silently. (2026-08-29 04:31 AM CDT)
- The allow-listed output model for the job list. A field Jobvite returns that is not declared there
  does not reach the caller, and a new Jobvite field is dropped rather than failing the call. (2026-08-29 04:31 AM CDT)
- **The fencing-path registry, generated from the output models rather than maintained beside
  them.** Model attributes are snake_case and fencing paths are Jobvite's camelCase, so two
  hand-kept lists that must correspond would be a defect waiting for the first schema change. Every
  field carries an explicit decision and a reason; a field with none raises at generation time
  rather than defaulting. (2026-08-29 04:31 AM CDT)
- The shared inbound constraint rule every input model reuses, under ADR-0012: control characters
  and bidi overrides are refused. A name carrying a NUL or a bidi override is a well-formed short
  string that every length and regex check admits, which is why the rule is separate from
  `max_length`. (2026-08-29 04:31 AM CDT)
- **Jobvite client with a single request entry point**, checking every call against the
  error-detection rule before returning a body: a response is successful only if the body carries no
  `status.code` of 400 or above **and** the HTTP status is below 400. Both, every call. This matters
  because `api.jobvite.com` answers a rejected credential with HTTP 200 and a body saying 401 - a
  client trusting the HTTP status reports zero results for a credential that was actually
  refused. (2026-08-29 04:31 AM CDT)
- Error bodies are decoded without assuming JSON and without relying on `Content-Type`, which the
  job-feed route does not send: the JSON status envelope, plain text and Tomcat HTML error pages are
  all recognised as failures rather than degrading to an empty result. XML is parsed with a hardened
  parser and always treated as an error. (2026-08-29 04:31 AM CDT)
- Credentials travel as request headers, and no URL containing a secret is ever built. The one route
  that structurally requires credentials in its query string is treated as sensitive: never written
  to a log line or an error message in full. (2026-08-29 04:31 AM CDT)
- **Per-invocation audit event for every tool call**, carrying the tool name, redacted arguments,
  result status, latency and `request_id`, plus the transport and - on HTTP - the resolved client
  id. On stdio the event records that caller attribution is unavailable rather than implying an
  identity that does not exist. W3C trace context is recorded when the caller supplies it and
  omitted when it does not; it is never synthesised. (2026-08-29 04:31 AM CDT)
- **Secret redaction at a single enforcement point.** The `jobFeed` URL's `api`, `sc` and
  `companyId` query parameters are redacted before any log line, including where the URL appears
  inside an exception message, and tool arguments are redacted by a fail-closed allow-list so a
  field added later is redacted until it is allowed deliberately. (2026-08-29 04:31 AM CDT)
- **The server boots**: configuration, transport selection, and a graceful shutdown that runs
  lifespan teardown on SIGTERM. `fast-mcp-jobvite` is now a console script. (2026-08-29 04:31 AM CDT)
- Configuration is validated at boot and names every variable it refuses on, scoped to the tools
  actually enabled, so a deployment running only candidate search is not asked for a job-feed
  company id. (2026-08-29 04:31 AM CDT)
- An unrecognised name in `JOBVITE_TOOLS` is a startup failure rather than a silently disabled
  tool. (2026-08-29 04:31 AM CDT)
- Binding a non-loopback address without `JOBVITE_TLS_TERMINATED_BY_PROXY=true` refuses to start:
  this server terminates no TLS of its own, and an off-loopback bind would carry a bearer token and
  candidate PII in the clear. (2026-08-29 04:31 AM CDT)
- `JOBVITE_MCP_TRANSPORT=http` without `JOBVITE_HTTP_TOKENS` refuses to start rather than serving an
  open server. (2026-08-29 04:31 AM CDT)
- `server.json` declares all fifteen environment variables for registry consumers. (2026-08-29 04:31 AM CDT)
- **`README.md`**, written against `documentation/readme-standard.md`: all fourteen sections in the
  prescribed order, a configuration table covering every environment variable the server reads, and
  copy-paste-runnable examples. Its Quickstart is parsed and executed by CI, so an example that
  stops working fails the build rather than sitting there. (2026-08-29 04:31 AM CDT)
- ADR-0018 (Proposed): the forced exit in the shutdown path reports a crash as a clean stop. (2026-08-29 04:31 AM CDT)
- ADR-0021, recording that the audit event's approval "mechanism" is required by two `DESIGN.md`
  rows and defined by neither. (2026-08-29 04:31 AM CDT)

- **`docs/DESIGN.md` is frozen at revision 6.** Only a numbered ADR may change it from here.
  The freeze certifies a 0C/0H/0M round, an empty must-mitigate table, and every conditional
  dismissal re-tested and recorded. It explicitly does not certify correctness: three carried risks
  are named in the status block, including that five defects were found by attempting to build and
  none by reading. (2026-08-28 03:04 PM CDT)
- §3 records where input models live - beside their tools, with `models/` explicitly output-only.
  A file boundary rather than a naming choice, and it is what lets implementation agents run
  concurrently without overwriting each other. (2026-08-28 03:04 PM CDT)

- `JOBVITE_MCP_HOST`, `JOBVITE_MCP_PORT` and the secret-class `JOBVITE_HTTP_TOKENS`. §7.1 said the
  server binds loopback "unless told otherwise" and named nothing that does the telling, and §7.2
  said the token verifier is "built from environment" without naming the variable. Found by trying
  to build against it: the HTTP unit could not be started, let alone bound off-loopback to exercise
  the TLS-refusal tests. (2026-08-28 02:46 PM CDT)

- `JOBVITE_MAX_RESULTS` (default 50) and `JOBVITE_OUTBOUND_RATE_LIMIT` (default 6/min), the two
  settings that were specified without names and left `.env.example` incomplete by construction.
  The rate limit is recorded as a conservative guess rather than a vendor figure, because Jobvite
  documents no numeric limit at all. (2026-08-28 02:21 PM CDT)

- A disposal of the no-ambient-authority requirement, which two binding standards state and which
  no B-number, sweep verdict or ADR had ever covered. `get_candidate` resolves a record from a
  model-supplied id; that is not ambient authority here because one API key and one company id per
  deployment leave no caller-scoped record set to discriminate on. Stated as a property of our
  deployment model rather than of Jobvite, whose permission model we have never seen, and carrying
  an expiry: per-user or multi-tenant scoping makes the clause live again. (2026-08-28 02:09 PM CDT)
- `docs/CREDENTIAL-CHECKLIST.md` row 0, asked of a human before a key is issued rather than
  observed against the API afterwards: does Jobvite issue a read-only key at all, and request one
  for every deployment running with writes disabled. If the answer is no, the exposure is
  undiminished and that is recorded rather than left as an unticked box. (2026-08-28 02:09 PM CDT)

- Threat model as `DESIGN.md` §11, required by `architecture/threat-modeling.md`, which four of
  its six triggers reach. Ten assets, seven trust boundaries, sixty STRIDE rows across nine
  components, and residual risks, every rated row checked against the standard's own matrix.
  Independently validated by a reviewer who did not write it, since its author cannot be its
  reviewer. (2026-08-27 04:20 PM CDT)
- Ten architecture decision records, each citing the clause it deviates from at `file:line`, plus
  one obligation recorded as knowingly unmet because the corpus contradicts itself about the ticket
  prefix it requires. (2026-08-27 04:56 PM CDT)
- `docs/data-inventory.md`, the Article 30 record of processing. It names the language model host
  as a downstream processor, which is the disclosure a conventional integration does not make.
  (2026-08-27 04:56 PM CDT)
- Design document scoping v1.0 to five Jobvite operations, with the module layout, error
  contract, resilience model and testing strategy. **Not frozen.** Four adversarial rounds have
  run and the most recent recommended against freezing; the freeze rule is that a round must
  return 0C/0H/0M first, after which only a numbered ADR may change it. (2026-08-27 02:23 PM CDT)
- Decision log covering D1-D16, each recording what was decided and the evidence behind it.
  (2026-08-27 02:15 PM CDT)
- Day-one credential checklist: the ordered observations that convert synthetic success
  fixtures into recorded ones when a Jobvite key first exists, with rows 1-4 marked blocking
  and safety conditions on the two rows that touch production data.
  (2026-08-27 02:31 PM CDT)
- Security policy, covering the two failure classes specific to this server: candidate-authored
  free text escaping its delimiters and reaching a model as instructions, and credentials
  leaking through logs via the v1 job feed's query-string authentication.
  (2026-08-27 02:31 PM CDT)
- Six research reports: the Jobvite API surface and client contract, FastMCP capabilities, two
  executed runtime spikes, the binding standards, and a repository compliance specification.
  (2026-08-27 02:23 PM CDT)
- Apache-2.0 licence with a completed copyright line, plus a NOTICE that also disclaims
  affiliation with Jobvite. (2026-08-27 02:23 PM CDT)
- Canonical hosting on `evolvconsulting/fast-mcp-jobvite` with an automatic mirror to
  `Aztec03hub/fast-mcp-jobvite`, via a dual-push-URL `origin` plus a `mirror.yml` workflow for
  pushes originating elsewhere. (2026-08-27 01:52 PM CDT)
- `.gitignore` and `.env.example`: the environment template names the ten variables settled so far,
  with every value empty, since a placeholder that looks like a credential is what a reader copies
  by accident. Two more are specified but unnamed - the result cap and the outbound rate-limit
  setting - and the template is not complete until they land. (2026-08-27 01:37 PM CDT)

### Changed

- **`ci.yml`'s design citations no longer carry line numbers, so a re-freeze cannot stale them.**
  The re-freeze at `8a9d63c` left 18 of the file's 20 `DESIGN.md:NNN` citations pointing at text
  that had moved - each still RESOLVED, each now naming a different sentence, and no checker covers
  `ci.yml`. All 20 are now subject phrases (`DESIGN.md §8's zero-skips clause`), the remedy
  `OBLIGATIONS.md` already took: an anchor with no line number cannot drift. The two that had NOT
  gone stale were converted as well rather than left, because fixing only the members that broke is
  how the next re-freeze finds them. Two citations are deliberately kept with their numbers - they
  are illustrations OF the bare-text citation form, not pointers to content, and a comment now says
  so. (2026-08-29 01:03 PM CDT)

- **`main`'s in-progress CI run is no longer cancelled; every other ref still cancels.** `cancel-in-progress` was true for
  all refs, which is right for a busy branch and wrong for a trunk: on `main` the run IS the record,
  and a cancelled run leaves none. Measured on 2026-08-29, `main` had **54 cancelled runs, 5
  failures and zero successes in a day** - and because a cancelled conclusion is not a failure,
  nothing read as red while the trunk had been broken for hours. Each push cancelled the evidence
  that the previous one was broken. **This does not mean every commit gets a run:** measured after
  the change, GitHub keeps at most one PENDING run per concurrency group and cancels older queued
  ones regardless of the setting - two were cancelled having never scheduled a runner at all. What
  it buys is a trunk that always has a run which will reach a conclusion, where before it had 54
  cancellations and none. (2026-08-29 12:45 PM CDT)

- ADRs separated from the freeze. The two jobs the instrument was doing - recording a deviation
  from a required standard, and being the only thing that may change a frozen design - were stated
  in consecutive sentences of the same README and had no way to be told apart. Deviations are
  recorded when decided and are independent of the freeze, which is why eleven exist against an
  unfrozen design; from ADR-0012 each carries a `Type:` field. (2026-08-28 12:54 PM CDT)
- The freeze rule now requires §11's must-mitigate table to be empty as well as a 0C/0H/0M round.
  The two came apart in practice: rounds returned few findings while the table still held High rows
  whose remedies were edits to this document, and freezing then would have put a document's own
  stated remedies behind the process that exists to protect a settled design.
  (2026-08-28 12:54 PM CDT)

- Human-in-the-loop approval reworked after execution refuted the design. MRTR works on the
  sessionless era and raises on the handshake era; `ctx.elicit()` does the reverse. The two are
  exactly complementary, a default stdio install lands on the handshake era, and the previous
  guard branched on an attribute present on both eras, so it discriminated nothing. The
  discriminator is now the negotiated protocol version, and an unidentifiable era refuses the
  write. (2026-08-27 04:05 PM CDT)
- Confirmation token cut. Neither it nor elicitation distinguishes a human from an agent, so it was
  a second copy of a control rather than a second control, and its store is per-connection on the
  default transport. (2026-08-27 04:45 PM CDT)
- `ResponseCachingMiddleware` dropped. The cached data is candidate personal information, the scope
  model exists so different callers see different data, and this framework's sibling middleware
  measurably defaults every caller to one shared bucket. (2026-08-27 03:55 PM CDT)
- Pagination now starts at zero and de-duplicates, after two earlier mechanisms were each wrong in
  a different direction. (2026-08-27 05:05 PM CDT)

- Licence changed from MIT to Apache-2.0. MIT had been a default rather than a choice. A survey
  of all 187 repositories in the organisation found no house convention to follow - 174 carry no
  licence at all - so the choice was made on merit: Apache's express patent grant matters for a
  connector facing enterprise legal review. (2026-08-27 02:23 PM CDT)
- Framework target changed from the stable `fastmcp` line to `4.0.0b4` and the sessionless
  `2026-07-28` MCP specification, as deliberate early adopters. (2026-08-27 01:58 PM CDT)

### Security

- **A failed call to Jobvite no longer puts the HTTP library's own exception text into the error
  returned to the caller.** That text carries whatever the library chose to write into it - the
  request URL, a TLS source file and line number, a local socket path - and it reached the caller
  unchanged. Callers now get one of three stable reasons instead, which still distinguish an
  upstream failure from a circuit breaker this server has opened; the full text goes to the log,
  redacted. (2026-08-29 04:31 AM CDT)
- **An exception's text and traceback are now redacted on their way to the log stream.** Redaction
  ran over a record's message, and the serialising sink writes more than the message: an exception
  logged by any library in the process reached stderr with the job-feed URL - and therefore the
  `api`, `sc` and `companyId` credentials - in the clear, measured twice in one record. Confirmed
  before the fix by a probe that plants a credential-shaped URL in a real child process and reads
  what that process writes. (2026-08-29 04:31 AM CDT)
- The v2 credential headers are redacted before a failure is logged. The header redactor existed and
  had no caller until this line needed it. (2026-08-29 04:31 AM CDT)
- **The Jobvite job-feed URL no longer reaches the log stream in the clear.** The HTTP client library
  logs each request URL through the standard library's logging, which the server configured at INFO
  on stderr, and that URL structurally carries the `api`, `sc` and `companyId` credentials. Every
  record now passes through the project's single redaction point on its way to the sink, whichever
  library produced it. (2026-08-29 04:31 AM CDT)

- The caller-replay path on `create_candidate` now carries a stated ceiling instead of an unexamined
  acceptance. The standard permits a retried write only behind an idempotency key; nothing
  establishes that Jobvite accepts one, so the ceiling is recorded with the condition that expires
  it rather than a control being claimed. (2026-08-28 02:01 PM CDT)

- `request_id` now reaches the caller on every result, not only on errors, in the result's `_meta`
  under a namespaced key. Executed rather than assumed: an undeclared top-level key in structured
  content is rejected by the same unconditional output-schema validation that broke
  `ResponseLimitingMiddleware`, while `_meta` is never inspected by the validator and survives a
  serialise round trip. (2026-08-28 01:35 PM CDT)
- The audit event records the inbound W3C trace context beside `request_id`, discharging
  `ai/tool-calling.md:176-177`. Recorded when present, omitted when absent, never synthesised - a
  locally-minted id in a field named for the host's trace joins nothing while looking like it does.
  (2026-08-28 01:35 PM CDT)

- The three freeze blockers closed, emptying §11's must-mitigate table. Retries and breaker
  transitions are now logged with the invocation's correlation id, carried by a `ContextVar` to
  hooks the resilience library calls with no argument we control; a module global would interleave
  concurrent invocations silently, each line still carrying a well-formed id, so the test asserts
  under concurrency. Where writes are disabled the Jobvite key must be read-only - recorded as an
  operator instruction with a stated ceiling, since the server cannot verify a key's rights and
  whether Jobvite issues read-only keys at all is unknown. And `pip-audit`, which fails on any
  advisory on a deliberately beta stack, has a four-step triage policy whose ignores carry a 30-day
  expiry that CI enforces. (2026-08-28 12:54 PM CDT)

- Off-loopback binds require TLS or a declared terminating proxy, and the server refuses to start
  otherwise. The flag is an operator assertion rather than a check of `X-Forwarded-Proto`, which
  would authenticate the attacker's own claim about their connection. (2026-08-27 04:15 PM CDT)
- The approval request must state what is being authorised, including whether an email is sent. A
  guard that checks only that something was approved lets an approver authorise an email nobody
  mentioned. (2026-08-27 04:30 PM CDT)
- Inbound argument limits: nesting depth, list length, dict keys, body size, and control-character
  rejection. (2026-08-27 05:10 PM CDT)

- Purged a CONFIDENTIAL-marked vendor PDF and an unlicensed RAML file from the repository's git
  history after they reached both public remotes. The history rewrite alone proved insufficient,
  because the blob remained fetchable by commit SHA; closing the exposure required making both
  repositories private. Vendored third-party source documents are now blocked by gitignore.
  (2026-08-27 02:45 PM CDT)

### Fixed

- **Main was red on two gates, and one of them was a row I ruled into existence.** ADR-0032's new
  STRIDE row `C2-T2` carried a Test cell reading `§8: <a test function name>`. That prefix asserts a
  §8 CASE, and the coupling gate requires the named case to exist in §8 - a test name is not one. My
  ruling fixed the row's id and its Likelihood/Impact and said nothing about the disposition column,
  so the row was added in a form the gate refuses. The Test cell now reads `not required (Low)`,
  which is the vocabulary's own term for the exemption a Low row has, and the tripwire it was
  pointing at is named in the MITIGATION column where it belongs - nothing is lost and nothing is
  overclaimed. The second failure was a 40-character git SHA in a probe read as a "Hex High Entropy
  String"; it is marked with the inline pragma the tool itself prints, in preference to a baseline
  entry that would be invisible at the call site. (2026-09-01 01:07 PM CDT)

- **A harness baseline could hang forever and CI would just sit there.** Five harnesses bound their
  ROW runs at 900s - with a comment saying why, *"a row that hangs anyway must report rather than
  stall the gate"* - and ran the BASELINE pytest above them with no bound at all. The protection had
  been applied to the rows and not to the sibling run thirty lines up. **The motivating measurement
  was corrected before this shipped:** the step that prompted it was not hung, it is genuinely slow -
  `U9 HTTP hardening amputation` ran 17:53:09 to 18:17:28, **24m19s, and passed**, against 27-77
  seconds for every step around it. That is the actual argument for a bound rather than against one:
  where one step legitimately runs for 24 minutes, a real hang is indistinguishable from normal
  slowness for as long as anyone is willing to wait, and an unbounded baseline would simply never
  end. All five baselines are now bounded, and a hang gets its OWN message and its OWN
  exit code (4, against 3 for a red suite), because "never finished" and "finished red" need
  different diagnoses. Proved on all three arms: hang -> 4, red -> 3, green -> 0. (2026-08-29 01:14 PM CDT)

- **Sixteen CI steps had an unreachable diagnostic branch, because GitHub runs every `run:` block
  as `bash -e`.** The steps open with `set -uo pipefail` and then `out=$(checker); rc=$?`, intending
  to print a tailored message for a non-zero result. `set -uo pipefail` does not clear `-e`, and
  under `-e` the ASSIGNMENT is itself the failing command - so the shell dies at that line, `rc=$?`
  never runs, no message is printed, and the step exits with the checker's raw code. Every one of
  those sixteen tailored failure messages was dead code. Proved by extracting the real step out of
  the workflow and running it under `bash -e` against a tree with no standards corpus: before, exit
  2 and total silence; after, the diagnostic prints and the step exits 0. Also in this commit: the
  fourteen `E501`s and one `N806` that `ruff format` created in two checkers and that had been red
  on `main` - `ruff format` cannot split a long string literal, so format-clean and lint-clean are
  different states. (2026-08-29 12:44 PM CDT)

- **`ctypes.CDLL` ran after `fork`, where `dlopen` can deadlock the child.** The orphan fix shipped
  earlier today resolved libc inside the `preexec_fn`; `dlopen` takes loader locks, and a lock held
  by another thread at the moment of the fork is held forever in the child, which has only the
  forking thread. This suite is multi-threaded at spawn time - the AnyIO workers its own shutdown
  tests document - so that was a hang waiting for a schedule. libc is now resolved at import,
  before anything forks. Alongside it: `prctl`'s return is checked rather than discarded, because a
  silently failed install leaves the child unprotected, which is the defect wearing the fix's name;
  and the race check no longer asks `getppid() == 1`, which was wrong in BOTH directions - in a
  container where pytest is itself PID 1 every child sees 1 from birth and would die at spawn, and
  under a subreaper an orphan never reparents to 1 at all. The parent's pid is passed in and
  compared against. Each bail-out has a distinct exit code, and a new arm proves a healthy child
  takes none of them. (2026-08-29 12:31 PM CDT)

- **A CI gate had never once passed on a runner, and could not.** `Standards citations resolve`
  reads a corpus that lives in a private sibling repository. `GITHUB_TOKEN` is scoped to this
  repository and no step checks the other one out, so on a runner the checker finds no corpus and
  exits 2 - deliberately, because a checker reporting all-clear when it cannot find its subject has
  checked nothing. Reproduced by unpacking the tree into a directory with no sibling. The step now
  distinguishes its two states: an absent corpus is reported loudly as a gate that DID NOT RUN, in a
  green run, and a citation that genuinely fails still fails the build. Verified by planting a
  citation past the end of its standard - exit 1, distinct from the absent-corpus exit 2. Making it
  green is not making it pass: nothing about standards citations is checked on a runner until a
  `STANDARDS_TOKEN` secret exists. (2026-08-29 12:16 PM CDT)

- **The last two audit rows that nothing asserted are now asserted, and one was on the write.**
  Six places in `src/` record a failed invocation as `result_status = "error"`; deleting each in
  turn and running the whole suite showed two that no test could see - `search_candidates` and
  `create_candidate`. Both sit in a module measuring 100.00% line and 100.00% branch on the
  critical-path floors, because the cases that walk those arms assert the caller-visible half and
  never read the audit row. The write is the serious one: a failed or ambiguous create was recorded
  as a success, and the audit row is the only surviving evidence afterwards. The write also emits
  **twice** - the pre-write row is correctly `success` because nothing has failed yet - so the
  assertion had to name which row carries the verdict, and the first attempt at it would have
  passed against the amputated code. (2026-08-29 12:13 PM CDT)

- **CI's zero-skips guard read the wrong input and never fired, and CI has been red all day behind
  cancelled runs.** The step's here-string sat after `then` rather than on its `grep`, so the grep
  read standard input instead of the captured pytest output, matched nothing, and the guard stayed
  silent on a run full of skips - the step whose own comment says *"a skip is a green that tested
  nothing"* was itself testing nothing. It came from the SIGPIPE sweep, where pipes were converted
  to here-strings and one landed a token too late. Found because **every CI run on `main` today was
  `cancelled` by the next push** - 54 of them - so the five that did complete, all failures, were
  the only evidence and nothing on the dashboard read as red. A cancelled run is not a failure, and
  that is what let it hide. Reproduced locally by running actionlint at CI's pinned version WITH
  shellcheck installed: without shellcheck on PATH, actionlint silently disables the integration and
  exits 0, which is why the local gate had passed. (2026-08-29 12:07 PM CDT)

- **A harness's two row floors could disagree, and one of them did.** A floor lives in two places:
  `ROW_FLOOR=<n>` inside the harness and `--min-rows <n>` on its gate line in `ci.yml`. They are
  derived at different times by different people, so where a harness carries both they are two
  independent opinions about one number - and `check-critical-coverage-amputation.sh` held 18
  against 15 for as long as both existed, the external floor tolerating the loss of three rows the
  internal one would have caught. The wired floor checker now requires them to agree wherever both
  exist. It reports how many harnesses each of its two claims actually reaches (9 and 8 of 24),
  because a check that does not name its blind spot reads as a whole one, and it refuses to report
  a verdict at all when its ci.yml join comes up short - a wrong join here produces a reassuring
  zero rather than an error. (2026-08-29 11:48 AM CDT)

- **Three CI floors were behind the tree they gate.** The suite floor said 863 against 867 passing
  tests, the harness-anchor floor 453 against 456 resolving anchors, and the critical-path
  amputation's `--min-rows` 15 against a harness that runs 18 rows. A floor below its live count is
  the silent direction - it fails nothing while tolerating exactly the loss it exists to catch, and
  the amputation one had drifted three rows. All three were re-derived from a run on the merged tree
  rather than by adding each merged branch's delta to the previous number, because a branch-local
  floor plus a delta is how the last slack floor was produced. (2026-08-29 11:42 AM CDT)

- **A row floor could sit below its harness's live row count and say nothing.**
  `check-u7-resilience-controls.sh` carried 31 rows against `ROW_FLOOR=26`, so five of its rows
  could have been deleted with CI green. Neither branch was wrong: the 26 was honestly derived on
  one branch, the five extra rows arrived on another, and neither commit is an ancestor of the
  other - **the merge produced the slack**, and nothing in the repository compared a floor to a live
  count. A floor that is too high fails loudly on the next run; a floor that is too low is silent
  forever, which is why only this direction needed a checker. The floor is now raised and a wired
  step re-derives every checked floor from the harness itself, reading the row-invocation pattern
  out of the control table rather than keeping a second copy of it. It states in its own docstring
  that it covers 9 of the 24 floored harnesses, because a partial check that does not say so reads
  as a whole one. (2026-08-29 11:37 AM CDT)

- **A test's server outlived the harness that spawned it, twice in one day.** `spawn_marker_server`
  starts a real server in a real process; when a run was killed rather than allowed to finish, that
  server was still alive 2h02m later, holding its port and executing out of a worktree that had
  already been deleted. The identical orphan appeared again the same day from the same test. No
  `try: ... finally: proc.kill()` can close this, because `SIGKILL` runs no Python - so the child now
  asks the kernel for `PR_SET_PDEATHSIG`, and re-checks `getppid()` to cover the fork-window race
  where the signal would have been delivered to nobody. Two callers that had no cleanup path at all
  gained one as well: an ordinary assertion failure in either left a live server behind for the rest
  of the run. Proved by amputating the `prctl` call, which turns the new arm red while its positive
  control - a parent left deliberately alive, whose child must NOT vanish - stays green.
  (2026-08-29 11:26 AM CDT)

- **`JOBVITE_PAGINATION_START_BASE` reached no code at all.** The variable shipped, was documented
  as an operator override, and was read by nothing: the tool built its client without passing it
  through, so setting it changed no request on the wire. It is the same omission as the result-cap
  one below, in the same argument list, and the fix for that one did not check its siblings. The
  setting now reaches the client for every route the tool asks it for, and a case builds the real
  client and asks it what base it would scan from - with a silence arm, because a factory that
  applies a base unconditionally is the failure that loses record zero.
  (2026-08-29 05:41 AM CDT)

- **The two halves of the result cap could hold different numbers.** `JOBVITE_MAX_RESULTS` is applied
  in two places by design - once in the tool, which owns the `showing N of total` string, and once at
  the transport, which bounds what leaves the client. The tool built its client without passing the
  setting through, so raising the limit moved one half and left the other at the client's own
  default. No test could see it, because each half was correct on its own. (2026-08-29 05:12 AM CDT)

- **The audit event's mandated fields now reach the log stream.** `audit.py` writes through `loguru`
  and nothing configured it, so every record went to `loguru`'s default handler, whose format
  carries no structured context: `tool_name`, `request_id`, `transport`, `result_status`,
  `latency_ms` and the redacted arguments were dropped, and the whole event arrived as the word
  `tool_invocation`. The entry point now installs one serialising sink on stderr. (2026-08-29 04:31 AM CDT)
- **The audit-write-failure policy can now fire.** `loguru` handlers swallow a sink failure by
  default and return normally, so the branch that fails a call before its side effect - the one that
  stops a second live candidate being emailed when the audit record cannot be written - was
  unreachable in production. The sink no longer swallows. (2026-08-29 04:31 AM CDT)

- Threat-model bookkeeping in the design, three defects of one family. A prose count stated the
  size of a table three times and was wrong all three times, most recently reading "Two" over an
  emptied table in the section a reader consults to check the freeze condition; it is replaced by a
  removal ledger, and no sentence in that section states a total for it. A rule forbidding totals
  was itself false, since the section states totals elsewhere. And an exclusivity claim about the
  one residual row rested on a single unrepeated adjective. (2026-08-28 02:09 PM CDT)
- The read-only-key requirement was said to be stated "in the README's deployment section", present
  tense, in a repository that has no README and whose design deliberately withholds one until an
  implementation exists. The requirement is stated today in the credential checklist; the README
  arm is gated on the file's presence rather than skipped, because a skip is a green that tested
  nothing. (2026-08-28 02:09 PM CDT)

- Two upstream FastMCP defects found by our runtime spikes and reported to the project:
  [#4926](https://github.com/PrefectHQ/fastmcp/issues/4926), a regression where
  `ResponseLimitingMiddleware` breaks any tool with an output schema, and
  [#4927](https://github.com/PrefectHQ/fastmcp/issues/4927), lifespan teardown not running under
  SIGTERM and therefore leaking resources on every container shutdown. Both are worked around in
  our design. (2026-08-27 02:38 PM CDT)
