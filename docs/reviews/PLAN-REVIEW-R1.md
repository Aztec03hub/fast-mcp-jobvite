# PLAN-REVIEW-R1 - `docs/plans/IMPLEMENTATION-PLAN.md` (draft 2)

Reviewer: `plan-review-r1`, fresh - I wrote none of this document.
Reviewed at `cc94459` (`Make every §8 case name its owner, and retract a claim I made twice`).
Subject: `docs/plans/IMPLEMENTATION-PLAN.md`, untracked, 980 lines.
Authority: `docs/DESIGN.md`. Where the plan contradicts it, the plan is wrong unless the plan has
found a design defect - and two of the findings below are design defects, marked as such.

Nothing was edited. `DESIGN.md` and the plan are untouched. Nothing was committed.

---

## Verdict

**NOT READY.**

The plan is good work and most of it is right: all 25 §8 cases are scheduled somewhere, the
dependency order is sound, the credential-free reordering in §5 is genuinely insightful, and §6's
risk call on U7 is correct. The failure is not the shape of the plan - it is that a document whose
whole subject is *"a hand-carried count is the defect this project has spent the day repairing"*
carries a hand-carried renumbering it applied to its own table and not to its own units. Seven §8
case references in U7, U8 and U10 are still draft 1's numbering. That is not a typo class; an agent
handed U8 in isolation builds a SIGTERM test and calls it fencing.

Beyond that, two units cannot be built as briefed because the configuration variables they read do
not exist anywhere in the repository or the design, and U0's first CI assertion is a number that is
already stale against HEAD.

### Tally

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| HIGH | 5 |
| MEDIUM | 11 |
| LOW | 2 |
| NIT | 1 |

Two of these (H2, M11) are **design defects surfaced by the plan review**, not plan defects, and
are flagged rather than worked around.

### Gates, re-run by me at HEAD

From the repository root:

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md
  exit=0   60 STRIDE rows, 17 Critical/High, 23 naming a §8 case

python3 docs/reviews/check-coupling-controls.py
  exit=0   34/34 controls fired; post-run re-check of the real DESIGN.md exit=0 (still green)

python3 docs/reviews/check-coupling-sweep.py
  exit=0   23 rows name a §8 case; 184 substitutions;
           6 escapes are the designed Medium/Low exemption; 0 escapes are holes
```

**34/34, not the 32/32 the plan records.** See H5.

### The repoint question the brief asked

**Still outstanding, and the shift is now +3.** `git diff -U0 9d65cc0 HEAD -- docs/DESIGN.md`
shows a 1-line → 4-line expansion at `:1373`, so every plan cite at or after that line is short by
three. Spot-checked at HEAD: the plan's `:1640` for C3-I1 is C3-S1 at HEAD (C3-I1 is `:1643`);
`:1683` for C6-D1 is C6-R1 (C6-D1 is `:1686`); `:1704` for C8-R1 is a table separator; `:1740` is
blank. Seventeen cites are affected. The §2-§8 cites are unshifted, as the plan predicted.

One thing the plan got right and I want to record, because it survived the move: C3-I1 and C6-D1
still carry the disposition `unmitigated (B15)` at HEAD, even though their mitigation *prose*
changed at `fe226b6` to say the default is "now named and shipped". The plan's substantive claim -
naming a variable is not mitigating the row - holds.

### Could I build one unit of this plan handed nothing else?

For most units, yes. U0, U2, U3, U4, U5, U6, U11 and U12 are buildable from their own text.

**Weakest: U9, HTTP transport hardening.** I could not build it. It is told to construct
`StaticTokenVerifier` "from environment at startup" and to set `allowed_hosts`/`allowed_origins`
"whenever the bind is not loopback" - and **no environment variable for a token, a scope, a bind
address or a port exists** in `.env.example` (12 variables, listed at H2), in `DESIGN.md`'s
variable set, or anywhere else. U9 cites no §8 case at all, its "the HTTP half of `config.py`"
ownership boundary is undefined against U1's ownership of the whole file, and every quantitative
statement in it is an inherited limit rather than an acceptance threshold. An agent would have to
invent variable names - which is exactly the decision class the design refused to leave open when
it closed Q1 for two other variables.

Runner-up: **U14**, for the reason in H4 - its exclusive file ownership names a module class the
design does not have.

---

## CRITICAL

### C1 - Seven §8 case references in U7, U8 and U10 use draft 1's 24-case numbering, and two units now claim `#18` for different subjects

**Evidence.** The plan's own §1 table (`IMPLEMENTATION-PLAN.md:75-101`) is correct: I re-derived
the 25 bullets independently from `DESIGN.md` and every line anchor matches
(`:1174, 1175, 1176, 1180, 1186, 1190, 1192, 1194, 1198, 1200, 1204, 1209, 1214, 1220, 1227, 1231,
1238, 1243, 1250, 1251, 1252, 1253, 1255, 1256, 1257`). The plan states at `:70` that #18 is new and
*"everything below it shifted by one"*. It then did not shift the units:

| Plan line | Says | §1 table says | Actual subject of the number used |
|---|---|---|---|
| `:452` | `§8 #22`: 4xx does not trip the breaker | **#23** | #22 is the four-arm approval case |
| `:453` | `create_candidate` not retrying `(#20)` | **#21** | #20 is unknown-non-string-dropped |
| `:506` | `§8 #18`: fencing incl. closing its own fence | **#19** | **#18 is the SIGTERM teardown case, owned by U1 at `:221`** |
| `:509` | `§8 #19`: unknown non-string field dropped | **#20** | #19 is fencing |
| `:510` | `§8 #23`: `eId`/`EId` casing pinned | **#24** | #23 is 4xx-not-tripping |
| `:572` | `§8 #21`, four arms: deny refuses… | **#22** | #21 is create_candidate-no-retry |
| `:574` | `§8 #24`, both eras | **#25** | #24 is the casing pin |

Everything numbered below 18 is correct in both schemes, which is why this looks clean on a skim.
The blanket positive-control list at `:104` uses the **new** numbering, so the document contains
both schemes with no marker distinguishing them.

**Why this is Critical rather than a nit.** The plan's stated purpose is to be fanned out to
implementation agents unit by unit. `#18` is now claimed by U1 (SIGTERM, `:221`) and U8 (fencing,
`:506`). An agent handed U8 with no other context writes a test named for a case it does not
exercise - which is the failure mode `DESIGN.md` names against itself.

**Suggested fix (my suggestion, verify before adopting - cheap).** Renumber the seven references
above to the §1 table's values: `:452`→#23, `:453`→#21, `:506`→#19, `:509`→#20, `:510`→#24,
`:572`→#22, `:574`→#25. Then add one sentence under the §1 table: *"Every `§8 #n` reference in §2
resolves against this table. Draft 1's numbering is not used anywhere below."* I would also
mechanically re-derive rather than hand-edit, given the document's own thesis - extract each unit's
`§8 **#n**` reference and assert the case text it names matches the table row.

---

## HIGH

### H1 - U0's §8 #3 verification asserts something false about the committed tree, and the cheapest way to satisfy it destroys the answer to Q1

**Evidence.** `IMPLEMENTATION-PLAN.md:188-189` says the #3 test asserts *"that every value in
`.env.example` is empty."* Five values in the committed `.env.example` are not empty:

```
41:JOBVITE_ENABLE_WRITES=false      48:JOBVITE_MCP_TRANSPORT=stdio
54:JOBVITE_TLS_TERMINATED_BY_PROXY=false
62:JOBVITE_MAX_RESULTS=50           69:JOBVITE_OUTBOUND_RATE_LIMIT=6
```

Two of them are the Q1 answer the plan celebrates at `:239-245` and `:911-916`. The design's actual
wording (`DESIGN.md:1176`) is *"`.env.example` carries **no real value**"* - no real credential,
not no value at all. The plan tightened the case into something the repository already violates.

**Why High.** U0 is the first unit. Its test either fails on the committed tree, or an agent
"fixes" the tree by emptying `JOBVITE_MAX_RESULTS=50` and `JOBVITE_OUTBOUND_RATE_LIMIT=6` - undoing
B15's blocking half and re-blocking U1, U6 and U7.

**Suggested fix (my suggestion, verify before adopting - cheap).** Replace the clause at `:189`
with: *"and that every **secret-class** variable in `.env.example` - the five credential names
(`JOBVITE_API_KEY`, `JOBVITE_API_SECRET`, `JOBVITE_FEED_KEY`, `JOBVITE_FEED_SECRET`,
`JOBVITE_COMPANY_ID`) - carries an empty value, while non-secret defaults may and do carry one."*
Verify the credential-name list against `.env.example` before adopting; I read it from the
committed file today but the list is the load-bearing half of the assertion.

### H2 - No configuration variable exists for the HTTP bind address, the port, or the `StaticTokenVerifier` tokens and scopes - so U1's §8 #10 test and all of U9 cannot be built as briefed. **This is a design defect, and it is the same class as Q1.**

**Evidence.** The complete variable set is 12, and it is the same 12 in both places I can check:

```
.env.example:        JOBVITE_API_KEY, JOBVITE_API_SECRET, JOBVITE_FEED_KEY, JOBVITE_FEED_SECRET,
                     JOBVITE_COMPANY_ID, JOBVITE_TOOLS, JOBVITE_ENABLE_WRITES,
                     JOBVITE_MCP_TRANSPORT, JOBVITE_TLS_TERMINATED_BY_PROXY,
                     JOBVITE_MAX_RESULTS, JOBVITE_OUTBOUND_RATE_LIMIT,
                     JOBVITE_PAGINATION_START_BASE
DESIGN.md:           the same 12 (grep -oE "JOBVITE_[A-Z_]+" docs/DESIGN.md | sort -u)
```

`DESIGN.md:748-749` says *"HTTP binds `127.0.0.1` unless told otherwise"* and `:774` says *"HTTP
auth uses `StaticTokenVerifier` built from environment at startup"* - neither names the variable
that does the telling or holds the tokens.

Consequences inside the plan:
- U1 (`:218`) must test *"off-loopback bind, no certificates"* - there is no variable that makes the
  bind off-loopback.
- U1 (`:212`) must ship *"`server.json` declaring **every** variable for registry consumers"* and
  (`:240`) *"`config.py` can enumerate the **full set**"* - both are unsatisfiable while three or
  more variables are unnamed.
- U9 (`:523-527`) reads tokens and scopes from an environment that declares none.
- U13 (`:646-647`) then asserts the README Configuration table *equal to `.env.example`'s
  enumeration*, freezing the omission into a merge gate.

**Why High.** This is precisely the defect the design just closed for `JOBVITE_MAX_RESULTS` and
`JOBVITE_OUTBOUND_RATE_LIMIT` - two variables that had no name - and the plan's draft 1 caught that
one and stalled U1 on it. Draft 2 did not run the same sweep over the rest of the set.

**Suggested fix (my suggestion, verify before adopting - a design change, so a restructure at the
document level even though the edit is small).** This is a question for the design, not something
the plan may settle. Raise it in §9 as **Q5**: *"§7.1 says HTTP binds `127.0.0.1` unless told
otherwise and §7.2 says `StaticTokenVerifier` is built from environment, but no variable is named
for the bind host, the port, or the token/scope map. `.env.example` and `DESIGN.md` both enumerate
12 variables and none of them is one of these. §8 #10 cannot be written and U9 cannot be built
until they are named. This is the same shape as B15."* Until it is answered, mark U1's #10 bullet
and the whole of U9 **blocked**, the way draft 1 marked U1. My guess at the names -
`JOBVITE_MCP_HOST`, `JOBVITE_MCP_PORT`, `JOBVITE_HTTP_TOKENS` - is a guess and the plan must not
adopt it; naming them is the design's call, which is the entire lesson of B15.

### H3 - The capability-drift diff, one of the design's two never-executed mechanisms, is scheduled in U0 as an ordinary CI line with its ceiling dropped

**Evidence.** `DESIGN.md:43-45` names exactly two mechanisms that *"sit among executed results and
borrow their credibility"*: the capability-drift diff (§10) and the circuit breaker (§4.3).
`DESIGN.md:1857` records the diff as marked `UNVERIFIED:` at its point of use; `:1819` carries it as
a Residual Risk; C9-T1 is one of the 17 Critical/High rows.

The plan preserves the ceiling for one of the pair and drops it for the other. The circuit breaker
gets §6 in full, plus an explicit *"Inherited limit"* paragraph at `:483-485`. The capability-drift
diff appears exactly twice in 980 lines: at `:810`, only as scenery in the sentence establishing the
breaker's status, and at `:175` as `fastmcp inspect emitted and diffed between builds` - one clause
in U0's CI list, with no `UNVERIFIED:` marker, no verification bullet, no residual carry and no
mention of C9-T1. The string "capability drift" and the string "UNVERIFIED" appear nowhere else.

**Why High.** The brief's question was whether the plan preserves each stated ceiling as uncertain
or quietly plans as though settled. For this one it plans as settled, and it does so in the unit
that stands up CI - so the diff becomes a green gate before anyone has run it once.

**Suggested fix (my suggestion, verify before adopting - cheap).** Add to U0, immediately after the
CI list at `:177`: *"**Inherited limit, carried not resolved.** The `fastmcp inspect` capability-drift
diff is one of the two mechanisms `DESIGN.md:43-45` names as never executed, marked `UNVERIFIED:`
at its point of use and carried as a Residual Risk under C9-T1. Standing it up in CI does not
execute it: a diff that has never seen a real capability change has only ever compared a build to
itself. Its first genuine evidence is a dependency bump that actually moves the manifest, and until
then it is scheduled, not verified."* I would also add one line to §6 naming it as the third risk
item, so the pair the design names stays a pair in the plan.

### H4 - Wave C's "four concurrent agents" rests on a file boundary the design does not have: `models/` is output models, one per tool, and three units write it

**Evidence.** `IMPLEMENTATION-PLAN.md:740` gives U14 exclusive ownership of *"the input-model
modules under `models/`"*. `DESIGN.md:270` defines that directory as:

```
  models/                     allow-listed output models, one per tool
```

There are no input-model modules in the design's layout, and the design never says where input
models live. `DESIGN.md:161-162` only says *"Every check above lives in the input models, so every
one of them runs before the tool body and is raised by the framework"* - which, under FastMCP,
usually means the tool function's own signature in `tools/*.py`.

So either reading breaks the wave:
- If input models go in `models/`, U14 collides with **U8** (`:491`, candidate output models),
  **U12** (`:624`, the feed envelope needs a model) and the job model U5 already put there.
- If they go in the tool signatures, U14 collides with **U12** in `tools/jobs.py` and **U8** in
  `tools/candidates.py` - and U14's own row says it *"reads but does not write `tools/`"*.

The plan half-knows this: `:676-677` says U14 *"realistically accretes as each tool's input model is
written, and this unit is the sweep that proves the set is complete"* - which is the opposite of
exclusive ownership, in the same unit, forty lines from the table that grants it.

**Why High.** `:754-755` calls U9 + U6→U7 + U14 + U12 *"the widest safe fan-out in this plan"*, and
the plan's own §4 preamble says agents sharing a tree is how work gets lost here. Two of those four
agents write the same files.

**Suggested fix (my suggestion, verify before adopting - a small restructure).** Two changes.
(a) Change U14's Wave C row from an ownership claim to what the unit actually is: `| U14 | *(owns no
file exclusively - it is a sweep, see below)* | `models/`, `tools/` |`, and move U14 out of the
concurrent set, running it after U8 and U12 land. That reduces the widest safe fan-out to **three**
(U9, U6→U7, U12), and the plan should say three rather than four. (b) Add a fourth entry to the
"Three collisions to plan around" list at `:744`, since there are four: *"**U14's input-model checks
have no module of their own.** `DESIGN.md:270` gives `models/` to output models one per tool and
names no home for input models, so U14 either shares `models/` with U5, U8 and U12 or shares
`tools/` with U5, U8 and U12. It is sequenced last rather than parallelised, and where input models
live is raised as a design question."* The "where do input models live" half belongs in §9 alongside
H2 - I believe it is a genuine gap in `DESIGN.md:270`, but confirm that before filing it.

### H5 - The controls figure is stale, and U0 makes CI assert it

**Evidence.** The plan records `32/32` at `:47`, `:52`, `:192-195` and `:894`, measured against
`9d65cc0` and correct there. At HEAD the harness reports **34/34** - `cc94459` added two controls
(`git diff --stat 9d65cc0 HEAD -- docs/reviews/check-coupling-controls.py` shows +27 lines). U0's
verification at `:192` reads *"the controls harness reports **32/32** controls firing"*, which is an
assertion CI would carry.

There is an irony worth naming: the plan is right that the file's own docstring narrates 21, calls
that out as *"a small instance of the stale-count defect this repository keeps correcting"*, and
then hard-codes a third stale number in the unit that stands up the gate.

**Suggested fix (my suggestion, verify before adopting - cheap).** Two parts. Update `:47`, `:52`,
`:192-195` and `:894` to 34/34 **and** to a re-run at HEAD rather than at `9d65cc0`. More
importantly, change what U0 asserts: replace *"reports 32/32 controls firing"* with *"reports
**N/N** - every control it holds fires, and its exit code is 0. CI asserts the exit code and the
`all fired` property, never a literal count, because the harness grows and a literal count turns
growth into a red build."* That second half is the durable fix; the number update alone reproduces
the defect on the next commit.

---

## MEDIUM

### M1 - §9's Q2 finding and its suggested gate change have already landed; the plan is behind the tree

`IMPLEMENTATION-PLAN.md:953-959` offers, as a hypothesis, *"add a check that every §8 required case
is either named by at least one §11 row or carries an explicit exemption marker"*. That check exists
at HEAD. `git diff 9d65cc0 HEAD -- docs/reviews/check-coupling.py` shows a 35-line block labelled
`2a-ter. EVERY §8 CASE HAS AN OWNER (GATE-2)`, and `DESIGN.md:1246-1247` now carries the measured
residual in the case #18 bullet itself, including the conclusion the plan reached independently:
*"GATE-2 now requires every case to name its owner… **it does not make deletion visible.**"*

The plan's measurement was right and its independent arrival at the same conclusion is to its
credit. But as it stands, an agent reading §9 files work that is done.

**Suggested fix (my suggestion, verify before adopting - cheap).** Rewrite the Q2 residual section
in place rather than appending to it: keep the two-arm mutation table as the measurement, then
replace the suggested-fix paragraph with *"**Landed at `cc94459`.** `check-coupling.py` now carries
`2a-ter (GATE-2)`, requiring every §8 case to be named by a §11 row or to cite a B-number or section
as its owner; `DESIGN.md:1246-1247` records the same measured residual, that GATE-2 stops a case's
justification being stripped but does not make its deletion visible. The seven orphans this section
enumerated are the population that check now addresses. Nothing remains open here."* Re-derive the
orphan count against HEAD before publishing that sentence - I did not re-run the extraction.

### M2 - The §10/§10.1/§11 repoint is still outstanding, and the shift is +3

Detail and evidence under **Verdict → the repoint question** above. Seventeen cites at or after
`:1373` are short by three at HEAD.

**Suggested fix (my suggestion, verify before adopting - cheap, but do it mechanically).** Re-resolve
every cite against HEAD rather than adding three by hand, and change the header claim at `:15-20`
from *"resolves against the `9d65cc0` git object"* to name HEAD's SHA. Adding three by hand would
be a hand-carried offset, which is the defect class this document exists to avoid.

### M3 - Two citations point at the wrong subject, and the header's verification could not have caught them

The header at `:18` claims *"All 84 distinct cites land on non-blank content at that commit."* True,
and insufficient - non-blank is not the same subject. Two are wrong at `9d65cc0` itself, so this is
not repoint drift:

| Plan line | Cites | Actually at that line (`9d65cc0`) | Correct cite |
|---|---|---|---|
| `:345` | `DESIGN.md:1255-1256` for `MockTransport` | §8 bullets #23 and #24 | `:1262-1263` |
| `:750` | `DESIGN.md:1262-1264` for `utils/redaction.py` holding both halves | the `MockTransport` paragraph | `:1269-1271` |

The plan's own §1 table cites `:1255` and `:1256` correctly for cases #23 and #24, so the document
contradicts itself about what lives at those lines.

**Suggested fix (my suggestion, verify before adopting - cheap).** Correct the two cites, and
change the header sentence to state the check that was actually run and its limit: *"Every cite was
checked to land on non-blank content. That is a weaker check than it looks - it cannot catch a cite
that lands on the wrong paragraph, and two did."*

### M4 - The two malformed fixtures are synthetic, are placed in the Recorded tier, and are ordered asserted byte-exact; and the recorded count is given as six when it is five

`:119-121` puts seven files in the Recorded tier - *"Six exist already"* followed by five names
*"plus the two malformed bodies"* - three different numbers in one bullet. The tier is ordered
**"Assert verbatim"**, and U4 at `:335-338` repeats it as *"All five recorded error fixtures asserted
byte-exact"* followed by four names plus the two malformed.

The two malformed files are not captures. `malformed_not_json.txt` is the single line
`this is not JSON at all`; `malformed_truncated.json` is `{"candidates": [ {"eId": "TESTCND1", ` -
a placeholder id in the same style as the synthetic fixtures. `DESIGN.md:1162` defines Recorded as
*"byte-exact captures of **real Jobvite error transport**"*. These are invented.

**Why it matters beyond arithmetic.** Putting two invented files in the ground-truth tier is the
exact confusion the three-tier split exists to prevent, and the plan says so itself at `:860`. The
recorded tier is **five**.

**Suggested fix (my suggestion, verify before adopting - cheap, but check the fixtures' provenance
first, since I inferred it from their contents rather than from a manifest).** Rewrite `:119-121` as
*"**Recorded** - byte-exact captures of real Jobvite error transport. **Five exist**:
`error_auth_401.json`, `error_auth_200_body401.json`, `error_route_404.json`, `error_task_400.html`,
`error_v1_auth_401.txt`. **Assert verbatim.**"* and add to the Synthetic list *"plus
`malformed_not_json.txt` and `malformed_truncated.json` - deliberately invalid bodies, invented, and
belonging to this tier however they are asserted"*. Then correct U4's `:335` to *"All four remaining
recorded error fixtures asserted byte-exact… plus the two synthetic malformed bodies, which fail
loudly rather than degrading to an empty result."*

### M5 - U4 builds no way to issue a request, and U5 needs one

U4's Builds list (`:320-326`) is client construction, header auth, the v1 query-parameter exception,
the success invariant and three error encodings. Nothing in it exposes a method that performs a GET
and returns a decoded body. U5 (`:379`) then requires *"An in-process FastMCP `Client` calls
`search_jobs` against `MockTransport` and gets a typed result"*, and U6 - the unit that would
naturally add the request loop - comes after.

It is probably implied. But this document's whole premise is that a unit is a self-contained brief,
and an agent handed U4 alone would deliver an auth-and-error module with no caller.

**Suggested fix (my suggestion, verify before adopting - cheap).** Append to U4's Builds: *"…and a
single request entry point that issues one call, applies the invariant above to the response, and
returns a decoded body or raises the typed error. Paging around that entry point is U6; U4 owns the
one-call path, and U5's end-to-end test is what proves it exists."*

### M6 - The result cap is built twice, in U5 and in U6, with no owner named

U5's Builds (`:357`) includes *"the in-tool result cap reporting `showing N of total`"*, verified at
`:386`. U6's Builds (`:399`) includes *"`min(transport_cap, configured_result_cap)`"* and `:417-420`
declares *"The result cap is now named: `JOBVITE_MAX_RESULTS`… it is the configured half"*. Both
units also cite `DESIGN.md:409` territory for the same mechanism. §4's collision list does not
mention it, because they are nominally in different files - but they are one behaviour, and U6 will
either duplicate U5's cap or rewrite it.

**Suggested fix (my suggestion, verify before adopting - cheap).** Split it explicitly at the two
halves the design already names. In U5: *"the **in-tool** cap, `JOBVITE_MAX_RESULTS` applied to a
single page's items, reporting `showing N of total` from the envelope's own `total`. The
`min(transport_cap, configured_result_cap)` composition is U6's and is not built here."* In U6, add:
*"U5 built the in-tool half; U6 adds the transport half and the `min()` that composes them, without
re-implementing U5's reporting string."*

### M7 - §8 #16's error arm is scheduled in no unit

`DESIGN.md:1231` requires `request_id` on every result across **four arms**: successful read,
successful write, audit-failure warning branch, and error - which the plan's own §1 table records at
`:92`. U5 (`:382`) takes the read arm. U10 (`:580`) takes *"write arms: `request_id` on the wire for
a successful write **and** for the audit-failure warning branch"*. The **error** arm is claimed
nowhere. U5's adjacent bullet asserts that a 200-with-401 body returns `/problems/external-service-error`
502 with `is_error=True`, but says nothing about `request_id` reaching the wire on it.

**Suggested fix (my suggestion, verify before adopting - cheap).** Extend U5's `:382` bullet: *"…and
the **error arm** of the same case - the `error_auth_200_body401.json` call above returns a problem
object whose `request_id` member matches the audit event's id, asserted **on the wire result**, so
all four arms of #16 have an owner: read and error here, write and audit-failure-warning in U10."*
Check against `DESIGN.md:585-590` that the error half is carried by the problem object's own
`request_id` member rather than by `_meta`; the design distinguishes them and my sentence assumes it.

### M8 - The blanket positive-control rule is stated in §1 and then not carried into four units' verification lists

`:103-105` correctly derives that `DESIGN.md:1273-1274` requires a paired positive control for
cases #1, #7, #8, #9, #10, #12, #15, #21, #22, #23 and #25 *"not only where the bullet says so"*.
Checking each against the unit that owns it: #1 (U4) ✓, #8 (U14) ✓, #10 (U1) ✓, #12 (U0) ✓,
#15 (U11) ✓, #21 (U7 - the row counter serves) ✓, #23 (U7) ✓. Missing:

- **#7**, U14 `:679` - listed with no control.
- **#9**, U14 `:679-680` - four arms, no control.
- **#22**, U10 `:572` - four refusal arms, no arm showing an approved write succeeds.
- **#25**, U10 `:574` - both eras, no control. (The control at `:578` belongs to the
  unidentifiable-era test, not to #25.)

**Why it matters.** #22 without a positive control is the guard-that-refuses-everything the design's
rule is named for: four arms that all assert "the row count did not move" pass perfectly against a
`create_candidate` that is broken and never writes at all.

**Suggested fix (my suggestion, verify before adopting - cheap).** Add to U10 `:572`: *"Positive
control, required by `DESIGN.md:1273-1274` and load-bearing here: an **approved** write moves the
row counter by one. Without it, four refusal arms asserting the count did not move all pass against
a write that never works."* Add to U14 `:679`: *"#7 and #9 each carry the blanket positive control
of `DESIGN.md:1273-1274` - a well-formed argument passes schema validation, and a payload just
inside each of the four structural limits is accepted."*

### M9 - U0's CI invokes a script U11 builds, and U11 depends on U0

`:172-174` puts *"`pip-audit` behind `scripts/check_advisories.py` (U11)"* in U0's CI list. U11
(`:608`) depends on U0. So U0's first green CI run invokes a file that does not exist. The plan
flags the analogous `pyproject.toml` ordering for Wave A at `:725-726` and does not flag this one.

**Suggested fix (my suggestion, verify before adopting - cheap).** Add to U0 after the CI list:
*"One ordering note, the same shape as the `pyproject.toml` one in §4: the `pip-audit` step invokes
`scripts/check_advisories.py`, which U11 builds. Either U0 lands the step commented with the U11
reference and U11 enables it, or U0 lands a bare `pip-audit` that U11 replaces. Landing the wrapper
call against a missing file makes CI red from its first run, which trains everyone to ignore it."*

### M10 - Seven of the design's seventeen Critical/High rows are named by no unit

The plan names 16 threat ids across its units, and a reader reasonably treats that as the coverage
map. The design carries 17 Critical/High rows (confirmed by the gate: *"17 Critical/High"*). Of those 17, the plan
names ten: C1-I1, C1-S1, C1-T1, C4-R1, C4-S1, C5-I1, C5-R1, C5-S1, C6-I1, C6-S1. (The remaining six
ids it names - C3-I1, C4-D1, C4-D2, C6-D1, C7-T1, C8-R1 - are Medium rows.) Not named anywhere:
**C1-R1, C2-R1, C4-E1, C5-E1, C7-I1, C8-I1, C9-T1**.

Several are covered in substance by a §8 case the plan does schedule (C8-I1 by #3 in U0, C4-E1 by
#22's accept-carrying-false arm in U10). Two are not:
- **C9-T1** is the capability-drift diff - see H3.
- **C5-E1** is the read-only-key High residual. U13 schedules the README sentence and §8 #14 asserts
  its presence, but the *ceiling* - `DESIGN.md:1677-ish`, *"whether Jobvite issues read-only keys at
  all is unknown, so if the answer is no the residual stands"* - is carried nowhere in the plan. It
  reads as discharged by writing a sentence.

**Suggested fix (my suggestion, verify before adopting - cheap for the disclosure, moderate for the
sweep).** Add to §8 (*What this plan does NOT cover*): *"**The plan names 16 threat ids and the
design carries 17 Critical/High rows.** Seven are named by no unit: C1-R1, C2-R1, C4-E1, C5-E1,
C7-I1, C8-I1, C9-T1. Most are covered in substance by a §8 case a unit does schedule; the id list
above is not a coverage map and should not be read as one."* Separately add to U13: *"**Carried, not
resolved.** C5-E1 stays a High residual after this unit. Writing the requirement into the deployment
section satisfies §8 #14; it does not establish that Jobvite issues read-only keys, which
`CREDENTIAL-CHECKLIST.md` row 0 asks and nothing else settles."* Re-derive the seven-id list against
HEAD before publishing - I extracted it by grep and it should be confirmed row by row.

### M11 - "no library is selected yet (B47)" - B47 names `circuitbreaker ^2`. **This is a design defect the plan inherited.**

`IMPLEMENTATION-PLAN.md:469` and `:813` carry the design's claim that *"no library is selected yet
(B47)"* and that the survey runs *"against libraries nobody has surveyed"*. The plan is faithfully
repeating `DESIGN.md:581`, so the plan is not wrong relative to its authority. But B47 itself reads
(`docs/research/STANDARDS.md:374`, and `docs/reviews/CONFORMANCE-B1-B106.md:239`):

> **B47. Blessed libraries: Pydantic `>=2.10`, `httpx`, `tenacity ^9` + `circuitbreaker ^2`, `uv`,
> ruff/mypy/pytest**

B47 names a breaker library. What is genuinely open is whether `circuitbreaker ^2` satisfies
`:581`'s call-path constraint - which is a **one-library rejection test**, not an unbounded survey.
`docs/reviews/CONFORMANCE-RESWEEP.md:376` already flags `circuitbreaker` as *"unnamed, beside a
mechanism §12 already flags as unevidenced"*, so the corpus has noticed the gap from the other side.

The plan's §8 disclosure at `:869-871` explains how this got through - it did not read the standards
corpus and quotes every standards cite from `DESIGN.md`. That disclosure is honest and it is exactly
the right place for this to surface.

**Suggested fix (my suggestion, verify before adopting - cheap for the plan, a design change for the
root).** In U7 at `:478`, replace *"survey candidate libraries against the timer constraint"* with:
*"apply the rejection test to **`circuitbreaker ^2` first**, which B47's blessed-library list names
(`STANDARDS.md:374`) - `DESIGN.md:581` says no library is selected, but the standards register does
name one, and testing the blessed candidate before surveying alternatives is both cheaper and what
B47 requires. If it evaluates transitions from a background timer, it is rejected on the record and
the inline breaker is taken with evidence."* And raise it in §9 as a design question: `DESIGN.md:581`
characterises B47 as leaving the library unselected, and it does not. I checked B47's text at
`STANDARDS.md:374` directly; confirm the `^2` version constraint is still current before the plan
quotes it.

---

## LOW

### L1 - A bare `:70` in U13 resolves to the wrong document

`:662-664`: *"…rows 1-4 close (`CREDENTIAL-CHECKLIST.md:96-97`). **A CI status badge cannot be live
until CI exists** (`:70` forbids a static badge…)"*. The nearest antecedent is
`CREDENTIAL-CHECKLIST.md`, whose line 70 is blank (line 71 begins *"Row 9 - run it last"*). The rule
is `readme-standard.md:70` - *"**Badges are live**: each badge MUST point at a live source. Static
SVGs that no longer reflect reality are forbidden."* The design gets this right at `DESIGN.md:1520`,
where `:70` sits in a paragraph whose antecedent *is* `readme-standard.md`; the plan copied the bare
form across an antecedent change.

**Suggested fix (my suggestion, verify before adopting - cheap).** Write it out:
`readme-standard.md:70`.

### L2 - "All five recorded error fixtures" followed by four names

`:335-338`. Subsumed by M4's rewrite; noted separately so it is not lost if M4 is resolved
differently.

**Suggested fix (my suggestion - cheap).** Covered by the M4 rewrite above.

---

## NIT

### N1 - §3's dependency diagram orphans U12 and U13

`:706-707` places U12 and U13 as free-floating lines with no connecting edges, while every other
unit hangs off a tree branch. Their dependencies are stated correctly in prose; the diagram just
does not draw them.

**Suggested fix (my suggestion, verify before adopting - cheap).** Hang U12 under U5 (its earliest
parent) and annotate `(also needs U6, U3)`, and put U13 at the bottom with an explicit
`└── U13 README (needs U0-U12)`. A reader skimming the diagram for "what can start now" currently
sees two units with no prerequisites at all.

---

## What I checked and found sound

Recording this so the findings above are not read as a verdict on the whole document.

- **The §8 count.** I re-derived the 25 bullets independently against HEAD by extracting top-level
  bullets between the *"Required cases"* header (`DESIGN.md:1173`) and the *"Transport substitution
  uses"* paragraph (`:1262`). Twenty-five, and every line anchor in the plan's §1 table matches.
  The mechanical re-derivation was the right call and it produced the right answer.
- **Case coverage.** All 25 cases are scheduled to a unit under the §1 table's numbering. Nothing is
  orphaned (the numbering is wrong in seven places - C1 - but no case is unowned).
- **Dependency order.** U0 → U1/U2/U11, U2 → U3 → U4 → U5, U6 → U7 sequential in one file, U8 after
  U5/U6, U10 after U7/U8/U9. I could not find a unit that depends on something a later unit builds,
  with the two exceptions filed as M5 and M9. **U5 is genuinely the first runnable server** - it
  needs nothing from U6 or later that I could identify.
- **Collisions 1, 2 and 3 in §4** (`jobvite_client.py`, `utils/redaction.py`, `tools/candidates.py`)
  are real, correctly identified and correctly sequenced. H4 is a fourth they missed.
- **Spike and standards cites, spot-checked at source:** `FASTMCP-SPIKE-4.md:898` (the literal
  `"global"` client id), `:2073-2074` (transport and session_id both traps), `:2153-2165` (the
  per-era no-handler asymmetry); `architecture/error-contract.md:96-108` (the registry, and the
  design's seven-row subset at `DESIGN.md:486-494` is right); `backend/testing.md:67`
  (`--strict-markers` in `addopts`); `backend/resilience.md:166-168` (4xx MUST NOT trip the
  breaker); `documentation/readme-standard.md:83` (no credentials in Quickstart);
  `ai/tool-calling.md:173-175` (`request_id_var` verbatim). All correct.
- **`JOBVITE-API.md:393-399`** - the one observed `200`, its envelope, `total` as full result-set
  size, `start=0` accepted. The plan's structural tier is faithful to it, and the sequencing
  consequence at `:137-140` (structural assertions before the candidate models) is the strongest
  single judgement in the document.
- **`CREDENTIAL-CHECKLIST.md`** rows 0, 2, 3, 9, 10 and `:96-97` all resolve as cited, including
  row 9's *"run it last, and stop at the first `429`"* safety condition at `:71-72`.
- **The B15 ceilings.** `JOBVITE_OUTBOUND_RATE_LIMIT=6` is correctly and repeatedly described as a
  conservative guess and not a vendor figure, at U1, U6, U7 and §9. C3-I1 and C6-D1 are correctly
  carried as `unmitigated (B15)` despite the variable now having a name - I verified their
  dispositions at HEAD and the plan's reading is right.
- **The B108 dedupe ceiling.** U10 `:593-595` carries it correctly: the idempotency-key remedy
  cannot be built because nothing establishes Jobvite accepts one, and it is disclosed rather than
  planned.
- **`.github/workflows/` holds exactly `mirror.yml`**, and `src/` and `tests/` are empty. §0's
  factual claims are true at HEAD.
- **The three gates**, re-run by me at HEAD, all green - with the count correction at H5.

---

*`plan-review-r1`, 2026-08-28. `DESIGN.md` and `IMPLEMENTATION-PLAN.md` were not edited. Nothing was
committed.*
