# LOG-REDACTION - ADR-0026 option 1, implemented and made idempotent

Task **#83**. Branch `fix/log-redaction`, based at `9fae4bb`. Worktree `/tmp/log-redaction-work`.
Design read frozen, as `git show c15b138:docs/DESIGN.md`. **Not merged, not pushed.**

Written 2026-08-29 10:16 AM CDT.

---

## What this is, and what it is NOT

**The shipped server was never exposed.** `configure_logging()` runs at `__main__` module scope on
every shipped path (`src/fast_mcp_jobvite/__main__.py:353`), and U12's C5-I1 arm asserts the
redaction fires there, including on `httpx2`'s own record, asserted PRESENT rather than merely
absent. Nothing in this change fixes a live leak, and no incident is implied by it.

**It closes an EMBEDDER's exposure.** A process that imports `fast_mcp_jobvite.server` and calls
`build_server`, or constructs `JobviteClient` directly, never runs `configure_logging()`, and
`httpx2` logs the whole `jobFeed` URL - `api`, `sc`, `companyId` - through the standard library.
That was measured at `1b2af0c` and is re-measured below.

---

## FINDING 1 (High, fixed here): **the logger is `httpx2`, not `httpx`**

ADR-0026's Decision, its Ruling, this task's description and my brief all say the filter goes on
**"the `httpx` logger"**. The library logs on **`httpx2`**:

```
.venv/lib/python3.12/site-packages/httpx2/_client.py:110:logger = logging.getLogger("httpx2")
```

ADR-0007 is `httpx2-not-httpx`, and `__main__.py`'s own docstring says "`httpx2` logs
`HTTP Request: GET <url>`" - the codebase knew; the ADR's prose did not carry it through.

**A filter installed on `httpx` is accepted by `logging` without any complaint, never fires, and
leaves the leak exactly as measured.** Every "is it installed?" and "is it exactly one?" assertion
still passes against that tree, because they observe the logger they installed onto. It is the
"a fix can be real and correct where it landed, and on the wrong artefact" shape.

I implemented it against `httpx2`. Two things guard it:

- `HTTPX_LOGGER_NAME` in `utils/redaction.py`, asserted against the library's own logger object by
  `test_the_logger_guarded_is_the_one_the_library_actually_logs_through`, so a rename upstream goes
  red rather than going quiet.
- amputation row **A3**, which points the constant at `"httpx"` and is killed.

**Suggested fix for the record:** ADR-0026's body says `httpx` in three places. It is a documented
decision, so the correction is a one-line rider on the ADR ("the logger is `httpx2` - ADR-0007"),
not a silent edit, and it is yours to make.

## FINDING 2 (nit, not fixed): **`jobvite_client.py:994` is the wrong line**

The ADR, the task and the brief all cite `jobvite_client.py:994` for the "once per invocation"
sentence. At `9fae4bb` it is at **:1043**:

```
$ git show 9fae4bb:src/fast_mcp_jobvite/services/jobvite_client.py | grep -n "once per invocation"
1043:#: rebuilt - which is once per invocation in the shapes `tools/` uses.
```

The three call sites are exactly right and I confirmed all three:

```
src/fast_mcp_jobvite/tools/jobs.py:330:        return JobviteClient(
src/fast_mcp_jobvite/tools/jobs.py:642:        return JobviteClient(
src/fast_mcp_jobvite/tools/candidates.py:575:        return JobviteClient(
```

**Suggested fix:** drop the line number and cite the subject. `jobvite_client.py`'s
`_JOBVITE_BREAKER` note is unique in the file; `:994` is not, and it has already drifted 49 lines.

---

## What was built

### `src/fast_mcp_jobvite/utils/redaction.py`

- **`RedactingLogFilter(logging.Filter)`** - rewrites `record.msg = redact_text(record.getMessage())`
  and clears `record.args`. Returns `True` always: dropping the record would turn a leak into
  silence. It calls `redact_text`, so DESIGN.md:312-318's "enforced in one place" still holds - one
  redactor, now three depths.

  **`getMessage()` and not `msg` alone.** `httpx2` calls
  `logger.info("HTTP Request: %s %s ...", method, url, ...)`, so the credential is in `record.args`
  and `msg` is a format string carrying nothing. A redactor that read only `msg` looks correct,
  passes a hand-written test against a pre-formatted message, and leaks every real record. That is
  amputation row **A5**, and it is killed.
- **`HTTPX_LOGGER_NAME = "httpx2"`** - see Finding 1.
- **`install_log_redaction(logger_name=HTTPX_LOGGER_NAME) -> bool`** - the idempotent install.
  Returns `True` if it installed, `False` if one of ours was already there, which is what makes the
  idempotence observable without reaching into `logger.filters`. The check-then-add is under a
  module-level `threading.Lock`: two threads constructing a client concurrently would otherwise both
  read a filter-less logger and both append, which is the same unbounded growth, merely rarer.

### `src/fast_mcp_jobvite/services/jobvite_client.py`

`__init__` gains `install_log_redaction: bool = True` and calls the installer as its first
statement. **A constructor keyword, never a `Settings` field** - ADR-0025 is about a setting nothing
reads and a second one is not the answer. Defaults to installing: a credential leak is a worse
default than a surprising side effect, and an embedder who wants their logging untouched says so,
which makes the exposure a choice they made.

### `README.md` - REWRITTEN IN PLACE, not appended to

The "Embedding the server rather than running it" passage said *"Until ADR-0026 is decided, an
embedder must call `configure_logging()` itself"*. That sentence is gone, replaced by what is now
true: the client installs it, you need call nothing, here is the opt-out, and the install is
idempotent. No correction was appended anywhere; there is exactly one claim in that section.

---

## THE IDEMPOTENCE MEASUREMENT

`JobviteClient` is built once per invocation from three call sites, so a bare `addFilter` in
`__init__` stacks **one filter per tool call, forever**, and every record on that logger then walks a
list that grows without bound. Tests do not see it because they build a handful of clients and exit.

**So the assertion is not "the filter is installed"** - that passes on the first construction.

`tests/test_redaction.py::test_building_many_clients_leaves_exactly_one_redaction_filter` builds
**20** clients and asserts the count of our filters on `httpx2`'s logger is exactly 1. The probe's
ARM 2 builds **25** and asserts the same, in a fresh interpreter.

Measured, from the probe's own output:

```
ARM 2  25 clients -> 1 filter(s) on httpx2: exactly 1 (ok)
ARM 2c control: hand-appended 25 -> read 25: the counter is live (PASS)
```

**`== 1` is paired with a growing control, in both places.** A counter that can only ever return 1 -
because it reads a logger nothing installs onto, or because its `isinstance` matches nothing -
satisfies `== 1` perfectly. `test_the_filter_count_can_read_growth_at_all` and the probe's ARM 2c
append by hand and read 20 / 25 back, so the reading is known to be live.

### THE AMPUTATION PROVING THAT ASSERTION CAN GO RED

`scripts/check-log-redaction-amputation.sh`, built in the shape of the other harnesses in
`scripts/` (`amputate` rows, `cmp` against a pristine copy taken before row 1,
`PYTHONDONTWRITEBYTECODE=1`, exit code as the verdict rather than `grep -c '^FAILED'`).

**Row A1 is the row this harness exists for**: it deletes the idempotence check outright, so
`addFilter` runs on every construction.

```
########## BASELINE - the intact tree
============================== 51 passed in 0.14s ==============================

########## A1  the idempotence check does not exist
  ========================= 3 failed, 48 passed in 0.17s =========================
########## A2  JobviteClient.__init__ installs nothing
  ========================= 2 failed, 49 passed in 0.16s =========================
########## A3  the filter is installed on the wrong logger
  ========================= 2 failed, 49 passed in 0.17s =========================
########## A4  the filter body does nothing
  ========================= 2 failed, 49 passed in 0.17s =========================
########## A5  args are left unredacted, msg only
  ========================= 2 failed, 49 passed in 0.16s =========================
########## A6  the probe's positive control opts in too
  ========================= 1 failed, 50 passed in 0.16s =========================

########## 6/6 ROWS
########## ROWS: 6   ANCHORS APPLIED: 6
########## TOTAL SURVIVING ASSERTIONS: 294
########## VACUOUS ROWS: 0
```

**6 rows, 6 anchors applied, 0 vacuous, 0 survivors at the row level.** Every row landed (proved by
`cmp` against its backup) and was restored (proved by `cmp` against the pristine copy). The named
case that goes red under A1 is
`test_building_many_clients_leaves_exactly_one_redaction_filter`.

Run through the shared gate, argument for argument as a CI step would:

```
bash scripts/ci-harness-gate.sh check-log-redaction-amputation.sh \
  --amputation --anchors-applied --min-rows 6 --row-re '^########## A[0-9]+ '
   -> exit 0
```

---

## THE PROBE, BEFORE AND AFTER

`docs/reviews/probe-u12-f2-embedder-leak.py`, run from its committed path.

**BEFORE** (the tree at `9fae4bb`; the probe demonstrated the defect and exited 0 when it leaked):

```
Lines an embedder's own handler received, mentioning the route:
    HTTP Request: GET https://api.jobvite.com/v1/jobFeed?api=PROBEAPIKEYVALUE&sc=PROBESECRETVALUE&companyId=PROBECOMPANYVALUE "HTTP/1.1 200 OK"

Credential values in the clear: ['PROBEAPIKEYVALUE', 'PROBESECRETVALUE', 'PROBECOMPANYVALUE']
LEAKED. An embedder that calls build_server - or, as here, the
client directly - receives the whole URL. ADR-0026 is the decision.
EXIT=0  - and exit 0 MEANT LEAKED in the old probe, which is why it was never wired.
        Re-run unchanged against the FIXED tree it printed "NOT LEAKED" and exited 1.
```

**AFTER** (inverted; it now asserts the fix and **gates**):

```
ARM 1  default (redaction installed) : lines an embedder's own handler received, mentioning the route:
    HTTP Request: GET https://api.jobvite.com/v1/jobFeed?api=[REDACTED]&sc=[REDACTED]&companyId=[REDACTED] "HTTP/1.1 200 OK"
        credential values in the clear: none
ARM 1  verdict: NOT LEAKED (ok)

ARM 1c control (install_log_redaction=False): lines an embedder's own handler received, mentioning the route:
    HTTP Request: GET https://api.jobvite.com/v1/jobFeed?api=PROBEAPIKEYVALUE&sc=PROBESECRETVALUE&companyId=PROBECOMPANYVALUE "HTTP/1.1 200 OK"
        credential values in the clear: ['PROBEAPIKEYVALUE', 'PROBESECRETVALUE', 'PROBECOMPANYVALUE']
ARM 1c control: LEAKED [...] - the arm can read a leak (PASS)

ARM 2  25 clients -> 1 filter(s) on httpx2: exactly 1 (ok)
ARM 2c control: hand-appended 25 -> read 25: the counter is live (PASS)

VERDICT: an embedder who never runs configure_logging() gets the
         jobFeed credentials redacted, and the install does not stack.
EXIT=0
```

The treatment `probe-r6-breaker-reset.py` got at `3ef01f5` was applied:

- **Every arm's verdict is derived from the predicate the gate uses.** `_leak_verdict()` returns
  `None` for "read what it must" and the failure text otherwise; the printed line and the `failures`
  list are the same call. The r6 probe printed `not counted (ok)` beside a moved counter precisely
  because the string and the exit code were computed twice, and that cannot happen here.
- **A positive control that must READ a leak.** ARM 1c opts out and must observe all three
  credentials; if it does not, the probe FAILS rather than passing, because an arm that cannot read
  a leak makes ARM 1 unreadable. Amputation row **A6** removes the opt-out so ARM 1c installs the
  redaction too - the control then observes nothing and the probe goes red, which is the row proving
  the control is load-bearing.
- **The zero-line guard is kept and hardened.** An arm that captured no route line at all is a
  broken experiment and is reported as a failure, not a pass.
- **The `__main__`-already-imported abort is kept** (exit 2), and it is why the suite runs the probe
  in a **subprocess**: in-process it would abort every time.
- **Both `# pragma: allowlist secret` comments are untouched.** `pre-commit run --all-files` reports
  `secret scan (detect-secrets, staged content) ... Passed`.

**Wired**: `tests/test_redaction.py::test_the_embedder_leak_probe_still_reproduces_its_measurements`
runs it as a subprocess and asserts exit 0, the way `test_resilience.py` wires
`probe-scan-bounds.py` and `probe-breaker-call-path.py`.

---

## FINDING 3 (Medium, fixed here): four cases passed alone and FAILED in the full suite

The `httpx2` filter list is **process global**, and it arrives at `test_redaction.py` already
populated: every other module that constructs a `JobviteClient` - `test_jobvite_client`,
`test_tools_job_feed`, `test_resilience` - installs the filter as a side effect and it outlives
them.

Measured. `pytest tests/test_redaction.py` alone: **51 passed**. The full suite, same tree:

```
FAILED tests/test_redaction.py::test_building_many_clients_leaves_exactly_one_redaction_filter
FAILED tests/test_redaction.py::test_the_filter_count_can_read_growth_at_all
FAILED tests/test_redaction.py::test_the_opt_out_is_honoured_and_installs_nothing
FAILED tests/test_redaction.py::test_install_log_redaction_reports_whether_it_installed
================= 4 failed, 804 passed, 6 deselected in 48.03s =================
```

**Fixed at the fixture**, not per case: `httpx_logger` now CLEARS ours on the way in as well as
restoring the process's own list on the way out. Snapshot-and-restore alone left each case reading
whatever ran before it, so it would have passed or failed on test ORDER. This is the reason the
PREAMBLE says run the full gate before folding, not after - a focused green said nothing here.

---

## GATES - floors DERIVED, and every command is the gate's own

Both floors read out of `ci.yml`, never retyped:

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 801
$ grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .github/workflows/ci.yml
check-harness-anchors.py --self-check --floor 415
```

| gate | command (CI's own) | result |
|---|---|---|
| Lint | `uv run --frozen ruff check .` | `All checks passed!` exit 0 |
| Format | `uv run --frozen ruff format --check .` | `72 files already formatted` exit 0 |
| Types | `uv run --frozen mypy` | `Success: no issues found in 59 source files` exit 0 |
| Suite | `uv run --frozen pytest` | **808 passed, 6 deselected, 0 skipped** in 46.17s |
| Suite floor | 801, derived above | 808 >= 801 |
| Harness anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 415` | `OK: all 421 anchors resolve ... (floor 415)` exit 0 |
| Amputation | `scripts/check-log-redaction-amputation.sh` via `ci-harness-gate.sh` | 6/6 rows, 0 vacuous, exit 0 |
| Probe | `uv run --frozen python docs/reviews/probe-u12-f2-embedder-leak.py` | exit 0, both controls fire |
| pre-commit | `pre-commit run --all-files` | file-type gate, detect-secrets, ShellCheck: all **Passed** |
| Quickstart | `uv run --frozen python docs/reviews/check-quickstart.py` | exit 0 (the README changed) |
| doc checkers | `check-coupling`, `check-settings-are-read`, `check-standards-citations`, `check-cross-references`, `check-coupling-controls`, `check-obligations` (and `--controls`), `check-plan-measurements`, `check-resweep-verdicts`, `check-coupling-sweep`, `check-adr-numbers` | all exit 0 |

**`uv run --frozen mypy`, not `mypy src`.** It checks 59 source files here; that is the gate's own
command, `ci.yml:422`. It caught one real error in my work
(`tests/test_redaction.py:474`, a generator fixture typed as its yield type) which a narrower run
would not have.

**No obligations anchor moved** - `check-obligations.py` exits 0 in both modes:

```
$ python3 docs/reviews/check-obligations.py ; echo rc=$?
rc=0
$ python3 docs/reviews/check-obligations.py --controls ; echo rc=$?
rc=0
```

---

## WHAT `ci.yml` NEEDS - IT IS YOURS, SO IT IS HERE AND NOT IN THE FILE

### 1. The two floors move

- **Suite floor `801` -> `808`** (`ci.yml:446`). Measured on this branch; branch-local until merge.
- **Anchor floor `415` -> `421`** (the `--self-check --floor` step). The six new anchors are this
  branch's harness rows; `check-harness-anchors.py` scans **30** harnesses now, up from 29.

### 2. The harness needs a step, and `check-row-floors.py` IS RED UNTIL IT GETS ONE

This is the one gate that does not pass on this branch, and it is red for the correct reason:

```
$ python3 docs/reviews/check-row-floors.py ; echo rc=$?
check-log-redaction-amputation.sh             6         NO      -
Harnesses: 29
  not referenced by ci.yml at all : 1
  wired but no floor at either layer: 0
    UNWIRED  check-log-redaction-amputation.sh
rc=1
```

I closed the half I own - the harness carries `ROW_FLOOR=6`, on its own bare line so the checker can
see it, derived from a run and not typed in. The other half is a `ci.yml` step, which I did not
write. The step, verified locally exactly as written:

```yaml
      - name: Log redaction amputation, every row applied
        run: |
          bash scripts/ci-harness-gate.sh check-log-redaction-amputation.sh \
            --amputation --anchors-applied --min-rows 6 --row-re '^########## A[0-9]+ '
```

No other CI step is needed: the probe gates through the default suite, not through a step of its own.

---

## Delivered

Committed on `fix/log-redaction`, **not merged, not pushed**:

- `src/fast_mcp_jobvite/utils/redaction.py` - the filter, the constant, the idempotent installer
- `src/fast_mcp_jobvite/services/jobvite_client.py` - the keyword and the call
- `docs/reviews/probe-u12-f2-embedder-leak.py` - inverted, four arms, gating
- `tests/test_redaction.py` - 7 new cases, +1 fixture (51 in the file, up from 44)
- `scripts/check-log-redaction-amputation.sh` - 6 amputation rows, `ROW_FLOOR=6`
- `README.md` - the passage rewritten in place
- `changelog.d/83-log-redaction.md`
- `.secrets.baseline` - line-number drift only, rewritten by the hook itself (`936->950`, `76->78`,
  `82->84`, plus `generated_at`); no new baselined secret
- this report

`docs/DESIGN.md` unchanged - it is frozen and nothing here needed it moved.

**The worktree `/tmp/log-redaction-work` is NOT yet removed** - I am leaving it until you have
merged, because the branch is unpushed and the worktree is the only copy. Say the word and it goes.

---

## WHAT I COULD NOT SETTLE

1. **Whether an embedder in the wild would rather have the side effect or the control.** ADR-0026
   decided this and I implemented the decision; it is not re-litigated here. But the decision rests
   on a judgement about absent users, and nothing I ran can test it. The only thing I can report is
   that the opt-out exists, is a constructor argument, and is proved to work
   (`test_the_opt_out_is_honoured_and_installs_nothing`, plus the probe's ARM 1c which depends on
   it).

2. **Whether `httpx2` will keep logging on a logger named `httpx2`.** I asserted the constant
   against `httpx2._client.logger.name` at the pinned version, so a rename goes red. I could not
   establish that the library will not one day log the same URL through a DIFFERENT logger - a
   second module, a child logger, a transport-level one. A grep of
   `.venv/lib/python3.12/site-packages/httpx2/*.py` for `getLogger` returns exactly one hit
   (`_client.py:110`), and that is a claim about the top-level modules I searched, not about the
   package's subdirectories. A containment check ("no logger in the package logs a URL we have not
   guarded") is the shape that would settle it and I did not build one.

3. **Whether the `threading.Lock` is reachable.** I added it because a check-then-add on shared
   state is a race by construction, and one line is cheaper than the argument. I did NOT measure a
   process that races two constructions - the three call sites are all inside async tool handlers on
   one loop, so the interleaving may be unreachable in this server's shape today. The lock costs one
   uncontended acquire per client construction and I am content to pay it; if you want it gone, the
   argument for removing it is that nothing here is threaded, and that argument is unmeasured too.

4. **Whether the filter is the right depth for an embedder's EXCEPTION text.** `__main__` needs two
   depths - `_redact_message` for the record and `_redact_serialised` for the rendered line - because
   `serialize=True` renders `record["exception"]` and a formatted `text` that the record filter never
   sees. A stdlib `logging.Filter` reaches `msg` and `args`; it does not touch `record.exc_info`, so
   an embedder whose handler formats a traceback containing a `jobFeed` URL still gets it in the
   clear. **`httpx2` does not appear to log exceptions on this path** - the probe measures the only
   record it produced - so I did not widen the filter on speculation, and ADR-0026 is scoped to the
   request line. It is a real residual and it belongs on the board rather than in a paragraph.
