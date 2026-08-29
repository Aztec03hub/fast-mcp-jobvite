# M-5 and L-1 - a third-party exception message reaches the API consumer

**Read `docs/briefs/PREAMBLE.md` first.** It carries the task tools, isolation, evidence standards,
gates and delivery rules, and they are not repeated here.

Your agent name is `fix-m5-l1`. Your branch is `fix/m5-exception-detail`. Your report goes to
`docs/worklogs/FIX-M5-L1-REPORT.md`.

## M-5, and it is a `priority: required` breach

`standards/backend/error-handling.md` is `priority: required` and says, at two separate lines I have
verified at source:

- `:383` - *"Never leak raw exception messages from third-party libraries to API consumers"*
- `:493` - *"never pass `str(exc)` from third-party libraries"*

`src/fast_mcp_jobvite/services/jobvite_client.py` passes `f"{type(exc).__name__}: {exc}"` into
`JobviteUnavailableError.detail`, and that `detail` reaches the caller unchanged. Confirm this
end-to-end yourself - `grep -n` for the construction and follow `detail` to where it is serialised.

**`redact_text` does not save it.** Redaction bounds the credential classes it knows about. An
httpx2 exception string can carry an `_ssl.c` line number, a local socket path, or a resolver
detail - none of which are credential-shaped, and all of which are third-party internals reaching a
consumer.

**What the design actually requires**, so you fix this without over-reaching: `DESIGN.md` requires
`detail` to let a caller **distinguish an upstream outage from an open circuit breaker.** That is
all. A stable, enumerated reason string satisfies it. Verify that clause at the frozen SHA and quote
it - I am telling you my reading, not a fact you should adopt unchecked. **No ADR is needed**; I
grepped the design before saying so, but check me.

The full exception text does not vanish - it goes to the log, which is the correct destination.

## The sharp part, and it is why this is not a two-line change

`test_a_transport_error_on_the_jobfeed_route_is_redacted` asserts **`"jobvite.com" in detail`** as its
positive half.

**The control depends on the leak.** It is there to prove the redaction assertion is not vacuous, and
it does that by requiring that something real reached `detail`. Fix M-5 and this test fails - and it
fails *correctly*. Do not delete it and do not weaken it to `assert detail`. Re-point the positive
control at the log record, which is where the detail now goes, so the test still proves that
redaction ran over real content rather than over an empty string.

## L-1 converges with it, which is why they are one task

`redact_headers` in `src/fast_mcp_jobvite/utils/redaction.py` is called by nothing, and no planned
unit schedules a caller. It is correct and unwired.

It is not dead code to delete: **M-5's replacement log line is the caller it was written for.** Give
it one. That resolves L-1 by wiring, not by deletion, and it means the log line that receives the
exception detail is itself redacted rather than trusted.

Confirm the orphan claim yourself before acting - "called by nothing" is a claim about where I
looked, and I looked with grep.

## Why this waited for the audit-logging merge

It is merged, at `0d34c66`. Your fix needs a log assertion, and that branch rewrote how sinks are
configured and observed - a collision on **test approach**, not on files.

**Use the idiom it established: observe what the PROCESS writes, not what a fixture's sink saw.**
Read `tests/test_logging_process.py` and `docs/worklogs/FIX-AUDIT-LOGGING-REPORT.md` before writing a
single assertion. A fixture-local sink is exactly how the H-1 defect hid, and how a real credential
leak from `httpx2` sat unseen in `basicConfig` output.

## One live lead you should check while you are in this code

That report's sharpest unverified item: **`_redact_message` in `__main__.py` covers
`record["message"]` only, not `record["exception"]`** - and `serialize=True` renders both. I have
confirmed the asymmetry at source (`__main__.py:131` is the only `record[` assignment).

Nobody has enumerated the producers to show no live path reaches it, and **your change deliberately
routes an exception into the log**, which makes you the most likely person to create that path. Check
it as part of this work. If it is reachable, fix it here and say so; if you convince yourself it is
not, say exactly how you enumerated.

## Prove it, do not assert it

- An **amputation** row: delete the redaction on the new log line and show a test goes red.
- A **negative arm**: a `detail` that a caller can still act on - the outage-versus-breaker
  distinction must survive your fix. A fix that makes `detail` useless passes M-5 and breaks the
  design.
- Wire any new row into `ci.yml` and `CONTRIBUTING.md` **in the same commit**. Two harnesses had no
  CI step at all until last week, and that was found by an agent, not by a gate.

## In the report

The two standards clauses quoted from source; the design clause on `detail`, quoted from the frozen
SHA; what `detail` says now, verbatim, before and after; how you re-pointed the positive control;
where `redact_headers` is now called; and your finding on `record["exception"]` with the method you
used to reach it.
