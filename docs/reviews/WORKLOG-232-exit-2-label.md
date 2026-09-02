# WORKLOG #232 - the caller conflated exit 2 with exit 1, and so do three of its siblings

Agent: `suborch-232`. Branch `fix/232-exit-2-label`, off `main` at `c263767`
(derived with `git rev-parse main`, not typed from the brief).
Worktree `/tmp/w232-exit-2-label`, LEFT IN PLACE as instructed.

## Headline

**The defect is real, reproduced before it was changed, and #221's suggested
hunk is SUFFICIENT - it was adopted unmodified apart from a comment.**

**And it is not one step. Three OTHER `ci.yml` steps reproduce the identical
conflation, all three confirmed by running them, none of them the sibling the
brief predicted.** `check-coverage-floors.py` - the one the brief named - does
NOT conflate: its caller is a bare invocation with no message of its own.

**The actionlint gap in the brief is CLOSED, not carried.** actionlint is
genuinely not installed on this machine, but `ci.yml` itself documents how CI
acquires it, and that recipe works here. The hunk has now been linted.

## 1. The defect, reproduced BEFORE any change

The step body was extracted from `ci.yml` programmatically (not retyped) and
executed standalone under `/usr/bin/bash -e`, which is the interpreter GitHub
uses for a `run:` block.

`.venv` absent, CURRENT body, verbatim tail of the output:

    /tmp/w232-exit-2-label/.venv/bin/python does not exist, so the plan probes have no interpreter
    carrying this project's dependencies. Run:
        uv sync --frozen
    ...
    ::error::a measurement the plan rests a decision on no longer holds
    EXIT=1

The checker says the environment is unmet. The step says a plan claim is stale.
That is the defect: an unmet PRECONDITION reported in the words reserved for a
failed SUBJECT.

**Correction to the task description.** It cites `ci.yml:674`. On `c263767` the
line is **668** (`grep -n`), and the invocation is at **665**. The task's number
was correct when written and drifted.

## 2. Six-cell truth table, current body vs proposed body

To vary the exit code without varying anything else, `python3` was shadowed by a
stub earlier on `PATH` that returns 0, 1 or 2 with representative output. The
step body is byte-identical across all six cells.

| body | checker rc | step exit | `::error::` printed |
|---|---|---|---|
| CURRENT | 0 | 0 | (none) |
| CURRENT | 1 | 1 | a measurement ... no longer holds |
| CURRENT | 2 | 1 | **a measurement ... no longer holds** (WRONG) |
| PROPOSED | 0 | 0 | (none) |
| PROPOSED | 1 | 1 | a measurement ... no longer holds |
| PROPOSED | 2 | 1 | the plan probes had no venv ... run uv sync --frozen |

The proposed hunk changes exactly one cell and regresses neither of the others.

**And with the REAL checker, not a stub, in both tree states:**

    CURRENT  body, .venv present -> exit 0, four [PASS] rows
    CURRENT  body, .venv absent  -> exit 1, "a measurement ... no longer holds"   <- defect
    FIXED    body, .venv present -> exit 0, four [PASS] rows
    FIXED    body, .venv absent  -> exit 1, "the plan probes had no venv ..."

The venv was parked with `mv` and restored, and `.venv/bin/python` was confirmed
present again afterwards.

## 3. VERDICT ON #221's HUNK: sufficient, and it matches a precedent in the file

Adopted as offered. Two things settle it:

1. The truth table above: it fixes rc=2 and leaves rc=0 and rc=1 alone.
2. **`ci.yml` already contains this exact shape**, at the standards-citations
   step: `if [ "$rc" -eq 2 ]; then ... fi` placed BEFORE the `if [ "$rc" -ne 0 ]`
   branch. Adopting the same ordering keeps one shape in the file rather than
   inventing a second.

A comment was added above the branch stating why exit 2 is not a verdict and
naming the precedent, so the next reader does not have to rediscover it.

**Residual, stated rather than fixed.** With the hunk in, an UNEXPECTED code -
say 127 if `python3` were missing - still reaches the `-ne 0` branch and gets the
stale-claim sentence. The checker defines exactly 0, 1 and 2, so this is
unreachable through the checker itself. The precedent step at
standards-citations has the identical residual, and matching it was judged worth
more than a novel catch-all. Recorded here so it is visible, not silent.

## 4. THE SIBLING SWEEP - the part the brief asked for, and it found three more

### The population, and my FIRST instrument was wrong

A naive selector (`sys.exit(N)`, `exit N`, `EXIT_* = N` for N>=2) over the 45
distinct script paths `ci.yml` references returned **15** exit-2-capable
checkers - **and it missed `check-coverage-floors.py`, the one the brief names.**
That script reaches exit 2 by `return 2` inside `main()`, with
`sys.exit(main())` at the bottom. Widening the selector to include a bare
`return N` line took the count **15 -> 27**. The naive number was short by
twelve, and it was short in exactly the file the brief pointed at.

`ci.yml` references 45 distinct script paths; all 45 resolve on disk (checked,
because a search at a path that does not exist exits clean-empty).

### The discriminator

A step is defective only when BOTH hold:

- the script it calls has a code >= 2 meaning **an unmet precondition** - it
  could not judge - and
- the calling step prints a **subject-specific** `::error::` sentence for every
  nonzero code.

A bare `run: python3 check-x.py` with no message of its own cannot conflate: the
script's own text and its raw exit code are what CI shows. A caller whose
message NAMES BOTH modes does not conflate either.

### Result: 60 calling steps, 4 conflate

**CONFLATING (all four reproduced by running, none reasoned about):**

| ci.yml | script | what exit 2 MEANS | what the step SAYS |
|---|---|---|---|
| :665/:668 (pre-fix) | `check-plan-measurements.py` | `.venv` absent, nothing measured | "a measurement the plan rests a decision on no longer holds" |
| :1575/:1578 | `check-adr-numbers.py` | "NO ADR DIRECTORY at ... Exiting 2, not 0." | "two ADRs share a number, a number is missing, or a heading disagrees" |
| :1620/:1621 | `check-pytest-bounded.sh` | "MATCHED ZERO pytest invocations. The selector is broken" (`status=refused`) | "a pytest invocation runs unbounded; see #108" |
| :1630/:1631 | `check-committed-file-types.py` | "gate FAILED TO RUN" / "CRASHED", failing closed | "a tracked file fails the committed-file-type gate" |

Line numbers are pre-fix, from `grep -n` on `c263767`. After this branch's
12-line insertion the three siblings sit at **:1590**, **:1633** and **:1643**.

Each sibling was measured by driving the real script to a real exit 2 and then
running the real step body over it under `/usr/bin/bash -e`:

- **ADR.** A scratch tree holding only `docs/reviews/check-adr-numbers.py`, with
  no `docs/adr/`. Raw: `NO ADR DIRECTORY at /tmp/sib232/docs/adr. Exiting 2, not 0.`
  rc=2. Step body: prints `::error::two ADRs share a number, a number is
  missing, or a heading disagrees`, exit 1.
- **pytest-bounded.** An empty git repo holding only the harness and its
  `harness-result.sh`, so `git ls-files` yields a zero population. Raw:
  `MATCHED ZERO pytest invocations. The selector is broken`, `status=refused`,
  rc=2. Step body: `::error::a pytest invocation runs unbounded; see #108`,
  exit 1. **This one is the worst of the three** - it points the reader at a
  ticket about unbounded calls when the actual condition is that the selector
  found nothing at all, which is the exact "clean zero" failure the harness's
  own comment says the refusal exists to prevent.
- **committed-file-types.** A non-git directory, so `git ls-files -z` exits 128
  and `GateError` fires. Raw: `committed-file-type gate FAILED TO RUN: git
  ls-files -z exited 128 ...` / `Failing closed`, rc=2. Step body:
  `::error::a tracked file fails the committed-file-type gate`, exit 1.

**NOT CONFLATING - and this is why a blanket rewrite would have been wrong:**

- **`ci.yml:488` standards-citations.** Already tests `rc -eq 2` before its
  `-ne 0` branch, and treats it as a configured non-run with a `::warning::` and
  `exit 0`. **This is the precedent the fix copies.**
- **`ci.yml:1807` dependency audit.** `check_advisories.py` has
  `EXIT_CANNOT_RUN = 2` for a malformed advisory table, and the caller's sentence
  is "the advisory table is invalid **or** an entry expired" - it names both
  modes. Correct as written. Changing it would have been a regression.
- **`ci.yml:1744` secret-scan controls.** `python3 ... --controls || exit 1`
  with no message of its own; the script's text surfaces unaltered.
- **`ci.yml:997` `check-suite-floor.sh 887`.** Its exit 2 is a usage error on a
  non-integer argument, and the argument is a literal. No `::error::` attached.
- **`ci.yml:1876` `check-coverage-floors.py` - the sibling the brief predicted.**
  It is a BARE `run: python3 docs/reviews/check-coverage-floors.py`. Its four
  exit-2 messages reach the log verbatim and nothing overwrites them. **The
  brief's premise that an exit-2-capable checker has a calling step is TRUE; its
  implication that THAT step conflates is not.**
- The remaining ~50 sites are bare invocations, `ci-harness-gate.sh <name>`
  wrappers, or `|| exit 1` with no sentence. Nothing to conflate.

So the sweep is 27 exit-2-capable scripts, 60 calling steps, **4 defective and
56 correct**. Rewriting every caller with an `rc -eq 2` branch would have
touched 56 steps that are already right and would have broken at least one
(`:1807`, whose message is deliberately two-sided).

### Scope decision

**I fixed ONE step and REPORTED three.** `PROTOCOL-sub-orchestrators.md` and
PREAMBLE say out-of-scope work is reported, never silently fixed, and my brief
grants no `TaskCreate` mandate. `ci.yml` is Tier 0's file and #221 handed the
step over rather than editing it. Each of the three ships a ready hunk below, so
adopting them costs a paste, not a re-diagnosis.

**Suggested fix, ADR step** - insert immediately after `echo "$out"`:

    if [ "$rc" -eq 2 ]; then
      echo "::error::there is no docs/adr directory, so no ADR numbering was checked"; exit 1
    fi

**Suggested fix, pytest-bounded step** - replace the second invocation's `||`
block with an `rc` read, because the current form cannot see the code at all:

    set +e
    bash scripts/check-pytest-bounded.sh; rc=$?
    set -e
    if [ "$rc" -eq 2 ]; then
      echo "::error::the bounded-pytest selector matched ZERO invocations; nothing was judged"; exit 1
    fi
    if [ "$rc" -ne 0 ]; then
      echo "::error::a pytest invocation runs unbounded; see #108"; exit 1
    fi

**Suggested fix, committed-file-types step** - same shape:

    set +e
    scripts/check-committed-file-types.py --all; rc=$?
    set -e
    if [ "$rc" -eq 2 ]; then
      echo "::error::the committed-file-type gate could not run; it failed closed, nothing was judged"; exit 1
    fi
    if [ "$rc" -ne 0 ]; then
      echo "::error::a tracked file fails the committed-file-type gate"; exit 1
    fi

**These three hunks have NOT been run** - only the current bodies were, to prove
the defect. They are suggestions, and this project's record says a suggested
remedy gets measured before it is adopted.

## 5. On "not urgent" - the brief asked me to challenge this, and it holds

The brief rests its priority on ONE read of ONE green run's log. I did not find
a path where the runner reaches exit 2 on the plan-measurements step:
`uv sync` creates `.venv` before the step, and #221 read that from run
`33582613697` directly. I did not re-fetch the log.

**But the sibling sweep changes the shape of the answer.** Two of the three
siblings CAN reach exit 2 from a plausible runner state:

- `check-committed-file-types.py` exits 2 on any `git ls-files` failure - a
  shallow or corrupt checkout, not an exotic condition - and the step would then
  say a tracked file is bad when the gate never ran.
- `check-pytest-bounded.sh` exits 2 if its selector ever stops matching, which
  is precisely what happens when someone renames a directory. The step would
  then blame an unbounded pytest call.

Neither is urgent either. But "the runner never reaches exit 2" is a claim about
ONE checker, and it does not generalise to the other three.

## 6. actionlint - the gap the brief called first-class, now CLOSED

`actionlint` is not installed on this machine (`command -v actionlint` -> not
found). **But `ci.yml`'s own lint step names the version, URL and sha256**, and
that recipe runs here:

    ver=1.7.7 ; sha=023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757
    curl -fsSL .../actionlint_1.7.7_linux_amd64.tar.gz -o /tmp/actionlint.tgz
    echo "${sha}  /tmp/actionlint.tgz" | sha256sum -c -    # -> OK
    tar -xzf /tmp/actionlint.tgz -C /tmp actionlint

`shellcheck 0.10.0` is present at `~/.local/bin/shellcheck`, so the
`SHELLCHECK_OPTS=--severity=warning` half is live too, not silently skipped.

    BEFORE the edit: SHELLCHECK_OPTS=--severity=warning /tmp/actionlint -no-color  -> rc 0
    AFTER  the edit: SHELLCHECK_OPTS=--severity=warning /tmp/actionlint -no-color  -> rc 0

**So the hunk HAS been linted, by CI's exact invocation, with a green baseline
taken first so the zero is not vacuous.** #221 said its hunk had never been
linted and that was true of #221; it is no longer true of this branch. The
brief's "any `ci.yml` hunk you write has never been linted" is therefore
CORRECTED rather than repeated.

What actionlint still cannot tell me is whether the step behaves on a real
runner. That remains unverified - see below.

## 7. Gates, each judged by exit code on its own line

Both floors DERIVED from `ci.yml`, not typed: `check-suite-floor.sh 887`,
`--self-check --floor 464`.

| gate | command | exit | result |
|---|---|---|---|
| workflow lint | `SHELLCHECK_OPTS=--severity=warning /tmp/actionlint -no-color` | 0 | clean, and clean at baseline too |
| lint | `uv run --frozen ruff check .` | 0 | All checks passed! |
| format | `uv run --frozen ruff format --check .` | 0 | 143 files already formatted |
| types | `uv run --frozen mypy .` | 0 | Success: no issues found in 143 source files |
| suite | `uv run --frozen pytest` | 0 | **887 passed, 0 skipped**, 6 deselected, 53.61s |
| anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 464` | 0 | 464 anchors, 35 harnesses |
| wiring | `uv run --frozen python docs/reviews/check-checkers-are-wired.py` | 0 | |
| row floors | `python3 docs/reviews/check-row-floors.py` | 0 | |
| floor exactness | `python3 docs/reviews/check-row-floor-exactness.py` | 0 | |
| timeout literals | `uv run --frozen python scripts/check-timeout-literals.py` | 0 | |
| sigpipe | `python3 docs/reviews/check-no-sigpipe-pipelines.py` | 0 | |
| landing published | `python3 docs/reviews/check-landing-published.py` | 0 | |
| design freeze | `python3 docs/reviews/check-design-freeze.py` | 0 | |
| design citations | `python3 docs/reviews/check-design-citations.py` | 0 | |
| no-errexit | `python3 docs/reviews/check-no-errexit.py` | 0 | |
| coupling | `python3 docs/reviews/check-coupling.py docs/DESIGN.md` | 0 | |
| obligations | `python3 docs/reviews/check-obligations.py` | 0 | |

The suite meets 887 exactly with zero skips.

**#221's inherited red is GONE.** It reported `ci.yml:265`
`check-no-errexit.py` exiting 1 on `probe-stale-branch-regression.sh:50`. On
`c263767` that checker exits **0**. Fixed by someone between #221's base and
now; recorded because #221's worklog still says `main` is red and a reader would
otherwise carry that forward.

The seven checkers that parse `ci.yml` were run specifically because this branch
inserts 12 lines into it and a line-numbered anchor could have drifted. None did.

## 8. What I did NOT verify

- **The three sibling hunks in §4.** I ran the CURRENT bodies to prove they
  conflate; I did not run the SUGGESTED replacements, and two of them change the
  invocation shape from `|| { ... }` to an `rc` read. They are unmeasured
  suggestions and should be treated as such.
- **CI itself.** Nothing on this branch has run on a GitHub runner. actionlint
  parses the workflow, which is more than #221 had, but it is not execution.
- **The green run's log.** I did not re-fetch `33582613697`. My statement that
  `.venv` always exists on the runner is #221's read, carried, not re-taken.
- **`check-coverage-floors.py`'s exit 2 was not TRIGGERED.** I read its four
  `return 2` branches and its caller; I did not construct a missing
  `coverage.json`. The verdict "its bare caller cannot conflate" is a property of
  the CALLER and holds regardless, but the script's side is read, not run.
- **Whether the 45 script paths are the complete population of ci.yml
  invocations.** They are what a path-shaped regex over `ci.yml` finds. A step
  that builds a script path from a variable would be invisible to it. I checked
  that all 45 resolve on disk; I did not prove no 46th exists by another
  mechanism - and my first selector already under-reported by twelve once.
- **`ci-harness-gate.sh`'s own exit 2.** It is exit-2-capable and appears at 25
  call sites, all bare `run:` lines with no message. I classified them all as
  non-conflating from the absence of an `::error::` in the step, without reading
  what the gate's exit 2 means. If it has a message-bearing caller anywhere I
  did not find it, that classification is where the gap would be.

## 9. Merge

One commit on `fix/232-exit-2-label`, off `main` at `c263767`. `main` has moved
under agents repeatedly tonight, so if this refuses, rebase - do not force:

    git -C /home/plafayette/claude_projects/evolv/repos/fast-mcp-jobvite \
        merge --ff-only fix/232-exit-2-label

Worktree `/tmp/w232-exit-2-label` LEFT IN PLACE as instructed. The three scratch
trees used for the sibling arms (`/tmp/sib232`, `/tmp/empty232`, `/tmp/nogit232`)
are throwaway and hold no work.
