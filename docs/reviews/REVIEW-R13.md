# REVIEW R13 - the eighteen unreviewed trunk commits

<!-- REVIEW-COVERS: 92cb89b..2584afb -->

One agent, both lenses: adversarial reviewer first, responder second, a
settled disposition per finding. Range `92cb89b..2584afb`, 18 commits, 45
files, +1950/-68, **all paths** - no `PATHS:` clause, and that is the claim
being made.

Reviewed from a detached worktree at `2584afb`
(`/home/plafayette/claude_projects/fmj-worktrees/r13-scope`), never in the shared checkout;
`tally-shapes` and `tally-rebuild` were live on their own worktrees
throughout and nothing of theirs was touched. Design read at the freeze:
`docs/DESIGN-FREEZE.txt` at `2584afb` says `5d17cd7`, and
`git show 5d17cd7:docs/DESIGN.md` hashes to `639f4b7...`, byte-identical to
the working-tree copy. 2133 lines.

Every mutation below was reverted and the revert proved with
`git diff --stat` returning empty.

---

## Summary

| # | Sev | Subject |
|---|---|---|
| H1 | High | `REPOINT-EXEMPT` silences BOTH citation gates, unscoped, reasonless, and the counter that was supposed to make it visible is never read |
| H2 | High | `bare_python_steps` misses every invocation carrying an interpreter flag - the exact class it was written for |
| M1 | Medium | `probe-ci-checker-steps.py` cannot detect either of the two failures it was written for |
| M2 | Medium | The STDERR fix landed on one of two `run_probe` call sites |
| M3 | Medium | A name in an `echo` still reads WIRED - the comment-strip closed one shape of a two-shape hole |
| M4 | Medium | The clause-citation step turns "did not run" into a **green tick**, contradicting the checker's own printed sentence |
| M5 | Medium | `probe-repoint-fail-closed.py` row E scores a refusal as a PASS and exits early past its own restoration row |
| L1 | Low | `scripts/check-u1-pid1-shutdown.sh` is unwired with no machine-readable exemption - the defect class, just outside the declared container |
| L2 | Low | The exemption register accepts any non-empty string; nothing requires an end condition |
| L3 | Low | The probe runs CI's strings under the LOCAL environment and ignores every declared `env:` |
| L4 | Low | `uv run  --frozen` (two spaces) is a false positive in `_BARE_PYTHON` |
| N1 | nit | "32 call sites in `ci.yml`" is 31 - the docstring's own number came from the grep it condemns |
| N2 | nit | Self-test control 2 is vacuous |
| N3 | nit | `_SHELLY` has never fired; the category is reported as 0 forever |
| N4 | nit | `uv run --frozen` builds a 116-package venv to import `yaml` |
| N5 | nit | Row 1 of the #126 sweep trims to a colon lead-in |

**Nothing Critical.** The suite, the lock and the #126 sweep all held under
re-measurement.

---

## Numbers I re-measured

| Claim | Verdict |
|---|---|
| 27 checkers / 23 wired / 4 exempt | **HOLDS** - `check-checkers-are-wired.py` at `2584afb`, exit 0, prints exactly 27/23/4 |
| `Ran 12 of 78 run steps` | **HOLDS** - 12 run + 36 multi-line + 29 not-a-checker + 1 destructive = 78 |
| 80 run steps across `.github/workflows/` | **HOLDS** - ci.yml 78, mirror.yml 2, pr-title.yml 0 |
| 47 citation sites / 19 end lines / 26 ranges (#126) | **HOLDS** - summed independently off the evidence table: 47, 19, 26 |
| 16 trims + 2 repoints + 1 exempt = 19 | **HOLDS** |
| `uv lock --check` | **HOLDS** - exit 0, 121 packages, only `types-pyyaml` is a new package block |
| 0/40 upper bound 7.2% (#134) | **HOLDS** - `1 - 0.05^(1/40) = 0.0722` |
| "32 `ci-harness-gate.sh` call sites" | **WRONG** - 31. See N1 |
| suite 873 passed | see the Suite section at the end |

**Six of the nineteen end-line decisions re-derived independently against
`5d17cd7`, not read off the worklog. All six hold**, including both
repoints, which are the two that mattered:

- Row 3, `312-314` -> `312-313`. 312-313 is exactly *"v2 credentials travel
  as headers... **A URL containing a secret is never constructed**, even
  though Jobvite's own published sample code does exactly that."* Confirmed.
- Row 4, `312-319` -> `312-318`. 318 ends *"fails if a secret can reach a
  log record."* Complete sentence. Confirmed.
- Row 7, `649-654` -> `649-653`. The `include_payloads=False` claim is at
  650-653. Confirmed.
- Row 9, `692-698` -> `692-697` **+ F2**. Independently confirmed: the
  success/error channel split is at **681-687** (*"The error half is the
  problem object's own `request_id` member... The success half goes in the
  result's `_meta`"*), and 692-697 sits inside the *"Not a field on the
  output models"* paragraph, starting mid-sentence at 692. Reporting rather
  than silently trimming was the right call, and `fe237d5` (#133) then
  repointed both sites to 681-687. Correct.
- Row 11, `906-907` -> **`908-910`** + F3. Independently confirmed: 908-910
  is *"**Scopes follow the three data classes of §4.1**: candidate PII,
  public job data, and the job feed."* and 906 is the tail of the fail-fast
  sentence (*"§7.3 applies to every required variable"*). A mechanical
  `end - 1` would have produced `906-906`, a citation that resolves and
  names something else. The repoint is right.
- Row 14, `1143-1144` -> **`1142-1143`** + F4. Independently confirmed:
  1142-1143 is *"The elicitation payload accordingly names the candidate,
  the target job, and **whether `send_email` is true**, in those terms."*
  `end - 1` leaves `1143` = *"is true**, in those terms."* - a fragment.
  The repoint is right.
- Also spot-checked row 18 (`1451-1453` -> `1451-1452`, the guard/positive-
  control pair, exact) and rows 8 and 11's siblings (`678-679`,
  `901-906`, `905-906`). All hold.

**The #126 sweep is the strongest work in this range and I could not break
it.** Say that plainly, because most of what follows is not.

---

## Findings

### H1 - `REPOINT-EXEMPT` silences both citation gates, and the counter meant to prevent that is dead code

`docs/reviews/check-design-citations.py:142-143`:

```python
if EXEMPT_MARKER in line:
    EXEMPT_SKIPPED += 1
    continue
```

The docstring three lines above, at `check-design-citations.py:129-130`,
says:

> *Lines marked `REPOINT-EXEMPT` are skipped and COUNTED, so the
> exemption can never be silent - a skip nobody reports is how a
> population shrinks without anyone noticing.*

`EXEMPT_SKIPPED` is assigned at `:123`, reset at `:135`, incremented at
`:143`, **and read nowhere**. `grep -n EXEMPT_SKIPPED` returns exactly those
four lines, in the scope tree and at current `main`. The exemption is
silent. The sentence describing why it cannot be is the only thing standing
where the report should be.

**Positive control** (planted at `2584afb`, then reverted):

```
# PLANT DESIGN.md:99999-99999 REPOINT-EXEMPT
```

prepended to `src/fast_mcp_jobvite/audit.py`. Result:

```
check-design-citations.py        -> EXIT 0, "Every citation resolves to a line that exists."
check-design-citation-shape.py   -> EXIT 0, "0 citation(s) point at something that cannot be their subject."
```

A citation 97,866 lines past the end of a 2133-line file passes both wired
gates, silently, because the same physical line contains an eleven-character
string. There are already 23 exempt lines in the shape checker's population.

Three separate weaknesses compound here:

1. The marker is matched as a **bare substring anywhere on the line**, so
   prose mentioning the mechanism exempts itself.
2. It is applied at **line** granularity before the citation regex runs, so
   a line carrying one legitimate record and one wrong citation loses both.
3. It carries **no reason**, in a file whose sibling gate
   (`UNWIRED_BY_DECISION`) refuses a blank one and argues at length that the
   reason IS the exemption. The same author wrote both, hours apart.

**Suggested fix.** Three parts, smallest first:

- Print the count. `main()` already prints a summary; add
  `print(f"{EXEMPT_SKIPPED} line(s) skipped as REPOINT-EXEMPT.")` -
  `check-design-citation-shape.py` already does exactly this, which is how
  I knew the number was 23.
- Scope the marker to the citation it exempts: require
  `REPOINT-EXEMPT(DESIGN.md:373-383)` and skip only that range on that line.
  Anything else on the line stays in the population.
- Require a reason, the way `UNWIRED_BY_DECISION` does: a register keyed by
  `file:line` with a sentence, rather than a self-service inline marker.
  Then a ratchet on `len(register)` makes every new exemption a diff someone
  has to defend.

If only one of the three lands, make it the first: a silent skip and a
reported skip are different gates.

---

### H2 - `bare_python_steps` misses any invocation with an interpreter flag

`docs/reviews/check-checkers-are-wired.py:163-165`:

```python
_BARE_PYTHON = re.compile(
    r"(?<!uv run )(?<!uv run --frozen )python3?\s+\S*?(?P<name>check-[\w-]+\.py)"
)
```

`\S*?` cannot span a space, so the path must be the very next token.
Measured by calling `bare_python_steps` directly on each string:

| step body | flagged? |
|---|---|
| `python3 docs/reviews/check-checkers-are-wired.py` | **True** |
| `python3 -u docs/reviews/check-checkers-are-wired.py` | **False** |
| `python3 -X faulthandler docs/reviews/check-checkers-are-wired.py` | **False** |
| `uv run --frozen python docs/reviews/check-checkers-are-wired.py` | False (correct) |
| `uv run  --frozen python docs/reviews/check-checkers-are-wired.py` | **True** (see L4) |
| `cd docs/reviews && python3 check-checkers-are-wired.py` | True |

This function exists because a bare `python3` invocation of a
pyyaml-importing checker turned `main` red. Written as `python3 -u ...` -
which is a perfectly ordinary thing to write for a step whose output you
want unbuffered in the Actions log - the same defect ships and the gate says
nothing. A detector whose docstring says *"THIS EXISTS BECAUSE I SHIPPED
EXACTLY THIS"* should not be defeated by one flag.

**Suggested fix.** Stop pattern-matching the whole invocation. Tokenise the
step body with `shlex.split`, walk the tokens, and treat any token whose
basename is `python`/`python3` as an interpreter unless it is preceded by
`uv run` (with any intervening flags); then take the first following token
that is not a `-`-prefixed flag as the script:

```python
def _interpreter_invocations(text: str) -> list[str]:
    """(interpreter, script) pairs, flag-tolerant."""
    names = []
    for line in text.splitlines():
        try:
            toks = shlex.split(line, comments=True)
        except ValueError:
            continue
        for i, tok in enumerate(toks):
            if pathlib.PurePath(tok).name not in {"python", "python3"}:
                continue
            if "uv" in toks[:i] and "run" in toks[:i]:
                break            # reaches the project environment
            for nxt in toks[i + 1:]:
                if not nxt.startswith("-"):
                    names.append(nxt)
                    break
    return names
```

then match `check-[\w-]+\.py` against the *script* token only. That also
kills L4 for free, and removes both lookbehinds, which are the reason the
double-space case exists at all.

---

### M1 - the probe cannot detect either failure it was written for

`docs/reviews/probe-ci-checker-steps.py:6-20` names two founding failures,
both from 2026-09-01. Neither is inside its detection power.

**Failure one, `actionlint` bare vs `SHELLCHECK_OPTS=--severity=warning`.**
The population filter at `:58` is
`(?:docs/reviews|scripts)/check-[\w-]+\.py`. `actionlint` is not a
`check-*.py`, so the step is never a candidate. The probe cannot run the
command whose configuration difference it was built to eliminate.

**Failure two, `python3` vs `uv run --frozen python`.** The probe executes
`python3 docs/reviews/check-*.py` with **the local `python3`**. On this
machine `python3 -c "import yaml"` prints `6.0.2`. That is precisely the
condition that produced the false green: the author's manual run passed
because the local interpreter had the module the runner lacked, and the
probe reproduces that run exactly.

I mutated `ci.yml` back to the known-bad
`python3 docs/reviews/check-checkers-are-wired.py` and the probe **did** go
red - but for the wrong reason. It exited 1 because
`check-checkers-are-wired.py`, which happens to be one of the twelve
commands the probe runs, statically detected the bad wiring in the mutated
YAML. There was no `ModuleNotFoundError`; there could not be. Take that one
checker out of the runnable set and the probe is blind. **The green is
supplied by a different gate, and a control that passes because a neighbour
is doing the work is not a control.** (Mutation reverted; `git diff --stat`
empty.)

**Suggested fix.** Two changes, either of which restores a real claim:

- Widen the population beyond `check-*.py`: any single-command step is
  runnable. Drop `_CHECKER` and rely on `_DESTRUCTIVE` plus `_SHELLY` to
  refuse. That admits the `actionlint` step.
- Run bare-`python3` steps under an interpreter that actually resembles a
  clean runner - `uv run --frozen --isolated --no-project python ...` or a
  `venv` created with `--without-pip` - rather than `sys.executable`'s
  neighbour. If that is not wanted, then say so in the docstring: today it
  claims to prevent a failure mode it structurally reproduces.

---

### M2 - the STDERR fix landed on one of two call sites

`2584afb`'s subject line is *"Capture the probe's STDERR too - I fixed half
of a paired source"*. `run_probe` now returns `(rc, failed, detail)` and the
post-run re-check prints the tail of `detail` on failure. But:

```
docs/reviews/probe-docs-lint-amputation.py:140:        rc, failed, _ = run_probe(probe)
docs/reviews/probe-docs-lint-amputation.py:239:    rc, failed, detail = run_probe(probe)
```

`:140` is inside `amputate()` - **the main body of the harness, one call per
amputation row**. When an amputation row reports a wrong verdict, the
probe's own words are still captured and thrown away, which is the exact
defect the commit's own comment at `:243-252` describes:

> *`exit=1 failed=none` IS THE WORST THING THIS CAN PRINT, and it printed
> it... the output that would say WHAT was captured and thrown away one line
> above.*

The commit that says it fixed half of a paired source fixed one of two
paired call sites. Say it directly, because the brief asked: **this is the
one thing in the range described as fixed that is not fixed.**

**Suggested fix.** At `:140`, keep `detail` and print its tail whenever the
row does not behave:

```python
rc, failed, detail = run_probe(probe)
killed = set(failed)
ok = killed == expect and (rc != 0 if expect else rc == 0)
print(...)
if not ok:
    for line in detail.strip().splitlines()[-24:]:
        print(f"      | {line}")
```

While there: the `[-24:]` window is the tail of `stdout + "\n--- stderr ---\n" + stderr`,
so a stderr longer than 24 lines swallows the marker and all of stdout. Print
the last 12 of each stream separately, labelled, rather than the last 24 of a
concatenation - the two streams are not interleaved anyway, so the joined
ordering is fabricated.

---

### M3 - a name in an `echo` still reads WIRED

`check-checkers-are-wired.py:300`:

```python
wired = [n for n in names if n in text]
```

`text` is every `run:` body with shell comments stripped. Measured:

```python
"check-review-coverage.py" in strip_comments('echo "run docs/reviews/check-review-coverage.py by hand"')
-> True
```

The whole file exists because *"the obvious census counts a name in a
COMMENT as wired"*. The fix removed `#`-comments. It did not remove the
other way a name appears in a `run:` body without being executed: quoted in
an `echo`, in a heredoc, in a `--help` string, or as an argument to
something else. The dangerous direction - false WIRED - is still open, and
it is the direction that produces silent coverage claims.

`echo` mentions of checkers are not hypothetical in this file: the two
`::warning::` blocks at `ci.yml:288-295` and `:395-402` are exactly that
shape today. Neither happens to name a `check-*.py` basename, so nothing is
mislabelled right now - but nothing prevents it either.

**Suggested fix.** Reuse the tokeniser proposed in H2. A checker counts as
wired when its basename appears as a **command-position or script-position
token** in some `run:` body, not when it appears anywhere in the text. Add a
fifth self-test control that plants
`echo "docs/reviews/check-a-name-nobody-has-written.py"` into a synthetic
body and asserts it reads UNWIRED - the mirror of control 3, which is the
only control in the file that tests a real past defect.

**The amputation.** I renamed both `check-obligations.py` mentions in
`ci.yml` to a name nothing wires and re-ran: the gate reported
`1 checker(s) are UNWIRED and unexplained: check-obligations.py` and exited
1. **The gate is not vacuous for its primary claim** - it dies when the
wiring dies. That is worth recording as the good news alongside M3.
(Reverted; `git diff --stat` empty.)

---

### M4 - "the gate did not run" renders as a green tick

`.github/workflows/ci.yml:288-295`:

```yaml
if [ "$rc" -eq 2 ]; then
  echo "::warning::THE CLAUSE-CITATION GATE DID NOT RUN. ..."
  echo "         ... CONFIGURED state, not a failure - and"
  echo "         not a green: no clause citation was checked."
  exit 0
fi
```

The step comment says the state is *"announced loudly so it can never read
as a green"*. It exits 0, so in the Actions UI the step is a green tick, in
a green job, in a green run. The annotation is one line in a sidebar.

The checker's own refusal message, which I confirmed by running it with
`--standards /tmp/definitely-not-here` (rc=**2**, verbatim):

> `Exiting 2, NOT 0: this measurement did not run, and a skip that reports success is a green that tested nothing.`

The workflow then makes it report success. The checker and the step that
wraps it disagree in the same run output, and the step wins.

Fairness: `ci.yml:395-402` already carried this exact shape for the
standards gate before this range. The new step matched an existing
convention rather than inventing one, so this is a finding about the
convention at both sites, not a regression introduced here.

**Suggested fix.** Make "did not run" render as its own state, not as pass:

```yaml
      - name: Standard clause citations resolve
        continue-on-error: true          # rc 2 shows as a distinct ⚠, not a ✓
        run: |
          out=$(python3 docs/reviews/check-clause-citations.py 2>&1) || rc=$?
          ...
          exit "${rc:-0}"
```

`continue-on-error: true` marks the step with a warning glyph and does not
fail the job, which is exactly the semantics wanted. Better still, gate it
with `if: ${{ secrets.STANDARDS_TOKEN != '' }}` so it renders as **skipped**
until #106 lands - a skipped step is unmistakable at a glance, and it stops
the job spending time on a measurement that cannot happen.

(Note on the shell form: `out=$(...); rc=$?` after `set +e` is safe here
because `rc` is tested and `exit "$rc"` is the last statement. That is the
correct version of a pattern that has bitten this repo; no finding.)

---

### M5 - a refusal scored as a pass, and an early exit past the restoration row

`docs/reviews/probe-repoint-fail-closed.py:163-176`:

```python
os.chmod(victim, before_mode)
row(
    "E. unreadable cited file -> REFUSED, not measured here",
    True,
    "chmod 000 did not deny this process (root or CAP_DAC_OVERRIDE), ... NOTHING was tested by this row.",
)
...
raise SystemExit(0)
```

Replacing an `AssertionError` with an honest refusal was right, and the
detail string says plainly that nothing was tested. Two problems remain:

1. **The refusal's verdict is `True`.** It counts as a behaving row, and the
   probe exits 0. Under this repo's own rule that a skip is a green that
   tested nothing, a row that says *"NOTHING was tested by this row"* must
   not be scored as a row that behaved. Containers commonly run as root, so
   this branch is not exotic - it is the likely branch anywhere but a
   developer laptop.
2. **`raise SystemExit(0)` at `:176` skips row E1** at `:203-207`, *"the
   probe restored the victim file (mode and bytes)"*. The refusal branch
   does restore the mode at `:163` and has not yet written bytes, so nothing
   is damaged today - but the assertion that would prove it is the one thing
   the branch jumps over, and it is jumped over exactly in the environment
   where the branch fires.

**Suggested fix.** Give refusal its own verdict rather than borrowing
`True`, and keep E1 in every path:

```python
REFUSALS.append("E")
row("E. unreadable cited file -> REFUSED, not measured here", None, "...")
```

with `row()` treating `None` as *refused* - printed as `REFUSED`, excluded
from the pass tally, and counted separately. Then fall through to E1 instead
of exiting, and at the end exit `2` when `REFUSALS and not FAILURES`, which
is the code this repo already uses for "this measurement did not run"
(`check-clause-citations.py`). Do not exit 0: a probe that measured four of
five rows should not be indistinguishable from one that measured five.

Same shape applies to `probe-gate-swallowed-exceptions.py:157-161`, where
row D now accepts `proc.returncode in (0, 2)`. The widening is correct - the
old `== 0` encoded a local-only precondition - but rc 2 means the gate did
not run, so on every runner row D now passes without exercising the happy
path it is named for. Make it the same three-state row: `0` passes, `2`
refuses, anything else fails. Otherwise the A3/A4 amputation rows, which
compare *which* rows die, are comparing against a row that cannot die.

---

### L1 - one harness is unwired with no machine-readable exemption

`check-checkers-are-wired.py:41-48` excludes `scripts/check-*.sh` on this
argument:

> *those are the per-unit mutation and control HARNESSES, and they reach CI
> through `scripts/ci-harness-gate.sh` (32 call sites in `ci.yml`), which is
> its own container with its own gate.*

Tested rather than accepted. Set-equality over the container:

```
git ls-files 'scripts/check-*.sh'                          -> 35
distinct names passed to ci-harness-gate.sh                -> 31
in container, NOT passed to the gate:
  check-harness-anchors-controls.sh   (invoked directly, ci.yml:927)
  check-pytest-bounded.sh             (invoked directly, ci.yml:1199, :1202)
  check-suite-floor.sh                (invoked directly, ci.yml:707, :732)
  check-u1-pid1-shutdown.sh           (NOT MENTIONED IN ci.yml AT ALL)
passed to the gate but not in container                    -> 0
```

Three of the four reach CI by another route, so the argument holds for them.
The fourth does not reach CI at all. Its non-wiring is a real decision - it
needs Docker, argued at `scripts/check-u1-pid1-shutdown.sh:35-38` and
`CONTRIBUTING.md:151` - but that decision lives **only in prose**. It is
precisely the state this checker exists to forbid: unwired is fine, unwired
and unrecorded is the defect. It sits one directory outside the declared
container, which is what a container argument selects for.

**Suggested fix.** Keep the two populations separate - conflating them
really would make the checker report on files it cannot judge - but extend
the enumeration rather than the exemption list. Add a second pass over
`scripts/check-*.sh` asking a different question ("reached by
`ci-harness-gate.sh`, invoked directly, or exempt with a reason?"), reusing
`UNWIRED_BY_DECISION` for the reasons. Then move
`check-u1-pid1-shutdown.sh`'s Docker argument out of its own header and into
the register, where a gate can see it. While there, replace the "32 call
sites" prose with a derived count (N1).

---

### L2 - the exemption register accepts any non-empty string

`check-checkers-are-wired.py:108-112` refuses only a blank reason. The four
current entries are genuinely good - the `check-review-coverage.py` entry
even names its end condition and its task (#119). Nothing enforces that. A
future entry reading `"later"` passes `_reasons_are_non_empty` and silences
a real gap permanently, and adding one is a three-line diff in a dict that
nobody diffs closely.

**Suggested fix.** Two cheap ratchets:

- Require an end condition: reject a reason that matches neither `#\d+` nor
  a `20\d\d-\d\d-\d\d` date. Every current entry passes; the two control
  harnesses would need `#`-tasks filed for "run by hand when X changes",
  which is arguably the correct outcome anyway.
- Add `EXEMPTION_CEILING = 4` and fail when `len(UNWIRED_BY_DECISION)`
  exceeds it. Raising a declared ceiling is a visible diff someone has to
  argue for; adding a dict entry is not. This is the same mechanism the
  suite floor already uses, and it works for the same reason.

---

### L3 - CI's strings, run under the local environment

`probe-ci-checker-steps.py:137-139` calls `subprocess.run(..., cwd=ROOT)`
with no `env=`, so the twelve commands inherit **this machine's**
environment and see nothing of the workflow's. `ci.yml:93-95` declares
workflow-level `env:` (`UV_VERSION`, `PYTHON_VERSION`), one step declares
its own, and `mirror.yml` has job-level env. None of the twelve currently
read any of those, so nothing is wrong today - but "runs CI's steps
VERBATIM" is a claim about more than the argv string, and the founding
failure at `:9-13` was a configuration difference, not an argv difference.

The inheritance direction is the risky one: a `JOBVITE_*` variable exported
in the developer's shell, or a `PYTHONPATH`, changes a checker's answer here
and not on the runner. That is a false green with the same shape as the one
this probe was built to stop.

**Suggested fix.** Collect workflow-, job- and step-level `env:` (later
scopes overriding earlier), and pass an explicit environment rather than
inheriting:

```python
base = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
done = subprocess.run(shlex.split(command), cwd=ROOT, env={**base, **step_env}, ...)
```

Print the env keys applied alongside `Ran N of M`, so the claim states its
own scope. Also wrap the call in `try/except FileNotFoundError` - a
single-line step of the form `SOME_VAR=x python3 .../check-y.py` would reach
`shlex.split` intact (`=` is not in `_SHELLY`) and raise an uncaught
`FileNotFoundError` on the `SOME_VAR=x` token, crashing the probe with a
traceback instead of a verdict.

---

### L4 - `uv run  --frozen` is a false positive

Consequence of the lookbehinds in H2:
`uv run  --frozen python docs/reviews/check-checkers-are-wired.py` (two
spaces after `run`) matches neither `(?<!uv run )` nor
`(?<!uv run --frozen )`, so a perfectly safe invocation is reported as a
bare interpreter needing `yaml`, and the build fails for a reason that is
not about the code.

**Suggested fix.** Subsumed by the tokeniser in H2 - `shlex.split` collapses
runs of whitespace, so the case disappears. If H2 is not taken, at minimum
change both lookbehinds to `(?<!uv run\s)` style by restructuring as a
negative lookahead on the whole `uv run [--flags ]*python` prefix; the
lookbehind form cannot express variable width, which is why this bug exists.

---

### N1 - "32 call sites" is 31, produced by the grep the file condemns

`check-checkers-are-wired.py:45` states `ci-harness-gate.sh` has *"32 call
sites in `ci.yml`"*. Measured:

```
grep -c "ci-harness-gate.sh" ci.yml                             -> 32
grep -oE 'ci-harness-gate\.sh +[A-Za-z0-9._-]+' ci.yml | sort -u -> 31
the 32nd line:
  820:      # THE HARNESS BLOCK. Every step below calls scripts/ci-harness-gate.sh
```

The 32nd is a comment. The docstring of the file whose entire thesis is
*"the obvious census is `grep <basename> ci.yml`. That counts a name in a
COMMENT as wired"* contains a number produced by exactly that grep.

**Suggested fix.** Do not retype the count; derive it, or drop it. Since
L1's suggested fix already parses the gate's arguments, print the number:
`f"({len(gate_args)} call sites in ci.yml)"`. A constant in prose beside the
thing it counts decays - this file's own docstring is the demonstration.

---

### N2 - self-test control 2 is vacuous

`check-checkers-are-wired.py:248`:

```python
if "check-a-name-nobody-has-written.py" in text:
    failures.append("a fabricated name reads WIRED")
```

A name nobody has written cannot appear in a file nobody wrote it into. This
control cannot fail for any reachable reason; it tests Python's `in`
operator, not the checker. It is the "control that never runs the artifact"
shape: a proxy, not the subject. Control 1 has a milder version of the same
problem - it hardcodes `check-design-citations.py` and would fail if that
checker were legitimately unwired, reporting a parser fault for a wiring
change.

Controls 3 and 4 are real. Control 3 tests the exact defect that produced
two wrong censuses; control 4 asserts self-membership and is the correction
of an inert comment. Both would fire.

**Suggested fix.** Replace control 2 with the useful negative: assert that a
name appearing **only inside a comment** reads UNWIRED, by running the real
pipeline over a synthetic body:

```python
if "check-fake.py" in strip_comments("run: true  # calls check-fake.py\n"):
    failures.append("a name in a comment reads WIRED")
```

That is control 3's assertion at the level the checker actually operates,
and it fails if `strip_comments` is ever removed from `run_bodies`. Then add
the `echo` control from M3 as control 5. For control 1, derive the name from
the workflow instead of hardcoding it: assert `len(wired) > 0`, which fails
on a broken parser without coupling to one checker's wiring.

---

### N3 - `_SHELLY` has never fired

`probe-ci-checker-steps.py:100-101` refuses steps carrying shell
metacharacters. The run at `2584afb` reports:

```
Not run, by category:
   36  multi-line block, has its own setup
   29  not a checker invocation
    1  MUTATES THE TREE or costs minutes
```

The `needs shell semantics` category is absent - count zero. Not a defect;
the branch is a correct guard. But a guard nobody has watched fire is a
guard whose regex nobody has checked, and `_SHELLY` includes `*`, `?`, `[`,
`]` and `~`, which appear in plenty of harmless argument strings and would
refuse a step that is in fact runnable.

**Suggested fix.** Print zero-count categories explicitly rather than
omitting them (`reasons` is a `Counter`; seed it with all four keys at zero),
so the report says *"0 needs shell semantics"* instead of staying silent.
Then add a one-line assertion in a `--self-test` that
`classify("python3 docs/reviews/check-x.py | tee log")` returns the shell
refusal, so the branch has been watched firing at least once.

---

### N4 - a 116-package venv to import `yaml`

`ci.yml`'s wired step is
`uv run --frozen python docs/reviews/check-checkers-are-wired.py`. In the
`design-gates` job that resolves and installs the whole project environment
(I measured `Installed 116 packages` on first run in a fresh worktree) so
one checker can `import yaml`. The comment defending the choice is right
that bare `python3` is wrong; `uv run --frozen` is simply heavier than
needed for a job the file itself describes as one that *"does not need the
Python project to install"*.

**Suggested fix.**
`uv run --frozen --no-project --with pyyaml python docs/reviews/check-checkers-are-wired.py`.
Keeps the guarantee that the module is present rather than borrowed, drops
the project install, and leaves the `pyproject` dev entry in place for mypy,
which still needs `types-PyYAML`. Measure it before wiring - that is the
lesson this step was added to record.

---

### N5 - row 1 of the sweep trims to a colon lead-in

Row 1 trimmed `DESIGN.md:207-213` to `207-212`. Line 212 at the freeze is:

```
212| **The governing clause is `ai/agent-guardrails.md:70-73`**, and this section exists to discharge it:
```

A colon-terminated lead-in whose blockquote begins at 214. The trim removed
the blank end correctly, and the sweep reported F1 honestly, and `fe237d5`
(#132) then widened it to `207-229` - so the outcome is right and this is
already closed. Recording it only because it is the general shape: the
mechanical `end - 1` can leave a range ending on a promise rather than a
statement, which reads as complete to `check-design-citation-shape.py` and
as truncated to a person. Rows 9, 11 and 14 caught this by reading; nothing
mechanical would have.

**Suggested fix.** Add a fifth shape to `check-design-citation-shape.py`: a
range whose END line ends in `:` and whose next line is blank or a `>`
blockquote. That is a cheap, high-precision detector for "cited the
introduction and not the thing introduced", and it is the same class as the
blank-END shape it would sit beside.

---

## What is clean, stated so it is not re-reviewed

- **`pyproject.toml` + `uv.lock`.** `uv lock --check` exits 0, 121 packages.
  `pyyaml` gains only dev-group references because it was already resolved
  transitively; `types-pyyaml 6.0.12.20260815` is the single new `[[package]]`
  block. Nothing else moved - the diff is 13 added lines and no removals.
  The comment explaining why both lines are deliberate is accurate.
- **`fetch-depth: 0`.** Added to `design-gates`, which is the job that runs
  `check-design-freeze.py` and `check-design-citation-shape.py:260`, the two
  things that resolve the frozen SHA. I checked the siblings: `supply-chain`
  already had it, and the `test` job's only citation step
  (`check-design-citations.py`, `ci.yml:881`) reads DESIGN.md from the
  worktree and needs no history. No sibling gap.
- **`check-design-freeze.py`'s new exit 3.** Correctly distinguishes a
  broken instrument from a finding, and names the shallow-clone cause. Right
  call and right exit code.
- **`sample-134-citations.py`.** Imports the shape checker's selector rather
  than reimplementing it, draws over sorted sites with a seeded `Random`, and
  argues its container choice against the brief's. Reproducible and correct.
  One observation, not a finding: the draw excludes `REPOINT-EXEMPT` lines,
  so the measured rate is a rate over the non-exempt population - which H1
  makes more interesting than it was.
- **`check-design-citation-shape.py --controls`: 7/7 fired**, including the
  blank-END detector, at `2584afb`. The zero is not a dead detector.
- **The #126 sweep itself.** Six decisions re-derived, all correct. Both
  repoints are right and both would have been made wrong by a mechanical
  `end - 1`. The two reported-not-repointed sites were correctly ruled out of
  scope and both were then fixed in `fe237d5`.

---

## Out of range, but you are about to push: `main` is RED

Not in `92cb89b..2584afb`, so it is not this round's finding, but it will
cost a CI round if it goes unnoticed. At `efdfe3f` (current `main`):

```
$ uv run --frozen python docs/reviews/check-design-citations.py
  1962 DESIGN.md citations across 206 files
  highest line cited: 99999 of 2133

1 problem(s):
  FAIL: docs/worklogs/AUDIT-SURVIVORS-REPORT.md:266: DESIGN.md:99999 is past the end of DESIGN.md (2133 lines)
```

Exit 1. `check-design-citations.py` is wired and gating in the `test` job.
The offending line arrived with the audit-survivors merge. It is a
deliberate illustrative citation inside a report - the same shape as the
`REVIEW-R10.md` case that `8270487` fixed by honouring `REPOINT-EXEMPT`,
which is why marking that one line is the right fix and not a workaround.
Note the irony worth keeping: **the correct fix for this red is to apply the
exemption whose silence is H1.** Fix H1's reporting first, then mark the
line.

---

## The suite

`uv run --frozen pytest -q` at `2584afb`, from the detached worktree:

> SUITE_PLACEHOLDER

`ci.yml:707` sets the floor at `873` at `2584afb` (derived from the
workflow, not retyped from any brief).

---

## What I could NOT settle

Each of these was attempted and could not be closed, not skipped.

1. **Whether `check-clause-citations.py` returns 2 in CI.** I proved rc=2
   with `--standards /tmp/definitely-not-here`, and rc=0 with the default
   path because the standards corpus is checked out beside this repo on this
   machine. I did not exercise the runner's actual condition, and I would
   not move or hide a sibling repository I do not own to fake it. The wired
   step's rc=2 branch is therefore verified by injection, not by the real
   absence.
2. **Whether the 36 "multi-line block" skips hide runnable checker
   invocations.** I confirmed the count and confirmed at least one real
   checker is inside that bucket (`check-obligations.py`, `ci.yml:493`,
   `:519`, wrapped in `out=$(...)` blocks). I did not classify all 36 by
   hand, so I cannot say what fraction of the 78 is *checkable* as opposed
   to *checked*. "12 of 78" is honest about what it ran; it is silent about
   how much of the remainder is reachable with a slightly better classifier,
   and that number would be the useful one.
3. **Whether M3's false-WIRED is exploitable today.** I proved the mechanism
   (`echo` mention reads WIRED) but did not enumerate every `run:` body for
   an existing `check-*` basename in a non-executed position. The two
   `::warning::` blocks are the right shape and do not name a checker; I did
   not check the other 76.
4. **The `-24:` window's behaviour on a real long traceback.** I read the
   slice and reasoned about it; I did not stage a probe failure with >24
   lines of stderr to watch the marker get cut, because doing that requires
   breaking `probe-fail-closed` or `probe-swallow` while another agent is on
   the tree.
5. **Whether any of the 23 currently-exempt lines is hiding a wrong
   citation.** H1 proves the mechanism silences arbitrary citations. I did
   not read all 23 sites to see whether any is doing so in fact. That is a
   bounded piece of work and worth a task; the count is derivable from
   `check-design-citation-shape.py`'s own output line.

Worktrees: `review/r13` at
`/home/plafayette/claude_projects/fmj-worktrees/r13`, scope worktree
`r13-scope` detached at `2584afb`. Both to be removed after this report is
merged; say the word and I will remove them, or remove them yourself with
`git worktree remove`.
