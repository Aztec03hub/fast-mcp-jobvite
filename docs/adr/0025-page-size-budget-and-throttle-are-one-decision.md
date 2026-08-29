# ADR-0025: the page size, the outbound budget and the self-throttle contradict each other

**Status:** Accepted (orchestrator, 2026-08-29) - **Q2 and Q3 answered and APPLIED; Q1 WITHDRAWN**
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
| in-tool / configured result cap | `JOBVITE_MAX_RESULTS` = **50** | §10.1's variable list, the `JOBVITE_MAX_RESULTS` entry ("§7.7's in-tool result cap") |
| total outbound budget | **60s** | `DESIGN.md:373-375`, implemented by U7 |
| outbound self-throttle | `JOBVITE_OUTBOUND_RATE_LIMIT` = **6/min** | §10.1's variable list, the `JOBVITE_OUTBOUND_RATE_LIMIT` entry ("§4.4's self-throttle") |
| v2 transport page cap | **500** | §4.5, unobserved |

§10.1's variable list already says the open question is "whether either default is *right*, which no
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

**§4.5 and §4.4 must settle the page size, the budget and the throttle scope TOGETHER**, because any
one of them chosen alone falsifies the arithmetic of the other two. Three coupled questions:

1. **What page size does an EXHAUSTIVE scan use?** U6 shipped
   `min(transport_cap, configured_result_cap)` and deleted its own "exhaustive uses the raw transport
   cap" branch. Deleting it was right. **The reason recorded here was wrong, and the Ruling below
   withdraws this question over it.** This said *"because the design states no paging policy and it
   had invented one"*; §4.5 states one, and it is the rule U6 shipped, so the deleted branch was
   CONTRADICTING the design rather than filling a vacuum. Whether the policy §4.5 states is the
   RIGHT one is a real question, and it needs its own ADR amending §4.5.
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

## Ruling, 2026-08-29 - Q2 and Q3 answered; Q1 WITHDRAWN on re-reading the design

**Accepting this ADR as a framing and stopping there would relabel the deferral, not end it**, so Q2
and Q3 are answered here rather than re-deferred. **Q1 is WITHDRAWN**: the reading of the design it
rested on does not survive reading the design. The original ruling answered all three together, on
the argument that each alone falsifies the other two, and that argument is why Q1's withdrawal is
stated below with its consequences for Q3 rather than as a quiet deletion.

### Q1. WITHDRAWN, 2026-08-29 - it rested on a false reading of the design

**This question is withdrawn, not deferred, and what withdraws it is a measurement rather than a
change of mind.** Its answer was *"an exhaustive scan uses the RAW TRANSPORT CAP"*, and the argument
for it turned on a claim about what the frozen design says. That claim is false.

`git show 8a9d63c:docs/DESIGN.md`, §4.5, lines 453-455 of that blob, whole sentence:

> Offset-based, `start` and `count`. Page cap **500** on v2, **1000** on `/v1/jobFeed`. These are
> the *transport* limits. The *result* limit returned to a model is separate and configurable
> (§7.7); the two are related by `min(transport_cap, configured_result_cap)`.

**§4.5 states a paging policy, and `services/jobvite_client.py`'s `result_cap()` implements exactly
it.** The withdrawn answer closed *"U6 was right to delete its invented branch - the design stated no
policy and an implementation must not invent one. The design now states one."* Both halves fail. The
design stated one all along, so U6's deleted branch was contradicting §4.5 rather than filling a
vacuum - which is a better reason for deleting it than the one recorded. And *"the design now states
one"* described an edit that had never happened.

**There is therefore no gap here to close.** The design states a rule and the code follows it. A
ruling resting on a false reading of the frozen design is withdrawn rather than applied, and applying
it would have amended a frozen sentence that other ADRs and tests cite, on the authority of a premise
that does not survive reading that sentence.

**The underlying question is real and is NOT answered here.** Whether an exhaustive scan *should*
page at the raw transport cap - trading a caller's `max_results` against our wire page size - is a
genuine design question with a genuine cost behind it: 25 requests versus 3 for the worked example of
1,240 records. It needs **its own ADR, amending §4.5 explicitly**, argued on its merits rather than
carried in on the back of an application batch.

**What the composition question keeps.** Q1 was the answer this ADR's thesis leaned on hardest - the
Q3 section below once called it *"what makes Q3 payable"*. Q2 and Q3 do not depend on it: both are
about how the throttle is SCOPED and what the budget COUNTS, and both hold at whatever page size §4.5
settles on. The arithmetic Q1 was invoked to fix is now recorded in §4.4 as a composition the
throttle's implementer inherits and must either size for or raise as an ADR.

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

**Whether this answer is affordable depends on the page size, and Q1 is withdrawn, so the arithmetic
is an inherited constraint rather than a settled one.** At §4.5's
`min(transport_cap, configured_result_cap)` an exhaustive scan of the worked example spends 4m10s in
throttle waiting against a 60s budget - the failure mode this ADR predicts, *"a 503 that looks like
Jobvite being slow and is actually three of our own defaults disagreeing"*. **That does not un-answer
Q3.** A budget excluding the dominant term would not be a bound at any page size. What it does is
hand the throttle's implementer a composition to size for, which is what §4.4 now records. An earlier
revision of this section closed *"Q1 is what makes Q3 payable"*; Q1 is withdrawn, so that sentence is
removed rather than left pointing at it.

### What this ruling still does not settle, and deliberately

**None of the three constants.** 6/min is recorded in the design as a conservative guess and not a
vendor figure; 60s and the retry counts are U7's choices with nothing observed about Jobvite's
latency; 500 is unobserved as a server limit. This ADR was always about the composition, and the
composition is now decided for any values those rows eventually produce.

**The throttle is still unimplemented**, and §4.4 now says so IN THE DESIGN rather than only here, so
no reader takes that section as a description of what runs. The ADR's warning stands and is now more
pointed: implementing it before this composition landed would have turned a latent contradiction into
a live one. Whoever implements it implements Q2 and Q3 with it, not before them.

**One irony worth recording, because this ADR is partly about that exact shape.** ADR-0025 was raised
over a setting nothing reads, and its own remedy is a design paragraph about a mechanism nobody has
built. Two conditions keep that paragraph from becoming the thing it condemns: it states plainly that
the throttle is not implemented, and it reads as a constraint on the implementer rather than as a
description of behaviour. **It still wants a tripwire** - a test that fires when `outbound_rate_limit`
gains its first reader, so the paragraph is checked against code the moment there is code to check it
against, in the shape task #86 already used for `scan()`'s first caller. That test is NOT written
here; it is filed as its own task.
