### Fixed
- The audit event's mandated fields now reach the log stream. `audit.py` writes through `loguru`
  and nothing configured it, so every record went to `loguru`'s default handler, whose format
  carries no structured context: `tool_name`, `request_id`, `transport`, `result_status`,
  `latency_ms` and the redacted arguments were dropped and the whole event arrived as the word
  `tool_invocation`. The entry point now installs one serialising sink on stderr. (task #12)
- The audit-write-failure policy can now fire. `loguru` handlers swallow a sink failure by
  default and return normally, so the branch that fails a call before its side effect - the one
  that stops a second live candidate being emailed when the audit record cannot be written -
  was unreachable in production. The sink no longer swallows. (task #12)

### Security
- The Jobvite job-feed URL no longer reaches the log stream in the clear. The HTTP client library
  logs each request URL through the standard library's logging, which the server configured at
  INFO on stderr, and that URL structurally carries the `api`, `sc` and `companyId` credentials.
  Every record now passes through the project's single redaction point on its way to the sink,
  whichever library produced it. (task #12)
