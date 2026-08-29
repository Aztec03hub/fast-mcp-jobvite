# ADR-0024: `DESIGN.md:486-487` bounds paging by the server's honesty and by nothing else

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Design change

> Paging terminates on a short page and never on `total`. That rule is right about `total` and
> **silent about non-advancement**: a server that ignores `start` and answers a full page every time
> is paged forever. The design removed one loop condition and supplied no replacement, and U6
> implemented it faithfully. This ADR proposes that §4.5 name a bound that does not read `total`.

## Context

### The clause, quoted at source

`git show c15b138:docs/DESIGN.md`, lines 486-487:

> Paging terminates on a short page (`len(items) < count`), never on `total`. `total` is reported
> and never trusted as a loop condition.

That sentence exists for a good reason and this ADR does not weaken it. `DESIGN.md:469-477` explains
it: `total` cannot be trusted, `eId` is opaque so a gap cannot be found by inspection, and a capped
call is a mismatch by design. **Terminating on `total` would page against a number the server may be
lying about.** Nothing below proposes going back to it.

### What the rule does not say

It names the condition paging must NOT use and does not name one it must. The implementation is
therefore correct and unbounded at the same time.

`src/fast_mcp_jobvite/services/jobvite_client.py:945-995` at `8d7af64`: the only exits from
`while True:` are a short page and the caller's cap. **No page ceiling, no request ceiling, no
zero-progress detector, no elapsed bound.**

### Measured, not argued

R5 ran an exhaustive scan against a fake that ignores `start` and answers a full page every time:

```
C) starting unbounded-loop probe against a server that ignores `start` ...
PROBE ABORT: 200 requests, loop is unbounded
```

**The abort is the reviewer's, at 200 requests. The client's own answer is "keep going."**

### The unit wrote the hazard down twice and did not treat it as one

`tests/test_pagination.py:346-348` says *"A loop that paged until it had `total` records would
request forever against a server that keeps answering"* - of the route the design already forbids.
The shipped loop does exactly that by a different route. `check-u6-paging-amputation.sh`'s header
declines to amputate the advance and the short-page break for the same reason: delete either and the
scan requests the same page forever. **The shape was understood as a property of the amputation
harness and not as a property of production.**

## Decision

**§4.5 should name a bound that does not read `total`.** (This ADR said §7.3, which is
*Configuration*. The sentence it quotes at `DESIGN.md:486-487` is in §4.5 *Pagination*, and that is
where the bound landed. Corrected in place.) Two mechanisms, and the recommendation is
both:

1. **A zero-progress break.** Track new records per page; a FULL page that adds nothing to `seen`
   and nothing to `unidentified` breaks and sets `incomplete = True`. This cannot fire on healthy
   paging - a full page that adds no records means the server is not advancing - and it is the one
   that actually terminates the loop rather than capping it.
2. **A page ceiling not derived from `total`.** A named `MAX_PAGES` beside `SCAN_START`; reaching it
   sets `incomplete` and logs. **This is not termination *on* `total`**, so 486-487 stays intact.

**Neither is a substitute for the other.** The zero-progress break catches a server that repeats;
the ceiling catches one that advances but never shortens.

## Consequences

### The outbound budget is a mitigation, not a fix, and this is the load-bearing point

`DESIGN.md:373-375` promises a total outbound budget. It would bound this **in wall-clock only** and
turn it into a typed 503. Three reasons that is not the answer:

- **It bounds a symptom by time.** The scan still makes every request it can afford, learns nothing,
  and reports a timeout rather than "the server is not advancing".
- **It did not exist when this was found**, at `8d7af64`, and is being built by U7 now (#43, #49).
- **Against the 6/min self-throttle of `DESIGN.md:425-427` the budget is consumed by a scan making no
  progress.** A budget written without knowing about this defect would be sized for a *slow* Jobvite
  rather than a *non-terminating* one, and those want different numbers.

U7 has been told this specifically, before sizing it.

### It interacts with the wire page size, so they are one decision

The page size an exhaustive scan uses is unresolved and deferred to U7 (task #48): today it is
`min(transport_cap, configured_result_cap)`, so a 1,240-record resource costs 25 requests -
**4 minutes 10 seconds at 6/min**. Whatever bound answers this ADR **must be sane at both 50 and 500
records per page**. A `MAX_PAGES` chosen against one page size is wrong for the other.

### What this ADR does NOT claim

**Not that the defect is reachable against real Jobvite.** It needs an endpoint that ignores `start`;
`/v1/jobFeed` is the candidate and no credential exists to test it. R5 recorded that as unsettled and
so does this.

**Not that anything is currently exposed.** `scan()` has **zero callers in `src/`** at `8d7af64` -
planned, since U8 and U12 key off it. Every consequence here is latent. That is a reason to fix it
before the first caller arrives, not a reason to defer.

**Not that U6 erred.** It implemented 486-487 faithfully. **This is a defect in the design at least
as much as in the code**, which is why it is an ADR and not a patch - and why R5 proposed it as one
rather than editing a frozen document.

## Ruling, 2026-08-29

**ACCEPTED. Both mechanisms, and the bound is in RECORDS rather than pages.**

The ADR proposes a `MAX_PAGES` and, two sections later, requires that any bound be *"sane at both 50
and 500 records per page"*. **Those two cannot both hold.** A ceiling in pages is a different record
count at each page size, which is precisely the objection the ADR raises against choosing one
against a single page size. The ceiling is therefore in records. The zero-progress break is
unchanged and is still not a substitute - it catches a server that repeats, the ceiling catches one
that advances but never shortens.

### Re-measured before ruling, at `40ce300`, because the ADR's own framing depends on it

The ADR argues the defect is latent because `scan()` has zero callers in `src/`. U8 and U12 - the
callers it named as planned - have both landed since, so that claim needed re-checking rather than
inheriting.

```
$ grep -rn "scan(" --include="*.py" src/ | grep -v "def scan" | grep -v scan_start
src/fast_mcp_jobvite/tools/jobs.py:321:   # because `scan()` has no caller in `src/` yet (U8/U12), and
src/fast_mcp_jobvite/tools/jobs.py:680:   # DELIBERATE. `client.scan()` exists and this tool
```

**Both hits are comments saying there is no caller.** Still zero, and the exhaustive path's only
loop exits remain a short page and the non-exhaustive caller cap. The defect is unfixed and still
latent - and both of its intended callers now exist, so the first real caller is the next unit that
wants one, not a distant prospect.

### An implementation already exists and is NOT adopted by this ruling

`rescue/adr-0024-scan-bound` carries 513 lines implementing exactly this shape - a record ceiling,
tests, a harness row, and `scripts/probe-scan-bounds.py`, which measures both failure directions
including the advancing-forever server R5's fake could not produce. Its recorded pre-fix numbers:

```
A1  budget 60s   requests issued: 2001   *** UNBOUNDED ***
A2  budget  2s   requests issued: 2001   *** UNBOUNDED ***
```

That is the direct evidence for this ADR's load-bearing claim that the outbound budget is a
mitigation and not a fix - the claim R5 could not test, because the budget did not exist at
`8d7af64` where R5 looked.

**It was written by an agent that never reported it, found uncommitted in a worktree during a
cleanup, and nobody has reviewed a line of it.** Accepting this ADR does not accept that branch. It
needs a full review round and its numbers re-measured on current `main` before any of it lands.

### What this ruling does not settle

Whether the defect is reachable against real Jobvite. It needs an endpoint that ignores `start`;
`/v1/jobFeed` is the candidate and no credential exists to test it. R5 recorded that as unsettled,
the ADR repeated it, and it is still unsettled. **The bound is being adopted because the client must
terminate against a server that misbehaves, not because this server is known to.**
