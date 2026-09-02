# MEASURED-270: the exactness gate now multiplies by a shard count, and it is still an equality

Task #270. Branch `fix/270-exactness-shards`, based on `1636f56`.

**Two files changed: `docs/reviews/check-row-floor-exactness.py`, and ONE
COMMENT in `.github/workflows/ci.yml`** - R270-R2-N3, a retyped arm count that
was already stale at the base and staler here; it is deleted rather than
corrected. Everything under `scripts/` is byte-identical to `1636f56`, and the
ci.yml delta is three comment lines replacing one, with no workflow semantics
touched. Every sharded step in this report was PLANTED and REVERTED.

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
| `--self-test` | rc=0, 20/20 | **rc=0, 48/48** (27, 34, 38, 42, 48 across five rounds) |
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
deleted silently. Raised to 48 across five rounds, which is an equality against the live arm count
in the same run. *Note:* this file's arm floor is still spelled `>=`,
which is correct for a floor meant to ratchet upward as arms are added, and is
NOT the comparison #223 tightened - that one was the ROW floor. I did not change
it, and I am naming it so nobody reads my `>=` as the blind one.

**F3 (Nit, FIXED).** My own arm A22 FAILED on first run, and it was right to.
I asserted a deleted row produces `"SLACK by 1"`. It does not: deleting a row
moves `live` DOWN, so it lands on the cannot-pass message, not the slack one.
#268's "a deleted row still reds, because 9 != 5*2" is true about the arithmetic
and silent about which of the two messages it reaches. Both directions are now
armed separately (A22 short, A23 grew) rather than conflated.

## 6. The new arms (seven at first pass, fourteen after R270)

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

## 7. The w194 salvage: NO COLLISION, and it is already superseded

After this branch was committed, 65 uncommitted lines from task #194 were
rescued to `salvage/269-worktree-residue` (`0c73f0d`) and pointed at me, because
they touch this same file. **They do not collide, and the question is settled by
reading both, not by preferring mine.**

The salvage introduces a `COMPUTED <ere>` table form. That is a DIFFERENT claim
from #270's - it is about members whose row count is built at run time, not
about sharded steps - and it is **already on `main` at `1636f56`, in a stronger
form than the salvage's**:

| | salvage `w194` | main `1636f56` |
| --- | --- | --- |
| the test | `:759` `ere.strip() == "COMPUTED" or ere.startswith("COMPUTED ")` | `:428` `is_computed()`: `ere.strip().split()[:1] == ["COMPUTED"]` |
| the census | `:859` `e.strip() == "COMPUTED"` - **NOT widened** | `:986` `is_computed(e)` - the same rule |
| arms | none | A17 admits `COMPUTED ^row "`, A18 refuses `^row "COMPUTED` |

**The salvage carries the defect this project keeps measuring: the fix rebuilt
one column over.** It widened the BRANCH at `:759` and left the CENSUS at `:859`
on the old equality, so a `COMPUTED <ere>` member would have been admitted by
the check and silently MISSING from the printed count. `is_computed()` closes
that by being one named rule with one call site per consumer, and it handles
leading whitespace, which `startswith` on an unstripped cell does not.

The controls.sh half is landed too: `mode=computed` appears 18 times in
`main`'s `check-row-floor-controls.sh`, including the
`ABORT: mode=computed requires column 2 to read 'COMPUTED <ere>'` guard at
`:365`.

**And my change does not touch any of it.** Measured, not asserted:

    git diff 1636f56 fix/270-exactness-shards -- <this checker> \
      | grep -E "^[-+].*(is_computed|COMPUTED)"

returns EMPTY. My diff is confined to claim 3 - `_shard_count`, `_step_block`,
`_min_rows_verdict`, `_external_floors` - and adds no line touching the COMPUTED
vocabulary. Two concerns, one file, disjoint hunks.

*Suggested disposition:* the salvage needs no adoption and no merge. Its
exactness.py half is superseded by #223's `is_computed()`; its controls.sh half
is on `main`. It stays valuable only as the record of what #194 concluded.

## 8. R270 round 1: a MEASURED fail-open in my own fix, and nine guards armed

R270 returned 0C/1H/4M/5L. **The High was real, and it was the shape this
whole file exists to catch: my fix rebuilt the defect one column over.** All
ten findings are closed below. Everything in §1-§7 above stands as written
unless a row here says otherwise.

### H1 - the join took a COMMENT, and it laundered real slack into exit 0

`anchor = raw.find(f"ci-harness-gate.sh {name}")` takes the FIRST textual
occurrence anywhere in the file. `_step_block()` then correctly bounded the
WRONG step. A27 passed throughout because it tested bounding GIVEN an offset;
the defect was in choosing the offset. **A six-line comment about exactly that
hazard sat one line above it and was not a guard.**

REPRODUCED HERE, old code against new, on the real `ci.yml`. u3 made genuinely
slack (`--min-rows 5` against 10 live rows, NO `env:`, unsharded) plus an
unrelated sharded step EARLIER in the file whose comment merely names u3's gate
command:

    OLD (701131a, raw.find)   rc=0   <- FAIL-OPEN. 5 deletable rows, gate green.
    NEW (step blocks)         rc=1   "SLACK by 5"

The decoy must precede u3 in FILE ORDER - my first two plants put it after, and
`raw.find` then picked the correct step, so the run was green for the wrong
reason. That is worth recording: the fail-open is order-dependent, which is why
it sat latent.

**THE FIX IS STRUCTURAL, not a patched offset.** `_step_blocks()` yields step
texts, continuations fold INSIDE each block, and `--min-rows`, `--row-re` and
the shard count all come from ONE block - so they cannot be attributed to
different steps. There is no offset left to be wrong.

### The other nine

| # | what | disposition |
| --- | --- | --- |
| M1 | `shards = 1` was a silent default for a LOOKUP FAILURE, not only a genuine absence | FIXED, and at the rule: wrapped gate lines and deep `- ` bullets are fixed by construction; job/workflow-level and flow-style `env:` are now a REFUSAL comparing every `HARNESS_SHARDS` mention against those readable in a step block |
| M2 | `shards < 1` guard untested, amputating left 27/27 green | FIXED, arm A31 |
| M3 | duplicate-`HARNESS_SHARDS` refusal untested, same | FIXED, arm A32 |
| M4 | the equality does NOT establish the lanes are DISJOINT | ADOPTED, stated in the docstring; two lanes running the same 5 rows satisfy both instruments. Blocking prerequisite filed on #272 |
| L1 | A24 vacuous - asserted only `!= []`, survived AMP-H | FIXED, asserts `SLACK by 1` |
| L2 | a negative count was refused as a "run-time expression" | FIXED, the sign is admitted so it reaches `shards < 1` |
| L3 | `2  # two lanes` refused as a non-literal | FIXED, trailing comment stripped |
| N4 | "no sharded step could ever be green" was INFERRED | NARROWED to what was run: blocked AT THIS GATE, and u3 specifically is unblocked because it declares no internal `ROW_FLOOR` |
| N5 | two gate lines for one harness collapsed last-one-wins | FIXED, now a refusal |

### Every guard amputated, and which arm died

Arms 27 -> 34. Each row is a run of `--self-test` with that guard replaced:

    AMP-A  the comment filter in _step_blocks     rc=1  33/34  killed A28
    AMP-B  duplicate gate line refusal            rc=1  33/34  killed A29
    AMP-C  out-of-block shard assertion           rc=1  33/34  killed A30
    AMP-D  shards < 1 guard                       rc=1  32/34  killed A31, A33
    AMP-E  duplicate HARNESS_SHARDS refusal       rc=1  33/34  killed A32
    AMP-F  the sign in the literal test           rc=1  33/34  killed A33
    AMP-G  the trailing-comment strip             rc=1  33/34  killed A34
    AMP-H  the multiplication itself              rc=1  30/34  killed A21-A24
    AMP-I  step-indent bounding                   rc=1  33/34  killed A27
    AMP-J  the non-literal refusal                rc=1  CRASH  (uncaught ValueError)

AMP-J kills by crashing rather than by a named arm - the same shape R270 itself
recorded for that guard. It is a kill; it is not a clean one, and I am naming
it rather than counting it as covered.

### TWO OF MY OWN ARMS WERE VACUOUS ON THE FIRST RUN OF THIS BATTERY

Recorded because it is the finding, not a footnote:

* **AMP-A survived at 34/34.** I had written TWO comment filters, and the one
  in `_external_floors()` could never fire because `_step_blocks()` already
  drops comment lines. It was INOPERATIVE code. **Deleted**, not left beside
  the live one, and A28 now covers the surviving filter.
* **AMP-B survived at 34/34.** A29 caught *any* `SystemExit`, and with the
  duplicate refusal amputated the FLAGS-COUNT assertion raised instead - so the
  arm passed for a reason that had nothing to do with its name. It now asserts
  its own message text.

Both are the same defect R270 found in A24, in my own new arms, found only by
amputating rather than by reading them.

### The count assertion earned its place

My first `_step_blocks()` treated a comment at step indent as a dedent and
ended the scan at the first block comment: **57 blocks holding 6 of 36 gate
lines.** The run did not report a reassuring number - `parsed 5 --min-rows
values but ci.yml carries 16 as flags` at rc=1. That assertion pre-dates this
branch and is why the bug took minutes rather than a review round.

### What I REFUSED, with the measurement

**R270-M1's suggested `yaml.safe_load` rewrite. NOT ADOPTED.** It would kill
all four M1 spellings at once and I still refused it, because the reviewer's
own "did NOT verify" list names the reason: whether PyYAML is importable in the
CI image. It is not safe here. This checker is invoked as bare
`python3 docs/reviews/check-row-floor-exactness.py` (`ci.yml:1186`, `:1197`),
and its job runs `actions/setup-python@v5` (`ci.yml:891`), which puts a
hostedtoolcache interpreter first on `PATH` - the same one #221 measured as
`hostedtoolcache 3.12.14`. A fresh hostedtoolcache Python carries no PyYAML.
The three sibling checkers that DO `import yaml` are every one of them invoked
as `uv run --frozen python`, never bare - so there is no precedent for it under
this checker's actual interpreter, and adopting it would trade a latent
join defect for an `ImportError` on every run. The regex path is hardened
instead, and M1's unreadable spellings are made LOUD rather than silently 1.

## 9. R270 round 2: 0H, and both Mediums were in code round 1 ADDED

Round 2 returned 0C/0H/2M/3L/4N and confirmed H1 closed by re-deriving it. All
nine findings are closed below; ONE is closed by REFUTING it with a measurement.

### M2 - the gate red ON A COMMENT, and this one would have fired immediately

`mentions` was a raw `findall` over the whole file. Its sibling `flags`, eleven
lines above, filters `#`. `readable` sums over blocks that already dropped
comments. Three quantities, three different ideas of what a line is.

MEASURED end to end on the real `ci.yml`, old code against new, by inserting
ONE documentation comment naming the token above the wired step:

    OLD (08fe119)  rc=1  "mentions HARNESS_SHARDS 1 time(s) but only 0 sit in
                          a step-level `env:` mapping" - blaming job-level,
                          workflow-level and flow-style env:, none of which
                          had happened
    NEW            rc=0

**Commenting a step out to disable one lane is the first thing anyone does to
the feature this branch exists to unblock.** `mentions` now carries the same
filter as `flags`; arm A36 dies when it is removed.

### M1 - the dedent exit was load-bearing and my own battery skipped it

`_step_blocks()`'s dedent exit. Deleting it left the suite 34/34 GREEN. My
round-1 battery ran ten guards and this was not one of them - `AMP-I` is the
OTHER branch of the same function, so it LOOKED covered. Without it, a later
job's `env:` is absorbed into the previous job's last step block, becomes
`readable`, DEFEATS the `mentions != readable` refusal I built for round-1 M1,
and hands an unsharded step a multiplier of 2. **That is H1 across a job
boundary.** Arm A35; the acceptance test the brief named passes - deleting the
four lines now prints `fired=37/38` and kills A35 by name.

### The rest

| # | disposition |
| --- | --- |
| L1 | FIXED at the rule. `_env_shard_values()` is ONE function with TWO callers (`_shard_count` and the `readable` sum), so a count inside a `run: |` script or under `with:` is no longer honoured - the refusal message now states a property the code actually establishes. Arm A37 |
| L2 | FIXED. A23 is a full-string equality, so the ` x N shards = E` clause is pinned; deleting it kills A23 |
| L3 | FIXED, and it was my own sibling-check omission. A25, A30, A31, A32 asserted only "some SystemExit" - the exact vacuity I found and fixed in A29 one round earlier and left in four siblings. All four now assert their message text, and all five catch `BaseException` so a non-`SystemExit` crash lands as a named FAIL row instead of silencing the tally |
| N2 | FIXED by deletion. The blank-line append was inoperative |
| N3 | FIXED in `ci.yml`. The retyped arm count is DELETED rather than corrected, per the docstring's own rule that a number written beside a gate decays |
| N4 | FIXED. `[-+]?` - R270-L2's fix had stopped at one of the two signs. A33 now carries `+2` |
| **N1** | **REFUTED, with the measurement. See below.** |

### N1 REFUTED: the not-a-step-list exit is load-bearing, and here is the case

R270-R2 could not build a shape where it changes a verdict and suggested
deleting it. **It decides.** A `steps:` whose first content line is not a `- `
item:

    intact     -> []                      (correctly not a step list; the
                                           flags-count assertion then reds)
    amputated  -> ['      - run: bash scripts/ci-harness-gate.sh a.sh ...']

Amputated, the item below is collected as a step of a mapping that is not a
step list at all. The guard STAYS, and arm A38 now holds it - deleting it
prints `fired=37/38`. This is the one finding I did not adopt, and the reason
is a measurement rather than a preference.

### The battery, ten guards, every one killed by a NAMED arm

    R2-M1 the dedent exit (acceptance test)     rc=1  37/38  killed A35
    R2-M2 the comment filter on `mentions`      rc=1  37/38  killed A36
    R2-L1 env-bounding: leave-the-mapping reset rc=1  37/38  killed A37
    R2-L1 env-bounding: the `env:` anchor       rc=1  37/38  killed A37
    R2-N1 the not-a-step-list exit              rc=1  37/38  killed A38
    R2-L2 the ` x N shards = E` clause          rc=1  37/38  killed A23
    R2-N4 the `+` sign                          rc=1  37/38  killed A33
    R2-L3 the non-literal refusal               rc=1  37/38  killed A25
    prior the multiplication                    rc=1  34/38  killed A21-A24
    prior equality -> `>=`                      rc=1  35/38  killed A23,A24,A26

**`R2-L3` is the row that changed character.** In round 1 that same amputation
was my AMP-J: it crashed with an uncaught `ValueError`, printed no
`HARNESS-RESULT` line, and I reported it as a kill that was not a clean one.
The `BaseException` catch turns it into a named A25 failure. The tally can no
longer be silenced by the thing it is meant to measure.

### THREE OF MY OWN NEW ARMS WERE WEAKER THAN THEIR NAMES, again

Found by running the battery, not by reading them:

* **A37 survived its own guard's amputation at 38/38.** My first fixture put
  the token inside a `run: |` script in a step with NO `env:` at all, so
  `env_indent` was never set and the leave-the-mapping reset was never
  exercised. The fixture now carries a real `env:` first.
* **A33 did not cover `+`.** R270-R2-N4 said to extend it and I had not; the
  amputation proved the gap rather than the report.
* **A36 crashed instead of failing** when its guard was cut, silencing the
  tally - my own A28 rationale, not applied to A28's newest sibling.

That is the same class as round 1's two vacuous arms and round 2's L3. The
lesson holds at the level of the RULE, not the instance: **an arm is not
evidence until its guard has been cut and the arm has been seen red.**

### The sibling sweep completed - two MORE of the same shape, in my own round-2 fix

The round-2 note asked me to take the twin search seriously as a RULE rather
than as nine separate fixes. Applying it to my own round-2 work found two more
instances I had left: A28 and A34 still carried a bare `except SystemExit:`
while their five siblings had been converted.

They are exposed to exactly the defect the conversion exists for. Amputating
the literal test raises `ValueError` inside BOTH their call paths, which a bare
`except SystemExit` does not catch - so the harness would print no
`HARNESS-RESULT` line and the arm floor would never run. Measured after the
sweep:

    literal test amputated -> rc=1  fired=37/38  killed A25

`grep -c "except SystemExit:"` over the file is now **0**. Seven arms, one
rule, no survivors of the shape.

**This is the third round in which the twin search found something reading did
not.** Round 1: A29 vacuous, four siblings left. Round 2: those four fixed, A28
and A34 left. The rule that actually holds is narrower than "check the twin" -
it is *the sweep is not finished until the selector returns zero*, and a count
is the only way to know that.

## 10. R270 round 3: the same fail-open a THIRD time, one column over again

Round 3 returned 0C/0H/2M/2L/2N and NOT MERGEABLE. All six closed. Two of them
I closed by REFUTING the finding with a measurement, and the blocking one was
mine for the third time in the same file.

### M1 - I bounded the TOKEN and never bounded the `env:` ITSELF

Round 2's L1 said a count outside `env:` was silently honoured. I fixed it by
requiring the token to sit under an `env:` line - and accepted **any**
`^\s*env:\s*$` at **any** indent. So an `env:`-SHAPED line inside the step's
own `run: |` scalar, or an `env:` nested under `with:`, is found and read.
GitHub Actions applies neither.

MEASURED, old code against new, all three shapes:

    P1  env: here-doc'd inside a run scalar, no step env: at all
          OLD a38e0fb: {'a.sh': (5, '^r ', 2)}      NEW: REFUSED
    P3  with: > env: nested
          OLD a38e0fb: {'a.sh': (5, '^r ', 2)}      NEW: REFUSED
    P1b real env: FIRST, then env: in the run scalar
          OLD a38e0fb: {'a.sh': (5, '^r ', 2)}      NEW: REFUSED
    CONTROL a real step-level env:
          OLD: (5, '^r ', 2)                        NEW: (5, '^r ', 2)

End to end that laundered a genuinely unsharded, genuinely slack step to exit 0
where base reds `SLACK by 5` - **the same signature as round 1's H1, arrived at
through a third door.**

*Fix:* `_env_shard_values()` derives the step's KEY INDENT from the block's own
`- ` and requires `env:` at exactly that indent with the token strictly deeper.
Both my measurement and the reviewer's were true; mine tested the token and
theirs tested the mapping, and only one of us was testing the property the
message claims.

**A37 was the eighth weak arm** and its name was the tell: it claimed the
general property while its fixture exercised only the leave-the-mapping reset.
It now runs all three shapes.

### M2 - two guards, each the other's only backstop, both unarmed

The per-block continuation fold and the `flags`-count assertion. Amputate BOTH
and **13 of the live `ci.yml`'s 16 gate lines silently vanish**: the checker
parses 3, compares 3, prints "Every floor equals its harness's live row count.
OK." and exits 0 - verbatim the "reassuring zero rather than an error" the
assertion's own message names. Both pre-date this branch and were unarmed
there too; this branch rewrote both sides, so it closes them. Arms A39, A40.

### L1 and N1 REFUTED, both with measurements

* **L1** called the dedent test's second half unreachable and a deletion
  candidate. It is neither: a non-comment, non-item line at exactly the item
  indent yields **1 block intact, 2 amputated** - the item below is collected
  into a list that key already closed. Kept, and armed by A41.
* **N1** is about my own evidence rather than the code, and it is right:
  `grep -c "except SystemExit:"` returning 0 was **blind to
  `except SystemExit as exc:`**, which two sites still used. Neither was
  exposed, so the code was fine and the PROOF was not. Both converted for
  uniformity; `grep -cE "except SystemExit\b"` is now 0.

**That is the second time in two rounds that a selector I offered as proof was
narrower than the shape it swept.** Round 2's rule - *the sweep is not finished
until the selector returns zero* - needs its rider: **the selector must match
the SHAPE, not a literal string.** A count from a pattern blind to its own
variants is exactly the confident zero the rule exists to prevent.

### L2, N2

L2: the quote strip in `int(value.strip(...))` was unarmed - a mutant turns a
legal `HARNESS_SHARDS: '2'` into an unhandled `ValueError`. Arm A42. N2: a
comment my own round-2 reflow garbled, duplicating one line and dropping
another. Rewritten.

### The battery: twelve guards, every one killed by a NAMED arm

    R3-M1 env: bounded to key indent      41/42  A37
    R3-M1 the key_indent derivation       34/42  A25,A27,A28,A31,A32,A33,A34,A42
    R3-M2 the continuation fold           41/42  A39
    R3-M2 the flags-count assertion       41/42  A40
    R3-L1 the dedent test's 2nd half      41/42  A41
    R3-L2 the quote strip                 41/42  A42
    prior the dedent exit                 41/42  A41
    prior the comment filter              40/42  A28,A36
    prior the not-a-step-list exit        41/42  A38
    prior the multiplication              38/42  A21,A22,A23,A24
    prior equality -> `>=`                39/42  A23,A24,A26
    prior the mentions comment filter     41/42  A36

**One honest note on attribution.** Amputating the dedent exit now kills A41,
not A35. A35 survives it because M1's key-indent bound independently refuses
the absorbed job-level `env:` - two guards where there was one. The dedent exit
IS armed, by A41; A35 no longer arms it, and saying "A35 covers it" would be
the kind of stale attribution this file exists to catch.

## 11. R270 round 4: the FOURTH join, and a decision on the unread variable

Round 4 returned 0C/0H/1M/3L, NOT MERGEABLE on the Medium. All four closed.

### M1 - I bounded the `env:` KEY and never bounded the token to its CHILDREN

Round 3 fixed "any `env:` at any indent" by requiring the step's key indent.
It still never required the token to be a **DIRECT CHILD** of that mapping, so
a line inside a multi-line env VALUE is read as the lane count:

        env:
          NOTE: |
            HARNESS_SHARDS: 2

Actions sets `NOTE`. MEASURED end to end on the live `ci.yml`, u3's real step
with its floor halved 10 -> 5:

    OLD (f2c88b1)  rc=0  "Every floor equals its harness's live row count. OK."
    NEW            rc=1

**Four rounds, four joins, each one column over from the last:** the offset
(H1), the `env:` mapping (R3-M1), the token's depth (this), and in between the
comment filter and the dedent exit. The property I keep getting wrong is not
the code, it is that I bound ONE dimension of a two-dimensional shape and call
it done. `_env_shard_values()` now latches the mapping's own child indent and
skips anything deeper. Arm A43, on the reviewer's `NOTE: |` fixture rather
than one of mine - a nested-map fixture is weaker because Actions rejects that
workflow anyway.

**Why the `mentions != readable` assertion could never have caught it:** that
assertion compares a token INVISIBLE to the step scan against one it can see.
Here both counts are 1. It was never the guard for a MISATTRIBUTED token, and
believing otherwise is how a guard gets credited with coverage it does not
have.

### L3 - my reading, since it was asked for rather than dictated

**Nothing consumes `HARNESS_SHARDS`.** Measured: `grep -rlE '\$\{?HARNESS_SHARDS'
scripts/` returns ZERO, and the same selector for `$ROW_FLOOR` returns three
files, so the zero is not a broken path.

**My reading is that the checker should REFUSE a shard count nothing reads,
and it now does.** The reasoning, so it is overrulable:

1. With no consumer the harness still runs every row in one lane. `--min-rows
   5` against 10 live rows is then satisfied by the gate's own `-lt`, five rows
   are deletable, and nothing reds. That is the defect this file's docstring
   OPENS with, re-entered through the mechanism built to make sharding safe.
2. This file already refuses things that look like a floor and cannot breach -
   "0 is not a floor". A divisor nothing divides by is the same category.
3. It costs nothing today: no step declares a count, so it cannot red anything
   live.

**DERIVED, NOT FLAGGED, which is the part that matters.** The refusal is keyed
on whether anything expands the variable, so the splitter that reads it turns
this green in the same commit. Nobody has to remember to delete a guard - and
a guard that must be remembered is how #106 and #272 became standing rows.
Arms A46 (refuses), A47 (self-clears), A48 (the scan is not vacuous).

**Its bound, stated:** an expansion proves something READS the variable, not
that it splits rows correctly. Coverage of the split itself is the disjointness
check on #272, which no static reader can do. If you would rather ship the
multiplier unguarded, this is one `if` to delete and I will not re-argue it.

### L1, L2

L1: A35's in-code rationale claimed the dedent exit makes the job-level count
`readable`. Measured, that amputation leaves A35 PASSING and kills A41. The
comment now says so - the doc was already right, and the comment is what the
next amputator reads.

L2: five anchors were stricter than YAML and false-red legal syntax. ONE
`_strip_comment()` helper now serves three call sites, `key_indent` derives
from the first key line rather than `dash + 2`, and a bare `-` is admitted.
Arms A44, A45.

### The battery

    R4-M1 the direct-child bound      47/48  A43     prior env: key-indent bound  47/48  A37
    R4-M1 env_indent latch            47/48  A43     prior continuation fold      47/48  A39
    R4-L2 the comment stripper        46/48  A34,A44 prior flags assertion        47/48  A40
    R4-L2 key_indent from first key   47/48  A45     prior the multiplication     44/48  A21-A24
    R4-L3 the no-consumer refusal     47/48  A46     prior equality -> `>=`       45/48  A23,A24,A26
    R4-L3 the consumer file scan      47/48  A48
    R4-L3 the SHARD_USE pattern       47/48  A48

### THE NINTH WEAK ARM WAS A48, AND IT WAS THE ARM AGAINST VACUOUS ZEROS

My first A48 asserted `_shard_consumers() == []` plus a regex probe. Disabling
the file scan entirely left it **48/48 GREEN** - the assertion is satisfied by
the selector returning nothing *because it was switched off*. I wrote a vacuous
arm inside the arm whose whole job was to stop a vacuous zero.

It now PLANTS a real consumer under `scripts/`, asserts the scan sees it, and
removes it in a `finally` - the shape A6 has used since #187. That is the third
distinct form of this mistake in four rounds, and the through-line is the same
one round 3 named: **an assertion about an absence is only evidence if
something was present and then found.**

## 12. Merge

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only fix/270-exactness-shards

## 13. What I did NOT verify

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
