# HARNESS-GATES - tasks #27 and #29

Agent `harness-gates`. Branch `fix/harness-gates`, based on `eb4d254`. Worktree `/tmp/gates-work`,
removed at the end of the run. Five commits, all on the branch; nothing pushed.

Everything below is a measurement taken in this worktree, and every command quoted was run.

---

## 1. The stale-anchor count, which is what the brief asked for first

**154 anchors across 12 of the 15 harnesses. ONE was stale.** Measured with
`scripts/check-harness-anchors.py`, written for this, before any of it was fixed.

```
check-suite-floor-amputation.sh      anchors=  4
check-u1-boot-amputation.sh          anchors= 12
check-u1-boot-controls.sh            anchors= 20
check-u11-advisory-controls.sh       anchors= 15
check-u15-gate-amputation.sh         anchors=  4
check-u15-gate-controls.sh           anchors= 15
check-u3-audit-amputation.sh         anchors= 10
check-u3-audit-controls.sh           anchors= 15
check-u4-client-amputation.sh        anchors= 17
check-u4-client-controls.sh          anchors= 19
check-u5-jobs-amputation.sh          anchors= 11
check-u5-jobs-controls.sh            anchors= 12
anchors resolved: 154
STALE ANCHOR  check-u4-client-amputation.sh:160 [shell-arg]  0 hits in
              src/fast_mcp_jobvite/services/jobvite_client.py (need exactly 1)
    anchor: '    if text.startswith("<"):' ...
```

Three carry no anchors, and none is a defect: `check-suite-floor.sh` is the *subject* of a harness
rather than one, `check-u1-pid1-shutdown.sh` is a Docker reproducer, and
`check-u0-test-controls.sh` mutates with `sed -i` expressions the checker cannot read - it is
**named on every run** rather than counted as a clean zero (§5).

### The stale one, and why it is the same failure as B49b

U4's amputation row A5 anchored on three lines, one of which was a comment:

```
  '    if text.startswith("<"):
        # Markup: the Tomcat HTML page, or HR-XML. Neither is ever a success.
        _raise_from_markup(http_status, text)'
```

`jobvite_client.py:310-313` now reads `# success.` on its own line. The comment was rewrapped, the
anchor matched nothing, and **A5 has been applying to nothing.** Amputation rows are the instrument
that has found a vacuous assertion in every unit on this project; this one was measuring an intact
tree and reporting its survivors as findings.

CI would have caught it - the U4 amputation step greps `COULD NOT APPLY` - but only after a
multi-minute harness run, and only on the run *after* the sweep that broke it. That is precisely the
gap B49b left: main red, discovered when a passing unit tripped over it.

**Fixed by shrinking the anchor to the condition alone**, replaced with `if False:  # AMPUTATED-A5`.
The branch is unreachable, so `_raise_from_markup` is never called - the same amputation - and there
is no prose left in the anchor to rewrap. A prose line inside an anchor is a line that *will* be
reflowed.

**Suggested follow-up (nit, no ticket filed):** sweep the other 153 for prose. I did not, because
the checker now fails on the next one within milliseconds, which is cheaper than a sweep and does
not go stale.

---

## 2. The static checker: `scripts/check-harness-anchors.py`

Four anchor shapes, **all derived, none tabulated** - a hand-kept list beside its container is blind
to the member nobody adds:

| shape | where the anchor is | how the position is derived |
|---|---|---|
| `shell-arg` | argument to a shell helper | the helper's own `local id="$1" file="$2" old="$3"` line |
| `py-heredoc` | `str.replace` literal in a `python3 -` heredoc | parsed with `ast` |
| `py-regex` | `re.sub` pattern | parsed with `ast`, checked with `re.findall` under `re.S` |
| `spec-row` | `@@`-delimited spec table | the loop's own `NAME="${...@@...}"` assignments, in order |

The target file is the `file` parameter when the helper takes one, and otherwise the path in the
helper's own `python3 - "..."` invocation.

### Building it found four blind spots IN ITSELF, every one a silent zero

Not one of these raised an error. Each was found by the `--self-check` tally - call sites seen
counted *independently* of anchors parsed - and not one would have been found by reading the code:

1. **Anchors held in a local variable.** `anchor = "..."` then `s.replace(anchor, ...)`. Missed 5 of
   U1's 7 and 6 of the controls' 20.
2. **Harnesses naming their target in their own python invocation** rather than as a parameter.
   Missed all 15 of U11's.
3. **`name () {` with a space** before the parens. Missed all 4 of the suite-floor harness's.
4. **My own transitive runtime-path rule**, which turned 15 live anchors into false findings by
   emptying `TREE="$WORK/tree"` whole. Reverted; the filesystem decides instead, because
   `SCRIPT="$REPO/scripts/x.sh"` needs its literal tail kept and `TREE="$WORK/tree"` needs its
   dropped, and nothing in the assignment distinguishes them.

The fourth is the one worth keeping: it was **me producing findings in the alarming direction**, and
it looked exactly as convincing as the true one.

---

## 3. Controls on the checker: `scripts/check-harness-anchors-controls.sh` - 7/7 fired

```
  FIRED    P1 an intact tree passes (exit 0, wanted 0)
  FIRED    P2 a reflowed line inside a live anchor is caught (exit 1, wanted 1)
  FIRED    A1 the hit-count comparison is deleted (exit 0, wanted 0)
  FIRED    A2 zero hits is no longer a failure, only ambiguity is (exit 0, wanted 0)
  FIRED    A3 the shell-helper shape parses nothing (exit 0, wanted 0)
  FIRED    A4 findings are printed but the exit code ignores them (exit 0, wanted 0)
  FIRED    F1 a deleted shape passes WITHOUT the floor (exit 0) and fails WITH it (exit 1)
7/7 controls fired.
```

**This harness found a defect in the checker on its first run, which is the whole argument for
writing it.** `check-*.sh` matched the control harness itself, so the checker parsed a script that
anchors into a throwaway copy of the tree and reported its rows as findings about files that do not
exist. Worse: **P2 - the row that proves a reflowed anchor is caught - was passing for that reason
rather than for the reflow.** A green from the wrong cause is the exact shape all of this exists to
find, and only the layer above could see it.

The first fix for that was also wrong: excluding any script whose *text* mentioned the checker. A
comment I later added to `check-u15-gate-amputation.sh` - a real harness with four live anchors -
then excluded it silently, dropping 154 to 150. **A predicate over prose is a predicate any prose
can trip.** It now matches on the filename stem.

### The floor, and why the count needed one

A1-A4 break the tree and delete the rule that notices. **F1 does not touch the tree at all**: it
deletes one parser *shape*, and every anchor that still parses resolves perfectly.

```
      no floor:   anchors resolved: 139
      no floor:   OK: all 139 anchors resolve to exactly one hit in their target file.
      with floor: FAIL: only 139 anchors were resolved, below the floor of 154.
```

Fifteen rows uncovered, exit 0, no complaint. `--floor 154` lives in `ci.yml`, the one place the
suite floor lives, where lowering it is a visible diff that has to be defended.

**The floor earned itself within the hour.** My own fix to `check-u15-gate-amputation.sh` (§4) used
a loop over `(pattern, repl, label)` tuples, which moved three anchors out of `re.sub`'s arguments
and out of the parser's sight: 154 to 151, still reporting OK. The rows are written out longhand
now, with the reason in a comment beside them.

---

## 4. Task #29 - what each gap step now gates on

### The task's own list was out of date, re-measured at `eb4d254`

It was measured at `954e157`. Two rows have moved since:

- **Suite-floor amputation is no longer a gap** - its step already greps
  `DID NOT LAND|ANCHOR MISSING|ANCHOR NOT UNIQUE`.
- **U5's two steps were never in the list**, having landed after it was written. The mutation step
  was a genuine gap; the amputation step gates on `ROWS == ANCHORS APPLIED`, which detects one.

This is the third time on this project a hand-enumerated list has been overtaken by its subject, so
**the gap is now closed by construction rather than by enumeration** (below), and there is no list
to go stale.

### The vocabulary is derived, so no gate can be inoperative

Six new copies of one grep would have been worse than the gap - *a grep for a string a harness never
prints is an inoperative gate, and it looks like coverage.* Instead `scripts/ci-harness-gate.sh`
reads each harness's **own source**, keeps the anchor-failure phrases that actually appear in it,
and greps the log for exactly those. Measured, per harness:

```
check-u0-test-controls.sh         STAGING ERROR
check-u1-boot-amputation.sh       anchor is not unique
check-u1-boot-controls.sh         DID NOT LAND | anchor is not unique
check-u11-advisory-controls.sh    the mutation target was not found
check-u15-gate-amputation.sh      DID NOT LAND          <- did not exist before this branch
check-u15-gate-controls.sh        MUTATION TARGET NOT FOUND | BROKEN CONTROL
check-u3-audit-*.sh               COULD NOT APPLY | DID NOT LAND | ANCHOR NOT UNIQUE
check-u4-client-*.sh              COULD NOT APPLY | DID NOT LAND | ANCHOR NOT UNIQUE
check-u5-jobs-*.sh                COULD NOT APPLY | DID NOT LAND | ANCHOR NOT UNIQUE
check-suite-floor-amputation.sh   DID NOT LAND | ANCHOR MISSING | ANCHOR NOT UNIQUE
```

**I did not unify the six phrases into one.** The brief suggested `DID NOT LAND`, and I am
disagreeing with a reason: each phrase is printed beside a *different* diagnosis (an anchor that
matched nothing, one that matched twice, a write that succeeded and changed nothing), and
collapsing them re-creates one layer down the exact defect the U1 step's three exit codes exist to
avoid - a message that misdescribes what happened sends the next reader to the wrong place. Deriving
the grep from the source gets uniform gating **without** flattening the diagnosis. If you want the
unification anyway, say so and it is a small follow-up.

### The sharpest item, confirmed and fixed

`check-u15-gate-amputation.sh` had **no anchor-failure vocabulary whatsoever**, and the cause is
worse than the symptom: it amputates with `re.sub`, which **returns the string unchanged and raises
nothing when it matches nothing**. A row with a moved anchor would run against an *intact* tree,
print a survivor list of pure false findings, exit 0, and no step could gate on it because it
printed no phrase to gate on.

Both rows now assert that the amputation landed. Row D asserts its **three tables separately** -
asserting only "the file changed" passes with two of the three still populated, and the row would
report that an empty rule table is caught while two thirds of the rules were intact.

Positive control, both arms, run against a copy:

```
  intact-anchor exit=0
  C: AMPUTATION DID NOT LAND - the classify() anchor moved. Fix the harness.
  moved-anchor exit=1
```

```
  intact exit=0
  D: AMPUTATION DID NOT LAND - the MAGIC anchor moved. Fix the harness.
  moved-MAGIC exit=1
```

The `python3 ... <<'PY'` blocks are followed by `[ $? -eq 0 ] || exit 1`. **The message alone is not
the gate** - without that line the row prints its diagnosis and then runs `report` anyway, which is
the failure sitting one line below its own description.

---

## 5. Task #27 - the extraction, and the scope decision

**`scripts/ci-harness-gate.sh`, called by all thirteen harness steps. My decision, stated here and
in the file's header.**

Converting one step would have left the file inconsistent for no gain. More to the point, the
sibling steps were near-identical copies of one another already, and that is exactly how U3's and
U4's mutation steps both shipped the same anchor blindness and had to be found and fixed twice,
separately. One artefact cannot do that. The non-harness steps (lint, format, types, the licence
gate) stay inline: they are single commands, and inline is the right form for a single command.

**No twin was committed.** The previous agent's refusal to commit a hand-copied gate was right and
is honoured: the thing the controls exercise is the real `ci-harness-gate.sh`, copied unmodified
into a scratch tree and invoked as CI invokes it, with only its *subject* substituted.

Run end to end against a real harness, and the tree was clean afterwards:

```
gate vocabulary for check-suite-floor-amputation.sh (derived from its source):
  DID NOT LAND ANCHOR MISSING ANCHOR NOT UNIQUE
  KILLED   A1 ... A4
4/4 amputations killed a test.
post-run re-check of the real script: exit=0
GATE EXIT=0
```

### Controls on the extracted gate: 23/23 fired

The brief asked for a recorded log with an `UNEXPECTED SURVIVOR` requiring exit 1; that is C5. The
gate runs its harness rather than reading a log, so each row substitutes a **stub harness replaying
recorded output** at a chosen exit code - the arms worth testing are the ones a healthy repository
never produces, and waiting for a real harness to fail is not a test plan.

```
  C1  a clean mutation harness passes                                  exit 0
  C2  COULD NOT APPLY is caught even though the harness exited 0       exit 1
  C3  DID NOT LAND is caught even though the harness exited 0          exit 1
  C4  a harness with no anchor-failure vocabulary is REFUSED           exit 2
  C5  an amputation exit 1 is a FINDING, not a pass                    exit 1
  C6  an amputation exit 3 is could-not-run                            exit 1
  C7  any other non-zero exit fails                                    exit 1
  C8  TIMED OUT is caught                                              exit 1
  C9  all controls fired passes                                        exit 0
  C10 13 of 14 fired is caught                                         exit 1
  C11 zero controls held is caught, though 0 == 0                      exit 1
  C12 a missing 'N/M controls fired.' line is caught                   exit 1
  C13 a surviving mutation is caught                                   exit 1
  C14 zero mutations killed is caught, though 0 survived               exit 1
  C15 every anchor applied passes                                      exit 0
  C16 9 of 11 anchors applied is caught                                exit 1
  C17 enough rows passes                                               exit 0
  C18 a vanished row is caught                                         exit 1
  C19 a suffixed row id is INVISIBLE to the naive pattern              exit 1
  C20 and visible to the corrected one                                 exit 0
  C21 the restore line present passes                                  exit 0
  C22 a missing restore line is caught                                 exit 1
  C23 a harness that does not exist is refused                         exit 2
23/23 controls fired.
```

C11 and C14 are the rows where **equality passes on nothing** - `0/0 controls fired.` and
`0 killed, 0 not killed` both satisfy every comparison. C19/C20 are U4's suffixed-row lesson from
both sides, as a **negative control**: the naive pattern must NOT count `A9b`.

Two defects found by running them, both in the controls rather than the gate: `printf %q`
backslash-escaped the recorded phrases so no `grep -F` could see them (21 of 23 rows refused for
want of a vocabulary that was there all along, in a form invisible to inspection but not to
execution), and the lines meant to *supply* vocabulary were being **printed**, which tripped the
very anchor gate they were enabling.

### CONTRIBUTING.md

Its local-gate list was a hand-typed twin of these thirteen steps. It is now **derived from
`ci.yml`** by a grep that I ran and that returns all thirteen. The four multi-line steps were
collapsed to one line each so the derived listing carries the **whole** invocation - a local run
that silently dropped `--min-rows` would gate on less than CI while looking like the same command.
One step must be a **quoted** YAML scalar because its `--require` pattern contains `": "`, which a
plain scalar reads as a mapping; measured, the file stopped parsing entirely.

---

## 6. Concurrency, and the two traps

- **Nothing was touched in the shared checkout.** All work in `git worktree add /tmp/gates-work
  eb4d254`; `git worktree list` checked first (`/tmp/bash-work` on `chore/bash-standard` noted and
  avoided). The worktree is removed.
- **`git status` after every harness run**, and it was clean every time. No `git add -A` while a
  harness was live.
- **`cmp` against a backup, never `git diff`**, for every landing check in the new harnesses - the
  copies are untracked and `git diff` reports no difference for an untracked file whatever it
  contains.
- **I did not touch any `set -uo pipefail` line and did not add a shellcheck step** - that is
  `bash-standard`'s task #24. The four scripts I wrote or edited pass `bash -n`. **shellcheck is not
  installed in this worktree**, so they are unchecked by it; `bash-standard` should run it over
  `scripts/ci-harness-gate.sh`, `scripts/ci-harness-gate-controls.sh` and
  `scripts/check-harness-anchors-controls.sh`, which are new since its measurement.

---

## 7. Suggested follow-ups, each with its fix

1. **`check-u0-test-controls.sh` mutates with `sed -i`, so its rows have no statically readable
   anchor.** *Fix:* teach the checker a fifth shape by parsing the `s/OLD/NEW/` and `/PAT/d`
   expressions out of the command strings, or convert the harness to the `@@`-spec form U15 already
   uses. Until then the checker **names it on every run** under `UNREAD MUTATION MECHANISMS`, so it
   cannot pass as a clean zero.
2. **The vocabulary list in `ci-harness-gate.sh` is the one hand-kept list left.** A harness that
   invents a tenth phrase gets no gate from it. *Fix:* it is covered from the other side - the
   static checker reads that harness's anchors regardless of what it prints - but if you want it
   airtight, add a control asserting every `echo` in a harness that mentions an anchor uses a listed
   phrase.
3. **The `--floor 154` will need raising** whenever a harness gains rows. *Fix:* that is the
   intended cost, the same as the suite floor; the failure message says what to do.

---

## 8. What I did NOT verify

These are things I could not settle here, not things I skipped.

- **I did not run the twelve other harness gates end to end.** Only
  `check-suite-floor-amputation.sh` was run through `ci-harness-gate.sh` in full (4/4 killed, tree
  clean). The rest each run a pytest suite per row and take minutes to tens of minutes, and running
  thirteen of them serially in a worktree while `bash-standard` was live on the same repository was
  a risk I judged worse than the gap. **The gate's logic is covered by 23 controls; what is
  unverified is the pairing of each step's flags to each harness's actual output format.** I derived
  those flags from the assertions the previous inline steps made, which is a transcription and
  transcriptions are where this project keeps finding defects. **This is the thing I most want CI to
  confirm, and it is the first thing to look at if a step goes red.**
- **The full `pytest` suite was not run.** I changed no Python that any test imports - one new
  standalone script, plus shell and YAML - but I did not confirm that by running it. `ruff check .`
  ("All checks passed!"), `ruff format --check .` ("61 files already formatted") and `mypy`
  ("Success: no issues found in 43 source files") **were** run, over the whole repo, and are clean.
- **shellcheck** - not installed, as above.

### And one I listed here first, then settled, which is the lesson

I had written "ruff was not run" into this section as though it were something I could not settle.
It was two minutes. **`scripts/` is in ruff's scope - only `docs` is excluded - and the new file had
113 errors**, so the branch would have turned CI red on the lint step. 88 of them were **W505,
doc-line-too-long at 72**, in a file whose entire subject is that reflowed prose breaks anchors.

One was not cosmetic: **B023**, a closure over `assigned`, a dict rebound once per heredoc. It is
called inside its own iteration today, so the behaviour was correct - correct *by accident*, which
is the shape that survives review and breaks under the next edit. Bound as a default argument.

The reformat itself then acted as a small positive control: it rewrote the file the controls harness
amputates **by text**, and the controls still reported 7/7. Had the reformat moved those anchors,
they would have said `DID NOT LAND` - which is the whole thesis of this branch, arriving unbidden.

**The unverified list is for what I could not settle, not for what I did not try.**
- **Whether `--floor 154` is right for `main` rather than for `eb4d254`.** If anything landed on
  main that adds or removes anchors, the floor is wrong in one direction or the other. Re-run
  `python3 scripts/check-harness-anchors.py --self-check` after merging and adjust the one number in
  `ci.yml`.
**`docs/reviews/check-obligations.py` WAS run**, verbatim output:

```
Mappings: 29  |  anchors verified against their subject: 22  |  recorded as absent: 7
Every mapped anchor still contains its subject. OK.
```

Exit 0. Nothing I changed moves an obligation anchor.
