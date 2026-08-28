# DESIGN.md - Round 7 targeted confirmation pass (§5.3 and §11)

Reviewer: `design-confirm-r7`, fresh - wrote none of this.
Date: 2026-08-28 01:41 PM CDT.
Pinned at `bc1ef49760c607399d394d09963def9176ed64da`.

**Scope**, per the brief: §5.3 and §11 only, §8 for the cases those two sections name, and
§3 / §4.3 / §7.2 / §7.7 / §10 / §12 only where §5.3 or §11 point at them. This is a confirmation
pass over the two sections every round-6 fix touched, not a re-review.

---

## VERDICT: **DO NOT FREEZE**

Tally: **0 CRITICAL / 0 HIGH / 1 MEDIUM / 5 LOW / 2 NIT.**

The freeze rule is 0C/0H/0M from a review round **and** §11's must-mitigate table empty. **The second
condition holds; the first does not.**

- **The must-mitigate table is empty and stays empty.** `DESIGN.md:1646` carries a single `*(none)*`
  placeholder, `check-coupling.py` independently reports every unmitigated Critical/High row disposed
  of, and C4-S1 is the only unmitigated one. I examined whether C5-E1 must drop back to unmitigated
  and concluded it must not - reasoning in M-1 below. That conclusion is mine, reached against the
  evidence, and I would have said the opposite if the evidence had gone the other way.
- **One Medium stands: M-1**, §7.2 asserting in the present tense that a file which does not exist
  already states C5-E1's mitigation.

M-1 is a four-line prose fix. **Apply it and this design freezes** - I am not asking for another
round, and the L and N findings do not gate anything. But the rule as written is 0C/0H/0M, the
defect sits in the evidence chain of an inherent-High row inside text about to become
ADR-only-changeable, and I am not going to call it a Low to clear a gate.

**Update after the pass closed - three Mediums total, two now closed.** Findings referred to me after
this report was first written:

| # | Finding | State |
|---|---|---|
| **M-1** | §7.2 asserted a README that does not exist as C5-E1's mitigation | **Applied `f5c63e7`**, gates green |
| **M-2** | "No ambient authority" (`agent-guardrails.md:54-56`, `tool-calling.md:108-111`) disposed nowhere | **Applied `90b0504`** as §7.2:763-792 + B107, gates green. I verified the paragraph: it carries the expiry trigger and states single-tenancy as a property of our deployment model rather than of Jobvite, which is what I asked for |
| **M-3** | The caller-replay clause (`resilience.md:146-151`) names a remedy nobody evaluated | **OPEN.** B108 is written in the corpus; `DESIGN.md` still does not dispose of it |

**M-3 is the only thing between this document and a freeze.** Verdict stays **DO NOT FREEZE**.
Running tally: **0C / 0H / 3M (two applied, one open) / 5L / 2N.**

### Status of these findings at the time of writing

While this report was being written the team lead applied **L-1 through L-5, N-1 and N-2** to the
working tree (uncommitted at `ce1017a`). I re-read each edit against the finding it answers and all
seven are faithful, including the two I was least sure would survive rewording: L-1's replacement
names both disputed totals (seven and nine) and forbids deriving one from the ledger, and L-4's
replacement states the *unmitigated* distinction explicitly instead of leaving it implicit.

**I re-ran all three gates against the edited working tree: exit 0, 0, 0, with 60 STRIDE rows,
17 Critical/High, 16 mitigated and 23 naming a §8 case - identical to the pre-edit run.** The prose
fixes moved no row and changed no rating.

**M-1 is the one finding not yet applied**, and it is the one the freeze rule turns on.

---

## A note on the tree moving under the pass

The brief pinned HEAD at `d144247`. Mid-review, at 13:36 CDT, commit `bc1ef49` ("Assert
`request_id` on the wire result, not on the `ToolResult` object") landed on `main` and shifted
§11 by 11 lines. I re-based every citation and **re-ran all three gates against `bc1ef49`**; the
findings below are against that SHA. `bc1ef49`'s new §5.3 paragraph is included in this pass and is
verified clean (see below). Flagging it because a confirmation pass whose subject changes while it
runs is exactly how a stale citation gets published.

---

## Gates - re-run by me, from the repo root, at `bc1ef49`

Not taken on trust; run and read by exit code, not by the last line of output.

| Gate | Exit | Result |
|---|---|---|
| `python3 docs/reviews/check-coupling.py` | **0** | 60 STRIDE rows, 17 Critical/High (16 mitigated, 1 not); 49 rated rows agree with the matrix, 11 fully unrated; all 60 dispose of themselves; 23 name a §8 case |
| `python3 docs/reviews/check-coupling-controls.py` | **0** | **29/29 controls fired**; post-run re-check of the real `DESIGN.md` still green |
| `python3 docs/reviews/check-coupling-sweep.py` | **0** | 184 substitutions; 7 escapes, all the designed Medium/Low exemption; **0 holes** |

---

## What I verified at source and found correct

These are the load-bearing claims the round-6 fixes introduced. I checked each against the pinned
stack rather than against the document's own account of it.

**M-2 (`request_id` in `_meta`, not on the output model).** Confirmed at
`mcp/client/session.py:1108-1109` - every non-error `CallToolResult` goes through
`validate_tool_result` - and `:1131-1145`, which refreshes the schema cache by calling
`list_tools()` if it has to and then validates whenever the tool has an output schema. There is no
opt-out and no flag. With `additionalProperties: false` an undeclared top-level `request_id` raises.
§5.3's word "unconditionally" is accurate for this project's tools. The skip at `:1108`
(`not result.is_error`) does not weaken the argument, because §5.3 routes the error half through
the problem object's own `request_id`.

**`bc1ef49`'s new paragraph, and whether it contradicts the paragraph nine lines below it.** It does
not. `fastmcp/tools/base.py:168` stashes `_raw_mcp_result` in `from_mcp_result`; `:176-177`
short-circuits on it at the top of `to_mcp_result()`; `:181` is a *separate, later* branch on
`if self.meta is not None or self.is_error`. §5.3:578-586 describes the first, §5.3:590-593 the
second, and both are true of the same function.

**M-3 (trace context), all five citations, exact.**
- `mcp/shared/jsonrpc_dispatcher.py:389-390` - the SEP-414 inject, and `:389` is verbatim the
  comment §5.3 paraphrases about `_meta` staying on the wire with a no-op tracer.
- `opentelemetry-api>=1.28.0` is a hard `Requires-Dist` at `mcp-2.1.1.dist-info/METADATA:29`, so
  §5.3 is right that nothing new joins §10's pins.
- `fastmcp/server/telemetry.py:95` extracts from `req_ctx.meta` server-side.
- `fastmcp/telemetry.py:263` is `extract_trace_context`, exported at `:308`.
- The caveat is real and precise: `fastmcp/telemetry.py:277-278` is exactly the
  `telemetry_mode() == "off"` early return that hands back the ambient context, which is why §5.3
  reads `ctx.request_context.meta` directly instead.

**L-1.** `utils/correlation.py` is in §3's tree at `:246`, described as the correlation ContextVar.

**Do the §8 cases test what the §11 rows claim?** The six rows in scope name cases that exist, and
each case's §8 body matches the row rather than only its name:

| Row | Test cell | §8 body checked |
|---|---|---|
| C1-R1 | audit event emitted with mandated fields | `:1117-1122` - includes the resolved client id on HTTP and an explicit attribution-unavailable marker on stdio, matching §5.3:630-635 |
| C2-R1 | same case | `:1120-1122` - deliberately positive, paired against the PII absence case so neither passes on silence |
| C4-R1 | same case | `:1119` - `approval_state` **and the mechanism that produced it** |
| C5-R1 | retry/breaker lines carry `request_id`, under concurrency | `:1160-1165` - two parallel invocations, each forced to retry, each line matched to its invocation; the single-call arm explicitly ruled insufficient |
| C7-I1 | candidate PII never in a log or audit record | `:1132-1135` - asserted against the audit event the case above proves exists, not an empty stream |
| C5-E1 | read-only-key requirement present in README and checklist | `:1166-1170` |

**C5-E1 is the known-weak one, and the two halves agree.** §8:1168-1170 says outright that the case
tests only that the instruction exists and is discoverable, "which is **all that is testable**",
and that a stronger assertion would misrepresent the design. §11:1714 rates the exposure **High,
unreduced**, with "**No server-side remedy exists.**" §11:1688-1691 states the distinction directly:
what closed is the obligation to state and test the requirement, not the underlying exposure. That
is the honest pairing, and it is the one M-1 was supposed to produce.

**Is the removal ledger honest?** Yes, and this is the answer I most expected to go the other way.
The claim at `:1669-1672` that the original total is not reconstructible **holds**, though not for
the reason the document gives. Two reconstructions exist and they disagree:
- The retired prose (`86f87ca:docs/DESIGN.md:1005`, "**Down from seven to five**") asserts **seven**,
  and its own arithmetic is the broken one H-1 removed - four removals from seven concluding five.
- The current ledger at `:1661-1667` names **nine** removed rows (3 + 1 + 2 + 1 + 2) above a table
  that is now empty, which implies **nine**.

Neither number can be trusted over the other, so no total is reconstructible. The claim is true.
The *wording* is the problem, and that is finding L-1 below.

**No new numeric total** was introduced into §11's threshold-disposition section by these edits,
beyond the wording issues at L-1 and L-2 below.

---

## Findings

Every suggested fix below is **my suggestion, to be verified before adoption**, not an instruction.

### M-1 - §7.2 states, in the present tense, that a file which does not exist already carries C5-E1's mitigation

`DESIGN.md:771-772`, `:1157-1161`, `:1354-1358`, `:1581`.

**Provenance, stated because it matters to how this was checked.** The team lead found this in his
own edit and handed it to me as an observation with an explicit instruction to verify it
independently and to reach the inconvenient conclusion if the evidence supported it. I verified it
from the repository rather than from his description, and I reached a *different* conclusion than
his hypothesis on the part that decides the freeze. Both halves are below.

**The defect, confirmed.** `ls` of the repository root: `.env.example`, `.github`, `.gitignore`,
`CHANGELOG.md`, `LICENSE`, `NOTICE`, `SECURITY.md`, `changelog.d`, `docs`, `src`, `tests`. **There is
no `README.md`.** `git ls-files | grep -i readme` returns only `changelog.d/README.md` and
`docs/adr/README.md`. `find src tests -type f` returns **0 files**. Against that tree:

- §7.2:771-772 - "**Operator requirement: where writes are disabled, the Jobvite key must be a
  read-only key.** This **is stated in the README's deployment section** and in
  `docs/CREDENTIAL-CHECKLIST.md`". Present tense, about a named section of a file that does not exist.
- §10.1:1354-1358 - "**The README is not written yet, deliberately**", because "A README describing
  an unbuilt system is a false claim in the present tense."
- §11:1581 marks C5-E1 **Mitigated**, and §11:1699 names §7.2's read-only-key requirement as what
  closed it.

So the design deliberately defers the README in §10.1 and then, 580 lines earlier, asserts its
contents as established fact - and that assertion is load-bearing for an inherent-High row's
mitigation status. §8:1157-1161 compounds it by specifying a case "asserted against the committed
files", which cannot pass against half its subject. Its sibling case at §8:1113-1116 uses the same
phrase and *can* pass, which is precisely why C8-I1 was closed (`:1666`); C5-E1 was closed on the
same shape of evidence with half of it absent.

**What did not catch it, which is the part worth carrying forward.** `check-coupling.py` verifies
that a row names a §8 case **present in the document**. It has no visibility into whether the
artifact that case asserts against exists on disk. This is M-1-from-round-6's class one layer down:
not a row rated generously, but a row whose evidence cannot be produced. I endorse tracking that gate
limitation separately; it is not fixable in this document.

**Where I disagree with the hypothesis I was handed: C5-E1 should NOT drop back to unmitigated, and
the must-mitigate table stays empty.** Three reasons, in order of weight:

1. **The mitigation's substance is present today for its entire current audience.** The mitigation is
   "the operator instruction exists and is discoverable". `docs/CREDENTIAL-CHECKLIST.md:39-45` now
   carries **row 0** - ask Jobvite whether a read-only key exists and request one for every
   writes-disabled deployment, recording the answer either way - and that file is committed; I
   confirmed both the content and that `git status` shows it clean. The checklist is the document the
   first key request actually passes through, which is the only moment before implementation at which
   this instruction can be acted on at all. The README's audience is a deployer, and there is nothing
   to deploy.
2. **§7.2's stated ceiling is untouched.** `:779-783` already says whether Jobvite issues read-only
   keys at all is unknown, and that if the answer is no "this requirement is unsatisfiable and the
   residual risk stands". §11:1714 rates the exposure **High and unreduced** in Residual Risks. The
   honest accounting M-1-of-round-6 asked for is intact; nothing here inflates what the mitigation
   achieves.
3. **Reopening the row would misdescribe the defect.** What is wrong is a tense in two sentences, not
   the existence of the control. Marking C5-E1 unmitigated would put a row back on the must-mitigate
   table whose action item is "write a README for software that does not exist" - which is the exact
   fabrication §10.1 refuses. The fix belongs in the sentences.

**I checked the siblings before concluding the tense is isolated** (four other README references:
`:374`, `:755-756`, `:990`, `:1332`, plus §5.3:588). `:588` - "The README **must** document the key" -
is correctly forward-looking, and `:755-756`, `:990` and `:1332` are obligations or labels rather
than claims of present fact. `:374` ("the README states the envelope") is the same idiom but nothing
rests on it. **§7.2:772 is the only one that asserts existing README content AND carries a
Critical/High row's mitigation status.** That is what makes it a Medium and the others not findings.

**Suggested fix (mine, verify before adopting) - cheap, two sentences, no structural change.**

§7.2:771-772:

> **Operator requirement: where writes are disabled, the Jobvite key must be a read-only key.** This
> is stated today in `docs/CREDENTIAL-CHECKLIST.md`, whose row 0 records the question to Jobvite and
> its answer either way, and **the README must carry it in the deployment section when the
> implementation produces one** (§10.1). It is **an instruction to a human, not a control this server
> can enforce**, for two reasons that should not be blurred together:

§8:1157-1161, so the case is runnable against the tree it will first run on:

> - **the read-only-key requirement is present in `CREDENTIAL-CHECKLIST.md`, and in the README's
>   deployment section once a README exists** - asserted against the committed files, with the README
>   arm gated on its presence rather than skipped (a skip is a green that tested nothing). This tests
>   that the instruction exists and is discoverable, which is **all that is testable** - ...

If that fix is applied, my verdict is **FREEZE**, with no further round needed.

### M-2 - "No ambient authority" is required by two binding standards and disposed nowhere

`ai/agent-guardrails.md:54-56`, `ai/tool-calling.md:108-111`; `DESIGN.md:747-761`; `ADR-0005:22`.

Referred to me after this report was first written. Verified independently, from the standards and
the repository, not from the referral.

**The clauses exist verbatim.** `agent-guardrails.md:54-56` - *"**No ambient authority.** A tool must
not act on behalf of an arbitrary user. Pass the caller's identity/tenant explicitly and enforce
authorization inside the tool"*. `tool-calling.md:108-111` - *"Tools **re-validate authorization
independently** of the model: enforce the authenticated caller's tenant / row-level access inside the
tool, off the request principal, never off a value the model supplied."*

**They are cited nowhere.** Two independent search forms, plus a positive control, because an absence
is only a claim about where I looked:
- Line-range search for `guardrails.md:5[4-6]` and `tool-calling.md:10[89]|11[01]` across the repo:
  hits only in `docs/reviews/CITATION-RANGE-AUDIT.md`, the report that raised this.
- Phrase search for *ambient authority*, *row-level*, *request principal*, *re-validate
  authorization*: same, only that report.
- **Positive control:** `guardrails.md:79` resolves in 5 files under `docs/`, so the instrument does
  find guardrails citations when they are there.
- `docs/research/STANDARDS.md:211` cites `:50-53` and `:157` cites `:57-58` - **the bullets
  immediately either side of `:54-56`**. The corpus stepped over it.

**No ADR reaches it.** `ADR-0005:22` grants "Obligations **B9-B26** apply in full" - a B-number grant,
and this clause carries no B-number. ADR-0009 is scoped to the approver, which §5.3:622 states
explicitly ("for the approver specifically, and not for the caller").

**What the design actually does, which is better than the gap suggests and still not written down.**
On HTTP, `require_scopes` enforces authorization off the **bearer token's** scopes (§7.2:749-756) -
that is the request principal, never a model-supplied value, so the second clause's central demand is
substantially met at data-class granularity. What is absent is row-level scoping, and the reason it
is absent is that there is one Jobvite tenant per deployment and no per-caller record set to scope
against. **I grepped for that fact and it is not in the document**: `tenant` appears at `:90`, `:396`
and `:1035`, none of them establishing single-tenancy or the absence of a per-caller record model.
Meanwhile §7.2:758-761 states "**stdio is unauthenticated by design**" without connecting it, so a
reader auditing this clause finds a section that appears to *concede* ambient authority rather than
dispose of it, and `get_candidate` resolving a record off a model-supplied `candidateId` (§2:115) is
the literal shape `:110-111` forbids.

**Why Medium, by the same test I applied to M-1.** A required clause from a binding standard, with no
citation, no B-number and no ADR, whose justification exists in the author's head and nowhere in the
text, inside a document about to become ADR-only-changeable. A reader cannot tell whether it was
considered and disposed or simply missed - and the evidence is that it was missed, by every
instrument, for the life of the document. That is a conformance defect, not a wording nit. It is
**not** a security defect: I found no exposure that the current design leaves open.

**Suggested fix (mine, verify before adopting) - one paragraph and one B-number. I am deliberately
bounding this so it does not grow.**

1. **A §7.2 paragraph**, after the stdio paragraph, disposing the clause: that `require_scopes`
   enforces off the token principal and never off a model-supplied value; that `get_candidate`
   resolves off a model-supplied id **and why that is not ambient authority here** - one Jobvite
   credential per deployment, no per-caller record set, so there is no caller-scoped access to
   enforce; and the ceiling - **if Jobvite ever exposes per-user or multi-tenant scoping, this clause
   becomes a live obligation and this disposal expires.** Without that trigger sentence the disposal
   rots silently the day the assumption changes.
2. **One B-number (B107)** citing **both** ranges, so the next conformance sweep sees it.
3. **No new §11 row**, and I want to be explicit that I considered one and rejected it. C1-E1 already
   carries "a token provisioned with the wrong scope set reaches candidate PII it should not" at
   Medium, which is the real adjacent exposure. Adding a row would assert a threat whose disposal is
   that it does not exist here.
4. **No code change.**

One caution on the wording: state the single-tenant fact as a property of **the deployment model**
(one API key, one `companyId`, per deployment), not as a Jobvite guarantee. We have never seen
Jobvite's permission model - §7.2:785-788 says so about read-only keys - and asserting it as a vendor
property would be the same over-read this document has corrected twice.

### M-3 - The caller-replay clause names a remedy nobody evaluated, and DESIGN.md still does not dispose of it

`backend/resilience.md:146-151`; `DESIGN.md:1602` (C4-D2), `:1874`; `STANDARDS.md:605-621` (B108).

Referred to me as F10 and rated above F1 by the referrer. Verified independently. **I rate it the
same as F1 - Medium - and I explain below why I do not rate it higher, because I was asked not to
deflate it and I want the reasoning visible rather than the number asserted.**

**The clause exists and was stepped over.** `backend/resilience.md:146-148` - *"Make a write
retry-safe by guarding it with an **idempotency key** so the downstream dedupes the replay ... Only
then may the write be retried."* The corpus cites `:143-145` as B36 (`STANDARDS.md:313`) and
`:159-161` as B37 (`:317`) - the clauses on either side - and stepped over the six lines between.
Positive control: `resilience.md:224` / `:74` resolve 23 times across `docs/`, so the instrument
finds resilience citations.

**The dismissal that should have caught it is circular, and the corpus now says so itself.** B36 and
B19 both concern the **server's own** auto-retry and are discharged by `create_candidate` never being
retried (§4.3). The residue is **caller** replay, which never-auto-retrying does not touch.
`STANDARDS.md:615-617` now records that the `backend/idempotency.md` dismissal - *"B19's tool-level
idempotency covers the residue"* - does not survive reading B19's own verdict.

**The exposure is the project's worst harm, and its rated mitigation is a hypothesis.** C4-D2
(`DESIGN.md:1602`) is a duplicate candidate and **a second email to a live person** - the same harm
§5.3's audit-failure branch is built to avoid. Its treatment is "Never retried (§4.3); a `409` is
surfaced as `/problems/conflict`... **Detection, not prevention**", and the row itself concedes the
`409` shape is **inferred rather than observed**. So the accepted residual rests on detection that
has never been seen working, and the acceptance was made without the named remedy ever being
considered.

**Why Medium and not High.** A High would mean the design permits a bad outcome it could close. It
may not be able to close it: `grep -i idempot` over `JOBVITE-API.md` and `JOBVITE-CONTRACT.md`
returns **zero**, so whether Jobvite accepts a dedupe key is unknown, and if it does not, the correct
disposal is a named ceiling - which is a documentation fix, exactly like F1. The bounded worst case
is "accept, and say why". That caps it at Medium. What makes it a Medium rather than a Low is that
**an acceptance made in ignorance of an available remedy is not a valid acceptance**, and after the
freeze only an ADR can revisit it.

**Suggested fix (mine, verify before adopting) - a §4.3 or §2.2 paragraph plus two small edits.**

1. **Dispose of the clause where the write is specified**, discharging B108: state that the server
   never auto-retries `create_candidate` (already true, B36/B19), that the remaining path is a
   **caller** re-issuing the write, and then the decision - either an idempotency key is sent to
   Jobvite, or **the ceiling is named**: we do not know that Jobvite accepts a dedupe key, the
   research corpus contains no evidence either way, and until a credential exists this cannot be
   established. Model it on §7.2's read-only-key treatment, which is the right precedent and already
   in the document.
2. **Point C4-D2 at it.** The row should cite the clause and the disposal rather than stopping at
   "Detection, not prevention", so a reader auditing the residual can see the remedy was considered.
   I am **not** proposing a re-rating: L=M × I=M yields Medium by the matrix and that is unchanged.
3. **Fix `DESIGN.md:1874`, which is now stale in an unfortunate direction.** It reads
   "`devops/docker.md` and `backend/idempotency.md` are the two most likely to have gone live" -
   still future-tense about a condition that **has** now tripped. The document predicted this exact
   failure and the prediction outlived its own event. Suggested: "`backend/idempotency.md` **did** go
   live - reopened as B108 - which is the second time a conditional dismissal tripped unnoticed;
   `devops/docker.md` remains the outstanding one."

**One option I want on the record before the disposal is written, offered as a hypothesis and not a
recommendation.** The choice is not only "Jobvite dedupe key or accept". A **server-side** guard is
possible and independent of Jobvite's support - §4.5 already specifies a de-duplication seen-set for
pagination, so the pattern is in this design's vocabulary. It carries real costs (state, TTL,
behaviour across restart) and may well be rejected. **My point is only that the disposal should say
it was considered**, because "Jobvite may not support it" does not by itself establish that nothing
can be done. I have not designed this and I am not asking for it to be built.

### L-1 - The "not reconstructible" sentence invites the next editor to reconstruct it

`DESIGN.md:1669-1672`.

> **The original total is not reconstructible from this document and is deliberately not asserted
> here.** The prose it came from did not reconcile - it named four removals from *"seven"* and
> concluded *"five"* - so restating any number would propagate a figure whose derivation is lost.

The claim is true (see above), but the stated reason points only at the deleted prose. Meanwhile the
ledger sitting directly above the sentence now names nine removed rows over an empty table, and
`:1659` mandates that every future edit adds a row to it. Summing it is a one-line arithmetic step,
it yields **nine**, and nothing on the page tells a reader that nine is as untrustworthy as seven.
This paragraph exists to stop a total being restored; as written it leaves the restoration a
subtraction away, in the section whose count has now been re-broken four times.

**Suggested fix (mine, verify before adopting) - cheap, one sentence.** Replace the sentence with:

> **The original total is not asserted here, and cannot be recovered.** Two records of it exist and
> they disagree: the retired prose said *"seven"* while naming four removals and concluding *"five"*,
> and the ledger above accounts for nine removed rows over a now-empty table. Neither is
> load-bearing and neither is trustworthy. **Do not derive a total by summing the ledger.**

### L-2 - "No sentence in this section states a total" is false of §11 as written

`DESIGN.md:1648`: **"This table is the count. No sentence in this section states a total."**

§11 states several totals: `:1447` "Four of the six triggers at `:120-127` fire", `:1452` "Four
conventions", `:1458` "An earlier revision left six ids colliding", `:1650` "the total was stated in
prose three times". The sentence plainly means *a total for this table*, and every reader will read
it that way - but it is an unqualified universal about counting, two lines above a ledger, in the
section that has been bitten four times by exactly that. It is the one sentence here that should not
need charitable reading.

**Suggested fix (mine, verify before adopting) - cheap, two words.**
"This table is the count. **No sentence in this section states a total for it.**"

### L-3 - The production-release list reads its departed rows as members

`DESIGN.md:1678-1682`:

> **Mitigate before production release** (inherent Medium, unmitigated): C3-I1 and C6-D1 the
> undocumented result cap (B15), C7-I2 log-stream handling, C8-R1 configuration-change logging, and
> **C3-T1 (B25), C3-D1 (B30) and C9-D1 (B72) have left this list**: ...

The `and` joins current members to rows that have **left**, inside one comma-list under one
"(inherent Medium, unmitigated)" header. Scanned rather than parsed - which is how a list of ids
gets read - it names seven members where there are four. I confirmed the substance is right: C3-I1,
C6-D1 and C8-R1 carry `unmitigated` and C7-I2 carries `residual` in their Test cells, while C3-T1,
C3-D1 and C9-D1 each name a real §8 case. Only the sentence is wrong, and `check-coupling.py` cannot
see it - the gate checks that every id named is defined, not which side of a list it is on. This is
the same defect class as §11's own complaint at `:1687` that "an earlier revision named all three
departures in one sentence, which read as a single group".

**Suggested fix (mine, verify before adopting) - cheap, split the sentence.**

> **Mitigate before production release** (inherent Medium, unmitigated): C3-I1 and C6-D1 the
> undocumented result cap (B15), C7-I2 log-stream handling, and C8-R1 configuration-change logging.
> **Three rows have left this list:** C3-T1 (B25), C3-D1 (B30) and C9-D1 (B72) - §2.1 specifies the
> control-character and encoding rejection and the four structural limits, and §10 carries the
> advisory-triage policy, each with a §8 case.

### L-4 - "C4-S1 is the one such row" now survives on a single unstated word

`DESIGN.md:1634-1639` states the selection rule, then: "**C4-S1 is the one such row.**"

M-1 then added C5-E1 to Residual Risks at `:1714`, at **High**, with "**No server-side remedy
exists.**" A reader who asks the rule's own question - which Critical/High rows have no server-side
remedy and were carried to Residual Risks instead? - now finds two, and reads that there is one.
The claim is not actually false: the rule's predicate is *unmitigated*, and C5-E1 is mitigated as an
operator instruction (`:1581`), so it was never selected. But that reconciliation lives nowhere near
the sentence, and an exclusivity claim resting on one unrepeated adjective is precisely what round 6
found broken here.

**Suggested fix (mine, verify before adopting) - cheap, one added sentence after "C4-S1 is the one
such row."**

> C5-E1 is also inherent High with no server-side remedy, but this rule never selected it: it is
> mitigated in §7.2 as an operator instruction, so it was never unmitigated. It appears in Residual
> Risks for the exposure that instruction does not reduce, not by this rule.

### L-5 - §12 does not carry the external unknown that §5.3's trace work introduced

§5.3:609-611 records "**Whether a given host injects at all is unverified**", written to the wire
contract rather than to a measured client. §12:1737 enumerates: "Items 1 to 4 are external unknowns
about Jobvite or about a host", and item 4 (`:1730`) is a host-capability unknown of exactly this
shape - whether Claude Desktop supports elicitation. Host trace injection is the same class and is
absent from the list. §12 does disclaim being an inventory of everything unexecuted (`:1741`), but
this is not unexecuted work; it is an external unknown, which is what §12 *is* the list of.

**Suggested fix (mine, verify before adopting) - cheap, one list item.** Add to §12 as item 6, and
leave `:1737`'s "Items 1 to 4" sentence to be reworded to include it:

> 6. **Whether any host injects W3C trace context into a tool call's `_meta`.** The mechanism is
>    verified present on the pinned stack (§5.3) but no host has been observed using it. Nothing
>    depends on it: the fields are recorded when present, omitted when absent, and §8's two-arm case
>    passes either way.

### N-1 - Broken nested bold in the audit-PII sentence (the L-2 rewrite)

`DESIGN.md:639`, raw:

```
**Candidate PII reaches the audit *path* by construction - the arguments to redact are the candidate's own fields - and **what is emitted carries none of it in the clear****, because ...
```

A `**` pair opened inside an already-open `**` pair does not nest in Markdown. The rendered output
is mangled and the emphasis the L-2 fix was written to place on "carries none of it in the clear" -
the whole point of that rewrite - is lost or turned into stray asterisks. The sentence is also the
longest unwrapped line in the section.

**Suggested fix (mine, verify before adopting) - cheap, delete the inner pair and rewrap.**

> **Candidate PII reaches the audit *path* by construction** - the arguments to redact are the
> candidate's own fields - **and what is emitted carries none of it in the clear**, because the
> approval request describes the candidate about to be written.

### N-2 - §7.7 puts the `ResponseLimiting` raise in the wrong process

§5.3:570-572 attributes the `ResponseLimitingMiddleware` breakage to the client's unconditional
output-schema validation. §7.7:1047 describes it as the middleware itself: "broken - raises on any
tool with a return annotation". I verified the mechanism: the middleware truncates to a single
`TextContent` block (`fastmcp/server/middleware/response_limiting.py:24-26`), which drops
`structured_content`, and the **client** then raises at `mcp/client/session.py:1144-1145` -
"has an output schema but did not return structured content". Same failure, but §7.7's phrasing
locates the raise server-side, which is what makes §5.3's "the same unconditional validation" read
as a cross-reference to something §7.7 does not say. §7.7:1047 is unchanged by these commits, so
this is pre-existing; I am reporting it only because §5.3 now points at it.

**Suggested fix (mine, verify before adopting) - cheap, one clause.**

> Not used: `ResponseLimiting` (broken - truncating a result drops its structured content, so the
> *client's* output-schema validation raises on any tool with a return annotation, filed as [#4926])

---

## OUT OF SCOPE, NOT ASSESSED

§1, §2, §4.1, §4.2, §4.4, §4.5, §6, §7.1, §7.3-§7.6, §9, §10 beyond the §11/§5.3 references, §13,
and the rest of §8 beyond the six cases tabled above - not read for this pass, per the brief. The
one thing I would not want silently inherited: I re-ran the three gates but did not re-audit the
gate scripts themselves, so their green licenses only what they check, and `check-coupling.py`
demonstrably cannot see L-3.
