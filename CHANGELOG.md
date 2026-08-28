# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Timestamps are America/Chicago.

## [Unreleased]

No release yet. The project is in design; no runtime code exists. Entries below record the
decisions and research that the implementation will be built against.

### Added

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
