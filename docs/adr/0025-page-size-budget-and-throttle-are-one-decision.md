# ADR-0025: the page size, the outbound budget and the self-throttle contradict each other

**Status:** Proposed
**Type:** Design change

> Three defaults were chosen separately and cannot all hold. At `JOBVITE_MAX_RESULTS=50`,
> `JOBVITE_OUTBOUND_BUDGET_SECONDS=60` and `JOBVITE_OUTBOUND_RATE_LIMIT=6`, an exhaustive scan of
> the design's own 1,240-record example needs **25 requests, 240 seconds against a 60-second
> budget** - it dies with its own 503 at about request 7 and returns nothing. The contradiction is
> invisible today only because **the self-throttle does not exist**.

## Context

### The three figures, each defensible alone

| Figure | Value | Where |
|---|---|---|
| in-tool / configured result cap | `JOBVITE_MAX_RESULTS` = **50** | `DESIGN.md:1572-1575` |
| total outbound budget | **60s** | `DESIGN.md:373-375`, implemented by U7 |
| outbound self-throttle | `JOBVITE_OUTBOUND_RATE_LIMIT` = **6/min** | `DESIGN.md:1576-1581`, §4.4 |
| v2 transport page cap | **500** | §7.3, unobserved |

`DESIGN.md:1583-1584` already says the open question is "whether either default is *right*, which no
amount of specification settles and only a live tenant can." **This ADR is not that question.** It is
narrower and answerable now: the three do not compose, whatever the right values turn out to be.

### The arithmetic, using the design's own worked example

§7.7's example is `showing 50 of 1,240`. An exhaustive scan pages at
`min(transport_cap, configured_result_cap)` = **50**, so 1,240 records is **25 requests**.

- At 6/min, 25 requests is **240 seconds**. The budget is **60**. The scan dies at roughly request 7.
- At the raw v2 cap of 500, the same resource is **3 requests**, comfortably inside both.

**So the page size is not a tuning knob. It decides whether an exhaustive scan can complete at all.**

### The reason nobody has hit it

**`config.py`'s `outbound_rate_limit` is read by NOTHING.** Measured at `ec38835`:

```
grep -rn "outbound_rate_limit" src/
  src/fast_mcp_jobvite/config.py:228:    outbound_rate_limit: int = Field(default=6, ge=1)
  src/fast_mcp_jobvite/services/jobvite_client.py:579: # ... is NOT this and cannot be made ...
```

Two hits: the declaration, and a comment saying what it is not. **The self-throttle §4.4 requires
does not exist**, so 25 requests currently fit inside 60 seconds trivially.

**This is the same shape as the budget obligation, one mechanism over.** `DESIGN.md:373-375`
promised a total outbound budget and nothing implemented one until U7; that gap was found while
ruling a review finding wrong, not by a gate. This one was found while U7 tried to answer a paging
question. **Neither was found by anything designed to look.**

## Decision

**§7.3 and §4.4 must settle the page size, the budget and the throttle scope TOGETHER**, because any
one of them chosen alone falsifies the arithmetic of the other two. Three coupled questions:

1. **What page size does an EXHAUSTIVE scan use?** U6 shipped
   `min(transport_cap, configured_result_cap)` and deleted its own "exhaustive uses the raw transport
   cap" branch because the design states no paging policy and it had invented one. That was right.
   The design should now state one.
2. **Is the throttle per-process, per-scan, or per-attempt?** A budget scoped to one scan and a
   throttle scoped to a process interact differently from two scoped alike, and only one of those
   combinations makes an exhaustive scan finishable.
3. **Does the budget bound wall-clock INCLUDING throttle waiting?** If it does, the throttle spends
   the budget without making a request. If it does not, "total outbound budget" means something
   narrower than its name.

**No implementation should choose any of these silently.** U7 wrote no branch and no code comment
about it, and said so - which is why this ADR exists rather than a quiet constant.

## Consequences

### What this ADR does NOT claim

**Not that any of the three values is wrong.** 6/min is recorded in the design as a conservative
guess and not a vendor figure; 60s and the retry counts are U7's choices with nothing observed about
Jobvite's latency to support them; 500 is unobserved as a server limit. **This ADR is about the
composition, not the constants**, and it stays true whichever numbers checklist rows 2, 3 and 9
eventually produce.

**Not that anything is broken in production today.** `scan()` has no caller in `src/` and the
throttle is unimplemented, so the contradiction is latent in both directions. That is the argument
for settling it before U8 and U12 give it a caller - not for treating it as an incident.

**Not that the throttle should be implemented first.** Implementing it before this is settled turns a
latent contradiction into a live one: the default exhaustive scan starts failing with a 503 that
looks like Jobvite being slow and is actually three of our own defaults disagreeing.

### The one that is genuinely uncomfortable

**A gate would not have found either gap.** `outbound_rate_limit` is declared, typed, defaulted,
documented in `.env.example` and covered by config tests - all of which pass on a setting nothing
reads. `check-design-citation-shape.py`, the obligations map and the harnesses are all silent about
it, because none of them asks "does anything consume this?". That question has now produced two
findings in one day and is worth a checker of its own.
