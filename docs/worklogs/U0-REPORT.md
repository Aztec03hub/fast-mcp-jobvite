# U0 - Repository skeleton, pinned manifest, test selection, CI

**Executed** 2026-08-28, 03:19 PM CDT, against `docs/DESIGN.md` **revision 6, FROZEN**, and
`docs/plans/IMPLEMENTATION-PLAN.md` draft 4 (uncommitted in the tree at the time of writing - the
plan file shows as modified in `git status` and that modification is **not mine**).

Toolchain: uv **0.11.3**, Python **3.12.3**, on Linux. Repo HEAD when this was written: `b08c6e1`.

**Nothing is committed and nothing is pushed.** The work is in the tree.

**Two untracked paths in this tree are NOT mine** and I have not touched them:
`docs/plans/IMPLEMENTATION-PLAN.md` (modified) and `docs/reviews/PLAN-REVIEW-R3.md`, which appeared
while I was working. R3 states at `:26` *"U0 is unaffected. Every finding lands on U5-and-later
scheduling or on citation text"* - so it asks nothing of this unit. Mine are exactly:
`.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, `scripts/check-u0-test-controls.sh`,
`src/fast_mcp_jobvite/__init__.py`, `tests/` (six files), and this report.

---

## 1. What landed

| Path | Status | Note |
|---|---|---|
| `pyproject.toml` | new | the verbatim three-pin block, `prerelease = "explicit"`, pytest selection, ADR-0010 coverage floors, an empty advisory-ignore table for U11 |
| `uv.lock` | new | committed; CI installs it with `uv sync --frozen` |
| `src/fast_mcp_jobvite/__init__.py` | new | package only. No module from `DESIGN.md:280-293` is implemented |
| `tests/__init__.py`, `tests/conftest.py` | new | shared paths; settles how tests reach the fixtures |
| `tests/test_manifest.py` | new | §8 case **#11** |
| `tests/test_markers.py` | new | §8 case **#12** |
| `tests/test_repo_hygiene.py` | new | §8 case **#3** |
| `tests/test_fixture_path.py` | new | positive control on the fixture path itself |
| `tests/credentialed/README.md` | new | the contract for arms later units add here |
| `scripts/check-u0-test-controls.sh` | new | mutation harness proving U0's own tests can fail |
| `.github/workflows/ci.yml` | new | the point of the unit |

**Out of scope and not written**, as briefed: `config.py`, `server.py`, `__main__.py`,
`server.json`, any tool, client, or model. `.env.example` and `.gitignore` were **read and never
written** - they are U1's, and `PLAN-REVIEW-R2.md:343-351` (N1) already notes U0 reads them.

### Decisions I made that the design and plan left open

- **The credential-dependent marker is named `credentialed`.** Neither document names it;
  `DESIGN.md:1199` only requires that it be declared. Declared in `markers`, deselected in
  `addopts`.
- **A second marker, `network`, exists** and is a decision worth challenging. §8 #11's negative arm
  (removing the `fastmcp-slim` pin must fail to resolve) performs a **real dependency resolve**,
  and `DESIGN.md:1185` says the default suite runs with **no network**. Excluding it by *selection*
  keeps both properties true and keeps skips at zero. CI runs it as its own step. The alternative -
  putting a network call in the default suite - would quietly contradict `:1185`.
- **`extend-exclude = ["docs"]` for ruff and mypy.** Running the new lint config over
  `docs/reviews/check-coupling*.py` produced 16 findings in the *gate harnesses*. Reformatting a
  gate under a config written after it is not a thing U0 should do silently; CI runs those scripts
  by exit code.
- **`[project.scripts]` and `readme = "README.md"` were deliberately omitted** from the manifest. An
  entry point at `fast_mcp_jobvite.__main__:main` names a function U1 writes, and a `readme` key
  pointing at a file the design deliberately has not written yet breaks the build. Both belong to
  the units that create their targets.

---

## 2. Every check, with its real output

### 2.1 The resolve, and the 72 figure

The design's count reproduces **exactly**, in a scratch directory outside the repo, against the
runtime-only manifest:

```
$ cd /tmp/u0probe && uv lock
Using CPython 3.12.3 interpreter at: /usr/bin/python3
Resolved 72 packages in 35ms
```

**The repo's own lock resolves 85, and that is not drift.** The delta is the `dev` dependency group
(pytest, pytest-asyncio, pytest-cov, ruff, mypy and their transitives). Cross-checked from the other
direction:

```
$ uv export --frozen --no-dev --no-emit-project | grep -c '=='
71          # + the project itself = 72
```

Recorded because a future reader comparing `85` to the design's `72` would otherwise reasonably
conclude the resolve had moved.

```
$ uv lock            # in-repo, with the dev group
Resolved 85 packages in 177ms
```

### 2.2 The `fastmcp-slim` causal claim, re-confirmed

Removing **only** that line from the probe manifest:

```
      hint: `fastmcp-slim` was requested with a pre-release marker (e.g.,
      fastmcp-slim==4.0.0b4), but pre-releases weren't enabled (try:
      `--prerelease=allow`)
EXIT=1
```

This is now a permanent test (`test_removing_fastmcp_slim_breaks_the_resolve`) with a positive
control beside it (`test_the_unmutated_manifest_still_resolves`), so a `uv` that failed on
*everything* cannot make the negative arm pass.

### 2.3 The full CI sequence, run locally

```
########## uv sync --frozen
Checked 81 packages in 0.37ms                                   EXIT=0
########## uv lock --check
Resolved 85 packages in 0.67ms                                  EXIT=0
########## ruff check
All checks passed!                                              EXIT=0
########## ruff format --check
11 files already formatted                                      EXIT=0
########## mypy
Success: no issues found in 7 source files                      EXIT=0
########## pytest (default)
collected 19 items / 2 deselected / 17 selected
======= 17 passed, 2 deselected in 0.57s =======                EXIT=0
########## pytest -m network
======= 2 passed, 17 deselected in 0.16s =======                EXIT=0
########## pytest -m credentialed --collect-only -q
no tests collected (19 deselected) in 0.01s                     EXIT=5
```

**17 passed, 2 deselected, 0 skipped.**

**The "no network" property of `DESIGN.md:1185` is measured, not assumed.** The whole default suite
was re-run with the network forced off, and the exit codes were read directly rather than through a
pipe (a `cmd | tail` reports `tail`'s status, which is how a green gets misread):

```
$ uv lock --check --offline          ; echo $?
Resolved 85 packages in 0.74ms
0
$ uv run --frozen --offline pytest -q ; echo $?
======= 17 passed, 2 deselected in 0.81s =======
0
```

### 2.4 The three design gates

```
########## python3 docs/reviews/check-coupling.py docs/DESIGN.md
docs/DESIGN.md: 60 STRIDE rows, 17 Critical/High (16 mitigated by the roster's
reckoning, 1 not); all 60 rows checked for disposition, 23 naming a §8 case.
PASS: ids unique, STRIDE coverage complete, ...                 EXIT=0

########## python3 docs/reviews/check-coupling-controls.py
34/34 controls fired.
post-run re-check of the real DESIGN.md: exit=0 (still green)   EXIT=0

########## python3 docs/reviews/check-coupling-sweep.py
  6 escapes are the designed Medium/Low exemption
  0 escapes are holes. Every one of the 23 rows that names a §8 case loses its
  green when that reference is removed.                         EXIT=0
```

**CI asserts the exit code and the "all fired" property, never a literal count** - H5. The step
parses the `N/M controls fired.` line and requires `N == M` and `M > 0`, so the harness growing from
21 to 34 to 40 is a green, not a red. Same for the sweep: `0 escapes are holes`, never a row count.

### 2.5 The CI parsers were themselves falsified

A parser that has only run against passing input is the unfalsifiable green this project has spent
the day removing, so each was run against its failure modes verbatim:

| Parser | Input | Result |
|---|---|---|
| controls | real harness output | `parsed: 34 fired of 34 held` -> **ACCEPT** |
| controls | `30/34 controls fired.` | REJECT: 30 of 34 fired |
| controls | `0/0 controls fired.` | REJECT: zero controls held |
| controls | no `N/M` line at all | REJECT: no N/M line |
| controls | `34/34` but post-run re-check `exit=1` | REJECT: DESIGN.md not left green |
| sweep | real sweep output | **ACCEPT** |
| sweep | an `ABORT` line | REJECT (no holes line) |
| zero-skips | real pytest output | **ACCEPT** |
| zero-skips | `15 passed, 2 skipped` | REJECT: skips present |
| zero-skips | `0 passed, 19 deselected` | REJECT: nothing passed |

The `0 passed` arm matters: without it the zero-skips step goes green on a run whose selection
matched nothing at all.

### 2.6 U0's own tests, mutation-tested

Every U0 test asserts a property of a **file**, which is the easiest class of test to write green
and hollow. `scripts/check-u0-test-controls.sh` breaks one thing at a time in a copy of the tree and
requires the **named** test to go red:

```
BASELINE: the unmutated copy
======= 17 passed, 2 deselected in 0.52s =======
--- empty a deliberate non-secret default (draft 2's 'fix')  -> CONTROL FIRED
--- a secret-class variable carries a value                  -> CONTROL FIRED
--- drop *.pem from .gitignore                               -> CONTROL FIRED
--- un-ignore a credential with an extra negation            -> CONTROL FIRED
--- remove --strict-markers from addopts                     -> CONTROL FIRED
--- remove the -m selection from addopts                     -> CONTROL FIRED
--- loosen the mcp pin to >=                                 -> CONTROL FIRED
--- delete the fastmcp-slim justification comment            -> CONTROL FIRED
--- point FIXTURES_DIR at a path that does not exist         -> CONTROL FIRED
--- drop a variable from .env.example                        -> CONTROL FIRED
--- make uv.lock disagree with the manifest                  -> CONTROL FIRED
11/11 controls fired.                                           EXIT=0
```

The harness aborts if the unmutated copy is already red, and rejects a mutation that turns out to be
a no-op.

### 2.7 Licence gate and SBOM

```
########## pip-licenses --fail-on="<the standard's flag-list>"
EXIT=0  (83 rows emitted)
########## NEGATIVE ARM: --fail-on="MIT"
fail-on license MIT was found for package truststore:0.10.4
EXIT=1
########## cyclonedx-py environment .venv --output-format JSON
specVersion 1.6 | components 81                                 EXIT=0
```

The negative arm is there because a `--fail-on` that never fires would make the green above
meaningless.

---

## 3. Defects found

### D1 - CRITICAL to correct, and it is inside the FROZEN design. Needs an ADR.

**`DESIGN.md:1760`, threat row C8-I1, says `.env.example` is committed with "empty values".** That
is false against the committed tree. **Seven of the fifteen variables carry a value**
(`JOBVITE_ENABLE_WRITES=false`, `JOBVITE_MCP_TRANSPORT=stdio`, `JOBVITE_MCP_HOST=127.0.0.1`,
`JOBVITE_MCP_PORT=8000`, `JOBVITE_TLS_TERMINATED_BY_PROXY=false`, `JOBVITE_MAX_RESULTS=50`,
`JOBVITE_OUTBOUND_RATE_LIMIT=6` - `.env.example:41,48,53,54,67,75,82`).

The design's **own §8 wording is correct**: `:1222` says *"carries no real value"* - no real
*credential*. C8-I1 tightened that into *"empty values"*, which is a different and false claim, and
C8-I1 is a **Critical** row.

**This is the exact defect `PLAN-REVIEW-R2.md` H1/M3 corrected in the plan**, and the correction
landed on the plan only. The design row and `.env.example` are its untouched siblings.

*Suggested fix, a hypothesis to verify not an instruction:* amend C8-I1's mitigation text to
*"`.env.example` is committed with every secret-class variable empty"*, matching `:1222`. It is a
wording change inside a frozen document, so it needs a numbered ADR or a freeze amendment - I have
not touched it.

**My test is already written against the correct property**, not the design's wrong one: it asserts
the six secret-class names are empty and separately pins the non-secret defaults *positively*, so
an agent "fixing" the tree to satisfy C8-I1's literal wording turns the suite **red**. Control
`empty a deliberate non-secret default (draft 2's 'fix')` in §2.6 is that arm.

### D2 - HIGH. `.env.example` contradicts itself, in its own header.

**`.env.example:4`** reads *"Every value here is EMPTY on purpose"*, thirty-seven lines above
`JOBVITE_ENABLE_WRITES=false` and seventy-one above `JOBVITE_MAX_RESULTS=50`. Same defect as D1,
different artifact. `.env.example` is **U1's file** so I did not edit it.

*Suggested fix (hypothesis):* rewrite `:4-6` in place - *"Every credential here is EMPTY on purpose;
the non-secret defaults below carry real values and must keep them"* - rather than appending a
correction, which would leave two contradictory claims in one header.

### D3 - MEDIUM. The standard's licence allow-list cannot be applied as written.

`quality-gates.md:288-292` allow-lists five SPDX ids. `pip-licenses` reports **fifteen distinct
spellings** over this tree for six actual licences (`MIT` and `MIT License` both appear, as do
`BSD-3-Clause` and `BSD License`). **`--allow-only` on the standard's five ids is red on its first
run against a tree containing nothing objectionable**, which is the "trains everyone to ignore the
gate" failure the plan warns about for `pip-audit`.

Worse, four packages carry licences on **neither** list, which `quality-gates.md:307` classes as
*"Custom / unknown - always flag for review"*:

| Package | Licence | Shipped? |
|---|---|---|
| `cffi` 2.1.1 | MIT-0 | **RUNTIME** |
| `email-validator` 2.3.0 | Unlicense | **RUNTIME** |
| `typing_extensions` 4.16.0 | PSF-2.0 | **RUNTIME** |
| `pathspec` 1.1.1 | MPL-2.0 | dev/build only, **not shipped** |

All four are permissive, or weak copyleft that does not ship. **No strong copyleft is present in
either tree** - I checked. But three permissive-but-unlisted licences do ship, and extending an
allow-list is an ADR, not a CI edit.

*Suggested fix (hypothesis):* U0 lands a **deny-list on the standard's flag-list** (GPL / AGPL /
LGPL / SSPL / BUSL), which is runnable today, green today, and demonstrably fires (§2.7). File an
ADR extending the allow-list with `MIT-0`, `Unlicense`, `PSF-2.0` and `MPL-2.0`, and only then
switch the gate to `--allow-only`. I have implemented the deny-list and documented the open half in
a comment on the step itself.

### D4 - LOW. The plan's "nine of the fifteen variables" is still wrong in draft 4.

`IMPLEMENTATION-PLAN.md` still carries *"Nine of the fifteen variables carry a value"* inside the
paragraph correcting draft 2's count. **Seven do**, as `PLAN-REVIEW-R2.md:255-260` states and as I
re-derived from the file. The brief already flagged this and I built to the correct number; noting
it because the plan text itself has not been fixed and this is now the third copy-forward of a wrong
count inside a correction of a wrong count.

---

## 4. What is deferred, and to whom - none of it silently

| Deferred | Owner | Why it is not landed now |
|---|---|---|
| `pip-audit` behind `scripts/check_advisories.py` | **U11** | the script does not exist; calling it makes CI red from its first run (`IMPLEMENTATION-PLAN.md:206-211`). Landed as a commented step naming U11, with the empty `[tool.fast-mcp-jobvite.advisory-ignores]` table already in `pyproject.toml` so U11 only edits rows inside it |
| coverage floors enforced in CI | **U1** | `src/fast_mcp_jobvite` holds only `__init__.py`. A coverage run reports either "No data collected" (red) or a **vacuous 100%** over an empty package. The floors are configured in `pyproject.toml` today; only the CI step is off |
| `fastmcp inspect` capability-drift diff | **U1** | `fastmcp inspect --help` confirms `SERVER-SPEC` is required and `server.py` is U1's file. **Standing it up does not execute it** - `DESIGN.md:1443-1446` carries `UNVERIFIED:` and **U0 does not remove that marker** |
| pre-commit hooks (secret scan, committed-file-type gate) | **not built** | see §5 |

---

## 5. What I could NOT verify, and one thing I did not build

**Never executed, and they cannot be executed on a developer machine.** These are GitHub-hosted
actions. They are written to the standards' pinned versions and **their first real run in CI is
their first evidence**:

- `github/codeql-action/init@v3` + `analyze@v3`
- `trufflesecurity/trufflehog@main` (with `fetch-depth: 0`, since a secret removed in a later commit
  is still compromised and a shallow clone cannot see it)
- `anchore/sbom-action@v0`, both formats, pointed at `.venv` so the SBOM comes from the **frozen**
  resolve

The `.venv` path for the SBOM action is my choice and is **unverified**: I have not confirmed syft
enumerates a uv-created virtualenv the way it enumerates a `requirements.txt`. `cyclonedx-py` **does**
work from the frozen environment (§2.7, 81 components) and is the fallback if the action comes back
thin on its first run.

**Not built: the two commit-time gates of `DESIGN.md:1573-1586`** - pre-commit secret scanning and
the committed-file-type gate. The plan lists them under U0 (`IMPLEMENTATION-PLAN.md:201-202`) and I
did not write them. They are a `.pre-commit-config.yaml` plus a custom allowlist-first,
magic-number-sniffing, fail-closed file-type hook, which is a real piece of software with its own
test surface, not a config line - and it is the control the design says would **not** have caught
the incident it was named for. I judged it a unit of its own rather than a corner of this one.
**Flagging it rather than pretending U0 is complete without it.** If it should be in U0, say so and
I will build it next.

**Other limits, stated:**

- **The credentialed-collect step accepts exit 5.** `tests/credentialed/` is empty, so the step
  cannot presently distinguish *"the suite is empty"* from *"the suite is healthy"*. Recorded in
  `tests/credentialed/README.md` with the instruction that the first unit adding an arm must tighten
  it to require exit 0 and a non-zero count.
- **The `network` arm was verified to genuinely need the network, and the check paid for itself.**
  Re-run with the network disabled, **both** arms fail rather than one silently passing:

  ```
  FAILED tests/test_manifest.py::test_removing_fastmcp_slim_breaks_the_resolve
  FAILED tests/test_manifest.py::test_the_unmutated_manifest_still_resolves
  ```

  This is the behaviour I wanted and it is worth recording. Offline, `uv lock` fails for *every*
  manifest, so a negative arm asserting only `returncode != 0` would have gone **green for the
  wrong reason** - reporting "the `fastmcp-slim` pin is load-bearing" on the strength of a network
  outage. The second assertion (`"fastmcp-slim" in combined`) is what refuses that, and the
  positive control fails loudly beside it. Marking the pair `network` is therefore correct, not
  precautionary.
- **The workflow as a whole has never run on GitHub.** Every step I could run locally, I ran, and the
  output is above. Job wiring, action versions, caching and permissions are unexercised until the
  first push.

---

## 6. How tests reach the fixtures - settled here, per PLAN-REVIEW-R2 L1

Tests read the recorded fixtures from **`docs/research/fixtures/` by path**, via
`tests/conftest.py`'s `FIXTURES_DIR`. They are **not** copied under `tests/`, because U4 asserts five
of them byte-exact and a second copy of a byte-exact ground truth can drift from the first silently.

`tests/test_fixture_path.py` is the **positive control on that path**, and it is not decoration: a
glob at a directory that does not exist returns a clean empty list and passes every assertion
written over it. It asserts the directory resolves, that all fifteen named files are present, and
that none is zero-byte. Control `point FIXTURES_DIR at a path that does not exist` in §2.6 proves
it fires.

---

## 7. Which assertions would still pass against an empty tree

Asked directly, so it is answered by measurement rather than by reassurance. This is a **different**
question from §2.6: that harness breaks one thing and asks whether the named test notices. This one
asks the **absence** question - if the subject simply is not there, does anything report success?

Four trees, each run for real:

| Tree | Result | Passed for a reason other than its subject being present and correct? |
|---|---|---|
| **A.** `tests/` + `pyproject.toml` only - no `.env.example`, `.gitignore`, `docs/`, `src/`, `uv.lock` | `10 failed, 7 passed` | **No.** The 7 are the four manifest-content tests and the three marker tests, whose subject - `pyproject.toml` - **is** present and correct. Every test whose subject was removed failed |
| **B.** no `docs/` at all | `3 failed, 14 passed` | No. Exactly the three fixture-path tests fail |
| **C.** no `.env.example`, no `.gitignore` | `6 failed, 11 passed` | No. Exactly the six tests reading those two files fail |
| **D.** `docs/research/fixtures/` **exists but is empty** - the clean-empty trap | `2 failed, 15 passed` | No. `test_fixtures_directory_resolves` passes *correctly* (the directory does exist); the other two catch the emptiness |

### The one genuinely vacuous assertion, and the control that already catches it

Pushed to its sharpest form - `.env.example` **present and zero bytes**, so the parser returns `{}`
and everything written over it is vacuously true:

```
### .env.example EXISTS and is EMPTY
FAILED tests/test_repo_hygiene.py::test_the_parser_actually_found_variables
FAILED tests/test_repo_hygiene.py::test_every_secret_class_variable_is_empty
FAILED tests/test_repo_hygiene.py::test_the_deliberate_non_secret_defaults_are_intact
========================= 3 failed, 3 passed in 0.02s ==========================
```

**`test_no_value_in_env_example_looks_like_a_real_credential` is vacuous in isolation.** It iterates
the parsed dict looking for anything credential-shaped; over `{}` it finds nothing and passes. I am
naming it rather than counting it.

It is not left standing alone. `test_the_parser_actually_found_variables` asserts the parser found
**fifteen** variables and fails first, so the suite goes red. That is deliberately the pairing
`DESIGN.md:1230-1236` uses for the audit/PII pair - *"the two are paired so that neither can be
satisfied by silence"* - applied to the instrument rather than to the subject.

Note also that `test_every_secret_class_variable_is_empty` is **not** in that category: it checks
membership before emptiness, so an absent name fails rather than passing as "empty". It fails above
for that reason.

### Summary

**No U0 test passes against an absent subject.** One passes against an *empty* subject, it is named
above, and the paired instrument control turns that case red. The `0 passed` arm in CI's zero-skips
step (§2.5) is the outer backstop: a run whose selection matched nothing at all is a red build, not
a green one.
