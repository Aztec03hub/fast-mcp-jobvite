# F10 ruling: the caller-replay clause, `backend/resilience.md:146-151`

Fresh reviewer, no stake in the freeze. 2026-08-28. Ruling on F10 alone, plus the freeze-procedure
question the brief attached to it. Every citation below is from `grep -n` or a numbered `awk` window;
no offset was counted inside an unnumbered `sed` window.

---

## 1. What I verified from source

**The clause exists, at the stated lines.** `grep -n` over
`evolv-coder-standards/standards/backend/resilience.md` puts *"Make a write retry-safe by guarding it
with an **idempotency key**"* at `:146`, *"Only then may the write be retried"* at `:148`, and
*"Never auto-retry across an already-committed side effect"* at `:149`. Confirmed.

**The corpus stepped over it, and has since stopped stepping over it.** `STANDARDS.md:313` cites
`:143-145` as B36; `:317` cites `:159-161` as B37. But the brief's premise is one revision stale:
**B108 already exists** (`STANDARDS.md:609-625`), citing `:146-151` directly, and the
`backend/idempotency.md` dismissal row (`STANDARDS.md:781`) has already been reopened in the corpus,
in those words: *"Dismissal reopened by CONF-5 - see B108 ... Live until B108 is answered."*
`DESIGN-R7-CONFIRM.md:308-370` also already ruled on this exact finding, at Medium, with a fix.

Two of the brief's own citations are stale and should not be re-quoted downstream:
`STANDARDS.md:673` is the **rate-limiting** adaptation, not the idempotency dismissal (that is
`:781`); `CONFORMANCE-B1-B106.md:152` is a note about markdown syntax in quoted spans, and **B19 is
at `:186`**.

**What is genuinely still open is narrower than F10 as stated:** `grep -n "idempot\|B108"
docs/DESIGN.md` returns **nothing** in any section - `DESIGN.md` disposes of B107 (§7.2:763-792) and
does not dispose of B108 anywhere. So the live defect is *"a B-number in the corpus that the design
never answers"*, not *"a clause nobody has noticed"*.

**C4-D2 is as described.** `DESIGN.md:1650` - *"a model retrying after a timeout, or a human
approving twice - creating a duplicate candidate and a second email to a live person"*, M x M =
Medium, *"**Detection, not prevention**, and the `409` shape is inferred rather than observed"*,
carried to Residual Risks at `:1759`.

---

## 2. The circularity argument: correct, but narrower than stated

The dismissal has **two** legs, and only one of them is circular.

- Leg A - *"The `Idempotency-Key` HTTP recipe is for inbound mutating endpoints, which this server
  has none of."* **This is sound and I confirmed it against the standard itself.** Every operative
  part of `backend/idempotency.md` is receiver-side: header format (`:55`), server-side Redis
  storage (`:73`), replay semantics (`:94`), the in-flight sentinel (`:108`), a FastAPI dependency
  (`:124`). Its own scope table (`:43-49`) is keyed on the HTTP method **of the route you serve**.
  Nothing in it binds an outbound API client. Reading `:36` (*"mandates the pattern for all unsafe
  mutations"*) as an outbound obligation would be an over-read of exactly the kind this document has
  had to correct twice.
- Leg B - *"B19's tool-level idempotency covers the residue."* **This is circular, as claimed.**
  `CONFORMANCE-B1-B106.md:186` marks B19 SATISFIED because *"§4.3 excludes `create_candidate` from
  retry by construction"*. Never-auto-retrying is a statement about **this server's** retries; the
  residue is a **caller** re-issuing the write. The two do not touch.

So: the dismissal correctly disposed of the *document* and incorrectly disposed of the *residue*, and
the residue rode out on the second leg. **The circularity finding stands.** The corpus already says
so at `STANDARDS.md:619-621`.

---

## 3. The counter-argument F10 has not had to face, and it is a real one

`resilience.md:146-151` sits under the heading **`## Retry only idempotent operations`**
(`resilience.md:136`). Read in place, both bullets address **whoever performs the retry**: `:148`
grants a *permission* (*"Only then **may** the write be retried"*), and `:149-151` forbids the
retrier from auto-retrying across a committed side effect. §4.3 takes the other branch of the same
sentence: it does not retry at all, so the permission is never needed and the prohibition is never
violated.

**On a strict reading, `:146-151` is discharged by construction, and no control is owed.** That
matters for severity: F10's force does not come from an unmet MUST. It comes from the fact that a
**named remedy was never evaluated** before a Medium harm was accepted as residual, and that after
the freeze only an ADR may revisit it. That is a real but documentary defect.

**On the `409`.** It cuts against F10 rather than for it, and the previous rulings did not say so.
If Jobvite really returns `409` on a duplicate candidate, then the downstream **already dedupes** -
which is the outcome `:146-148` asks an idempotency key to produce - and the duplicate record and the
second email are both prevented, not merely detected. That would make C4-D2's *"Detection, not
prevention"* an understatement. But `409` is `[INFERRED]` in every source we hold
(`JOBVITE-API.md:678`, `JOBVITE-CONTRACT.md:160`, `:323`) and is a checklist item for the day a
credential exists (`JOBVITE-CONTRACT.md:674`, row 10). **I am not proposing a re-rating** - unverified
in the design's favour is not a mitigation. It belongs in the disposal as a stated uncertainty.

---

## 4. The Jobvite question, answered as far as the evidence allows

**No idempotency or dedupe key is established on the write in scope, and nothing in the corpus points
toward one.**

- `grep -ci idempot` over `docs/research/JOBVITE-API.md` and `JOBVITE-CONTRACT.md` returns **0** and
  **0**. Confirmed independently.
- The `POST /api/v2/candidate` request body is enumerated at `JOBVITE-API.md:440-457`: `email`,
  `firstName`, `lastName`, `mobile`, `sendEmail`, `application{jobEId, sourceType, source, resume}`.
  **No dedupe, key, or client-reference field.** No idempotency header is documented anywhere in
  either file.
- **The one near-miss, and why it does not rescue the finding.** `JOBVITE-API.md:620` documents
  `importDuplicates` (default `false`) - but on **`POST /v1/contacts`, the Contact Import API,
  Jobvite Engage only** (`JOBVITE-API.md:618`). Different product surface, different endpoint,
  different auth (`api` + `sc` in the query string), and not the write in scope. It is also the wrong
  *shape*: a boolean "import duplicates or don't" is a policy toggle, not a client-supplied key, and
  it cannot distinguish a replayed request from a genuine second submission by the same person.

**Verdict on the mechanism question: cannot be established, and not for want of looking.** Jobvite
publishes no public API documentation at all (`DESIGN.md:84`), there is no sandbox
(`JOBVITE-CONTRACT.md:264`), and this cannot be settled before a credential exists - the same wall
`DESIGN.md` §12 item 1 already names. **Therefore the honest outcome is a stated ceiling, not a
control**, exactly as B108's own second branch (`STANDARDS.md:624-625`) anticipates. The design has
the right precedent already in it: the read-only-key treatment at `DESIGN.md:823-837` /
`:1763`, which states an operator requirement, states that the server cannot verify it, states that
*"whether Jobvite issues read-only keys at all is unknown"*, and declines to tick the box.

This is a **prose fix**, not an implementation obligation. That is the single largest input to my
severity.

---

## 5. The freeze-procedure question: the brief is right, and it is worse than one skip

**Verified: round 6 did not run the conditional-dismissal re-test.** `DESIGN-R5.md:496-499` asked for
it by name - *"§13's conditional-dismissal re-test run against `devops/docker.md` and
`backend/idempotency.md`"*. `grep -n "docker\|idempot\|conditional dismissal" docs/reviews/DESIGN-R6.md`
returns **zero lines**. Positive control: the same grep returns hits in
`DESIGN-R5.md`, `CONFORMANCE-DESIGN-ARTIFACT.md`, `CITATION-RANGE-AUDIT.md` and
`DESIGN-R7-CONFIRM.md`, so the instrument finds these strings where they exist. The step was
requested and skipped.

**So the count is now two.** `architecture/caching.md` tripped unnoticed (`DESIGN.md:1917-1921`);
`backend/idempotency.md` tripped unnoticed and was caught by an audit rather than by the procedure.
The procedure has never once caught its own quarry.

**And `DESIGN.md:1922` is now stale in the worst possible direction.** It reads *"`devops/docker.md`
and `backend/idempotency.md` are the two most likely to have gone live"* - future tense about a
condition that **has already tripped**, in a sentence a freeze reader will use as a to-do list. The
document predicted its own failure and then outlived the prediction without noticing.

**I ran the `devops/docker.md` re-test myself, since nobody had.** Its condition
(`STANDARDS.md:786`) is *"Applies only if a container image ships."*

- No `Dockerfile`, `*.dockerfile`, or `docker-compose*` exists anywhere in the repo (`find`).
- `.github/workflows/` contains only `mirror.yml`; no image build or push.
- §10 (`DESIGN.md:1318-1348`, and `grep -i "pypi|uvx|wheel|publish"`) describes a Python `>=3.12`
  package with pinned dependencies and a PyPI upload (`:1428`). No image is a deliverable.
- The `docker` hits in `DESIGN.md` (`:872`, `:881`, `:915`) are §7.4 discussing SIGTERM in a
  container an **operator** might run us in - not an image we ship.
  `CONFORMANCE-DESIGN-ARTIFACT.md:382-383` reasoned from those hits that *"someone expects one"*;
  that was marked `[REASONED]` and, checked against the tree, it is **not** the case.

**`devops/docker.md`'s condition has NOT tripped. Its dismissal stands, as of this commit
(`90b0504`), tested rather than assumed.** That closes the outstanding half of the R5 request. It
should be recorded as tested-and-standing, because an untested dismissal and a dismissal that was
tested and held are different objects and only one of them needs re-running.

---

## 6. Severity

**F10 on the clause itself: LOW.** The clause is discharged by construction on a strict reading
(§3); no control is owed; no mechanism is known to exist to build one from (§4); the remedy is one
paragraph. I depart from `DESIGN-R7-CONFIRM.md`'s Medium on one point only: it rated Medium because
*"an acceptance made in ignorance of an available remedy is not a valid acceptance"* (`:342`). Having
now looked, **the remedy is not available** - and an acceptance made in ignorance of an *unavailable*
remedy is a documentation gap, not an invalid acceptance. Nothing about the outcome changes when the
paragraph is written; only the reader's ability to see that it was considered.

**The freeze-procedure finding, which I am raising as separate: MEDIUM.** Not because the design is
wrong, but because the *instrument that gates the freeze* has a verified skip at the exact step about
to run, and `:1874` will mislead the person running it. This one is not about F10's subject matter at
all and should not be folded into it.

---

## 7. Suggested fixes

**All four are MY suggestions and must be verified before adoption.** A reviewer's one-line remedy on
this project once turned out to be a mutation the suite kills. In particular, check every `§`
cross-reference and line number below against the document as it stands when you apply it.

### Fix 1 - dispose of B108 in `DESIGN.md` §2.2, after the sentence at `:221`

§2.2 is the better home than §4.3: `:221` already says *"the tool is never retried (§4.3)"*, so the
disposal reads as the continuation of a sentence already there, and §4.3 is about the client's
resilience policy rather than about the write's blast radius.

> **The other replay path, and the ceiling on what we can do about it (B108).**
> `backend/resilience.md:146-151` permits a write to be retried only when an **idempotency key** lets
> the downstream dedupe the replay. We take the other branch of that clause: the server never
> auto-retries `create_candidate`, by construction (§4.3). What that does not reach is a **caller**
> re-issuing the write - a model retrying after a timeout, or a human approving twice - which is
> C4-D2. **We evaluated the remedy the clause names and cannot build it.** Nothing in the research
> corpus establishes that Jobvite accepts a dedupe key on candidate creation: `POST
> /api/v2/candidate`'s documented body carries no such field, no idempotency header appears in any
> source we hold, and the nearest thing Jobvite exposes - `importDuplicates` on the Engage Contact
> Import API - is a policy toggle on a different endpoint of a different product, not a
> client-supplied key. Jobvite publishes no API documentation and there is no sandbox, so this cannot
> be settled before a credential exists (§12, item 1). **We therefore state the ceiling rather than
> claim a control**, on the same footing as the read-only-key requirement in §7.2: the residual
> duplicate is accepted, it is C4-D2, and it is in Residual Risks. **This disposal expires** the day a
> credential or Jobvite documentation shows a dedupe key exists on this endpoint, at which point the
> clause becomes a live obligation on the client.

### Fix 2 - point C4-D2 at the disposal (`DESIGN.md:1650`, and the Residual Risks row at `:1759`)

Append to the mitigation cell, so a reader auditing the residual can see the remedy was considered
rather than skipped. **No re-rating**: L=M x I=M is Medium by the matrix and stays Medium.

> The idempotency-key remedy named by `backend/resilience.md:146-151` was evaluated and is
> unavailable to us; see §2.2 (B108). The `409` may in fact prevent rather than merely detect the
> duplicate, but its shape is inferred and unobserved, so nothing here is claimed on it.

### Fix 3 - rewrite `DESIGN.md:1922`, in place, not appended

> `backend/idempotency.md` **did** go live - reopened as B108 and disposed of in §2.2 - which is the
> second time a conditional dismissal tripped without this procedure catching it. `devops/docker.md`
> was re-tested at commit `90b0504`: no `Dockerfile`, no image build in CI, and §10 ships a PyPI
> package rather than an image, so **its condition has not tripped and its dismissal stands**. Both
> are re-tested at freeze regardless; a dismissal that held once is still a dated claim.

### Fix 4 - add one sentence to the freeze procedure at `DESIGN.md:1917`

Because the procedure's failure is that nobody is accountable for running it:

> **The re-test is a numbered step of the freeze, not a review's discretion.** Round 5 asked round 6
> to run it (`DESIGN-R5.md:496-499`) and round 6 did not, which is how `backend/idempotency.md`
> reached an audit instead of the procedure. Freezing without a written re-test result for **each**
> conditional dismissal is not a freeze.

---

## 8. Verdict

**On F10 alone: DO NOT FREEZE - but the blocker is small, prose-only, and closable today.**

To be plain about why, because "Low" and "do not freeze" look contradictory: the severity of the
*exposure* is Low. The blocker is **mechanical**. `STANDARDS.md:781` currently reads *"Live until
B108 is answered"*, and `DESIGN.md` answers B108 nowhere. Freezing now would freeze a document that
leaves a live B-number undisposed, at the same moment §13 promises every conditional dismissal is
re-tested at freeze. That is not a judgement about idempotency; it is that the document would
contradict its own procedure on the page where the procedure is written.

**Apply Fixes 1-4, confirm `grep -n "B108" docs/DESIGN.md` is non-empty and `STANDARDS.md:781` is
updated from "Live until B108 is answered" to disposed, and F10 no longer blocks. I see nothing else
in this finding that should hold the freeze.**

## What I did not verify

- **Whether Jobvite accepts a dedupe key.** Unsettleable from here; it needs a credential. This is
  the one item in this document I could not close by looking harder, and §4 says so rather than
  parking it.
- **Whether `409` is returned on duplicate candidate creation.** Same wall. Already a checklist row
  (`JOBVITE-CONTRACT.md:674`).
- **The server-side dedupe option** floated at `DESIGN-R7-CONFIRM.md:364-370` (a seen-set, on the
  §4.5 pattern). I did not design or cost it. My Fix 1 wording does not mention it; if you want it on
  the record as considered-and-rejected, that is a decision for the author, not a review finding.
