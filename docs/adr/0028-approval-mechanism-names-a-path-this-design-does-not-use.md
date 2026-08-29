# ADR-0028: `approval_mechanism`'s closed set names `sampling`, and this design has no sampling path

> **This was written as ADR-0027 and renumbered on merge.** Two agents claimed 0027 within the same
> hour: `u10-write` checked `git log --all` before choosing, found 0026 taken and 0027 free, and was
> correct at the moment it looked - I created the other 0027 afterwards, on a different branch.
> **Neither of us did anything wrong and the collision still happened**, which is why
> `docs/reviews/check-adr-numbers.py` now exists. The number on main at merge time keeps its
> identity; this one moved, and every inbound reference moved with it in the same commit.


**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> **Found by BUILDING U10**, the unit that emits the field. ADR-0021 defined the vocabulary before
> anything could exercise it, which is the risk that ADR's own last section names about itself. This
> is that risk landing.
>
> **ADR-0026 was taken while U10 was in flight** (the log-redaction entry-point decision), so this is
> 0027. The brief dispatched it as "0026 is free"; `docs/adr/` on another ref already held one, which
> is why the brief also said to check.

## Context

**ADR-0021 closed the `approval_mechanism` vocabulary at three values** and made the set closed
deliberately, for the reason `error-contract.md`'s registry is closed (`DESIGN.md:510-511`): a value
emitted into an audit record is a contract, and an open string invites a fourth spelling of the first
three. `DESIGN.md:1276-1278` carries the applied result - the write's audit event records
`approval_mechanism`, *"present and one of `elicitation`, `sampling`, `no_handler`"*.

**This server has no sampling path.** `DESIGN.md` §7.5 specifies exactly two mechanisms and neither
is sampling:

- the handshake era uses **`ctx.elicit()`** - which the closed set does name, as `elicitation`;
- the sessionless era uses **MRTR**, Multi Round-Trip Requests: the tool returns an
  `InputRequiredResult` carrying an `elicitation/create` request and the client retries the original
  call with `inputResponses` attached (`DESIGN.md:1051-1054`). MCP sampling is the server asking the
  client's *model* for a completion. It is a different protocol facility, and this design never uses
  it.

**Where the wrong noun entered is traceable to one sentence.** ADR-0021's own context paragraph
describes §7.5 as *"elicitation on one era, **sampling** with `ctx.input_responses` on the other"*.
`ctx.input_responses` is the MRTR accessor; the paragraph attached it to the wrong mechanism name,
and the closed set was then drawn from that paragraph.

**So the audit record's most informative field is wrong on one of the two eras it exists to
distinguish.** ADR-0021's stated purpose is that *"which approval path produced the response"* be
recordable, because a compliance reader will later treat that record as authoritative. On the
sessionless era it currently reads `sampling`, naming a facility that was never invoked.

**This is not a citation defect and grepping would not have found it.** The field exists, the set is
closed, the design states it, and a checker verifying that the emitted value is one of the three
passes. Only building the two paths and asking *which one is this* exposes it - which is the shape
`docs/reviews/CITATION-AUDIT.md` records for citations that resolve to the wrong subject, one level
down, in a vocabulary rather than a reference.

## Decision

**Rename the sessionless value from `sampling` to `mrtr`, and keep the set closed at three.**

1. Amend the vocabulary in `DESIGN.md` §5.3 to `elicitation`, `mrtr`, `no_handler`.
2. Amend `DESIGN.md:1276-1278`'s §8 arm to the same three.
3. `src/fast_mcp_jobvite/approval.py`'s `ApprovalMechanism.SAMPLING` becomes `MRTR`, and
   `tests/test_approval_write.py`'s two era-parameterised expectations follow.

**What U10 shipped in the meantime, so the record is accurate.** `approval.py` emits `sampling` for
the MRTR path, because the set is closed by an **applied** ADR against a **frozen** design and a unit
that invents a fourth string is a unit that decided a contract on its own. The wrong value is
emitted with the mismatch documented at its definition, which is the direction that leaves a reader
able to find this. **U10 deliberately did not rename it unilaterally**, for the reason ADR-0021 gives
about its own restraint: a vocabulary settled by the unit that could not exercise it is a guess that
later reads as a decision, and so is one changed by the unit that could.

## Consequences

- **One audit value changes.** No PII either way: the value names a protocol path.
- **Any consumer keyed on the literal `sampling` breaks**, which today is
  `tests/test_approval_write.py` and nothing else - the write has never run against a live tenant.
  Doing this before a credential exists is the cheapest this change will ever be.
- **`DESIGN.md` is frozen**, so this joins the next ADR batch rather than being applied here.
- **ADR-0021 stays correct in its substance.** It was right that the mechanism must be recorded and
  right to close the set; only one member's name is wrong. This ADR does not reopen the decision.

## What this does NOT settle

- **It does not settle `approval_state`'s vocabulary.** ADR-0021 raised that as a second gap in the
  same paragraph and deliberately declined to fold it in, and this ADR declines for the same reason -
  ADR-0017 and `U2-REPORT.md`'s D1 record what happens when one ADR resolves two things and reviewers
  approve the one they were looking at. U10 emits `approved`, `refused`, `pending` and `unavailable`,
  chosen by the implementer and named in `approval.py` so they are visible as a choice. **That is
  four values against a design that defines none, and it needs its own decision.**
- **It does not settle whether a fourth path exists.** If a host answers some other way the closed
  set is wrong, and the audit record will say so by failing rather than by absorbing it - which
  ADR-0021 records as the intended direction and this ADR keeps.
- **It does not audit the rest of the corpus for the same shape.** One vocabulary was found because
  U10 had to emit it. **A sweep for other closed sets whose members name things this design does not
  do has not been run**, and it is a different sweep from the citation one.

## Ruling, 2026-08-29

**ACCEPTED. `sampling` becomes `mrtr`, and the set stays closed at three.**

All three amendments land together - `DESIGN.md` §5.3's vocabulary, the §8 arm at `:1276-1278`, and
`approval.py`'s `ApprovalMechanism.SAMPLING` with the two era-parameterised expectations in
`tests/test_approval_write.py`. A vocabulary amended in the design and not in the code is the same
disagreement pointing the other way.

### U10's restraint was correct and is the reason this ADR is cheap

U10 emitted the wrong value **deliberately**, with the mismatch documented at its definition, rather
than inventing a fourth string. The set was closed by an applied ADR against a frozen design, and a
unit that widens a closed set has decided a contract on its own. Because it did not, the fix is a
rename and three call sites rather than an archaeology exercise.

**And the reason it did not rename unilaterally is the reason to keep applying:** a vocabulary settled
by the unit that could not exercise it is a guess that later reads as a decision. That cuts both ways,
which is why ADR-0021's restraint about `ApprovalState` is being honoured separately at task #84 and
NOT folded in here.

### The one thing the implementing work must not do

**Do not rename the value and leave the documented mismatch in place.** The comment at the definition
exists to tell a reader the emitted string disagrees with the design; once it agrees, that comment is
false. Rewrite it in place to record the history, or delete it - do not leave two claims where the
code now contradicts its own note.
