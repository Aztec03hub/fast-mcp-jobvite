# Architecture Decision Records

An ADR here does **two different jobs**, and they must stay distinguishable:

1. **`Deviation`** - records a decision that departs from a `priority: required` standard, or that a
   reviewer would otherwise be right to file as a defect. **This is independent of the freeze.** A
   deviation is recorded when it is decided; that is why the ADRs exist against a design that is
   not yet frozen, which is correct rather than contradictory.
2. **`Design change`** - after the freeze, an ADR is the only instrument that may change
   `docs/DESIGN.md`. This job begins at the freeze and not before.

**Every ADR carries a `Type:` field** - `Deviation`, `Design change`, or `Both` - because after the
freeze "is this a deviation or a design change?" must have an answer, and the freeze rule's teeth
depend on telling them apart. `DESIGN.md` §13 states the same split.

The convention began at 0012, and **0001 to 0011 were backfilled** as `Deviation` - which is what
this paragraph had already asserted collectively, and each file now says for itself. Round 2 of the
code review found the gap: the two ADRs in its scope, 0010 and 0011, are deviations that sat in the
unlabelled half, and **once a convention exists, the ABSENCE of the field reads as "not a
deviation"** rather than as "written before the field did". A classification that lives only in the
index is not carried by the artifact a reader opens.

Format: Status, Type, Context, Decision, Consequences. Every ADR cites the clause it deviates from
at its `file:line`, and says what evidence the decision rests on.

## An ADR's citations are AS AT its acceptance, and are NOT repointed

**MEASURED, all 64 `DESIGN.md:N` citations in this directory read one at a time
(`docs/reviews/CITATION-READ-ADR-VERDICTS.md`): 46 DRIFTED, 14 CORRECT, 2 WRONG, 2 boundary.**
Seventy-two per cent point at text that WAS the cited subject when written and is not any more,
because `DESIGN.md` moved under them.

**They stay.** An ADR is a DECISION RECORD: it states what was decided against the design as it
stood. Repointing its citations rewrites the evidence for a decision already taken and makes every
ADR silently claim to be about today's design. #111 ruled the same shape for `docs/plans` and the
reasoning carries.

**THE CASE THAT MAKES THIS NON-OBVIOUS IS IN THIS DIRECTORY.** `ADR-0034` cites `DESIGN.md:2063`
for the words *"all eleven ADRs"*. At `e3b5c97^` line 2063 reads exactly that - and `e3b5c97` is
the commit that APPLIED ADR-0034 and deleted the count. **The ADR's own accepted change falsified
its own citation**, and the re-freeze made the stale reading official. That is drift arriving in
one commit, from the decision itself, and no reader looking only at today's freeze can tell it
apart from carelessness.

**HOW TO READ A CITATION THAT DOES NOT MATCH.** Date the citation, then read the design as it was:

    git log -S'DESIGN.md:2063' --reverse -- docs/adr/0034-*.md   # when the citation was written
    git show <that sha>^:docs/DESIGN.md | sed -n '2063p'         # what it said then

**`git blame` IS THE WRONG INSTRUMENT and gives a confidently wrong answer.** It returns the last
commit to TOUCH the line, which for prose is a later rewrite - it dated ADR-0019's citations three
days after they were written, to a `DESIGN.md` the author never saw.

**NO SHA IS WRITTEN INTO THE ADRs.** A per-file "citations are against `<sha>`" line is a retyped
datum in 19 files, and this project has spent a night on what retyped data do. The acceptance
commit is already recoverable from git, which is where provenance belongs.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-target-fastmcp-4-beta.md) | Target `fastmcp 4.0.0b4` and the sessionless spec, not the stable line | Accepted |
| [0002](0002-in-process-rate-limiting.md) | In-process rate limiting instead of the mandated Redis token bucket | Accepted |
| [0003](0003-problem-json-on-mcp-transport.md) | `problem+json` cannot be set on an MCP tool error | Accepted |
| [0004](0004-exclude-response-limiting-middleware.md) | `ResponseLimitingMiddleware` excluded; size bounded in-tool | Accepted |
| [0005](0005-ai-domain-binds-by-intent.md) | The `ai/` standards domain binds this repository by intent | Accepted |
| [0006](0006-single-main-branch.md) | Single `main` branch rather than the mandated `main`+`develop` | Accepted |
| [0007](0007-httpx2-not-httpx.md) | `httpx2` rather than `httpx` | Accepted |
| [0008](0008-eeo-fields-excluded.md) | Special-category EEO fields excluded from output models | Accepted |
| [0009](0009-approver-identity-unknowable.md) | Approver identity cannot be recorded; caller identity can | Accepted |
| [0010](0010-coverage-targets-remapped.md) | Coverage targets remapped from the standard's category model | Accepted |
| [0011](0011-three-log-producers-not-one.md) | Three log producers per invocation, not the mandated one | Accepted |
| [0012](0012-shared-inbound-constraints-module.md) | A shared `utils/constraints.py` for the inbound constraints | Accepted |
| [0013](0013-secret-absence-case-needs-a-pairing.md) | §8's secret-absence case needs a positive pairing, as the audit cases have | Accepted |
| [0014](0014-c8-i1-empty-values-is-wrong.md) | C8-I1 says `.env.example` has empty values; seven of fifteen carry one | Accepted |
| [0015](0015-licence-gate-is-a-deny-list.md) | The licence gate is a deny-list; four packages sit on neither list | Accepted |
| [0016](0016-setup-uv-v5-not-the-standards-v4.md) | `astral-sh/setup-uv@v5`, where the standard pins `@v4` | Accepted |
| [0017](0017-unmapped-errors-are-internal-error-not-about-blank.md) | The unmapped row is `/problems/internal-error`, not `about:blank` | Accepted |
| [0018](0018-forced-exit-masks-a-crash-as-a-clean-stop.md) | `os._exit(status)`, not `os._exit(0)`, so a crash is not reported as a clean stop | Accepted |
| [0019](0019-design-603-cites-a-section-that-does-not-exist.md) | `DESIGN.md`'s one `§5.4` becomes `§4.1`; there is no §5.4 | Accepted |
| [0020](0020-the-30-day-advisory-budget-runs-from-the-recorded-date.md) | The 30-day advisory budget runs from the recorded date, not from now | Accepted |
| [0021](0021-approval-mechanism-is-required-by-two-rows-and-defined-nowhere.md) | `approval_mechanism` defined in §5.3, closed to three values | Accepted |
| [0022](0022-no-cookie-jar-is-a-disable-not-an-omission.md) | "Do not implement a cookie jar" is a DISABLE, not an omission | Accepted |
| [0023](0023-harnesses-drop-e-from-strict-mode.md) | The `scripts/` harnesses run `set -uo pipefail`; `-e` would destroy the measurement and strand mutations | Proposed |

## Acknowledged non-conformances without an ADR

One obligation is knowingly unmet and deliberately has no ADR, because an ADR would imply a
decision we are not entitled to make:

- **`threat-modeling.md:146`** requires mitigations to become numbered functional requirements.
  The corpus contradicts itself about the ticket prefix - `agentic-coding-standard.md` expects
  `FEAT/FR/BUG/TECH`, `quality-gates.md` adds `TECH`, `development-workflow.md:166` expects
  layer-prefixed `[FE-001]`, and this work is tracked as `EC-###`. **Inventing a prefix to satisfy
  a clause the standards cannot agree on would move the defect rather than fix it.** Recorded here
  so it is visible rather than skipped.

