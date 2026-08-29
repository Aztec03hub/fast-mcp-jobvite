# R4-FIXES - eleven findings closed, one judged wrong in part, one left to CI ownership

**Agent:** `r4-fixes` **Branch:** `fix/r4-findings` **Base SHA:** `c5bdeb6`
**Frozen design:** `c15b138`, read only as `git show c15b138:docs/DESIGN.md`
**Worktree:** `/tmp/r4fix-work`. **Not yet removed** - see the last section.
**Task:** #36. R4-H2 was already fixed at `d08e5a6` and was not touched.

| Finding | State | Where |
|---|---|---|
| R4-H1 | FIXED | `c935bd1` |
| R4-H2 | already fixed at `d08e5a6` | not touched |
| R4-H3 | FIXED | `97eb93b` |
| R4-M1 | FIXED | `8597ba6` |
| R4-M2 | FIXED, and the population was **twice** what R4 sampled | `8bc5967` |
| R4-M3 | FIXED | `c935bd1` |
| R4-M4 | FIXED - half by me, half by `shell-hygiene` at `dcd8c5e` | `c935bd1`, `8597ba6` |
| R4-M5 | FIXED, and the gate is proved able to fire | `8597ba6` |
| R4-L1 | FIXED | `8597ba6` |
| R4-L2 | FIXED, **and its suggested fix does not type-check** | `8597ba6` |
| R4-L3 | FIXED | `8597ba6` |
| R4-N1 | FIXED, and the check is proved able to fire | `c935bd1`, `8597ba6` |

---

## Gates, each by exit code on its own line, at `8597ba6`

```
uv run --frozen pytest                        0    420 passed, 6 deselected, 0 skipped
uv run --frozen pytest --cov                  0    93.63%, floor 80
uv run --frozen ruff check .                  0
uv run --frozen ruff format --check .         0
uv run --frozen mypy                          0    44 source files
uv run --frozen pytest -m credentialed --collect-only  0   4/421 collected
python3 scripts/check-harness-anchors.py      0    161 anchors, all unique
python3 scripts/check-harness-anchors.py --self-check  0
python3 docs/reviews/check-obligations.py     0    31 mappings, 23 verified, 8 absent
python3 docs/reviews/check-design-citations.py 0   every citation resolves
bash scripts/check-u5-jobs-controls.sh        0    16/16 controls fired
bash scripts/check-u5-jobs-amputation.sh      0    ROWS 14, APPLIED 14, VACUOUS 0
bash docs/reviews/probe-r4-h3-live-arm-cannot-detect.py  0
bash docs/reviews/probe-r4-m5-n1-the-gates-can-fire.sh   0
```

The suite floor derived from `ci.yml` is `check-suite-floor.sh 398`; 420 >= 398.
Baseline at `c5bdeb6` was **413 passed, 5 deselected**, so this branch adds 7
offline cases and 1 credentialed one, and removes none.

---

## R4-H1 - nothing asserted the outbound request

**Before, `docs/reviews/probe-r4-unmutated-anchors.sh` at `c5bdeb6`** - reproduced
exactly, which is worth stating because R4 measured it at `555bad6` and the suite
has grown since:

```
########## BASELINE   413 passed, 5 deselected
R4-P1 the ids query parameter never reaches the wire   *** SURVIVED ***
R4-P2 the ids query key is misspelled                  *** SURVIVED ***
R4-P3 JOBS_PATH points at a route that does not exist  *** SURVIVED ***
R4-P4 JOBS_ENVELOPE_KEY ...                            KILLED
R4-P5 TOTAL_ENVELOPE_KEY ...                           KILLED
R4-P6 the read-only annotation is inverted             *** SURVIVED ***
########## ROWS: 6   SURVIVED: 4
```

**After, same probe at `8597ba6`:**

```
########## BASELINE   420 passed, 6 deselected
R4-P1   KILLED   1 failed, 419 passed
R4-P2   KILLED   1 failed, 419 passed
R4-P3   KILLED   2 failed, 418 passed
R4-P4   KILLED   4 failed, 416 passed
R4-P5   KILLED   1 failed, 419 passed
R4-P6   *** SURVIVED ***   420 passed
########## ROWS: 6   SURVIVED: 1
```

The one survivor is P6, `readOnlyHint`. R4 recorded it and explicitly did not
raise it, because `tools/jobs.py:262` states the annotation is advisory and never
counted as a control, and `DESIGN.md:270-274` agrees. **I agree and have not added
a row for it**: a mutation row asserting an advisory value would make it look like
a control, which is the opposite of what the design says.

**The fix**: two cases in `tests/test_tools_jobs.py`
(`test_the_ids_argument_reaches_the_wire_as_a_query_parameter` and
`test_omitting_ids_sends_no_ids_parameter`), plus four rows M12-M15 in
`check-u5-jobs-controls.sh` so a case cannot rot back into a name without a body.

**MEASURED, and this is the more useful half.** My first version asserted
`seen[0].url.path.endswith(JOBS_PATH)`, exactly as R4's suggested fix does. Row
M14 SURVIVED:

```
########## M14 JOBS_PATH points at a route that does not exist
  *** SURVIVED *** the named test passed against the mutation.
      ============================== 1 passed in 1.26s ===============================
```

The assertion moves with the constant it cites. **That is the M3 defect this
harness exists to catch, reappearing inside its own fix**, and R4's suggested code
carried it. The route is now pinned as the literal `"/job"` with
`JOBS_PATH == "/job"` asserted beside it, and M14 kills.

---

## R4-H3 - the credentialed arm could not detect what it existed to detect

The arm has never run - nobody holds a key - so neither the defect nor the fix can
be shown by running it. **`docs/reviews/probe-r4-h3-live-arm-cannot-detect.py`,
committed, exit 0**, substitutes a `MockTransport` serving 50 real jobs under
`jobs` with the count under `count`:

```
what the TOOL returned: 'showing 0 of 0'

the assertions the live arm carried BEFORE R4-H3
  passed   is_error is False
  passed   parsed.total >= 0
  passed   summary == showing N of total
  passed   showing <= 1 (the max_results=1 arm)

the assertions R4-H3 adds, on the RAW payload
  FAILED   'requisitions' in payload   -> the envelope key is not 'requisitions': ['count', 'jobs']
  FAILED   'total' in payload          -> the 'total' member is absent: ['count', 'jobs']
```

R4's diagnosis is confirmed in full. The fix has three parts, because the
assertion alone is not enough:

1. `test_the_live_envelope_uses_the_inferred_keys` asserts on the raw payload, one
   level below the tool, where the envelope still exists.
2. `total >= 0` becomes `total >= 1`, `showing <= 1` becomes `showing == 1`. Both
   old forms are satisfied by `showing 0 of 0` - **the assertion that existed to
   prove the cap held passed hardest in the case where the cap was never
   applied.**
3. `docs/CREDENTIAL-CHECKLIST.md` now states the precondition that makes those two
   non-vacuous: the tenant must hold at least one open requisition, and which
   tenant was used gets recorded when rows 1-4 are ticked.

The module docstring's claim about which case converts the fixture was REWRITTEN in
place, not appended to, because it was the false claim.

**ONE THING FOR THE TEAM LEAD.** `ci.yml`'s credentialed-collect floor is
`-ge 3`; this makes it 4. It still passes, but the floor should ratchet to 4 or
the half-empty case it exists to catch is one arm wider than it was. That is a
`ci.yml` edit and I did not make it - see the last section.

---

## R4-M2 - the citations, which is the one I was asked to be most careful about

**R4's ten are all real. It sampled 18 of the population and I read all of it, and
found ten more.** The base rate R4 warned about is not zero.

I fixed each **by subject**, reading `git show c15b138:docs/DESIGN.md` with
`grep -n`, via a keyed script that refuses if the citation text is not unique on
its line or is a prefix of a longer citation. **A constant offset would have been
wrong**, and the numbers say so without needing to be argued:

| Cited as | Repointed to | Delta | Sites | Subject |
|---|---|---|---|---|
| `186-190` | `192-195` | **+6** | 7 | a new Jobvite field is dropped until admitted |
| `216-220` | `227-229` | **+11** | 2 | the only unconditionally enforceable gate |
| `181-183` | `178-179` | **-3** | 2 | tab/newline/CR; bidi beside the control characters |
| `156` | `152-154` | **-4** | 2 | `max_length` on every string; regex on every identifier |
| `154` | `152-153` | **-2** | 1 | `extra="forbid"`, never a free-form dict |
| `176-183` | `172-179` | **-4** | 1 | "`max_length` does not cover this" |
| `172-175` | `172-179` | widened | 1 | the character rule, enumerated at 178-179 |
| `296` | `291` | **-5** | 1 | allow-listed OUTPUT models, one per tool |
| `294-296` | `289-290` | **-5** | 1 | tool bodies and their INPUT models |
| `302-306` | `300-301` | **-4** | 1 | every input model imports its constraints |
| `1219-1221` | `621-622` | **-598** | 1 | `request_id` on EVERY result |

The last row is the one that settles it. It is not off by a paragraph, it is in a
different **section**: `1219-1221` is *"Result size is bounded inside each tool"*;
the id-on-every-result requirement is §5.3 at 621. Any constant-offset repair would
have moved it somewhere equally wrong and left it resolving.

**A twelfth defect, of a different kind.** `models/fencing.py:18` cited
`DESIGN.md:828-833` for *"Job fields take an explicit not free text decision"*.
Those are the right LINES in the **wrong FILE**: `docs/plans/IMPLEMENTATION-PLAN.md`
at `c15b138` says exactly that at 831-832, and `DESIGN.md:828-833` is the
`JOBVITE_HTTP_TOKENS` paragraph. The parenthetical even said *"in the plan"*. The
plan is not frozen and those lines have **already moved by one** since `c15b138`,
so it is now cited by HEADING, not by number.

**Negative control, because a sweep that moves everything it looks at proves
nothing.** The ranges I did NOT touch were read the same way and are correct:
`202-205` (13 sites), `469-477`, `474-476`, `487-489`, `197-200`, `270-274`,
`162-164`, `137`, `133-139`, `917-934`, `1229-1232`, `1244-1249`, `1258-1260`,
`1280-1282`, `1325-1337`, `1332-1334`, `1359-1360`, `1370-1371`, `548-568`,
`536-540`, `502-509`, `532-534`, `632-638`, `639-650`, `646-650`, `738-744`,
`745-748`, `747-750`, `295-297`.

**SCOPE, and it is not the whole repo.** While resolving R4's own table I read
citations in `utils/redaction.py` and `utils/__init__.py` and found six more wrong
there - `DESIGN.md:311` (blank line), `313`, `314-315`, `317-319`, `289-291`, and
`312-316` stopping one sentence short of *"Enforced in one place"*. **Those are
U2/U4 and task #37 explicitly assigns them elsewhere**, so I did not touch them;
they are listed here as evidence for #37 and #40. My repoints are the U5 population
plus the module-layout sites R4 named in its own table.

---

## R4-M3, M4, M5, N1 - the four "the harness cannot fail" shapes

**M3.** `mutate()` treated any non-zero pytest exit as a kill, and pytest exits 4
when a selector matches nothing - so a renamed test made its row report KILLED
forever. It now `--collect-only`s the selector first and returns without
incrementing `FIRED`, so `fired != total` and the run exits 1. All sixteen
selectors resolve today, so this was latent, and it is now impossible for it to
stop being latent quietly. *(The same guard belongs in
`check-u1-boot-controls.sh:73`, which is not my file - noted for a follow-up.)*

**M4.** `FIRED -ne TOTAL` and `APPLIED -ne ROWS` are both satisfied by `0 == 0`.
Both harnesses now carry a `ROW_FLOOR` (16 and 14). The **generic** form of this
hole, in `scripts/ci-harness-gate.sh`'s `--anchors-applied` branch, was closed by
`shell-hygiene` at `dcd8c5e` while I was working; `--controls-fired` had already
been closed at `b0d7729`. So M4 is fully covered and I did not need the `ci.yml`
`--min-rows` edit I asked about.

**M5.** The amputation harness's header claimed *"no row survived, which is the
vacuous shape"* and gated on `APPLIED == ROWS` instead. It now tracks `VACUOUS`
and exits 1 on any. The verdict is the run's **exit code**, not
`grep -cE '^FAILED '`, because that grep misses ERROR entirely.

**N1.** `cp b f; cmp f b` is equal by construction: it could detect a failed `cp`
and nothing else, while its message claimed to detect *"the tree still carries this
row's mutation"*. Both harnesses now compare against a pristine copy taken before
row 1.

**Both new gates are proved able to fire**, because a fix for "the harness cannot
fail" that is not itself proved able to fail is the same defect one layer up.
`docs/reviews/probe-r4-m5-n1-the-gates-can-fire.sh`, committed, exit 0:

```
ARM 1 - the R4-M5 vacuous-row gate
Renaming test_to_job_sets_every_field_the_model_declares, the only test row A14 kills.
    *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red.
  ::error::1 VACUOUS ROW(S)
  harness exit: 1
  ARM 1 PASSED - the gate fired and the harness went red.

ARM 2 - the R4-N1 restore check, against the instrument
  OLD CHECK (cmp file backup):   passed - and the tree is MUTATED.
  NEW CHECK (cmp file pristine): FAILED - RESTORE FAILED would fire.
  ARM 2 PASSED

TREE RESTORED - tests/test_tools_jobs.py matches the copy taken before arm 1.
```

Arm 2 runs against the **instrument**, not the harness, because the claim is about
the instrument. Arm 1 runs the real harness against a real vacuous row.

---

## R4-M1 - the registry was rooted at a hand-named model

Confirmed as measured. `JobSearchResult` - the model actually serialised to the
caller - carried no decisions, and `fencing_paths` walked `model_fields` only, so
`summary`, a caller-facing string built from data, could never carry one at all.

The fix follows R4's suggestion and enumerates the **container**:
`test_every_output_model_in_the_package_has_a_registry` walks
`fast_mcp_jobvite.models.*` with `pkgutil`, discovers every `BaseModel` defined
there, and requires each to generate. `_decision_of` was split into
`_decision_of` / `_computed_decision_of` over a shared `_single`, and the decision
for a computed field lives in its RETURN annotation because a computed field has no
`FieldInfo.metadata`. Measured: that extra metadata does **not** reach
`model_json_schema(mode="serialization")`, so the advertised schema is unchanged.

**Amputations proving it**: A12 deletes the computed-field walk (kills 2), A13
removes `JobSearchResult.total`'s decision (kills 2). Before the fix, both of those
would have killed nothing, because nothing looked.

---

## R4-L1, L2, L3

**L1** - `_to_job` is a hand-kept list beside `Job`. The new case builds its raw
object FROM the model's own `Fenced.jobvite_key` annotations - never a second
literal list - and asserts no admitted field came back unset. A14 amputates one
mapping and kills it.

**L2 - the finding is right and its suggested fix does not compile.** R4 says the
`None` default "guards against nothing that is currently true". It guards against
one thing that is: fastmcp declares `request_context` as
`FastMCPRequestContext | None`, so `meta = ctx.request_context.meta` fails the type
gate:

```
src/fast_mcp_jobvite/tools/jobs.py:294: error: Item "None" of "FastMCPRequestContext | None" has no attribute "meta"  [union-attr]
Found 1 error in 1 file (checked 44 source files)
```

The finding's *diagnosis* stands - `getattr(..., "meta", None)` turns a library
rename into silent trace loss, which is amputation row A11 arriving by accident. So
the two cases are now written out separately: `.meta` is read **by name**, so a
rename is an `AttributeError`, and the declared-optional branch is explicit beside
it. A context we were never given is not a renamed attribute, and the code now says
which is which.

**L3** - confirmed. The `\A`/`\z` comment claimed the anchors stop a trailing
newline reaching a log line; newline is in the permitted set, so they do not. The
comment was REWRITTEN in place, and `test_safetext_admits_a_trailing_newline_and_the_identifier_does_not`
asserts what is true: `SafeText` admits `"ab\n"`, `JobviteIdentifier` refuses
`"TESTJOB1\n"`. Writing the assertion matters more than the prose - a comment
nothing checks is how the wrong claim survived.

While there I also corrected a second stale sentence in the same block: it still
described `_NO_FORBIDDEN` as "used as a negative lookahead below", which `d08e5a6`
had already stopped being true.

---

## Two things I got wrong, recorded because the next reader needs them

**1. I stashed a live worktree and nearly lost an hour of uncommitted work.** In a
command whose purpose was to read the anchor count at the base SHA, I chained
`git stash -q -u` and `git checkout -q c5bdeb6 -- .`. That staged the base
revision over three committed files and moved everything uncommitted into
`stash@{0}`. Recovered in full with `git restore --source=HEAD --staged --worktree .`
followed by `git stash pop`, and verified afterwards by grepping for four specific
changes and re-running the suite. Nothing was lost, and only because the stash
existed. The rule in this project's own memory is "never stash while editing"; I
broke it inside a command I had not thought of as a write.

**2. `ruff format` moved an anchor and only the STATIC checker saw it.** After
reformatting, `check-u5-jobs-amputation.sh`'s A10 anchor
(`def summary(self) -> Annotated[`) no longer matched, because the signature had
been re-wrapped. The harness itself had already run green against the pre-format
tree. `scripts/check-harness-anchors.py` caught it in milliseconds:
`FAIL: 1 of 161 anchors do not resolve uniquely`. That is exactly the case that
checker exists for, and it is the second time on this branch that a run-based gate
and a static one disagreed in the static one's favour.

---

## What I did NOT verify

These are things I could not settle, not things I did not try.

- **`ci.yml` is untouched.** I asked the team lead before editing it and no reply
  had arrived by the time the work was done, so I closed M4 inside my own two
  harnesses instead - which turned out to be the right split anyway, since
  `dcd8c5e` closed the generic hole. **Two `ci.yml` edits are still outstanding and
  are the team lead's:** (a) the credentialed-collect floor should ratchet from 3
  to 4, and (b) `--floor 154` at `ci.yml:419` is now 7 below the real anchor count
  of 161 on this branch, and `shell-hygiene` moved it to 164 on theirs, so the
  merged value has to be re-derived rather than taken from either branch.
- **The rest of the citation population.** `check-design-citation-shape.py` at
  `4f4ae1d` reports 36 machine-decidable failures, exactly ONE of which is in a U5
  file (`constraints.py:4`, fixed here). The other 35 are U1/U3/U4 and belong to
  #37. Separately, I read the U5 population by hand and cannot claim the same for
  `tests/` outside `test_tools_jobs.py` - roughly 160 citation sites in seven other
  test modules that neither the checker's shapes nor my reading has covered.
- **The `readOnlyHint` survivor (P6).** Left deliberately, argued above. I did not
  verify whether any host in use actually prompts on it.
- **The credentialed arm still cannot be run.** The probe reproduces the failure
  offline against a `MockTransport`; it does not prove Jobvite's real envelope key
  is `requisitions`. Nothing in this repository can, which is the whole point of
  checklist rows 1-4.
- **`check-u1-boot-controls.sh:73`** has the same named-selector defect M3 fixed
  here. I did not touch it - not my file - and did not measure whether its
  selectors currently resolve.
- **Coverage of `models/fencing.py` is 96%**, with lines 201-202 (`_nested_model`'s
  `Union` branch) uncovered. That is pre-existing and I did not add a case for it.

## Worktree

`/tmp/r4fix-work` is **still present**, deliberately: everything is committed on
`fix/r4-findings`, but the two committed probes are worth re-running from a live
tree if any of this is questioned before the merge. It is a detached worktree of
the shared checkout and `git worktree remove /tmp/r4fix-work` retires it.
