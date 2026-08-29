# U6 - Pagination: implementation report

**Agent:** `u6-pagination`. **Branch:** `feat/u6-pagination`, cut from `d9cfc7f`.
**Design read at:** `git show c15b138:docs/DESIGN.md`, never the working tree.
**Worktree:** `/tmp/u6-pagination-work`, removed after the final push (stated again at the end).

---

## 1. What was built

All of it in `src/fast_mcp_jobvite/services/jobvite_client.py`, which I owned exclusively, plus one
new test module and two new harnesses. `tools/jobs.py`, `config.py` and `ci.yml` were read and not
written.

| Behaviour | Where | Design |
|---|---|---|
| Every scan starts at `start=0` | `SCAN_START`, `scan_start()` | `DESIGN.md:455-464` |
| Page cap 500 on v2, 1000 on `/v1/jobFeed` | `V2_PAGE_CAP`, `JOBFEED_PAGE_CAP`, `transport_cap()` | `DESIGN.md:434` |
| Per-scan seen set dropping duplicates | `scan()` | `DESIGN.md:465-468` |
| Termination on a SHORT page, never on `total` | `scan()` | `DESIGN.md:486-487` |
| Completeness vs `total`, **only** on an exhaustive scan | `_check_completeness()` | `DESIGN.md:469-477` |
| Start base per resource, with an override | `start_base_overrides` | `DESIGN.md:478-480` |
| `min(transport_cap, configured_result_cap)` | `result_cap()` | `DESIGN.md:434-436`, `:1572-1575` |

`ScanResult` carries `items`, `total`, `pages`, `duplicates_dropped`, `unidentified`, `capped`,
`exhaustive` and `incomplete`, because a caller handed only a list has to guess which of a capped
answer and an anomaly it is holding.

### Two decisions I made rather than deferred

**The advance is `start += count` from 0, never from a declared base.** This is the only advance
that is gap-free under both hypotheses the evidence leaves standing:

```
0-based:            page 1 = records 0..count-1, next start = count   -> no gap, no overlap
1-based + clamping: page 1 = records 1..count,   next start = count   -> record `count` twice,
                                                                         the seen set drops one
```

Advancing from a declared base of 1 skips record `count` on a 0-based server, which is the loss
`DESIGN.md:463-464` exists to prevent. The reasoning is in the module header so the next reader does
not have to re-derive it.

**The wire page size is `min(transport_cap, configured_result_cap)` with no branch on top.** My
first version used the raw transport cap for exhaustive scans and the min for capped ones. I removed
that branch: it is a paging policy the design does not state, I invented it, and it was untestable
without inventing a knob to test it with. One rule, one `min`, and `limit` only ever narrows it
further. **The cost is real and I am naming it**: an exhaustive scan now pages at
`JOBVITE_MAX_RESULTS` (50 by default), so a 1,240-record resource is 25 requests against a client
`DESIGN.md:425-427` says should self-throttle. If you want the other behaviour it should be a
decision recorded somewhere, not a branch I added quietly.

---

## 2. The three traps, and what I did about each

**Trap 1 - de-duplication defends against OVER-reading only.**
`test_de_duplication_cannot_recover_a_never_returned_record` drives a server that never serves
record zero whatever it is asked. The scan returns 5 of 6, `duplicates_dropped == 0` (the seen set
is the wrong instrument for this failure and never fires), and `incomplete is True`. The assertion
is on the **limitation**, not on the behaviour: the behaviour half is a separate case
(`test_an_overlapping_page_drops_duplicates`). Mutation row **M4** kills the behaviour case, **M11**
kills the limitation case, and neither kills the other.

**Trap 2 - the completeness check has two arms, and the second is the one people skip.**
Both are present and both are proved able to fail: **M10** makes the check never fire and kills arm
one; **M9** makes it fire on a capped call and kills arm two. Amputation **A3** deletes the
exhaustive condition outright.

**M9 SURVIVED on my first run, and the survivor was the finding.** My arm-two case used a capped
call that filled its limit, so it never reached a short page - `short_page` kept it quiet and
`not exhaustive` was doing nothing. An implementation with the exhaustive condition deleted passed
it. The case now carries a second sub-case: a capped call that **does** terminate on a short page
and still mismatches `total` (30 records served, `total` reporting 1,240). That is the only shape
where `not exhaustive` is load-bearing, and M9 kills it.

**Trap 3 - the result cap is one behaviour across two files.**
I added `transport_cap()`, `result_cap()` and the `min()`. I did not touch `tools/jobs.py`, did not
re-implement `build_result`, and this suite asserts nothing about `showing N of total`. Both
operands of the `min` are mutated separately (**M12**, **M13**), because a `min` written as either
operand alone passes a one-sided test.

---

## 3. What I did NOT write as established

- **`start` being 1-based is a VENDOR CLAIM** (`DESIGN.md:451`), and no default, comment or test
  says otherwise. `scan_start()` defaults to 0 for every resource; the vendor's sentence is recorded
  in the header as a claim beside the observation that falsifies only "1-based and strict".
- **The observation is `JOBVITE-API.md:399`**, and nothing more: `start=0` is accepted and returns
  records, in one genuine `200`. `test_the_structural_assertion_start_zero_is_accepted` asserts
  exactly that and no more.
- **Whether 500 and 1000 are real server limits is unobserved.** The constants say so at their
  definition, and the case that pins them (`test_the_transport_caps_are_the_designs_figures`) says
  in its own docstring that it is a claim about this client and not about Jobvite.
- **C3-I1 and C6-D1 are untouched.** I made no threat-model edit and closed nothing.

---

## 4. Gate exit codes, read from the terminal

Every one copied from the run, not predicted.

```
uv run --frozen pytest -q -p no:cacheprovider            exit 0   446 passed, 6 deselected, 0 skipped
uv run --frozen ruff check .                             exit 0   All checks passed!
uv run --frozen ruff format --check .                    exit 0   56 files already formatted
uv run --frozen mypy src tests                           exit 0   no issues found in 45 source files
python3 scripts/check-harness-anchors.py --self-check --floor 171   exit 0   197 anchors resolved
python3 docs/reviews/check-design-citation-shape.py      exit 0   464 citations, 0 unresolvable
python3 docs/reviews/check-obligations.py                exit 0   31 mappings, 23 verified, 8 absent
bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh --controls-fired         exit 0
bash scripts/ci-harness-gate.sh check-u6-paging-amputation.sh --anchors-applied
     --min-rows 10 --row-re '^########## A[0-9]+ '                                   exit 0
```

`check-obligations.py` verbatim final lines:

```
Mappings: 31  |  anchors verified against their subject: 23  |  recorded as absent: 8
Every mapped anchor still contains its subject. OK.
```

**Zero skips.** The 6 deselected are the `credentialed` and `network` markers the addopts deselect
by design, and that count is unchanged from the baseline.

### The two floors, measured on both trees. **The `ci.yml` edits are the team lead's.**

| Floor | `ci.yml` today | Measured on `main` at `d9cfc7f` | Measured on this branch | New value |
|---|---|---|---|---|
| `check-suite-floor.sh` | **421** | 421 passed | 446 passed | **446** |
| `check-harness-anchors.py --floor` | **171** | 171 anchors | 197 anchors | **197** |

+25 tests and +26 anchors (16 mutation rows + 10 amputation rows).

**A disagreement worth reporting, per the preamble.** `docs/briefs/U6.md` tells me to run
`--self-check --floor 164`. `ci.yml:481` carries **171**, and the dispatch message also said 171.
164 was the value at `9eed403` and went stale before the brief was dispatched - the same decay the
preamble's own suite-baseline paragraph is about. Suggested fix: the brief should point at the
derivation (`grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml`)
rather than name a number, exactly as it already does for the suite floor.

### The two `ci.yml` steps to add, for you to place in the harness block

```yaml
      - name: U6 paging - mutation controls
        run: bash scripts/ci-harness-gate.sh check-u6-paging-controls.sh --controls-fired

      - name: U6 paging - amputation
        run: bash scripts/ci-harness-gate.sh check-u6-paging-amputation.sh --amputation --min-rows 10 --row-re '^########## A[0-9]+ '
```

I ran the amputation step locally with `--anchors-applied` instead of `--amputation` (both exit 0);
`--amputation` is the right flag for CI because survivors are output there, and `--anchors-applied`
now refuses a run of zero rows either way.

---

## 5. Every harness row, and whether it fired

### `scripts/check-u6-paging-controls.sh` - **16/16 controls fired, exit 0**

Row floor 16. Every row names one test and that test must go red.

| Row | Mutation | Named test | Verdict |
|---|---|---|---|
| M1 | `SCAN_START` 0 -> 1 | `test_every_scan_starts_at_zero_on_the_wire` | KILLED |
| M2 | a per-resource override applied globally | `test_an_override_is_per_resource_and_not_global` | KILLED |
| M3 | the advance skips one record per page | `test_a_scan_is_whole_under_both_surviving_hypotheses` | KILLED |
| M4 | the seen set never rejects a duplicate | `test_an_overlapping_page_drops_duplicates` | KILLED |
| M5 | id-less records de-duplicated onto one key | `test_records_without_an_id_are_kept_not_collapsed` | KILLED |
| M6 | short-page test reads the kept records | `test_a_full_page_of_duplicates_is_not_a_short_page` | KILLED |
| M7 | `total` used as a loop condition | `test_a_total_that_understates_does_not_end_the_loop_early` | KILLED |
| M8 | `total` counted from the page | `test_a_total_that_overstates_does_not_extend_the_loop` | KILLED |
| M9 | completeness fires on a capped call | `test_completeness_does_not_fire_on_a_capped_call` | KILLED |
| M10 | completeness never fires | `test_completeness_fires_on_an_exhaustive_scan_with_a_gap` | KILLED |
| M11 | completeness counts every record, not unique | `test_de_duplication_cannot_recover_a_never_returned_record` | KILLED |
| M12 | `min()` drops its configured half | `test_the_result_cap_is_the_min_of_the_two_halves` | KILLED |
| M13 | `min()` drops its transport half | `test_the_result_cap_is_the_min_of_the_two_halves` | KILLED |
| M14 | the jobFeed page cap becomes v2's | `test_the_jobfeed_route_uses_its_own_transport_cap` | KILLED |
| M15 | `V2_PAGE_CAP` 500 -> 50 | `test_the_transport_caps_are_the_designs_figures` | KILLED |
| M16 | a caller's limit not clamped to the cap | `test_a_limit_above_the_configured_cap_is_clamped_to_it` | KILLED |

**Two rows survived the first run and both were real.** M8 and M9. Both are recorded above and in
§2; both tests were strengthened and both rows now kill. **The controls were run against the
unfixed code, seen to survive, then the test was fixed and the row seen to die** - not written
after the fact.

### `scripts/check-u6-paging-amputation.sh` - **10 rows, 10 anchors applied, 0 vacuous, exit 0**

Row floor 10. Survivors are the output. `TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS: 205`.

| Row | Behaviour deleted | Result (out of 25) | Read |
|---|---|---|---|
| A1 | the seen set entirely | 3 failed, 22 passed | the three de-duplication cases and nothing else, correctly |
| A2 | the completeness check never runs | 2 failed, 23 passed | arm one plus the limitation case |
| A3 | the completeness check fires on every call | 4 failed, 21 passed | arm two plus the two silence controls |
| A4 | paging: one request and stop | 8 failed, 17 passed | every multi-page case |
| A5 | every scan starts at the vendor's base of 1 | 17 failed, 8 passed | the widest blast radius here, as it should be |
| A6 | the transport half of `min()` | 3 failed, 22 passed | the cap cases |
| A7 | a caller's limit bounds nothing | 1 failed, 24 passed | see below - this row was VACUOUS first |
| A8 | id-less records discarded | 1 failed, 24 passed | one case owns it and no other sees it |
| A9 | `total` never read from the envelope | 5 failed, 20 passed | every case that reads `total` |
| A10 | an incomplete scan is never logged | 1 failed, 24 passed | only arm one asserts the log line |

**A7 WAS VACUOUS on the first run and that is the amputation harness earning its place.** Deleting
the in-loop cap break changed nothing observable, because the final truncation still returned 50
records. The suite could not tell a capped call that **stops** from one that pages the whole
resource and throws the rest away - 25 requests against a self-throttled client to return 50
records. The missing assertion was the request COUNT, and
`test_a_capped_call_stops_asking_once_it_is_full` (renamed from `..._asks_for_no_more_than_its_cap`)
now asserts `len(server.asks) == 1` and `result.pages == 1`. A7 kills it.

**Two behaviours are deliberately NOT amputated here, and the harness header says so** rather than
leaving it as a gap someone rediscovers: the `start += count` advance and the short-page termination
with no replacement. Delete either and the scan requests the same full page forever against a server
that keeps answering. Both are covered by bounded mutation rows instead (M3, M6, M7). The harness
also carries a `timeout 300` per row as a guard, with a message telling the next author to move an
unbounded row to the mutation harness.

### Shell linting, stated plainly

**`shellcheck` is ABSENT from the base checkout** (`command -v shellcheck` -> not found). I did not
leave it there: both new harnesses were linted with the pinned wheel,
`uvx --from shellcheck-py shellcheck scripts/check-u6-paging-{controls,amputation}.sh`, **exit 0,
zero warnings**. That is a different binary from the one a CI step would use, so it is evidence and
not a discharge of `bash.md:734`.

Both harnesses carry the ADR-0023 comment beside `set -uo pipefail`, and both follow the obligation
that ADR names: pristine copies taken before row 1, landing and restore checked with `cmp` and never
`git diff` (blind to an untracked file), `PYTHONDONTWRITEBYTECODE=1`, an anchor-uniqueness assertion
before every write, a row floor, and a selector-resolution check in the mutation harness.

---

## 6. Findings, each with a suggested fix

**F1 (High) - the two halves of the result cap can disagree in production, because nothing wires
the configured half into the transport half.** `tools/jobs.py:247` builds
`JobviteClient(api_key=api_key, api_secret=api_secret)` and passes neither `max_results` nor
`company_id`. So `JOBVITE_MAX_RESULTS=200` moves U5's in-tool cap and leaves the transport cap at
the client's default of 50: one behaviour, two files, two different numbers, and no test can see it
because each half is correct on its own. **Suggested fix**, one line in a file I do not own:
`JobviteClient(api_key=api_key, api_secret=api_secret, max_results=settings.max_results)`. Wiring
`start_base_overrides` needs F2 settled first.

**F2 (Medium) - `config.py`'s `pagination_start_base` is a SCALAR where `DESIGN.md:478-480`
requires per-resource.** `config.py:207` is `pagination_start_base: int | None = None`, and
`.env.example:101-104` documents it as "Pagination base, per resource" while offering one value.
A single int cannot express "per resource", so as shipped the override is global - which is the
exact failure mutation row M2 exists to catch inside the client. The client takes
`start_base_overrides: Mapping[str, int] | None` and is ready for either resolution.
**Suggested fix, and it is a decision not a patch**: either (a) parse the variable as comma-separated
`resource=base` pairs (`/jobFeed=1,/job=0`) and hand the client the mapping, or (b) keep the scalar,
document it as applying to every resource, and build `{path: value for path in ROUTES}` at the call
site. (a) matches the design; (b) is a smaller diff and needs a line in `.env.example` saying the
scalar is global.

**F3 (Low) - a contracted citation in `config.py:197`.** It cites `DESIGN.md:1569-1573` for
`max_results`. The `JOBVITE_MAX_RESULTS` bullet is `1572-1575`; `1569-1571` is the tail of the
preceding bullet, about a hand-kept list going stale. The range resolves, overlaps the subject, and
is wrong at both ends - the decay shape `check-design-citation-shape.py` explicitly cannot see.
`config.py:200` has the same shape for `outbound_rate_limit` (`:1574-1580` where the bullet is
`1576-1581`). **Suggested fix:** repoint both to `DESIGN.md:1572-1575` and `DESIGN.md:1576-1581`.
I did not touch `config.py`.

**F4 (Nit) - the brief's anchor floor was stale on arrival.** Covered in §4 with its fix.

---

## 7. What I could NOT settle

- **Whether the exhaustive-scan page size should be the transport cap or the result cap.** I chose
  the result cap and said why in §1, but the design does not decide it, and the choice costs 25
  requests where 3 would do on a 1,240-record resource against a client that is meant to self-throttle
  at 6/min. This wants your call or a line in the design, not my comment. **This is the one item
  here I would check first.**
- **Whether F2 should change the meaning of an already-documented environment variable.** Changing
  `JOBVITE_PAGINATION_START_BASE` from a scalar to a pair list is a `.env.example` contract change
  and I am not the one to make it alone.
- **Whether 500 and 1000 are real server limits.** Unobserved, as the brief says, and only a live
  tenant settles it. I asserted the configured figures and labelled them.
- **Whether `eId` is the right identifier key for every resource.** `DEFAULT_ID_KEY` is `eId` and
  `scan()` takes `id_key` per call, but the only recorded success body is the candidate one
  (`JOBVITE-API.md:395-400`). I did not verify that job requisitions carry `eId` under the same name,
  and a wrong key means every record is `unidentified`: kept, never de-duplicated, and silently
  immune to the seen set. **U8/U12 should check this against a real payload before relying on it.**
- **Whether `fix/r2-leftovers` (task #45, in progress) touches `services/jobvite_client.py`.** Task
  #44 records an open L-4 finding in that file. I was told the file was mine and worked on that
  basis; if r2-leftovers lands there, the merge order matters and I did not check its branch.
- **CI itself.** Task #46 records 11 consecutive CI failures. Every number above is from a local
  run in a clean worktree; I have not seen this branch go through CI.

---

## 8. Housekeeping

- Nothing was merged and nothing was pushed to `main`. The branch `feat/u6-pagination` is pushed.
- `docs/DESIGN.md` was not edited. No ADR was needed: nothing I found is a defect in the design, and
  the one place I went beyond it (§1's page-size rule) is a choice the design leaves open, recorded
  here rather than legislated in a comment.
- `docs/OBLIGATIONS.md` was not hand-edited; `check-obligations.py` exits 0 and its output is quoted
  in §4.
- `ci.yml` was not edited. The two floors and the two steps are in §4 for you.
- The worktree `/tmp/u6-pagination-work` was removed after the final push.
- `services/jobvite_client.py` is left for U7 to extend: `request` is untouched, the paging block is
  additive and sits after it, and U7's timeout/retry/breaker ordering goes around `request` without
  needing to unpick anything here.
