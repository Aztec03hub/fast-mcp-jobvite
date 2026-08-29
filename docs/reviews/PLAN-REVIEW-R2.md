# PLAN-REVIEW-R2 - `docs/plans/IMPLEMENTATION-PLAN.md` (draft 3)

Fresh reviewer, round 2. I wrote none of this plan and did not conduct round 1.
Reviewed at `docs/DESIGN.md` HEAD = `8814d69` (`Name the HTTP transport variables, and stop
mischaracterising B47`), plan untracked at 1,164 lines, `src/` and `tests/` empty.

Every `Suggested fix:` below is **my suggestion, to be verified before adoption**, not an
instruction.

---

## Verdict

**NOT READY** - by three HIGH findings, none of which is a rewrite. All three are localised and
I would expect draft 4 inside an hour. This is a materially better document than the round-1
tally suggests: the CRITICAL is genuinely fixed, and the two halves of the brief split cleanly -
the citation half is now very strong, and the fan-out half is where the remaining defects are.

### Tally

| Severity | Count |
|---|---|
| CRITICAL | **0** |
| HIGH | **3** |
| MEDIUM | **5** |
| LOW | **2** |
| NIT | **1** |

---

## Gates, re-run by me from the repo root at HEAD

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md   exit 0
    60 STRIDE rows, 17 Critical/High, 23 naming a §8 case
python3 docs/reviews/check-coupling-controls.py         exit 0
    34/34 controls fired; post-run re-check of the real DESIGN.md exit=0
python3 docs/reviews/check-coupling-sweep.py            exit 0
    23 rows name a §8 case; 184 substitutions; 6 escapes are the designed
    Medium/Low exemption; 0 escapes are holes
```

All three match the plan's §0 report exactly, including the 34. The plan's refusal to let CI
assert a literal count (§0, §2 U0) is correct and I would not change it.

---

## Part 1 - Are the twenty round-1 findings actually fixed?

I re-derived the §8 case list from `DESIGN.md` at HEAD myself rather than reading the plan's
table: every top-level bullet between `DESIGN.md:1226` (*"Required cases"*) and `:1273`
(*"Transport substitution uses"*).

**25 cases. Every one of the plan's 25 line anchors in §1 is correct.** I checked each anchor
against the bullet text at that line, not by counting offsets:

```
#1  :1185  #2  :1186  #3  :1187  #4  :1191  #5  :1197
#6  :1201  #7  :1203  #8  :1205  #9  :1209  #10 :1211
#11 :1215  #12 :1220  #13 :1225  #14 :1231  #15 :1238
#16 :1242  #17 :1249  #18 :1254  #19 :1261  #20 :1262
#21 :1263  #22 :1264  #23 :1266  #24 :1267  #25 :1268
```

**C1 is genuinely fixed.** I resolved every `§8 #n` reference in §2 subject by subject. All
of them - U0's #11/#12/#3, U1's #10/#18, U3's #4/#5/#2/#17, U4's #1, U5's #16 read and error
arms, U7's #13/#23/#21, U8's #6/#19/#20/#24/#5, U9's #10, U10's #22/#25/#16, U11's #15,
U13's #14, U14's #7/#8/#9 - name the right subject under the 25-case scheme. Draft 1's
numbering appears nowhere. The author's claim that it re-extracted the table rather than
repointing it is borne out: the table is right, and everything keyed off it is right.

**The orphan claim in Q2 is also correct.** §11 carries 18 distinct `§8:` references; 25 - 18
leaves exactly the seven the plan names (#12, #16, #17, #18, #21, #23, #24). GATE-2 is real and
is at `check-coupling.py:305`, labelled as the plan describes.

**All 25 cases have exactly one owning unit**, with #16's four arms split U5/U10 as stated.
I verified this by mapping owners rather than trusting §8's self-claim.

### Status of the twenty

| R1 | Subject | Status |
|---|---|---|
| C1 | Seven stale §8 references | **Fixed and verified** subject by subject |
| H1 | U0 #3 asserts something false about the tree | **Fixed in direction, wrong in number** - see M3 |
| H2 | No HTTP bind/port/token variables | **Fixed in design.** 15 vars in `.env.example`, 15 in `DESIGN.md`, sets identical - I diffed them |
| H3 | Capability-drift ceiling dropped | **Fixed**, and well - U0 and §6 both carry it |
| H4 | Wave C's four agents rest on a boundary that does not exist | **Partially fixed** - `models/` analysis is right, but see H2/H3 below |
| H5 | Stale controls figure asserted in CI | **Fixed** - exit code + *all fired*, no literal |
| M1 | Q2 already landed | **Fixed** - rewritten in place, GATE-2 confirmed at `:305` |
| M2 | §10/§10.1/§11 repoint outstanding | **NOT fixed for §11** - see H1 |
| M3 | Two citations at wrong subject | **Fixed** - `MockTransport` at `:1273-1274` ✓, redaction coverage at `:1280-1282` ✓ |
| M4 | Malformed fixtures in Recorded tier | **Fixed** - 5 recorded / 10 synthetic, matches disk exactly |
| M5 | U4 builds no request entry point | **Fixed** |
| M6 | Result cap built twice | **Fixed for the result cap** - but the sibling survives, see H3 |
| M7 | #16 error arm unscheduled | **Fixed** - U5 |
| M8 | Blanket positive control not carried | **Mostly fixed** - see M1, M2, M4 |
| M9 | U0 invokes a script U11 builds | **Fixed** - explicit ordering note |
| M10 | Seven Critical/High rows named by no unit | **Fixed** - §8 addresses all seven |
| M11 | "B47 selects no library" | **Fixed in design.** Verified independently: `docs/research/STANDARDS.md:374-375` gives B47 with `circuitbreaker ^2`; `:316` gives B37; and the corpus at `architecture/reference-architecture.md:95` reads `tenacity + circuitbreaker ^9 / ^2` |
| L1 | Bare `:70` resolves to wrong document | **Fixed.** `readme-standard.md:70` = *"Badges are live... Static SVGs that no longer reflect reality are forbidden"* - exactly as quoted |
| L2 | "All five recorded" then four names | **Fixed** |
| N1 | Diagram orphans U12/U13 | **Fixed** |

Eighteen of twenty are properly fixed. **M2 is not fixed for §11 (→ H1), and M6's sibling
survives (→ H3).**

---

## HIGH

### H1 - Six threat-row anchors are stale from `9d65cc0`, and one of them lands on a row that asserts the negation of the sentence citing it

The plan's headline guarantee (`IMPLEMENTATION-PLAN.md:18-21`) is that *"Every `DESIGN.md:<line>`
citation resolves against `8814d69`, repointed mechanically by matching each cited line's text"*.
I swept all 127 cites in the document - 86 in `DESIGN.md:N` form and 41 in the plan's bare
`` `:N` `` shorthand. **121 resolve correctly. Six do not, and they are two anchors repeated
three times each.**

| Plan says | Cites | Actually at that line | True line |
|---|---|---|---|
| C3-I1 | `DESIGN.md:1688` | **C2-I1** (`include_payloads` flipped to True) | **`:1654`** |
| C6-D1 | `:1683` | **C5-R1** (retries/breaker not logged) | **`:1697`** |

At `IMPLEMENTATION-PLAN.md:319`, `:512` and `:1095`.

Both are off by exactly -14, and I traced why: **at `9d65cc0`, `DESIGN.md:1688` really was
C3-I1** (`git show 9d65cc0:docs/DESIGN.md | sed -n 1640p`). These are draft-2 anchors carried
forward untouched. This is round 1's M2 - *"the §10/§10.1/§11 repoint is still outstanding"* -
applied to §10 and §10.1 and **not** to §11.

Why this is HIGH rather than a typo:

1. `:1683` lands on **C5-R1, which reads "Mitigated in §5.3."** The plan's sentence at `:319`
   is *"C3-I1 ... and C6-D1 ... **still read `unmitigated (B15)`**"*. A reader who follows the
   anchor finds a row asserting the opposite. This repo already fixed one instance of a row
   asserting a thing and its negation (`fe226b6`); this is the same shape.
2. `:1683` is C5-R1, which the plan **separately** discusses at `:975` as *"a High that just
   came off the must-mitigate table"*. The same anchor now serves two different subjects in one
   document - which is precisely the confusion C1 was.
3. It falsifies the one guarantee the plan asks implementation agents to trust.

**The underlying claim is true.** I verified C3-I1 at `:1654` and C6-D1 at `:1697`: both read
`unmitigated (B15)`, and `DESIGN.md:1837` lists both on the mitigate-before-production-release
list. Only the anchors are wrong.

**Suggested fix (mine, verify before adopting):** replace `DESIGN.md:1688` → `DESIGN.md:1702`
and `:1683` → `:1697` at plan lines 319, 512 and 1095. Then re-run the text-identity repoint
over §11 specifically, since the sweep that produced the header's claim demonstrably did not
cover the threat table - and state in the header that §11 anchors were included, because that
is the part the last two drafts both missed.

---

### H2 - §4 schedules U12 concurrently with U6, and U12 depends on U6. The "widest safe fan-out" is two agents, not three

`IMPLEMENTATION-PLAN.md:906` states: *"**U9, U6→U7 and U12 can genuinely run as three concurrent
agents** once U5 has landed, because their write sets are disjoint."*

But the plan says three times that U12 needs U6:

- `:754` - **"Depends on. U5, U6, U3."**
- `:841` - the §3 diagram: `U12 get_job_feed (also needs U6, U3)`
- `:764` - *"it is `[OFFICIAL]` 1-based, so it wants U6's per-resource base configured"*

The write sets being disjoint is necessary, not sufficient. An agent handed U12 at U5-landing,
told it may run concurrently, needs `JOBVITE_PAGINATION_START_BASE` and the per-resource base
that U6 is at that moment building inside `services/jobvite_client.py` - a file U6 owns
exclusively. The agent either blocks, or writes into U6's file, which is the failure §4's own
opening sentence exists to prevent.

Round 1 caught that draft 2 said four agents and the fourth's boundary did not exist. Draft 3
removed U14 and re-asserted three. **The correct number, on this plan's own dependency graph,
is two: U9 and U6→U7. U12 joins after U6 completes.**

**Suggested fix (mine, verify before adopting):** rewrite `:906` to read that **U9 and U6→U7
run as two concurrent agents once U5 has landed, and U12 becomes available as a third once U6
completes** (it does not need to wait for U7). Restate Wave C as two lanes plus a deferred
third, and add U12's `needs U6` to the Wave C table's own row rather than leaving it only in
§3 and in U12's prose - the table is what an orchestrator reads.

---

### H3 - The v1 1000 page cap is built by both U6 and U12, in a file only U6 owns. This is M6's sibling, fixed for the result cap and not for this

Round 1's M6 found the result cap built twice with no owner named. Draft 3 fixed that
carefully and explicitly (`:502-507`: *"U5 built the in-tool half; U6 adds the transport half
... neither unit may assume it owns all of it"*). The same shape survives one line away:

- **U6 builds** (`:481`): *"page cap 500 on v2 and **1000 on `/v1/jobFeed`**"* - inside
  `services/jobvite_client.py`, which §4 gives U6 exclusively.
- **U12 builds** (`:751`): *"the v1 base, the separate ... credential class, **the 1000 page
  cap**, and the `jobs`-keyed envelope"* - and §4 gives U12 only *"the `get_job_feed` half of
  `tools/jobs.py`"*, with `services/jobvite_client.py` listed as **read, not write**.

`DESIGN.md:413` states the cap once (*"Page cap **500** on v2, **1000** on `/v1/jobFeed`"*), in
§4.5, which is client-layer. So one behaviour, one home, two claimed builders - and the second
builder is denied write access to the only file it can live in.

This is the fifth collision, and §4 says *"Four collisions to plan around, all real"* - so it
is both unnamed and outside the count.

**Suggested fix (mine, verify before adopting):** give the 1000 cap to **U6** outright, matching
where the design puts it, and strike *"the 1000 page cap"* from U12's Builds list, replacing it
with *"consumes U6's `/v1/jobFeed` page cap; does not implement it"* - the same sentence shape
draft 3 already used successfully for the result cap. Then raise §4's collision count to five
and add this row, since the count is stated as exhaustive.

---

## MEDIUM

### M1 - U8's verification has no arm proving a candidate read returns anything, and its absence arms all pass against a tool that returns nothing

This is the shape the brief asked me to hunt, and U8 is where I found the clearest instance.
U8's Verified-by list (`:599-614`) is: EEO fields absent (#6), fencing (#19), unknown field
dropped (#20), casing pinned (#24), PII not emitted (#5), path-keyed not name-keyed, two tools
not one, date/empty-string normalisation.

Against a `search_candidates` that returns an empty page every time: #6 passes (no EEO fields
appear), #5 passes (no PII is emitted), #20 passes (no field is stringified). #19's red-team
cases and the normalisation arm do exercise real data, so the unit is not fully vacuous - but
the three arms carrying the unit's two Criticals (C6-I1, C6-S1) are the vacuous ones.

The blanket rule at `DESIGN.md:1332-1333` is exactly this, and draft 3 applied it correctly to
U10 (`:698-702`) and U14 (`:816-819`). U8 did not get the same pass.

**Suggested fix (mine, verify before adopting):** add to U8's list - *"Positive control: a
populated candidate record round-trips with every allow-listed field present and correctly
normalised, so #6, #5 and #20 are asserted against a non-empty result rather than against
silence."* Consider stating it in the same load-bearing terms U10 uses, since U8 carries two
Criticals and U10 carries one.

### M2 - §8 case #2 asserts an absence in the log stream, and nothing in U3 proves the log stream carries records

U3 verifies #2 as *"a secret never reaches a log record, including the whole `jobFeed` URL"*
(`:369`). Against a logger that is misconfigured and emits nothing, this passes.

The design anticipated this failure mode for the audit stream and solved it by pairing #4
(positive, *"positive on purpose"*) with #5 (absence) - `DESIGN.md:1236-1239`. **#2 has no such
pair, and #4 does not supply one**: #4 proves the *audit event* exists, which is a different
stream from the `loguru` log records #2 is about. The plan's own list of cases carrying the
blanket control (`:113-115`) does not include #2.

U7's #13 does prove retry log lines exist, but that is four units later.

**Suggested fix (mine, verify before adopting):** add a positive arm to U3's #2 - *"asserted
against a log stream proven non-empty: the same call emits a log record carrying the request's
non-secret attributes, and the `sc=` value is absent from it."* This is a plan change, not a
design change; if you would rather it be a design change, it is the natural companion to
`DESIGN.md:1236-1239` and worth raising as a Q6.

### M3 - "Nine of the fifteen variables carry a value" is false; seven do

`IMPLEMENTATION-PLAN.md:236`. Counted off the committed `.env.example`:

- **Seven carry a value**: `JOBVITE_ENABLE_WRITES=false`, `JOBVITE_MCP_TRANSPORT=stdio`,
  `JOBVITE_MCP_HOST=127.0.0.1`, `JOBVITE_MCP_PORT=8000`,
  `JOBVITE_TLS_TERMINATED_BY_PROXY=false`, `JOBVITE_MAX_RESULTS=50`,
  `JOBVITE_OUTBOUND_RATE_LIMIT=6`.
- **Eight are empty**: the six secret-class ones the plan names, plus `JOBVITE_TOOLS` and
  `JOBVITE_PAGINATION_START_BASE`, which are empty and **not** secret-class.

The paragraph this sits in exists specifically to correct round 1's H1 - draft 2's false claim
about the committed tree. The direction is now right and **the assertion U0 actually schedules
is correct** (I verified all six secret-class variables are empty, and the `.gitignore` claim:
`.env`, `.env.*`, `*.key`, `*.pem`, `secrets/` are all present). Only the supporting count is
wrong. Given this project's record, a wrong number inside a correction of a wrong number is
worth fixing before it is copied forward a third time.

**Suggested fix (mine, verify before adopting):** *"**Seven** of the fifteen variables carry a
value, and two of them - `JOBVITE_MAX_RESULTS=50` and `JOBVITE_OUTBOUND_RATE_LIMIT=6` - are the
answer to Q1. Eight are empty, and only six of those eight are secret-class: `JOBVITE_TOOLS`
and `JOBVITE_PAGINATION_START_BASE` are empty non-secrets, so an assertion keyed on emptiness
rather than on secret-class would admit them wrongly."* That last clause is the one that
actually protects the test.

### M4 - U9 asserts five middleware are absent but positively verifies only one of the three it adopts

U9 (`:661-664`) requires asserting `ResponseCachingMiddleware`, `ErrorHandlingMiddleware`,
`ResponseLimitingMiddleware`, `RetryMiddleware` and `PingMiddleware` are **absent**, each
excluded for a measured reason. Good regression guard - but an absence assertion over a
middleware stack passes trivially if the stack is empty or never constructed.

U9 adopts three: `RateLimitingMiddleware`, `TimingMiddleware`, `StructuredLoggingMiddleware`.
Only the first is positively verified (the per-client bucket test, `:646-648`). `TimingMiddleware`
and `StructuredLoggingMiddleware` - including `include_payloads=False`, which C2-I1 is the row
for - have no assertion at all.

**Suggested fix (mine, verify before adopting):** add - *"Positive control for the absence
assertion: the three adopted middleware are present in the constructed stack, and
`StructuredLoggingMiddleware` is constructed with `include_payloads=False` (C2-I1). Asserting
five absences against a stack never proven non-empty cannot distinguish 'excluded' from 'no
middleware at all'."*

### M5 - U2's `request_id_var` reset test has no arm proving the id is set

U2's last bullet (`:350-351`): *"`request_id_var` resets in a `finally`; an id cannot leak into
the next invocation on a reused worker task."* A `ContextVar` that is never set at any point
passes this perfectly.

U3 mints it and U5 asserts it on the wire, so the property is covered downstream - but U2 is
handed to an agent as a standalone unit (§4 Wave A, exclusive owner of
`utils/correlation.py`), and its verification list is what that agent builds to.

**Suggested fix (mine, verify before adopting):** *"...and the paired positive arm: inside a
simulated invocation the var reads back the id that was set, so the leak test is asserted
against a var proven to hold a value."*

---

## LOW

### L1 - No unit says how tests reach the fixtures, which live outside `tests/`

All fifteen fixtures exist and match §1's tiers exactly - I checked the disk. But they are in
`docs/research/fixtures/`, and no unit states whether tests read them from there, or whether
U0 copies them under `tests/fixtures/`. U4 asserts five of them **byte-exact**, so the path is
load-bearing: an agent that copies rather than references creates a second copy that can drift
from the ground truth silently.

**Suggested fix (mine, verify before adopting):** one line in U0's Builds - *"tests read the
recorded fixtures from `docs/research/fixtures/` by path; they are not copied under `tests/`,
because a second copy of a byte-exact ground truth can drift from the first."*

### L2 - U7's "I read it at `STANDARDS.md:375` today" is ambiguous about which `STANDARDS.md`

`:578`. §8 disclaims reading the standards corpus (*"Every `standards/...:line` citation in this
plan is quoted from `DESIGN.md` or an ADR"*), so a direct reading claim reads as a contradiction.
It is not one: the line resolves in **`docs/research/STANDARDS.md`**, the local research digest,
which I confirmed carries B47 at `:374-375`. I also confirmed the corpus agrees
(`architecture/reference-architecture.md:95` gives `circuitbreaker ^2`), so the substance is
sound in both places.

**Suggested fix (mine, verify before adopting):** write it as
`docs/research/STANDARDS.md:374-375` and add *"the local research digest, not the corpus"*, so
an agent told to *"confirm the `^2` constraint is current"* knows the digest is not the
authority for currency.

---

## NIT

### N1 - §4's Wave A table gives `.env.example` to U1, and U0 asserts against it

U0's §8 #3 asserts against `.env.example` (`:229-232`) while §4 lists that file under U1's
exclusive ownership. No live collision - U0 completes before U1 starts, and U0 only reads - but
the table's own rule is *"One owner per file"* and the reader has to derive the read/write
distinction.

**Suggested fix (mine, verify before adopting):** add a *"Reads but does not write"* column to
the Wave A table, as Wave C already has, with `.env.example` in U0's row.

---

## Part 2 - Is this plan safe to hand to parallel implementation agents?

### File-ownership boundaries

**The three named lanes are disjoint at file level. The scheduling around them is not.**

Wave A (U1 / U2 / U11) is genuinely disjoint; the one shared file, `pyproject.toml`, is called
out with a workable resolution. Wave B correctly refuses to parallelise U3 and U4 even though
their files differ, on the grounds that U4's assertions run against U3's implementation - that
is the right instinct and rarer than it should be.

Wave C is where it breaks, and in two ways: **H2** (U12 is scheduled concurrently with a unit it
depends on) and **H3** (U12 is told to build a behaviour in a file it may not write). The four
named collisions are all real and correctly sequenced - I checked each against `DESIGN.md:258-272`.
There is a fifth.

The `models/` analysis behind Q5 is correct: `DESIGN.md:270` genuinely defines `models/` as
output models one per tool, and the design genuinely names no home for input models. Dropping
U14 out of the fan-out was the right call.

### Does each unit's stated verification actually verify it?

Mostly yes, and in several places conspicuously well - U6's *"de-duplication cannot recover a
never-returned record"*, U10's approved-write row-counter control, U5's *"deleting a fencing
decision fails the suite"*, and U1's insistence that #18 assert the teardown side effect and not
the exit code are all tests that can fail for the right reason.

Four instances of the requested shape survive: **M1** (U8, the largest), **M2** (#2 in the log
stream), **M4** (U9's middleware absences) and **M5** (U2's ContextVar). None is the same defect
round 1 found in U10 - that one is properly fixed.

### Are the design's ceilings preserved as uncertain?

**Yes - all five, and this is the strongest part of the document.** I checked each at its point
of use, not just where it is first declared:

| Ceiling | Carried? |
|---|---|
| Capability-drift diff | **Yes**, twice. U0's inherited-limit paragraph (*"standing it up in CI does not execute it"*) and §6's second entry. Explicitly says it cannot be retired by building it |
| Circuit breaker | **Yes.** U7's closing *"unevidenced until this unit's tests run"*, §6 item 1, and §8's *"no breaker-library survey was run"* |
| Jobvite dedupe / idempotency key | **Yes.** U10: *"cannot be built because nothing establishes Jobvite accepts one (B108)"*, disclosed in README rather than becoming a plan item |
| Read-only key | **Yes**, and carefully. U13 states C5-E1 stays a High residual *after* the unit, and names the over-reading it guards against |
| `JOBVITE_OUTBOUND_RATE_LIMIT=6` | **Yes.** *"A conservative guess, not a vendor figure"* at U1, at U7's point of use, and in Q1, with checklist row 9 named as what replaces it |

I found no place where the plan treats a stated ceiling as settled. The `JOBVITE_MAX_RESULTS=50`
handling is a good example of the discipline: it says plainly that 50 was chosen for internal
consistency with a caller-facing string and is *"not a measurement of anything."*

---

## Judgement 1 - Which unit would I least want to hand to an agent in isolation?

**U8 - candidate reads.** Not U7, which is the plan's own answer and is defensible, but U7 has
the best scaffolding in the document: one named experiment, a design-sanctioned fallback, and a
throwaway harness that retires the risk before the unit starts. An agent can execute U7.

U8 compounds four things no single one of which would worry me:

1. It shares `utils/redaction.py` with U3 and holds only half of it - and that file is at 95%
   coverage precisely because it holds two Critical-rated mechanisms with nothing in common.
2. It is told to *"write the structural assertions first"*, and the structural tier is
   deliberately **prose, not a file** - a description of an envelope observed once, that cannot
   ship. An agent given U8 alone must derive assertions from §1's paragraph and get the
   direction of the derivation right, or it encodes the synthetic fixtures it was warned about.
3. It carries two Criticals (C6-I1, C6-S1), and per **M1** its arms for them pass against a
   tool that returns nothing.
4. Its fencing depends on a mechanism U5 built - generating camelCase paths from snake_case
   models - which §6 says *"the design does not say how"*, and U8 is the first unit where it
   must fire on real content rather than on one small model.

An agent that does all four correctly has done the hardest reading in this project. An agent
that does three of four ships a green suite over a tool that silently returns nothing.

## Judgement 2 - If executed as written, what goes wrong first?

**Wave C's fan-out, via U12.** On the record as a carried risk, not as a defect - H2 and H3 are
the defects; this is what happens if they are fixed on paper and the habit survives.

Wave C is the first place this plan tells an orchestrator it is safe to run agents in parallel,
and it is the place the plan's own dependency graph contradicts its own scheduling table. The
concrete failure: an agent is handed U12 at U5-landing, discovers it needs the per-resource
pagination base and the v1 page cap, finds both belong in `services/jobvite_client.py`, and -
because the unit brief tells it to *build* the 1000 cap - writes them there while U6's agent is
mid-unit in the same file. Nobody notices until U6's page-cap tests and U12's disagree, by which
point both agents have committed and one of them has lost work.

The plan already knows the shape of this. `:910-913` is a good rule - *"no agent runs `git
stash`, and no agent switches branches on a tree another agent is working"* - and it is aimed at
the right failure. It just does not cover the case where the schedule itself puts two agents in
one file, which no discipline about stashing will catch.

---

*Round 2 by `plan-review-r2`, 2026-08-28, against `DESIGN.md` at `8814d69`. All three gates
re-run from the repo root. `docs/DESIGN.md` and the plan were not edited; nothing was committed.*
