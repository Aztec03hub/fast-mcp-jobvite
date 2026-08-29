### Added
- Jobvite client with a single request entry point. Every call is checked against the
  error-detection rule before its body is returned: a response counts as successful only if the
  body carries no `status.code` of 400 or above **and** the HTTP status is below 400. Both, every
  call. This matters because `api.jobvite.com` answers a rejected credential with HTTP 200 and a
  body saying 401 - a client trusting the HTTP status reports zero results for a credential that
  was actually refused.
- Error bodies are decoded without assuming JSON and without relying on `Content-Type`, which the
  job-feed route does not send: the JSON status envelope, plain text and Tomcat HTML error pages
  are all recognised as failures rather than degrading to an empty result. XML is parsed with a
  hardened parser and always treated as an error.
- Credentials travel as request headers, and no URL containing a secret is ever built. The one
  route that structurally requires credentials in its query string is treated as sensitive: it is
  never written to a log line or an error message in full.
