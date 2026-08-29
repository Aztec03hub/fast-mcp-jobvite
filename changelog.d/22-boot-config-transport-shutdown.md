### Added
- The server boots: configuration, transport selection, and a graceful shutdown that runs lifespan
  teardown on SIGTERM. `fast-mcp-jobvite` is now a console script. (task #22)
- Configuration is validated at boot and names every variable it refuses on, scoped to the tools
  actually enabled, so a deployment running only candidate search is not asked for a job-feed
  company id. (task #22)
- An unrecognised name in `JOBVITE_TOOLS` is a startup failure rather than a silently disabled tool.
  (task #22)
- Binding a non-loopback address without `JOBVITE_TLS_TERMINATED_BY_PROXY=true` refuses to start:
  this server terminates no TLS of its own, and an off-loopback bind would carry a bearer token and
  candidate PII in the clear. (task #22)
- `JOBVITE_MCP_TRANSPORT=http` without `JOBVITE_HTTP_TOKENS` refuses to start rather than serving an
  open server. (task #22)
- `server.json` declares all fifteen environment variables for registry consumers. (task #22)
- ADR-0018 (Proposed): the forced exit in the shutdown path reports a crash as a clean stop.
  (task #22)
