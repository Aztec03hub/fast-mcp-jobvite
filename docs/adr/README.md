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

**MEASURED, all 64 `DESIGN.md:N` citations carried by the ADRs THEMSELVES - `docs/adr/0*.md`, 19 of
the 35 numbered files - read one at a time (`docs/reviews/CITATION-READ-ADR-VERDICTS.md`):
46 DRIFTED, 14 CORRECT, 2 WRONG, 2 boundary.** Seventy-two per cent point at text that WAS the
cited subject when written and is not any more, because `DESIGN.md` moved under them.

    grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/0*.md | wc -l    # 64, the population read
    grep -rhoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' docs/adr/*.md  | wc -l    # more: this README quotes

**NAMING THAT BOUNDARY IS NOT PEDANTRY: THE COMMIT THAT FIRST WROTE THE SENTENCE ABOVE FALSIFIED
IT.** It said *"all 64 in this directory"*, and ruling on four citations meant quoting them, so the
bare directory grep returned 68 and the paragraph was wrong about itself on arrival - **the
ADR-0034 shape eight lines below, in the same commit as the claim.** The rewrite you are reading
quoted three more while explaining it. **So no total for `docs/adr/*.md` is written here**: it
moves whenever this file discusses a citation, which is the ADR-0034 remedy - a count that cannot
be maintained is DELETED, not corrected. What the extras have in common is that they are
QUOTATIONS, not citations - the class `check-brief-report-references.py`'s docstring rules on, one
corpus over - and no selector here can tell the two apart, which is why the population that was
read is named by PATH above rather than left to one.

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

**THE WORKED CASE, AND IT IS THE EMPIRICAL ARGUMENT FOR THIS RULE.** `ADR-0017` cites ONE range
twice - qualified at `:16`, bare at `:67`. `b0e86b8` ("Repoint 713 DESIGN.md citations") moved the
qualified half `489-490 -> 495-496` and could not see the bare half, because its selector requires
the filename. Measured across three trees:

    at acceptance 02245b1   :489-490  IS the seven-member problem object   BOTH halves correct
    at b0e86b8              :495-496  IS that sentence                     the repoint was right
    at the freeze d1f1a52   the sentence is at :546-547                    the repoint is now wrong

**THE HALF THAT WAS NEVER TOUCHED IS THE ONE THAT STILL MEANS WHAT ITS AUTHOR WROTE.** The
repointed half was correct for exactly as long as it took `DESIGN.md` to move again, and it left
the document contradicting itself in the meantime. `:16` is restored to `489-490`: the ADR agrees
with itself again and is back to the record it was.

**SO THE REPOINT TOOL MUST NOT LEARN THE BARE FORM.** That was proposed as "the only fix that stops
the class recurring", and it is the wrong direction - it would let a sweep move BOTH halves and
produce a consistent document that is still wrong at the next re-freeze, twice as thoroughly. **The
fix is for the repoint tool to stop touching `docs/adr/` at all**, which this rule already implies
and which no selector needs to learn.

**HOW TO READ A CITATION THAT DOES NOT MATCH.** Date the citation, then read the design as it was:

    git log -S'DESIGN.md:2063' --reverse -- docs/adr/0034-*.md   # when the citation was written
    git show <that sha>^:docs/DESIGN.md | sed -n '2063p'         # what it said then

**`git blame` IS THE WRONG INSTRUMENT and gives a confidently wrong answer.** It returns the last
commit to TOUCH the line, which for prose is a later rewrite - it dated ADR-0019's citations three
days after they were written, to a `DESIGN.md` the author never saw.

**NO SHA IS RETROFITTED INTO THE EXISTING ADRs**, and the reason is measured rather than argued.

Five ADRs already name a `DESIGN.md` blob with `git show <sha>:docs/DESIGN.md` - 0019, 0024, 0025,
0030, 0031 - and **in every one of them, line-numbered citations elsewhere in the same file drifted
anyway.**

    grep -lE 'git show [0-9a-f]{7}:docs/DESIGN\.md' docs/adr/00*.md | wc -l    # 5

**THOSE FIVE LINES ARE NOT ONE FORM, AND CALLING THEM ONE WAS THE ERROR.** Read one at a time, only
`ADR-0019:18` declares a SCOPE - *"Verified against the frozen object `git show
135c3ac:docs/DESIGN.md`"*. The other four INTRODUCE ONE QUOTATION each - *"`git show
c15b138:docs/DESIGN.md`, lines 486-487:"* - and bind that quotation and nothing else. A sentence
calling all five *"a citations-are-against-`<sha>` line"* describes one of them.

**WHAT ALL FIVE DO SHOW, PER FILE**, is that a blob named anywhere in an ADR does not bind the line
numbers elsewhere in it (`docs/reviews/CITATION-READ-ADR-VERDICTS.md`, the DRIFTED table):

    0019   4 bare `DESIGN.md:603`                                    all 4 DRIFTED
    0024   5 bare `DESIGN.md:N`                                      all 5 DRIFTED
    0025   3 bare `DESIGN.md:373-375`                                all 3 DRIFTED
    0031   3 bare `DESIGN.md:N`                                      all 3 DRIFTED
    0030   `:356-359` and `:361-362`, THREE LINES BELOW the sha, filename omitted
           both exact at `c15b138`, both DRIFTED at the freeze `d1f1a52`

**`ADR-0030` IS THE TIGHTEST CASE IN THE SET AND EVERY SELECTOR RUN HERE WAS BLIND TO IT.** Its two
citations omit the filename, so `grep -E 'DESIGN\.md:[0-9]+'` returns zero for that file and it
reads as carrying no citation at all - a review round concluded exactly that. It carries two, three
lines under the sha, and both drifted:

    git show c15b138:docs/DESIGN.md | sed -n '356,359p'   # the open-breaker/outage 503, as cited
    git show d1f1a52:docs/DESIGN.md | sed -n '356,359p'   # "Ordered timeout, then retry, then breaker"

**Proximity is the strongest binding short of naming the blob inline, and it still failed.**

(The count was five only on the second attempt. The first selector asked for "an ADR mentioning a
seven-hex sha near the words `git show`", which also matched ADRs recording where a fix LANDED, and
returned twelve; the discriminator is naming a `DESIGN.md` BLOB, not naming a commit. **The second
selector was loose too, one column over.** It counts blob-naming LINES, and this section is about a
FORM - which is how four quote-introducers were read as scope declarations, and how `0030`'s bare
citations were read as an absence. Every one of these was caught the same way: two independently
derived numbers disagreed, and nothing else looked.)

**`ADR-0019` IS THE PROOF THAT A SCOPE DECLARATION DOES NOT BIND EITHER.** `:18` names the frozen
object outright, and all four of its `DESIGN.md:603` citations drifted anyway. **The ADR that best
documented its own reference point is the one with four drifted citations in it.** Each
`DESIGN.md:603` still resolves on its own against the current freeze, and a reader who lands on one
never sees the paragraph.

**THE FORM THAT BINDS PUTS THE SHA INSIDE THE CITATION**, and that exists too. `ADR-0025:117`:

> `git show 8a9d63c:docs/DESIGN.md`, §4.5, lines 453-455 **of that blob**

There is no number there that can drift, because the blob is named and immutable - **and it binds
that quotation only.** The same file's three `DESIGN.md:373-375` citations sit outside it and all
three drifted. That is not a contradiction with the row above; it is the scope of the form, stated
exactly.

**SO: NEW ADRs SHOULD CITE THE BINDING FORM. Existing ones are not rewritten.** Retrofitting is a
sweep over a record set, which is the thing this whole section refuses; and adding the NEAR form
would deploy, for the thirteenth time, a convention already measured not to work.

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
| [0024](0024-paging-is-bounded-by-the-servers-honesty-and-nothing-else.md) | Paging is bounded by the server's honesty and by nothing else | Accepted |
| [0025](0025-page-size-budget-and-throttle-are-one-decision.md) | The page size, the outbound budget and the self-throttle are one decision | Accepted |
| [0026](0026-log-redaction-is-a-property-of-the-entry-point-not-the-client.md) | Log redaction belongs to the entry point; the client carries the credential | Accepted |
| [0027](0027-the-budget-must-be-configured-and-the-variable-set-is-closed.md) | The budget must be configurable, and the closed variable set had no seat for it | Accepted |
| [0028](0028-approval-mechanism-names-a-path-this-design-does-not-use.md) | `approval_mechanism`'s closed set names `sampling`, a path this design has not got | Accepted |
| [0029](0029-the-body-size-limit-has-no-middleware-to-live-in.md) | §2.1's 1 MiB body limit is placed at a middleware this design does not have | Accepted in part |
| [0030](0030-the-upstreams-retry-hint-is-dropped-on-every-shape-but-two.md) | The upstream's retry hint is passed on wherever we were given one | Accepted |
| [0031](0031-the-registry-has-no-row-for-a-refused-approval.md) | The registry has no row for a refused approval; add the row, mint no slug | Accepted |
| [0032](0032-a-fifth-middleware-runs-that-the-design-never-assessed.md) | A fifth middleware runs that the design never assessed | Accepted |
| [0033](0033-approval-state-is-a-published-vocabulary.md) | `approval_state`'s four values are a published vocabulary, so the design names them | Accepted |
| [0034](0034-the-adr-count-in-design-md-is-deleted-not-corrected.md) | `DESIGN.md`'s ADR count is DELETED, not corrected, and "all" was the worse half | Accepted |
| [0035](0035-the-frozen-selector-must-admit-both.md) | The frozen selector must admit `Both`, and the "0012 onward" boundary is deleted | Accepted |

## Acknowledged non-conformances without an ADR

One obligation is knowingly unmet and deliberately has no ADR, because an ADR would imply a
decision we are not entitled to make:

- **`threat-modeling.md:146`** requires mitigations to become numbered functional requirements.
  The corpus contradicts itself about the ticket prefix - `agentic-coding-standard.md` expects
  `FEAT/FR/BUG/TECH`, `quality-gates.md` adds `TECH`, `development-workflow.md:166` expects
  layer-prefixed `[FE-001]`, and this work is tracked as `EC-###`. **Inventing a prefix to satisfy
  a clause the standards cannot agree on would move the defect rather than fix it.** Recorded here
  so it is visible rather than skipped.

