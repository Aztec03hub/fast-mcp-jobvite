# ADR-0010: Coverage targets remapped from the standard's category model

**Status:** Accepted

## Context

`backend/testing.md:583-589` sets per-category coverage targets - Services 90%, API Routes 85%,
Utilities 95%, Models 70% - against a layered FastAPI application. **An MCP tool module is none of
those categories.** The 80% overall floor is unambiguous and is met; the sub-targets require a
judgement call.

## Decision

Tool modules 85%, the Jobvite client 90%, critical paths 95% line and 90% branch, against the 80%
floor.

## Consequences

Loosening a mandated coverage number is exactly what the ADR mechanism exists to record, which is
why this exists rather than being applied silently.

**The first version of this mapping inverted the risk** and the correction is the useful part: the
standard sets Utilities at **95%**, the highest of any category. `utils/redaction.py` holds secret
redaction **and** untrusted-content fencing - two of the design's own required test cases, both
rated Critical in the threat model - and the original remap left it at the 80% floor while giving
the client 90%. **Utilities keep the standard's 95%.**

