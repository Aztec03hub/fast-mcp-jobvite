# CITATION-READ - reading the 158 `DESIGN.md` citations no checker can judge

Agent: `citation-read`. Brief: `docs/briefs/CITATION-READ.md`. Measured against `main` at
**`bb546ba`**, targets read from **`git show c15b138:docs/DESIGN.md`** (2045 lines), never from the
working tree. Worktree `/tmp/citation-read-work`, branch `review/citation-read`, removed on
completion. **Nothing under `src/`, `tests/` or `scripts/` was edited** - `u7-resilience`, `r2-fixes`
and `code-review-r5` were live in those trees. Every fix below is text.

**Line numbers in this report may have moved by the time anyone applies them. Anchor on the SUBJECT
column, not on the number** - every proposed target is quoted, and every quoted subject was checked
unique with `grep -n` over `c15b138:docs/DESIGN.md`.

## The population, enumerated rather than inherited

```
$ grep -rnoE 'DESIGN\.md:[0-9]+(-[0-9]+)?' tests/ | grep -v test_tools_jobs.py | wc -l
158
$ ... | awk -F'DESIGN.md:' '{print $2}' | sort -u | wc -l
115
```

**158 occurrences, 115 distinct ranges, across 23 files** including `tests/test_pagination.py`
(U6's) and `tests/credentialed/`. The brief said "roughly 160"; the count is 158 and it is the
number this report is about. **All 115 distinct ranges were read** - citing line plus surrounding
context to learn the claim, then the target text in full.

## Tally

| Verdict | Ranges | Sites in `tests/` |
|---|---|---|
| **CORRECT** | 105 | 145 |
| **WRONG** | **10** | **13** (+1 in `src/`) |
| UNSETTLEABLE | 0 | 0 |
| *of the CORRECT, carrying a boundary nit* | *10* | *11* |

**No range in this population was found to have the "right lines, wrong file" defect.** I checked
the ten WRONG targets against `c15b138:docs/plans/IMPLEMENTATION-PLAN.md` at the same numbers; none
of them reads plausibly there. That trap is real - `models/fencing.py:18` had it - but it is not in
this population, and saying so is part of the control.

## The ten WRONG ranges

Grouped by range. **Every site of a range moves in one pass or none do.**

### W-1. `1342-1344` -> `1037-1038` - the interpreter requirement is in §7.4, not §8

**2 sites**, and this is the largest miss in the set.

- `tests/test_shutdown.py:77` - `# DESIGN.md:1342-1344: resolve the INTERPRETER via /proc/<pid>/cmdline rather than trusting that the pid we hold is the process we signalled.`
- `tests/boot_process.py:177` - `DESIGN.md:1342-1344 requires the shutdown case to resolve the **interpreter** PID rather than a wrapper's.`

`1342-1344` is inside §8's *lifespan-teardown* bullet and is about asserting by side effect rather
than exit code, plus the gate's self-immunisation retraction. **It contains no mention of an
interpreter, a PID, `/proc`, or a wrapper.** `grep -n 'interpreter\|cmdline\|/proc/\|wrapper'` over
`c15b138:docs/DESIGN.md` returns exactly three lines: 982, 1037, 1038. The subject is **1037-1038**:

> that the process exited within the grace period, signalling the interpreter PID resolved
> **via `/proc/<pid>/cmdline` rather than a wrapper**.

**Fix:** both sites -> `DESIGN.md:1037-1038`. Anchor phrase: *"signalling the interpreter PID
resolved via `/proc/<pid>/cmdline` rather than a wrapper"* (unique, §7.4).

### W-2. `1345-1346` -> `1038-1040` - the same §7.4 sentence, cited from §8

**1 site.** `tests/test_shutdown.py:13`:

> **Both transports, because they fail differently** (DESIGN.md:1345-1346). The HTTP arm passes on
> teardown alone; **only the stdio arm exercises the `os._exit(0)` half** ...

That is a near-verbatim restatement of **1038-1040**:

> **The HTTP path passes on teardown alone; only stdio catches the exit failure**, which is precisely
> why a single-transport test would have shipped this bug.

`1345-1346` says something else entirely - *"of this document's stated verification gaps close only
on it (the upstream defect at `#4927` ...)"* - which **this same docstring already cites correctly
at `1340-1346` in its first paragraph**. The second citation is a copy of the first that was never
re-derived for the different claim it now supports.

**Fix:** `tests/test_shutdown.py:13` -> `DESIGN.md:1038-1040`. Anchor phrase: *"The HTTP path passes
on teardown alone"* (unique).

### W-3. `1323` -> `1297-1300` - §8 #10 is the off-loopback case; 1323 is §8 #15

**2 sites**, both in `tests/test_boot.py`, whose module docstring opens:

> `"""§8 #10: an off-loopback bind without TLS refuses to START.  DESIGN.md:1323.`

- `tests/test_boot.py:3` - the module docstring
- `tests/test_boot.py:64` - `"""Positive control for the REAL-PROCESS pair (DESIGN.md:1323)."""`

`1323` is the closing line of §8's **read-only-key** bullet (*"than as a control. A test asserting
anything stronger would misrepresent what the design achieves"*). Counting §8's required-case list
from `1265` as #1 - the base every other test in this repo uses, confirmed independently by
`test_markers.py`'s "#12", `test_manifest.py`'s "#11", `test_audit.py`'s "#17" and
`test_shutdown.py`'s "#18" all landing on the right bullets - **#10 is at 1297-1300**:

> - **an off-loopback bind without TLS refuses to start** - no certificates configured here and
>   `JOBVITE_TLS_TERMINATED_BY_PROXY` not declared, and the server exits naming the reason rather
>   than warning and continuing (§7.1). **Three High rows rest on this refusal and none of them
>   rested on a test before**;

The docstring's next sentence - *"Three High threat rows (C1-S1, C1-T1, C1-I1) rest on this refusal,
and none of them rested on a test before"* - is a paraphrase of **1299-1300**, inside the range it
should have cited. The citation is one bullet-cluster away from text the same docstring quotes.

**Fix:** both sites -> `DESIGN.md:1297-1300`. Anchor phrase: *"an off-loopback bind without TLS
refuses to start"* (occurs 4x: once as the §8 bullet at 1297, three times as the "verified by" cell
of threat rows C1-S1/C1-T1/C1-I1 at 1717/1719/1721 - **the §8 bullet is the one that begins a line
with `- **`**).

*Left as written:* `docs/reviews/REVIEW-R3.md:494` and `docs/reviews/b49b/short-summaries.json`
quote the old string as a dated record. Same call the repoint map made for the five `312-316` sites
under `docs/`.

### W-4. `1338-1343` -> `1335-1339` - §8 #17 starts three lines earlier

**2 sites in `tests/`, plus one in `src/` I could not touch and one in `docs/`.**

- `tests/test_audit.py:16` - `- **#17 needs both arms** (DESIGN.md:1338-1343): a field always absent ...`
- `tests/test_audit.py:307` - `# §8 #17 - trace context, BOTH arms (DESIGN.md:1338-1343).`
- **`src/fast_mcp_jobvite/audit.py:190`** - `single-arm test (DESIGN.md:1338-1343).` **- READ-ONLY
  to me; this site must move with the other two or the range is fixed at 2 of 3.**
- `docs/worklogs/U3-IMPL-REPORT.md:198` - dated record, leave as written.

The whole of §8 #17 is **1335-1339**. The cited range starts at 1338, which drops the two lines
carrying the claim these sites make - *"**Both arms are required**: a field that is always absent and
a field that is always synthesised each pass a single-arm test"* is at **1336-1337** - and then runs
past the bullet's end into `1340-1343`, the **lifespan-teardown** bullet, a different case entirely.

**Fix:** all three code sites -> `DESIGN.md:1335-1339`. Anchor phrase: *"trace context is recorded
when the caller supplies it and absent when it does not"* (unique).

### W-5. `1341-1343` -> `1337-1339` - "the failure that matters" is in the bullet above

**1 site.** `tests/test_audit.py:322` - `# failure DESIGN.md:1341-1343 says is the one that matters.`

*"and the second is the failure that matters"* is at **1338** (`grep -n` confirms one occurrence in
the file). `1341-1343` is the lifespan-teardown bullet. This is W-4's neighbour and the same
underlying slip; fix it in the same pass so a reader grepping either string gets one answer.

**Fix:** -> `DESIGN.md:1337-1339`. Anchor phrase: *"the second is the failure that matters, because a
minted id in a field named for the host's trace looks like a join and is not one"*.

### W-6. `986-1025` -> `1026-1034` - the range stops one line before its own subject

**1 site.** `tests/test_shutdown.py:144`:

> DESIGN.md:986-1025 **is explicit that the mitigation this replaced was also called verified and was
> not.**

That sentence is at **1026-1027**, one line past the end of the cited range:

> **Two limits on the word "verified" here, stated because the mitigation this replaced was also
> called verified and was not.** First, the two halves were executed separately ... Second, **PID 1
> was never simulated.**

`986-1025` is the code block and the exit-status paragraph. The claim the docstring makes is in the
paragraph that follows it. Recommend the whole paragraph, **1026-1034**, since the docstring's point
is that a test which reimplements the handler proves only that its author can write one.

**Fix:** -> `DESIGN.md:1026-1034`. Anchor phrase: *"the mitigation this replaced was also called
verified and was not"* (unique).

### W-7. `701-705` -> `723-727` - the retry harm is in §5.3's warning-shape paragraph

**1 site.** `tests/test_audit.py:475`, in `test_arm3_the_warning_tells_the_caller_not_to_retry`:

> The whole reason this branch exists. DESIGN.md:715-717 and DESIGN.md:701-705.
> **A retry emails a second live human**, so a warning that does not say so invites the exact harm
> the branch was written to prevent.

`715-717` is right and stays. `701-705` is the **stdio caller-attribution** paragraph plus the ADR
sentence - nothing about retry, warnings, or a second human. The second reference the sentence needs
is **723-727**:

> **Not a problem object.** ... the caller's reasonable response to that is to **retry, which emails a
> second live candidate. Preventing exactly that is why this branch exists**, so its result shape must
> not reintroduce it.

*"Preventing exactly that is why this branch exists"* is the design's own phrasing of *"the whole
reason this branch exists"*.

**Fix:** -> `DESIGN.md:715-717 and DESIGN.md:723-727`. Anchor phrase: *"retry, which emails a second
live candidate"* (unique).

*Left as written:* `docs/reviews/b49b/short-summaries.json:295` and
`docs/worklogs/B49B-SWEEP-REPORT.md:218` - dated records.

### W-8. `1432` -> `1437-1439` - the prerelease sentence is five lines down

**1 site.** `tests/test_manifest.py:103`, `test_prerelease_is_explicit`:

> `--prerelease=allow` is global in uv; `explicit` confines it.  DESIGN.md:1432.

`1432` is inside *"**The lockfile is the actual cure and it was missing**"*. The subject is
**1437-1439**, and it is nearly verbatim:

> **`--prerelease=allow` is global in uv** and pulls in a beta pydantic; **`explicit` alone fails to
> resolve** because `fastmcp-slim` arrives transitively. Naming it directly resolves pydantic to
> stable.

**Fix:** -> `DESIGN.md:1437-1439`. Anchor phrase: *"`--prerelease=allow` is global in uv"* (unique).

### W-9. `792-795` -> `795-798` - the range stops at the paragraph's first line

**1 site.** `tests/test_boot.py:180`:

> DESIGN.md:792-795 records that this section's variables were found missing **by someone trying to
> build against it and discovering the unit could not be started at all.**

That clause is at **796-798** (`grep -n 'Found the same way, by someone trying to'` -> 796):

> Found the same way, by someone trying to build against it and discovering the unit could not be
> started, let alone bound off-loopback to exercise the TLS refusal §8 tests.

`795` is only the paragraph's opening line (*"Both are named here because an earlier revision said
'unless told otherwise' and named nothing"*), so the range holds the variable declarations at
792-793 and a truncated sentence, but not the claim.

**Fix:** -> `DESIGN.md:795-798`. Anchor phrase: *"Found the same way, by someone trying to build
against it and discovering the unit could not be started"*.

### W-10. `938-939` -> `937-938` - a verbatim quote whose first clause is outside the range

**1 site.** `tests/test_config.py:123`:

> The NEGATIVE of the matrix, stated at DESIGN.md:938-939.
> "**a deployment using only** candidate search must not be forced to invent a `companyId` it has no
> use for"

The quote begins at **937** (*"...never the union - a deployment using only"*) and finishes at 938.
`939` is blank. The lowest-severity row here, and the only one a `+1`-style sweep would have caught -
which is why it is stated separately from the nine that no offset finds.

**Fix:** -> `DESIGN.md:937-938`. Anchor phrase: *"candidate search must not be forced to invent a
`companyId` it has no use for"* (unique). Note the *union* half of the claim lives at 937, so the
range must start there.

## Why no constant offset would have found these

| Range | Repoint | Delta |
|---|---|---|
| `1345-1346` | `1038-1040` | **-307** |
| `1342-1344` | `1037-1038` | **-305** |
| `1323` | `1297-1300` | -26 |
| `1341-1343` | `1337-1339` | -4 |
| `1338-1343` | `1335-1339` | -3 |
| `938-939` | `937-938` | -1 |
| `792-795` | `795-798` | **+3** |
| `1432` | `1437-1439` | +5 |
| `701-705` | `723-727` | **+22** |
| `986-1025` | `1026-1034` | **+40** |

Six negative, four positive, magnitudes from 1 to 307, and **two of them cross a section boundary**
(§8 -> §7.4). One is off by a single line. A `+1` sweep would have corrected exactly one of ten and
made two others worse while silencing nothing, because all ten already land on real prose and the
shape checker exits 0 over every one of them.

## Negative control

**105 of 115 ranges were read and judged CORRECT.** Naming them, because a sweep that finds
something wrong with everything it looks at proves nothing:

`178`, `303-304`, `308-340`, `312`, `312-313`, `312-318`, `315-318`, `332-333`, `335-337`,
`335-340`, `337-340`, `346`, `356-360`, `358`, `425-427`, `432-487`, `434`, `434-436`, `451`, `455`,
`460-462`, `463-464`, `465-466`, `465-468`, `469-473`, `469-477`, `473-477`, `474`, `474-476`,
`478-480`, `486`, `487`, `491-540`, `495-496`, `497`, `499-500`, `506-509`, `510-511`, `513-521`,
`532-533`, `532-534`, `534`, `536-540`, `601-612`, `604`, `605-606`, `608-612`, `698-703`,
`711-727`, `712-713`, `712-718`, `714-715`, `715-717`, `716-727`, `717-718`, `721-727`, `800-804`,
`828-831`, `828-834`, `832-834`, `911-957`, `913-917`, `919-936`, `921-923`, `925-929`, `927-928`,
`929`, `931-932`, `931-936`, `938-945`, `948-953`, `955-957`, `960-961`, `969-975`, `981-983`,
`996-1010`, `1015-1023`, `1021-1023`, `1229-1232`, `1237-1242`, `1244-1249`, `1251-1257`,
`1258-1260`, `1272`, `1276-1278`, `1278`, `1280-1282`, `1280-1283`, `1340-1346`, `1359-1360`,
`1370-1371`, `1370-1372`, `1404-1407`, `1418-1420`, `1505-1524`, `1513-1516`, `1523-1524`,
`1546-1552`, `1548-1552`, `1555-1560`, `1627-1637`, `1633-1634`, `1635-1637`, `1788`, `1797`.

Four of these deserve naming as *positive* evidence that the earlier repoint work landed correctly:
`315-318` (6 sites), `312-318` (3 sites) and `960-961` (3 sites) are exactly where
`CITATION-REPOINT-MAP.md` sent them, and `tests/test_error_contract.py:162` now cites `335-340` -
the map's own counter-example row, previously `345-347`. **Those repoints are verified landed by
reading, not by the checker's exit code.**

### Boundary nits inside the CORRECT set

Ten of the 105 contain their subject - a reader landing there gets the right claim, so they are not
WRONG - but a boundary line is off. Listed with a suggested tightening; **each is worth one edit and
none is worth an argument.**

| Range | Site(s) | Nit | Suggested |
|---|---|---|---|
| `921-923` | `test_config.py:169` | ends inside the *next* paragraph's topic sentence; "unset means" is at 920 | `920-921` |
| `1237-1242` | `test_markers.py:6` | the quoted "Without it, a typo in the" starts at 1236; "the configuration this strategy rests on" is at 1233 | `1233-1241` |
| `1523-1524` | `test_advisory_gate.py:279` | 1523 is the tail of policy item 3; item 4 finishes at 1525 | `1524-1525` |
| `1505-1524` | `test_advisory_gate.py:1` | clips the second half of policy item 4 | `1505-1525` |
| `1513-1516` | `test_advisory_gate.py:220` | starts one line into item 2 - the *same shape* as the map's `302-306` counter-example, one line LONG | `1514-1516` |
| `1546-1552` | `test_config.py:577` | opens on the previous bullet's tail; subject starts at 1548 | `1548-1552` |
| `1555-1560` | `test_repo_hygiene.py:32` | starts mid-word-wrap; the sentence opens at 1554 | `1554-1560` |
| `491-540` | `test_error_contract.py:1` | §5.1 runs to ~568; the range stops before "Three honest exceptions to uniformity" | `491-568` |
| `1015-1023` | `test_shutdown.py:221` | the topic sentence *"The status is the one the run earned, not a constant"* is at 1014 | `1014-1023` |
| `1021-1023` | `test_shutdown.py:234` | see "could not settle" below | - |

None of these was counted as a finding. They are listed so the negative control stays falsifiable:
I did not grade a range CORRECT without looking at both of its endpoints.

## What I could NOT settle

**One item, and it is an ambiguity in the citing prose rather than in the target.**

`tests/test_shutdown.py:234` reads: *"So this forces `mcp.run` to fail for a real reason - **a bound
port, the cheapest one, and the one DESIGN.md:1021-1023 names** - and reads the exit status."*
The referent of *"the one ... names"* is genuinely ambiguous:

- If it is **"a bound port"**, the citation is wrong: a bound port is named at **1016**
  (*"`os._exit(0)` would report a bound port, a misconfiguration or an escaping cancellation as a
  clean stop"*), not at 1021-1023.
- If it is **"forces `mcp.run` to fail for a real reason and reads the exit status"**, the citation
  is right: that is verbatim at 1022-1023.

I graded it CORRECT on the second reading, because the design requirement the test discharges is the
side-effect rule and not the choice of failure. **The unambiguous repair is to widen to `1016-1023`
and rewrite the parenthetical**, which covers both readings; I am not proposing it as a finding
because I cannot establish which the author meant, and a repoint made on a guess is the failure mode
this whole exercise exists to catch.

Nothing else in the 115 was left unresolved. Every other range was settled by reading both ends.

## What is NOT in scope here, stated so nobody reads a false absence

- **`tests/test_tools_jobs.py`** - excluded by the brief; `r4-fixes` read that population at
  `8bc5967`.
- **The 49 shape-detectable occurrences** swept at `cdcac62` - a different population, already fixed.
  I did not re-derive them, but W-3/W-4/W-5 confirm by reading that the shape checker's exit 0 says
  nothing about subject: all ten WRONG ranges pass it today.
- **`src/`, `scripts/`, and everything under `docs/`** were not swept for these ten strings beyond
  the `grep -rn` recorded above. **`src/fast_mcp_jobvite/audit.py:190` is the one live code site
  outside `tests/` that I found, and it belongs to W-4.** A full `src/` + `scripts/` read of the same
  kind has not been done by anyone and is the obvious next unit.
- `docs/worklogs/` and `docs/reviews/` hits are left as written, following
  `CITATION-REPOINT-MAP.md`'s call on the five `312-316` sites: repointing a dated record edits
  history to agree with the present.
