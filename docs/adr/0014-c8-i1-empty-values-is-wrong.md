# ADR-0014: C8-I1 says `.env.example` has empty values; seven of fifteen carry one

**Status:** Accepted
**Type:** Design change

> **Accepted and APPLIED**, with ADR-0012 and ADR-0013 and five more, in one commit. The hold was
> operational: the implementation plan was repointing citations against the frozen `DESIGN.md`
> object, and landing a design change mid-repoint produced six wrong-subject citations once
> already.

## Context

`DESIGN.md:1760`, threat row **C8-I1**, rated **Critical**, states that `.env.example` is

> *"committed with empty values"*

**That is false against the committed tree.** Seven of fifteen variables carry a value:

```
.env.example:41  JOBVITE_ENABLE_WRITES=false
             :48  JOBVITE_MCP_TRANSPORT=stdio
             :53  JOBVITE_MCP_HOST=127.0.0.1
             :54  JOBVITE_MCP_PORT=8000
             :67  JOBVITE_TLS_TERMINATED_BY_PROXY=false
             :75  JOBVITE_MAX_RESULTS=50
             :82  JOBVITE_OUTBOUND_RATE_LIMIT=6
```

Every one is deliberate. Two of them — `JOBVITE_MAX_RESULTS` and `JOBVITE_OUTBOUND_RATE_LIMIT` — are
the B15 answer, named and defaulted specifically because leaving them unnamed made the template
incomplete by construction and blocked `config.py`.

**§8's own wording is correct** and says something different. At `:1222` the required case reads:

> *"`.gitignore` covers the credential patterns and `.env.example` **carries no real value**"*

*No real value* means no credential. *Empty values* means no value at all. C8-I1 tightened the first
into the second, and C8-I1 is the Critical row.

## Why this is not cosmetic

**The wrong wording is the one an implementer would satisfy.** An agent reading C8-I1 literally, and
finding seven populated variables, would empty them to make the Critical row true — deleting the B15
defaults and re-blocking the units that read them. The row would then be satisfied and the design
broken.

U0's test is already written against the **correct** property — the six secret-class variables are
declared and empty, non-secret defaults may carry a value — so that "fix" turns the suite red rather
than passing. That is control #1 in U0's harness, and it is the only thing standing between C8-I1's
literal text and a plausible, destructive correction.

## Decision

Amend C8-I1's evidence clause to match `:1222`:

> `.env.example` is committed with **every secret-class variable empty**

The six secret-class names are `JOBVITE_API_KEY`, `JOBVITE_API_SECRET`, `JOBVITE_FEED_KEY`,
`JOBVITE_FEED_SECRET`, `JOBVITE_COMPANY_ID`, `JOBVITE_HTTP_TOKENS`.

No rating changes. No disposition changes. C8-I1 stays Critical and stays mitigated; what changes is
the sentence describing the evidence, which currently describes evidence that does not exist.

## How it got here, because the pattern matters more than the row

This is **the fourth instance in one day of a fix going stale in its own sibling**, and the first
found by a test rather than by a reviewer.

A plan review found that `JOBVITE_MAX_RESULTS` had been named and shipped while three places still
called it undocumented. Those three were corrected. **§8's case was corrected. C8-I1 was not** — it
sat in the threat table, four hundred lines from the edit, saying something the edit had just made
false in the other direction.

The general form, now written into `feedback` memory and observed here for the fourth time: **after
changing a claim, the siblings to check are every other place that asserts something about the same
subject** — not every place with the same bug. In a document set that means the summary table, the
threat row, the conformance entry, the changelog and any test that names it.

## The related sibling that is NOT covered here

`.env.example:4` reads *"Every value here is EMPTY on purpose"*, thirty-seven lines above
`JOBVITE_ENABLE_WRITES=false`. Same defect, different artifact, and `.env.example` is a file this
ADR does not govern — it belongs to U1's scope in the implementation plan and is being fixed there,
rewritten in place rather than appended to.

It is named here so that whoever applies this ADR checks both, since the whole subject of this ADR
is a fix that reached one artifact and not its sibling.
