# ADR-0012: A shared `utils/constraints.py` for the inbound constraints

**Status:** Proposed
**Type:** Design change

> **First ADR to carry `Type:`.** §13 separates the two jobs an ADR does here: recording a
> **Deviation** from a required standard, which is independent of the freeze, and making a
> **Design change**, which only exists after it. ADR-0001 to ADR-0011 are all `Deviation` and were
> filed while the design was open. This is the first of the second kind, and the field exists so a
> later reader can tell which one they are looking at without reconstructing the date.

> **Proposed, not Accepted.** The design edit is held until the implementation plan settles. The
> plan repoints its citations against the frozen `DESIGN.md` object, and landing a design change
> mid-repoint is what produced six wrong-subject citations once already. Flip to Accepted in the
> same commit that applies the edit.

## Context

§2.1 specifies four inbound structural limits and a character rule:

- control-character and bidi-override rejection, `DESIGN.md:172-175` — **one rule for every string
  argument on every tool**;
- nesting depth 5, list length 1,000, dict keys 100, `:162-164`;
- body size 1 MiB, `:165` — **already placed**, at the middleware, and therefore C2 rather than
  C3.

The first four are placed nowhere. §3's module layout, as frozen at revision 6, gives `tools/*.py`
their tools and their input models, and `models/` the allow-listed output models. There is no home
for a rule that every input model must apply.

**This gap was found by trying to parallelise, not by reading.** An implementation plan granted one
unit exclusive ownership of "the input-model modules", built its widest concurrent wave on that, and
the wave did not survive review: under one reading the unit collided with three others, under the
other with two. Settling *where input models live* fixed the ownership question and left this one —
**housing the models without housing the validators re-runs the same ambiguity one layer down.**

## Decision

Add one module to §3:

```
  utils/constraints.py        the shared inbound constraint types every input model reuses:
                              control-character and bidi rejection, and the depth/list/dict-key
                              limits (§2.1)
```

Every input model imports its constraints from here. No input model defines its own.

## Why this is an ADR and not a layout line

Q5's first half — recording that input models live beside their tools — went into §3 before the
freeze **because it recorded something the design already implied**: `C2-T1` (`:1679`) reads *"Payload shaping
happens in the tools and in `models/`, which is C3 and C6"*. That is a record, not a decision.

This is a decision, for two reasons:

1. **§3's block closes by enumerating the modules this design refuses** — *"No cache module, no bulk
   module, no custom logging module"* (`:297-298`). A section that justifies its absences owes a
   justification for an addition.
2. **There is a real alternative**, and it deserves a recorded rejection rather than a silent one.

## The alternative, and why it is rejected

**Rescope `models/` to hold input and output models together, and put the shared constraints there.**

Rejected because it merges the module footprints of two components that §11 deliberately keeps
apart: **C3 is the tool argument layer and C6 is the output pipeline**, they carry different
ratings, and C6-I1 (EEO exclusion) is Critical while C3's rows are Medium. A single directory
holding both makes the boundary between them a matter of filename convention rather than of
structure, and it is the reading under which the concurrency collision recurs.

The cost of the decision taken is one more module in a design that is proud of having few. That is
the honest trade and it is why this is written down.

## Consequences

- **The duplication is the obvious thing an implementer factors out on sight.** Four input models
  each carrying the same four limits is exactly the shape someone extracts into a helper without
  asking. Without this ADR that extraction is an unrecorded design change made by whoever happens to
  write the second tool; with it, the module is specified and the extraction is the plan.
- **No unit may plan a shared constraints module until this ADR is Accepted.** The implementation
  plan carries that prohibition explicitly, at the collision and again in Q5, so the refusal is in
  writing rather than rediscovered.
- **`utils/` gains a third member** — `correlation.py`, `redaction.py`, `normalise.py`, and now
  `constraints.py`. Each is a single-purpose module named for one enforcement point, which is the
  pattern §4.1 already sets at `:311`: *"Enforced in one place, `utils/redaction.py`"*.
- **§11 is unaffected.** No row changes rating, disposition or test. This places existing controls;
  it does not add or remove one.

## What this ADR does not settle

Whether the constraint types are Pydantic `Annotated` aliases, validators, or a base model is an
implementation choice and is left to the unit that builds them. This ADR settles **where they live
and that there is one copy**, which is the part that governs file ownership and therefore who may
work concurrently.
