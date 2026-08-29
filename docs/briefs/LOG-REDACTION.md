# LOG-REDACTION - ADR-0026 is Accepted, and the install must be idempotent

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `log-redaction`. Your branch is `fix/log-redaction`. Your report goes to
`docs/worklogs/LOG-REDACTION-REPORT.md`, committed on your branch. Your task record is **#83**.

**Read `docs/adr/0026-*.md` in full, INCLUDING the "Ruling, 2026-08-29" section at the end** - the
ruling adds a requirement the ADR body does not state, and it is the requirement most likely to be
missed.

## What to build

`JobviteClient.__init__` installs the redaction `logging.Filter` on the `httpx` logger, with an
opt-out keyword defaulting to installing.

**The opt-out is a constructor argument and NEVER a `Settings` field.** ADR-0025 is precisely about a
setting nothing reads; a second one is not the answer. The ADR says this explicitly.

Option 1 of three was chosen because a credential leak is a worse default than a surprising side
effect, and because option 3 - a documented `install_log_redaction()` an embedder must call - is a
documented obligation enforced by nobody, which is the same shape as a setting nothing reads, a
comment naming a variable that does not exist, and an absent obligations row. This project found all
three in one week.

## THE PART THE ADR DOES NOT SAY, AND THE DEFECT IF YOU MISS IT

**The install must be IDEMPOTENT.**

`JobviteClient` is constructed **once per invocation**. That is not a guess - it is written in the
tree at `src/fast_mcp_jobvite/services/jobvite_client.py:994`, as the reason the breaker is
module-level rather than per-instance, and three call sites build one: `tools/jobs.py:330`, `:642`
and `tools/candidates.py:575`.

A `logging.Filter` appended in `__init__` therefore stacks **one filter per tool call, forever**, in
a long-running server. Every log record then walks a list that grows without bound. **That is a slow
leak inside the change written to stop a leak**, and tests will not see it because they build a
handful of clients and exit.

**The test for it is not "the filter is installed"** - that passes on the first call and proves
nothing. Build N clients, assert the filter count on the `httpx` logger is exactly 1, and
**amputate the idempotence check** to confirm the assertion goes red.

## Then invert the probe

`docs/reviews/probe-u12-f2-embedder-leak.py` currently **demonstrates** the defect and exits 0 when
it leaks. It is deliberately unwired, because gating on it would gate on the bug staying.

Once the fix lands, invert it into an assertion and wire it, with the treatment
`docs/reviews/probe-r6-breaker-reset.py` got at `3ef01f5`:

- **Every arm's verdict derived from the same predicate the gate uses.** That probe printed
  `not counted (ok)` beside a failing counter because the verdict string and the exit code were
  computed in two places.
- **A positive control proving an arm can still READ a leak** when one is present. A probe that can
  only pass is indistinguishable from one that cannot fail.

Note the probe carries `# pragma: allowlist secret` on two lines - leave those alone, they are what
keeps CI's secret scan green.

## Rewrite, do not append

The README currently discloses that an embedder must call `configure_logging()` themselves. That is
accurate until this lands and wrong after. **Rewrite the passage in place.** Appending a correction
leaves two contradictory claims, which is the failure this project rewrote a whole review document
to avoid.

## Say what this is, and what it is not

**The shipped server was never exposed.** `configure_logging()` runs at `__main__` module scope on
every shipped path, and U12's C5-I1 arm asserts the redaction fires there - including on httpx2's own
record, asserted PRESENT rather than merely absent. This closes an **embedder's** exposure. Say that
plainly in your report rather than implying a live leak was fixed.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - they were 801 and 415 as this was written and
will have moved. **0 skips.**

**Run the gate's OWN commands, argument for argument.** Specifically `uv run --frozen mypy`, NOT
`mypy src` - I spent a day reporting "mypy clean" from a command that checked 23 files while CI
checks 65, and shipped a type error to `main` that way. `ci.yml:422` is the authority.

`ci.yml` is the orchestrator's; put any steps you need in your report.

## In the report

The measurement that the install is idempotent, and the amputation proving that assertion can fail.
The probe's before and after. Then what you could not settle - that list is for what you CANNOT
settle, not what you did not try.
