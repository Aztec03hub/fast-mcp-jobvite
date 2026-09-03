# MEASURED-290: what `check-u4-client-amputation.sh` selects, and whether it holds

Task #290. Measured 2026-09-02 (finished 06:45 PM CDT) in a dedicated worktree
`/home/plafayette/claude_projects/evolv/repos/wt-290-u4` on branch
`measure/290-u4-selection`, based at `c965ce0d27ce0185518ab13034cae6344a7b25b8`
(read with `git rev-parse HEAD`, not typed from a brief). Box: WSL2 kernel
6.18.33.2-microsoft-standard-WSL2, 8 CPUs. Runnable artefact:
`docs/reviews/probe-290-u4-coverage.sh`, committed beside this file.

**THE ANSWER IN ONE LINE.** U4 selects per row from a coverage map its own
baseline builds, exactly as U9 does, and selection is **verdict-preserving on all
17 rows with an IDENTICAL killer set on all 17** - strictly better than U9's
13/14. **U4 does NOT carry U9's A14 subprocess blind spot**, and it cannot: the
`tests/test_jobvite_client.py` suite that both arms live inside contains **zero**
subprocess, `Popen`, `spawn_marker_server`, `multiprocessing` or
`sys.executable` call sites (`grep -n`, §5). Zero rows hit the rc=4 fallback.

What IS true, and is a reporting defect rather than a gate weakness, is that
**every row's published `survivors:` count is a SELECTED-set figure while it
reads as a suite figure** - `A9f` prints `survivors: NONE` under selection where
the same amputation leaves 39 passing assertions in the full file (§4). That is
the mirror image of the killer-count finding #286 recorded for U9 as F1/F3.

---

## 1. The mechanism, stated before it was measured

`scripts/check-u4-client-amputation.sh` differs from
`check-u9-http-amputation.sh` in one structural way that is the entire reason
this had to be measured rather than argued by analogy from #286.

| | U9 | **U4** |
| --- | --- | --- |
| suite / fallback arm | the whole `tests` tree | **one file**, `tests/test_jobvite_client.py` (`:72`) |
| map built over | the whole `tests` tree | **that one file** (`:114`) |
| suite size in the tally | 895 collected | **42 passed** |

The steps, all in `check-u4-client-amputation.sh`:

- `:107` `COVDB="$(mktemp /tmp/u4-amp-covdb-XXXXXX)"` - a per-run database.
- `:114` `COVERAGE_FILE="$COVDB" ... pytest $SUITE -q ... --cov --cov-context=test`
  builds the map. `$SUITE` is the single file at `:72`, so **the map can only
  ever name node ids inside that file**.
- `:160-161` each row pipes its **pristine-file** anchor into
  `scripts/lib/select-covering-tests.py "$file"` with `COVERAGE_DB="$COVDB"`.
  The selector locates the anchor, converts it to a line range, and reads
  `DISTINCT c.context` from the `arc` table for arcs whose `fromno`/`tono` land
  in that range (`scripts/lib/select-covering-tests.py:68-98`).
- `:213` `pytest $sel -q -p no:cacheprovider -rA` - `$sel`, a space-separated
  node-id list, **replaces `$SUITE` as the pytest argument**. Unquoted on
  purpose, with a measured `shellcheck disable=SC2086` note at `:205-212`.
- `:222` `verdict_guard "$rc" "$OUT" "$ROW_TIMEOUT"` refuses any rc outside
  `{0,1}`, so a collection error cannot be scored as a kill.

Selector rc handling, at `:163-169`:

| selector rc | harness does | at |
| --- | --- | --- |
| 0 | runs the selected node ids | `:213` |
| 4 (no in-process coverage) | falls back to the **whole `$SUITE` file** | `:164-165` |
| anything else | **aborts, exit 3** | `:166-168` |

The harness reads its verdict from `^PASSED ` lines (`:226-235`) and publishes
`survivors`, not killers - the inverse of U9. CI wires it at
`.github/workflows/ci.yml:1717` with `--amputation --anchors-applied
--min-rows 17`, so the **gate is on rows and anchors applied, never on the
survivor count**.

**The brief's description of the mechanism is CONFIRMED in every particular.**
Nothing about it was refuted.

## 2. Direction of any possible error, restated because it bounds the finding

The selected ids are a **subset** of `$SUITE`. A test that goes red under
selection goes red under the file too. So selection can only ever turn a real
kill into a **loudly vacuous row** - the harness prints its survivors and
`ci-harness-gate.sh` reads them - and can **never** turn a vacuous row green.
Any difference found below is a noise/weakening question, not a correctness
hole. **No difference was found in the killer sets at all.**

## 3. The measurement, both arms, every row

`bash docs/reviews/probe-290-u4-coverage.sh`. Baseline `rc=0`,
`42 passed in 13.71s`. Suite size **42**, taken from the tally line, not counted
by hand. `TREE ROWS: 0` afterwards, and `cmp` proved the restore.

`ARM SEL` = the selected node ids. `ARM FULL` = all of
`tests/test_jobvite_client.py`. Seconds are pytest's own reported figures.

| row | selected | SEL killers | FULL killers | killer set same | SEL survivors | FULL survivors | SEL s | FULL s |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| `A1` evaluate_response applies NEITHER arm | 15/42 | 9 | 9 | **yes** | 6 | 33 | 0.09 | 13.41 |
| `A2` the ENVELOPE arm is deleted | 15/42 | 4 | 4 | **yes** | 11 | 38 | 0.07 | 13.35 |
| `A3` the HTTP-STATUS arm is deleted | 10/42 | 3 | 3 | **yes** | 7 | 39 | 0.06 | 13.30 |
| `A4` `_decode_json_object` returns `{}` | 26/42 | 17 | 17 | **yes** | 9 | 25 | 0.12 | 0.18 |
| `A5` markup never routed to defusedxml | 26/42 | 2 | 2 | **yes** | 24 | 40 | 13.54 | 13.40 |
| `A6` v2 sends NO credential headers | 23/42 | 2 | 2 | **yes** | 21 | 40 | 13.45 | 13.46 |
| `A7` jobFeed sends no credential params | 5/42 | 2 | 2 | **yes** | 3 | 40 | 0.05 | 13.53 |
| `A8` `_excerpt` neither redacts nor truncates | 10/42 | 2 | 2 | **yes** | 8 | 40 | 0.06 | 0.14 |
| `A9` M-5 reopened | 3/42 | 2 | 2 | **yes** | 1 | 40 | 0.06 | 13.38 |
| `A9b` transport error text unredacted | 3/42 | 2 | 2 | **yes** | 1 | 40 | 0.06 | 13.38 |
| `A9c` enumerated detail says nothing | 3/42 | 2 | 2 | **yes** | 1 | 40 | 0.06 | 13.39 |
| `A9d` v2 headers reach the log unredacted | 3/42 | 1 | 1 | **yes** | 2 | 41 | 0.05 | 13.61 |
| `A9e` exception text logged unredacted | 3/42 | 1 | 1 | **yes** | 2 | 41 | 0.06 | 13.61 |
| `A9f` transport failure never logged | 3/42 | 3 | 3 | **yes** | **0** | 39 | 0.07 | 13.63 |
| `A10` cookie jar never cleared | 28/42 | 2 | 2 | **yes** | 26 | 40 | 13.37 | 13.50 |
| `A11` request path logs NOTHING | 28/42 | 1 | 1 | **yes** | 27 | 41 | 13.37 | 13.58 |
| `A12` route-level 404 mapped to not-found | 15/42 | 2 | 2 | **yes** | 13 | 40 | 0.10 | 13.51 |

**Totals: 17 rows. Verdicts preserved 17/17. Killer sets identical 17/17. Rows
with a FULL-only killer: 0. Rows with a SEL-only killer (which would mean
selection is not a subset run, and would be an instrument fault): 0. Rows that
hit the rc=4 fallback: 0.** Row time 54.64s selected vs 202.36s unselected -
**3.70x** on the row phase alone, before the shared baseline is charged to
either side.

Every arm returned `rc=1`; none was refused by `verdict-guard.sh`, so the
"a nonzero rc is not automatically a kill" trap named in the brief did not fire
here and no row's verdict rests on that inference.

## 4. The one thing selection DOES change: the published survivor count

The killer sets agree everywhere. The **survivor counts do not, on all 17 rows**,
because the FULL arm runs 42 tests and the selected arm runs 3 to 28. Most of
that gap is uninteresting - a test that never executes the amputated lines is
not a "survivor" of the amputation in any useful sense, which is precisely the
argument `select-covering-tests.py:8-14` makes for selecting at all.

**`A9f` is where it stops being uninteresting.** Under selection it prints

```
  survivors: NONE - no assertion passed against this tree
```

which is the harness's phrasing for a perfect kill, on a row whose whole purpose
(`check-u4-client-amputation.sh:386-391`) is to prove that relocated controls go
vacuous when the log line is deleted. Under the file it prints 39 survivors. The
number is not wrong for what it measures; it is **labelled as a fact about the
suite and is a fact about 3 node ids**. `HARNESS-RESULT` publishes `applied=`,
not survivors, and CI gates on rows and anchors (`ci.yml:1717`), so **no gate is
affected** - but `TOTAL SURVIVING ASSERTIONS ACROSS ALL AMPUTATIONS` is now a
selected-set sum, and past tasks (#104, #130, #280) have read that class of
number as a finding. Recorded here rather than changed, because #261 and the
REVAMP-238 record quote U4's tallies and this branch is a measurement.

## 5. The blind-spot question, answered by grep and not by inference

U9's A14 lost four killers that drive a real child process through
`spawn_marker_server`, which an in-process `--cov-context` map cannot observe.
The equivalent search over U4's suite:

```
grep -n -E 'subprocess|Popen|spawn|multiprocessing|sys\.executable|uvicorn\.run|os\.fork|threading|run_in_executor|asyncio\.create_subprocess' tests/test_jobvite_client.py
```

returns **nothing** over all 1000 lines. `spawn_marker_server` appears only in
`tests/test_boot.py`, `tests/test_shutdown.py` and `tests/test_spawn_orphan.py`,
none of which is in `$SUITE`. **U4 does not carry the A14 blind spot**, and the
0 FULL-only killers in §3 is the independent confirmation: there was no killer
outside the map to lose.

## 6. A SEPARATE finding, which is about the harness's SUITE and not its selection

Do not fold this into §3 - it answers a different question.

`probe-290-u4-coverage.sh` also runs in a mode that builds the map over the
**whole tree** and prints, per row, which test FILES cover that row's anchor:

```
PROBE_290_MODE=select-only PROBE_290_BASE_SCOPE=tests \
  bash docs/reviews/probe-290-u4-coverage.sh
```

Baseline `889 passed, 6 deselected in 57.45s`. Every one of the 17 anchors is
covered by tests **outside** `tests/test_jobvite_client.py`, and by a large
margin - `A1` is covered by 126 ids of which only 15 are in `$SUITE`; `A9`
through `A9f` by 11 ids of which 3 are. The recurring outside files are
`test_pagination.py`, `test_resilience.py`, `test_approval_write.py`,
`test_tools_jobs.py`, `test_tools_job_feed.py`, `test_tools_candidates.py`,
`test_audit_phase_sites.py` and `test_http_hardening.py`.

That is a property of the harness choosing a single-file `$SUITE` at `:72`, not
of selection: it predates #238 and both arms of §3 sit inside it. It bounds what
U4's rows can ever claim - "nothing in `test_jobvite_client.py` survived" is not
"nothing in the suite survived". **None of those outside files spawns a child
process either**, so widening `$SUITE` would not expose a subprocess blind spot;
it would only add in-process killers. Not changed here, and not filed as a
defect: it is a scope decision that deserves its own task if anyone wants it
revisited.

## 7. Reproducing this

```bash
git worktree add -b <branch> <dir> c965ce0d27ce0185518ab13034cae6344a7b25b8
cd <dir>
bash docs/reviews/probe-290-u4-coverage.sh                    # §3, ~5 min
PROBE_290_MODE=select-only PROBE_290_BASE_SCOPE=tests \
  bash docs/reviews/probe-290-u4-coverage.sh                  # §6, ~2 min
git status --porcelain -- src tests                           # must be empty
```

The probe takes a pristine copy of the subject before anything runs, restores it
from that copy on **any** exit via an EXIT trap, proves the restore with `cmp`
after every single arm, and prints `git status --porcelain -- src tests` at the
end. It printed `TREE ROWS: 0` on both runs recorded here.

## 8. What I did NOT verify

- **The runner.** Everything above is one WSL2 box. #243 has already measured one
  mutant that dies locally and survives on the GitHub runner, so a CI-side
  re-run is the only thing that would settle the arms there. The subprocess
  answer in §5 is a `grep` over committed source and is machine-independent.
- **Row-to-row flake.** Each arm ran **once**. The killer sets agreeing 17/17
  with zero one-sided differences is strong, but it is a single sample per arm.
- **Whether widening `$SUITE` would change any row's verdict.** §6 measures only
  *coverage*, not the arms - I did not run the 17 amputations against the whole
  tree. That is a bigger measurement and a different task.
