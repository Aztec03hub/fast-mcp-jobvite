# MEASURED-284: fixed `/tmp` paths, the false kill they manufacture, and the one gate CI can hold

Branch `fix/284-fixed-tmp-paths`, cut from `main` at `99ebf05`. Written 2026-09-02.

## 1. The defect, and why no green run was ever going to find it

Every mutation harness here redirects pytest into a file and reads its verdict
back out of that file with `grep`. When the file has a **fixed name**, two
worktrees on one machine open the **same inode**. Both hold independent offsets,
so one run's `>` truncate lands under the other's writer and the kernel leaves a
NUL hole between the short write and the far-out one. GNU grep 3.11 then
classifies the file as **binary** - and binary is not an error:

* `grep -qE '^FAILED ...'` still **matches** and still **exits 0**, so the row
  records `killed by <test>` for a test this run never failed. #262 produced
  exactly that against a row whose killer had been neutered.
* `cap=$(grep -E '^FAILED ' "$OUT")` returns an **empty capture at exit 0**,
  with `binary file matches` on **stderr**, where no `2>&1` is looking.

**CI can never catch a regression of this class by running the harnesses.** The
runner has one checkout and no second worktree, so the collision cannot occur
there. That is why it survived, and it is why the deliverable is not only the
path change.

## 2. The population, re-derived at `99ebf05`

**The discriminator is not the string `/tmp`. It is a `/tmp` path whose text does
not vary per invocation** - no `mktemp`, no `XXXXXX` template, no `$$`, no
`$RANDOM` - on a non-comment line. That is what lets two runs collide.

The selector is now executable and committed, so the next reader re-runs it
rather than trusting a number:

    python3 docs/reviews/check-no-shared-tmp-paths.py

Its `offending_lines()` is the rule. Against `99ebf05` it reports:

| container | lines | files | distinct paths |
|---|---|---|---|
| tracked `.sh` (the gate's population) | 48 | 28 | 33 |
| widened to every executable file - `.sh`, `.py`, `.github/workflows/*` | 66 | 34 | 40 |

Both rows come from the **same** `offending_lines()`, so they are comparable.
The widened set adds six `.py`/workflow files to the 28 and drops none, which
is why the file counts read 28 and 34. To reproduce either at any revision -
this is the code that produced the table, not a paraphrase of it:

    import subprocess, importlib.util
    REV = "99ebf05"
    spec = importlib.util.spec_from_file_location(
        "g", "docs/reviews/check-no-shared-tmp-paths.py")
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    files = subprocess.run(["git", "ls-tree", "-r", "--name-only", REV],
                           capture_output=True, text=True,
                           check=True).stdout.split()

    def census(pred):
        lines, fs, paths = 0, set(), set()
        for f in files:
            if not pred(f):
                continue
            body = subprocess.run(["git", "show", REV + ":" + f],
                                  capture_output=True, text=True,
                                  check=True).stdout
            hits = g.offending_lines(body)
            if hits:
                fs.add(f)
            lines += len(hits)
            for _, line in hits:
                for m in g.TMP_PATH.finditer(line):
                    paths.add(m.group(0).rstrip('."\'}'))
        return lines, len(fs), len(paths)

    print("tracked .sh        :", census(lambda f: f.endswith(".sh")))
    print("widened .sh/.py/wf :", census(
        lambda f: f.endswith((".sh", ".py"))
        or f.startswith(".github/workflows/")))

### A rule keyed on the naming convention would have missed a third of it

Of the 33 distinct fixed paths in tracked `.sh` at `99ebf05`, **23** match
`/tmp/<uN|rN|probe...>-(mut|amp|base|sel|out).txt`. **Ten do not**, and **eight
of those ten are the identical defect under a different prefix**:

    /tmp/body-cap-amp.txt          /tmp/body-cap-mut.txt
    /tmp/critical-coverage-amp.txt /tmp/log-redaction-amp.txt
    /tmp/probe-252-rc4.txt         /tmp/probe-252-fake-fail.txt
    /tmp/prof240/arm1.txt          /tmp/prof240/arm2.txt

The remaining two are `/tmp/bash-work` and `/tmp/prof240/.coverage-ctx`, both
judged separately in §4. A regex keyed on `u[0-9]+` would have left eight
harness output files broken while reporting the class closed. **Select by shape,
never by name** - and that is what the committed gate does.

## 3. The collision, reproduced both ways

`docs/reviews/probe-284-shared-path-collision.sh`, seven rows, run before any
fix was applied:

    ARM A - the BEFORE shape: one path, two writers
      file is 4141 bytes and holds 4004 NUL bytes
      ROW 1 PASSED: the shared path holds NUL bytes - grep will call it binary
      verdict from the collided shared file: killed
      ROW 2 PASSED: THE FALSE KILL: the shared path reports a kill this run never made
      capture rc=0, capture length=0 bytes
      ROW 3 PASSED: the evidence capture is EMPTY at exit 0 - a match that prints nothing
      stderr: grep: .../one-shared-name.txt: binary file matches
      ROW 4 PASSED: grep announced the problem on STDERR, which no harness reads

    ARM B - the AFTER shape: mktemp, so the rival cannot reach it
      this run's file is 4141 bytes and holds 0 NUL bytes
      ROW 5 PASSED: the per-run path holds NO NUL bytes - the rival cannot reach this inode
      verdict from this run's own file: not-killed
      ROW 6 PASSED: the per-run path reports NOT-KILLED, which is the truth
      the same expression against a GENUINE failure in this run's file: killed
      ROW 7 PASSED: a real kill in this run's own file still reads as a kill

    HARNESS-RESULT name=probe-284-shared-path-collision.sh rows=7 floor=7 fired=7/7 status=ok

Three things about that probe are deliberate and are the difference between
evidence and decoration.

**The interleave is ordered, not raced.** #262's genuine rival gave 0 hits in
3 trials; a racing probe would measure a window, not a property. The question is
whether the shape admits the collision, not how often the dice land on it.

**Row 7 is a positive control.** Rows 5 and 6 would both pass for a verdict
expression that matched nothing - `not-killed` is the answer a broken regex gives
to every question - so a fix that merely blinded the grep would look identical
without it.

**The verdict expression is read out of `scripts/check-u4-client-controls.sh`,
not retyped.** The probe aborts if it cannot find it, rather than passing against
a stale copy.

One measurement inside the probe corrected itself. The first draft printed
grep's stderr with `2>&1 >/dev/null | sed`. That showed an **empty** stderr, and
would have been read as "grep said nothing" - grep sees `/dev/null` on stdout and
silently behaves like `-q`. Captured to a file instead, the message is there.
An instrument that answers "nothing" for a reason that has nothing to do with the
subject is the shape this repository keeps finding; it found it again here.

## 4. Per-site decisions

### 4a. Fixed - writers that could collide destructively (28 `.sh` files)

**Twenty-one harnesses of one shape.** `OUT=/tmp/<name>.txt` became
`OUT="$(mktemp /tmp/<name>-XXXXXX)"`, and `"$OUT"` was chained into the
**existing** `trap 'harness_result_emit; rm -rf ...' EXIT` rather than given a
second `trap`. Bash has no trap stack: a second `trap ... EXIT` **replaces**
`harness_result_emit` and an abort would render as silence. This is
`check-u3-audit-controls.sh`'s shape, copied, not reinvented:

    scripts/check-body-cap-amputation.sh        scripts/check-body-cap-controls.sh
    scripts/check-critical-coverage-amputation.sh
    scripts/check-log-redaction-amputation.sh
    scripts/check-u{5,6,7,8,9,10,12,14}-*-{amputation,controls}.sh

**`check-u3-audit-amputation.sh` and `check-u4-client-amputation.sh` had no EXIT
trap at all** - only the emitter the library arms at source time. Both got
`trap 'harness_result_emit; rm -f ...' EXIT`. This also closed a second, smaller
defect in `check-u4-client-amputation.sh`: its `COVDB="$(mktemp ...)"` was
created every run and deleted never.

**`check-u1-boot-controls.sh`** repeated `/tmp/u1-base.txt` three times; it now
writes `BASE_OUT` once and reads it in all three places. A repeated literal lets
the writer and its readers drift.

**`check-u4-client-controls.sh` was the worst site in the tree** - seven
occurrences of two literals, and no EXIT trap of its own. `$MUT_OUT` is the
dangerous one: line 161 reads a **verdict** out of it with
`grep -qE "^FAILED $SUITE::$want"`, which is precisely the expression a rival's
bytes satisfy. Both paths are now single variables cleaned by one chained trap.

**Probes.** `probe-252-rc4-verdict-trap.sh` (2 paths; the `mktemp` calls were
also moved *below* its four pre-flight `exit 3` paths, so an early refusal leaks
nothing). `probe-r4-unmutated-anchors.sh` (2 paths, 6 literals).
`probe-240-selected-row.sh` (the two files it **writes**; see 4c for the one it
reads).

**`probe-bash-namespace-amputation.sh:16` was deleted rather than randomised.**
It read `cd /tmp/bash-work 2>/dev/null || cd "$(git rev-parse --show-toplevel)"`
- scaffolding from the throwaway worktree the BASH standard was written in, which
`docs/worklogs/BASH-STANDARD-REPORT.md:476` records being removed. A stale or
unrelated `/tmp/bash-work` would silently win that `||` and run the probe
**against a different tree**, reporting a verdict about code nobody asked about.
A fixed path with no owner is not a temp file to rename; it is a line to cut.

### 4b. The tally that nothing checked

`probe-r4-unmutated-anchors.sh` printed `ROWS: 6 SURVIVED: 0` and asserted
neither number. Every early return in its `probe()` - anchor moved, mutation did
not land, row timed out - prints a line and returns **without a verdict**, and
`SURVIVED` stays 0. So all six rows could have failed to apply and the probe
would have printed `SURVIVED: 0` and exited 0: identical, to any reader and to
any caller, to six rows that were all correctly killed. That is the shape #262
measured, where a probe printed `killed=12/15` and still reported
`ARMS: 3/3 passed status=ok rc=0`.

It now counts `JUDGED` - rows that reached a verdict - and refuses when
`ROWS != 6` or `JUDGED != 6`. The new probe in §3 asserts its own tally the same
way, against a declared `ROW_COUNT` rather than a denominator free to shrink
until the ratio agrees with itself.

**On its first real run, that assertion found a control that had been dead for
months.** `probe-r4-unmutated-anchors.sh` R4-P6 anchors on
`annotations={"readOnlyHint": True},`. That string was unique when the row was
written and stopped being unique at `12e3c60`, which added `get_job_feed` with
the identical annotation. Since then the row has printed

    ANCHOR NOT UNIQUE (2 hits)
    COULD NOT APPLY - anchor moved

emitted no verdict, and the probe **still exited 0**. Run on this same tree, the
unmodified `99ebf05` version confirms it:

    ########## ROWS: 6   SURVIVED: 0
    TREE RESTORED - both files match the pristine pre-run copies.
    OLD-R4 rc=0

against the same tree under the new assertion:

    ########## ROWS: 6   JUDGED: 5   SURVIVED: 0
    ::error::TALLY SHORT - 6/6 rows entered, 5 reached a verdict.
    rc=1

**So the red is not a regression and it is not "pre-existing red" either - the
old shape was pre-existing GREEN over a missing row.** That is the whole
argument for asserting a tally: the defect was five months old and every run of
this probe had reported success. The anchor is fixed in the same commit, by
carrying its preceding comment line, which is unique. With the row running:

    ########## R4-P6 the read-only annotation is inverted
      *** SURVIVED *** ====== 889 passed, 6 deselected in 55.57s ======
    ########## ROWS: 6   JUDGED: 6   SURVIVED: 1
    rc=0

**The recovered row SURVIVES, and that is the documented answer, not a new
bug.** `src/fast_mcp_jobvite/tools/jobs.py:355-358` already states that
`readOnlyHint` is *"Advisory only (DESIGN.md:270-274) ... never counted as a
control"*. The probe reports survivors rather than gating on them, so it exits
0. What was wrong for five months was that nobody could tell this answer from
a row that never ran.

One more consequence, worth stating because the old code's comment names the
hazard and could not act on it: `probe()` refuses a row that TIMED OUT
(`rc == 124`) *before* `JUDGED` is incremented. A hang used to score as this
probe's good outcome - `rc != 0` means KILLED - and be invisible. It now makes
the tally short and turns the probe red.

Both assertions were also proved by planting a wrong tally; see §6.

### 4c. Excluded, with the reason

**`.github/workflows/ci.yml` and `mirror.yml`** - `/tmp/actionlint.tgz`,
`/tmp/actionlint`, `/tmp/mirror-canonical.txt`, `/tmp/mirror-copy.txt`. These run
on a GitHub runner: a fresh VM per job, one job's filesystem, no second worktree.
The concurrency this defect needs does not exist there. Excluded **structurally**
- the gate's population is `*.sh` - so a new workflow needs no maintenance in a
register.

**`docs/reviews/probe-240-selected-row.sh:36`,
`DATA="${DATA:-/tmp/prof240/.coverage-ctx}"`** - an **input this script does not
write**, and half of a two-command contract: the coverage database is produced by
the `COVERAGE_FILE=/tmp/prof240/.coverage-ctx ... pytest --cov-context` run that
`scripts/coverage-test-map.py` documents, and consumed here. **A path two
commands use to find each other cannot be randomised on one side only**, and
randomising a *reader* fixes nothing - a reader cannot collide with a reader. It
is already overridable per run (`DATA=... probe-240-selected-row.sh`), which is
the escape a concurrent operator actually needs. Registered in the gate's
`DELIBERATE` dict **with this reason**, so a green names it rather than hiding it.

**`scripts/coverage-test-map.py:42,46`** - the other end of that same contract,
in a docstring showing the command to run. Prose, not an executable line.

**`docs/reviews/check-checkers-are-wired.py:1746`,
`python3 -m cProfile -o /tmp/prof.out {needs}`** - a command **string** in a
self-test table, fed to this checker's own parser and **never executed**. Inert
text.

**`docs/reviews/check-checkers-are-wired.py:405` and
`docs/reviews/check-standards-citations.py:51`** - prose inside a register entry
and an error message.

**`docs/reviews/b49b/apply-short-summaries.py:2`** - a docstring. **The brief
asked about an unexplained trailing dot in `/tmp/summaries.tsv.`** It is a
sentence-ending full stop:

    """Apply the hand-authored short summaries from /tmp/summaries.tsv.

`/tmp/summaries.tsv` and `/tmp/summaries.tsv.` are not two paths. They are one
docstring plus one prose mention of the same file in
`check-checkers-are-wired.py:405`, which records that it "no longer exists".

## 5. The durable half: the one question CI *can* ask

The path changes close today's instances. They do nothing about the next
`OUT=/tmp/u16-mut.txt`, and no harness run on the runner will ever object to it.
So `docs/reviews/check-no-shared-tmp-paths.py` is wired in `ci.yml`, as two
steps (`--self-test` **separate**, not chained with `&&` - the job does not run
under errexit and a chained self-test failure would be invisible).

It keys on the shape, refuses an empty population with exit 2, and carries a
`DELIBERATE` register in which **a bare name is refused: the reason is the
exemption**, the shape `check-no-errexit.py` and `check-checkers-are-wired.py`
already use.

Its positive control is on real data rather than on strings this sweep wrote:
replayed against `99ebf05` via `git show`, the gate reports **48 fixed paths
across 28 tracked `.sh`**; against this branch it reports **one**, and that one
prints its reason. Its `--self-test` holds 10 controls: three lines that must
FIRE, **five that must stay SILENT** - `mktemp`, an `XXXXXX` template, a `$$`
name, a rationale comment naming `/tmp`, a path that is not under `/tmp` - and
two structural ones, that `git ls-files` is non-empty and that a planted path in
a file read from DISK fires end to end. The silent five are the load-bearing
half: every firing row alone would pass for a detector that returned true for
any line containing `/tmp`.

`probe-284-shared-path-collision.sh` is registered **unwired by decision**: both
its arms assert properties of the kernel and of GNU grep against files in its own
`mktemp`'d directory, so a green says nothing about this repository and it could
not go red for a defect here. Inert as a gate - the same ruling
`probe-243-forced-exit-window.py` carries. The gate for the class is the checker;
the probe is the evidence the rule is about a real failure and not a style
preference.

## 6. Planting a wrong tally

Each assertion added was driven to fire, on a copy, with a non-zero exit that
**names the count**.

`probe-284-shared-path-collision.sh`, one row deleted:

    ########## ROWS: 6/6 passed
    ::error::ROW COUNT MOVED - 6 rows ran against 7 declared.
    HARNESS-RESULT name=.plant-284.sh rows=6 floor=7 fired=6/6 status=breach
    exit=1

The same probe with one row's expected answer inverted:

    ########## ROWS: 6/7 passed
    HARNESS-RESULT name=.plant-284.sh rows=7 floor=7 fired=6/7 status=breach
    exit=1

Note the first plant: `6/6 passed` is what the old shape would have printed and
exited 0 on. The denominator moved with the numerator, and only the declared
`ROW_COUNT` noticed.

## 7. What in the brief was wrong

The brief's figures were taken at `d314283` and carried these caveats itself.
Measured at `99ebf05`:

* **"39 distinct fixed paths across 34 files, 34 of them written."** The widened
  census is **40 distinct across 34 files (66 lines)**; restricted to tracked
  `.sh`, where every writer actually lives, **33 distinct across 28 files (48
  lines)**. The file count is a coincidence, not the same 34 files.
* **"26 of 39 match the convention; thirteen do not, and six of those are the
  same defect under a different prefix."** In the `.sh` population: **23 of 33
  match, ten do not, and eight of those ten are the same defect** - the brief's
  six, plus `/tmp/prof240/arm1.txt` and `arm2.txt`. The brief's point holds and
  is stronger than it claimed.
* **"`/tmp/summaries.tsv` and `/tmp/summaries.tsv.` - that trailing dot is
  unexplained."** Explained in §4c: a full stop ending a docstring sentence. One
  file, not two paths, and it no longer exists.
* **"`/tmp/prof240` (8 hits)."** At `99ebf05`, **6 in
  `probe-240-selected-row.sh` and 2 in `scripts/coverage-test-map.py`** - 8, but
  split across a script and a docstring, which is what decides them differently.
* **`/tmp/bash-work`, `/tmp/evolv-coder-standards`, `/tmp/prof.out`** were listed
  as "needing a decision rather than a rewrite". Correct, and all three landed on
  a different answer from each other: deleted, prose, inert string.

## 8. Every harness run end to end

Sequentially, never concurrently - a harness owns the tree while it runs.
`git status --porcelain -- src tests` was 0 rows after **every** one.

    scripts/check-body-cap-amputation.sh           rc=0    26s  HARNESS-RESULT name=check-body-cap-amputation.sh rows=5 floor=5 status=ok
    scripts/check-body-cap-controls.sh             rc=0    23s  HARNESS-RESULT name=check-body-cap-controls.sh rows=12 floor=12 fired=12/12 status=ok
    scripts/check-critical-coverage-amputation.sh  rc=0    80s  HARNESS-RESULT name=check-critical-coverage-amputation.sh rows=20 floor=20 applied=20/20 status=ok
    scripts/check-log-redaction-amputation.sh      rc=0     3s  HARNESS-RESULT name=check-log-redaction-amputation.sh rows=6 floor=6 applied=6/6 status=ok
    scripts/check-u1-boot-controls.sh              rc=0   117s  HARNESS-RESULT name=check-u1-boot-controls.sh rows=23 floor=23 fired=23/23 status=ok
    scripts/check-u3-audit-amputation.sh           rc=0   116s  HARNESS-RESULT name=check-u3-audit-amputation.sh rows=10 floor=0 applied=10/10 status=ok
    scripts/check-u4-client-amputation.sh          rc=0    83s  HARNESS-RESULT name=check-u4-client-amputation.sh rows=17 floor=0 applied=17/17 status=ok
    scripts/check-u4-client-controls.sh            rc=0    36s  HARNESS-RESULT name=check-u4-client-controls.sh rows=19 floor=19 killed=19/19 status=ok
    scripts/check-u5-jobs-amputation.sh            rc=0    26s  HARNESS-RESULT name=check-u5-jobs-amputation.sh rows=14 floor=14 applied=14/14 status=ok
    scripts/check-u5-jobs-controls.sh              rc=0    22s  HARNESS-RESULT name=check-u5-jobs-controls.sh rows=16 floor=16 fired=16/16 status=ok
    scripts/check-u6-paging-amputation.sh          rc=0     4s  HARNESS-RESULT name=check-u6-paging-amputation.sh rows=11 floor=11 applied=11/11 status=ok
    scripts/check-u6-paging-controls.sh            rc=0    14s  HARNESS-RESULT name=check-u6-paging-controls.sh rows=16 floor=16 fired=16/16 status=ok
    scripts/check-u7-resilience-amputation.sh      rc=0    69s  HARNESS-RESULT name=check-u7-resilience-amputation.sh rows=22 floor=0 applied=22/22 status=ok
    scripts/check-u7-resilience-controls.sh        rc=0    17s  HARNESS-RESULT name=check-u7-resilience-controls.sh rows=31 floor=31 fired=31/31 status=ok
    scripts/check-u8-candidates-amputation.sh      rc=0    28s  HARNESS-RESULT name=check-u8-candidates-amputation.sh rows=14 floor=14 applied=14/14 status=ok
    scripts/check-u8-candidates-controls.sh        rc=0    33s  HARNESS-RESULT name=check-u8-candidates-controls.sh rows=25 floor=25 fired=25/25 status=ok
    scripts/check-u9-http-amputation.sh            rc=0   131s  HARNESS-RESULT name=check-u9-http-amputation.sh rows=14 floor=0 applied=14/14 status=ok
    scripts/check-u9-http-controls.sh              rc=0    25s  HARNESS-RESULT name=check-u9-http-controls.sh rows=14 floor=14 fired=14/14 status=ok
    scripts/check-u10-write-amputation.sh          rc=0    22s  HARNESS-RESULT name=check-u10-write-amputation.sh rows=10 floor=0 applied=10/10 status=ok
    scripts/check-u10-write-controls.sh            rc=0    25s  HARNESS-RESULT name=check-u10-write-controls.sh rows=21 floor=21 fired=21/21 status=ok
    scripts/check-u12-jobfeed-amputation.sh        rc=0    20s  HARNESS-RESULT name=check-u12-jobfeed-amputation.sh rows=10 floor=0 applied=10/10 status=ok
    scripts/check-u12-jobfeed-controls.sh          rc=0    26s  HARNESS-RESULT name=check-u12-jobfeed-controls.sh rows=17 floor=17 fired=17/17 status=ok
    scripts/check-u14-arguments-amputation.sh      rc=0    18s  HARNESS-RESULT name=check-u14-arguments-amputation.sh rows=16 floor=0 applied=16/16 status=ok
    scripts/check-u14-arguments-controls.sh        rc=0    23s  HARNESS-RESULT name=check-u14-arguments-controls.sh rows=20 floor=20 fired=20/20 status=ok
    docs/reviews/probe-284-shared-path-collision.sh rc=0    1s  HARNESS-RESULT name=probe-284-shared-path-collision.sh rows=7 floor=7 fired=7/7 status=ok
    docs/reviews/probe-252-rc4-verdict-trap.sh     rc=0    -    HARNESS-RESULT name=probe-252-rc4-verdict-trap.sh rows=7 floor=7 fired=7/7 status=ok
    docs/reviews/probe-bash-namespace-amputation.sh rc=0    -   CONTROL FIRED (no HARNESS-RESULT: it does not source the emitter)
    docs/reviews/probe-240-selected-row.sh         rc=0    21s  VERDICT: the covering set HOLDS U9 row A1 (no HARNESS-RESULT line)
    docs/reviews/probe-r4-unmutated-anchors.sh     rc=0   430s  ROWS: 6  JUDGED: 6  SURVIVED: 1 (no HARNESS-RESULT line)

`probe-r4-unmutated-anchors.sh` is listed at its FIXED-anchor run. Its first run
on this branch exited **1** with `JUDGED: 5`; §4b is that story.

Gates, all after the harness runs and none concurrent with one:

* `shellcheck -x -P docs/reviews:scripts --severity=warning` over all 29 changed
  `.sh`: **rc=0**. `bash -n` on each: clean.
* `ruff check` and `ruff format --check` on the new checker: clean.
* `actionlint` with `SHELLCHECK_OPTS=--severity=warning`: **rc=0**.
* Every `check-*.py` under `docs/reviews/` and `scripts/`: **0 red**, excluding
  four that refuse on this machine for environment reasons. **All four are
  byte-identical to `99ebf05` on this branch** (`git diff --cached` names none
  of them), so their refusal cannot be attributed to it - `check-coverage-floors.py` (no
  `coverage.json`), `check-merge-invented.py` (needs a range argument),
  `check-review-coverage.py` (belongs on pull requests), and
  `check-secrets-baseline.py` (`detect-secrets` not importable).
* `check-row-floor-exactness.py`: 35 harnesses, 8 carrying both floors, 16
  compared to a live count - **identical to `99ebf05`**.
* `check-row-floors.py`: 33 harnesses, 0 unreferenced, 0 unfloored - **identical
  to `99ebf05`**.
* `check-checkers-are-wired.py`: rc=0, `--self-test` 53/53. Its two counters
  moved exactly as intended - `run:` steps 105 -> 107 (the two new `ci.yml`
  steps), unwired-with-a-reason 76 -> 77 (`probe-284-shared-path-collision.sh`).
