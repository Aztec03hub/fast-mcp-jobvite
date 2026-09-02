# FINDINGS — #153 / #155 / #149: one checker, blind in three directions

`suborch-153`, 2026-09-01 09:06 PM CDT.
Branch `fix/153-wiring-container`, commit `bfade9e`, cut from `2d886a4`.
**Not pushed, not merged.**

Every count below names its container.

---

## 1. What landed

`docs/reviews/check-checkers-are-wired.py` enumerated
`docs/reviews/check-*.py` and `docs/reviews/check-*.sh` — **two globs
wearing a container's name**. It now enumerates every tracked `.py` or
`.sh` under `docs/reviews/` and `scripts/`, selected by KIND and never
by name prefix.

| measured at `2d886a4` | before | after |
|---|---|---|
| members enumerated | 28 | **123** |
| wired | 24 | 67 |
| unwired, reason recorded | 4 | **56** |
| unwired, unexplained | 0 | 0 |
| files in the two directories it printed a verdict about | 28 of 123 | 123 of 123 |
| `--self-test` controls | 31 | **35** |
| amputation arms in `probe-wired-checker-amputation.py` | 8 | **12** |

The old run printed *"Every checker is wired"* while saying nothing
about 95 of the 123 files in its own two directories.

**Both halves landed in one commit**, so the gate is never red:

- `scripts/check-timeout-literals.py` **WIRED** — #153's own ruling and
  the step `suborch-116` wrote. Measured green first: self-test 3/3,
  main run 0 retyped figures over 38 scripts and 1017 echo lines. It
  had been committed *unwired* by the task that built it, at exit 0,
  because `scripts/` was outside the population.
- `check-checkers-are-wired.py --self-test` **WIRED** (#149 M-3).
- The other 52 members carry a written reason.

---

## 2. Three corrections to the brief

### 2.1 "Four probes ARE wired" is a false count — it is ONE of thirty

The brief (§C) and task #155 both say: *"probes NAMED in a workflow: 4"*,
naming `probe-docs-lint-amputation.py`, `probe-r6-breaker-reset.py`,
`probe-repoint-fail-closed.py`, `probe-set-e-vs-harness.sh`. That number
came from asking which basenames appear *anywhere* under
`.github/workflows/`.

**Three of those four appear only inside `#` comments:**

    probe-docs-lint-amputation.py   ci.yml:980   run: uv run --frozen python ...   WIRED
    probe-r6-breaker-reset.py       ci.yml:976   # ...comment...                   NOT
    probe-repoint-fail-closed.py    ci.yml:816   # ...comment...                   NOT
    probe-set-e-vs-harness.sh       ci.yml:252   # ...comment...                   NOT

By the sound instrument — parsed `jobs.*.steps[].run`, shell comments
stripped — it is **1 wired of 30 tracked probes under `docs/reviews/`**
at `2d886a4`, not 4 of 28.

This is the exact false positive `check-checkers-are-wired.py`'s own
docstring was written against: *"The obvious census is
`grep <basename> .github/workflows/ci.yml`. That counts a name in a
COMMENT as wired."* The brief used the instrument the subject file
exists to warn about.

The brief's argument survives — *"probes are not categorically
unwirable"* still holds on one wired probe — but it rests on 1, not 4.

### 2.2 `probe-ci-checker-steps.py` — RULED, against the brief

§D says to expect it *"to deserve a real step instead."* **I exempted it
instead**, and this is a ruling, not an omission:

Its purpose is to execute `ci.yml`'s checker steps VERBATIM so that a
local green means what a CI green means. Its audience is the terminal
**before** a push. Running it *inside* CI is a tautology — it re-runs,
in the job, the steps the job is already running, doubling the bill for
no new signal, and it cannot fail in a way the real steps would not have
failed first.

The gap #155 names is real: `suborch-147`'s improvements only fire when a
human types the command. But the remedy is a **pre-push hook**, not a CI
step. Raised for the board rather than settled here.

### 2.3 `probe-coverage-ratchet.py` does not mutate the tree

The brief (§D) says its pre-classification grep flagged this file as a
tree-mutator and that this was wrong. Confirmed by reading: all nine arms
write exclusively into a `TemporaryDirectory`. Its recorded reason is now
the true one — it is the control for `check-review-coverage.py`, and a
control has no job to share until its subject has one.

---

## 2.4 R16's three "newly visible members", checked one at a time

`review-r16` reported R16-M1 while this was in flight. All three of its
claims were re-measured against this branch rather than relied on.

| claim | verdict |
|---|---|
| `scripts/check-timeout-literals.py` is in no workflow | **CONFIRMED, and now CLOSED** — wired at `ci.yml:328-329` by this change |
| `docs/reviews/probe-*`: 24 unwired of 28 | **CORRECTED**: 29 unwired of 30 (see §2.1) |
| `scripts/check-secrets-baseline.py` "invisible to the gate today" | **TRUE of the OLD container, NOT of this one** |

The third needs saying precisely, because the difference is the whole
change: `scripts/check-secrets-baseline.py` is *newly visible* — it was
outside the old population entirely — but it is **not newly a problem.**
It reads WIRED, correctly, via `python3 scripts/check-secrets-baseline.py
--controls` at `ci.yml:1581`. Newly visible and already wired is the
outcome the widening wants, not a finding.

The `scripts/` half classifies as: **51 members, 41 wired, 10 unwired and
all 10 excused with a reason.**

**R16-H1 and R16-M2 are NOT newly visible.** Both
`docs/reviews/check-harness-result.sh` and
`docs/reviews/check-landing-published.py` were already in the old
`docs/reviews/check-*` container. Neither is mine this run and I have not
touched them.

The one file in that family that IS newly visible is
`scripts/lib/harness-result.sh` — exempted as a sourced library, and the
file whose false-GREEN classification produced §3.1 below.

---

## 3. Two defects the widening found IN THE CHECKER ITSELF

### 3.1 HIGH — the wiring test was a bare SUBSTRING, and it produced a false GREEN

`wired` was computed as `name in text` over the concatenated run bodies.
On the first widened run, `scripts/lib/harness-result.sh` read **WIRED**
— because `docs/reviews/check-harness-result.sh` is invoked at
`ci.yml:272` and the shorter name is a substring of the longer one.

That is a **false green**: the direction this file exists to prevent. It
was invisible for as long as every member was `check-*` with names that
happened not to nest — a property nobody chose and that expired the
moment the population grew.

Caught by the file's own stale-exemption check, firing on an entry I had
just written.

**Fix:** the bodies are TOKENISED, using the same `_commands` walk the
interpreter test already uses, and a name counts as wired when it is the
basename of a real argv token. Measured: 68 substring-wired vs 67
token-wired, and the single difference is the false positive.

**Control 2b** asserts it, and derives the collision (`check-` stripped
from a name that really is wired) rather than naming a file that could be
renamed out from under it. **Amputation arm I** puts the substring test
back and kills exactly that row.

### 3.2 HIGH — `third_party_imports` would have gone silent on the whole new half

It resolved `ROOT/"docs"/"reviews"/name`. Every `scripts/` member would
have resolved to a path that does not exist, returned `[]`, and read
*stdlib-only* — so the bare-interpreter arm, the thing that once turned
`main` red, would have been **silently blind to exactly the half the
widening was for**. A wrong zero that explains itself.

Fixed to resolve through the container, with a documented fallback to the
token-as-path that keeps the negative control non-vacuous (see §5).

---

## 4. The prefix was load-bearing as an ESCAPE HATCH (#149)

`probe-midsentence-shape.py`'s docstring says it is named `probe-`
**"so it cannot become a gate by accident"** — it was using this
checker's `check-*` filter *as a mechanism*.

The widening removes that hatch deliberately. A file opts out by
**recording a reason someone can read and argue with**, never by
choosing a name the checker cannot see.

**That docstring is now wrong and says so in its register entry.**
Rewriting the paragraph in place is left to the owner of that file — it
is not mine this run. Its exemption stands on its own merits (backlog
320 of 881, 36.3%, per #135).

---

## 5. A vacuity I shipped, and the probe caught it

`_non_member_subject` — the subject-picker for the control that proves
`_is_ours` is not `True` — **used `_is_ours` to skip container members.**

Amputation arm C (`_is_ours` always True) therefore made it find no
subject at all and raise `SystemExit`, rather than produce a failing row.
A control that selects its own subject THROUGH the construct it tests
does not fail when that construct dies; it *disappears*, and that reads
as an instrument error rather than a kill.

The function it replaced carried this exact warning about `_CHECKER_NAME`.
**I reintroduced the defect one identifier over while rewriting the
paragraph that warns about it.** It reads `path_of()` directly now, and
arm C kills the right row for the right reason.

---

## 6. The positive control, both arms, in BOTH halves (§E, R16-M1)

In `probe-wired-checker-amputation.py`, running the real checker as a
**subprocess** and reading ITS exit code:

- **ARM 1 (must be RED).** A newly `git add`ed `verify-container-arm.py`
  — a *fourth* prefix, one no existing filter would have matched — with
  no recorded reason. The checker must exit non-zero **and name the
  file**. Scoring on the exit code alone would let a stale exemption or a
  bare interpreter pass for this arm.
- **ARM 2 (must be GREEN).** The same file with a reason recorded must be
  excused, and no other member may be unexplained — otherwise a green
  here would not be attributable to the reason.

**Both arms now run ONCE PER HALF of the container** — `docs/reviews/`
and `scripts/`. That is `review-r16`'s correction to my first version and
it was right: my original planted only into `docs/reviews/`, **the half
that was never broken.**

**Measured, because the point of the row is that it fires.** With
`CONTAINER_DIRS` narrowed back to the pre-#153 value:

    docs/reviews/  ARM 1: ok        <- passes unchanged on the OLD code
    docs/reviews/  ARM 2: ok        <- passes unchanged on the OLD code
    scripts/       ARM 1: FAILED    "exited 1 but never named
                                     scripts/verify-container-arm.py"
    scripts/       ARM 2: FAILED    "not in the enumerated container
                                     at all"
    probe exit 1

The `docs/reviews/` pair is green on the broken code. Only the
`scripts/` pair can see the defect this task exists for. Source restored
by byte-comparison against a pre-mutation backup, not by re-editing — a
`sed` that matches nothing succeeds silently — and the anchor count is
asserted to be exactly 1 first, so the mutation cannot no-op and pass.

The fixture is removed in a `finally` and the tree is asserted clean **by
asking git**, not by trusting the unlink.

---

## 7. Gates, each exit code on its own line

Run in `fmj-worktrees/w153` at `bfade9e`, with CI's exact invocations.

    ruff check .                                          exit 0   (All checks passed)
    ruff format --check .                                 exit 0   (133 files already formatted)
    SHELLCHECK_OPTS=--severity=warning actionlint         exit 0
    pre-commit run --all-files                            exit 0   (3 hooks, all Passed)
    pytest -q                                             exit 0   (887 passed, 0 skipped, 6 deselected)
    check-checkers-are-wired.py                           exit 0   (123 members, 67 wired, 56 reasoned, 0 unexplained)
    check-checkers-are-wired.py --self-test               exit 0   (35/35 controls)
    check-timeout-literals.py --self-test                 exit 0   (3/3)
    check-timeout-literals.py                             exit 0   (0 retyped figures, 38 scripts, 1017 echo lines)
    probe-wired-checker-amputation.py                     exit 0   (14/14 arms, no survivor)

Suite floor 887, met exactly. `pre-commit` passes and keeps passing.

`pyright` is **not a CI gate in this repo** (no `pyright` in `ci.yml`).
Measured anyway: **27 errors on `main` at `2d886a4` and 27 on this
branch — no delta, and zero in either file I touched.** One error I *did*
introduce (ruff's reformat moved a `type: ignore` off its assignment) was
found and fixed before the commit.

---

## 8. What I could NOT settle — handed back

Distinct from what I did not attempt.

1. **`scripts/check-u1-pid1-shutdown.sh`** — exempted, reason recorded,
   but the exemption says UNSETTLED. It needs Docker with no `--init`
   and `docker stop -t 15`. GitHub runners *do* have Docker; nobody has
   measured what this costs or whether it is stable there. I did not run
   it, so I did not wire it.
2. **`docs/reviews/probe-coverage-ref-resolves.py`** — same. Reading it,
   it looks self-contained, cheap and wirable. I did not run it, and
   this project's rule is measure-then-wire, so it is exempted with that
   said out loud rather than wired on the strength of a read.
3. **`check-review-coverage.py`** — still exempted. Its own reason says
   it belongs on **pull requests** against `origin/main`, because a merge
   cannot record its own sha, and asks to be wired "with #153's
   widening, in one ci.yml change". **I did not wire it.** The widening
   does not by itself create the PR-scoped job it needs, and adding one
   is a ci.yml change of a different shape than this task authorised.
   §F said to say so rather than wire it silently. Saying so.
4. **#149's second half is NOT done.** M-3 (wire `--self-test`) is done.
   M-4 — build `scripts/check-wired-checker-amputation.sh` in the shape
   the other units use, reached through `ci-harness-gate.sh` with the
   canonical `HARNESS-RESULT` line — is not. The 12 arms are a program
   and they run; they are still not a harness. #149 should stay open on
   M-4, and on the unexplained arm numbering (A1, A2, A3, A5 — no A4).

**Not attempted:** anything in `scripts/check-u1-boot-amputation.sh`
(`suborch-156`) or `docs/reviews/review-coverage-backlog.txt`
(`review-r16`).

---

## 9. New tasks this run suggests

- **A pre-push hook running `probe-ci-checker-steps.py`.** The honest
  remedy for #155's sharpest instance, since a CI step is a tautology
  (§2.2).
- **Rewrite `probe-midsentence-shape.py`'s docstring**: its stated
  protection mechanism no longer exists (§4).
- **`third_party_imports` has a false positive.** It reports
  `probe-ci-checker-steps.py` as importing a module named `the` — its
  `_IMPORT` regex matched prose in a docstring, not code. Harmless in
  the safe direction (it can only over-report a need), but it is an
  instrument reporting something that is not there. Nit, unfixed, mine
  to declare.
