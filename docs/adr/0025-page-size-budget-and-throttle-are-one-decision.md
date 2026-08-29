# ADR-0025: the page size, the outbound budget and the self-throttle contradict each other

**Status:** Accepted (orchestrator, 2026-08-29) - and the three questions are ANSWERED below
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

## Ruling, 2026-08-29 - accepted, and answered rather than re-deferred

**Accepting this ADR as a framing and stopping there would relabel the deferral, not end it.** The
three questions are answered here. They are answered together because, as the ADR argues, each one
alone falsifies the other two - and the arithmetic below is what shows that is literally true rather
than rhetorical.

### Q1. An exhaustive scan uses the RAW TRANSPORT CAP

`min(transport_cap, configured_result_cap)` conflates two different axes. **The result cap bounds
what the CALLER gets back; the transport cap bounds what we ASK JOBVITE FOR.** The design already
names this exact confusion in the other direction at `DESIGN.md:166-169`, where it warns that §4.5's
page caps are *"outbound transport limits ... and bound nothing about what a caller sends us"*.
Letting a caller's `max_results` shrink our wire page is the same mistake pointing the other way.

The measured cost decides it. `V2_PAGE_CAP = 500`, `DEFAULT_MAX_RESULTS = 50`, and the ADR's own
worked example is a 1,240-record resource:

```
min(500, 50) =  50 per page  ->  25 requests  ->  4m 10s at 6/min
raw cap      = 500 per page  ->   3 requests  ->  ~30s   at 6/min
```

**U6 was right to delete its invented branch** - the design stated no policy and an implementation
must not invent one. The design now states one.

### Q2. The throttle is PER-PROCESS

The throttle exists to protect Jobvite from us, and **Jobvite sees our process, not our scans.** A
per-scan throttle lets N concurrent scans each spend 6/min, so the rate arriving at Jobvite is 6N and
the limit means nothing.

This is the same argument the tree already makes for the breaker at `jobvite_client.py:994` - one
instance per dependency, module-level, because it records what the DEPENDENCY has been doing.
Scoping the throttle differently from the breaker would give two mechanisms with the same purpose
opposite ideas of what they are protecting.

### Q3. The budget bounds wall-clock INCLUDING throttle waiting

Half of this is already settled by the frozen design and I nearly ruled past it: `DESIGN.md:373-375`
says the budget *"bounds all attempts for one tool invocation"*. **The budget is per-invocation, not
per-process**, and that was never open.

What was open is whether throttle waiting spends it. **It does.** The budget's stated purpose is that
*"a slow Jobvite surfaces as a typed 503 rather than an unbounded wait"*, and a bound that excludes
the term which dominates the wait is not a bound. A caller does not care whether we were waiting on
Jobvite or waiting on ourselves.

**This is the answer that would be unaffordable under Q1's rejected alternative, which is the ADR's
thesis made concrete.** At 50 records per page an exhaustive scan spends 4m10s in throttle waiting
and a 60s budget fails every time - the failure mode the ADR predicts, *"a 503 that looks like
Jobvite being slow and is actually three of our own defaults disagreeing"*. At 500 it costs ~30s and
fits. **Q1 is what makes Q3 payable.**

### What this ruling still does not settle, and deliberately

**None of the three constants.** 6/min is recorded in the design as a conservative guess and not a
vendor figure; 60s and the retry counts are U7's choices with nothing observed about Jobvite's
latency; 500 is unobserved as a server limit. This ADR was always about the composition, and the
composition is now decided for any values those rows eventually produce.

**The throttle is still unimplemented.** The ADR's warning stands and is now more pointed: implementing
it before this composition landed would have turned a latent contradiction into a live one. Whoever
implements it implements this ruling with it, not before it.
