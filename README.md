# fast-mcp-jobvite

An MCP server exposing the Jobvite applicant tracking system as tools, with every result bounded and
allow-listed.

[![CI](https://github.com/evolvconsulting/fast-mcp-jobvite/actions/workflows/ci.yml/badge.svg)](https://github.com/evolvconsulting/fast-mcp-jobvite/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](./pyproject.toml)

> **The server boots, authenticates, audits, redacts and shuts down cleanly. It exposes NO TOOL
> yet.** `fastmcp inspect` reports `Tools: 0`, and the Usage section below shows exactly that rather
> than an example that does not run. `search_jobs` is the next unit of work. This paragraph is a
> statement of current behaviour, not a placeholder - when the first tool lands, it changes.

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
| `JOBVITE_OUTBOUND_RATE_LIMIT` | No | `6` | Outbound requests per second to Jobvite, minimum 1. |
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
  Tools:        0
  Prompts:      0
  Resources:    0
```

**`Tools: 0` is not a documentation gap.** No tool is implemented yet. When one is, this block
changes and so does the count.

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
