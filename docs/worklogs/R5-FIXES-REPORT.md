# R5-FIXES - H1, M1, M3 and M4, the four findings outside U7's file

**Agent:** `r5-fixes`. **Branch:** `fix/r5-findings`, cut from `a99238b`.
**Worktree:** `/tmp/r5-fixes-work` (`git worktree add`), removed after the final push - stated
again in §7.
**Design read at:** `git show c15b138:docs/DESIGN.md`. Not edited, and no ADR was needed: nothing
here is a defect in the design.

**`src/fast_mcp_jobvite/services/jobvite_client.py` WAS NOT EDITED ON THIS BRANCH.** `u7-resilience`
owns it. The two U6 harnesses mutate and amputate it in the worktree by design; every row takes a
backup first, `cmp`-checks that the change LANDED, restores by `cp`, and `cmp`-checks the restore
against a pristine copy taken before row 1. Every probe I ran by hand did the same. `git status` on
this branch shows no modification to that file, and I confirmed the restore with `cmp` after every
harness run - quoted below. **No `git stash` and no `git checkout <path>` was used anywhere.**

**Baseline at `a99238b`, read from the terminal before any edit:**

```
uv run --frozen pytest -q -p no:cacheprovider    447 passed, 6 deselected in 28.96s   exit 0
```

Zero skipped. The 6 deselected are the `credentialed` and `network` markers the addopts deselect.

---

## 1. H1 and M3 - one piece of work, done in the order that proves the control

R5's H1 is a surviving amputation: deleting `jobvite_client.py:997-999` left the whole suite green.
M3 is *why* - amputation row A7's comment claimed it deleted "both the loop break and the final
truncation" and its anchor deleted only the break. The row read as coverage of a behaviour it never
touched.

### Step 1, before writing any test: split A7, raise the floor, watch A7b go VACUOUS

`scripts/check-u6-paging-amputation.sh`: A7 became **A7a** (the in-loop break, the original anchor)
and **A7b** (the final truncation, the half the comment claimed), and `ROW_FLOOR` went `10` -> `11`.
Run against the tree with no new test in it:

```
HARNESS EXIT=1
########## A7b the caller's limit does not truncate the result
  ============================== 25 passed in 0.07s ==============================
  *** VACUOUS ROW *** the behaviour was deleted and NOTHING went red.
########## ROWS: 11   ANCHORS APPLIED: 11
::error::1 VACUOUS ROW(S) - a behaviour was deleted and nothing
         went red. Search the log above for 'VACUOUS ROW'.
CLIENT RESTORED (cmp ok)
```

**That is the control, and it was run first on purpose.** A7b is proved able to fail before anything
was done to make it pass. 11 rows, 11 anchors applied, so the split landed on both halves.

### Step 2: the case, in `tests/test_pagination.py`

`test_a_clamped_page_still_returns_no_more_than_the_limit`. Server holds one record repeated three
times followed by five fresh ones; `max_results=4`, `limit=4`. Page one is **full on the wire (4)
and yields two NEW records**, so the in-loop break at `len(items) >= effective_limit` does not fire
and the scan asks for a second page, reaching six. Only the final truncation brings it back to four.

**The assertion is the item COUNT, never `capped`** - R5 measured `capped=True` both intact and
amputated, so the result object cannot tell the two apart. Asserted: `server.asks == [(0, 4),
(4, 4)]`, `result.pages == 2`, `len(result.items) == 4`, `result.duplicates_dropped == 2`.
`pages == 2` is what stops the case being satisfiable by an implementation that never pages.

### Step 3: the same harness again, and A7b now kills

```
HARNESS EXIT=0
########## A7a a caller's limit does not stop the loop
  ========================= 2 failed, 24 passed in 0.08s =========================
########## A7b the caller's limit does not truncate the result
  ========================= 1 failed, 25 passed in 0.07s =========================
########## ROWS: 11   ANCHORS APPLIED: 11
########## TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: 236
CLIENT RESTORED (cmp ok)
```

A7b: exactly one test goes red, and it is the new one. A7a now kills two, because a scan that never
stops on the limit also changes the asks the new case pins.

**One thing worth saying about the two rows.** They are not independent in the direction a reader
might assume: A7a kills the new case as well as
`test_a_capped_call_stops_asking_once_it_is_full`, while A7b kills **only** the new case. So A7b is
the row with exactly one owner, and it is the one that was vacuous.

---

## 2. M4 - M11's title and body were both wrong, in opposite directions

**Re-measured rather than trusted.** All three probes: backup first, `cmp` for LANDED, `cp` restore,
`cmp` for RESTORED, `PYTHONDONTWRITEBYTECODE=1`.

**Probe 1 - the TITLE's mutation is a no-op.** Replacing `unique=len(seen) + unidentified` with
`unique=len(items)`:

```
LANDED: YES
exit=0   ====================== 448 passed, 6 deselected in 25.17s ======================
RESTORED OK
```

448 rather than R5's 447 because H1's case had already landed. R5's reasoning holds: `scan()`
appends to `items` exactly once per new id and once per unidentified record, so on the path where
completeness runs `len(items) == len(seen) + unidentified` **identically**. A survivor that is not a
defect - the row's stated subject is not a behaviour this code has.

**Probe 2 - the BODY is M10.** Applying M11's own body,
`unique=total if isinstance(total, int) else len(seen)`, over `tests/test_pagination.py`:

```
LANDED: YES
exit=1
FAILED tests/test_pagination.py::test_de_duplication_cannot_recover_a_never_returned_record
FAILED tests/test_pagination.py::test_completeness_fires_on_an_exhaustive_scan_with_a_gap
========================= 2 failed, 24 passed in 0.09s =========================
RESTORED OK
```

The second name is **M10's own named test**. Forcing `unique = total` makes
`if unique == total: return False` always taken, which is M10's behaviour reached by another route.
Confirmed by measurement, not by reading: 16 rows held 15 distinct behaviours.

**Probe 3 - R5's replacement, and THE FAILING TEST'S NAME, read off my own run.** R5 recorded the
count and not the node id and said so. Applying `unique=len(seen) + unidentified + duplicates`:

```
LANDED: YES
exit=1
FAILED tests/test_pagination.py::test_a_scan_is_whole_under_both_surviving_hypotheses[1]
================= 1 failed, 447 passed, 6 deselected in 24.67s =================
RESTORED OK
```

**It is NOT `test_a_full_page_of_duplicates_is_not_a_short_page`**, which is what R5 guessed. It is
the clamping arm of the both-hypotheses case, and that is the right owner on the merits: a
1-based-with-clamping server serves one duplicate per page after the first (`DESIGN.md:460-462`),
so counting those duplicates inflates `unique` past `total` and a **whole** scan reports itself
incomplete. `:665` asserts `result.incomplete is False`, which is the assertion that dies.

**The row now reads:**

```bash
mutate "M11 the completeness count includes duplicates the seen set dropped" \
  "$CLIENT" \
  "$SUITE::test_a_scan_is_whole_under_both_surviving_hypotheses[1]" \
  '            unique=len(seen) + unidentified,' \
  '            unique=len(seen) + unidentified + duplicates,'
```

with the whole measurement above written into the comment beside it, so the next reader does not
re-derive why the old title was undetectable.

**On the parametrised selector.** `[1]` is pytest's id for the VALUE `base=1`, not a positional
index into the parametrize list, so it does not silently repoint if the list is reordered - and
`mutate()` refuses to run a row whose selector does not `--collect-only`, so a rename reports rather
than passing forever. Verified: the selector collects exactly 1 test.

Row count is unchanged at 16 and the harness's own floor of 16 is untouched; this is a repoint, not
an addition. Post-fix, through the gate CI uses:

```
bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh --controls-fired      exit 0
########## M11 the completeness count includes duplicates the seen set dropped
  target: tests/test_pagination.py::test_a_scan_is_whole_under_both_surviving_hypotheses[1]
  KILLED - the named test went red, as it must
########## 16/16 controls fired.
CLIENT RESTORED (cmp ok)
```

---

## 3. M1 - the two sets, enumerated rather than eyeballed

**The brief asked for both sets and here they are**, produced by `inspect.signature` over the real
constructor and an `ast` walk over the real factory, not by reading:

```
__init__ parameters : ['api_key', 'api_secret', 'company_id', 'max_results',
                       'start_base_overrides', 'timeout', 'transport']
factory passes      : ['api_key', 'api_secret', 'company_id', 'max_results']
IN __init__, NOT PASSED: ['start_base_overrides', 'timeout', 'transport']
PASSED, NOT IN __init__: []
```

**Three are unpassed and only one is a defect.** I checked the other two rather than assuming:

- `transport` - `None` in production is the documented value (`:583-584`, ADR-0007); it exists for
  `MockTransport`. Not a settings-to-transport gap: **there is no setting for it.**
- `timeout` - falls back to the client's own explicit per-phase
  `httpx2.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)` at `:613-616`, chosen precisely so
  no library default is inherited silently. **`grep -n "timeout" src/fast_mcp_jobvite/config.py
  .env.example` returns NOTHING**, so there is no configured value failing to reach it. Not a
  sibling of F1.
- `start_base_overrides` - the real one, and F1's sibling in the argument list F1 was fixed in.

### The fix, and the container check that goes with it

`src/fast_mcp_jobvite/tools/jobs.py`:

```python
CLIENT_ROUTES: Final = (JOBS_PATH,)
...
            start_base_overrides=(
                None
                if settings.pagination_start_base is None
                else dict.fromkeys(CLIENT_ROUTES, settings.pagination_start_base)
            ),
```

The config value is a scalar and the client's contract is a per-route `Mapping`, so **something has
to name the routes the scalar applies to** - and a tuple written beside the call site is a hand-kept
list next to its container, the defect recorded seven times here. So it is not maintained by hand:
`test_the_client_routes_tuple_lists_every_route_this_module_asks_for` parses `tools/jobs.py`,
collects the `*_PATH` name every `client.request(...)` / `client.scan(...)` call actually passes,
and asserts that set is **EQUAL** to what `CLIENT_ROUTES` covers. A new route reaching the client
without an entry fails; so does a stale entry for a route nobody calls.

### The behavioural case, and both amputations proving it can fail

`test_the_default_client_factory_carries_the_pagination_start_base`, modelled on F1's case -
`client_factory=None` is the whole point, because every other case in that file supplies its own
factory and never reaches the branch that builds the real client. **It asserts BEHAVIOUR, not the
keyword argument**: `built_client.scan_start(JOBS_PATH) == 1`, because a case asserting
`seen[0]["start_base_overrides"] == {...}` passes against a client that ignores what it was handed.
It carries a **silence arm** - unset settings must give `scan_start(JOBS_PATH) == 0` - without which
it would pass against a factory that hands every route a base unconditionally, which is the failure
that loses record zero on a 0-based server.

```
CONTROL 1: amputate the start_base_overrides argument entirely
LANDED: YES   exit=1
FAILED tests/test_tools_jobs.py::test_the_default_client_factory_carries_the_pagination_start_base
========================= 1 failed, 42 passed in 0.92s =========================
RESTORED OK

CONTROL 2: CLIENT_ROUTES: Final = ()   (the hand-kept list going stale)
LANDED: YES   exit=1
FAILED tests/test_tools_jobs.py::test_the_default_client_factory_carries_the_pagination_start_base
FAILED tests/test_tools_jobs.py::test_the_client_routes_tuple_lists_every_route_this_module_asks_for
========================= 2 failed, 41 passed in 0.88s =========================
RESTORED OK
```

Control 2 is the interesting one: emptying the tuple is what "a route was added and nobody updated
the list" looks like from the other end, and the container check catches it independently of the
behavioural case.

### `.env.example`, rewritten in place rather than appended to

It said *"Pagination base, per resource"* over a single value, for a variable that reached no code.
The wiring fixes half of that; the wording was still wrong, so I rewrote those lines to say what is
now true - one value, applied to every route the calling tool asks the client for - and to name
U6-F2 as the open question rather than implying the file can already express a per-resource answer.
**I did not settle F2.**

### What F2 costs now, since I was told to say

- **F2 is cheaper than when U6 filed it, and my change does not make it more expensive.** There is
  still no reader outside this factory: `grep -rn "pagination_start_base" src/` now returns its
  definition in `config.py` and **exactly one** call site, `tools/jobs.py`. Option (a) - parse
  `resource=base` pairs - replaces the `dict.fromkeys(...)` expression and the `.env.example` block
  and touches nothing else. Option (b) - keep the scalar, call it global - is what is shipped
  minus the word "global", and `CLIENT_ROUTES` is where "global" would be spelled out.
- **The cost F2 defers is a wrong answer that cannot be expressed.** A tenant whose resources
  disagree about the base cannot be configured today. That is now written in `.env.example` instead
  of being implied away.
- **The remaining latency is not F2's.** `scan()` still has no caller in `src/` (U8/U12), so
  `scan_start()` is only reached by tests. The value now reaches the client; nothing yet reaches
  `scan()`. `search_jobs` calls `client.request(...)` directly.

---

## 4. Gate exit codes, every one copied from the terminal

```
uv run --frozen pytest -q -p no:cacheprovider          exit 0   450 passed, 6 deselected, 0 skipped
uv run --frozen ruff check .                           exit 0   All checks passed!
uv run --frozen ruff format --check .                  exit 0   56 files already formatted
uv run --frozen mypy                                   exit 0   no issues found in 45 source files
uv lock --check                                        exit 0   Resolved 118 packages
uv run --frozen python docs/reviews/check-quickstart.py            exit 0
uv run --frozen python scripts/check_advisories.py                 exit 0
python3 scripts/check-harness-anchors.py --self-check --floor 197  exit 0   198 anchors resolved
bash scripts/check-harness-anchors-controls.sh                     exit 0   9/9 controls fired
python3 scripts/check-committed-file-types.py --all   exit 0   247 files checked, none refused
python3 docs/reviews/check-design-citation-shape.py                exit 0
python3 docs/reviews/check-obligations.py                          exit 0
python3 docs/reviews/check-obligations.py --controls               exit 0
python3 docs/reviews/check-coupling.py docs/DESIGN.md              exit 0
python3 docs/reviews/check-cross-references.py                     exit 0
python3 docs/reviews/check-coupling-controls.py       exit 0   34/34 controls fired
python3 docs/reviews/check-coupling-sweep.py                       exit 0
python3 docs/reviews/check-plan-measurements.py                    exit 0
python3 docs/reviews/check-resweep-verdicts.py                     exit 0

bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh  --controls-fired   exit 0  16/16
bash scripts/ci-harness-gate.sh check-u6-paging-amputation.sh --anchors-applied exit 0  11/11, 0 vacuous
bash scripts/ci-harness-gate.sh check-u5-jobs-controls.sh    --controls-fired   exit 0  16/16
bash scripts/ci-harness-gate.sh check-u5-jobs-amputation.sh  --anchors-applied  exit 0  14/14
```

`check-obligations.py` verbatim final lines:

```
Mappings: 31  |  anchors verified against their subject: 24  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
```

**No anchor moved.** That 24/7 split is identical on unmodified `main` at `a99238b`, which I ran in
the shared checkout to be sure it was not my edit - `docs/OBLIGATIONS.md` was not hand-edited.

**The two U5 harnesses were run because they are the only ones that touch `tools/jobs.py`**
(`grep -ln "tools/jobs.py" scripts/*.sh` -> exactly those two), and their CI invocations were read
out of `ci.yml` rather than retyped. Both still green, `jobs.py` `cmp`-verified restored.

**`ruff format` was run BEFORE the final harness runs**, as the brief requires; it reported
`56 files left unchanged`, and every harness number above is from after it. It did surface one real
lint failure in my new docstring - `W505 Doc line too long (76 > 72)` at
`tests/test_pagination.py:587` - which I fixed by rewrapping, after which `ruff check .` exits 0.

**Shell linting.** `command -v shellcheck` -> **ABSENT from PATH**, as U6 recorded. Both harnesses I
edited linted with the pinned wheel instead:
`uvx --from shellcheck-py shellcheck scripts/check-u6-paging-{controls,amputation}.sh` -> **exit 0**,
zero output. That is a different binary from a CI step's and is evidence, not a discharge of
`bash.md:734`.

## The floors. DERIVED, not retyped, and the `ci.yml` edits are yours

Both read out of `ci.yml` with the `PREAMBLE.md` commands, on this branch, at the time of writing:

```
grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
    check-suite-floor.sh 447
grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
    check-harness-anchors.py --self-check --floor 197
```

| Floor | `ci.yml` today | Measured on this branch | New value |
|---|---|---|---|
| `check-suite-floor.sh` | **447** | 450 passed, 0 skipped | **450** |
| `check-harness-anchors.py --floor` | **197** | 198 anchors resolved | **198** |

+3 tests (H1's case, and M1's two) and +1 anchor (A7's split adds one row; M11's repoint adds none).

**I did not edit `ci.yml`.** The row floor that IS mine is the one inside the harness at
`check-u6-paging-amputation.sh`, and it is done: `ROW_FLOOR=10` -> `ROW_FLOOR=11`.

**A note for whoever takes R5's N2.** N2 proposes making `ci.yml:549` match the other amputation
steps - `--amputation --min-rows 10 --row-re '^########## A[0-9]+ '`. **That number must now be 11.**
Both `A7a` and `A7b` match `^########## A[0-9]+ ` unchanged, so the regex needs nothing.

---

## 5. Findings, each with a suggested fix

**F1 (Low) - two mutation rows now name arms of the same test, and nothing says so.** M3
(`the advance skips one record per page`) names
`test_a_scan_is_whole_under_both_surviving_hypotheses` unparametrised - so it runs BOTH arms - while
M11 now names `[1]`. Both are legitimately distinct behaviours killed by the same case, exactly as
M12/M13 already share `test_the_result_cap_is_the_min_of_the_two_halves`. The risk is not
correctness, it is that a future edit to that one test can silently weaken two rows at once.
**Suggested fix:** a one-line comment on the test itself naming M3 and M11 as its mutation rows, in
the style `tests/test_pagination.py` already uses when it names M4 and M11 in the module docstring -
which, incidentally, is now stale in exactly this way and is F2 below.

**F2 (Low) - M4's repoint made a row attribution false, and I got its LOCATION wrong first.**
M11 no longer kills `test_de_duplication_cannot_recover_a_never_returned_record` - probe 3 shows
that case passing. **My first draft of this finding said the stale sentence was in
`tests/test_pagination.py`'s module docstring. It is not. `grep -n "M11" tests/test_pagination.py`
returns NOTHING**, and I am recording the miss rather than quietly fixing it, because I wrote a
`file:line`-shaped claim from memory of the U6 report I had read an hour earlier. The sentence is at
`docs/worklogs/U6-IMPL-REPORT.md:62` and `:177`, with a weaker echo at `docs/reviews/REVIEW-R5.md:62`.

**Those are historical reports and I did not touch them.** Each was true when written; rewriting a
dated measurement to match a later tree is how a record stops being one. The real gap is that
**nothing live carries the attribution at all** - the tests themselves name no mutation row, so no
instrument and no reader would ever notice this going false. It went false today and only a probe
found it.

**Suggested fix:** put the attribution where it can be checked, as a one-line comment on each of the
two cases naming the rows that own them - `test_de_duplication_cannot_recover_a_never_returned_record`
is now killed by amputation row **A2** (verified: A2's failures are exactly that case and
`test_completeness_fires_on_an_exhaustive_scan_with_a_gap`), and
`test_a_scan_is_whole_under_both_surviving_hypotheses` by **M3** and **M11**. Then a future repoint
edits a line beside the test rather than orphaning a sentence in a report nobody re-reads. I did not
do it because it belongs with F1's identical remedy and both are in prose another agent may be in.

**F3 (Nit) - `.env.example`'s pagination block is now the longest comment in the file.** Eleven
lines for one variable, because it carries the F2 history. **Suggested fix:** when F2 is settled,
cut it back to three lines and let the ADR carry the history - a template comment that outgrows its
variable is read past.

---

## 6. What I could NOT settle

- **U6-F2, deliberately.** Scalar versus per-resource is a contract decision and the brief reserved
  it. §3 states what it costs now rather than choosing.
- **Whether `CLIENT_ROUTES`'s container check survives contact with U8/U12.** It parses
  `client.request` and `client.scan` calls in `tools/jobs.py` only. A future tool module gets its
  own factory and its own tuple, and **nothing yet asserts that every such module has one** - that
  is the same defect one level out, and it does not exist to fix until a second module does.
- **R5's L2 / U6's F3 - the two contracted citations at `config.py:197` and `:200`.** Verified still
  open at `a99238b` (`config.py:197` cites `DESIGN.md:1569-1573`, `:200` cites `:1574-1580`). Not in
  my four, and `config.py` is not a file my brief gave me. **Nobody owns it**: R5 filed it, this
  brief excluded it, and it is not on the task list. It wants a task.
- **Whether CI has ever run the two U6 steps green.** Every number here is a local run in a pinned
  worktree. I did not look at an Actions run.
- **H2, H3, M2, N1** - `jobvite_client.py`, `u7-resilience`'s. Untouched, unread except as a
  measurement target, and unchanged on this branch.

---

## 7. Housekeeping

- Nothing merged, `main` not pushed. `fix/r5-findings` is pushed.
- Files changed on this branch: `tests/test_pagination.py`, `tests/test_tools_jobs.py`,
  `src/fast_mcp_jobvite/tools/jobs.py`, `.env.example`, `CHANGELOG.md`,
  `scripts/check-u6-paging-amputation.sh`, `scripts/check-u6-paging-controls.sh`, and this report.
  **`src/fast_mcp_jobvite/services/jobvite_client.py` is NOT among them.**
- **`CHANGELOG.md` carried a claim that had gone false and I rewrote it in place rather than
  appending a correction.** Its `Added` entry announced
  `JOBVITE_PAGINATION_START_BASE` as a working operator override; M1 is the finding that it read
  nothing. The entry now says what the variable does - one value over every route the calling tool
  uses - and a `Fixed` entry records that it previously reached no code, naming it as the
  result-cap omission's sibling in the same argument list.
- `docs/DESIGN.md` not edited; no ADR proposed.
- `docs/OBLIGATIONS.md` not hand-edited; `check-obligations.py` exits 0 and its output is quoted in
  §4, with the same numbers verified on unmodified `main`.
- `ci.yml` not edited. The two floors are in §4 for you.
- The worktree `/tmp/r5-fixes-work` was removed after the final push.
