# ADR-0023: the harnesses run `set -uo pipefail`, where `bash.md:40` mandates `set -euo pipefail`

**Status:** Accepted (orchestrator, 2026-08-29)
**Type:** Standards deviation

> Fifteen scripts in `scripts/*.sh` omit `-e` from the strict-mode line that
> `standards/devops/bash.md` makes mandatory. This ADR records that as a **deviation, not
> compliance**: the clause admits no exception, and the standard's own prescribed remedy for
> commands allowed to fail is a different one than the one taken here. The deviation is accepted
> because `-e` does not merely inconvenience these scripts - it makes their central measurement
> unreadable and strands mutations in the working tree.

## Context

### The clause, quoted at source

`standards/devops/bash.md` is `priority: required`, `applicable_to: [bash, shell, ci-cd,
automation]`, version 1.0.2. Lines 36-41:

> Every script MUST begin with:
>
> ```bash
> #!/usr/bin/env bash
> set -euo pipefail
> ```

and the table immediately below it, `:43-47`:

> | Flag | Effect |
> |------|--------|
> | `-e` | Exit immediately on non-zero return |
> | `-u` | Treat unset variables as errors |
> | `-o pipefail` | Pipe fails if any command in chain fails |

**There is no exception clause.** The whole document was searched for one - every occurrence of
`set -e`, `set +e`, `errexit`, `exit code` and `$?` was read. The nearest thing to an escape hatch
is `:277-278`, and it points the other way:

> ```bash
> # Let set -e handle most failures. Use explicit checks for
> # commands that are allowed to fail.
> ```

That is the standard answering this exact question, and its answer is: **keep `-e`, and guard the
individual commands that may fail.** It does not license dropping `-e` from the file.

`:802` observes that "`set -e` has surprising edge cases", but it does so under **"When NOT to Use
Bash"** - it is an argument for writing the thing in Python, not for writing bash without `-e`.

**So this is a deviation.** A reading on which `set -uo pipefail` is compliant is not available from
the text, and this ADR does not claim one.

### What is actually in the tree, measured

Measured at `eb4d254` by grepping whole files, not headers:

```
grep -n '^set ' scripts/*.sh          -> 15 files, all `set -uo pipefail`
grep -l '^set -euo pipefail$' ...     -> 0
head -1 -q scripts/*.sh | sort -u     -> #!/usr/bin/env bash   (15/15 compliant)
```

The shebang half of `:36-41` is met by every script. Only the `-e` is missing.

*(Header-only greps are unreliable here: these files carry long comment prologues and the `set` line
sits between lines 17 and 54. A `head -12` grep reports 0 of 15 carrying any strict-mode line at
all, which is false and fits a tempting "nobody applied this standard" story.)*

### Why `-e` is not a cosmetic difference here, measured both ways

Every one of these scripts is a **control or amputation harness**. Its method is: mutate the source,
run the suite, and require the suite to go **red**. A non-zero exit from `pytest` is the
observation, not an error.

The shape they all use is `out=$(cmd); rc=$?`, or the `local out rc` variant. Twelve such sites
exist (`grep -n '=\$?' scripts/*.sh`). Under `-e`, `out=$(cmd)` is a simple command with non-zero
status, and the shell exits **before** `rc=$?` is ever evaluated.

A positive control, both arms, same body, differing only in the flag:

```
ARM A: set -uo pipefail          # what the tree does today
    captured rc=1  out=boom
    RESTORE RAN
    outer sees exit=0

ARM B: set -euo pipefail         # what bash.md:40 mandates
    outer sees exit=1
    (no rc captured, no output captured, RESTORE never ran)
```

Two distinct consequences, and the second is the serious one:

1. **The measurement is destroyed.** `rc` is never read, so the harness cannot distinguish "the
   mutation fired" from "the mutation did not fire". Every control would abort at its first
   *intended* red.
2. **The mutation is stranded in the working tree.** In `scripts/check-u1-boot-controls.sh` the
   `restore` call is at `:76`, immediately after the `rc=$?` at `:75`. Under `-e` the shell dies at
   `:73-74` and `restore` never runs - leaving the source mutated. The script's own next line
   (`:77-79`, `RESTORE FAILED - the mutation is still in the tree`, `exit 3`) exists because that
   state is recognised as serious, and `-e` would produce it silently instead of reporting it.

So adding `-e` would not turn survivors into crashes in a merely noisy way. It would leave edited
source behind on a developer's checkout.

### The compliant alternative, stated so it is a choice and not an oversight

The standard's `:277-278` remedy *is* available: keep `-e`, and rewrite each of the twelve sites as
an explicitly guarded form, e.g.

```bash
rc=0
out=$(cmd) || rc=$?
```

which is `-e`-safe, because a command on the left of `||` is exempt from `errexit`. This is a real
option and it is the standard-conformant one.

It is not taken **in this pass** for one reason: it is a twelve-site edit across fifteen harnesses
whose correctness is the thing the rest of the repository's gates depend on, and the edit is
invisible in a green run - a mis-converted site keeps passing until the day a mutation genuinely
survives. That is a change that wants its own unit with its own controls, not a rider on a
standards-coverage task.

## Decision

**Keep `set -uo pipefail` in `scripts/*.sh`, and record it here as a deviation from
`bash.md:36-41`.**

The `-u` and `-o pipefail` halves are kept and are not in question. Only `-e` is dropped, and only
in `scripts/*.sh`.

**Scope, stated by PURPOSE and not by path.** This ADR covers **anything here whose measurement is
the exit code of a command that is expected to fail** - the control and amputation harnesses in
`scripts/`, the two probes in `docs/reviews/` that this ADR and its obligation row are evidenced by,
and **the `run:` blocks in `.github/workflows/ci.yml` that call them**. Anything else in this
repository gets `set -euo pipefail` and is not covered here. This ADR is not a licence to omit `-e`
generally.

*The workflow blocks were added to this scope after it was written, and the omission is instructive.
The first draft said "any SCRIPT here", which is a rule shaped by ARTIFACT TYPE rather than by
purpose - the same error one level up from the directory-shaped draft this ADR already records
below. **Measured at `2d20ed6`: `ci.yml` has 18 multi-line `run:` blocks; 16 carry
`set -uo pipefail`, 13 capture `rc=$?` from a command expected to fail, and ZERO combine `-e` with
`rc=$?`.** So those blocks were already following this ADR's discipline while sitting outside its
stated scope - deviating from `bash.md:36-41` with no ADR covering them. The seventeenth block uses
`set -euo pipefail` and captures no exit code, which is correct and stays. The eighteenth is a single
command whose exit code IS the step's result, where a strict-mode line would add nothing.*

*Scoping this by directory was the first draft, and it was wrong within the hour: it excluded
`docs/reviews/probe-set-e-vs-harness.sh` - the probe that measures this very ADR's central claim,
and whose ARM B is expected to exit non-zero by construction. A path-shaped rule selects for the
member nobody thought of, and the member it missed here was the ADR's own evidence.*

**Every one of these scripts should say so at the `set` line.** A reader who knows `bash.md` will
otherwise read the missing `-e` as an oversight, which is exactly how a considered deviation decays
into drift. The suggested comment is one line:

```bash
# `-e` deliberately omitted: these harnesses read the exit code of a suite that
# is EXPECTED to fail. See docs/adr/0023-harnesses-drop-e-from-strict-mode.md
set -uo pipefail
```

## Consequences

- **An unguarded failure mid-harness does not abort it.** That is the accepted cost, and it is
  real: a `cp` or `mktemp` that fails silently continues into a measurement that is now meaningless.
  The harnesses mitigate this themselves rather than relying on the shell - `stage()` in
  `check-u0-test-controls.sh` asserts `git ls-files` returned a non-zero count and probes three
  files in the copy before proceeding, precisely because `-e` is not there to catch it. **That
  pattern is the obligation this deviation creates**, and a new harness that omits it is not
  covered by this ADR merely by omitting `-e`.
- **`bash.md`'s remaining clauses still bind.** This deviation is one line of one clause. In
  particular `:734` ("All scripts MUST pass ShellCheck with zero warnings") is unaffected and is
  discharged separately.
- **A future unit may convert the twelve sites to `|| rc=$?` and retire this ADR.** That is the
  preferred end state; this records why it has not happened yet rather than pretending the question
  is closed.

## What this ADR does not settle

- **It does not claim the clause admits the deviation.** It does not. If a reviewer's reading of
  `:36-41` differs, the disagreement is about whether the deviation is *warranted*, not about
  whether it is a deviation.
- **It does not enumerate the twelve sites as safe.** They were located
  (`grep -n '=\$?' scripts/*.sh`) and three were read in full. The other nine were not individually
  audited for what else `-e` would have caught in them.
- **It does not cover `ci.yml`.** `bash.md` is `applicable_to: ci-cd`, and every `run:` block in
  the workflow is shell that no strict-mode line governs at all. That is a separate and unmeasured
  gap, recorded in the report rather than decided here.

## Ruling, 2026-08-29

**ACCEPTED**, including the scope stated by PURPOSE rather than by path, and including the `ci.yml`
`run:` blocks the first draft left out.

The scoping correction is the part worth keeping. The draft said *"any SCRIPT here"* - a rule shaped
by ARTIFACT TYPE - which left 18 workflow blocks already practising this discipline while sitting
outside the ADR that authorises it, deviating from `bash.md:36-41` with nothing covering them. **A
rule named for the kind of file it applies to is a rule that misses the next kind of file**, which is
this project's most-repeated shape in a new costume.

### Re-measured at `5eb64b0`, because the ADR's evidence was taken at `2d20ed6` and I have added
### blocks to that file since

```
multi-line run: blocks      30      (was 18)
  carry `set -uo pipefail`  19      (was 16)
  capture rc=$?             16      (was 13)
  COMBINE -e WITH rc=$?      0      (was 0)
```

**The file has grown by twelve blocks and the invariant still holds at zero.** That is the number the
ADR turns on: `-e` together with `rc=$?` is the combination that makes a measurement of an expected
failure unreadable, and nothing in twelve new blocks introduced one.

The ADR is right that this is a deviation and not a licence. **`-u` and `-o pipefail` are kept
everywhere and are not in question; only `-e`, and only where the measurement IS the exit code of a
command expected to fail.** Everything else in this repository gets `set -euo pipefail`.
