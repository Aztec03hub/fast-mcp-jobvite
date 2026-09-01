# AUDIT-SHAPES (task #104) - the unverified probe, verified; and the three-shape sweep

Branch `fix/audit-shapes`. Base `dad014e` (`git merge-base main fix/audit-shapes`), NOT `main`.
Worktree `/tmp/audit-shapes-work`, removed at the end of this report.

**What I inherited.** One commit, `d1a07d0`, one file, 498 lines,
`docs/reviews/probe-audit-shape-container.py`, written by an agent killed by a usage limit before
it reported. Never run, no gate ever run against it. Its own commit message says it is not to be
trusted, and I re-derived every number in it rather than reading them.

**Headline.** The probe was substantially correct and it RUNS. It had one defect of exactly the
class it exists to hunt (a hand-kept list beside its container), which I fixed. The controls it
needed did not exist; they do now, they pass, and they are a committed script rather than a
paragraph.

---

## 1. THE POPULATION, DERIVED - and reconciled against an independent enumeration

`--list` at `e2b4ecb`:

| shape | AST population | raw `grep -rn ... src/` | delta, and what the delta IS |
|---|---|---|---|
| `emit(...)` | **13** | 15 | 2 `def emit(` DEFINITIONS: `audit.py:352`, `__main__.py:284` |
| `is_error=True` | **6** | 8 | 2 PROSE mentions in docstrings: `approval.py:27`, `tools/jobs.py:26` |
| `AuditPhase.X` | **15** | 17 | 2 COMMENTS naming the member: `tools/jobs.py:413`, `audit.py:409` |

**Every one of the six deltas is accounted for by name, not by arithmetic.** The task's
`~8 / ~17 / ~15` are not stale: they are exactly the RAW GREP counts, which have not moved. The
AST counts are lower because a grep counts a definition, a comment and a docstring as a call site
- which is why the brief forbids regressing this to a grep, and the numbers say why.

The `AuditPhase` container was enumerated independently, out of the enum itself:

```
$ python3 -c "...ast over src/fast_mcp_jobvite/audit.py, class AuditPhase..."
['BEFORE_SIDE_EFFECT', 'READ', 'AFTER_WRITE']
```

**POPULATION SIZE IS PRINTED BESIDE EVERY VERDICT** in §3, and the probe re-derives the population
from the RESTORED tree at the end of the run and fails if it moved. A shrinking population is the
mechanism that manufactures a clean zero, and this run cannot hide one.

---

## 2. NON-VACUITY, PROVED BEFORE ANY VERDICT WAS READ

`docs/reviews/probe-audit-shape-controls.py`, committed at `e2b4ecb`, exit **0**, verbatim:

```
population BEFORE planting: 13
population AFTER planting:  16
A PASS: the derivation grew by exactly 3 and named the plants
B: applied=True rc=1 killed=['tests/test_probe_control_plant.py::test_asserted_site_emits_its_audit_row'] tail='============ 1 failed, 868 passed, 6 deselected in 75.47s (0:01:15) ============'
B PASS: the asserted plant was killed, by its own test
C: applied=True rc=0 killed=[] tail='================= 869 passed, 6 deselected in 73.73s (0:01:13) ================='
C PASS: the unasserted plant survived - a survivor is real
D1: applied=False refused="IndentationError: expected an indented block after 'if' statement on line 23 (<unknown>, line 24)" rc=None
D1 PASS: refused, no verdict - IndentationError: expected an indented block after 'if' statement on line 23 (<unknown>, line 24)
D2: applied=False refused='mutation did not land despite a successful write' rc=None
D2 PASS: a write that changed nothing was refused, not scored

ALL FOUR CONTROLS PASS. Population restored to 13 emit sites.
```

Mapping to the four the brief required:

- **the population is DERIVED, not listed** - control A. Three `emit(...)` sites are planted in
  `src/` and the derivation moves 13 -> 16 and NAMES them. A derivation frozen into a literal
  would not move. Reconciled against the container in §1.
- **a planted site that MUST be killed is killed** - control B, `rc=1`. Not merely red: the killed
  test is the planted one, so it did not die for an unrelated reason. Counts reconcile
  (`1 failed, 868 passed` = 869, the baseline 868 plus the plant).
- **a planted site that MUST survive survives** - control C, `rc=0`, `869 passed`. **B and C are
  byte-identical function bodies under the identical operator, differing only in that a test names
  one of them.** That is what makes a survivor in §3 a property of the SUITE rather than an
  artefact of the probe.
- **a row whose mutation does not land is REFUSED, not scored** - controls D1 and D2, at two
  DIFFERENT refusal points. D1 refuses before writing anything (the mutation cannot parse). D2
  forces the case the preamble names - a write that silently changes nothing, the `str.replace`
  against a moved anchor - and the probe's byte comparison against its backup catches it. Both
  report `applied=False` and **`rc=None`**: no exit code, so neither can be read as a survivor.

**Dry run first.** All 34 rows applied and restored with the suite never run
(`--dry-run`, exit 0, `TREE RESTORED CLEAN UNDER src/ AND tests/`), so no row's verdict rests on a
mutation that never landed.

**Baseline, re-measured on this branch, not retyped:** `868 passed, 6 deselected in 74.77s`.
**0 skipped.** Floors derived from `ci.yml` by grep at this SHA: `check-suite-floor.sh 868`,
`check-harness-anchors.py --self-check --floor 458`. Deselected is not skipped - `-m "not
credentialed and not network"` is a SELECTION (DESIGN.md:1310-1313).

---

## 3. THE SWEEP - 34 rows, 34 applied, 0 refused, 14 SURVIVORS

**Every verdict carries its population.** `POPULATION` is the derived set; `ROWS` is what was
swept. They are equal for all three shapes, so nothing was measured against a shrunken set.

| shape | POPULATION | ROWS | APPLIED | REFUSED | **SURVIVORS** |
|---|---|---|---|---|---|
| `emit(...)` | 13 | 13 | 13 | 0 | **2** |
| `is_error=True` | 6 | 6 | 6 | 0 | **0** |
| `AuditPhase.X` | 15 | 15 | 15 | 0 | **12** |
| **total** | **34** | **34** | **34** | **0** | **14** |

Every row that did NOT survive printed the tests that killed it, and every row measured a suite of
868 passed / 6 deselected / 0 skipped in its unmutated form.

### 3.1 `emit(...)` - population 13, 2 survivors

```
candidates.py:656  emit(...)  exit 0  868 passed, 6 deselected   *** VACUOUS ***
candidates.py:768  emit(...)  exit 0  868 passed, 6 deselected   *** VACUOUS ***
```

- **`candidates.py:656`** is the SUCCESS path of `search_candidates`. Nothing asserts that a
  successful search writes an audit row at all. Its ERROR sibling at 648 IS asserted, so the
  failure path is covered and the ordinary path is not. **Task #127.**
- **`candidates.py:768`** is the MRTR first leg of `create_candidate` - the `ApprovalPending`
  branch, phase `BEFORE_SIDE_EFFECT`. A pending approval for a write that emails a live human can
  be recorded nowhere and the suite stays green. Its sibling REFUSAL leg twelve lines below (780)
  IS asserted. **Task #128.**

The other eleven were killed, several by tests that name the audit row explicitly
(`test_the_audit_event_records_this_invocation`,
`test_a_job_feed_read_error_is_a_problem_object_and_an_audit_row`).

### 3.2 `is_error=True` - population 6, 0 survivors

All six killed. This shape needs nothing and should not be re-swept. Two of the six were measured
before the run was killed and four after; the six verdicts are the union, and the tool NAMES the
two it had not yet covered rather than reporting 4 of 4 (see §6).

### 3.3 `AuditPhase.X` - population 15, **12 survivors**

The operator is a ROTATION, not a deletion: deleting the argument would break the call's arity and
every test would kill it for a reason unrelated to auditing.

**Asserted (3):** `audit.py:381`, `audit.py:403` - the policy DISPATCHER, killed by 7 and 5 tests
respectively - and `candidates.py:832`.

**Survivors (12):** every remaining CALL SITE. `candidates.py` 648, 656, 694, 702, 768, 780, 796,
818; `jobs.py` 419, 426, 704, 711. All twelve measured `868 passed, exit 0`.

**The worst is `candidates.py:796`** - the emission its own comment labels *"NO AUDIT, NO WRITE
(DESIGN.md:784-785)"*. Rotating it to `READ` converts "an audit failure fails the call" into "log
to stderr and continue", so a failed audit write would let the `create_candidate` POST proceed
UNAUDITED. That is the precise inversion DESIGN.md:784-785 exists to prevent, and 868 tests do
not notice.

**This reads as ONE defect, not twelve.** The dispatcher's three branches are well tested; what
nothing tests is that a given call site passes the phase the design assigns it. **Task #129**,
with all twelve sites enumerated - see §4 for why I grouped them against the brief's instruction.

---

## 3.4 The suite floor, and why the sweep never threatened it

Baseline `868 passed, 6 deselected, 0 skipped`; `ci.yml` floor `868`, derived by grep, not
retyped. Every mutation was restored by byte comparison against a backup and the tree was verified
clean under BOTH `src/` and `tests/` at the end of every run.

---

## 4. FINDINGS

### F1 (Medium, FIXED here) - the probe carried a hand-kept list beside its container

`AUDIT_PHASES = ("READ", "BEFORE_SIDE_EFFECT", "AFTER_WRITE")` was a literal tuple sitting beside
the `AuditPhase` enum it describes. **It was CORRECT** - it equals the enum's member set, which I
checked - and that is the point: a hand-kept list reads correct right up until someone adds a
member. A fourth phase would be silently excluded from `_matches`, its call sites would never
enter the population, and the sweep would report a clean zero over a set that had quietly shrunk.
That is the failure this probe was written to prevent, present in the probe.

**Fix, applied:** `AUDIT_PHASES` is read out of `AuditPhase` by `ast`, and an empty result is a
hard `SystemExit` rather than an empty sweep. Population unchanged (15), which is the evidence the
fix is behaviour-preserving today.

### F2 (High, NOT fixed - task #130) - one row's verdict is confounded and cannot be trusted

`candidates.py:832` is `warnings = emit(event, AuditPhase.AFTER_WRITE)` - the only one of the 13
emit sites whose value is BOUND. The operator deletes the whole statement, so `warnings` stops
existing and the next line raises `NameError`. The row measured **14 failed**, and 12 of those 14
tests have nothing to do with auditing (`test_send_email_defaults_to_false_on_the_wire`,
`test_the_body_reaches_the_wire_under_jobvites_own_keys`).

A non-zero exit is scored as "asserted", so this row is a FALSE NEGATIVE and may be concealing a
third emit survivor. **The probe flagged the condition itself** - it prints
`[a NameError appears in the output - see the report]` - which is how I found it; the inherited
code was right to look for this and stopped one step short of acting on it.

**Suggested fix (a hypothesis, NOT measured):** when the enclosing statement is an `ast.Assign`
whose value IS the matched call, replace the CALL with a same-shaped literal (`warnings = []`,
since `emit` returns `list[str]`) instead of deleting the statement. That removes the emission -
the question the shape asks - and keeps the binding, which is the confound. Both existing
assertions still apply, with `expect_stmt_delta` 0 for that branch. Failing that, REFUSE the row:
the probe already has a refusal channel, and a refusal is honest where a wrong verdict is not.

### F3 (Medium, FIXED here) - the inherited probe had never been linted or type-checked

`ruff check .` and `uv run --frozen mypy` had never been run against `d1a07d0`. Running them:
**31 ruff errors and 7 mypy errors in the inherited file** (W505 doc-line-too-long including five
77-character dividers, D101/D102 missing docstrings, and seven `"AST" has no attribute "lineno"`
/ `"col_offset"` / `"end_lineno"` / `"attr"` under `strict = true`). This is the most direct
possible confirmation of the commit message's own warning that no gate was ever run against it.

**Fix, applied:** all 38 resolved. The mypy fix is not a `cast`: `_pos()` and `_span()` read the
position off the node and RAISE if it is absent, because a matched node without a position is a
bug in `_matches` rather than something to silence.

**These edits landed AFTER the sweep, so they were re-verified rather than assumed**: the
population is unchanged at 13/6/15 and all four controls still pass against the gated file. A
change to the instrument after the measurement is exactly the kind of thing that quietly
invalidates a result, so it is measured rather than argued.

### F4 (nit, FIXED here) - `--only`, so a 43-minute sweep survives being interrupted

Added because the first full run was killed mid-row (§6). `--only` narrows what RUNS and never
what the run is JUDGED against: the swept set is still compared to the full derived population and
every unswept site prints as `NOT SWEPT (no verdict exists for this site)`. A partial sweep
therefore cannot be mistaken for a complete one by reading the tally.

---

## 6. THE FIRST FULL RUN WAS KILLED, AND IT LEFT A LIVE MUTATION IN `src/`

Worth recording because it is #100's lesson reproduced exactly. The 34-row run was killed by the
harness at row 16 of 34, ~19 minutes in. **SIGKILL runs no `finally`**, so the probe's restore
never executed and `src/fast_mcp_jobvite/tools/candidates.py` was left holding a live amputation:

```
@@ -787,7 +787,7 @@ def register(
                         meta={REQUEST_ID_META_KEY: event.request_id},
-                        is_error=True,
+
                     )
```

I found it by `git status` immediately on being notified of the kill, restored by
`git checkout --` and re-verified clean before doing anything else. **No verdict in this report
was measured against that dirty tree** - the row it died on (`candidates.py:790`) was re-run from
a clean tree afterwards and is one of the four in §3.2's second chunk.

The remaining 19 rows were then run in foreground chunks small enough to finish inside a timeout,
which is what `--only` (F4) exists for. Rows 1-15 were kept: they completed and restored normally
before the kill, and every one of them printed its own restore-clean line.

**Suggested fix for the next agent, not built here:** the probe restores in a `finally`, which a
SIGKILL defeats. The durable answer is the one #100 landed for subprocesses - do not rely on the
parent's cleanup. A `--restore-only` mode that byte-compares `src/` and `tests/` against `git` and
repairs them would turn "I hope it cleaned up" into one command; the backup directory is already
`mkdtemp`ed per run, so it would need to write its manifest somewhere durable first.

---

---

## 5. THE BRIEF'S READING ORDER NAMES THE WRONG SECTION

`docs/briefs/AUDIT-SHAPES.md:12` orders `docs/DESIGN.md` **§7 (the audit trail)** read first, "frozen
at `aca9397`". At `aca9397`, **§7 is "Server, transport, configuration" (line 860)**. The audit
trail is **§5.3, "Audit logging and `request_id`", line 642**, and the audit-write-failure policy
this sweep's `AuditPhase` shape encodes is at **lines 784-800** - which is the range `audit.py:115`
itself cites. I read §5.3 and 784-800 as the authority and proceeded.

The preamble says a brief-vs-preamble disagreement is worth reporting; this is a brief-vs-DESIGN
disagreement, so recording it rather than silently reading something else.

**Suggested fix:** change `AUDIT-SHAPES.md:12` to read `docs/DESIGN.md` §5.3 and the
audit-write-failure policy at 784-800. Better, per the repo's own anchor lesson: cite the SUBJECT
phrase ("Audit-write failure has a stated policy") rather than a section number, since section
numbers drift exactly like line numbers.

---

## 6a. A DEVIATION FROM THE BRIEF, DECIDED AND FLAGGED

The brief says **"File a task per survivor."** There are 14 survivors. I filed **four** tasks:
#127 and #128 are one survivor each; **#129 carries all twelve `AuditPhase` survivors in one
task, with every site enumerated as its own row**; #130 is the confounded row (F2), which is a
probe defect rather than a survivor and would otherwise have lived only in this report.

Why: the twelve are one defect applied twelve times - the policy dispatcher is well tested and
what nothing tests is that a call site passes the phase the design assigns it. Twelve
near-identical tasks on a 126-item board is noise, and the risk the brief guards against (a
survivor silently dropped) is met by enumerating all twelve inside #129. **Split #129 if you
prefer the literal reading** - every site, its current phase, its rotation and its exit code is
in there.

---

## 7. WHAT I DID NOT VERIFY

Short on purpose. This list is for what I could not settle, not for what I did not try.

1. **Whether `candidates.py:832` is a third `emit` survivor.** F2 / #130. I could not settle it
   without changing the operator, which would have changed the instrument mid-sweep after I had
   already re-verified it once. The row is recorded as CONFOUNDED rather than as either verdict.
   This is the one place where the sweep's "2 emit survivors" could become 3.
2. **Either suggested fix in #129.** I wrote two and measured neither; they are hypotheses. The
   brief is explicit that a survivor's fix is a test and not this task's work.
3. **Whether the twelve `AuditPhase` survivors are reachable as a real defect in production.**
   The sweep proves nothing ASSERTS the phase at those call sites. It does not prove the phases
   are WRONG - I read all fifteen and they look correct today. The finding is the absence of a
   guard, not a live bug.

Things I explicitly DID settle that might look like candidates for this list:

- ShellCheck: **v0.10.0, present** (`shellcheck --version`), so it is not silently checking
  nothing. No shell file changed on this branch, so it had nothing of mine to check.
- Gate scope: `mypy`'s `files = ["src", "tests", "docs/reviews"]` and `ruff`'s
  `extend-exclude = ["**/*.md"]` both cover the two files I touched, so the green in §F3 is not a
  green over a skipped path. I checked this BEFORE running them.
- The suite floor: derived by grep at this SHA (`check-suite-floor.sh 868`), matched exactly by
  the measured baseline, `0 skipped`.

## 8. DELIVERY

Committed on `fix/audit-shapes`. **Not merged and not pushed.** Worktree `/tmp/audit-shapes-work`
removed. Tasks #127, #128, #129, #130 filed.

**Gates, run with `ci.yml`'s own commands and CHAINED WITH `&&`** so a red one stops the line
(never `cmd; echo "EXIT=$?"`, which is how a lint-red `main` got pushed on 2026-09-01):

```
uv run --frozen ruff check .        -> All checks passed!
uv run --frozen ruff format --check .-> 107 files already formatted
uv run --frozen mypy                -> Success: no issues found in 98 source files
=== ALL THREE GATES PASSED (chained with &&) ===
```

Suite: `868 passed, 6 deselected in 74.77s`, **0 skipped**, against the `ci.yml` floor of 868
derived by grep. ShellCheck is v0.10.0 and present; no shell file changed here.

**`docs/OBLIGATIONS.md` was not hand-edited, and I ran the checker rather than assuming my line
moves did not reach it** - verbatim:

```
Mappings: 31  |  anchors verified against their subject: 25  |  recorded as absent: 6
Every mapped anchor still contains its subject. OK.
```
exit 0.

**Harness anchors, floor DERIVED from `ci.yml` (458), not retyped** - verbatim tail:

```
harnesses scanned: 33
anchors resolved: 458
OK: all 458 anchors resolve to exactly one hit in their target file (floor 458).
```
exit 0. Neither new file is a shell harness, so that scan's population is unmoved by this branch.

**No `ci.yml` step is proposed by this report.** The two probes are run by hand today. If you want
them wired, `probe-audit-shape-controls.py` is the one that belongs in CI - it exits non-zero when
the instrument is broken, whereas the container probe exits 0 by design even with 14 survivors and
would gate nothing. I have run both from this worktree; the commands and their exit codes are
above and in §2.
