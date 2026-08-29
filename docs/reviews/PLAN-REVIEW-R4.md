# PLAN-REVIEW-R4 - `docs/plans/IMPLEMENTATION-PLAN.md` draft 5

Reviewer: `plan-review-r4`, fresh - I wrote none of this plan and conducted none of rounds 1-3.
Date: 2026-08-28. Repo HEAD at review: `fd8d0b2`. `docs/DESIGN.md` read from the frozen object
`135c3ac` (`git diff --stat 135c3ac..HEAD -- docs/DESIGN.md` is empty, so the tree copy is the
frozen text, but every citation below was resolved against the object).

## Verdict

**NOT READY** - by one editing pass, and the pass is three table rows, one sentence and one
owner assignment. Nothing here asks for a re-plan, and nothing here is a citation nit dressed up
as a blocker.

**TALLY: 0C / 3H / 5M / 3L.**

Two of the three Highs are the *seventh and eighth* collisions, found the way the brief said the
sixth was found: by asking, for each unit, which file it must **write** that the ownership table
gives to somebody else. The third is a Critical design row whose mitigation the build declined and
which now has no owner.

**Dispatch guidance, since the answer is not a flat "wait":**
- **H2 blocks Wave A** (U1 and U11 are concurrent and both must write `ci.yml` and
  `pyproject.toml`). Fix H2 and Wave A - U1, U2, U11 - is safe to hand out.
- **H1 blocks Wave C's four-lane widening** (U8 and U12 concurrently need `models/`). It does not
  block Wave B.
- **H3 blocks nothing today** but must not be closed by silence: it is a Critical row's stated
  mitigation with no owning unit.

## What I verified rather than trusted

**All three gates, re-run from the repo root at `fd8d0b2`:**

```
python3 docs/reviews/check-coupling.py docs/DESIGN.md    EXIT=0
  60 STRIDE rows, 17 Critical/High, 23 naming a §8 case
python3 docs/reviews/check-coupling-controls.py          EXIT=0   34/34 controls fired
  post-run re-check of the real DESIGN.md: exit=0
python3 docs/reviews/check-coupling-sweep.py             EXIT=0   0 escapes are holes
```

**The suite, which exists now:** `uv run --frozen pytest -q` -> `17 passed, 2 deselected in 0.71s`,
**EXIT=0, zero skips.**

**§1's case table:** I re-counted the §8 bullets in the frozen object - `sed -n '1216,1307p' |
grep -c '^- '` returns **25**, matching the plan. I then subject-verified all 25 line anchors
(`:1220`, `:1221`, `:1222`, `:1226`, `:1232`, `:1236`, `:1238`, `:1240`, `:1244`, `:1246`, `:1250`,
`:1255`, `:1260`, `:1266`, `:1273`, `:1277`, `:1284`, `:1289`, `:1296`, `:1297`, `:1298`, `:1299`,
`:1301`, `:1302`, `:1303`): **every one lands on its own case's text.** §1 is clean.

**The structural cites §4's rulings rest on** - `:283` (server.py = instance, middleware, lifespan),
`:289-291` (tools own their input models; `models/` is output-only, one per tool), `:1319-1320`
(the blanket positive control), `:64-68` (the two never-executed mechanisms), `:202-205` (fencing
paths generated), `:1576-1586` (the two commit-time gates) - **all subject-correct.**

**The draft-5 correction the brief told me to check rather than assume: it is right.** U8 and U12
each declare `Depends on: U5, U6, U3`, §3's diagram marks both `(needs U5 AND U6)`, and U6's
earliest start is U4-completion. Because U5 and U6 both start at U4-completion and can finish in
either order, "start at U6-completion" would have been wrong and "when U5 **and** U6 have both
completed" is the only correct form. **The round-3 reviewer who proposed the original was wrong;
the author's correction of it is right.** Draft 5 gets this one clean.

---

# Findings

Every `Suggested fix:` below is **my suggestion, a hypothesis to verify before adoption**, not an
instruction.

## H1 - The seventh collision: `models/` has one owner and two concurrent claimants

`IMPLEMENTATION-PLAN.md:1035` gives U8 **`models/`** *exclusively*. `:1036` gives U12 only *"the
`get_job_feed` half of `tools/jobs.py`"*. **Both rows carry the same earliest start** - *"starts
when U5 AND U6 have both completed"* - so they are scheduled concurrent, by design, and the plan
says so at `:1087`.

But `get_job_feed` needs an **output model**, and the frozen design puts it in `models/`:
`DESIGN.md:291` reads *"`models/` allow-listed OUTPUT models, **one per tool**; no input model
lives here"* - the plan quotes that same line at `:1359`. U12's own verification requires
`jobfeed_success.json` / `jobfeed_empty.json` to round-trip with *"the third envelope key
normalised"* (`:900-905`), which cannot be asserted without a model. So **U12 must write into
`models/` while U8 holds it exclusively, at the same instant.**

This is collision 5's shape exactly - a file with no stated home and units that overlap in time -
one directory over, and it is the highest-traffic directory in Wave C.

*Suggested fix (mine, verify before adopting):* amend `:1035` to `models/` **candidate** models and
add `models/` to U12's owned set as the **job-feed** model, on the same footing as the `tools/jobs.py`
split the plan already makes - one file per tool, no shared module, so the write sets stay disjoint.
Then name it as **collision 7** in `§4` with the same wording collisions 4 and 5 use, and state
explicitly that `models/` is a directory of per-tool files and never a shared module - otherwise
the first agent to add a shared base class re-creates the collision. Note `DESIGN.md:291`'s "one per
tool" is what makes the split legal without an ADR.

## H2 - The eighth collision: `.github/workflows/ci.yml` and `pyproject.toml` have no owner row, and U1 and U11 are concurrent

`.github/workflows/ci.yml` appears in the plan twice - at `:86` (there is no CI) and `:248` (U0
builds it) - and **appears in no ownership table at all**. `grep -n '\.github/workflows'
docs/plans/IMPLEMENTATION-PLAN.md` returns exactly those two lines.

The built unit is what makes this bite. `docs/worklogs/U0-REPORT.md` §4 defers **three CI steps with
named owners**, and the workflow carries them as commented steps:

- `ci.yml:226-227` - the advisory-audit step, **deferred to U11**;
- `ci.yml:243-244` - the coverage step, **deferred to U1**;
- `ci.yml:236-237` - the capability-drift diff, **deferred to U1**.

**Enabling a commented step is a write to `ci.yml`.** U1 and U11 are both in Wave A
(`:1014`, `:1016`) and are declared *"Genuinely disjoint"* at `:1019`. They are not: both must edit
`ci.yml`, and both must edit `pyproject.toml` - U11 the advisory table it is given, U1 the
`[project.scripts]` entry point that U0 deliberately omitted because it *"names a function U1
writes"* (`U0-REPORT.md`, §1). U13 makes a third claimant on both (`readme = "README.md"`, and the
Quickstart *"exercised by CI on every merge"*, `:1149-1151`).

`:1019-1020` already solves the `pyproject.toml` half for U11 only - *"Have U0 land the empty table
so U11 only edits rows inside it"*. That mechanism is right and just needs extending; the workflow
half has no mechanism at all.

*Suggested fix (mine, verify before adopting):* add a row to the Wave A table -
`| .github/workflows/ci.yml | U0 owns the file. U1, U11 and U13 each enable exactly the commented
step naming their unit and touch nothing else; the step blocks are non-adjacent by construction |` -
and the same treatment for `pyproject.toml` (U0 owns; U11 edits rows inside
`[tool.fast-mcp-jobvite.advisory-ignores]`, U1 adds `[project.scripts]`, U13 adds `readme`). If
that is judged too fine-grained to trust to concurrent agents, the alternative is to make U1 and U11
sequential in Wave A, which costs one lane out of three. I would take the row over the sequencing,
because the edits are genuinely non-overlapping line ranges - but say which, because otherwise the
first two agents to land will find out by conflict.

## H3 - The two commit-time gates are a Critical row's stated mitigation, U0 declined them, and no unit now owns them

`IMPLEMENTATION-PLAN.md:255-256` lists under U0: *"Pre-commit: secret scanning and the
committed-file-type gate (`DESIGN.md:1624-1634`)"*. `DESIGN.md:1624` is subject-correct - *"Two
commit-time gates, both exceeding the standard deliberately"*.

**U0 did not build them.** `U0-REPORT.md` §5: *"Not built: the two commit-time gates of
`DESIGN.md:1621-1634`... I judged it a unit of its own rather than a corner of this one. Flagging
it rather than pretending U0 is complete without it. If it should be in U0, say so and I will build
it next."* There is no `.pre-commit-config.yaml` in the tree. U0 is committed (`b53886e`) and the
task board marks U0 completed.

That question was asked and has not been answered, and the plan still reads as though U0 covers it.
It is not cosmetic: **`DESIGN.md:1808` is C8-I1, a Critical row, and its mitigation text is
literally *"pre-commit secret scanning and a committed-file-type gate, both exceeding the standard
(§10)"***. The plan's §8 says C8-I1 is *"covered in substance by #3 in U0"* - #3 covers the
`.gitignore`/`.env.example` half only. The pre-commit half of a Critical row's mitigation is now
scheduled nowhere.

Under the plan's own precedence rule - *"if the U0 agent's report contradicts anything in THIS U0
SECTION, the report wins"* (`:229`) - the report wins here, and the consequence is that the work
leaves U0 without landing anywhere.

*Suggested fix (mine, verify before adopting):* file it as **U15, commit-time gates**, depending on
U0 only, parallelisable throughout beside U11, owning `.pre-commit-config.yaml` and
`scripts/check_committed_file_types.py`; strike the pre-commit sentence from U0's build list and
replace it with a pointer to U15; and add U15 to §3's diagram on the U11 branch. Verification:
the file-type gate is allowlist-first and fail-closed per `:1581-1583`, so it needs a positive
control (an ordinary `.py` commits) beside each refusal arm, and `DESIGN.md:1632-1634`'s stated
limit - it does nothing about confidential prose in Markdown - must be carried into U15 so a green
gate is not read as covering the incident it was named for. U0's agent has offered to build it; the
cheaper answer may be to say yes rather than to open a unit, but **either answer must be written
down**, because the current state is a Critical mitigation held by an unanswered question in a
worklog.

---

## M1 - U5 has no row in any wave table, which is the "U8 had no wave" defect one unit over

Wave C's table (`:1031-1036`) holds U6→U7, U9, U8 and U12. **U5 is not in it**, and it is not in
Wave A or B either. U5 starts at U4-completion, runs concurrently with U6, and owns real files -
`tools/jobs.py`, the job-list model in `models/`, and per §4's collision-5 ruling its own tool
registration. An orchestrator reading these tables has **no row to assign U5 from and no record of
what U5 owns** - which is verbatim the criticism draft 5 makes of draft 4 at `:1093-1098` for U8.

This is also the *cause* of H1: `models/` looks single-owner only because the unit that writes it
first has no row.

*Suggested fix (mine, verify before adopting):* add U5 as the first row of the Wave C table -
`| U5 | tools/jobs.py (search_jobs half), models/ (job model), the fencing-decision registry |
services/jobvite_client.py | starts at U4 |` - and retitle the section *"Wave C - after U4"*, since
two of its lanes now start there and only U9 waits for U5.

## M2 - `DESIGN.md:413` is a wrong-subject citation, twice, and it is load-bearing for collision 4

`IMPLEMENTATION-PLAN.md:895` and `:1060` both cite `DESIGN.md:413` for the `/v1/jobFeed` page cap of
1000 - `:1060` reads *"`DESIGN.md:413` puts it in §4.5, the client layer"*, which is the sentence
that awards the cap to U6 and denies it to U12.

`DESIGN.md:413` reads: *"On stdio there is no token and thus no `client_id`, but there is exactly
one caller, so the global bucket is correct there."* That is the **rate limiter**, not the page cap.
The page cap is at **`DESIGN.md:434`**: *"Offset-based, `start` and `count`. Page cap **500** on v2,
**1000** on `/v1/jobFeed`."*

The plan uses `:407` correctly elsewhere - `:811`, for *"the limiter has never been exercised on
stdio"*, cites `:407-410` and is right. So one line number is doing two jobs and is wrong at one of
them. **The ruling collision 4 makes is correct; only its anchor is wrong**, which is the precise
failure mode the plan's own preamble says non-blankness cannot catch. It falls inside the residue
draft 5 declares (a cite into §4-§7 prose quoting nothing), so this is the class converging, not
re-opening.

*Suggested fix (mine, verify before adopting):* replace `DESIGN.md:413` with `DESIGN.md:434` at
both `:895` and `:1060`, and quote the fragment - *"Page cap 500 on v2, 1000 on `/v1/jobFeed`"* -
so the cite becomes checkable against what it quotes, which is the durable form the plan already
prefers.

## M3 - The lane-count sentence names the wrong pair for the moment it describes

`:1087` reads *"Wave C is two lanes at U4/U5-landing - U6→U7 and U9 - and widens to FOUR when U5 and
U6 have both completed"*. The table two dozen lines above says U9's earliest start is **U5**, so at
**U4**-landing U9 cannot run. The two lanes at U4-landing are **U5 and U6→U7**; the two lanes at
U5-landing are U6→U7 and U9. The compound *"U4/U5-landing"* is true under one reading and false
under the other, and the pair it names fits only the second.

The count itself (2, then 4) is right. This is the fourth revision of this sentence and it is now
wrong in a smaller way than before, but it is still the sentence an orchestrator reads to decide how
many agents to start.

*Suggested fix (mine, verify before adopting):* rewrite in place as *"Wave C is two lanes at
U4-landing - U5 and U6→U7 - stays two at U5-landing as U5 hands off to U9, and widens to FOUR when
U5 and U6 have both completed, as U8 and U12 unblock together."* Derive it from the earliest-start
column rather than restating it, per the plan's own rule at `:1105-1108`.

## M4 - The licence gate landed as a deny-list; the plan still says allow-list, and the ADR U0 asked for is unfiled and unowned

`:254` lists among U0's CI steps *"`pip-licenses` allow-list"*. The build landed a **deny-list** on
the standard's flag-list (`ci.yml:293-297`), for a measured reason: `U0-REPORT.md` D3 records that
`pip-licenses` reports fifteen distinct spellings for six licences, so `--allow-only` on
`quality-gates.md:288-292`'s five SPDX ids **is red on its first run against a clean tree** - the
same "trains everyone to ignore the gate" failure the plan warns about for `pip-audit` at
`:206-211`. Four packages carry licences on neither list (`MIT-0`, `Unlicense`, `PSF-2.0` shipped;
`MPL-2.0` dev-only), which `quality-gates.md:307` classes as always-flag-for-review.

D3's suggested remedy was an ADR extending the allow-list, and then switching the gate. **No such
ADR exists** - `docs/adr/` holds 0001-0014 and `grep -rn 'allow-only\|MIT-0\|Unlicense' docs/adr/`
finds nothing. So the plan describes a gate that was not built, and the open half is recorded only
in a comment on a CI step and a worklog.

*Suggested fix (mine, verify before adopting):* change `:254` to *"`pip-licenses` deny-list on the
standard's flag-list, with the allow-list conversion owed to an ADR (U0-REPORT D3)"*, and file
**ADR-0015** as Proposed - *"extend the licence allow-list with MIT-0, Unlicense, PSF-2.0 and
MPL-2.0"* - alongside 0012-0014. The gate as built is green and demonstrably fires
(`U0-REPORT.md` §2.7 runs the negative arm), so this is a record-keeping gap rather than a hole in
CI; but an unfiled ADR named only inside a YAML comment is how a deviation becomes a convention.

## M5 - U5 reads `services/jobvite_client.py` while U6 rewrites it, and no rule covers read-of-a-file-under-write

`:1033` starts U6 at U4-completion. U5 also starts at U4-completion and its end-to-end test drives
U4's *"one request entry point"* (`:659-663`) inside the file U6 is at that moment restructuring for
paging. `§4`'s rules are stated as **write** ownership only, and the closing rule (`:1112-1116`)
addresses two agents *writing* a file: *"separate worktrees pinned to a SHA, not turns in one
checkout."*

Pinning U5 to U4's SHA makes U5 green against a client that no longer exists by the time U6 merges,
which is a worse failure than a conflict because nothing reports it. The plan makes exactly this
argument against scheduling U12 early (`:1099-1104`); the U5/U6 pair is the same relationship with
the roles of reader and writer swapped, and it is scheduled concurrent on purpose.

I do **not** think this should re-sequence U5 and U6 - the parallelism is real and U5 needs only the
one-call path, which exists at U4-completion.

*Suggested fix (mine, verify before adopting):* add one sentence to `§4` - *"U6 may extend
`services/jobvite_client.py` but may not change the signature or the error behaviour of U4's single
request entry point while U5 is open; a change there is a message to U5's owner, not a merge."*
That converts an invisible drift into a stated interface, at no scheduling cost.

---

## L1 - U0's section is now stale against the build in four small places

Per the plan's own precedence rule the build wins; these are the places U0's text no longer
describes what exists.

1. `:247-248` - *"coverage floors per ADR-0010 (80% overall, 85% tools, 90% client, 95% `utils/`,
   95 line / 90 branch on critical paths)"*. `pyproject.toml:95-96` records that **only the overall
   floor is expressible as a single `fail_under`**; the per-module floors are enforced by the units
   that create those modules, and the CI coverage step is off until U1.
2. The **`network` marker** does not appear in the plan at all. `pyproject.toml:78-84` declares two
   selection markers, not one, and `ci.yml:174-175` runs the network arm as its own step - because
   §8 #11's negative arm performs a real resolve and `DESIGN.md:1227` requires the default suite to
   run with no network. §1's *"Zero skips"* paragraph (`:212-218`) describes a single credentialed
   marker.
3. `[project.scripts]` and `readme` were deliberately omitted from the manifest and belong to U1 and
   U13 - see H2.
4. `:301` - the *"Seven of the fifteen variables carry a value"* correction is **right** in draft 5.
   U0-REPORT D4 was filed against draft 4 and is closed.

*Suggested fix (mine, verify before adopting):* rewrite `:247-248` in place to say the overall floor
lands in U0 and the per-module floors land with their modules; add the `network` marker to §1's Zero
skips paragraph with its one-sentence justification, because **every later unit adding an arm that
touches the network needs to know the marker exists** or it will put a live resolve in the default
offline suite. Rewrite, do not append - two contradictory statements about the marker set is worse
than one stale one.

## L2 - U2's repository-wide absence assertion is vacuous at the moment it is written

`:440-441` gives U2 *"a repository-wide assertion that no `success: true/false` envelope exists
anywhere (`DESIGN.md:497`)"*. At U2-completion the repository holds `errors.py`,
`utils/correlation.py` and U0's skeleton. The assertion passes over a corpus that contains almost no
code, and it will keep passing whether or not later units respect it - it is only meaningful once
the tools exist. U2's other arms are non-vacuous, so the unit is fine; the **assertion** is the
plan's own hunted shape.

*Suggested fix (mine, verify before adopting):* keep it in U2 (it is where the rule lives) and add
one line to U14 - *"re-assert U2's no-`success`-envelope sweep across the completed tool set"* -
since U14 is already the unit whose entire job is a completeness sweep after every tool has landed.

## L3 - "the first unit adding an arm" is not the name of a unit

`ci.yml:182-186` and `tests/credentialed/README.md` record that the credentialed-collect step
accepts exit 5 today, cannot tell *"the suite is empty"* from *"the suite is healthy"*, and that
**the first unit adding an arm must tighten it to require exit 0 and a non-zero count**. §5 point 5
of the plan (`:1265-1270`) says every tool unit adds its credentialed arm, so the first is U5 - but
nothing says so, and per H2 that tightening is another write to `ci.yml`.

*Suggested fix (mine, verify before adopting):* name U5 in U5's own verification list - *"U5 adds
the first credentialed arm and tightens CI's credentialed-collect step from `0 or 5` to `0 with a
non-zero count`"* - and add it to the `ci.yml` owner row from H2.

---

# The two judgements

## 1. If five agents took the parallel units tomorrow, what breaks first?

**Before Wave C is even reached: `.github/workflows/ci.yml`, between U1 and U11, in Wave A (H2).**
The table calls Wave A *"genuinely disjoint"*. It is not, and the reason is invisible from the plan
alone: U0 landed three commented CI steps addressed to U1 and U11 by name, so both agents' first or
last act is an edit to the same YAML file, on a day the plan tells them they share nothing. Round 3
answered `server.py` because it read the plan; the plan has no row for `ci.yml` at all, so this one
is only visible from the build.

**Then, at the four-lane widening: `models/`, between U8 and U12 (H1).** These two units are
deliberately started at the same instant, and `DESIGN.md:291` requires one output model per tool.
U8 is told it owns `models/` exclusively; U12 is told it owns half of a different file. The first
agent to need a job-feed model either blocks or writes into a directory the table says is not
theirs - which is exactly the position collision 5 was written to prevent, and it is now the only
place in Wave C where two *concurrent* units contend for one path.

Everything else I could construct - `utils/redaction.py`, `tools/candidates.py`, `server.py`,
`config.py`, `tools/jobs.py`, `services/jobvite_client.py` - is either named as a collision or is
separated by a real dependency edge. `models/` and `ci.yml` are the two that are not.

## 2. What did building U0 reveal that reading the plan would not?

Four things, all from `U0-REPORT.md` and the tree, none from theory.

**(a) The plan's ownership model is drawn on source modules, and every surface that actually
collided is one nobody thought of as code.** U0's four deferrals are *all* future writes back into
U0's own files - `ci.yml` three times, `pyproject.toml` twice - and the plan's table has no way even
to express "U11 will later edit a file U0 owns". `tests/conftest.py` is the same shape waiting to
happen: U0 created it as *"shared paths"*, every subsequent unit adds tests, and no table row
mentions `tests/` at all. **Reading the plan gives you the module layout; building gives you the
list of files two units must touch, and they are almost disjoint sets.** Both Highs above are
instances of this and I would not have found either by reading §4 more carefully.

**(b) Contact with a real toolchain falsified a Critical row in the frozen design and an
allow-list in the standards corpus, on day one, in the smallest unit.** D1 found `DESIGN.md:1808`
(C8-I1, Critical) asserting `.env.example` has *"empty values"* when seven of fifteen carry one -
which is now ADR-0014. D3 found `quality-gates.md`'s five-id allow-list unrunnable against a clean
tree. **Neither was findable by reading, and both needed an ADR rather than an edit.** U0 was the
unit with the *least* contact with the design's substance. The calibration for the remaining
fourteen units is: expect roughly one design-or-standards defect per unit that only building
surfaces, expect it to require a numbered ADR, and treat ADR-filing as routine throughput rather
than as an exception - the plan currently reads as though the freeze made ADRs rare.

**(c) The verification-shape question has a cheap experiment behind it, and the experiment finds
things review does not.** U0 ran two distinct harnesses: mutation (`11/11` controls, break one thing
and require the *named* test to go red) and **amputation** (four trees with the subject removed,
plus a fifth with `.env.example` present-and-zero-bytes). Only the amputation found the single
genuinely vacuous assertion - `test_no_value_in_env_example_looks_like_a_real_credential` passes
over `{}` - and U0 named it rather than counting it. **Reading a unit's "Verified by" list tells you
which arms exist; only the amputation tells you which are hollow.** The plan specifies positive
controls well - I checked all fifteen units and every one has an arm that fails if the unit builds
nothing, with U8's ordering fix and U9's middleware-presence control being the two that close the
worst cases - but *specifying* a control is not the same evidence as U0 produced. Every remaining
unit brief should carry U0's two harnesses as a requirement, not just the sentence "include a
positive control".

**(d) The plan's unit list is a dependency order, not a sizing, and the boundary leaks.** U0
declined a listed obligation on the judgement that it was a unit of its own - correctly, I think -
and asked for a ruling that has not been answered (H3). That happened on the *smallest* unit in the
plan. U1 (config, transport, TLS refusal, shutdown, `server.json`) and U8 (models, normalisation,
EEO exclusion, fencing, two tools) are visibly larger and the plan itself calls U8 the one it would
least want handed over in isolation. **How much can the remaining fourteen specs be trusted?
Their content held up well - U0's build contradicted the plan only in small, honest ways, and the
`72`-package resolve and the `fastmcp-slim` causal claim both reproduced exactly. Their
*boundaries* did not.** I would trust each unit's "Builds" and "Verified by" lists and re-derive the
ownership table from them before dispatching, rather than the other way round.

---

*Review by `plan-review-r4`, 2026-08-28. `docs/plans/IMPLEMENTATION-PLAN.md` and `docs/DESIGN.md`
were not edited. Nothing was committed.*
