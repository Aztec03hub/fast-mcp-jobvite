# ROW-FLOORS - ten derived floors, one red CI step, one killed harness

Task #79. Branch `chore/row-floors`, based at `20e71ed`. Eleven commits, `7d3800c..1994c3b`.
Not merged, not pushed.

`docs/reviews/check-row-floors.py` now reports **0 of 28 harnesses floorless** and exits 0.

## 1. The table

Every floor below was read out of a run of that harness. Nothing was copied from a task record, a
worklog, this project's other reports, or the brief - several of which carry numbers that are right,
and one of which (#49, "22/22") is stale for a harness in this set.

| Harness | Rows | Floor | The line the count was read from |
|---|---|---|---|
| `check-harness-anchors-controls.sh` | 9 | `ROW_FLOOR=9` | `9/9 controls fired.` |
| `check-suite-floor-amputation.sh` | 4 | `ROW_FLOOR=4` | `4/4 amputations killed a test.` |
| `check-u0-test-controls.sh` | 11 | `ROW_FLOOR=11` | `11/11 controls fired.` (and `10/11` before the fix in §2) |
| `check-u1-boot-controls.sh` | 23 | `ROW_FLOOR=23` | `23/23 controls fired.` |
| `check-u11-advisory-controls.sh` | 15 | `ROW_FLOOR=15` | `15/15 controls fired.` |
| `check-u15-gate-amputation.sh` | 5 | `ROW_FLOOR=5` | had NO tally - see §4 |
| `check-u15-gate-controls.sh` | 15 | `ROW_FLOOR=15` | `15/15 controls fired.` |
| `check-u3-audit-controls.sh` | 15 | `ROW_FLOOR=15` | `########## RESULT: 15 killed, 0 not killed` |
| `check-u4-client-controls.sh` | 19 | `ROW_FLOOR=19` | `########## RESULT: 19 killed, 0 not killed` |
| `check-u7-resilience-controls.sh` | 26 | `ROW_FLOOR=26` | `26/26 controls fired.` |

All ten use the internal `ROW_FLOOR` form, per the brief's steer away from `--min-rows`. **No
`--min-rows` was added to `ci.yml` and `ci.yml` is untouched on this branch.** The tally-prefix trap
R7 recorded would have bitten at least four of these: `check-harness-anchors-controls.sh`,
`check-u0-test-controls.sh`, `check-u1-boot-controls.sh` and `check-u11-advisory-controls.sh` all
print a bare `N/M controls fired.` with no `##########` prefix, so a `--row-re '^########## '`
would have matched zero rows in each.

### Three places the number was NOT what a careful reader would have typed

- **`check-u4-client-controls.sh` is 19, and its labels run `M01..M17`.** Deriving from the highest
  M-number gives 17 - a floor two rows below the truth, which passes the checker and looks done.
  `M12` carries an `M12b` and an `M12c` beside it. Confirmed independently with
  `grep -c '^run_mutation ' scripts/check-u4-client-controls.sh` -> 19.
- **`check-u7-resilience-controls.sh` is 26, and `check-harness-anchors.py` prints
  `check-u7-resilience-controls.sh anchors= 26` for it.** Those two agreeing is a coincidence of this
  one file: the anchor table counts ANCHORS, not rows, and for `check-u3-audit-controls.sh` it says
  15 anchors against 15 rows while for `check-u1-boot-controls.sh` it says 23 against 23 and for
  `check-u11-advisory-controls.sh` 15 against 15. The table is not a row count and must not be used
  as one, however often it happens to match.
- **Task #49 records "22/22" for `check-u7-resilience-controls.sh`.** It now measures 26. That record
  is not wrong, it is old - which is exactly why the brief forbids copying one.

## 2. FINDING (High) - `check-u0-test-controls.sh` is RED on `main`, and has been

This is not a floor problem. It was found because a floor cannot be derived from a harness that
will not go green.

The first run printed `10/11 controls fired.` and exited 1. The failing row:

```
--- CONTROL point FIXTURES_DIR at a path that does not exist
    exit=1 but 'test_fixtures_directory_resolves' was NOT the failing test -> WRONG TEST FIRED
      FAILED tests/test_approval_write.py::...
      ... 85 more ...
      FAILED tests/test_fixture_path.py::test_fixtures_directory_resolves - Asserti...
```

The verdict and the evidence contradicting it are printed three lines apart, out of the same
variable. `test_fixtures_directory_resolves` IS in `$out`; the check on `$out` said it was not.

**Mechanism**, from a positive control rather than from reading:

```
$ bash -c 'set -uo pipefail
    huge=$(printf "NEEDLE_AT_START\n"; seq 1 200000)
    printf "%s\n" "$huge" | grep -q "NEEDLE_AT_START"; echo "early-match rc=$?"
    small=$(printf "NEEDLE_AT_START\nx\n")
    printf "%s\n" "$small" | grep -q "NEEDLE_AT_START"; echo "small       rc=$?"'
early-match rc=141
small       rc=0
```

`grep -q` exits the instant it matches. The writer, still writing, takes SIGPIPE, and `pipefail`
(line 26 of that file) promotes 141 to the pipeline's status. The pipeline reports NOT FOUND for a
string that is present - **but only when the output is large**. Ten of the eleven rows break one or
two tests, so their output fits the pipe buffer and they match normally. The FIXTURES_DIR row breaks
~87, and it is the only row that fails. **This step goes red as a function of how much the suite has
grown**, which is why it can have been fine when written.

**Fixed** at `73269fe`, in the one file I had to run: `[[ "$out" == *"$expect"* ]]`. A bash
substring test starts no second process and cannot SIGPIPE. `11/11 controls fired.`, exit 0.

### FINDING (High, NOT FIXED) - fifteen sibling sites, five in shell, ten in `ci.yml`

Filed as task **#85**. All four shell files carry `set -uo pipefail`:

```
scripts/ci-harness-gate.sh:153   if printf '%s\n' "$out" | grep -qF -- "$phrase"
scripts/ci-harness-gate.sh:161   if printf '%s\n' "$out" | grep -q 'TIMED OUT'
scripts/ci-harness-gate.sh:235   if ! printf '%s\n' "$out" | grep -qE -- "$re"
scripts/check-suite-floor-amputation.sh:59   if printf '%s\n' "$out" | grep -q "failed"
scripts/check-u1-boot-amputation.sh:117      if printf '%s\n' "$survivors" | grep -Fxq -- "$t"
```

and ten more inside `ci.yml` itself, which I did not edit:

```
.github/workflows/ci.yml:231 262 287 317 320 323 345 367 379 381
```

`ci-harness-gate.sh` is the wrapper **all 13 harness steps** run through, and its exposure runs both
ways. Line 235's `!` turns a 141 into a gate FAILURE - loud, fails closed, survivable. Line 161's
`grep -q 'TIMED OUT'` turns a 141 into "no timeout was found", which **fails OPEN on exactly the run
whose output is longest**, which is the run most likely to have timed out. The `ci.yml` sites are the
`|| { echo "::error::..."; exit 1; }` shape, so they fail closed and would read as a mystery red.

**Suggested fix, one line per site.** `[[ "$out" == *"$phrase"* ]]` for the fixed-string sites,
`[[ "$out" =~ $re ]]` for the regex ones. Where a pipeline must stay, `grep -c ... >/dev/null` reads
to EOF and cannot SIGPIPE - but the builtin is smaller and has no second process at all. **Each site
needs its own positive control**: the fix is only proved by a case whose output is large enough to
have failed before, and a small-output case passes either way.

**Why I did not fix them here.** Seven harnesses were still to run and they all run through
`ci-harness-gate.sh`. Editing the wrapper mid-flight would have meant every subsequent measurement
was taken against a tree I had just changed underneath it.

## 3. FINDING (Medium) - two of my own floors were invisible to the checker that demanded them

After nine commits, `check-row-floors.py` still reported two harnesses as `NO FLOOR` -
`check-suite-floor-amputation.sh` and `check-u15-gate-amputation.sh` - **both of which had floors I
had just written**. The checker matches:

```python
FLOOR = re.compile(r"^\s*ROW_FLOOR=(\d+)\s*$", re.M)
```

Mine were `row_floor=4` (lowercase, matching that file's own local style) and
`ROW_FLOOR=5   # DERIVED - see...` (a trailing comment). Both are floors; neither is visible to the
instrument. This is the same shape as U14's row that bash executed and `check-harness-anchors.py`
could not parse, and the same shape as the defect the floors themselves exist to catch: **a floor
nobody can see is a floor nobody is checking.**

Both are now in the exact form the checker reads, with the reason written beside the assignment in
`check-u15-gate-amputation.sh` so the next person does not re-add a comment there.

**I am not proposing widening the regex.** A strict pattern that a writer must match is better than a
loose one that quietly accepts four spellings, *provided the failure is loud* - and here it was: the
checker said NO FLOOR and exited 1. It worked. It is worth knowing that it will say NO FLOOR rather
than MALFORMED FLOOR, so the message points at the wrong repair. **Suggested fix, if you want one:**
have the checker also match `^\s*ROW_FLOOR=` case-insensitively with anything after it, and report
those as `FLOOR NOT IN THE CHECKED FORM` rather than `NO FLOOR`. One extra regex, and it names the
actual repair.

## 4. `check-u15-gate-amputation.sh` had no row count at all

The other nine harnesses tally their rows. This one deliberately does not fail on survivors -
survivors are its output - and it had **no counter, no tally line, and nothing a floor could compare
against**. Delete four of its five rows and it printed the same closing sentence and exited 0. It
could not lose rows loudly because it never counted them.

So it got a counter first (`ROWS`, incremented in `report()`), then the floor. **The counter does not
change what a survivor means.** A survivor still does not fail the run. Only a missing row does.

Derived in two steps, since there was no tally line to read: the run before the change printed five
row headers, counted with `grep -cE '^########## [A-E]\.'` over its output; the run after prints
`########## 5/5 ROWS` itself.

## 5. The floors are proved able to fire, not just typed

Ten derived numbers, and until this point not one had been watched fail. A derived count establishes
that the number is right and says nothing about whether the comparison works - it could be inverted,
the variable could be misspelled under `set -u`, the exit could be swallowed by the next line.

`docs/reviews/check-row-floor-control.sh` (committed, `1994c3b`) deletes a real row from
`check-u15-gate-amputation.sh` and reads that harness's own exit code:

```
anchor occurrences: 1 (must be exactly 1)
deletion landed: 1 line(s) removed
########## 4/5 ROWS
::error::4/5 ROWS - THE HARNESS LOST ROWS.
exit with a deleted row: 1 (must be 1)
restored: byte-identical to the backup
restored: and identical to the commit
CONTROL FIRED: a deleted row is caught by the floor and exits 1.
```

That harness is the right subject precisely because it does not fail on survivors: exit 1 there can
only mean the floor fired.

It asserts its anchor is unique and present before deleting (an already-renamed row would delete
nothing and pass for the wrong reason), restores by `cmp` against a backup rather than by re-editing
(a `sed` matching nothing succeeds silently), and **takes the backup before arming the restore trap**
- armed first, an abort on the cleanliness check would have fired the trap and copied the empty file
`mktemp` had just made over the harness. That last one was caught by reading, before the script ever
ran.

It is **not wired into `ci.yml`**: it edits a tracked file and refuses to run when that file is
dirty, which is not something a CI step should depend on.

**This control covers ONE of the ten floors.** See §8.

## 6. A killed harness left its mutation in my tree, twice

The background runner killed `check-u3-audit-controls.sh` mid-row on two consecutive attempts. Both
times the tree was left carrying M7's mutation:

```
-    # AuditPhase.READ: log to stderr and continue. A read is recoverable
-    # and losing the tool is worse than losing one audit line.
-    return []
+    return ["audit write failed"]
```

Caught by `git status` before anything else ran, restored with `git restore`, and the third attempt
was launched under `setsid` so a process-group kill could not reach it. Every harness after that one
was launched the same way and none was killed again.

Worth stating plainly because of what nearly happened: had I run the suite, committed, or started the
next harness in that window, the result would have been a measurement of the harness rather than of
the code, and the mutation would have entered a commit looking like an ordinary edit. Task **#89**
covers making the gate notice a stranded mutation after an interruption; today it is silent.

## 7. The wiring you asked for - `ci.yml` lines

`ci.yml` is yours; I have not touched it. `check-row-floors.py` is green (0 backlog, exit 0), so it
can be wired now. In the `design-gates` job, matching the shape of the steps already there:

```yaml
      - name: Every harness declares a row floor
        run: |
          set -uo pipefail
          out=$(python3 docs/reviews/check-row-floors.py 2>&1); rc=$?
          echo "$out"
          [ "$rc" -eq 0 ] || { echo "::error::a harness has no row floor at either layer - a"
                               echo "         floorless harness reports fully green with all but"
                               echo "         one row deleted, because FIRED -ne TOTAL is 0 == 0"
                               exit 1; }
          case "$out" in
            *"wired but no floor at either layer: 0"*) ;;
            *) echo "::error::the checker exited 0 without reporting a zero backlog; a"
               echo "         green whose sentence is missing is a green nobody read"
               exit 1;;
          esac
```

**The `case`, not `grep -q`.** The other steps in that job use
`printf '%s\n' "$out" | grep -q '...' || { ... }`, and §2 is the reason I did not copy it: under
`pipefail` that pipeline returns 141 on a match when the output is long, and this checker's output
grows by one line per harness. `case` is a bash builtin, needs no second process, and cannot SIGPIPE.
Those ten existing sites are task #85 and are not for me to change.

**No other `ci.yml` change is needed.** All ten floors are internal `ROW_FLOOR`, so no `--min-rows`
is involved, and no `--row-re` had to be checked against a harness's real output.

## 8. What I could NOT settle

- **Nine of the ten floors have never been watched fire.** §5 proves the mechanism on
  `check-u15-gate-amputation.sh` only. The other nine use the same shape, but "the same shape" is an
  argument, not a measurement, and this branch exists because arguments about floors have been wrong
  four times. Extending the control to the other nine is ~20 minutes of runtime each because each
  needs a full harness run per arm; I did not have a way to make that cheap. **A cheaper design that
  would settle it:** run each harness once with `ROW_FLOOR` overridden upward via an environment
  variable rather than by deleting a row - one run each, no tree mutation - which would need each
  harness to read `ROW_FLOOR="${ROW_FLOOR:-<n>}"`. That is a real change to ten files and I did not
  want to make it in the same branch that sets the numbers.
- **Whether `check-u0-test-controls.sh` is currently red on `main`, or only in my worktree.** I
  measured it at `20e71ed` in `/tmp/row-floors-work` and it failed; I did not check a CI run to
  confirm the same step is red on `main` today, and I cannot rule out something environmental about
  this machine making the output larger than a runner's. The mechanism is not in doubt - the positive
  control in §2 is independent of this repo - but "CI is red right now" is a claim about a CI run I
  did not read.
- **How long the ten `ci.yml` `grep -q` sites have been exposed, and whether any has already
  misfired.** Each depends on the size of one step's output, which I did not measure per step. Line
  161's fail-open case in `ci-harness-gate.sh` is the one worth measuring first.
- **Why the background runner killed two u3 runs and nothing else.** `setsid` made the symptom go
  away, which is a workaround, not a diagnosis. If other agents on this repo are losing harness runs
  the same way, the stranded-mutation risk in §6 is theirs too.

## 9. Housekeeping

- Gate run in full **before** folding, every step judged by its own exit code:
  `uv lock --check`, `ruff check`, `ruff format --check`, `mypy`, `check-quickstart`,
  `check-harness-anchors --self-check --floor 401`, `check-committed-file-types --all`,
  `check_advisories`, `check-coupling`, `check-cross-references`, `check-coupling-controls`,
  `check-coupling-sweep`, `check-obligations`, `check-obligations --controls`,
  `check-plan-measurements`, `check-resweep-verdicts`, `check-row-floors` - **17 of 17 exit 0**.
- `768 passed, 6 deselected in 46.08s`, exit 0, **0 skips**. Identical to the baseline at `20e71ed`,
  which is what the brief required: this branch edits harnesses, not tests, so the suite count must
  not move, and it did not.
- Anchor floor holds at **401**, re-checked after every one of the eleven commits.
- Both floors read from `ci.yml` by grep, never retyped: suite floor `768`, anchor floor `401`.
- `docs/OBLIGATIONS.md` not touched, so no anchors moved and no repoint was needed.
- Not merged, not pushed, `ci.yml` not edited.
- **Worktree `/tmp/row-floors-work` NOT removed** - it holds the eleven commits and nothing is
  pushed, so removing it would strand them. Remove it after you have merged the branch.
