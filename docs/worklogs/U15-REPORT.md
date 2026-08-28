# U15 - The two commit-time gates

**Executed** 2026-08-28, 05:27 PM CDT, against `docs/DESIGN.md` **revision 6, FROZEN**
(`:1576-1586` for the gates, `:1760` for threat row **C8-I1**, rated **Critical**), and
`docs/plans/IMPLEMENTATION-PLAN.md` unit **U15** (`:919-958`).

Toolchain: Python **3.12.3**, uv **0.11.3**, pre-commit **4.6.2**, detect-secrets **1.5.0**, on
Linux. Repo HEAD when this was written: `299cf8b`.

**Nothing is committed and nothing is pushed.** The work is in the tree.

**This unit did not start from zero.** `scripts/check-committed-file-types.py` was already in the
tree, untracked, written 15:44 by the session that hit its limit before landing anything around it.
I inherited it, found two defects in it, and built everything else. There was no
`.pre-commit-config.yaml`, no test, no harness, no baseline, and no CI step.

---

## 1. What landed

| Path | Status | Note |
|---|---|---|
| `.pre-commit-config.yaml` | **new** | both gates. The deliverable |
| `.secrets.baseline` | **new** | detect-secrets' audited baseline, 2 entries, both `is_secret=false` |
| `scripts/check-committed-file-types.py` | inherited + fixed | one real defect fixed (§4 D1) |
| `tests/test_file_type_gate.py` | **new** | 36 assertions |
| `scripts/check-u15-gate-controls.sh` | **new** | mutation harness, 15 controls |
| `scripts/check-u15-gate-amputation.sh` | **new** | amputation harness, 5 trees |
| `.gitignore` | **modified** | vendor-document block widened repo-wide (§3) |
| `.github/workflows/ci.yml` | **modified** | 3 steps added, no restructuring (§5) |
| `scripts/check-u0-test-controls.sh` | **modified, 1 line** | I broke it; §4 D3 |

**The blocking gate landed first**, before the tests, the harnesses and the CI, as briefed. The
brief's warning was well aimed: the session that preceded me delivered a gate script and nothing
that ran it.

---

## 2. Every check, with its real output

### 2.1 The gates blocking real commits, in a throwaway clone with the hooks installed

`pre-commit install`, then real `git commit` attempts. `head_moved` is read from `git rev-parse`
after each attempt, not inferred from the exit code, and the last column is each hook's own verdict.

```
=== do U15's OWN new files pass the gate when staged? ===
committed-file-type gate: 9 file(s) checked, none refused.
EXIT=0

=== FINAL: both hooks, real commits, current files ===
positive-control-ordinary-file     exit=0 head_moved=YES Passed/Passed/
real-PDF-renamed-.md               exit=1 head_moved=NO  Failed/Passed/
NUL-bearing-.txt                   exit=1 head_moved=NO  Failed/Passed/
staged-credential                  exit=1 head_moved=NO  Passed/Failed/
```

**Read the last column.** The PDF is refused by the file-type gate while the secret scanner passes
it; the credential is refused by the secret scanner while the file-type gate passes it. That is
`DESIGN.md:1579-1581`'s claim - *"a CONFIDENTIAL PDF ... passes every secret scanner cleanly"* -
**measured on this tree rather than repeated from the design.** Neither gate is redundant with the
other, and the measurement is what says so.

An **earlier version of this table reported `exit=0` for every refusal**, because I read
`${PIPESTATUS[0]}` after a later command. The refusals were real; my instrument was not. Recorded
because a wrong exit code that agrees with a correct conclusion is exactly the reading that
survives review.

### 2.2 The PDF is a real PDF, not five magic bytes

```
$ file vendor-spec.md
vendor-spec.md: PDF document, version 1.4, 1 page(s)
```

```
COMMIT REFUSED by the committed-file-type gate (DESIGN.md:1579-1586).
A CONFIDENTIAL vendor PDF and an unlicensed RAML reached public remotes
on this project once already. History rewriting did not close it.

  vendor-spec.md: content is a PDF, whatever the .md says
```

### 2.3 Every refusal arm, exit codes read correctly

```
pdf-ext                      commit exit=1  head_moved=NO
nul-txt                      commit exit=1  head_moved=NO
raml                         commit exit=1  head_moved=NO
unknown-ext                  commit exit=1  head_moved=NO
pdf-as-md                    commit exit=1  head_moved=NO

HEAD before: ab4f3639986030fd873a576c83388fd573e6c4f3
HEAD after : ab4f3639986030fd873a576c83388fd573e6c4f3
```

Reasons emitted, one per class:

```
  leaked.pdf:  denylisted extension .pdf (vendor document - THIS IS THE CLASS THAT LEAKED)
  api.raml:    denylisted extension .raml (vendor API description - THIS IS THE CLASS THAT LEAKED)
  notes.txt:   contains a NUL byte at offset 19; this is a binary file
  thing.bin:   .bin is not on the allowlist (allowlist-first: unknown means refused)
```

### 2.4 The override, and the "same commit" property

`DESIGN.md:1582-1583` requires that an override be reviewable in the diff. That is not a property of
the allowlist file, it is a property of **reading the allowlist through the index**:

```
### allowlist entry written to the worktree but NOT STAGED
  thing.bin: .bin is not on the allowlist (allowlist-first: unknown means refused)
gate exit=1

### the same entry STAGED IN THE SAME COMMIT
  exception: thing.bin is listed in .file-type-allowlist
committed-file-type gate: 2 file(s) checked, none refused.
gate exit=0

COMMIT LANDED. The exception is in the diff:
15e0330 override with the exception in the same diff
 .file-type-allowlist | 1 +
 thing.bin            | 1 +
```

**No `.file-type-allowlist` is committed.** The gate treats an absent allowlist as an empty set, not
an error, and nothing in the tree needs an exception (92 tracked files, all clean). An empty
allowlist file would only advertise the escape hatch.

### 2.5 Fail-closed

```
### git fails
committed-file-type gate FAILED TO RUN: git diff --cached --name-only -z --diff-filter=ACMR
  exited 128: fatal: simulated git failure
Failing closed: the commit is blocked.
gate exit=2

### git absent from PATH
committed-file-type gate FAILED TO RUN: could not run git diff ...: [Errno 2] No such file or
  directory: 'git'
Failing closed: the commit is blocked.
gate exit=2

### an internal crash in the rule engine
committed-file-type gate CRASHED: RuntimeError('simulated bug in the gate')
Failing closed: the commit is blocked.
gate exit=2

### unknown argument
check-committed-file-types: unknown argument(s): ['--pretty-please']
gate exit=2
```

**My first fail-closed test was a false negative and I nearly filed it as a defect.** Shadowing
`git` with a **non-executable** stub does not shadow anything: `execvp` skips a non-executable file
and keeps searching `PATH`, so the real git ran, there was genuinely nothing staged, and the gate
printed `0 file(s) checked, none refused` and exited **0**. I read that as the gate failing open. It
was my stub failing to be a stub. The corrected test uses an executable stub that exits 128, with a
positive control confirming which `git` resolves. **The lesson is the one about instruments, not
about the gate** - and the wrong version had a plausible story attached, which is why it would have
shipped.

### 2.6 The full gate, as CI runs it

```
########## yaml parses                            both parse OK
########## full default suite                     53 passed, 2 deselected in 0.85s
########## ruff check                             EXIT=0
########## ruff format --check                    13 files already formatted
########## mypy                                   Success: no issues found in 8 source files
########## committed file types, whole tree       92 file(s) checked, none refused.   EXIT=0
########## U0's controls                          11/11 controls fired.               EXIT=0
```

**53 passed, 2 deselected, 0 skipped.**

---

## 3. `.gitignore` - I took it, and here is what it costs

**It is mine**, on the grounds that the brief's finding is about the same incident mechanism this
unit exists for and no other unit owns the file.

The measurement in the brief reproduces exactly:

```
=== BEFORE ===                        === AFTER ===
STAGEABLE  test.pdf                   BLOCKED    test.pdf
STAGEABLE  docs/test.pdf              BLOCKED    docs/test.pdf
STAGEABLE  src/test.pdf               BLOCKED    src/test.pdf
STAGEABLE  vendor.raml                BLOCKED    vendor.raml
STAGEABLE  notes.docx                 BLOCKED    notes.docx
STAGEABLE  archive.zip                BLOCKED    archive.zip
BLOCKED    docs/research/test.pdf     BLOCKED    docs/research/test.pdf
                                      STAGEABLE  src/ok.py
                                      STAGEABLE  docs/DESIGN.md
```

The last two rows are the control: the widening blocks the vendor-document classes and **not**
ordinary source and prose. `.gitignore:25-26` were `docs/research/*.pdf` and `docs/research/*.raml`;
they are now repo-wide, and the block covers `.ppt/.pptx/.xls/.xlsx` too, which the old one missed
in both scopes.

**The cost, stated rather than assumed, because the brief asked and assuming is how the original
narrow scope happened.** A legitimate PDF someone later wants is now blocked as well.

- **There is no such file today.** `git ls-files | grep -Ei '\.(pdf|raml|docx?|zip|pptx?|xlsx?)$'`
  returns nothing. Checked, not presumed.
- **No tracked file changes status.** `.gitignore` does not apply to files git already tracks, so
  this widening cannot un-track anything. The only modified path is `.gitignore` itself.
- **The route back is two steps, deliberately.** `git add -f` gets past `.gitignore`; the gate
  denylists these extensions independently and still refuses, so a genuine exception also needs a
  `.file-type-allowlist` entry staged in the same commit. That is the reviewable path, and it is the
  same one the design specifies.

**`.gitignore` is not the control and the rewritten comment now says so in the file.** It is
bypassed by `git add -f` and silent about already-tracked files. It removes the *accident* - the
broad `git add` sweep, which is this project's actual mechanism, twice - and the gate handles the
rest. **I rewrote the block's comment in place rather than appending**, so the file does not carry
two accounts of its own scope.

---

## 4. Defects found

### D1 - HIGH, and it is in the code this unit shipped. Fixed.

**The two gates refused each other out of the box.** detect-secrets requires `.secrets.baseline`
committed. The file-type gate's allowlist had no `.baseline` extension and no such basename, so:

```
  .secrets.baseline: .baseline is not on the allowlist (allowlist-first: unknown means refused)
EXIT=1
```

Measured before fixing, not reasoned about. Fixed by adding `.secrets.baseline` to
`ALLOWED_BASENAMES`, with the reason recorded at the entry. **Mutation control #14 is that
regression**, so the two gates cannot silently stop composing again.

This is the class of defect only building finds: both gates are individually correct and the design
specifies both, and nothing short of installing them together surfaces it.

### D2 - MEDIUM. The secret gate is red on its first run against a clean tree. Mitigated.

Exactly D3's shape from `U0-REPORT`, one gate over. With no baseline, detect-secrets fails
immediately on the current tree:

```
Secret Type: Secret Keyword    Location: docs/research/FASTMCP.md:354
Secret Type: Secret Keyword    Location: docs/research/FASTMCP.md:584
```

Both are vendor-documentation placeholders, read and audited:

```
FASTMCP.md:354    client_secret="your-client-secret",
FASTMCP.md:584    "API_KEY": "secret-key",
```

**A gate that is red on a clean tree trains everyone to ignore it**, which is the failure the plan
names for `pip-audit` at `IMPLEMENTATION-PLAN.md:206-211`.

I resolved it with an **audited baseline** rather than the two alternatives, and I changed my mind
after measuring: my first config committed a comment saying a baseline is "the place where a future
finding gets silenced without review", which is true of an *unaudited* one and false of this one.
Excluding `docs/research/` is a blanket hole over exactly the directory vendor material lands in.
Inline `pragma: allowlist secret` edits research prose that is not this unit's file. The baseline
records path, line and a hash per entry, so it appears in the diff and a changed line re-fires -
the same reviewable shape `DESIGN.md:1582-1583` demands of the file-type gate's override. Both
entries carry `is_secret=false`.

### D3 - MEDIUM. I broke U0's control harness, and it would have gone red in CI.

`scripts/check-u0-test-controls.sh:42` copies a fixed subset of the tree into each mutation
sandbox: `(pyproject.toml uv.lock .env.example .gitignore src tests docs)`. **`scripts/` is not in
it.** `tests/test_file_type_gate.py` imports the gate from `scripts/`, so U0's copied tree failed at
*collection* and the harness aborted before running a single control:

```
======================== 2 deselected, 1 error in 0.07s ========================
ABORT: the unmutated copy is already red. Fix that before running controls.
```

Note what the abort did: it **refused to score 11 controls it could not honestly run**. U0's harness
caught my breakage of U0's harness, which is the design working.

Fixed by adding `scripts` to that array - a one-entry data change, not a restructure of a file the
brief put out of scope. Re-verified: `11/11 controls fired. EXIT=0`.

### D4 - MEDIUM. Two of my own tests asserted nothing, and each harness found one.

Reported as defects because they shipped in my first draft and a reviewer would have inherited them.

- **`test_a_pdf_by_extension_is_refused` did not test the denylist.** Rule 1 is redundant with rule
  2 (`.pdf` is not on the allowlist either), so deleting `.pdf` from the denylist still produced a
  refusal - with a message that also contains `.pdf`, satisfying my assertion. **Two mutation
  controls survived**, which is how it was found. Fixed to assert the denylist's own message, which
  is the only observable difference and the reason rule 1 exists.
- **`test_e2e_a_real_pdf_staged_as_markdown_is_refused` asserted `"PDF" in result.stdout`**, and the
  refusal *banner* contains the word PDF. **In amputation tree D, with every rule table emptied, it
  still passed** - reporting that magic-number sniffing worked when it had been deleted. Fixed to
  assert the per-file reason line.

### D5 - LOW, but it is a green that tests nothing. Documented in CI rather than hidden.

**`pre-commit run --all-files` does not exercise the file-type gate.** `--all-files` passes files as
hook *arguments*; the gate takes none by design, because it reads the index. In CI nothing is
staged:

```
$ pre-commit run committed-file-types --all-files --verbose
committed-file-type gate (allowlist-first, ...) .......Passed
committed-file-type gate: 0 file(s) checked, none refused.
```

Passed, having checked zero files. The separate `--all` CI step is what actually covers it. I named
the step **"Secret scan hook runs clean"** rather than "Pre-commit hooks run clean" and wrote the
measurement into its comment, so nobody deletes the `--all` step believing this one duplicates it.

### D6 - LOW. A note on the design, not a change to it.

The brief is right that C8-I1's `.gitignore` clause was unqualified where the file was
path-scoped. **That is now true rather than aspirational** (§3), so the row's *evidence* has been
made correct by the tree rather than by an edit. `DESIGN.md` is untouched; `docs/adr/0014` and the
team lead own the record.

---

## 5. CI

Three steps added to the existing `test` job, in U0's own style, immediately after its controls
step. **No job, trigger, permission or existing step was restructured.**

- **Committed file types, whole tree** - `--all`, the backstop for a commit made with `--no-verify`
  or by someone who never ran `pre-commit install`.
- **U15 gate controls, all fired** - parses `N/M controls fired.` and asserts `N == M` and `M > 0`,
  never a literal count, exactly as U0's step does, so the harness growing from 15 controls is a
  green.
- **Secret scan hook runs clean** - `uv tool run pre-commit@4.6.2 run --all-files`, pinned. Covers
  detect-secrets and keeps `.secrets.baseline` honest. See D5 for what it does *not* cover.

**Never executed on GitHub.** Every step was run locally and its output is above, but job wiring and
`uv tool run` under Actions are unexercised until the first push.

---

## 6. Both harnesses

### 6.1 Mutation - 15/15

```
--- drop .pdf from the extension denylist                          -> CONTROL FIRED
--- drop .raml from the extension denylist                         -> CONTROL FIRED
--- allowlist-first inverted: unknown becomes PERMITTED            -> CONTROL FIRED
--- delete the magic-number rule entirely                          -> CONTROL FIRED
--- remove only the %PDF- signature                                -> CONTROL FIRED
--- delete the NUL backstop                                        -> CONTROL FIRED
--- fail OPEN on a gate error instead of closed                    -> CONTROL FIRED
--- accept unknown argv instead of refusing                        -> CONTROL FIRED
--- read the allowlist from the WORKTREE so an unstaged exception applies -> CONTROL FIRED
--- read the WORKTREE instead of the index                         -> CONTROL FIRED
--- report success even when files were refused                    -> CONTROL FIRED
--- classify permits EVERYTHING                                    -> CONTROL FIRED
--- classify refuses EVERYTHING                                    -> CONTROL FIRED
--- drop .secrets.baseline, so the two shipped gates refuse each other again -> CONTROL FIRED
--- empty the rule tables                                          -> CONTROL FIRED

15/15 controls fired.
post-run re-check of the real gate: exit=0 (must be 0)
```

Controls 12 and 13 are the pair that answers the brief's question directly. **A gate that permits
everything and a gate that refuses everything each turn this suite red**, and they turn *different*
tests red.

The harness aborts if the unmutated copy is not green, and **rejects a mutation that does not change
the file** - which is not decoration: two of my controls were initially written against the wrong
indentation, and the harness reported `BROKEN CONTROL (mutation did not apply)` rather than counting
them as fired. A no-op control that scores as a pass is a harness lying about itself.

### 6.2 Amputation - 5 trees

Different question: not "break a rule, does the named test notice" but "remove the **subject**, does
anything still report success".

| Tree | Result | Verdict |
|---|---|---|
| **A.** the gate script does not exist | `1 error` | **No survivors.** Collection fails |
| **B.** the gate exists, **ZERO BYTES** | `36 failed` | **No survivors** - after a fix; see below |
| **C.** imports, but `classify()` removed | `30 failed, 6 passed` | 6 survivors, all legitimate |
| **D.** runs, but every rule table EMPTY | `18 failed, 18 passed` | 18 survivors, all paired |
| **E.** `git` not on PATH | `28 passed, 8 errors` | 28 survivors, all in-process |

**Tree B found the genuinely vacuous assertion, exactly as it did for U0.** A zero-byte Python file
runs and exits 0, so `test_e2e_an_ordinary_staged_file_passes` - the **positive control for every
e2e refusal in the suite** - passed against a gate that had been deleted down to nothing, while
every refusal test around it correctly failed. That reads as "the gate is too permissive", which is
the wrong diagnosis and the expensive kind of wrong.

Fixed with the pairing U0 used for `.env.example`: the gate must also **say what it looked at**, and
the test now parses `N file(s) checked` and requires `N >= 1`. An instrument that cannot be
satisfied by silence. `test_the_gate_script_exists_...` also gained a non-zero-size assertion.
**Tree B now has zero survivors.**

### 6.3 Which assertions survive amputation, and why

**Tree C** (`classify()` gone) - 6 survivors, none vacuous:

- `test_the_gate_script_exists_..._and_is_not_empty`, `test_the_rule_tables_are_populated`,
  `test_the_allowlist_parser_...`, `test_a_missing_allowlist_...` - **their subjects are still
  present and correct.** The file, the tables and `load_allowlist` were not what was amputated.
- `test_e2e_the_gate_fails_closed_when_it_cannot_run` and `test_e2e_an_unknown_argument_fails_closed`
  - these pass **because the amputation is exactly what they assert**. A gate missing `classify`
  raises `NameError`, the top-level handler catches it and exits 2. A gate with a bug in it failing
  closed is the specified behaviour, so passing here is correct, not vacuous.

**Tree D** (rule tables emptied) - 18 survivors, every one paired:

- All the **refusal** assertions survive, because with `ALLOWED_EXTENSIONS` empty, rule 2 refuses
  everything. They pass **for the wrong reason**.
- They are not left alone. **Their partners fail**: 4 of the 10
  `test_an_ordinary_repository_file_is_permitted` cases go red, and so do
  `test_the_rule_tables_are_populated`, `test_a_real_pdf_..._by_its_bytes`,
  `test_the_magic_rule_and_the_extension_rule_are_independently_load_bearing`, both denylist-message
  tests, and both e2e PDF arms. **18 failures.** The suite is red, loudly, and the failures name the
  right thing.
- The 4 permitted-cases that *survive* tree D are `.gitignore`, `LICENSE`, `NOTICE` and
  `.secrets.baseline` - matched by `ALLOWED_BASENAMES`, which tree D does not empty. Correct.

**Tree E** (no `git`) - 28 survivors: every in-process `classify` test, whose subject is present.
The 8 that error are exactly the git-dependent e2e arms. Nothing passed whose subject was gone.

**Summary: no assertion in this suite passes against an absent subject.** The one that did is named
in §6.2, is fixed, and the harness that found it is committed so the fix cannot silently regress.

---

## 7. What I could NOT verify

- **Neither gate has run on GitHub.** All local. `uv tool run pre-commit@4.6.2` in Actions, and the
  three new steps as job wiring, are unexercised until the first push.
- **detect-secrets' detector coverage is not characterised.** I proved it catches an AWS key and two
  keyword-shaped credentials (§2.1). I have **not** measured what it misses, and a Jobvite API
  secret is not a shape I tested against a real example. TruffleHog in CI is a second engine over
  full history, which is the mitigation for that gap, and it too has never run.
- **The magic table's short signatures can false-positive and I did not measure the rate.** `BM`
  (BMP) and `MZ` (DOS/PE) are two ASCII characters: a Markdown file beginning "BM" or "MZ" is
  refused. I judged this acceptable - the refusal is loud, the fix is one allowlist line - but
  **acceptable-because-I-reasoned-about-it, not acceptable-because-I-measured-it**. No file in the
  tree trips it (92 checked, none refused).
- **Symlinks are unexamined.** `git ls-files` includes them; in `--all` mode the gate follows the
  link and reads the target. A symlink named `x.md` pointing at a binary outside the repo is a case
  I have not reasoned through and did not test.
- **`0 file(s) checked` exits 0.** Correct for `git commit` (an empty index fails on its own) and it
  is what makes D5 possible. I left the behaviour and documented it rather than adding a rule whose
  consequences I have not measured.

---

## 8. The stated ceiling, carried not dropped

`DESIGN.md:1584-1586` says this gate stops a **file** of the wrong type and does nothing about
confidential prose pasted into Markdown - *"which is the incident we actually had"*.

`IMPLEMENTATION-PLAN.md:950-953` requires that no test here be written as though the gate closed
that. **It is pinned as a passing assertion**, not merely respected in prose:

```python
def test_the_gate_does_NOT_stop_confidential_prose_in_markdown() -> None:
    """This asserts a LIMIT, not a capability. It must keep passing."""
    prose = b"# Notes\n\nCONFIDENTIAL - Jobvite internal pricing, do not distribute.\n"
    assert gate.classify("docs/research/notes.md", prose) is None
```

If someone later teaches the gate to scan prose, that test goes red and the design change gets an
ADR instead of a quiet edit. The limit is also stated at the top of
`.pre-commit-config.yaml` and in the gate's own docstring, because the trees the design worries
about are read one file at a time.

**Of the two files that actually leaked, this gate refuses both** - the `.raml` by rules 1 and 2,
the `.pdf` by rules 1 and 3, and the `.pdf` still by rule 3 when renamed. **The incident as a whole
it does not close**, and C8-I1 should not be read as saying otherwise.
