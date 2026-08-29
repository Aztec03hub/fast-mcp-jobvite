### Added
- Per-invocation audit event for every tool call, carrying the tool name, redacted arguments,
  result status, latency and `request_id`, plus the transport and - on HTTP - the resolved client
  id. On stdio the event records that caller attribution is unavailable rather than implying an
  identity that does not exist. W3C trace context is recorded when the caller supplies it and
  omitted when it does not; it is never synthesised. (task #27)
- Secret redaction at a single enforcement point: the `jobFeed` URL's `api`, `sc` and `companyId`
  query parameters are redacted before any log line, including where the URL appears inside an
  exception message, and tool arguments are redacted by a fail-closed allow-list so a field added
  later is redacted until it is allowed deliberately. (task #27)
- ADR-0021, recording that the audit event's approval "mechanism" is required by two `DESIGN.md`
  rows and defined by neither. (task #27)
