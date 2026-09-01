# CODE-REVIEW-R9 - everything merged between 8695101 (exclusive) and f699f74

<!-- REVIEW-COVERS: 8695101..f699f74 -->

Reviewer: `review-r9`. Subject: `git diff 8695101..f699f74`, **23 commits** (16 excluding
merges), 17 files, +2612/-38. Most of it was written and merged by the orchestrator with no
review round.

*This line originally read "17 commits, 17 files". The file count was right and the commit
count was not - 17 is the number of FILES, copied into the commit slot. Re-measured at R10:
`git log --oneline 8695101..f699f74 | wc -l` is 23, `--no-merges` is 16, `git diff --shortstat`
is 17 files / +2612 / -38, and `git merge-base --is-ancestor 8695101 f699f74` confirms the range
is linear. Corrected in place rather than annotated, so a reader is not left choosing between two
figures; the range itself was always right, which is why this document can carry the
`REVIEW-COVERS` declaration above. A record may go stale. It may not be wrong.*

Read first: `docs/briefs/PREAMBLE.md` in full; `docs/standards/` **does not exist in this
repo** (`ls docs/standards/` -> `No such file or directory`), so the brief's "then
`docs/standards/` as it directs" resolved to nothing and PREAMBLE does not name that path
either. Design read as frozen via `git show c15b138:docs/DESIGN.md` (2045 lines), never
from the working tree.

**Worked read-only in the shared checkout as instructed.** No branch, no commit, no push,
no worktree, and the only file I wrote is this one. `git status --porcelain` was clean of
tracked modifications before and after every command below.

---

## What I RAN, and what it licenses

| Command | Result |
|---|---|
| `uv run --frozen pytest -q` | `867 passed, 6 deselected in 52.47s`, **0 skipped** |
| `python3 scripts/check-harness-anchors.py --self-check --floor 456` | `anchors resolved: 456`, `OK`, exit 0 |
| `python3 docs/reviews/check-row-floor-exactness.py` | exit 0, `Harnesses checked for exactness: 23`, `Harnesses carrying BOTH floors, checked for agreement: 8` |
| `bash docs/reviews/check-row-floor-controls.sh --list` | 23 names |
| the two `floor_line` greps against the literal breach text of `check-critical-coverage-amputation.sh` | **both NO MATCH** (H1) |
| `grep -rno 'DESIGN\.md:[0-9]' <dir> \| wc -l` per directory | see M2 |
| `grep -lE '^[[:space:]]*ROW_FLOOR=[0-9]+[[:space:]]*$' scripts/*.sh` vs `--list` | 24 vs 23, one omission (L1) |

**A green gate licenses only what it checked.** The exactness gate's exit 0 licenses
23 static floor-vs-ERE comparisons and 8 internal-vs-external agreements. It does not
license any claim that a floor matches a *live* run for the 14 harnesses added by
82bec4c, and it says so itself.

**I did NOT run `check-row-floor-controls.sh` against any harness.** It edits a tracked
file and its subjects mutate `src/` for the length of a run, in a checkout the
orchestrator is working in. Every finding about that script is read-only reasoning or a
greps-against-literal-text proof, and each is labelled below.

---

## Answers to the three questions the brief asked directly

**"Can either exactness claim pass while being false?"** Yes, in one shape. The claim is
`floor == (lines matching the ERE) + EXTRA`, measured over the harness **source**. If the
ERE undercounts by k *and* the floor is k too low, the check passes and the floor is
slack by k - exactly the u7 defect it was built to find. What breaks the correlation is
the floor having been derived from a **run** rather than from the same reading of the
file. I checked the derivation comment above `ROW_FLOOR=` in the 14 new rows:
`check-u9-http-controls.sh:314-318` and `check-body-cap-controls.sh:263-266` both record
a run ("`14/14 controls fired`", "`12/12 controls fired` ... read off its own last line -
not a count of `mutate` calls made by reading the file"). `check-u10-write-controls.sh:402-407`,
`check-u5-jobs-amputation.sh:471-473` and `check-u8-candidates-controls.sh:481-486` record
**no provenance at all**. For those the correlated-error path is open, and the exactness
gate cannot see it. This is what task #102 is, and the gate's docstring is honest about it.

**"Is the row-count arithmetic right for a harness whose ERE cannot match every row?"**
Yes, for the one such harness. `check-harness-anchors-controls.sh` has 8 `^row "` call
sites plus one inline F1 row; `EXTRA=1` and the gate prints `floor 9 rows 9`, and
`ROW_FLOOR=9`. Both directions of an EXTRA error are loud, not silent: an EXTRA too high
reports SLACK, an EXTRA too low reports "floor exceeds its rows". The control script
guards the consequent arithmetic at `docs/reviews/check-row-floor-controls.sh:167`
(`DELETE -gt MATCHED` -> abort), so an inline-only row can never be selected for deletion.

**"Verify the 14 EREs and the EXTRA=0 claim by reading each harness."** Done, and both
hold. For all 14 the ERE count, the whitespace-tolerant count
(`^[[:space:]]*<fn> `) and the floor are the same number, so no row is written
indented or with a non-`"` first argument. Each of the 14 has exactly **one** counter
increment (`ROWS=$((ROWS + 1))` or `TOTAL=$((TOTAL + 1))`), it sits inside the row
function, and no second increment exists at top level - so `EXTRA=0` is correct in all
14. All 14 exit **1** on a floor breach, matching the table's fourth column, and in every
one the floor comparison is the **first** gate reached, so the exit is attributable.

That is the good news. The bad news is H1.

---

# FINDINGS

## HIGH

### H1 - `check-critical-coverage-amputation.sh` prints a SIXTH tally shape, and its control row can never pass

**CONFIRMED by running the assertion's own greps against the harness's literal text.**

`docs/reviews/check-row-floor-controls.sh:261-264` accepts exactly two breach shapes:

```
floor_line() {
  grep -qE "(^|[^0-9])${EXPECT}/${FLOOR} ROWS" "$1" ||
    grep -qF "holds ${EXPECT} rows, below its floor of ${FLOOR}" "$1"
}
```

`scripts/check-critical-coverage-amputation.sh:469` prints neither:

```
469:  echo "ONLY $ROWS ROWS RAN against a floor of $ROW_FLOOR. Rows were deleted"
```

and its only other tally line, `:463`, is
`echo "########## ROWS: $ROWS   ANCHORS APPLIED: $APPLIED"` - no `N/M` form anywhere in
the file (`grep -n 'ROWS|ROW_FLOOR'` over the whole harness returns 10 lines; I read all
of them).

Proof, run at HEAD with the harness's exact message text in a temp file, `EXPECT=17`,
`FLOOR=18`:

```
shapeA NO MATCH
shapeB NO MATCH
```

So when someone runs
`docs/reviews/check-row-floor-controls.sh check-critical-coverage-amputation.sh`, the
deletion will land, the harness will exit 1 as the table predicts, and the control will
still print `::error::the floor named neither '17/18 ROWS' nor 'holds 17 rows, below its
floor of 18'. Either the comparison never fired, or the counter does not track rows.` and
exit 1. That is a **false negative on a healthy harness**, and it is precisely the class
of error the script's own comment at `:256-260` warns about ("A control asserting only
the `N/M ROWS` form calls those three broken while they are working perfectly, which is
the same class of error as assuming one exit code"). The fifth shape was added by reading
three harnesses; the sixth was in the same batch of fourteen and was not.

This also means task #102's remaining work is booby-trapped: whoever runs the 14 will get
one red that is not a defect and has to diagnose it.

**Severity High** because it will produce a wrong verdict on the first attempt to close
#102, on the harness that guards critical-path coverage.

**Suggested fix.** Make the accepted set an enumerated list rather than a growing `||`
chain, so adding a shape is one line and the count is visible:

```bash
# Each entry is a grep invocation over "$1". Adding a harness whose tally
# reads differently means adding a row here, not widening a regex.
floor_line() {
  grep -qE "(^|[^0-9])${EXPECT}/${FLOOR} ROWS" "$1" && return 0
  grep -qF "holds ${EXPECT} rows, below its floor of ${FLOOR}" "$1" && return 0
  grep -qF "ONLY ${EXPECT} ROWS RAN against a floor of ${FLOOR}" "$1" && return 0
  return 1
}
```

**And close the shape at the container, not one message at a time.** A sixth shape found
by a reviewer is a seventh waiting. The durable fix is a static assertion that every
harness in `TABLE` prints a tally `floor_line` can parse: for each row, grep the harness
source for the breach `echo` on the line after `if [ "$X" -lt "$ROW_FLOOR" ]` and require
it to match one of the enumerated forms. That turns "we found five, then six" into a gate.

---

### H2 - ADR-BATCH's code citations are BASENAMES for files that are not at those paths

**CONFIRMED by running them.** `docs/briefs/ADR-BATCH.md:38-40, 62-64, 71-74` cite:

- `jobvite_client.py:518`, `:475-478`, `:2039-2049`, `:1234`
- `redaction.py:489`, `:498`

Followed literally, every one is a wrong zero:

```
ugrep: warning: src/fast_mcp_jobvite/jobvite_client.py: No such file or directory
ugrep: warning: src/fast_mcp_jobvite/redaction.py: No such file or directory
```

The real paths are `src/fast_mcp_jobvite/services/jobvite_client.py` and
`src/fast_mcp_jobvite/utils/redaction.py`.

**The line numbers themselves are all exact** - I re-read every one at the correct path:

```
518:MAX_SCAN_RECORDS: Final = 100_000
475:#: **The ADR's own text proposes a `MAX_PAGES` and, two sections
1234:        install_log_redaction: bool = True,
489:HTTPX_LOGGER_NAME: Final = "httpx2"
498:def install_log_redaction(logger_name: str = HTTPX_LOGGER_NAME) -> bool:
2039:        # ONE RULE FOR THE PAGE SIZE, and it is DESIGN.md:434-436's
```

So this is not a wrong citation, it is a citation that **cannot be resolved by the tool
the applier will reach for**, and the failure mode is a clean empty result identical to
"the code is not there". This brief is the dispatch record for task #95 and its whole
argument is "already implemented, and correctly" - an applier who greps and finds nothing
has been handed evidence for the opposite conclusion. `check-design-citation-shape.py`
does not help: it selects `DESIGN.md:` citations, not source-file ones.

**Suggested fix.** Rewrite all six to repo-relative paths in place (not appended):
`src/fast_mcp_jobvite/services/jobvite_client.py:518` and
`src/fast_mcp_jobvite/utils/redaction.py:489`, etc. Then sweep: `grep -rnoE
'\b[a-z_]+\.py:[0-9]+' docs/briefs docs/adr` and, for each hit whose basename resolves to
exactly one file under `src/` or `tests/`, check whether the written path exists. That is
a ten-line checker and it is the same shape as `check-design-citation-shape.py`.

---

### H3 - ADR-BATCH undercounts the wrong-citation SITES, so an applier stops one short

**CONFIRMED by `grep -rn` over `docs/adr/`.**

`docs/briefs/ADR-BATCH.md:127` says: *"ADR-0028 cites the §8 arm as `DESIGN.md:1276-1278`,
**twice**."*

It is three times inside ADR-0028, and a fourth outside it:

```
docs/adr/0028-approval-mechanism-names-a-path-this-design-does-not-use.md:27
docs/adr/0028-approval-mechanism-names-a-path-this-design-does-not-use.md:61
docs/adr/0028-approval-mechanism-names-a-path-this-design-does-not-use.md:102
docs/adr/0021-approval-mechanism-is-required-by-two-rows-and-defined-nowhere.md:17
```

The same undercount is in the next bullet: `ADR-BATCH.md:132` says *"ADR-0027 cites `assert
len(variables) == 15` at `test_repo_hygiene.py:81`. It is `:82`."* singular. ADR-0027
cites `:81` at **two** sites, `:35` and `:56`.

**The underlying claims are all correct**, and I verified each against the frozen design
and the tree:

- `sampling` is on `:1280`. `grep -n sampling` over `git show c15b138:docs/DESIGN.md`
  returns exactly `687` and `1280`, as the brief says. Line `1279` ends
  ``...one of `elicitation`,`` so `:1276-1278` genuinely excludes the subject. CONFIRMED.
- `assert len(variables) == 15` is `tests/test_repo_hygiene.py:82`; `:81` is
  `variables = _declared_variables()`. CONFIRMED.
- ``**`:210` makes a published `type` URI a contract**`` is `DESIGN.md:510`, not `:509`
  (`:509` ends the previous bullet, "...which is what actually happened."). ADR-0031 cites
  `:509` at `docs/adr/0031-...:28`. CONFIRMED.

So the diagnosis is right and only the multiplicity is wrong - which is the failure the
brief's own R1 warns about in a different guise ("a hand-kept list beside its container").

**Suggested fix.** Replace the counts with the command that produces them, so the number
cannot go stale independently of the sites:

```
- **ADR-0028 cites the §8 arm as `DESIGN.md:1276-1278`. `sampling` is on `:1280`.**
  Sites: `grep -rn '1276-1278' docs/adr/` (four at f699f74: 0028 x3, 0021 x1).
  Anchor on the subject instead: `grep -n sampling` gives exactly `687` and `1280`.
- **ADR-0027 cites `test_repo_hygiene.py:81`. It is `:82`.**
  Sites: `grep -rn 'test_repo_hygiene.py:81' docs/adr/` (two: 0027:35, 0027:56).
```

And add ADR-0021:17 to the batch explicitly, or state in one line why an ADR already
applied is left as a record. Right now it is neither.

---

## MEDIUM

### M1 - the gate's own docstring and its ci.yml step both still say "9", and the program prints 23

**CONFIRMED by running the program.**

`docs/reviews/check-row-floor-exactness.py:37-44`:

> *"24 harnesses carry a literal `ROW_FLOOR`. The control table names 9, so the exactness
> claim covers 9. Only 8 harnesses carry BOTH floors, so the agreement claim covers 8 -
> the other 16 have a single number with nothing to check it against, and 8 more are
> floored only in `ci.yml`. **Neither claim reaches the majority of harnesses.**"*

`.github/workflows/ci.yml:591-593`:

> *"Checks the 9 harnesses the control table names; the other 15 are #102."*

The program's own last three lines at HEAD:

```
Harnesses checked for exactness: 23
Harnesses carrying BOTH floors, checked for agreement: 8
Every floor equals its harness's live row count. OK.
```

`check-row-floor-controls.sh:58` was updated ("The exactness claim now covers all 23 rows
below") but the two downstream copies were not. So the gate that exists because a number
lived in two places has its own count living in three, two of them wrong, and the
headline sentence "Neither claim reaches the majority of harnesses" is now false for the
exactness claim (23 of 24).

**Suggested fix.** Do not retype 23 in either place. Make the docstring stop carrying a
count, and let the program's own output be the record:

```python
"""...
**WHAT THIS DOES NOT COVER.** The exactness claim covers exactly the harnesses named
by the control table; the agreement claim covers exactly those carrying both floors.
Both numbers are PRINTED by this program on every run - read them there rather than
here. Every harness carrying a literal ROW_FLOOR that the table does not name is
outside both claims, and closing that gap is task #102.
"""
```

and shorten the ci.yml comment to `# Covers the harnesses the control table names; the
remainder is #102.` The `#102` task title on the board is already correct ("23 of 24 now
CHECKED tight, but only 9 (+1) have been WATCHED fire").

---

### M2 - "867 to repoint, 767 to leave alone" silently drops `docs/briefs`' 42 from BOTH totals

**CONFIRMED by arithmetic on the document's own table, and by re-measuring.**

`docs/briefs/ADR-BATCH.md`'s table and the sentence under it:

```
src               388        <- repoint
tests             346        <- repoint
scripts           133        <- repoint
docs/briefs        42        <- repoint only the LIVE ones (see below)
docs/adr           62        <- LEAVE
docs/worklogs     186        <- LEAVE
docs/reviews      519        <- LEAVE
```
> **867 to repoint, 767 to leave alone**

`388 + 346 + 133 = 867` exactly. `62 + 186 + 519 = 767` exactly. `docs/briefs` appears in
neither, and `867 + 767 = 1634` against a table summing to `1676`.

The **previous** revision was internally consistent: `370+336+125 = 831`, plus the 3 live
brief citations = **834**; `60+170+519 = 749`, plus the other 39 briefs = **788**. The
update recomputed the three big directories and lost the briefs split that made the two
numbers add up.

Under the document's own rule the totals should read **869 to repoint** (867 + 2 live
briefs) and **807 to leave alone** (767 + 40 record briefs). See M3 - even those are wrong
now.

Re-measured at f699f74 with the document's own stated command, `grep -rno
'DESIGN\.md:[0-9]' <dir> | wc -l`:

```
src              388   tests  346   scripts       133
docs/briefs       44   docs/adr 62   docs/worklogs 214   docs/reviews 519
```

`src`, `tests`, `scripts`, `docs/adr`, `docs/reviews` all still match. `docs/briefs` is
now 44 and `docs/worklogs` 214 - the document does warn "Re-measure before you start", so
the drift is disclosed; the broken totals are not.

**Suggested fix.** Delete both totals and put the derivation in the document instead of
the result, since the point of the section is that the split is a judgement:

```
**The totals are DERIVED, not typed**, because the last two revisions of this line
disagreed with the table above it:

    repoint = src + tests + scripts + (live briefs only)
    leave   = docs/adr + docs/worklogs + docs/reviews + (record briefs)

Re-measure both with `grep -rno 'DESIGN\.md:[0-9]' <dir> | wc -l` and the live-brief
list against the task board, and check they sum to the table.
```

---

### M3 - the live-brief count is wrong at HEAD, and f699f74 broke it in the same commit that wrote it

**CONFIRMED by `git show` at three revisions.**

`ADR-BATCH.md` says: *"the only briefs belonging to open tasks are `ADR-BATCH.md` (1) and
`AUDIT-ROWS.md` (1). **So the live brief set is 2 citations, not 42**"*.

```
8695101 ADR-BATCH.md=1 AUDIT-ROWS.md=0
1a51107 ADR-BATCH.md=1 AUDIT-ROWS.md=0
f699f74 ADR-BATCH.md=3 AUDIT-ROWS.md=1
```

The three sites in `ADR-BATCH.md` at HEAD:

```
54:**Q3 IS PARTLY ALREADY IN THE DESIGN.** ... `DESIGN.md:373-375` already
127:- **ADR-0028 cites the §8 arm as `DESIGN.md:1276-1278`, twice. ...
188:- **A citation trimmed at a comma is not a citation.** `DESIGN.md:1072` cost an ADR ...
```

Lines 54 and 127 were **added by f699f74**, the same commit whose text says the file
carries 1. The live set at HEAD is **4**, not 2.

Two of the supporting measurements are right: `grep -rlo 'DESIGN\.md:[0-9]' docs/briefs |
wc -l` gives **20** brief files, and `docs/briefs/PREAMBLE.md` carries **0**. Both
CONFIRMED.

There is also an open-task problem underneath: the board now has #95, #101, #102, #103 and
#104 open, and `AUDIT-ROWS.md` is the brief for #101 while `CRITICAL-COVERAGE.md` (2
citations) belongs to #94, closed. The list is right about *which* briefs; it is the
counts that decayed inside one commit.

**Suggested fix.** Replace the parenthesised counts with the command, and re-derive the
live set at apply time:

```
Measured with `for f in docs/briefs/*.md; do printf '%s %s\n' "$f" \
  "$(grep -c 'DESIGN\.md:[0-9]' "$f")"; done`, intersected with the OPEN tasks on the
board. **Re-run both halves when you start** - this line has already gone stale once
inside the commit that wrote it, because applying the brief added citations to it.
```

That last clause is worth keeping verbatim: a brief that cites the design and instructs a
citation sweep is its own moving target, and nothing in the repo currently says so.

---

### M4 - `_die_with_parent` calls `ctypes.CDLL` after `fork`, which can deadlock the child

Read-only reasoning, not reproduced (the race is not reliably triggerable on demand).

`tests/boot_process.py:132-155`:

```python
def _die_with_parent() -> None:
    ...
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.prctl(_PR_SET_PDEATHSIG, signal.SIGKILL)
```

The docstring's own last line is *"Runs between `fork` and `exec` in the child."* Between
`fork` and `exec`, in a process forked from a multi-threaded parent, only
async-signal-safe work is safe. `ctypes.CDLL` performs a `dlopen`, which takes the
dynamic loader's locks. If any other thread in the pytest process held those locks at the
instant of the fork, the child blocks forever holding a lock no thread exists to release,
and the parent's `Popen` hangs until the pytest timeout. pytest processes here are
multi-threaded in practice (AnyIO worker threads are named explicitly at
`tests/test_shutdown.py:109-111`).

The fix's own reason for existing is that a cleanup path you cannot reach does not
protect you. A `preexec_fn` that can deadlock is the same shape one level down.

**Suggested fix.** Resolve libc **at import time**, before any fork, so the hook only
calls an already-resolved function pointer:

```python
#: Resolved at IMPORT, not inside the hook. `preexec_fn` runs between
#: fork and exec, where `dlopen` can block on a loader lock another
#: thread held at the moment of the fork. Only the call survives there.
_LIBC = ctypes.CDLL("libc.so.6", use_errno=True)
_LIBC.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong)
_LIBC.prctl.restype = ctypes.c_int


def _die_with_parent() -> None:
    if _LIBC.prctl(_PR_SET_PDEATHSIG, signal.SIGKILL) != 0:
        os._exit(_EXIT_PRCTL_FAILED)
    if os.getppid() == 1:
        os._exit(_EXIT_ALREADY_ORPHANED)
```

Setting `argtypes`/`restype` also removes a second latent issue: `signal.SIGKILL` is an
`IntEnum` passed to an untyped `ctypes` call, which works today by accident of the default
`c_int` conversion.

---

### M5 - `prctl`'s return value is never checked, and `use_errno=True` is never read

Read-only reasoning; the argument is from the code text.

`tests/boot_process.py:151` calls `libc.prctl(...)` and discards the result. `use_errno=True`
is requested and `ctypes.get_errno()` is never called. If `prctl` returns `-1` on some
host (an unusual seccomp profile, a non-glibc libc where the symbol resolves differently),
the child continues **unprotected and silently**, and `spawn_marker_server` returns a
handle that looks identical to a protected one.

`tests/test_spawn_orphan.py::test_sigkilling_the_harness_reaps_the_spawned_server` would
catch a total failure on the CI runner. It would not catch a failure on a developer's
host, and it says nothing about the other call site
(`tests/boot_process.py:181-188`, `spawn_marker_server`), which is the one that actually
orphaned a server twice.

This is the repo's own "switched-off must not look like broken" rule, inverted: broken and
working currently render identically.

**Suggested fix.** As in M4 - check the return and `os._exit` with a distinct code, so a
failed install surfaces as a child that died immediately with a nameable status instead of
a server that quietly outlives its parent. Add one line to the orphan test's docstring
recording that the exit code is the tell.

---

### M6 - `os.getppid() == 1` misfires under PID 1 and misses a subreaper

Read-only reasoning.

`tests/boot_process.py:152-155`:

```python
    # The race prctl cannot close by itself: if the parent died in the
    # window between `fork` and this call, the signal has already been
    # delivered to nobody. Re-parenting is the observable, so check it.
    if os.getppid() == 1:
        os._exit(1)
```

Two problems, in opposite directions.

**False positive.** In a container where pytest itself is PID 1, *every* child sees
`getppid() == 1` from the moment it is forked, whether or not the parent died. Every
`spawn_marker_server` call would exit immediately and every U1 boot and shutdown test
would fail with a timeout rather than a diagnosis. This repo is not hypothetical about PID
1: board task #5 is a PID-1 reproducer, and `tests/boot_process.py:32-38` documents a
PID-1 harness. CI is `ubuntu-latest` (`.github/workflows/ci.yml:87`), so CI is unaffected;
a containerised local run is not.

**False negative.** On a host where a process has called
`PR_SET_CHILD_SUBREAPER` (systemd user sessions do this), an orphan is reparented to the
subreaper's pid, not to 1, so the race check does not fire and the window it exists to
close stays open.

**And the exit is undiagnosable.** `os._exit(1)` produces a child that vanishes with
status 1 before `exec`. To `spawn_marker_server` that is indistinguishable from the
entry script failing to import, and the caller reports "the server never wrote its
marker".

**Suggested fix.** Compare against the pid the parent recorded, not against the constant
1, and give the exit its own code:

```python
_EXIT_ALREADY_ORPHANED = 91


def _die_with_parent(expected_ppid: int | None = None) -> None:
    ...
    # Compare to the pid recorded BEFORE the fork rather than to the
    # literal 1: a subreaper adopts orphans without pid 1 ever appearing,
    # and in a container where the test process IS pid 1 the constant
    # form fires on every healthy child.
    if os.getppid() != (expected_ppid if expected_ppid is not None else os.getppid()):
        os._exit(_EXIT_ALREADY_ORPHANED)
```

called as `preexec_fn=functools.partial(_die_with_parent, os.getpid())` from both sites.
Then add one arm to `tests/test_spawn_orphan.py` asserting that a child whose parent is
alive does **not** exit with `_EXIT_ALREADY_ORPHANED` - which is a positive control for
the race check itself, which currently has none.

---

## LOW / NITS

### L1 - the control table is not asserted against its container

**CONFIRMED by set comparison.** 24 harnesses carry a literal `ROW_FLOOR`; the table names
23. The omission is `check-u15-gate-amputation.sh`, which is covered by the singular
`docs/reviews/check-row-floor-control.sh` - so the gap is benign today. Nothing enforces
that. If a row is deleted from `TABLE`, exactness silently stops checking that harness and
the gate still exits 0, which is the same silent direction the whole file exists to close.

**Suggested fix.** Add to `check-row-floor-exactness.py`, after `_table()`:

```python
ALLOWED_ABSENT = {
    # Covered by the singular `check-row-floor-control.sh`, which watched
    # it fire. Named here so its ABSENCE is a decision and not a gap.
    "check-u15-gate-amputation.sh",
}
floored = {p.name for p in SCRIPTS.glob("check-*.sh")
           if FLOOR_RE.search(p.read_text(encoding="utf-8"))}
missing = floored - {n for n, _, _ in table} - ALLOWED_ABSENT
if missing:
    bad.append(
        f"carries ROW_FLOOR but the control table does not name it: "
        f"{sorted(missing)}. A harness dropped from the table is checked "
        "by nothing and this gate still exits 0."
    )
```

### L2 - the ci.yml join failure and a real floor breach both exit 1

`check-row-floor-exactness.py:110-115` raises `SystemExit(<str>)`, which prints to stderr
and exits **1** - the same code `main()` returns for "floor(s) wrong". The message is
clear to a human reading the log; a machine reading the exit code cannot tell a parser
break from a defect in the floors.

**Suggested fix.** `raise SystemExit(2)` after printing, matching the file's own use of 2
for "PARSED ZERO ROWS" at `:125`, and say so in the message: `... The join is wrong (exit
2, not the 1 a real floor breach uses).`

### L3 - the `--min-rows` flag count trusts a leading `#`

`check-row-floor-exactness.py:105-109` counts a line as a flag when it contains
`--min-rows` and does not *start* with `#`. A trailing comment (`... \  # --min-rows 3
once`) would be counted as a flag and the join would raise on a correct parse. Nothing in
`ci.yml` does this today; the three excluded comment lines are `:540`, `:566` and `:664`
and all three start with `#`, which is why the check passes.

**Suggested fix.** Count flags the same way they are parsed - from the folded text, not
the raw lines - so the two sides cannot disagree about what a flag is:

```python
flags = len(re.findall(r"--min-rows\s+\d+", re.sub(r"#[^\n]*", "", joined)))
```

### L4 - one ERE string, two regex engines

The `TABLE` EREs are consumed by `grep -E` in the shell control and by Python `re.search`
in the exactness gate. They agree on all 23 rows today (I compared counts by hand for the
14 new ones). They will not agree on a POSIX class such as `[[:space:]]`, which `grep -E`
supports and Python `re` reads as a character set of the letters in "space", nor on a
backreference. That is the "same shape is an argument, not a measurement" trap the control
script's own header opens with.

**Suggested fix.** One comment above `TABLE`:

```
# THESE EREs ARE READ BY TWO ENGINES: `grep -E` here and Python `re` in
# check-row-floor-exactness.py. Stick to the intersection - no POSIX
# classes ([[:space:]] means something different to each), no
# backreferences. A divergence here gives two row counts and no error.
```

### L5 - `docs/worklogs` is named a "repointable directory" two lines under a table marking it LEAVE

`ADR-BATCH.md`: *"The four repointable directories grew between `9c41009` and `1a51107`
(370/336/125 **and 170**)"*. The fourth value, 170, is `docs/worklogs` - which the table
directly above marks `<- LEAVE (a worklog records what that unit saw)`, and which the
brief elsewhere says repointing would "rewrite history". An applier taking that sentence
literally repoints 214 worklog citations.

**Suggested fix.** *"The three repointable directories grew between `9c41009` and
`1a51107` (370/336/125), and so did `docs/worklogs` (170), which is a record and stays as
written."*

### L6 - the R4 quotation is trimmed

`ADR-BATCH.md` quotes `:1170` as *"These two plus `audit.py` make three log producers"*.
The frozen text is *"These two plus §5.3's `audit.py` make three log producers per
invocation, against a clause that..."*. The dropped fragments do not change the ruling,
but this repo has a recorded finding about a citation trimmed at a comma inventing a
conflict, and the brief itself cites it four lines later at `:188`.

**Suggested fix.** Quote the clause to its comma: *"These two plus §5.3's `audit.py` make
three log producers per invocation"*.

### L7 - `ADR-BATCH.md:127` carries a citation it declares wrong

The document's own text contains `` `DESIGN.md:1276-1278` `` - as the subject of the
sentence saying that range is wrong. It is also, per the same document, one of the "live
brief" citations a post-application sweep must repoint. A sweep that repoints it destroys
the finding.

**Suggested fix.** Mark it inline so both the sweep and the reader stop:
`` `DESIGN.md:1276-1278` (quoted as written in ADR-0028, DO NOT REPOINT) ``.

### L8 - the fix is Linux-only by construction, and fails loudly rather than skipping

`tests/boot_process.py:129-131` justifies this: *"Linux-only, which this module already is
- `interpreter_of` reads `/proc/<pid>/cmdline`."* The justification holds for the module,
but the failure modes differ: `interpreter_of` fails inside a test with a readable
assertion, whereas `ctypes.CDLL("libc.so.6")` raises `OSError` inside `preexec_fn` and
surfaces as a `SubprocessError` from `Popen`, i.e. every server-spawning test errors at
spawn time on macOS. CI is `ubuntu-latest` so there is no CI impact.

**Suggested fix.** If non-Linux is out of scope, say so once where it bites, at the top of
`tests/boot_process.py`: `pytestmark`-style skip is not available in a non-test module, so
a module-level `if not sys.platform.startswith("linux"): raise ImportError(...)` with the
reason is clearer than an `OSError` from a fork hook.

### L9 - two of the fourteen satisfy `floor_line` from an UNCONDITIONAL print

`scripts/check-body-cap-amputation.sh:189` and
`scripts/check-log-redaction-amputation.sh:221` both print
`echo "########## $ROWS/$ROW_FLOOR ROWS"` unconditionally, before the floor comparison.
For those two, `floor_line` matching proves the **counter** tracked rows (which is claim
3, and worth having) but proves nothing about the comparison firing. Only the
`rc -eq WANT_RC` check separates a working floor from an inverted one there.

**Suggested fix.** No code change; a comment in `check-row-floor-controls.sh` beside
`floor_line` recording that on those two harnesses the tally is unconditional, so the
exit-code assertion is load-bearing rather than corroborating. A reader who deletes the
`rc` check as redundant would silently weaken two rows.

### L10 - "with no branch" describes the page-size rule, not the code

`ADR-BATCH.md:56-57` says
`jobvite_client.py:2039-2049` *"uses `min(transport_cap, configured_result_cap)` for the
exhaustive path **with no branch**"*. The cited range does branch:

```
2046:        exhaustive = limit is None
2048:        effective_limit = cap if exhaustive else min(limit or 0, cap)
```

The intended claim - that the **page size** is one rule with no exhaustive-vs-bounded
branch on top of it - is correct and is what the comment at `:2039-2045` argues. The
wording invites a reader to grep for a branch, find one, and doubt the whole paragraph.

**Suggested fix.** *"uses one page-size rule, `min(transport_cap,
configured_result_cap)`, for both paths - the `exhaustive` branch at `:2046-2049` selects
the LIMIT, never the page size."*

---

## Verified and FINE, with what I ran

State these as checked so the orchestrator does not re-check them.

- **`check-suite-floor.sh 867`** - re-derived from a run, not from arithmetic:
  `uv run --frozen pytest -q` -> `867 passed, 6 deselected in 52.47s`, **0 skipped**.
  The floor equals the count exactly. The 6 deselected are the offline job's deselection
  and are by design (`.github/workflows/ci.yml:448-450`).
- **`check-harness-anchors.py --self-check --floor 456`** - run, exit 0,
  `harnesses scanned: 33`, `anchors resolved: 456`, `OK: all 456 anchors resolve to
  exactly one hit in their target file (floor 456)`. Exact, not slack.
- **`--min-rows 18` for `check-critical-coverage-amputation.sh`** - derived, not
  arithmetic-checked. The harness has exactly 18 `^amputate "` call sites; every label is
  `A1 `..`A18 ` (I listed all 18); the row echo is
  `scripts/check-critical-coverage-amputation.sh:98`, `echo "########## $label"`; so the
  `ci.yml` row regex `'^########## A[0-9]+ '` matches exactly 18 output lines. It also
  agrees with `ROW_FLOOR=18`, which is what the exactness gate's second claim checks. The
  earlier `--min-rows 15` against `ROW_FLOOR=18` is exactly the slack this gate was built
  for, and the move to 18 closes it. I did **not** execute the harness - it mutates `src/`
  in the shared checkout.
- **The `#100` sibling sweep is complete.** `grep -rn 'Popen' --include=*.py --include=*.sh`
  over the whole repo (excluding `.git/`) returns three call sites -
  `tests/boot_process.py:181`, `tests/test_spawn_orphan.py:75`, and
  `tests/test_spawn_orphan.py:37` inside the `PARENT` source string - and all three carry
  `preexec_fn=_die_with_parent`. No backgrounded server exists in any shell harness either
  (`grep -rn ' &$' --include=*.sh scripts/ docs/reviews/` returns nothing).
- **The two cleanup callers are correctly scoped.** `tests/test_shutdown.py:74-86` wraps
  the three pre-signal asserts and re-raises; the post-signal path at `:88-97` already
  killed and waited in its own `except subprocess.TimeoutExpired`. `:361-374`'s `finally`
  is safe against a double kill (`Popen.kill` is a no-op once `returncode` is set). No gap
  between them.
- **The orphan test's positive control is not vacuous.**
  `test_the_orphan_detector_sees_a_live_child` leaves the parent alive and asserts
  `_gone_within(...) is None`, so a `_alive` that returns `False` unconditionally - the
  way the kill-arm would pass against a broken fix - fails this arm. `_alive` keys on the
  argv tag rather than on `/proc/<pid>` existence, which also closes pid recycling and
  the zombie case (a zombie's `cmdline` reads empty). The control covers the detector; it
  does **not** cover the `getppid` race check, which is M6.
- **All 14 new table rows.** ERE count == whitespace-tolerant count == `ROW_FLOOR` for
  every one; exactly one counter increment each, inside the row function, so `EXTRA=0` is
  right; all 14 exit 1 on breach, matching column four; and in all 14 the floor comparison
  is the first gate reached, so the exit is attributable to the floor and not to a later
  check.
- **Every design and source line number in ADR-BATCH resolves**, once the paths in H2 are
  corrected: `:373-375`, `:509`/`:510`, `:520`, `:1170`, `:1276-1280`, `:1545`/`:1563`/
  `:1583`/`:1584`, `:1990`, `:495-497`. §7.6 is `Why there is no confirmation token`
  (`:1148`), so R1's "there is no such list" is right; §10.1 is `Documentation
  deliverables` (`:1531`) and the `:1545-1584` block is one bullet, ending before `:1585`
  starts the next. §4.3 `Resilience` runs `:342` to `:383` (§4.4 begins `:384`), so R6's
  "a new §4.3 bullet after `:363`" lands inside the right section. The problem-type table
  is `:513-521` with **seven** data rows, so R2's "add the EIGHTH row, after `:520`"
  places it correctly, before the unmapped/500 catch-all at `:521`. §5.1's member list at
  `:496` is exactly seven members, so R6's warning against bumping it to eight is right.
- **ADR-0023's two claims.** `grep -icE 'shellcheck|strict mode|strict-mode|bash\.md'` over
  `git show c15b138:docs/DESIGN.md` returns **0**, so "no DESIGN.md change at all" holds.
  The self-contradiction is real: the Decision at
  `docs/adr/0023-...:136` puts *"the `run:` blocks in `.github/workflows/ci.yml` that call
  them"* in scope and the "does not settle" bullet at `:189` says *"It does not cover
  `ci.yml`."* The Ruling at `:195` settles it in favour of the Decision, so deleting the
  stale bullet is the right edit.

---

## What I did NOT verify

For what could not be settled, not for what I did not try.

1. **No `check-row-floor-controls.sh` run against any harness.** It edits a tracked file
   and its subjects mutate `src/` for the duration; the brief put me read-only in a shared
   checkout the orchestrator is working in, and `feedback: never stash while a subagent
   edits` applies in the other direction too. **H1 is therefore proven against the
   harness's literal breach text, not against a live control run.** It is a two-minute
   confirmation for whoever owns #102: run the control on
   `check-critical-coverage-amputation.sh` in a worktree and read the `::error::the floor
   named neither` line.
2. **The other 13 `--min-rows` values in `ci.yml`** (`:674` 19, `:686` 25, `:691` 14,
   `:711` 14, `:728` 17, `:733` 10, `:749` 10, `:762` 20, `:767` 10, `:777` 6, `:788` 12,
   `:793` 5, `:885` 14, `:896` 10, `:913` 17). The brief named three floors and I
   re-derived those three. The exactness gate's second claim covers the 8 that also carry
   an internal `ROW_FLOOR`; the rest are unchecked by anything and are #102's other half.
3. **The 14 harnesses' floors against a LIVE run.** That is the whole content of #102 and
   the reason the review could not close it: my check is the same static one the gate
   makes, so it inherits the correlated-error hole described at the top.
4. **ADR-0024/0025/0026 bodies in full.** I verified the code each ruling hangs on and the
   frozen-design lines each cites. I did not re-derive the rulings themselves, which the
   brief explicitly says to verify rather than re-derive.
5. **Whether ADR-0025's Q1 needs a code change.** `ADR-BATCH.md:59-61` calls this "the
   biggest thing in this brief" and routes it to the orchestrator. The code at
   `src/fast_mcp_jobvite/services/jobvite_client.py:2039-2049` and its comment do read as
   the brief describes, and the comment does argue against the ruling. Whether the ruling
   or the code moves is a decision, not a review finding, and it is still open.
6. **`docs/worklogs/ADR-AUDIT-REPORT.md` (698 lines), `FLOOR-CONTROLS-REPORT.md` (221) and
   `JOBS-GAPS-REPORT.md` (403)**, and `docs/reviews/probe-audit-row-container.sh` (166).
   1488 of the range's 2612 added lines. They are records rather than wired gates, the
   brief did not name them, and board task #104 already records a container defect in the
   probe. Not read line by line.
7. **`tests/test_tools_jobs.py` (+73) and `tests/test_tools_job_feed.py` (+44)** beyond
   their contribution to the 867. The brief did not name them and they are covered by
   `check-critical-coverage-amputation.sh`'s A16-A18, whose floor I did re-derive.
8. **`docs/standards/`** - the brief ordered me to read it and it does not exist. If a
   `priority: required` clause lives elsewhere in this workspace and bears on any finding
   above, I did not see it and it outranks this report.
