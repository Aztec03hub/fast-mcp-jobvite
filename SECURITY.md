# Security policy

## Reporting a vulnerability

Please report security issues privately. Do **not** open a public issue.

- Use [GitHub private vulnerability reporting](https://github.com/evolvconsulting/fast-mcp-jobvite/security/advisories/new)
  on this repository, or
- email `security@evolvconsulting.com`.

Please include what you were doing, what happened, and enough detail to reproduce it. If a
proof of concept touches a live Jobvite tenant, describe it rather than attaching captured data —
see the note on candidate data below.

We aim to acknowledge within three working days.

## Scope

In scope: this repository's code, its dependency set, its GitHub Actions workflows, and its
published packages.

Out of scope: vulnerabilities in Jobvite's own API or hosted service. Report those to Jobvite or
Employ Inc. directly. We are an independent client of that API and cannot fix it.

## What this software handles, and why that matters

This server exposes candidate records from an applicant tracking system to a language model.
That means it routinely handles **personal data about job applicants** — names, contact details,
work history, résumé text — belonging to people who are not the operator and have no relationship
with us.

Two consequences shape what counts as a serious bug here:

**Candidate free text is untrusted input.** Résumés, cover letters and notes are authored by
people outside the operator's organisation, and this server feeds them directly to a model. A
path by which that content escapes its delimiters and reaches a model as instructions is a
security bug, not a formatting bug. Report it as one.

**Credentials can leak through logs.** Jobvite's v2 API takes credentials in headers, but its v1
job feed structurally requires the secret in the query string. Any path by which a secret reaches
a log line, an exception message, a tool result, or an error returned to a client is a
vulnerability. This includes indirect paths: framework middleware that logs request payloads,
tracebacks written to the server log, and third-party libraries that log URLs.

## Please do not include real data in a report

Do not attach real candidate records, real Jobvite tenant identifiers, real hostnames, or working
credentials. Describe the shape of the problem and we will reproduce it. If you believe you have
found an exposed credential belonging to someone else, tell us where without reproducing its
value.

## Known limitations, disclosed deliberately

These are documented rather than hidden, and are not what we need reported:

- **No success-path response from Jobvite has ever been observed by this project.** There is no
  sandbox and the maintainers hold no credential. Success-path fixtures are synthetic. See
  `docs/CREDENTIAL-CHECKLIST.md`.
- **stdio transport is unauthenticated by design.** Anything able to spawn the process can call
  its tools; the trust boundary is the operating system's, not this server's. Use the HTTP
  transport with a token if you need an authentication boundary.
- **Rate limiting is in-process and configuration-driven.** Jobvite publishes no limits and
  returns no rate-limit headers, so there is nothing to adapt to at runtime.
