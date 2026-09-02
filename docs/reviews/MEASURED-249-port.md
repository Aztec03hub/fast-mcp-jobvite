# MEASURED: #249, porting R24-H1 (`84d4959`) onto current main

2026-09-02 09:01 AM CDT. Branch `fix/249-port-r24h1`, forked from `main` at
`6f89364`. Worktree `/tmp/w249`.

`84d4959` ("R24-H1: ask the INTACT tree once per harness, because no mutated run
can answer the question") was written, reviewed, credited as done on task #249 -
and never landed. `git for-each-ref --contains 84d4959` returns one ref,
`refs/heads/ci/242-under-five`, which is not an ancestor of main. Eight harnesses
still carry the defect it fixes.

## WHAT THE DEFECT IS ON MAIN, WHICH IS NOT WHAT IT WAS ON `84d4959`'S BASE

This is the first thing a reader needs, because the two trees carry DIFFERENT
wrong answers to the same question and a cherry-pick would have swapped one for
the other blind.

`84d4959` forked before #244. On its base, the per-row `--collect-only` probe had
already been deleted by #244 and replaced by a per-row rule reading pytest's rc
plus its `^ERROR <file> - <Exception>` line; `84d4959` deleted THAT rule.

Main never took #244. On main the operative code is the ORIGINAL per-row probe,
a second pytest process inside `mutate()`:

    main:scripts/check-u9-http-controls.sh:119
      timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "$selector" \
        --collect-only -q -p no:cacheprovider >/dev/null 2>&1

So on main the fix is worth MORE than it was on the branch it was written on. It
is still the correctness fix - the property is about the INTACT tree and
`mutate()` is a loop over MUTATED ones - and here it also DELETES a pytest
process per row instead of merely relocating a grep.

`git cherry-pick 84d4959` was NOT used, and could not have been: it would have
tried to remove a block that is not in main's files, and where it did apply it
would have reverted main's ROW_FLOOR derivation prose (rewritten since the fork -
see "Differences from `84d4959`" below).

## THE TRANSFORMATION

Applied to all eight, anchored on lines asserted UNIQUE per file before use
(`/tmp/w249-port.py`; it exits non-zero on a missing or duplicated anchor rather
than editing on a guess):

1. after `TOTAL=0` - declare `SELECTORS=()`
2. after `TOTAL=$((TOTAL + 1))` in `mutate()` - `SELECTORS+=("$selector")`,
   placed beside the counter it must equal
3. DELETE the per-row probe block from `mutate()` (comment head
   `# DOES THE SELECTOR STILL RESOLVE?` through the closing `fi` of its `if`,
   plus the separating blank line)
4. after `ROW_FLOOR=N`, before `harness_result_ran` - the ONE intact-tree check:
   a count comparison against `TOTAL`, then a single
   `timeout "$SELECTOR_TIMEOUT" uv run --frozen pytest "${SELECTORS[@]}"
   --collect-only`, then a success line

The check sits BEFORE `harness_result_ran`, deliberately. `harness_result_emit`
defaults `status` to `refused` when `harness_result_ran` was never called, so an
`exit 3` here prints `status=refused` - the honest word for a harness that cannot
aim - rather than `breach`, which would read as a mutation result.

Aggregate check that nothing else was touched: every deleted line across the
eight is one of the 14 lines of that probe block, each appearing exactly 8 times,
plus the per-file comment prose above it. Nothing else was removed.

Deleted process starts: the eight declared ROW_FLOORs sum to 12+21+17+20+16+31+
25+14 = **156**. Eight one-per-harness calls are added. Net **-148 pytest process
starts** per full harness sweep.

### Per-harness notes

All eight took the transformation identically - the deleted block's CODE is
byte-identical in all eight (only the explanatory comment above it differs), and
all four anchors were unique in every file. **Nothing was left unported.**

One ordering note, `check-u7-resilience-controls.sh`. Alone among the eight, u7
prints `echo "$FIRED/$TOTAL controls fired."` and calls `harness_result_tally`
BEFORE `ROW_FLOOR=31` (line 535-538), where the other seven print them after. The
new block therefore emits its refusal AFTER u7's "31/31 controls fired." line.
This is cosmetically inverted but not wrong: `harness_result_ran` is still below
the new block (line 620), so a refusal still exits 3 with `status=refused`, and
the tally field is independent of status by design (see the "WHY THIS IS NOT JUST
`status` READ TWICE" note in `scripts/lib/harness-result.sh`). Recorded so the
next reader does not mistake it for a port error.

## DIFFERENCES FROM `84d4959`, AND WHY

Measured file by file (`diff -u` of `git show 84d4959:scripts/<f>` against the
ported file). Changed lines: u9 52, u10/u12/u14/u8 68, body-cap/u5 78, u7 90.
Every one falls into exactly one of four buckets.

1. **The ROW_FLOOR derivation comments (all files except u9).** Main rewrote
   these since the fork. The port keeps MAIN's version; `84d4959`'s file carries
   the older prose. Keeping the branch's would have been the silent revert a
   cherry-pick produces. This is the whole reason for buckets existing at all.

2. **The `harness_result_tally` position in u7.** Main moved it above the floor
   comment; `84d4959` has it below. Main's position is kept - the port inserted
   nothing there.

3. **The rc=124 branch, KEPT from main and absent from `84d4959`.** `84d4959`
   wrote the call as `if ! timeout ...; then`, which discards the exit code, so a
   collection HANG and a rename render identically. Main's per-row probe
   distinguished them ("collection NEVER FINISHED... a hang, not a rename") and
   this port preserves that by capturing `sel_rc` and branching on 124. Two
   reasons: (a) losing a diagnosis main already has would be a regression smuggled
   in under a port, and (b) `scripts/check-timeout-literals.py` requires a seconds
   figure in an abort message to be INTERPOLATED from the bound's name - the
   preserved branch is where `${SELECTOR_TIMEOUT}s` is read, and it keeps that
   gate meaningful rather than merely satisfied by absence.

4. **Prose in the new block's comment, and one added success line.** The comment
   is rewritten because it must describe MAIN's starting point (the per-row pytest
   probe), not `84d4959`'s (#244's grep rule); describing the wrong predecessor
   would be a doc that lies at exit 0. `84d4959`'s measured per-harness misreport
   counts (u7 31/31, u8 14/25, u12 2/17, u5 2/16) were dropped rather than copied
   forward, because those were measured against #244's rule which is NOT in this
   tree - a number carried into a tree it was not measured on is a second copy
   free to disagree with reality. The added
   `########## ALL $TOTAL SELECTORS RESOLVE (one intact-tree process)` follows
   `check-u3-audit-controls.sh`'s shape on main, so a switched-off check and a
   passing one do not render identically. It does not match any `--row-re` in
   `ci.yml` (`^########## M[0-9]+ `), so no row count moves.

No unexplained difference remains.

The reference for "what fixed looks like against CURRENT main" was
`scripts/check-u3-audit-controls.sh`, which carries this shape already - arrived
at from the other direction by #252's per-row selection work (`5f46303`), and
citing `84d4959` by hash in its own comment at line 95.

## MEASURED

### Before/after verdicts - `check-u9-http-controls.sh` and `check-body-cap-controls.sh`

Run in `/tmp/w249` on `main` (`6f89364`) and again after the change.

| harness | rc before | rc after | result line before | result line after |
|---|---|---|---|---|
| check-u9-http-controls.sh | 0 | 0 | `rows=14 floor=14 fired=14/14 status=ok` | `rows=14 floor=14 fired=14/14 status=ok` |
| check-body-cap-controls.sh | 0 | 0 | `rows=12 floor=12 fired=12/12 status=ok` | `rows=12 floor=12 fired=12/12 status=ok` |

Row-by-row: `diff` of every `##########`, `KILLED`, `SURVIVED` and
`controls fired` line, before against after, is EMPTY except for the one added
success line in each. **No row's verdict changed.**

### The other six, after only

Not run before, so this is a floor check rather than a verdict comparison - but
`docs/reviews/check-row-floor-exactness.py` asserts every floor EQUALS its
harness's live row count, and all six printed exactly their floor:

    check-u5-jobs-controls.sh        rc=0  fired=16/16  status=ok   40.8s
    check-u7-resilience-controls.sh  rc=0  fired=31/31  status=ok   33.1s
    check-u8-candidates-controls.sh  rc=0  fired=25/25  status=ok   62.3s
    check-u10-write-controls.sh      rc=0  fired=21/21  status=ok   57.1s
    check-u12-jobfeed-controls.sh    rc=0  fired=17/17  status=ok   43.6s
    check-u14-arguments-controls.sh  rc=0  fired=20/20  status=ok   42.7s

### A renamed selector is STILL DETECTED - the fix must not trade a defect for a blind spot

Negative control (`/tmp/w249-planted.sh`): one selector renamed to a test that
does not exist (`test_a_malformed_inbound_request_id_is_REPLACED_XYZ`), planted
into a COPY of the u9 harness, run against both shapes.

| shape | rc | what it printed |
|---|---|---|
| main (per-row probe) | 1 | `SELECTOR DOES NOT RESOLVE - the test was renamed or moved.` / `fired=13/14 status=breach` |
| ported (one per harness) | 3 | `A SELECTOR DOES NOT RESOLVE ON THE INTACT TREE (pytest rc=4).` / `rows=0 floor=0 status=refused` |

Still caught, and caught LOUDER: `refused` instead of `breach`, which is the
correct word - the harness could not aim, it did not measure a control and find
it short. The probe copy was removed afterwards and `git status` re-read.

### Timing

Wall clock, same worktree, same machine, back to back:

| harness | rows | before | after | delta | per row |
|---|---|---|---|---|---|
| check-u9-http-controls.sh | 14 | 69.4s | 39.9s | **-29.6s (-42.6%)** | -2.1s |
| check-body-cap-controls.sh | 12 | 59.8s | 38.9s | **-20.9s (-34.9%)** | -1.7s |

Roughly **1.7-2.1 seconds per row**, which is one `uv run --frozen pytest`
startup and collection. Extrapolated over the 156 rows of the eight, that is on
the order of **4.5-5.5 minutes of pytest startup deleted from a full sweep**, and
CI's floor is bound by TOTAL work spread over lanes rather than by the largest
step - so this is work removed, not work moved. #273 should take the measured
per-row figure above rather than the row count.

## GATES

Run in `/tmp/w249` with ci.yml's exact invocations, flags included.

    shellcheck --severity=warning <the 8 files>                            rc=0
    bash -n <the 8 files>                                            8x    rc=0
    uv run --frozen python scripts/check-timeout-literals.py --self-test   rc=0
    uv run --frozen python scripts/check-timeout-literals.py               rc=0
    python3 scripts/check-harness-anchors.py --self-check --floor 464      rc=0
    python3 docs/reviews/check-row-floors.py                               rc=0
    python3 docs/reviews/check-row-floor-exactness.py                      rc=0
    python3 docs/reviews/check-row-floor-exactness.py --self-test          rc=0  (A1-A20 all PASS)
    bash scripts/check-pytest-bounded.sh --self-test                       rc=0
    bash scripts/check-pytest-bounded.sh                                   rc=0  (81 invocations, 81 bounded)

    bash scripts/ci-harness-gate.sh check-u9-http-controls.sh --controls-fired   rc=0
    bash scripts/ci-harness-gate.sh check-body-cap-controls.sh \
      --controls-fired --min-rows 12 --row-re '^########## M[0-9]+ '             rc=0

No floor moved: `check-row-floor-exactness.py` prints "Every floor equals its
harness's live row count" over 34 harnesses, 16 `--min-rows` values compared to
live counts.

## WHAT I DID NOT DO

* Did not push, did not merge, did not touch `ci/242-under-five` or any other
  agent's worktree.
* Did not run before/after verdict comparisons on six of the eight - only u9 and
  body-cap were run in both states. The six were run in the ported state only.
* `src/fast_mcp_jobvite/http_hardening.py` is MUTATED IN PLACE by these harnesses
  and restored per row, so `git status` in this worktree shows product code as
  modified WHILE a harness is running. It is transient by design (each row `cmp`s
  the restored file against a pristine copy and exits 3 if it differs). Verified
  clean after the runs three ways, because `git diff --quiet` alone is blind to
  an untracked file: `git diff --quiet -- src/` rc=0, `git status --porcelain --
  src/` 0 lines, and a byte `cmp` of the working file against `HEAD:`. No product
  code is in this branch.
