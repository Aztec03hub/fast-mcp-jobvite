# Citation audit of `CONFORMANCE-B1-B106.md`

**Task:** CONF-3 · **Auditor:** gate-and-citations · **Date:** 2026-08-27 05:30 PM CDT

**Subject under test:** `docs/reviews/CONFORMANCE-B1-B106.md` (106 obligations, authored by
`conformance-sweep`, never audited by anyone but its author).
**Authority:** `/home/plafayette/claude_projects/evolv/repos/evolv-coder-standards/standards/`,
re-opened at every coordinate.
**Auditor independence:** I did not write this document, `DESIGN.md`, or any ADR, and I edited none
of them during this pass.

---

## 1. Headline

**No fabrications. One wrong coordinate, off by one line and harmless. One substantive
verdict-3 defect, at B103.** The document is in materially better shape than the artifacts audited
before it.

The finding that outlives this pass is not a count. It is that **the document's author identified a
citation defect class at B76, called it "one imprecision short of a defect", and did not then check
whether it recurred. It recurs five more times.** One of those recurrences, B103, is a real
verdict-3 defect: the coordinate resolves, the quotation is real, and it does not support half the
sentence citing it.

| Verdict | Count | Severity |
|---|---|---|
| **1 - coordinate wrong, clause elsewhere in the same file** | **1** (B40) | Trivial. Off by one at the start of a range. |
| **2 - quoted text exists nowhere in the cited file (fabrication)** | **0** | - |
| **3 - coordinate resolves, quotation real, does not support the citing sentence** | **1 substantive** (B103) + **4 minor** (B54, B92, B100, and B76 as the author recorded it) | B103 is the one that matters. |
| Sound at the cited coordinate | 114 of 116 | |

**Scope of those counts:** 116 citations that carry both a `file:line` and a quotation, spread over
99 of the 106 B-numbers. The remaining rows cite code identifiers or line ranges without a
quotation; those are covered separately in §6.

---

## 2. Verdict 2 - fabrications

**None. Zero of 116.**

Every quoted span resolves to real text in the file it is attributed to. This is a clean result and
it is worth stating plainly, because the last two audits on this project each expected fabrications
and the expectation has now been wrong twice.

**Why this clean zero is trustworthy.** A zero that explains itself is the shape of a broken
instrument, so the resolver was positive-controlled before its output was believed. Three mutations
were injected into a copy of the document and the tool was required to catch each:

```
--- CONTROL: fabricated quote on B1
    [VERDICT 2 candidate: not found in file] B1 @ CONFORMANCE:129  architecture/error-contract.md:204
--- CONTROL: wrong coordinate on B2
    [VERDICT 1 coord wrong] B2 @ CONFORMANCE:130  architecture/error-contract.md:9 -> clause found at line(s) [66]
--- CONTROL: line past EOF on B2
    [V1/V2 PAST EOF] B2 @ CONFORMANCE:130  architecture/error-contract.md:9999  (file is 226 lines)
document restored byte-identical: True
```

All three fired, and the wrong-coordinate control also correctly recovered the true line. The
document was restored byte-identical after each mutation.

**Two rounds of my own false positives, recorded because they were mine and not the document's.**
The resolver first reported 20, then 7 verdict-2 candidates. Every one was an artifact of my
normaliser: escaped table pipes (`\|`), markdown link syntax inside a quoted span, and multi-bullet
quotations rendered by joining the bullets with `-`. All were the instrument, not the document. The
prior audit hit the same class and called it correctly; I repeated the mistake before reading its
note.

---

## 3. Verdict 1 - wrong coordinates

### V1-1 (trivial): B40's range starts one line late

B40 cites `ai/tool-calling.md:173-175` for:

> *"Use the canonical triple verbatim: HTTP header `X-Request-ID`, log field `request_id`,
> ContextVar `request_id_var`"*

The quoted sentence begins with **"Use"**, and `grep -n` puts that word at the end of `:172`:

```
172:   redacted), result status, latency, and the request correlation id. Use
173:   the canonical triple verbatim: HTTP header `X-Request-ID`, log field
174:   `request_id`, ContextVar `request_id_var` (see CLAUDE.md "Correlation ID
```

The cited range should be `:172-175`. **Nothing rests on this.** The clause is real, the obligation
is real, and B40's verdict does not move. Recorded for completeness, not for action.

**No citation points past EOF, and no cited file is missing.** The `error-contract.md:290` defect
the author found in STANDARDS.md (their CD-3) has no counterpart inside this document.

---

## 4. Verdict 3 - the one that matters

The test applied throughout: **put the quoted clause and the citing sentence side by side and ask
whether they can share a paragraph without visibly disagreeing.**

### V3-1 (SUBSTANTIVE): B103 claims 14 required sections and cites the list of *locations*

**The citing sentence** (B103's Requires column):

> A README exists at the repo root **with all 14 sections**

**The only citation on the row**, `documentation/readme-standard.md:34-35`:

> *"- The top level of every Git repository. - The root of every published package (npm, PyPI,
> Cargo, Go module, container image, Helm chart)."*

Those two lines are the second and third bullets of a list answering **where a README is
required**. They are the whole of `## When to apply`. They say nothing whatever about sections,
their number, their order, or their headings. The citation supports *"a README exists at the repo
root"* and stops there. **The "all 14 sections" half of the claim has no citation at all.**

This is not a coordinate error and not a fabrication. `:34-35` resolves, the quotation is verbatim,
and the sentence it is attached to asserts something the quotation does not carry. It is invisible
to any resolver that only checks whether the text is there.

**The clause that would have carried the claim is uncited, and it is in the same file.**
`grep -n` on `readme-standard.md`:

```
41:## Required sections
43:Every README MUST contain the following sections, in this order. Section headings must match exactly so that automated checks can locate them.
```

`readme-standard.md:43` is the clause. It carries `MUST`, the ordering requirement, and the exact
heading rule - every element of B103's claim.

**And the document already knows this**, which is what makes it a defect rather than an oversight.
**B77 cites `:43` correctly**, with the list at `:45-58`. B103 is described in its own evidence
column as a *"Restatement of B77 with a second trigger"* - and in restating it, it kept B77's claim
and swapped in B77's *trigger* citation for B77's *content* citation. The two halves of the
sentence come from two different clauses and only one was carried across.

**Consequence.** B103's verdict is PARTIAL and B77's is UNADDRESSED, so the compliance conclusion
does not move. What moves is the evidence: anyone who follows B103's citation to check the
14-section requirement lands on a list of locations and finds no requirement there. Given that this
document is the source of several design citations, that is precisely the propagation path worth
closing.

**Fix:** add `documentation/readme-standard.md:43` to B103, keeping `:34-35` for the location half.

### V3-2 to V3-5 (MINOR): the binding lead-in is uncited - a class, not four accidents

The author found this once and wrote it up at **B76**:

> *"The obligation is real and the path is where STANDARDS.md says; only the clause that makes it
> binding is elsewhere."*

They classified it as *"One imprecision short of a defect"* and did not test whether it recurred. A
mechanical sweep for the pattern - a citation pointing at an enumerated item or table row that
carries no modality of its own, where a lead-in within the preceding lines does - returns **six
hits**:

| B | Cites | Cited text carries no obligation | The binding line, uncited | Disclosed in prose? |
|---|---|---|---|---|
| B45 | `observability.md:636` | `- Log sensitive data (passwords, tokens, PII)` | `:634` `### Don't` | **Yes** - row says "(under **Don't**)" |
| B88 | `observability.md:636` | same | `:634` `### Don't` | **Yes** - row says "(under **Don't**)" |
| **B92** | `agentic-coding-standard.md:127` | `- Hardcodes secrets, API keys, or passwords` | `:126` `# NEVER generate code that:` | **No** |
| **B54** | `agentic-coding-standard.md:153` | `\| Python \| cryptography, bcrypt, argon2-cffi \|` | `:146` `- Approved cryptographic libraries only` | **No** |
| **B100** | `quality-gates.md:50` | `- [ ] Completed PR template` | `:48` `PR must include:` | **No** |
| **B103** | `readme-standard.md:34-35` | the locations list | `:32` `A README.md is **required** in...` | **No** - and see V3-1 |

**B45 and B88 are sound and should not be counted against the document.** Both disclose the
governing context in the citation itself. That is the correct way to cite an item under a `Don't`
heading, and it is the standard the other four fail to meet.

The remaining three minors are low consequence individually:

- **B92** (SATISFIED). Cited alone, `- Hardcodes secrets, API keys, or passwords` reads as a
  description of behaviour, not a prohibition. The prohibition is `:126`, `# NEVER generate code
  that:`. The row's second citation, `development-workflow.md:280` - *"- [ ] No secrets or
  credentials in code"* - independently carries the claim, so nothing is left unsupported. Worth
  noting separately: `:126`'s scope is **generated** code, while B92's claim is about source
  generally.
- **B54** (NOT-APPLICABLE). The word **"only"** in *"Approved crypto libraries only"* comes from
  `:146`, not from the table row at `:153`. The verdict is NOT-APPLICABLE, so nothing rests on it.
- **B100** (UNADDRESSED). The modality is `:48` *"PR must include:"*. The row's other citation, the
  verbatim template at `development-workflow.md:202-241`, carries "the mandated sections". Adequate
  across the pair.

**Why the class matters more than its four instances.** Every one is the same move: cite the item,
not the sentence that makes the item binding. It survived a self-audit that had already named it
once. At B103 it produced a real defect. The recommendation is not to fix four lines but to make
the check routine, and it is mechanical: *a citation whose target is a list item or table row with
no modality of its own must either cite the lead-in as well, or name it in prose the way B45 and
B88 do.*

---

## 5. The advisory-file question

**Asked:** does any B-number treat `architecture/caching.md`, or a similarly advisory file, as
binding?

**For `caching.md` the answer is a clean absence: `CONFORMANCE-B1-B106.md` never cites it.**
`grep -n "caching.md"` over the document returns nothing. No B-number treats it as binding because
no B-number treats it at all.

The file is genuinely advisory, and by more than the absence of `MUST`. It contains no
`MUST`/`REQUIRED`/`shall`, and also no `should`, `prefer` or `recommend`; its Purpose reads
*"This standard defines caching strategies and patterns for full-stack applications using Next.js,
FastAPI, Redis, and PostgreSQL."* It is a pattern catalogue with `priority: required` frontmatter.

**The over-reading of `caching.md` did happen - in `DESIGN.md`, not here, and it is already fixed.**
`CITATION-AUDIT.md`'s C-2 caught `caching.md:833` being cited as a requirement when it is a
checklist tick reading "when needed", and `DESIGN.md:836` now presents the file *"at its actual
strength"*, saying `caching.md:841` *"agrees rather than compels"*. Nothing further is owed here.

### A corpus-wide inference I nearly reported, and why it was wrong

Grepping the corpus, **105 of 172 standards files contain no `MUST`, `REQUIRED` or `shall`**. Read
naively that says the audit cites advisory files constantly: `prompt-injection.md`, `python.md`,
`agentic-coding-standard.md`, `reference-architecture.md`, `development-workflow.md` and
`testing-strategy.md` are all on that list, and B24, B25, B26, B52, B92 and B97 all rest on them.

**That inference is false, and reporting it would have been the more damaging error.** The absence
of RFC 2119 keywords is a fact about my grep, not about whether a file binds.
`ai/prompt-injection.md` carries no `MUST` anywhere, and its Purpose reads:

> *"This standard defines the threat model and mandatory controls against **prompt injection**"*

It is organised as `## Rule 1 - Separate instruction and data channels`, and states
*"**Never concatenate untrusted input into the system or developer prompt.**"* A file that says
"mandatory controls", numbers its rules, and prohibits by "Never" is binding whether or not it
spells `MUST`. **B24, B25 and B26 are correctly treated as binding**, and B25 is the obligation
`DESIGN.md` §2.1 and the §11 row `C3-T1` were just built to satisfy - so getting this wrong would
have argued for removing a control that should stay.

The real distinction is framing, not keyword presence: `prompt-injection.md` declares mandatory
controls, `caching.md` defines strategies and patterns. **`caching.md` is the exception in this
corpus, not the archetype.** No further advisory-as-binding instance was found.

---

## 6. Two things that look like defects and are not

**Table rows quoted with trailing columns dropped.** B30, B52, B54, B56, B57, B62, B63, B68, B96
and B97 quote table rows as `| Services | 90% |` where the file reads
`| Services | 90% | Business logic requires thorough testing |`. The example or rationale column is
dropped inside the quotation marks. This is applied consistently across the document, it never
changes a meaning, and the retained cells are verbatim. **B97** additionally joins three rows across
an elision. **Recorded as a convention, not a defect** - though a reader reconstructing a table from
these quotations will get a narrower table than the file holds.

**Paraphrase inside quotation marks in the Evidence column - four instances, minor.** Of 78
design-side quotations, 74 resolve verbatim against `DESIGN.md` (current or revision 2), the
standards corpus, or `STANDARDS.md`. Four are near-verbatim rather than verbatim:

| B | Rendered as a quotation | The document actually reads |
|---|---|---|
| B31 | *"a new Jobvite field is dropped until someone adds it deliberately"* | `an unlisted field is dropped until someone adds it deliberately` (§11, `C6-I2`) |
| B55 | *"95% line and 90% branch on critical paths"* | `95% line with 90% branch on` (`DESIGN.md:950`) |
| B58 | *"CI runs --collect-only against the live suite and fails on a collection error"* | `CI runs \`--collect-only\` against it and fails on a collection` (`DESIGN.md:887`) |
| B99 | *"single main branch rather than the mandated main+develop GitFlow"* | not located as a quotation; reads as the author's own summary |

No meaning changes in any of the four. The rule they cross is the one this project has already had
to correct once: **inside quotation marks, reproduce the source exactly.** Substance unaffected.

---

## 7. What I did NOT check, and why

Listed because an absence is a claim about where I looked, and because a cheap item parked here
reads as rigour while costing the reader the time I saved.

1. **Whether each B-number's *verdict* about `DESIGN.md` is correct.** This is a citation audit. I
   checked whether the quoted standard says what the row claims it says; I did not re-derive whether
   `DESIGN.md` satisfies it. A citation can be perfect under a wrong SATISFIED. **This is the
   largest uncovered area and the obvious next pass.**
2. **The 7 B-numbers with no quoted span** (B7, B55, B63, B69, B93, B95, and the code-identifier
   halves of B53 and B68). These cite code identifiers and line ranges - `fetch-depth: 0`,
   `trufflesecurity/trufflehog@v3.88.0`, the `Settings(BaseSettings)` block - which the
   quotation-matcher cannot process. **I did not verify these by hand.** They are a genuine hole in
   this pass, roughly 7 percent of the rows, and I am recording it rather than implying coverage.
3. **Whether the B1-B106 obligation list is itself complete** against the standards corpus. That was
   CONF-1's and CONF-2's job. An obligation nobody wrote down cannot be found by auditing citations.
4. **`STANDARDS.md` as an intermediary.** The document states it treated STANDARDS.md as a secondary
   source and quoted from the standards files directly. I verified the quotations against the
   standards files, which is the stronger check, so I did not separately audit STANDARDS.md.
   CD-1, CD-2 and CD-3 in §2 of the subject document are defects *in STANDARDS.md*, and I did not
   re-verify them.
5. **Non-`.md` sources.** No citation in the document points at one.

---

## 8. Recommended actions

| # | Action | Priority | Status |
|---|---|---|---|
| 1 | **B103: add `documentation/readme-standard.md:43`**, the `MUST` clause carrying "all 14 sections". Keep `:34-35` for the location half. | **Do this one.** | **APPLIED** |
| 2 | B92, B54, B100: cite the binding lead-in (`:126`, `:146`, `:48`) alongside the item, or name it in prose the way B45 and B88 already do. | Low | **APPLIED** |
| 3 | B40: widen the range to `:172-175` so it starts where the quoted sentence starts. | Trivial | Open |
| 4 | B31, B55, B58, B99: make the four Evidence-column quotations verbatim, or drop the quotation marks. | Trivial | Open |
| 5 | Audit the 7 code-identifier citations left unchecked here (§7 item 2). | Medium | Open |
| 6 | Re-verify the *verdicts*, not the citations (§7 item 1). | Medium - the largest remaining gap | Open |

Nothing here blocks a freeze. **Action 1 is the only one that changes what a reader would conclude
from following a citation.**

### Actions 1 and 2, as applied

Four rows now cite the clause that makes the item binding, alongside the item itself. Each added
coordinate was taken from `grep -n` on a distinctive phrase and re-checked against the file:

| B | Added | Quoted verbatim from the file |
|---|---|---|
| B103 | `readme-standard.md:32` and `:43` | *"A `README.md` is **required** in each of the following locations:"* and *"Every README MUST contain the following sections, in this order. Section headings must match exactly so that automated checks can locate them."* |
| B92 | `agentic-coding-standard.md:126` | *"# NEVER generate code that:"* |
| B54 | `agentic-coding-standard.md:146` | *"- Approved cryptographic libraries only"* |
| B100 | `quality-gates.md:48` | *"PR must include:"* |

The second coordinate in each pair uses the relative `` `:NN` `` form, which is the style B45 and
B77 already use, so the total citation count is unchanged at 116.

**Re-run after the edit:** the lead-in sweep that found six instances now returns **0 rows citing
enumerated content with an uncited binding lead-in**, and all 116 citations still resolve at their
coordinates. B92's addition also records that `:126`'s scope is *generated* code, with
`development-workflow.md:280` carrying the claim for source generally.

**No verdict changed.** These are evidence fixes: every affected row keeps the SATISFIED,
NOT-APPLICABLE or UNADDRESSED verdict it already had. Nothing in `DESIGN.md` or any ADR was
touched.
