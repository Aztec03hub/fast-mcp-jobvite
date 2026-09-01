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

## 3. THE SWEEP

*(filled in when the run completes)*

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
