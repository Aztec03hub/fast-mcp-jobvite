# docs-lint: task #103

Branch `chore/docs-lint`, off `main` at `8f5bb6f`, in the worktree
`/tmp/docs-lint-work`. Two commits, in the order the brief asked for.

    b0e2e19  An unreadable file was silently treated as NOT exempt, and repointed
    d5340b7  Take the docs/ exclusions off ruff and mypy, and sweep what they found

I did not merge and did not push. `.github/workflows/ci.yml` is untouched;
everything I would put there is in **What ci.yml needs** below.

---

## 1. The three behaviour rulings

### 1.1 `repoint-design-citations.py:64-68` - CONFIRMED fail-open. Fixed.

`parse()` reads the cited line to see whether it carries `REPOINT-EXEMPT`.
That read was wrapped in `except (OSError, IndexError, UnicodeDecodeError):
pass`, so control **fell through to the repoint**: "I could not tell whether
this line is exempt" resolved to "it is not exempt, rewrite it", in the tool
that rewrites 867 citations.

Now the unreadable lines are collected and the run refuses:

    N cited line(s) could not be read, so whether they carry REPOINT-EXEMPT
    is UNKNOWN. Refusing to repoint anything: an unknown must not resolve
    to 'not exempt'.

**Proving it end to end found a second fail-open one level up.** `report()`
kept only the checker's `.stdout`, and the checker's *normal* exit code is 1
(it exits 1 whenever moves exist), so a **crashed** checker was
indistinguishable from a clean one with nothing to move. `chmod 000` on one
cited `.md` file raises `PermissionError` inside `check-design-citations.py`
- which catches `UnicodeDecodeError` only (`:99`) - the report comes back
empty, and the repoint tool blamed **its own parser**:

    SELECTOR CONTROL: parsed 0 MOVED lines out of 0 lines of report.
    The parser is broken, or there is genuinely nothing to move.

Measured: the checker writes **0 bytes** to stderr over a run that emits 970
MOVED lines. So anything on stderr is now a refusal (`CheckerFailed`), and
the message names the real fault.

**Evidence.** `docs/reviews/probe-repoint-fail-closed.py`, 7 rows, exit 0:

    A.  missing file -> OSError is REFUSED, not repointed             PASS
    B.  line past EOF -> IndexError is REFUSED, not repointed         PASS
    C.  readable, unmarked line IS repointed (negative control)       PASS
    D.  REPOINT-EXEMPT line is skipped and is NOT called unreadable   PASS
    E0. readable baseline does NOT refuse (control on the control)    PASS
        -> "964 citation(s) repointed across 145 file(s) (DRY RUN)"
    E.  unreadable cited file -> the tool REFUSES and repoints nothing PASS
        -> rc=1, victim=docs/CODE-REVIEW-CHECKLIST.md,
           "PermissionError: [Errno 13] Permission denied: ..."
    E1. the probe restored the victim file (mode and bytes)           PASS

Rows C and D are the negative controls: a gate that refuses everything is not
a gate. Row E0 is a control on the control - the same command with the file
readable must NOT refuse, or row E proves nothing about the chmod.

### 1.2 `check-standards-citations.py:79` S110 - RULED not-a-defect. Narrowed anyway.

The swallow guards a `git rev-parse --git-common-dir` whose only job is to
**append one more candidate directory** to the corpus search list.
`candidates[0]` survives, and what the gate concludes on finding nothing does
not move - the docstring at `:61-62` says "Absence is still exit 2 and that
rule does not move." So: not a live defect.

But `except Exception` is **wider than the failure it names**. The comment
said "git absent is just one fewer candidate"; a `TypeError` or
`AttributeError` from editing the three guarded lines is neither of those,
and the old catch could not tell the difference - it would silently narrow
where a WIRED gate looks while reporting a clean run. Narrowed to
`(OSError, CalledProcessError)`, with the reasoning in the file.

### 1.3 `probe-r6-breaker-reset.py:88` S110 - same ruling, same narrowing.

`drive_to()` drives N outage failures on purpose; the raise **is** the
expected outcome of each call, so swallowing is correct - for the two outage
errors only. A bare `except Exception` would absorb a `TypeError` from a
changed `request` signature and report a drive that never happened. ARM 1c
would eventually have caught that (it reads the counter go 4 -> 5); the
narrow catch catches it at the row that lied. Now
`(JobviteUnavailableError, JobviteUpstreamError)`.

**Evidence for 1.2 and 1.3.** `docs/reviews/probe-gate-swallowed-exceptions.py`,
7 rows, exit 0:

    A. git ABSENT (OSError) still falls back, does not raise            PASS
    B. not a repo (CalledProcessError) still falls back                 PASS
    C. an UNNAMED TypeError now ESCAPES instead of being swallowed      PASS
    D. happy path unchanged, and the wired gate still exits 0           PASS
    E. an OUTAGE error is still swallowed, all 4 calls made             PASS
    F. an UNNAMED TypeError now ESCAPES on the FIRST call               PASS
    G. NEGATIVE CONTROL: no exception at all is not an error either     PASS
    7/7 rows ran.

**Its first draft exited 0 with three rows never run.** Importing an
unguarded probe module runs it, and `probe-r6-breaker-reset.py` ends on
`raise SystemExit(0)`, which took the whole process with it before rows E-G
executed. Every row printed up to that point had passed, so it read as a
clean green. The `load()` helper now swallows a zero SystemExit and the file
carries a `ROW_FLOOR = 7` that refuses a partial run. A skip is a green that
tested nothing.

### 1.4 `repoint-design-citations.py:92,95` B023 - NOT a bug, NOT restructured.

Confirmed by reading: `sub` is handed straight to `_CITATION.sub(sub,
original)` on the very next statement, called synchronously and discarded
before the loop advances; `seen` is read on the line after that, still inside
the same iteration. A comment now records why it is safe **and what would
break it** - collecting these callables to run later would silently give
every one of them the LAST iteration's `pairs` and repoint 867 citations
against the wrong map. The `noqa: B023` markers sit on the two lines ruff
actually reports (the uses, not the `def`).

### 1.5 Amputation: every fix watched failing

`docs/reviews/probe-docs-lint-amputation.py`, exit 0. Each row deletes one
behaviour, re-runs the probe that watches it, and asserts exactly the right
rows die. Anchors are asserted unique before writing; the file is asserted
CHANGED after (a `str.replace` that matches nothing no-ops in silence); the
tree is restored from an in-memory copy in a `finally`.

    A1 fail-open REPOINT-EXEMPT read restored     CAUGHT: rows killed {A, B}
    A2 checker stderr health check deleted        CAUGHT: rows killed {E}
    A3 _corpus() catch widened to Exception       CAUGHT: rows killed {C}
    A4 drive_to() catch widened to Exception      CAUGHT: rows killed {F}
    A5 NEGATIVE CONTROL, comment-only edit        CAUGHT: rows killed NONE
    restored repoint-design-citations.py: yes
    restored check-standards-citations.py: yes
    restored probe-r6-breaker-reset.py: yes
    post-run re-check of probe-repoint-fail-closed.py:      exit=0
    post-run re-check of probe-gate-swallowed-exceptions.py: exit=0

The uniqueness assert earned its place on the first run: A4's one-line anchor
appears **four** times in that file, so the anchor now carries the call above
it.

---

## 2. The cosmetic sweep (commit 2)

### What came off

    ruff  extend-exclude = ["docs"]  ->  []
    mypy  files   = ["src", "tests"] ->  ["src", "tests", "docs/reviews"]
          exclude = ["^docs/"]       ->  deleted

### The proof that matters

An exclusion narrowed so it still misses the directory looks identical to one
that was removed. So a violation was planted and the **repo-wide** command
watched go red:

    planted `import os, sys` (unsorted, unused) in check-adr-numbers.py
      uv run --frozen ruff check .   EXIT=1  --> docs/reviews/check-adr-numbers.py:160
    planted `_planted: int = "not an int"` in check-quickstart.py
      uv run --frozen mypy           EXIT=1  docs/reviews/check-quickstart.py:121:
        error: Incompatible types in assignment (expression has type "str",
        variable has type "int")  [assignment]
    both restored, then:  ruff EXIT=0   mypy EXIT=0

Restoration was checked with `cmp`, not `git diff` - `git diff --quiet`
reports NO DIFF for an untracked file, and the plant target could have been
one.

`uv run --frozen mypy` now reports **96 source files**, up from 63.

### Exempted rather than swept, and both entries say why

`{scripts,docs/reviews}/**` keeps `T201, D103` - the existing `scripts/*`
entry, extended rather than reinvented. **No print was deleted.**

I also added a second entry, and this is the one judgement call I want ruled
on:

    "docs/reviews/**" = ["S101", "S603", "S607", "ANN"]

That is the `tests/*` entry's own list, for the `tests/*` entry's own stated
reason - "asserts and subprocess are the point in a test", "unannotated tests
are fine". `docs/reviews/**` is the `tests/*` population living at another
path. Six probe files carry a matching `# mypy: allow-untyped-defs,
allow-untyped-calls` header so the two tools say the same thing about the
same population; mypy still READS every one of those files and every other
strict check applies to them. **The brief said to extend only the T201/D103
entry, so this is wider than instructed. Say the word and I will annotate the
~26 signatures instead** - I began that and backed it out, because my own
`object` annotations made mypy *worse* (73 errors -> 111) before I reverted
them.

Everything else was swept, not exempted: **1500 -> 0**.

    W505  590 -> 0      E501  417 -> 0      T201  329 (exempt, unchanged)
    D103   71 (exempt)  E741    3 -> 0      B023    2 -> annotated
    N806    2 -> 0      N818    1 -> 0      D403/D301/D205/F401 -> 0

Method: the B49b pipeline's own `reflow-doc-lines.py` (per
`docs/reviews/b49b/README.md`) for the bulk, then 52 hand-shortened
docstring summaries, then three value-preserving wrappers, then 39 final
wraps by hand. **Every automated rewrite re-parsed the module and compared
its string constants as a multiset** before writing - a gate's message must
not change under a cosmetic sweep - and three files were REFUSED by that
guard rather than written.

### The control I would keep

Exit codes cannot see a corrupted message. So every checker's **full
stdout+stderr transcript** was captured at `8f5bb6f` in a separate worktree
and re-diffed after each stage. Across ~370 rewrapped lines, **not one
checker message changed**.

### What the sweep found, once the tools could see

- `by_file` in `b49b/apply-short-summaries.py` declared its elements
  `tuple[int, str, str]` and appends three **strings**. Wrong since it was
  written; unchallenged because mypy had never read the file. The
  module-level `row` was also bound to an `int` and then to a `dict`.
- `missing` in `check-coupling.py` is bound to a `list[str]`, then reused for
  a `str | None`, then again as a loop variable - in a WIRED gate. Renamed at
  both reuses.
- `node.end_lineno` is `int | None` and was indexed unguarded in two places.
- **The B49b reflow broke three hanging-indent list items**, dropping a
  single word to column 0 mid-item (`probe-r6-arm1c-tautology.py:15`,
  `probe-r6-wait-burns-budget.py:16,20`). That is the sweep's own damage. It
  is repaired in place and recorded here rather than shipped quietly.
- My three new probe files were also mangled by the reflow (collapsed lists,
  broken dividers). I reverted them to the committed version and hand-wrapped
  instead. The reflow tool is right for flowing prose and wrong for
  structured indented lists; worth knowing before the next sweep.
- `probe-repoint-fail-closed.py` writes example `DESIGN.md:100` citations,
  which `check-design-citations.py` immediately counted as real (1785 ->
  1789 across one more file). They are marked `REPOINT-EXEMPT`, which is the
  exact hazard that marker exists for.

---

## 3. Before/after exit codes: all runnable checkers

Run under `uv run --frozen python` in both trees. BEFORE is a **separate
worktree at 8f5bb6f** (`/tmp/docs-lint-before`), not a stash.

| checker | before | after |
|---|---|---|
| check-adr-numbers.py | 0 | 0 |
| check-clause-citations.py | 0 | 0 |
| check-coupling-controls.py | 0 | 0 |
| check-coupling-sweep.py | 0 | 0 |
| check-coupling.py | 0 | 0 |
| check-coupling.py `docs/DESIGN.md` | 0 | 0 |
| check-coverage-floors.py | 2 | 2 |
| check-cross-references.py | 0 | 0 |
| check-design-citation-shape.py | 0 | 0 |
| check-design-citations.py | 0 | 0 |
| check-env-vars-are-declared.py | 1 | 1 |
| check-no-sigpipe-pipelines.py | 0 | 0 |
| check-obligations.py | 0 | 0 |
| check-obligations.py `--controls` | 0 | 0 |
| check-plan-measurements.py | 0 | 0 |
| check-quickstart.py | 0 | 0 |
| check-resweep-verdicts.py | 0 | 0 |
| check-row-floor-exactness.py | 0 | 0 |
| check-row-floors.py | 0 | 0 |
| check-settings-are-read.py | 0 | 0 |
| check-standards-citations.py | 0 | 0 |
| classify-w505.py | 1 | 1 |
| probe-r4-h3-live-arm-cannot-detect.py | 0 | 0 |
| probe-r6-arm1c-tautology.py | 0 | 0 |
| probe-r6-breaker-reset.py | 0 | 0 |
| probe-r6-post-escape.py | 0 | 0 |
| probe-r6-wait-burns-budget.py | 0 | 0 |
| probe-u12-f2-embedder-leak.py | 0 | 0 |
| repoint-design-citations.py | not run - MUTATES | not run - MUTATES |
| *new:* probe-repoint-fail-closed.py | - | 0 |
| *new:* probe-gate-swallowed-exceptions.py | - | 0 |
| *new:* probe-docs-lint-amputation.py | - | not run here - MUTATES |

**Nothing moved.** `check-coverage-floors.py` exits 2 in a fresh worktree
before and after (no coverage data); `check-env-vars-are-declared.py` exits 1
before and after (it is the unwired one with a backlog, per `ci.yml:572`);
`classify-w505.py` exits 1 by design against a swept tree
(`b49b/README.md`).

Three **transcripts** differ, all explained:

- `check-design-citations.py`: 1785 citations / 192 files -> 1789 / 193. The
  four are the new probe's example citations, in one new file.
- `check-adr-numbers.py`: "Across 7 local branch(es)" -> "6". It reads the
  LOCAL BRANCH SET; a branch was merged in the shared checkout between the
  two captures. Nothing to do with this diff, but worth knowing: **this
  checker's output is not reproducible across two checkouts.**
- `probe-r6-wait-burns-budget.py`: one extra retry WARNING. Measured 3 runs
  in EACH tree: after = 2, 2, 3; before = 1, 2, 1. A timing flap present in
  both, and the only diff to that file is a comment header.

---

## 4. Gate numbers, each read from its own exit code

Floors **grepped from `ci.yml` at run time**, never retyped:

    grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml    -> 867
    grep -oE 'check-harness-anchors\.py --self-check --floor [0-9]+' .. -> 456

| gate | command | exit | number |
|---|---|---|---|
| suite | `uv run --frozen pytest` | 0 | **867 passed, 0 skipped**, 6 deselected (floor 867) |
| anchors | `python3 scripts/check-harness-anchors.py --self-check --floor 456` | 0 | 456 resolved (floor 456) |
| ruff | `uv run --frozen ruff check .` | 0 | All checks passed |
| mypy | `uv run --frozen mypy` | 0 | no issues in **96** source files (was 63) |

Zero skips: the run line is `867 passed, 6 deselected` - deselection, not
skipping, and no `skipped` appears at all.

---

## 5. What ci.yml needs from me

**Nothing.** `ruff check .` and `uv run --frozen mypy` are already the
commands `ci.yml` runs; this branch only changes what they can see. I ran
both, argument for argument, and both exit 0.

Two steps you may want to ADD, both run from this worktree first:

    - name: The docs/ gates' own fail-closed probes
      run: |
        uv run --frozen python docs/reviews/probe-repoint-fail-closed.py
        uv run --frozen python docs/reviews/probe-gate-swallowed-exceptions.py
    # measured: exit 0 and exit 0

    - name: The docs-lint amputation harness
      run: uv run --frozen python docs/reviews/probe-docs-lint-amputation.py
    # measured: exit 0, 5/5 rows CAUGHT, tree restored

I did **not** route these through `scripts/ci-harness-gate.sh`: that gate
builds `scripts/$harness` itself and these are Python files under
`docs/reviews/`, so it would look for `scripts/docs/reviews/...`. They gate on
their own exit codes, which is what the preamble asks for.

---

## 6. What I could NOT settle

- **Whether the `docs/reviews/**` ANN/S101/S603/S607 exemption is what you
  want** (section 2). It is wider than the brief, it is argued from the
  `tests/*` precedent, and it is one line to reverse. Your call, not mine.
- **The task says NINETEEN wired gates; I count EIGHTEEN.** Seventeen
  `docs/reviews/*.py` are named in `ci.yml`, plus `probe-u12-f2-embedder-leak.py`
  reached transitively through `scripts/check-log-redaction-amputation.sh:41`.
  `check-clause-citations.py`, `check-design-citation-shape.py` and
  `check-env-vars-are-declared.py` appear in `ci.yml` only inside COMMENTS
  (lines 193, 194, 572, 575) - a grep for the bare name finds them and reads
  as wiring. Nineteen may be counting `check-obligations.py` twice for its
  two modes. I did not change anything on this; I ran all 26 runnable files
  either way, which is a superset.
- **The task measured 1464 ruff findings; I measured 1500** at the same SHA
  with the exclusion off. I did not reconcile the 36. Both are pre-sweep and
  both are now 0, so nothing turns on it.
- **`repoint-design-citations.py` was never run for real**, only in DRY RUN.
  It mutates 867 citations and the brief did not ask me to run it. Its
  behaviour under `--write` after my change is unexercised except by the
  probe's parse-level rows.
- **`check-coverage-floors.py` exits 2 in a bare worktree** and `ci.yml`
  runs it after a coverage run. I did not reproduce CI's ordering, so I know
  its exit code is unchanged but not that it is 0 in CI.

The worktree `/tmp/docs-lint-work` is still in place because the branch is
unmerged; `/tmp/docs-lint-before` (detached at 8f5bb6f) exists only to hold
the BEFORE measurements. **Remove both after you merge** -
`git worktree remove /tmp/docs-lint-work /tmp/docs-lint-before`.
