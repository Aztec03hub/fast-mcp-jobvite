# AUDIT-SHAPES - three audit shapes have never been swept, and the probe for it is UNVERIFIED

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `audit-shapes`. Your branch is `fix/audit-shapes` - **it already exists and
already has a commit on it.** Your report goes to `docs/worklogs/AUDIT-SHAPES-REPORT.md`,
committed on your branch. Your task record is **#104**.

## Read these first, in this order

1. `docs/DESIGN.md` at the SHA in `docs/DESIGN-FREEZE.txt` - the authority. Do NOT retype that SHA
   anywhere; read the file. **Find the audit trail by its SUBJECT, not by a section number**: the
   heading *"Audit logging and `request_id`"*, and the paragraph opening *"Audit-write failure has a
   stated policy, and the third case is the one that matters"*. This brief originally said "§7 (the
   audit trail)" and **that was wrong** - §7 is "Server, transport, configuration". The agent read
   the right text anyway and told me. Section numbers drift exactly like line numbers, which is why
   every citation in this repo is a subject phrase.
2. `docs/adr/` - **every** numbered ADR. An ADR overrides a standard inside its own scope.
3. `docs/reviews/probe-audit-row-container.sh` - the existing one-shape probe you are generalising.
4. The commit on `fix/audit-shapes` - **and read its message before its code.**

## THE SITUATION, and the first thing you must not do

`fix/audit-shapes` carries **one new file, 498 lines**:
`docs/reviews/probe-audit-shape-container.py`. It was written by an agent that was **killed by a
usage limit before it reported**. It was committed WIP purely so a worktree cleanup could not
destroy it.

**It is UNVERIFIED. No gate was ever run against it and it has never been run.** Treat it as a
starting point to verify, not a result to trust, and **re-derive every number in it.**

**DO NOT diff it against `main`.** Its base is `dad014e` and main has moved a long way since; the
diff in that direction shows my later commits reflected back and reads as if the branch deleted
things it never touched. That exact misreading cost me an hour on #115. Diff against
`git merge-base main fix/audit-shapes`.

## What the probe claims to do

It sweeps three audit shapes the existing probe never covered - `emit(...)`, `is_error=True`,
`AuditPhase.X` - by locating each with `ast`, deleting exactly that node using the node's own
`end_lineno`/`end_col_offset`, and running the suite. Two assertions guard every row: the file
still parses, and exactly one node of the shape went away.

`emit(` is deliberately first: deleting a `result_status` asks whether a failure was recorded AS a
failure, while deleting an `emit(...)` asks whether the row exists **at all**.

**Survivors are the OUTPUT, not a failure.** A site whose amputation leaves the suite green is a
behaviour with no assertion behind it. The probe reports and exits 0 unless it could not run.

## Your job, in order

1. **Make it run.** It has never been executed. Expect it to be broken.
2. **Prove it is not vacuous BEFORE you trust a single verdict.** A probe that mutates nothing
   reports a clean sweep. Required, and put each in the report:
   - the population is DERIVED, not listed - print it and check it against an independent
     enumeration of the container. A hand-kept list of one is what it exists to replace.
   - a planted site that MUST be killed is killed.
   - a planted site that MUST survive survives.
   - a row whose mutation does not land is REFUSED, not scored. Verify by making one not land.
3. **Run the full sweep** and report every survivor with the file, the shape and what it means.
4. **File a task per survivor.** Do not fix them here; the fix for a survivor is a test.

## The trap this repo keeps falling into

A green sweep from a probe you just widened is exactly the result to distrust, and the population
SHRINKING is the mechanism that manufactures it - I watched a citation scan's population fall 15
to 12 while reporting a clean zero. **Report the population size next to the verdict, every time.**

Also: `grep` counts a comment as a call site. Anything reasoning about `emit(` must use `ast`, and
the probe already knows this - do not regress it to a grep because a grep is easier to explain.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - they move hourly. **0 skips.**

**Run the gate's OWN commands, argument for argument.** `uv run --frozen mypy`, NOT `mypy src`.
`ruff check` and `ruff format --check` must be **chained with `&&`**, never
`cmd; echo "EXIT=$?"` - capturing a status into `$?` defeats the gate, and I pushed a lint-red
`main` that way on 2026-09-01.

ShellCheck is **v0.10.0 at `--severity=warning`**. If the binary is absent it does not fail, it
silently checks nothing.

## Delivery

**Commit to your branch. Do NOT merge and do NOT push.** Only the orchestrator merges and pushes.
Report by `SendMessage` to `team-lead` when done - a completion report is required, and your work
is invisible until you send one.
