### Security
- A failed call to Jobvite no longer puts the HTTP library's own exception text into the error
  returned to the caller. That text carries whatever the library chose to write into it - the
  request URL, a TLS source file and line number, a local socket path - and it reached the caller
  unchanged. Callers now get one of three stable reasons instead, which still distinguish an
  upstream failure from a circuit breaker this server has opened; the full text goes to the log,
  redacted. (task #14)
- The v2 credential headers are redacted before that failure is logged. The header redactor
  existed and had no caller until this line needed it. (task #14)
- An exception's text and traceback are now redacted on their way to the log stream. Redaction ran
  over a record's message, and the serialising sink writes more than the message: an exception
  logged by any library in the process reached stderr with the job-feed URL - and therefore the
  `api`, `sc` and `companyId` credentials - in the clear, measured twice in one record. (task #14,
  task #15)
