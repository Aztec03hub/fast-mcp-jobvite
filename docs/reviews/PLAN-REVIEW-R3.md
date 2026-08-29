# PLAN-REVIEW-R3 - `docs/plans/IMPLEMENTATION-PLAN.md` draft 4

Reviewer: `plan-review-r3`, a fresh reviewer. I wrote none of this plan and conducted neither prior
round. 2026-08-28, 03:16 PM CDT.

Subject: `docs/plans/IMPLEMENTATION-PLAN.md`, draft 4, 1,337 lines, untracked.
Design read from the frozen git object `git show 135c3ac:docs/DESIGN.md` (1,994 lines), **not** the
working tree. Repo HEAD at review time: `b08c6e1`. `git diff 135c3ac HEAD -- docs/DESIGN.md` is
empty, so the frozen text and the working tree agree today - but every line number below was taken
from the `135c3ac` object regardless.

---

## Verdict

**NOT READY** - by one editing pass, with no design change and no ADR required, and **with no reason
to pause U0.**

**TALLY: 0 Critical / 2 High / 5 Medium / 2 Low / 1 Nit.**

I want to be precise about what that verdict does and does not mean, because the brief said this was
intended to be the last round and that I should neither manufacture nor suppress.

- **No Critical.** I looked for one and there is not one. Nothing here invalidates a unit, reopens a
  design question, or contradicts the frozen design.
- **U0 is unaffected.** Every finding lands on U5-and-later scheduling or on citation text. U0's
  assertions verified clean again this round. The agent building it should continue.
- **The two Highs are real and neither is cosmetic.** H1 is the third consecutive draft to ship
  wrong-subject cites while claiming the class was fixed - and this time the claim is the plan's
  headline. H2 is a concurrent-write collision between two units the plan schedules **into the same
  wave**, in a file the plan hands to one of them exclusively.

What I verified and found **clean**, so it is not re-litigated below:

| Checked | Result |
|---|---|
| All three gates, re-run from repo root at `b08c6e1` | `check-coupling.py` exit 0 (60 rows, 17 C/H, 23 naming a §8 case); `check-coupling-controls.py` exit 0, **34/34 fired**, post-run re-check exit 0; `check-coupling-sweep.py` exit 0, **0 escapes are holes** |
| All 25 `§8 #n` line anchors in the §1 table, subject by subject against `135c3ac` | **25/25 land on their own case.** No drift, no off-by-one |
| Every threat-row cite (`:1681` C2-I1, `:1695` C3-I1, `:1738` C6-D1, `:1759` C8-R1, `:1795` empty must-mitigate table, `:1816` C5-R1/C5-E1 ledger row, `:1830` production-release list) | **7/7 land on their own row.** The row-id→line repoint worked |
| §8 case ownership: does every case have exactly one owning unit? | **25/25 owned.** #16 split U5/U10 as stated |
| `.env.example` counts, read off the `135c3ac` object | **15 variables, 8 empty, 7 valued.** All six secret-class variables empty; `JOBVITE_TOOLS` and `JOBVITE_PAGINATION_START_BASE` the two empty non-secrets. Plan is correct on every number |
| The 17 Critical/High rows | Confirmed 17, enumerated below in M3 |
| ~68 distinct `DESIGN.md:<line>` cites outside the two checked subsets | 6 wrong (H1), 2 over-extended (L1, L2), the rest land on subject |

**Round 2 got nothing wrong that I can find.** Its five-Medium verification-shape class was correctly
identified and, with one exception (M2), correctly fixed. Its H2 lane-count finding was correct and
the fix was correct as far as it went (M4 is the part it did not reach).

---

## H1 - Six wrong-subject `DESIGN.md` cites, in ten places, all outside the two subsets draft 4 actually checked

**Severity: High.**

The plan's header is a sustained argument that draft 4 fixed the wrong-subject citation class. Lines
39-46 say draft 4's check is *"subject-level"*; lines 48-55 use the author's own relapse as evidence
that non-blankness is structurally too weak.

**Both subsets it names are genuinely clean.** I re-derived all 25 `§8 #n` anchors and all 7
threat-row cites independently and every one lands on its own subject. That work is sound and I am
not disputing it.

**The problem is scope.** Line 57-58 states the limit honestly:

> What was run here is a text-identity repoint plus a subject-by-subject check of every `§8 #n`;
> cites into §4-§7 prose carry the weaker guarantee.

So the class was **not** fixed as a class. It was fixed for two subsets and left on text-identity
repointing everywhere else - which is the mechanism the same header says *"silently no-ops"*. I
swept the remainder. Six are wrong, and two of them anchor the plan's most load-bearing claims.

| # | Plan line(s) | Cite | What the plan says it supports | What is actually at that line in `135c3ac` | Correct cite |
|---|---|---|---|---|---|
| a | `:238`, `:1137` | `DESIGN.md:43-45` | *"names exactly **two** mechanisms in the whole design that 'sit among executed results and borrow their credibility'"* | The **freeze condition** - 0C/0H/0M vs the must-mitigate table coming apart | **`:64-68`** |
| b | `:667`, `:1106` | `DESIGN.md:44-47` | *"the two mechanisms `DESIGN.md:44-47` names as **never executed**"* | Same freeze-condition paragraph | **`:64-68`** |
| c | `:1062` | `DESIGN.md:39-51` | *"says **no claim about a Jobvite success response is verified, because none has ever been observed**"* | Same freeze-condition paragraph | **`:63`** (the sentence is quoted verbatim there) |
| d | `:451`, `:1318` | `DESIGN.md:1238-1241` | *"The design solved this exact shape for the audit stream by pairing #4 with #5"* / *"shows the design already knows this shape"* | `--strict-markers` and the typo-in-marker-name argument. Nothing about #4/#5 | **`:1229-1231`** |
| e | `:711`, `:1324` | `DESIGN.md:1335-1336` | *"the blanket rule"* / *"the design's own blanket positive-control rule"* | Case **#17**, trace context, *"two arms... both are required"* | **`:1319-1320`** |
| f | `:1262` | `DESIGN.md:1330` | *"records the same measured residual in case **#18**'s own bullet"* | Case **#16**, *"The success arms assert it in `_meta`..."* | **`:1293`** |

Four observations that make this High rather than Medium:

1. **(a)+(b)+(c) are one cluster, all landing ~21 lines short, on a paragraph about the freeze.** They
   are the anchors for the plan's *"two never-executed mechanisms"* pair - the backbone of U0's
   inherited-limit paragraph and of §6's entire riskiest-unit ranking. An agent that follows the cite
   to `:43-47` finds a paragraph about review rounds and must decide, alone, whether the plan is
   confused or the claim is unsupported.
2. **(d) is load-bearing for Q6**, which the brief asked me to adjudicate. The plan's argument that
   the design *"already knows this shape"* rests on a cite that points at the strict-markers
   paragraph. The **substance** is right - the design does pair #4/#5 and says so, at `:1229-1231` -
   but the evidence offered for it is not.
3. **This is the fix-one-instance-miss-the-sibling shape the plan itself names three times.** Plan
   line 444 cites `:1229-1232` for the #4/#5 pairing **correctly**, in U3. Two other places cite
   `:1194-1197` for the same fact. One instance was right and its siblings were not swept.
4. **(e) is self-undermining in the same way (a) is:** the plan cites the wrong line for the blanket
   positive-control rule in the two places where it is arguing about positive controls, while citing
   `:1319-1320` correctly at lines 143, 816 and 938.

None of this changes a single scheduling or verification decision. Every claim these cites support
is **true**; only the anchors are wrong. That is exactly why it survived three drafts.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Apply the six corrections in the table
> above verbatim. Then, so the header stops overstating: replace lines 57-58 with a statement of
> what was actually swept, e.g. *"Three sets were checked subject by subject: every `§8 #n`, every
> threat-row cite, and every cite into §1's front matter and §8's prose. Cites into §4-§7 prose
> carry the weaker text-identity guarantee."* - and only claim the third set once it has been run.
> The cheapest durable version is to extend the row-id→line repoint to **quoted-string identity**:
> where the plan quotes the design verbatim (as it does in a, b, c and e), locate the cite by
> `grep -n` on the quoted fragment rather than by the remembered line number.

---

## H2 - Wave C has a sixth collision it does not name: tool registration in `server.py`

**Severity: High.** This is the direct answer to the brief's *"is the fifth complete, or is there a
sixth?"*

The five named collisions are all real and I confirmed each against the design's module layout
(`DESIGN.md:280-298`). **They are not exhaustive.**

**The gap.** Four units each add a tool that must be registered, and registration is
config-conditional (`DESIGN.md:925-929` requires `create_candidate` registered only on the
`JOBVITE_ENABLE_WRITES` **and** `JOBVITE_TOOLS` conjunction):

| Unit | Adds | Plan text |
|---|---|---|
| U5 | `search_jobs` | `:516` *"`tools/jobs.py` with `search_jobs` only, **registration wired to `JOBVITE_TOOLS`**"* |
| U8 | `search_candidates`, `get_candidate` | `:679` |
| U12 | `get_job_feed` | `:868` |
| U10 | `create_candidate` | `:800` *"**registered only under** `JOBVITE_ENABLE_WRITES=true` and naming in `JOBVITE_TOOLS`"* |

**And the plan never says where registration lives.** `grep -n "regist" IMPLEMENTATION-PLAN.md`
returns no line assigning it to a file. `DESIGN.md:283` gives `server.py` as *"FastMCP instance,
middleware stack, lifespan"* - registration is not named there either, nor anywhere else in §3.

**Meanwhile `server.py` is handed out exclusively, twice:**

- Wave A (`:983`): U1 owns `server.py` outright.
- Wave C (`:1002`): **U9 owns `server.py` (middleware + auth block)** exclusively.

**The live collision.** U9 and U12 are in the same wave by the plan's own table - U9 from
U5-landing, U12 from U6-completion - so they **overlap in time**. If registration lives in
`server.py`, U12 must write a file the table gives to U9. An agent alone has exactly two options,
and the plan's §4 opening names both as the failure it exists to prevent: block, or write into
another unit's file. U8 (also unblocked at U6-completion, see M4) makes it three.

This is materially different from collisions 1-5. Those are all **stated** and sequenced. This one is
an unstated ownership question about a file that two concurrent units both need.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Add a sixth collision to §4's list and
> settle the location in the same edit, because naming the collision without naming the owner leaves
> the agent in the same position:
>
> > **6. Tool registration has no stated home and four claimants.** U5, U8, U10 and U12 each add a
> > tool, and `create_candidate`'s registration is conditional on the `JOBVITE_ENABLE_WRITES` ∧
> > `JOBVITE_TOOLS` conjunction (`DESIGN.md:925-929`). `DESIGN.md:280-298` does not assign
> > registration to a module. **Each unit registers its own tools in its own `tools/*.py` via the
> > `FastMCP` instance imported from `server.py`, and the `JOBVITE_TOOLS` gate is applied at that
> > decorator site.** `server.py` therefore holds the instance, the middleware stack and the lifespan
> > only, and stays U9's exclusively in Wave C. No unit but U1 and U9 writes `server.py`.
>
> I am **not** confident this is the right resolution - the alternative (a single registration block
> in `server.py`, owned by U1, that every later unit appends to) is also defensible and may match
> what the design intends by *"FastMCP instance"*. What I am confident of is that **the plan must
> pick one**, because it is the question an agent alone cannot answer. If the decorator-site answer
> is taken, check whether it needs an ADR: §3's module block *"closes by enumerating the modules this
> design refuses"*, and this is a placement the design does not state either way.

---

## M1 - U14's own "Depends on" line contradicts §4 and Q5

**Severity: Medium.**

Three places in this plan give U14 three different dependency sets:

| Where | Plan line | Says |
|---|---|---|
| U14's own **Depends on** | `:932-933` | *"**U5** (first tool). **Can run in parallel with U8** if the models are already in place"* |
| §3 diagram | `:966` | under U8, *"(also needs U12; owns no file)"* |
| §4 | `:1012-1013` | *"it depends on **U5, U8 and U12** having written their input models"* |
| Q5 | `:1301-1303` | *"depends on **U5, U8 and U12**"* |

The plan spends `:1300-1305` separating "the ownership question" from "the scheduling question" and
concludes U14 *"still runs last"* - correctly. **It then never corrected U14's own Depends line**,
which still explicitly authorises running concurrently with U8.

**Why it matters more than a stale line.** An agent handed U14 reads U14 first. Its Depends line
tells it to start after U5 and permits overlap with U8. U14 is *"the sweep that proves the set is
complete"* (`:934`) - so run early it sweeps an input-model set that U8 and U12 have not written yet,
finds it complete, and goes green. **A vacuous pass on the unit whose entire job is completeness** -
the same class round 2 spent five Mediums on, arriving through the schedule rather than through a
missing arm.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Replace `:932-934` with:
>
> > **Depends on.** U5, U8 and U12 - every unit that writes an input model. It **cannot** run
> > concurrently with U8: U14 is the sweep proving the inbound set is complete, so a run that starts
> > before U8 and U12 have written their input models passes over an incomplete set and proves
> > nothing. It owns no file exclusively and runs last. See [§4](#4-what-can-run-in-parallel) and
> > [Q5](#q5---answered-and-landed-input-models-live-beside-their-tools).

---

## M2 - U12's C5-I1 arm is the sibling Q6's fix did not reach

**Severity: Medium.** This is the direct answer to the brief's *"check it as a class"*.

I checked all fifteen units for an arm that would fail if the unit built nothing. **Fourteen pass.**
Draft 4's fix is real and it is broad - U8's positive-control-first, U9's adopted-middleware-present,
U10's approved-write-moves-the-counter, U2's var-reads-back-the-id, U14's just-inside-each-limit,
U11's unexpired-entry-honoured. That class of work was done properly and I want it recorded as such.

**U12 is the escapee.** Its entire *"Verified by"* is `:878-881`:

> The `jobFeed` URL never reaching a log record whole, `sc=` redacted - this is C5-I1, a **High**...
> Plus `jobfeed_success.json` / `jobfeed_empty.json` round-tripping, and the third envelope key
> normalised.

The first arm is **an absence over a log stream** - byte-for-byte the shape Q6 exists for. U3's #2
got the pairing (`:448-449`: *"asserted against a log stream proven non-empty... the `sc=` value is
absent from *that record*"*). U12's C5-I1 did not, and it is the **same secret in the same URL**, one
unit later, carrying a High.

The round-trip arm does not close it: it proves the tool returns data, not that the logger emitted
anything. Against a misconfigured logger emitting nothing, the round-trip passes **and** the absence
passes.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Rewrite U12's first verification bullet
> to carry U3's construction:
>
> > - The `jobFeed` URL never reaching a log record whole, `sc=` redacted - C5-I1, a **High**, and
> >   the one endpoint that structurally requires the secret in the query string. **Asserted against
> >   a log stream proven non-empty by the same call**, exactly as U3's #2 is: the call emits a log
> >   record carrying the request's non-secret attributes, and the `sc=` value is absent from *that
> >   record*. Against a logger emitting nothing the absence alone passes, and this arm carries a
> >   High.
>
> And, so the class check is stated as a class rather than re-derived next round, add to §8's
> verified-rather-than-asserted paragraph: *"Every unit was checked for at least one arm that fails
> if the unit built nothing; the absence-over-a-log-stream shape specifically was swept for siblings,
> and #2 (U3) and C5-I1 (U12) are the two instances."*

---

## M3 - §8's threat-id arithmetic is stale and contradicts itself two sentences later

**Severity: Medium.**

Plan `:1197-1203` reads:

> **The plan names 16 threat ids and the design carries 17 Critical/High rows.** ... Seven
> Critical/High rows are named by no unit: C1-R1, C2-R1, C4-E1, **C5-E1**, C7-I1, C8-I1, **C9-T1**.
> ... Two were genuinely thin and are now addressed: **C9-T1 in U0's** inherited-limit paragraph and
> in §6, and **C5-E1's ceiling in U13.**

Measured against the plan text and the frozen design:

- **"names 16 threat ids"** - the plan's §2 units name **17** distinct ids (`C1-I1 C1-S1 C1-T1 C2-I1
  C3-I1 C4-D1 C4-D2 C4-R1 C4-S1 C5-E1 C5-I1 C5-S1 C6-D1 C6-I1 C6-S1 C7-T1 C9-T1`); the whole plan
  names **25**. Neither is 16.
- **"Seven ... named by no unit"** - two of the seven **are** named by units. C9-T1 appears at
  `:242` (U0) and C5-E1 at `:909` and `:914` (U13). The correct count is **five**: C1-R1, C2-R1,
  C4-E1, C7-I1, C8-I1.
- **The paragraph refutes its own list four lines later**, naming C9-T1's home as U0 and C5-E1's as
  U13 while the list above still counts both as unowned.

The design's 17 C/H rows, for the record, verified against `135c3ac`: C1-S1 `:1666`, C1-T1 `:1668`,
C1-R1 `:1669`, C1-I1 `:1670`, C2-R1 `:1680`, C4-S1 `:1703`, C4-R1 `:1705`, C4-E1 `:1709`, C5-S1
`:1722`, C5-R1 `:1724`, C5-I1 `:1725`, C5-E1 `:1727`, C6-S1 `:1733`, C6-I1 `:1736`, C7-I1 `:1748`,
C8-I1 `:1760`, C9-T1 `:1770`. **The "17" is correct.**

This is a count carried through its own correction - the defect the plan names at `:89-94`,
`:285-286` and `:1048-1051`, and which `DESIGN.md:1848-1857` legislates against directly (*"This
table is the count. No sentence in this section states a total for it."*).

> **Suggested fix (MY SUGGESTION - verify before adopting).** Replace the first sentence and the list
> with a derived form:
>
> > **The plan's §2 units name 17 distinct threat ids; the design carries 17 Critical/High rows, and
> > the two sets are not the same 17. The id list is not a coverage map and must not be read as one.**
> > **Five** Critical/High rows are named by no unit: C1-R1, C2-R1, C4-E1, C7-I1, C8-I1. Most are
> > covered in substance by a §8 case some unit does schedule - C8-I1 by #3 in U0, C4-E1 by #22's
> > accept-carrying-false arm in U10, C7-I1 by #5 in U3. The two that were genuinely thin now have
> > homes: C9-T1 in U0's inherited-limit paragraph and in §6, and C5-E1's ceiling in U13.
>
> Better still, given this document's history with counts: state the **list** and drop the totals
> entirely, per `DESIGN.md:1848`.

---

## M4 - U8 has no wave and no earliest start, so Wave C's lane count is understated a third time

**Severity: Medium.** This is the rest of the brief's lane-count question.

The brief noted the lane count *"has been wrong twice in the same place."* Draft 4's correction -
two lanes, U12 joining at U6-completion - is **correct as far as it goes**, and I verified it against
the dependency graph. It does not go far enough.

**U8 appears in no wave at all.** §4 covers Waves A, B and C; U8, U10, U13 and U14 are placed in
none. But U8's dependencies (`:681`: *"U5 ... U6, U3"*) resolve at **U6-completion - the identical
moment U12 unblocks.** And U8's write set (`models/`, `utils/normalise.py`, `utils/redaction.py`,
`tools/candidates.py`) is disjoint from U9's, from U6→U7's, and from U12's.

So at U6-completion the real picture is **four concurrent lanes**: U7, U9, U12 and **U8** - not the
three the plan's closing sentence describes (`:1037-1038`):

> **Wave C is two lanes, not three: U9 and U6→U7 run concurrently once U5 has landed. U12 becomes a
> third lane when U6 completes** - it does not need to wait for U7.

The consequence is the mirror of the one draft 4 just fixed. Draft 3 scheduled a unit **too early**;
draft 4 leaves the plan's largest and riskiest read unit - the one `:686` calls *"the unit I would
least want to hand to an agent in isolation"* - with **no scheduled start at all**. An orchestrator
reading the table, which the plan at `:1045-1046` says is the artifact an orchestrator reads, has no
row for U8.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Add U8 to the Wave C table and correct
> the closing sentence:
>
> > | U8 | `models/`, `utils/normalise.py`, the fencing half of `utils/redaction.py`, `tools/candidates.py` | `services/jobvite_client.py` | **needs U6 - starts when U6 completes** |
> >
> > **Wave C is two lanes at U5-landing - U9 and U6→U7 - and widens to four when U6 completes, as
> > U12 and U8 both unblock.** Neither needs U7. U8 and U12 have disjoint write sets and may run
> > concurrently with each other and with U7 and U9.
>
> Verify the disjointness claim before adopting: it depends on H2's registration question, since U8
> and U12 each register a tool. If registration lands in `server.py`, U8, U12 and U9 are **three**
> units in one file and the four-lane claim is wrong.

---

## M5 - U6's "Depends on" says U4; the diagram and the Wave C table say U5

**Severity: Medium.**

- U6's own Depends line (`:570`): *"**Depends on.** U4. Sequential with U7."*
- §3's diagram (`:960-961`) nests U6 under **U5**.
- Wave C's table (`:1003`) gives U6→U7 an earliest start of *"starts at U5"*.

Checked against write sets, **U6's own line is the correct one**: U6 owns
`services/jobvite_client.py`, which U4 writes and U5 does not. U6 could genuinely begin at
U4-completion, concurrently with U5.

Two consequences, in opposite directions, and the second is the one that matters:

1. The table needlessly delays U6 - and therefore U12 **and** U8, both of which key off
   U6-completion (M4). The critical path is longer than it needs to be.
2. More seriously, it is **the same defect draft 4 just fixed, pointing the other way.** Plan
   `:1045-1046` says the earliest-start column exists *"because the table is what an orchestrator
   reads and the dependency was only ever in the prose."* Here the prose and the table disagree
   again, and this time the prose is right. An orchestrator following the table and an agent
   following its own unit's Depends line get different answers about when U6 may start.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Settle it in the table, which is the
> artifact that governs, and reconcile the diagram:
>
> - Wave C row: change U6→U7's earliest start to **"starts at U4 - U6 owns `services/jobvite_client.py`, which U5 does not write, so it need not wait for U5"**, and retitle §4's Wave C heading from *"after U5"* to *"after U4/U5"*.
> - §3 diagram: move `U6 ──► U7` from under U5 to under U4, keeping U5 as a sibling.
>
> Verify the claim before adopting - specifically, confirm no U5 verification arm requires paging
> behaviour. I read U5's arms as using single-page `MockTransport` responses only (`:542-557`), but
> that is my reading of the plan, not an executed result.

---

## L1 - `DESIGN.md:1333-1335` spills into the next case

**Severity: Low.**

Plan `:547`: *"`DESIGN.md:1333-1335` is explicit that asserting on the `ToolResult` object would
pass while the wire carried nothing."*

The sentence runs `:1281-1283`. Line `:1284` is the **first line of case #17**, trace context. The
cite starts one line late and ends one line into a different case. It resolves to non-blank,
plausible text, and the claim it supports is true - the exact profile the plan's own header warns
about at `:41-46`.

> **Suggested fix (MY SUGGESTION - verify before adopting).** Change `DESIGN.md:1333-1335` to
> **`DESIGN.md:1332-1334`**.

---

## L2 - Two ranges over-extend into adjacent subjects

**Severity: Low.**

- `:162` cites `DESIGN.md:1251-1262` for the fixture tiers. The tiers are `:1207-1212`; `:1213` is
  blank and `:1214-1217` is the synthetic-fixtures docstring sentence, a different subject the plan
  cites separately.
- `:186` cites `DESIGN.md:1258-1260` for *"the sentence"* going in the test module's docstring. The
  sentence is `:1214-1215`; `:1216` begins the `CREDENTIAL-CHECKLIST.md` conversion clause.

Neither misleads. Both are the range-contraction-and-expansion drift that goes unnoticed because a
narrowed or widened range still resolves.

> **Suggested fix (MY SUGGESTION - verify before adopting).** `:1207-1218` → **`:1207-1212`**;
> `:1214-1216` → **`:1214-1215`**.

---

## N1 - "exactly one owning unit, except #16" is true of #5 as well

**Severity: Nit.**

Plan `:1209-1211`: *"all 25 cases have exactly one owning unit, except #16, whose four arms are
split between U5 and U10 by design."*

#5 is also worked in two units: U3 owns it as the #4/#5 pair (`:444`), and U8 carries *"§8 **#5**
extended to the candidate path"* (`:719`). This is an extension rather than a second owner, so the
claim is defensible - but a reader auditing the sentence finds a second split and has to decide
whether it counts.

> **Suggested fix (MY SUGGESTION - verify before adopting).** *"...all 25 cases have exactly one
> owning unit, except #16, whose four arms are split between U5 and U10 by design. #5 is owned by U3
> and **extended** to the candidate path by U8, which is an additional assertion on the same case
> rather than a second owner."*

---

## Q6 - the brief's fourth question, answered

**The brief asked: is a plan-level fix sufficient, or does the asymmetry belong in the design as an
ADR? My answer is that it belongs in the design, and this round produced the evidence.**

The plan's own reasoning for keeping it at plan level (`:1327-1330`) is *"That is enough for the
implementation."* For U3 in isolation, that is true - U3's #2 arm as written at `:446-454` is
correct, complete, and would catch the defect.

**But M2 is the counterexample, and it was produced by this exact arrangement.** The pairing lives in
one unit's prose. Nothing propagated it to C5-I1 in U12 - the same secret, in the same URL, over the
same log stream, carrying a High. A pairing stated in the design's §8 would have propagated, because:

1. **§8 is what the gates see.** `check-coupling.py` and GATE-2 resolve §11 rows to §8 cases. A plan
   paragraph is invisible to all three gates. The plan established this itself in Q2 (`:1260-1266`):
   a case's protection comes from a §11 row naming it, and *"GATE-2 stops a case's justification
   being quietly stripped, and it does not make deletion visible."* A plan-level pairing has neither
   protection.
2. **§8 is what a later reader reads.** The plan says so at `:1328-1330`: an ADR *"would settle
   whether the design wants the pairing stated where it states the other one, so a future reader of
   §8 sees #2 and #4 as the same construction rather than discovering the asymmetry in a plan."*
   That is the right question and the right answer is yes.
3. **The design already made this call once, for the same reason.** `DESIGN.md:1280-1282` pairs #4
   and #5 explicitly *"so that neither can be satisfied by silence."* #2 is the same construction on
   a different stream. Leaving one pair in the design and its twin in a plan is the two-lists defect
   the design designs around at `:1497-1501` and `:202-205`.

**Recommendation.** Keep U3's plan-level arm exactly as written - it is correct and it should not
wait. File the ADR **in parallel, not as a blocker**, proposing that `DESIGN.md` §8 case #2 gain a
paired-positive clause in the same terms as #4/#5, **and that its scope name C5-I1's arm in U12 as
the second instance** so the sibling is closed in the design rather than in a plan. That last part is
what M2 shows a narrower ADR would miss.

This does not gate implementation, and I would not hold U0, U3 or U12 for it.

---

## Judgement 1 - if five agents took the parallel units tomorrow, what breaks first?

**`server.py` breaks first, and it breaks quietly.**

Take the widest realistic fan-out: U5 has landed, U6 is running, and agents pick up U9, U12, U8, U7
and U14.

1. **U9 and U12 collide in `server.py` (H2).** U12 finishes `get_job_feed` in `tools/jobs.py` and
   needs it registered. The plan tells it `server.py` is U9's, exclusively. It has no one to ask. It
   either stalls - and a stalled agent usually **guesses** - or it edits `server.py` while U9 is
   rebuilding the middleware and auth block in the same file. Both agents' work is correct; the merge
   is not. This is the first thing that breaks because it is the first thing that **requires** a
   decision the plan does not contain.
2. **U14 goes green having tested nothing (M1).** Its own Depends line authorises a start after U5,
   in parallel with U8. It sweeps `tools/*.py` for input models, finds U5's, and reports the inbound
   set complete. Nobody notices, because the failure mode of a completeness sweep run early is a
   **pass**. This is worse than the collision: the collision announces itself in a merge, this one
   produces a green result that outlives the round.
3. **U8 is never picked up (M4).** It is in no wave and has no earliest start. The orchestrator reads
   §4 and assigns from the table; U8 has no row. The unit the plan calls the one it would least want
   to hand to an agent in isolation ends up handed to nobody, then handed to somebody late and in a
   hurry.
4. **U6 is held back a wave (M5)**, which delays U12 and U8, which compresses everything after them.

The pattern is worth naming: **every one of these is a place where the plan's prose and its tables
disagree, and the agent reads whichever one it was pointed at.** Draft 4 fixed exactly this defect
for U12 and added the earliest-start column for it. The column is right. It is just not finished.

## Judgement 2 - the single sentence most likely to be misread by an agent working alone

Plan `:216-217`, in U0:

> **If that agent's report contradicts anything specified below, the report wins** - a unit that has
> been built beats a unit that has been described, and this section should be corrected from the
> build rather than the build argued back to this section.

**Why this one.** It is the only sentence in the plan that authorises an agent to **deviate**, and
its scope is set by the word *"below"* - which is ambiguous in the one direction that costs most.
Read as *"below, in this U0 section"* it is a sensible, bounded instruction. Read as *"below, in this
plan"* - and it sits in §2's first unit, with twelve hundred lines below it - it says the U0 agent's
report **overrides every remaining unit.**

The second reading is not a stretch. The preceding paragraph is about the whole plan's relationship
to the build, and the generalisation offered as justification - *"a unit that has been built beats a
unit that has been described"* - contains no scope at all. An agent picking up U1 tomorrow, finding
that U0's `pyproject.toml` did something the plan did not describe, has been told in advance that the
build wins.

**And the sentence has no floor.** The design is **frozen**. Every other deviation in this plan
routes through an ADR - the header says so at `:6-10`, §9 says so at `:1226-1227`, Q5 says so at
`:1307-1313`. This sentence is the one place that grants precedence to a build artifact over a
written specification without naming that limit. If U0's agent lands something contradicting
`DESIGN.md` rather than contradicting the plan, this sentence - read alone, by an agent with no one
to ask - says the build wins. It should say the opposite, loudly.

> **Suggested fix (MY SUGGESTION - verify before adopting).**
>
> > **If that agent's report contradicts anything specified *in this U0 section*, the report wins** -
> > a unit that has been built beats a unit that has been described, and **this section**, and only
> > this section, should be corrected from the build rather than the build argued back to it. **This
> > precedence does not extend past U0, and it does not reach `DESIGN.md` at all:** the design is
> > frozen, and a build that contradicts it is a defect in the build or an ADR, never a correction to
> > the design.

---

## What I did not verify

Genuinely unsettleable or out of scope, rather than untried:

- **Standards-corpus citations** (`STANDARDS.md:374-375`, `readme-standard.md:70/83`,
  `ai/tool-calling.md:171-177`, `backend/testing.md`, `FASTMCP-SPIKE-4.md`, `JOBVITE-API.md:399`,
  `error-contract.md:96-108`). The plan discloses at `:1174-1176` that these are quoted from
  `DESIGN.md` rather than verified at source; I inherited that limit rather than closing it. **U7's
  own instruction to confirm `circuitbreaker ^2` against the corpus (`:662-665`) remains the right
  place for that.**
- **Whether `circuitbreaker ^2` evaluates half-open expiry on the call path.** Unrun by anyone; U7
  names the experiment.
- **Whether U5's verification arms require paging** - the assumption underlying M5's suggested fix.
  Read from the plan, not executed.
- **Whether H2's suggested resolution (decorator-site registration) is what the design intends.** The
  design does not say, which is the finding; the fix is a proposal and may itself need ADR-0012's
  treatment.

---

*Round 3 by `plan-review-r3`, 2026-08-28. Design read from the frozen `135c3ac` git object; repo HEAD
`b08c6e1`; all three gates re-run from the repository root. `docs/DESIGN.md` and
`docs/plans/IMPLEMENTATION-PLAN.md` were not edited and nothing was committed.*
