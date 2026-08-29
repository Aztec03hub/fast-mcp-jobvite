# ADR-0021: `approval_state`'s "mechanism" is required by two rows and defined nowhere

**Status:** Accepted
**Type:** Design change

> **Accepted and APPLIED**, in the ADR batch, before U10. It asked the design to define a field it
> required an implementer to invent, and the vocabulary it settles is U10's to emit, so resolving
> it before U10 was the point of not holding it on sequencing alone.

## Context

Found by **building U3**, not by reading. U3 emits the audit event, so U3 is the unit that has to
put the field on the wire.

**Two rows require the field.**

`DESIGN.md:1273-1275`, §8's required case for the audit event, states that the event carries
*"on the write `approval_state` together with the mechanism that produced it (§5.3)"*.

`DESIGN.md:1753`, threat row **C4-R1**, rated **High**, states its mitigation as
*"**Mitigated in §5.3:** the audit event includes `approval_state` and the mechanism that produced
it"*, and names §8's audit-event case as its test.

**§5.3 does not contain it.** `DESIGN.md:676-682` is §5.3's whole treatment of `approval_state`:

> **The audit event includes `approval_state`.** `agent-guardrails.md:121-123` names it explicitly,
> and `create_candidate` is gated two ways and emails a live human [...] We record what we can
> prove - that an approval response was received and what it said - and **ADR-0009** records that
> identity is unsatisfiable **for the approver specifically, and not for the caller.**

That paragraph settles *what* is recorded (a response was received, and what it said) and *who*
cannot be (ADR-0009). It says nothing about a mechanism. Grepping `mechanism` across the whole of
§5.3 - `DESIGN.md:580-733` - returns exactly one hit, `DESIGN.md:609`, and it is about the
`ContextVar`:

> That is the failure this **mechanism** exists to prevent [...]

So both rows cite §5.3 for a requirement §5.3 does not state. **Verified by subject and by
exhaustive grep over the section's line range, not by reading around a line number.**

**Why this is worse than a dangling citation.** ADR-0019 records a cross-reference that points at a
section which does not exist; a reader who follows it finds nothing and knows they have found
nothing. Here the reader follows the citation, finds a real and relevant paragraph, and has no
signal that the specific thing they came for is absent. C4-R1 is a **High** row whose mitigation
text reads as settled. It is the shape `docs/reviews/CITATION-AUDIT.md` was opened for: a citation
that resolves is not a citation that supports.

**And the field is not obvious.** §7.5 makes approval **dual-era** - elicitation on one era,
sampling with `ctx.input_responses` on the other, and a no-handler arm that fails closed and
surfaces differently on each (`DESIGN.md:1358-1361`). "The mechanism that produced it" is most
plausibly *which of those paths answered*, which is exactly the distinction §8's approval case
turns on. But that is an inference. Two implementers will not make the same one, and the value ends
up in an audit record that a compliance reader will later treat as authoritative.

## Decision

**Define the mechanism in §5.3, beside `approval_state`, and make its vocabulary closed.**

1. Add to `DESIGN.md`'s §5.3 approval paragraph a sentence stating that the audit event records
   **which approval path produced the response**, in a field named `approval_mechanism`, drawn from
   a closed set: `elicitation`, `sampling`, `no_handler`. The set is closed for the same reason
   `error-contract.md`'s registry is closed (`DESIGN.md:510-511`): a value emitted into an audit
   record is a contract, and an open string invites a fourth spelling of the first three.
2. Repoint `DESIGN.md:1275` and `DESIGN.md:1753` at that sentence once it exists. Until then both
   cite a subject their target does not carry.
3. §8's audit-event case gains the corresponding arm: on the write, `approval_mechanism` is present
   and is one of the three.

**What U3 shipped in the meantime, so the record is accurate.** `audit.py` carries
`approval_mechanism` as an optional field on `AuditEvent`, omitted when unset, with no vocabulary
enforced - U3 does not call the approval guard and has nothing to enforce against. U3's test
(`test_case4_the_write_records_approval_state_and_its_mechanism`) asserts the field reaches the
record and nothing about its value. **The vocabulary is U10's to emit and this ADR's to define; U3
deliberately did not invent one**, because a closed set invented by the unit that cannot exercise
it is a guess that later reads as a decision.

## Consequences

- **U10 is unblocked on a question it would otherwise have answered silently.** It is the unit that
  knows which path answered, and without this it would pick three strings and move on.
- **C4-R1's mitigation becomes checkable.** Today `check-coupling.py` verifies that the row names a
  §8 case which exists (`docs/reviews/PLAN-REVIEW-R*` and GATE-1 record that this is all it
  verifies). It cannot see that the §8 case names a field the design never defines, so the row is
  green on a mitigation that is one inference short of real.
- **One more field on every write's audit record.** No PII: the value names a protocol path.
- Applying this is a `DESIGN.md` edit and therefore blocked behind the freeze in the same way as
  ADRs 0012, 0013, 0014, 0017 and 0019. It should join that batch.

## What this does NOT settle

- **It does not settle what `approval_state` itself may contain.** `DESIGN.md:676-680` says "what it
  said", which is not a vocabulary either. That is a second gap in the same paragraph and this ADR
  deliberately does not fold it in - `docs/worklogs/U2-REPORT.md`'s D1 and ADR-0017 record what
  happens when one ADR resolves two things and reviewers approve the one they were looking at.
  It is raised here so it is not lost, and it needs its own decision.
- **It does not settle whether a fourth path exists.** §7.5's dual-era treatment names elicitation
  and sampling and the absence of a handler. If a host answers some other way, the closed set is
  wrong and the audit record will say so by failing rather than by absorbing it, which is the
  intended direction.
- **It does not settle ADR-0009's boundary.** *Who* approved stays unknowable. This is about *how*
  the answer arrived, which is knowable, and conflating the two is the error ADR-0009's own text
  warns about (`DESIGN.md:690-693`).
- **It does not audit the rest of the corpus for the same shape.** Two rows were found because U3
  had to emit the field. `docs/reviews/CITATION-AUDIT.md` covers citations that do not resolve;
  **a citation that resolves to the wrong subject is a different sweep and nobody has run it.**
