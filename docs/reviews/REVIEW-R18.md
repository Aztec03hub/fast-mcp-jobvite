# REVIEW-R18 — the four gates built on 2026-09-01, reviewed by nobody until now

Reviewer: `review-r18` (Tier 1). Worktree `fmj-worktrees/r18`, branch
`review/r18`, cut from `origin/main` at `e845839`. The fifth commit
`9c08427` is not on the trunk; it was cherry-picked here as `9b49318`
and read from the main checkout. **Nothing was pushed and nothing was
merged.** CI run 33582613697 was in flight throughout.

Every finding below carries a suggested fix. Every number below was
measured in this worktree, not read off a commit message.

---

## Summary

| Severity | Count |
|---|---|
| High | 2 |
| Medium | 5 |
| Low | 2 |
| Nit | 1 |
| **Total** | **10** |

The fifth Medium (**M5**) is reported in section 10 rather than section
3, because it explains four of the eight commits in my own population
and has to be read beside the backlog numbers it accounts for.

Two findings I drafted and then **WITHDREW on measurement** are recorded
in section 6, because a withdrawn finding is a fact about my instrument
and the next reviewer should not re-derive it.

---

## 1. HIGH — H1: the secrets gate prints "none would be a finding" precisely when it failed to look

`scripts/check-secrets-baseline.py:265-268` (commit `3987403`, #163).

```python
listed = subprocess.run(
    [git, "ls-files", "--others", "--exclude-standard"], ...
).stdout.split()
```

`git ls-files` separates paths with `\n` and does **not** quote a
filename merely because it contains a space. `.stdout.split()` splits on
*any* whitespace, so one untracked file named `my notes.md` becomes two
argv entries, `my` and `notes.md`, neither of which exists. The scan
then reports nothing for it, and the function takes its `if not results`
branch.

**Measured, two arms, in a scratch repository with a synthetic AWS key
pair assembled at runtime so no command line ever held the pair. Both
arms ran under `uv run --no-project --with detect-secrets==1.5.0`, which
is the invocation this file's own line 176 prescribes:**

| Arm | Untracked filenames | Output |
|---|---|---|
| A | `my notes.md` (3 findings) + `clean.md` | `5 untracked file(s) checked ahead of tracking: none would be a finding.` |
| B (control) | `mynotes.md` (same 3 findings) + `clean.md` | `WARNING - 1 UNTRACKED file(s) would become findings... mynotes.md: 3 finding(s)` |

Arm B fires, so arm A is not vacuous: the *only* difference is the space
in the filename. The file with three real secret findings is silently
dropped, **and the gate prints a reassuring all-clear about it**, with a
count of 5 that is also wrong.

This is the failure the rest of this repository is built to hunt — a
clean zero that explains itself — sitting inside the secret scanner.
It is warn-only, so it cannot turn CI wrongly green or red about the
*tracked* set; what it can do is tell an author their untracked file is
clean when it holds a credential.

**Suggested fix.** Use the NUL-delimited form, which is what `-z` exists
for, and stop splitting on whitespace:

```python
listed = [
    p
    for p in subprocess.run(
        [git, "ls-files", "-z", "--others", "--exclude-standard"], ...
    ).stdout.split("\0")
    if p
]
```

Add a control arm (see M4) with a space in the fixture's filename, so
this cannot come back.

---

## 2. HIGH — H2: not one of the mirror gate's 14 control rows executes `_gh()` at all

`scripts/check-mirror-liveness.py:84-106` and
`scripts/check-mirror-liveness-controls.sh` (commit `6f858ea`, #164).

The commit message and the controls header both state one blind spot:
that a fixture-fed row builds no URL, so none of them could catch the
`PATH`-vs-`FILE NAME` 404. **That understates it.** Every one of the 14
rows passes *both* `--workflow-json` and `--runs-json`, so `_load()`
never takes its `fetch` branch and `_gh()` is never entered.

**Measured with a tripwire.** I planted `raise SystemExit("!!! _gh WAS
REACHED !!!")` as the first statement of `_gh` in a copy and ran the
harness:

```
$ grep -c "_gh WAS REACHED"        ->  0
14/14 controls fired.
HARNESS-RESULT ... rows=14 floor=14 fired=14/14 status=ok
```

The harness is fully green with its entire live-API path amputated at
the top. Three of the five `UnmeasurableError` producers live inside
`_gh` — `gh` not on `PATH` (`:88`), a non-zero `gh` exit (`:95-99`), and
unparseable JSON (`:100-105`) — and **none of the three is exercised by
any control here or by the live CI step**, which only ever traverses the
happy path on a healthy repository. The `MISSING` row (`:127`) does not
reach it either: a nonexistent fixture path raises inside `_load`'s
`read_text`, one branch earlier.

So the class the file names is real but narrow. The wider true statement
is: *the controls cover `check()`'s decision logic and nothing of the
transport*, and the `COULD NOT MEASURE` exit that the design leans on
hardest is the least exercised branch in the file.

**Suggested fix.** Two cheap rows that need no network, raising
`ROW_FLOOR` 14 → 16:

```bash
row "NO-GH     gh absent is COULD NOT MEASURE" 4 "$CHECKER" \
    "$WORK/fx/active.json" "" "not on PATH"      # with PATH= emptied
row "GH-FAILS  a non-zero gh exit is too"      4 "$CHECKER" \
    "" "" "exited"                               # with a stub gh on PATH
```

This needs `row()` to accept an omitted fixture (pass no flag when the
argument is empty) — a small change, and the point of it is that the
argument-passing path gets executed at all. Then amend the header's
blind-spot paragraph to say the transport is untested, not merely the
URL.

---

## 3. MEDIUM

### M1 — the runs query depends on the ordering the code refuses to trust

`scripts/check-mirror-liveness.py:177-181` against `:119-127`.

`_newest_run`'s docstring is explicit: *"The API returns newest-first,
but that ordering is not a documented guarantee ... so this takes the
max rather than the head."* The query one function down is
`...&per_page=10&filter=all`. Taking the max of a page is only equivalent
to the true newest **if that page is the newest ten**, which is exactly
the ordering guarantee the docstring just declined to rely on. The repo
had 335 mirror runs when this was written, so the page is 3% of the
population.

The two defences contradict each other, and only one can be right. The
failure is in the safe direction — a max over a subset is never newer
than the true max, so this can produce a false `STALE`, never a false
`OK` — but a gate that goes red on a healthy mirror is the gate that
gets ignored, which is this file's own stated reason for a 48h window
rather than 26h.

**Suggested fix.** Pick one and say so. Either keep `per_page=10` and
replace the docstring paragraph with "the API returns newest-first; the
max is a defence against a hand-written fixture, not against the API",
or drop the dependency by asking for what you want:
`...&per_page=1` plus a comment that a single newest run is all the age
test needs. I prefer the first: it costs nothing and the fixture defence
is worth keeping for the `UNORDERED` control row.

### M2 — the mirror step is unguarded on repository identity, so it is red on every fork

`.github/workflows/ci.yml:875-877` (commit `6f858ea`).

```yaml
run: |
  uv run --frozen python scripts/check-mirror-liveness.py \
    --repo "${{ github.repository }}" || exit 1
```

`on:` includes `push: branches: [main]` (`:44-46`). On a fork,
`github.repository` is the *fork*, whose `mirror.yml` has never run —
so `gh api` returns a workflow with zero runs and the step exits 2
(`NEVER RUN`), or 404s and exits 4 (`COULD NOT MEASURE`). Either way CI
is red for something no commit contains, which is the precise failure
mode the commit message uses to justify making exit 4 fatal.

This is the only repository-identity-dependent API call in the file: I
grepped `ci.yml` for `github.repository`, `github.event.pull_request.head.repo`
and `fork` and this line at `:877` is the sole hit, so no existing
convention was missed — the step introduces the class.

The `pull_request`-from-a-fork case is **fine** and I checked it: that
event runs in the base repository's context, so `github.repository` is
`evolvconsulting/fast-mcp-jobvite` and the read-only token still carries
`actions: read`. The exposure is a fork's own `push` to its own `main`.

**Suggested fix.** One line, and it makes the intent readable:

```yaml
- name: The mirror workflow is still running
  if: github.repository == 'evolvconsulting/fast-mcp-jobvite'
```

with a comment saying a fork has no mirror to watch, so the check has
nothing to say there. Hard-coding the name is correct here rather than
lazy: the mirror is a property of *this* repository, not of whatever
repository the workflow happens to be running in.

### M3 — probe-131's ARM 4 "absent" assertion is vacuous, and only its sibling saves it

`docs/reviews/probe-131-gate-state.sh:164-167` (commit `9c08427`).

The file explains at `:96-99` why ARM 1's *absent* assertion is not
vacuous — ARM 1 also requires no skip `NOTE`, and ARM 2 shows the file
present after the same path. It says nothing about ARM 4's *absent*
assertion, and ARM 4's is the one that does not hold.

**Measured.** I amputated the dirty-tree branch in
`scripts/ci-harness-gate.sh` (`elif [ -n "$tree_before" ]; then` →
`elif false; then`), which makes the gate record state on a dirty tree —
the exact defect ARM 4 exists to catch:

```
ARM 4 - a dirty tree records nothing, and says so:
  PASS  DIRTY     nothing recorded on a tree that was already dirty: state file absent (want absent)
::error::  FAIL  DIRTY     the gate recorded nothing and did not say why
```

The absence assertion **passes on the mutant**. The gate wrote the state
file, ran, found `tree_before == tree_after` (both dirty and unchanged),
and cleared it — so the file is absent at the end for a completely
different reason. Only the paired `NOTE` assertion caught it, and if
someone ever "simplifies" that assertion the arm becomes a control that
passes without testing its subject.

**Suggested fix.** Assert the mechanism, not the residue. Have ARM 4
check the state file *during* the run rather than after it — the stub
harness can `[ -f "$STATE" ] && echo SAW-STATE` — or add the explicit
sentence the file already gives ARM 1:

```bash
# ARM 4's "absent" is NOT self-sufficient: a gate that recorded state
# and then cleared it also ends absent. The NOTE assertion below is
# what distinguishes them, and it is load-bearing, not decoration.
```

I would take the first; the comment alone leaves the arm weak.

### M4 — the untracked warning has zero controls, which is #149's own defect one file over

`scripts/check-secrets-baseline.py:224-297` (commit `3987403`).

`_warn_untracked` is referenced exactly twice in the file: its
definition at `:224` and its single call at `:220`. The `controls()`
function has no row for it. The commit message says *"PROVED ABLE TO
FIRE: planted an obvious synthetic ... The gate stayed exit 0 and
printed the file with its finding count"* — that was a real measurement,
and it is now prose. Nothing makes it run again.

That is verbatim the gap `fd300ec` was written to close for the wiring
probe, in the same sitting: *"The gap was never that they were failing —
it was that NOTHING MADE THEM RUN and nothing would have noticed if they
stopped."* H1 above is the cost: a defect that a single control row over
this function would have caught on the day it was written.

**Suggested fix.** Add two rows to `controls()`, using a scratch
repository so nothing touches the working tree, with the fixture named
with a space in it so it doubles as H1's regression test:

```
arm("UNTRACKED-WARN",  ...)  # a planted synthetic in an untracked
                             # `my notes.md` is REPORTED, with its count
arm("UNTRACKED-CLEAN", ...)  # a clean untracked file yields the
                             # "none would be a finding" line
```

Raise the file's control floor by 2 in the same commit.

---

## 4. LOW

### L1 — `_warn_untracked` goes silent in three places, against this file family's own doctrine

`scripts/check-secrets-baseline.py:262`, `:271`, `:281` — bare `return`
on `git` missing, on `ls-files` failing, and on the scan being
unreadable. No message in any of the three.

The same author, in the same sitting, wrote `check-mirror-liveness.py`
around the sentence *"An instrument that cannot see reports that it
cannot see"* and `ci-harness-gate.sh` around *"a skip has to announce
itself"*. This function does the opposite three times, and the gate's
surrounding output looks exactly as it does on a healthy run.

The blast radius is genuinely small — `gate()`'s guard at `:171` already
refuses when `detect_secrets` is not importable, so the common cause
cannot reach here — which is why this is Low and not Medium.

**Suggested fix.** Give each `return` a one-line reason on stdout, e.g.
`print("  (untracked pre-check skipped: git is not on PATH)")`, matching
the vocabulary the two sibling gates already use.

### L2 — probe-131 ships nine positive assertions and no amputation of its own

`docs/reviews/probe-131-gate-state.sh` (commit `9c08427`).

Every other harness family here pairs positives with amputations that
delete the rule and require the finding to disappear.
`check-mirror-liveness-controls.sh` has three in the same population.
This probe has none, so nothing in CI holds its nine assertions to being
non-vacuous.

I ran the three that are missing, against copies, and **all three
killed** — so the assertions are sound *today*:

| Amputation of `scripts/ci-harness-gate.sh` | probe exit | row that died |
|---|---|---|
| `harness_state_begin ...` → `:` (never writes) | 1 | `STRANDED ... want present` |
| `harness_state_end ...` → `:` (never clears) | 1 | `CLEAN ... want absent` |
| `elif [ -n "$tree_before" ]` → `elif false` | 1 | `DIRTY ... did not say why` |

That result is mine and lives in this document, which is the same
"a measurement decayed into a claim" shape as M4.

**Suggested fix.** Fold those three into the probe as an `amputate`
helper copied from `check-mirror-liveness-controls.sh:136-169` (counted
substitution, so a stale anchor cannot look like a successful
amputation), and raise `ROW_FLOOR` 9 → 12.

---

## 5. NIT

### N1 — `harness_state_file` does not normalise the repo path it keys on

`docs/reviews/lib/harness-state.sh:53-62`.

The key is `cksum` of the path string. Writer and reader agree today —
I checked all three call sites and they derive the path the same way,
`cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd`
(`scripts/ci-harness-gate.sh:59`) and `.../../..`
(`docs/reviews/probe-harness-exit-codes.sh:13`,
`docs/reviews/restore-stranded-mutation.sh:72-77`) — so no defect exists
now. But `restore-stranded-mutation.sh:83` accepts `--repo "$2"` from a
human, and `/path/to/repo` and `/path/to/repo/` cksum differently, which
would send the restorer to look at a file nobody wrote.

**Suggested fix.** One line in `harness_state_file`, before the cksum:
`repo="${repo%/}"`. Cheap, and it removes a way for the two halves to
disagree about where to look, which is the two-lists defect the
function's own comment says it exists to prevent.

---

## 6. Findings I withdrew, and why

Recorded because a withdrawn finding is a fact about my instrument.

**WITHDRAWN — "the mirror controls use `python3`, not CI's `uv run
--frozen python`."** I drafted this against §A's exact-invocation rule.
Measured before publishing: `grep -ho` across `scripts/check-*-controls.sh`
returns **47 uses of `python3` and 0 of `uv run --frozen`**. Bare
`python3` is the house style for this file family, and the new harness
matches it. The rule applies to what *CI* invokes; CI invokes the
harness through `ci-harness-gate.sh`. No finding.

**WITHDRAWN — "`detect_secrets` is not importable, so `_warn_untracked`
is inert and swallows the failure."** I measured this against the
project's `.venv` and it is true *there*. It is not the environment the
gate runs in: `.pre-commit-config.yaml:107` gives the local hook
`additional_dependencies: ['detect-secrets==1.5.0']`, so pre-commit
builds an isolated venv where `sys.executable -m detect_secrets` works,
and `gate():171` refuses with an explicit message when it does not. My
first measurement was outside the subject's environment. The residue of
this is L1, at the severity it actually deserves.

---

## 7. The commit-message claims I checked, and how each came out

§C5 named five numbers. All five hold.

| Claim | Source | Measured here | Verdict |
|---|---|---|---|
| 887 tests, 0 skipped | `fd300ec`, `9c08427` | `887 passed, 6 deselected in 55.91s` | **HOLDS** |
| 464 anchors | `9c08427` | `anchors resolved: 464`, exit 0 | **HOLDS** |
| 38 container members | `fd300ec`, `9c08427` | `scripts/*.sh (the container): 38` | **HOLDS** |
| 31 tallies | `fd300ec`, `9c08427` | `print a tally line: 31` | **HOLDS** |
| backlog 65 | brief §C5 | 65, by two instruments | **HOLDS** |

On the 6 deselected: I checked whether it hides the shape a skip hides.
It does not. `pyproject.toml:153-157` deselects by `-m "not credentialed
and not network"` as a documented **selection**, both sets are collected
elsewhere with `--collect-only` so they cannot rot, and `ci.yml:960`
gates on `[0-9]+ skipped` separately. "0 skipped" is accurate, not a
euphemism.

Three further claims from the same messages, checked:

- **`6f858ea`'s stated anchor-layer limit HOLDS and is honest.**
  `check-harness-anchors.py` prints, unprompted:
  `UNREAD MUTATION MECHANISMS (1) ... check-mirror-liveness-controls.sh:
  Python str.replace, in-place sed -i expressions`. The commit said so
  before the tool did.
- **`fd300ec`'s "ten ARMS plus two arms in each of two container halves"
  HOLDS.** The probe prints `arms=14` and `rows = len(ARMS) + 2 * halves`
  at `probe-wired-checker-amputation.py:380`.
- **`9c08427`'s claim that both `git status` calls needed `-C "$REPO"`
  HOLDS, and it is a fix rather than a behaviour change.** See §8.

---

## 8. The four §C questions, answered

**§C1 — a control that passes without testing its subject.** Two found:
H2 (the mirror harness's entire transport) and M3 (probe-131's ARM 4).
`probe-wired-checker-amputation.py` came out clean: 14/14, tree clean
after, and its container positive control fires in both halves.

**§C2 — a floor carrying slack.** None. All three new floors were
**watched firing**, not read, and all three are exact:

| Floor | Green | One row removed | Slack |
|---|---|---|---|
| `ROW_FLOOR=14` mirror controls | `rows=14 floor=14 fired=14/14 status=ok` | `rows=13 floor=14 status=breach`, exit 1 | **0** |
| `floor = 14` wiring probe | `arms=14 failures=0 ... status=ok` | `rows=13 floor=14 status=breach`, exit 1 | **0** |
| `ROW_FLOOR=9` probe-131 | `rows=9 floor=9 fired=9/9 status=ok` | 8/9 under each of three amputations, exit 1 | **0** |

#91 found five rows of slack in a floor; there is none here.

**§C3 — a gate that cannot go red in CI.** The opposite: it goes red
where it should not. Exit 4 as a failure is **right** — an instrument
that cannot see must not report on what it did not look at — and the
fork case (M2) is not an argument against exit 4, it is an argument for
not running the step where there is nothing to watch. `pull_request`
from a fork is safe; a fork's own `push` to `main` is not.

**§C4 — the #131 change touches every harness.**

*Is there a caller for whom `-C "$REPO"` is a behaviour change rather
than a fix?* **No, and I checked the whole container rather than
reasoning about it.** All 38 files in `scripts/*.sh` anchor to
`${BASH_SOURCE[0]}`, so every harness mutates `$REPO`'s tree, never the
caller's cwd. Before the change, a gate invoked from another directory
compared the wrong tree against itself and would have missed its own
harness's dirt. There is no caller that relied on the old reading.

*Two worktrees of the same repo at once?* **They do not collide.**
`REPO` is the worktree path, not the shared git dir, so
`fmj-worktrees/r16` and `fmj-worktrees/r18` cksum to different keys and
get different state files — which is what `harness-state.sh:50-52`
claims, and it is correct. The remaining case is two harnesses in *one*
worktree, where the second finds the file present, prints the
`NOTE: ... not overwriting it` refusal, and runs uncovered. That is
announced by design. N1 is the only residue.

---

## 9. Corrections to my brief

§A required me to correct the brief where it is wrong. Three:

1. **§B lists the population as "exactly five commits" and then lists
   eight shas.** The fifth line is four commits
   (`e6333ef 39bfab8 a36883f e845839`), so the population is eight.
   It matters for the declaration, because each of those four is a
   separate trunk commit the coverage checker scores separately, and
   three of the four are already backlogged individually.

2. **§C2 says `ROW_FLOOR=14` is "in check-mirror-liveness-controls.sh"
   and `floor = 14` "in probe-wired-checker-amputation.py".** Correct.
   But it calls all three "new floors landed tonight" — `ROW_FLOOR=9`
   in `probe-131-gate-state.sh` landed in a commit that is **not on the
   trunk**, so it is not in CI and no CI run has ever executed it. The
   brief's §F says 9c08427 is local-only; §C2 does not carry that
   through, and a reader of §C2 alone would think three floors are
   guarding the trunk when two are.

3. **§E asks for "the backlog edit ... deletions for what you covered".**
   Following that literally would have been wrong for one commit: see
   §10. The instruction is right in general and I flag only that the
   checker's output, not the instruction, is what I acted on.

---

## 10. The backlog, before and after — and a defect in the ratchet itself

**Before**, on this worktree at `e845839` (+ cherry-picked `9b49318`),
with no R18 declaration present: **65 entries**,
`check-review-coverage.py` **exit 1**, one commit outstanding and
unrecorded (`e845839`).

**After** writing the declaration in section 12 and applying the edit
the checker itself named: **60 entries**, `check-review-coverage.py`
**exit 0**, `probe-coverage-ratchet.py` **exit 0, 10/10 arms**.

The edit was three parts, all of them named by the tool rather than
chosen by me:

| Part | Lines | Detail |
|---|---|---|
| Deletions | 5 | `e6333ef`, `39bfab8`, `a36883f`, `fd300ec`, `6f858ea` — now covered by this round's range and paths |
| KIND corrections | 1 | `3987403` `NONE` → `PARTIAL`, because I did not read the three `docs/briefs/` files it also touches |
| Additions | 0 | `ENTERED, unrecorded: 0` |

Final line: `The backlog holds at 60, every commit recorded.`

Refs: before `e845839` (trunk) / `9b49318` (worktree HEAD, = `9c08427`
cherry-picked); after, the same refs plus one uncommitted edit to
`docs/reviews/review-coverage-backlog.txt` and the untracked
`docs/reviews/REVIEW-R18.md`. **Nothing committed, nothing pushed.**

The `PARTIAL` on `3987403` is the declaration doing its job: I claimed
`scripts`, so `check-secrets-baseline.py` is covered and the three
briefs are not, and the record now says so rather than reading as a
clean sweep.

### M5 — the backlog file is not a `RECORD_PATH`, so the ratchet feeds itself

`docs/reviews/check-review-coverage.py:232-246`.

`RECORD_PATHS` holds exactly three keys: `CHANGELOG.md`,
`docs/worklogs`, `docs/plans`. It does **not** hold
`docs/reviews/review-coverage-backlog.txt`.

Every one of the four "backlog top-up" commits in my population touches
that file and nothing else — checked with `--name-only`:

```
e6333ef: docs/reviews/review-coverage-backlog.txt
39bfab8: docs/reviews/review-coverage-backlog.txt
a36883f: docs/reviews/review-coverage-backlog.txt
e845839: docs/reviews/review-coverage-backlog.txt
```

So each commit that records the backlog becomes, itself, a trunk commit
no round has covered — which the next backlog commit must then record,
which becomes outstanding in turn. The subjects trace the loop exactly:
`e6333ef` records `3987403`; `39bfab8` records `e6333ef`; `a36883f`
records `39bfab8`; `e845839` records `a36883f`; and `e845839` was what
the checker was red about when I started.

**Four of my eight commits are this loop.** It cost four commits of the
night's work to chase a tail the tool creates.

**The clearance above does NOT fix it, and that is the point.** Those
four cleared only because I happened to declare `docs/reviews` as a
path — a round declaring `src tests` would have left them, and the very
next backlog commit re-enters the loop regardless. The checker's own
docstring states the principle it is missing: *"A COMMIT WITH NOTHING IN
IT TO READ IS DECIDED BY ITS CONTENT, NEVER BY A DECLARATION ... a
record-only commit touches only `RECORD_PATHS`."* The backlog file is
the purest record in the repository and was simply never added to the
list. That is the "a named list misses the unlisted" shape, inside the
file written to enforce container thinking — where R12-M4 already found
it once, when the glob `*REVIEW-R*.md` missed `REVIEW-CODE-R2.md`.

**Suggested fix.** Add the fourth key, with its reason beside it in the
style of the other three:

```python
    "docs/reviews/review-coverage-backlog.txt": (
        "the ratchet's own record. A commit that only edits it adds no "
        "code to read, and scoring it outstanding makes the backlog "
        "self-feeding: every entry needs a commit, and every such "
        "commit needs an entry. Measured at e845839: four of the eight "
        "commits in R18's population were this loop."
    ),
```

The measured consequence of that one line: backlog commits stop
entering, and the four this round cleared by path would have been
excluded by content — which, per the docstring, is the test that is
supposed to run FIRST.

## 11. What I could not settle

Kept separate from what I did not attempt.

1. **Whether the mirror step actually passes on a fork.** M2 is derived
   from `github.repository`'s documented value on a `push` event and
   from the API's behaviour on a repository with no runs. I did not
   fork the repository and push to it, and I would not have without
   asking. The `pull_request`-from-a-fork half I am confident about; the
   fork-`push` half is reasoning from documented behaviour, not a run.

2. **Whether `per_page=10` has ever actually mis-ordered (M1).** The
   contradiction between the two defences is settled and visible in the
   source. Whether GitHub has ever returned a runs page out of order is
   not something I can measure without a live token and a long
   observation, and I did not make a live API call from this worktree.

3. **The in-flight CI run 33582613697.** I did not look at it, query it,
   or wait on it, per §F. So everything in section 8 about what CI does
   is read from `ci.yml` and from local runs, never from that run's
   logs. If it reveals something about the three new steps, it is not in
   this document.

**Not attempted, and deliberately so:** `src/` and `tests/` (no commit
in my population touches either); `docs/briefs/BRIEF-166/167/168`
(touched by `3987403`, and they are briefs for other rounds, not this
one); the other 30 ADRs beyond confirming ADR-0023's bearing on
`set -uo pipefail` in the two new harnesses.

---

## 12. Declaration

I read, in full or by measured execution:
`scripts/check-mirror-liveness.py`,
`scripts/check-mirror-liveness-controls.sh`,
`scripts/check-secrets-baseline.py`,
`scripts/ci-harness-gate.sh`,
`.github/workflows/ci.yml` (the three added regions and its `on:` and
`permissions:` blocks),
`docs/reviews/probe-131-gate-state.sh`,
`docs/reviews/probe-wired-checker-amputation.py`,
`docs/reviews/lib/harness-state.sh`,
`docs/reviews/check-review-coverage.py`,
`docs/reviews/review-coverage-backlog.txt`.

I did **not** read `docs/briefs/BRIEF-166-drifted-claims.md`,
`BRIEF-167-anchor-blind-shapes.md` or `BRIEF-168-range-before-paths.md`,
which `3987403` also touches. So `3987403` is **PARTIAL** under this
declaration and I am not claiming otherwise — a narrower true
declaration beats a wide false one.

The range ends at `e845839`, the trunk tip. **`9c08427` is not on the
trunk and no declaration can cover it**, so the work in section 8 §C4
and findings M3, L2 and N1 are recorded here but will need re-declaring
by whichever round covers that commit once it lands.

<!-- REVIEW-COVERS: 5e087eb..e845839 PATHS: scripts .github/workflows/ci.yml docs/reviews -->
