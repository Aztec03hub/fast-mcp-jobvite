# fast-mcp-jobvite

An MCP server exposing the Jobvite applicant tracking system as tools, with every result bounded and
allow-listed.

[![CI](https://github.com/evolvconsulting/fast-mcp-jobvite/actions/workflows/ci.yml/badge.svg)](https://github.com/evolvconsulting/fast-mcp-jobvite/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](./pyproject.toml)

> **The server exposes its first tool: `search_jobs`.** It boots, authenticates, audits, redacts,
> shuts down cleanly, and answers a real MCP `tools/call`. `fastmcp inspect` reports `Tools: 1`.
> The remaining tools - `get_job_feed`, `search_candidates`, `get_candidate` and the single gated
> write - are later units, and this paragraph changes again when each lands.

> **AND IT HAS NEVER TALKED TO JOBVITE.** Nobody who built this held a Jobvite credential.
> Jobvite publishes no API documentation and operates no sandbox, so **no success response
> from Jobvite has ever been observed by this project.** Error-path fixtures are byte-exact
> recordings of real transport; every success-path fixture is synthetic, and every success
> response shape is a hypothesis derived from third-party clients and Jobvite's 2014-era v1
> docs.
>
> So read the green badge precisely: **a passing suite proves this client is internally
> consistent. It does not prove this client speaks Jobvite.** The specific things still
> unobserved - the response envelope keys, whether `start` is 0- or 1-based (three
> third-party clients disagree, and a wrong answer silently skips or duplicates a record on
> every page), whether the 500-item page cap is real or truncates silently, and the
> record-level not-found shape - are enumerated with their test rows in
> [`docs/CREDENTIAL-CHECKLIST.md`](docs/CREDENTIAL-CHECKLIST.md).
>
> `tests/credentialed/` holds the arms that settle it. They are deselected by marker rather
> than skipped, and CI `--collect-only`s them so they cannot rot before a key exists.

## Quickstart

No Jobvite account is required. The placeholder credentials below are never sent anywhere; the
server checks only that the variables for its enabled tools are *set*, and this command never opens
a connection.

```bash
git clone https://github.com/evolvconsulting/fast-mcp-jobvite && cd fast-mcp-jobvite
uv sync --frozen
env JOBVITE_API_KEY=placeholder JOBVITE_API_SECRET=placeholder JOBVITE_FEED_KEY=placeholder \
    JOBVITE_FEED_SECRET=placeholder JOBVITE_COMPANY_ID=placeholder \
    uv run --frozen fastmcp inspect "src/fast_mcp_jobvite/server.py:create_server"
```

That prints the server's name, version, instructions and component counts, and exits 0.

**Why credentials appear in a Quickstart at all.** The configuration layer refuses to start when an
enabled tool's variables are unset - a deliberate fail-closed choice, so a misconfigured deployment
cannot come up half-working and silently serve errors. Without *some* value the server will not
boot, so the honest Quickstart supplies placeholders and says why.

## Installation

**Requirements**

| | |
|---|---|
| Python | 3.12 or newer (`requires-python = ">=3.12"`) |
| Package manager | [uv](https://docs.astral.sh/uv/) - the lockfile is authoritative |
| Platform | Any POSIX host. Linux is what CI runs. |

**From a clone**, which is the only supported method today:

```bash
uv sync --frozen
```

`--frozen` is not optional. It installs exactly the pinned versions in `uv.lock` and fails rather
than re-resolving. The project pins a FastMCP beta deliberately, and an unpinned resolve silently
changes the stack underneath the test suite.

**Not yet on PyPI.** `pyproject.toml` declares the `fast-mcp-jobvite` distribution and a
`fast-mcp-jobvite` console script, and `server.json` declares the PyPI package for the MCP registry,
but nothing has been published. Install from a clone.

## Configuration

Every variable is read through `pydantic-settings` with the `JOBVITE_` prefix, and this table lists
every one the server reads - the authority is `src/fast_mcp_jobvite/config.py`, not this table.
**Secrets are named here and never valued.** `.env` is gitignored; `.env.example` carries empty
values for the secret-class entries.

| Name | Required | Default | Description |
|---|---|---|---|
| `JOBVITE_API_KEY` | Per tool | *(none)* | Jobvite v2 API key, sent as the `x-jvi-api` header. Required by the candidate and job tools. |
| `JOBVITE_API_SECRET` | Per tool | *(none)* | Jobvite v2 API secret, sent as the `x-jvi-sc` header. Required alongside `JOBVITE_API_KEY`. |
| `JOBVITE_FEED_KEY` | Per tool | *(none)* | Job-feed key. The feed is a separate credential pair from the v2 API. |
| `JOBVITE_FEED_SECRET` | Per tool | *(none)* | Job-feed secret. |
| `JOBVITE_COMPANY_ID` | Per tool | *(none)* | Company identifier used by the job-feed route. |
| `JOBVITE_TOOLS` | No | *(all)* | Comma-separated allow-list of tool names to enable. Unset enables every tool, and each enabled tool's credentials must then be set. |
| `JOBVITE_ENABLE_WRITES` | No | `false` | Gates the single write tool. Off unless explicitly enabled. |
| `JOBVITE_MCP_TRANSPORT` | No | `stdio` | `stdio` or `http`. |
| `JOBVITE_MCP_HOST` | No | `127.0.0.1` | Bind address for the `http` transport. Loopback by default. |
| `JOBVITE_MCP_PORT` | No | `8000` | Bind port for the `http` transport, 1-65535. |
| `JOBVITE_HTTP_TOKENS` | No | *(none)* | Bearer tokens accepted on the `http` transport. |
| `JOBVITE_TLS_TERMINATED_BY_PROXY` | No | `false` | Asserts that a proxy terminates TLS. The server refuses to bind off-loopback in plaintext without it. |
| `JOBVITE_MAX_RESULTS` | No | `50` | Upper bound on results returned by any tool, minimum 1. |
| `JOBVITE_OUTBOUND_RATE_LIMIT` | No | `6` | `JOBVITE_OUTBOUND_RATE_LIMIT` IS NOT YET IMPLEMENTED (ADR-0025): it is declared and validated, and **no code reads it**, so setting it changes nothing today. Intended as outbound requests per **minute** to Jobvite, minimum 1. |
| `JOBVITE_OUTBOUND_BUDGET_SECONDS` | No | `60` | Total wall-clock budget for all outbound attempts in one tool invocation. Greater than 0. |
| `JOBVITE_PAGINATION_START_BASE` | No | *(unset)* | Overrides the detected pagination base. Leave unset unless a measurement says otherwise. |

**"Per tool" means what it says.** A credential is required only when a tool that needs it is
enabled, and the server names the missing variables and the tool that wanted them at startup rather
than failing later on the first call.

## Usage examples

**Inspect the server** - runnable now, and its output is the honest current state:

```bash
env JOBVITE_API_KEY=placeholder JOBVITE_API_SECRET=placeholder JOBVITE_FEED_KEY=placeholder \
    JOBVITE_FEED_SECRET=placeholder JOBVITE_COMPANY_ID=placeholder \
    uv run --frozen fastmcp inspect "src/fast_mcp_jobvite/server.py:create_server"
```

```
Server
  Name:         fast-mcp-jobvite
  Version:      0.1.0
Components
  Tools:        1
  Prompts:      0
  Resources:    0
```

**That count is the honest one, and it was `Tools: 0` until `search_jobs` landed.** It is quoted
from a real run rather than written by hand, which is why it was correct when it said zero and is
correct now that it says one.

**Run the server over stdio**, which is how an MCP client launches it:

```bash
env JOBVITE_API_KEY=... JOBVITE_API_SECRET=... uv run --frozen fast-mcp-jobvite
```

It speaks MCP on stdin/stdout, so it will appear to hang in a terminal - that is correct. Point a
client at it instead.

**Run it over HTTP**, refusing an unsafe bind:

```bash
env JOBVITE_MCP_TRANSPORT=http JOBVITE_MCP_HOST=0.0.0.0 uv run --frozen fast-mcp-jobvite
```

That command **exits 78 on purpose** - `EX_CONFIG`, measured, not inferred. Binding off-loopback in
plaintext is refused unless `JOBVITE_TLS_TERMINATED_BY_PROXY=true` asserts a TLS-terminating proxy in
front. It is documented because the refusal is a feature, and because a distinct exit code is what
lets a supervisor tell a misconfiguration from a crash.

## API / CLI reference link

**Generate the reference rather than reading a copy of it.** The MCP tool surface is declared by the
server itself, so the live reference is one command:

```bash
env JOBVITE_API_KEY=placeholder JOBVITE_API_SECRET=placeholder JOBVITE_FEED_KEY=placeholder \
    JOBVITE_FEED_SECRET=placeholder JOBVITE_COMPANY_ID=placeholder \
    uv run --frozen fastmcp inspect "src/fast_mcp_jobvite/server.py:create_server" --format mcp
```

- [`server.json`](./server.json) - the MCP registry declaration: package, transport, and every
  environment variable with its secret and required flags.
- [`docs/DESIGN.md`](./docs/DESIGN.md) - the interface contract, including the error model. **It is
  frozen**; only a numbered ADR in [`docs/adr/`](./docs/adr/) may change it.

No reference material is inlined here, because a hand-copied tool table drifts from the server that
generates it.

## Development setup

```bash
uv sync --frozen                        # exact pinned versions, no re-resolve
uv run --frozen ruff check .            # lint
uv run --frozen ruff format --check .   # format
uv run --frozen mypy                    # types - mypy is the type gate, not pyright
```

**`pyright` is not in the lock and is not the gate.** Running it via `uv run --with pyright`
resolves a tool outside the lockfile, which is the defect [ADR-0015](./docs/adr/) records.

The full gate list, including every mutation and amputation harness, is in
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Testing

```bash
uv run --frozen pytest
```

Focused:

```bash
uv run --frozen pytest tests/test_config.py -q
uv run --frozen pytest "tests/test_config.py::test_loopback_addresses_are_recognised" -q
uv run --frozen pytest tests/test_config.py -k loopback -q
```

Those are real node ids, not illustrative ones - each was run before being written here.

**Zero skips is enforced, and the suite size is floored.** A skip is a green that tested nothing, so
the credentialed and network arms are excluded by marker selection rather than by `skipif`. The
count is checked against a ratchet by [`scripts/check-suite-floor.sh`](./scripts/check-suite-floor.sh),
because a guard that only asks "did anything pass?" is satisfied by one test.

Behaviour is verified by **amputation** as well as mutation - deleting a behaviour outright, and
requiring a test to go red. Survivors are the output, not a crash. The harnesses are in
[`scripts/`](./scripts/) and every one is wired into CI.

## Deployment

**Nothing is deployed and nothing is published yet.** There is no runbook to point at, and inventing
one would be worse than saying so.

### A token without a scope makes the tool VANISH, it does not produce a permission error

On the `http` transport, `JOBVITE_HTTP_TOKENS` maps each bearer token to the scopes it holds, and a
tool the caller's token does not hold is **removed from `tools/list` entirely**. A direct call then
returns **"Unknown tool"** - indistinguishable from a tool that was never registered.

That is correct and it is confusing, so it is written here rather than left to be discovered:

> **If an integrator reports a tool missing, check the scopes on their token before you check
> `JOBVITE_TOOLS`.** Both produce a server that does not list the tool, and only one of them is a
> configuration mistake.

### A request body over 1 MiB is refused as a 422, not a 413

On the `http` transport a request body larger than **1 MiB** is refused before the application is
entered, with `/problems/validation-error` at **422**. The reason it is size is in `detail`, not in
the status line.

**422 rather than the more precise 413 is deliberate.** The error registry has no 413 row, and a new
`type` URI is a contract this project owes forever - so a row is reused and the distinction lives in
`detail`. If you are matching on status alone, match `detail` too.

**It applies to every route and only to HTTP.** The bound sits outside the router, so it covers
anything the server mounts. There is no body on `stdio`; the separate argument-payload bound applies
there, and the two are not duplicates.

### `create_candidate` writes to a real ATS, and what the approval does NOT prove

`create_candidate` is registered only when `JOBVITE_ENABLE_WRITES=true` **and** it is named in
`JOBVITE_TOOLS`. Before it writes, the server asks the host to approve, naming the candidate, the
target job, and whether `send_email` is true.

**`send_email` defaults to `false`. Setting it `true` mails a real person.** An integrator who does
not know that does not know what they are approving.

Four limits, stated because none of them is fixable here:

- **Nothing proves a human approved anything.** The server requires an approval *response from the
  host* and refuses to write without one. **A host may auto-respond with no person present** - MCP
  places human-in-the-loop on the host, not on us. Do not read an approved write as human consent.
- **An abandoned approval hangs the call.** The handler runs in the client's process and there is no
  server-side bound on it. The write stays safe and no row is created; the call simply does not
  return.
- **An authorised write can be made twice.** This server never retries it. A duplicate surfaces as
  `/problems/conflict` naming the duplicate - **that is detection, not prevention**, and the `409`
  shape is inferred rather than observed, so even the detection is a hypothesis until a live
  credential exists. An idempotency key cannot be built: nothing establishes that Jobvite accepts
  one.
- **A host that cannot elicit cannot use this tool.** There is no fallback, so on such a host
  `create_candidate` refuses. Correct, and surprising if you had not been told.

### Embedding the server rather than running it

The HTTP client library logs each request URL through the standard library, and on the job-feed
route that URL structurally carries the API key, secret and company id.
`fast_mcp_jobvite.__main__` redacts it at import, so **the shipped server has never been exposed** -
but an embedder who imports `fast_mcp_jobvite.server`, or constructs `JobviteClient` directly, never
runs that.

So **`JobviteClient` installs the redaction itself**, on `httpx2`'s logger, per
[ADR-0026](./docs/adr/0026-log-redaction-is-a-property-of-the-entry-point-not-the-client.md).
You need call nothing. Two things worth knowing before you embed it:

- **It touches your logging configuration from a constructor**, which you are entitled to object to.
  Pass `JobviteClient(..., install_log_redaction=False)` and it will not - a constructor argument,
  never a setting. The default installs because a credential leak is a worse default than a
  surprising side effect; opting out makes the exposure a choice you made.
- **The install is idempotent.** A client is built once per invocation, so a filter appended per
  construction would stack one per tool call forever. Build a thousand and there is still one.

Not a theoretical guarantee: `docs/reviews/probe-u12-f2-embedder-leak.py` measures it on a handler
that is not ours, with a control arm that opts out and must still read the credentials in the clear,
and the test suite runs it.

What exists:

- [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) - the pipeline: gates, the test suite,
  the harnesses, and a weekly scheduled security sweep so an advisory against the pinned beta stack
  cannot wait for the next merge.
- [`server.json`](./server.json) - the MCP registry entry a published release would be consumed
  through.
- [`CHANGELOG.md`](./CHANGELOG.md) - assembled from fragments in
  [`changelog.d/`](./changelog.d/).

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full gate list and the review rules.

Two that catch people out: **`docs/DESIGN.md` is frozen**, so a change to it needs a numbered ADR in
[`docs/adr/`](./docs/adr/) and an edit without one is a review finding regardless of whether the
edit is right; and **every gate is judged by its exit code**, never by a truncated view - `lint |
tail -1` looks identical whether the run was clean or red.

Security issues: [`SECURITY.md`](./SECURITY.md). Do not open a public issue for a vulnerability.

## License

[Apache-2.0](./LICENSE). SPDX identifier: `Apache-2.0`. Copyright notices are in
[`NOTICE`](./NOTICE).

## Maintainers

**evolv Consulting.** Maintained by Phil LaFayette (@Aztec03hub).

Review and release run through pull requests against `main`; see
[`CONTRIBUTING.md`](./CONTRIBUTING.md).
