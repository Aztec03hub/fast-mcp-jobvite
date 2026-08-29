# R2-FIXES - the ten verified-open leftovers, and the one that stays wrong

**Agent:** `r2-fixes` (task #45)
**Branch:** `fix/r2-leftovers`, from `main` at **`7bfd3eb`**
**Worktree:** `/tmp/r2-fixes-work`, `git worktree add /tmp/r2-fixes-work 7bfd3eb`. The shared
checkout was never touched. **No `git stash` and no `git checkout <path>` was run at any point** -
every restore is a `cp` from `/tmp/r2fix-backup/` proven with `cmp`, and every harness restore is the
harness's own.
**Authority:** `docs/reviews/R2-LEFTOVER-VERDICTS.md`, read before the brief and reproduced before
being believed.

## Baseline, measured before anything changed

```
$ grep -oE 'check-suite-floor\.sh [0-9]+' .github/workflows/ci.yml | head -1
check-suite-floor.sh 421
$ PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q
421 passed, 6 deselected in 39.85s          # exit 0
```

421 passed, **0 skipped**, at the floor.

## Result

| Finding | Verdict here | Mutation/amputation | Before | After |
|---|---|---|---|---|
| M-1 | FIXED | `from None` removed | test red | test green, mutant red |
| M-2 | FIXED | three process arms | 3 arms red | 3 green, mutant red |
| M-3 | FIXED | `78 -> 1` | **SURVIVED full suite** | KILLED |
| M-4 residual | FIXED | `.strip()` deleted | held by suite only | held by gate M22 |
| M-8 | FIXED (the comment) | n/a - a comment | - | - |
| L-6 | FIXED | 4 mutations + 1 negative control | - | 4 red, negative green |
| nit-1 | FIXED | n/a - a docstring | - | - |
| nit-2 | FIXED | `SecretStr` branch removed | 3 arms red | 3 green, mutant red |
| nit-3 | FIXED | the fix reverted | 6 arms red | 6 green |
| nit-4 | FIXED | `.lower()` deleted | **SURVIVED full suite** | KILLED |
| M-6 | **STILL WRONG - not fixed** | - | - | - |

**Both surviving mutations are dead.** Re-measured at the full suite, not inferred.

---

# M-1 - `AuditWriteError` rode the redacted-away exception on `__context__`

## FIXED - and the verdict's suggested assertion is wrong

**Reproduced first.** The test was written before the fix and run against the unfixed tree:

```
tests/test_audit.py:493: AssertionError: the raw sink exception rides on __context__
1 failed, 45 passed in 0.10s          # exit 1
```

**The trap the brief named did not bite, because the reproduction does not go through loguru at
all.** `tests/test_audit.py` already ships `_ExplodingLogger`, monkeypatched over `audit.logger`, so
`emit`'s `except` sees the failure directly and loguru's `catch=True` never enters it. The
production path's dependence on `catch=False` is separately held by
`check-u1-boot-controls.sh`'s M17.

**The change** (`src/fast_mcp_jobvite/audit.py`): `raise AuditWriteError(...) from None`, with the
reason recorded beside it.

**THE VERDICT'S SUGGESTED TEST FAILS AGAINST THE CORRECT FIX, and I only found that by running it.**
It proposes:

```python
assert excinfo.value.__context__ is None
```

`raise X from None` sets `__cause__ = None` and `__suppress_context__ = True`. **It does not clear
`__context__`** - the object is still hanging off the exception. Measured:

```
tests/test_audit.py:493: AssertionError: the raw sink exception rides on __context__
```

with the fix applied. So the assertion the report recommends would have sent whoever took it looking
for a second defect that does not exist. What closes the leak is that **no formatter prints it**, so
that is what the test asserts - a formatted traceback carrying no sentinel - with
`__suppress_context__` asserted as the mechanism behind it.

**And the first version of my own test leaked the credential in its failure output**, because
`assert raised.__context__ is None` renders the `OSError`'s repr. Both leak assertions now compute a
bool first, per the convention `test_audit.py:20-22` states and which I had just broken.

**The control.** `from None` removed, anchor asserted unique, landing proven:

```
E  +  where True = _leaks('Traceback (most recent call last): ... ', 'SUPERSECRETSC')
FAILED tests/test_audit.py::test_arm1_the_raise_does_not_carry_the_unredacted_exception_along
1 failed, 45 passed in 0.10s          # exit 1    *** KILLED ***
```

Restored with `cp`, `cmp` clean.

---

# M-2 - a pydantic validation failure exited 1 with a traceback

## FIXED

**Reproduced first**, as three process arms in `tests/test_boot.py`, run against the unfixed tree:

```
FAILED tests/test_boot.py::test_a_constrained_field_is_refused_not_raised[JOBVITE_MCP_PORT-99999]
FAILED tests/test_boot.py::test_a_constrained_field_is_refused_not_raised[JOBVITE_MCP_TRANSPORT-htp]
FAILED tests/test_boot.py::test_a_constrained_field_is_refused_not_raised[JOBVITE_MAX_RESULTS-0]
3 failed, 10 deselected in 3.64s      # exit 1
E   assert 1 == 78
```

**The change** (`src/fast_mcp_jobvite/config.py`): `Settings()` moved inside a `try` in
`load_settings`, `PydanticValidationError` translated to `ConfigurationError` `from None`, and the
reasons built by `_validation_reasons` from each error's `loc` and `msg`.

**`str(exc)` is never used, and that is the half of the fix that matters.** pydantic's rendering
echoes `input_value=` back, and refusal reasons are written to a log. The verdict could not settle
whether that can leak a secret; neither can I, and the answer does not change the fix. `loc`/`msg`
makes the question moot rather than answered, and the test asserts `"input_value" not in combined`
so a future `str(exc)` shortcut goes red.

Each arm asserts four things: `returncode == 78`, the variable named, no `Traceback`, and nothing on
stdout - stdout being the JSON-RPC channel.

```
3 passed, 10 deselected in 3.73s      # exit 0
```

**A gate row was NOT added for this one.** The mutation is a multi-line structural revert rather than
a single unique anchor, and `check-harness-anchors.py` is strongest on one-line anchors. The suite
holds it with three real process arms. Say so if you want it in the harness anyway.

---

# M-3 - the refusal exit status was asserted only against its own constant

## FIXED - the surviving mutation is dead

**Reproduced at the full suite first**, on my branch with the two tests written so far already in it:

```
EXIT_CONFIGURATION_REFUSED = 78  ->  = 1     (anchor count 1, `git diff --stat` 1 insertion)
423 passed, 6 deselected in 39.90s           # exit 0    *** SURVIVED ***
```

**The change**: `tests/test_boot.py::test_the_refusal_status_is_the_sysexits_ex_config_number`,
asserting `== 78` **and** `!= 1` - 1 being the specific value that erases the distinction
`__main__.py:62-65` says 78 exists to make.

**Same mutation, after:**

```
E   assert 1 == 78
FAILED tests/test_boot.py::test_the_refusal_status_is_the_sysexits_ex_config_number
1 failed, 423 passed, 6 deselected in 38.64s   # exit 1   *** KILLED ***
```

Restored, `cmp` clean. **And it is now held by the gate too**, as `check-u1-boot-controls.sh` row
M21, which fired.

---

# M-4's residual - the gate row that never landed

## CLOSED

`grep -n 'strip' scripts/check-u1-boot-controls.sh` found no mutation row, as the verdict said.
Three rows are added, all three FIRED in a real run:

```
[M21 the refusal status is a generic 1] FIRED
[M22 whitespace-only is a present credential] FIRED
[M23 a blank SecretStr is a credential] FIRED
23/23 controls fired.                          # exit 0
```

M22 is R2's own mutation - `not value.strip()` -> `not value`. Its anchor moved into the new
`_is_blank` helper when nit-2 gave the rule a name, so the row anchors there.

---

# M-6 - NOT FIXED, and the reason is evidence rather than deference

I re-ran the falsification myself rather than taking the verdict's word for it:

```
$ git show 3f313ce:docs/DESIGN.md | grep -c "deadline"
5
```

R2's supporting claim - *"`grep -rn "deadline" src/ docs/DESIGN.md` finds none"* - is false at R2's
own pinned SHA, and one of the five hits is the bolded paragraph answering
`backend/resilience.md:74-76` by name. **The finding asked for a deviation record that was already in
the frozen design, one section above the code being reviewed.**

What genuinely remains - `DESIGN.md:373-374`'s **total outbound budget**, implemented by nothing - is
U7's and is on the board as task #43. Not implemented here, not re-filed against U4, and
`services/jobvite_client.py` was not opened.

---

# M-8 - the figure was stale, the mechanism was not

## FIXED, the comment and NOT the machinery

Re-measured rather than retyped:

```
src/fast_mcp_jobvite/__main__.py   88  27  14  3   69%   163->165, 191, 226-232, ..., 426-458
TOTAL                             742  49 146 12   93%
Required test coverage of 80.0% reached. Total coverage: 92.68%
441 passed, 6 deselected in 44.44s
```

`pyproject.toml`'s `[tool.coverage.run]` gains a comment naming the mechanism - the subprocess arms
in `test_boot.py` and `test_shutdown.py` are unmeasured because no `parallel`, `sigterm`,
`concurrency` or `COVERAGE_PROCESS_START` is set - and stating outright that an `omit` row is the
wrong fix.

**No percentage is written into it.** R2 filed 58%, it was 69% when checked, and a per-module figure
in a comment is stale on the next test that lands. The comment says to run `pytest --cov` and read
it. It also records that `fail_under = 80` still does not enforce ADR-0010's per-module floors, which
stays open.

Wiring subprocess measurement needs a `coverage combine` step in `ci.yml`, which is yours.

---

# L-6 - the shutdown case now parses instead of grepping

## FIXED, and M-3's pin was carried across as the brief required

`test_the_shipped_entry_point_is_what_the_case_exercises` now walks the AST for: a `signal.signal`
call whose second argument is `Name("_term")`; an `os._exit` call inside a `Try.finalbody`; **no
`os._exit` call taking any literal argument at all**; and an assignment of `EXIT_SOFTWARE` to
`status`. The two `MARKER_ENTRY` assertions stay substring checks - those are string literals, where
a substring search is the right instrument.

**`assert "EXIT_SOFTWARE = 70" in source` is now `assert EXIT_SOFTWARE == 70`**, the real comparison,
so the one `sysexits.h` number that *was* pinned is still pinned and is now pinned properly.

**Four controls, each anchor asserted unique, each restored with `cp` and verified with `cmp`:**

| Amputation | Result |
|---|---|
| `signal.signal(signal.SIGTERM, _term)` -> `pass` | rc=1 |
| `os._exit(status)` -> `os._exit(0)` | rc=1 |
| `status = EXIT_SOFTWARE` -> `pass` | rc=1 |
| `EXIT_SOFTWARE = 70` -> `= 71` | rc=1 |

**And a NEGATIVE control for what must NOT matter**, which is the whole point of the instrument
change. A comment reading `# NEGATIVE CONTROL: os._exit(0) named in a comment, not called.` inserted
into `__main__.py`:

```
1 passed in 0.84s     # the parser correctly ignores prose
the OLD substring assertion on this same tree: False    # it would have gone red
```

The old form went red on a comment; the new one does not. That is the defect L-6 named, demonstrated
rather than asserted.

**The sibling docstring was rewritten in place, not appended to.**
`test_a_crashing_mcp_run_exits_70_read_from_the_process` opened by describing the structural test as
one that "finds `os._exit(status)` and `EXIT_SOFTWARE = 70` in it" - true of the old instrument and
false of the new one. Its argument is unchanged and still correct: source reading, parsed or grepped,
does not discharge a defect about exit codes.

---

# nit-1 - "registers nothing"

## FIXED, and the test that contradicted it already existed

`config.py`'s `enabled_tools` docstring now says writes-on with `JOBVITE_TOOLS` unset registers **no
write**, and states explicitly that the read tools are registered throughout.

**No new test.** `tests/test_config.py:187-188`
(`test_enable_writes_true_with_tools_unset_does_not_register_the_write`) already asserts
`settings.enabled_tools == READ_TOOLS`, which is exactly the claim the docstring got wrong. The code
was right, one test already held it, and only the prose was false - so the remedy is the prose.

---

# nit-2 - `_empty_is_unset` only stripped `str`

## FIXED, at the rule rather than beside it

The verdict suggested a new loop in `validate_settings`. I put it in the existing rule instead:
`_empty_is_unset`'s inline `isinstance(value, str)` became a named `_is_blank(value)` helper that
unwraps `SecretStr` first. A blank secret is then dropped from the raw mapping, falls back to `None`,
and `_check_required_variables` refuses it through the door that already exists.

**One rule, one place.** A second refusal in `validate_settings` would be the same rule stated twice,
and this module's own doctrine is that empty **is** unset.

**Control, run before the fix** (`tests/test_config.py::test_a_directly_constructed_blank_secret_is_also_unset`,
parametrised over `""`, `" "`, `"\t"`):

```
3 failed, 54 deselected in 0.16s      # exit 1   before
57 passed in 0.21s                    # exit 0   after
```

Plus gate row M23, which fired.

---

# nit-3 - `redact_text` swallowed the closing quote

## FIXED

`redact_text` now splits a trailing run of `'"),.;` off a whitespace-delimited token before handing it
to `redact_url`, and re-appends it.

**Controls, run before the fix:** 6 of the 7 delimiter cases red (`'`, `"`, `)`, `,`, `),`, `".`; the
bare `.` case passed because it lands on `page=2`, which is not secret).

```
6 failed, 5 passed, 33 deselected in 0.04s    # exit 1   before
44 passed in 0.03s                            # exit 0   after
```

**The paired arm the verdict asked for is there:** `test_punctuation_INSIDE_the_secret_is_still_redacted`
parametrises a secret whose own last character is `.`, `)`, `,` or `'` and asserts it is still fully
redacted. Those four passed before and after, which is what makes them a negative control rather than
a second copy of the first test.

**This edit broke a harness anchor and the static checker caught it**, which is exactly the sequence
the brief warned about:

```
STALE ANCHOR  check-u3-audit-controls.sh:214 [shell-arg]  0 hits in .../redaction.py
    anchor: 'out.append(redact_url(token) if "?" in token and "=" in token else token)'
FAIL: 1 of 174 anchors do not resolve uniquely.
```

Repointed at `out.append(redact_url(core) + token[len(core) :])` - the redacting call itself, which is
the mutation's SUBJECT - and the harness re-run confirms it still kills:

```
M15 the exception-message arm stops redacting: killed by test_a_url_embedded_in_an_exception_message_is_redacted
########## RESULT: 15 killed, 0 not killed      # exit 0
```

---

# nit-4 - the lower-cased echo

## FIXED - the second surviving mutation is dead

**Reproduced at the full suite first:**

```
return inbound_request_id.lower()  ->  return inbound_request_id
421 passed, 6 deselected in 38.99s        # exit 0    *** SURVIVED ***
```

**The behaviour chosen is to echo unchanged**, for the verdict's reasons: `_UUID4_RE` is already
`IGNORECASE` so case was never a validity question, and the point of echoing a correlation id is an
exact string join across two systems.

**The replacement literal carries letters** - `A1B2C3D4-1111-4111-8111-11111111CDEF` - which is the
whole mechanism of the nit. The all-digit literal is retained as the first parametrised row.

**Control, the fix reversed** (`.lower()` put back):

```
FAILED tests/test_audit.py::test_a_valid_inbound_uuid4_is_echoed_unchanged[A1B2C3D4-1111-4111-8111-11111111CDEF]
1 failed, 44 passed in 0.10s          # exit 1    *** KILLED ***
```

The all-digit row stayed green under that mutation, which is the nit reproducing itself inside the
test that fixes it.

---

# Gates

Run in `/tmp/r2-fixes-work` on `fix/r2-leftovers`, each judged by its own exit code on its own line,
read from the terminal. **`ruff format` was run BEFORE this pass**, per the brief - it reformatted 2
files and re-broke nothing, and `check-harness-anchors.py` was re-run after it.

| Gate | Result | Exit |
|---|---|---|
| `uv run --frozen ruff check .` | `All checks passed!` | 0 |
| `uv run --frozen ruff format --check .` | clean | 0 |
| `uv run --frozen mypy` | `Success: no issues found in 44 source files` | 0 |
| `uv run --frozen pytest` | **441 passed, 6 deselected, 0 skipped** | 0 |
| `uv run --frozen python docs/reviews/check-quickstart.py` | 1 command ran | 0 |
| `python3 scripts/check-harness-anchors.py --self-check` | **174 anchors, all unique** | 0 |
| `bash scripts/check-harness-anchors-controls.sh` | 9/9 controls fired | 0 |
| `bash scripts/check-u1-boot-controls.sh` | **23/23 controls fired** | 0 |
| `bash scripts/check-u3-audit-controls.sh` | 15 killed, 0 not killed | 0 |
| `bash scripts/check-u1-boot-amputation.sh` | 14 amputations A-N, every assertion died | 0 |
| `bash scripts/check-u0-test-controls.sh` | 11/11 controls fired | 0 |
| `python3 scripts/check-committed-file-types.py --all` | 238 checked, none refused | 0 |
| `python3 docs/reviews/check-design-citation-shape.py` | clean - **still 0, not 1** | 0 |
| `python3 docs/reviews/check-obligations.py` | 31 mappings, 23 anchors verified | 0 |
| `python3 docs/reviews/check-obligations.py --controls` | `post-run re-check: exit=0` | 0 |
| `python3 docs/reviews/check-cross-references.py` | every reference resolves | 0 |

## The new floors - measured, not predicted. **The `ci.yml` edit is yours.**

```
suite floor   421  ->  441      (+20: 3 M-2 arms, 1 M-3, 3 nit-2, 6+4 nit-3, 2 nit-4 rows, less 1 replaced)
anchor floor  171  ->  174      (+3: M21, M22, M23)
```

`ci.yml` was **not edited**. Nothing else in it needs to change for this branch.

# What I could NOT settle

1. **SETTLED after the table above was written**, and recorded here rather than parked:
   `bash scripts/check-u1-boot-amputation.sh` finished at **exit 0**, all fourteen amputations
   A-N - *"Every declared assertion died under its own amputation."* It is the harness that
   amputates `config.py` and `__main__.py`, both of which I changed, so it is the one that mattered
   most. Added to the gate table.

2. **The remaining seven CI harnesses were not run** -
   `check-u4-client-*`, `check-u5-jobs-*`, `check-u11-*`, `check-u15-*`,
   `check-suite-floor-amputation.sh`. None anchors on a file I edited except through
   `check-u3-audit-controls.sh`, which I did run, and the static anchor checker covers all 174
   anchors across all fifteen. This is a statement about what the table above does not cover.

3. **Whether M-2's `input_value=` echo can leak a secret**, unchanged from the verdict. No
   secret-class field carries a pydantic constraint today, so I could not construct the case either.
   The fix is written so the question cannot become live: reasons come from `loc`/`msg`, and a test
   asserts `input_value` is absent from the process output.

4. **`check-u1-pid1-shutdown.sh` (Docker) and `actionlint`** were not run - neither is on this
   machine's path and neither is reachable from these changes.

5. **`main` moved while this ran.** U6 merged and U7 was dispatched. This branch is built on
   `7bfd3eb` and was never rebased; `services/jobvite_client.py` was not opened, which is the file
   those units are in.

The worktree at `/tmp/r2-fixes-work` is left in place until the branch is merged, in case a gate
has to be re-run in it. Remove it after.
