# ADR-0026: log redaction is a property of the entry point, and the client carries the credential

**Status:** Proposed
**Type:** Design change

> `httpx2` logs the whole `jobFeed` URL - `api`, `sc` and `companyId` - through the standard library
> logger. Our redaction is a filter that `__main__.configure_logging()` installs, so the shipped
> server is safe and **an embedder that constructs `JobviteClient` directly receives all three
> credentials in the clear.** MEASURED, not argued. The design says redaction is "enforced in one
> place"; the place it is enforced is not the place that holds the secret.

## Context

### Measured, and the probe is committed

`docs/reviews/probe-u12-f2-embedder-leak.py`, at `1b2af0c`, with `__main__` deliberately never
imported:

```
HTTP Request: GET https://api.jobvite.com/v1/jobFeed?api=PROBEAPIKEYVALUE&sc=PROBESECRETVALUE&companyId=PROBECOMPANYVALUE
Credential values in the clear: ['PROBEAPIKEYVALUE', 'PROBESECRETVALUE', 'PROBECOMPANYVALUE']
```

**The probe does not call `build_server`.** It constructs `JobviteClient`, which is the object that
holds the credential, and that is the finding's real scope: a fix installed in `build_server` would
leave this path exactly as measured.

### Why the current design is not simply wrong

`__main__.py:137` states the reasoning and it is good:

> Silencing `httpx2`'s logger would fix the producer we happened to find and leave every producer
> nobody has thought of. Redacting at the one sink covers all of them.

That is correct **for a process whose sink we own**. It cannot cover a process whose handlers belong
to someone else, and no amount of one-sink discipline changes that - there is no sink of ours in an
embedder's process at all.

### So the gap is structural, not an oversight

`DESIGN.md:315-318` requires the `jobFeed` URL to be redacted "before any log line", and
`utils/redaction.py` is named as the single enforcement point. **The enforcement point is a filter
on OUR handler.** The credential lives in `JobviteClient`. Those are different objects with
different lifetimes, and only one of them is guaranteed to exist.

## Decision

**§4.1 should say which entry points carry the redaction guarantee, and the answer must be
reachable by an embedder.** Three shapes, and the trade is real in every direction:

1. **`JobviteClient` installs a `logging.Filter` on the `httpx` logger.** Covers the measured path
   exactly. **A library mutating a host's global logging configuration from a constructor is a side
   effect an embedder is entitled to object to**, and this project would object to it in someone
   else's library.
2. **`build_server` installs the filter.** Smaller blast radius, and it is where U12 first suggested
   it - but it does not cover the probe above, which never calls it.
3. **A public, documented `install_log_redaction()` that `__main__` calls and an embedder must
   call.** No side effect, and it is **a documented obligation enforced by nobody** - the same shape
   as a setting nothing reads, a comment naming a variable that does not exist, and an ABSENT
   obligations row. This project has found all three this week.

**No option is free, which is why this is an ADR and not a patch.** (1) trades an embedder's control
of its own logging for a guarantee; (3) trades the guarantee for their control. (2) is the
comfortable middle that does not cover the measured case.

**My recommendation is (1) with an opt-out keyword**, defaulting to installing. A credential leak is
a worse default than a surprising side effect, and an embedder who wants their logging untouched can
say so in the constructor - which makes the exposure a choice they made rather than one they did not
know about. **The opt-out must not become a `Settings` field**: a setting nothing reads is exactly
what ADR-0025 is about, and this one would be read by a constructor argument instead.

## Consequences

### The probe must be inverted, not deleted

`probe-u12-f2-embedder-leak.py` currently **demonstrates the defect** and exits 0 when it leaks. It
is deliberately NOT wired, because gating on it would gate on the bug staying - the same call R6 made
about its own two probes. **When this ADR is decided, invert it into an assertion and wire it.**

### What this ADR does NOT claim

**Not that the shipped server is exposed.** `configure_logging()` runs at `__main__` module scope on
every shipped path, and U12's C5-I1 arm asserts the redaction fires there - including on httpx2's own
record, asserted PRESENT rather than merely absent.

**Not that this is U12's defect.** U12 found it while building a High's positive control, implemented
neither remedy because both files belonged to other agents, and said so. The gap predates it: the
same leak exists for `search_jobs`' v2 route in any embedder, minus the query-string credentials.

**Not that (3) is dishonest.** If the project decides an embedder owns its own logging, that is a
defensible position - but it must then be stated in the README's deployment section as a
**requirement**, not a note, and C5-I1's residual must record that the guarantee has a precondition.
