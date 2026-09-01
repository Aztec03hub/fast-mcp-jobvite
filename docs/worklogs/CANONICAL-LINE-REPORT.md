# Task #107 - one canonical result line, and the shape lists deleted

Agent `canonical-line`, branch `chore/canonical-line`, worktree
`/home/plafayette/claude_projects/fmj-worktrees/canonical-line`.
Brief: `docs/briefs/CANONICAL-LINE.md`. `docs/DESIGN.md` frozen at `aca9397`.
**Committed only. Not merged, not pushed.**

---

## 1. The lead's 24/20-versus-23/19: BOTH ARE RIGHT, and the gap is one deliberate exclusion

The dispatch asked whether `check-row-floor-controls.sh`'s comment - *"Enumerated over all 23
harnesses in the table ... 19 print `N/M ROWS - THE HARNESS LOST ROWS.`"* - had already gone stale
against a repository holding 24 such harnesses, 20 of that shape. **It has not.** The two numbers
count two different populations and both are accurate. Re-derived here, not inherited:

```
$ grep -lE '^[[:space:]]*ROW_FLOOR=[0-9]+[[:space:]]*$' scripts/*.sh | wc -l
24

$ docs/reviews/check-row-floor-controls.sh --list | wc -l
23

$ comm -23 <(scripts with a literal ROW_FLOOR, sorted) <(the table, sorted)
check-u15-gate-amputation.sh
```

Shape census, taken by reading the `echo` on the line directly under each floor comparison, over
all 24:

| shape | count |
|---|---|
| A `N/M ROWS - THE HARNESS LOST ROWS` (four different prefixes) | **20** |
| B `holds N rows, below its floor of M` | 3 |
| C `ONLY N ROWS RAN against a floor of M` | 1 |

`check-u15-gate-amputation.sh` carries shape A. Remove it and the table's population is 23 with 19
of shape A - exactly what the comment claims. **It is excluded from the table on purpose**, because
it has its own singular control: `docs/reviews/check-row-floor-control.sh:23` names it as its only
subject, and the plural file's header says so - *"plus `check-u15-gate-amputation.sh` in the
singular `check-row-floor-control.sh`"*.

So the hand-kept enumeration was NOT stale. **That does not make it safe**, and it is worth being
precise about why the suspicion was reasonable: the comment's numbers are correct today and there
is no mechanism that would make them go red when they stop being correct. The defect was never that
the count was wrong; it was that nothing could tell you when it became wrong. That is what §2
replaces.

---

## 2. The grammar I settled, and why `fired=` is not in it

    HARNESS-RESULT name=<basename> rows=<n> floor=<n> status=<ok|breach|refused>

Emitted from `scripts/lib/harness-result.sh`, which is the only place the format string exists.

**`fired=` is DROPPED.** The dispatch left the call to me; the reasoning, re-derived rather than
inherited from the previous pass:

1. **It would carry four incompatible meanings.** The tally in this family is
   `N/M controls fired.` (mutation controls), `RESULT: N killed, M not killed` (audit and client
   controls), `ROWS: N   ANCHORS APPLIED: M` (amputation harnesses) - and for the amputation
   harnesses the pass condition is INVERTED, survivors being the OUTPUT rather than a failure,
   which is the entire reason `ci-harness-gate.sh` has an `--amputation` flag.
2. **`ci-harness-gate.sh` argues the point itself**, about the exact phrases such a field would
   absorb: *"each is printed beside a different diagnosis, and collapsing them would send the next
   reader to the wrong place."* One field over four semantics is that collapse.
3. **`status` already carries the verdict**, and carries it from the harness's REAL exit code
   rather than from a counter a later refactor could leave stranded.
4. `rows`, `floor` and `status` are universal and each means exactly one thing.

The tally half of the defect is therefore **not** closed by this task, and it is filed as **task
#120** with the above reasoning and a suggested fix (semantically named per-diagnosis fields, which
the `key=value` grammar already tolerates), rather than smuggled in here - it moves `ci.yml` flag
semantics across ~20 steps and wants its own before/after ledger.

### `status`, derived rather than declared

| value | meaning | how it is produced |
|---|---|---|
| `refused` | the harness did not reach the end of its rows | **the default** - nothing has to remember to say it |
| `ok` | rows completed, exit 0 | computed from `$?` inside the EXIT trap |
| `breach` | rows completed, exit non-zero | computed from `$?` inside the EXIT trap |

`refused` being the default is the whole design. A script that dies in setup, refuses its
arguments, or is signalled never reaches `harness_result_ran`, so it says `refused` without
anyone wiring that path. **A silent harness and a passing one cannot render identically** - the
shape that let 119 consecutive CI failures go unread here.

`$?` is captured on `harness_result_emit`'s first line and returned on its last: captured first
because a `[` or a `basename` before it would overwrite the status the trap fired with, returned
last because in the 27 traps it is chained into it is followed by the harness's own cleanup, and a
cleanup that reads `$?` must see the script's status and not this function's. Both directions are
measured (C1-C8 below, and the `cleanup saw rc=7` arm of the bench probe).

### How it is armed, and the one thing that could silently disarm it

`bash has no trap stack.` The shared file arms `trap harness_result_emit EXIT` at source time so an
abort BEFORE the harness's own trap still reports; the harness's own `trap ... EXIT`, set later,
REPLACES it. So `harness_result_emit;` is also chained into the front of every existing EXIT trap
(27 of them, including the `trap - EXIT` disarm in `check-suite-floor-amputation.sh`, which becomes
`trap harness_result_emit EXIT`). Only one EXIT trap is ever live, so the line prints once;
`HR_EMITTED` guards that anyway rather than relying on the reasoning holding for the next editor.

**A trap added later that does not chain the emitter would disarm the line for that whole script,
and disarmed looks exactly like passing.** `docs/reviews/check-harness-result.sh` asserts
`traps == chained` per script for exactly that reason.

---

## 3. The container: 36 emitting, 36 existing, EQUAL

The population is the glob `scripts/*.sh`. There is no table, no allowlist, and **no partition into
"harness" and "not a harness"** - `ci-harness-gate.sh` is a gate rather than a harness and it emits
too, because a partition would be the same hand-kept list one level up. The `name=` field is what
disambiguates: a gate echoes the output of the harness it ran, so two lines appear and they differ
by `name=`. Every consumer selects on `name=`, never on position.

```
$ docs/reviews/check-harness-result.sh
scripts/*.sh (the container)     : 36
source scripts/lib/harness-result.sh : 36
every EXIT trap chains the emitter   : 36
call harness_result_ran              : 36
EQUAL: all 36 scripts in the container emit the canonical line.
EXIT=0
```

**Its negative control found two real defects in it, both of which would have made it green while
lying:**

- it matched `printf 'HARNESS-RESULT` in **its own prose**, reporting two copies of the format
  where there is one. The needle is now split across a concatenation, with the reason written
  beside it.
- it detected "sources the shared file" with `grep -qF 'lib/harness-result.sh'`, which **passed a
  script whose `.` line had been deleted**, because the `# shellcheck source=lib/harness-result.sh`
  directive three lines above carries the same substring. It now matches the source COMMAND.

Arm B, after the fix, on one script unwired:

```
source scripts/lib/harness-result.sh : 35
::error::these scripts do NOT source the shared result file ...
           check-u9-http-controls.sh
::error::the set that emits the line is NOT the set that exists.
ARM B EXIT=1
restored: byte-identical to the backup
```

### Where the numbers come from, per script

Every `harness_result_ran` call sits beside the harness's own counter, so `rows` and `floor` are
the values that harness compared - never a second copy typed into the migration:

| population | site | rows | floor |
|---|---|---|---|
| 24 with a literal `ROW_FLOOR` | the line above `if [ "$X" -lt "$ROW_FLOOR" ]` | `$TOTAL`/`$ROWS`/`$HELD`/`$total` | `$ROW_FLOOR` |
| `check-suite-floor.sh` | above its own floor comparison | `$passed` | `$floor` (its argument) |
| 5 floorless amputation harnesses | beside `ROWS: n   ANCHORS APPLIED: m` | `$ROWS` | `0` |
| `ci-harness-gate-controls.sh` | above its zero-row guard | `$TOTAL` | `0` |
| `ci-harness-gate.sh` | immediately after the harness it gates has run | `1` | `0` |
| 4 that had **no counter at all** | above their verdict | a counter added in their row function | `0` |

`floor=0` reads as absent: 0 is not a floor anything can breach.

**The last row is a change beyond pure reporting and is called out as such.**
`check-u1-boot-amputation.sh`, `check-u3-audit-amputation.sh`, `check-u4-client-amputation.sh` and
`check-u1-pid1-shutdown.sh` counted no rows at all, so their line could only ever have said
`rows=0` - and `rows=0` beside a green is precisely the shape a row floor exists to catch. Each
gained `HR_COUNTED_ROWS=$((HR_COUNTED_ROWS + 1))` at the TOP of its row function, so a row that
aborts on a missing anchor still counts as having run. It adds no output and no exit path; the
before/after ledger in §5 is what says so rather than this sentence.

---

## 4. The three controls the brief demanded, plus a fourth

### 4.1 `docs/reviews/check-harness-result-controls.sh` - 8/8, every row runs a real artifact

```
########## THE ABORT PATH - refused must not render as a pass
  FIRED  C1 a script that refuses its arguments reports refused
         HARNESS-RESULT name=check-suite-floor.sh rows=0 floor=0 status=refused   (exit 2)
  FIRED  C2 the gate with no harness named reports refused
         HARNESS-RESULT name=ci-harness-gate.sh rows=0 floor=0 status=refused   (exit 2)
  FIRED  C3 the gate pointed at a harness that does not exist reports refused
         HARNESS-RESULT name=ci-harness-gate.sh rows=0 floor=0 status=refused   (exit 2)

########## THE COMPLETING PATH - ok and breach carry the real numbers
  FIRED  C4 a floor met reports ok with the rows and floor it measured
         HARNESS-RESULT name=check-suite-floor.sh rows=900 floor=3 status=ok   (exit 0)
  FIRED  C5 a floor breached reports breach, and rows < floor is in the line
         HARNESS-RESULT name=check-suite-floor.sh rows=1 floor=5 status=breach   (exit 1)

########## THE INTERRUPTED PATH - a killed run must not read as a verdict
  FIRED  C6 a SIGTERMed script reports refused from the source-armed trap
         HARNESS-RESULT name=check-suite-floor.sh rows=0 floor=0 status=refused   (exit 124)
  FIRED  C7 a SIGTERMed harness reports refused from its OWN chained trap
         HARNESS-RESULT name=check-harness-anchors-controls.sh rows=0 floor=0 status=refused   (exit 124, budget 0.3s)

########## THE AMPUTATION - remove the report and the line must notice
  FIRED  C8 with its report amputated the line says refused at exit 0
         HARNESS-RESULT name=check-suite-floor.sh rows=0 floor=0 status=refused   (exit 0)
restored: byte-identical to the backup
restored: and identical to the commit

8/8 controls fired.
CONTROLS EXIT=0
```

C6 and C7 are separate claims on purpose: C6 exercises the trap the shared file arms, C7 exercises
a trap the harness itself set, which replaced it. Without C7, C6 is consistent with the emitter
being disarmed in all 27 scripts that set their own EXIT trap. **C8 is the row that stops C4 and C5
being vacuous:** without it, `status` is equally consistent with a value printf'd from the exit code
and meaning nothing. With `harness_result_ran` amputated the exit code stays 0 and the line changes
to `refused`, so the field tracks the harness rather than restating `$?`.

C6's interrupt is deterministic rather than a race against a timer: `check-suite-floor.sh` reads its
input with `cat`, so a producer that never writes and never closes blocks it indefinitely. C7 cannot
use that trick, so its budget starts below the harness's ~1s runtime and HALVES on a miss, and
"finished inside the budget" is reported as a BROKEN CONTROL rather than passed over.

Neither interrupted row touches `src/`: a mutation harness killed mid-row strands its mutation in
the working tree, measured here once when a killed `check-u9-http-amputation.sh` left every
bearer-token check on the HTTP transport disabled. The control re-reads `git status --porcelain`
after both rows and aborts if anything moved.

**The one thing SIGKILL cannot do**: `kill -9` runs no trap, so a SIGKILLed script prints no line at
all. That is not a silent pass - `ci-harness-gate.sh` already branches on `rc >= 128` and says the
run was killed, and the ABSENCE of a `HARNESS-RESULT` line is now itself detectable, which it was
not before. It is recorded as a limit of the mechanism rather than papered over.

### 4.2 `docs/reviews/probe-floor-checker-planted-defect.sh` - 4/4, and it watches the rewritten checker FAIL

A checker that has been rewritten and never watched fail is untested: it would pass identically if
its assertions had been deleted. Each arm plants a defect in the subject harness's canonical line
and requires the control to go red **for the stated reason**, not merely to be red.

```
########## PLANTED DEFECTS - the control must go red, for the right reason
  FIRED  P1 the harness's report is amputated, so the line says refused
           ::error::the harness reported status=refused, wanted breach.
  FIRED  P2 the harness reports a row count it did not measure
           deleted; it must report 8. The counter does not track
  FIRED  P3 the harness reports a floor its source does not declare
           are not the same value.
  FIRED  P4 the shared file is not sourced, so no line is printed at all
           ::error::the harness printed NO 'HARNESS-RESULT name=check-harness-anchors-controls.sh ...' line.

4/4 planted defects were caught.
restored: check-harness-anchors-controls.sh is identical to HEAD
PROBE EXIT=0
```

The plant is STAGED rather than committed: the control under test refuses a dirty subject, and
`git diff --quiet -- <file>` compares the working tree to the INDEX, so `git add` satisfies that
guard without writing history. The trap restores from HEAD on every exit path.

### 4.3 The rewritten `docs/reviews/check-row-floor-controls.sh`, pass arm

```
harness            : check-harness-anchors-controls.sh
floor (from source): 9
rows               : 9  (8 matched by the ERE + 1 inline)
rows to delete     : 1   (rows - floor + 1)
expected count     : 8   (must print as 8/9)
row invocations still matching: 7 (was 8, must be 7)
restored: byte-identical to the backup
restored: and identical to the commit
--- the harness's canonical result line ---
HARNESS-RESULT name=check-harness-anchors-controls.sh rows=8 floor=9 status=breach
exit with 1 row(s) deleted: 1 (must be 1)
CONTROL FIRED: check-harness-anchors-controls.sh loses 1 row(s), reported rows=8 floor=9 status=breach, exiting 1.
EXIT=0
```

**The shape lists are DELETED, not extended.** The display `grep -E` alternation and `floor_line()`
are both gone; residual prose literals in that file: **0**
(`grep -c "HARNESS LOST ROWS\|holds .* rows, below its floor\|ONLY .* ROWS RAN"` -> `0`). What
replaced them is strictly stronger than a shape match: it asserts `rows`, `floor` and `status`
SEPARATELY and reports each separately, where the old grep collapsed "the counter does not track
rows" and "the comparison never fired" into one message.

---

## 5. Before and after: INCOMPLETE, and the denominator is the point

**This section does not yet support the claim the task asks it to support, and it says so rather
than reporting the part that is finished as though it were the whole.**

    $ docs/reviews/compare-harness-exit-codes.sh <before> <after>
    harness                                    before    after
    ---------------------------------------------------------
    check-body-cap-amputation.sh               rc=0      rc=0
    check-body-cap-controls.sh                 rc=0      rc=0
    check-critical-coverage-amputation.sh      rc=0      rc=0
    check-harness-anchors-controls.sh          rc=0      rc=0
    check-log-redaction-amputation.sh          rc=0      rc=0
    check-suite-floor-amputation.sh            rc=0      rc=0
    check-suite-floor.sh                       rc=2      rc=2

    container (scripts/*.sh)          : 36
    COMPARED (measured on both sides) : 7 of 36
    exit codes that MOVED             : 0
    ::error::no exit code moved across the 7 compared, and that is NOT
             a statement about the other 29.
    COMPARE EXIT=1

**Nothing is known about the other 29.** The comparison step exits NON-ZERO on that incompleteness
by construction, so this cannot be mistaken for a result at a glance.

### The three instrument defects this measurement went through, all recorded in the probe

1. **My own edit dirtied the tree mid-pass.** I changed a tracked file in the worktree the baseline
   was running in, and `probe-harness-exit-codes.sh` correctly aborted with *"LEFT THE TREE DIRTY.
   Stopping: every later row would measure its mutation rather than its own subject."* The guard was
   right and I was wrong; the baseline now runs in its own detached worktree at the pre-migration
   commit, where nothing I do can reach it.
2. **Two background passes were killed from outside**, at row 7 of 36, losing the whole pass. The
   probe is now RESUMABLE - an existing ledger is appended to, not truncated - so a kill costs
   progress rather than the pass, and it takes its OWN deadline so an external bound never lands
   mid-harness. A mutation harness killed mid-row strands its mutation in the working tree; all
   three worktrees were verified clean after every kill.
3. **A timed-out row was being recorded as if it were an exit code.** `timeout` returns 124, which
   would have been written into a file whose entire purpose is to be compared against another run.
   Two runs with different budgets would then differ *on the budget*, and it would read as the
   refactor having moved a harness's exit code. Timeouts are now not recorded at all, so the row
   drops out of the comparison instead of poisoning it.

**Defect 3 was found by the orchestrator reviewing my `ps` output, not by me.** The guard already
existed when he raised it - which is why no 124 has ever entered either ledger, and why
`check-u0-test-controls.sh` is absent from BOTH sides rather than present on one - but the
underlying inconsistency was real: I had run the two sides at different per-script budgets (900 and
500) after lowering one to fit a foreground tool limit. **A before/after comparison whose two arms
use different instruments measures the instruments.** That it was caught downstream is luck of a
kind worth not relying on, so `compare-harness-exit-codes.sh` now refuses outright, exit 3, if a
timeout code ever appears in a ledger.

### Why the comparison is on the INTERSECTION and not a `diff`

`diff` answers "are these two files identical", which is not the question, and it reports every
legitimately-absent row (resumed pass, deadline, unrecorded timeout) as a difference - training the
reader to skim past real ones. The comparison therefore reports two claims that fail differently:
AGREEMENT over the harnesses measured on both sides, and COVERAGE of how much of the container that
intersection is. A perfect agreement over seven rows is not evidence about thirty-six.

---

## 6. Gates

TO BE FILLED IN

---

## 7. Findings, each with a suggested fix

TO BE FILLED IN

---

## 8. What I did NOT verify

TO BE FILLED IN
