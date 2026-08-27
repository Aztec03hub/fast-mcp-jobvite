# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Timestamps are America/Chicago.

## [Unreleased]

No release yet. The project is in design; no runtime code exists. Entries below record the
decisions and research that the implementation will be built against.

### Added

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
- `docs/reviews/check-coupling.py` and its control harness: a machine check that every threat-model
  row accounts for itself against the test list, with nineteen executable controls proving each
  check can fail. Wired into CI. (2026-08-27 05:30 PM CDT)


- Design document scoping v1.0 to five Jobvite operations, with the module layout, error
  contract, resilience model and testing strategy. Under adversarial review; frozen at
  0C/0H/0M, after which only a numbered ADR may change it. (2026-08-27 02:23 PM CDT)
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
- Repository scaffolding: gitignore, the changelog-fragment workflow that keeps parallel agent
  work off a single shared file, and the docs layout. (2026-08-27 01:37 PM CDT)

### Changed

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

- Two upstream FastMCP defects found by our runtime spikes and reported to the project:
  [#4926](https://github.com/PrefectHQ/fastmcp/issues/4926), a regression where
  `ResponseLimitingMiddleware` breaks any tool with an output schema, and
  [#4927](https://github.com/PrefectHQ/fastmcp/issues/4927), lifespan teardown not running under
  SIGTERM and therefore leaking resources on every container shutdown. Both are worked around in
  our design. (2026-08-27 02:38 PM CDT)
