# ADR-0011: Three log producers per invocation, not the mandated one

**Status:** Accepted
**Type:** Deviation

## Context

`backend/request-middleware.md:145` is a numbered rule:

> *"4. **One log per request**: The middleware emits exactly one structured log entry per request."*

This server emits **three** records per tool invocation, from three producers:

- `TimingMiddleware`, adopted in `DESIGN.md` §7.7;
- `StructuredLoggingMiddleware`, adopted in §7.7 with `include_payloads=False`;
- `audit.py`, the per-invocation audit event of §5.3.

The design argued the third convincingly and never reconciled the result with the clause, so the
deviation existed on the record only as an unexplained arithmetic difference between two sections.
A conformance re-sweep raised it as a defect for exactly that reason: the clause is not hard to
satisfy, it is that nobody had said which way we went.

## Decision

Keep all three. Deviate from `:145` deliberately.

## Consequences

**The third producer is forced and is the one the standards elsewhere require.**
`ai/agent-guardrails.md:121-122` and `ai/tool-calling.md:171-172` mandate an audit record carrying
tool name, **validated arguments with PII redacted**, result status, latency, the approval decision
if gated, and the correlation id. `StructuredLoggingMiddleware` cannot supply it: it runs with
`include_payloads=False`, because for this server those payloads are candidate personal data, and
that setting emits **no** arguments rather than **redacted** arguments. The mandated field is
redacted arguments. So the choice is not between one record and three; it is between three records
and breaching B17, which is a `priority: required` obligation with a Critical threat-model row
behind it (C7-I1, candidate PII in logs).

**Why the other two are not dropped to reach a count of one.** They are the framework's own
middleware, constructed with explicit arguments and verified in the spike, and they cover different
things: `Timing` measures the framework's view of the call, `StructuredLogging` records the
protocol-level event including calls that never reach a tool body. `audit.py` sees only invocations
that reach a tool. **A pre-dispatch argument rejection produces no audit event at all** (`DESIGN.md`
§5.1's third exception, and §2.1), so collapsing onto `audit.py` alone would make the failure path
callers hit most often the one path with no record. That is the opposite of what `:145` is for.

**What is genuinely lost by deviating.** The clause exists so a reader can reconstruct one request
from one line, and so log volume is predictable. Three producers means correlating three records,
and the instrument for that is `request_id`. **That instrument now exists**: DESIGN.md §5.3
specifies `request_id_var`, a per-Task ContextVar in `utils/correlation.py`, set where the id is
minted and reset in a `finally`, and C5-R1 has left the must-mitigate table (B39, B40 closed).

An earlier version of this paragraph said the mechanism was *missing* and that "until that lands,
this deviation costs more than it should". It landed in the same revision that closed the blockers,
which left this ADR contradicting the §13 summary of itself. **The cost that remains is the
deviation itself** - three records where the clause asks for one - and not a missing correlation
key. What a reader loses is having to join three records rather than read one; what they keep is
that all three carry the same id.

**Not a licence to add a fourth.** Three is the set: two framework middlewares whose defaults were
each justified in §7.7, and one audit event the standards separately mandate. Any further producer
needs its own argument, not this ADR.
