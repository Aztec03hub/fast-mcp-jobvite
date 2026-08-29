# HARNESS-INTEGRITY - task #20

Agent: `harness-integrity`. Branch: `fix/harness-integrity`. Base SHA: `667db50`, **rebased onto
`main` at `0291bac`** - see "The rebase, and what it caught" near the end; the numbers in Item 1's
two survivor tables are from `667db50` and `1e04ae3`, which is where the question was asked.
Worktrees: `/tmp/harness-work` (667db50, my branch), `/tmp/harness-base` (`1e04ae3`, the commit
before `c7809f6`), `/tmp/harness-pid1` (667db50, controls only, never committed from).
Nothing was checked out in the shared checkout.

**Headline.** Item 1's survivor is **pre-existing, and it is not a defect in the test.** The
measurement says so directly, and the belief the brief flagged as unproved is confirmed rather than
overturned. What the investigation did find is a defect one level up: **the amputation harness could
not fail, and its output called 82 unrelated passes "survivors"**. That is fixed. Item 2 is fixed and
proved able to go red twice.

---

## Item 1 - the unexplained amputation survivor

### The two survivor lists

`scripts/check-u1-boot-amputation.sh` run to completion on two clean worktrees, `uv sync --frozen`
first in each. Both runs completed; neither timed out.

| Row | 667db50 passed | 1e04ae3 passed | 667db50 failed | 1e04ae3 failed |
|---|---|---|---|---|
| BASELINE | 83 | 76 | 0 | 0 |
| A. `config.py` does not exist | 0 | 0 | all error | all error |
| B. `config.py` is ZERO BYTES | 0 | 0 | all error | all error |
| C. `validate_settings()` refuses nothing | 53 | 52 | 30 | 24 |
| D. `_check_transport` never called | 70 | 69 | 13 | 7 |
| E. `TOOL_REQUIREMENTS` empty | 69 | 62 | 14 | 14 |
| F. `KNOWN_TOOLS` empty | 43 | 37 | 40 | 39 |
| G. `_term` + handler GONE | 77 | 70 | 6 | 6 |
| H. `finally` block GONE | 80 | 73 | 3 | 3 |
| I. bare `FastMCP` | 72 | 65 | 11 | 11 |
| J. `configure_logging()` never called | 76 | 69 | 7 | 7 |
| K. `configure_logging()` configures NOTHING | 76 | 69 | 7 | 7 |
| L. the sink's redactor redacts nothing | 82 | 75 | 1 | 1 |
| M. stdlib never bridged into loguru | 81 | 74 | 2 | 2 |

Both runs exited **0**, which is the old contract and is itself the second finding below.

### The lists differ by exactly the seven tests `c7809f6` added, and by nothing else

Diffed **by test id**, per row. Every id present at 667db50 and absent at `1e04ae3` is one of the
seven `c7809f6` wrote:

```
test_a_well_formed_token_map_still_boots
test_a_token_mapped_to_no_scopes_is_refused
test_a_token_mapped_to_a_blank_scope_is_refused
test_a_refusal_over_a_bad_key_never_echoes_the_token_map
test_an_empty_bearer_token_key_is_refused[-the empty string is not a bearer token]
test_an_empty_bearer_token_key_is_refused[   -a whitespace-only key is not a bearer token]
test_an_empty_bearer_token_key_is_refused[\t\n-nor is one made of other whitespace]
```

**No test that exists in both trees changed survivor status on any row.** In particular
`test_a_failing_sink_after_a_write_returns_a_warning_not_an_error` survives rows C, D, E, F, G, H, I,
L and M on **both** trees, and dies on J and K on **both** trees.

**So the survivor is pre-existing. `c7809f6` did not cause it.** The belief the brief asked me to
treat as a claim is confirmed by measurement, and I would have said so plainly if it were not.

### The mechanism - and why this one is NOT the audit-logging precedent

The brief's hypothesis was a second instance of "the READ arm survived J/K/L/M because 'no raise, no
warning' is what an unconfigured logger returns too". **It is not.** Measured directly, row by row,
against that single test (`/tmp/probe-survivor.sh`, reproduced below in "Reproducing this"):

```
=== INTACT baseline ===                                        1 passed
G handler+_term GONE:              exit=0   1 passed
H finally block GONE:              exit=0   1 passed
I bare FastMCP:                    exit=0   1 passed
J configure_logging never CALLED:  exit=1   1 failed
K configure_logging configures NOTHING: exit=1   1 failed
L redactor redacts NOTHING:        exit=0   1 passed
M stdlib never bridged:            exit=0   1 passed
```

**J and K kill it.** J and K are the two amputations that remove the subject this test actually
names - a configured loguru sink with `catch=False` pointed at the process's stderr. Under J or K the
autoinit handler is what remains, it has `catch=True`, it swallows the `/dev/full` write failure,
`emit()` returns `[]`, and `len(recorded["warnings"]) == 1` goes red. The assertion is anchored to
its subject exactly as its name claims. The in-process `sink_really_failed` control the
audit-logging agent added is doing its job.

The rows it survives are rows that **do not touch its subject**:

- **C-F** amputate `config.py`. `FAILING_SINK_ENTRY` never calls `main()`; it imports
  `fast_mcp_jobvite.__main__` for its module-scope `configure_logging()` and then drives
  `audit.emit` directly. No refusal is on that path.
- **G, H** amputate the SIGTERM handler and the `finally: os._exit` block. Neither runs in this
  script.
- **I** amputates `build_server`. This script never builds a server.
- **L** removes redaction. Redaction changes what the *stderr line* says; it does not change whether
  `logger.bind(...).info(...)` **raises**, which is what the failure policy branches on
  (`src/fast_mcp_jobvite/audit.py:331-335`), and the returned warning text
  (`audit.py:357-362`) contains no redacted material. Correctly unaffected.
- **M** removes the stdlib-to-loguru bridge. `audit.py` writes through loguru directly.

A test surviving an amputation of something it is not about is the **correct** result. Which brings
us to what the actual defect is.

### The defect: the harness called all 82 of those "survivors", and could not go red

Row L at 667db50 printed **82 survivors**. Exactly one of them - the redaction test - was about
redaction; it died, so it is not in the list. The other 82 are tests row L does not reach, and they
pass on an intact tree for the same reason. The word "survivor" had come to mean "passed", so the one
line that would be a genuine finding was indistinguishable from 81 lines of noise, by hand, on every
row. That is how a real vacuous assertion would get missed, and it is why this row needed a person at
all.

Underneath that, the harness **could not fail**. Its header said so as a virtue - "THIS HARNESS DOES
NOT EXIT NON-ZERO ON SURVIVORS" - and the consequence is that a row whose `re.sub` anchor moves, or
whose `str.replace` silently no-ops, prints a *longer* list and still exits 0. Nothing automated, and
almost nobody reading, can tell that from a clean run. **A harness that cannot fail is worse than no
harness.**

### Recommendation, and what I did

**A better ROW, not a better assertion.** `tests/test_logging_process.py` needs no change: J and K
prove the assertion is anchored, and the brief's hold on that file costs nothing. The change is to
the harness, and I made it on my branch:

1. **Every row declares a `MUST_DIE` array** - the assertions that exist to notice that row. Derived
   by measurement (each row was run and the tests it actually killed recorded), never from reading
   test names, because a test name is an unverified claim about its body.
2. **A `MUST_DIE` test that passes is an `UNEXPECTED SURVIVOR`, printed first, and exits 1.** The
   full passed list is kept and relabelled as what it always was: context, not a finding.
3. **Every declared id is verified to PASS on the intact baseline before any row runs**, aborting
   with 3 otherwise. Without this, a renamed test "does not survive" every row forever - a green that
   checked nothing, which is the exact defect this file hunts.
4. **A timed-out row now sets the failure flag.** It previously printed a note and continued; a
   timed-out run emits no `PASSED` lines, so every declared id would read as having died and the row
   would score as a pass. A row that could not be measured is a row that failed.

New exit contract, stated in the header: **0** every declared assertion died; **1** an unexpected
survivor or an unmeasurable row; **3** could not run (baseline red, or a declared id gone).

### Proof the reworked harness can go red - three controls

**Control 1, the finding path.** Row L's amputation neutered (the `str.replace` still runs, still
rewrites the file, but inserts a comment instead of `return True`), so the redactor survives:

```
########## BASELINE - the intact tree
============================= 83 passed in 22.03s ==============================
  all declared MUST_DIE ids pass on the intact tree.

########## L. the sink's redactor returns without redacting
============================= 83 passed in 21.80s ==============================
  UNEXPECTED SURVIVOR: tests/test_logging_process.py::test_a_third_party_log_line_is_redacted_at_the_sink
    This assertion exists to notice THIS amputation and did not.
########## END
FAILED: at least one assertion that exists to notice an amputation
        survived it, or a row could not be measured. Search this
        output for 'UNEXPECTED SURVIVOR' and 'TIMED OUT'.
EXIT=1
```

Note the row summary line: `83 passed` where the intact tree also gives `83 passed`. Under the old
harness that row was **indistinguishable from a working one** and exited 0.

**Control 2, the instrument path.** One declared id renamed to a name no test has:

```
ABORT: declared MUST_DIE id does not pass on the INTACT tree:
         tests/test_logging_process.py::test_a_third_party_log_line_is_redacted_at_the_sink_RENAMED
       It was renamed, deleted or is failing. Its row is checking
       nothing until this is repointed.
EXIT=3
```

(printed twice, correctly - that id is declared by both row L and row M.)

**Control 3, the whole harness unmodified**, all 13 rows on my branch: see "Verification" below.

### Reproducing this

The per-row probe is `/tmp/probe-survivor.sh` and the survivor-list differ is `/tmp/persurvivor.py`.
**Both are in `/tmp` and a restart will destroy them**, which this project has already paid for
twice. The measurement they produced is now carried by the committed `MUST_DIE` tables, which is the
durable form: the per-row expectation is the probe, re-run by the harness itself every time.

---

## Item 2 - R3-M2, the PID-1 harness

### What each arm established BEFORE the fix

`scripts/check-u1-pid1-shutdown.sh` at 667db50, `run_arm`:

- **`http`**: marker reached `closed`; `docker stop` returned inside the 15s grace; and
  `printf '%s' "$logs" | grep -q 'process \[1\]'` - uvicorn's `Started server process [1]`.
- **`stdio`**: marker reached `closed`; `docker stop` returned inside the grace. **Nothing about
  PID 1.** The `grep` was inside `if [ "$transport" = "http" ]`.

Both of the stdio assertions hold for a process that is not PID 1. **Measured, not argued** - the
unmodified 667db50 script with `--init` added to `docker run` (which makes the interpreter PID 7):

```
PID-1 shutdown, host venv under python:3.12-slim, no --init, docker stop -t 15
  stdio: marker='opened pid=1 closed ' stop=.017746449s exit=0        <- PASSES at pid 7
  http:  marker='opened pid=1 closed ' stop=.337931037s exit=0
    FAIL: no 'Started server process [1]' in the log - this was NOT pid 1
FAILED
EXIT=1
```

The stdio arm is green against a container where the interpreter is **not** PID 1. That is R3-M2,
confirmed by running it rather than by reading it. (The `pid=1` inside the marker string is my own
instrumentation already present in that worktree; the 667db50 script never reads it - which is the
point.)

### The fix

Per R3-M2's suggested fix, with one addition.

- `tests/boot_process.py`: `MARKER_ENTRY` now writes `f"opened pid={os.getpid()}\n"` (with
  `import os`). Every downstream reader matches the substring `opened`
  (`tests/boot_process.py:153`, `tests/test_boot.py:191`, `tests/test_shutdown.py:74`,
  `scripts/check-u1-pid1-shutdown.sh:108`) and is unaffected. **355 passed, 2 deselected, 0
  skipped** confirms it.
- `scripts/check-u1-pid1-shutdown.sh`: the `http`-only `grep` is replaced by an **unconditional**
  check that parses the pid out of the marker. This also drops the dependency on a uvicorn log
  string, a third-party format this project does not control.
- **My addition: two checks, not one.** A missing pid and a wrong pid are different failures and say
  so. `grep -q 'pid=1'` alone would go red when `MARKER_ENTRY` stops recording the pid, but with a
  message blaming the container - and the cheapest way for a future reader to make that message go
  away is to delete the check. An absent instrument must not render as a wrong reading.
- The header's "on BOTH transports" claim now has a paragraph saying what it used to mean and what it
  means now, rather than a claim silently becoming true.

`exit 2` when Docker is missing is untouched, and was exercised by accident: an early control run
from `/tmp` derived `REPO` from `BASH_SOURCE` and reported
`CANNOT RUN: //.venv/lib/python3.12/site-packages is missing; run uv sync --frozen`, `EXIT=2`.

### What each arm establishes NOW, from a real run

```
PID-1 shutdown, host venv under python:3.12-slim, no --init, docker stop -t 15
  stdio: marker='opened pid=1 closed ' stop=.023219174s exit=0
  http:  marker='opened pid=1 closed ' stop=.326772427s exit=0
Both arms: teardown ran and the process exited inside the grace period.
EXIT=0
```

Both arms: teardown ran (`closed`), inside the grace, **at pid 1**.

### The amputations that prove the fixed arms can fail

**Amputation 1 - the container's PID 1 is taken away.** `--init` added to `docker run`, nothing else
changed:

```
  stdio: marker='opened pid=7 closed ' stop=.028126307s exit=0
    FAIL: the entry ran as pid 7, not pid 1 - this arm did
          NOT measure a PID-1 signal disposition.
  http:  marker='opened pid=7 closed ' stop=.265556201s exit=0
    FAIL: the entry ran as pid 7, not pid 1 - this arm did
          NOT measure a PID-1 signal disposition.
FAILED
EXIT=1
```

**Both** arms red, against the same tree where the pre-fix script passed stdio.

**Amputation 2 - the instrument is taken away.** `MARKER_ENTRY` reverted to `fh.write("opened\n")`:

```
  stdio: marker='opened closed ' stop=.056095725s exit=0
    FAIL: the marker records no pid - MARKER_ENTRY no longer writes
          'opened pid=<n>', so this arm CANNOT establish pid 1.
          marker was: 'opened closed '
  http:  marker='opened closed ' stop=.309848997s exit=0
    FAIL: the marker records no pid - MARKER_ENTRY no longer writes
          'opened pid=<n>', so this arm CANNOT establish pid 1.
FAILED
EXIT=1
```

The arm refuses to degrade to the weaker check. That is the specific failure R3-M2 was about.

---

## Two things I found outside the two items

**F-1 (Low) - `docs/worklogs/U1-IMPL-REPORT.md` carried R3-M2 in prose.** Its lines 193-200 print two
columns and then say "The container log naming process **[1]** is the evidence that this was PID 1" -
but that `[1]` appears in the **HTTP** column only. The paragraph above it claims "simulated, in a
container, on **both** transports". One arm's evidence carrying two arms' claim, in the record that
closed a DESIGN.md limit. **Fix, applied:** a `Correction, R3-M2` paragraph rewritten into that
section naming what the stdio column did and did not show, and the post-fix numbers. I did not delete
the original measurement - it is a dated record of what was measured then, and the correction sits
against it.

**F-2 (Nit) - the same file pointed at a `/tmp` reproducer that has been committed since `06dd240`.**
Line 210 read "The reproducer is `/tmp/u1probe/pid1.sh`; if you want it durable, say so and I will
commit it as `scripts/check-u1-pid1-shutdown.sh`". The offer was taken up; the sentence was not
updated, so it points a reader at a path a restart destroyed. **Fix, applied:** rewritten in place to
name the committed script and `CONTRIBUTING.md:118`.

**Not a finding, but worth a line:** `CONTRIBUTING.md:121-122` says the harness runs "on both
transports", which was too strong at 667db50 and is now true. No edit needed.

---

## Verification

Run in `/tmp/harness-work` on the rebased branch, each gate on its own line, judged by exit code:

```
uv run --frozen pytest -q          362 passed, 2 deselected in 24.24s   PYTEST_EXIT=0
uv run --frozen ruff check .       All checks passed!                   RUFF_EXIT=0
uv run --frozen ruff format --check .  51 files already formatted       FMT_EXIT=0
uv run --frozen mypy .             Success: no issues found in 38 source files   MYPY_EXIT=0
bash -n scripts/check-u1-pid1-shutdown.sh                               SYNTAX OK
bash -n scripts/check-u1-boot-amputation.sh                             SYNTAX OK
```

**362 passed, 2 deselected, 0 skipped**, run on the RESTORED tree after the final amputation run
finished - an earlier gate pass overlapped a running harness, which mutates `src/` in place, so its
result was not trustworthy and was re-run rather than reported. `shellcheck` is **not installed on
this host**, so the shell
changes are syntax-checked by `bash -n` and by running them, not linted.

`docs/reviews/check-obligations.py`, verbatim:

```
Mappings: 29  |  anchors verified against their subject: 22  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
OBLIGATIONS_EXIT=0
```

**PREAMBLE.md's suite baseline line is stale.** It says "322 passed, 2 deselected, 0 skipped
(measured at `0d34c66`)". The measured figure at 667db50 is **355**, which is what `4322fd2`
("ratchet the suite floor 348 -> 355") set the floor to, and **362** after the rebase onto
`0291bac`. Reporting it as the preamble instructs; the line has now been stale across at least three
ratchets, which suggests it wants to be derived rather than retyped - the same argument the preamble
itself makes about retyped constants.

**Amputation harness, full 14-row run on the REBASED branch, `HARNESS_EXIT=0`:**

```
########## BASELINE - the intact tree              87 passed in 15.26s
  all declared MUST_DIE ids pass on the intact tree.
########## A. config.py does not exist               every declared assertion died (2 of 2)
########## B. config.py is ZERO BYTES                every declared assertion died (2 of 2)
########## C. validate_settings() refuses nothing    30 failed, 57 passed   (3 of 3)
########## D. _check_transport never called          13 failed, 74 passed   (3 of 3)
########## E. TOOL_REQUIREMENTS is EMPTY             54 failed, 33 passed   (2 of 2)
########## F. KNOWN_TOOLS is EMPTY                   41 failed, 46 passed   (2 of 2)
########## G. _term + handler GONE                    6 failed, 81 passed   (2 of 2)
########## H. the finally block GONE                  3 failed, 84 passed   (2 of 2)
########## I. build_server returns a BARE FastMCP    11 failed, 76 passed   (3 of 3)
########## J. configure_logging() never called       10 failed, 77 passed   (3 of 3)
########## K. configure_logging() configures NOTHING 10 failed, 77 passed   (3 of 3)
########## L. the record filter redacts nothing       1 failed, 86 passed   (1 of 1)
########## N. the sink writes it unredacted           1 failed, 86 passed   (1 of 1)
########## M. stdlib never bridged into loguru        4 failed, 83 passed   (2 of 2)
########## END
Every declared assertion died under its own amputation.
The 'everything else that passed' lists are context, not findings.
HARNESS_EXIT=0
```

No row timed out; the 300s cap was never approached (slowest row: I, 162.16s). The pre-rebase run
of the same rework at `667db50` was also `HARNESS_EXIT=0` across its 13 rows, with failed/passed
counts identical row for row to the ORIGINAL harness at that SHA - the rework changed what the
harness says and returns, not what it amputates.

---

## The rebase, and what it caught

`main` moved 15 commits while I worked, and four of those touch files I changed. I rebased rather
than hand over a conflict, because the file the conflict lands in is the one this task reworked.

**One content conflict**, in `scripts/check-u1-boot-amputation.sh`: `main` had renamed row L to "the
record FILTER redacts nothing" and added a **row N** for the rendered half. Resolved by keeping
`main`'s rows verbatim and wiring both to `MUST_DIE` arrays.

**Then the new harness immediately failed on its own author.** Three of my declarations were wrong
after the rebase, and each was caught rather than shipped:

1. `MUST_F` named `tests/test_boot.py::test_the_default_loopback_bind_starts`, which `45a60b8`
   (R3-N1) renamed to `..._starts_a_real_process`. Caught by the **baseline id check**, `EXIT=3`.
   This is the check earning its place on its first real encounter: a rename is exactly how a
   declared expectation goes silently vacuous.
2. `MUST_L` also named `test_a_third_party_log_line_is_redacted_at_the_sink`. Caught as an
   `UNEXPECTED SURVIVOR`. **Measured** (`/tmp/probe-LN.sh`): row L kills exactly one arm,
   `test_a_sink_this_project_did_not_install_sees_a_redacted_record`, and the third-party arm
   survives because row N's sink still redacts what it renders - so the stream that arm reads is
   clean either way. Not vacuous; declared under neither row now, with the reason in a comment.
3. `MUST_N` also named `test_the_process_publishes_no_credential_when_the_transport_fails`. Caught
   the same way. Row N kills exactly `test_an_exception_carrying_a_credential_is_redacted_at_the_sink`.
   The transport arm survives because its credentials travel in **headers**, which `redact_headers`
   scrubs at the producer before the record exists (M-5/L-1) - the sink is not the layer protecting
   it. Declaring otherwise would assert an expectation the code does not owe.

I am recording these as findings against myself rather than quietly correcting them, because the
tempting repair for all three - delete the declaration until the run is green - is the defect this
task exists to remove. Each was resolved by measuring which arm actually dies.

`docs/reviews/check-obligations.py` after the rebase, verbatim:

```
Mappings: 29  |  anchors verified against their subject: 22  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
```

Post-rebase suite: **362 passed, 2 deselected, 0 skipped**. (`main`'s own `45a60b8` reports 362 too.)

---

## What I did NOT verify

- **`shellcheck` on either script.** It is not installed on this host. I could not settle it; both
  scripts pass `bash -n` and were executed end to end, which is stronger than a linter for the
  control paths but says nothing about quoting hazards on paths I did not exercise.
- **Whether the `MUST_DIE` lists are the RIGHT lists rather than merely correct ones.** They are the
  tests each row actually kills today, chosen for naming that row's subject. They are a monotone
  regression guard: they catch a row that stops amputating, and they are structurally blind to a
  vacuous assertion nobody declared. That is a narrower instrument than the harness's stated ambition
  and I would rather say so than let the exit code imply otherwise.
- **Rows A and B under the new contract in a tree where they could partially fire.** Both produce
  collection errors, so no test passes and no declared id can survive. I did not construct a case
  where `config.py` is broken enough to error some modules and not others.
- **Whether any OTHER test in the suite is vacuous.** I measured the one the brief named, plus the 12
  ids the `MUST_DIE` tables now declare. The other 70 collected tests were not amputation-tested
  individually.
- **The `http` arm's uvicorn assertion is now gone.** I removed it per R3-M2's suggested fix. It was
  a second, independent witness to PID 1 on that arm, and the marker check replaces two witnesses
  with one. I judge the trade correct (the marker is ours, the log string is not) but it is a real
  loss and the decision was mine.

Worktrees `/tmp/harness-base` and `/tmp/harness-pid1` removed. **`/tmp/harness-work` is left in
place**: it holds the rebased `fix/harness-integrity` and a synced `.venv`, so the merge and any
re-run land there without a fresh `uv sync`. Remove it with
`git worktree remove --force /tmp/harness-work` once the branch is merged - the branch itself lives
in the repository, not in the worktree. Nothing was pushed and nothing was merged.
