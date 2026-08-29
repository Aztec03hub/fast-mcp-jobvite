# Code review checklist

**Obligation:** `devops/development-workflow.md:248` - *"Reviewers must verify all items before
approving:"* - tracked as **B101**. That standard is `priority: required`.

**This is the REVIEWER's checklist. It is not the author's.** The author's self-check is
`.github/pull_request_template.md`, copied from `development-workflow.md:201-241` and tracked
separately as B100. Closing one does not close the other, and the distinction is the whole point:
a checklist the author ticks about their own work is not a review.

**Why this lives in its own file rather than in the PR template.** Putting fifty reviewer rows in
the template puts them in front of the author, who is the one person whose ticking them proves
nothing. The template links here instead.

---

## How to use this

Work the sections in order. **A row you cannot verify is not a row you tick** - say so in the
review instead. `docs/reviews/` holds the reports from previous rounds; the file naming convention
is `REVIEW-<subject>-R<n>.md`.

**Every finding ships with a suggested fix, at every severity including nits.** That is a standing
project rule, not a courtesy: a finding without a proposed remedy costs the author the whole
diagnosis a second time.

---

## Functionality

- [ ] Code accomplishes the stated task requirements
- [ ] Edge cases are properly handled
- [ ] Error handling is appropriate and user-friendly
- [ ] No obvious bugs or logic errors

## Architecture

- [ ] Proper separation of concerns
- [ ] Changes respect `docs/DESIGN.md`, which is **FROZEN** - a change to it requires a numbered ADR
      in `docs/adr/`, and an edit without one is a finding regardless of whether the edit is right
- [ ] A deviation from a `priority: required` standard clause is recorded as an ADR with a `Type:`
      field, not left as an undocumented difference

## Code quality

- [ ] Follows project coding standards (`backend/python.md`)
- [ ] No code duplication (DRY principle)
- [ ] Functions/methods are focused (Single Responsibility)
- [ ] Naming is clear, consistent, and descriptive
- [ ] No hardcoded values (use config/env vars)
- [ ] No debug code or stray `print` statements

## Type safety

- [ ] Type hints on all functions
- [ ] Pydantic models for request/response shapes
- [ ] **`mypy` is clean** on the delta, and new files are clean outright

> **This row named `pyright` until round 2 caught it, and the way it was caught matters.** The
> reviewer discharged it with `uv run --frozen --with pyright ...` - which resolves the tool
> **outside the lock**, exactly the defect ADR-0015 records for `pip-licenses` and `ci.yml` forbids
> for `pip-audit`. A checklist row naming a tool the project cannot run under `--frozen` does not
> just fail to help: it *instructs* a careful reviewer into the unfrozen-tool defect, which is what
> happened.
>
> `mypy` is what `pyproject.toml` declares, what CI gates on, and what `backend/python.md:370`
> names. Adding `pyright` to the lock was the alternative and was rejected: it is a second type
> checker for a typing convenience, and U4 already declined `types-defusedxml` on the same ground.

## Security

- [ ] No secrets or credentials in code
- [ ] Authentication checked before privileged operations
- [ ] Authorization verified before operations
- [ ] Input validation present (Pydantic)
- [ ] Audit logging for sensitive operations
- [ ] Secret-class values in `.env.example` are **empty**, and `.env` is gitignored
- [ ] No vendor document, PDF, or unlicensed specification is added to the tree - the committed
      file-type gate refuses these, and a change that works around the gate is a finding

## Testing

- [ ] Unit tests cover new functionality
- [ ] Tests are meaningful (not just for coverage)
- [ ] Integration tests for behaviour changes
- [ ] Tests are deterministic (no flakiness)
- [ ] Edge cases have test coverage

## Performance

- [ ] Large result sets paginated
- [ ] Appropriate caching implemented, where caching is warranted at all

## Documentation

- [ ] Public functions have docstrings
- [ ] Complex logic has explanatory comments
- [ ] README updated if needed
- [ ] `CHANGELOG` fragment present for a user-facing change

---

## Project additions

**These are not from `development-workflow.md:248`.** They are here because each names a failure
this project has actually shipped, and a checklist that omits them would pass the reviews that
missed them.

- [ ] **The gate was judged by exit code**, not by a truncated view. `lint | tail -1` looks
      identical red or clean, and `grep -c "^FAILED"` on pytest misses ERROR entirely - a run with
      440 errors once reported "0 failures".
- [ ] **Zero skips**, and the passed-count is quoted rather than the word "green". A skip is a green
      that tested nothing.
- [ ] **Citations were verified by subject**, not by checking that a `file:line` is non-blank. Nine
      wrong-subject citations have been found on this project; four were inside the ADR documenting
      that defect class.
- [ ] **A new test was checked for vacuity by amputation**, not only by mutation. Deleting the
      behaviour outright has exposed an assertion that survived mutation in every unit built so far.
- [ ] **A claimed absence states where the search looked.** "It exists nowhere" after two greps is
      not an absence, and a grep over a binary file prints nothing without erroring.

---

## Sections of the standard that do not apply here, and why

**Nothing below is dropped silently.** `development-workflow.md:248` is a checklist written for a
Next.js-plus-FastAPI-plus-PostgreSQL product. This repository is a Python MCP server with no
frontend, no database, and no browser session, so the rows below have no subject here. Each is
recorded rather than deleted, because a reviewer who finds a row missing cannot tell whether it was
considered or overlooked.

| Row from the standard | Why it has no subject here |
|---|---|
| *Follows the SSR with Server Actions pattern* | No frontend. `git ls-files '*.ts' '*.tsx'` returns 0 and there is no `package.json`. |
| *Data flow: Client -> Server Action -> FastAPI -> PostgreSQL* | Same. The flow here is MCP client -> tool -> Jobvite REST. |
| *No direct API calls from client components* / *Server components used where possible* | No frontend. |
| *No `any` types in TypeScript*, *Explicit return types*, *Discriminated unions* | No TypeScript. The Python equivalents are in **Type safety** above. |
| *Zod schemas for frontend validation* | No frontend. Pydantic covers the equivalent obligation and is listed above. |
| *XSS prevention in frontend* | No frontend, and this server renders no HTML. |
| *CSRF protection for mutations* | **Verified, not assumed.** HTTP auth is `StaticTokenVerifier` over a Bearer token (`DESIGN.md:828`). CSRF requires an *ambient* credential the browser attaches automatically; a Bearer token is not one, and there are no cookies. `grep -in csrf docs/DESIGN.md` returns nothing, so the design never states this - **the reasoning is recorded here because it was not recorded there.** |
| *SQL injection prevented (SQLAlchemy ORM)* | No database. `pyproject.toml` declares no SQLAlchemy, psycopg, asyncpg or alembic dependency. |
| *No N+1 queries (use eager loading)* | No database. Upstream request volume is governed by the pagination and rate-limit rows instead. |
| *Images optimized (next/image)* / *No unnecessary re-renders* | No frontend. |
| *Component tests for UI changes* | No UI. |
| *API documentation updated (OpenAPI)* | This server exposes MCP tools, not an OpenAPI surface. The equivalent declaration is `server.json`, covered by the README row. |

**One row was translated rather than dropped**: *"Authentication checked in server actions"* becomes
*"Authentication checked before privileged operations"*, because the obligation is real here even
though the mechanism named is not.
