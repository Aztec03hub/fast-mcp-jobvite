# Pending fixes from the B1-B106 conformance sweep

Staged rather than applied, because `design-review-r2` is reading `DESIGN.md` and moving the
document under a reviewer produces findings against text that no longer exists. Applied in one
pass with the round-2 findings. **This file is deleted when applied.**

Source: `docs/reviews/CONFORMANCE-B1-B106.md`. Counts: 42 SATISFIED / 22 PARTIAL / **37
UNADDRESSED** / 5 NOT-APPLICABLE.

---

## C0 - Citation defects, all three verified by me at source

**CD-3 is the one that matters, and it is in a load-bearing place.**

`DESIGN.md` sources the `instance` semantics to `architecture/error-contract.md:290`. **That file
is 226 lines long. Line 290 does not exist.** The quote is real and sits at **`:83`**, verified:

> `| instance | string | yes | URI of the request that generated the error |`

This is the clause §5.1 leans on to justify substituting `urn:fast-mcp-jobvite:invocation:<request_id>`
for a request URI. **The substitution currently rests on an uncheckable line number.** Fix the
citation to `:83`; the argument itself survives intact.

Also confirmed at source, an off-by-one where two obligations swapped onto each other's neighbours:
- **CD-1:** the `print()` clause is `agentic-coding-standard.md:172`, not `:173`.
- **CD-2:** "No commented-out code blocks" is `:173`, not `:174`. Line 174 is blank.

And one imprecision to tighten: B76 cites `:93-96` where the path lives, but the binding language
is the heading at `:66`, "### Always Protected (Never Auto-Modify)".

---

## C1 - The RFC 9457 uniformity claim has a THIRD hole, and it is unadmitted

§5.1 admits two exceptions: a rate-limit refusal raises `MCPError`, and an abandoned approval never
resolves. **There is a third, on the most common failure path of all.**

A schema violation is caught by FastMCP **before the tool body runs**. By §5.1's own reasoning -
that problem objects are safe precisely because they are *returned* rather than *raised* - nothing
can return, so an argument rejection can only be raised, and **carries no problem object**.

B12 and B23 both require argument rejection to fail closed *and be testable*, and §5.1 currently
implies a uniformity it does not have on the path users will hit most often. Either state the third
exception plainly alongside the other two, or specify a pre-validation hook that converts it. **Do
not leave it implied.**

---

## C2 - Ranked gaps. Top ten, by consequence rather than B-number

1. **B58: the mandated collection-guard meta-test is absent.** A REQUIRED CI check that cannot
   pass from commit one. §8's `--collect-only` on the live suite is a *different* control for a
   *different* failure. `quality-gates.md:79-81` is explicit: absent guard means the CI test job
   MUST fail. And our two-suite split is exactly the configuration where an orphaned test file is
   invisible.
2. **B39: retries and breaker transitions are never logged.** `resilience.md:226`: *"Never retry or
   trip silently."* §5.3's audit event fires once per invocation, so three retries plus a breaker
   trip look identical to a first-try success. On a server whose upstream has **never been observed
   succeeding**, the first production incident would be undiagnosable. Five-line fix.
3. **B72: no advisory-tracking policy, against a deliberately-beta dependency.** `pip-audit` has no
   severity threshold and fails on ANY advisory. One transitive advisory turns a required gate red
   with no sanctioned response, and the unsanctioned response is a blanket `--ignore-vuln` - the
   exact silent suppression the clause forbids. We chose a beta stack; we owe it a policy.
4. **B64+B65: no `uv sync --frozen`, no committed `uv.lock`.** §10's own thesis is that a
   transitive bump broke code with zero change to that code. **It diagnoses the disease and then
   pins two packages by hand instead of prescribing the cure.** This also silently undermines B67
   and B70: an SBOM generated from an unfrozen resolve documents a build nobody shipped.
5. **B96: no key-rotation policy** for three credential classes, where `environments.md:626-628`
   makes rotation "enforced (not aspirational)" and names "key found in logs" as a trigger. §4.1
   builds excellent *detection* for exactly that event and specifies no *response*.
6. **B12+B23:** see C1 above.
7. **B17: the approval decision is not among the audited fields.** `agent-guardrails.md:122`
   requires logging "the approval decision if gated". `create_candidate` is gated three ways and
   emails a live human, and **the only record that a write was authorised would not exist.**
8. **B40: the `request_id_var` ContextVar is missing - and it is *why* B39 is missing.** Without
   it the id must be threaded by parameter into redaction, client and breaker, which is awkward
   enough that it gets skipped. Fix B40 and B39 becomes nearly free. **Do them together.**
9. **B30+B25: no inbound nesting, list, dict or body-size limits, and no control-character or
   encoding rejection.** §4.5's 500/1000 caps are *outbound transport* limits and say so.
10. **B56: the coverage remap inverts the risk.** The standard sets Utilities at 95%. §8 has no
    utilities target, so **`utils/redaction.py` sits at the 80% floor while holding secret
    redaction and untrusted-content fencing - two of §8's own required test cases** - and the
    client gets 90%.

Beyond the top ten: **B77-B87 is eleven consecutive documentation obligations with zero design
coverage** (§10 lists CI job names and stops); B98+B106 (nine CI gates, none declared *required*);
B7 (a Jobvite 401 surfacing to the caller *as* a 401 - mislabelled a second time, right after §4.2
catches Jobvite doing the same thing); B90/B91 (`.gitignore` never stated, on a public repo);
B51 (no UTC idiom, with token expiry on the write path as the live surface); B55 (without
`--strict-markers` a typo'd marker selects nothing and CI goes green having run less than it
claimed - and §8's entire credential-free strategy rests on marker selection); B80 (Quickstart-CI
parity is unmeetable as implied, since CI is credential-free by §8 and a working Quickstart needs a
credential - pick one or take an ADR).

---

## C3 - Two ADRs are under-scoped, and one is missing

- **ADR-0002 is under-scoped.** It covers substituting the Redis bucket. `rate-limiting.md:361-362`
  rule 6 is a **separate clause** - "429 uses ProblemDetail" - and §4.4 breaches it by raising
  `MCPError` with no problem object. §5.1 lists that among its honest exceptions and assigns it no
  ADR. **The design's most candid admission is the one with no decision record behind it.** Rule 5
  (`RateLimit-*` headers) is also undisposed.
- **ADR-0006 is under-scoped.** It disposes of B99 correctly but leaves B97 (branch *naming* - an
  independent clause the branch-model deviation does not touch, and which collides with the
  EC-### convention) and the "only merge from develop or hotfix" half of B98, which the deviation
  necessarily voids with nothing voiding it on the record. Also: B99's four properties - PR,
  approval, CI green, currency, squash - should **relocate onto `main`**, not retire.
- **A NEW ADR is required for the B56 coverage remap.** Loosening a mandated coverage number is
  exactly what the ADR mechanism exists to record, and §12 does not list it.

ADR-0003, ADR-0005 and ADR-0008 are correctly scoped.

---

## C4 - The hole the sweep could not reach, and it is the most concerning item here

`architecture/data-flow.md` and `architecture/threat-modeling.md` are **both `priority: required`**
- I verified both files exist and both carry that marker. `STANDARDS.md` dismissed them as
"process/design-artifact standards" **without reading either**, so **no B-number was ever derived
from them.**

**A design document is precisely the artifact a design-artifact standard binds.** So this is not a
gap in the design's conformance to the B-list; it is a **gap in the B-list itself**, and by
construction a B1-B106 sweep cannot find it. Tracked as its own task.

This is the same failure shape as CD-3 and as the confidential-scrub incident: a claim
("these do not apply") asserted without opening the thing it is about.
