# CODE-REVIEW-R2 - U1, U3 and U4, which nobody has reviewed

## Tools you must load before you start

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

`TaskList`, then `TaskGet` your task immediately before claiming it. Claim with `TaskUpdate`
(`owner: "code-review-r2"`, `status: "in_progress"`); mark `completed` when done.

**You will receive your own claim back as an assignment. Do not act on it** - `TaskUpdate(owner=you)`
enqueues a notification delivered after the work, with `assignedBy` naming YOU.

## What you are reviewing

**`src/fast_mcp_jobvite/config.py`, `server.py`, `__main__.py`, `audit.py`, `utils/redaction.py`,
`services/jobvite_client.py`, and every test and harness that came with them.** That is U1, U3 and
U4. **No reviewer has read any of it.** Each was self-reviewed by its own author with mutation and
amputation harnesses, and a harness written by the author of the code it tests shares that author's
blind spot - measured here: three of four mutants once survived a script's own `--self-test` and
were killed by an independent test.

**Round 1 covered U0, U2, U11 and U15 only.** Do not re-review those except where U1/U3/U4 changed
their behaviour.

## What round 1 explicitly did NOT do, and you should

Its own report says so rather than implying coverage:

1. **It did not read the TIER-1 standards.** The index is
   `/home/plafayette/claude_projects/evolv/MUST-READ-DOCS.md`. For this code the ones that bite are
   `ai/tool-calling.md`, `architecture/error-contract.md`, `backend/error-handling.md`,
   **`backend/rate-limiting.md`**, `backend/python.md`, `ai/prompt-injection.md`.
   **`priority: required` in the frontmatter is the only authority marker and outranks this brief.**
2. **It did not work `docs/CODE-REVIEW-CHECKLIST.md` row by row.** Do that explicitly. A checklist
   catches the row nobody thought to look for, which is the whole argument for having one.

## Named open questions the authors could not settle

These are handed to you because the unit that raised them could not close them:

- **U4's timeouts.** `httpx2.Timeout(connect=5, read=30, write=30, pool=5)` was chosen from nothing
  more authoritative than "not a single scalar". **Check it against `backend/rate-limiting.md`,**
  which U4 never opened.
- **U3's transport spellings** `"stdio"` and `"http"` versus U1's transport selection in
  `config.py`. One grep settles whether the audit event's `transport` field agrees with the rest of
  the server. Nothing currently fails if it does not.
- **U3's `ctx.request_context.meta`** is tested against the wire contract, not a live FastMCP
  context, because no server existed to get one from. If it is not a plain mapping of the wire
  `_meta`, U3's parse call site is wrong and no test here would say so.
- **U3 never reconciled its emission against ADR-0011** (three log producers, not one). It read that
  ADR for status only.
- **U4 has never seen a real success body.** Every success assertion is against a synthetic
  hypothesis.
- **Coverage against ADR-0010's 95% floor for `utils/`** was never measured by U3.

## Where I would look first

Leads, not a scope limit. **Finding something I have not listed is worth more than confirming
something I have.**

1. **The seams between the three units**, which is where nobody was responsible. `audit.py` calls
   `utils/redaction.py`; `jobvite_client.py` must not defeat that single redaction point;
   `config.py`'s `SecretStr` reaches `jobvite_client.py`'s `SecretValue` Protocol. **Each unit
   tested its own side.**
2. **Secret safety, hard.** This code holds credentials and builds a URL that carries `sc=` as a
   query parameter. Look for any test, fixture, failure message, log line or exception path that
   would print one. Round 1 found exactly this and it was its highest finding.
3. **Assertions that pass vacuously.** Three of U3's five verification items are ABSENCE claims. For
   each, ask what the test does if the thing it inspects is empty, missing or silent.
4. **The harnesses that grade the code.** Does each control exercise what its name says? U4 found one
   of its own rows passing 36/36 because the injected branch was unreachable - **the row tested
   nothing and said so by passing everything.**
5. **`config.py`'s empty-is-absent rule.** U1 made an empty string mean "absent" so the committed
   template does not crash. What else does that admit? A whitespace-only credential? A variable set
   to `""` deliberately?
6. **The shutdown path.** `os._exit` in a `finally`, an interlock, and a three-cycle arm added
   because a single cycle was measured to be a coin flip.

## How to judge, and the traps this repository has already paid for

- **Judge every gate by EXIT CODE**, on its own line. Under `set -euo pipefail`,
  `cmd | grep FAIL || echo clean` prints "clean" when `cmd` FAILS - I did that and committed a red
  map. **One gate is red on purpose**: `check-cross-references.py` on `DESIGN.md:603`, held for
  ADR-0019. Do not report it.
- **A test NAME is an unverified claim about its BODY.** Two collisions here were exactly that.
- **An absence is a claim about where you looked.** State your search and positive-control it.
- **Verify citations by SUBJECT.** Three range-contraction defects were found in one day and every
  one still resolved to plausible text.
- **`PYTHONDONTWRITEBYTECODE=1`** for in-place mutation; prove a mutation LANDED before running and
  RESTORED after, comparing against git rather than `grep -F`.
- **A surviving mutation is the strongest finding you can bring me.**

## The standing rule on findings

**EVERY finding at EVERY severity - Critical, High, Medium, Low, nit - ships with a SUGGESTED FIX**,
marked as your suggestion to be verified rather than applied blindly. A finding without a remedy
costs the author the whole diagnosis a second time.

## Isolation

- **READ-ONLY on the repository.** Do not edit, commit, stash or check anything out in it.
- Pin the SHA you start from and `git worktree add /tmp/code-review-r2-work <sha>` if you need to run
  things. **`adr-batch` is in flight** and is rewriting `DESIGN.md`, its citations, `ci.yml`,
  `CONTRIBUTING.md` and `OBLIGATIONS.md`. **Pin, and say which SHA you pinned** - your findings are
  judged at that SHA and I need to know which.
- **Remove your worktree when done** and say so.

## How to deliver

1. **Write your report to `docs/reviews/REVIEW-CODE-R2.md` in your worktree and COMMIT it on a
   branch `review/code-r2`.** **Not `/tmp`.** Round 1's 48KB report was written only to a scratchpad
   and a restart destroyed it - nineteen findings with their evidence and fixes, gone. That is why
   this brief is in the repository and why your report must be too.
2. `SendMessage` `to: "team-lead"` with the full report. **`to: "main"` does NOT work.**

Structure: a tally, then each finding with its evidence and **its suggested fix**, then **what you
checked and found clean** so the absence of a finding is bounded, then the checklist worked row by
row, then **what you did NOT verify** - what you could not settle, not what you did not try.
