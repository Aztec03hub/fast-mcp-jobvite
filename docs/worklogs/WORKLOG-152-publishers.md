# WORKLOG #152 - the tally that is computed and never printed

Branch `fix/152-publishers`, worktree `repos/fmj-worktrees/w152`, cut from
`origin/main` at `9e04411`.

## THE DISCRIMINATOR, established before anything was changed

The brief asked for one and warned that a blanket rule would be wrong. It was
right to warn: **the suggested rule is wrong on 4 of the 6 harnesses it names.**

Expected-vs-observed, both derived from the container
(`git ls-files 'scripts/*.sh'`, 38 files, 37 after removing the sourced
library `scripts/lib/harness-result.sh`):

| set | count |
|---|---|
| container (harnesses) | 37 |
| EXPECTED to publish, by the brief's shape rule (`-controls.sh` or `-amputation.sh`) | 33 |
| OBSERVED publishing a `harness_result_tally` at `9e04411` | 27 |
| EXPECTED \ OBSERVED (the difference) | **6** |
| OBSERVED \ EXPECTED | 0 |

The six: `check-body-cap-amputation.sh`, `check-suite-floor-amputation.sh`,
`check-u1-boot-amputation.sh`, `check-u15-gate-amputation.sh`,
`check-u3-audit-amputation.sh`, `check-u4-client-amputation.sh`.

**A pattern matching 6 is a SEARCH.** Reading every landing site in all 17
`-amputation.sh` files splits those 6 four ways, and only 3 are the defect:

### Kind 1 - computes a tally, gates on it, publishes nothing (the pure #152)

`check-suite-floor-amputation.sh`. Counters `fired`/`total` at `:41-42`,
incremented at `:46` and `:88`, PRINTED as prose at `:109`
(`"$fired/$total amputations killed a test."`), and GATED at `:142`
(`if [ "$fired" -ne "$total" ]` -> `exit 1`). It published no field at all, so
a tally it had all along was invisible to the #120 census, the field-name
checker and the gate's flag reader. **This is the brief's thesis exactly.**

The field is `killed=`, not `applied=`: `fired` counts amputations that KILLED
A TEST, which is the meaning `harness_result_tally killed` names. The shape
rule would have demanded the wrong field here.

### Kind 2 - computes the per-row landing outcome, does not gate it, publishes nothing

`check-u4-client-amputation.sh` and `check-u3-audit-amputation.sh`. Each row
verifies its anchor TWICE - `s.count(old) != 1` inside the heredoc, then
`git diff --quiet` against git - and each failure path is a **bare `return`**
under `set -uo pipefail`, having already incremented `HR_COUNTED_ROWS` at the
top of the row function. So `rows=` on the canonical line is identical whether
the anchor landed or not, and nothing anywhere records the difference.

**And `check-u4-client-amputation.sh:21` asserted a gate that did not exist:**

> "The CI step gates on every row having APPLIED ITS ANCHOR, not on this exit
> code."

Its CI step is `ci.yml:1310`:
`--amputation --min-rows 17 --row-re '^########## A[0-9]+[a-z]* '` - rows and
an exit code, never anchors. There was no counter, no `applied=` field and no
`--anchors-applied` on the step. The claim named the gate that would have
caught the defect, which is why it read as safe. **No gate reads a comment.**

### Kind 3 - the landing failure is FATAL, so the invariant is structural

`check-body-cap-amputation.sh` (`exit 1` at `:114` and `:120`) and
`check-u15-gate-amputation.sh` (`exit 1` at `:133`, `:140`, `:165`). A
non-landing row aborts the run, so `applied < rows` is impossible at exit 0
and an `applied=` field would be a fabricated N/N on every run.

`scripts/lib/harness-result.sh:157-162` forbids exactly that: a fabricated
`fired=0/0` "would be read by `ci-harness-gate.sh` as a harness that held zero
controls - a false finding". **These two legitimately publish nothing, and
they are the reason the sweep would have been wrong.**

### Kind 4 - the anchor failure is never CONSUMED (a different, worse defect)

`check-u1-boot-amputation.sh`. **I corrected myself here**: my first pass
recorded "no landing check at all", which was false. It DOES verify, with
`assert s.count(anchor) == 1` at `:403`, `:418`, `:441`, `:455`, `:470`,
`:471`, `:484`.

The defect is that nothing consumes the failure. The file runs **13** Python
mutation heredocs (`:308`, `:325`, `:336`, `:347`, `:359`, `:371`, `:384`,
`:399`, `:414`, `:437`, `:451`, `:465`, `:480`) under `set -uo pipefail` at
`:31` - **no errexit** - and not one is guarded by `|| exit`, `if !`, or a
`$?` read. A moved anchor prints a traceback and **the row runs against an
intact tree**, publishing survivors that are instrument artefacts.

Six of the thirteen have no `assert` at all. This is the shape
`check-u15-gate-amputation.sh:136-140` names in its own comment - "the failure
sitting one line below its own diagnosis" - and guards against with
`[ $? -eq 0 ] || exit 1`. **Out of #152's scope; raised as a finding below.**

## WHAT CHANGED

`f742da4` - the three Kind-1/Kind-2 harnesses:

- `check-suite-floor-amputation.sh` publishes `killed="$fired" "$total"`, the
  same two counters its prose line and its gate already used. No recount.
- `check-u4-client-amputation.sh` and `check-u3-audit-amputation.sh` gain
  `HR_APPLIED`, incremented only after BOTH landing checks pass, published as
  `applied="$HR_APPLIED" "$HR_COUNTED_ROWS"`.
- `check-u4-client-amputation.sh:21`'s false claim REWRITTEN IN PLACE (not
  appended to), recording that it was false and what makes it true.

`2b245d3` / `5028cae` - `docs/reviews/check-landing-published.py`.

## THE CHECKER, AND MY OWN FIRST DRAFT WAS ALSO A SEARCH

The gated invariant:

> A harness that diagnoses a per-row anchor-landing failure must not let that
> row continue silently. Either the branch is FATAL, or the harness publishes
> a named tally.

**My first draft demanded `applied=` specifically and reported 26 findings
across 14 files** - the entire `-controls.sh` family. That was a search, not a
diagnosis. A controls harness mutates to prove a control FIRES; a mutation
that does not land leaves `FIRED < TOTAL`, so the landing failure IS counted,
in `fired=`, under the only name that fits it. Demanding `applied=` there
would have forced a fourth meaning into harnesses that already report the
fact - the collapse `harness-result.sh:24-44` exists to refuse.

Narrowed to "publishes SOME named tally": **0 findings, exit 0.**

## GATE EXIT CODES, each on its own line

    python3 docs/reviews/check-landing-published.py            exit 0   (37 scanned, 30 publish a tally, 0 findings)
    uv run --frozen ruff check .                               exit 0
    uv run --frozen ruff format --check .                      exit 0
    uv run --frozen mypy                                       exit 0   (127 source files)
    bash -n on all 3 modified harnesses                        exit 0
    shellcheck --severity=warning on all 3 modified harnesses  exit 0
    ci-harness-gate.sh check-suite-floor-amputation.sh
      --amputation --require 'post-run re-check...'  (CI's line) exit 0
    ... same line + --result-killed  (the HANDOVER step)        exit 0

Both `ruff` gates were **RED** on the first draft of the checker (53 + 1
errors): W505 fires on plain `#` comments here, not only docstrings - a rule's
name is not its scope. My first reflow script then wrapped string literals
inside code and broke the file; restored from the commit and redone.

## THE ZERO IS NOT VACUOUS - three arms, all on real artefacts

    amputate suite-floor's `harness_result_tally killed` call
        -> 0 -> 1 finding, exit 0 -> 1
    amputate u4-client's `harness_result_tally applied` call
        -> 0 -> 2 findings, exit 1
    run in an empty git repo (container comes back empty)
        -> exit 2, with an ::error:: naming it an instrument failure

Both amputations were proved to have LANDED with `git diff --quiet` (not
`grep -F`), and both restores were verified clean against git afterwards. The
first two arms were re-run AFTER the reflow, because a reflow that broke the
logic would have left a passing gate testing nothing.

**Field selectivity, a C28-shaped control**: offering the new `killed=4/4`
line to `--controls-fired` (which wants `fired=`) **exits 1** with "its
controls tally was never published". The three names are not interchangeable
and my new field is not read by a flag that did not ask for it.

## THE ci.yml STEPS, WRITTEN AND MEASURED BUT NOT WIRED

`ci.yml` is owned by `suborch-143`. These are handed over, not applied. Each
is the existing line **plus one flag**; nothing else changes.

`ci.yml:1300` - suite-floor. **RUN, exit 0.**

```yaml
run: "bash scripts/ci-harness-gate.sh check-suite-floor-amputation.sh --amputation --result-killed --require 'post-run re-check of the real script: exit=0'"
```

`ci.yml:1293` - u3-audit. **RUN, see the result line below.**

```yaml
run: bash scripts/ci-harness-gate.sh check-u3-audit-amputation.sh --amputation --anchors-applied --min-rows 10 --row-re '^########## A[0-9]+ '
```

`ci.yml:1310` - u4-client. **NOT run - see "not settled".**

```yaml
run: bash scripts/ci-harness-gate.sh check-u4-client-amputation.sh --amputation --anchors-applied --min-rows 17 --row-re '^########## A[0-9]+[a-z]* '
```

Without these flags the new fields are published and read by nobody, which is
the inoperative-gate shape. **The fields and the flags must land together.**

A step for the new checker, for whenever Tier 0 rules on wiring (#153, #149):

```yaml
- name: A landing failure is never discarded
  run: python3 docs/reviews/check-landing-published.py
```

## FINDINGS RAISED, each with a suggested fix

**F1 (High) - `check-u1-boot-amputation.sh` runs 13 unguarded mutation
heredocs.** `set -uo pipefail` at `:31`, no errexit, and no `|| exit`, `if !`
or `$?` check on any of the 13 `python3 - <<'PY'` blocks. A moved anchor
prints a traceback and the row measures an INTACT tree, so every survivor it
names is an instrument artefact rather than a finding. Six of the 13 have no
`assert s.count(anchor) == 1` at all.
*Fix*: append `[ $? -eq 0 ] || exit 1` after each heredoc, exactly as
`check-u15-gate-amputation.sh:140` does, and add the missing uniqueness
asserts to the six. Then it can publish `applied=` like its siblings.

**F2 (Medium) - `VACUOUS` is computed in 10 files and published in none.** The
wider rule "every incremented counter must reach the canonical line" measures
12 of 37 files, and 11 of those are one class: `VACUOUS` (10 files) plus
`UNEXPECTED_VACUOUS` (`check-critical-coverage-amputation.sh`). A vacuity
count is a real tally, computed per row, invisible to every checker - the same
defect as #152 one concept over.
*Fix*: this needs a RULING, not a sweep. If vacuity should be published it
needs a fourth name in `harness_result_tally` and a reader in
`ci-harness-gate.sh`; `harness-result.sh:108-112` says a fifth meaning needs
both or the field is written and never read. **I did not gate this.**

**F3 (Low) - `check-u15-gate-controls.sh` increments `HELD` and publishes
`FIRED`/`TOTAL`.** `HELD` is a denominator elsewhere in the family
(`check-u11-advisory-controls.sh:242` publishes `fired "$FIRED" "$HELD"`), so
two harnesses use the name for different roles.
*Fix*: confirm which of `TOTAL`/`HELD` is the intended denominator in
`check-u15-gate-controls.sh` and make the two harnesses agree, or rename one.

**F4 (nit) - my measurement instrument had a bug worth recording.** The first
version of the incremented-counter scan extracted `$VAR` tokens from the
published arguments and therefore could not see a counter inside
`$((PASS + FAIL))`. It reported 15 files; 4 of those were the bug. Fixed by
matching identifiers rather than `$`-prefixed names: 15 -> 12.
*Fix*: already applied, in this worklog's numbers. Recorded because the
uncorrected 15 would have sent a sweep at 4 harnesses that were already right.

## WHAT I COULD NOT SETTLE (as opposed to did not attempt)

**U1 - whether a non-landing row is correctly counted by the 14 harnesses that
publish `killed=$PASS/$((PASS + FAIL))`.** A row that never landed may be
counted in NEITHER `PASS` nor `FAIL`, which would SHRINK the denominator
rather than fail the tally - a short tally that reads as a perfect one. This
is a real question about 14 files. I read 3 of them and the answer was not the
same shape in all 3, so I did not generalise. **Not gated; the checker's
docstring records it as open.** Settling it needs a run per harness.

**U2 - the u4-client gate line was not run.** `check-u4-client-amputation.sh`
holds 17 rows, each a full `uv run --frozen pytest` of the client suite with a
900s per-row timeout. I ran the suite-floor line (exit 0) and started the
u3-audit line; the u4-client line is the same shape as the u3-audit one and
the flag is identical, but **I am not claiming an exit code I did not read.**

## Worktree

`repos/fmj-worktrees/w152` is **left in place** - it holds three commits that
are not merged anywhere. Tier 0 merges; remove it after.
