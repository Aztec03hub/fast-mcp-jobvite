# DESIGN.md revision 3 - adversarial review round 3, and threat-model validation

Reviewer: `design-review-r3`. Date: 2026-08-27.
Target: `docs/DESIGN.md` at `78ba3ca` (1163 lines).
Result: **0c / 5h / 6m surviving.** Threat model: **VALIDATED WITH CHANGES.**

> **The document moved under this review.** I began against the revision at `86f87ca` and the lead
> committed `a9f6219`, `c326d30` and `78ba3ca` while I was reading. Three findings I had drafted
> (the `three ways` / `two gates` contradiction in §2.2, §5.3 and §9.6; the era-downgrade
> fall-through; ADR-0009 over-reaching onto caller identity) were fixed by those commits before I
> filed them, and I have dropped them rather than claim them. **Every line number below was
> re-pinned against `78ba3ca` after those commits.** One of the fixes introduced a new defect,
> which is R-3.

## What I read

**In full:** `docs/DESIGN.md` (all 1163 lines, twice - once at `86f87ca`, once at `78ba3ca`);
`docs/reviews/DESIGN-R1.md` and `DESIGN-R2.md` "What I did NOT review" sections plus R2's CRITICAL
findings; `standards/architecture/threat-modeling.md` (whole file).

**Targeted, opened at every `file:line` I cite:** `CONFORMANCE-B1-B106.md` rows B12, B15, B17, B21,
B22, B23, B25, B30, B39, B40, B41, B88, B90, B91; `JOBVITE-API.md` §6.1 and §§13, 20 (pagination,
`total`, id shapes); `docs/DECISIONS.md` (grep for stale mechanism references);
`standards/ai/agent-guardrails.md:40,47-49,79,106-107,121-123`;
`standards/ai/tool-calling.md:54,171-173`; `standards/architecture/error-contract.md:44`;
`standards/architecture/caching.md:833,841`; `standards/architecture/gdpr-data-rights.md:9,119-129`;
`standards/backend/rate-limiting.md:361-362`; `standards/backend/resilience.md:220-230`;
`standards/backend/input-validation.md:218-230`.

**Not read:** see the closing section.

---

## The document's factual assertions about the world: a clean result

Per the brief, I ran this first. Every previous round found at least one false, checkable claim
about a file outside the document. **This round found none of that class.** Recording it explicitly
because a clean sub-result backed by the checks is the point of a convergence round:

- `threat-modeling.md` frontmatter is `applicable_to: all` (`:6-7`) and `priority: required`
  (`:8`). §11:906 states both. **Correct.**
- `:35` reads *"Use **STRIDE per-component** as the default approach. For each component in the
  feature's data flow, evaluate all six STRIDE categories."* §11:924 cites it for exactly that.
  **Correct.**
- `:62-74` are the Likelihood and Impact ladders; `:78-82` is the matrix; `:86-88` are the
  thresholds; `:120-127` are the six Required triggers; `:143` is "authored during specification";
  `:145` is "Tech Lead or Security reviewer validates". **Every one lands where §11 says it does.**
- Four of the six triggers do fire: `:122` PII, `:123` authn/authz, `:124` new API endpoints exposed
  to external clients, `:125` third-party integrations. **Correct.**
- `agent-guardrails.md:122` reads *"result status, latency, the approval decision if gated, and"*.
  §11:1012 cites `:122` for the approval decision. **Correct.**
- `gdpr-data-rights.md:9` reads `priority: required`, and §6.2:415-418 now says so and names its own
  earlier claim as false. **R2's C3 is closed correctly.**
- §10's packaging block now contains `"mcp==2.1.1"` (`:826`). **R2's C4 is closed.**
- §4.5's inverted probe is gone. **R2's C1 is closed in the mechanism** (though not in two
  cross-references - see m1).

One citation is imprecise rather than false: **m6** below.

I also hand-checked the arithmetic claim at §11:921-923 (*"Machine-checked: every rated row agrees
with it"*). **All 43 rated rows agree with the matrix at `:78-82`.** The claim holds.

---

# RED ROUND - Adversarial Review

## MAJOR

### R-1. §4.5's "base-agnostic" paging is robust in exactly one direction, and it is not the dangerous one. [DEALBREAKER if shipped as written]

This is the mechanism that replaced R2's inverted probe, and the lead named it as a place he may
have swapped one broken thing for another. He did, partially.

§4.5:283-290, verbatim:

> "**What we do instead, and it needs no probe.** `start` is **1-based** ... Correctness does not
> rest on that being right, because paging is made **base-agnostic**:
> - Pages are requested by `start` and every returned record's id is checked against a per-scan seen
>   set. **A record already seen is dropped, and a gap is detected and logged.**"

Walk both hypotheses. The evidence leaves exactly two open (`JOBVITE-API.md:811`: *"does **not**
distinguish a 0-based server from a 1-based one that clamps `0` to `1`"*).

**Case A - server is 1-based (the assumed case).** First request `start=1`. Correct throughout.
Zero cost.

**Case B - server is 0-based.** The design's first request is `start=1`, because the design says
`start` is 1-based. **The record at offset 0 is never requested and never returned.** A seen-set
cannot de-duplicate a record that was never fetched. **De-duplicating on the way out defends
against over-reading, not under-reading.** The scan silently loses one record - which is precisely
the failure §4.5:271-272 exists to prevent (*"If we are wrong we silently skip the first record of
every page"*). It is now one record per scan rather than one per page, which is an improvement, but
the section claims the class is eliminated and it is not.

**And the stated backstop does not exist.** *"a gap is detected and logged"* has no mechanism.
`JOBVITE-API.md:517` records that `eId` is an **8-character opaque id** and that *"Jobvite's id
formats are not uniform across resources"*. **You cannot detect a gap in a set of opaque
identifiers.** There is nothing ordinal to find a hole in. The sentence promises a control that
cannot be implemented as described.

Both halves are fixable, cheaply, from evidence already in the repository:

1. **Start every scan at `start=0`, not `start=1`.** `JOBVITE-API.md:399` records that *"`start=0` is
   accepted and returns records"*, and §4.5:277 records the lead's own conclusion that a 1-based
   server **clamps 0 to 1**. So `start=0` costs a 1-based server nothing and is the only value that
   is correct on both. The seen-set then absorbs the clamp duplicate exactly as designed. **That
   single change is what actually makes the paging base-agnostic.**
2. **Gap detection must compare unique-id count against `total`**, which is the only ordinal
   quantity available. `JOBVITE-API.md:397-398,428` confirm `total` is returned and is the full
   result-set size. This does not conflict with §4.5:308-309 (*"`total` ... never trusted as a loop
   condition"*): a post-scan integrity check is not a loop condition.

### R-2. §11's own load-bearing integrity claim is false, and it fails on the two Critical rows protecting special-category data and PII.

§11:929-930 and again at §11:1090-1092:

> "**Every mitigated Critical or High row below has a required test in §8. That coupling is the
> point: if a mitigation loses its test, this threat model becomes false.**"

§8:725-737 is the "Required cases" list. Checked row by row against §11:1087-1089's roster:

| Row | Rating | Required test in §8? |
|---|---|---|
| C5-S 200-with-401 | Critical | Yes, §8:726 |
| C6-S prompt injection | Critical | Yes, §8:728 |
| **C6-I EEO exclusion** | **Critical** | **No. §8 has no EEO test.** |
| **C7-I PII in logs** | **Critical** | **No. §8:727 tests a *secret* never reaching a log record. A secret is not candidate PII, and C7-I is *"Candidate PII written to logs in the clear"*.** |
| C4-E accept-carrying-false | High | Yes, §8:731-732 |
| C5-I jobFeed URL | High | Yes, §8:727 |
| C1-S/T/I TLS | High | Excused in the sentence itself, startup check |
| **C2-R audit event exists** | **High** | **No. §8 has no test that the audit event is emitted at all.** |

Three rows fail, two of them Critical. By the document's own sentence, **this threat model is
currently false**, and it is false about the exclusion of `gender`, `race` and `veteranStatus` and
about candidate PII reaching logs. §2.1:116 mentions a fencing-coverage test, which is adjacent and
covers neither.

Either add the three cases to §8 or delete the claim. Deleting it is worse - the coupling is the
best idea in §11.

### R-3. §5.3's brand-new caller-identity paragraph is false on the default transport, and it silently closes a must-mitigate row that §11 still lists as open.

Added in `c326d30`. §5.3:374-377:

> "*which client invoked the tool* is entirely knowable, and §4.4 **already derives that value**
> through `get_client_id` in order to rate-limit on it. **The caller identity is recorded in the
> audit event.**"

§4.4:247, unchanged:

> "On stdio there is no token and thus no `client_id`, but there is exactly one caller, so the
> global bucket is correct there."

And §7.2:490 (`stdio is unauthenticated by design`). **On stdio - the default transport, and per
§7.5:607 where the majority of local users land - there is no client identity to derive.**
`get_client_id` there yields the framework's literal `"global"`, which is not a caller identity;
it is the absence of one. "Entirely knowable" is true on the opt-in HTTP transport and false on the
default one, stated without qualification, in a document about to freeze.

Two consequences, and the second is the worse one:

- §11:1073 still lists **C1-R** under *"Must mitigate before implementation proceeds"* with the
  action *"Record the resolved client id beside `request_id`"*. §5.3 now says that is done. **The
  threat model and the design contradict each other on a must-mitigate row.**
- The action as written **cannot be completed on stdio.** An implementer will wire
  `get_client_id`, get `"global"`, and close C1-R believing caller attribution exists. It will not.
  The honest form is: caller identity is recorded on HTTP; on stdio the audit event records that
  the caller is the spawning OS process and attribution is the OS's, per §7.2's trust boundary.

### R-4. `JOBVITE_TOOLS` has undefined behaviour in the most common deployment, no unknown-name policy, and is absent from the threat model entirely.

New in revision 3, added to make §7.3's "each enabled tool" implementable, and the lead correctly
flags that nothing has reviewed it. §7.3:503-506:

> "`JOBVITE_TOOLS` is a comma-separated allow-list of tool names; unset means all read tools.
> `JOBVITE_ENABLE_WRITES` additionally gates `create_candidate` (§2.2) and is independent, so a
> write cannot be enabled by naming it alone."

Three gaps:

**(a) The default deployment is undefined for the write tool.** *"unset means all read tools"* -
`create_candidate` is not a read tool, so the unset default selects it nowhere. `ENABLE_WRITES`
*"additionally gates"* it - additionally to a selection that never happened. So for
`JOBVITE_TOOLS` unset plus `JOBVITE_ENABLE_WRITES=true`, which is the obvious way an operator turns
writes on, **the text does not say whether `create_candidate` is registered.** The sentence answers
only the converse (naming it in `JOBVITE_TOOLS` alone does not enable it). This is the enable
surface for the only destructive tool in the server, and its most likely configuration is
unspecified.

**(b) No policy for an unrecognised name.** §7.3's entire thesis is fail-fast at boot
(`:496-500`: a missing credential *"must fail at boot, naming the variable"*). `JOBVITE_TOOLS=serch_candidates`
should therefore be a boot failure. The section does not say so, and the silent-ignore alternative
produces a server that starts cleanly with fewer tools than the operator asked for.

**(c) It is nowhere in §11.** B6 (§11:962) lists the operator-to-configuration boundary's controls as
*"`JOBVITE_ENABLE_WRITES` and TLS enforcement both server-side"*. `JOBVITE_TOOLS` is now a
capability-determining input crossing that same boundary and appears in no asset, no boundary
control, and no STRIDE row. Compare C8-E, which models `ENABLE_WRITES` being flipped: the identical
threat against `JOBVITE_TOOLS` is unmodelled.

## MINOR

- **m1. The cut probe is still live in two places.** §1:20-22 lists *"the runtime `start`-base probe
  (§4.5)"* among *"Two mechanisms designed here [that] have never been executed"*, and §12:1114
  reads *"**The `start` base.** Now probed at runtime (§4.5), but the probe itself is unverified"*.
  §4.5:283 says *"it needs no probe."* The preamble also mislabels what is actually unexecuted: it
  is the base-agnostic seen-set, not a probe.
- **m2. §12 open question 4 is answered inside the same document.** §12:1117 asks *"Whether success
  bodies carry a `status` block at all."* §8:714-716 says the structural fixture *"already answers
  what was an open question"*, and `JOBVITE-API.md:397` states it outright: *"A success body DOES
  carry a `status` block."* Resolved, not open.
- **m3. §8's required-case list has a dead entry and a missing one.** §8:733 requires *"token replay,
  expiry, and payload mismatch each refused"* for the mechanism §7.6 cut. Meanwhile §5.1:333 claims
  *"The rejection still fails closed and is unit-tested, which is what B12 and B23 actually
  require"* - but `CONFORMANCE-B1-B106.md:145` rates **B12 PARTIAL** for precisely the reason that
  argument rejection *"is **not** in §8's 'Required cases' list"*, and `:156` rates **B23 PARTIAL**
  with an untested unbounded-loop arm. The design asserts conformance that the sweep it folded in
  says it does not have.
- **m4. §5.3's post-write audit policy routes its warning through the channel that just failed.**
  §5.3:391: a post-write audit failure returns success *"and it is recorded as a warning in the same
  stream."* If the audit sink is what failed, the warning to that sink is lost too. §5.3:389 already
  has the right answer for the read path (*"log to stderr and continue"*); the post-write path needs
  the same independent channel. Separately, §5.1:310 says no `success`/`false` envelope exists
  anywhere, and nothing defines the shape of a "success with a warning".
- **m5. C7-E violates §11's own stated convention.** §11:924-926: *"Where a category carries no
  credible threat the row says so **and gives the reason**."* §11:1051 reads
  `| C7 | E | No credible threat | - | - | - | - |` with no reason. It is the only one of the ten
  such rows that omits it; the other nine comply.
- **m6. `resilience.md:226` is ambiguous and clipped.** §11:1022 cites it bare. Two files carry that
  name (`ai/resilience.md`, `backend/resilience.md`) and only `backend/` has a line 226. The
  obligation also spans `:224-226`; `:226` alone is the sentence fragment *"`request_id` correlation
  field. Never retry or trip silently."* Cite `backend/resilience.md:224-226`.
- **m7. The threshold table's stated selection rule does not produce its own contents.** §11:1069
  selects *"unmitigated, inherent Critical or High"*. **C4-S is High and explicitly unmitigated**
  (§11:1007: *"Not mitigable server-side"*) and is correctly absent from the must-mitigate list
  because it is accepted. The rule needs a third disposition (accepted) or C4-S needs a line saying
  why the rule does not reach it.
- **m8 (flagged, not litigated, per the brief).** Rows resting on the cut confirmation token, for
  the rerating pass in flight: the Assets row at `:949`; the C4 component header at `:1005`; C4-T
  `:1010`; C4-T-TTL `:1011`; C4-I `:1013`; C4-E-era `:1016` (its premise *"the write falls through
  to the confirmation token alone"* is now contradicted by §7.5:619-624's refusal rule); C8-E
  `:1062` (*"the write still requires approval plus a confirmation token"*); the roster entry *"C4-T
  token binding"* at `:1089`; the production-release entry *"C4-T the unstated token TTL (B22)"* at
  `:1084`; the Residual Risks rows at `:1098` (whose defence-in-depth clause names the token) and
  `:1099` (entirely about the token). **One independent defect inside that set that the rerating
  will not catch: `:1011` cites B22 as an open gap, but `CONFORMANCE-B1-B106.md:155` rates B22
  SATISFIED.**

---

# BLUE ROUND - Normal Response

**R-1 - ACCEPT, in full.** The asymmetry is real and I do not think it was noticed. De-duplication
was chosen because it is robust against the *duplicate* failure R2 identified, and the section then
generalised that to "base-agnostic" without walking the opposite hypothesis. The remedy is one
character (`start=0`) and it is licensed by evidence already cited two paragraphs above the defect.
The opaque-id point is separately correct and worse: the sentence promises detection that has no
implementation. Both go in.

**R-2 - ACCEPT.** C6-I and C7-I have no §8 case, and I cannot argue that "a secret never reaching a
log record" tests candidate PII redaction - §5.3 spends a paragraph distinguishing the two, so the
document already knows they are different controls. C2-R likewise. The claim is the most valuable
sentence in §11 and it must be made true rather than softened.

**R-3 - MODIFY.** The finding is correct and the framing overshoots slightly. The paragraph's
*purpose* is right: ADR-0009 was over-reaching from approver identity to caller identity, and
separating them was the correct fix. What is wrong is the unqualified "entirely knowable", which is
an HTTP-only truth stated globally. So: keep the paragraph, qualify the transport, and reconcile
§11:1073 with it. The second consequence Red names - an implementer closing C1-R on a `"global"`
literal - is the part that actually matters and I accept it without qualification.

**R-4 - ACCEPT (a), (b) and (c).** (a) is the one I would have defended and cannot: re-reading
§7.3:503-506 with the write tool in mind, the two sentences genuinely do not compose into an answer
for the unset-plus-writes-enabled case. (b) follows from §7.3's own fail-fast thesis. (c) is a
threat-model omission and belongs in Job 2's change list as well.

**m1 ACCEPT. m2 ACCEPT. m4 ACCEPT** (both halves; the stderr fix is one clause and the
success-with-warning shape is genuinely undefined). **m5 ACCEPT. m6 ACCEPT. m7 ACCEPT** (the rule
should gain "accepted" as a disposition; C4-S is correctly excluded and incorrectly unexplained).
**m8 ACKNOWLEDGED**, held for the rerating pass, with the B22 mis-citation noted separately because
it is not staleness.

**m3 - MODIFY.** Two different things are bundled. The token-test line is staleness and belongs in
m8. The B12/B23 half is not staleness at all: §5.1:333 asserts conformance that
`CONFORMANCE-B1-B106.md:145,156` explicitly denies, in a document whose whole preamble is about not
self-certifying. Splitting it, the token half merges into m8 and the conformance half stands alone
as a MINOR.

---

# RED ROUND - Adversarial Rebuttal

**On R-3's modification: accepted, no further push.** The distinction between approver and caller is
right and the fix commit was correct. My finding survives at MAJOR on the strength of its second
consequence alone: a must-mitigate row that the design believes is closed and the threat model still
lists as open, with an action that returns a placeholder string on the default transport.

**On m3's split: I push back on the severity, not the split.** Blue is right that these are two
things. But calling the surviving half MINOR misreads what class it is in. Consider the record:

- R1 found a `priority: optional` that read `required`.
- R2 found a "verbatim" packaging block missing the package the prose said it pinned.
- R3's preamble at §1:24-25 instructs the reader to *"challenge any sentence that reads as verified
  without belonging to them."*

§5.1:333 says an obligation is met. The sweep this revision folded in, at
`CONFORMANCE-B1-B106.md:145`, says it is PARTIAL **and gives as its reason the exact absence
§5.1 is claiming to have filled**. This is not a stale cross-reference. It is the document
asserting its own compliance against evidence it already contains, which is the specific failure
mode the entire preamble was written to prevent and the specific failure mode that has survived
into every revision so far. It is also self-reinforcing with R-2: §5.1 claims a test exists, §8's
required list does not contain it, and §11 then claims every mitigation has a required test. Three
sections agreeing with each other and none of them agreeing with the test list.

**Promote to MAJOR.** No new points; nothing else was unlocked.

---

# BLUE ROUND - Final Normal Response

**m3's surviving half is promoted to MAJOR, as R-5.** The argument is correct and the pattern
evidence is decisive: three rounds, three false self-claims, and this is the fourth in the same
family. It is also the cheapest of the five to fix - add the argument-rejection case to §8:725-737
and B12 closes, at which point §5.1:333 becomes true rather than needing to be weakened.

Everything else stands as ruled in the Blue round. No finding is rejected. Two were modified (R-3
qualified to transport scope; m3 split and promoted).

---

# Final Report - Job 1

| # | Severity | Section | Finding | Disposition |
|---|---|---|---|---|
| R-1 | MAJOR | §4.5:283-290 | Paging is robust against over-reading only; a 0-based server silently loses record 0, and opaque `eId`s make the promised gap detection unimplementable | **Accepted.** Start scans at `start=0` (licensed by `JOBVITE-API.md:399` and §4.5:277); detect gaps by unique-count vs `total` |
| R-2 | MAJOR | §11:929-930, 1087-1092 | The test-coupling claim is false for C6-I (Critical), C7-I (Critical) and C2-R (High) | **Accepted.** Add three cases to §8 |
| R-3 | MAJOR | §5.3:374-377 vs §4.4:247, §11:1073 | "Caller identity is entirely knowable" is HTTP-only; stated globally; and C1-R's must-mitigate action yields `"global"` on the default transport | **Accepted, modified.** Qualify by transport; reconcile §11:1073 |
| R-4 | MAJOR | §7.3:503-506, §11:962 | `JOBVITE_TOOLS`: unset-plus-writes-enabled is undefined for `create_candidate`; no unknown-name policy; absent from §11 | **Accepted** on all three limbs |
| R-5 | MAJOR | §5.1:333 | Asserts B12/B23 are met against `CONFORMANCE-B1-B106.md:145,156`, which rate both PARTIAL for exactly the missing thing | **Accepted, promoted** from MINOR |
| m1 | MINOR | §1:20-22, §12:1114 | Cut probe still described as live; preamble mislabels what is unexecuted | Accepted |
| m2 | MINOR | §12:1117 | Open question already answered by §8:714-716 and `JOBVITE-API.md:397` | Accepted |
| m4 | MINOR | §5.3:391 | Post-write audit warning routed through the stream that just failed; success-with-warning shape undefined against §5.1:310 | Accepted |
| m5 | MINOR | §11:1051 | C7-E gives no reason, violating §11:924-926 | Accepted |
| m6 | MINOR | §11:1022 | `resilience.md:226` ambiguous across two files and clipped; use `backend/resilience.md:224-226` | Accepted |
| m7 | MINOR | §11:1069 | Selection rule does not account for accepted-and-unmitigated C4-S | Accepted |
| m8 | flagged | eleven rows | Confirmation-token residue, held for the rerating pass. Plus one non-staleness defect: `:1011` cites B22 as a gap; the sweep rates it SATISFIED | Not counted |

**Convergence assessment.** This is not a clean round, but it is a converging one, and the shape of
what is left has changed. Rounds 1 and 2 found false claims about *the world* - a standards
frontmatter, a packaging block, a probe whose logic was inverted. **Round 3 found none of those**;
every external citation I checked landed, and the matrix arithmetic is correct on all 43 rows. What
remains is a different and lesser class: **claims the document makes about itself** that its own
other sections contradict. Four of the five MAJORs are internal inconsistencies (R-2, R-3, R-4c,
R-5) and every one is fixable inside a paragraph. Only R-1 is a design defect, and its remedy is
already licensed by evidence sitting two paragraphs above it.

The document is not yet at 0C/0H/0M and should not be frozen. It is close.

**0c / 5h / 6m surviving.**

---

# Job 2 - Independent threat-model validation

Per `architecture/threat-modeling.md:145` (*"Tech Lead or Security reviewer validates the threat
model during spec review"*). The author correctly refused to self-certify. I did not write §11 and
have no stake in it.

## Verdict: **VALIDATED WITH CHANGES**

The methodology is sound, the structure conforms to the standard, and the arithmetic is
independently correct. It is not padded. It has real omissions, and one of them is the boundary
across which this project's only actual security incident occurred.

## Asset completeness

Ten assets. Sensitivity labels are consistent and the locations are specific enough to be
falsifiable, which is better than most. **Three are missing:**

**A-miss-1. The calling model's context.** §11:1034 rates **C6-S Critical** - candidate free text
forging a channel break and impersonating system instructions to the calling model. The asset that
threat damages is the model's context window and, through it, whatever else the host has wired to
that model. **It is not in the Assets table.** B4 (§11:960) names it as a *destination* of a
boundary, which is not the same as valuing it. A table that omits the asset its Critical row
attacks is incomplete on its face.

**A-miss-2. The build and its inputs.** No asset covers `uv.lock`, the CI pipeline, its credentials,
or the push credential for the `Aztec03hub` mirror named at §10:829. C8's header names "repository"
and only C8-I touches it, at rest, for secrets. See M-1 and B-miss-1.

**A-miss-3. The `JOBVITE_TOOLS` enable surface.** Now determines which tools exist. See R-4(c).

Everything else of value is present and correctly rated. Note one asset (`:949`, the confirmation-token
HMAC key) is for a mechanism that no longer exists - m8.

## Trust boundaries

Six boundaries. B1 through B5 are drawn in the right places: the stdio/OS boundary is correctly
identified as the OS's rather than the server's and stated rather than assumed (B1), the
attacker-authored-content boundary at B4 is the non-obvious one and it is present, and B5 (server to
log sink) is the boundary most designs forget. This is above-average boundary work.

**B-miss-1, and it is the most serious finding in Job 2. The boundary where this project's only real
incident actually occurred is not in the table.** §11:1061 rates C8-I **Critical** with the
justification *"This repository has already had confidential material reach a public remote once"* -
and tasks #8 and #16 in this project's own dispatch record confirm it. The boundary that crossing
traverses is **developer or agent workstation to public git remote**. B1-B6 do not contain it. B6 is
*operator to configuration*, which is a different flow entirely.

This matters beyond bookkeeping. The mitigations §10:865-874 builds - pre-commit secret scanning and
the committed-file-type gate - are controls sitting *on that boundary*, and §10:873-874 states the
gate's limit precisely (*"It does nothing about confidential prose pasted into Markdown, which is
the incident we actually had"*). So the design knows the boundary, knows its controls, and knows the
residual. The boundary table carries none of it. **A boundary table that omits the boundary of your
only realised incident is drawn in the wrong place**, and it is the exact failure the brief warned
about: a table that looks complete and models the wrong system.

**B-miss-2. Server to a live human's inbox, via Jobvite.** §2.2:120-121: the write's *"side effect is
an email to a live human, and there is no sandbox."* That is data leaving the operator's control to
an uncontrolled third-party recipient, irreversibly. It is the least reversible action in the system
and no boundary row draws it. C4 and C8 model *authorisation* to cross it; nothing models the
crossing.

## Is the STRIDE coverage genuine or padded?

**Genuine.** I checked this structurally rather than taking the convention at its word.

Eight components, 48 category-rows, and **all six categories appear on all eight components** - I
counted them individually. Ten rows say "no credible threat". Nine give a reason and the reasons are
substantive rather than formulaic: C2-S and C3-S both defer to C1 with the specific claim that
identity is established there, which is true and checkable; C2-T's *"No adopted middleware mutates
request or response payloads"* is a real property of the §7.7 stack; C6-R's *"produces no auditable
decision"* is correct.

Two observations:

- **C7-E (`:1051`) is bare** - the single row that gives no reason, against §11:924-926's own
  convention (m5). One in ten is not padding, but it is the one row a reader would use to argue the
  convention is decorative.
- **The `no credible threat` rows are not where the padding risk lives.** The real test is whether
  the *populated* rows are distinct threats or the same threat restated. They are distinct: C1-S/T/I
  share a mitigation and are correctly kept as three rows because they violate three different
  properties, and the table says so rather than merging them.

## Are the ratings defensible?

**The arithmetic: yes, verified independently.** I checked all 43 rated rows against the matrix at
`:78-82` by hand. **43 of 43 agree.** §11:921-923's "machine-checked" claim is true, and it is worth
saying that this is the first document-level self-claim in this project that survived checking.

**The inputs: mostly, with one overclaim in the convention rather than in the ratings.**

§11:919-921 says *"Ratings are computed from the matrix at `:78-82`, not chosen."* Strictly, only
the **Risk cell** is computed. Likelihood and Impact are judgements, and they are the part that
determines the outcome. Spot-checking them against `:62-74`:

- **C6-S (H/H, Critical).** `:64` High likelihood is *"Easily exploitable, public attack tooling
  exists"* - injection payloads in a résumé field are exactly that. `:72` High impact is *"full
  compromise"*. **Correct on both.**
- **C4-S (H/M, High).** A host auto-responding is not merely likely, it is the documented default
  behaviour of some hosts. H is right; M impact (a write occurring without a person) is defensible
  against `:73`. **Correct.**
- **C5-S (H/H, Critical) - the one I would challenge.** Likelihood H is right; this fires on every
  rejected credential. But Impact H requires `:72`'s *"Data breach, full compromise, regulatory
  violation"*, and the stated consequence is *"reporting zero candidates for an unauthenticated
  caller"*. That is a silent wrong answer, not a breach - `:73`'s *"service degradation"* fits
  better, which would yield **High** rather than Critical. **This reads as reverse-engineered from
  the desired outcome**, and §4.2:192 (*"The load-bearing behaviour in this codebase"*) tells you
  why. Operationally nothing changes: High still clears `:86`'s must-mitigate threshold. **No rating
  change requested; soften the convention's wording at `:919-921` to claim what is true - the Risk
  cell is computed, the inputs are judged.**

**On the deliberately contested rating, C8-I Likelihood HIGH: I agree, and I would defend it against
a challenge.**

The obvious objection is that `:64`'s High is defined as *"Easily exploitable, public attack tooling
exists"*, which is adversarial-exploitability language and does not fit an operator accident.
That objection is about the standard, not the rating. The ladder at `:64-66` has no vocabulary for
accident frequency, and forcing this threat down it produces nonsense: `:66`'s Low is *"requires
insider access or unlikely preconditions"* and `:65`'s Medium is *"requires moderate skill or
specific conditions"* - both flatly contradicted by an event that **has already occurred once, in
this repository, under preconditions that are all still in force.** An observed base rate of one
occurrence is the strongest likelihood evidence a threat model can have, and it beats a definitional
quibble. **HIGH is correct, and H/H = Critical is correct** (Impact H is independently right under
`:72`: a leaked Jobvite credential is a breach of candidate PII for which the client is controller,
which is a regulatory violation).

I would add one sentence to the row recording *why* the ladder had to be read past, so a future
reviewer does not "correct" it downward by applying `:64` literally.

## What is missing that a threat model should have caught

This is the highest-value question and it is where §11 has the most to gain. Five items, none of
which a B-number clause sweep could have produced:

**M-1. There is no supply-chain component.** Eight components stop at the running process. §10 is
almost entirely a supply-chain security section - `uv.lock` committed, `uv sync --frozen`, SBOM from
the frozen resolve, pip-audit, CodeQL, TruffleHog at full history depth, a licence gate, and the
`fastmcp inspect` capability diff. **None of it is modelled.** And the design supplies the threat
itself, realised: §10:794-796 records that *"the `ResponseLimiting` regression arrived through the
transitive SDK with zero change to the code that broke."* That is a Tampering threat against the
build, it has already happened once benignly, and the threat model does not contain it. Add a **C9.
Build and supply chain** with at minimum: T (malicious or regressed transitive dependency), I (CI
secrets and the mirror push credential), and E (a dependency bump silently adding a capability - the
`fastmcp inspect` diff is its mitigation and §10:846-849 already marks that control **UNVERIFIED**).

**M-2. `send_email` is never modelled as an argument.** §2.2:150 notes it *"defaults to `false`"*,
and §11:973 uses *"flipping `send_email` to `true`"* as an example of **in-flight tampering** on a
plaintext bind. But there is no row anywhere for the legitimate path: **the model itself setting
`send_email: true`.** §7.5:592-595's guard checks `action == "accept" and content.get("approve") is
True` - it validates *that* something was approved, never *what*. Nothing in §7.5 specifies what the
elicitation payload shows the approver. So an approver can approve "create candidate Jane Doe" and
thereby authorise an email to Jane Doe that the prompt never mentioned. **This is the highest-value
gap in the model**: it is the one place where the strongest gate can be satisfied honestly and still
produce the outcome the gate exists to prevent, and no clause sweep would ever surface it. It needs
a C3 or C4 row and a sentence in §7.5 requiring the elicitation payload to name the destructive
parameters, `send_email` first.

**M-3. §9's hazard 6 is a stated unmitigated risk that reaches neither the STRIDE tables nor Residual
Risks.** §9:767-773, verbatim: *"none of §2.2's gates prevent one ... This is a real residual risk,
not a solved one: we can report a duplicate, not prevent it."* The consequence is **a second live
human emailed**, which is the same harm C4 exists to bound. It is in no STRIDE row and in no Residual
Risks row. The document names an accepted residual risk in §9 and the register of accepted residual
risks does not contain it. This also interacts with m4: §5.3:387-391's audit policy accepts an
audit hole *specifically to avoid* triggering this duplicate write, so the two are one coupled
decision and neither §11 row records the coupling.

**M-4. `JOBVITE_TOOLS` is unmodelled at B6.** See R-4(c).

**M-5. No row covers the audit stream as a PII store.** `c326d30` added §5.3:379-381: *"**The audit
stream holds candidate PII by construction**, because the approval request describes the candidate
about to be written."* That is a new and correct statement, and it means the audit stream is a
second PII sink alongside the log stream. C7-I (`:1049`) covers *"Candidate PII written to logs in
the clear"* and the C7-I retention row (`:1050`) covers the log stream's retention. Neither names the
audit stream, which now has the same handling class by the design's own sentence and is the stream
that must survive for C4-R's mitigation to mean anything.

## Required changes for full validation

| # | Change | Source |
|---|---|---|
| V1 | Add the workstation-to-public-remote trust boundary, with §10's two commit-time gates as its controls and §10:873-874's stated limit as its residual | B-miss-1 |
| V2 | Add a **C9 Build and supply chain** component with all six categories | M-1 |
| V3 | Add a `send_email` row, and require §7.5's elicitation payload to name the destructive parameters | M-2 |
| V4 | Carry §9 hazard 6 (duplicate creates) into Residual Risks, coupled to §5.3's audit-hole trade | M-3 |
| V5 | Add the calling model's context as an asset | A-miss-1 |
| V6 | Model `JOBVITE_TOOLS` at B6 and give it a STRIDE row | M-4, R-4c |
| V7 | Extend C7-I to name the audit stream, or add a row for it | M-5 |
| V8 | Add a server-to-live-human-inbox boundary | B-miss-2 |
| V9 | Make the test-coupling claim true: add §8 cases for C6-I, C7-I and C2-R | R-2 |
| V10 | Reconcile C1-R with §5.3, and state that its action is unimplementable on stdio | R-3 |
| V11 | Give C7-E its reason | m5 |
| V12 | Soften `:919-921` to claim only that the Risk cell is computed; add one sentence to C8-I recording why `:64` was read past | ratings |
| V13 | Fix the B22 citation at `:1011`; the sweep rates it SATISFIED | m8 |
| V14 | Complete the token rerating pass | m8 |

V1, V2 and V3 are the substantive ones. The rest are corrections.

## What I did NOT review, and why

- **`FASTMCP-SPIKE-4.md` in full (~2350 lines).** Targeted reads only: I opened it for the
  pagination and era claims and did not sweep it. **No finding here rests on a spike result**, and
  correspondingly I cannot certify that §7.4, §7.5 and §4.4's measured claims match their spikes.
  R2 read §§1.3, 6, 12.1, 13-15, 17, 19; nobody has read the whole thing against the design.
- **`COMPLIANCE-SPEC.md` and `STANDARDS.md` in full.** Not opened this round. I worked from
  `CONFORMANCE-B1-B106.md`'s rows for the fourteen B-numbers §11 cites and verified those clauses at
  their `file:line` in the standards corpus directly. I did not look for B-numbers §11 *should* cite
  and does not.
- **The 37 UNADDRESSED and 22 PARTIAL rows of the B1-B106 sweep, as a set.** Deliberately not
  duplicated, per R2's precedent. I touched only the fourteen §11 references.
- **`CONFORMANCE-DESIGN-ARTIFACT.md`.** Not opened. Named in the brief; I ran out of higher-value
  work before it, which is a real gap in this review rather than a judgement that it does not matter.
- **`docs/DECISIONS.md` D1-D17.** Grepped for stale token/probe references (clean) rather than read.
- **`docs/reviews/THREAT-MODEL-DRAFT.md`.** **Deliberately not opened**, and this is a methodological
  choice rather than an omission: §11's author drafted it, and reading the draft would have told me
  what the author intended rather than what the integrated section says. `:145` asks for independent
  validation of the artifact. I validated the artifact. The cost is that I cannot tell the lead which
  of §11's omissions were dropped during integration and which were never drafted - his stated doubt
  #1. **I can only report that they are absent now.**
- **Anything requiring a live Jobvite call.** No credential, no sandbox. R-1's remedy is
  deliberately chosen to need none: `start=0` is safe under both surviving hypotheses, so it is
  actionable today. Everything else about success shapes remains blocked on
  `CREDENTIAL-CHECKLIST.md`.
- **`src/` and `tests/`.** Empty. Correct for a design round.
