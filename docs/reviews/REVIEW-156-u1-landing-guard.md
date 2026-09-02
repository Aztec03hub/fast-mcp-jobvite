# #156 - thirteen mutation heredocs whose failure nothing consumed

**Agent:** `suborch-156` (Tier 1) - **Branch:** `fix/156-u1-boot-guards`
**Cut from:** `ccbdaae` on `main` - **Worktree:** `fmj-worktrees/w156`
**Files owned and touched:** `scripts/check-u1-boot-amputation.sh`,
`docs/reviews/probe-156-u1-landing-guard.sh`, this file, and the three arm
transcripts beside it. **Nothing else was written.** `ci.yml` (`suborch-161`)
and the mirror workflow (`suborch-157`) were read and not touched.

**Not pushed, not merged.** Tier 0 merges.

---

## 1. THE MEASUREMENT, TAKEN FIRST

Every count below is `scripts/check-u1-boot-amputation.sh` **at `ccbdaae`**,
derived by parsing the file rather than by reading it, so the numbers carry
their container:

| | at `ccbdaae` | on this branch |
|---|---|---|
| `python3 - "$VAR" <<'PY'` mutation heredocs | 13 | 13 |
| ... followed by `\|\| exit`, `if !` or a `$?` read | **0** | **13** |
| ... containing any landing check at all | 7 | 13 |
| ... whose diagnostic is in `ci-harness-gate.sh`'s VOCABULARY | **6** | 13 |
| `report` rows (A, B and the 13) | 15 | 15 |
| anchors visible to `check-harness-anchors.py` | 12 | 12 |

**The brief's headline number is right and its split is right**: 13 heredocs,
0 consuming the exit status, 6 with no landing check. `suborch-152`'s
self-correction ("the harness DOES assert at 7 sites") is also right, and I
re-derived both rather than taking either on trust.

---

## 2. FIVE CORRECTIONS, EVERY ONE MEASURED

### C1 - the defect is a MISDIAGNOSIS, not a silent green. This is the big one.

The brief and task #156 both describe the consequence as *"the harness reports
a survivor, and that survivor is an artefact"*, which reads as a run that goes
quietly on. **It does not go quietly on. It goes RED, blaming the wrong
thing**, and I only know that because arm A0 ran the pre-fix harness against a
moved anchor instead of reasoning about it.

The mechanism: `:284-297` verifies that **every declared `MUST_DIE` id passes
on the intact baseline**, and aborts with exit 3 if one does not. So a row
whose mutation never lands leaves all of its declared ids passing, and
`report` prints each one as

```
  UNEXPECTED SURVIVOR: tests/test_config.py::test_every_reason_is_named_not_just_the_first
    This assertion exists to notice THIS amputation and did not.
```

That sets `UNEXPECTED=1` and the harness exits 1. **The reader is sent to
`tests/test_config.py` to look for a vacuous assertion that is not there,
while the actual fault is an anchor in `scripts/`.** `ci-harness-gate.sh:208`
then prints "an amputation was survived by an assertion that exists to notice
it", which is a true sentence about a false event.

This makes the finding *more* serious to act on, not less: the old behaviour
was not a hole that CI could not see, it was CI being told a specific, wrong,
actionable thing. And it is exactly the failure
`check-u15-gate-amputation.sh:136-140` already names in its own comment - "the
failure sitting one line below its own diagnosis".

**Where the "silent" reading IS true** is the case neither the brief nor #152
separated: a row that lands **PARTIALLY**. Rows G and LN each apply two
operations. If one lands and the other does not, the declared ids may still
all die, and the row reports a clean pass while amputating half of what its
label claims. That case produces no survivor and no diagnostic. LN already
checked both of its anchors; **G checked neither**, and now checks both
separately.

### C2 - row H asserted, and its failure was unreadable to the gate anyway

`ci-harness-gate.sh:73-82` derives its grep vocabulary from phrases **the
harness's own source contains**, and greps the run's OUTPUT for them. Six of
the seven asserting rows say `"<row> anchor is not unique"`, which is a
VOCABULARY entry (`ci-harness-gate.sh:80`), so their AssertionError text was
caught by the phrase loop even though the harness exited 0.

**Row H is the seventh, and its message was `"amputation H found nothing to
remove; the anchor moved"` - in none of the nine vocabulary entries.** So H
had a landing check whose failure no gate could read: the traceback would be
printed, the row would run against an intact tree, and the phrase loop would
find nothing. The brief's "7 asserted sites" is arithmetically right and
operationally 6. H's message now says `DID NOT LAND`.

### C3 - row M's assertion identified itself as row J

`:491` at `ccbdaae`: `assert s.count(anchor) == 1, "J anchor is not unique"`,
in the heredoc for **row M**, nine rows away from J. A reader who hit it would
have opened the wrong heredoc. Corrected to `"M anchor is not unique"`, with a
line saying what it was.

### C4 - #152's own suggested fix contradicts #152's own Kind-3 finding

`WORKLOG-152-publishers.md:203-210` closes F1 with *"Then it can publish
`applied=` like its siblings."* But the same worklog's **Kind 3** section
(`:64-74`) establishes that `check-body-cap-amputation.sh` and
`check-u15-gate-amputation.sh` legitimately publish nothing **because their
landing failure is fatal** - `applied < rows` is impossible at exit 0, so an
`applied=` field would be a fabricated N/N, which
`scripts/lib/harness-result.sh:157-162` explicitly refuses ("a fabricated
`fired=0/0` would be read ... as a harness that held zero controls - a false
finding").

**Applying F1's guard moves this harness INTO Kind 3.** So the second half of
F1's fix must not be applied: this file should publish no `applied=` tally,
and `docs/reviews/check-landing-published.py` agrees - it exits 0 on this
branch with the fatal branch and no tally. I did not add one.

### C5 - three of this file's anchors are invisible to the static anchor gate

`scripts/check-harness-anchors.py` reports `anchors= 12` for this file against
13 heredocs. Derived, not guessed - its shape-B parser requires `.replace(` or
`re.sub(` in the heredoc body (`:331`) and matches `node.func.attr == "sub"`
(`:417`) / `== "replace"` (`:381`):

- **row H** binds its anchor through **`re.subn`**, and `"subn" != "sub"`;
- **rows K and M** mutate by `s.index(...)` and slicing, with no `.replace`
  or `re.sub` anywhere, so their `anchor = "..."` literals are never read.

Counting the parseable operations gives exactly 12 (C1 D1 E1 F1 G2 I1 J1 L1
N1 LN2), which is the number it prints. **So the repo-wide floor of 458 is
blind to three real anchors in this one file**, and the same shapes elsewhere
are equally invisible. This is `check-harness-anchors.py`'s shape, not mine to
change (§B), and it is reported rather than swept - see §5.

**It is also why I did not convert anything to `re.subn`.** The obvious way to
check a `re.sub` landing is `s, n = re.subn(...)`; doing that to rows C, E, G
and I would have silently dropped four more anchors from the floor while every
gate stayed green. Every new check compares `out == s` instead, or counts a
literal, so `458` is unchanged and verified below.

---

## 3. WHAT CHANGED

`scripts/check-u1-boot-amputation.sh`, one commit, nothing else:

1. **All 13 heredocs are followed by `[ $? -eq 0 ] || exit 1`** - the shape
   `check-u15-gate-amputation.sh:140` already uses. The rationale is written
   once, at the first guard, and not repeated twelve times.
2. **The six unchecked rows (C, D, E, F, G, I) now diagnose their own
   non-landing** and `sys.exit(1)`, in the `DID NOT LAND` vocabulary the gate
   can read. C, E, G and I compare the substituted text against the original;
   D and F count their literal anchor; E additionally counts the table's
   opening line, because its `re.sub` carries no `count=` and a
   twice-matching pattern would empty two tables and still compare unequal.
3. **Row G checks each of its two operations separately** (C1).
4. **Row H's message joins the vocabulary** (C2); **row M's names itself**
   (C3).
5. The header records all of it, including what an unguarded non-landing
   ACTUALLY did, so the next reader does not have to re-run A0 to find out.

**Why `exit 1` and not `exit 3`.** I considered 3: this file's header calls 3
"could not run", and a moved anchor is an instrument fault, which argues for
sending the reader to `scripts/` rather than to `src/`. Two things settle it
for 1. `ci-harness-gate.sh:214-217` prints a fixed message for 3 - "the intact
baseline is red, or a declared test id no longer exists" - which would then be
a wrong diagnosis, and **`ci-harness-gate.sh` is not mine to edit** (§B). Its
exit-1 message already ends "or a row could not be measured", which covers
this exactly. `check-u15-gate-amputation.sh` uses 1 for the same event.

**Nothing needs a `ci.yml` step.** The existing step already fails on this,
three ways over: exit 1, the `DID NOT LAND` phrase in the derived vocabulary,
and `--min-rows 14` against a run that stopped early.

---

## 4. THE POSITIVE CONTROL - `docs/reviews/probe-156-u1-landing-guard.sh`

Three arms. **The anchor move is behaviour-preserving by construction** -
`    reasons: list[str] = []` becomes `    reasons: list[str] = list()` in
`validate_settings`, which builds the same object, so the baseline stays green
and the arm is not a clean zero that explains itself. The probe asserts the
move fired (occurrences 2 -> 1) before running anything.

**Each arm runs against a scratch copy of the tree, never the checkout**, so
an interrupted arm strands its mutation in a directory that is about to be
deleted. `ARM_TIMEOUT` defaults to 2400s and is passed explicitly.

**Scoring is on WHICH LINES APPEAR, never on the exit code. A0 and A1 both
exit 1 and mean opposite things** - that is the whole finding.

`rows` counts `^########## ` lines, which is BASELINE + the 15 rows + END for
a complete run, and BASELINE + A + B for a run that stops at C.

| | harness | tree | exit | `rows` | UNEXPECTED SURVIVOR | landing diagnostic | row C reached `report` | `HARNESS-RESULT` |
|---|---|---|---|---|---|---|---|---|
| **A0** | `ccbdaae` | anchor MOVED | 1 | 17 | **3** | **0** | **yes** | `rows=15 status=breach` |
| **A1** | this branch | anchor MOVED | 1 | 3 | **0** | **1** | **no** | `rows=0 status=refused` |
| **B** | this branch | INTACT | 0 | 17 | 0 | 0 | yes | `rows=15 status=ok` |

**A0 is the finding, recorded rather than argued.** The pre-fix harness ran
row C against an intact `validate_settings` and named three tests as false
instruments:

```
########## C. validate_settings() refuses nothing
  UNEXPECTED SURVIVOR: tests/test_config.py::test_every_reason_is_named_not_just_the_first
  UNEXPECTED SURVIVOR: tests/test_boot.py::test_a_missing_credential_exits_naming_the_variable
  UNEXPECTED SURVIVOR: tests/test_boot.py::test_an_unrecognised_tool_name_exits_naming_it
```

All three are correct tests that noticed nothing because there was nothing to
notice. It then completed all 15 rows and reported `status=breach`. **Zero
landing diagnostics anywhere in 1144 lines of output**: nothing in the run
said the anchor had moved.

**A1 is the same tree with the guard.** One line, at the top of row C, naming
the harness rather than the tests; `report` never runs; the run stops with
`status=refused` and `rows=0`, which `ci-harness-gate.sh --min-rows 14` also
refuses.

**B proves the guard is not merely a way to fail.** The unmodified tree still
runs all 15 rows, every declared assertion still dies, exit 0.

**A nit against my own instrument, and it is the third instance of this shape
today.** The probe's first survivor counter said `4` for A0. The fourth hit
was the harness's own closing paragraph - *"Search this output for 'UNEXPECTED
SURVIVOR'"*. The counter is now anchored at `^  UNEXPECTED SURVIVOR: `; the
transcripts were not re-run, the corrected counters were applied to the saved
output, and the table above is the corrected reading. (The same defect ate my
first guard-count: `13` guards read as `14` because the header paragraph
explaining the guard quotes it.)

Transcripts are committed beside this file as `probe-156-arm-A0.txt`,
`probe-156-arm-A1.txt` and `probe-156-arm-B.txt`.

---

## 5. REPORTED, NOT FIXED (§D: one file read completely beats 37 changed)

**R1 - `check-harness-anchors.py` cannot see three anchor shapes.** C5 above,
with the landing sites read: `:331` (the `.replace(`/`re.sub(` gate on the
whole heredoc), `:381` (`attr == "replace"`), `:417` (`attr == "sub"`, which
excludes `subn`). In `check-u1-boot-amputation.sh` that hides row H's
`re.subn` anchor and rows K and M's index-and-slice anchors. **I did not
measure how many other files this hides**, and the number matters before
anyone raises the floor. Suggested fix: accept `subn` alongside `sub` in the
`attr` test, and decide separately whether an `s.index(...)`-and-slice anchor
should be readable at all - if it should, the parser needs a third shape; if
it should not, the two rows should be rewritten to `.replace`, which is the
cheaper change and keeps one shape in the file.

**R2 - the same unguarded-heredoc shape elsewhere: NOT SWEPT, and it is not a
uniform defect.** `git ls-files 'scripts/*.sh'` is 37 files. Per §D I read the
landing sites rather than pattern-matching, and #152 already measured that the
two Kind-3 harnesses (`check-body-cap-amputation.sh`,
`check-u15-gate-amputation.sh`) exit on a non-landing row and are correct as
they stand. `docs/reviews/check-landing-published.py` gates the one invariant
that survived reading every site and reports **0 findings** on this branch, so
there is no evidence of a second instance of THIS defect in the container.
Suggested fix: none until someone measures it; a shape rule over these files
was wrong on 4 of the 6 it named last time.

**R4 - the new probe is deliberately NOT wired, and nothing complained.**
`docs/reviews/probe-156-u1-landing-guard.sh` is a one-shot positive control
for a change, not a standing gate: its three arms run the U1 suite 35 times
and take tens of minutes. `check-checkers-are-wired.py` exits 0 with it
present, and that is not evidence it is fine - it is task #155, which measured
that the wiring checker's container is `check-*` **by prefix**, so every
`probe-*` file is invisible to it. Recording it here so the zero is not read
as a clearance. **The standing gate for this defect already exists and is
unchanged**: `ci.yml:1468`'s `ci-harness-gate.sh` step now fails three
independent ways on a non-landing row (exit 1, the `DID NOT LAND` phrase in
its derived vocabulary, and `--min-rows 14` against a truncated run).

**R3 - the mutators run bare `python3`, not `uv run --frozen python`.** All 13
heredocs, plus the same shape across the harness family. It is not currently
wrong - they use only `pathlib`, `re` and `sys` from the stdlib - but it is
the interpreter-inherited-rather-than-chosen shape task #46 fixed in four
other places. Suggested fix: leave it; record it here so the next reader who
adds a third-party import to a mutator knows the interpreter is ambient.

---

## 6. GATES, each exit code on its own line

Run in `fmj-worktrees/w156` at `b84b77d` plus the uncommitted report and
transcripts. CI's own invocation, copied out of the workflow file, wherever
the workflow has one.

```
bash -n scripts/check-u1-boot-amputation.sh                          rc=0
bash -n docs/reviews/probe-156-u1-landing-guard.sh                   rc=0
shellcheck --severity=warning <both touched files>                   rc=0
uv run --frozen ruff check .                                         rc=0
uv run --frozen ruff format --check .                                rc=0
uv run --frozen mypy                                                 rc=0
python3 scripts/check-harness-anchors.py --self-check --floor 458    rc=0
python3 docs/reviews/check-landing-published.py                      rc=0
python3 docs/reviews/check-no-errexit.py                             rc=0
python3 docs/reviews/check-no-sigpipe-pipelines.py                   rc=0
bash    docs/reviews/check-harness-result.sh                         rc=0
uv run --frozen python docs/reviews/check-checkers-are-wired.py      rc=0
python3 docs/reviews/check-row-floors.py                             rc=0
python3 docs/reviews/check-row-floor-exactness.py                    rc=0
bash    docs/reviews/control-stranded-mutation.sh                    rc=0
python3 docs/reviews/check-design-freeze.py                          rc=0
python3 docs/reviews/check-design-citations.py                       rc=0
python3 docs/reviews/check-design-citation-shape.py                  rc=0
python3 docs/reviews/check-coupling.py docs/DESIGN.md                rc=0
python3 docs/reviews/check-env-vars-are-declared.py                  rc=0
python3 scripts/check-committed-file-types.py --all                  rc=0
python3 scripts/check-timeout-literals.py                            rc=0
uv run --frozen pre-commit run --files <both touched files>          rc=0
uv run --frozen pytest --cov --cov-report=term-missing \
                       --cov-report=json                             rc=0
    887 passed, 6 deselected, 0 failed, 0 skipped. Floor 887: MET.
    Coverage 97.01% against a required 80.0%.
bash scripts/ci-harness-gate.sh check-u1-boot-amputation.sh \
     --amputation --min-rows 14 --row-re '^########## [A-N]\. '      rc=0
    HARNESS-RESULT name=check-u1-boot-amputation.sh rows=15 floor=0 status=ok
    HARNESS-RESULT name=ci-harness-gate.sh          rows=1  floor=0 status=ok
```

`check-harness-anchors.py` is the one to look at twice: **458 before and 458
after**, which is what says the new checks did not cost an anchor. C5 explains
why that was a live risk rather than a formality.

**`ci.yml:1468`'s gate now derives `DID NOT LAND` from this file** in addition
to `anchor is not unique`, and a clean run prints neither, so the phrase loop
stays silent on green and speaks on a moved anchor.

**AN INSTRUMENT ERROR OF MINE, CAUGHT AND CORRECTED.** The first full-suite
run reported **1 failed, 886 passed** -
`test_python_dash_m_gets_the_same_configured_sink`, which is row M's declared
`MUST_DIE` id. It was not a regression: I had launched `pytest` and the
harness gate **concurrently in the same worktree**, and the harness owns
`src/fast_mcp_jobvite/__main__.py` for the length of its run. The suite read a
mutated tree. Re-run alone: 887 passed, rc=0. The tree was clean afterwards
(`git status --porcelain` showed no `src/` entry), so nothing was stranded -
but the failing name pointed straight at my own change and would have been
very easy to write up as one.

---

## 7. WHAT I COULD NOT SETTLE, as distinct from what I did not attempt

**Could not settle:**

- **How many anchors R1 hides repo-wide.** I measured this one file exactly
  (12 seen, 15 real operations, 3 shapes invisible). Deriving the same across
  37 files needs a second parser that reads the shapes the first one cannot,
  and a parser written to find what another parser misses is exactly the
  instrument that wants its own control. Out of scope here.
- **Whether any survivor this harness has previously named was an artefact.**
  The brief says every past survivor is suspect until the guard exists. That
  is a claim about runs I cannot re-run: the transcripts in
  `docs/worklogs/HARNESS-INTEGRITY-REPORT.md` and `FIX-M5-L1-REPORT.md` record
  outcomes, not the tree state at each row. What I can say is narrower and
  is now true going forward: no future survivor from this file can be one.

**Did not attempt:**

- **The other 36 harnesses** (§D, R2). One file read completely.
- **Rebasing onto `main`.** This branch is cut from `ccbdaae`; `main` has moved
  since (#161 landed at `2d886a4`). Tier 0 merges, so I left it where it was
  cut rather than moving a branch under a merge queue I do not own.
- Publishing an `applied=` tally (C4 - it would be a fabricated N/N).
- Any change to `ci.yml`, the mirror workflow, `ci-harness-gate.sh`,
  `check-harness-anchors.py`, or the other 36 harnesses.
