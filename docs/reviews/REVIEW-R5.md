# REVIEW-R5 - U6 paging, reviewed at the merged SHA

**Agent:** `code-review-r5`. **Branch:** `review/r5`, cut from `d0abd10`.

**EVERY FINDING BELOW IS AGAINST `8d7af64`**, the merge commit, read as
`git show 8d7af64:<path>` and measured in a pinned worktree at `/tmp/code-review-r5-work`
(`git worktree add /tmp/code-review-r5-work 8d7af64`). **Nothing was read from the shared
checkout**, because `u7-resilience` is live in `services/jobvite_client.py` and `r2-fixes` is live
elsewhere in `src/` and `tests/`. `docs/DESIGN.md` was read as `git show c15b138:docs/DESIGN.md`;
it is byte-identical at `d0abd10` (`git rev-parse` on both blobs matched), so the design citations
below resolve on either tree.

**No edit was made to `src/`, `tests/` or `scripts/` on any branch.** Three amputations and two
mutations were applied to the pinned worktree's copy of the client, each proved to have LANDED with
`cmp` against a backup taken first, each RESTORED with `cmp` afterwards, all under
`PYTHONDONTWRITEBYTECODE=1`. The worktree removal is recorded in §5.

**Baseline in the pinned worktree, read from the terminal:**

```
uv run --frozen pytest -q -p no:cacheprovider tests/     447 passed, 6 deselected   exit 0
bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh   --controls-fired      exit 0
        ########## 16/16 controls fired.
bash scripts/ci-harness-gate.sh check-u6-paging-amputation.sh --anchors-applied     exit 0
        ########## ROWS: 10   ANCHORS APPLIED: 10
        ########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: 205
```

**Both harnesses are wired and both fire.** Verified by running them, not by reading `ci.yml`:
`ci.yml:546` and `ci.yml:549` at `8d7af64`. Zero skips.

**Where the unit stands relative to production.** `grep -rn "\.scan(" src/` at `8d7af64` returns
**nothing**: `scan()`, `ScanResult` and `start_base_overrides` have no caller anywhere in `src/`.
That is what `IMPLEMENTATION-PLAN.md:887-889` schedules (U8 and U12 key off U6), so it is not a
finding - but it is the reason every behavioural finding below is **latent**: the two harnesses and
`tests/test_pagination.py` are currently the only thing standing between these defects and the
first tool that calls `scan()`.

---

## The three claims the brief asked me to attack

**Claim 2 - "termination is on a SHORT page and never on `total`" - HOLDS.** I looked for the path
where a lying `total` shortens or extends the loop and did not find one: `total` is written at
`jobvite_client.py:953-955` and read only at `:1006`, inside `_check_completeness`, which runs after
the loop and returns a flag. There is no arithmetic on it and no branch on it inside `while True`.
**But the claim is narrower than it sounds and H2 below is its shadow**: the design removed `total`
as a bound and put nothing in its place, so the loop has no bound at all.

**Claim 3 - "the completeness check is armed ONLY by an exhaustive scan" - HOLDS, and the M9 shape
does not recur in the guard.** I amputated the `not exhaustive` half of both remaining `not
exhaustive and ...` conditions in my head and then in the tree: deleting it from `:991` truncates
every exhaustive scan to one page and `test_the_scan_terminates_on_a_short_page` kills it; deleting
it from `:997` truncates every exhaustive scan to `cap` and the same test kills it. **The same shape
does recur one level out, in the harness rather than the code** - see M3 and M4.

**Claim 1 - "de-duplication defends against OVER-reading only" - the test proves the limitation, but
its docstring overstates by one word, and the finding is elsewhere.**
`tests/test_pagination.py:269-295` does more than show duplicates being dropped: `:292` asserts
`duplicates_dropped == 0`, which is the assertion that says the seen set *did not fire*, and that is
the limitation rather than the behaviour. `test_an_overlapping_page_drops_duplicates` (`:254`) is
the separate behaviour case, and M4/M11 kill them separately. The claim is carried.

One word is wrong. `:280` says a later author who moved the start to 1 would get this "silently",
and `:295` then asserts `result.incomplete is True` - the scan is **not** silent, the completeness
check catches exactly this. The docstring's own body contradicts it. **Suggested fix:** change
"silently" to "on every scan, reported only as a count mismatch a caller has to look for" at
`tests/test_pagination.py:280`. Nit, filed as N4.

---

## Findings, ranked

### H1 (High) - the caller's `limit` is enforced by a block that no test in the repository reaches, and deleting it lets a `limit=4` call return six records

`src/fast_mcp_jobvite/services/jobvite_client.py:997-999` (`8d7af64`):

```python
        if not exhaustive and len(items) > effective_limit:
            capped = True
            items = items[:effective_limit]
```

**MEASURED. I deleted all three lines and the entire suite stayed green:**

```
LANDED: YES   (cmp against a backup taken first)
uv run --frozen pytest -q -p no:cacheprovider tests/
====================== 447 passed, 6 deselected in 41.72s ======================
RESTORED OK   (cmp against the backup)
```

**A surviving amputation with a demonstrated consequence.** No case in `tests/test_pagination.py`
ever arrives at the truncation with `len(items) > effective_limit`, because both capped cases
(`:550` and `:570`) accumulate their limit exactly on page one. Reaching it needs a page that is
full on the wire but yields fewer than `effective_limit` new records, so the next page overshoots -
which is the ordinary clamping-hypothesis shape the whole unit is built for. With a probe:

```
A) limit=4, records [A,A,A,B,C,D,E,F]:
   intact:    items=4  capped=True  pages=2  asks=[(0,4),(4,4)]
   amputated: items=6  capped=True  pages=2  asks=[(0,4),(4,4)]
```

**The client hands a caller who asked for 4 records 6 of them, and `capped` is `True` either way,
so the result object cannot be used to tell the two apart.** Downstream that is `showing 50 of
1,240` printed over 62 records.

**Suggested fix:** add the case, do not touch the code. In `tests/test_pagination.py`, a case whose
server holds `[A,A,A,B]` followed by four fresh records, scanned with `limit=4` and
`max_results=4`, asserting `len(result.items) == 4` **and** `result.pages == 2` (the second
assertion is what stops the case being satisfiable by a one-page implementation). Then extend the
amputation harness's A7 so it deletes both halves - see M3, which is the same defect from the
harness's side.

### H2 (High) - `scan()` has no bound of any kind, and a server that ignores `start` pages forever

`src/fast_mcp_jobvite/services/jobvite_client.py:945-995`. The only exits from `while True:` are a
short page (`:987`) and the caller's cap (`:991`). There is no page ceiling, no request ceiling, no
zero-progress detector, and no elapsed bound.

**MEASURED.** Against a fake that ignores `start` and answers a full page every time, with an
exhaustive scan:

```
C) starting unbounded-loop probe against a server that ignores `start` ...
PROBE ABORT: 200 requests, loop is unbounded
```

The abort is mine, at 200 requests; the client's own answer is "keep going". `DESIGN.md:486-487`
removed `total` as a loop condition and supplied no replacement bound, and U6 implemented that
faithfully - **this is a defect in the design as much as in the code**, which is why it is a
Proposed ADR below and not just a patch.

The unit knew the shape and wrote it down twice without treating it as a production risk.
`tests/test_pagination.py:346-348` says *"A loop that paged until it had `total` records would
request forever against a server that keeps answering"* - and the shipped loop does exactly that by
a different route. `scripts/check-u6-paging-amputation.sh`'s header declines to amputate the advance
and the short-page break for the same reason.

Note the interaction with task #43/#49: `DESIGN.md:373-375`'s **total outbound budget** would bound
this in wall-clock and turn it into a typed 503. That is a mitigation, not a fix - it bounds a
symptom by time, is not implemented at `8d7af64`, and against the 6/min self-throttle of
`DESIGN.md:425-427` the budget would be consumed by a scan that is making no progress. **U7 should
be told this specifically**, because a budget written without knowing about it will be sized for a
slow Jobvite rather than for a non-terminating one.

**Suggested fix**, cheapest first, and I would take both:

1. **Zero-progress break.** Track new records per page; if a full page adds nothing to `seen` and
   nothing to `unidentified`, break and set `incomplete = True`. Cannot fire on healthy paging - a
   full page that adds no records means the server is not advancing.
2. **A page ceiling that is not derived from `total`.** `MAX_PAGES: Final = 10_000` beside
   `SCAN_START`, with the same "named rather than inlined" comment, and hitting it sets
   `incomplete` and logs. Not a termination *on* `total`, so `DESIGN.md:486-487` is intact.

**Proposed ADR-0024:** *`DESIGN.md:486-487` bounds paging by the server's honesty and by nothing
else.* Terminating only on a short page is correct about `total` and silent about non-advancement;
the section should name a bound that does not read `total`. **Proposed only - I made no edit to
`docs/DESIGN.md`.**

### H3 (High) - a wrong `id_key` returns duplicate records to the caller, the seen set is silently inert, and the anomaly is logged as the opposite of what it is

The brief named the exposure; this is what the path actually does. `DEFAULT_ID_KEY` is `eId`
(`jobvite_client.py:475`) and the only recorded success body is the candidate one. When the key is
wrong for a resource, `:965` sends every record down the `unidentified` branch at `:972-973`: kept,
appended, **never de-duplicated**.

**MEASURED**, exhaustive scan of a 9-record resource, clamping server, `id_key="id"` where the
records carry `eId`:

```
B) wrong id_key -> items=10 unique=9 dups_dropped=0 unidentified=10 incomplete=True total=9
   items returned to caller:
   ['E0','E1','E2','E3','E3','E4','E5','E6','E7','E8']
```

Three separate failures in one path:

1. **`E3` is returned twice.** The de-duplication the design requires (`DESIGN.md:465-466`) is
   inert, and a model consuming this sees a duplicate job.
2. **`unique` is inflated, not deflated.** `:1005` computes `unique=len(seen) + unidentified`, and
   `unidentified` counts every copy. So `unique=10 > total=9`.
3. **The anomaly is mislabelled.** `:1058` fires on `unique != total`, so an OVER-read is logged as
   `"jobvite scan incomplete"` (`:1060-1065`) - see M2.

**Nothing anywhere says the id key is wrong.** `ScanResult.unidentified` carries the number, no
caller exists to read it, and no log line mentions it. `unidentified == len(items)` on a non-empty
scan has exactly one cause and the client stays quiet about it.

**Suggested fix**, at `_check_completeness` or just before it, and it needs no new configuration:

```python
if unidentified and unidentified == len(items):
    logger.warning(
        "jobvite scan: no record carried the id key; de-duplication is inert",
        route=redact_url(f"{V2_BASE_URL}{path}"),
        id_key=id_key,
        records=len(items),
    )
```

With a test asserting the line fires when every record lacks the key and is **silent** when one
record carries it (the positive control - without it the case passes against a check that always
fires). This is also the mechanism that would let U8/U12 discover the right key from a live payload
instead of inferring it from a green scan, which answers the last item in U6's §7.

### M1 (Medium) - `JOBVITE_PAGINATION_START_BASE` reaches nothing, and it is F1's sibling at the very construction site F1 was fixed at

`git show 8d7af64:src/fast_mcp_jobvite/tools/jobs.py`, lines 264-269:

```python
        return JobviteClient(
            api_key=api_key,
            api_secret=api_secret,
            company_id=settings.company_id,
            max_results=settings.max_results,
        )
```

`start_base_overrides` is not passed. `grep -rn "pagination_start_base" src/` at `8d7af64` returns
**one line**, its own definition at `config.py:207`; there is no reader. So the knob
`.env.example:104` ships, documented at `.env.example:101-103` as *"Pagination base, per
resource... Override only if you have established the truth against a live tenant"*, does nothing
at all - and `IMPLEMENTATION-PLAN.md:883-885` lists it as something U6 **builds**.

This is precisely the shape F1 was: a configured half that never reaches the transport half. F1 was
fixed by adding two arguments to this call and the third was not added. **Fix one instance, check
its siblings** - and the sibling was in the same argument list.

It is also why I rank this above U6's own F2. F2 asks whether the variable should be a scalar or a
mapping; **whichever it is, today it is read by nobody**, so F2 is a decision about the shape of
something inoperative.

**Suggested fix**, in the order it has to happen:

1. Settle F2 (below). If (b), the scalar-is-global reading, then here:
   `start_base_overrides={path: settings.pagination_start_base for path in ROUTES}` guarded on
   `is not None`.
2. Add the case that proves it, and give it the shape the F1 fix used, because that is the shape no
   other case in `test_tools_jobs.py` reaches: `client_factory=None`, settings carrying a start
   base, asserting the constructed client's `scan_start()` returns it. Prove it able to fail by
   amputating the new argument.
3. Until 1 and 2 land, `.env.example:101-104` should say the variable is **not yet read**. A
   template that documents an operator override which silently does nothing is worse than one that
   omits it.

### M2 (Medium) - the completeness check fires in both directions while its own docstring says one, so an over-read is reported as "incomplete"

`jobvite_client.py:1058` is `if unique == total: return False`, so the warning at `:1060` fires
whenever `unique != total`. The docstring three lines up, `:1034-1035`, says the check fires when a
scan *"terminated on a short page and returned **fewer** unique records than `total`"*. **The code
says "different" and the comment says "fewer".** `DESIGN.md:469-477` is about a gap throughout - it
never contemplates an over-count.

The over-count branch is reachable and I reached it: H3's probe produced `unique=10, total=9,
incomplete=True`, logged as `"jobvite scan incomplete"`. `DESIGN.md:474` is explicit that a check
which cries wolf on the ordinary path *"would fire the alarm on the default path and train everyone
to ignore it"*, and an over-read logged as an under-read is the same wolf with a wrong name on it.

**Suggested fix:** split the two directions, keeping the design's word for the design's case.

```python
        if unique == total:
            return False
        if unique > total:
            logger.warning(
                "jobvite scan over-read", route=..., unique=unique, reported_total=total
            )
            return False        # or a new `over_read` field on ScanResult
        logger.warning("jobvite scan incomplete", ...)
        return True
```

with a case per direction. If the team prefers one flag, then at minimum `:1034-1035` must be
rewritten to say "a count that disagrees with `total` in either direction", so the comment stops
being a claim the code does not honour.

### M3 (Medium) - amputation row A7's comment claims to delete two things and deletes one, which is why H1 was never found

`scripts/check-u6-paging-amputation.sh:228-239` at `8d7af64`. The comment reads:

```
# A7 - THE CALLER'S LIMIT IS NEVER ENFORCED. Both the loop break and the
# final truncation go, so a `limit=50` call returns everything Jobvite
# holds - and reports it as an ordinary result.
```

The row's anchor is only the loop break at `jobvite_client.py:991-993`. The final truncation at
`:997-999` is untouched. **The row's own comment is the claim; the anchor is what it does; they
disagree, and the half the comment claims is the half H1 proves is untested.**

This is worth more than its severity, because A7 is *the* row U6 records as having been vacuous
first and then fixed (report §5, `test_a_capped_call_stops_asking_once_it_is_full`). The fix was
real. The comment describing the fixed row was written for an amputation that was never applied,
and it then read as coverage.

**Suggested fix:** split into two rows so each anchor is separately measurable and the row floor
goes 10 -> 11.

```bash
amputate "A7a a caller's limit does not stop the loop" \
  "$CLIENT" \
  '            if not exhaustive and len(items) >= effective_limit:
                capped = True
                break' \
  '            if False:
                capped = True
                break'

amputate "A7b the caller's limit does not truncate the result" \
  "$CLIENT" \
  '        if not exhaustive and len(items) > effective_limit:
            capped = True
            items = items[:effective_limit]' \
  '        pass'
```

A7b will report **VACUOUS** until H1's case is added, which is the harness working: raise the floor
and add the case in the same change.

### M4 (Medium) - mutation row M11's title describes a mutation that is a provable no-op, and its body is a second copy of M10

`scripts/check-u6-paging-controls.sh:262-266`:

```bash
mutate "M11 completeness counts every record returned, not unique ones" \
  ... '            unique=len(seen) + unidentified,' \
      '            unique=total if isinstance(total, int) else len(seen),'
```

Two problems.

**The title's mutation cannot be detected, by construction.** `scan()` appends to `items` exactly
once per new id and once per unidentified record (`:973`, `:979`), so on the path where completeness
runs, `len(items) == len(seen) + unidentified` **identically**. MEASURED: I replaced `:1005` with
`unique=len(items)` and the suite was `447 passed, 6 deselected` - restored with `cmp`. That is a
survivor that is not a defect; it is a row whose stated subject is not a behaviour this code has.

**The body is M10 wearing arm one's clothes.** Forcing `unique = total` makes `:1058` always return
`False` - the completeness check never fires, which is exactly what M10 (`:250-254`) does. So 16
rows contain 15 distinct behaviours, and the "16/16 controls fired" line overstates its own breadth.

**Suggested fix:** repoint M11 at the mutation its title is reaching for - one that *is* distinct
and *is* killed. MEASURED with `unique=len(seen) + unidentified + duplicates`:
`1 failed, 446 passed`.

```bash
mutate "M11 the completeness count includes duplicates the seen set dropped" \
  "$CLIENT" "$SUITE::test_a_full_page_of_duplicates_is_not_a_short_page" \
  '            unique=len(seen) + unidentified,' \
  '            unique=len(seen) + unidentified + duplicates,'
```

(Confirm the named test from the run before committing the row - I measured the count, not which
one.) This also makes M11 the row that would have caught H3's inflation, which the current M11
cannot see.

### L1 (Low) - U6's F2 re-confirmed open at `8d7af64`, and it is a decision, not a patch

`config.py:207` is `pagination_start_base: int | None = None`; `.env.example:101` calls it
"Pagination base, per resource" while offering one value; `DESIGN.md:478-480` says *"The base is
per-resource, not global... They are configured separately."* Nothing changed at the merge. I add
only that M1 makes the choice cheaper than it looks: since no reader exists, either option is a
green-field change rather than a contract break, and **(b) - keep the scalar, expand it to every
route at the call site, and say "global" in `.env.example`** - is the one I would take. It is
smaller, and it cannot express the thing the design warns against (a per-route 1 written down as
the vendor's claim) any more dangerously than the mapping can.

### L2 (Low) - U6's F3 re-confirmed open, and I re-measured both ranges rather than copying them

`config.py:197` cites `DESIGN.md:1569-1573`; `config.py:200` cites `DESIGN.md:1574-1580`. Resolved
against `git show c15b138:docs/DESIGN.md`:

| Line | subject bullet actually begins/ends |
|---|---|
| `1569-1571` | tail of the *previous* bullet, about a hand-kept list going stale |
| `1572-1575` | `- **JOBVITE_MAX_RESULTS**, default **50**` |
| `1576-1581` | `- **JOBVITE_OUTBOUND_RATE_LIMIT**, requests per minute, default **6**` |

Both cited ranges resolve, overlap their subject, and are wrong at both ends - the decay shape
`check-design-citation-shape.py` cannot see. **Suggested fix:** `config.py:197` -> `1572-1575`;
`config.py:200` -> `1576-1581`. Every design citation inside the U6 paging block itself
(`:425-427`, `:434`, `:434-436`, `:451`, `:455-464`, `:460-462`, `:463-464`, `:465-468`,
`:469-472`, `:469-477`, `:473-477`, `:474`, `:478-480`, `:486-487`, `:1572-1575`) I resolved one by
one and **all fifteen are correct** - the decay is in `config.py`, which U6 did not own.

### L3 (Low) - `limit=0` issues a real request to return nothing, and a negative `limit` reaches a negative slice

`jobvite_client.py:931-932`:

```python
        effective_limit = cap if exhaustive else min(limit or 0, cap)
        count = cap if exhaustive else max(effective_limit, 1)
```

MEASURED:

```
D) limit=0  -> requests=1 asks=[(0, 1)] items=0 capped=True
D) limit=-5 -> requests=1 asks=[(0, 1)] items=0 capped=True
```

Both spend one of six requests per minute to return an empty list. The negative case also reaches
`items[:effective_limit]` at `:999` with a negative index, where `items[:-5]` means "all but the
last five" and happens to be empty here only because the list is short. `limit or 0` is there to
satisfy mypy (which cannot narrow `limit` through the `exhaustive` bool), and it silently converts
a caller's `0`.

**Suggested fix:** reject it at the door rather than defend it three lines later.

```python
        if limit is not None and limit < 1:
            raise ValueError(f"limit must be >= 1 or None for an exhaustive scan, got {limit}")
```

which also removes the `or 0` and the `max(..., 1)`, and gives mypy the narrowing it wanted. Two
cases: `limit=0` and `limit=-1` both raise, and the server records **zero** asks - the request count
is the assertion, exactly as A7 taught this suite.

### N1 (Nit) - `isinstance(reported, int)` accepts `True`

`jobvite_client.py:954`. `isinstance(True, int)` is `True` in Python, so an envelope carrying
`"total": true` lands a `bool` in `ScanResult.total`. MEASURED:
`E) total=true -> result.total=True type=bool incomplete=False`. `total=True` then compares equal to
`unique == 1`, so a one-record scan is declared complete against a `total` that is not a number.
`test_completeness_is_silent_when_no_total_was_reported` (`:476`) uses a string and does not reach
this. **Suggested fix:** `if isinstance(reported, int) and not isinstance(reported, bool):`, and add
`server.total = True` as a second arm of that existing case.

### N2 (Nit) - the U6 amputation step is the only amputation harness in `ci.yml` not passed `--amputation`

`ci.yml:549` at `8d7af64` runs `check-u6-paging-amputation.sh --anchors-applied`. Every other
amputation step passes `--amputation` (`ci.yml:600`, `:614`, `:625`, `:632`, `:642`); U5's `:528` is
the only other exception. U6's own report §4 says *"`--amputation` is the right flag for CI because
survivors are output there"* and the merge used the other one.

**I checked before filing this and the gating is equivalent**: `scripts/ci-harness-gate.sh:131-146`
shows `--amputation` converts exit 1 and exit 3 into named errors, and the generic `rc -ne 0` branch
below still fails the build without it. So the loss is diagnostic, not a hole: an unexpected
survivor reports `harness exited 1` instead of pointing the reader at `UNEXPECTED SURVIVOR`, and a
red baseline or a renamed test id (exit 3) is indistinguishable from it. Likewise `--min-rows 10
--row-re` is absent from `:549`, but the harness carries `ROW_FLOOR=10` internally at
`check-u6-paging-amputation.sh:296-300`, so the floor exists. **Suggested fix:** make `:549` (and
`:528`) match the others - `--amputation --min-rows 10 --row-re '^########## A[0-9]+ '` - and raise
10 to 11 when M3's split lands.

### N3 (Nit) - the wire-page-size consequence, stated as a number rather than as a worry

Not re-filing the deferral. The consequence, since a finding about it was invited: with
`min(transport_cap, configured_result_cap)` and the default 50, an exhaustive scan of the 1,240
records `DESIGN.md:473` uses as its worked example is **25 requests**, which against the 6/min
self-throttle of `DESIGN.md:425-427` is **4 minutes 10 seconds of wall clock for one tool call**.
`test_the_wire_page_size_is_the_min_of_the_two_caps` (`:519`) pins that at 500 for the
transport-binding arm, so if the decision goes the other way the case changes with it. **The
decision interacts with H2**: whatever bound answers H2 must be expressed in pages *and* be sane at
both 50 and 500 per page, so it should be settled before U7 sizes the outbound budget, not after.

### N4 (Nit) - a docstring word contradicting its own assertion

`tests/test_pagination.py:280` says a moved start would lose record zero "silently"; `:295` asserts
`result.incomplete is True`. Fix quoted in the Claim 1 section above.

---

## Where I looked and found nothing

Recorded so the next round does not re-derive it, and each is a search whose path I confirmed
resolves.

- **A `total` path into the loop.** None. `total` is written at `:953-955` and read at `:1006` only.
- **A hand-kept list beside its container.** The paging block enumerates nothing. `transport_cap()`
  (`:843-853`) is a two-branch conditional, not a route table, and `scan_start()` (`:874-891`) reads
  a `Mapping` supplied by the caller. The `ROUTES`-shaped list M1's fix would need does not exist
  yet, which is a thing to watch when M1 is fixed, not a finding now.
- **A green that tested nothing.** 447 passed, 6 deselected, **0 skipped**; the 6 are the
  `credentialed` and `network` markers the addopts deselect. 16/16 controls fired and 10/10 anchors
  applied, both run by me at `8d7af64`, not read from a log.
- **ADR-0023 compliance in the two new harnesses.** `set -uo pipefail` at
  `check-u6-paging-controls.sh:34` and `check-u6-paging-amputation.sh:33`, each with the `-e`
  rationale and a path citation to `docs/adr/0023-...` directly above. **My first grep looked for
  the token `ADR-0023`, found nothing, and I nearly filed it** - the harnesses cite the ADR by file
  path. Recorded because the instrument, not the object, produced the zero.
- **A comment upgrading the vendor's 1-based claim into an observation.** None. `:415-422`,
  `:874-891`, `.env.example:101-103` and `tests/test_pagination.py:584-594` each keep "claim" and
  "observation" apart, and `test_the_structural_assertion_start_zero_is_accepted` asserts only the
  one `200`.
- **500/1000 asserted as server facts.** None; labelled at `:443-451`, at `transport_cap()`'s
  docstring `:850-851`, and inside `test_the_transport_caps_are_the_designs_figures` `:494-495`.

---

## What I could NOT settle

- **Whether H2 is reachable against the real Jobvite.** It needs an endpoint that ignores `start`
  and keeps answering a full page. `/v1/jobFeed` is the candidate - it is the one route on a
  different API version, and whether it honours `start`/`count` at all is not in
  `JOBVITE-API.md`. No credential exists, so I could not ask it. **The fix does not depend on the
  answer** (an unbounded loop is a defect whether or not this tenant triggers it), but the priority
  does.
- **Which named test kills M4's replacement mutation.** I measured `1 failed, 446 passed` for
  `unique=len(seen) + unidentified + duplicates` and did not capture the failing node id before
  restoring. Whoever writes the row must read it off the run rather than take my guess at
  `test_a_full_page_of_duplicates_is_not_a_short_page`.
- **Whether the `unidentified` inflation in H3 can occur with the *correct* id key.** It needs a
  resource where some records legitimately lack `eId`, under the clamping hypothesis. I could not
  establish from `JOBVITE-API.md` whether `eId` is mandatory in a v2 record; the fix in H3 is
  correct either way, but if `eId` is optional then M2's over-read branch is reachable in normal
  operation and not only under a mis-keyed scan.
- **Whether CI has ever run these two steps green.** U6's report §7 records 11 consecutive CI
  failures at the time it was written and task #46 records the root cause fixed at `3082a18`. I ran
  both harnesses locally in a pinned worktree; I did not look at an Actions run.
- **U7's and r2-fixes' current content.** I deliberately did not read either working tree. If U7 has
  already added a bound inside `scan()`, H2 may be closed on that branch and my finding is against
  `8d7af64` as instructed.

---

## Housekeeping

- Report committed on `review/r5`, cut from `d0abd10`. **Not merged, and `main` was not pushed.**
- **No file under `src/`, `tests/` or `scripts/` was modified on any branch.** The five mutations
  and amputations lived only in `/tmp/code-review-r5-work`, each `cmp`-verified as landed before the
  run and `cmp`-verified as restored after it. The final `cmp` against the backup passed, and
  `git status` in that worktree was clean.
- `docs/DESIGN.md` was not edited. H2 carries a **Proposed** ADR-0024 and nothing more.
- `docs/OBLIGATIONS.md` was not hand-edited and no anchor moved; this report adds a file and changes
  no existing line.
- Both worktrees removed: `/tmp/code-review-r5-work` (the pinned `8d7af64` measurement tree) and
  `/tmp/code-review-r5-report`.
