### Security
- `JobviteClient` now installs the log redaction on `httpx2`'s standard-library logger from its
  constructor, so an embedder who never runs `fast_mcp_jobvite.__main__.configure_logging()` no
  longer receives the job-feed URL's `api`, `sc` and `companyId` in the clear. The shipped server
  was never exposed; this closes an embedder's exposure. ADR-0026. (task #83)

### Added
- `JobviteClient(install_log_redaction=False)` opts out of that side effect, for an embedder who
  wants their logging configuration untouched. A constructor argument, never a setting. (task #83)
