# FIX-3 - applying R3's unapplied findings, R4's H2/H3/H4, and the structural remedy

**Task:** #27 - **Agent:** `fix-applier` - **Date:** 2026-08-27
**Subject:** `docs/DESIGN.md`, 1234 lines at R4, 1300 lines now.
**Result:** all assigned items applied. `docs/reviews/check-coupling.py` PASSES, and eight positive
controls prove it can fail. Two items are referred to Phil rather than decided.

Baseline: `90a9f51`, working tree clean at start. Nothing committed or pushed.

---

## Step 1 - the mechanical diff R4 asked for, run first

### `PENDING-DESIGN-CHANGES.md` is not the register R4 assumed it was

R4's closing map says *"somebody should diff those two files against `DESIGN.md` directly; that is
a mechanical check that would have found H6 in five minutes"*. **It would not have.** I opened it:
`PENDING-DESIGN-CHANGES.md` is the P1-P19 runtime-spike staging file, whose own header
(`:1-6`) says it is temporary and deleted when applied. It carries spike results, not review
findings, and it is **stale in one load-bearing way**: P19 reinstates `create_candidate` behind
**three** gates including a confirmation token, and §2.2:128-136 records that the token was
subsequently cut, leaving two. Diffing it against `DESIGN.md` would have produced a false
finding, not H6.

**The register that would have found H6 is `DESIGN-R3.md`'s disposition table (`:333-357`).** That
is what I diffed. `PENDING-CONFORMANCE-FIXES.md` is out of scope for this task and I did not open
it beyond confirming its subject.

### R3's accepted findings against `DESIGN.md` as it stood at the start of this task

| R3 finding | R3 disposition | State when I started | Where it is now |
|---|---|---|---|
| R-1 paging under-read | Accepted | **Applied** (commit `cc3b5b8`), and H1's follow-on scoping applied in `90a9f51` | §4.5:287-308 |
| R-2 coupling claim false on C6-I, C7-I, C2-R | Accepted, add three §8 cases | **Two of three applied.** C6-I and C7-I closed; **C2-R never closed** - this is R4's H2 | §8:776-781; §11:1082 |
| R-3 caller identity is HTTP-only; reconcile §11 | Accepted, modified | **Half applied.** §5.3:390-402 qualified by transport; §11's C1-R row never reconciled | §11:1071 |
| R-4 `JOBVITE_TOOLS` semantics | Accepted, three limbs | **Applied in §7.3:534-544**; R4's m4 (the table at `:554` and §2.2:125 not updated, no §8 case) is **out of my brief** and still open | unchanged |
| R-5 §5.1 asserts B12/B23 met | Accepted, promoted | **Half applied.** B12 closed (R4 verified this at the file); the B23 unbounded-loop arm is R4's m2, **out of my brief** and still open | unchanged |
| m1 cut probe still live in §1 and §12 | Accepted | **Not applied** | Applied - §1:20-24, §12:1243-1245 |
| m2 §12 Q4 answered inside the document | Accepted | **Not applied** | Applied - question removed, §12:1260-1262 |
| m3 §8 requires tests for the cut token | Accepted | **Not applied** | Applied - bullet deleted from §8 |
| m4 post-write warning routing / success-with-warning shape | Accepted | **Half applied.** stderr routing landed at §5.3:416-418 | Second limb **NOT applied** - see "Refused", below |
| m5 C7-E gives no reason | Accepted | **Not applied** | Applied - §11:1153 |
| m6 `resilience.md:226` ambiguous and clipped | Accepted | **Not applied** | Applied - §11:1126 now `backend/resilience.md:224-226`, verified at the file |
| m7 threshold selection rule omits C4-S | Accepted | **Not applied** | Applied - §11:1182-1189 |
| m8 confirmation-token residue, four survivors | Held for rerating | **Not applied** | Applied - all four removed |

**R3 Job 2 (threat-model validation) is a separate finding set and I did not audit it.** Its
`A-miss-1` (the calling model's context as an asset), `A-miss-2` (the build and its inputs) and
`A-miss-3` (the `JOBVITE_TOOLS` enable surface) are **not** in the Assets table now. I drafted
A-miss-2 and a matching trust boundary, then removed them as outside this brief. **Somebody should
confirm whether those three were dispositioned**; commit `65ac2b9` is titled "Extend the threat
model with the three gaps its validation found" and what it added was the C9 block, the C4-D
duplicate-write row and C7-I log retention, which are `M-1`-class gaps, not the missing assets.

---

## Step 2 and 3 - what was applied

### H2 - the coupling claim, and the structural remedy that retires it

**Remedy applied as R4's BLUE final specified**, not by adding two tests and restating the
sentence.

1. **Every STRIDE row now has a unique id**, `C<n>-<STRIDE letter><k>`, with the index **always
   present** so a second row added later never renames the first (§11:1003-1007). R4's m6 named
   five colliding ids; there were **six** - it missed `C8-E`, which named both the
   `JOBVITE_ENABLE_WRITES` row and the TLS-assertion row. The convention paragraph says six.
2. **Every row has a `Test` column** naming either the §8 case or an explicit disposition. The
   `Component`/`Category` pair was replaced by the id, so the tables stayed at seven columns and
   the C4 addendum and C9 now use the same header as everything else, which also closes R4's n5.
3. **The universal sentence at the old `:997-998` is deleted**, along with the "it did not hold on first
   writing" paragraph and the 184-line-distant escape clause at the old `:1184-1186`. §11:1029-1034
   records why, in the document's own register.
4. **The C1 escape clause was removed rather than relocated.** R4 accepted "or in C1's case a
   startup check". I did not keep it: §7.1:486-490 specifies a startup refusal, and a startup
   refusal is unit-testable credential-free, so §8:790-793 now requires it. C1-S1, C1-T1 and C1-I1
   name a real §8 case. **Three High rows rested on an escape clause and now rest on a test.**

**C2-R closed with a test, not a smaller claim.** §8:776-781 adds *"the audit event is emitted and
carries its mandated fields"*, asserted positively. The reviewer's charge that the PII case
*"passes trivially against a server emitting no audit event"* was correct; §8:782-785 now states
that the two cases are paired so neither can be satisfied by silence, and the PII case asserts
against the event the new case proves exists. **This single case closes C2-R1, C1-R1 and C4-R1.**

**C9-T closed with a test, and honestly split.** §8:794-798 adds *"the manifest pins `mcp` and the
frozen resolve has no lock drift"* - credential-free, runnable in CI, and covering the two legs of
C9-T1's mitigation that are real (`mcp==2.1.1` at §10:867, `uv sync --frozen` at §10:880). **The
third leg, the `fastmcp inspect` drift diff, is not a test and I did not pretend it was**: it is a
CI gate, it is unexecuted, §10:914-916 already carries the `UNVERIFIED:` marker, and it is now a
row in Residual Risks (§11:1233).

### H3 - C1-R and C4-R reconciled

**Which is true: §5.3.** I checked rather than assumed. §5.3:384-402 is normative design text that
states both remedies performed, and both remedies are things the design *does*, not things it
merely aspires to; §11's rows were the stale half, written before §5.3 was qualified in R3's
fix pass and never revisited. §11's own convention 1 makes this coherent - Risk is inherent risk,
so the rating stays High and the disposition changes from Unmitigated to Mitigated.

- **C1-R1** (§11:1071) now reads Mitigated in §5.3, **and carries the transport qualifier R3's R-3
  asked for and never got**: HTTP records the resolved client id; stdio records that attribution is
  unavailable rather than emitting `"global"`. The unqualified remedy an implementer would have
  followed on stdio is spelled out as the trap it is.
- **C4-R1** (§11:1107) now reads Mitigated in §5.3, with `approval_state` and the mechanism.
- Both come off the must-mitigate table.

### H4 - the six orphaned rows carried into the outputs

- **`:1112`'s false claim is now true.** The C4-D note (§11:1114-1118) says the duplicate write is
  C4-D2 and is in Residual Risks, **and it is** (§11:1228). The sentence also records that an
  earlier revision asserted the placement in the same edit that failed to make it.
- **C9-D1** added to the mitigate-before-production list (§11:1209-1211).
- **C9-I1** added to Residual Risks (§11:1232); its own cell called it residual and unmitigable.
- **C9-T1** placed: mitigated at High by the pins and frozen resolve, with the unexecuted diff in
  Residual Risks. It joins the "already mitigated at Critical or High" roster.
- **C9 moved to sit after C8**, so the analysis reads C1 through C9 in order. That was R4's n5 seam.
- **The count is recomputed and the arithmetic is written out** (§11:1198-1206): seven, then five,
  now **three** - C5-R1, C5-E1, C8-I1. "Down from seven to five" is gone.

### R3's minors

- **m1** - §1:20-24 now says **one** mechanism is unexecuted and states plainly that the probe does
  not exist. §12:1243-1245 rewritten. R4's n2 falls out of the same edit.
- **m2** - the `status`-block question deleted from §12 and the remaining items renumbered 1-5;
  §12:1260-1262 records that it was answered by §8's structural fixture and `JOBVITE-API.md:397`.
- **m3** - the token-test bullet deleted from §8.
- **m5** - C7-E1 (§11:1153) gives its reason and points at C7-I1/C7-I2 for the exposure.
- **m6** - `backend/resilience.md:224-226`, and the row now states what the clause requires.
- **m7** - the selection rule (§11:1182-1189) distinguishes "unmitigated with a server-side remedy
  an action item can name" from "unmitigated with no available remedy, accepted and carried to
  Residual Risks", and names **C4-S1** as the one such row, which is exactly what the old rule
  selected and then silently omitted.
- **m8, all four survivors** - the Confirmation-token HMAC key asset row deleted; "C4-T token
  binding" removed from the mitigated roster; the C4-S1 residual-risk rationale no longer offers
  the cut token as defence in depth for the document's highest residual risk; the entire
  preview-then-create residual-risk row deleted.

---

## The coupling check, and proof that it can fail

`docs/reviews/check-coupling.py`. No dependencies, reads only `DESIGN.md`.

```
$ python3 docs/reviews/check-coupling.py docs/DESIGN.md
docs/DESIGN.md: 60 STRIDE rows, 17 Critical/High (13 mitigated, 4 not).
PASS: ids unique, STRIDE coverage complete, every mitigated Critical/High row names a §8 case that
exists, every unmitigated one is disposed of, and every id the closing tables name is defined.
```

**A green that has never been shown to go red is worth nothing**, and this claim has been asserted
green three times already. Eight positive controls, each a one-line mutation of a copy of
`DESIGN.md`, each confirmed to make the script exit 1:

| # | Mutation | Output |
|---|---|---|
| 1 | `C1-S2` renamed `C1-S1` | `duplicate row id 'C1-S1'` |
| 2 | the `C7-E1` row deleted | `component C7 has no row for STRIDE E` |
| 3 | the audit-event `Test` cells changed to `residual` | `C1-R1 / C2-R1 / C4-R1 is a mitigated High row but its Test cell names no §8 case` |
| 4 | the §8 startup-refusal case deleted, §11 unchanged | `C1-S1 / C1-T1 / C1-I1 names §8 case '...', which does not appear in §8` |
| 5 | `C5-E1` deleted from the must-mitigate table | `C5-E1 is an unmitigated High row and appears in neither the must-mitigate table nor Residual Risks` |
| 6 | must-mitigate table renamed `C5-R1` to `C5-R9` | `closing tables reference 'C5-R9', which no STRIDE row defines` |
| 7 | `C9-T1` dropped from the mitigated roster | `roster omits C9-T1, a mitigated Critical/High row` |
| 8 | `C5-R1` added to the mitigated roster | `roster claims C5-R1 is a mitigated Critical/High row; it is not` |

Control 4 is the one that matters most: it is H2's exact failure mode, a §8 case disappearing under
a §11 claim that still names it, and it is now impossible to land silently.

**Run it in CI.** It costs milliseconds and it is the only thing standing between this document and
a fourth wrong assertion of the same claim.

---

## Citations, checked at the file

Every `file:line` I touched or relied on was opened with `grep -n` rather than counted off a window.

| Citation | Verdict |
|---|---|
| `backend/resilience.md:224-226` | **Correct.** `:224` is "Log every **retry attempt**", running to `:226` "correlation field". R3's m6 asked for exactly this form |
| `readme-standard.md:67`, `:70`, `:83` (§10.1, applied before this task) | **All three correct.** Note R4's H5 quoted the anti-pattern as `:88`; it is `:83`, and the applied fix used the right line. R4 was wrong, the document is right |
| `threat-modeling.md:86-88` | Correct |
| `agent-guardrails.md:40`, `:79`, `:121-123`, `:122` | **All correct.** R4 listed `:79` and `:122` as citations nobody had re-verified. They resolve |
| `input-validation.md:223-226` | **Correct.** R4 also listed this as unverified. `:223-226` are the four limit rows |
| `JOBVITE-API.md:397` | Correct - "A success body DOES carry a `status` block" |
| **`JOBVITE-API.md:401`** | **WRONG, and it was in the document twice.** The `start=0` observation is at **`:399`**; `:401` is the handling note. Fixed at §1:24 and §4.5:291. This is a recurrence of the false-citation class in the paragraph R4's own n1 asked to have this citation added to, and **R4 propagated the wrong number itself** |

---

## What I refused to apply, and why

**R3 m4's second limb - the "success with a warning" shape** (R4's n6). §5.3:414 mandates the
response; §5.1:328 says *"No `success: true/false` envelope exists anywhere in this repository."*
Specifying what a caller actually receives is **a design decision about the error contract**, not
the application of one already taken, and the two candidate shapes (a warning member on the success
payload, or a second problem-shaped object beside it) have different consequences for §5.1's
"problem objects are the primary channel" rule. **Referred to Phil.** Everything else R4 lists as
accepted-but-unapplied is applied.

**R4's m9 - the two contestable C9 ratings.** C9-I1's L=Low and C9-D1's I=Low are the two inputs
that keep C9 out of the must-mitigate table, on a stack that deliberately ships a beta framework
and a transitive prerelease. **Rerating is a decision, not an application.** I did not touch either
rating; I recorded the contest inside C9-I1's Residual Risks rationale (§11:1232) so a reader meets
it rather than having to reconstruct it from R4. **Referred to Phil.**

---

## Out of my brief and still open, listed so nobody reads this as a clean sweep

- **R4 m2** - §5.1:351 still asserts B23 is met; the unbounded-loop arm still has no §8 case.
- **R4 m3** - §7.5's `send_email` approval-payload requirement still has no §8 case, and the
  "an approval obtained without showing the email is not an approval for the email" claim still
  reads as a claim about what the approver saw.
- **R4 m4** - §7.3:554's requirements table and §2.2:125 still omit the `JOBVITE_TOOLS` conjunct;
  §8 still has no `JOBVITE_TOOLS` case.
- **R4 m5** - §4.5 still states the `total` check without the observed-on-one-resource qualifier,
  and does not state the §9-hazard-5 interaction.
- **R4 m8** - C9-S1 still claims `uv.lock` "with hashes" and C9-E1 still claims hatchling; §10 says
  neither. I left the mitigation text alone deliberately rather than softening a claim I was not
  asked to adjudicate.
- **R4 n3** - the status block at §1:3-8 still omits rounds 3 and 4 and still says
  *"Frozen at 0C/0H/0M"* in the present tense while four rounds have returned findings. That
  sentence is now the most visibly false line in the document.
- **R4 n4** - §10:987 still says the prose paste is "the incident we actually had" while B6 says
  the PDF was; there were two.
- **R3 Job 2 A-miss-1/2/3** - see Step 1.

## Two changes I made that nobody asked for, flagged rather than buried

1. **The `[NEW]` markers are gone from §11.** Six rows carried them. They marked "added since the
   last revision" and the rewrite dropped them. If they are load-bearing for a reviewer tracking
   what moved, they need re-adding against this revision, not the last one.
2. **`C4-E2` removed from the mitigate-before-production list.** Its row says "Mitigated" in plain
   text, so listing it among *unmitigated* Mediums was a contradiction. I resolved it in favour of
   the row. If the row is the wrong half, say so and it goes back.

Also removed: the seven-line duplicate conventions block at the old `:1006-1012`, which restated
`:985-995` in compressed form (R4's m7, accepted as editorial). Nothing in it contradicted the
block above it.
