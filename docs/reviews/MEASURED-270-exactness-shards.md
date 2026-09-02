# MEASURED-270: the exactness gate now multiplies by a shard count, and it is still an equality

Task #270. Branch `fix/270-exactness-shards`, based on `1636f56`.

**One file changed: `docs/reviews/check-row-floor-exactness.py`.** `ci.yml` and
everything under `scripts/` are byte-identical to `1636f56` - `git diff --stat
HEAD -- .github/workflows/ci.yml scripts/` is empty. Every sharded step in this
report was PLANTED and REVERTED.

## 1. The blocker, re-derived rather than taken on trust

#268 §5 says the gate reds on any sharded step. I did not carry that forward; I
planted it again on this branch and read the exit code.

    ci.yml:1667  --min-rows 10 -> 5, harness untouched at 10 rows

    check-u3-audit-amputation.sh   --min-rows   5  rows  10
    check-u3-audit-amputation.sh: SLACK by 5. It prints 10 rows and ci.yml
    passes --min-rows 5, so 5 row(s) can be deleted without the gate
    noticing. --min-rows is a LOWER bound; it must EQUAL the live count.
    rc=1

**#268 §5 REPRODUCES.** The step is wired at `ci.yml:1186`, so this is a red on
`main` the moment anything shards. `ci.yml` was restored and `git status
--short` was empty before I started the fix.

## 2. What changed, and why it is a tightening

Claim 3 was `live == min_rows`. It is now `live == min_rows * shards`, with
`shards` read from the step's own `env:` block. Four new functions and one
constant, all in the checker:

| site | what |
| --- | --- |
| `:360` | `SHARD_ENV = "HARNESS_SHARDS"` |
| `:371` | `_step_block()` - bounds the `env:` search to the step carrying the gate line |
| `:389` | `_shard_count()` - reads the count, or REFUSES |
| `:438` | `_min_rows_verdict()` - the equality, armed by `--self-test` rather than copied |
| `:472` | `_external_floors()` now returns `(min_rows, row_re, shards)` |

**The equality survives, and that was the constraint.** #223 tightened this
project's other floor comparison from `>=` to equality after measuring `>=`
blind (arms=10, floor=9, status=ok, exit 0). Nothing here reintroduces slack: a
sharded step gets a different MULTIPLIER against the same equality, not a lower
bound. §3 proves that by amputating a real row.

Three refusals, because a static checker that cannot read a shard count must
say so rather than default:

* **more than one `HARNESS_SHARDS` in a step** - undecidable multiplier;
* **a non-integer value** (`${{ matrix.n }}`) - a static checker cannot
  multiply by a run-time expression, and silently reading it as 1 lane would
  compare a real 2-shard step against the whole row count;
* **`shards < 1`** - `min_rows * 0` is 0, which would pass with the whole
  harness deleted.

Absent `env:` means `shards = 1`, which is every step in `ci.yml` today.

**Why `env:` and not a flag.** `scripts/ci-harness-gate.sh:190` is
`out=$(bash "$HARNESS_PATH" 2>&1); rc=$?` - no arguments. Nothing a gate line
writes after the harness name reaches the harness. That is read off the gate,
not chosen.

## 3. Gates, each judged by exit code

Every row below is a real run against the real `ci.yml`, not a unit fixture.

| what | before | after |
| --- | --- | --- |
| `check-row-floor-exactness.py`, unmodified ci.yml | rc=0, 16 compared | **rc=0, 16 compared** |
| `--self-test` | rc=0, 20/20 | **rc=0, 27/27** |
| PLANTED sharded step (`HARNESS_SHARDS: 2`, `--min-rows 5`, 10 rows) | **rc=1 "SLACK by 5"** | **rc=0** |
| ...and one row AMPUTATED from the harness (9 rows) | - | **rc=1** |
| ...and `--min-rows 4` against 10 rows (harness grew) | - | **rc=1 "SLACK by 2"** |
| `check-row-floors.py` on the sharded plant | rc=0 | **rc=0** |
| `ruff check` on the changed file | clean at HEAD | **rc=0** |
| `mypy` on the changed file | - | **rc=0** |
| `git status --short` after every plant | - | empty |

The decisive pair is rows 3 and 4. The exact configuration that was
`rc=1 "SLACK by 5"` is now `rc=0`; delete one real row from the sharded harness
and it returns to `rc=1`:

    check-u3-audit-amputation.sh   --min-rows   5  rows   9  x 2 shards
    check-u3-audit-amputation.sh: --min-rows 5 x 2 shards = 10 exceeds the
    9 rows it prints, so this step cannot pass.

The amputation was a real deletion of the `A10` row invocation from
`scripts/check-u3-audit-amputation.sh`, not a number edited in `ci.yml`.

**An UNEVEN split reds too**, and that is deliberate: 11 rows across 2 lanes has
no exact `--min-rows`, so the equality refuses rather than rounding. That closes
#268's own F6 nit at the checker instead of leaving it to the outer literal.

## 4. The three instruments, checked rather than assumed

The brief flagged that a fix landing on one of three instruments is a shape this
project has been burned by. **One of the three needed the change. I established
that by running the other two, not by reading them.**

* **`check-row-floors.py` - NOT AFFECTED, and it does read `--min-rows`.** It
  parses the flag at `:86` but only ever PRESENCE-tests it: `main()` asks
  "internal floor, external floor, or neither", never "does this equal a live
  count". Run against the planted sharded `ci.yml` it prints
  `check-u3-audit-amputation.sh - yes 5` and exits 0. It cannot go wrong on a
  sharded step because it never does the arithmetic.
* **`check-row-floor-controls.sh` - NOT AFFECTED, and it never reads `ci.yml`
  at all.** `grep -cE "min-rows|ci\.yml|workflows|HARNESS_SHARDS"` returns 0.
  **The zero is proved non-vacuous**: the same grep for `ROW_FLOOR|mode=computed`
  returns 16. Its subject is the harness's INTERNAL `ROW_FLOOR`, and it is not a
  CI gate.
* **`check-row-floor-exactness.py` - the only one that compared `--min-rows` to
  a derived row count, and the only one changed.**

## 5. Findings, each with a fix

**F1 (Medium, NOT fixed - filed, not widened into this task).** A sharded
harness will need its INTERNAL `ROW_FLOOR` to be shard-aware too, and
`check-row-floor-controls.sh` is the thing that watches that floor fire. Today
no harness is sharded, so there is nothing to be wrong; the moment one is, its
`ROW_FLOOR` becomes a per-lane number and the control's `rows - floor + 1`
deletion arithmetic is computed from a whole-harness count. *Fix:* whichever
task first shards a harness must decide whether `ROW_FLOOR` is per-lane or
whole-harness and make the control agree, in the same commit. The brief said to
file rather than widen, so this is filed.

**F2 (Low, FIXED in this branch).** `arm_floor` was `20` with `len(arms) >=
arm_floor`. I added 7 arms, so leaving the floor at 20 would have let all 7 be
deleted silently. Raised to 27, which is an equality against the live arm count
in the same run. *Note:* this file's arm floor is still spelled `>=` at `:1102`,
which is correct for a floor meant to ratchet upward as arms are added, and is
NOT the comparison #223 tightened - that one was the ROW floor. I did not change
it, and I am naming it so nobody reads my `>=` as the blind one.

**F3 (Nit, FIXED).** My own arm A22 FAILED on first run, and it was right to.
I asserted a deleted row produces `"SLACK by 1"`. It does not: deleting a row
moves `live` DOWN, so it lands on the cannot-pass message, not the slack one.
#268's "a deleted row still reds, because 9 != 5*2" is true about the arithmetic
and silent about which of the two messages it reaches. Both directions are now
armed separately (A22 short, A23 grew) rather than conflated.

## 6. The seven new arms

    A21  a sharded step with the right arithmetic PASSES
    A22  a sharded step ONE ROW SHORT still REDS
    A23  a sharded harness that GREW is SLACK, the other direction
    A24  an UNEVEN split REDS rather than rounding
    A25  a `${{ }}` shard count is REFUSED, not treated as unsharded
    A26  shards=1 leaves BOTH messages byte-identical
    A27  a sibling step's shard count does NOT leak across

**A26 is the one that would catch my own change going wrong.** The unsharded
population is all 16 compared steps in `ci.yml`, so a reworded finding would be
a change to 16 live verdicts; it pins both message strings byte-for-byte.

**A27 exists because the join is the dangerous part.** `_external_floors()`
folds continuations into a `joined` string, which moves every offset after the
first wrapped gate line. Reading the shard count off `joined` coordinates would
drift into a neighbouring step - silently, and in the direction that pairs one
step's `--min-rows` with another's shard count. The lookup is done on the RAW
text for that reason, and A27 holds it.

## 7. Merge

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only fix/270-exactness-shards

## 8. What I did NOT verify

- **No sharded step has ever RUN.** Everything here is static analysis of a
  planted `ci.yml`. That a 2-lane `check-u3-audit-amputation.sh` actually
  executes 5 rows per lane and that the gate's own `-lt` comparison behaves is
  UNPROVED, and belongs to whichever task builds the sharding.
- **actionlint: UNRUN.** Not installed locally, and CI fetches a pinned
  tarball. **This is an absence, not a green.** It is also not load-bearing
  here: `ci.yml` is byte-identical to `1636f56`, so there is no workflow change
  for it to judge. It becomes mandatory the moment a sharded step is committed.
- **pytest, ShellCheck: NOT RUN.** No shipped `.py` under `src/` and no `.sh`
  changed on this branch. ruff and mypy were run because the one changed file
  is Python.
- **`HARNESS_SHARDS` is a name I chose.** No prior art exists - `grep -rn
  "SHARD\|shard" scripts/ .github/workflows/ci.yml` returns nothing at
  `1636f56`. If the sharding task prefers another spelling, `SHARD_ENV:360` is
  the single site.
- **Job-level and workflow-level `env:` are NOT read**, only step-level - and
  I nearly shipped this bullet with the alarming version of that fact. My draft
  said a job-level `HARNESS_SHARDS` "would be a wrong-and-quiet 1". **That is
  FALSE, and planting it says so:** a job-level `HARNESS_SHARDS: 2` with
  `--min-rows 5` against 10 rows gives

      check-u3-audit-amputation.sh   --min-rows   5  rows  10
      ...SLACK by 5... rc=1

  It FAILS CLOSED, loudly, because the unread shard count leaves `shards = 1`
  and the step's halved `--min-rows` then looks like slack. That is the safe
  direction and it is a red somebody will chase, not a silent pass. I did not
  implement job-level inheritance because #268 §5 specified the step's block
  and a `matrix`-driven count is refused as non-literal anyway (A25); the bound
  is real but it is a nuisance, not a hole. *Fix, if it ever bites:*
  `_step_block()` is the single site, and the job block is its enclosing scope.
- **The container census is unchanged at 34 members**, equal both directions,
  and 16 harnesses compared - identical before and after. I did not
  independently re-derive those two numbers; I read them off the same program's
  output on both sides.
