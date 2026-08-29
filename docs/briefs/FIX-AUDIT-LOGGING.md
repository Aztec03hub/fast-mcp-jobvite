# FIX-AUDIT-LOGGING - the audit trail records nothing, and its failure policy cannot fire

## Tools you must load before you start

    ToolSearch with query: select:TaskCreate,TaskGet,TaskList,TaskUpdate

`TaskList`, then `TaskGet` your task immediately before claiming it. Claim with `TaskUpdate`
(`owner: "fix-audit-logging"`, `status: "in_progress"`).

**You will receive your own claim back as an assignment. Do not act on it** - `TaskUpdate(owner=you)`
enqueues a notification delivered after the work, carrying the description as it stood when you
claimed it. Two agents have already correctly identified and ignored this echo. `TaskGet` first.

## The three defects, all measured, none of them yours to re-derive

Round 2 of the code review found the first two and I reproduced both myself. **You do not need to
confirm they exist. You need to fix them and prove the fix.**

### H-1: every mandated field is dropped in production

`audit.py` and `services/jobvite_client.py` do `from loguru import logger`. **Nothing in `src/`
calls `logger.add` or `logger.configure`.** `__main__.py` configures **stdlib `logging`** - a
different library. Loguru's autoinit handler has no `{extra}` in its format and `LOGURU_SERIALIZE`
is unset, so:

```
logger.bind(tool_name="search_jobs", request_id="abc-123", transport="stdio").info("tool_invocation")
-> 2026-08-28 22:36:52.722 | INFO | __main__:<module>:2 - tool_invocation
```

`tool_name`, `request_id` and `transport` appear **nowhere**. That breaches
`ai/tool-calling.md:171-179`, which mandates those fields, and it voids ADR-0011's own justification
for keeping a third log producer.

**Why the tests pass**: the fixture installs its OWN sink and reads `record["extra"]`. A real loguru
stream, just not the one the server writes to. **The tests are correct about the API and silent
about the deployment**, which is the gap you are closing.

### H-2: the fail-closed branch cannot fire

**Loguru handlers default to `catch=True`.** Measured: a sink that raises prints
`--- End of logging error ---` to stderr and **`.info()` returns normally**. So `emit`'s `except` is
dead code, and the `BEFORE_SIDE_EFFECT` branch - no audit, no write, the branch that stops a second
live candidate being emailed - never runs in production.

The existing test's `_ExplodingLogger` raises from **`bind()`**, which is not what fails when a disk
fills. **U3's own amputation confirms the gap**: `A1` deletes `emit()` entirely and
`test_arm1_before_the_side_effect_the_call_fails` still passes.

### H-3: ADR-0018 is asserted structurally and never observed

**This is the batch's own unverified item 3, and it is the same shape as the two above.** ADR-0018
made `os._exit(status)` carry `70` on an abnormal exit. The test asserts the **source text** says
`os._exit(status)` and that `EXIT_SOFTWARE = 70`. **Nothing ever forces `mcp.run` to fail and reads
the process's actual exit status.**

The design already knows an exit code can lie - §8 #18 refuses to assert shutdown by exit code for
exactly that reason. So a structural assertion about the source is the weakest possible discharge of
a defect *about* exit codes.

## What to build

1. **Configure loguru once, at startup, in `__main__.py`.** One explicit sink. Either
   `serialize=True` or a format that carries `{extra}` - **decide and say why**, because
   `ai/tool-calling.md` cares that the fields ARRIVE, and a human-readable format that drops a field
   under some condition is the defect again.
2. **Pass `catch=False` on that handler**, so a sink failure propagates and `emit`'s `except` becomes
   reachable. Check that this does not make an ordinary logging failure crash the server in a way
   the design does not want - `DESIGN.md`'s three-branch audit-failure policy is the specification,
   read it at the frozen SHA in your dispatch message.
3. **Reconcile with `__main__.py`'s existing stdlib `logging.basicConfig`.** Two logging systems
   writing to the same stream is its own defect. Say what you decided and why.

## How the fix must be proven, and this is the whole point

**Every assertion must observe the PROCESS's real output, not a fixture's private sink.**

- Spawn the server the way `tests/boot_process.py` already does, invoke the path that emits an audit
  event, and assert the mandated fields appear in **what the process actually wrote**.
- For H-2, make a **sink** fail - not `bind` - and assert the fail-closed branch runs.
- For H-3, force `mcp.run` to raise and assert the **process exit status is 70**, read from the
  process. Not from the source text.

**A test that installs its own sink proves the API and not the deployment. That is the defect.**

## Standing requirements

- **BOTH harnesses**, and any new row wired into `ci.yml` and `CONTRIBUTING.md` in the same commit.
  Extend the existing U1 and U3 harnesses rather than adding a fourth if the rows belong there.
- **`PYTHONDONTWRITEBYTECODE=1`** for in-place mutation; prove each mutation LANDED before running
  and RESTORED after, **comparing against git, not `grep -F`**.
- **The batch found that `str.replace` in a harness silently no-ops when an anchor moves**, and an
  amputation regex cut nothing while reporting a survivor that was never cut. **Assert your anchor
  is unique and present before mutating.**
- **Amputation survivors are the OUTPUT.** Gate on every row having applied its anchor.
- **Report passed-counts, never "green".** Baseline: **294 passed, 2 deselected, 0 skipped**.

## Isolation

- **The frozen SHA is in your dispatch message.** `docs/DESIGN.md` is frozen; read it as
  `git show <SHA>:docs/DESIGN.md`, never the working tree. A defect there is a **Proposed** ADR.
- Pin the SHA in your dispatch message. `git worktree add /tmp/fix-audit-work <sha>`.
- **Do NOT check anything out in the shared checkout.**
- Commit to **`fix/audit-logging`**. **I merge and push. Commit as you go** - a task was destroyed
  by a restart with zero commits.
- **`docs/OBLIGATIONS.md` is not yours.** Report the checker's own output if an anchor moves.
- **Remove your worktree when done** and say so.

## Gates

Full list in `CONTRIBUTING.md`. **mypy is the type gate, not pyright. Judge by exit code on its own
line** - under `set -euo pipefail`, `cmd | grep FAIL || echo clean` prints "clean" when `cmd` FAILS.
**Always quote your heredoc delimiter** (`<<'PY'`).

## How to deliver

1. `docs/worklogs/FIX-AUDIT-LOGGING-REPORT.md`, **committed on your branch.** Not `/tmp` - a 48KB
   report was destroyed that way.
2. `SendMessage` `to: "team-lead"`. **`to: "main"` does NOT work.**

State: what the process actually writes now, quoted; how you proved the fail-closed branch runs; the
observed exit status for H-3; what you decided about serialize-versus-format and about the two
logging systems; and the merge command.

**End with what you did NOT verify.**
